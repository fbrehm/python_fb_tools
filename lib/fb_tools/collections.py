#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: Frank Brehm
@contact: frank.brehm@pixelpark.com
@copyright: © 2021 by Frank Brehm, Berlin
@summary: This module implements specialized container datatypes providing
          alternatives to Python's general purpose built-in frozen_set, set and dict.
"""
from __future__ import absolute_import

# Standard modules
import logging

try:
    from collections.abc import Set, MutableSet
    from collections.abc import Mapping, MutableMapping
except ImportError:
    from collections import Set, MutableSet
    from collections import Mapping, MutableMapping

# Third party modules

# Own modules
from .errors import FbError

from .common import is_sequence

from .obj import FbGenericBaseObject

from .xlate import XLATOR

__version__ = '1.0.0'
LOG = logging.getLogger(__name__)

_ = XLATOR.gettext
ngettext = XLATOR.ngettext


# =============================================================================
class FbCollectionsError(FbError):
    """Base class for all self defined execeptiond in this module."""

    pass


# =============================================================================
class WrongItemTypeError(TypeError, FbCollectionsError):
    """Exeception class for the case, that a given parameter ist not of type str."""

    # -------------------------------------------------------------------------
    def __init__(self, item, expected='str'):

        self.item = item
        self.expected = expected
        super(WrongItemTypeError, self).__init__()

    # -------------------------------------------------------------------------
    def __str__(self):

        msg = _("Item {item!r} must be of type {must!r}, but is of type {cls!r} instead.")
        return msg.format(item=self.item, must=self.expected, cls=self.item.__class__.__name__)


# =============================================================================
class WrongCompareSetClassError(TypeError, FbCollectionsError):
    """Exeception class for the case, that a given class ist not of an
       instance of CIStringSet."""

    # -------------------------------------------------------------------------
    def __init__(self, other, expected='CIStringSet'):

        self.other_class = other.__class__.__name__
        self.expected = expected
        super(WrongCompareSetClassError, self).__init__()

    # -------------------------------------------------------------------------
    def __str__(self):

        msg = _("Object {o!r} is not a {e} object.")
        return msg.format(o=self.other_class, e=self.expected)


# =============================================================================
class WrongKeyTypeError(TypeError, FbCollectionsError):

    # -------------------------------------------------------------------------
    def __init__(self, key, expected='str'):

        self.key = key
        self.expected = expected
        super(WrongKeyTypeError, self).__init__()

    # -------------------------------------------------------------------------
    def __str__(self):

        msg = _("Key {key!r} must be of type {must!r}, but is of type {cls!r} instead.")
        return msg.format(key=self.key, must=self.expected, cls=self.key.__class__.__name__)


# =============================================================================
class WrongUpdateClassError(TypeError, FbCollectionsError):

    # -------------------------------------------------------------------------
    def __init__(self, other):

        self.other_class = other.__class__.__name__
        super(WrongUpdateClassError, self).__init__()

    # -------------------------------------------------------------------------
    def __str__(self):

        msg = _(
            "Object is neither a {m} object, nor a sequential object, "
            "but a {o!r} object instead.")
        return msg.format(o=self.other_class, m="Mapping")


# =============================================================================
class CaseInsensitiveKeyError(KeyError, FbCollectionsError):

    # -------------------------------------------------------------------------
    def __init__(self, key):

        self.key = key
        super(CaseInsensitiveKeyError, self).__init__()

    # -------------------------------------------------------------------------
    def __str__(self):

        msg = _("Key {!r} is not existing.")
        return msg.format(self.key)


# =============================================================================
class CIInitfromSequenceError(TypeError, FbCollectionsError):

    # -------------------------------------------------------------------------
    def __init__(self, item, emesg, expected='FrozenCIDict'):

        self.item = item
        self.emesg = emesg
        self.expected = expected
        super(CIInitfromSequenceError, self).__init__()

    # -------------------------------------------------------------------------
    def __str__(self):

        msg = _("Could update {ex} with {i!r}: {m}")
        return msg.format(ex=self.expected, i=self.item, m=self.emesg)


# =============================================================================
class CIInitfromTupleError(IndexError, FbCollectionsError):

    # -------------------------------------------------------------------------
    def __init__(self, item, emesg, expected='FrozenCIDict'):

        self.item = item
        self.emesg = emesg
        self.expected = expected
        super(CIInitfromTupleError, self).__init__()

    # -------------------------------------------------------------------------
    def __str__(self):

        msg = _("Could update {ex} with {i!r}: {m}")
        return msg.format(ex=self.expected, i=self.item, m=self.emesg)


# =============================================================================
class FrozenCIStringSet(Set, FbGenericBaseObject):
    """
    An immutable set, where the items are insensitive strings.
    The items MUST be of type string!
    It works like a set.
    """

    # -------------------------------------------------------------------------
    def __init__(self, iterable=None):

        self._items = {}
        if iterable is not None:
            ok = False
            if is_sequence(iterable):
                ok = True
            elif isinstance(iterable, FrozenCIStringSet):
                ok = True
            if not ok:
                msg = _("Parameter {p!r} is not a sequence type, but a {c!r} object instead.")
                msg = msg.format(p='iterable', c=iterable.__class__.__qualname__)
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

    def real_value(self, item):

        if not isinstance(item, str):
            raise WrongItemTypeError(item)

        ival = item.lower()
        if ival not in self._items:
            raise KeyError(item)

        return self._items[ival]

    # -------------------------------------------------------------------------
    def __bool__(self):
        if self.__len__() > 0:
            return True
        return False

    # -------------------------------------------------------------------------
    def issubset(self, other):

        cls = self.__class__.__name__
        if not isinstance(other, FrozenCIStringSet):
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
        if not isinstance(other, FrozenCIStringSet):
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

        if not isinstance(other, FrozenCIStringSet):
            return False

        if isinstance(self, CIStringSet):
            if not isinstance(other, CIStringSet):
                return False
        else:
            if isinstance(other, CIStringSet):
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
        if not isinstance(other, FrozenCIStringSet):
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
        if not isinstance(other, FrozenCIStringSet):
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
            if not isinstance(other, FrozenCIStringSet):
                raise WrongCompareSetClassError(other, cls)

        new_set = self.__copy__()
        for other in others:
            for item in other:
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
            if not isinstance(other, FrozenCIStringSet):
                raise WrongCompareSetClassError(other, cls)

        new_set = self.__class__()
        for item in self:
            do_add = True
            value = item
            for other in others:
                if item in other:
                    value = other.real_value(item)
                else:
                    do_add = False
            if do_add:
                ival = item.lower()
                new_set._items[ival] = value

        return new_set

    # -------------------------------------------------------------------------
    def __and__(self, *others):
        """The '&' operator."""

        return self.intersection(*others)

    # -------------------------------------------------------------------------
    def difference(self, *others):

        cls = self.__class__.__name__
        for other in others:
            if not isinstance(other, FrozenCIStringSet):
                raise WrongCompareSetClassError(other, cls)

        new_set = self.__class__()
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
        if not isinstance(other, FrozenCIStringSet):
            raise WrongCompareSetClassError(other, cls)

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
        if not isinstance(other, FrozenCIStringSet):
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

        res = super(FrozenCIStringSet, self).as_dict(short=short)

        res['items'] = self.values()

        return res

    # -------------------------------------------------------------------------
    def as_list(self):

        ret = []
        for item in self:
            ret.append(item)

        return ret

# =============================================================================
class CIStringSet(MutableSet, FrozenCIStringSet):
    """
    A mutable set, where the strings are insensitive strings.
    The items MUST be of type string!
    It works like a set.
    """

    # -------------------------------------------------------------------------
    def add(self, value, keep=False):

        vals = []
        if is_sequence(value):
            vals = value
        elif isinstance(value, FrozenCIStringSet):
            vals = value
        else:
            vals = [value]

        for val in vals:
            if not isinstance(val, str):
                raise WrongItemTypeError(val)

            if keep and val in self:
                continue

            ival = val.lower()
            self._items[ival] = val

    # -------------------------------------------------------------------------
    def discard(self, value):

        vals = []
        if is_sequence(value):
            vals = value
        elif isinstance(value, FrozenCIStringSet):
            vals = value
        else:
            vals = [value]

        for val in vals:
            if not isinstance(val, str):
                raise WrongItemTypeError(val)

            ival = val.lower()
            if ival in self._items:
                del self._items[ival]

    # -------------------------------------------------------------------------
    def update(self, *others):

        for other in others:
            if not isinstance(other, FrozenCIStringSet):
                cls = self.__class__.__name__
                raise WrongCompareSetClassError(other, cls)

        for other in others:
            for item in other:
                self.add(item)

    # -------------------------------------------------------------------------
    def __ior__(self, *others):
        """The '|=' operator."""

        self.update(*others)

    # -------------------------------------------------------------------------
    def intersection_update(self, *others):

        for other in others:
            if not isinstance(other, FrozenCIStringSet):
                cls = self.__class__.__name__
                raise WrongCompareSetClassError(other, cls)

        for item in self:
            for other in others:
                value = item
                if item in other:
                    value = other.real_value(item)
                else:
                    self.discard(item)
                    break
                if value != item:
                    self.add(value)

    # -------------------------------------------------------------------------
    def __iand__(self, *others):
        """The '&=' operator."""

        self.intersection_update(*others)

    # -------------------------------------------------------------------------
    def difference_update(self, *others):

        for other in others:
            if not isinstance(other, CIStringSet):
                cls = self.__class__.__name__
                raise WrongCompareSetClassError(other, cls)

        for item in self:
            for other in others:
                if item in other:
                    self.discard(item)
                    break

    # -------------------------------------------------------------------------
    def __isub__(self, *others):
        """The '-=' operator."""

        self.difference_update(*others)

    # -------------------------------------------------------------------------
    def symmetric_difference_update(self, other):

        if not isinstance(other, CIStringSet):
            cls = self.__class__.__name__
            raise WrongCompareSetClassError(other, cls)

        for item in self:
            if item in other:
                self.discard(item)

        for item in other:
            if item not in self:
                self.add(item)

    # -------------------------------------------------------------------------
    def __ixor__(self, other):
        """The '|=' operator."""

        self.symmetric_difference_update(other)

    # -------------------------------------------------------------------------
    def remove(self, value):

        vals = []
        if is_sequence(value):
            vals = value
        elif isinstance(value, FrozenCIStringSet):
            vals = value
        else:
            vals = [value]

        for val in vals:
            if not isinstance(val, str):
                raise WrongItemTypeError(val)

            ival = val.lower()
            if ival in self._items:
                del self._items[ival]
            else:
                raise KeyError(value)

    # -------------------------------------------------------------------------
    def pop(self):

        if len(self) == 0:
            raise IndexError("pop() from empty list")

        key = self._items.keys()[0]
        value = self._items[key]
        del self._items[key]

        return value

    # -------------------------------------------------------------------------
    def clear(self):

        self._items = {}


# =============================================================================
class FrozenCIDict(Mapping, FbGenericBaseObject):
    """
    A dictionary, where the keys are case insensitive strings.
    The keys MUST be of type string!
    It works like a dict.
    """

    # -------------------------------------------------------------------------
    def __init__(self, first_param=None, **kwargs):
        '''Use the object dict'''

        self._map = dict()

        if first_param is not None:

            # LOG.debug("First parameter type {t!r}: {p!r}".format(
            #     t=type(first_param), p=first_param))

            if isinstance(first_param, Mapping):
                self._update_from_mapping(first_param)
            elif first_param.__class__.__name__ == 'zip':
                self._update_from_mapping(dict(first_param))
            elif is_sequence(first_param):
                self._update_from_sequence(first_param)
            else:
                raise WrongUpdateClassError(first_param)

        if kwargs:
            self._update_from_mapping(kwargs)

    # -------------------------------------------------------------------------
    def _update_from_mapping(self, mapping):

        for key in mapping.keys():
            if not isinstance(key, str):
                raise WrongKeyTypeError(key)
            lkey = key.lower()
            self._map[lkey] = {
                'key': key,
                'val': mapping[key],
            }

    # -------------------------------------------------------------------------
    def _update_from_sequence(self, sequence):

        for token in sequence:
            try:
                key = token[0]
                value = token[1]
            except TypeError as e:
                raise CIInitfromSequenceError(token, str(e), self.__class__.__name__)
            except IndexError as e:
                raise CIInitfromTupleError(token, str(e), self.__class__.__name__)
            if not isinstance(key, str):
                raise WrongKeyTypeError(key)
            lkey = key.lower()
            self._map[lkey] = {
                'key': key,
                'val': value,
            }

    # -------------------------------------------------------------------------
    def __copy__(self):

        return self.__class__(self.dict())

    # -------------------------------------------------------------------------
    def copy(self):
        return self.__copy__()

    # -------------------------------------------------------------------------
    def _get_item(self, key):

        if not isinstance(key, str):
            raise WrongKeyTypeError(key)
        lkey = key.lower()
        if lkey in self._map:
            return self._map[lkey]['val']

        raise CaseInsensitiveKeyError(key)

    # -------------------------------------------------------------------------
    def get(self, key):
        return self._get_item(key)

    # -------------------------------------------------------------------------
    # The next four methods are requirements of the ABC.

    # -------------------------------------------------------------------------
    def __getitem__(self, key):
        return self._get_item(key)

    # -------------------------------------------------------------------------
    def __iter__(self):

        for key in self.keys():
            yield key

    # -------------------------------------------------------------------------
    def __len__(self):
        return len(self._map)

    # -------------------------------------------------------------------------
    def __repr__(self):

        if len(self) == 0:
            return "{}()".format(self.__class__.__name__)

        ret = "{}({{".format(self.__class__.__name__)
        kargs = []
        for pair in self.items():
            arg = "{k!r}: {v!r}".format(k=pair[0], v=pair[1])
            kargs.append(arg)
        ret += ', '.join(kargs)
        ret += '})'

        return ret

    # -------------------------------------------------------------------------
    # The next methods aren't required, but nice for different purposes:

    # -------------------------------------------------------------------------
    def as_dict(self, short=True, pure=False):
        """
        Transforms the elements of the object into a dict

        @param short: don't include local properties in resulting dict.
        @type short: bool
        @param pure: Only include keys and values of the internal map
        @type pure: bool

        @return: structure as dict
        @rtype:  dict
        """

        if pure:
            res = {}
        else:
            res = super(FrozenCIDict, self).as_dict(short=short)
        for pair in self.items():
            if isinstance(pair[1], FbGenericBaseObject):
                val = pair[1].as_dict(short=short)
            else:
                val = pair[1]
            res[pair[0]] = val

        return res

    # -------------------------------------------------------------------------
    def dict(self):

        return self.as_dict(pure=True)

    # -------------------------------------------------------------------------
    def real_key(self, key):

        if not isinstance(key, str):
            raise WrongKeyTypeError(key)

        lkey = key.lower()
        if lkey in self._map:
            return self._map[lkey]['key']

        raise CaseInsensitiveKeyError(key)

    # -------------------------------------------------------------------------
    def __bool__(self):

        if len(self._map) > 0:
            return True
        return False

    # -------------------------------------------------------------------------
    def __contains__(self, key):

        if not isinstance(key, str):
            raise WrongKeyTypeError(key)

        if key.lower() in self._map:
            return True
        return False

    # -------------------------------------------------------------------------
    def keys(self):

        return list(map(lambda x: self._map[x]['key'], sorted(self._map.keys())))

    # -------------------------------------------------------------------------
    def items(self):

        item_list = []

        for lkey in sorted(self._map.keys()):
            key = self._map[lkey]['key']
            value = self._map[lkey]['val']
            item_list.append((key, value))

        return item_list

    # -------------------------------------------------------------------------
    def values(self):

        return list(map(lambda x: self._map[x]['val'], sorted(self._map.keys())))

    # -------------------------------------------------------------------------
    def __eq__(self, other):

        if not isinstance(other, FrozenCIDict):
            return False

        if isinstance(self, CIDict) and not isinstance(other, CIDict):
            return False

        if not isinstance(self, CIDict) and isinstance(other, CIDict):
            return False

        if len(self) != len(other):
            return False

        # First compare keys
        my_keys = []
        other_keys = []

        for key in self.keys():
            my_keys.append(key.lower())

        for key in other.keys():
            other_keys.append(key.lower())

        if my_keys != other_keys:
            return False

        # Now compare values
        for key in self.keys():
            if self[key] != other[key]:
                return False

        return True

    # -------------------------------------------------------------------------
    def __ne__(self, other):

        if self == other:
            return False

        return True

# =============================================================================
class CIDict(MutableMapping, FrozenCIDict):
    """
    A dictionary, where the keys are case insensitive strings.
    The keys MUST be of type string!
    It works like a dict.
    """

    # -------------------------------------------------------------------------
    # The next two methods are requirements of the ABC.

    # -------------------------------------------------------------------------
    def __setitem__(self, key, value):

        if not isinstance(key, str):
            raise WrongKeyTypeError(key)

        lkey = key.lower()
        self._map[lkey] = {
            'key': key,
            'val': value,
        }

    # -------------------------------------------------------------------------
    def set(self, key, value):

        self[key] = value

    # -------------------------------------------------------------------------
    def __delitem__(self, key):

        if not isinstance(key, str):
            raise WrongKeyTypeError(key)

        lkey = key.lower()
        if lkey not in self._map:
            raise CaseInsensitiveKeyError(key)

        del self._map[lkey]

    # -------------------------------------------------------------------------
    # The next methods aren't required, but nice for different purposes:

    # -------------------------------------------------------------------------
    def pop(self, key, *args):

        if not isinstance(key, str):
            raise WrongKeyTypeError(key)

        if len(args) > 1:
            msg = _("The method {met}() expected at most {max} arguments, got {got}.").format(
                met='pop', max=2, got=(len(args) + 1))
            raise TypeError(msg)

        lkey = key.lower()
        if lkey not in self._map:
            if args:
                return args[0]
            raise CaseInsensitiveKeyError(key)

        val = self._map[lkey]['val']
        del self._map[lkey]

        return val

    # -------------------------------------------------------------------------
    def popitem(self):

        if not len(self._map):
            return None

        key = self.keys()[0]
        lkey = key.lower()
        value = self[key]
        del self._map[lkey]
        return (key, value)

    # -------------------------------------------------------------------------
    def clear(self):

        self._map = dict()

    # -------------------------------------------------------------------------
    def setdefault(self, key, default=None):

        if not isinstance(key, str):
            raise WrongKeyTypeError(key)

        if key in self:
            return self[key]

        self[key] = default
        return default

    # -------------------------------------------------------------------------
    def update(self, other):

        if isinstance(other, Mapping):
            self._update_from_mapping(other)
        elif other.__class__.__name__ == 'zip':
            self._update_from_mapping(dict(other))
        elif is_sequence(other):
            self._update_from_sequence(other)
        else:
            WrongUpdateClassError(other)


# =============================================================================

if __name__ == "__main__":

    pass

# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 list
