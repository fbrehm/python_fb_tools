#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
@author: Frank Brehm
@contact: frank@brehm-online.com
@copyright: © 2019 Frank Brehm, Berlin
@license: GPL3
@summary: test script (and module) for unit tests on base handler object
'''

import os
import sys
import logging
import tempfile

try:
    import unittest2 as unittest
except ImportError:
    import unittest

libdir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'lib'))
sys.path.insert(0, libdir)

from general import FbToolsTestcase, get_arg_verbose, init_root_logger

LOG = logging.getLogger('test_base_handler')

EXEC_LONG_TESTS = True
if 'EXEC_LONG_TESTS' in os.environ and os.environ['EXEC_LONG_TESTS'] != '':
    EXEC_LONG_TESTS = to_bool(os.environ['EXEC_LONG_TESTS'])

# =============================================================================
class TestFbBaseHandler(FbToolsTestcase):

    # -------------------------------------------------------------------------
    def setUp(self):

        self.test_file = None

    # -------------------------------------------------------------------------
    def tearDown(self):

        if self.test_file is not None:
            if os.path.exists(self.test_file):
                LOG.debug("Removing {!r} ...".format(self.test_file))
                os.remove(self.test_file)

    # -------------------------------------------------------------------------
    def test_import(self):

        LOG.info("Testing import of fb_tools.handler ...")
        import fb_tools.handler                                             # noqa

        LOG.info("Testing import of BaseHandler from fb_tools.handler ...")
        from fb_tools.handler import BaseHandler                            # noqa

    # -------------------------------------------------------------------------
    def test_generic_base_handler(self):

        LOG.info("Testing init of a base handler object.")

        import fb_tools.handler
        from fb_tools.handler import BaseHandler

        BaseHandler.fileio_timeout = 10
        hdlr = BaseHandler(
            appname=self.appname,
            verbose=self.verbose,
        )
        LOG.debug("BaseHandler %%r: {!r}".format(hdlr))
        LOG.debug("BaseHandler %%s: {}".format(hdlr))

        # from HandlingObject
        self.assertEqual(hdlr.appname, self.appname)
        self.assertEqual(hdlr.verbose, self.verbose)
        self.assertIsNotNone(hdlr.base_dir)
        self.assertEqual(hdlr.version, fb_tools.handler.__version__)
        self.assertFalse(hdlr.simulate)
        self.assertFalse(hdlr.force)
        self.assertFalse(hdlr.quiet)
        self.assertFalse(hdlr.interrupted)
        self.assertEqual(hdlr.fileio_timeout, 10)

        # from BaseHandler
        self.assertIsNotNone(hdlr.default_locale)
        self.assertIsNotNone(hdlr.tz)
        self.assertIsNotNone(hdlr.tz_name)
        self.assertFalse(hdlr.sudo)
        self.assertIsNotNone(hdlr.chown_cmd)
        self.assertIsNotNone(hdlr.echo_cmd)
        self.assertIsNotNone(hdlr.sudo_cmd)

        # from HandlingObject
        hdlr.simulate = True
        self.assertTrue(hdlr.simulate)

        hdlr.force = True
        self.assertTrue(hdlr.force)

        hdlr.quiet = True
        self.assertTrue(hdlr.quiet)

        # from BaseHandler
        hdlr.sudo = True
        self.assertTrue(hdlr.sudo)

        hdlr.set_tz('America/Los_Angeles')

# =============================================================================
if __name__ == '__main__':

    verbose = get_arg_verbose()
    if verbose is None:
        verbose = 0
    init_root_logger(verbose)

    LOG.info("Starting tests ...")

    suite = unittest.TestSuite()

    suite.addTest(TestFbBaseHandler('test_import', verbose))
    suite.addTest(TestFbBaseHandler('test_generic_base_handler', verbose))

    runner = unittest.TextTestRunner(verbosity=verbose)

    result = runner.run(suite)


# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
