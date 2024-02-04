#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
@author: Frank Brehm
@contact: frank@brehm-online.com
@copyright: © 2024 Frank Brehm, Berlin
@license: GPL3
@summary: test script (and module) for unit tests on base object
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

LOG = logging.getLogger('test_base_object')


# =============================================================================
class TestFbBaseObject(FbToolsTestcase):

    # -------------------------------------------------------------------------
    def setUp(self):
        pass

    # -------------------------------------------------------------------------
    def test_import(self):

        LOG.info("Testing import of fb_tools.obj ...")
        import fb_tools.obj
        LOG.debug("Version of fb_tools.obj: {!r}".format(fb_tools.obj.__version__))

    # -------------------------------------------------------------------------
    def test_object(self):

        LOG.info("Testing init of a simple object.")

        from fb_tools.obj import FbGenericBaseObject, FbBaseObject

        with self.assertRaises(TypeError) as cm:
            gen_obj = FbGenericBaseObject()                         # noqa
        e = cm.exception
        LOG.debug("TypeError raised on instantiate a FbGenericBaseObject: %s", str(e))

        obj = FbBaseObject(
            appname='test_base_object',
            verbose=1,
        )
        LOG.debug("FbBaseObject %%r: %r", obj)
        LOG.debug("FbBaseObject %%s: %s", str(obj))

    # -------------------------------------------------------------------------
    def test_verbose1(self):

        LOG.info("Testing wrong verbose values #1.")

        from fb_tools.obj import FbBaseObject

        v = 'hh'
        obj = None

        with self.assertRaises(ValueError) as cm:
            obj = FbBaseObject(appname='test_base_object', verbose=v)   # noqa
        e = cm.exception
        LOG.debug("ValueError raised on verbose = %r: %s", v, str(e))

    # -------------------------------------------------------------------------
    def test_verbose2(self):

        LOG.info("Testing wrong verbose values #2.")

        from fb_tools.obj import FbBaseObject

        v = -2
        obj = None

        with self.assertRaises(ValueError) as cm:
            obj = FbBaseObject(appname='test_base_object', verbose=v)   # noqa
        e = cm.exception
        LOG.debug("ValueError raised on verbose = %r: %s", v, str(e))

    # -------------------------------------------------------------------------
    def test_basedir1(self):

        bd = '/blablub'
        LOG.info("Testing #1 wrong basedir: %r", bd)

        from fb_tools.obj import FbBaseObject

        obj = FbBaseObject(appname='test_base_object', base_dir=bd)     # noqa

    # -------------------------------------------------------------------------
    def test_basedir2(self):

        bd = '/etc/passwd'
        LOG.info("Testing #2 wrong basedir: %r", bd)

        from fb_tools.obj import FbBaseObject

        obj = FbBaseObject(appname='test_base_object', base_dir=bd)     # noqa

    # -------------------------------------------------------------------------
    def test_as_dict1(self):

        LOG.info("Testing obj.as_dict() #1 - simple")

        from fb_tools.obj import FbBaseObject

        obj = FbBaseObject(appname='test_base_object', verbose=1)

        di = obj.as_dict()
        LOG.debug("Got FbBaseObject.as_dict(): %r", di)
        self.assertIsInstance(di, dict)

    # -------------------------------------------------------------------------
    def test_as_dict2(self):

        LOG.info("Testing obj.as_dict() #2 - stacked")

        from fb_tools.obj import FbBaseObject

        obj = FbBaseObject(appname='test_base_object', verbose=1)
        obj.obj2 = FbBaseObject(appname='test_base_object2', verbose=1)

        di = obj.as_dict()
        LOG.debug("Got FbBaseObject.as_dict(): %r", di)
        self.assertIsInstance(di, dict)
        self.assertIsInstance(obj.obj2.as_dict(), dict)

    # -------------------------------------------------------------------------
    def test_as_dict3(self):

        LOG.info("Testing obj.as_dict() #3 - typecasting to str")

        from fb_tools.obj import FbBaseObject

        obj = FbBaseObject(appname='test_base_object', verbose=1)
        obj.obj2 = FbBaseObject(appname='test_base_object2', verbose=1)

        out = str(obj)
        self.assertIsInstance(out, str)
        LOG.debug("Got str(FbBaseObject): %s", out)

    # -------------------------------------------------------------------------
    def test_as_dict_short(self):

        LOG.info("Testing obj.as_dict() #4 - stacked and short")

        from fb_tools.obj import FbBaseObject

        obj = FbBaseObject(appname='test_base_object', verbose=1)
        obj.obj2 = FbBaseObject(appname='test_base_object2', verbose=1)

        di = obj.as_dict(short=True)
        LOG.debug("Got FbBaseObject.as_dict(): %r", di)
        self.assertIsInstance(di, dict)
        self.assertIsInstance(obj.obj2.as_dict(), dict)


# =============================================================================
if __name__ == '__main__':

    verbose = get_arg_verbose()
    if verbose is None:
        verbose = 0
    init_root_logger(verbose)

    LOG.info("Starting tests ...")

    suite = unittest.TestSuite()

    suite.addTest(TestFbBaseObject('test_import', verbose))
    suite.addTest(TestFbBaseObject('test_object', verbose))
    suite.addTest(TestFbBaseObject('test_verbose1', verbose))
    suite.addTest(TestFbBaseObject('test_verbose2', verbose))
    suite.addTest(TestFbBaseObject('test_basedir1', verbose))
    suite.addTest(TestFbBaseObject('test_basedir2', verbose))
    suite.addTest(TestFbBaseObject('test_as_dict1', verbose))
    suite.addTest(TestFbBaseObject('test_as_dict2', verbose))
    suite.addTest(TestFbBaseObject('test_as_dict3', verbose))
    suite.addTest(TestFbBaseObject('test_as_dict_short', verbose))

    runner = unittest.TextTestRunner(verbosity=verbose)

    result = runner.run(suite)


# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
