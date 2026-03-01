#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@summary: The module for the ConfigOptionsInifile object.

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
class ConfigOptionsInifile(BaseConfigOptions):
    """A class for encapsulating all options for reading an inifile."""

    _argparse_prefix = "inifile"

    _defaults = {}
    _defaults["allow_no_value"] = False
    _defaults["comment_prefixes"] = ('#', ';')
    _defaults["delimiters"] = ('=', ':')
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
    _doc["inline_comment_prefixes"] = _(
        "The inline prefixes for comment lines in ini-files."
    )
    _doc["strict"] = _(
        "Perform strict parsing of inifiles without duplicated sections or options."
    )

    # -------------------------------------------------------------------------
#    def __init__(
#            self,
#            allow_no_value=None,
#            comment_prefixes=None,
#            delimiters=None,
#            extended_interpolation=None,
#            inline_comment_prefixes=None,
#            strict=None,
#        ):
#        """Initialize the ConfigOptionsInifile object."""
#        self._allow_no_value = self._defaults["allow_no_value"]
#        self._comment_prefixes = self._defaults["comment_prefixes"]
#        self._delimiters = self._defaults["delimiters"]
#        self._extended_interpolation = self._defaults["extended_interpolation"]
#        self._inline_comment_prefixes = None
#        self._strict = self._defaults["strict"]
#
#        if allow_no_value is not None:
#            self.allow_no_value = allow_no_value
#
#        if comment_prefixes is not None:
#            self.comment_prefixes = comment_prefixes
#
#        if extended_interpolation is not None:
#            self.extended_interpolation = extended_interpolation
#
#        if delimiters is not None:
#            self.delimiters = delimiters
#
#        if inline_comment_prefixes is not None:
#            self.inline_comment_prefixes = inline_comment_prefixes
#
#        if strict is not None:
#            self.strict = strict

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

#        out = "<%s(" % (self.__class__.__name__)
#
#        fields = []
#
#        if self.allow_no_value != self._defaults["allow_no_value"]:
#            fields.append("allow_no_value={!r}".format(self.allow_no_value))
#
#        if self.comment_prefixes != self._defaults["comment_prefixes"]:
#            fields.append("comment_prefixes={!r}".format(self.comment_prefixes))
#
#        if self.delimiters != self._defaults["delimiters"]:
#            fields.append("delimiters={!r}".format(self.delimiters))
#
#        if self.extended_interpolation != self._defaults["extended_interpolation"]:
#            fields.append("extended_interpolation={!r}".format(self.extended_interpolation))
#
#        if self.inline_comment_prefixes is not None:
#            fields.append("inline_comment_prefixes={!r}".format(self.inline_comment_prefixes))
#
#        if self.strict != self._defaults["strict"]:
#            fields.append("strict={!r}".format(self.strict))
#
#        out += ", ".join(fields) + ")>"
#        return out


# =============================================================================
def main():
    """Entrypoint for test-config-options."""
    my_path = Path(__file__)
    appname = my_path.name

    locale.setlocale(locale.LC_ALL, "")

    cfg_options = ConfigOptionsInifile()

    out = "All properties:\n" + pp(cfg_options.as_dict())
    print(out)
    print()

    print("repr(): {!r}".format(cfg_options))
    print()

    for prop_name in sorted(list(cfg_options.properties()), key=str.lower):
        option = cfg_options.argparse_option(prop_name)
        doc = cfg_options.get_property_doc(prop_name)
        print(f"{option} => {doc}")

    # if len(props) > 0:
    #     prop_name = list(props)[0]
    #     prop = getattr(cfg_options.__class__, prop_name)
    #     doc = prop.__doc__
    #     print("Description of property {p!r}: {d}".format(
    #         p=prop_name, d=prop.__doc__))
    #     # pdict = {}
    #     # for attr_name in prop.__dict__:
    #     #     pdict[attr_name] = prop.__dict__[attr_name].__class__.__name__
    #     # out = "All attributes of property {!r}:\n".format(prop_name)
    #     # out += pp(pdict)
    #     # print(out)
    # else:
    #     print("Did not found any properties for class {!r}.".format("ConfigOptionsInifile"))

    return 0


# =============================================================================
if __name__ == "__main__":

    pass

# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
