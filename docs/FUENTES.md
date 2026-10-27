# Fuentes y herramientas utilizadas

> Revisar y ajustar: debe decir la verdad sobre qué se usó, para qué y cómo se verificó.

| Fuente / herramienta | Finalidad | Cómo se verificó su aporte |
|----------------------|-----------|----------------------------|
| Documentación de Django (vistas, formularios, autenticación, sesiones) — docs.djangoproject.com | Construcción de las vistas, el formulario de simulación, el login y la protección de rutas | Se probó cada ruta en el navegador (ver `COMPROBACIONES.md`) |
| django-crispy-forms + crispy-bootstrap5 | Mostrar formularios (login y simulación) con estilos y errores por campo | Se envió el formulario con datos inválidos y se vio el mensaje de cada campo |
| Bootstrap 5 y Google Fonts (CDN) | Estilos base de la interfaz | Revisión visual en el navegador |
| Claude (Anthropic), asistente de IA | Revisión del proyecto contra la pauta | Ayuda en creacion y redaccion de documentacion |
| Datos de personajes y armas de *Wuthering Waves* (fuente: *https://wuthering.gg/es*) | Contenido del fixture `datos_iniciales.json` y de las imágenes |
