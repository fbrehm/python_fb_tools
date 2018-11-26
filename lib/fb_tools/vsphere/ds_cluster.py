#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: Frank Brehm
@contact: frank.brehm@pixelpark.com
@copyright: © 2018 by Frank Brehm, Berlin
@summary: The module for a VSphere datastore cluster object.
"""
from __future__ import absolute_import

# Standard modules
import logging
import collections

# Third party modules
from pyVmomi import vim

# Own modules
from ..common import pp

from .object import VsphereObject


__version__ = '1.1.0'
LOG = logging.getLogger(__name__)


# =============================================================================
class VsphereDsCluster(VsphereObject):

    # -------------------------------------------------------------------------
    def __init__(
        self, appname=None, verbose=0, version=__version__, base_dir=None, initialized=None,
            name=None, status='gray', config_status='gray', capacity=None, free_space=None):

        self.repr_fields = (
            'name', 'status', 'config_status', 'capacity', 'free_space',
            'appname', 'verbose', 'version')

        self._capacity = int(capacity)
        self._free_space = int(free_space)

        self._calculated_usage = 0.0

        super(VsphereDsCluster, self).__init__(
            name=name, obj_type='vsphere_datastore_cluster', name_prefix="dspod",
            status=status, config_status=config_status,
            appname=appname, verbose=verbose, version=version, base_dir=base_dir)

        if initialized is not None:
            self.initialized = initialized

    # -----------------------------------------------------------
    @property
    def capacity(self):
        """Maximum capacity of this datastore cluster, in bytes."""
        return self._capacity

    # -----------------------------------------------------------
    @property
    def capacity_gb(self):
        """Maximum capacity of this datastore cluster, in GiBytes."""
        return float(self.capacity) / 1024.0 / 1024.0 / 1024.0

    # -----------------------------------------------------------
    @property
    def free_space(self):
        """Available space of this datastore cluster, in bytes."""
        return self._free_space

    # -----------------------------------------------------------
    @property
    def free_space_gb(self):
        """Available space of this datastore cluster, in GiBytes."""
        return float(self._free_space) / 1024.0 / 1024.0 / 1024.0

    # -----------------------------------------------------------
    @property
    def calculated_usage(self):
        """The calculated additional usage of this datastore cluster, in GiBytes."""
        return self._calculated_usage

    @calculated_usage.setter
    def calculated_usage(self, value):
        val = float(value)
        self._calculated_usage = val

    # -----------------------------------------------------------
    @property
    def avail_space_gb(self):
        """Available space of datastore cluster in GiB in respect of calculated space."""
        if not self.free_space:
            return 0.0
        if not self.calculated_usage:
            return self.free_space_gb
        return self.free_space_gb - self.calculated_usage

    # -------------------------------------------------------------------------
    @classmethod
    def from_summary(cls, data, appname=None, verbose=0, base_dir=None):

        if not isinstance(data, vim.StoragePod):
            msg = "Argument {!r} is not a VSphere datastore cluster.".format(data)
            raise TypeError(msg)

        params = {
            'appname': appname,
            'verbose': verbose,
            'base_dir': base_dir,
            'initialized': True,
            'capacity': data.summary.capacity,
            'free_space': data.summary.freeSpace,
            'name': data.summary.name,
            'status': data.overallStatus,
            'config_status': data.configStatus,
        }

        if verbose > 2:
            LOG.debug("Creating {c} object from:\n{p}".format(
                c=cls.__name__, p=pp(params)))

        cluster = cls(**params)
        return cluster

    # -------------------------------------------------------------------------
    def as_dict(self, short=True):
        """
        Transforms the elements of the object into a dict

        @param short: don't include local properties in resulting dict.
        @type short: bool

        @return: structure as dict
        @rtype:  dict
        """

        res = super(VsphereDsCluster, self).as_dict(short=short)
        res['capacity'] = self.capacity
        res['capacity_gb'] = self.capacity_gb
        res['free_space'] = self.free_space
        res['free_space_gb'] = self.free_space_gb
        res['calculated_usage'] = self.calculated_usage
        res['avail_space_gb'] = self.avail_space_gb

        return res

    # -------------------------------------------------------------------------
    def __copy__(self):

        return VsphereDsCluster(
            appname=self.appname, verbose=self.verbose, base_dir=self.base_dir,
            initialized=self.initialized, name=self.name, status=self.status,
            config_status=config_status, capacity=self.capacity, free_space=self.free_space,)

    # -------------------------------------------------------------------------
    def __eq__(self, other):

        if self.verbose > 4:
            LOG.debug("Comparing {}-objects ...".format(self.__class__.__name__))

        if not isinstance(other, VsphereDsCluster):
            return False

        if self.name != other.name:
            return False

        return True

# =============================================================================
class VsphereDsClusterDict(collections.MutableMapping):
    """
    A dictionary containing VsphereDsCluster objects.
    It works like a dict.
    """

    msg_invalid_cluster_type = "Invalid value type {!r} to set, only VsphereDsCluster allowed."
    msg_key_not_name = "The key {k!r} must be equal to the datastore cluster name {n!r}."
    msg_none_type_error = "None type as key is not allowed."
    msg_empty_key_error = "Empty key {!r} is not allowed."
    msg_no_cluster_dict = "Object {!r} is not a VsphereDsClusterDict object."

    # -------------------------------------------------------------------------
    def __init__(self, *args, **kwargs):
        '''Use the object dict'''
        self._map = dict()

        for arg in args:
            self.append(arg)

    # -------------------------------------------------------------------------
    def _set_item(self, key, cluster):

        if not isinstance(cluster, VsphereDsCluster):
            raise TypeError(self.msg_invalid_cluster_type.format(cluster.__class__.__name__))

        cluster_name = cluster.name
        if cluster_name != key:
            raise KeyError(self.msg_key_not_name.format(k=key, n=cluster_name))

        self._map[cluster_name] = cluster

    # -------------------------------------------------------------------------
    def append(self, cluster):

        if not isinstance(cluster, VsphereDsCluster):
            raise TypeError(self.msg_invalid_cluster_type.format(cluster.__class__.__name__))
        self._set_item(cluster.name, cluster)

    # -------------------------------------------------------------------------
    def _get_item(self, key):

        if key is None:
            raise TypeError(self.msg_none_type_error)

        cluster_name = str(key).strip()
        if cluster_name == '':
            raise ValueError(self.msg_empty_key_error.format(key))

        return self._map[cluster_name]

    # -------------------------------------------------------------------------
    def get(self, key):
        return self._get_item(key)

    # -------------------------------------------------------------------------
    def _del_item(self, key, strict=True):

        if key is None:
            raise TypeError(self.msg_none_type_error)

        cluster_name = str(key).strip()
        if cluster_name == '':
            raise ValueError(self.msg_empty_key_error.format(key))

        if not strict and cluster_name not in self._map:
            return

        del self._map[cluster_name]

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

        for cluster_name in self.keys():
            yield cluster_name

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
            super(VsphereDsClusterDict, self).__repr__(),
            self.__class__.__name__,
            self._map)

    # -------------------------------------------------------------------------
    def __contains__(self, key):
        if key is None:
            raise TypeError(self.msg_none_type_error)

        cluster_name = str(key).strip()
        if cluster_name == '':
            raise ValueError(self.msg_empty_key_error.format(key))

        return cluster_name in self._map

    # -------------------------------------------------------------------------
    def keys(self):

        return sorted(self._map.keys(), key=str.lower)

    # -------------------------------------------------------------------------
    def items(self):

        item_list = []

        for cluster_name in self.keys():
            item_list.append((cluster_name, self._map[cluster_name]))

        return item_list

    # -------------------------------------------------------------------------
    def values(self):

        value_list = []
        for cluster_name in self.keys():
            value_list.append(self._map[cluster_name])
        return value_list

    # -------------------------------------------------------------------------
    def __eq__(self, other):

        if not isinstance(other, VsphereDsClusterDict):
            raise TypeError(self.msg_no_cluster_dict.format(other))

        return self._map == other._map

    # -------------------------------------------------------------------------
    def __ne__(self, other):

        if not isinstance(other, VsphereDsClusterDict):
            raise TypeError(self.msg_no_cluster_dict.format(other))

        return self._map != other._map

    # -------------------------------------------------------------------------
    def pop(self, key, *args):

        if key is None:
            raise TypeError(self.msg_none_type_error)

        cluster_name = str(key).strip()
        if cluster_name == '':
            raise ValueError(self.msg_empty_key_error.format(key))

        return self._map.pop(cluster_name, *args)

    # -------------------------------------------------------------------------
    def popitem(self):

        if not len(self._map):
            return None

        cluster_name = self.keys()[0]
        cluster = self._map[cluster_name]
        del self._map[cluster_name]
        return (cluster_name, cluster)

    # -------------------------------------------------------------------------
    def clear(self):
        self._map = dict()

    # -------------------------------------------------------------------------
    def setdefault(self, key, default):

        if key is None:
            raise TypeError(self.msg_none_type_error)

        cluster_name = str(key).strip()
        if cluster_name == '':
            raise ValueError(self.msg_empty_key_error.format(key))

        if not isinstance(default, VsphereDsCluster):
            raise TypeError(self.msg_invalid_cluster_type.format(default.__class__.__name__))

        if cluster_name in self._map:
            return self._map[cluster_name]

        self._set_item(cluster_name, default)
        return default

    # -------------------------------------------------------------------------
    def update(self, other):

        if isinstance(other, VsphereDsClusterDict) or isinstance(other, dict):
            for cluster_name in other.keys():
                self._set_item(cluster_name, other[cluster_name])
            return

        for tokens in other:
            key = tokens[0]
            value = tokens[1]
            self._set_item(key, value)

    # -------------------------------------------------------------------------
    def as_dict(self, short=True):

        res = {}
        for cluster_name in self._map:
            res[cluster_name] = self._map[cluster_name].as_dict(short)
        return res

    # -------------------------------------------------------------------------
    def as_list(self, short=True):

        res = []
        for cluster_name in self.keys():
            res.append(self._map[cluster_name].as_dict(short))
        return res


# =============================================================================

if __name__ == "__main__":

    pass

# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 list
