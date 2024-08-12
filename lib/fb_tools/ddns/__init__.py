#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@summary: The base module for all DDNS related classes.

@author: Frank Brehm
@contact: frank.brehm@pixelpark.com
@copyright: © 2024 by Frank Brehm, Berlin
"""
from __future__ import absolute_import, print_function

# Standard modules
import copy
import ipaddress
import json
import logging
import os
import re
import socket
import sys
from json import JSONDecodeError

# Third party modules
import requests

import urllib3

HAS_DNS_MODULE = False
try:
    import dns
    import dns.resolver
    from dns.resolver import NoAnswer
    from dns.resolver import NXDOMAIN
    HAS_DNS_MODULE = True
except ImportError:
    pass

# Own modules
from .config import DdnsConfiguration
from .errors import DdnsAppError
from .errors import DdnsRequestError
from .errors import WorkDirAccessError
from .errors import WorkDirNotDirError
from .errors import WorkDirNotExistsError
from .. import __version__ as GLOBAL_VERSION
from ..argparse_actions import DirectoryOptionAction
from ..cfg_app import FbConfigApplication
from ..common import pp
from ..common import to_bool
from ..errors import IoTimeoutError
from ..xlate import XLATOR, format_list

__version__ = '2.3.0'
LOG = logging.getLogger(__name__)

_ = XLATOR.gettext


# =============================================================================
class BaseDdnsApplication(FbConfigApplication):
    """Class for the application objects."""

    library_name = 'ddns-client'
    loglevel_requests_set = False

    work_directory_must_exists = False
    work_directory_must_be_writeable = False

    default_verify_server_cert = True

    # -------------------------------------------------------------------------
    def __init__(
        self, appname=None, verbose=0, version=GLOBAL_VERSION, base_dir=None,
            cfg_class=DdnsConfiguration, initialized=False, usage=None, description=None,
            argparse_epilog=None, argparse_prefix_chars='-', env_prefix=None,
            config_dir=None):
        """Initialize a BaseDdnsApplication object."""
        if description is None:
            description = _('This is a base DDNS related application.')

        self._user_agent = '{}/{}'.format(self.library_name, GLOBAL_VERSION)
        self._verify_server_cert = self.default_verify_server_cert

        super(BaseDdnsApplication, self).__init__(
            appname=appname, verbose=verbose, version=version, base_dir=base_dir,
            description=description, cfg_class=cfg_class, initialized=False,
            argparse_epilog=argparse_epilog, argparse_prefix_chars=argparse_prefix_chars,
            env_prefix=env_prefix, config_dir=config_dir
        )

        if initialized:
            self.initialized = True

    # -----------------------------------------------------------
    @property
    def user_agent(self):
        """Return the name of the user agent used in API calls."""
        return self._user_agent

    @user_agent.setter
    def user_agent(self, value):
        if value is None or str(value).strip() == '':
            raise DdnsAppError(_('Invalid user agent {!r} given.').format(value))
        self._user_agent = str(value).strip()

    # -----------------------------------------------------------
    @property
    def verify_server_cert(self):
        """Return whether to verify the SSL certificate of the requested server."""
        return self._verify_server_cert

    @verify_server_cert.setter
    def verify_server_cert(self, value):
        if value is None:
            self._verify_server_cert = self.default_verify_server_cert
            return
        self._verify_server_cert = to_bool(value)

    # -------------------------------------------------------------------------
    @property
    def has_dns_module(self):
        """Return, whether the dns module could be imported."""
        return HAS_DNS_MODULE

    # -------------------------------------------------------------------------
    def as_dict(self, short=True):
        """
        Transform the elements of the object into a dict.

        @param short: don't include local properties in resulting dict.
        @type short: bool

        @return: structure as dict
        @rtype:  dict
        """
        res = super(BaseDdnsApplication, self).as_dict(short=short)
        res['has_dns_module'] = self.has_dns_module
        res['user_agent'] = self.user_agent
        res['verify_server_cert'] = self.verify_server_cert

        return res

    # -------------------------------------------------------------------------
    def init_arg_parser(self):
        """Initiate the argument parser."""
        ddns_group = self.arg_parser.add_argument_group(_('DDNS options'))

        valid_list = copy.copy(DdnsConfiguration.valid_protocols)

        protocol_group = ddns_group.add_mutually_exclusive_group()

        ipv4_help = getattr(self, '_ipv4_help', None)
        ipv6_help = getattr(self, '_ipv6_help', None)
        proto_help = getattr(self, '_proto_help', None)

        if ipv4_help is None:
            ipv4_help = _('Perform action only for {}.').format('IPv4')

        if ipv6_help is None:
            ipv6_help = _('Perform action only for {}.').format('IPv6')

        if proto_help is None:
            proto_help = _(
                'The IP protocol, for which the action should be performed '
                '(one of {c}, default {d!r}).').format(
                    c=format_list(valid_list, do_repr=True, style='or'), d='any')

        protocol_group.add_argument(
            '-4', '--ipv4', dest='ipv4', action='store_true', help=ipv4_help,
        )

        protocol_group.add_argument(
            '-6', '--ipv6', dest='ipv6', action='store_true', help=ipv6_help,
        )

        protocol_group.add_argument(
            '-p', '--protocol', dest='protocol', metavar=_('PROTOCOL'),
            choices=valid_list, help=proto_help,
        )

        ddns_group.add_argument(
            '-d', '--dir', '--work-directory', dest='directory', metavar=_('DIRECTORY'),
            action=DirectoryOptionAction, must_exists=self.work_directory_must_exists,
            writeable=self.work_directory_must_be_writeable,
            help=_(
                'The directory, where to read and write the cache files of the '
                'evaluated IP addresses (default: {!r}).').format(
                str(DdnsConfiguration.default_working_dir)),
        )

        ddns_group.add_argument(
            '-T', '--timeout', dest='timeout', type=int, metavar=_('SECONDS'),
            help=_('The timeout in seconds for Web requests (default: {}).').format(
                DdnsConfiguration.default_timeout),
        )

        ddns_group.add_argument(
            '-k', '--insecure', dest='insecure', action='store_true',
            help=_(
                'By default, every secure connection {app} makes is verified to be secure before '
                'the request takes place. This option makes {app} skip the verification step and '
                'proceed without checking.').format(app=self.appname),
        )

        super(BaseDdnsApplication, self).init_arg_parser()

    # -------------------------------------------------------------------------
    def post_init(self):
        """
        Execute actions after init and befor the underlaying run.

        Method to execute before calling run(). Here could be done some
        finishing actions after reading in commandline parameters,
        configuration a.s.o.

        This method could be overwritten by descendant classes, these
        methhods should allways include a call to post_init() of the
        parent class.

        """
        super(BaseDdnsApplication, self).post_init()

        if self.args.ipv4:
            self.cfg.protocol = 'ipv4'
        elif self.args.ipv6:
            self.cfg.protocol = 'ipv6'
        elif self.args.protocol:
            if self.args.protocol == 'both':
                self.cfg.protocol = 'any'
            else:
                self.cfg.protocol = self.args.protocol

        if self.args.timeout:
            try:
                self.cfg.timeout = self.args.timeout
            except (ValueError, KeyError) as e:
                msg = _('Invalid value {!r} as timeout:').format(self.args.timeout) + ' ' + str(e)
                LOG.error(msg)
                print()
                self.arg_parser.print_usage(sys.stdout)
                self.exit(1)

        if self.args.directory:
            self.cfg.working_dir = self.args.directory

        # TODO: also for urllib3 !!!
        if not self.loglevel_requests_set:
            msg = _('Setting Loglevel of the {m} module to {ll}.').format(
                m='requests', ll='WARNING')
            LOG.debug(msg)
            logging.getLogger('requests').setLevel(logging.WARNING)
            self.loglevel_requests_set = True

        if self.args.insecure:
            self.verify_server_cert = False

        self.initialized = True

    # -------------------------------------------------------------------------
    def get_my_ipv(self, protocol):
        """Retrieve the current public IPv64 address."""
        LOG.debug(_('Trying to get my public IPv{} address.').format(protocol))

        url = self.cfg.get_ipv4_url
        if protocol == 6:
            url = self.cfg.get_ipv6_url

        try:
            json_response = self.perform_request(url)
        except DdnsAppError as e:
            LOG.error(str(e))
            return None
        if self.verbose > 1:
            LOG.debug(_('Got a response:') + '\n' + pp(json_response))

        return json_response['IP']

    # -------------------------------------------------------------------------
    def perform_request(
            self, url, method='GET', data=None, headers=None, may_simulate=False,
            return_json=True):
        """Perform the underlying Web request."""
        verify = None
        if url.startswith('https://'):
            if self.verify_server_cert:
                verify = True
            else:
                verify = False
                urllib3.disable_warnings()
            LOG.debug(f'Verifying remote server certificate: {verify!r}.')

        if headers is None:
            headers = {}

        if self.verbose > 1:
            LOG.debug(_('Request method: {!r}').format(method))

        if data and self.verbose > 1:
            data_out = '{!r}'.format(data)
            try:
                data_out = json.loads(data)
            except ValueError:
                pass
            else:
                data_out = pp(data_out)
            LOG.debug('Data:\n{}'.format(data_out))
            if self.verbose > 2:
                LOG.debug('RAW data:\n{}'.format(data))

        headers.update({'User-Agent': self.user_agent})
        headers.update({'Content-Type': 'application/json'})
        if self.verbose > 1:
            LOG.debug('Headers:\n{}'.format(pp(headers)))

        if may_simulate and self.simulate:
            LOG.debug(_('Simulation mode, Request will not be sent.'))
            return ''

        try:

            session = requests.Session()
            response = session.request(
                method, url, data=data, headers=headers, timeout=self.cfg.timeout, verify=verify)

        except (
                socket.timeout, urllib3.exceptions.ConnectTimeoutError,
                urllib3.exceptions.MaxRetryError, requests.exceptions.ConnectionError,
                requests.exceptions.ConnectTimeout) as e:
            msg = _('Got a {c} on requesting {u!r}: {e}.').format(
                c=e.__class__.__name__, u=url, e=e)
            raise DdnsAppError(msg)

        try:
            self._eval_response(url, response)
        except ValueError:
            raise DdnsAppError(_('Failed to parse the response'), response.text)

        return self._mangle_response(response, return_json=return_json)

    # -------------------------------------------------------------------------
    def _mangle_response(self, response, return_json=True):

        if self.verbose > 3:
            LOG.debug('RAW response: {!r}.'.format(response.text))
            LOG.debug('Status of request: {c!r} - {r!r}'.format(
                c=response.status_code, r=response.reason))
        if not response.text:
            return ('', response.status_code, response.reason)

        if not return_json:
            msg = _('Text response:') + '\n' + response.text
            if self.verbose > 3:
                LOG.debug(msg)
            return (response.text, response.status_code, response.reason)

        try:
            json_response = response.json()
        except JSONDecodeError:
            encoding = 'utf-8-sig'
            if self.verbose > 2:
                msg = _('Setting encoding of response to {!r}.').format(encoding)
                LOG.debug(msg)
            response.encoding = encoding
            json_response = response.json()

        if self.verbose > 3:
            LOG.debug('JSON response:\n{}'.format(pp(json_response)))

        return json_response

    # -------------------------------------------------------------------------
    def _eval_response(self, url, response):

        if response.ok:
            return

        err = response.json()
        code = response.status_code
        msg = err['error']
        raise DdnsRequestError(code, msg, url)

    # -------------------------------------------------------------------------
    def verify_working_dir(self):
        """Verify existence and accessibility of working directory."""
        if self.verbose > 1:
            LOG.debug(_(
                'Checking existence and accessibility of working directory {!r} ...').format(
                str(self.cfg.working_dir)))

        if not self.cfg.working_dir.exists():
            raise WorkDirNotExistsError(self.cfg.working_dir)

        if not self.cfg.working_dir.is_dir():
            raise WorkDirNotDirError(self.cfg.working_dir)

        if not os.access(str(self.cfg.working_dir), os.R_OK):
            raise WorkDirAccessError(
                self.cfg.working_dir, _('No read access'))

        if not os.access(str(self.cfg.working_dir), os.W_OK):
            raise WorkDirAccessError(
                self.cfg.working_dir, _('No write access'))

    # -------------------------------------------------------------------------
    def write_ipv4_cache(self, address):
        """Write the cache for IPv4 addresses."""
        self.write_ip_cache(address, self.cfg.ipv4_cache_file)

    # -------------------------------------------------------------------------
    def write_ipv6_cache(self, address):
        """Write the cache for IPv6 addresses."""
        self.write_ip_cache(address, self.cfg.ipv6_cache_file)

    # -------------------------------------------------------------------------
    def write_ip_cache(self, address, cache_file):
        """Write a cache entry."""
        LOG.debug(_(
            'Writing IP address {a!r} into {f!r} ...').format(
                a=str(address), f=str(cache_file)))
        cont = str(address) + '\n'
        try:
            self.write_file(filename=str(cache_file), content=cont, must_exists=False, quiet=True)
        except (IOError, IoTimeoutError) as e:
            LOG.error(str(e))
            if self.exit_value <= 1:
                self.exit_value = 4

    # -------------------------------------------------------------------------
    def get_ipv4_cache(self):
        """Return a current IPv4 address cache entry."""
        return self.get_ip_cache(self.cfg.ipv4_cache_file)

    # -------------------------------------------------------------------------
    def get_ipv6_cache(self):
        """Return a current IPv6 address cache entry."""
        return self.get_ip_cache(self.cfg.ipv6_cache_file)

    # -------------------------------------------------------------------------
    def get_ip_cache(self, cache_file):
        """Return a common IP address entry."""
        re_comment = re.compile(r'^\s*[;#]')

        if not cache_file.exists():
            if self.verbose > 2:
                LOG.debug(_('File {!r} not found.').format(cache_file))
            return None

        LOG.debug(_('Reading IP address from {!r}...').format(str(cache_file)))
        has_errors = False
        try:
            cont = self.read_file(str(cache_file), quiet=True)
        except (IOError, IoTimeoutError) as e:
            LOG.error(str(e))
            has_errors = True

        if not has_errors:
            address = None
            lines = cont.splitlines()
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                if re_comment.match(line):
                    continue
                try:
                    addr = ipaddress.ip_address(line)
                except ValueError as e:
                    msg = _('Line {li!r} in {f!r} is not a valid IP address:').format(
                        li=line, f=str(cache_file)) + ' ' + str(e)
                    LOG.error(msg)
                    continue
                address = addr
                break
            return address

        if self.exit_value <= 1:
            self.exit_value = 5
        return None

    # -------------------------------------------------------------------------
    def resolve_address(self, name, nameservers=None, address_family=None):
        """Try to resolve a name to a list of Ip addresses."""
        if not HAS_DNS_MODULE:
            return self.get_address(name, address_family=address_family)

        family = self.get_address_famlily_int(address_family)

        addresses = []
        # A normal resolver based on /etc/resolv.conf
        resolver = dns.resolver.Resolver()
        if nameservers:
            resolver.nameservers = nameservers
        if self.verbose > 3:
            LOG.debug(_('Using resolver:') + '\n' + pp(resolver.__dict__))

        if family in (0, 6):
            try:
                answer = resolver.resolve(name, 'AAAA')
                for rd in answer.rrset:
                    address = ipaddress.ip_address(str(rd))
                    if address not in addresses:
                        addresses.append(address)
            except (NoAnswer, NXDOMAIN) as e:
                if self.verbose > 1:
                    msg = _('Did not found a {t} address for {n}:').format(t='IPv6', n=name)
                    LOG.debug(msg + ' ' + str(e))

        if family in (0, 4):
            try:
                answer = resolver.resolve(name, 'A')
                for rd in answer.rrset:
                    address = ipaddress.ip_address(str(rd))
                    if address not in addresses:
                        addresses.append(address)
            except (NoAnswer, NXDOMAIN) as e:
                if self.verbose > 1:
                    msg = _('Did not found a {t} address for {n}:').format(t='IPv4', n=name)
                    LOG.debug(msg + ' ' + str(e))

        return addresses

    # -------------------------------------------------------------------------
    def get_ns_of_zone(self, zone, nameservers=None, address_family=None):
        """Try to get a list of the nameservers of the given zone."""
        if not HAS_DNS_MODULE:
            msg = _('Cannot execute {method}() - module {mod!r} could not imported.').format(
                method='get_ns_of_zone', mod='dns')
            raise RuntimeError(msg)

        ns_list = []
        resolver = dns.resolver.Resolver()
        if nameservers:
            resolver.nameservers = nameservers
        if self.verbose > 3:
            LOG.debug(_('Using resolver:') + '\n' + pp(resolver.__dict__))

        try:
            answer = resolver.resolve(zone, 'NS')
            for rd in answer.rrset:
                ns_name = str(rd)
                adresses = self.resolve_address(
                    ns_name, nameservers=nameservers, address_family=address_family)
                if adresses:
                    for address in adresses:
                        if address not in ns_list:
                            ns_list.append(ns_list)
        except (NoAnswer, NXDOMAIN) as e:
            if self.verbose > 1:
                msg = _('Did not found a {t} entry for zone {z}:').format(t='NS', n=zone)
                LOG.debug(msg + ' ' + str(e))

        return ns_list

    # -------------------------------------------------------------------------
    def get_mx_of_zone(self, zone, nameservers=None, address_family=None, as_text=True):
        """Try to get a list of the mail exchangers of the given zone."""
        if not HAS_DNS_MODULE:
            msg = _('Cannot execute {method}() - module {mod!r} could not imported.').format(
                method='get_mx_of_zone', mod='dns')
            raise RuntimeError(msg)

        mx_list = []
        resolver = dns.resolver.Resolver()
        if nameservers:
            resolver.nameservers = nameservers
        if self.verbose > 3:
            LOG.debug(_('Using resolver:') + '\n' + pp(resolver.__dict__))

        try:
            answer = resolver.resolve(zone, 'MX')
            for rd in answer.rrset:
                if as_text:
                    mx_list.append(str(rd))
                else:
                    mx_list.append(rd)

        except (NoAnswer, NXDOMAIN) as e:
            if self.verbose > 1:
                msg = _('Did not found a {t} entry for zone {z}:').format(t='MX', n=zone)
                LOG.debug(msg + ' ' + str(e))

        return mx_list


# =============================================================================
if __name__ == '__main__':

    pass

# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 list
