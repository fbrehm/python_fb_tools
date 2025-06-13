#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@summary: Modules for socket object classes.

@author: Frank Brehm
@contact: frank@brehm-online.com
@copyright: © 2025 by Frank Brehm, Berlin
@summary: modules for socket object classes
"""
from __future__ import absolute_import

# Standard modules
import codecs
import logging
# import re
import select
from abc import ABCMeta
from abc import abstractmethod

# Third party modules
# from fb_logging.colored import colorstr

from six import add_metaclass

# Own modules
from .. import DEFAULT_ENCODING
from .. import MAX_TIMEOUT
from ..common import RE_FIRST_LINE
from ..common import to_bytes
from ..common import to_str
from ..errors import FunctionNotImplementedError
from ..errors import GenericSocketError
# from ..errors import SocketReadTimeoutError
# from ..errors import SocketWriteTimeoutError
from ..handling_obj import HandlingObject
from ..xlate import XLATOR

__version__ = '0.7.0'

LOG = logging.getLogger(__name__)

_ = XLATOR.gettext
ngettext = XLATOR.ngettext

DEFAULT_SOCKET_TIMEOUT = 5
DEFAULT_REQUEST_QUEUE_SIZE = 5
DEFAULT_BUFFER_SIZE = 8192
DEFAULT_POLLING_INTERVAL = 0.05
MIN_BUFFER_SIZE = 512
MAX_BUFFER_SIZE = (1024 * 1024 * 10)
MAX_REQUEST_QUEUE_SIZE = 5
MAX_POLLING_INTERVAL = 60.0


# =============================================================================
@add_metaclass(ABCMeta)
class GenericSocket(HandlingObject):
    """
    Class for capsulation a generic socket somehow.

    Properties:
    * address_family     (str or int   - rw) (inherited from HandlingObject)
    * appname            (str          - rw) (inherited from FbBaseObject)
    * assumed_answer     (None or bool - rw) (inherited from HandlingObject)
    * base_dir           (pathlib.Path - rw) (inherited from FbBaseObject)
    * bonded             (bool         - ro)
    * buffer_size        (int          - rw)
    * connected          (bool         - ro)
    * encoding           (str          - rw)
    * fileno             (None or int  - rw)
    * force              (bool         - rw) (inherited from HandlingObject)
    * initialized        (bool         - rw) (inherited from FbBaseObject)
    * interrupted        (bool         - rw) (inherited from HandlingObject)
    * is_venv            (bool         - ro) (inherited from HandlingObject)
    * polling_interval   (float        - rw)
    * prompt_timeout     (int          - rw) (inherited from HandlingObject)
    * quiet              (bool         - rw) (inherited from HandlingObject)
    * request_queue_size (int          - rw)
    * simulate           (bool         - rw) (inherited from HandlingObject)
    * timeout            (float        - rw)
    * verbose            (int          - rw) (inherited from FbBaseObject)
    * version            (str          - ro) (inherited from FbBaseObject)

    Public attributes:
    * add_search_paths       Array of pathlib.Path (inherited from HandlingObject)
    * client_address         object
    * connection             socket.socket
    * signals_dont_interrupt Array of int          (inherited from HandlingObject)
    * sock                   socket
    """

    default_timeout = DEFAULT_SOCKET_TIMEOUT
    default_request_queue_size = DEFAULT_REQUEST_QUEUE_SIZE
    max_request_queue_size = MAX_REQUEST_QUEUE_SIZE
    default_buffer_size = DEFAULT_BUFFER_SIZE
    min_buffer_size = MIN_BUFFER_SIZE
    max_buffer_size = MAX_BUFFER_SIZE
    default_polling_interval = DEFAULT_POLLING_INTERVAL

    # -------------------------------------------------------------------------
    @abstractmethod
    def __init__(
        self, version=__version__, timeout=None, request_queue_size=None,
            buffer_size=None, encoding=None, polling_interval=None, *args, **kwargs):
        """
        Initialize a GenericSocket object.

        @raise GenericSocketError: on a uncoverable error.

        @param version: version string of the current object or application
        @type version: str
        @param timeout: timeout in seconds for all opening and IO operations
        @type timeout: int
        @param request_queue_size: the maximum number of queued connections (between 0 and 5)
        @type request_queue_size: int
        @param buffer_size: The size of the buffer for receiving data from sockets
        @type buffer_size: int
        @param encoding: The used encoding for Byte-Strings.
        @type encoding: str or None
        @param polling_interval: The interval in seconds between polling attempts from socket
        @type polling_interval: float or None

        @param appname: name of the current running application
        @type appname: str
        @param assumed_answer: The assumed answer to all yes/no questions.
        @type assumed_answer: bool or None
        @param base_dir: base directory used for different purposes
        @type base_dir: str or pathlib.Path
        @param force: Forced execution of something
        @type force: bool
        @param initialized: initialisation of this object is complete after init
        @type initialized: bool
        @param quiet: Quiet execution
        @type quiet: bool
        @param simulate: actions with changing a state are not executed
        @type simulate: bool
        @param terminal_has_colors: has the current terminal colored output
        @type terminal_has_colors: bool
        @param verbose: verbosity level (0 - 9)
        @type verbose: int

        @return: None
        """
        self._timeout = self.default_timeout
        self._request_queue_size = self.default_request_queue_size
        self._buffer_size = self.default_buffer_size
        self._encoding = DEFAULT_ENCODING
        self._bonded = False
        self._connected = False
        self._fileno = None
        self._polling_interval = self.default_polling_interval

        self._input_buffer = ''
        """
        @ivar: the input buffer for all reading actions
        @type: str
        """

        self.sock = None
        """
        @ivar: the underlaying socket object
        @type: socket
        """

        self.connection = None
        """
        @ivar: a socket object after a successful accept()
        @type: socket.socket
        """

        self.client_address = None
        """
        @ivar: the client address after establishing a socket connection
        @type: object
        """

        super(GenericSocket, self).__init__(
            version=version,
            *args, **kwargs,
        )

        if timeout:
            self.timeout = timeout

        self.request_queue_size = request_queue_size
        self.buffer_size = buffer_size
        self.encoding = encoding
        self.polling_interval = polling_interval

        self._input_buffer = bytes('', self.encoding)

    # -----------------------------------------------------------
    @property
    def timeout(self):
        """Return the timeout in seconds for all opening and IO operations."""
        return self._timeout

    @timeout.setter
    def timeout(self, value):
        if value is None:
            self._timeout = self.default_timeout
            return

        v = float(value)
        if v <= 0:
            msg = _('A timeout for a socket operation may not be equal or less then zero.')
            msg += ' ' + _('Given: {!r}').format(value)
            raise ValueError(msg)

        if v > MAX_TIMEOUT:
            msg = _('The timeout for a socket operation must be less or equal to {}.').format(
                MAX_TIMEOUT)
            msg += ' ' + _('Given: {!r}').format(value)
            raise ValueError(msg)

        self._timeout = v

    # -----------------------------------------------------------
    @property
    def fileno(self):
        """Return the file number of the socket after binding or connecting."""
        return self._fileno

    @fileno.setter
    def fileno(self, value):
        if value is None:
            self._fileno = None
        else:
            self._fileno = int(value)

    # -----------------------------------------------------------
    @property
    def connected(self):
        """Get a flag indicating, that the application is connected to the UNIX socket."""
        return self._connected

    # -----------------------------------------------------------
    @property
    def bonded(self):
        """Get a flag indicating, that the socket is bonded for listening."""
        return self._bonded

    # -----------------------------------------------------------
    @property
    def request_queue_size(self):
        """Return the maximum number of queued connections."""
        return self._request_queue_size

    @request_queue_size.setter
    def request_queue_size(self, value):
        if value is None:
            self._request_queue_size = self.default_request_queue_size
            return

        v = int(value)

        if v < 0:
            msg = _('The request queue size must be at least a non nagetive value.')
            msg += ' ' + _('Given: {!r}').format(value)
            raise ValueError(msg)

        if v > self.max_request_queue_size:
            msg = _('The request queue size must be less or equal to {}.').format(
                self.max_request_queue_size)
            msg += ' ' + _('Given: {!r}').format(value)
            raise ValueError(msg)

        self._request_queue_size = v

    # -----------------------------------------------------------
    @property
    def buffer_size(self):
        """Return the size of the buffer for receiving data from sockets."""
        return self._buffer_size

    @buffer_size.setter
    def buffer_size(self, value):
        if value is None:
            self._buffer_size = self.default_buffer_size
            return

        v = int(value)

        if v < self.min_buffer_size:
            msg = _('The buffer size must be at least {} bytes.').format(self.min_buffer_size)
            msg += ' ' + _('Given: {!r}').format(value)
            raise ValueError(msg)

        if v > self.max_buffer_size:
            msg = _('The buffer size must be less or equal to {} bytes.').format(
                self.max_buffer_size)
            msg += ' ' + _('Given: {!r}').format(value)
            raise ValueError(msg)

        mod = v % 512
        if mod:
            msg = _('The buffer size must be a multiple of 512 bytes.')
            msg += ' ' + _('Given: {!r}').format(value)
            raise ValueError(msg)

        self._buffer_size = v

    # -----------------------------------------------------------
    @property
    def encoding(self):
        """Return the the used encoding."""
        return self._encoding

    @encoding.setter
    def encoding(self, value):
        if value is None:
            self._encoding = DEFAULT_ENCODING
            return

        enc = str(value).strip()

        found_encoding = True
        try:
            codecs.lookup(enc)
        except LookupError:
            found_encoding = False

        if not found_encoding:
            msg = _('Did not found encoding {!r}.').format(value)
            raise ValueError(msg)

        self._encoding = enc

    # -----------------------------------------------------------
    @property
    def polling_interval(self):
        """Return the interval in seconds between polling attempts from socket."""
        return self._polling_interval

    @polling_interval.setter
    def polling_interval(self, value):
        if value is None:
            self._polling_interval = self.default_polling_interval
            return

        v = float(value)
        if v <= 0:
            msg = _('An intervall between polling attempts from socket must be greater than zero.')
            msg += ' ' + _('Given: {!r}').format(value)
            raise ValueError(msg)

        if v > MAX_POLLING_INTERVAL:
            msg = _('The intervall between polling attempts from socket must be less '
                    'or equal to {}.').format(MAX_POLLING_INTERVAL)
            msg += ' ' + _('Given: {!r}').format(value)
            raise ValueError(msg)

        self._polling_interval = v

    # -------------------------------------------------------------------------
    @abstractmethod
    def connect(self):
        """Connect to the saved socket as a client."""
        raise FunctionNotImplementedError('connect', self.__class__.__name__)

    # -------------------------------------------------------------------------
    @abstractmethod
    def bind(self):
        """Create the socket and listen on it."""
        raise FunctionNotImplementedError('bind', self.__class__.__name__)

    # -------------------------------------------------------------------------
    def as_dict(self, short=False):
        """
        Transform the elements of the object into a dict.

        @param short: don't include local properties in resulting dict.
        @type short: bool

        @return: structure as dict
        @rtype:  dict
        """
        res = super(GenericSocket, self).as_dict(short=short)

        res['bonded'] = self.bonded
        res['buffer_size'] = self.buffer_size
        res['connected'] = self.connected
        res['encoding'] = self.encoding
        res['fileno'] = self.fileno
        res['polling_interval'] = self.polling_interval
        res['request_queue_size'] = self.request_queue_size
        res['timeout'] = self.timeout

        return res

    # -------------------------------------------------------------------------
    def close(self):
        """Close the current socket."""
        sock = getattr(self, 'sock', None)
        if sock:
            if self.connected or self.bonded:
                if self.verbose > 1:
                    LOG.debug(_('Closing socket ...'))
                sock.close()
            self.sock = None

        self._connected = False
        self._bonded = False

    # -------------------------------------------------------------------------
    def __del__(self):
        """Destruct the current object. Close current socket, if necessary."""
        self.close()

    # -------------------------------------------------------------------------
    def socket_desc(self):
        """Return a textual description of the used socket. Should be overridden."""
        return 'unknown'

    # -------------------------------------------------------------------------
    def reset(self):
        """Reset the socket after interruption of communication."""
        if self.verbose > 2:
            LOG.debug(_('Resetting socket connection ...'))

        if self.connection:
            self.connection.close()
        self.connection = None
        self.client_address = None
        self.interrupted = False

    # -------------------------------------------------------------------------
    def send(self, message):
        """
        Send the message over the socket to the communication partner.

        @param message: the message to send
        @type message: str
        """
        if self.interrupted:
            msg = _(
                'Cannot send message to the receipient, because the socket '
                'connection is interrupted.')
            raise GenericSocketError(msg)

        ok = False
        if self.bonded and self.connection:
            ok = True
        elif self.connected:
            ok = True

        if not ok:
            msg = _(
                'Cannot send message to the receipient, because the socket connection is closed.')
            raise GenericSocketError(msg)

        msg_utf8 = to_bytes(message, self.encoding)

        if self.verbose > 3:
            LOG.debug(_('Sending {!r} to socket.').format(msg_utf8))

        if self.bonded:
            self.connection.sendall(msg_utf8)
        else:
            self.sock.sendall(msg_utf8)

    # -------------------------------------------------------------------------
    def accept(self):
        """Accept a connection, if the socket is bonded in listening mode."""
        if self.connected:
            return

        if not self.bonded:
            msg = _('Cannot accept connection, socket is not bonded.')
            raise GenericSocketError(msg)

        if self.verbose > 1:
            LOG.debug(_('Accept a connection ...'))

        connection, client_address = self.sock.accept()
        self.connection = connection
        self.client_address = client_address
        cla = str(client_address)
        if cla:
            cla = _('Got a request from {!r}.').format(cla)
        else:
            cla = _('Got a request from somewhere on the system.')
        LOG.debug(cla)

    # -------------------------------------------------------------------------
    def _read(self):
        """
        Read data from current socket.

        iThis is done from self.connection, if there is such one after accept(),
        or from self.sock) and store the data in self._input_buffer.

        I assume, that there are some data on the socket, so this call is
        not blocking. If it isn't so, then the call to this method is
        blocking.

        It reads exact one time from socket. If nothing was read, then the
        counterpart of communication has closed the socket, and
        self.interrupted is set to True.
        """
        if self.verbose > 4:
            LOG.debug(_('Trying to get data ...'))
        data = ''
        if self.bonded:
            data = self.connection.recv(self.buffer_size)
        else:
            data = self.sock.recv(self.buffer_size)

        if data:
            if self.verbose > 3:
                LOG.debug(_('Got data: {!r}.').format(data))
            self._input_buffer += data
            return

        if self.verbose > 3:
            LOG.debug(_('Got EOF, counterpart has interrupted ...'))
        self.interrupted = True
        return

    # -------------------------------------------------------------------------
    def read(self, socket_has_data=False, check_socket=True, binary=False):
        """
        Read complete data from socket and gives it back.

        @param socket_has_data: assumes, that there are some data on the socket, that can be read.
                                If False, then read_line() checks, with select, whether there are
                                some data on the socket
        @type socket_has_data: bool
        @param check_socket: Checks whether some data on the socket, if socket_has_data is False
        @type check_socket: bool
        @param binary: if False, decode th read data from current encoding,
                       else return a byte string
        @type binary: bool

        @return: the complete self._input_buffer including the EOL character
        @rtype: str
        """
        # Checking, whether to read from socket
        if not socket_has_data and check_socket:
            if self.has_data():
                socket_has_data = True

        # Read in all data, they are even on socket.
        if socket_has_data:
            if self.verbose > 3:
                LOG.debug(_('Socket has data.'))
            if not self.connection:
                self.accept()

            while socket_has_data:
                self._read()
                if self.interrupted:
                    socket_has_data = False
                else:
                    socket_has_data = self.has_data()
        else:
            if self.verbose > 3:
                LOG.debug(_('Socket has no data.'))

        if self.interrupted:
            self.reset()

        if self.verbose > 3:
            LOG.debug(_('Get input buffer ...'))

        if self._input_buffer:
            if self.verbose > 3:
                LOG.debug(_('Current input buffer: {!r}').format(self._input_buffer))
            if binary:
                ibuffer = self._input_buffer
            else:
                ibuffer = to_str(self._input_buffer, self.encoding)
            self._input_buffer = bytes('', self.encoding)
            return ibuffer

        if binary:
            return bytes('', self.encoding)
        return ''

    # -------------------------------------------------------------------------
    def read_line(self, socket_has_data=False, check_socket=True):
        """
        Read exact one line of data from socket and gives it back.

        This reading action is performed either from self.connection, if
        there is such one after accept(), or from self.sock.

        I assume, that there are some data on the socket, so this call is
        not blocking. If it isn't so, then the call to this method is
        blocking (if has_data was set to False).

        If there was more than one line read at once, the rest is saved
        self._input_buffer.

        @param socket_has_data: assumes, that there are some data on the socket, that can be read.
                                If False, then read_line() checks, with select, whether there are
                                some data on the socket
        @type socket_has_data: bool
        @param check_socket: Checks whether some data on the socket, if socket_has_data is False
        @type check_socket: bool

        @return: the first line from self._input_buffer including the
                 EOL character
        @rtype: str
        """
        ibuffer = self.read(socket_has_data=socket_has_data, check_socket=check_socket)

        if self.verbose > 3:
            LOG.debug(_('Performing input buffer {!r}').format(ibuffer))

        if not ibuffer:
            return ''

        match = RE_FIRST_LINE.search(ibuffer)
        if match:
            line = match.group(1) + match.group(2)
            self._input_buffer = to_bytes(RE_FIRST_LINE.sub('', ibuffer), self.encoding)
            if self.verbose > 3:
                LOG.debug(_('Got a line: {!r}').format(line))
                LOG.debug(_('Current input buffer after read_line(): {!r}').format(
                    self._input_buffer))
            return line

        return ''

    # -------------------------------------------------------------------------
    def has_data(self, polling_interval=None):
        """
        Check, whether the current socket has data in his input buffer, that can be read in.

        @param polling_interval: The interval in seconds between polling attempts from socket
        @type polling_interval: float or None

        @return: there are some data to read
        @rtype: bool
        """
        result = False
        p_int = self.polling_interval
        if polling_interval is not None:
            p_int = polling_interval

        try:
            rlist, wlist, elist = select.select(
                [self.fileno],
                [],
                [],
                p_int
            )
            if self.fileno in rlist:
                result = True

        except select.error as e:
            if e[0] == 4:
                pass

        return result


# =============================================================================

if __name__ == '__main__':

    pass

# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 list
