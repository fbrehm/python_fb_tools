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

LOG = logging.getLogger('test_handling_object')


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

        LOG.info("Testing import of TimeoutExpired from fb_tools.handling_obj ...")
        from fb_tools.handling_obj import TimeoutExpired                    # noqa

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
        LOG.debug("Testing for returncode == {}.".format(ret_val))
        self.assertEqual(e.returncode, ret_val)
        LOG.debug("Testing for cmd == {!r}.".format(cmd))
        self.assertEqual(e.cmd, cmd)
        LOG.debug("Testing for output is None.")
        self.assertIsNone(e.output)
        LOG.debug("Testing for stdout is None.")
        self.assertIsNone(e.stdout)
        LOG.debug("Testing for stderr is None.")
        self.assertIsNone(e.stderr)

        with self.assertRaises(CalledProcessError) as cm:
            raise CalledProcessError(ret_val, cmd, output, stderr)
        e = cm.exception
        LOG.debug("{} raised: {}".format(e.__class__.__name__, e))
        LOG.debug("Testing for output == {!r}.".format(output))
        self.assertEqual(e.output, output)
        LOG.debug("Testing for stdout == {!r}.".format(output))
        self.assertEqual(e.stdout, output)
        LOG.debug("Testing for stderr == {!r}.".format(stderr))
        self.assertEqual(e.stderr, stderr)

    # -------------------------------------------------------------------------
    def test_run(self):

        LOG.info("Testing execution of a shell script.")

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

        LOG.debug("Got return value: %d.", proc.returncode)
        LOG.debug("Got STDOUT: %r", proc.stdout)
        LOG.debug("Got STDERR: %r", proc.stderr)



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
    suite.addTest(TestFbHandlingObject('test_run', verbose))

    runner = unittest.TextTestRunner(verbosity=verbose)

    result = runner.run(suite)


# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
