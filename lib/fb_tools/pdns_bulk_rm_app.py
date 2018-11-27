#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: Frank Brehm
@contact: frank.brehm@pixelpark.com
@copyright: © 2018 by Frank Brehm, Berlin
@summary: The module for the 'pdns-bulk-remove' application object.
"""
from __future__ import absolute_import

# Standard modules
import logging
import textwrap
import argparse
import getpass
import pathlib
import sys
import os
import re

# Third party modules

# Own modules
from . import __version__ as GLOBAL_VERSION

from .common import pp, to_bool

from .app import BaseApplication

from .config import CfgFileOptionAction

from .pdns_bulk_rm_cfg import PdnsBulkRmCfg

from .errors import FbAppError

from .pdns import DEFAULT_PORT, DEFAULT_API_PREFIX

from .pdns.server import PowerDNSServer

__version__ = '0.3.2'
LOG = logging.getLogger(__name__)


# =============================================================================
class PdnsBulkRmError(FbAppError):
    """ Base exception class for all exceptions in this application."""
    pass


# =============================================================================
class PdnsBulkRmApp(BaseApplication):
    """
    Class for the application object.
    """

    # -------------------------------------------------------------------------
    def __init__(
        self, appname=None, verbose=0, version=GLOBAL_VERSION, base_dir=None,
            initialized=False, usage=None, description=None,
            argparse_epilog=None, argparse_prefix_chars='-', env_prefix=None):

        desc = textwrap.dedent("""\
            Removes the given addresses (A-, AAAA- or CNAME-Records) completety from
            PowerDNS. If there are multiple entries to a DNS-Name, all appropriate
            records are removed. Additionally all appropriate reverse entries (PTR-records)
            were also removed.
            """).strip()

        self._cfg_file = None
        self.config = None
        self.pdns = None
        self._rm_reverse = True

        self.address_file = None

        self.addresses = []

        super(PdnsBulkRmApp, self).__init__(
            appname=appname, verbose=verbose, version=version, base_dir=base_dir,
            description=desc, initialized=False,
        )

        self.initialized = True

    # -------------------------------------------------------------------------
    @property
    def cfg_file(self):
        """Configuration file."""
        return self._cfg_file

    # -------------------------------------------------------------------------
    @property
    def rm_reverse(self):
        """Flag indicating, that the reverse DNS entries (PTR records)
            should not be removed."""
        return self._rm_reverse

    @rm_reverse.setter
    def rm_reverse(self, value):
        self._rm_reverse = to_bool(value)

    # -------------------------------------------------------------------------
    def as_dict(self, short=True):
        """
        Transforms the elements of the object into a dict

        @param short: don't include local properties in resulting dict.
        @type short: bool

        @return: structure as dict
        @rtype:  dict
        """

        res = super(PdnsBulkRmApp, self).as_dict(short=short)
        res['cfg_file'] = self.cfg_file
        res['rm_reverse'] = self.rm_reverse

        return res

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

        self.config = PdnsBulkRmCfg(
            appname=self.appname, verbose=self.verbose, base_dir=self.base_dir,
            config_file=self.cfg_file)

        self.config.read()
        if self.config.verbose > self.verbose:
            self.verbose = self.config.verbose
        self.config.initialized = True

        if self.verbose > 3:
            LOG.debug("Read configuration:\n{}".format(pp(self.config.as_dict())))

        self.perform_arg_parser_pdns()

        if self.address_file:
            self.read_address_file()

        if not self.addresses:
            LOG.error("No addresses to remove given.")
            self.exit(1)

        self.pdns = PowerDNSServer(
            appname=self.appname, verbose=self.verbose, base_dir=self.base_dir,
            master_server=self.config.pdns_master, port=self.config.pdns_api_port,
            key=self.config.pdns_api_key, use_https=self.config.pdns_api_https,
            path_prefix=self.config.pdns_api_prefix,
            simulate=self.simulate, force=self.force, initialized=True,
        )

        self.pdns.initialized = True
        self.initialized = True

    # -------------------------------------------------------------------------
    def init_arg_parser(self):
        """
        Public available method to initiate the argument parser.
        """

        super(PdnsBulkRmApp, self).init_arg_parser()

        default_cfg_file = self.base_dir.joinpath('etc').joinpath(self.appname + '.ini')

        self.arg_parser.add_argument(
            '-c', '--config', '--config-file', dest='cfg_file', metavar='FILE',
            action=CfgFileOptionAction,
            help="Configuration file (default: {!r})".format(default_cfg_file)
        )

        pdns_group = self.arg_parser.add_argument_group('PowerDNS options')

        pdns_group.add_argument(
            '-H', '--host', dest='host',
            help="PowerDNS server providing the API (Default: {!r}).".format(
                PdnsBulkRmCfg.default_pdns_master)
        )

        pdns_group.add_argument(
            '-P', '--port', dest='port', type=int,
            help="Port on PowerDNS server for API on (Default: {}).".format(DEFAULT_PORT))

        pdns_group.add_argument(
            '-K', '--key', '--api-key', metavar='KEY', dest='api_key',
            help="The API key for accessing the PowerDNS API."
        )

        pdns_group.add_argument(
            '--https', action="store_true", dest='https',
            help="Use HTTPS to access the PowerDNS API (Default: {}).".format(
                PdnsBulkRmCfg.default_pdns_api_https),
        )

        pdns_group.add_argument(
            '--prefix', dest='api_path_prefix',
            help=(
                "The global prefix for all paths for accessing the PowerDNS API "
                "(Default: {!r}).").format(DEFAULT_API_PREFIX)
        )

        # Source of the addresses - file or cmdline arguments
        # source_group = self.arg_parser.add_mutually_exclusive_group()

        self.arg_parser.add_argument(
            '-N', '--no-reverse', action="store_true", dest='no_reverse',
            help=(
                "Don't remove reverse DNS entries (PTR records) to the given addresses. "
                "(Default: False - reverse entries will be removed).")
        )

        self.arg_parser.add_argument(
            '-F', '--file', metavar='FILE', dest='addr_file', type=pathlib.Path,
            help=(
                "File containing the addresses to remove. The addresses must be "
                "whitespace separeted, lines may be commented out by prepending them "
                "with a hash sign '#'. This option is mutually exclusive with "
                "giving the addresses as command line arguments.")
        )

        self.arg_parser.add_argument(
            'addresses', metavar='ADDRESS', type=str, nargs='*',
            help=(
                "Addresses to remove. This option is mutually exclusive with "
                "the -F/--file option."),
        )

    # -------------------------------------------------------------------------
    def perform_arg_parser(self):

        if self.args.cfg_file:
            self._cfg_file = self.args.cfg_file

    # -------------------------------------------------------------------------
    def perform_arg_parser_pdns(self):
        """
        Public available method to execute some actions after parsing
        the command line parameters.
        """

        if self.args.addr_file and self.args.addresses:
            msg = (
                "The option '-F|--file' is mutually exclusive with giving the addresses "
                "as command line arguments.")
            LOG.error(msg)
            self.arg_parser.print_usage(sys.stderr)
            self.exit(1)

        if self.args.addr_file:
            afile = self.args.addr_file
            if not afile.exists():
                msg = "File {!r} does not exists.".format(str(afile))
                LOG.error(msg)
                self.exit(1)
            if not afile.is_file():
                msg = "File {!r} is not a regular file.".format(str(afile))
                LOG.error(msg)
                self.exit(1)
            if not os.access(str(afile), os.R_OK):
                msg = "No read access to file {!r}.".format(str(afile))
                LOG.error(msg)
                self.exit(1)
            self.address_file = afile

        if self.args.host:
            self.config.pdns_master = self.args.host
        if self.args.port:
            self.config.pdns_port = self.args.port
        if self.args.api_key:
            self.config.pdns_api_key = self.args.api_key
        if self.args.https:
            self.config.pdns_api_https = True
        if self.args.api_path_prefix is not None:
            self.config.pdns_api_prefix = self.args.api_path_prefix.strip()

        if self.args.no_reverse:
            self.rm_reverse = False

        if self.args.addresses:
            for address in self.args.addresses:
                self.addresses.append(address)

    # -------------------------------------------------------------------------
    def read_address_file(self):

        content = self.read_file(self.address_file)
        if self.verbose > 2:
            LOG.debug("Content of {f!r}:\n{c}".format(f=str(self.address_file), c=content))

        re_comment = re.compile(r'\s*#.*')
        re_whitespace = re.compile(r'\s+')

        addresses = []
        for line in content.splitlines():
            l = re_comment.sub('', line).strip()
            if l == '':
                continue
            for token in re_whitespace.split(l):
                addresses.append(token)

        if addresses:
            self.addresses = addresses

        if not self.addresses:
            LOG.error("No addresses to remove found in {!r}.".format(str(self.address_file)))
            self.exit(1)

    # -------------------------------------------------------------------------
    def _run(self):

        LOG.info("Starting {a!r}, version {v!r} ...".format(
            a=self.appname, v=self.version))

        ret = 0
#        try:
#            ret = self.get_vms()
#        finally:
#            # Aufräumen ...
#            LOG.debug("Closing ...")
#            self.vsphere.disconnect()
#            self.vsphere = None

        self.exit(ret)


# =============================================================================
if __name__ == "__main__":

    pass

# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 list
