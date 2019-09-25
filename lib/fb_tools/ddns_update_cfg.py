#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: Frank Brehm
@contact: frank@brehm-online.com
@copyright: © 2019 by Frank Brehm, Berlin
@summary: A module for providing a configuration for the ddns-update script
"""
from __future__ import absolute_import

# Standard module
import logging
import re
from pathlib import Path

# Third party modules

# Own modules
from .common import to_bool

from .config import ConfigError, BaseConfiguration

from .xlate import XLATOR, format_list

__version__ = '0.2.1'

LOG = logging.getLogger(__name__)

_ = XLATOR.gettext


# =============================================================================
class DdnsUpdateConfigError(ConfigError):
    """Base error class for all exceptions happened during
    execution this configured application"""

    pass


# =============================================================================
class DdnsUpdateConfiguration(BaseConfiguration):
    """
    A class for providing a configuration for the GetVmApplication class
    and methods to read it from configuration files.
    """

    default_working_dir = Path('/var/lib/ddns')
    default_logfile = Path('/var/log/ddnss/ddnss-update.log')

    default_get_ipv4_url = 'http://ip4.ddnss.de/jsonip.php'
    default_get_ipv6_url = 'http://ip6.ddnss.de/jsonip.php'
    default_upd_ipv4_url = 'http://ip4.ddnss.de/upd.php'
    default_upd_ipv6_url = 'http://ip6.ddnss.de/upd.php'

    valid_protocols = ('any', 'ipv4', 'ipv6')

    # -------------------------------------------------------------------------
    def __init__(
        self, appname=None, verbose=0, version=__version__, base_dir=None,
            encoding=None, config_dir=None, config_file=None, initialized=False):

        self.working_dir = self.default_working_dir
        self.logfile = self.default_logfile
        self.ddns_user = None
        self.ddns_pwd = None
        self.domains = []
        self.all_domains = False
        self.with_mx = False
        self.get_ipv4_url = self.default_get_ipv4_url
        self.get_ipv6_url = self.default_get_ipv6_url
        self.upd_ipv4_url = self.default_upd_ipv4_url
        self.upd_ipv6_url = self.default_upd_ipv6_url
        self.protocol = 'any'

        super(DdnsUpdateConfiguration, self).__init__(
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

        res = super(DdnsUpdateConfiguration, self).as_dict(short=short)

        res['ddns_pwd'] = None
        if self.ddns_pwd:
            if self.verbose > 4:
                res['ddns_pwd'] = self.ddns_pwd
            else:
                res['ddns_pwd'] = '*******'

        res['default_working_dir'] = self.default_working_dir
        res['default_logfile'] = self.default_logfile
        res['default_get_ipv4_url'] = self.default_get_ipv4_url
        res['default_get_ipv6_url'] = self.default_get_ipv6_url
        res['default_upd_ipv4_url'] = self.default_upd_ipv4_url
        res['default_upd_ipv6_url'] = self.default_upd_ipv6_url
        res['valid_protocols'] = self.valid_protocols

        return res

    # -------------------------------------------------------------------------
    def eval_config_section(self, config, section_name):

        super(DdnsUpdateConfiguration, self).eval_config_section(config, section_name)

        if section_name.lower() == 'ddns':
            self._eval_config_ddns(config, section_name)
            return

        if section_name.lower() == 'files':
            self._eval_config_files(config, section_name)
            return

        if self.verbose > 1:
            LOG.debug("Unhandled configuration section {!r}.".format(section_name))

    # -------------------------------------------------------------------------
    def _eval_config_ddns(self, config, section_name):

        if self.verbose > 1:
            LOG.debug("Checking config section {!r} ...".format(section_name))

        re_domains = re.compile(r'(\s+)|\s*([,;]\s*)+')
        re_all_domains = re.compile(r'^all[_-]?domains$', re.IGNORECASE)
        re_with_mx = re.compile(r'^with[_-]?mx$', re.IGNORECASE)
        re_get_url = re.compile(r'^\s*get[_-]ipv([46])[_-]url\s*$', re.IGNORECASE)
        re_upd_url = re.compile(r'^\s*upd(?:ate)?[_-]ipv([46])[_-]url\s*$', re.IGNORECASE)

        for (key, value) in config.items(section_name):

            if key.lower() == 'user' and value.strip():
                self.ddns_user = value.strip()
                continue
            elif (key.lower() == 'pwd' or key.lower() == 'password') and value.strip():
                self.ddns_pwd = value.strip()
                continue
            elif key.lower() == 'domains':
                domains_str = value.strip()
                if domains_str:
                    self.domains = re_domains.split(domains_str)
                continue
            elif re_all_domains.match(key) and value.strip():
                self.all_domains = to_bool(value.strip())
                continue
            elif re_with_mx.match(key) and value.strip():
                self.with_mx = to_bool(value.strip())
                continue
            match = re_get_url.match(key)
            if match and value.strip():
                setattr(self, 'get_ipv{}_url'.format(match.group(1)), value.strip())
                return
            match = re_upd_url.match(key)
            if match and value.strip():
                setattr(self, 'upd_ipv{}_url'.format(match.group(1)), value.strip())
                return
            if key.lower() == 'protocol' and value.strip():
                p = value.strip().lower()
                if p not in self.valid_protocols:
                    LOG.error(_(
                        "Invalid value {ur} for protocols to update, valid protocols "
                        "are: ").format(value) + format_list(self.valid_protocols, do_repr=True))
                else:
                    self.protocol = p

            LOG.warning(_("Unknown configuration option {o!r} with value {v!r}.").format(
                o=key, v=value))

        return


# =============================================================================

if __name__ == "__main__":

    pass

# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 list
