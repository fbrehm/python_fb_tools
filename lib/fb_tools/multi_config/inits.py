#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@summary: A mixin module for the BaseMultiConfig class for helper methods on initialization.

@author: Frank Brehm
@contact: frank.brehm@pixelpark.com
@copyright: © 2023 by Frank Brehm, Berlin
"""
from __future__ import absolute_import

# Standard module
import copy
import logging
import os
import re
import sys
from pathlib import Path

# Third party modules
import six

# Own modules
from ..common import is_sequence, to_str
from ..xlate import XLATOR

__version__ = '0.2.0'

LOG = logging.getLogger(__name__)

_ = XLATOR.gettext
ngettext = XLATOR.ngettext


# =============================================================================
class MultiCfgInitMixin():
    """
    A mixin class for extending the BaseMultiConfig class.

    It contains helper methods on initialization.
    """

    # -------------------------------------------------------------------------
    def _init_config_dirs(self, additional_cfgdirs=None):

        self.config_dirs = []

        self.config_dirs.append(Path('/etc') / self.config_dir)

        path = Path(os.path.expanduser('~')) / '.config' / self.config_dir
        if path in self.config_dirs:
            self.config_dirs.remove(path)

        self.config_dirs.append(path)
        if self.is_venv():
            path = Path(sys.prefix) / 'etc'
            if path in self.config_dirs:
                self.config_dirs.remove(path)
            self.config_dirs.append(path)

        path = Path.cwd() / 'etc'
        if path in self.config_dirs:
            self.config_dirs.remove(path)
        self.config_dirs.append(path)

        path = self.base_dir / 'etc'
        if path in self.config_dirs:
            self.config_dirs.remove(path)
        self.config_dirs.append(path)

        path = self.base_dir
        if path in self.config_dirs:
            self.config_dirs.remove(path)
        self.config_dirs.append(path)

        path = Path.cwd()
        if path in self.config_dirs:
            self.config_dirs.remove(path)
        self.config_dirs.append(path)

        if additional_cfgdirs:
            if is_sequence(additional_cfgdirs):
                for item in additional_cfgdirs:
                    path = Path(item)
                    if path in self.config_dirs:
                        self.config_dirs.remove(path)
                    self.config_dirs.append(path)
            else:
                path = Path(additional_cfgdirs)
                if path in self.config_dirs:
                    self.config_dirs.remove(path)
                self.config_dirs.append(path)

    # -------------------------------------------------------------------------
    def _init_stems(self, append_appname_to_stems, additional_stems=None):

        self.stems = copy.copy(self.default_stems)

        if additional_stems:
            if is_sequence(additional_stems):
                for stem in additional_stems:
                    if not isinstance(stem, (six.string_types, six.binary_type, Path)):
                        msg = _('Stem {!r} is not a String type.').format(stem)
                        raise TypeError(msg)
                    s = str(to_str(stem))
                    if not self.valid_stem(s):
                        msg = _('File name stem {!r} is invalid.').format(s)
                        raise ValueError(msg)
                    if s not in self.stems:
                        self.stems.append(s)
            else:
                if not isinstance(additional_stems, (
                        six.string_types, six.binary_type, Path)):
                    msg = _('Stem {!r} is not a String type.').format(additional_stems)
                    raise TypeError(msg)
                s = str(to_str(additional_stems))
                if not self.valid_stem(s):
                    msg = _('File name stem {!r} is invalid.').format(s)
                    raise ValueError(msg)
                if s not in self.stems:
                    self.stems.append(s)

        if not self.stems or append_appname_to_stems:
            if not self.valid_stem(self.appname):
                msg = _('File name stem {!r} is invalid.').format(self.appname)
                raise ValueError(msg)
            if self.appname not in self.stems:
                self.stems.append(self.appname)

    # -------------------------------------------------------------------------
    def append_stem(self, stem):
        """Append the given stem to the list of basename stems."""
        if self.verbose > 2:
            LOG.debug('Appending basename stem {!r} ...'.format(stem))

        stems = []

        for st in self.stems:
            if st != stem:
                stems.append(st)

        stems.append(stem)
        self.stems = stems

    # -------------------------------------------------------------------------
    def add_stem(self, stem):
        """
        Append the given stem to the list of basename stems.

        This is a wrapper method for append_stem().
        """
        self.append_stem(stem)

    # -------------------------------------------------------------------------
    def prepend_stem(self, stem):
        """Put the given stem to the begin of the list of basename stems."""
        if self.verbose > 2:
            LOG.debug('Prepending basename stem {!r} ...'.format(stem))

        stems = [stem]

        for st in self.stems:
            if st != stem:
                stems.append(st)

        self.stems = stems

    # -------------------------------------------------------------------------
    def _init_types(self):
        """Initialize configuration types and their assigned file extensions."""
        invalid_msg = _('Invalid configuration type {t!r} - not found in {w!r}.')

        for cfg_type in self.available_cfg_types:

            if cfg_type not in self.default_loader_methods:
                msg = invalid_msg.format(t=cfg_type, w='default_loader_methods')
                raise RuntimeError(msg)
            if cfg_type not in self.default_type_extension_patterns:
                msg = invalid_msg.format(t=cfg_type, w='default_type_extension_patterns')
                raise RuntimeError(msg)

            method = self.default_loader_methods[cfg_type]
            for pattern in self.default_type_extension_patterns[cfg_type]:
                ini_style = False
                if cfg_type in self.default_ini_style_types:
                    ini_style = True
                self.assign_extension(cfg_type, pattern, method, ini_style)

    # -------------------------------------------------------------------------
    def assign_extension(self, type_name, ext_pattern, loader_method_name, ini_style=None):
        """Assign a file extension to a cofiguration type."""
        type_name = type_name.lower()
        if type_name not in self.available_cfg_types:
            self.available_cfg_types.append(type_name)
        if type_name not in self.ext_patterns:
            self.ext_patterns[type_name] = []
        self.ext_patterns[type_name].append(ext_pattern)
        self.ext_loader[ext_pattern] = loader_method_name
        self.ext_re[ext_pattern] = re.compile(r'\.' + ext_pattern + r'$', re.IGNORECASE)
        if ini_style is not None:
            if ini_style:
                if ext_pattern not in self.ini_style_types:
                    self.ini_style_types.append(ext_pattern)
            else:
                if ext_pattern in self.ini_style_types:
                    self.ini_style_types.remove(ext_pattern)


# =============================================================================

if __name__ == '__main__':

    pass

# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 list
