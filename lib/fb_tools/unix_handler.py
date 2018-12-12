#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
@summary: additional logging handler for the common logging framework
          to combine it with syslog
'''

# Standard modules
import logging
import syslog
import os.path
import sys

from numbers import Number

# Third party modules

# Own modules
from .xlate import XLATOR

__version__ = '1.1.0'
_ = XLATOR.gettext


# =============================================================================
class UnixSyslogHandler(logging.Handler):
    '''
    A handler class which sends formatted logging records over
    the C API.
    '''

    # from <linux/sys/syslog.h>:
    # ======================================================================
    # priorities/facilities are encoded into a single 32-bit quantity, where
    # the bottom 3 bits are the priority (0-7) and the top 28 bits are the
    # facility (0-big number). Both the priorities and the facilities map
    # roughly one-to-one to strings in the syslogd(8) source code.  This
    # mapping is included in this file.
    #
    # priorities (these are ordered)

    LOG_EMERG = 0    # system is unusable
    LOG_ALERT = 1    # action must be taken immediately
    LOG_CRIT = 2     # critical conditions
    LOG_ERR = 3      # error conditions
    LOG_WARNING = 4  # warning conditions
    LOG_NOTICE = 5   # normal but significant condition
    LOG_INFO = 6     # informational
    LOG_DEBUG = 7    # debug-level messages

    # facility codes
    LOG_KERN = 0       # kernel messages
    LOG_USER = 1       # random user-level messages
    LOG_MAIL = 2       # mail system
    LOG_DAEMON = 3     # system daemons
    LOG_AUTH = 4       # security/authorization messages
    LOG_SYSLOG = 5     # messages generated internally by syslogd
    LOG_LPR = 6        # line printer subsystem
    LOG_NEWS = 7       # network news subsystem
    LOG_UUCP = 8       # UUCP subsystem
    LOG_CRON = 9       # clock daemon
    LOG_AUTHPRIV = 10  # security/authorization messages (private)
    LOG_FTP = 11       # FTP daemon

    # other codes through 15 reserved for system use
    LOG_LOCAL0 = 16  # reserved for local use
    LOG_LOCAL1 = 17  # reserved for local use
    LOG_LOCAL2 = 18  # reserved for local use
    LOG_LOCAL3 = 19  # reserved for local use
    LOG_LOCAL4 = 20  # reserved for local use
    LOG_LOCAL5 = 21  # reserved for local use
    LOG_LOCAL6 = 22  # reserved for local use
    LOG_LOCAL7 = 23  # reserved for local use
    # options for syslog.openlog()
    # LOG_PID, LOG_CONS, LOG_NDELAY, LOG_NOWAIT
    LOG_PID = syslog.LOG_PID        # log the pid with each message
    LOG_CONS = syslog.LOG_CONS      # log on the console if errors in sending
    LOG_NDELAY = syslog.LOG_NDELAY  # don't delay open
    # if forking to log on console, don't wait()
    LOG_NOWAIT = syslog.LOG_NOWAIT

    priority_names = {
        "alert": LOG_ALERT,
        "crit": LOG_CRIT,
        "critical": LOG_CRIT,
        "debug": LOG_DEBUG,
        "emerg": LOG_EMERG,
        "err": LOG_ERR,
        "error": LOG_ERR,       # DEPRECATED
        "info": LOG_INFO,
        "notice": LOG_NOTICE,
        "panic": LOG_EMERG,     # DEPRECATED
        "warn": LOG_WARNING,    # DEPRECATED
        "warning": LOG_WARNING,
    }

    priority_ids = {}
    for key in list(priority_names.keys()):
        val = priority_names[key]
        if val not in priority_ids:
            priority_ids[val] = key

    facility_names = {
        "auth": LOG_AUTH,
        "authpriv": LOG_AUTHPRIV,
        "cron": LOG_CRON,
        "daemon": LOG_DAEMON,
        "ftp": LOG_FTP,
        "kern": LOG_KERN,
        "lpr": LOG_LPR,
        "mail": LOG_MAIL,
        "news": LOG_NEWS,
        "security": LOG_AUTH,       # DEPRECATED
        "user": LOG_USER,
        "uucp": LOG_UUCP,
        "local0": LOG_LOCAL0,
        "local1": LOG_LOCAL1,
        "local2": LOG_LOCAL2,
        "local3": LOG_LOCAL3,
        "local4": LOG_LOCAL4,
        "local5": LOG_LOCAL5,
        "local6": LOG_LOCAL6,
        "local7": LOG_LOCAL7,
    }

    facility_ids = {}
    for key in list(facility_names.keys()):
        val = facility_names[key]
        if val not in facility_ids:
            facility_ids[val] = key

    priority_map = {
        "DEBUG": "debug",
        "INFO": "info",
        "WARNING": "warning",
        "ERROR": "error",
        "CRITICAL": "critical"
    }

    # -------------------------------------------------------------------------
    def __init__(
            self, ident=None, logopt=LOG_PID,
            facility=LOG_USER, encoding="utf-8"):
        """
        Initialize a handler.

        @param ident: Identifier of the syslog message, uses basename
                      or current running program, if not given
        @type ident: str
        @param logopt: options for syslog.openlog(), see there for possible
                       values (linked with a binary or). Uses LOG_PID,
                       if not given.
        @type logopt: int
        @param facility: syslog facility to use.
        @type facility: int
        @param encoding: the character set to use to encode unicode messages
        @type encoding: str

        """

        self._opened = False
        self._facility = 'user'

        logging.Handler.__init__(self)

        if ident is not None:
            ident = ident.strip()
            if ident == '':
                ident = None
        if ident is None:
            ident = os.path.basename(sys.argv[0])

        self.ident = ident
        """
        @ivar: Identifier of the syslog message.
        @type: str
        """

        self.logopt = logopt
        """
        @ivar: options for syslog.openlog()
        @type: int
        """

        self.facility = facility

        self.encoding = encoding
        """
        @ivar: the character set to use to encode unicode messages
        @type: str
        """

        self.formatter = None

        syslog.openlog(self.ident, self.logopt, self.facility_id)

        self._opened = True

    # -------------------------------------------------------------------------
    @property
    def opened(self):
        """Is the syslog object already opened."""
        return getattr(self, '_opened', False)

    # -------------------------------------------------------------------------
    @property
    def facility(self):
        """The syslog facility name to use."""
        return getattr(self, '_facility', 'user')

    @facility.setter
    def facility(self, value):
        if self.opened:
            return

        used_facility = 'user'
        if isinstance(value, Number):
            v = int(value)
            if v not in self.facility_ids:
                msg = _("Invalid value {!r} for facility.").format(value)
                raise ValueError(msg)
            used_facility = self.facility_ids[v]
        else:
            used_facility = str(value).lower()
            if used_facility not in self.facility_names:
                msg = _("Invalid value {!r} for facility.").format(value)
                raise ValueError(msg)
        self._facility = used_facility

    # -------------------------------------------------------------------------
    @property
    def facility_id(self):
        """The numeric value of the syslog facility."""
        return self.facility_names.get(
            self.facility, self.facility_names['user'])

    # -------------------------------------------------------------------------
    def close(self):
        """
        Closes the handler.
        """

        syslog.closelog()
        logging.Handler.close(self)

    # -------------------------------------------------------------------------
    def mapPriority(self, level_name):
        """
        Map a logging level name to a key in the priority_names map.
        This is useful in two scenarios: when custom levels are being
        used, and in the case where you can't do a straightforward
        mapping by lowercasing the logging level name because of locale-
        specific issues (see SF #1524081).

        If no valid level name was given, "warning" is assumed.

        @param level_name: the level name, which should be mapped
        @type level_name: str

        @return: the numeric logging level code
        @rtype: str

        """

        return self.priority_map.get(level_name.upper(), "warning")

    # -------------------------------------------------------------------------
    def emit(self, record):
        """
        Emit a record.

        The record is formatted, and then sent to the syslog server. If
        exception information is present, it is NOT sent to the server.
        """

        msg = record.msg
        if sys.version_info[0] > 2:
            if isinstance(msg, bytes):
                msg = msg.decode(self.encoding)
                record.msg = msg
        else:
            if isinstance(msg, unicode):                # noqa
                msg = msg.encode(self.encoding)
                record.msg = msg

        msg_send = self.format(record)

        level_name = self.mapPriority(record.levelname)
        level_id = self.priority_names[level_name]

        try:
            syslog.syslog(level_id, msg_send)
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception:
            self.handleError(record)


# =============================================================================
if __name__ == "__main__":

    pass

# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
