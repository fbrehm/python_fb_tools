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

        LOG.debug("Version of fb_tools.any_config: {!r}.".format(fb_tools.any_config.__version__))

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

    # -------------------------------------------------------------------------
    def test_guess_config_type_by_name(self):
        """Test detecting config type by file extension."""
        LOG.info(self.get_method_doc())

        from fb_tools.any_config import AnyConfigHandler
        from fb_tools.errors import ConfigDetectionError

        terminal_has_colors = False
        if self.verbose:
            terminal_has_colors = True

        cfg_handler = AnyConfigHandler(
            appname=self.appname,
            verbose=self.verbose,
            terminal_has_colors=terminal_has_colors,
        )

        for fname in (None, "-", "", "bla.blub", 1, "bla.jsn", "bla.configuration"):
            LOG.debug("Testing raise ConfigDetectionError in filename {!r} ...".format(fname))
            with self.assertRaises(ConfigDetectionError) as cm:
                ftype = cfg_handler.guess_config_type_by_name(fname, raise_on_error=True)
                LOG.error("This should have not been visible for {!r} ...".format(fname))
            e = cm.exception
            LOG.debug("%s raised: %s", e.__class__.__name__, e)

        if self.verbose >= 1:
            print()

        test_data = (
            ("config.ini", "ini"),
            ("config.conf", "ini"),
            (Path("config.config"), "ini"),
            ("config.INI", "ini"),
            ("config.cfg", "ini"),
            ("config.js", "json"),
            ("config.json", "json"),
            ("config.hjs", "hjson"),
            ("config.Hjson", "hjson"),
            ("config.yml", "yaml"),
            ("config.yaml", "yaml"),
            ("config.toml", "toml"),
            ("config.tml", "toml"),
        )

        for test_pair in test_data:
            fname = test_pair[0]
            exp_type = test_pair[1]

            LOG.debug(f"Test config file {fname!r} for type {exp_type!r} ...")
            got_type = cfg_handler.guess_config_type_by_name(fname, raise_on_error=True)
            LOG.debug(f"Got config type {got_type!r} for config file {fname!r}.")

    # -------------------------------------------------------------------------
    def test_read_cfg_files(self):
        """Test reading of configuration files."""
        LOG.info(self.get_method_doc())

        from fb_tools.any_config import AnyConfigHandler

        terminal_has_colors = False
        if self.verbose:
            terminal_has_colors = True

        cfg_handler = AnyConfigHandler(
            appname=self.appname,
            verbose=self.verbose,
            terminal_has_colors=terminal_has_colors,
        )

        config_files = (
            "test_multicfg-additional.ini",
            "test_multicfg-additional.uhu",
            "test_multicfg-latin1.ini",
            "test_multicfg-utf-16.ini",
            "test_multicfg-utf-32.ini",
            "test_multicfg-utf8.ini",
            "test_multicfg-utf8.yaml",
            "test_multicfg.hjson",
            "test_multicfg.ini",
            "test_multicfg.js",
            "test_multicfg.toml",
            "test_multicfg.yaml",
        )

        for base_file in config_files:
            if self.verbose:
                print()

            path = self.test_cfg_dir / base_file
            LOG.info("Testing for file {!r} ...".format(str(path)))
            config = cfg_handler.load_file(path)


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
    suite.addTest(TestFbAnyConfig("test_guess_config_type_by_name", verbose))
    suite.addTest(TestFbAnyConfig("test_read_cfg_files", verbose))

    runner = unittest.TextTestRunner(verbosity=verbose)

    result = runner.run(suite)


# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
