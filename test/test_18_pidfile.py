#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@summary: Test script (and module) for unit tests on PID-File handler and PID-File objects.

@author: Frank Brehm
@contact: frank@brehm-online.com
@license: GPL3
"""

import logging
import os
import sys
from pathlib import Path

try:
    import unittest2 as unittest
except ImportError:
    import unittest

libdir = os.path.abspath(os.path.join(os.path.dirname(sys.argv[0]), "..", "src"))
sys.path.insert(0, libdir)

# from fb_tools.common import pp, to_utf8

from general import FbToolsTestcase, get_arg_verbose, init_root_logger


APPNAME = "test_pidfile"

LOG = logging.getLogger(APPNAME)


# =============================================================================
class TestPidfileHandler(FbToolsTestcase):
    """Testcase for unit tests on module fb_tools.pidfile."""

    # -------------------------------------------------------------------------
    def setUp(self):
        """Execute this on setting up before calling each particular test method."""
        if self.verbose >= 1:
            print()

        self.pidfile_dir = Path("/tmp")
        self.pidfile_basename = Path("test-{}.pid".format(os.getpid()))
        self.pidfile = self.pidfile_dir / self.pidfile_basename

    # -------------------------------------------------------------------------
    def tearDown(self):
        """Tear down routine for calling each particular test method."""
        if self.pidfile.exists():
            LOG.debug("Removing {!r} ...".format(self.pidfile))
            self.pidfile.unlink()

    # -------------------------------------------------------------------------
    def test_import_and_errors(self):
        """Test import of pp_admintools.pidfile."""
        LOG.info(self.get_method_doc())

        import fb_tools.pidfile

        LOG.debug("Version of module fb_tools.pidfile: {!r}.".format(fb_tools.pidfile.__version__))

        LOG.info("Testing {} exception ...".format("PidFileError"))
        from fb_tools.pidfile import PidFileError

        with self.assertRaises(PidFileError) as cm:
            raise PidFileError("bla")
        e = cm.exception
        LOG.debug("{what} raised: {msg}".format(what=e.__class__.__name__, msg=e))
        self.assertEqual(str(e), "bla")

        LOG.info("Testing {} exception ...".format("InvalidPidFileError"))
        from fb_tools.pidfile import InvalidPidFileError

        with self.assertRaises(InvalidPidFileError) as cm:
            raise InvalidPidFileError(self.pidfile)
        e = cm.exception
        LOG.debug("{what} raised: {msg}".format(what=e.__class__.__name__, msg=e))

        LOG.info("Testing {} exception ...".format("PidFileInUseError"))
        from fb_tools.pidfile import PidFileInUseError

        with self.assertRaises(PidFileInUseError) as cm:
            raise PidFileInUseError(self.pidfile, os.getpid())
        e = cm.exception
        LOG.debug("{what} raised: {msg}".format(what=e.__class__.__name__, msg=e))

    # -------------------------------------------------------------------------
    def test_object(self):
        """Test init of a simple PidFile object."""
        LOG.info(self.get_method_doc())

        from fb_tools.pidfile import PidFile

        pidfile = PidFile(
            filename=self.pidfile,
            appname=APPNAME,
            verbose=self.verbose,
        )
        LOG.debug("PidFile %r:\n{!r}".format(pidfile))
        LOG.debug("PidFile %s:\n{}".format(pidfile))

    # -------------------------------------------------------------------------
    def test_create_pidfile(self):
        """Test init of a simple PidFile object."""
        LOG.info(self.get_method_doc())

        if self.pidfile.exists():
            self.skipTest("File {!r} is already existing.".format(str(self.pidfile)))

        from fb_tools.pidfile import PidFile

        pidfile = PidFile(
            filename=self.pidfile,
            appname=APPNAME,
            verbose=self.verbose,
        )
        if self.verbose > 2:
            LOG.debug("PidFile %s:\n{}".format(pidfile))

        if self.pidfile.exists():
            self.fail("File {!r} may not exists in this moment.".format(str(self.pidfile)))
        self.assertFalse(pidfile.created)
        self.assertTrue(pidfile.auto_remove)

        LOG.debug("Creating PID file {!r} ...".format(str(self.pidfile)))
        pidfile.create()

        self.assertTrue(pidfile.created)
        if not self.pidfile.exists():
            self.fail("File {!r} must exists in this moment.".format(str(self.pidfile)))
        if not self.pidfile.is_file():
            self.fail("Pidfile {!r} is not a regular file.".format(str(self.pidfile)))

        content = self.pidfile.read_text()
        pid = os.getpid()
        exp_content = "{}\n".format(pid)

        if self.verbose > 1:
            msg = "Expected content of {f!r}: {exp!r},\nRead content: {r!r}."
            LOG.debug(msg.format(f=str(self.pidfile), exp=exp_content, r=content))
        self.assertEqual(content, exp_content)

        LOG.debug("Destroying PID file {!r} ...".format(str(self.pidfile)))
        pidfile = None

        if self.pidfile.exists():
            self.fail(
                "File {!r} may no more existing after destrying PidFile object.".format(
                    str(self.pidfile)
                )
            )


# =============================================================================
if __name__ == "__main__":

    verbose = get_arg_verbose()
    if verbose is None:
        verbose = 0
    init_root_logger(verbose)

    LOG.info("Starting tests ...")

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTest(TestPidfileHandler("test_import_and_errors", verbose))
    suite.addTest(TestPidfileHandler("test_object", verbose))
    suite.addTest(TestPidfileHandler("test_create_pidfile", verbose))

    runner = unittest.TextTestRunner(verbosity=verbose)

    result = runner.run(suite)


# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 list
