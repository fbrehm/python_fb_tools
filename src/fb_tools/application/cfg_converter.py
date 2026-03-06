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
import errno
import importlib
import locale
import logging
import os
import sys
from pathlib import Path

# Third party modules

# Own modules
from .. import MAX_INDENT
from .. import MIN_INDENT
from .. import MAX_TERM_WIDTH
from .. import MIN_TERM_WIDTH
from .. import __version__ as GLOBAL_VERSION
from ..any_config import AnyConfigHandler
from ..app import BaseApplication
from ..argparse_actions import InputFileOptionAction
from ..argparse_actions import OutputFileOptionAction
from ..argparse_actions import RangeOptionAction
from ..common import pp, to_bool
from ..errors import ConfigDetectionError
from ..errors import ConfigError
from ..errors import ConfigWrongTypeError
from ..errors import FbAppError
from ..xlate import DEFAULT_LOCALE
from ..xlate import XLATOR
from ..xlate import format_list

# from ..multi_config import BaseMultiConfig

__version__ = "0.8.0"
LOG = logging.getLogger(__name__)

_ = XLATOR.gettext
ngettext = XLATOR.ngettext


# =============================================================================
class CfgConvertError(FbAppError):
    """Base exception class for all exceptions in this application."""

    pass


# =============================================================================
class InputFileError(CfgConvertError, OSError):
    """Special exception class for the case of errors with the input file."""

    # -------------------------------------------------------------------------
    def __init__(self, err_no, strerror, filename):
        """Initialise a InputFileError exception."""
        super(InputFileError, self).__init__(err_no, strerror, str(filename))


# =============================================================================
class InputFileNotExistingError(InputFileError):
    """Class for a exception in case an input file is not existing."""

    # -------------------------------------------------------------------------
    def __init__(self, filename):
        """Initialise a InputFileNotExistingError exception."""
        msg = _("The input file is not existing")
        super(InputFileNotExistingError, self).__init__(errno.ENOENT, msg, filename)


