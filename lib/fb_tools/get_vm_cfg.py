#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: Frank Brehm
@contact: frank.brehm@pixelpark.com
@copyright: © 2018 by Frank Brehm, Berlin
@summary: A module for providing a configuration
"""
from __future__ import absolute_import

# Standard module
import os
import logging
import re

# Third party modules
import six

# Own modules
from fb_tools.config import ConfigError, BaseConfiguration

__version__ = '0.6.3'
LOG = logging.getLogger(__name__)


# =============================================================================
class CrTplConfigError(ConfigError):
    """Base error class for all exceptions happened during
    execution this configured application"""

    pass


# =============================================================================
class CrTplConfiguration(BaseConfiguration):
    """
    A class for providing a configuration for the CrTplApplication class
    and methods to read it from configuration files.
    """

    default_vsphere_host = 'vcs01.ppbrln.internal'
    default_vsphere_port = 443
    default_vsphere_user = 'root'
    default_vsphere_cluster = 'vmcc-l105-01'
    default_dc = 'vmcc'
    default_folder = 'templates'
    default_template_vm = 'template.pixelpark.com'
    default_template_name = 'oracle-linux-7-template'
    default_data_size_gb = 32.0
    default_num_cpus = 2
    default_ram_mb = 4 * 1024
    default_network = '192.168.88.0_23'
    default_mac_address = '00:16:3e:54:ab:2b'
    default_max_wait_for_finish_install = 60 * 60
    default_max_nr_templates_stay = 4
    default_vmware_cfg_version = 'vmx-13'
    default_os_version = 'oracleLinux7_64Guest'
    min_max_wait_for_finish_install = 3 * 60
    max_max_wait_for_finish_install = 24 * 60 * 60
    limit_max_nr_templates_stay = 100

    mac_address_template = "00:16:3e:53:{:02x}:{:02x}"

    # -------------------------------------------------------------------------
    def __init__(
        self, appname=None, verbose=0, version=__version__, base_dir=None,
            encoding=None, config_dir=None, config_file=None, initialized=False):

        self.vsphere_host = self.default_vsphere_host
        self.vsphere_port = self.default_vsphere_port
        self.vsphere_user = self.default_vsphere_user
        self.vsphere_cluster = self.default_vsphere_cluster
        self.dc = self.default_dc
        self.password = None
        self.folder = self.default_folder
        self.template_vm = self.default_template_vm
        self.template_name = self.default_template_name
        self.data_size_gb = self.default_data_size_gb
        self.num_cpus = self.default_num_cpus
        self.ram_mb = self.default_ram_mb
        self.network = self.default_network
        self.mac_address = self.default_mac_address
        self.max_wait_for_finish_install = self.default_max_wait_for_finish_install
        self.max_nr_templates_stay = self.default_max_nr_templates_stay
        self.vmware_cfg_version = self.default_vmware_cfg_version
        self.os_version = self.default_os_version

        self.excluded_datastores = []

        super(CrTplConfiguration, self).__init__(
            appname=appname, verbose=verbose, version=version, base_dir=base_dir,
            encoding=encoding, config_dir=config_dir, config_file=config_file, initialized=False,
        )

        if initialized:
            self.initialized = True

    # -------------------------------------------------------------------------
    @property
    def data_size_mb(self):
        """Size of template volume in MiB."""
        return int(self.data_size_gb * 1024.0)

    # -------------------------------------------------------------------------
    @property
    def data_size_kb(self):
        """Size of template volume in KiB."""
        return self.data_size_mb * 1024

    # -------------------------------------------------------------------------
    @property
    def data_size(self):
        """Size of template volume in Bytes."""
        return self.data_size_mb * 1024 * 1024

    # -------------------------------------------------------------------------
    @property
    def ram_gb(self):
        """Size of RAM in GiB."""
        return float(self.ram_mb) / 1024

    # -------------------------------------------------------------------------
    def as_dict(self, short=True):
        """
        Transforms the elements of the object into a dict

        @param short: don't include local properties in resulting dict.
        @type short: bool

        @return: structure as dict
        @rtype:  dict
        """

        res = super(CrTplConfiguration, self).as_dict(short=short)
        res['data_size_mb'] = self.data_size_mb
        res['data_size_kb'] = self.data_size_kb
        res['data_size'] = self.data_size
        res['ram_gb'] = self.ram_gb

        res['password'] = None
        if self.password:
            if self.verbose > 4:
                res['password'] = self.password
            else:
                res['password'] = '*******'

        return res

    # -------------------------------------------------------------------------
    def eval_config_section(self, config, section_name):

        super(CrTplConfiguration, self).eval_config_section(config, section_name)

        if section_name.lower() == 'vsphere':
            self._eval_config_vsphere(config, section_name)
            return
        if section_name.lower() == 'template':
            self._eval_config_template(config, section_name)
            return

        if self.verbose > 1:
            LOG.debug("Unhandled configuration section {!r}.".format(section_name))

    # -------------------------------------------------------------------------
    def _eval_config_vsphere(self, config, section_name):

        if self.verbose > 1:
            LOG.debug("Checking config section {!r} ...".format(section_name))

        re_excl_ds = re.compile(r'^\s*excluded?[-_]datastores?\s*$', re.IGNORECASE)
        re_split_ds = re.compile(r'[,;\s]+')

        for (key, value) in config.items(section_name):

            if key.lower() == 'host':
                self.vsphere_host = value
                continue
            elif key.lower() == 'port':
                self.vsphere_port = int(value)
                continue
            elif key.lower() == 'user':
                self.vsphere_user = value
                continue
            elif key.lower() == 'password':
                self.password = value
                continue
            elif key.lower() == 'cluster':
                self.vsphere_cluster = value
                continue
            elif key.lower() == 'folder':
                self.folder = value
            elif key.lower() == 'dc':
                self.dc = value

            elif key.lower() == 'max_nr_templates_stay':
                v = int(value)
                if v < 1:
                    LOG.error((
                        "Value {val} for max_nr_templates_stay is less than {minval}, "
                        "using {default}.").format(
                            val=v, minval=1,
                            default=self.default_max_nr_templates_stay))
                elif v >= 100:
                    LOG.error((
                        "Value {val} for max_nr_templates_stay is greater than {maxval}, "
                        "using {default}.").format(
                            val=v, maxval=100,
                            default=self.default_max_nr_templates_stay))
                else:
                    self.max_nr_templates_stay = v

            elif re_excl_ds.search(key):
                datastores = re_split_ds.split(value.strip())
                self.excluded_datastores = datastores

        return

    # -------------------------------------------------------------------------
    def _eval_config_template(self, config, section_name):

        if self.verbose > 1:
            LOG.debug("Checking config section {!r} ...".format(section_name))

        for (key, value) in config.items(section_name):
            if key.lower() == 'vm':
                self.template_vm = value
                continue
            elif key.lower() == 'name':
                self.template_name = value
            elif key.lower() == 'data_size_gb':
                self.data_size_gb = float(value)
            elif key.lower() == 'data_size_mb':
                self.data_size_gb = float(value) / 1024.0
            elif key.lower() == 'data_size_kb':
                self.data_size_gb = float(value) / 1024.0 / 1024.0
            elif key.lower() == 'data_size':
                self.data_size_gb = float(value) / 1024.0 / 1024.0 / 1024.0
            elif key.lower() == 'num_cpus':
                self.num_cpus = int(value)
            elif key.lower() == 'ram_gb':
                self.ram_mb = int(float(value) * 1024.0)
            elif key.lower() == 'ram_mb':
                self.ram_mb = int(value)
            elif key.lower() == 'network':
                self.network = value.strip()
            elif key.lower() == 'mac_address':
                v = value.strip().lower()
                if v:
                    self.mac_address = v
            elif key.lower() == 'vmware_cfg_version':
                self.vmware_cfg_version = value.strip()
            elif key.lower() == 'os_version':
                self.os_version = value.strip()
            elif key.lower() == 'max_wait_for_finish_install':
                v = float(value)
                if v < self.min_max_wait_for_finish_install:
                    LOG.error((
                        "Value {val} for max_wait_for_finish_install is less than "
                        "{minval}, using {default} seconds.").format(
                            val=v, minval=self.min_max_wait_for_finish_install,
                            default=self.default_max_wait_for_finish_install))
                elif v > self.max_max_wait_for_finish_install:
                    LOG.error((
                        "Value {val} for max_wait_for_finish_install is greater than "
                        "{maxval}, using {default} seconds.").format(
                            val=v, maxval=self.max_max_wait_for_finish_install,
                            default=self.default_max_wait_for_finish_install))
                else:
                    self.max_wait_for_finish_install = v

        return


# =============================================================================

if __name__ == "__main__":

    pass

# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 list
