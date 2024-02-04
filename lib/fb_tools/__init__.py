#!/bin/env python3
# -*- coding: utf-8 -*-
"""
@summary: A module for common used objects, error classes and functions.

@author: Frank Brehm
@contact: frank@brehm-online.com
@copyright: © 2023 by Frank Brehm, Berlin
"""

DDNS_CFG_BASENAME = 'ddns.ini'
MAX_TIMEOUT = 3600
UTF8_ENCODING = 'utf-8'
DEFAULT_ENCODING = UTF8_ENCODING

__version__ = '2.3.4'

from .mailaddress import MailAddress, QualifiedMailAddress, MailAddressList     # noqa
from .multi_config import BaseMultiConfig                                       # noqa

# vim: ts=4 et list
