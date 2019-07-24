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
import json

from pathlib import Path

try:
    import unittest2 as unittest
except ImportError:
    import unittest

# from babel.dates import LOCALTZ
import six

import requests
import requests_mock

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

        self.curdir = Path(os.path.dirname(os.path.abspath(__file__)))
        self.zone_file = self.curdir / 'zone.js'
        self.a_rrset_file = self.curdir / 'rrset-a.js'
        self.a_rrset_file_comment = self.curdir / 'rrset-a-with-comment.js'
        self.mx_rrset_file = self.curdir / 'rrset-mx.js'
        self.soa_rrset_file = self.curdir / 'rrset-soa.js'

        self.server_name = 'pdns-master.testing.net'
        self.api_key = 'test123'

        self.open_args = {}
        if six.PY3:
            self.open_args['encoding'] = 'utf-8'
            self.open_args['errors'] = 'surrogateescape'

        self.server_version = '4.1.10-mocked'

        self.server_list_data = [
            {
                "config_url": "/api/v1/servers/localhost/config{/config_setting}",
                "daemon_type": "authoritative",
                "id": "localhost",
                "type": "Server",
                "url": "/api/v1/servers/localhost",
                "version": "{}".format(self.server_version),
                "zones_url": "/api/v1/servers/localhost/zones{/zone}"
            }
        ]

    # -------------------------------------------------------------------------
    def tearDown(self):

        pass

    # -------------------------------------------------------------------------
    def get_js_a_rrset(self):

        ret = None
        with self.a_rrset_file.open('r', **self.open_args) as fh:
            ret = json.load(fh)
        return ret

    # -------------------------------------------------------------------------
    def get_js_a_rrset_comment(self):

        ret = None
        with self.a_rrset_file_comment.open('r', **self.open_args) as fh:
            ret = json.load(fh)
        return ret

    # -------------------------------------------------------------------------
    def get_js_mx_rrset(self):

        ret = None
        with self.mx_rrset_file.open('r', **self.open_args) as fh:
            ret = json.load(fh)
        return ret

    # -------------------------------------------------------------------------
    def get_js_soa_rrset(self):

        ret = None
        with self.soa_rrset_file.open('r', **self.open_args) as fh:
            ret = json.load(fh)
        return ret

    # -------------------------------------------------------------------------
    def get_js_zone(self):

        ret = None
        with self.zone_file.open('r', **self.open_args) as fh:
            ret = json.load(fh)
        return ret

    # -------------------------------------------------------------------------
    def get_js_serverlist(self, index=None):

        import json

        if index is None:
            data = self.server_list_data
        else:
            data = self.server_list_data[index]

        return json.dumps(data)

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
        if self.verbose > 1:
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
        if self.verbose > 1:
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

    # -------------------------------------------------------------------------
    def test_pdns_record(self):

        LOG.info("Testing class PowerDNSRecord ...")

        test_content = "www.testing.com."

        from fb_tools.pdns.record import PowerDNSRecord

        LOG.debug("Creating an enabled record.")
        record = PowerDNSRecord(
            appname=self.appname, verbose=self.verbose, content=test_content)
        LOG.debug("Record: %%r: {!r}".format(record))
        if self.verbose > 1:
            LOG.debug("Record: %%s: {}".format(record))
            LOG.debug("record.as_dict():\n{}".format(pp(record.as_dict())))
        self.assertEqual(record.content, test_content)
        self.assertIsInstance(record.disabled, bool)
        self.assertFalse(record.disabled)

        LOG.debug("Creating a disabled record.")
        record = PowerDNSRecord(
            appname=self.appname, verbose=self.verbose, content=test_content, disabled=True)
        LOG.debug("Record: %%r: {!r}".format(record))
        LOG.debug("Record: %%s: {}".format(record))
        if self.verbose > 1:
            LOG.debug("record.as_dict():\n{}".format(pp(record.as_dict())))
        self.assertEqual(record.content, test_content)
        self.assertIsInstance(record.disabled, bool)
        self.assertTrue(record.disabled)

    # -------------------------------------------------------------------------
    def test_pdns_recordset_simple(self):

        LOG.info("Testing class PowerDNSRecordSet ...")

        from fb_tools.pdns.record import PowerDNSRecordSet

        js_rrset = self.get_js_a_rrset()

        rrset = PowerDNSRecordSet.init_from_dict(
            js_rrset, appname=self.appname, verbose=self.verbose)
        LOG.debug("RecordSet: %%r: {!r}".format(rrset))
        if self.verbose > 1:
            LOG.debug("RecordSet: %%s: {}".format(rrset))
            LOG.debug("rrset.as_dict():\n{}".format(pp(rrset.as_dict())))
        LOG.debug("RecordSet.as_dict(minimal=True): {}".format(
            pp(rrset.as_dict(minimal=True))))

    # -------------------------------------------------------------------------
    def test_pdns_recordset_comment(self):

        LOG.info("Testing class PowerDNSRecordSet with comments ...")

        from fb_tools.pdns.record import PowerDNSRecordSet

        js_rrset = self.get_js_a_rrset_comment()

        rrset = PowerDNSRecordSet.init_from_dict(
            js_rrset, appname=self.appname, verbose=self.verbose)
        LOG.debug("RecordSet: %%r: {!r}".format(rrset))
        if self.verbose > 1:
            LOG.debug("RecordSet: %%s: {}".format(rrset))
            LOG.debug("rrset.as_dict():\n{}".format(pp(rrset.as_dict())))
        LOG.debug("RecordSet.as_dict(minimal=True): {}".format(
            pp(rrset.as_dict(minimal=True))))

    # -------------------------------------------------------------------------
    def test_zone_simple(self):

        LOG.info("Testing class PowerDNSZone ...")

        from fb_tools.pdns.zone import PowerDNSZone

        js_zone = self.get_js_zone()

        zone = PowerDNSZone.init_from_dict(
            js_zone, appname=self.appname, verbose=self.verbose)
        LOG.debug("Zone: %%r: {!r}".format(zone))
        if self.verbose > 1:
            LOG.debug("Zone: %%s: {}".format(zone))
            LOG.debug("zone.as_dict():\n{}".format(pp(zone.as_dict())))

    # -------------------------------------------------------------------------
    def test_zone_get_soa(self):

        LOG.info("Testing class PowerDNSZone.get_soa() ...")

        from fb_tools.pdns.zone import PowerDNSZone

        js_zone = self.get_js_zone()

        zone = PowerDNSZone.init_from_dict(
            js_zone, appname=self.appname, verbose=self.verbose)
        if self.verbose > 1:
            LOG.debug("Zone: %%r: {!r}".format(zone))

        soa = zone.get_soa()
        if self.verbose > 2:
            LOG.debug("Got SOA object:\n{}".format(pp(soa.as_dict())))
        self.assertIsNotNone(soa)
        self.assertEqual(soa.primary, 'ns1.example.com.')
        self.assertEqual(soa.email, 'hostmaster.example.com.')
        self.assertEqual(soa.serial, 2018061201)
        self.assertEqual(soa.refresh, 10800)
        self.assertEqual(soa.retry, 1800)
        self.assertEqual(soa.expire, 604800)
        self.assertEqual(soa.ttl, 3600)

    # -------------------------------------------------------------------------
    def test_verify_fqdn(self):

        LOG.info("Testing PowerDNSZone.verify_fqdn() ...")

        valid_fqdns = [
            '@', 'testing.com.', 'uhu.testing.com.', ' uhu.testing.com.',
            'uhu.banane.testing.com.', 'UHU.TESTING.COM.']
        invalid_fqdns_type = [None, 33, True]
        invalid_fqdns_value = [
            '', '.', 'bla.@', 'testing.com', 'test.com.', '.testing.com', '.testing.com.',
            '4+5.testing.com.', '.uhu.testing.com.', 'uhu.testing.net.']

        from fb_tools.pdns.zone import PowerDNSZone

        js_zone = self.get_js_zone()

        zone = PowerDNSZone.init_from_dict(
            js_zone, appname=self.appname, verbose=self.verbose)
        if self.verbose > 1:
            LOG.debug("Zone: %%r: {!r}".format(zone))
        if self.verbose > 2:
            LOG.debug("zone.as_dict():\n{}".format(pp(zone.as_dict())))

        for fqdn in valid_fqdns:
            LOG.debug("Testing FQDN {f!r} for zone {z!r} ...".format(f=fqdn, z=zone.name))
            got_fqdn = zone.verify_fqdn(fqdn)
            LOG.debug("Got verified FQDN {!r}.".format(got_fqdn))
            self.assertIsNotNone(got_fqdn)

        for fqdn in invalid_fqdns_type:
            LOG.debug("Testing raise on FQDN {f!r} for zone {z!r} ...".format(f=fqdn, z=zone.name))
            with self.assertRaises(TypeError) as cm:
                got_fqdn = zone.verify_fqdn(fqdn)                                       # noqa
            e = cm.exception
            LOG.debug("{} raised: {}".format(e.__class__.__name__, e))

            LOG.debug("Testing returning None on FQDN {f!r} for zone {z!r} ...".format(
                f=fqdn, z=zone.name))
            got_fqdn = zone.verify_fqdn(fqdn, raise_on_error=False)
            LOG.debug("Got back {!r}.".format(got_fqdn))
            self.assertIsNone(got_fqdn)

        for fqdn in invalid_fqdns_value:
            LOG.debug("Testing raise on FQDN {f!r} for zone {z!r} ...".format(f=fqdn, z=zone.name))
            with self.assertRaises(ValueError) as cm:
                got_fqdn = zone.verify_fqdn(fqdn)                                       # noqa
            e = cm.exception
            LOG.debug("{} raised: {}".format(e.__class__.__name__, e))

            LOG.debug("Testing returning None on FQDN {f!r} for zone {z!r} ...".format(
                f=fqdn, z=zone.name))
            got_fqdn = zone.verify_fqdn(fqdn, raise_on_error=False)
            LOG.debug("Got back {!r}.".format(got_fqdn))
            self.assertIsNone(got_fqdn)

    # -------------------------------------------------------------------------
    def test_get_zone(self):

        LOG.info("Testing getting a zone from a mocked PDNS API ...")

        adapter = requests_mock.Adapter()
        session = requests.Session()
        session.mount('mock', adapter)

        js_zone = self.get_js_zone()

        from fb_tools.pdns.server import PowerDNSServer
        from fb_tools.pdns.zone import PowerDNSZone

        pdns = PowerDNSServer(
            appname=self.appname, verbose=self.verbose, master_server=self.server_name,
            key=self.api_key, use_https=False)
        pdns.mocked = True
        slist = self.get_js_serverlist()
        pdns.mocking_paths.append({
            'method': 'GET', 'url': '/api/v1/servers', 'text': slist})
        s_localhost = self.get_js_serverlist(0)
        pdns.mocking_paths.append({
            'method': 'GET', 'url': '/api/v1/servers/localhost', 'text': s_localhost})

        LOG.debug("PowerDNSServer  %%r: {!r}".format(pdns))
        if self.verbose > 1:
            LOG.debug("PowerDNSServer: %%s: {}".format(pdns))
        if self.verbose > 2:
            LOG.debug("pdns.as_dict():\n{}".format(pp(pdns.as_dict())))

        api_version = pdns.get_api_server_version()

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
    suite.addTest(TestFbPdns('test_pdns_record', verbose))
    suite.addTest(TestFbPdns('test_pdns_recordset_simple', verbose))
    suite.addTest(TestFbPdns('test_pdns_recordset_comment', verbose))
    suite.addTest(TestFbPdns('test_zone_simple', verbose))
    suite.addTest(TestFbPdns('test_verify_fqdn', verbose))
    suite.addTest(TestFbPdns('test_zone_get_soa', verbose))
    suite.addTest(TestFbPdns('test_get_zone', verbose))

    runner = unittest.TextTestRunner(verbosity=verbose)

    result = runner.run(suite)


# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
