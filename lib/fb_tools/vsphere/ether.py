#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: Frank Brehm
@contact: frank.brehm@pixelpark.com
@copyright: © 2019 by Frank Brehm, Berlin
@summary: The module for a VSphere ethernet card object.
"""
from __future__ import absolute_import

# Standard modules
import logging
import uuid

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


__version__ = '0.1.2'
LOG = logging.getLogger(__name__)

_ = XLATOR.gettext


# =============================================================================
class VsphereEthernetcard(FbBaseObject):

    # -------------------------------------------------------------------------
    def __init__(
        self, appname=None, verbose=0, version=__version__, base_dir=None, initialized=None,
            unit_nr=None, key=None, address_type=None, external_id=None, mac_address=None,
            wake_on_lan=False, backing_device=None, backing_type=None, connected=False,
            connect_status=None, connect_on_start=False, allow_guest_control=False,
            ether_type=None, label=None):

        self._unit_nr = None
        self._key = None
        self._address_type = None
        self._external_id = None
        self._mac_address = None
        self._wake_on_lan = False
        self._backing_device = None
        self._backing_type = None
        self._connected = False
        self._connect_status = None
        self._connect_on_start = False
        self._allow_guest_control = False
        self._ether_type = None
        self._label = None

        super(VsphereEthernetcard, self).__init__(
            appname=appname, verbose=verbose, version=version, base_dir=base_dir, initialized=False)

        self.unit_nr = unit_nr
        self.key = key
        self.address_type = address_type
        self.external_id = external_id
        self.mac_address = mac_address
        self.wake_on_lan = wake_on_lan
        self.backing_device = backing_device
        self.backing_type = backing_type
        self.connected = connected
        self.connect_status = connect_status
        self.connect_on_start = connect_on_start
        self.allow_guest_control = allow_guest_control
        self.ether_type = ether_type
        self.label = label

        if initialized is not None:
            self.initialized = initialized

    # -----------------------------------------------------------
    @property
    def unit_nr(self):
        """The unit number of this device on its controller.
            This property is None if the controller property is None
            (for example, when the device is not attached to a specific controller object)."""
        return self._unit_nr

    @unit_nr.setter
    def unit_nr(self, value):
        if value is None:
            self._unit_nr = None
            return
        self._unit_nr = int(value)

    # -----------------------------------------------------------
    @property
    def key(self):
        """A unique key that distinguishes this device from other devices
            in the same virtual machine."""
        return self._key

    @key.setter
    def key(self, value):
        if value is None:
            self._key = None
            return
        self._key = int(value)

    # -----------------------------------------------------------
    @property
    def address_type(self):
        """MAC address type - Manual, Generated or Assigned."""
        return self._address_type

    @address_type.setter
    def address_type(self, value):
        if value is None:
            self._address_type = None
            return
        v = str(value).strip()
        if v == '':
            self._address_type = None
            return
        self._address_type = v

    # -----------------------------------------------------------
    @property
    def external_id(self):
        """An ID assigned to the virtual network adapter by external
            management plane or controller."""
        return self._external_id

    @external_id.setter
    def external_id(self, value):
        if value is None:
            self._external_id = None
            return
        v = str(value).strip()
        if v == '':
            self._external_id = None
            return
        self._external_id = v

    # -----------------------------------------------------------
    @property
    def mac_address(self):
        """The MAC address of this virtual ethernet card."""
        return self._mac_address

    @mac_address.setter
    def mac_address(self, value):
        if value is None:
            self._mac_address = None
            return
        v = str(value).strip()
        if v == '':
            self._mac_address = None
            return
        self._mac_address = v

    # -----------------------------------------------------------
    @property
    def wake_on_lan(self):
        """Indicates whether wake-on-LAN is enabled on this virtual network adapter."""
        return self._wake_on_lan

    @wake_on_lan.setter
    def wake_on_lan(self, value):
        self._wake_on_lan = to_bool(value)

    # -----------------------------------------------------------
    @property
    def backing_device(self):
        """The name of the backing device of this virtual network adapter."""
        return self._backing_device

    @backing_device.setter
    def backing_device(self, value):
        if value is None:
            self._backing_device = None
            return
        v = str(value).strip()
        if v == '':
            self._backing_device = None
            return
        self._backing_device = v

    # -----------------------------------------------------------
    @property
    def backing_type(self):
        """The type of the backing device of this virtual network adapter."""
        return self._backing_type

    @backing_type.setter
    def backing_type(self, value):
        if value is None:
            self._backing_type = None
            return
        v = str(value).strip()
        if v == '':
            self._backing_type = None
            return
        self._backing_type = v

    # -----------------------------------------------------------
    @property
    def connected(self):
        """Indicates whether the device is currently connected."""
        return self._connected

    @connected.setter
    def connected(self, value):
        self._connected = to_bool(value)

    # -----------------------------------------------------------
    @property
    def connect_status(self):
        """Indicates the current status of the connectable device."""
        return self._connect_status

    @connect_status.setter
    def connect_status(self, value):
        if value is None:
            self._connect_status = None
            return
        v = str(value).strip()
        if v == '':
            self._connect_status = None
            return
        self._connect_status = v

    # -----------------------------------------------------------
    @property
    def connect_on_start(self):
        """Specifies whether or not to connect the device when the virtual machine starts."""
        return self._connect_on_start

    @connect_on_start.setter
    def connect_on_start(self, value):
        self._connect_on_start = to_bool(value)

    # -----------------------------------------------------------
    @property
    def allow_guest_control(self):
        """Enables guest control over whether the connectable device is connected."""
        return self._allow_guest_control

    @allow_guest_control.setter
    def allow_guest_control(self, value):
        self._allow_guest_control = to_bool(value)

    # -----------------------------------------------------------
    @property
    def ether_type(self):
        """The type of this virtual network adapter."""
        return self._ether_type

    @ether_type.setter
    def ether_type(self, value):
        if value is None:
            self._ether_type = None
            return
        v = str(value).strip()
        if v == '':
            self._ether_type = None
            return
        self._ether_type = v

    # -----------------------------------------------------------
    @property
    def label(self):
        """Display label of this virtual network adapter."""
        return self._label

    @label.setter
    def label(self, value):
        if value is None:
            self._label = None
            return
        v = str(value).strip()
        if v == '':
            self._label = None
            return
        self._label = v

    # -------------------------------------------------------------------------
    def __eq__(self, other):

        if self.verbose > 4:
            LOG.debug(_("Comparing {} objects ...").format(self.__class__.__name__))

        if not isinstance(other, VsphereEthernetcard):
            return False

        if self.unit_nr != other.unit_nr:
            return False
        if self.key != other.key:
            return False
        if self.address_type != other.address_type:
            return False
        if self.external_id != other.external_id:
            return False
        if self.mac_address != other.mac_address:
            return False
        if self.wake_on_lan != other.wake_on_lan:
            return False
        if self.backing_device != other.backing_device:
            return False
        if self.backing_type != other.backing_type:
            return False
        if self.connected != other.connected:
            return False
        if self.connect_status != other.connect_status:
            return False
        if self.connect_on_start != other.connect_on_start:
            return False
        if self.allow_guest_control != other.allow_guest_control:
            return False
        if self.ether_type != other.ether_type:
            return False
        if self.label != other.label:
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
                'unit_nr': self.unit_nr
                'key': self.key
                'address_type': self.address_type
                'external_id': self.external_id
                'mac_address': self.mac_address
                'wake_on_lan': self.wake_on_lan
                'backing_device': self.backing_device
                'backing_type': self.backing_type
                'connected': self.connected
                'connect_status': self.connect_status
                'connect_on_start': self.connect_on_start
                'allow_guest_control': self.allow_guest_control
                'ether_type': self.ether_type
                'label': self.label
            }
            return res

        res = super(VsphereEthernetcard, self).as_dict(short=short)
        res['unit_nr'] = self.unit_nr
        res['key'] = self.key
        res['address_type'] = self.address_type
        res['external_id'] = self.external_id
        res['mac_address'] = self.mac_address
        res['wake_on_lan'] = self.wake_on_lan
        res['backing_device'] = self.backing_device
        res['backing_type'] = self.backing_type
        res['connected'] = self.connected
        res['connect_status'] = self.connect_status
        res['connect_on_start'] = self.connect_on_start
        res['allow_guest_control'] = self.allow_guest_control
        res['ether_type'] = self.ether_type
        res['label'] = self.label

        return res

    # -------------------------------------------------------------------------
    def __copy__(self):

        card = VsphereEthernetcard(
            appname=self.appname, verbose=self.verbose, base_dir=self.base_dir,
            initialized=self.initialized, unit_nr=self.unit_nr, key=self.key,
            address_type=self.address_type, external_id=self.external_id,
            mac_address=self.mac_address, wake_on_lan=self.wake_on_lan,
            backing_device=self.backing_device, backing_type=self.backing_type,
            connected=self.connected, connect_status=self.connect_status,
            connect_on_start=self.connect_on_start, allow_guest_control=self.allow_guest_control,
            ether_type=self.ether_type, label=self.label)

        return card

    # -------------------------------------------------------------------------
    @classmethod
    def from_summary(cls, data, appname=None, verbose=0, base_dir=None):

        if not isinstance(data, vim.vm.device.VirtualEthernetCard):
            msg = _("Parameter {t!r} must be a {e}, {v!r} ({vt}) was given.").format(
                t='data', e='vim.vm.device.VirtualEthernetCard', v=data, vt=data.__class__.__name__)
            raise TypeError(msg)

        params = {
            'appname': appname,
            'verbose': verbose,
            'base_dir': base_dir,
            'initialized': True,
            'unit_nr': data.unitNumber,
            'key': data.key,
            'address_type': data.addressType,
            'external_id': data.externalId,
            'mac_address': data.macAddress,
            'wake_on_lan': data.wakeOnLanEnabled,
            'backing_device': data.backing.deviceName,
            'backing_type': data.backing.__class__.__name__,
            'connected': data.connectable.connected,
            'connect_status': data.connectable.status,
            'connect_on_start': data.connectable.startConnected,
            'allow_guest_control': data.connectable.allowGuestControl,
            'ether_type': 'unknown',
        }
        if data.deviceInfo:
            params['label'] = data.deviceInfo.label

        if verbose > 2:
            LOG.debug(_("Checking class of ethernet card: {!r}").format(data.__class__.__name__))

        try:
            if isinstance(data, vim.vm.device.VirtualE1000e):
                params['ether_type'] = 'e1000e'
            if isinstance(data, vim.vm.device.VirtualE1000):
                params['ether_type'] = 'e1000'
            elif isinstance(data, vim.vm.device.VirtualPCNet32):
                params['ether_type'] = 'pcnet32'
            elif isinstance(data, vim.vm.device.VirtualSriovEthernetCard):
                params['ether_type'] = 'sriov'
            elif isinstance(data, vim.vm.device.VirtualVmxnet2):
                params['ether_type'] = 'vmxnet2'
            elif isinstance(data, vim.vm.device.VirtualVmxnet3Vrdma):
                params['ether_type'] = 'vmxnet3_rdma'
            elif isinstance(data, vim.vm.device.VirtualVmxnet3):
                params['ether_type'] = 'vmxnet3'
            elif isinstance(data, vim.vm.device.VirtualVmxnet):
                params['ether_type'] = 'vmxnet'
        except Exception:
            pass

        if verbose > 2:
            LOG.debug(_("Creating {} object from:").format(cls.__name__) + '\n' + pp(params))

        card = cls(**params)

        if verbose > 2:
            LOG.debug(_("Created {} object:").format(cls.__name__) + '\n' + pp(card.as_dict()))

        return card


# =============================================================================
class VsphereEthernetcardList(FbBaseObject, MutableSequence):
    """
    A list containing VsphereEthernetcard objects.
    """

    msg_no_ether_card = _("Invalid type {t!r} as an item of a {c}, only {o} objects are allowed.")

    # -------------------------------------------------------------------------
    def __init__(
        self, appname=None, verbose=0, version=__version__, base_dir=None,
            initialized=None, *cards):

        self._list = []

        super(VsphereEthernetcardList, self).__init__(
            appname=appname, verbose=verbose, version=version, base_dir=base_dir,
            initialized=False)

        for card in cards:
            self.append(card)

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
            for card in self:
                res.append(card.as_dict(bare=True))
            return res

        res = super(VsphereEthernetcardList, self).as_dict(short=short)
        res['_list'] = []

        for card in self:
            res['_list'].append(card.as_dict(short=short))

        return res

    # -------------------------------------------------------------------------
    def __copy__(self):

        new_list = VsphereEthernetcardList(
            appname=appname, verbose=verbose, base_dir=base_dir, initialized=False)

        for card in self:
            new_list.append(card)

        new_list.initialized = self.initialized
        return new_list

    # -------------------------------------------------------------------------
    def index(self, card, *args):

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
            if item == card:
                return index

        if wrap:
            for index in list(range(len(self._list))):
                item = self._list[index]
                if index >= end:
                    break
            if item == card:
                return index

        msg = _("card is not in card list.")
        raise ValueError(msg)

    # -------------------------------------------------------------------------
    def __contains__(self, card):

        if not isinstance(card, VsphereEthernetcard):
            raise TypeError(self.msg_no_ether_card.format(
                t=card.__class__.__name__, c=self.__class__.__name__, o='VsphereEthernetcard'))

        if not self._list:
            return False

        for item in self._list:
            if item == card:
                return True

        return False

    # -------------------------------------------------------------------------
    def count(self, card):

        if not isinstance(card, VsphereEthernetcard):
            raise TypeError(self.msg_no_ether_card.format(
                t=card.__class__.__name__, c=self.__class__.__name__, o='VsphereEthernetcard'))

        if not self._list:
            return 0

        num = 0
        for item in self._list:
            if item == card:
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
    def __setitem__(self, key, card):

        if not isinstance(card, VsphereEthernetcard):
            raise TypeError(self.msg_no_ether_card.format(
                t=card.__class__.__name__, c=self.__class__.__name__, o='VsphereEthernetcard'))

        self._list.__setitem__(key, card)

    # -------------------------------------------------------------------------
    def __delitem__(self, key):

        del self._list[key]

    # -------------------------------------------------------------------------
    def append(self, card):

        if not isinstance(card, VsphereEthernetcard):
            raise TypeError(self.msg_no_ether_card.format(
                t=card.__class__.__name__, c=self.__class__.__name__, o='VsphereEthernetcard'))

        self._list.append(card)

    # -------------------------------------------------------------------------
    def insert(self, index, card):

        if not isinstance(card, VsphereEthernetcard):
            raise TypeError(self.msg_no_ether_card.format(
                t=card.__class__.__name__, c=self.__class__.__name__, o='VsphereEthernetcard'))

        self._list.insert(index, card)

    # -------------------------------------------------------------------------
    def __copy__(self):

        new_list = self.__class__()
        for card in self._list:
            new_list.append(copy.copy(card))
        return new_list

    # -------------------------------------------------------------------------
    def clear(self):
        "Remove all items from the VsphereEthernetcardList."

        self._list = []


# =============================================================================
if __name__ == "__main__":

    pass

# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 list
