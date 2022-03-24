#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: Frank Brehm
@contact: frank@brehm-online.com
@copyright: © 2022 by Frank Brehm, Berlin
@summary: The module for the 'get-vmware-hosts' application object.
"""
from __future__ import absolute_import, print_function

# Standard modules
import logging

# Third party modules

# Own modules
from . import __version__ as GLOBAL_VERSION

from .xlate import XLATOR
# from .xlate import format_list

from .common import pp, to_bool

from .vmware_app import BaseVmwareApplication, VmwareAppError

# from .vsphere.vm import VsphereVm

__version__ = '0.2.1'
LOG = logging.getLogger(__name__)

_ = XLATOR.gettext
ngettext = XLATOR.ngettext


# =============================================================================
class GetVmHostsAppError(VmwareAppError):
    """ Base exception class for all exceptions in this application."""
    pass


# =============================================================================
class GetVmHostsApplication(BaseVmwareApplication):
    """Class for the application object."""

    # -------------------------------------------------------------------------
    def __init__(
        self, appname=None, verbose=0, version=GLOBAL_VERSION, base_dir=None,
            initialized=False, usage=None, description=None,
            argparse_epilog=None, argparse_prefix_chars='-', env_prefix=None):

        desc = _(
            "Tries to get a list of all physical hosts in "
            "VMWare VSphere and print it out.")

        self._details = False

        self.vms = []

        super(GetVmHostsApplication, self).__init__(
            appname=appname, verbose=verbose, version=version, base_dir=base_dir,
            description=desc, initialized=False,
        )

        self.initialized = True

    # -------------------------------------------------------------------------
    @property
    def details(self):
        """Should the list be diisplyed with all details."""
        return self._details

    @details.setter
    def details(self, value):
        self._details = to_bool(value)

    # -------------------------------------------------------------------------
    def as_dict(self, short=True):
        """
        Transforms the elements of the object into a dict

        @param short: don't include local properties in resulting dict.
        @type short: bool

        @return: structure as dict
        @rtype:  dict
        """

        res = super(GetVmHostsApplication, self).as_dict(short=short)
        res['details'] = self.details

        return res

    # -------------------------------------------------------------------------
    def init_arg_parser(self):
        """
        Public available method to initiate the argument parser.
        """

        super(GetVmHostsApplication, self).init_arg_parser()

        output_options = self.arg_parser.add_argument_group(_('Output options'))

        output_options.add_argument(
            '-D', '--details', dest='details', action="store_true",
            help=_("Detailed output list (quering data needs some time longer).")
        )

    # -------------------------------------------------------------------------
    def perform_arg_parser(self):

        super(GetVmHostsApplication, self).perform_arg_parser()

        if self.args.details:
            self.details = self.args.details

    # -------------------------------------------------------------------------
    def _run(self):

        LOG.debug(_("Starting {a!r}, version {v!r} ...").format(
            a=self.appname, v=self.version))

        ret = 0
        try:
            ret = self.get_all_vms()
        finally:
            self.cleaning_up()

        self.exit(ret)

    # -------------------------------------------------------------------------
    def get_all_vms(self):

        ret = 0
        all_hosts = []

        for vsphere_name in self.vsphere:
            all_hosts += self.get_hosts(vsphere_name)

        if self.verbose > 1:
            out_hosts = []
            for host in all_hosts:
                out_hosts.append(host.as_dict())
            LOG.debug("All hosts:\n{}".format(pp(out_hosts)))

#        if self.details:
#            self.print_vms_detailed(all_vms)
#        else:
#            self.print_vms(all_vms)

        return ret

    # -------------------------------------------------------------------------
    def get_hosts(self, vsphere_name):

        hosts = []

        vsphere = self.vsphere[vsphere_name]
        vsphere.get_datacenter()
        vsphere.get_hosts()

        for host_name in sorted(vsphere.hosts.keys()):
            host = vsphere.hosts[host_name]
            hosts.append(host)

        return hosts


# =============================================================================
if __name__ == "__main__":

    pass

# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 list
