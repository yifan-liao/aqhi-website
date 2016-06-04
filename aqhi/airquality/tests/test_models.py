# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from decimal import Decimal

import pytz
from django.core.exceptions import ValidationError
from django.test import TestCase

from aqhi.airquality.tests.utils import random_datetime
from . import factories
from ..models import (
    City, Station, CityRecord, StationRecord, EstimatedCityRecord, EstimatedStationRecord,
    CityPrimaryPollutantItem, StationPrimaryPollutantItem,
    EstimatedCityPrimaryPollutantItem, EstimatedStationPrimaryPollutantItem,
    create_city_record
)


class TestCity(TestCase):

    def test_duplicate_save(self):
        self.assertTrue(City.objects.validate_and_create(
            name_en='beijing', name_cn='北京'
        ))
        with self.assertRaises(ValidationError) as cm:
            City.objects.validate_and_create(
                name_en='beijing', name_cn='123'
            )

        with self.assertRaises(ValidationError) as cm:
            City.objects.validate_and_create(
                name_en='Beijing', name_cn='123'
            )


class TestStation(TestCase):

    def test_duplicate_save(self):
        city = City(name_cn='北京', name_en='beijing')
        city.save()
        station = Station.objects.validate_and_create(
            name_cn='东城区', city=city
        )
        with self.assertRaises(ValidationError) as cm:
            Station.objects.validate_and_create(
                name_cn='东城区', city=city
            )


class TestCityRecord(TestCase):

    def test_create_without_pollutants(self):
        # normally with all fields present
        record_fields = factories.CityRecordFieldsFactory()
        record = CityRecord.objects.validate_and_create_with_pollutants(
            city=factories.CityFactory(),
            **record_fields,
        )
        self.assertTrue(CityRecord.objects.filter(pk=record.pk).exists())
        for field_name, field in record_fields.items():
            self.assertEqual(field, getattr(record, field_name))

        # with some absent fields
        del record_fields['aqi']
        del record_fields['co']
        del record_fields['quality']
        record = CityRecord.objects.validate_and_create_with_pollutants(
            city=factories.CityFactory(),
            **record_fields,
        )
        self.assertIsNone(getattr(record, 'aqi'))
        self.assertIsNone(getattr(record, 'co'))
        self.assertEqual(getattr(record, 'quality'), '')

        # without city
        record_fields = factories.RecordFieldsFactory()
        with self.assertRaises(ValidationError) as cm:
            CityRecord.objects.validate_and_create_with_pollutants(
                **record_fields,
            )
        self.assertIn('city', cm.exception.message_dict)

        # with invalid value: ('None', '1234')
        record_fields['aqi'] = ('None', '1234')
        with self.assertRaises(ValueError) as cm:
            CityRecord.objects.validate_and_create_with_pollutants(
                city=factories.CityFactory(),
                **record_fields,
            )

    def test_create_with_pollutants(self):
        # normally with one pollutant
        record = CityRecord.objects.validate_and_create_with_pollutants(
            city=factories.CityFactory(),
            pollutants='no2',
            **factories.CityRecordFieldsFactory(),
        )
        self.assertTrue(CityPrimaryPollutantItem.objects.filter(city_record=record, pollutant='no2').exists())

        # with two pollutants
        record = CityRecord.objects.validate_and_create_with_pollutants(
            city=factories.CityFactory(),
            pollutants=['co', 'so2'],
            **factories.CityRecordFieldsFactory(),
        )
        self.assertTrue(CityPrimaryPollutantItem.objects.filter(city_record=record, pollutant='so2').exists())
        self.assertTrue(CityPrimaryPollutantItem.objects.filter(city_record=record, pollutant='co').exists())

        # without pollutants
        for empty_poll in ['', [], None]:
            record = CityRecord.objects.validate_and_create_with_pollutants(
                city=factories.CityFactory(),
                pollutants=empty_poll,
                **factories.CityRecordFieldsFactory(),
            )
            self.assertFalse(CityPrimaryPollutantItem.objects.filter(city_record=record).exists())

    def test_latests(self):
        base_dtm = datetime(2016, 1, 1, tzinfo=pytz.utc)
        city1 = factories.CityFactory()
        city2 = factories.CityFactory()

        factories.CityRecordFactory(city=city1, update_dtm=base_dtm)
        factories.CityRecordFactory(city=city2, update_dtm=base_dtm)
        latest_dtm = base_dtm + timedelta(days=1)
        latest_city1 = factories.CityRecordFactory(city=city1, update_dtm=latest_dtm)
        latest_city2 = factories.CityRecordFactory(city=city2, update_dtm=latest_dtm)

        latests = CityRecord.objects.latests()
        self.assertListEqual(
            list(latests),
            [latest_city1, latest_city2],
        )

    def test_calc_aqhi_field(self):
        fields = ['pm10', 'pm2_5', 'so2', 'no2', 'o3']
        data = [
            [[426, 473, 495], [133, 141, 140], [2, 2, 2], [9, 8, 9], [86, 93, 93], 10],
        ]
        data_values = []
        for data_row in data:
            data_row = data_row[:-1]
            lines = []
            for j in range(len(data_row[0])):
                lines.append([line[j] for line in data_row])
            data_values.append(lines)

        dtm_now = random_datetime(hour_delta=0)
        city = factories.CityFactory()
        for i, values in enumerate(data_values):
            records = []
            j = -1
            for j, row in enumerate(values):
                records.append(factories.CityRecordFactory(
                    city=city,
                    **dict(zip(fields, list(map(Decimal, row))))
                ))

            self.assertEqual(records[0].calculate_aqhi_field(), data[i][-1])
            dtm_now += timedelta(hours=j+1)


