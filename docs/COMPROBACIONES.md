# Comprobaciones realizadas

Cada fila es una comprobación con su acción o entrada, el resultado esperado y el resultado observado al
ejecutar el proyecto. **Repetirlas en el navegador durante la demostración** y corregir la columna
"Observado" si algo difiere.

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
| 9 | Con sesión, abrir `/simular/` | Se muestra el formulario con banner y cantidad | OK (200) |
| 10 | Enviar cantidad `5`, `abc` o `-1` (con un banner válido) | Se rechaza, se vuelve al formulario marcando "Cantidad" con error; no se guarda nada | OK ("Escoja una opción válida."; sin cambios en la base) |
| 11 | Enviar banner inexistente (`999`) o vacío | Se rechaza, se marca "Banner" con error; no se guarda nada | OK ("Escoja una opción válida." / "Este campo es obligatorio.") |
| 12 | Enviar el formulario sin ningún campo | Ambos campos marcados como obligatorios | OK (2 × "Este campo es obligatorio.") |
| 13 | Tirar x1 en un banner (botón del catálogo o formulario) | Redirige a `/resultado/` | OK (302 a `/resultado/`) |
| 14 | Tirar x10 en un banner | Redirige a `/resultado/`; el pity del banner avanza o se reinicia si salió un 5★ | OK |
| 15 | Abrir `/resultado/` y `/dashboard/` después de tirar | Resultado de la última simulación; el dashboard muestra el pity por banner y el historial | OK (200 en ambas) |

## C. Compartir, feed y protección CSRF

| # | Acción / entrada | Resultado esperado | Observado |
|---|------------------|--------------------|-----------|
| 16 | Presionar "Compartir" en una tirada propia y abrir `/feed/` | La tirada queda marcada como compartida y aparece en el feed con el nombre del usuario | OK |
| 17 | Intentar compartir la tirada de otro usuario (POST a `/compartir/<id ajeno>/`) | Error 404; la tirada no cambia | OK (404; sigue sin compartir) |
| 18 | Enviar el formulario de `/simular/` sin token CSRF | Django lo rechaza | OK (403) |
| 19 | Enviar el formulario de login sin token CSRF | Django lo rechaza | OK (403) |
