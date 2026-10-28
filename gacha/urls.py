from django.urls import path
from . import views

app_name = 'gacha'

urlpatterns = [
    # Catalogo (publico)
    path('', views.catalogo, name='catalogo'),
    path('items/nuevo/', views.item_crear, name='item_crear'),
    path('items/<slug:slug>/', views.item_detalle, name='item_detalle'),
    path('banners/', views.banners, name='banners'),
    path('banners/<int:banner_id>/', views.banner_detalle, name='banner_detalle'),
    path('feed/', views.feed_publico, name='feed'),

    # Tiradas y dashboard (requieren sesion)
    path('simular/', views.simular, name='simular'),
    path('resultado/', views.resultado, name='resultado'),
    path('compartir/<int:tirada_id>/', views.compartir, name='compartir'),
    path('dashboard/', views.dashboard, name='dashboard'),
]
