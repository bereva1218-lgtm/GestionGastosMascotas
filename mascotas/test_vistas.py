from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import CategoriaGasto, Gasto, Mascota, Medicamento


class VistasBase(TestCase):
    def setUp(self):
        self.ana = User.objects.create_user('ana', password='x')
        self.beto = User.objects.create_user('beto', password='x')
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
