import copy
import datetime

from django.http import Http404
from django.core.cache import cache
from django.utils.encoding import force_text
from django.db.models.signals import post_save, post_delete

from rest_framework import viewsets, generics
from rest_framework import filters as drf_filters
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.utils.serializer_helpers import ReturnDict
from rest_framework_extensions.cache.mixins import RetrieveCacheResponseMixin
from rest_framework_extensions.key_constructor.constructors import (
    DefaultObjectKeyConstructor, DefaultListKeyConstructor
)
from rest_framework_extensions.key_constructor import bits

from . import models, serializers, filters


# ===================================================================
# Mixins
# ===================================================================
class FilterFieldsMixin(object):
    def finalize_response(self, request, response, *args, **kwargs):
        res = super(FilterFieldsMixin, self).finalize_response(request, response, *args, **kwargs)
        params = request.query_params
        if 'fields' in params:
            if "count" in res.data and "previous" in res.data and "next" in res.data and "results" in res.data:
                data_type = 'paged'
            elif isinstance(res.data, list):
                data_type = 'list'
            else:
                data_type = 'object'

            if data_type == 'list':
                data = res.data
                for i, obj in enumerate(data):
                    filtered_obj = type(obj)()
                    self._filter_instance(
                        obj,
                        self._generate_structure(params['fields'].split(',')),
                        filtered_obj
                    )
                    data[i] = filtered_obj
                res.data = data
            elif data_type == 'object':
                filtered_data = ReturnDict(serializer=res.data.serializer)
                self._filter_instance(
                    res.data,
                    self._generate_structure(params['fields'].split(',')),
                    filtered_data
                )
                res.data = filtered_data
            else:
                data = res.data['results']
                for i, obj in enumerate(data):
                    filtered_obj = type(obj)()
                    self._filter_instance(
                        obj,
                        self._generate_structure(params['fields'].split(',')),
                        filtered_obj
                    )
                    data[i] = filtered_obj

        return res

    @classmethod
    def _generate_structure(cls, field_list):
        struct = {}
        for field in field_list:
            if '__' not in field:
                if field not in struct:
                    struct[field] = None
            else:
                field, subfield = field.split('__', maxsplit=1)
                if field not in struct or not isinstance(struct[field], dict):
                    struct[field] = {}
                struct[field].update(cls._generate_structure([subfield]))
        return struct

    @classmethod
    def _filter_instance(cls, instance_dict, filter_dict, result_dict, preserved_fields=('url', 'id')):
        for name, field in instance_dict.items():
            if not isinstance(field, dict):
                if name in filter_dict:
                    result_dict[name] = instance_dict[name]
                elif name in preserved_fields:
                    result_dict[name] = instance_dict[name]
            elif name in filter_dict:
                if isinstance(filter_dict[name], dict):
                    result_dict[name] = {}
                    cls._filter_instance(field, filter_dict[name], result_dict[name])
                else:
                    result_dict[name] = copy.deepcopy(field)


# ===================================================================
# Caching
# ===================================================================
# Custom Cache Key Constructor
# -------------------------------------------------------------------
class UpdateAtKeyBit(bits.KeyBitBase):
    def __init__(self, update_name, *args, **kwargs):
        super(UpdateAtKeyBit, self).__init__(*args, **kwargs)
        self.cache_key = '{}_updated_at_timestamp'.format(update_name)

    def get_data(self, params, view_instance, view_method, request, args, kwargs):
        value = cache.get(self.cache_key, None)
        if not value:
            value = datetime.datetime.utcnow()
            cache.set(self.cache_key, value)
        return force_text(value)


class UpdateAtObjectKeyConstructor(DefaultObjectKeyConstructor):
    def __init__(self, update_name, *args, **kwargs):
        super(UpdateAtObjectKeyConstructor, self).__init__(*args, **kwargs)
        self.bits['update_at'] = UpdateAtKeyBit(update_name)


class UpdateAtListKeyConstructor(DefaultListKeyConstructor):
    def __init__(self, update_name, *args, **kwargs):
        super(UpdateAtListKeyConstructor, self).__init__(*args, **kwargs)
        self.bits['update_at'] = UpdateAtKeyBit(update_name)


# Latest CityRecord Key Constructor
# -------------------------------------------------------------------
class LatestCityRecordKeyConstructor(UpdateAtObjectKeyConstructor):
    city = bits.QueryParamsKeyBit(['city'])


# ===================================================================
# ViewSets
# ===================================================================
# City and Station ViewSets
# -------------------------------------------------------------------
class CityViewSet(FilterFieldsMixin, viewsets.ReadOnlyModelViewSet):
    queryset = models.City.objects.all()
    serializer_class = serializers.CitySerializer
    filter_backends = (drf_filters.DjangoFilterBackend,)
    filter_class = filters.CityFilter


class StationViewSet(FilterFieldsMixin, viewsets.ReadOnlyModelViewSet):
    queryset = models.Station.objects.all()
    serializer_class = serializers.StationSerializer
    filter_backends = (drf_filters.DjangoFilterBackend,)
    filter_class = filters.StationFilter


# CityRecord ViewSet
# -------------------------------------------------------------------
class CityRecordViewSet(FilterFieldsMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = serializers.CityRecordSerializer
    filter_backends = (drf_filters.DjangoFilterBackend,)
    filter_class = filters.CityRecordFilter

    def get_queryset(self):
        return models.CityRecord.objects.select_related('city').prefetch_related('primary_pollutants')
        # return models.CityRecord.objects.all()


# Latest city record view
# -------------------------------------------------------------------
class LatestCityRecordView(FilterFieldsMixin,
                           generics.RetrieveAPIView):
    queryset = models.CityRecord.objects.all()
    serializer_class = serializers.CityRecordSerializer
    #object_cache_key_func = LatestCityRecordKeyConstructor(update_name='city')

    def get_object(self):
        queryset = self.get_queryset()

        city_en = self.request.query_params.get('city', None)
        if city_en is None:
            return None
        try:
            obj = queryset.latest_record_in(city_en)
        except queryset.model.DoesNotExist:
            raise Http404('No city records found.')
        if obj is None:
            raise Http404('City {} not found.'.format(city_en))

        return obj


# Average city record view
# -------------------------------------------------------------------
class AverageCityRecordView(APIView):
    def get(self, request, *args, **kwargs):
        params = request.query_params
        city = params.get('city', None)
        city_cn = params.get('city_cn', None)
        start_dtm = params.get('start_dtm', None)
        end_dtm = params.get('end_dtm', None)
        hours = params.get('hours', None)
        avg_field = params.get('avg_field', None)

        return Response()


# StationRecord ViewSet
# -------------------------------------------------------------------
class StationRecordViewSet(FilterFieldsMixin, viewsets.ReadOnlyModelViewSet):
    queryset = models.StationRecord.objects.all()
    serializer_class = serializers.StationRecordSerializer
    filter_backends = (drf_filters.DjangoFilterBackend,)
    filter_class = filters.StationRecordFilter


# Cache Key Invalidation
# -------------------------------------------------------------------
def get_change_update_at_function(update_name):
    def change_api_updated_at(*args, **kwargs):
        cache.set('{}_updated_at_timestamp'.format(update_name), datetime.datetime.utcnow())

    return change_api_updated_at


for model in [models.CityRecord]:
    receiver = get_change_update_at_function(model._meta.model_name)
    post_save.connect(sender=model, receiver=receiver)
    post_delete.connect(sender=model, receiver=receiver)
