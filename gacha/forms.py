from django import forms
from django.core.files.uploadedfile import UploadedFile

from .models import Banner, Item, CATEGORIA_ITEM

CANTIDAD_CHOICES = [
    (1, 'x1'),
    (10, 'x10'),
]

EXTENSIONES_IMAGEN = ('.jpg', '.jpeg', '.png', '.webp')
TAMANO_MAXIMO_IMAGEN = 2 * 1024 * 1024  # 2 MB


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


class ItemForm(forms.ModelForm):
    """Alta de un personaje o arma desde la pagina (sin pasar por la terminal)."""

    class Meta:
        model = Item
        fields = ['nombre', 'categoria', 'rareza', 'banner', 'imagen', 'es_destacado']
        labels = {
            'nombre': 'Nombre',
            'categoria': 'Categoría',
            'rareza': 'Rareza',
            'banner': 'Banner',
            'imagen': 'Imagen',
            'es_destacado': 'Item destacado (rate-up)',
        }
        help_texts = {
            'imagen': 'Opcional. JPG, PNG o WEBP de hasta 2 MB. Si no subes nada se usa una imagen genérica.',
            'es_destacado': 'Solo un 5 estrellas puede serlo, y cada banner limitado tiene uno solo.',
        }
        widgets = {
            'imagen': forms.FileInput(attrs={'accept': 'image/png,image/jpeg,image/webp'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['banner'].empty_label = 'Selecciona un banner'
        self.fields['categoria'].choices = [('', 'Selecciona una categoría')] + list(CATEGORIA_ITEM)
        self.fields['rareza'].choices = [('', 'Selecciona la rareza'), (4, '4 estrellas'), (5, '5 estrellas')]

    # ---- validaciones de un solo campo ----
    def clean_nombre(self):
        nombre = ' '.join(self.cleaned_data['nombre'].split())
        if len(nombre) < 2:
            raise forms.ValidationError('El nombre debe tener al menos 2 caracteres.')
        repetidos = Item.objects.filter(nombre__iexact=nombre).exclude(pk=self.instance.pk)
        if repetidos.exists():
            raise forms.ValidationError(f'Ya existe un item llamado «{nombre}». Usa otro nombre.')
        return nombre

    def clean_imagen(self):
        imagen = self.cleaned_data.get('imagen')
        # Solo se revisa cuando realmente se subio un archivo (si no, queda la imagen por defecto).
        if isinstance(imagen, UploadedFile):
            if not imagen.name.lower().endswith(EXTENSIONES_IMAGEN):
                raise forms.ValidationError('Formato no permitido: usa JPG, PNG o WEBP.')
            if imagen.size > TAMANO_MAXIMO_IMAGEN:
                raise forms.ValidationError('La imagen pesa más de 2 MB. Sube una más liviana.')
        return imagen

    # ---- reglas del negocio que cruzan varios campos ----
    def clean(self):
        datos = super().clean()
        banner = datos.get('banner')
        categoria = datos.get('categoria')
        rareza = datos.get('rareza')
        destacado = datos.get('es_destacado')

        if banner and categoria and banner.tipo != 'permanente' and banner.tipo != categoria:
            admite = 'personajes' if banner.tipo == 'personaje' else 'armas'
            self.add_error(
                'categoria',
                f'El banner «{banner.nombre}» solo admite {admite}. '
                'Cambia la categoría o elige otro banner.',
            )

        if banner and rareza:
            if destacado:
                if int(rareza) != 5:
                    self.add_error('es_destacado', 'Solo un item de 5 estrellas puede ser el destacado.')
                elif banner.tipo == 'permanente':
                    self.add_error('es_destacado', 'El banner permanente no tiene item destacado.')
                else:
                    actual = banner.items.filter(es_destacado=True).exclude(pk=self.instance.pk).first()
                    if actual:
                        self.add_error(
                            'es_destacado',
                            f'El banner «{banner.nombre}» ya tiene un destacado ({actual.nombre}).',
                        )
            elif int(rareza) == 5 and banner.tipo != 'permanente':
                self.add_error(
                    'es_destacado',
                    'En un banner limitado el 5 estrellas debe ser el destacado. '
                    'Marca la casilla o elige el banner permanente.',
                )
        return datos


ORDEN_CATALOGO = {
    'recientes': ('-id',),
    'rareza': ('-rareza', 'nombre'),
    'nombre': ('nombre',),
}


class FiltroCatalogoForm(forms.Form):
    """Filtros del catalogo (se envian por GET, todos opcionales)."""

    q = forms.CharField(required=False, max_length=100, label='Buscar')
    categoria = forms.ChoiceField(
        required=False, label='Categoría',
        choices=[('', 'Todas')] + list(CATEGORIA_ITEM),
    )
    rareza = forms.ChoiceField(
        required=False, label='Rareza',
        choices=[('', 'Todas'), ('5', '5 estrellas'), ('4', '4 estrellas')],
    )
    banner = forms.ModelChoiceField(
        queryset=Banner.objects.all(), required=False,
        label='Banner', empty_label='Todos',
    )
    orden = forms.ChoiceField(
        required=False, label='Orden',
        choices=[('recientes', 'Más recientes'), ('rareza', 'Rareza'), ('nombre', 'Nombre')],
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for nombre, campo in self.fields.items():
            clase = 'form-control' if nombre == 'q' else 'form-select'
            campo.widget.attrs['class'] = clase
        self.fields['q'].widget.attrs['placeholder'] = 'Buscar por nombre'
