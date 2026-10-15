from datetime import date

from django.contrib.auth.models import User
from django.test import TestCase

from .forms import GastoFiltroForm, GastoForm, MedicamentoForm
from .models import CategoriaGasto, Mascota


class FormulariosTests(TestCase):
    def setUp(self):
        self.ana = User.objects.create_user('ana', password='x')
        self.beto = User.objects.create_user('beto', password='x')
        self.michi = Mascota.objects.create(usuario=self.ana, nombre='Michi', sexo='H')
        self.retirada = Mascota.objects.create(usuario=self.ana, nombre='Tom', sexo='M', activa=False)
        self.ajena = Mascota.objects.create(usuario=self.beto, nombre='Luna', sexo='H')
        self.comida = CategoriaGasto.objects.get(nombre='Comida')

    def datos_gasto(self, **cambios):
        datos = {
            'mascota': self.michi.pk, 'categoria': self.comida.pk, 'producto': 'Concentrado',
            'fecha': '2026-10-08', 'cantidad': '2', 'valor_unitario': '15000',
        }
        datos.update(cambios)
        return datos

    def test_gasto_valido(self):
        self.assertTrue(GastoForm(self.datos_gasto(), usuario=self.ana).is_valid())

    def test_gasto_rechaza_cantidad_cero(self):
        form = GastoForm(self.datos_gasto(cantidad='0'), usuario=self.ana)
        self.assertFalse(form.is_valid())
        self.assertIn('cantidad', form.errors)

    def test_gasto_rechaza_valor_unitario_negativo(self):
        form = GastoForm(self.datos_gasto(valor_unitario='-1'), usuario=self.ana)
        self.assertIn('valor_unitario', form.errors)

    def test_gasto_solo_ofrece_mascotas_activas_del_usuario(self):
        opciones = GastoForm(usuario=self.ana).fields['mascota'].queryset
        self.assertQuerySetEqual(opciones, [self.michi])

    def test_gasto_rechaza_mascota_ajena(self):
        form = GastoForm(self.datos_gasto(mascota=self.ajena.pk), usuario=self.ana)
        self.assertIn('mascota', form.errors)

    def test_medicamento_fecha_fin_anterior_al_inicio_es_invalida(self):
        form = MedicamentoForm({
            'mascota': self.michi.pk, 'nombre': 'Antipulgas', 'dosis': '1 pipeta',
            'frecuencia': 'Mensual', 'fecha_inicio': '2026-10-10', 'fecha_fin': '2026-10-01',
        }, usuario=self.ana)
        self.assertIn('fecha_fin', form.errors)

    def test_filtro_rango_de_fechas_invertido_es_invalido(self):
        form = GastoFiltroForm({'desde': date(2026, 10, 31), 'hasta': date(2026, 10, 1)}, usuario=self.ana)
        self.assertFalse(form.is_valid())

    def test_filtro_incluye_mascotas_retiradas_pero_no_ajenas(self):
        opciones = GastoFiltroForm(usuario=self.ana).fields['mascota'].queryset
        self.assertQuerySetEqual(opciones, [self.michi, self.retirada], ordered=False)
