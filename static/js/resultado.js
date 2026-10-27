// Las tiradas de 3 estrellas no se guardan en la base de datos, asi que
// las calculamos aqui: total pedido - cartas de 4/5 estrellas mostradas.
(function () {
    var cont = document.querySelector('[data-total]');
    var el = document.getElementById('tres-estrellas');
    if (!cont || !el) return;
    var total = parseInt(cont.dataset.total, 10) || 0;
    var vistas = document.querySelectorAll('.pull').length;
    var tres = total - vistas;
    if (tres > 0) {
        el.textContent = '+ ' + tres + ' tirada' + (tres > 1 ? 's' : '') + ' de 3★ (cuentan para tu pity)';
        el.hidden = false;
    }
})();
