"""Pruebas de la integración del rediseño: reglas, modelos, formularios y vistas que
alimentan las plantillas, más los filtros compartidos de `ui`."""
from datetime import date, timedelta
from decimal import Decimal
from types import SimpleNamespace

from django.contrib.auth.models import User
from django.test import SimpleTestCase, TestCase
from django.urls import reverse
from django.utils import timezone

from .forms import AccesoForm, GastoFiltroForm, GastoForm, MascotaForm, RegistroForm
from .models import CategoriaGasto, Gasto, Mascota, Medicamento
from .reglas import meses_entre
from .templatetags.ui import estado_medicamento, fecha_larga, icono_categoria, porcentaje, tono
from .test_vistas import VistasBase


class MesesEntreTests(SimpleTestCase):
    def test_incluye_extremos_y_cruza_anio(self):
        self.assertEqual(
            meses_entre(date(2025, 11, 20), date(2026, 2, 3)),
            [(2025, 11), (2025, 12), (2026, 1), (2026, 2)],
        )

    def test_mismo_mes(self):
        self.assertEqual(meses_entre(date(2026, 10, 1), date(2026, 10, 31)), [(2026, 10)])

    def test_rango_invertido_es_invalido(self):
        with self.assertRaises(ValueError):
            meses_entre(date(2026, 10, 1), date(2026, 9, 1))


class ModelosTests(TestCase):
    def setUp(self):
        self.ana = User.objects.create_user('ana')
        self.mascota = Mascota.objects.create(usuario=self.ana, nombre='Michi', sexo='H')
        self.hoy = timezone.localdate()

    def test_programado_si_empieza_despues_de_hoy(self):
        futuro = Medicamento(mascota=self.mascota, nombre='X', dosis='1', frecuencia='D',
                             fecha_inicio=self.hoy + timedelta(days=2))
        presente = Medicamento(mascota=self.mascota, nombre='X', dosis='1', frecuencia='D', fecha_inicio=self.hoy)
        self.assertTrue(futuro.programado)
        self.assertFalse(presente.programado)

    def test_gastos_del_mismo_dia_ordenan_por_el_mas_reciente(self):
        comida = CategoriaGasto.objects.get(nombre='Comida')
        primero, segundo = (
            Gasto.objects.create(mascota=self.mascota, categoria=comida, producto=p, fecha=date(2026, 10, 1),
                                 cantidad=Decimal('1'), valor_unitario=Decimal('1'))
            for p in ('A', 'B')
        )
        self.assertEqual(list(Gasto.objects.all()), [segundo, primero])


class TextosEnEspanolTests(TestCase):
    def setUp(self):
        self.ana = User.objects.create_user('ana')

    def test_valor_no_positivo_explica_en_tu(self):
        form = GastoForm({'cantidad': '0', 'valor_unitario': '0'}, usuario=self.ana)
        self.assertEqual(form.errors['cantidad'], ['Debe ser mayor que 0.'])
        self.assertEqual(form.errors['valor_unitario'], ['Debe ser mayor que 0.'])

    def test_fecha_invalida_en_tu(self):
        form = GastoFiltroForm({'desde': 'ayer'}, usuario=self.ana)
        self.assertEqual(form.errors['desde'], ['Escribe una fecha válida.'])

    def test_opciones_vacias_en_espanol(self):
        campos = GastoForm(usuario=self.ana).fields
        self.assertEqual(campos['mascota'].empty_label, 'Selecciona una mascota')
        self.assertEqual(campos['categoria'].empty_label, 'Selecciona una categoría')
        self.assertEqual(MascotaForm().fields['sexo'].choices[0], ('', 'Selecciona el sexo'))

    def test_registro_en_tu(self):
        form = RegistroForm()
        self.assertEqual(form.fields['password2'].label, 'Confirma tu contraseña')
        self.assertNotIn('Su contraseña', str(form.fields['password1'].help_text))
        self.assertNotIn('carácteres', str(form.fields['username'].help_text))

    def test_acceso_invalido_en_tu(self):
        form = AccesoForm(data={'username': 'nadie', 'password': 'mal'})
        self.assertFalse(form.is_valid())
        self.assertIn('Usuario o contraseña incorrectos', form.non_field_errors()[0])


