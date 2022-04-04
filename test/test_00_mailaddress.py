#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
@author: Frank Brehm
@contact: frank.brehm@pixelpark.com
@copyright: © 2021 Frank Brehm, Digitas Pixelpark GmbH Berlin
@license: LGPL3
@summary: test script (and module) for unit tests on mailaddress class and objects
'''

import os
import sys
import logging
import copy
import random

# from importlib import reload

try:
    import unittest2 as unittest
except ImportError:
    import unittest

libdir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'lib'))
sys.path.insert(0, libdir)

from fb_tools.common import pp                                                  # noqa

from general import FbToolsTestcase, get_arg_verbose, init_root_logger          # noqa

LOG = logging.getLogger('test_mailaddress')


# =============================================================================
class TestMailaddress(FbToolsTestcase):

    # -------------------------------------------------------------------------
    def setUp(self):
        pass
        # if 'fb_tools.mailaddress' in sys.modules:
        #     LOG.debug("Reloading module 'fb_tools.mailaddress' ...")
        #     reload(fb_tools.mailaddress)

    # -------------------------------------------------------------------------
    def tearDown(self):
        # LOG.debug("Current loaded modules:\n" + pp(sys.modules))
        pass

    # -------------------------------------------------------------------------
    def test_import(self):

        if self.verbose == 1:
            print()
        LOG.info("Testing import of pp_admintools.mailaddress ...")

        import fb_tools.mailaddress
        LOG.debug("Version of fb_tools.mailaddress: {!r}".format(
            fb_tools.mailaddress.__version__))

    # -------------------------------------------------------------------------
    def test_object(self):

        if self.verbose == 1:
            print()
        LOG.info("Testing init of a simple mailaddress object.")

        test_address = 'frank@brehm-online.com'

        from fb_tools import MailAddress

        address = MailAddress(test_address, verbose=self.verbose)
        LOG.debug("MailAddress %r: {!r}".format(address))
        LOG.debug("MailAddress %s: {}".format(address))

        self.assertEqual(str(address), test_address)

        other_address = MailAddress(test_address, verbose=self.verbose)
        LOG.debug("Other MailAddress: {}".format(other_address))
        self.assertIsNot(address, other_address)
        self.assertEqual(address, other_address)

        LOG.debug("Copying address ...")
        yet_another_address = copy.copy(address)
        LOG.debug("Yet Another MailAddress: {}".format(yet_another_address))
        self.assertIsNot(address, yet_another_address)
        self.assertEqual(address, yet_another_address)
        self.assertEqual(yet_another_address.verbose, self.verbose)

        still_another_address = MailAddress(test_address, verbose=self.verbose)
        LOG.debug("Still Another MailAddress: {}".format(still_another_address))
        self.assertEqual(address, still_another_address)

        wrong_verboses = ('uhu', -3)
        for verb in wrong_verboses:
            LOG.debug("Testing wrong verbose level {!r} ...".format(verb))
            with self.assertRaises((TypeError, ValueError)) as cm:
                address = MailAddress(test_address, verbose=verb)
                LOG.error("This should not be visible: {!r}".format(address))
            e = cm.exception
            LOG.debug("{c} raised: {e}".format(c=e.__class__.__name__, e=e))

        expected_dict = {
            '__class_name__': 'MailAddress',
            'domain': 'brehm-online.com',
            'empty_ok': False,
            'user': 'frank',
            'verbose': self.verbose
        }
        expected_tuple = ('frank', 'brehm-online.com', self.verbose, False)

        got_dict = address.as_dict()
        LOG.debug("MailAddress.as_dict():\n" + pp(got_dict))
        self.assertEqual(got_dict, expected_dict)

        got_tuple = address.as_tuple()
        LOG.debug("MailAddress.as_tuple():\n" + pp(got_tuple))
        self.assertEqual(got_tuple, expected_tuple)

    # -------------------------------------------------------------------------
    def test_empty_address(self):

        if self.verbose == 1:
            print()
        LOG.info("Testing init of an empty mailaddress objects.")

        from fb_tools import MailAddress
        from fb_tools.errors import BaseMailAddressError

        LOG.debug("Testing raise on init empty mail address ...")
        with self.assertRaises(BaseMailAddressError) as cm:
            address = MailAddress(verbose=self.verbose)
            LOG.error("This should not be visible: {!r}".format(address))
        e = cm.exception
        LOG.debug("{c} raised: {e}".format(c=e.__class__.__name__, e=e))

        LOG.debug("Testing successful init of an empty mail address ...")
        address = MailAddress(empty_ok=True, verbose=self.verbose)
        LOG.debug("Empty MailAddress {a!r}: {s!r}".format(
            a=address, s=str(address)))
        self.assertEqual(str(address), '')

    # -------------------------------------------------------------------------
    def test_compare(self):

        if self.verbose == 1:
            print()
        LOG.info("Testing comparision of mail addresses.")

        from fb_tools import MailAddress

        a1 = 'uhu@banane.de'
        a2 = 'Uhu@Banane.de'
        a3 = 'frank.brehm@uhu-banane.de'
        a4 = 'frank-brehm@uhu-banane.de'

        LOG.debug("Testing equality with different verbose levels.")
        address1 = MailAddress(a1, verbose=1)
        address2 = MailAddress(a1, verbose=2)
        self.assertEqual(address1, address2)

        LOG.debug("Testing equality of addresses with different cases.")
        address1 = MailAddress(a1, verbose=self.verbose)
        address2 = MailAddress(a2, verbose=self.verbose)
        self.assertEqual(address1, address2)

        LOG.debug("Testing inequality of addresses with minor differences.")
        address1 = MailAddress(a3, verbose=self.verbose)
        address2 = MailAddress(a4, verbose=self.verbose)
        self.assertNotEqual(address1, address2)

    # -------------------------------------------------------------------------
    def test_wrong_addresses(self):

        if self.verbose == 1:
            print()
        LOG.info("Testing init of wrong mailaddress objects.")

        from fb_tools import MailAddress
        from fb_tools.errors import BaseMailAddressError

        correct_addresses = (
            ('frank.brehm', 'frank.brehm'),
            ('uhu_banane.de', 'uhu_banane.de'),
            ('@uhu-banane.de', '@uhu-banane.de'),
            ('uhu@banane.de', 'uhu@banane.de'),
            ('Uhu@Banane.de', 'uhu@banane.de'),
            ('ich@mueller.de', 'ich@mueller.de'),
            ('root+bla@banane.de', 'root+bla@banane.de'),
            ('root+bla.uhu-banane.de@banane.de', 'root+bla.uhu-banane.de@banane.de'),
            ('root+bla+blub@banane.de', 'root+bla+blub@banane.de'),
            ('frank.uwe@banane.de', 'frank.uwe@banane.de'),
            ('frank.uwe.brehm@banane.de', 'frank.uwe.brehm@banane.de'),
            ('frank-uwe.61@banane.de', 'frank-uwe.61@banane.de'),
            ('frank_uwe@banane.de', 'frank_uwe@banane.de'),
            ('frank_uwe.61@banane.de', 'frank_uwe.61@banane.de'),
        )

        for pair in correct_addresses:
            addr = pair[0]
            expected = pair[1]
            LOG.debug("Testing mail address {a!r} => {e!r} ...".format(a=addr, e=expected))
            address = MailAddress(addr, verbose=self.verbose)
            LOG.debug("Successful mail address from {s!r}: {a!r} => {r!r}".format(
                s=addr, a=str(address), r=address))
            self.assertEqual(str(address), expected)

        wrong_addresses = (
            True, 1, ('uhu@banane.de', ), ['uhu@banane.de'], 'uhu:banane', 'uhu!banane', 'a@b@c',
            'müller.de', 'ich@Müller.de', 'ich@mueller', '@uhu_banane.de', 'frank@uhu_banane.de',
        )

        for addr in wrong_addresses:
            LOG.debug("Testing wrong mail address {!r} ...".format(addr))
            with self.assertRaises(BaseMailAddressError) as cm:
                address = MailAddress(addr, verbose=self.verbose)
                LOG.error("This should not be visible: {!r}".format(address))
            e = cm.exception
            LOG.debug("{c} raised: {e}".format(c=e.__class__.__name__, e=e))

    # -------------------------------------------------------------------------
    def test_wrong_user(self):

        if self.verbose == 1:
            print()
        LOG.info("Testing wrong users on init of mailaddress objects.")

        from fb_tools import MailAddress
        from fb_tools.errors import BaseMailAddressError

        domain = 'uhu-banane.de'
        correct_users = (
            None, '', 'me', 'Frank', 'Frank-Uwe', 'soeren', 'root+bla',
            'root+bla.uhu-banane.de', 'root+bla+blub'
        )
        wrong_users = (
            'Frank Uwe', 'Sören', True, 1, 'uhu:banane', 'uhu!banane', 'a@b', 'a@b@c',
            'root+bla blub'
        )

        for user in correct_users:
            LOG.debug("Testing correct user {!r} ...".format(user))
            address = MailAddress(user=user, domain=domain, verbose=self.verbose)
            LOG.debug("Successful mail address from {u!r} (@{d}): {a!r} => {r!r}".format(
                u=user, d=domain, a=str(address), r=address))

        for user in wrong_users:
            LOG.debug("Testing wrong user {!r} ...".format(user))
            with self.assertRaises(BaseMailAddressError) as cm:
                address = MailAddress(user=user, domain=domain, verbose=self.verbose)
                LOG.error("This should not be visible: {!r}".format(address))
            e = cm.exception
            LOG.debug("{c} raised: {e}".format(c=e.__class__.__name__, e=e))

    # -------------------------------------------------------------------------
    def test_to_str(self):

        if self.verbose == 1:
            print()
        LOG.info("Testing typecasting to str.")

        from fb_tools import MailAddress

        data = (
            ('uhu', 'banane.de', 'uhu@banane.de', 'uhu@banane.de'),
            ('Uhu', 'Banane.de', 'uhu@banane.de', 'uhu@banane.de'),
            ('uhu', None, 'uhu', 'uhu@'),
            (None, 'banane.de', '@banane.de', 'banane.de'),
            (None, None, '', ''),
        )

        for row in data:
            address = MailAddress(
                user=row[0], domain=row[1], verbose=self.verbose, empty_ok=True)
            LOG.debug("Testing typecasting or address {!r}.".format(address))
            LOG.debug("Expected: Str(adress): {s!r}, adress.str_for_access(): {a!r}".format(
                s=row[2], a=row[3]))
            addr_str = str(address)
            addr_access_str = address.str_for_access()
            LOG.debug("Str(adress): {s!r}, adress.str_for_access(): {a!r}".format(
                s=addr_str, a=addr_access_str))
            self.assertEqual(addr_str, row[2])
            self.assertEqual(addr_access_str, row[3])

    # -------------------------------------------------------------------------
    def test_sorting(self):

        if self.verbose == 1:
            print()
        LOG.info("Testing typecasting to str.")

        from fb_tools import MailAddress

        addr_list = (
            ('a1', 'banane.de'),
            ('a2', 'banane.de'),
            ('uhu', 'banane.de'),
            ('Uhu', 'Banane.de'),
            ('uhu', None),
            (None, 'banane.de'),
            ('Uhu', 'xylophon.de'),
            (None, None),
        )

        expected_list = [
            '',
            'uhu',
            '@banane.de',
            'a1@banane.de',
            'a2@banane.de',
            'uhu@banane.de',
            'uhu@banane.de',
            'uhu@xylophon.de',
        ]

        result_list = []

        alist = []
        for row in random.sample(addr_list, k=len(addr_list)):
            address = MailAddress(
                user=row[0], domain=row[1], verbose=self.verbose, empty_ok=True)
            alist.append(address)
        LOG.debug("Shuffeled address list:\n{}".format(pp(alist)))
        addr_list = sorted(alist)
        LOG.debug("Sorted address list:\n{}".format(pp(addr_list)))
        LOG.debug("Expected address list:\n{}".format(pp(expected_list)))
        for addr in addr_list:
            result_list.append(str(addr))
        LOG.debug("Sorted address list:\n{}".format(pp(result_list)))
        self.assertEqual(expected_list, result_list)

    # -------------------------------------------------------------------------
    def test_qualified_object(self):

        if self.verbose == 1:
            print()
        LOG.info("Testing init of a qualified mailaddress object.")

        test_address = 'frank@brehm-online.com'
        test_name = 'Frank Brehm'
        expected_str = '{n} <{a}>'.format(n=test_name, a=test_address)

        from fb_tools import QualifiedMailAddress

        address = QualifiedMailAddress(test_address, name=test_name, verbose=self.verbose)
        LOG.debug("QualifiedMailAddress %r: {!r}".format(address))
        LOG.debug("QualifiedMailAddress %s: {}".format(address))

        self.assertEqual(str(address), expected_str)

        other_address = QualifiedMailAddress(test_address, name=test_name, verbose=self.verbose)
        LOG.debug("Other QualifiedMailAddress: {}".format(other_address))
        self.assertIsNot(address, other_address)
        self.assertEqual(address, other_address)

        yet_another_address = copy.copy(address)
        LOG.debug("Yet Another QualifiedMailAddress: {}".format(yet_another_address))
        self.assertIsNot(address, yet_another_address)
        self.assertEqual(address, yet_another_address)
        self.assertEqual(yet_another_address.verbose, self.verbose)

        still_another_address = QualifiedMailAddress(
            test_address, name=test_name, verbose=self.verbose)
        LOG.debug("Still Another QualifiedMailAddress: {}".format(still_another_address))
        self.assertEqual(address, still_another_address)

        expected_dict = {
            '__class_name__': 'QualifiedMailAddress',
            'domain': 'brehm-online.com',
            'empty_ok': False,
            'name': 'Frank Brehm',
            'user': 'frank',
            'verbose': self.verbose
        }
        expected_tuple = ('brehm-online.com', 'frank', self.verbose, False, 'Frank Brehm')

        got_dict = address.as_dict()
        LOG.debug("MailAddress.as_dict():\n" + pp(got_dict))
        self.assertEqual(got_dict, expected_dict)

        got_tuple = address.as_tuple()
        LOG.debug("MailAddress.as_tuple():\n" + pp(got_tuple))
        self.assertEqual(got_tuple, expected_tuple)


# =============================================================================
if __name__ == '__main__':

    verbose = get_arg_verbose()
    if verbose is None:
        verbose = 0
    init_root_logger(verbose)

    LOG.info("Starting tests ...")

    suite = unittest.TestSuite()

    suite.addTest(TestMailaddress('test_import', verbose))
    suite.addTest(TestMailaddress('test_object', verbose))
    suite.addTest(TestMailaddress('test_empty_address', verbose))
    suite.addTest(TestMailaddress('test_compare', verbose))
    suite.addTest(TestMailaddress('test_wrong_addresses', verbose))
    suite.addTest(TestMailaddress('test_wrong_user', verbose))
    suite.addTest(TestMailaddress('test_to_str', verbose))
    suite.addTest(TestMailaddress('test_sorting', verbose))
    # suite.addTest(TestMailaddress('test_qualified_object', verbose))

    runner = unittest.TextTestRunner(verbosity=verbose)

    result = runner.run(suite)


# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
