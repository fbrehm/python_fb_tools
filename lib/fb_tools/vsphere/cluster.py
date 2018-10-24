#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: Frank Brehm
@contact: frank.brehm@pixelpark.com
@copyright: © 2018 by Frank Brehm, Berlin
@summary: The module for a VSphere calculation cluster object.
"""
from __future__ import absolute_import

# Standard modules
import logging

# Third party modules
from pyVmomi import vim

# Own modules
from ..common import pp

from .object import VsphereObject


__version__ = '0.2.1'
LOG = logging.getLogger(__name__)


# =============================================================================
class VsphereCluster(VsphereObject):

    # -------------------------------------------------------------------------
    def __init__(
        self, appname=None, verbose=0, version=__version__, base_dir=None, initialized=None,
            name=None, status='gray', cpu_cores=0, cpu_threads=0,
            hosts_effective=0, hosts_total=0, mem_mb_effective=0, mem_total=0):

        self.repr_fields = (
            'name', 'status', 'cpu_cores', 'cpu_threads', 'hosts_effective', 'hosts_total',
            'mem_mb_effective', 'mem_total', 'appname', 'verbose', 'version')

        self._status = None
        self._cpu_cores = None
        self._cpu_threads = None
        self._hosts_effective = None
        self._hosts_total = None
        self._mem_mb_effective = None
        self._mem_total = None

        super(VsphereCluster, self).__init__(
            name=name, obj_type='vsphere_cluster', name_prefix="cluster",
            appname=appname, verbose=verbose, version=version, base_dir=base_dir)

        self.status = status
        self.cpu_cores = cpu_cores
        self.cpu_threads = cpu_threads
        self.hosts_effective = hosts_effective
        self.hosts_total = hosts_total
        self.mem_mb_effective = mem_mb_effective
        self.mem_total = mem_total

        if initialized is not None:
            self.initialized = initialized

    # -----------------------------------------------------------
    @property
    def resource_pool_name(self):
        """The name of the default resource pool of this cluster."""
        return self.name + '/Resources'

    # -----------------------------------------------------------
    @property
    def resource_pool_var(self):
        """The variable name of the default resource pool used for terraform."""
        return 'pool_' + self.tf_name

    # -----------------------------------------------------------
    @property
    def status(self):
        """Overall alarm status of the cluster."""
        return self._status

    @status.setter
    def status(self, value):
        if value is None:
            self._status = 'gray'
            return

        val = str(value).strip().lower()
        if val == '':
            self._status = 'gray'
            return
        self._status = val

    # -----------------------------------------------------------
    @property
    def cpu_cores(self):
        """The number of physical CPU cores of the cluster."""
        return self._cpu_cores

    @cpu_cores.setter
    def cpu_cores(self, value):
        if value is None:
            self._cpu_cores = 0
            return

        val = int(value)
        self._cpu_cores = val

    # -----------------------------------------------------------
    @property
    def cpu_threads(self):
        """The aggregated number of CPU threads of the cluster."""
        return self._cpu_threads

    @cpu_threads.setter
    def cpu_threads(self, value):
        if value is None:
            self._cpu_threads = 0
            return

        val = int(value)
        self._cpu_threads = val

    # -----------------------------------------------------------
    @property
    def hosts_effective(self):
        """The total number of effective hosts of the cluster."""
        return self._hosts_effective

    @hosts_effective.setter
    def hosts_effective(self, value):
        if value is None:
            self._hosts_effective = 0
            return

        val = int(value)
        self._hosts_effective = val

    # -----------------------------------------------------------
    @property
    def hosts_total(self):
        """The total number of hosts of the cluster."""
        return self._hosts_total

    @hosts_total.setter
    def hosts_total(self, value):
        if value is None:
            self._hosts_total = 0
            return

        val = int(value)
        self._hosts_total = val

    # -----------------------------------------------------------
    @property
    def mem_total(self):
        """The aggregated memory resources of all hosts of the cluster in Bytes."""
        return self._mem_total

    @mem_total.setter
    def mem_total(self, value):
        if value is None:
            self._mem_total = 0
            return

        val = int(value)
        self._mem_total = val

    # -----------------------------------------------------------
    @property
    def mem_mb_total(self):
        """The aggregated memory resources of all hosts of the cluster in MiBytes."""
        if self.mem_total is None:
            return None
        return self.mem_total / 1024 / 1024

    # -----------------------------------------------------------
    @property
    def mem_gb_total(self):
        """The aggregated memory resources of all hosts of the cluster in GiBytes."""
        if self.mem_total is None:
            return None
        return float(self.mem_total) / 1024.0 / 1024.0 / 1024.0

    # -----------------------------------------------------------
    @property
    def mem_mb_effective(self):
        """The effective memory resources (in MB) available
            to run virtual machines of the cluster."""
        return self._mem_mb_effective

    @mem_mb_effective.setter
    def mem_mb_effective(self, value):
        if value is None:
            self._mem_mb_effective = 0
            return

        val = int(value)
        self._mem_mb_effective = val

    # -----------------------------------------------------------
    @property
    def mem_gb_effective(self):
        """The effective memory resources (in GiBytes) available
            to run virtual machines of the cluster."""
        if self.mem_mb_effective is None:
            return None
        return float(self.mem_mb_effective) / 1024.0

    # -------------------------------------------------------------------------
    def as_dict(self, short=True):
        """
        Transforms the elements of the object into a dict

        @param short: don't include local properties in resulting dict.
        @type short: bool

        @return: structure as dict
        @rtype:  dict
        """

        res = super(VsphereCluster, self).as_dict(short=short)
        res['status'] = self.status
        res['resource_pool_name'] = self.resource_pool_name
        res['resource_pool_var'] = self.resource_pool_var
        res['cpu_cores'] = self.cpu_cores
        res['cpu_threads'] = self.cpu_threads
        res['hosts_effective'] = self.hosts_effective
        res['hosts_total'] = self.hosts_total
        res['mem_mb_effective'] = self.mem_mb_effective
        res['mem_gb_effective'] = self.mem_gb_effective
        res['mem_total'] = self.mem_total
        res['mem_mb_total'] = self.mem_mb_total
        res['mem_gb_total'] = self.mem_gb_total

        return res

    # -------------------------------------------------------------------------
    def __copy__(self):

        return VsphereCluster(
            appname=self.appname, verbose=self.verbose, base_dir=self.base_dir,
            initialized=self.initialized, name=self.name,
            status=self.status, cpu_cores=self.cpu_cores, cpu_threads=self.cpu_threads,
            hosts_effective=self.hosts_effective, hosts_total=self.hosts_total,
            mem_mb_effective=self.mem_mb_effective, mem_total=self.mem_total)

    # -------------------------------------------------------------------------
    def __eq__(self, other):

        if self.verbose > 4:
            LOG.debug("Comparing {}-objects ...".format(self.__class__.__name__))

        if not isinstance(other, VsphereCluster):
            return False

        if self.name != other.name:
            return False

        return True

    # -------------------------------------------------------------------------
    @classmethod
    def from_summary(cls, data, appname=None, verbose=0, base_dir=None):

        if not isinstance(data, vim.ClusterComputeResource):
            msg = "Argument {!r} is not a cluster compute resource.".format(data)
            raise TypeError(msg)

        params = {
            'appname': appname,
            'verbose': verbose,
            'base_dir': base_dir,
            'initialized': True,
            'name': data.name,
            'status': data.summary.overallStatus,
            'cpu_cores': data.summary.numCpuCores,
            'cpu_threads': data.summary.numCpuThreads,
            'hosts_effective': data.summary.numEffectiveHosts,
            'hosts_total': data.summary.numHosts,
            'mem_mb_effective': data.summary.effectiveMemory,
            'mem_total': data.summary.totalMemory,
        }

        if verbose > 2:
            LOG.debug("Creating {c} object from:\n{p}".format(
                c=cls.__name__, p=pp(params)))

        cluster = cls(**params)
        return cluster


# =============================================================================
if __name__ == "__main__":

    pass

# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 list
