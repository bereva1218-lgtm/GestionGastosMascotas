"""Pruebas de la regla `total_mensual` (segundo parcial TPA - TDD).

Son funciones puras: no tocan la base de datos, por eso usan SimpleTestCase.
"""
from datetime import date
from decimal import Decimal
from types import SimpleNamespace

from django.test import SimpleTestCase

from .reglas import total_mensual


def gasto(fecha, valor_total):
    return SimpleNamespace(fecha=fecha, valor_total=Decimal(valor_total))


class TotalMensualTests(SimpleTestCase):
    def test_suma_solo_los_gastos_del_mes_pedido(self):
        gastos = [
            gasto(date(2026, 10, 5), '30000'),
            gasto(date(2026, 10, 20), '12500.50'),
            gasto(date(2026, 9, 28), '99999'),
        ]
        self.assertEqual(total_mensual(gastos, 2026, 10), Decimal('42500.50'))

    def test_sin_gastos_el_total_es_cero(self):
        self.assertEqual(total_mensual([], 2026, 10), Decimal('0'))

    def test_incluye_primer_y_ultimo_dia_y_excluye_mes_vecino(self):
        gastos = [
            gasto(date(2025, 12, 31), '500'),
            gasto(date(2026, 1, 1), '100'),
            gasto(date(2026, 1, 31), '200'),
            gasto(date(2026, 2, 1), '700'),
        ]
        self.assertEqual(total_mensual(gastos, 2026, 1), Decimal('300'))

    def test_mes_fuera_de_rango_es_invalido(self):
        for mes in (0, 13):
            with self.subTest(mes=mes), self.assertRaises(ValueError):
                total_mensual([], 2026, mes)

    def test_mismo_mes_de_otro_anio_no_se_suma(self):
        gastos = [
            gasto(date(2025, 10, 15), '1000'),
            gasto(date(2026, 10, 15), '250'),
        ]
        self.assertEqual(total_mensual(gastos, 2026, 10), Decimal('250'))
