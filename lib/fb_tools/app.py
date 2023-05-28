#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@summary: The module for a base application object.

@author: Frank Brehm
@contact: frank@brehm-online.com
@copyright: © 2022 by Frank Brehm, Berlin
"""
from __future__ import absolute_import

# Standard modules
import argparse
import copy
import getpass
import logging
import os
import re
import signal
import sys
import time
import traceback

# Third party modules

# Own modules
from fb_logging.colored import ColoredFormatter

from . import __version__ as __pkg_version__
from .argparse_actions import TimeoutOptionAction
from .common import terminal_can_colors
from .errors import FbAppError
from .errors import FunctionNotImplementedError
from .handling_obj import HandlingObject
from .xlate import DOMAIN, LOCALE_DIR, XLATOR
from .xlate import __base_dir__ as __xlate_base_dir__
from .xlate import __mo_file__ as __xlate_mo_file__
from .xlate import __module_dir__ as __xlate_module_dir__

__version__ = '2.2.2'
LOG = logging.getLogger(__name__)

SIGNAL_NAMES = {
    signal.SIGHUP: 'HUP',
    signal.SIGINT: 'INT',
    signal.SIGABRT: 'ABRT',
    signal.SIGTERM: 'TERM',
    signal.SIGKILL: 'KILL',
    signal.SIGQUIT: 'QUIT',
    signal.SIGUSR1: 'USR1',
    signal.SIGUSR2: 'USR2',
}

_ = XLATOR.gettext


# =============================================================================
class BaseApplication(HandlingObject):
    """Class for the base application objects."""

    re_prefix = re.compile(r'^[a-z0-9][a-z0-9_]*$', re.IGNORECASE)
    re_anum = re.compile(r'[^A-Z0-9_]+', re.IGNORECASE)

    default_force_desc_msg = _('Forced execution - whatever it means.')

    show_assume_options = False
    show_console_timeout_option = False
    show_force_option = False
    show_simulate_option = True

    # -------------------------------------------------------------------------
    def __init__(
        self, appname=None, verbose=0, version=__pkg_version__, base_dir=None, quiet=False,
            terminal_has_colors=False, simulate=None, force=None, assumed_answer=None,
            initialized=False, usage=None, description=None,
            argparse_epilog=None, argparse_prefix_chars='-', env_prefix=None):
        """Initialise a BaseApplication object."""
        self.arg_parser = None
        """
        @ivar: argparser object to parse commandline parameters
        @type: argparse.ArgumentParser
        """

        self.args = None
        """
        @ivar: an object containing all commandline parameters
               after parsing them
        @type: Namespace
        """

        self._exit_value = 0
        """
        @ivar: return value of the application for exiting with sys.exit().
        @type: int
        """

        self._usage = usage
        """
        @ivar: usage text used on argparse
        @type: str
        """

        self._description = description
        """
        @ivar: a short text describing the application
        @type: str
        """

        self._argparse_epilog = argparse_epilog
        """
        @ivar: an epilog displayed at the end of the argparse help screen
        @type: str
        """

        self._argparse_prefix_chars = argparse_prefix_chars
        """
        @ivar: The set of characters that prefix optional arguments.
        @type: str
        """

        self.env = {}
        """
        @ivar: a dictionary with all application specifiv environment variables,
               they will detected by the env_prefix property of this object,
               and their names will transformed before saving their values in
               self.env by removing the env_prefix from the variable name.
        @type: dict
        """

        self._env_prefix = None
        """
        @ivar: a prefix for environment variables to detect them and to assign
               their transformed names and their values in self.env
        @type: str
        """

        super(BaseApplication, self).__init__(
            appname=appname, verbose=verbose, version=version, base_dir=base_dir,
            quiet=quiet, simulate=simulate, force=force, assumed_answer=assumed_answer,
            terminal_has_colors=terminal_has_colors, initialized=False,
        )

        if env_prefix:
            ep = str(env_prefix).strip()
            if not ep:
                msg = _('Invalid env_prefix {!r} given - it may not be empty.').format(env_prefix)
                raise FbAppError(msg)
            match = self.re_prefix.search(ep)
            if not match:
                msg = _(
                    'Invalid characters found in env_prefix {!r}, only '
                    'alphanumeric characters and digits and underscore '
                    '(this not as the first character) are allowed.').format(env_prefix)
                raise FbAppError(msg)
            self._env_prefix = ep
        else:
            ep = self.appname.upper() + '_'
            self._env_prefix = self.re_anum.sub('_', ep)

        if not self.description:
            self._description = _('Unknown and undescriped application.')

        if not hasattr(self, '_force_desc_msg'):
            self._force_desc_msg = self.default_force_desc_msg

        self._init_arg_parser()
        self._perform_arg_parser()

        self._init_env()
        self._perform_env()

        self.post_init()

    # -----------------------------------------------------------
    @property
    def exit_value(self):
        """Get the return value of the application for exiting with sys.exit()."""
        return self._exit_value

    @exit_value.setter
    def exit_value(self, value):
        v = int(value)
        if v >= 0:
            self._exit_value = v
        else:
            LOG.warning(_('Wrong exit_value {!r}, must be >= 0.').format(value))

    # -----------------------------------------------------------
    @property
    def force_desc_msg(self):
        """Get the help text for the --force command line option."""
        msg = getattr(self, '_force_desc_msg', None)
        if not msg:
            msg = self.default_force_desc_msg
        return msg

    # -----------------------------------------------------------
    @property
    def exitvalue(self):
        """Get the return value of the application for exiting with sys.exit()."""
        return self._exit_value

    @exitvalue.setter
    def exitvalue(self, value):
        self._exit_value = int(value)

    # -----------------------------------------------------------
    @property
    def usage(self):
        """Get the usage text used on argparse."""
        return self._usage

    # -----------------------------------------------------------
    @property
    def description(self):
        """Get a short text describing the application."""
        return self._description

    # -----------------------------------------------------------
    @property
    def argparse_epilog(self):
        """Get the epilog displayed at the end of the argparse help screen."""
        return self._argparse_epilog

    # -----------------------------------------------------------
    @property
    def argparse_prefix_chars(self):
        """Get the set of characters that prefix optional arguments."""
        return self._argparse_prefix_chars

    # -----------------------------------------------------------
    @property
    def env_prefix(self):
        """Get a prefix for environment variables to detect them."""
        return self._env_prefix

    # -----------------------------------------------------------
    @property
    def usage_term(self):
        """Get the localized version of 'usage: '."""
        return 'Usage: '

    # -----------------------------------------------------------
    @property
    def usage_term_len(self):
        """Get the length of the localized version of 'usage: '."""
        return len(self.usage_term)

    # -------------------------------------------------------------------------
    def exit(self, retval=-1, msg=None, trace=False):                       # noqa A003
        """
        Exit the current application.

        Universal method to call sys.exit(). If fake_exit is set, a
        FakeExitError exception is raised instead (useful for unittests.)

        @param retval: the return value to give back to theoperating system
        @type retval: int
        @param msg: a last message, which should be emitted before exit.
        @type msg: str
        @param trace: flag to output a stack trace before exiting
        @type trace: bool

        @return: None

        """
        retval = int(retval)
        trace = bool(trace)

        root_logger = logging.getLogger()
        has_handlers = False
        if root_logger.handlers:
            has_handlers = True

        if msg:
            if has_handlers:
                if retval:
                    LOG.error(msg)
                else:
                    LOG.info(msg)
            if not has_handlers:
                if hasattr(sys.stderr, 'buffer'):
                    sys.stderr.buffer.write(str(msg) + '\n')
                else:
                    sys.stderr.write(str(msg) + '\n')

        if trace:
            if has_handlers:
                if retval:
                    LOG.error(traceback.format_exc())
                else:
                    LOG.info(traceback.format_exc())
            else:
                traceback.print_exc()

        sys.exit(retval)

    # -------------------------------------------------------------------------
    def as_dict(self, short=True):
        """
        Transform the elements of the object into a dict.

        @param short: don't include local properties in resulting dict.
        @type short: bool

        @return: structure as dict
        @rtype:  dict
        """
        res = super(BaseApplication, self).as_dict(short=short)
        res['argparse_epilog'] = self.argparse_epilog
        res['argparse_prefix_chars'] = self.argparse_prefix_chars
        res['args'] = copy.copy(self.args.__dict__)
        res['description'] = self.description
        res['env_prefix'] = self.env_prefix
        res['exit_value'] = self.exit_value
        res['force_desc_msg'] = self.force_desc_msg
        res['show_assume_options'] = self.show_assume_options
        res['show_console_timeout_option'] = self.show_console_timeout_option
        res['show_force_option'] = self.show_force_option
        res['show_simulate_option'] = self.show_simulate_option
        res['usage'] = self.usage
        if 'xlate' not in res:
            res['xlate'] = {}
        res['xlate']['fb_tools'] = {
            '__module_dir__': __xlate_module_dir__,
            '__base_dir__': __xlate_base_dir__,
            'LOCALE_DIR': LOCALE_DIR,
            'DOMAIN': DOMAIN,
            '__mo_file__': __xlate_mo_file__,
        }

        return res

    # -------------------------------------------------------------------------
    def init_logging(self):
        """
        Initialize the logger object.

        It creates a colored loghandler with all output to STDERR.
        Maybe overridden in descendant classes.

        @return: None
        """
        log_level = logging.INFO
        if self.verbose:
            log_level = logging.DEBUG
        root_loglevel = log_level
        if self.quiet:
            log_level = logging.WARNING

        root_logger = logging.getLogger()
        root_logger.setLevel(root_loglevel)

        # create formatter
        format_str = ''
        if self.verbose:
            format_str = '[%(asctime)s]: '
        format_str += self.appname + ': '
        if self.verbose:
            if self.verbose > 1:
                format_str += '%(name)s(%(lineno)d) %(funcName)s() '
            else:
                format_str += '%(name)s '
        format_str += '%(levelname)s - %(message)s'
        formatter = None
        if self.terminal_has_colors:
            formatter = ColoredFormatter(format_str)
        else:
            formatter = logging.Formatter(format_str)

        # create log handler for console output
        lh_console = logging.StreamHandler(sys.stderr)
        lh_console.setLevel(log_level)
        lh_console.setFormatter(formatter)

        root_logger.addHandler(lh_console)

        if self.verbose < 3:
            paramiko_logger = logging.getLogger('paramiko.transport')
            if self.verbose < 1:
                paramiko_logger.setLevel(logging.WARNING)
            else:
                paramiko_logger.setLevel(logging.INFO)

        return

    # -------------------------------------------------------------------------
    def terminal_can_color(self):
        """
        Detect, whether the current terminal is able to perform ANSI color sequences.

        This will be done for both stdout and stderr.

        @return: both stdout and stderr can perform ANSI color sequences
        @rtype: bool

        """
        term_debug = False
        if self.verbose > 3:
            term_debug = True
        return terminal_can_colors(debug=term_debug)

    # -------------------------------------------------------------------------
    def post_init(self):
        """
        Execute some actions after initialising.

        Here could be done some finishing actions after reading in
        commandline parameters, configuration a.s.o.

        This method could be overwritten by descendant classes, these
        methhods should allways include a call to post_init() of the
        parent class.

        """
        self.init_logging()

        self.perform_arg_parser()

    # -------------------------------------------------------------------------
    def get_secret(self, prompt, item_name):
        """Get a secret as input from console."""
        LOG.debug(_('Trying to get {} via console ...').format(item_name))

        # ------------------------
        def signal_handler(signum, frame):
            """
            React to an alarm signal.

            Handler as a callback function for getting a signal from somewhere.

            @param signum: the gotten signal number
            @type signum: int
            @param frame: the current stack frame
            @type frame: None or a frame object

            """
            signame = '{}'.format(signum)
            msg = _('Got a signal {}.').format(signum)
            if signum in SIGNAL_NAMES:
                signame = SIGNAL_NAMES[signum]
                msg = _('Got a signal {n!r} ({s}).').format(
                    n=signame, s=signum)
            LOG.debug(msg)

            if signum in (
                    signal.SIGHUP, signal.SIGINT, signal.SIGABRT,
                    signal.SIGTERM, signal.SIGKILL, signal.SIGQUIT):
                LOG.info(_('Exit on signal {n!r} ({s}).').format(
                    n=signame, s=signum))
                self.exit(1)

        # ------------------------
        old_handlers = {}

        if self.verbose > 2:
            LOG.debug(_('Tweaking signal handlers.'))
        for signum in (
                signal.SIGHUP, signal.SIGINT, signal.SIGABRT,
                signal.SIGTERM, signal.SIGQUIT):
            if self.verbose > 3:
                signame = SIGNAL_NAMES[signum]
                LOG.debug(_('Setting signal handler for {n!r} ({s}).').format(
                    n=signame, s=signum))
            old_handlers[signum] = signal.signal(signum, signal_handler)

        secret = None
        secret_repeat = None

        try:

            while True:

                p = _('Enter ') + prompt + ': '
                while True:
                    secret = getpass.getpass(prompt=p)
                    secret = secret.strip()
                    if secret != '':
                        break

                p = _('Repeat enter ') + prompt + ': '
                while True:
                    secret_repeat = getpass.getpass(prompt=p)
                    secret_repeat = secret_repeat.strip()
                    if secret_repeat != '':
                        break

                if secret == secret_repeat:
                    break

                LOG.error(_('{n} and repeated {n} did not match.').format(n=item_name))

        finally:
            if self.verbose > 2:
                LOG.debug(_('Restoring original signal handlers.'))
            for signum in old_handlers.keys():
                signal.signal(signum, old_handlers[signum])

        if self.force:
            LOG.debug(_('Got {n!r}: {s!r}').format(n=item_name, s=secret))

        return secret

    # -------------------------------------------------------------------------
    def pre_run(self):
        """
        Execute some actions before the main routine.

        This is a dummy method an could be overwritten by descendant classes.
        """
        pass

    # -------------------------------------------------------------------------
    def _run(self):
        """
        Execute the main actions of the application.

        Dummy function as main routine.

        MUST be overwritten by descendant classes.
        """
        raise FunctionNotImplementedError('_run()', self.__class__.__name__)

    # -------------------------------------------------------------------------
    def __call__(self):
        """
        Call the main run method.

        Helper method to make the resulting object callable, e.g.::

            app = PBApplication(...)
            app()

        @return: None

        """
        self.run()

    # -------------------------------------------------------------------------
    def run(self):
        """
        Execute the main actions of the application.

        The visible start point of this object.

        @return: None
        """
        if not self.initialized:
            self.handle_error(
                _('The application is not completely initialized.'), '', True)
            self.exit(9)

        try:
            self.pre_run()
        except Exception as e:
            self.handle_error(str(e), e.__class__.__name__, True)
            self.exit(98)

        if not self.initialized:
            raise FbAppError(
                _('Object {!r} seems not to be completely initialized.').format(
                    self.__class__.__name__))

        try:
            self._run()
        except Exception as e:
            self.handle_error(str(e), e.__class__.__name__, True)
            self.exit_value = 99

        if self.verbose > 1:
            LOG.info(_('Ending.'))

        try:
            self.post_run()
        except Exception as e:
            self.handle_error(str(e), e.__class__.__name__, True)
            self.exit_value = 97

        self.exit(self.exit_value)

    # -------------------------------------------------------------------------
    def post_run(self):
        """
        Execute some actions after the main routine.

        This is a dummy method an could be overwritten by descendant classes.
        """
        if self.verbose > 1:
            LOG.info(_('Executing {} ...').format('post_run()'))

    # -------------------------------------------------------------------------
    def _init_arg_parser(self):
        """
        Initialise the argument parser.

        Local called method to initiate the argument parser.

        @raise PBApplicationError: on some errors
        """
        self.arg_parser = argparse.ArgumentParser(
            prog=self.appname,
            description=self.description,
            usage=self.usage,
            epilog=self.argparse_epilog,
            prefix_chars=self.argparse_prefix_chars,
            add_help=False,
        )

        self.init_arg_parser()

        general_group = self.arg_parser.add_argument_group(_('General options'))

        if self.show_simulate_option:
            general_group.add_argument(
                '-s', '--simulate', action='store_true', dest='simulate',
                help=_('Simulation mode, nothing is really done.')
            )

        if self.show_force_option:
            general_group.add_argument(
                '-f', '--force', action='store_true', dest='force',
                help=self.force_desc_msg,
            )

        if self.show_assume_options:
            assume_group = general_group.add_mutually_exclusive_group()

            assume_group.add_argument(
                '--yes', '--assume-yes', action='store_true', dest='assume_yes',
                help=_("Automatically answer '{}' for all questions.").format(
                    self.colored(_('Yes'), 'CYAN'))
            )

            assume_group.add_argument(
                '--no', '--assume-no', action='store_true', dest='assume_no',
                help=_("Automatically answer '{}' for all questions.").format(
                    self.colored(_('No'), 'CYAN'))
            )

        if self.show_console_timeout_option:
            general_group.add_argument(
                '--console-timeout', metavar=_('SECONDS'), dest='console_timeout', type=int,
                action=TimeoutOptionAction, max_timeout=self.max_prompt_timeout,
                help=_('The timeout in seconds for console input. Default: {}').format(
                    self.default_prompt_timeout)
            )

        general_group.add_argument(
            '--color', action='store', dest='color', const='yes',
            default='auto', nargs='?', choices=['yes', 'no', 'auto'],
            help=_('Use colored output for messages.'),
        )

        verbose_group = general_group.add_mutually_exclusive_group()

        verbose_group.add_argument(
            '-v', '--verbose', action='count', dest='verbose',
            help=_('Increase the verbosity level'),
        )

        verbose_group.add_argument(
            '-q', '--quiet', action='store_true', dest='quiet',
            help=_('Silent execution, only warnings and errors are emitted.'),
        )

        general_group.add_argument(
            '-h', '--help', action='help', dest='help',
            help=_('Show this help message and exit.')
        )
        general_group.add_argument(
            '--usage', action='store_true', dest='usage',
            help=_('Display brief usage message and exit.')
        )
        v_msg = _('Version of %(prog)s: {}').format(self.version)
        general_group.add_argument(
            '-V', '--version', action='version', version=v_msg,
            help=_("Show program's version number and exit.")
        )

    # -------------------------------------------------------------------------
    def init_arg_parser(self):
        """
        Initialise the argument parser - the public available method.

        Note::
             avoid adding the general options '--verbose', '--help', '--usage'
             and '--version'. These options are allways added after executing
             this method.

        This is a dummy method an could be overwritten by descendant classes.
        """
        pass

    # -------------------------------------------------------------------------
    def _perform_arg_parser(self):
        """Parse the command line options."""
        self.args = self.arg_parser.parse_args()

        if hasattr(self.args, 'simulate'):
            self.simulate = getattr(self.args, 'simulate', True)

        if self.args.usage:
            self.arg_parser.print_usage(sys.stdout)
            self.exit(0)

        if self.args.verbose is not None and self.args.verbose > self.verbose:
            self.verbose = self.args.verbose

        if hasattr(self.args, 'force'):
            self.force = getattr(self.args, 'force', False)

        if hasattr(self.args, 'assume_yes'):
            if self.args.assume_yes:
                self.assumed_answer = True
        if hasattr(self.args, 'assume_no'):
            if self.args.assume_no:
                self.assumed_answer = False

        if self.args.quiet:
            self.quiet = self.args.quiet

        prompt_timeout = getattr(self.args, 'console_timeout', None)
        if prompt_timeout is not None:
            self.prompt_timeout = prompt_timeout

        if self.args.color == 'yes':
            self._terminal_has_colors = True
        elif self.args.color == 'no':
            self._terminal_has_colors = False
        else:
            self._terminal_has_colors = self.terminal_can_color()

    # -------------------------------------------------------------------------
    def perform_arg_parser(self):
        """
        Parse the command line options - public available method.

        This is a dummy method an could be overwritten by descendant classes.
        """
        pass

    # -------------------------------------------------------------------------
    def _init_env(self):
        """
        Initialise self.env by application specific environment variables.

        It calls self.init_env(), after it has done his job.
        """
        for (key, value) in list(os.environ.items()):

            if not key.startswith(self.env_prefix):
                continue

            newkey = key.replace(self.env_prefix, '', 1)
            self.env[newkey] = value

        self.init_env()

    # -------------------------------------------------------------------------
    def init_env(self):
        """
        Initialise self.env by application specific environment variables.

        Public available method to initiate self.env additional to the implicit
        initialization done by this module.
        Maybe it can be used to import environment variables, their
        names not starting with self.env_prefix.

        Currently a dummy method, which ca be overriden by descendant classes.
        """
        pass

    # -------------------------------------------------------------------------
    def _perform_env(self):
        """
        Do some useful things with the found environment.

        It calls self.perform_env(), after it has done his job.
        """
        # try to detect verbosity level from environment
        if 'VERBOSE' in self.env and self.env['VERBOSE']:
            v = 0
            try:
                v = int(self.env['VERBOSE'])
            except ValueError:
                v = 1
            if v > self.verbose:
                self.verbose = v

        self.perform_env()

    # -------------------------------------------------------------------------
    def perform_env(self):
        """
        Do some useful things with the found environment - public available method.

        This is a dummy method an could be overwritten by descendant classes.
        """
        pass

    # -------------------------------------------------------------------------
    def countdown(self, number=5, delay=1, prompt=None):
        """Perform a countdown at the console."""
        if prompt:
            prompt = str(prompt).strip()
        if not prompt:
            prompt = _('Starting in:')
        prompt = self.colored(prompt, 'YELLOW')

        try:
            if not self.force:
                i = number
                out = self.colored('%d' % (i), 'RED')
                msg = '\n{p} {o}'.format(p=prompt, o=out)
                sys.stdout.write(msg)
                sys.stdout.flush()
                while i > 0:
                    sys.stdout.write(' ')
                    sys.stdout.flush()
                    time.sleep(delay)
                    i -= 1
                    out = self.colored('{}'.format(i), 'RED')
                    sys.stdout.write(out)
                    sys.stdout.flush()
                sys.stdout.write('\n')
                sys.stdout.flush()
        except KeyboardInterrupt:
            sys.stderr.write('\n')
            LOG.warning(_('Aborted by user interrupt.'))
            sys.exit(99)

        go = self.colored('Go go go ...', 'GREEN')
        sys.stdout.write('\n%s\n\n' % (go))


# =============================================================================

if __name__ == '__main__':

    pass

# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 list
