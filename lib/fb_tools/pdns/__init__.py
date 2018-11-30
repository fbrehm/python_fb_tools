#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: Frank Brehm
@contact: frank@brehm-online.com
@copyright: © 2018 Frank Brehm, Berlin
@summary: The module for a base PowerDNS handler object.
"""
from __future__ import absolute_import

# Standard modules
import os
import logging
import re
import json
import copy
import socket
import ipaddress

from abc import ABCMeta

# Third party modules
import requests
import urllib3

from six import add_metaclass

# Own modules
from ..common import pp, to_bool, RE_DOT_AT_END

from ..handling_obj import HandlingObject

from .. import __version__ as __global_version__

from .errors import PowerDNSHandlerError, PDNSApiError, PDNSApiNotAuthorizedError
from .errors import PDNSApiNotFoundError, PDNSApiValidationError, PDNSApiRateLimitExceededError

__version__ = '0.5.1'
LOG = logging.getLogger(__name__)
_LIBRARY_NAME = "pp-pdns-api-client"

LOGLEVEL_REQUESTS_SET = False

DEFAULT_PORT = 8081
DEFAULT_TIMEOUT = 20
DEFAULT_API_PREFIX = '/api/v1'
DEFAULT_USE_HTTPS = False

# =============================================================================
@add_metaclass(ABCMeta)
class BasePowerDNSHandler(HandlingObject):
    """
    Base class for a PowerDNS handler object.
    May not be instantiated.
    """

    default_port = DEFAULT_PORT
    default_timeout = DEFAULT_TIMEOUT
    default_api_servername = "localhost"

    loglevel_requests_set = False

    re_request_id = re.compile(r'/requests/([-a-f0-9]+)/', re.IGNORECASE)

    # -------------------------------------------------------------------------
    def __init__(
        self, appname=None, verbose=0, version=__version__, base_dir=None,
            master_server=None, port=DEFAULT_PORT, key=None, use_https=False, timeout=None,
            path_prefix=DEFAULT_API_PREFIX, simulate=None, force=None, terminal_has_colors=False,
            initialized=False,):

        self._master_server = master_server
        self._port = self.default_port
        self._key = key
        self._use_https = False
        self._path_prefix = path_prefix
        self._timeout = self.default_timeout
        self._user_agent = '{}/{}'.format(_LIBRARY_NAME, __global_version__)
        self._api_servername = self.default_api_servername

        super(BasePowerDNSHandler, self).__init__(
            appname=appname, verbose=verbose, version=version, base_dir=base_dir,
            simulate=simulate, force=force, terminal_has_colors=terminal_has_colors,
            initialized=False,
        )

        self.use_https = use_https
        self.port = port
        self.timeout = timeout

        global LOGLEVEL_REQUESTS_SET

        if not LOGLEVEL_REQUESTS_SET:
            LOG.debug("Setting Loglevel of the requests module to WARNING")
            logging.getLogger("requests").setLevel(logging.WARNING)
            LOGLEVEL_REQUESTS_SET = True

        self.initialized = initialized

    # -----------------------------------------------------------
    @property
    def master_server(self):
        """The hostname or address of the PowerDNS master server."""
        return self._master_server

    @master_server.setter
    def master_server(self, value):
        if value is None:
            self._master_server = None
            return

        val = str(value).strip().lower()
        if val == '':
            self._master_server = None
        else:
            self._master_server = val

    # -----------------------------------------------------------
    @property
    def port(self):
        """The TCP port number of the PowerDNS API."""
        return self._port

    @port.setter
    def port(self, value):
        if value is None:
            self._port = self.default_port
            return
        val = int(value)
        err_msg = (
            "Invalid port number {!r} for the PowerDNS API, "
            "must be 0 < PORT < 65536.")
        if val <= 0 or val > 65536:
            msg = err_msg.format(value)
            raise ValueError(msg)
        self._port = val

    # -----------------------------------------------------------
    @property
    def key(self):
        """The key used to authenticate against the PowerDNS API."""
        return self._key

    @key.setter
    def key(self, value):
        if value is None:
            self._key = None
            return

        val = str(value)
        if val == '':
            self._key = None
        else:
            self._key = val

    # -----------------------------------------------------------
    @property
    def use_https(self):
        """Should be HTTPS used to communicate with the API?"""
        return self._use_https

    @use_https.setter
    def use_https(self, value):
        self._use_https = to_bool(value)

    # -----------------------------------------------------------
    @property
    def path_prefix(self):
        """The hostname or address of the PowerDNS master server."""
        return self._path_prefix

    @path_prefix.setter
    def path_prefix(self, value):
        if value is None:
            self._path_prefix = None
            return

        val = str(value).strip()
        if val == '':
            self._path_prefix = None
        else:
            if not os.path.isabs(val):
                msg = "The path prefix {!r} must be an absolute path.".format(value)
                raise ValueError(msg)
            self._path_prefix = val

    # -----------------------------------------------------------
    @property
    def timeout(self):
        """The timeout in seconds for requesting the PowerDNS API."""
        return self._timeout

    @timeout.setter
    def timeout(self, value):
        if value is None:
            self._timeout = self.default_timeout
            return
        val = int(value)
        err_msg = (
            "Invalid timeout {!r} for requesting the PowerDNS API, "
            "must be 0 < SECONDS < 3600.")
        if val <= 0 or val > 3600:
            msg = err_msg.format(value)
            raise ValueError(msg)
        self._timeout = val

    # -----------------------------------------------------------
    @property
    def user_agent(self):
        "The name of the user agent used in API calls."
        return self._user_agent

    @user_agent.setter
    def user_agent(self, value):
        if value is None or str(value).strip() == '':
            raise PowerDNSHandlerError("Invalid user agent {!r} given.".format(value))
        self._user_agent = str(value).strip()

    # -----------------------------------------------------------
    @property
    def api_servername(self):
        "The (virtual) name of the PowerDNS server used in API calls."
        return self._api_servername

    @api_servername.setter
    def api_servername(self, value):
        if value is None or str(value).strip() == '':
            raise PowerDNSHandlerError("Invalid API server name {!r} given.".format(value))
        self._api_servername = str(value).strip()

    # -------------------------------------------------------------------------
    def as_dict(self, short=True):
        """
        Transforms the elements of the object into a dict

        @param short: don't include local properties in resulting dict.
        @type short: bool

        @return: structure as dict
        @rtype:  dict
        """

        res = super(BasePowerDNSHandler, self).as_dict(short=short)
        res['default_port'] = self.default_port
        res['default_timeout'] = self.default_timeout
        res['default_api_servername'] = self.default_api_servername
        res['master_server'] = self.master_server
        res['port'] = self.port
        res['use_https'] = self.use_https
        res['path_prefix'] = self.path_prefix
        res['timeout'] = self.timeout
        res['user_agent'] = self.user_agent
        res['api_servername'] = self.api_servername
        res['key'] = None
        if self.key:
            if self.verbose > 4:
                res['key'] = self.key
            else:
                res['key'] = '*******'

        return res

    # -------------------------------------------------------------------------
    @classmethod
    def _request_id(cls, headers):

        if 'location' not in headers:
            return None

        loc = headers['location']
        match = cls.re_request_id.search(loc)
        if match:
            return match.group(1)
        else:
            msg = "Failed to extract request ID from response header 'location': {!r}".format(loc)
            raise PowerDNSHandlerError(msg)

    # -------------------------------------------------------------------------
    def _build_url(self, path, no_prefix=False):

        if not os.path.isabs(path):
            msg = "The path {!r} must be an absolute path.".format(path)
            raise ValueError(msg)

        url = 'http://{}'.format(self.master_server)
        if self.use_https:
            url = 'https://{}'.format(self.master_server)
            if self.port != 443:
                url += ':{}'.format(self.port)
        else:
            if self.port != 80:
                url += ':{}'.format(self.port)

        if self.path_prefix and not no_prefix:
            url += self.path_prefix

        url += path

        if self.verbose > 1:
            LOG.debug("Used URL: {!r}".format(url))
        return url

    # -------------------------------------------------------------------------
    def perform_request(
        self, path, no_prefix=False, method='GET',
            data=None, headers=None, may_simulate=False):
        """Performing the underlying API request."""

        if headers is None:
            headers = dict()
        if self.key:
            headers['X-API-Key'] = self.key

        url = self._build_url(path, no_prefix=no_prefix)
        if self.verbose > 1:
            LOG.debug("Request method: {!r}".format(method))
        if data and self.verbose > 2:
            data_out = "{!r}".format(data)
            try:
                data_out = json.loads(data)
            except ValueError:
                pass
            else:
                data_out = pp(data_out)
            if self.verbose > 1:
                LOG.debug("Data:\n{}".format(data_out))
                LOG.debug("RAW data:\n{}".format(data))

        headers.update({'User-Agent': self.user_agent})
        headers.update({'Content-Type': 'application/json'})
        if self.verbose > 1:
            head_out = copy.copy(headers)
            if 'X-API-Key' in head_out and self.verbose <= 4:
                head_out['X-API-Key'] = '******'
            LOG.debug("Headers:\n{}".format(pp(head_out)))

        if may_simulate and self.simulate:
            LOG.debug("Simulation mode, Request will not be sent.")
            return ''

        try:

            session = requests.Session()
            response = session.request(
                method, url, data=data, headers=headers, timeout=self.timeout)

        except (
                socket.timeout, urllib3.exceptions.ConnectTimeoutError,
                urllib3.exceptions.MaxRetryError,
                requests.exceptions.ConnectTimeout) as e:
            msg = "Got a {c} on connecting to {h!r}: {e}.".format(
                c=e.__class__.__name__, h=self.master_server, e=e)
            raise PowerDNSHandlerError(msg)

        try:
            self._eval_response(url, response)

        except ValueError:
            raise PDNSApiError('Failed to parse the response', response.text)

        if self.verbose > 3:
            LOG.debug("RAW response: {!r}.".format(response.text))
        if not response.text:
            return ''

        json_response = response.json()
        if self.verbose > 3:
            LOG.debug("JSON response:\n{}".format(pp(json_response)))

        if 'location' in response.headers:
            json_response['requestId'] = self._request_id(response.headers)

        return json_response

    # -------------------------------------------------------------------------
    def _eval_response(self, url, response):

        if response.ok:
            return

        err = response.json()
        code = response.status_code
        msg = err['error']
        LOG.debug("Got an error response code {code}: {msg}".format(code=code, msg=msg))
        if response.status_code == 401:
            raise PDNSApiNotAuthorizedError(code, msg, url)
        if response.status_code == 404:
            raise PDNSApiNotFoundError(code, msg, url)
        if response.status_code == 422:
            raise PDNSApiValidationError(code, msg, url)
        if response.status_code == 429:
            raise PDNSApiRateLimitExceededError(code, msg, url)
        else:
            raise PDNSApiError(code, msg, url)

    # -------------------------------------------------------------------------
    def canon_name(self, name):

        ret = RE_DOT_AT_END.sub('.', name)
        return ret

    # -------------------------------------------------------------------------
    def name2fqdn(self, name, is_fqdn=False):

        fqdn = name

        if not is_fqdn:
            try:
                address = ipaddress.ip_address(name)
                fqdn = address.reverse_pointer
                is_fqdn = False
            except ValueError:
                if self.verbose > 3:
                    LOG.debug("Name {!r} is not a valid IP address.".format(name))
                is_fqdn = True
                fqdn = name

        if ':' in fqdn:
            LOG.error("Invalid FQDN {!r}.".format(fqdn))
            return None

        return self.canon_name(fqdn)

    # -------------------------------------------------------------------------
    def decanon_name(self, name):

        ret = RE_DOT_AT_END.sub('', name)
        return ret


# =============================================================================

if __name__ == "__main__":

    pass

# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 list
