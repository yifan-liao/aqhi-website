# -*- coding: utf-8 -*-
import os
import re
from datetime import datetime
import pytz
from decimal import Decimal

from django.test import SimpleTestCase

import aqhi.airquality.utils
from .. import extractors
from ..extractors import ssh_exception
from aqhi.airquality.tests.utils import random_datetime

dir_path = os.path.dirname(os.path.realpath(__file__))


class TestUtils(SimpleTestCase):

    def test_aggregate_keys_with_one_value(self):

        D = {
            'a': {'asd': 1, 'agds': 1, 'fgh': 1, 'two': 2},
            'b': {'two1': 2, 'two2': 2, 'two3': 2, 'three': 3},
            'c': {'asd': 1, 'agds': 1, 'fgh': 1, 'oneone': 1},
            'd': {0: {'asd': 1, 'agds': 1, 'fgh': 1, 'oneone': 1},
                  1: {'asd': 1, 'agds': 1, 'fgh': 1, 'two': 2},
                  2: {'two1': 2, 'two2': 2, 'two3': 2, 'three': 3}}
        }

        D_after = extractors.aggregate_keys_with_one_freq(D, 1)

        self.assertEqual(D_after, {
            'a': {'single_value_keys': 3, 'two': 2},
            'b': {'two1': 2, 'two2': 2, 'two3': 2, 'three': 3},
            'c': {'single_value_keys': 4},
            'd': {0: {'single_value_keys': 4},
                  1: {'single_value_keys': 3, 'two': 2},
                  2: {'two1': 2, 'two2': 2, 'two3': 2, 'three': 3}}
        })


class TestPatternFieldMappings(SimpleTestCase):

    @classmethod
    def setUpClass(cls):
        super(TestPatternFieldMappings, cls).setUpClass()
        cls.mappings = extractors.rules.consts_pattern_field_mappings

    def test_mappings(self):
        expected_mappings = {
            'AQI': 'aqi',
            'CO/1h': 'co',
            'NO2/1h': 'no2',
            'NO2二氧化氮': 'no2',
            'O3/8h': 'o3_8h',
            'PM10/1h': 'pm10',
            'SO2/1h': 'so2',
            'SO2二氧化硫': 'so2',
            '二氧化硫': 'so2',
            '一氧化碳': 'co',
            'CO一氧化碳': 'co',
            '二氧化氮': 'no2',
            '颗粒物(PM10)': 'pm10',
            'PM10可吸入颗粒物': 'pm10',
            '臭氧1小时': 'o3',
            'O3臭氧1小时平均': 'o3',
            '臭氧8小时': 'o3_8h',
            'O3臭氧8小时平均': 'o3_8h',
            '颗粒物(PM2.5)': 'pm2_5',
            'PM2.5细颗粒物': 'pm2_5',
            '细颗粒物(PM2.5)': 'pm2_5',
            '一级（优）': 'E',
            '优': 'E',
            '三级（轻度污染）': 'LP',
            '轻度污染': 'LP',
            '二级（良）': 'G',
            '良': 'G',
            '五级（重度污染）': 'HP',
            '重度污染': 'HP',
            '六级（严重污染）': 'SP',
            '严重污染': 'SP',
            '四级（中度污染）': 'MP',
            '中度污染': 'MP',
            '监测点': 'name',
            '空气质量指数类别': 'quality',
            '首要污染物': 'primary_pollutant',
            '': '',
            '->': '',
            '_': '',
            '—': '',
        }

        for string, match in expected_mappings.items():
            with self.subTest(string=string, expected_match=match):
                self.assertEqual(self.get_first_mapping(string), match)

    def get_first_mapping(self, string):
        for pattern in self.mappings:
            match = pattern.search(string)
            if match:
                return self.mappings[pattern]
        return None


