from decimal import Decimal
import random
from itertools import combinations
from datetime import datetime, timedelta

import pytz
import factory
from factory.django import DjangoModelFactory

from .. import models
from .. import utils


class CityFactory(DjangoModelFactory):
    name_en = factory.Sequence(lambda n: 'city{}'.format(n))
    name_cn = factory.Sequence(lambda n: '城市{}'.format(n))
    longitude = factory.LazyFunction(lambda: Decimal('{}.{}'.format(
        random.randint(0, 9999),
        random.randint(0, 9999),
    )))
    latitude = factory.LazyFunction(lambda: Decimal('{}.{}'.format(
        random.randint(0, 9999),
        random.randint(0, 9999),
    )))

    class Meta:
        model = models.City


class StationFactory(DjangoModelFactory):
    city = factory.SubFactory(CityFactory)
    name_cn = factory.Sequence(lambda n: '监测站{}'.format(n))
    longitude = factory.LazyFunction(lambda: Decimal('{}.{}'.format(
        random.randint(0, 9999),
        random.randint(0, 9999),
    )))
    latitude = factory.LazyFunction(lambda: Decimal('{}.{}'.format(
        random.randint(0, 9999),
        random.randint(0, 9999),
    )))

    class Meta:
        model = models.Station


class UpdateDtmFieldsMixin(object):

    dtm_counter = 0

    def __new__(cls, update_dtm=None, *args, **kwargs):
        fields = super(UpdateDtmFieldsMixin, cls).__new__(cls, *args, **kwargs)
        if update_dtm is None:
            fields['update_dtm'] = datetime(2016, 5, 10, tzinfo=pytz.utc) + timedelta(hours=cls.dtm_counter)
            cls.dtm_counter += 1
        else:
            fields['update_dtm'] = update_dtm

        return fields


class PrimaryPollutantFieldsMixin(object):

    def __new__(cls, primary_pollutant=None, *args, **kwargs):
        fields = super(PrimaryPollutantFieldsMixin, cls).__new__(cls, *args, **kwargs)
        if primary_pollutant is None:
            choices = list(zip(*models.PrimaryPollutantItem.PRIMARY_POLLUTANT_CHOICES))[0]
            combs = list(combinations(choices, random.randint(1, len(choices))))
            polls = combs[random.randint(0, len(combs) - 1)]
            fields['primary_pollutant'] = list(polls) if len(polls) > 1 else polls[0]
        else:
            fields['primary_pollutant'] = primary_pollutant

        return fields


class RecordFieldsFactory(object):

    quality_counter = 0

    def __new__(cls, *args, **kwargs):
        if 'quality' not in kwargs:
            quality_values = list(zip(*models.RecordFields.QUALITY_LEVEL_CHOICES))[0]
            n = cls.quality_counter
            cls.quality_counter = (n + 1) % len(quality_values)
            quality = quality_values[n]
        else:
            quality = kwargs['quality']

        return {
            'aqi': kwargs['aqi'] if 'aqi' in kwargs else Decimal(random.randint(30, 200)),
            'co': kwargs['co'] if 'co' in kwargs else Decimal(random.randint(10, 150)) / Decimal(100),
            'no2': kwargs['no2'] if 'no2' in kwargs else Decimal(random.randint(20, 100)),
            'o3': kwargs['o3'] if 'o3' in kwargs else Decimal(random.randint(20, 250)),
            'o3_8h': kwargs['o3_8h'] if 'o3_8h' in kwargs else Decimal(random.randint(20, 250)),
            'pm10': kwargs['pm10'] if 'pm10' in kwargs else Decimal(random.randint(20, 150)),
            'pm2_5': kwargs['pm2_5'] if 'pm2_5' in kwargs else Decimal(random.randint(20, 150)),
            'so2': kwargs['so2'] if 'so2' in kwargs else Decimal(random.randint(20, 150)),
            'quality': quality,
        }


class CityRecordFieldsFactory(UpdateDtmFieldsMixin, RecordFieldsFactory):
    pass


class StationRecordFieldsWithPollutants(PrimaryPollutantFieldsMixin, RecordFieldsFactory):

    station_name_counter = 0

    def __new__(cls, name_cn=None, *args, **kwargs):
        fields = super(StationRecordFieldsWithPollutants, cls).__new__(cls, *args, **kwargs)
        if name_cn is None:
            name_cn = '监测点{}'.format(cls.station_name_counter)
            cls.station_name_counter += 1

        return {name_cn: fields}


