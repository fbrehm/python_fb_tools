#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: Frank Brehm
@contact: frank@brehm-online.com
@copyright: © 2019 Frank Brehm, Berlin
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

LOG = logging.getLogger('test_common')


# =============================================================================
class TestFbCommon(FbToolsTestcase):

    # -------------------------------------------------------------------------
    def setUp(self):
        pass

    # -------------------------------------------------------------------------
    def test_import(self):

        LOG.info("Testing import of fb_tools.common ...")
        import fb_tools.common                                          # noqa

    # -------------------------------------------------------------------------
    def test_to_unicode(self):

        LOG.info("Testing to_unicode() ...")

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
            LOG.debug(
                "Testing to_unicode(%r) => %r, result %r",
                src, tgt, result)

            if sys.version_info[0] <= 2:
                if isinstance(src, (str, unicode)):                     # noqa
                    self.assertIsInstance(result, unicode)              # noqa
                else:
                    self.assertNotIsInstance(result, (str, unicode))    # noqa
            else:
                if isinstance(src, (str, bytes)):
                    self.assertIsInstance(result, str)
                else:
                    self.assertNotIsInstance(result, (str, bytes))

            self.assertEqual(tgt, result)

    # -------------------------------------------------------------------------
    def test_to_utf8(self):

        LOG.info("Testing to_utf8() ...")

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
            LOG.debug(
                "Testing to_utf8(%r) => %r, result %r",
                src, tgt, result)

            if sys.version_info[0] <= 2:
                if isinstance(src, (str, unicode)):                     # noqa
                    self.assertIsInstance(result, str)
                else:
                    self.assertNotIsInstance(result, (str, unicode))    # noqa
            else:
                if isinstance(src, (str, bytes)):
                    self.assertIsInstance(result, bytes)
                else:
                    self.assertNotIsInstance(result, (str, bytes))

            self.assertEqual(tgt, result)

    # -------------------------------------------------------------------------
    def test_to_str(self):

        LOG.info("Testing to_str() ...")

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
            LOG.debug(
                "Testing to_str(%r) => %r, result %r",
                src, tgt, result)

            if sys.version_info[0] <= 2:
                if isinstance(src, (str, unicode)):                     # noqa
                    self.assertIsInstance(result, str)
                else:
                    self.assertNotIsInstance(result, (str, unicode))    # noqa
            else:
                if isinstance(src, (str, bytes)):
                    self.assertIsInstance(result, str)
                else:
                    self.assertNotIsInstance(result, (str, bytes))

            self.assertEqual(tgt, result)

    # -------------------------------------------------------------------------
    def test_human2mbytes(self):

        LOG.info("Testing human2mbytes() from fb_tools.common ...")

        from fb_tools.common import human2mbytes

        loc = locale.getlocale()    # get current locale
        encoding = loc[1]
        LOG.debug("Current locale is %r.", loc)
        german = ('de_DE', encoding)                                    # noqa

        do_switch_locales = True
        try:
            locale.setlocale(locale.LC_ALL, german)
        except Exception as e:
            LOG.warning("Got a {c}: {e}".format(c=e.__class__.__name__, e=e))
            do_switch_locales = False

        if do_switch_locales:
            LOG.debug("Setting to locale 'C' to be secure.")
            locale.setlocale(locale.LC_ALL, 'C')
            LOG.debug("Current locale is now %r.", locale.getlocale())

        test_pairs_int_si = (
            ('1048576', 1),
            ('1MiB', 1),
            ('1 MiB', 1),
            ('1 MiB', 1),
            (' 1 MiB	', 1),
            ('1.2 MiB', int(1.2)),
            ('1 GiB', 1024),
            ('1 GB', 953),
            ('1.2 GiB', int(1.2 * 1024)),
            ('102400 KB', 100),
            ('100000 KB', 97),
            ('102400 MB', int(1024 * 1000 * 1000 * 100 / 1024 / 1024)),
            ('100000 MB', int(1000 * 1000 * 1000 * 100 / 1024 / 1024)),
            ('102400 MiB', 1024 * 100),
            ('100000 MiB', 1000 * 100),
            ('102400 GB', int(1024 * 1000 * 1000 * 1000 * 100 / 1024 / 1024)),
            ('100000 GB', int(1000 * 1000 * 1000 * 1000 * 100 / 1024 / 1024)),
            ('102400 GiB', 1024 * 1024 * 100),
            ('100000 GiB', 1024 * 1000 * 100),
            ('1024 TB', int(1024 * 1000 * 1000 * 1000 * 1000 / 1024 / 1024)),
            ('1000 TB', int(1000 * 1000 * 1000 * 1000 * 1000 / 1024 / 1024)),
            ('1024 TiB', 1024 * 1024 * 1024),
            ('1000 TiB', 1024 * 1024 * 1000),
            ('1024 PB', int(1024 * 1000 * 1000 * 1000 * 1000 * 1000 / 1024 / 1024)),
            ('1000 PB', int(1000 * 1000 * 1000 * 1000 * 1000 * 1000 / 1024 / 1024)),
            ('1024 PiB', 1024 * 1024 * 1024 * 1024),
            ('1000 PiB', 1024 * 1024 * 1024 * 1000),
            ('1024 EB', int(1024 * 1000 * 1000 * 1000 * 1000 * 1000 * 1000 / 1024 / 1024)),
            ('1000 EB', int(1000 * 1000 * 1000 * 1000 * 1000 * 1000 * 1000 / 1024 / 1024)),
            ('1024 EiB', 1024 * 1024 * 1024 * 1024 * 1024),
            ('1000 EiB', 1024 * 1024 * 1024 * 1024 * 1000),
            ('1024 ZB', int(1024 * 1000 * 1000 * 1000 * 1000 * 1000 * 1000 * 1000 / 1024 / 1024)),
            ('1000 ZB', int(1000 * 1000 * 1000 * 1000 * 1000 * 1000 * 1000 * 1000 / 1024 / 1024)),
            ('1024 ZiB', 1024 * 1024 * 1024 * 1024 * 1024 * 1024),
            ('1000 ZiB', 1024 * 1024 * 1024 * 1024 * 1024 * 1000),
        )

        for pair in test_pairs_int_si:

            src = pair[0]
            expected = pair[1]
            if self.verbose > 1:
                LOG.debug("Testing human2mbytes(%r) => %d", src, expected)
            result = human2mbytes(src, si_conform=True)
            if self.verbose > 1:
                LOG.debug("Got result: %r", result)
            self.assertIsInstance(result, int)
            self.assertEqual(expected, result)

        if do_switch_locales:
            # Switch back to saved locales
            LOG.debug("Switching back to saved locales %r.", loc)
            locale.setlocale(locale.LC_ALL, loc)                            # restore saved locale

    # -------------------------------------------------------------------------
    def test_human2mbytes_l10n(self):

        LOG.info("Testing localisation of human2mbytes() from fb_tools.common ...")

        loc = locale.getlocale()                                        # get current locale
        encoding = loc[1]
        LOG.debug("Current locale is %r.", loc)
        german = ('de_DE', encoding)

        try:
            locale.setlocale(locale.LC_ALL, german)
        except Exception as e:
            LOG.warning("Got a {c}: {e}".format(c=e.__class__.__name__, e=e))
            return True

        LOG.debug("Setting to locale 'C' to be secure.")
        locale.setlocale(locale.LC_ALL, 'C')
        LOG.debug("Current locale is now %r.", locale.getlocale())

        from fb_tools.common import human2mbytes

        pairs_en = (
            ('1.2 GiB', int(1.2 * 1024)),
            ('1.2 TiB', int(1.2 * 1024 * 1024)),
        )

        pairs_de = (
            ('1,2 GiB', int(1.2 * 1024)),
            ('1,2 TiB', int(1.2 * 1024 * 1024)),
            ('1.024 MiB', 1024),
            ('1.055,4 GiB', int(10554 * 1024 / 10)),
        )

        LOG.debug("Testing english decimal radix character %r.", '.')
        for pair in pairs_en:
            src = pair[0]
            expected = pair[1]
            if self.verbose > 1:
                LOG.debug("Testing localisation of human2mbytes(%r) => %d", src, expected)
            result = human2mbytes(src, si_conform=True)
            if self.verbose > 1:
                LOG.debug("Got result: %r", result)
            self.assertIsInstance(result, int)
            self.assertEqual(expected, result)

        # Switch to german locales
        LOG.debug("Switching to german locale %r.", german)
        # use German locale; name might vary with platform
        locale.setlocale(locale.LC_ALL, german)
        LOG.debug("Current locale is now %r.", locale.getlocale())

        LOG.debug("Testing german decimal radix character %r.", ',')
        for pair in pairs_de:
            src = pair[0]
            expected = pair[1]
            if self.verbose > 1:
                LOG.debug("Testing localisation of human2mbytes(%r) => %d", src, expected)
            result = human2mbytes(src, si_conform=True)
            if self.verbose > 1:
                LOG.debug("Got result: %r", result)
            self.assertIsInstance(result, int)
            self.assertEqual(expected, result)

        # Switch back to english locales
        locale.setlocale(locale.LC_ALL, 'C')    # restore saved locale

        LOG.debug("Testing english decimal radix character %r again.", '.')
        for pair in pairs_en:
            src = pair[0]
            expected = pair[1]
            if self.verbose > 1:
                LOG.debug("Testing localisation of human2mbytes(%r) => %d", src, expected)
            result = human2mbytes(src, si_conform=True)
            if self.verbose > 1:
                LOG.debug("Got result: %r", result)
            self.assertIsInstance(result, int)
            self.assertEqual(expected, result)

        # Switch back to saved locales
        LOG.debug("Switching back to saved locales %r.", loc)
        locale.setlocale(locale.LC_ALL, loc)    # restore saved locale

    # -------------------------------------------------------------------------
    def test_bytes2human(self):

        LOG.info("Testing bytes2human() from fb_tools.common ...")

        from fb_tools.common import bytes2human

        loc = locale.getlocale()    # get current locale
        encoding = loc[1]
        LOG.debug("Current locale is %r.", loc)
        german = ('de_DE', encoding)                                    # noqa

        do_switch_locales = True
        try:
            locale.setlocale(locale.LC_ALL, german)
        except Exception as e:
            LOG.warning("Got a {c}: {e}".format(c=e.__class__.__name__, e=e))
            do_switch_locales = False

        if do_switch_locales:
            LOG.debug("Setting to locale 'C' to be secure.")
            locale.setlocale(locale.LC_ALL, 'C')
            LOG.debug("Current locale is now %r.", locale.getlocale())

        test_pairs_no_si = (
            (0, '0 Bytes'),
            (1, '1 Byte'),
            (5, '5 Bytes'),
            (5 * 1024, '5 KiB'),
            (1999 * 1024 * 1024, '1999 MiB'),
            (2047 * 1024 * 1024, '2047 MiB'),
            (2048 * 1024 * 1024, '2 GiB'),
            (2304 * 1024 * 1024, '2.25 GiB'),
        )

        for pair in test_pairs_no_si:

            src = pair[0]
            expected = pair[1]
            if self.verbose > 1:
                LOG.debug("Testing bytes2human(%r) => %r", src, expected)
            result = bytes2human(src)
            if self.verbose > 1:
                LOG.debug("Got result: %r", result)
            self.assertIsInstance(result, str)
            self.assertEqual(expected, result)

        test_pairs_no_si = (
            (0, '0 Bytes'),
            (1, '1 Byte'),
            (5, '5 Bytes'),
            (5 * 1024, '5.00 KiB'),
            (1999 * 1024 * 1024, '1999.00 MiB'),
            (2047 * 1024 * 1024, '2047.00 MiB'),
            (2048 * 1024 * 1024, '2.00 GiB'),
            (2304 * 1024 * 1024, '2.25 GiB'),
        )

        for pair in test_pairs_no_si:

            src = pair[0]
            expected = pair[1]
            if self.verbose > 1:
                LOG.debug("Testing bytes2human(%r) precission 2 => %r", src, expected)
            result = bytes2human(src, precision=2)
            if self.verbose > 1:
                LOG.debug("Got result: %r", result)
            self.assertIsInstance(result, str)
            self.assertEqual(expected, result)

        if do_switch_locales:
            # Switch back to saved locales
            LOG.debug("Switching back to saved locales %r.", loc)
            locale.setlocale(locale.LC_ALL, loc)                            # restore saved locale

    # -------------------------------------------------------------------------
    def test_to_bool(self):

        LOG.info("Testing to_bool() from fb_tools.common ...")

        from fb_tools.common import to_bool

        class TestClass(object):
            pass
        test_object = TestClass()

        class TestClassTrue(object):
            if sys.version_info[0] > 2:
                def __bool__(self):
                    return True
            else:
                def __nonzero__(self):
                    return True
        test_object_true = TestClassTrue()

        class TestClassFalse(object):
            if sys.version_info[0] > 2:
                def __bool__(self):
                    return False
            else:
                def __nonzero__(self):
                    return False
        test_object_false = TestClassFalse()

        class TestClassFilled(object):
            def __len__(self):
                return 1
        test_object_filled = TestClassFilled()

        class TestClassEmpty(object):
            def __len__(self):
                return 0
        test_object_empty = TestClassEmpty()

        test_pairs = (
            (None, False),
            (True, True),
            (False, False),
            (0, False),
            (0.0, False),
            (1, True),
            (1.0, True),
            (-1, True),
            ('', False),
            ('yes', True),
            ('YES', True),
            ('Yes', True),
            ('y', True),
            ('no', False),
            ('NO', False),
            ('No', False),
            ('n', False),
            ('true', True),
            ('False', False),
            ('On', True),
            ('Off', False),
            (test_object, True),
            (test_object_true, True),
            (test_object_false, False),
            (test_object_filled, True),
            (test_object_empty, False),
        )

        test_pairs_de = (
            ('ja', True),
            ('JA', True),
            ('Ja', True),
            ('j', True),
            ('nein', False),
            ('NEIN', False),
            ('Nein', False),
            ('n', False),
        )

        for pair in test_pairs:

            src = pair[0]
            expected = pair[1]
            if self.verbose > 1:
                LOG.debug("Testing to_bool(%r) => %r", src, expected)
            result = to_bool(src)
            if self.verbose > 1:
                LOG.debug("Got result: %r", result)
            self.assertIsInstance(result, bool)
            self.assertEqual(expected, result)

        # Switch to german locales
        loc = locale.getlocale()                                        # get current locale
        encoding = loc[1]
        LOG.debug("Current locale is %r.", loc)
        german = ('de_DE', encoding)
        try:
            locale.setlocale(locale.LC_ALL, german)
        except Exception as e:
            LOG.warning("Got a {c}: {e}".format(c=e.__class__.__name__, e=e))
            return True

        # use German locale; name might vary with platform
        LOG.debug("Switching to german locale %r.", german)
        locale.setlocale(locale.LC_ALL, german)

        LOG.debug("Testing german Yes/No expressions for to_bool().")
        for pair in test_pairs_de:
            src = pair[0]
            expected = pair[1]
            if self.verbose > 1:
                LOG.debug("Testing localisation of to_bool(%r) => %r", src, expected)
            result = to_bool(src)
            if self.verbose > 1:
                LOG.debug("Got result: %r", result)
            self.assertIsInstance(result, bool)
            self.assertEqual(expected, result)

        # Switch back to saved locales
        LOG.debug("Switching back to saved locales %r.", loc)
        locale.setlocale(locale.LC_ALL, loc)                            # restore saved locale

    # -------------------------------------------------------------------------
    def test_indent(self):

        LOG.info("Testing indent() from fb_tools.common ...")

        from fb_tools.common import indent

        ind = '  '
        initial_ind = ' '

        LOG.debug("Testing indent() without a separate initial_prefix.")
        test_pairs = (
            ('', ''),
            ('a', ind + 'a'),
            ('\na', '\n' + ind + 'a'),
            ('a\nb', ind + 'a\n' + ind + 'b'),
            ('a\n	b', ind + 'a\n' + ind + '	b'),
            ('a\n\nb', ind + 'a\n\n' + ind + 'b'),
            ('a\n \nb', ind + 'a\n \n' + ind + 'b'),
        )
        for pair in test_pairs:
            src = pair[0]
            expected = pair[1]
            if self.verbose > 1:
                LOG.debug("Testing indenting {src!r} => {tgt!r}".format(src=src, tgt=expected))
            result = indent(src, ind)
            if self.verbose > 1:
                LOG.debug("Got result: {!r}".format(result))
            self.assertEqual(expected, result)

        LOG.debug("Testing indent() with a separate initial_prefix.")
        test_pairs = (
            ('', ''),
            ('a', initial_ind + 'a'),
            ('\na', '\n' + ind + 'a'),
            ('a\nb', initial_ind + 'a\n' + ind + 'b'),
            ('a\n	b', initial_ind + 'a\n' + ind + '	b'),
            ('a\n\nb', initial_ind + 'a\n\n' + ind + 'b'),
            ('a\n \nb', initial_ind + 'a\n \n' + ind + 'b'),
        )
        for pair in test_pairs:
            src = pair[0]
            expected = pair[1]
            if self.verbose > 1:
                LOG.debug("Testing indenting {src!r} => {tgt!r}".format(src=src, tgt=expected))
            result = indent(src, ind, initial_prefix=initial_ind)
            if self.verbose > 1:
                LOG.debug("Got result: {!r}".format(result))
            self.assertEqual(expected, result)

        LOG.debug("Testing indent() with a predicate function.")

        def test_predicate(line):
            if line.strip().startswith('b'):
                return False
            return line.strip()

        test_pairs = (
            ('', ''),
            ('a', ind + 'a'),
            ('\na', '\n' + ind + 'a'),
            ('a\nb', ind + 'a\nb'),
            ('a\nb\nc', ind + 'a\nb\n' + ind + 'c'),
            ('a\n b', ind + 'a\n b'),
            ('a\nB', ind + 'a\n' + ind + 'B'),
            ('a\nba', ind + 'a\nba'),
            ('a\n	b', ind + 'a\n	b'),
            ('a\n\nb', ind + 'a\n\nb'),
            ('a\n\nc', ind + 'a\n\n' + ind + 'c'),
            ('a\n \nb', ind + 'a\n \nb'),
            ('a\n \nc', ind + 'a\n \n' + ind + 'c'),
        )
        for pair in test_pairs:
            src = pair[0]
            expected = pair[1]
            if self.verbose > 1:
                LOG.debug("Testing indenting {src!r} => {tgt!r}".format(src=src, tgt=expected))
            result = indent(src, ind, predicate=test_predicate)
            if self.verbose > 1:
                LOG.debug("Got result: {!r}".format(result))
            self.assertEqual(expected, result)


# =============================================================================

if __name__ == '__main__':

    verbose = get_arg_verbose()
    if verbose is None:
        verbose = 0
    init_root_logger(verbose)

    LOG.info("Starting tests ...")

    suite = unittest.TestSuite()

    suite.addTest(TestFbCommon('test_import', verbose))
    suite.addTest(TestFbCommon('test_to_unicode', verbose))
    suite.addTest(TestFbCommon('test_to_utf8', verbose))
    suite.addTest(TestFbCommon('test_to_str', verbose))
    suite.addTest(TestFbCommon('test_human2mbytes', verbose))
    suite.addTest(TestFbCommon('test_human2mbytes_l10n', verbose))
    suite.addTest(TestFbCommon('test_bytes2human', verbose))
    suite.addTest(TestFbCommon('test_to_bool', verbose))
    suite.addTest(TestFbCommon('test_indent', verbose))

    runner = unittest.TextTestRunner(verbosity=verbose)

    result = runner.run(suite)

# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 fileencoding=utf-8
