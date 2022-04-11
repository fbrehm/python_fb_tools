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

from .xlate import XLATOR, format_list

__version__ = '0.7.3'
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

    pat_valid_domain = r'@((?:[a-z0-9](?:[a-z0-9\-]*[a-z0-9])?\.)+[a-z][a-z]+)'

    pat_valid_user = r'([a-z0-9][a-z0-9_\-\.\+]*[a-z0-9]'
    pat_valid_user += r'(?:\+[a-z0-9][a-z0-9_\-\.]*[a-z0-9])*)'

    pat_valid_address = pat_valid_user + pat_valid_domain

    re_valid_user = re.compile(r'^' + pat_valid_user + r'$', re.IGNORECASE)
    re_valid_domain = re.compile(r'^' + pat_valid_domain + r'$', re.IGNORECASE)
    re_valid_address = re.compile(r'^' + pat_valid_address + r'$', re.IGNORECASE)

    # -------------------------------------------------------------------------
    @classmethod
    def valid_address(cls, address, raise_on_failure=False, verbose=0):

        if not address:
            e = InvalidMailAddressError(address, _("Empty address."))
            if raise_on_failure:
                raise e
            if verbose > 2:
                LOG.debug(str(e))
            return False

        addr = to_str(address)
        if not isinstance(addr, str):
            e = InvalidMailAddressError(address, _("Wrong type."))
            if raise_on_failure:
                raise e
            if verbose > 2:
                LOG.debug(str(e))
            return False

        if cls.re_valid_address.search(addr):
            return True

        e = InvalidMailAddressError(address, _("Invalid address."))
        if raise_on_failure:
            raise e
        if verbose > 2:
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

        if self.verbose > 3:
            msg = _("Given user: {u!r}, given domain: {d!r}.")
            LOG.debug(msg.format(u=user, d=domain))

        if user:
            if not isinstance(user, six.string_types):
                msg = _("Invalid mail address.")
                raise InvalidMailAddressError(user, msg)
            user = to_str(user)

        if not domain:
            if user:
                addr = convert_attr(user)
                if self.valid_address(addr, verbose=self.verbose):
                    match = self.re_valid_address.search(addr)
                    self._user = match.group(1)
                    self._domain = match.group(2)
                    return
                match = self.re_valid_domain.search(addr)
                if match:
                    self._domain = match.group(1)
                    return
                if not self.re_valid_user.search(user):
                    msg = _("Invalid user/mailbox name.")
                    raise InvalidMailAddressError(user, msg)
                self._user = addr
                return

            e = EmptyMailAddressError()
            if self.empty_ok:
                if self.verbose > 2:
                    LOG.debug(str(e))
                return
            raise e

        if user:
            c_user = convert_attr(user)
            if not self.re_valid_user.search(c_user):
                msg = _("Invalid user/mailbox name.")
                raise InvalidMailAddressError(user, msg)
        else:
            c_user = None

        c_domain = convert_attr(domain)
        if not self.re_valid_domain.search('@' + c_domain):
            msg = _("Invalid domain.")
            raise InvalidMailAddressError(domain, msg)

        self._user = c_user
        self._domain = c_domain

    # -------------------------------------------------------------------------
    def _short_init(self, user, domain, verbose=0, empty_ok=False):

        self._user = ''
        self._domain = ''
        self._verbose = 0
        self.verbose = verbose
        self._empty_ok = False
        self.empty_ok = empty_ok

        if self.verbose > 3:
            msg = _("Given user: {u!r}, given domain: {d!r}.")
            LOG.debug(msg.format(u=user, d=domain))

        if user:
            self._user = str(user).lower().strip()

        if domain:
            self._domain = str(domain).lower().strip()

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
            msg = _("Wrong verbose level {!r}, must be >= 0").format(value)
            raise ValueError(msg)

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
    def as_tuple(self):
        """
        Transforms the elements of the object into a tuple

        @return: structure as tuple
        @rtype:  tuple
        """

        return (self.user, self.domain, self.verbose, self.empty_ok)

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
            return ''

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
            msg = _("Object {o!r} for comparing is not a {c}.").format(
                o=other, c='MailAddress')
            raise TypeError(msg)

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
            msg = _("Object {o!r} for comparing is not a {c}.").format(
                o=other, c='MailAddress')
            raise TypeError(msg)

        if self.verbose > 5:
            msg = _("Comparing {self!r} with {other!r} ...")
            LOG.debug(msg.format(self=self, other=other))

        if not self.domain:
            if other.domain:
                return True
            if not other.user:
                return False
            if self.user.lower() != other.user.lower():
                return self.user.lower() < other.user.lower()
            return False

        if not self.user:
            if not self.domain:
                if other.domain:
                    return False
                return True
            if not other.domain:
                return False
            if self.domain.lower() != other.domain.lower():
                return self.domain.lower() < other.domain.lower()
            return True

        # From here on there are existing both user and domain
        if not other.domain:
            return False
        if self.domain.lower() != other.domain.lower():
            return self.domain.lower() < other.domain.lower()

        # Both domains are equal now
        if not other.user:
            return False

        if self.user.lower() != other.user.lower():
            return self.user.lower() < other.user.lower()

        return False

    # -------------------------------------------------------------------------
    def __gt__(self, other):

        if self == other:
            return False
        if self < other:
            return False
        return True

    # -------------------------------------------------------------------------
    def __copy__(self):
        "Implementing a wrapper for copy.copy()."

        addr = MailAddress(empty_ok=True)

        addr._user = self.user
        addr._domain = self.domain
        addr.verbose = self.verbose
        addr.empty_ok = self.empty_ok

        return addr


