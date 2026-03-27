#!/bin/env python3
# -*- coding: utf-8 -*-
"""
@summary: A module for common used objects, error classes and functions.

@author: Frank Brehm
@contact: frank@brehm-online.com
@copyright: © 2018 - 2026 by Frank Brehm, Berlin
"""

from __future__ import absolute_import

UTF8_ENCODING = "utf-8"

MAX_TIMEOUT = 3600
MAX_PORT_NUMBER = (2**16) - 1
DEFAULT_ENCODING = UTF8_ENCODING
DEFAULT_TERMINAL_WIDTH = 99
DEFAULT_TERMINAL_HEIGHT = 40

# Minimal usable terminal size
MIN_TERM_WIDTH = 10
# Maximal usable terminal size
MAX_TERM_WIDTH = 4000
# Minimal indention of configuration files
MIN_INDENT = 2
# Maximal indention of configuration files
MAX_INDENT = 12

# Own modules

from .mailaddress import MailAddress, MailAddressList, QualifiedMailAddress  # noqa: F401
from .multi_config import BaseMultiConfig  # noqa: F401

__version__ = "3.1.1"

# vim: ts=4 et list
