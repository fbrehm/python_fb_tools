#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: Frank Brehm
@contact: frank.brehm@pixelpark.com
@copyright: © 2021 by Frank Brehm, Berlin
@summary: The module for the 'get-vmware-vm-info' application object.
"""
from __future__ import absolute_import, print_function

# Standard modules
import logging
import getpass
import re
import copy

from operator import itemgetter, attrgetter

# Third party modules
import pytz

# Own modules
from . import __version__ as GLOBAL_VERSION
from . import VMWARE_CFGFILE_BASENAME

from .xlate import XLATOR, format_list

from .common import pp, to_bool

from .app import RegexOptionAction

from .cfg_app import FbConfigApplication

from .config import CfgFileOptionAction

from .errors import FbAppError

from .vmware_config import VmwareConfiguration

from .vsphere.server import VsphereServer

from .vsphere.vm import VsphereVm

__version__ = '1.4.0'
LOG = logging.getLogger(__name__)
TZ = pytz.timezone('Europe/Berlin')

_ = XLATOR.gettext
ngettext = XLATOR.ngettext


# =============================================================================
class GetVmListAppError(FbAppError):
    """ Base exception class for all exceptions in this application."""
    pass


# =============================================================================
class GetVmListApplication(FbConfigApplication):
    """
    Class for the application objects.
    """

    default_vm_pattern = r'.*'

    # -------------------------------------------------------------------------
    def __init__(
        self, appname=None, verbose=0, version=GLOBAL_VERSION, base_dir=None,
            cfg_class=VmwareConfiguration, initialized=False, usage=None, description=None,
            argparse_epilog=None, argparse_prefix_chars='-', env_prefix=None):

        desc = _(
            "Tries to get a list of all virtual machines in "
            "VMWare VSphere and print it out.")

        self._vm_pattern = self.default_vm_pattern
        self.req_vspheres = None
        self.do_vspheres = []
        self._details = False

        self._re_hw = None
        self._re_os = None

        # Hash with all VSphere handler objects
        self.vsphere = {}

        self.vms = []

        super(GetVmListApplication, self).__init__(
            appname=appname, verbose=verbose, version=version, base_dir=base_dir,
            description=desc, cfg_class=cfg_class, initialized=False,
        )

        self.initialized = True

    # -------------------------------------------------------------------------
    @property
    def vm_pattern(self):
        """The regex search pattern for filtering the VM list."""
        return self._vm_pattern

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

        res = super(GetVmListApplication, self).as_dict(short=short)
        res['vm_pattern'] = self.vm_pattern
        res['details'] = self.details
        res['default_vm_pattern'] = self.default_vm_pattern

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

        super(GetVmListApplication, self).post_init()

        if not self.cfg.vsphere.keys():
            msg = _("Did not found any configured Vsphere environments.")
            LOG.error(msg)
            self.exit(3)

        if self.args.req_vsphere:
            self.req_vspheres = []
            all_found = True
            for vs_name in self.args.req_vsphere:
                LOG.debug(_("Checking for configured VSPhere instance {!r} ...").format(vs_name))
                vs = vs_name.strip().lower()
                if vs not in self.cfg.vsphere.keys():
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
            self.do_vspheres = copy.copy(self.req_vspheres)
        else:
            for vs_name in self.cfg.vsphere.keys():
                self.do_vspheres.append(vs_name)

        for vsphere_name in self.cfg.vsphere.keys():
            vsphere_data = self.cfg.vsphere[vsphere_name]
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

        filter_group = self.arg_parser.add_argument_group(_('Filter options'))

        filter_group.add_argument(
            '-p', '--pattern', '--search-pattern',
            dest='vm_pattern', metavar='REGEX', action=RegexOptionAction,
            topic=_('for names of VMs'), re_options=re.IGNORECASE,
            help=_(
                "A regular expression to filter the output list of VMs by their name "
                "(Default: {!r}).").format(self.default_vm_pattern)
        )

        valid_vm_types = ('all', 'vm', 'template')
        filter_group.add_argument(
            '-T', '--type', metavar=_('TYPE'), dest='vm_type', choices=valid_vm_types,
            default='all', help=_(
                "Filter output for the type of the VM. Valid values are {li} "
                "(Default: {dflt!r}).").format(
                dflt='all', li=format_list(valid_vm_types, do_repr=True))
        )

        online_filter = filter_group.add_mutually_exclusive_group()
        online_filter.add_argument(
            '--on', '--online', action="store_true", dest="online",
            help=_("Filter output for online VMs.")
        )
        online_filter.add_argument(
            '--off', '--offline', action="store_true", dest="offline",
            help=_("Filter output for offline VMs and templates.")
        )

        filter_group.add_argument(
            '-H', '--hw', '--hardware-config', metavar='REGEX', action=RegexOptionAction,
            dest='hw', topic=_('for VMWare hardware config version'), re_options=re.IGNORECASE,
            help=_(
                "A regular expression to filter the output list of VMs by the VMWare hardware "
                "configuration version (e.g. '{}').").format(r'vmx-0\d$'),
        )

        filter_group.add_argument(
            '--os', metavar='REGEX', action=RegexOptionAction, dest='os',
            topic=_('for the Operating System version'), re_options=re.IGNORECASE,
            help=_(
                "A regular expression to filter the output list of VMs by their Operating "
                "System version, e.g. '{}'.").format('oracleLinux.*(_64)?Guest')
        )

        filter_group.add_argument(
            '--vs', '--vsphere', dest='req_vsphere', nargs='*',
            help=_(
                "The VSPhere names from configuration, in which the VMs should be searched.")
        )

        output_options = self.arg_parser.add_argument_group(_('Output options'))

        output_options.add_argument(
            '-D', '--details', dest='details', action="store_true",
            help=_("Detailed output list (quering data needs some time longer).")
        )

    # -------------------------------------------------------------------------
    def perform_arg_parser(self):

        if self.verbose > 2:
            LOG.debug(_("Got command line arguments:") + '\n' + pp(self.args))

        if self.args.cfg_file:
            self._cfg_file = self.args.cfg_file

        if self.args.details:
            self.details = self.args.details

        if self.args.vm_pattern:
            try:
                re_name = re.compile(self.args.vm_pattern, re.IGNORECASE)
                LOG.debug(_("Regular expression for filtering: {!r}").format(re_name.pattern))
                self._vm_pattern = self.args.vm_pattern
            except Exception as e:
                msg = _("Got a {c} for pattern {p!r}: {e}").format(
                    c=e.__class__.__name__, p=self.args.vm_pattern, e=e)
                LOG.error(msg)

        if not self.details:
            if self.args.online or self.args.offline or self.args.hw or self.args.os or \
                    self.args.vm_type != 'all':
                LOG.info(_("Detailed output is required because of your given options."))
                self.details = True

        if self.args.hw:
            self._re_hw = re.compile(self.args.hw, re.IGNORECASE)
        if self.args.os:
            self._re_os = re.compile(self.args.os, re.IGNORECASE)

    # -------------------------------------------------------------------------
    def init_vsphere_handlers(self):

        for vsphere_name in self.do_vspheres:
            self.init_vsphere_handler(vsphere_name)

    # -------------------------------------------------------------------------
    def init_vsphere_handler(self, vsphere_name):

        vsphere_data = self.cfg.vsphere[vsphere_name]

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
            msg = _("Could not initialize {} object from:").format('VsphereServer')
            msg += '\n' + pp(vsphere_data)
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
            for vsphere_name in self.do_vspheres:
                LOG.debug(_("Closing VSPhere object {!r} ...").format(vsphere_name))
                self.vsphere[vsphere_name].disconnect()
                del self.vsphere[vsphere_name]

        self.exit(ret)

    # -------------------------------------------------------------------------
    def get_all_vms(self):

        ret = 0
        all_vms = []

        re_name = re.compile(self.vm_pattern, re.IGNORECASE)

        for vsphere_name in self.vsphere:
            all_vms += self.get_vms(vsphere_name, re_name)

        if self.details:
            self.print_vms_detailed(all_vms)
        else:
            self.print_vms(all_vms)

        return ret

    # -------------------------------------------------------------------------
    def print_vms(self, all_vms):

        label_list = ('name', 'vsphere', 'path')
        labels = {
            'name': 'Host',
            'vsphere': 'VSphere',
            'path': 'Path',
        }

        self._print_vms(all_vms, label_list, labels)

    # -------------------------------------------------------------------------
    def print_vms_detailed(self, all_vms):

        label_list = ('name', 'vsphere', 'cluster', 'path', 'type', 'onl_str', 'cfg_ver', 'os')
        labels = {
            'name': 'Host',
            'vsphere': 'VSphere',
            'cluster': 'Cluster',
            'path': 'Path',
            'type': 'Type',
            'onl_str': 'Online Status',
            'cfg_ver': 'Config Version',
            'os': 'Operating System',
        }

        self._print_vms(all_vms, label_list, labels)

    # -------------------------------------------------------------------------
    def _print_vms(self, all_vms, label_list, labels):

        str_lengths = {}
        for label in labels.keys():
            str_lengths[label] = len(labels[label])

        max_len = 0
        count = 0
        for cdata in all_vms:
            for field in ('cluster', 'path', 'type', 'cfg_ver', 'os'):
                if field in labels and cdata[field] is None:
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

        for cdata in all_vms:
            count += 1

            print(tpl.format(**cdata))

        if not self.quiet:
            print()
            if count == 0:
                msg = _("Found no VMWare VMs.")
            else:
                msg = ngettext(
                    "Found one VMWare VM.",
                    "Found {} VMWare VMs.", count).format(count)
            print(msg)
            print()

    # -------------------------------------------------------------------------
    def get_vms(self, vsphere_name, re_name=None):

        vsphere = self.vsphere[vsphere_name]
        vsphere.get_datacenter()

        if re_name is None:
            re_name = re.compile(self.vm_pattern, re.IGNORECASE)

        if self.details:
            vm_list = vsphere.get_vms(re_name, vsphere_name=vsphere_name, as_obj=True)
            vms = self.mangle_vmlist_details(vm_list, vsphere_name)
        else:
            vm_list = vsphere.get_vms(re_name, vsphere_name=vsphere_name, name_only=True)
            vms = self.mangle_vmlist_no_details(vm_list, vsphere_name)

        return vms

    # -------------------------------------------------------------------------
    def mangle_vmlist_no_details(self, vm_list, vsphere_name):

        if self.verbose > 3:
            LOG.debug("Mangling VM list:\n" + pp(vm_list))

        vms = []

        for vm in sorted(vm_list, key=itemgetter(0, 1)):
            cdata = {
                'vsphere': vsphere_name,
                'name': vm[0],
                'path': vm[1],
            }

            if cdata['path']:
                cdata['path'] = '/' + cdata['path']
            else:
                cdata['path'] = '/'

            vms.append(cdata)

        return vms

    # -------------------------------------------------------------------------
    def mangle_vmlist_details(self, vm_list, vsphere_name):

        vms = []

        first = True
        for vm in sorted(vm_list, key=attrgetter('name', 'path')):

            if not isinstance(vm, VsphereVm):
                msg = _("Found a {} object:").format(vm.__class__.__name__)
                msg += '\n' + pp(vm)
                LOG.error(msg)
                continue

            if self.verbose > 2 and first:
                LOG.debug("VM:\n" + pp(vm.as_dict()))
            first = False

            cdata = self._mangle_vm_details(vm, vsphere_name)
            if not cdata:
                continue

            vms.append(cdata)

        return vms

    # -------------------------------------------------------------------------
    def _mangle_vm_details(self, vm, vsphere_name):

        cdata = None

        if self.args.vm_type != 'all':
            if self.args.vm_type == 'vm':
                if vm.template:
                    return None
            else:
                if not vm.template:
                    return None

        if self.args.online:
            if not vm.online:
                return None
        elif self.args.offline:
            if vm.online:
                return None

        if self._re_hw:
            if not self._re_hw.search(vm.config_version):
                return None

        if self._re_os:
            if not self._re_os.search(vm.config_version):
                return None

        cdata = {
            'vsphere': vsphere_name,
            'cluster': vm.cluster_name,
            'name': vm.name,
            'path': vm.path,
            'type': 'Virtual Machine',
            'online': vm.online,
            'onl_str': 'Online',
            'cfg_ver': vm.config_version,
            'os': vm.guest_id,
        }

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

        return cdata


# =============================================================================
if __name__ == "__main__":

    pass

# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 list
