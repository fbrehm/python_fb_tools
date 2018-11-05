#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@author: Frank Brehm
@contact: frank@brehm-online.com
@license: LGPL3+
@copyright: © 2018 Frank Brehm, Berlin
@summary: Modules for common used objects, error classes and methods.
"""
from __future__ import print_function

import os
import sys
import re
import pprint
import datetime

# Third party modules
import six
from setuptools import setup

# own modules:
base_dir = os.path.join(__file__)
lib_dir = os.path.join(base_dir, 'lib')
module_dir = os.path.join(lib_dir, 'fb_tools')
init_py = os.path.join(module_dir, '__init__.py')

if os.path.exists(lib_dir) and os.path.exists(module_dir) and os.path.isfile(init_py):
    sys.path.insert(0, os.path.abspath(lib_dir))


# =======================================================================

# vim: fileencoding=utf-8 filetype=python ts=4 expandtab