class TestInfoPreprocessors(SimpleTestCase):

    def test_primary_pollutant_preprocessor(self):
        pre = extractors.rules.info_preprocessors['primary_pollutant']
        self.assertEqual(
            pre(['首要污染物： 二氧化硫,颗粒物(PM10)']),
            ['二氧化硫', '颗粒物(PM10)']
        )
        self.assertEqual(
            pre(['首要污染物：臭氧8小时,颗粒物(PM10),颗粒物(PM2.5)']),
            ['臭氧8小时', '颗粒物(PM10)', '颗粒物(PM2.5)']
        )
        self.assertEqual(
            pre(['首要污染物: 二氧化硫 颗粒物(PM10)']),
            ['二氧化硫', '颗粒物(PM10)']
        )


class TestExtractInfo(SimpleTestCase):

    @classmethod
    def setUpClass(cls):
        super(TestExtractInfo, cls).setUpClass()
        with open(os.path.join(dir_path, 'files/beijing.html')) as f:
            cls.html_string = f.read()

        with open(os.path.join(dir_path, 'files/yushuzhou.html')) as f:
            cls.html_string_single_row = f.read()

    def test_extract_from_single_html(self):
        # Test extracting info from beijing.html
        info_dict = extractors.extract_info(self.html_string)
        self.assertEqual(
            set(info_dict.keys()),
            set(extractors.rules.info_xpath_mappings.keys())
        )
        self.assertEqual(
            info_dict['city_quality_names'],
            ['AQI', 'PM2.5/1h', 'PM10/1h', 'CO/1h',
                'NO2/1h', 'O3/1h', 'O3/8h', 'SO2/1h']
        )
        self.assertEqual(
            info_dict['city_quality_values'],
            ['48', '24', '47', '0.35', '36', '43', '44', '3']
        )
        self.assertEqual(
            info_dict['area_cn'],
            ['北京'],
        )
        self.assertEqual(
            info_dict['update_dtm'],
            ['2016-05-07 08:00:00'],
        )
        self.assertEqual(
            info_dict['quality'],
            ['一级（优）'],
        )
        self.assertEqual(
            info_dict['primary_pollutant'],
            ['臭氧8小时', '颗粒物(PM10)'],
        )
        self.assertEqual(
            info_dict['station_quality_names'],
            ['监测点', 'AQI', '空气质量指数类别', '首要污染物', 'PM2.5细颗粒物', 'PM10可吸入颗粒物',
             'CO一氧化碳', 'NO2二氧化氮', 'O3臭氧1小时平均', 'O3臭氧8小时平均', 'SO2二氧化硫']
        )
        self.assertEqual(
            info_dict['station_quality_rows'][:2],
            [['万寿西宫', '26', '优', '_', '18', '_', '0.4', '39', '45', '44', '2'],
             ['定陵', '28', '优', '_', '13', '28', '0.3', '11', '65', '63', '3']
             ]
        )

        with self.subTest(msg='Test calc_freq function'):
            freq_dict = extractors.calc_freq([info_dict])
            self.assertEqual(
                freq_dict['city_quality_names'],
                dict.fromkeys(info_dict['city_quality_names'], 1)
            )

    def test_extract_from_html_with_single_station(self):
        info_dict = extractors.extract_info(self.html_string_single_row)
        self.assertEqual(
            info_dict['station_quality_rows'],
            [['玉树县结古镇', '36', '优', '_', '8', '36', '1.207', '5', '17', '44', '3']]
        )

    def test_index_error(self):
        import pprint
        with open(os.path.join(dir_path, 'files/guangzhou-index-error.html')) as f:
            html_string = f.read()

        info_dict = extractors.extract_info(self.html_string)
        pprint.pprint(info_dict)


