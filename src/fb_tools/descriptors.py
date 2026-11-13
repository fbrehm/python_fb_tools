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
from pathlib import Path
from pathlib import PurePath
from pathlib import PurePosixPath

# Third party modules

try:
    from semver import Version
except ImportError:
    from semver import VersionInfo as Version


# Own modules
from . import DEFAULT_CODING_ERROR_HANDLER
from . import DEFAULT_ENCODING
from . import VALID_DECODE_ERROR_HANDLERS
# from . import VALID_ENCODE_ERROR_HANDLERS
from .common import is_sequence
from .common import to_bool
from .xlate import XLATOR

__version__ = "0.9.1"
LOG = logging.getLogger(__name__)

_ = XLATOR.gettext


# =============================================================================
class IntegerDescriptor:
    """Descriptor for an integer field."""

    # -------------------------------------------------------------------------
    def __init__(self, name, lower_limit=None, upper_limit=None, maybe_none=False):
        """Initialize the IntegerDescriptor descriptor."""
        self.public_name = name
        self.private_name = "_" + name

        self.maybe_none = to_bool(maybe_none)

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

        self.lower_limit_msg = _(
            "Invalid value {{v}} of attribute {a}, must be greater or equal to {m}."
        ).format(a=self.public_name, m=self.lower_limit)
        self.upper_limit_msg = _(
            "Invalid value {{v}} of attribute {a}, must be less or equal to {m}."
        ).format(a=self.public_name, m=self.upper_limit)

    # -------------------------------------------------------------------------
    def __set_name__(self, owner, name):
        """Keep the name of the descriptor."""
        self.public_name = name
        self.private_name = "_" + name

    # -------------------------------------------------------------------------
    def __get__(self, instance, owner):
        """Get the data from instance object by the private name."""
        return getattr(instance, self.private_name, 0)

    # -------------------------------------------------------------------------
    def __set__(self, instance, value):
        """Set the data in the instance object by the private name as an integer value."""
        if value is None:
            if self.maybe_none:
                setattr(instance, self.private_name, None)
                return
            msg = _("The attribute {a!r} must not be None.").format(a=self.public_name)
            raise TypeError(msg)

        val = int(value)

        if self.lower_limit is not None and val < self.lower_limit:
            msg = self.lower_limit_msg.format(v=val)
            raise ValueError(msg)

        if self.upper_limit is not None and val > self.upper_limit:
            msg = self.upper_limit_msg.format(v=value)
            raise ValueError(msg)

        setattr(instance, self.private_name, val)


# =============================================================================
class FloatDescriptor:
    """Descriptor for an float field."""

    # -------------------------------------------------------------------------
    def __init__(
        self,
        name,
        lower_limit=None,
        include_lower_limit=True,
        upper_limit=None,
        include_upper_limit=True,
        maybe_none=False,
    ):
        """Initialize the FloatDescriptor."""
        self.public_name = name
        self.private_name = "_" + name

        self.maybe_none = to_bool(maybe_none)

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

        if (
            self.lower_limit is not None
            and self.upper_limit is not None
            and self.upper_limit < self.lower_limit
        ):
            msg = _(
                "The upper limit of an {} must be greater or equal to its lower_limit."
            ).format(self.__class__.__name__)
            raise ValueError(msg)

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
    def __set_name__(self, owner, name):
        """Keep the name of the descriptor."""
        self.public_name = name
        self.private_name = "_" + name

    # -------------------------------------------------------------------------
    def __get__(self, instance, owner):
        """Get the data from instance object by the private name."""
        return getattr(instance, self.private_name, 0)

    # -------------------------------------------------------------------------
    def __set__(self, instance, value):
        """Set the data in the instance object by the private name as an float value."""
        if value is None:
            if self.maybe_none:
                setattr(instance, self.private_name, None)
                return
            msg = _("The attribute {a!r} must not be None.").format(a=self.public_name)
            raise TypeError(msg)

        val = float(value)

        if self.lower_limit is not None:
            if self.include_lower_limit and val < self.lower_limit:
                msg = self.lower_limit_msg.format(v=val)
                raise ValueError(msg)
            if not self.include_lower_limit and val <= self.lower_limit:
                msg = self.lower_limit_msg.format(v=val)
                raise ValueError(msg)

        if self.upper_limit is not None:
            if self.include_upper_limit and val > self.upper_limit:
                msg = self.upper_limit_msg.format(v=value)
                raise ValueError(msg)
            if not self.include_upper_limit and val >= self.upper_limit:
                msg = self.upper_limit_msg.format(v=value)
                raise ValueError(msg)

        setattr(instance, self.private_name, val)


