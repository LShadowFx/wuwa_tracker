# Fuentes y herramientas utilizadas

Cada fila indica qué se usó, para qué y cómo se verificó su aporte. Los textos marcados con
**[completar]** deben escribirse con lo que el equipo realmente hizo.

| Fuente / herramienta | Finalidad | Cómo se verificó su aporte |
|----------------------|-----------|----------------------------|
| Documentación de Django — docs.djangoproject.com | Vistas, formularios (`Form` y `ModelForm`), `ImageField` y `request.FILES`, autenticación, sesiones, `SlugField` y `slugify` | Se probó cada ruta y cada formulario en el navegador (ver `COMPROBACIONES.md`) |
| Proyecto de ejemplo del docente (`anuncios`, app `diariomural`) | Guía de la lógica: subir imágenes con `ImageField` + `enctype="multipart/form-data"` + `request.FILES`, plantilla "maestra" con includes, y slugs en las rutas de detalle | Se comparó el flujo con el de este proyecto y se comprobó creando un item con imagen desde el formulario (ver comprobaciones 22 y 32) |
| django-crispy-forms + crispy-bootstrap5 | Mostrar formularios (login, simulación y creación de items) con estilos y errores por campo | Se enviaron los formularios con datos inválidos y se vio el mensaje de cada campo |
| Bootstrap 5 y fuentes locales | Estilos base de la interfaz | Revisión visual en el navegador |
| Prydwen — prydwen.gg/wuthering-waves (páginas de stats y de armas) | Ataque base a nivel 90 de los 16 personajes y 10 armas, y estadística secundaria de las armas | Se comprobó que los nombres coincidieran con los 26 items de la base. Comparamos con otras paginas o wikis para tener los datos reales y ver que concordaran. |
| Sportskeeda y PCGamesN (guías de armas de *Wuthering Waves*) | Efectos de algunas armas (regeneración de energía y bonos de ataque) usados en las descripciones | Las descripciones se redactaron con palabras propias, no se copió el texto del juego. Se hizo segun lo que sabiamos |
| wuthering.gg/es | Nombres de personajes y armas del fixture `datos_iniciales.json` e imágenes | Nombre para todos los personajes y armas que se ven en la pagina |
| Claude (Anthropic), asistente de IA | Revisión del proyecto contra la pauta, apoyo para escribir los campos `descripcion` y `ataque_base`, las validaciones de `ItemForm`, scripts de carga de datos de un solo uso y la documentación, búsqueda de los datos del juego | Cada cambio se ejecutó y probó localmente antes de incorporarlo (ver `COMPROBACIONES.md`), y los scripts de un solo uso se retiraron después de ejecutarse |
