#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@summary: This module implements specialized container datatypes.

They are providing alternatives to Python's general purpose built-in frozen_set, set and dict.

@author: Frank Brehm
@contact: frank@brehm-online.com
@copyright: © 2018 - 2026 by Frank Brehm, Berlin
"""

from __future__ import absolute_import

# Standard modules
import codecs
import logging
from collections.abc import Mapping
from collections.abc import MutableMapping
from collections.abc import MutableSequence
from collections.abc import MutableSet
from collections.abc import Sequence
from collections.abc import Set

# Third party modules

# Own modules
from . import DEFAULT_CODING_ERROR_HANDLER
from . import DEFAULT_ENCODING
from . import VALID_DECODE_ERROR_HANDLERS
from .common import is_sequence
from .common import to_bool
from .errors import FbError
from .obj import FbGenericBaseObject
from .xlate import XLATOR

__version__ = "2.1.0"
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
    def __init__(self, item, expected="str"):
        """Initialise a WrongItemTypeError exception."""
        self.item = item
        self.expected = expected
        super(WrongItemTypeError, self).__init__()

    # -------------------------------------------------------------------------
    def __str__(self):
        """Typecast into str."""
        msg = _("Item {item!r} must be of type {must!r}, but is of type {cls!r} instead.")
        return msg.format(item=self.item, must=self.expected, cls=self.item.__class__.__name__)


# =============================================================================
class WrongCompareSetClassError(TypeError, FbCollectionsError):
    """Exeception class for the case, that a given class ist not of an instance of CIStringSet."""

    # -------------------------------------------------------------------------
    def __init__(self, other, expected="CIStringSet"):
        """Initialise a WrongCompareSetClassError exception."""
        self.other_class = other.__class__.__name__
        self.expected = expected
        super(WrongCompareSetClassError, self).__init__()

    # -------------------------------------------------------------------------
    def __str__(self):
        """Typecast into str."""
        msg = _("Object {o!r} is not a {e} object.")
        return msg.format(o=self.other_class, e=self.expected)


# =============================================================================
class WrongKeyTypeError(TypeError, FbCollectionsError):
    """Exeception if a given key is from wrong type."""

    # -------------------------------------------------------------------------
    def __init__(self, key, expected="str"):
        """Initialise a WrongKeyTypeError exception."""
        self.key = key
        self.expected = expected
        super(WrongKeyTypeError, self).__init__()

    # -------------------------------------------------------------------------
    def __str__(self):
        """Typecast into str."""
        msg = _("Key {key!r} must be of type {must!r}, but is of type {cls!r} instead.")
        return msg.format(key=self.key, must=self.expected, cls=self.key.__class__.__name__)


# =============================================================================
class WrongUpdateClassError(TypeError, FbCollectionsError):
    """Exeception if an object for update is from the wrong type."""

    # -------------------------------------------------------------------------
    def __init__(self, other):
        """Initialise a WrongUpdateClassError exception."""
        self.other_class = other.__class__.__name__
        super(WrongUpdateClassError, self).__init__()

    # -------------------------------------------------------------------------
    def __str__(self):
        """Typecast into str."""
        msg = _(
            "Object is neither a {m} object, nor a sequential object, "
            "but a {o!r} object instead."
        )
        return msg.format(o=self.other_class, m="Mapping")


# =============================================================================
class CaseInsensitiveKeyError(KeyError, FbCollectionsError):
    """Exeception, if a key was not found."""

    # -------------------------------------------------------------------------
    def __init__(self, key):
        """Initialise a CaseInsensitiveKeyError exception."""
        self.key = key
        super(CaseInsensitiveKeyError, self).__init__()

    # -------------------------------------------------------------------------
    def __str__(self):
        """Typecast into str."""
        msg = _("Key {!r} is not existing.")
        return msg.format(self.key)


# =============================================================================
class CIInitfromSequenceError(TypeError, FbCollectionsError):
    """Exeception if an object for update is from the wrong type."""

    # -------------------------------------------------------------------------
    def __init__(self, item, emesg, expected="FrozenCIDict"):
        """Initialise a CIInitfromSequenceError exception."""
        self.item = item
        self.emesg = emesg
        self.expected = expected
        super(CIInitfromSequenceError, self).__init__()

    # -------------------------------------------------------------------------
    def __str__(self):
        """Typecast into str."""
        msg = _("Could update {ex} with {i!r}: {m}")
        return msg.format(ex=self.expected, i=self.item, m=self.emesg)


# =============================================================================
class CIInitfromTupleError(IndexError, FbCollectionsError):
    """Exeception if an object for update is from the wrong type."""

    # -------------------------------------------------------------------------
    def __init__(self, item, emesg, expected="FrozenCIDict"):
        """Initialise a CIInitfromTupleError exception."""
        self.item = item
        self.emesg = emesg
        self.expected = expected
        super(CIInitfromTupleError, self).__init__()

    # -------------------------------------------------------------------------
    def __str__(self):
        """Typecast into str."""
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
        """Initialise a FrozenCIStringSet object."""
        self._items = {}
        if iterable is not None:
            ok = False
            if is_sequence(iterable):
                ok = True
            elif isinstance(iterable, FrozenCIStringSet):
                ok = True
            if not ok:
                msg = _("Parameter {p!r} is not a sequence type, but a {c!r} object instead.")
                msg = msg.format(p="iterable", c=iterable.__class__.__qualname__)
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
        """Return, whether the value is existing - the 'in' operator."""
        if not isinstance(value, str):
            raise WrongItemTypeError(value)

        ival = value.lower()
        if ival in self._items:
            return True
        return False

    # -------------------------------------------------------------------------
    def __iter__(self):
        """Return an iterator over all entries."""
        for key in sorted(self._items.keys()):
            yield self._items[key]

    # -------------------------------------------------------------------------
    def __len__(self):
        """Return the length of the current set."""
        return len(self._items)

    # -------------------------------------------------------------------------
    # Nice to have methods

    def real_value(self, item):
        """Return the item with the original case."""
        if not isinstance(item, str):
            raise WrongItemTypeError(item)

        ival = item.lower()
        if ival not in self._items:
            raise KeyError(item)

        return self._items[ival]

    # -------------------------------------------------------------------------
    def __bool__(self):
        """Typecast into a boolean type."""
        if self.__len__() > 0:
            return True
        return False

    # -------------------------------------------------------------------------
    def issubset(self, other):
        """Return, whether the current set is an subset of the other set."""
        cls = self.__class__.__name__
        if not isinstance(other, FrozenCIStringSet):
            raise WrongCompareSetClassError(other, cls)

        for item in self._items:
            if item not in other:
                return False

        return True

    # -------------------------------------------------------------------------
    def __le__(self, other):
        """Return the '<=' operator."""
        return self.issubset(other)

    # -------------------------------------------------------------------------
    def __lt__(self, other):
        """Return the '<' operator."""
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
        """Return the '==' operator."""
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
        """Return the '!=' operator."""
        if self == other:
            return False
        return True

    # -------------------------------------------------------------------------
    def __gt__(self, other):
        """Return the '>' operator."""
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
        """Return the '>=' operator."""
        cls = self.__class__.__name__
        if not isinstance(other, FrozenCIStringSet):
            raise WrongCompareSetClassError(other, cls)

        for item in other._items:
            if item not in self:
                return False
        return True

    # -------------------------------------------------------------------------
    def __copy__(self):
        """Return a copy of the current set."""
        new_set = self.__class__()
        for item in self:
            ival = item.lower()
            new_set._items[ival] = item

        return new_set

    # -------------------------------------------------------------------------
    def copy(self):
        """Return a copy of the current set."""
        return self.__copy__()

    # -------------------------------------------------------------------------
    def values(self):
        """Return all values as a list."""
        return self.as_list()

    # -------------------------------------------------------------------------
    def __str__(self):
        """Typecast into string."""
        if len(self) == 0:
            return "{}()".format(self.__class__.__name__)

        ret = "{}(".format(self.__class__.__name__)
        if len(self):
            ret += "["
            ret += ", ".join(map(lambda x: "{!r}".format(x), self.values()))  # noqa: C417
            ret += "]"
        ret += ")"

        return ret

    # -------------------------------------------------------------------------
    def __repr__(self):
        """Typecast into string for reproduction."""
        return str(self)

    # -------------------------------------------------------------------------
    def union(self, *others):
        """Return a union of the current and the other set."""
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
        """Return the '|' operator."""
        return self.union(*others)

    # -------------------------------------------------------------------------
    def intersection(self, *others):
        """Return a set containing all values which are members of both sets."""
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
        """Return the '&' operator."""
        return self.intersection(*others)

    # -------------------------------------------------------------------------
    def difference(self, *others):
        """Return a set of own members, which are not members of the other set."""
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
        """Return the '-' operator."""
        return self.difference(*others)

    # -------------------------------------------------------------------------
    def symmetric_difference(self, other):
        """Return a set of members, which are exclusive existing in one of both sets."""
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
        """Return the '^' operator."""
        return self.symmetric_difference(other)

    # -------------------------------------------------------------------------
    def isdisjoint(self, other):
        """Return, whether all members of both sets are exclusive in one set."""
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
        Transform the elements of the object into a dict.

        @param short: don't include local properties in resulting dict.
        @type short: bool

        @return: structure as dict
        @rtype:  dict
        """
        res = super(FrozenCIStringSet, self).as_dict(short=short)

        res["items"] = self.values()

        return res

    # -------------------------------------------------------------------------
    def as_list(self):
        """Typecast into a list."""
        ret = []
        for item in self:
            ret.append(item)

        return ret


