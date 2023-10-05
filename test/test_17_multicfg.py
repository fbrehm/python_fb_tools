#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
@author: Frank Brehm
@contact: frank@brehm-online.com
@copyright: © 2023 Frank Brehm, Berlin
@license: GPL3
@summary: test script (and module) for unit tests on multi config class
'''

import os
import sys
import logging
import tempfile
import stat

from pathlib import Path

try:
    import unittest2 as unittest
except ImportError:
    import unittest

# from babel.dates import LOCALTZ

libdir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'lib'))
sys.path.insert(0, libdir)

from general import FbToolsTestcase, get_arg_verbose, init_root_logger

from fb_tools.common import pp, to_str, is_sequence

LOG = logging.getLogger('test_multicfg')


# =============================================================================
class TestFbMultiConfig(FbToolsTestcase):

    # -------------------------------------------------------------------------
    def setUp(self):

        self.test_dir = Path(__file__).parent.resolve()
        self.base_dir = self.test_dir.parent
        self.test_cfg_dir = self.test_dir / 'test-multiconfig'
        self._appname = 'test_multicfg'

    # -------------------------------------------------------------------------
    def tearDown(self):

        pass

    # -------------------------------------------------------------------------
    def test_import(self):

        if self.verbose >= 1:
            print()

        LOG.info("Testing import of fb_tools.multi_config ...")
        import fb_tools.multi_config                                        # noqa

        LOG.info("Testing import of MultiConfigError from fb_tools.multi_config ...")
        from fb_tools.multi_config import MultiConfigError                  # noqa

        LOG.info("Testing import of BaseMultiConfig from fb_tools.multi_config ...")
        from fb_tools.multi_config import BaseMultiConfig                   # noqa

    # -------------------------------------------------------------------------
    def test_object(self):

        if self.verbose >= 1:
            print()

        LOG.info("Testing init of a BaseMultiConfig object.")

        from fb_tools.multi_config import BaseMultiConfig

        cfg = BaseMultiConfig(
            appname=self.appname,
            config_dir='test', additional_stems='test',
            verbose=self.verbose,
        )
        LOG.debug("BaseMultiConfig %%r: %r", cfg)
        LOG.debug("BaseMultiConfig %%s: %s", str(cfg))

    # -------------------------------------------------------------------------
    def test_init_cfg_dirs(self):

        if self.verbose >= 1:
            print()

        LOG.info("Testing init of configuration directories.")

        from fb_tools.multi_config import BaseMultiConfig

        cfg = BaseMultiConfig(
            appname=self.appname, base_dir=self.base_dir,
            config_dir='test', additional_stems='test',
            additional_cfgdirs=self.test_cfg_dir, verbose=self.verbose,
        )

        if self.verbose >= 2:
            LOG.debug("Current configuration directories:\n{}".format(pp(cfg.config_dirs)))

        system_path = Path('/etc', 'test')
        LOG.debug("Testing existence of system config path {!r}.".format(system_path))
        self.assertIn(system_path, cfg.config_dirs)

        user_path = Path(os.path.expanduser('~')) / '.config' / 'test'
        LOG.debug("Testing existence of user config path {!r}.".format(user_path))
        self.assertIn(user_path, cfg.config_dirs)

        cwd_etc_dir = Path.cwd() / 'etc'
        LOG.debug("Testing existence of config path in current dir {!r}.".format(cwd_etc_dir))
        self.assertIn(cwd_etc_dir, cfg.config_dirs)

        base_etc_dir = self.base_dir / 'etc'
        LOG.debug("Testing existence of basedir config path {!r}.".format(base_etc_dir))
        self.assertIn(base_etc_dir, cfg.config_dirs)

        LOG.debug("Testing existence of basedir {!r}.".format(self.base_dir))
        self.assertIn(self.base_dir, cfg.config_dirs)

        cur_dir = Path.cwd()
        LOG.debug("Testing existence of current dir {!r}.".format(cur_dir))
        self.assertIn(cur_dir, cfg.config_dirs)

        LOG.debug("Testing existence of config dir {!r}.".format(str(self.test_cfg_dir)))
        self.assertIn(self.test_cfg_dir, cfg.config_dirs)

    # -------------------------------------------------------------------------
    def test_init_stems(self):

        if self.verbose >= 1:
            print()

        LOG.info("Testing init of configuration file stems.")

        valid_stems = [
            'uhu', ('bla', 'blub'), b'banane', ['item0', 'item1'], Path('p0'),
        ]
        valid_stems.append(('a', b'b', Path('p1')))

        invalid_stems = (
            1, 2.3, {'uhu': 'banane'}, os.sep, str(Path('p0') / 'p1'), Path('uhu') / 'banane',
        )

        from fb_tools.multi_config import BaseMultiConfig

        LOG.debug("Testing, whether appname is in file stems ...")
        cfg = BaseMultiConfig(appname=self.appname, config_dir='test', verbose=self.verbose)
        if self.verbose >= 2:
            LOG.debug("Initialized base stems:\n{}".format(pp(cfg.stems)))
        if self.verbose > 1:
            LOG.debug("Checking for existence of stem {!r}.".format(self.appname))
        self.assertIn(self.appname, cfg.stems)

        LOG.debug("Testing for valid stems ...")

        for stem in valid_stems:
            LOG.debug("Testing valid stem {s!r} ({c}).".format(s=stem, c=stem.__class__.__name__))
            cfg = BaseMultiConfig(
                appname=self.appname, config_dir='test', additional_stems=stem,
                verbose=self.verbose,
            )
            if self.verbose >= 2:
                LOG.debug("Initialized stems:\n{}".format(pp(cfg.stems)))
            if is_sequence(stem):
                for st in stem:
                    item = str(to_str(st))
                    if self.verbose > 1:
                        LOG.debug("Checking for existence of stem {!r}.".format(item))
                    self.assertIn(item, cfg.stems)
            else:
                item = str(to_str(stem))
                if self.verbose > 1:
                    LOG.debug("Checking for existence of stem {!r}.".format(item))
                self.assertIn(item, cfg.stems)

        for stem in invalid_stems:
            LOG.debug("Testing invalid stem {s!r} ({c}).".format(
                s=stem, c=stem.__class__.__name__))
            with self.assertRaises((TypeError, ValueError)) as cm:
                cfg = BaseMultiConfig(
                    appname=self.appname, config_dir='test', additional_stems=stem,
                    verbose=self.verbose,
                )
            e = cm.exception
            LOG.debug("{c} raised on stem {s!r}: {e}".format(c=e.__class__.__name__, s=stem, e=e))

        LOG.debug("Testing appending and perpending stems ...")

        cfg = BaseMultiConfig(appname=self.appname, config_dir='test', verbose=self.verbose)

        LOG.debug("Appending stem 'uhu' ...")
        cfg.append_stem('uhu')
        if self.verbose >= 2:
            LOG.debug("Initialized stems:\n{}".format(pp(cfg.stems)))
        self.assertEqual(cfg.stems, [self.appname, 'uhu'])

        LOG.debug("Appending stem 'uhu' again ...")
        cfg.append_stem('uhu')
        if self.verbose >= 2:
            LOG.debug("Initialized stems:\n{}".format(pp(cfg.stems)))
        self.assertEqual(cfg.stems, [self.appname, 'uhu'])

        LOG.debug("Appending stem 'mycfg' ...")
        cfg.add_stem('mycfg')
        if self.verbose >= 2:
            LOG.debug("Initialized stems:\n{}".format(pp(cfg.stems)))
        self.assertEqual(cfg.stems, [self.appname, 'uhu', 'mycfg'])

        LOG.debug("Prepending stem 'bla' ...")
        cfg.prepend_stem('bla')
        if self.verbose >= 2:
            LOG.debug("Initialized stems:\n{}".format(pp(cfg.stems)))
        self.assertEqual(cfg.stems, ['bla', self.appname, 'uhu', 'mycfg'])


    # -------------------------------------------------------------------------
    def test_collect_cfg_files(self):

        if self.verbose >= 1:
            print()

        LOG.info("Testing collecting of configuration files.")

        exts = ('.ini', '.js', '.yaml')
        ext_methods = {
            '.ini': 'load_ini',
            '.js': 'load_json',
            '.yaml': 'load_yaml',
        }

        from fb_tools.multi_config import BaseMultiConfig

        cfg = BaseMultiConfig(
            appname=self.appname, config_dir=self.test_cfg_dir.name,
            additional_cfgdirs=self.test_cfg_dir, verbose=self.verbose)
        if self.verbose >= 2:
            LOG.debug("Current configuration directories:\n{}".format(pp(cfg.config_dirs)))
            LOG.debug("Initialized stems:\n{}".format(pp(cfg.stems)))

        cfg.collect_config_files()
        if self.verbose >= 2:
            LOG.debug("Found configuration files:\n{}".format(pp(cfg.config_files)))
            LOG.debug("Found read methods:\n{}".format(pp(cfg.config_file_methods)))
            LOG.debug("Assigned ext_patterns:\n{}".format(pp(cfg.ext_patterns)))
            LOG.debug("Assigned ext_loaders:\n{}".format(pp(cfg.ext_loader)))

        for ext in exts:
            path = self.test_cfg_dir / (self.appname + ext)
            exp_method = ext_methods[ext]
            LOG.debug("Checking for existence of detected cfg file {!r}.".format(str(path)))
            if path.exists():
                self.assertIn(path, cfg.config_files)
                LOG.debug("Checking method {m!r} of cfg file {f!r}.".format(
                    m=exp_method, f=str(path)))
                found_method = cfg.config_file_methods[path]
                LOG.debug("Found method: {!r}".format(found_method))
                self.assertEqual(exp_method, found_method)
            else:
                self.assertNotIn(path, cfg.config_files)
                LOG.debug("Not existing file {!r} not in cfg.config_files.".format(path))

        for ext in exts:
            path = self.test_cfg_dir / (self.appname + '.d') / ('uhu' + ext)
            exp_method = ext_methods[ext]
            LOG.debug("Checking for existence of detected cfg file {!r}.".format(str(path)))
            if path.exists():
                self.assertIn(path, cfg.config_files)
                LOG.debug("Checking method {m!r} of cfg file {f!r}.".format(
                    m=exp_method, f=str(path)))
                found_method = cfg.config_file_methods[path]
                LOG.debug("Found method: {!r}".format(found_method))
                self.assertEqual(exp_method, found_method)
            else:
                self.assertNotIn(path, cfg.config_files)
                LOG.debug("Not existing file {!r} not in cfg.config_files.".format(path))

    # -------------------------------------------------------------------------
    def test_read_cfg_files(self):

        if self.verbose >= 1:
            print()

        LOG.info("Testing reading of configuration files.")

        from fb_tools.multi_config import BaseMultiConfig

        cfg = BaseMultiConfig(
            appname=self.appname, config_dir=self.test_cfg_dir.name,
            additional_cfgdirs=self.test_cfg_dir, verbose=self.verbose)
        if self.verbose >= 2:
            LOG.debug("Current configuration directories:\n{}".format(pp(cfg.config_dirs)))

        cfg.read()

        if self.verbose > 1:
            LOG.debug("Read raw configs:\n" + pp(cfg.configs_raw))

    # -------------------------------------------------------------------------
    def test_read_charset(self):

        if self.verbose >= 1:
            print()

        LOG.info("Testing reading of configuration files with different charcter sets.")

        from fb_tools.multi_config import BaseMultiConfig

        test_stems = (
            'test_multicfg-latin1', 'test_multicfg-utf-16',
            'test_multicfg-utf-32', 'test_multicfg-utf8')

        for stem in test_stems:

            if self.verbose:
                print()
            LOG.info("Testing for file stem {!r} ...".format(stem))

            cfg = BaseMultiConfig(
                appname=self.appname, config_dir=self.test_cfg_dir.name,
                additional_cfgdirs=self.test_cfg_dir, verbose=self.verbose,
                append_appname_to_stems=False, additional_stems=stem)

            cfg.read()
            LOG.info('Read config:\n' + pp(cfg.cfg))

    # -------------------------------------------------------------------------
    def test_read_broken(self):

        if self.verbose >= 1:
            print()

        LOG.info("Testing reading of broken configuration files.")

        from fb_tools.multi_config import BaseMultiConfig, MultiCfgParseError

        test_stems = (
            'test_multicfg-broken-ini',
            'test_multicfg-broken-json',
            'test_multicfg-broken-hjson',
            'test_multicfg-broken-yaml',
            'test_multicfg-broken-toml',
        )

        for stem in test_stems:

            if self.verbose:
                print()
            LOG.info("Testing for file stem {!r} ...".format(stem))

            with self.assertRaises(MultiCfgParseError) as cm:
                cfg = BaseMultiConfig(
                    appname=self.appname, config_dir=self.test_cfg_dir.name,
                    additional_cfgdirs=self.test_cfg_dir, verbose=self.verbose,
                    append_appname_to_stems=False, additional_stems=stem)

                cfg.read()
                LOG.info('Read config:\n' + pp(cfg.cfg))
            e = cm.exception
            LOG.info("{c} raised on stem {s!r}: {e}".format(c=e.__class__.__name__, s=stem, e=e))

    # -------------------------------------------------------------------------
    def test_evaluation(self):

        if self.verbose >= 1:
            print()

        LOG.info("Testing evaluation configuration.")

        from fb_tools.multi_config import BaseMultiConfig

        test_stem = 'test_multicfg-verbose'
        test_logfile = Path('/var/log/test-multiconfig.log')

        used_verbose = self.verbose
        if self.verbose > 3:
            used_verbose = 3

        cfg = BaseMultiConfig(
            appname=self.appname, config_dir=self.test_cfg_dir.name,
            additional_cfgdirs=self.test_cfg_dir, verbose=used_verbose,
            append_appname_to_stems=False, additional_stems=test_stem)

        LOG.debug("Testing raising RuntimeError on unread configuration ...")
        with self.assertRaises(RuntimeError) as cm:
            cfg.eval()
        e = cm.exception
        LOG.info("{c} raised on unread configuration: {e}".format(
            c=e.__class__.__name__, e=e))

        LOG.debug("Reading verbose level from configuration.")
        cfg.read()
        LOG.info('Read config:\n' + pp(cfg.cfg))
        cfg.eval()
        LOG.debug("New debug level: {!r}.".format(cfg.verbose))
        LOG.debug("Evaluated logfile: {!r}.".format(cfg.logfile))
        self.assertEqual(cfg.verbose, 7)
        self.assertEqual(cfg.logfile, test_logfile)

    # -------------------------------------------------------------------------
    def test_additional_config_file(self):

        if self.verbose >= 1:
            print()

        LOG.info("Test performing additional config file.")

        from fb_tools.multi_config import BaseMultiConfig, MultiConfigError

        test_stem = 'test_multicfg-add'
        test_add_config = self.test_cfg_dir / 'test_multicfg-additional.ini'

        LOG.debug("Using {!r} as dditional config file.".format(str(test_add_config)))

        LOG.info("Testing appending additional config file given as parameter.")
        cfg = BaseMultiConfig(
            appname=self.appname, config_dir=self.test_cfg_dir.name,
            additional_cfgdirs=self.test_cfg_dir, verbose=self.verbose,
            append_appname_to_stems=True, additional_stems=test_stem,
            additional_config_file=str(test_add_config))
        cfg.collect_config_files()
        if self.verbose >= 2:
            LOG.debug("Found configuration files:\n{}".format(pp(cfg.config_files)))
        self.assertIn(test_add_config, cfg.config_files)
        self.assertEqual(test_add_config, cfg.config_files[-1])

        LOG.info("Testing appending additional config file by class property.")
        cfg = BaseMultiConfig(
            appname=self.appname, config_dir=self.test_cfg_dir.name,
            additional_cfgdirs=self.test_cfg_dir, verbose=self.verbose,
            append_appname_to_stems=True, additional_stems=test_stem)
        cfg.additional_config_file = str(test_add_config)
        cfg.collect_config_files()
        if self.verbose >= 2:
            LOG.debug("Found configuration files:\n{}".format(pp(cfg.config_files)))
        self.assertIn(test_add_config, cfg.config_files)
        self.assertEqual(test_add_config, cfg.config_files[-1])

        LOG.info("Testing appending additional config file by method append_config_file().")
        cfg = BaseMultiConfig(
            appname=self.appname, config_dir=self.test_cfg_dir.name,
            additional_cfgdirs=self.test_cfg_dir, verbose=self.verbose,
            append_appname_to_stems=True, additional_stems=test_stem)
        cfg.collect_config_files()
        cfg.append_config_file(test_add_config)
        if self.verbose >= 2:
            LOG.debug("Found configuration files:\n{}".format(pp(cfg.config_files)))
        self.assertIn(test_add_config, cfg.config_files)
        self.assertEqual(test_add_config, cfg.config_files[-1])

        LOG.info("Testing prepending additional config file by method prepend_config_file().")
        cfg = BaseMultiConfig(
            appname=self.appname, config_dir=self.test_cfg_dir.name,
            additional_cfgdirs=self.test_cfg_dir, verbose=self.verbose,
            append_appname_to_stems=True, additional_stems=test_stem)
        cfg.collect_config_files()
        cfg.prepend_config_file(test_add_config)
        if self.verbose >= 2:
            LOG.debug("Found configuration files:\n{}".format(pp(cfg.config_files)))
        self.assertIn(test_add_config, cfg.config_files)
        self.assertEqual(test_add_config, cfg.config_files[0])

        LOG.info("Testing wrong config file.")
        wrong_configs = (
            '/this/should/not/exists',
            '/dev',
            '/etc/shadow',
            str(self.test_cfg_dir / 'test_multicfg-additional.uhu'),
        )
        cfg = BaseMultiConfig(
            appname=self.appname, config_dir=self.test_cfg_dir.name,
            additional_cfgdirs=self.test_cfg_dir, verbose=self.verbose,
            append_appname_to_stems=False, additional_stems=test_stem)

        for test_add_config in wrong_configs:
            LOG.debug("Testing not usable config file {!r} ...".format(test_add_config))
            with self.assertRaises(MultiConfigError) as cm:
                cfg.additional_config_file = test_add_config
                cfg.collect_config_files()
            e = cm.exception
            LOG.debug("{c} raised on not usable config file {fn!r}: {e}".format(
                c=e.__class__.__name__, fn=test_add_config, e=e))

    # -------------------------------------------------------------------------
    def test_checking_privacy(self):

        if self.verbose >= 1:
            print()

        LOG.info("Testing check privacy ...")

        from fb_tools.multi_config import BaseMultiConfig, MultiConfigError

        source_file = self.test_cfg_dir / 'test_multicfg.ini'
        content = source_file.read_bytes()
        test_stem = 'test_multicfg-uhu'

        mode_private = stat.S_IRUSR | stat.S_IWUSR
        mode_public = mode_private | stat.S_IRGRP | stat.S_IROTH
        LOG.debug("Using modes private '{priv:04o}' and public '{pub:04o}'.".format(
            priv=mode_private, pub=mode_public))

        cfg = BaseMultiConfig(
            appname=self.appname, config_dir=self.test_cfg_dir.name,
            additional_cfgdirs=self.test_cfg_dir, verbose=self.verbose,
            append_appname_to_stems=False, additional_stems=test_stem,
            ensure_privacy=True)

        with tempfile.NamedTemporaryFile(
                mode="w+b", buffering=0, prefix='test_multicfg-', suffix='.ini',
                dir=str(self.test_cfg_dir)) as fh:
            cfg_file = Path(fh.name)
            if self.verbose > 1:
                LOG.debug("Using temporary file {!r} ...".format(str(cfg_file)))
            fh.write(content)

            LOG.debug("Testing privacy with a private config file ...")
            os.chmod(cfg_file, mode_private)
            cfg.additional_config_file = cfg_file
            cfg.collect_config_files()

            LOG.debug("Testing privacy with a public config file ...")
            os.chmod(cfg_file, mode_public)
            with self.assertRaises(MultiConfigError) as cm:
                cfg.check_privacy()
            e = cm.exception
            LOG.info("{c} raised on public visible config file: {e}".format(
                c=e.__class__.__name__, e=e))


# =============================================================================
if __name__ == '__main__':

    verbose = get_arg_verbose()
    if verbose is None:
        verbose = 0
    init_root_logger(verbose)

    LOG.info("Starting tests ...")

    suite = unittest.TestSuite()

    suite.addTest(TestFbMultiConfig('test_import', verbose))
    suite.addTest(TestFbMultiConfig('test_object', verbose))
    suite.addTest(TestFbMultiConfig('test_init_cfg_dirs', verbose))
    suite.addTest(TestFbMultiConfig('test_init_stems', verbose))
    suite.addTest(TestFbMultiConfig('test_collect_cfg_files', verbose))
    suite.addTest(TestFbMultiConfig('test_read_cfg_files', verbose))
    suite.addTest(TestFbMultiConfig('test_read_charset', verbose))
    suite.addTest(TestFbMultiConfig('test_read_broken', verbose))
    suite.addTest(TestFbMultiConfig('test_evaluation', verbose))
    suite.addTest(TestFbMultiConfig('test_additional_config_file', verbose))
    suite.addTest(TestFbMultiConfig('test_checking_privacy', verbose))

    runner = unittest.TextTestRunner(verbosity=verbose)

    result = runner.run(suite)


# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
