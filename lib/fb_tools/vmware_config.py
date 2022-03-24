#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: Frank Brehm
@contact: frank.brehm@pixelpark.com
@copyright: © 2021 by Frank Brehm, Berlin
@summary: A module for providing a configuration for VSPhere
"""
from __future__ import absolute_import

# Standard module
import logging

# Third party modules

# Own modules

from .common import is_sequence

# from .config import ConfigError, BaseConfiguration
from .multi_config import MultiConfigError, BaseMultiConfig
from .multi_config import DEFAULT_ENCODING

from .xlate import XLATOR

__version__ = '0.4.0'
LOG = logging.getLogger(__name__)

_ = XLATOR.gettext

DEFAULT_CONFIG_DIR = 'pixelpark'


# =============================================================================
class VmwareConfigError(MultiConfigError):
    """Base error class for all exceptions happened during
    execution this configured application"""

    pass


# =============================================================================
class VmwareConfiguration(BaseMultiConfig):
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
            append_appname_to_stems=True, additional_stems=None, config_dir=DEFAULT_CONFIG_DIR,
            additional_config_file=None, additional_cfgdirs=None, encoding=DEFAULT_ENCODING,
            use_chardet=True, initialized=False):

        add_stems = []
        if additional_stems:
            if is_sequence(additional_stems):
                for stem in additional_stems:
                    add_stems.append(stem)
            else:
                add_stems.append(additional_stems)

        if 'vmware' not in add_stems:
            add_stems.append('vmware')
        if 'vsphere' not in add_stems:
            add_stems.append('vsphere')

        self.vsphere = {}

        super(VmwareConfiguration, self).__init__(
            appname=appname, verbose=verbose, version=version, base_dir=base_dir,
            append_appname_to_stems=append_appname_to_stems, config_dir=config_dir,
            additional_stems=add_stems, additional_config_file=additional_config_file,
            additional_cfgdirs=additional_cfgdirs, encoding=encoding, use_chardet=use_chardet,
            ensure_privacy=True, initialized=False,
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
    def eval_section(self, section_name):

        super(VmwareConfiguration, self).eval_section(section_name)
        sn = section_name.lower()

        if sn == 'vsphere' or sn.startswith('vsphere:'):

            section = self.cfg[section_name]

            if sn == 'vsphere':
                return self._eval_bare_vsphere(section_name, section)

            if sn.startswith('vsphere:'):
                vsphere_name = sn.replace('vsphere:', '').strip()
                return self._eval_vsphere_instance(section_name, vsphere_name, section)

            LOG.error(_("Empty VSphere name found."))

    # -------------------------------------------------------------------------
    def _eval_vsphere_instance(self, section_name, vsphere_name, section):

        vsphere_data = {}
        vsphere_data['port'] = self.default_vsphere_port
        vsphere_data['user'] = self.default_vsphere_user
        vsphere_data['dc'] = self.default_vsphere_dc
        vsphere_data['password'] = None

        for key in section.keys():

            value = section[key]

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

            msg = _(
                "Unknown key {k!r} with value {v!r} for VSphere {vs!r} in section "
                "{sec!r} found.").format(k=key, v=value, vs=vsphere_name, sec=section_name)
            LOG.warn(msg)

        if 'host' not in vsphere_data:
            LOG.error(_("There must be a Host definition for VSphere {!r}.").format(vsphere_name))
            return

        self.vsphere[vsphere_name] = vsphere_data

    # -------------------------------------------------------------------------
    def _eval_bare_vsphere(self, section_name, section):

        for vsphere_name in section.keys():
            sub_section = section[vsphere_name]
            vs_name = vsphere_name.strip()
            self._eval_vsphere_instance(section_name, vs_name, sub_section)


# =============================================================================
if __name__ == "__main__":

    pass

# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 list
