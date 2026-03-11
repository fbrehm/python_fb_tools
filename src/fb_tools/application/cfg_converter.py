#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@summary: The module for the config-converter application object.

@author: Frank Brehm
@contact: frank.brehm@pixelpark.com
@copyright: © 2026 by Frank Brehm, Berlin
"""

from __future__ import absolute_import, print_function

# Standard modules
import argparse
import copy
import locale
import logging
import os
import sys
from pathlib import Path

# Third party modules

# Own modules
from .. import DEFAULT_TERMINAL_WIDTH
from .. import MAX_INDENT
from .. import MAX_TERM_WIDTH
from .. import MIN_INDENT
from .. import MIN_TERM_WIDTH
from .. import __version__ as GLOBAL_VERSION
from ..any_config import AnyConfigHandler
from ..app import BaseApplication
from ..argparse_actions import InputFileOptionAction
from ..argparse_actions import NonNegativeIntegerOptionAction
from ..argparse_actions import OutputFileOptionAction
from ..argparse_actions import RangeOptionAction
from ..cfg_options.dump import ConfigOptionsDump
from ..cfg_options.hjson import ConfigOptionsHJson
from ..cfg_options.inifile import ConfigOptionsInifile
from ..cfg_options.json import ConfigOptionsJson
from ..cfg_options.yaml import ConfigOptionsYaml
from ..common import pp
from ..errors import ConfigDetectionError
from ..errors import ConfigWrongTypeError
from ..errors import FbAppError
from ..errors import InputFileNotExistingError
from ..errors import InputFileNotReadableError
from ..xlate import DEFAULT_LOCALE
from ..xlate import XLATOR
from ..xlate import format_list

# from ..multi_config import BaseMultiConfig

__version__ = "0.10.1"
LOG = logging.getLogger(__name__)

_ = XLATOR.gettext
ngettext = XLATOR.ngettext


# =============================================================================
class CfgConvertError(FbAppError):
    """Base exception class for all exceptions in this application."""

    pass


# =============================================================================
class CfgTypeOptionAction(argparse.Action):
    """An argparse action for a configuration type option."""

    # -------------------------------------------------------------------------
    def __init__(self, option_strings, supported_types, *args, **kwargs):
        """Initialise a CfgTypeOptionAction object."""
        self.supported_types = copy.copy(supported_types)

        super(CfgTypeOptionAction, self).__init__(*args, **kwargs, option_strings=option_strings)

    # -------------------------------------------------------------------------
    def __call__(self, parser, namespace, cfg_type, option_string=None):
        """Parse the configuration type option."""
        if cfg_type is None:
            msg = _("The configuration file type may not be None.")
            raise argparse.ArgumentError(self, msg)

        cfg_type_clean = cfg_type.strip().lower()
        if cfg_type_clean not in self.supported_types:
            msg = _("The configuration file type must be one of {lst}, given {g!r}.").format(
                lst=format_list(self.supported_types, do_repr=True, locale=DEFAULT_LOCALE),
                g=cfg_type,
            )
            raise argparse.ArgumentError(self, msg)

        setattr(namespace, self.dest, cfg_type_clean)
        return


# =============================================================================
class YamlStyleOptionAction(argparse.Action):
    """An argparse action for YAML style options."""

    # -------------------------------------------------------------------------
    def __init__(self, option_strings, supported_styles, *args, **kwargs):
        """Initialise a YamlStyleOptionAction object."""
        self.supported_styles = copy.copy(supported_styles)

        super(YamlStyleOptionAction, self).__init__(*args, **kwargs, option_strings=option_strings)

    # -------------------------------------------------------------------------
    def __call__(self, parser, namespace, style, option_string=None):
        """Parse the YAML style option."""
        if style is None:
            setattr(namespace, self.dest, None)
            return

        style_clean = style.strip()
        if style_clean not in self.supported_styles:
            msg = _("The YAML style type must be one of {opt}, given {g!r}.").format(
                opt=format_list(self.supported_styles, do_repr=True, locale=DEFAULT_LOCALE),
                g=style,
            )
            raise argparse.ArgumentError(self, msg)

        setattr(namespace, self.dest, style_clean)
        return


# =============================================================================
class CfgConvertApplication(BaseApplication):
    """Class for the application objects."""

    min_width = MIN_TERM_WIDTH
    max_width = MAX_TERM_WIDTH
    min_indent = MIN_INDENT
    max_indent = MAX_INDENT

    show_quiet_option = False
    show_force_option = True

    # -------------------------------------------------------------------------
    def __init__(self, version=GLOBAL_VERSION, *args, **kwargs):
        """Initialize the application object."""
        desc = _(
            "Converts the given configuration file from the given input format "
            "into the given output format and print it out to {o} "
            "or into a given output file."
        ).format(o="STDOUT")

        self._from_type = None
        self._to_type = None
        self._input_file = "-"
        self._output_file = "-"
        self.cfg_content = None

        self._force_desc_msg = _(
            "Override an existing target config file without a question, "
            "if it is already existing."
        )

        self.config_handler = None

        super(CfgConvertApplication, self).__init__(
            *args, initialized=False, description=desc, version=version, **kwargs
        )

        self.config_handler = AnyConfigHandler(
            appname=self.appname,
            base_dir=self.base_dir,
            terminal_has_colors=self.terminal_has_colors,
            verbose=self.verbose,
            simulate=self.simulate,
            force=self.force,
        )
        self.eval_args_cfg_types()

        self.fileio_timeout = 10

        self.initialized = True

    # -------------------------------------------------------------------------
    @property
    def from_type(self):
        """Type of configuration of source files."""
        return self._from_type

    @from_type.setter
    def from_type(self, value):
        if value is None:
            self._from_type = None
            return
        v = str(value).strip().lower()
        if v not in AnyConfigHandler.supported_read_cfg_types:
            msg = _("Invalid input configuration type {!r}").format(value)
            raise ConfigWrongTypeError(msg)
        self._from_type = v

    # -------------------------------------------------------------------------
    @property
    def to_type(self):
        """Type of configuration of target files."""
        return self._to_type

    @to_type.setter
    def to_type(self, value):
        if value is None:
            self._to_type = None
            return
        v = str(value).strip().lower()
        if v not in AnyConfigHandler.supported_write_cfg_types:
            msg = _("Invalid target configuration type {!r}").format(value)
            raise ConfigWrongTypeError(msg)
        self._to_type = v

    # -------------------------------------------------------------------------
    @property
    def input_file(self):
        """Give the file name of the input, the source configuration."""
        return self._input_file

    @input_file.setter
    def input_file(self, value):
        if value is None:
            self._input_file = "-"
            return
        path = value
        if not isinstance(value, Path):
            v = str(value).strip()
            if v == "" or v == "-":
                self._input_file = "-"
                return
            path = Path(v)

        if not path.exists():
            raise InputFileNotExistingError(path)
        if not os.access(str(path), os.R_OK):
            raise InputFileNotReadableError(path)
        self._input_file = path

    # -------------------------------------------------------------------------
    @property
    def output_file(self):
        """Give the file name of the output, the target configuration."""
        return self._output_file

    @output_file.setter
    def output_file(self, value):
        if value is None:
            self._output_file = "-"
            return
        path = value
        if not isinstance(value, Path):
            v = str(value).strip()
            if v == "" or v == "-":
                self._output_file = "-"
                return
            path = Path(v)

        self._output_file = path

    # -------------------------------------------------------------------------
    def as_dict(self, short=True):
        """
        Transform the elements of the object into a dict.

        @param short: don't include local properties in resulting dict.
        @type short: bool

        @return: structure as dict
        @rtype:  dict
        """
        res = super(CfgConvertApplication, self).as_dict(short=short)

        res["from_type"] = self.from_type
        res["to_type"] = self.to_type
        res["input_file"] = self.input_file
        res["output_file"] = self.output_file

        return res

    # -------------------------------------------------------------------------
    def post_init(self):
        """Execute some actions after initialising."""
        self.initialized = False

        self.init_logging()

        self.perform_arg_parser()

    # -------------------------------------------------------------------------
    def init_arg_parser(self):
        """Initialise the argument parser."""
        super(CfgConvertApplication, self).init_arg_parser()

        conv_group = self.arg_parser.add_argument_group(_("Converting options"))

        read_type_list = format_list(
            AnyConfigHandler.supported_read_cfg_types,
            do_repr=True,
            style="or",
            locale=DEFAULT_LOCALE,
        )
        conv_group.add_argument(
            "-F",
            "--from-type",
            metavar=_("CFG_TYPE"),
            dest="from_type",
            action=CfgTypeOptionAction,
            supported_types=AnyConfigHandler.supported_read_cfg_types,
            help=_("The configuration type of the source, must be one of {}.").format(
                read_type_list
            ),
        )

        write_type_list = format_list(
            AnyConfigHandler.supported_write_cfg_types,
            do_repr=True,
            style="or",
            locale=DEFAULT_LOCALE,
        )
        conv_group.add_argument(
            "-T",
            "--to-type",
            metavar=_("CFG_TYPE"),
            dest="to_type",
            action=CfgTypeOptionAction,
            supported_types=AnyConfigHandler.supported_write_cfg_types,
            help=_("The configuration type of the target, must be one " "of {}.").format(
                write_type_list
            ),
        )

        width_help = _(
            "The maximum number of characters per line in the output. The default is the width "
            "of the current terminal. If this one cannot be evaluated, the default width is {}."
        ).format(DEFAULT_TERMINAL_WIDTH)
        conv_group.add_argument(
            "-W",
            "--width",
            metavar="INT",
            dest="width",
            type=int,
            action=RangeOptionAction,
            min_val=self.min_width,
            max_val=self.max_width,
            help=width_help,
        )

        indent_help = _(
            "The amount of indentation added for each nesting level. The default depends of the "
            "output configuration type. For YAML output it is 2, JSON and HJSON it is None "
            "(compact output), and for Dump and Toml is is 4."
        )
        conv_group.add_argument(
            "-I",
            "--indent",
            metavar="INT",
            dest="indent",
            type=int,
            action=RangeOptionAction,
            min_val=0,
            max_val=9,
            help=indent_help,
        )

        if "dump" in AnyConfigHandler.supported_write_cfg_types:
            self._init_dump_args()
        if "ini" in AnyConfigHandler.supported_read_cfg_types:
            self._init_inifile_args()
        if "yaml" in AnyConfigHandler.supported_write_cfg_types:
            self._init_yaml_args()
        if "json" in AnyConfigHandler.supported_write_cfg_types:
            self._init_json_args()
        if "hjson" in AnyConfigHandler.supported_write_cfg_types:
            self._init_hjson_args()

        self.arg_parser.add_argument(
            "input_file",
            metavar=_("INPUT_FILE"),
            nargs="?",
            default="-",
            action=InputFileOptionAction,
            help=_(
                "The filename of the input file. Use {i!r} to read from {f} "
                "(which is the default)."
            ).format(i="-", f="STDIN"),
        )

        self.arg_parser.add_argument(
            "output_file",
            metavar=_("OUTPUT_FILE"),
            nargs="?",
            default="-",
            action=OutputFileOptionAction,
            help=_(
                "The filename of the output file. Use {i!r} to write to {f} "
                "(which is the default)."
            ).format(i="-", f="STDOUT"),
        )

    # -------------------------------------------------------------------------
    def _init_inifile_args(self):
        """Define commandline options for reading inifiles."""
        inifile_group = self.arg_parser.add_argument_group(_("Options for reading inifiles"))

        inifile_group.add_argument(
            ConfigOptionsInifile.argparse_option("allow_no_value"),
            dest="inifile_allow_no_value",
            action="store_true",
            help=ConfigOptionsInifile.get_property_doc("allow_no_value"),
        )

        prefix_list = ConfigOptionsInifile.get_default_value("comment_prefixes")
        prefix_help = ConfigOptionsInifile.get_property_doc("comment_prefixes")
        prefix_help += " " + _("Default: {!r}.").format("".join(prefix_list))
        inifile_group.add_argument(
            ConfigOptionsInifile.argparse_option("comment_prefixes"),
            metavar=_("PREFIXES"),
            dest="inifile_comment_prefixes",
            help=prefix_help,
        )

        delim_list = ConfigOptionsInifile.get_default_value("delimiters")
        delim_help = ConfigOptionsInifile.get_property_doc("delimiters")
        delim_help += _("Default: {!r}.").format("".join(delim_list))
        inifile_group.add_argument(
            ConfigOptionsInifile.argparse_option("delimiters"),
            metavar=_("DELIMITERS"),
            dest="inifile_delimiters",
            help=prefix_help,
        )

        inifile_group.add_argument(
            "--inifile-no-empty-lines-in-values",
            dest="inifile_empty_lines_in_values",
            action="store_false",
            help=_("Don't allow multi-line values in inifiles."),
        )

        inifile_group.add_argument(
            ConfigOptionsInifile.argparse_option("extended_interpolation"),
            dest="inifile_extended_interpolation",
            action="store_true",
            help=ConfigOptionsInifile.get_property_doc("extended_interpolation"),
        )

        prefix_list = ConfigOptionsInifile.get_default_value("inline_comment_prefixes")
        prefix_default = None
        if prefix_list is not None:
            prefix_default = "".join(prefix_default)
        prefix_help = ConfigOptionsInifile.get_property_doc("inline_comment_prefixes")
        prefix_help += " " + _("Default: {!r}.").format(prefix_default)
        inifile_group.add_argument(
            ConfigOptionsInifile.argparse_option("inline_comment_prefixes"),
            metavar=_("PREFIXES"),
            dest="inifile_inline_comment_prefixes",
            help=prefix_help,
        )

        inifile_group.add_argument(
            ConfigOptionsInifile.argparse_option("strict"),
            dest="inifile_strict",
            action="store_true",
            help=ConfigOptionsInifile.get_property_doc("strict"),
        )

    # -------------------------------------------------------------------------
    def _init_dump_args(self):
        """Define commandline options for dumping out the read config."""
        dumping_group = self.arg_parser.add_argument_group(_("Dump output options"))

        dumping_group.add_argument(
            ConfigOptionsDump.argparse_option("compact"),
            dest="dump_compact",
            action="store_true",
            help=ConfigOptionsDump.get_property_doc("compact"),
        )

        dumping_group.add_argument(
            ConfigOptionsDump.argparse_option("depth"),
            dest="dump_depth",
            type=int,
            may_zero=False,
            action=NonNegativeIntegerOptionAction,
            help=ConfigOptionsDump.get_property_doc("depth"),
        )

        if sys.version_info.major > 3 or (
            sys.version_info.major == 3 and sys.version_info.minor >= 8
        ):
            dumping_group.add_argument(
                "--dump-no-sort-dicts",
                dest="dump_sort_dicts",
                action="store_false",
                help=_("Dictionaries will not be outputted sorted by key."),
            )

        if sys.version_info.major > 3 or (
            sys.version_info.major == 3 and sys.version_info.minor >= 11
        ):
            dumping_group.add_argument(
                ConfigOptionsDump.argparse_option("underscore_numbers"),
                dest="dump_underscore_numbers",
                action="store_true",
                help=ConfigOptionsDump.get_property_doc("underscore_numbers"),
            )

    # -------------------------------------------------------------------------
    def _init_yaml_args(self):
        """Define commandline options for converting into YAML format."""
        yaml_group = self.arg_parser.add_argument_group(_("YAML output options"))

        yaml_group.add_argument(
            ConfigOptionsYaml.argparse_option("canonical"),
            dest="yaml_canonical",
            action="store_true",
            help=ConfigOptionsYaml.get_property_doc("canonical"),
        )

        yaml_group.add_argument(
            "--yaml-no-allow-unicode",
            dest="yaml_no_allow_unicode",
            action="store_true",
            help=_("Unicode characters are not allowed in YAML output."),
        )

        yaml_group.add_argument(
            ConfigOptionsYaml.argparse_option("flow_style"),
            action="store_true",
            dest="yaml_flow_style",
            help=ConfigOptionsYaml.get_property_doc("flow_style"),
        )

        yaml_group.add_argument(
            ConfigOptionsYaml.argparse_option("style"),
            dest="yaml_style",
            nargs="?",
            metavar=_("STYLE"),
            supported_styles=ConfigOptionsYaml.avail_styles,
            action=YamlStyleOptionAction,
            help=ConfigOptionsYaml.get_property_doc("style"),
        )

        yaml_group.add_argument(
            "--yaml-no-explicit-start",
            dest="yaml_no_explicit_start",
            action="store_true",
            help=_("Don't print an explicit start marker in YAML output."),
        )

        yaml_group.add_argument(
            "--yaml-explicit-end",
            dest="yaml_explicit_end",
            action="store_true",
            help=_("Print an explicit end marker in YAML output."),
        )

    # -------------------------------------------------------------------------
    def _init_json_args(self):
        """Define commandline options for converting into JSON format."""
        json_group = self.arg_parser.add_argument_group(_("JSON output options"))

        json_group.add_argument(
            ConfigOptionsJson.argparse_option("ensure_ascii"),
            action="store_true",
            dest="json_ensure_ascii",
            help=ConfigOptionsJson.get_property_doc("ensure_ascii"),
        )

        json_group.add_argument(
            ConfigOptionsJson.argparse_option("sort_keys"),
            action="store_true",
            dest="json_sort_keys",
            help=ConfigOptionsJson.get_property_doc("sort_keys"),
        )

    # -------------------------------------------------------------------------
    def _init_hjson_args(self):
        """Define commandline options for converting into HJSON format."""
        hjson_group = self.arg_parser.add_argument_group(_("HJSON output options"))

        hjson_group.add_argument(
            ConfigOptionsHJson.argparse_option("ensure_ascii"),
            action="store_true",
            dest="hjson_ensure_ascii",
            help=ConfigOptionsHJson.get_property_doc("ensure_ascii"),
        )

        hjson_group.add_argument(
            ConfigOptionsHJson.argparse_option("sort_keys"),
            action="store_true",
            dest="hjson_sort_keys",
            help=ConfigOptionsHJson.get_property_doc("sort_keys"),
        )

    # -------------------------------------------------------------------------
    def perform_arg_parser(self):
        """Parse the command line options."""
        from_type = getattr(self.args, "from_type", None)
        if from_type:
            self.from_type = from_type

        self.to_type = getattr(self.args, "to_type", None)

        self.input_file = getattr(self.args, "input_file", "-")
        self.output_file = getattr(self.args, "output_file", "-")

    # -------------------------------------------------------------------------
    def eval_args_cfg_types(self):
        """Evaluate all options for the particular configuration types from command line."""
        if self.verbose > 1:
            LOG.debug(
                _("Evaluate all options for the particular configuration types from command line.")
            )

        if "dump" in self.config_handler.supported_write_cfg_types:
            self._eval_dump_args()
        if "ini" in self.config_handler.supported_read_cfg_types:
            self._eval_inifile_args()
        if "yaml" in self.config_handler.supported_write_cfg_types:
            self._eval_yaml_args()
        if "json" in self.config_handler.supported_write_cfg_types:
            self._eval_json_args()
        if "hjson" in self.config_handler.supported_write_cfg_types:
            self._eval_hjson_args()
        if "toml" in self.config_handler.supported_write_cfg_types:
            self._eval_toml_args()

    # -------------------------------------------------------------------------
    def _eval_dump_args(self):
        """Evaluate options for dumping the output."""
        if self.verbose > 2:
            LOG.debug(_("Evaluate options for dumping the output."))

        val = getattr(self.args, "width", None)
        if val is not None:
            self.config_handler.options_dump.width = val

        val = getattr(self.args, "indent", None)
        if val is not None:
            self.config_handler.options_dump.indent = val

        val = getattr(self.args, "dump_compact", False)
        if val:
            self.config_handler.options_dump.compact = True

        val = getattr(self.args, "dump_depth", None)
        if val:
            self.config_handler.options_dump.depth = val

        if hasattr(self.args, "dump_sort_dicts"):
            val = getattr(self.args, "dump_sort_dicts", True)
            if not val:
                self.config_handler.options_dump.sort_dicts = False

        if hasattr(self.args, "dump_underscore_numbers"):
            val = getattr(self.args, "dump_underscore_numbers", False)
            if val:
                self.config_handler.options_dump.underscore_numbers = True

        if self.verbose > 1:
            LOG.debug(
                _("Options for dumping the output:")
                + "\n"
                + pp(self.config_handler.options_dump.property_dict())
            )

    # -------------------------------------------------------------------------
    def _eval_inifile_args(self):
        """Evaluate options for reading inifiles."""
        if self.verbose > 2:
            LOG.debug(_("Evaluate options for reading inifiles."))

        if hasattr(self.args, "inifile_allow_no_value"):
            val = self.args.inifile_allow_no_value
            if val:
                self.config_handler.options_inifile.allow_no_value = True

        if hasattr(self.args, "inifile_comment_prefixes"):
            val = self.args.inifile_comment_prefixes
            if val:
                self.config_handler.options_inifile.comment_prefixes = val

        if hasattr(self.args, "inifile_delimiters"):
            val = self.args.inifile_delimiters
            if val:
                self.config_handler.options_inifile.delimiters = val

        if hasattr(self.args, "inifile_empty_lines_in_values"):
            val = self.args.inifile_empty_lines_in_values
            if not val:
                self.config_handler.options_inifile.empty_lines_in_values = False

        if hasattr(self.args, "inifile_extended_interpolation"):
            val = self.args.inifile_extended_interpolation
            if val:
                self.config_handler.options_inifile.extended_interpolation = True

        if hasattr(self.args, "inifile_inline_comment_prefixes"):
            val = self.args.inifile_inline_comment_prefixes
            if val:
                self.config_handler.options_inifile.inline_comment_prefixes = val

        if hasattr(self.args, "inifile_strict"):
            val = self.args.inifile_strict
            if val:
                self.config_handler.options_inifile.strict = True

        if self.verbose > 1:
            LOG.debug(
                _("Options for reading inifiles:")
                + "\n"
                + pp(self.config_handler.options_inifile.property_dict())
            )

    # -------------------------------------------------------------------------
    def _eval_yaml_args(self):
        """Evaluate options for generating YAML output."""
        if self.verbose > 2:
            LOG.debug(_("Evaluate options for generating YAML output."))

        val = getattr(self.args, "width", None)
        if val is not None:
            self.config_handler.options_yaml.width = val

        val = getattr(self.args, "indent", None)
        if val is not None:
            try:
                self.config_handler.options_yaml.indent = val
            except ValueError as e:
                LOG.error(str(e))
                self.exit(1)

        if hasattr(self.args, "yaml_canonical"):
            val = getattr(self.args, "yaml_canonical", False)
            if val:
                self.config_handler.options_yaml.canonical = True

        if hasattr(self.args, "yaml_no_allow_unicode"):
            val = getattr(self.args, "yaml_no_allow_unicode", False)
            if val:
                self.config_handler.options_yaml.allow_unicode = False

        if hasattr(self.args, "yaml_flow_style"):
            val = getattr(self.args, "yaml_flow_style", False)
            if val:
                self.config_handler.options_yaml.flow_style = True

        if hasattr(self.args, "yaml_style"):
            val = getattr(self.args, "yaml_style", None)
            if val:
                self.config_handler.options_yaml.style = val

        if hasattr(self.args, "yaml_no_explicit_start"):
            val = getattr(self.args, "yaml_no_explicit_start", False)
            if val:
                self.config_handler.options_yaml.explicit_start = False

        if hasattr(self.args, "yaml_explicit_end"):
            val = getattr(self.args, "yaml_explicit_end", False)
            if val:
                self.config_handler.options_yaml.explicit_end = True

        if self.verbose > 1:
            LOG.debug(
                _("Options for generating YAML output:")
                + "\n"
                + pp(self.config_handler.options_yaml.property_dict())
            )

    # -------------------------------------------------------------------------
    def _eval_json_args(self):
        """Evaluate options for generating JSON output."""
        if self.verbose > 2:
            LOG.debug(_("Evaluate options for generating JSON output."))

        val = getattr(self.args, "indent", None)
        if val is not None:
            try:
                self.config_handler.options_json.indent = val
            except ValueError as e:
                LOG.error(str(e))
                self.exit(1)

        if hasattr(self.args, "json_ensure_ascii"):
            val = self.args.json_ensure_ascii
            if val:
                self.config_handler.options_json.ensure_ascii = True

        if hasattr(self.args, "json_sort_keys"):
            val = self.args.json_sort_keys
            if val:
                self.config_handler.options_json.sort_keys = True

        if self.verbose > 1:
            LOG.debug(
                _("Options for generating JSON output:")
                + "\n"
                + pp(self.config_handler.options_json.property_dict())
            )

    # -------------------------------------------------------------------------
    def _eval_hjson_args(self):
        """Evaluate options for generating HJSON output."""
        if self.verbose > 2:
            LOG.debug(_("Evaluate options for generating HJSON output."))

        val = getattr(self.args, "indent", None)
        if val is not None:
            try:
                self.config_handler.options_hjson.indent = val
            except ValueError as e:
                LOG.error(str(e))
                self.exit(1)

        if hasattr(self.args, "hjson_ensure_ascii"):
            val = self.args.hjson_ensure_ascii
            if val:
                self.config_handler.options_hjson.ensure_ascii = True

        if hasattr(self.args, "hjson_sort_keys"):
            val = self.args.hjson_sort_keys
            if val:
                self.config_handler.options_hjson.sort_keys = True

        if self.verbose > 1:
            LOG.debug(
                _("Options for generating HJSON output:")
                + "\n"
                + pp(self.config_handler.options_hjson.property_dict())
            )

    # -------------------------------------------------------------------------
    def _eval_toml_args(self):
        """Evaluate options for generating Toml output."""
        if self.verbose > 2:
            LOG.debug(_("Evaluate options for generating Toml output."))

        val = getattr(self.args, "indent", None)
        if val is not None:
            try:
                self.config_handler.options_toml.indent = val
            except ValueError as e:
                LOG.error(str(e))
                self.exit(1)

        if self.verbose > 1:
            LOG.debug(
                _("Options for generating TOML output:")
                + "\n"
                + pp(self.config_handler.options_toml.property_dict())
            )

    # -------------------------------------------------------------------------
    def _run(self):

        LOG.debug(_("Starting {a!r}, version {v!r} ...").format(a=self.appname, v=self.version))
        ret = 0

        try:
            config_type, config = self.load()
        except ConfigWrongTypeError as e:
            msg = _("Could not read or evaluate configuration file '{}':").format(
                self.colored(str(self.input_file), "red")
            )
            msg += " " + str(e)
            LOG.error(msg)
            self.exit(5)
            return

        self.save(config)

        self.exit(ret)

    # -------------------------------------------------------------------------
    def load(self):
        """Load config file."""
        if self.verbose > 1:
            LOG.debug(
                _("Trying to read from '{}' ...").format(
                    self.colored(str(self.input_file), "cyan")
                )
            )

        config_type, config = self.config_handler.load_file(self.input_file, self.from_type)
        if config_type != self.from_type:
            LOG.debug(
                _("Detected config type of '{infile}': {cfgtype}").format(
                    infile=self.colored(str(self.input_file), "cyan"),
                    cfgtype=self.colored(config_type, "green"),
                )
            )

        return (config_type, config)

    # -------------------------------------------------------------------------
    def save(self, config):
        """Output of converted file in a file or to STDOUT."""
        config_type = self.to_type
        if config_type is None:
            if self.output_file == "-":
                config_type = "dump"
            else:
                try:
                    config_type = self.config_handler.guess_config_type_by_name(
                        self.output_file, raise_on_error=True
                    )
                    LOG.debug(
                        _("Guessed config type of {fo} is '{t}'.").format(
                            fo=self.colored(str(self.output_file), "cyan"),
                            t=self.colored(config_type, "green"),
                        )
                    )
                except ConfigDetectionError as e:
                    LOG.error(str(e))
                    self.exit(1)

        self.config_handler.dump_file(config, self.output_file, config_type=config_type)


# =============================================================================
def main():
    """Entrypoint for config-convert."""
    my_path = Path(__file__)
    appname = my_path.name

    locale.setlocale(locale.LC_ALL, "")

    app = CfgConvertApplication(appname=appname)
    app.initialized = True

    if app.verbose > 2:
        print(_("{c}-Object:\n{a}").format(c=app.__class__.__name__, a=app), file=sys.stderr)

    app()

    sys.exit(0)


# =============================================================================
if __name__ == "__main__":

    pass

# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 list
