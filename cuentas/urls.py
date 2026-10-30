from django.urls import path
from cuentas import views

app_name = 'cuentas'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
]
