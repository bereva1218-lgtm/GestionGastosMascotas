# Diseño de la interfaz

Sistema de diseño de la aplicación: un gestor administrativo sobrio, legible y
consistente en todas las vistas. La referencia viva es el panel de inicio
(`mascotas/templates/mascotas/inicio.html`).

## Principios

- **Datos primero:** totales grandes con números tabulares, tablas limpias,
  gráficos simples en CSS (sin librerías).
- **Consistencia:** las mismas piezas en todas las páginas: encabezado de
  página, tarjetas, tablas, insignias, estados vacíos.
- **Accesible:** contraste AA, foco visible, etiquetas en todos los campos,
  `aria-label` en botones de solo icono, tablas con alternativa textual para
  gráficos, respeto a `prefers-reduced-motion`.
- **Responsivo:** barra lateral fija en escritorio; menú desplegable en
  pantallas de menos de 1024 px; tablas apilables en móvil (menos de 720 px).
- **Claro y oscuro:** todos los colores salen de tokens CSS; el tema sigue al
  sistema y se puede cambiar con el botón de la barra superior.

## Archivos

| Archivo | Rol |
|---|---|
| `static/mascotas/estilos.css` | Tokens y componentes (única fuente de colores). |
| `static/mascotas/app.js` | Tema, menú móvil, cierre de avisos, total en vivo, imprimir, evitar doble envío. |
| `templates/base_documento.html` | `<html>`, fuentes, sprite de iconos, avisos, JS. Bloques: `titulo`, `css`, `js`, `clase_body`, `cuerpo`. |
| `templates/base.html` | Layout con sesión: barra lateral + barra superior + `<main>`. Bloques: `titulo`, `migas`, `accion_barra`, `contenido`. |
| `templates/base_publico.html` | Layout sin sesión (acceso/registro): panel de marca + formulario. Bloques: `titulo`, `panel`, `contenido`. |
| `templates/includes/iconos.html` | Sprite SVG (estilo Lucide). |
| `templates/includes/campo.html` | Render de un campo de formulario (lo usa `{% campo %}`). |
| `templatetags/ui.py` | Etiquetas y filtros de presentación. |
| `static/mascotas/css/<pagina>.css` | (Opcional) estilos propios de una página; solo tokens. Se cargan en `{% block css %}`. |

## Etiquetas y filtros (`{% load ui %}`)

| Uso | Resultado |
|---|---|
| `{% icono 'plus' %}` · `{% icono 'plus' 'icono--sm' %}` | SVG con `aria-hidden`. Tamaños: `icono--sm` (15), normal (18), `icono--lg` (22), `icono--xl` (28). |
| `{{ valor\|moneda }}` | `$ 133.000` o `$ 12.500,50`. Úsalo para todo valor monetario. |
| `{{ mascota.fecha_nacimiento\|edad }}` | `3 años`, `6 meses`, `Menos de 1 mes` o vacío. |
| `{{ variacion\|absoluto }}` | Valor absoluto. |
| `{{ texto\|inicial }}` | Primera letra en mayúscula (avatares). |
| `{{ objeto\|tono }}` | `avatar--t0` … `avatar--t5`, estable por `pk`. |
| `{{ categoria\|clase_categoria }}` | `cat-comida`, `cat-medicamentos`, `cat-juguetes`: colorea insignias, barras, leyendas e `icono-circulo`. |
| `{% seccion_actual as seccion %}` | Sección de la URL (`inicio`, `mascota`, `gasto`, `medicamento`, `reportes`). |
| `{% campo form.x %}` · `{% campo form.x prefijo='$' %}` · `{% campo form.x sufijo='kg' %}` · `{% campo form.x ancho='completo' %}` | Campo con etiqueta, asterisco de obligatorio, ayuda y errores (`.campo--error`). |

Iconos disponibles: `inicio huella recibo pastilla grafico torta billetera plus
editar eliminar archivar restaurar salir buscar filtro calendario sube baja
check alerta info cerrar menu sol luna usuario imprimir izquierda derecha abajo
volver etiqueta reloj salud peso paquete nota comida regalo candado escudo ojo
bandeja actividad tienda hash gota palette`.

## Componentes (clases CSS)

**Encabezado de página** (toda vista lo tiene):

```html
<header class="pagina-encabezado">
  <div class="pagina-encabezado__texto">
    <span class="pagina-encabezado__antetitulo">Gestión</span>   <!-- opcional -->
    <h1>Mascotas</h1>
    <p>Descripción breve de la vista.</p>
  </div>
  <div class="pagina-encabezado__acciones">
    <a class="btn btn--secundario" href="…">{% icono 'imprimir' %} Imprimir</a>
    <a class="btn btn--primario" href="…">{% icono 'plus' %} Nueva mascota</a>
  </div>
</header>
```

**Migas** (en `{% block migas %}`; "Inicio" ya está en la base):
`<li><a href="{% url 'mascotas:mascota_lista' %}">Mascotas</a></li><li><span aria-current="page">Michi</span></li>`

