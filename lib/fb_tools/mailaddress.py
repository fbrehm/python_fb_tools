#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: Frank Brehm
@contact: frank@brehm-online.com
@copyright: © 2022 by Frank Brehm, Berlin
@summary: The module for the MailAddress object.
"""
from __future__ import absolute_import

# Standard modules
import logging
import re

# Third party modules
import six

# Own modules
from .errors import InvalidMailAddressError
# from .errors import GeneralMailAddressError, EmptyMailAddressError
from .errors import EmptyMailAddressError

from .common import to_str, to_bool

from .obj import FbGenericBaseObject

from .xlate import XLATOR

__version__ = '0.6.1'
LOG = logging.getLogger(__name__)

_ = XLATOR.gettext


# =============================================================================
def convert_attr(value):
    if isinstance(value, six.string_types):
        return to_str(value).lower().strip()
    return value


# =============================================================================
class MailAddress(FbGenericBaseObject):
    """
    Class for encapsulating a mail simple address.
    """

    pattern_valid_domain = r'@((?:[a-z0-9](?:[a-z0-9\-]*[a-z0-9])?\.)+[a-z][a-z]+)$'

    pattern_valid_user = r'^([a-z0-9][a-z0-9_\-\.\+\&@]*[a-z0-9]'
    pattern_valid_user += r'(?:\+[a-z0-9][a-z0-9_\-\.]*[a-z0-9])*)'

    pattern_valid_address = pattern_valid_user + pattern_valid_domain

    re_valid_user = re.compile(pattern_valid_user + r'$', re.IGNORECASE)
    re_valid_domain = re.compile(r'^' + pattern_valid_domain, re.IGNORECASE)
    re_valid_address = re.compile(pattern_valid_address, re.IGNORECASE)

    verbose = 0

    # -------------------------------------------------------------------------
    @classmethod
    def valid_address(cls, address, raise_on_failure=False):

        if not address:
            e = InvalidMailAddressError(address, _("Empty address."))
            if raise_on_failure:
                raise e
            elif cls.verbose > 2:
                LOG.debug(str(e))
            return False

        addr = to_str(address)
        if not isinstance(addr, str):
            e = InvalidMailAddressError(address, _("Wrong type."))
            if raise_on_failure:
                raise e
            elif cls.verbose > 2:
                LOG.debug(str(e))
            return False

        if cls.re_valid_address.search(addr):
            return True

        e = InvalidMailAddressError(address, _("Invalid address."))
        if raise_on_failure:
            raise e
        elif cls.verbose > 2:
            LOG.debug(str(e))
        return False

    # -------------------------------------------------------------------------
    def __init__(self, user=None, domain=None, verbose=0, empty_ok=False):

        self._user = ''
        self._domain = ''
        self._verbose = 0
        self.verbose = verbose
        self._empty_ok = False
        self.empty_ok = empty_ok

        if not domain:
            if user:
                addr = convert_attr(user)
                if self.valid_address(addr):
                    match = self.re_valid_address.search(addr)
                    self._user = match.group(1)
                    self._domain = match.group(2)
                    return
                match = self.re_valid_domain.search(addr)
                if match:
                    self._domain = match.group(1)
                    return
                self._user = addr
                return

            e = EmptyMailAddressError()
            if self.empty_ok:
                if self.verbose > 2:
                    LOG.debug(str(e))
                return
            raise e

        self._user = convert_attr(user)
        self._domain = convert_attr(domain)

    # -----------------------------------------------------------
    @property
    def user(self):
        """The user part of the address."""
        if self._user is None:
            return ''
        return self._user

    # -----------------------------------------------------------
    @property
    def domain(self):
        """The domain part of the address."""
        if self._domain is None:
            return ''
        return self._domain

    # -----------------------------------------------------------
    @property
    def verbose(self):
        """The verbosity level."""
        return getattr(self, '_verbose', 0)

    @verbose.setter
    def verbose(self, value):
        v = int(value)
        if v >= 0:
            self._verbose = v
        else:
            LOG.warning(_("Wrong verbose level {!r}, must be >= 0").format(value))

    # -----------------------------------------------------------
    @property
    def empty_ok(self):
        """Is an empty mail address valid or should there be raised an exceptiom."""
        return self._empty_ok

    @empty_ok.setter
    def empty_ok(self, value):
        self._empty_ok = to_bool(value)

    # -------------------------------------------------------------------------
    def as_dict(self, short=True):
        """
        Transforms the elements of the object into a dict

        @param short: don't include local properties in resulting dict.
        @type short: bool

        @return: structure as dict
        @rtype:  dict
        """

        res = super(MailAddress, self).as_dict(short=short)

        res['user'] = self.user
        res['domain'] = self.domain
        res['verbose'] = self.verbose
        res['empty_ok'] = self.empty_ok

        return res

    # -------------------------------------------------------------------------
    def __str__(self):

        if not self.user and not self.domain:
            return ''

        if not self.domain:
            return self.user

        if not self.user:
            return '@' + self.domain

        return self.user + '@' + self.domain

    # -------------------------------------------------------------------------
    def str_for_access(self):

        if not self.user and not self.domain:
            return None

        if not self.domain:
            return self.user + '@'

        if not self.user:
            return self.domain

        return self.user + '@' + self.domain

    # -------------------------------------------------------------------------
    def __repr__(self):
        """Typecasting into a string for reproduction."""

        out = "<%s(" % (self.__class__.__name__)

        fields = []
        fields.append("user={!r}".format(self.user))
        fields.append("domain={!r}".format(self.domain))

        out += ", ".join(fields) + ")>"
        return out

    # -------------------------------------------------------------------------
    def __hash__(self):
        return hash(str(self).lower())

    # -------------------------------------------------------------------------
    def __eq__(self, other):

        if not isinstance(other, MailAddress):
            if other is None:
                return False
            return str(self).lower() == str(other).lower()

        if not self.user:
            if other.user:
                return False
            if not self.domain:
                if other.domain:
                    return False
                return True
            if not other.domain:
                return False
            if self.domain.lower() == other.domain.lower():
                return True
            return False

        if not self.domain:
            if other.domain:
                return False
            if not other.user:
                return False
            if self.user.lower() == other.user.lower():
                return True
            return False

        if not other.user:
            return False
        if not other.domain:
            return False
        if self.domain.lower() != other.domain.lower():
            return False
        if self.user.lower() != other.user.lower():
            return False

        return True

    # -------------------------------------------------------------------------
    def __ne__(self, other):

        if self == other:
            return False
        return True

    # -------------------------------------------------------------------------
    def __lt__(self, other):

        if not isinstance(other, MailAddress):
            if other is None:
                return False
            return str(self).lower() < str(other).lower()

        if not self.user:
            if not self.domain:
                if other.domain:
                    return False
                return True
            if not other.domain:
                return False
            if self.domain.lower() != other.domain.lower():
                return self.domain.lower() < other.domain.lower()
            if other.user:
                return False
            return True

        if not self.domain:
            if other.domain:
                return True
            if not other.user:
                return False
            if self.user.lower() != other.user.lower():
                return self.user.lower() < other.user.lower()
            return False

        if not other.domain:
            return False
        if not other.user:
            return False

        if self.domain.lower() != other.domain.lower():
            return self.domain.lower() < other.domain.lower()
        if self.user.lower() != other.user.lower():
            return self.user.lower() < other.user.lower()

        return False

    # -------------------------------------------------------------------------
    def __gt__(self, other):

        if self < other:
            return False
        return True

    # -------------------------------------------------------------------------
    def __copy__(self):
        "Implementing a wrapper for copy.copy()."

        addr = MailAddress()

        addr._user = self.user
        addr._domain = self.domain
        addr.verbose = self.verbose
        addr.empty_ok = self.empty_ok

        return addr


# =============================================================================

if __name__ == "__main__":

    pass

# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 list
