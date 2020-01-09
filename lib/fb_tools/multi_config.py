#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: Frank Brehm
@contact: frank.brehm@pixelpark.com
@copyright: © 2019 by Frank Brehm, Berlin
@summary: A module for providing a configuration based on multiple configuration files
"""
from __future__ import absolute_import

# Standard module
import logging
import pathlib
import codecs
import argparse
import json

from pathlib import Path

# Third party modules
import six

from six import StringIO
from six.moves import configparser

from configparser import Error as ConfigParseError

import yaml

HAS_HJSON = False
try:
    import hjson
    HAS_HJSON = True
except ImportError:
    pass

# Own modules
from .errors import FbError

from .obj import FbBaseObject

from .xlate import XLATOR

__version__ = '0.1.0'
LOG = logging.getLogger(__name__)
DEFAULT_ENCODING = 'utf-8'

_ = XLATOR.gettext



# =============================================================================

if __name__ == "__main__":

    pass

# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 list
