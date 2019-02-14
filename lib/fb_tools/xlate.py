#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: Frank Brehm
@contact: frank.brehm@pixelpark.com
@copyright: © 2019 by Frank Brehm, Berlin
@summary: The module for i18n.
          It provides translation object, usable from all other
          modules in this package.
"""
from __future__ import absolute_import, print_function

# Standard modules
import logging
import gettext

from pathlib import Path

# Third party modules
import babel
from babel.core import Locale
from babel.support import Translations

DOMAIN = 'fb_tools'

LOG = logging.getLogger(__name__)

__version__ = '1.1.5'

__me__ = Path(__file__).resolve()
__module_dir__ = __me__.parent
__lib_dir__ = __module_dir__.parent
__base_dir__ = __lib_dir__.parent
LOCALE_DIR = __base_dir__.joinpath('locale')
if not LOCALE_DIR.is_dir():
    LOCALE_DIR = __module_dir__.joinpath('locale')
    if not LOCALE_DIR.is_dir():
        LOCALE_DIR = None

DEFAULT_LOCALE_DEF = 'en_US'
DEFAULT_LOCALE = babel.core.default_locale()
if not DEFAULT_LOCALE:
    DEFAULT_LOCALE = DEFAULT_LOCALE_DEF

__mo_file__ = gettext.find(DOMAIN, str(LOCALE_DIR))
if __mo_file__:
    try:
        with open(__mo_file__, 'rb') as F:
            XLATOR = Translations(F, DOMAIN)
    except IOError:
        XLATOR = gettext.NullTranslations()
else:
    XLATOR = gettext.NullTranslations()

SUPPORTED_LANGS = (
    'de_DE',
    'en_US'
)

_ = XLATOR.gettext


# =============================================================================
def format_list(lst, do_repr=False, locale=DEFAULT_LOCALE):
    """
    Format the items in `lst` as a list.
    :param lst: a sequence of items to format in to a list
    :param locale: the locale
    """
    locale = Locale.parse(locale)
    if not lst:
        return ''

    if do_repr:
        lst = map(repr, lst)

    if len(lst) == 1:
        return lst[0]

    result = locale.list_patterns['start'].format(lst[0], lst[1])
    for elem in lst[2:-1]:
        result = locale.list_patterns['middle'].format(result, elem)
    result = locale.list_patterns['end'].format(result, lst[-1])

    return result

# =============================================================================
if __name__ == "__main__":

    print(_("Module directory: {!r}").format(__module_dir__))
    print(_("Base directory: {!r}").format(__base_dir__))
    print(_("Locale directory: {!r}").format(LOCALE_DIR))
    print(_("Locale domain: {!r}").format(DOMAIN))
    print(_("Found .mo-file: {!r}").format(__mo_file__))

# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
