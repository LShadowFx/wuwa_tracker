# Comprobaciones realizadas
 
Cada fila es una comprobación con su acción o entrada, el resultado esperado y el resultado observado al
ejecutar el proyecto en el navegador (`python manage.py runserver`) sobre **PostgreSQL**.
 
Cuentas usadas (ver README, sección 3.5):
 
| Cuenta | Perfil |
|--------|--------|
| `vice` / `luis` | Administrador (superusuario) |
| `staff` | Staff (`is_staff=True`) |
| `jugador` | Jugador (con sesión, sin permisos de gestión) |
 
Un acceso sin el perfil necesario responde **403** con la página `403.html`; un acceso sin sesión redirige
a `/cuentas/login/?next=…`.
 
## A. Acceso y sesiones
 
| # | Acción / entrada | Resultado esperado | Observado |
|---|------------------|--------------------|-----------|
| 1 | Sin sesión, abrir `/`, `/feed/` y `/cuentas/login/` | Las tres páginas cargan | OK (200) |
| 2 | Sin sesión, escribir directo `/dashboard/`, `/resultado/`, `/simular/` y `/compartir/1/` | Redirige a `/cuentas/login/?next=…` | OK (302 al login en las cuatro) |
| 3 | Sin sesión, enviar un POST a `/simular/` | Redirige al login; no se guarda nada | OK (302; no se crearon tiradas ni pity) |
| 4 | Login con usuario y clave correctos | Entra y vuelve al catálogo; el menú muestra el usuario y "Cerrar sesión" | OK (302 a `/`) |
| 5 | Login con clave incorrecta | Vuelve al formulario con mensaje de error; no inicia sesión | OK (200 con "Por favor, introduzca un nombre de usuario y clave correctos…") |
| 6 | Login con los campos vacíos | Marca usuario y contraseña como obligatorios | OK (2 × "Este campo es obligatorio") |
| 7 | Presionar "Cerrar sesión" y luego escribir `/dashboard/` | Cierra la sesión; `/dashboard/` redirige al login | OK |
| 8 | Después de cerrar sesión, escribir `/resultado/` | Redirige al login | OK |
 
## B. Formulario de simulación (validación en el servidor)
 
| # | Acción / entrada | Resultado esperado | Observado |
|---|------------------|--------------------|-----------|
| 9 | Con sesión, presionar el botón para simular | Se muestra el formulario con banner y cantidad | OK (200) |
| 10 | Enviar cantidad `5`, `abc` o `-1` (con un banner válido) | Se rechaza, se vuelve al formulario marcando "Cantidad" con error; no se guarda nada | OK ("Escoja una opción válida."; sin cambios en la base) |
| 11 | Enviar banner inexistente (`999`) o vacío | Se rechaza, se marca "Banner" con error; no se guarda nada | OK ("Escoja una opción válida." / "Este campo es obligatorio.") |
| 12 | Enviar el formulario sin ningún campo | Ambos campos marcados como obligatorios | OK (2 × "Este campo es obligatorio.") |
| 13 | Tirar x1 en un banner desde `/simular/` | Redirige a `/resultado/` | OK (302 a `/resultado/`) |
| 14 | Tirar x10 en un banner | Redirige a `/resultado/`; el pity del banner avanza o se reinicia si salió un 5★ | OK |
| 15 | Abrir `/resultado/` y `/dashboard/` después de tirar | Resultado de la última simulación; el dashboard muestra el pity por banner y el historial | OK (200 en ambas) |
 
## C. Compartir, feed y protección CSRF
 
| # | Acción / entrada | Resultado esperado | Observado |
|---|------------------|--------------------|-----------|
| 16 | Presionar "Compartir" en una tirada propia y abrir `/feed/` | La tirada queda marcada como compartida y aparece en el feed con el nombre del usuario | OK |
| 17 | Intentar compartir la tirada de otro usuario (POST a `/compartir/<id ajeno>/`) | Error 404; la tirada no cambia | OK (404; sigue sin compartir) |
| 18 | Enviar el formulario de `/simular/` sin token CSRF | Django lo rechaza | OK (403) |
| 19 | Enviar el formulario de login sin token CSRF | Django lo rechaza | OK (403) |
 
## D. Catálogo y creación de personajes y armas (`ItemForm`)
 
Para las filas 22 a 31, abrir `/items/nuevo/` con una cuenta de **administrador** (`vice` o `luis`).
 
