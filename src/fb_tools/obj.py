#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@summary: Module for base object classes, which are used everywhere in my projects.

@author: Frank Brehm
@contact: frank@brehm-online.com
@copyright: © 2018 - 2026 Frank Brehm, Berlin
"""

from __future__ import absolute_import

# Standard modules
import logging
import os

# Third party modules

# Own modules
from .base_obj import FbGenericBaseObject
from .descriptors import BooleanDescriptor
from .descriptors import IntegerDescriptor
from .descriptors import PathDescriptor
from .descriptors import StringDescriptor
from .descriptors import VersionDescriptor
from .errors import FbError
from .xlate import XLATOR

__version__ = "2.3.0"

LOG = logging.getLogger(__name__)

_ = XLATOR.gettext


# =============================================================================
class FbBaseObjectError(FbError):
    """Base error class useable by all descendand objects."""

    pass


# =============================================================================
class BasedirNotExistingError(FbBaseObjectError):
    """Special error class for the case, if the base directory is not existing."""

    # -------------------------------------------------------------------------
    def __init__(self, dir_name):
        """Initialise a BasedirNotExistingError exception."""
        self.dir_name = dir_name

    # -------------------------------------------------------------------------
    def __str__(self):
        """Typecast into a string object."""
        msg = _("The base directory {!r} is not existing or not " "a directory.").format(
            str(self.dir_name)
        )
        return msg


# =============================================================================
class FbBaseObject(FbGenericBaseObject):
    """
    Base class for all objects with some fundamental properties.

    Properties:
    * appname     (str - rw)
    * base_dir    (pathlib.Path - rw)
    * initialized (bool - rw)
    * verbose     (int - rw)
    * version     (Version - rw)

    Public attributes: None
    """

    appname = StringDescriptor(
        name="appname",
        stripped=True,
        not_empty=True,
        default_value=FbGenericBaseObject.get_generic_appname(),
    )
    base_dir = PathDescriptor(name="base_dir", default_value=os.getcwd())
    initialized = BooleanDescriptor(name="initialized", default_value=False)
    verbose = IntegerDescriptor(name="verbose", lower_limit=0, default_value=0)
    version = VersionDescriptor(name="version", default_value=__version__)

    # -------------------------------------------------------------------------
    def __init__(
        self, appname=None, verbose=0, version=__version__, base_dir=None, initialized=False
    ):
        """
        Initialise the base object.

        @param appname: name of the current running applicatio
        @type: str
        @param base_dir: base directory used for different purposes
        @type: str or pathlib.Path
        @param initialized: initialisation of this object is complete after init
        @type: bool
        @param verbose: verbosity level (0 - 9)
        @type: int
        @param version: version string of the current object or application
        @type: str

        Raises an exception on a uncoverable error.
        """
        if appname:
            self.appname = appname
        self.version = version
        self.verbose = verbose

        if base_dir:
            self.base_dir = base_dir
        self.base_dir = self.base_dir.resolve()

        self.initialized = initialized

    # -----------------------------------------------------------
    # @property
    # def base_dir(self):
    #     """Return the base directory, which can be used for different purposes."""
    #     return self._base_dir

    # @base_dir.setter
    # def base_dir(self, value):
    #     base_dir_path = pathlib.Path(value)
    #     if str(base_dir_path).startswith("~"):
    #         base_dir_path = base_dir_path.expanduser()
    #     if not base_dir_path.exists():
    #         msg = _("Base directory {!r} does not exists.").format(str(value))
    #         self.handle_error(msg, self.appname)
    #     elif not base_dir_path.is_dir():
    #         msg = _("Path for base directory {!r} is not a directory.").format(str(value))
    #         self.handle_error(msg, self.appname)
    #     else:
    #         self._base_dir = base_dir_path

    # -------------------------------------------------------------------------
    def __repr__(self):
        """Typecasting into a string for reproduction."""
        out = "<%s(" % (self.__class__.__name__)

        fields = []
        fields.append("appname={!r}".format(self.appname))
        fields.append("verbose={!r}".format(self.verbose))
        fields.append("version={!r}".format(self.version))
        fields.append("base_dir={!r}".format(self.base_dir))
        fields.append("initialized={!r}".format(self.initialized))

        out += ", ".join(fields) + ")>"
        return out

    # -------------------------------------------------------------------------
    def as_dict(self, short=True):
        """
        Transform the elements of the object into a dict.

        @param short: don't include local properties in resulting dict.
        @type short: bool

        @return: structure as dict
        @rtype:  dict
        """
        res = super(FbBaseObject, self).as_dict(short=short)

        res["appname"] = self.appname
        res["version"] = self.version
        res["verbose"] = self.verbose
        res["initialized"] = self.initialized
        res["base_dir"] = self.base_dir

        return res


# =============================================================================

if __name__ == "__main__":

    pass

# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
