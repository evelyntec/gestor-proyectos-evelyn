from datetime import timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from proyectos.models import Proyecto, Tarea


class Command(BaseCommand):
    help = "Crea una cuenta de ejemplo con proyectos y tareas."

    def handle(self, *args, **options):
        hoy = timezone.localdate()
        usuaria, creada = User.objects.get_or_create(
            username="evelyn",
            defaults={"first_name": "Evelyn", "last_name": "Álvarez", "email": "evelyn@ejemplo.cl"},
        )
        if creada:
            usuaria.set_password("Evelyn2026!")
            usuaria.save()

        datos = [
            (
                "Planificación de Matemática 5° básico",
                "Clases del segundo semestre: fracciones, decimales y geometría.",
                Proyecto.Estado.EN_CURSO,
                hoy - timedelta(days=20),
                hoy + timedelta(days=60),
                [
                    ("Preparar guía de fracciones equivalentes", Tarea.Prioridad.ALTA, 2, True),
                    ("Diseñar evaluación formativa de decimales", Tarea.Prioridad.MEDIA, 9, False),
                    ("Seleccionar material concreto para geometría", Tarea.Prioridad.BAJA, 20, False),
                    ("Revisar resultados del diagnóstico", Tarea.Prioridad.ALTA, -3, False),
                ],
            ),
            (
                "Portafolio web profesional",
                "Publicar proyectos de programación y material docente en GitHub.",
                Proyecto.Estado.EN_CURSO,
                hoy - timedelta(days=5),
                hoy + timedelta(days=30),
                [
                    ("Subir este gestor de proyectos a GitHub", Tarea.Prioridad.ALTA, 1, False),
                    ("Tomar capturas de pantalla de la aplicación", Tarea.Prioridad.MEDIA, 3, True),
                    ("Enlazar el repositorio en el currículum", Tarea.Prioridad.MEDIA, 5, False),
                ],
            ),
            (
                "Mini ensayo SIMCE 4° básico",
                "Ensayo breve de Matemática con retroalimentación por eje.",
                Proyecto.Estado.PLANIFICADO,
                hoy + timedelta(days=7),
                hoy + timedelta(days=45),
                [
                    ("Elegir objetivos de aprendizaje a evaluar", Tarea.Prioridad.MEDIA, 14, False),
                ],
            ),
        ]

        for nombre, descripcion, estado, inicio, limite, tareas in datos:
            proyecto, _ = Proyecto.objects.get_or_create(
                propietario=usuaria,
                nombre=nombre,
                defaults={
                    "descripcion": descripcion,
                    "estado": estado,
                    "fecha_inicio": inicio,
                    "fecha_limite": limite,
                },
            )
            for titulo, prioridad, dias, completada in tareas:
                Tarea.objects.get_or_create(
                    proyecto=proyecto,
                    titulo=titulo,
                    defaults={
                        "prioridad": prioridad,
                        "fecha_limite": hoy + timedelta(days=dias),
                        "completada": completada,
                    },
                )

        self.stdout.write(self.style.SUCCESS("Datos de ejemplo listos."))
        self.stdout.write("Usuario: evelyn  |  Contraseña: Evelyn2026!")
