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

import fb_tools

from fb_tools.common import pp, caller_search_path

from fb_tools.app import BaseApplication

from fb_tools.errors import FbAppError, ExpectedHandlerError, CommandNotFoundError

from .config import CrTplConfiguration

from .handler import CrTplHandler

__version__ = '0.6.4'
LOG = logging.getLogger(__name__)


# =============================================================================
class CrTplAppError(FbAppError):
    """ Base exception class for all exceptions in this application."""
    pass

# =============================================================================
class NrTemplatesOptionAction(argparse.Action):

    # -------------------------------------------------------------------------
    def __init__(self, option_strings, max_val, *args, **kwargs):

        self._max = max_val

        super(NrTemplatesOptionAction, self).__init__(
            option_strings=option_strings, *args, **kwargs)

    # -------------------------------------------------------------------------
    def __call__(self, parser, namespace, values, option_string=None):

        if values < 1:
            msg = "Value must be at least 1, {} was given.".format(values)
            raise argparse.ArgumentError(self, msg)

        if values >= self._max:
            msg = "Value must be at most {m} - {v} was given.".format(
                m=self._max - 1, v=values)
            raise argparse.ArgumentError(self, msg)

        setattr(namespace, self.dest, values)


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
class CrTplApplication(BaseApplication):
    """
    Class for the application objects.
    """

    re_prefix = re.compile(r'^[a-z0-9][a-z0-9_]*$', re.IGNORECASE)
    re_anum = re.compile(r'[^A-Z0-9_]+', re.IGNORECASE)

    # -------------------------------------------------------------------------
    def __init__(
        self, appname=None, verbose=0, version=GLOBAL_VERSION, base_dir=None,
            initialized=False, usage=None, description=None,
            argparse_epilog=None, argparse_prefix_chars='-', env_prefix=None):

        desc = textwrap.dedent("""\
            Creates in the given vSphere environment and cluster a template object,
            which can be used to spawn different virtual machines.
            """).strip()

        self._cfg_file = None
        self.config = None

        super(CrTplApplication, self).__init__(
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

        res = super(CrTplApplication, self).as_dict(short=short)
        res['cfg_file'] = self.cfg_file

        return res

#    # -------------------------------------------------------------------------
#    def init_logging(self):
#        """
#        Initialize the logger object.
#        It creates a colored loghandler with all output to STDERR.
#        Maybe overridden in descendant classes.
#
#        @return: None
#        """
#
#        log_level = logging.INFO
#        if self.verbose:
#            log_level = logging.DEBUG
#        elif self.quiet:
#            log_level = logging.WARNING
#
#        root_logger = logging.getLogger()
#        root_logger.setLevel(log_level)
#
#        # create formatter
#        format_str = ''
#        if self.verbose:
#            format_str = '[%(asctime)s]: '
#        format_str += self.appname + ': '
#        if self.verbose:
#            if self.verbose > 1:
#                format_str += '%(name)s(%(lineno)d) %(funcName)s() '
#            else:
#                format_str += '%(name)s '
#        format_str += '%(levelname)s - %(message)s'
#        formatter = None
#        if self.terminal_has_colors:
#            formatter = ColoredFormatter(format_str)
#        else:
#            formatter = logging.Formatter(format_str)
#
#        # create log handler for console output
#        lh_console = logging.StreamHandler(sys.stderr)
#        lh_console.setLevel(log_level)
#        lh_console.setFormatter(formatter)
#
#        root_logger.addHandler(lh_console)
#
#        if self.verbose < 3:
#            paramiko_logger = logging.getLogger('paramiko.transport')
#            if self.verbose < 1:
#                paramiko_logger.setLevel(logging.WARNING)
#            else:
#                paramiko_logger.setLevel(logging.INFO)
#
#        return

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

        self.handler = CrTplHandler(
            appname=self.appname, verbose=self.verbose, base_dir=self.base_dir,
            simulate=self.simulate, force=self.force, config=self.config,
            terminal_has_colors=self.terminal_has_colors)

        if self.args.rotate:
            self.handler.rotate_only = True
        if self.args.abort:
            self.handler.abort = True

        self.handler.vsphere.initialized = True
        self.handler.initialized = True
        self.initialized = True

    # -------------------------------------------------------------------------
    def init_arg_parser(self):
        """
        Public available method to initiate the argument parser.
        """

        super(CrTplApplication, self).init_arg_parser()

        default_cfg_file = self.base_dir.joinpath('etc').joinpath(self.appname + '.ini')

        self.arg_parser.add_argument(
            '-A', '--abort', dest='abort', action='store_true',
            help="Abort creation of VMWare template after successsful creation of template VM.",
        )

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

        vmware_group.add_argument(
            '-F', '--folder', dest='folder',
            help="Folder in vSphere, where to create the template (Default: {!r}).".format(
                CrTplConfiguration.default_folder)
        )

        vmware_group.add_argument(
            '-C', '--cluster', dest='cluster',
            help="Host cluster in vSphere, where to create the template (Default: {!r}).".format(
                CrTplConfiguration.default_vsphere_cluster)
        )

        vmware_group.add_argument(
            '-M', '--vm', dest='vm',
            help=(
                "The temporary VM, which will be created and converted into a "
                "template (Default: {!r}).").format(CrTplConfiguration.default_template_vm)
        )

        vmware_group.add_argument(
            '-T', '--template',
            help=(
                "The name of the created template as result of this script "
                "(Default: {!r}).").format(CrTplConfiguration.default_template_name)
        )

        vmware_group.add_argument(
            '-N', '--number', '--number-templates', dest='number', type=int, metavar='INT',
            action=NrTemplatesOptionAction, max_val=CrTplConfiguration.limit_max_nr_templates_stay,
            help=(
                "Maximum number of templates to stay in templates folder ("
                "1 <= x < {max_nr}, Default: {def_nr}).".format(
                    max_nr=CrTplConfiguration.limit_max_nr_templates_stay,
                    def_nr=CrTplConfiguration.default_max_nr_templates_stay))
        )

        vmware_group.add_argument(
            '-R', '--rotate', '--rotate-only', dest="rotate", action='store_true',
            help="Execute rortation of existing templates only, don't create a new one."
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
        if self.args.cluster:
            self.config.vsphere_cluster = self.args.cluster
        if self.args.folder:
            self.config.folder = self.args.folder
        if self.args.vm:
            self.config.template_vm = self.args.vm
        if self.args.template:
            self.config.template_name = self.args.template

        if self.args.number is not None:
            self.config.max_nr_templates_stay = self.args.number

    # -------------------------------------------------------------------------
    def _run(self):
        """
        Dummy function as main routine.

        MUST be overwritten by descendant classes.

        """

        LOG.info("Starting {a!r}, version {v!r} ...".format(
            a=self.appname, v=self.version))

        try:
            ret = self.handler()
            self.exit(ret)
        except ExpectedHandlerError as e:
            self.handle_error(str(e), "Temporary VM")
            self.exit(5)


# =============================================================================

if __name__ == "__main__":

    pass

# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 list
