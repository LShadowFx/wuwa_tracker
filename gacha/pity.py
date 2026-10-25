import random

from .models import Banner, Item, EstadoPity, Tirada

PROBABILIDAD_BASE_5E = 0.008
PROBABILIDAD_BASE_4E = 0.06
INICIO_SOFT_PITY = 60
INCREMENTO_SOFT_PITY = 0.05
HARD_PITY = 80
PITY_4_MAXIMO = 10


def probabilidad_5_estrellas(pity_actual):
    """Calcula la probabilidad de 5 estrellas segun el pity acumulado."""
    if pity_actual < INICIO_SOFT_PITY:
        return PROBABILIDAD_BASE_5E
    pasos_en_soft_pity = pity_actual - (INICIO_SOFT_PITY - 1)
    probabilidad = PROBABILIDAD_BASE_5E + (pasos_en_soft_pity * INCREMENTO_SOFT_PITY)
    return min(probabilidad, 1.0)


def _elegir_item_cinco_estrellas(banner, estado):
    """
    Decide que item de 5 estrellas entrega esta tirada segun el tipo de
    banner, aplicando la regla del 50/50 cuando corresponde.
    Devuelve una tupla (item, gano_50_50).
    """
    items_5e = list(banner.items.filter(rareza=5))

    if banner.tipo == 'personaje':
        destacado = next((i for i in items_5e if i.es_destacado), None)

        if estado.garantizado or random.random() < 0.5:
            estado.garantizado = False
            return destacado, True

        # Perdio el 50/50: el 5 estrellas viene del pool estandar
        # (banner permanente), no del propio banner limitado.
        estado.garantizado = True
        banner_permanente = Banner.objects.filter(tipo='permanente').first()
        if banner_permanente:
            pool_estandar = list(
                banner_permanente.items.filter(rareza=5, categoria='personaje')
            )
        else:
            pool_estandar = []
        item = random.choice(pool_estandar) if pool_estandar else destacado
        return item, False

    if banner.tipo == 'arma':
        destacado = next((i for i in items_5e if i.es_destacado), None)
        return destacado, None

    # Banner permanente: sin item destacado, se elige cualquiera al azar.
    item = random.choice(items_5e) if items_5e else None
    return item, None


def simular_una_tirada(banner, estado):
    """
    Simula UNA tirada individual sobre un banner, usando y actualizando
    (en memoria, sin guardar todavia) el EstadoPity recibido.

    Devuelve un diccionario, por ejemplo:
        {'rareza': 3, 'item': None, 'gano_50_50': None, 'pity_en_momento': 45}
        {'rareza': 5, 'item': <Item: Jiyan>, 'gano_50_50': True, 'pity_en_momento': 62}
    """
    estado.pity_actual += 1
    estado.pity_4_actual += 1

    salio_cinco = estado.pity_actual >= HARD_PITY
    if not salio_cinco:
        salio_cinco = random.random() < probabilidad_5_estrellas(estado.pity_actual)

    if salio_cinco:
        item, gano_50_50 = _elegir_item_cinco_estrellas(banner, estado)
        pity_de_esta_tirada = estado.pity_actual
        estado.pity_actual = 0
        estado.pity_4_actual = 0
        return {
            'rareza': 5,
            'item': item,
            'gano_50_50': gano_50_50,
            'pity_en_momento': pity_de_esta_tirada,
        }

    salio_cuatro = estado.pity_4_actual >= PITY_4_MAXIMO
    if not salio_cuatro:
        salio_cuatro = random.random() < PROBABILIDAD_BASE_4E

    if salio_cuatro:
        items_4e = list(banner.items.filter(rareza=4))
        item = random.choice(items_4e) if items_4e else None
        pity_de_esta_tirada = estado.pity_actual
        estado.pity_4_actual = 0
        return {
            'rareza': 4,
            'item': item,
            'gano_50_50': None,
            'pity_en_momento': pity_de_esta_tirada,
        }

    return {
        'rareza': 3,
        'item': None,
        'gano_50_50': None,
        'pity_en_momento': estado.pity_actual,
    }


def simular_tiradas(usuario, banner, cantidad):
    """
    Simula `cantidad` tiradas (1 o 10) para un usuario en un banner.

    Actualiza y guarda el EstadoPity del usuario para ese banner, y crea
    en la base de datos una fila Tirada por cada resultado de 4 o 5
    estrellas (las de 3 estrellas no quedan registradas individualmente,
    pero si cuentan para el contador de pity).

    Devuelve la lista de objetos Tirada creados en esta simulacion.
    """
    estado, _ = EstadoPity.objects.get_or_create(usuario=usuario, banner=banner)

    tiradas_creadas = []
    for _ in range(cantidad):
        resultado = simular_una_tirada(banner, estado)
        if resultado['rareza'] in (4, 5) and resultado['item'] is not None:
            tirada = Tirada.objects.create(
                usuario=usuario,
                banner=banner,
                item=resultado['item'],
                pity_en_momento=resultado['pity_en_momento'],
                gano_50_50=resultado['gano_50_50'],
            )
            tiradas_creadas.append(tirada)

    estado.save()
    return tiradas_creadas
