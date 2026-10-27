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
