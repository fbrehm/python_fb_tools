#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@summary: Test script (and module) for unit tests on TCP socket handler objects.

@author: Frank Brehm
@contact: frank@brehm-online.com
@copyright: © 2025 Frank Brehm, Berlin
@license: GPL3
"""
from __future__ import absolute_import

import logging
import os
import sys
import textwrap
import time

try:
    import unittest2 as unittest
except ImportError:
    import unittest

libdir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'lib'))
sys.path.insert(0, libdir)

from general import FbToolsTestcase, get_arg_verbose, init_root_logger

APPNAME = 'test_tcp_socket'
LOG = logging.getLogger(APPNAME)
TEST_PORT = 21345


# =============================================================================
class TestTcpSocketHandler(FbToolsTestcase):
    """Testcase for unit tests on module fb_tools.socket_obj.unix and class UnixSocket."""

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
        """Test import of fb_tools.socket_obj.tcp."""
        LOG.info(self.get_method_doc())

        import fb_tools.socket_obj.tcp
        LOG.debug('Version of fb_tools.socket_obj.tcp: {!r}'.format(
            fb_tools.socket_obj.tcp.__version__))

        LOG.info('Test import of TcpSocket from fb_tools.socket_obj.tcp ...')
        from fb_tools.socket_obj.tcp import TcpSocket
        LOG.debug('Description of TcpSocket: ' + textwrap.dedent(TcpSocket.__doc__))

    # -------------------------------------------------------------------------
    def test_object(self):
        """Test instantiating a TcpSocket object."""
        LOG.info(self.get_method_doc())

        from fb_tools import MAX_PORT_NUMBER
        from fb_tools.handling_obj import HandlingObject
        from fb_tools.socket_obj.tcp import TcpSocket
        from fb_tools.socket_obj.tcp import TcpSocketError

        with self.assertRaises(TypeError) as cm:
            sock = TcpSocket(appname=APPNAME, verbose=self.verbose)
            LOG.debug('TcpSocket %%r: {!r}'.format(sock))
        e = cm.exception
        LOG.debug(
            '{cls} raised on creating a TcpSocket object without an address '
            'and port: {err}'.format(cls=e.__class__.__name__, err=e))

        if self.verbose >= 1:
            print()
        for port in (None, -100, MAX_PORT_NUMBER + 1000):
            with self.assertRaises((TypeError, TcpSocketError)) as cm:
                sock = TcpSocket('*', port, appname=APPNAME, verbose=self.verbose)
                LOG.debug('TcpSocket %%r: {!r}'.format(sock))
            e = cm.exception
            LOG.debug(
                '{cls} raised on creating a TcpSocket object with a wrong '
                'port: {err}'.format(cls=e.__class__.__name__, err=e))

        sock = TcpSocket(None, TEST_PORT, appname=APPNAME, verbose=self.verbose)
        LOG.debug('TcpSocket %%r: {!r}'.format(sock))
        LOG.debug('TcpSocket %%s: {}'.format(sock))
        LOG.debug('Used address: {!r}'.format(sock.address))
        self.assertIsNone(sock.address)
        LOG.debug('Used port number: {!r}'.format(sock.port))
        self.assertEqual(sock.port, TEST_PORT)
        LOG.debug('Used address family: {!r}'.format(sock.address_family))
        self.assertEqual(sock.address_family, HandlingObject.default_address_family)

        del sock

    # -------------------------------------------------------------------------
    def test_readwrite(self):
        """Test reading from and writing to a network socket with a TcpSocket object."""
        LOG.info(self.get_method_doc())

        from fb_tools.socket_obj.tcp import TcpSocket
        from listener_thread import ListenerThread

        msg2send = 'Hallo Ballo!\n'

        listener_socket = TcpSocket('localhost', TEST_PORT, appname=APPNAME, verbose=self.verbose)
        listener_thread = ListenerThread(listener_socket, msg2send)

        write_sock = TcpSocket('localhost', TEST_PORT, appname=APPNAME, verbose=self.verbose)
        write_sock.connect()

        listener_thread.start()

        time.sleep(0.5)
        LOG.debug('Sending to socket: {!r}'.format(msg2send))
        write_sock.send(msg2send)

        listener_thread.join_with_exception()


# =============================================================================
if __name__ == '__main__':

    verbose = get_arg_verbose()
    if verbose is None:
        verbose = 0
    init_root_logger(verbose)

    LOG.info('Starting tests ...')

    suite = unittest.TestSuite()

    suite.addTest(TestTcpSocketHandler('test_import', verbose))
    suite.addTest(TestTcpSocketHandler('test_object', verbose))
    suite.addTest(TestTcpSocketHandler('test_readwrite', verbose))

    runner = unittest.TextTestRunner(verbosity=verbose)

    result = runner.run(suite)


# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 list
