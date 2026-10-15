from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import ProtectedError, Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, ListView, TemplateView, UpdateView

from . import reportes
from .forms import GastoFiltroForm, GastoForm, MascotaForm, MedicamentoForm, RangoFechasForm
from .models import Gasto, Mascota, Medicamento
from .reglas import total_mensual


class DelUsuarioMixin(LoginRequiredMixin):
    """Exige sesión y limita las consultas a los registros del usuario actual."""

    campo_usuario = 'usuario'

    def get_queryset(self):
        return super().get_queryset().filter(**{self.campo_usuario: self.request.user})


class FormConUsuarioMixin:
    """Pasa el usuario al formulario para limitar las mascotas que puede elegir."""

    def get_form_kwargs(self):
        return {**super().get_form_kwargs(), 'usuario': self.request.user}


class EliminarConMensajeMixin:
    mensaje_eliminado = 'Registro eliminado.'

    def form_valid(self, form):
        respuesta = super().form_valid(form)
        messages.success(self.request, self.mensaje_eliminado)
        return respuesta


def gastos_del(usuario):
    return Gasto.objects.filter(mascota__usuario=usuario)


class Registro(CreateView):
    form_class = UserCreationForm
    template_name = 'registration/registro.html'
    success_url = reverse_lazy('mascotas:inicio')

    def form_valid(self, form):
        respuesta = super().form_valid(form)
        login(self.request, self.object)
        messages.success(self.request, f'Cuenta creada. ¡Bienvenido, {self.object.username}!')
        return respuesta


class Inicio(LoginRequiredMixin, TemplateView):
    template_name = 'mascotas/inicio.html'

    def get_context_data(self, **kwargs):
        hoy = timezone.localdate()
        del_mes = gastos_del(self.request.user).filter(fecha__year=hoy.year, fecha__month=hoy.month)
        return super().get_context_data(
            hoy=hoy,
            total_mes=total_mensual(del_mes, hoy.year, hoy.month),
            mascotas=self.request.user.mascotas.filter(activa=True),
            ultimos_gastos=gastos_del(self.request.user).select_related('mascota', 'categoria')[:5],
            **kwargs,
        )


# --- Mascotas ---

class MascotaLista(DelUsuarioMixin, ListView):
    model = Mascota
    context_object_name = 'mascotas'


class MascotaDetalle(DelUsuarioMixin, DetailView):
    model = Mascota

    def get_context_data(self, **kwargs):
        gastos = self.object.gastos.select_related('categoria')
        return super().get_context_data(
            gastos=gastos,
            total_gastos=reportes.total(gastos),
            por_categoria=reportes.totales_por_categoria(gastos),
            medicamentos=self.object.medicamentos.all(),
            **kwargs,
        )


