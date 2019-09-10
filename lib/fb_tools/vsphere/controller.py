#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: Frank Brehm
@contact: frank.brehm@pixelpark.com
@copyright: © 2019 by Frank Brehm, Berlin
@summary: The module for a VSphere disk controller object.
"""
from __future__ import absolute_import

# Standard modules
import logging
import uuid
import copy

try:
    from collections.abc import MutableSequence
except ImportError:
    from collections import MutableSequence

# Third party modules
from pyVmomi import vim

# Own modules
from ..xlate import XLATOR

from ..common import pp, to_bool

from ..obj import FbBaseObject

from .errors import VSphereNameError

__version__ = '0.2.0'
LOG = logging.getLogger(__name__)

_ = XLATOR.gettext


# =============================================================================
class VsphereDiskController(FbBaseObject):

    # -------------------------------------------------------------------------
    def __init__(
        self, appname=None, verbose=0, version=__version__, base_dir=None, initialized=None,
            ctrl_type=None, bus_nr=None, devices=None, hot_add_remove=False,
            scsi_ctrl_nr=None, sharing=None):

        self._ctrl_type = None
        self._bus_nr = None
        self.devices = []
        self._hot_add_remove = False
        self._scsi_ctrl_nr = None
        self._sharing = None

        super(VsphereDiskController, self).__init__(
            appname=appname, verbose=verbose, version=version, base_dir=base_dir, initialized=False)

        self.ctrl_type = ctrl_type
        self.bus_nr = bus_nr
        if devices:
            for dev_nr in devices:
                self.devices.append(int(dev_nr))
        self.hot_add_remove = hot_add_remove
        self.scsi_ctrl_nr = scsi_ctrl_nr
        self.sharing = sharing

        if initialized is not None:
            self.initialized = initialized

    # -----------------------------------------------------------
    @property
    def ctrl_type(self):
        """The type of this virtual disk controller."""
        return self._ctrl_type

    @ctrl_type.setter
    def ctrl_type(self, value):
        if value is None:
            self._ctrl_type = None
            return
        v = str(value).strip()
        if v == '':
            self._ctrl_type = None
            return
        self._ctrl_type = v

    # -----------------------------------------------------------
    @property
    def bus_nr(self):
        """Bus number associated with this controller."""
        return self._bus_nr

    @bus_nr.setter
    def bus_nr(self, value):
        if value is None:
            self._bus_nr = None
            return
        self._bus_nr = int(value)

    # -----------------------------------------------------------
    @property
    def hot_add_remove(self):
        """All SCSI controllers support hot adding and removing of devices."""
        return self._hot_add_remove

    @hot_add_remove.setter
    def hot_add_remove(self, value):
        self._hot_add_remove = to_bool(value)

    # -----------------------------------------------------------
    @property
    def scsi_ctrl_nr(self):
        """The unit number of the SCSI controller."""
        return self._scsi_ctrl_nr

    @scsi_ctrl_nr.setter
    def scsi_ctrl_nr(self, value):
        if value is None:
            self._scsi_ctrl_nr = None
            return
        self._scsi_ctrl_nr = int(value)

    # -----------------------------------------------------------
    @property
    def sharing(self):
        """Mode for sharing the SCSI bus."""
        return self._sharing

    @sharing.setter
    def sharing(self, value):
        if value is None:
            self._sharing = None
            return
        v = str(value).strip()
        if v == '':
            self._sharing = None
            return
        self._sharing = v

    # -------------------------------------------------------------------------
    def __eq__(self, other):

        if self.verbose > 4:
            LOG.debug(_("Comparing {} objects ...").format(self.__class__.__name__))

        if not isinstance(other, VsphereDiskController):
            return False

        if self.ctrl_type != other.ctrl_type:
            return False
        if self.bus_nr != other.bus_nr:
            return False
        if self.hot_add_remove != other.hot_add_remove:
            return False
        if self.scsi_ctrl_nr != other.scsi_ctrl_nr:
            return False

        return True

    # -------------------------------------------------------------------------
    def as_dict(self, short=True, bare=False):
        """
        Transforms the elements of the object into a dict

        @param short: don't include local properties in resulting dict.
        @type short: bool
        @param bare: don't include generic fields in returning dict
        @type bare: bool

        @return: structure as dict
        @rtype:  dict
        """

        if bare:
            res = {
                'ctrl_type': self.ctrl_type,
                'bus_nr': self.bus_nr,
                'hot_add_remove': self.hot_add_remove,
                'scsi_ctrl_nr': self.scsi_ctrl_nr,
                'sharing': self.sharing,
                'devices': copy.copy(self.devices),
            }
            return res

        res = super(VsphereDiskController, self).as_dict(short=short)
        res['ctrl_type'] = self.ctrl_type
        res['bus_nr'] = self.bus_nr
        res['hot_add_remove'] = self.hot_add_remove
        res['scsi_ctrl_nr'] = self.scsi_ctrl_nr
        res['sharing'] = self.sharing
        res['devices'] = copy.copy(self.devices),

        return res

    # -------------------------------------------------------------------------
    def __copy__(self):

        ctrl = VsphereDiskController(
            appname=self.appname, verbose=self.verbose, base_dir=self.base_dir,
            initialized=self.initialized, ctrl_type=self.ctrl_type, bus_nr=self.bus_nr,
            hot_add_remove=self.hot_add_remove, scsi_ctrl_nr=self.scsi_ctrl_nr,
            sharing=self.sharing, devices=self.devices)

        return ctrl

    # -------------------------------------------------------------------------
    @classmethod
    def from_summary(cls, data, appname=None, verbose=0, base_dir=None):

        if not isinstance(data, vim.vm.device.VirtualController):
            msg = _("Parameter {t!r} must be a {e}, {v!r} ({vt}) was given.").format(
                t='data', e='vim.vm.device.VirtualController', v=data, vt=data.__class__.__name__)
            raise TypeError(msg)

        params = {
            'appname': appname,
            'verbose': verbose,
            'base_dir': base_dir,
            'initialized': True,
            'bus_nr': data.busNumber,
            'devices' = [],
            'ctrl_type': 'unknown',
        }
        for disk_id in data.device:
            params['devices'].apprend(disk_id)
        if isinstance(data, vim.vm.device.VirtualSCSIController):
          params['hot_add_remove'] = data.hotAddRemove
          params['scsi_ctrl_nr'] = data.scsiCtlrUnitNumber
          params['sharing'] = data.sharedBus

        if verbose > 2:
            LOG.debug(_("Checking class of controller: {!r}").format(data.__class__.__name__))

        try:
            if isinstance(data, vim.vm.device.VirtualIDEController):
                params['ctrl_type'] = 'ide'
            elif isinstance(data, vim.vm.device.VirtualNVMEController):
                params['ctrl_type'] = 'nvme'
            elif isinstance(data, vim.vm.device.VirtualPCIController):
                params['ctrl_type'] = 'pci'
            elif isinstance(data, vim.vm.device.VirtualPS2Controller):
                params['ctrl_type'] = 'ps2'
            elif isinstance(data, vim.vm.device.VirtualAHCIController):
                params['ctrl_type'] = 'ahci'
            elif isinstance(data, vim.vm.device.VirtualSATAController):
                params['ctrl_type'] = 'sata'
            elif isinstance(data, vim.vm.device.VirtualSATAController):
                params['ctrl_type'] = 'sata'
            elif isinstance(data, vim.vm.device.ParaVirtualSCSIController):
                params['ctrl_type'] = 'para_virt_scsi'
            elif isinstance(data, vim.vm.device.VirtualBusLogicController):
                params['ctrl_type'] = 'bus_logic'
            elif isinstance(data, vim.vm.device.VirtualLsiLogicController):
                params['ctrl_type'] = 'lsi_logic'
            elif isinstance(data, vim.vm.device.VirtualLsiLogicSASController):
                params['ctrl_type'] = 'lsi_logic_sas'
            elif isinstance(data, vim.vm.device.VirtualSCSIController):
                params['ctrl_type'] = 'scsi'
            elif isinstance(data, vim.vm.device.VirtualSIOController):
                params['ctrl_type'] = 'sio'
            elif isinstance(data, vim.vm.device.VirtualUSBController):
                params['ctrl_type'] = 'usb'
            elif isinstance(data, vim.vm.device.VirtualUSBXHCIController):
                params['ctrl_type'] = 'usb_xhci'
        except Exception:
            pass

        if verbose > 2:
            LOG.debug(_("Creating {} object from:").format(cls.__name__) + '\n' + pp(params))

        ctrl = cls(**params)

        if verbose > 2:
            LOG.debug(_("Created {} object:").format(cls.__name__) + '\n' + pp(ctrl.as_dict()))

        return ctrl


# =============================================================================
class VsphereDiskControllerList(FbBaseObject, MutableSequence):
    """
    A list containing VsphereDiskController objects.
    """

    msg_no_controller = _("Invalid type {t!r} as an item of a {c}, only {o} objects are allowed.")

    # -------------------------------------------------------------------------
    def __init__(
        self, appname=None, verbose=0, version=__version__, base_dir=None,
            initialized=None, *ctrls):

        self._list = []

        super(VsphereDiskControllerList, self).__init__(
            appname=appname, verbose=verbose, version=version, base_dir=base_dir,
            initialized=False)

        for ctrl in ctrls:
            self.append(ctrl)

        if initialized is not None:
            self.initialized = initialized

    # -------------------------------------------------------------------------
    def as_dict(self, short=True, bare=False):
        """
        Transforms the elements of the object into a dict

        @param short: don't include local properties in resulting dict.
        @type short: bool
        @param bare: don't include generic fields in returning dict
        @type bare: bool

        @return: structure as dict or list
        @rtype:  dict or list
        """

        if bare:
            res = []
            for ctrl in self:
                res.append(ctrl.as_dict(bare=True))
            return res

        res = super(VsphereDiskControllerList, self).as_dict(short=short)
        res['_list'] = []

        for ctrl in self:
            res['_list'].append(ctrl.as_dict(short=short))

        return res

    # -------------------------------------------------------------------------
    def __copy__(self):

        new_list = VsphereDiskControllerList(
            appname=appname, verbose=verbose, base_dir=base_dir, initialized=False)

        for ctrl in self:
            new_list.append(ctrl)

        new_list.initialized = self.initialized
        return new_list

    # -------------------------------------------------------------------------
    def index(self, ctrl, *args):

        i = None
        j = None

        if len(args) > 0:
            if len(args) > 2:
                raise TypeError(_("{m} takes at most {max} arguments ({n} given).").format(
                    m='index()', max=3, n=len(args) + 1))
            i = int(args[0])
            if len(args) > 1:
                j = int(args[1])

        index = 0
        if i is not None:
            start = i
            if i < 0:
                start = len(self._list) + i

        wrap = False
        end = len(self._list)
        if j is not None:
            if j < 0:
                end = len(self._list) + j
                if end < index:
                    wrap = True
            else:
                end = j
        for index in list(range(len(self._list))):
            item = self._list[index]
            if index < start:
                continue
            if index >= end and not wrap:
                break
            if item == ctrl:
                return index

        if wrap:
            for index in list(range(len(self._list))):
                item = self._list[index]
                if index >= end:
                    break
            if item == ctrl:
                return index

        msg = _("Controller is not in controller list.")
        raise ValueError(msg)

    # -------------------------------------------------------------------------
    def __contains__(self, ctrl):

        if not isinstance(ctrl, VsphereDiskController):
            raise TypeError(self.msg_no_controller.format(
                t=ctrl.__class__.__name__, c=self.__class__.__name__, o='VsphereDiskController'))

        if not self._list:
            return False

        for item in self._list:
            if item == ctrl:
                return True

        return False

    # -------------------------------------------------------------------------
    def count(self, ctrl):

        if not isinstance(ctrl, VsphereDiskController):
            raise TypeError(self.msg_no_controller.format(
                t=ctrl.__class__.__name__, c=self.__class__.__name__, o='VsphereDiskController'))

        if not self._list:
            return 0

        num = 0
        for item in self._list:
            if item == ctrl:
                num += 1
        return num

    # -------------------------------------------------------------------------
    def __len__(self):
        return len(self._list)

    # -------------------------------------------------------------------------
    def __getitem__(self, key):
        return self._list.__getitem__(key)

    # -------------------------------------------------------------------------
    def __reversed__(self):

        return reversed(self._list)

    # -------------------------------------------------------------------------
    def __setitem__(self, key, ctrl):

        if not isinstance(ctrl, VsphereDiskController):
            raise TypeError(self.msg_no_controller.format(
                t=ctrl.__class__.__name__, c=self.__class__.__name__, o='VsphereDiskController'))

        self._list.__setitem__(key, ctrl)

    # -------------------------------------------------------------------------
    def __delitem__(self, key):

        del self._list[key]

    # -------------------------------------------------------------------------
    def append(self, ctrl):

        if not isinstance(ctrl, VsphereDiskController):
            raise TypeError(self.msg_no_controller.format(
                t=ctrl.__class__.__name__, c=self.__class__.__name__, o='VsphereDiskController'))

        self._list.append(ctrl)

    # -------------------------------------------------------------------------
    def insert(self, index, ctrl):

        if not isinstance(ctrl, VsphereDiskController):
            raise TypeError(self.msg_no_controller.format(
                t=ctrl.__class__.__name__, c=self.__class__.__name__, o='VsphereDiskController'))

        self._list.insert(index, ctrl)

    # -------------------------------------------------------------------------
    def __copy__(self):

        new_list = self.__class__()
        for ctrl in self._list:
            new_list.append(copy.copy(ctrl))
        return new_list

    # -------------------------------------------------------------------------
    def clear(self):
        "Remove all items from the VsphereDiskControllerList."

        self._list = []


# =============================================================================
if __name__ == "__main__":

    pass

# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 list
