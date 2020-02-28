import pdfkit
from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse
from django.template.response import SimpleTemplateResponse
from django.views.generic import TemplateView

__all__ = [
    "PLCChartView",
]


class PLCChartView(TemplateView):
    template_name = "devices/chart.html"

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
        pdf = pdfkit.from_string(content, False, options=options)
        response = HttpResponse(pdf, content_type='application/pdf')
        return response
