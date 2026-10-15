from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q
from django.urls import reverse

from .reglas import calcular_valor_total

POSITIVO = [MinValueValidator(Decimal('0.01'))]


class Mascota(models.Model):
    class Sexo(models.TextChoices):
        MACHO = 'M', 'Macho'
        HEMBRA = 'H', 'Hembra'

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='mascotas'
    )
    nombre = models.CharField(max_length=100)
    especie = models.CharField(max_length=50, default='Gato')
    raza = models.CharField(max_length=100, blank=True)
    sexo = models.CharField(max_length=1, choices=Sexo.choices)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    peso = models.DecimalField(
        'peso (kg)', max_digits=5, decimal_places=2, null=True, blank=True, validators=POSITIVO
    )
    color = models.CharField(max_length=50, blank=True)
    estado_salud = models.CharField('estado de salud', max_length=200, blank=True)
    observaciones = models.TextField(blank=True)
    # Retirar = activa=False; nunca se borra para conservar el historial financiero.
    activa = models.BooleanField(default=True)

    class Meta:
        ordering = ['nombre']
        constraints = [
            models.CheckConstraint(condition=Q(peso__gt=0) | Q(peso__isnull=True), name='peso_positivo'),
        ]

    def __str__(self):
        return self.nombre

    def get_absolute_url(self):
        return reverse('mascotas:mascota_detalle', args=[self.pk])


class CategoriaGasto(models.Model):
    nombre = models.CharField(max_length=50, unique=True)

    class Meta:
        ordering = ['nombre']
        verbose_name = 'categoría de gasto'
        verbose_name_plural = 'categorías de gasto'

    def __str__(self):
        return self.nombre


class Gasto(models.Model):
    mascota = models.ForeignKey(Mascota, on_delete=models.PROTECT, related_name='gastos')
    categoria = models.ForeignKey(CategoriaGasto, on_delete=models.PROTECT, related_name='gastos')
    producto = models.CharField(max_length=150)
    fecha = models.DateField()
    cantidad = models.DecimalField(max_digits=10, decimal_places=2, validators=POSITIVO)
    valor_unitario = models.DecimalField(max_digits=12, decimal_places=2, validators=POSITIVO)
    valor_total = models.DecimalField(max_digits=14, decimal_places=2, editable=False)
    proveedor = models.CharField(max_length=150, blank=True)
    notas = models.TextField(blank=True)

    class Meta:
        ordering = ['-fecha']
        constraints = [
            models.CheckConstraint(condition=Q(cantidad__gt=0), name='cantidad_positiva'),
            models.CheckConstraint(condition=Q(valor_unitario__gt=0), name='valor_unitario_positivo'),
        ]

    def save(self, *args, **kwargs):
        self.valor_total = calcular_valor_total(self.cantidad, self.valor_unitario)
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.producto} ({self.fecha})'


class Medicamento(models.Model):
    mascota = models.ForeignKey(Mascota, on_delete=models.PROTECT, related_name='medicamentos')
    nombre = models.CharField(max_length=150)
    dosis = models.CharField(max_length=100)
    frecuencia = models.CharField(max_length=100)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField(null=True, blank=True)
    observaciones = models.TextField('observaciones veterinarias', blank=True)

    class Meta:
        ordering = ['-fecha_inicio']
        constraints = [
            models.CheckConstraint(
                condition=Q(fecha_fin__isnull=True) | Q(fecha_fin__gte=models.F('fecha_inicio')),
                name='fecha_fin_posterior_inicio',
            ),
        ]

    def __str__(self):
        return f'{self.nombre} - {self.mascota}'
