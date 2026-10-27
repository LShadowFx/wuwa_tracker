from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render, redirect
from django.utils.http import url_has_allowed_host_and_scheme


def _destino_seguro(request):
    """Devuelve la pagina a la que volver tras el login (parametro ?next=), solo si es de este sitio."""
    destino = request.POST.get('next') or request.GET.get('next') or ''
    if destino and url_has_allowed_host_and_scheme(destino, allowed_hosts={request.get_host()}):
        return destino
    return 'gacha:catalogo'


def login_view(request):
    if request.user.is_authenticated:
        return redirect('gacha:catalogo')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect(_destino_seguro(request))
        messages.error(request, 'Usuario o contrasena incorrectos.')
    else:
        form = AuthenticationForm()
    return render(request, 'cuentas/login.html', {
        'form': form,
        'next': request.GET.get('next', ''),
    })


def logout_view(request):
    if request.method == 'POST':
        logout(request)
    return redirect('gacha:catalogo')
