"""Consultas de resumen sobre un queryset de gastos ya filtrado por usuario."""
from decimal import Decimal

from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth


def total(gastos):
    return gastos.aggregate(total=Sum('valor_total'))['total'] or Decimal('0')


def totales_por_mascota(gastos):
    return gastos.values('mascota__id', 'mascota__nombre').annotate(total=Sum('valor_total')).order_by('-total')


def totales_por_categoria(gastos):
    return gastos.values('categoria__nombre').annotate(total=Sum('valor_total')).order_by('-total')


def resumen_mensual(gastos):
    return (
        gastos.annotate(mes=TruncMonth('fecha'))
        .values('mes')
        .annotate(total=Sum('valor_total'), cantidad=Count('id'))
        .order_by('-mes')
    )


def productos(gastos):
    return (
        gastos.values('producto', 'categoria__nombre')
        .annotate(veces=Count('id'), total=Sum('valor_total'))
        .order_by('producto')
    )
