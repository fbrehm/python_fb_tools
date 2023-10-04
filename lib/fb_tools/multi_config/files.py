#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@summary: A mixin module for the BaseMultiConfig class for files and directory methods.

@author: Frank Brehm
@contact: frank.brehm@pixelpark.com
@copyright: © 2023 by Frank Brehm, Berlin
"""
from __future__ import absolute_import

# Standard module
import logging
import re
import stat
from pathlib import Path

# Third party modules

# Own modules
from ..common import pp
from ..errors import MultiConfigError
from ..xlate import XLATOR, format_list

__version__ = '0.2.0'

LOG = logging.getLogger(__name__)

_ = XLATOR.gettext
ngettext = XLATOR.ngettext


# =============================================================================
class MultiCfgFilesMixin():
    """
    A mixin class for extending the BaseMultiConfig class.

    It contains helper methods for methods regarding files and directories.
    """

    # -------------------------------------------------------------------------
    def collect_config_files(self):
        """Collect all appropriate config file from different directories."""
        LOG.debug(_('Collecting all configuration files.'))

        self.config_files = []
        self.config_file_pattern = {}

        for cfg_dir in self.config_dirs:
            if self.verbose > 1:
                msg = _('Discovering config directory {!r} ...').format(str(cfg_dir))
                LOG.debug(msg)
            self._eval_config_dir(cfg_dir)

        self._set_additional_file(self.additional_config_file)

        self.check_privacy()

        if self.verbose > 2:
            LOG.debug(_('Collected config files:') + '\n' + pp(self.config_files))

        self._cfgfiles_collected = True

    # -------------------------------------------------------------------------
    def check_privacy(self):
        """Check the permissions of the given config file.

        If it  is not located below /etc and public visible, then raise a MultiConfigError.
        """
        if not self.ensure_privacy:
            return

        LOG.debug(_('Checking permissions of config files ...'))

        def is_relative_to_etc(cfile):
            try:
                rel = cfile.relative_to('/etc')                 # noqa
                return True
            except ValueError:
                return False

        for cfg_file in self.config_files:

            # if cfg_file.is_relative_to('/etc'):
            if is_relative_to_etc(cfg_file):
                continue

            if self.verbose > 1:
                LOG.debug(_('Checking permissions of {!r} ...').format(str(cfg_file)))

            mode = cfg_file.stat().st_mode
            if self.verbose > 2:
                msg = _('Found file permissions of {fn!r}: {mode:04o}')
                LOG.debug(msg.format(fn=str(cfg_file), mode=mode))
            if (mode & stat.S_IRGRP) or (mode & stat.S_IROTH):
                msg = _('File {fn!r} is readable by group or by others, found mode {mode:04o}.')
                if self.raise_on_error:
                    raise MultiConfigError(msg.format(fn=str(cfg_file), mode=mode))
                LOG.error(msg.format(fn=str(cfg_file), mode=mode))

    # -------------------------------------------------------------------------
    def _eval_config_dir(self, cfg_dir):

        performed_files = []
        file_list = []
        for found_file in cfg_dir.glob('*'):
            file_list.append(found_file)

        for type_name in self.available_cfg_types:

            if type_name not in self.ext_patterns:
                msg = _('Something strange is happend, file type {!r} not found.')
                LOG.error(msg.format(type_name))
                continue

            for found_file in file_list:

                if found_file in performed_files:
                    continue

                if not found_file.is_file():
                    if self.verbose > 2:
                        msg = _('Path {!r} is not a regular file.').format(str(found_file))
                        LOG.debug(msg)
                    performed_files.append(found_file)
                    continue

                for stem in self.stems:

                    for ext_pattern in self.ext_patterns[type_name]:

                        pat = r'^' + re.escape(stem) + r'\.' + ext_pattern + r'$'
                        if self.verbose > 3:
                            LOG.debug(_('Checking file {fn!r} for pattern {pat!r}.').format(
                                fn=found_file.name, pat=pat))

                        if re.search(pat, found_file.name, re.IGNORECASE):
                            method = self.ext_loader[ext_pattern]
                            if self.verbose > 1:
                                msg = _('Found config file {fi!r}, loader method {m!r}.').format(
                                    fi=str(found_file), m=method)
                                LOG.debug(msg)
                            if found_file in self.config_files:
                                self.config_files.remove(found_file)
                            self.config_files.append(found_file)
                            self.config_file_methods[found_file] = method
                            performed_files.append(found_file)

    # -------------------------------------------------------------------------
    def _get_file_type(self, fn, raise_on_error=None):

        if self.verbose > 1:
            msg = _('Trying to detect file type of file {!r}.')
            LOG.debug(msg.format(str(fn)))

        if raise_on_error is None:
            raise_on_error = self.raise_on_error

        for type_name in self.available_cfg_types:
            for ext_pattern in self.ext_patterns[type_name]:

                pat = r'\.' + ext_pattern + r'$'
                if self.verbose > 3:
                    msg = _('Checking file {fn!r} for pattern {pat!r}.')
                    LOG.debug(msg.format(fn=fn.name, pat=pat))

                if re.search(pat, fn.name, re.IGNORECASE):
                    method = self.ext_loader[ext_pattern]
                    if self.verbose > 1:
                        msg = _('Found config file {fi!r}, loader method {m!r}.')
                        LOG.debug(msg.format(fi=str(fn), m=method))
                    return (type_name, method)

        msg = _(
            'Did not found file type of config file {fn!r}. '
            'Available config types are: {list}.').format(
            fn=str(fn), list=format_list(self.available_cfg_types))
        if self.raise_on_error:
            raise MultiConfigError(msg)
        LOG.error(msg)

        return None

    # -------------------------------------------------------------------------
    def add_config_file(self, filename, prepend=False, type_name=None, raise_on_error=None):
        """Append or prepend a file to the list of config files to use."""
        fn = Path(filename)

        if raise_on_error is None:
            raise_on_error = self.raise_on_error

        if self.verbose > 3:
            msg = _('Checking, whether {!r} is a possible config file.').format(str(fn))
            LOG.debug(msg)

        if not fn.exists():
            msg = _('File {!r} does not exists.').format(str(fn))
            if raise_on_error:
                raise MultiConfigError(msg)
            if self.verbose > 2:
                LOG.debug(msg)
            return False

        if not fn.is_file():
            msg = _('Path {!r} is not a regular file.').format(str(fn))
            if raise_on_error:
                raise MultiConfigError(msg)
            if self.verbose > 2:
                LOG.debug(msg)
            return False

        if type_name:
            method = self.ext_patterns[type_name]
        else:
            file_info = self._get_file_type(fn, raise_on_error=raise_on_error)
            if file_info is None:
                return False
            type_name = file_info(0)
            method = file_info(1)

        if fn in self.config_files:
            self.config_files.remove(fn)
        if prepend:
            self.config_files.insert(0, fn)
        else:
            self.config_files.append(fn)
        self.config_file_methods[fn] = method

        return True

    # -------------------------------------------------------------------------
    def append_config_file(self, filename, stem=None, raise_on_error=None):
        """Append a file to the list of config files to use."""
        if self.verbose > 1:
            msg = _('Trying to append file {!r} to the list of config files ...').format(
                str(filename))
            LOG.debug(msg)
        return self.add_config_file(filename=filename, stem=stem, raise_on_error=raise_on_error)

    # -------------------------------------------------------------------------
    def prepend_config_file(self, filename, stem=None, raise_on_error=None):
        """Prepend a file to the list of config files to use."""
        if self.verbose > 1:
            msg = _('Trying to prepend file {!r} to the list of config files ...').format(
                str(filename))
            LOG.debug(msg)
        return self.add_config_file(
            filename=filename, prepend=True, stem=stem, raise_on_error=raise_on_error)

    # -------------------------------------------------------------------------
    def _set_additional_file(self, cfg_file):

        if not cfg_file:
            return

        if self.verbose > 1:
            msg = _('Trying to add additional config file {!r}.')
            LOG.debug(msg.format(str(cfg_file)))

        self.append_config_file(cfg_file)


# =============================================================================

if __name__ == '__main__':

    pass

# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 list
