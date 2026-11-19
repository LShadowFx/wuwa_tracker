/*
 * Vista previa de la probabilidad en el formulario de items.
 * Toma el peso que escribes y los items que ya tiene el banner elegido (misma rareza),
 * y calcula: peso del item * 100 / (suma de todos los pesos del grupo).
 * Es solo una ayuda visual: el calculo real lo hace el servidor.
 */
(function () {
    var datos = document.getElementById('datos-prob');
    var caja = document.getElementById('probPreview');
    var peso = document.getElementById('id_probabilidad');
    var banner = document.getElementById('id_banner');
    var rareza = document.getElementById('id_rareza');
    var destacado = document.getElementById('id_es_destacado');
    if (!datos || !caja || !peso || !banner || !rareza) return;

    var grupos = JSON.parse(datos.textContent);
    var itemId = caja.dataset.itemId ? parseInt(caja.dataset.itemId, 10) : null;
    var MAX_LISTA = 8;

    function porcentaje(numero) {
        return numero.toLocaleString('es-CL', { maximumFractionDigits: 1 }) + ' %';
    }

    function escapar(texto) {
        var div = document.createElement('div');
        div.textContent = texto;
        return div.innerHTML;
    }

    function actualizar() {
        if (destacado && destacado.checked) {
            caja.innerHTML = 'El item <b>destacado</b> no usa probabilidad: sale por la regla del banner (el 50/50).';
            return;
        }

        var valor = parseInt(peso.value, 10);
        if (isNaN(valor) || valor < 1 || valor > 100) {
            caja.textContent = 'Escribe un peso entre 1 y 100 para ver la vista previa.';
            return;
        }
        if (!banner.value || !rareza.value) {
            caja.textContent = 'Elige el banner y la rareza para ver la probabilidad.';
            return;
        }

        var nivel = parseInt(rareza.value, 10);
        var nombreBanner = banner.options[banner.selectedIndex].text;
        var otros = (grupos[banner.value] || []).filter(function (i) {
            return i.rareza === nivel && i.id !== itemId;
        });

        if (!otros.length) {
            caja.innerHTML = 'Es el único ' + nivel + '★ de «' + escapar(nombreBanner) + '», así que sale el <b>100 %</b> de las veces sin importar el peso.';
            return;
        }

        var total = otros.reduce(function (suma, i) { return suma + i.peso; }, valor);
        var html = 'Con peso <b>' + valor + '</b>, este item saldrá el <b>' + porcentaje(valor * 100 / total) +
            '</b> de las veces cuando caiga un ' + nivel + '★ en «' + escapar(nombreBanner) + '».' +
            '<ul>';
        otros.slice(0, MAX_LISTA).forEach(function (i) {
            html += '<li>' + escapar(i.nombre) + ': ' + porcentaje(i.peso * 100 / total) + '</li>';
        });
        if (otros.length > MAX_LISTA) {
            html += '<li>y ' + (otros.length - MAX_LISTA) + ' más…</li>';
        }
        caja.innerHTML = html + '</ul>';
    }

    [peso, banner, rareza, destacado].forEach(function (campo) {
        if (!campo) return;
        campo.addEventListener('input', actualizar);
        campo.addEventListener('change', actualizar);
    });
    actualizar();
})();
