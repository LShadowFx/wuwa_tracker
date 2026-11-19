from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Count
from django.db.models.deletion import ProtectedError
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST

from .models import Banner, Item, Tirada, EstadoPity
from .forms import SimularTiradaForm, ItemForm, BannerForm, FiltroCatalogoForm, ORDEN_CATALOGO
from .pity import simular_tiradas

ITEMS_POR_PAGINA = 12
TIRADAS_EN_DASHBOARD = 10

# ---------------------------------------------------------------------------
# Perfiles (mismas banderas que usa el profe en su proyecto):
#   Visitante : sin sesion.
#   Jugador   : con sesion, is_staff=False, is_superuser=False.
#   Staff     : is_staff=True. Solo puede VER y EDITAR (no crea ni elimina).
#   Admin     : is_superuser=True. Hace todo el CRUD.
# ---------------------------------------------------------------------------


def _cuenta(n, singular, plural):
    return f'{n} {singular if n == 1 else plural}'


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


def item_detalle(request, slug):
    item = get_object_or_404(Item.objects.select_related('banner'), slug=slug)
    veces_obtenido = Tirada.objects.filter(item=item).count()
    mis_copias = None
    if request.user.is_authenticated:
        mis_copias = Tirada.objects.filter(item=item, usuario=request.user).count()
    return render(request, 'gacha/item_detalle.html', {
        'item': item,
        'veces_obtenido': veces_obtenido,
        'mis_copias': mis_copias,
    })


# ---------------------------------------------------------------------------
# CRUD de items (personajes y armas)
# ---------------------------------------------------------------------------
@login_required
def item_gestionar(request):
    """Tabla de gestion de items. La ven staff y admin."""
    if not (request.user.is_staff or request.user.is_superuser):
        raise PermissionDenied

    items = Item.objects.prefetch_related('banner__items').order_by('banner__nombre', '-rareza', 'nombre')
    return render(request, 'gacha/item_gestionar.html', {'items': items})


@login_required
def item_crear(request):
    """Solo el admin crea items."""
    if not request.user.is_superuser:
        raise PermissionDenied

    if request.method == 'POST':
        form = ItemForm(request.POST, request.FILES)
        if form.is_valid():
            item = form.save()
            messages.success(request, f'Se creó «{item.nombre}» y ya aparece en el catálogo.')
            return redirect('gacha:item_detalle', slug=item.slug)
        messages.error(request, 'No se pudo guardar. Revisa los campos marcados.')
    else:
        # Si se llega desde un banner (?banner=<id>) se deja ese banner preseleccionado.
        form = ItemForm(initial={'banner': request.GET.get('banner')})
    return render(request, 'gacha/item_form.html', {'form': form, 'editando': False})


@login_required
def item_editar(request, id):
    """Staff y admin editan cualquier dato del item, incluida su probabilidad."""
    if not (request.user.is_staff or request.user.is_superuser):
        raise PermissionDenied

    item = get_object_or_404(Item, id=id)
    nombre_original = item.nombre
    slug = item.slug

    if request.method == 'POST':
        form = ItemForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            item = form.save()
            messages.success(request, f'Se actualizó «{item.nombre}» correctamente.')
            return redirect('gacha:item_detalle', slug=item.slug)
        messages.error(request, 'No se pudo guardar. Revisa los campos marcados.')
    else:
        form = ItemForm(instance=item)
    return render(request, 'gacha/item_form.html', {
        'form': form,
        'editando': True,
        'nombre_original': nombre_original,
        'slug_original': slug,
        'imagen_actual': Item.objects.get(id=id).imagen,
    })


@login_required
@require_POST
def item_eliminar(request, id):
    """Solo el admin elimina. Un item que ya salio en tiradas queda protegido."""
    if not request.user.is_superuser:
        raise PermissionDenied

    item = get_object_or_404(Item, id=id)
    nombre = item.nombre
    imagen = item.imagen
    try:
        item.delete()
    except ProtectedError:
        veces = Tirada.objects.filter(item_id=id).count()
        messages.error(
            request,
            f'No se puede eliminar «{nombre}»: aparece en el historial de los jugadores '
            f'({_cuenta(veces, "tirada", "tiradas")}).',
        )
        return redirect('gacha:item_detalle', slug=item.slug)
    # Igual que el profe: se borra el archivo de la imagen, salvo la generica
    # (o si otro item todavia usa el mismo archivo).
    if imagen and imagen.name != 'sin_imagen.jpg' and not Item.objects.filter(imagen=imagen.name).exists():
        imagen.delete(save=False)
    messages.success(request, f'Se eliminó «{nombre}» correctamente.')
    return redirect('gacha:item_gestionar')


