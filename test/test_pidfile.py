#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: Frank Brehm
@contact: frank@brehm-online.com
@license: GPL3
@summary: test script (and module) for unit tests on PID-File handler and PID-File objects.
"""

import os
import sys
import logging
# import tempfile
# import time

from pathlib import Path

try:
    import unittest2 as unittest
except ImportError:
    import unittest

libdir = os.path.abspath(os.path.join(os.path.dirname(sys.argv[0]), '..', 'lib'))
sys.path.insert(0, libdir)

# from fb_tools.common import pp, to_utf8

from general import FbToolsTestcase, get_arg_verbose, init_root_logger


APPNAME = 'test_pidfile'

LOG = logging.getLogger(APPNAME)


# =============================================================================
class TestPidfileHandler(FbToolsTestcase):

    # -------------------------------------------------------------------------
    def setUp(self):
        self.pidfile_dir = Path('/tmp')
        self.pidfile_basename = Path('test-{}.pid'.format(os.getpid()))
        self.pidfile = self.pidfile_dir / self.pidfile_basename

    # -------------------------------------------------------------------------
    def tearDown(self):

        if self.pidfile.exists():
            LOG.debug("Removing {!r} ...".format(self.pidfile))
            self.pidfile.unlink()

    # -------------------------------------------------------------------------
    def test_import_and_errors(self):

        LOG.info("Testing import of fb_tools.pidfile ...")
        import fb_tools.pidfile
        LOG.debug("Version of module fb_tools.pidfile: {!r}.".format(
            fb_tools.pidfile.__version__))

        LOG.info("Testing {} exception ...".format('PidFileError'))
        from fb_tools.pidfile import PidFileError
        with self.assertRaises(PidFileError) as cm:
            raise PidFileError('bla')
        e = cm.exception
        LOG.debug("{what} raised: {msg}".format(what=e.__class__.__name__, msg=e))
        self.assertEqual(str(e), 'bla')

        LOG.info("Testing {} exception ...".format('InvalidPidFileError'))
        from fb_tools.pidfile import InvalidPidFileError
        with self.assertRaises(InvalidPidFileError) as cm:
            raise InvalidPidFileError(self.pidfile)
        e = cm.exception
        LOG.debug("{what} raised: {msg}".format(what=e.__class__.__name__, msg=e))

        LOG.info("Testing {} exception ...".format('PidFileInUseError'))
        from fb_tools.pidfile import PidFileInUseError
        with self.assertRaises(PidFileInUseError) as cm:
            raise PidFileInUseError(self.pidfile, os.getpid())
        e = cm.exception
        LOG.debug("{what} raised: {msg}".format(what=e.__class__.__name__, msg=e))

    # -------------------------------------------------------------------------
    def test_object(self):

        LOG.info("Testing init of a simple PidFile object.")

        from fb_tools.pidfile import PidFile

        pidfile = PidFile(
            filename=self.pidfile,
            appname=APPNAME,
            verbose=self.verbose,
        )
        LOG.debug("PidFile %%r:\n{!r}".format(pidfile))
        LOG.debug("PidFile %%s:\n{}".format(pidfile))


# =============================================================================
if __name__ == '__main__':

    verbose = get_arg_verbose()
    if verbose is None:
        verbose = 0
    init_root_logger(verbose)

    LOG.info("Starting tests ...")

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTest(TestPidfileHandler('test_import_and_errors', verbose))
    suite.addTest(TestPidfileHandler('test_object', verbose))

    runner = unittest.TextTestRunner(verbosity=verbose)

    result = runner.run(suite)


# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 list
