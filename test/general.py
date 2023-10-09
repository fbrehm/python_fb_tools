#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@summary: General used functions an objects used for unit tests on the base python modules.

@author: Frank Brehm
@contact: frank@brehm-online.com
@copyright: © 2023 Frank Brehm, Berlin
@license: GPL3
"""

import argparse
import logging
import os
import sys

try:
    import unittest2 as unittest
except ImportError:
    import unittest

# Own modules
from fb_logging.colored import ColoredFormatter

# =============================================================================

LOG = logging.getLogger(__name__)


# =============================================================================
def get_arg_verbose():
    """Get and return command line arguments."""
    arg_parser = argparse.ArgumentParser()

    arg_parser.add_argument(
        '-v', '--verbose', action='count',
        dest='verbose', help='Increase the verbosity level')
    args = arg_parser.parse_args()

    return args.verbose


# =============================================================================
def init_root_logger(verbose=0):
    """Initialize the root logger."""
    root_log = logging.getLogger()
    root_log.setLevel(logging.WARNING)
    if verbose:
        root_log.setLevel(logging.INFO)
        if verbose > 1:
            root_log.setLevel(logging.DEBUG)

    appname = os.path.basename(sys.argv[0])
    format_str = appname + ': '
    if verbose:
        if verbose > 1:
            format_str += '%(name)s(%(lineno)d) %(funcName)s() '
        else:
            format_str += '%(name)s '
    format_str += '%(levelname)s - %(message)s'
    formatter = None
    formatter = ColoredFormatter(format_str)

    # create log handler for console output
    lh_console = logging.StreamHandler(sys.stderr)
    if verbose:
        lh_console.setLevel(logging.DEBUG)
    else:
        lh_console.setLevel(logging.INFO)
    lh_console.setFormatter(formatter)

    root_log.addHandler(lh_console)


# =============================================================================
class FbToolsTestcase(unittest.TestCase):
    """Base test case for all testcase classes of this package."""

    # -------------------------------------------------------------------------
    def __init__(self, methodName='runTest', verbose=0):
        """Initialize the base testcase class."""
        self._verbose = int(verbose)

        appname = os.path.basename(sys.argv[0]).replace('.py', '')
        self._appname = appname

        super(FbToolsTestcase, self).__init__(methodName)

    # -------------------------------------------------------------------------
    @property
    def verbose(self):
        """The verbosity level."""
        return getattr(self, '_verbose', 0)

    # -------------------------------------------------------------------------
    @property
    def appname(self):
        """The name of the current running application."""
        return self._appname

    # -------------------------------------------------------------------------
    def setUp(self):
        """Execute this on seting up before calling each particular test method."""
        pass

    # -------------------------------------------------------------------------
    def tearDown(self):
        """Tear down routine for calling each particular test method."""
        pass


# =============================================================================
if __name__ == '__main__':

    pass

# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
