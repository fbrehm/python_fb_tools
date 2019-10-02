#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: Frank Brehm
@contact: frank.brehm@pixelpark.com
@copyright: © 2019 by Frank Brehm, Berlin
@summary: The module for the classes of the myip application.
"""
from __future__ import absolute_import, print_function

# Standard modules
import logging
import copy
import sys

# Own modules
from .. import __version__ as GLOBAL_VERSION

from ..xlate import XLATOR, format_list

from ..common import pp

from . import DdnsAppError, DdnsRequestError, BaseDdnsApplication

from .config import DdnsConfiguration

__version__ = '0.1.0'
LOG = logging.getLogger(__name__)

_ = XLATOR.gettext

# =============================================================================
class MyIpApplication(BaseDdnsApplication):
    """
    Class for the application objects.
    """

    # -------------------------------------------------------------------------
    def __init__(
        self, appname=None, verbose=0, version=GLOBAL_VERSION, base_dir=None,
            initialized=False, usage=None, description=None,
            argparse_epilog=None, argparse_prefix_chars='-', env_prefix=None):

        if description is None:
            description = _(
                "Tries to detect the public NAT IPv4 address and/or the automatic assigned "
                "IPv6 addess in a local network and print it out.")
        valid_proto_list = copy.copy(DdnsConfiguration.valid_protocols)

        self._ipv4_help = _("Use only {} to retreive the public IP address.").format('IPv4')
        self._ipv6_help = _("Use only {} to retreive the public IP address.").format('IPv6')
        self._proto_help = _(
            "The IP protocol, for which the public IP should be retrieved (one of {c}, default "
            "{d!r}).").format(c=format_list(valid_proto_list, do_repr=True, style='or'), d='any')

        super(MyIpApplication, self).__init__(
            appname=appname, verbose=verbose, version=version, base_dir=base_dir,
            description=description, initialized=False,
        )

        self.initialized = True

    # -------------------------------------------------------------------------
    def _run(self):

        LOG.debug(_("Starting {a!r}, version {v!r} ...").format(
            a=self.appname, v=self.version))

        if self.config.protocol in ('any', 'both', 'ipv4'):
            self.print_my_ipv(4)
        if self.config.protocol in ('any', 'both', 'ipv6'):
            self.print_my_ipv(6)

        self.exit(0)

    # -------------------------------------------------------------------------
    def print_my_ipv(self, protocol):

        my_ip = self.get_my_ipv(protocol)
        if my_ip:
            print('IPv{p}: {i}'.format(p=protocol, i=my_ip))


# =============================================================================
if __name__ == "__main__":

    pass

# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 list
