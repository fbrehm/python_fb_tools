#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@summary: Test script (and module) for unit tests on any-config class.

@author: Frank Brehm
@contact: frank@brehm-online.com
@copyright: © 2026 Frank Brehm, Berlin
@license: GPL3
"""

import logging
import os
import stat
import sys
import tempfile
import textwrap
from pathlib import Path

try:
    import unittest2 as unittest
except ImportError:
    import unittest

libdir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, libdir)

from fb_tools.common import is_sequence
from fb_tools.common import pp
from fb_tools.common import to_str

from general import FbToolsTestcase, get_arg_verbose, init_root_logger

LOG = logging.getLogger("test_anycfg")


# =============================================================================
class TestFbAnyConfig(FbToolsTestcase):
    """Testcase for unit tests on fb_tools.any_config and class AnyConfigHandler."""

    # -------------------------------------------------------------------------
    def setUp(self):
        """Execute this on setting up before calling each particular test method."""
        if self.verbose >= 1:
            print()

        self.test_dir = Path(__file__).parent.resolve()
        self.base_dir = self.test_dir.parent
        self.test_cfg_dir = self.test_dir / "test-multiconfig"
        self._appname = "test_anycfg"

    # -------------------------------------------------------------------------
    def tearDown(self):
        """Tear down routine for calling each particular test method."""
        pass

    # -------------------------------------------------------------------------
    def test_import(self):
        """Test instantiating fb_tools.any_config."""
        LOG.info(self.get_method_doc())
        import fb_tools.any_config

        LOG.debug(
            "Version of fb_tools.any_config: {!r}.".format(fb_tools.any_config.__version__)
        )

        LOG.info("Testing import of AnyConfigHandler from fb_tools.any_config ...")
        from fb_tools.any_config import AnyConfigHandler

        LOG.debug("Description of AnyConfigHandler: " + textwrap.dedent(AnyConfigHandler.__doc__))

    # -------------------------------------------------------------------------
    def test_object(self):
        """Test init of a AnyConfigHandler object."""
        LOG.info(self.get_method_doc())

        from fb_tools.any_config import AnyConfigHandler

        cfg = AnyConfigHandler(
            appname=self.appname,
            verbose=self.verbose,
        )
        LOG.debug("AnyConfigHandler %%r: {!r}".format(cfg))
        LOG.debug("AnyConfigHandler %%s: {}".format(cfg))


# =============================================================================
if __name__ == "__main__":

    verbose = get_arg_verbose()
    if verbose is None:
        verbose = 0
    init_root_logger(verbose)

    LOG.info("Starting tests ...")

    suite = unittest.TestSuite()

    suite.addTest(TestFbAnyConfig("test_import", verbose))
    suite.addTest(TestFbAnyConfig("test_object", verbose))

    runner = unittest.TextTestRunner(verbosity=verbose)

    result = runner.run(suite)


# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
