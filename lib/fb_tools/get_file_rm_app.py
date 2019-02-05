#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: Frank Brehm
@contact: frank.brehm@pixelpark.com
@copyright: © 2019 by Frank Brehm, Berlin
@summary: The module for the get-file-to-remove application object.
"""
from __future__ import absolute_import

# Standard modules
import logging
import datetime
import argparse
import pathlib
import glob
import re
import sre_constants

# Third party modules

# Own modules
from .xlate import XLATOR

from .errors import FbAppError

from .common import pp, get_monday

from .app import BaseApplication

__version__ = '1.1.3'
LOG = logging.getLogger(__name__)

_ = XLATOR.gettext


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
            msg = _("Value must be at least {m} - {v} was given.").format(
                m=self._min, v=values)
            raise argparse.ArgumentError(self, msg)

        setattr(namespace, self.dest, values)


# =============================================================================
def check_date_pattern(pattern):
    """Function to check, whether the given pattern is a valid pattern for
        files with an timestamp in it."""

    if not pattern:
        return False

    pat = str(pattern).strip()
    if not pattern:
        return False

    if pat.count('%Y') != 1:
        return False

    if pat.count('%m') != 1:
        return False

    if pat.count('%d') != 1:
        return False

    return True


# =============================================================================
class WrongDatePattern(GetFileRmError):

    # -------------------------------------------------------------------------
    def __init__(self, pattern, add_info=None):
        self.pattern = pattern
        self.add_info = add_info

    # -------------------------------------------------------------------------
    def __str__(self):

        msg = _("The given pattern {!r} is not a valid date pattern").format(self.pattern)
        if self.add_info:
            msg += ': ' + self.add_info
        else:
            msg += _(". The must be exactly one occurence of '%Y', one of '%m' and one of '%d'.")
        return msg


# =============================================================================
class GetFileRmApplication(BaseApplication):
    """Class for the get-file-to-remove application object."""

    default_keep_days = 6
    default_keep_weeks = 3
    default_keep_months = 3
    default_keep_years = 3
    default_keep_last = 1

    min_keep_days = 1
    min_keep_weeks = 1
    min_keep_months = 1
    min_keep_years = 0
    min_keep_last = 1

    default_date_pattern = r'%Y[-_]?%m[-_]?%d'

    # -------------------------------------------------------------------------
    def __init__(
            self, verbose=0, version=__version__, *arg, **kwargs):
        """
        Initialisation of the get-file-to-remove application object.
        """

        desc = _(
            "Returns a newline separated list of files generated from file globbing patterns "
            "given as arguments to this application, where all files are omitted, which "
            "should not be removed.")

        self._keep_days = self.default_keep_days
        self._keep_weeks = self.default_keep_weeks
        self._keep_months = self.default_keep_months
        self._keep_years = self.default_keep_years
        self._keep_last = self.default_keep_last

        self._date_pattern = self.default_date_pattern
        self._pattern = None
        self.re_date = None

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
            msg = _("Wrong value {v!r} for {n}, must be >= {m}").format(
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
            msg = _("Wrong value {v!r} for {n}, must be >= {m}").format(
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
            msg = _("Wrong value {v!r} for {n}, must be >= {m}").format(
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
            msg = _("Wrong value {v!r} for {n}, must be >= {m}").format(
                v=value, n='keep_years', m=self.min_keep_years)
            raise ValueError(msg)

    # -----------------------------------------------------------
    @property
    def keep_last(self):
        """The number of last files to keep."""
        return self._keep_last

    @keep_last.setter
    def keep_last(self, value):
        v = int(value)
        if v >= self.min_keep_last:
            self._keep_last = v
        else:
            msg = _("Wrong value {v!r} for {n}, must be >= {m}").format(
                v=value, n='keep_last', m=self.min_keep_last)
            raise ValueError(msg)

    # -----------------------------------------------------------
    @property
    def date_pattern(self):
        """The pattern to extract the date from filename before transition to
            a regular expression pattern."""
        return self._date_pattern

    # -----------------------------------------------------------
    @property
    def pattern(self):
        """The translated pattern to extract the date from filename."""
        return self._pattern

    # -------------------------------------------------------------------------
    def init_arg_parser(self):
        """
        Method to initiate the argument parser.
        """

        super(GetFileRmApplication, self).init_arg_parser()

        keep_group = self.arg_parser.add_argument_group(_('Keep options'))

        keep_group.add_argument(
            '-L', '--last', metavar=_('NR_FILES'), dest='last', type=int,
            action=KeepOptionAction, min_val=self.min_keep_last,
            help=_(
                "How many of the last files should be kept "
                "(default: {default}, minimum: {min})?").format(
                default=self.default_keep_last, min=self.min_keep_last),
        )

        keep_group.add_argument(
            '-D', '--days', metavar=_('DAYS'), dest='days', type=int,
            action=KeepOptionAction, min_val=self.min_keep_days,
            help=_(
                "How many files one per day from today on should be kept "
                "(default: {default}, minimum: {min})?").format(
                default=self.default_keep_days, min=self.min_keep_days),
        )

        keep_group.add_argument(
            '-W', '--weeks', metavar=_('WEEKS'), dest='weeks', type=int,
            action=KeepOptionAction, min_val=self.min_keep_weeks,
            help=_(
                "How many files one per week from today on should be kept "
                "(default: {default}, minimum: {min})?").format(
                default=self.default_keep_weeks, min=self.min_keep_weeks),
        )

        keep_group.add_argument(
            '-M', '--months', metavar=_('MONTHS'), dest='months', type=int,
            action=KeepOptionAction, min_val=self.min_keep_months,
            help=_(
                "How many files one per month from today on should be kept "
                "(default: {default}, minimum: {min})?").format(
                default=self.default_keep_months, min=self.min_keep_months),
        )

        keep_group.add_argument(
            '-Y', '--years', metavar=_('YEARS'), dest='years', type=int,
            action=KeepOptionAction, min_val=self.min_keep_years,
            help=_(
                "How many files one per year from today on should be kept "
                "(default: {default}, minimum: {min})?").format(
                default=self.default_keep_years, min=self.min_keep_years),
        )

        self.arg_parser.add_argument(
            'files', metavar=_('FILE'), type=str, nargs='+',
            help=_('File pattern to generate list of files to remove.'),
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

        if self.args.last is not None:
            self.keep_last = self.args.last

    # -------------------------------------------------------------------------
    def _xlate_date_pattern(self):

        pat = self.date_pattern.strip()
        if not check_date_pattern(pat):
            raise WrongDatePattern(self.date_pattern)
        if self.verbose > 1:
            LOG.debug("Resolving date pattern {!r}.".format(pat))

        self._pattern = pat.replace(
            '%Y', r'(?P<year>\d{4})').replace(
            '%m', r'(?P<month>\d\d?)').replace(
            '%d', r'(?P<day>\d\d?)')

        try:
            self.re_date = re.compile(self.pattern)
        except sre_constants.error as e:
            raise WrongDatePattern(self.date_pattern, str(e))

    # -------------------------------------------------------------------------
    def post_init(self):
        """
        Method to execute before calling run().
        """

        super(GetFileRmApplication, self).post_init()
        self.initialized = False

        self._xlate_date_pattern()

        if self.verbose > 1:
            LOG.debug("Checking given files...")

        for fname in self.args.files:

            if self.verbose > 2:
                LOG.debug("Checking given file {!r} ...".format(fname))

            given_paths = []
            single_fpath = pathlib.Path(fname)
            if single_fpath.exists():
                given_paths = [single_fpath]
            else:
                given_paths = glob.glob(fname)
                if self.verbose > 2:
                    LOG.debug("Resolved paths:\n{}".format(pp(given_paths)))
                if not given_paths:
                    LOG.info(_("File pattern {!r} does not match any files.").format(fname))
                    continue
            for f_name in given_paths:
                fpath = pathlib.Path(f_name)
                if self.verbose > 2:
                    LOG.debug("Checking {!r} ...".format(fpath))
                if not fpath.exists():
                    LOG.warning(_("File {!r} does not exists.").format(str(fpath)))
                    continue
                if not fpath.is_file():
                    LOG.warning(_("File {!r} is not a regular file.").format(str(fpath)))
                    continue

                match = self.re_date.search(str(fpath))
                if not match:
                    LOG.warning(_("File {fi!r} does not match pattern {pa!r}.").format(
                        fi=str(fpath), pa=self.date_pattern))
                    continue

                year = int(match.group('year'))
                month = int(match.group('month'))
                day = int(match.group('day'))
                try:
                    fdate = datetime.date(year, month, day)                         # noqa
                except ValueError as e:
                    msg = _("Date in file {fi!r} is not a valid date: {e}.").format(
                        fi=str(fpath), e=e)
                    LOG.warning(msg)
                    continue

                fpath_abs = fpath.resolve()
                if fpath_abs not in self.files_given:
                    self.files_given.append(fpath_abs)

        self.initialized = True

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
        res['default_keep_last'] = self.default_keep_last

        res['min_keep_days'] = self.min_keep_days
        res['min_keep_weeks'] = self.min_keep_weeks
        res['min_keep_months'] = self.min_keep_months
        res['min_keep_years'] = self.min_keep_years
        res['min_keep_last'] = self.min_keep_last

        res['keep_days'] = self.keep_days
        res['keep_weeks'] = self.keep_weeks
        res['keep_months'] = self.keep_months
        res['keep_years'] = self.keep_years
        res['keep_last'] = self.keep_last

        res['date_pattern'] = self.date_pattern
        res['pattern'] = self.pattern

        return res

    # -------------------------------------------------------------------------
    def pre_run(self):

        if not self.files_given:
            msg = _("Did not found any files to evaluate.")
            LOG.info(msg)
            self.exit(0)

    # -------------------------------------------------------------------------
    def _run(self):
        """The underlaying startpoint of the application."""

        files_assigned = self.get_date_from_filenames()
        files_to_keep = self.get_files_to_keep(files_assigned)

        for fpath in sorted(self.files_given):
            if fpath not in files_to_keep:
                print(str(fpath))

    # -------------------------------------------------------------------------
    def get_files_to_keep(self, files_assigned):

        files_to_keep = []
        for f in self.get_files_to_keep_year(files_assigned['year']):
            if f not in files_to_keep:
                files_to_keep.append(f)
        for f in self.get_files_to_keep_month(files_assigned['month']):
            if f not in files_to_keep:
                files_to_keep.append(f)
        for f in self.get_files_to_keep_week(files_assigned['week']):
            if f not in files_to_keep:
                files_to_keep.append(f)
        for f in self.get_files_to_keep_day(files_assigned['day']):
            if f not in files_to_keep:
                files_to_keep.append(f)

        if self.keep_last:
            LOG.debug("Keeping last {} files ...".format(self.keep_last))
            files = sorted(self.files_given)
            index = self.keep_last * -1
            for f in files[index:]:
                if self.verbose > 1:
                    LOG.debug("Keep last file {!r}.".format(str(f)))
                if f not in files_to_keep:
                    files_to_keep.append(f)

        if self.verbose > 2:
            LOG.debug("Files to keep:\n{}".format(pp(files_to_keep)))
        return files_to_keep

    # -------------------------------------------------------------------------
    def get_files_to_keep_year(self, files_assigned):

        files_to_keep = []

        this_year = datetime.date.today().year
        last_year = this_year - self.keep_years

        for year_str in files_assigned.keys():
            year = int(year_str)
            if year <= last_year:
                continue

            files = sorted(files_assigned[year_str])
            if len(files) > 0:
                files_to_keep.append(files[0])

        if self.verbose > 2:
            LOG.debug("Files to keep for year:\n{}".format(pp(files_to_keep)))

        return files_to_keep

    # -------------------------------------------------------------------------
    def get_files_to_keep_month(self, files_assigned):

        files_to_keep = []
        i = 0

        today = datetime.date.today()
        y = today.year
        m = today.month
        last_month = today
        while i < self.keep_months:
            m = today.month - i
            y = today.year
            while m <= 0:
                y -= 1
                m += 12
            last_month = datetime.date(y, m, 1)
            i += 1
        LOG.debug("Got last month: {!r}".format(last_month.strftime('%Y-%m')))

        re_date = re.compile(r'(\d+)-(\d+)')
        for month_str in files_assigned.keys():
            match = re_date.match(month_str)
            this_month = datetime.date(
                int(match.group(1)), int(match.group(2)), 1)
            if this_month < last_month:
                continue
            files = sorted(files_assigned[month_str])
            if len(files) > 0:
                files_to_keep.append(files[0])

        if self.verbose > 2:
            LOG.debug("Files to keep for month:\n{}".format(pp(files_to_keep)))

        return files_to_keep

    # -------------------------------------------------------------------------
    def get_files_to_keep_week(self, files_assigned):

        files_to_keep = []

        today = datetime.date.today()
        this_monday = get_monday(today)
        tdelta = datetime.timedelta((self.keep_weeks - 1) * 7)
        last_monday = this_monday - tdelta

        LOG.debug("Got last monday: {!r}".format(last_monday.strftime('%Y-%m-%d')))

        re_date = re.compile(r'(\d+)-(\d+)-(\d+)')
        for day_str in files_assigned.keys():
            match = re_date.match(day_str)
            this_day = datetime.date(
                int(match.group(1)), int(match.group(2)), int(match.group(3)))
            if this_day < last_monday:
                continue
            files = sorted(files_assigned[day_str])
            files_to_keep.append(files[0])

        if self.verbose > 2:
            LOG.debug("Files to keep for week:\n{}".format(pp(files_to_keep)))

        return files_to_keep

    # -------------------------------------------------------------------------
    def get_files_to_keep_day(self, files_assigned):

        files_to_keep = []

        today = datetime.date.today()
        tdelta = datetime.timedelta(self.keep_days - 1)
        last_day = today - tdelta

        LOG.debug("Got last day: {!r}".format(last_day.strftime('%Y-%m-%d')))

        re_date = re.compile(r'(\d+)-(\d+)-(\d+)')
        for day_str in files_assigned.keys():
            match = re_date.match(day_str)
            this_day = datetime.date(
                int(match.group(1)), int(match.group(2)), int(match.group(3)))
            if this_day < last_day:
                continue
            files = sorted(files_assigned[day_str])
            if this_day == today:
                LOG.debug("Keeping all files from today.")
                for f in files:
                    files_to_keep.append(f)
            elif len(files) > 0:
                files_to_keep.append(files[0])

        if self.verbose > 2:
            LOG.debug("Files to keep for day:\n{}".format(pp(files_to_keep)))

        return files_to_keep

    # -------------------------------------------------------------------------
    def get_date_from_filenames(self):

        files = {}
        files['year'] = {}
        files['month'] = {}
        files['week'] = {}
        files['day'] = {}

        for fpath in self.files_given:

            fname = str(fpath)
            if self.verbose > 2:
                LOG.debug("Trying to get dat of file {!r}.".format(fname))

            match = self.re_date.search(fname)
            if not match:
                continue

            year = int(match.group('year'))
            month = int(match.group('month'))
            day = int(match.group('day'))
            fdate = datetime.date(year, month, day)
            if self.verbose > 2:
                LOG.debug("Got date {!r}.".format(fdate.isoformat()))

            y = fdate.strftime('%Y')
            if y not in files['year']:
                files['year'][y] = []
            if fpath not in files['year'][y]:
                files['year'][y].append(fpath)

            m = fdate.strftime('%Y-%m')
            if m not in files['month']:
                files['month'][m] = []
            if fpath not in files['month'][m]:
                files['month'][m].append(fpath)

            monday = get_monday(fdate)
            monday_s = monday.strftime('%Y-%m-%d')
            if monday_s not in files['week']:
                files['week'][monday_s] = []
            if fpath not in files['week'][monday_s]:
                files['week'][monday_s].append(fpath)

            this_day = fdate.strftime('%Y-%m-%d')
            if this_day not in files['day']:
                files['day'][this_day] = []
            if fpath not in files['day'][this_day]:
                files['day'][this_day].append(fpath)

        if self.verbose > 1:
            LOG.debug("Explored and assigned files:\n{}".format(pp(files)))
        return files


# =============================================================================
if __name__ == "__main__":

    pass

# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
