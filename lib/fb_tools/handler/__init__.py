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
import logging
import stat
import pathlib

# Third party modules
import pytz
import six

# Own modules
from ..errors import HandlerError

from ..handling_obj import HandlingObject

__version__ = '0.6.4'
LOG = logging.getLogger(__name__)

CHOWN_CMD = pathlib.Path('/bin/chown')
ECHO_CMD = pathlib.Path('/bin/echo')
SUDO_CMD = pathlib.Path('/usr/bin/sudo')


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
        self, appname=None, verbose=0, version=__version__, base_dir=None,
            terminal_has_colors=False, simulate=None, force=None, initialized=None):

        self._chown_cmd = CHOWN_CMD
        self._echo_cmd = ECHO_CMD
        self._sudo_cmd = SUDO_CMD

        super(BaseHandler, self).__init__(
            appname=appname, verbose=verbose, version=version, base_dir=base_dir,
            terminal_has_colors=terminal_has_colors, simulate=simulate, force=force,
            initialized=False,
        )

        self._chown_cmd = self.get_command('chown')
        self._echo_cmd = self.get_command('echo')
        self._sudo_cmd = self.get_command('sudo')

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

        return res

    # -------------------------------------------------------------------------
    @classmethod
    def set_tz(cls, tz_name):

        if not tz_name.strip():
            raise ValueError("Invalid time zone name {!r}.".format(tz_name))
        tz_name = tz_name.strip()
        LOG.debug("Setting time zone to {!r}.".format(tz_name))
        cls.tz = pytz.timezone(tz_name)
        cls.tz_name = tz_name

    # -------------------------------------------------------------------------
    def __call__(self, yaml_file):
        """Executing the underlying action."""

        if not self.initialized:
            raise HandlerError("{}-object not initialized.".format(self.__class__.__name__))

        raise HandlerError("Method __call__() must be overridden in descendant classes.")


# =============================================================================
if __name__ == "__main__":

    pass

# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 list
