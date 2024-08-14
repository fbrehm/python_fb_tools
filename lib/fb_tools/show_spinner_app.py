#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@summary: The module for the show-spinner application class.

@author: Frank Brehm
@contact: frank.brehm@pixelpark.com
@copyright: © 2024 by Frank Brehm, Berlin
"""
from __future__ import absolute_import

# Standard modules
# import argparse
# import datetime
# import glob
import logging
# import re
import sys

# Third party modules

# Own modules
from . import __version__ as __global_version__
from .app import BaseApplication
# from .common import pp
# from .errors import FbAppError
from .spinner import CycleList
# from .spinner import Spinner
from .xlate import XLATOR

__version__ = '0.1.0'
LOG = logging.getLogger(__name__)

_ = XLATOR.gettext
ngettext = XLATOR.ngettext

# =============================================================================
class ShowSpinnerApplication(BaseApplication):
    """Class for the show-spinner application object."""

    default_show_time = 6
    min_show_time = 1.0
    default_spinner = 'random'

    # -------------------------------------------------------------------------
    def __init__(
            self, verbose=0, version=__global_version__, *arg, **kwargs):
        """Initialise of the show-spinnerapplication object."""
        desc = _(
            'Shows one or more spinners and their names for demonstration purposes. '
            'iIf no spinner is given, a random spinner will be displayed.')

        self._show_time = self.default_show_time

        self.spinners = []
        self.all_spinners = list(CycleList.keys()).sort()

        super(ShowSpinnerApplication, self).__init__(
            description=desc,
            verbose=verbose,
            version=version,
            *arg, **kwargs
        )

        self.initialized = True

    # -----------------------------------------------------------
    @property
    def show_time(self):
        """Give the number of seconds for displaying each spinner."""
        return self._show_time

    @show_time.setter
    def show_time(self, value):
        if value is None:
            self._show_time = self.default_show_time
            return

        v = float(value)
        if v < self.min_show_time:
            msg = _(
                'Wrong time for showing the spinners {v!r} given, it must be '
                'at least {m} seconds.').format(v=value, m=self.min_show_time)
            raise ValueError(msg)

        self._show_time = v

    # -------------------------------------------------------------------------
    def as_dict(self, short=True):
        """
        Transform the elements of the object into a dict.

        @param short: don't include local properties in resulting dict.
        @type short: bool

        @return: structure as dict
        @rtype:  dict
        """
        res = super(ShowSpinnerApplication, self).as_dict(short=short)

        res['show_time'] = self.show_time

        return res

    # -------------------------------------------------------------------------
    def init_arg_parser(self):
        """Initialise the argument parser."""
        super(ShowSpinnerApplication, self).init_arg_parser()

        all_spinners = ['random', 'all', 'list']
        all_spinners += self.all_spinners

        app_group = self.arg_parser.add_argument_group(_('Options for {}').format(self.appname))

        app_group.add_argument(
            '-t', '--time', dest='time', metavar=_('SECONDS'), type=float,
            help=_(
                'The time in seconds for displaying each spinner. Default: {} seconds.').format(
                self.default_show_time),
        )

        app_group.add_argument(
            'spinners', metavar=_('SPINNER'), type=str, nargs='*', choices=all_spinners,
            dest='spinners', help=_(
                'The spinners, which should be displayed. If not given, a random spinner will be '
                'displayed, which is the same as giving {rand!r} as the name of the spinner. '
                'If giving {list!r}, a simple list of all available spinners will be shown, '
                'without displaying them. If giving {all!r}, all available spinners will be '
                'shown.').format(rand='random', list='list', all='all'),
        )

    # -------------------------------------------------------------------------
    def perform_arg_parser(self):
        """Parse the command line options."""
        if self.args.time is not None:
            try:
                self.show_time = self.args.time
            except (ValueError, TypeError) as e:
                LOG.error(str(e))
                self.arg_parser.print_usage(sys.stdout)
                self.exit(1)
        if self.args.spinners:
            for spinner in self.args.spinners:
                if spinner == 'all' and len(self.spinners):
                    msg = _('You may give {!r} only as the only spinner.').format('all')
                    LOG.error(msg)
                    self.arg_parser.print_usage(sys.stdout)
                    self.exit(1)
                if spinner == 'list' and len(self.spinners):
                    msg = _('You may give {!r} only as the only spinner.').format('list')
                    LOG.error(msg)
                    self.arg_parser.print_usage(sys.stdout)
                    self.exit(1)
                self.spinners.append(spinner)
        else:
            self.spinners.append(self.default_spinner)


# =============================================================================
if __name__ == '__main__':

    pass

# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