class TestEstimatedCityRecord(TestCase):

    def test_create_without_pollutants(self):
        # normally with all fields present
        record_fields = factories.RecordFieldsFactory()
        record = EstimatedCityRecord.objects.validate_and_create_with_pollutants(
            original_record=factories.CityRecordFactory(),
            **record_fields,
        )
        self.assertTrue(EstimatedCityRecord.objects.filter(pk=record.pk).exists())
        for field_name, field in record_fields.items():
            self.assertEqual(field, getattr(record, field_name))

        # with some absent fields
        del record_fields['aqi']
        del record_fields['co']
        del record_fields['quality']
        record = EstimatedCityRecord.objects.validate_and_create_with_pollutants(
            original_record=factories.CityRecordFactory(),
            **record_fields,
        )
        self.assertIsNone(getattr(record, 'aqi'))
        self.assertIsNone(getattr(record, 'co'))
        self.assertEqual(getattr(record, 'quality'), '')

        # without original_record
        with self.assertRaises(ValidationError) as cm:
            EstimatedCityRecord.objects.validate_and_create_with_pollutants(
                **record_fields,
            )
        self.assertIn('original_record', cm.exception.message_dict)

    def test_create_with_pollutants(self):
        # normally with one pollutant
        record = EstimatedCityRecord.objects.validate_and_create_with_pollutants(
            original_record=factories.CityRecordFactory(),
            pollutants='no2',
            **factories.RecordFieldsFactory(),
        )
        self.assertTrue(EstimatedCityPrimaryPollutantItem.objects.filter(city_record=record, pollutant='no2').exists())

        # with 2 pollutants
        record = EstimatedCityRecord.objects.validate_and_create_with_pollutants(
            original_record=factories.CityRecordFactory(),
            pollutants=['no2', 'pm2_5'],
            **factories.RecordFieldsFactory(),
        )
        self.assertTrue(EstimatedCityPrimaryPollutantItem.objects.filter(city_record=record, pollutant='no2').exists())
        self.assertTrue(
            EstimatedCityPrimaryPollutantItem.objects.filter(city_record=record, pollutant='pm2_5').exists()
        )

        # without pollutants
        for empty_poll in ['', [], None]:
            record = EstimatedCityRecord.objects.validate_and_create_with_pollutants(
                original_record=factories.CityRecordFactory(),
                pollutants=empty_poll,
                **factories.RecordFieldsFactory(),
            )
            self.assertFalse(EstimatedCityPrimaryPollutantItem.objects.filter(city_record=record).exists())


