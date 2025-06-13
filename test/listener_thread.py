#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@summary: Module for the helper class ListenerThread for testing socket objects.

@author: Frank Brehm
@contact: frank@brehm-online.com
@copyright: © 2025 Frank Brehm, Berlin
@license: GPL3
"""
from __future__ import absolute_import

# Standard modules
import logging
import queue
import sys
from threading import Thread

LOG = logging.getLogger('listener_thread')

__version__ = '0.2.1'

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

        from fb_tools.socket_obj import GenericSocket

        if not isinstance(listener_sock, GenericSocket):
            msg = 'Given socket is not a {o} object, but a {g} instead.'.format(
                o='GenericSocket', g=listener_sock.__class__.__name__)
            raise TypeError(msg)

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
                        nr=cur_attempt, s=self.listener_sock.socket_desc()))

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
                    s=self.listener_sock.socket_desc(), at=cur_attempt)
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

if __name__ == '__main__':

    pass

# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
