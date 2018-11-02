#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: Frank Brehm
@contact: frank.brehm@pixelpark.com
@copyright: © 2018 by Frank Brehm, Berlin
@summary: The module for special error classes on VSphere API operations.
"""
from __future__ import absolute_import

# Standard modules

# Own modules
from ..errors import FbHandlerError


# =============================================================================
class VSphereHandlerError(FbHandlerError):
    """Base class for all exception belonging to VSphere."""
    pass


# =============================================================================
class VSphereNoDatastoresFoundError(FbHandlerError):

    # -------------------------------------------------------------------------
    def __init__(self, msg=None):

        if not msg:
            msg = "No VSphere datastores found."
        self.msg = msg

    # -------------------------------------------------------------------------
    def __str__(self):

        return self.msg

# =============================================================================
class VSphereExpectedError(VSphereHandlerError):
    """Base class for all errors, which could be expected in application object
        and displayed without stack trace."""
    pass


# =============================================================================
class VSphereNameError(VSphereExpectedError):
    """Special error class for invalid Vsphere object names."""

    # -------------------------------------------------------------------------
    def __init__(self, name, obj_type=None):

        self.name = name
        self.obj_type = obj_type

    # -------------------------------------------------------------------------
    def __str__(self):

        if self.obj_type:
            msg = "Invalid name {n!r} for a {o} VSphere object.".format(
                n=self.name, o=self.obj_type)
        else:
            msg = "Invalid name {!r} for a VSphere object.".format(self.name)

        return msg

# =============================================================================
class VSphereDatacenterNotFoundError(VSphereExpectedError):
    """Special error class for the case, that the given datacenter
         was not found in VSphere."""

    # -------------------------------------------------------------------------
    def __init__(self, dc):

        self.dc = dc

    # -------------------------------------------------------------------------
    def __str__(self):

        msg = "The VSphere datacenter {!r} is not existing.".format(self.dc)
        return msg


# =============================================================================
class VSphereVmNotFoundError(VSphereExpectedError):
    """Special error class for the case, that the given VM was not found in VSphere."""

    # -------------------------------------------------------------------------
    def __init__(self, vm):

        self.vm = vm

    # -------------------------------------------------------------------------
    def __str__(self):

        msg = "The VSphere Virtual machine {!r} was not found.".format(self.vm)
        return msg


# =============================================================================
class VSphereNoDatastoreFoundError(VSphereExpectedError):
    """Special error class for the case, that no SAN based data store was with
        enogh free space was found."""

    # -------------------------------------------------------------------------
    def __init__(self, needed_bytes):

        self.needed_bytes = int(needed_bytes)

    # -------------------------------------------------------------------------
    def __str__(self):

        mb = float(self.needed_bytes) / 1024.0 / 1024.0
        gb = mb / 1024.0

        msg = (
            "No SAN based datastore found with at least {m:0.0f} MiB == {g:0.1f} GiB "
            "available space found.").format(m=mb, g=gb)
        return msg


# =============================================================================
class VSphereNetworkNotExistingError(VSphereExpectedError):
    """Special error class for the case, if the expected network is not existing."""

    # -------------------------------------------------------------------------
    def __init__(self, net_name):

        self.net_name = net_name

    # -------------------------------------------------------------------------
    def __str__(self):

        msg = "The network {!r} is not existing.".format(self.net_name)
        return msg


# =============================================================================
class VSphereCannotConnectError(VSphereExpectedError):
    """Special error class for the case, it cannot connect
        to the given vSphere server."""

    # -------------------------------------------------------------------------
    def __init__(self, host, port, user):

        self.host = host
        self.port = port
        self.user = user

    # -------------------------------------------------------------------------
    def __str__(self):

        msg = "Could not connect to the vSphere host {h}:{p} as user {u!r}.".format(
            h=self.host, p=self.port, u=self.user)
        return msg

# =============================================================================
class TimeoutCreateVmError(VSphereExpectedError):

    # -------------------------------------------------------------------------
    def __init__(self, vm, timeout):

        t_o = None
        try:
            t_o = float(timeout)
        except ValueError:
            pass
        self.timeout = t_o

        self.vm = vm

    # -------------------------------------------------------------------------
    def __str__(self):

        msg = "Timeout on creating VM {vm!r} after {to:0.1f} seconds.".format(
            vm=self.vm, to=self.timeout)
        return msg


# =============================================================================
if __name__ == "__main__":

    pass

# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 list
