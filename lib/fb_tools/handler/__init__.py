#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@summary: A base handler module for underlaying actions.

@author: Frank Brehm
@contact: frank.brehm@pixelpark.com
@copyright: © 2021 by Frank Brehm, Berlin

"""
from __future__ import absolute_import, print_function

# Standard module
import os
import logging
import stat
import subprocess
import pwd
import locale
import time
import pipes
import datetime
from fcntl import fcntl, F_GETFL, F_SETFL

try:
    import pathlib
except ImportError:
    import pathlib2 as pathlib

# Third party modules
import pytz
import six

import babel

from babel.dates import LOCALTZ

# Own modules
from ..xlate import XLATOR

from ..common import to_bool

from ..errors import HandlerError

from ..handling_obj import HandlingObject, CompletedProcess

__version__ = '2.0.1'
LOG = logging.getLogger(__name__)

CHOWN_CMD = pathlib.Path('/bin/chown')
ECHO_CMD = pathlib.Path('/bin/echo')
SUDO_CMD = pathlib.Path('/usr/bin/sudo')

DEFAULT_LOCALE = 'en_US'

_ = XLATOR.gettext


# =============================================================================
class BaseHandler(HandlingObject):
    """A base handler class for creating the terraform environment."""

    std_file_permissions = stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH
    std_secure_file_permissions = stat.S_IRUSR | stat.S_IWUSR

    open_opts = {}
    if six.PY3:
        open_opts['encoding'] = 'utf-8'
        open_opts['errors'] = 'surrogateescape'

    default_locale = babel.core.default_locale()
    if not default_locale:
        default_locale = DEFAULT_LOCALE
    tz = LOCALTZ
    tz_name = babel.dates.get_timezone_name(tz, width='long', locale=default_locale)

    # -------------------------------------------------------------------------
    def __init__(
        self, appname=None, verbose=0, version=__version__, base_dir=None, sudo=False,
            quiet=False, terminal_has_colors=False, simulate=None, force=None, initialized=None):
        """Construct the object."""
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
        """Return the absolute path to the OS command 'chown'."""
        return self._chown_cmd

    # -----------------------------------------------------------
    @property
    def echo_cmd(self):
        """Set the absolute path to the OS command 'echo'."""
        return self._echo_cmd

    # -----------------------------------------------------------
    @property
    def sudo_cmd(self):
        """Return the absolute path to the OS command 'sudo'."""
        return self._sudo_cmd

    # -----------------------------------------------------------
    @property
    def sudo(self):
        """Return, whiether the command should be executed by sudo by default."""
        return self._sudo

    @sudo.setter
    def sudo(self, value):
        self._sudo = to_bool(value)

    # -------------------------------------------------------------------------
    def as_dict(self, short=True):
        """Transform the elements of the object into a dict.

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
        res['default_locale'] = self.default_locale

        return res

    # -------------------------------------------------------------------------
    @classmethod
    def set_tz(cls, tz_name):
        """Set the timezone to the given name."""
        if not tz_name.strip():
            raise ValueError(_("Invalid time zone name {!r}.").format(tz_name))
        tz_name = tz_name.strip()
        LOG.debug(_("Setting time zone to {!r}.").format(tz_name))
        cls.tz = pytz.timezone(tz_name)
        cls.tz_name = babel.dates.get_timezone_name(
            cls.tz, width='long', locale=cls.default_locale)
        LOG.debug(_("Name of the time zone: {!r}.").format(cls.tz_name))

    # -------------------------------------------------------------------------
    def __call__(self, yaml_file):
        """Execute the underlying action."""
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
        Execute a OS command.

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
            LOG.debug(_("Executing: {}").format(cmd_list))

        if quiet and self.verbose > 1:
            LOG.debug(_("Quiet execution."))

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

        start_dt = datetime.datetime.now(self.tz)

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

        # Display Output of executable
        if hb_handler is not None:

            (stdoutdata, stderrdata) = self._wait_for_proc_with_heartbeat(
                cmd_obj=cmd_obj, cmd_str=cmd_str, hb_handler=hb_handler, hb_interval=hb_interval,
                use_stdout=use_stdout, use_stderr=use_stderr,
                poll_interval=poll_interval, quiet=quiet)

        else:

            if not quiet or self.verbose > 1:
                LOG.debug(_("Starting synchronous communication with '{}'.").format(cmd_str))
            (stdoutdata, stderrdata) = cmd_obj.communicate()

        if not quiet or self.verbose > 1:
            LOG.debug(_("Finished communication with '{}'.").format(cmd_str))

        ret = cmd_obj.wait()

        end_dt = datetime.datetime.now(self.tz)
        proc = CompletedProcess(
            args=cmd_list, returncode=ret, encoding=cur_encoding,
            stdout=stdoutdata, stderr=stderrdata, start_dt=start_dt, end_dt=end_dt)
        return self._eval_call_results(proc, log_output=log_output, quiet=quiet)

    # -------------------------------------------------------------------------
    def _eval_call_results(self, proc, log_output=True, quiet=False):

        if not isinstance(proc, CompletedProcess):
            msg = _("Parameter {p!r} is not of type {t!r}.").format(
                p='proc', t='CompletedProcess')
            raise TypeError(msg)

        if self.verbose > 2:
            LOG.debug(_("Got completed process:") + "\n{}".format(proc))

        if proc.stderr:
            if not quiet:
                msg = _("Output on {}:").format('proc.stderr')
                msg += '\n' + proc.stderr
                if proc.returncode:
                    LOG.warning(msg)
                elif log_output:
                    LOG.info(msg)
                else:
                    LOG.debug(msg)

        if proc.stdout:
            if not quiet:
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
            LOG.debug(_(
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
                LOG.debug(_("Checking for the end of the communication ..."))
            if cmd_obj.poll() is not None:
                cmd_obj.wait()
                break

            # Heartbeat handling ...
            cur_time = time.time()
            time_diff = cur_time - start_time
            if time_diff >= hb_interval:
                if not quiet or self.verbose > 1:
                    LOG.debug(_("Time to execute the heartbeat handler."))
                hb_handler()
                start_time = cur_time
            if self.verbose > 3:
                LOG.debug(_("Sleeping {:0.2f} seconds ...").format(poll_interval))
            time.sleep(poll_interval)

            # Reading out file descriptors
            if use_stdout:
                try:
                    stdoutdata += os.read(cmd_obj.stdout.fileno(), 1024)
                    if self.verbose > 3:
                        msg = _("   {w} is now: {o!r}").format(w='stdout', o=stdoutdata)
                        LOG.debug(msg)
                except OSError:
                    pass

            if use_stderr:
                try:
                    stderrdata += os.read(cmd_obj.stderr.fileno(), 1024)
                    if self.verbose > 3:
                        msg = _("   {w} is now: {o!r}").format(w='stderr', o=stderrdata)
                        LOG.debug(msg)
                except OSError:
                    pass

        return (stdoutdata, stderrdata)


# =============================================================================
if __name__ == "__main__":

    pass

# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 list
