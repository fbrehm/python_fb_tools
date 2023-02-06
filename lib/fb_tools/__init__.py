#!/bin/env python3
# -*- coding: utf-8 -*-
"""
@summary: A module for common used objects, error classes and functions.

@author: Frank Brehm
@contact: frank@brehm-online.com
@copyright: © 2022 by Frank Brehm, Berlin
"""

DDNS_CFG_BASENAME = 'ddns.ini'
MAX_TIMEOUT = 3600

__version__ = '2.2.2'

from .mailaddress import MailAddress, QualifiedMailAddress, MailAddressList      # noqa

# vim: ts=4 et list
