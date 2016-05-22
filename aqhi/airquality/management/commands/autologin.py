import argparse
import logging
import os

from django.core.management.base import BaseCommand

from aqhi.airquality.utils import buptnet


class Command(BaseCommand):
    help = "Try to log on into campus network."

    def add_arguments(self, parser):
        parser.add_argument('username',
                            help='campus network username')
        parser.add_argument('password',
                            help='campus network password')
        parser.add_argument('-l', '--log',
                            help='log file path')
        parser.add_argument('-p', '--parents', action='store_true',
                            help="make log file parents directories as needed")

    def handle(self, *args, **options):
        # logging
        logger = logging.getLogger('autologin')
        log_file = options['log']
        if log_file:
            log_file_dir = os.path.dirname(log_file)
            if log_file_dir != '' and not os.path.exists(log_file_dir):
                if options['parents']:
                    os.makedirs(log_file_dir)
                else:
                    raise argparse.ArgumentError(
                        None,
                        "Log file's directory does not exist. "
                        "You can use set -p flag to create necessary directories as needed."
                    )

            formatter = logging.Formatter(
                fmt='%(asctime)s [%(name)s] %(levelname)s: %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S',
            )
            log_file_handler = logging.FileHandler(log_file)
            log_file_handler.setFormatter(formatter)
            logger.setLevel(logging.INFO)
            logger.addHandler(log_file_handler)
        else:
            formatter = logging.Formatter('%(name)-12s %(levelname)-8s %(message)s')
            console = logging.StreamHandler()
            console.setFormatter(formatter)
            logger.setLevel(logging.ERROR)
            logger.addHandler(console)

        # check network status
        buptnet.autologin(options['username'], options['password'], logger)



