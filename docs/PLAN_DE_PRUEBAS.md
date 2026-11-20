# Plan de pruebas

Complementa a `COMPROBACIONES.md` (pruebas manuales en el navegador). Aquí están las pruebas
**automáticas** y las pruebas manuales nuevas del candado en vivo y de la gestión con filtros.

## 1. Tipos de prueba usados

| Tipo | Qué comprueba | Dónde está |
|---|---|---|
| **Unitaria** | Una sola función o regla, aislada. El azar se reemplaza con `mock` para que siempre dé lo mismo. | `gacha/tests/test_unitarias_*.py` |
| **Integración** | Varias piezas trabajando juntas: vista + formulario + modelo + plantilla, con peticiones HTTP reales. | `gacha/tests/test_integracion_vistas.py` |
| **Sistema (extremo a extremo)** | Un recorrido completo como lo haría una persona: login, crear, tirar, ver historial, eliminar. | `gacha/tests/test_sistema_flujos.py` |
| **Regresión** | Un error que ya existió no puede volver. Ej.: dejar a un banner sin destacado con un POST manipulado. | marcadas como `regresion` en el nombre |
| **Seguridad** | Permisos por perfil, CSRF, redirección segura al login, escape de HTML. | `PermisosTests`, `SeguridadTests` |
| **Pruebas del JavaScript** | Las reglas en vivo del navegador, con un DOM falso. | `tests_js/reglas_formularios.test.js` |
| **Manual / aceptación** | Lo visual (colores, bloqueo al pasar el mouse, filtros sin recargar). Sección 5. | este documento |

La idea de fondo: el **servidor es la autoridad** y el **JavaScript es un espejo** que avisa antes.
Por eso casi cada regla se prueba dos veces: en el servidor (Python) y en el espejo (JS).

## 2. Cómo ejecutarlas

```
python manage.py test gacha            # 131 pruebas de Python (usa una base de datos de prueba)
node tests_js/reglas_formularios.test.js   # 30 pruebas de JavaScript (no necesita instalar nada)
```

`manage.py test` crea y borra su propia base `test_wuwa_tracker_DB` en PostgreSQL: el usuario de la
base necesita permiso para crear bases de datos. No toca los datos reales.

## 3. Resumen de lo automatizado (161 pruebas)

| Archivo | Pruebas | Cubre |
|---|---|---|
| `test_unitarias_modelos_pity.py` | 27 | `probabilidad_real`, slug único, destacado del banner, curva de pity (soft y hard), elección del 5★ (50/50, garantizado, arma limitada, permanente), pity de 4★, guardado de tiradas |
| `test_unitarias_forms.py` | 45 | Cada campo de `ItemForm` y `BannerForm` (nombre, peso 1–100, ataque 100–800, descripción, imagen), reglas de categoría y de destacado, candado del destacado fijo, cambio de tipo de banner, formularios de filtro y de simulación |
| `test_integracion_vistas.py` | 50 | Matriz de permisos (visitante/jugador/staff/admin), filtros y paginación de 10 en gestionar, formato de datos que consume el JS, crear/editar/eliminar con mensajes, regresión del POST manipulado |
| `test_sistema_flujos.py` | 10 | Admin arma un banner y un jugador tira; 50/50 perdido y luego garantizado; staff solo edita; cambio de tipo; CSRF; tiradas ajenas; login seguro; escape de HTML |
| `reglas_formularios.test.js` | 30 | Reglas en vivo del formulario de items (J01–J20), del de banners (B01–B06) y confirmación de eliminar (C01–C04) |

## 4. Reglas de negocio y quién las prueba

| # | Regla | Servidor (Python) | Espejo (JS) |
|---|---|---|---|
| R1 | La categoría del item debe calzar con el banner limitado | `ItemFormReglasDeNegocioTests` | J07, J08 |
| R2 | Solo un 5★ puede ser destacado | `…test_destacado_en_un_4_estrellas…` | J10 |
| R3 | El permanente no tiene destacado | `…test_destacado_en_banner_permanente…` | J09 |
| R4 | Un banner limitado tiene un solo destacado | `…test_segundo_destacado…` | J03, J04 |
| R5 | En un banner limitado, el 5★ es el destacado | `…test_5_estrellas_en_banner_limitado…` | J01, J02 |
| R6 | El destacado de un limitado no puede cambiar de banner, de rareza ni dejar de serlo | `ItemFormDestacadoFijoTests`, `test_regresion_post_manipulado…` | J12, J14 |
| R7 | El tipo de un banner no puede contradecir sus items | `BannerFormTests` | B01–B05 |
| R8 | Solo el admin crea y elimina; staff solo edita | `PermisosTests`, `FlujoStaffTests` | — |
| R9 | No se elimina lo que ya tiene tiradas o items | `EliminarTests`, `FlujoAdminArmeBannerTests` | — |
| R10 | Eliminar siempre pide confirmación, también tras filtrar en vivo | `test_staff_y_jugador_no_ven…` | C01–C04 |
| R11 | Gestionar pagina de a 10 y filtra | `GestionarItemsTests`, `GestionarBannersTests` | (manual M09–M13) |

