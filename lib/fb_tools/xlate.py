#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: Frank Brehm
@contact: frank.brehm@pixelpark.com
@copyright: © 2018 by Frank Brehm, Berlin
@summary: The module for i18n.
          It provides translation object, usable from all other
          modules in this package.
"""
from __future__ import absolute_import, print_function

# Standard modules
import os
import logging
import gettext
import pathlib

from pathlib import Path

# Third party modules
import six

from babel.support import Translations

# Own modules
#if __name__ == "__main__":
#    from common import to_str
#else:
#    from .common import to_str

DOMAIN = 'fb_tools'

LOG = logging.getLogger(__name__)

__me__ = Path(__file__).resolve()
__module_dir__ = __me__.parent
__lib_dir__ = __module_dir__.parent
__base_dir__ = __lib_dir__.parent
LOCALE_DIR = __base_dir__.joinpath('locale')
if not LOCALE_DIR.is_dir():
    LOCALE_DIR = None

__mo_file__ = gettext.find(DOMAIN, str(LOCALE_DIR))
if __mo_file__:
    try:
        with open(__mo_file__, 'rb') as F:
            XLATOR = Translations(F, DOMAIN)
    except FileNotFoundError:
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


