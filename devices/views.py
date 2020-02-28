from django.views.generic import TemplateView

__all__ = [
    "PLCChartView",
]


class PLCChartView(TemplateView):
    template_name = "devices/chart.html"

    def dispatch(self, request, *args, **kwargs):
        """Mark this view as safe to embed in iframes."""
        response = super().dispatch(request, *args, **kwargs)
        response.xframe_options_exempt = True
        return response
