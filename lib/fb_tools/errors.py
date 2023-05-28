#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@summary: Module for some common used error classes.

@author: Frank Brehm
"""

# Standard modules
import errno
import os
import signal

# Own modules
from .xlate import XLATOR

__version__ = '2.1.2'

_ = XLATOR.gettext
ngettext = XLATOR.ngettext


# =============================================================================
class FbError(Exception):
    """Base error class for all other self defined exceptions."""

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
        """Typecast into a string."""
        return _('Empty mail address.')


# =============================================================================
class InvalidMailAddressError(BaseMailAddressError):
    """Class for a exception in case of a malformed mail address."""

    # -------------------------------------------------------------------------
    def __init__(self, address, msg=None):
        """Initialise a InvalidMailAddressError exception."""
        self.address = address
        self.msg = msg

    # -------------------------------------------------------------------------
    def __str__(self):
        """Typecast into a string."""
        msg = _('Wrong mail address {a!r} ({c})').format(
            a=self.address, c=self.address.__class__.__name__)
        if self.msg:
            msg += ': ' + self.msg
        else:
            msg += '.'
        return msg


# =============================================================================
class FbHandlerError(FbError):
    """Generic exception class for all handler classes."""

    pass


# =============================================================================
class FbAppError(FbHandlerError):
    """Generic exception class for all application classes."""

    pass


# =============================================================================
class AbortAppError(FbAppError):
    """Special exception class interrupting the application."""

    pass


# =============================================================================
class FbCfgAppError(FbAppError):
    """Generic exception class for all configured application classes."""

    pass


# =============================================================================
class HandlerError(FbHandlerError, RuntimeError):
    """Base error class for all exceptions happened during execution this handler."""

    pass


# =============================================================================
class ExpectedHandlerError(HandlerError):
    """Generic exception class for expected exception in all application classes.

    They should be displayed without stack trace.
    """

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
        """Initialise a InterruptError exception."""
        self.signum = signum

    # -------------------------------------------------------------------------
    def __str__(self):
        """Typecast into a string."""
        signame = '{}'.format(self.signum)
        if self.signum in self.signal_names:
            signame = self.signal_names[self.signum] + '(' + signame + ')'

        msg = _('Process with PID {pid} got signal {signal}.').format(
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
        """Initialise a NetworkNotExistingError exception."""
        self.net_name = net_name

    # -------------------------------------------------------------------------
    def __str__(self):
        """Typecast into a string."""
        msg = _('The network {!r} is not existing.').format(self.net_name)
        return msg


# =============================================================================
class FunctionNotImplementedError(FbError, NotImplementedError):
    """Error class for not implemented functions."""

    # -------------------------------------------------------------------------
    def __init__(self, function_name, class_name=None):
        """
        Initialise a FunctionNotImplementedError exception.

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
        """Typecast into a string for error output."""
        msg = _('Method {func}() has to be overridden in class {cls!r}.')
        return msg.format(func=self.function_name, cls=self.class_name)


# =============================================================================
class IoTimeoutError(FbError, IOError):
    """Special error class indicating a timout error on a read/write operation."""

    # -------------------------------------------------------------------------
    def __init__(self, strerror, timeout, filename=None):
        """
        Initialise an IoTimeoutError exception.

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
            strerror += _(' (timeout after {:0.1f} secs)').format(t_o)

        if filename is None:
            super(IoTimeoutError, self).__init__(errno.ETIMEDOUT, strerror)
        else:
            super(IoTimeoutError, self).__init__(
                errno.ETIMEDOUT, strerror, filename)


# =============================================================================
class ReadTimeoutError(IoTimeoutError):
    """Special error class indicating a timout error on reading of a file."""

    # -------------------------------------------------------------------------
    def __init__(self, timeout, filename):
        """
        Initialise a ReadTimeoutError exception.

        @param timeout: the timout in seconds leading to the error
        @type timeout: float
        @param filename: the filename leading to the error
        @type filename: str

        """
        strerror = _('Timeout error on reading')
        super(ReadTimeoutError, self).__init__(strerror, timeout, filename)


# =============================================================================
class WriteTimeoutError(IoTimeoutError):
    """Special error class indicating a timout error on a writing into a file."""

    # -------------------------------------------------------------------------
    def __init__(self, timeout, filename):
        """
        Initialise a WriteTimeoutError exception.

        @param timeout: the timout in seconds leading to the error
        @type timeout: float
        @param filename: the filename leading to the error
        @type filename: str

        """
        strerror = _('Timeout error on writing')
        super(WriteTimeoutError, self).__init__(strerror, timeout, filename)


# =============================================================================
class TimeoutOnPromptError(AbortAppError, IoTimeoutError):
    """Special exception class on timout on a prompt."""

    # -------------------------------------------------------------------------
    def __init__(self, timeout):
        """Initialise a TimeoutOnPromptError exception."""
        strerror = _('Timeout on answering on the console.')
        super(TimeoutOnPromptError, self).__init__(strerror, timeout)


# =============================================================================
class CommandNotFoundError(HandlerError):
    """Special exception, if one ore more OS commands were not found."""

    # -------------------------------------------------------------------------
    def __init__(self, cmd_list):
        """
        Initialise a CommandNotFoundError exception.

        @param cmd_list: all not found OS commands.
        @type cmd_list: list

        """
        self.cmd_list = None
        if cmd_list is None:
            self.cmd_list = [_('Unknown OS command.')]
        elif isinstance(cmd_list, list):
            self.cmd_list = cmd_list
        else:
            self.cmd_list = [cmd_list]

        if len(self.cmd_list) < 1:
            raise ValueError(_('Empty command list given.'))

    # -------------------------------------------------------------------------
    def __str__(self):
        """Typecast into a string for error output."""
        cmds = ', '.join((("'" + str(x) + "'") for x in self.cmd_list))
        msg = ngettext(
            'Could not found OS command:', 'Could not found OS commands:',
            len(self.cmd_list)) + cmds

        return msg


# =============================================================================
class CouldntOccupyLockfileError(FbError):
    """Special error class indicating, that a lockfile couldn't coccupied after a defined time."""

    # -----------------------------------------------------
    def __init__(self, lockfile, duration, tries):
        """
        Initialise a CouldntOccupyLockfileError exception.

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
        """Typecast into a string for error output."""
        return _("Couldn't occupy lockfile {lf!r} in {d:0.1f} seconds with {tries} tries.").format(
            lf=self.lockfile, d=self.duration, tries=self.tries)


# =============================================================================

if __name__ == '__main__':
    pass

# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
