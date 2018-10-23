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
import re
import socket
import ipaddress
import shutil
import glob
import stat
import textwrap
import copy
import sys
import pathlib

from subprocess import PIPE

# Third party modules
import pytz
import yaml
import six

# Own modules
from ..common import pp, to_bool

from ..errors import HandlerError, ExpectedHandlerError
from ..errors import CommandNotFoundError

from ..handling_obj import HandlingObject

__version__ = '0.6.1'
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
        """
        @ivar: the chown command for changing ownership of file objects
        @type: str
        """

        super(BaseHandler, self).__init__(
            appname=appname, verbose=verbose, version=version, base_dir=base_dir,
            terminal_has_colors=terminal_has_colors, simulate=simulate, force=force,
            initialized=False,
        )

#        if not self.chown_cmd.exists():
#            self._chown_cmd = self.get_command('chown')
        self._chown_cmd = self.get_command('chown')

        if initialized:
            self.initialized = True

    # -----------------------------------------------------------
    @property
    def chown_cmd(self):
        """The absolute path to the OS command 'chown'."""
        return self._chown_cmd

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
