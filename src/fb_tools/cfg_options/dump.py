#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@summary: The module for the ConfigOptionsDump object.

@author: Frank Brehm
@contact: frank@brehm-online.com
@copyright: © 2026 by Frank Brehm, Berlin
"""

from __future__ import absolute_import

# Standard modules
import logging

# Own modules
from . import BaseConfigOptions
from .. import MAX_TERM_WIDTH
from .. import MIN_TERM_WIDTH
from ..common import to_bool
from ..xlate import XLATOR

__version__ = "0.2.0"
LOG = logging.getLogger(__name__)

_ = XLATOR.gettext


# =============================================================================
class ConfigOptionsDump(BaseConfigOptions):
    """A class for encapsulating all options for generating a dumped output."""

    min_width = MIN_TERM_WIDTH
    max_width = MAX_TERM_WIDTH

    _argparse_prefix = "dump"

    _defaults = {}
    _defaults["compact"] = False
    _defaults["depth"] = None
    _defaults["indent"] = 4
    _defaults["sort_dicts"] = True
    _defaults["underscore_numbers"] = False
    _defaults["width"] = 99

    _doc = {}
    _doc["compact"] = _(
        "If False, each item of a sequence will be formatted on a separate line, otherwise as "
        "many items as will fit within the width will be formatted on each output line."
    )
    _doc["depth"] = _("The number of nesting levels which may be printed.")
    _doc["indent"] = _("The amount of indentation added for each nesting level.")
    _doc["sort_dicts"] = _("Dictionaries will be outputted sorted by key.")
    _doc["underscore_numbers"] = _(
        "Integers will be formatted with the {!r} character for a thousands separator."
    ).format("_")
    _doc["width"] = _("The desired maximum number of characters per line in the output.")

    # -------------------------------------------------------------------------
    @property
    def compact(self):
        """Control the way long sequences are formatted."""
        return self._compact

    @compact.setter
    def compact(self, value):
        self._compact = to_bool(value)

    # -------------------------------------------------------------------------
    @property
    def depth(self):
        """Control the way long sequences are formatted."""
        return self._depth

    @depth.setter
    def depth(self, value):
        if value is None:
            self._depth = None
            return
        depth = int(value)
        if depth < 1:
            msg = _("The dump depth value must be a positive integer, {} was given.").format(depth)
            raise ValueError(msg)

        self._depth = depth

    # -------------------------------------------------------------------------
    @property
    def indent(self):
        """Return the indention of the dumped output."""
        return self._indent

    @indent.setter
    def indent(self, value):
        if value is None:
            self._indent = self._defaults["indent"]
            return
        indent = int(value)
        if indent < 0:
            msg = _("The indent value must be a non negative integer, {} was given.").format(
                indent
            )
            raise ValueError(msg)
        self._indent = indent

    # -------------------------------------------------------------------------
    @property
    def sort_dicts(self):
        """Sort dictionaries by key on generating dumping output."""
        return self._sort_dicts

    @sort_dicts.setter
    def sort_dicts(self, value):
        self._sort_dicts = to_bool(value)

    # -------------------------------------------------------------------------
    @property
    def underscore_numbers(self):
        """Integers will be formatted with the {!r} character for a thousands separator."""
        return self._underscore_numbers

    @underscore_numbers.setter
    def underscore_numbers(self, value):
        self._underscore_numbers = to_bool(value)

    # -------------------------------------------------------------------------
    @property
    def width(self):
        """Control the way long sequences are formatted."""
        return self._width

    @width.setter
    def width(self, value):
        if value is None:
            self._width = self._defaults["width"]
            return
        width = int(value)
        if width < self.min_width:
            msg = _(
                "The value for the width must be an integer greater than {m}, {v} was given."
            ).format(m=self.min_width - 9, v=width)
            raise ValueError(msg)
        if v > self.max_width:
            msg = _(
                "The value for the width must be an integer less than {m}, {v} was given."
            ).format(m=self.max_width + 1, v=value)
            raise ValueError(msg)

        self._width = width

    # -------------------------------------------------------------------------
    def __repr__(self):
        """Typecasting into a string for reproduction."""
        return super(ConfigOptionsDump, self).__repr__()


# =============================================================================
if __name__ == "__main__":

    pass

# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
