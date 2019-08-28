#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: Frank Brehm
@contact: frank.brehm@pixelpark.com
@copyright: © 2019 by Frank Brehm, Berlin
@summary: The module for a VSphere about info object.
"""
from __future__ import absolute_import

# Standard modules
import logging
import random
import re
import uuid


# Third party modules
from pyVmomi import vim

# Own modules
from ..xlate import XLATOR

from ..common import pp, to_bool

from ..obj import FbBaseObject

__version__ = '0.1.1'
LOG = logging.getLogger(__name__)

_ = XLATOR.gettext


# =============================================================================
class VsphereAboutInfo(FbBaseObject):

    # -------------------------------------------------------------------------
    def __init__(
            self, appname=None, verbose=0, version=__version__, base_dir=None, initialized=None):

        self._api_type = None
        self._name = None
        self._full_name = None

        super(VsphereAboutInfo, self).__init__(
            appname=appname, verbose=verbose, version=version, base_dir=base_dir)

        if initialized is not None:
            self.initialized = initialized

    # -----------------------------------------------------------
    @property
    def api_type(self):
        """The API type of the about object."""
        return self._api_type

    @api_type.setter
    def api_type(self, value):

        if value is None:
            self._api_type = None
            return
        v = str(value).strip()
        if v == '':
            self._api_type = None
        else:
            self._api_type = v

    # -----------------------------------------------------------
    @property
    def name(self):
        """The name of the about object."""
        return self._name

    @name.setter
    def name(self, value):

        if value is None:
            self._name = None
            return
        v = str(value).strip()
        if v == '':
            self._name = None
        else:
            self._name = v

    # -----------------------------------------------------------
    @property
    def full_name(self):
        """The full name of the about object."""
        return self._full_name

    @full_name.setter
    def full_name(self, value):

        if value is None:
            self._full_name = None
            return
        v = str(value).strip()
        if v == '':
            self._full_name = None
        else:
            self._full_name = v

    # -------------------------------------------------------------------------
    def as_dict(self, short=True):
        """
        Transforms the elements of the object into a dict

        @param short: don't include local properties in resulting dict.
        @type short: bool

        @return: structure as dict
        @rtype:  dict
        """

        res = super(VsphereAboutInfo, self).as_dict(short=short)
        res['api_type'] = self.api_type
        res['name'] = self.name
        res['full_name'] = self.full_name

        return res

    # -------------------------------------------------------------------------
    @classmethod
    def from_summary(cls, data, appname=None, verbose=0, base_dir=None):

        if not isinstance(data, vim.AboutInfo):
            msg = _("Parameter {t!r} must be a {e}, {v!r} was given.").format(
                t='data', e='vim.AboutInfo', v=data)
            raise TypeError(msg)

        params = {
            'appname': appname,
            'verbose': verbose,
            'base_dir': base_dir,
            'initialized': False,
        }

        if verbose > 2:
            LOG.debug(_("Creating {} object from:").format(cls.__name__) + '\n' + pp(params))
        info = cls(**params)

#        'about': (vim.AboutInfo) {
#               dynamicType = <unset>,
#               dynamicProperty = (vmodl.DynamicProperty) [],
#               name = 'VMware vCenter Server',
#               fullName = 'VMware vCenter Server 6.5.0 build-8024368',
#               vendor = 'VMware, Inc.',
#               version = '6.5.0',
#               build = '8024368',
#               localeVersion = 'INTL',
#               localeBuild = '000',
#               osType = 'linux-x64',
#               productLineId = 'vpx',
#               apiType = 'VirtualCenter',
#               apiVersion = '6.5',
#               instanceUuid = 'ea1b28ca-0d17-4292-ab04-189e57ec9629',
#               licenseProductName = 'VMware VirtualCenter Server',
#               licenseProductVersion = '6.0'
#        },

        info.api_type = data.apiType
        info.name = data.name
        info.full_name = data.fullName

        info.initialized = True

        return info

    # -------------------------------------------------------------------------
    def __copy__(self):

        info = VsphereAboutInfo(
            appname=self.appname, verbose=self.verbose, base_dir=self.base_dir,
            initialized=False)

        info.api_type = self.api_type
        info.name = self.name
        info.full_name = self.fullName


        return info

# =============================================================================

if __name__ == "__main__":

    pass

# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 list
