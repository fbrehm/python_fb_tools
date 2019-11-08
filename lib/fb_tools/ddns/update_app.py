#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: Frank Brehm
@contact: frank.brehm@pixelpark.com
@copyright: © 2019 by Frank Brehm, Berlin
@summary: The module for the classes of the update-ddns application.
"""
from __future__ import absolute_import, print_function

# Standard modules
import logging
import copy
import sys
import time
import os

# Own modules
from .. import __version__ as GLOBAL_VERSION

from ..xlate import XLATOR, format_list

from ..common import pp, to_bool

from ..colored import ColoredFormatter

from . import DdnsAppError, DdnsRequestError, BaseDdnsApplication, WorkDirError
from . import WorkDirError, WorkDirNotExistsError, WorkDirNotDirError, WorkDirAccessError

from .config import DdnsConfiguration

__version__ = '0.1.0'
LOG = logging.getLogger(__name__)

_ = XLATOR.gettext


# =============================================================================
class UpdateDdnsApplication(BaseDdnsApplication):
    """
    Class for the application objects.
    """

    # -------------------------------------------------------------------------
    def __init__(
        self, appname=None, verbose=0, version=GLOBAL_VERSION, base_dir=None,
            initialized=False, usage=None, description=None,
            argparse_epilog=None, argparse_prefix_chars='-', env_prefix=None):

        self.last_ipv4_address = None
        self.last_ipv6_address = None

        if description is None:
            description = _(
                "Tries to update the A and/or AAAA record at ddns.de with the current "
                "IP address.")
        valid_proto_list = copy.copy(DdnsConfiguration.valid_protocols)

        self._ipv4_help = _("Update only the {} record with the public IP address.").format('A')
        self._ipv6_help = _("Update only the {} record with the public IP address.").format('AAAA')
        self._proto_help = _(
            "The IP protocol, for which the appropriate DNS record sould be updated with the "
            "public IP (one of {c}, default {d!r}).").format(c=format_list(
                valid_proto_list, do_repr=True, style='or'), d='any')

        super(UpdateDdnsApplication, self).__init__(
            appname=appname, verbose=verbose, version=version, base_dir=base_dir,
            description=description, initialized=False,
        )

        self.initialized = True

    # -------------------------------------------------------------------------
    def _get_log_formatter(self, is_term=True):

        # create formatter
        if is_term:
            format_str = ''
            if self.verbose > 1:
                format_str = '[%(asctime)s]: '
            format_str += self.appname + ': '
        else:
            format_str = '[%(asctime)s]: ' + self.appname + ': '
        if self.verbose:
            if self.verbose > 1:
                format_str += '%(name)s(%(lineno)d) %(funcName)s() '
            else:
                format_str += '%(name)s '
        format_str += '%(levelname)s - %(message)s'
        if is_term and self.terminal_has_colors:
            formatter = ColoredFormatter(format_str)
        else:
            formatter = logging.Formatter(format_str)

        return formatter

    # -------------------------------------------------------------------------
    def init_logging(self):
        """
        Initialize the logger object.
        It creates a colored loghandler with all output to STDERR.
        Maybe overridden in descendant classes.

        @return: None
        """

        log_level = logging.INFO
        if self.verbose:
            log_level = logging.DEBUG
        elif self.quiet:
            log_level = logging.WARNING

        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)

        formatter = self._get_log_formatter()

        # create log handler for console output
        lh_console = logging.StreamHandler(sys.stderr)
        lh_console.setLevel(log_level)
        lh_console.setFormatter(formatter)

        root_logger.addHandler(lh_console)

        if self.verbose < 3:
            paramiko_logger = logging.getLogger('paramiko.transport')
            if self.verbose < 1:
                paramiko_logger.setLevel(logging.WARNING)
            else:
                paramiko_logger.setLevel(logging.INFO)

        return

    # -------------------------------------------------------------------------
    def init_file_logging(self):

        logfile = self.config.logfile
        logdir = logfile.parent

        if self.verbose > 1:
            LOG.debug(_(
                "Checking existence and accessibility of log directory {!r} ...").format(
                str(logdir)))

        if not logdir.exists():
            raise WorkDirNotExistsError(logdir)

        if not logdir.is_dir():
            raise WorkDirNotDirError(logdir)

        if not os.access(str(logdir), os.R_OK):
            raise WorkDirAccessError(logdir, _("No read access"))

        if not os.access(str(logdir), os.W_OK):
            raise WorkDirAccessError(logdir, _("No write access"))

        root_log = logging.getLogger()
        formatter = self._get_log_formatter(is_term=False)

        lh_file = logging.FileHandler(str(logfile), mode='a', encoding='utf-8', delay=True)
        if self.verbose:
            lh_file.setLevel(logging.DEBUG)
        else:
            lh_file.setLevel(logging.INFO)
        lh_file.setFormatter(formatter)
        root_log.addHandler(lh_file)

    # -------------------------------------------------------------------------
    def post_init(self):
        """
        Method to execute before calling run(). Here could be done some
        finishing actions after reading in commandline parameters,
        configuration a.s.o.
        """

        super(UpdateDdnsApplication, self).post_init()
        self.initialized = False

        try:
            self.init_file_logging()
            self.verify_working_dir()
        except WorkDirError as e:
            LOG.error(str(e))
            self.exit(3)

        self.initialized = True

    # -------------------------------------------------------------------------
    def _run(self):

        LOG.info(_("Starting {a!r}, version {v!r} ...").format(
            a=self.appname, v=self.version))

        time.sleep(2)

        LOG.info(_("Ending {a!r}.").format(
            a=self.appname, v=self.version))



# =============================================================================
if __name__ == "__main__":

    pass

# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 list
