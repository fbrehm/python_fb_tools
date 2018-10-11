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

__version__ = '0.2.0'
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

    default_keep_days = 6
    default_keep_weeks = 3
    default_keep_months = 3
    default_keep_years = 3

    min_keep_days = 1
    min_keep_weeks = 1
    min_keep_months = 1
    min_keep_years = 0

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

        self._keep_days = self.default_keep_days
        self._keep_weeks = self.default_keep_weeks
        self._keep_months = self.default_keep_months
        self._keep_years = self.default_keep_years

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
    def keep_days(self):
        """The number of last days to keep a file."""
        return self._keep_days

    @keep_days.setter
    def keep_days(self, value):
        v = int(value)
        if v >= self.min_keep_days:
            self._keep_days = v
        else:
            msg = "Wrong value {v!r} for {n}, must be >= {m}".format(
                v=value, n='keep_days', m=self.min_keep_days)
            raise ValueError(msg)

    # -----------------------------------------------------------
    @property
    def keep_weeks(self):
        """The number of last weeks to keep a file."""
        return self._keep_weeks

    @keep_weeks.setter
    def keep_weeks(self, value):
        v = int(value)
        if v >= self.min_keep_weeks:
            self._keep_weeks = v
        else:
            msg = "Wrong value {v!r} for {n}, must be >= {m}".format(
                v=value, n='keep_weeks', m=self.min_keep_weeks)
            raise ValueError(msg)

    # -----------------------------------------------------------
    @property
    def keep_months(self):
        """The number of last months to keep a file."""
        return self._keep_months

    @keep_months.setter
    def keep_months(self, value):
        v = int(value)
        if v >= self.min_keep_months:
            self._keep_months = v
        else:
            msg = "Wrong value {v!r} for {n}, must be >= {m}".format(
                v=value, n='keep_months', m=self.min_keep_months)
            raise ValueError(msg)

    # -----------------------------------------------------------
    @property
    def keep_years(self):
        """The number of last years to keep a file."""
        return self._keep_years

    @keep_years.setter
    def keep_years(self, value):
        v = int(value)
        if v >= self.min_keep_years:
            self._keep_years = v
        else:
            msg = "Wrong value {v!r} for {n}, must be >= {m}".format(
                v=value, n='keep_years', m=self.min_keep_years)
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
            '-D', '--days', metavar='DAYS', dest='days', type=int,
            action=KeepOptionAction, min_val=self.min_keep_days,
            help=(
                "How many files one per day from today on should be kept "
                "(default: {default}, minimum: {min})?").format(
                default=self.default_keep_days, min=self.min_keep_days),
        )

        keep_group.add_argument(
            '-W', '--weeks', metavar='WEEKS', dest='weeks', type=int,
            action=KeepOptionAction, min_val=self.min_keep_weeks,
            help=(
                "How many files one per week from today on should be kept "
                "(default: {default}, minimum: {min})?").format(
                default=self.default_keep_weeks, min=self.min_keep_weeks),
        )

        keep_group.add_argument(
            '-M', '--months', metavar='MONTHS', dest='months', type=int,
            action=KeepOptionAction, min_val=self.min_keep_months,
            help=(
                "How many files one per month from today on should be kept "
                "(default: {default}, minimum: {min})?").format(
                default=self.default_keep_months, min=self.min_keep_months),
        )

        keep_group.add_argument(
            '-Y', '--years', metavar='YEARS', dest='years', type=int,
            action=KeepOptionAction, min_val=self.min_keep_years,
            help=(
                "How many files one per year from today on should be kept "
                "(default: {default}, minimum: {min})?").format(
                default=self.default_keep_years, min=self.min_keep_years),
        )

        self.arg_parser.add_argument(
            'files', metavar='FILE', type=str, nargs='+',
            help='File pattern to generate list of files to remove.',
        )

    # -------------------------------------------------------------------------
    def perform_arg_parser(self):

        if self.args.days is not None:
            self.keep_days = self.args.days

        if self.args.weeks is not None:
            self.keep_weeks = self.args.weeks

        if self.args.months is not None:
            self.keep_months = self.args.months

        if self.args.years is not None:
            self.keep_years = self.args.years

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

        res['default_keep_days'] = self.default_keep_days
        res['default_keep_weeks'] = self.default_keep_weeks
        res['default_keep_months'] = self.default_keep_months
        res['default_keep_years'] = self.default_keep_years

        res['min_keep_days'] = self.min_keep_days
        res['min_keep_weeks'] = self.min_keep_weeks
        res['min_keep_months'] = self.min_keep_months
        res['min_keep_years'] = self.min_keep_years

        res['keep_days'] = self.keep_days
        res['keep_weeks'] = self.keep_weeks
        res['keep_months'] = self.keep_months
        res['keep_years'] = self.keep_years

        #res['config'] = None
        #if self.config:
        #    res['config'] = self.config.as_dict(short=short, show_secrets=self.force)

        return res

# =============================================================================

if __name__ == "__main__":

    pass

# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4

