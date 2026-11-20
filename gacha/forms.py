from PIL import Image

from django import forms
from django.core.files.uploadedfile import UploadedFile

from .models import Banner, Item, CATEGORIA_ITEM, TIPO_BANNER

CANTIDAD_CHOICES = [
    (1, 'x1'),
    (10, 'x10'),
]

EXTENSIONES_IMAGEN = ('.jpg', '.jpeg', '.png', '.webp')
TAMANO_MAXIMO_IMAGEN = 2 * 1024 * 1024

BANNER_IMG_ANCHO_MIN = 1200
BANNER_IMG_ALTO_MIN = 500
BANNER_IMG_RATIO_MIN = 1.7
BANNER_IMG_RATIO_MAX = 3.0
BANNER_IMG_RESOLUCION_TEXTO = (
    f'{BANNER_IMG_ANCHO_MIN}×{BANNER_IMG_ALTO_MIN} px como mínimo, panorámica '
    f'(ancho entre {BANNER_IMG_RATIO_MIN:.1f} y {BANNER_IMG_RATIO_MAX:.1f} veces el alto)'
)


def _validar_formato_y_peso(imagen):
    if isinstance(imagen, UploadedFile):
        if not imagen.name.lower().endswith(EXTENSIONES_IMAGEN):
            raise forms.ValidationError('Formato no permitido: usa JPG, PNG o WEBP.')
        if imagen.size > TAMANO_MAXIMO_IMAGEN:
            raise forms.ValidationError('La imagen pesa más de 2 MB. Sube una más liviana.')
    return imagen


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


