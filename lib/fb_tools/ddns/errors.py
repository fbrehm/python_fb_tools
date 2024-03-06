#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@summary: Module for error classes used by ddns classes and applications.

@author: Frank Brehm
"""

# Standard modules
import errno

# Own modules
from ..errors import FbAppError
from ..errors import MultiConfigError
from ..xlate import XLATOR

__version__ = '0.1.0'

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
class WorkDirError(DdnsAppError):
    """Special exception class with problems with the working directory."""

    pass


# =============================================================================
class WorkDirNotExistsError(WorkDirError, FileNotFoundError):
    """Special exception class, if working diretory does not exists."""

    # -------------------------------------------------------------------------
    def __init__(self, workdir):
        """Construct a WorkDirNotExistsError object."""
        super(WorkDirNotExistsError, self).__init__(
            errno.ENOENT, _('Directory does not exists'), str(workdir))


# =============================================================================
class WorkDirNotDirError(WorkDirError, NotADirectoryError):
    """Special exception class, if path to working diretory is not a directory."""

    # -------------------------------------------------------------------------
    def __init__(self, workdir):
        """Construct a WorkDirNotDirError object."""
        super(WorkDirNotDirError, self).__init__(
            errno.ENOTDIR, _('Path is not a directory'), str(workdir))


# =============================================================================
class WorkDirAccessError(WorkDirError, PermissionError):
    """Special exception class, if working diretory is not accessible."""

    # -------------------------------------------------------------------------
    def __init__(self, workdir, msg=None):
        """Construct a WorkDirAccessError object."""
        if not msg:
            msg = _('Invalid permissions')

        super(WorkDirAccessError, self).__init__(errno.EACCES, msg, str(workdir))


# =============================================================================
if __name__ == '__main__':

    pass

# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 list
