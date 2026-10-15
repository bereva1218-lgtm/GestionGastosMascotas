from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import CategoriaGasto, Gasto, Mascota, Medicamento


class VistasBase(TestCase):
    def setUp(self):
        self.ana = User.objects.create_user('ana')
        self.beto = User.objects.create_user('beto')
        self.michi = Mascota.objects.create(usuario=self.ana, nombre='Michi', sexo='H')
        self.luna = Mascota.objects.create(usuario=self.beto, nombre='Luna', sexo='H')
        self.comida = CategoriaGasto.objects.get(nombre='Comida')
        self.juguetes = CategoriaGasto.objects.get(nombre='Juguetes')
        self.client.force_login(self.ana)

    def crear_gasto(self, mascota, categoria, fecha, cantidad='1', valor='1000', producto='Producto'):
        return Gasto.objects.create(
            mascota=mascota, categoria=categoria, producto=producto, fecha=fecha,
            cantidad=Decimal(cantidad), valor_unitario=Decimal(valor),
        )


class AutenticacionTests(VistasBase):
    def test_anonimo_es_redirigido_al_login(self):
        self.client.logout()
        respuesta = self.client.get(reverse('mascotas:mascota_lista'))
        self.assertRedirects(respuesta, f"{reverse('login')}?next={reverse('mascotas:mascota_lista')}")

    def test_registro_crea_usuario_e_inicia_sesion(self):
        self.client.logout()
        respuesta = self.client.post(reverse('mascotas:registro'), {
            'username': 'carla', 'password1': 'ClaveSegura-2026', 'password2': 'ClaveSegura-2026',
        }, follow=True)
        self.assertTrue(User.objects.filter(username='carla').exists())
        self.assertEqual(respuesta.context['user'].username, 'carla')
        self.assertContains(respuesta, 'Cuenta creada')


class MascotaVistasTests(VistasBase):
    def test_crear_asigna_usuario_y_muestra_mensaje(self):
        respuesta = self.client.post(reverse('mascotas:mascota_crear'), {
            'nombre': 'Garfield', 'especie': 'Gato', 'sexo': 'M',
        }, follow=True)
        self.assertEqual(Mascota.objects.get(nombre='Garfield').usuario, self.ana)
        self.assertContains(respuesta, 'Garfield')
        self.assertContains(respuesta, 'registrada')

    def test_lista_solo_muestra_mascotas_propias(self):
        respuesta = self.client.get(reverse('mascotas:mascota_lista'))
        self.assertContains(respuesta, 'Michi')
        self.assertNotContains(respuesta, 'Luna')

    def test_mascota_ajena_responde_404(self):
        for nombre in ('mascota_detalle', 'mascota_editar', 'mascota_eliminar'):
            with self.subTest(vista=nombre):
                respuesta = self.client.get(reverse(f'mascotas:{nombre}', args=[self.luna.pk]))
                self.assertEqual(respuesta.status_code, 404)
        respuesta = self.client.post(reverse('mascotas:mascota_retirar', args=[self.luna.pk]))
        self.assertEqual(respuesta.status_code, 404)

    def test_detalle_muestra_total_de_gastos(self):
        self.crear_gasto(self.michi, self.comida, date(2026, 10, 1), '2', '10000')
        self.crear_gasto(self.michi, self.juguetes, date(2026, 10, 2), '1', '5000')
        respuesta = self.client.get(reverse('mascotas:mascota_detalle', args=[self.michi.pk]))
        self.assertEqual(respuesta.context['total_gastos'], Decimal('25000'))

    def test_retirar_conserva_historial(self):
        self.crear_gasto(self.michi, self.comida, date(2026, 10, 1))
        respuesta = self.client.post(reverse('mascotas:mascota_retirar', args=[self.michi.pk]), follow=True)
        self.michi.refresh_from_db()
        self.assertFalse(self.michi.activa)
        self.assertEqual(self.michi.gastos.count(), 1)
        self.assertContains(respuesta, 'retirada')

    def test_retirar_exige_post(self):
        respuesta = self.client.get(reverse('mascotas:mascota_retirar', args=[self.michi.pk]))
        self.assertEqual(respuesta.status_code, 405)

    def test_eliminar_con_historial_no_borra_y_muestra_error(self):
        self.crear_gasto(self.michi, self.comida, date(2026, 10, 1))
        respuesta = self.client.post(reverse('mascotas:mascota_eliminar', args=[self.michi.pk]), follow=True)
        self.assertTrue(Mascota.objects.filter(pk=self.michi.pk).exists())
        self.assertContains(respuesta, 'No se puede eliminar')

    def test_eliminar_sin_historial_borra(self):
        respuesta = self.client.post(reverse('mascotas:mascota_eliminar', args=[self.michi.pk]), follow=True)
        self.assertFalse(Mascota.objects.filter(pk=self.michi.pk).exists())
        self.assertContains(respuesta, 'eliminada')