| # | Acción / entrada | Resultado esperado | Observado |
|---|------------------|--------------------|-----------|
| 20 | Sin sesión, escribir directo `/items/nuevo/` | Redirige a `/cuentas/login/?next=/items/nuevo/`; no muestra el formulario | OK (302 al login) |
| 21 | Sin sesión, abrir `/` y el detalle de un personaje | Ambas páginas cargan (son públicas) | OK (200 en ambas) |
| 22 | Crear un personaje válido: nombre nuevo (ej. `Prueba Uno`), categoría Personaje, 4 estrellas, banner permanente, ataque `300`, descripción de 20 caracteres y una imagen JPG, PNG o WEBP de menos de 2 MB | Se guarda, muestra un mensaje de éxito, redirige al detalle del nuevo item y ahí se ve la imagen subida | OK |
| 23 | Crear un item con un nombre que ya existe (ej. `jiyan`, en minúsculas) | Se rechaza con el mensaje de que ya existe; no se crea el item | OK (rechazado; no permite nombres repetidos) |
| 24 | Nombre de un solo carácter (ej. `A`) | Se rechaza: "al menos 2 caracteres" | OK ("El nombre debe tener al menos 2 caracteres.") |
| 25 | Subir un archivo de imagen con formato no permitido (ej. `.gif` o `.pdf`) | Se rechaza: "Formato no permitido" | OK |
| 26 | Subir una imagen de más de 2 MB | Se rechaza: "La imagen pesa más de 2 MB" | OK |
| 27 | Ataque base `50` y luego `801` | Se rechaza: "debe estar entre 100 y 800" | OK ("El ataque base debe estar entre 100 y 800.") |
| 28 | Descripción de `hola` (menos de 10 caracteres) y luego una de más de 600 caracteres | Se rechaza en ambos casos, indicando el largo permitido | OK |
| 29 | Categoría Arma en un banner de personaje limitado | Se rechaza: el banner "solo admite personajes" | OK |
| 30 | 5 estrellas en un banner limitado sin marcar "destacado"; luego marcar "destacado" en un 4 estrellas | Ambos se rechazan, con el motivo bajo la casilla "destacado" | OK |
| 31 | Crear un 5 estrellas destacado en un banner limitado que ya tiene uno | Se rechaza indicando cuál es el destacado actual | OK |
 
## E. Slugs en el detalle de items
 
| # | Acción / entrada | Resultado esperado | Observado |
|---|------------------|--------------------|-----------|
| 32 | Abrir un personaje desde el catálogo (ej. `Verdant Summit`) | La dirección usa el nombre en minúsculas y con guiones: `/items/verdant-summit/` | OK |
| 33 | Crear un item llamado `Jiyan!` (nombre distinto de `Jiyan`, pero con el mismo slug) | Se crea con el slug `jiyan-1`; el detalle de `Jiyan` sigue en `/items/jiyan/` | OK |
 
## F. Detalle del item: descripción, ataque base e imagen
 
| # | Acción / entrada | Resultado esperado | Observado |
|---|------------------|--------------------|-----------|
| 34 | Abrir `/items/jiyan/` | Muestra la descripción y la fila "Ataque base (nivel 90): 438" | OK |
| 35 | Crear otro item válido (ej. `Prueba Dos`) sin subir imagen y abrir su detalle | Muestra la imagen genérica (`sin_imagen.jpg`), no un ícono de imagen rota | OK |
 
## G. PostgreSQL, migraciones y traslado de datos
 
| # | Acción / entrada | Resultado esperado | Observado |
|---|------------------|--------------------|-----------|
| 36 | Con la base `wuwa_tracker_DB` vacía, ejecutar `python manage.py migrate` | Aplica las migraciones `0001` a `0006` sin errores | OK |
| 37 | Ejecutar `python manage.py shell -c "from django.db import connection; print(connection.vendor)"` | Muestra `postgresql` | OK |
| 38 | Ejecutar `python manage.py loaddata datos_migracion.json` | Carga los datos sin errores | OK |
| 39 | Comparar las cantidades antes y después del traslado (tabla siguiente) | Las cinco cantidades coinciden | OK |
| 40 | Abrir `/dashboard/` con `vice` | El pity por banner y el historial coinciden con los de la versión anterior | OK |
| 41 | Abrir el detalle de un banner y de un item (ej. `Jiyan`: 5★, ataque 438, destacado) | El banner lista sus items y el item muestra el mismo banner y los mismos valores que antes | OK |
 
**Comparación de cantidades** (antes: datos exportados de SQLite en `datos_migracion.json`; después: PostgreSQL, antes de crear `staff` y `jugador`):
 
