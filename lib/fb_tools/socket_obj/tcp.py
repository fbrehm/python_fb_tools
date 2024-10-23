#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@summary: Module for a TCP socket object class.

@author: Frank Brehm
@contact: frank@brehm-online.com
@copyright: © 2024 by Frank Brehm, Berlin
"""
from __future__ import absolute_import

# Standard modules
import ipaddress
import logging
import socket

# Third party modules

# Own modules

from . import GenericSocket
from .. import MAX_PORT_NUMBER
from ..errors import GenericSocketError
from ..xlate import XLATOR

__version__ = '0.3.0'

LOG = logging.getLogger(__name__)

_ = XLATOR.gettext
ngettext = XLATOR.ngettext


# =============================================================================
class TcpSocketError(GenericSocketError):
    """Base error class for all special exceptions raised in this module."""

    pass


# =============================================================================
class CouldNotOpenTcpSocketError(TcpSocketError):
    """Special exception class for the case, the socket could not opened."""

    pass


# =============================================================================
class TcpSocket(GenericSocket):
    """
    Class for capsulation a TCP socket.

    Properties:
    * address            (ipaddress or str  - ro)
    * address_family     (str or int        - rw) (inherited from HandlingObject)
    * address_info_flags (int               - ro)
    * appname            (str               - rw) (inherited from FbBaseObject)
    * assumed_answer     (None or bool      - rw) (inherited from HandlingObject)
    * base_dir           (pathlib.Path      - rw) (inherited from FbBaseObject)
    * bonded             (bool              - ro) (inherited from GenericSocket)
    * buffer_size        (int               - rw) (inherited from GenericSocket)
    * connected          (bool              - ro) (inherited from GenericSocket)
    * encoding           (str               - rw) (inherited from GenericSocket)
    * fileno             (None or int       - rw) (inherited from GenericSocket)
    * force              (bool              - rw) (inherited from HandlingObject)
    * initialized        (bool              - rw) (inherited from FbBaseObject)
    * interrupted        (bool              - rw) (inherited from HandlingObject)
    * is_venv            (bool              - ro) (inherited from HandlingObject)
    * own_address        (ipaddress         - ro)
    * port               (int               - rw)
    * prompt_timeout     (int               - rw) (inherited from HandlingObject)
    * quiet              (bool              - rw) (inherited from HandlingObject)
    * request_queue_size (int               - rw) (inherited from GenericSocket)
    * resolved_address   (None or ipaddress - ro)
    * simulate           (bool              - rw) (inherited from HandlingObject)
    * timeout            (float             - rw) (inherited from GenericSocket)
    * used_addr_family   (Nonee or int      - ro)
    * used_protocol      (None or int       - ro)
    * used_socket_addr   (None or tuple     - ro)
    * used_socket_type   (?                 - ro)
    * verbose            (int               - rw) (inherited from FbBaseObject)
    * version            (str               - ro) (inherited from FbBaseObject)

    Public attributes:
    * add_search_paths       Array of pathlib.Path (inherited from HandlingObject)
    * client_address         object                (inherited from GenericSocket)
    * connection             socket.socket         (inherited from GenericSocket)
    * signals_dont_interrupt Array of int          (inherited from HandlingObject)
    * sock                   socket                (inherited from GenericSocket)
    """

    port_err_msg_min = _('The TCP port number must be a positive integer value, not {!r}.')
    port_err_msg_max = _('The TCP port number must be less than {max}, not {cur!r}.')

    # -------------------------------------------------------------------------
    def __init__(
        self, address, port, address_family=None, address_info_flags=0,
            version=__version__, *args, **kwargs):
        """
        Initialise of the TcpSocket object.

        @raise TcpSocketError: on a uncoverable error.

        @param address: the hostname or IP address, where to connect to or on which listening to.
                        If it can be converted to a IPy.IP object, an IP address is assumed.
                        If None is given, then the socket will listen on all local IP addresses -
                        not usable for client sockets.  Else a hostname is assumed.
        @type address: str or IPy.IP or None
        @param address_family: the IP address family, may be socket.AF_INET or socket.AF_INET6 or
                               None (for both).  If None, in client mode will tried to connect
                               first to an IPv6 address, then IPv4 address.  If None in listening
                               mode it will listen on both IPv6 and IPv4.
        @type address_family: int or None
        @param address_info_flags: additional address information flags, used by
                                   socket.getaddrinfo().
                                   See "man getaddrinfo" for more information.
        @type address_info_flags: int
        @param appname: name of the current running application
        @type appname: str
        @param assumed_answer: The assumed answer to all yes/no questions.
        @type assumed_answer: bool or None
        @param base_dir: base directory used for different purposes
        @type base_dir: str or pathlib.Path
        @param buffer_size: The size of the buffer for receiving data from sockets
        @type buffer_size: int
        @param force: Forced execution of something
        @type force: bool
        @param initialized: initialisation of this object is complete after init
        @type initialized: bool
        @param port: the TCP port number, where to connect to or on which should be listened.
        @type port: int
        @param quiet: Quiet execution
        @type quiet: bool
        @param request_queue_size: the maximum number of queued connections (between 0 and 5)
        @type request_queue_size: int
        @param simulate: actions with changing a state are not executed
        @type simulate: bool
        @param terminal_has_colors: has the current terminal colored output
        @type terminal_has_colors: bool
        @param timeout: timeout in seconds for all opening and IO operations
        @type timeout: int
        @param verbose: verbosity level (0 - 9)
        @type verbose: int
        @param version: version string of the current object or application
        @type version: str

        @return: None
        """
        self._address = None
        self._address_info_flags = None
        self._port = None

        super(TcpSocket, self).__init__(
            version=version,
            *args, **kwargs,
        )

        self._address = address
        self._address_info_flags = int(address_info_flags)

        self._resolved_address = None
        """
        @ivar: The resolved IP address, where to connect to or on which listening to.
               If self.address is '*', the self.resolved_address stays to None.
        @type: IPy.IP or None
        """

        self.port = port

        self._used_addr_family = None
        self._used_socket_type = None
        self._used_protocol = None
        self._used_canon_name = None
        self._used_socket_addr = None
        self._own_address = None

        self.address_family = address_family

        self.initialized = True

    # -----------------------------------------------------------
    @property
    def address(self):
        """The hostname or IP address, where to connect to or on which listening to."""
        return self._address

    # -----------------------------------------------------------
    @property
    def address_info_flags(self):
        """Additional address information flags, used by socket.getaddrinfo()."""
        return self._address_info_flags

    # -----------------------------------------------------------
    @property
    def resolved_address(self):
        """The resolved IP address, where to connect to or on which listening to."""
        return self._resolved_address

    # -----------------------------------------------------------
    @property
    def port(self):
        """The TCP port number, where to connect to or on which should be listened."""
        return self._port

    @port.setter
    def port(self, value):
        v = int(value)
        if v < 1:
            raise TcpSocketError(self.port_err_msg_min.format(value))
        if v >= MAX_PORT_NUMBER:
            msg = self.port_err_msg_max.format(max=MAX_PORT_NUMBER, cur=value)
            raise TcpSocketError(msg)

    # -----------------------------------------------------------
    @property
    def used_addr_family(self):
        """The used IP address family after connecting or binding."""
        return self._used_addr_family

    # -----------------------------------------------------------
    @property
    def used_socket_type(self):
        """The used socket type after connecting or binding."""
        return self._used_socket_type

    # -----------------------------------------------------------
    @property
    def used_protocol(self):
        """The used IP protocol after connecting or binding."""
        return self._used_protocol

    # -----------------------------------------------------------
    @property
    def used_socket_addr(self):
        """
        Return a tuple describing a socket address.

        Its whose format depends on used_addr_family (a (address, port) 2-tuple for AF_INET,
        a (address, port, flow info, scope id) 4-tuple for AF_INET6),
        and is meant to be passed to the socket.connect() method.
        """
        return self._used_socket_addr

    # -----------------------------------------------------------
    @property
    def own_address(self):
        """The socket’s own address."""
        return self._own_address

    # -------------------------------------------------------------------------
    def as_dict(self, short=False):
        """
        Transform the elements of the object into a dict.

        @return: structure as dict
        @rtype:  dict
        """
        res = super(TcpSocket, self).as_dict(short=short)

        res['address'] = self.address
        res['resolved_address'] = self.resolved_address
        res['address_info_flags'] = self.address_info_flags
        res['port'] = self.port
        res['used_addr_family'] = self.used_addr_family
        res['used_socket_type'] = self.used_socket_type
        res['used_protocol'] = self.used_protocol
        res['used_socket_addr'] = self.used_socket_addr
        res['own_address'] = self.own_address

        return res

    # -------------------------------------------------------------------------
    def close(self):
        """Close the current socket."""
        super(TcpSocket, self).close()

        self._used_addr_family = None
        self._used_socket_type = None
        self._used_protocol = None
        self._used_socket_addr = None
        self._own_address = None
        self.fileno = None

    # -------------------------------------------------------------------------
    def connect(self):
        """Connect to the TCP socket as a client."""
        if not self.address:
            msg = _('Cannot connect to an undefined IP address or hostname.')
            raise TcpSocketError(msg)

        if self.verbose > 2:
            LOG.debug(_(
                'Connecting to address {addr!r}, port {port} by TCP ...').format(
                addr=self.address, port=self.port))

        if self.connected:
            msg = _(
                'The socket is already connected to {addr!r}, port {port}.').format(
                addr=self.address, port=self.port)
            raise TcpSocketError(msg)

        if self.bonded:
            msg = _(
                'The application is allready bonded to {addr!r}, port {port}.').format(
                addr=self.address, port=self.port)
            raise TcpSocketError(msg)

        self.sock = None
        self._used_addr_family = None
        self._used_socket_type = None
        self._used_protocol = None
        self._used_socket_addr = None
        self._resolved_address = None
        self._own_address = None
        ip_addr = None
        family = None
        socktype = socket.SOCK_STREAM
        proto = socket.IPPROTO_TCP
        socketaddr = None

        ai_flags = self.address_info_flags & ~socket.AI_PASSIVE
        addresses = self.get_address(
            self.address, port=self.port, addr_type=socktype,
            flags=ai_flags, as_socket_address=True)

        if not addresses:
            msg = _('No valid address for host {!r} found.').format(str(self.address))
            raise CouldNotOpenTcpSocketError(msg)

        last_err_msg = None
        can_not_connect_msg = 'Could not connect to {addr!r} port {p} via TCP: {m}'

        for socketaddr in addresses:
            ip_addr = ipaddress.ip_address(socketaddr[0])
            if ip_addr.version == 4:
                family = socket.AF_INET
            else:
                family = socket.AF_INET6

            try:
                self.sock = socket.socket(family, socktype, proto)
            except socket.error as msg:
                if self.verbose > 3:
                    LOG.debug('Could not create TCP socket: {}'.format(msg))
                last_err_msg = str(msg)
                self.sock = None
                continue

            try:
                self.sock.connect(socketaddr)
            except socket.error as msg:
                if self.verbose > 3:
                    LOG.debug(can_not_connect_msg.format(addr=str(ip_addr), p=self.port, n=msg))
                self.sock.close()
                last_err_msg = str(msg)
                self.sock = None
                continue

            break

        if self.sock is None:
            msg = can_not_connect_msg.format(addr=self.address, p=self.port, n=last_err_msg)
            raise CouldNotOpenTcpSocketError(msg)

        self._connected = True
        self.fileno = self.sock.fileno()
        self._used_addr_family = family
        self._used_socket_type = socktype
        self._used_protocol = proto
        self._used_socket_addr = socketaddr
        self._resolved_address = ip_addr
        self._own_address = self.sock.getsockname()

    # -------------------------------------------------------------------------
    def bind(self):
        """Create a TCP socket and listen on it."""
        msg_args = {'addr': '*', 'port': self.port}
        if self.address:
            msg_args['addr'] = str(self.address)

        if self.verbose > 1:
            msg = _('Creating a listening TCP socket on address {addr!r}, port {port} ...')
            LOG.debug(msg.format(**msg_args))

        if self.connected:
            msg = _('The socket is already connected to address {addr!r}, port {port}.')
            raise TcpSocketError(msg.format(**msg_args))

        if self.bonded:
            msg = _('The application is already bonded to address {addr!r}, port {port}.')
            raise TcpSocketError(msg.format(**msg_args))

        ai_flags = self.address_info_flags | socket.AI_PASSIVE
        self.sock = None
        self._used_addr_family = None
        self._used_socket_type = None
        self._used_protocol = None
        self._used_socket_addr = None
        self._resolved_address = None
        self._own_address = None
        family = None
        socktype = socket.SOCK_STREAM
        proto = socket.IPPROTO_TCP
        sockaddr = None

        addresses = self.get_address(
            self.address, port=self.port, addr_type=socktype,
            flags=ai_flags, as_socket_address=True)

        if not addresses:
            msg = _('No valid address for host {!r} found.').format(str(self.address))
            raise CouldNotOpenTcpSocketError(msg)

        last_err_msg = None
        can_not_bind_msg = 'Could not open listening TCP socket on {addr!r}, port {port}:'

        for socketaddr in addresses:
            ip_addr = ipaddress.ip_address(socketaddr[0])
            if ip_addr.version == 4:
                family = socket.AF_INET
            else:
                family = socket.AF_INET6

            try:
                self.sock = socket.socket(family, socktype, proto)
            except socket.error as msg:
                if self.verbose > 3:
                    LOG.debug('Could not create TCP socket: {}'.format(msg))
                last_err_msg = str(msg)
                self.sock = None
                continue

            try:
                self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                self.sock.bind(sockaddr)
                self.sock.listen(self.request_queue_size)
            except socket.error as msg:
                self.sock.close()
                if self.verbose > 3:
                    LOG.debug(can_not_bind_msg.format(**msg_args) + ' ' + str(msg))
                last_err_msg = str(msg)
                self.sock = None
                continue

            # precedence for IPv6
            if family == socket.AF_INET6:
                break

        # Could not open listening socket
        if self.sock is None:
            msg = can_not_bind_msg.format(**msg_args) + ' ' + str(last_err_msg)
            raise CouldNotOpenTcpSocketError(msg)

        self._bonded = True
        self._connected = True
        self.fileno = self.sock.fileno()
        self._used_addr_family = family
        self._used_socket_type = socktype
        self._used_protocol = proto
        self._used_socket_addr = sockaddr
        self._resolved_address = sockaddr[0]
        self._own_address = self.sock.getsockname()


# =============================================================================

if __name__ == '__main__':

    pass

# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
