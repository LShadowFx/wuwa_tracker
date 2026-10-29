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