class TestStationRecord(TestCase):

    def test_create_without_pollutants(self):
        # normally with all fields present
        record_fields = factories.RecordFieldsFactory()
        record = StationRecord.objects.validate_and_create_with_pollutants(
            station=factories.StationFactory(),
            city_record=factories.CityRecordFactory(),
            **record_fields,
        )
        self.assertTrue(StationRecord.objects.filter(pk=record.pk).exists())
        for field_name, field in record_fields.items():
            self.assertEqual(field, getattr(record, field_name))

        # with some absent fields
        del record_fields['aqi']
        del record_fields['co']
        del record_fields['quality']
        record = StationRecord.objects.validate_and_create_with_pollutants(
            station=factories.StationFactory(),
            city_record=factories.CityRecordFactory(),
            **record_fields,
        )
        self.assertIsNone(getattr(record, 'aqi'))
        self.assertIsNone(getattr(record, 'co'))
        self.assertEqual(getattr(record, 'quality'), '')

        # without station and city_record
        with self.assertRaises(ValidationError) as cm:
            StationRecord.objects.validate_and_create_with_pollutants(
                **record_fields,
            )
        self.assertIn('station', cm.exception.message_dict)
        self.assertIn('city_record', cm.exception.message_dict)

    def test_create_with_pollutants(self):
        # normally with one pollutant
        record = StationRecord.objects.validate_and_create_with_pollutants(
            city_record=factories.CityRecordFactory(),
            station=factories.StationFactory(),
            pollutants='co',
            **factories.RecordFieldsFactory(),
        )
        self.assertTrue(StationPrimaryPollutantItem.objects.filter(station_record=record, pollutant='co').exists())

        # with two pollutants
        record = StationRecord.objects.validate_and_create_with_pollutants(
            city_record=factories.CityRecordFactory(),
            station=factories.StationFactory(),
            pollutants=['co', 'pm10'],
            **factories.RecordFieldsFactory(),
        )
        self.assertTrue(StationPrimaryPollutantItem.objects.filter(station_record=record, pollutant='co').exists())
        self.assertTrue(StationPrimaryPollutantItem.objects.filter(station_record=record, pollutant='pm10').exists())

        # Without pollutants
        for empty_poll in ['', [], None]:
            record = StationRecord.objects.validate_and_create_with_pollutants(
                city_record=factories.CityRecordFactory(),
                station=factories.StationFactory(),
                pollutants=empty_poll,
                **factories.RecordFieldsFactory(),
            )
        self.assertFalse(StationPrimaryPollutantItem.objects.filter(station_record=record).exists())

    def test_latests(self):
        base_dtm = datetime(2016, 1, 1, tzinfo=pytz.utc)
        city = factories.CityFactory()
        station = factories.StationFactory(city=city)

        old_record_city_1 = factories.CityRecordFactory(city=city, update_dtm=base_dtm)
        old_record_city_2 = factories.CityRecordFactory(city=city, update_dtm=base_dtm + timedelta(days=1))
        latest_city_record = factories.CityRecordFactory(city=city, update_dtm=base_dtm + timedelta(days=2))

        factories.StationRecordFactory(city_record=old_record_city_1, station=station)
        factories.StationRecordFactory(city_record=old_record_city_2, station=station)

        latest_record = factories.StationRecordFactory(city_record=latest_city_record, station=station)

        latests = StationRecord.objects.latests()
        self.assertListEqual(
            list(latests),
            [latest_record],
        )

    def test_calc_aqhi_field(self):
        fields = ['pm10', 'pm2_5', 'so2', 'no2', 'o3']
        data = [
            [[605, 579, 592], [236, 296, 238], [7, 7, 7], [12, 11, 10], [162, 168, 169], 11],
            [[426, 473, 495], [133, 141, 140], [2, 2, 2], [9, 8, 9], [86, 93, 93], 10],
            [[332, 234, 248], [92, 58, 63], [11, 11, 12], [10, 13, 9], [112, 106, 108], 8],
            [[61, 65, 65], [38, 37, 36], [16, 15, 13], [8, 10, 15], [202, 204, 192], 8],
        ]
        data_values = []
        for data_row in data:
            data_row = data_row[:-1]
            lines = []
            for j in range(len(data_row[0])):
                lines.append([line[j] for line in data_row])
            data_values.append(lines)

        dtm_now = random_datetime(hour_delta=0)
        station = factories.StationFactory()
        for i, values in enumerate(data_values):
            records = []
            j = -1
            for j, row in enumerate(values):
                records.append(factories.StationRecordFactory(
                    station=station,
                    city_record=factories.CityRecordFactory(city=station.city, update_dtm=dtm_now - timedelta(hours=j)),
                    **dict(zip(fields, list(map(Decimal, row))))
                ))

            self.assertEqual(records[0].calculate_aqhi_field(), data[i][-1])
            dtm_now += timedelta(hours=j+1)

    def test_none_aqhi_field(self):
        dtm_now = random_datetime(hour_delta=0)
        station = factories.StationFactory()

        records = []
        records.append(factories.StationRecordFactory(
            station=station,
            city_record=factories.CityRecordFactory(city=station.city, update_dtm=dtm_now - timedelta(hours=0)),
        ))

        for hour in range(1, 3):
            records.append(factories.StationRecordFactory(
                station=station,
                city_record=factories.CityRecordFactory(city=station.city, update_dtm=dtm_now - timedelta(hours=hour)),
            ))
        self.assertIsNotNone(records[0].calculate_aqhi_field())

        for i in range(len(records)):
            records[i].pm10 = None
            records[i].save()

        self.assertIsNone(records[0].calculate_aqhi_field())


