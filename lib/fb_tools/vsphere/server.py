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
import time
import datetime

from numbers import Number

from collections import Sequence

# Third party modules
from pyVmomi import vim, vmodl
import requests
import urllib3

# Own modules
from ..common import pp, RE_TF_NAME

from ..errors import HandlerError

from . import BaseVsphereHandler, DEFAULT_TZ_NAME
from . import DEFAULT_HOST, DEFAULT_PORT, DEFAULT_USER, DEFAULT_DC, DEFAULT_CLUSTER

from .cluster import VsphereCluster

from .ds import VsphereDatastore, VsphereDatastoreDict

from .ds_cluster import VsphereDsCluster, VsphereDsClusterDict

from .network import VsphereNetwork, VsphereNetworkDict

from .iface import VsphereVmInterface

from .errors import VSphereExpectedError, TimeoutCreateVmError, VSphereVmNotFoundError
from .errors import VSphereDatacenterNotFoundError, VSphereNoDatastoresFoundError

__version__ = '0.9.7'
LOG = logging.getLogger(__name__)

DEFAULT_OS_VERSION = 'oracleLinux7_64Guest'
DEFAULT_VM_CFG_VERSION = 'vmx-13'

# =============================================================================
class VsphereServer(BaseVsphereHandler):
    """
    Class for a VSphere server handler object.
    """

    re_local_ds = re.compile(r'^local[_-]', re.IGNORECASE)
    vmw_api_version_to_hw_version = {
        '5.0': 8,
        '5.1': 9,
        '5.5': 10,
        '6.0': 11,
        '6.5': 13,
        '6.7': 14,
    }

    # -------------------------------------------------------------------------
    def __init__(
        self, appname=None, verbose=0, version=__version__, base_dir=None,
            host=DEFAULT_HOST, port=DEFAULT_PORT, user=DEFAULT_USER, password=None,
            dc=DEFAULT_DC, cluster=DEFAULT_CLUSTER, auto_close=True, simulate=None,
            force=None, terminal_has_colors=False, tz=DEFAULT_TZ_NAME, initialized=False):

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
            terminal_has_colors=terminal_has_colors, tz=tz, initialized=False,
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
            self.about['max_hw_version'] = None
            if 'apiVersion' in self.about:
                api_version = self.about['apiVersion']
                if api_version in self.vmw_api_version_to_hw_version:
                    hw_version = self.vmw_api_version_to_hw_version[api_version]
                    self.about['max_hw_version'] = 'vmx-{}'.format(hw_version)
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
        if self.verbose > 1:
            LOG.debug("Found VSphere about-information:\n{}".format(pp(self.about)))

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
    def get_datastores(self, disconnect=False):

        LOG.debug("Trying to get all datastores from VSphere ...")
        self.datastores = VsphereDatastoreDict()
        self.ds_mapping = {}

        try:

            if not self.service_instance:
                self.connect()

            content = self.service_instance.RetrieveContent()
            dc = self.get_obj(content, [vim.Datacenter], self.dc)
            if not dc:
                raise VSphereDatacenterNotFoundError(self.dc)
            for child in dc.datastoreFolder.childEntity:
                self._get_datastores(child)

        finally:
            if disconnect:
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
    def get_ds_clusters(self, disconnect=False):

        LOG.debug("Trying to get all datastore clusters from VSphere ...")
        self.ds_clusters = VsphereDsClusterDict()
        self.ds_cluster_mapping = {}

        try:

            if not self.service_instance:
                self.connect()

            content = self.service_instance.RetrieveContent()
            dc = self.get_obj(content, [vim.Datacenter], self.dc)
            if not dc:
                raise VSphereDatacenterNotFoundError(self.dc)
            for child in dc.datastoreFolder.childEntity:
                self._get_ds_clusters(child)

        finally:
            if disconnect:
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
    def get_networks(self, disconnect=False):

        LOG.debug("Trying to get all networks from VSphere ...")
        self.networks = VsphereNetworkDict()
        self.network_mapping = {}

        try:

            if not self.service_instance:
                self.connect()

            content = self.service_instance.RetrieveContent()
            dc = self.get_obj(content, [vim.Datacenter], self.dc)
            if not dc:
                raise VSphereDatacenterNotFoundError(self.dc)
            for child in dc.networkFolder.childEntity:
                self._get_networks(child)

        finally:
            if disconnect:
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
    def get_vm(self, vm_name, no_error=False, disconnect=False, as_vmw_obj=False):

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
                path = child.name
                if self.verbose > 1:
                    LOG.debug("Searching in path {!r} ...".format(path))
                vm = self._get_vm(child, vm_name, as_vmw_obj=as_vmw_obj)
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
    def _get_vm(self, child, vm_name, cur_path='', depth=1, as_vmw_obj=False):

        vm = None

        if self.verbose > 2:
            LOG.debug("Searching in path {!r} ...".format(cur_path))
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
                vm = self._get_vm(sub_child, vm_name, child_path, depth + 1, as_vmw_obj=as_vmw_obj)
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
                if as_vmw_obj:
                    return child
                vm_info = {}
                vm_info['name'] = vm_config.name
                vm_info['tf_name'] = 'vm_' + RE_TF_NAME.sub('_', vm_config.name.lower())
                vm_info['cluster'] = None
                if child.resourcePool:
                    vm_info['cluster'] = child.resourcePool.owner.name
                vm_info['path'] = cur_path
                vm_info['memorySizeMB'] = vm_config.memorySizeMB
                vm_info['numCpu'] = vm_config.numCpu
                vm_info['numEthernetCards'] = vm_config.numEthernetCards
                vm_info['numVirtualDisks'] = vm_config.numVirtualDisks
                vm_info['template'] = vm_config.template
                vm_info['guestFullName'] = vm_config.guestFullName
                vm_info['guestId'] = vm_config.guestId
                vm_info['vm_tools'] = {}
                if child.guest:
                    vm_info['vm_tools']['install_type'] = None
                    if hasattr(child.guest, 'toolsInstallType'):
                        vm_info['vm_tools']['install_type'] = child.guest.toolsInstallType
                    vm_info['vm_tools']['state'] = None
                    if hasattr(child.guest, 'toolsRunningStatus'):
                        vm_info['vm_tools']['state'] = child.guest.toolsRunningStatus
                    else:
                        vm_info['vm_tools']['state'] = child.guest.toolsStatus
                    vm_info['vm_tools']['version'] = child.guest.toolsVersion
                    vm_info['vm_tools']['version_state'] = None
                    if hasattr(child.guest, 'toolsVersionStatus2'):
                        vm_info['vm_tools']['version_state'] = child.guest.toolsVersionStatus2
                    else:
                        vm_info['vm_tools']['version_state'] = child.guest.toolsVersionStatus
                vm_info['host'] = None
                if child.runtime.host:
                    vm_info['host'] = child.runtime.host.name
                vm_info['instanceUuid'] = vm_config.instanceUuid
                vm_info['power_state'] = child.runtime.powerState
                if vm_config.instanceUuid:
                    vm_info['instanceUuid'] = uuid.UUID(vm_config.instanceUuid)
                vm_info['uuid'] = vm_config.uuid
                if vm_config.uuid:
                    vm_info['uuid'] = uuid.UUID(vm_config.uuid)
                vm_info['vmPathName'] = vm_config.vmPathName
                vm_info['cfg_version'] = child.config.version
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
    def get_vms(self, re_name, is_template=None, disconnect=False):

        if not hasattr(re_name, 'match'):
            raise TypeError("Parameter 're_name' => {!r} seems not to be a regex object.".format(
                re_name))

        LOG.debug("Trying to get list of VMs with name pattern {!r}.".format(re_name.pattern))
        vm_list = []

        try:
            if not self.service_instance:
                self.connect()

            content = self.service_instance.RetrieveContent()
            dc = self.get_obj(content, [vim.Datacenter], self.dc)
            if not dc:
                raise VSphereDatacenterNotFoundError(self.dc)

            for child in dc.vmFolder.childEntity:
                path = child.name
                if self.verbose > 1:
                    LOG.debug("Searching in path {!r} ...".format(path))
                vms = self._get_vms(child, re_name, is_template=is_template)
                if vms:
                    vm_list += vms

        finally:
            if disconnect:
                self.disconnect()

        LOG.debug("Found {no} VMs with pattern {p!r}.".format(
            no=len(vm_list), p=re_name.pattern))

        return vm_list

    # -------------------------------------------------------------------------
    def _get_vms(self, child, re_name, is_template=None, depth=1):

        vm_list = []

        if self.verbose > 3:
            LOG.debug("Found a {} child.".format(child.__class__.__name__))

        if hasattr(child, 'childEntity'):
            if depth > self.max_search_depth:
                return vms
            for sub_child in child.childEntity:
                vms = self._get_vms(sub_child, re_name, is_template, depth + 1)
                if vms:
                    vm_list += vms
            return vm_list

        if isinstance(child, vim.VirtualMachine):

            summary = child.summary
            vm_config = summary.config
            vm_name = vm_config.name

            if self.verbose > 2:
                LOG.debug("Checking VM {!r}...".format(vm_name))
            if is_template is not None:
                if self.verbose > 2:
                    not_tpl = ''
                    if not is_template:
                        not_tpl = 'not '
                    LOG.debug("Checking VM {name!r} for being {no}a template ...".format(
                        name=vm_name, no=not_tpl))
                if is_template and not vm_config.template:
                    return []
                if not is_template and vm_config.template:
                    return []

            if self.verbose > 2:
                LOG.debug("Checking VM {!r} for pattern.".format(vm_name))
            if re_name.search(vm_name):
                if self.verbose > 2:
                    LOG.debug("Found VM {!r}.".format(vm_name))
                vm_list.append(child)

        return vm_list

    # -------------------------------------------------------------------------
    def poweron_vm(self, vm, max_wait=20, disconnect=False):

        try:

            if not self.service_instance:
                self.connect()

            if isinstance(vm, vim.VirtualMachine):
                vm_obj = vm
                vm_name = vm.summary.config.name
            else:
                vm_name = vm
                vm_obj = self.get_vm(vm, as_vmw_obj=True)
                if not vm_obj:
                    raise VSphereVmNotFoundError(vm)

            if vm_obj.runtime.powerState.lower() == 'poweredon':
                LOG.info("VM {!r} is already powered on.".format(vm_name))
                return

            LOG.info("Powering on VM {!r} ...".format(vm_name))

            task = vm_obj.PowerOnVM_Task()
            self.wait_for_tasks([task], max_wait=max_wait)
            LOG.debug("VM {!r} successful powered on.".format(vm_name))

        finally:
            if disconnect:
                self.disconnect()

    # -------------------------------------------------------------------------
    def poweroff_vm(self, vm, max_wait=20, disconnect=False):

        try:

            if not self.service_instance:
                self.connect()

            if isinstance(vm, vim.VirtualMachine):
                vm_obj = vm
                vm_name = vm.summary.config.name
            else:
                vm_name = vm
                vm_obj = self.get_vm(vm, as_vmw_obj=True)
                if not vm_obj:
                    raise VSphereVmNotFoundError(vm)

            if vm_obj.runtime.powerState.lower() == 'poweredoff':
                LOG.info("VM {!r} is already powered off.".format(vm_name))
                return

            LOG.info("Powering off VM {!r} ...".format(vm_name))

            task = vm_obj.PowerOffVM_Task()
            self.wait_for_tasks([task], max_wait=max_wait)
            LOG.debug("VM {!r} successful powered off.".format(vm_name))

        finally:
            if disconnect:
                self.disconnect()

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

    # -------------------------------------------------------------------------
    def wait_for_tasks(
            self, tasks, poll_time=0.1, disconnect=False, max_wait=None, start_time=None):

        LOG.debug("Waiting for tasks to finish ...")
        if not start_time:
            start_time = time.time()

        try:

            if not self.service_instance:
                self.connect()

            property_collector = self.service_instance.content.propertyCollector
            task_list = [str(task) for task in tasks]
            if max_wait:
                LOG.debug("Waiting at most {m} seconds for tasks {t} to finish ...".format(
                    m=max_wait, t=task_list))
            else:
                LOG.debug("Waiting for tasks {} to finish ...".format(task_list))
            # Create filter
            obj_specs = [vmodl.query.PropertyCollector.ObjectSpec(obj=task) for task in tasks]
            property_spec = vmodl.query.PropertyCollector.PropertySpec(
                type=vim.Task, pathSet=[], all=True)
            filter_spec = vmodl.query.PropertyCollector.FilterSpec()
            filter_spec.objectSet = obj_specs
            filter_spec.propSet = [property_spec]
            pcfilter = property_collector.CreateFilter(filter_spec, True)
            try:
                version, state = None, None
                # Loop looking for updates till the state moves to a completed state.
                while len(task_list):
                    update = property_collector.WaitForUpdates(version)
                    for filter_set in update.filterSet:
                        if max_wait is not None and max_wait > 0:
                            time_diff = time.time() - start_time
                            if time_diff >= max_wait:
                                return False
                        time.sleep(poll_time)
                        LOG.debug("Waiting ...")
                        for obj_set in filter_set.objectSet:
                            task = obj_set.obj
                            for change in obj_set.changeSet:
                                if change.name == 'info':
                                    state = change.val.state
                                elif change.name == 'info.state':
                                    state = change.val
                                else:
                                    continue

                                if not str(task) in task_list:
                                    continue

                                if state == vim.TaskInfo.State.success:
                                    # Remove task from taskList
                                    task_list.remove(str(task))
                                elif state == vim.TaskInfo.State.error:
                                    raise task.info.error
                        # Move to next version
                    version = update.version
            finally:
                if pcfilter:
                    pcfilter.Destroy()

        finally:
            if disconnect:
                self.disconnect()

        return True

    # -------------------------------------------------------------------------
    def create_vm(self, name, vm_folder, vm_config_spec, pool, max_wait=5):

        LOG.info("Creating VM {!r} ...".format(name))

        if self.simulate:
            LOG.info("Simulation mode - VM {!r} will not be created.".format(name))
            return

        start_time = time.time()

        task = vm_folder.CreateVM_Task(config=vm_config_spec, pool=pool)

        if not self.wait_for_tasks(
                [task], poll_time=0.2, max_wait=max_wait, start_time=start_time):
            time_diff = time.time() - start_time
            raise TimeoutCreateVmError(name, time_diff)

    # -------------------------------------------------------------------------
    def generate_vm_create_spec(
        self, name, datastore, disks=None, nw_interfaces=None, graphic_ram_mb=256,
            videao_ram_mb=32, boot_delay_secs=3, ram_mb=1024, num_cpus=1, ds_with_timestamp=False,
            os_version=DEFAULT_OS_VERSION, cfg_version=DEFAULT_VM_CFG_VERSION):

        LOG.debug("Generating create spec for VM {!r} ...".format(name))

        # File definitions
        datastore_path = '[{ds}] {name}'.format(ds=datastore, name=name)
        if ds_with_timestamp:
            tstamp = datetime.datetime.now(tz=self.tz).strftime('%Y-%m-%d_%H-%M')
            datastore_path += '-' + tstamp
        datastore_path += '/'
        LOG.debug("Datastore path: {!r}".format(datastore_path))

        vm_path_name = datastore_path + name + '.vmx'
        LOG.debug("VM path name: {!r}".format(vm_path_name))

        vm_file_info = vim.vm.FileInfo(
            logDirectory=datastore_path, snapshotDirectory=datastore_path,
            suspendDirectory=datastore_path, vmPathName=vm_path_name)

        # Device definitions
        dev_changes = []

        dev_changes += self.generate_disk_spec(datastore_path, disks)
        dev_changes += self.generate_if_create_spec(nw_interfaces)

        # Graphic Card
        video_spec = vim.vm.device.VirtualDeviceSpec()
        video_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
        video_spec.device = vim.vm.device.VirtualVideoCard()
        video_spec.device.enable3DSupport = False
        video_spec.device.graphicsMemorySizeInKB = graphic_ram_mb * 1024
        video_spec.device.numDisplays = 1
        video_spec.device.use3dRenderer = 'automatic'
        video_spec.device.videoRamSizeInKB = videao_ram_mb * 1024

        dev_changes.append(video_spec)

        # Some other flags
        vm_flags = vim.vm.FlagInfo()
        vm_flags.diskUuidEnabled = True

        # Some extra options and properties
        extra_opts = []
        created_opt = vim.option.OptionValue()
        created_opt.key = 'created'
        created_opt.value = int(time.time())
        extra_opts.append(created_opt)

        # Set waiting for 3 second in BIOS before booting
        boot_opts = vim.vm.BootOptions()
        boot_opts.bootDelay = boot_delay_secs * 1000
        boot_opts.bootRetryEnabled = False
        boot_opts.enterBIOSSetup = False

        # Creating ConfigSpec
        config = vim.vm.ConfigSpec(
            name=name, deviceChange=dev_changes, flags=vm_flags, extraConfig=extra_opts,
            memoryMB=ram_mb, memoryHotAddEnabled=True, numCPUs=num_cpus,
            cpuHotAddEnabled=True, cpuHotRemoveEnabled=True, files=vm_file_info,
            guestId=os_version, version=cfg_version, bootOptions=boot_opts,
        )

        if self.verbose > 1:
            LOG.debug("Generated VM config:\n{}".format(pp(config)))

        return config

    # -------------------------------------------------------------------------
    def generate_disk_spec(self, datastore_path, disks=None):

        disk_sizes2create = []
        if disks:
            err_msg_tpl = "Given disksize {!r} must be greater than zero."
            if isinstance(disks, Number):
                if disks <= 0:
                    raise ValueError(err_msg_tpl.format(disks))
                disk_sizes2create.append(int(disks))
            elif isinstance(disks, Sequence):
                if isinstance(disks, str):
                    size = int(disks)
                    if size <= 0:
                        raise ValueError(err_msg_tpl.format(disks))
                    disk_sizes2create.append(size)
                else:
                    if len(disks) > 6:
                        msg = "There may be created at most 6 disks, but {} were given.".format(
                            len(disks))
                    for disk in disks:
                        size = int(disk)
                        if size <= 0:
                            raise ValueError(err_msg_tpl.format(disk))
                        disk_sizes2create.append(size)

        if self.verbose > 1:
            if disk_sizes2create:
                LOG.debug("Generating spec for SCSI controller and {n} disks: {d}.".format(
                    n=len(disk_sizes2create), d=pp(disk_sizes2create)))
            else:
                LOG.debug("Generating spec for SCSI controller without disks.")

        dev_changes = []

        # Creating SCSI Controller
        scsi_ctr_spec = vim.vm.device.VirtualDeviceSpec()
        scsi_ctr_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
        scsi_ctr_spec.device = vim.vm.device.VirtualLsiLogicController()
        scsi_ctr_spec.device.key = 0
        scsi_ctr_spec.device.unitNumber = 1
        scsi_ctr_spec.device.sharedBus = 'noSharing'
        controller = scsi_ctr_spec.device

        dev_changes.append(scsi_ctr_spec)

        # Creating disks

        i = 0
        letter = 'a'

        for size in disk_sizes2create:

            size_kb = size * 1024 * 1024
            if self.verbose > 1:
                dname = "sd{}".format(letter)
                LOG.debug("Adding spec for disk {n!r} with {gb} GiB => {kb} KiByte.".format(
                    n=dname, gb=size, kb=size_kb))

            disk_spec = vim.vm.device.VirtualDeviceSpec()
            disk_spec.fileOperation = "create"
            disk_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
            disk_spec.device = vim.vm.device.VirtualDisk()
            disk_spec.device.backing = vim.vm.device.VirtualDisk.FlatVer2BackingInfo()
            disk_spec.device.backing.diskMode = 'persistent'
            disk_spec.device.backing.fileName = '{p}template-sd{l}.vmdk'.format(
                p=datastore_path, l=letter)
            disk_spec.device.unitNumber = i
            # disk_spec.device.key = 1
            disk_spec.device.capacityInKB = size_kb
            disk_spec.device.controllerKey = controller.key

            dev_changes.append(disk_spec)

            i += 1
            letter = chr(ord(letter) + 1)

        return dev_changes

    # -------------------------------------------------------------------------
    def generate_if_create_spec(self, nw_interfaces=None):

        if not nw_interfaces:
            return []

        ifaces = []
        if isinstance(nw_interfaces, VsphereVmInterface):
            ifaces.append(nw_interfaces)
        else:
            for iface in nw_interfaces:
                if not isinstance(iface, VsphereVmInterface):
                    msg = "Invalid Interface description {!r} given.".format(iface)
                    raise TypeError(msg)
                ifaces.append(iface)

        dev_changes = []
        dev_name = "eth{}"
        i = 0

        for iface in ifaces:

            if self.verbose > 2:
                LOG.debug("Defined interface:\n{}".format(pp(iface.as_dict())))

            dname = dev_name.format(i)
            if self.verbose > 1:
                LOG.debug((
                    "Adding spec for network interface {d!r} (Network {n!r}, "
                    "MAC: {m!r}, summary: {s!r}).").format(
                    d=dname, n=iface.network_name, m=iface.mac_address,
                    s=iface.summary))

            nic_spec = vim.vm.device.VirtualDeviceSpec()
            nic_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
            nic_spec.device = vim.vm.device.VirtualVmxnet3()
            nic_spec.device.deviceInfo = vim.Description()
            nic_spec.device.deviceInfo.label = dname
            if iface.summary:
                nic_spec.device.deviceInfo.summary = iface.summary

            nic_spec.device.backing = vim.vm.device.VirtualEthernetCard.NetworkBackingInfo()
            nic_spec.device.backing.useAutoDetect = False
            nic_spec.device.backing.network = iface.network
            nic_spec.device.backing.deviceName = iface.network_name

            nic_spec.device.connectable = vim.vm.device.VirtualDevice.ConnectInfo()
            nic_spec.device.connectable.startConnected = True
            nic_spec.device.connectable.allowGuestControl = True
            nic_spec.device.wakeOnLanEnabled = True
            if iface.mac_address:
                nic_spec.device.addressType = 'assigned'
                nic_spec.device.macAddress = iface.mac_address
            else:
                nic_spec.device.addressType = 'generated'

            dev_changes.append(nic_spec)

        return dev_changes

    # -------------------------------------------------------------------------
    def purge_vm(self, vm, max_wait=20, disconnect=False):

        try:

            if not self.service_instance:
                self.connect()

            if isinstance(vm, vim.VirtualMachine):
                vm_obj = vm
                vm_name = vm.summary.config.name
            else:
                vm_name = vm
                vm_obj = self.get_vm(vm, as_vmw_obj=True)
                if not vm_obj:
                    raise VSphereVmNotFoundError(vm)

            self.poweroff_vm(vm_obj)

            LOG.info("Purging VM {!r} ...".format(vm_name))

            task = vm_obj.Destroy_Task()
            self.wait_for_tasks([task], max_wait=max_wait)
            LOG.debug("VM {!r} successful removed.".format(vm_name))

        finally:
            if disconnect:
                self.disconnect()

    # -------------------------------------------------------------------------
    def set_mac_of_nic(self, vm, new_mac, nic_nr=0):

        if not self.service_instance:
            self.connect()

        if isinstance(vm, vim.VirtualMachine):
            vm_obj = vm
            vm_name = vm.summary.config.name
        else:
            vm_name = vm
            vm_obj = self.get_vm(vm, as_vmw_obj=True)
            if not vm_obj:
                raise VSphereVmNotFoundError(vm)

        i = 0
        virtual_nic_device = None
        for dev in vm_obj.config.hardware.device:
            if isinstance(dev, vim.vm.device.VirtualEthernetCard):
                if i == nic_nr:
                    virtual_nic_device = dev
                    break
                i += 1

        if not virtual_nic_device:
            msg = (
                "Did not found virtual ethernet device No. {no} ("
                "found {count} devices).").format(no=nic_nr, count=i)
            raise HandlerError(msg)

        virtual_nic_spec = vim.vm.device.VirtualDeviceSpec()
        virtual_nic_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.edit
        virtual_nic_spec.device = virtual_nic_device
        virtual_nic_spec.device.macAddress = new_mac
        virtual_nic_spec.device.backing = virtual_nic_device.backing
        virtual_nic_spec.device.wakeOnLanEnabled = virtual_nic_device.wakeOnLanEnabled
        virtual_nic_spec.device.connectable = virtual_nic_device.connectable

        dev_changes = []
        dev_changes.append(virtual_nic_spec)
        spec = vim.vm.ConfigSpec()
        spec.deviceChange = dev_changes

        if self.verbose > 2:
            LOG.debug("Changes of MAC address:\n{}".format(pp(spec)))

        task = vm_obj.ReconfigVM_Task(spec=spec)
        self.wait_for_tasks([task])
        LOG.debug("Successful changed MAC address of VM {v!r} to {m!r}..".format(
            v=vm_name, m=new_mac))


# =============================================================================

if __name__ == "__main__":

    pass

# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 list
