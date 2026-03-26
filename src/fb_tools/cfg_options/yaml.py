#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@summary: The module for the ConfigOptionsYaml object.

@author: Frank Brehm
@contact: frank@brehm-online.com
@copyright: © 2018 - 2026 by Frank Brehm, Berlin
"""

from __future__ import absolute_import

# Standard modules
import logging

# Own modules
from . import BaseConfigOptions
from .. import MAX_INDENT
from .. import MAX_TERM_WIDTH
from .. import MIN_INDENT
from .. import MIN_TERM_WIDTH
from ..common import to_bool
from ..xlate import DEFAULT_LOCALE
from ..xlate import XLATOR
from ..xlate import format_list

__version__ = "0.3.1"
LOG = logging.getLogger(__name__)

_ = XLATOR.gettext


# =============================================================================
class ConfigOptionsYaml(BaseConfigOptions):
    """A class for encapsulating all options for generating a yaml output."""

    _argparse_prefix = "yaml"

    min_width = MIN_TERM_WIDTH
    max_width = MAX_TERM_WIDTH
    min_indent = MIN_INDENT
    max_indent = MAX_INDENT

    _defaults = {}
    _defaults["allow_unicode"] = True
    _defaults["canonical"] = False
    _defaults["explicit_end"] = False
    _defaults["explicit_start"] = True
    _defaults["flow_style"] = False
    _defaults["indent"] = 2
    _defaults["line_break"] = None
    _defaults["style"] = None
    _defaults["width"] = 99

    avail_styles = (None, "", "'", '"', "|", ">")
    avail_linebreaks = (None, "\n", "\r", "\r\n")

    style_list_xlated = format_list(avail_styles, do_repr=True, locale=DEFAULT_LOCALE)
    linebreak_list_xlated = format_list(avail_linebreaks, do_repr=True, locale=DEFAULT_LOCALE)

    _doc = {}
    _doc["allow_unicode"] = _("Are Unicode characters allowed in YAML output.")
    _doc["canonical"] = _("Include export tag type in YAML output.")
    _doc["explicit_end"] = _("Should be added an explicite end in YAML output.")
    _doc["explicit_start"] = _("Should be added an explicite start in YAML output.")
    _doc["flow_style"] = _("Print a collection as flow in YAML output.")
    _doc["line_break"] = _(
        "The linebreak used to generate the YAML output, must be one of {}."
    ).format(linebreak_list_xlated)
    _doc["style"] = _("The style of the scalars in YAML output, may be be one of {}.").format(
        style_list_xlated
    )
    _doc["width"] = _("The maximum width of generated lines on YAML output.")

    # -------------------------------------------------------------------------
    @property
    def allow_unicode(self):
        """Are Unicode characters allowed in YAML output."""
        return self._allow_unicode

    @allow_unicode.setter
    def allow_unicode(self, value):
        self._allow_unicode = to_bool(value)

    # -------------------------------------------------------------------------
    @property
    def canonical(self):
        """Output YAML in canonical style."""
        return self._canonical

    @canonical.setter
    def canonical(self, value):
        self._canonical = to_bool(value)

    # -------------------------------------------------------------------------
    @property
    def explicit_end(self):
        """Should be added an explicite end in YAML output."""
        return self._explicit_end

    @explicit_end.setter
    def explicit_end(self, value):
        self._explicit_end = to_bool(value)

    # -------------------------------------------------------------------------
    @property
    def explicit_start(self):
        """Should be added an explicite start in YAML output."""
        return self._explicit_start

    @explicit_start.setter
    def explicit_start(self, value):
        self._explicit_start = to_bool(value)

    # -------------------------------------------------------------------------
    @property
    def flow_style(self):
        """Output YAML in flow style."""
        return self._flow_style

    @flow_style.setter
    def flow_style(self, value):
        self._flow_style = to_bool(value)

    # -------------------------------------------------------------------------
    @property
    def indent(self):
        """Return the indention of the YAML output."""
        return self._indent

    @indent.setter
    def indent(self, value):
        v = int(value)
        if v < 2:
            msg = _(
                "The indention of generated YAML files must be at least "
                "{m} characters, {v!r} are given."
            ).format(m=2, v=value)
            raise ValueError(msg)
        if v > 40:
            msg = _(
                "The indention of generated YAML files must be at most "
                "{m} characters, {v!r} are given."
            ).format(m=40, v=value)
            raise ValueError(msg)
        self._indent = v

    # -------------------------------------------------------------------------
    @property
    def line_break(self):
        """Style for outputting YAML."""
        return self._line_break

    @line_break.setter
    def line_break(self, value):
        if value is None:
            self._line_break = None
            return
        v = str(value)
        if v not in self.avail_linebreaks:
            msg = _(
                "The line break used to generate ouput YAML must be one of {lst}, "
                "but {v!r} was given."
            ).format(lst=self.linebreak_list_xlated, v=value)
            raise ValueError(msg)

        self._style = v

    # -------------------------------------------------------------------------
    @property
    def style(self):
        """Style for outputting YAML."""
        return self._style

    @style.setter
    def style(self, value):
        if value is None:
            self._style = None
            return
        v = str(value).strip()
        if v not in self.avail_styles:
            msg = _(
                "The default style on ouput YAML must be one of {lst}, but {v!r} was given."
            ).format(lst=self.style_list_xlated, v=value)
            raise ValueError(msg)

        self._style = v

    # -------------------------------------------------------------------------
    @property
    def width(self):
        """Return the maximum width of generated lines on YAML output."""
        return self._width

    @width.setter
    def width(self, value):
        if value is None:
            self._width = self._defaults["width"]
            return
        v = int(value)
        if v < self.min_width:
            msg = _(
                "The maximum width of generated YAML output must be at least "
                "{m} characters, {v!r} are given."
            ).format(m=self.min_width, v=value)
            raise ValueError(msg)
        if v > self.max_width:
            msg = _(
                "The maximum width of generated YAML output must be at most "
                "{m} characters, {v!r} are given."
            ).format(m=self.max_width, v=value)
            raise ValueError(msg)
        self._width = v

    # -------------------------------------------------------------------------
    def __repr__(self):
        """Typecasting into a string for reproduction."""
        return super(ConfigOptionsYaml, self).__repr__()


# =============================================================================
if __name__ == "__main__":

    pass

# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
