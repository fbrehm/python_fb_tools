#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: Frank Brehm
@contact: frank.brehm@pixelpark.com
@copyright: © 2018 by Frank Brehm, Berlin
@summary: The module for a VSphere server object.
"""
from __future__ import absolute_import

# Standard modules
import logging
import re
import uuid
import socket

# Third party modules
from pyVmomi import vim
import requests
import urllib3

# Own modules
from ..common import pp, RE_TF_NAME

from . import BaseVsphereHandler
from . import DEFAULT_HOST, DEFAULT_PORT, DEFAULT_USER, DEFAULT_DC, DEFAULT_CLUSTER

from .cluster import VsphereCluster

from .ds import VsphereDatastore, VsphereDatastoreDict

from .ds_cluster import VsphereDsCluster, VsphereDsClusterDict

from .network import VsphereNetwork, VsphereNetworkDict

from .errors import VSphereExpectedError
from .errors import VSphereDatacenterNotFoundError, VSphereNoDatastoresFoundError

__version__ = '0.7.10'
LOG = logging.getLogger(__name__)


# =============================================================================
class VsphereServer(BaseVsphereHandler):
    """
    Class for a VSphere server handler object.
    """

    re_local_ds = re.compile(r'^local[_-]', re.IGNORECASE)

    # -------------------------------------------------------------------------
    def __init__(
        self, appname=None, verbose=0, version=__version__, base_dir=None,
            host=DEFAULT_HOST, port=DEFAULT_PORT, user=DEFAULT_USER, password=None,
            dc=DEFAULT_DC, cluster=DEFAULT_CLUSTER, auto_close=True, simulate=None,
            force=None, terminal_has_colors=False, initialized=False):

        self.datastores = VsphereDatastoreDict()
        self.ds_clusters = VsphereDsClusterDict()
        self.networks = VsphereNetworkDict()
        self.about = None

        self.ds_mapping = {}
        self.ds_cluster_mapping = {}
        self.network_mapping = {}

        self.clusters = []

        super(VsphereServer, self).__init__(
            appname=appname, verbose=verbose, version=version, base_dir=base_dir,
            host=host, port=port, user=user, password=password, dc=dc, cluster=cluster,
            simulate=simulate, force=force, auto_close=auto_close,
            terminal_has_colors=terminal_has_colors, initialized=False,
        )

        self.initialized = initialized

    # -------------------------------------------------------------------------
    def get_about(self, disconnect=False):

        LOG.debug("Trying to get some 'about' information from VSphere.")

        try:

            if not self.service_instance:
                self.connect()

            about = self.service_instance.content.about
            self.about = {}

#               'about': (vim.AboutInfo) {
#                   dynamicType = <unset>,
#                   dynamicProperty = (vmodl.DynamicProperty) [],
#                   name = 'VMware vCenter Server',
#                   fullName = 'VMware vCenter Server 6.5.0 build-8024368',
#                   vendor = 'VMware, Inc.',
#                   version = '6.5.0',
#                   build = '8024368',
#                   localeVersion = 'INTL',
#                   localeBuild = '000',
#                   osType = 'linux-x64',
#                   productLineId = 'vpx',
#                   apiType = 'VirtualCenter',
#                   apiVersion = '6.5',
#                   instanceUuid = 'ea1b28ca-0d17-4292-ab04-189e57ec9629',
#                   licenseProductName = 'VMware VirtualCenter Server',
#                   licenseProductVersion = '6.0'
#               },

            for attr in (
                    'dynamicType', 'dynamicProperty', 'name', 'fullName', 'vendor', 'version',
                    'build', 'localeVersion', 'localeBuild', 'osType', 'productLineId', 'apiType',
                    'apiVersion', 'instanceUuid', 'licenseProductName', 'licenseProductVersion'):
                if hasattr(about, attr):
                    value = getattr(about, attr)
                    if attr == 'instanceUuid':
                        value = uuid.UUID(value)
                    self.about[attr] = value
        except (
                socket.timeout, urllib3.exceptions.ConnectTimeoutError,
                urllib3.exceptions.MaxRetryError,
                requests.exceptions.ConnectTimeout) as e:
            msg = "Got a {c} on connecting to {h!r}: {e}.".format(
                c=e.__class__.__name__, h=self.host, e=e)
            raise VSphereExpectedError(msg)

        finally:
            if disconnect:
                self.disconnect()

        LOG.info("VSphere server version: {!r}".format(self.about['version']))
        if self.verbose > 2:
            LOG.debug("Found about-information:\n{}".format(pp(self.about)))

    # -------------------------------------------------------------------------
    def get_clusters(self, disconnect=False):

        LOG.debug("Trying to get all clusters from VSphere ...")

        self.clusters = []

        try:

            if not self.service_instance:
                self.connect()

            content = self.service_instance.RetrieveContent()
            dc = self.get_obj(content, [vim.Datacenter], self.dc)
            if not dc:
                raise VSphereDatacenterNotFoundError(self.dc)
            for child in dc.hostFolder.childEntity:
                self._get_clusters(child)

        finally:
            if disconnect:
                self.disconnect()

        if self.verbose > 2:
            out = []
            for cluster in self.clusters:
                out.append(cluster.as_dict())
            LOG.debug("Found clusters:\n{}".format(pp(out)))
        elif self.verbose:
            out = []
            for cluster in self.clusters:
                out.append(cluster.name)
            LOG.debug("Found clusters: {}".format(pp(out)))

    # -------------------------------------------------------------------------
    def _get_clusters(self, child, depth=1):

        if hasattr(child, 'childEntity'):
            if depth > self.max_search_depth:
                return
            for sub_child in child.childEntity:
                self._get_clusters(sub_child, depth + 1)
            return

        if isinstance(child, vim.ClusterComputeResource):
            cluster = VsphereCluster.from_summary(
                child, appname=self.appname, verbose=self.verbose, base_dir=self.base_dir)
            if self.verbose > 1:
                LOG.debug((
                    "Found cluster {cl!r}, {h} hosts, {cpu} CPUs, {thr} threads, "
                    "{mem:0.1f} GiB Memory, {net} networks and {ds} datastores.").format(
                    cl=cluster.name, h=cluster.hosts_total, cpu=cluster.cpu_cores,
                    thr=cluster.cpu_threads, mem=cluster.mem_gb_total,
                    net=len(cluster.networks), ds=len(cluster.datastores)))
            self.clusters.append(cluster)

        return

    # -------------------------------------------------------------------------
    def get_cluster_by_name(self, cl_name):

        for cluster in self.clusters:
            if cluster.name.lower() == cl_name.lower():
                return cluster

        return None

    # -------------------------------------------------------------------------
    def get_datastores(self):

        LOG.debug("Trying to get all datastores from VSphere ...")
        self.datastores = VsphereDatastoreDict()
        self.ds_mapping = {}

        try:

            self.connect()

            content = self.service_instance.RetrieveContent()
            dc = self.get_obj(content, [vim.Datacenter], self.dc)
            if not dc:
                raise VSphereDatacenterNotFoundError(self.dc)
            for child in dc.datastoreFolder.childEntity:
                self._get_datastores(child)

        finally:
            self.disconnect()

        if self.datastores:
            if self.verbose > 1:
                if self.verbose > 3:
                    LOG.debug("Found datastores:\n{}".format(pp(self.datastores.as_list())))
                else:
                    LOG.debug("Found datastores:\n{}".format(pp(list(self.datastores.keys()))))
        else:
            raise VSphereNoDatastoresFoundError()

        for (ds_name, ds) in self.datastores.items():
            self.ds_mapping[ds_name] = ds.tf_name

        if self.verbose > 2:
            LOG.debug("Datastore mappings:\n{}".format(pp(self.ds_mapping)))

    # -------------------------------------------------------------------------
    def _get_datastores(self, child, depth=1):

        if hasattr(child, 'childEntity'):
            if depth > self.max_search_depth:
                return
            for sub_child in child.childEntity:
                self._get_datastores(sub_child, depth + 1)
            return

        if isinstance(child, vim.Datastore):
            if self.re_local_ds.match(child.summary.name):
                if self.verbose > 2:
                    LOG.debug("Datastore {!r} seems to be local.".format(child.summary.name))
                return
            ds = VsphereDatastore.from_summary(
                child.summary, appname=self.appname, verbose=self.verbose, base_dir=self.base_dir)
            if self.verbose > 2:
                LOG.debug("Found datastore {ds!r} of type {t!r}, capacity {c:0.1f} GByte.".format(
                    ds=ds.name, t=ds.storage_type, c=ds.capacity_gb))
            self.datastores.append(ds)

        return

    # -------------------------------------------------------------------------
    def get_ds_clusters(self):

        LOG.debug("Trying to get all datastore clusters from VSphere ...")
        self.ds_clusters = VsphereDsClusterDict()
        self.ds_cluster_mapping = {}

        try:

            self.connect()

            content = self.service_instance.RetrieveContent()
            dc = self.get_obj(content, [vim.Datacenter], self.dc)
            if not dc:
                raise VSphereDatacenterNotFoundError(self.dc)
            for child in dc.datastoreFolder.childEntity:
                self._get_ds_clusters(child)

        finally:
            self.disconnect()

        if self.ds_clusters:
            if self.verbose > 1:
                if self.verbose > 3:
                    LOG.debug(
                        "Found datastores clusters:\n{}".format(pp(self.ds_clusters.as_list())))
                else:
                    LOG.debug(
                        "Found datastores clusters:\n{}".format(pp(list(self.ds_clusters.keys()))))
        else:
            LOG.warn("No VSphere datastore clusters found.")

        for (dsc_name, dsc) in self.ds_clusters.items():
            self.ds_cluster_mapping[dsc_name] = dsc.tf_name

        if self.verbose > 2:
            LOG.debug("Datastore cluster mappings:\n{}".format(pp(self.ds_cluster_mapping)))

    # -------------------------------------------------------------------------
    def _get_ds_clusters(self, child, depth=1):

        if self.verbose > 3:
            LOG.debug("Found a {} child.".format(child.__class__.__name__))

        if hasattr(child, 'childEntity'):
            if depth > self.max_search_depth:
                return
            for sub_child in child.childEntity:
                self._get_ds_clusters(sub_child, depth + 1)

        if isinstance(child, vim.StoragePod):
            ds = VsphereDsCluster.from_summary(
                child.summary, appname=self.appname, verbose=self.verbose, base_dir=self.base_dir)
            self.ds_clusters.append(ds)

        return

    # -------------------------------------------------------------------------
    def get_networks(self):

        LOG.debug("Trying to get all networks from VSphere ...")
        self.networks = VsphereNetworkDict()
        self.network_mapping = {}

        try:

            self.connect()

            content = self.service_instance.RetrieveContent()
            dc = self.get_obj(content, [vim.Datacenter], self.dc)
            if not dc:
                raise VSphereDatacenterNotFoundError(self.dc)
            for child in dc.networkFolder.childEntity:
                self._get_networks(child)

        finally:
            self.disconnect()

        if self.networks:
            LOG.debug("Found {} VSphere networks.".format(len(self.networks)))
            if self.verbose > 2:
                if self.verbose > 3:
                    LOG.debug("Found VSphere networks:\n{}".format(pp(self.networks.as_list())))
                else:
                    LOG.debug("Found VSphere networks:\n{}".format(pp(list(self.networks.keys()))))
        else:
            LOG.error("No VSphere networks found.")

        for (net_name, net) in self.networks.items():
            self.network_mapping[net_name] = net.tf_name

        if self.verbose > 2:
            LOG.debug("Network mappings:\n{}".format(pp(self.network_mapping)))

    # -------------------------------------------------------------------------
    def _get_networks(self, child, depth=1):

        if self.verbose > 3:
            LOG.debug("Found a {} child.".format(child.__class__.__name__))

        if hasattr(child, 'childEntity'):
            if depth > self.max_search_depth:
                return
            for sub_child in child.childEntity:
                self._get_networks(sub_child, depth + 1)

        if isinstance(child, vim.Network):
            ds = VsphereNetwork.from_summary(
                child.summary, appname=self.appname, verbose=self.verbose, base_dir=self.base_dir)
            self.networks.append(ds)

        return

    # -------------------------------------------------------------------------
    def get_vm(self, vm_name, no_error=False, disconnect=False):

        LOG.debug("Trying to get VM {!r} from VSphere ...".format(vm_name))

        vm = None

        try:

            if not self.service_instance:
                self.connect()

            content = self.service_instance.RetrieveContent()
            dc = self.get_obj(content, [vim.Datacenter], self.dc)
            if not dc:
                raise VSphereDatacenterNotFoundError(self.dc)
            for child in dc.vmFolder.childEntity:
                vm = self._get_vm(child, vm_name)
                if vm:
                    break

        finally:
            if disconnect:
                self.disconnect()

        if not vm:
            msg = "VSphere VM {!r} not found.".format(vm_name)
            if no_error:
                LOG.debug(msg)
            else:
                LOG.error(msg)

        return vm

    # -------------------------------------------------------------------------
    def _get_vm(self, child, vm_name, cur_path='', depth=1):

        vm = None

        if self.verbose > 3:
            LOG.debug("Found a {} child.".format(child.__class__.__name__))

        if hasattr(child, 'childEntity'):
            if depth > self.max_search_depth:
                return None
            for sub_child in child.childEntity:
                child_path = ''
                if cur_path:
                    child_path = cur_path + '/' + child.name
                else:
                    child_path = child.name
                vm = self._get_vm(sub_child, vm_name, child_path, depth + 1)
                if vm:
                    return vm
            return None

        if isinstance(child, vim.VirtualMachine):
            summary = child.summary
            vm_config = summary.config
            if vm_name.lower() == vm_config.name.lower():
                if self.verbose > 2:
                    LOG.debug("Found VM {n!r} summary:\n{s}".format(
                        n=vm_name, s=pp(summary)))
                if self.verbose > 3:
                    LOG.debug("Found VM {n!r} config:\n{s}".format(
                        n=vm_name, s=pp(child.config)))
                vm_info = {}
                vm_info['name'] = vm_config.name
                vm_info['tf_name'] = 'vm_' + RE_TF_NAME.sub('_', vm_config.name.lower())
                vm_info['path'] = cur_path
                vm_info['memorySizeMB'] = vm_config.memorySizeMB
                vm_info['numCpu'] = vm_config.numCpu
                vm_info['numEthernetCards'] = vm_config.numEthernetCards
                vm_info['numVirtualDisks'] = vm_config.numVirtualDisks
                vm_info['template'] = vm_config.template
                vm_info['guestFullName'] = vm_config.guestFullName
                vm_info['guestId'] = vm_config.guestId
                vm_info['instanceUuid'] = vm_config.instanceUuid
                if vm_config.instanceUuid:
                    vm_info['instanceUuid'] = uuid.UUID(vm_config.instanceUuid)
                vm_info['uuid'] = vm_config.uuid
                if vm_config.uuid:
                    vm_info['uuid'] = uuid.UUID(vm_config.uuid)
                vm_info['vmPathName'] = vm_config.vmPathName
                vm_info['disks'] = {}
                for device in child.config.hardware.device:
                    if not isinstance(device, vim.vm.device.VirtualDisk):
                        continue
                    unit_nr = device.unitNumber
                    disk = {
                        'label': device.deviceInfo.label,
                        'unitNumber': unit_nr,
                        'capacityInKB': device.capacityInKB,
                        'capacityInBytes': device.capacityInBytes,
                        'uuid': device.backing.uuid,
                        'fileName': device.backing.fileName
                    }
                    disk['capacityInGB'] = device.capacityInKB / 1024 / 1024
                    if device.backing.uuid:
                        disk['uuid'] = uuid.UUID(device.backing.uuid)
                    vm_info['disks'][unit_nr] = disk
                vm_info['interfaces'] = {}
                for device in child.config.hardware.device:
                    if not isinstance(device, vim.vm.device.VirtualEthernetCard):
                        continue
                    unit_nr = device.unitNumber
                    iface = {
                        'unitNumber': unit_nr,
                        'class': device.__class__.__name__,
                        'addressType': device.addressType,
                        'macAddress': device.macAddress,
                        'backing_device': device.backing.deviceName,
                        'connected': device.connectable.connected,
                        'status': device.connectable.status,
                    }
                    vm_info['interfaces'][unit_nr] = iface
                return vm_info

        return None

    # -------------------------------------------------------------------------
    def ensure_vm_folders(self, folders, disconnect=False):
        LOG.debug("Ensuring existence of VSphere VM folders:\n{}".format(pp(folders)))
        try:

            if not self.service_instance:
                self.connect()

            for folder in folders:
                self.ensure_vm_folder(folder, disconnect=False)

        finally:
            if disconnect:
                self.disconnect()

    # -------------------------------------------------------------------------
    def get_vm_folder(self, folder, disconnect=False):

        if self.verbose > 1:
            LOG.debug("Trying to get VM folder object for path {!r}.".format(folder))

        paths = []
        parts = folder.split('/')
        for i in range(0, len(parts)):
            path = '/'.join(parts[0:i + 1])
            paths.append(path)

        try:

            if not self.service_instance:
                self.connect()

            content = self.service_instance.RetrieveContent()
            dc = self.get_obj(content, [vim.Datacenter], self.dc)
            if not dc:
                raise VSphereDatacenterNotFoundError(self.dc)
            parent_folder = dc.vmFolder
            folder_object = None

            index = 0
            last = False
            for part in parts:
                abs_path = '/' + paths[index]
                if self.verbose > 1:
                    LOG.debug("Checking single VM folder {i}: {f!r}.".format(
                        i=index, f=abs_path))
                if index == len(parts) - 1:
                    last = True

                for child in parent_folder.childEntity:
                    if not isinstance(child, vim.Folder):
                        continue
                    if child.name != part:
                        continue
                    if self.verbose > 1:
                        LOG.debug("Found VM folder {n}, parent: {p}".format(
                            n=child.name, p=parent_folder.name))
                    parent_folder = child
                    if last:
                        folder_object = child
                index += 1
                if last:
                    break

            return folder_object

        finally:
            if disconnect:
                self.disconnect()

    # -------------------------------------------------------------------------
    def ensure_vm_folder(self, folder, disconnect=False):

        LOG.debug("Ensuring existence of VSphere VM folder {!r}.".format(folder))

        paths = []
        parts = folder.split('/')
        for i in range(0, len(parts)):
            path = '/'.join(parts[0:i + 1])
            paths.append(path)

        try:

            if not self.service_instance:
                self.connect()

            content = self.service_instance.RetrieveContent()
            dc = self.get_obj(content, [vim.Datacenter], self.dc)
            if not dc:
                raise VSphereDatacenterNotFoundError(self.dc)
            root_folder = dc.vmFolder

            index = 0
            for part in parts:

                abs_path = '/' + paths[index]
                folder_object = self.get_vm_folder(paths[index], disconnect=False)
                if folder_object:
                    LOG.debug("VM Folder {!r} already exists.".format(abs_path))
                else:
                    LOG.info("Creating VM folder {!r} ...".format(abs_path))
                    if self.simulate:
                        LOG.debug("Simulation mode, don't creating it.")
                        break
                    parent_folder = root_folder
                    if index != 0:
                        parent_folder = self.get_vm_folder(paths[index - 1], disconnect=False)
                    parent_folder.CreateFolder(part)
                index += 1

        finally:
            if disconnect:
                self.disconnect()


# =============================================================================

if __name__ == "__main__":

    pass

# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 list
