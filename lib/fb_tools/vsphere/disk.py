#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: Frank Brehm
@contact: frank.brehm@pixelpark.com
@copyright: © 2019 by Frank Brehm, Berlin
@summary: The module for a VSphere disk object.
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

from ..common import pp

from ..obj import FbBaseObject

from .errors import VSphereNameError


__version__ = '0.2.2'
LOG = logging.getLogger(__name__)

_ = XLATOR.gettext


# =============================================================================
class VsphereDisk(FbBaseObject):

    # -------------------------------------------------------------------------
    def __init__(
        self, appname=None, verbose=0, version=__version__, base_dir=None, initialized=None,
            uuid=None, file_name=None, unit_nr=None, label=None, key=None, controller_key=None,
            size=None, disk_id=None, summary=None):

        # self.repr_fields = (
        #     'uuid', 'file_name', 'unit_nr', 'label', 'key', 'controller_key',
        #     'size', 'disk_id', 'appname', 'verbose')

        self._uuid = None
        self._file_name = None
        self._unit_nr = None
        self._label = None
        self._summary = None
        self._key = None
        self._controller_key = None
        self._size = None
        self._disk_id = None

        super(VsphereDisk, self).__init__(
            appname=appname, verbose=verbose, version=version, base_dir=base_dir, initialized=False)

        self.uuid = uuid
        self.file_name = file_name
        self.unit_nr = unit_nr
        self.label = label
        self.summary = summary
        self.key = key
        self.controller_key = controller_key
        self.size = size
        self.disk_id = disk_id

        if initialized is not None:
            self.initialized = initialized

    # -----------------------------------------------------------
    @property
    def uuid(self):
        """The UUID of the disk."""
        return self._uuid

    @uuid.setter
    def uuid(self, value):
        if value is None:
            self._uuid = None
            return
        v = str(value).strip()
        if v == '':
            self._uuid = None
            return
        try:
            self._uuid = uuid.UUID(v)
        except Exception:
            self._uuid = v

    # -----------------------------------------------------------
    @property
    def file_name(self):
        """The name of the backing device on the host system."""
        return self._file_name

    @file_name.setter
    def file_name(self, value):
        if value is None:
            self._file_name = None
            return
        v = str(value).strip()
        if v == '':
            self._file_name = None
            return
        self._file_name = v

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
    def label(self):
        """The display label of the disk."""
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

    # -----------------------------------------------------------
    @property
    def summary(self):
        """A summary description of the disk."""
        return self._summary

    @summary.setter
    def summary(self, value):
        if value is None:
            self._summary = None
            return
        v = str(value).strip()
        if v == '':
            self._summary = None
            return
        self._summary = v

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
    def size(self):
        """The size of the disk in Bytes."""
        return self._size

    @size.setter
    def size(self, value):
        if value is None:
            self._size = None
            return
        self._size = int(value)

    # -----------------------------------------------------------
    @property
    def size_kb(self):
        """The size of the disk in KiBytes."""
        if self.size is None:
            return None
        return int(self.size / 1024)

    # -----------------------------------------------------------
    @property
    def size_mb(self):
        """The size of the disk in MiBytes."""
        if self.size is None:
            return None
        return int(self.size / 1024 / 1024)

    # -----------------------------------------------------------
    @property
    def size_gb(self):
        """The size of the disk in GiBytes as a float value."""
        if self.size_mb is None:
            return None
        return float(self.size_mb) / 1024.0

    # -----------------------------------------------------------
    @property
    def controller_key(self):
        """Object key for the controller object for this device."""
        return self._controller_key

    @controller_key.setter
    def controller_key(self, value):
        if value is None:
            self._controller_key = None
            return
        self._controller_key = int(value)

    # -----------------------------------------------------------
    @property
    def disk_id(self):
        """TODO whatever."""
        return self._disk_id

    @disk_id.setter
    def disk_id(self, value):
        if value is None:
            self._disk_id = None
            return
        v = str(value).strip()
        if v == '':
            self._disk_id = None
            return
        self._disk_id = v

    # -------------------------------------------------------------------------
    def __eq__(self, other):

        if self.verbose > 4:
            LOG.debug(_("Comparing {} objects ...").format(self.__class__.__name__))

        if not isinstance(other, VsphereDisk):
            return False

        if self.uuid != other.uuid:
            return False
        if self.file_name != other.file_name:
            return False
        if self.unit_nr != other.unit_nr:
            return False
        if self.label != other.label:
            return False
        if self.summary != other.summary:
            return False
        if self.key != other.key:
            return False
        if self.size != other.size:
            return False
        if self.controller_key != other.controller_key:
            return False
        if self.disk_id != other.disk_id:
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

        res = super(VsphereDisk, self).as_dict(short=short)
        res['uuid'] = self.uuid
        res['file_name'] = self.file_name
        res['unit_nr'] = self.unit_nr
        res['label'] = self.label
        res['summary'] = self.summary
        res['key'] = self.key
        res['size'] = self.size
        res['size_kb'] = self.size_kb
        res['size_mb'] = self.size_mb
        res['size_gb'] = self.size_gb
        res['controller_key'] = self.controller_key
        res['disk_id'] = self.disk_id

        return res

    # -------------------------------------------------------------------------
    def __copy__(self):

        disk = VsphereDisk(
            appname=self.appname, verbose=self.verbose, base_dir=self.base_dir,
            initialized=self.initialized, uuid=self.uuid, file_name=self.file_name,
            unit_nr=self.unit_nr, label=self.label, key=self.key, size=self.size,
            controller_key=self.controller_key, disk_id=self.disk_id, summary=self.summary)

        return disk

    # -------------------------------------------------------------------------
    @classmethod
    def from_summary(cls, data, appname=None, verbose=0, base_dir=None):

        if not isinstance(data, vim.vm.device.VirtualDisk):
            msg = _("Parameter {t!r} must be a {e}, {v!r} ({vt}) was given.").format(
                t='data', e='vim.vm.device.VirtualDisk', v=data, vt=data.__class__.__name__)
            raise TypeError(msg)

        params = {
            'appname': appname,
            'verbose': verbose,
            'base_dir': base_dir,
            'initialized': True,
            'unit_nr': data.unitNumber,
            'label': data.deviceInfo.label,
            'summary': data.deviceInfo.summary,
            'size': data.capacityInBytes,
            'key': data.key,
            'file_name': data.backing.fileName,
            'controller_key': data.controllerKey,
            'disk_id': data.vDiskId,
        }

        if verbose > 2:
            LOG.debug(_("Creating {} object from:").format(cls.__name__) + '\n' + pp(params))

        disk = cls(**params)

        if verbose > 2:
            LOG.debug(_("Created {} object:").format(cls.__name__) + '\n' + pp(disk.as_dict()))

        return disk


