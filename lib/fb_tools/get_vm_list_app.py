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
import argparse
import re

# Third party modules
import pytz

# Own modules
from . import __version__ as GLOBAL_VERSION
from . import VMWARE_CFGFILE_BASENAME

from .xlate import XLATOR

from .common import pp

from .app import BaseApplication, RegexOptionAction

from .config import CfgFileOptionAction

from .errors import FbAppError

from .vmware_config import VmwareConfiguration

from .vsphere.server import VsphereServer

from .vsphere.vm import VsphereVm

__version__ = '1.1.1'
LOG = logging.getLogger(__name__)
TZ = pytz.timezone('Europe/Berlin')

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

    default_vm_pattern = r'.*'

    # -------------------------------------------------------------------------
    def __init__(
        self, appname=None, verbose=0, version=GLOBAL_VERSION, base_dir=None,
            initialized=False, usage=None, description=None,
            argparse_epilog=None, argparse_prefix_chars='-', env_prefix=None):

        desc = _(
            "Tries to get a list of all virtual machines in "
            "VMWare VSphere and print it out.")

        self._cfg_file = None
        self._cfg_dir = None
        self.config = None
        self._vm_pattern = self.default_vm_pattern
        self.req_vspheres = None

        # Hash with all VSphere handler objects
        self.vsphere = {}

        self.vms = []

        super(GetVmListApplication, self).__init__(
            appname=appname, verbose=verbose, version=version, base_dir=base_dir,
            description=desc, initialized=False,
        )

        self.initialized = True

    # -------------------------------------------------------------------------
    @property
    def cfg_dir(self):
        """Directory of the configuration file."""
        return self._cfg_dir

    # -------------------------------------------------------------------------
    @property
    def cfg_file(self):
        """Configuration file."""
        return self._cfg_file

    # -------------------------------------------------------------------------
    @property
    def vm_pattern(self):
        """The regex search pattern for filtering the VM list."""
        return self._vm_pattern

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
        res['cfg_dir'] = self.cfg_dir
        res['cfg_file'] = self.cfg_file
        res['vm_pattern'] = self.vm_pattern
        res['default_vm_pattern'] = self.default_vm_pattern

        res['vsphere'] = {}
        for vsphere_name in self.vsphere:
            res['vsphere'][vsphere_name] = {}
            vsphere = self.vsphere[vsphere_name]
            if vsphere:
                res['vsphere'][vsphere_name] = vsphere.as_dict(short=short)

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

        self._cfg_dir = self.base_dir.joinpath('etc')
        self._cfg_file = self.cfg_dir.joinpath(VMWARE_CFGFILE_BASENAME)

        self.perform_arg_parser()

        if not self.cfg_file.exists():
            default_conf_file = self.cfg_dir.joinpath(VMWARE_CFGFILE_BASENAME + '.default')
            msg = (_(
                "Configuration file {f!r} does not exists. Please copy {d!r} to {f!r} and "
                "fill out all necessary entries, e.g. the passwords.").format(
                    f=str(self.cfg_file), d=str(default_conf_file)))
            LOG.error(msg)
            self.exit(1)

        self.config = VmwareConfiguration(
            appname=self.appname, verbose=self.verbose, base_dir=self.base_dir,
            config_file=self.cfg_file)

        self.config.read()
        if self.config.verbose > self.verbose:
            self.verbose = self.config.verbose
        self.config.initialized = True

        if self.verbose > 3:
            LOG.debug("Read configuration:\n{}".format(pp(self.config.as_dict())))

        if self.args.req_vsphere:
            self.req_vspheres = []
            all_found = True
            for vs_name in self.args.req_vsphere:
                LOG.debug(_("Checking for configured VSPhere instance {!r} ...").format(vs_name))
                vs = vs_name.strip().lower()
                if vs not in self.config.vsphere.keys():
                    all_found = False
                    msg = _(
                        "VSPhere {!r} not found in list of configured VSPhere instances.").format(
                            vs_name)
                    LOG.error(msg)
                else:
                    if vs not in self.req_vspheres:
                        self.req_vspheres.append(vs)
            if not all_found:
                self.exit(1)

        if self.req_vspheres:
            vs2remove = []
            for vsphere_name in self.config.vsphere.keys():
                if vsphere_name not in self.req_vspheres:
                    vs2remove.append(vsphere_name)
            for vsphere_name in vs2remove:
                del self.config.vsphere[vsphere_name]

        if not self.config.vsphere.keys():
            msg = (_(
                'Did not found any valid VSphere definition in {!r}.').format(self.cfg_file))
            LOG.error(msg)
            self.exit(1)

        for vsphere_name in self.config.vsphere.keys():
            vsphere_data = self.config.vsphere[vsphere_name]
            pw = None
            if 'password' in vsphere_data:
                pw = vsphere_data['password']
                if pw is None or pw == '':
                    prompt = (
                        _('Enter password for {n} VSPhere user {u!r} on host {h!r}:').format(
                            n=vsphere_name, u=vsphere_data['user'], h=vsphere_data['host'])) + ' '
                    vsphere_data['password'] = getpass.getpass(prompt=prompt)

        self.init_vsphere_handlers()

        self.initialized = True

    # -------------------------------------------------------------------------
    def init_arg_parser(self):
        """
        Public available method to initiate the argument parser.
        """

        super(GetVmListApplication, self).init_arg_parser()

        self._cfg_dir = self.base_dir.joinpath('etc')
        self._cfg_file = self.cfg_dir.joinpath(VMWARE_CFGFILE_BASENAME)
        default_cfg_file = self.cfg_file

        self.arg_parser.add_argument(
            '-p', '--pattern', '--search-pattern',
            dest='vm_pattern', metavar='REGEX', action=RegexOptionAction,
            topic=_('for names of VMs'), re_options=re.IGNORECASE,
            help=_(
                "A regular expression to filter the output list of VMs by their name "
                "(Default: {!r}).").format(self.default_vm_pattern)
        )

        self.arg_parser.add_argument(
            '--vs', '--vsphere', dest='req_vsphere', nargs='*',
            help=_(
                "The VSPhere names from configuration, in which the VMs should be searched.")
        )

        self.arg_parser.add_argument(
            '-c', '--config', '--config-file', dest='cfg_file', metavar=_('FILE'),
            action=CfgFileOptionAction,
            help=_("Configuration file (default: {!r})").format(str(default_cfg_file))
        )

    # -------------------------------------------------------------------------
    def perform_arg_parser(self):

        if self.verbose > 1:
            LOG.debug(_("Got command line arguments:") + '\n' + pp(self.args))

        if self.args.cfg_file:
            self._cfg_file = self.args.cfg_file

        if self.args.vm_pattern:
            try:
                re_name = re.compile(self.args.vm_pattern, re.IGNORECASE)
                LOG.debug(_("Regular expression for filtering: {!r}").format(re_name.pattern))
                self._vm_pattern = self.args.vm_pattern
            except Exception as e:
                msg = _("Got a {c} for pattern {p!r}: {e}").format(
                    c=e.__class__.__name__, p=self.args.vm_pattern, e=e)
                LOG.error(msg)

    # -------------------------------------------------------------------------
    def init_vsphere_handlers(self):

        for vsphere_name in self.config.vsphere.keys():
            self.init_vsphere_handler(vsphere_name)

    # -------------------------------------------------------------------------
    def init_vsphere_handler(self, vsphere_name):

        vsphere_data = self.config.vsphere[vsphere_name]

        pwd = None
        if 'password' in vsphere_data:
            pwd = vsphere_data['password']

        vsphere = VsphereServer(
            appname=self.appname, verbose=self.verbose, base_dir=self.base_dir,
            host=vsphere_data['host'], port=vsphere_data['port'], dc=vsphere_data['dc'],
            user=vsphere_data['user'], password=pwd,
            auto_close=True, simulate=self.simulate, force=self.force,
            terminal_has_colors=self.terminal_has_colors, initialized=False)

        if vsphere:
            self.vsphere[vsphere_name] = vsphere
            vsphere.initialized = True
        else:
            msg = (
                _("Could not initialize {} object from:").format('VsphereServer') + \
                '\n' + pp(vsphere_data))
            LOG.error(msg)

    # -------------------------------------------------------------------------
    def _run(self):

        LOG.debug(_("Starting {a!r}, version {v!r} ...").format(
            a=self.appname, v=self.version))

        ret = 0
        try:
            ret = self.get_all_vms()
        finally:
            # Aufräumen ...
            for vsphere_name in self.config.vsphere.keys():
                LOG.debug(_("Closing VSPhere object {!r} ...").format(vsphere_name))
                self.vsphere[vsphere_name].disconnect()
                del self.vsphere[vsphere_name]

        self.exit(ret)

    # -------------------------------------------------------------------------
    def get_all_vms(self):

        ret = 0
        all_vms = {}

        re_name = re.compile(self.vm_pattern, re.IGNORECASE)

        for vsphere_name in self.vsphere:
            vms = self.get_vms(vsphere_name, re_name)
            for vm_name in vms.keys():
                all_vms[vm_name] = vms[vm_name]

        label_list = ('name', 'vsphere', 'cluster', 'path', 'type', 'onl_str', 'os')
        labels = {
            'name': 'Host',
            'vsphere': 'VSphere',
            'cluster': 'Cluster',
            'path': 'Path',
            'type': 'Type',
            'onl_str': 'Online Status',
            'os': 'Operating System',
        }
        str_lengths = {}
        for label in labels.keys():
            str_lengths[label] = len(labels[label])

        max_len = 0
        count = 0
        for host_name in all_vms.keys():
            cdata = all_vms[host_name]
            for field in ('cluster', 'path', 'type', 'os'):
                if cdata[field] is None:
                    cdata[field] = '-'
            for label in labels.keys():
                val = cdata[label]
                if len(val) > str_lengths[label]:
                    str_lengths[label] = len(val)

        for label in labels.keys():
            if max_len:
                max_len += 2
            max_len += str_lengths[label]

        if self.verbose > 1:
            LOG.debug("Label length:\n" + pp(str_lengths))
            LOG.debug("Max line length: {} chars".format(max_len))

        tpl = ''
        for label in label_list:
            if tpl != '':
                tpl += '  '
            tpl += '{{{la}:<{le}}}'.format(la=label, le=str_lengths[label])
        if self.verbose > 1:
            LOG.debug("Line template: {}".format(tpl))

        if not self.quiet:
            print()
            print(tpl.format(**labels))
            print('-' * max_len)

        for host_name in sorted(all_vms.keys(), key=str.lower):
            cdata = all_vms[host_name]
            count += 1

            print(tpl.format(**cdata))

        if not self.quiet:
            print()
            msg = "Found {} VMWare hosts and VMs.".format(count)
            if count == 1:
                msg = "Found one VMWare host or VM."
            elif count == 0:
                msg = "Found no VMWare hosts or VMs."
            print(msg)
            print()

        return ret

    # -------------------------------------------------------------------------
    def get_vms(self, vsphere_name, re_name=None):

        vsphere = self.vsphere[vsphere_name]
        vsphere.get_datacenter()

        if re_name is None:
            re_name = re.compile(self.vm_pattern, re.IGNORECASE)

        vm_list = vsphere.get_vms(re_name, as_obj=True)
        vms = {}

        for vm in vm_list:
            if not isinstance(vm, VsphereVm):
                LOG.error("Found a {} object:\n".format(vm.__class__.__name__) + pp(vm))
                continue
            cdata = {
                'vsphere': vsphere_name,
                'cluster': vm.cluster_name,
                'name': vm.name,
                'path': vm.path,
                'type': 'Virtual Machine',
                'online': vm.online,
                'onl_str': 'Online',
                'os': vm.guest_id,
            }
            if vm.template:
                continue

            if cdata['path']:
                cdata['path'] = '/' + cdata['path']
            else:
                cdata['path'] = '/'

            if not cdata['cluster']:
                cdata['cluster'] = None

            if not cdata['os']:
                cdata['os'] = None

            if not vm.online:
                cdata['onl_str'] = 'Offline'

            if vm.template:
                cdata['type'] = 'VMWare Template'

            vms[vm.name] = cdata

        return vms

# =============================================================================
if __name__ == "__main__":

    pass

# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 list