class TestParseInfoDict(SimpleTestCase):

    @classmethod
    def setUpClass(cls):
        super(TestParseInfoDict, cls).setUpClass()
        cls.info_dict = {
            'area_cn': ['北京'],
            'city_quality_names': ['AQI', 'PM2.5/1h', 'PM10/1h', 'CO/1h', 'NO2/1h',
                                   'O3/1h', 'O3/8h', 'SO2/1h'],
            'city_quality_values': ['48', '24', '47', '0.35', '36', '43', '44', '3'],
            'primary_pollutant': [''],
            'quality': ['一级（优）'],
            'station_quality_names': ['监测点', 'AQI', '空气质量指数类别', '首要污染物', 'PM2.5细颗粒物',
                                      'PM10可吸入颗粒物', 'CO一氧化碳', 'NO2二氧化氮', 'O3臭氧1小时平均',
                                      'O3臭氧8小时平均', 'SO2二氧化硫'],
            'station_quality_rows': [['万寿西宫', '26', '优', '_', '18', '_', '0.4', '39',
                                      '45', '44', '2'],
                                     ['定陵', '28', '优', '_', '13', '28', '0.3', '11',
                                      '65', '63', '3'],
                                     ['东四', '50', '优', '_', '35', '_', '0.4', '40',
                                      '42', '44', '2'],
                                     ['天坛', '60', '良', '细颗粒物(PM2.5)', '43', '_', '0.5',
                                      '44', '46', '36', '2'],
                                     ['农展馆', '25', '优', '_', '16', '_', '0.3', '50',
                                      '36', '45', '4'],
                                     ['官园', '45', '优', '_', '17', '45', '0.4', '35',
                                      '41', '40', '4'],
                                     ['海淀区万柳', '75', '良', '颗粒物(PM10)', '24', '99',
                                      '0.4', '53', '31', '31', '2'],
                                     ['顺义新城', '48', '优', '_', '33', '_', '0.3', '34',
                                      '43', '28', '2'],
                                     ['怀柔镇', '55', '良', '颗粒物(PM10)', '31', '59', '0.2',
                                      '27', '37', '58', '2'],
                                     ['昌平镇', '57', '良', '细颗粒物(PM2.5)', '40', '41',
                                      '0.4', '51', '28', '38', '6'],
                                     ['奥体中心', '36', '优', '_', '19', '36', '0.3', '41',
                                      '34', '34', '4'],
                                     ['古城', '25', '优', '_', '6', '25', '0.3', '15',
                                      '73', '68', '3']],
            'update_dtm': ['2016-05-07 08:00:00']}

        cls.parsed_dict = {'area_cn': '北京',
                           'city_quality_names': ['aqi',
                                                  'pm2_5',
                                                  'pm10',
                                                  'co',
                                                  'no2',
                                                  'o3',
                                                  'o3_8h',
                                                  'so2'],
                           'city_quality_values': [Decimal('48'),
                                                   Decimal('24'),
                                                   Decimal('47'),
                                                   Decimal('0.35'),
                                                   Decimal('36'),
                                                   Decimal('43'),
                                                   Decimal('44'),
                                                   Decimal('3')],
                           'primary_pollutant': '',
                           'quality': 'E',
                           'station_quality_names': ['name',
                                                     'aqi',
                                                     'quality',
                                                     'primary_pollutant',
                                                     'pm2_5',
                                                     'pm10',
                                                     'co',
                                                     'no2',
                                                     'o3',
                                                     'o3_8h',
                                                     'so2'],
                           'station_quality_rows': [['万寿西宫',
                                                     Decimal('26'),
                                                     'E',
                                                     '',
                                                     Decimal('18'),
                                                     '',
                                                     Decimal('0.4'),
                                                     Decimal('39'),
                                                     Decimal('45'),
                                                     Decimal('44'),
                                                     Decimal('2')],
                                                    ['定陵',
                                                     Decimal('28'),
                                                     'E',
                                                     '',
                                                     Decimal('13'),
                                                     Decimal('28'),
                                                     Decimal('0.3'),
                                                     Decimal('11'),
                                                     Decimal('65'),
                                                     Decimal('63'),
                                                     Decimal('3')],
                                                    ['东四',
                                                     Decimal('50'),
                                                     'E',
                                                     '',
                                                     Decimal('35'),
                                                     '',
                                                     Decimal('0.4'),
                                                     Decimal('40'),
                                                     Decimal('42'),
                                                     Decimal('44'),
                                                     Decimal('2')],
                                                    ['天坛',
                                                     Decimal('60'),
                                                     'G',
                                                     'pm2_5',
                                                     Decimal('43'),
                                                     '',
                                                     Decimal('0.5'),
                                                     Decimal('44'),
                                                     Decimal('46'),
                                                     Decimal('36'),
                                                     Decimal('2')],
                                                    ['农展馆',
                                                     Decimal('25'),
                                                     'E',
                                                     '',
                                                     Decimal('16'),
                                                     '',
                                                     Decimal('0.3'),
                                                     Decimal('50'),
                                                     Decimal('36'),
                                                     Decimal('45'),
                                                     Decimal('4')],
                                                    ['官园',
                                                     Decimal('45'),
                                                     'E',
                                                     '',
                                                     Decimal('17'),
                                                     Decimal('45'),
                                                     Decimal('0.4'),
                                                     Decimal('35'),
                                                     Decimal('41'),
                                                     Decimal('40'),
                                                     Decimal('4')],
                                                    ['海淀区万柳',
                                                     Decimal('75'),
                                                     'G',
                                                     'pm10',
                                                     Decimal('24'),
                                                     Decimal('99'),
                                                     Decimal('0.4'),
                                                     Decimal('53'),
                                                     Decimal('31'),
                                                     Decimal('31'),
                                                     Decimal('2')],
                                                    ['顺义新城',
                                                     Decimal('48'),
                                                     'E',
                                                     '',
                                                     Decimal('33'),
                                                     '',
                                                     Decimal('0.3'),
                                                     Decimal('34'),
                                                     Decimal('43'),
                                                     Decimal('28'),
                                                     Decimal('2')],
                                                    ['怀柔镇',
                                                     Decimal('55'),
                                                     'G',
                                                     'pm10',
                                                     Decimal('31'),
                                                     Decimal('59'),
                                                     Decimal('0.2'),
                                                     Decimal('27'),
                                                     Decimal('37'),
                                                     Decimal('58'),
                                                     Decimal('2')],
                                                    ['昌平镇',
                                                     Decimal('57'),
                                                     'G',
                                                     'pm2_5',
                                                     Decimal('40'),
                                                     Decimal('41'),
                                                     Decimal('0.4'),
                                                     Decimal('51'),
                                                     Decimal('28'),
                                                     Decimal('38'),
                                                     Decimal('6')],
                                                    ['奥体中心',
                                                     Decimal('36'),
                                                     'E',
                                                     '',
                                                     Decimal('19'),
                                                     Decimal('36'),
                                                     Decimal('0.3'),
                                                     Decimal('41'),
                                                     Decimal('34'),
                                                     Decimal('34'),
                                                     Decimal('4')],
                                                    ['古城',
                                                     Decimal('25'),
                                                     'E',
                                                     '',
                                                     Decimal('6'),
                                                     Decimal('25'),
                                                     Decimal('0.3'),
                                                     Decimal('15'),
                                                     Decimal('73'),
                                                     Decimal('68'),
                                                     Decimal('3')]],
                           'update_dtm': datetime(2016, 5, 7, 0, 0, tzinfo=pytz.utc)}

    def test_parse_output(self):
        self.maxDiff = None
        self.assertEqual(self.parsed_dict,
                         extractors.parse_info_dict(self.info_dict))

        # Test with multiple pollutants
        mul_pol_dict = {'primary_pollutant': [
            '臭氧8小时', '颗粒物(PM10)', '颗粒物(PM2.5)']}
        self.assertEqual(
            extractors.parse_info_dict(mul_pol_dict),
            {'primary_pollutant': ['o3_8h', 'pm10', 'pm2_5']}
        )

    def test_parse_dict_with_single_station_row(self):
        info_dict = {
            'station_quality_rows': [['玉树县结古镇', '36', '优', '_', '8', '36', '1.207', '5', '17', '44', '3']]
        }
        parsed = extractors.parse_info_dict(info_dict)
        self.assertEqual(
            parsed,
            {'station_quality_rows': [['玉树县结古镇', Decimal('36'), 'E', '', Decimal('8'), Decimal('36'), Decimal('1.207'), Decimal('5'), Decimal('17'), Decimal('44'), Decimal('3')]]}
        )

    def test_parse_dict_with_single_datetime_row(self):
        dtm = random_datetime()
        info_dict = {
            'update_dtm': [dtm.astimezone(pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S')]
        }
        parsed = extractors.parse_info_dict(info_dict)
        self.assertEqual(
            parsed,
            {'update_dtm': dtm}
        )


class TestListDepth(SimpleTestCase):

    def test_main(self):
        list_depth = aqhi.airquality.utils.list_depth

        self.assertEqual(list_depth([]), 0)
        self.assertEqual(list_depth(1), 0)
        self.assertEqual(list_depth([0]), 1)
        self.assertEqual(list_depth([[0]]), 2)
        self.assertEqual(list_depth([0, [0]]), 2)
        self.assertEqual(list_depth([0, []]), 1)


class TestProcessParsedDict(SimpleTestCase):

    def setUp(self):
        self.parsed_dict = {
            'area_cn': '北京',
            'city_quality_names': ['aqi',
                                   'pm2_5',
                                   'pm10',
                                   'co',
                                   'no2',
                                   'o3',
                                   'o3_8h',
                                   'so2'],
            'city_quality_values': [Decimal('48'),
                                    Decimal('24'),
                                    Decimal('47'),
                                    Decimal('0.35'),
                                    Decimal('36'),
                                    Decimal('43'),
                                    Decimal('44'),
                                    Decimal('3')],
            'primary_pollutant': '',
            'quality': 'E',
            'station_quality_names': ['name',
                                      'aqi',
                                      'quality',
                                      'primary_pollutant',
                                      'pm2_5',
                                      'pm10',
                                      'co',
                                      'no2',
                                      'o3',
                                      'o3_8h',
                                      'so2'],
            'station_quality_rows': [['万寿西宫',
                                      Decimal('26'),
                                      'E',
                                      '',
                                      Decimal('18'),
                                      '',
                                      Decimal('0.4'),
                                      Decimal('39'),
                                      Decimal('45'),
                                      Decimal('44'),
                                      Decimal('2')],
                                     ['定陵',
                                      Decimal('28'),
                                      'E',
                                      '',
                                      Decimal('13'),
                                      Decimal('28'),
                                      Decimal('0.3'),
                                      Decimal('11'),
                                      Decimal('65'),
                                      Decimal('63'),
                                      Decimal('3')],
                                     ['东四',
                                      Decimal('50'),
                                      'E',
                                      '',
                                      Decimal('35'),
                                      '',
                                      Decimal('0.4'),
                                      Decimal('40'),
                                      Decimal('42'),
                                      Decimal('44'),
                                      Decimal('2')],
                                     ['天坛',
                                      Decimal('60'),
                                      'G',
                                      'pm2_5',
                                      Decimal('43'),
                                      '',
                                      Decimal('0.5'),
                                      Decimal('44'),
                                      Decimal('46'),
                                      Decimal('36'),
                                      Decimal('2')],
                                     ['农展馆',
                                      Decimal('25'),
                                      'E',
                                      '',
                                      Decimal('16'),
                                      '',
                                      Decimal('0.3'),
                                      Decimal('50'),
                                      Decimal('36'),
                                      Decimal('45'),
                                      Decimal('4')],
                                     ['官园',
                                      Decimal('45'),
                                      'E',
                                      '',
                                      Decimal('17'),
                                      Decimal('45'),
                                      Decimal('0.4'),
                                      Decimal('35'),
                                      Decimal('41'),
                                      Decimal('40'),
                                      Decimal('4')],
                                     ['海淀区万柳',
                                      Decimal('75'),
                                      'G',
                                      'pm10',
                                      Decimal('24'),
                                      Decimal('99'),
                                      Decimal('0.4'),
                                      Decimal('53'),
                                      Decimal('31'),
                                      Decimal('31'),
                                      Decimal('2')],
                                     ['顺义新城',
                                      Decimal('48'),
                                      'E',
                                      '',
                                      Decimal('33'),
                                      '',
                                      Decimal('0.3'),
                                      Decimal('34'),
                                      Decimal('43'),
                                      Decimal('28'),
                                      Decimal('2')],
                                     ['怀柔镇',
                                      Decimal('55'),
                                      'G',
                                      'pm10',
                                      Decimal('31'),
                                      Decimal('59'),
                                      Decimal('0.2'),
                                      Decimal('27'),
                                      Decimal('37'),
                                      Decimal('58'),
                                      Decimal('2')],
                                     ['昌平镇',
                                      Decimal('57'),
                                      'G',
                                      'pm2_5',
                                      Decimal('40'),
                                      Decimal('41'),
                                      Decimal('0.4'),
                                      Decimal('51'),
                                      Decimal('28'),
                                      Decimal('38'),
                                      Decimal('6')],
                                     ['奥体中心',
                                      Decimal('36'),
                                      'E',
                                      '',
                                      Decimal('19'),
                                      Decimal('36'),
                                      Decimal('0.3'),
                                      Decimal('41'),
                                      Decimal('34'),
                                      Decimal('34'),
                                      Decimal('4')],
                                     ['古城',
                                      Decimal('25'),
                                      'E',
                                      '',
                                      Decimal('6'),
                                      Decimal('25'),
                                      Decimal('0.3'),
                                      Decimal('15'),
                                      Decimal('73'),
                                      Decimal('68'),
                                      Decimal('3')]],
            'update_dtm': datetime(2016, 5, 7, 0, 0, tzinfo=pytz.utc)
        }

        self.expected_processed_dict = {
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
                         '东四': {'aqi': Decimal('50'),
                                'co': Decimal('0.4'),
                                'no2': Decimal('40'),
                                'o3': Decimal('42'),
                                'o3_8h': Decimal('44'),
                                'pm10': None,
                                'pm2_5': Decimal('35'),
                                'primary_pollutant': '',
                                'quality': 'E',
                                'so2': Decimal('2')},
                         '农展馆': {'aqi': Decimal('25'),
                                 'co': Decimal('0.3'),
                                 'no2': Decimal('50'),
                                 'o3': Decimal('36'),
                                 'o3_8h': Decimal('45'),
                                 'pm10': None,
                                 'pm2_5': Decimal('16'),
                                 'primary_pollutant': '',
                                 'quality': 'E',
                                 'so2': Decimal('4')},
                         '古城': {'aqi': Decimal('25'),
                                'co': Decimal('0.3'),
                                'no2': Decimal('15'),
                                'o3': Decimal('73'),
                                'o3_8h': Decimal('68'),
                                'pm10': Decimal('25'),
                                'pm2_5': Decimal('6'),
                                'primary_pollutant': '',
                                'quality': 'E',
                                'so2': Decimal('3')},
                         '天坛': {'aqi': Decimal('60'),
                                'co': Decimal('0.5'),
                                'no2': Decimal('44'),
                                'o3': Decimal('46'),
                                'o3_8h': Decimal('36'),
                                'pm10': None,
                                'pm2_5': Decimal('43'),
                                'primary_pollutant': 'pm2_5',
                                'quality': 'G',
                                'so2': Decimal('2')},
                         '奥体中心': {'aqi': Decimal('36'),
                                  'co': Decimal('0.3'),
                                  'no2': Decimal('41'),
                                  'o3': Decimal('34'),
                                  'o3_8h': Decimal('34'),
                                  'pm10': Decimal('36'),
                                  'pm2_5': Decimal('19'),
                                  'primary_pollutant': '',
                                  'quality': 'E',
                                  'so2': Decimal('4')},
                         '官园': {'aqi': Decimal('45'),
                                'co': Decimal('0.4'),
                                'no2': Decimal('35'),
                                'o3': Decimal('41'),
                                'o3_8h': Decimal('40'),
                                'pm10': Decimal('45'),
                                'pm2_5': Decimal('17'),
                                'primary_pollutant': '',
                                'quality': 'E',
                                'so2': Decimal('4')},
                         '定陵': {'aqi': Decimal('28'),
                                'co': Decimal('0.3'),
                                'no2': Decimal('11'),
                                'o3': Decimal('65'),
                                'o3_8h': Decimal('63'),
                                'pm10': Decimal('28'),
                                'pm2_5': Decimal('13'),
                                'primary_pollutant': '',
                                'quality': 'E',
                                'so2': Decimal('3')},
                         '怀柔镇': {'aqi': Decimal('55'),
                                 'co': Decimal('0.2'),
                                 'no2': Decimal('27'),
                                 'o3': Decimal('37'),
                                 'o3_8h': Decimal('58'),
                                 'pm10': Decimal('59'),
                                 'pm2_5': Decimal('31'),
                                 'primary_pollutant': 'pm10',
                                 'quality': 'G',
                                 'so2': Decimal('2')},
                         '昌平镇': {'aqi': Decimal('57'),
                                 'co': Decimal('0.4'),
                                 'no2': Decimal('51'),
                                 'o3': Decimal('28'),
                                 'o3_8h': Decimal('38'),
                                 'pm10': Decimal('41'),
                                 'pm2_5': Decimal('40'),
                                 'primary_pollutant': 'pm2_5',
                                 'quality': 'G',
                                 'so2': Decimal('6')},
                         '海淀区万柳': {'aqi': Decimal('75'),
                                   'co': Decimal('0.4'),
                                   'no2': Decimal('53'),
                                   'o3': Decimal('31'),
                                   'o3_8h': Decimal('31'),
                                   'pm10': Decimal('99'),
                                   'pm2_5': Decimal('24'),
                                   'primary_pollutant': 'pm10',
                                   'quality': 'G',
                                   'so2': Decimal('2')},
                         '顺义新城': {'aqi': Decimal('48'),
                                  'co': Decimal('0.3'),
                                  'no2': Decimal('34'),
                                  'o3': Decimal('43'),
                                  'o3_8h': Decimal('28'),
                                  'pm10': None,
                                  'pm2_5': Decimal('33'),
                                  'primary_pollutant': '',
                                  'quality': 'E',
                                  'so2': Decimal('2')}},
            'update_dtm': datetime(2016, 5, 7, 0, 0, tzinfo=pytz.utc)}

    def test_output(self):
        self.assertEqual(self.expected_processed_dict, extractors.process_parsed_dict(self.parsed_dict))


class TestBuiltinPatterns(SimpleTestCase):

    def setUp(self):
        self.file = open(os.path.join(dir_path, 'files/zh_names.txt'))

    def test_func(self):
        pattern = re.compile(r"[0-9a-z\uff00-\uffef\u4e00-\u9fff]+", re.I)
        for line in self.file:
            line = line.strip()
            if line:
                self.assertTrue(pattern.fullmatch(line))

    def tearDown(self):
        self.file.close()


class TestGetSSHClient(SimpleTestCase):

    def setUp(self):
        self.known_host = '10.103.248.78'
        self.known_user = 'yifan'
        self.unknown_but_exists_host = '10.103.248.79'
        self.not_exist_host = '12.123.456.78'

    def test_get_ssh_client(self):
        # wrong user without password
        with self.assertRaises(ssh_exception.PasswordRequiredException):
            aqhi.airquality.utils.get_ssh_client(self.known_host, 'abcd')

        # existing user with wrong password
        with self.assertRaises(ssh_exception.AuthenticationException):
            aqhi.airquality.utils.get_ssh_client(self.known_host, 'root', '123456')

        # wrong user with password
        with self.assertRaises(ssh_exception.AuthenticationException):
            aqhi.airquality.utils.get_ssh_client(self.known_host, 'abcd', '123445')

        # unknown host
        with self.assertRaises(ssh_exception.ServerNotKnown):
            aqhi.airquality.utils.get_ssh_client(self.not_exist_host, 'abcd')

        # existing server but without ssh service
        with self.assertRaises(ssh_exception.ConnectionTimeOut):
            aqhi.airquality.utils.get_ssh_client(self.unknown_but_exists_host, 'foo')
