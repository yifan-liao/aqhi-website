from django.forms.fields import MultipleChoiceField
import django_filters
import django_filters.fields
from django_filters.filters import MultipleChoiceFilter
from rest_framework import filters

from . import models


# ===================================================================
# Custom Filters
# ===================================================================
class CommaSeperatedMultipleFilterMixin(object):
    def sanitize(self, value_list):
        """
        remove empty items in case of ?number=1,,2
        """
        return [v for v in value_list if v != '']

    def customize(self, value):
        return value

    def filter(self, qs, value):
        multiple_vals = value.split(",")
        multiple_vals = self.sanitize(multiple_vals)
        multiple_vals = list(map(self.customize, multiple_vals))
        actual_filter = django_filters.fields.Lookup(multiple_vals, 'in')
        return super(CommaSeperatedMultipleFilterMixin, self).filter(qs, actual_filter)


class CommaSeperatedMultipleCharFilter(CommaSeperatedMultipleFilterMixin, django_filters.CharFilter):
    pass


# ===================================================================
# Filter Sets
# ===================================================================
class CityFilter(filters.FilterSet):
    primary = django_filters.BooleanFilter(False, action=lambda qs, v: qs.primary() if v else qs)
    principal = django_filters.BooleanFilter(False, action=lambda qs, v: qs.principal() if v else qs)

    order_by_field = 'ordering'

    class Meta:
        model = models.City
        fields = ['name_en', 'name_cn']
        order_by = ['name_cn', 'name_en']


class StationFilter(filters.FilterSet):
    city_en = django_filters.CharFilter(name='city__name_en')
    city_cn = django_filters.CharFilter(name='city__name_cn')

    order_by_field = 'ordering'

    class Meta:
        model = models.Station
        fields = ['name_cn']
        order_by = ['name_cn']


class CityRecordFilter(filters.FilterSet):
    update_dtm = django_filters.IsoDateTimeFilter()
    start_dtm = django_filters.IsoDateTimeFilter(name='update_dtm', lookup_expr='gte')
    end_dtm = django_filters.IsoDateTimeFilter(name='update_dtm', lookup_expr='lte')
    city = CommaSeperatedMultipleCharFilter(name='city__name_en')
    city_cn = django_filters.CharFilter(name='city__name_cn')

    order_by_field = 'ordering'

    class Meta:
        model = models.CityRecord
        fields = ['id']
        order_by = ['update_dtm', '-update_dtm',
                    'aqhi', '-aqhi', 'aqi', '-aqi', 'no2', '-no2', 'co', '-co', 'so2', '-so2',
                    'pm2_5', '-pm2_5', 'pm10', '-pm10', 'o3', '-o3', 'o3_8h', '-o3_8h']


class StationRecordFilter(filters.FilterSet):
    update_dtm = django_filters.IsoDateTimeFilter(name='city_record__update_dtm')
    start_dtm = django_filters.IsoDateTimeFilter(name='city_record__update_dtm', lookup_expr='gte')
    end_dtm = django_filters.IsoDateTimeFilter(name='city_record__update_dtm', lookup_expr='lte')
    city = django_filters.CharFilter(name='city_record__city__name_en')
    city_cn = django_filters.CharFilter(name='city_record__city__name_cn')

    order_by_field = 'ordering'

    class Meta:
        model = models.StationRecord
        fields = ['city_record', 'id']
        order_by = ['-update_dtm', 'update_dtm',
                    'aqhi', '-aqhi', 'aqi', '-aqi', 'no2', '-no2', 'co', '-co', 'so2', '-so2',
                    'pm2_5', '-pm2_5', 'pm10', '-pm10', 'o3', '-o3', 'o3_8h', '-o3_8h']


