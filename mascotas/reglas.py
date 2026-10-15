"""Reglas de negocio puras (sin base de datos).

Cada función tiene una sola responsabilidad. Los modelos y las vistas las usan,
y se prueban sin crear registros (ver `test_reglas.py`).
"""
from decimal import Decimal


def calcular_valor_total(cantidad, valor_unitario):
    """Total de un gasto: cantidad × valor unitario."""
    return cantidad * valor_unitario


def validar_mes(mes):
    if not 1 <= mes <= 12:
        raise ValueError(f'Mes inválido: {mes}. Debe estar entre 1 y 12.')


def es_del_mes(fecha, anio, mes):
    return fecha.year == anio and fecha.month == mes


def total_mensual(gastos, anio, mes):
    """Suma `valor_total` de los gastos cuya fecha cae en el mes `mes` del año `anio`."""
    validar_mes(mes)
    return sum(
        (g.valor_total for g in gastos if es_del_mes(g.fecha, anio, mes)),
        Decimal('0'),
    )
