from django.db import models as dj_models
from django.db.models import Q

from . import models


class CityQuerySet(dj_models.QuerySet):
    def primary(self):
        return self.filter(name_en='beijing')

    def principal(self):
        return self.filter(Q(name_en='beijing') | Q(name_en='shanghai') | Q(name_en='guangzhou'))


class CityRecordQuerySet(dj_models.QuerySet):
    def recorded_in(self, city=None, name_en=None, name_cn=None):
        if city is not None:
            return self.filter(city=city)
        elif name_en is not None:
            return self.filter(city__name_en=name_en)
        elif name_cn is not None:
            return self.filter(city__name_cn=name_cn)
        else:
            return self

    def latests(self):
        return self.filter(update_dtm=self.latest().update_dtm)


class StationRecordQuerySet(dj_models.QuerySet):
    def recorded_in(self, city=None, name_en=None, name_cn=None):
        if city is not None:
            return self.filter(city_record__city=city)
        elif name_en is not None:
            return self.filter(city_record__city__name_en=name_en)
        elif name_cn is not None:
            return self.filter(city_record__city__name_cn=name_cn)
        else:
            return self

    def latests(self):
        return self.filter(city_record__update_dtm=self.latest().get_update_dtm())