# =============================================================================
class CIStringSet(MutableSet, FrozenCIStringSet):
    """
    A mutable set, where the strings are case insensitive strings.

    The items MUST be of type string!
    It works like a set.
    """

    # -------------------------------------------------------------------------
    def add(self, value, keep=False):
        """Add a string to the current set, if it does not exists."""
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
        """Remove a string from current set, if it exists."""
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
        """Update the current set with the members of the other set."""
        for other in others:
            if not isinstance(other, FrozenCIStringSet):
                cls = self.__class__.__name__
                raise WrongCompareSetClassError(other, cls)

        for other in others:
            for item in other:
                self.add(item)

    # -------------------------------------------------------------------------
    def __ior__(self, *others):
        """Return the '|=' operator."""
        self.update(*others)

    # -------------------------------------------------------------------------
    def intersection_update(self, *others):
        """Remove all members on current set, which are not member of the other set."""
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
        """Return the '&=' operator."""
        self.intersection_update(*others)

    # -------------------------------------------------------------------------
    def difference_update(self, *others):
        """Remove all members on current set, which are member of the other set."""
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
        """Return the '-=' operator."""
        self.difference_update(*others)

    # -------------------------------------------------------------------------
    def symmetric_difference_update(self, other):
        """Update the set to a symmetric differencewith the other set."""
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
        """Return the '^=' operator."""
        self.symmetric_difference_update(other)

    # -------------------------------------------------------------------------
    def remove(self, value):
        """Remove the value from set, raise a KeyError if it is not existing."""
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
        """Remove and return an arbitrary element from the set."""
        if len(self) == 0:
            raise IndexError("pop() from empty list")

        key = self._items.keys()[0]
        value = self._items[key]
        del self._items[key]

        return value

    # -------------------------------------------------------------------------
    def clear(self):
        """Remove all elements from the set."""
        self._items = {}


