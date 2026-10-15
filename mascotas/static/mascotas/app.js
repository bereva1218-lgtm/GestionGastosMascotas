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
    /* Mismo formato que el filtro |moneda: sin decimales si el valor es entero, con dos si no. */
    var pesosEnteros = new Intl.NumberFormat('es-CO', { maximumFractionDigits: 0 });
    var pesosDecimales = new Intl.NumberFormat('es-CO', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    function formatoPesos(valor) {
        var redondeado = Math.round(valor * 100) / 100;
        return '$ ' + (Number.isInteger(redondeado) ? pesosEnteros : pesosDecimales).format(redondeado);
    }
    document.querySelectorAll('[data-calcular-total]').forEach(function (contenedor) {
        var cantidad = contenedor.querySelector('[data-cantidad] input, input[data-cantidad]');
        var valor = contenedor.querySelector('[data-valor-unitario] input, input[data-valor-unitario]');
        var salida = contenedor.querySelector('[data-total]');
        if (!cantidad || !valor || !salida) return;
        function actualizar() {
            var c = parseFloat(String(cantidad.value).replace(',', '.'));
            var v = parseFloat(String(valor.value).replace(',', '.'));
            salida.textContent = (c > 0 && v > 0) ? formatoPesos(c * v) : '—';
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

    /* --- Imprimir: siempre en tema claro --- */
    document.querySelectorAll('[data-imprimir]').forEach(function (boton) {
        boton.addEventListener('click', function () { window.print(); });
    });
    var temaAntesDeImprimir = null;
    window.addEventListener('beforeprint', function () {
        temaAntesDeImprimir = raiz.dataset.theme || '';
        raiz.dataset.theme = 'light';
    });
    window.addEventListener('afterprint', function () {
        if (temaAntesDeImprimir === null) return;
        if (temaAntesDeImprimir) raiz.dataset.theme = temaAntesDeImprimir; else delete raiz.dataset.theme;
        temaAntesDeImprimir = null;
    });

    /* --- «Volver atrás»: solo si hay una página anterior en el historial --- */
    document.querySelectorAll('[data-volver]').forEach(function (boton) {
        if (window.history.length > 1) boton.hidden = false;
        boton.addEventListener('click', function () { window.history.back(); });
    });
})();
