#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@summary: Module for error classes used by ddns classes and applications.

@author: Frank Brehm
"""

# Standard modules

# Own modules
from ..errors import CommonDirectoryError
from ..errors import CommonFileError
from ..errors import FbAppError
from ..errors import MultiConfigError
from ..xlate import XLATOR

__version__ = '0.2.0'

_ = XLATOR.gettext
ngettext = XLATOR.ngettext


# =============================================================================
class DdnsConfigError(MultiConfigError):
    """Base error class for all exceptions in this module."""

    pass


# =============================================================================
class DdnsAppError(FbAppError):
    """Base exception class for all exceptions in this application."""

    pass


# =============================================================================
class DdnsRequestError(DdnsAppError):
    """Base class for more complex exceptions."""

    # -------------------------------------------------------------------------
    def __init__(self, code, content, url=None):
        """Construct a DdnsRequestError object."""
        self.code = code
        self.content = content
        self.url = url

    # -------------------------------------------------------------------------
    def __str__(self):
        """Typecast into a string."""
        msg = _('Got an error {c} on requesting {u!r}: {m}').format(
            c=self.code, u=self.url, m=self.content)
        return msg


# =============================================================================
class InvalidUpdateStatusFileError(CommonFileError):
    """Special exception class with an invalid DDNS update status file."""

    # -----------------------------------------------------
    def __str__(self):
        """Typecast into a string for error output."""
        msg = _('There is a problem with the update status file {!r}').format(self.path)
        if self.msg:
            msg += ': ' + self.msg
        else:
            msg += '.'
        return msg


# =============================================================================
class WorkDirError(CommonDirectoryError):
    """Special exception class with problems with the working directory."""

    # -----------------------------------------------------
    def __str__(self):
        """Typecast into a string for error output."""
        msg = _('There is a problem with the working directory {!r}').format(self.path)
        if self.msg:
            msg += ': ' + self.msg
        else:
            msg += '.'
        return msg


# =============================================================================
class WorkDirNotExistsError(WorkDirError, FileNotFoundError):
    """Special exception class, if working diretory does not exists."""

    # -----------------------------------------------------
    def __str__(self):
        """Typecast into a string for error output."""
        msg = _('Working directory {!r} does not exists').format(self.path)
        if self.msg:
            msg += ': ' + self.msg
        else:
            msg += '.'
        return msg


# =============================================================================
class WorkDirNotDirError(WorkDirError, NotADirectoryError):
    """Special exception class, if path to working diretory is not a directory."""

    # -----------------------------------------------------
    def __str__(self):
        """Typecast into a string for error output."""
        msg = _('Path {!r} is not a directory').format(self.path)
        if self.msg:
            msg += ': ' + self.msg
        else:
            msg += '.'
        return msg


# =============================================================================
class WorkDirAccessError(WorkDirError, PermissionError):
    """Special exception class, if working diretory is not accessible."""

    # -----------------------------------------------------
    def __str__(self):
        """Typecast into a string for error output."""
        msg = _('Invalid permissions for working directory {!r}').format(self.path)
        if self.msg:
            msg += ': ' + self.msg
        else:
            msg += '.'
        return msg


# =============================================================================
if __name__ == '__main__':

    pass

# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 list
