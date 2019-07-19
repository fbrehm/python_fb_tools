#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
@author: Frank Brehm
@contact: frank@brehm-online.com
@copyright: © 2019 Frank Brehm, Berlin
@license: GPL3
@summary: test script (and module) for unit tests on PDNS objects
'''

import os
import sys
import logging
# import tempfile
import datetime

# from pathlib import Path

try:
    import unittest2 as unittest
except ImportError:
    import unittest

# from babel.dates import LOCALTZ

libdir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'lib'))
sys.path.insert(0, libdir)

from general import FbToolsTestcase, get_arg_verbose, init_root_logger

from fb_tools.common import pp

LOG = logging.getLogger('test_pdns')

# EXEC_LONG_TESTS = True
# if 'EXEC_LONG_TESTS' in os.environ and os.environ['EXEC_LONG_TESTS'] != '':
#     EXEC_LONG_TESTS = to_bool(os.environ['EXEC_LONG_TESTS'])


# =============================================================================
class TestFbPdns(FbToolsTestcase):

    # -------------------------------------------------------------------------
    def setUp(self):

        pass

    # -------------------------------------------------------------------------
    def tearDown(self):

        pass

    # -------------------------------------------------------------------------
    def test_import(self):

        LOG.info("Testing import of fb_tools.pdns ...")
        import fb_tools.pdns
        LOG.debug("Version of fb_tools.pdns: {!r}.".format(fb_tools.pdns.__version__))

        LOG.info("Testing import of fb_tools.pdns.errors ...")
        import fb_tools.pdns.errors
        LOG.debug("Version of fb_tools.pdns.errors: {!r}.".format(
            fb_tools.pdns.errors.__version__))

        LOG.info("Testing import of fb_tools.pdns.record ...")
        import fb_tools.pdns.record
        LOG.debug("Version of fb_tools.pdns.record: {!r}.".format(
            fb_tools.pdns.record.__version__))

        LOG.info("Testing import of fb_tools.pdns.zone ...")
        import fb_tools.pdns.zone
        LOG.debug("Version of fb_tools.pdns.zone: {!r}.".format(
            fb_tools.pdns.zone.__version__))

        LOG.info("Testing import of fb_tools.pdns.server ...")
        import fb_tools.pdns.server
        LOG.debug("Version of fb_tools.pdns.server: {!r}.".format(
            fb_tools.pdns.server.__version__))

        LOG.info("Testing import of PowerDNSHandlerError from fb_tools.pdns.errors ...")
        from fb_tools.pdns.errors import PowerDNSHandlerError               # noqa

        LOG.info("Testing import of PowerDNSZoneError from fb_tools.pdns.errors ...")
        from fb_tools.pdns.errors import PowerDNSZoneError                  # noqa

        LOG.info("Testing import of PowerDNSRecordError from fb_tools.pdns.errors ...")
        from fb_tools.pdns.errors import PowerDNSRecordError                # noqa

        LOG.info("Testing import of PowerDNSRecordSetError from fb_tools.pdns.errors ...")
        from fb_tools.pdns.errors import PowerDNSRecordSetError             # noqa

        LOG.info("Testing import of PDNSApiError from fb_tools.pdns.errors ...")
        from fb_tools.pdns.errors import PDNSApiError                       # noqa

        LOG.info("Testing import of PDNSApiNotAuthorizedError from fb_tools.pdns.errors ...")
        from fb_tools.pdns.errors import PDNSApiNotAuthorizedError          # noqa

        LOG.info("Testing import of PDNSApiNotFoundError from fb_tools.pdns.errors ...")
        from fb_tools.pdns.errors import PDNSApiNotFoundError               # noqa

        LOG.info("Testing import of PDNSApiValidationError from fb_tools.pdns.errors ...")
        from fb_tools.pdns.errors import PDNSApiValidationError             # noqa

        LOG.info("Testing import of PDNSApiRateLimitExceededError from fb_tools.pdns.errors ...")
        from fb_tools.pdns.errors import PDNSApiRateLimitExceededError      # noqa

        LOG.info("Testing import of PDNSApiRequestError from fb_tools.pdns.errors ...")
        from fb_tools.pdns.errors import PDNSApiRequestError                # noqa

        LOG.info("Testing import of PDNSApiTimeoutError from fb_tools.pdns.errors ...")
        from fb_tools.pdns.errors import PDNSApiTimeoutError                # noqa

        LOG.info("Testing import of PowerDNSRecord from fb_tools.pdns.record ...")
        from fb_tools.pdns.record import PowerDNSRecord                     # noqa

        LOG.info("Testing import of PowerDnsSOAData from fb_tools.pdns.record ...")
        from fb_tools.pdns.record import PowerDnsSOAData                    # noqa

        LOG.info("Testing import of PowerDNSRecordList from fb_tools.pdns.record ...")
        from fb_tools.pdns.record import PowerDNSRecordList                 # noqa

        LOG.info("Testing import of PowerDNSRecordSetComment from fb_tools.pdns.record ...")
        from fb_tools.pdns.record import PowerDNSRecordSetComment           # noqa

        LOG.info("Testing import of PowerDNSRecordSet from fb_tools.pdns.record ...")
        from fb_tools.pdns.record import PowerDNSRecordSet                  # noqa

        LOG.info("Testing import of PowerDNSRecordSetList from fb_tools.pdns.record ...")
        from fb_tools.pdns.record import PowerDNSRecordSetList              # noqa

        LOG.info("Testing import of PDNSNoRecordsToRemove from fb_tools.pdns.zone ...")
        from fb_tools.pdns.zone import PDNSNoRecordsToRemove               # noqa

        LOG.info("Testing import of PowerDNSZone from fb_tools.pdns.zone ...")
        from fb_tools.pdns.zone import PowerDNSZone                        # noqa

        LOG.info("Testing import of PowerDNSZoneDict from fb_tools.pdns.zone ...")
        from fb_tools.pdns.zone import PowerDNSZoneDict                    # noqa

        LOG.info("Testing import of PowerDNSServer from fb_tools.pdns.server ...")
        from fb_tools.pdns.server import PowerDNSServer                    # noqa

    # -------------------------------------------------------------------------
    def test_pdns_recordset_comment(self):

        LOG.info("Testing class PowerDNSRecordSetComment ...")

        test_account = 'tester'
        test_content = "Test comment"
        test_modified_at = 1000 * 24 * 60 * 60

        from fb_tools.pdns.record import PowerDNSRecordSetComment

        LOG.debug("Creating an empty, invalid comment.")
        empty_comment = PowerDNSRecordSetComment(
            appname=self.appname, verbose=self.verbose)
        LOG.debug("Empty comment: %%r: {!r}".format(empty_comment))
        LOG.debug("Empty comment: %%s: {}".format(empty_comment))
        LOG.debug("Empty comment.as_dict():\n{}".format(pp(empty_comment.as_dict())))
        LOG.debug("Empty comment.as_dict(minimal=True): {}".format(
            pp(empty_comment.as_dict(minimal=True))))
        self.assertIsNone(empty_comment.account)
        self.assertEqual(empty_comment.content, '')
        self.assertIsInstance(empty_comment.modified_at, int)
        self.assertGreaterEqual(empty_comment.modified_at, 0)
        self.assertIsInstance(empty_comment.modified_date, datetime.datetime)
        self.assertFalse(empty_comment.valid)
        del empty_comment

        LOG.debug("Creating an non empty, valid comment.")
        comment = PowerDNSRecordSetComment(
            appname=self.appname, verbose=self.verbose, account=test_account, content=test_content)
        LOG.debug("Comment: %%r: {!r}".format(comment))
        LOG.debug("Comment: %%s: {}".format(comment))
        LOG.debug("Comment.as_dict():\n{}".format(pp(comment.as_dict())))
        LOG.debug("Comment.as_dict(minimal=True): {}".format(
            pp(comment.as_dict(minimal=True))))
        self.assertEqual(comment.account, test_account)
        self.assertEqual(comment.content, test_content)
        self.assertIsInstance(comment.modified_at, int)
        self.assertGreaterEqual(comment.modified_at, 0)
        self.assertIsInstance(comment.modified_date, datetime.datetime)
        self.assertTrue(comment.valid)

        LOG.debug("Creating a comment with a defined modified_at property.")
        comment = PowerDNSRecordSetComment(
            appname=self.appname, verbose=self.verbose,
            account=test_account, content=test_content, modified_at=test_modified_at)
        LOG.debug("Comment: %%s: {}".format(comment))
        if self.verbose > 1:
            LOG.debug("Comment: %%r: {!r}".format(comment))
        if self.verbose > 2:
            LOG.debug("Ccomment.as_dict():\n{}".format(pp(comment.as_dict())))
        self.assertIsInstance(comment.modified_at, int)
        self.assertEqual(comment.modified_at, test_modified_at)
        self.assertIsInstance(comment.modified_date, datetime.datetime)

        LOG.debug("Testing raising errors on wrong (String) modified_at property.")
        with self.assertRaises(ValueError) as cm:
            comment = PowerDNSRecordSetComment(
                appname=self.appname, verbose=self.verbose,
                account=test_account, content=test_content, modified_at='bla')
        e = cm.exception
        LOG.debug("{} raised: {}".format(e.__class__.__name__, e))

        LOG.debug("Testing raising errors on wrong (negative) modified_at property.")
        with self.assertRaises(ValueError) as cm:
            comment = PowerDNSRecordSetComment(
                appname=self.appname, verbose=self.verbose,
                account=test_account, content=test_content, modified_at=-100)
        e = cm.exception
        LOG.debug("{} raised: {}".format(e.__class__.__name__, e))


# =============================================================================
if __name__ == '__main__':

    verbose = get_arg_verbose()
    if verbose is None:
        verbose = 0
    init_root_logger(verbose)

    LOG.info("Starting tests ...")

    suite = unittest.TestSuite()

    suite.addTest(TestFbPdns('test_import', verbose))
    suite.addTest(TestFbPdns('test_pdns_recordset_comment', verbose))

    runner = unittest.TextTestRunner(verbosity=verbose)

    result = runner.run(suite)


# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
