#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: Frank Brehm
@contact: frank.brehm@pixelpark.com
@copyright: © 2019 by Frank Brehm, Berlin
@summary: A module for providing a configuration for VSPhere
"""
from __future__ import absolute_import

# Standard module
import logging

# Third party modules

# Own modules
from .config import ConfigError, BaseConfiguration

from .xlate import XLATOR

__version__ = '0.3.1'
LOG = logging.getLogger(__name__)

_ = XLATOR.gettext


# =============================================================================
class VmwareConfigError(ConfigError):
    """Base error class for all exceptions happened during
    execution this configured application"""

    pass


# =============================================================================
class VmwareConfiguration(BaseConfiguration):
    """
    A class for providing a configuration for an arbitrary Vmware Application
    and methods to read it from configuration files.
    """

    default_vsphere_port = 443
    default_vsphere_user = 'Administrator@vsphere.local'
    default_vsphere_dc = 'vmcc'

    # -------------------------------------------------------------------------
    def __init__(
        self, appname=None, verbose=0, version=__version__, base_dir=None,
            encoding=None, config_dir=None, config_file=None, initialized=False):

        self.vsphere = {}

        super(VmwareConfiguration, self).__init__(
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

        res = super(VmwareConfiguration, self).as_dict(short=short)

        res['default_vsphere_port'] = self.default_vsphere_port
        res['default_vsphere_user'] = self.default_vsphere_user
        res['default_vsphere_dc'] = self.default_vsphere_dc

        res['vsphere'] = {}
        for vsphere_name in self.vsphere.keys():
            vsphere_data = self.vsphere[vsphere_name]
            res['vsphere'][vsphere_name] = {}
            res['vsphere'][vsphere_name]['host'] = vsphere_data['host']
            res['vsphere'][vsphere_name]['port'] = vsphere_data['port']
            res['vsphere'][vsphere_name]['user'] = vsphere_data['user']
            res['vsphere'][vsphere_name]['dc'] = vsphere_data['dc']
            res['vsphere'][vsphere_name]['password'] = '*******'
            if self.verbose > 4:
                if 'password' in vsphere_data:
                    res['vsphere'][vsphere_name]['password'] = vsphere_data['password']
                else:
                    res['vsphere'][vsphere_name]['password'] = None

        return res

    # -------------------------------------------------------------------------
    def eval_config_section(self, config, section_name):

        super(VmwareConfiguration, self).eval_config_section(config, section_name)
        sn = section_name.lower()

        if sn == 'vsphere' or sn.startswith('vsphere:'):

            if sn.startswith('vsphere:'):
                vsphere_name = sn.replace('vsphere:', '').strip()
                if vsphere_name == '':
                    LOG.error(_("Empty VSpehre name found."))
                    return
            else:
                vsphere_name = '_default'

            vsphere_data = {}
            vsphere_data['port'] = self.default_vsphere_port
            vsphere_data['user'] = self.default_vsphere_user
            vsphere_data['dc'] = self.default_vsphere_dc
            vsphere_data['password'] = None

            for (key, value) in config.items(section_name):
                if key.lower() == 'host' and str(value).strip():
                    vsphere_data['host'] = value.strip().lower()
                    continue
                if key.lower() == 'dc' and str(value).strip():
                    vsphere_data['dc'] = value.strip()
                    continue
                if key.lower() == 'port':
                    vsphere_data['port'] = int(value)
                    continue
                if key.lower() == 'user' and str(value).strip():
                    vsphere_data['user'] = value.strip()
                    continue
                if key.lower() == 'password':
                    vsphere_data['password'] = value
                    continue
                LOG.warn(_("Unknown key {k!r} with value {v!r} for VSphere {vs!r} found.").format(
                    k=key, v=value, vs=vsphere_name))

            if 'host' not in vsphere_data:
                LOG.error(_("There must be a Host definition for VSphere {!r}.").format(
                    vsphere_name))
                return

            self.vsphere[vsphere_name] = vsphere_data


# =============================================================================
if __name__ == "__main__":

    pass

# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 list
