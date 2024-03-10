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
        )
        LOG.debug('UpdateDdnsStatus %%r: {!r}'.format(update_status))
        LOG.debug('UpdateDdnsStatus %%s: {}'.format(update_status))


# =============================================================================
if __name__ == '__main__':

    verbose = get_arg_verbose()
    if verbose is None:
        verbose = 0
    init_root_logger(verbose)

    LOG.info('Starting tests ...')

    suite = unittest.TestSuite()

    suite.addTest(TestDdnsUpdateStatus('test_import', verbose))

    runner = unittest.TextTestRunner(verbosity=verbose)

    result = runner.run(suite)


# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
