from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render, redirect


def login_view(request):
    if request.user.is_authenticated:
        return redirect('gacha:catalogo')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            usuario = form.cleaned_data.get('username')
            clave = form.cleaned_data.get('password')
            user = authenticate(request, username=usuario, password=clave)
            if user is not None:
                login(request, user)
                return redirect('gacha:catalogo')
        messages.error(request, 'Usuario o contrasena incorrectos.')
    else:
        form = AuthenticationForm()
    return render(request, 'cuentas/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('gacha:catalogo')
