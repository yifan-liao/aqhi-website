# -*- coding: utf-8 -*-
import json
import collections

from django.test import SimpleTestCase
from django.core.urlresolvers import reverse
from django.forms.models import model_to_dict
from rest_framework.test import APITestCase, APIRequestFactory
from rest_framework import status

from . import factories
from .. import serializers, views


def get_formatted_json(data):
    return json.dumps(data, indent=2)


def patch_params_to_url(url, params):
    if params:
        if url[-1] != '/':
            url += '/'
        url += '?'
    else:
        return url

    field = list(params.items())[0][0]
    value = params.pop(field)
    url += '{0}={1}'.format(field, value)
    for field, value in params.items():
        url += '&{0}={1}'.format(field, value)

    return url


def has_fields(d, fields):
    """
    has_fields({"a": 1, "b": {"c": 1}}, {"a", ("b", "c")}) == True
    """
    if len(d.keys()) != len(fields):
        return False

    for field in fields:
        if not isinstance(field, str) and isinstance(field, collections.Iterable):
            it = iter(field)
            key = next(it)
            if key not in d:
                return False
            nested_d = d[key]
            if set(nested_d.keys()) != set(it):
                return False
        elif field not in d:
            return False

    return True


class UtilTest(SimpleTestCase):

    def test_has_fields(self):
        self.assertTrue(has_fields({"a": 1, "b": {"c": 1}}, {"a", ("b", "c")}))
        self.assertTrue(has_fields({"a": 1, "b": 1}, {"a", "b"}))
        self.assertTrue(has_fields({"a": 1, "b": {"c": 1, "d": 2}, "e": 5}, {"a", ("b", "c", "d"), "e"}))


class APITestUtilsMixin(object):

    def force_authenticate_user(self, user):
        self.client.force_authenticate(user=user)


class CityRecordAPITest(APITestUtilsMixin, APITestCase):

    def get_city_record_list(self, params=None):
        if params is None:
            params = {}
        return self.client.get(patch_params_to_url(reverse('api:city-record-list'), params))

    def get_city_record_detail(self, record, params=None):
        if params is None:
            params = {}
        return self.client.get(patch_params_to_url(reverse('api:city-record-detail', kwargs={'pk': record.pk}), params))

    def test_get_city_records(self):
        fields = list(serializers.CityRecordSerializer.Meta.fields)
        fields.remove('city')
        fields.append(('city', ) + serializers.CitySerializer.Meta.fields)

        city = factories.CityFactory()
        factories.CityRecordFactory(city=city)

        response = self.get_city_record_list()
        self.assertTrue(has_fields(response.data['results'][0], fields))

        factories.CityRecordFactory()
        fields_param = 'city,update_dtm,o3'
        response = self.get_city_record_list(params={'city': city.name_en, 'fields': fields_param})
        self.assertEqual(len(response.data['results']), 1)
        self.assertTrue(has_fields(response.data['results'][0], ['url', 'id', 'o3', 'update_dtm', ('city', ) + serializers.CitySerializer.Meta.fields]))

    def test_get_city_record_detail(self):
        city = factories.CityFactory()
        record = factories.CityRecordFactory(city=city)

        fields_param = 'city,update_dtm,o3'
        response = self.get_city_record_detail(record,
                                               params={'city_en': city.name_en, 'fields': fields_param})
        self.assertTrue(has_fields(response.data, {'url', 'id', 'update_dtm', 'o3', ('city', ) + serializers.CitySerializer.Meta.fields}))

    def test_filter_multiple_cities(self):
        city1 = factories.CityFactory()
        city2 = factories.CityFactory()

        factories.CityRecordFactory(city=city1)

        response = self.get_city_record_list()
        self.assertEqual(len(response.data['results']), 1)

        response = self.get_city_record_list(params={'city': city1.name_en})
        self.assertEqual(len(response.data['results']), 1)

    def test_primary_pollutants(self):
        city_record = factories.CityRecordFactory()

        response = self.get_city_record_detail(city_record)
        self.assertIn('primary_pollutants', response.data)


class FilterFieldsSerializerMixinTest(SimpleTestCase):

    def test_gen_struct(self):
        fields = ['a', 'b__a', 'b__b__a']
        self.assertEqual(
            views.FilterFieldsMixin._generate_structure(fields),
            {'a': None, 'b': {'a': None, 'b': {'a': None}}}
        )

        fields = ['a', 'b__a', 'b__b', 'c', 'd__a', 'e__b']
        self.assertEqual(
            views.FilterFieldsMixin._generate_structure(fields),
            {'a': None, 'b': {'a': None, 'b': None}, 'c': None, 'd': {'a': None}, 'e': {'b': None}}
        )

        fields = ['a', 'b', 'c']
        self.assertEqual(
            views.FilterFieldsMixin._generate_structure(fields),
            {'a': None, 'b': None, 'c': None}
        )

        for fields in [['a', 'a__b'], ['a__b', 'a']]:
            with self.subTest(fields=fields):
                self.assertEqual(
                    views.FilterFieldsMixin._generate_structure(fields),
                    {'a': {'b': None}}
                )

        fields = ['a', 'b', 'b']
        self.assertEqual(
            views.FilterFieldsMixin._generate_structure(fields),
            {'a': None, 'b': None}
        )

    def test_filter_instance(self):
        instance = {'url': 'url_a',
                    'id': 12,
                    'a': 'a',
                    'b': {'url': 'foo', 'id': 10, 'a': 'ba', 'b': 'bb', 'c': 'bc'},
                    'c': 'c'}
        filter_dict = {'a': None, 'b': {'a': None, 'b': None}, 'c': None}
        res = {}
        views.FilterFieldsMixin._filter_instance(instance, filter_dict, res)
        self.assertEqual(res, {'url': 'url_a', 'id': 12, 'a': 'a', 'c': 'c', 'b': {'url': 'foo', 'id': 10, 'a': 'ba', 'b': 'bb'}})

        filter_dict = {'a': None, 'b': None}
        res = {}
        views.FilterFieldsMixin._filter_instance(instance, filter_dict, res)
        self.assertEqual(res, {'url': 'url_a', 'id': 12, 'a': 'a', 'b': {'url': 'foo', 'id': 10, 'a': 'ba', 'b': 'bb', 'c': 'bc'}})


class LatestCityRecordTestCase(APITestCase):

    @classmethod
    def setUpClass(cls):
        super(LatestCityRecordTestCase, cls).setUpClass()
        cls.factory = APIRequestFactory()
        cls.url_name = 'api:latest-city-record'

    def get_latest_city_record(self, params=None):
        if params is None:
            params = {}
        return self.client.get(patch_params_to_url(reverse(self.url_name), params))

    def serialize_city_record(self, record):
        return serializers.CityRecordSerializer(record,
                                                context={'request': self.factory.get(reverse(self.url_name))}).data

    def test_get_without_existing_records(self):
        resp = self.get_latest_city_record({'city': 'beijing'})
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_not_existing_city(self):
        factories.CityRecordFactory()

        resp = self.get_latest_city_record({'city': 'beijing'})
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_record(self):
        record = factories.CityRecordFactory()

        resp = self.get_latest_city_record({'city': record.city.name_en})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data, self.serialize_city_record(record))
