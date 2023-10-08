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
from pathlib import Path

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
        if self.verbose >= 1:
            print()

    # -------------------------------------------------------------------------
    def tearDown(self):
        """Tear down routine for calling each particular test method."""
        pass

    # -------------------------------------------------------------------------
    def test_import_base_app(self):
        """Test importing module fb_tools.app."""
        LOG.info('Testing import of fb_tools.app ...')
        import fb_tools.app

        LOG.info('Module version of fb_tools.app is {!r}.'.format(
            fb_tools.app.__version__))

    # -------------------------------------------------------------------------
    def test_instance_base_app(self):
        """Test create an instance of a BaseApplication object."""
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
        """Test importing module fb_tools.cfg_app."""
        LOG.info('Testing import of fb_tools.cfg_app ...')
        import fb_tools.cfg_app

        LOG.info('Module version of fb_tools.cfg_app is {!r}.'.format(
            fb_tools.cfg_app.__version__))

    # -------------------------------------------------------------------------
    def test_instance_cfg_app(self):
        """Test create an instance of a FbConfigApplication object."""
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

    # -------------------------------------------------------------------------
    def test_import_ddns_app(self):
        """Test importing module fb_tools.ddns."""
        LOG.info('Testing import of fb_tools.ddns ...')
        import fb_tools.ddns

        LOG.info('Module version of fb_tools.ddns is {!r}.'.format(
            fb_tools.ddns.__version__))

    # -------------------------------------------------------------------------
    def test_instance_ddns_app(self):
        """Test create an instance of a BaseDdnsApplication object."""
        LOG.info('Test creating an instance of a BaseDdnsApplication object.')

        from fb_tools.ddns import BaseDdnsApplication

        BaseDdnsApplication.do_init_logging = False

        app = BaseDdnsApplication(
            appname=self.appname,
            verbose=self.verbose,
        )
        LOG.debug('BaseDdnsApplication %%r: {!r}'.format(app))
        if self.verbose > 1:
            LOG.debug('BaseDdnsApplication %%s: {}'.format(app))

        del app

    # -------------------------------------------------------------------------
    def test_import_myip_app(self):
        """Test importing module fb_tools.ddns.myip_app."""
        LOG.info('Testing import of fb_tools.ddns.myip_app ...')
        import fb_tools.ddns.myip_app

        LOG.info('Module version of fb_tools.ddns.myip_app is {!r}.'.format(
            fb_tools.ddns.myip_app.__version__))

    # -------------------------------------------------------------------------
    def test_instance_myip_app(self):
        """Test create an instance of a MyIpApplication object."""
        LOG.info('Test creating an instance of a MyIpApplication object.')

        from fb_tools.ddns.myip_app import MyIpApplication

        MyIpApplication.do_init_logging = False

        app = MyIpApplication(
            appname=self.appname,
            verbose=self.verbose,
        )
        LOG.debug('MyIpApplication %%r: {!r}'.format(app))
        if self.verbose > 1:
            LOG.debug('MyIpApplication %%s: {}'.format(app))

        del app

    # -------------------------------------------------------------------------
    def test_import_update_ddns_app(self):
        """Test importing module fb_tools.ddns.update_app."""
        LOG.info('Testing import of fb_tools.ddns.update_app ...')
        import fb_tools.ddns.update_app

        LOG.info('Module version of fb_tools.ddns.update_app is {!r}.'.format(
            fb_tools.ddns.update_app.__version__))

    # -------------------------------------------------------------------------
    def test_instance_update_ddns_app(self):
        """Test create an instance of a UpdateDdnsApplication object."""
        LOG.info('Test creating an instance of a UpdateDdnsApplication object.')

        from fb_tools.ddns.update_app import UpdateDdnsApplication

        UpdateDdnsApplication.do_init_logging = False

        app = UpdateDdnsApplication(
            appname=self.appname,
            verbose=self.verbose,
        )
        LOG.debug('UpdateDdnsApplication %%r: {!r}'.format(app))
        if self.verbose > 1:
            LOG.debug('UpdateDdnsApplication %%s: {}'.format(app))

        del app

    # -------------------------------------------------------------------------
    def test_import_get_file_rm_app(self):
        """Test importing module fb_tools.get_file_rm_app."""
        LOG.info('Testing import of fb_tools.get_file_rm_app ...')
        import fb_tools.get_file_rm_app

        LOG.info('Module version of fb_tools.get_file_rm_app is {!r}.'.format(
            fb_tools.get_file_rm_app.__version__))

    # -------------------------------------------------------------------------
    def test_instance_get_file_rm_app(self):
        """Test create an instance of a GetFileRmApplication object."""
        LOG.info('Test creating an instance of a GetFileRmApplication object.')

        from fb_tools.get_file_rm_app import GetFileRmApplication

        GetFileRmApplication.do_init_logging = False

        app = GetFileRmApplication(
            appname=self.appname,
            testing_args=[str(Path.cwd() / '*.log')],
            verbose=self.verbose,
        )
        LOG.debug('GetFileRmApplication %%r: {!r}'.format(app))
        if self.verbose > 1:
            LOG.debug('GetFileRmApplication %%s: {}'.format(app))

        del app


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
    suite.addTest(TestAppModules('test_import_ddns_app', verbose))
    suite.addTest(TestAppModules('test_instance_ddns_app', verbose))
    suite.addTest(TestAppModules('test_import_myip_app', verbose))
    suite.addTest(TestAppModules('test_instance_myip_app', verbose))
    suite.addTest(TestAppModules('test_import_update_ddns_app', verbose))
    suite.addTest(TestAppModules('test_instance_update_ddns_app', verbose))
    suite.addTest(TestAppModules('test_import_get_file_rm_app', verbose))
    suite.addTest(TestAppModules('test_instance_get_file_rm_app', verbose))

    runner = unittest.TextTestRunner(verbosity=verbose)

    result = runner.run(suite)


# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
