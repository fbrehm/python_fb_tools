#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@summary: Prints the public NAT IPv4 address and/or the automatic assigned IPv6 address.

@author: Frank Brehm
@contact: frank@brehm-online.com
@copyright: © 2025 by Frank Brehm, Berlin
"""
from __future__ import absolute_import, print_function

# Standard modules
import copy
import locale
import logging
import sys

try:
    import pathlib
except ImportError:
    import pathlib2 as pathlib

# Own modules
from .. import __version__ as GLOBAL_VERSION
from ..common import to_bool
from ..ddns import BaseDdnsApplication
from ..ddns.config import DdnsConfiguration
from ..ddns.errors import WorkDirError
from ..xlate import XLATOR, format_list

__version__ = "2.1.0"
LOG = logging.getLogger(__name__)

_ = XLATOR.gettext


# =============================================================================
class MyIpApplication(BaseDdnsApplication):
    """Class for the application objects."""

    show_assume_options = False
    show_console_timeout_option = False
    show_force_option = False
    show_quiet_option = False
    show_simulate_option = False

    # -------------------------------------------------------------------------
    def __init__(
        self, version=GLOBAL_VERSION, initialized=None, description=None, *args, **kwargs
    ):
        """Initialise a MyIpApplication object."""
        self._write_ips = False

        if description is None:
            description = _(
                "Tries to detect the public NAT IPv4 address and/or the automatic assigned "
                "IPv6 address in a local network and print it out."
            )
        valid_proto_list = copy.copy(DdnsConfiguration.valid_protocols)

        self._ipv4_help = _("Use only {} to retreive the public IP address.").format("IPv4")
        self._ipv6_help = _("Use only {} to retreive the public IP address.").format("IPv6")
        self._proto_help = _(
            "The IP protocol, for which the public IP should be retrieved (one of {c}, default "
            "{d!r})."
        ).format(c=format_list(valid_proto_list, do_repr=True, style="or"), d="any")

        super(MyIpApplication, self).__init__(
            *args, version=version, description=description, initialized=False, **kwargs
        )

        if initialized is None:
            self.initialized = True
        else:
            if initialized:
                self.initialized = True

    # -------------------------------------------------------------------------
    @property
    def write_ips(self):
        """Return the Flag to write retreived IPs into the working directory."""
        return self._write_ips

    @write_ips.setter
    def write_ips(self, value):
        self._write_ips = to_bool(value)

    # -------------------------------------------------------------------------
    def as_dict(self, short=True):
        """
        Transform the elements of the object into a dict.

        @param short: don't include local properties in resulting dict.
        @type short: bool

        @return: structure as dict
        @rtype:  dict
        """
        res = super(MyIpApplication, self).as_dict(short=short)
        res["write_ips"] = self.write_ips

        return res

    # -------------------------------------------------------------------------
    def init_arg_parser(self):
        """Initiate th eargument parser."""
        myip_group = self.arg_parser.add_argument_group(_("myip options"))

        myip_group.add_argument(
            "-W",
            "--write",
            "--write-ips",
            action="store_true",
            dest="write_ips",
            help=_("Write found public IPs into a cache file in working directory."),
        )

        super(MyIpApplication, self).init_arg_parser()

    # -------------------------------------------------------------------------
    def post_init(self):
        """Execute some actions before calling run().

        Here could be done some finishing actions after reading in
        commandline parameters, configuration a.s.o.
        """
        super(MyIpApplication, self).post_init()
        self.initialized = False

        if self.write_ips:
            try:
                self.verify_working_dir()
            except WorkDirError as e:
                LOG.error(str(e))
                self.exit(3)

        self.initialized = True

    # -------------------------------------------------------------------------
    def perform_arg_parser(self):
        """Execute some actions after parsing the command line parameters."""
        if self.args.write_ips:
            self.write_ips = True

    # -------------------------------------------------------------------------
    def _run(self):

        LOG.debug(_("Starting {a!r}, version {v!r} ...").format(a=self.appname, v=self.version))

        if self.cfg.protocol in ("any", "both", "ipv4"):
            self.print_my_ipv(4)
        if self.cfg.protocol in ("any", "both", "ipv6"):
            self.print_my_ipv(6)

    # -------------------------------------------------------------------------
    def print_my_ipv(self, protocol):
        """Write back the current public IP to console."""
        my_ip = self.get_my_ipv(protocol)
        if my_ip:
            print("IPv{p}: {i}".format(p=protocol, i=my_ip))
            if self.write_ips:
                if protocol == 4:
                    self.write_ipv4_cache(my_ip)
                else:
                    self.write_ipv6_cache(my_ip)


# =============================================================================
def main():
    """Entrypoint for myip."""
    my_path = pathlib.Path(__file__)
    appname = my_path.name

    locale.setlocale(locale.LC_ALL, "")

    app = MyIpApplication(appname=appname)
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
