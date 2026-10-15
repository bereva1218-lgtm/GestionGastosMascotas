"""Crea usuarios y datos de demostración para probar la aplicación localmente.

Uso: python manage.py datos_demo
Usuarios: `demo` (con mascotas, gastos y medicamentos) y `otro` (para comprobar
que cada usuario ve solo lo suyo). Contraseña de ambos: CLAVE_DEMO.
Solo para desarrollo; no usar en producción.
"""
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from mascotas.models import CategoriaGasto, Gasto, Mascota, Medicamento

CLAVE_DEMO = 'Demo-Mascotas-2026'


class Command(BaseCommand):
    help = 'Crea usuarios y datos de demostración (solo desarrollo).'

    @transaction.atomic
    def handle(self, *args, **options):
        if User.objects.filter(username='demo').exists():
            self.stdout.write(self.style.WARNING('Los datos de demostración ya existen.'))
            return

        demo = User.objects.create_user('demo', password=CLAVE_DEMO)
        otro = User.objects.create_user('otro', password=CLAVE_DEMO)
        cat = {c.nombre: c for c in CategoriaGasto.objects.all()}
        hoy = timezone.localdate()
        mes_pasado = hoy.replace(day=1) - timedelta(days=1)

        michi = Mascota.objects.create(
            usuario=demo, nombre='Michi', raza='Criollo', sexo='H', color='Atigrado',
            peso=Decimal('4.2'), estado_salud='Sana',
        )
        tom = Mascota.objects.create(usuario=demo, nombre='Tom', raza='Siamés', sexo='M', peso=Decimal('5.1'))
        Mascota.objects.create(usuario=otro, nombre='Luna', sexo='H')

        for mascota, categoria, fecha, producto, cantidad, valor in [
            (michi, 'Comida', hoy, 'Concentrado 3 kg', '1', '68000'),
            (michi, 'Juguetes', hoy, 'Ratón de tela', '2', '9500'),
            (michi, 'Medicamentos', mes_pasado, 'Antipulgas', '1', '42000'),
            (tom, 'Comida', mes_pasado, 'Concentrado 3 kg', '1.5', '68000'),
            (tom, 'Comida', hoy, 'Arena sanitaria', '2', '23000'),
        ]:
            Gasto.objects.create(
                mascota=mascota, categoria=cat[categoria], producto=producto, fecha=fecha,
                cantidad=Decimal(cantidad), valor_unitario=Decimal(valor), proveedor='Tienda Mascotas',
            )

        Medicamento.objects.create(
            mascota=michi, nombre='Antipulgas', dosis='1 pipeta', frecuencia='Mensual', fecha_inicio=hoy,
        )
        Medicamento.objects.create(
            mascota=tom, nombre='Antibiótico', dosis='5 ml', frecuencia='Cada 12 horas',
            fecha_inicio=hoy - timedelta(days=20), fecha_fin=hoy - timedelta(days=10),
        )
        self.stdout.write(self.style.SUCCESS('Datos creados: usuarios "demo" y "otro".'))
