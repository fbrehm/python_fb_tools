#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: Frank Brehm
@contact: frank@brehm-online.com
@copyright: © 2018 Frank Brehm, Berlin
@summary: An encapsulation class for zone objects by PowerDNS API
"""
from __future__ import absolute_import

# Standard modules
import logging
import copy
import re
import ipaddress
import collections
import json

from functools import cmp_to_key

# Third party modules

# Own modules
from ..xlate import XLATOR

from ..common import pp, to_utf8, to_bool, compare_fqdn, RE_DOT

from ..obj import FbBaseObject

from . import BasePowerDNSHandler, DEFAULT_PORT, DEFAULT_API_PREFIX

from .errors import PowerDNSZoneError

from .record import PowerDnsSOAData
from .record import PowerDNSRecordSet, PowerDNSRecordSetList

__version__ = '0.8.4'

LOG = logging.getLogger(__name__)

_ = XLATOR.gettext
ngettext = XLATOR.ngettext


# =============================================================================
class PDNSNoRecordsToRemove(PowerDNSZoneError):

    # -------------------------------------------------------------------------
    def __init__(self, zone_name):
        self.zone_name = zone_name

    # -------------------------------------------------------------------------
    def __str__(self):

        msg = _("No Resource Record Sets found to remove from zone {!r}.").format(
            self.zone_name)
        return msg


# =============================================================================
class PowerDNSZone(BasePowerDNSHandler):
    """An encapsulation class for zone objects by PowerDNS API"""

    re_rev_ipv4 = re.compile(r'^((?:\d+\.)*\d+)\.in-addr\.arpa\.?$', re.IGNORECASE)
    re_rev_ipv6 = re.compile(r'^((?:[0-9a-f]\.)*[0-9a-f])\.ip6.arpa.?$', re.IGNORECASE)

    # -------------------------------------------------------------------------
    def __init__(
        self, appname=None, verbose=0, version=__version__, base_dir=None,
            account=None, dnssec=False, id=None, kind=None, last_check=None,
            masters=None, name=None, notified_serial=None, serial=None, url=None,
            soa_edit=None, soa_edit_api=None, nsec3narrow=None, nsec3param=None,
            presigned=None, api_rectify=None, master_server=None, port=DEFAULT_PORT,
            key=None, use_https=False, timeout=None, path_prefix=DEFAULT_API_PREFIX,
            simulate=None, force=None, terminal_has_colors=False, initialized=None):

        self._account = account
        self._dnssec = dnssec
        self._id = id
        self._kind = kind
        self._last_check = last_check
        self.masters = []
        if masters:
            self.masters = copy.copy(masters)
        self._name = None
        self._notified_serial = notified_serial
        self._serial = serial
        self._url = url
        self._nsec3narrow = None
        if nsec3narrow is not None:
            self._nsec3narrow = to_bool(nsec3narrow)
        self._nsec3param = None
        if nsec3param is not None and str(nsec3param).strip() != '':
            self._nsec3param = str(nsec3param).strip()
        self._presigned = None
        if presigned is not None:
            self._presigned = to_bool(presigned)
        self._api_rectify = None
        if api_rectify is not None:
            self._api_rectify = to_bool(api_rectify)

        self._reverse_zone = False
        self._reverse_net = None

        self.rrsets = PowerDNSRecordSetList()

        self._soa_edit = soa_edit
        self._soa_edit_api = soa_edit_api

        super(PowerDNSZone, self).__init__(
            appname=appname, verbose=verbose, version=version, base_dir=base_dir,
            master_server=master_server, port=port, key=key, use_https=use_https,
            timeout=timeout, path_prefix=path_prefix, simulate=simulate, force=force,
            terminal_has_colors=terminal_has_colors, initialized=False)

        self.name = name

        if initialized is not None:
            self.initialized = initialized

    # -----------------------------------------------------------
    @classmethod
    def init_from_dict(
        cls, data,
            appname=None, verbose=0, version=__version__, base_dir=None,
            master_server=None, port=DEFAULT_PORT, key=None, use_https=False,
            timeout=None, path_prefix=DEFAULT_API_PREFIX,
            simulate=None, force=None, terminal_has_colors=False, initialized=None):

        if not isinstance(data, dict):
            raise PowerDNSZoneError(_("Given data {!r} is not a dict object.").format(data))

        # {   'account': 'local',
        #     'api_rectify': False,
        #     'dnssec': False,
        #     'id': 'bla.ai.',
        #     'kind': 'Master',
        #     'last_check': 0,
        #     'masters': [],
        #     'name': 'bla.ai.',
        #     'nsec3narrow': False,
        #     'nsec3param': '',
        #     'notified_serial': 2018080404,
        #     'rrsets': [   {   'comments': [],
        #                       'name': '59.55.168.192.in-addr.arpa.',
        #                       'records': [   {   'content': 'slave009.prometheus.pixelpark.net.',
        #                                          'disabled': False}],
        #                       'ttl': 86400,
        #                       'type': 'PTR'},
        #                    ...],
        #     'serial': 2018080404,
        #     'soa_edit': '',
        #     'soa_edit_api': 'INCEPTION-INCREMENT',
        #     'url': 'api/v1/servers/localhost/zones/bla.ai.'},

        params = {
            'appname': appname,
            'verbose': verbose,
            'version': version,
            'base_dir': base_dir,
            'master_server': master_server,
            'port': port,
            'key': key,
            'use_https': use_https,
            'timeout': timeout,
            'path_prefix': path_prefix,
            'simulate': simulate,
            'force': force,
            'terminal_has_colors': terminal_has_colors,
        }
        if initialized is not None:
            params['initialized'] = initialized

        rrsets = None
        if 'rrsets' in data:
            if data['rrsets']:
                rrsets = data['rrsets']
            del data['rrsets']

        params.update(data)

        if verbose > 3:
            pout = copy.copy(params)
            pout['key'] = None
            if key:
                pout['key'] = '******'
            LOG.debug("Params initialisation:\n{}".format(pp(pout)))

        zone = cls(**params)

        if rrsets:
            for single_rrset in rrsets:
                rrset = PowerDNSRecordSet.init_from_dict(
                    single_rrset, appname=appname, verbose=verbose, base_dir=base_dir,
                    master_server=master_server, port=port, key=key, use_https=use_https,
                    timeout=timeout, path_prefix=path_prefix, simulate=simulate,
                    force=force, terminal_has_colors=terminal_has_colors, initialized=True)
                zone.rrsets.append(rrset)

        zone.initialized = True

        return zone

    # -----------------------------------------------------------
    @property
    def account(self):
        """The name of the owning account of the zone, internal used
            to differ local visible zones from all other zones."""
        return getattr(self, '_account', None)

    @account.setter
    def account(self, value):
        if value:
            v = str(value).strip()
            if v:
                self._account = v
            else:
                self._account = None
        else:
            self._account = None

    # -----------------------------------------------------------
    @property
    def dnssec(self):
        """Is the zone under control of DNSSEC."""
        return getattr(self, '_dnssec', False)

    @dnssec.setter
    def dnssec(self, value):
        self._dnssec = bool(value)

    # -----------------------------------------------------------
    @property
    def id(self):
        """The unique idendity of the zone."""
        return getattr(self, '_id', None)

    @id.setter
    def id(self, value):
        if value:
            v = str(value).strip()
            if v:
                self._id = v
            else:
                self._id = None
        else:
            self._id = None

    # -----------------------------------------------------------
    @property
    def kind(self):
        """The kind or type of the zone."""
        return getattr(self, '_kind', None)

    @kind.setter
    def kind(self, value):
        if value:
            v = str(value).strip()
            if v:
                self._kind = v
            else:
                self._kind = None
        else:
            self._kind = None

    # -----------------------------------------------------------
    @property
    def last_check(self):
        """The timestamp of the last check of the zone"""
        return getattr(self, '_last_check', None)

    # -----------------------------------------------------------
    @property
    def name(self):
        """The name of the zone."""
        return getattr(self, '_name', None)

    @name.setter
    def name(self, value):
        if value:
            v = str(value).strip()
            if v:
                self._name = v
                match = self.re_rev_ipv4.search(v)
                if match:
                    self._reverse_zone = True
                    self._reverse_net = self.ipv4_nw_from_tuples(match.group(1))
                else:
                    match = self.re_rev_ipv6.search(v)
                    if match:
                        self._reverse_zone = True
                        self._reverse_net = self.ipv6_nw_from_tuples(match.group(1))
                    else:
                        self._reverse_zone = False
                        self._reverse_net = None
            else:
                self._name = None
                self._reverse_zone = False
                self._reverse_net = None
        else:
            self._name = None
            self._reverse_zone = False
            self._reverse_net = None

    # -----------------------------------------------------------
    @property
    def reverse_zone(self):
        """Is this a reverse zone?"""
        return self._reverse_zone

    # -----------------------------------------------------------
    @property
    def reverse_net(self):
        """An IP network object representing the network, for which
            this is the reverse zone."""
        return self._reverse_net

    # -----------------------------------------------------------
    @property
    def name_unicode(self):
        """The name of the zone in unicode, if it is an IDNA encoded zone."""
        n = getattr(self, '_name', None)
        if n is None:
            return None
        if 'xn--' in n:
            return to_utf8(n).decode('idna')
        return n

    # -----------------------------------------------------------
    @property
    def notified_serial(self):
        """The notified serial number of the zone"""
        return getattr(self, '_notified_serial', None)

    # -----------------------------------------------------------
    @property
    def serial(self):
        """The serial number of the zone"""
        return getattr(self, '_serial', None)

    # -----------------------------------------------------------
    @property
    def url(self):
        """The URL in the API to get the zone object."""
        return getattr(self, '_url', None)

    # -----------------------------------------------------------
    @property
    def soa_edit(self):
        """The SOA edit property of the zone object."""
        return getattr(self, '_soa_edit', None)

    # -----------------------------------------------------------
    @property
    def soa_edit_api(self):
        """The SOA edit property (API) of the zone object."""
        return getattr(self, '_soa_edit_api', None)

    # -----------------------------------------------------------
    @property
    def nsec3narrow(self):
        """Some stuff belonging to DNSSEC."""
        return getattr(self, '_nsec3narrow', None)

    # -----------------------------------------------------------
    @property
    def nsec3param(self):
        """Some stuff belonging to DNSSEC."""
        return getattr(self, '_nsec3param', None)

    # -----------------------------------------------------------
    @property
    def presigned(self):
        """Some stuff belonging to PowerDNS >= 4.1."""
        return getattr(self, '_presigned', None)

    # -----------------------------------------------------------
    @property
    def api_rectify(self):
        """Some stuff belonging to PowerDNS >= 4.1."""
        return getattr(self, '_api_rectify', None)

    # -------------------------------------------------------------------------
    def as_dict(self, short=True):
        """
        Transforms the elements of the object into a dict

        @param short: don't include local properties in resulting dict.
        @type short: bool

        @return: structure as dict
        @rtype:  dict
        """

        res = super(PowerDNSZone, self).as_dict(short=short)
        res['account'] = self.account
        res['dnssec'] = copy.copy(self.dnssec)
        res['id'] = self.id
        res['kind'] = self.kind
        res['last_check'] = self.last_check
        res['masters'] = copy.copy(self.masters)
        res['name'] = self.name
        res['name_unicode'] = self.name_unicode
        res['notified_serial'] = self.notified_serial
        res['serial'] = self.serial
        res['url'] = self.url
        res['rrsets'] = []
        res['soa_edit'] = self.soa_edit
        res['soa_edit_api'] = self.soa_edit_api
        res['nsec3narrow'] = self.nsec3narrow
        res['nsec3param'] = self.nsec3param
        res['presigned'] = self.presigned
        res['api_rectify'] = self.api_rectify
        res['reverse_zone'] = self.reverse_zone
        res['reverse_net'] = self.reverse_net

        for rrset in self.rrsets:
            if isinstance(rrset, FbBaseObject):
                res['rrsets'].append(rrset.as_dict(short))
            else:
                res['rrsets'].append(rrset)

        return res

    # -------------------------------------------------------------------------
    def __str__(self):
        """
        Typecasting function for translating object structure
        into a string

        @return: structure as string
        @rtype:  str
        """

        return pp(self.as_dict(short=True))

    # -------------------------------------------------------------------------
    @classmethod
    def ipv4_nw_from_tuples(cls, tuples):

        bitmask = 0
        tokens = []
        for part in reversed(RE_DOT.split(tuples)):
            tokens.append(part)

        if len(tokens) == 3:
            tokens.append('0')
            bitmask = 24
        elif len(tokens) == 2:
            tokens.append('0')
            tokens.append('0')
            bitmask = 16
        elif len(tokens) == 1:
            tokens.append('0')
            tokens.append('0')
            tokens.append('0')
            bitmask = 8
        else:
            msg = _("Invalid source tuples for detecting IPv4-network: {!r}.").format(tuples)
            raise ValueError(msg)

        ip_str = '.'.join(tokens) + '/{}'.format(bitmask)
        net = ipaddress.ip_network(ip_str)

        return net

    # -------------------------------------------------------------------------
    @classmethod
    def ipv6_nw_from_tuples(cls, tuples):

        parts = RE_DOT.split(tuples)
        bitmask = 0
        tokens = []
        token = ''
        i = 0

        for part in reversed(parts):
            bitmask += 4
            i += 1
            token += part
            if i >= 4:
                tokens.append(token)
                token = ''
                i = 0

        if token != '':
            tokens.append(token.ljust(4, '0'))

        ip_str = ':'.join(tokens)
        if len(tokens) < 8:
            ip_str += ':'
            if len(tokens) < 7:
                ip_str += ':'

        ip_str += '/{}'.format(bitmask)
        net = ipaddress.ip_network(ip_str)

        return net

    # -------------------------------------------------------------------------
    def __repr__(self):
        """Typecasting into a string for reproduction."""

        out = "<%s(" % (self.__class__.__name__)

        fields = []
        fields.append("name={!r}".format(self.name))
        fields.append("url={!r}".format(self.url))
        fields.append("reverse_zone={!r}".format(self.reverse_zone))
        fields.append("reverse_net={!r}".format(self.reverse_net))
        fields.append("kind={!r}".format(self.kind))
        fields.append("serial={!r}".format(self.serial))
        fields.append("dnssec={!r}".format(self.dnssec))
        fields.append("account={!r}".format(self.account))
        fields.append("appname={!r}".format(self.appname))
        fields.append("verbose={!r}".format(self.verbose))
        fields.append("version={!r}".format(self.version))

        out += ", ".join(fields) + ")>"
        return out

    # -------------------------------------------------------------------------
    def __copy__(self):

        if self.verbose > 3:
            LOG.debug("Copying current {}-object into a new one.".format(self.__class__.__name__))

        zone = self.__class__(
            appname=self.appname, verbose=self.verbose, base_dir=self.base_dir,
            account=self.account, dnssec=self.dnssec, id=self.id, kind=self.kind,
            last_check=self.last_check, masters=self.masters, name=self.name,
            notified_serial=self.notified_serial, serial=self.serial, url=self.url,
            presigned=self.presigned, api_rectify=self.api_rectify,
            master_server=self.master_server, port=self.port, key=self.key,
            use_https=self.use_https, timeout=self.timeout, path_prefix=self.path_prefix,
            simulate=self.simulate, force=self.force, initialized=False)

        zone.rrsets = copy.copy(self.rrsets)

        zone.initialized = True
        return zone

    # -------------------------------------------------------------------------
    def update(self):

        if not self.url:
            msg = _("Cannot update zone {!r}, no API URL defined.").format(self.name)
            raise PowerDNSZoneError(msg)

        LOG.debug("Updating data of zone {n!r} from API path {u!r} ...".format(
            n=self.name, u=self.url))
        json_response = self.perform_request(self.url)

        if 'account' in json_response:
            self.account = json_response['account']
        else:
            self.account = None

        if 'dnssec' in json_response:
            self.dnssec = json_response['dnssec']
        else:
            self.dnssec = False

        if 'id' in json_response:
            self.id = json_response['id']
        else:
            self.id = None

        if 'kind' in json_response:
            self.kind = json_response['kind']
        else:
            self.kind = None

        if 'last_check' in json_response:
            self._last_check = json_response['last_check']
        else:
            self._last_check = None

        if 'notified_serial' in json_response:
            self._notified_serial = json_response['notified_serial']
        else:
            self._notified_serial = None

        if 'serial' in json_response:
            self._serial = json_response['serial']
        else:
            self._serial = None

        if 'nsec3narrow' in json_response:
            self._nsec3narrow = json_response['nsec3narrow']
        else:
            self._nsec3narrow = None

        if 'nsec3param' in json_response:
            self._nsec3param = json_response['nsec3param']
        else:
            self._nsec3param = None

        if 'soa_edit' in json_response:
            self._soa_edit = json_response['soa_edit']
        else:
            self._soa_edit = None

        if 'soa_edit_api' in json_response:
            self._soa_edit_api = json_response['soa_edit_api']
        else:
            self._soa_edit_api = None

        self.masters = []
        if 'masters' in json_response:
            self.masters = copy.copy(json_response['masters'])

        self.rrsets = PowerDNSRecordSetList()
        if 'rrsets' in json_response:
            for single_rrset in json_response['rrsets']:
                rrset = PowerDNSRecordSet.init_from_dict(
                    single_rrset, appname=self.appname, verbose=self.verbose,
                    base_dir=self.base_dir, master_server=self.master_server, port=self.port,
                    key=self.key, use_https=self.use_https, timeout=self.timeout,
                    path_prefix=self.path_prefix, simulate=self.simulate, force=self.force,
                    initialized=True)
                self.rrsets.append(rrset)

    # -------------------------------------------------------------------------
    def perform_request(
            self, path, no_prefix=True, method='GET', data=None, headers=None, may_simulate=False):
        """Performing the underlying API request."""

        return super(PowerDNSZone, self).perform_request(
            path=path, no_prefix=no_prefix, method=method, data=data,
            headers=copy.copy(headers), may_simulate=may_simulate)

    # -------------------------------------------------------------------------
    def patch(self, payload):

        if self.verbose > 1:
            LOG.debug("Patching zone {!r} ...".format(self.name))

        return self.perform_request(
            self.url, method='PATCH',
            data=json.dumps(payload), may_simulate=True)

    # -------------------------------------------------------------------------
    def get_soa(self):

        if not len(self.rrsets):
            self.update()

        for rrset in self.rrsets:
            if rrset.type == 'SOA':
                soa = rrset.get_soa_data()
                return soa

        LOG.warn(_("Did not get SOA for zone {!r}.").format(self.name))
        return None

    # -------------------------------------------------------------------------
    def update_soa(self, new_soa, comment=None, ttl=None):

        if not isinstance(new_soa, PowerDnsSOAData):
            msg = _("New SOA must be of type {e}, given {t}: {s!r}").format(
                e='PowerDnsSOAData', t=new_soa.__class__.__name__, s=new_soa)
            raise TypeError(msg)

        if ttl:
            ttl = int(ttl)
        else:
            if not len(self.rrsets):
                self.update()
            cur_soa_rrset = self.get_soa()
            if not cur_soa_rrset:
                raise RuntimeError(_("Got no SOA for zone {!r}.").format(self.name))
            ttl = cur_soa_rrset.ttl

        if comment is not None:
            comment = str(comment).strip()
            if comment == '':
                comment = None

        rrset = {
            'name': self.name,
            'type': 'SOA',
            'ttl': ttl,
            'changetype': 'REPLACE',
            'records': [],
            'comments': [],
        }

#        if comment:
#            comment_rec = {
#                'content': comment,
#                'account': getpass.getuser(),
#                'modified_at': int(time.time() + 0.5),
#            }
#            rrset['comments'] = [comment_rec]

        record = {
            'content': new_soa.data,
            'disabled': False,
            'name': self.name,
            'set-ptr': False,
            'type': 'SOA',
        }
        rrset['records'].append(record)
        payload = {"rrsets": [rrset]}

        if self.verbose > 1:
            LOG.debug("Setting new SOA {s!r} for zone {z!r}, TTL {t} ...".format(
                s=new_soa.data, z=self.name, t=ttl))

        self.patch(payload)

    # -------------------------------------------------------------------------
    def increase_serial(self):

        self.update()

        soa = self.get_soa()
        old_serial = soa.serial
        new_serial = soa.increase_serial()

        LOG.debug("Increasing serial of zone {z!r} from {o} => {n}.".format(
            z=self.name, o=old_serial, n=new_serial))
        self.update_soa(soa)

    # -------------------------------------------------------------------------
    def add_address_record(self, fqdn, address, ttl=None):

        if not isinstance(address, (ipaddress.IPv4Address, ipaddress.IPv6Address)):
            msg = _(
                "Parameter address {a!r} is not an IPv4Address or IPv6Address object, "
                "but a {c} object instead.").format(a=address, c=address.__class__.__name__)
            raise TypeError(msg)

        record_type = 'A'
        if address.version == 6:
            record_type = 'AAAA'
        LOG.debug("Trying to create {t}-record {f!r} => {a!r}.".format(
            t=record_type, f=fqdn, a=str(address)))

        canon_fqdn = self.canon_name(fqdn)

        self.update()
        if self.verbose > 3:
            LOG.debug("Current zone:\n{}".format(pp(self.as_dict())))

        soa = self.get_soa()
        rrset = None
        for item in self.rrsets:
            if item.name == canon_fqdn and item.type == record_type:
                rrset = item
                break

        if ttl is None:
            ttl = soa.ttl
            if rrset:
                ttl = rrset.ttl

        records = []
        if rrset:
            for r in rrset.records:
                record = {
                    "name": canon_fqdn,
                    "type": record_type,
                    "content": r.content,
                    "disabled": r.disabled,
                    "set-ptr": False,
                }
                records.append(record)

        record = {
            "name": canon_fqdn,
            "type": record_type,
            "content": str(address),
            "disabled": False,
            "set-ptr": False,
        }
        records.append(record)

        new_rrset = {
            "name": canon_fqdn,
            "type": record_type,
            "ttl": ttl,
            "changetype": "REPLACE",
            "records": records,
        }

        payload = {"rrsets": [new_rrset]}
        LOG.info(_("Creating {t}-record {f!r} => {a!r}.").format(
            t=record_type, f=fqdn, a=str(address)))

        self.patch(payload)

        return True

    # -------------------------------------------------------------------------
    def add_ptr_record(self, pointer, fqdn, ttl=None):

        canon_fqdn = self.canon_name(fqdn)

        self.update()
        if self.verbose > 3:
            LOG.debug("Current zone:\n{}".format(pp(self.as_dict())))

        soa = self.get_soa()

        rrset = None
        for item in self.rrsets:
            if item.name == pointer and item.type == 'PTR':
                rrset = item
                break

        if ttl is None:
            ttl = soa.ttl
            if rrset:
                ttl = rrset.ttl

        records = []
        if rrset:
            for r in rrset.records:
                record = {
                    "name": pointer,
                    "type": 'PTR',
                    "content": r.content,
                    "disabled": r.disabled,
                    "set-ptr": False,
                }
                records.append(record)

        record = {
            "name": pointer,
            "type": 'PTR',
            "content": canon_fqdn,
            "disabled": False,
            "set-ptr": False,
        }
        records.append(record)

        new_rrset = {
            "name": pointer,
            "type": 'PTR',
            "ttl": ttl,
            "changetype": "REPLACE",
            "records": records,
        }

        payload = {"rrsets": [new_rrset]}
        LOG.info(_("Creating {t}-record {f!r} => {a!r}.").format(
            t='PTR', f=pointer, a=str(fqdn)))

        self.patch(payload)

        return True

    # -------------------------------------------------------------------------
    def add_rrset_for_remove(self, fqdn, rr_type, rrsets=None):

        if rrsets is None:
            rrsets = []

        rrset = {
            "name": self.canon_name(fqdn),
            "type": rr_type.upper(),
            "records": [],
            "comments": [],
            "changetype": "DELETE",
        }
        rrsets.append(rrset)
        return rrsets

    # -------------------------------------------------------------------------
    def del_rrsets(self, rrsets):

        if not rrsets:
            raise PDNSNoRecordsToRemove(self.name_unicode)

        self.update()
        if self.verbose > 3:
            LOG.debug("Current zone:\n{}".format(pp(self.as_dict())))

        rrsets_rm = []

        for rrset in rrsets:
            found = False
            for item in self.rrsets:
                if item.name == rrset["name"] and item.type == rrset["type"]:
                    found = True
                    break
            if not found:
                msg = _("DNS {t!r}-record {n!r} is already deleted.").format(
                    t=rrset["type"], n=rrset["name"])
                LOG.warn(msg)
                continue
            rrsets_rm.append(rrset)
        if not rrsets_rm:
            raise PDNSNoRecordsToRemove(self.name_unicode)

        payload = {"rrsets": rrsets_rm}
        count = len(rrsets_rm)
        msg = ngettext(
            "Removing one resource record set from zone {z!r}.",
            "Removing {c} resource record sets from zone {z!r}.", count).format(
            c=count, z=self.name_unicode)
        LOG.info(msg)
        if self.verbose > 1:
            LOG.debug("Resorce record sets:\n{}".format(pp(payload)))

        self.patch(payload)
        LOG.info(_("Done."))

        return True
    # -------------------------------------------------------------------------

    def notify(self):

        LOG.info(_("Notifying slave servers of zone {!r} ...").format(self.name))
        path = self.url + '/notify'
        return self.perform_request(path, method='PUT', may_simulate=True)


# =============================================================================
class PowerDNSZoneDict(collections.MutableMapping):
    """
    A dictionary containing PDNS Zone objects.
    It works like a dict.
    i.e.:
    zones = PowerDNSZoneDict(PowerDNSZone(name='pp.com', ...))
    and
    zones['pp.com'] returns a PowerDNSZone object for zone 'pp.com'
    """

    msg_invalid_zone_type = _("Invalid item type {{!r}} to set, only {} allowed.").format(
        'PowerDNSZone')
    msg_key_not_name = _("The key {k!r} must be equal to the zone name {n!r}.")
    msg_none_type_error = _("None type as key is not allowed.")
    msg_empty_key_error = _("Empty key {!r} is not allowed.")
    msg_no_zone_dict = _("Object {o!r} is not a {e} object.")

    # -------------------------------------------------------------------------
    # __init__() method required to create instance from class.
    def __init__(self, *args, **kwargs):
        '''Use the object dict'''
        self._map = dict()

        for arg in args:
            self.append(arg)

    # -------------------------------------------------------------------------
    def _set_item(self, key, zone):

        if not isinstance(zone, PowerDNSZone):
            raise TypeError(self.msg_invalid_zone_type.format(zone.__class__.__name__))

        zone_name = zone.name
        if zone_name != key.lower():
            raise KeyError(self.msg_key_not_name.format(k=key, n=zone_name))

        self._map[zone_name] = zone

    # -------------------------------------------------------------------------
    def append(self, zone):

        if not isinstance(zone, PowerDNSZone):
            raise TypeError(self.msg_invalid_zone_type.format(zone.__class__.__name__))
        self._set_item(zone.name, zone)

    # -------------------------------------------------------------------------
    def _get_item(self, key):

        if key is None:
            raise TypeError(self.msg_none_type_error)

        zone_name = str(key).lower().strip()
        if zone_name == '':
            raise ValueError(self.msg_empty_key_error.format(key))

        return self._map[zone_name]

    # -------------------------------------------------------------------------
    def get(self, key):
        return self._get_item(key)

    # -------------------------------------------------------------------------
    def _del_item(self, key, strict=True):

        if key is None:
            raise TypeError(self.msg_none_type_error)

        zone_name = str(key).lower().strip()
        if zone_name == '':
            raise ValueError(self.msg_empty_key_error.format(key))

        if not strict and zone_name not in self._map:
            return

        del self._map[zone_name]

    # -------------------------------------------------------------------------
    # The next five methods are requirements of the ABC.
    def __setitem__(self, key, value):
        self._set_item(key, value)

    # -------------------------------------------------------------------------
    def __getitem__(self, key):
        return self._get_item(key)

    # -------------------------------------------------------------------------
    def __delitem__(self, key):
        self._del_item(key)

    # -------------------------------------------------------------------------
    def __iter__(self):

        for zone_name in self.keys():
            yield zone_name

    # -------------------------------------------------------------------------
    def __len__(self):
        return len(self._map)

    # -------------------------------------------------------------------------
    # The next methods aren't required, but nice for different purposes:
    def __str__(self):
        '''returns simple dict representation of the mapping'''
        return str(self._map)

    # -------------------------------------------------------------------------
    def __repr__(self):
        '''echoes class, id, & reproducible representation in the REPL'''
        return '{}, {}({})'.format(
            super(PowerDNSZoneDict, self).__repr__(),
            self.__class__.__name__,
            self._map)

    # -------------------------------------------------------------------------
    def __contains__(self, key):
        if key is None:
            raise TypeError(self.msg_none_type_error)

        zone_name = str(key).lower().strip()
        if zone_name == '':
            raise ValueError(self.msg_empty_key_error.format(key))

        return zone_name in self._map

    # -------------------------------------------------------------------------
    def keys(self):

        return sorted(
            self._map.keys(),
            key=lambda x: cmp_to_key(compare_fqdn)(self._map[x].name_unicode))

    # -------------------------------------------------------------------------
    def items(self):

        item_list = []

        for zone_name in self.keys():
            item_list.append((zone_name, self._map[zone_name]))

        return item_list

    # -------------------------------------------------------------------------
    def values(self):

        value_list = []
        for zone_name in self.keys():
            value_list.append(self._map[zone_name])
        return value_list

    # -------------------------------------------------------------------------
    def __eq__(self, other):

        if not isinstance(other, PowerDNSZoneDict):
            raise TypeError(self.msg_no_zone_dict.format(o=other, e='PowerDNSZoneDict'))

        return self._map == other._map

    # -------------------------------------------------------------------------
    def __ne__(self, other):

        if not isinstance(other, PowerDNSZoneDict):
            raise TypeError(self.msg_no_zone_dict.format(o=other, e='PowerDNSZoneDict'))

        return self._map != other._map

    # -------------------------------------------------------------------------
    def pop(self, key, *args):

        if key is None:
            raise TypeError(self.msg_none_type_error)

        zone_name = str(key).lower().strip()
        if zone_name == '':
            raise ValueError(self.msg_empty_key_error.format(key))

        return self._map.pop(zone_name, *args)

    # -------------------------------------------------------------------------
    def popitem(self):

        if not len(self._map):
            return None

        zone_name = self.keys()[0]
        zone = self._map[zone_name]
        del self._map[zone_name]
        return (zone_name, zone)

    # -------------------------------------------------------------------------
    def clear(self):
        self._map = dict()

    # -------------------------------------------------------------------------
    def setdefault(self, key, default):

        if key is None:
            raise TypeError(self.msg_none_type_error)

        zone_name = str(key).lower().strip()
        if zone_name == '':
            raise ValueError(self.msg_empty_key_error.format(key))

        if not isinstance(default, PowerDNSZone):
            raise TypeError(self.msg_invalid_zone_type.format(default.__class__.__name__))

        if zone_name in self._map:
            return self._map[zone_name]

        self._set_item(zone_name, default)
        return default

    # -------------------------------------------------------------------------
    def update(self, other):

        if isinstance(other, PowerDNSZoneDict) or isinstance(other, dict):
            for zone_name in other.keys():
                self._set_item(zone_name, other[zone_name])
            return

        for tokens in other:
            key = tokens[0]
            value = tokens[1]
            self._set_item(key, value)

    # -------------------------------------------------------------------------
    def as_dict(self, short=True):

        res = {}
        for zone_name in self._map:
            res[zone_name] = self._map[zone_name].as_dict(short)
        return res

    # -------------------------------------------------------------------------
    def as_list(self, short=True):

        res = []
        for zone_name in self.keys():
            res.append(self._map[zone_name].as_dict(short))
        return res


# =============================================================================

if __name__ == "__main__":

    pass

# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 list
