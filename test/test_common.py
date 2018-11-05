#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: Frank Brehm
@contact: frank@brehm-online.com
@copyright: © 2018 Frank Brehm, Berlin
@license: GPL3
@summary: test script (and module) for unit tests on common.py
"""

import os
import sys
import logging
import locale

try:
    import unittest2 as unittest
except ImportError:
    import unittest

# Setting the user’s preferred locale settings
locale.setlocale(locale.LC_ALL, '')

libdir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'lib'))
sys.path.insert(0, libdir)

from general import FbToolsTestcase, get_arg_verbose, init_root_logger

log = logging.getLogger('test_common')

# =============================================================================
class TestFbCommon(FbToolsTestcase):

    # -------------------------------------------------------------------------
    def setUp(self):
        pass

    # -------------------------------------------------------------------------
    def test_import(self):

        log.info("Testing import of fb_tools.common ...")
        import fb_tools.common                                  # noqa

    # -------------------------------------------------------------------------
    def test_to_unicode(self):

        log.info("Testing to_unicode() ...")

        from fb_tools.common import to_unicode

        data = []
        data.append((None, None))
        data.append((1, 1))

        if sys.version_info[0] <= 2:
            data.append((u'a', u'a'))
            data.append(('a', u'a'))
        else:
            data.append(('a', 'a'))
            data.append((b'a', 'a'))

        for pair in data:

            src = pair[0]
            tgt = pair[1]
            result = to_unicode(src)
            log.debug(
                "Testing to_unicode(%r) => %r, result %r",
                src, tgt, result)

            if sys.version_info[0] <= 2:
                if isinstance(src, (str, unicode)):
                    self.assertIsInstance(result, unicode)
                else:
                    self.assertNotIsInstance(result, (str, unicode))
            else:
                if isinstance(src, (str, bytes)):
                    self.assertIsInstance(result, str)
                else:
                    self.assertNotIsInstance(result, (str, bytes))

            self.assertEqual(tgt, result)

    # -------------------------------------------------------------------------
    def test_to_utf8(self):

        log.info("Testing to_utf8() ...")

        from fb_tools.common import to_utf8

        data = []
        data.append((None, None))
        data.append((1, 1))

        if sys.version_info[0] <= 2:
            data.append((u'a', 'a'))
            data.append(('a', 'a'))
        else:
            data.append(('a', b'a'))
            data.append((b'a', b'a'))

        for pair in data:

            src = pair[0]
            tgt = pair[1]
            result = to_utf8(src)
            log.debug(
                "Testing to_utf8(%r) => %r, result %r",
                src, tgt, result)

            if sys.version_info[0] <= 2:
                if isinstance(src, (str, unicode)):
                    self.assertIsInstance(result, str)
                else:
                    self.assertNotIsInstance(result, (str, unicode))
            else:
                if isinstance(src, (str, bytes)):
                    self.assertIsInstance(result, bytes)
                else:
                    self.assertNotIsInstance(result, (str, bytes))

            self.assertEqual(tgt, result)

    # -------------------------------------------------------------------------
    def test_to_str(self):

        log.info("Testing to_str() ...")

        from fb_tools.common import to_str

        data = []
        data.append((None, None))
        data.append((1, 1))

        if sys.version_info[0] <= 2:
            data.append((u'a', 'a'))
            data.append(('a', 'a'))
        else:
            data.append(('a', 'a'))
            data.append((b'a', 'a'))

        for pair in data:

            src = pair[0]
            tgt = pair[1]
            result = to_str(src)
            log.debug(
                "Testing to_str(%r) => %r, result %r",
                src, tgt, result)

            if sys.version_info[0] <= 2:
                if isinstance(src, (str, unicode)):
                    self.assertIsInstance(result, str)
                else:
                    self.assertNotIsInstance(result, (str, unicode))
            else:
                if isinstance(src, (str, bytes)):
                    self.assertIsInstance(result, str)
                else:
                    self.assertNotIsInstance(result, (str, bytes))

            self.assertEqual(tgt, result)

# =============================================================================

if __name__ == '__main__':

    verbose = get_arg_verbose()
    if verbose is None:
        verbose = 0
    init_root_logger(verbose)

    log.info("Starting tests ...")

    suite = unittest.TestSuite()

    suite.addTest(TestFbCommon('test_import', verbose))
    suite.addTest(TestFbCommon('test_to_unicode', verbose))
    suite.addTest(TestFbCommon('test_to_utf8', verbose))
    suite.addTest(TestFbCommon('test_to_str', verbose))
#    suite.addTest(TestFbCommon('test_human2mbytes', verbose))
#    suite.addTest(TestFbCommon('test_human2mbytes_l10n', verbose))
#    suite.addTest(TestFbCommon('test_bytes2human', verbose))
#    suite.addTest(TestFbCommon('test_to_bool', verbose))

    runner = unittest.TextTestRunner(verbosity=verbose)

    result = runner.run(suite)

# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 fileencoding=utf-8
