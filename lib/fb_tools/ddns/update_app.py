#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@summary: The module for the classes of the update-ddns application.

@author: Frank Brehm
@contact: frank.brehm@pixelpark.com
@copyright: © 2024 by Frank Brehm, Berlin
"""
from __future__ import absolute_import, print_function

# Standard modules
import copy
import ipaddress
import logging
import os
import sys
try:
    from pathlib import Path
except ImportError:
    from pathlib2 import Path

# Third party module
from fb_logging.colored import ColoredFormatter

from six.moves.urllib.parse import quote

# Own modules
from . import BaseDdnsApplication
from .config import DdnsConfiguration
from .errors import DdnsAppError
from .errors import WorkDirAccessError
from .errors import WorkDirError
from .errors import WorkDirNotDirError
from .errors import WorkDirNotExistsError
from .. import __version__ as GLOBAL_VERSION
from ..common import pp
from ..xlate import XLATOR, format_list

__version__ = '2.1.1'
LOG = logging.getLogger(__name__)

_ = XLATOR.gettext


# =============================================================================
class UpdateDdnsApplication(BaseDdnsApplication):
    """Class for the application objects."""

    show_assume_options = False
    show_console_timeout_option = False
    show_force_option = True
    show_simulate_option = True

    # -------------------------------------------------------------------------
    def __init__(
        self, version=GLOBAL_VERSION, initialized=None, description=None,
            *args, **kwargs):
        """Initialise a UpdateDdnsApplication object."""
        self.last_ipv4_address = None
        self.last_ipv6_address = None
        self.current_ipv4_address = None
        self.current_ipv6_address = None
        self.txt_records = []
        self.cur_resolved_addresses = {}

        self._force_desc_msg = _('Updating the DDNS records, even if seems not to be changed.')

        if description is None:
            description = _(
                'Tries to update the A and/or AAAA record at ddns.de with the current '
                'IP address.')
        valid_proto_list = copy.copy(DdnsConfiguration.valid_protocols)

        self._ipv4_help = _('Update only the {} record with the public IP address.').format('A')
        self._ipv6_help = _('Update only the {} record with the public IP address.').format('AAAA')
        self._proto_help = _(
            'The IP protocol, for which the appropriate DNS record should be updated with the '
            'public IP (one of {c}, default {d!r}).').format(c=format_list(
                valid_proto_list, do_repr=True, style='or'), d='any')

        super(UpdateDdnsApplication, self).__init__(
            version=version,
            description=description,
            initialized=False,
            *args, **kwargs
        )

        if initialized is None:
            self.initialized = True
        else:
            if initialized:
                self.initialized = True

    # -------------------------------------------------------------------------
    def _get_log_formatter(self, is_term=True):

        # create formatter
        if is_term:
            format_str = ''
            if self.verbose > 1:
                format_str = '[%(asctime)s]: '
            format_str += self.appname + ': '
        else:
            format_str = '[%(asctime)s]: ' + self.appname + ': '
        if self.verbose:
            if self.verbose > 1:
                format_str += '%(name)s(%(lineno)d) %(funcName)s() '
            else:
                format_str += '%(name)s '
        format_str += '%(levelname)s - %(message)s'
        if is_term and self.terminal_has_colors:
            formatter = ColoredFormatter(format_str)
        else:
            formatter = logging.Formatter(format_str)

        return formatter

    # -------------------------------------------------------------------------
    def init_logging(self):
        """Initialize the logger object.

        It creates a colored loghandler with all output to STDERR.
        Maybe overridden in descendant classes.

        @return: None
        """
        if not self.do_init_logging:
            return

        log_level = logging.INFO
        if self.verbose:
            log_level = logging.DEBUG
        elif self.quiet:
            log_level = logging.WARNING

        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)

        formatter = self._get_log_formatter()

        # create log handler for console output
        lh_console = logging.StreamHandler(sys.stderr)
        lh_console.setLevel(log_level)
        lh_console.setFormatter(formatter)

        root_logger.addHandler(lh_console)

        if self.verbose < 3:
            paramiko_logger = logging.getLogger('paramiko.transport')
            if self.verbose < 1:
                paramiko_logger.setLevel(logging.WARNING)
            else:
                paramiko_logger.setLevel(logging.INFO)

        return

    # -------------------------------------------------------------------------
    def init_file_logging(self):
        """Initialise logging into a logfile."""
        if not self.do_init_logging:
            return

        logfile = self.config.logfile
        if not logfile:
            return

        logdir = logfile.parent

        if self.verbose > 1:
            LOG.debug(_(
                'Checking existence and accessibility of log directory {!r} ...').format(
                str(logdir)))

        if not logdir.exists():
            raise WorkDirNotExistsError(logdir)

        if not logdir.is_dir():
            raise WorkDirNotDirError(logdir)

        if not os.access(str(logdir), os.R_OK):
            raise WorkDirAccessError(logdir, _('No read access'))

        if not os.access(str(logdir), os.W_OK):
            raise WorkDirAccessError(logdir, _('No write access'))

        root_log = logging.getLogger()
        formatter = self._get_log_formatter(is_term=False)

        lh_file = logging.FileHandler(str(logfile), mode='a', encoding='utf-8', delay=True)
        if self.verbose:
            lh_file.setLevel(logging.DEBUG)
        else:
            lh_file.setLevel(logging.INFO)
        lh_file.setFormatter(formatter)
        root_log.addHandler(lh_file)

    # -------------------------------------------------------------------------
    def init_arg_parser(self):
        """Initiate the argument parser."""
        super(UpdateDdnsApplication, self).init_arg_parser()

        update_group = self.arg_parser.add_argument_group(_('Update DDNS options'))

        update_group.add_argument(
            '-U', '--user', metavar=_('USER'), dest='user',
            help=_('The username to login at ddns.de.')
        )

        update_group.add_argument(
            '-P', '--password', metavar=_('PASSWORD'), dest='password',
            help=_('The password of the user to login at ddns.de.')
        )

        update_group.add_argument(
            '--logfile', nargs='?', metavar=_('FILENAME'), dest='logfile', const='',
            help=_('The filename to use as a logfile. Leave it empty to disable file logging.'),
        )

        domain_group = update_group.add_mutually_exclusive_group()

        domain_group.add_argument(
            '-A', '--all', '--all-domains', action='store_true', dest='all_domains',
            help=_('Update all domains, which are connected whith the given ddns account.'),
        )

        domain_group.add_argument(
            '-D', '--domain', nargs='+', metavar=_('DOMAIN'), dest='domains',
            help=_('The particular domain(s), which should be updated (if not all).')
        )

    # -------------------------------------------------------------------------
    def post_init(self):
        """
        Execute post-init actions.

        Method to execute before calling run(). Here could be done some
        finishing actions after reading in commandline parameters,
        configuration a.s.o.
        """
        super(UpdateDdnsApplication, self).post_init()
        self.initialized = False

        self.perform_arg_parser_late()

        try:
            self.init_file_logging()
        except WorkDirError as e:
            LOG.error(str(e))
            self.exit(3)

        self.initialized = True

    # -------------------------------------------------------------------------
    def perform_arg_parser_late(self):
        """Execute some actions after parsing the command line parameters."""
        if self.args.user:
            user = self.args.user.strip()
            if user:
                self.config.ddns_user = user

        if self.args.password:
            self.config.ddns_pwd = self.args.password

        if self.args.logfile is not None:
            logfile = self.args.logfile.strip()
            if logfile == '':
                self.config.logfile = None
            else:
                self.config.logfile = Path(logfile).resolve()

        if self.args.all_domains:
            self.config.all_domains = True
        elif self.args.domains:
            self.config.domains = []
            for domain in self.args.domains:
                self.config.domains.append(domain)

    # -------------------------------------------------------------------------
    def _run(self):

        LOG.info(_('Starting {a!r}, version {v!r} ...').format(
            a=self.appname, v=self.version))

        self.get_current_addresses()

        if self.config.all_domains:
            LOG.info(_('Updating all domains ...'))
        else:
            for domain in self.config.domains:
                self.update_domain(domain)
        self.empty_line()

        # if self.config.protocol in ('any', 'both', 'ipv4'):
        #     self.do_update_ipv4()

        # if self.config.protocol in ('any', 'both', 'ipv6'):
        #     self.do_update_ipv6()

        LOG.info(_('Ending {a!r}.').format(
            a=self.appname, v=self.version))

    # -------------------------------------------------------------------------
    def pre_run(self):
        """Execute some actions before the main routine."""
        if self.verbose > 1:
            LOG.debug(_('Actions before running.'))

        if not self.config.all_domains and not self.config.domains:
            msg = _('No domains to update given, but the option all domains is deactivated.')
            LOG.error(msg)
            self.exit(6)

        # try:
        #     self.verify_working_dir()
        # except WorkDirError as e:
        #     LOG.error(str(e))
        #     self.exit(3)

    # -------------------------------------------------------------------------
    def get_current_addresses(self):
        """Get the current addresses."""
        self.current_ipv4_address = None
        current_address_v4 = self.get_my_ipv(4)
        my_ip_v4 = None
        if current_address_v4:
            try:
                my_ip_v4 = ipaddress.ip_address(current_address_v4)
                self.current_ipv4_address = my_ip_v4
                LOG.info(_('Found current {t} address {a}.').format(t='IPv4', a=my_ip_v4))
            except ValueError as e:
                msg = _('Address {a!r} seems not to be a valid {w} address: {e}').format(
                    a=current_address_v4, w='IPv4', e=e)
                LOG.error(msg)
        else:
            LOG.error(_('Got no public {} address.').format('IPv4'))
        self.current_ipv4_address = my_ip_v4

        self.current_ipv6_address = None
        current_address_v6 = self.get_my_ipv(6)
        my_ip_v6 = None
        if current_address_v6:
            try:
                my_ip_v6 = ipaddress.ip_address(current_address_v6)
                self.current_ipv6_address = my_ip_v6
                LOG.info(_('Found current {t} address {a}.').format(t='IPv6', a=my_ip_v6))
            except ValueError as e:
                msg = _('Address {a!r} seems not to be a valid {w} address: {e}').format(
                    a=current_address_v6, w='IPv6', e=e)
                LOG.error(msg)
        else:
            LOG.error(_('Got no public {} address.').format('IPv5'))
        self.current_ipv6_address = my_ip_v6

        if not self.config.all_domains:
            for domain in self.config.domains:
                addresses = self.resolve_address(domain)
                self.cur_resolved_addresses[domain] = addresses
        LOG.info(_('Currently configured dynamic addresses:') + '\n' + pp(
            self.cur_resolved_addresses))

    # -------------------------------------------------------------------------
    def update_domain(self, domain):
        """Update an IPv4 addresses of the given domain."""
        self.empty_line()
        LOG.debug(_('Checking the need for updating the given domain {!r}.').format(domain))

        do_update = False
        if self.config.protocol in ('any', 'ipv4'):
            if self.current_ipv4_address:
                if self.current_ipv4_address not in self.cur_resolved_addresses[domain]:
                    do_update = True
            else:
                for addr in self.cur_resolved_addresses[domain]:
                    if addr.version == 4:
                        do_update = True

        if self.config.protocol in ('any', 'ipv6'):
            if self.current_ipv6_address:
                if self.current_ipv6_address not in self.cur_resolved_addresses[domain]:
                    do_update = True
            else:
                for addr in self.cur_resolved_addresses[domain]:
                    if addr.version == 6:
                        do_update = True

        if not do_update:
            if self.force:
                LOG.info(_(
                    'Updating the DDNS records of domain {!r}, although if they seems not '
                    'to be changed.').format(domain))
            else:
                LOG.info(_('Update of domain {!r} is not necessary.').format(domain))
                return
        else:
            LOG.info(_('Updating the DDNS records of domain {!r}.').format(domain))

        url = self.config.upd_url

        args = []
        args_out = []

        arg = 'user=' + quote(self.config.ddns_user)
        args.append(arg)
        args_out.append(arg)

        arg = 'pwd=' + quote(self.config.ddns_pwd)
        args.append(arg)
        args_out.append('pwd=******')

        arg = 'host=' + quote(domain)
        args.append(arg)
        args_out.append(arg)

        if self.config.protocol in ('any', 'ipv4') and self.current_ipv4_address:
            arg = 'ip=' + quote(str(self.current_ipv4_address))
            args.append(arg)
            args_out.append(arg)

        if self.config.protocol in ('any', 'ipv6') and self.current_ipv6_address:
            arg = 'ip6=' + quote(str(self.current_ipv6_address))
            args.append(arg)
            args_out.append(arg)

        if self.config.with_mx:
            args.append('mx=1')
            args.append(arg)
            args_out.append(arg)

        url_out = url + '?' + '&'.join(args_out)
        url += '?' + '&'.join(args)
        LOG.debug('Update-URL: {}'.format(url_out))
        # LOG.debug('Update-URL: {}'.format(url))

        if self.simulate:
            LOG.debug(_('Simulation mode, update of domain {!r} will not be sended.').format(
                domain))
            return True

        try:
            self.perform_request(url, return_json=False)
        except DdnsAppError as e:
            LOG.error(str(e))
            return None

        return True

    # -------------------------------------------------------------------------
    def do_update_ipv4(self):
        """Update an IPv4 address entry."""
        last_address = self.get_ipv4_cache()
        if last_address:
            LOG.debug(_('Last {w} address: {a!r}.').format(w='IPv4', a=str(last_address)))
        else:
            LOG.debug(_('Did not found a last {} address.').format('IPv4'))
        current_address = self.get_my_ipv(4)
        if not current_address:
            LOG.error(_('Got no public IPv4 address.'))
            return
        try:
            my_ip = ipaddress.ip_address(current_address)
        except ValueError as e:
            msg = _('Address {a!r} seems not to be a valid {w} address: {e}').format(
                a=current_address, w='IP', e=e)
            LOG.error(msg)
            return
        if my_ip.version != 4:
            msg = _('Address {a!r} seems not to be a valid {w} address.').format(
                a=current_address, w='IPv4')
            LOG.error(msg)
            return

        LOG.debug(_('Current {w} address is {a!r}.').format(w='IPv4', a=str(my_ip)))

        if last_address == my_ip:
            msg = _(
                'The public {w} address {a!r} seems not to be changed since '
                'the last update.').format(w='IPv4', a=str(last_address))
            LOG.info(msg)
            if not self.force:
                return

        self.do_update(my_ip, 4)
        self.write_ipv4_cache(my_ip)

    # -------------------------------------------------------------------------
    def do_update_ipv6(self):
        """Update an IPv6 address entry."""
        last_address = self.get_ipv6_cache()
        if last_address:
            LOG.debug(_('Last {w} address: {a!r}.').format(w='IPv6', a=str(last_address)))
        else:
            LOG.debug(_('Did not found a last {} address.').format('IPv6'))
        current_address = self.get_my_ipv(6)
        if not current_address:
            LOG.error(_('Got no public IPv6 address.'))
            return
        try:
            my_ip = ipaddress.ip_address(current_address)
        except ValueError as e:
            msg = _('Address {a!r} seems not to be a valid {w} address: {e}').format(
                a=current_address, w='IP', e=e)
            LOG.error(msg)
            return
        if my_ip.version != 6:
            msg = _('Address {a!r} seems not to be a valid {w} address.').format(
                a=current_address, w='IPv6')
            LOG.error(msg)
            return

        LOG.debug(_('Current {w} address is {a!r}.').format(w='IPv6', a=str(my_ip)))

        if last_address == my_ip:
            msg = _(
                'The public {w} address {a!r} seems not to be changed since '
                'the last update.').format(w='IPv6', a=str(last_address))
            LOG.info(msg)
            if not self.force:
                return

        self.do_update(my_ip, 6)
        self.write_ipv6_cache(my_ip)

    # -------------------------------------------------------------------------
    def do_update(self, my_ip, protocol):
        """Execute the update."""
        msg = _('Updating DNS records to IPv{p} address {a!r} ...').format(
            p=protocol, a=str(my_ip))
        LOG.info(msg)

        url = self.config.upd_ipv4_url
        if protocol == 6:
            url = self.config.upd_ipv6_url

        args = []

        arg = 'user=' + quote(self.config.ddns_user)
        args.append(arg)

        arg = 'pwd=' + quote(self.config.ddns_pwd)
        args.append(arg)

        if self.config.all_domains:
            arg = 'host=all'
            args.append(arg)
        else:
            domains = ','.join(map(quote, self.config.domains))
            arg = 'host=' + domains
            args.append(arg)

        if self.config.with_mx:
            args.append('mx=1')

        url += '?' + '&'.join(args)
        LOG.debug('Update-URL: {}'.format(url))

        if self.simulate:
            LOG.debug('Simulation mode, update will not be sended.')
            return True


# =============================================================================
if __name__ == '__main__':

    pass

# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 list
