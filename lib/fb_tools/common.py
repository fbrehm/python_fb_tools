#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: Frank Brehm
@contact: frank.brehm@pixelpark.com
@copyright: © 2018 by Frank Brehm, Berlin
@summary: The module for common used functions.
"""

# Standard modules
import sys
import os
import logging
import re
import pprint
import platform
import locale
import string
import random
import datetime
import pathlib
import ipaddress
import collections

# Third party modules
import six

# Own modules

from .xlate import XLATOR

__version__ = '1.3.1'

_ = XLATOR.gettext

LOG = logging.getLogger(__name__)

RE_YES = re.compile(r'^\s*(?:y(?:es)?|true)\s*$', re.IGNORECASE)
RE_NO = re.compile(r'^\s*(?:no?|false|off)\s*$', re.IGNORECASE)
PAT_TO_BOOL_TRUE = locale.nl_langinfo(locale.YESEXPR)
RE_TO_BOOL_TRUE = re.compile(PAT_TO_BOOL_TRUE)
PAT_TO_BOOL_FALSE = locale.nl_langinfo(locale.NOEXPR)
RE_TO_BOOL_FALSE = re.compile(PAT_TO_BOOL_FALSE)

RE_DOT = re.compile(r'\.')
RE_DOT_AT_END = re.compile(r'(\.)*$')
RE_DECIMAL = re.compile(r'^\d+$')
RE_IPV4_PTR = re.compile(r'\.in-addr\.arpa\.$', re.IGNORECASE)
RE_IPV6_PTR = re.compile(r'\.ip6\.arpa\.$', re.IGNORECASE)

RE_MAC_ADRESS = re.compile(r'^(?:[0-9a-f]{2}:){5}[0-9a-f]{2}$', re.IGNORECASE)

RE_TF_NAME = re.compile(r'[^a-z0-9_]+', re.IGNORECASE)

RE_FQDN = re.compile(
    r'(?=^.{4,253}$)(^((?!-)[a-z0-9-]{1,63}(?<!-)\.)+[a-z]{2,63}\.?$)',
    re.IGNORECASE)

CUR_RADIX = locale.nl_langinfo(locale.RADIXCHAR)
CUR_THOUSEP = locale.nl_langinfo(locale.THOUSEP)
H2MB_PAT = r'^\s*\+?(\d+(?:' + re.escape(CUR_THOUSEP) + r'\d+)*(?:'
H2MB_PAT += re.escape(CUR_RADIX) + r'\d*)?)\s*(\S+)?'
H2MB_RE = re.compile(H2MB_PAT)
RADIX_RE = re.compile(re.escape(CUR_RADIX))
THOUSEP_RE = re.compile(re.escape(CUR_THOUSEP))

RE_B2H_FINAL_ZEROES = re.compile(r'0+$')
RE_B2H_FINAL_SIGNS = re.compile(r'\D+$')

RE_UNIT_BYTES = re.compile(r'^\s*(?:b(?:yte)?)?\s*$', re.IGNORECASE)
RE_UNIT_KBYTES = re.compile(r'^\s*k(?:[bB](?:[Yy][Tt][Ee])?)?\s*$')
RE_UNIT_KIBYTES = re.compile(r'^\s*K[Ii]?(?:[bB](?:[Yy][Tt][Ee])?)?\s*$')
RE_UNIT_MBYTES = re.compile(r'^\s*M(?:B(?:yte)?)?\s*$', re.IGNORECASE)
RE_UNIT_MIBYTES = re.compile(r'^\s*Mi(?:B(?:yte)?)?\s*$', re.IGNORECASE)
RE_UNIT_GBYTES = re.compile(r'^\s*G(?:B(?:yte)?)?\s*$', re.IGNORECASE)
RE_UNIT_GIBYTES = re.compile(r'^\s*Gi(?:B(?:yte)?)?\s*$', re.IGNORECASE)
RE_UNIT_TBYTES = re.compile(r'^\s*T(?:B(?:yte)?)?\s*$', re.IGNORECASE)
RE_UNIT_TIBYTES = re.compile(r'^\s*Ti(?:B(?:yte)?)?\s*$', re.IGNORECASE)
RE_UNIT_PBYTES = re.compile(r'^\s*P(?:B(?:yte)?)?\s*$', re.IGNORECASE)
RE_UNIT_PIBYTES = re.compile(r'^\s*Pi(?:B(?:yte)?)?\s*$', re.IGNORECASE)
RE_UNIT_EBYTES = re.compile(r'^\s*E(?:B(?:yte)?)?\s*$', re.IGNORECASE)
RE_UNIT_EIBYTES = re.compile(r'^\s*Ei(?:B(?:yte)?)?\s*$', re.IGNORECASE)
RE_UNIT_ZBYTES = re.compile(r'^\s*Z(?:B(?:yte)?)?\s*$', re.IGNORECASE)
RE_UNIT_ZIBYTES = re.compile(r'^\s*Zi(?:B(?:yte)?)?\s*$', re.IGNORECASE)


# =============================================================================
def pp(value, indent=4, width=99, depth=None):
    """
    Returns a pretty print string of the given value.

    @return: pretty print string
    @rtype: str
    """

    pretty_printer = pprint.PrettyPrinter(
        indent=indent, width=width, depth=depth)
    return pretty_printer.pformat(value)


# =============================================================================
def terminal_can_colors(debug=False):
    """
    Method to detect, whether the current terminal (stdout and stderr)
    is able to perform ANSI color sequences.

    @return: both stdout and stderr can perform ANSI color sequences
    @rtype: bool

    """

    cur_term = ''
    if 'TERM' in os.environ:
        cur_term = os.environ['TERM'].lower().strip()

    colored_term_list = (
        r'ansi',
        r'linux.*',
        r'screen.*',
        r'[xeak]term.*',
        r'gnome.*',
        r'rxvt.*',
        r'interix',
    )
    term_pattern = r'^(?:' + r'|'.join(colored_term_list) + r')$'
    re_term = re.compile(term_pattern)

    ansi_term = False
    env_term_has_colors = False

    if cur_term:
        if cur_term == 'ansi':
            env_term_has_colors = True
            ansi_term = True
        elif re_term.search(cur_term):
            env_term_has_colors = True
    if debug:
        sys.stderr.write(
            "ansi_term: %r, env_term_has_colors: %r\n" % (
                ansi_term, env_term_has_colors))

    has_colors = False
    if env_term_has_colors:
        has_colors = True
    for handle in [sys.stdout, sys.stderr]:
        if (hasattr(handle, "isatty") and handle.isatty()):
            if debug:
                msg = "{} is a tty.".format(handle.name)
                sys.stderr.write(msg + '\n')
            if (platform.system() == 'Windows' and not ansi_term):
                if debug:
                    sys.stderr.write("platform is Windows and not ansi_term.\n")
                has_colors = False
        else:
            if debug:
                msg = "{} is not a tty.".format(handle.name)
                sys.stderr.write(msg + '\n')
            if ansi_term:
                pass
            else:
                has_colors = False

    return has_colors


# =============================================================================
def to_bool(value):
    """
    Converter from string to boolean values (e.g. from configurations)
    """

    if not value:
        return False

    try:
        v_int = int(value)
    except ValueError:
        pass
    except TypeError:
        pass
    else:
        if v_int == 0:
            return False
        else:
            return True

    global PAT_TO_BOOL_TRUE
    global RE_TO_BOOL_TRUE
    global PAT_TO_BOOL_FALSE
    global RE_TO_BOOL_FALSE

    c_yes_expr = locale.nl_langinfo(locale.YESEXPR)
    if c_yes_expr != PAT_TO_BOOL_TRUE:
        PAT_TO_BOOL_TRUE = c_yes_expr
        RE_TO_BOOL_TRUE = re.compile(PAT_TO_BOOL_TRUE)
    # LOG.debug("Current pattern for 'yes': %r.", c_yes_expr)

    c_no_expr = locale.nl_langinfo(locale.NOEXPR)
    if c_no_expr != PAT_TO_BOOL_FALSE:
        PAT_TO_BOOL_FALSE = c_no_expr
        RE_TO_BOOL_FALSE = re.compile(PAT_TO_BOOL_FALSE)
    # LOG.debug("Current pattern for 'no': %r.", c_no_expr)

    v_str = ''
    if isinstance(value, str):
        v_str = value
        if six.PY2:
            if isinstance(value, unicode):                      # noqa
                v_str = value.encode('utf-8')
    elif six.PY3 and isinstance(value, bytes):
        v_str = value.decode('utf-8')
    else:
        v_str = str(value)

    match = RE_YES.search(v_str)
    if match:
        return True
    match = RE_TO_BOOL_TRUE.search(v_str)
    if match:
        return True

    match = RE_NO.search(v_str)
    if match:
        return False
    match = RE_TO_BOOL_FALSE.search(v_str)
    if match:
        return False

    return bool(value)


# =============================================================================
def to_unicode(obj, encoding='utf-8'):

    do_decode = False
    if six.PY2:
        if isinstance(obj, str):
            do_decode = True
    else:
        if isinstance(obj, bytes):
            do_decode = True

    if do_decode:
        obj = obj.decode(encoding)

    return obj


# =============================================================================
def to_utf8(obj):

    return encode_or_bust(obj, 'utf-8')


# =============================================================================
def encode_or_bust(obj, encoding='utf-8'):

    do_encode = False
    if six.PY2:
        if isinstance(obj, unicode):                            # noqa
            do_encode = True
    else:
        if isinstance(obj, str):
            do_encode = True

    if do_encode:
        obj = obj.encode(encoding)

    return obj


# =============================================================================
def to_bytes(obj, encoding='utf-8'):
    "Wrapper for encode_or_bust()"

    return encode_or_bust(obj, encoding)


# =============================================================================
def to_str(obj, encoding='utf-8'):
    """
    Transformes the given string-like object into the str-type according
    to the current Python version.
    """

    if six.PY2:
        return encode_or_bust(obj, encoding)
    else:
        return to_unicode(obj, encoding)


# =============================================================================
def is_sequence(arg):

    if not isinstance(arg, collections.Sequence):
        return False

    if hasattr(arg, "strip"):
        return False

    return True

# =============================================================================
def caller_search_path(*additional_paths):
    """
    Builds a search path for executables from environment $PATH
    including some standard paths.

    @return: all existing search paths
    @rtype: list
    """

    path_list = []
    search_path = os.environ['PATH']
    if not search_path:
        search_path = os.defpath

    search_path_list = [
        pathlib.Path('/opt/pixelpark/bin'),
        pathlib.Path('/www/bin'),
        pathlib.Path('/opt/PPlocal/bin'),
        pathlib.Path('/opt/puppetlabs/bin'),
        pathlib.Path('/opt/puppetlabs/puppet/bin'),
    ]

    for d in additional_paths:
        search_path_list.append(pathlib.Path(d))

    for d in search_path.split(os.pathsep):
        search_path_list.append(pathlib.Path(d))

    default_path = [
        '/bin',
        '/usr/bin',
        '/usr/local/bin',
        '/sbin',
        '/usr/sbin',
        '/usr/local/sbin',
        '/usr/ucb',
        '/usr/sfw/bin',
        '/opt/csw/bin',
        '/usr/openwin/bin',
        '/usr/ccs/bin',
    ]

    for d in default_path:
        search_path_list.append(pathlib.Path(d))

    for d in search_path_list:
        if not d.exists():
            continue
        if not d.is_dir():
            continue
        d_abs = d.resolve()
        if d_abs not in path_list:
            path_list.append(d_abs)

    return path_list


# =============================================================================
def compare_fqdn(x, y):

    # LOG.debug("Comparing {!r} <=> {!r}.".format(x, y))

    # First check for None values
    if x is None and y is None:
        return 0
    if x is None:
        return -1
    if y is None:
        return 1

    # Check for empty FQDNs
    xs = str(x).strip().lower()
    ys = str(y).strip().lower()

    if xs == '' and ys == '':
        return 0
    if xs == '':
        return -1
    if ys == '':
        return 1

    # Ensure a dot at end
    xs = RE_DOT_AT_END.sub('.', xs)
    ys = RE_DOT_AT_END.sub('.', ys)

    if xs == ys:
        return 0

    # Reverse IPv4 zones first, then reverse IPv6 zones
    if RE_IPV4_PTR.search(xs):
        if not RE_IPV4_PTR.search(ys):
            return -1
    elif RE_IPV4_PTR.search(ys):
        if not RE_IPV4_PTR.search(xs):
            return 1
    elif RE_IPV6_PTR.search(xs):
        if not RE_IPV6_PTR.search(ys):
            return -1
    elif RE_IPV6_PTR.search(ys):
        if not RE_IPV6_PTR.search(xs):
            return 1

    return compare_fqdn_tokens(xs, ys)


# =============================================================================
def compare_fqdn_tokens(xs, ys):

    xa = RE_DOT.split(xs)
    xa.reverse()
    xa.pop(0)

    ya = RE_DOT.split(ys)
    ya.reverse()
    ya.pop(0)

    # Compare token from the last to the first
    nr_tokens = min(len(xa), len(ya))
    while nr_tokens > 0:
        token_x = xa.pop(0)
        token_y = ya.pop(0)
        if RE_DECIMAL.match(token_x) and RE_DECIMAL.match(token_y):
            num_x = int(token_x)
            num_y = int(token_y)
            if num_x < num_y:
                return -1
            elif num_x > num_y:
                return 1
        else:
            if token_x < token_y:
                return -1
            elif token_x > token_y:
                return 1
        nr_tokens -= 1

    if len(xa):
        return 1
    if len(ya):
        return -1

    return 0

# =============================================================================
def human2mbytes(value, si_conform=False, as_float=False):
    """
    Converts the given human readable byte value (e.g. 5MB, 8.4GiB etc.)
    with a prefix into an integer/float value (without a prefix) of MiBiBytes.
    It raises a ValueError on invalid values.

    Available prefixes are:
        - kB (1000), KB (1024), KiB (1024)
        - MB (1000*1000), MiB (1024*1024)
        - GB (1000^3), GiB (1024^3)
        - TB (1000^4), TiB (1024^4)
        - PB (1000^5), PiB (1024^5)
        - EB (1000^6), EiB (1024^6)
        - ZB (1000^7), ZiB (1024^7)

    @raise ValueError: on an invalid value

    @param value: the value to convert
    @type value: str
    @param si_conform: use factor 1000 instead of 1024 for kB a.s.o.
    @type si_conform: bool
    @param as_float: flag to gives back the value as a float value
                     instead of an integer value
    @type as_float: bool

    @return: amount of MibiBytes
    @rtype:  int or float

    """

    if value is None:
        msg = _("Given value is {!r}.").format(None)
        raise ValueError(msg)

    radix = '.'
    radix = re.escape(radix)

    c_radix = locale.nl_langinfo(locale.RADIXCHAR)
    global CUR_RADIX
    global H2MB_PAT
    global H2MB_RE
    global RADIX_RE
    global CUR_THOUSEP
    global THOUSEP_RE

    c_thousep = locale.nl_langinfo(locale.THOUSEP)
    if c_thousep != CUR_THOUSEP:
        CUR_THOUSEP = c_thousep
        # log.debug("Current separator character for thousands is now %r.",
        #         CUR_THOUSEP)
        THOUSEP_RE = re.compile(re.escape(CUR_THOUSEP))

    if c_radix != CUR_RADIX:
        CUR_RADIX = c_radix
        # log.debug("Current decimal radix is now %r.", CUR_RADIX)
        H2MB_PAT = r'^\s*\+?(\d+(?:' + re.escape(CUR_RADIX) + r'\d*)?)\s*(\S+)?'
        if CUR_THOUSEP:
            H2MB_PAT = r'^\s*\+?(\d+(?:' + re.escape(CUR_THOUSEP) + r'\d+)*(?:'
            H2MB_PAT += re.escape(CUR_RADIX) + r'\d*)?)\s*(\S+)?'
        H2MB_RE = re.compile(H2MB_PAT)
        RADIX_RE = re.compile(re.escape(CUR_RADIX))
    # log.debug("Current pattern: %r", H2MB_PAT)

    value_raw = ''
    unit = None
    match = H2MB_RE.search(value)
    if match is not None:
        value_raw = match.group(1)
        unit = match.group(2)
    else:
        msg = _("Could not determine bytes in {!r}.").format(value)
        raise ValueError(msg)

    if CUR_THOUSEP:
        value_raw = THOUSEP_RE.sub('', value_raw)
    if CUR_RADIX != '.':
        value_raw = RADIX_RE.sub('.', value_raw)
    value_float = float(value_raw)
    if unit is None:
        unit = ''

    factor_bin = 1024
    factor_si = 1000
    if not si_conform:
        factor_si = factor_bin

    # LOG.debug("factor_bin: {b!r}, factor_si: {s!r}".format(b=factor_bin, s=factor_si))

    factor = 1

    final_factor = 1024 * 1024

    while int(value_float) != value_float:
        value_float *= 10
        final_factor *= 10
    value_long = int(value_float)

    factor = _get_factor_human2bytes(unit, factor_bin, factor_si)

    # LOG.debug("Using factor {fa!r}, final factor: {fi!r}.".format(fa=factor, fi=final_factor))
    # LOG.debug("Cur value_long = {!r}.".format(value_long))

    lbytes = factor * value_long
    # LOG.debug("Cur long bytes: {!r}.".format(lbytes))
    mbytes = lbytes / final_factor
    if as_float:
        return float(mbytes)
    if mbytes <= sys.maxsize:
        return int(mbytes)
    return mbytes
    if mbytes != int(mbytes):
        raise ValueError("int {integer!r} != long {long!r}.".format(
            integer=int(mbytes), long=mbytes))

    mbytes = int(mbytes)

    return mbytes


# =============================================================================
def _get_factor_human2bytes(unit, factor_bin, factor_si):

    factor = 1

    if RE_UNIT_BYTES.search(unit):
        factor = 1
    elif RE_UNIT_KBYTES.search(unit):
        factor = factor_si
    elif RE_UNIT_KIBYTES.search(unit):
        factor = factor_bin
    elif RE_UNIT_MBYTES.search(unit):
        factor = (factor_si * factor_si)
    elif RE_UNIT_MIBYTES.search(unit):
        factor = (factor_bin * factor_bin)
    elif RE_UNIT_GBYTES.search(unit):
        factor = (factor_si ** 3)
    elif RE_UNIT_GIBYTES.search(unit):
        factor = (factor_bin ** 3)
    elif RE_UNIT_TBYTES.search(unit):
        factor = (factor_si ** 4)
    elif RE_UNIT_TIBYTES.search(unit):
        factor = (factor_bin ** 4)
    elif RE_UNIT_PBYTES.search(unit):
        factor = (factor_si ** 5)
    elif RE_UNIT_PIBYTES.search(unit):
        factor = (factor_bin ** 5)
    elif RE_UNIT_EBYTES.search(unit):
        factor = (factor_si ** 6)
    elif RE_UNIT_EIBYTES.search(unit):
        factor = (factor_bin ** 6)
    elif RE_UNIT_ZBYTES.search(unit):
        factor = (factor_si ** 7)
    elif RE_UNIT_ZIBYTES.search(unit):
        factor = (factor_bin ** 7)
    else:
        msg = _("Couldn't detect unit {!r}.").format(unit)
        raise ValueError(msg)

    return factor


# =============================================================================
def bytes2human(
        value, si_conform=False, precision=None, format_str='{value} {unit}'):
    """
    Converts the given value in bytes into a human readable format.
    The limit for electing the next higher prefix is at 1500.

    It raises a ValueError on invalid values.

    @param value: the value to convert
    @type value: long
    @param si_conform: use factor 1000 instead of 1024 for kB a.s.o.,
                       if do so, than the units are for example MB instead MiB.
    @type si_conform: bool
    @param precision: how many digits after the decimal point have to stay
                      in the result
    @type precision: int
    @param format_str: a format string to format the result.
    @type format_str: str

    @return: the value in a human readable format together with the unit
    @rtype: str

    """

    val = int(value)

    if not val:
        return format_str.format(value='0', unit='Bytes')

    base = 1024
    prefixes = {
        1: 'KiB',
        2: 'MiB',
        3: 'GiB',
        4: 'TiB',
        5: 'PiB',
        6: 'EiB',
        7: 'ZiB',
        8: 'YiB',
    }
    if si_conform:
        base = 1000
        prefixes = {
            1: 'kB',
            2: 'MB',
            3: 'GB',
            4: 'TB',
            5: 'PB',
            6: 'EB',
            7: 'ZB',
            8: 'YB',
        }

    exponent = 0

    float_val = float(val)
    while float_val >= (2 * base) and exponent < 8:
        float_val /= base
        exponent += 1

    unit = ''
    if not exponent:
        precision = None
        unit = 'Bytes'
        if val == 1:
            unit = 'Byte'
        value_str = locale.format_string('%d', val)
        return format_str.format(value=value_str, unit=unit)

    unit = prefixes[exponent]
    value_str = ''
    if precision is None:
        value_str = locale.format_string('%f', float_val)
        value_str = RE_B2H_FINAL_ZEROES.sub('', value_str)
        value_str = RE_B2H_FINAL_SIGNS.sub('', value_str)
    else:
        value_str = locale.format_string('%.*f', (precision, float_val))

    if not exponent:
        return value_str

    return format_str.format(value=value_str, unit=unit)

# =============================================================================
def generate_password(length=12):

    characters = string.ascii_letters + string.punctuation + string.digits
    password = "".join(random.choice(characters) for x in range(length))
    return password


# =============================================================================
def get_monday(day):

    if not isinstance(day, (datetime.date, datetime.datetime)):
        msg = _("Argument {a!r} must be of type {t1!r} or {t2!r}.").format(
            a=day, t1='datetime.date', t2='datetime.datetime')
        raise TypeError(msg)

    # copy of day as datetime.date
    monday = datetime.date(day.year, day.month, day.day)
    # date is Monday => date.weekday() == 0
    if monday.weekday() == 0:
        return monday

    tdiff = datetime.timedelta(monday.weekday())
    monday -= tdiff
    return monday


# =============================================================================
def reverse_pointer(address):

    addr = ipaddress.ip_address(address)

    if addr.version == 4:
        reverse_octets = str(addr).split('.')[::-1]
        return '.'.join(reverse_octets) + '.in-addr.arpa'
    else:
        reverse_chars = addr.exploded[::-1].replace(':', '')
        return '.'.join(reverse_chars) + '.ip6.arpa'


# =============================================================================

if __name__ == "__main__":

    pass

# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
