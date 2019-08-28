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
import datetime
import uuid
import ipaddress

# Third party modules
from pyVmomi import vim

# Own modules
from ..xlate import XLATOR

from ..common import pp, to_bool

from ..obj import FbBaseObject

from .object import VsphereObject

__version__ = '0.2.1'
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

        super(VsphereVm, self).__init__(
            name=name, obj_type='vsphere_vm', name_prefix="vm", status=status,
            config_status=config_status, appname=appname, verbose=verbose,
            version=version, base_dir=base_dir)

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
    def path(self):
        """The path of the VM in the iVM folder structure."""
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
        res['path'] = self.path
        res['template'] = self.template

        return res

    # -------------------------------------------------------------------------
    def __copy__(self):

        vm = VsphereVm(
            appname=self.appname, verbose=self.verbose, base_dir=self.base_dir,
            initialized=self.initialized, name=self.name, status=self.status,
            config_status=self.config_status)

        vm.cluster_name = self.cluster_name
        vm.path = self.path
        vm.template = self.template

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

        vm.path = cur_path
        vm.template = data.summary.config.template

        if verbose > 2:
            LOG.debug(_("Created {} object:").format(cls.__name__) + '\n' + pp(vm.as_dict()))

        return vm


# =============================================================================
if __name__ == "__main__":

    pass

# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 list
