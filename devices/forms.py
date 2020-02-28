from django import forms

from .models import PLC


class PLCChartForm(forms.Form):
    date_min = forms.DateField(required=True, label="From")
    date_max = forms.DateField(required=True, label="To")
    plcs = forms.ModelMultipleChoiceField(
        PLC.objects.all(), widget=forms.CheckboxSelectMultiple())
