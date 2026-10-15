"""Etiquetas y filtros de presentación compartidos por todas las plantillas.

Uso: {% load ui %}. La referencia visual está en Context/DisenoUI.md.
"""
from django import template
from django.template.defaultfilters import date as formato_fecha, floatformat
from django.utils import timezone
from django.utils.html import format_html
from django.utils.text import slugify

from ..reglas import calcular_edad

register = template.Library()

TONOS_AVATAR = 6
ICONOS_CATEGORIA = {'comida': 'comida', 'medicamentos': 'pastilla', 'juguetes': 'regalo'}
DIAS_AVISO_MEDICAMENTO = 3


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
    """Clase de color estable para un avatar a partir de un objeto con pk o de un id: avatar--t0 … avatar--t5."""
    pk = getattr(objeto, 'pk', objeto)
    return f'avatar--t{(pk or 0) % TONOS_AVATAR}'


@register.filter
def clase_categoria(categoria):
    """Modificador de color por categoría: 'cat-comida', 'cat-medicamentos', 'cat-juguetes'."""
    return f'cat-{slugify(str(categoria))}'


@register.filter
def icono_categoria(categoria):
    """Icono de una categoría de gasto: 'comida', 'pastilla', 'regalo' o 'paquete' para las demás."""
    return ICONOS_CATEGORIA.get(slugify(str(categoria)), 'paquete')


@register.filter
def fecha_larga(fecha):
    """'15 de octubre de 2026' (el formato del idioma pone el mes en mayúscula)."""
    if not fecha:
        return ''
    return formato_fecha(fecha, r'j \d\e F \d\e Y').lower()


@register.filter
def porcentaje(parte, total):
    """Participación entera de `parte` en `total`: '25 %', '< 1 %' o '0 %'."""
    if not total or not parte:
        return '0\xa0%'
    valor = round(parte * 100 / total)
    return '<\xa01\xa0%' if valor < 1 else f'{valor}\xa0%'


def estado_medicamento(medicamento):
    """Texto y variante de insignia del estado de un tratamiento."""
    dias = medicamento.dias_restantes
    if medicamento.fecha_inicio > timezone.localdate():
        return {'texto': 'Programado', 'variante': 'primario'}
    if dias is None:
        return {'texto': 'Continuo', 'variante': 'info'}
    if dias < 0:
        return {'texto': 'Finalizado', 'variante': 'neutra'}
    if dias == 0:
        return {'texto': 'Termina hoy', 'variante': 'aviso'}
    texto = 'Queda 1 día' if dias == 1 else f'Quedan {dias} días'
    return {'texto': texto, 'variante': 'aviso' if dias <= DIAS_AVISO_MEDICAMENTO else 'exito'}


@register.inclusion_tag('includes/estado_medicamento.html')
def insignia_medicamento(medicamento):
    """Insignia de estado de un tratamiento: {% insignia_medicamento m %}."""
    return estado_medicamento(medicamento)


@register.simple_tag(takes_context=True)
def seccion_actual(context):
    """Sección de la URL actual ('inicio', 'mascota', 'gasto', 'medicamento', 'reportes')."""
    coincidencia = getattr(context.get('request'), 'resolver_match', None)
    if not coincidencia or not coincidencia.url_name:
        return ''
    return coincidencia.url_name.split('_')[0]


@register.inclusion_tag('includes/campo.html')
def campo(field, prefijo='', sufijo='', ancho='', error=False):
    """Campo de formulario con etiqueta, ayuda y errores.

    {% campo form.valor_unitario prefijo='$' %} · {% campo form.notas ancho='completo' %}
    `error` marca el campo aunque el error sea del formulario (p. ej. un rango de fechas invertido):
    {% campo rango.desde error=rango.non_field_errors %}
    """
    return {'field': field, 'prefijo': prefijo, 'sufijo': sufijo, 'ancho': ancho, 'error': bool(error)}
