#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@summary: The module for the BaseConfigOptions object.

@author: Frank Brehm
@contact: frank@brehm-online.com
@copyright: © 2026 by Frank Brehm, Berlin
"""

from __future__ import absolute_import

# Standard modules
import logging
import re
from abc import ABCMeta, abstractmethod

# Third party modules
from six import add_metaclass

# Own modules
from ..obj import FbGenericBaseObject
from ..xlate import XLATOR

# from ..common import is_sequence, pp, to_bool, to_str
# from ..xlate import XLATOR, format_list

__version__ = "0.1.0"
LOG = logging.getLogger(__name__)

_ = XLATOR.gettext


# =============================================================================
@add_metaclass(ABCMeta)
class BaseConfigOptions(FbGenericBaseObject):
    """Base class for all config options classes."""

    _argparse_prefix = "cfgoption"
    _defaults = {}
    _doc = {}

    # -------------------------------------------------------------------------
    def __init__(self, **kwargs):
        """Initialize this ConfigOptions object."""
        properties = self.properties()

        for prop_name in properties:
            default = self._defaults[prop_name]
            attr = "_" + prop_name
            setattr(self, attr, default)

        for arg_name in kwargs:
            if arg_name not in properties:
                msg = _("Unknown attribute {a!r} for class {c!r}.").format(
                    a=arg_name, c=self.__class__.__name__)
                raise AttributeError(msg)
            arg_val = kwargs[arg_name]
            setattr(self, arg_name, arg_val)

    # -------------------------------------------------------------------------
    def property_dict(self):
        """Return a dict with all properties as keys and their values."""
        props = {}

        for prop_name in self.properties():
            props[prop_name] = getattr(self, prop_name)

        return props

    # -------------------------------------------------------------------------
    def as_dict(self, short=True):
        """
        Transform the elements of the object into a dict.

        @param short: don't include local properties in resulting dict.
        @type short: bool

        @return: structure as dict
        @rtype:  dict
        """
        res = super(BaseConfigOptions, self).as_dict(short=short)

        res["properties"] = self.properties()

        props = self.property_dict()
        for prop_name in props:
            res[prop_name] = props[prop_name]

        return res

    # -------------------------------------------------------------------------
    @classmethod
    def properties(cls):
        """Try to get all names of properties of the current class retzurn them as a dict."""
        props = set()

        for attr_name in cls.__dict__:
            attr_class = cls.__dict__[attr_name].__class__.__name__
            if attr_class != "property":
                continue
            props.add(attr_name)

        return props

    # -------------------------------------------------------------------------
    @abstractmethod
    def __repr__(self):
        """Typecasting into a string for reproduction."""
        out = "<%s(" % (self.__class__.__name__)

        fields = []
        for prop_name in self.properties():
            prop_val = getattr(self, prop_name)

            if prop_val != self._defaults[prop_name]:
                fields.append("{n}={v!r}".format(n=prop_name, v=prop_val))

        out += ", ".join(fields) + ")>"
        return out

    # -------------------------------------------------------------------------
    @classmethod
    def argparse_option(cls, prop_name):
        """Return the appropriate command line option for the given property."""
        props = cls.properties()
        if prop_name not in props:
            msg = _("Wrong property {p!r} for class {c!r} given.").format(
                p=prop_name, c=cls.__name__)
            raise ValueError(msg)

        option = "--" + cls._argparse_prefix + "-" + re.sub(r"_", "-", prop_name)
        return option

    # -------------------------------------------------------------------------
    @classmethod
    def get_property_doc(cls, prop_name):
        """Return the appropriate docstring for the given property."""
        props = cls.properties()
        if prop_name not in props:
            msg = _("Wrong property {p!r} for class {c!r} given.").format(
                p=prop_name, c=cls.__name__)
            raise ValueError(msg)

        doc = "Unknown documentation."
        if prop_name in cls._doc:
            doc = cls._doc[prop_name]
        else:
            prop = getattr(cls, prop_name)
            doc = prop.__doc__

        return doc

# =============================================================================

if __name__ == "__main__":

    pass

# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
