#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: Frank Brehm
@contact: frank.brehm@pixelpark.com
@copyright: © 2020 by Frank Brehm, Berlin
@summary: This module implements specialized container datatypes providing
          alternatives to Python's general purpose built-in frozen_set, set and dict.
"""
from __future__ import absolute_import

# Standard modules
import os
import logging

try:
    from collections.abc import Set, MutableSet
except ImportError:
    from collections import Set, MutableSet

# Third party modules
import six

# Own modules
from .errors import FbError

from .common import is_sequence

from .obj import FbGenericBaseObject

from .xlate import XLATOR

__version__ = '0.1.6'
LOG = logging.getLogger(__name__)

_ = XLATOR.gettext
ngettext = XLATOR.ngettext


# =============================================================================
class WrongItemTypeError(TypeError, FbError):
    """Exeception class for the case, that a given parameter ist not of type str."""

    # -------------------------------------------------------------------------
    def __init__(self, item):

        self.item = item
        super(WrongItemTypeError, self).__init__()

    # -------------------------------------------------------------------------
    def __str__(self):

        msg = _("Item {item!r} must be of type {must!r}, but is of type {cls!r} instead.")
        return msg.format(
                item=self.item, must='str', cls=self.item.__class__.__name__)


# =============================================================================
class WrongCompareSetClassError(TypeError, FbError):
    """Exeception class for the case, that a given class ist not of an
       instance of CaseInsensitiveStringSet."""

    # -------------------------------------------------------------------------
    def __init__(self, other, expected=None):

        self.other_class = other.__class__.__name__
        self.expected = expected
        super(WrongCompareSetClassError, self).__init__()

    # -------------------------------------------------------------------------
    def __str__(self):

        msg = _("Object {o!r} is not a {e} object.")
        expected = 'CaseInsensitiveStringSet'
        if self.expected:
            expected = self.expected
        return msg.format(o=self.other_class, e=expected)

# =============================================================================
class FrozenCaseInsensitiveStringSet(Set, FbGenericBaseObject):
    """
    An immutable set, where the items are insensitive strings.
    The items MUST be of type string!
    It works like a set.
    """

    wrong_type_msg =  _("Item {item!r} must be of type {must!r}, but is of type {cls!r} instead.")

    # -------------------------------------------------------------------------
    def __init__(self, iterable=None):

        self._items = {}
        if iterable is not None:
            if not is_sequence(iterable):
                msg = _("Parameter {p!r} is not a sequence type, but a {c!r} object instead.")
                msg = msg.format(p='iterable', c=iterable.__class__.__name__)
                raise TypeError(msg)

            for item in iterable:

                if not isinstance(item, str):
                    raise WrongItemTypeError(item)
                ival = item.lower()
                self._items[ival] = item

    # -------------------------------------------------------------------------
    # Mandatory methods (ABC methods)

    # -------------------------------------------------------------------------
    def __contains__(self, value):
        """ The 'in' operator."""

        if not isinstance(value, str):
            raise WrongItemTypeError(value)

        ival = value.lower()
        if ival in self._items:
            return True
        return False

    # -------------------------------------------------------------------------
    def __iter__(self):

        for key in sorted(self._items.keys()):
            yield self._items[key]

    # -------------------------------------------------------------------------
    def __len__(self):
        return len(self._items)

    # -------------------------------------------------------------------------
    # Nice to have methods

    # -------------------------------------------------------------------------
    def __bool__(self):
        if self.__len__() > 0:
            return True
        return False

    # -------------------------------------------------------------------------
    def issubset(self, other):

        cls = self.__class__.__name__
        if not isinstance(other, FrozenCaseInsensitiveStringSet):
            raise WrongCompareSetClassError(other, cls)

        for item in self._items:
            if item not in other:
                return False

        return True

    # -------------------------------------------------------------------------
    def __le__(self, other):
        """The '<=' operator."""

        return self.issubset(other)

    # -------------------------------------------------------------------------
    def __lt__(self, other):
        """The '<' operator."""

        cls = self.__class__.__name__
        if not isinstance(other, FrozenCaseInsensitiveStringSet):
            raise WrongCompareSetClassError(other, cls)

        ret = True
        for item in self._items:
            if item not in other:
                ret = False
        if ret:
            if len(self) != len(other):
                return True
        return False

    # -------------------------------------------------------------------------
    def __eq__(self, other):
        """The '==' operator."""

        if not isinstance(other, FrozenCaseInsensitiveStringSet):
            return False

        if len(self) != len(other):
            return False

        for item in self._items:
            if item not in other:
                return False

        return True

    # -------------------------------------------------------------------------
    def __ne__(self, other):
        """The '!=' operator."""

        if self == other:
            return False
        return True

    # -------------------------------------------------------------------------
    def __gt__(self, other):
        """The '>' operator."""

        cls = self.__class__.__name__
        if not isinstance(other, FrozenCaseInsensitiveStringSet):
            raise WrongCompareSetClassError(other, cls)

        ret = True
        for item in other._items:
            if item not in self:
                ret = False
        if ret:
            if len(self) != len(other):
                return True

        return False

    # -------------------------------------------------------------------------
    def __ge__(self, other):
        """The '>=' operator."""

        cls = self.__class__.__name__
        if not isinstance(other, FrozenCaseInsensitiveStringSet):
            raise WrongCompareSetClassError(other, cls)

        for item in other._items:
            if item not in self:
                return False
        return True

    # -------------------------------------------------------------------------
    def __copy__(self):

        new_set = self.__class__()
        for item in self:
            ival = item.lower()
            new_set._items[ival] = item

        return new_set

    # -------------------------------------------------------------------------
    def copy(self):
        return self.__copy__()

    # -------------------------------------------------------------------------
    def values(self):

        return self.as_list()

    # -------------------------------------------------------------------------
    def __str__(self):

        if len(self) == 0:
            return "{}()".format(self.__class__.__name__)

        ret = "{}(".format(self.__class__.__name__)
        if len(self):
            ret += '['
            ret += ', '.join(map(lambda x: "{!r}".format(x), self.values()))
            ret += ']'
        ret += ')'

        return ret

    # -------------------------------------------------------------------------
    def __repr__(self):
        return str(self)

    # -------------------------------------------------------------------------
    def union(self, *others):

        cls = self.__class__.__name__
        for other in others:
            if not isinstance(other, FrozenCaseInsensitiveStringSet):
                raise WrongCompareSetClassError(other, cls)

        new_set = self.__copy__()
        for other in others:
            for item in other:
                if item not in new_set:
                    ival = item.lower()
                    new_set._items[ival] = item

        return new_set

    # -------------------------------------------------------------------------
    def __or__(self, *others):
        """The '|' operator."""

        return self.union(*others)

    # -------------------------------------------------------------------------
    def intersection(self, *others):

        cls = self.__class__.__name__
        for other in others:
            if not isinstance(other, FrozenCaseInsensitiveStringSet):
                raise WrongCompareSetClassError(other, cls)

        empty = []
        new_set = self.__class__(empty)
        for item in self:
            do_add = True
            for other in others:
                if item not in other:
                    do_add = False
            if do_add:
                ival = item.lower()
                new_set._items[ival] = item

        return new_set

    # -------------------------------------------------------------------------
    def __and__(self, *others):
        """The '&' operator."""

        return self.intersection(*others)

    # -------------------------------------------------------------------------
    def difference(self, *others):

        cls = self.__class__.__name__
        for other in others:
            if not isinstance(other, FrozenCaseInsensitiveStringSet):
                raise WrongCompareSetClassError(other, cls)

        empty = []
        new_set = self.__class__(empty)
        for item in self:
            do_add = True
            for other in others:
                if item in other:
                    do_add = False
            if do_add:
                ival = item.lower()
                new_set._items[ival] = item

        return new_set

    # -------------------------------------------------------------------------
    def __sub__(self, *others):
        """The '-' operator."""

        return self.difference(*others)

    # -------------------------------------------------------------------------
    def symmetric_difference(self, other):

        cls = self.__class__.__name__
        if not isinstance(other, FrozenCaseInsensitiveStringSet):
            raise WrongCompareSetClassError(other, self)

        new_set = self.__class__()

        for item in self:
            if item not in other:
                ival = item.lower()
                new_set._items[ival] = item

        for item in other:
            if item not in self:
                ival = item.lower()
                new_set._items[ival] = item

        return new_set

    # -------------------------------------------------------------------------
    def __xor__(self, other):
        """The '^' operator."""

        return self.symmetric_difference(other)

    # -------------------------------------------------------------------------
    def isdisjoint(self, other):

        cls = self.__class__.__name__
        if not isinstance(other, FrozenCaseInsensitiveStringSet):
            raise WrongCompareSetClassError(other, cls)

        for item in self:
            if item in other:
                return False

        for item in other:
            if item in self:
                return False

        return True

    # -------------------------------------------------------------------------
    def as_dict(self, short=True):
        """
        Transforms the elements of the object into a dict

        @param short: don't include local properties in resulting dict.
        @type short: bool

        @return: structure as dict
        @rtype:  dict
        """

        res = super(FrozenCaseInsensitiveStringSet, self).as_dict(short=short)

        res['items'] = self.values()

        return res

    # -------------------------------------------------------------------------
    def as_list(self):

        ret = []
        for item in self:
            ret.append(item)

        return ret


# =============================================================================

if __name__ == "__main__":

    pass

# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 list
