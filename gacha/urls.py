from django.urls import path
from . import views

app_name = 'gacha'

urlpatterns = [
    path('', views.catalogo, name='catalogo'),
    path('simular/', views.simular, name='simular'),
    path('resultado/', views.resultado, name='resultado'),
    path('compartir/<int:tirada_id>/', views.compartir, name='compartir'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('feed/', views.feed_publico, name='feed'),
]
