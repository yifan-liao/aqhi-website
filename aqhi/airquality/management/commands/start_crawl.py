from datetime import datetime
import os
import logging
import argparse
import pytz

from scrapy.signals import engine_started, engine_stopped
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from pydispatch import dispatcher
from django.core.management.base import BaseCommand

from aqhi.airquality.crawler.pm25in.spiders.pm25in_spider import AQISpider
from aqhi.airquality.utils import buptnet


def positive_integer(string):
    try:
        value = int(string)
        if value < 0:
            raise ValueError()
    except ValueError:
        raise argparse.ArgumentTypeError("'{}' is not a positive integer.".format(string))
    return value


class Command(BaseCommand):
    help = 'Crawl all the city pages from pm25.in. Automatically login before crawling.'

    def add_arguments(self, parser):
        parser.add_argument('dest',
                            help='The parent directory to save the pages. '
                                 'If -s is not set, then '
                                 'web pages will be saved in a directory under it named by timestamp.')
        parser.add_argument('--username',
                            help='campus network username')
        parser.add_argument('--password',
                            help='campus network password')
        parser.add_argument('-s', '--absolute', action='store_true',
                            help='a flag showing whether dest is absolute(disable auto-generating subdirectory)')
        parser.add_argument('-p', '--parents', action='store_true',
                            help="make dest and log's parents directories as needed")
        parser.add_argument('-l', '--log',
                            help="log file path which defaults to 'log.txt' under dest")
        parser.add_argument('--page-num', type=positive_integer, default=0,
                            help='Set a max number of pages to crawl. Default to 0 represents no limit. '
                                 '(for debugging)')
        parser.add_argument('--not-parse', action='store_false',
                            help='whether to parse crawled pagees and save data to db.')

        return parser

    def handle(self, *args, **options):
        # Decide save path
        root_dir = options['dest']
        root_dir = os.path.expanduser(root_dir)
        if root_dir != '' and not os.path.exists(root_dir):
            if not options['parents']:
                raise argparse.ArgumentError(
                    None,
                    "dest's directory does not exist. "
                    "You can use set -p flag to create necessary directories as needed."
                )
            else:
                os.makedirs(root_dir)
        if not options['absolute']:
            root_dir = os.path.join(root_dir, datetime.now(pytz.utc).astimezone().strftime("%Y-%m-%d-%H-%M-%S"))
            os.makedirs(root_dir)

        # Decide logging path
        log_file_path = options['log']
        if not log_file_path:
            log_file_path = os.path.join(root_dir, 'log.txt')
        else:
            log_file_path = os.path.expanduser(log_file_path)
            log_file_dir = os.path.dirname(log_file_path)
            if log_file_dir != '' and not os.path.exists(log_file_dir):
                if not options['parents']:
                    raise argparse.ArgumentError(
                        None,
                        "log files's directory does not exist. "
                        "You can use set -p flag to create necessary directories as needed."
                    )
                else:
                    os.makedirs(log_file_dir)

        # Setup logger for autologin
        log_file_handler = logging.FileHandler(log_file_path)
        formatter = logging.Formatter(
            fmt='%(asctime)s [%(name)s] %(levelname)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
        )
        log_file_handler.setFormatter(formatter)
        login_logger = logging.getLogger('autologin')
        login_logger.setLevel(logging.INFO)
        login_logger.addHandler(log_file_handler)
        # auto login
        username = options['username']
        password = options['password']
        if username is not None and password is not None:
            buptnet.autologin(username, password, login_logger)

        # Setup logger for crawler
        crawler_logger = logging.getLogger('pm25in')
        crawler_logger.setLevel(logging.INFO)
        # Redirect ERROR or higher level logging to stderr
        console = logging.StreamHandler()
        console.setLevel(logging.ERROR)
        console.setFormatter(logging.Formatter("[%(name)s] %(levelname)s: %(message)s"))
        logging.getLogger().addHandler(console)

        def engine_stopped_handler():
            crawler_logger.info("Stop crawling.")

        def engine_started_handler():
            crawler_logger.info("Start crawling.")

        dispatcher.connect(engine_started_handler, engine_started)
        dispatcher.connect(engine_stopped_handler, engine_stopped)

        proj_settings = get_project_settings()
        proj_settings.set('LOG_FILE', log_file_path)
        process = CrawlerProcess(proj_settings)
        process.crawl(
            AQISpider,
            res_dir=root_dir,
            logger=crawler_logger,
            page_num=options['page_num'],
            to_parse=options['not_parse']
        )
        process.start()
