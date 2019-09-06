#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: Frank Brehm
@contact: frank.brehm@pixelpark.com
@copyright: © 2019 by Frank Brehm, Berlin
@summary: The module for a VSphere virtual machine or template object.
"""
from __future__ import absolute_import

# Standard modules
import logging
import uuid

# Third party modules
from pyVmomi import vim

# Own modules
from ..xlate import XLATOR

from ..common import pp, to_bool

from .object import VsphereObject

from .disk import VsphereDisk, VsphereDiskList

__version__ = '0.3.1'
LOG = logging.getLogger(__name__)


_ = XLATOR.gettext


# =============================================================================
class VsphereVm(VsphereObject):

    # -------------------------------------------------------------------------
    def __init__(
        self, appname=None, verbose=0, version=__version__, base_dir=None, initialized=None,
            name=None, status='gray', config_status='gray'):

        self.repr_fields = ('name', )
        self._cluster_name = None
        self._path = None
        self._template = False
        self._memory_mb = None
        self._num_cpu = None
        self._num_ethernet = None
        self._num_vdisk = None
        self._guest_fullname = None
        self._guest_id = None
        self._uuid = None
        self._instance_uuid = None
        self._host = None
        self.power_state = None
        self.disks = []

        self.vm_tools = None

        super(VsphereVm, self).__init__(
            name=name, obj_type='vsphere_vm', name_prefix="vm", status=status,
            config_status=config_status, appname=appname, verbose=verbose,
            version=version, base_dir=base_dir)

        self.disks = VsphereDiskList(
            appname=appname, verbose=verbose, base_dir=base_dir, initialized=True)

    # -----------------------------------------------------------
    @property
    def cluster_name(self):
        """The name of the compute resource, where this host is a member."""
        return self._cluster_name

    @cluster_name.setter
    def cluster_name(self, value):
        if value is None:
            self._cluster_name = None
            return
        v = str(value).strip().lower()
        if v == '':
            self._cluster_name = None
        else:
            self._cluster_name = v

    # -----------------------------------------------------------
    @property
    def host(self):
        """The host name, where the VM is configured."""
        return self._host

    @host.setter
    def host(self, value):
        if value is None:
            self._host = None
            return
        v = str(value).strip()
        if v == '':
            self._host = None
        else:
            self._host = v

    # -----------------------------------------------------------
    @property
    def path(self):
        """The path of the VM in the VM folder structure."""
        return self._path

    @path.setter
    def path(self, value):
        if value is None:
            self._path = None
            return
        v = str(value).strip()
        if v == '':
            self._path = None
        else:
            self._path = v

    # -----------------------------------------------------------
    @property
    def template(self):
        "Is this a VMWare template instead of a VM."
        return self._template

    @template.setter
    def template(self, value):
        self._template = to_bool(value)

    # -----------------------------------------------------------
    @property
    def memory_mb(self):
        """The memory (RAM) of the VM in MiB."""
        return self._memory_mb

    @memory_mb.setter
    def memory_mb(self, value):
        if value is None:
            self._memory_mb = None
            return
        self._memory_mb = int(value)

    # -----------------------------------------------------------
    @property
    def memory_gb(self):
        """The memory (RAM) of the VM in GiB."""
        if self.memory_mb is None:
            return None
        return float(self.memory_mb) / 1024.0

    # -----------------------------------------------------------
    @property
    def num_cpu(self):
        """The number of CPUs of the VM."""
        return self._num_cpu

    @num_cpu.setter
    def num_cpu(self, value):
        if value is None:
            self._num_cpu = None
            return
        self._num_cpu = int(value)

    # -----------------------------------------------------------
    @property
    def num_ethernet(self):
        """The number of virtual ethernet network cards of the VM."""
        return self._num_ethernet

    @num_ethernet.setter
    def num_ethernet(self, value):
        if value is None:
            self._num_ethernet = None
            return
        self._num_ethernet = int(value)

    # -----------------------------------------------------------
    @property
    def num_vdisk(self):
        """The number of virtual disks of the VM."""
        return self._num_vdisk

    @num_vdisk.setter
    def num_vdisk(self, value):
        if value is None:
            self._num_vdisk = None
            return
        self._num_vdisk = int(value)

    # -----------------------------------------------------------
    @property
    def guest_fullname(self):
        """The guest Operating system name."""
        return self._guest_fullname

    @guest_fullname.setter
    def guest_fullname(self, value):
        if value is None:
            self._guest_fullname = None
            return
        v = str(value).strip()
        if v == '':
            self._guest_fullname = None
        else:
            self._guest_fullname = v

    # -----------------------------------------------------------
    @property
    def guest_id(self):
        """The guest Operating system identifier (shortname)."""
        return self._guest_id

    @guest_id.setter
    def guest_id(self, value):
        if value is None:
            self._guest_id = None
            return
        v = str(value).strip()
        if v == '':
            self._guest_id = None
        else:
            self._guest_id = v

    # -----------------------------------------------------------
    @property
    def uuid(self):
        """The Virtual machine BIOS identification."""
        return self._uuid

    @uuid.setter
    def uuid(self, value):
        if value is None:
            self._uuid = None
            return
        v = str(value).strip()
        if v == '':
            self._uuid = None
        else:
            self._uuid = uuid.UUID(v)

    # -----------------------------------------------------------
    @property
    def instance_uuid(self):
        """The VC-specific identifier of the virtual machine."""
        return self._instance_uuid

    @instance_uuid.setter
    def instance_uuid(self, value):
        if value is None:
            self._instance_uuid = None
            return
        v = str(value).strip()
        if v == '':
            self._instance_uuid = None
        else:
            self._instance_uuid = uuid.UUID(v)

    # -----------------------------------------------------------
    @property
    def online(self):
        """Is this VM generally online or not."""
        if self.template:
            return False
        if self.power_state is None:
            return False
        if self.power_state.lower() in ('poweredoff', 'suspended'):
            return False
        return True

    # -------------------------------------------------------------------------
    def as_dict(self, short=True):
        """
        Transforms the elements of the object into a dict

        @param short: don't include local properties in resulting dict.
        @type short: bool

        @return: structure as dict
        @rtype:  dict
        """

        res = super(VsphereVm, self).as_dict(short=short)
        res['cluster_name'] = self.cluster_name
        res['host'] = self.cluster_name
        res['path'] = self.path
        res['template'] = self.template
        res['online'] = self.online
        res['memory_mb'] = self.memory_mb
        res['memory_gb'] = self.memory_gb
        res['num_cpu'] = self.num_cpu
        res['num_ethernet'] = self.num_ethernet
        res['num_vdisk'] = self.num_vdisk
        res['guest_fullname'] = self.guest_fullname
        res['guest_id'] = self.guest_id
        res['uuid'] = self.uuid
        res['instance_uuid'] = self.instance_uuid

        return res

    # -------------------------------------------------------------------------
    def __copy__(self):

        vm = VsphereVm(
            appname=self.appname, verbose=self.verbose, base_dir=self.base_dir,
            initialized=self.initialized, name=self.name, status=self.status,
            config_status=self.config_status)

        vm.cluster_name = self.cluster_name
        vm.host = self.host
        vm.path = self.path
        vm.template = self.template
        vm.memory_mb = self.memory_mb
        vm.num_cpu = self.num_cpu
        vm.num_ethernet = self.num_ethernet
        vm.num_vdisk = self.num_vdisk
        vm.guest_fullname = self.guest_fullname
        vm.guest_id = self.guest_id
        vm.uuid = self.uuid
        vm.instance_uuid = self.instance_uuid
        vm.power_state = self.power_state
        vm.disks = copy.copy(self.disks)

        return vm

    # -------------------------------------------------------------------------
    def __eq__(self, other):

        if self.verbose > 4:
            LOG.debug(_("Comparing {} objects ...").format(self.__class__.__name__))

        if not isinstance(other, VsphereVm):
            return False

        if self.name != other.name:
            return False

        return True

    # -------------------------------------------------------------------------
    @classmethod
    def from_summary(cls, data, cur_path, appname=None, verbose=0, base_dir=None):

        if not isinstance(data, vim.VirtualMachine):
            msg = _("Parameter {t!r} must be a {e}, {v!r} ({vt}) was given.").format(
                t='data', e='vim.VirtualMachine', v=data, vt=data.__class__.__name__)
            raise TypeError(msg)

        params = {
            'appname': appname,
            'verbose': verbose,
            'base_dir': base_dir,
            'initialized': True,
            'name': data.summary.config.name,
            'status': 'gray',
            'config_status': 'green',
        }

        if verbose > 2:
            LOG.debug(_("Creating {} object from:").format(cls.__name__) + '\n' + pp(params))

        vm = cls(**params)

        vm.cluster_name = None
        if data.resourcePool:
            vm.cluster_name = data.resourcePool.owner.name

        vm.host = None
        if data.runtime.host:
            vm.host = data.runtime.host

        vm.path = cur_path
        vm.template = data.summary.config.template
        vm.memory_mb = data.summary.config.memorySizeMB
        vm.num_cpu = data.summary.config.numCpu
        vm.num_ethernet = data.summary.config.numEthernetCards
        vm.num_vdisk = data.summary.config.numVirtualDisks
        vm.guest_fullname = data.summary.config.guestFullName
        vm.guest_id = data.summary.config.guestId
        vm.uuid = data.summary.config.uuid
        vm.instance_uuid = data.summary.config.instanceUuid
        vm.power_state = data.runtime.powerState

        if data.guest:

            vm.vm_tools = {}

            vm.vm_tools['install_type'] = None
            vm.vm_tools['state'] = None
            vm.vm_tools['version'] = data.guest.toolsVersion
            vm.vm_tools['version_state'] = None

            if hasattr(data.guest, 'toolsInstallType'):
                vm.vm_tools['install_type'] = data.guest.toolsInstallType

            if hasattr(data.guest, 'toolsRunningStatus'):
                vm.vm_tools['state'] = data.guest.toolsRunningStatus
            else:
                vm.vm_tools['state'] = data.guest.toolsStatus

            if hasattr(data.guest, 'toolsVersionStatus2'):
                vm.vm_tools['version_state'] = data.guest.toolsVersionStatus2
            else:
                vm.vm_tools['version_state'] = data.guest.toolsVersionStatus

        for device in data.config.hardware.device:
            if isinstance(device, vim.vm.device.VirtualDisk):
                disk = VsphereDisk.from_summary(
                    device, appname=appname, verbose=verbose, base_dir=base_dir)
                vm.disks.append(disk)

        if verbose > 2:
            LOG.debug(_("Created {} object:").format(cls.__name__) + '\n' + pp(vm.as_dict()))

        return vm


# =============================================================================
if __name__ == "__main__":

    pass

# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 list
