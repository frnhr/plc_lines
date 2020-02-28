import json
import os
from datetime import timedelta, datetime

import pdfkit
import pytz
from django.conf import settings
from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse
from django.template.response import SimpleTemplateResponse
from django.utils.timezone import now
from django.views.generic import FormView

from .forms import PLCChartForm

__all__ = [
    "PLCChartView",
]

from .models import PLC


class PLCChartView(FormView):
    template_name = "devices/chart.html"
    form_class = PLCChartForm

    def dispatch(self, request: WSGIRequest, *args, **kwargs) -> HttpResponse:
        """Mark this view as safe to embed in iframes."""
        response = super().dispatch(request, *args, **kwargs)
        response.xframe_options_exempt = True
        return response

    def get(self, request: WSGIRequest, *args, **kwargs) -> HttpResponse:
        response = super().get(request, *args, **kwargs)
        if request.GET.get("export") == "pdf":
            return self.export_to_pdf(response)
        return response

    def get_form_kwargs(self) -> dict:
        """
        Careful! We are using the form with query params and GET method.
        """
        kwargs = {
            'initial': self.get_initial(),
            'prefix': self.get_prefix(),
        }

        if self.request.GET.get("date_min") is not None:
            kwargs.update({
                'data': self.request.GET,
            })
        return kwargs

    def get_initial(self):
        today = now().date()
        return {
            "date_min": today - timedelta(days=31),
            "date_max": today,
            "plcs": PLC.objects.all(),
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["chart_data"] = self.get_chart_data()
        return context

    @staticmethod
    def export_to_pdf(response: SimpleTemplateResponse) -> HttpResponse:
        response.render()
        content = response.rendered_content.strip()

        options = {
            'page-size': 'A4',
            'javascript-delay': 100,
            'no-stop-slow-scripts': None,
            # 'debug-javascript': None,
            "enable-javascript": None,
            'margin-top': '0.75in',
            'margin-right': '0.75in',
            'margin-bottom': '0.75in',
            'margin-left': '0.75in',
            'encoding': "UTF-8",
        }
        css = os.path.join(
            settings.BASE_DIR, "devices/static/devices/pdf_chart.css")
        pdf = pdfkit.from_string(content, False, options=options, css=css)
        response = HttpResponse(pdf, content_type='application/pdf')
        return response

    def get_chart_data(self):
        form = self.get_form()
        if not form.is_valid():
            data = form.initial
        else:
            data = form.cleaned_data
        start = data["date_min"]
        end = data["date_max"]
        date_range = (start + timedelta(days=x)
                      for x in range(0, (end - start).days))
        plcs = data["plcs"]
        plc_ids = plcs.values_list("id", flat=True)
        uptimes = PLC.get_multiple_uptimes(plc_ids, start, end)
        data = [
            {
                "symbol": f"{plc}",
                "date": date.strftime("%Y-%m-%d"),
                "uptime": uptimes.get(plc.id, {}).get(date, None),
            }
            for i, date in enumerate(date_range)
            for plc in PLC.objects.all()
        ]
        return json.dumps(data)
