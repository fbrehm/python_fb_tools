#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@summary: A mixin module for the BaseMultiConfig class for methods reading config files.

@author: Frank Brehm
@contact: frank@brehm-online.com
@copyright: © 2025 by Frank Brehm, Berlin
"""
from __future__ import absolute_import

# Standard module
import json
import logging
# from configparser import Error as ConfigParseError
from configparser import ExtendedInterpolation

# Third party modules
import chardet

from six import StringIO
from six.moves import configparser

try:
    import yaml
except ImportError:
    pass

try:
    import hjson
except ImportError:
    pass

try:
    import toml
    from toml import TomlDecodeError
except ImportError:
    pass

# Own modules
from .. import UTF8_ENCODING
from ..common import pp
from ..errors import MultiCfgLoaderNotFoundError, MultiCfgParseError
from ..merge import merge_structure
from ..xlate import XLATOR

__version__ = '0.2.0'

LOG = logging.getLogger(__name__)

_ = XLATOR.gettext
ngettext = XLATOR.ngettext


# =============================================================================
class MultiCfgReadMixin():
    """
    A mixin class for extending the BaseMultiConfig class.

    It contains helper methods for methods regarding reading config files.
    """

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


# =============================================================================

if __name__ == '__main__':

    pass

# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 list
