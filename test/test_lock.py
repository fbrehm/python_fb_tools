#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: Frank Brehm
@contact: frank.brehm@pixlpark.com
@license: GPL3
@summary: test script (and module) for unit tests on locking handler object
"""

import os
import sys
import logging
import tempfile
import time

try:
    import unittest2 as unittest
except ImportError:
    import unittest

libdir = os.path.abspath(os.path.join(os.path.dirname(sys.argv[0]), '..', 'lib'))
sys.path.insert(0, libdir)

from fb_tools.common import pp, to_utf8

from general import FbToolsTestcase, get_arg_verbose, init_root_logger


APPNAME = 'test_lock'

LOG = logging.getLogger(APPNAME)

# =============================================================================
class TestLockHandler(FbToolsTestcase):

    # -------------------------------------------------------------------------
    def setUp(self):
        self.lock_dir = '/tmp'
        self.lock_basename = 'test-%d.lock' % (os.getpid())
        self.lock_file = os.path.join(self.lock_dir, self.lock_basename)

    # -------------------------------------------------------------------------
    def tearDown(self):

        if os.path.exists(self.lock_file):
            log.debug("Removing %r ...", self.lock_file)
            os.remove(self.lock_file)

    # -------------------------------------------------------------------------
    def create_lockfile(self, content):

        (fd, filename) = tempfile.mkstemp(suffix='.lock', prefix='test-', dir=self.lock_dir)

        LOG.debug("Created temporary file %r, writing in it.", filename)
        content = to_utf8(str(content))
        os.write(fd, content)
        os.close(fd)

        LOG.debug("Created test lockfile: %r.", filename)

        return filename

    # -------------------------------------------------------------------------
    def remove_lockfile(self, filename):

        if os.path.exists(filename):
            LOG.debug("Removing test lockfile %r ...", filename)
            os.remove(filename)
        else:
            LOG.debug("Lockfile %r doesn't exists.", filename)

    # -------------------------------------------------------------------------
    def test_import(self):

        LOG.info("Testing import of fb_tools.handler.lock ...")
        import fb_tools.handler.lock                                        # noqa
        LOG.debug("Module fb_tools.handler.lock imported.")

        from fb_tools.handler.lock import LockHandlerError                  # noqa
        LOG.debug(
            "Exception class %r from %r imported.",
            'LockHandlerError', 'fb_tools.handler.lock')

        from fb_tools.handler.lock import LockdirNotExistsError             # noqa
        LOG.debug(
            "Exception class %r from %r imported.",
            'LockdirNotExistsError', 'fb_tools.handler.lock')

        from fb_tools.handler.lock import LockdirNotWriteableError          # noqa
        LOG.debug(
            "Exception class %r from %r imported.",
            'LockdirNotWriteableError', 'fb_tools.handler.lock')

        from fb_tools.handler.lock import LockHandler                       # noqa
        LOG.debug(
            "Class %r from %r imported.",
            'LockHandler', 'fb_tools.handler.lock')

    # -------------------------------------------------------------------------
    def test_could_not_occupy_lockfile_error(self):

        LOG.info("Test raising a CouldntOccupyLockfileError exception ...")

        from fb_tools.errors import CouldntOccupyLockfileError

        with self.assertRaises(CouldntOccupyLockfileError) as cm:
            raise CouldntOccupyLockfileError('/var/lock/bla.lock', 9.1, 5)
        e = cm.exception
        LOG.debug("%s raised: %s", e.__class__.__name__, e)

    # -------------------------------------------------------------------------
    def test_object(self):

        LOG.info("Testing init of a simple object.")

        from fb_tools.handler.lock import LockHandler

        locker = LockHandler(
            appname='test_base_object',
            verbose=self.verbose,
            lockdir='/tmp',
        )
        LOG.debug("LockHandler %%r:\n%r", locker)
        LOG.debug("LockHandler %%s:\n%s", str(locker))

    # -------------------------------------------------------------------------
    def test_simple_lockfile(self):

        LOG.info("Testing creation and removing of a simple lockfile.")

        from fb_tools.handler.lock import LockHandler

        locker = LockHandler(
            appname='test_base_object',
            verbose=self.verbose,
            lockdir=self.lock_dir,
        )
        LOG.debug("Creating lockfile %r ...", self.lock_file)
        lock = locker.create_lockfile(self.lock_basename)
        LOG.debug("Removing lockfile %r ...", self.lock_file)
        lock = None
        locker.remove_lockfile(self.lock_basename)

    # -------------------------------------------------------------------------
    def test_lockobject(self):

        LOG.info("Testing lock object on creation of a simple lockfile.")

        from fb_tools.handler.lock import LockHandler

        locker = LockHandler(
            appname='test_lock',
            verbose=self.verbose,
            lockdir=self.lock_dir,
        )
        try:
            LOG.debug("Creating lockfile %r ...", self.lock_file)
            lock = locker.create_lockfile(self.lock_basename)
            LOG.debug("PbLock object %%r: %r", lock)
            LOG.debug("PbLock object %%s:\n%s", str(lock))
            lock = None
        finally:
            LOG.debug("Removing lockfile %r ...", self.lock_file)
            locker.remove_lockfile(self.lock_basename)

    # -------------------------------------------------------------------------
    def test_refresh_lockobject(self):

        LOG.info("Testing refreshing of a lock object.")

        from fb_tools.handler.lock import LockHandler

        locker = LockHandler(
            appname='test_lock',
            verbose=self.verbose,
            lockdir=self.lock_dir,
        )
        try:
            LOG.debug("Creating lockfile %r ...", self.lock_file)
            lock = locker.create_lockfile(self.lock_basename)
            LOG.debug("Current ctime: %s" % (lock.ctime.isoformat(' ')))
            LOG.debug("Current mtime: %s" % (lock.mtime.isoformat(' ')))
            if self.verbose > 2:
                LOG.debug("Current lock object before refreshing:\n{}".format(pp(lock.as_dict())))
            mtime1 = lock.stat().st_mtime
            LOG.debug("Sleeping two seconds ...")
            time.sleep(2)
            lock.refresh()
            LOG.debug("New mtime: %s" % (lock.mtime.isoformat(' ')))
            if self.verbose > 2:
                LOG.debug("Current lock object after refreshing:\n{}".format(pp(lock.as_dict())))
            mtime2 = lock.stat().st_mtime
            tdiff = mtime2 - mtime1
            LOG.debug("Got a time difference between mtimes of %0.3f seconds." % (tdiff))
            self.assertGreater(mtime2, mtime1)
            lock = None
        finally:
            LOG.debug("Removing lockfile %r ...", self.lock_file)
            locker.remove_lockfile(self.lock_basename)

    # -------------------------------------------------------------------------
    def test_invalid_dir(self):

        LOG.info("Testing creation lockfile in an invalid lock directory.")

        from fb_tools.handler.lock import LockHandler
        from fb_tools.handler.lock import LockdirNotExistsError
        from fb_tools.handler.lock import LockdirNotWriteableError

        ldir = '/etc/passwd'
        locker = LockHandler(
            appname='test_lock',
            verbose=self.verbose,
            lockdir=ldir,
        )
        with self.assertRaises(LockdirNotExistsError) as cm:
            lock = locker.create_lockfile(self.lock_basename)
            lock = None
        e = cm.exception
        LOG.debug(
            "%s raised as expected on lockdir = %r: %s.",
            'LockdirNotExistsError', ldir, e)
        del locker

        if os.getegid():
            ldir = '/var'
            locker = LockHandler(
                appname='test_lock',
                verbose=self.verbose,
                lockdir=ldir,
            )
            with self.assertRaises(LockdirNotWriteableError) as cm:
                lock = locker.create_lockfile(self.lock_basename)
                lock = None
            e = cm.exception
            LOG.debug(
                "%s raised as expected on lockdir = %r: %s.",
                'LockdirNotWriteableError', ldir, e)

    # -------------------------------------------------------------------------
    def test_valid_lockfile(self):

        LOG.info("Testing fail on creation lockfile with a valid PID.")

        from fb_tools.handler.lock import LockHandler
        from fb_tools.errors import CouldntOccupyLockfileError

        content = "%d\n" % (os.getpid())

        locker = LockHandler(
            appname='test_lock',
            verbose=self.verbose,
            lockdir=self.lock_dir,
        )

        lockfile = self.create_lockfile(content)
        result = None

        try:
            with self.assertRaises(CouldntOccupyLockfileError) as cm:
                result = locker.create_lockfile(
                    lockfile,
                    delay_start=0.2,
                    delay_increase=0.4,
                    max_delay=5
                )
            e = cm.exception
            LOG.debug(
                "%s raised as expected on an valid lockfile: %s",
                e.__class__.__name__, e)
            self.assertEqual(lockfile, e.lockfile)
            if result:
                self.fail("PbLockHandler shouldn't be able to create the lockfile.")
                result = None
        finally:
            self.remove_lockfile(lockfile)

    # -------------------------------------------------------------------------
    def test_invalid_lockfile1(self):

        LOG.info("Testing creation lockfile with an invalid previous lockfile #1.")

        from fb_tools.handler.lock import LockHandler
        from fb_tools.errors import CouldntOccupyLockfileError

        locker = LockHandler(
            appname='test_lock',
            verbose=self.verbose,
            lockdir=self.lock_dir,
        )

        content = "\n\n"
        lockfile = self.create_lockfile(content)
        result = None

        try:
            with self.assertRaises(CouldntOccupyLockfileError) as cm:
                result = locker.create_lockfile(                        # noqa
                    lockfile,
                    delay_start=0.2,
                    delay_increase=0.4,
                    max_delay=5
                )
            e = cm.exception
            LOG.debug(
                "%s raised as expected on an invalid lockfile (empty lines): %s",
                e.__class__.__name__, e)
            result = None

        finally:
            self.remove_lockfile(lockfile)

    # -------------------------------------------------------------------------
    def test_invalid_lockfile2(self):

        LOG.info("Testing creation lockfile with an invalid previous lockfile #2.")

        from fb_tools.handler.lock import LockHandler
        from fb_tools.errors import CouldntOccupyLockfileError

        locker = LockHandler(
            appname='test_lock',
            verbose=self.verbose,
            lockdir=self.lock_dir,
        )

        content = "Bli bla blub\n\n"
        lockfile = self.create_lockfile(content)
        result = None

        try:
            with self.assertRaises(CouldntOccupyLockfileError) as cm:
                result = locker.create_lockfile(
                    lockfile,
                    delay_start=0.2,
                    delay_increase=0.4,
                    max_delay=5
                )
            e = cm.exception
            LOG.debug(
                "%s raised as expected on an invalid lockfile (non-numeric): %s",
                e.__class__.__name__, e)

            locker.remove_lockfile(lockfile)
            if result:
                self.fail("LockHandler should not be able to create the lockfile.")
                result = None

        finally:
            self.remove_lockfile(lockfile)

    # -------------------------------------------------------------------------
    def test_invalid_lockfile3(self):

        LOG.info("Testing creation lockfile with an invalid previous lockfile #3.")

        from fb_tools.handler.lock import LockHandler

        locker = LockHandler(
            appname='test_lock',
            verbose=self.verbose,
            lockdir=self.lock_dir,
        )

        content = "123456\n\n"
        lockfile = self.create_lockfile(content)
        result = None

        try:
            result = locker.create_lockfile(
                lockfile,
                delay_start=0.2,
                delay_increase=0.4,
                max_delay=5
            )
            locker.remove_lockfile(lockfile)
            if not result:
                self.fail("PbLockHandler should be able to create the lockfile.")
            result = None
        finally:
            self.remove_lockfile(lockfile)



# =============================================================================


if __name__ == '__main__':

    verbose = get_arg_verbose()
    if verbose is None:
        verbose = 0
    init_root_logger(verbose)

    LOG.info("Starting tests ...")

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTest(TestLockHandler('test_import', verbose))
    suite.addTest(TestLockHandler('test_could_not_occupy_lockfile_error', verbose))
    suite.addTest(TestLockHandler('test_object', verbose))
    suite.addTest(TestLockHandler('test_simple_lockfile', verbose))
    suite.addTest(TestLockHandler('test_lockobject', verbose))
    suite.addTest(TestLockHandler('test_refresh_lockobject', verbose))
    suite.addTest(TestLockHandler('test_invalid_dir', verbose))
    suite.addTest(TestLockHandler('test_valid_lockfile', verbose))
    suite.addTest(TestLockHandler('test_invalid_lockfile1', verbose))
    suite.addTest(TestLockHandler('test_invalid_lockfile2', verbose))
    suite.addTest(TestLockHandler('test_invalid_lockfile3', verbose))

    runner = unittest.TextTestRunner(verbosity=verbose)

    result = runner.run(suite)


# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 list
