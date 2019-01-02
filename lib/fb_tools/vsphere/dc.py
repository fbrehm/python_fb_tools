#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: Frank Brehm
@contact: frank.brehm@pixelpark.com
@copyright: © 2019 by Frank Brehm, Berlin
@summary: The module for a VSphere server object.
"""
from __future__ import absolute_import

# Standard modules
import logging

# Third party modules
from pyVmomi import vim

# Own modules
from ..xlate import XLATOR

from ..common import pp

from .object import VsphereObject

__version__ = '0.2.3'
LOG = logging.getLogger(__name__)

_ = XLATOR.gettext


# =============================================================================
class VsphereDatacenter(VsphereObject):
    """
    Class for a VSphere Datacenter object.
    """

    # -------------------------------------------------------------------------
    def __init__(
        self, appname=None, verbose=0, version=__version__, base_dir=None, initialized=None,
            name=None, status='gray', config_status='gray', ds_folder='datastore',
            host_folder='host', network_folder='network', vm_folder='vm'):

        self.repr_fields = (
            'name', 'obj_type', 'name_prefix', 'status', 'config_status',
            'appname', 'verbose', 'version')

        self._ds_folder = 'datastore'
        self._host_folder = 'host'
        self._network_folder = 'network'
        self._vm_folder = 'vm'

        super(VsphereDatacenter, self).__init__(
            name=name, obj_type='vsphere_datacenter', name_prefix="dc", status=status,
            config_status=config_status, appname=appname, verbose=verbose,
            version=version, base_dir=base_dir)

        self._ds_folder = ds_folder
        self._host_folder = host_folder
        self._network_folder = network_folder
        self._vm_folder = vm_folder

        if initialized is not None:
            self.initialized = initialized

    # -------------------------------------------------------------------------
    @property
    def ds_folder(self):
        """Name of the Folder for datastores and datastore clusters."""
        return self._ds_folder

    # -------------------------------------------------------------------------
    @property
    def host_folder(self):
        """Name of the Folder for hosts and compute resources."""
        return self._host_folder

    # -------------------------------------------------------------------------
    @property
    def network_folder(self):
        """Name of the Folder for networks."""
        return self._network_folder

    # -------------------------------------------------------------------------
    @property
    def vm_folder(self):
        """Name of the Folder for VMs."""
        return self._vm_folder

    # -------------------------------------------------------------------------
    def as_dict(self, short=True):
        """
        Transforms the elements of the object into a dict

        @param short: don't include local properties in resulting dict.
        @type short: bool

        @return: structure as dict
        @rtype:  dict
        """

        res = super(VsphereDatacenter, self).as_dict(short=short)
        res['ds_folder'] = self.ds_folder
        res['host_folder'] = self.host_folder
        res['network_folder'] = self.network_folder
        res['vm_folder'] = self.vm_folder

        return res

    # -------------------------------------------------------------------------
    def __copy__(self):

        return VsphereDatacenter(
            appname=self.appname, verbose=self.verbose, base_dir=self.base_dir,
            initialized=self.initialized, name=self.name,
            status=self.status, config_status=self.config_status)

    # -------------------------------------------------------------------------
    def __eq__(self, other):

        if self.verbose > 4:
            LOG.debug("Comparing {}-objects ...".format(self.__class__.__name__))

        if not isinstance(other, VsphereDatacenter):
            return False

        if self.name != other.name:
            return False

        return True

    # -------------------------------------------------------------------------
    @classmethod
    def from_summary(cls, data, appname=None, verbose=0, base_dir=None):

        if not isinstance(data, vim.Datacenter):
            msg = _("Parameter {t!r} must be a {e}, {v!r} was given.").format(
                t='data', e='vim.Datacenter', v=data)
            raise TypeError(msg)

        params = {
            'appname': appname,
            'verbose': verbose,
            'base_dir': base_dir,
            'initialized': True,
            'name': data.name,
            'status': data.overallStatus,
            'config_status': data.configStatus,
            'ds_folder': data.datastoreFolder.name,
            'host_folder': data.hostFolder.name,
            'network_folder': data.networkFolder.name,
            'vm_folder': data.vmFolder.name,
        }

        if verbose > 2:
            LOG.debug("Creating {c} object from:\n{p}".format(
                c=cls.__name__, p=pp(params)))

        dc = cls(**params)

        return dc


# =============================================================================

if __name__ == "__main__":

    pass

# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 list
