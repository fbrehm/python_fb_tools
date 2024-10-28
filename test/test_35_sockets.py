#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@summary: Test script (and module) for unit tests on socket handler objects.

@author: Frank Brehm
@contact: frank@brehm-online.com
@copyright: © 2024 Frank Brehm, Berlin
@license: GPL3
"""

import logging
import os
import sys
import textwrap

try:
    import unittest2 as unittest
except ImportError:
    import unittest

libdir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'lib'))
sys.path.insert(0, libdir)

from general import FbToolsTestcase, get_arg_verbose, init_root_logger

APPNAME = 'test_socket_handler'
LOG = logging.getLogger(APPNAME)

# =============================================================================
class TestSocketHandler(FbToolsTestcase):
    """Testcase for unit tests on module fb_tools.socket_obj and class GenericSocket."""

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
        """Test import of fb_tools.socket_obj."""
        LOG.info(self.get_method_doc())

        import fb_tools.socket_obj
        LOG.debug('Version of fb_tools.socket_obj: {!r}'.format(
            fb_tools.socket_obj.__version__))

        LOG.info('Test import of GenericSocket from fb_tools.socket_obj ...')
        from fb_tools.socket_obj import GenericSocket
        LOG.debug('Description of GenericSocket: ' + textwrap.dedent(GenericSocket.__doc__))

    # -------------------------------------------------------------------------
    def test_object(self):
        """Test instantiating a simple GenericSocket object."""
        LOG.info(self.get_method_doc())

        from fb_tools.socket_obj import GenericSocket

        with self.assertRaises(TypeError) as cm:
            gen_socket = GenericSocket(appname=APPNAME, verbose=self.verbose)
            LOG.error('This message should never be visible: {!r}'.format(gen_socket))

        e = cm.exception
        LOG.debug('{cls} raised on instantiate a GenericSocket: {err}'.format(
            cls=e.__class__.__name__, err=e))


# =============================================================================
if __name__ == '__main__':

    verbose = get_arg_verbose()
    if verbose is None:
        verbose = 0
    init_root_logger(verbose)

    LOG.info('Starting tests ...')

    suite = unittest.TestSuite()

    suite.addTest(TestSocketHandler('test_import', verbose))
    suite.addTest(TestSocketHandler('test_object', verbose))

    runner = unittest.TextTestRunner(verbosity=verbose)

    result = runner.run(suite)


# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
