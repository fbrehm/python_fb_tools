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

        LOG.debug("Trying to add add a value to a FrozenCaseInsensitiveStringSet ...")
        with self.assertRaises(AttributeError) as cm:
            my_set.add('bla')
        e = cm.exception
        msg = ("AttributeError raised on trying to add a value to a "
                "FrozenCaseInsensitiveStringSet object: {}").format(e)
        LOG.debug(msg)

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

    # -------------------------------------------------------------------------
    def test_frozenset_bool(self):

        LOG.info("Testing bool() of a FrozenCaseInsensitiveStringSet object.")

        from fb_tools.collections import FrozenCaseInsensitiveStringSet

        test_tuples = (
            (None, False),
            ([], False),
            (['a'], True),
            (['a', 'b'], True),
        )

        for test_tuple in test_tuples:
            src = test_tuple[0]
            expected_bool = test_tuple[1]
            LOG.debug("Testing bool() of a FrozenCaseInsensitiveStringSet from {!r}.".format(src))
            my_set = FrozenCaseInsensitiveStringSet(src)
            if self.verbose > 1:
                LOG.debug("FrozenCaseInsensitiveStringSet %s: {}".format(my_set))
            result = bool(my_set)
            LOG.debug("Got boolean of: {}".format(result))
            self.assertEqual(result, expected_bool)

    # -------------------------------------------------------------------------
    def test_frozenset_operator_le(self):

        LOG.info("Testing operator le ('<=', issubset()) of a "
            "FrozenCaseInsensitiveStringSet object.")

        from fb_tools.collections import FrozenCaseInsensitiveStringSet
        from fb_tools.collections import WrongCompareSetClassError

        my_set = FrozenCaseInsensitiveStringSet(['a', 'b'])

        test_tuples = (
            (['a', 'b'], True),
            (['A', 'b'], True),
            (['a', 'B'], True),
            (['a'], False),
            (['a', 'b', 'c'], True),
            (['b', 'c'], False),
        )

        LOG.debug("Trying to compare with a wrong partner ...")
        with self.assertRaises(WrongCompareSetClassError) as cm:
            if my_set <= ['a']:
                LOG.debug("Bla")
        e = cm.exception
        msg = "WrongCompareSetClassError on comparing with a wrong object: {}".format(e)
        LOG.debug(msg)

        for test_tuple in test_tuples:
            src = test_tuple[0]
            expected = test_tuple[1]
            test_set = FrozenCaseInsensitiveStringSet(src)
            msg = "Testing, whether set {left!r} is a subset of {right!r}.".format(
                left=my_set.as_list(), right=test_set.as_list())
            LOG.debug(msg)
            result = False
            if my_set <= test_set:
                result = True
            LOG.debug("Result: {r} (expected: {e}).".format(r=result, e=expected))
            self.assertEqual(result, expected)

    # -------------------------------------------------------------------------
    def test_frozenset_operator_lt(self):

        LOG.info("Testing operator lt ('<') of a FrozenCaseInsensitiveStringSet object.")

        from fb_tools.collections import FrozenCaseInsensitiveStringSet
        from fb_tools.collections import WrongCompareSetClassError

        my_set = FrozenCaseInsensitiveStringSet(['a', 'b'])

        test_tuples = (
            (['a', 'b'], False),
            (['A', 'b'], False),
            (['a', 'B'], False),
            (['a'], False),
            (['a', 'b', 'c'], True),
            (['b', 'c'], False),
        )

        LOG.debug("Trying to compare with a wrong partner ...")
        with self.assertRaises(WrongCompareSetClassError) as cm:
            if my_set < ['a']:
                LOG.debug("Bla")
        e = cm.exception
        msg = "WrongCompareSetClassError on comparing with a wrong object: {}".format(e)
        LOG.debug(msg)

        for test_tuple in test_tuples:
            src = test_tuple[0]
            expected = test_tuple[1]
            test_set = FrozenCaseInsensitiveStringSet(src)
            msg = "Testing, whether set {left!r} is a real subset of {right!r}.".format(
                left=my_set.as_list(), right=test_set.as_list())
            LOG.debug(msg)
            result = False
            if my_set < test_set:
                result = True
            LOG.debug("Result: {r} (expected: {e}).".format(r=result, e=expected))
            self.assertEqual(result, expected)

    # -------------------------------------------------------------------------
    def test_frozenset_operator_eq(self):

        LOG.info("Testing operator eq ('==') of a FrozenCaseInsensitiveStringSet object.")

        from fb_tools.collections import FrozenCaseInsensitiveStringSet
        from fb_tools.collections import WrongCompareSetClassError

        my_set = FrozenCaseInsensitiveStringSet(['a', 'b'])

        test_tuples = (
            (['a', 'b'], True),
            (['A', 'b'], True),
            (['a', 'B'], True),
            (['a'], False),
            (['a', 'b', 'c'], False),
            (['b', 'c'], False),
        )

        LOG.debug("Trying to compare with a wrong partner ...")
        result = False
        if my_set == ['a', 'b']:
            result = True
        LOG.debug("Result: {r} (expected: {e}).".format(r=result, e=False))
        self.assertEqual(result, False)

        for test_tuple in test_tuples:
            src = test_tuple[0]
            expected = test_tuple[1]
            test_set = FrozenCaseInsensitiveStringSet(src)
            msg = "Testing, whether set {left!r} is equal to {right!r}.".format(
                left=my_set.as_list(), right=test_set.as_list())
            LOG.debug(msg)
            result = False
            if my_set == test_set:
                result = True
            LOG.debug("Result: {r} (expected: {e}).".format(r=result, e=expected))
            self.assertEqual(result, expected)

    # -------------------------------------------------------------------------
    def test_frozenset_operator_ne(self):

        LOG.info("Testing operator ne ('!=') of a FrozenCaseInsensitiveStringSet object.")

        from fb_tools.collections import FrozenCaseInsensitiveStringSet
        from fb_tools.collections import WrongCompareSetClassError

        my_set = FrozenCaseInsensitiveStringSet(['a', 'b'])

        test_tuples = (
            (['a', 'b'], False),
            (['A', 'b'], False),
            (['a', 'B'], False),
            (['a'], True),
            (['a', 'b', 'c'], True),
            (['b', 'c'], True),
        )

        LOG.debug("Trying to compare with a wrong partner ...")
        result = True
        if my_set != ['a']:
            result = False
        LOG.debug("Result: {r} (expected: {e}).".format(r=result, e=False))
        self.assertEqual(result, False)

        for test_tuple in test_tuples:
            src = test_tuple[0]
            expected = test_tuple[1]
            test_set = FrozenCaseInsensitiveStringSet(src)
            msg = "Testing, whether set {left!r} is not equal to {right!r}.".format(
                left=my_set.as_list(), right=test_set.as_list())
            LOG.debug(msg)
            result = False
            if my_set != test_set:
                result = True
            LOG.debug("Result: {r} (expected: {e}).".format(r=result, e=expected))
            self.assertEqual(result, expected)

    # -------------------------------------------------------------------------
    def test_frozenset_operator_gt(self):

        LOG.info("Testing operator gt ('>') of a "
            "FrozenCaseInsensitiveStringSet object.")

        from fb_tools.collections import FrozenCaseInsensitiveStringSet
        from fb_tools.collections import WrongCompareSetClassError

        my_set = FrozenCaseInsensitiveStringSet(['a', 'b'])

        test_tuples = (
            (['a', 'b'], False),
            (['A', 'b'], False),
            (['a', 'B'], False),
            (['a'], True),
            (['a', 'b', 'c'], False),
            (['b', 'c'], False),
        )

        LOG.debug("Trying to compare with a wrong partner ...")
        with self.assertRaises(WrongCompareSetClassError) as cm:
            if my_set > ['a']:
                LOG.debug("Bla")
        e = cm.exception
        msg = "WrongCompareSetClassError on comparing with a wrong object: {}".format(e)
        LOG.debug(msg)

        for test_tuple in test_tuples:
            src = test_tuple[0]
            expected = test_tuple[1]
            test_set = FrozenCaseInsensitiveStringSet(src)
            msg = "Testing, whether set {right!r} is a real subset of {left!r}.".format(
                left=my_set.as_list(), right=test_set.as_list())
            LOG.debug(msg)
            result = False
            if my_set > test_set:
                result = True
            LOG.debug("Result: {r} (expected: {e}).".format(r=result, e=expected))
            self.assertEqual(result, expected)

    # -------------------------------------------------------------------------
    def test_frozenset_operator_ge(self):

        LOG.info("Testing operator ge ('>=') of a FrozenCaseInsensitiveStringSet object.")

        from fb_tools.collections import FrozenCaseInsensitiveStringSet
        from fb_tools.collections import WrongCompareSetClassError

        my_set = FrozenCaseInsensitiveStringSet(['a', 'b'])

        test_tuples = (
            (['a', 'b'], True),
            (['A', 'b'], True),
            (['a', 'B'], True),
            (['a'], True),
            (['a', 'b', 'c'], False),
            (['b', 'c'], False),
        )

        LOG.debug("Trying to compare with a wrong partner ...")
        with self.assertRaises(WrongCompareSetClassError) as cm:
            if my_set >= ['a']:
                LOG.debug("Bla")
        e = cm.exception
        msg = "WrongCompareSetClassError on comparing with a wrong object: {}".format(e)
        LOG.debug(msg)

        for test_tuple in test_tuples:
            src = test_tuple[0]
            expected = test_tuple[1]
            test_set = FrozenCaseInsensitiveStringSet(src)
            msg = "Testing, whether set {right!r} is a subset of {left!r}.".format(
                left=my_set.as_list(), right=test_set.as_list())
            LOG.debug(msg)
            result = False
            if my_set >= test_set:
                result = True
            LOG.debug("Result: {r} (expected: {e}).".format(r=result, e=expected))
            self.assertEqual(result, expected)

    # -------------------------------------------------------------------------
    def test_frozenset_operator_or(self):

        LOG.info("Testing operator ge ('|', union()) of a FrozenCaseInsensitiveStringSet object.")

        from fb_tools.collections import FrozenCaseInsensitiveStringSet
        from fb_tools.collections import WrongCompareSetClassError

        set_one = FrozenCaseInsensitiveStringSet(['a', 'B', 'c'])
        set_two = FrozenCaseInsensitiveStringSet(['b', 'c', 'e'])
        set_three = FrozenCaseInsensitiveStringSet(['C', 'd', 'f'])

        set_expected = FrozenCaseInsensitiveStringSet(['a', 'B', 'c', 'd', 'e', 'f'])

        LOG.debug("Trying to union with a wrong partner ...")
        with self.assertRaises(WrongCompareSetClassError) as cm:
            my_set = set_one | ['a']
            LOG.debug('bla')
        e = cm.exception
        msg = "WrongCompareSetClassError on a union with a wrong object: {}".format(e)
        LOG.debug(msg)

        msg = "Making a union of frozen sets {one!r}, {two!r} and {three!r}."
        msg = msg.format(one=set_one.as_list(), two=set_two.as_list(), three=set_three.as_list())
        LOG.debug(msg)
        set_result = set_one | set_two | set_three
        msg = "Got a union result {res!r} (expecting: {exp!r}).".format(
            res=set_result.as_list(), exp=set_expected.as_list())
        LOG.debug(msg)
        self.assertEqual(set_result.as_list(), set_expected.as_list())

    # -------------------------------------------------------------------------
    def test_frozenset_operator_and(self):

        LOG.info("Testing operator and ('&', intersection()) of a "
                "FrozenCaseInsensitiveStringSet object.")

        from fb_tools.collections import FrozenCaseInsensitiveStringSet
        from fb_tools.collections import WrongCompareSetClassError

        set_one = FrozenCaseInsensitiveStringSet(['a', 'B', 'c', 'd', 'E', 'f', 'G'])
        set_two = FrozenCaseInsensitiveStringSet(['a', 'b', 'd', 'e', 'h'])
        set_three = FrozenCaseInsensitiveStringSet(['A', 'b', 'C', 'd', 'f', 'g'])

        set_expected = FrozenCaseInsensitiveStringSet(['a', 'B', 'd'])

        LOG.debug("Trying to intersection with a wrong partner ...")
        with self.assertRaises(WrongCompareSetClassError) as cm:
            my_set = set_one & ['a']
            LOG.debug('bla')
        e = cm.exception
        msg = "WrongCompareSetClassError on a union with a wrong object: {}".format(e)
        LOG.debug(msg)

        msg = "Making an intersection of frozen sets {one!r}, {two!r} and {three!r}."
        msg = msg.format(one=set_one.as_list(), two=set_two.as_list(), three=set_three.as_list())
        LOG.debug(msg)
        set_result = set_one & set_two & set_three
        msg = "Got an intersection result {res!r} (expecting: {exp!r}).".format(
            res=set_result.as_list(), exp=set_expected.as_list())
        LOG.debug(msg)
        self.assertEqual(set_result.as_list(), set_expected.as_list())


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
    suite.addTest(TestFbCollections('test_frozenset_bool', verbose))
    suite.addTest(TestFbCollections('test_frozenset_operator_le', verbose))
    suite.addTest(TestFbCollections('test_frozenset_operator_lt', verbose))
    suite.addTest(TestFbCollections('test_frozenset_operator_eq', verbose))
    suite.addTest(TestFbCollections('test_frozenset_operator_ne', verbose))
    suite.addTest(TestFbCollections('test_frozenset_operator_gt', verbose))
    suite.addTest(TestFbCollections('test_frozenset_operator_ge', verbose))
    suite.addTest(TestFbCollections('test_frozenset_operator_or', verbose))
    suite.addTest(TestFbCollections('test_frozenset_operator_and', verbose))

    runner = unittest.TextTestRunner(verbosity=verbose)

    result = runner.run(suite)


# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
