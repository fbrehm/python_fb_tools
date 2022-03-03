#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: Frank Brehm
@contact: frank.brehm@pixelpark.com
@copyright: © 2021 by Frank Brehm, Berlin
@summary: The module for a base object with extended handling.
"""
from __future__ import absolute_import

# Standard modules
import os
import logging
import pipes
import signal
import errno
import sys
import locale
import datetime
import copy

try:
    import pathlib
except ImportError:
    import pathlib2 as pathlib

from subprocess import Popen, PIPE
if sys.version_info[0] >= 3:
    from subprocess import SubprocessError, TimeoutExpired
else:
    class SubprocessError(Exception):
        pass

    class TimeoutExpired(SubprocessError):
        pass

# Third party modules
import six

# Own modules
from fb_logging.colored import colorstr

from .common import pp, to_bool, caller_search_path, to_str, encode_or_bust
from .common import indent, is_sequence

from .xlate import XLATOR

from .errors import InterruptError, IoTimeoutError, ReadTimeoutError, WriteTimeoutError

from .obj import FbBaseObject

__version__ = '1.6.3'
LOG = logging.getLogger(__name__)

_ = XLATOR.gettext
ngettext = XLATOR.ngettext

DEFAULT_FILEIO_TIMEOUT = 2


# =============================================================================
class ProcessCommunicationTimeout(IoTimeoutError, SubprocessError):

    # -------------------------------------------------------------------------
    def __init__(self, timeout):

        msg = _("Timeout on communicating with process.")
        super(ProcessCommunicationTimeout, self).__init__(msg, timeout)


# =============================================================================
class CalledProcessError(SubprocessError):
    """
    Raised when run() is called with check=True and the process
    returns a non-zero exit status.

    Attributes:
      cmd, returncode, stdout, stderr, output

    This class was taken from subprocess.py of the standard library of Python 3.5.
    """

    # -------------------------------------------------------------------------
    def __init__(self, returncode, cmd, output=None, stderr=None):
        self.returncode = returncode
        self.cmd = cmd
        self.output = output
        self.stderr = stderr

    # -------------------------------------------------------------------------
    def __str__(self):
        return _("Command {c!r} returned non-zero exit status {rc}.").format(
            c=self.cmd, rc=self.returncode)

    # -------------------------------------------------------------------------
    @property
    def stdout(self):
        """Alias for output attribute, to match stderr"""
        return self.output

    @stdout.setter
    def stdout(self, value):
        # There's no obvious reason to set this, but allow it anyway so
        # .stdout is a transparent alias for .output
        self.output = value


# =============================================================================
class TimeoutExpiredError(SubprocessError):
    """
    This exception is raised when the timeout expires while waiting for a
    child process.

    Attributes:
        cmd, output, stdout, stderr, timeout

    This class was taken from subprocess.py of the standard library of Python 3.5.
    """

    # -------------------------------------------------------------------------
    def __init__(self, cmd, timeout, output=None, stderr=None):
        self.cmd = cmd
        self.timeout = timeout
        self.output = output
        self.stderr = stderr

    # -------------------------------------------------------------------------
    def __str__(self):
        msg = ngettext(
            "Command {c!r} timed out after {s} second.",
            "Command {c!r} timed out after {s} seconds.", self.timeout)
        return msg.format(c=self.cmd, s=self.timeout)

    # -------------------------------------------------------------------------
    @property
    def stdout(self):
        return self.output

    @stdout.setter
    def stdout(self, value):
        # There's no obvious reason to set this, but allow it anyway so
        # .stdout is a transparent alias for .output
        self.output = value


# =============================================================================
class HandlingObject(FbBaseObject):
    """
    Base class for an object with extend handling possibilities.
    """

    fileio_timeout = DEFAULT_FILEIO_TIMEOUT

    # -------------------------------------------------------------------------
    def __init__(
        self, appname=None, verbose=0, version=__version__, base_dir=None, quiet=False,
            terminal_has_colors=False, simulate=None, force=None, initialized=None):

        self._simulate = False

        self._force = False

        self._quiet = quiet

        self.add_search_paths = []

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
            appname=appname,
            verbose=verbose,
            version=version,
            base_dir=base_dir,
            initialized=False,
        )

        if simulate is not None:
            self.simulate = simulate

    # -----------------------------------------------------------
    @property
    def simulate(self):
        """A flag describing, that all should be simulated."""
        return self._simulate

    @simulate.setter
    def simulate(self, value):
        self._simulate = to_bool(value)

    # -----------------------------------------------------------
    @property
    def force(self):
        """Forced execution of some actions."""
        return self._force

    @force.setter
    def force(self, value):
        self._force = to_bool(value)

    # -----------------------------------------------------------
    @property
    def quiet(self):
        """Quiet execution of the application,
            only warnings and errors are emitted."""
        return self._quiet

    @quiet.setter
    def quiet(self, value):
        self._quiet = bool(value)

    # -----------------------------------------------------------
    @property
    def is_venv(self):
        """Flag showing, that the current application is running
            inside a virtual environment."""

        if hasattr(sys, 'real_prefix'):
            return True
        return (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)

    # -----------------------------------------------------------
    @property
    def interrupted(self):
        """Flag indicating, that the current process was interrupted."""
        return self._interrupted

    # -----------------------------------------------------------
    @property
    def terminal_has_colors(self):
        """A flag, that the current terminal understands color ANSI codes."""
        return self._terminal_has_colors

    @terminal_has_colors.setter
    def terminal_has_colors(self, value):
        self._terminal_has_colors = bool(value)

    # -------------------------------------------------------------------------
    def as_dict(self, short=True):
        """
        Transforms the elements of the object into a dict

        @param short: don't include local properties in resulting dict.
        @type short: bool

        @return: structure as dict
        @rtype:  dict
        """

        res = super(HandlingObject, self).as_dict(short=short)
        res['fileio_timeout'] = self.fileio_timeout
        res['force'] = self.force
        res['interrupted'] = self.interrupted
        res['is_venv'] = self.is_venv
        res['quiet'] = self.quiet
        res['simulate'] = self.simulate
        res['terminal_has_colors'] = self.terminal_has_colors

        return res

    # -------------------------------------------------------------------------
    def get_cmd(self, cmd, quiet=False):

        return self.get_command(cmd, quiet=quiet)

    # -------------------------------------------------------------------------
    def get_command(self, cmd, quiet=False, resolve=False):
        """
        Searches the OS search path for the given command and gives back the
        normalized position of this command.
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
            LOG.debug(_("Searching for command {!r} ...").format(str(cmd)))

        # Checking an absolute path
        if cmd.is_absolute():
            if not cmd.exists():
                LOG.warning(_("Command {!r} doesn't exists.").format(str(cmd)))
                return None
            if not os.access(str(cmd), os.X_OK):
                msg = _("Command {!r} is not executable.").format(str(cmd))
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
                LOG.debug(_("Searching command in {!r} ...").format(str(d)))
            p = d / cmd
            if p.exists():
                if self.verbose > 2:
                    LOG.debug("Found {!r} ...".format(str(p)))
                if os.access(str(p), os.X_OK):
                    if resolve:
                        return p.resolve()
                    return p
                else:
                    LOG.debug(_("Command {!r} is not executable.").format(str(p)))

        # command not found, sorry
        msg = _("Command {!r} not found.").format(str(cmd))
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

        input = None
        if 'input' in kwargs:
            input = kwargs['input']
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
                'input': input,
                'timeout': timeout,
                'check': check,
                'may_simulate': may_simulate,
                'popenargs': popenargs,
                'kwargs': kwargs,
            }
            LOG.debug("Args of run():\n{}".format(pp(myargs)))

        if input is not None:
            if 'stdin' in kwargs:
                raise ValueError(_('STDIN and input arguments may not both be used.'))
            kwargs['stdin'] = PIPE

        LOG.debug(_("Executing command args:") + '\n' + pp(popenargs))
        cmd_args = []
        for arg in popenargs[0]:
            LOG.debug(_("Performing argument {!r}.").format(arg))
            cmd_args.append(pipes.quote(arg))
        cmd_str = ' '.join(cmd_args)

        cmd_str = ' '.join(map(lambda x: pipes.quote(x), popenargs[0]))
        LOG.debug(_("Executing: {}").format(cmd_str))

        if may_simulate and self.simulate:
            LOG.info(_("Simulation mode, not executing: {}").format(cmd_str))
            return CompletedProcess(popenargs, 0, "Simulated execution.\n", '')

        process = None
        try:
            start_dt = datetime.datetime.now()
            process = Popen(*popenargs, **kwargs)
            if self.verbose > 0:
                LOG.debug(_("PID of process: {}").format(process.pid))
            try:
                stdout, stderr = self._communicate(
                    process, popenargs, input=input, timeout=timeout)
            except Exception as e:
                if self.verbose > 2:
                    LOG.debug(_("{c} happened, killing process: {e}").format(
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
    def _communicate(self, process, popenargs, input=None, timeout=None):

        try:

            if timeout is None:
                return process.communicate(input)

            def communicate_alarm_caller(signum, sigframe):
                err = InterruptError(signum)
                self.handle_info(str(err))
                process.kill()
                raise ProcessCommunicationTimeout(timeout)

            signal.signal(signal.SIGALRM, communicate_alarm_caller)
            signal.alarm(timeout)

            stdout, stderr = process.communicate(input)

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
        Handler as a callback function for getting a signal from somewhere.

        @param signum: the gotten signal number
        @type signum: int
        @param frame: the current stack frame
        @type frame: None or a frame object

        """

        err = InterruptError(signum)

        if signum in self.signals_dont_interrupt:
            self.handle_info(str(err))
            LOG.info(_("Nothing to do on signal."))
            return

        self._interrupted = True
        raise err

    # -------------------------------------------------------------------------
    def read_file(
            self, filename, timeout=None, binary=False, quiet=False, encoding='utf-8'):
        """
        Reads the content of the given filename.

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
            '''
            This nested function will be called in event of a timeout

            @param signum:   the signal number (POSIX) which happend
            @type signum:    int
            @param sigframe: the frame of the signal
            @type sigframe:  object
            '''

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
            LOG.debug(_("Reading file content of {!r} ...").format(ifile))

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
        Writes the given content into the given filename.
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
            '''
            This nested function will be called in event of a timeout

            @param signum:   the signal number (POSIX) which happend
            @type signum:    int
            @param sigframe: the frame of the signal
            @type sigframe:  object
            '''

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
                    LOG.error(_("Write permission to {!r} denied.").format(ofile))
                else:
                    raise IOError(errno.EACCES, _('Write permission denied.'), ofile)
        else:
            parent_dir = os.path.dirname(ofile)
            if not os.access(parent_dir, os.W_OK):
                if self.simulate:
                    LOG.error(_("Write permission to {!r} denied.").format(parent_dir))
                else:
                    raise IOError(errno.EACCES, _('Write permission denied.'), parent_dir)

        if self.verbose > verb_level1:
            if self.verbose > verb_level2:
                LOG.debug(_("Write {what!r} into {to!r}.").format(what=content, to=ofile))
            else:
                LOG.debug(_("Writing {!r} ...").format(ofile))

        if isinstance(content, six.binary_type):
            content_bin = content
        else:
            if isinstance(content, six.text_type):
                content_bin = encode_or_bust(content, encoding)
            else:
                content_bin = encode_or_bust(str(content), encoding)

        if self.simulate:
            if self.verbose > verb_level2:
                LOG.debug(_("Simulating write into {!r}.").format(ofile))
            return

        signal.signal(signal.SIGALRM, write_alarm_caller)
        signal.alarm(timeout)

        # Open filename for writing unbuffered
        if self.verbose > verb_level3:
            LOG.debug(_("Opening {!r} for write unbuffered ...").format(ofile))
        with open(ofile, 'wb', 0) as fh:
            fh.write(content_bin)
            if self.verbose > verb_level3:
                LOG.debug(_("Closing {!r} ...").format(ofile))

        signal.alarm(0)

        return


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
                msg = _("Parameter {t!r} must be a {e}, {v!r} was given.").format(
                    t='start_dt', e='datetime.datetime', v=start_dt)
                raise TypeError(msg)
            self._start_dt = start_dt
        if end_dt is not None:
            if not isinstance(end_dt, datetime.datetime):
                msg = _("Parameter {t!r} must be a {e}, {v!r} was given.").format(
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
        "The timestamp of starting the process."
        return self._start_dt

    # -------------------------------------------------------------------------
    @property
    def end_dt(self):
        "The timestamp of ending the process."
        return self._end_dt

    # -------------------------------------------------------------------------
    @property
    def duration(self):
        "The duration of executing the process."
        if self.start_dt is None:
            return None
        if self.end_dt is None:
            return None
        return self.end_dt - self.start_dt

    # -------------------------------------------------------------------------
    def __repr__(self):
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
        return "{}({})".format(type(self).__name__, ', '.join(args))

    # -------------------------------------------------------------------------
    def __str__(self):
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

if __name__ == "__main__":

    pass

# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 list
