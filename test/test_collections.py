#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
@author: Frank Brehm
@contact: frank@brehm-online.com
@copyright: © 2020 Frank Brehm, Berlin
@license: GPL3
@summary: test script (and module) for unit tests on fb_tools.collections
'''

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

LOG = logging.getLogger('test_collections')


# =============================================================================
class TestFbCollections(FbToolsTestcase):

    # -------------------------------------------------------------------------
    def setUp(self):
        pass

    # -------------------------------------------------------------------------
    def test_import(self):

        LOG.info("Testing import of fb_tools.collections ...")
        import fb_tools.collections
        LOG.debug("Version of fb_tools.collections: {!r}".format(fb_tools.collections.__version__))

    # -------------------------------------------------------------------------
    def test_init_frozenset(self):

        LOG.info("Testing init of a FrozenCaseInsensitiveStringSet object.")

        from fb_tools.collections import FrozenCaseInsensitiveStringSet
        from fb_tools.collections import WrongItemTypeError

        LOG.debug("Testing init of an empty set.")
        my_set = FrozenCaseInsensitiveStringSet()
        LOG.debug("FrozenCaseInsensitiveStringSet %r: {!r}".format(my_set))
        LOG.debug("FrozenCaseInsensitiveStringSet %s: {}".format(my_set))
        self.assertEqual(my_set.as_list(), [])

        correct_iterables = (
            (('a',), ['a']),
            (['a'], ['a']),
            (['A'], ['A']),
            (['a', 'b'], ['a', 'b']),
            (['a', 'B'], ['a', 'B']),
            (['b', 'a'], ['a', 'b']),
            (['a', 'a'], ['a']),
            (['a', 'A'], ['A']),
            (['A', 'a'], ['a']),
        )

        for test_tuple in correct_iterables:
            src = test_tuple[0]
            expected = test_tuple[1]
            LOG.debug("Testing init of a FrozenCaseInsensitiveStringSet from {!r}.".format(src))
            my_set = FrozenCaseInsensitiveStringSet(src)
            if self.verbose > 1:
                LOG.debug("FrozenCaseInsensitiveStringSet %s: {}".format(my_set))
            result = my_set.as_list()
            LOG.debug("FrozenCaseInsensitiveStringSet as a list: {r!r} (expeced: {ex!r})".format(
                r=result, ex=expected))
            self.assertEqual(result, expected)

        class Tobj(object):
            def uhu(self):
                return 'banane'

        tobj = Tobj()

        wrong_iterables = (
            'a', 1, {'uhu': 'banane'}, tobj, tobj.uhu)

        for obj in wrong_iterables:

            msg = "Trying to init a FrozenCaseInsensitiveStringSet from {!r} ..."
            LOG.debug(msg.format(obj))
            with self.assertRaises(TypeError) as cm:
                my_set = FrozenCaseInsensitiveStringSet(obj)
            e = cm.exception
            msg = ("TypeError raised on init of a "
                    "FrozenCaseInsensitiveStringSet object: {}").format(e)
            LOG.debug(msg)

        iterables_with_wrong_values = (
                [None], [1], ['a', 1], [{'uhu': 'banane'}], [tobj], [tobj.uhu])

        for obj in iterables_with_wrong_values:

            msg = "Trying to init a FrozenCaseInsensitiveStringSet from {!r} ..."
            LOG.debug(msg.format(obj))
            with self.assertRaises(WrongItemTypeError) as cm:
                my_set = FrozenCaseInsensitiveStringSet(obj)
            e = cm.exception
            msg = ("WrongItemTypeError raised on init of a "
                    "FrozenCaseInsensitiveStringSet object: {}").format(e)
            LOG.debug(msg)

    # -------------------------------------------------------------------------
    def test_frozenset_len(self):

        LOG.info("Testing len() of a FrozenCaseInsensitiveStringSet object.")

        from fb_tools.collections import FrozenCaseInsensitiveStringSet

        test_tuples = (
            (None, 0),
            ([], 0),
            (['a'], 1),
            (['a', 'b'], 2),
        )

        for test_tuple in test_tuples:
            src = test_tuple[0]
            expected_len = test_tuple[1]
            LOG.debug("Testing len() of a FrozenCaseInsensitiveStringSet from {!r}.".format(src))
            my_set = FrozenCaseInsensitiveStringSet(src)
            if self.verbose > 1:
                LOG.debug("FrozenCaseInsensitiveStringSet %s: {}".format(my_set))
            result = len(my_set)
            LOG.debug("Got a length of: {}".format(result))
            self.assertEqual(result, expected_len)


# =============================================================================
if __name__ == '__main__':

    verbose = get_arg_verbose()
    if verbose is None:
        verbose = 0
    init_root_logger(verbose)

    LOG.info("Starting tests ...")

    suite = unittest.TestSuite()

    suite.addTest(TestFbCollections('test_import', verbose))
    suite.addTest(TestFbCollections('test_init_frozenset', verbose))
    suite.addTest(TestFbCollections('test_frozenset_len', verbose))

    runner = unittest.TextTestRunner(verbosity=verbose)

    result = runner.run(suite)


# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
