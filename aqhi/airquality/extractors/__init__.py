# -*- coding: utf-8 -*-
# These are tools to extract info from web page.
import re
import decimal
import copy
from datetime import datetime
import pytz

import lxml.html as html

from .utils import (
    aggregate_keys_with_one_freq, calc_freq,
)
from . import rules


def extract_info(html_string, name_xpath_mappings=rules.info_xpath_mappings,
                 name_preprocessor_mappings=rules.info_preprocessors):
    """
    Given an html unicode string, return a dict containing info.
    Use xpath in name_xpath_mappings dict to parse the page.

    :param html_string: a string containing html content
    :param name_xpath_mappings: a dict mapping info's name to xpath
    :param name_preprocessor_mappings: a dict telling how to process data just after extracting
    :return: a dict mapping info's name to a list of info(strings or lists of strings)

    The info returned has only been processed a little bit, not yet parsed.

    After info has been extracted by xpath, info will be normalized first and then processed by
    the functions in name_preprocessor_mappings if corresponding method exists.

    Preprocessors are given a list of strings(or even list of lists of strings) as argument instead of
    a single string. In this way, you can process further such as split one value into multiple ones.

    Each info value will be in a list even if there is only one value.
    """
    html_element = html.fromstring(html_string)

    def extract_and_normalize_string_from_element(e):
        return re.sub(r'\s+', ' ', e.xpath("string()")).strip()

    info_dict = {}
    for info_name in name_xpath_mappings:
        xpath_pattern = name_xpath_mappings[info_name]
        if isinstance(xpath_pattern, str):
            # One dimension
            data_list = html_element.xpath(xpath_pattern)

            processed_list = list(map(
                extract_and_normalize_string_from_element,
                data_list
            ))
            if info_name in name_preprocessor_mappings:
                preprocessor = name_preprocessor_mappings[info_name]
                processed_list = preprocessor(processed_list)

            info_dict[info_name] = processed_list

        elif isinstance(xpath_pattern, list):
            # Two dimensions
            data_rows = html_element.xpath(xpath_pattern[0])
            for i in range(len(data_rows)):
                data_row = data_rows[i].xpath(xpath_pattern[1])
                data_rows[i] = data_row

            has_preprocessor = (info_name in name_preprocessor_mappings)
            for i, row in enumerate(data_rows):
                for j, cell in enumerate(row):
                    cell = extract_and_normalize_string_from_element(cell)
                    data_rows[i][j] = cell

                if has_preprocessor:
                    data_rows[i] = name_preprocessor_mappings[info_name](row)

            info_dict[info_name] = data_rows

        else:
            raise ValueError('Invalid name-xpath mappings.')

    return info_dict


