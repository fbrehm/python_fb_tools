#!/bin/env python3
# -*- coding: utf-8 -*-
"""
@summary: A module for common used objects, error classes and functions.

@author: Frank Brehm
@contact: frank@brehm-online.com
@copyright: © 2024 by Frank Brehm, Berlin
"""
# flake8: noqa
from __future__ import absolute_import

# Own modules

from .mailaddress import MailAddress, QualifiedMailAddress, MailAddressList
from .multi_config import BaseMultiConfig

DDNS_CFG_BASENAME = 'ddns.ini'
MAX_TIMEOUT = 3600
UTF8_ENCODING = 'utf-8'
DEFAULT_ENCODING = UTF8_ENCODING
DEFAULT_TERMINAL_WIDTH = 99
DEFAULT_TERMINAL_HEIGHT = 40

__version__ = '2.6.0'

# vim: ts=4 et list
