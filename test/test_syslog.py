#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
@author: Frank Brehm
@contact: frank@brehm-online.com
@copyright: © 2021 Frank Brehm, Berlin
@license: GPL3
@summary: test script (and module) for unit tests on logging objects
'''

import os
import sys
import logging
import logging.handlers

try:
    import unittest2 as unittest
except ImportError:
    import unittest

libdir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'lib'))
sys.path.insert(0, libdir)

from general import FbToolsTestcase, get_arg_verbose, init_root_logger

LOG = logging.getLogger('test_syslog')


# =============================================================================
class TestSyslogTestcase(FbToolsTestcase):

    # -------------------------------------------------------------------------
    def setUp(self):

        mb_chars = 'äöüÄÖÜß»«¢„“”µ·…@ł€¶ŧ←↓→øþ¨æſðđŋħłĸ˝^'
        py_version = "Python %d.%d.%d" % (
            sys.version_info[0], sys.version_info[1], sys.version_info[2])
        self.msg_utf8 = "Test %s UTF-8 with wide characters: '%s'." % (py_version, mb_chars)
        self.msg_uni = "Test %s Unicode with wide characters: '%s'." % (py_version, mb_chars)
        LOG.debug("self.msg_utf8 (%s): %r", self.msg_utf8.__class__.__name__, self.msg_utf8)
        LOG.debug("self.msg_uni (%s): %r", self.msg_uni.__class__.__name__, self.msg_uni)

        LOG.debug("This is %s", py_version)
        if sys.version_info[0] > 2:
            self.msg_utf8 = self.msg_utf8.encode('utf-8')
        else:
            self.msg_uni = self.msg_uni.decode('utf-8')

        LOG.debug("self.msg_utf8 (%s): %r", self.msg_utf8.__class__.__name__, self.msg_utf8)
        LOG.debug("self.msg_uni (%s): %r", self.msg_uni.__class__.__name__, self.msg_uni)

    # -------------------------------------------------------------------------
    def test_import_modules(self):

        LOG.info("Test importing all appropriate modules ...")

        LOG.debug("Importing ColoredFormatter from fb_tools.colored ...")
        from fb_tools.colored import ColoredFormatter                     # noqa

        LOG.debug("Importing FbSysLogHandler from fb_tools.syslog_handler ...")
        from fb_tools.syslog_handler import FbSysLogHandler               # noqa

        LOG.debug("Importing UnixSyslogHandler from fb_tools.unix_handler ...")
        from fb_tools.unix_handler import UnixSyslogHandler               # noqa

    # -------------------------------------------------------------------------
    @unittest.skipUnless(os.path.exists('/dev/log'), "Socket '/dev/log' must exist.")
    def test_logging_syslog(self):

        LOG.info("Test logging with FbSysLogHandler ...")

        from fb_tools.syslog_handler import FbSysLogHandler

        LOG.debug("Init of a test logger instance ...")
        test_logger = logging.getLogger('test.unicode')
        test_logger.setLevel(logging.INFO)
        appname = os.path.basename(sys.argv[0])

        format_str_syslog = (
            appname + ': %(name)s(%(lineno)d) %(funcName)s() %(levelname)s - %(message)s')
        format_str_console = (
            '[%(asctime)s]: ' + appname +
            ': %(name)s(%(lineno)d) %(funcName)s() %(levelname)s - %(message)s')

        formatter_syslog = logging.Formatter(format_str_syslog)
        formatter_console = logging.Formatter(format_str_console)

        LOG.debug("Init of a FbSysLogHandler ...")
        lh_syslog = FbSysLogHandler(
            address='/dev/log',
            facility=logging.handlers.SysLogHandler.LOG_USER,
        )

        lh_syslog.setFormatter(formatter_syslog)

        LOG.debug("Init of a StreamHandler ...")
        lh_console = logging.StreamHandler(sys.stderr)
        lh_console.setFormatter(formatter_console)

        LOG.debug("Adding log handlers to test logger instance ...")
        test_logger.addHandler(lh_syslog)
        test_logger.addHandler(lh_console)

        LOG.debug("Logging an UTF-8 message without wide characters ...")
        test_logger.info(self.msg_utf8)
        LOG.debug("Logging an unicode message with wide characters ...")
        test_logger.info(self.msg_uni)

    # -------------------------------------------------------------------------
    def test_unix_syslog(self):

        LOG.info("Test logging with UnixSyslogHandler ...")

        from fb_tools.unix_handler import UnixSyslogHandler

        LOG.debug("Init of a test logger instance ...")
        test_logger = logging.getLogger('test.unix_handler')
        test_logger.setLevel(logging.INFO)
        appname = os.path.basename(sys.argv[0])

        format_str_syslog = (
            appname + ': %(name)s(%(lineno)d) %(funcName)s() %(levelname)s - %(message)s')
        format_str_console = (
            '[%(asctime)s]: ' + appname +
            ': %(name)s(%(lineno)d) %(funcName)s() %(levelname)s - %(message)s')

        formatter_syslog = logging.Formatter(format_str_syslog)
        formatter_console = logging.Formatter(format_str_console)

        LOG.debug("Init of a UnixSyslogHandler ...")
        lh_unix_syslog = UnixSyslogHandler(
            ident=appname,
            facility=UnixSyslogHandler.LOG_USER,
        )

        lh_unix_syslog.setFormatter(formatter_syslog)

        LOG.debug("Init of a StreamHandler ...")
        lh_console = logging.StreamHandler(sys.stderr)
        lh_console.setFormatter(formatter_console)

        LOG.debug("Adding log handlers to test logger instance ...")
        test_logger.addHandler(lh_unix_syslog)
        test_logger.addHandler(lh_console)

        LOG.debug("Logging an UTF-8 message without wide characters ...")
        test_logger.info(self.msg_utf8)
        LOG.debug("Logging an unicode message with wide characters ...")
        test_logger.info(self.msg_uni)


# =============================================================================
if __name__ == '__main__':

    verbose = get_arg_verbose()
    if verbose is None:
        verbose = 0
    init_root_logger(verbose)

    LOG.info("Starting tests ...")

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTest(TestSyslogTestcase('test_import_modules', verbose))
    suite.addTest(TestSyslogTestcase('test_logging_syslog', verbose))
    suite.addTest(TestSyslogTestcase('test_unix_syslog', verbose))

    runner = unittest.TextTestRunner(verbosity=verbose)

    result = runner.run(suite)


# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
