#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: Frank Brehm
@contact: frank.brehm@pixelpark.com
@copyright: © 2018 by Frank Brehm, Publicies Pixelpark GmbH, Berlin
"""
from __future__ import absolute_import

# Standard modules
import sys
import os
import logging
import datetime
import traceback
import pathlib

# Third party modules

# Own modules
from .common import pp, to_bytes

from .errors import FbError

__version__ = '0.2.5'

LOG = logging.getLogger(__name__)


# =============================================================================
class FbBaseObjectError(FbError):
    """
    Base error class useable by all descendand objects.
    """

    pass


# =============================================================================
class FbBaseObject(object):
    """
    Base class for all objects.
    """

    # -------------------------------------------------------------------------
    def __init__(
        self, appname=None, verbose=0, version=__version__, base_dir=None,
            initialized=False):
        """
        Initialisation of the base object.

        Raises an exception on a uncoverable error.
        """

        self._appname = None
        """
        @ivar: name of the current running application
        @type: str
        """
        if appname:
            v = str(appname).strip()
            if v:
                self._appname = v
        if not self._appname:
            self._appname = os.path.basename(sys.argv[0])

        self._version = version
        """
        @ivar: version string of the current object or application
        @type: str
        """

        self._verbose = int(verbose)
        """
        @ivar: verbosity level (0 - 9)
        @type: int
        """
        if self._verbose < 0:
            msg = "Wrong verbose level {!r}, must be >= 0".format(verbose)
            raise ValueError(msg)

        self._initialized = False
        """
        @ivar: initialisation of this object is complete
               after __init__() of this object
        @type: bool
        """

        self._base_dir = None
        """
        @ivar: base directory used for different purposes, must be an existent
               directory. Defaults to directory of current script daemon.py.
        @type: str or pathlib.Path
        """
        if base_dir:
            pase_dir_path = pathlib.Path(base_dir)
            if not pase_dir_path.exists():
                msg = "Base directory {!r} does not exists.".format(str(pase_dir_path))
                self.handle_error(msg)
            elif not pase_dir_path.is_dir():
                msg = "Base directory {!r} is not a directory.".format(str(pase_dir_path))
                self.handle_error(msg)
                self._base_dir = None
            else:
                self._base_dir = pase_dir_path
        if not self._base_dir:
            self._base_dir = pathlib.Path(sys.argv[0]).resolve().parent

        self._initialized = bool(initialized)

    # -----------------------------------------------------------
    @property
    def appname(self):
        """The name of the current running application."""
        if hasattr(self, '_appname'):
            return self._appname
        return os.path.basename(sys.argv[0])

    @appname.setter
    def appname(self, value):
        if value:
            v = str(value).strip()
            if v:
                self._appname = v

    # -----------------------------------------------------------
    @property
    def version(self):
        """The version string of the current object or application."""
        return getattr(self, '_version', __version__)

    # -----------------------------------------------------------
    @property
    def verbose(self):
        """The verbosity level."""
        return getattr(self, '_verbose', 0)

    @verbose.setter
    def verbose(self, value):
        v = int(value)
        if v >= 0:
            self._verbose = v
        else:
            LOG.warn("Wrong verbose level {!r}, must be >= 0".format(value))

    # -----------------------------------------------------------
    @property
    def initialized(self):
        """The initialisation of this object is complete."""
        return getattr(self, '_initialized', False)

    @initialized.setter
    def initialized(self, value):
        self._initialized = bool(value)

    # -----------------------------------------------------------
    @property
    def base_dir(self):
        """The base directory used for different purposes."""
        return self._base_dir

    @base_dir.setter
    def base_dir(self, value):
        base_dir_path = pathlib.Path(value)
        if str(base_dir_path).startswith('~'):
            base_dir_path = base_dir_path.expanduser()
        if not base_dir_path.exists():
            msg = "Base directory {!r} does not exists.".format(str(value))
            LOG.error(msg)
        elif not base_dir_path.is_dir():
            msg = "Base directory {!r} is not a directory.".format(str(value))
            LOG.error(msg)
        else:
            self._base_dir = base_dir_path

    # -------------------------------------------------------------------------
    def __str__(self):
        """
        Typecasting function for translating object structure
        into a string

        @return: structure as string
        @rtype:  str
        """

        return pp(self.as_dict(short=True))

    # -------------------------------------------------------------------------
    def __repr__(self):
        """Typecasting into a string for reproduction."""

        out = "<%s(" % (self.__class__.__name__)

        fields = []
        fields.append("appname={!r}".format(self.appname))
        fields.append("verbose={!r}".format(self.verbose))
        fields.append("version={!r}".format(self.version))
        fields.append("base_dir={!r}".format(self.base_dir))
        fields.append("initialized={!r}".format(self.initialized))

        out += ", ".join(fields) + ")>"
        return out

    # -------------------------------------------------------------------------
    def as_dict(self, short=True):
        """
        Transforms the elements of the object into a dict

        @param short: don't include local properties in resulting dict.
        @type short: bool

        @return: structure as dict
        @rtype:  dict
        """

        res = self.__dict__
        res = {}
        for key in self.__dict__:
            if short and key.startswith('_') and not key.startswith('__'):
                continue
            val = self.__dict__[key]
            if isinstance(val, FbBaseObject):
                res[key] = val.as_dict(short=short)
            else:
                res[key] = val
        res['__class_name__'] = self.__class__.__name__
        res['appname'] = self.appname
        res['version'] = self.version
        res['verbose'] = self.verbose
        res['initialized'] = self.initialized
        res['base_dir'] = self.base_dir

        return res

    # -------------------------------------------------------------------------
    def handle_error(
            self, error_message=None, exception_name=None, do_traceback=False):
        """
        Handle an error gracefully.

        Print a traceback and continue.

        @param error_message: the error message to display
        @type error_message: str
        @param exception_name: name of the exception class
        @type exception_name: str
        @param do_traceback: allways show a traceback
        @type do_traceback: bool

        """

        msg = 'Exception happened: '
        if exception_name is not None:
            exception_name = exception_name.strip()
            if exception_name:
                msg = exception_name + ': '
            else:
                msg = ''
        if error_message:
            msg += str(error_message)
        else:
            msg += 'undefined error.'

        root_log = logging.getLogger()
        has_handlers = False
        if root_log.handlers:
            has_handlers = True

        if has_handlers:
            LOG.error(msg)
            if do_traceback:
                LOG.error(traceback.format_exc())
        else:
            curdate = datetime.datetime.now()
            curdate_str = "[" + curdate.isoformat(' ') + "]: "
            msg = curdate_str + msg + "\n"
            if hasattr(sys.stderr, 'buffer'):
                sys.stderr.buffer.write(to_bytes(msg))
            else:
                sys.stderr.write(msg)
            if do_traceback:
                traceback.print_exc()

        return

    # -------------------------------------------------------------------------
    def handle_info(self, message, info_name=None):
        """
        Shows an information. This happens both to STDERR and to all
        initialized log handlers.

        @param message: the info message to display
        @type message: str
        @param info_name: Title of information
        @type info_name: str

        """

        msg = ''
        if info_name is not None:
            info_name = info_name.strip()
            if info_name:
                msg = info_name + ': '
        msg += str(message).strip()

        root_log = logging.getLogger()
        has_handlers = False
        if root_log.handlers:
            has_handlers = True

        if has_handlers:
            LOG.info(msg)
        else:
            curdate = datetime.datetime.now()
            curdate_str = "[" + curdate.isoformat(' ') + "]: "
            msg = curdate_str + msg + "\n"
            if hasattr(sys.stderr, 'buffer'):
                sys.stderr.buffer.write(to_bytes(msg))
            else:
                sys.stderr.write(msg)

        return


# =============================================================================

if __name__ == "__main__":

    pass

# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
