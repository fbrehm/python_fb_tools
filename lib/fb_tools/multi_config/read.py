#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@summary: A mixin module for the BaseMultiConfig class for methods reading config files.

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
from ..xlate import XLATOR

__version__ = '0.1.0'

LOG = logging.getLogger(__name__)

_ = XLATOR.gettext
ngettext = XLATOR.ngettext


# =============================================================================
class MultiCfgReadMixin():
    """
    A mixin class for extending the BaseMultiConfig class.

    It contains helper methods for methods regarding reading config files.
    """

    pass


# =============================================================================

if __name__ == '__main__':

    pass

# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 list
