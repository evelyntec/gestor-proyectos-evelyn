from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import Proyecto, Tarea


class CampoFecha(forms.DateInput):
    input_type = "date"

    def __init__(self, attrs=None):
        super().__init__(attrs=attrs, format="%Y-%m-%d")


class ProyectoForm(forms.ModelForm):
    class Meta:
        model = Proyecto
        fields = ["nombre", "descripcion", "estado", "fecha_inicio", "fecha_limite"]
        labels = {
            "nombre": "Nombre del proyecto",
            "descripcion": "Descripción",
            "estado": "Estado",
            "fecha_inicio": "Fecha de inicio",
            "fecha_limite": "Fecha límite",
        }
        help_texts = {
            "fecha_limite": "Opcional. Debe ser igual o posterior a la fecha de inicio.",
        }
        widgets = {
            "nombre": forms.TextInput(attrs={"autofocus": True, "placeholder": "Ej.: Planificación de Matemática 5° básico"}),
            "descripcion": forms.Textarea(attrs={"rows": 4, "placeholder": "¿De qué se trata este proyecto?"}),
            "fecha_inicio": CampoFecha(),
            "fecha_limite": CampoFecha(),
        }

    def __init__(self, *args, usuario=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.usuario = usuario
        if usuario is not None and not self.instance.pk:
            self.instance.propietario = usuario

    def clean_nombre(self):
        nombre = " ".join(self.cleaned_data["nombre"].split())
        existentes = Proyecto.objects.filter(propietario=self.usuario, nombre__iexact=nombre)
        if self.instance.pk:
            existentes = existentes.exclude(pk=self.instance.pk)
        if existentes.exists():
            raise ValidationError("Ya tienes un proyecto con este nombre.")
        return nombre


class TareaForm(forms.ModelForm):
    class Meta:
        model = Tarea
        fields = ["titulo", "descripcion", "prioridad", "fecha_limite", "completada"]
        labels = {
            "titulo": "Título",
            "descripcion": "Descripción",
            "prioridad": "Prioridad",
            "fecha_limite": "Fecha límite",
            "completada": "Marcar como completada",
        }
        widgets = {
            "titulo": forms.TextInput(attrs={"autofocus": True, "placeholder": "Ej.: Preparar guía de fracciones"}),
            "descripcion": forms.Textarea(attrs={"rows": 3}),
            "fecha_limite": CampoFecha(),
        }

    def __init__(self, *args, proyecto=None, **kwargs):
        super().__init__(*args, **kwargs)
        if proyecto is not None:
            self.instance.proyecto = proyecto

    def clean_titulo(self):
        return " ".join(self.cleaned_data["titulo"].split())

    def clean_fecha_limite(self):
        fecha = self.cleaned_data.get("fecha_limite")
        if fecha and "fecha_limite" in self.changed_data and fecha < timezone.localdate():
            raise ValidationError("La fecha límite no puede estar en el pasado.")
        return fecha
