(function () {
    var datos = document.getElementById('datos-prob');
    var caja = document.getElementById('probPreview');
    var peso = document.getElementById('id_probabilidad');
    var banner = document.getElementById('id_banner');
    var categoria = document.getElementById('id_categoria');
    var rareza = document.getElementById('id_rareza');
    var destacado = document.getElementById('id_es_destacado');
    var aviso = document.getElementById('avisoDestacado');
    var envoltorioDestacado = document.getElementById('envoltorioDestacado');
    if (!datos || !caja || !peso || !banner || !categoria || !rareza || !destacado) return;

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

    function grupoBanner() {
        return grupos[banner.value] || null;
    }

    function otrosItems() {
        var grupo = grupoBanner();
        return grupo ? grupo.items.filter(function (i) { return i.id !== itemId; }) : [];
    }

    function nombreBanner() {
        var opcion = banner.options[banner.selectedIndex];
        return banner.value && opcion ? opcion.text : 'este banner';
    }

    function envoltorio(campo) {
        return campo.closest('[id^="div_id_"]') || campo.parentElement;
    }

    function marcar(campo, texto) {
        if (!campo.classList.contains('is-invalid')) {
            campo.classList.add('is-invalid');
            campo.dataset.candado = '1';
        }
        var nodo = document.getElementById('candado-' + campo.id);
        if (!nodo) {
            nodo = document.createElement('div');
            nodo.id = 'candado-' + campo.id;
            nodo.className = 'invalid-feedback d-block';
            nodo.style.color = 'var(--rojo)';
            envoltorio(campo).appendChild(nodo);
        }
        nodo.textContent = texto;
    }

    function limpiar(campo) {
        if (campo.dataset.candado === '1') {
            campo.classList.remove('is-invalid');
            campo.dataset.candado = '';
        }
        var nodo = document.getElementById('candado-' + campo.id);
        if (nodo) nodo.remove();
    }

    function mostrarAviso(texto, esError) {
        if (!aviso) return;
        aviso.hidden = !texto;
        aviso.textContent = texto || '';
        aviso.className = 'span-2 aviso-regla aviso-regla--' + (esError ? 'error' : 'info');
    }

    function restringirOpciones(select, permitida) {
        Array.prototype.forEach.call(select.options, function (opcion) {
            opcion.disabled = !!opcion.value && opcion.value !== select.value && !permitida(opcion.value);
        });
    }

    function fijarDestacado(valor) {
        var bloqueado = valor !== null;
        if (bloqueado) destacado.checked = valor;
        destacado.setAttribute('aria-disabled', bloqueado ? 'true' : 'false');
        if (envoltorioDestacado) envoltorioDestacado.classList.toggle('chk-bloqueado', bloqueado);
    }

    function aplicarReglas() {
        var grupo = grupoBanner();
        var tipo = grupo ? grupo.tipo : null;
        var limitado = tipo === 'personaje' || tipo === 'arma';
        var nivel = parseInt(rareza.value, 10);

        limpiar(categoria);
        limpiar(rareza);

        restringirOpciones(categoria, function (v) { return !limitado || v === tipo; });
        if (limitado && categoria.value && categoria.value !== tipo) {
            marcar(categoria, 'El banner «' + nombreBanner() + '» solo admite ' +
                (tipo === 'personaje' ? 'personajes' : 'armas') + '.');
        }

        if (destacado.disabled) return;

        var otroDestacado = limitado
            ? otrosItems().filter(function (i) { return i.rareza === 5 && i.destacado; })[0]
            : null;
        restringirOpciones(rareza, function (v) { return !(otroDestacado && v === '5'); });

        if (tipo === 'permanente') {
            fijarDestacado(false);
            mostrarAviso('El banner permanente no tiene item destacado.');
        } else if (!tipo || isNaN(nivel)) {
            fijarDestacado(null);
            mostrarAviso('');
        } else if (nivel !== 5) {
            fijarDestacado(false);
            mostrarAviso(otroDestacado
                ? '«' + nombreBanner() + '» ya tiene su 5★ destacado (' + otroDestacado.nombre +
                '): aquí solo se pueden agregar items de 4★.'
                : 'Solo un item de 5 estrellas puede ser el destacado.');
        } else if (otroDestacado) {
            fijarDestacado(false);
            marcar(rareza, '«' + nombreBanner() + '» ya tiene su 5★ destacado (' + otroDestacado.nombre + ').');
            mostrarAviso('Un banner limitado tiene un solo destacado: la casilla queda bloqueada.', true);
        } else {
            fijarDestacado(true);
            mostrarAviso('En un banner limitado el 5★ siempre es el destacado: no se puede desmarcar.');
        }
    }

    function actualizarPreview() {
        if (destacado.checked) {
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
        var otros = otrosItems().filter(function (i) { return i.rareza === nivel; });

        if (!otros.length) {
            caja.innerHTML = 'Es el único ' + nivel + '★ de «' + escapar(nombreBanner()) + '», así que sale el <b>100 %</b> de las veces sin importar el peso.';
            return;
        }

        var total = otros.reduce(function (suma, i) { return suma + i.peso; }, valor);
        var html = 'Con peso <b>' + valor + '</b>, este item saldrá el <b>' + porcentaje(valor * 100 / total) +
            '</b> de las veces cuando caiga un ' + nivel + '★ en «' + escapar(nombreBanner()) + '».' +
            '<ul>';
        otros.slice(0, MAX_LISTA).forEach(function (i) {
            html += '<li>' + escapar(i.nombre) + ': ' + porcentaje(i.peso * 100 / total) + '</li>';
        });
        if (otros.length > MAX_LISTA) {
            html += '<li>y ' + (otros.length - MAX_LISTA) + ' más…</li>';
        }
        caja.innerHTML = html + '</ul>';
    }

    function actualizar() {
        aplicarReglas();
        actualizarPreview();
    }

    destacado.addEventListener('click', function (evento) {
        if (destacado.getAttribute('aria-disabled') === 'true') evento.preventDefault();
    });

    [peso, banner, categoria, rareza, destacado].forEach(function (campo) {
        campo.addEventListener('input', actualizar);
        campo.addEventListener('change', actualizar);
    });
    actualizar();
})();