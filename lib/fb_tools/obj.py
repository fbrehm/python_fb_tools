#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@summary: Module for base object classes, which are used everywhere in my projects.

@author: Frank Brehm
@contact: frank@brehm-online.com
@copyright: © 2022 Frank Brehm, Berlin
"""
from __future__ import absolute_import

# Standard modules
import datetime
import logging
import os
import sys
import traceback
from abc import ABCMeta, abstractmethod
try:
    import pathlib
except ImportError:
    import pathlib2 as pathlib

# Third party modules
from six import add_metaclass

# Own modules
from .common import pp, to_bytes
from .errors import FbError
from .xlate import XLATOR

__version__ = '2.0.2'

LOG = logging.getLogger(__name__)

_ = XLATOR.gettext


# =============================================================================
class FbBaseObjectError(FbError):
    """Base error class useable by all descendand objects."""

    pass


# =============================================================================
class BasedirNotExistingError(FbBaseObjectError):
    """Special error class for the case, if the base directory is not existing."""

    # -------------------------------------------------------------------------
    def __init__(self, dir_name):
        """Initialise a BasedirNotExistingError exception."""
        self.dir_name = dir_name

    # -------------------------------------------------------------------------
    def __str__(self):
        """Typecast into a string object."""
        msg = _(
            'The base directory {!r} is not existing or not '
            'a directory.').format(str(self.dir_name))
        return msg


# =============================================================================
@add_metaclass(ABCMeta)
class FbGenericBaseObject(object):
    """Base class for all and everything.

    42
    """

    # -------------------------------------------------------------------------
    @classmethod
    def get_generic_appname(cls, appname=None):
        """Get the base name of the currently running application."""
        if appname:
            v = str(appname).strip()
            if v:
                return v
        return os.path.basename(sys.argv[0])

    # -------------------------------------------------------------------------
    def __str__(self):
        """Typecast into a string object.

        @return: structure as string
        @rtype:  str
        """
        return pp(self.as_dict(short=True))

    # -------------------------------------------------------------------------
    @abstractmethod
    def __repr__(self):
        """Typecast into a string for reproduction."""
        out = '<%s()>' % (self.__class__.__name__)
        return out

    # -------------------------------------------------------------------------
    def as_dict(self, short=True):
        """
        Transform the elements of the object into a dict.

        @param short: don't include local properties in resulting dict.
        @type short: bool

        @return: structure as dict
        @rtype:  dict
        """
        res = {}
        for key in self.__dict__:
            if short and key.startswith('_') and not key.startswith('__'):
                continue
            val = self.__dict__[key]
            if isinstance(val, FbGenericBaseObject):
                res[key] = val.as_dict(short=short)
            else:
                res[key] = val

        res['__class_name__'] = self.__class__.__name__

        return res

    # -------------------------------------------------------------------------
    def handle_error(
            self, error_message=None, exception_name=None, do_traceback=False):
        """
        Handle an error gracefully.

        Print a traceback and continue.

        @param error_message: the error message to display
        @type error_message: Exception or str
        @param exception_name: name of the exception class
        @type exception_name: str
        @param do_traceback: allways show a traceback
        @type do_traceback: bool

        """
        msg = str(error_message).strip()
        if not msg:
            msg = _('undefined error.')
        title = None

        if isinstance(error_message, Exception):
            title = error_message.__class__.__name__
        else:
            if exception_name is not None:
                title = exception_name.strip()
            else:
                title = _('Exception happened')
        msg = title + ': ' + msg

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
            curdate_str = '[' + curdate.isoformat(' ') + ']: '
            msg = curdate_str + msg + '\n'
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
        Show an information.

        This happens both to STDERR and to all initialized log handlers.

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
            curdate_str = '[' + curdate.isoformat(' ') + ']: '
            msg = curdate_str + msg + '\n'
            if hasattr(sys.stderr, 'buffer'):
                sys.stderr.buffer.write(to_bytes(msg))
            else:
                sys.stderr.write(msg)

        return


# =============================================================================
class FbBaseObject(FbGenericBaseObject):
    """Base class for all objects with some fundamental properties."""

    # -------------------------------------------------------------------------
    def __init__(
        self, appname=None, verbose=0, version=__version__, base_dir=None,
            initialized=False):
        """
        Initialise the base object.

        Raises an exception on a uncoverable error.
        """
        # Senseless comment to satisfy the linter.

        """
        @ivar: name of the current running application
        @type: str
        """
        self._appname = self.get_generic_appname(appname)

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
            msg = _('Wrong verbose level {!r}, must be >= 0').format(verbose)
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
            self.base_dir = base_dir
        if not self._base_dir:
            self._base_dir = pathlib.Path(os.getcwd()).resolve()

        self._initialized = bool(initialized)

    # -----------------------------------------------------------
    @property
    def appname(self):
        """Return the name of the current running application."""
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
        """Return the version string of the current object or application."""
        return getattr(self, '_version', __version__)

    # -----------------------------------------------------------
    @property
    def verbose(self):
        """Return the verbosity level."""
        return getattr(self, '_verbose', 0)

    @verbose.setter
    def verbose(self, value):
        v = int(value)
        if v >= 0:
            self._verbose = v
        else:
            LOG.warning(_('Wrong verbose level {!r}, must be >= 0').format(value))

    # -----------------------------------------------------------
    @property
    def initialized(self):
        """Return whther the initialisation of this object is complete."""
        return getattr(self, '_initialized', False)

    @initialized.setter
    def initialized(self, value):
        self._initialized = bool(value)

    # -----------------------------------------------------------
    @property
    def base_dir(self):
        """Return the base directory, which can be used for different purposes."""
        return self._base_dir

    @base_dir.setter
    def base_dir(self, value):
        base_dir_path = pathlib.Path(value)
        if str(base_dir_path).startswith('~'):
            base_dir_path = base_dir_path.expanduser()
        if not base_dir_path.exists():
            msg = _('Base directory {!r} does not exists.').format(str(value))
            self.handle_error(msg, self.appname)
        elif not base_dir_path.is_dir():
            msg = _('Path for base directory {!r} is not a directory.').format(str(value))
            self.handle_error(msg, self.appname)
        else:
            self._base_dir = base_dir_path

    # -------------------------------------------------------------------------
    def __repr__(self):
        """Typecasting into a string for reproduction."""
        out = '<%s(' % (self.__class__.__name__)

        fields = []
        fields.append('appname={!r}'.format(self.appname))
        fields.append('verbose={!r}'.format(self.verbose))
        fields.append('version={!r}'.format(self.version))
        fields.append('base_dir={!r}'.format(self.base_dir))
        fields.append('initialized={!r}'.format(self.initialized))

        out += ', '.join(fields) + ')>'
        return out

    # -------------------------------------------------------------------------
    def as_dict(self, short=True):
        """
        Transform the elements of the object into a dict.

        @param short: don't include local properties in resulting dict.
        @type short: bool

        @return: structure as dict
        @rtype:  dict
        """
        res = super(FbBaseObject, self).as_dict(short=short)

        res['appname'] = self.appname
        res['version'] = self.version
        res['verbose'] = self.verbose
        res['initialized'] = self.initialized
        res['base_dir'] = self.base_dir

        return res


# =============================================================================

if __name__ == '__main__':

    pass

# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
