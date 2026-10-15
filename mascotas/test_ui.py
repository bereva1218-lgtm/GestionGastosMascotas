"""Pruebas de la capa de presentación: filtros de plantilla y humo de todas las páginas.

Cada método `test_paginas_*` recorre una sección y se puede ejecutar por separado, p. ej.:
    python manage.py test mascotas.test_ui.PaginasTests.test_paginas_gastos
"""
from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.template import Context, Template
from django.test import SimpleTestCase, TestCase
from django.urls import reverse
from django.utils import timezone

from .models import CategoriaGasto, Gasto, Mascota, Medicamento
from .templatetags.ui import edad, moneda


class FiltrosTests(SimpleTestCase):
    def test_moneda_entera_sin_decimales(self):
        self.assertEqual(moneda(Decimal('133000')), '$\xa0133.000')

    def test_moneda_con_decimales(self):
        self.assertEqual(moneda(Decimal('12500.5')), '$\xa012.500,50')

    def test_moneda_vacia(self):
        self.assertEqual(moneda(None), '$\xa00')

    def test_edad(self):
        hoy = timezone.localdate()
        self.assertEqual(edad(hoy.replace(year=hoy.year - 2)), '2 años')
        self.assertEqual(edad(hoy.replace(year=hoy.year - 1)), '1 año')
        self.assertEqual(edad(hoy), 'Menos de 1 mes')
        self.assertEqual(edad(None), '')

    def test_icono_genera_svg_accesible(self):
        html = Template("{% load ui %}{% icono 'plus' %}").render(Context())
        self.assertIn('<svg class="icono"', html)
        self.assertIn('aria-hidden="true"', html)
        self.assertIn('href="#i-plus"', html)


class PaginasTests(TestCase):
    """Cada página responde 200 con datos reales y usa el layout de la aplicación."""

    def setUp(self):
        self.ana = User.objects.create_user('ana')
        hoy = timezone.localdate()
        self.michi = Mascota.objects.create(
            usuario=self.ana, nombre='Michi', sexo='H', raza='Criollo',
            fecha_nacimiento=hoy.replace(year=hoy.year - 3), peso=Decimal('4.2'),
        )
        self.tom = Mascota.objects.create(usuario=self.ana, nombre='Tom', sexo='M', activa=False)
        comida = CategoriaGasto.objects.get(nombre='Comida')
        self.gasto = Gasto.objects.create(
            mascota=self.michi, categoria=comida, producto='Concentrado', fecha=hoy,
            cantidad=Decimal('2'), valor_unitario=Decimal('15000'), proveedor='Tienda',
        )
        Gasto.objects.create(
            mascota=self.tom, categoria=CategoriaGasto.objects.get(nombre='Juguetes'), producto='Ratón',
            fecha=hoy - timedelta(days=40), cantidad=Decimal('1'), valor_unitario=Decimal('9000'),
        )
        self.medicamento = Medicamento.objects.create(
            mascota=self.michi, nombre='Antipulgas', dosis='1 pipeta', frecuencia='Mensual',
            fecha_inicio=hoy, fecha_fin=hoy + timedelta(days=5),
        )
        Medicamento.objects.create(
            mascota=self.michi, nombre='Antibiótico', dosis='5 ml', frecuencia='12 h',
            fecha_inicio=hoy - timedelta(days=20), fecha_fin=hoy - timedelta(days=2),
        )
        self.client.force_login(self.ana)

    def revisar(self, url, *textos, **params):
        respuesta = self.client.get(url, params)
        self.assertEqual(respuesta.status_code, 200, url)
        self.assertContains(respuesta, '<main')
        for texto in textos:
            self.assertContains(respuesta, texto)
        return respuesta

    def test_paginas_inicio(self):
        self.revisar(reverse('mascotas:inicio'), 'Michi', 'Concentrado', 'Antipulgas')

    def test_paginas_mascotas(self):
        self.revisar(reverse('mascotas:mascota_lista'), 'Michi', 'Tom')
        self.revisar(reverse('mascotas:mascota_lista'), 'Michi', q='mic', estado='activas')
        self.revisar(reverse('mascotas:mascota_detalle', args=[self.michi.pk]), 'Michi', 'Concentrado', 'Antipulgas')
        self.revisar(reverse('mascotas:mascota_detalle', args=[self.tom.pk]), 'Tom')
        self.revisar(reverse('mascotas:mascota_crear'), 'name="nombre"')
        self.revisar(reverse('mascotas:mascota_editar', args=[self.michi.pk]), 'value="Michi"')
        self.revisar(reverse('mascotas:mascota_eliminar', args=[self.michi.pk]), 'Michi')

    def test_paginas_gastos(self):
        self.revisar(reverse('mascotas:gasto_lista'), 'Concentrado', 'Ratón')
        self.revisar(reverse('mascotas:gasto_lista'), 'Concentrado', q='conc', desde='2000-01-01', hasta='2100-01-01')
        self.revisar(reverse('mascotas:gasto_lista'), desde='2026-12-31', hasta='2026-01-01')  # rango inválido
        self.revisar(reverse('mascotas:gasto_crear'), 'name="valor_unitario"')
        self.revisar(reverse('mascotas:gasto_editar', args=[self.gasto.pk]), 'value="Concentrado"')
        self.revisar(reverse('mascotas:gasto_eliminar', args=[self.gasto.pk]), 'Concentrado')

    def test_paginas_medicamentos(self):
        self.revisar(reverse('mascotas:medicamento_lista'), 'Antipulgas')
        self.revisar(reverse('mascotas:medicamento_lista'), 'Antibiótico', ver='historial')
        self.revisar(reverse('mascotas:medicamento_crear'), 'name="dosis"')
        self.revisar(reverse('mascotas:medicamento_editar', args=[self.medicamento.pk]), 'value="Antipulgas"')
        self.revisar(reverse('mascotas:medicamento_eliminar', args=[self.medicamento.pk]), 'Antipulgas')

    def test_paginas_reportes(self):
        self.revisar(reverse('mascotas:reportes'), 'Michi', 'Comida', 'Concentrado')
        self.revisar(reverse('mascotas:reportes'), desde='2100-01-01', hasta='2100-12-31')  # sin datos

    def test_paginas_publicas(self):
        self.client.logout()
        for nombre in ('login', 'mascotas:registro'):
            respuesta = self.client.get(reverse(nombre))
            self.assertEqual(respuesta.status_code, 200)
            self.assertContains(respuesta, '<main')

    def test_formulario_con_errores_se_renderiza(self):
        respuesta = self.client.post(reverse('mascotas:gasto_crear'), {'cantidad': '0'})
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'campo--error')

    def test_pagina_404_personalizada(self):
        with self.settings(DEBUG=False):
            respuesta = self.client.get('/no-existe/')
        self.assertEqual(respuesta.status_code, 404)
        self.assertContains(respuesta, 'Página no encontrada', status_code=404)
