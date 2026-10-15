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


def variacion_porcentual(actual, anterior):
    """Cambio porcentual de `anterior` a `actual`, con un decimal. None si no hay base."""
    if not anterior:
        return None
    return ((actual - anterior) * 100 / anterior).quantize(Decimal('0.1'))


def ultimos_meses(hoy, cantidad):
    """Los `cantidad` meses que terminan en el de `hoy`, como (año, mes) en orden cronológico."""
    if cantidad < 1:
        raise ValueError('La cantidad de meses debe ser al menos 1.')
    actual = hoy.year * 12 + hoy.month - 1  # meses contados desde el año 0
    meses = []
    for indice in range(actual - cantidad + 1, actual + 1):
        anio, mes = divmod(indice, 12)
        meses.append((anio, mes + 1))
    return meses


def calcular_edad(nacimiento, hoy):
    """Edad cumplida como (años, meses)."""
    if nacimiento > hoy:
        raise ValueError('La fecha de nacimiento no puede ser futura.')
    meses = (hoy.year - nacimiento.year) * 12 + hoy.month - nacimiento.month
    if hoy.day < nacimiento.day:
        meses -= 1
    return divmod(meses, 12)


def meses_entre(inicio, fin):
    """Meses de `inicio` a `fin` (ambos incluidos) como (año, mes), en orden cronológico."""
    if fin < inicio:
        raise ValueError('La fecha final no puede ser anterior a la inicial.')
    return ultimos_meses(fin, (fin.year - inicio.year) * 12 + fin.month - inicio.month + 1)
