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

__version__ = '0.2.1'

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

        file_list = []
        for found_file in cfg_dir.glob('*'):
            file_list.append(found_file)

        avail_dir_names = []
        avail_file_names = []

        for stem in self.stems:

            avail_dir_names.append(cfg_dir / (stem + '.d'))

            for type_name in self.available_cfg_types:
                for ext_pattern in self.ext_patterns[type_name]:
                    base_name_pattern = stem + '.' + ext_pattern
                    avail_file_names.append(str(cfg_dir / base_name_pattern))

        if self.verbose > 1:
            msg = _('Possible usable config directories:') + '\n' + pp(avail_dir_names)
            LOG.debug(msg)
            msg = _('Possible usable config files:') + '\n' + pp(avail_file_names)
            LOG.debug(msg)

        for fn in file_list:

            if fn.is_dir():
                if fn in avail_dir_names:
                    # self._eval_whole_dir(fn)
                    continue
                if self.verbose > 2:
                    msg = _('Path {!r} is a unusable directory.').format(str(fn))
                    LOG.debug(msg)
                continue

            if not fn.is_file():
                if self.verbose > 2:
                    msg = _('Path {!r} is not a regular file.').format(str(fn))
                    LOG.debug(msg)
                continue

            found_file = False
            for file_pattern in avail_file_names:
                if re.match(file_pattern, str(fn)):
                    found_file = True
                    break

            if found_file:
                file_info = self._get_file_type(fn)
                if file_info is None:
                    if self.verbose > 2:
                        msg = _('File {!r} is not useable.').format(str(fn))
                        LOG.debug(msg)
                    continue
                if self.verbose > 1:
                    msg = _('Got file info for {!r}:').format(str(fn)) + '\n' + pp(file_info)
                    LOG.debug(msg)
                type_name = file_info['type_name']
                self.append_config_file(
                    fn, type_name=file_info['type_name'], method=file_info['method'])

            elif self.verbose > 2:
                msg = _('File {!r} is not useable.').format(str(fn))
                LOG.debug(msg)

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
                    return {'type_name': type_name, 'method': method}

        msg = _(
            'Did not found file type of config file {fn!r}. '
            'Available config types are: {list}.').format(
            fn=str(fn), list=format_list(self.available_cfg_types))
        if self.raise_on_error:
            raise MultiConfigError(msg)
        LOG.error(msg)

        return None

    # -------------------------------------------------------------------------
    def add_config_file(
            self, filename, prepend=False, type_name=None, method=None, raise_on_error=None):
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

        if type_name is None or method is None:
            file_info = self._get_file_type(fn, raise_on_error=raise_on_error)
            if file_info is None:
                return False
            if self.verbose > 1:
                msg = _('Got file info for {!r}:').format(str(fn)) + '\n' + pp(file_info)
                LOG.debug(msg)
            type_name = file_info['type_name']
            method = file_info['method']

        if fn in self.config_files:
            self.config_files.remove(fn)
        if prepend:
            self.config_files.insert(0, fn)
        else:
            self.config_files.append(fn)
        if self.verbose > 1:
            msg = _('Loading method of {fn!r} is: {m!r}.').format(fn=str(fn), m=method)
            LOG.debug(msg)
        self.config_file_methods[fn] = method

        return True

    # -------------------------------------------------------------------------
    def append_config_file(self, filename, type_name=None, method=None, raise_on_error=None):
        """Append a file to the list of config files to use."""
        if self.verbose > 1:
            msg = _('Trying to append file {!r} to the list of config files ...').format(
                str(filename))
            LOG.debug(msg)
        return self.add_config_file(
            filename=filename, type_name=type_name, method=method,
            raise_on_error=raise_on_error)

    # -------------------------------------------------------------------------
    def prepend_config_file(self, filename, type_name=None, method=None, raise_on_error=None):
        """Prepend a file to the list of config files to use."""
        if self.verbose > 1:
            msg = _('Trying to prepend file {!r} to the list of config files ...').format(
                str(filename))
            LOG.debug(msg)
        return self.add_config_file(
            filename=filename, prepend=True, type_name=type_name,
            method=method, raise_on_error=raise_on_error)

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
