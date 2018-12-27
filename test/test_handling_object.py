#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
@author: Frank Brehm
@contact: frank@brehm-online.com
@copyright: © 2018 Frank Brehm, Berlin
@license: GPL3
@summary: test script (and module) for unit tests on handling object
'''

import os
import sys
import logging

try:
    import unittest2 as unittest
except ImportError:
    import unittest

libdir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'lib'))
sys.path.insert(0, libdir)

from general import FbToolsTestcase, get_arg_verbose, init_root_logger

from fb_tools.common import to_bool

LOG = logging.getLogger('test_handling_object')

EXEC_LONG_TESTS = True
if 'EXEC_LONG_TESTS' in os.environ and os.environ['EXEC_LONG_TESTS'] != '':
    EXEC_LONG_TESTS = to_bool(os.environ['EXEC_LONG_TESTS'])

# =============================================================================
class TestFbHandlingObject(FbToolsTestcase):

    # -------------------------------------------------------------------------
    def setUp(self):
        pass

    # -------------------------------------------------------------------------
    def tearDown(self):
        pass

    # -------------------------------------------------------------------------
    def test_import(self):

        LOG.info("Testing import of fb_tools.handling_obj ...")
        import fb_tools.handling_obj                                        # noqa

        LOG.info("Testing import of CalledProcessError from fb_tools.handling_obj ...")
        from fb_tools.handling_obj import CalledProcessError                # noqa

        LOG.info("Testing import of TimeoutExpiredError from fb_tools.handling_obj ...")
        from fb_tools.handling_obj import TimeoutExpiredError               # noqa

        LOG.info("Testing import of HandlingObject from fb_tools.handling_obj ...")
        from fb_tools.handling_obj import HandlingObject                    # noqa

        LOG.info("Testing import of CompletedProcess from fb_tools.handling_obj ...")
        from fb_tools.handling_obj import CompletedProcess                  # noqa

    # -------------------------------------------------------------------------
    def test_called_process_error(self):

        LOG.info("Testing raising a CalledProcessError exception ...")

        from fb_tools.handling_obj import CalledProcessError

        ret_val = 1
        cmd = "/bin/wrong.command"
        output = "Sample output"
        stderr = "Sample error message"

        with self.assertRaises(CalledProcessError) as cm:
            raise CalledProcessError(ret_val, cmd)
        e = cm.exception
        LOG.debug("{} raised: {}".format(e.__class__.__name__, e))
        LOG.debug("Testing for e.returncode == {}.".format(ret_val))
        self.assertEqual(e.returncode, ret_val)
        LOG.debug("Testing for e.cmd == {!r}.".format(cmd))
        self.assertEqual(e.cmd, cmd)
        LOG.debug("Testing for e.output is None.")
        self.assertIsNone(e.output)
        LOG.debug("Testing for e.stdout is None.")
        self.assertIsNone(e.stdout)
        LOG.debug("Testing for e.stderr is None.")
        self.assertIsNone(e.stderr)

        with self.assertRaises(CalledProcessError) as cm:
            raise CalledProcessError(ret_val, cmd, output, stderr)
        e = cm.exception
        LOG.debug("{} raised: {}".format(e.__class__.__name__, e))
        LOG.debug("Testing for e.output == {!r}.".format(output))
        self.assertEqual(e.output, output)
        LOG.debug("Testing for e.stdout == {!r}.".format(output))
        self.assertEqual(e.stdout, output)
        LOG.debug("Testing for e.stderr == {!r}.".format(stderr))
        self.assertEqual(e.stderr, stderr)

    # -------------------------------------------------------------------------
    def test_timeout_expired_error(self):

        LOG.info("Testing raising a TimeoutExpiredError exception ...")

        from fb_tools.handling_obj import TimeoutExpiredError

        timeout_1sec = 1
        timeout_10sec = 10
        cmd = "/bin/long.terming.command"
        output = "Sample output"
        stderr = "Sample error message"

        with self.assertRaises(TimeoutExpiredError) as cm:
            raise TimeoutExpiredError(cmd, timeout_1sec)
        e = cm.exception
        LOG.debug("{} raised: {}".format(e.__class__.__name__, e))
        LOG.debug("Testing for e.timeout == {}.".format(timeout_1sec))
        self.assertEqual(e.timeout, timeout_1sec)
        LOG.debug("Testing for e.cmd == {!r}.".format(cmd))
        self.assertEqual(e.cmd, cmd)
        LOG.debug("Testing for e.output is None.")
        self.assertIsNone(e.output)
        LOG.debug("Testing for e.stdout is None.")
        self.assertIsNone(e.stdout)
        LOG.debug("Testing for e.stderr is None.")
        self.assertIsNone(e.stderr)

        with self.assertRaises(TimeoutExpiredError) as cm:
            raise TimeoutExpiredError(cmd, timeout_10sec, output, stderr)
        e = cm.exception
        LOG.debug("{} raised: {}".format(e.__class__.__name__, e))
        LOG.debug("Testing for e.output == {!r}.".format(output))
        self.assertEqual(e.output, output)
        LOG.debug("Testing for e.stdout == {!r}.".format(output))
        self.assertEqual(e.stdout, output)
        LOG.debug("Testing for e.stderr == {!r}.".format(stderr))
        self.assertEqual(e.stderr, stderr)

    # -------------------------------------------------------------------------
    def test_generic_handling_object(self):

        LOG.info("Testing init of a generic handling object.")

        import fb_tools.handling_obj
        from fb_tools.handling_obj import HandlingObject

        HandlingObject.fileio_timeout = 10
        hdlr = HandlingObject(
            appname=self.appname,
            verbose=self.verbose,
        )
        LOG.debug("HandlingObject %%r: {!r}".format(hdlr))
        LOG.debug("HandlingObject %%s: {}".format(hdlr))
        self.assertEqual(hdlr.appname, self.appname)
        self.assertEqual(hdlr.verbose, self.verbose)
        self.assertIsNotNone(hdlr.base_dir)
        self.assertEqual(hdlr.version, fb_tools.handling_obj.__version__)
        self.assertFalse(hdlr.simulate)
        self.assertFalse(hdlr.force)
        self.assertFalse(hdlr.interrupted)
        self.assertEqual(hdlr.fileio_timeout, 10)

        hdlr.simulate = True
        self.assertTrue(hdlr.simulate)

        hdlr.force = True
        self.assertTrue(hdlr.force)

    # -------------------------------------------------------------------------
    @unittest.skipUnless(EXEC_LONG_TESTS, "Long terming tests are not executed.")
    def test_run_simple(self):

        LOG.info("Testing execution of a shell script.")

        from fb_tools.common import pp
        from fb_tools.handling_obj import HandlingObject, CompletedProcess
        from fb_tools.errors import CommandNotFoundError

        curdir = os.path.dirname(os.path.abspath(__file__))
        call_script = os.path.join(curdir, 'call_script.sh')
        if not os.path.exists(call_script):
            raise CommandNotFoundError(call_script)

        LOG.debug("Trying to execute {!r} ...".format(call_script))

        hdlr = HandlingObject(
            appname=self.appname,
            verbose=self.verbose,
        )

        proc = hdlr.run([call_script])
        LOG.debug("Got back a {} object.".format(proc.__class__.__name__))
        self.assertIsInstance(proc, CompletedProcess)

        LOG.debug("Got return value: {}.".format(proc.returncode))
        LOG.debug("Got proc args:\n{}.".format(pp(proc.args)))
        LOG.debug("Got STDOUT: {!r}".format(proc.stdout))
        LOG.debug("Got STDERR: {!r}".format(proc.stderr))

        self.assertEqual(proc.returncode, 0)
        self.assertIsNone(proc.stdout)
        self.assertIsNone(proc.stderr)

# =============================================================================
if __name__ == '__main__':

    verbose = get_arg_verbose()
    if verbose is None:
        verbose = 0
    init_root_logger(verbose)

    LOG.info("Starting tests ...")

    suite = unittest.TestSuite()

    suite.addTest(TestFbHandlingObject('test_import', verbose))
    suite.addTest(TestFbHandlingObject('test_called_process_error', verbose))
    suite.addTest(TestFbHandlingObject('test_timeout_expired_error', verbose))
    suite.addTest(TestFbHandlingObject('test_generic_handling_object', verbose))
    suite.addTest(TestFbHandlingObject('test_run_simple', verbose))

    runner = unittest.TextTestRunner(verbosity=verbose)

    result = runner.run(suite)


# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
