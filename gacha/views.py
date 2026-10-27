from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404

from .models import Banner, Item, Tirada, EstadoPity
from .forms import SimularTiradaForm, ItemForm, FiltroCatalogoForm, ORDEN_CATALOGO
from .pity import simular_tiradas

ITEMS_POR_PAGINA = 12
TIRADAS_EN_DASHBOARD = 10


# ---------------------------------------------------------------------------
# Catalogo (publico, solo lectura)
# ---------------------------------------------------------------------------
def catalogo(request):
    """Listado compacto de personajes y armas. El detalle esta en otra pagina."""
    filtro = FiltroCatalogoForm(request.GET)
    items = Item.objects.select_related('banner')
    orden = 'recientes'

    if filtro.is_valid():
        datos = filtro.cleaned_data
        if datos['q']:
            items = items.filter(nombre__icontains=datos['q'].strip())
        if datos['categoria']:
            items = items.filter(categoria=datos['categoria'])
        if datos['rareza']:
            items = items.filter(rareza=int(datos['rareza']))
        if datos['banner']:
            items = items.filter(banner=datos['banner'])
        orden = datos['orden'] or 'recientes'

    items = items.order_by(*ORDEN_CATALOGO[orden])
    pagina = Paginator(items, ITEMS_POR_PAGINA).get_page(request.GET.get('page'))

    # Querystring de los filtros (sin "page") para conservarlos al cambiar de pagina.
    params = request.GET.copy()
    params.pop('page', None)

    return render(request, 'gacha/catalogo.html', {
        'filtro': filtro,
        'pagina': pagina,
        'total': pagina.paginator.count,
        'querystring': params.urlencode(),
    })


def item_detalle(request, item_id):
    item = get_object_or_404(Item.objects.select_related('banner'), id=item_id)
    veces_obtenido = Tirada.objects.filter(item=item).count()
    mis_copias = None
    if request.user.is_authenticated:
        mis_copias = Tirada.objects.filter(item=item, usuario=request.user).count()
    return render(request, 'gacha/item_detalle.html', {
        'item': item,
        'veces_obtenido': veces_obtenido,
        'mis_copias': mis_copias,
    })


@login_required
def item_crear(request):
    if request.method == 'POST':
        form = ItemForm(request.POST, request.FILES)
        if form.is_valid():
            item = form.save()
            messages.success(request, f'Se creó «{item.nombre}» y ya aparece en el catálogo.')
            return redirect('gacha:item_detalle', item_id=item.id)
        messages.error(request, 'No se pudo guardar. Revisa los campos marcados.')
    else:
        form = ItemForm()
    return render(request, 'gacha/item_form.html', {'form': form})


def banners(request):
    lista = Banner.objects.prefetch_related('items').all()
    return render(request, 'gacha/banners.html', {'banners': lista})


def banner_detalle(request, banner_id):
    banner = get_object_or_404(Banner.objects.prefetch_related('items'), id=banner_id)
    return render(request, 'gacha/banner_detalle.html', {
        'banner': banner,
        'destacado': banner.item_destacado(),
    })


# ---------------------------------------------------------------------------
# Tiradas (requieren sesion)
# ---------------------------------------------------------------------------


@login_required
def simular(request):
    if request.method == 'POST':
        form = SimularTiradaForm(request.POST)
        if form.is_valid():
            banner = form.cleaned_data['banner']
            cantidad = form.cleaned_data['cantidad']
            tiradas = simular_tiradas(request.user, banner, cantidad)
            request.session['ultimos_resultados'] = [t.id for t in tiradas]
            request.session['ultimo_banner_id'] = banner.id
            request.session['ultima_cantidad'] = cantidad
            return redirect('gacha:resultado')
        messages.error(request, 'No se pudo procesar la tirada. Revisa los campos marcados.')
    else:
        form = SimularTiradaForm()
    return render(request, 'gacha/simular.html', {'form': form})


@login_required
def resultado(request):
    ids = request.session.get('ultimos_resultados', [])
    tiradas = Tirada.objects.filter(id__in=ids, usuario=request.user).select_related('banner', 'item')

    banner_id = request.session.get('ultimo_banner_id')
    banner = Banner.objects.prefetch_related('items').filter(id=banner_id).first() if banner_id else None

    if banner is None:
        messages.info(request, 'Primero tira desde un banner para ver un resultado.')
        return redirect('gacha:banners')

    return render(request, 'gacha/resultado.html', {
        'tiradas': tiradas,
        'cantidad': request.session.get('ultima_cantidad'),
        'banner': banner,
    })


@login_required
def compartir(request, tirada_id):
    tirada = get_object_or_404(Tirada, id=tirada_id, usuario=request.user)
    if request.method == 'POST':
        tirada.compartida = True
        tirada.save()
        messages.success(request, f'Compartiste tu {tirada.item.nombre} en el feed publico.')
    return redirect('gacha:dashboard')


@login_required
def dashboard(request):
    estados = list(
        EstadoPity.objects.filter(usuario=request.user)
        .select_related('banner')
        .prefetch_related('banner__items')
    )
    for estado in estados:
        estado.porcentaje_pity = min(100, round(estado.pity_actual / 80 * 100))

    historial = Tirada.objects.filter(usuario=request.user).select_related('banner', 'item')[:TIRADAS_EN_DASHBOARD]
    return render(request, 'gacha/dashboard.html', {
        'estados': estados,
        'historial': historial,
        'limite': TIRADAS_EN_DASHBOARD,
        'total_tiradas': Tirada.objects.filter(usuario=request.user).count(),
    })


def feed_publico(request):
    tiradas = Tirada.objects.filter(compartida=True).select_related('usuario', 'banner', 'item')[:20]
    return render(request, 'gacha/feed.html', {'tiradas': tiradas})
