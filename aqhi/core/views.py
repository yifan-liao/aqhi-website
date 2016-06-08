# views for main page
import django.template
from django.template import Context
from django.views.generic import TemplateView, View
from django.http import HttpResponseBadRequest, HttpResponse

from aqhi.airquality import models as aq_models


engine = django.template.Engine.get_default()


def render_city_panel(city=None, primary=False, context=None):
    panel_template = engine.get_template('pages/home_citypanel.html')

    if context is not None:
        return panel_template.render(Context(context))
    else:
        assert isinstance(city, aq_models.City), "city is not a City instance."

        filled = False
        collapsed = True
        city_en = city.name_en
        title = city.name_cn

        if primary:
            filled = True
            collapsed = False
            primary = True

        return panel_template.render(Context({
            'filled': filled,
            'collapsed': collapsed,
            'city_en': city_en,
            'title': title,
            'primary': primary
        }))


class HomeView(TemplateView):
    template_name = 'pages/home.html'

    def get_context_data(self, **kwargs):
        context = super(HomeView, self).get_context_data(**kwargs)

        # Construct city panels
        panel_list = []
        # primary panel
        primary_city = aq_models.City.objects.primary()
        if not primary_city.exists():
            return {}
        primary_panel = render_city_panel(city=primary_city, primary=True)
        panel_list.append(primary_panel)

        # other panels
        for city in aq_models.City.objects.principal().order_by('name_cn').exclude(pk=primary_city.pk):
            panel_list.append(render_city_panel(city=city, primary=False))

        context['panel_list'] = panel_list
        return context


class CityPanelView(TemplateView):
    """Return html skeleton for a city panel body."""
    template_name = 'pages/home_citypanel_body.html'

    def get_context_data(self, **kwargs):
        context = super(CityPanelView, self).get_context_data(**kwargs)

        params = self.request.GET
        context['city_en'] = params['city_en']
        return context
