from django import forms
from .models import Banner

CANTIDAD_CHOICES = [
    (1, 'x1'),
    (10, 'x10'),
]


class SimularTiradaForm(forms.Form):
    banner = forms.ModelChoiceField(
        queryset=Banner.objects.all(),
        label='Banner',
        empty_label='Selecciona un banner',
    )
    cantidad = forms.ChoiceField(
        choices=CANTIDAD_CHOICES,
        label='Cantidad de tiradas',
    )

    def clean_cantidad(self):
        cantidad = int(self.cleaned_data['cantidad'])
        if cantidad not in (1, 10):
            raise forms.ValidationError('La cantidad de tiradas solo puede ser 1 o 10.')
        return cantidad
