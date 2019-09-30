#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: Frank Brehm
@contact: frank.brehm@pixelpark.com
@copyright: © 2019 by Frank Brehm, Berlin
@summary: The module for the 'myip' application object.
"""
from __future__ import absolute_import, print_function

# Standard modules
import logging
import copy
import sys

# Third party modules
import requests

# Own modules
from . import __version__ as GLOBAL_VERSION
from . import DDNS_CFG_BASENAME

from .xlate import XLATOR, format_list

from .common import pp

from .app import BaseApplication

from .config import CfgFileOptionAction

from .errors import FbAppError

from .ddns_update_cfg import DdnsUpdateConfigError, DdnsUpdateConfiguration

__version__ = '0.2.1'
LOG = logging.getLogger(__name__)

_ = XLATOR.gettext


# =============================================================================
class MyIpAppError(FbAppError):
    """ Base exception class for all exceptions in this application."""
    pass

# =============================================================================
class MyIpApplication(BaseApplication):
    """
    Class for the application objects.
    """

    library_name = "ddns-client"
    loglevel_requests_set = False

    # -------------------------------------------------------------------------
    def __init__(
        self, appname=None, verbose=0, version=GLOBAL_VERSION, base_dir=None,
            initialized=False, usage=None, description=None,
            argparse_epilog=None, argparse_prefix_chars='-', env_prefix=None):

        desc = _(
            "Tries to detect the public NAT IPv4 address and/or the automatic assigned "
            "IPv6 addess in a local network and print it out.")

        self._cfg_dir = None
        self._cfg_file = None
        self.config = None
        self._user_agent = '{}/{}'.format(self.library_name, GLOBAL_VERSION)

        self.vms = []

        super(MyIpApplication, self).__init__(
            appname=appname, verbose=verbose, version=version, base_dir=base_dir,
            description=desc, initialized=False,
        )

        self.initialized = True

    # -------------------------------------------------------------------------
    @property
    def cfg_dir(self):
        """The directory containing the configuration file."""
        return self._cfg_dir

    # -------------------------------------------------------------------------
    @property
    def cfg_file(self):
        """Configuration file."""
        return self._cfg_file

    # -----------------------------------------------------------
    @property
    def user_agent(self):
        "The name of the user agent used in API calls."
        return self._user_agent

    @user_agent.setter
    def user_agent(self, value):
        if value is None or str(value).strip() == '':
            raise MyIpAppError(_("Invalid user agent {!r} given.").format(value))
        self._user_agent = str(value).strip()

    # -------------------------------------------------------------------------
    def as_dict(self, short=True):
        """
        Transforms the elements of the object into a dict

        @param short: don't include local properties in resulting dict.
        @type short: bool

        @return: structure as dict
        @rtype:  dict
        """

        res = super(MyIpApplication, self).as_dict(short=short)
        res['cfg_dir'] = self.cfg_dir
        res['cfg_file'] = self.cfg_file
        res['user_agent'] = self.user_agent

        return res

    # -------------------------------------------------------------------------
    def init_arg_parser(self):
        """
        Public available method to initiate the argument parser.
        """

        super(MyIpApplication, self).init_arg_parser()

        self._cfg_dir = self.base_dir.joinpath('etc')
        self._cfg_file = self.cfg_dir.joinpath(DDNS_CFG_BASENAME)
        default_cfg_file = copy.copy(self.cfg_file)
        valid_list = copy.copy(DdnsUpdateConfiguration.valid_protocols)

        protocol_group = self.arg_parser.add_mutually_exclusive_group()

        protocol_group.add_argument(
            '-4', '--ipv4', dest='ipv4', action="store_true",
            help=_("Use only {} to retreive the public IP address.").format('IPv4'),
        )

        protocol_group.add_argument(
            '-6', '--ipv6', dest='ipv6', action="store_true",
            help=_("Use only {} to retreive the public IP address.").format('IPv6'),
        )

        protocol_group.add_argument(
            '-p', '--protocol', dest='protocol', metavar=_('PROTOCOL'),
            choices=valid_list, help=_(
                "The IP protocol, for which the public IP should be retrieved "
                "(one of {c}, default {d!r}).").format(
                c=format_list(valid_list, do_repr=True, style='or'), d='any')
        )

        self.arg_parser.add_argument(
            '-T', '--timeout', dest='timeout', type=int, metavar=_('SECONDS'),
            help=_("The timeout in seconds for Web requests (default: {}).").format(
                DdnsUpdateConfiguration.default_timeout),
        )

        self.arg_parser.add_argument(
            '-c', '--config', '--config-file', dest='cfg_file', metavar=_('FILE'),
            action=CfgFileOptionAction,
            help=_("Configuration file (default: {!r})").format(str(default_cfg_file))
        )

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

        if self.args.cfg_file:
            self._cfg_file = self.args.cfg_file
            self._cfg_dir = self.cfg_file.parent

        self.config = DdnsUpdateConfiguration(
            appname=self.appname, verbose=self.verbose, base_dir=self.base_dir,
            config_file=self.cfg_file)

        self.config.read()
        if self.config.verbose > self.verbose:
            self.verbose = self.config.verbose
        self.config.initialized = True

        if self.verbose > 3:
            LOG.debug("Read configuration:\n{}".format(pp(self.config.as_dict())))

        if self.args.ipv4:
            self.config.protocol = 'ipv4'
        elif self.args.ipv6:
            self.config.protocol = 'ipv6'
        elif self.args.protocol:
            if self.args.protocol == 'both':
                self.config.protocol = 'any'
            else:
                self.config.protocol = self.args.protocol

        if self.args.timeout:
            try:
                self.config.timeout = self.args.timeout
            except (ValueError, KeyError) as e:
                msg = _("Invalid value {!r} as timeout:").format(self.args.timeout) + ' ' + str(e)
                LOG.error(msg)
                print()
                self.arg_parser.print_usage(sys.stdout)
                self.exit(1)

        if not self.loglevel_requests_set:
            msg = _("Setting Loglevel of the {m} module to {ll}.").format(
                m='requests', ll='WARNING')
            LOG.debug(msg)
            logging.getLogger("requests").setLevel(logging.WARNING)
            self.loglevel_requests_set = True

        self.initialized = True

    # -------------------------------------------------------------------------
    def _run(self):

        LOG.debug(_("Starting {a!r}, version {v!r} ...").format(
            a=self.appname, v=self.version))

        self.exit(0)


# =============================================================================
if __name__ == "__main__":

    pass

# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 list
