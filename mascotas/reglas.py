"""Reglas de negocio puras (sin base de datos)."""
from decimal import Decimal


def total_mensual(gastos, anio, mes):
    if not 1 <= mes <= 12:
        raise ValueError(f'Mes inválido: {mes}. Debe estar entre 1 y 12.')
    total = Decimal('0')
    for gasto in gastos:
        if gasto.fecha.year == anio and gasto.fecha.month == mes:
            total += gasto.valor_total
    return total
