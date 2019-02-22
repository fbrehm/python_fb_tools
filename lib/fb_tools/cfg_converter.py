#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: Frank Brehm
@contact: frank.brehm@pixelpark.com
@copyright: © 2019 by Frank Brehm, Berlin
@summary: The module for the config-converter application object.
"""
from __future__ import absolute_import, print_function

# Standard modules
import logging
import argparse
import pathlib
import errno
import os
import importlib
import sys
import copy

from pathlib import Path

# Third party modules

import babel

# Own modules
from . import __version__ as GLOBAL_VERSION

from .xlate import XLATOR, DEFAULT_LOCALE, format_list

from .common import pp, to_bool

from .app import BaseApplication

from .errors import FbAppError

__version__ = '0.4.4'
LOG = logging.getLogger(__name__)

SUPPORTED_CFG_TYPES = ('json', 'hjson', 'yaml')
CFG_TYPE_MODULE = {
    'json': 'json',
    'hjson': 'hjson',
    'yaml': 'yaml',
}

_ = XLATOR.gettext
ngettext = XLATOR.ngettext


# =============================================================================
class CfgConvertError(FbAppError):
    """Base exception class for all exceptions in this application."""
    pass


# =============================================================================
class WrongCfgTypeError(CfgConvertError, ValueError):
    """Special exception class for the case of wrong configuration type."""
    pass


# =============================================================================
class InputFileError(CfgConvertError, OSError):
    """Special exception class for the case of errors with the input file."""

    # -------------------------------------------------------------------------
    def __init__(self, err_no, strerror, filename):

        super(InputFileError, self).__init__(err_no, strerror, str(filename))


# =============================================================================
class InputFileNotExistingError(InputFileError):

    # -------------------------------------------------------------------------
    def __init__(self, filename):

        msg = _("The input file is not existing")
        super(InputFileNotExistingError, self).__init__(
            errno.ENOENT, msg, filename)


# =============================================================================
class InputFileNotReadableError(InputFileError):

    # -------------------------------------------------------------------------
    def __init__(self, filename):

        msg = _("The input file is not readable")
        super(InputFileNotReadableError, self).__init__(
            errno.EACCES, msg, filename)


# =============================================================================
class CfgTypeOptionAction(argparse.Action):

    # -------------------------------------------------------------------------
    def __init__(self, option_strings, supported_types, *args, **kwargs):

        self.supported_types = copy.copy(supported_types)

        super(CfgTypeOptionAction, self).__init__(
            option_strings=option_strings, *args, **kwargs)

    # -------------------------------------------------------------------------
    def __call__(self, parser, namespace, cfg_type, option_string=None):

        if cfg_type is None:
            msg = _("The configuration file type may not be None.")
            raise argparse.ArgumentError(self, msg)

        cfg_type_clean = cfg_type.strip().lower()
        if cfg_type_clean not in self.supported_types:
            msg = _(
                "The configuration file type must be one of {l}, given {g!r}.").format(
                    l=format_list(self.supported_types, do_repr=True, locale=DEFAULT_LOCALE),
                    g=cfg_type)
            raise argparse.ArgumentError(self, msg)

        setattr(namespace, self.dest, cfg_type_clean)
        return


# =============================================================================
class InputFileOptionAction(argparse.Action):

    # -------------------------------------------------------------------------
    def __init__(self, option_strings, *args, **kwargs):

        super(InputFileOptionAction, self).__init__(
            option_strings=option_strings, *args, **kwargs)

    # -------------------------------------------------------------------------
    def __call__(self, parser, namespace, filename, option_string=None):

        if filename is None or filename == '-' or filename == '':
            setattr(namespace, self.dest, '-')
            return
        path = Path(filename)
        if not path.exists():
            err = InputFileNotExistingError(path)
            raise argparse.ArgumentError(self, str(err))
        if not os.access(str(path), os.R_OK):
            err = InputFileNotReadableError(path)
            raise argparse.ArgumentError(self, str(err))
        setattr(namespace, self.dest, path)


# =============================================================================
class OutputFileOptionAction(argparse.Action):

    # -------------------------------------------------------------------------
    def __init__(self, option_strings, *args, **kwargs):

        super(OutputFileOptionAction, self).__init__(
            option_strings=option_strings, *args, **kwargs)

    # -------------------------------------------------------------------------
    def __call__(self, parser, namespace, filename, option_string=None):

        if filename is None or filename == '-' or filename == '':
            setattr(namespace, self.dest, '-')
            return
        path = Path(filename)
        setattr(namespace, self.dest, path)


# =============================================================================
class RangeOptionAction(argparse.Action):

    # -------------------------------------------------------------------------
    def __init__(self, option_strings, min_val, max_val, *args, **kwargs):

        self._min_val = min_val
        self._max_val = max_val

        super(RangeOptionAction, self).__init__(
            option_strings=option_strings, *args, **kwargs)

    # -------------------------------------------------------------------------
    def __call__(self, parser, namespace, value, option_string=None):

        if value < self._min_val:
            msg = _("The value for {l!r} may be at least {m}, {v} were given.").format(
                l=option_string, m=self._min_val, v=value)
            raise argparse.ArgumentError(self, msg)

        if value > self._max_val:
            msg = _("The value for {l!r} may be at most {m}, {v} were given.").format(
                l=option_string, m=self._max_val, v=value)
            raise argparse.ArgumentError(self, msg)

        setattr(namespace, self.dest, value)


# =============================================================================
class YamlStyleOptionAction(argparse.Action):

    # -------------------------------------------------------------------------
    def __init__(self, option_strings, supported_styles, *args, **kwargs):

        self.supported_styles = copy.copy(supported_styles)

        super(YamlStyleOptionAction, self).__init__(
            option_strings=option_strings, *args, **kwargs)

    # -------------------------------------------------------------------------
    def __call__(self, parser, namespace, style, option_string=None):

        if style is None:
            setattr(namespace, self.dest, None)
            return

        style_clean = style.strip()
        if style_clean not in self.supported_styles:
            msg = _(
                "The YAML style type must be one of {l}, given {g!r}.").format(
                    l=format_list(self.supported_styles, do_repr=True,
                    locale=DEFAULT_LOCALE), g=style)
            raise argparse.ArgumentError(self, msg)

        setattr(namespace, self.dest, style_clean)
        return


# =============================================================================
class CfgConvertApplication(BaseApplication):
    """
    Class for the application objects.
    """

    supported_cfg_types = []
    module_name = None
    mod_spec = None

    loader_methods = {
        'yaml': 'load_yaml',
        'json': 'load_json',
        'hjson': 'load_hjson',
    }

    dumper_methods = {
        'yaml': 'dump_yaml',
        'json': 'dump_json',
        'hjson': 'dump_hjson',
    }

    yaml_avail_styles = (None, '', '\'', '"', '|', '>')
    yaml_avail_linebreaks = (None, '\n', '\r', '\r\n')

    for cfg_type in SUPPORTED_CFG_TYPES:
        module_name = CFG_TYPE_MODULE[cfg_type]
        mod_spec = importlib.util.find_spec(module_name)
        if mod_spec:
            supported_cfg_types.append(cfg_type)

    del module_name
    del mod_spec

    # -------------------------------------------------------------------------
    def __init__(
        self, from_type=None, to_type=None,
            appname=None, verbose=0, version=GLOBAL_VERSION, base_dir=None,
            initialized=False, usage=None, description=None,
            argparse_epilog=None, argparse_prefix_chars='-', env_prefix=None):

        desc = description
        if not desc:
            desc = _(
                "Converts the given configuration file from the given input format "
                "into the given output format and print it out to {o} "
                "or into a given output file.").format(o='STDOUT')

        self.cfg_files = []
        self._from_type = None
        self._to_type = None
        self._input = '-'
        self._output = '-'
        self.cfg_content = None
        self.cfg_modules = {}

        self.from_type = from_type
        self.to_type = to_type

        self._cfg_encoding = 'utf-8'

        self._yaml_width = 99
        self._yaml_indent = 2
        self._yaml_canonical = False
        self._yaml_default_flow_style = False
        self._yaml_default_style = None
        self._yaml_allow_unicode = True
        self._yaml_line_break = None
        self._yaml_explicit_start = True
        self._yaml_explicit_end = False

        self._json_ensure_ascii = False
        self.json_indent = None
        self._json_sort_keys = False

        super(CfgConvertApplication, self).__init__(
            appname=appname, verbose=verbose, version=version, base_dir=base_dir,
            description=desc, initialized=False,
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
        if v not in self.supported_cfg_types:
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
        if v not in self.supported_cfg_types:
            msg = _("Invalid target configuration type {!r}").format(value)
            raise WrongCfgTypeError(msg)
        self._to_type = v

    # -------------------------------------------------------------------------
    @property
    def input(self):
        """The file name of the input, the source configuration."""
        return self._input

    @input.setter
    def input(self, value):
        if value is None:
            self._input = '-'
            return
        path = value
        if not isinstance(value, Path):
            v = str(value).strip()
            if v == '':
                self._input = '-'
                return
            path = Path(v)

        if not path.exists():
            raise InputFileNotExistingError(path)
        if not os.access(str(path), os.R_OK):
            raise InputFileNotReadableError(path)
        self._input = path

    # -------------------------------------------------------------------------
    @property
    def output(self):
        """The file name of the output, the target configuration."""
        return self._output

    @output.setter
    def output(self, value):
        if value is None:
            self._output = '-'
            return
        path = value
        if not isinstance(value, Path):
            v = str(value).strip()
            if v == '':
                self._output = '-'
                return
            path = Path(v)

        self._output = path

    # -------------------------------------------------------------------------
    @property
    def yaml_width(self):
        """Maximum width of generated lines on YAML output."""
        return self._yaml_width

    @yaml_width.setter
    def yaml_width(self, value):
        v = int(value)
        if v < 10:
            msg = _(
                "The maximum width of generated YAML files must be at least "
                "{m} characters, {v!r} are given.").format(m=10, v=value)
            raise ValueError(msg)
        if v > 4000:
            msg = _(
                "The maximum width of generated YAML files must be at most "
                "{m} characters, {v!r} are given.").format(m=4000, v=value)
            raise ValueError(msg)
        self._yaml_width = v

    # -------------------------------------------------------------------------
    @property
    def yaml_indent(self):
        """The indention of generated YAML output."""
        return self._yaml_indent

    @yaml_indent.setter
    def yaml_indent(self, value):
        v = int(value)
        if v < 2:
            msg = _(
                "The indention of generated YAML files must be at least "
                "{m} characters, {v!r} are given.").format(m=2, v=value)
            raise ValueError(msg)
        if v > 40:
            msg = _(
                "The indention of generated YAML files must be at most "
                "{m} characters, {v!r} are given.").format(m=40, v=value)
            raise ValueError(msg)
        self._yaml_indent = v

    # -------------------------------------------------------------------------
    @property
    def yaml_canonical(self):
        """Output YAML in canonical style."""
        return self._yaml_canonical

    @yaml_canonical.setter
    def yaml_canonical(self, value):
        self._yaml_canonical = to_bool(value)

    # -------------------------------------------------------------------------
    @property
    def yaml_default_flow_style(self):
        """Output YAML in default flow style."""
        return self._yaml_default_flow_style

    @yaml_default_flow_style.setter
    def yaml_default_flow_style(self, value):
        self._yaml_default_flow_style = to_bool(value)

    # -------------------------------------------------------------------------
    @property
    def yaml_default_style(self):
        """Style for outputting YAML."""
        return self._yaml_default_style

    @yaml_default_style.setter
    def yaml_default_style(self, value):
        if value is None:
            self._yaml_default_style = None
            return
        v = str(value).strip()
        if v not in self.yaml_avail_styles:
            style_list = format_list(self.yaml_avail_styles, do_repr=True, locale=DEFAULT_LOCALE)
            msg = _(
                "The default style on ouput YAML must be one of {l}, "
                "but {v!r} was given.").format(l=style_list, v=value)
            raise ValueError(msg)

        self._yaml_default_style = v

    # -------------------------------------------------------------------------
    @property
    def yaml_allow_unicode(self):
        """Are Unicode characters allowed in YAML output."""
        return self._yaml_allow_unicode

    @yaml_allow_unicode.setter
    def yaml_allow_unicode(self, value):
        self._yaml_allow_unicode = to_bool(value)

    # -------------------------------------------------------------------------
    @property
    def yaml_explicit_start(self):
        """Should be added an explicite start in YAML output."""
        return self._yaml_explicit_start

    @yaml_explicit_start.setter
    def yaml_explicit_start(self, value):
        self._yaml_explicit_start = to_bool(value)

    # -------------------------------------------------------------------------
    @property
    def yaml_explicit_end(self):
        """Should be added an explicite end in YAML output."""
        return self._yaml_explicit_end

    @yaml_explicit_end.setter
    def yaml_explicit_end(self, value):
        self._yaml_explicit_end = to_bool(value)

    # -------------------------------------------------------------------------
    @property
    def yaml_line_break(self):
        """The character(s) used for linebreak in YAML output."""
        return self._yaml_line_break

    @yaml_line_break.setter
    def yaml_line_break(self, value):
        if value is None:
            self._yaml_line_break = None
            return
        v = str(value).strip()
        if v not in self.yaml_avail_linebreaks:
            lb_list = format_list(self.yaml_avail_linebreaks, do_repr=True, locale=DEFAULT_LOCALE)
            msg = _(
                "The linebrake used in ouput YAML must be one of {l}, "
                "but {v!r} was given.").format(l=lb_list, v=value)
            raise ValueError(msg)

        self._yaml_line_break = v

    # -------------------------------------------------------------------------
    @property
    def json_ensure_ascii(self):
        """Indicating that the JSON output is guaranteed to have
            all incoming non-ASCII characters escaped."""
        return self._json_ensure_ascii

    @json_ensure_ascii.setter
    def json_ensure_ascii(self, value):
        self._json_ensure_ascii = to_bool(value)

    # -------------------------------------------------------------------------
    @property
    def json_sort_keys(self):
        """Are Unicode characters allowed in YAML output."""
        return self._json_sort_keys

    @json_sort_keys.setter
    def json_sort_keys(self, value):
        self._json_sort_keys = to_bool(value)

    # -------------------------------------------------------------------------
    def as_dict(self, short=True):
        """
        Transforms the elements of the object into a dict

        @param short: don't include local properties in resulting dict.
        @type short: bool

        @return: structure as dict
        @rtype:  dict
        """

        res = super(CfgConvertApplication, self).as_dict(short=short)
        res['from_type'] = self.from_type
        res['to_type'] = self.to_type
        res['input'] = self.input
        res['output'] = self.output
        res['supported_cfg_types'] = self.supported_cfg_types
        res['yaml_avail_styles'] = self.yaml_avail_styles
        res['yaml_width'] = self.yaml_width
        res['yaml_indent'] = self.yaml_indent
        res['yaml_canonical'] = self.yaml_canonical
        res['yaml_default_flow_style'] = self.yaml_default_flow_style
        res['yaml_default_style'] = self.yaml_default_style
        res['yaml_allow_unicode'] = self.yaml_allow_unicode
        res['yaml_avail_linebreaks'] = self.yaml_avail_linebreaks
        res['yaml_line_break'] = self.yaml_line_break
        res['yaml_explicit_start'] = self.yaml_explicit_start
        res['yaml_explicit_end'] = self.yaml_explicit_end
        res['json_ensure_ascii'] = self.json_ensure_ascii
        res['json_sort_keys'] = self.json_sort_keys

        return res

    # -------------------------------------------------------------------------
    def post_init(self):
        """
        Method to execute before calling run(). Here could be done some
        finishing actions after reading in commandline parameters,
        configuration a.s.o.

        This method could be overwritten by descendant classes, these
        methhods should allways include a call to post_init() of the
        parent class.

        """

        self.initialized = False

        self.init_logging()

        self.perform_arg_parser()

        module_name = CFG_TYPE_MODULE[self.from_type]
        if module_name not in self.cfg_modules:
            LOG.debug(_("Loading module {!r} ...").format(module_name))
            mod = importlib.import_module(module_name)
            self.cfg_modules[module_name] = mod

        module_name = CFG_TYPE_MODULE[self.to_type]
        if module_name not in self.cfg_modules:
            LOG.debug(_("Loading module {!r} ...").format(module_name))
            mod = importlib.import_module(module_name)
            self.cfg_modules[module_name] = mod

        self.initialized = True

    # -------------------------------------------------------------------------
    def init_arg_parser(self):
        """
        Public available method to initiate the argument parser.
        """



        super(CfgConvertApplication, self).init_arg_parser()

        file_group = self.arg_parser.add_argument_group(_('File options'))

        file_group.add_argument(
            '-i', '--input', metavar=_('FILE'), dest='input',
            action=InputFileOptionAction, help=_(
                "The filename of the input file. Use {i!r} to read from {f} "
                "(which is the default).").format(i='-', f='STDIN'),
        )

        file_group.add_argument(
            '-o', '--output', metavar=_('FILE'), dest='output',
            action=OutputFileOptionAction, help=_(
                "The filename of the output file. Use {i!r} to write to {f} "
                "(which is the default).").format(i='-', f='STDOUT'),
        )

        if not self.from_type or not self.to_type:

            conv_group = self.arg_parser.add_argument_group(_('Converting options'))
            type_list = format_list(
                self.supported_cfg_types, do_repr=True, style='or', locale=DEFAULT_LOCALE)

            if not self.from_type:
                conv_group.add_argument(
                    '-F', '--from-type', metavar=_('CFG_TYPE'), dest='from_type',
                    required=True, action=CfgTypeOptionAction,
                    supported_types=self.supported_cfg_types,
                    help=_(
                        "The configuration type of the source, must be one "
                        "of {}.").format(type_list),
                )

            if not self.to_type:
                conv_group.add_argument(
                    '-T', '--to-type', metavar=_('CFG_TYPE'), dest='to_type',
                    required=True, action=CfgTypeOptionAction,
                    supported_types=self.supported_cfg_types,
                    help=_(
                        "The configuration type of the target, must be one "
                        "of {}.").format(type_list),
                )

        self.init_yaml_args()
        self.init_json_args()

    # -------------------------------------------------------------------------
    def init_yaml_args(self):

        if self.to_type and self.to_type != 'yaml':
            return

        yaml_group = self.arg_parser.add_argument_group(_('YAML output options'))

        yaml_group.add_argument(
            '--yaml-with', metavar='INT', dest='yaml_width', type=int,
            action=RangeOptionAction, min_val=10, max_val=4000,
            help=_("The maximum width of generated lines on YAML output (Default: {}).").format(
                self.yaml_width))

        yaml_group.add_argument(
            '--yaml-indent', metavar='INT', dest='yaml_indent', type=int,
            action=RangeOptionAction, min_val=2, max_val=9,
            help=_("The indention of generated YAML output (Default: {}).").format(
                self.yaml_indent))

        yaml_group.add_argument(
            '--yaml-canonical', action="store_true", dest="yaml_canonical",
            help=_("Include export tag type in YAML output."))

        yaml_group.add_argument(
            '--yaml-flow-style', action="store_true", dest="yaml_flow_style",
            help=_("Print a collection as flow in YAML output."))

        style_list = format_list(self.yaml_avail_styles, do_repr=True, locale=DEFAULT_LOCALE)
        yaml_group.add_argument(
            '--yaml-style', dest="yaml_style", nargs='?', metavar=_('STYLE'),
            supported_styles=self.yaml_avail_styles, action=YamlStyleOptionAction,
            help=_("The style of the scalars in YAML output, may be be one of {}.").format(
                style_list))

        yaml_group.add_argument(
            '--yaml-no-explicit-start', action="store_true", dest="yaml_no_explicit_start",
            help=_("Don't print an explicit start marker in YAML output."))

        yaml_group.add_argument(
            '--yaml-explicit-end', action="store_true", dest="yaml_explicit_end",
            help=_("Print an explicit end marker in YAML output."))

    # -------------------------------------------------------------------------
    def init_json_args(self):

        if self.to_type and self.to_type != 'json':
            return

        json_group = self.arg_parser.add_argument_group(_('JSON output options'))

        json_group.add_argument(
            '--json-ensure-ascii', action="store_true", dest="json_ensure_ascii",
            help=_(
                "The JSON output is guaranteed to have all incoming "
                "non-ASCII characters escaped. "))

        json_group.add_argument(
            '--json-indent', metavar='INDENT', dest='json_indent', help=_(
                "The indention of the JSON output. If given an positive integer value, these "
                "number of characters are indented. I given '0', a negative integer or  an empty "
                "string (''), only newlines are inserted. If a non empty string is given, this "
                "will be used as indention. If omitted, the most compact form without newlines "
                "a.s.o. will be generated."))

        json_group.add_argument(
            '--json-sort-keys', action="store_true", dest="json_sort_keys",
            help=_("The keys of dictionaries will be sorted in JSON output."))

    # -------------------------------------------------------------------------
    def perform_arg_parser(self):
        """
        Public available method to execute some actions after parsing
        the command line parameters.
        """

        from_type = getattr(self.args, 'from_type', None)
        if from_type:
            self.from_type = from_type

        to_type = getattr(self.args, 'to_type', None)
        if to_type:
            self.to_type = to_type

        self.input = getattr(self.args, 'input', None)
        self.output = getattr(self.args, 'output', None)

        val = getattr(self.args, 'yaml_width', None)
        if val is not None:
            self.yaml_width = val

        val = getattr(self.args, 'yaml_indent', None)
        if val is not None:
            self.yaml_indent = val

        if getattr(self.args, 'yaml_canonical', False):
            self.yaml_canonical = True

        if getattr(self.args, 'yaml_flow_style', False):
            self.yaml_default_flow_style = True

        val = getattr(self.args, 'yaml_style', None)
        if val is not None:
            self.yaml_default_style = val

        if getattr(self.args, 'yaml_no_explicit_start', False):
            self.yaml_explicit_start = False

        if getattr(self.args, 'yaml_explicit_end', False):
            self.yaml_explicit_end = True

        if getattr(self.args, 'json_ensure_ascii', False):
            self.json_ensure_ascii = True

        val = getattr(self.args, 'json_indent', None)
        if val is not None:
            self.json_indent = val

        if getattr(self.args, 'json_sort_keys', False):
            self.json_sort_keys = True

    # -------------------------------------------------------------------------
    def _run(self):

        LOG.debug(_("Starting {a!r}, version {v!r} ...").format(
            a=self.appname, v=self.version))
        ret = 0

        try:
            self.load()
        except WrongCfgTypeError as e:
            LOG.error(str(e))
            self.exit(5)
            return

        self.save()

#        ret = 99
#        try:
#            ret = self.get_vms()
#        finally:
#            # Aufräumen ...
#            LOG.debug(_("Closing ..."))
#            self.vsphere.disconnect()
#            self.vsphere = None

        self.exit(ret)

    # -------------------------------------------------------------------------
    def load(self):

        content = None
        if self.input == '-':
            content = sys.stdin.read()
        else:
            content = self.read_file(self.input)

        lmethod = getattr(self.__class__, self.loader_methods[self.from_type])
        lmethod(self, content)

        if self.verbose > 1:
            LOG.debug(_("Interpreted content of {!r}:").format(self.input) + '\n' + pp(self.cfg_content))

    # -------------------------------------------------------------------------
    def load_yaml(self, content):

        LOG.debug(_("Loading content from {!r} format.").format('YAML'))

        mod = self.cfg_modules['yaml']

        docs = []
        try:
            for doc in mod.safe_load_all(content):
                docs.append(doc)
        except Exception as e:
            if e.__class__.__name__ == 'ParserError':
                raise WrongCfgTypeError('YAML ParseError: ' + str(e))
            raise
        if not docs:
            self.cfg_content = None
            return
        if len(docs) == 1:
            self.cfg_content = docs[0]
        self.cfg_content = docs

    # -------------------------------------------------------------------------
    def load_json(self, content):

        LOG.debug(_("Loading content from {!r} format.").format('JSON'))

        mod = self.cfg_modules['json']
        try:
            doc = mod.loads(content)
        except Exception as e:
            if e.__class__.__name__ == 'JSONDecodeError':
                raise WrongCfgTypeError('JSONDecodeError: ' + str(e))
            raise

        self.cfg_content = doc

    # -------------------------------------------------------------------------
    def load_hjson(self, content):

        LOG.debug(_("Loading content from {!r} format.").format('HJSON'))

        mod = self.cfg_modules['hjson']
        try:
            doc = mod.loads(content)
        except Exception as e:
            if e.__class__.__name__ == 'HjsonDecodeError':
                raise WrongCfgTypeError('HjsonDecodeError: ' + str(e))
            raise

        self.cfg_content = doc

    # -------------------------------------------------------------------------
    def save(self):

        dmethod = getattr(self.__class__, self.dumper_methods[self.to_type])
        content = dmethod(self)

        if self.verbose > 2:
            LOG.debug(_("Generated output:") + '\n' + content)

        if self.output == '-':
            print(content)
        else:
            self.write_file(self.output, content)

    # -------------------------------------------------------------------------
    def dump_yaml(self):

        LOG.debug(_("Dumping content to {!r} format.").format('YAML'))

        mod = self.cfg_modules['yaml']
        content = mod.dump(
            self.cfg_content,
            width=self.yaml_width, indent=self.yaml_indent, canonical=self.yaml_canonical,
            default_flow_style=self.yaml_default_flow_style, default_style=self.yaml_default_style,
            allow_unicode=self.yaml_allow_unicode, line_break=self.yaml_line_break,
            explicit_start=self.yaml_explicit_start, explicit_end=self.yaml_explicit_end,
        )

        return content

    # -------------------------------------------------------------------------
    def dump_json(self):

        LOG.debug(_("Dumping content to {!r} format.").format('JSON'))

        mod = self.cfg_modules['json']
        item_separator = ', '
        key_separator = ': '
        ind = self.json_indent

        if ind is None:
            item_separator = ','
            key_separator = ':'
        else:
            if ind == '':
                item_separator = ','
            else:
                try:
                    ind_int = int(self.json_indent)
                    if ind_int <= 0:
                        item_separator = ','
                    ind = ind_int
                except Exception:
                    pass

        content = mod.dumps(
            self.cfg_content,
            ensure_ascii=self.json_ensure_ascii,
            indent=ind,
            separators=(item_separator, key_separator),
            sort_keys=self.json_sort_keys)

        return content


# =============================================================================
if __name__ == "__main__":

    pass

# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 list
