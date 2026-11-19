/*
 * Confirmacion antes de eliminar.
 * Cualquier <form data-confirmar="texto" data-titulo="titulo"> abre un dialogo;
 * el formulario solo se envia si el usuario pulsa "Si, eliminar".
 * (La validacion real de permisos y del borrado se hace igualmente en el servidor.)
 */
(function () {
    var formularios = document.querySelectorAll('form[data-confirmar]');
    if (!formularios.length || typeof HTMLDialogElement === 'undefined') return;

    var dialogo = document.createElement('dialog');
    dialogo.className = 'dialogo-w';
    dialogo.innerHTML =
        '<h3></h3><p></p>' +
        '<div class="acciones-form">' +
        '<button type="button" class="btn-w btn-w--fantasma btn-w--sm" data-accion="cancelar">Cancelar</button>' +
        '<button type="button" class="btn-w btn-w--peligro btn-w--sm" data-accion="confirmar">Sí, eliminar</button>' +
        '</div>';
    document.body.appendChild(dialogo);

    var titulo = dialogo.querySelector('h3');
    var texto = dialogo.querySelector('p');
    var pendiente = null;

    formularios.forEach(function (form) {
        form.addEventListener('submit', function (evento) {
            evento.preventDefault();
            pendiente = form;
            titulo.textContent = form.dataset.titulo || '¿Eliminar?';
            texto.textContent = form.dataset.confirmar || 'Esta acción no se puede deshacer.';
            dialogo.showModal();
        });
    });

    dialogo.addEventListener('click', function (evento) {
        var accion = evento.target.getAttribute('data-accion');
        if (accion === 'cancelar') {
            pendiente = null;
            dialogo.close();
        } else if (accion === 'confirmar' && pendiente) {
            var formulario = pendiente;
            pendiente = null;
            dialogo.close();
            formulario.submit();
        }
    });
})();
