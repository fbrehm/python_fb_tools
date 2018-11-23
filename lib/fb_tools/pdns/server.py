#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: Frank Brehm
@contact: frank@brehm-online.com
@copyright: © 2018 by Frank Brehm, Berlin
@summary: The module for a PowerDNS server handler object.
"""
from __future__ import absolute_import

# Standard modules
import logging
import re
import ipaddress

# Third party modules

# Own modules
from ..common import pp, to_bool

from ..handling_obj import HandlingObject

from . import BasePowerDNSHandler, DEFAULT_PORT, DEFAULT_API_PREFIX

from .errors import PDNSApiNotFoundError, PDNSApiValidationError

from .zone import PowerDNSZone, PowerDNSZoneDict

__version__ = '0.5.2'
LOG = logging.getLogger(__name__)


# =============================================================================
class PowerDNSServer(BasePowerDNSHandler):
    """
    Class for a PowerDNS server handler.
    """

    # -------------------------------------------------------------------------
    def __init__(
        self, appname=None, verbose=0, version=__version__, base_dir=None,
            master_server=None, port=DEFAULT_PORT, key=None, use_https=False,
            path_prefix=DEFAULT_API_PREFIX, simulate=None, force=None,
            terminal_has_colors=False, initialized=False):

        self._api_servername = self.default_api_servername
        self._api_server_version = 'unknown'
        self.zones = None

        super(PowerDNSServer, self).__init__(
            appname=appname, verbose=verbose, version=version, base_dir=base_dir,
            master_server=master_server, port=port, key=key, use_https=use_https,
            path_prefix=path_prefix, simulate=simulate, force=force,
            terminal_has_colors=terminal_has_colors, initialized=False,
        )

        self.initialized = initialized

    # -----------------------------------------------------------
    @property
    def api_server_version(self):
        "The version of the PowerDNS server, how provided by API."
        return self._api_server_version

    # -----------------------------------------------------------
    @HandlingObject.simulate.setter
    def simulate(self, value):
        self._simulate = to_bool(value)

        if self.initialized:
            LOG.debug("Setting simulate of all subsequent objects to {!r} ...".format(
                self.simulate))

        if self.zones:
            for zone_name in self.zones:
                self.zones[zone_name].simulate = self.simulate

    # -------------------------------------------------------------------------
    def as_dict(self, short=True):
        """
        Transforms the elements of the object into a dict

        @param short: don't include local properties in resulting dict.
        @type short: bool

        @return: structure as dict
        @rtype:  dict
        """

        res = super(PowerDNSServer, self).as_dict(short=short)
        res['api_server_version'] = self.api_server_version

        return res

    # -------------------------------------------------------------------------
    def get_api_server_version(self):

        path = "/servers/{}".format(self.api_servername)
        try:
            json_response = self.perform_request(path)
        except (PDNSApiNotFoundError, PDNSApiValidationError):
            LOG.error("Could not found server info.")
            return None
        if self.verbose > 2:
            LOG.debug("Got a response:\n{}".format(pp(json_response)))

        if 'version' in json_response:
            self._api_server_version = json_response['version']
            LOG.info("PowerDNS server version {!r}.".format(self.api_server_version))
            return self.api_server_version
        LOG.error("Did not found version info in server info:\n{}".format(pp(json_response)))
        return None

    # -------------------------------------------------------------------------
    def get_api_zones(self):

        LOG.debug("Trying to get all zones from PDNS API ...")

        path = "/servers/{}/zones".format(self.api_servername)
        json_response = self.perform_request(path)
        if self.verbose > 3:
            LOG.debug("Got a response:\n{}".format(pp(json_response)))

        self.zones = PowerDNSZoneDict()

        for data in json_response:
            zone = PowerDNSZone.init_from_dict(
                data, appname=self.appname, verbose=self.verbose, base_dir=self.base_dir,
                master_server=self.master_server, port=self.port, key=self.key,
                use_https=self.use_https, timeout=self.timeout, path_prefix=self.path_prefix,
                simulate=self.simulate, force=self.force, initialized=True)
            self.zones.append(zone)
            if self.verbose > 3:
                print("{!r}".format(zone))

        if self.verbose > 1:
            LOG.debug("Found {} zones.".format(len(self.zones)))

        if self.verbose > 2:
            if self.verbose > 3:
                LOG.debug("Zones:\n{}".format(pp(self.zones.as_list())))
            else:
                LOG.debug("Zones:\n{}".format(pp(list(self.zones.keys()))))

        return self.zones

    # -------------------------------------------------------------------------
    def get_zone_for_item(self, item, is_fqdn=False):

        if not len(self.zones):
            self.get_api_zones()

        fqdn = item

        if not is_fqdn:
            try:
                address = ipaddress.ip_address(item)
                fqdn = address.reverse_pointer
                is_fqdn = False
            except ValueError:
                if self.verbose > 3:
                    LOG.debug("Item {!r} is not a valid IP address.".format(item))
                is_fqdn = True
                fqdn = item

        if ':' in fqdn:
            LOG.error("Invalid FQDN {!r}.".format(fqdn))
            return None

        fqdn = self.canon_name(fqdn)

        if self.verbose > 2:
            LOG.debug("Searching an appropriate zone for FQDN {!r} ...".format(fqdn))

        for zone_name in reversed(self.zones.keys()):
            pattern = r'\.' + re.escape(zone_name) + '$'
            if self.verbose > 3:
                LOG.debug("Search pattern: {}".format(pattern))
            if re.search(pattern, fqdn):
                return zone_name

        return None


# =============================================================================

if __name__ == "__main__":

    pass

# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 list
