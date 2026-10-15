from datetime import date, timedelta
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Count, DecimalField, F, ProtectedError, Q, Sum, Value
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, ListView, TemplateView, UpdateView

from . import reportes
from .forms import GastoFiltroForm, GastoForm, MascotaForm, MedicamentoForm, RangoFechasForm, RegistroForm
from .models import Gasto, Mascota, Medicamento
from .reglas import meses_entre, total_mensual, ultimos_meses, variacion_porcentual

MESES_TENDENCIA = 6
MESES_GRAFICO_REPORTE = 12
DIAS_POR_TERMINAR = 3


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


def medicamentos_activos_del(usuario):
    hoy = timezone.localdate()
    return (
        Medicamento.objects.filter(mascota__usuario=usuario)
        .filter(Q(fecha_fin__isnull=True) | Q(fecha_fin__gte=hoy))
        .select_related('mascota')
    )


def promedio(total, cantidad):
    return (total / cantidad).quantize(Decimal('0.01')) if cantidad else Decimal('0')


def con_total_gastado(mascotas):
    return mascotas.annotate(
        total_gastado=Coalesce(Sum('gastos__valor_total'), Value(Decimal('0')), output_field=DecimalField()),
        num_gastos=Count('gastos'),
    )


class Registro(CreateView):
    form_class = RegistroForm
    template_name = 'registration/registro.html'
    success_url = reverse_lazy('mascotas:inicio')

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(self.success_url)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        respuesta = super().form_valid(form)
        login(self.request, self.object)
        messages.success(self.request, f'Cuenta creada. ¡Bienvenido, {self.object.username}!')
        return respuesta


class Inicio(LoginRequiredMixin, TemplateView):
    template_name = 'mascotas/inicio.html'

    def get_context_data(self, **kwargs):
        usuario = self.request.user
        hoy = timezone.localdate()
        gastos = gastos_del(usuario)

        meses = ultimos_meses(hoy, MESES_TENDENCIA)
        primer_mes = date(meses[0][0], meses[0][1], 1)
        recientes = list(gastos.filter(fecha__gte=primer_mes).only('fecha', 'valor_total'))
        tendencia = [
            {'fecha': date(anio, mes, 1), 'total': total_mensual(recientes, anio, mes)}
            for anio, mes in meses
        ]
        total_mes, total_mes_anterior = tendencia[-1]['total'], tendencia[-2]['total']
        tratamientos = medicamentos_activos_del(usuario)

        return super().get_context_data(
            hoy=hoy,
            total_mes=total_mes,
            total_mes_anterior=total_mes_anterior,
            variacion=variacion_porcentual(total_mes, total_mes_anterior),
            total_anio=reportes.total(gastos.filter(fecha__year=hoy.year)),
            tendencia=tendencia,
            max_tendencia=max(t['total'] for t in tendencia),
            por_categoria_mes=reportes.totales_por_categoria(
                gastos.filter(fecha__year=hoy.year, fecha__month=hoy.month)
            ),
            mascotas=con_total_gastado(usuario.mascotas.filter(activa=True)),
            conteo_tratamientos=tratamientos.count(),
            medicamentos_activos=tratamientos.order_by(F('fecha_fin').asc(nulls_last=True), 'nombre')[:5],
            ultimos_gastos=gastos.select_related('mascota', 'categoria')[:6],
            **kwargs,
        )


# --- Mascotas ---

class MascotaLista(DelUsuarioMixin, ListView):
    model = Mascota
    context_object_name = 'mascotas'
    ESTADOS = {'activas': True, 'retiradas': False}

    def get_queryset(self):
        mascotas = super().get_queryset()
        self.conteos = {
            'todas': mascotas.count(),
            'activas': mascotas.filter(activa=True).count(),
            'retiradas': mascotas.filter(activa=False).count(),
        }
        self.q = self.request.GET.get('q', '').strip()
        self.estado = self.request.GET.get('estado', 'todas')
        if self.q:
            mascotas = mascotas.filter(nombre__icontains=self.q)
        if self.estado in self.ESTADOS:
            mascotas = mascotas.filter(activa=self.ESTADOS[self.estado])
        return con_total_gastado(mascotas)

    def get_context_data(self, **kwargs):
        return super().get_context_data(q=self.q, estado=self.estado, conteos=self.conteos, **kwargs)