def parse_info_dict(info_dict, info_patterns=rules.info_patterns, consts_mapping=rules.consts_pattern_field_mappings):
    """
    Try to parse the info dict returned by extract_info using the consts mapping to
    help map row data to data we know.

    :param info_dict: the dict returned by extract_info
    :param info_patterns: the mapping fro info name to a list of pattern names telling how to parse the value
    :param consts_mapping: the mapping from re patterns to const values
    :return: a dict with same structure as info_dict but with data parsed

    For each value in info_dict, first get the required pattern names, then use the corresponding pattern
    to parse.

    Pattern names explained
    1. `num`. Parse to Decimal objects.
    2. `consts`. Use consts_mapping to parse to constant values.
    3. `zh_name`. Parse strings with alpnum, Chinese character or symbol
    4. `datetime`. Parse to datetime objects with utc timezone.

    Unknown values are matched to tuple (None, original_string).

    All lists with only one string value will be flattened. (only flat one level)
    """
    from aqhi.airquality.utils import list_depth
    zh_name_pattern = re.compile(r"[0-9a-z\uff00-\uffef\u4e00-\u9fff ]+", re.I)
    dtm_fmt = '%Y-%m-%d %H:%M:%S'
    shanghai = pytz.timezone('Asia/Shanghai')

    def parse_list(list_to_parse, info_name):

        def map_to_const(t):
            if not isinstance(t, tuple):
                return t
            for pattern in consts_mapping:
                match = pattern.search(t[1])
                if match:
                    return consts_mapping[pattern]
            return t

        def map_to_decimal(t):
            if not isinstance(t, tuple):
                return t
            string = t[1]
            try:
                return decimal.Decimal(string)
            except decimal.InvalidOperation:
                return t

        def preserve_zh_name(t):
            if not isinstance(t, tuple):
                return t
            string = t[1]
            if zh_name_pattern.fullmatch(string):
                return string
            return t

        def map_to_datetime(t):
            if not isinstance(t, tuple):
                return t
            string = t[1]
            try:
                loc_dt = shanghai.localize(datetime.strptime(string, dtm_fmt))
                return loc_dt.astimezone(pytz.utc)
            except ValueError as e:
                return t

        # first tag all values to unknown: (None, value)
        parsed = map(
            lambda value: (None, value),
            list_to_parse
        )
        # then
        pattern_names = info_patterns[info_name]
        for pattern_name in pattern_names:
            if pattern_name == 'consts':
                parsed = map(map_to_const, parsed)
            elif pattern_name == 'num':
                parsed = map(map_to_decimal, parsed)
            elif pattern_name == 'zh_name':
                parsed = map(preserve_zh_name, parsed)
            elif pattern_name == 'datetime':
                parsed = map(map_to_datetime, parsed)
            else:
                raise ValueError('Unknown pattern name of {}: {}.'.format(info_name, pattern_name))

        return list(parsed)

    parsed_dict = {}
    for name, info_list in info_dict.items():
        parsed_list = copy.deepcopy(info_list)
        depth = list_depth(info_list)

        # then map according to the rules
        if depth == 1:
            parsed_list = parse_list(parsed_list, name)
        elif depth == 2:
            for i, row in enumerate(parsed_list):
                parsed_list[i] = parse_list(row, name)

        if len(parsed_list) == 1 and not isinstance(parsed_list[0], list):
            parsed_list = parsed_list[0]

        parsed_dict[name] = parsed_list

    return parsed_dict


def process_parsed_dict(parsed_dict):
    """
    Process the parsed info dict.

    1. Aggregate 'city_quality_names', 'city_quality_values', 'area_cn', 'primary_pollutant' and 'quality'
    fields to 'city' field, while aggregate 'station_quality_names' and 'station_quality_rows' to 'stations'.
    2. Map decimal field's empty value to None.

    :param parsed_dict: the dict returned by parse _info_dict
    :return: the aggregated dict
    """
    city = dict(zip(parsed_dict['city_quality_names'], parsed_dict['city_quality_values']))
    city.update((
        ('area_cn', parsed_dict['area_cn']),
        ('primary_pollutant', parsed_dict['primary_pollutant']),
        ('quality', parsed_dict['quality']),
    ))

    name_index = parsed_dict['station_quality_names'].index('name')
    new_names = parsed_dict['station_quality_names'][:]
    del new_names[name_index]
    stations = {}
    for station in parsed_dict['station_quality_rows']:
        name = station[name_index]
        new_values = station[:]
        del new_values[name_index]
        stations[name] = dict(zip(new_names, new_values))

    # Map empty decimal fields to None
    def map_empty_decimal_string_to_none(k, v):
        if v == '' and k in {'aqi', 'co', 'no2', 'o3', 'o3_8h', 'pm10', 'pm2_5', 'so2'}:
            return None
        return v

    for key, value in city.items():
        if map_empty_decimal_string_to_none(key, value) is None:
            city[key] = None
    for name, station in stations.items():
        for key, value in station.items():
            if map_empty_decimal_string_to_none(key, value) is None:
                station[key] = None

    return {
        'city': city,
        'stations': stations,
        'update_dtm': parsed_dict['update_dtm']
    }


