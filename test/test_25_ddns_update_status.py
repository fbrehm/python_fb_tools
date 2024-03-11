#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@summary: Test script (and module) for unit tests on ddns update status class.

@author: Frank Brehm
@contact: frank@brehm-online.com
@copyright: © 2024 Frank Brehm, Berlin
@license: GPL3
"""

import logging
import os
import sys
import textwrap
from pathlib import Path

try:
    import unittest2 as unittest
except ImportError:
    import unittest

libdir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'lib'))
sys.path.insert(0, libdir)

# from fb_tools.common import to_bool

from general import FbToolsTestcase, get_arg_verbose, init_root_logger

LOG = logging.getLogger('test_ddns_update_status')


# =============================================================================
class TestDdnsUpdateStatus(FbToolsTestcase):
    """Testcase for unit tests on module fb_tools.update_app and class UpdateDdnsStatus."""

    # -------------------------------------------------------------------------
    def setUp(self):
        """Execute this on setting up before calling each particular test method."""
        if self.verbose >= 1:
            print()

        self.test_dir = Path(__file__).parent.resolve()
        self.work_dir = self.test_dir / 'ddns-update-status'

        self.invalid_test_file = self.test_dir / 'testfile'
        self.invalid_test_file.touch()

        self.invalid_test_dir = self.test_dir / 'testdir'
        self.invalid_test_dir.mkdir(mode=0o000)

        self.invalid_test_dir_ro = self.test_dir / 'testdir-ro'
        self.invalid_test_dir_ro.mkdir(mode=0o500)

        self.domain = 'home-uhu-banane.ddnss.org'

    # -------------------------------------------------------------------------
    def tearDown(self):
        """Tear down routine for calling each particular test method."""
        # Removing test update ddns status files
        files = self.work_dir.glob('*')
        if files:
            for status_file in files:
                if status_file.name.startswith('.'):
                    continue
                LOG.debug('Removing status file {!r} ...'.format(str(status_file)))
                status_file.unlink()

        for path in (self.invalid_test_file, self.invalid_test_dir, self.invalid_test_dir_ro):
            if path.exists():
                if path.is_dir():
                    LOG.debug('Removing test directory {!r} ...'.format(str(path)))
                    path.rmdir()
                else:
                    LOG.debug('Removing test file {!r} ...'.format(str(path)))
                    path.unlink()

    # -------------------------------------------------------------------------
    def test_import(self):
        """Test importing and instantiating an empty UpdateDdnsStatus object."""
        LOG.info(self.get_method_doc())

        from fb_tools.ddns.update_app import UpdateDdnsStatus
        LOG.debug('Description of UpdateDdnsStatus: ' + textwrap.dedent(
            UpdateDdnsStatus.__doc__))

        update_status = UpdateDdnsStatus(
            appname=self.appname,
            verbose=self.verbose,
            workdir=self.work_dir,
            domain=self.domain,
        )
        LOG.debug('UpdateDdnsStatus %%r: {!r}'.format(update_status))
        LOG.debug('UpdateDdnsStatus %%s: {}'.format(update_status))

        LOG.debug('Test invalid UpdateDdnsStatus ...')
        with self.assertRaises(ValueError) as cm:
            update_status = UpdateDdnsStatus(
                appname=self.appname,
                verbose=self.verbose,
                workdir=self.work_dir,
                domain=None,
            )
            LOG.debug('UpdateDdnsStatus %%s: {}'.format(update_status))
        e = cm.exception
        LOG.debug('%s raised: %s', e.__class__.__name__, e)

    # -------------------------------------------------------------------------
    def test_check_workdir(self):
        """Test method check_workdir() of a UpdateDdnsStatus object."""
        LOG.info(self.get_method_doc())

        from fb_tools.ddns.update_app import UpdateDdnsStatus
        from fb_tools.errors import CommonDirectoryError

        LOG.debug('Testing valid working directory {!r} ...'.format(self.work_dir))
        update_status = UpdateDdnsStatus(
            appname=self.appname,
            verbose=self.verbose,
            workdir=self.work_dir,
            domain=self.domain,
        )
        if self.verbose > 1:
            LOG.debug('UpdateDdnsStatus %%s: {}'.format(update_status))
        update_status.check_workdir(check_writeable=True)
        LOG.debug('Check of working directory {!r} was successful.'.format(self.work_dir))
        self.assertEqual(self.work_dir, update_status.workdir)

        invalid_workdirs = (
            None, self.invalid_test_file, self.invalid_test_dir, self.invalid_test_dir_ro,
        )
        for workdir in invalid_workdirs:
            LOG.debug('Check of invalid working directory {!r} ...'.format(workdir))
            update_status = UpdateDdnsStatus(
                appname=self.appname,
                verbose=self.verbose,
                workdir=workdir,
                domain=self.domain,
            )
            with self.assertRaises(CommonDirectoryError) as cm:
                update_status.check_workdir(check_writeable=True)
            e = cm.exception
            LOG.debug('%s raised: %s', e.__class__.__name__, e)

    # -------------------------------------------------------------------------
    def test_write_yaml(self):
        """Test writingg an update status YAML file."""
        LOG.info(self.get_method_doc())

        from fb_tools.ddns.update_app import UpdateDdnsStatus
        update_status = UpdateDdnsStatus(
            appname=self.appname,
            verbose=self.verbose,
            workdir=self.work_dir,
            domain=self.domain,
        )

        update_status.write_status()
        content = update_status.filename_abs.read_text(encoding='utf-8')
        msg = 'Content of written status file {!r}:'.format(str(update_status.filename_abs))
        msg += '\n' + content
        LOG.debug(msg)


# =============================================================================
if __name__ == '__main__':

    verbose = get_arg_verbose()
    if verbose is None:
        verbose = 0
    init_root_logger(verbose)

    LOG.info('Starting tests ...')

    suite = unittest.TestSuite()

    suite.addTest(TestDdnsUpdateStatus('test_import', verbose))
    suite.addTest(TestDdnsUpdateStatus('test_check_workdir', verbose))
    suite.addTest(TestDdnsUpdateStatus('test_write_yaml', verbose))

    runner = unittest.TextTestRunner(verbosity=verbose)

    result = runner.run(suite)


# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
