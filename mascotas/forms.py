from django import forms
from django.db.models import Q

from .models import CategoriaGasto, Gasto, Mascota, Medicamento


class FechaInput(forms.DateInput):
    input_type = 'date'

    def __init__(self, **kwargs):
        super().__init__(format='%Y-%m-%d', **kwargs)


class MascotaForm(forms.ModelForm):
    class Meta:
        model = Mascota
        fields = [
            'nombre', 'especie', 'raza', 'sexo', 'fecha_nacimiento', 'peso',
            'color', 'estado_salud', 'observaciones',
        ]
        widgets = {'fecha_nacimiento': FechaInput(), 'observaciones': forms.Textarea(attrs={'rows': 3})}
        labels = {'fecha_nacimiento': 'Fecha de nacimiento'}


class MascotaDelUsuarioMixin:
    """Limita el campo `mascota` a las mascotas activas del usuario.

    Al editar, conserva la mascota actual aunque esté retirada.
    """

    def __init__(self, *args, usuario, **kwargs):
        super().__init__(*args, **kwargs)
        visibles = Q(activa=True)
        if self.instance.mascota_id:
            visibles |= Q(pk=self.instance.mascota_id)
        self.fields['mascota'].queryset = Mascota.objects.filter(visibles, usuario=usuario)


class GastoForm(MascotaDelUsuarioMixin, forms.ModelForm):
    class Meta:
        model = Gasto
        fields = [
            'mascota', 'categoria', 'producto', 'fecha', 'cantidad', 'valor_unitario',
            'proveedor', 'notas',
        ]
        widgets = {'fecha': FechaInput(), 'notas': forms.Textarea(attrs={'rows': 3})}
        labels = {'categoria': 'Categoría'}
        help_texts = {'valor_unitario': 'El valor total se calcula automáticamente.'}


class MedicamentoForm(MascotaDelUsuarioMixin, forms.ModelForm):
    class Meta:
        model = Medicamento
        fields = ['mascota', 'nombre', 'dosis', 'frecuencia', 'fecha_inicio', 'fecha_fin', 'observaciones']
        widgets = {
            'fecha_inicio': FechaInput(),
            'fecha_fin': FechaInput(),
            'observaciones': forms.Textarea(attrs={'rows': 3}),
        }
        labels = {'fecha_inicio': 'Fecha de inicio', 'fecha_fin': 'Fecha de finalización'}

    def clean(self):
        datos = super().clean()
        inicio, fin = datos.get('fecha_inicio'), datos.get('fecha_fin')
        if inicio and fin and fin < inicio:
            self.add_error('fecha_fin', 'La fecha de finalización no puede ser anterior a la de inicio.')
        return datos


class RangoFechasForm(forms.Form):
    desde = forms.DateField(required=False, widget=FechaInput())
    hasta = forms.DateField(required=False, widget=FechaInput())

    def clean(self):
        datos = super().clean()
        desde, hasta = datos.get('desde'), datos.get('hasta')
        if desde and hasta and desde > hasta:
            raise forms.ValidationError('La fecha inicial no puede ser posterior a la final.')
        return datos

    def filtrar(self, gastos):
        """Aplica el rango a un queryset de gastos; usar después de `is_valid()`."""
        if self.cleaned_data.get('desde'):
            gastos = gastos.filter(fecha__gte=self.cleaned_data['desde'])
        if self.cleaned_data.get('hasta'):
            gastos = gastos.filter(fecha__lte=self.cleaned_data['hasta'])
        return gastos


class GastoFiltroForm(RangoFechasForm):
    mascota = forms.ModelChoiceField(queryset=Mascota.objects.none(), required=False, empty_label='Todas')
    categoria = forms.ModelChoiceField(
        queryset=CategoriaGasto.objects.all(), required=False, empty_label='Todas', label='Categoría'
    )

    field_order = ['mascota', 'categoria', 'desde', 'hasta']

    def __init__(self, *args, usuario, **kwargs):
        super().__init__(*args, **kwargs)
        # Incluye retiradas: su historial sigue siendo consultable.
        self.fields['mascota'].queryset = Mascota.objects.filter(usuario=usuario)

    def filtrar(self, gastos):
        gastos = super().filtrar(gastos)
        for campo in ('mascota', 'categoria'):
            if self.cleaned_data.get(campo):
                gastos = gastos.filter(**{campo: self.cleaned_data[campo]})
        return gastos
