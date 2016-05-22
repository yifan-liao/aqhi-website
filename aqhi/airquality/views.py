import copy

from rest_framework import viewsets
from rest_framework import filters as drf_filters
from rest_framework.utils.serializer_helpers import ReturnDict

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
# ViewSets
# ===================================================================
# City and Station ViewSets
# -------------------------------------------------------------------
class CityViewSet(FilterFieldsMixin, viewsets.ReadOnlyModelViewSet):
    queryset = models.City.objects.all()
    serializer_class = serializers.CitySerializer
    filter_backends = (drf_filters.DjangoFilterBackend, )
    filter_class = filters.CityFilter


class StationViewSet(FilterFieldsMixin, viewsets.ReadOnlyModelViewSet):
    queryset = models.Station.objects.all()
    serializer_class = serializers.StationSerializer
    filter_backends = (drf_filters.DjangoFilterBackend, )
    filter_class = filters.StationFilter


# CityRecord ViewSet
# -------------------------------------------------------------------
class CityRecordViewSet(FilterFieldsMixin, viewsets.ReadOnlyModelViewSet):
    queryset = models.CityRecord.objects.all()
    serializer_class = serializers.CityRecordSerializer
    filter_backends = (drf_filters.DjangoFilterBackend, )
    filter_class = filters.CityRecordFilter


# StationRecord ViewSet
# -------------------------------------------------------------------
class StationRecordViewSet(FilterFieldsMixin, viewsets.ReadOnlyModelViewSet):
    queryset = models.StationRecord.objects.all()
    serializer_class = serializers.StationRecordSerializer
    filter_backends = (drf_filters.DjangoFilterBackend, )
    filter_class = filters.StationRecordFilter
