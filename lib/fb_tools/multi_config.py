#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: Frank Brehm
@contact: frank.brehm@pixelpark.com
@copyright: © 2019 by Frank Brehm, Berlin
@summary: A module for providing a configuration based on multiple configuration files
"""
from __future__ import absolute_import

# Standard module
import logging
import pathlib
import codecs
import argparse
import json
import re

from pathlib import Path

# Third party modules
import six

from six import StringIO
from six.moves import configparser

from configparser import Error as ConfigParseError

import yaml

HAS_HJSON = False
try:
    import hjson
    HAS_HJSON = True
except ImportError:
    pass

# Own modules
from .config import ConfigError

from .common import to_bool

from .obj import FbBaseObject

from .xlate import XLATOR

__version__ = '0.2.0'
LOG = logging.getLogger(__name__)
DEFAULT_ENCODING = 'utf-8'

_ = XLATOR.gettext


# =============================================================================
class MultiConfigError(ConfigError):
    """Base error class for all exceptions happened during
    execution this configured application"""

    pass


# =============================================================================
class BaseMultiConfig(FbBaseObject):
    """
    A base class for providing a configuration for the BaseMultiConfig class
    and methods to read it from configuration files.
    """

    default_encoding = DEFAULT_ENCODING

    default_stems = []
    default_config_dir = 'fb-tools'

    default_loader_methods = {
        'yaml': 'load_yaml',
        'json': 'load_json',
        'hjson': 'load_hjson',
    }
    default_type_extension_patterns = {
        'yaml': [r'ya?ml'],
        'json': [r'js(?:on)'],
        'hjson': [r'hjs(?:on)'],
    }

    available_cfg_types = ['yaml', 'json']
    if HAS_HJSON:
        available_cfg_types.append('hjson')

    # -------------------------------------------------------------------------
    def __init__(
        self, appname=None, verbose=0, version=__version__, base_dir=None,
            append_appname_to_stems=True, config_dir=None,
            encoding=DEFAULT_ENCODING, additional_config_file=None, initialized=False):

        self._encoding = None
        self._config_dir = None
        self._additional_config_file = None
        self._simulate = False
        self.type2loader = {}
        self.type_extensions = {}
        self.config_dirs = []

        super(BaseMultiConfig, self).__init__(
            appname=appname, verbose=verbose, version=version,
            base_dir=base_dir, initialized=False,
        )

        if encoding:
            self.encoding = encoding
        else:
            self.encoding = self.default_encoding

        if config_dir:
            self.config_dir = config_dir
        else:
            self.config_dir = self.default_config_dir

        if additional_config_file:
            self.additional_config_file = additional_config_file

        self._init_config_dirs()

        if initialized:
            self.initialized = True

    # -------------------------------------------------------------------------
    @property
    def encoding(self):
        """The encoding used to read config files."""
        return self._encoding

    @encoding.setter
    def encoding(self, value):
        if not isinstance(value, str):
            msg = _(
                "Encoding {v!r} must be a {s!r} object, "
                "but is a {c!r} object instead.").format(
                v=value, s='str', c=value.__class__.__name__)
            raise TypeError(msg)

        encoder = codecs.lookup(value)
        self._encoding = encoder.name

    # -------------------------------------------------------------------------
    @property
    def additional_config_file(self):
        """An additional configuration file."""
        return self._additional_config_file

    @additional_config_file.setter
    def additional_config_file(self, value):
        if value is None:
            self._additional_config_file = None
            return

        cfile = pathlib.Path(value)
        if cfile.exists():
            if not cfile.is_file():
                msg = _("Configuration file {!r} exists, but is not a regular file.").format(
                    str(cfile))
                raise MultiConfigError(msg)
            self._additional_config_file = cfile.resolve()
            return
        self._additional_config_file = cfile

    # -------------------------------------------------------------------------
    @property
    def config_dir(self):
        """The directory containing the configuration relative to different paths."""
        return self._config_dir

    @config_dir.setter
    def config_dir(self, value):
        if value is None:
            raise TypeError(_("A configuration directory may not be None."))
        cdir = pathlib.Path(value)
        if cdir.is_absolute():
            msg = _("Configuration directory {!r} may not be absolute.").format(str(cdir))
            raise MultiConfigError(msg)

    # -------------------------------------------------------------------------
    def as_dict(self, short=True):
        """
        Transforms the elements of the object into a dict

        @param short: don't include local properties in resulting dict.
        @type short: bool

        @return: structure as dict
        @rtype:  dict
        """

        res = super(BaseMultiConfig, self).as_dict(short=short)
        res['default_encoding'] = self.default_encoding
        res['default_stems'] = self.default_stems
        res['default_config_dir'] = self.default_config_dir
        res['encoding'] = self.encoding
        res['config_dir'] = self.config_dir
        res['additional_config_file'] = self.additional_config_file

        return res

    # -------------------------------------------------------------------------
    @classmethod
    def is_venv(cls):
        """Flag showing, that the current application is running
            inside a virtual environment."""

        if hasattr(sys, 'real_prefix'):
            return True
        return (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)

    # -------------------------------------------------------------------------
    def _init_config_dirs(self):

        self.config_dirs = []
        self.config_dirs.append(Path('/etc') / self.config_dir)
        self.config_dirs.append(Path.home() / '.config' / self.config_dir)
        if self.is_venv():
            self.config_dirs.append(Path(sys.prefix).parent / 'etc')
        self.config_dirs.append(Path.cwd() / 'etc')
        self.config_dirs.append(Path.cwd())


# =============================================================================

if __name__ == "__main__":

    pass

# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 list
