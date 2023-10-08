#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@summary: Test script (and module) for unit tests on error (exception) classes.

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

LOG = logging.getLogger('test_errors')


# =============================================================================
class TestFbErrors(FbToolsTestcase):
    """Testcase class for unit tests on error (exception) classes."""

    # -------------------------------------------------------------------------
    def setUp(self):
        """Execute this on seting up before calling each particular test method."""
        pass

    # -------------------------------------------------------------------------
    def test_import(self):
        """Test importing module fb_tools.errors."""
        LOG.info('Testing import of fb_tools.errors ...')

        import fb_tools.errors

        LOG.info('Module version of fb_tools.errors is {!r}.'.format(
            fb_tools.errors.__version__))

    # -------------------------------------------------------------------------
    def test_fb_error(self):
        """Test raising a FbError exception."""
        LOG.info('Test raising a FbError exception ...')

        from fb_tools.errors import FbError

        with self.assertRaises(FbError) as cm:
            raise FbError('Bla blub')
        e = cm.exception
        LOG.debug('%s raised: %s', e.__class__.__name__, e)

    # -------------------------------------------------------------------------
    def test_func_not_implemented(self):
        """Test raising a FunctionNotImplementedError exception."""
        LOG.info('Test raising a FunctionNotImplementedError exception ...')

        from fb_tools.errors import FunctionNotImplementedError

        with self.assertRaises(FunctionNotImplementedError) as cm:
            raise FunctionNotImplementedError(
                'test_func_not_implemented', 'test_errors')
        e = cm.exception
        LOG.debug('%s raised: %s', e.__class__.__name__, e)

    # -------------------------------------------------------------------------
    def test_io_timeout_error(self):
        """Test raising an IoTimeoutError exception."""
        LOG.info('Test raising an IoTimeoutError exception ...')

        from fb_tools.errors import IoTimeoutError

        with self.assertRaises(IoTimeoutError) as cm:
            raise IoTimeoutError('Test IO error', 2.5, '/etc/shadow')
        e = cm.exception
        LOG.debug('%s raised: %s', e.__class__.__name__, e)

    # -------------------------------------------------------------------------
    def test_read_timeout_error(self):
        """Test raising a ReadTimeoutError exception."""
        LOG.info('Test raising a ReadTimeoutError exception ...')

        from fb_tools.errors import ReadTimeoutError

        with self.assertRaises(ReadTimeoutError) as cm:
            raise ReadTimeoutError(2.55, '/etc/shadow')
        e = cm.exception
        LOG.debug('%s raised: %s', e.__class__.__name__, e)

    # -------------------------------------------------------------------------
    def test_write_timeout_error(self):
        """Test raising a WriteTimeoutError exception."""
        LOG.info('Test raising a WriteTimeoutError exception ...')

        from fb_tools.errors import WriteTimeoutError

        with self.assertRaises(WriteTimeoutError) as cm:
            raise WriteTimeoutError(5, '/etc/shadow')
        e = cm.exception
        LOG.debug('%s raised: %s', e.__class__.__name__, e)


# =============================================================================
if __name__ == '__main__':

    verbose = get_arg_verbose()
    if verbose is None:
        verbose = 0
    init_root_logger(verbose)

    LOG.info('Starting tests ...')

    suite = unittest.TestSuite()

    suite.addTest(TestFbErrors('test_import', verbose))
    suite.addTest(TestFbErrors('test_fb_error', verbose))
    suite.addTest(TestFbErrors('test_func_not_implemented', verbose))
    suite.addTest(TestFbErrors('test_io_timeout_error', verbose))
    suite.addTest(TestFbErrors('test_read_timeout_error', verbose))
    suite.addTest(TestFbErrors('test_write_timeout_error', verbose))

    runner = unittest.TextTestRunner(verbosity=verbose)

    result = runner.run(suite)

# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
