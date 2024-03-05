#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@summary: The module for a base object with extended handling.

@author: Frank Brehm
@contact: frank.brehm@pixelpark.com
@copyright: © 2024 by Frank Brehm, Berlin
"""
from __future__ import absolute_import

# Standard modules
import copy
import datetime
import errno
import getpass
import ipaddress
import locale
import logging
import os
import re
import signal
import socket
import sys
try:
    import pathlib
except ImportError:
    import pathlib2 as pathlib
from shlex import quote
from subprocess import PIPE, Popen
if sys.version_info[0] >= 3:
    from subprocess import SubprocessError, TimeoutExpired
else:
    class SubprocessError(Exception):
        """Dummy exception for Python 2."""

        pass

    class TimeoutExpired(SubprocessError):
        """Dummy exception for Python 2."""

        pass

# Third party modules
from fb_logging.colored import colorstr

import six

# Own modules
from .common import caller_search_path, encode_or_bust, pp, to_bool, to_str
from .common import indent, is_sequence
from .errors import AbortAppError, TimeoutOnPromptError
from .errors import InterruptError, IoTimeoutError, ReadTimeoutError, WriteTimeoutError
from .obj import FbBaseObject
from .xlate import XLATOR, format_list

__version__ = '2.2.1'
LOG = logging.getLogger(__name__)

_ = XLATOR.gettext
ngettext = XLATOR.ngettext

DEFAULT_FILEIO_TIMEOUT = 2
DEFAULT_PROMPT_TIMEOUT = 30
DEFAULT_MAX_PROMPT_TIMEOUT = 600


# =============================================================================
class ProcessCommunicationTimeout(IoTimeoutError, SubprocessError):
    """Special exception class for process communication errors."""

    # -------------------------------------------------------------------------
    def __init__(self, timeout):
        """Initialise a ProcessCommunicationTimeout exception."""
        msg = _('Timeout on communicating with process.')
        super(ProcessCommunicationTimeout, self).__init__(msg, timeout)


# =============================================================================
class CalledProcessError(SubprocessError):
    """
    Raised when run() is called with check=True and the process returns a non-zero exit status.

    Attributes:
      cmd, returncode, stdout, stderr, output

    This class was taken from subprocess.py of the standard library of Python 3.5.
    """

    # -------------------------------------------------------------------------
    def __init__(self, returncode, cmd, output=None, stderr=None):
        """Initialise a CalledProcessError exception."""
        self.returncode = returncode
        self.cmd = cmd
        self.output = output
        self.stderr = stderr

    # -------------------------------------------------------------------------
    def __str__(self):
        """Typecast into string."""
        return _('Command {c!r} returned non-zero exit status {rc}.').format(
            c=self.cmd, rc=self.returncode)

    # -------------------------------------------------------------------------
    @property
    def stdout(self):
        """Alias for output attribute, to match stderr."""
        return self.output

    @stdout.setter
    def stdout(self, value):
        # There's no obvious reason to set this, but allow it anyway so
        # .stdout is a transparent alias for .output
        self.output = value


# =============================================================================
class TimeoutExpiredError(SubprocessError):
    """
    This exception is raised when the timeout expires while waiting for a child process.

    Attributes:
        cmd, output, stdout, stderr, timeout

    This class was taken from subprocess.py of the standard library of Python 3.5.
    """

    # -------------------------------------------------------------------------
    def __init__(self, cmd, timeout, output=None, stderr=None):
        """Initialise a TimeoutExpiredError exception."""
        self.cmd = cmd
        self.timeout = timeout
        self.output = output
        self.stderr = stderr

    # -------------------------------------------------------------------------
    def __str__(self):
        """Typecast into string."""
        msg = ngettext(
            'Command {c!r} timed out after {s} second.',
            'Command {c!r} timed out after {s} seconds.', self.timeout)
        return msg.format(c=self.cmd, s=self.timeout)

    # -------------------------------------------------------------------------
    @property
    def stdout(self):
        """Return self.output."""
        return self.output

    @stdout.setter
    def stdout(self, value):
        # There's no obvious reason to set this, but allow it anyway so
        # .stdout is a transparent alias for .output
        self.output = value


# =============================================================================
class HandlingObject(FbBaseObject):
    """Base class for an object with extend handling possibilities."""

    fileio_timeout = DEFAULT_FILEIO_TIMEOUT
    default_prompt_timeout = DEFAULT_PROMPT_TIMEOUT
    max_prompt_timeout = DEFAULT_MAX_PROMPT_TIMEOUT
    default_address_family = 'any'

    yes_list = ['y', 'yes']
    no_list = ['n', 'no']

    pattern_yes_no = r'^\s*(' + '|'.join(yes_list) + '|' + '|'.join(no_list) + r')?\s*$'
    re_yes_no = re.compile(pattern_yes_no, re.IGNORECASE)

    valid_address_families = ('any', socket.AF_INET, 'ipv4', socket.AF_INET6, 'ipv6')
    valid_address_families_out = ("'any'", 'socket.AF_INET', "'IPv4'", 'socket.AF_INET6', "'IPv6'")

    # -------------------------------------------------------------------------
    def __init__(
        self, version=__version__, quiet=False, terminal_has_colors=False,
            simulate=None, force=None, assumed_answer=None, *args, **kwargs):
        """Initialise a HandlingObject."""
        self.init_yes_no_lists()

        self._simulate = False
        self._force = False
        self._quiet = quiet
        self._assumed_answer = None
        self._address_family = self.default_address_family

        self.add_search_paths = []

        self._prompt_timeout = self.default_prompt_timeout

        self._terminal_has_colors = bool(terminal_has_colors)
        """
        @ivar: flag, that the current terminal understands color ANSI codes
        @type: bool
        """

        self.signals_dont_interrupt = [
            signal.SIGUSR1,
            signal.SIGUSR2,
        ]

        self._interrupted = False

        super(HandlingObject, self).__init__(
            version=version,
            *args, **kwargs,
        )

        if simulate is not None:
            self.simulate = simulate
        if force is not None:
            self.force = force
        if assumed_answer is not None:
            self.assumed_answer = assumed_answer

    # -----------------------------------------------------------
    @property
    def simulate(self):
        """Return whether simulation mode is enabled."""
        return self._simulate

    @simulate.setter
    def simulate(self, value):
        self._simulate = to_bool(value)

    # -----------------------------------------------------------
    @property
    def force(self):
        """Return whether some actions should be executed forced."""
        return self._force

    @force.setter
    def force(self, value):
        self._force = to_bool(value)

    # -----------------------------------------------------------
    @property
    def quiet(self):
        """Return whether the application should be executed quietly.

        Only warnings and errors are emitted.
        """
        return self._quiet

    @quiet.setter
    def quiet(self, value):
        self._quiet = bool(value)

    # -----------------------------------------------------------
    @property
    def assumed_answer(self):
        """Return the assuming of the answer to all questions.

        If None, no answer is assumed.
        If True, then assuming 'yes', if False, then assuming 'no'.
        """
        return getattr(self, '_assumed_answer', None)

    @assumed_answer.setter
    def assumed_answer(self, value):
        if value is None:
            self._assumed_answer = None
        else:
            self._assumed_answer = bool(value)

    # -----------------------------------------------------------
    @property
    def is_venv(self):
        """Return whether the current application is running inside a virtual environment."""
        if hasattr(sys, 'real_prefix'):
            return True
        return (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)

    # -----------------------------------------------------------
    @property
    def interrupted(self):
        """Return the flag indicating, that the current process was interrupted."""
        return self._interrupted

    # -----------------------------------------------------------
    @property
    def terminal_has_colors(self):
        """Return whether the current terminal understands color ANSI codes."""
        return self._terminal_has_colors

    @terminal_has_colors.setter
    def terminal_has_colors(self, value):
        self._terminal_has_colors = bool(value)

    # -----------------------------------------------------------
    @property
    def prompt_timeout(self):
        """Return the timeout in seconds for waiting for an answer on a prompt."""
        return getattr(self, '_prompt_timeout', self.default_prompt_timeout)

    @prompt_timeout.setter
    def prompt_timeout(self, value):
        v = int(value)
        if v < 0 or v > self.max_prompt_timeout:
            msg = _(
                'Wrong prompt timeout {v!r}, must be greater or equal to Null '
                'and less or equal to {max}.').format(v=value, max=self.max_prompt_timeout)
            LOG.warning(msg)
        else:
            self._prompt_timeout = v

    # -----------------------------------------------------------
    @property
    def address_family(self):
        """
        Get the used address family to use for resolving host names.

        Possible values are: 'any', socket.AF_INET, socket.AF_INET6
        """
        return self._address_family

    @address_family.setter
    def address_family(self, value):
        family = value
        if isinstance(family, str):
            family = value.lower()
        if value not in self.valid_address_families:
            msg = _('Wrong address family {!r} given. Valid values are:').format(value)
            msg += ' ' + format_list(self.valid_address_families_out)
            raise ValueError(msg)
        if family == 'ipv4':
            family = socket.AF_INET
        elif family == 'ipv6':
            family = socket.AF_INET6
        self._address_family = family

    # -------------------------------------------------------------------------
    @classmethod
    def init_yes_no_lists(cls):
        """Initialise the lists for 'yes'- and 'no'-values by localized values."""
        yes = _('yes')
        if yes not in cls.yes_list:
            cls.yes_list.append(yes)
        yes_fc = yes[0]
        if yes_fc not in cls.yes_list:
            cls.yes_list.append(yes_fc)

        no = _('no')
        if no not in cls.no_list and no not in cls.yes_list:
            cls.no_list.append(no)
        no_fc = no[0]
        if no_fc not in cls.no_list and no_fc not in cls.yes_list:
            cls.no_list.append(no_fc)

        cls.pattern_yes_no = (
            r'^\s*(' + '|'.join(cls.yes_list) + '|' + '|'.join(cls.no_list) + r')?\s*$')
        cls.re_yes_no = re.compile(cls.pattern_yes_no, re.IGNORECASE)

    # -------------------------------------------------------------------------
    def as_dict(self, short=True):
        """
        Transform the elements of the object into a dict.

        @param short: don't include local properties in resulting dict.
        @type short: bool

        @return: structure as dict
        @rtype:  dict
        """
        res = super(HandlingObject, self).as_dict(short=short)
        res['address_family'] = self.assumed_answer
        res['assumed_answer'] = self.assumed_answer
        res['fileio_timeout'] = self.fileio_timeout
        res['force'] = self.force
        res['interrupted'] = self.interrupted
        res['is_venv'] = self.is_venv
        res['no_list'] = self.no_list
        res['pattern_yes_no'] = self.pattern_yes_no
        res['prompt_timeout'] = self.prompt_timeout
        res['quiet'] = self.quiet
        res['simulate'] = self.simulate
        res['terminal_has_colors'] = self.terminal_has_colors
        res['yes_list'] = self.yes_list

        return res

    # -------------------------------------------------------------------------
    def get_address_famlily_int(self, address_family):
        """Transform the given address family into an integer value (4, 6 or 0)."""
        family = address_family
        if isinstance(address_family, str):
            family = address_family.lower()

        if family not in self.valid_address_families:
            msg = _('Wrong address family {!r} given. Valid values are:').format(address_family)
            msg += ' ' + format_list(['None'] + self.valid_address_families_out)
            raise ValueError(msg)

        if family is None:
            family = self.address_family

        if family == 'any':
            return 0
        elif family == 'ipv4':
            return socket.AF_INET
        elif family == 'ipv6':
            return socket.AF_INET6

        return address_family

    # -------------------------------------------------------------------------
    def get_address(self, host, address_family=None):
        """
        Try to resolve the addresses of the given hostname and returns them as a list.

        @param host: the hostname to resolve.
        @param address_family: Limit the result to the addresses of the given address family.
        """
        af = self.get_address_famlily_int(address_family)

        try:
            address = ipaddress.ip_address(host)
            if af == socket.AF_INET and address.version == 6:
                return []
            if af == socket.AF_INET6 and address.version == 4:
                return []
            return [address]
        except ValueError:
            pass

        addresses = []
        addr_infos = socket.getaddrinfo(host, None, family=af)
        for addr_info in addr_infos:
            got_af = addr_info[0]
            if af and got_af != af:
                continue
            addr = ipaddress.ip_address(addr_info[4][0])
            if addr not in addresses:
                addresses.append(addr)

        return addresses

    # -------------------------------------------------------------------------
    def get_cmd(self, cmd, quiet=False):
        """Search the OS search path for the given command."""
        return self.get_command(cmd, quiet=quiet)

    # -------------------------------------------------------------------------
    def get_command(self, cmd, quiet=False, resolve=False):
        """
        Search the OS search path for the given command.

        Gives back the normalized position of this command.
        If the command is given as an absolute path, it check the existence
        of this command.

        @param cmd: the command to search
        @type cmd: str
        @param quiet: No warning message, if the command could not be found, only a debug message
        @type quiet: bool
        @param resolve: Resolving the path to the executable by resolving any symlinks.
                        Search paths are always resolved.
        @type resolve: bool

        @return: normalized complete path of this command, or None,
                 if not found
        @rtype: str or None

        """
        cmd = pathlib.Path(cmd)

        if self.verbose > 2:
            LOG.debug(_('Searching for command {!r} ...').format(str(cmd)))

        # Checking an absolute path
        if cmd.is_absolute():
            if not cmd.exists():
                LOG.warning(_("Command {!r} doesn't exists.").format(str(cmd)))
                return None
            if not os.access(str(cmd), os.X_OK):
                msg = _('Command {!r} is not executable.').format(str(cmd))
                LOG.warning(msg)
                return None
            if resolve:
                return cmd.resolve()
            return cmd

        additional_paths = []
        if self.add_search_paths and is_sequence(self.add_search_paths):
            additional_paths = copy.copy(self.add_search_paths)

        # Checking a relative path
        for d in caller_search_path(*additional_paths):
            if self.verbose > 3:
                LOG.debug(_('Searching command in {!r} ...').format(str(d)))
            p = d / cmd
            if p.exists():
                if self.verbose > 2:
                    LOG.debug('Found {!r} ...'.format(str(p)))
                if os.access(str(p), os.X_OK):
                    if resolve:
                        return p.resolve()
                    return p
                else:
                    LOG.debug(_('Command {!r} is not executable.').format(str(p)))

        # command not found, sorry
        msg = _('Command {!r} not found.').format(str(cmd))
        if quiet:
            if self.verbose > 2:
                LOG.debug(msg)
        else:
            LOG.warning(msg)

        return None

    # -------------------------------------------------------------------------
    def run(self, *popenargs, **kwargs):
        """
        Run command with arguments and return a CompletedProcess instance.

        The returned instance will have attributes args, returncode, stdout and
        stderr. By default, stdout and stderr are not captured, and those attributes
        will be None. Pass stdout=PIPE and/or stderr=PIPE in order to capture them.

        If check is True and the exit code was non-zero, it raises a
        CalledProcessError. The CalledProcessError object will have the return code
        in the returncode attribute, and output & stderr attributes if those streams
        were captured.

        If timeout is given, and the process takes too long, a TimeoutExpiredError
        exception will be raised.

        There is an optional argument "input", allowing you to
        pass a string to the subprocess's stdin.  If you use this argument
        you may not also use the Popen constructor's "stdin" argument, as
        it will be used internally.

        The other arguments are the same as for the Popen constructor.

        If universal_newlines=True is passed, the "input" argument must be a
        string and stdout/stderr in the returned object will be strings rather than
        bytes.

        This method was taken from subprocess.py of the standard library of Python 3.5.
        """
        inp = None
        if 'input' in kwargs:
            inp = kwargs['input']
            del kwargs['input']

        timeout = None
        if 'timeout' in kwargs:
            timeout = kwargs['timeout']
            del kwargs['timeout']

        check = False
        if 'check' in kwargs:
            check = bool(kwargs['check'])
            del kwargs['check']

        may_simulate = None
        if 'may_simulate' in kwargs:
            may_simulate = bool(kwargs['may_simulate'])
            del kwargs['may_simulate']

        if self.verbose >= 2:
            myargs = {
                'input': inp,
                'timeout': timeout,
                'check': check,
                'may_simulate': may_simulate,
                'popenargs': popenargs,
                'kwargs': kwargs,
            }
            LOG.debug('Args of run():\n{}'.format(pp(myargs)))

        if inp is not None:
            if 'stdin' in kwargs:
                raise ValueError(_('STDIN and input arguments may not both be used.'))
            kwargs['stdin'] = PIPE

        LOG.debug(_('Executing command args:') + '\n' + pp(popenargs))
        cmd_args = []
        for arg in popenargs[0]:
            LOG.debug(_('Performing argument {!r}.').format(arg))
            cmd_args.append(quote(arg))
        cmd_str = ' '.join(cmd_args)

        cmd_str = ' '.join((quote(x) for x in popenargs[0]))
        LOG.debug(_('Executing: {}').format(cmd_str))

        if may_simulate and self.simulate:
            LOG.info(_('Simulation mode, not executing: {}').format(cmd_str))
            return CompletedProcess(popenargs, 0, 'Simulated execution.\n', '')

        process = None
        try:
            start_dt = datetime.datetime.now()
            process = Popen(*popenargs, **kwargs)
            if self.verbose > 0:
                LOG.debug(_('PID of process: {}').format(process.pid))
            try:
                stdout, stderr = self._communicate(
                    process, popenargs, inp=inp, timeout=timeout)
            except Exception as e:
                if self.verbose > 2:
                    LOG.debug(_('{c} happened, killing process: {e}').format(
                        c=e.__class__.__name__, e=e))
                process.poll()
                if process.returncode is None:
                    process.kill()
                process.wait()
                raise
            retcode = process.poll()
            if check and retcode:
                if six.PY3:
                    raise CalledProcessError(retcode, process.args, output=stdout, stderr=stderr)
                raise CalledProcessError(retcode, popenargs, output=stdout, stderr=stderr)
        finally:
            if process:
                if process.stdout:
                    process.stdout.close()
                if process.stderr:
                    process.stderr.close()
                if process.stdin:
                    try:
                        process.stdin.close()
                    finally:
                        pass

        end_dt = datetime.datetime.now()
        if six.PY3:
            return CompletedProcess(
                process.args, retcode, stdout, stderr, start_dt=start_dt, end_dt=end_dt)
        else:
            return CompletedProcess(
                popenargs, retcode, stdout, stderr, start_dt=start_dt, end_dt=end_dt)

    # -------------------------------------------------------------------------
    def _communicate(self, process, popenargs, inp=None, timeout=None):

        try:

            if timeout is None:
                return process.communicate(inp)

            def communicate_alarm_caller(signum, sigframe):
                err = InterruptError(signum)
                self.handle_info(str(err))
                process.kill()
                raise ProcessCommunicationTimeout(timeout)

            signal.signal(signal.SIGALRM, communicate_alarm_caller)
            signal.alarm(timeout)

            stdout, stderr = process.communicate(inp)

            signal.alarm(0)

        except TimeoutExpired:
            stdout, stderr = process.communicate()
            raise TimeoutExpiredError(popenargs, timeout, output=stdout, stderr=stderr)

        except ProcessCommunicationTimeout:
            stdout, stderr = process.communicate()
            signal.alarm(0)
            raise TimeoutExpiredError(popenargs, timeout, output=stdout, stderr=stderr)

        return (stdout, stderr)

    # -------------------------------------------------------------------------
    def colored(self, msg, color):
        """
        Colorize the given string somehow.

        Wrapper function to colorize the message. Depending, whether the current
        terminal can display ANSI colors, the message is colorized or not.

        @param msg: The message to colorize
        @type msg: str
        @param color: The color to use, must be one of the keys of COLOR_CODE
        @type color: str

        @return: the colorized message
        @rtype: str

        """
        if not self.terminal_has_colors:
            return msg
        return colorstr(msg, color)

    # -------------------------------------------------------------------------
    def signal_handler(self, signum, frame):
        """
        Do some actions on a signal.

        Handler as a callback function for getting a signal from somewhere.

        @param signum: the gotten signal number
        @type signum: int
        @param frame: the current stack frame
        @type frame: None or a frame object

        """
        err = InterruptError(signum)

        if signum in self.signals_dont_interrupt:
            self.handle_info(str(err))
            LOG.info(_('Nothing to do on signal.'))
            return

        self._interrupted = True
        raise err

    # -------------------------------------------------------------------------
    def read_file(
            self, filename, timeout=None, binary=False, quiet=False, encoding='utf-8'):
        """
        Read the content of the given filename.

        @raise IOError: if file doesn't exists or isn't readable
        @raise PbReadTimeoutError: on timeout reading the file

        @param filename: name of the file to read
        @type filename: str
        @param timeout: the amount in seconds when this method should timeout
        @type timeout: int
        @param binary: Read the file as binary data.
        @type binary: bool
        @param quiet: increases the necessary verbosity level to
                      put some debug messages
        @type quiet: bool

        @return: file content
        @rtype:  str

        """
        needed_verbose_level = 1
        if quiet:
            needed_verbose_level = 3

        def read_alarm_caller(signum, sigframe):
            """
            Raise a ReadTimeoutError on an alarm event.

            This nested function will be called in event of a timeout.

            @param signum:   the signal number (POSIX) which happend
            @type signum:    int
            @param sigframe: the frame of the signal
            @type sigframe:  object
            """
            raise ReadTimeoutError(timeout, filename)

        if timeout is None:
            timeout = self.fileio_timeout

        timeout = abs(int(timeout))
        ifile = str(filename)

        if not os.path.isfile(ifile):
            raise IOError(
                errno.ENOENT, _("File doesn't exists."), ifile)
        if not os.access(ifile, os.R_OK):
            raise IOError(
                errno.EACCES, _('Read permission denied.'), ifile)

        if self.verbose > needed_verbose_level:
            LOG.debug(_('Reading file content of {!r} ...').format(ifile))

        signal.signal(signal.SIGALRM, read_alarm_caller)
        signal.alarm(timeout)

        open_args = {}
        if six.PY3 and not binary:
            open_args['encoding'] = encoding
            open_args['errors'] = 'surrogateescape'

        mode = 'r'
        content = ''
        if binary:
            mode += 'b'
            content = encode_or_bust('')

        with open(ifile, mode, **open_args) as fh:
            for line in fh.readlines():
                content += line
            fh.close()

        signal.alarm(0)

        if six.PY2 and not binary:
            content = content.decode(encoding, 'replace')

        return content

    # -------------------------------------------------------------------------
    def write_file(
            self, filename, content, timeout=None, must_exists=True,
            quiet=False, encoding='utf-8'):
        """
        Write the given content into the given filename.

        It should only be used for small things, because it writes unbuffered.

        @raise IOError: if file doesn't exists or isn't writeable
        @raise WriteTimeoutError: on timeout writing into the file

        @param filename: name of the file to write
        @type filename: str
        @param content: the content to write into the file
        @type content: str
        @param timeout: the amount in seconds when this method should timeout
        @type timeout: int
        @param must_exists: the file must exists before writing
        @type must_exists: bool
        @param quiet: increases the necessary verbosity level to
                      put some debug messages
        @type quiet: bool

        @return: None
        """

        def write_alarm_caller(signum, sigframe):
            """
            Raise a WriteTimeoutError on a alarm event.

            This nested function will be called in event of a timeout

            @param signum:   the signal number (POSIX) which happend
            @type signum:    int
            @param sigframe: the frame of the signal
            @type sigframe:  object
            """
            raise WriteTimeoutError(timeout, filename)

        verb_level1 = 0
        verb_level2 = 1
        verb_level3 = 3
        if quiet:
            verb_level1 = 2
            verb_level2 = 3
            verb_level3 = 4

        if timeout is None:
            timeout = self.fileio_timeout
        timeout = abs(int(timeout))
        ofile = str(filename)

        if must_exists:
            if not os.path.isfile(ofile):
                raise IOError(errno.ENOENT, _("File doesn't exists."), ofile)

        if os.path.exists(ofile):
            if not os.access(ofile, os.W_OK):
                if self.simulate:
                    LOG.error(_('Write permission to {!r} denied.').format(ofile))
                else:
                    raise IOError(errno.EACCES, _('Write permission denied.'), ofile)
        else:
            parent_dir = os.path.dirname(ofile)
            if not os.access(parent_dir, os.W_OK):
                if self.simulate:
                    LOG.error(_('Write permission to {!r} denied.').format(parent_dir))
                else:
                    raise IOError(errno.EACCES, _('Write permission denied.'), parent_dir)

        if self.verbose > verb_level1:
            if self.verbose > verb_level2:
                LOG.debug(_('Write {what!r} into {to!r}.').format(what=content, to=ofile))
            else:
                LOG.debug(_('Writing {!r} ...').format(ofile))

        if isinstance(content, six.binary_type):
            content_bin = content
        else:
            if isinstance(content, six.text_type):
                content_bin = encode_or_bust(content, encoding)
            else:
                content_bin = encode_or_bust(str(content), encoding)

        if self.simulate:
            if self.verbose > verb_level2:
                LOG.debug(_('Simulating write into {!r}.').format(ofile))
            return

        signal.signal(signal.SIGALRM, write_alarm_caller)
        signal.alarm(timeout)

        # Open filename for writing unbuffered
        if self.verbose > verb_level3:
            LOG.debug(_('Opening {!r} for write unbuffered ...').format(ofile))
        with open(ofile, 'wb', 0) as fh:
            fh.write(content_bin)
            if self.verbose > verb_level3:
                LOG.debug(_('Closing {!r} ...').format(ofile))

        signal.alarm(0)

        return

    # -------------------------------------------------------------------------
    def get_password(self, first_prompt=None, second_prompt=None, may_empty=True, repeat=True):
        """
        Ask the user for a password on the console.

        @raise AbortAppError: if the user presses Ctrl-D (EOF)
        @raise TimeoutOnPromptError: if the user does not finishing after a time

        @param first_prompt: the prompt for the first password question
        @type first_prompt: str
        @param second_prompt: the prompt for the second password question
        @type second_prompt: str
        @param may_empty: The behaviour, if the user inputs an empty password:
                          if True, an empty password will be returned
                          if False, the question will be repeated.
        @type may_empty: bool
        @param repeat: Asking for the password a second time, which must be equal
                       to the first given password.
        @type repeat: bool

        @return: The entered password
        @rtype: str

        """
        if not first_prompt:
            first_prompt = _('Password:') + ' '

        if not second_prompt:
            second_prompt = _('Repeat password:') + ' '

        ret_passwd = None
        second_passwd = None

        while True:

            if not self.quiet:
                print()
            ret_passwd = self._get_password(first_prompt, may_empty)
            if ret_passwd:
                if repeat:
                    second_passwd = self._get_password(second_prompt, may_empty=False)
                    if ret_passwd != second_passwd:
                        msg = _('The entered passwords does not match.')
                        LOG.error(msg)
                        continue
            break

        return ret_passwd

    # -------------------------------------------------------------------------
    def _get_password(self, prompt, may_empty=True):

        def passwd_alarm_caller(signum, sigframe):
            raise TimeoutOnPromptError(self.prompt_timeout)

        msg_intr = _('Interrupted on demand.')
        ret_passwd = ''

        try:
            signal.signal(signal.SIGALRM, passwd_alarm_caller)
            signal.alarm(self.prompt_timeout)

            while True:

                try:
                    ret_passwd = getpass.getpass(prompt)
                except EOFError:
                    raise AbortAppError(msg_intr)

                signal.alarm(self.prompt_timeout)

                if ret_passwd == '':
                    if may_empty:
                        return ''
                    else:
                        continue
                else:
                    break

        except (TimeoutOnPromptError, AbortAppError) as e:
            msg = _('Got a {}:').format(e.__class__.__name__) + ' ' + str(e)
            LOG.error(msg)
            self.exit(10)

        except KeyboardInterrupt:
            msg = _('Got a {}:').format('KeyboardInterrupt') + ' ' + msg_intr
            LOG.error(msg)
            self.exit(10)

        finally:
            signal.alarm(0)

        return ret_passwd

    # -------------------------------------------------------------------------
    def ask_for_yes_or_no(self, prompt, default_on_empty=None):
        """
        Ask the user for yes or no.

        @raise AbortAppError: if the user presses Ctrl-D (EOF)
        @raise TimeoutOnPromptError: if the user does not correct answer after a time

        @param prompt: the prompt for the question
        @type prompt: str
        @param default_on_empty: behaviour on an empty reply:
                                 * if None, repeat the question
                                 * if True, return True
                                 * else return False
        @type default_on_empty: bool or None

        @return: True, if the user answered Yes, else False
        @rtype: bool

        """
        if not prompt:
            prompt = _('Yes/No') + ' '

        if self.assumed_answer is not None:
            ret = self.assumed_answer
            if not self.quiet:
                answer = _('No')
                if ret:
                    answer = _('Yes')
                answer = ' ' + _("Automatic answer: '{}'.").format(self.colored(answer, 'CYAN'))
                print(prompt + answer)
            return ret

        def prompt_alarm_caller(signum, sigframe):
            raise TimeoutOnPromptError(self.prompt_timeout)

        msg_intr = _('Interrupted on demand.')
        try:
            signal.signal(signal.SIGALRM, prompt_alarm_caller)
            signal.alarm(self.prompt_timeout)

            reply = ''
            while True:
                try:
                    reply = input(prompt)
                except EOFError:
                    raise AbortAppError(msg_intr)
                signal.alarm(self.prompt_timeout)
                match = self.re_yes_no.match(reply)
                if match:
                    if match.group(1) is None:
                        if default_on_empty is None:
                            continue
                        return bool(default_on_empty)
                    # There is an answer
                    r = match.group(1).lower()
                    if r in self.no_list:
                        # Continue == no
                        return False
                    elif r in self.yes_list:
                        # Continue == yes
                        return True
                    else:
                        continue
                else:
                    continue
                # Repeat the question

        except (TimeoutOnPromptError, AbortAppError) as e:
            print()
            msg = _('Got a {}:').format(e.__class__.__name__) + ' ' + str(e)
            LOG.error(msg)
            self.exit(10)

        except KeyboardInterrupt:
            msg = _('Got a {}:').format('KeyboardInterrupt') + ' ' + msg_intr
            print()
            LOG.error(msg)
            self.exit(10)

        finally:
            signal.alarm(0)


# =============================================================================
class CompletedProcess(object):
    """
    A process that has finished running.

    This is returned by run().

    Attributes:
      args: The list or str args passed to run().
      returncode: The exit code of the process, negative for signals.
      stdout: The standard output (None if not captured).
      stderr: The standard error (None if not captured).

    This class was taken from subprocess.py of the standard library of Python 3.5.
    """

    # -------------------------------------------------------------------------
    def __init__(
            self, args, returncode, stdout=None, stderr=None, encoding=None,
            start_dt=None, end_dt=None):
        """Initialize a CompletedProcess object."""
        self.args = args
        self.returncode = returncode
        self.encoding = encoding
        if encoding is None:
            if locale.getpreferredencoding():
                self.encoding = locale.getpreferredencoding()
            else:
                self.encoding = 'utf-8'

        self._start_dt = None
        self._end_dt = None
        if start_dt is not None:
            if not isinstance(start_dt, datetime.datetime):
                msg = _('Parameter {t!r} must be a {e}, {v!r} was given.').format(
                    t='start_dt', e='datetime.datetime', v=start_dt)
                raise TypeError(msg)
            self._start_dt = start_dt
        if end_dt is not None:
            if not isinstance(end_dt, datetime.datetime):
                msg = _('Parameter {t!r} must be a {e}, {v!r} was given.').format(
                    t='end_dt', e='datetime.datetime', v=end_dt)
                raise TypeError(msg)
            self._end_dt = end_dt

        self.stdout = stdout
        if stdout is not None:
            stdout = to_str(stdout, self.encoding)
            if stdout.strip() == '':
                self.stdout = None
            else:
                self.stdout = stdout

        self.stderr = stderr
        if stderr is not None:
            stderr = to_str(stderr, self.encoding)
            if stderr.strip() == '':
                self.stderr = None
            else:
                self.stderr = stderr

    # -------------------------------------------------------------------------
    @property
    def start_dt(self):
        """Return the timestamp of starting the process."""
        return self._start_dt

    # -------------------------------------------------------------------------
    @property
    def end_dt(self):
        """Return the timestamp of ending the process."""
        return self._end_dt

    # -------------------------------------------------------------------------
    @property
    def duration(self):
        """Return the duration of executing the process."""
        if self.start_dt is None:
            return None
        if self.end_dt is None:
            return None
        return self.end_dt - self.start_dt

    # -------------------------------------------------------------------------
    def __repr__(self):
        """Typecast into a string for reproduction."""
        args = ['args={!r}'.format(self.args),
                'returncode={!r}'.format(self.returncode)]
        if self.start_dt is not None:
            args.append('start_dt={!r}'.format(self.start_dt))
        if self.end_dt is not None:
            args.append('end_dt={!r}'.format(self.end_dt))
        if self.stdout is not None or self.stderr is not None:
            args.append('encoding={!r}'.format(self.encoding))
        if self.stdout is not None:
            args.append('stdout={!r}'.format(self.stdout))
        if self.stderr is not None:
            args.append('stderr={!r}'.format(self.stderr))
        return '{}({})'.format(type(self).__name__, ', '.join(args))

    # -------------------------------------------------------------------------
    def __str__(self):
        """Typecast into a string."""
        out = _('Completed process') + ':\n'
        out += '  args:       {!r}\n'.format(self.args)
        out += '  returncode: {}\n'.format(self.returncode)
        if self.start_dt is not None:
            out += '  started:    {}\n'.format(self.start_dt.isoformat(' '))
        if self.end_dt is not None:
            out += '  ended:      {}\n'.format(self.end_dt.isoformat(' '))
        if self.duration is not None:
            out += '  duration:   {}\n'.format(self.duration)
        if self.stdout is not None or self.stderr is not None:
            out += '  encoding:   {!r}\n'.format(self.encoding)
        iind = '     '
        ind = '              '
        if self.stdout is not None:
            o = indent(self.stdout.rstrip(), ind, iind)
            out += '  stdout:{}\n'.format(o)
        if self.stderr is not None:
            o = indent(self.stderr.rstrip(), ind, iind)
            out += '  stderr:{}\n'.format(o)
        return out

    # -------------------------------------------------------------------------
    def check_returncode(self):
        """Raise CalledProcessError if the exit code is non-zero."""
        if self.returncode:
            raise CalledProcessError(self.returncode, self.args, self.stdout, self.stderr)


# =============================================================================

if __name__ == '__main__':

    pass

# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 list