# =============================================================================
class QualifiedMailAddress(MailAddress):
    """
    Class for encapsulating a mail address with an optional Name.
    """

    pat_valid_name = r'("[^"]*"|[^",;<>@|]*)'
    pat_valid_full_address = r'^\s*' + pat_valid_name + r'\s*<'
    pat_valid_full_address += MailAddress.pat_valid_address + r'>\s*$'

    re_valid_full_address = re.compile(pat_valid_full_address, re.IGNORECASE)
    re_qouting = re.compile(r'^\s*"([^"]*)"\s*$')
    re_invalid_name_chars = re.compile(r'[,;<>@|]')
    re_only_whitespace = re.compile(r'^\s+$')

    # -------------------------------------------------------------------------
    @classmethod
    def valid_full_address(cls, address, raise_on_failure=False, verbose=0):

        if not address:
            e = InvalidMailAddressError(address, _("Empty address."))
            if raise_on_failure:
                raise e
            if verbose > 2:
                LOG.debug(str(e))
            return False

        addr = to_str(address)
        if not isinstance(addr, str):
            e = InvalidMailAddressError(address, _("Wrong type."))
            if raise_on_failure:
                raise e
            if verbose > 2:
                LOG.debug(str(e))
            return False

        if verbose > 4:
            LOG.debug(_("Evaluating address {!r} ...").format(addr))
            LOG.debug(_("Search pattern simple: {}").format(cls.re_valid_address))
        if cls.re_valid_address.search(addr):
            return True

        if verbose > 4:
            LOG.debug(_("Search pattern full: {}").format(cls.re_valid_full_address))
        if cls.re_valid_full_address.match(addr):
            return True

        e = InvalidMailAddressError(address, _("Invalid address."))
        if raise_on_failure:
            raise e
        if verbose > 2:
            LOG.debug(str(e))
        return False

    # -------------------------------------------------------------------------
    def __init__(
            self, address=None, *, user=None, domain=None, name=None, verbose=0, empty_ok=False):

        self._name = None

        if verbose > 1:
            msg = "Given - address: {a!r}, user: {u!r}, domain: {d!r}, full name: {n!r}."
            LOG.debug(msg.format(a=address, u=user, d=domain, n=name))

        if address:
            if user or domain or name:
                param_list = ('user', 'domain', 'name')
                msg = _("Parameters {lst} may not be given, if parameter {a!r} was given.")
                msg = msg.format(lst=format_list(param_list, do_repr=True), a='address')
                raise RuntimeError(msg)
            return self._init_from_address(address, verbose=verbose, empty_ok=empty_ok)

        super(QualifiedMailAddress, self).__init__(
            user=user, domain=domain, verbose=verbose, empty_ok=empty_ok)

        if name:
            _name = to_str(name).strip()
            if not isinstance(_name, six.string_types):
                msg = _("Invalid full user name.")
                raise InvalidMailAddressError(name, msg)
            if _name:
                self._name = _name

    # -------------------------------------------------------------------------
    def _init_from_address(self, address, verbose=0, empty_ok=False):

        if not self.valid_full_address(address, raise_on_failure=True, verbose=verbose):
            raise InvalidMailAddressError(address, _("Invalid address."))

        user = None
        domain = None
        name = None

        match = self.re_valid_full_address.search(address)
        if match:
            name = match.group(1).strip()
            user = match.group(2).strip().lower()
            domain = match.group(3).strip().lower()
            super(QualifiedMailAddress, self)._short_init(
                user=user, domain=domain, verbose=verbose, empty_ok=empty_ok)
            if name:
                match_quoting = self.re_qouting.match(name)
                if match_quoting:
                    self._name = match_quoting.group(1)
                else:
                    self._name = name
            return

        match = self.re_valid_address.search(address)
        if not match:
            raise InvalidMailAddressError(address, _("Invalid address."))

        user = match.group(1).strip().lower()
        domain = match.group(2).strip().lower()
        super(QualifiedMailAddress, self)._short_init(
            user=user, domain=domain, verbose=verbose, empty_ok=empty_ok)

    # -----------------------------------------------------------
    @property
    def name(self):
        """The full and elaborate name of the owner of the mail address."""
        return self._name

    # -------------------------------------------------------------------------
    def as_dict(self, short=True):
        """
        Transforms the elements of the object into a dict

        @param short: don't include local properties in resulting dict.
        @type short: bool

        @return: structure as dict
        @rtype:  dict
        """

        res = super(QualifiedMailAddress, self).as_dict(short=short)

        res['name'] = self.name

        return res

    # -------------------------------------------------------------------------
    def as_tuple(self):
        """
        Transforms the elements of the object into a tuple

        @return: structure as tuple
        @rtype:  tuple
        """

        return (self.user, self.domain, self.name, self.verbose, self.empty_ok)

    # -------------------------------------------------------------------------
    def simple(self):

        return super(QualifiedMailAddress, self).__copy__()

    # -------------------------------------------------------------------------
    def __copy__(self):
        "Implementing a wrapper for copy.copy()."

        addr = self.__class__(empty_ok=True)

        addr._user = self.user
        addr._domain = self.domain
        addr._name = self.name
        addr.verbose = self.verbose
        addr.empty_ok = self.empty_ok

        return addr

    # -------------------------------------------------------------------------
    def __str__(self):

        no_addr = 'undisclosed recipient'

        address = super(QualifiedMailAddress, self).__str__()
        show_addr = address
        if address:
            if self.name:
                show_addr = '<{a}>'.format(a=address)
        else:
            show_addr = '<{a}>'.format(a=no_addr)

        if not self.name:
            return show_addr

        show_name = self.name
        if self.re_invalid_name_chars.search(show_name) \
                or self.re_only_whitespace.search(show_name):
            show_name = '"' + show_name + '"'

        return show_name + ' {a}'.format(a=show_addr)

    # -------------------------------------------------------------------------
    def __repr__(self):
        """Typecasting into a string for reproduction."""

        out = "<%s(" % (self.__class__.__name__)

        fields = []
        fields.append("user={!r}".format(self.user))
        fields.append("domain={!r}".format(self.domain))
        fields.append("name={!r}".format(self.name))

        out += ", ".join(fields) + ")>"
        return out

    # -------------------------------------------------------------------------
    def __eq__(self, other):

        if not isinstance(other, QualifiedMailAddress):
            if other is None:
                return False
            return str(self) == str(other)

        if not super(QualifiedMailAddress, self).__eq__(other):
            return False

        return self.name == other.name

    # -------------------------------------------------------------------------
    def __lt__(self, other):

        if not isinstance(other, MailAddress):
            msg = _("Object {o!r} for comparing is not a {c}.").format(
                o=other, c='MailAddress')
            raise TypeError(msg)

        if self.verbose > 4:
            msg = _("Comparing {self!r} with {other!r} ...")
            LOG.debug(msg.format(self=self, other=other))

        if not isinstance(other, QualifiedMailAddress):
            return super(QualifiedMailAddress, self).__lt__(other)

        if super(QualifiedMailAddress, self).__eq__(other):
            if self.name.lower() == other.name.lower():
                return self.name < other.name
            else:
                return self.name.lower() < other.name.lower()

        return super(QualifiedMailAddress, self).__lt__(other)


# =============================================================================

if __name__ == "__main__":

    pass

# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 list
