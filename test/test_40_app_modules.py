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

# from fb_tools.common import to_bool
from general import FbToolsTestcase, get_arg_verbose, init_root_logger

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
        if self.verbose >= 1:
            print()

        LOG.info('Testing import of fb_tools.app ...')
        import fb_tools.app

        LOG.debug('Module version of BaseApplication is {!r}.'.format(
            fb_tools.app.__version__))

    # -------------------------------------------------------------------------
    def test_instance_base_app(self):
        """Test create an instance of a BaseApplication object."""
        if self.verbose >= 1:
            print()

        LOG.info('Test creating an instance of a BaseApplication object.')

        from fb_tools.app import BaseApplication

        BaseApplication.do_init_logging = False

        base_app = BaseApplication(
            appname=self.appname,
            verbose=self.verbose,
        )
        LOG.debug('BaseApplication %%r: {!r}'.format(base_app))
        if self.verbose > 1:
            LOG.debug('BaseApplication %%s: {}'.format(base_app))

        del base_app

    # -------------------------------------------------------------------------
    def test_import_config_app(self):
        """Test importing module fb_tools.cfg_app and class FbConfigApplication."""
        if self.verbose >= 1:
            print()

        LOG.info('Testing import of fb_tools.cfg_app ...')
        import fb_tools.cfg_app

        LOG.debug('Module version of FbConfigApplication is {!r}.'.format(
            fb_tools.cfg_app.__version__))

    # -------------------------------------------------------------------------
    def test_instance_cfg_app(self):
        """Test create an instance of a FbConfigApplication object."""
        if self.verbose >= 1:
            print()

        LOG.info('Test creating an instance of a FbConfigApplication object.')

        from fb_tools.cfg_app import FbConfigApplication

        FbConfigApplication.do_init_logging = False

        cfgapp = FbConfigApplication(
            appname=self.appname,
            verbose=self.verbose,
        )
        LOG.debug('FbConfigApplication %%r: {!r}'.format(cfgapp))
        if self.verbose > 1:
            LOG.debug('FbConfigApplication %%s: {}'.format(cfgapp))

        del cfgapp


# =============================================================================
if __name__ == '__main__':

    verbose = get_arg_verbose()
    if verbose is None:
        verbose = 0
    init_root_logger(verbose)

    LOG.info('Starting tests ...')

    suite = unittest.TestSuite()

    suite.addTest(TestAppModules('test_import_base_app', verbose))
    suite.addTest(TestAppModules('test_instance_base_app', verbose))
    suite.addTest(TestAppModules('test_import_config_app', verbose))
    suite.addTest(TestAppModules('test_instance_cfg_app', verbose))

    runner = unittest.TextTestRunner(verbosity=verbose)

    result = runner.run(suite)


# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
