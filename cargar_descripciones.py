"""Carga el ataque base y una descripcion en cada Item ya existente.

Uso (desde la raiz del proyecto, con el venv activo y DESPUES de migrate):
    python cargar_descripciones.py

Es seguro correrlo mas de una vez: solo actualiza los dos campos nuevos.
Cuando termine y todo se vea bien en la pagina, se puede borrar este archivo.

Fuente de los numeros: Prydwen (prydwen.gg/wuthering-waves/stats y /weapons).
 - Personajes: ATK base a nivel 90, sin arma ni ecos.
 - Armas: ATK base a nivel 90.
Las descripciones son resumenes propios (no es el texto oficial del juego).
"""
import os

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wuwa_tracker.settings')
django.setup()

from gacha.models import Item  # noqa: E402  (debe ir despues de django.setup())

# nombre del item: (ataque_base, descripcion)
DATOS = {
    # ------------------------------ Personajes ------------------------------
    'Jiyan': (
        438,
        'Resonador Aero de 5 estrellas que combate con Broadblade. Es el general de los '
        'Midnight Rangers de Jinzhou y funciona como DPS principal del equipo. '
        'Su arma exclusiva es Verdant Summit.',
    ),
    'Aalto': (
        263,
        'Resonador Aero de 4 estrellas que usa Pistols. Es un sub-DPS: entra al combate, '
        'aporta daño rápido y deja el lugar a otro personaje.',
    ),
    'Danjin': (
        263,
        'Resonadora Havoc de 4 estrellas que usa Sword. Su estilo es arriesgado: sacrifica '
        'parte de su propia vida a cambio de más daño, así que conviene llevar curación en el equipo.',
    ),
    'Taoqi': (
        225,
        'Resonadora Havoc de 4 estrellas con Broadblade. Es un personaje defensivo: '
        'su escudo y su daño escalan con la DEF, no con el ataque, por eso su ATK base es bajo.',
    ),
    'Calcharo': (
        438,
        'Resonador Electro de 5 estrellas con Broadblade. DPS principal que concentra '
        'su daño en un solo objetivo con ataques de gran impacto.',
    ),
    'Encore': (
        425,
        'Resonadora Fusion de 5 estrellas con Rectifier. DPS principal que lucha junto a '
        'su inseparable Cosmos y puede entrar en un modo de ataque explosivo.',
    ),
    'Jianxin': (
        338,
        'Resonadora Aero de 5 estrellas con Gauntlets. Cumple un rol de soporte: tiene mucha '
        'vida base, cura y ayuda al equipo, aunque su ATK base es moderado.',
    ),
    'Lingyang': (
        438,
        'Resonador Glacio de 5 estrellas con Gauntlets. DPS principal de combate cercano, '
        'con ataques rápidos de daño Glacio.',
    ),
    'Verina': (
        338,
        'Resonadora Spectro de 5 estrellas con Rectifier. Es la sanadora principal del '
        'catálogo y, además de curar, potencia el daño del equipo.',
    ),
    'Yinlin': (
        400,
        'Resonadora Electro de 5 estrellas con Rectifier. Sub-DPS que marca a los enemigos '
        'para provocar daño Electro adicional cuando el equipo ataca.',
    ),
    'Baizhi': (
        213,
        'Resonadora Glacio de 4 estrellas con Rectifier. Sanadora del equipo, con mucha '
        'vida base y el ATK base más bajo del catálogo.',
    ),
    'Chixia': (
        300,
        'Resonadora Fusion de 4 estrellas con Pistols. DPS que basa su daño en ataques '
        'básicos disparados en ráfaga.',
    ),
    'Sanhua': (
        275,
        'Resonadora Glacio de 4 estrellas con Sword. Sub-DPS que aporta daño Glacio '
        'al equipo.',
    ),
    'Mortefi': (
        250,
        'Resonador Fusion de 4 estrellas con Pistols. Sub-DPS con aporte de apoyo para '
        'el personaje que está en primera línea.',
    ),
    'Yangyang': (
        250,
        'Resonadora Aero de 4 estrellas con Sword. Personaje de apoyo y sub-DPS, '
        'pensada para acompañar a otros Resonadores.',
    ),
    'Yuanwu': (
        225,
        'Resonador Electro de 4 estrellas con Gauntlets. Es un sub-DPS defensivo cuyo daño '
        'escala con la DEF; tiene la DEF base más alta de este catálogo (1637).',
    ),
    # -------------------------------- Armas ---------------------------------
    'Verdant Summit': (
        587,
        'Broadblade de 5 estrellas, arma exclusiva de Jiyan (banner limitado). Combina '
        '587 de ATK base con CRIT DMG 48.6% como estadística secundaria.',
    ),
    'Guardian Broadblade': (
        325,
        'Broadblade sencilla de la serie Guardian. 325 de ATK base y ATK 24.3% como '
        'estadística secundaria. Sirve como arma de transición.',
    ),
    'Guardian Pistols': (
        325,
        'Pistols sencillas de la serie Guardian. 325 de ATK base y ATK 24.3% como '
        'estadística secundaria. Sirven como arma de transición.',
    ),
    'Guardian Sword': (
        300,
        'Sword sencilla de la serie Guardian. 300 de ATK base y HP 30.3% como '
        'estadística secundaria, más orientada a la resistencia que al daño.',
    ),
    'Guardian Rectifier': (
        325,
        'Rectifier sencillo de la serie Guardian. 325 de ATK base y ATK 24.3% como '
        'estadística secundaria. Sirve como arma de transición.',
    ),
    'Emerald of Genesis': (
        587,
        'Sword de 5 estrellas del banner permanente. 587 de ATK base y CRIT Rate 24.3%. '
        'Es la opción más usada para los personajes que pelean con espada.',
    ),
    'Lustrous Razor': (
        587,
        'Broadblade de 5 estrellas del banner permanente. 587 de ATK base y ATK 36.4%. '
        'Su efecto sube la regeneración de energía y potencia el daño de la Resonance Liberation.',
    ),
    'Static Mist': (
        587,
        'Pistols de 5 estrellas del banner permanente. 587 de ATK base y CRIT Rate 24.3%. '
        'Sube la regeneración de energía y, al usar la Outro Skill, da un bono de ATK '
        'al personaje que entra al combate.',
    ),
    'Abyss Surges': (
        587,
        'Gauntlets de 5 estrellas del banner permanente. 587 de ATK base y ATK 36.4%. '
        'Su efecto mejora la regeneración de energía y combina bien con Jianxin y Lingyang.',
    ),
    'Cosmic Ripples': (
        500,
        'Rectifier de 5 estrellas del banner permanente. 500 de ATK base y cerca de 54% '
        'de ATK como estadística secundaria. Va bien con personajes que dañan con ataques básicos.',
    ),
}


def main():
    actualizados = 0
    for nombre, (ataque_base, descripcion) in DATOS.items():
        filas = Item.objects.filter(nombre=nombre).update(
            ataque_base=ataque_base,
            descripcion=descripcion,
        )
        if filas:
            actualizados += 1
        else:
            print('NO ENCONTRADO en la base:', nombre)

    print('Items actualizados:', actualizados, 'de', len(DATOS))

    sin_datos = Item.objects.filter(descripcion='')
    for item in sin_datos:
        print('Sigue sin descripcion:', item.nombre)


main()