class MascotaCrear(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = Mascota
    form_class = MascotaForm
    template_name = 'mascotas/form.html'
    success_message = 'Mascota «%(nombre)s» registrada.'
    extra_context = {'titulo': 'Nueva mascota'}

    def form_valid(self, form):
        form.instance.usuario = self.request.user
        return super().form_valid(form)


class MascotaEditar(DelUsuarioMixin, SuccessMessageMixin, UpdateView):
    model = Mascota
    form_class = MascotaForm
    template_name = 'mascotas/form.html'
    success_message = 'Mascota «%(nombre)s» actualizada.'
    extra_context = {'titulo': 'Editar mascota'}


class MascotaCambiarEstado(LoginRequiredMixin, View):
    """Retira o reactiva una mascota sin tocar su historial."""

    http_method_names = ['post']
    activa = False

    def post(self, request, pk):
        mascota = get_object_or_404(Mascota, pk=pk, usuario=request.user)
        mascota.activa = self.activa
        mascota.save(update_fields=['activa'])
        estado = 'reactivada' if self.activa else 'retirada; su historial se conserva'
        messages.success(request, f'Mascota «{mascota}» {estado}.')
        return redirect('mascotas:mascota_detalle', pk=mascota.pk)


class MascotaEliminar(DelUsuarioMixin, DeleteView):
    model = Mascota
    template_name = 'mascotas/confirmar_eliminar.html'
    success_url = reverse_lazy('mascotas:mascota_lista')

    def form_valid(self, form):
        nombre = str(self.object)
        try:
            self.object.delete()
        except ProtectedError:
            messages.error(
                self.request,
                f'No se puede eliminar «{nombre}» porque tiene gastos o medicamentos. Retírela en su lugar.',
            )
            return redirect('mascotas:mascota_detalle', pk=self.object.pk)
        messages.success(self.request, f'Mascota «{nombre}» eliminada.')
        return redirect(self.success_url)


# --- Gastos ---

class GastoLista(LoginRequiredMixin, ListView):
    context_object_name = 'gastos'
    template_name = 'mascotas/gasto_list.html'

    def get_queryset(self):
        self.filtro = GastoFiltroForm(self.request.GET or None, usuario=self.request.user)
        gastos = gastos_del(self.request.user).select_related('mascota', 'categoria')
        if self.filtro.is_valid():
            gastos = self.filtro.filtrar(gastos)
        return gastos

    def get_context_data(self, **kwargs):
        return super().get_context_data(
            filtro=self.filtro, total=reportes.total(self.object_list), **kwargs
        )


class GastoCrear(LoginRequiredMixin, FormConUsuarioMixin, SuccessMessageMixin, CreateView):
    model = Gasto
    form_class = GastoForm
    template_name = 'mascotas/form.html'
    success_url = reverse_lazy('mascotas:gasto_lista')
    success_message = 'Gasto «%(producto)s» registrado.'
    extra_context = {'titulo': 'Nuevo gasto'}

    def get_initial(self):
        return {'fecha': timezone.localdate(), 'mascota': self.request.GET.get('mascota')}


class GastoEditar(DelUsuarioMixin, FormConUsuarioMixin, SuccessMessageMixin, UpdateView):
    model = Gasto
    campo_usuario = 'mascota__usuario'
    form_class = GastoForm
    template_name = 'mascotas/form.html'
    success_url = reverse_lazy('mascotas:gasto_lista')
    success_message = 'Gasto «%(producto)s» actualizado.'
    extra_context = {'titulo': 'Editar gasto'}


class GastoEliminar(DelUsuarioMixin, EliminarConMensajeMixin, DeleteView):
    model = Gasto
    campo_usuario = 'mascota__usuario'
    template_name = 'mascotas/confirmar_eliminar.html'
    success_url = reverse_lazy('mascotas:gasto_lista')
    mensaje_eliminado = 'Gasto eliminado.'


# --- Medicamentos ---

class MedicamentoLista(LoginRequiredMixin, ListView):
    context_object_name = 'medicamentos'
    template_name = 'mascotas/medicamento_list.html'

    def get_queryset(self):
        medicamentos = Medicamento.objects.filter(mascota__usuario=self.request.user).select_related('mascota')
        self.historial = self.request.GET.get('ver') == 'historial'
        if not self.historial:
            medicamentos = medicamentos.filter(
                Q(fecha_fin__isnull=True) | Q(fecha_fin__gte=timezone.localdate())
            )
        return medicamentos

    def get_context_data(self, **kwargs):
        return super().get_context_data(historial=self.historial, **kwargs)


class MedicamentoCrear(LoginRequiredMixin, FormConUsuarioMixin, SuccessMessageMixin, CreateView):
    model = Medicamento
    form_class = MedicamentoForm
    template_name = 'mascotas/form.html'
    success_url = reverse_lazy('mascotas:medicamento_lista')
    success_message = 'Medicamento «%(nombre)s» registrado.'
    extra_context = {'titulo': 'Nuevo medicamento'}

    def get_initial(self):
        return {'fecha_inicio': timezone.localdate(), 'mascota': self.request.GET.get('mascota')}


class MedicamentoEditar(DelUsuarioMixin, FormConUsuarioMixin, SuccessMessageMixin, UpdateView):
    model = Medicamento
    campo_usuario = 'mascota__usuario'
    form_class = MedicamentoForm
    template_name = 'mascotas/form.html'
    success_url = reverse_lazy('mascotas:medicamento_lista')
    success_message = 'Medicamento «%(nombre)s» actualizado.'
    extra_context = {'titulo': 'Editar medicamento'}


class MedicamentoEliminar(DelUsuarioMixin, EliminarConMensajeMixin, DeleteView):
    model = Medicamento
    campo_usuario = 'mascota__usuario'
    template_name = 'mascotas/confirmar_eliminar.html'
    success_url = reverse_lazy('mascotas:medicamento_lista')
    mensaje_eliminado = 'Medicamento eliminado.'


# --- Reportes ---

class Reportes(LoginRequiredMixin, TemplateView):
    template_name = 'mascotas/reportes.html'

    def get_context_data(self, **kwargs):
        rango = RangoFechasForm(self.request.GET or None)
        gastos = gastos_del(self.request.user)
        if rango.is_valid():
            gastos = rango.filtrar(gastos)
        return super().get_context_data(
            rango=rango,
            total=reportes.total(gastos),
            por_mascota=reportes.totales_por_mascota(gastos),
            por_categoria=reportes.totales_por_categoria(gastos),
            mensual=reportes.resumen_mensual(gastos),
            productos=reportes.productos(gastos),
            **kwargs,
        )
