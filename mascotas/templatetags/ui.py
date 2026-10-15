"""Etiquetas y filtros de presentación compartidos por todas las plantillas.

Uso: {% load ui %}. La referencia visual está en Context/DisenoUI.md.
"""
from django import template
from django.template.defaultfilters import floatformat
from django.utils import timezone
from django.utils.html import format_html
from django.utils.text import slugify

from ..reglas import calcular_edad

register = template.Library()

TONOS_AVATAR = 6


@register.simple_tag
def icono(nombre, clase=''):
    """SVG del sprite de `includes/iconos.html`: {% icono 'plus' %} o {% icono 'plus' 'icono--lg' %}."""
    clases = f'icono {clase}'.strip()
    return format_html(
        '<svg class="{}" aria-hidden="true" focusable="false"><use href="#i-{}"></use></svg>',
        clases, nombre,
    )


@register.filter
def moneda(valor):
    """Pesos con separadores locales; sin decimales si el valor es entero: $ 133.000 / $ 12.500,50."""
    return f'$\xa0{floatformat(valor or 0, "-2g")}'


@register.filter
def edad(fecha_nacimiento):
    """Edad legible a partir de la fecha de nacimiento: '2 años', '6 meses', 'Menos de 1 mes'."""
    if not fecha_nacimiento:
        return ''
    try:
        anios, meses = calcular_edad(fecha_nacimiento, timezone.localdate())
    except ValueError:
        return ''
    if anios:
        return f'{anios} año' if anios == 1 else f'{anios} años'
    if meses:
        return f'{meses} mes' if meses == 1 else f'{meses} meses'
    return 'Menos de 1 mes'


@register.filter
def absoluto(valor):
    return abs(valor) if valor is not None else valor


@register.filter
def inicial(texto):
    return str(texto)[:1].upper()


@register.filter
def tono(objeto):
    """Clase de color estable para el avatar de un objeto con pk: avatar--t0 … avatar--t5."""
    return f'avatar--t{(objeto.pk or 0) % TONOS_AVATAR}'


@register.filter
def clase_categoria(categoria):
    """Modificador de color por categoría: 'cat-comida', 'cat-medicamentos', 'cat-juguetes'."""
    return f'cat-{slugify(str(categoria))}'


@register.simple_tag(takes_context=True)
def seccion_actual(context):
    """Sección de la URL actual ('inicio', 'mascota', 'gasto', 'medicamento', 'reportes')."""
    coincidencia = getattr(context.get('request'), 'resolver_match', None)
    if not coincidencia or not coincidencia.url_name:
        return ''
    return coincidencia.url_name.split('_')[0]


@register.inclusion_tag('includes/campo.html')
def campo(field, prefijo='', sufijo='', ancho=''):
    """Campo de formulario con etiqueta, ayuda y errores.

    {% campo form.valor_unitario prefijo='$' %} · {% campo form.notas ancho='completo' %}
    """
    return {'field': field, 'prefijo': prefijo, 'sufijo': sufijo, 'ancho': ancho}
