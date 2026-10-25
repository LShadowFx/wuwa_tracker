from django.contrib import admin
from .models import Banner, Item, Tirada, EstadoPity


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'tipo')
    list_filter = ('tipo',)


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'categoria', 'rareza', 'es_destacado', 'banner')
    list_filter = ('categoria', 'rareza', 'banner')


@admin.register(Tirada)
class TiradaAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'banner', 'item', 'pity_en_momento', 'compartida', 'fecha')
    list_filter = ('banner', 'compartida')
    readonly_fields = ('fecha',)


@admin.register(EstadoPity)
class EstadoPityAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'banner', 'pity_actual', 'pity_4_actual', 'garantizado')
    list_filter = ('banner',)
