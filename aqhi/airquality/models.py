# -*- coding: utf-8 -*-
import copy

from django.db import models, transaction
from django.core.exceptions import ValidationError

from . import querysets


POLL_MAX_DIGITS = 8
POLL_DECIMAL_PLACES = 4
COORD_MAX_DIGITS = 8
COORD_DECIMAL_PLACES = 4


# ===================================================================
# Custom Mixins
# ===================================================================
class ValidateAndCreateWithPollutantsManagerMixin(object):
    def validate_and_create_with_pollutants(self, pollutants=None, **kwargs):
        instance = self.model(**kwargs)

        if pollutants is None:
            instance.full_clean()
            instance.save()
            return instance

        pollutant_item_model = [
            f.related_model
            for f in self.model._meta.get_fields(include_parents=False)
            if f.is_relation and f.one_to_many and issubclass(f.related_model, PrimaryPollutantItem)
            ][0]
        item_record_field_name = [
            f.name
            for f in pollutant_item_model._meta.get_fields()
            if f.many_to_one and issubclass(f.related_model, RecordFields)
            ][0]

        if pollutants == '':
            pollutants = []
        if isinstance(pollutants, str):
            pollutants = [pollutants]

        instance.full_clean()
        with transaction.atomic():
            instance.save()

        items = []
        for p in pollutants:
            item = pollutant_item_model(**{'pollutant': p, item_record_field_name: instance})
            item.full_clean()
            items.append(item)

        with transaction.atomic():
            for item in items:
                item.save()

        return instance


class ValidateAndCreateManagerMixin(object):
    def validate_and_create(self, **kwargs):
        instance = self.model(**kwargs)
        instance.full_clean()
        instance.save()
        return instance


# ===================================================================
# Models
# ===================================================================
# Primary Pollutant Base
# -------------------------------------------------------------------
class PrimaryPollutantItem(models.Model):
    PRIMARY_POLLUTANT_CHOICES = (
        ('co', 'CO/1h'),
        ('no2', 'NO2/1h'),
        ('o3', 'O3/1h'),
        ('o3_8h', 'O3/8h'),
        ('pm10', 'PM10/1h'),
        ('pm2_5', 'PM2.5/1h'),
        ('so2', 'SO2/1h'),
    )
    pollutant = models.CharField(max_length=5, choices=PRIMARY_POLLUTANT_CHOICES)

    class Meta:
        abstract = True


# Primary Pollutants
# -------------------------------------------------------------------
class CityPrimaryPollutantItem(PrimaryPollutantItem):
    city_record = models.ForeignKey('CityRecord',
                                    on_delete=models.CASCADE,
                                    related_name='primary_pollutants',
                                    related_query_name='primary_pollutant')

    class Meta:
        unique_together = ('city_record', 'pollutant')


class StationPrimaryPollutantItem(PrimaryPollutantItem):
    station_record = models.ForeignKey('StationRecord',
                                       on_delete=models.CASCADE,
                                       related_name='primary_pollutants',
                                       related_query_name='primary_pollutant')

    class Meta:
        unique_together = ('station_record', 'pollutant')


class EstimatedCityPrimaryPollutantItem(PrimaryPollutantItem):
    city_record = models.ForeignKey('EstimatedCityRecord',
                                    on_delete=models.CASCADE,
                                    related_name='primary_pollutants',
                                    related_query_name='primary_pollutant')

    class Meta:
        unique_together = ('city_record', 'pollutant')


class EstimatedStationPrimaryPollutantItem(PrimaryPollutantItem):
    station_record = models.ForeignKey('EstimatedStationRecord',
                                       on_delete=models.CASCADE,
                                       related_name='primary_pollutants',
                                       related_query_name='primary_pollutant')

    class Meta:
        unique_together = ('station_record', 'pollutant')


