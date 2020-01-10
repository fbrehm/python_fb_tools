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
            config_dir='test', additional_stems='test',
            verbose=self.verbose,
        )
        LOG.debug("BaseMultiConfig %%r: %r", cfg)
        LOG.debug("BaseMultiConfig %%s: %s", str(cfg))

    # -------------------------------------------------------------------------
    def test_init_cfg_dirs(self):

        LOG.info("Testing init of cofiguration directories.")

        from fb_tools.multi_config import BaseMultiConfig

        cfg = BaseMultiConfig(
            appname='test_multicfg',
            config_dir='test', additional_stems='test',
            verbose=self.verbose,
        )

        system_path = Path('/etc', 'test')
        LOG.debug("Testing existence of system config path {!r}.".format(system_path))
        self.assertIn(system_path, cfg.config_dirs)

        user_path = Path.home() / '.config' / 'test'
        LOG.debug("Testing existence of user config path {!r}.".format(user_path))
        self.assertIn(user_path, cfg.config_dirs)

        cwd_etc_dir = Path.cwd() / 'etc'
        LOG.debug("Testing existence of basedir config path {!r}.".format(cwd_etc_dir))
        self.assertIn(cwd_etc_dir, cfg.config_dirs)



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
    suite.addTest(TestFbMultiConfig('test_init_cfg_dirs', verbose))

    runner = unittest.TextTestRunner(verbosity=verbose)

    result = runner.run(suite)


# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
