#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@summary: The module for the MailAddress object.

@author: Frank Brehm
@contact: frank@brehm-online.com
@copyright: © 2024 by Frank Brehm, Berlin
"""
from __future__ import absolute_import

# Standard modules
import copy
import logging
import re
try:
    from collections.abc import MutableSequence
except ImportError:
    from collections import MutableSequence

# Third party modules
import six

# Own modules
from .common import is_sequence, pp, to_bool, to_str
from .errors import EmptyMailAddressError
from .errors import InvalidMailAddressError
from .obj import FbBaseObject, FbGenericBaseObject
from .xlate import XLATOR, format_list

__version__ = '2.1.0'
LOG = logging.getLogger(__name__)

_ = XLATOR.gettext


# =============================================================================
def convert_attr(value):
    """Convert a value into a string."""
    if isinstance(value, six.string_types):
        return to_str(value).lower().strip()
    return value


# =============================================================================
class MailAddress(FbGenericBaseObject):
    """Class for encapsulating a mail simple address."""

    pat_tld = r'(?:(?:[a-z][a-z]+)|(?:xn--[a-z0-9]+))'
    pat_valid_domain = r'@((?:[a-z0-9](?:[a-z0-9\-]*[a-z0-9])?\.)*' + pat_tld + ')'

    pat_valid_user = r'([a-z0-9](?:[a-z0-9_\-\.\+=/]*[a-z0-9=\-_])?'
    pat_valid_user += r'(?:\+[a-z0-9][a-z0-9_\-\.=/]*[a-z0-9=\-_])*)'

    pat_valid_address = pat_valid_user + pat_valid_domain

    re_valid_user = re.compile(r'^' + pat_valid_user + r'$', re.IGNORECASE)
    re_valid_domain = re.compile(r'^' + pat_valid_domain + r'$', re.IGNORECASE)
    re_valid_address = re.compile(r'^' + pat_valid_address + r'$', re.IGNORECASE)

    # -------------------------------------------------------------------------
    @classmethod
    def valid_address(cls, address, raise_on_failure=False, verbose=0):
        """Check the validity of a mail address."""
        if not address:
            e = InvalidMailAddressError(address, _('Empty address.'))
            if raise_on_failure:
                raise e
            if verbose > 2:
                LOG.debug(str(e))
            return False

        addr = to_str(address)
        if not isinstance(addr, str):
            e = InvalidMailAddressError(address, _('Wrong type.'))
            if raise_on_failure:
                raise e
            if verbose > 2:
                LOG.debug(str(e))
            return False

        if cls.re_valid_address.search(addr):
            return True

        e = InvalidMailAddressError(address, _('Invalid address.'))
        if raise_on_failure:
            raise e
        if verbose > 2:
            LOG.debug(str(e))
        return False

    # -------------------------------------------------------------------------
    def __init__(self, user=None, domain=None, verbose=0, empty_ok=False):
        """Initialise a MailAddress object."""
        self._user = ''
        self._domain = ''
        self._verbose = 0
        self.verbose = verbose
        self._empty_ok = False
        self.empty_ok = empty_ok

        if self.verbose > 3:
            msg = _('Given user: {u!r}, given domain: {d!r}.')
            LOG.debug(msg.format(u=user, d=domain))

        if user:
            if not isinstance(user, six.string_types):
                msg = _('Invalid mail address.')
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
                    msg = _('Invalid user/mailbox name.')
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
                msg = _('Invalid user/mailbox name.')
                raise InvalidMailAddressError(user, msg)
        else:
            c_user = None

        c_domain = convert_attr(domain)
        if not self.re_valid_domain.search('@' + c_domain):
            msg = _('Invalid domain.')
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
            msg = _('Given user: {u!r}, given domain: {d!r}.')
            LOG.debug(msg.format(u=user, d=domain))

        if user:
            self._user = str(user).lower().strip()

        if domain:
            self._domain = str(domain).lower().strip()

    # -----------------------------------------------------------
    @property
    def user(self):
        """Return the user part of the address."""
        if self._user is None:
            return ''
        return self._user

    # -----------------------------------------------------------
    @property
    def domain(self):
        """Return the domain part of the address."""
        if self._domain is None:
            return ''
        return self._domain

    # -----------------------------------------------------------
    @property
    def verbose(self):
        """Return the verbosity level."""
        return getattr(self, '_verbose', 0)

    @verbose.setter
    def verbose(self, value):
        v = int(value)
        if v >= 0:
            self._verbose = v
        else:
            msg = _('Wrong verbose level {!r}, must be >= 0').format(value)
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
        Transform the elements of the object into a dict.

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
        Transform the elements of the object into a tuple.

        @return: structure as tuple
        @rtype:  tuple
        """
        return (self.user, self.domain, self.verbose, self.empty_ok)

    # -------------------------------------------------------------------------
    def __str__(self):
        """Typecast into a string."""
        if not self.user and not self.domain:
            return ''

        if not self.domain:
            return self.user

        if not self.user:
            return '@' + self.domain

        return self.user + '@' + self.domain

    # -------------------------------------------------------------------------
    def str_for_access(self):
        """Typecast into a string for access mappings."""
        if not self.user and not self.domain:
            return ''

        if not self.domain:
            return self.user + '@'

        if not self.user:
            return self.domain

        return self.user + '@' + self.domain

    # -------------------------------------------------------------------------
    def __repr__(self):
        """Typecast into a string for reproduction."""
        out = '<%s(' % (self.__class__.__name__)

        fields = []
        fields.append('user={!r}'.format(self.user))
        fields.append('domain={!r}'.format(self.domain))

        out += ', '.join(fields) + ')>'
        return out

    # -------------------------------------------------------------------------
    def __hash__(self):
        """Return e hash value of the current object."""
        return hash(str(self).lower())

    # -------------------------------------------------------------------------
    def __eq__(self, other):
        """Compare for equality."""
        if self.verbose > 5:
            msg = _('Checking equality {self!r} with {other!r} ...')
            LOG.debug(msg.format(self=self, other=other))

        if not isinstance(other, MailAddress):
            return False

        if MailAddress is not other.__class__.__mro__[0]:
            if isinstance(other, QualifiedMailAddress):
                if other.name is None and self == other.simple():
                    return True
            return False

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
        """Compare for non-equality."""
        if self == other:
            return False
        return True

    # -------------------------------------------------------------------------
    def __lt__(self, other):
        """Compare, whether the current address is less than another."""
        if not isinstance(other, MailAddress):
            msg = _('Object {o!r} for comparing is not a {c} object.').format(
                o=other, c='MailAddress')
            raise TypeError(msg)

        if self.verbose > 5:
            msg = _('Comparing {self!r} with {other!r} ...')
            LOG.debug(msg.format(self=self, other=other))

        if MailAddress is not other.__class__.__mro__[0]:
            if isinstance(other, QualifiedMailAddress):
                other_simple = other.simple()
                if self == other_simple:
                    if other.name is None:
                        return False
                    else:
                        return True
                else:
                    return self < other_simple
            else:
                return True

        # At this point both self and other are pure MailAddress objects

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
        """Compare, whether the current address is greater than another."""
        if self == other:
            return False
        if self < other:
            return False
        return True

    # -------------------------------------------------------------------------
    def __le__(self, other):
        """Compare, whether the current address is less or equal than another."""
        if self == other:
            return True
        if self < other:
            return True
        return False

    # -------------------------------------------------------------------------
    def __ge__(self, other):
        """Compare, whether the current address is greater or equal than another."""
        if self == other:
            return True
        if self < other:
            return False
        return True

    # -------------------------------------------------------------------------
    def __copy__(self):
        """Return a copy of the current address."""
        addr = MailAddress(empty_ok=True)

        addr._user = self.user
        addr._domain = self.domain
        addr.verbose = self.verbose
        addr.empty_ok = self.empty_ok

        return addr


