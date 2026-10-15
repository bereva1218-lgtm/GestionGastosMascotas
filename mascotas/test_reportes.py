from datetime import date
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from . import reportes
from .models import CategoriaGasto, Gasto, Mascota


class ReportesTests(TestCase):
    def setUp(self):
        self.ana = User.objects.create_user('ana')
        beto = User.objects.create_user('beto')
        self.michi = Mascota.objects.create(usuario=self.ana, nombre='Michi', sexo='H')
        self.tom = Mascota.objects.create(usuario=self.ana, nombre='Tom', sexo='M')
        luna = Mascota.objects.create(usuario=beto, nombre='Luna', sexo='H')
        comida = CategoriaGasto.objects.get(nombre='Comida')
        juguetes = CategoriaGasto.objects.get(nombre='Juguetes')
        for mascota, categoria, fecha, valor, producto in [
            (self.michi, comida, date(2026, 9, 10), '1000', 'Concentrado'),
            (self.michi, comida, date(2026, 10, 10), '2000', 'Concentrado'),
            (self.tom, juguetes, date(2026, 10, 12), '500', 'Ratón'),
            (luna, comida, date(2026, 10, 10), '9999', 'Atún'),
        ]:
            Gasto.objects.create(
                mascota=mascota, categoria=categoria, producto=producto, fecha=fecha,
                cantidad=Decimal('1'), valor_unitario=Decimal(valor),
            )
        self.gastos_ana = Gasto.objects.filter(mascota__usuario=self.ana)

    def test_total(self):
        self.assertEqual(reportes.total(self.gastos_ana), Decimal('3500'))
        self.assertEqual(reportes.total(Gasto.objects.none()), Decimal('0'))

    def test_totales_por_mascota(self):
        filas = {f['mascota__nombre']: f['total'] for f in reportes.totales_por_mascota(self.gastos_ana)}
        self.assertEqual(filas, {'Michi': Decimal('3000'), 'Tom': Decimal('500')})

    def test_totales_por_categoria(self):
        filas = {f['categoria__nombre']: f['total'] for f in reportes.totales_por_categoria(self.gastos_ana)}
        self.assertEqual(filas, {'Comida': Decimal('3000'), 'Juguetes': Decimal('500')})

    def test_resumen_mensual(self):
        filas = [(f['mes'], f['total']) for f in reportes.resumen_mensual(self.gastos_ana)]
        self.assertEqual(filas, [(date(2026, 10, 1), Decimal('2500')), (date(2026, 9, 1), Decimal('1000'))])

    def test_productos_registrados(self):
        filas = {f['producto']: f['veces'] for f in reportes.productos(self.gastos_ana)}
        self.assertEqual(filas, {'Concentrado': 2, 'Ratón': 1})

    def test_vista_usa_solo_datos_propios_y_respeta_rango(self):
        self.client.force_login(self.ana)
        respuesta = self.client.get(reverse('mascotas:reportes'), {'desde': '2026-10-01', 'hasta': '2026-10-31'})
        self.assertEqual(respuesta.context['total'], Decimal('2500'))
        self.assertNotContains(respuesta, 'Luna')