class MascotaDetalle(DelUsuarioMixin, DetailView):
    model = Mascota

    def get_context_data(self, **kwargs):
        hoy = timezone.localdate()
        gastos = self.object.gastos.select_related('categoria')
        medicamentos = self.object.medicamentos.all()
        return super().get_context_data(
            gastos=gastos,
            total_gastos=reportes.total(gastos),
            total_mes=reportes.total(gastos.filter(fecha__year=hoy.year, fecha__month=hoy.month)),
            por_categoria=reportes.totales_por_categoria(gastos),
            medicamentos=medicamentos,
            medicamentos_activos=sum(1 for m in medicamentos if m.activo),
            ultimo_gasto=gastos.first(),
            **kwargs,
        )


class MascotaCrear(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = Mascota
    form_class = MascotaForm
    success_message = 'Mascota «%(nombre)s» registrada.'
    extra_context = {'titulo': 'Nueva mascota'}

    def form_valid(self, form):
        form.instance.usuario = self.request.user
        return super().form_valid(form)


class MascotaEditar(DelUsuarioMixin, SuccessMessageMixin, UpdateView):
    model = Mascota
    form_class = MascotaForm
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
    extra_context = {'tipo': 'mascota'}

    def get_context_data(self, **kwargs):
        return super().get_context_data(
            num_gastos=self.object.gastos.count(),
            num_medicamentos=self.object.medicamentos.count(),
            **kwargs,
        )

    def form_valid(self, form):
        nombre = str(self.object)
        try:
            self.object.delete()
        except ProtectedError:
            messages.error(
                self.request,
                f'No se puede eliminar «{nombre}» porque tiene gastos o medicamentos. Retírala en su lugar.',
            )
            return redirect('mascotas:mascota_detalle', pk=self.object.pk)
        messages.success(self.request, f'Mascota «{nombre}» eliminada.')
        return redirect(self.success_url)


# --- Gastos ---

class GastoLista(LoginRequiredMixin, ListView):
    context_object_name = 'gastos'
    template_name = 'mascotas/gasto_list.html'
    paginate_by = 15

    def get_queryset(self):
        self.filtro = GastoFiltroForm(self.request.GET or None, usuario=self.request.user)
        gastos = gastos_del(self.request.user).select_related('mascota', 'categoria')
        if self.filtro.is_valid():
            gastos = self.filtro.filtrar(gastos)
        return gastos

    def get_context_data(self, **kwargs):
        total = reportes.total(self.object_list)
        cantidad = self.object_list.count()
        filtrando = self.filtro.is_bound and any(self.request.GET.get(c) for c in self.filtro.fields)
        contexto = super().get_context_data(
            filtro=self.filtro,
            total=total,
            cantidad=cantidad,
            promedio=promedio(total, cantidad),
            filtrando=filtrando,
            filtros_aplicados=filtrando and self.filtro.is_valid(),
            tiene_mascotas=self.request.user.mascotas.exists(),
            **kwargs,
        )
        pagina = contexto['page_obj']
        contexto['paginas'] = pagina.paginator.get_elided_page_range(pagina.number, on_each_side=1, on_ends=1)
        return contexto


class GastoCrear(LoginRequiredMixin, FormConUsuarioMixin, SuccessMessageMixin, CreateView):
    model = Gasto
    form_class = GastoForm
    success_url = reverse_lazy('mascotas:gasto_lista')
    success_message = 'Gasto «%(producto)s» registrado.'
    extra_context = {'titulo': 'Nuevo gasto'}

    def get_initial(self):
        return {'fecha': timezone.localdate(), 'mascota': self.request.GET.get('mascota')}


class GastoEditar(DelUsuarioMixin, FormConUsuarioMixin, SuccessMessageMixin, UpdateView):
    model = Gasto
    campo_usuario = 'mascota__usuario'
    form_class = GastoForm
    success_url = reverse_lazy('mascotas:gasto_lista')
    success_message = 'Gasto «%(producto)s» actualizado.'
    extra_context = {'titulo': 'Editar gasto'}


class GastoEliminar(DelUsuarioMixin, EliminarConMensajeMixin, DeleteView):
    model = Gasto
    campo_usuario = 'mascota__usuario'
    template_name = 'mascotas/confirmar_eliminar.html'
    success_url = reverse_lazy('mascotas:gasto_lista')
    mensaje_eliminado = 'Gasto eliminado.'
    extra_context = {'tipo': 'gasto'}


# --- Medicamentos ---

class MedicamentoLista(LoginRequiredMixin, ListView):
    context_object_name = 'medicamentos'
    template_name = 'mascotas/medicamento_list.html'

    def get_queryset(self):
        todos = Medicamento.objects.filter(mascota__usuario=self.request.user).select_related('mascota')
        activos = medicamentos_activos_del(self.request.user)
        self.conteos = {'activos': activos.count(), 'historial': todos.count()}
        hoy = timezone.localdate()
        self.por_terminar = activos.filter(fecha_fin__range=(hoy, hoy + timedelta(days=DIAS_POR_TERMINAR))).count()
        self.historial = self.request.GET.get('ver') == 'historial'
        return todos if self.historial else activos.order_by(F('fecha_fin').asc(nulls_last=True), 'nombre')

    def get_context_data(self, **kwargs):
        return super().get_context_data(
            historial=self.historial, conteos=self.conteos, por_terminar=self.por_terminar,
            hoy=timezone.localdate(), **kwargs
        )


class MedicamentoCrear(LoginRequiredMixin, FormConUsuarioMixin, SuccessMessageMixin, CreateView):
    model = Medicamento
    form_class = MedicamentoForm
    success_url = reverse_lazy('mascotas:medicamento_lista')
    success_message = 'Medicamento «%(nombre)s» registrado.'
    extra_context = {'titulo': 'Nuevo medicamento'}

    def get_initial(self):
        return {'fecha_inicio': timezone.localdate(), 'mascota': self.request.GET.get('mascota')}


class MedicamentoEditar(DelUsuarioMixin, FormConUsuarioMixin, SuccessMessageMixin, UpdateView):
    model = Medicamento
    campo_usuario = 'mascota__usuario'
    form_class = MedicamentoForm
    success_url = reverse_lazy('mascotas:medicamento_lista')
    success_message = 'Medicamento «%(nombre)s» actualizado.'
    extra_context = {'titulo': 'Editar medicamento'}


class MedicamentoEliminar(DelUsuarioMixin, EliminarConMensajeMixin, DeleteView):
    model = Medicamento
    campo_usuario = 'mascota__usuario'
    template_name = 'mascotas/confirmar_eliminar.html'
    success_url = reverse_lazy('mascotas:medicamento_lista')
    mensaje_eliminado = 'Medicamento eliminado.'
    extra_context = {'tipo': 'medicamento'}


# --- Reportes ---

def rangos_predefinidos(hoy):
    inicio_mes = hoy.replace(day=1)
    fin_mes_anterior = inicio_mes - timedelta(days=1)
    return [
        ('Este mes', inicio_mes, hoy),
        ('Mes anterior', fin_mes_anterior.replace(day=1), fin_mes_anterior),
        ('Últimos 90 días', hoy - timedelta(days=89), hoy),
        ('Este año', date(hoy.year, 1, 1), hoy),
    ]


def grafico_mensual(mensual):
    """Serie cronológica y continua (meses sin gastos en 0) a partir del resumen mensual."""
    if not mensual:
        return []
    por_mes = {(m['mes'].year, m['mes'].month): m for m in mensual}
    inicio, fin = min(m['mes'] for m in mensual), max(m['mes'] for m in mensual)
    return [
        {
            'fecha': date(anio, mes, 1),
            'total': por_mes.get((anio, mes), {}).get('total', Decimal('0')),
            'cantidad': por_mes.get((anio, mes), {}).get('cantidad', 0),
        }
        for anio, mes in meses_entre(inicio, fin)
    ]


class Reportes(LoginRequiredMixin, TemplateView):
    template_name = 'mascotas/reportes.html'

    def get_context_data(self, **kwargs):
        rango = RangoFechasForm(self.request.GET or None)
        gastos = gastos_del(self.request.user)
        if rango.is_valid():
            gastos = rango.filtrar(gastos)
        desde, hasta = self.request.GET.get('desde', ''), self.request.GET.get('hasta', '')
        presets = [
            {
                'etiqueta': etiqueta, 'desde': inicio.isoformat(), 'hasta': fin.isoformat(),
                'activo': (desde, hasta) == (inicio.isoformat(), fin.isoformat()),
            }
            for etiqueta, inicio, fin in rangos_predefinidos(timezone.localdate())
        ]
        mensual = list(reportes.resumen_mensual(gastos))
        grafico = grafico_mensual(mensual)[-MESES_GRAFICO_REPORTE:]
        total, cantidad = reportes.total(gastos), gastos.count()
        return super().get_context_data(
            rango=rango,
            presets=presets,
            filtrando=bool(desde or hasta),
            total=total,
            cantidad=cantidad,
            promedio=promedio(total, cantidad),
            promedio_mensual=promedio(total, len(mensual)),
            grafico_mensual=grafico,
            max_grafico=max((g['total'] for g in grafico), default=Decimal('0')),
            por_mascota=reportes.totales_por_mascota(gastos),
            por_categoria=reportes.totales_por_categoria(gastos),
            mensual=mensual,
            max_mensual=max((m['total'] for m in mensual), default=Decimal('0')),
            productos=reportes.productos(gastos),
            **kwargs,
        )