# Record Base
# -------------------------------------------------------------------
class RecordFields(models.Model):

    QUALITY_LEVEL_CHOICES = (
        ('E', 'Excellent'),
        ('G', 'Good'),
        ('LP', 'Lightly Polluted'),
        ('MP', 'Moderately Polluted'),
        ('HP', 'Heavily Polluted'),
        ('SP', 'Severely Polluted')
    )

    aqi = models.DecimalField(max_digits=POLL_MAX_DIGITS, decimal_places=POLL_DECIMAL_PLACES, null=True, blank=True)
    aqhi = models.DecimalField(max_digits=POLL_MAX_DIGITS, decimal_places=POLL_DECIMAL_PLACES, null=True, blank=True)
    co = models.DecimalField(max_digits=POLL_MAX_DIGITS, decimal_places=POLL_DECIMAL_PLACES, null=True, blank=True)
    no2 = models.DecimalField(max_digits=POLL_MAX_DIGITS, decimal_places=POLL_DECIMAL_PLACES, null=True, blank=True)
    o3 = models.DecimalField(max_digits=POLL_MAX_DIGITS, decimal_places=POLL_DECIMAL_PLACES, null=True, blank=True)
    o3_8h = models.DecimalField(max_digits=POLL_MAX_DIGITS, decimal_places=POLL_DECIMAL_PLACES, null=True, blank=True)
    pm10 = models.DecimalField(max_digits=POLL_MAX_DIGITS, decimal_places=POLL_DECIMAL_PLACES, null=True, blank=True)
    pm2_5 = models.DecimalField(max_digits=POLL_MAX_DIGITS, decimal_places=POLL_DECIMAL_PLACES, null=True, blank=True)
    so2 = models.DecimalField(max_digits=POLL_MAX_DIGITS, decimal_places=POLL_DECIMAL_PLACES, null=True, blank=True)
    quality = models.CharField(max_length=2, choices=QUALITY_LEVEL_CHOICES, blank=True)

    class Meta:
        abstract = True


# City Records
# -------------------------------------------------------------------
class CityRecordManager(ValidateAndCreateWithPollutantsManagerMixin, models.Manager):
    pass


class CityRecord(RecordFields):
    city = models.ForeignKey('City', models.CASCADE,
                             related_name="cities_%(app_label)s_%(class)s",)
    update_dtm = models.DateTimeField(db_index=True)
    objects = CityRecordManager.from_queryset(querysets.CityRecordQuerySet)()

    class Meta:
        unique_together = ('city', 'update_dtm')
        get_latest_by = 'update_dtm'

    def __str__(self):
        return '{city} on {dtm}'.format(city=self.city, dtm=self.update_dtm.strftime('%Y-%m-%d-%H-%M'))


class EstimatedCityRecordManager(ValidateAndCreateManagerMixin,
                                 ValidateAndCreateWithPollutantsManagerMixin,
                                 models.Manager):
    pass


class EstimatedCityRecord(RecordFields):
    original_record = models.OneToOneField('CityRecord', models.CASCADE,
                                           related_name='estimated_record')
    objects = EstimatedCityRecordManager()


# Station Records
# -------------------------------------------------------------------
class StationRecordManager(ValidateAndCreateWithPollutantsManagerMixin, models.Manager):
    pass


class StationRecord(RecordFields):
    city_record = models.ForeignKey('CityRecord', models.CASCADE,
                                    related_name="station_records")
    station = models.ForeignKey('Station', models.CASCADE,
                                related_name="stations_%(app_label)s_%(class)s",)

    objects = StationRecordManager.from_queryset(querysets.StationRecordQuerySet)()

    class Meta:
        unique_together = ('city_record', 'station')
        get_latest_by = 'city_record__update_dtm'

    def get_update_dtm(self):
        return self.city_record.update_dtm

    def get_city(self):
        return self.city_record.city

    def __str__(self):
        return '{station}-{dtm}'.format(station=self.station, dtm=self.city_record.update_dtm)


class EstimatedStationRecordManager(ValidateAndCreateManagerMixin,
                                    ValidateAndCreateWithPollutantsManagerMixin,
                                    models.Manager):
    pass


class EstimatedStationRecord(RecordFields):
    original_record = models.OneToOneField('StationRecord', models.CASCADE,
                                           related_name='estimated_record')
    objects = EstimatedStationRecordManager()


# Station and City
# -------------------------------------------------------------------
class CityManager(ValidateAndCreateManagerMixin, models.Manager):
    pass


class City(models.Model):
    name_en = models.CharField(max_length=30, primary_key=True)
    name_cn = models.CharField(max_length=50)
    longitude = models.DecimalField(max_digits=COORD_MAX_DIGITS, decimal_places=COORD_DECIMAL_PLACES, null=True, blank=True)
    latitude = models.DecimalField(max_digits=COORD_MAX_DIGITS, decimal_places=COORD_DECIMAL_PLACES, null=True, blank=True)

    objects = CityManager.from_queryset(querysets.CityQuerySet)()

    def clean(self):
        # name_en should be case insensitive
        self.name_en = self.name_en.lower()

    def __str__(self):
        return '{en}/{cn}'.format(en=self.name_en, cn=self.name_cn)


