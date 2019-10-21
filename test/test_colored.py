#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: Frank Brehm
@contact: frank@brehm-online.com
@copyright: © 2019 Frank Brehm, Berlin
@license: GPL3
@summary: testing colored logging formatter
"""

import os
import sys
import logging

try:
    import unittest2 as unittest
except ImportError:
    import unittest

libdir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'lib'))
sys.path.insert(0, libdir)

from general import FbToolsTestcase, get_arg_verbose, init_root_logger

LOG = logging.getLogger('test_common')


# =============================================================================
class TestColoredFormatter(FbToolsTestcase):

    # -------------------------------------------------------------------------
    def setUp(self):
        pass

    # -------------------------------------------------------------------------
    def test_import(self):

        LOG.info("Testing import of fb_tools.colored ...")
        import fb_tools.colored                                         # noqa

    # -------------------------------------------------------------------------
    def test_colorcode(self):

        LOG.info("Testing colored output ...")

        from fb_tools.colored import COLOR_CODE
        from fb_tools.colored import colorstr

        msg = "Colored output"

        print('')
        for key in sorted(COLOR_CODE.keys()):

            try:
                print('%s: %s' % (key, colorstr(msg, key)))
            except Exception as e:
                self.fail("Failed to generate colored string %r with %s: %s" % (
                    key, e.__class__.__name__, str(e)))

    # -------------------------------------------------------------------------
    def test_object(self):

        LOG.info("Testing init of a ColoredFormatter object ...")

        from fb_tools.colored import ColoredFormatter

        try:
            formatter = ColoredFormatter(                                   # noqa
                '%(name)s: %(message)s (%(filename)s:%(lineno)d)')
        except Exception as e:
            self.fail("Could not instatiate ColoredFormatter object with %s: %s" % (
                e.__class__.__name__, str(e)))

    # -------------------------------------------------------------------------
    def test_colored_logging(self):

        LOG.info("Testing logging with a ColoredFormatter object ...")

        from fb_tools.colored import ColoredFormatter

        fmt_str = '%(name)s: %(message)s (%(filename)s:%(lineno)d)'
        test_logger = logging.getLogger('test.colored_logging')

        orig_handlers = []
        for log_handler in test_logger.handlers:
            orig_handlers.append(log_handler)
            test_logger.removeHandler(log_handler)

        try:
            c_formatter = ColoredFormatter(fmt_str)
            lh_console = logging.StreamHandler(sys.stdout)
            lh_console.setLevel(logging.DEBUG)
            lh_console.setFormatter(c_formatter)
            test_logger.addHandler(lh_console)

            test_logger.debug('debug')
            test_logger.info('info')
            test_logger.warning('Warning')
            test_logger.error('ERROR')
            test_logger.critical('CRITICAL!!!')

        finally:
            for log_handler in test_logger.handlers:
                test_logger.removeHandler(log_handler)
            for log_handler in orig_handlers:
                test_logger.addHandler(log_handler)

    # -------------------------------------------------------------------------
    def test_dark_colored_logging(self):

        LOG.info("Testing logging with a ColoredFormatter object with dark colors ...")

        from fb_tools.colored import ColoredFormatter

        fmt_str = '%(name)s: %(message)s (%(filename)s:%(lineno)d)'
        test_logger = logging.getLogger('test.colored_logging')

        orig_handlers = []
        for log_handler in test_logger.handlers:
            orig_handlers.append(log_handler)
            test_logger.removeHandler(log_handler)

        try:
            c_formatter = ColoredFormatter(fmt_str, dark=True)
            lh_console = logging.StreamHandler(sys.stdout)
            lh_console.setLevel(logging.DEBUG)
            lh_console.setFormatter(c_formatter)
            test_logger.addHandler(lh_console)

            test_logger.debug('debug')
            test_logger.info('info')
            test_logger.warning('Warning')
            test_logger.error('ERROR')
            test_logger.critical('CRITICAL!!!')

        finally:
            for log_handler in test_logger.handlers:
                test_logger.removeHandler(log_handler)
            for log_handler in orig_handlers:
                test_logger.addHandler(log_handler)


# =============================================================================

if __name__ == '__main__':

    verbose = get_arg_verbose()
    if verbose is None:
        verbose = 0
    init_root_logger(verbose)

    LOG.info("Starting tests ...")

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTest(TestColoredFormatter('test_import', verbose))
    suite.addTest(TestColoredFormatter('test_colorcode', verbose))
    suite.addTest(TestColoredFormatter('test_object', verbose))
    suite.addTest(TestColoredFormatter('test_colored_logging', verbose))
    suite.addTest(TestColoredFormatter('test_dark_colored_logging', verbose))

    runner = unittest.TextTestRunner(verbosity=verbose)

    result = runner.run(suite)

# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