class GastoVistasTests(VistasBase):
    def test_crear_calcula_total(self):
        respuesta = self.client.post(reverse('mascotas:gasto_crear'), {
            'mascota': self.michi.pk, 'categoria': self.comida.pk, 'producto': 'Arena',
            'fecha': '2026-10-08', 'cantidad': '3', 'valor_unitario': '12000',
        }, follow=True)
        self.assertEqual(Gasto.objects.get(producto='Arena').valor_total, Decimal('36000'))
        self.assertContains(respuesta, 'registrado')

    def test_crear_con_mascota_ajena_no_guarda(self):
        respuesta = self.client.post(reverse('mascotas:gasto_crear'), {
            'mascota': self.luna.pk, 'categoria': self.comida.pk, 'producto': 'Arena',
            'fecha': '2026-10-08', 'cantidad': '1', 'valor_unitario': '1000',
        })
        self.assertEqual(respuesta.status_code, 200)
        self.assertFalse(Gasto.objects.exists())

    def test_gasto_ajeno_responde_404(self):
        ajeno = self.crear_gasto(self.luna, self.comida, date(2026, 10, 1))
        for nombre in ('gasto_editar', 'gasto_eliminar'):
            with self.subTest(vista=nombre):
                respuesta = self.client.get(reverse(f'mascotas:{nombre}', args=[ajeno.pk]))
                self.assertEqual(respuesta.status_code, 404)

    def test_lista_filtra_y_calcula_total_filtrado(self):
        self.crear_gasto(self.michi, self.comida, date(2026, 10, 5), '1', '1000')
        self.crear_gasto(self.michi, self.comida, date(2026, 9, 5), '1', '2000')
        self.crear_gasto(self.michi, self.juguetes, date(2026, 10, 6), '1', '4000')
        self.crear_gasto(self.luna, self.comida, date(2026, 10, 5), '1', '8000')
        respuesta = self.client.get(reverse('mascotas:gasto_lista'), {
            'categoria': self.comida.pk, 'desde': '2026-10-01', 'hasta': '2026-10-31',
        })
        self.assertEqual(len(respuesta.context['gastos']), 1)
        self.assertEqual(respuesta.context['total'], Decimal('1000'))

    def test_lista_sin_filtros_suma_solo_lo_propio(self):
        self.crear_gasto(self.michi, self.comida, date(2026, 10, 5), '1', '1000')
        self.crear_gasto(self.luna, self.comida, date(2026, 10, 5), '1', '8000')
        respuesta = self.client.get(reverse('mascotas:gasto_lista'))
        self.assertEqual(respuesta.context['total'], Decimal('1000'))

    def test_eliminar_gasto(self):
        gasto = self.crear_gasto(self.michi, self.comida, date(2026, 10, 1))
        respuesta = self.client.post(reverse('mascotas:gasto_eliminar', args=[gasto.pk]), follow=True)
        self.assertFalse(Gasto.objects.exists())
        self.assertContains(respuesta, 'eliminado')


class MedicamentoVistasTests(VistasBase):
    def test_lista_separa_activos_e_historial(self):
        hoy = timezone.localdate()
        Medicamento.objects.create(
            mascota=self.michi, nombre='Activo', dosis='1', frecuencia='Diaria', fecha_inicio=hoy,
        )
        Medicamento.objects.create(
            mascota=self.michi, nombre='Terminado', dosis='1', frecuencia='Diaria',
            fecha_inicio=hoy - timedelta(days=30), fecha_fin=hoy - timedelta(days=1),
        )
        activos = self.client.get(reverse('mascotas:medicamento_lista'))
        self.assertContains(activos, 'Activo')
        self.assertNotContains(activos, 'Terminado')
        historial = self.client.get(reverse('mascotas:medicamento_lista'), {'ver': 'historial'})
        self.assertContains(historial, 'Terminado')

    def test_crear_medicamento(self):
        respuesta = self.client.post(reverse('mascotas:medicamento_crear'), {
            'mascota': self.michi.pk, 'nombre': 'Antipulgas', 'dosis': '1 pipeta',
            'frecuencia': 'Mensual', 'fecha_inicio': '2026-10-01',
        }, follow=True)
        self.assertTrue(Medicamento.objects.filter(nombre='Antipulgas').exists())
        self.assertContains(respuesta, 'registrado')


class InicioTests(VistasBase):
    def test_muestra_total_del_mes_actual(self):
        hoy = timezone.localdate()
        self.crear_gasto(self.michi, self.comida, hoy, '1', '7000')
        self.crear_gasto(self.michi, self.comida, hoy.replace(day=1) - timedelta(days=1), '1', '9000')
        respuesta = self.client.get(reverse('mascotas:inicio'))
        self.assertEqual(respuesta.context['total_mes'], Decimal('7000'))


