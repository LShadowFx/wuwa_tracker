# Comprobaciones realizadas

Cada fila es una comprobación con su acción o entrada, el resultado esperado y el resultado observado al
ejecutar el proyecto en el navegador (`python manage.py runserver`).

Usuario usado para las pruebas con sesión: `vice` o `luis` (ver README).

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

Para las filas 22 a 31, abrir `/items/nuevo/` con sesión iniciada.

| # | Acción / entrada | Resultado esperado | Observado |
|---|------------------|--------------------|-----------|
| 20 | Sin sesión, escribir directo `/items/nuevo/` | Redirige a `/cuentas/login/?next=/items/nuevo/`; no muestra el formulario | _(completar)_ |
| 21 | Sin sesión, abrir `/` y el detalle de un personaje | Ambas páginas cargan (son públicas) | _(completar)_ |
| 22 | Crear un personaje válido: nombre nuevo (ej. `Prueba Uno`), categoría Personaje, 4 estrellas, banner permanente, ataque `300`, descripción de 20 caracteres y una imagen JPG, PNG o WEBP de menos de 2 MB | Se guarda, muestra un mensaje de éxito, redirige al detalle del nuevo item y ahí se ve la imagen subida | _(completar)_ |
| 23 | Crear un item con un nombre que ya existe (ej. `jiyan`, en minúsculas) | Se rechaza con el mensaje de que ya existe; no se crea el item | Rechazado, no permite crear un item con nombre repetido |
| 24 | Nombre de un solo carácter (ej. `A`) | Se rechaza: "al menos 2 caracteres" | _(completar)_ |
| 25 | Subir un archivo de imagen con formato no permitido (ej. `.gif` o `.pdf`) | Se rechaza: "Formato no permitido" | _(completar)_ |
| 26 | Subir una imagen de más de 2 MB | Se rechaza: "La imagen pesa más de 2 MB" | _(completar)_ |
| 27 | Ataque base `50` y luego `801` | Se rechaza: "debe estar entre 100 y 800" | _(completar)_ |
| 28 | Descripción de `hola` (menos de 10 caracteres) y luego una de más de 600 caracteres | Se rechaza en ambos casos, indicando el largo permitido | _(completar)_ |
| 29 | Categoría Arma en un banner de personaje limitado | Se rechaza: el banner "solo admite personajes" | _(completar)_ |
| 30 | 5 estrellas en un banner limitado sin marcar "destacado"; luego marcar "destacado" en un 4 estrellas | Ambos se rechazan, con el motivo bajo la casilla "destacado" | _(completar)_ |
| 31 | Crear un 5 estrellas destacado en un banner limitado que ya tiene uno | Se rechaza indicando cuál es el destacado actual | _(completar)_ |

## E. Slugs en el detalle de items

| # | Acción / entrada | Resultado esperado | Observado |
|---|------------------|--------------------|-----------|
| 32 | Abrir un personaje desde el catálogo (ej. `Verdant Summit`) | La dirección usa el nombre en minúsculas y con guiones: `/items/verdant-summit/` | Correcto: la dirección muestra el nombre, con guiones donde hay espacios |
| 33 | Crear un item llamado `Jiyan!` (nombre distinto de `Jiyan`, pero con el mismo slug) | Se crea con el slug `jiyan-1`; el detalle de `Jiyan` sigue en `/items/jiyan/` | _(completar)_ |

## F. Detalle del item: descripción, ataque base e imagen

| # | Acción / entrada | Resultado esperado | Observado |
|---|------------------|--------------------|-----------|
| 34 | Abrir `/items/jiyan/` | Muestra la descripción y la fila "Ataque base (nivel 90): 438" | _(completar)_ |
| 35 | Crear otro item válido (ej. `Prueba Dos`) sin subir imagen y abrir su detalle | Muestra la imagen genérica (`sin_imagen.jpg`), no un ícono de imagen rota | _(completar)_ |
