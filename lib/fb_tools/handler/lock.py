#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@summary: Module for a extended handler module, which has additional methods for locking.

@author: Frank Brehm
@contact: frank.brehm@pixelpark.com
@copyright: © 2021 by Frank Brehm, Berlin
"""
from __future__ import absolute_import

# Standard modules
import sys
import os
import logging
import time
import errno
import traceback
import datetime
import fcntl

try:
    from pathlib import Path
except ImportError:
    from pathlib2 import Path

from numbers import Number

# Third party modules
from six import reraise

# Own modules
from ..common import to_utf8
from ..errors import CouldntOccupyLockfileError, HandlerError
from ..obj import FbBaseObject
from ..xlate import XLATOR
from . import BaseHandler

__version__ = '2.0.1'

LOG = logging.getLogger(__name__)

# Module variables
DEFAULT_LOCKRETRY_DELAY_START = 0.1
DEFAULT_LOCKRETRY_DELAY_INCREASE = 0.2
DEFAULT_LOCKRETRY_MAX_DELAY = 10
DEFAULT_MAX_LOCKFILE_AGE = 300
DEFAULT_LOCKING_USE_PID = True

_ = XLATOR.gettext
ngettext = XLATOR.ngettext


# =============================================================================
class LockHandlerError(HandlerError):
    """
    General exception class.

    Base exception class for all exceptions belonging to locking issues
    in this module
    """

    pass


# =============================================================================
class LockObjectError(LockHandlerError):
    """
    General exception class for LockObject.

    Special exception class for exceptions raising inside methods of
    the LockObject.
    """

    pass


# =============================================================================
class LockdirNotExistsError(LockHandlerError):
    """
    Exception class for not existing lockdir.

    Exception class for the case, that the parent directory of the lockfile
    (lockdir) doesn't exists.
    """

    # -------------------------------------------------------------------------
    def __init__(self, lockdir):
        """
        Create a LockdirNotExistsError object..

        @param lockdir: the directory, wich doesn't exists.
        @type lockdir: str

        """
        self.lockdir = lockdir

    # -------------------------------------------------------------------------
    def __str__(self):
        """Typecaste into a string for error output."""
        return _("Locking directory {!r} doesn't exists or is not a directory.").format(
            str(self.lockdir))


# =============================================================================
class LockdirNotWriteableError(LockHandlerError):
    """
    Exception class for not writeable directoriy.

    Exception class for the case, that the parent directory of the lockfile
    (lockdir) isn't writeable for the current process.
    """

    # -------------------------------------------------------------------------
    def __init__(self, lockdir):
        """
        Create an LockdirNotWriteableError object.

        @param lockdir: the directory, wich isn't writeable
        @type lockdir: str

        """
        self.lockdir = lockdir

    # -------------------------------------------------------------------------
    def __str__(self):
        """Typecaste into a string for error output."""
        return _("Locking directory {!r} isn't writeable.").format(
            str(self.lockdir))


# =============================================================================
class LockObject(FbBaseObject):
    """
    Capsulation class as a result of a successful lock action.

    It contains all important informations about the lock.

    It can be used for holding these informations and, if desired, to remove
    the lock automatically, if the current instance of LockObject is removed.

    """

    # -------------------------------------------------------------------------
    def __init__(
        self, lockfile, ctime=None, mtime=None, fcontent=None, fd=None, simulate=False,
            autoremove=False, appname=None, verbose=0, version=__version__,
            base_dir=None, silent=False):
        """
        Initialise a LockObject object.

        @raise LockObjectError: on a uncoverable error.

        @param lockfile: the file, which represents the lock, must exists
        @type lockfile: str
        @param ctime: the creation time of the lockfile
        @type ctime: datetime
        @param mtime: the modification time of the lockfile
        @type mtime: datetime
        @param fcontent: the content of the lockfile
        @type fcontent: str
        @param fd: The numeric file descriptor of the lockfile, if opened, if not opened, then None
        @type fd: int or None
        @param simulate: don't execute actions, only display them
        @type simulate: bool
        @param autoremove: removing the lockfile on deleting the current object
        @type autoremove: bool
        @param appname: name of the current running application
        @type appname: str
        @param verbose: verbose level
        @type verbose: int
        @param version: the version string of the current object or application
        @type version: str
        @param base_dir: the base directory of all operations
        @type base_dir: str
        @param silent: Remove silently the lockfile (except on verbose level >= 2)
        @type silent: bool

        @return: None
        """
        self._fd = None

        super(LockObject, self).__init__(
            appname=appname, verbose=verbose, version=version,
            base_dir=base_dir, initialized=False,
        )

        self._simulate = bool(simulate)
        self._autoremove = bool(autoremove)
        self._silent = bool(silent)

        if not lockfile:
            raise LockObjectError(_("No lockfile given on init of a LockObject object."))

        lfile = Path(lockfile)

        if not lfile.exists():
            if self.simulate:
                LOG.info(_(
                    "Lockfile {!r} doesn't exists, but don't worry, "
                    "it's simulation mode.").format(str(lockfile)))
            else:
                raise LockObjectError(_("Lockfile {!r} doesn't exists.").format(str(lockfile)))
        else:
            if not lfile.is_file():
                raise LockObjectError(_(
                    "Lockfile {!r} is not a regular file.").format(str(lockfile)))

        if fd is not None:
            self._fd = fd

        self._lockfile = lfile.resolve()

        self._fcontent = None
        if fcontent is not None:
            self._fcontent = str(fcontent)

        self._ctime = ctime
        self._mtime = mtime

        # Detecting self._ctime and self._mtime from filestat of the lockfile
        if not self.ctime or not self.mtime:
            if lfile.exists():
                fstat = self.stat()
                if not self.ctime:
                    self._ctime = datetime.datetime.utcfromtimestamp(fstat.st_ctime)
                if not self.mtime:
                    self._mtime = datetime.datetime.utcfromtimestamp(fstat.st_mtime)
            else:
                if not self.ctime:
                    self._ctime = datetime.datetime.utcnow()
                if not self.mtime:
                    self._mtime = datetime.datetime.utcnow()

        self.initialized = True

    # -----------------------------------------------------------
    @property
    def lockfile(self):
        """Return the file, which represents the lock."""
        return self._lockfile

    # -----------------------------------------------------------
    @property
    def lockdir(self):
        """Return the parent directory of the lockfile."""
        return self.lockfile.parent

    # -----------------------------------------------------------
    @property
    def ctime(self):
        """Return the creation time of the lockfile."""
        return self._ctime

    # -----------------------------------------------------------
    @property
    def mtime(self):
        """Return the last modification time of the lockfile."""
        return self._mtime

    # -----------------------------------------------------------
    @property
    def fcontent(self):
        """Return the content of the lockfile."""
        return self._fcontent

    # -----------------------------------------------------------
    @property
    def fd(self):
        """Return the numeric file descriptor of the lockfile."""
        return self._fd

    # -----------------------------------------------------------
    @property
    def simulate(self):
        """Do not execute actions, only display them."""
        return self._simulate

    @simulate.setter
    def simulate(self, value):
        self._simulate = bool(value)

    # -----------------------------------------------------------
    @property
    def autoremove(self):
        """Remove the lockfile on deleting the current object."""
        return self._autoremove

    @autoremove.setter
    def autoremove(self, value):
        self._autoremove = bool(value)

    # -----------------------------------------------------------
    @property
    def silent(self):
        """Remove silently the lockfile (except on verbose level >= 2)."""
        return self._silent

    @silent.setter
    def silent(self, value):
        self._silent = bool(value)

    # -------------------------------------------------------------------------
    def as_dict(self, short=True):
        """
        Transform the elements of the object into a dict.

        @param short: don't include local properties in resulting dict.
        @type short: bool

        @return: structure as dict
        @rtype:  dict
        """
        res = super(LockObject, self).as_dict(short=short)
        res['lockfile'] = self.lockfile
        res['lockdir'] = self.lockdir
        res['ctime'] = self.ctime
        res['mtime'] = self.mtime
        res['fcontent'] = self.fcontent
        res['simulate'] = self.simulate
        res['autoremove'] = self.autoremove
        res['silent'] = self.silent
        res['fd'] = self.fd

        return res

    # -------------------------------------------------------------------------
    def __repr__(self):
        """Typecast  the current objectinto a string for reproduction."""
        out = super(LockObject, self).__repr__()[:-2]

        fields = []
        fields.append("lockfile={!r}".format(self.lockfile))
        if self.fcontent:
            fields.append("fcontent={!r}".format(self.fcontent))
        fields.append("ctime={!r}".format(self.ctime))
        fields.append("mtime={!r}".format(self.mtime))
        fields.append("fcontent={!r}".format(self.fcontent))
        fields.append("fd={!r}".format(self.fd))
        fields.append("simulate={!r}".format(self.simulate))
        fields.append("autoremove={!r}".format(self.autoremove))
        fields.append("silent={!r}".format(self.silent))

        if fields:
            out += ', ' + ", ".join(fields)
        out += ")>"
        return out

    # -------------------------------------------------------------------------
    def __del__(self):
        """Delete this object - a destructor.

        Removes the lockfile, if self.autoremove is True

        """
        if not getattr(self, '_initialized', False):
            return

        if self.fd is not None:
            msg = _("Closing file descriptor {} ...").format(self.fd)
            if self.silent:
                if self.verbose >= 2:
                    LOG.debug(msg)
            else:
                LOG.debug(msg)
            os.close(self.fd)
            self._fd = None

        if self.autoremove and self.exists:

            msg = _("Automatic removing of {!r} ...").format(self.lockfile)
            if self.silent:
                if self.verbose >= 2:
                    LOG.debug(msg)
            else:
                LOG.info(msg)

            if not self.simulate:
                self.lockfile.unlink()

    # -------------------------------------------------------------------------
    def exists(self):
        """Return, whether the lockfile exists or not."""
        if self.simulate:
            return True

        return self.lockfile.exists()

    # -------------------------------------------------------------------------
    def stat(self):
        """Return the path information of the lockfile (like os.stat)."""
        if not self.exists():
            return None
        return self.lockfile.stat()

    # -------------------------------------------------------------------------
    def refresh(self):
        """Refresh the atime and mtime of the lockfile to the current time."""
        msg = _("Refreshing atime and mtime of {!r} to the current timestamp.").format(
            str(self.lockfile))
        LOG.debug(msg)

        if not self.simulate:
            os.utime(str(self.lockfile), None)

        self._mtime = datetime.datetime.utcfromtimestamp(self.stat().st_mtime)


# =============================================================================
class LockHandler(BaseHandler):
    """A handler class for locking.

    Handler class with additional properties and methods to create,
    check and remove lock files.
    """

    # -------------------------------------------------------------------------
    def __init__(
        self, lockdir=None,
            lockretry_delay_start=DEFAULT_LOCKRETRY_DELAY_START,
            lockretry_delay_increase=DEFAULT_LOCKRETRY_DELAY_INCREASE,
            lockretry_max_delay=DEFAULT_LOCKRETRY_MAX_DELAY,
            max_lockfile_age=DEFAULT_MAX_LOCKFILE_AGE,
            locking_use_pid=DEFAULT_LOCKING_USE_PID,
            stay_opened=True, appname=None, verbose=0, version=__version__, base_dir=None,
            simulate=False, sudo=False, quiet=False, silent=False, *targs, **kwargs):
        """Initialise the locking handler object.

        @raise LockdirNotExistsError: if the lockdir (or base_dir) doesn't exists
        @raise LockHandlerError: on a uncoverable error.

        @param lockdir: a special directory for searching and creating the
                        lockfiles, if not given, self.base_dir will used
        @type lockdir: str
        @param lockretry_delay_start: the first delay in seconds after an
                                      unsuccessful lockfile creation
        @type lockretry_delay_start: Number
        @param lockretry_delay_increase: seconds to increase the delay in every
                                         wait cycle
        @type lockretry_delay_increase: Number
        @param lockretry_max_delay: the total maximum delay in seconds for
                                    trying to create a lockfile
        @type lockretry_max_delay: Number
        @param max_lockfile_age: the maximum age of the lockfile (in seconds),
                                 for the existing lockfile is valid (if
                                 locking_use_pid is False).
        @type max_lockfile_age: Number
        @param locking_use_pid: write the PID of creating process into the
                                fresh created lockfile, if False, the lockfile
                                will be leaved empty, the PID in the lockfile
                                can be used to check the validity of the
                                lockfile
        @type locking_use_pid: bool
        @param stay_opened: should the lockfile stay opened after creation
        @@type stay_opened: bool
        @param appname: name of the current running application
        @type appname: str
        @param verbose: verbose level
        @type verbose: int
        @param version: the version string of the current object or application
        @type version: str
        @param base_dir: the base directory of all operations
        @type base_dir: str
        @param simulate: don't execute actions, only display them
        @type simulate: bool
        @param sudo: should the command executed by sudo by default
        @type sudo: bool
        @param quiet: don't display ouput of action after calling
        @type quiet: bool
        @param silent: Create and remove silently the lockfile (except on verbose level >= 2)
        @type silent: bool

        @return: None

        """
        self._stay_opened = bool(stay_opened)

        super(LockHandler, self).__init__(
            appname=appname, verbose=verbose, version=version, base_dir=base_dir,
            initialized=False, simulate=simulate, sudo=sudo, quiet=quiet,
        )

        self._lockdir = None
        if lockdir is not None:
            self.lockdir = lockdir

        self._lockretry_delay_start = DEFAULT_LOCKRETRY_DELAY_START
        self.lockretry_delay_start = lockretry_delay_start

        self._lockretry_delay_increase = DEFAULT_LOCKRETRY_DELAY_INCREASE
        self.lockretry_delay_increase = lockretry_delay_increase

        self._lockretry_max_delay = DEFAULT_LOCKRETRY_MAX_DELAY
        self.lockretry_max_delay = lockretry_max_delay

        self._max_lockfile_age = DEFAULT_MAX_LOCKFILE_AGE
        self.max_lockfile_age = max_lockfile_age

        self._locking_use_pid = DEFAULT_LOCKING_USE_PID
        self.locking_use_pid = locking_use_pid

        self._silent = bool(silent)

    # -----------------------------------------------------------
    @property
    def lockdir(self):
        """Return the directory for searching and creating the lockfiles."""
        if self._lockdir:
            return self._lockdir
        return self.base_dir

    @lockdir.setter
    def lockdir(self, value):
        if not value:
            self._lockdir = None
            return

        ldir = Path(value)
        if not ldir.is_absolute():
            ldir = self.base_dir / ldir

        self._lockdir = ldir.resolve()

    # -----------------------------------------------------------
    @property
    def lockretry_delay_start(self):
        """Return the first delay in seconds after an unsuccessful lockfile creation."""
        return self._lockretry_delay_start

    @lockretry_delay_start.setter
    def lockretry_delay_start(self, value):
        if not isinstance(value, Number):
            msg = _("Value {val!r} for {what} is not a Number.").format(
                val=value, what='lockretry_delay_start')
            raise LockHandlerError(msg)

        if value <= 0:
            msg = _("The value for {what} must be greater than zero (is {val!r}).").format(
                val=value, what='lockretry_delay_start')
            raise LockHandlerError(msg)

        self._lockretry_delay_start = value

    # -----------------------------------------------------------
    @property
    def lockretry_delay_increase(self):
        """Return the seconds to increase the delay in every wait cycle."""
        return self._lockretry_delay_increase

    @lockretry_delay_increase.setter
    def lockretry_delay_increase(self, value):
        if not isinstance(value, Number):
            msg = _("Value {val!r} for {what} is not a Number.").format(
                val=value, what='lockretry_delay_increase')
            raise LockHandlerError(msg)

        if value < 0:
            msg = _("The value for {what} must be greater than zero (is {val!r}).").format(
                val=value, what='lockretry_delay_increase')
            raise LockHandlerError(msg)

        self._lockretry_delay_increase = value

    # -----------------------------------------------------------
    @property
    def lockretry_max_delay(self):
        """Return ttotal maximum delay in seconds for trying to create a lockfile."""
        return self._lockretry_max_delay

    @lockretry_max_delay.setter
    def lockretry_max_delay(self, value):
        if not isinstance(value, Number):
            msg = _("Value {val!r} for {what} is not a Number.").format(
                val=value, what='lockretry_max_delay')
            raise LockHandlerError(msg)

        if value <= 0:
            msg = _("The value for {what} must be greater than zero (is {val!r}).").format(
                val=value, what='lockretry_max_delay')
            raise LockHandlerError(msg)

        self._lockretry_max_delay = value

    # -----------------------------------------------------------
    @property
    def max_lockfile_age(self):
        """Return the maximum age of the lockfile (in seconds).

        The maximum age of the lockfile (in seconds), for the existing lockfile
        is valid (if locking_use_pid is False).
        """
        return self._max_lockfile_age

    @max_lockfile_age.setter
    def max_lockfile_age(self, value):
        if not isinstance(value, Number):
            msg = _("Value {val!r} for {what} is not a Number.").format(
                val=value, what='max_lockfile_age')
            raise LockHandlerError(msg)

        if value <= 0:
            msg = _("The value for {what} must be greater than zero (is {val!r}).").format(
                val=value, what='max_lockfile_age')
            raise LockHandlerError(msg)

        self._max_lockfile_age = value

    # -----------------------------------------------------------
    @property
    def locking_use_pid(self):
        """Write the PID of creating process into the fresh created lockfile."""
        return self._locking_use_pid

    @locking_use_pid.setter
    def locking_use_pid(self, value):
        self._locking_use_pid = bool(value)

    # -----------------------------------------------------------
    @property
    def stay_opened(self):
        """Return, whether the the lockfile should stay opened after creation.

        If yes, then it will be closed on deleting the LockObject.
        """
        return self._stay_opened

    @stay_opened.setter
    def stay_opened(self, value):
        self._stay_opened = bool(value)

    # -----------------------------------------------------------
    @property
    def silent(self):
        """Create and remove silently the lockfile (except on verbose level >= 2)."""
        return self._silent

    @silent.setter
    def silent(self, value):
        self._silent = bool(value)

    # -------------------------------------------------------------------------
    def as_dict(self, short=True):
        """
        Transform the elements of the object into a dict.

        @param short: don't include local properties in resulting dict.
        @type short: bool

        @return: structure as dict
        @rtype:  dict
        """
        res = super(LockHandler, self).as_dict(short=short)
        res['lockdir'] = self.lockdir
        res['lockretry_delay_start'] = self.lockretry_delay_start
        res['lockretry_delay_increase'] = self.lockretry_delay_increase
        res['lockretry_max_delay'] = self.lockretry_max_delay
        res['max_lockfile_age'] = self.max_lockfile_age
        res['locking_use_pid'] = self.locking_use_pid
        res['silent'] = self.silent
        res['stay_opened'] = self.stay_opened

        return res

    # -------------------------------------------------------------------------
    def __repr__(self):
        """Typecaste into a string for reproduction."""
        out = super(LockHandler, self).__repr__()[:-2]

        fields = []
        if self._lockdir:
            fields.append("lockdir=%r" % (self.lockdir))
        fields.append("lockretry_delay_start=%r" % (self.lockretry_delay_start))
        fields.append("lockretry_delay_increase=%r" % (self.lockretry_delay_increase))
        fields.append("lockretry_max_delay=%r" % (self.lockretry_max_delay))
        fields.append("max_lockfile_age=%r" % (self.max_lockfile_age))
        fields.append("locking_use_pid=%r" % (self.locking_use_pid))
        fields.append("silent=%r" % (self.silent))
        fields.append("stay_opened=%r" % (self.stay_opened))

        if fields:
            out += ', ' + ", ".join(fields)
        out += ")>"
        return out

    # -------------------------------------------------------------------------
    def check_for_number(self, value, default, what, must_gt_zero=False, must_ge_zero=False):
        """Check the given value for a numeric value."""
        if value is None:
            return default

        if not isinstance(value, Number):
            msg = _("Value {val!r} for {what} is not a Number.").format(
                val=value, what=what)
            raise LockHandlerError(msg)

        if must_gt_zero and value <= 0:
            msg = _("The value for {what} must be greater than zero (is {val!r}).").format(
                val=value, what=what)
            raise LockHandlerError(msg)

        if must_ge_zero and value < 0:
            msg = _(
                "The value for {what} must be greater than "
                "or equal to zero (is {val!r}).").format(
                val=value, what=what)
            raise LockHandlerError(msg)

        return value

    # -------------------------------------------------------------------------
    def create_lockfile(
        self, lockfile, delay_start=None, delay_increase=None, max_delay=None,
            use_pid=None, max_age=None, pid=None, raise_on_fail=True, stay_opened=None):
        """
        Try to create the given lockfile exclusive.

        If the lockfile exists and is valid, it waits a total maximum
        of max_delay seconds an increasing amount of seconds to get exclusive
        access to the lockfile.

        @raise CouldntOccupyLockfileError: if the lockfile couldn't occupied
                                           and raise_on_fail is set to True

        @param lockfile: the lockfile to use as a semaphore, if not given
                         as an absolute path, it will be supposed to be
                         relative to self.lockdir.
        @type lockfile: str
        @param delay_start: the first delay in seconds after an unsuccessful
                            lockfile creation, if not given,
                            self.lockretry_delay_start will used.
        @type delay_start: Number (or None)
        @param delay_increase: seconds to increase the delay in every wait
                               cycle, if not given, self.lockretry_delay_increase
                               will used.
        @type delay_increase: Number
        @param max_delay: the total maximum delay in seconds for trying
                          to create a lockfile, if not given,
                          self.lockretry_max_delay will used.
        @type max_delay: Number
        @param use_pid: write the PID of creating process into the fresh
                        created lockfile, if not given, self.locking_use_pid
                        will used.
        @type use_pid: bool
        @param max_age: the maximum age of the lockfile (in seconds), for the
                        existing lockfile is valid (if locking_use_pid is False).
        @type max_age: Number
        @param pid: the pid to write into the lockfile, if use_pid is set
                    to True, if not given, the PID of the current process is used.
        @type pid: int
        @param raise_on_fail: raise an exception instead of returning False, if
                              the lockfile couldn't occupied.
        @type raise_on_fail: bool

        @param stay_opened: should the lockfile stay opened after creation,
        @@type stay_opened: bool or None

        @return: a lock object on success, else None
        @rtype: LockObject or None

        """
        delay_start = self.check_for_number(
            delay_start, self.lockretry_delay_start,
            what='delay_start', must_gt_zero=True)

        delay_increase = self.check_for_number(
            delay_increase, self.lockretry_delay_increase,
            what='delay_increase', must_ge_zero=True)

        max_delay = self.check_for_number(
            max_delay, self.lockretry_max_delay,
            what='max_delay', must_ge_zero=True)

        if use_pid is None:
            use_pid = self.locking_use_pid
        else:
            use_pid = bool(use_pid)

        max_age = self.check_for_number(
            max_age, self.max_lockfile_age,
            what='max_age', must_ge_zero=True)

        if pid is None:
            pid = os.getpid()
        else:
            pid = int(pid)
            if pid <= 0:
                msg = _("Invalid PID {} given on calling create_lockfile().").format(pid)
                raise LockHandlerError(msg)

        lfile = Path(lockfile)
        if not lfile.is_absolute():
            lfile = self.lockdir / lfile

        lockdir = lfile.parent
        if self.verbose > 1:
            LOG.debug(_("Using lock directory {!r} ...").format(str(lockdir)))
        if not lockdir.is_dir():
            raise LockdirNotExistsError(lockdir)

        lfile = lockdir.resolve() / lfile.name
        if lfile.exists():
            lfile = lfile.resolve()

        LOG.debug(_("Trying to lock lockfile {!r} ...").format(str(lockfile)))

        if not os.access(str(lockdir), os.W_OK):
            msg = _("Locking directory {!r} isn't writeable.").format(str(lockdir))
            if self.simulate:
                LOG.error(msg)
            else:
                raise LockdirNotWriteableError(lockdir)

        if stay_opened is None:
            stay_opened = self.stay_opened
        else:
            stay_opened = bool(stay_opened)

        return self._do_create_lockfile(
            lockfile=lfile, delay_start=delay_start, max_delay=max_delay, max_age=max_age,
            delay_increase=delay_increase, pid=pid, use_pid=use_pid, raise_on_fail=raise_on_fail,
            stay_opened=stay_opened)

    # -------------------------------------------------------------------------
    def _do_create_lockfile(
        self, lockfile, delay_start, max_delay, max_age, delay_increase,
            pid, use_pid, raise_on_fail, stay_opened):

        counter = 0
        delay = delay_start

        fd = None
        time_diff = 0
        start_time = time.time()

        # Big try block to ensure closing open file descriptor
        try:

            # Big loop on trying to create the lockfile
            while fd is None and time_diff < max_delay:

                time_diff = time.time() - start_time
                counter += 1

                if self.verbose > 3:
                    LOG.debug(_("Current time difference: {:0.3f} seconds.").format(time_diff))
                if time_diff >= max_delay:
                    break

                # Try creating lockfile exclusive
                LOG.debug(_("Try {try_nr} on creating lockfile {lfile!r} ...").format(
                    try_nr=counter, lfile=str(lockfile)))
                fd = self._create_lockfile(lockfile)
                if fd is not None:
                    # success, then exit
                    break

                # Check for other process, using this lockfile
                if not self.check_lockfile(lockfile, max_age, use_pid):
                    # No other process is using this lockfile
                    if lockfile.exists():
                        LOG.info(_("Removing lockfile {!r} ...").format(str(lockfile)))
                    try:
                        if not self.simulate:
                            lockfile.unlink()
                    except Exception as e:
                        msg = _("Error on removing lockfile {lfile!r}: {err}").format(
                            lfile=str(lockfile), err=e)
                        LOG.error(msg)
                        time.sleep(delay)
                        delay += delay_increase
                        continue

                    fd = self._create_lockfile(lockfile)
                    if fd:
                        break

                # No success, then retry later
                if self.verbose > 2:
                    LOG.debug(_("Sleeping for {:0.1f} seconds.").format(float(delay)))
                time.sleep(delay)
                delay += delay_increase

            # fd is either None, for no success on locking
            if fd is None:
                time_diff = time.time() - start_time
                e = CouldntOccupyLockfileError(lockfile, time_diff, counter)
                if raise_on_fail:
                    raise e
                else:
                    LOG.error(str(e))
                return None

            # or an int for success
            msg = _("Got a lock for lockfile {!r}.").format(str(lockfile))
            if self.silent:
                LOG.debug(msg)
            else:
                LOG.info(msg)
            out = to_utf8("{}\n".format(pid))
            LOG.debug(_("Write {what!r} in lockfile {lfile!r} ...").format(
                what=out, lfile=str(lockfile)))

        finally:

            if fd is not None and not self.simulate:
                os.write(fd, out)

                if stay_opened:
                    LOG.debug(_("Seeking and syncing {!r} ...").format(str(lockfile)))
                    os.lseek(fd, 0, 0)
                    os.fsync(fd)
                else:
                    LOG.debug(_("Closing {!r} ...").format(str(lockfile)))
                    os.close(fd)
                    fd = None

        if fd is not None and self.simulate:
            fd = None

        lock_object = LockObject(
            lockfile, fcontent=out, fd=fd, simulate=self.simulate, appname=self.appname,
            verbose=self.verbose, base_dir=self.base_dir, silent=self.silent,
        )

        return lock_object

    # -------------------------------------------------------------------------
    def _create_lockfile(self, lockfile):
        """
        Handle exclusive the creation of a lockfile.

        @return: a file decriptor of the opened lockfile (if possible),
                 or None, if it isn't.
        @rtype: int or None

        """
        if self.verbose > 1:
            LOG.debug(_("Trying to open {!r} exclusive ...").format(str(lockfile)))
        if self.simulate:
            LOG.debug(_("Simulation mode, no real creation of a lockfile."))
            return -1

        fd = None
        try:
            fd = os.open(str(lockfile), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as e:
            msg = _("Error on creating lockfile {lfile!r}: {err}").format(
                lfile=str(lockfile), err=e)
            if e.errno == errno.EEXIST:
                LOG.debug(msg)
                return None
            else:
                error_tuple = sys.exc_info()
                reraise(LockHandlerError, msg, error_tuple[2])

        return fd

    # -------------------------------------------------------------------------
    def remove_lockfile(self, lockfile):
        """
        Remove the lockfile.

        @param lockfile: the lockfile to remove.
        @type lockfile: str or pathlib.Path

        @return: the lockfile was removed (or not)
        @rtype: bool

        """
        lfile = Path(lockfile)
        if not lfile.is_absolute():
            lfile = self.lockdir / lfile
        lfile = lfile.resolve()

        if not lfile.exists():
            LOG.debug(_("Lockfile {!r} to remove doesn't exists.").format(str(lfile)))
            return True

        LOG.info(_("Removing lockfile {!r} ...").format(str(lfile)))
        if self.simulate:
            LOG.debug(_("Simulation mode - lockfile won't removed."))
            return True

        try:
            lfile.unlink()
        except Exception as e:
            LOG.error(_("Error on removing lockfile {lfile!r}: {err}").format(
                lfile=str(lockfile), err=e))
            if self.verbose:
                tb = traceback.format_exc()
                LOG.debug("Stacktrace:\n" + tb)
            return False

        return True

    # -------------------------------------------------------------------------
    def check_lockfile(self, lockfile, max_age=None, use_pid=None):
        """
        Check the validity of the given lockfile.

        If use_pid is True, and there is a PID inside the lockfile, then
        this PID is checked for a running process.
        If use_pid is not True, then the age of the lockfile is checked
        against the parameter max_age.

        @param lockfile: the lockfile to check
        @type lockfile: str or pathlib.Path
        @param max_age: the maximum age of the lockfile (in seconds), for
                        this lockfile is valid (if use_pid is False).
        @type max_age: int
        @param use_pid: check the content of the lockfile for a PID
                          of a running process
        @type use_pid: bool

        @return: Validity of the lockfile (PID exists and shows to a
                 running process or the lockfile is not too old).
                 Returns False, if the lockfile is not existing, contains an
                 invalid PID or is too old.
        @rtype: bool

        """
        lfile = Path(lockfile)

        if use_pid is None:
            use_pid = self.locking_use_pid
        else:
            use_pid = bool(use_pid)

        if max_age is None:
            max_age = self.max_lockfile_age
        else:
            if not isinstance(max_age, Number):
                msg = _("Value {val!r} for {what} is not a Number.").format(
                    val=max_age, what='max_age')
                raise LockHandlerError(msg)
            if max_age <= 0:
                msg = _("The value for {what} must be greater than zero (is {val!r}).").format(
                    val=max_age, what='max_age')
                raise LockHandlerError(msg)

        LOG.debug(_("Checking lockfile {!r} ...").format(str(lfile)))

        if not lfile.exists():
            LOG.debug(_("Lockfile {!r} doesn't exists.").format(str(lfile)))
            return False

        if not os.access(str(lfile), os.R_OK):
            LOG.warning(_("No read access for lockfile {!r}.").format(str(lfile)))
            return True

        if not os.access(str(lfile), os.W_OK):
            LOG.warning(_("No write access for lockfile {!r}.").format(str(lfile)))
            return True

        if use_pid:
            pid = self.get_pid_from_file(lfile, True)
            if pid is None:
                LOG.warning(_("Unusable lockfile {!r}.").format(str(lfile)))
            else:
                if self.dead(pid):
                    LOG.warning(_("Process with PID {} is unfortunately dead.").format(pid))
                    return False
                else:
                    LOG.debug(_("Process with PID {} is still running.").format(pid))
                    return True

        fstat = None
        try:
            fstat = lfile.stat()
        except OSError as e:
            if e.errno == errno.ENOENT:
                LOG.info(_("Could not stat for file {lfile!r}: {err}").format(
                    lfile=str(lfile), err=e.strerror))
                return False
            raise

        age = time.time() - fstat.st_mtime
        if age >= max_age:
            LOG.debug(_("Lockfile {lfile!r} is older than {max} seconds ({age} seconds).").format(
                lfile=str(lfile), max=max_age, age=age))
            return False
        msg = _(
            "Lockfile {lfile!r} is {age} seconds old, but not old enough "
            "({max} seconds).").format(lfile=str(lfile), max=max_age, age=age)
        LOG.debug(msg)
        return True

    # -------------------------------------------------------------------------
    def get_pid_from_file(self, pidfile, force=False):
        """
        Try to read the PID of some process from the given file.

        @raise LockHandlerError: if the pidfile could not be read

        @param pidfile: The file, where the PID should be in.
        @type pidfile: str
        @param force: Don't raise an exception, if something is going wrong.
                      Only return None.
        @type force: bool

        @return: PID from pidfile
        @rtype: int (or None)

        """
        pfile = Path(pidfile)
        fh = None

        if self.verbose > 1:
            LOG.debug(_("Trying to open pidfile {!r} ...").format(str(pfile)))
        try:
            fh = pfile.open("rb")
        except Exception as e:
            msg = _("Could not open pidfile {!r} for reading:").format(str(pfile))
            msg += ' ' + str(e)
            if force:
                LOG.warning(msg)
                return None
            else:
                raise LockHandlerError(str(e))

        content = fh.readline()
        fh.close()

        content = content.strip()
        if content == "":
            msg = _("First line of pidfile {!r} was empty.").format(str(pfile))
            if force:
                LOG.warning(msg)
                return None
            else:
                raise LockHandlerError(msg)

        pid = None
        try:
            pid = int(content)
        except Exception as e:
            msg = _("Could not interprete {cont!r} as a PID from {file!r}: {err}").format(
                cont=content, file=str(pfile), err=e)
            if force:
                LOG.warning(msg)
                return None
            else:
                raise LockHandlerError(msg)

        if pid <= 0:
            msg = _("Invalid PID {pid} in {file!r} found.").format(pid=pid, file=str(pfile))
            if force:
                LOG.warning(msg)
                return None
            else:
                raise LockHandlerError(msg)

        return pid

    # -------------------------------------------------------------------------
    def kill(self, pid, signal=0):
        """
        Send a signal to a process.

        @raise OSError: on some unpredictable errors

        @param pid: the PID of the process
        @type pid: int
        @param signal: the signal to send to the process, if the signal is 0
                       (the default), no real signal is sent to the process,
                       it will only checked, whether the process is dead or not
        @type signal: int

        @return: the process is dead or not
        @rtype: bool

        """
        try:
            return os.kill(pid, signal)
        except OSError as e:
            # process is dead
            if e.errno == errno.ESRCH:
                return True
            # no permissions
            elif e.errno == errno.EPERM:
                return False
            else:
                # reraise the error
                raise

    # -------------------------------------------------------------------------
    def dead(self, pid):
        """
        Give back, whether the process with the given pid is dead.

        @raise OSError: on some unpredictable errors

        @param pid: the PID of the process to check
        @type pid: int

        @return: the process is dead or not
        @rtype: bool

        """
        if self.kill(pid):
            return True

        # maybe the pid is a zombie that needs us to wait4 it
        from os import waitpid, WNOHANG

        try:
            dead = waitpid(pid, WNOHANG)[0]
        except OSError as e:
            # pid is not a child
            if e.errno == errno.ECHILD:
                return False
            else:
                raise

        return dead


# =============================================================================
if __name__ == "__main__":

    pass

# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
