# -*- coding: utf-8 -*-
from decimal import Decimal
import random
from statistics import mean

from django.test import TestCase, SimpleTestCase

from . import factories
from ..utils import (
    calculate_aqhi, reduce_to_average_in_hours, reduce_to_one_record_dict
)
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
    @staticmethod
    def get_aqhi_from_data_lists(data):
        fields = ['pm10_3h', 'pm25_3h', 'so2_3h', 'no2_3h', 'o3_3h']
        avg_data = [mean(l) for l in data]
        return calculate_aqhi(**dict(zip(fields, avg_data)))

    def test_calculate_aqhi(self):
        data = [
            [[605, 579, 592], [236, 296, 238], [7, 7, 7], [12, 11, 10], [162, 168, 169], 11],
            [[426, 473, 495], [133, 141, 140], [2, 2, 2], [9, 8, 9], [86, 93, 93], 10],
            [[332, 234, 248], [92, 58, 63], [11, 11, 12], [10, 13, 9], [112, 106, 108], 8],
            [[61, 65, 65], [38, 37, 36], [16, 15, 13], [8, 10, 15], [202, 204, 192], 8],
            [[74, 77, 85], [51, 54, 59], [13, 15, 13], [12, 17, 14], [201, 202, 223], 8],
            [[87, 98, 125], [71, 78, 78], [19, 17, 15], [24, 27, 27], [83, 88, 92], 5],
            [[90, 102, 106], [40, 42, 42], [31, 34, 35], [4, 5, 5], [49, 47, 46], 4],
            [[58, 54, 44], [8, 2, 2], [3, 3, 3], [3, 2, 2], [100, 104, 107], 4],
            [[55, 46, 44], [16, 19, 21], [12, 13, 13], [5, 5, 5], [73, 74, 72], 3],
            [[16, 12, 10], [11, 9, 10], [6, 6, 7], [2, 1, 1], [65, 63, 62], 3],
            [[4, 4, 4], [2, 1, 1], [6, 7, 6], [8, 10, 7], [15, 46, 43], 2],
            [[4, 8, 16], [2, 5, 11], [5, 5, 5], [5, 6, 4], [14, 14, 11], 1],
        ]
        for row in data:
            self.assertEqual(self.get_aqhi_from_data_lists(row[:-1]), row[-1])


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

    def test_with_all_values_of_a_field_are_none(self):
        records, data = build_records_with_hour_range_and_random_field_value(self.city, 1, 4, 'pm2_5')
        for i in range(4):
            records[i].pm2_5 = None
        reduced = reduce_to_average_in_hours(records, 4, fields='pm2_5')
        self.assertIsNone(reduced[0]['pm2_5'])


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

    def test_with_all_values_of_a_field_are_none(self):
        records, data = build_records_with_hour_range_and_random_field_value(self.city, 1, 2, 'no2')
        records[0].no2 = None
        records[1].no2 = None

        self.assertIsNone(reduce_to_one_record_dict(records, ['no2'])['no2'])

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

