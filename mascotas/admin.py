from django.contrib import admin

from .models import CategoriaGasto, Gasto, Mascota, Medicamento


@admin.register(Mascota)
class MascotaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'especie', 'raza', 'usuario', 'activa']
    list_filter = ['especie', 'activa']


@admin.register(Gasto)
class GastoAdmin(admin.ModelAdmin):
    list_display = ['producto', 'mascota', 'categoria', 'fecha', 'valor_total']
    list_filter = ['categoria', 'fecha']


@admin.register(Medicamento)
class MedicamentoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'mascota', 'dosis', 'frecuencia', 'fecha_inicio', 'fecha_fin']


admin.site.register(CategoriaGasto)
