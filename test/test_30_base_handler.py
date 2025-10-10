#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@summary: Test script (and module) for unit tests on base handler object.

@author: Frank Brehm
@contact: frank@brehm-online.com
@copyright: © 2025 Frank Brehm, Berlin
@license: GPL3
"""

import logging
import os
import sys
import textwrap

try:
    import unittest2 as unittest
except ImportError:
    import unittest

from babel.dates import LOCALTZ

libdir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, libdir)

from fb_tools.common import to_bool

from general import FbToolsTestcase, get_arg_verbose, init_root_logger

LOG = logging.getLogger('test_base_handler')

EXEC_LONG_TESTS = True
if 'EXEC_LONG_TESTS' in os.environ and os.environ['EXEC_LONG_TESTS'] != '':
    EXEC_LONG_TESTS = to_bool(os.environ['EXEC_LONG_TESTS'])


# =============================================================================
class TestFbBaseHandler(FbToolsTestcase):
    """Testcase for unit tests on module fb_tools.handler and class BaseHandler."""

    # -------------------------------------------------------------------------
    def setUp(self):
        """Execute this on setting up before calling each particular test method."""
        if self.verbose >= 1:
            print()

        self.test_file = None

    # -------------------------------------------------------------------------
    def tearDown(self):
        """Tear down routine for calling each particular test method."""
        if self.test_file is not None:
            if os.path.exists(self.test_file):
                LOG.debug('Removing {!r} ...'.format(self.test_file))
                os.remove(self.test_file)

    # -------------------------------------------------------------------------
    def test_import(self):
        """Test import of fb_tools.handler."""
        LOG.info(self.get_method_doc())

        import fb_tools.handler
        LOG.debug('Version of fb_tools.handler: {!r}'.format(
            fb_tools.handler.__version__))

        LOG.info('Test import of BaseHandler from fb_tools.handler ...')
        from fb_tools.handler import BaseHandler
        LOG.debug('Description of BaseHandler: ' + textwrap.dedent(BaseHandler.__doc__))

    # -------------------------------------------------------------------------
    def test_generic_base_handler(self):
        """Test init of a base handler object."""
        LOG.info(self.get_method_doc())

        import fb_tools.handler
        from fb_tools.handler import BaseHandler

        BaseHandler.fileio_timeout = 10
        hdlr = BaseHandler(
            appname=self.appname,
            verbose=self.verbose,
        )
        LOG.debug('BaseHandler %%r: {!r}'.format(hdlr))
        LOG.debug('BaseHandler %%s: {}'.format(hdlr))

        # from HandlingObject
        self.assertEqual(hdlr.appname, self.appname)
        self.assertEqual(hdlr.verbose, self.verbose)
        self.assertIsNotNone(hdlr.base_dir)
        self.assertEqual(hdlr.version, fb_tools.handler.__version__)
        self.assertFalse(hdlr.simulate)
        self.assertFalse(hdlr.force)
        self.assertFalse(hdlr.quiet)
        self.assertFalse(hdlr.interrupted)
        self.assertEqual(hdlr.fileio_timeout, 10)

        # from BaseHandler
        self.assertIsNotNone(hdlr.default_locale)
        self.assertIsNotNone(hdlr.tz)
        self.assertIsNotNone(hdlr.tz_name)
        self.assertFalse(hdlr.sudo)
        self.assertIsNotNone(hdlr.chown_cmd)
        self.assertIsNotNone(hdlr.echo_cmd)
        has_sudo = True
        if hdlr.sudo_cmd is None:
            has_sudo = False

        # from HandlingObject
        hdlr.simulate = True
        self.assertTrue(hdlr.simulate)

        hdlr.force = True
        self.assertTrue(hdlr.force)

        hdlr.quiet = True
        self.assertTrue(hdlr.quiet)

        # from BaseHandler
        if has_sudo:
            hdlr.sudo = True
            self.assertTrue(hdlr.sudo)

        LOG.debug('Setting timezone to {!r}'.format('America/Los_Angeles'))
        hdlr.set_tz('America/Los_Angeles')
        tz_name = LOCALTZ.zone
        LOG.debug('Setting timezone to {!r}'.format(tz_name))
        hdlr.set_tz(tz_name)

    # -------------------------------------------------------------------------
    @unittest.skipUnless(EXEC_LONG_TESTS, 'Long terming tests are not executed.')
    def test_call_sync(self):
        """Test synchronous execution of a shell script."""
        LOG.info(self.get_method_doc())

        from fb_tools.common import pp
        from fb_tools.errors import CommandNotFoundError
        from fb_tools.handling_obj import CompletedProcess
        import fb_tools.handler                                                 # noqa
        from fb_tools.handler import BaseHandler

        curdir = os.path.dirname(os.path.abspath(__file__))
        call_script = os.path.join(curdir, 'call_script.sh')
        if not os.path.exists(call_script):
            raise CommandNotFoundError(call_script)

        LOG.debug('Trying to execute {!r} synchronous ...'.format(call_script))

        hdlr = BaseHandler(
            appname=self.appname,
            verbose=self.verbose,
        )

        proc = hdlr.call([call_script])

        LOG.debug('Got back a {} object.'.format(proc.__class__.__name__))
        self.assertIsInstance(proc, CompletedProcess)

        LOG.debug('Got return value: {}.'.format(proc.returncode))
        LOG.debug('Got proc args:\n{}.'.format(pp(proc.args)))
        LOG.debug('Got STDOUT: {!r}'.format(proc.stdout))
        LOG.debug('Got STDERR: {!r}'.format(proc.stderr))

        self.assertEqual(proc.returncode, 0)
        self.assertIsNotNone(proc.stdout)
        self.assertIsNotNone(proc.stderr)

    # -------------------------------------------------------------------------
    @unittest.skipUnless(EXEC_LONG_TESTS, 'Long terming tests are not executed.')
    def test_call_async(self):
        """Test asynchronous execution of a shell script."""
        LOG.info(self.get_method_doc())

        from fb_tools.common import pp
        from fb_tools.errors import CommandNotFoundError
        from fb_tools.handling_obj import CompletedProcess
        import fb_tools.handler                                                 # noqa
        from fb_tools.handler import BaseHandler

        curdir = os.path.dirname(os.path.abspath(__file__))
        call_script = os.path.join(curdir, 'call_script.sh')
        if not os.path.exists(call_script):
            raise CommandNotFoundError(call_script)

        LOG.debug('Trying to execute {!r} asynchronous ...'.format(call_script))

        hdlr = BaseHandler(
            appname=self.appname,
            verbose=self.verbose,
        )

        def heartbeat():
            LOG.debug('Do you hear my heartbeat?')

        proc = hdlr.call([call_script], hb_handler=heartbeat, hb_interval=1)

        LOG.debug('Got back a {} object.'.format(proc.__class__.__name__))
        self.assertIsInstance(proc, CompletedProcess)

        LOG.debug('Got return value: {}.'.format(proc.returncode))
        LOG.debug('Got proc args:\n{}.'.format(pp(proc.args)))
        LOG.debug('Got STDOUT: {!r}'.format(proc.stdout))
        LOG.debug('Got STDERR: {!r}'.format(proc.stderr))

        self.assertEqual(proc.returncode, 0)
        self.assertIsNotNone(proc.stdout)
        self.assertIsNotNone(proc.stderr)


# =============================================================================
if __name__ == '__main__':

    verbose = get_arg_verbose()
    if verbose is None:
        verbose = 0
    init_root_logger(verbose)

    LOG.info('Starting tests ...')

    suite = unittest.TestSuite()

    suite.addTest(TestFbBaseHandler('test_import', verbose))
    suite.addTest(TestFbBaseHandler('test_generic_base_handler', verbose))
    suite.addTest(TestFbBaseHandler('test_call_sync', verbose))
    suite.addTest(TestFbBaseHandler('test_call_async', verbose))

    runner = unittest.TextTestRunner(verbosity=verbose)

    result = runner.run(suite)


# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