**Botones:** `btn` + `btn--primario` (una acción principal por zona), `btn--secundario`,
`btn--fantasma`, `btn--peligro`, `btn--peligro-suave`; tamaños `btn--sm`, `btn--lg`;
`btn--bloque`; solo icono: `btn btn--icono` (+ `btn--fantasma`/`btn--peligro-suave`,
`btn--sm`) **con `aria-label` y `title`**. Formularios POST en línea: `<form class="form-en-linea">`.

**Tarjeta:** `.tarjeta` > `.tarjeta__encabezado` (`.tarjeta__titulo` con icono,
`.tarjeta__subtitulo`, acciones) + `.tarjeta__cuerpo` (`--compacto`, `--sin-relleno`)
+ `.tarjeta__pie`. Variantes: `.tarjeta--interactiva`, `.tarjeta--atenuada`.

**Indicadores:** `.kpis` > `.kpi` > `.kpi__cabeza` (`.kpi__etiqueta`, `.kpi__icono`
`--info/--aviso/--juguetes/--exito`) + `.kpi__valor` (`--md`) + `.kpi__meta`.
Tendencia: `.tendencia--sube` (rojo: gastar más es alerta), `--baja` (verde), `--neutra`.

**Insignias:** `.insignia` + `--exito/--peligro/--aviso/--info/--primario/--neutra/--borde`
o una clase de categoría; punto opcional `<span class="insignia__punto"></span>`.

**Avatar:** `.avatar {{ obj|tono }}` + `--xs/--sm/--lg/--xl`, `--cuadrado`, `--inactivo`.

**Tabla:**

```html
<div class="tabla-contenedor">
  <table class="tabla tabla--apilable">
    <thead><tr><th scope="col">Producto</th><th scope="col" class="num">Total</th><th scope="col"><span class="oculto-visual">Acciones</span></th></tr></thead>
    <tbody><tr>
      <td data-label="Producto"><div class="celda-principal">…<span class="celda-principal__texto"><a class="celda-principal__titulo">…</a><span class="celda-principal__sub">…</span></span></div></td>
      <td data-label="Total" class="num fuerte">{{ g.valor_total|moneda }}</td>
      <td class="tabla__acciones"><div class="fila">…botones icono…</div></td>
    </tr></tbody>
    <tfoot>…</tfoot>  <!-- opcional -->
  </table>
</div>
```

Toda `<td>` de una `.tabla--apilable` lleva `data-label` (excepto acciones).
Filas inactivas: `tr.fila--inactiva`.

**Formularios:** `form.formulario` > varias `.formulario__seccion` (columna de texto
`.formulario__seccion-texto` con `h2` + `p`, y `.formulario__rejilla` de 2 columnas
con `{% campo %}`) > `.formulario__acciones` (barra fija inferior; nota opcional
`.formulario__acciones-nota`). Errores generales: `.alerta.alerta--peligro`.
Total en vivo: contenedor `data-calcular-total` con los campos marcados
`data-cantidad` / `data-valor-unitario` (en un elemento que envuelve el campo) y una salida
`data-total` (`.resumen-calculo`).

**Filtros:** `form.filtros` (rejilla) con `.campo` por filtro, búsqueda con
`.buscador` (icono + input), `.filtros__acciones`, errores en `.filtros__errores`.
**Segmentos/pestañas:** `.segmento` > `a[aria-current="page"]` + `.segmento__conteo`.
**Franja de resumen:** `.resumen-franja` (encima de una tabla dentro de la tarjeta).

**Estado vacío:** `.vacio` (`--compacto`) > `.vacio__icono` + `.vacio__titulo` +
`.vacio__texto` + botón. Toda lista tiene estado vacío (y uno distinto si el
vacío se debe a filtros).

**Gráficos:** columnas `.grafico-columnas` (cada `.grafico-columnas__barra`
con `style="--valor: {% widthratio v max 100 %}%"`), barras horizontales `.barras`
(`.barras__relleno` con `--valor` + clase de categoría), distribución
`.barra-apilada` + `.leyenda`. Acompañar con una tabla `.oculto-visual` o con
los valores visibles.

**Otros:** `.lista`/`.lista__item(--enlace)`, `.ficha` (dl clave/valor), `.perfil`
(cabecera de detalle con `.perfil__estadisticas` > `.estadistica`),
`.cuadricula-tarjetas` + `.tarjeta-mascota`, `.paginacion`, `.alerta--*`,
`.icono-circulo`, `.barra-herramientas`. Utilidades: `.pila(--sm/--lg)`,
`.fila(--sm/--entre)`, `.rejilla-2`, `.rejilla-3`, `.rejilla-panel` (2/3 + 1/3),
`.num`, `.texto-tenue`, `.texto-2`, `.texto-sm`, `.texto-xs`, `.fuerte`,
`.truncar`, `.oculto-visual`, `.solo-pantalla`, `.solo-impresion`.

## Reglas

1. Sin colores sueltos ni `style=""` en plantillas, salvo `--valor` de gráficos.
2. Toda vista: `{% block titulo %}`, `{% block migas %}`, `.pagina-encabezado`.
3. Dinero siempre con `|moneda`; fechas en tablas `d M Y`, en fichas `j \d\e F \d\e Y`.
4. Textos en español, en tono claro y en "tú"; mayúscula solo al inicio.
5. Las acciones destructivas usan `btn--peligro` y pasan por la página de confirmación.
