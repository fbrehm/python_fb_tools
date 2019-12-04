#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: Frank Brehm
@contact: frank.brehm@pixelpark.com
@copyright: © 2019 by Frank Brehm, Berlin
@summary: The base module for all DDNS related classes.
"""
from __future__ import absolute_import, print_function

# Standard modules
import logging
import copy
import sys
import socket
import errno
import os
import ipaddress
import re

# Third party modules
import requests
import urllib3
import json

# Own modules
from .. import __version__ as GLOBAL_VERSION
from .. import DDNS_CFG_BASENAME

from ..errors import IoTimeoutError

from ..xlate import XLATOR, format_list

from ..common import pp

from ..app import BaseApplication, DirectoryOptionAction

from ..config import CfgFileOptionAction

from ..errors import FbAppError

from .config import DdnsConfiguration

__version__ = '0.4.3'
LOG = logging.getLogger(__name__)

_ = XLATOR.gettext


# =============================================================================
class DdnsAppError(FbAppError):
    """ Base exception class for all exceptions in this application."""
    pass


# =============================================================================
class DdnsRequestError(DdnsAppError):
    """Base class for more complex exceptions"""

    # -------------------------------------------------------------------------
    def __init__(self, code, content, url=None):
        self.code = code
        self.content = content
        self.url = url

    # -------------------------------------------------------------------------
    def __str__(self):

        msg = _("Got an error {c} on requesting {u!r}: {m}").format(
            c=self.code, u=self.url, m=self.content)
        return msg

# =============================================================================
class WorkDirError(DdnsAppError):
    """Special exception class with problems with the working directory."""

    pass


# =============================================================================
class WorkDirNotExistsError(WorkDirError, FileNotFoundError):
    """Special exception class, if working diretory does not exists."""

    # -------------------------------------------------------------------------
    def __init__(self, workdir):

        super(WorkDirNotExistsError, self).__init__(
            errno.ENOENT, _("Directory does not exists"), str(workdir))


# =============================================================================
class WorkDirNotDirError(WorkDirError, NotADirectoryError):
    """Special exception class, if path to working diretory is not a directory."""

    # -------------------------------------------------------------------------
    def __init__(self, workdir):

        super(WorkDirNotDirError, self).__init__(
            errno.ENOTDIR, _("Path is not a directory"), str(workdir))


# =============================================================================
class WorkDirAccessError(WorkDirError, PermissionError):
    """Special exception class, if working diretory is not accessible."""

    # -------------------------------------------------------------------------
    def __init__(self, workdir, msg=None):

        if not msg:
            msg = _("Invalid permissions")

        super(WorkDirAccessError, self).__init__(errno.EACCES, msg, str(workdir))


# =============================================================================
class BaseDdnsApplication(BaseApplication):
    """
    Class for the application objects.
    """

    library_name = "ddns-client"
    loglevel_requests_set = False

    # -------------------------------------------------------------------------
    def __init__(
        self, appname=None, verbose=0, version=GLOBAL_VERSION, base_dir=None,
            initialized=False, usage=None, description=None,
            argparse_epilog=None, argparse_prefix_chars='-', env_prefix=None):

        if description is None:
            description = _("This is a base DDNS related application.")

        self._cfg_dir = None
        self._cfg_file = None
        self.config = None
        self._user_agent = '{}/{}'.format(self.library_name, GLOBAL_VERSION)

        super(BaseDdnsApplication, self).__init__(
            appname=appname, verbose=verbose, version=version, base_dir=base_dir,
            description=description, initialized=False,
        )

        if initialized:
            self.initialized = True

    # -------------------------------------------------------------------------
    @property
    def cfg_dir(self):
        """The directory containing the configuration file."""
        return self._cfg_dir

    # -------------------------------------------------------------------------
    @property
    def cfg_file(self):
        """Configuration file."""
        return self._cfg_file

    # -----------------------------------------------------------
    @property
    def user_agent(self):
        "The name of the user agent used in API calls."
        return self._user_agent

    @user_agent.setter
    def user_agent(self, value):
        if value is None or str(value).strip() == '':
            raise DdnsAppError(_("Invalid user agent {!r} given.").format(value))
        self._user_agent = str(value).strip()

    # -------------------------------------------------------------------------
    def as_dict(self, short=True):
        """
        Transforms the elements of the object into a dict

        @param short: don't include local properties in resulting dict.
        @type short: bool

        @return: structure as dict
        @rtype:  dict
        """

        res = super(BaseDdnsApplication, self).as_dict(short=short)
        res['cfg_dir'] = self.cfg_dir
        res['cfg_file'] = self.cfg_file
        res['user_agent'] = self.user_agent

        return res

    # -------------------------------------------------------------------------
    def init_arg_parser(self):
        """
        Public available method to initiate the argument parser.
        """

        super(BaseDdnsApplication, self).init_arg_parser()

        ddns_group = self.arg_parser.add_argument_group(_('DDNS options'))

        self._cfg_dir = self.base_dir.joinpath('etc')
        self._cfg_file = self.cfg_dir.joinpath(DDNS_CFG_BASENAME)
        default_cfg_file = copy.copy(self.cfg_file)
        valid_list = copy.copy(DdnsConfiguration.valid_protocols)

        protocol_group = ddns_group.add_mutually_exclusive_group()

        ipv4_help = getattr(self, '_ipv4_help', None)
        ipv6_help = getattr(self, '_ipv6_help', None)
        proto_help = getattr(self, '_proto_help', None)

        if ipv4_help is None:
            ipv4_help = _("Perform action only for {}.").format('IPv4')

        if ipv6_help is None:
            ipv6_help = _("Perform action only for {}.").format('IPv6')

        if proto_help is None:
            proto_help = _(
                "The IP protocol, for which the action should be performed "
                "(one of {c}, default {d!r}).").format(
                    c=format_list(valid_list, do_repr=True, style='or'), d='any')

        protocol_group.add_argument(
            '-4', '--ipv4', dest='ipv4', action="store_true", help=ipv4_help,
        )

        protocol_group.add_argument(
            '-6', '--ipv6', dest='ipv6', action="store_true", help=ipv6_help,
        )

        protocol_group.add_argument(
            '-p', '--protocol', dest='protocol', metavar=_('PROTOCOL'),
            choices=valid_list, help=proto_help,
        )

        dir_must_exists = False
        writeable = False
        if self.appname == 'update-ddns':
            dir_must_exists = True
            writeable = True
        ddns_group.add_argument(
            '-d', '--dir', '--work-directory', dest='directory', metavar=_('DIRECTORY'),
            action=DirectoryOptionAction, must_exists=dir_must_exists, writeable=writeable,
            help=_(
                "The directory, where to read and write the cache files of the "
                "evaluated IP addresses (default: {!r}).").format(
                str(DdnsConfiguration.default_working_dir)),
        )

        ddns_group.add_argument(
            '-T', '--timeout', dest='timeout', type=int, metavar=_('SECONDS'),
            help=_("The timeout in seconds for Web requests (default: {}).").format(
                DdnsConfiguration.default_timeout),
        )

        ddns_group.add_argument(
            '-c', '--config', '--config-file', dest='cfg_file', metavar=_('FILE'),
            action=CfgFileOptionAction,
            help=_("Configuration file (default: {!r})").format(str(default_cfg_file))
        )

    # -------------------------------------------------------------------------
    def post_init(self):
        """
        Method to execute before calling run(). Here could be done some
        finishing actions after reading in commandline parameters,
        configuration a.s.o.

        This method could be overwritten by descendant classes, these
        methhods should allways include a call to post_init() of the
        parent class.

        """

        self.initialized = False

        self.init_logging()

        self.perform_arg_parser()

        if self.args.cfg_file:
            self._cfg_file = self.args.cfg_file
            self._cfg_dir = self.cfg_file.parent

        self.config = DdnsConfiguration(
            appname=self.appname, verbose=self.verbose, base_dir=self.base_dir,
            config_file=self.cfg_file)

        self.config.read()
        if self.config.verbose > self.verbose:
            self.verbose = self.config.verbose
        self.config.initialized = True

        if self.verbose > 3:
            LOG.debug("Read configuration:\n{}".format(pp(self.config.as_dict())))

        if self.args.ipv4:
            self.config.protocol = 'ipv4'
        elif self.args.ipv6:
            self.config.protocol = 'ipv6'
        elif self.args.protocol:
            if self.args.protocol == 'both':
                self.config.protocol = 'any'
            else:
                self.config.protocol = self.args.protocol

        if self.args.timeout:
            try:
                self.config.timeout = self.args.timeout
            except (ValueError, KeyError) as e:
                msg = _("Invalid value {!r} as timeout:").format(self.args.timeout) + ' ' + str(e)
                LOG.error(msg)
                print()
                self.arg_parser.print_usage(sys.stdout)
                self.exit(1)

        if self.args.directory:
            self.config.working_dir = self.args.directory

        if not self.loglevel_requests_set:
            msg = _("Setting Loglevel of the {m} module to {ll}.").format(
                m='requests', ll='WARNING')
            LOG.debug(msg)
            logging.getLogger("requests").setLevel(logging.WARNING)
            self.loglevel_requests_set = True

        self.initialized = True

    # -------------------------------------------------------------------------
    def get_my_ipv(self, protocol):

        LOG.debug(_("Trying to get my public IPv{} address.").format(protocol))

        url = self.config.get_ipv4_url
        if protocol == 6:
            url = self.config.get_ipv6_url

        try:
            json_response = self.perform_request(url)
        except DdnsAppError as e:
            LOG.error(str(e))
            return None
        if self.verbose > 0:
            LOG.debug(_("Got a response:") + '\n' + pp(json_response))

        return json_response['IP']

    # -------------------------------------------------------------------------
    def perform_request(self, url, method='GET', data=None, headers=None, may_simulate=False):
        """Performing the underlying Web request."""

        if headers is None:
            headers = dict()

        if self.verbose > 1:
            LOG.debug(_("Request method: {!r}").format(method))

        if data and self.verbose > 1:
            data_out = "{!r}".format(data)
            try:
                data_out = json.loads(data)
            except ValueError:
                pass
            else:
                data_out = pp(data_out)
            LOG.debug("Data:\n{}".format(data_out))
            if self.verbose > 2:
                LOG.debug("RAW data:\n{}".format(data))

        headers.update({'User-Agent': self.user_agent})
        headers.update({'Content-Type': 'application/json'})
        if self.verbose > 1:
            LOG.debug("Headers:\n{}".format(pp(headers)))

        if may_simulate and self.simulate:
            LOG.debug(_("Simulation mode, Request will not be sent."))
            return ''

        try:

            session = requests.Session()
            response = session.request(
                method, url, data=data, headers=headers, timeout=self.config.timeout)

        except (
                socket.timeout, urllib3.exceptions.ConnectTimeoutError,
                urllib3.exceptions.MaxRetryError, requests.exceptions.ConnectionError,
                requests.exceptions.ConnectTimeout) as e:
            msg = _("Got a {c} on requesting {u!r}: {e}.").format(
                c=e.__class__.__name__, u=url, e=e)
            raise DdnsAppError(msg)

        try:
            self._eval_response(url, response)
        except ValueError:
            raise DdnsAppError(_('Failed to parse the response'), response.text)

        if self.verbose > 3:
            LOG.debug("RAW response: {!r}.".format(response.text))
        if not response.text:
            return ''

        json_response = response.json()
        if self.verbose > 3:
            LOG.debug("JSON response:\n{}".format(pp(json_response)))

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
        """Verifying existence and accessibility of working directory."""

        if self.verbose > 1:
            LOG.debug(_(
                "Checking existence and accessibility of working directory {!r} ...").format(
                str(self.config.working_dir)))

        if not self.config.working_dir.exists():
            raise WorkDirNotExistsError(self.config.working_dir)

        if not self.config.working_dir.is_dir():
            raise WorkDirNotDirError(self.config.working_dir)

        if not os.access(str(self.config.working_dir), os.R_OK):
            raise WorkDirAccessError(
                self.config.working_dir, _("No read access"))

        if not os.access(str(self.config.working_dir), os.W_OK):
            raise WorkDirAccessError(
                self.config.working_dir, _("No write access"))

    # -------------------------------------------------------------------------
    def write_ipv4_cache(self, address):
        self.write_ip_cache(address, self.config.ipv4_cache_file)

    # -------------------------------------------------------------------------
    def write_ipv6_cache(self, address):
        self.write_ip_cache(address, self.config.ipv6_cache_file)

    # -------------------------------------------------------------------------
    def write_ip_cache(self, address, cache_file):

        LOG.debug(_(
            "Writing IP address {a!r} into {f!r} ...").format(
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
        return self.get_ip_cache(self.config.ipv4_cache_file)

    # -------------------------------------------------------------------------
    def get_ipv6_cache(self):
        return self.get_ip_cache(self.config.ipv6_cache_file)

    # -------------------------------------------------------------------------
    def get_ip_cache(self, cache_file):

        re_comment = re.compile(r'^\s*[;#]')

        if not cache_file.exists():
            if self.verbose > 2:
                LOG.debug(_("File {!r} not found.").format(cache_file))
            return None

        LOG.debug(_("Reading IP address from {!r}...").format(str(cache_file)))
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
                    msg = _("Line {li!r} in {f!r} is not a valid IP address:").format(
                        li=line, f=str(cache_file)) + ' ' + str(e)
                    LOG.error(msg)
                    continue
                address = addr
                break
            return address

        if self.exit_value <= 1:
            self.exit_value = 5
        return None


# =============================================================================
if __name__ == "__main__":

    pass

# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 list
