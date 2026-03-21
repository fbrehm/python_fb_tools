#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@summary: The module for the ConfigOptionsInifile object.

@author: Frank Brehm
@contact: frank@brehm-online.com
@copyright: © 2018 - 2026 by Frank Brehm, Berlin
"""

from __future__ import absolute_import

# Standard modules
import copy
import locale
import logging

# Own modules
from . import BaseConfigOptions
from ..common import is_sequence, pp, to_bool
from ..xlate import XLATOR

__version__ = "0.1.3"
LOG = logging.getLogger(__name__)

_ = XLATOR.gettext


# =============================================================================
class ConfigOptionsInifile(BaseConfigOptions):
    """A class for encapsulating all options for reading an inifile."""

    _argparse_prefix = "inifile"

    _defaults = {}
    _defaults["allow_no_value"] = False
    _defaults["comment_prefixes"] = ("#", ";")
    _defaults["delimiters"] = ("=", ":")
    _defaults["empty_lines_in_values"] = True
    _defaults["extended_interpolation"] = False
    _defaults["inline_comment_prefixes"] = None
    _defaults["strict"] = True

    _doc = {}
    _doc["allow_no_value"] = _("Allow keys without values in inifiles.")
    _doc["comment_prefixes"] = _("The prefixes for comment lines in inifiles.")
    _doc["delimiters"] = _(
        "The delimiters of inifiles for delimit keys from values within a section."
    )
    _doc["empty_lines_in_values"] = _("Allow multi-line values in inifiles.")
    _doc["extended_interpolation"] = _("Use ExtendedInterpolation for interpolation of inifiles.")
    _doc["inline_comment_prefixes"] = _("The inline prefixes for comment lines in inifiles.")
    _doc["strict"] = _(
        "Perform strict parsing of inifiles without duplicated sections or options."
    )

    # -------------------------------------------------------------------------
    @property
    def allow_no_value(self):
        """Allow keys without values in inifiles."""
        return self._allow_no_value

    @allow_no_value.setter
    def allow_no_value(self, value):
        self.allow_no_value = to_bool(value)

    # -------------------------------------------------------------------------
    @property
    def comment_prefixes(self):
        """The prefixes for comment lines in inifiles."""
        return self._comment_prefixes

    @comment_prefixes.setter
    def comment_prefixes(self, value):
        if not value:
            self._comment_prefixes = self._defaults["comment_prefixes"]
            return
        if isinstance(value, str):
            self._comment_prefixes = []
            for character in value:
                self._comment_prefixes.append(character)
            return
        if is_sequence(value):
            self._comment_prefixes = copy.copy(value)
            return
        msg = _("Cannot use {!r} as comment prefixes for inifiles.").format(value)
        raise TypeError(msg)

    # -------------------------------------------------------------------------
    @property
    def delimiters(self):
        """The delimiters of inifiles for delimit keys from values within a section."""
        return self._delimiters

    @delimiters.setter
    def delimiters(self, value):
        if not value:
            self._delimiters = None
            return
        if isinstance(value, str):
            self._delimiters = []
            for character in value:
                self._delimiters.append(character)
            return
        if is_sequence(value):
            self._delimiters = copy.copy(value)
            return
        msg = _("Cannot use {!r} as delimiters for inifiles.").format(value)
        raise TypeError(msg)

    # -------------------------------------------------------------------------
    @property
    def inline_comment_prefixes(self):
        """The inline prefixes for comment lines in ini-files."""
        return self._inline_comment_prefixes

    @inline_comment_prefixes.setter
    def inline_comment_prefixes(self, value):
        if not value:
            self._inline_comment_prefixes = None
            return
        if isinstance(value, str):
            self._inline_comment_prefixes = []
            for character in value:
                self._inline_comment_prefixes.append(character)
            return
        if is_sequence(value):
            self._inline_comment_prefixes = copy.copy(value)
            return
        msg = _("Cannot use {!r} as inline comment prefixes for inifiles.").format(value)
        raise TypeError(msg)

    # -------------------------------------------------------------------------
    @property
    def extended_interpolation(self):
        """Use ExtendedInterpolation for interpolation of inifiles."""
        return self._extended_interpolation

    @extended_interpolation.setter
    def extended_interpolation(self, value):
        self._extended_interpolation = to_bool(value)

    # -------------------------------------------------------------------------
    @property
    def strict(self):
        """Perform strict parsing of inifiles without duplicated sections or options."""
        return self._strict

    @strict.setter
    def strict(self, value):
        self._strict = to_bool(value)

    # -------------------------------------------------------------------------
    @property
    def empty_lines_in_values(self):
        """Return the possibility of multi-line values in ini-files.

        May values can span multiple lines as long as they are indented more thans
        the key that holds them in ini-files.
        """
        return self._empty_lines_in_values

    @empty_lines_in_values.setter
    def empty_lines_in_values(self, value):
        self._empty_lines_in_values = to_bool(value)

    # -------------------------------------------------------------------------
    def __repr__(self):
        """Typecasting into a string for reproduction."""
        return super(ConfigOptionsInifile, self).__repr__()


# =============================================================================
def main():
    """Entrypoint for test-config-options."""
    locale.setlocale(locale.LC_ALL, "")

    cfg_options = ConfigOptionsInifile()

    out = "All properties:\n" + pp(cfg_options.as_dict())
    print(out)
    print()

    print("repr(): {!r}".format(cfg_options))
    print()

    for prop_name in sorted(cfg_options.properties(), key=str.lower):
        option = cfg_options.argparse_option(prop_name)
        doc = cfg_options.get_property_doc(prop_name)
        print(f"{option} => {doc}")

    return 0


# =============================================================================
if __name__ == "__main__":

    pass

# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