# =============================================================================
class QualifiedMailAddress(MailAddress):
    """Class for encapsulating a mail address with an optional Name."""

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
        """Check the validity of a full qualified mail address."""
        if not address:
            e = InvalidMailAddressError(address, _('Empty address.'))
            if raise_on_failure:
                raise e
            if verbose > 2:
                LOG.debug(str(e))
            return False

        addr = to_str(address)
        if not isinstance(addr, str):
            e = InvalidMailAddressError(address, _('Wrong type.'))
            if raise_on_failure:
                raise e
            if verbose > 2:
                LOG.debug(str(e))
            return False

        if verbose > 4:
            LOG.debug(_('Evaluating address {!r} ...').format(addr))
            LOG.debug(_('Search pattern simple: {}').format(cls.re_valid_address))
        if cls.re_valid_address.search(addr):
            return True

        if verbose > 4:
            LOG.debug(_('Search pattern full: {}').format(cls.re_valid_full_address))
        if cls.re_valid_full_address.match(addr):
            return True

        e = InvalidMailAddressError(address, _('Invalid address.'))
        if raise_on_failure:
            raise e
        if verbose > 2:
            LOG.debug(str(e))
        return False

    # -------------------------------------------------------------------------
    def __init__(
            self, address=None, *, user=None, domain=None, name=None, verbose=0, empty_ok=False):
        """Initialise a QualifiedMailAddress object."""
        self._name = None

        if verbose > 3:
            msg = 'Given - address: {a!r}, user: {u!r}, domain: {d!r}, full name: {n!r}.'
            LOG.debug(msg.format(a=address, u=user, d=domain, n=name))

        if address:
            if user or domain or name:
                param_list = ('user', 'domain', 'name')
                msg = _('Parameters {lst} may not be given, if parameter {a!r} was given.')
                msg = msg.format(lst=format_list(param_list, do_repr=True), a='address')
                raise RuntimeError(msg)
            return self._init_from_address(address, verbose=verbose, empty_ok=empty_ok)

        super(QualifiedMailAddress, self).__init__(
            user=user, domain=domain, verbose=verbose, empty_ok=empty_ok)

        if name:
            _name = to_str(name).strip()
            if not isinstance(_name, six.string_types):
                msg = _('Invalid full user name.')
                raise InvalidMailAddressError(name, msg)
            if _name:
                self._name = _name

    # -------------------------------------------------------------------------
    def _init_from_address(self, address, verbose=0, empty_ok=False):

        if not self.valid_full_address(address, raise_on_failure=True, verbose=verbose):
            raise InvalidMailAddressError(address, _('Invalid address.'))

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
            raise InvalidMailAddressError(address, _('Invalid address.'))

        user = match.group(1).strip().lower()
        domain = match.group(2).strip().lower()
        super(QualifiedMailAddress, self)._short_init(
            user=user, domain=domain, verbose=verbose, empty_ok=empty_ok)

    # -----------------------------------------------------------
    @property
    def name(self):
        """Return the full and elaborate name of the owner of the mail address."""
        return self._name

    # -------------------------------------------------------------------------
    def as_dict(self, short=True):
        """
        Transform the elements of the object into a dict.

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
        Transform the elements of the object into a tuple.

        @return: structure as tuple
        @rtype:  tuple
        """
        return (self.user, self.domain, self.name, self.verbose, self.empty_ok)

    # -------------------------------------------------------------------------
    def simple(self):
        """Return a copy of the current address as a simple MailAddress object."""
        return super(QualifiedMailAddress, self).__copy__()

    # -------------------------------------------------------------------------
    def __copy__(self):
        """Return a copy of the current address."""
        addr = self.__class__(empty_ok=True)

        addr._user = self.user
        addr._domain = self.domain
        addr._name = self.name
        addr.verbose = self.verbose
        addr.empty_ok = self.empty_ok

        return addr

    # -------------------------------------------------------------------------
    def __str__(self):
        """Typecast into a string."""
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
        """Typecast into a string for reproduction."""
        out = '<%s(' % (self.__class__.__name__)

        fields = []
        fields.append('user={!r}'.format(self.user))
        fields.append('domain={!r}'.format(self.domain))
        fields.append('name={!r}'.format(self.name))

        out += ', '.join(fields) + ')>'
        return out

    # -------------------------------------------------------------------------
    def __eq__(self, other):
        """Compare for equality."""
        if self.verbose > 5:
            msg = _('Checking equality {self!r} with {other!r} ...')
            LOG.debug(msg.format(self=self, other=other))

        if not isinstance(other, MailAddress):
            return False

        if not isinstance(other, QualifiedMailAddress):
            # Other must be a simple MailAddress
            if self.name is None and self.simple() == other:
                return True
            return False

        if QualifiedMailAddress is not other.__class__.__mro__[0]:
            return False

        if self.simple() != other.simple():
            return False

        return self.name == other.name

    # -------------------------------------------------------------------------
    def __lt__(self, other):
        """Compare, whether the current address is less than another."""
        if not isinstance(other, MailAddress):
            msg = _('Object {o!r} for comparing is not a {c} object.').format(
                o=other, c='MailAddress')
            raise TypeError(msg)

        if self.verbose > 5:
            msg = _('Comparing {self!r} with {other!r} ...')
            LOG.debug(msg.format(self=self, other=other))

        self_simple = self.simple()

        if not isinstance(other, QualifiedMailAddress):
            if self_simple == other:
                return False
            return self_simple < other

        # At this point both self and other are QualifiedMailAddress objects

        other_simple = other.simple()

        if self_simple == other_simple:
            if self.name.lower() == other.name.lower():
                return self.name < other.name
            else:
                return self.name.lower() < other.name.lower()

        return self_simple < other_simple


