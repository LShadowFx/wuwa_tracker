from django.urls import path
from . import views

app_name = 'gacha'

urlpatterns = [
    path('', views.catalogo, name='catalogo'),

    # Items (personajes y armas). Las rutas fijas van ANTES de <slug:slug>.
    path('items/nuevo/', views.item_crear, name='item_crear'),
    path('items/gestionar/', views.item_gestionar, name='item_gestionar'),
    path('items/<int:id>/editar/', views.item_editar, name='item_editar'),
    path('items/<int:id>/eliminar/', views.item_eliminar, name='item_eliminar'),
    path('items/<slug:slug>/', views.item_detalle, name='item_detalle'),

    # Banners
    path('banners/', views.banners, name='banners'),
    path('banners/nuevo/', views.banner_crear, name='banner_crear'),
    path('banners/gestionar/', views.banner_gestionar, name='banner_gestionar'),
    path('banners/<int:id>/editar/', views.banner_editar, name='banner_editar'),
    path('banners/<int:id>/eliminar/', views.banner_eliminar, name='banner_eliminar'),
    path('banners/<int:banner_id>/', views.banner_detalle, name='banner_detalle'),

    path('feed/', views.feed_publico, name='feed'),

    # Tiradas y dashboard (requieren sesion)
    path('simular/', views.simular, name='simular'),
    path('resultado/', views.resultado, name='resultado'),
    path('compartir/<int:tirada_id>/', views.compartir, name='compartir'),
    path('dashboard/', views.dashboard, name='dashboard'),
]
