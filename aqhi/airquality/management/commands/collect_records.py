# -*- coding: utf-8 -*-
import getpass
import re
import os.path
import pprint

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from aqhi.airquality.utils import get_ssh_client, get_html_files_from_dir
from aqhi.airquality import extractors, utils
from aqhi.airquality.extractors import ssh_exception
from aqhi.airquality.models import create_city_record


class Command(BaseCommand):

    help = "Collect air quality data from html files stored either locally or through shh and" \
           "save them in database. " \
           "Corresponding City and Station instances must exist in database."

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

        # Collect any error info for each file
        errors = []
        # Collect update datetime for each successful creation classified by city
        success = {}
        try:
            with transaction.atomic():
                for file_name, content in get_html_files_from_dir(pages_dir, client, city_names=options['city']):
                    info_dict = utils.append_extra_fileds(
                        extractors.process_parsed_dict(
                            extractors.parse_info_dict(
                                extractors.extract_info(content)
                            )
                        )
                    )
                    name_en = re.search(r'([a-z]+)\.html', file_name).group(1)
                    info_dict['city']['area_en'] = name_en

                    rel_path = os.path.relpath(file_name, pages_dir)

                    result = create_city_record(info_dict)
                    if result['success'] == 0:
                        del result['success']
                        result['file'] = rel_path
                        result['info_dict'] = info_dict
                        errors.append(result)
                    else:
                        if name_en not in success:
                            success[name_en] = []

                        record = result['info']
                        success[name_en].append(record.update_dtm)
        except Exception as e:
            self.stderr.write('Exception raised from {}: {}'.format(file_name, repr(e)))
            raise e

        error_num = len(errors)
        success_num_by_city = dict(map(lambda item: (item[0], len(item[1])), success))
        success_num = sum(success_num_by_city.values())

        self.stdout.write('Successfully collect {} city records.'.format(success_num))
        for city, num in success_num_by_city.items():
            self.stdout.write('{}: {}'.format(city, num))

        self.stdout.write('Fail to create {} city records.'.format(error_num))
        for error in errors:
            self.stdout.write('file: {}, type: {}, info: {}'.format(
                error['file'], error['error_type'], error['info']
            ))
            if error['error_type'] in {'ValidationError' or 'ValueError'}:
                self.stdout.write('{}'.format(pprint.pformat(error['info_dict'])))
