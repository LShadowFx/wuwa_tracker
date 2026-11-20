/*
 * Filtros en tiempo real, reutilizable en cualquier pagina.
 * Se activa en todo formulario que tenga el atributo [data-filtros-vivos],
 * usando data-resultados="idDeLaZona" para saber que bloque reemplazar
 * (si no se indica, usa "resultados" por defecto). Asi el mismo archivo
 * sirve para el catalogo (zona "resultados") y para la gestion de items
 * (zona "resultadosGestion"), sin duplicar logica.
 *
 * - Selects: se aplican apenas eliges una opcion.
 * - Buscador de texto: se aplica mientras escribes (espera 300 ms tras la ultima tecla).
 * La pagina no se recarga: se pide la misma URL al servidor con los filtros elegidos y
 * solo se reemplaza la zona de resultados. La URL se actualiza para poder recargar o compartir.
 * Si algo falla, se envia el formulario de forma normal (el servidor sigue haciendo el filtrado).
 */
(function () {
    function iniciar(form) {
        var zona = document.getElementById(form.dataset.resultados || 'resultados');
        if (!zona || !window.fetch || !window.URLSearchParams) return;

        var boton = form.querySelector('button[type="submit"]');
        if (boton) boton.hidden = true; // ya no hace falta "Filtrar"

        var espera = null;
        var pedido = null;

        function urlConFiltros() {
            var params = new URLSearchParams(new FormData(form));
            // No enviar filtros vacios, para mantener una URL limpia.
            Array.from(params.keys()).forEach(function (clave) {
                if (params.get(clave) === '') params.delete(clave);
            });
            var texto = params.toString();
            return form.getAttribute('action') || window.location.pathname + (texto ? '?' + texto : '');
        }

        function aplicar() {
            var url = urlConFiltros();
            if (pedido) pedido.abort();
            pedido = new AbortController();
            zona.style.opacity = '0.5';

            fetch(url, { signal: pedido.signal, headers: { 'X-Requested-With': 'XMLHttpRequest' } })
                .then(function (respuesta) {
                    if (!respuesta.ok) throw new Error('Respuesta ' + respuesta.status);
                    return respuesta.text();
                })
                .then(function (html) {
                    var documento = new DOMParser().parseFromString(html, 'text/html');
                    var nueva = documento.getElementById(zona.id);
                    if (!nueva) throw new Error('Sin zona de resultados');
                    zona.innerHTML = nueva.innerHTML;
                    zona.style.opacity = '';
                    window.history.replaceState(null, '', url);
                })
                .catch(function (error) {
                    if (error.name === 'AbortError') return; // llego una busqueda mas nueva
                    form.submit(); // plan B: envio normal
                });
        }

        form.addEventListener('change', function (evento) {
            if (evento.target.tagName === 'SELECT') aplicar();
        });

        form.addEventListener('input', function (evento) {
            if (evento.target.type === 'text' || evento.target.type === 'search') {
                clearTimeout(espera);
                espera = setTimeout(aplicar, 300);
            }
        });

        form.addEventListener('submit', function (evento) {
            evento.preventDefault(); // Enter en el buscador: aplicar al instante
            clearTimeout(espera);
            aplicar();
        });
    }

    document.querySelectorAll('[data-filtros-vivos]').forEach(iniciar);
})();