# =============================================================================
class VsphereDiskList(FbBaseObject, MutableSequence):
    """
    A list containing VsphereDisk objects.
    """

    msg_no_disk = _("Invalid type {t!r} as an item of a {c}, only {o} objects are allowed.")

    # -------------------------------------------------------------------------
    def __init__(
        self, appname=None, verbose=0, version=__version__, base_dir=None,
            initialized=None, *disks):

        self._list = []

        super(VsphereDiskList, self).__init__(
            appname=appname, verbose=verbose, version=version, base_dir=base_dir,
            initialized=False)

        for disk in disks:
            self.append(disk)

        if initialized is not None:
            self.initialized = initialized

    # -------------------------------------------------------------------------
    def as_dict(self, short=True):
        """
        Transforms the elements of the object into a dict

        @param short: don't include local properties in resulting dict.
        @type short: bool

        @return: structure as dict
        @rtype:  dict
        """

        res = super(VsphereDiskList, self).as_dict(short=short)
        res['_list'] = []

        for disk in self:
            res['_list'].append(disk.as_dict(short=short))

        return res

    # -------------------------------------------------------------------------
    def __copy__(self):

        new_list = VsphereDiskList(
            appname=appname, verbose=verbose, base_dir=base_dir, initialized=False)

        for disk in self:
            new_list.append(disk)

        new_list.initialized = self.initialized
        return new_list

    # -------------------------------------------------------------------------
    def index(self, disk, *args):

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
            if item == disk:
                return index

        if wrap:
            for index in list(range(len(self._list))):
                item = self._list[index]
                if index >= end:
                    break
            if item == disk:
                return index

        msg = _("Disk is not in disk list.")
        raise ValueError(msg)

    # -------------------------------------------------------------------------
    def __contains__(self, disk):

        if not isinstance(disk, VsphereDisk):
            raise TypeError(self.msg_no_disk.format(
                t=disk.__class__.__name__, c=self.__class__.__name__, o='VsphereDisk'))

        if not self._list:
            return False

        for item in self._list:
            if item == disk:
                return True

        return False

    # -------------------------------------------------------------------------
    def count(self, disk):

        if not isinstance(disk, VsphereDisk):
            raise TypeError(self.msg_no_disk.format(
                t=disk.__class__.__name__, c=self.__class__.__name__, o='VsphereDisk'))

        if not self._list:
            return 0

        num = 0
        for item in self._list:
            if item == disk:
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
    def __setitem__(self, key, disk):

        if not isinstance(disk, VsphereDisk):
            raise TypeError(self.msg_no_disk.format(
                t=disk.__class__.__name__, c=self.__class__.__name__, o='VsphereDisk'))

        self._list.__setitem__(key, disk)

    # -------------------------------------------------------------------------
    def __delitem__(self, key):

        del self._list[key]

    # -------------------------------------------------------------------------
    def append(self, disk):

        if not isinstance(disk, VsphereDisk):
            raise TypeError(self.msg_no_disk.format(
                t=disk.__class__.__name__, c=self.__class__.__name__, o='VsphereDisk'))

        self._list.append(disk)

    # -------------------------------------------------------------------------
    def insert(self, index, disk):

        if not isinstance(disk, VsphereDisk):
            raise TypeError(self.msg_no_disk.format(
                t=disk.__class__.__name__, c=self.__class__.__name__, o='VsphereDisk'))

        self._list.insert(index, disk)

    # -------------------------------------------------------------------------
    def __copy__(self):

        new_list = self.__class__()
        for disk in self._list:
            new_list.append(copy.copy(disk))
        return new_list

    # -------------------------------------------------------------------------
    def clear(self):
        "Remove all items from the VsphereDiskList."

        self._list = []


# =============================================================================
if __name__ == "__main__":

    pass

# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 list
