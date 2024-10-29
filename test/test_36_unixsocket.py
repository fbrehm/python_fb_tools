#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@summary: Test script (and module) for unit tests on UNIX socket handler objects.

@author: Frank Brehm
@contact: frank@brehm-online.com
@copyright: © 2024 Frank Brehm, Berlin
@license: GPL3
"""

import logging
import os
import queue
import stat
import sys
import tempfile
import textwrap
import time
from pathlib import Path
from threading import Thread

try:
    import unittest2 as unittest
except ImportError:
    import unittest

libdir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'lib'))
sys.path.insert(0, libdir)

from general import FbToolsTestcase, get_arg_verbose, init_root_logger

APPNAME = 'test_unix_socket'
LOG = logging.getLogger(APPNAME)


# =============================================================================
class ListenerThread(Thread):
    """A Thread for listening on a socket file."""

    # -------------------------------------------------------------------------
    def __init__(self, listener_sock, msg2read, *args, **kwargs):
        """Initialize the thread."""
        self.listener_sock = listener_sock
        self.msg2read = msg2read
        self.listener_sock.bind()
        self.__status_queue = queue.Queue()
        super(ListenerThread, self).__init__(*args, **kwargs)

    # -------------------------------------------------------------------------
    def run(self):
        """Read from socket and log the result."""
        max_attempts = 100
        cur_attempt = 0
        line = None

        try:
            while cur_attempt < max_attempts:
                cur_attempt += 1
                if self.listener_sock.verbose > 2:
                    LOG.debug('Attempt {nr} on reading from socket {s!r} ...'.format(
                        nr=cur_attempt, s=str(self.listener_sock.filename)))

                if self.listener_sock.has_data():
                    line = self.listener_sock.read_line()
                    break

            if line:
                LOG.debug('Got line from socket after {at} attempts: {li!r}'.format(
                    at=cur_attempt, li=line))
                if line != self.msg2read:
                    msg = 'Read wrong content - expected: {ex!r}, got {got!r}.'.format(
                        ex=self.msg2read, got=line)
                    raise RuntimeError(msg)

            else:
                msg = 'Got not data from socket {s!r} after {at} reading attempts.'.format(
                    s=str(self.listener_sock.filename), at=cur_attempt)
                raise RuntimeError(msg)

        except BaseException:
            self.__status_queue.put(sys.exc_info())

        self.__status_queue.put(None)

    # -------------------------------------------------------------------------
    def wait_for_exc_info(self):
        """Return content of status quue."""
        return self.__status_queue.get()

    # -------------------------------------------------------------------------
    def join_with_exception(self):
        """Return, if there was no exception, otherwise reraise it."""
        ex_info = self.wait_for_exc_info()
        if ex_info is None:
            return
        else:
            raise ex_info[1]


# =============================================================================
class TestUnixSocketHandler(FbToolsTestcase):
    """Testcase for unit tests on module fb_tools.socket_obj.unix and class UnixSocket."""

    # -------------------------------------------------------------------------
    def setUp(self):
        """Execute this on setting up before calling each particular test method."""
        if self.verbose >= 1:
            print()

        tempsock = tempfile.mkstemp(suffix='.sock', prefix='test-')
        os.close(tempsock[0])
        self.socketfile = Path(tempsock[1])

    # -------------------------------------------------------------------------
    def tearDown(self):
        """Tear down routine for calling each particular test method."""
        if self.socketfile.exists():
            LOG.debug('Removing test socket file {!r}.'.format(str(self.socketfile)))
            self.socketfile.unlink()

    # -------------------------------------------------------------------------
    def test_import(self):
        """Test import of fb_tools.socket_obj.unix."""
        LOG.info(self.get_method_doc())

        import fb_tools.socket_obj.unix
        LOG.debug('Version of fb_tools.socket_obj.unix: {!r}'.format(
            fb_tools.socket_obj.unix.__version__))

        LOG.info('Test import of UnixSocket from fb_tools.socket_obj.unix ...')
        from fb_tools.socket_obj.unix import UnixSocket
        LOG.debug('Description of UnixSocket: ' + textwrap.dedent(UnixSocket.__doc__))

    # -------------------------------------------------------------------------
    def test_object(self):
        """Test instantiating a UnixSocket object."""
        LOG.info(self.get_method_doc())

        self.socketfile.unlink()

        from fb_tools.socket_obj.unix import UnixSocket
        from fb_tools.socket_obj.unix import UnixSocketError
        from fb_tools.socket_obj.unix import DEFAULT_SOCKET_MODE

        with self.assertRaises(TypeError) as cm:
            sock = UnixSocket(appname=APPNAME, verbose=self.verbose)
            LOG.debug('UnixSocket %%r: {!r}'.format(sock))
        e = cm.exception
        LOG.debug(
            '{cls} raised on creating a UnixSocket object without a '
            'socket file name: {err}'.format(cls=e.__class__.__name__, err=e))

        default_mode = stat.S_IFSOCK | stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IWGRP

        sock = UnixSocket(self.socketfile, appname=APPNAME, verbose=self.verbose)
        LOG.debug('UnixSocket %%r: {!r}'.format(sock))
        LOG.debug('UnixSocket %%s: {}'.format(sock))
        LOG.debug('Used owner: {id} ({name!r}).'.format(id=sock.owner_id, name=sock.owner_name))
        self.assertEqual(sock.owner_id, os.geteuid())
        LOG.debug('Used group: {id} ({name!r}).'.format(id=sock.group_id, name=sock.group_name))
        self.assertEqual(sock.group_id, os.getegid())
        LOG.debug('Used socket file mode: {m} == 0o{oct}.'.format(m=sock.mode, oct=sock.mode_oct))
        self.assertEqual(sock.mode, default_mode)
        self.assertEqual(DEFAULT_SOCKET_MODE, default_mode)

        del sock

        if self.verbose >= 1:
            print()
        na_sockfile = 'bla.sock'
        LOG.debug('Testing create a socket without an absolute socket path name.')
        with self.assertRaises(UnixSocketError) as cm:
            sock = UnixSocket(na_sockfile, appname=APPNAME, verbose=self.verbose)
        e = cm.exception
        LOG.debug(
            '{cls} raised on creating a UnixSocket object without an absolute '
            'socket file name: {err}'.format(cls=e.__class__.__name__, err=e))

        LOG.debug('Testing create a socket without the absolute socket path name {!r}.'.format(
            na_sockfile))
        sock = UnixSocket(
            na_sockfile, must_be_absolute=False, appname=APPNAME, verbose=self.verbose)
        LOG.debug('UnixSocket with socket file: {!r}.'.format(sock.filename))
        self.assertEqual(Path(na_sockfile), sock.filename)

    # -------------------------------------------------------------------------
    def test_readwrite(self):
        """Test instantiating a UnixSocket object."""
        LOG.info(self.get_method_doc())

        self.socketfile.unlink()

        from fb_tools.socket_obj.unix import UnixSocket

        msg2send = 'Hallo Ballo!\n'

        listener_socket = UnixSocket(self.socketfile, appname=APPNAME, verbose=self.verbose)
        listener_thread = ListenerThread(listener_socket, msg2send)

        write_sock = UnixSocket(self.socketfile, appname=APPNAME, verbose=self.verbose)
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

    suite.addTest(TestUnixSocketHandler('test_import', verbose))
    suite.addTest(TestUnixSocketHandler('test_object', verbose))
    suite.addTest(TestUnixSocketHandler('test_readwrite', verbose))

    runner = unittest.TextTestRunner(verbosity=verbose)

    result = runner.run(suite)


# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 list
