from django.urls import path

from . import views


app_name = "devices"
urlpatterns = [
    path("chart", views.PLCChartView.as_view(), name="plc_chart"),
]
