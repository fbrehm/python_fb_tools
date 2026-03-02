#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@summary: The module for the ConfigOptionsToml object.

@author: Frank Brehm
@contact: frank@brehm-online.com
@copyright: © 2026 by Frank Brehm, Berlin
"""

from __future__ import absolute_import

# Standard modules
import copy
import locale
import logging
from pathlib import Path

# Own modules
from . import BaseConfigOptions
from ..common import is_sequence, pp, to_bool, to_str
from ..xlate import XLATOR

__version__ = "0.1.0"
LOG = logging.getLogger(__name__)

_ = XLATOR.gettext


# =============================================================================
class ConfigOptionsToml(BaseConfigOptions):
    """A class for encapsulating all options for generating a toml output."""

    _argparse_prefix = "toml"

    _defaults = {}
    _defaults["indent"] = 4

    _doc = {}
    _doc["indent"] = _("The indention toml output. It takes a non negative number.")

    # -------------------------------------------------------------------------
    @property
    def indent(self):
        """Return the indention of the toml output."""
        return self._indent

    @indent.setter
    def indent(self, value):
        if value is None:
            self._indent = self._defaults["indent"]
            return
        indent = int(value)
        if indent < 0:
            raise ValueError(
                _("Toml indent takes a non negative number, {} was given.").format(indent)
            )
        self._indent = indent

    # -------------------------------------------------------------------------
    def __repr__(self):
        """Typecasting into a string for reproduction."""
        return super(ConfigOptionsToml, self).__repr__()


# =============================================================================
if __name__ == "__main__":

    pass

# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
