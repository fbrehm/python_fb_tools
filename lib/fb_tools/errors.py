#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: Frank Brehm
@summary: module for some common used error classes
"""

# Standard modules
import errno
import signal
import os

# Own modules
from .xlate import XLATOR

__version__ = '1.2.9'

_ = XLATOR.gettext
ngettext = XLATOR.ngettext


# =============================================================================
class FbError(Exception):
    """
    Base error class for all other self defined exceptions.
    """

    pass


# =============================================================================
class BaseMailAddressError(FbError, ValueError):
    """Base Exception class for Mail address errors."""
    pass


# =============================================================================
class GeneralMailAddressError(BaseMailAddressError):
    """Class for a exception bcause of general mail address errors."""
    pass


# =============================================================================
class EmptyMailAddressError(BaseMailAddressError):
    """Class for a exception in case of an empty mail address."""

    # -------------------------------------------------------------------------
    def __str__(self):

        return _("Empty mail address.")


# =============================================================================
class InvalidMailAddressError(BaseMailAddressError):
    """Class for a exception in case of a malformed mail address."""

    # -------------------------------------------------------------------------
    def __init__(self, address, msg=None):

        self.address = address
        self.msg = msg

    # -------------------------------------------------------------------------
    def __str__(self):

        msg = _("Wrong mail address {a!r} ({c})").format(
            a=self.address, c=self.address.__class__.__name__)
        if self.msg:
            msg += ': ' + self.msg
        else:
            msg += '.'
        return msg


# =============================================================================
class FbHandlerError(FbError):

    pass


# =============================================================================
class FbAppError(FbHandlerError):

    pass


# =============================================================================
class FbCfgAppError(FbAppError):

    pass


# =============================================================================
class HandlerError(FbHandlerError, RuntimeError):
    """Base error class for all exceptions happened during
    execution this handler"""

    pass


# =============================================================================
class ExpectedHandlerError(HandlerError):
    """Base class for all errors, which could be expected in application object
        and displayed without stack trace."""

    pass


# =============================================================================
class InterruptError(ExpectedHandlerError):
    """Special error class for the case, the process was interrupted somehow."""

    signal_names = {
        signal.SIGHUP: 'HUP',
        signal.SIGINT: 'INT',
        signal.SIGABRT: 'ABRT',
        signal.SIGTERM: 'TERM',
        signal.SIGKILL: 'KILL',
        signal.SIGUSR1: 'USR1',
        signal.SIGUSR2: 'USR2',
    }

    # -------------------------------------------------------------------------
    def __init__(self, signum):

        self.signum = signum

    # -------------------------------------------------------------------------
    def __str__(self):

        signame = "{}".format(self.signum)
        if self.signum in self.signal_names:
            signame = self.signal_names[self.signum] + '(' + signame + ')'

        msg = _("Process with PID {pid} got signal {signal}.").format(
            pid=os.getpid(), signal=signame)

        return msg


# =============================================================================
class TerraformObjectError(FbHandlerError):
    """Exception class on errors evaluation VM definition for terraform."""

    pass


# =============================================================================
class TerraformVmError(TerraformObjectError):
    """Exception class on errors evaluation VM definition for terraform."""

    pass


# =============================================================================
class TerraformVmDefinitionError(TerraformVmError):
    """Exception class on errors evaluation VM definition for terraform."""

    pass


# =============================================================================
class NetworkNotExistingError(ExpectedHandlerError):
    """Special error class for the case, if the expected network is not existing."""

    # -------------------------------------------------------------------------
    def __init__(self, net_name):

        self.net_name = net_name

    # -------------------------------------------------------------------------
    def __str__(self):

        msg = _("The network {!r} is not existing.").format(self.net_name)
        return msg


# =============================================================================
class CannotConnectVsphereError(ExpectedHandlerError):
    """Special error class for the case, it cannot connect
        to the given vSphere server."""

    # -------------------------------------------------------------------------
    def __init__(self, host, port, user):

        self.host = host
        self.port = port
        self.user = user

    # -------------------------------------------------------------------------
    def __str__(self):

        msg = _("Could not connect to the vSphere host {h}:{p} as user {u!r}.").format(
            h=self.host, p=self.port, u=self.user)
        return msg


# =============================================================================
class NoDatastoreFoundError(ExpectedHandlerError):
    """Special error class for the case, that no SAN based data store was with
        enogh free space was found."""

    # -------------------------------------------------------------------------
    def __init__(self, needed_bytes):

        self.needed_bytes = int(needed_bytes)

    # -------------------------------------------------------------------------
    def __str__(self):

        mb = float(self.needed_bytes) / 1024.0 / 1024.0
        gb = mb / 1024.0

        msg = _(
            "No SAN based datastore found with at least {m:0.0f} MiB == {g:0.1f} GiB "
            "available space.").format(m=mb, g=gb)
        return msg


# =============================================================================
class FunctionNotImplementedError(FbError, NotImplementedError):
    """
    Error class for not implemented functions.
    """

    # -------------------------------------------------------------------------
    def __init__(self, function_name, class_name=None):
        """
        Constructor.

        @param function_name: the name of the not implemented function
        @type function_name: str
        @param class_name: the name of the class of the function
        @type class_name: str

        """

        self.function_name = function_name
        if not function_name:
            self.function_name = '__unkown_function__'

        self.class_name = class_name
        if not class_name:
            self.class_name = '__unkown_class__'

    # -------------------------------------------------------------------------
    def __str__(self):
        """
        Typecasting into a string for error output.
        """

        msg = _("Method {func}() has to be overridden in class {cls!r}.")
        return msg.format(func=self.function_name, cls=self.class_name)


# =============================================================================
class IoTimeoutError(FbError, IOError):
    """
    Special error class indicating a timout error on a read/write operation
    """

    # -------------------------------------------------------------------------
    def __init__(self, strerror, timeout, filename=None):
        """
        Constructor.

        @param strerror: the error message about the operation
        @type strerror: str
        @param timeout: the timout in seconds leading to the error
        @type timeout: float
        @param filename: the filename leading to the error
        @type filename: str

        """

        t_o = None
        try:
            t_o = float(timeout)
        except ValueError:
            pass
        self.timeout = t_o

        if t_o is not None:
            strerror += _(" (timeout after {:0.1f} secs)").format(t_o)

        if filename is None:
            super(IoTimeoutError, self).__init__(errno.ETIMEDOUT, strerror)
        else:
            super(IoTimeoutError, self).__init__(
                errno.ETIMEDOUT, strerror, filename)


# =============================================================================
class ReadTimeoutError(IoTimeoutError):
    """
    Special error class indicating a timout error on reading of a file.
    """

    # -------------------------------------------------------------------------
    def __init__(self, timeout, filename):
        """
        Constructor.

        @param timeout: the timout in seconds leading to the error
        @type timeout: float
        @param filename: the filename leading to the error
        @type filename: str

        """

        strerror = _("Timeout error on reading")
        super(ReadTimeoutError, self).__init__(strerror, timeout, filename)


# =============================================================================
class WriteTimeoutError(IoTimeoutError):
    """
    Special error class indicating a timout error on a writing into a file.
    """

    # -------------------------------------------------------------------------
    def __init__(self, timeout, filename):
        """
        Constructor.

        @param timeout: the timout in seconds leading to the error
        @type timeout: float
        @param filename: the filename leading to the error
        @type filename: str

        """

        strerror = _("Timeout error on writing")
        super(WriteTimeoutError, self).__init__(strerror, timeout, filename)


# =============================================================================
class CommandNotFoundError(HandlerError):
    """
    Special exception, if one ore more OS commands were not found.

    """

    # -------------------------------------------------------------------------
    def __init__(self, cmd_list):
        """
        Constructor.

        @param cmd_list: all not found OS commands.
        @type cmd_list: list

        """

        self.cmd_list = None
        if cmd_list is None:
            self.cmd_list = [_("Unknown OS command.")]
        elif isinstance(cmd_list, list):
            self.cmd_list = cmd_list
        else:
            self.cmd_list = [cmd_list]

        if len(self.cmd_list) < 1:
            raise ValueError(_("Empty command list given."))

    # -------------------------------------------------------------------------
    def __str__(self):
        """
        Typecasting into a string for error output.
        """

        cmds = ', '.join(map(lambda x: ("'" + str(x) + "'"), self.cmd_list))
        msg = ngettext(
            'Could not found OS command:', 'Could not found OS commands:',
            len(self.cmd_list)) + cmds

        return msg


# =============================================================================
class CouldntOccupyLockfileError(FbError):
    """
    Special error class indicating, that a lockfile couldn't coccupied
    after a defined time.
    """

    # -----------------------------------------------------
    def __init__(self, lockfile, duration, tries):
        """
        Constructor.

        @param lockfile: the lockfile, which could't be occupied.
        @type lockfile: str
        @param duration: The duration in seconds, which has lead to this situation
        @type duration: float
        @param tries: the number of tries creating the lockfile
        @type tries: int

        """

        self.lockfile = str(lockfile)
        self.duration = float(duration)
        self.tries = int(tries)

    # -----------------------------------------------------
    def __str__(self):

        return _("Couldn't occupy lockfile {lf!r} in {d:0.1f} seconds with {tries} tries.").format(
            lf=self.lockfile, d=self.duration, tries=self.tries)


# =============================================================================

if __name__ == "__main__":
    pass

# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
