#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: Frank Brehm
@contact: frank.brehm@pixelpark.com
@copyright: © 2018 by Frank Brehm, Berlin
@summary: The module for the get-file-to-remove application object.
"""
from __future__ import absolute_import

# Standard modules
import sys
import os
import logging
import textwrap
import datetime
import argparse

# Third party modules

# Own modules
from .errors import FbAppError, ExpectedHandlerError, CommandNotFoundError

from .app import BaseApplication

__version__ = '0.1.0'
LOG = logging.getLogger(__name__)


# =============================================================================
class GetFileRmError(FbAppError):
    """Base error class for all exceptions happened during
    execution this application"""

    pass


# =============================================================================
class KeepOptionAction(argparse.Action):

    # -------------------------------------------------------------------------
    def __init__(self, option_strings, min_val, *args, **kwargs):

        self._min = min_val

        super(KeepOptionAction, self).__init__(
            option_strings=option_strings, *args, **kwargs)

    # -------------------------------------------------------------------------
    def __call__(self, parser, namespace, values, option_string=None):

        if values < self._min:
            msg = "Value must be at least {m} - {v} was given.".format(
                m=self._min, v=values)
            raise argparse.ArgumentError(self, msg)

        setattr(namespace, self.dest, values)

# =============================================================================
class GetFileRmApplication(BaseApplication):
    """Class for the get-file-to-remove application object."""

    default_keep_daily = 6
    default_keep_weekly = 3
    default_keep_monthly = 3
    default_keep_yearly = 3

    min_keep_daily = 1
    min_keep_weekly = 1
    min_keep_monthly = 1
    min_keep_yearly = 0

    # -------------------------------------------------------------------------
    def __init__(
            self, verbose=0, version=__version__, *arg, **kwargs):
        """
        Initialisation of the get-file-to-remove application object.
        """

        indent = ' ' * self.usage_term_len

        desc = textwrap.dedent("""\
            Returns a newline separated list of files generated from file globbing patterns
            given as arguments to this application, where all files are omitted, which
            should not be removed.
            """).strip()

        self._keep_daily = self.default_keep_daily
        self._keep_weekly = self.default_keep_weekly
        self._keep_monthly = self.default_keep_monthly
        self._keep_yearly = self.default_keep_yearly

        self.files_given = []
        self.files = []

        super(GetFileRmApplication, self).__init__(
            description=desc,
            verbose=verbose,
            version=version,
            *arg, **kwargs
        )

        self.initialized = True

    # -----------------------------------------------------------
    @property
    def keep_daily(self):
        """The number of last days to keep a file."""
        return self._keep_daily

    @keep_daily.setter
    def keep_daily(self, value):
        v = int(value)
        if v >= self.min_keep_daily:
            self._keep_daily = v
        else:
            msg = "Wrong value {v!r} for {n}, must be >= {m}".format(
                v=value, n='keep_daily', m=self.min_keep_daily)
            raise ValueError(msg)

    # -----------------------------------------------------------
    @property
    def keep_weekly(self):
        """The number of last weeks to keep a file."""
        return self._keep_weekly

    @keep_weekly.setter
    def keep_weekly(self, value):
        v = int(value)
        if v >= self.min_keep_weekly:
            self._keep_weekly = v
        else:
            msg = "Wrong value {v!r} for {n}, must be >= {m}".format(
                v=value, n='keep_weekly', m=self.min_keep_weekly)
            raise ValueError(msg)

    # -----------------------------------------------------------
    @property
    def keep_monthly(self):
        """The number of last months to keep a file."""
        return self._keep_monthly

    @keep_monthly.setter
    def keep_monthly(self, value):
        v = int(value)
        if v >= self.min_keep_monthly:
            self._keep_monthly = v
        else:
            msg = "Wrong value {v!r} for {n}, must be >= {m}".format(
                v=value, n='keep_monthly', m=self.min_keep_monthly)
            raise ValueError(msg)

    # -----------------------------------------------------------
    @property
    def keep_yearly(self):
        """The number of last years to keep a file."""
        return self._keep_yearly

    @keep_yearly.setter
    def keep_yearly(self, value):
        v = int(value)
        if v >= self.min_keep_yearly:
            self._keep_yearly = v
        else:
            msg = "Wrong value {v!r} for {n}, must be >= {m}".format(
                v=value, n='keep_yearly', m=self.min_keep_yearly)
            raise ValueError(msg)

    # -------------------------------------------------------------------------
    def _run(self):
        """The underlaying startpoint of the application."""

        print("Working ...")

    # -------------------------------------------------------------------------
    def init_arg_parser(self):
        """
        Method to initiate the argument parser.
        """

        super(GetFileRmApplication, self).init_arg_parser()

        keep_group = self.arg_parser.add_argument_group('Keep options')

        keep_group.add_argument(
            '-D', '--daily', metavar='DAYS', dest='daily', type=int,
            action=KeepOptionAction, min_val=self.min_keep_daily,
            help=(
                "How many files one per day from today on should be kept "
                "(default: {default}, minimum: {min})?").format(
                default=self.default_keep_daily, min=self.min_keep_daily),
        )

        keep_group.add_argument(
            '-W', '--weekly', metavar='WEEKS', dest='weekly', type=int,
            action=KeepOptionAction, min_val=self.min_keep_weekly,
            help=(
                "How many files one per week from today on should be kept "
                "(default: {default}, minimum: {min})?").format(
                default=self.default_keep_weekly, min=self.min_keep_weekly),
        )

        keep_group.add_argument(
            '-M', '--monthly', metavar='MONTHS', dest='monthly', type=int,
            action=KeepOptionAction, min_val=self.min_keep_monthly,
            help=(
                "How many files one per month from today on should be kept "
                "(default: {default}, minimum: {min})?").format(
                default=self.default_keep_monthly, min=self.min_keep_monthly),
        )

        keep_group.add_argument(
            '-Y', '--yearly', metavar='YEARS', dest='yearly', type=int,
            action=KeepOptionAction, min_val=self.min_keep_yearly,
            help=(
                "How many files one per year from today on should be kept "
                "(default: {default}, minimum: {min})?").format(
                default=self.default_keep_yearly, min=self.min_keep_yearly),
        )

        self.arg_parser.add_argument(
            'files', metavar='FILE', type=str, nargs='+',
            help='File pattern to generate list of files to remove.',
        )

    # -------------------------------------------------------------------------
    def perform_arg_parser(self):

        if self.args.daily is not None:
            self.keep_daily = self.args.daily

        if self.args.weekly is not None:
            self.keep_weekly = self.args.weekly

        if self.args.monthly is not None:
            self.keep_monthly = self.args.monthly

        if self.args.yearly is not None:
            self.keep_yearly = self.args.yearly

    # -------------------------------------------------------------------------
    def as_dict(self, short=True):
        """
        Transforms the elements of the object into a dict

        @param short: don't include local properties in resulting dict.
        @type short: bool

        @return: structure as dict
        @rtype:  dict
        """

        res = super(GetFileRmApplication, self).as_dict(short=short)

        res['default_keep_daily'] = self.default_keep_daily
        res['default_keep_weekly'] = self.default_keep_weekly
        res['default_keep_monthly'] = self.default_keep_monthly
        res['default_keep_yearly'] = self.default_keep_yearly

        res['min_keep_daily'] = self.min_keep_daily
        res['min_keep_weekly'] = self.min_keep_weekly
        res['min_keep_monthly'] = self.min_keep_monthly
        res['min_keep_yearly'] = self.min_keep_yearly

        res['keep_daily'] = self.keep_daily
        res['keep_weekly'] = self.keep_weekly
        res['keep_monthly'] = self.keep_monthly
        res['keep_yearly'] = self.keep_yearly

        #res['config'] = None
        #if self.config:
        #    res['config'] = self.config.as_dict(short=short, show_secrets=self.force)

        return res

# =============================================================================

if __name__ == "__main__":

    pass

# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4

