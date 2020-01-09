#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
@author: Frank Brehm
@contact: frank@brehm-online.com
@copyright: © 2020 Frank Brehm, Berlin
@license: GPL3
@summary: test script (and module) for unit tests on multi config class
'''

import os
import sys
import logging
import tempfile
import datetime

from pathlib import Path

try:
    import unittest2 as unittest
except ImportError:
    import unittest

from babel.dates import LOCALTZ

libdir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'lib'))
sys.path.insert(0, libdir)

from general import FbToolsTestcase, get_arg_verbose, init_root_logger

from fb_tools.common import to_bool

LOG = logging.getLogger('test_multicfg')


# =============================================================================
class TestFbMultiConfig(FbToolsTestcase):

    # -------------------------------------------------------------------------
    def setUp(self):

        pass

    # -------------------------------------------------------------------------
    def tearDown(self):

        pass

    # -------------------------------------------------------------------------
    def test_import(self):

        LOG.info("Testing import of fb_tools.multi_config ...")
        import fb_tools.multi_config                                        # noqa

        LOG.info("Testing import of MultiConfigError from fb_tools.multi_config ...")
        from fb_tools.multi_config import MultiConfigError                  # noqa

        LOG.info("Testing import of BaseMultiConfig from fb_tools.multi_config ...")
        from fb_tools.multi_config import BaseMultiConfig                   # noqa

    # -------------------------------------------------------------------------
    def test_object(self):

        LOG.info("Testing init of a BaseMultiConfig object.")

        from fb_tools.multi_config import BaseMultiConfig

        cfg = BaseMultiConfig(
            appname='test_multicfg',
            verbose=1,
        )
        LOG.debug("BaseMultiConfig %%r: %r", cfg)
        LOG.debug("BaseMultiConfig %%s: %s", str(cfg))

# =============================================================================
if __name__ == '__main__':

    verbose = get_arg_verbose()
    if verbose is None:
        verbose = 0
    init_root_logger(verbose)

    LOG.info("Starting tests ...")

    suite = unittest.TestSuite()

    suite.addTest(TestFbMultiConfig('test_import', verbose))
    suite.addTest(TestFbMultiConfig('test_object', verbose))

    runner = unittest.TextTestRunner(verbosity=verbose)

    result = runner.run(suite)


# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
