from django.conf.urls import url, include

from rest_framework.routers import DefaultRouter

from aqhi.airquality import views as airquality_views
from . import views as core_views


router = DefaultRouter()
router.register(r'airquality/city', airquality_views.CityViewSet)
router.register(r'airquality/station', airquality_views.StationViewSet)
router.register(r'airquality/city_record', airquality_views.CityRecordViewSet, base_name='city-record')
router.register(r'airquality/station_record', airquality_views.StationRecordViewSet, base_name='station-record')

urlpatterns = [
    url(r'^', include(router.urls)),
    # get city panel html
    url(r'^core/city_panel_body/$', core_views.CityPanelView.as_view(), name='city-panel-body')
]
