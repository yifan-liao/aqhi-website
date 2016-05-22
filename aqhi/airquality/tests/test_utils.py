# -*- coding: utf-8 -*-
from decimal import Decimal

from django.test import TestCase, SimpleTestCase

from . import factories
from ..utils import (calculate_aqhi, append_aqhi_field)


class TestCalcAqhi(TestCase):
    def test_create_records(self):
        pass
        """
        for i in range(3):
            print(factories.CityRecordFactory().aqhi)
            print(factories.StationRecordFactory().aqhi)
        """


class TestAppendAqhiField(SimpleTestCase):
    def test_append(self):
        processed_dict = {
            'city': {'aqi': Decimal('48'),
                     'area_cn': '北京',
                     'co': Decimal('0.35'),
                     'no2': Decimal('36'),
                     'o3': Decimal('43'),
                     'o3_8h': Decimal('44'),
                     'pm10': Decimal('47'),
                     'pm2_5': Decimal('24'),
                     'primary_pollutant': '',
                     'quality': 'E',
                     'so2': Decimal('3')},
            'stations': {'万寿西宫': {'aqi': Decimal('26'),
                                  'co': Decimal('0.4'),
                                  'no2': Decimal('39'),
                                  'o3': Decimal('45'),
                                  'o3_8h': Decimal('44'),
                                  'pm10': None,
                                  'pm2_5': Decimal('18'),
                                  'primary_pollutant': '',
                                  'quality': 'E',
                                  'so2': Decimal('2')},
                         }
        }

        result = append_aqhi_field(processed_dict)
        self.assertEqual(
            result['city']['aqhi'],
            Decimal('1.9008')
        )
        self.assertEqual(
            result['stations']['万寿西宫']['aqhi'],
            None
        )