class StationManager(ValidateAndCreateManagerMixin, models.Manager):
    pass


class Station(models.Model):
    city = models.ForeignKey('City', related_name='stations', related_query_name='station')
    name_cn = models.CharField(max_length=50)
    longitude = models.DecimalField(max_digits=COORD_MAX_DIGITS, decimal_places=COORD_DECIMAL_PLACES, null=True, blank=True)
    latitude = models.DecimalField(max_digits=COORD_MAX_DIGITS, decimal_places=COORD_DECIMAL_PLACES, null=True, blank=True)

    objects = StationManager()

    class Meta:
        unique_together = ('city', 'name_cn')

    def __str__(self):
        return '{name} in {city}'.format(name=self.name_cn, city=self.city)


# ===================================================================
# Utils
# ===================================================================
def create_city_record(info_dict):
    """
    Save the info dict to database as a city record with any necessary station record.
    The expecting dict is almost the same as the dict returned by extractors.aggregate_parsed_dict but it has
    an extra field 'area_en' in 'city' dict, which is for uniquely locate the city object.

    First, if city does not exist in database, the error type is 'CityNotFound' with its English name in info.
    {'success': 0, 'error_type': 'CityNotFound', 'info': 'beijing'}
    Second, it will check the uniqueness of the update_dtm field. If the check fails, it will return
    {'success': 0, 'error_type': 'UniquenessError', 'info': datetime_object}.
    Third, if any station of the city does not exist, error type is 'StationNotFound' with a list of missing
    station's Chinese names.
    {'success': 0, 'error_type': 'StationNotFound', 'info': [name1, name2, ...]}
    Finally, model level validation will be run, so ValidationError or ValueError may be raised:
    {'success': 0, 'error_type': 'ValidationError', 'info': message_dict}
    {'success': 0, 'error_type': 'ValueError', 'info': '...'}

    The successful return is {'success': 1, 'info': the created CityRecord instance}

    This operation is atomic.

    :param info_dict: the dict returned by extractors.aggregate_parsed_dict
    :return: a dict showing the success of the saving.
    """
    city_dict = info_dict['city']
    city_name_en = city_dict['area_en']
    # Check city's existence
    city = City.objects.filter(name_en=city_name_en)
    if not city.exists():
        return {'success': 0, 'error_type': 'CityNotFound', 'info': city_name_en}
    city = city[0]

    # Check uniqueness of this record
    update_dtm = info_dict['update_dtm']
    if CityRecord.objects.filter(city=city, update_dtm=update_dtm).exists():
        return {'success': 0, 'error_type': 'UniquenessError', 'info': update_dtm}

    # Check stations' existence
    station_names = list(info_dict['stations'])
    stations = []
    missing_station = []
    for station_name in station_names:
        station = Station.objects.filter(city=city, name_cn=station_name)
        if not station.exists():
            missing_station.append(station_name)
        else:
            stations.append(station[0])
    if missing_station:
        return {'success': 0, 'error_type': 'StationNotFound', 'info': missing_station}

    # Begin to save!
    # First prepare the arguments to create the CityRecord
    city_dict = copy.deepcopy(city_dict)
    del city_dict['area_en']
    del city_dict['area_cn']
    city_dict['update_dtm'] = update_dtm

    city_dict['pollutants'] = city_dict.pop('primary_pollutant')

    city_dict['city'] = city

    try:
        with transaction.atomic():
            # Create CityRecord
            city_record = CityRecord.objects.validate_and_create_with_pollutants(**city_dict)
            # Create StationRecords
            for i, station in enumerate(stations):
                station_dict = copy.deepcopy(info_dict['stations'][station_names[i]])
                station_dict['station'] = station
                station_dict['city_record'] = city_record
                station_dict['pollutants'] = station_dict.pop('primary_pollutant')
                StationRecord.objects.validate_and_create_with_pollutants(**station_dict)
    except ValidationError as e:
        return {'success': 0, 'error_type': 'ValidationError', 'info': e.message_dict if hasattr(e, 'message_dict') else str(e)}
    except ValueError as e:
        return {'success': 0, 'error_type': 'ValueError', 'info': str(e)}

    return {'success': 1, 'info': city_record}
