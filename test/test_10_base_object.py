#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@summary: Test script (and module) for unit tests on base object.

@author: Frank Brehm
@contact: frank@brehm-online.com
@copyright: © 2025 Frank Brehm, Berlin
@license: GPL3
"""

import logging
import os
import sys
from pathlib import Path

try:
    import unittest2 as unittest
except ImportError:
    import unittest

libdir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, libdir)

from general import FbToolsTestcase, get_arg_verbose, init_root_logger

LOG = logging.getLogger('test_base_object')


# =============================================================================
class TestFbBaseObject(FbToolsTestcase):
    """Testcase for unit tests on base object."""

    # -------------------------------------------------------------------------
    def setUp(self):
        """Execute this on seting up before calling each particular test method."""
        if self.verbose >= 1:
            print()

    # -------------------------------------------------------------------------
    def test_import(self):
        """Test importing module fb_tools.obj."""
        LOG.info('Testing import of fb_tools.obj ...')
        import fb_tools.obj
        LOG.debug('Version of fb_tools.obj: {!r}'.format(fb_tools.obj.__version__))

    # -------------------------------------------------------------------------
    def test_object(self):
        """Test instantiating a simple object."""
        LOG.info('Testing init of a simple object.')

        from fb_tools.obj import FbGenericBaseObject, FbBaseObject

        with self.assertRaises(TypeError) as cm:
            gen_obj = FbGenericBaseObject()
            LOG.error('This message should never be visible: {!r}'.format(gen_obj))
        e = cm.exception
        LOG.debug('{cls} raised on instantiate a FbGenericBaseObject: {err}'.format(
            cls=e.__class__.__name__, err=e))

        obj = FbBaseObject(
            appname='test_base_object',
            verbose=1,
        )
        LOG.debug('FbBaseObject %%r: {!r}'.format(obj))
        LOG.debug('FbBaseObject %%s: {}'.format(obj))

    # -------------------------------------------------------------------------
    def test_verbose(self):
        """Test wrong verbose values."""
        LOG.info('Testing wrong verbose values.')

        from fb_tools.obj import FbBaseObject

        wrong_values = ('hh', -2)

        for value in wrong_values:
            LOG.debug('Testing verbose value {!r} ...'.format(value))
            obj = None
            with self.assertRaises(ValueError) as cm:
                obj = FbBaseObject(appname='test_base_object', verbose=value)
                LOG.error('This message should never be visible: {!r}'.format(obj))
            e = cm.exception
            LOG.debug('{cls} raised on verbose = {val!r}: {err}'.format(
                cls=e.__class__.__name__, val=value, err=e))

    # -------------------------------------------------------------------------
    def test_basedir(self):
        """Test wrong values for base_dir."""
        LOG.info('Testing wrong values for base_dir.')

        wrong_values = ('/blablub', '/etc/passwd')
        from fb_tools.obj import FbBaseObject

        for value in wrong_values:
            base_path = Path(value)
            LOG.debug('Testing wrong base_dir {!r} ...'.format(value))
            obj = FbBaseObject(appname='test_base_object', base_dir=value)
            if self.verbose > 1:
                LOG.debug('Created base object:\n{}'.format(obj))
            self.assertNotEqual(base_path, obj.base_dir)

    # -------------------------------------------------------------------------
    def test_as_dict1(self):
        """Test obj.as_dict() simple."""
        LOG.info('Testing obj.as_dict() #1 - simple')

        from fb_tools.obj import FbBaseObject

        obj = FbBaseObject(appname='test_base_object', verbose=1)

        di = obj.as_dict()
        LOG.debug('Got FbBaseObject.as_dict(): {!r}'.format(di))
        self.assertIsInstance(di, dict)

    # -------------------------------------------------------------------------
    def test_as_dict2(self):
        """Test obj.as_dict() stacked."""
        LOG.info('Testing obj.as_dict() #2 - stacked')

        from fb_tools.obj import FbBaseObject

        obj = FbBaseObject(appname='test_base_object', verbose=1)
        obj.obj2 = FbBaseObject(appname='test_base_object2', verbose=1)

        di = obj.as_dict()
        LOG.debug('Got FbBaseObject.as_dict(): {!r}'.format(di))
        self.assertIsInstance(di, dict)
        self.assertIsInstance(obj.obj2.as_dict(), dict)

    # -------------------------------------------------------------------------
    def test_as_dict3(self):
        """Test obj.as_dict() for typecasting to str."""
        LOG.info('Testing obj.as_dict() #3 - typecasting to str')

        from fb_tools.obj import FbBaseObject

        obj = FbBaseObject(appname='test_base_object', verbose=self.verbose)
        obj.obj2 = FbBaseObject(appname='test_base_object2', verbose=self.verbose)

        out = str(obj)
        self.assertIsInstance(out, str)
        LOG.debug('Got str(FbBaseObject):\n{}'.format(out))

    # -------------------------------------------------------------------------
    def test_as_dict_short(self):
        """Test obj.as_dict() stacked and short."""
        LOG.info('Testing obj.as_dict() #4 - stacked and short.')

        from fb_tools.obj import FbBaseObject

        obj = FbBaseObject(appname='test_base_object', verbose=self.verbose)
        obj.obj2 = FbBaseObject(appname='test_base_object2', verbose=self.verbose)

        di = obj.as_dict(short=True)
        LOG.debug('Got FbBaseObject.as_dict(): {!r}'.format(di))
        self.assertIsInstance(di, dict)
        self.assertIsInstance(obj.obj2.as_dict(), dict)


# =============================================================================
if __name__ == '__main__':

    verbose = get_arg_verbose()
    if verbose is None:
        verbose = 0
    init_root_logger(verbose)

    LOG.info('Starting tests ...')

    suite = unittest.TestSuite()

    suite.addTest(TestFbBaseObject('test_import', verbose))
    suite.addTest(TestFbBaseObject('test_object', verbose))
    suite.addTest(TestFbBaseObject('test_verbose', verbose))
    suite.addTest(TestFbBaseObject('test_basedir', verbose))
    suite.addTest(TestFbBaseObject('test_as_dict1', verbose))
    suite.addTest(TestFbBaseObject('test_as_dict2', verbose))
    suite.addTest(TestFbBaseObject('test_as_dict3', verbose))
    suite.addTest(TestFbBaseObject('test_as_dict_short', verbose))

    runner = unittest.TextTestRunner(verbosity=verbose)

    result = runner.run(suite)


# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
