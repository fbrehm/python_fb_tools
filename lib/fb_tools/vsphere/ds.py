#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: Frank Brehm
@contact: frank.brehm@pixelpark.com
@copyright: © 2018 by Frank Brehm, Berlin
@summary: The module for a VSphere datastore object.
"""
from __future__ import absolute_import

# Standard modules
import logging
import collections
import random
import re

# Third party modules
from pyVmomi import vim

# Own modules
from ..common import pp

from .object import VsphereObject


__version__ = '0.4.4'
LOG = logging.getLogger(__name__)


# =============================================================================
class VsphereDatastore(VsphereObject):

    re_is_nfs = re.compile(r'(?:share[_-]*nfs|nfs[_-]*share)', re.IGNORECASE)
    re_vmcb_fs = re.compile(r'vmcb-\d+-fc-\d+', re.IGNORECASE)
    re_local_ds = re.compile(r'^local_', re.IGNORECASE)

    # -------------------------------------------------------------------------
    def __init__(
        self, appname=None, verbose=0, version=__version__, base_dir=None, initialized=None,
            name=None, accessible=True, capacity=None, free_space=None, maintenance_mode=None,
            multiple_host_access=True, fs_type=None, uncommitted=None, url=None):

        self.repr_fields = (
            'name', 'accessible', 'capacity', 'free_space', 'fs_type', 'storage_type',
            'appname', 'verbose', 'version')

        self._accessible = bool(accessible)
        self._capacity = int(capacity)
        self._free_space = int(free_space)
        self._maintenance_mode = 'normal'
        if maintenance_mode is not None:
            self._maintenance_mode = str(maintenance_mode)
        self._multiple_host_access = bool(multiple_host_access)
        self._fs_type = 'unknown'
        if fs_type is not None:
            self._fs_type = fs_type
        self._uncommitted = 0
        if uncommitted is not None:
            self._uncommitted = int(uncommitted)
        self._url = None
        if url is not None:
            self._url = str(url)

        self._storage_type = 'unknown'

        self._calculated_usage = 0.0

        super(VsphereDatastore, self).__init__(
            name=name, obj_type='vsphere_datastore', name_prefix="ds",
            appname=appname, verbose=verbose, version=version, base_dir=base_dir)

        st_type = self.storage_type_by_name(self.name)
        if st_type:
            self._storage_type = st_type

        if initialized is not None:
            self.initialized = initialized

    # -----------------------------------------------------------
    @property
    def accessible(self):
        """The connectivity status of this datastore."""
        return self._accessible

    # -----------------------------------------------------------
    @property
    def capacity(self):
        """Maximum capacity of this datastore, in bytes."""
        return self._capacity

    # -----------------------------------------------------------
    @property
    def capacity_gb(self):
        """Maximum capacity of this datastore, in GiBytes."""
        return float(self.capacity) / 1024.0 / 1024.0 / 1024.0

    # -----------------------------------------------------------
    @property
    def free_space(self):
        """Available space of this datastore, in bytes."""
        return self._free_space

    # -----------------------------------------------------------
    @property
    def free_space_gb(self):
        """Available space of this datastore, in GiBytes."""
        return float(self._free_space) / 1024.0 / 1024.0 / 1024.0

    # -----------------------------------------------------------
    @property
    def maintenance_mode(self):
        """The current maintenance mode state of the datastore."""
        return self._maintenance_mode

    # -----------------------------------------------------------
    @property
    def multiple_host_access(self):
        """More than one host in the datacenter has been configured
            with access to the datastore."""
        return self._multiple_host_access

    # -----------------------------------------------------------
    @property
    def fs_type(self):
        """Type of file system volume, such as VMFS or NFS."""
        return self._fs_type

    # -----------------------------------------------------------
    @property
    def uncommitted(self):
        """Total additional storage space, in bytes,
            potentially used by all virtual machines on this datastore."""
        return self._uncommitted

    # -----------------------------------------------------------
    @property
    def uncommitted_gb(self):
        """Total additional storage space, in GiBytes,
            potentially used by all virtual machines on this datastore."""
        return float(self._uncommitted) / 1024.0 / 1024.0 / 1024.0

    # -----------------------------------------------------------
    @property
    def url(self):
        """The unique locator for the datastore."""
        return self._url

    # -----------------------------------------------------------
    @property
    def storage_type(self):
        """Type of storage volume, such as SAS or SATA or SSD."""
        return self._storage_type

    # -----------------------------------------------------------
    @property
    def calculated_usage(self):
        """The calculated additional usage of this datastore, in GiBytes."""
        return self._calculated_usage

    @calculated_usage.setter
    def calculated_usage(self, value):
        val = float(value)
        self._calculated_usage = val

    # -----------------------------------------------------------
    @property
    def avail_space_gb(self):
        """Available space of datastore in GiB in respect of calculated space."""
        if not self.free_space:
            return 0.0
        if not self.calculated_usage:
            return self.free_space_gb
        return self.free_space_gb - self.calculated_usage

    # -------------------------------------------------------------------------
    @classmethod
    def from_summary(cls, summary, appname=None, verbose=0, base_dir=None):

        if not isinstance(summary, vim.Datastore.Summary):
            msg = "Argument {!r} is not a datastore summary.".format(summary)
            raise TypeError(msg)

        params = {
            'appname': appname,
            'verbose': verbose,
            'base_dir': base_dir,
            'initialized': True,
            'capacity': summary.capacity,
            'free_space': summary.freeSpace,
            'name': summary.name,
            'fs_type': summary.type,
            'url': summary.url,
        }

        if hasattr(summary, 'accessible'):
            params['accessible'] = summary.accessible

        if hasattr(summary, 'maintenanceMode'):
            params['maintenance_mode'] = summary.maintenanceMode

        if hasattr(summary, 'multipleHostAccess'):
            params['multiple_host_access'] = summary.multipleHostAccess

        if hasattr(summary, 'uncommitted'):
            params['uncommitted'] = summary.uncommitted

        if verbose > 2:
            LOG.debug("Creating {c} object from:\n{p}".format(
                c=cls.__name__, p=pp(params)))

        ds = cls(**params)
        return ds

    # -------------------------------------------------------------------------
    @classmethod
    def storage_type_by_name(cls, name):
        """Trying to guess the storage type by its name.
            May be overridden in descentant classes."""

        if cls.re_is_nfs.search(name):
            return 'NFS'

        if '-sas-' in name.lower():
            return 'SAS'

        if '-ssd-' in name.lower():
            return  'SSD'

        if '-sata-' in name.lower():
            return 'SATA'

        if cls.re_vmcb_fs.search(name):
            return 'SATA'

        if cls.re_local_ds.search(name):
            return 'LOCAL'

        return None

    # -------------------------------------------------------------------------
    def as_dict(self, short=True):
        """
        Transforms the elements of the object into a dict

        @param short: don't include local properties in resulting dict.
        @type short: bool

        @return: structure as dict
        @rtype:  dict
        """

        res = super(VsphereDatastore, self).as_dict(short=short)
        res['accessible'] = self.accessible
        res['capacity'] = self.capacity
        res['capacity_gb'] = self.capacity_gb
        res['free_space'] = self.free_space
        res['free_space_gb'] = self.free_space_gb
        res['maintenance_mode'] = self.maintenance_mode
        res['multiple_host_access'] = self.multiple_host_access
        res['fs_type'] = self.fs_type
        res['uncommitted'] = self.uncommitted
        res['uncommitted_gb'] = self.uncommitted_gb
        res['url'] = self.url
        res['storage_type'] = self.storage_type
        res['calculated_usage'] = self.calculated_usage
        res['avail_space_gb'] = self.avail_space_gb

        return res

    # -------------------------------------------------------------------------
    def __copy__(self):

        return VsphereDatastore(
            appname=self.appname, verbose=self.verbose, base_dir=self.base_dir,
            initialized=self.initialized, name=self.name, accessible=self.accessible,
            capacity=self.capacity, free_space=self.free_space,
            maintenance_mode=self.maintenance_mode, multiple_host_access=self.multiple_host_access,
            fs_type=self.fs_type, uncommitted=self.uncommitted, url=self.url)

    # -------------------------------------------------------------------------
    def __eq__(self, other):

        if self.verbose > 4:
            LOG.debug("Comparing {}-objects ...".format(self.__class__.__name__))

        if not isinstance(other, VsphereDatastore):
            return False

        if self.name != other.name:
            return False

        return True


# =============================================================================
class VsphereDatastoreDict(collections.MutableMapping):
    """
    A dictionary containing VsphereDatastore objects.
    It works like a dict.
    """

    msg_invalid_ds_type = "Invalid value type {!r} to set, only VsphereDatastore allowed."
    msg_key_not_name = "The key {k!r} must be equal to the datastore name {n!r}."
    msg_none_type_error = "None type as key is not allowed."
    msg_empty_key_error = "Empty key {!r} is not allowed."
    msg_no_ds_dict = "Object {!r} is not a VsphereDatastoreDict object."

    # -------------------------------------------------------------------------
    def __init__(self, *args, **kwargs):
        '''Use the object dict'''
        self._map = dict()

        for arg in args:
            self.append(arg)

    # -------------------------------------------------------------------------
    def _set_item(self, key, ds):

        if not isinstance(ds, VsphereDatastore):
            raise TypeError(self.msg_invalid_ds_type.format(ds.__class__.__name__))

        ds_name = ds.name
        if ds_name != key:
            raise KeyError(self.msg_key_not_name.format(k=key, n=ds_name))

        self._map[ds_name] = ds

    # -------------------------------------------------------------------------
    def append(self, ds):

        if not isinstance(ds, VsphereDatastore):
            raise TypeError(self.msg_invalid_ds_type.format(ds.__class__.__name__))
        self._set_item(ds.name, ds)

    # -------------------------------------------------------------------------
    def _get_item(self, key):

        if key is None:
            raise TypeError(self.msg_none_type_error)

        ds_name = str(key).strip()
        if ds_name == '':
            raise ValueError(self.msg_empty_key_error.format(key))

        return self._map[ds_name]

    # -------------------------------------------------------------------------
    def get(self, key):
        return self._get_item(key)

    # -------------------------------------------------------------------------
    def _del_item(self, key, strict=True):

        if key is None:
            raise TypeError(self.msg_none_type_error)

        ds_name = str(key).strip()
        if ds_name == '':
            raise ValueError(self.msg_empty_key_error.format(key))

        if not strict and ds_name not in self._map:
            return

        del self._map[ds_name]

    # -------------------------------------------------------------------------
    # The next five methods are requirements of the ABC.
    def __setitem__(self, key, value):
        self._set_item(key, value)

    # -------------------------------------------------------------------------
    def __getitem__(self, key):
        return self._get_item(key)

    # -------------------------------------------------------------------------
    def __delitem__(self, key):
        self._del_item(key)

    # -------------------------------------------------------------------------
    def __iter__(self):

        for ds_name in self.keys():
            yield ds_name

    # -------------------------------------------------------------------------
    def __len__(self):
        return len(self._map)

    # -------------------------------------------------------------------------
    # The next methods aren't required, but nice for different purposes:
    def __str__(self):
        '''returns simple dict representation of the mapping'''
        return str(self._map)

    # -------------------------------------------------------------------------
    def __repr__(self):
        '''echoes class, id, & reproducible representation in the REPL'''
        return '{}, {}({})'.format(
            super(VsphereDatastoreDict, self).__repr__(),
            self.__class__.__name__,
            self._map)

    # -------------------------------------------------------------------------
    def __contains__(self, key):
        if key is None:
            raise TypeError(self.msg_none_type_error)

        ds_name = str(key).strip()
        if ds_name == '':
            raise ValueError(self.msg_empty_key_error.format(key))

        return ds_name in self._map

    # -------------------------------------------------------------------------
    def keys(self):

        return sorted(self._map.keys(), key=str.lower)

    # -------------------------------------------------------------------------
    def items(self):

        item_list = []

        for ds_name in self.keys():
            item_list.append((ds_name, self._map[ds_name]))

        return item_list

    # -------------------------------------------------------------------------
    def values(self):

        value_list = []
        for ds_name in self.keys():
            value_list.append(self._map[ds_name])
        return value_list

    # -------------------------------------------------------------------------
    def __eq__(self, other):

        if not isinstance(other, VsphereDatastoreDict):
            raise TypeError(self.msg_no_ds_dict.format(other))

        return self._map == other._map

    # -------------------------------------------------------------------------
    def __ne__(self, other):

        if not isinstance(other, VsphereDatastoreDict):
            raise TypeError(self.msg_no_ds_dict.format(other))

        return self._map != other._map

    # -------------------------------------------------------------------------
    def pop(self, key, *args):

        if key is None:
            raise TypeError(self.msg_none_type_error)

        ds_name = str(key).strip()
        if ds_name == '':
            raise ValueError(self.msg_empty_key_error.format(key))

        return self._map.pop(ds_name, *args)

    # -------------------------------------------------------------------------
    def popitem(self):

        if not len(self._map):
            return None

        ds_name = self.keys()[0]
        ds = self._map[ds_name]
        del self._map[ds_name]
        return (ds_name, ds)

    # -------------------------------------------------------------------------
    def clear(self):
        self._map = dict()

    # -------------------------------------------------------------------------
    def setdefault(self, key, default):

        if key is None:
            raise TypeError(self.msg_none_type_error)

        ds_name = str(key).strip()
        if ds_name == '':
            raise ValueError(self.msg_empty_key_error.format(key))

        if not isinstance(default, VsphereDatastore):
            raise TypeError(self.msg_invalid_ds_type.format(default.__class__.__name__))

        if ds_name in self._map:
            return self._map[ds_name]

        self._set_item(ds_name, default)
        return default

    # -------------------------------------------------------------------------
    def update(self, other):

        if isinstance(other, VsphereDatastoreDict) or isinstance(other, dict):
            for ds_name in other.keys():
                self._set_item(ds_name, other[ds_name])
            return

        for tokens in other:
            key = tokens[0]
            value = tokens[1]
            self._set_item(key, value)

    # -------------------------------------------------------------------------
    def as_dict(self, short=True):

        res = {}
        for ds_name in self._map:
            res[ds_name] = self._map[ds_name].as_dict(short)
        return res

    # -------------------------------------------------------------------------
    def as_list(self, short=True):

        res = []
        for ds_name in self.keys():
            res.append(self._map[ds_name].as_dict(short))
        return res

    # -------------------------------------------------------------------------
    def find_ds(self, needed_gb, ds_type='sata', reserve_space=True):

        search_chains = {
            'sata': ('sata', 'sas', 'ssd'),
            'sas': ('sas', 'sata', 'ssd'),
            'ssd': ('ssd', 'sas', 'sata'),
        }

        if ds_type not in search_chains:
            raise ValueError("Could not handle datastore type {!r}.".format(ds_type))
        for dstp in search_chains[ds_type]:
            ds_name = self._find_ds(needed_gb, dstp, reserve_space)
            if ds_name:
                return ds_name

        LOG.error("Could not found a datastore for {c:0.1f} GiB of type {t!r}.".format(
            c=needed_gb, t=ds_type))
        return None

    # -------------------------------------------------------------------------
    def _find_ds(self, needed_gb, ds_type, reserve_space=True):

        LOG.debug("Searching datastore for {c:0.1f} GiB of type {t!r}.".format(
            c=needed_gb, t=ds_type))

        avail_ds_names = []
        for (ds_name, ds) in self.items():
            if ds.storage_type.lower() != ds_type.lower():
                continue
            if ds.avail_space_gb >= needed_gb:
                avail_ds_names.append(ds_name)

        if not avail_ds_names:
            return None

        ds_name = random.choice(avail_ds_names)
        if reserve_space:
            ds = self[ds_name]
            ds.calculated_usage += needed_gb

        return ds_name


# =============================================================================
if __name__ == "__main__":

    pass

# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 list
