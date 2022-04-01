#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: Frank Brehm
@contact: frank@brehm-online.com
@copyright: © 2022 by Frank Brehm, Berlin
@summary: A module for a pidfile object.
          It provides methods to define, check, create
          and remove a pidfile.
"""
from __future__ import absolute_import

# Standard modules
import os
import sys
import logging

import re
import signal
import errno

# Third party modules
import six
from six import reraise

# Own modules
from .errors import ReadTimeoutError
from .common import to_utf8
from .obj import FbBaseObjectError, FbBaseObject

from .xlate import XLATOR

__version__ = '0.3.2'

LOG = logging.getLogger(__name__)

_ = XLATOR.gettext


# =============================================================================
class PidFileError(FbBaseObjectError):
    """Base error class for all exceptions happened during
    handling a pidfile."""

    pass


# =============================================================================
class InvalidPidFileError(PidFileError):
    """An error class indicating, that the given pidfile is unusable"""

    def __init__(self, pidfile, reason=None):
        """
        Constructor.

        @param pidfile: the filename of the invalid pidfile.
        @type pidfile: str
        @param reason: the reason, why the pidfile is invalid.
        @type reason: str

        """

        self.pidfile = pidfile
        self.reason = reason

    # -------------------------------------------------------------------------
    def __str__(self):
        """Typecasting into a string for error output."""

        msg = None
        if self.reason:
            msg = _("Invalid pidfile {f!r} given: {r}").format(
                f=self.pidfile, r=self.reason)
        else:
            msg = _("Invalid pidfile {!r} given.").format(self.pidfile)

        return msg

# =============================================================================
class PidFileInUseError(PidFileError):
    """
    An error class indicating, that the given pidfile is in use
    by another application.
    """

    def __init__(self, pidfile, pid):
        """
        Constructor.

        @param pidfile: the filename of the pidfile.
        @type pidfile: str
        @param pid: the PID of the process owning the pidfile
        @type pid: int

        """

        self.pidfile = pidfile
        self.pid = pid

    # -------------------------------------------------------------------------
    def __str__(self):
        """Typecasting into a string for error output."""

        msg = _(
            "The pidfile {f!r} is currently in use by the application with the PID {p}.").format(
            f=self.pidfile, p=self.pid)

        return msg


# =============================================================================
class PidFile(FbBaseObject):
    """
    Base class for a pidfile object.
    """

    open_args = {}
    if six.PY3:
        open_args = {
            'encoding': 'utf-8',
            'errors': 'surrogateescape',
        }

    # -------------------------------------------------------------------------
    def __init__(
        self, filename, auto_remove=True, appname=None, verbose=0,
            version=__version__, base_dir=None,
            initialized=False, simulate=False, timeout=10):
        """
        Initialisation of the pidfile object.

        @raise ValueError: no filename was given
        @raise PidFileError: on some errors.

        @param filename: the filename of the pidfile
        @type filename: str
        @param auto_remove: Remove the self created pidfile on destroying
                            the current object
        @type auto_remove: bool
        @param appname: name of the current running application
        @type appname: str
        @param verbose: verbose level
        @type verbose: int
        @param version: the version string of the current object or application
        @type version: str
        @param base_dir: the base directory of all operations
        @type base_dir: str
        @param initialized: initialisation is complete after __init__()
                            of this object
        @type initialized: bool
        @param simulate: simulation mode
        @type simulate: bool
        @param timeout: timeout in seconds for IO operations on pidfile
        @type timeout: int

        @return: None
        """

        self._created = False
        """
        @ivar: the pidfile was created by this current object
        @type: bool
        """

        super(PidFile, self).__init__(
            appname=appname,
            verbose=verbose,
            version=version,
            base_dir=base_dir,
            initialized=False,
        )

        if not filename:
            raise ValueError(_(
                'No filename given on initializing {} object.').format('PidFile'))

        self._filename = os.path.abspath(str(filename))
        """
        @ivar: The filename of the pidfile
        @type: str
        """

        self._auto_remove = bool(auto_remove)
        """
        @ivar: Remove the self created pidfile on destroying the current object
        @type: bool
        """

        self._simulate = bool(simulate)
        """
        @ivar: Simulation mode
        @type: bool
        """

        self._timeout = int(timeout)
        """
        @ivar: timeout in seconds for IO operations on pidfile
        @type: int
        """

    # -----------------------------------------------------------
    @property
    def filename(self):
        """The filename of the pidfile."""
        return self._filename

    # -----------------------------------------------------------
    @property
    def auto_remove(self):
        """Remove the self created pidfile on destroying the current object."""
        return self._auto_remove

    @auto_remove.setter
    def auto_remove(self, value):
        self._auto_remove = bool(value)

    # -----------------------------------------------------------
    @property
    def simulate(self):
        """Simulation mode."""
        return self._simulate

    # -----------------------------------------------------------
    @property
    def created(self):
        """The pidfile was created by this current object."""
        return self._created

    # -----------------------------------------------------------
    @property
    def timeout(self):
        """The timeout in seconds for IO operations on pidfile."""
        return self._timeout

    # -----------------------------------------------------------
    @property
    def parent_dir(self):
        """The directory containing the pidfile."""
        return os.path.dirname(self.filename)

    # -------------------------------------------------------------------------
    def as_dict(self, short=True):
        """
        Transforms the elements of the object into a dict

        @param short: don't include local properties in resulting dict.
        @type short: bool

        @return: structure as dict
        @rtype:  dict
        """

        res = super(PidFile, self).as_dict(short=short)
        res['filename'] = self.filename
        res['auto_remove'] = self.auto_remove
        res['simulate'] = self.simulate
        res['created'] = self.created
        res['timeout'] = self.timeout
        res['parent_dir'] = self.parent_dir
        res['open_args'] = self.open_args

        return res

    # -------------------------------------------------------------------------
    def __repr__(self):
        """Typecasting into a string for reproduction."""

        out = "<%s(" % (self.__class__.__name__)

        fields = []
        fields.append("filename=%r" % (self.filename))
        fields.append("auto_remove=%r" % (self.auto_remove))
        fields.append("appname=%r" % (self.appname))
        fields.append("verbose=%r" % (self.verbose))
        fields.append("base_dir=%r" % (self.base_dir))
        fields.append("initialized=%r" % (self.initialized))
        fields.append("simulate=%r" % (self.simulate))
        fields.append("timeout=%r" % (self.timeout))

        out += ", ".join(fields) + ")>"
        return out

    # -------------------------------------------------------------------------
    def __del__(self):
        """Destructor. Removes the pidfile, if it was created by ourselfes."""

        if not self.created:
            return

        if not os.path.exists(self.filename):
            if self.verbose > 3:
                LOG.debug(_("Pidfile {!r} doesn't exists, not removing.").format(self.filename))
            return

        if not self.auto_remove:
            if self.verbose > 3:
                LOG.debug(_("Auto removing disabled, don't deleting {!r}.").format(self.filename))
            return

        if self.verbose > 1:
            LOG.debug(_("Removing pidfile {!r} ...").format(self.filename))
        if self.simulate:
            if self.verbose > 1:
                LOG.debug(_("Just kidding ..."))
            return
        try:
            os.remove(self.filename)
        except OSError as e:
            LOG.err(_("Could not delete pidfile {f!r}: {e}").format(f=self.filename, e=e))
        except Exception as e:
            self.handle_error(str(e), e.__class__.__name__, True)

    # -------------------------------------------------------------------------
    def create(self, pid=None):
        """
        The main method of this class. It tries to write the PID of the process
        into the pidfile.

        @param pid: the pid to write into the pidfile. If not given, the PID of
                    the current process will taken.
        @type pid: int

        """

        if pid:
            pid = int(pid)
            if pid <= 0:
                msg = _("Invalid PID {p} for creating pidfile {f!r} given.").format(
                    p=pid, f=self.filename)
                raise PidFileError(msg)
        else:
            pid = os.getpid()

        if self.check():

            LOG.info(_("Deleting pidfile {!r} ...").format(self.filename))
            if self.simulate:
                LOG.debug(_("Just kidding ..."))
            else:
                try:
                    os.remove(self.filename)
                except OSError as e:
                    raise InvalidPidFileError(self.filename, str(e))

        if self.verbose > 1:
            LOG.debug(_("Trying opening {!r} exclusive ...").format(self.filename))

        if self.simulate:
            LOG.debug(_("Simulation mode - don't real writing in {!r}.").format(self.filename))
            self._created = True
            return

        fd = None
        try:
            fd = os.open(
                self.filename, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
        except OSError as e:
            error_tuple = sys.exc_info()
            msg = _("Error on creating pidfile {f!r}: {e}").format(f=self.filename, e=e)
            reraise(PidFileError, msg, error_tuple[2])

        if self.verbose > 2:
            LOG.debug(_("Writing {p} into {f!r} ...").format(p=pid, f=self.filename))

        out = to_utf8("%d\n" % (pid))
        try:
            os.write(fd, out)
        finally:
            os.close(fd)

        self._created = True

    # -------------------------------------------------------------------------
    def recreate(self, pid=None):
        """
        Rewrites an even created pidfile with the current PID.

        @param pid: the pid to write into the pidfile. If not given, the PID of
                    the current process will taken.
        @type pid: int

        """

        if not self.created:
            msg = _("Calling {} on a not self created pidfile.").format('recreate()')
            raise PidFileError(msg)

        if pid:
            pid = int(pid)
            if pid <= 0:
                msg = "Invalid PID {p} for creating pidfile {f!r} given.".format(
                    p=pid, f=self.filename)
                raise PidFileError(msg)
        else:
            pid = os.getpid()

        if self.verbose > 1:
            LOG.debug(_("Trying opening {!r} for recreate ...").format(self.filename))

        if self.simulate:
            LOG.debug(_("Simulation mode - don't real writing in {!r}.").format(self.filename))
            return

        fh = None
        try:
            fh = open(self.filename, 'w', **self.open_args)
        except OSError as e:
            error_tuple = sys.exc_info()
            msg = _("Error on recreating pidfile {f!r}: {e}").format(f=self.filename, e=e)
            reraise(PidFileError, msg, error_tuple[2])

        if self.verbose > 2:
            LOG.debug(_("Writing {p} into {f!r} ...").format(p=pid, f=self.filename))

        try:
            fh.write("%d\n" % (pid))
        finally:
            fh.close()

    # -------------------------------------------------------------------------
    def check(self):
        """
        This methods checks the usability of the pidfile.
        If the method doesn't raise an exception, the pidfile is usable.

        It returns, whether the pidfile exist and can be deleted or not.

        @raise InvalidPidFileError: if the pidfile is unusable
        @raise PidFileInUseError: if the pidfile is in use by another application
        @raise ReadTimeoutError: on timeout reading an existing pidfile
        @raise OSError: on some other reasons, why the existing pidfile
                        couldn't be read

        @return: the pidfile exists, but can be deleted - or it doesn't
                 exists.
        @rtype: bool

        """

        if not os.path.exists(self.filename):
            if not os.path.exists(self.parent_dir):
                reason = _("Pidfile parent directory {!r} doesn't exists.").format(
                    self.parent_dir)
                raise InvalidPidFileError(self.filename, reason)
            if not os.path.isdir(self.parent_dir):
                reason = _("Pidfile parent directory {!r} is not a directory.").format(
                    self.parent_dir)
                raise InvalidPidFileError(self.filename, reason)
            if not os.access(self.parent_dir, os.X_OK):
                reason = _("No write access to pidfile parent directory {!r}.").format(
                    self.parent_dir)
                raise InvalidPidFileError(self.filename, reason)

            return False

        if not os.path.isfile(self.filename):
            reason = _("It is not a regular file.")
            raise InvalidPidFileError(self.filename, self.parent_dir)

        # ---------
        def pidfile_read_alarm_caller(signum, sigframe):
            """
            This nested function will be called in event of a timeout.

            @param signum: the signal number (POSIX) which happend
            @type signum: int
            @param sigframe: the frame of the signal
            @type sigframe: object
            """

            return ReadTimeoutError(self.timeout, self.filename)

        if self.verbose > 1:
            LOG.debug(_("Reading content of pidfile {!r} ...").format(self.filename))

        signal.signal(signal.SIGALRM, pidfile_read_alarm_caller)
        signal.alarm(self.timeout)

        content = ''
        fh = None

        try:
            fh = open(self.filename, 'r')
            for line in fh.readlines():
                content += line
        finally:
            if fh:
                fh.close()
            signal.alarm(0)

        # Performing content of pidfile

        pid = None
        line = content.strip()
        match = re.search(r'^\s*(\d+)\s*$', line)
        if match:
            pid = int(match.group(1))
        else:
            msg = _("No useful information found in pidfile {f!r}: {z!r}").format(
                f=self.filename, z=line)
            return True

        if self.verbose > 1:
            LOG.debug(_("Trying check for process with PID {} ...").format(pid))

        try:
            os.kill(pid, 0)
        except OSError as err:
            if err.errno == errno.ESRCH:
                LOG.info(_("Process with PID {} anonymous died.").format(pid))
                return True
            elif err.errno == errno.EPERM:
                error_tuple = sys.exc_info()
                msg = _("No permission to signal the process {} ...").format(pid)
                reraise(PidFileError, msg, error_tuple[2])
            else:
                error_tuple = sys.exc_info()
                msg = _("Got a {c}: {e}.").format(err.__class__.__name__, err)
                reraise(PidFileError, msg, error_tuple[2])
        else:
            raise PidFileInUseError(self.filename, pid)

        return False


# =============================================================================

if __name__ == "__main__":

    pass

# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 list