## 5. Pruebas manuales nuevas (en el navegador)

Completar la columna **Observado** al ejecutarlas, igual que en `COMPROBACIONES.md`.
Entrar como admin (`/items/nuevo/` y `/banners/gestionar/`). Datos: usar un banner de arma limitada con su destacado.

### E. Reglas en vivo del formulario de items

| # | Acción / entrada | Resultado esperado | Observado |
|---|------------------|--------------------|-----------|
| M01 | Elegir un banner limitado sin destacado y rareza 5★ | La casilla "destacado" se marca sola, se ve atenuada y no se puede desmarcar; aviso explicando por qué | _(completar)_ |
| M02 | Sin tocar nada más, cambiar la rareza a 4★ | La casilla se desmarca; la rareza no queda trabada | _(completar)_ |
| M03 | Elegir un banner que ya tiene destacado y rareza 5★ | La rareza se marca en rojo con el nombre del destacado actual; la casilla queda bloqueada sin marcar | _(completar)_ |
| M04 | En ese mismo banner, abrir la lista de rareza | La opción 5★ está deshabilitada y hay un aviso | _(completar)_ |
| M05 | Elegir categoría Personaje en un banner de armas | La categoría se marca en rojo: "solo admite armas"; la opción Personaje queda deshabilitada al cambiar de banner | _(completar)_ |
| M06 | Elegir el banner permanente | La casilla destacado se desmarca y se bloquea; categoría y rareza libres | _(completar)_ |
| M07 | Cambiar de banner varias veces seguidas | Marcas y avisos se actualizan al instante y no queda ninguno viejo | _(completar)_ |
| M08 | Corregir el error (cambiar a 4★ o a otro banner) y presionar Guardar | El rojo desaparece y se guarda sin errores | _(completar)_ |
| M09 | Editar el destacado de un banner limitado | Banner, rareza y casilla aparecen bloqueados; aviso "quedan fijos"; el nombre y la descripción sí se pueden cambiar y se guardan | _(completar)_ |
| M10 | Desde las herramientas del navegador, quitar `disabled` a esos campos, cambiar la rareza a 4★ y guardar | El servidor ignora el cambio: el item sigue 5★, destacado y en su banner | _(completar)_ |

### F. Banners y gestión

| # | Acción / entrada | Resultado esperado | Observado |
|---|------------------|--------------------|-----------|
| M11 | Editar un banner de armas que tiene destacado | En "Tipo", Permanente y Personaje limitado aparecen deshabilitados y un aviso dice por qué | _(completar)_ |
| M12 | Editar un banner vacío | Los tres tipos se pueden elegir y no hay aviso | _(completar)_ |
| M13 | Gestionar items: escribir en el buscador y cambiar los selectores | La tabla se actualiza sin recargar la página y la URL cambia | _(completar)_ |
| M14 | Con más de 10 items, mirar el pie de la tabla y pasar de página | Muestra 10 por página, "Página X de Y" y Anterior/Siguiente que conservan los filtros | _(completar)_ |
| M15 | Filtrar en vivo y luego presionar "Eliminar" en una fila | Aparece el diálogo de confirmación (no borra directo) | _(completar)_ |
| M16 | Gestionar banners: buscar por nombre y filtrar por tipo | Igual que items: en vivo, con conteo y paginación de 10 | _(completar)_ |
| M17 | Entrar como staff a Gestionar | Ve la tabla y "Editar", pero no "Crear" ni "Eliminar" | _(completar)_ |

## 6. Limitaciones conocidas (para reconocerlas en la presentación)

Dos pruebas documentan el comportamiento actual en vez de esconderlo; si algún día se corrige, hay que actualizarlas.

1. **Banner limitado sin destacado** (`test_limitacion_conocida_banner_limitado_sin_destacado…`): si un admin elimina el
   destacado, el pity se reinicia al llegar a 5★ pero no se crea ninguna tirada. Lo evita el formulario al editar, no el borrado.
2. **Pesos en cero** (`test_limitacion_conocida_pesos_en_cero_revientan`): solo ocurre saltándose los formularios
   (`shell` o `.update()`); `random.choices` lanza `ValueError` y la simulación cae en error 500.
3. **`/admin/` de Django** no usa `ItemForm` ni `BannerForm`: las reglas de negocio solo rigen en las vistas del sitio.
4. El JavaScript se probó con un DOM falso, no con un navegador real: lo visual (colores, atenuado) se cubre con las pruebas manuales M01–M17.