class InfoDictFactory(PrimaryPollutantFieldsMixin, UpdateDtmFieldsMixin, RecordFieldsFactory):

    area_name_counter = 0

    def __new__(cls, stations=None, station_num=5, city=None, area_cn=None, area_en=None, *args, **kwargs):
        city_dict = super(InfoDictFactory, cls).__new__(cls, *args, **kwargs)

        update_dtm = city_dict['update_dtm']
        del city_dict['update_dtm']

        if city is None:
            if area_cn is None:
                city_dict['area_cn'] = '城市{}'.format(cls.area_name_counter)
            else:
                city_dict['area_cn'] = area_cn

            if area_en is None:
                city_dict['area_en'] = 'city{}'.format(cls.area_name_counter)
            else:
                city_dict['area_en'] = area_cn
        else:
            city_dict['area_cn'] = city.name_cn
            city_dict['area_en'] = city.name_en

        if area_cn is None or area_en is None:
            cls.area_name_counter += 1
            
        station_dicts = {}
        if stations is not None:
            for station in stations:
                if isinstance(station, models.Station):
                    name_cn = station.name_cn
                elif isinstance(station, str):
                    name_cn = station
                else:
                    raise ValueError('Invalid stations item type.')

                station_dicts.update(StationRecordFieldsWithPollutants(name_cn=name_cn))
            station_num = min(station_num - len(stations), 0)

        for i in range(station_num):
            station_dicts.update(StationRecordFieldsWithPollutants())

        return {
            'city': city_dict,
            'stations': station_dicts,
            'update_dtm': update_dtm,
        }


class BaseRecordFactory(DjangoModelFactory):

    aqi = factory.LazyFunction(lambda: Decimal(random.randint(30, 200)))
    co = factory.LazyFunction(lambda: Decimal(random.randint(10, 150) / 100))
    no2 = factory.LazyFunction(lambda: Decimal(random.randint(20, 100)))
    o3 = factory.LazyFunction(lambda: Decimal(random.randint(20, 250)))
    o3_8h = factory.LazyFunction(lambda: Decimal(random.randint(20, 250)))
    pm10 = factory.LazyFunction(lambda: Decimal(random.randint(20, 150)))
    pm2_5 = factory.LazyFunction(lambda: Decimal(random.randint(20, 150)))
    so2 = factory.LazyFunction(lambda: Decimal(random.randint(20, 150)))
    quality = factory.Iterator(list(zip(*models.RecordFields.QUALITY_LEVEL_CHOICES))[0])

    @factory.lazy_attribute
    def aqhi(self):
        return Decimal(str(
            round(utils.calculate_aqhi(float(self.pm10), float(self.no2)), 2)
        ))


class CityRecordFactory(BaseRecordFactory):
    city = factory.SubFactory(CityFactory)
    update_dtm = factory.Sequence(lambda n: datetime(2016, 5, 10, tzinfo=pytz.utc) + timedelta(hours=n))
    primary_pollutant = factory.RelatedFactory(
        'aqhi.airquality.tests.factories.CityPrimaryPollutantItemFactory',
        'city_record'
    )

    class Meta:
        model = models.CityRecord


class EstimatedCityRecordFactory(BaseRecordFactory):
    original_record = factory.SubFactory(CityRecordFactory)
    primary_pollutant = factory.RelatedFactory(
        'aqhi.airquality.tests.factories.EstimatedCityPrimaryPollutantItemFactory',
        'city_record'
    )

    class Meta:
        model = models.EstimatedCityRecord


class StationRecordFactory(BaseRecordFactory):
    station = factory.SubFactory(StationFactory)
    city_record = factory.SubFactory(CityRecordFactory)
    primary_pollutant = factory.RelatedFactory(
        'aqhi.airquality.tests.factories.StationPrimaryPollutantItemFactory',
        'station_record'
    )

    class Meta:
        model = models.StationRecord


class EstimatedStationRecordFactory(BaseRecordFactory):
    original_record = factory.SubFactory(StationRecordFactory)
    primary_pollutant = factory.RelatedFactory(
        'aqhi.airquality.tests.factories.EstimatedStationPrimaryPollutantItemFactory',
        'station_record'
    )

    class Meta:
        model = models.EstimatedStationRecord


class PrimaryPollutantItemFactory(DjangoModelFactory):
    pollutant = factory.Iterator(
        list(zip(*models.PrimaryPollutantItem.PRIMARY_POLLUTANT_CHOICES))[0]
    )


class CityPrimaryPollutantItemFactory(PrimaryPollutantItemFactory):
    city_record = factory.SubFactory(CityRecordFactory)

    class Meta:
        model = models.CityPrimaryPollutantItem


class StationPrimaryPollutantItemFactory(PrimaryPollutantItemFactory):
    station_record = factory.SubFactory(StationRecordFactory)

    class Meta:
        model = models.StationPrimaryPollutantItem


class EstimatedCityPrimaryPollutantItemFactory(PrimaryPollutantItemFactory):
    city_record = factory.SubFactory(EstimatedCityRecordFactory)

    class Meta:
        model = models.EstimatedCityPrimaryPollutantItem


class EstimatedStationPrimaryPollutantItemFactory(PrimaryPollutantItemFactory):
    station_record = factory.SubFactory(EstimatedStationRecordFactory)

    class Meta:
        model = models.EstimatedStationPrimaryPollutantItem
