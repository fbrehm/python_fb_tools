#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@summary: A module for a collection of descriptors.

These descriptors may be used for data properties in classes.

@author: Frank Brehm
@contact: frank@brehm-online.com
@copyright: © 2019 - 2026 Frank Brehm, Berlin
"""

from __future__ import absolute_import

# Standard modules
import codecs
import logging
from abc import ABCMeta, abstractmethod
from pathlib import Path
from pathlib import PurePath
from pathlib import PurePosixPath

# Third party modules
from six import add_metaclass

try:
    from semver import Version
except ImportError:
    from semver import VersionInfo as Version


# Own modules
from . import DEFAULT_CODING_ERROR_HANDLER
from . import DEFAULT_ENCODING
from . import VALID_DECODE_ERROR_HANDLERS
from .common import is_sequence
from .common import to_bool
from .xlate import XLATOR

__version__ = "0.11.5"
LOG = logging.getLogger(__name__)

_ = XLATOR.gettext


# =============================================================================
@add_metaclass(ABCMeta)
class BaseDescriptor:
    """
    Base descriptor as the parent of all following descriptors in this module.

    Descriptors let objects customize attribute lookup, storage, and deletion.
    (See https://docs.python.org/3/howto/descriptor.html#descriptorhowto)

    It provides the following properties:

    * name          - the name of the attribute of a class, which will will be
                      provided by the descriptor.
                      This is a mandatory option for __imit__.
                      Unfortunately I found no way to detect the name of the
                      provided class attribute.
    * _name         - identical with 'name', but with an additional leading underscrore.
                      Will be set automatically wth setting 'name'.
                      This property will be used for the underlaying attribute storing
                      the value.
    * maybe_none    - may the provided attributed be a None value.
    * readonly      - Is the provided property write protected or not.
                      To set the value of the attribute either set a proper
                      default value (if possible), or set the attribute
                      '_name' of the parent object.
    * default_value - The value of the provided attribute, als long as the value
                      of the attribute was not set before.
                      This is a mandatory option for __imit__.

    """

    # -------------------------------------------------------------------------
    def __init__(self, name, default_value, maybe_none=False, readonly=False):
        """Initialize the descriptor."""
        self.public_name = name
        self.private_name = "_" + name

        self.readonly = to_bool(readonly)
        self.maybe_none = to_bool(maybe_none)

        self.default_value = self.check_value(default_value, for_default=True)

    # -------------------------------------------------------------------------
    def __set_name__(self, owner, name):
        """Keep the name of the descriptor."""
        self.public_name = name
        self.private_name = "_" + name

    # -------------------------------------------------------------------------
    @abstractmethod
    def check_value(self, value, for_default=False):
        """
        Check the given value according to the destination of the current descriptor.

        This is an abstract method and hhas to be overridden by all derived classes.
        But it may be called as a super method.
        """
        if value is None and not self.maybe_none:
            if for_default:
                msg = _("The default value of attribute {a!r} must not be None.").format(
                    a=self.public_name
                )
            else:
                msg = _("The attribute {a!r} must not be None.").format(a=self.public_name)
            raise TypeError(msg)

        return value

    # -------------------------------------------------------------------------
    def __get__(self, instance, owner):
        """Get the data from instance object by the private name."""
        return getattr(instance, self.private_name, self.default_value)

    # -------------------------------------------------------------------------
    def __set__(self, instance, value):
        """Set the data in the instance object by the private name as a string value."""
        if self.readonly:
            msg = _("The attribute {!r} is set to readonly.").format(self.public_name)
            raise AttributeError(msg)

        if value is None:
            if self.maybe_none:
                setattr(instance, self.private_name, None)
                return
            msg = _("The attribute {a!r} must not be None.").format(a=self.public_name)
            raise TypeError(msg)

        val = self.check_value(value)
        setattr(instance, self.private_name, val)

    # -------------------------------------------------------------------------
    def __delete__(self, instance):
        """Call to delete the attribute on an instance instance of the owner class."""
        if hasattr(instance, self.private_name):
            delattr(instance, self.private_name)


# =============================================================================
class IntegerDescriptor(BaseDescriptor):
    """Descriptor for an integer attribute."""

    # -------------------------------------------------------------------------
    def __init__(self, default_value=0, lower_limit=None, upper_limit=None, **kwargs):
        """Initialize the IntegerDescriptor descriptor."""
        kwargs["default_value"] = default_value

        self.lower_limit_msg = "Invalid value {v}, must be greater or equal than the lower limit."
        self.upper_limit_msg = "Invalid value {v}, must be less or equal than the upper limit."

        if lower_limit is None:
            self.lower_limit = None
        else:
            self.lower_limit = int(lower_limit)

        if upper_limit is None:
            self.upper_limit = None
        else:
            self.upper_limit = int(upper_limit)

        if (
            self.lower_limit is not None
            and self.upper_limit is not None
            and self.upper_limit < self.lower_limit
        ):
            msg = _(
                "The upper limit of an {} must be greater or equal to its lower_limit."
            ).format(self.__class__.__name__)
            raise ValueError(msg)

        # LOG.debug("kwargs: " + pp(kwargs))
        super(IntegerDescriptor, self).__init__(**kwargs)

        self.lower_limit_msg = _(
            "Invalid value {{v}} of attribute {a}, must be greater or equal to {m}."
        ).format(a=self.public_name, m=self.lower_limit)

        self.upper_limit_msg = _(
            "Invalid value {{v}} of attribute {a}, must be less or equal to {m}."
        ).format(a=self.public_name, m=self.upper_limit)

    # -------------------------------------------------------------------------
    def check_value(self, value, for_default=False):
        """Check the given value."""
        val = super(IntegerDescriptor, self).check_value(value, for_default=for_default)
        if val is None:
            return None

        int_val = int(val)

        if (
            hasattr(self, "lower_limit")
            and self.lower_limit is not None
            and int_val < self.lower_limit
        ):
            msg = self.lower_limit_msg.format(v=int_val)
            raise ValueError(msg)

        if (
            hasattr(self, "upper_limit")
            and self.upper_limit is not None
            and int_val > self.upper_limit
        ):
            msg = self.upper_limit_msg.format(v=int_val)
            raise ValueError(msg)

        return int_val


# =============================================================================
class FloatDescriptor(BaseDescriptor):
    """Descriptor for an float field."""

    # -------------------------------------------------------------------------
    def __init__(
        self,
        default_value=0.0,
        lower_limit=None,
        include_lower_limit=True,
        upper_limit=None,
        include_upper_limit=True,
        **kwargs,
    ):
        """Initialize the FloatDescriptor."""
        kwargs["default_value"] = default_value

        if lower_limit is None:
            self.lower_limit = None
        else:
            self.lower_limit = float(lower_limit)

        self.include_lower_limit = to_bool(include_lower_limit)

        if upper_limit is None:
            self.upper_limit = None
        else:
            self.upper_limit = float(upper_limit)

        self.include_upper_limit = to_bool(include_upper_limit)

        if self.include_lower_limit:
            self.lower_limit_msg = (
                "Invalid value {v}, must be greater or equal than the lower limit."
            )
        else:
            self.lower_limit_msg = "Invalid value {v}, must be greater than the lower limit."

        if self.include_upper_limit:
            self.upper_limit_msg = "Invalid value {v}, must be less or equal than the upper limit."
        else:
            self.upper_limit_msg = "Invalid value {v}, must be less than the upper limit."

        if (
            self.lower_limit is not None
            and self.upper_limit is not None
            and self.upper_limit < self.lower_limit
        ):
            msg = _(
                "The upper limit of an {} must be greater or equal to its lower_limit."
            ).format(self.__class__.__name__)
            raise ValueError(msg)

        # LOG.debug("kwargs: " + pp(kwargs))
        super(FloatDescriptor, self).__init__(**kwargs)

        if self.include_lower_limit:
            self.lower_limit_msg = _(
                "Invalid value {{v}} of attribute {a}, must be greater or equal to {m}."
            )
        else:
            self.lower_limit_msg = _(
                "Invalid value {{v}} of attribute {a}, must be greater to {m}."
            )

        self.lower_limit_msg = self.lower_limit_msg.format(a=self.public_name, m=self.lower_limit)

        if self.include_upper_limit:
            self.upper_limit_msg = _(
                "Invalid value {{v}} of attribute {a}, must be less or equal to {m}."
            )
        else:
            self.upper_limit_msg = _("Invalid value {{v}} of attribute {a}, must be less to {m}.")

        self.upper_limit_msg = self.upper_limit_msg.format(a=self.public_name, m=self.upper_limit)

    # -------------------------------------------------------------------------
    def check_value(self, value, for_default=False):
        """Check the given value."""
        val = super(FloatDescriptor, self).check_value(value, for_default=for_default)
        if val is None:
            return None

        float_val = float(val)

        if hasattr(self, "lower_limit") and self.lower_limit is not None:
            if self.include_lower_limit and float_val < self.lower_limit:
                msg = self.lower_limit_msg.format(v=float_val)
                raise ValueError(msg)
            if not self.include_lower_limit and float_val <= self.lower_limit:
                msg = self.lower_limit_msg.format(v=float_val)
                raise ValueError(msg)

        if hasattr(self, "upper_limit") and self.upper_limit is not None:
            if self.include_upper_limit and float_val > self.upper_limit:
                msg = self.upper_limit_msg.format(v=float_val)
                raise ValueError(msg)
            if not self.include_upper_limit and float_val >= self.upper_limit:
                msg = self.upper_limit_msg.format(v=float_val)
                raise ValueError(msg)

        return float_val


# =============================================================================
class BooleanDescriptor(BaseDescriptor):
    """Descriptor for a boolean attribute."""

    # -------------------------------------------------------------------------
    def __init__(self, default_value=False, **kwargs):
        """Initialize the BooleanDescriptor descriptor."""
        kwargs["default_value"] = default_value
        super(BooleanDescriptor, self).__init__(**kwargs)

    # -------------------------------------------------------------------------
    def check_value(self, value, for_default=False):
        """Check the given value."""
        val = super(BooleanDescriptor, self).check_value(value, for_default=for_default)
        if val is None:
            return None

        return to_bool(val)


# =============================================================================
class PathDescriptor(BaseDescriptor):
    """Descriptor for a field containing a common file path."""

    # -------------------------------------------------------------------------
    def __init__(
        self,
        default_value="",
        must_absolute=False,
        posix=False,
        pure_path=False,
        **kwargs,
    ):
        """Initialize the PathDescriptor descriptor."""
        kwargs["default_value"] = default_value

        self.must_absolute = to_bool(must_absolute)
        self.posix = to_bool(posix)
        self.pure_path = to_bool(pure_path)

        super(PathDescriptor, self).__init__(**kwargs)

    # -------------------------------------------------------------------------
    def check_value(self, value, for_default=False):
        """Check the given value."""
        val = super(PathDescriptor, self).check_value(value, for_default=for_default)
        if val is None:
            return None

        if isinstance(val, PurePath):
            if self.posix and not isinstance(val, PurePosixPath):
                if for_default:
                    msg = _(
                        "The default value of {a!r} {p!r} is a WindowsPath, "
                        "but a PosixPath is required."
                    ).format(a=self.public_name, p=str(val))
                else:
                    msg = _(
                        "The given path of {a!r} {p!r} is a WindowsPath, "
                        "but a PosixPath is required."
                    ).format(a=self.public_name, p=str(val))
                raise ValueError(msg)
            path = value
        else:
            if self.pure_path:
                path = PurePath(value)
            else:
                path = Path(value)

        if self.must_absolute:
            if not path.is_absolute():
                if for_default:
                    msg = _(
                        "The default value of {a!r} must be an absolute path, given {p!r}."
                    ).format(a=self.public_name, p=str(path))
                else:
                    msg = _("The attribute {a!r} must be an absolute path, given {p!r}.").format(
                        a=self.public_name, p=str(path)
                    )
                raise ValueError(msg)

        return path


# =============================================================================
class StringDescriptor(BaseDescriptor):
    """Descriptor for a string field."""

    default_encoding = DEFAULT_ENCODING
    default_coding_error_handler = DEFAULT_CODING_ERROR_HANDLER

    # -------------------------------------------------------------------------
    def __init__(
        self,
        default_value="",
        lowcase=False,
        upcase=False,
        stripped=False,
        not_empty=False,
        raise_on_non_str=False,
        choices=None,
        encoding=None,
        error_handler=None,
        **kwargs,
    ):
        """Initialize the StringDescriptor descriptor."""
        kwargs["default_value"] = default_value

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

        self._check_choices(choices)
        self.choices = choices

        super(StringDescriptor, self).__init__(**kwargs)

        if self.lowcase and self.upcase:
            msg = _(
                "The properties {lc!r} and {uc!r} of attribute {a!r} must not be set to {w} "
                "at the same time."
            ).format(lc="lowcase", uc="upcase", a=self.public_name, w="True")
            raise ValueError(msg)

    # -------------------------------------------------------------------------
    def _check_choices(self, choices):
        """Check the choices attribute for validity."""
        if choices is None:
            return

        if not is_sequence(choices):
            msg = _("Invalid {c} given (not a sequence): {v!r}.").format(c="choices", v=choices)
            raise TypeError(msg)

        if not choices:
            msg = _("Invalid {} given - empty squence.").format("choices")
            raise ValueError(msg)

        for item in choices:
            if not isinstance(item, str):
                msg = _("Invalid {c} given - item {i!r} is not a {o} object.").format(
                    c="choices", i=item, o="str"
                )
                raise TypeError(msg)

        if self.lowcase:
            for item in choices:
                if item != item.lower():
                    msg = _("Invalid {c} given - item {i!r} has non lowcase characters.").format(
                        c="choices", i=item
                    )
                    raise ValueError(msg)
        elif self.upcase:
            for item in choices:
                if item != item.upper():
                    msg = _("Invalid {c} given - item {i!r} has non upcase characters.").format(
                        c="choices", i=item
                    )
                    raise ValueError(msg)

    # -------------------------------------------------------------------------
    def check_value(self, value, for_default=False):
        """Check the given value."""
        val = super(StringDescriptor, self).check_value(value, for_default=for_default)
        if val is None:
            return None

        if isinstance(value, str):
            val = value
        elif isinstance(value, (bytes, bytearray)):
            val = value.decode(encoding=self.encoding, errors=self.error_handler)
        elif self.raise_on_non_str:
            if for_default:
                msg = _(
                    "Invalid type {typ} of {v!r} as default value for attribute {a!r}."
                ).format(typ=value.__class__.__name__, v=value, a=self.public_name)
            else:
                msg = _("Invalid type {typ} of {v!r} given for attribute {a!r}.").format(
                    typ=value.__class__.__name__, v=value, a=self.public_name
                )
            raise TypeError(msg)
        else:
            val = str(value)

        if self.lowcase:
            val = val.lower()
        elif self.upcase:
            val = val.upper()
        if self.stripped:
            val = val.strip()
        if self.not_empty and val == "":
            if for_default:
                msg = _("The default value of ttribute {a!r} must not be empty.").format(
                    a=self.public_name
                )
            else:
                msg = _("The attribute {a!r} must not be empty.").format(a=self.public_name)
            raise ValueError(msg)

        if self.choices and val not in self.choices:
            if for_default:
                msg = _("The default value {!r} must be included in choices.").format(val)
            else:
                msg = _("The given value {!r} must be included in choices.").format(val)
            raise ValueError(msg)

        return val


# =============================================================================
class StringArrayDescriptor:
    """Descriptor for an field of an array of strings."""

    default_encoding = DEFAULT_ENCODING
    default_coding_error_handler = DEFAULT_CODING_ERROR_HANDLER

    # -------------------------------------------------------------------------
    def __init__(
        self,
        name,
        lowcase=False,
        upcase=False,
        stripped=False,
        not_empty=False,
        maybe_none=False,
        raise_on_non_str=False,
        encoding=None,
        error_handler=None,
    ):
        """Initialize the StringDescriptor descriptor."""
        self.public_name = name
        self.private_name = "_" + name

        self.lowcase = to_bool(lowcase)
        self.upcase = to_bool(upcase)
        self.stripped = to_bool(stripped)
        self.not_empty = to_bool(not_empty)
        self.maybe_none = to_bool(maybe_none)
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
                "The properties {lc!r} and {uc!r} of attribute {a!r} must not be set to {w} "
                "at the same time."
            ).format(lc="lowcase", uc="upcase", a=self.public_name, r="True")
            raise ValueError(msg)

    # -------------------------------------------------------------------------
    def __set_name__(self, owner, name):
        """Keep the name of teh descriptor."""
        self.public_name = name
        self.private_name = "_" + name

    # -------------------------------------------------------------------------
    def __get__(self, instance, owner):
        """Get the data from instance object by the private name."""
        return getattr(instance, self.private_name, [])

    # -------------------------------------------------------------------------
    def __set__(self, instance, value):
        """Set the data in the instance object by the private name as an array of strings."""
        if value is None:
            if self.maybe_none:
                setattr(instance, self.private_name, None)
                return
            msg = _("The attribute {a!r} must not be None.").format(a=self.public_name)
            raise TypeError(msg)

        def val2str(v):
            """Convert the value into a str object."""
            if isinstance(v, str):
                return v

            if isinstance(v, (bytes, bytearray)):
                return v.decode(encoding=self.encoding, errors=self.error_handler)

            if self.raise_on_non_str:
                msg = _("Invalid type {typ} of {v!r} given for attribute {a!r}.").format(
                    typ=v.__class__.__name__, v=v, a=self.public_name
                )
                raise TypeError(msg)

            return str(v)

        def check_value(v):
            """Check the given value for validity."""
            if self.lowcase:
                v = v.lower()
            elif self.upcase:
                v = v.upper()

            if self.stripped:
                v = v.strip()

            if self.not_empty and v == "":
                msg = _("The attribute {a!r} must not contain empty strings.").format(
                    a=self.public_name
                )
                raise ValueError(msg)

            return v

        array = []
        if is_sequence(value):
            for val in value:
                item = check_value(val2str(val))
                array.append(item)
        else:
            val = check_value(val2str(value))
            array.append(val)

        setattr(instance, self.private_name, array)


# =============================================================================
class VersionDescriptor:
    """Descriptor for a version field."""

    # -------------------------------------------------------------------------
    def __init__(self, name, maybe_none=False):
        """Initialize the VersionDescriptor: descriptor."""
        self.public_name = name
        self.private_name = "_" + name

        self.maybe_none = to_bool(maybe_none)

    # -------------------------------------------------------------------------
    def __set_name__(self, owner, name):
        """Keep the name of teh descriptor."""
        self.public_name = name
        self.private_name = "_" + name

    # -------------------------------------------------------------------------
    def __get__(self, instance, owner):
        """Get the data from instance object by the private name."""
        return getattr(instance, self.private_name, None)

    # -------------------------------------------------------------------------
    def __set__(self, instance, value):
        """Set the data in the instance object by the private name as an semver.Version object."""
        if value is None:
            if self.maybe_none:
                setattr(instance, self.private_name, None)
                return
            msg = _("The attribute {a!r} must not be None.").format(a=self.public_name)
            raise TypeError(msg)

        version = Version.parse(value)

        setattr(instance, self.private_name, version)


# =============================================================================
if __name__ == "__main__":

    pass

# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 list
