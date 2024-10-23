#!/bin/env python3
# -*- coding: utf-8 -*-
"""
@summary: A module for common used objects, error classes and functions.

@author: Frank Brehm
@contact: frank@brehm-online.com
@copyright: © 2024 by Frank Brehm, Berlin
"""
from __future__ import absolute_import

UTF8_ENCODING = 'utf-8'

DDNS_CFG_BASENAME = 'ddns.ini'
MAX_TIMEOUT = 3600
MAX_PORT_NUMBER = (2 ** 16) - 1
DEFAULT_ENCODING = UTF8_ENCODING
DEFAULT_TERMINAL_WIDTH = 99
DEFAULT_TERMINAL_HEIGHT = 40

# Own modules

from .mailaddress import MailAddress, MailAddressList, QualifiedMailAddress     # noqa: F401
from .multi_config import BaseMultiConfig                                       # noqa: F401

__version__ = '2.7.0'

# vim: ts=4 et list
