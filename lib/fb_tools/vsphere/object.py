#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: Frank Brehm
@contact: frank.brehm@pixelpark.com
@copyright: © 2019 by Frank Brehm, Berlin
@summary: The base module module for a VSphere object.
"""
from __future__ import absolute_import

# Standard modules
import re
import logging
import copy

# Third party modules

# Own modules
from ..xlate import XLATOR

from ..common import pp, RE_TF_NAME

from ..obj import FbBaseObject

from .errors import VSphereNameError

__version__ = '1.2.1'
LOG = logging.getLogger(__name__)

_ = XLATOR.gettext


# =============================================================================
class VsphereObject(FbBaseObject):

    re_ws = re.compile(r'\s+')

    repr_fields = (
        'name', 'obj_type', 'name_prefix', 'status', 'config_status',
        'appname', 'verbose', 'version')
    available_status_color = ['red', 'yellow', 'green', 'gray']

    # -------------------------------------------------------------------------
    def __init__(
        self, name=None, obj_type=None, name_prefix="unknown", status='gray', config_status='gray',
            appname=None, verbose=0, version=__version__, base_dir=None, initialized=None):

        self._name = None
        self._obj_type = None
        self._name_prefix = None
        self._status = None
        self._config_status = None

        super(VsphereObject, self).__init__(
            appname=appname, verbose=verbose, version=version, base_dir=base_dir)

        self.status = status
        self.config_status = config_status
        self.obj_type = obj_type
        self.name_prefix = name_prefix
        self.name = name

        if initialized is not None:
            self.initialized = initialized

    # -----------------------------------------------------------
    @property
    def obj_type(self):
        """The type of the VSphere object."""
        return self._obj_type

    @obj_type.setter
    def obj_type(self, value):

        if value is None:
            msg = _("The type of a {} may not be None.").format('VsphereObject')
            raise TypeError(msg)

        val = self.re_ws.sub('', str(value))
        if val == '':
            msg = _("Invalid {w}.{p} {v!r}.").format(
                w='VsphereObject', p='type', v=value)
            raise ValueError(msg)

        self._obj_type = val

    # -----------------------------------------------------------
    @property
    def status(self):
        """Overall alarm status of the object."""
        return self._status

    @status.setter
    def status(self, value):
        if value is None:
            self._status = 'gray'
            return

        val = str(value).strip().lower()
        if val == '':
            self._status = 'gray'
            return
        if val not in self.available_status_color:
            msg = _("Invalid {w}.{p} {v!r}.").format(
                w='VsphereObject', p='status', v=value)
            raise ValueError(msg)

        self._status = val

    # -----------------------------------------------------------
    @property
    def config_status(self):
        """Overall config status of the object."""
        return self._config_status

    @config_status.setter
    def config_status(self, value):
        if value is None:
            self._config_status = 'gray'
            return

        val = str(value).strip().lower()
        if val == '':
            self._config_status = 'gray'
            return
        if val not in self.available_status_color:
            msg = _("Invalid {w}.{p} {v!r}.").format(
                w='VsphereObject', p='config_status', v=value)
            raise ValueError(msg)

        self._config_status = val

    # -----------------------------------------------------------
    @property
    def name_prefix(self):
        """The prefix for the terraform name."""
        return self._name_prefix

    @name_prefix.setter
    def name_prefix(self, value):

        if value is None:
            raise TypeError(_("The name prefix of a {} may not be None.").format('VsphereObject'))

        val = self.re_ws.sub('', str(value))
        if val == '':
            msg = _("Invalid name prefix {p!r} for a {o}.").format(p=value, o='VsphereObject')
            raise ValueError(msg)

        self._name_prefix = val

    # -----------------------------------------------------------
    @property
    def name(self):
        """The name of the datastore object."""
        return self._name

    @name.setter
    def name(self, value):

        if value is None:
            raise VSphereNameError(value, self.obj_type)

        val = self.re_ws.sub('_', str(value).strip())
        if val == '':
            raise VSphereNameError(value, self.obj_type)

        self._name = val

    # -----------------------------------------------------------
    @property
    def tf_name(self):
        """The name of the bject how used in terraform."""
        if self.name is None:
            return None
        return self.name_prefix + '_' + RE_TF_NAME.sub('_', self.name.lower())

    # -----------------------------------------------------------
    @property
    def var_name(self):
        """The name of the variable used in terraform definitions."""
        return self.obj_type + '_' + RE_TF_NAME.sub('_', self.name.lower())

    # -------------------------------------------------------------------------
    def as_dict(self, short=True):
        """
        Transforms the elements of the object into a dict

        @param short: don't include local properties in resulting dict.
        @type short: bool

        @return: structure as dict
        @rtype:  dict
        """

        res = super(VsphereObject, self).as_dict(short=short)
        res['name'] = self.name
        res['obj_type'] = self.obj_type
        res['name_prefix'] = self.name_prefix
        res['tf_name'] = self.tf_name
        res['var_name'] = self.var_name
        res['repr_fields'] = copy.copy(self.repr_fields)
        res['status'] = self.status
        res['config_status'] = self.config_status

        return res

    # -------------------------------------------------------------------------
    def __str__(self):
        """
        Typecasting function for translating object structure
        into a string

        @return: structure as string
        @rtype:  str
        """

        return pp(self.as_dict(short=True))

    # -------------------------------------------------------------------------
    def __repr__(self):
        """Typecasting into a string for reproduction."""

        out = "<%s(" % (self.__class__.__name__)

        fields = []
        for field in self.repr_fields:
            token = "{f}={v!r}".format(f=field, v=getattr(self, field))
            fields.append(token)

        out += ", ".join(fields) + ")>"
        return out


# =============================================================================

if __name__ == "__main__":

    pass

# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 list
