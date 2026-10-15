from django.urls import path

from . import views

app_name = 'mascotas'

urlpatterns = [
    path('', views.Inicio.as_view(), name='inicio'),
    path('registro/', views.Registro.as_view(), name='registro'),

    path('mascotas/', views.MascotaLista.as_view(), name='mascota_lista'),
    path('mascotas/nueva/', views.MascotaCrear.as_view(), name='mascota_crear'),
    path('mascotas/<int:pk>/', views.MascotaDetalle.as_view(), name='mascota_detalle'),
    path('mascotas/<int:pk>/editar/', views.MascotaEditar.as_view(), name='mascota_editar'),
    path('mascotas/<int:pk>/retirar/', views.MascotaCambiarEstado.as_view(activa=False), name='mascota_retirar'),
    path('mascotas/<int:pk>/reactivar/', views.MascotaCambiarEstado.as_view(activa=True), name='mascota_reactivar'),
    path('mascotas/<int:pk>/eliminar/', views.MascotaEliminar.as_view(), name='mascota_eliminar'),

    path('gastos/', views.GastoLista.as_view(), name='gasto_lista'),
    path('gastos/nuevo/', views.GastoCrear.as_view(), name='gasto_crear'),
    path('gastos/<int:pk>/editar/', views.GastoEditar.as_view(), name='gasto_editar'),
    path('gastos/<int:pk>/eliminar/', views.GastoEliminar.as_view(), name='gasto_eliminar'),

    path('medicamentos/', views.MedicamentoLista.as_view(), name='medicamento_lista'),
    path('medicamentos/nuevo/', views.MedicamentoCrear.as_view(), name='medicamento_crear'),
    path('medicamentos/<int:pk>/editar/', views.MedicamentoEditar.as_view(), name='medicamento_editar'),
    path('medicamentos/<int:pk>/eliminar/', views.MedicamentoEliminar.as_view(), name='medicamento_eliminar'),

    path('reportes/', views.Reportes.as_view(), name='reportes'),
]
