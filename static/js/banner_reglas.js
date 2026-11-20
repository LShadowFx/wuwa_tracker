/*
 * Formulario de banners (solo al editar): reglas en vivo al cambiar el tipo.
 * Usa #datos-banner = { personajes, armas, destacados, cinco_sin_destacado } con lo que el
 * banner tiene hoy, y repite BannerForm.clean(). El servidor sigue validando de verdad.
 *
 *  - Permanente: no se puede si algun item es destacado.
 *  - Personaje / arma limitada: no se puede si tiene items de la otra categoria, ni si tiene
 *    algun 5★ que no sea el destacado.
 * Las opciones no disponibles se deshabilitan (la elegida se respeta) y se explica por que.
 */
(function () {
    var datos = document.getElementById('datos-banner');
    var tipo = document.getElementById('id_tipo');
    var aviso = document.getElementById('avisoTipo');
    if (!datos || !tipo || !aviso) return;

    var d = JSON.parse(datos.textContent);

    function plural(n, singular, plural) {
        return n + ' ' + (n === 1 ? singular : plural);
    }

    // Devuelve el motivo por el que ese tipo no se puede elegir, o '' si se puede.
    function motivo(valor) {
        if (valor === 'permanente') {
            return d.destacados
                ? 'tiene ' + plural(d.destacados, 'item destacado', 'items destacados') +
                ' y el permanente no admite destacados'
                : '';
        }
        if (valor === 'personaje' || valor === 'arma') {
            var esPersonaje = valor === 'personaje';
            var otros = esPersonaje ? d.armas : d.personajes;
            if (otros) {
                return 'tiene ' + (esPersonaje ? plural(otros, 'arma', 'armas') : plural(otros, 'personaje', 'personajes')) +
                    ' y ese tipo solo admite ' + (esPersonaje ? 'personajes' : 'armas');
            }
            if (d.cinco_sin_destacado) {
                return 'tiene ' + plural(d.cinco_sin_destacado, '5★ que no es el destacado', '5★ que no son el destacado') +
                    ' y en un banner limitado el único 5★ es el destacado';
            }
        }
        return '';
    }

    function nombreTipo(opcion) {
        return opcion.text;
    }

    function revisar() {
        var bloqueadas = [];
        Array.prototype.forEach.call(tipo.options, function (opcion) {
            var razon = opcion.value ? motivo(opcion.value) : '';
            opcion.disabled = !!razon && opcion.value !== tipo.value;
            if (razon && opcion.value !== tipo.value) bloqueadas.push(nombreTipo(opcion) + ' (' + razon + ')');
        });

        var razonActual = tipo.value ? motivo(tipo.value) : '';
        tipo.classList.toggle('is-invalid', !!razonActual);
        if (razonActual) {
            aviso.hidden = false;
            aviso.className = 'aviso-regla aviso-regla--error';
            aviso.textContent = 'No se puede dejar este tipo: el banner ' + razonActual + '. Arregla sus items primero.';
        } else if (bloqueadas.length) {
            aviso.hidden = false;
            aviso.className = 'aviso-regla aviso-regla--info';
            aviso.textContent = 'Tipos no disponibles para este banner: ' + bloqueadas.join('; ') + '.';
        } else {
            aviso.hidden = true;
            aviso.textContent = '';
        }
    }

    tipo.addEventListener('change', revisar);
    revisar();
})();