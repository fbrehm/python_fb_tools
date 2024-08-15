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
import copy
import logging
import random
import signal
import sys
import time

# Third party modules

# Own modules
from . import __version__ as __global_version__
from .app import BaseApplication
from .app import SIGNAL_NAMES
from .spinner import CycleList
from .spinner import Spinner
from .xlate import XLATOR

__version__ = '0.2.0'
LOG = logging.getLogger(__name__)

_ = XLATOR.gettext
ngettext = XLATOR.ngettext

# =============================================================================
class ShowSpinnerApplication(BaseApplication):
    """Class for the show-spinner application object."""

    default_show_time = 6
    default_spinner = 'random'
    default_prompt = _('Waiting ... ')

    # -------------------------------------------------------------------------
    def __init__(
            self, verbose=0, version=__global_version__, *arg, **kwargs):
        """Initialise of the show-spinnerapplication object."""
        desc = _(
            'Shows one or more spinners, and their names, if multiple spinners should be shown. '
            'If no spinner is given, a random spinner will be displayed.')

        self._show_time = None
        self._prompt = self.default_prompt

        self.spinners = []
        self.all_spinners = sorted(CycleList.keys(), key=str.lower)

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
            self._show_time = None
            return

        v = float(value)
        if v < 0:
            msg = _(
                'A negative time for showing the spinner {v!r} is not allowed.').format(
                value)
            raise ValueError(msg)

        if v == 0:
            self._show_time = None
        else:
            self._show_time = v

    # -----------------------------------------------------------
    @property
    def prompt(self):
        """Give the prompt displayed before the spinner."""
        return self._prompt

    @prompt.setter
    def prompt(self, value):
        if value is None:
            self._prompt = ''
            return

        self._prompt = str(value)

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

        res['prompt'] = self.prompt
        res['show_time'] = self.show_time

        return res

    # -------------------------------------------------------------------------
    def init_arg_parser(self):
        """Initialise the argument parser."""
        super(ShowSpinnerApplication, self).init_arg_parser()

        app_group = self.arg_parser.add_argument_group(_('Options for {}').format(self.appname))

        app_group.add_argument(
            '-P', '--prompt', dest='prompt',
            help=_(
                'The prompt displayed before the spinner, if only one spinner should be shown. '
                'Default: {!r}.').format(self.default_prompt),
        )

        app_group.add_argument(
            '-t', '--time', dest='time', metavar=_('SECONDS'), type=float,
            help=_(
                'The time in seconds for displaying each spinner.').format(
                self.default_show_time),
        )

        app_group.add_argument(
            'spinnerei', metavar=_('SPINNER'), type=str, nargs='*',
            help=_(
                'The spinners, which should be displayed. If not given, a random spinner will be '
                'displayed, which is the same as giving {rand!r} as the name of the spinner. '
                'If giving {list!r}, a simple list of all available spinners will be shown, '
                'without displaying them. If giving {all!r}, all available spinners will be '
                'shown.').format(rand='random', list='list', all='all'),
        )

    # -------------------------------------------------------------------------
    def perform_arg_parser(self):
        """Parse the command line options."""
        if self.args.prompt is not None:
            self.prompt = self.args.prompt

        if self.args.time is not None:
            try:
                self.show_time = self.args.time
            except (ValueError, TypeError) as e:
                LOG.error(str(e))
                self.arg_parser.print_usage(sys.stdout)
                self.exit(1)

        all_spinners = ['random'] + self.all_spinners

        if self.args.spinnerei:
            for spinner in self.args.spinnerei:
                if spinner == 'all':
                    if len(self.spinners):
                        msg = _('You may give {!r} only as the only spinner.').format('all')
                        LOG.error(msg)
                        self.arg_parser.print_usage(sys.stdout)
                        self.exit(1)
                    self.spinners.append(spinner)
                    if not self.show_time:
                        self.show_time = self.default_show_time
                    continue

                if spinner == 'list':
                    if len(self.spinners):
                        msg = _('You may give {!r} only as the only spinner.').format('list')
                        LOG.error(msg)
                        self.arg_parser.print_usage(sys.stdout)
                        self.exit(1)
                    self.spinners.append(spinner)
                    continue

                if spinner not in all_spinners:
                    msg = _('Invalid spinner {!r} given.').format(spinner)
                    LOG.error(msg)
                    self.arg_parser.print_usage(sys.stdout)
                    self.exit(1)

                self.spinners.append(spinner)
        else:
            self.spinners.append(self.default_spinner)

    # -------------------------------------------------------------------------
    def _run(self):
        """Run the application."""
        prompt = self.prompt

        show_time = 1
        if self.show_time:
            show_time = self.show_time

        if 'list' in self.spinners:
            self.list_spinners()
            self.exit(0)

        if 'all' in self.spinners:
            self.spinners = copy.copy(self.all_spinners)

        if len(self.spinners) > 1 or ('random' in self.spinners and self.args.prompt is None):
            prompt = _('Spinner {!r}: ')

        # ---------------------
        def _signal_handler(signum, frame):

            signame = '{}'.format(signum)
            msg = _('Got a signal {}.').format(signum)
            if signum in SIGNAL_NAMES:
                signame = SIGNAL_NAMES[signum]
                msg = _('Got a signal {n!r} ({s}).').format(
                    n=signame, s=signum)
            LOG.debug(msg)

            if signum in (
                    signal.SIGHUP, signal.SIGINT, signal.SIGABRT,
                    signal.SIGTERM, signal.SIGKILL, signal.SIGQUIT):
                print()
                if self.verbose > 1:
                    LOG.info(_('Exit on signal {n!r} ({s}).').format(n=signame, s=signum))
                self.exit(0)

        # ------------------------
        old_handlers = {}

        if self.verbose > 2:
            LOG.debug(_('Tweaking signal handlers.'))
        for signum in (
                signal.SIGHUP, signal.SIGINT, signal.SIGABRT,
                signal.SIGTERM, signal.SIGQUIT):
            if self.verbose > 3:
                signame = SIGNAL_NAMES[signum]
                LOG.debug(_('Setting signal handler for {n!r} ({s}).').format(
                    n=signame, s=signum))
            old_handlers[signum] = signal.signal(signum, _signal_handler)

        try:
            for spinner_name in self.spinners:
                if spinner_name == 'random':
                    spinner_name = self._get_random_spinner_name()
                print(prompt.format(spinner_name), end='', flush=True)

                with Spinner('', spinner_name):
                    if self.show_time:
                        time.sleep(show_time)
                    else:
                        while True:
                            time.sleep(show_time)
                print()
        finally:
            if self.verbose > 2:
                LOG.debug(_('Restoring original signal handlers.'))
            for signum in old_handlers.keys():
                signal.signal(signum, old_handlers[signum])

        self.exit(0)

    # -------------------------------------------------------------------------
    def _get_random_spinner_name(self):

        randomizer = random.SystemRandom()
        return randomizer.choice(list(CycleList.keys()))

    # -------------------------------------------------------------------------
    def list_spinners(self):
        """Print out a list of all available spinners."""
        if self.verbose:
            title = _('All available spinners:')
            print(title)
            print('-' * len(title))

        for spinner_name in self.all_spinners:
            print(spinner_name)


# =============================================================================
if __name__ == '__main__':

    pass

# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