class PanelTests(VistasBase):
    def test_compara_con_el_mes_anterior(self):
        hoy = timezone.localdate()
        self.crear_gasto(self.michi, self.comida, hoy, '1', '7000')
        self.crear_gasto(self.michi, self.comida, hoy.replace(day=1) - timedelta(days=1), '1', '9000')
        contexto = self.client.get(reverse('mascotas:inicio')).context
        self.assertEqual(contexto['total_mes_anterior'], Decimal('9000'))
        self.assertEqual(contexto['variacion'], Decimal('-22.2'))

    def test_tendencia_de_seis_meses_termina_en_el_mes_actual(self):
        hoy = timezone.localdate()
        self.crear_gasto(self.michi, self.comida, hoy, '1', '7000')
        tendencia = self.client.get(reverse('mascotas:inicio')).context['tendencia']
        self.assertEqual(len(tendencia), 6)
        self.assertEqual(tendencia[-1]['total'], Decimal('7000'))
        self.assertEqual(tendencia[-1]['fecha'], hoy.replace(day=1))

    def test_medicamentos_activos_solo_del_usuario(self):
        hoy = timezone.localdate()
        Medicamento.objects.create(mascota=self.michi, nombre='Propio', dosis='1', frecuencia='D', fecha_inicio=hoy)
        Medicamento.objects.create(mascota=self.luna, nombre='Ajeno', dosis='1', frecuencia='D', fecha_inicio=hoy)
        activos = self.client.get(reverse('mascotas:inicio')).context['medicamentos_activos']
        self.assertEqual([m.nombre for m in activos], ['Propio'])


class MascotaListaTests(VistasBase):
    def setUp(self):
        super().setUp()
        self.tom = Mascota.objects.create(usuario=self.ana, nombre='Tom', sexo='M', activa=False)
        self.crear_gasto(self.michi, self.comida, date(2026, 10, 1), '2', '1500')

    def test_anota_total_gastado(self):
        mascotas = {m.nombre: m for m in self.client.get(reverse('mascotas:mascota_lista')).context['mascotas']}
        self.assertEqual(mascotas['Michi'].total_gastado, Decimal('3000'))
        self.assertEqual(mascotas['Tom'].total_gastado, Decimal('0'))

    def test_busqueda_por_nombre(self):
        respuesta = self.client.get(reverse('mascotas:mascota_lista'), {'q': 'mic'})
        self.assertEqual([m.nombre for m in respuesta.context['mascotas']], ['Michi'])

    def test_filtro_por_estado(self):
        respuesta = self.client.get(reverse('mascotas:mascota_lista'), {'estado': 'retiradas'})
        self.assertEqual([m.nombre for m in respuesta.context['mascotas']], ['Tom'])
        self.assertEqual(respuesta.context['conteos'], {'todas': 2, 'activas': 1, 'retiradas': 1})


class MascotaDetalleExtraTests(VistasBase):
    def test_total_del_mes_de_la_mascota(self):
        hoy = timezone.localdate()
        self.crear_gasto(self.michi, self.comida, hoy, '1', '4000')
        self.crear_gasto(self.michi, self.comida, hoy.replace(day=1) - timedelta(days=1), '1', '9000')
        contexto = self.client.get(reverse('mascotas:mascota_detalle', args=[self.michi.pk])).context
        self.assertEqual(contexto['total_mes'], Decimal('4000'))


class GastoListaExtraTests(VistasBase):
    def test_pagina_de_quince_y_total_de_todo_el_filtro(self):
        for dia in range(1, 21):
            self.crear_gasto(self.michi, self.comida, date(2026, 10, dia), '1', '100')
        primera = self.client.get(reverse('mascotas:gasto_lista'))
        self.assertEqual(len(primera.context['gastos']), 15)
        self.assertEqual(primera.context['total'], Decimal('2000'))
        self.assertEqual(primera.context['cantidad'], 20)
        self.assertEqual(primera.context['promedio'], Decimal('100'))
        segunda = self.client.get(reverse('mascotas:gasto_lista'), {'page': 2})
        self.assertEqual(len(segunda.context['gastos']), 5)

    def test_busqueda_por_producto_o_proveedor(self):
        self.crear_gasto(self.michi, self.comida, date(2026, 10, 1), producto='Arena sanitaria')
        self.crear_gasto(self.michi, self.comida, date(2026, 10, 2), producto='Concentrado')
        respuesta = self.client.get(reverse('mascotas:gasto_lista'), {'q': 'arena'})
        self.assertEqual([g.producto for g in respuesta.context['gastos']], ['Arena sanitaria'])

    def test_sin_gastos_el_promedio_es_cero(self):
        self.assertEqual(self.client.get(reverse('mascotas:gasto_lista')).context['promedio'], Decimal('0'))


class ReportesPresetsTests(VistasBase):
    def test_ofrece_rangos_predefinidos(self):
        hoy = timezone.localdate()
        presets = self.client.get(reverse('mascotas:reportes')).context['presets']
        este_mes = next(p for p in presets if p['etiqueta'] == 'Este mes')
        self.assertEqual(este_mes['desde'], hoy.replace(day=1).isoformat())
        self.assertEqual(este_mes['hasta'], hoy.isoformat())

    def test_marca_el_rango_activo(self):
        hoy = timezone.localdate()
        respuesta = self.client.get(reverse('mascotas:reportes'), {
            'desde': hoy.replace(day=1).isoformat(), 'hasta': hoy.isoformat(),
        })
        activos = [p['etiqueta'] for p in respuesta.context['presets'] if p['activo']]
        self.assertEqual(activos, ['Este mes'])
