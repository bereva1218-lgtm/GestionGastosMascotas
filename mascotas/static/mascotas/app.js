/* Interacciones mínimas de la interfaz. Sin dependencias. */
(function () {
    'use strict';

    var raiz = document.documentElement;

    /* --- Tema claro/oscuro --- */
    function temaActual() {
        if (raiz.dataset.theme) return raiz.dataset.theme;
        return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }
    function pintarIconoTema() {
        var oscuro = temaActual() === 'dark';
        document.querySelectorAll('[data-tema-icono="claro"]').forEach(function (el) { el.hidden = oscuro; });
        document.querySelectorAll('[data-tema-icono="oscuro"]').forEach(function (el) { el.hidden = !oscuro; });
    }
    document.querySelectorAll('[data-cambiar-tema]').forEach(function (boton) {
        boton.addEventListener('click', function () {
            var nuevo = temaActual() === 'dark' ? 'light' : 'dark';
            raiz.dataset.theme = nuevo;
            try { localStorage.setItem('tema', nuevo); } catch (e) { /* almacenamiento no disponible */ }
            pintarIconoTema();
        });
    });
    pintarIconoTema();

    /* --- Menú lateral en pantallas pequeñas --- */
    var app = document.querySelector('[data-app]');
    var botonMenu = document.querySelector('[data-abrir-menu]');
    function menu(abierto) {
        if (!app) return;
        app.classList.toggle('app--menu-abierto', abierto);
        if (botonMenu) botonMenu.setAttribute('aria-expanded', String(abierto));
    }
    if (botonMenu) botonMenu.addEventListener('click', function () { menu(!app.classList.contains('app--menu-abierto')); });
    document.querySelectorAll('[data-cerrar-menu]').forEach(function (el) { el.addEventListener('click', function () { menu(false); }); });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape') menu(false); });

    /* --- Avisos: cierre manual y automático --- */
    function cerrarAviso(aviso) {
        aviso.classList.add('saliendo');
        setTimeout(function () { aviso.remove(); }, 220);
    }
    document.querySelectorAll('[data-aviso]').forEach(function (aviso) {
        var boton = aviso.querySelector('[data-cerrar-aviso]');
        if (boton) boton.addEventListener('click', function () { cerrarAviso(aviso); });
        if (!aviso.classList.contains('aviso--error')) {
            setTimeout(function () { if (aviso.isConnected) cerrarAviso(aviso); }, 6000);
        }
    });

    /* --- Total en vivo: contenedor [data-calcular-total] con
           [data-cantidad], [data-valor-unitario] (inputs) y [data-total] (salida) --- */
    var formatoPesos = new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 2 });
    document.querySelectorAll('[data-calcular-total]').forEach(function (contenedor) {
        var cantidad = contenedor.querySelector('[data-cantidad] input, input[data-cantidad]');
        var valor = contenedor.querySelector('[data-valor-unitario] input, input[data-valor-unitario]');
        var salida = contenedor.querySelector('[data-total]');
        if (!cantidad || !valor || !salida) return;
        function actualizar() {
            var c = parseFloat(String(cantidad.value).replace(',', '.'));
            var v = parseFloat(String(valor.value).replace(',', '.'));
            salida.textContent = (c > 0 && v > 0) ? formatoPesos.format(c * v) : '—';
        }
        cantidad.addEventListener('input', actualizar);
        valor.addEventListener('input', actualizar);
        actualizar();
    });

    /* --- Evitar doble envío de formularios --- */
    document.querySelectorAll('form[method="post"]').forEach(function (form) {
        form.addEventListener('submit', function () {
            var boton = form.querySelector('button[type="submit"]:not([data-sin-bloqueo])');
            if (boton) setTimeout(function () { boton.disabled = true; boton.setAttribute('aria-busy', 'true'); }, 0);
        });
    });

    /* --- Imprimir --- */
    document.querySelectorAll('[data-imprimir]').forEach(function (boton) {
        boton.addEventListener('click', function () { window.print(); });
    });
})();
