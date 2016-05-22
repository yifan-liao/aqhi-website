# -*- coding: utf-8 -*-
import os
import re
import pprint
import getpass

from django.core.management.base import BaseCommand, CommandError

from aqhi.airquality.utils import get_ssh_client, get_html_files_from_dir
from aqhi.airquality import extractors
from aqhi.airquality.extractors import ssh_exception


class Command(BaseCommand):
    help = """Print counting result for raw info just crawled from web pages. \n
           Automatically find *.html files recursively."""

    def add_arguments(self, parser):
        parser.add_argument('pages_dir', nargs='?',
                            help='the path(s) of the directory containing web pages.'
                                 'If ssh is used, it should be in format: [user@]hostname:path/to/dir.'
                                 'If no username is provided, then it will try to get current system username.')
        ssh_group = parser.add_argument_group('SSH', 'options for using ssh')
        ssh_group.add_argument('--ssh', action='store_true',
                               help='whether to access pages_dir through ssh')
        ssh_group.add_argument('-E', nargs='?', metavar='ssh_log_file',
                               help='ssh log file, no logging by default')
        ssh_group.add_argument('-p', '--port', type=int, default=22,
                               help='ssh port')
        ssh_group.add_argument('-P', '--password',
                               help="ssh user's password")
        ssh_group.add_argument('-o', '--output', default='freq.txt',
                               help="file to save the frequency dictionary")

    def handle(self, *args, **options):

        pages_dir = options['pages_dir']
        client = None

        if options['ssh']:
            # Use sftp to access file
            logging_file = options['E']
            if logging_file:
                logging_file = os.path.expanduser(logging_file)

            port = options['port']
            # get hostname
            username = ''
            if pages_dir.find(':') > 0:
                hostname, pages_dir = pages_dir.split(':')
                if hostname.find('@') >= 0:
                    username, hostname = hostname.split('@')
            else:
                hostname = input('Hostname: ')
            if len(hostname) == 0:
                raise CommandError('*** Hostname required.')

            # get username
            if username == '':
                username = getpass.getuser()

            # get password
            password = options['password']

            # connect
            try:
                client = get_ssh_client(hostname, username, password, port, log_file=logging_file)
            except ssh_exception.PasswordRequiredException:
                raise CommandError('Password is required.')
            except ssh_exception.AuthenticationException:
                raise CommandError('Authentication failed.')
            except ssh_exception.ServerNotKnown:
                raise CommandError('Unknown server.')
            except ssh_exception.ConnectionTimeOut:
                raise CommandError('Connection timed out.')

        # output file
        out_file = options['output']
        out_file = os.path.expanduser(out_file)

        empty_cities = []
        total = [0]

        def gen_info_dict():
            for name, content in get_html_files_from_dir(pages_dir, client):
                city_name = re.search(r'([a-z]+)\.html', name).group(1)
                info_dict = extractors.extract_info(content)
                total[0] += 1
                if not info_dict[list(info_dict.keys())[0]]:
                    empty_cities.append(city_name)
                    continue
                yield info_dict

        freq_dict = extractors.calc_freq(gen_info_dict())

        # Make frequency dictionary more readable
        freq_dict = extractors.aggregate_keys_with_one_freq(freq_dict, 5)

        with open(out_file, 'w') as out:
            out.write(pprint.pformat(freq_dict, indent=2, compact=True))

        if empty_cities:
            self.stdout.write('Empty cities are:')
            self.stdout.write(pprint.pformat(empty_cities, indent=2, compact=True))
        else:
            self.stdout.write('No empty cities.')

        self.stdout.write(self.style.SUCCESS('Successfully count the frequency of total {} pages.'.format(total[0])))

        if client:
            client.close()