class TestEstimatedStationRecord(TestCase):

    def test_create_without_pollutants(self):
        # normally with all fields present
        record_fields = factories.RecordFieldsFactory()
        record = EstimatedStationRecord.objects.validate_and_create_with_pollutants(
            original_record=factories.StationRecordFactory(),
            **record_fields,
        )
        self.assertTrue(EstimatedStationRecord.objects.filter(pk=record.pk).exists())
        for field_name, field in record_fields.items():
            self.assertEqual(field, getattr(record, field_name))

        # with some absent fields
        del record_fields['aqi']
        del record_fields['co']
        del record_fields['quality']
        record = EstimatedStationRecord.objects.validate_and_create_with_pollutants(
            original_record=factories.StationRecordFactory(),
            **record_fields,
        )
        self.assertIsNone(getattr(record, 'aqi'))
        self.assertIsNone(getattr(record, 'co'))
        self.assertEqual(getattr(record, 'quality'), '')

        # without original record
        with self.assertRaises(ValidationError) as cm:
            EstimatedStationRecord.objects.validate_and_create_with_pollutants(
                **record_fields,
            )
        self.assertIn('original_record', cm.exception.message_dict)

    def test_create_with_pollutants(self):
        # normally with one pollutant
        record = EstimatedStationRecord.objects.validate_and_create_with_pollutants(
            original_record=factories.StationRecordFactory(),
            pollutants='no2',
            **factories.RecordFieldsFactory(),
        )
        self.assertTrue(EstimatedStationPrimaryPollutantItem.objects.filter(station_record=record, pollutant='no2').exists())

        # with 2 pollutants
        record = EstimatedStationRecord.objects.validate_and_create_with_pollutants(
            original_record=factories.StationRecordFactory(),
            pollutants=['no2', 'pm2_5'],
            **factories.RecordFieldsFactory(),
        )
        self.assertTrue(EstimatedStationPrimaryPollutantItem.objects.filter(station_record=record, pollutant='no2').exists())
        self.assertTrue(EstimatedStationPrimaryPollutantItem.objects.filter(station_record=record, pollutant='pm2_5').exists())

        # without pollutants
        for empty_poll in ['', [], None]:
            record = EstimatedStationRecord.objects.validate_and_create_with_pollutants(
                original_record=factories.StationRecordFactory(),
                pollutants=empty_poll,
                **factories.RecordFieldsFactory(),
            )
            self.assertFalse(EstimatedStationPrimaryPollutantItem.objects.filter(station_record=record).exists())


class TestCreateCityRecord(TestCase):

    def test_without_city_existence(self):
        info_dict = factories.InfoDictFactory()
        result = create_city_record(info_dict)
        self.assertEqual(result['success'], 0)
        self.assertEqual(result['error_type'], 'CityNotFound')
        self.assertEqual(result['info'], info_dict['city']['area_en'])

    def test_with_existing_record(self):
        dtm = random_datetime()
        city = factories.CityFactory()
        factories.CityRecordFactory(city=city, update_dtm=dtm)

        result = create_city_record(factories.InfoDictFactory(city=city, update_dtm=dtm))
        self.assertEqual(result['success'], 0)
        self.assertEqual(result['error_type'], 'UniquenessError')
        self.assertEqual(result['info'], dtm)

    def test_without_stations_existence(self):
        city = factories.CityFactory()
        station = factories.StationFactory(city=city, name_cn='监测点一')

        result = create_city_record(factories.InfoDictFactory(city=city, stations=[station, 'foo', '甲'], station_num=3))
        self.assertEqual(result['success'], 0)
        self.assertEqual(result['error_type'], 'StationNotFound')
        self.assertSetEqual(set(result['info']), {'foo', '甲'})
        
    def test_save_record(self):
        dtm = random_datetime()
        city = factories.CityFactory()
        station1 = factories.StationFactory(city=city)
        station2 = factories.StationFactory(city=city)

        result = create_city_record(factories.InfoDictFactory(
            city=city, stations=[station1, station2], station_num=2,
            update_dtm=dtm
        ))
        self.assertEqual(result['success'], 1)
        city_record = CityRecord.objects.filter(city=city, update_dtm=dtm)
        self.assertTrue(city_record.exists())
        city_record = city_record[0]
        self.assertEqual(result['info'], city_record)
        self.assertTrue(StationRecord.objects.filter(city_record=city_record, station=station1).exists())

    def test_atomicity(self):
        dtm = random_datetime()
        city = factories.CityFactory()
        station = factories.StationFactory(city=city)

        info_dict = factories.InfoDictFactory(
            city=city, stations=[station], station_num=3,
            update_dtm=dtm
        )
        info_dict['stations'][station.name_cn]['aqi'] = (None, 'foobar')
        result = create_city_record(info_dict)
        self.assertEqual(result['success'], 0)
        self.assertEqual(result['error_type'], 'ValueError')
        self.assertFalse(CityRecord.objects.filter(city=city, update_dtm=dtm).exists())
