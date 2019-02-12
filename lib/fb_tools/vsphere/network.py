#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: Frank Brehm
@contact: frank.brehm@pixelpark.com
@copyright: © 2019 by Frank Brehm, Berlin
@summary: The module for a VSphere network object.
"""
from __future__ import absolute_import

# Standard modules
import logging
import re
import collections
import ipaddress
import functools

# Third party modules
from pyVmomi import vim

# Own modules
from ..xlate import XLATOR

from ..common import pp

from .object import VsphereObject

__version__ = '1.2.5'
LOG = logging.getLogger(__name__)

_ = XLATOR.gettext


# =============================================================================
class VsphereNetwork(VsphereObject):

    re_ipv4_name = re.compile(r'\s*((?:\d{1,3}\.){3}\d{1,3})_(\d+)\s*$')
    re_tf_name = re.compile(r'[^a-z0-9_]+', re.IGNORECASE)

    # -------------------------------------------------------------------------
    def __init__(
        self, appname=None, verbose=0, version=__version__, base_dir=None, initialized=None,
            name=None, status='gray', config_status='gray', accessible=True,
            ip_pool_id=None, ip_pool_name=None):

        self.repr_fields = (
            'name', 'obj_type', 'status', 'config_status', 'accessible',
            'ip_pool_id', 'ip_pool_name', 'appname', 'verbose')

        self._accessible = bool(accessible)
        self._ip_pool_id = ip_pool_id
        self._ip_pool_name = ip_pool_name

        self._network = None

        super(VsphereNetwork, self).__init__(
            name=name, obj_type='vsphere_network', name_prefix="net", status=status,
            config_status=config_status, appname=appname, verbose=verbose,
            version=version, base_dir=base_dir)

        match = self.re_ipv4_name.search(self.name)
        if match:
            ip = "{a}/{m}".format(a=match.group(1), m=match.group(2))
            if self.verbose > 3:
                LOG.debug(_("Trying to get IPv4 network {n!r} -> {i!r}.").format(
                    n=self.name, i=ip))

            try:
                net = ipaddress.ip_network(ip)
                self._network = net
            except ValueError:
                LOG.error(_("Could not get IP network from network name {!r}.").format(self.name))

        if not self.network:
            LOG.warning(_("Network {!r} has no IP network assigned.").format(self.name))

        if initialized is not None:
            self.initialized = initialized

        if self.verbose > 3:
            LOG.debug(_("Initialized network object:") + '\n' + pp(self.as_dict()))

    # -----------------------------------------------------------
    @property
    def accessible(self):
        """The connectivity status of this network."""
        return self._accessible

    # -----------------------------------------------------------
    @property
    def ip_pool_id(self):
        """Identifier of the associated IP pool."""
        return self._ip_pool_id

    # -----------------------------------------------------------
    @property
    def ip_pool_name(self):
        """Name of the associated IP pool."""
        return self._ip_pool_name

    # -----------------------------------------------------------
    @property
    def network(self):
        """The ipaddress network object associated with this network."""
        return self._network

    # -----------------------------------------------------------
    @property
    def gateway(self):
        """The IP address of the getaeway inside this network."""
        if not self.network:
            return None
        return self.network.network_address + 1

    # -------------------------------------------------------------------------
    @classmethod
    def from_summary(cls, data, appname=None, verbose=0, base_dir=None):

        if not isinstance(data, vim.Network):
            msg = _("Parameter {t!r} must be a {e}, {v!r} was given.").format(
                t='data', e='vim.Network', v=data)
            raise TypeError(msg)

        params = {
            'appname': appname,
            'verbose': verbose,
            'base_dir': base_dir,
            'initialized': True,
            'name': data.summary.name,
            'status': data.overallStatus,
            'config_status': data.configStatus,
        }

        if hasattr(data.summary, 'accessible'):
            params['accessible'] = data.summary.accessible

        if hasattr(data.summary, 'ipPoolId'):
            params['ip_pool_id'] = data.summary.ipPoolId

        if hasattr(data.summary, 'ipPoolName'):
            params['ip_pool_name'] = data.summary.ipPoolName

        if verbose > 3:
            LOG.debug(_("Creating {} object from:").format(cls.__name__) + '\n' + pp(params))

        net = cls(**params)
        return net

    # -------------------------------------------------------------------------
    def as_dict(self, short=True):
        """
        Transforms the elements of the object into a dict

        @param short: don't include local properties in resulting dict.
        @type short: bool

        @return: structure as dict
        @rtype:  dict
        """

        res = super(VsphereNetwork, self).as_dict(short=short)
        res['accessible'] = self.accessible
        res['ip_pool_id'] = self.ip_pool_id
        res['ip_pool_name'] = self.ip_pool_name
        res['network'] = self.network
        res['gateway'] = self.gateway

        return res

    # -------------------------------------------------------------------------
    def __copy__(self):

        return VsphereNetwork(
            appname=self.appname, verbose=self.verbose, base_dir=self.base_dir,
            initialized=self.initialized, name=self.name, accessible=self.accessible,
            ip_pool_id=self.ip_pool_id, ip_pool_name=self.ip_pool_name,
            status=self.status, config_status=self.config_status)

    # -------------------------------------------------------------------------
    def __eq__(self, other):

        if self.verbose > 4:
            LOG.debug(_("Comparing {} objects ...").format(self.__class__.__name__))

        if not isinstance(other, VsphereNetwork):
            return False

        if self.name != other.name:
            return False

        return True


# =============================================================================
class VsphereNetworkDict(collections.MutableMapping):
    """
    A dictionary containing VsphereNetwork objects.
    It works like a dict.
    """

    msg_invalid_net_type = _("Invalid item type {{!r}} to set, only {} allowed.").format(
        'VsphereNetwork')
    msg_key_not_name = _("The key {k!r} must be equal to the network name {n!r}.")
    msg_none_type_error = _("None type as key is not allowed.")
    msg_empty_key_error = _("Empty key {!r} is not allowed.")
    msg_no_net_dict = _("Object {{!r}} is not a {} object.").format('VsphereNetworkDict')

    # -------------------------------------------------------------------------
    def __init__(self, *args, **kwargs):
        '''Use the object dict'''
        self._map = dict()

        for arg in args:
            self.append(arg)

    # -------------------------------------------------------------------------
    def _set_item(self, key, net):

        if not isinstance(net, VsphereNetwork):
            raise TypeError(self.msg_invalid_net_type.format(net.__class__.__name__))

        net_name = net.name
        if net_name != key:
            raise KeyError(self.msg_key_not_name.format(k=key, n=net_name))

        self._map[net_name] = net

    # -------------------------------------------------------------------------
    def append(self, net):

        if not isinstance(net, VsphereNetwork):
            raise TypeError(self.msg_invalid_net_type.format(net.__class__.__name__))
        self._set_item(net.name, net)

    # -------------------------------------------------------------------------
    def _get_item(self, key):

        if key is None:
            raise TypeError(self.msg_none_type_error)

        net_name = str(key).strip()
        if net_name == '':
            raise ValueError(self.msg_empty_key_error.format(key))

        return self._map[net_name]

    # -------------------------------------------------------------------------
    def get(self, key):
        return self._get_item(key)

    # -------------------------------------------------------------------------
    def _del_item(self, key, strict=True):

        if key is None:
            raise TypeError(self.msg_none_type_error)

        net_name = str(key).strip()
        if net_name == '':
            raise ValueError(self.msg_empty_key_error.format(key))

        if not strict and net_name not in self._map:
            return

        del self._map[net_name]

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

        for net_name in self.keys():
            yield net_name

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
            super(VsphereNetworkDict, self).__repr__(),
            self.__class__.__name__,
            self._map)

    # -------------------------------------------------------------------------
    def __contains__(self, key):
        if key is None:
            raise TypeError(self.msg_none_type_error)

        net_name = str(key).strip()
        if net_name == '':
            raise ValueError(self.msg_empty_key_error.format(key))

        return net_name in self._map

    # -------------------------------------------------------------------------
    def keys(self):

        def netsort(x, y):
            net_x = self[x]
            net_y = self[y]
            if net_x.network is None and net_y.network is None:
                return (
                    (net_x.name.lower() > net_y.name.lower()) - (
                        net_x.name.lower() < net_y.name.lower()))
            if net_x.network is None:
                return -1
            if net_y.network is None:
                return 1
            if net_x.network < net_y.network:
                return -1
            if net_x.network > net_y.network:
                return 1
            return 0

        return sorted(self._map.keys(), key=functools.cmp_to_key(netsort))

    # -------------------------------------------------------------------------
    def items(self):

        item_list = []

        for net_name in self.keys():
            item_list.append((net_name, self._map[net_name]))

        return item_list

    # -------------------------------------------------------------------------
    def values(self):

        value_list = []
        for net_name in self.keys():
            value_list.append(self._map[net_name])
        return value_list

    # -------------------------------------------------------------------------
    def __eq__(self, other):

        if not isinstance(other, VsphereNetworkDict):
            raise TypeError(self.msg_no_net_dict.format(other))

        return self._map == other._map

    # -------------------------------------------------------------------------
    def __ne__(self, other):

        if not isinstance(other, VsphereNetworkDict):
            raise TypeError(self.msg_no_net_dict.format(other))

        return self._map != other._map

    # -------------------------------------------------------------------------
    def pop(self, key, *args):

        if key is None:
            raise TypeError(self.msg_none_type_error)

        net_name = str(key).strip()
        if net_name == '':
            raise ValueError(self.msg_empty_key_error.format(key))

        return self._map.pop(net_name, *args)

    # -------------------------------------------------------------------------
    def popitem(self):

        if not len(self._map):
            return None

        net_name = self.keys()[0]
        net = self._map[net_name]
        del self._map[net_name]
        return (net_name, net)

    # -------------------------------------------------------------------------
    def clear(self):
        self._map = dict()

    # -------------------------------------------------------------------------
    def setdefault(self, key, default):

        if key is None:
            raise TypeError(self.msg_none_type_error)

        net_name = str(key).strip()
        if net_name == '':
            raise ValueError(self.msg_empty_key_error.format(key))

        if not isinstance(default, VsphereNetwork):
            raise TypeError(self.msg_invalid_net_type.format(default.__class__.__name__))

        if net_name in self._map:
            return self._map[net_name]

        self._set_item(net_name, default)
        return default

    # -------------------------------------------------------------------------
    def update(self, other):

        if isinstance(other, VsphereNetworkDict) or isinstance(other, dict):
            for net_name in other.keys():
                self._set_item(net_name, other[net_name])
            return

        for tokens in other:
            key = tokens[0]
            value = tokens[1]
            self._set_item(key, value)

    # -------------------------------------------------------------------------
    def as_dict(self, short=True):

        res = {}
        for net_name in self._map:
            res[net_name] = self._map[net_name].as_dict(short)
        return res

    # -------------------------------------------------------------------------
    def as_list(self, short=True):

        res = []
        for net_name in self.keys():
            res.append(self._map[net_name].as_dict(short))
        return res

    # -------------------------------------------------------------------------
    def get_network_for_ip(self, *ips):

        for ip in ips:
            if not ip:
                continue
            LOG.debug(_("Searching VSphere network for address {} ...").format(ip))
            ipa = ipaddress.ip_address(ip)

            for net_name in self.keys():
                net = self[net_name]
                if net.network and ipa in net.network:
                    LOG.debug(_("Found network {n!r} for IP {i}.").format(
                        n=net_name, i=ip))
                    return net_name

            LOG.debug(_("Could not find VSphere network for IP {}.").format(ip))

        ips_str = ', '.join(map(lambda x: str(x), list(filter(bool, ips))))
        LOG.error(_("Could not find VSphere network for IP addresses {}.").format(ips_str))
        return None


# =============================================================================
if __name__ == "__main__":

    pass

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 list
