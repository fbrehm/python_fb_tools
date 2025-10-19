#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@summary: Module for a UNIX socket object class.

@author: Frank Brehm
@contact: frank.brehm@profitbricks.com
@copyright: © 2025 by Frank Brehm, Berlin
"""
from __future__ import absolute_import

# Standard modules
import errno
import grp
import logging
import os
import pwd
import socket
import stat
import sys
from pathlib import Path

# Third party modules
from six import reraise

# Own modules
from . import GenericSocket
from ..errors import GenericSocketError
from ..xlate import XLATOR

__version__ = "0.5.2"

LOG = logging.getLogger(__name__)

_ = XLATOR.gettext
ngettext = XLATOR.ngettext

DEFAULT_SOCKET_MODE = stat.S_IFSOCK | stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IWGRP


# =============================================================================
class UnixSocketError(GenericSocketError):
    """Base error class for all special exceptions raised in this module."""

    pass


# =============================================================================
class NoSocketFileError(UnixSocketError):
    """Error class indicating, that the Unix socket file was not found on connecting."""

    # -------------------------------------------------------------------------
    def __init__(self, filename):
        """Initialize the NoSocketFileError exception object."""
        self.filename = filename

    # -----------------------------------------------------
    def __str__(self):
        """Typecast into a string for error output."""
        msg = _("The Unix socket file {!r} was not found.").format(str(self.filename))
        return msg


# =============================================================================
class NoPermissionsToSocketError(UnixSocketError):
    """Error class for having invalid permissions on the Unix socket file."""

    # -------------------------------------------------------------------------
    def __init__(self, filename):
        """Initialize the NoSocketFileError exception object."""
        self.filename = filename

    # -----------------------------------------------------
    def __str__(self):
        """Typecast into a string for error output."""
        msg = _("Invalid permissions to connect to Unix socket {!r}.").format(str(self.filename))
        return msg


# =============================================================================
class UnixSocket(GenericSocket):
    """
    Class for capsulation a UNIX socket.

    Properties:
    * address_family     (str or int        - rw) (inherited from HandlingObject)
    * appname            (str               - rw) (inherited from FbBaseObject)
    * assumed_answer     (None or bool      - rw) (inherited from HandlingObject)
    * auto_remove        (bool              - rw)
    * base_dir           (pathlib.Path      - rw) (inherited from FbBaseObject)
    * bonded             (bool              - ro) (inherited from GenericSocket)
    * buffer_size        (int               - rw) (inherited from GenericSocket)
    * connected          (bool              - ro) (inherited from GenericSocket)
    * encoding           (str               - rw) (inherited from GenericSocket)
    * filename           (pathlib.Path      - rw)
    * fileno             (None or int       - rw) (inherited from GenericSocket)
    * force              (bool              - rw) (inherited from HandlingObject)
    * group_id           (int               - rw)
    * group_name         (str               - ro)
    * initialized        (bool              - rw) (inherited from FbBaseObject)
    * interrupted        (bool              - rw) (inherited from HandlingObject)
    * is_venv            (bool              - ro) (inherited from HandlingObject)
    * mode               (int               - rw)
    * mode_oct           (str               - ro)
    * must_be_absolute   (bool              - ro)
    * owner_id           (int               - rw)
    * owner_name         (str               - ro)
    * was_bonded         (bool              - ro)
    * polling_interval   (float             - rw) (inherited from GenericSocket)
    * prompt_timeout     (int               - rw) (inherited from HandlingObject)
    * quiet              (bool              - rw) (inherited from HandlingObject)
    * request_queue_size (int               - rw) (inherited from GenericSocket)
    * simulate           (bool              - rw) (inherited from HandlingObject)
    * timeout            (float             - rw) (inherited from GenericSocket)
    * verbose            (int               - rw) (inherited from FbBaseObject)
    * version            (str               - ro) (inherited from FbBaseObject)

    Public attributes:
    * add_search_paths       Array of pathlib.Path (inherited from HandlingObject)
    * client_address         object                (inherited from GenericSocket)
    * connection             socket.socket         (inherited from GenericSocket)
    * signals_dont_interrupt Array of int          (inherited from HandlingObject)
    * sock                   socket                (inherited from GenericSocket)
    """

    default_mode = DEFAULT_SOCKET_MODE

    # -------------------------------------------------------------------------
    def __init__(
        self,
        filename,
        mode=None,
        owner=None,
        group=None,
        auto_remove=True,
        must_be_absolute=True,
        version=__version__,
        *args,
        **kwargs,
    ):
        """
        Initialise of the UnixSocket object.

        @raise UnixSocketError: on a uncoverable error.

        @param filename: the filename of the socket, that should be used
        @type filename: pathlib.Path or str
        @param mode: The creation mode of the scstadm communication socket.
        @type mode: int
        @param owner: The owning user of the scstadm communication socket
        @type owner: str or int or None
        @param group: The owning group of the scstadm communication socket
        @type group: str or int or None
        @param auto_remove: Remove the self created socket file on destroying the current object
        @type auto_remove: bool
        @param must_be_absolute: if true, raise an exception if the given filename is not absolute
        @type must_be_absolute: bool
        @param version: the version string of the current object or application
        @type version: str

        @param appname: name of the current running application
        @type appname: str
        @param assumed_answer: The assumed answer to all yes/no questions.
        @type assumed_answer: bool or None
        @param base_dir: base directory used for different purposes
        @type base_dir: str or pathlib.Path
        @param buffer_size: The size of the buffer for receiving data from sockets
        @type buffer_size: int
        @param encoding: The used encoding for Byte-Strings.
        @type encoding: str or None
        @param force: Forced execution of something
        @type force: bool
        @param initialized: initialisation of this object is complete after init
        @type initialized: bool
        @param polling_interval: The interval in seconds between polling attempts from socket
        @type polling_interval: float or None
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

        @return: None
        """
        self._filename = None
        self._mode = self.default_mode
        self._owner_id = os.geteuid()
        self._owner_name = None
        self._group_id = os.getegid()
        self._group_name = None
        self._auto_remove = bool(auto_remove)
        self._must_be_absolute = bool(must_be_absolute)

        super(UnixSocket, self).__init__(
            *args,
            version=version,
            **kwargs,
        )

        self.filename = filename
        self.mode = mode

        if owner is None:
            self.owner_id = os.geteuid()
        else:
            self.owner_id = owner

        if group is None:
            self.group_id = os.getegid()
        else:
            self.group_id = group

        self._was_bonded = False

        # Create an UDS socket
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

    # -----------------------------------------------------------
    @property
    def filename(self):
        """Return the filename of the socket, that should be used."""
        return self._filename

    @filename.setter
    def filename(self, value):
        if value is None:
            msg = _("A UNIX socket filename may not be None.")
            raise UnixSocketError(msg)

        path = Path(value)
        if self.must_be_absolute and not path.is_absolute():
            msg = _("The UNIX socket filename {!r} must be an absolute filename.")
            raise UnixSocketError(msg.format(str(path)))

        self._filename = path

    # -----------------------------------------------------------
    @property
    def mode(self):
        """Return the creation mode of the UNIX socket file as an integer."""
        return self._mode

    @mode.setter
    def mode(self, value):
        if value is None:
            self._mode = self.default_mode
            return

        try:
            mode = int(value)
        except (TypeError, ValueError) as e:
            msg = _("Wrong socket mode {!r}:") + format(value)
            msg += " " + str(e)
            raise UnixSocketError(msg)

        mask = stat.S_IFSOCK | stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO
        self._mode = (mode | stat.S_IFSOCK) & mask

    # -----------------------------------------------------------
    @property
    def mode_oct(self):
        """Return the creation mode of the socket file as stringified octal number."""
        return "{:6o}".format(self.mode)

    # -----------------------------------------------------------
    @property
    def owner_id(self):
        """Return the numeric UID of the owning user of the UNIX socket file."""
        return self._owner_id

    @owner_id.setter
    def owner_id(self, value):
        uid = os.geteuid()
        owner = uid
        try:
            entry = pwd.getpwuid(uid)
            owner = entry.pw_name
        except KeyError:
            pass

        if value is None:
            self._owner_id = uid
            self._owner_name = owner
            return

        if isinstance(value, int):
            if value < 0:
                msg = _("Invalid UID {!r} for socket owner given.").format(value)
                raise UnixSocketError(msg)
            self._owner_id = value
            owner = value
            try:
                entry = pwd.getpwuid(value)
                owner = entry.pw_name
            except KeyError:
                pass
            self._owner_name = owner
            return

        owner = str(value)
        uid = None
        try:
            entry = pwd.getpwnam(owner)
            uid = entry.pw_uid
        except KeyError:
            msg = _("Username {!r} as the owner for the UNIX socket file not found.")
            raise UnixSocketError(msg.format(owner))

        self._owner_id = uid
        self._owner_name = owner

    # -----------------------------------------------------------
    @property
    def owner_name(self):
        """Return the textual user name of the owning user of the UNIX ocket file."""
        return self._owner_name

    # -----------------------------------------------------------
    @property
    def group_id(self):
        """Return the numeric GID of the group of the UNIX socket file."""
        return self._group_id

    @group_id.setter
    def group_id(self, value):
        gid = os.getegid()
        group = gid
        try:
            entry = grp.getgrgid(gid)
            group = entry.gr_name
        except KeyError:
            pass

        if value is None:
            self._group_id = gid
            self._group_name = group
            return

        if isinstance(value, int):
            if value < 0:
                msg = _("Invalid GID {!r} for socket file group given.").format(value)
                raise UnixSocketError(msg)
            self._group_id = value
            group = value
            try:
                entry = grp.getgrgid(gid)
                group = entry.gr_name
            except KeyError:
                pass
            self._group_name = group
            return

        group = str(value)
        gid = None
        try:
            entry = grp.getgrnam(group)
            gid = entry.gr_name
        except KeyError:
            msg = _("Groupname {!r} as the group for the UNIX socket file not found.")
            raise UnixSocketError(msg.format(value))

        self._group_id = gid
        self._group_name = group

    # -----------------------------------------------------------
    @property
    def group_name(self):
        """Return the textual groupname of the owning groupof the UNIX ocket file."""
        return self._group_name

    # -----------------------------------------------------------
    @property
    def auto_remove(self):
        """Remove the self created socket file on destroying the current object."""
        return self._auto_remove

    @auto_remove.setter
    def auto_remove(self, value):
        self._auto_remove = bool(value)

    # -----------------------------------------------------------
    @property
    def must_be_absolute(self):
        """Return, whether the socket file name must be an absolute file name."""
        return getattr(self, "_must_be_absolute", True)

    # -----------------------------------------------------------
    @property
    def was_bonded(self):
        """Flag, that the socket was bonded by the current object."""
        return getattr(self, "_was_bonded", False)

    # -------------------------------------------------------------------------
    def as_dict(self, short=False):
        """
        Transform the elements of the object into a dict.

        @return: structure as dict
        @rtype:  dict
        """
        res = super(UnixSocket, self).as_dict(short=short)

        res["auto_remove"] = self.auto_remove
        res["filename"] = self.filename
        res["group_id"] = self.group_id
        res["group_name"] = self.group_name
        res["mode"] = self.mode
        res["mode_oct"] = self.mode_oct
        res["must_be_absolute"] = self.must_be_absolute
        res["owner_id"] = self.owner_id
        res["owner_name"] = self.owner_name
        res["was_bonded"] = self.was_bonded

        return res

    # -------------------------------------------------------------------------
    def socket_desc(self):
        """Return a textual description of the used socket."""
        return "file://{}".format(self.filename)

    # -------------------------------------------------------------------------
    def close(self):
        """Close the current socket."""
        super(UnixSocket, self).close()

        if self.was_bonded and self.filename.exists() and self.auto_remove:
            if self.verbose > 1:
                LOG.debug(_("Removing socket file {!r} ...").format(str(self.filename)))
            self.filename.unlink()

        self.fileno = None

    # -------------------------------------------------------------------------
    def connect(self):
        """Connect to the saved socket as a client."""
        if self.verbose > 1:
            LOG.debug(_("Connecting to Unix Domain Socket {!r} ...").format(str(self.filename)))

        if self.connected:
            msg = _("The socket is already connected to {!r} ...").format(str(self.filename))
            raise UnixSocketError(msg)

        if self.bonded:
            msg = _("The application is already bonded to {!r} ...").format(str(self.filename))
            raise UnixSocketError(msg)

        try:
            self.sock.connect(str(self.filename))
        except socket.error as e:
            error_tuple = sys.exc_info()
            if e.errno == errno.ENOENT:
                raise NoSocketFileError(self.filename)
            if e.errno == errno.EACCES:
                raise NoPermissionsToSocketError(self.filename)
            msg = _("Error connecting to Unix Socket {sock!r}: {e}").format(
                sock=str(self.filename), e=e
            )
            reraise(UnixSocketError, msg, error_tuple[2])

        self._connected = True
        self.fileno = self.sock.fileno()

    # -------------------------------------------------------------------------
    def _set_socket_permissions(self):
        """Set file mode, owner and group to the socket file."""
        sock_stat = self.filename.stat()

        if self.mode is not None and sock_stat.st_mode != self.mode:
            if self.verbose > 1:
                LOG.debug(
                    _("Setting permissions of {sock!r} to 0o{mode} ...").format(
                        sock=str(self.filename), mode=self.mode_oct
                    )
                )
            self.filename.chmod(self.mode)

        do_chown = False

        if self.owner_id is not None and sock_stat.st_uid != self.owner_id:
            do_chown = True

        if self.group_id is not None and sock_stat.st_gid != self.group_id:
            do_chown = True

        if do_chown:
            if os.geteuid():
                LOG.warn(_("Only root may change the ownership of a socket."))
                return
            if self.verbose > 1:
                msg = _(
                    "Setting owner and group of {sock!r} to {uid}:{gid} " "({owner}:{group}) ..."
                ).format(
                    sock=str(self.filename),
                    uid=self.self.owner_id,
                    gid=self.group_id,
                    owner=self.owner_name,
                    group=self.group_name,
                )
                LOG.debug(msg)
            os.chown(self.filename, self.owner_id, self.group_id)

    # -------------------------------------------------------------------------
    def bind(self):
        """Create the socket and listen on it."""
        if self.verbose > 1:
            LOG.debug(_("Creating and bind to Unix Socket {!r} ...").format(str(self.filename)))

        if self.connected:
            msg = _("The socket is already connected to {!r} ...").format(str(self.filename))
            raise UnixSocketError(msg)

        if self.bonded:
            msg = _("The application is already bonded to {!r} ...").format(str(self.filename))
            raise UnixSocketError(msg)

        self.sock.bind(str(self.filename))

        if not self.filename.exists():
            raise NoSocketFileError(self.filename)

        self._bonded = True
        self._was_bonded = True
        self.fileno = self.sock.fileno()

        self._set_socket_permissions()

        if self.verbose > 2:
            LOG.debug(
                _("Start listening on socket with a queue size of {}.").format(
                    self.request_queue_size
                )
            )
        self.sock.listen(self.request_queue_size)


# =============================================================================

if __name__ == "__main__":

    pass

# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 list
