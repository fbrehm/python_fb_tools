#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@summary: Test script (and module) for unit tests on descriptor classes.

@author: Frank Brehm
@contact: frank@brehm-online.com
@copyright: © 2018 - 2026 Frank Brehm, Berlin
@license: LGPL3
"""

import logging
import os
import sys

try:
    import unittest2 as unittest
except ImportError:
    import unittest

libdir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, libdir)

from general import FbToolsTestcase, get_arg_verbose, init_root_logger

LOG = logging.getLogger("test_descriptors")


# =============================================================================
class TestDescriptors(FbToolsTestcase):
    """Testcase for unit tests on module fb_tools.descriptors and its descriptor classes."""

    # -------------------------------------------------------------------------
    def setUp(self):
        """Execute this on setting up before calling each particular test method."""
        if self.verbose >= 1:
            print()

    # -------------------------------------------------------------------------
    def tearDown(self):
        """Tear down routine for calling each particular test method."""
        # LOG.debug("Current loaded modules:\n" + pp(sys.modules))
        pass

    # -------------------------------------------------------------------------
    def test_import(self):
        """Test import of fb_tools.mailaddress."""
        LOG.info(self.get_method_doc())

        import fb_tools.descriptors

        LOG.debug("Version of fb_tools.descriptors: {!r}".format(fb_tools.descriptors.__version__))

    # -------------------------------------------------------------------------
    def test_boolean_descriptor(self):
        """Test object with a BooleanDescriptor."""
        LOG.info(self.get_method_doc())

        from fb_tools.descriptors import BooleanDescriptor

        LOG.debug("Testing an BooleanDescriptor.")

        class TestClass:

            test_bool = BooleanDescriptor(name="test_bool")

            def __init__(myself):
                """Init TestClass."""
                myself.test_bool = False

        test_obj = TestClass()

        LOG.debug(f"test_obj.test_bool: {test_obj.test_bool!r}")
        self.assertEqual(test_obj.test_bool, False)
        self.assertFalse(test_obj.test_bool)

        if self.verbose > 1:
            print()
        LOG.debug("Test setting to None.")
        with self.assertRaises((TypeError, ValueError)) as cm:
            test_obj.test_bool = None
        e = cm.exception
        LOG.debug("{cls} raised: {e}".format(cls=e.__class__.__name__, e=e))

        LOG.debug("Testing an BooleanDescriptor, which may be set to None.")

        class TestClassWithNone:

            test_bool = BooleanDescriptor(name="test_bool", maybe_none=True)

            def __init__(myself):
                """Init TestClassWithNone."""
                myself.test_bool = None

        test_obj_none = TestClassWithNone()
        LOG.debug(f"test_obj_none.test_bool: {test_obj_none.test_bool!r}")
        self.assertIsNone(test_obj_none.test_bool)

        if self.verbose > 1:
            print()
        LOG.debug("Test setting true values ...")
        true_values = (True, 1, 1.0, -1, "yes", "YES", "Yes", "y", "true", "True", "On", "Uhu")

        for value in true_values:
            LOG.debug(f"Test setting to {value!r} ...")
            test_obj.test_bool = value
            LOG.debug(f"test_obj.test_bool: {test_obj.test_bool!r}")
            self.assertTrue(test_obj.test_bool)

        if self.verbose > 1:
            print()
        LOG.debug("Test setting false values ...")
        true_values = (False, 0, 0.0, "no", "NO", "No", "n", "false", "False", "Off")

        for value in true_values:
            LOG.debug(f"Test setting to {value!r} ...")
            test_obj.test_bool = value
            LOG.debug(f"test_obj.test_bool: {test_obj.test_bool!r}")
            self.assertFalse(test_obj.test_bool)

    # -------------------------------------------------------------------------
    def test_integer_descriptor(self):
        """Test object with a IntegerDescriptor."""
        LOG.info(self.get_method_doc())

        from fb_tools.descriptors import IntegerDescriptor

        LOG.debug("Testing an IntegerDescriptor.")

        class TestClass:

            test_int = IntegerDescriptor(name="test_int")

            def __init__(myself):
                """Init TestClass."""
                myself.test_int = 1

        test_obj = TestClass()

        LOG.debug(f"test_obj.test_int: {test_obj.test_int}")
        self.assertEqual(test_obj.test_int, 1)

        LOG.debug("Test setting test_obj.test_int ...")
        test_obj.test_int = 2
        LOG.debug(f"test_obj.test_int: {test_obj.test_int}")
        self.assertEqual(test_obj.test_int, 2)

        if self.verbose > 1:
            print()
        LOG.debug("Test wrong values for IntegerDescriptor ...")
        wrong_values = (None, 'bla', print, [])
        for wrong_value in wrong_values:
            LOG.debug(f"Testing wrong value {wrong_value!r} ...")
            with self.assertRaises((TypeError, ValueError)) as cm:
                test_obj.test_int = wrong_value
            e = cm.exception
            LOG.debug("{cls} raised: {e}".format(cls=e.__class__.__name__, e=e))

        if self.verbose > 1:
            print()
        LOG.debug("Testing an IntegerDescriptor, which may be set to None.")

        class TestClass1:

            test_int = IntegerDescriptor(name="test_int", maybe_none=True)

            def __init__(myself):
                """Init TestClass1."""
                myself.test_int = None

        test_obj1 = TestClass1()

        LOG.debug(f"test_obj1.test_int: {test_obj1.test_int!r}")
        self.assertIsNone(test_obj1.test_int)

        test_obj1.test_int = 1
        LOG.debug(f"test_obj1.test_int: {test_obj1.test_int!r}")
        self.assertEqual(test_obj1.test_int, 1)

        test_obj1.test_int = None
        LOG.debug(f"test_obj1.test_int: {test_obj1.test_int!r}")
        self.assertIsNone(test_obj1.test_int)

        if self.verbose > 1:
            print()
        LOG.debug("Testing an IntegerDescriptor with limits for its value.")

        LOG.debug("Testing an IntegerDescriptor with wrong set limits.")
        with self.assertRaises((TypeError, ValueError)) as cm:
            class TestClass2:

                test_int = IntegerDescriptor(name="test_int", lower_limit="bla")

                def __init__(myself):
                    """Init TestClass2."""
                    myself.test_int = 1

        e = cm.exception
        LOG.debug("{cls} raised: {e}".format(cls=e.__class__.__name__, e=e))

        with self.assertRaises((TypeError, ValueError)) as cm:
            class TestClass3:

                test_int = IntegerDescriptor(name="test_int", upper_limit={})

                def __init__(myself):
                    """Init TestClass3."""
                    myself.test_int = 1

        e = cm.exception
        LOG.debug("{cls} raised: {e}".format(cls=e.__class__.__name__, e=e))

        with self.assertRaises((TypeError, ValueError)) as cm:
            class TestClass4:

                test_int = IntegerDescriptor(name="test_int", lower_limit=10, upper_limit=5)

                def __init__(myself):
                    """Init TestClass4."""
                    myself.test_int = 1

        e = cm.exception
        LOG.debug("{cls} raised: {e}".format(cls=e.__class__.__name__, e=e))

        class TestClass5:

            test_int = IntegerDescriptor(name="test_int", lower_limit=1, upper_limit=5)

            def __init__(myself):
                """Init TestClass2."""
                myself.test_int = 3

        test_obj5 = TestClass5()
        LOG.debug(f"test_obj5.test_int: {test_obj5.test_int}")
        self.assertEqual(test_obj5.test_int, 3)

        test_obj5.test_int = 1
        LOG.debug(f"test_obj5.test_int: {test_obj5.test_int}")
        self.assertEqual(test_obj5.test_int, 1)
        test_obj5.test_int = 5
        LOG.debug(f"test_obj5.test_int: {test_obj5.test_int}")
        self.assertEqual(test_obj5.test_int, 5)

        wrong_values = (0, 6)
        for wrong_value in wrong_values:
            LOG.debug(f"Testing wrong value {wrong_value!r} ...")
            with self.assertRaises((TypeError, ValueError)) as cm:
                test_obj5.test_int = wrong_value
            e = cm.exception
            LOG.debug("{cls} raised: {e}".format(cls=e.__class__.__name__, e=e))


# =============================================================================
if __name__ == "__main__":

    verbose = get_arg_verbose()
    if verbose is None:
        verbose = 0
    init_root_logger(verbose)

    LOG.info("Starting tests ...")

    suite = unittest.TestSuite()

    suite.addTest(TestDescriptors("test_import", verbose))
    suite.addTest(TestDescriptors("test_boolean_descriptor", verbose))
    suite.addTest(TestDescriptors("test_integer_descriptor", verbose))

    runner = unittest.TextTestRunner(verbosity=verbose)

    result = runner.run(suite)


# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