# =============================================================================
class InputFileNotReadableError(InputFileError):
    """Class for a exception in case an input file is not readable."""

    # -------------------------------------------------------------------------
    def __init__(self, filename):
        """Initialise a InputFileNotReadableError exception."""
        msg = _("The input file is not readable")
        super(InputFileNotReadableError, self).__init__(errno.EACCES, msg, filename)


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

    # json_indent_help = _(
    #     "The indention of the {} output. If given an positive integer value, these "
    #     "number of spaces are indented. I given '0', a negative integer or an empty "
    #     "string (''), only newlines are inserted. If a non empty string is given, this "
    #     "will be used as indention to each level. If omitted, the most compact form without "
    #     "newlines will be generated."
    # )

    # json_sort_help = _("Dictionaries will be outputted sorted by key.")
    # width_help_epilog = _("If not given, the available screen width will be taken.")

    # for cfg_type in CFG_TYPE_READER_MODULE:
    #     module_name = SUPPORTED_CFG_TYPES[cfg_type]
    #     mod_spec = importlib.util.find_spec(module_name)
    #     if mod_spec:
    #         supported_read_cfg_types.append(cfg_type)

    # for cfg_type in CFG_TYPE_WRITER_MODULE:
    #     module_name = CFG_TYPE_WRITER_MODULE[cfg_type]
    #     mod_spec = importlib.util.find_spec(module_name)
    #     if mod_spec:
    #         supported_write_cfg_types.append(cfg_type)

    # for cfg_type in SUPPORTED_CFG_TYPES:
    #     module_name = CFG_TYPE_MODULE[cfg_type]
    #     mod_spec = importlib.util.find_spec(module_name)
    #     if mod_spec:
    #         supported_cfg_types.append(cfg_type)

    # del module_name
    # del mod_spec

    min_width = MIN_TERM_WIDTH
    max_width = MAX_TERM_WIDTH
    min_indent = MIN_INDENT
    max_indent = MAX_INDENT

    # -------------------------------------------------------------------------
    def __init__(self, verbose=0, version=GLOBAL_VERSION, *args, **kwargs):
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

        self.config_handler = None

        super(CfgConvertApplication, self).__init__(
            *args, description=desc, verbose=verbose, version=version, **kwargs
        )

        self.config_handler = AnyConfigHandler(
            appname=self.appname,
            base_dir=self.base_dir,
            terminal_has_colors=self.terminal_has_colors,
            verbose=self.verbose,
        )

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
        if v not in self.config_handler.supported_read_cfg_types:
            msg = _("Invalid input configuration type {!r}").format(value)
            raise WrongCfgTypeError(msg)
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
        if v not in self.config_handler.supported_write_cfg_types:
            msg = _("Invalid target configuration type {!r}").format(value)
            raise WrongCfgTypeError(msg)
        self._to_type = v

    # -------------------------------------------------------------------------
    @property
    def input_file(self):
        """The file name of the input, the source configuration."""
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
        """The file name of the output, the target configuration."""
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

        module_name = CFG_TYPE_READER_MODULE[self.from_type]
        if module_name not in self.cfg_modules:
            LOG.debug(_("Loading module {!r} ...").format(module_name))
            mod = importlib.import_module(module_name)
            self.cfg_modules[module_name] = mod

        module_name = CFG_TYPE_WRITER_MODULE[self.to_type]
        if module_name not in self.cfg_modules:
            LOG.debug(_("Loading module {!r} ...").format(module_name))
            mod = importlib.import_module(module_name)
            self.cfg_modules[module_name] = mod

        self.initialized = True

    # -------------------------------------------------------------------------
    def init_arg_parser(self):
        """Initialise the argument parser."""
        super(CfgConvertApplication, self).init_arg_parser()

        conv_group = self.arg_parser.add_argument_group(_("Converting options"))

        read_type_list = format_list(
            self.supported_read_cfg_types, do_repr=True, style="or", locale=DEFAULT_LOCALE
        )
        conv_group.add_argument(
            "-F",
            "--from-type",
            metavar=_("CFG_TYPE"),
            dest="from_type",
            action=CfgTypeOptionAction,
            supported_types=self.supported_read_cfg_types,
            help=_("The configuration type of the source, must be one of {}.").format(
                read_type_list
            ),
        )

        write_type_list = format_list(
            self.supported_write_cfg_types, do_repr=True, style="or", locale=DEFAULT_LOCALE
        )
        conv_group.add_argument(
            "-T",
            "--to-type",
            metavar=_("CFG_TYPE"),
            dest="to_type",
            action=CfgTypeOptionAction,
            supported_types=self.supported_write_cfg_types,
            help=_("The configuration type of the target, must be one " "of {}.").format(
                write_type_list
            ),
        )

        if "dump" in self.supported_write_cfg_types:
            self._init_dump_args()
        if "yaml" in self.supported_write_cfg_types:
            self._init_yaml_args()
        if "json" in self.supported_write_cfg_types:
            self._init_json_args()
        if "hjson" in self.supported_write_cfg_types:
            self._init_hjson_args()
        if "toml" in self.supported_write_cfg_types:
            self._init_toml_args()

        # file_group = self.arg_parser.add_argument_group(_("File options"))

        self.arg_parser.add_argument(
            "input",
            metavar=_("FILE"),
            dest="input",
            action=InputFileOptionAction,
            help=_(
                "The filename of the input file. Use {i!r} to read from {f} "
                "(which is the default)."
            ).format(i="-", f="STDIN"),
        )

        self.arg_parser.add_argument(
            "output",
            metavar=_("FILE"),
            dest="output",
            action=OutputFileOptionAction,
            help=_(
                "The filename of the output file. Use {i!r} to write to {f} "
                "(which is the default)."
            ).format(i="-", f="STDOUT"),
        )

    # -------------------------------------------------------------------------
    def _init_dump_args(self):
        """Define commandline options for dumping out the read config."""
        dumping_group = self.arg_parser.add_argument_group(_("Dump output options"))

        width_help = (
            _("The maximum width of generated lines on dumping output.")
            + " "
            + self.width_help_epilog
        )

        dumping_group.add_argument(
            "--dump-with",
            metavar="INT",
            dest="dump_width",
            type=int,
            action=RangeOptionAction,
            min_val=10,
            max_val=4000,
            help=width_help,
        )

    # -------------------------------------------------------------------------
    def _init_yaml_args(self):
        """Define commandline options for converting into YAML format."""
        yaml_group = self.arg_parser.add_argument_group(_("YAML output options"))

        width_help = (
            _("The maximum width of generated lines on YAML output.")
            + " "
            + self.width_help_epilog
        )

        yaml_group.add_argument(
            "--yaml-with",
            metavar="INT",
            dest="yaml_width",
            type=int,
            action=RangeOptionAction,
            min_val=10,
            max_val=4000,
            help=width_help,
        )

        yaml_group.add_argument(
            "--yaml-indent",
            metavar="INT",
            dest="yaml_indent",
            type=int,
            action=RangeOptionAction,
            min_val=2,
            max_val=9,
            help=_("The indention of generated YAML output (Default: {}).").format(
                self.yaml_indent
            ),
        )

        yaml_group.add_argument(
            "--yaml-canonical",
            action="store_true",
            dest="yaml_canonical",
            help=_("Include export tag type in YAML output."),
        )

        yaml_group.add_argument(
            "--yaml-flow-style",
            action="store_true",
            dest="yaml_flow_style",
            help=_("Print a collection as flow in YAML output."),
        )

        style_list = format_list(self.yaml_avail_styles, do_repr=True, locale=DEFAULT_LOCALE)
        yaml_group.add_argument(
            "--yaml-style",
            dest="yaml_style",
            nargs="?",
            metavar=_("STYLE"),
            supported_styles=self.yaml_avail_styles,
            action=YamlStyleOptionAction,
            help=_("The style of the scalars in YAML output, may be be one of {}.").format(
                style_list
            ),
        )

        yaml_group.add_argument(
            "--yaml-no-explicit-start",
            action="store_true",
            dest="yaml_no_explicit_start",
            help=_("Don't print an explicit start marker in YAML output."),
        )

        yaml_group.add_argument(
            "--yaml-explicit-end",
            action="store_true",
            dest="yaml_explicit_end",
            help=_("Print an explicit end marker in YAML output."),
        )

    # -------------------------------------------------------------------------
    def _init_json_args(self):
        """Define commandline options for converting into JSON format."""
        if self.to_type and self.to_type != "json":
            return

        json_group = self.arg_parser.add_argument_group(_("JSON output options"))

        json_group.add_argument(
            "--json-ensure-ascii",
            action="store_true",
            dest="json_ensure_ascii",
            help=_(
                "The {} output is guaranteed to have all incoming non-ASCII characters escaped."
            ).format("JSON"),
        )

        json_group.add_argument(
            "--json-indent",
            metavar="INDENT",
            dest="json_indent",
            help=self.json_indent_help.format("JSON"),
        )

        json_group.add_argument(
            "--json-sort-keys",
            action="store_true",
            dest="json_sort_keys",
            help=self.json_sort_help,
        )

    # -------------------------------------------------------------------------
    def _init_hjson_args(self):
        """Define commandline options for converting into HJSON format."""
        if self.to_type and self.to_type != "hjson":
            return

        hjson_group = self.arg_parser.add_argument_group(_("HJSON output options"))

        hjson_group.add_argument(
            "--hjson-ensure-ascii",
            action="store_true",
            dest="hjson_ensure_ascii",
            help=_(
                "The {} output is guaranteed to have all incoming " "non-ASCII characters escaped."
            ).format("HJSON"),
        )

        hjson_group.add_argument(
            "--hjson-indent",
            metavar="INDENT",
            dest="hjson_indent",
            help=self.json_indent_help.format("HJSON"),
        )

        hjson_group.add_argument(
            "--hjson-sort-keys",
            action="store_true",
            dest="hjson_sort_keys",
            help=self.json_sort_help,
        )

    # -------------------------------------------------------------------------
    def perform_arg_parser(self):
        """Parse the command line options."""
        from_type = getattr(self.args, "from_type", None)
        if from_type:
            self.from_type = from_type

        to_type = getattr(self.args, "to_type", None)
        if to_type:
            self.to_type = to_type

        self.input_file = getattr(self.args, "input", None)
        self.output = getattr(self.args, "output", None)

        val = getattr(self.args, "yaml_width", None)
        if val is not None:
            self.yaml_width = val

        val = getattr(self.args, "yaml_indent", None)
        if val is not None:
            self.yaml_indent = val

        if getattr(self.args, "yaml_canonical", False):
            self.yaml_canonical = True

        if getattr(self.args, "yaml_flow_style", False):
            self.yaml_default_flow_style = True

        val = getattr(self.args, "yaml_style", None)
        if val is not None:
            self.yaml_default_style = val

        if getattr(self.args, "yaml_no_explicit_start", False):
            self.yaml_explicit_start = False

        if getattr(self.args, "yaml_explicit_end", False):
            self.yaml_explicit_end = True

        if getattr(self.args, "json_ensure_ascii", False):
            self.json_ensure_ascii = True

        val = getattr(self.args, "json_indent", None)
        if val is not None:
            self.json_indent = val

        if getattr(self.args, "json_sort_keys", False):
            self.json_sort_keys = True

        if getattr(self.args, "hjson_ensure_ascii", False):
            self.hjson_ensure_ascii = True

        val = getattr(self.args, "hjson_indent", None)
        if val is not None:
            self.hjson_indent = val

        if getattr(self.args, "hjson_sort_keys", False):
            self.hjson_sort_keys = True

    # -------------------------------------------------------------------------
    def _run(self):

        LOG.debug(_("Starting {a!r}, version {v!r} ...").format(a=self.appname, v=self.version))
        ret = 0

        try:
            self.load()
        except WrongCfgTypeError as e:
            LOG.error(str(e))
            self.exit(5)
            return

        self.save()

        self.exit(ret)

    # -------------------------------------------------------------------------
    def load(self):
        """Load config file."""
        content = None
        if self.input_file == "-":
            content = sys.stdin.read()
        else:
            content = self.read_file(self.input_file)

        lmethod = getattr(self.__class__, self.loader_methods[self.from_type])
        lmethod(self, content)

        if self.verbose > 1:
            msg = _("Interpreted content of {!r}:").format(self.input_file)
            LOG.debug(msg + "\n" + pp(self.cfg_content))

    # -------------------------------------------------------------------------
    def load_yaml(self, content):
        """Load config file in YAML format."""
        LOG.debug(_("Loading content from {!r} format.").format("YAML"))

        mod = self.cfg_modules["yaml"]

        docs = []
        try:
            for doc in mod.safe_load_all(content):
                docs.append(doc)
        except Exception as e:
            if e.__class__.__name__ == "ParserError":
                raise WrongCfgTypeError("YAML ParseError: " + str(e))
            raise
        if not docs:
            self.cfg_content = None
            return
        if len(docs) == 1:
            self.cfg_content = docs[0]
        self.cfg_content = docs

    # -------------------------------------------------------------------------
    def load_json(self, content):
        """Load config file in JSON format."""
        LOG.debug(_("Loading content from {!r} format.").format("JSON"))

        mod = self.cfg_modules["json"]
        try:
            doc = mod.loads(content)
        except Exception as e:
            if e.__class__.__name__ == "JSONDecodeError":
                raise WrongCfgTypeError("JSONDecodeError: " + str(e))
            raise

        self.cfg_content = doc

    # -------------------------------------------------------------------------
    def load_hjson(self, content):
        """Load config file in HJSON format."""
        LOG.debug(_("Loading content from {!r} format.").format("HJSON"))

        mod = self.cfg_modules["hjson"]
        try:
            doc = mod.loads(content)
        except Exception as e:
            if e.__class__.__name__ == "HjsonDecodeError":
                raise WrongCfgTypeError("HjsonDecodeError: " + str(e))
            raise

        self.cfg_content = doc

    # -------------------------------------------------------------------------
    def save(self):
        """Output of converted file in a file or to STDOUT."""
        dmethod = getattr(self.__class__, self.dumper_methods[self.to_type])
        content = dmethod(self)

        if self.verbose > 2:
            LOG.debug(_("Generated output:") + "\n" + content)

        if self.output == "-":
            print(content)
        else:
            self.write_file(self.output, content)

    # -------------------------------------------------------------------------
    def dump_yaml(self):
        """Return content of config file in YAML format."""
        LOG.debug(_("Dumping content to {!r} format.").format("YAML"))

        mod = self.cfg_modules["yaml"]
        content = mod.dump(
            self.cfg_content,
            width=self.yaml_width,
            indent=self.yaml_indent,
            canonical=self.yaml_canonical,
            default_flow_style=self.yaml_default_flow_style,
            default_style=self.yaml_default_style,
            allow_unicode=self.yaml_allow_unicode,
            line_break=self.yaml_line_break,
            explicit_start=self.yaml_explicit_start,
            explicit_end=self.yaml_explicit_end,
        )

        return content

    # -------------------------------------------------------------------------
    def dump_json(self):
        """Return content of config file in JSON format."""
        LOG.debug(_("Dumping content to {!r} format.").format("JSON"))

        mod = self.cfg_modules["json"]
        item_separator = ", "
        key_separator = ": "
        ind = self.json_indent

        if ind is None:
            item_separator = ","
            key_separator = ":"
        else:
            if ind == "":
                item_separator = ","
            else:
                try:
                    ind_int = int(self.json_indent)
                    if ind_int <= 0:
                        item_separator = ","
                    ind = ind_int
                except Exception:
                    pass

        content = mod.dumps(
            self.cfg_content,
            ensure_ascii=self.json_ensure_ascii,
            indent=ind,
            separators=(item_separator, key_separator),
            sort_keys=self.json_sort_keys,
        )

        return content

    # -------------------------------------------------------------------------
    def dump_hjson(self):
        """Return content of config file in HJSON format."""
        LOG.debug(_("Dumping content to {!r} format.").format("HJSON"))

        mod = self.cfg_modules["hjson"]
        ind = self.hjson_indent
        try:
            ind_int = int(ind)
            ind = ind_int
        except Exception:
            pass

        content = mod.dumps(
            self.cfg_content,
            ensure_ascii=self.hjson_ensure_ascii,
            indent=ind,
            sort_keys=self.hjson_sort_keys,
        )

        return content


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
