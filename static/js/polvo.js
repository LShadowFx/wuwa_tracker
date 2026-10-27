// Particulas de polvo del fondo (canvas#polvo). Se desactiva si el usuario prefiere menos movimiento.
(function () {
    var c = document.getElementById('polvo');
    if (!c || window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    var x = c.getContext('2d'), W, H, P = [];
    function medir() { W = c.width = innerWidth; H = c.height = innerHeight; }
    medir(); addEventListener('resize', medir);
    for (var i = 0; i < 60; i++) {
        P.push({ x: Math.random() * W, y: Math.random() * H, r: Math.random() * 1.7 + 0.4,
                 v: Math.random() * 0.3 + 0.06, a: Math.random() * 0.5 + 0.15, d: Math.random() * 6.28 });
    }
    (function dibujar() {
        x.clearRect(0, 0, W, H);
        P.forEach(function (p) {
            p.y -= p.v; p.d += 0.004; p.x += Math.sin(p.d) * 0.25;
            if (p.y < -5) { p.y = H + 5; p.x = Math.random() * W; }
            x.beginPath(); x.fillStyle = 'rgba(120,235,245,' + p.a + ')';
            x.arc(p.x, p.y, p.r, 0, 6.283); x.fill();
        });
        requestAnimationFrame(dibujar);
    })();
})();
