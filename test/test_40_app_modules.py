#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@summary: Test script (and module) for unit tests on  pplication objects (only syntax checks).

@author: Frank Brehm
@contact: frank@brehm-online.com
@copyright: © 2023 Frank Brehm, Berlin
@license: GPL3
"""

import logging
import os
import sys

try:
    import unittest2 as unittest
except ImportError:
    import unittest

libdir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'lib'))
sys.path.insert(0, libdir)

from general import FbToolsTestcase, get_arg_verbose, init_root_logger

# from fb_tools.common import to_bool

LOG = logging.getLogger('test_app_modules')

# =============================================================================
class TestAppModules(FbToolsTestcase):
    """Testcase for importing different application modules and classes."""

    # -------------------------------------------------------------------------
    def setUp(self):
        """Execute this on seting up before calling each particular test method."""
        pass

    # -------------------------------------------------------------------------
    def tearDown(self):
        """Tear down routine for calling each particular test method."""
        pass

    # -------------------------------------------------------------------------
    def test_import_base_app(self):
        """Test importing module fb_tools.app and class BaseApplication."""
        LOG.info('Testing import of fb_tools.app ...')
        import fb_tools.app

        LOG.info('Testing import of BaseApplication from fb_tools.app ...')
        from fb_tools.app import BaseApplication                            # noqa: F401

        LOG.debug('Module version of BaseApplication is {!r}.'.format(
            fb_tools.app.__version__))


# =============================================================================
if __name__ == '__main__':

    verbose = get_arg_verbose()
    if verbose is None:
        verbose = 0
    init_root_logger(verbose)

    LOG.info('Starting tests ...')

    suite = unittest.TestSuite()

    suite.addTest(TestAppModules('test_import_base_app', verbose))

    runner = unittest.TextTestRunner(verbosity=verbose)

    result = runner.run(suite)


# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
