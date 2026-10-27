// Menu desplegable en pantallas chicas y marca del link activo.
(function () {
    var boton = document.getElementById('navToggle');
    var menu = document.getElementById('navMenu');
    if (boton && menu) {
        boton.addEventListener('click', function () {
            menu.classList.toggle('abierto');
        });
    }

    // Marca el link activo segun la URL actual
    document.querySelectorAll('.nav-link-w').forEach(function (a) {
        if (a.getAttribute('href') === location.pathname) a.classList.add('activo');
    });
})();