# ---------------------------------------------------------------------------
# CRUD de banners
# ---------------------------------------------------------------------------
def banners(request):
    lista = Banner.objects.prefetch_related('items').all()
    return render(request, 'gacha/banners.html', {'banners': lista})


def banner_detalle(request, banner_id):
    banner = get_object_or_404(Banner.objects.prefetch_related('items'), id=banner_id)
    return render(request, 'gacha/banner_detalle.html', {
        'banner': banner,
        'destacado': banner.item_destacado(),
    })


@login_required
def banner_gestionar(request):
    """Tabla de gestion de banners. La ven staff y admin."""
    if not (request.user.is_staff or request.user.is_superuser):
        raise PermissionDenied

    lista = Banner.objects.prefetch_related('items').order_by('nombre')
    return render(request, 'gacha/banner_gestionar.html', {'banners': lista})


@login_required
def banner_crear(request):
    """Solo el admin crea banners."""
    if not request.user.is_superuser:
        raise PermissionDenied

    if request.method == 'POST':
        form = BannerForm(request.POST)
        if form.is_valid():
            banner = form.save()
            messages.success(
                request,
                f'Se creó el banner «{banner.nombre}». Ahora puedes agregarle personajes o armas.',
            )
            return redirect('gacha:banner_detalle', banner_id=banner.id)
        messages.error(request, 'No se pudo guardar. Revisa los campos marcados.')
    else:
        form = BannerForm()
    return render(request, 'gacha/banner_form.html', {'form': form, 'editando': False})


@login_required
def banner_editar(request, id):
    """Staff y admin editan los datos del banner."""
    if not (request.user.is_staff or request.user.is_superuser):
        raise PermissionDenied

    banner = get_object_or_404(Banner, id=id)
    nombre_original = banner.nombre

    if request.method == 'POST':
        form = BannerForm(request.POST, instance=banner)
        if form.is_valid():
            banner = form.save()
            messages.success(request, f'Se actualizó el banner «{banner.nombre}» correctamente.')
            return redirect('gacha:banner_detalle', banner_id=banner.id)
        messages.error(request, 'No se pudo guardar. Revisa los campos marcados.')
    else:
        form = BannerForm(instance=banner)
    return render(request, 'gacha/banner_form.html', {
        'form': form,
        'editando': True,
        'banner_id': id,
        'nombre_original': nombre_original,
    })


@login_required
@require_POST
def banner_eliminar(request, id):
    """Solo el admin elimina. Un banner con items o con tiradas queda protegido."""
    if not request.user.is_superuser:
        raise PermissionDenied

    banner = get_object_or_404(Banner, id=id)
    nombre = banner.nombre
    try:
        banner.delete()
    except ProtectedError:
        partes = []
        n_items = banner.items.count()
        n_tiradas = Tirada.objects.filter(banner_id=id).count()
        n_estados = EstadoPity.objects.filter(banner_id=id).count()
        if n_items:
            partes.append(_cuenta(n_items, 'item asociado', 'items asociados'))
        if n_tiradas:
            partes.append(_cuenta(n_tiradas, 'tirada registrada', 'tiradas registradas'))
        if n_estados:
            partes.append(_cuenta(n_estados, 'registro de pity', 'registros de pity'))
        messages.error(
            request,
            f'No se puede eliminar el banner «{nombre}»: tiene {", ".join(partes)}. '
            'Mueve o elimina primero sus items.',
        )
        return redirect('gacha:banner_detalle', banner_id=id)
    messages.success(request, f'Se eliminó el banner «{nombre}» correctamente.')
    return redirect('gacha:banner_gestionar')


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
            if not banner.items.exists():
                messages.error(request, f'El banner «{banner.nombre}» todavía no tiene items para tirar.')
                return redirect('gacha:banner_detalle', banner_id=banner.id)
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

    # Personajes y armas que el jugador ya obtuvo, con cuantas copias tiene de cada uno.
    coleccion = (
        Item.objects.filter(tirada__usuario=request.user)
        .annotate(copias=Count('tirada'))
        .select_related('banner')
        .order_by('-rareza', 'nombre')
    )
    return render(request, 'gacha/dashboard.html', {
        'estados': estados,
        'historial': historial,
        'coleccion': coleccion,
        'limite': TIRADAS_EN_DASHBOARD,
        'total_tiradas': Tirada.objects.filter(usuario=request.user).count(),
    })


def feed_publico(request):
    """El feed es publico: lo puede ver cualquiera, con o sin sesion."""
    tiradas = Tirada.objects.filter(compartida=True).select_related('usuario', 'banner', 'item')[:20]
    return render(request, 'gacha/feed.html', {'tiradas': tiradas})
