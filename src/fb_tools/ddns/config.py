#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@summary: A module for providing a configuration for the ddns-update script.

@author: Frank Brehm
@contact: frank@brehm-online.com
@copyright: © 2025 by Frank Brehm, Berlin
"""
from __future__ import absolute_import

# Standard module
import datetime
import logging
import re

try:
    from pathlib import Path
except ImportError:
    from pathlib2 import Path

# Third party modules

# Own modules
from .. import DEFAULT_ENCODING
from ..common import is_sequence
from ..common import timeinterval2delta
from ..common import to_bool
from ..errors import InvalidTimeIntervalError
from ..multi_config import BaseMultiConfig
from ..xlate import XLATOR, format_list

__version__ = "3.1.3"

LOG = logging.getLogger(__name__)

_ = XLATOR.gettext


# =============================================================================
class DdnsConfiguration(BaseMultiConfig):
    """A configuration class for DDNS application classes."""

    default_working_dir = Path("/var/lib/ddns")
    default_logfile = Path("/var/log/ddns/ddnss-update.log")

    default_get_ipv4_url = "https://ip4.ddnss.de/jsonip.php"
    default_get_ipv6_url = "https://ip6.ddnss.de/jsonip.php"
    default_upd_url = "https://www.ddnss.de/upd.php"
    default_upd_ipv4_url = "https://ip4.ddnss.de/upd.php"
    default_upd_ipv6_url = "https://ip6.ddnss.de/upd.php"

    default_ipv4_cache_basename = "my-ipv4-address"
    default_ipv6_cache_basename = "my-ipv6-address"

    default_timeout = 20

    valid_protocols = ("any", "both", "ipv4", "ipv6")

    # Standard interval for forced updating a domain
    default_forced_update_interval = 7 * 24 * 60 * 60

    re_domains_selector = re.compile(r"[,;\s]+")
    re_all_domains = re.compile(r"^all[_-]?domains$", re.IGNORECASE)
    re_with_mx = re.compile(r"^\s*with[_-]?mx\s*$", re.IGNORECASE)
    re_get_url = re.compile(r"^\s*get[_-]?ipv([46])[_-]?url\s*$", re.IGNORECASE)
    re_upd_url = re.compile(r"^\s*upd(?:ate)?[_-]?url\s*$", re.IGNORECASE)
    re_upd_url_ipv = re.compile(r"^\s*upd(?:ate)?[_-]?ipv([46])[_-]?url\s*$", re.IGNORECASE)
    re_forced_update_interval = re.compile(
        r"^^\s*forced[_-]?update[_-]?intervall?\s*$", re.IGNORECASE
    )

    # -------------------------------------------------------------------------
    def __init__(
        self,
        appname=None,
        verbose=0,
        version=__version__,
        base_dir=None,
        append_appname_to_stems=True,
        config_dir=None,
        additional_stems=None,
        additional_cfgdirs=None,
        additional_config_file=None,
        encoding=DEFAULT_ENCODING,
        use_chardet=True,
        initialized=False,
    ):
        """Initialise a DdnsConfiguration object."""
        add_stems = []
        if additional_stems:
            if is_sequence(additional_stems):
                for stem in additional_stems:
                    add_stems.append(stem)
            else:
                add_stems.append(additional_stems)

        if "ddns" not in add_stems:
            add_stems.append("ddns")

        self.working_dir = self.default_working_dir
        self.logfile = self.default_logfile
        self.ddns_user = None
        self.ddns_pwd = None
        self.domains = []
        self.all_domains = False
        self.with_mx = False
        self.get_ipv4_url = self.default_get_ipv4_url
        self.get_ipv6_url = self.default_get_ipv6_url
        self.upd_url = self.default_upd_url
        self.upd_ipv4_url = self.default_upd_ipv4_url
        self.upd_ipv6_url = self.default_upd_ipv6_url
        self._timeout = self.default_timeout
        self.protocol = "any"
        self.ipv4_cache_basename = self.default_ipv4_cache_basename
        self.ipv6_cache_basename = self.default_ipv6_cache_basename
        self.forced_update_interval = datetime.timedelta(
            seconds=self.default_forced_update_interval
        )

        super(DdnsConfiguration, self).__init__(
            appname=appname,
            verbose=verbose,
            version=version,
            base_dir=base_dir,
            append_appname_to_stems=append_appname_to_stems,
            config_dir=config_dir,
            additional_stems=add_stems,
            additional_cfgdirs=additional_cfgdirs,
            encoding=DEFAULT_ENCODING,
            additional_config_file=additional_config_file,
            use_chardet=use_chardet,
            raise_on_error=True,
            ensure_privacy=False,
            initialized=False,
        )

        if initialized:
            self.initialized = True

    # -------------------------------------------------------------------------
    @property
    def timeout(self):
        """Return the timeout in seconds for Web requests."""
        return self._timeout

    @timeout.setter
    def timeout(self, value):
        if value is None:
            self._timeout = self.default_timeout
            return
        val = int(value)
        err_msg = _("Invalid timeout {!r} for Web requests, must be 0 < SECONDS < 3600.")
        if val <= 0 or val > 3600:
            msg = err_msg.format(value)
            raise ValueError(msg)
        self._timeout = val

    # -------------------------------------------------------------------------
    @property
    def ipv4_cache_file(self):
        """Return the Filename (as Path-object) for storing the current public IPv4 address."""
        return self.working_dir / self.ipv4_cache_basename

    # -------------------------------------------------------------------------
    @property
    def ipv6_cache_file(self):
        """Return the Filename (as Path-object) for storing the current public IPv6 address."""
        return self.working_dir / self.ipv6_cache_basename

    # -------------------------------------------------------------------------
    def as_dict(self, short=True):
        """
        Transform the elements of the object into a dict.

        @param short: don't include local properties in resulting dict.
        @type short: bool

        @return: structure as dict
        @rtype:  dict
        """
        res = super(DdnsConfiguration, self).as_dict(short=short)

        res["ddns_pwd"] = None
        if self.ddns_pwd:
            if self.verbose > 4:
                res["ddns_pwd"] = self.ddns_pwd
            else:
                res["ddns_pwd"] = "*******"

        res["default_working_dir"] = self.default_working_dir
        res["default_logfile"] = self.default_logfile
        res["default_get_ipv4_url"] = self.default_get_ipv4_url
        res["default_get_ipv6_url"] = self.default_get_ipv6_url
        res["default_upd_url"] = self.default_upd_url
        res["default_upd_ipv4_url"] = self.default_upd_ipv4_url
        res["default_upd_ipv6_url"] = self.default_upd_ipv6_url
        res["default_timeout"] = self.default_timeout
        res["default_ipv4_cache_basename"] = self.default_ipv4_cache_basename
        res["default_ipv6_cache_basename"] = self.default_ipv6_cache_basename
        res["ipv4_cache_file"] = self.ipv4_cache_file
        res["ipv6_cache_file"] = self.ipv6_cache_file
        res["timeout"] = self.timeout
        res["valid_protocols"] = self.valid_protocols

        return res

    # -------------------------------------------------------------------------
    def eval_section(self, section_name):
        """Evaluate config sections for DDNS."""
        super(DdnsConfiguration, self).eval_section(section_name)

        sn = section_name.lower()

        if sn == "ddns":
            section = self.cfg[section_name]
            return self._eval_config_ddns(section_name, section)

        if sn == "files":
            section = self.cfg[section_name]
            return self._eval_config_files(section_name, section)

    # -------------------------------------------------------------------------
    def _eval_config_ddns(self, section_name, section):

        if self.verbose > 1:
            LOG.debug("Checking config section {!r} ...".format(section_name))

        for key in section.keys():
            value = section[key]

            self._eval_config_ddns_value(key, value, section_name)

        return

    # -------------------------------------------------------------------------
    def _eval_config_ddns_value(self, key, value, section_name):

        if key.lower() == "user" and value.strip():
            self.ddns_user = value.strip()
            return

        if (key.lower() == "pwd" or key.lower() == "password") and value.strip():
            self.ddns_pwd = value.strip()
            return

        if key.lower() == "domains":
            domains_str = value.strip()
            if domains_str:
                self.domains = self.re_domains_selector.split(domains_str)
            return

        if self.re_all_domains.match(key) and value.strip():
            self.all_domains = to_bool(value.strip())
            return

        if self.re_with_mx.match(key) and value.strip():
            self.with_mx = to_bool(value.strip())
            return

        if key.lower() == "timeout":
            try:
                self.timeout = value
            except (ValueError, KeyError) as e:
                msg = _("Invalid value {!r} as timeout:").format(value) + " " + str(e)
                LOG.error(msg)
            return

        match = self.re_get_url.match(key)
        if match and value.strip():
            setattr(self, "get_ipv{}_url".format(match.group(1)), value.strip())
            return

        match = self.re_upd_url.match(key)
        if match and value.strip():
            self.upd_url = value.strip()
            return

        match = self.re_upd_url_ipv.match(key)
        if match and value.strip():
            setattr(self, "upd_ipv{}_url".format(match.group(1)), value.strip())
            return

        if key.lower() == "protocol" and value.strip():
            p = value.strip().lower()
            if p not in self.valid_protocols:
                LOG.error(
                    _(
                        "Invalid value {u!r} for protocols to update in section {s!r}, valid "
                        "protocols are: "
                    ).format(u=value, s=section_name)
                    + format_list(self.valid_protocols, do_repr=True)
                )
            else:
                if p == "both":
                    p = "any"
                self.protocol = p
            return

        match = self.re_forced_update_interval.match(key)
        if match:
            try:
                interval = timeinterval2delta(value)
                self.forced_update_interval = interval
            except InvalidTimeIntervalError as e:
                LOG.error(
                    _("Invalid forced update interval in section {!r}:").format(section_name)
                    + " "
                    + str(e)
                )
            return

        LOG.warning(
            _("Unknown configuration option {o!r} with value {v!r} in " "section {s!r}.").format(
                o=key, v=value, s=section_name
            )
        )

    # -------------------------------------------------------------------------
    def _eval_config_files(self, section_name, section):

        if self.verbose > 1:
            LOG.debug("Checking config section {!r} ...".format(section_name))

        re_work_dir = re.compile(r"^\s*work(ing)?[_-]?dir(ectory)?\ſ*", re.IGNORECASE)
        re_logfile = re.compile(r"^\s*log[_-]?file\s*$", re.IGNORECASE)

        for key in section.keys():
            value = section[key]

            if re_work_dir.match(key) and value.strip():
                p = Path(value.strip())
                if p.is_absolute():
                    self.working_dir = p
                else:
                    LOG.error(
                        _(
                            "The path to the working directory must be an absolute path "
                            "(given: {!r})."
                        ).format(value)
                    )
                continue

            if re_logfile.match(key) and value.strip():
                p = Path(value.strip())
                if p.is_absolute():
                    self.logfile = p
                else:
                    LOG.error(
                        _(
                            "The path to the logfile must be an absolute path " "(given: {!r})."
                        ).format(value)
                    )
                continue

            LOG.warning(
                _(
                    "Unknown configuration option {o!r} with value {v!r} in " "section {s!r}."
                ).format(o=key, v=value, s=section_name)
            )

        return


# =============================================================================

if __name__ == "__main__":

    pass

# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 list
