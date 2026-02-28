#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@summary: A module for reading and writing a configuration of different configuration formats.

@author: Frank Brehm
@contact: frank@brehm-online.com
@copyright: © 2026 by Frank Brehm, Berlin
"""

from __future__ import absolute_import

# Standard module
import importlib
import logging
import os
import re
import sys

# Own modules
from . import DEFAULT_ENCODING
from .common import to_bool
from .errors import ConfigDetectionError
from .handling_obj import HandlingObject
from .obj import FbBaseObject
from .xlate import XLATOR

__version__ = "0.1.1"

LOG = logging.getLogger(__name__)

_ = XLATOR.gettext

CFG_TYPE_READER_MODULE = {
    "ini": "configparser",
    "json": "json",
    "hjson": "hjson",
    "toml": "tomli",
    "yaml": "yaml",
}

CFG_TYPE_WRITER_MODULE = {
    "dump": "pprint",
    "json": "json",
    "hjson": "hjson",
    "toml": "tomli_w",
    "yaml": "yaml",
}


# =============================================================================
class AnyConfigHandler(HandlingObject):
    """
    A class for reading and detecting a configuration of an abriatrary format.

    Properties:
    * address_family      (str or int   - rw) (inherited from HandlingObject)
    * appname             (str          - rw) (inherited from FbBaseObject)
    * assumed_answer      (None or bool - rw) (inherited from HandlingObject)
    * base_dir            (pathlib.Path - rw) (inherited from FbBaseObject)
    * encoding            (str          - rw)
    * force               (bool         - rw) (inherited from HandlingObject)
    * initialized         (bool         - rw) (inherited from FbBaseObject)
    * interrupted         (bool         - rw) (inherited from HandlingObject)
    * is_venv             (bool         - ro) (inherited from HandlingObject)
    * prompt_timeout      (int          - rw) (inherited from HandlingObject)
    * quiet               (bool         - rw) (inherited from HandlingObject)
    * raise_on_error      (bool         - rw)
    * simulate            (bool         - rw) (inherited from HandlingObject)
    * terminal_has_colors (bool         - rw) (inherited from HandlingObject)
    * use_chardet         (bool         - rw)
    * verbose             (int          - rw) (inherited from FbBaseObject)
    * version             (str          - ro) (inherited from FbBaseObject)
    """

    default_encoding = DEFAULT_ENCODING

    chardet_min_level_confidence = 1.0 / 3

    supported_read_cfg_types = []
    supported_write_cfg_types = []
    default_width = 99

    loader_methods = {
        "ini": "load_iniparser",
        "json": "load_json",
        "hjson": "load_hjson",
        "toml": "load_toml",
        "yaml": "load_yaml",
    }

    dumper_methods = {
        "dump": "dump_pprint",
        "json": "dump_json",
        "hjson": "dump_hjson",
        "toml": "dump_toml",
        "yaml": "dump_yaml",
    }

    type_extension_patterns = {
        "ini": [r"ini", r"conf(?:ig)?", r"cfg"],
        "json": [r"js(?:on)?"],
        "hjson": [r"hjs(?:on)?"],
        "yaml": [r"ya?ml"],
        "toml": ["to?ml"],
    }

    type_order = ("ini", "yaml", "json", "hjson", "toml")

    yaml_avail_styles = (None, "", "'", '"', "|", ">")
    yaml_avail_linebreaks = (None, "\n", "\r", "\r\n")

    # Detecting different configuration formats for loading and dumping
    module_name = None
    mod_spec = None
    for cfg_type in CFG_TYPE_READER_MODULE:
        module_name = CFG_TYPE_READER_MODULE[cfg_type]
        mod_spec = importlib.util.find_spec(module_name)
        if mod_spec:
            supported_read_cfg_types.append(cfg_type)

    for cfg_type in CFG_TYPE_WRITER_MODULE:
        module_name = CFG_TYPE_WRITER_MODULE[cfg_type]
        mod_spec = importlib.util.find_spec(module_name)
        if mod_spec:
            supported_write_cfg_types.append(cfg_type)

    del module_name
    del mod_spec

    # -------------------------------------------------------------------------
    def __init__(
        self, encoding=DEFAULT_ENCODING, use_chardet=True, raise_on_error=True, *args, **kwargs
    ):
        """Initialise a AnyConfigHandler object."""
        self._encoding = DEFAULT_ENCODING
        self._use_chardet = to_bool(use_chardet)
        self._raise_on_error = to_bool(raise_on_error)

        super(AnyConfigHandler, self).__init__(*args, **kwargs)

        self.initialized = True

    # -------------------------------------------------------------------------
    @property
    def encoding(self):
        """Return the default encoding used to read config files."""
        return self._encoding

    @encoding.setter
    def encoding(self, value):
        if not isinstance(value, str):
            msg = _(
                "Encoding {v!r} must be a {s!r} object, " "but is a {c!r} object instead."
            ).format(v=value, s="str", c=value.__class__.__name__)
            raise TypeError(msg)

        encoder = codecs.lookup(value)
        self._encoding = encoder.name

    # -------------------------------------------------------------------------
    @property
    def raise_on_error(self):
        """Accept keys without values in ini-files."""
        return self._raise_on_error

    @raise_on_error.setter
    def raise_on_error(self, value):
        self._raise_on_error = to_bool(value)

    # -------------------------------------------------------------------------
    @property
    def use_chardet(self):
        """Return whether the chardet module should be used.

        Use the chardet module to detect the character set of a config file.
        """
        return self._use_chardet

    # -------------------------------------------------------------------------
    def as_dict(self, short=True):
        """
        Transform the elements of the object into a dict.

        @param short: don't include local properties in resulting dict.
        @type short: bool

        @return: structure as dict
        @rtype:  dict
        """
        res = super(AnyConfigHandler, self).as_dict(short=short)

        res["default_encoding"] = self.default_encoding
        res["chardet_min_level_confidence"] = self.chardet_min_level_confidence
        # res["config_modules"] = self.config_modules
        res["encoding"] = self.encoding
        res["raise_on_error"] = self.raise_on_error
        res["use_chardet"] = self.use_chardet

        return res

    # -------------------------------------------------------------------------
    def guess_config_type_by_name(self, file_name, raise_on_error=None):
        """Trying to guess the configuration type by the name of the configuration file."""
        if raise_on_error is None:
            raise_on_error = self.raise_on_error
        else:
            raise_on_error = bool(raise_on_error)

        if file_name is None:
            raise ConfigDetectionError(
                _("Could not detect file type by a file name of type {}.").format(
                    self.colored("None", "red")
                )
            )

        file_name = str(file_name)
        if file_name == "-":
            raise ConfigDetectionError(
                _("Could not detect file type by file name '{}'.").format(self.colored("-", "red"))
            )

        for config_type in self.type_order:
            if config_type not in self.type_extension_patterns:
                continue

            for cfg_pattern in self.type_extension_patterns[config_type]:
                pattern = r"\." + cfg_pattern + "$"
                if self.verbose > 4:
                    LOG.debug(f"Searching for pattern {pattern!r} in file name {file_name!r} ...")
                if re.search(pattern, file_name, re.IGNORECASE):
                    return config_type

        if not raise_on_error:
            return None

        raise ConfigDetectionError(
            _("Could not detect file type of file '{}'.").format(self.colored(file_name, "red"))
        )


# =============================================================================

if __name__ == "__main__":

    pass

# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 list