class BannerForm(forms.ModelForm):

    class Meta:
        model = Banner
        fields = ['nombre', 'tipo', 'descripcion', 'imagen']
        labels = {
            'nombre': 'Nombre del banner',
            'tipo': 'Tipo de banner',
            'descripcion': 'Descripción',
            'imagen': 'Imagen de portada',
        }
        help_texts = {
            'nombre': 'Entre 3 y 100 caracteres. No puede repetirse.',
            'tipo': 'Personaje limitado: solo personajes y un 5★ destacado (con 50/50). '
                    'Arma limitada: solo armas y un 5★ destacado. '
                    'Permanente: personajes y armas, sin destacado.',
            'descripcion': 'Opcional. Máximo 400 caracteres.',
            'imagen': f'Opcional. JPG, PNG o WEBP de hasta 2 MB, de {BANNER_IMG_RESOLUCION_TEXTO}. '
                      'Si no subes nada se usa una imagen genérica. Para quitar la que ya tiene, '
                      'marca «Clear» y guarda.',
        }
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 4}),
            'imagen': forms.ClearableFileInput(attrs={'accept': 'image/png,image/jpeg,image/webp'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['tipo'].choices = [('', 'Selecciona el tipo')] + list(TIPO_BANNER)

    def clean_nombre(self):
        nombre = ' '.join(self.cleaned_data['nombre'].split())
        if len(nombre) < 3:
            raise forms.ValidationError('El nombre debe tener al menos 3 caracteres.')
        repetidos = Banner.objects.filter(nombre__iexact=nombre).exclude(pk=self.instance.pk)
        if repetidos.exists():
            raise forms.ValidationError(f'Ya existe un banner llamado «{nombre}». Usa otro nombre.')
        return nombre

    def clean_descripcion(self):
        descripcion = self.cleaned_data.get('descripcion', '').strip()
        if len(descripcion) > 400:
            raise forms.ValidationError(
                f'La descripción tiene {len(descripcion)} caracteres; el máximo es 400.'
            )
        return descripcion

    def clean_imagen(self):
        imagen = _validar_formato_y_peso(self.cleaned_data.get('imagen'))
        if isinstance(imagen, UploadedFile):
            try:
                ancho, alto = Image.open(imagen).size
            finally:
                imagen.seek(0)
            if ancho < BANNER_IMG_ANCHO_MIN or alto < BANNER_IMG_ALTO_MIN:
                raise forms.ValidationError(
                    f'La imagen mide {ancho}×{alto} px; se necesita {BANNER_IMG_RESOLUCION_TEXTO}.'
                )
            ratio = ancho / alto
            if not (BANNER_IMG_RATIO_MIN <= ratio <= BANNER_IMG_RATIO_MAX):
                raise forms.ValidationError(
                    f'La imagen mide {ancho}×{alto} px (proporción {ratio:.2f}:1); se necesita una '
                    f'imagen panorámica, {BANNER_IMG_RESOLUCION_TEXTO}.'
                )
        return imagen

    def clean(self):
        datos = super().clean()
        tipo = datos.get('tipo')
        if self.instance.pk and tipo:
            items = self.instance.items.all()
            if tipo == 'permanente':
                if items.filter(es_destacado=True).exists():
                    self.add_error(
                        'tipo',
                        'El banner permanente no tiene item destacado. '
                        'Quita el destacado de sus items antes de cambiar el tipo.',
                    )
            else:
                admite = 'personajes' if tipo == 'personaje' else 'armas'
                if items.exclude(categoria=tipo).exists():
                    self.add_error(
                        'tipo',
                        f'Este banner tiene items que no son {admite}. '
                        'Muévelos a otro banner antes de cambiar el tipo.',
                    )
                elif items.filter(rareza=5, es_destacado=False).exists():
                    self.add_error(
                        'tipo',
                        'Un banner limitado solo puede tener como 5★ al item destacado. '
                        'Revisa los 5★ de este banner antes de cambiar el tipo.',
                    )
        return datos


class ItemForm(forms.ModelForm):

    class Meta:
        model = Item
        fields = ['nombre', 'categoria', 'rareza', 'banner', 'probabilidad', 'imagen',
                  'ataque_base', 'descripcion', 'es_destacado']
        labels = {
            'nombre': 'Nombre',
            'categoria': 'Categoría',
            'rareza': 'Rareza',
            'banner': 'Banner',
            'probabilidad': 'Probabilidad (1 a 100)',
            'imagen': 'Imagen',
            'ataque_base': 'Ataque base (nivel 90)',
            'descripcion': 'Descripción',
            'es_destacado': 'Item destacado (rate-up)',
        }
        help_texts = {
            'imagen': 'Opcional. JPG, PNG o WEBP de hasta 2 MB. Si no subes nada se usa una imagen genérica.',
            'ataque_base': 'Opcional. Número entero entre 100 y 800 (ATK a nivel 90, sin arma ni ecos en personajes).',
            'descripcion': 'Opcional. Entre 10 y 600 caracteres: rol, elemento, tipo de arma, etc.',
            'es_destacado': 'Solo un 5 estrellas puede serlo, y cada banner limitado tiene uno solo.',
            'probabilidad': 'Mientras más alto el número, más seguido sale este item frente a los '
                            'demás de su misma rareza en el banner. No se usa en el item destacado '
                            '(ese sale por la regla del banner).',
        }
        widgets = {
            'imagen': forms.FileInput(attrs={'accept': 'image/png,image/jpeg,image/webp'}),
            'descripcion': forms.Textarea(attrs={'rows': 4}),
            'probabilidad': forms.NumberInput(attrs={'min': 1, 'max': 100, 'step': 1}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['banner'].empty_label = 'Selecciona un banner'
        self.fields['categoria'].choices = [('', 'Selecciona una categoría')] + list(CATEGORIA_ITEM)
        self.fields['rareza'].choices = [('', 'Selecciona la rareza'), (4, '4 estrellas'), (5, '5 estrellas')]

        self.destacado_fijo = bool(
            self.instance.pk
            and self.instance.es_destacado
            and self.instance.banner.tipo != 'permanente'
        )
        if self.destacado_fijo:
            for nombre in ('banner', 'rareza', 'es_destacado'):
                self.fields[nombre].disabled = True

    def clean_nombre(self):
        nombre = ' '.join(self.cleaned_data['nombre'].split())
        if len(nombre) < 2:
            raise forms.ValidationError('El nombre debe tener al menos 2 caracteres.')
        repetidos = Item.objects.filter(nombre__iexact=nombre).exclude(pk=self.instance.pk)
        if repetidos.exists():
            raise forms.ValidationError(f'Ya existe un item llamado «{nombre}». Usa otro nombre.')
        return nombre

    def clean_imagen(self):
        return _validar_formato_y_peso(self.cleaned_data.get('imagen'))

    def clean_probabilidad(self):
        probabilidad = self.cleaned_data.get('probabilidad')
        if probabilidad is None or not (1 <= probabilidad <= 100):
            raise forms.ValidationError('La probabilidad debe ser un número entero entre 1 y 100.')
        return probabilidad

    def clean_ataque_base(self):
        ataque = self.cleaned_data.get('ataque_base')
        if ataque is not None and not (100 <= ataque <= 800):
            raise forms.ValidationError('El ataque base debe estar entre 100 y 800.')
        return ataque

    def clean_descripcion(self):
        descripcion = self.cleaned_data.get('descripcion', '').strip()
        if descripcion and len(descripcion) < 10:
            raise forms.ValidationError('Si escribes una descripción, usa al menos 10 caracteres.')
        if len(descripcion) > 600:
            raise forms.ValidationError(
                f'La descripción tiene {len(descripcion)} caracteres; el máximo es 600.'
            )
        return descripcion

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


class FiltroBannerForm(forms.Form):

    q = forms.CharField(required=False, max_length=100, label='Buscar')
    tipo = forms.ChoiceField(
        required=False, label='Tipo',
        choices=[('', 'Todos')] + list(TIPO_BANNER),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['q'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Buscar por nombre'})
        self.fields['tipo'].widget.attrs['class'] = 'form-select'


class FiltroCatalogoForm(forms.Form):

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