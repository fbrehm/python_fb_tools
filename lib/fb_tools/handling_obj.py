#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: Frank Brehm
@contact: frank.brehm@pixelpark.com
@copyright: © 2018 by Frank Brehm, Berlin
@summary: The module for a base object with extended handling.
"""
from __future__ import absolute_import

# Standard modules
import os
import logging
import pipes
import textwrap

from subprocess import Popen, PIPE, SubprocessError

# Third party modules

# Own modules
from .common import pp, to_bool, caller_search_path, to_str

from .colored import colorstr

from .obj import FbBaseObject

__version__ = '0.1.1'
LOG = logging.getLogger(__name__)


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
        return "Command '%s' returned non-zero exit status %d" % (self.cmd, self.returncode)

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
class TimeoutExpired(SubprocessError):
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
        return ("Command '%s' timed out after %s seconds" %
                (self.cmd, self.timeout))

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

    # -------------------------------------------------------------------------
    def __init__(
        self, appname=None, verbose=0, version=__version__, base_dir=None,
            terminal_has_colors=False, simulate=None, force=None, initialized=None):

        self._simulate = False

        self._force = False

        self._terminal_has_colors = bool(terminal_has_colors)
        """
        @ivar: flag, that the current terminal understands color ANSI codes
        @type: bool
        """

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
        res['force'] = self.force
        res['simulate'] = self.simulate
        res['terminal_has_colors'] = self.terminal_has_colors

        return res

    # -------------------------------------------------------------------------
    def get_command(self, cmd, quiet=False):
        """
        Searches the OS search path for the given command and gives back the
        normalized position of this command.
        If the command is given as an absolute path, it check the existence
        of this command.

        @param cmd: the command to search
        @type cmd: str
        @param quiet: No warning message, if the command could not be found,
                      only a debug message
        @type quiet: bool

        @return: normalized complete path of this command, or None,
                 if not found
        @rtype: str or None

        """

        if self.verbose > 2:
            LOG.debug("Searching for command {!r} ...".format(cmd))

        # Checking an absolute path
        if os.path.isabs(cmd):
            if not os.path.exists(cmd):
                LOG.warning("Command {!r} doesn't exists.".format(cmd))
                return None
            if not os.access(cmd, os.X_OK):
                msg = "Command {!r} is not executable.".format(cmd)
                LOG.warning(msg)
                return None
            return os.path.normpath(cmd)

        # Checking a relative path
        for d in caller_search_path():
            if self.verbose > 3:
                LOG.debug("Searching command in {!r} ...".format(d))
            p = os.path.join(d, cmd)
            if os.path.exists(p):
                if self.verbose > 2:
                    LOG.debug("Found {!r} ...".format(p))
                if os.access(p, os.X_OK):
                    return os.path.normpath(p)
                else:
                    LOG.debug("Command {!r} is not executable.".format(p))

        # command not found, sorry
        if quiet:
            if self.verbose > 2:
                LOG.debug("Command {!r} not found.".format(cmd))
        else:
            LOG.warning("Command {!r} not found.".format(cmd))

        return None

    # -------------------------------------------------------------------------
    def run(self, *popenargs, input=None, timeout=None, check=False, may_simulate=True, **kwargs):
        """
        Run command with arguments and return a CompletedProcess instance.

        The returned instance will have attributes args, returncode, stdout and
        stderr. By default, stdout and stderr are not captured, and those attributes
        will be None. Pass stdout=PIPE and/or stderr=PIPE in order to capture them.

        If check is True and the exit code was non-zero, it raises a
        CalledProcessError. The CalledProcessError object will have the return code
        in the returncode attribute, and output & stderr attributes if those streams
        were captured.

        If timeout is given, and the process takes too long, a TimeoutExpired
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

        if input is not None:
            if 'stdin' in kwargs:
                raise ValueError('stdin and input arguments may not both be used.')
            kwargs['stdin'] = PIPE

        LOG.debug("Executing command args:\n{}".format(pp(popenargs)))
        cmd_args = []
        for arg in popenargs[0]:
            LOG.debug("Performing argument {!r}.".format(arg))
            cmd_args.append(pipes.quote(arg))
        cmd_str = ' '.join(cmd_args)

        cmd_str = ' '.join(map(lambda x: pipes.quote(x), popenargs[0]))
        LOG.debug("Executing: {}".format(cmd_str))

        if may_simulate and self.simulate:
            LOG.info("Simulation mode, not executing: {}".format(cmd_str))
            return CompletedProcess(popenargs, 0, "Simulated execution.\n", '')

        with Popen(*popenargs, **kwargs) as process:
            try:
                stdout, stderr = process.communicate(input, timeout=timeout)
            except TimeoutExpired:
                process.kill()
                stdout, stderr = process.communicate()
                raise TimeoutExpired(process.args, timeout, output=stdout, stderr=stderr)
            except Exception:
                process.kill()
                process.wait()
                raise
            retcode = process.poll()
            if check and retcode:
                raise CalledProcessError(retcode, process.args, output=stdout, stderr=stderr)

        return CompletedProcess(process.args, retcode, stdout, stderr)

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
    def __init__(self, args, returncode, stdout=None, stderr=None):

        self.args = args
        self.returncode = returncode

        self.stdout = stdout
        if stdout is not None:
            stdout = to_str(stdout)
            if stdout.strip() == '':
                self.stdout = None
            else:
                self.stdout = stdout

        self.stderr = stderr
        if stderr is not None:
            stderr = to_str(stderr)
            if stderr.strip() == '':
                self.stderr = None
            else:
                self.stderr = stderr

    # -------------------------------------------------------------------------
    def __repr__(self):
        args = ['args={!r}'.format(self.args),
                'returncode={!r}'.format(self.returncode)]
        if self.stdout is not None:
            args.append('stdout={!r}'.format(self.stdout))
        if self.stderr is not None:
            args.append('stderr={!r}'.format(self.stderr))
        return "{}({})".format(type(self).__name__, ', '.join(args))

    # -------------------------------------------------------------------------
    def __str__(self):
        out = 'Completed process:\n'
        out += '  args:       {!r}\n'.format(self.args)
        out += '  returncode: {}\n'.format(self.returncode)
        if self.stdout is not None:
            o = self.stdout
            out += '  stdout:     {}\n'.format(textwrap.indent(o, '              ').strip())
        if self.stderr is not None:
            o = self.stderr
            out += '  stderr:     {}\n'.format(textwrap.indent(o, '              ').strip())
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
