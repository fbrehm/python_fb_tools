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
from babel.support import Translations

DOMAIN = 'fb_tools'

LOG = logging.getLogger(__name__)

__version__ = '1.1.4'

__me__ = Path(__file__).resolve()
__module_dir__ = __me__.parent
__lib_dir__ = __module_dir__.parent
__base_dir__ = __lib_dir__.parent
LOCALE_DIR = __base_dir__.joinpath('locale')
if not LOCALE_DIR.is_dir():
    LOCALE_DIR = __module_dir__.joinpath('locale')
    if not LOCALE_DIR.is_dir():
        LOCALE_DIR = None

__mo_file__ = gettext.find(DOMAIN, str(LOCALE_DIR))
if __mo_file__:
    try:
        with open(__mo_file__, 'rb') as F:
            XLATOR = Translations(F, DOMAIN)
    except IOError:
        XLATOR = gettext.NullTranslations()
else:
    XLATOR = gettext.NullTranslations()

_ = XLATOR.gettext

# =============================================================================

if __name__ == "__main__":

    print(_("Module directory: {!r}").format(__module_dir__))
    print(_("Base directory: {!r}").format(__base_dir__))
    print(_("Locale directory: {!r}").format(LOCALE_DIR))
    print(_("Locale domain: {!r}").format(DOMAIN))
    print(_("Found .mo-file: {!r}").format(__mo_file__))

# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
