# -*- coding: utf-8 -*-
from decimal import Decimal
import random
from statistics import mean

from django.test import TestCase, SimpleTestCase

from . import factories
from ..utils import (calculate_aqhi, append_aqhi_field, reduce_to_average_in_hours, reduce_to_one_record_dict)
from .. import models
from . import utils as test_utils


def build_records_with_hour_range_and_random_field_value(city, start, end, field):
    data_list = []
    records = []
    count = end - start + 1
    for i in range(start, start + count):
        dtm = test_utils.random_datetime(i)
        random_data = random.randint(0, 100)
        data_list.append(random_data)
        records.append(factories.CityRecordFactory.build(city=city, update_dtm=dtm, **{field: Decimal(random_data)}))

    return records, data_list


def get_decimal_mean(num_list):
    return Decimal(str(round(mean(num_list), models.POLL_DECIMAL_PLACES)))


class TestCalcAqhi(TestCase):
    def test_create_records(self):
        pass
        """
        for i in range(3):
            print(factories.CityRecordFactory().aqhi)
            print(factories.StationRecordFactory().aqhi)
        """


class ReduceToAverageTestCase(TestCase):

    def setUp(self):
        self.city = factories.CityFactory()

    def test_create_rec(self):
        records, data = build_records_with_hour_range_and_random_field_value(self.city, 1, 2, 'no2')
        self.assertEqual(len(records), 2)
        self.assertEqual(
            [rec.no2 for rec in records],
            data
        )

    def test_fields(self):
        records = [factories.CityRecordFactory()]
        reduced = reduce_to_average_in_hours(records, 1, fields=['so2', 'pm2_5'])
        self.assertEqual(len(reduced), 1)
        self.assertEqual(set(reduced[0].keys()), {'so2', 'pm2_5', 'update_dtm'})

    def test_with_exact_two_days(self):
        first_day_records, first_day_data = \
            build_records_with_hour_range_and_random_field_value(self.city, 1, 24, 'no2')
        second_day_records, second_day_data = \
            build_records_with_hour_range_and_random_field_value(self.city, 25, 48, 'no2')

        reduced = reduce_to_average_in_hours(first_day_records + second_day_records, 24, 'no2')
        self.assertEqual(
            len(reduced),
            2
        )
        self.assertEqual(reduced[0]['no2'], get_decimal_mean(second_day_data))
        self.assertEqual(reduced[1]['no2'], get_decimal_mean(first_day_data))
        self.assertEqual(
            reduced[0]['update_dtm'],
            second_day_records[-1].update_dtm
        )
        self.assertEqual(
            reduced[1]['update_dtm'],
            first_day_records[-1].update_dtm
        )

    def test_with_not_enough_hours(self):
        records, data = build_records_with_hour_range_and_random_field_value(self.city, 1, 3, 'no2')
        self.assertEqual(
            reduce_to_average_in_hours(records, 4),
            []
        )

    def test_with_exact_one_period(self):
        records, data = build_records_with_hour_range_and_random_field_value(self.city, 1, 3, 'pm10')
        reduced = reduce_to_average_in_hours(records, 3, fields='pm10')
        self.assertEqual(len(reduced), 1)
        self.assertEqual(
            reduced[0]['pm10'],
            get_decimal_mean(data)
        )
        self.assertEqual(
            reduced[0]['update_dtm'],
            records[-1].update_dtm
        )

    def test_one_period_with_extra_hours(self):
        records, data = build_records_with_hour_range_and_random_field_value(self.city, 1, 4, 'co')
        reduced = reduce_to_average_in_hours(records, 3, fields='co')
        self.assertEqual(len(reduced), 1)
        self.assertEqual(
            reduced[0]['co'],
            get_decimal_mean(data[-3:])
        )
        self.assertEqual(
            reduced[0]['update_dtm'],
            records[-1].update_dtm
        )


class ReduceToOneRecordTestCase(TestCase):

    def setUp(self):
        self.city = factories.CityFactory()

    def test_without_absent_data(self):
        records, data = build_records_with_hour_range_and_random_field_value(self.city, 1, 24, 'no2')
        reduced = reduce_to_one_record_dict(records, ['no2'])
        self.assertEqual(reduced['no2'], get_decimal_mean(data))

    def test_with_absent_data(self):
        records, data = build_records_with_hour_range_and_random_field_value(self.city, 1, 24, 'so2')

        absent_index = random.randrange(0, len(data))
        records[absent_index].so2 = None
        del data[absent_index]

        reduced = reduce_to_one_record_dict(records, ['so2'])
        self.assertEqual(set(reduced.keys()), {'so2'})
        self.assertEqual(reduced['so2'], get_decimal_mean(data))

    def test_default(self):

        def default_value(_, __):
            return Decimal(1)

        records, data = build_records_with_hour_range_and_random_field_value(self.city, 1, 24, 'aqi')

        absent_index = random.randrange(0, len(data))
        records[absent_index].aqi = None
        data[absent_index] = 1

        reduced = reduce_to_one_record_dict(records, ['aqi'], default=default_value)
        self.assertEqual(set(reduced.keys()), {'aqi'})
        self.assertEqual(reduced['aqi'], get_decimal_mean(data))


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
