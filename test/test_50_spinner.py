#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@summary: Test script (and module) for unit tests on spinner module and Spinner objects.

@author: Frank Brehm
@contact: frank@brehm-online.com
@license: GPL3
"""

import logging
import os
import sys
import time

try:
    import unittest2 as unittest
except ImportError:
    import unittest

libdir = os.path.abspath(os.path.join(os.path.dirname(sys.argv[0]), '..', 'src'))
sys.path.insert(0, libdir)

from fb_tools.common import to_bool

from general import FbToolsTestcase, get_arg_verbose, init_root_logger


APPNAME = 'test_spinner'

LOG = logging.getLogger(APPNAME)

EXEC_LONG_TESTS = False
if 'EXEC_LONG_TESTS' in os.environ and os.environ['EXEC_LONG_TESTS'] != '':
    EXEC_LONG_TESTS = to_bool(os.environ['EXEC_LONG_TESTS'])

SPINNER_TO_TEST = 'line'
if 'SPINNER_TO_TEST' in os.environ:
    SPINNER_TO_TEST = os.environ['SPINNER_TO_TEST'].strip()
    if not SPINNER_TO_TEST:
        SPINNER_TO_TEST = None

# =============================================================================
class TestSpinner(FbToolsTestcase):
    """Testcase for unit tests on module fb_tools.spinner."""

    # -------------------------------------------------------------------------
    def setUp(self):
        """Execute this on setting up before calling each particular test method."""
        if self.verbose >= 1:
            print()

    # -------------------------------------------------------------------------
    def tearDown(self):
        """Tear down routine for calling each particular test method."""
        pass

    # -------------------------------------------------------------------------
    def test_import(self):
        """Test import of pp_admintools.spinner."""
        LOG.info(self.get_method_doc())

        import fb_tools.spinner
        LOG.debug('Version of module fb_tools.spinner: {!r}.'.format(
            fb_tools.spinner.__version__))

    # -------------------------------------------------------------------------
    @unittest.skipUnless(SPINNER_TO_TEST, 'No spinner to test selected.')
    def test_particular_spinner(self):
        """Test execution of a particular spinner."""
        LOG.info(self.get_method_doc())

        from fb_tools.spinner import Spinner

        seconds_per_spinner = 10

        msg = 'Testing spinner {!r}: '.format(SPINNER_TO_TEST)
        with Spinner(msg, SPINNER_TO_TEST):
            time.sleep(seconds_per_spinner)
        print()
        print('Continue ...')

    # -------------------------------------------------------------------------
    @unittest.skipUnless(EXEC_LONG_TESTS, 'Long terming tests are not executed.')
    def test_all_spinners(self):
        """Test execution of all spinners."""
        LOG.info(self.get_method_doc())

        import fb_tools.spinner
        from fb_tools.spinner import Spinner

        seconds_per_spinner = 6

        for cycle_name in fb_tools.spinner.CycleList.keys():

            msg = 'Testing spinner {!r}: '.format(cycle_name)
            with Spinner(msg, cycle_name):
                time.sleep(seconds_per_spinner)
            print()


# =============================================================================
if __name__ == '__main__':

    verbose = get_arg_verbose()
    if verbose is None:
        verbose = 0
    init_root_logger(verbose)

    LOG.info('Starting tests ...')

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTest(TestSpinner('test_import', verbose))
    suite.addTest(TestSpinner('test_particular_spinner', verbose))
    suite.addTest(TestSpinner('test_all_spinners', verbose))

    runner = unittest.TextTestRunner(verbosity=verbose)

    result = runner.run(suite)


# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 list
