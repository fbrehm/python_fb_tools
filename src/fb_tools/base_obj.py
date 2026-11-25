#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@summary: Module for a base object class, which is used everywhere in my projects.

@author: Frank Brehm
@contact: frank@brehm-online.com
@copyright: © 2018 - 2026 Frank Brehm, Berlin
"""

from __future__ import absolute_import

# Standard modules
import datetime
import logging
import os
import sys
import traceback
from abc import ABCMeta, abstractmethod

# Third party modules
from six import add_metaclass

# Own modules
from .common import pp, to_bytes
from .xlate import XLATOR

__version__ = "1.0.0"

LOG = logging.getLogger(__name__)

_ = XLATOR.gettext


# =============================================================================
@add_metaclass(ABCMeta)
class FbGenericBaseObject(object):
    """Base class for all and everything.

    42
    """

    # -------------------------------------------------------------------------
    @classmethod
    def get_generic_appname(cls, appname=None):
        """Get the base name of the currently running application."""
        if appname:
            v = str(appname).strip()
            if v:
                return v
        return os.path.basename(sys.argv[0])

    # -------------------------------------------------------------------------
    def __str__(self):
        """Typecast into a string object.

        @return: structure as string
        @rtype:  str
        """
        return pp(self.as_dict(short=True))

    # -------------------------------------------------------------------------
    @abstractmethod
    def __repr__(self):
        """Typecast into a string for reproduction."""
        out = "<%s()>" % (self.__class__.__name__)
        return out

    # -------------------------------------------------------------------------
    def as_dict(self, short=True):
        """
        Transform the elements of the object into a dict.

        @param short: don't include local properties in resulting dict.
        @type short: bool

        @return: structure as dict
        @rtype:  dict
        """
        res = {}
        for key in self.__dict__:
            if short and key.startswith("_") and not key.startswith("__"):
                continue
            val = self.__dict__[key]
            if isinstance(val, FbGenericBaseObject):
                res[key] = val.as_dict(short=short)
            else:
                res[key] = val

        res["__class_name__"] = self.__class__.__name__

        return res

    # -------------------------------------------------------------------------
    def handle_error(self, error_message=None, exception_name=None, do_traceback=False):
        """
        Handle an error gracefully.

        Print a traceback and continue.

        @param error_message: the error message to display
        @type error_message: Exception or str
        @param exception_name: name of the exception class
        @type exception_name: str
        @param do_traceback: allways show a traceback
        @type do_traceback: bool

        """
        msg = str(error_message).strip()
        if not msg:
            msg = _("undefined error.")
        title = None

        if isinstance(error_message, Exception):
            title = error_message.__class__.__name__
        else:
            if exception_name is not None:
                title = exception_name.strip()
            else:
                title = _("Exception happened")
        msg = title + ": " + msg

        root_log = logging.getLogger()
        has_handlers = False
        if root_log.handlers:
            has_handlers = True

        if has_handlers:
            LOG.error(msg)
            if do_traceback:
                LOG.error(traceback.format_exc())
        else:
            curdate = datetime.datetime.now()
            curdate_str = "[" + curdate.isoformat(" ") + "]: "
            msg = curdate_str + msg + "\n"
            if hasattr(sys.stderr, "buffer"):
                sys.stderr.buffer.write(to_bytes(msg))
            else:
                sys.stderr.write(msg)
            if do_traceback:
                traceback.print_exc()

        return

    # -------------------------------------------------------------------------
    def handle_info(self, message, info_name=None):
        """
        Show an information.

        This happens both to STDERR and to all initialized log handlers.

        @param message: the info message to display
        @type message: str
        @param info_name: Title of information
        @type info_name: str

        """
        msg = ""
        if info_name is not None:
            info_name = info_name.strip()
            if info_name:
                msg = info_name + ": "
        msg += str(message).strip()

        root_log = logging.getLogger()
        has_handlers = False
        if root_log.handlers:
            has_handlers = True

        if has_handlers:
            LOG.info(msg)
        else:
            curdate = datetime.datetime.now()
            curdate_str = "[" + curdate.isoformat(" ") + "]: "
            msg = curdate_str + msg + "\n"
            if hasattr(sys.stderr, "buffer"):
                sys.stderr.buffer.write(to_bytes(msg))
            else:
                sys.stderr.write(msg)

        return


# =============================================================================

if __name__ == "__main__":

    pass

# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
