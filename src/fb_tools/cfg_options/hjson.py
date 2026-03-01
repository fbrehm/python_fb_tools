#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@summary: The module for the ConfigOptionsHJson object.

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
class ConfigOptionsHJson(BaseConfigOptions):
    """A class for encapsulating all options for generating a hjson output."""

    _argparse_prefix = "hjson"

    _defaults = {}
    _defaults["ensure_ascii"] = False
    _defaults["indent"] = None
    _defaults["sort_keys"] = False

    _doc = {}
    _doc["ensure_ascii"] = _(
        "Ensure, the {} output is guaranteed to have all non-ASCII characters escaped."
    ).format("JSON")
    _doc["indent"] = _(
        "The indention of the {} output. If given an positive integer value, these "
        "number of spaces are indented. I given '0', a negative integer or an empty "
        "string (''), only newlines are inserted. If a non empty string is given, this "
        "will be used as indention to each level. If omitted, the most compact form without "
        "newlines will be generated."
    ).format("HJSON")
    _doc["sort_keys"] = _("Dictionaries will be outputted sorted by key.")


    # -------------------------------------------------------------------------
    @property
    def ensure_ascii(self):
        """Indicate, the JSON output is guaranteed to have all non-ASCII characters escaped."""
        return self._ensure_ascii

    @ensure_ascii.setter
    def ensure_ascii(self, value):
        self._ensure_ascii = to_bool(value)

    # -------------------------------------------------------------------------
    @property
    def indent(self):
        """Return the indention of the JSON output."""
        return self._indent

    @indent.setter
    def indent(self, value):
        if value is None:
            self._indent = None
            return
        try:
            indent_int = int(value)
            self._indent = indent_int
        except ValueError:
            pass

        self._indent = str(value)

    # -------------------------------------------------------------------------
    @property
    def sort_keys(self):
        """Sort dictionaries by key on generating JSON output."""
        return self._sort_keys

    @sort_keys.setter
    def sort_keys(self, value):
        self._sort_keys = to_bool(value)

    # -------------------------------------------------------------------------
    def __repr__(self):
        """Typecasting into a string for reproduction."""
        return super(ConfigOptionsHJson, self).__repr__()


# =============================================================================
if __name__ == "__main__":

    pass

# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
