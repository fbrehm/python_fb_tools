#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: Frank Brehm
@contact: frank.brehm@pixelpark.com
@copyright: © 2019 by Frank Brehm, Berlin
@summary: The module for the config-converter application object.
"""
from __future__ import absolute_import, print_function

# Standard modules
import logging
import argparse
import pathlib
import errno
import os

from pathlib import Path

# Third party modules

import babel

# Own modules
from . import __version__ as GLOBAL_VERSION

from .xlate import XLATOR, DEFAULT_LOCALE, format_list

from .common import pp

from .app import BaseApplication

from .errors import FbAppError

__version__ = '0.2.1'
LOG = logging.getLogger(__name__)

SUPPORTED_CFG_TYPES = ('json', 'hjson', 'yaml')

_ = XLATOR.gettext
ngettext = XLATOR.ngettext


# =============================================================================
class CfgConvertError(FbAppError):
    """Base exception class for all exceptions in this application."""
    pass


# =============================================================================
class WrongCfgTypeError(CfgConvertError, ValueError):
    """Special exception class for the case of wrong configuration type."""
    pass


# =============================================================================
class InputFileError(CfgConvertError, OSError):
    """Special exception class for the case of errors with the input file."""

    # -------------------------------------------------------------------------
    def __init__(self, err_no, strerror, filename):

        super(InputFileError, self).__init__(err_no, strerror, str(filename))


# =============================================================================
class InputFileNotExistingError(InputFileError):

    # -------------------------------------------------------------------------
    def __init__(self, filename):

        msg = _("The input file is not existing")
        super(InputFileNotExistingError, self).__init__(
            errno.ENOENT, msg, filename)


# =============================================================================
class InputFileNotReadableError(InputFileError):

    # -------------------------------------------------------------------------
    def __init__(self, filename):

        msg = _("The input file is not readable")
        super(InputFileNotReadableError, self).__init__(
            errno.EACCES, msg, filename)


# =============================================================================
class CfgTypeOptionAction(argparse.Action):

    # -------------------------------------------------------------------------
    def __init__(self, option_strings, *args, **kwargs):

        super(CfgTypeOptionAction, self).__init__(
            option_strings=option_strings, *args, **kwargs)

    # -------------------------------------------------------------------------
    def __call__(self, parser, namespace, cfg_type, option_string=None):

        if cfg_type is None:
            msg = _("The configuration file type may not be None.")
            raise argparse.ArgumentError(self, msg)

        cfg_type_clean = cfg_type.strip().lower()
        if cfg_type_clean not in SUPPORTED_CFG_TYPES:
            msg = _(
                "The configuration file type must be one of {l}, given {g!r}.").format(
                    l=format_list(SUPPORTED_CFG_TYPES, do_repr=True, locale=DEFAULT_LOCALE),
                    g=cfg_type)
            raise argparse.ArgumentError(self, msg)

        setattr(namespace, self.dest, cfg_type_clean)
        return


# =============================================================================
class InputFileOptionAction(argparse.Action):

    # -------------------------------------------------------------------------
    def __init__(self, option_strings, *args, **kwargs):

        super(InputFileOptionAction, self).__init__(
            option_strings=option_strings, *args, **kwargs)

    # -------------------------------------------------------------------------
    def __call__(self, parser, namespace, filename, option_string=None):

        if filename is None or filename == '-' or filename == '':
            setattr(namespace, self.dest, '-')
            return
        path = Path(filename)
        if not path.exists():
            err = InputFileNotExistingError(path)
            raise argparse.ArgumentError(self, str(err))
        if not os.access(str(path), os.R_OK):
            err = InputFileNotReadableError(path)
            raise argparse.ArgumentError(self, str(err))
        setattr(namespace, self.dest, path)


# =============================================================================
class OutputFileOptionAction(argparse.Action):

    # -------------------------------------------------------------------------
    def __init__(self, option_strings, *args, **kwargs):

        super(OutputFileOptionAction, self).__init__(
            option_strings=option_strings, *args, **kwargs)

    # -------------------------------------------------------------------------
    def __call__(self, parser, namespace, filename, option_string=None):

        if filename is None or filename == '-' or filename == '':
            setattr(namespace, self.dest, '-')
            return
        path = Path(filename)
        setattr(namespace, self.dest, path)


# =============================================================================
class CfgConvertApplication(BaseApplication):
    """
    Class for the application objects.
    """

    supported_cfg_types = SUPPORTED_CFG_TYPES

    # -------------------------------------------------------------------------
    def __init__(
        self, from_type=None, to_type=None,
            appname=None, verbose=0, version=GLOBAL_VERSION, base_dir=None,
            initialized=False, usage=None, description=None,
            argparse_epilog=None, argparse_prefix_chars='-', env_prefix=None):

        desc = description
        if not desc:
            desc = _(
                "Converts the given configuration file from the given input format "
                "into the given output format and print it out to {o} "
                "or into a given output file.").format(o='STDOUT')

        self.cfg_files = []
        self._from_type = None
        self._to_type = None
        self._input = '-'
        self._output = '-'

        self.from_type = from_type
        self.to_type = to_type

        super(CfgConvertApplication, self).__init__(
            appname=appname, verbose=verbose, version=version, base_dir=base_dir,
            description=desc, initialized=False,
        )

        self.initialized = True

    # -------------------------------------------------------------------------
    @property
    def from_type(self):
        """Type of configuration of source files."""
        return self._from_type

    @from_type.setter
    def from_type(self, value):
        if value is None:
            self._from_type = None
            return
        v = str(value).strip().lower()
        if v not in self.supported_cfg_types:
            msg = _("Invalid input configuration type {!r}").format(value)
            raise WrongCfgTypeError(msg)
        self._from_type = v

    # -------------------------------------------------------------------------
    @property
    def to_type(self):
        """Type of configuration of target files."""
        return self._to_type

    @to_type.setter
    def to_type(self, value):
        if value is None:
            self._to_type = None
            return
        v = str(value).strip().lower()
        if v not in self.supported_cfg_types:
            msg = _("Invalid target configuration type {!r}").format(value)
            raise WrongCfgTypeError(msg)
        self._to_type = v

    # -------------------------------------------------------------------------
    @property
    def input(self):
        """The file name of the input, the source configuration."""
        return self._input

    @input.setter
    def input(self, value):
        if value is None:
            self._input = '-'
            return
        path = value
        if not isinstance(value, Path):
            v = str(value).strip()
            if v == '':
                self._input = '-'
                return
            path = Path(v)

        if not path.exists():
            raise InputFileNotExistingError(path)
        if not os.access(str(path), os.R_OK):
            raise InputFileNotReadableError(path)
        self._input = path

    # -------------------------------------------------------------------------
    @property
    def output(self):
        """The file name of the output, the target configuration."""
        return self._output

    @output.setter
    def output(self, value):
        if value is None:
            self._output = '-'
            return
        path = value
        if not isinstance(value, Path):
            v = str(value).strip()
            if v == '':
                self._output = '-'
                return
            path = Path(v)

        self._output = path

    # -------------------------------------------------------------------------
    def as_dict(self, short=True):
        """
        Transforms the elements of the object into a dict

        @param short: don't include local properties in resulting dict.
        @type short: bool

        @return: structure as dict
        @rtype:  dict
        """

        res = super(CfgConvertApplication, self).as_dict(short=short)
        res['from_type'] = self.from_type
        res['to_type'] = self.to_type
        res['input'] = self.input
        res['output'] = self.output
        res['supported_cfg_types'] = self.supported_cfg_types

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

        self.initialized = True

    # -------------------------------------------------------------------------
    def init_arg_parser(self):
        """
        Public available method to initiate the argument parser.
        """

        super(CfgConvertApplication, self).init_arg_parser()

        file_group = self.arg_parser.add_argument_group(_('File options'))

        file_group.add_argument(
            '-i', '--input', metavar=_('FILE'), dest='input',
            action=InputFileOptionAction, help=_(
                "The filename of the input file. Use {i!r} to read from {f} "
                "(which is the default).").format(i='-', f='STDIN'),
        )

        file_group.add_argument(
            '-o', '--output', metavar=_('FILE'), dest='output',
            action=OutputFileOptionAction, help=_(
                "The filename of the output file. Use {i!r} to write to {f} "
                "(which is the default).").format(i='-', f='STDOUT'),
        )

        if not self.from_type or not self.to_type:

            conv_group = self.arg_parser.add_argument_group(_('Converting options'))
            type_list = format_list(
                SUPPORTED_CFG_TYPES, do_repr=True, style='or', locale=DEFAULT_LOCALE)

            if not self.from_type:
                conv_group.add_argument(
                    '-F', '--from-type', metavar=_('CFG_TYPE'), dest='from_type',
                    required=True, action=CfgTypeOptionAction,
                    help=_(
                        "The configuration type of the source, must be one "
                        "of {}.").format(type_list),
                )

            if not self.to_type:
                conv_group.add_argument(
                    '-T', '--to-type', metavar=_('CFG_TYPE'), dest='to_type',
                    required=True, action=CfgTypeOptionAction,
                    help=_(
                        "The configuration type of the target, must be one "
                        "of {}.").format(type_list),
                )

    # -------------------------------------------------------------------------
    def perform_arg_parser(self):
        """
        Public available method to execute some actions after parsing
        the command line parameters.
        """

        from_type = getattr(self.args, 'from_type', None)
        if from_type:
            self.from_type = from_type

        to_type = getattr(self.args, 'to_type', None)
        if to_type:
            self.to_type = to_type

        self.input = getattr(self.args, 'input', None)
        self.output = getattr(self.args, 'output', None)

    # -------------------------------------------------------------------------
    def _run(self):

        LOG.debug(_("Starting {a!r}, version {v!r} ...").format(
            a=self.appname, v=self.version))
        ret = 0

#        ret = 99
#        try:
#            ret = self.get_vms()
#        finally:
#            # Aufräumen ...
#            LOG.debug(_("Closing ..."))
#            self.vsphere.disconnect()
#            self.vsphere = None

        self.exit(ret)


# =============================================================================
if __name__ == "__main__":

    pass

# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 list
