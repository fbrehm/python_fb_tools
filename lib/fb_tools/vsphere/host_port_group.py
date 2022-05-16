#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: Frank Brehm
@contact: frank.brehm@pixelpark.com
@copyright: © 2019 by Frank Brehm, Berlin
@summary: The module for a VSphere host portgroup object.
"""
from __future__ import absolute_import

# Standard modules
import logging
import copy

try:
    from collections.abc import MutableSequence
except ImportError:
    from collections import MutableSequence

# Third party modules
from pyVmomi import vim

# Own modules
from ..xlate import XLATOR

from ..common import pp
# from ..common import to_bool

from ..obj import FbBaseObject

__version__ = '0.1.1'
LOG = logging.getLogger(__name__)

_ = XLATOR.gettext


# =============================================================================
class VsphereHostPortgroup(FbBaseObject):

    # -------------------------------------------------------------------------
    def __init__(
        self, appname=None, verbose=0, version=__version__, base_dir=None, initialized=None,
            name=None, vlan_id=None, vswitch_name=None, hostname=None):

        self._name = None
        self._vlan_id = None
        self._vswitch_name = None
        self._hostname = None

        super(VsphereHostPortgroup, self).__init__(
            appname=appname, verbose=verbose, version=version,
            base_dir=base_dir, initialized=False)

        self.name = name
        self.vlan_id = vlan_id
        self.vswitch_name = vswitch_name
        self.hostname = hostname

        if initialized is not None:
            self.initialized = initialized

    # -----------------------------------------------------------
    @property
    def name(self):
        """The name of the port group."""
        return self._name

    @name.setter
    def name(self, value):
        if value is None:
            self._name = None
            return
        v = str(value).strip()
        if v == '':
            self._name = None
            return
        self._name = v

    # -----------------------------------------------------------
    @property
    def vlan_id(self):
        """The VLAN ID for ports using this port group."""
        return self._vlan_id

    @vlan_id.setter
    def vlan_id(self, value):
        if value is None:
            self._vlan_id = None
            return
        self._vlan_id = int(value)

    # -----------------------------------------------------------
    @property
    def vswitch_name(self):
        """The identifier of the virtual switch on which this port group is located."""
        return self._vswitch_name

    @vswitch_name.setter
    def vswitch_name(self, value):
        if value is None:
            self._vswitch_name = None
            return
        v = str(value).strip()
        if v == '':
            self._vswitch_name = None
            return
        self._vswitch_name = v

    # -----------------------------------------------------------
    @property
    def hostname(self):
        """The host name of the port group."""
        return self._hostname

    @hostname.setter
    def hostname(self, value):
        if value is None:
            self._hostname = None
            return
        v = str(value).strip().lower()
        if v == '':
            self._hostname = None
            return
        self._hostname = v

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
                'name': self.name,
                'vlan_id': self.vlan_id,
                'vswitch_name': self.vswitch_name,
                'hostname': self.hostname,
            }
            return res

        res = super(VsphereHostPortgroup, self).as_dict(short=short)
        res['name'] = self.name
        res['vlan_id'] = self.vlan_id
        res['vswitch_name'] = self.vswitch_name
        res['hostname'] = self.hostname

        return res

    # -------------------------------------------------------------------------
    def __eq__(self, other):

        if self.verbose > 4:
            LOG.debug(_("Comparing {} objects ...").format(self.__class__.__name__))

        if not isinstance(other, VsphereHostPortgroup):
            return False

        if self.hostname != other.hostname:
            return False
        if self.name != other.name:
            return False

        return True

    # -------------------------------------------------------------------------
    def __copy__(self):

        group = VsphereHostPortgroup(
            appname=self.appname, verbose=self.verbose, base_dir=self.base_dir,
            initialized=self.initialized, name=self.name, vlan_id=self.vlan_id,
            vswitch_name=self.vswitch_name, hostname=self.hostname)

        return group

    # -------------------------------------------------------------------------
    @classmethod
    def from_summary(cls, data, hostname=None, appname=None, verbose=0, base_dir=None):

        if not isinstance(data, vim.host.PortGroup):
            msg = _("Parameter {t!r} must be a {e}, {v!r} ({vt}) was given.").format(
                t='data', e='vim.host.PortGroup', v=data, vt=data.__class__.__name__)
            raise TypeError(msg)

        params = {
            'appname': appname,
            'verbose': verbose,
            'base_dir': base_dir,
            'initialized': True,
            'name': data.spec.name,
            'vlan_id': data.spec.vlanId,
            'vswitch_name': data.spec.vswitchName,
            'hostname': hostname,
        }

        if verbose > 2:
            LOG.debug(_("Creating {} object from:").format(cls.__name__) + '\n' + pp(params))

        group = cls(**params)

        if verbose > 2:
            LOG.debug(_("Created {} object:").format(cls.__name__) + '\n' + pp(group.as_dict()))

        return group


# =============================================================================
class VsphereHostPortgroupList(FbBaseObject, MutableSequence):
    """
    A list containing VsphereHostPortgroup objects.
    """

    msg_no_portgroup = _("Invalid type {t!r} as an item of a {c}, only {o} objects are allowed.")

    # -------------------------------------------------------------------------
    def __init__(
        self, appname=None, verbose=0, version=__version__, base_dir=None,
            initialized=None, hostname=None, *groups):

        self._list = []
        self._hostname = None

        super(VsphereHostPortgroupList, self).__init__(
            appname=appname, verbose=verbose, version=version, base_dir=base_dir,
            initialized=False)

        self.hostname = hostname

        for group in groups:
            self.append(group)

        if initialized is not None:
            self.initialized = initialized

    # -----------------------------------------------------------
    @property
    def hostname(self):
        """The host name of the port group list."""
        return self._hostname

    @hostname.setter
    def hostname(self, value):
        if value is None:
            self._hostname = None
            return
        v = str(value).strip().lower()
        if v == '':
            self._hostname = None
            return
        self._hostname = v

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
            for group in self:
                res.append(group.as_dict(bare=True))
            return res

        res = super(VsphereHostPortgroupList, self).as_dict(short=short)
        res['hostname'] = self.hostname
        res['_list'] = []

        for group in self:
            res['_list'].append(group.as_dict(short=short))

        return res

    # -------------------------------------------------------------------------
    def __copy__(self):

        new_list = self.__class__(
            appname=self.appname, verbose=self.verbose, base_dir=self.base_dir,
            hostname=self.hostname, initialized=False)

        for group in self:
            new_list.append(copy.copy(group))

        new_list.initialized = self.initialized
        return new_list

    # -------------------------------------------------------------------------
    def index(self, group, *args):

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
        start = 0
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
            if item == group:
                return index

        if wrap:
            for index in list(range(len(self._list))):
                item = self._list[index]
                if index >= end:
                    break
            if item == group:
                return index

        msg = _("group is not in group list.")
        raise ValueError(msg)

    # -------------------------------------------------------------------------
    def __contains__(self, group):

        if not isinstance(group, VsphereHostPortgroup):
            raise TypeError(self.msg_no_ether_card.format(
                t=group.__class__.__name__, c=self.__class__.__name__, o='VsphereHostPortgroup'))

        if not self._list:
            return False

        for item in self._list:
            if item == group:
                return True

        return False

    # -------------------------------------------------------------------------
    def count(self, group):

        if not isinstance(group, VsphereHostPortgroup):
            raise TypeError(self.msg_no_ether_card.format(
                t=group.__class__.__name__, c=self.__class__.__name__, o='VsphereHostPortgroup'))

        if not self._list:
            return 0

        num = 0
        for item in self._list:
            if item == group:
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

        new_list = self.__class__(
            appname=self.appname, verbose=self.verbose,
            base_dir=self.base_dir, initialized=False)

        for group in reversed(self._list):
            new_list.append(copy.copy(group))

        new_list.initialized = self.initialized
        return new_list

    # -------------------------------------------------------------------------
    def __setitem__(self, key, group):

        if not isinstance(group, VsphereHostPortgroup):
            raise TypeError(self.msg_no_ether_card.format(
                t=group.__class__.__name__, c=self.__class__.__name__, o='VsphereHostPortgroup'))

        self._list.__setitem__(key, group)

    # -------------------------------------------------------------------------
    def __delitem__(self, key):

        del self._list[key]

    # -------------------------------------------------------------------------
    def append(self, group):

        if not isinstance(group, VsphereHostPortgroup):
            raise TypeError(self.msg_no_ether_card.format(
                t=group.__class__.__name__, c=self.__class__.__name__, o='VsphereHostPortgroup'))

        self._list.append(group)

    # -------------------------------------------------------------------------
    def insert(self, index, group):

        if not isinstance(group, VsphereHostPortgroup):
            raise TypeError(self.msg_no_ether_card.format(
                t=group.__class__.__name__, c=self.__class__.__name__, o='VsphereHostPortgroup'))

        self._list.insert(index, group)

    # -------------------------------------------------------------------------
    def clear(self):
        "Remove all items from the VsphereHostPortgroupList."

        self._list = []

    # -------------------------------------------------------------------------
    def ordered(self):

        try:
            for group in sorted(self._list, key=lambda x: x.name.lower()):
                yield group
        except StopIteration:
            pass


# =============================================================================
if __name__ == "__main__":

    pass

# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 list
