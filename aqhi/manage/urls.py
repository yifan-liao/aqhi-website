# -*- coding: utf-8 -*-
from django.conf.urls import url
from django.views.generic import TemplateView

urlpatterns = [
    url(
        regex=r'^$',
        view=TemplateView.as_view(template_name='manage/home.html'),
        name="home"
    ),
    url(
        regex=r'^charts$',
        view=TemplateView.as_view(template_name='manage/charts.html'),
        name="charts",
    ),
]
