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
    suite.addTest(TestFbHandlingObject('test_run', verbose))

    runner = unittest.TextTestRunner(verbosity=verbose)

    result = runner.run(suite)


# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