# =============================================================================
class BooleanDescriptor:
    """Descriptor for a boolean field."""

    # -------------------------------------------------------------------------
    def __init__(self, name, maybe_none=False):
        """Initialize the BooleanDescriptor descriptor."""
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
        return getattr(instance, self.private_name, "")

    # -------------------------------------------------------------------------
    def __set__(self, instance, value):
        """Set the data in the instance object by the private name as a string value."""
        if value is None:
            if self.maybe_none:
                setattr(instance, self.private_name, None)
                return
            msg = _("The attribute {a!r} must not be None.").format(a=self.public_name)
            raise TypeError(msg)

        setattr(instance, self.private_name, to_bool(value))


# =============================================================================
class PathDescriptor:
    """Descriptor for a field containing a common file path."""

    # -------------------------------------------------------------------------
    def __init__(self, name, must_absolute=False, maybe_none=False, posix=False, pure_path=False):
        """Initialize the PathDescriptor descriptor."""
        self.public_name = name
        self.private_name = "_" + name

        self.must_absolute = to_bool(must_absolute)
        self.maybe_none = to_bool(maybe_none)
        self.posix = to_bool(posix)
        self.pure_path = to_bool(pure_path)

    # -------------------------------------------------------------------------
    def __set_name__(self, owner, name):
        """Keep the name of teh descriptor."""
        self.public_name = name
        self.private_name = "_" + name

    # -------------------------------------------------------------------------
    def __get__(self, instance, owner):
        """Get the data from instance object by the private name."""
        return getattr(instance, self.private_name, "")

    # -------------------------------------------------------------------------
    def __set__(self, instance, value):
        """Set the data in the instance object by the private name as a string value."""
        if value is None:
            if self.maybe_none:
                setattr(instance, self.private_name, None)
                return
            msg = _("The attribute {a!r} must not be None.").format(a=self.public_name)
            raise TypeError(msg)

        if isinstance(value, PurePath):
            if self.posix and not isinstance(value, PurePosixPath):
                msg = _(
                    "The given path {!r} is a WindowsPath, but a PosixPath is required."
                ).format(str(value))
                raise ValueError(msg)
            path = value
        else:
            if self.pure_path:
                path = PurePath(value)
            else:
                path = Path(value)

        if self.must_absolute:
            if not path.is_absolute():
                mdg = _("The attribute {a!r} must be an absolute path, given {p!r}.").format(
                    a=self.public_name, p=str(path)
                )
                raise ValueError(mdg)

        setattr(instance, self.private_name, path)


# =============================================================================
class StringDescriptor:
    """Descriptor for a string field."""

    default_encoding = DEFAULT_ENCODING
    default_coding_error_handler = DEFAULT_CODING_ERROR_HANDLER

    # -------------------------------------------------------------------------
    def __init__(
        self,
        name,
        lowcase=False,
        upcase=False,
        stripped=False,
        maybe_none=False,
        not_empty=False,
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
        self.maybe_none = to_bool(maybe_none)
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
                "The properties {lc!r} and {uc!r} of attribute {a!r} must not be set to {w} "
                "at the same time."
            ).format(lc="lowcase", uc="upcase", a=self.public_name, w="True")
            raise ValueError(msg)

    # -------------------------------------------------------------------------
    def __set_name__(self, owner, name):
        """Keep the name of teh descriptor."""
        self.public_name = name
        self.private_name = "_" + name

    # -------------------------------------------------------------------------
    def __get__(self, instance, owner):
        """Get the data from instance object by the private name."""
        return getattr(instance, self.private_name, "")

    # -------------------------------------------------------------------------
    def __set__(self, instance, value):
        """Set the data in the instance object by the private name as a string value."""
        if value is None:
            if self.maybe_none:
                setattr(instance, self.private_name, None)
                return
            msg = _("The attribute {a!r} must not be None.").format(a=self.public_name)
            raise TypeError(msg)

        if isinstance(value, str):
            val = value
        elif isinstance(value, (bytes, bytearray)):
            val = value.decode(encoding=self.encoding, errors=self.error_handler)
        elif self.raise_on_non_str:
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
            msg = _("The attribute {a!r} must not be empty.").format(a=self.public_name)
            raise ValueError(msg)
        setattr(instance, self.private_name, val)


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
