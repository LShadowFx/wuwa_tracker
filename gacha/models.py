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
    nombre = models.CharField(max_length=100)
    tipo = models.CharField(max_length=20, choices=TIPO_BANNER)
    descripcion = models.TextField(blank=True)

    def __str__(self):
        return self.nombre

    def item_destacado(self):
        for item in self.items.all():
            if item.es_destacado:
                return item
        return None

    def imagen_fondo_css(self):
        item = self.item_destacado()
        if item and item.imagen:
            return f"background-image:url('{item.imagen.url}')"
        return ''


class Item(models.Model):
    nombre = models.CharField(max_length=100)
    categoria = models.CharField(max_length=20, choices=CATEGORIA_ITEM)
    rareza = models.IntegerField(choices=RAREZA)
    imagen = models.ImageField(default='sin_imagen.jpg', blank=True)
    descripcion = models.TextField(blank=True)
    ataque_base = models.PositiveIntegerField(
        null=True, blank=True,
        help_text='ATK base a nivel 90 (personajes: sin arma ni ecos).',
    )
    es_destacado = models.BooleanField(
        default=False,
        help_text='Marca si es el item destacado (rate-up) de su banner.',
    )
    banner = models.ForeignKey(Banner, on_delete=models.CASCADE, related_name='items')

    def __str__(self):
        return self.nombre


class EstadoPity(models.Model):
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
