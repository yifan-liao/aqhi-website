import io
from decimal import Decimal

from django.test import TestCase
from django.core.management import call_command

from aqhi.airquality.management.commands.add_coordinates import add_coord_to_station_by_name
from . import factories
from .. import models


class TestPrintFreq(TestCase):

    def test_cmd_output(self):
        out = io.StringIO()
        call_command('print_freq',
                     ssh=True, pages_dir="yifan@10.103.248.78:/media/Documents/pm25in-pages/2016-05-06-13-30-01",
                     password='Ub1881200', stdout=out)
        print(out.getvalue())


class TestAddCoordinates(TestCase):

    def test_add_coord_with_coord_none(self):
        station = factories.StationFactory(longitude=None, latitude=None)
        city = station.city

        station = add_coord_to_station_by_name(city.name_cn, station.name_cn, '10.10', '12.321')
        self.assertEqual(station.longitude, Decimal('10.10'))
        self.assertEqual(station.latitude, Decimal('12.321'))

    def test_add_coord_with_existing_coord(self):
        station = factories.StationFactory(latitude=None)
        city = station.city

        old_lng = station.longitude
        station = add_coord_to_station_by_name(
            city.name_cn, station.name_cn, old_lng + Decimal('1'), '12.321'
        )
        self.assertEqual(station.longitude, old_lng)
        self.assertEqual(station.latitude, Decimal('12.321'))

        old_lng = station.longitude
        old_lat = station.latitude
        station = add_coord_to_station_by_name(
            city.name_cn, station.name_cn, old_lng + Decimal('1'), old_lat + Decimal('1'),
            override=True
        )
        self.assertEqual(station.longitude, old_lng + Decimal('1'))
        self.assertEqual(station.latitude, old_lat + Decimal('1'))
