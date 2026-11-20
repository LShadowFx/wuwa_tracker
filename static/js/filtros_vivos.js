(function () {
    function iniciar(form) {
        var zona = document.getElementById(form.dataset.resultados || 'resultados');
        if (!zona || !window.fetch || !window.URLSearchParams) return;

        var boton = form.querySelector('button[type="submit"]');
        if (boton) boton.hidden = true;

        var espera = null;
        var pedido = null;

        function urlConFiltros() {
            var params = new URLSearchParams(new FormData(form));
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
                    if (error.name === 'AbortError') return;
                    form.submit();
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
            evento.preventDefault();
            clearTimeout(espera);
            aplicar();
        });
    }

    document.querySelectorAll('[data-filtros-vivos]').forEach(iniciar);
})();