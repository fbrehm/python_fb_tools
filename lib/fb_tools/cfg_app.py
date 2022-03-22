#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: Frank Brehm
@contact: frank.brehm@pixelpark.com
@copyright: © 2022 by Frank Brehm, Berlin
@summary: The module for the application object with support
          for configuration files.
"""
from __future__ import absolute_import

# Standard modules
import os

# Third party modules
import six

# Own modules

from . import __version__ as __pkg_version__

from .app import BaseApplication

from .error import FbCfgAppError

from .common import pp, to_bool

from .config import CfgFileOptionAction

from .multi_config import UTF8_ENCODING, DEFAULT_ENCODING
from .multi_config import MultiConfigError, BaseMultiConfig

from .xlate import XLATOR

__version__ = '0.1.0'
LOG = logging.getLogger(__name__)


_ = XLATOR.gettext


# =============================================================================
class FbConfigApplication(BaseApplication):
    """
    Class for configured application objects.
    """

    # -------------------------------------------------------------------------
    def __init__(
        self, appname=None, verbose=0, version=__pkg_version__, base_dir=None,
            initialized=None, usage=None, description=None, cfg_class=BaseMultiConfig,
            argparse_epilog=None, argparse_prefix_chars='-', env_prefix=None,
            append_appname_to_stems=True, config_dir=None, additional_stems=None,
            additional_cfgdirs=None, cfg_encoding=DEFAULT_ENCODING,
            use_chardet=True, initialized=False):

        if not issubclass(cfg_class, BaseMultiConfig):
            msg = _("Parameter {cls!r} must be a subclass of {clinfo!r}.").format(
                cls='cfg_class', clinfo='BaseMultiConfig')
            raise TypeError(msg)

        self.cfg = None
        self._use_chardet = True
        self.use_chardet = use_chardet
        self._additional_cfg_file = None

        super(FbConfigApplication, self).__init__(
            appname=appname, verbose=verbose, version=version, base_dir=base_dir,
            initialized=False, usage=usage, description=description,
            argparse_epilog=argparse_epilog, argparse_prefix_chars=argparse_prefix_chars,
            env_prefix=env_prefix,
        )

        self.cfg = cfg_class(
            appname=self.appname, verbose=self.verbose, base_dir=self.base_dir,
            append_appname_to_stems=append_appname_to_stems, config_dir=config_dir,
            additional_stems=additional_stems, additional_cfgdirs=additional_cfgdirs,
            encoding=cfg_encoding, use_chardet=self.use_chardet, initialized=initialized)

    # -------------------------------------------------------------------------
    @property
    def use_chardet(self):
        """Flag, whether to use the chardet module to detect the
           character set of files."""
        return self._use_chardet

    @use_chardet.setter
    def use_chardet(self, value):
        self._use_chardet = to_bool(value)

    # -------------------------------------------------------------------------
    @property
    def additional_cfg_file(self):
        """Configuration file."""
        return self._additional_cfg_file

    # -------------------------------------------------------------------------
    def as_dict(self, short=True):
        """
        Transforms the elements of the object into a dict

        @param short: don't include local properties in resulting dict.
        @type short: bool

        @return: structure as dict
        @rtype:  dict
        """

        res = super(FbConfigApplication, self).as_dict(short=short)

        res['additional_cfg_file'] = self.additional_cfg_file
        res['use_chardet'] = self.use_chardet

        return res

    # -------------------------------------------------------------------------
    def init_arg_parser(self):
        """
        Method to initiate the argument parser.

        This method should be explicitely called by all init_arg_parser()
        methods in descendant classes.
        """

        self.arg_parser.add_argument(
            "-C", "--cfgfile", "--cfg-file", "--config",
            metavar=_("FILE"), nargs='+', dest="cfg_file",
            action=CfgFileOptionAction,
            help=_("Configuration files to use additional to the standard configuration files."),
        )

    # -------------------------------------------------------------------------
    def perform_arg_parser(self):

        if self.verbose > 2:
            LOG.debug(_("Got command line arguments:") + '\n' + pp(self.args))

        if self.args.cfg_file:
            self._additional_cfg_file = self.args.cfg_file
            if self.cfg:
                self.cfg.additional_cfg_file = self.args.cfg_file

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

        if not self.cfg:
            msg = _("The configuration should be existing at this point.")
            raise RuntimeError(msg)

        self.cfg.read()
        self.cfg.eval()
        if self.cfg.verbose > self.verbose:
            self.verbose = self.cfg.verbose


# =============================================================================

if __name__ == "__main__":

    pass

# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 list
