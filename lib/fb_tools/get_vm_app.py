#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: Frank Brehm
@contact: frank.brehm@pixelpark.com
@copyright: © 2018 by Frank Brehm, Berlin
@summary: The module for the application object.
"""
from __future__ import absolute_import

# Standard modules
import sys
import os
import logging
import re
import traceback
import textwrap
import argparse
import getpass
import argparse
import pathlib

# Third party modules

# Own modules
from . import __version__ as GLOBAL_VERSION

from .common import pp, caller_search_path

from .app import BaseApplication

from .errors import FbAppError, ExpectedHandlerError, CommandNotFoundError

from .get_vm_cfg import GetVmConfiguration

__version__ = '0.1.1'
LOG = logging.getLogger(__name__)


# =============================================================================
class GetVmAppError(FbAppError):
    """ Base exception class for all exceptions in this application."""
    pass

# =============================================================================
class CfgFileOptionAction(argparse.Action):

    # -------------------------------------------------------------------------
    def __init__(self, option_strings, *args, **kwargs):

        super(CfgFileOptionAction, self).__init__(
            option_strings=option_strings, *args, **kwargs)

    # -------------------------------------------------------------------------
    def __call__(self, parser, namespace, values, option_string=None):

        if values is None:
            setattr(namespace, self.dest, None)
            return

        path = pathlib.Path(values)
        if not path.exists():
            msg = "File {!r} does not exists.".format(values)
            raise argparse.ArgumentError(self, msg)
        if not path.is_file():
            msg = "File {!r} is not a regular file.".format(values)
            raise argparse.ArgumentError(self, msg)

        setattr(namespace, self.dest, path.resolve())


# =============================================================================
class GetVmApplication(BaseApplication):
    """
    Class for the application objects.
    """

    # -------------------------------------------------------------------------
    def __init__(
        self, appname=None, verbose=0, version=GLOBAL_VERSION, base_dir=None,
            initialized=False, usage=None, description=None,
            argparse_epilog=None, argparse_prefix_chars='-', env_prefix=None):

        desc = textwrap.dedent("""\
            Tries to get information about the given virtual maschines in
            VMWare VSphere and print it out.
            """).strip()

        self._cfg_file = None
        self.config = None

        super(GetVmApplication, self).__init__(
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
    def as_dict(self, short=True):
        """
        Transforms the elements of the object into a dict

        @param short: don't include local properties in resulting dict.
        @type short: bool

        @return: structure as dict
        @rtype:  dict
        """

        res = super(GetVmApplication, self).as_dict(short=short)
        res['cfg_file'] = self.cfg_file

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

        self.config = CrTplConfiguration(
            appname=self.appname, verbose=self.verbose, base_dir=self.base_dir,
            config_file=self.cfg_file)
        #self.config.config_file = self.cfg_file

        self.config.read()
        if self.config.verbose > self.verbose:
            self.verbose = self.config.verbose
        self.config.initialized = True

        if self.verbose > 3:
            LOG.debug("Read configuration:\n{}".format(pp(self.config.as_dict())))

        self.perform_arg_parser_vmware()

        if not self.config.password:
            prompt = 'Enter password for host {h!r} and user {u!r}: '.format(
                h=self.config.vsphere_host, u=self.config.vsphere_user)
            self.config.password = getpass.getpass(prompt=prompt)

        self.initialized = True

    # -------------------------------------------------------------------------
    def init_arg_parser(self):
        """
        Public available method to initiate the argument parser.
        """

        super(GetVmApplication, self).init_arg_parser()

        default_cfg_file = self.base_dir.joinpath('etc').joinpath(self.appname + '.ini')

        self.arg_parser.add_argument(
            '-c', '--config', '--config-file', dest='cfg_file', metavar='FILE',
            action=CfgFileOptionAction,
            help="Configuration file (default: {!r})".format(default_cfg_file)
        )

        vmware_group = self.arg_parser.add_argument_group('VMWare options')

        vmware_group.add_argument(
            '-H', '--host', dest='host',
            help="Remote vSphere host to connect to (Default: {!r}).".format(
                CrTplConfiguration.default_vsphere_host)
        )

        vmware_group.add_argument(
            '-p', '--port', dest='port', type=int,
            help="Port on vSphere host to connect on (Default: {}).".format(
                CrTplConfiguration.default_vsphere_port)
        )

        vmware_group.add_argument(
            '-U', '--user', dest='user',
            help="User name to use when connecting to vSphere host (Default: {!r}).".format(
                CrTplConfiguration.default_vsphere_user)
        )

        vmware_group.add_argument(
            '-P', '--password', dest='password',
            help="Password to use when connecting to vSphere host.",
        )

    # -------------------------------------------------------------------------
    def perform_arg_parser(self):

        if self.args.cfg_file:
            self._cfg_file = self.args.cfg_file

    # -------------------------------------------------------------------------
    def perform_arg_parser_vmware(self):
        """
        Public available method to execute some actions after parsing
        the command line parameters.
        """

        if self.args.host:
            self.config.vsphere_host = self.args.host
        if self.args.port:
            self.config.vsphere_port = self.args.port
        if self.args.user:
            self.config.vsphere_user = self.args.user
        if self.args.password:
            self.config.password = self.args.password

    # -------------------------------------------------------------------------
    def _run(self):
        """
        Dummy function as main routine.

        MUST be overwritten by descendant classes.

        """

        LOG.debug("Starting {a!r}, version {v!r} ...".format(
            a=self.appname, v=self.version))
        return


# =============================================================================

if __name__ == "__main__":

    pass

# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 list
