#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: Frank Brehm
@contact: frank.brehm@pixelpark.com
@copyright: © 2019 by Frank Brehm, Berlin
@summary: The module for the 'get-vmware-vm-info' application object.
"""
from __future__ import absolute_import, print_function

# Standard modules
import logging
import getpass
import re

# Third party modules

# Own modules
from . import __version__ as GLOBAL_VERSION

from .xlate import XLATOR

from .common import pp

from .app import BaseApplication

from .config import CfgFileOptionAction

from .errors import FbAppError

from .get_vm_cfg import GetVmConfiguration

from .vsphere.server import VsphereServer

__version__ = '1.0.1'
LOG = logging.getLogger(__name__)

_ = XLATOR.gettext


# =============================================================================
class GetVmListAppError(FbAppError):
    """ Base exception class for all exceptions in this application."""
    pass


# =============================================================================
class GetVmListApplication(BaseApplication):
    """
    Class for the application objects.
    """

    # -------------------------------------------------------------------------
    def __init__(
        self, appname=None, verbose=0, version=GLOBAL_VERSION, base_dir=None,
            initialized=False, usage=None, description=None,
            argparse_epilog=None, argparse_prefix_chars='-', env_prefix=None):

        desc = _(
            "Tries to get a list of all virtual machines in "
            "VMWare VSphere and print it out.")

        self._cfg_file = None
        self.config = None
        self.vsphere = None

        self.vms = []

        super(GetVmListApplication, self).__init__(
            appname=appname, verbose=verbose, version=version, base_dir=base_dir,
            description=desc, initialized=False,
        )

        self.initialized = True

    # -------------------------------------------------------------------------
    @property
    def cfg_file(self):
        """Configuration file."""
        return self._cfg_file

    # -------------------------------------------------------------------------
    def as_dict(self, short=True):
        """
        Transforms the elements of the object into a dict

        @param short: don't include local properties in resulting dict.
        @type short: bool

        @return: structure as dict
        @rtype:  dict
        """

        res = super(GetVmListApplication, self).as_dict(short=short)
        res['cfg_file'] = self.cfg_file

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

        if not self.cfg_file:
            self._cfg_file = self.base_dir.joinpath('etc').joinpath('get-vmware-vm-info.ini')

        self.config = GetVmConfiguration(
            appname=self.appname, verbose=self.verbose, base_dir=self.base_dir,
            config_file=self.cfg_file)

        self.config.read()
        if self.config.verbose > self.verbose:
            self.verbose = self.config.verbose
        self.config.initialized = True

        if self.verbose > 3:
            LOG.debug("Read configuration:\n{}".format(pp(self.config.as_dict())))

        self.perform_arg_parser_vmware()

        if not self.config.password:
            prompt = _('Enter password for host {h!r} and user {u!r}: ').format(
                h=self.config.vsphere_host, u=self.config.vsphere_user)
            self.config.password = getpass.getpass(prompt=prompt)

        self.vsphere = VsphereServer(
            appname=self.appname, verbose=self.verbose, base_dir=self.base_dir,
            host=self.config.vsphere_host, port=self.config.vsphere_port,
            user=self.config.vsphere_user, password=self.config.password,
            dc=self.config.dc, auto_close=True, simulate=self.simulate, force=self.force,
            terminal_has_colors=self.terminal_has_colors, initialized=False)

        self.vsphere.initialized = True
        self.initialized = True

    # -------------------------------------------------------------------------
    def init_arg_parser(self):
        """
        Public available method to initiate the argument parser.
        """

        super(GetVmListApplication, self).init_arg_parser()

        default_cfg_file = self.base_dir.joinpath('etc').joinpath(self.appname + '.ini')

        self.arg_parser.add_argument(
            '-c', '--config', '--config-file', dest='cfg_file', metavar=_('FILE'),
            action=CfgFileOptionAction,
            help=_("Configuration file (default: {!r})").format(str(default_cfg_file))
        )

        vmware_group = self.arg_parser.add_argument_group(_('VMWare options'))

        vmware_group.add_argument(
            '-H', '--host', dest='host',
            help=_("Remote vSphere host to connect to (Default: {!r}).").format(
                GetVmConfiguration.default_vsphere_host)
        )

        vmware_group.add_argument(
            '-p', '--port', dest='port', type=int,
            help=_("Port on vSphere host to connect on (Default: {}).").format(
                GetVmConfiguration.default_vsphere_port)
        )

        vmware_group.add_argument(
            '-U', '--user', dest='user', metavar=_('USER'),
            help=_("User name to use when connecting to vSphere host (Default: {!r}).").format(
                GetVmConfiguration.default_vsphere_user)
        )

        vmware_group.add_argument(
            '-P', '--password', dest='password', metavar=_('PASSWORD'),
            help=_("Password to use when connecting to vSphere host."),
        )

    # -------------------------------------------------------------------------
    def perform_arg_parser(self):

        if self.args.cfg_file:
            self._cfg_file = self.args.cfg_file

    # -------------------------------------------------------------------------
    def perform_arg_parser_vmware(self):
        """
        Public available method to execute some actions after parsing
        the command line parameters.
        """

        if self.args.host:
            self.config.vsphere_host = self.args.host
        if self.args.port:
            self.config.vsphere_port = self.args.port
        if self.args.user:
            self.config.vsphere_user = self.args.user
        if self.args.password:
            self.config.password = self.args.password

    # -------------------------------------------------------------------------
    def _run(self):

        LOG.debug(_("Starting {a!r}, version {v!r} ...").format(
            a=self.appname, v=self.version))

        ret = 99
        try:
            ret = self.get_vms()
        finally:
            # Aufräumen ...
            LOG.debug(_("Closing ..."))
            self.vsphere.disconnect()
            self.vsphere = None

        self.exit(ret)

    # -------------------------------------------------------------------------
    def get_vms(self):

        ret = 0
        vms = []

        re_all = re.compile(r'.*')
        vms = self.vsphere.get_vms(re_all, disconnect=True)

        i = 0
        for vm in vms:
            i += 1
            print("\n{n}:\n{vm}".format(n=vm['name'], vm=pp(vm)))
            if i >= 3:
                break

        return ret


# =============================================================================
if __name__ == "__main__":

    pass

# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 list
