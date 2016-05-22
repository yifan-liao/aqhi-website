# -*- coding: utf-8 -*-
import getpass
import re
import os
import pprint

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.core.exceptions import ValidationError

from aqhi.airquality.utils import get_ssh_client, get_html_files_from_dir
from aqhi.airquality import extractors
from aqhi.airquality.extractors import ssh_exception
from aqhi.airquality.models import City, Station


class Command(BaseCommand):

    help = "Collect city and station names from html files either locally or through ssh " \
           "and save them in database." \
           "City and Station instances will be created as needed."

    def add_arguments(self, parser):
        parser.add_argument('pages_dir', nargs='?',
                            help='the path(s) of the directory containing web pages.'
                                 'If ssh is used, it should be in format: [user@]hostname:path/to/dir.'
                                 'If no username is provided, then it will try to get current system username.')
        parser.add_argument('--city', action='append',
                            help='the city name to collect, file name without .html is the city name')
        ssh_group = parser.add_argument_group('SSH', 'options for using ssh')
        ssh_group.add_argument('--ssh', action='store_true',
                               help='whether to access pages_dir through ssh')
        ssh_group.add_argument('-E', nargs='?', metavar='ssh_log_file',
                               help='ssh log file, no logging by default')
        ssh_group.add_argument('-p', '--port', type=int, default=22,
                               help='ssh port')
        ssh_group.add_argument('-P', '--password',
                               help="ssh user's password")

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

        station_duplicates = {}
        city_duplicates = {}
        total_city = 0
        total_station = 0

        try:
            with transaction.atomic():
                for file_name, content in get_html_files_from_dir(pages_dir, client, city_names=options['city']):
                    total_city += 1
                    info_dict = extractors.process_parsed_dict(
                        extractors.parse_info_dict(
                            extractors.extract_info(content)
                        )
                    )
                    name_en = re.search(r'([a-z]+)\.html', file_name).group(1)
                    name_cn = info_dict['city']['area_cn']
                    try:
                        city = City.objects.validate_and_create(name_en=name_en, name_cn=name_cn)
                    except ValidationError:
                        self.count_duplicates(city_duplicates, name_en)
                        continue

                    for station_name in info_dict['stations']:
                        total_station += 1
                        try:
                            Station.objects.validate_and_create(name_cn=station_name, city=city)
                        except ValidationError:
                            self.count_duplicates(station_duplicates, (name_en, station_name))
        except Exception as e:
            self.stderr.write('Exception raised from {}: {}'.format(file_name, repr(e)))
            raise e

        # print result
        self.stdout.write('Total cities scanned: {}. {} new city info is saved.'.format(
            total_city,
            total_city - self.calc_duplicates(city_duplicates)
        ))
        self.stdout.write('Duplicate cities are: {}'.format(pprint.pformat(city_duplicates, indent=4)))
        self.stdout.write('Total stations scanned: {}. {} new station info is saved.'.format(
            total_station,
            total_station - self.calc_duplicates(station_duplicates)
        ))
        self.stdout.write('Duplicate stations are: {}'.format(pprint.pformat(station_duplicates, indent=4)))

        if client:
            client.close()

    @classmethod
    def count_duplicates(cls, dup_dict, name):
        if name in dup_dict:
            dup_dict[name] += 1
        else:
            dup_dict[name] = 1

    @classmethod
    def calc_duplicates(cls, dup_dict):
        return sum(dup_dict.values())
