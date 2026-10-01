from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinLengthValidator
from django.db import models
from django.db.models import F
from django.urls import reverse
from django.utils import timezone


class Proyecto(models.Model):
    class Estado(models.TextChoices):
        PLANIFICADO = "planificado", "Planificado"
        EN_CURSO = "en_curso", "En curso"
        FINALIZADO = "finalizado", "Finalizado"

    propietario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="proyectos",
        verbose_name="propietario",
    )
    nombre = models.CharField("nombre", max_length=120, validators=[MinLengthValidator(3)])
    descripcion = models.TextField("descripción", blank=True)
    estado = models.CharField("estado", max_length=20, choices=Estado.choices, default=Estado.PLANIFICADO)
    fecha_inicio = models.DateField("fecha de inicio", default=timezone.localdate)
    fecha_limite = models.DateField("fecha límite", null=True, blank=True)
    creado = models.DateTimeField("creado", auto_now_add=True)
    actualizado = models.DateTimeField("actualizado", auto_now=True)

    class Meta:
        ordering = ["-actualizado"]
        verbose_name = "proyecto"
        verbose_name_plural = "proyectos"
        constraints = [
            models.UniqueConstraint(fields=["propietario", "nombre"], name="proyecto_unico_por_usuario"),
        ]

    def __str__(self):
        return self.nombre

    def get_absolute_url(self):
        return reverse("proyectos:detalle", args=[self.pk])

    def clean(self):
        if self.fecha_limite and self.fecha_inicio and self.fecha_limite < self.fecha_inicio:
            raise ValidationError(
                {"fecha_limite": "La fecha límite no puede ser anterior a la fecha de inicio."}
            )

    @property
    def avance(self):
        total = getattr(self, "num_tareas", None)
        completadas = getattr(self, "num_completadas", None)
        if total is None or completadas is None:
            total = self.tareas.count()
            completadas = self.tareas.filter(completada=True).count()
        return round(completadas * 100 / total) if total else 0


class Tarea(models.Model):
    class Prioridad(models.TextChoices):
        BAJA = "baja", "Baja"
        MEDIA = "media", "Media"
        ALTA = "alta", "Alta"

    proyecto = models.ForeignKey(
        Proyecto,
        on_delete=models.CASCADE,
        related_name="tareas",
        verbose_name="proyecto",
    )
    titulo = models.CharField("título", max_length=150, validators=[MinLengthValidator(3)])
    descripcion = models.TextField("descripción", blank=True)
    prioridad = models.CharField("prioridad", max_length=10, choices=Prioridad.choices, default=Prioridad.MEDIA)
    fecha_limite = models.DateField("fecha límite", null=True, blank=True)
    completada = models.BooleanField("completada", default=False)
    creada = models.DateTimeField("creada", auto_now_add=True)
    actualizada = models.DateTimeField("actualizada", auto_now=True)

    class Meta:
        ordering = ["completada", F("fecha_limite").asc(nulls_last=True), "-creada"]
        verbose_name = "tarea"
        verbose_name_plural = "tareas"

    def __str__(self):
        return self.titulo

    def get_absolute_url(self):
        return self.proyecto.get_absolute_url()

    def clean(self):
        if not self.proyecto_id or not self.fecha_limite:
            return
        cierre = self.proyecto.fecha_limite
        if cierre and self.fecha_limite > cierre:
            raise ValidationError(
                {"fecha_limite": f"La tarea no puede vencer después del cierre del proyecto ({cierre:%d-%m-%Y})."}
            )

    @property
    def vencida(self):
        return bool(not self.completada and self.fecha_limite and self.fecha_limite < timezone.localdate())
