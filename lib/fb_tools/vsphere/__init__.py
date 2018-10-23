#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: Frank Brehm
@contact: frank.brehm@pixelpark.com
@copyright: © 2018 by Frank Brehm, Berlin
@summary: The module for a base VSphere handler object.
"""
from __future__ import absolute_import

# Standard modules
import logging
import ssl

from abc import ABCMeta

# Third party modules
from six import add_metaclass

from pyVim.connect import SmartConnect, Disconnect

# Own modules
from ..handling_obj import HandlingObject

from .errors import VSphereCannotConnectError

__version__ = '0.2.3'
LOG = logging.getLogger(__name__)

DEFAULT_HOST = 'vcs01.ppbrln.internal'
DEFAULT_PORT = 443
DEFAULT_USER = 'Administrator@vsphere.local'
DEFAULT_DC = 'vmcc'
DEFAULT_CLUSTER = 'vmcc-l105-01'

# =============================================================================
# @add_metaclass(ABCMeta)
class BaseVsphereHandler(HandlingObject):
    """
    Base class for a VSphere handler object.
    May not be instantiated.
    """

    max_search_depth = 10

    # -------------------------------------------------------------------------
    def __init__(
        self, appname=None, verbose=0, version=__version__, base_dir=None,
            host=DEFAULT_HOST, port=DEFAULT_PORT, user=DEFAULT_USER, password=None,
            dc=DEFAULT_DC, cluster=DEFAULT_CLUSTER, simulate=None, force=None,
            terminal_has_colors=False, initialized=False):

        self._host = host
        self._port = port
        self._user = user
        self._password = password
        self._dc = dc
        self._cluster = cluster

        self.service_instance = None

        super(BaseVsphereHandler, self).__init__(
            appname=appname, verbose=verbose, version=version, base_dir=base_dir,
            simulate=simulate, force=force, terminal_has_colors=terminal_has_colors,
            initialized=False,
        )

        self.port = port

        self.initialized = initialized

    # -----------------------------------------------------------
    @property
    def host(self):
        """The hostname or IP address of the VSpere server."""
        return self._host

    # -----------------------------------------------------------
    @property
    def port(self):
        """The TCP port number of the VSphere server."""
        return self._port

    @port.setter
    def port(self, value):
        if value is None:
            self._port = self.default_port
            return
        val = int(value)
        err_msg = (
            "Invalid port number {!r} for the VSphere server, "
            "must be 0 < PORT < 65536.")
        if val <= 0 or val > 65536:
            msg = err_msg.format(value)
            raise ValueError(msg)
        self._port = val

    # -----------------------------------------------------------
    @property
    def user(self):
        """The username to connect to the VSpere server."""
        return self._user

    # -----------------------------------------------------------
    @property
    def password(self):
        """The username to connect to the VSpere server."""
        return self._password

    # -----------------------------------------------------------
    @property
    def dc(self):
        """The name of the VSphere data center to use."""
        return self._dc

    # -----------------------------------------------------------
    @property
    def cluster(self):
        """The name of the VSphere cluster to use."""
        return self._cluster

    # -------------------------------------------------------------------------
    def as_dict(self, short=True):
        """
        Transforms the elements of the object into a dict

        @param short: don't include local properties in resulting dict.
        @type short: bool

        @return: structure as dict
        @rtype:  dict
        """

        res = super(BaseVsphereHandler, self).as_dict(short=short)
        res['host'] = self.host
        res['port'] = self.port
        res['user'] = self.user
        res['dc'] = self.dc
        res['cluster'] = self.cluster
        res['max_search_depth'] = self.max_search_depth
        res['password'] = None
        if self.password:
            if self.verbose > 4:
                res['password'] = self.password
            else:
                res['password'] = '*******'
        else:
            res['password'] = None

        return res

    # -------------------------------------------------------------------------
    def connect(self):

        LOG.debug("Connecting to vSphere host {h}:{p} as {u!r} ...".format(
            h=self.host, p=self.port, u=self.user))

        ssl_context = None
        if hasattr(ssl, '_create_unverified_context'):
            ssl_context = ssl._create_unverified_context()

        self.service_instance = SmartConnect(
            host=self.host, port=self.port, user=self.user, pwd=self.password,
            sslContext=ssl_context)

        if not self.service_instance:
            raise VSphereCannotConnectError(host=self.host, port=self.port, user=self.user)

    # -------------------------------------------------------------------------
    def disconnect(self):

        if self.service_instance:
            LOG.debug("Disconnecting from vSphere host {}.".format(self.host))
            Disconnect(self.service_instance)

        self.service_instance = None

    # -------------------------------------------------------------------------
    def get_obj(self, content, vimtype, name):

        obj = None
        container = content.viewManager.CreateContainerView(content.rootFolder, vimtype, True)
        for c in container.view:
            if c.name == name:
                obj = c
                break

        return obj

    # -------------------------------------------------------------------------
    def __del__(self):
        self.disconnect()


# =============================================================================

if __name__ == "__main__":

    pass

# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 list