# =============================================================================
class FrozenStringArray(Sequence, FbGenericBaseObject):
    """A list, where all items are strings."""

    default_encoding = DEFAULT_ENCODING
    default_coding_error_handler = DEFAULT_CODING_ERROR_HANDLER

    # -------------------------------------------------------------------------
    def __init__(
        self,
        iterable=None,
        /,
        lowcase=False,
        upcase=False,
        stripped=False,
        not_empty=False,
        raise_on_non_str=False,
        encoding=None,
        error_handler=None,
    ):
        """Initialise a FrozenStringArray object."""
        self._array = []

        self.lowcase = to_bool(lowcase)
        self.upcase = to_bool(upcase)
        self.stripped = to_bool(stripped)
        self.not_empty = to_bool(not_empty)
        self.raise_on_non_str = to_bool(raise_on_non_str)

        if encoding is None:
            encoding = self.default_encoding
        codec_info = codecs.lookup(str(encoding))
        self.encoding = codec_info.name

        given_error_handler = error_handler
        if error_handler is None:
            given_error_handler = self.default_coding_error_handler
        given_error_handler = str(given_error_handler).strip().lower()
        if given_error_handler in VALID_DECODE_ERROR_HANDLERS:
            self.error_handler = given_error_handler
        else:
            msg = _(
                "Invalid coding error handler {hdlr!r} given on init of a {cls} object."
            ).format(hdlr=error_handler, cls=self.__class__.__name__)
            raise LookupError(msg)

        if self.lowcase and self.upcase:
            msg = _(
                "The properties {lc!r} and {uc!r} of the {c} object must not be set to {w} "
                "at the same time."
            ).format(lc="lowcase", uc="upcase", c=self.__class__.__qualname__, r="True")
            raise ValueError(msg)

        if iterable is not None:
            if not is_sequence(iterable):
                msg = _("Parameter {p!r} is not a sequence type, but a {c!r} object instead.")
                msg = msg.format(p="iterable", c=iterable.__class__.__qualname__)
                raise TypeError(msg)

            for item in iterable:
                value = self._check_item(item)
                self._array.append(value)

    # -------------------------------------------------------------------------
    def __repr__(self):
        """Typecast into string for reproduction."""
        out = "<%s(" % (self.__class__.__name__)

        fields = []

        fields.append(f"{self._array!r}")

        if self.lowcase is not False:
            fields.append(f"lowcase={self.lowcase!r}")
        if self.upcase is not False:
            fields.append(f"upcase={self.upcase!r}")
        if self.stripped is not False:
            fields.append(f"stripped={self.stripped!r}")
        if self.not_empty is not False:
            fields.append(f"not_empty={self.not_empty!r}")
        if self.raise_on_non_str is not False:
            fields.append(f"raise_on_non_str={self.raise_on_non_str!r}")
        if self.encoding is not None:
            fields.append(f"encoding={self.encoding!r}")
        if self.error_handler is not None:
            fields.append(f"error_handler={self.error_handler!r}")

        out += ", ".join(fields) + ")>"

        return out

    # -------------------------------------------------------------------------
    def _val2str(self, value, raise_always=False):
        """Convert the value into a str object."""
        if isinstance(value, str):
            return value

        if isinstance(value, (bytes, bytearray)):
            return value.decode(encoding=self.encoding, errors=self.error_handler)

        if self.raise_on_non_str or raise_always:
            msg = _("Invalid type {typ} of {v!r} given for a {c}.").format(
                typ=value.__class__.__name__, v=value, c=self.__class__.__qualname__
            )
            raise TypeError(msg)

        return str(value)

    # -------------------------------------------------------------------------
    def _check_item(self, item, raise_always=False):
        """Check the given item for a usable value."""
        value = self._val2str(item, raise_always=raise_always)

        if self.lowcase:
            value = value.lower()
        elif self.upcase:
            value = value.upper()

        if self.stripped:
            value = value.strip()

        if self.not_empty and value == "":
            msg = _("The {c} object must not contain empty strings.").format(
                c=self.__class__.__qualname__
            )
            raise ValueError(msg)

        return value

    # -------------------------------------------------------------------------
    def __len__(self):
        """Return the the nuber of entries (keys) in this list/array."""
        return len(self._array)

    # -------------------------------------------------------------------------
    def _get_item(self, index):
        """Return an arbitrary item by the index."""
        idx = int(index)
        if idx >= len(self) or idx < (len(self) * -1):
            msg = _("Index {i} os out of range of the {c} object.").format(
                i=idx, c=self.__class__.__qualname__)
            raise IndexError(msg)
        return self._array[idx]

    # -------------------------------------------------------------------------
    def __getitem__(self, index):
        """Return an arbitrary item by the index."""
        return self._get_item(index)

    # -------------------------------------------------------------------------
    def __iter__(self):
        """Return an iterator over all items."""
        for item in self._array:
            yield item

    # -------------------------------------------------------------------------
    def __contains__(self, item):
        """Return, whether the given item exists (the 'in'-operator)."""
        check_item = self._check_item(item, raise_always=True)

        if check_item in self._array:
            return True

        return False

    # -------------------------------------------------------------------------
    def __reversed__(self):
        """Return a (Frozen)StringArray with reversed items."""
        new = self.__class__(
            lowcase=self.lowcase,
            upcase=self.upcase,
            stripped=self.stripped,
            not_empty=self.not_empty,
            raise_on_non_str=self.raise_on_non_str,
            encoding=self.encoding,
            error_handler=self.error_handler
        )

        new._array = reversed(self._array)

        return new

    # -------------------------------------------------------------------------
    def index(self, item):
        """Return the index of the given item."""
        check_item = self._check_item(item, raise_always=True)

        index = 0
        while index < len(self):
            if self[index] == check_item:
                return index
            index += 1

        msg = _("Item {!r} is not in array.").format(item)
        raise ValueError(msg)

    # -------------------------------------------------------------------------
    def as_list(self):
        """Typecast into a list."""
        ret = []
        for item in self:
            ret.append(item)

        return ret

    # -------------------------------------------------------------------------
    def list(self):
        """Typecast into a list."""
        return self.as_list()


