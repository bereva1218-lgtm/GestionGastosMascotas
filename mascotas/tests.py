from datetime import date
from decimal import Decimal

from django.contrib.auth.models import User
from django.db import IntegrityError
from django.db.models import ProtectedError
from django.test import TestCase

from .models import CategoriaGasto, Gasto, Mascota


class ReglasDeNegocioTests(TestCase):
    def setUp(self):
        usuario = User.objects.create_user('ana', password='x')
        self.mascota = Mascota.objects.create(usuario=usuario, nombre='Michi', sexo='H')
        self.comida = CategoriaGasto.objects.get(nombre='Comida')

    def crear_gasto(self, cantidad, valor_unitario):
        return Gasto.objects.create(
            mascota=self.mascota, categoria=self.comida, producto='Concentrado',
            fecha=date(2026, 10, 8), cantidad=cantidad, valor_unitario=valor_unitario,
        )

    def test_categorias_iniciales(self):
        self.assertEqual(
            set(CategoriaGasto.objects.values_list('nombre', flat=True)),
            {'Medicamentos', 'Comida', 'Juguetes'},
        )

    def test_total_es_cantidad_por_valor_unitario(self):
        gasto = self.crear_gasto(Decimal('3'), Decimal('12500.50'))
        self.assertEqual(gasto.valor_total, Decimal('37501.50'))

    def test_cantidad_debe_ser_positiva(self):
        with self.assertRaises(IntegrityError):
            self.crear_gasto(Decimal('0'), Decimal('100'))

    def test_borrar_mascota_con_gastos_esta_protegido(self):
        self.crear_gasto(Decimal('1'), Decimal('100'))
        with self.assertRaises(ProtectedError):
            self.mascota.delete()
