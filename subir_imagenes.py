"""
Sube varias imagenes de una sola vez, emparejando cada archivo con su
Item segun el NOMBRE del archivo (no importa si usas mayusculas o
minusculas, pero el texto debe ser igual al nombre del item).

Como usarlo:
1. Crea una carpeta llamada "imagenes_a_subir" en la raiz del proyecto
   (al mismo nivel que manage.py).
2. Adentro, pon cada foto con el mismo nombre que el item en el
   catalogo, por ejemplo:
       Jiyan.jpg
       Verdant Summit.png
       Guardian Broadblade.jpg
   Extensiones aceptadas: .jpg, .jpeg, .png, .webp

3. Corre este comando desde la raiz del proyecto (con el venv activado):
       python manage.py shell < subir_imagenes.py

4. Revisa el resumen que imprime al final: cuantas se subieron bien y
   cuales nombres de archivo no calzaron con ningun item (por typos).

Este script no se usa dentro de la aplicacion (no es una vista ni se
ejecuta cuando alguien visita el sitio); es una herramienta para cargar
datos auxiliares, igual que el fixture datos_iniciales.json.
"""
import os

from django.core.files import File

from gacha.models import Item

CARPETA = 'imagenes_a_subir'
EXTENSIONES_VALIDAS = ('.jpg', '.jpeg', '.png', '.webp')


def subir_todas():
    if not os.path.isdir(CARPETA):
        print(f'No encontre la carpeta "{CARPETA}" en la raiz del proyecto.')
        print(f'Creala y pon ahi las fotos antes de correr este script de nuevo.')
        return

    subidas = []
    no_encontradas = []

    for nombre_archivo in sorted(os.listdir(CARPETA)):
        ruta = os.path.join(CARPETA, nombre_archivo)
        nombre_sin_extension, extension = os.path.splitext(nombre_archivo)

        if extension.lower() not in EXTENSIONES_VALIDAS:
            continue

        item = Item.objects.filter(nombre__iexact=nombre_sin_extension.strip()).first()
        if item is None:
            no_encontradas.append(nombre_archivo)
            continue

        with open(ruta, 'rb') as f:
            item.imagen.save(nombre_archivo, File(f), save=True)
        subidas.append(item.nombre)

    print('')
    print(f'Imagenes subidas correctamente: {len(subidas)}')
    for nombre in subidas:
        print(f'  - {nombre}')

    if no_encontradas:
        print('')
        print(f'Archivos que NO coincidieron con ningun item ({len(no_encontradas)}):')
        for nombre in no_encontradas:
            print(f'  - {nombre}')
        print('Revisa que el nombre del archivo sea igual al nombre del item (sin la extension).')


subir_todas()
