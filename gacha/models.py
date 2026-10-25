from django.db import models
from django.contrib.auth.models import User

TIPO_BANNER = [
    ('personaje', 'Personaje limitado'),
    ('arma', 'Arma limitada'),
    ('permanente', 'Permanente'),
]

CATEGORIA_ITEM = [
    ('personaje', 'Personaje'),
    ('arma', 'Arma'),
]

RAREZA = [
    (4, '4 estrellas'),
    (5, '5 estrellas'),
]


class Banner(models.Model):
    """Un banner de Wuthering Waves."""
    nombre = models.CharField(max_length=100)
    tipo = models.CharField(max_length=20, choices=TIPO_BANNER)
    descripcion = models.TextField(blank=True)

    def __str__(self):
        return self.nombre

    def item_destacado(self):
        """
        Devuelve el item marcado como destacado de este banner, o None si
        no tiene (el banner permanente no tiene destacado a proposito).
        Se usa para mostrar su imagen como fondo grande del banner.

        Recorre self.items.all() en vez de usar .filter() para aprovechar
        el prefetch_related('items') que ya hace la vista del catalogo,
        y no generar una consulta extra a la base de datos por banner.
        """
        for item in self.items.all():
            if item.es_destacado:
                return item
        return None

    def imagen_fondo_css(self):
        """
        Fragmento de estilo listo para usar en style="..." con la imagen
        del item destacado como fondo. Si no hay destacado (banner
        permanente), devuelve una cadena vacia y el banner cae de vuelta
        al degradado de color definido en estilos.css para cada tipo.

        Se calcula aca (y no con un {% if %} dentro del HTML) para que
        el template solo tenga que escribir una variable corta y simple,
        en vez de una condicion larga metida dentro de una etiqueta.
        """
        item = self.item_destacado()
        if item and item.imagen:
            return f"background-image:url('{item.imagen.url}')"
        return ''


class Item(models.Model):
    """
    Un personaje o un arma que puede obtenerse en un banner.

    'categoria' distingue si es un personaje o un arma: la necesitamos
    para que el algoritmo de pity sepa, cuando alguien pierde el 50/50
    en el banner de personaje, que del banner permanente debe sacar un
    PERSONAJE estandar y no un arma por error.
    """
    nombre = models.CharField(max_length=100)
    categoria = models.CharField(max_length=20, choices=CATEGORIA_ITEM)
    rareza = models.IntegerField(choices=RAREZA)
    imagen = models.ImageField(default='sin_imagen.jpg', blank=True)
    es_destacado = models.BooleanField(
        default=False,
        help_text='Marca si es el item destacado (rate-up) de su banner.',
    )
    banner = models.ForeignKey(Banner, on_delete=models.CASCADE, related_name='items')

    def __str__(self):
        return self.nombre


class EstadoPity(models.Model):
    """
    Contador "vivo" de pity de un usuario para un banner especifico.
    Se actualiza en cada simulacion, incluso en las tiradas de 3 estrellas
    que no quedan guardadas como fila en Tirada.
    """
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    banner = models.ForeignKey(Banner, on_delete=models.CASCADE)
    pity_actual = models.IntegerField(default=0)
    pity_4_actual = models.IntegerField(default=0)
    garantizado = models.BooleanField(
        default=False,
        help_text='Si es True, el proximo 5 estrellas de este banner esta garantizado al item destacado.',
    )

    class Meta:
        unique_together = ('usuario', 'banner')
        verbose_name_plural = 'Estados de pity'

    def __str__(self):
        return f'{self.usuario.username} - {self.banner.nombre}: pity {self.pity_actual}'


class Tirada(models.Model):
    """
    Historial real: una fila por cada resultado de 4 o 5 estrellas que
    un usuario obtuvo al simular tiradas en un banner.
    """
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tiradas')
    banner = models.ForeignKey(Banner, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    pity_en_momento = models.IntegerField()
    gano_50_50 = models.BooleanField(
        null=True, blank=True,
        help_text='Solo aplica al banner de personaje. None si no corresponde.',
    )
    compartida = models.BooleanField(default=False)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha']

    def __str__(self):
        return f'{self.usuario.username} obtuvo {self.item.nombre} (pity {self.pity_en_momento})'
