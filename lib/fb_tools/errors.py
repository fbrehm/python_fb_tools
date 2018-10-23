#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: Frank Brehm
@summary: module for some common used error classes
"""

# Standard modules
import errno


__version__ = '0.3.1'

# =============================================================================
class FbError(Exception):
    """
    Base error class for all other self defined exceptions.
    """

    pass

# =============================================================================
class FbHandlerError(FbError):

    pass


# =============================================================================
class FbAppError(FbHandlerError):

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

        msg = "The network {!r} is not existing.".format(self.net_name)
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

        msg = "Could not connect to the vSphere host {h}:{p} as user {u!r}.".format(
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

        msg = (
            "No SAN based datastore found with at least {m:0.0f} MiB == {g:0.1f} GiB "
            "available space found.").format(m=mb, g=gb)
        return msg


# =============================================================================
class FunctionNotImplementedError(FbError, NotImplementedError):
    """
    Error class for not implemented functions.
    """

    # -------------------------------------------------------------------------
    def __init__(self, function_name, class_name):
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

        msg = "Function {func}() has to be overridden in class {cls!r}."
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
            strerror += " (timeout after {:0.1f} secs)".format(t_o)

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

        strerror = "Timeout error on reading"
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

        strerror = "Timeout error on writing"
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
            self.cmd_list = ["Unknown OS command."]
        elif isinstance(cmd_list, list):
            self.cmd_list = cmd_list
        else:
            self.cmd_list = [cmd_list]

        if len(self.cmd_list) < 1:
            raise ValueError("Empty command list given.")

    # -------------------------------------------------------------------------
    def __str__(self):
        """
        Typecasting into a string for error output.
        """

        cmds = ', '.join(map(lambda x: ("'" + str(x) + "'"), self.cmd_list))
        msg = "Could not found OS command"
        if len(self.cmd_list) != 1:
            msg += 's'
        msg += ": " + cmds
        return msg


# =============================================================================

if __name__ == "__main__":
    pass

# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
