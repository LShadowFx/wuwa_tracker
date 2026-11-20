/*
 * Pruebas del JavaScript de los formularios, sin navegador ni librerias:
 *     node tests_js/reglas_formularios.test.js
 * Se carga cada script real de static/js/ contra un DOM falso minimo y se simulan
 * las acciones de la persona (elegir un banner, cambiar la rareza, pulsar la casilla...).
 */
const fs = require('fs');
const path = require('path');
const assert = require('assert');

const JS = path.join(__dirname, '..', 'static', 'js');
const leer = (nombre) => fs.readFileSync(path.join(JS, nombre), 'utf8');

// ---------- DOM falso ----------
function elemento(id, o) {
    o = o || {};
    const registro = o.registro;
    const e = {
        id, dataset: {}, style: {}, hidden: false, textContent: '', className: '',
        checked: !!o.checked, disabled: !!o.disabled, _attrs: {}, _handlers: {}, _hijos: [],
        classList: new Set(),
        setAttribute(k, v) { this._attrs[k] = String(v); },
        getAttribute(k) { return k in this._attrs ? this._attrs[k] : null; },
        removeAttribute(k) { delete this._attrs[k]; },
        addEventListener(tipo, fn) { (this._handlers[tipo] = this._handlers[tipo] || []).push(fn); },
        appendChild(hijo) { hijo.parentElement = this; this._hijos.push(hijo); if (hijo.id && registro) registro[hijo.id] = hijo; },
        remove() { if (registro) delete registro[this.id]; },
        closest() { return this.parentElement; },
        disparar(tipo) {
            const evento = { cancelado: false, preventDefault() { this.cancelado = true; } };
            (this._handlers[tipo] || []).forEach((f) => f(evento));
            return evento;
        },
    };
    // Como el navegador: leer innerHTML de un nodo con texto devuelve ese texto escapado.
    let html = '';
    Object.defineProperty(e, 'innerHTML', {
        get: () => (e.textContent ? String(e.textContent).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;') : html),
        set: (v) => { html = v; e.textContent = ''; },
    });
    const cl = e.classList;
    e.classList = {
        add: (c) => cl.add(c), remove: (c) => cl.delete(c), contains: (c) => cl.has(c),
        toggle: (c, forzar) => { (forzar === undefined ? !cl.has(c) : forzar) ? cl.add(c) : cl.delete(c); },
    };
    e.roja = () => cl.has('is-invalid');
    return e;
}

function select(id, opciones, valor, registro) {
    const e = elemento(id, { registro });
    e.options = opciones.map(([v, t]) => ({ value: v, text: t, disabled: false }));
    let actual = valor;
    Object.defineProperty(e, 'value', {
        get: () => actual,
        set: (v) => { actual = v; e.selectedIndex = e.options.findIndex((o) => o.value === v); },
    });
    e.selectedIndex = Math.max(0, e.options.findIndex((o) => o.value === valor));
    e.elegir = (v) => { e.value = v; e.disparar('change'); };
    return e;
}

// ---------- Formulario de items ----------
const DATOS = {
    1: { tipo: 'permanente', items: [{ id: 3, nombre: 'Calcharo', rareza: 5, peso: 30, categoria: 'personaje', destacado: false },
                                      { id: 4, nombre: 'Verina', rareza: 5, peso: 10, categoria: 'personaje', destacado: false }] },
    2: { tipo: 'arma', items: [{ id: 1, nombre: 'Verdant', rareza: 5, peso: 10, categoria: 'arma', destacado: true },
                                { id: 2, nombre: 'Espada4', rareza: 4, peso: 20, categoria: 'arma', destacado: false }] },
    3: { tipo: 'personaje', items: [] },
};
const BANNERS = [['', '---'], ['1', 'Permanente'], ['2', 'ArmaLim'], ['3', 'Vacio']];

function formularioItem(o) {
    const R = {};
    const E = {
        'datos-prob': { textContent: JSON.stringify(o.datos || DATOS) },
        probPreview: elemento('probPreview', { registro: R }),
        id_probabilidad: Object.assign(elemento('id_probabilidad', { registro: R }), { value: o.peso !== undefined ? o.peso : '10' }),
        id_banner: select('id_banner', BANNERS, o.banner || '', R),
        id_categoria: select('id_categoria', [['', '--'], ['personaje', 'Personaje'], ['arma', 'Arma']], o.cat || '', R),
        id_rareza: select('id_rareza', [['', '--'], ['4', '4 estrellas'], ['5', '5 estrellas']], o.rar || '', R),
        id_es_destacado: elemento('id_es_destacado', { checked: o.chk, disabled: o.fijo, registro: R }),
        avisoDestacado: elemento('avisoDestacado', { registro: R }),
        envoltorioDestacado: elemento('envoltorioDestacado', { registro: R }),
    };
    if (o.itemId) E.probPreview.dataset.itemId = String(o.itemId);
    ['id_banner', 'id_categoria', 'id_rareza', 'id_es_destacado'].forEach((k) => { E[k].parentElement = elemento('div_' + k, { registro: R }); });
    if (o.rojaDelServidor) E.id_rareza.classList.add('is-invalid');
    Object.assign(R, E);
    global.document = { getElementById: (id) => R[id] || null, createElement: () => elemento('', { registro: R }) };
    new Function(leer('prob_vista_previa.js'))();
    E.msg = (campo) => (R['candado-' + campo] || {}).textContent;
    return E;
}

// ---------- Formulario de banners ----------
function formularioBanner(resumen, tipo) {
    const E = {
        'datos-banner': { textContent: JSON.stringify(resumen) },
        id_tipo: select('id_tipo', [['', '--'], ['personaje', 'Personaje limitado'], ['arma', 'Arma limitada'], ['permanente', 'Permanente']], tipo),
        avisoTipo: elemento('avisoTipo'),
    };
    global.document = { getElementById: (id) => E[id] || null };
    new Function(leer('banner_reglas.js'))();
    E.bloqueadas = () => E.id_tipo.options.filter((o) => o.disabled).map((o) => o.value);
    return E;
}

// ---------- confirmar.js ----------
function confirmar() {
    const sucesos = { modales: 0, enviados: [], textos: {} };
    const h3 = { textContent: '' }, p = { textContent: '' };
    const dialogo = Object.assign(elemento('dialogo'), {
        querySelector: (s) => (s === 'h3' ? h3 : p),
        showModal() { sucesos.modales++; }, close() {},
    });
    let alEnviar;
    global.HTMLDialogElement = function () {};
    global.document = {
        createElement: () => dialogo, body: { appendChild() {} },
        addEventListener: (t, f) => { if (t === 'submit') alEnviar = f; },
    };
    new Function(leer('confirmar.js'))();
    const form = (confirma) => ({
        dataset: confirma ? { confirmar: 'Se eliminará «X».', titulo: '¿Eliminar item?' } : {},
        matches: (s) => confirma && s === 'form[data-confirmar]', submit() { sucesos.enviados.push(this); },
    });
    const enviar = (f) => { const ev = { target: f, cancelado: false, preventDefault() { this.cancelado = true; } }; alEnviar(ev); return ev; };
    const pulsar = (accion) => dialogo._handlers.click.forEach((fn) => fn({ target: { getAttribute: () => accion } }));
    return { sucesos, h3, p, form, enviar, pulsar };
}

// ---------- ejecutor ----------
const pruebas = [];
const prueba = (nombre, fn) => pruebas.push([nombre, fn]);

// Reglas del destacado
prueba('J01 banner limitado vacío + 5★: el destacado se marca solo y queda bloqueado', () => {
    const E = formularioItem({ banner: '3', cat: 'personaje', rar: '5' });
    assert.strictEqual(E.id_es_destacado.checked, true);
    assert.strictEqual(E.id_es_destacado.getAttribute('aria-disabled'), 'true');
    assert.match(E.avisoDestacado.textContent, /siempre es el destacado/);
});
prueba('J02 si luego baja a 4★ se desmarca y la rareza NO queda atrapada', () => {
    const E = formularioItem({ banner: '3', cat: 'personaje', rar: '5' });
    E.id_rareza.elegir('4');
    assert.strictEqual(E.id_es_destacado.checked, false);
    assert.strictEqual(E.id_rareza.disabled, false);
    E.id_rareza.elegir('5');
    assert.strictEqual(E.id_es_destacado.checked, true);
});
prueba('J03 banner que ya tiene destacado + 5★: rareza en rojo con el nombre y casilla bloqueada sin marcar', () => {
    const E = formularioItem({ banner: '2', cat: 'arma', rar: '5' });
    assert.ok(E.id_rareza.roja());
    assert.match(E.msg('id_rareza'), /ya tiene su 5★ destacado \(Verdant\)/);
    assert.strictEqual(E.id_es_destacado.checked, false);
    assert.strictEqual(E.id_es_destacado.getAttribute('aria-disabled'), 'true');
});
prueba('J04 en ese mismo banner con 4★: la opción 5★ queda deshabilitada y se explica', () => {
    const E = formularioItem({ banner: '2', cat: 'arma', rar: '4' });
    assert.strictEqual(E.id_rareza.options[2].disabled, true);
    assert.strictEqual(E.id_rareza.options[1].disabled, false);
    assert.match(E.avisoDestacado.textContent, /solo se pueden agregar items de 4★/);
});
prueba('J05 al corregir el error, la marca roja y su mensaje desaparecen', () => {
    const E = formularioItem({ banner: '2', cat: 'arma', rar: '5' });
    E.id_rareza.elegir('4');
    assert.strictEqual(E.id_rareza.roja(), false);
    assert.strictEqual(E.msg('id_rareza'), undefined);
});
prueba('J06 cambiar a un banner sin destacado libera la rareza 5★', () => {
    const E = formularioItem({ banner: '2', cat: 'personaje', rar: '4' });
    E.id_banner.elegir('3');
    assert.strictEqual(E.id_rareza.options[2].disabled, false);
});
prueba('J07 categoría incompatible con el banner: roja con mensaje', () => {
    const E = formularioItem({ banner: '2', cat: 'personaje', rar: '4' });
    assert.ok(E.id_categoria.roja());
    assert.match(E.msg('id_categoria'), /«ArmaLim» solo admite armas/);
});
prueba('J08 en banner limitado se deshabilita la categoría que no calza (la elegida se respeta)', () => {
    const E = formularioItem({ banner: '2', cat: '', rar: '4' });
    assert.strictEqual(E.id_categoria.options[1].disabled, true);   // personaje
    assert.strictEqual(E.id_categoria.options[2].disabled, false);  // arma
});
prueba('J09 el banner permanente acepta ambas categorías y no tiene destacado', () => {
    const E = formularioItem({ banner: '1', cat: 'personaje', rar: '5', chk: true });
    assert.strictEqual(E.id_categoria.roja(), false);
    assert.ok(E.id_categoria.options.every((o) => !o.disabled));
    assert.strictEqual(E.id_es_destacado.checked, false);
    assert.match(E.avisoDestacado.textContent, /permanente no tiene item destacado/);
});
prueba('J10 un 4★ en banner limitado: la casilla se desmarca y se explica por qué', () => {
    const E = formularioItem({ banner: '3', cat: 'personaje', rar: '4', chk: true });
    assert.strictEqual(E.id_es_destacado.checked, false);
    assert.match(E.avisoDestacado.textContent, /Solo un item de 5 estrellas/);
});
prueba('J11 sin banner o sin rareza elegidos: casilla libre y sin avisos', () => {
    const E = formularioItem({ banner: '', cat: '', rar: '' });
    assert.strictEqual(E.id_es_destacado.getAttribute('aria-disabled'), 'false');
    assert.strictEqual(E.avisoDestacado.hidden, true);
});
prueba('J12 destacado fijo desde el servidor: el script no cambia nada de la casilla ni del aviso', () => {
    const E = formularioItem({ banner: '2', cat: 'arma', rar: '5', chk: true, fijo: true, itemId: 1 });
    E.avisoDestacado.textContent = 'aviso del servidor';
    E.id_banner.disparar('change');
    assert.strictEqual(E.id_es_destacado.checked, true);
    assert.strictEqual(E.avisoDestacado.textContent, 'aviso del servidor');
    assert.strictEqual(E.id_rareza.roja(), false);
});
prueba('J13 casilla bloqueada: el click se cancela; casilla libre: el click pasa', () => {
    const E = formularioItem({ banner: '3', cat: 'personaje', rar: '5' });
    assert.strictEqual(E.id_es_destacado.disparar('click').cancelado, true);
    const L = formularioItem({ banner: '', cat: '', rar: '' });
    assert.strictEqual(L.id_es_destacado.disparar('click').cancelado, false);
});
prueba('J14 un item editado no cuenta como "otro destacado" de sí mismo', () => {
    // Verdant (id 1) es el destacado de su banner: al editarlo no debe chocar consigo mismo.
    const E = formularioItem({ banner: '2', cat: 'arma', rar: '5', itemId: 1 });
    assert.strictEqual(E.id_rareza.roja(), false);
    assert.strictEqual(E.id_es_destacado.checked, true);
});
prueba('J15 un error que ya puso el servidor no se borra al recalcular', () => {
    const E = formularioItem({ banner: '3', cat: 'personaje', rar: '4', rojaDelServidor: true });
    E.id_rareza.disparar('change');
    assert.ok(E.id_rareza.roja());
});

// Vista previa de probabilidad
prueba('J16 vista previa: único del grupo sale 100 %', () => {
    const E = formularioItem({ banner: '3', cat: 'personaje', rar: '4' });
    assert.match(E.probPreview.innerHTML, /único 4★.*100 %/);
});
prueba('J17 vista previa: pesos 60 y 20 reparten 75 % / 25 %', () => {
    const E = formularioItem({ banner: '2', cat: 'arma', rar: '4', peso: '60' });
    assert.match(E.probPreview.innerHTML, /saldrá el <b>75 %<\/b>/);
    assert.match(E.probPreview.innerHTML, /Espada4: 25 %/);
});
prueba('J18 vista previa: pesos inválidos piden un valor entre 1 y 100', () => {
    for (const peso of ['', '0', '101', 'abc']) {
        const E = formularioItem({ banner: '1', cat: 'personaje', rar: '4', peso });
        assert.match(E.probPreview.textContent, /entre 1 y 100/, 'peso ' + peso);
    }
});
prueba('J19 vista previa: el destacado no usa probabilidad', () => {
    const E = formularioItem({ banner: '3', cat: 'personaje', rar: '5' });
    assert.match(E.probPreview.innerHTML, /destacado.*no usa probabilidad/);
});
prueba('J20 sin los datos del servidor el script no hace nada y no falla', () => {
    global.document = { getElementById: () => null };
    new Function(leer('prob_vista_previa.js'))();
});

// Formulario de banners
prueba('B01 banner de armas con destacado: personaje y permanente bloqueados, arma disponible', () => {
    const E = formularioBanner({ personajes: 0, armas: 2, destacados: 1, cinco_sin_destacado: 0 }, 'arma');
    assert.deepStrictEqual(E.bloqueadas(), ['personaje', 'permanente']);
    assert.match(E.avisoTipo.textContent, /Personaje limitado \(tiene 2 armas y ese tipo solo admite personajes\)/);
    assert.match(E.avisoTipo.textContent, /Permanente \(tiene 1 item destacado y el permanente no admite destacados\)/);
});
prueba('B02 banner vacío: ningún tipo bloqueado y sin aviso', () => {
    const E = formularioBanner({ personajes: 0, armas: 0, destacados: 0, cinco_sin_destacado: 0 }, 'arma');
    assert.deepStrictEqual(E.bloqueadas(), []);
    assert.strictEqual(E.avisoTipo.hidden, true);
});
prueba('B03 permanente con 5★ sin destacado: no puede pasar a ningún limitado', () => {
    const E = formularioBanner({ personajes: 3, armas: 0, destacados: 0, cinco_sin_destacado: 1 }, 'permanente');
    assert.deepStrictEqual(E.bloqueadas(), ['personaje', 'arma']);
    assert.match(E.avisoTipo.textContent, /el único 5★ es el destacado/);
});
prueba('B04 una opción elegida pero incompatible se marca en rojo con el motivo', () => {
    const E = formularioBanner({ personajes: 4, armas: 0, destacados: 1, cinco_sin_destacado: 0 }, 'personaje');
    E.id_tipo.value = 'arma';
    E.id_tipo.disparar('change');
    assert.ok(E.id_tipo.roja());
    assert.strictEqual(E.avisoTipo.className, 'aviso-regla aviso-regla--error');
    assert.match(E.avisoTipo.textContent, /el banner tiene 4 personajes y ese tipo solo admite armas/);
});
prueba('B05 singular y plural correctos (1 arma / 2 armas)', () => {
    const uno = formularioBanner({ personajes: 0, armas: 1, destacados: 0, cinco_sin_destacado: 0 }, 'arma');
    assert.match(uno.avisoTipo.textContent, /tiene 1 arma y/);
    const dos = formularioBanner({ personajes: 0, armas: 2, destacados: 0, cinco_sin_destacado: 0 }, 'arma');
    assert.match(dos.avisoTipo.textContent, /tiene 2 armas y/);
});
prueba('B06 al crear un banner (sin datos) el script no hace nada y no falla', () => {
    global.document = { getElementById: () => null };
    new Function(leer('banner_reglas.js'))();
});

// Confirmar eliminar (delegación)
prueba('C01 enviar un formulario de eliminar abre el diálogo y NO envía todavía', () => {
    const c = confirmar(); const f = c.form(true);
    assert.strictEqual(c.enviar(f).cancelado, true);
    assert.strictEqual(c.sucesos.modales, 1);
    assert.strictEqual(c.h3.textContent, '¿Eliminar item?');
    assert.strictEqual(c.sucesos.enviados.length, 0);
});
prueba('C02 "Sí, eliminar" envía el formulario; "Cancelar" no', () => {
    const c = confirmar(); const f = c.form(true);
    c.enviar(f); c.pulsar('cancelar');
    assert.strictEqual(c.sucesos.enviados.length, 0);
    c.enviar(f); c.pulsar('confirmar');
    assert.deepStrictEqual(c.sucesos.enviados, [f]);
});
prueba('C03 un formulario cualquiera (sin data-confirmar) se envía normal', () => {
    const c = confirmar();
    assert.strictEqual(c.enviar(c.form(false)).cancelado, false);
    assert.strictEqual(c.sucesos.modales, 0);
});
prueba('C04 formularios que aparecen después (filtros en vivo) también piden confirmación', () => {
    const c = confirmar();
    const filaNueva = c.form(true);  // creada después de cargar el script
    assert.strictEqual(c.enviar(filaNueva).cancelado, true);
});

let fallos = 0;
pruebas.forEach(([nombre, fn]) => {
    try { fn(); console.log('  ✓ ' + nombre); }
    catch (e) { fallos++; console.log('  ✗ ' + nombre + '\n      ' + String(e.message).split('\n').join('\n      ')); }
});
console.log('\n' + (pruebas.length - fallos) + ' de ' + pruebas.length + ' pruebas correctas');
process.exit(fallos ? 1 : 0);
