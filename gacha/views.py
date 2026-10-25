from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

from .models import Banner, Tirada, EstadoPity
from .forms import SimularTiradaForm
from .pity import simular_tiradas


def catalogo(request):
    """Vista publica: cualquiera puede ver los banners y sus items."""
    banners = Banner.objects.prefetch_related('items').all()
    return render(request, 'gacha/catalogo.html', {'banners': banners})


@login_required
def simular(request):
    """
    Procesa un pull disparado directamente desde los botones "Tirar x1" /
    "Tirar x10" de un banner en el catalogo. Ya no existe una pagina
    aparte para elegir el banner: el pull se inicia desde el banner mismo.
    Si alguien entra a esta URL sin mandar un POST valido, lo mandamos
    de vuelta al catalogo (no hay nada que mostrar aqui directamente).
    """
    if request.method == 'POST':
        form = SimularTiradaForm(request.POST)
        if form.is_valid():
            banner = form.cleaned_data['banner']
            cantidad = form.cleaned_data['cantidad']
            tiradas = simular_tiradas(request.user, banner, cantidad)

            # Guardamos los resultados en la sesion para mostrarlos en la
            # siguiente pagina sin reenviar el formulario al refrescar.
            request.session['ultimos_resultados'] = [t.id for t in tiradas]
            request.session['ultimo_banner_id'] = banner.id
            request.session['ultima_cantidad'] = cantidad
            return redirect('gacha:resultado')
        messages.error(request, 'No se pudo procesar la tirada. Intenta de nuevo desde el banner.')
    return redirect('gacha:catalogo')


@login_required
def resultado(request):
    """
    Muestra el resultado de la ultima tirada. Recupera el Banner completo
    (no solo su nombre) para que la pantalla de resultado use el mismo
    fondo e imagen destacada que el banner donde se tiro.
    """
    ids = request.session.get('ultimos_resultados', [])
    tiradas = Tirada.objects.filter(id__in=ids, usuario=request.user).select_related('banner', 'item')

    banner_id = request.session.get('ultimo_banner_id')
    banner = Banner.objects.prefetch_related('items').filter(id=banner_id).first() if banner_id else None

    if banner is None:
        # Nadie tiro todavia en esta sesion (o entraron directo a esta URL).
        messages.info(request, 'Primero tira desde un banner para ver un resultado.')
        return redirect('gacha:catalogo')

    return render(request, 'gacha/resultado.html', {
        'tiradas': tiradas,
        'cantidad': request.session.get('ultima_cantidad'),
        'banner': banner,
    })


@login_required
def compartir(request, tirada_id):
    """
    Marca una tirada como compartida al feed publico.
    get_object_or_404 con usuario=request.user asegura que nadie pueda
    compartir (ni ver) una tirada que no es suya cambiando el numero
    en la URL.
    """
    tirada = get_object_or_404(Tirada, id=tirada_id, usuario=request.user)
    if request.method == 'POST':
        tirada.compartida = True
        tirada.save()
        messages.success(request, f'Compartiste tu {tirada.item.nombre} en el feed publico.')
    return redirect('gacha:dashboard')


@login_required
def dashboard(request):
    """Vista protegida: historial privado y pity actual del usuario."""
    estados = list(
        EstadoPity.objects.filter(usuario=request.user)
        .select_related('banner')
        .prefetch_related('banner__items')
    )
    for estado in estados:
        estado.porcentaje_pity = min(100, round(estado.pity_actual / 80 * 100))

    historial = Tirada.objects.filter(usuario=request.user).select_related('banner', 'item')[:30]
    return render(request, 'gacha/dashboard.html', {
        'estados': estados,
        'historial': historial,
    })


def feed_publico(request):
    """Vista publica: ultimas tiradas que otros usuarios compartieron."""
    tiradas = Tirada.objects.filter(compartida=True).select_related('usuario', 'banner', 'item')[:20]
    return render(request, 'gacha/feed.html', {'tiradas': tiradas})
