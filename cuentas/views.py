from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render, redirect


def login_view(request):
    if request.user.is_authenticated:
        return redirect('gacha:catalogo')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('gacha:catalogo')
        messages.error(request, 'Usuario o contrasena incorrectos.')
    else:
        form = AuthenticationForm()
    return render(request, 'cuentas/login.html', {'form': form})


def logout_view(request):
    if request.method == 'POST':
        logout(request)
    return redirect('gacha:catalogo')
