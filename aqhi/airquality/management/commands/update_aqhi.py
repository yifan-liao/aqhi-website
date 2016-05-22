# -*- coding: utf-8 -*-
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from aqhi.airquality import utils
from aqhi.airquality import models


def update_record(record, override=False):
    if record.pm10 and record.no2:
        if record.aqhi is None or override:
            record.aqhi = utils.calculate_aqhi_in_decimal(record.pm10, record.no2, models.POLL_DECIMAL_PLACES)
            record.save()
            return True
    return False


class Command(BaseCommand):
    help = """Update current database: calculate aqhi to replace null values. \n
           Ignore existing aqhi by default."""

    def add_arguments(self, parser):
        parser.add_argument('--override', action='store_true',
                            help='whether to re-calculate and override the original value')

    def handle(self, *args, **options):
        override = options['override']
        count = 0
        with transaction.atomic():
            for city_record in models.CityRecord.objects.all():
                if update_record(city_record, override):
                    count += 1

        self.stdout.write('Total {} city records updated.'.format(count) if count else 'No city records updated.')

        count = 0
        with transaction.atomic():
            for station_record in models.StationRecord.objects.all():
                if update_record(station_record, override):
                    count += 1
        self.stdout.write('Total {} station records updated.'.format(count) if count else 'No station records updated.')
