"""Pruebas de las reglas puras que alimentan el panel y las fichas."""
from datetime import date
from decimal import Decimal

from django.test import SimpleTestCase

from .reglas import calcular_edad, ultimos_meses, variacion_porcentual


class VariacionPorcentualTests(SimpleTestCase):
    def test_aumento(self):
        self.assertEqual(variacion_porcentual(Decimal('150'), Decimal('100')), Decimal('50.0'))

    def test_disminucion_redondea_a_un_decimal(self):
        self.assertEqual(variacion_porcentual(Decimal('1'), Decimal('3')), Decimal('-66.7'))

    def test_sin_periodo_anterior_no_hay_variacion(self):
        self.assertIsNone(variacion_porcentual(Decimal('500'), Decimal('0')))
        self.assertIsNone(variacion_porcentual(Decimal('0'), Decimal('0')))


class UltimosMesesTests(SimpleTestCase):
    def test_cruza_el_cambio_de_anio_en_orden_cronologico(self):
        self.assertEqual(
            ultimos_meses(date(2026, 2, 15), 4),
            [(2025, 11), (2025, 12), (2026, 1), (2026, 2)],
        )

    def test_un_solo_mes(self):
        self.assertEqual(ultimos_meses(date(2026, 10, 1), 1), [(2026, 10)])

    def test_cantidad_invalida(self):
        with self.assertRaises(ValueError):
            ultimos_meses(date(2026, 10, 1), 0)


class CalcularEdadTests(SimpleTestCase):
    def test_anios_cumplidos(self):
        self.assertEqual(calcular_edad(date(2024, 10, 15), date(2026, 10, 15)), (2, 0))

    def test_meses_cumplidos(self):
        self.assertEqual(calcular_edad(date(2026, 3, 20), date(2026, 10, 15)), (0, 6))

    def test_aun_no_cumple_el_mes(self):
        self.assertEqual(calcular_edad(date(2025, 10, 20), date(2026, 10, 15)), (0, 11))

    def test_fecha_futura_es_invalida(self):
        with self.assertRaises(ValueError):
            calcular_edad(date(2026, 10, 16), date(2026, 10, 15))