# =============================================================================
class FrozenCIDict(Mapping, FbGenericBaseObject):
    """
    A dictionary, where the keys are case insensitive strings.

    The keys MUST be of type string!
    It works like a dict.
    """

    # -------------------------------------------------------------------------
    def __init__(self, first_param=None, **kwargs):
        """Initialise a FrozenCIDict object.

        Use the object dict.
        """
        self._map = {}

        if first_param is not None:

            # LOG.debug("First parameter type {t!r}: {p!r}".format(
            #     t=type(first_param), p=first_param))

            if isinstance(first_param, Mapping):
                self._update_from_mapping(first_param)
            elif first_param.__class__.__name__ == "zip":
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
                "key": key,
                "val": mapping[key],
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
                "key": key,
                "val": value,
            }

    # -------------------------------------------------------------------------
    def __copy__(self):
        """Return a copy of the current set."""
        return self.__class__(self.dict())

    # -------------------------------------------------------------------------
    def copy(self):
        """Return a copy of the current set."""
        return self.__copy__()

    # -------------------------------------------------------------------------
    def _get_item(self, key):
        """Return an arbitrary item by the key."""
        if not isinstance(key, str):
            raise WrongKeyTypeError(key)
        lkey = key.lower()
        if lkey in self._map:
            return self._map[lkey]["val"]

        raise CaseInsensitiveKeyError(key)

    # -------------------------------------------------------------------------
    def get(self, key):
        """Return an arbitrary item by the key."""
        return self._get_item(key)

    # -------------------------------------------------------------------------
    # The next four methods are requirements of the ABC.

    # -------------------------------------------------------------------------
    def __getitem__(self, key):
        """Return an arbitrary item by the key."""
        return self._get_item(key)

    # -------------------------------------------------------------------------
    def __iter__(self):
        """Return an iterator over all keys."""
        for key in self.keys():
            yield key

    # -------------------------------------------------------------------------
    def __len__(self):
        """Return the the nuber of entries (keys) in this dict."""
        return len(self._map)

    # -------------------------------------------------------------------------
    def __repr__(self):
        """Typecast into string for reproduction."""
        if len(self) == 0:
            return "{}()".format(self.__class__.__name__)

        ret = "{}({{".format(self.__class__.__name__)
        kargs = []
        for pair in self.items():
            arg = "{k!r}: {v!r}".format(k=pair[0], v=pair[1])
            kargs.append(arg)
        ret += ", ".join(kargs)
        ret += "})"

        return ret

    # -------------------------------------------------------------------------
    # The next methods aren't required, but nice for different purposes:

    # -------------------------------------------------------------------------
    def as_dict(self, short=True, pure=False):
        """
        Transform the elements of the object into a dict.

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
    def dict(self):  # noqa: A003
        """Typecast into a regular dict."""
        return self.as_dict(pure=True)

    # -------------------------------------------------------------------------
    def real_key(self, key):
        """Return the original notation of the given key."""
        if not isinstance(key, str):
            raise WrongKeyTypeError(key)

        lkey = key.lower()
        if lkey in self._map:
            return self._map[lkey]["key"]

        raise CaseInsensitiveKeyError(key)

    # -------------------------------------------------------------------------
    def __bool__(self):
        """Typecast into a boolean value."""
        if len(self._map) > 0:
            return True
        return False

    # -------------------------------------------------------------------------
    def __contains__(self, key):
        """Return, whether the given key exists(the 'in'-operator)."""
        if not isinstance(key, str):
            raise WrongKeyTypeError(key)

        if key.lower() in self._map:
            return True
        return False

    # -------------------------------------------------------------------------
    def keys(self):
        """Return a list with all keys in original notation."""
        return list(map(lambda x: self._map[x]["key"], sorted(self._map.keys())))  # noqa: C417

    # -------------------------------------------------------------------------
    def items(self):
        """Return a list of all items of the current dict.

        An item is a tuple, with the key in original notation and the value.
        """
        item_list = []

        for lkey in sorted(self._map.keys()):
            key = self._map[lkey]["key"]
            value = self._map[lkey]["val"]
            item_list.append((key, value))

        return item_list

    # -------------------------------------------------------------------------
    def values(self):
        """Return a list with all values of the current dict."""
        return list(map(lambda x: self._map[x]["val"], sorted(self._map.keys())))  # noqa: C417

    # -------------------------------------------------------------------------
    def __eq__(self, other):
        """Return the equality of current dict with another (the '=='-operator)."""
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
        """Return the not-equality of current dict with another (the '!='-operator)."""
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
        """Set the value of the given key."""
        if not isinstance(key, str):
            raise WrongKeyTypeError(key)

        lkey = key.lower()
        self._map[lkey] = {
            "key": key,
            "val": value,
        }

    # -------------------------------------------------------------------------
    def set(self, key, value):  # noqa: A003
        """Set the value of the given key."""
        self[key] = value

    # -------------------------------------------------------------------------
    def __delitem__(self, key):
        """Delete the entry on the given key.

        Raise a CaseInsensitiveKeyError, if the does not exists.
        """
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
        """Remove and return an arbitrary element from the dict."""
        if not isinstance(key, str):
            raise WrongKeyTypeError(key)

        if len(args) > 1:
            msg = _("The method {met}() expected at most {max} arguments, got {got}.").format(
                met="pop", max=2, got=(len(args) + 1)
            )
            raise TypeError(msg)

        lkey = key.lower()
        if lkey not in self._map:
            if args:
                return args[0]
            raise CaseInsensitiveKeyError(key)

        val = self._map[lkey]["val"]
        del self._map[lkey]

        return val

    # -------------------------------------------------------------------------
    def popitem(self):
        """Remove and return the first element from the dict."""
        if not len(self._map):
            return None

        key = self.keys()[0]
        lkey = key.lower()
        value = self[key]
        del self._map[lkey]
        return (key, value)

    # -------------------------------------------------------------------------
    def clear(self):
        """Remove all items from the dict."""
        self._map = {}

    # -------------------------------------------------------------------------
    def setdefault(self, key, default=None):
        """Set the item of the given key to a default value."""
        if not isinstance(key, str):
            raise WrongKeyTypeError(key)

        if key in self:
            return self[key]

        self[key] = default
        return default

    # -------------------------------------------------------------------------
    def update(self, other):
        """Update the current dict with the items of the other dict."""
        if isinstance(other, Mapping):
            self._update_from_mapping(other)
        elif other.__class__.__name__ == "zip":
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
