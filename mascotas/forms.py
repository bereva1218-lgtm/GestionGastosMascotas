from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.db.models import Q

from .models import CategoriaGasto, Gasto, Mascota, Medicamento

# Mensajes de validación en "tú" (los de Django vienen en "usted").
MENSAJES_POR_TIPO = {
    forms.DateField: {'invalid': 'Escribe una fecha válida.'},
    forms.DecimalField: {
        'invalid': 'Escribe un número válido.',
        'max_digits': 'Usa como máximo %(max)s dígitos en total.',
        'max_decimal_places': 'Usa como máximo %(max)s decimales.',
        'max_whole_digits': 'Usa como máximo %(max)s dígitos antes de la coma.',
    },
    forms.ModelChoiceField: {'invalid_choice': 'Elige una opción de la lista.'},
    forms.ChoiceField: {'invalid_choice': 'Elige una opción de la lista.'},
}


class MensajesEnTuMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for campo in self.fields.values():
            for tipo, mensajes in MENSAJES_POR_TIPO.items():
                if isinstance(campo, tipo):
                    campo.error_messages.update(mensajes)


class FechaInput(forms.DateInput):
    input_type = 'date'

    def __init__(self, **kwargs):
        super().__init__(format='%Y-%m-%d', **kwargs)


class MascotaForm(MensajesEnTuMixin, forms.ModelForm):
    class Meta:
        model = Mascota
        fields = [
            'nombre', 'especie', 'raza', 'sexo', 'fecha_nacimiento', 'peso',
            'color', 'estado_salud', 'observaciones',
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={'placeholder': 'Michi'}),
            'especie': forms.TextInput(attrs={'placeholder': 'Gato, perro…'}),
            'raza': forms.TextInput(attrs={'placeholder': 'Criollo, siamés…'}),
            'fecha_nacimiento': FechaInput(),
            'color': forms.TextInput(attrs={'placeholder': 'Atigrado, negro…'}),
            'estado_salud': forms.TextInput(attrs={'placeholder': 'Sana, en tratamiento…'}),
            'observaciones': forms.Textarea(attrs={'rows': 3}),
        }
        labels = {'fecha_nacimiento': 'Fecha de nacimiento', 'peso': 'Peso'}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['sexo'].choices = [('', 'Selecciona el sexo'), *Mascota.Sexo.choices]


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
        self.fields['mascota'].empty_label = 'Selecciona una mascota'


class GastoForm(MascotaDelUsuarioMixin, MensajesEnTuMixin, forms.ModelForm):
    class Meta:
        model = Gasto
        fields = [
            'mascota', 'categoria', 'producto', 'fecha', 'cantidad', 'valor_unitario',
            'proveedor', 'notas',
        ]
        widgets = {
            'producto': forms.TextInput(attrs={'placeholder': 'Concentrado 3 kg'}),
            'fecha': FechaInput(),
            'proveedor': forms.TextInput(attrs={'placeholder': 'Tienda o veterinaria'}),
            'notas': forms.Textarea(attrs={'rows': 3}),
        }
        labels = {'categoria': 'Categoría'}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['categoria'].empty_label = 'Selecciona una categoría'


class MedicamentoForm(MascotaDelUsuarioMixin, MensajesEnTuMixin, forms.ModelForm):
    class Meta:
        model = Medicamento
        fields = ['mascota', 'nombre', 'dosis', 'frecuencia', 'fecha_inicio', 'fecha_fin', 'observaciones']
        widgets = {
            'nombre': forms.TextInput(attrs={'placeholder': 'Antipulgas'}),
            'dosis': forms.TextInput(attrs={'placeholder': 'Ej.: 1 pipeta, 5 ml'}),
            'frecuencia': forms.TextInput(attrs={'placeholder': 'Ej.: cada 12 horas, mensual'}),
            'fecha_inicio': FechaInput(),
            'fecha_fin': FechaInput(),
            'observaciones': forms.Textarea(attrs={'rows': 3}),
        }
        labels = {'fecha_inicio': 'Fecha de inicio', 'fecha_fin': 'Fecha de finalización'}
        help_texts = {'fecha_fin': 'Déjala vacía si el tratamiento es continuo.'}

    def clean(self):
        datos = super().clean()
        inicio, fin = datos.get('fecha_inicio'), datos.get('fecha_fin')
        if inicio and fin and fin < inicio:
            self.add_error('fecha_fin', 'La fecha de finalización no puede ser anterior a la de inicio.')
        return datos


class RangoFechasForm(MensajesEnTuMixin, forms.Form):
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
    q = forms.CharField(
        label='Buscar', required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Producto o proveedor', 'type': 'search'}),
    )
    mascota = forms.ModelChoiceField(queryset=Mascota.objects.none(), required=False, empty_label='Todas')
    categoria = forms.ModelChoiceField(
        queryset=CategoriaGasto.objects.all(), required=False, empty_label='Todas', label='Categoría'
    )

    field_order = ['q', 'mascota', 'categoria', 'desde', 'hasta']

    def __init__(self, *args, usuario, **kwargs):
        super().__init__(*args, **kwargs)
        # Incluye retiradas: su historial sigue siendo consultable.
        self.fields['mascota'].queryset = Mascota.objects.filter(usuario=usuario)

    def filtrar(self, gastos):
        gastos = super().filtrar(gastos)
        if self.cleaned_data.get('q'):
            texto = self.cleaned_data['q']
            gastos = gastos.filter(Q(producto__icontains=texto) | Q(proveedor__icontains=texto))
        for campo in ('mascota', 'categoria'):
            if self.cleaned_data.get(campo):
                gastos = gastos.filter(**{campo: self.cleaned_data[campo]})
        return gastos


# --- Cuentas ---

class RegistroForm(UserCreationForm):
    error_messages = {**UserCreationForm.error_messages, 'password_mismatch': 'Las contraseñas no coinciden.'}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'Nombre de usuario'
        self.fields['username'].help_text = 'Hasta 150 caracteres: letras, números y @ . + - _'
        self.fields['password1'].label = 'Contraseña'
        self.fields['password1'].help_text = (
            '<ul><li>Al menos 8 caracteres.</li><li>Que no se parezca a tu nombre de usuario.</li>'
            '<li>Que no sea una contraseña común ni solo números.</li></ul>'
        )
        self.fields['password2'].label = 'Confirma tu contraseña'
        self.fields['password2'].help_text = 'Escribe la misma contraseña otra vez.'


class AccesoForm(AuthenticationForm):
    error_messages = {
        'invalid_login': 'Usuario o contraseña incorrectos. Ten en cuenta que distinguen mayúsculas y minúsculas.',
        'inactive': 'Esta cuenta está desactivada.',
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'Nombre de usuario'
        self.fields['password'].label = 'Contraseña'
