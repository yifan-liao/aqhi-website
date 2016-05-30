from rest_framework import serializers

from . import models


# ===================================================================
# Serializers
# ===================================================================
# City and Station Serializers
# -------------------------------------------------------------------
class CitySerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = models.City
        fields = ('url', 'name_en', 'name_cn', 'longitude', 'latitude')
        extra_kwargs = {
            'url': {'view_name': 'api:city-detail'}
        }


class StationSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = models.Station
        fields = ('url', 'id', 'name_cn', 'longitude', 'latitude')
        extra_kwargs = {
            'url': {'view_name': 'api:station-detail'}
        }


# Primary Pollutant Serializer
# -------------------------------------------------------------------
class CityPrimaryPollutantSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = models.CityPrimaryPollutantItem
        fields = ('pollutant', )


# CityRecord Serializer
# -------------------------------------------------------------------
class CityRecordSerializer(serializers.HyperlinkedModelSerializer):

    city = CitySerializer(read_only=True)
    primary_pollutants = CityPrimaryPollutantSerializer(many=True, read_only=True)

    class Meta:
        model = models.CityRecord
        fields = ('url', 'id', 'update_dtm', 'city', 'primary_pollutants',
                  'aqhi', 'aqi', 'co', 'no2', 'o3', 'o3_8h', 'pm10', 'pm2_5', 'so2', 'quality')
        extra_kwargs = {
            'url': {'view_name': 'api:city-record-detail'}
        }


class StationRecordSerializer(serializers.HyperlinkedModelSerializer):

    station = StationSerializer(read_only=True)
    update_dtm = serializers.DateTimeField(source='get_update_dtm')

    class Meta:
        model = models.StationRecord
        fields = ('url', 'id', 'station', 'city_record', 'update_dtm',
                  'aqhi', 'aqi', 'co', 'no2', 'o3', 'o3_8h', 'pm10', 'pm2_5', 'so2', 'quality')
        extra_kwargs = {
            'url': {'view_name': 'api:station-record-detail'},
            'city_record': {'view_name': 'api:city-record-detail'}
        }


# AvgCityRecord Serializer
# -------------------------------------------------------------------
class AverageCityRecordSerializer(serializers.Serializer):

    datetime = serializers.DateTimeField(read_only=True)
    aqhi = serializers.DecimalField(max_digits=models.POLL_MAX_DIGITS, decimal_places=models.POLL_DECIMAL_PLACES,
                                    required=False, read_only=True)
    aqi = serializers.DecimalField(max_digits=models.POLL_MAX_DIGITS, decimal_places=models.POLL_DECIMAL_PLACES,
                                   required=False, read_only=True)
    co = serializers.DecimalField(max_digits=models.POLL_MAX_DIGITS, decimal_places=models.POLL_DECIMAL_PLACES,
                                  required=False, read_only=True)
    no2 = serializers.DecimalField(max_digits=models.POLL_MAX_DIGITS, decimal_places=models.POLL_DECIMAL_PLACES,
                                   required=False, read_only=True)
    so2 = serializers.DecimalField(max_digits=models.POLL_MAX_DIGITS, decimal_places=models.POLL_DECIMAL_PLACES,
                                   required=False, read_only=True)
    o3 = serializers.DecimalField(max_digits=models.POLL_MAX_DIGITS, decimal_places=models.POLL_DECIMAL_PLACES,
                                  required=False, read_only=True)
    o3_8h = serializers.DecimalField(max_digits=models.POLL_MAX_DIGITS, decimal_places=models.POLL_DECIMAL_PLACES,
                                     required=False, read_only=True)
    pm10 = serializers.DecimalField(max_digits=models.POLL_MAX_DIGITS, decimal_places=models.POLL_DECIMAL_PLACES,
                                    required=False, read_only=True)
    pm2_5 = serializers.DecimalField(max_digits=models.POLL_MAX_DIGITS, decimal_places=models.POLL_DECIMAL_PLACES,
                                     required=False, read_only=True)