| Tabla | Antes (SQLite) | Después (PostgreSQL) | Coincide |
|-------|----------------|----------------------|----------|
| Usuarios (`auth.user`) | 2 | 2 | Sí |
| Banners | 3 | 3 | Sí |
| Items | 26 | 26 | Sí |
| Estados de pity | 4 | 4 | Sí |
| Tiradas | 30 | 30 | Sí |
 
## H. Perfiles y permisos (incluye accesos directos por URL)
 
| # | Acción / entrada | Resultado esperado | Observado |
|---|------------------|--------------------|-----------|
| 42 | Sin sesión, escribir directo `/items/gestionar/`, `/banners/gestionar/`, `/items/nuevo/`, `/banners/nuevo/`, `/items/1/editar/` y `/banners/1/editar/` | Redirige al login en las seis; no muestra nada | OK (302 al login) |
| 43 | Como Jugador, abrir `/items/gestionar/` y `/banners/gestionar/` | Se rechaza con 403 | OK (403) |
| 44 | Como Jugador, abrir `/items/nuevo/`, `/banners/nuevo/`, `/items/1/editar/` y `/banners/1/editar/` | Se rechaza con 403 en las cuatro | OK (403) |
| 45 | Como Jugador, enviar un POST a `/items/<id>/eliminar/` y `/banners/<id>/eliminar/` | Se rechaza con 403; no se elimina nada | OK (403; los registros siguen) |
| 46 | Como Staff, abrir `/items/gestionar/` y `/banners/gestionar/` | Ambas tablas cargan | OK (200) |
| 47 | Como Staff, escribir directo `/items/nuevo/` y `/banners/nuevo/` | Se rechaza con 403 | OK (403) |
| 48 | Como Staff, enviar un POST a `/items/<id>/eliminar/` y `/banners/<id>/eliminar/` | Se rechaza con 403; no se elimina nada | OK (403; los registros siguen) |
| 49 | Como Staff, editar un item y un banner válidos | Ambos se actualizan | OK |
| 50 | Como Staff, abrir el detalle de un banner | Ve "Editar banner"; no ve "Eliminar banner" ni "Agregar personaje o arma" | OK |
| 51 | Como Administrador, abrir todas las rutas de gestión, creación, edición y eliminación | Todas permiten la operación | OK |
| 52 | Como Administrador, abrir por GET `/items/<id>/eliminar/` | Se rechaza (405): solo acepta POST | OK (405) |
 
## I. CRUD de banners (`BannerForm`)
 
Cuenta de **administrador**, salvo donde se indica.
 
| # | Acción / entrada | Resultado esperado | Observado |
|---|------------------|--------------------|-----------|
| 53 | **Crear:** banner válido (nombre nuevo, tipo, descripción corta, sin portada) | Se guarda, muestra mensaje de éxito y redirige a su detalle | OK |
| 54 | **Crear:** nombre ya existente (ej. `danza del viento: jiyan`) | Se rechaza: ya existe un banner con ese nombre; no se guarda | OK |
| 55 | **Crear:** nombre de 2 caracteres | Se rechaza: "al menos 3 caracteres" | OK |
| 56 | **Crear:** descripción de más de 400 caracteres | Se rechaza indicando el largo y el máximo | OK |
| 57 | **Crear:** enviar el formulario sin token CSRF | Django lo rechaza | OK (403) |
| 58 | **Consultar:** abrir `/banners/` y el detalle de un banner | El listado muestra todos los banners; el detalle muestra tipo, descripción, destacado e items | OK |
| 59 | **Consultar:** en `/banners/gestionar/` buscar por nombre y filtrar por tipo | La tabla muestra solo los que coinciden y se pagina | OK |
| 60 | **Actualizar:** cambiar nombre y descripción de un banner | Se guarda, muestra mensaje de éxito y el detalle refleja los cambios | OK |
| 61 | **Actualizar:** poner a un banner el nombre de otro | Se rechaza; no se modifica | OK |
| 62 | **Actualizar:** cambiar un banner que tiene personajes a tipo "arma" | Se rechaza: tiene items que no son armas | OK |
| 63 | **Actualizar:** cambiar a "permanente" un banner que tiene item destacado | Se rechaza: el permanente no tiene destacado | OK |
| 64 | **Actualizar:** enviar el formulario de edición sin token CSRF | Django lo rechaza | OK (403) |
| 65 | **Eliminar:** presionar "Eliminar banner" en uno sin items, tiradas ni pity | Pide confirmación; al confirmar, se elimina y muestra mensaje de éxito | OK |
| 66 | **Eliminar:** presionar "Eliminar banner" y cancelar la confirmación | No se elimina nada | OK |
| 67 | **Eliminar:** intentar eliminar un banner con items o tiradas (ej. `Banner Permanente`) | Se bloquea y el mensaje indica cuántos items, tiradas o registros de pity tiene; el banner sigue | OK |
| 68 | **Eliminar:** enviar el POST de eliminación sin token CSRF | Django lo rechaza; no se elimina | OK (403) |
 
