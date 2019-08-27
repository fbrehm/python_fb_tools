#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: Frank Brehm
@contact: frank.brehm@pixelpark.com
@copyright: © 2019 by Frank Brehm, Berlin
@summary: The module for a VSphere host system object.
"""
from __future__ import absolute_import

# Standard modules
import logging
import datetime

# Third party modules
from pyVmomi import vim

# Own modules
from ..xlate import XLATOR

from ..common import pp, to_bool

from ..obj import FbBaseObject

from .object import VsphereObject

__version__ = '0.3.1'
LOG = logging.getLogger(__name__)


_ = XLATOR.gettext


# =============================================================================
class VsphereHostBiosInfo(FbBaseObject):

    # -------------------------------------------------------------------------
    def __init__(
        self, bios_version=None, fw_major=None, fw_minor=None, major=None, minor=None,
            release_date=None, vendor=None, appname=None, verbose=0, version=__version__,
            base_dir=None, initialized=None):

        self._bios_version = None
        self._fw_major = None
        self._fw_minor = None
        self._major = None
        self._minor = None
        self._release_date = None
        self._vendor = None

        super(VsphereHostBiosInfo, self).__init__(
            appname=appname, verbose=verbose, version=version, base_dir=base_dir)

        self.bios_version = bios_version
        self.fw_major = fw_major
        self.fw_minor = fw_minor
        self.major = major
        self.minor = minor
        self.release_date = release_date
        self.vendor = vendor

        if initialized is not None:
            self.initialized = initialized

    # -----------------------------------------------------------
    @property
    def bios_version(self):
        """The BIOS name of the host."""
        return self._bios_version

    @bios_version.setter
    def bios_version(self, value):
        if value is None:
            self._bios_version = None
            return
        v = str(value).strip()
        if v == '':
            self._bios_version = None
        else:
            self._bios_version = v

    # -----------------------------------------------------------
    @property
    def fw_major(self):
        """The major version of the firmware of the BIOS of the host."""
        return self._fw_major

    @fw_major.setter
    def fw_major(self, value):
        if value is None:
            self._fw_major = None
            return
        v = str(value).strip()
        if v == '':
            self._fw_major = None
        else:
            self._fw_major = v

    # -----------------------------------------------------------
    @property
    def fw_minor(self):
        """The minor version of the firmware of the BIOS of the host."""
        return self._fw_minor

    @fw_minor.setter
    def fw_minor(self, value):
        if value is None:
            self._fw_minor = None
            return
        v = str(value).strip()
        if v == '':
            self._fw_minor = None
        else:
            self._fw_minor = v

    # -----------------------------------------------------------
    @property
    def major(self):
        """The major version of the BIOS of the host."""
        return self._major

    @major.setter
    def major(self, value):
        if value is None:
            self._major = None
            return
        v = str(value).strip()
        if v == '':
            self._major = None
        else:
            self._major = v

    # -----------------------------------------------------------
    @property
    def minor(self):
        """The minor version of the BIOS of the host."""
        return self._minor

    @minor.setter
    def minor(self, value):
        if value is None:
            self._minor = None
            return
        v = str(value).strip()
        if v == '':
            self._minor = None
        else:
            self._minor = v

    # -----------------------------------------------------------
    @property
    def release_date(self):
        """The release date of the BIOS of the host."""
        return self._release_date

    @release_date.setter
    def release_date(self, value):
        if value is None:
            self._release_date = None
            return
        if isinstance(value, (datetime.datetime, datetime.date)):
            self._release_date = value
            return
        v = str(value).strip()
        if v == '':
            self._release_date = None
        else:
            self._release_date = v

    # -----------------------------------------------------------
    @property
    def vendor(self):
        """The vendor of the BIOS of the host."""
        return self._vendor

    @vendor.setter
    def vendor(self, value):
        if value is None:
            self._vendor = None
            return
        v = str(value).strip()
        if v == '':
            self._vendor = None
        else:
            self._vendor = v

    # -------------------------------------------------------------------------
    def as_dict(self, short=True):
        """
        Transforms the elements of the object into a dict

        @param short: don't include local properties in resulting dict.
        @type short: bool

        @return: structure as dict
        @rtype:  dict
        """

        res = super(VsphereHostBiosInfo, self).as_dict(short=short)
        res['bios_version'] = self.bios_version
        res['fw_major'] = self.fw_major
        res['fw_minor'] = self.fw_minor
        res['major'] = self.major
        res['minor'] = self.minor
        res['release_date'] = self.release_date
        res['vendor'] = self.vendor

        return res

    # -------------------------------------------------------------------------
    def __copy__(self):

        return VsphereHostBiosInfo(
            appname=self.appname, verbose=self.verbose, base_dir=self.base_dir,
            initialized=self.initialized, bios_version=self.bios_version,
            fw_major=self.fw_major, fw_minor=self.fw_minor, major=self.major, minor=self.minor,
            release_date=self.release_date, vendor=self.vendor)

    # -------------------------------------------------------------------------
    @classmethod
    def from_summary(cls, data, appname=None, verbose=0, base_dir=None):

        if not isinstance(data, vim.host.BIOSInfo):
            msg = _("Parameter {t!r} must be a {e}, {v!r} ({vt}) was given.").format(
                t='data', e='vim.host.BIOSInfo', v=data, vt=data.__class__.__name__)
            raise TypeError(msg)

        params = {
            'appname': appname,
            'verbose': verbose,
            'base_dir': base_dir,
            'initialized': True,
            'bios_version': data.biosVersion,
            'release_date': data.releaseDate,
        }
        if hasattr(data, 'firmwareMajorRelease'):
            params['fw_major'] = data.firmwareMajorRelease
        if hasattr(data, 'firmwareMinorRelease'):
            params['fw_minor'] = data.firmwareMinorRelease
        if hasattr(data, 'majorRelease'):
            params['major'] = data.majorRelease
        if hasattr(data, 'minorRelease'):
            params['minor'] = data.minorRelease
        if hasattr(data, 'vendor'):
            params['vendor'] = data.vendor

        if verbose > 2:
            LOG.debug(_("Creating {} object from:").format(cls.__name__) + '\n' + pp(params))

        bios = cls(**params)

        return bios


# =============================================================================
class VsphereHost(VsphereObject):

    # -------------------------------------------------------------------------
    def __init__(
        self, appname=None, verbose=0, version=__version__, base_dir=None, initialized=None,
            name=None, cluster_name=None, status='gray', config_status='gray'): 

        self.repr_fields = ('name', )
        self._cluster_name = None
        self.bios = None
        self.cpu_speed = None
        self.cpu_cores = None
        self.cpu_pkgs = None
        self.cpu_threads = None
        self.memory = None

        super(VsphereHost, self).__init__(
            name=name, obj_type='vsphere_host', name_prefix="host", status=status,
            config_status=config_status, appname=appname, verbose=verbose,
            version=version, base_dir=base_dir)

        self.cluster_name = cluster_name

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
    def memory_mb(self):
        "The RAM of the host in MiByte."
        if self.memory is None:
            return None
        return int(self.memory / 1024 / 1024)

    # -----------------------------------------------------------
    @property
    def memory_gb(self):
        "The RAM of the host in GiByte."
        if self.memory is None:
            return None
        return float(self.memory) / 1024.0 / 1024.0 / 1024.0

    # -------------------------------------------------------------------------
    def as_dict(self, short=True):
        """
        Transforms the elements of the object into a dict

        @param short: don't include local properties in resulting dict.
        @type short: bool

        @return: structure as dict
        @rtype:  dict
        """

        res = super(VsphereHost, self).as_dict(short=short)
        res['cluster_name'] = self.cluster_name
        res['memory_mb'] = self.memory_mb
        res['memory_gb'] = self.memory_gb
        if self.bios is not None:
            res['bios'] = self.bios.as_dict(short=short)

        return res

    # -------------------------------------------------------------------------
    def __copy__(self):

        host = VsphereHost(
            appname=self.appname, verbose=self.verbose, base_dir=self.base_dir,
            initialized=self.initialized, name=self.name, status=self.status,
            config_status=self.config_status, cluster_name=self.cluster_name)

        if self.bios:
            host.bios = copy.copy(self.bios)
        host.cpu_speed = self.cpu_speed
        host.cpu_cores = self.cpu_cores
        host.cpu_pkgs = self.cpu_pkgs
        host.cpu_threads = self.cpu_threads
        host.memory = self.memory

        return host

    # -------------------------------------------------------------------------
    def __eq__(self, other):

        if self.verbose > 4:
            LOG.debug(_("Comparing {} objects ...").format(self.__class__.__name__))

        if not isinstance(other, VsphereHost):
            return False

        if self.name != other.name:
            return False

        return True

    # -------------------------------------------------------------------------
    @classmethod
    def from_summary(cls, data, appname=None, verbose=0, base_dir=None, cluster_name=None):

        if not isinstance(data, vim.HostSystem):
            msg = _("Parameter {t!r} must be a {e}, {v!r} ({vt}) was given.").format(
                t='data', e='vim.HostSystem', v=data, vt=data.__class__.__name__)
            raise TypeError(msg)

        params = {
            'appname': appname,
            'verbose': verbose,
            'base_dir': base_dir,
            'initialized': True,
            'name': data.summary.config.name,
            'cluster_name': cluster_name,
            'status': 'gray',
            'config_status': 'green',
        }

        if verbose > 2:
            LOG.debug(_("Creating {} object from:").format(cls.__name__) + '\n' + pp(params))

        host = cls(**params)

        host.bios = VsphereHostBiosInfo.from_summary(
            data.hardware.biosInfo, appname=appname, verbose=verbose, base_dir=base_dir)

        host.cpu_speed = data.hardware.cpuInfo.hz
        host.cpu_cores = data.hardware.cpuInfo.numCpuCores
        host.cpu_pkgs = data.hardware.cpuInfo.numCpuPackages
        host.cpu_threads = data.hardware.cpuInfo.numCpuThreads
        host.memory = data.hardware.memorySize

        return host


# =============================================================================
if __name__ == "__main__":

    pass

# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 list
