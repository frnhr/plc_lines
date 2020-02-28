from django import forms


class PLCChartForm(forms.Form):
    date_min = forms.DateField(required=True, label="From")
    date_max = forms.DateField(required=True, label="To")
