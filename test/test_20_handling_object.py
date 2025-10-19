#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@summary: Test script (and module) for unit tests on handling object.

@author: Frank Brehm
@contact: frank@brehm-online.com
@copyright: © 2025 Frank Brehm, Berlin
@license: GPL3
"""

import datetime
import logging
import os
import sys
import tempfile
import textwrap
from pathlib import Path

try:
    import unittest2 as unittest
except ImportError:
    import unittest

from babel.dates import LOCALTZ

libdir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, libdir)

from fb_tools.common import to_bool

from general import FbToolsTestcase, get_arg_verbose, init_root_logger

LOG = logging.getLogger('test_handling_object')

EXEC_LONG_TESTS = False
if 'EXEC_LONG_TESTS' in os.environ and os.environ['EXEC_LONG_TESTS'] != '':
    EXEC_LONG_TESTS = to_bool(os.environ['EXEC_LONG_TESTS'])

EXEC_CONSOLE_TESTS = sys.stdin.isatty()
if 'EXEC_CONSOLE_TESTS' in os.environ and os.environ['EXEC_CONSOLE_TESTS'] != '':
    EXEC_CONSOLE_TESTS = to_bool(os.environ['EXEC_CONSOLE_TESTS'])

EXEC_DNS_DEPENDING_TESTS = False
if 'EXEC_DNS_DEPENDING_TESTS' in os.environ and os.environ['EXEC_DNS_DEPENDING_TESTS'] != '':
    EXEC_DNS_DEPENDING_TESTS = to_bool(os.environ['EXEC_DNS_DEPENDING_TESTS'])


# =============================================================================
class TestFbHandlingObject(FbToolsTestcase):
    """Testcase for unit tests on module fb_tools.handling_obj and class HandlingObject."""

    # -------------------------------------------------------------------------
    def setUp(self):
        """Execute this on setting up before calling each particular test method."""
        if self.verbose >= 1:
            print()

        self.test_file = None

    # -------------------------------------------------------------------------
    def tearDown(self):
        """Tear down routine for calling each particular test method."""
        if self.test_file is not None:
            if os.path.exists(self.test_file):
                LOG.debug('Removing {!r} ...'.format(self.test_file))
                os.remove(self.test_file)

    # -------------------------------------------------------------------------
    def create_test_file(self):
        """Create a temporary test file."""
        (fh, self.test_file) = tempfile.mkstemp(
            prefix='test-handling-obj.', suffix='.txt', text=False)
        os.close(fh)
        LOG.debug('Created temporary test file: {!r}.'.format(self.test_file))

    # -------------------------------------------------------------------------
    def write_test_file(self, content_bin):
        """Write the given content into the temporary test file."""
        if self.test_file is None:
            self.create_test_file()

        if self.verbose > 1:
            LOG.debug('Writing {!r} ...'.format(self.test_file))
        with open(self.test_file, 'wb') as fh:
            fh.write(content_bin)

    # -------------------------------------------------------------------------
    def test_import(self):
        """Test instantiating fb_tools.handling_obj."""
        LOG.info(self.get_method_doc())
        import fb_tools.handling_obj
        LOG.debug('Version of fb_tools.handling_obj: {!r}.'.format(
            fb_tools.handling_obj.__version__))

        LOG.info('Testing import of CalledProcessError from fb_tools.handling_obj ...')
        from fb_tools.handling_obj import CalledProcessError
        LOG.debug('Description of CalledProcessError: ' + textwrap.dedent(
            CalledProcessError.__doc__))

        LOG.info('Testing import of TimeoutExpiredError from fb_tools.handling_obj ...')
        from fb_tools.handling_obj import TimeoutExpiredError
        LOG.debug('Description of TimeoutExpiredError: ' + textwrap.dedent(
            TimeoutExpiredError.__doc__))

        LOG.info('Testing import of HandlingObject from fb_tools.handling_obj ...')
        from fb_tools.handling_obj import HandlingObject
        LOG.debug('Description of HandlingObject: ' + textwrap.dedent(
            HandlingObject.__doc__))

        LOG.info('Testing import of CompletedProcess from fb_tools.handling_obj ...')
        from fb_tools.handling_obj import CompletedProcess
        LOG.debug('Description of CompletedProcess: ' + textwrap.dedent(
            CompletedProcess.__doc__))

    # -------------------------------------------------------------------------
    def test_called_process_error(self):
        """Test raising a CalledProcessError exception."""
        LOG.info(self.get_method_doc())

        from fb_tools.handling_obj import CalledProcessError

        ret_val = 1
        cmd = '/bin/wrong.command'
        output = 'Sample output'
        stderr = 'Sample error message'

        with self.assertRaises(CalledProcessError) as cm:
            raise CalledProcessError(ret_val, cmd)
        e = cm.exception
        LOG.debug('{} raised: {}'.format(e.__class__.__name__, e))
        LOG.debug('Testing for e.returncode == {}.'.format(ret_val))
        self.assertEqual(e.returncode, ret_val)
        LOG.debug('Testing for e.cmd == {!r}.'.format(cmd))
        self.assertEqual(e.cmd, cmd)
        LOG.debug('Testing for e.output is None.')
        self.assertIsNone(e.output)
        LOG.debug('Testing for e.stdout is None.')
        self.assertIsNone(e.stdout)
        LOG.debug('Testing for e.stderr is None.')
        self.assertIsNone(e.stderr)

        with self.assertRaises(CalledProcessError) as cm:
            raise CalledProcessError(ret_val, cmd, output, stderr)
        e = cm.exception
        LOG.debug('{} raised: {}'.format(e.__class__.__name__, e))
        LOG.debug('Testing for e.output == {!r}.'.format(output))
        self.assertEqual(e.output, output)
        LOG.debug('Testing for e.stdout == {!r}.'.format(output))
        self.assertEqual(e.stdout, output)
        LOG.debug('Testing for e.stderr == {!r}.'.format(stderr))
        self.assertEqual(e.stderr, stderr)

    # -------------------------------------------------------------------------
    def test_timeout_expired_error(self):
        """Test raising a TimeoutExpiredError exception."""
        LOG.info(self.get_method_doc())

        from fb_tools.handling_obj import TimeoutExpiredError

        timeout_1sec = 1
        timeout_10sec = 10
        cmd = '/bin/long.terming.command'
        output = 'Sample output'
        stderr = 'Sample error message'

        with self.assertRaises(TimeoutExpiredError) as cm:
            raise TimeoutExpiredError(cmd, timeout_1sec)
        e = cm.exception
        LOG.debug('{} raised: {}'.format(e.__class__.__name__, e))
        LOG.debug('Testing for e.timeout == {}.'.format(timeout_1sec))
        self.assertEqual(e.timeout, timeout_1sec)
        LOG.debug('Testing for e.cmd == {!r}.'.format(cmd))
        self.assertEqual(e.cmd, cmd)
        LOG.debug('Testing for e.output is None.')
        self.assertIsNone(e.output)
        LOG.debug('Testing for e.stdout is None.')
        self.assertIsNone(e.stdout)
        LOG.debug('Testing for e.stderr is None.')
        self.assertIsNone(e.stderr)

        with self.assertRaises(TimeoutExpiredError) as cm:
            raise TimeoutExpiredError(cmd, timeout_10sec, output, stderr)
        e = cm.exception
        LOG.debug('{} raised: {}'.format(e.__class__.__name__, e))
        LOG.debug('Testing for e.output == {!r}.'.format(output))
        self.assertEqual(e.output, output)
        LOG.debug('Testing for e.stdout == {!r}.'.format(output))
        self.assertEqual(e.stdout, output)
        LOG.debug('Testing for e.stderr == {!r}.'.format(stderr))
        self.assertEqual(e.stderr, stderr)

    # -------------------------------------------------------------------------
    def test_generic_handling_object(self):
        """Test init of a generic handling object."""
        LOG.info(self.get_method_doc())

        import fb_tools.handling_obj
        from fb_tools.handling_obj import HandlingObject

        HandlingObject.fileio_timeout = 10
        hdlr = HandlingObject(
            appname=self.appname,
            verbose=self.verbose,
        )
        LOG.debug('HandlingObject %%r: {!r}'.format(hdlr))
        LOG.debug('HandlingObject %%s: {}'.format(hdlr))
        self.assertEqual(hdlr.appname, self.appname)
        self.assertEqual(hdlr.verbose, self.verbose)
        self.assertIsNotNone(hdlr.base_dir)
        self.assertEqual(hdlr.version, fb_tools.handling_obj.__version__)
        self.assertFalse(hdlr.simulate)
        self.assertFalse(hdlr.force)
        self.assertFalse(hdlr.quiet)
        self.assertFalse(hdlr.interrupted)
        self.assertEqual(hdlr.fileio_timeout, 10)

        hdlr.simulate = True
        self.assertTrue(hdlr.simulate)

        hdlr.force = True
        self.assertTrue(hdlr.force)

        hdlr.quiet = True
        self.assertTrue(hdlr.quiet)

    # -------------------------------------------------------------------------
    def test_completed_process(self):
        """Test class CompletedProcess."""
        LOG.info(self.get_method_doc())

        from fb_tools.handling_obj import CompletedProcess
        from fb_tools.handling_obj import CalledProcessError

        args = ['/bin/some.command', '--option', '1', 'arg2']
        retval = 5
        stdout = 'Message on STDOUT\n * Second line on STDOUT\n'
        stderr = 'Message on STDERR\n'

        tdiff = datetime.timedelta(seconds=5)
        start_dt = datetime.datetime.now(LOCALTZ) - tdiff
        end_dt = datetime.datetime.now(LOCALTZ)

        proc = CompletedProcess(args, retval, stdout, stderr, start_dt=start_dt, end_dt=end_dt)
        LOG.debug('Got a {} object.'.format(proc.__class__.__name__))
        self.assertIsInstance(proc, CompletedProcess)
        LOG.debug('CompletedProcess %%r: {!r}'.format(proc))
        LOG.debug('CompletedProcess %%s: {}'.format(proc))

        self.assertEqual(proc.returncode, retval)
        self.assertEqual(proc.args, args)
        self.assertEqual(proc.stdout, stdout)
        self.assertEqual(proc.stderr, stderr)

        LOG.info('Testing raising a CalledProcessError exception ...')
        with self.assertRaises(CalledProcessError) as cm:
            proc.check_returncode()
        e = cm.exception
        LOG.debug('{} raised: {}'.format(e.__class__.__name__, e))

    # -------------------------------------------------------------------------
    @unittest.skipUnless(EXEC_LONG_TESTS, 'Long terming tests are not executed.')
    def test_run_simple(self):
        """Test execution of a shell script."""
        LOG.info(self.get_method_doc())

        from fb_tools.common import pp
        from fb_tools.handling_obj import HandlingObject, CompletedProcess
        from fb_tools.errors import CommandNotFoundError

        curdir = os.path.dirname(os.path.abspath(__file__))
        call_script = os.path.join(curdir, 'call_script.sh')
        if not os.path.exists(call_script):
            raise CommandNotFoundError(call_script)

        LOG.debug('Trying to execute {!r} ...'.format(call_script))

        hdlr = HandlingObject(
            appname=self.appname,
            verbose=self.verbose,
        )

        proc = hdlr.run([call_script])
        LOG.debug('Got back a {} object.'.format(proc.__class__.__name__))
        self.assertIsInstance(proc, CompletedProcess)

        LOG.debug('Got return value: {}.'.format(proc.returncode))
        LOG.debug('Got proc args:\n{}.'.format(pp(proc.args)))
        LOG.debug('Got STDOUT: {!r}'.format(proc.stdout))
        LOG.debug('Got STDERR: {!r}'.format(proc.stderr))

        self.assertEqual(proc.returncode, 0)
        self.assertIsNone(proc.stdout)
        self.assertIsNone(proc.stderr)

    # -------------------------------------------------------------------------
    @unittest.skipUnless(EXEC_LONG_TESTS, 'Long terming tests are not executed.')
    def test_run_timeout(self):
        """Test timing out the run() method."""
        LOG.info(self.get_method_doc())

        from fb_tools.handling_obj import HandlingObject
        from fb_tools.handling_obj import TimeoutExpiredError
        from fb_tools.errors import CommandNotFoundError

        curdir = os.path.dirname(os.path.abspath(__file__))
        call_script = os.path.join(curdir, 'call_sleep.sh')
        if not os.path.exists(call_script):
            raise CommandNotFoundError(call_script)

        sleep = 10
        timeout = sleep - 6

        LOG.debug('Trying to execute {c!r} with a timeout of {t} seconds ...'.format(
            c=call_script, t=timeout))

        hdlr = HandlingObject(
            appname=self.appname,
            verbose=self.verbose,
        )

        cmd = [call_script, str(sleep)]

        with self.assertRaises(TimeoutExpiredError) as cm:
            proc = hdlr.run(cmd, timeout=timeout)                                   # noqa
        e = cm.exception
        LOG.debug('{} raised: {}'.format(e.__class__.__name__, e))

    # -------------------------------------------------------------------------
    def test_read_file(self):
        """Test method read_file() of class HandlingObject."""
        LOG.info(self.get_method_doc())

        from fb_tools.common import to_unicode, to_str, encode_or_bust

        from fb_tools.handling_obj import HandlingObject

        hdlr = HandlingObject(
            appname=self.appname,
            verbose=self.verbose,
        )

        text_ascii = 'This is a pure ASCII text.\n'
        text_uni = to_unicode('Das ist ein deutscher Text mit Umlauten: äöü ÄÖÜ ß@€.\n')

        # Pure ASCII ...
        text_bin = encode_or_bust(text_ascii, 'utf-8')
        self.write_test_file(text_bin)

        LOG.debug('Reading a pure ASCII file in binary mode.')
        content = hdlr.read_file(self.test_file, binary=True)
        LOG.debug('Read content: {!r}'.format(content))
        self.assertEqual(text_bin, content)

        LOG.debug('Reading a pure ASCII file in text mode.')
        content = hdlr.read_file(self.test_file, binary=False, encoding='utf-8')
        LOG.debug('Read content: {!r}'.format(content))
        self.assertEqual(text_ascii, content)

        # Unicode => utf-8
        text_bin = encode_or_bust(text_uni, 'utf-8')
        self.write_test_file(text_bin)

        LOG.debug('Reading an UTF-8 encoded file in binary mode.')
        content = hdlr.read_file(self.test_file, binary=True)
        LOG.debug('Read content: {!r}'.format(content))
        self.assertEqual(text_bin, content)

        LOG.debug('Reading an UTF-8 encoded file in text mode.')
        content = hdlr.read_file(self.test_file, binary=False, encoding='utf-8')
        LOG.debug('Read content: {!r}'.format(content))
        LOG.debug('Read content:\n{}'.format(to_str(content).strip()))
        self.assertEqual(text_uni, content)

        # Unicode => WINDOWS-1252
        text_bin = encode_or_bust(text_uni, 'WINDOWS-1252')
        self.write_test_file(text_bin)

        LOG.debug('Reading an WINDOWS-1252 encoded file in binary mode.')
        content = hdlr.read_file(self.test_file, binary=True)
        LOG.debug('Read content: {!r}'.format(content))
        self.assertEqual(text_bin, content)

        LOG.debug('Reading an WINDOWS-1252 encoded file in text mode.')
        content = hdlr.read_file(self.test_file, binary=False, encoding='WINDOWS-1252')
        LOG.debug('Read content: {!r}'.format(content))
        LOG.debug('Read content:\n{}'.format(to_str(content).strip()))
        self.assertEqual(text_uni, content)

        # Wrong encoding
        LOG.debug(
            'Reading a file with a wrong encoding (written in WINDOWS-1252, '
            'trying to read as UTF-8) ...')
        content = hdlr.read_file(self.test_file, binary=False, encoding='utf-8')
        LOG.debug('Read content: {!r}'.format(content))
        LOG.debug('Read content:\n{}'.format(to_str(content).strip()))

    # -------------------------------------------------------------------------
    def test_write_file(self):
        """Test method write_file() of class HandlingObject."""
        LOG.info(self.get_method_doc())

        from fb_tools.common import to_unicode, encode_or_bust

        from fb_tools.handling_obj import HandlingObject

        self.write_test_file(encode_or_bust(''))

        hdlr = HandlingObject(
            appname=self.appname,
            verbose=self.verbose,
        )

        text_ascii = 'This is a pure ASCII text.\n'
        text_ascii_as_uni = to_unicode(text_ascii)
        text_uni = to_unicode('Das ist ein deutscher Text mit Umlauten: äöü ÄÖÜ ß@€.\n')

        # Pure ASCII ...
        text_bin = encode_or_bust(text_ascii, 'utf-8')
        LOG.debug('Writing an UTF-8 encoded file in binary mode.')
        hdlr.write_file(self.test_file, text_bin)
        LOG.debug('Writing an UTF-8 encoded file in text mode.')
        hdlr.write_file(self.test_file, text_ascii_as_uni, encoding='utf-8')

        # Unicode => utf-8
        LOG.debug('Writing text with unicode characters in an UTF-8 encoded file.')
        hdlr.write_file(self.test_file, text_uni, encoding='utf-8')

        # Unicode => WINDOWS-1252
        LOG.debug('Writing text with unicode characters in an WINDOWS-1252 encoded file.')
        hdlr.write_file(self.test_file, text_uni, encoding='WINDOWS-1252')

    # -------------------------------------------------------------------------
    def test_get_command(self):
        """Test method get_command() of class HandlingObject."""
        LOG.info(self.get_method_doc())

        from fb_tools.handling_obj import HandlingObject

        hdlr = HandlingObject(
            appname=self.appname,
            verbose=self.verbose,
        )

        cmd = 'ls'
        LOG.debug('Searching command {!r}.'.format(cmd))
        p = hdlr.get_command(cmd)
        LOG.debug('Got back: {!r}'.format(p))
        self.assertIsInstance(p, Path)
        self.assertEqual(p.name, cmd)

        cmd = 'uhu-banane'
        LOG.debug('Searching non existing command {!r}.'.format(cmd))
        p = hdlr.get_command(cmd)
        LOG.debug('Got back: {!r}'.format(p))
        self.assertIsNone(p)

        cmd = 'call_sleep.sh'
        symlink = 'do_sleep'

        LOG.debug('Searching command {!r}, which is not in path.'.format(cmd))
        p = hdlr.get_command(cmd)
        LOG.debug('Got back: {!r}'.format(p))
        self.assertIsNone(p)

        cur_dir = Path(__file__).parent.resolve()

        cmd_abs = str(cur_dir / cmd)
        LOG.debug('Searching absolute command {!r}.'.format(cmd_abs))
        p = hdlr.get_command(cmd_abs)
        LOG.debug('Got back: {!r}'.format(p))
        self.assertIsInstance(p, Path)
        self.assertEqual(p.name, cmd)

        cmd_abs = str(cur_dir / symlink)
        LOG.debug('Searching absolute symlink command {!r}.'.format(cmd_abs))
        p = hdlr.get_command(cmd_abs)
        LOG.debug('Got back: {!r}'.format(p))
        self.assertIsInstance(p, Path)
        self.assertEqual(p.name, symlink)

        LOG.debug('Searching absolute symlink command {!r}, resolved.'.format(cmd_abs))
        p = hdlr.get_command(cmd_abs, resolve=True)
        LOG.debug('Got back: {!r}'.format(p))
        self.assertIsInstance(p, Path)
        self.assertEqual(p.name, cmd)

        LOG.debug('Adding {!r} to search paths.'.format(cur_dir))
        hdlr.add_search_paths.append(cur_dir)

        LOG.debug('Searching command {!r}, which is now in path.'.format(cmd))
        p = hdlr.get_command(cmd)
        LOG.debug('Got back: {!r}'.format(p))
        self.assertIsInstance(p, Path)
        self.assertEqual(p.name, cmd)

        LOG.debug('Searching symlinked command {!r}.'.format(symlink))
        p = hdlr.get_command(symlink)
        LOG.debug('Got back: {!r}'.format(p))
        self.assertIsInstance(p, Path)
        self.assertEqual(p.name, symlink)

        LOG.debug((
            'Searching symlinked command {!r}, which points to {!r} '
            'with resolved path.').format(symlink, cmd))
        p = hdlr.get_command(symlink, resolve=True)
        LOG.debug('Got back: {!r}'.format(p))
        self.assertIsInstance(p, Path)
        self.assertEqual(p.name, cmd)

    # -------------------------------------------------------------------------
    def test_get_int_addressfamily(self):
        """Test property address_famlily and method get_address_famlily_int()."""
        LOG.info(self.get_method_doc())

        import socket

        from fb_tools.handling_obj import HandlingObject

        hdlr = HandlingObject(
            appname=self.appname,
            verbose=self.verbose,
        )

        af = hdlr.address_family
        LOG.debug(f'Default value of property address_famlily is {af!r}.')
        self.assertEqual(hdlr.address_family, 'any')

        test_data = (
            (socket.AF_INET, socket.AF_INET),
            ('ipv4', socket.AF_INET),
            (4, socket.AF_INET),
            (socket.AF_INET6, socket.AF_INET6),
            ('ipv6', socket.AF_INET6),
            (6, socket.AF_INET6),
            ('any', 'any'),
            (0, 'any'),
        )

        for pair in test_data:
            test_val = pair[0]
            exp_val = pair[1]
            LOG.debug(f'Testing {test_val!r} for property address_family, expecting {exp_val!r}.')
            hdlr.address_family = test_val
            af = hdlr.address_family
            LOG.debug(f'Value of property address_famlily is {af!r}.')
            self.assertEqual(af, exp_val)

        test_data = (None, '0', 3, '4', 'bla')
        for test_val in test_data:
            LOG.debug(f'Testing {test_val!r} for property address_family.')
            with self.assertRaises(ValueError) as cm:
                hdlr.address_family = test_val
            e = cm.exception
            LOG.debug('{} raised: {}'.format(e.__class__.__name__, e))

        hdlr.address_family = 0

        test_data = (
            (None, 0),
            (0, 0),
            ('any', 0),
            (socket.AF_INET, socket.AF_INET),
            ('ipv4', socket.AF_INET),
            (4, socket.AF_INET),
            (socket.AF_INET6, socket.AF_INET6),
            ('ipv6', socket.AF_INET6),
            (6, socket.AF_INET6),
        )

        for pair in test_data:
            test_val = pair[0]
            exp_val = pair[1]
            LOG.debug(
                f'Testing {test_val!r} for get_address_famlily_int(), expecting {exp_val!r}.')
            af = hdlr.get_address_famlily_int(test_val)
            LOG.debug(f'Return value of get_address_famlily_int() is {af!r}.')
            self.assertEqual(af, exp_val)

        test_data = ('0', 3, '4', 'bla', object())
        for test_val in test_data:
            LOG.debug(f'Testing get_address_famlily_int({test_val!r}) ...')
            with self.assertRaises(ValueError) as cm:
                af = hdlr.get_address_famlily_int(test_val)
            e = cm.exception
            LOG.debug('{} raised: {}'.format(e.__class__.__name__, e))

    # -------------------------------------------------------------------------
    @unittest.skipUnless(
        EXEC_DNS_DEPENDING_TESTS, 'Tests depending on external DNS are not executed.')
    def test_get_address(self):
        """Test method get_address() of class HandlingObject."""
        LOG.info(self.get_method_doc())

        import ipaddress
        import socket

        from fb_tools.handling_obj import HandlingObject

        hdlr = HandlingObject(
            appname=self.appname,
            verbose=self.verbose,
        )

        test_addresses = (
            ('1.2.3.4', 'any', ['1.2.3.4']),
            (ipaddress.ip_address('1.2.3.4'), 'any', ['1.2.3.4']),
            ('1.2.3.4', socket.AF_INET, ['1.2.3.4']),
            ('1.2.3.4', socket.AF_INET6, []),
            ('fefe:affe::babe', 'any', ['fefe:affe::babe']),
            (ipaddress.ip_address('fefe:affe::babe'), 'any', ['fefe:affe::babe']),
            ('fefe:affe::babe', socket.AF_INET, []),
            ('fefe:affe::babe', socket.AF_INET6, ['fefe:affe::babe']),
            ('mail.uhu-banane.net', 'any', ['188.34.187.246', '2a01:4f8:c010:80ee::1']),
            ('mail.uhu-banane.net', socket.AF_INET, ['188.34.187.246']),
            ('mail.uhu-banane.net', socket.AF_INET6, ['2a01:4f8:c010:80ee::1']),
        )

        for test_tuple in test_addresses:
            host = test_tuple[0]
            af = test_tuple[1]
            exp_addresses = sorted(test_tuple[2])
            LOG.debug(
                'Testing resolving {h!r} with address family {af!r}, expecting: {exp!r}'.format(
                    h=host, af=af, exp=exp_addresses))
            got_addresses = hdlr.get_address(host, address_family=af)
            addr_list = []
            for addr in got_addresses:
                self.assertIsInstance(addr, (ipaddress.IPv4Address, ipaddress.IPv6Address))
                addr_list.append(str(addr))
            addr_list.sort()
            LOG.debug('Got resolved address list: {!r}.'.format(addr_list))
            self.assertEqual(addr_list, exp_addresses)

    # -------------------------------------------------------------------------
    @unittest.skipUnless(
        EXEC_CONSOLE_TESTS, 'Tests depending on a console are not executed.')
    def test_get_password(self):
        """Test method get_password() of class HandlingObject."""
        LOG.info(self.get_method_doc())

        import time

        from fb_tools.errors import ExitAppError
        from fb_tools.handling_obj import HandlingObject

        hdlr = HandlingObject(
            appname=self.appname,
            verbose=self.verbose,
        )
        hdlr.prompt_timeout = 5

        total_start = time.time()

        leaps = 3
        i = 0
        while i < leaps:
            i += 1
            try:
                start_time = time.time()
                prompt = f'Password {i}: '
                pwd = hdlr.get_password(prompt, repeat=False, raise_on_exit=True)
            except ExitAppError as e:
                LOG.info(str(e))
            except KeyboardInterrupt as e:
                LOG.info('Got a {c}: Interrupted on demand - {e}.'.format(
                    c=e.__class__.__name__, e=e))
            else:
                LOG.debug('Got password: {!r}.'.format(pwd))
            finally:
                diff = time.time() - start_time
                LOG.debug('Needed {:0.6f} seconds.'.format(diff))

        diff = time.time() - total_start
        LOG.info('Needed total {:0.6f} seconds.'.format(diff))


# =============================================================================
if __name__ == '__main__':

    verbose = get_arg_verbose()
    if verbose is None:
        verbose = 0
    init_root_logger(verbose)

    LOG.info('Starting tests ...')

    suite = unittest.TestSuite()

    suite.addTest(TestFbHandlingObject('test_import', verbose))
    suite.addTest(TestFbHandlingObject('test_called_process_error', verbose))
    suite.addTest(TestFbHandlingObject('test_timeout_expired_error', verbose))
    suite.addTest(TestFbHandlingObject('test_generic_handling_object', verbose))
    suite.addTest(TestFbHandlingObject('test_completed_process', verbose))
    suite.addTest(TestFbHandlingObject('test_run_simple', verbose))
    suite.addTest(TestFbHandlingObject('test_run_timeout', verbose))
    suite.addTest(TestFbHandlingObject('test_read_file', verbose))
    suite.addTest(TestFbHandlingObject('test_write_file', verbose))
    suite.addTest(TestFbHandlingObject('test_get_command', verbose))
    suite.addTest(TestFbHandlingObject('test_get_int_addressfamily', verbose))
    suite.addTest(TestFbHandlingObject('test_get_address', verbose))
    suite.addTest(TestFbHandlingObject('test_get_password', verbose))

    runner = unittest.TextTestRunner(verbosity=verbose)

    result = runner.run(suite)


# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
