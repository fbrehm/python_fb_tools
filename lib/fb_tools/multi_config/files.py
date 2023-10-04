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

__version__ = '0.1.0'

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


# =============================================================================

if __name__ == '__main__':

    pass

# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 list