# =============================================================================
class MailAddressList(FbBaseObject, MutableSequence):
    """A list containing MailAddress or QualifiedMailAddress objects."""

    # -------------------------------------------------------------------------
    def __init__(
        self, *addresses, appname=None, verbose=0, version=__version__, base_dir=None,
            empty_ok=False, may_simple=True, initialized=None):
        """Initialise a MailAddressList object."""
        self._addresses = []
        self._empty_ok = False
        self._may_simple = True

        super(MailAddressList, self).__init__(
            appname=appname, verbose=verbose, version=version, base_dir=base_dir,
            initialized=False)

        self.empty_ok = empty_ok
        self.may_simple = may_simple

        for address in addresses:
            self.append(address)

        if initialized is not None:
            self.initialized = initialized

    # -----------------------------------------------------------
    @property
    def empty_ok(self):
        """Return, whether an empty address is okay.

        Is an empty mail address valid or should there be raised an exceptiom.
        """
        return self._empty_ok

    @empty_ok.setter
    def empty_ok(self, value):
        self._empty_ok = to_bool(value)

    # -----------------------------------------------------------
    @property
    def may_simple(self):
        """Return, whether simple mail addresses are allowed.

        May an address be inserted/appanded as a simple MailAddress, if there is
        no explicit verbose user name, or should it be always as a QualifiedMailAddress
        object.
        """
        return self._may_simple

    @may_simple.setter
    def may_simple(self, value):
        self._may_simple = to_bool(value)

    # -------------------------------------------------------------------------
    def as_dict(self, short=True):
        """
        Transform the elements of the object into a dict.

        @param short: don't include local properties in resulting dict.
        @type short: bool

        @return: structure as dict or list
        @rtype:  dict or list
        """
        res = super(MailAddressList, self).as_dict(short=short)
        res['_addresses'] = []
        res['empty_ok'] = self.empty_ok
        res['may_simple'] = self.may_simple

        for address in self:
            res['_addresses'].append(address.as_dict(short=short))

        return res

    # -------------------------------------------------------------------------
    def as_list(self, as_str=False):
        """Typecast into a list object."""
        res = []
        for address in self:
            if as_str:
                res.append(str(address))
            else:
                res.append(copy.copy(address))

        return res

    # -------------------------------------------------------------------------
    def __str__(self):
        """Typecast into a str object."""
        return pp(self.as_list(True))

    # -------------------------------------------------------------------------
    def __repr__(self):
        """Typecast into a string for reproduction."""
        out = '<%s(' % (self.__class__.__name__)

        fields = []
        fields.append('appname={!r}'.format(self.appname))
        fields.append('verbose={!r}'.format(self.verbose))
        fields.append('version={!r}'.format(self.version))
        fields.append('empty_ok={!r}'.format(self.empty_ok))
        fields.append('may_simple={!r}'.format(self.may_simple))

        for address in self:
            fields.append('{!r}'.format(address))

        out += ', '.join(fields) + ')>'
        return out

    # -------------------------------------------------------------------------
    def _to_address(self, address):
        """Convert given address into a usable MailAddress or QualifiedMailAddress object."""
        if isinstance(address, MailAddress):
            if self.verbose > 5:
                LOG.debug('Trying to use address {!r} ...'.format(address))
            if not self.may_simple and not isinstance(address, QualifiedMailAddress):
                addr = QualifiedMailAddress(
                    user=address.user, domain=address.domain,
                    verbose=self.verbose, empty_ok=self.empty_ok)
                if self.verbose > 4:
                    LOG.debug('Using qualified address {!r} ...'.format(addr))
                return addr
            if self.verbose > 4:
                LOG.debug('Using address {!r} ...'.format(address))
            return address

        addr = QualifiedMailAddress(address, verbose=self.verbose, empty_ok=self.empty_ok)
        if self.may_simple and addr.name is None:
            return addr.simple()
        return addr

    # -------------------------------------------------------------------------
    def append(self, address):
        """Append the given address."""
        addr = self._to_address(address)
        self._addresses.append(addr)

    # -------------------------------------------------------------------------
    def __copy__(self):
        """Return a copy of the current address list."""
        if self.verbose > 1:
            LOG.debug('Copying myself ...')

        new_list = self.__class__(
            appname=self.appname, verbose=self.verbose, base_dir=self.base_dir,
            empty_ok=self.empty_ok, may_simple=self.may_simple, initialized=False)

        for addr in self:
            new_list.append(copy.copy(addr))

        new_list.initialized = self.initialized
        return new_list

    # -------------------------------------------------------------------------
    def __reversed__(self):
        """Return a reversed copy of the current address list."""
        new_list = self.__class__(
            appname=self.appname, verbose=self.verbose, base_dir=self.base_dir,
            empty_ok=self.empty_ok, may_simple=self.may_simple, initialized=False)

        for addr in reversed(self._addresses):
            new_list.append(copy.copy(addr))

        new_list.initialized = self.initialized
        return new_list

    # -------------------------------------------------------------------------
    def __add__(self, other):
        """Return a copy of the current address list with the other list appended."""
        if not is_sequence(other):
            msg = _('Given object {o!r} is not a sequence type, but a {t!r} type instead.')
            raise TypeError(msg.format(o=other, t=other.__class__.__qualname__))

        result = self.__copy__()

        for addr in other:
            result.append(addr)

        return result

    # -------------------------------------------------------------------------
    def __iadd__(self, other):
        """Append the other list to the current address list."""
        if not is_sequence(other):
            msg = _('Given object {o!r} is not a sequence type, but a {t!r} type instead.')
            raise TypeError(msg.format(o=other, t=other.__class__.__qualname__))

        for addr in other:
            self.append(addr)

    # -------------------------------------------------------------------------
    def index(self, address, *args):
        """Get the position of the first occurence of the given address."""
        i = None
        j = None
        addr = self._to_address(address)

        if len(args) > 0:
            if len(args) > 2:
                raise TypeError(_('{m} takes at most {max} arguments ({n} given).').format(
                    m='index()', max=3, n=len(args) + 1))
            i = int(args[0])
            if len(args) > 1:
                j = int(args[1])

        index = 0
        start = 0
        if i is not None:
            start = i
            if i < 0:
                start = len(self) + i

        wrap = False
        end = len(self)
        if j is not None:
            if j < 0:
                end = len(self) + j
                if end < index:
                    wrap = True
            else:
                end = j

        for index in list(range(len(self))):
            item = self._addresses[index]
            if index < start:
                continue
            if index >= end and not wrap:
                break
            if item == addr:
                return index

        if wrap:
            for index in list(range(len(self))):
                item = self._addresses[index]
                if index >= end:
                    break
            if item == addr:
                return index

        msg = _('Mail address {} is not in address list.').format(addr)
        raise ValueError(msg)

    # -------------------------------------------------------------------------
    def __contains__(self, address):
        """Return, whether the given address is existing in current list."""
        if not self._addresses:
            return False

        addr = self._to_address(address)
        for my_addr in self:
            if my_addr == addr:
                return True

        return False

    # -------------------------------------------------------------------------
    def count(self, address):
        """Return the number of given mail address in current list."""
        if not self._addresses:
            return 0

        addr = self._to_address(address)

        num = 0
        for my_addr in self:
            if my_addr == addr:
                num += 1
        return num

    # -------------------------------------------------------------------------
    def __len__(self):
        """Return the number of mail addresses in current list."""
        return len(self._addresses)

    # -------------------------------------------------------------------------
    def __getitem__(self, key):
        """Return the mail address with given index."""
        return self._addresses.__getitem__(key)

    # -------------------------------------------------------------------------
    def __setitem__(self, key, address):
        """Set the given mail address with given index."""
        addr = self._to_address(address)
        self._addresses.__setitem__(key, addr)

    # -------------------------------------------------------------------------
    def __delitem__(self, key):
        """Delete the mail address on given index."""
        del self._addresses[key]

    # -------------------------------------------------------------------------
    def __iter__(self):
        """Return iterator for mail addresses in list."""
        for addr in self._addresses:
            yield addr

    # -------------------------------------------------------------------------
    def insert(self, index, address):
        """Insert given mail address in list on given index."""
        addr = self._to_address(address)
        self._addresses.insert(index, addr)

    # -------------------------------------------------------------------------
    def clear(self):
        """Remove all items from the MailAddressList."""
        self._addresses = []


# =============================================================================

if __name__ == '__main__':

    pass

# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 list
