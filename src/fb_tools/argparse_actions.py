#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@summary: The module for a collection of useful argparse actions.

@author: Frank Brehm
@contact: frank@brehm-online.com
@copyright: © 2025 by Frank Brehm, Berlin
"""
from __future__ import absolute_import

# Standard modules
import argparse
import logging
import os
import re

try:
    from pathlib import Path
except ImportError:
    from pathlib2 import Path

# Own modules

from . import MAX_TIMEOUT
from .xlate import XLATOR

__version__ = '2.1.3'
LOG = logging.getLogger(__name__)

_ = XLATOR.gettext


# =============================================================================
class RegexOptionAction(argparse.Action):
    """An argparse action for regular expressions."""

    # -------------------------------------------------------------------------
    def __init__(self, option_strings, topic, re_options=None, *args, **kwargs):
        """Initialise a RegexOptionAction object."""
        self._topic = topic
        self._re_options = None
        if re_options is not None:
            self._re_options = re_options

        super(RegexOptionAction, self).__init__(
            option_strings=option_strings, *args, **kwargs)

    # -------------------------------------------------------------------------
    def __call__(self, parser, namespace, pattern, option_string=None):
        """Parse the regular expression option."""
        try:
            if self._re_options is None:
                re_test = re.compile(pattern)                               # noqa
            else:
                re_test = re.compile(pattern, self._re_options)             # noqa
        except Exception as e:
            msg = _('Got a {c} for pattern {p!r}: {e}').format(
                c=e.__class__.__name__, p=pattern, e=e)
            raise argparse.ArgumentError(self, msg)

        setattr(namespace, self.dest, pattern)

# =============================================================================
class DirectoryOptionAction(argparse.Action):
    """An argparse action for directories."""

    # -------------------------------------------------------------------------
    def __init__(self, option_strings, must_exists=True, writeable=False, *args, **kwargs):
        """Initialise a DirectoryOptionAction object."""
        self.must_exists = bool(must_exists)
        self.writeable = bool(writeable)
        if self.writeable:
            self.must_exists = True

        super(DirectoryOptionAction, self).__init__(
            option_strings=option_strings, *args, **kwargs)

    # -------------------------------------------------------------------------
    def __call__(self, parser, namespace, given_path, option_string=None):
        """Parse the directory option."""
        path = Path(given_path)
        if not path.is_absolute():
            msg = _('The path {!r} must be an absolute path.').format(given_path)
            raise argparse.ArgumentError(self, msg)

        if self.must_exists:

            if not path.exists():
                msg = _('The directory {!r} does not exists.').format(str(path))
                raise argparse.ArgumentError(self, msg)

            if not path.is_dir():
                msg = _('The given path {!r} exists, but is not a directory.').format(str(path))
                raise argparse.ArgumentError(self, msg)

            if not os.access(str(path), os.R_OK) or not os.access(str(path), os.X_OK):
                msg = _('The given directory {!r} is not readable.').format(str(path))
                raise argparse.ArgumentError(self, msg)

            if self.writeable and not os.access(str(path), os.W_OK):
                msg = _('The given directory {!r} is not writeable.').format(str(path))
                raise argparse.ArgumentError(self, msg)

        setattr(namespace, self.dest, path)


# =============================================================================
class LogFileOptionAction(argparse.Action):
    """An argparse action for logfiles."""

    # -------------------------------------------------------------------------
    def __init__(self, option_strings, *args, **kwargs):
        """Initialise a LogFileOptionAction object."""
        super(LogFileOptionAction, self).__init__(
            option_strings=option_strings, *args, **kwargs)

    # -------------------------------------------------------------------------
    def __call__(self, parser, namespace, values, option_string=None):
        """Parse the logfile option."""
        if values is None:
            setattr(namespace, self.dest, None)
            return

        path = Path(values)
        logdir = path.parent

        # Checking the parent directory of the Logfile
        if not logdir.exists():
            msg = _('Directory {!r} does not exists.').format(str(logdir))
            raise argparse.ArgumentError(self, msg)
        if not logdir.is_dir():
            msg = _('Path {!r} exists, but is not a directory.').format(str(logdir))
            raise argparse.ArgumentError(self, msg)

        # Checking logfile, if it is already existing
        if path.exists():
            if not path.is_file():
                msg = _('File {!r} is not a regular file.').format(values)
                raise argparse.ArgumentError(self, msg)
            if not os.access(values, os.W_OK):
                msg = _('File {!r} is not writeable.').format(values)
                raise argparse.ArgumentError(self, msg)
        else:
            if not os.access(logdir, os.W_OK):
                msg = _('Directory {!r} is not writeable.').format(str(logdir))
                raise argparse.ArgumentError(self, msg)

        setattr(namespace, self.dest, path.resolve())


# =============================================================================
class CfgFileOptionAction(argparse.Action):
    """An argparse action for a configuration file."""

    # -------------------------------------------------------------------------
    def __init__(self, option_strings, *args, **kwargs):
        """Initialise a CfgFileOptionAction object."""
        super(CfgFileOptionAction, self).__init__(
            option_strings=option_strings, *args, **kwargs)

    # -------------------------------------------------------------------------
    def __call__(self, parser, namespace, values, option_string=None):
        """Parse the configuration file option."""
        if values is None:
            setattr(namespace, self.dest, None)
            return

        path = Path(values)
        if not path.exists():
            msg = _('File {!r} does not exists.').format(values)
            raise argparse.ArgumentError(self, msg)
        if not path.is_file():
            msg = _('File {!r} is not a regular file.').format(values)
            raise argparse.ArgumentError(self, msg)

        setattr(namespace, self.dest, path.resolve())


# =============================================================================
class TimeoutOptionAction(argparse.Action):
    """An argparse action for timeouts."""

    # -------------------------------------------------------------------------
    def __init__(self, option_strings, max_timeout=MAX_TIMEOUT, *args, **kwargs):
        """Initialise a TimeoutOptionAction object."""
        super(TimeoutOptionAction, self).__init__(
            option_strings=option_strings, *args, **kwargs)
        self.max_timeout = max_timeout

    # -------------------------------------------------------------------------
    def __call__(self, parser, namespace, given_timeout, option_string=None):
        """Parse the timeout option."""
        try:
            timeout = int(given_timeout)
            if timeout <= 0 or timeout > self.max_timeout:
                msg = _(
                    'A timeout must be greater than zero and less '
                    'or equal to {}.').format(self.max_timeout)
                raise ValueError(msg)
        except (ValueError, TypeError) as e:
            msg = _('Wrong timeout {!r}:').format(given_timeout)
            msg += ' ' + str(e)
            raise argparse.ArgumentError(self, msg)

        setattr(namespace, self.dest, timeout)


# =============================================================================

if __name__ == '__main__':

    pass

# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 list