## J. CRUD de items (personajes y armas)
 
Crear con datos válidos e inválidos está en la sección D. Cuenta de **administrador**, salvo donde se indica.
 
| # | Acción / entrada | Resultado esperado | Observado |
|---|------------------|--------------------|-----------|
| 69 | **Consultar:** abrir `/items/gestionar/`, buscar por nombre, filtrar por categoría, rareza y banner, y cambiar de página | La tabla muestra solo lo que coincide y pagina de a 10 | OK |
| 70 | **Actualizar:** editar nombre, descripción y ataque base de un item (ej. `Prueba Uno`) | Se guarda, muestra mensaje de éxito y el detalle refleja los cambios | OK |
| 71 | **Actualizar:** cambiar el nombre de un item | El slug no cambia y el detalle sigue en la misma dirección | OK |
| 72 | **Actualizar:** poner a un item un nombre ya usado por otro | Se rechaza; no se modifica | OK |
| 73 | **Actualizar:** editar el destacado de un banner limitado (ej. `Jiyan`) | Banner, rareza y "destacado" aparecen bloqueados; si se manipula el formulario para cambiarlos, el servidor ignora el cambio | OK |
| 74 | **Actualizar:** mover un item a un banner que no admite su categoría | Se rechaza con el motivo | OK |
| 75 | **Actualizar:** enviar el formulario de edición sin token CSRF | Django lo rechaza | OK (403) |
| 76 | **Eliminar:** presionar "Eliminar" en un item creado en las pruebas y que no ha salido en tiradas (ej. `Prueba Dos`) | Pide confirmación; al confirmar, se elimina, se borra su archivo de imagen (salvo la genérica) y muestra mensaje de éxito | OK |
| 77 | **Eliminar:** presionar "Eliminar" y cancelar la confirmación | No se elimina nada | OK |
| 78 | **Eliminar:** intentar eliminar un item que ya salió en tiradas (ej. `Jiyan`) | Se bloquea; el mensaje indica en cuántas tiradas aparece y el item sigue | OK |
| 79 | **Eliminar:** enviar el POST de eliminación sin token CSRF | Django lo rechaza; no se elimina | OK (403) |
 
## K. Integridad de relaciones e información histórica
 
| # | Acción / entrada | Resultado esperado | Observado |
|---|------------------|--------------------|-----------|
| 80 | Editar un item que ya salió en tiradas (nombre o descripción) y abrir `/dashboard/` | El historial conserva las mismas tiradas, ahora con el nombre actualizado | OK |
| 81 | Editar un banner que tiene tiradas y pity y abrir `/dashboard/` | El pity y el historial del banner se conservan | OK |
| 82 | Tras intentar eliminar un item o banner protegido (filas 67 y 78), revisar tiradas y pity | Las cantidades no cambian | OK |
| 83 | Simular tiradas después de editar un banner o un item | La simulación sigue funcionando con los datos actualizados | OK |
 
## L. Portada del banner
 
| # | Acción / entrada | Resultado esperado | Observado |
|---|------------------|--------------------|-----------|
| 84 | Crear o editar un banner subiendo una imagen válida (ej. `banner-personaje.jpg`, 1920×1080) | Se guarda; la portada se ve en `/banners/` y en el detalle | OK |
| 85 | Subir una imagen demasiado pequeña (menos de 1200×500) | Se rechaza indicando las medidas de la imagen y las requeridas | OK |
| 86 | Subir una imagen con proporción fuera de rango (ej. cuadrada de 1500×1500) | Se rechaza indicando su proporción | OK |
| 87 | Subir un archivo con formato no permitido o de más de 2 MB | Se rechaza | OK |
| 88 | Editar un banner con portada y subir otra imagen válida | Se reemplaza y se ve la nueva | OK |
| 89 | Editar un banner con portada, marcar «Limpiar» y guardar | Se quita; el banner muestra la imagen genérica (o el degradado, si es el permanente) | OK |
| 90 | Abrir un banner sin portada propia | Muestra `banner_default.svg`; el permanente muestra el degradado oscuro con el collage de personajes | OK |