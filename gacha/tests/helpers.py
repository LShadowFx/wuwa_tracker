"""Datos y utilidades compartidas por las pruebas de gacha."""
import json
import re
from types import SimpleNamespace

from django.contrib.auth.models import User

from gacha.models import Banner, Item

CLAVE = 'clave-de-prueba-123'


def crear_usuarios():
    return SimpleNamespace(
        jugador=User.objects.create_user('jugador', password=CLAVE),
        otro=User.objects.create_user('otro', password=CLAVE),
        staff=User.objects.create_user('staff', password=CLAVE, is_staff=True),
        admin=User.objects.create_superuser('admin', 'a@a.cl', CLAVE),
    )


def crear_mundo():
    """Cuatro banners con un contenido minimo pero representativo.

    permanente : 2 personajes 5★ (sin destacado) y 2 personajes 4★.
    lim_pj     : banner de personaje limitado, con su destacado y un 4★.
    lim_arma   : banner de arma limitada, con su destacada y un 4★.
    vacio      : banner de arma limitada sin ningun item.
    """
    perm = Banner.objects.create(nombre='Permanente Prueba', tipo='permanente')
    lim_pj = Banner.objects.create(nombre='Personaje Prueba', tipo='personaje')
    lim_arma = Banner.objects.create(nombre='Arma Prueba', tipo='arma')
    vacio = Banner.objects.create(nombre='Banner Vacio', tipo='arma')

    def item(nombre, categoria, rareza, banner, peso=10, destacado=False):
        return Item.objects.create(nombre=nombre, categoria=categoria, rareza=rareza,
                                   banner=banner, probabilidad=peso, es_destacado=destacado)

    return SimpleNamespace(
        perm=perm, lim_pj=lim_pj, lim_arma=lim_arma, vacio=vacio,
        calcharo=item('Calcharo', 'personaje', 5, perm, 30),
        verina=item('Verina', 'personaje', 5, perm, 10),
        danjin=item('Danjin', 'personaje', 4, perm, 30),
        sanhua=item('Sanhua', 'personaje', 4, perm, 10),
        jiyan=item('Jiyan', 'personaje', 5, lim_pj, destacado=True),
        yuanwu=item('Yuanwu', 'personaje', 4, lim_pj, 20),
        verdant=item('Verdant Summit', 'arma', 5, lim_arma, destacado=True),
        espada4=item('Espada Cuatro', 'arma', 4, lim_arma, 20),
    )


def datos_item(banner, **cambios):
    """POST valido para ItemForm (4★ de personaje). Se pisa lo que se quiera probar."""
    datos = {
        'nombre': 'Item Nuevo', 'categoria': 'personaje', 'rareza': '4',
        'banner': str(banner.id), 'probabilidad': '10', 'descripcion': '', 'ataque_base': '',
    }
    datos.update({k: v for k, v in cambios.items()})
    return {k: v for k, v in datos.items() if v is not None}


def datos_banner(**cambios):
    datos = {'nombre': 'Banner Nuevo', 'tipo': 'permanente', 'descripcion': ''}
    datos.update(cambios)
    return datos


def json_script(html, id_):
    """Lee el contenido de un <script id="..." type="application/json"> de la pagina."""
    m = re.search(r'<script id="%s" type="application/json">(.*?)</script>' % re.escape(id_), html, re.S)
    return json.loads(m.group(1)) if m else None
