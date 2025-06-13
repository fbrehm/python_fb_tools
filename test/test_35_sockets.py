#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@summary: Test script (and module) for unit tests on socket handler objects.

@author: Frank Brehm
@contact: frank@brehm-online.com
@copyright: © 2025 Frank Brehm, Berlin
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
    def test_base_object(self):
        """Test instantiating a base GenericSocket object."""
        LOG.info(self.get_method_doc())

        from fb_tools.socket_obj import GenericSocket

        with self.assertRaises(TypeError) as cm:
            gen_socket = GenericSocket(appname=APPNAME, verbose=self.verbose)
            LOG.error('This message should never be visible: {!r}'.format(gen_socket))

        e = cm.exception
        LOG.debug('{cls} raised on instantiate a GenericSocket: {err}'.format(
            cls=e.__class__.__name__, err=e))

    # -------------------------------------------------------------------------
    def test_minimal_object(self):
        """Test instantiating a minimal inherited GenericSocket object."""
        LOG.info(self.get_method_doc())

        from fb_tools import DEFAULT_ENCODING, MAX_TIMEOUT
        from fb_tools.obj import FbBaseObject
        from fb_tools.socket_obj import GenericSocket
        from fb_tools.socket_obj import MIN_BUFFER_SIZE, MAX_BUFFER_SIZE, MAX_REQUEST_QUEUE_SIZE

        class TestSocket(GenericSocket):
            """Test Socket class."""

            def __init__(self, *args, **kwargs):
                """Initialize it."""
                super(TestSocket, self).__init__(*args, **kwargs,)

            def connect(self):
                pass

            def bind(self):
                pass

        min_socket = TestSocket(appname=APPNAME, verbose=self.verbose)
        LOG.debug('TestSocket %%r: {!r}'.format(min_socket))
        LOG.debug('TestSocket %%s: {}'.format(min_socket))

        if self.verbose >= 1:
            print()
        LOG.debug('Testing set timeout to 600.')
        min_socket.timeout = 600
        self.assertEqual(min_socket.timeout, 600)

        for to in ('bla', -10, MAX_TIMEOUT + 1000):
            with self.assertRaises(ValueError) as cm:
                min_socket.timeout = to
            e = cm.exception
            LOG.debug('{cls} raised on setting timeout {to!r}: {err}'.format(
                cls=e.__class__.__name__, to=to, err=e))

        if self.verbose >= 1:
            print()
        for rqs in (0, 4):
            LOG.debug('Testing set request_queue_size to {}.'.format(rqs))
            min_socket.request_queue_size = rqs
            self.assertEqual(min_socket.request_queue_size, rqs)
        for rqs in ('bla', -5, MAX_REQUEST_QUEUE_SIZE * 3):
            with self.assertRaises(ValueError) as cm:
                min_socket.request_queue_size = rqs
            e = cm.exception
            LOG.debug('{cls} raised on setting request_queue_size {to!r}: {err}'.format(
                cls=e.__class__.__name__, to=rqs, err=e))

        if self.verbose >= 1:
            print()
        for bs in (2048, (1024 * 1024)):
            LOG.debug('Testing set buffer_size to {}.'.format(bs))
            min_socket.buffer_size = bs
            self.assertEqual(min_socket.buffer_size, bs)
        for bs in ('blub', -512, 0, MIN_BUFFER_SIZE - 10, MAX_BUFFER_SIZE * 5, 5120 + 10):
            with self.assertRaises(ValueError) as cm:
                min_socket.buffer_size = bs
            e = cm.exception
            LOG.debug('{cls} raised on setting buffer_size {to!r}: {err}'.format(
                cls=e.__class__.__name__, to=bs, err=e))

        if self.verbose >= 1:
            print()
        LOG.debug('Testing for default encoding {!r}.'.format(DEFAULT_ENCODING))
        self.assertEqual(min_socket.encoding, DEFAULT_ENCODING)
        for enc in ('utf-16', 'latin1'):
            LOG.debug('Testing set encoding to {!r}.'.format(enc))
            min_socket.encoding = enc
            self.assertEqual(min_socket.encoding, enc)
        for enc in (0, 'bla', FbBaseObject()):
            with self.assertRaises(ValueError) as cm:
                min_socket.encoding = enc
            e = cm.exception
            LOG.debug('{cls} raised on setting encoding {enc!r}: {err}'.format(
                cls=e.__class__.__name__, enc=enc, err=e))


# =============================================================================
if __name__ == '__main__':

    verbose = get_arg_verbose()
    if verbose is None:
        verbose = 0
    init_root_logger(verbose)

    LOG.info('Starting tests ...')

    suite = unittest.TestSuite()

    suite.addTest(TestSocketHandler('test_import', verbose))
    suite.addTest(TestSocketHandler('test_base_object', verbose))
    suite.addTest(TestSocketHandler('test_minimal_object', verbose))

    runner = unittest.TextTestRunner(verbosity=verbose)

    result = runner.run(suite)


# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 list
