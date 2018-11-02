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
import logging

# Third party modules

# Own modules
from .config import ConfigError, BaseConfiguration

__version__ = '0.1.2'
LOG = logging.getLogger(__name__)


# =============================================================================
class GetVmConfigError(ConfigError):
    """Base error class for all exceptions happened during
    execution this configured application"""

    pass


# =============================================================================
class GetVmConfiguration(BaseConfiguration):
    """
    A class for providing a configuration for the GetVmApplication class
    and methods to read it from configuration files.
    """

    default_vsphere_host = 'vcs01.ppbrln.internal'
    default_vsphere_port = 443
    default_vsphere_user = 'root'
    default_dc = 'vmcc'

    # -------------------------------------------------------------------------
    def __init__(
        self, appname=None, verbose=0, version=__version__, base_dir=None,
            encoding=None, config_dir=None, config_file=None, initialized=False):

        self.vsphere_host = self.default_vsphere_host
        self.vsphere_port = self.default_vsphere_port
        self.vsphere_user = self.default_vsphere_user
        self.dc = self.default_dc
        self.password = None

        super(GetVmConfiguration, self).__init__(
            appname=appname, verbose=verbose, version=version, base_dir=base_dir,
            encoding=encoding, config_dir=config_dir, config_file=config_file, initialized=False,
        )

        if initialized:
            self.initialized = True

    # -------------------------------------------------------------------------
    def as_dict(self, short=True):
        """
        Transforms the elements of the object into a dict

        @param short: don't include local properties in resulting dict.
        @type short: bool

        @return: structure as dict
        @rtype:  dict
        """

        res = super(GetVmConfiguration, self).as_dict(short=short)

        res['password'] = None
        if self.password:
            if self.verbose > 4:
                res['password'] = self.password
            else:
                res['password'] = '*******'

        return res

    # -------------------------------------------------------------------------
    def eval_config_section(self, config, section_name):

        super(GetVmConfiguration, self).eval_config_section(config, section_name)

        if section_name.lower() == 'vsphere':
            self._eval_config_vsphere(config, section_name)
            return

        if self.verbose > 1:
            LOG.debug("Unhandled configuration section {!r}.".format(section_name))

    # -------------------------------------------------------------------------
    def _eval_config_vsphere(self, config, section_name):

        if self.verbose > 1:
            LOG.debug("Checking config section {!r} ...".format(section_name))

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
            elif key.lower() == 'dc':
                self.dc = value

        return


# =============================================================================

if __name__ == "__main__":

    pass

# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 list
