#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@summary: A module for reading and writing a configuration of different configuration formats.

@author: Frank Brehm
@contact: frank@brehm-online.com
@copyright: © 2018 - 2026 by Frank Brehm, Berlin
"""

from __future__ import absolute_import

# Standard module
import codecs
import copy
import importlib.util
import logging
import re
import shutil
import sys
from configparser import ExtendedInterpolation
from pathlib import Path

# Third party modules
import chardet

# Own modules
from . import DEFAULT_ENCODING
from . import DEFAULT_TERMINAL_HEIGHT, DEFAULT_TERMINAL_WIDTH
from .cfg_options.dump import ConfigOptionsDump
from .cfg_options.hjson import ConfigOptionsHJson
from .cfg_options.inifile import ConfigOptionsInifile
from .cfg_options.json import ConfigOptionsJson
from .cfg_options.toml import ConfigOptionsToml
from .cfg_options.yaml import ConfigOptionsYaml
from .common import pp, to_bool
from .errors import ConfigDetectionError
from .errors import ConfigError
from .errors import ConfigWrongTypeError
from .errors import ReadTimeoutError
from .handling_obj import HandlingObject
from .xlate import XLATOR

__version__ = "0.6.8"

LOG = logging.getLogger(__name__)

_ = XLATOR.gettext

CFG_TYPE_READER_MODULE = {
    "ini": "configparser",
    "json": "json",
    "hjson": "hjson",
    "toml": "tomli",
    "yaml": "yaml",
}

if sys.version_info.major > 3 or (sys.version_info.major == 3 and sys.version_info.minor >= 11):
    CFG_TYPE_READER_MODULE["toml"] = "tomllib"

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

    Public attributes:
    * add_search_paths          (Array of pathlib.Path) (inherited from HandlingObject)
    * cfg_modules               (Array of str)
    * options_dump              (ConfigOptionsDump)
    * options_hjson             (ConfigOptionsHJson)
    * options_inifile           (ConfigOptionsInifile)
    * options_json              (ConfigOptionsJson)
    * options_toml              (ConfigOptionsToml)
    * options_yaml              (ConfigOptionsYaml)
    * signals_dont_interrupt    (Array of int)          (inherited from HandlingObject)
    """

    default_encoding = DEFAULT_ENCODING

    chardet_min_level_confidence = 1.0 / 3

    modules_read = {}
    modules_write = {}
    supported_read_cfg_types = []
    supported_write_cfg_types = []
    default_width = 99

    loader_methods = {
        "ini": "load_inifile",
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
            modules_read[cfg_type] = module_name

    for cfg_type in CFG_TYPE_WRITER_MODULE:
        module_name = CFG_TYPE_WRITER_MODULE[cfg_type]
        mod_spec = importlib.util.find_spec(module_name)
        if mod_spec:
            supported_write_cfg_types.append(cfg_type)
            modules_write[cfg_type] = module_name

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

        self.cfg_modules = {}

        self.options_dump = ConfigOptionsDump()
        self.options_hjson = ConfigOptionsHJson()
        self.options_inifile = ConfigOptionsInifile()
        self.options_json = ConfigOptionsJson()
        self.options_toml = ConfigOptionsToml()
        self.options_yaml = ConfigOptionsYaml()

        self.set_width_to_termsize()

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
        res["cfg_modules"] = self.cfg_modules
        res["encoding"] = self.encoding
        res["modules_read"] = copy.copy(self.modules_read)
        res["modules_write"] = copy.copy(self.modules_write)
        res["raise_on_error"] = self.raise_on_error
        res["supported_read_cfg_types"] = self.supported_read_cfg_types
        res["supported_write_cfg_types"] = self.supported_write_cfg_types
        res["use_chardet"] = self.use_chardet

        return res

    # -------------------------------------------------------------------------
    def set_width_to_termsize(self):
        """Set the width of dump and yaml output to the width of the terminal."""
        term_size = shutil.get_terminal_size((DEFAULT_TERMINAL_WIDTH, DEFAULT_TERMINAL_HEIGHT))

        self.options_dump.width = term_size.columns
        self.options_yaml.width = term_size.columns

    # -------------------------------------------------------------------------
    def detect_file_encoding(self, cfg_file, force=False):
        """Try to detect the encoding of the given file."""
        if not force and not self.use_chardet:
            if self.verbose > 2:
                LOG.debug(
                    _(
                        "Character set detection by module {mod!r} for file {fn!r} should not be "
                        "used, using character set {enc!r}."
                    ).format(mod="chardet", fn=str(cfg_file), enc=self.encoding)
                )
            return self.encoding

        if self.verbose > 2:
            LOG.debug(
                _("Trying to detect character set of file {fn!r} ...").format(fn=str(cfg_file))
            )

        encoding = self.encoding
        confidence = 1
        try:
            rawdata = cfg_file.read_bytes()
            chardet_result = chardet.detect(rawdata)
            confidence = chardet_result["confidence"]
            if confidence < self.chardet_min_level_confidence:
                if chardet_result["encoding"] != self.encoding:
                    msg = _(
                        "The confidence of {con:0.1f}% is lower than the limit of {lim:0.1f}%, "
                        "using character set {cs_def!r} instead of {cs_found!r}."
                    ).format(
                        con=(chardet_result["confidence"] * 100),
                        lim=(self.chardet_min_level_confidence * 100),
                        cs_def=self.encoding,
                        cs_found=chardet_result["encoding"],
                    )
                    LOG.warn(msg)
                return self.encoding
            encoding = chardet_result["encoding"]
        except Exception as e:
            msg = _("Got {what} on detecting cheracter set of {fn!r}: {e}").format(
                what=e.__class__.__name__, fn=str(cfg_file), e=e
            )
            LOG.error(msg)

        if self.verbose > 1:
            msg = _(
                "Found character set {cs} for file {fn} with a confidence of {con:0.1f}%."
            ).format(
                cs=self.colored(encoding, "cyan"),
                fn=self.colored(str(cfg_file), "cyan"),
                con=(confidence * 100),
            )
            LOG.debug(msg)

        return encoding

    # -------------------------------------------------------------------------
    def load_file(self, file_name, config_type=None):
        """
        Try to read the given file and return the read content as a dict.

        If the config_type is not given, then it tries to detect the config type first
        by the file name, and if this was not successful, it tries to apply a
        configuration type after another, and if return the read configuration
        and configuration type on the first success.
        """
        if config_type is None or str(config_type) == "":
            config_type = None
        else:
            config_type = str(config_type)

        if file_name is None or str(file_name) in ("", "-"):
            content = sys.stdin.read()
            source = "-"
        else:
            cfg_file = Path(file_name)
            source = str(cfg_file)
            encoding = self.detect_file_encoding(cfg_file)
            try:
                content = self.read_file(cfg_file, encoding=encoding)
            except (ReadTimeoutError, IOError) as e:
                msg = _("Got a {c}: {e}.").format(c=e.__class__.__name__, e=e)
                raise ConfigError(msg)

        if self.verbose > 2:
            LOG.debug(_("Read configuration:") + "\n" + content)

        if config_type:
            config = self.load_config(content, config_type=config_type, source=source)
            return (config_type, config)

        if file_name is not None and str(file_name) not in ("", "-"):
            config_type = self.guess_config_type_by_name(file_name, raise_on_error=False)

        if config_type:
            if self.verbose > 1:
                LOG.info(
                    _("Detected configuration type {t} by file name {f}.").format(
                        t=self.colored(config_type, "cyan"), f=self.colored(str(file_name), "cyan")
                    )
                )
            config = self.load_config(content, config_type=config_type, source=source)
            return (config_type, config)

        config, cfg_type = self.try_load_config(content, source=source)
        msg = _("Detected configuration type {t} from file '{f}'.").format(
            t=self.colored(cfg_type, "cyan"), f=self.colored(str(file_name), "cyan")
        )
        LOG.info(msg)
        return (cfg_type, config)

    # -------------------------------------------------------------------------
    def try_load_config(self, content, raise_on_error=None, source="-"):
        """Try to apply one config loader after another to the content, until one works."""
        if raise_on_error is None:
            raise_on_error = self.raise_on_error
        else:
            raise_on_error = bool(raise_on_error)

        config = None
        count_types = len(self.type_order)
        i = 0

        for config_type in self.type_order:
            i += 1
            lmethod = getattr(self.__class__, self.loader_methods[config_type])
            if not lmethod:
                raise RuntimeError(
                    _("Loader method {m} not defined in class {c}.").format(
                        m=self.colored(self.loader_methods[config_type], "red"),
                        c=self.colored(self.__class__.__name__, "cyan"),
                    )
                )

            self.init_loader_module(config_type)

            try:
                config = lmethod(self, content, raise_on_error=True, source=source)
            except ConfigWrongTypeError as e:
                if self.verbose > 1:
                    msg = _("Unable to parse '{f}' as {t}: {e}").format(
                        f=self.colored(source, "cyan"), t=self.colored(config_type, "cyan"), e=e
                    )
                    LOG.debug(msg)
                if i >= count_types:
                    msg = _("Could not detect file type by file content from '{}'.").format(
                        self.colored(source, "red")
                    )
                    if raise_on_error:
                        raise ConfigDetectionError(msg)
                    else:
                        LOG.error(msg)
                        return (None, None)
            else:
                if self.verbose > 1:
                    msg = _("Loaded configuration of type {}:").format(
                        self.colored(config_type, "cyan")
                    )
                    msg += " " + pp(config)
                    LOG.debug(msg)
                break

        return (config, config_type)

    # -------------------------------------------------------------------------
    def load_config(self, content, config_type, raise_on_error=None, source="-"):
        """Try to load the given file content as a configuration of a given type."""
        if raise_on_error is None:
            raise_on_error = self.raise_on_error
        else:
            raise_on_error = bool(raise_on_error)

        if config_type not in self.loader_methods:
            msg = _("Invalid configuration type '{}' given on calling load_config().").format(
                self.colored(config_type, "red")
            )
            raise ValueError(msg)
        lmethod = getattr(self.__class__, self.loader_methods[config_type])
        if not lmethod:
            raise RuntimeError(
                _("Loader method {m} not defined in class {c}.").format(
                    m=self.colored(self.loader_methods[config_type], "red"),
                    c=self.colored(self.__class__.__name__, "cyan"),
                )
            )

        self.init_loader_module(config_type)
        config = lmethod(self, content, raise_on_error=raise_on_error, source=source)

        if self.verbose > 2:
            LOG.debug(_("Loaded configuration:") + " " + pp(config))

        return config

    # -------------------------------------------------------------------------
    def load_inifile(self, content, raise_on_error=None, source="-"):
        """Load configuration in Windows inifile format."""
        if raise_on_error is None:
            raise_on_error = self.raise_on_error
        else:
            raise_on_error = bool(raise_on_error)

        kargs = self.options_inifile.property_dict()
        ext_interpolation = kargs["extended_interpolation"]
        del kargs["extended_interpolation"]
        if ext_interpolation:
            kargs["interpolation"] = ExtendedInterpolation

        if self.verbose > 1:
            LOG.debug("Loaded modules: " + pp(self.cfg_modules))

        module_name = self.modules_read["ini"]
        module = self.cfg_modules[module_name]

        if self.verbose > 2:
            LOG.debug(_("Arguments on initializing {}:").format("ConfigParser") + "\n" + pp(kargs))

        if self.verbose > 3:
            LOG.debug("Evaluating inifile content:\n" + content)

        cfg = {}
        parser = module.ConfigParser(**kargs)
        try:
            parser.read_string(content, source)
        except module.Error as e:
            msg = _("{what} on parsing: {e}").format(
                what=self.colored(e.__class__.__name__, "red"), e=e
            )
            if raise_on_error:
                raise ConfigWrongTypeError(msg)
            else:
                LOG.error(msg)
                return None

        for section in parser.sections():
            if section not in cfg:
                cfg[section] = {}
            for key, value in parser.items(section):
                k = key.lower()
                cfg[section][k] = value

        return cfg

    # -------------------------------------------------------------------------
    def load_json(self, content, raise_on_error=None, source="-"):
        """Load configuration in JSON format."""
        if raise_on_error is None:
            raise_on_error = self.raise_on_error
        else:
            raise_on_error = bool(raise_on_error)

        module_name = self.modules_read["json"]
        module = self.cfg_modules[module_name]

        cfg = {}

        try:
            cfg = module.loads(content)
        except module.JSONDecodeError as e:
            msg = _("{what} parse error in '{fn}', line {line}, column {col}: {msg}").format(
                what=e.__class__.__name__,
                fn=self.colored(e.doc, "red"),
                line=e.lineno,
                col=e.colno,
                msg=e.msg,
            )
            if raise_on_error:
                raise ConfigWrongTypeError(msg)
            else:
                LOG.error(msg)
                return None

        return cfg

    # -------------------------------------------------------------------------
    def load_hjson(self, content, raise_on_error=None, source="-"):
        """Load configuration in HJSON format."""
        if raise_on_error is None:
            raise_on_error = self.raise_on_error
        else:
            raise_on_error = bool(raise_on_error)

        module_name = self.modules_read["hjson"]
        module = self.cfg_modules[module_name]

        cfg = {}

        try:
            cfg = module.loads(content)
        except module.HjsonDecodeError as e:
            msg = _("{what} parse error in '{fn}', line {line}, column {col}: {msg}").format(
                what=e.__class__.__name__,
                fn=self.colored(e.doc, "red"),
                line=e.lineno,
                col=e.colno,
                msg=e.msg,
            )
            if raise_on_error:
                raise ConfigWrongTypeError(msg)
            else:
                LOG.error(msg)
                return None

        return cfg

    # -------------------------------------------------------------------------
    def load_toml(self, content, raise_on_error=None, source="-"):
        """Load configuration in TOML format."""
        if raise_on_error is None:
            raise_on_error = self.raise_on_error
        else:
            raise_on_error = bool(raise_on_error)

        module_name = self.modules_read["toml"]
        module = self.cfg_modules[module_name]

        cfg = {}

        try:
            cfg = module.loads(content)
        except module.TOMLDecodeError as e:
            msg = _("{what} parse error in '{fn}': {e}").format(
                what=e.__class__.__name__, fn=self.colored(source, "red"), e=e
            )
            if raise_on_error:
                raise ConfigWrongTypeError(msg)
            else:
                LOG.error(msg)
                return None

        return cfg

    # -------------------------------------------------------------------------
    def load_yaml(self, content, raise_on_error=None, source="-"):
        """Load configuration in YAML format."""
        LOG.debug(_("Loading content from {!r} format.").format("YAML"))
        if raise_on_error is None:
            raise_on_error = self.raise_on_error
        else:
            raise_on_error = bool(raise_on_error)

        module_name = self.modules_read["yaml"]
        module = self.cfg_modules[module_name]

        try:
            docs = []

            for doc in module.safe_load_all(content):
                docs.append(doc)
        except module.YAMLError as e:
            msg = _("{what} in '{fn}': {msg}").format(
                what=e.__class__.__name__, fn=self.colored(source, "red"), msg=str(e)
            )
            if raise_on_error:
                raise ConfigWrongTypeError(msg)
            else:
                LOG.error(msg)
                return None

        if not docs:
            return None

        if len(docs) == 1:
            return docs[0]
        return docs

    # -------------------------------------------------------------------------
    def dump_file(self, config, file_name, config_type=None):
        """
        Try to write the given config into the given file in the given config type.

        If the config_type is not given, then it tries to detect the config type
        by the file name. If this is not successful, then a ConfigDetectionError
        is raised.

        If an invalid config_type was given, a ValueError is raised.

        If the the config could not be written, then a IOError is raised.
        """
        if config_type is None or str(config_type) == "":
            config_type = None
        else:
            config_type = str(config_type)

        if config_type is None:
            if file_name is None or str(file_name) in ("", "-"):
                msg = _(
                    "Cannot use STDOUT to dump the configuration, if no configuration "
                    "type was given."
                )
                raise ConfigDetectionError(msg)

            config_type = self.guess_config_type_by_name(file_name, raise_on_error=True)

        if config_type not in self.modules_write:
            msg = _("Invalid configuration type {} for dumping given.").format(
                self.colored(repr(config_type), "red")
            )
            raise ConfigWrongTypeError(msg)

        LOG.debug(
            _("writing {file_name} as {config_type} ...").format(
                file_name=self.colored(str(file_name), "cyan"),
                config_type=self.colored(config_type, "green"),
            )
        )

        content = self.dump_config(config, config_type, raise_on_error=True, target=str(file_name))

        if file_name is None or str(file_name) in ("", "-"):
            print(content)
        else:
            fo = Path(file_name)
            if fo.exists():
                if self.force:
                    msg = _("File '{}' is already existing and will be overridden.").format(
                        self.colored(str(fo), "yellow")
                    )
                    LOG.warn(msg)
                else:
                    prompt = (
                        _(
                            "File '{fo}' is already existing. Do you want to override it "
                            "[{y}|{n}]"
                        ).format(
                            fo=self.colored(str(fo), "cyan"),
                            y=self.colored(_("yes"), "red"),
                            n=self.colored(_("No"), "green"),
                        )
                        + " "
                    )
                    answer = self.ask_for_yes_or_no(prompt, False)
                    if not answer:
                        msg = _("File '{}' will not be overridden.").format(
                            self.colored(str(fo), "cyan")
                        )
                        LOG.info(msg)
                        return (config_type, content)

            self.write_file(fo, content, must_exists=False)

        return (config_type, content)

    # -------------------------------------------------------------------------
    def dump_config(self, config, config_type, raise_on_error=None, target="-"):
        """Try to generate the content of a config file by the given config and config_type."""
        if raise_on_error is None:
            raise_on_error = self.raise_on_error
        else:
            raise_on_error = bool(raise_on_error)

        if config_type not in self.modules_write:
            msg = _("Invalid configuration type {} for dumping given.").format(
                self.colored(repr(config_type), "red")
            )
            raise ValueError(msg)

        dmethod = getattr(self.__class__, self.dumper_methods[config_type])

        if not dmethod:
            raise RuntimeError(
                _("Dumper method {m} not defined in class {c}.").format(
                    m=self.colored(self.dumper_methods[config_type], "red"),
                    c=self.colored(self.__class__.__name__, "cyan"),
                )
            )

        self.init_dumper_module(config_type)
        content = dmethod(self, config, raise_on_error=raise_on_error, target=target)

        if self.verbose > 2:
            LOG.debug(_("Dumped configuration:") + "\n" + content + "\n")

        return content

    # -------------------------------------------------------------------------
    def dump_pprint(self, config, raise_on_error, target):
        """Return a pretty print dump of the given configuration."""
        if raise_on_error is None:
            raise_on_error = self.raise_on_error
        else:
            raise_on_error = bool(raise_on_error)

        module_name = self.modules_write["dump"]
        module = self.cfg_modules[module_name]

        kwargs = {
            "indent": self.options_dump.indent,
            "width": self.options_dump.width,
            "depth": self.options_dump.depth,
            "compact": self.options_dump.compact,
        }

        if sys.version_info.major > 3 or (
            sys.version_info.major == 3 and sys.version_info.minor >= 8
        ):
            kwargs["sort_dicts"] = self.options_dump.sort_dicts

        if sys.version_info.major > 3 or (
            sys.version_info.major == 3 and sys.version_info.minor >= 10
        ):
            kwargs["underscore_numbers"] = self.options_dump.underscore_numbers

        if self.verbose > 1:
            ppr = f"{module_name}.PrettyPrinter"
            LOG.debug(f"Init arguments of {ppr}:\n" + pp(kwargs))

        pretty_printer = module.PrettyPrinter(**kwargs)
        return pretty_printer.pformat(config)

    # -------------------------------------------------------------------------
    def dump_json(self, config, raise_on_error, target):
        """Return a Json formatted dump of the given configuration."""
        if raise_on_error is None:
            raise_on_error = self.raise_on_error
        else:
            raise_on_error = bool(raise_on_error)

        module_name = self.modules_write["json"]
        module = self.cfg_modules[module_name]

        kwargs = {
            "ensure_ascii": self.options_json.ensure_ascii,
            "indent": self.options_json.indent,
            "sort_keys": self.options_json.sort_keys,
        }

        if self.verbose > 1:
            ppr = f"{module_name}.JSONEncoder"
            LOG.debug(f"Init arguments of {ppr}:\n" + pp(kwargs))

        json_encoder = module.JSONEncoder(**kwargs)
        return json_encoder.encode(config)

    # -------------------------------------------------------------------------
    def dump_hjson(self, config, raise_on_error, target):
        """Return a HJson formatted dump of the given configuration."""
        if raise_on_error is None:
            raise_on_error = self.raise_on_error
        else:
            raise_on_error = bool(raise_on_error)

        module_name = self.modules_write["hjson"]
        module = self.cfg_modules[module_name]

        kwargs = {
            "ensure_ascii": self.options_hjson.ensure_ascii,
            "indent": self.options_hjson.indent,
            "sort_keys": self.options_hjson.sort_keys,
        }

        if self.verbose > 1:
            ppr = f"{module_name}.HjsonEncoder"
            LOG.debug(f"Init arguments of {ppr}:\n" + pp(kwargs))

        hjson_encoder = module.HjsonEncoder(**kwargs)
        return hjson_encoder.encode(config)

    # -------------------------------------------------------------------------
    def dump_toml(self, config, raise_on_error, target):
        """Return a HJson formatted dump of the given configuration."""
        if raise_on_error is None:
            raise_on_error = self.raise_on_error
        else:
            raise_on_error = bool(raise_on_error)

        module_name = self.modules_write["toml"]
        module = self.cfg_modules[module_name]

        kwargs = {
            "indent": self.options_toml.indent,
        }

        if self.verbose > 1:
            ppr = f"{module_name}.dumps()"
            LOG.debug(f"Arguments of {ppr}:\n" + pp(kwargs))

        return module.dumps(config, **kwargs)

    # -------------------------------------------------------------------------
    def dump_yaml(self, config, raise_on_error, target):
        """Return a YAML formatted dump of the given configuration."""
        if raise_on_error is None:
            raise_on_error = self.raise_on_error
        else:
            raise_on_error = bool(raise_on_error)

        module_name = self.modules_write["yaml"]
        module = self.cfg_modules[module_name]

        kwargs = {
            "allow_unicode": self.options_yaml.allow_unicode,
            "canonical": self.options_yaml.canonical,
            "default_flow_style": self.options_yaml.flow_style,
            "default_style": self.options_yaml.style,
            "explicit_end": self.options_yaml.explicit_end,
            "explicit_start": self.options_yaml.explicit_start,
            "indent": self.options_yaml.indent,
            "line_break": self.options_yaml.line_break,
            "width": self.options_yaml.width,
        }

        if self.verbose > 1:
            ppr = f"{module_name}.safe_dump()"
            LOG.debug(f"Arguments of {ppr}:\n" + pp(kwargs))

        return module.safe_dump(config, **kwargs)

    # -------------------------------------------------------------------------
    def init_loader_module(self, config_type):
        """Import the necessary loader modules for this configuration type."""
        module_name = self.modules_read[config_type]
        if module_name in self.cfg_modules:
            return

        LOG.debug(_("Trying to load module {} ...").format(self.colored(module_name, "cyan")))
        module = importlib.__import__(module_name, globals(), locals(), [], 0)
        if module:
            self.cfg_modules[module_name] = module

    # -------------------------------------------------------------------------
    def init_dumper_module(self, config_type):
        """Import the necessary dumper modules for this configuration type."""
        module_name = self.modules_write[config_type]
        if module_name in self.cfg_modules:
            return

        LOG.debug(_("Trying to load module {} ...").format(self.colored(module_name, "cyan")))
        module = importlib.__import__(module_name, globals(), locals(), [], 0)
        if module:
            self.cfg_modules[module_name] = module

    # -------------------------------------------------------------------------
    def guess_config_type_by_name(self, file_name, raise_on_error=None):
        """Try to guess the configuration type by the name of the configuration file."""
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