class VistasIntegracionTests(VistasBase):
    def test_registro_redirige_si_ya_hay_sesion(self):
        self.assertRedirects(self.client.get(reverse('mascotas:registro')), reverse('mascotas:inicio'))

    def test_login_redirige_si_ya_hay_sesion(self):
        self.assertRedirects(self.client.get(reverse('login')), reverse('mascotas:inicio'))

    def test_login_usa_textos_en_tu(self):
        self.client.logout()
        respuesta = self.client.post(reverse('login'), {'username': 'ana', 'password': 'mal'})
        self.assertContains(respuesta, 'Usuario o contraseña incorrectos')

    def test_eliminar_mascota_con_historial_sugiere_retirarla_en_tu(self):
        self.crear_gasto(self.michi, self.comida, date(2026, 10, 1))
        respuesta = self.client.post(reverse('mascotas:mascota_eliminar', args=[self.michi.pk]), follow=True)
        self.assertContains(respuesta, 'Retírala en su lugar')

    def test_confirmar_eliminar_mascota_informa_historial(self):
        self.crear_gasto(self.michi, self.comida, date(2026, 10, 1))
        contexto = self.client.get(reverse('mascotas:mascota_eliminar', args=[self.michi.pk])).context
        self.assertEqual((contexto['num_gastos'], contexto['num_medicamentos']), (1, 0))

    def test_medicamentos_por_terminar(self):
        hoy = timezone.localdate()
        for dias in (0, 3, 4):
            Medicamento.objects.create(mascota=self.michi, nombre=f'M{dias}', dosis='1', frecuencia='D',
                                       fecha_inicio=hoy - timedelta(days=5), fecha_fin=hoy + timedelta(days=dias))
        self.assertEqual(self.client.get(reverse('mascotas:medicamento_lista')).context['por_terminar'], 2)

    def test_gastos_paginas_y_mascotas(self):
        contexto = self.client.get(reverse('mascotas:gasto_lista')).context
        self.assertTrue(contexto['tiene_mascotas'])
        self.assertFalse(contexto['filtros_aplicados'])
        self.assertEqual(list(contexto['paginas']), [1])

    def test_gastos_filtros_aplicados(self):
        contexto = self.client.get(reverse('mascotas:gasto_lista'), {'q': 'x'}).context
        self.assertTrue(contexto['filtros_aplicados'])

    def test_reportes_grafico_continuo_y_promedios(self):
        self.crear_gasto(self.michi, self.comida, date(2026, 7, 10), '1', '1000')
        self.crear_gasto(self.michi, self.comida, date(2026, 9, 10), '1', '2001')
        contexto = self.client.get(reverse('mascotas:reportes')).context
        grafico = [(g['fecha'], g['total']) for g in contexto['grafico_mensual']]
        self.assertEqual(grafico, [
            (date(2026, 7, 1), Decimal('1000')), (date(2026, 8, 1), Decimal('0')), (date(2026, 9, 1), Decimal('2001')),
        ])
        self.assertEqual(contexto['max_grafico'], Decimal('2001'))
        self.assertEqual(contexto['promedio'], Decimal('1500.50'))
        self.assertEqual(contexto['promedio_mensual'], Decimal('1500.50'))

    def test_reportes_grafico_limita_a_doce_meses(self):
        self.crear_gasto(self.michi, self.comida, date(2025, 1, 10), '1', '9999')
        self.crear_gasto(self.michi, self.comida, date(2026, 9, 10), '1', '100')
        contexto = self.client.get(reverse('mascotas:reportes')).context
        self.assertEqual(len(contexto['grafico_mensual']), 12)
        self.assertEqual(contexto['grafico_mensual'][-1]['fecha'], date(2026, 9, 1))
        self.assertEqual(contexto['max_grafico'], Decimal('100'))

    def test_reportes_sin_datos(self):
        contexto = self.client.get(reverse('mascotas:reportes')).context
        self.assertEqual(contexto['grafico_mensual'], [])
        self.assertEqual(contexto['promedio'], Decimal('0'))

    def test_reportes_por_mascota_incluye_id(self):
        self.crear_gasto(self.michi, self.comida, date(2026, 7, 10))
        fila = self.client.get(reverse('mascotas:reportes')).context['por_mascota'][0]
        self.assertEqual(fila['mascota__id'], self.michi.pk)


class FiltrosCompartidosTests(SimpleTestCase):
    def test_icono_categoria(self):
        self.assertEqual(
            [icono_categoria(c) for c in ('Comida', 'Medicamentos', 'Juguetes', 'Arena')],
            ['comida', 'pastilla', 'regalo', 'paquete'],
        )

    def test_fecha_larga_en_minuscula(self):
        self.assertEqual(fecha_larga(date(2026, 10, 15)), '15 de octubre de 2026')
        self.assertEqual(fecha_larga(None), '')

    def test_porcentaje(self):
        # Espacio duro entre la cifra y el signo para que no se separen.
        self.assertEqual(porcentaje(Decimal('25'), Decimal('100')), '25\xa0%')
        self.assertEqual(porcentaje(Decimal('1'), Decimal('1000')), '<\xa01\xa0%')
        self.assertEqual(porcentaje(Decimal('0'), Decimal('100')), '0\xa0%')
        self.assertEqual(porcentaje(Decimal('5'), Decimal('0')), '0\xa0%')

    def test_tono_acepta_id(self):
        self.assertEqual(tono(7), 'avatar--t1')

    def test_estado_medicamento(self):
        hoy = timezone.localdate()

        def med(inicio=0, dias=None):
            return SimpleNamespace(fecha_inicio=hoy + timedelta(days=inicio), dias_restantes=dias)

        self.assertEqual(estado_medicamento(med(inicio=2))['texto'], 'Programado')
        self.assertEqual(estado_medicamento(med())['texto'], 'Continuo')
        self.assertEqual(estado_medicamento(med(dias=-1))['texto'], 'Finalizado')
        self.assertEqual(estado_medicamento(med(dias=0))['texto'], 'Termina hoy')
        self.assertEqual(estado_medicamento(med(dias=1))['texto'], 'Queda 1 día')
        self.assertEqual(estado_medicamento(med(dias=3))['variante'], 'aviso')
        self.assertEqual(estado_medicamento(med(dias=10)), {'texto': 'Quedan 10 días', 'variante': 'exito'})
