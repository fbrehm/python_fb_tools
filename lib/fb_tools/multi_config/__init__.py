#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@summary: A module for providing a configuration based on multiple configuration files.

@author: Frank Brehm
@contact: frank.brehm@pixelpark.com
@copyright: © 2023 by Frank Brehm, Berlin
"""
from __future__ import absolute_import

# Standard module
import codecs
import copy
import json
import logging
import os
import pathlib
import re
import sys
# from configparser import Error as ConfigParseError
from configparser import ExtendedInterpolation
from pathlib import Path

# Third party modules
import chardet

from six import StringIO
from six.moves import configparser

HAS_YAML = False
try:
    import yaml
    HAS_YAML = True
except ImportError:
    pass

HAS_HJSON = False
try:
    import hjson
    HAS_HJSON = True
except ImportError:
    pass

HAS_TOML = False
try:
    import toml
    from toml import TomlDecodeError
    HAS_TOML = True
except ImportError:
    pass


# Own modules
from .files import MultiCfgFilesMixin
from .inits import MultiCfgInitMixin
from ..common import is_sequence, pp, to_bool
from ..errors import MultiCfgLoaderNotFoundError, MultiCfgParseError, MultiConfigError
from ..handling_obj import HandlingObject
from ..merge import merge_structure
from ..obj import FbBaseObject
from ..xlate import XLATOR

__version__ = '2.1.3'

LOG = logging.getLogger(__name__)
UTF8_ENCODING = 'utf-8'
DEFAULT_ENCODING = UTF8_ENCODING

_ = XLATOR.gettext


# =============================================================================
class BaseMultiConfig(FbBaseObject, MultiCfgInitMixin, MultiCfgFilesMixin):
    """
    A base class for providing a configuration based in different config files.

    It provides methods to read it from configuration files.
    """

    default_encoding = DEFAULT_ENCODING

    default_stems = []
    default_config_dir = 'fb-tools'

    default_loader_methods = {
        'yaml': 'load_yaml',
        'ini': 'load_ini',
        'json': 'load_json',
        'hjson': 'load_hjson',
    }
    default_type_extension_patterns = {
        'yaml': [r'ya?ml'],
        'ini': [r'ini', r'conf(?:ig)?', r'cfg'],
        'json': [r'js(?:on)?'],
        'hjson': [r'hjs(?:on)?'],
    }

    available_cfg_types = ['ini', 'json']
    default_ini_style_types = ['ini']

    if HAS_HJSON:
        available_cfg_types.append('hjson')

    if HAS_YAML:
        available_cfg_types.append('yaml')

    if HAS_TOML:
        default_loader_methods['toml'] = 'load_toml'
        default_type_extension_patterns['toml'] = [r'to?ml']
        available_cfg_types.append('toml')

    re_invalid_stem = re.compile(re.escape(os.sep))

    re_common_prompt_timeout_key = re.compile(
        r'^\s*(?:prompt|console)[_-]*timeout\s*$', re.IGNORECASE)

    default_ini_default_section = '/'

    chardet_min_level_confidence = 1.0 / 3

    has_hjson = HAS_HJSON
    has_toml = HAS_TOML
    has_yaml = HAS_YAML

    # -------------------------------------------------------------------------
    def __init__(
        self, appname=None, verbose=0, version=__version__, base_dir=None,
            append_appname_to_stems=True, config_dir=None, additional_stems=None,
            additional_cfgdirs=None, encoding=DEFAULT_ENCODING, additional_config_file=None,
            use_chardet=True, raise_on_error=True, ensure_privacy=False, initialized=False):
        """Initialise a BaseMultiConfig object."""
        self._encoding = None
        self._config_dir = None
        self._additional_config_file = None
        self._cfgfiles_collected = False
        self._ini_allow_no_value = False
        self._ini_delimiters = None
        self._ini_comment_prefixes = None
        self._ini_inline_comment_prefixes = None
        self._ini_extended_interpolation = False
        self._ini_strict = True
        self._ini_empty_lines_in_values = True
        self._use_chardet = to_bool(use_chardet)
        self._raise_on_error = to_bool(raise_on_error)
        self._was_read = False
        self._ensure_privacy = to_bool(ensure_privacy)
        self._logfile = None
        self._prompt_timeout = None

        self.cfg = {}
        self.ext_loader = {}
        self.ext_re = {}
        self.configs = {}
        self.configs_raw = {}
        self.config_dirs = []
        self.config_files = []
        self.config_file_methods = {}
        self.stems = copy.copy(self.default_stems)
        self.ini_style_types = []
        self.ext_patterns = {}

        super(BaseMultiConfig, self).__init__(
            appname=appname, verbose=verbose, version=version,
            base_dir=base_dir, initialized=False,
        )

        if self.verbose > 1:
            if not HAS_YAML:
                LOG.debug(_('{} configuration is not supported.').format('Yaml'))
            if not HAS_HJSON:
                LOG.debug(_('{} configuration is not supported.').format('HJson'))
            if not HAS_TOML:
                LOG.debug(_('{} configuration is not supported.').format('Toml'))

        if encoding:
            self.encoding = encoding
        else:
            self.encoding = self.default_encoding

        if config_dir:
            self.config_dir = config_dir
        else:
            self.config_dir = self.default_config_dir

        self._init_config_dirs(additional_cfgdirs)
        self._init_stems(append_appname_to_stems, additional_stems)
        self._init_types()

        self.additional_config_file = additional_config_file

        if initialized:
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
                'Encoding {v!r} must be a {s!r} object, '
                'but is a {c!r} object instead.').format(
                v=value, s='str', c=value.__class__.__name__)
            raise TypeError(msg)

        encoder = codecs.lookup(value)
        self._encoding = encoder.name

    # -------------------------------------------------------------------------
    @property
    def additional_config_file(self):
        """Return an additional configuration file."""
        return self._additional_config_file

    @additional_config_file.setter
    def additional_config_file(self, value):
        if value is None:
            self._additional_config_file = None
            return

        cfg_file = Path(value)
        if not cfg_file.exists():
            msg = _('Additional config file {!r} does not exists.')
            if self.raise_on_error:
                raise MultiConfigError(msg.format(str(cfg_file)))
            LOG.error(msg.format(str(cfg_file)))
            return

        if not cfg_file.is_file():
            msg = _('Configuration file {!r} exists, but is not a regular file.')
            if self.raise_on_error:
                raise MultiConfigError(msg.format(str(cfg_file)))
            LOG.error(msg.format(str(cfg_file)))
            return

        if not os.access(cfg_file, os.R_OK):
            msg = _('Configuration file {!r} is not readable.')
            if self.raise_on_error:
                raise MultiConfigError(msg.format(str(cfg_file)))
            LOG.error(msg.format(str(cfg_file)))
            return

        cfg_file = cfg_file.resolve()
        self._additional_config_file = cfg_file

    # -------------------------------------------------------------------------
    @property
    def config_dir(self):
        """Return the config directory.

        This directory contains the configuration relative to different paths.
        """
        return self._config_dir

    @config_dir.setter
    def config_dir(self, value):
        if value is None:
            raise TypeError(_('A configuration directory may not be None.'))
        cdir = pathlib.Path(value)
        if cdir.is_absolute():
            msg = _('Configuration directory {!r} may not be absolute.').format(str(cdir))
            raise MultiConfigError(msg)
        self._config_dir = cdir

    # -------------------------------------------------------------------------
    @property
    def logfile(self):
        """Return a possible log file.

        This file can be used as a FileAppender target in logging.
        """
        return self._logfile

    @logfile.setter
    def logfile(self, value):
        if value is None:
            self._logfile = None
            return
        self._logfile = Path(value)

    # -------------------------------------------------------------------------
    @property
    def prompt_timeout(self):
        """Return the timeout in seconds for waiting for an answer on a prompt."""
        return getattr(self, '_prompt_timeout', None)

    # -------------------------------------------------------------------------
    @property
    def use_chardet(self):
        """Return whether the chardet module should be used.

        Use the chardet module to detect the character set of a config file.
        """
        return self._use_chardet

    # -------------------------------------------------------------------------
    @property
    def cfgfiles_collected(self):
        """Flag, whether the configuration files were collected."""
        return self._cfgfiles_collected

    # -------------------------------------------------------------------------
    @property
    def was_read(self):
        """Flag, whether the configuration files were read."""
        return self._was_read

    # -------------------------------------------------------------------------
    @property
    def ini_allow_no_value(self):
        """Return whether keys without values in ini-files are accepted."""
        return self._ini_allow_no_value

    @ini_allow_no_value.setter
    def ini_allow_no_value(self, value):
        self._ini_allow_no_value = to_bool(value)

    # -------------------------------------------------------------------------
    @property
    def ini_delimiters(self):
        """Reurn delimiters of ini-files.

        Delimiters are substrings that delimit keys from values within a section
        in ini-files.
        """
        return self._ini_delimiters

    @ini_delimiters.setter
    def ini_delimiters(self, value):
        if not value:
            self._ini_delimiters = None
            return
        if isinstance(value, str):
            self._ini_delimiters = []
            for character in value:
                self._ini_delimiters.append(character)
            return
        if is_sequence(value):
            self._ini_delimiters = copy.copy(value)
            return
        msg = _('Cannot use {!r} as delimiters for ini-files.').format(value)
        raise TypeError(msg)

    # -------------------------------------------------------------------------
    @property
    def ini_comment_prefixes(self):
        """Return prefixes for comment lines in ini-files."""
        return self._ini_comment_prefixes

    @ini_comment_prefixes.setter
    def ini_comment_prefixes(self, value):
        if not value:
            self._ini_comment_prefixes = None
            return
        if isinstance(value, str):
            self._ini_comment_prefixes = []
            for character in value:
                self._ini_comment_prefixes.append(character)
            return
        if is_sequence(value):
            self._ini_comment_prefixes = copy.copy(value)
            return
        msg = _('Cannot use {!r} as comment prefixes for ini-files.').format(value)
        raise TypeError(msg)

    # -------------------------------------------------------------------------
    @property
    def ini_inline_comment_prefixes(self):
        """Return inline prefixes for comment lines in ini-files."""
        return self._ini_inline_comment_prefixes

    @ini_inline_comment_prefixes.setter
    def ini_inline_comment_prefixes(self, value):
        if not value:
            self._ini_inline_comment_prefixes = None
            return
        if isinstance(value, str):
            self._ini_inline_comment_prefixes = []
            for character in value:
                self._ini_inline_comment_prefixes.append(character)
            return
        if is_sequence(value):
            self._ini_inline_comment_prefixes = copy.copy(value)
            return
        msg = _('Cannot use {!r} as inline comment prefixes for ini-files.').format(value)
        raise TypeError(msg)

    # -------------------------------------------------------------------------
    @property
    def ini_extended_interpolation(self):
        """Use ExtendedInterpolation for interpolation of ini-files.

        Use it instead of BasicInterpolation.
        """
        return self._ini_extended_interpolation

    @ini_extended_interpolation.setter
    def ini_extended_interpolation(self, value):
        self._ini_extended_interpolation = to_bool(value)

    # -------------------------------------------------------------------------
    @property
    def ini_strict(self):
        """Return the strictness of ini-files.

        The ini-parser will not allow for any section or option duplicates while
        reading from a single source.
        """
        return self._ini_strict

    @ini_strict.setter
    def ini_strict(self, value):
        self._ini_strict = to_bool(value)

    # -------------------------------------------------------------------------
    @property
    def ini_empty_lines_in_values(self):
        """Return the possibility of multi-line values in ini-files.

        May values can span multiple lines as long as they are indented more thans
        the key that holds them in ini-files.
        """
        return self._ini_empty_lines_in_values

    @ini_empty_lines_in_values.setter
    def ini_empty_lines_in_values(self, value):
        self._ini_empty_lines_in_values = to_bool(value)

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
    def ensure_privacy(self):
        """Return the need for privacy of the config files.

        If True, then all found config files, which are not located below /etc,
        must not readable for others or the group (mode 0400 or 0600).
        """
        return self._ensure_privacy

    @ensure_privacy.setter
    def ensure_privacy(self, value):
        self._ensure_privacy = to_bool(value)

    # -------------------------------------------------------------------------
    def as_dict(self, short=True):
        """
        Transform the elements of the object into a dict.

        @param short: don't include local properties in resulting dict.
        @type short: bool

        @return: structure as dict
        @rtype:  dict
        """
        res = super(BaseMultiConfig, self).as_dict(short=short)
        res['default_encoding'] = self.default_encoding
        res['default_stems'] = self.default_stems
        res['default_config_dir'] = self.default_config_dir
        res['default_loader_methods'] = self.default_loader_methods
        res['default_type_extension_patterns'] = self.default_type_extension_patterns
        res['default_ini_style_types'] = self.default_ini_style_types
        res['chardet_min_level_confidence'] = self.chardet_min_level_confidence
        res['available_cfg_types'] = self.available_cfg_types
        res['encoding'] = self.encoding
        res['config_dir'] = self.config_dir
        res['additional_config_file'] = self.additional_config_file
        res['cfgfiles_collected'] = self.cfgfiles_collected
        res['was_read'] = self.was_read
        res['ini_allow_no_value'] = self.ini_allow_no_value
        res['ini_delimiters'] = self.ini_delimiters
        res['ini_comment_prefixes'] = self.ini_comment_prefixes
        res['ini_inline_comment_prefixes'] = self.ini_inline_comment_prefixes
        res['ini_extended_interpolation'] = self.ini_extended_interpolation
        res['ini_strict'] = self.ini_strict
        res['raise_on_error'] = self.raise_on_error
        res['has_hjson'] = self.has_hjson
        res['has_toml'] = self.has_toml
        res['has_yaml'] = self.has_yaml
        res['use_chardet'] = self.use_chardet
        res['ensure_privacy'] = self.ensure_privacy
        res['logfile'] = self.logfile
        res['prompt_timeout'] = self.prompt_timeout

        return res

    # -------------------------------------------------------------------------
    @classmethod
    def is_venv(cls):
        """Return whther application is running inside a virtual environment."""
        if hasattr(sys, 'real_prefix'):
            return True
        return (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)

    # -------------------------------------------------------------------------
    @classmethod
    def valid_stem(cls, stem):
        """Check whether the given stem is a valid file name stem (whithout a path separator)."""
        if cls.re_invalid_stem.search(stem):
            return False
        return True

    # -------------------------------------------------------------------------
    def read(self):
        """Read all collected config files and save their configuration."""
        if not self.cfgfiles_collected:
            self.collect_config_files()

        self.cfg = {}
        for cfg_file in self.config_files:

            if self.verbose:
                LOG.info(_('Reading configuration file {!r} ...').format(str(cfg_file)))

            method = self.config_file_methods[cfg_file]
            if self.verbose > 1:
                LOG.debug(_('Using loading method {!r}.').format(method))

            meth = getattr(self, method, None)
            if not meth:
                raise MultiCfgLoaderNotFoundError(method)

            cfg = meth(cfg_file)
            if self.verbose > 3:
                msg = _('Read config from {fn!r}:').format(fn=str(cfg_file))
                msg += '\n' + pp(cfg)
                LOG.debug(msg)
            if cfg and cfg.keys():
                self.configs_raw[str(cfg_file)] = cfg
                self.cfg = merge_structure(self.cfg, cfg)
            else:
                self.configs_raw[str(cfg_file)] = None

        self._was_read = True
        if self.verbose > 2:
            LOG.debug(_('Read merged config:') + '\n' + pp(self.cfg))

    # -------------------------------------------------------------------------
    def detect_file_encoding(self, cfg_file, force=False):
        """Try to detect the encoding of the given file."""
        if not force and not self.use_chardet:
            if self.verbose > 2:
                LOG.debug(_(
                    'Character set detection by module {mod!r} for file {fn!r} should not be '
                    'used, using character set {enc!r}.').format(
                    mod='chardet', fn=str(cfg_file), enc=self.encoding))
            return self.encoding

        if self.verbose > 1:
            LOG.debug(_('Trying to detect character set of file {fn!r} ...').format(
                fn=str(cfg_file)))

        encoding = self.encoding
        confidence = 1
        try:
            rawdata = cfg_file.read_bytes()
            chardet_result = chardet.detect(rawdata)
            confidence = chardet_result['confidence']
            if confidence < self.chardet_min_level_confidence:
                if chardet_result['encoding'] != self.encoding:
                    msg = _(
                        'The confidence of {con:0.1f}% is lower than the limit of {lim:0.1f}%, '
                        'using character set {cs_def!r} instead of {cs_found!r}.').format(
                        con=(chardet_result['confidence'] * 100),
                        lim=(self.chardet_min_level_confidence * 100),
                        cs_def=self.encoding, cs_found=chardet_result['encoding'])
                    LOG.warn(msg)
                return self.encoding
            encoding = chardet_result['encoding']
        except Exception as e:
            msg = _('Got {what} on detecting cheracter set of {fn!r}: {e}').format(
                what=e.__class__.__name__, fn=str(cfg_file), e=e)
            LOG.error(msg)

        if self.verbose > 2:
            msg = _(
                'Found character set {cs!r} for file {fn!r} with a confidence of '
                '{con:0.1f}%.').format(cs=encoding, fn=str(cfg_file), con=(confidence * 100))
            LOG.debug(msg)

        return encoding

    # -------------------------------------------------------------------------
    def load_json(self, cfg_file):
        """Read and load the given file as a JSON file."""
        LOG.debug(_('Reading {tp} file {fn!r} ...').format(tp='JSON', fn=str(cfg_file)))

        open_opts = {
            'encoding': UTF8_ENCODING,
            'errors': 'surrogateescape',
        }

        try:
            with cfg_file.open('r', **open_opts) as fh:
                js = json.load(fh)
        except json.JSONDecodeError as e:
            msg = _('{what} parse error in {fn!r}, line {line}, column {col}: {msg}').format(
                what='JSON', fn=str(cfg_file), line=e.lineno, col=e.colno, msg=e.msg)
            if self.raise_on_error:
                raise MultiCfgParseError(msg)
            LOG.error(msg)
            return None
        except Exception as e:
            msg = _('Got {what} on reading and parsing {fn!r}: {e}').format(
                what=e.__class__.__name__, fn=str(cfg_file), e=e)
            if self.raise_on_error:
                raise MultiCfgParseError(msg)
            LOG.error(msg)
            return None

        return js

    # -------------------------------------------------------------------------
    def load_hjson(self, cfg_file):
        """Read and load the given file as an human readable JSON file."""
        LOG.debug(_('Reading {tp} file {fn!r} ...').format(
            tp='human readable JSON', fn=str(cfg_file)))

        encoding = self.detect_file_encoding(cfg_file)

        open_opts = {
            'encoding': encoding,
            'errors': 'surrogateescape',
        }

        js = {}
        try:
            with cfg_file.open('r', **open_opts) as fh:
                js = hjson.load(fh)
        except hjson.HjsonDecodeError as e:
            msg = _('{what} parse error in {fn!r}, line {line}, column {col}: {msg}').format(
                what='HJSON', fn=str(cfg_file), line=e.lineno, col=e.colno, msg=e.msg)
            if self.raise_on_error:
                raise MultiCfgParseError(msg)
            LOG.error(msg)
            return None
        except Exception as e:
            msg = _('Got {what} on reading and parsing {fn!r}: {e}').format(
                what=e.__class__.__name__, fn=str(cfg_file), e=e)
            if self.raise_on_error:
                raise MultiCfgParseError(msg)
            LOG.error(msg)
            return None

        return js

    # -------------------------------------------------------------------------
    def load_ini(self, cfg_file):
        """Read and load the given file as an INI file."""
        LOG.debug(_('Reading {tp} file {fn!r} ...').format(tp='INI', fn=str(cfg_file)))

        kargs = {
            'allow_no_value': self.ini_allow_no_value,
            'strict': self.ini_strict,
            'empty_lines_in_values': self.ini_empty_lines_in_values,
        }
        if self.ini_delimiters:
            kargs['delimiters'] = self.ini_delimiters
        if self.ini_comment_prefixes:
            kargs['comment_prefixes'] = self.ini_comment_prefixes
        if self.ini_inline_comment_prefixes:
            kargs['cinline_omment_prefixes'] = self.ini_inline_comment_prefixes
        if self.ini_extended_interpolation:
            kargs['interpolation'] = ExtendedInterpolation

        if self.verbose > 1:
            LOG.debug(_('Arguments on initializing {}:').format('ConfigParser') + '\n' + pp(kargs))

        parser = configparser.ConfigParser(**kargs)

        encoding = self.detect_file_encoding(cfg_file)

        open_opts = {
            'encoding': encoding,
            'errors': 'surrogateescape',
        }

        cfg = {}

        try:
            with cfg_file.open('r', **open_opts) as fh:
                stream = StringIO('[/]\n' + fh.read())
                parser.read_file(stream)
        except Exception as e:
            msg = _('Got {what} on reading and parsing {fn!r}: {e}').format(
                what=e.__class__.__name__, fn=str(cfg_file), e=e)
            if self.raise_on_error:
                raise MultiCfgParseError(msg)
            LOG.error(msg)
            return None

        for section in parser.sections():
            if section not in cfg:
                cfg[section] = {}
            for (key, value) in parser.items(section):
                k = key.lower()
                cfg[section][k] = value

        if not cfg['/'].keys():
            del cfg['/']

        return cfg

    # -------------------------------------------------------------------------
    def load_toml(self, cfg_file):
        """Read and load the given file as a TOML file."""
        LOG.debug(_('Reading {tp} file {fn!r} ...').format(tp='TOML', fn=str(cfg_file)))

        cfg = {}

        try:
            cfg = toml.load(cfg_file)
        except TomlDecodeError as e:
            msg = _('{what} parse error in {fn!r}, line {line}, column {col}: {msg}').format(
                what='TOML', fn=str(cfg_file), line=e.lineno, col=e.colno, msg=e.msg)
            if self.raise_on_error:
                raise MultiCfgParseError(msg)
            LOG.error(msg)
            return None
        except Exception as e:
            msg = _('Got {what} on reading and parsing {fn!r}: {e}').format(
                what=e.__class__.__name__, fn=str(cfg_file), e=e)
            if self.raise_on_error:
                raise MultiCfgParseError(msg)
            LOG.error(msg)
            return None

        return cfg

    # -------------------------------------------------------------------------
    def load_yaml(self, cfg_file):
        """Read and load the given file as a YAML file."""
        LOG.debug(_('Reading {tp} file {fn!r} ...').format(tp='YAML', fn=str(cfg_file)))

        open_opts = {
            'encoding': UTF8_ENCODING,
            'errors': 'surrogateescape',
        }

        cfg = {}
        try:
            with cfg_file.open('r', **open_opts) as fh:
                cfg = yaml.safe_load(fh)
        except yaml.YAMLError as e:
            if hasattr(e, 'problem_mark'):
                mark = e.problem_mark
                msg = _('{what} parse error in {fn!r}, line {line}, column {col}: {msg}').format(
                    what='YAML', fn=str(cfg_file),
                    line=(mark.line + 1), col=(mark.column + 1), msg=str(e))
            else:
                msg = _('Got {what} on reading and parsing {fn!r}: {e}').format(
                    what=e.__class__.__name__, fn=str(cfg_file), e=e)
            if self.raise_on_error:
                raise MultiCfgParseError(msg)
            LOG.error(msg)
            return None
        except Exception as e:
            msg = _('Got {what} on reading and parsing {fn!r}: {e}').format(
                what=e.__class__.__name__, fn=str(cfg_file), e=e)
            if self.raise_on_error:
                raise MultiCfgParseError(msg)
            LOG.error(msg)
            return None

        return cfg

    # -------------------------------------------------------------------------
    def eval(self):                                                         # noqa: A003
        """Evaluate configuration and store it in object properties."""
        if not self.was_read:
            msg = _('Evaluation of configuration could only be happen after reading it.')
            raise RuntimeError(msg)

        for section_name in self.cfg.keys():

            if section_name.lower() in ('default', 'global', 'common'):
                self.eval_global_section(section_name)
                continue
            self.eval_section(section_name)

    # -------------------------------------------------------------------------
    def eval_global_section(self, section_name):
        """Evaluate section [global] of configuration.

        May be overridden in descendant classes.
        """
        if self.verbose > 1:
            LOG.debug(_('Checking config section {!r} ...').format(section_name))

        max_timeout = HandlingObject.max_prompt_timeout
        invalid_msg = _('Invalid value {val!r} in section {sec!r} for console timeout.')

        config = self.cfg[section_name]
        for key in config.keys():
            value = config[key]
            if key.lower() == 'verbose':
                val = 0
                if value is None:
                    pass
                elif isinstance(value, bool):
                    if value:
                        val = 1
                else:
                    val = int(value)
                if val > self.verbose:
                    self.verbose = val
                continue

            if self.re_common_prompt_timeout_key.match(key):
                try:
                    timeout = int(value)
                except (ValueError, TypeError) as e:
                    msg = invalid_msg.format(val=value, sec=section_name)
                    msg += ' ' + str(e)
                    LOG.error(msg)
                    continue
                if timeout <= 0 or timeout > max_timeout:
                    msg = invalid_msg.format(val=value, sec=section_name)
                    msg += ' ' + _(
                        'A timeout must be greater than zero and less or equal to {}.').format(
                        max_timeout)
                    LOG.error(msg)
                    continue
                self._prompt_timeout = timeout
                continue

            if key.lower() in ('logfile', 'log-file', 'log'):
                self.logfile = value
                continue

    # -------------------------------------------------------------------------
    def eval_section(self, section_name):
        """Evaluate section with given name of configuration.

        Should be overridden in descendant classes.
        """
        pass


# =============================================================================

if __name__ == '__main__':

    pass

# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 list
