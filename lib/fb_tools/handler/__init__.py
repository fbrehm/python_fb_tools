#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: Frank Brehm
@contact: frank.brehm@pixelpark.com
@copyright: © 2018 by Frank Brehm, Berlin
@summary: A base handler module for underlaying actions
"""
from __future__ import absolute_import, print_function

# Standard module
import os
import logging
import stat
import pathlib
import subprocess
import pwd
import locale
import time
import pipes
from fcntl import fcntl, F_GETFL, F_SETFL

# Third party modules
import pytz
import six

# Own modules
from ..xlate import XLATOR

from ..common import to_bool

from ..errors import HandlerError

from ..handling_obj import HandlingObject, CompletedProcess

__version__ = '1.3.1'
LOG = logging.getLogger(__name__)

CHOWN_CMD = pathlib.Path('/bin/chown')
ECHO_CMD = pathlib.Path('/bin/echo')
SUDO_CMD = pathlib.Path('/usr/bin/sudo')

_ = XLATOR.gettext


# =============================================================================
class BaseHandler(HandlingObject):
    """
    A base handler class for creating the terraform environment
    """

    std_file_permissions = stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH
    std_secure_file_permissions = stat.S_IRUSR | stat.S_IWUSR

    open_opts = {}
    if six.PY3:
        open_opts['encoding'] = 'utf-8'
        open_opts['errors'] = 'surrogateescape'

    tz_name = 'Europe/Berlin'
    tz = pytz.timezone(tz_name)

    # -------------------------------------------------------------------------
    def __init__(
        self, appname=None, verbose=0, version=__version__, base_dir=None, sudo=False,
            quiet=False, terminal_has_colors=False, simulate=None, force=None, initialized=None):

        self._chown_cmd = CHOWN_CMD
        self._echo_cmd = ECHO_CMD
        self._sudo_cmd = SUDO_CMD

        self._sudo = False

        super(BaseHandler, self).__init__(
            appname=appname, verbose=verbose, version=version, base_dir=base_dir,
            terminal_has_colors=terminal_has_colors, simulate=simulate, force=force,
            quiet=quiet, initialized=False,
        )

        self._chown_cmd = self.get_command('chown')
        self._echo_cmd = self.get_command('echo')
        self._sudo_cmd = self.get_command('sudo')

        self.sudo = sudo

        if initialized:
            self.initialized = True

    # -----------------------------------------------------------
    @property
    def chown_cmd(self):
        """The absolute path to the OS command 'chown'."""
        return self._chown_cmd

    # -----------------------------------------------------------
    @property
    def echo_cmd(self):
        """The absolute path to the OS command 'echo'."""
        return self._echo_cmd

    # -----------------------------------------------------------
    @property
    def sudo_cmd(self):
        """The absolute path to the OS command 'sudo'."""
        return self._sudo_cmd

    # -----------------------------------------------------------
    @property
    def sudo(self):
        """Should the command executed by sudo by default."""
        return self._sudo

    @sudo.setter
    def sudo(self, value):
        self._sudo = to_bool(value)

    # -------------------------------------------------------------------------
    def as_dict(self, short=True):
        """
        Transforms the elements of the object into a dict

        @param short: don't include local properties in resulting dict.
        @type short: bool

        @return: structure as dict
        @rtype:  dict
        """

        res = super(BaseHandler, self).as_dict(short=short)
        res['std_file_permissions'] = "{:04o}".format(self.std_file_permissions)
        res['std_secure_file_permissions'] = "{:04o}".format(self.std_secure_file_permissions)
        res['open_opts'] = self.open_opts
        res['tz_name'] = self.tz_name
        res['chown_cmd'] = self.chown_cmd
        res['echo_cmd'] = self.echo_cmd
        res['sudo_cmd'] = self.sudo_cmd
        res['sudo'] = self.sudo

        return res

    # -------------------------------------------------------------------------
    @classmethod
    def set_tz(cls, tz_name):

        if not tz_name.strip():
            raise ValueError(_("Invalid time zone name {!r}.").format(tz_name))
        tz_name = tz_name.strip()
        LOG.debug("Setting time zone to {!r}.".format(tz_name))
        cls.tz = pytz.timezone(tz_name)
        cls.tz_name = tz_name

    # -------------------------------------------------------------------------
    def __call__(self, yaml_file):
        """Executing the underlying action."""

        if not self.initialized:
            raise HandlerError(_("{}-object not initialized.").format(self.__class__.__name__))

        raise HandlerError(_("Method {} must be overridden in descendant classes.").format(
            '__call__()'))

    # -------------------------------------------------------------------------
    def call(
        self, cmd, sudo=None, simulate=None, quiet=None, shell=False,
            stdout=None, stderr=None, bufsize=0, drop_stderr=False,
            close_fds=False, hb_handler=None, hb_interval=2.0,
            poll_interval=0.2, log_output=True, **kwargs):
        """
        Executing a OS command.

        @param cmd: the cmd you wanne call
        @type cmd: list of strings or str
        @param sudo: execute the command with sudo
        @type sudo: bool (or none, if self.sudo will be be asked)
        @param simulate: simulate execution or not,
                         if None, self.simulate will asked
        @type simulate: bool or None
        @param quiet: quiet execution independend of self.quiet
        @type quiet: bool
        @param shell: execute the command with a shell
        @type shell: bool
        @param stdout: file descriptor for stdout,
                       if not given, self.stdout is used
        @type stdout: int
        @param stderr: file descriptor for stderr,
                       if not given, self.stderr is used
        @type stderr: int
        @param bufsize: size of the buffer for stdout
        @type bufsize: int
        @param drop_stderr: drop all output on stderr, independend
                            of any value of stderr
        @type drop_stderr: bool
        @param close_fds: closing all open file descriptors
                          (except 0, 1 and 2) on calling subprocess.Popen()
        @type close_fds: bool
        @param kwargs: any optional named parameter (must be one
            of the supported suprocess.Popen arguments)
        @type kwargs: dict

        @return: tuple of::
            - return value of calling process,
            - output on STDOUT,
            - output on STDERR

        """

        cmd_list = cmd
        if isinstance(cmd, str):
            cmd_list = [cmd]

        pwd_info = pwd.getpwuid(os.geteuid())

        if sudo is None:
            sudo = self.sudo
        if sudo:
            cmd_list.insert(0, '-n')
            cmd_list.insert(0, str(self.sudo_cmd))

        if simulate is None:
            simulate = self.simulate
        if simulate:
            cmd_list.insert(0, str(self.echo_cmd))
            quiet = False

        if quiet is None:
            quiet = self.quiet

        use_shell = bool(shell)

        cmd_list = [str(element) for element in cmd_list]
        cmd_str = ' '.join(map(lambda x: pipes.quote(x), cmd_list))

        if not quiet or self.verbose > 1:
            LOG.debug("Executing: {}".format(cmd_list))

        if quiet and self.verbose > 1:
            LOG.debug("Quiet execution")

        used_stdout = subprocess.PIPE
        if stdout is not None:
            used_stdout = stdout
        use_stdout = True
        if used_stdout is None:
            use_stdout = False

        used_stderr = subprocess.PIPE
        if drop_stderr:
            used_stderr = None
        elif stderr is not None:
            used_stderr = stderr
        use_stderr = True
        if used_stderr is None:
            use_stderr = False

        cur_locale = locale.getlocale()
        cur_encoding = cur_locale[1]
        if cur_locale[1] is None or cur_locale[1] == '' or cur_locale[1].upper() == 'C' or \
                cur_locale[1].upper() == 'POSIX':
            cur_encoding = 'UTF-8'

        cmd_obj = subprocess.Popen(
            cmd_list,
            shell=use_shell,
            close_fds=close_fds,
            stderr=used_stderr,
            stdout=used_stdout,
            bufsize=bufsize,
            env={'USER': pwd_info.pw_name},
            **kwargs
        )
        # cwd=self.base_dir,

        # Display Output of executable
        if hb_handler is not None:

            (stdoutdata, stderrdata) = self._wait_for_proc_with_heartbeat(
                cmd_obj=cmd_obj, cmd_str=cmd_str, hb_handler=hb_handler, hb_interval=hb_interval,
                use_stdout=use_stdout, use_stderr=use_stderr,
                poll_interval=poll_interval, quiet=quiet)

        else:

            if not quiet or self.verbose > 1:
                LOG.debug("Starting synchronous communication with '{}'.".format(cmd_str))
            (stdoutdata, stderrdata) = cmd_obj.communicate()

        if not quiet or self.verbose > 1:
            LOG.debug("Finished communication with '{}'.".format(cmd_str))

        ret = cmd_obj.wait()

        proc = CompletedProcess(
            args=cmd_list, returncode=ret, stdout=stdoutdata, stderr=stderrdata)
        return _eval_call_results(
            proc, cur_encoding=cur_encoding, log_output=log_output, quiet=quiet)

    # -------------------------------------------------------------------------
    def _eval_call_results(
        self, proc, cur_encoding='utf-8', log_output=True, quiet=False):

        if not isinstance(proc, CompletedProcess):
            msg = _("Parameter {p!r} is not of type {t!r}.").format(
                p='proc', t='CompletedProcess')
            raise TypeError(msg)

        if not quiet:
            LOG.debug("Returncode: {}".format(proc.returncode))

        if proc.stderr:
            if six.PY3:
                if self.verbose > 2:
                    LOG.debug("Decoding {what} from {enc!r}.".format(
                        what='proc.stderr', enc=cur_encoding))
                proc.stderr = proc.stderr.decode(cur_encoding)
            if not quiet:
                msg = _("Output on {}:").format('proc.stderr')
                msg += '\n' + proc.stderr
                if ret:
                    LOG.warn(msg)
                elif log_output:
                    LOG.info(msg)
                else:
                    LOG.debug(msg)

        if proc.stdout:
            if six.PY3:
                if self.verbose > 2:
                    LOG.debug("Decoding {what} from {enc!r}.".format(
                        what='proc.stdout', enc=cur_encoding))
                proc.stdout = proc.stdout.decode(cur_encoding)
            if not quiet:
                msg = _("Output on {where}:\n{what}.").format(
                    where="STDOUT", what=stdoutdata.strip())
                msg = _("Output on {}:").format('proc.stdout')
                msg += '\n' + proc.stdout
                if log_output:
                    LOG.info(msg)
                else:
                    LOG.debug(msg)

        return proc

    # -------------------------------------------------------------------------
    def _wait_for_proc_with_heartbeat(
        self, cmd_obj, cmd_str, hb_handler, hb_interval, use_stdout=True, use_stderr=True,
            poll_interval=0.2, quiet=False):

        stdoutdata = ''
        stderrdata = ''
        if six.PY3:
            stdoutdata = bytearray()
            stderrdata = bytearray()

        if not quiet or self.verbose > 1:
            LOG.debug((
                "Starting asynchronous communication with '{cmd}', "
                "heartbeat interval is {interval:0.1f} seconds.").format(
                    cmd=cmd_str, interval=hb_interval))

        out_flags = fcntl(cmd_obj.stdout, F_GETFL)
        err_flags = fcntl(cmd_obj.stderr, F_GETFL)
        fcntl(cmd_obj.stdout, F_SETFL, out_flags | os.O_NONBLOCK)
        fcntl(cmd_obj.stderr, F_SETFL, err_flags | os.O_NONBLOCK)

        start_time = time.time()

        while True:

            if self.verbose > 3:
                LOG.debug("Checking for the end of the communication ...")
            if cmd_obj.poll() is not None:
                cmd_obj.wait()
                break

            # Heartbeat handling ...
            cur_time = time.time()
            time_diff = cur_time - start_time
            if time_diff >= hb_interval:
                if not quiet or self.verbose > 1:
                    LOG.debug("Time to execute the heartbeat handler.")
                hb_handler()
                start_time = cur_time
            if self.verbose > 3:
                LOG.debug("Sleeping {:0.2f} seconds ...".format(poll_interval))
            time.sleep(poll_interval)

            # Reading out file descriptors
            if use_stdout:
                try:
                    stdoutdata += os.read(cmd_obj.stdout.fileno(), 1024)
                    if self.verbose > 3:
                        LOG.debug("  stdout is now: {!r}".format(stdoutdata))
                except OSError:
                    pass

            if use_stderr:
                try:
                    stderrdata += os.read(cmd_obj.stderr.fileno(), 1024)
                    if self.verbose > 3:
                        LOG.debug("  stderr is now: {!r}".format(stderrdata))
                except OSError:
                    pass

        return (stdoutdata, stderrdata)


# =============================================================================
if __name__ == "__main__":

    pass

# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 list
