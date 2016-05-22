# -*- coding: utf-8 -*-
import os
import re
from decimal import Decimal
from functools import partial

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from aqhi.airquality.models import Station, City


def add_coord_to_station_by_name(city_name_cn, station_name_cn, lng, lat, override=False):
    station = Station.objects.filter(city__name_cn=city_name_cn, name_cn=station_name_cn)
    if not station.exists():
        raise CommandError('Station not found: {}, {}.'.format(station_name_cn, city_name_cn))

    station = station[0]
    old_lng = station.longitude
    if (old_lng and override) or not old_lng:
        station.longitude = Decimal(lng)

    old_lat = station.latitude
    if (old_lat and override) or not old_lat:
        station.latitude = Decimal(lat)

    station.full_clean()
    station.save()

    return station


def add_coord_to_city_by_name(city_name_cn, lng, lat, override=False):
    city = City.objects.filter(name_cn=city_name_cn)
    if not city.exists():
        raise CommandError('City not found: {}.'.format(city_name_cn))
    if len(city) > 1:
        raise CommandError('Duplicate cities not found: {}.'.format(city_name_cn))

    city = city[0]
    old_lng = city.longitude
    if (old_lng and override) or not old_lng:
        city.longitude = Decimal(lng)

    old_lat = city.latitude
    if (old_lat and override) or not old_lat:
        city.latitude = Decimal(lat)

    city.full_clean()
    city.save()

    return city


class Command(BaseCommand):

    help = "Add longitude and latitude data to existing Stations or Cities from file."

    def add_arguments(self, parser):
        parser.add_argument('type', choices=['station', 'city'])
        parser.add_argument('file',
                            help="Text file containing station or city coordinates data with the format of:"
                                 "CITY_CN_NAME STATION_NAME LATITUDE LONGITUDE or "
                                 "CITY_CN_NAME LATITUDE LONGITUDE")
        parser.add_argument('--override', action='store_true',
                            help="whether to force override existing data")

    def handle(self, *args, **options):
        station_file_path = options['file']
        station_file_path = os.path.expanduser(station_file_path)

        data_rows = []
        with open(station_file_path) as f:
            for line in f:
                frags = re.split(r'\s+', line)

                # First, city cn name
                city_name_cn = frags[0]
                if city_name_cn[-1] == '市':
                    city_name_cn = city_name_cn[:-1]

                if options['type'] == 'station':
                    # Second, station cn name
                    # Third is lat
                    # Last is lng
                    data_rows.append([city_name_cn, frags[1], frags[2], frags[3]])
                else:
                    data_rows.append([city_name_cn, frags[1], frags[2]])

        headers = (
            ['city_name_cn', 'station_name_cn', 'lat', 'lng']
            if options['type'] == 'station'
            else ['city_name_cn', 'lat', 'lng']
        )
        data_rows = list(map(
            dict,
            map(partial(zip, headers), data_rows)
        ))

        with transaction.atomic():
            add_func = (
                add_coord_to_station_by_name
                if options['type'] == 'station'
                else add_coord_to_city_by_name
            )
            for row in data_rows:
                add_func(override=options['override'], **row)
