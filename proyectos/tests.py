from datetime import timedelta

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .forms import ProyectoForm, TareaForm
from .models import Proyecto, Tarea


class BaseProyectosTest(TestCase):
    def setUp(self):
        self.hoy = timezone.localdate()
        self.evelyn = User.objects.create_user("evelyn", "evelyn@ejemplo.cl", "Clave-Segura-2026", first_name="Evelyn")
        self.otra = User.objects.create_user("otra", "otra@ejemplo.cl", "Clave-Segura-2026")
        self.proyecto = Proyecto.objects.create(
            propietario=self.evelyn,
            nombre="Planificación Matemática",
            fecha_inicio=self.hoy,
            fecha_limite=self.hoy + timedelta(days=30),
        )
        self.proyecto_ajeno = Proyecto.objects.create(propietario=self.otra, nombre="Proyecto ajeno")


class ProyectoModelTests(BaseProyectosTest):
    def test_str_y_url(self):
        self.assertEqual(str(self.proyecto), "Planificación Matemática")
        self.assertEqual(self.proyecto.get_absolute_url(), reverse("proyectos:detalle", args=[self.proyecto.pk]))

    def test_estado_por_defecto(self):
        self.assertEqual(self.proyecto.estado, Proyecto.Estado.PLANIFICADO)

    def test_avance_sin_tareas_es_cero(self):
        self.assertEqual(self.proyecto.avance, 0)

    def test_avance_calcula_porcentaje(self):
        Tarea.objects.create(proyecto=self.proyecto, titulo="Guía de fracciones", completada=True)
        Tarea.objects.create(proyecto=self.proyecto, titulo="Evaluación formativa")
        Tarea.objects.create(proyecto=self.proyecto, titulo="Material concreto")
        Tarea.objects.create(proyecto=self.proyecto, titulo="Revisión de notas", completada=True)
        self.assertEqual(self.proyecto.avance, 50)

    def test_fecha_limite_anterior_al_inicio_no_es_valida(self):
        self.proyecto.fecha_limite = self.hoy - timedelta(days=1)
        with self.assertRaises(ValidationError):
            self.proyecto.full_clean()

    def test_un_usuario_gestiona_multiples_proyectos_y_tareas(self):
        segundo = Proyecto.objects.create(propietario=self.evelyn, nombre="Portafolio")
        Tarea.objects.create(proyecto=self.proyecto, titulo="Tarea uno")
        Tarea.objects.create(proyecto=segundo, titulo="Tarea dos")
        self.assertEqual(self.evelyn.proyectos.count(), 2)
        self.assertEqual(Tarea.objects.filter(proyecto__propietario=self.evelyn).count(), 2)


class TareaModelTests(BaseProyectosTest):
    def test_tarea_vencida(self):
        tarea = Tarea(proyecto=self.proyecto, titulo="Atrasada", fecha_limite=self.hoy - timedelta(days=1))
        self.assertTrue(tarea.vencida)
        tarea.completada = True
        self.assertFalse(tarea.vencida)

    def test_tarea_no_puede_vencer_despues_del_proyecto(self):
        tarea = Tarea(proyecto=self.proyecto, titulo="Muy tarde", fecha_limite=self.hoy + timedelta(days=60))
        with self.assertRaises(ValidationError):
            tarea.full_clean()

    def test_titulo_corto_no_es_valido(self):
        with self.assertRaises(ValidationError):
            Tarea(proyecto=self.proyecto, titulo="ab").full_clean()

    def test_eliminar_proyecto_elimina_tareas(self):
        Tarea.objects.create(proyecto=self.proyecto, titulo="Se va con el proyecto")
        self.proyecto.delete()
        self.assertFalse(Tarea.objects.exists())


class FormulariosTests(BaseProyectosTest):
    def test_proyecto_con_nombre_repetido_no_es_valido(self):
        form = ProyectoForm(
            data={"nombre": "  planificación   matemática ", "estado": "planificado", "fecha_inicio": self.hoy},
            usuario=self.evelyn,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("nombre", form.errors)

    def test_otro_usuario_puede_repetir_nombre(self):
        form = ProyectoForm(
            data={"nombre": "Planificación Matemática", "estado": "planificado", "fecha_inicio": self.hoy},
            usuario=self.otra,
        )
        self.assertTrue(form.is_valid())

    def test_formulario_proyecto_valida_fechas(self):
        form = ProyectoForm(
            data={
                "nombre": "Fechas cruzadas",
                "estado": "planificado",
                "fecha_inicio": self.hoy,
                "fecha_limite": self.hoy - timedelta(days=3),
            },
            usuario=self.evelyn,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("fecha_limite", form.errors)

    def test_tarea_con_fecha_pasada_no_es_valida(self):
        form = TareaForm(
            data={"titulo": "Ayer", "prioridad": "media", "fecha_limite": self.hoy - timedelta(days=1)},
            proyecto=self.proyecto,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("fecha_limite", form.errors)

    def test_tarea_valida_normaliza_titulo(self):
        form = TareaForm(data={"titulo": "  Preparar   guía  ", "prioridad": "alta"}, proyecto=self.proyecto)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["titulo"], "Preparar guía")


class AccesoVistasTests(BaseProyectosTest):
    def test_vistas_protegidas_redirigen_al_login(self):
        rutas = [
            reverse("proyectos:resumen"),
            reverse("proyectos:lista"),
            reverse("proyectos:crear"),
            reverse("proyectos:detalle", args=[self.proyecto.pk]),
            reverse("proyectos:mis_tareas"),
            reverse("proyectos:tarea_crear", args=[self.proyecto.pk]),
        ]
        for ruta in rutas:
            with self.subTest(ruta=ruta):
                respuesta = self.client.get(ruta)
                self.assertRedirects(respuesta, f"{reverse('login')}?next={ruta}")

    def test_no_se_puede_ver_proyecto_ajeno(self):
        self.client.force_login(self.evelyn)
        for nombre in ("detalle", "editar", "eliminar"):
            with self.subTest(vista=nombre):
                respuesta = self.client.get(reverse(f"proyectos:{nombre}", args=[self.proyecto_ajeno.pk]))
                self.assertEqual(respuesta.status_code, 404)

    def test_no_se_puede_agregar_tarea_a_proyecto_ajeno(self):
        self.client.force_login(self.evelyn)
        respuesta = self.client.post(
            reverse("proyectos:tarea_crear", args=[self.proyecto_ajeno.pk]),
            {"titulo": "Intrusa", "prioridad": "media"},
        )
        self.assertEqual(respuesta.status_code, 404)
        self.assertFalse(Tarea.objects.filter(titulo="Intrusa").exists())

    def test_formularios_exigen_token_csrf(self):
        cliente = self.client_class(enforce_csrf_checks=True)
        cliente.force_login(self.evelyn)
        respuesta = cliente.post(reverse("proyectos:crear"), {"nombre": "Sin token", "estado": "planificado", "fecha_inicio": self.hoy})
        self.assertEqual(respuesta.status_code, 403)


class ProyectoVistasTests(BaseProyectosTest):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.evelyn)

    def test_resumen_muestra_solo_datos_propios(self):
        Tarea.objects.create(proyecto=self.proyecto, titulo="Pendiente propia")
        Tarea.objects.create(proyecto=self.proyecto_ajeno, titulo="Pendiente ajena")
        respuesta = self.client.get(reverse("proyectos:resumen"))
        self.assertEqual(respuesta.status_code, 200)
        self.assertTemplateUsed(respuesta, "base.html")
        self.assertEqual(respuesta.context["total_proyectos"], 1)
        self.assertEqual(respuesta.context["tareas_pendientes"], 1)
        self.assertContains(respuesta, "Planificación Matemática")
        self.assertNotContains(respuesta, "Proyecto ajeno")

    def test_lista_filtra_por_estado_y_busqueda(self):
        Proyecto.objects.create(propietario=self.evelyn, nombre="Portafolio web", estado=Proyecto.Estado.EN_CURSO)
        respuesta = self.client.get(reverse("proyectos:lista"), {"estado": "en_curso"})
        self.assertEqual([p.nombre for p in respuesta.context["proyectos"]], ["Portafolio web"])
        respuesta = self.client.get(reverse("proyectos:lista"), {"q": "matem"})
        self.assertEqual([p.nombre for p in respuesta.context["proyectos"]], ["Planificación Matemática"])

    def test_crear_proyecto_asigna_propietario(self):
        respuesta = self.client.post(
            reverse("proyectos:crear"),
            {"nombre": "Ensayo SIMCE", "descripcion": "", "estado": "planificado", "fecha_inicio": self.hoy},
        )
        proyecto = Proyecto.objects.get(nombre="Ensayo SIMCE")
        self.assertRedirects(respuesta, proyecto.get_absolute_url())
        self.assertEqual(proyecto.propietario, self.evelyn)

    def test_crear_proyecto_invalido_no_guarda(self):
        respuesta = self.client.post(reverse("proyectos:crear"), {"nombre": "", "estado": "planificado", "fecha_inicio": self.hoy})
        self.assertEqual(respuesta.status_code, 200)
        self.assertTrue(respuesta.context["form"].errors)
        self.assertEqual(self.evelyn.proyectos.count(), 1)

    def test_editar_proyecto(self):
        respuesta = self.client.post(
            reverse("proyectos:editar", args=[self.proyecto.pk]),
            {"nombre": "Planificación renovada", "estado": "en_curso", "fecha_inicio": self.hoy},
        )
        self.assertRedirects(respuesta, self.proyecto.get_absolute_url())
        self.proyecto.refresh_from_db()
        self.assertEqual(self.proyecto.nombre, "Planificación renovada")
        self.assertEqual(self.proyecto.estado, Proyecto.Estado.EN_CURSO)

    def test_eliminar_proyecto(self):
        respuesta = self.client.post(reverse("proyectos:eliminar", args=[self.proyecto.pk]))
        self.assertRedirects(respuesta, reverse("proyectos:lista"))
        self.assertFalse(Proyecto.objects.filter(pk=self.proyecto.pk).exists())


class TareaVistasTests(BaseProyectosTest):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.evelyn)
        self.tarea = Tarea.objects.create(proyecto=self.proyecto, titulo="Preparar guía")

    def test_crear_tarea(self):
        respuesta = self.client.post(
            reverse("proyectos:tarea_crear", args=[self.proyecto.pk]),
            {"titulo": "Diseñar evaluación", "prioridad": "alta", "fecha_limite": self.hoy + timedelta(days=5)},
        )
        self.assertRedirects(respuesta, self.proyecto.get_absolute_url())
        self.assertTrue(self.proyecto.tareas.filter(titulo="Diseñar evaluación").exists())

    def test_editar_tarea(self):
        respuesta = self.client.post(
            reverse("proyectos:tarea_editar", args=[self.tarea.pk]),
            {"titulo": "Preparar guía corregida", "prioridad": "baja", "completada": "on"},
        )
        self.assertRedirects(respuesta, self.proyecto.get_absolute_url())
        self.tarea.refresh_from_db()
        self.assertTrue(self.tarea.completada)
        self.assertEqual(self.tarea.prioridad, Tarea.Prioridad.BAJA)

    def test_eliminar_tarea(self):
        respuesta = self.client.post(reverse("proyectos:tarea_eliminar", args=[self.tarea.pk]))
        self.assertRedirects(respuesta, self.proyecto.get_absolute_url())
        self.assertFalse(Tarea.objects.filter(pk=self.tarea.pk).exists())

    def test_alternar_tarea_por_post(self):
        url = reverse("proyectos:tarea_alternar", args=[self.tarea.pk])
        respuesta = self.client.post(url, {"siguiente": reverse("proyectos:mis_tareas")})
        self.assertRedirects(respuesta, reverse("proyectos:mis_tareas"))
        self.tarea.refresh_from_db()
        self.assertTrue(self.tarea.completada)

    def test_alternar_ignora_redireccion_externa(self):
        url = reverse("proyectos:tarea_alternar", args=[self.tarea.pk])
        respuesta = self.client.post(url, {"siguiente": "https://sitio-malicioso.com/"})
        self.assertRedirects(respuesta, self.proyecto.get_absolute_url())

    def test_alternar_no_acepta_get(self):
        respuesta = self.client.get(reverse("proyectos:tarea_alternar", args=[self.tarea.pk]))
        self.assertEqual(respuesta.status_code, 405)

    def test_no_se_puede_editar_tarea_ajena(self):
        ajena = Tarea.objects.create(proyecto=self.proyecto_ajeno, titulo="Tarea ajena")
        respuesta = self.client.get(reverse("proyectos:tarea_editar", args=[ajena.pk]))
        self.assertEqual(respuesta.status_code, 404)

    def test_mis_tareas_filtra_vencidas(self):
        vencida = Tarea.objects.create(proyecto=self.proyecto, titulo="Vencida", fecha_limite=self.hoy - timedelta(days=2))
        respuesta = self.client.get(reverse("proyectos:mis_tareas"), {"filtro": "vencidas"})
        self.assertEqual(list(respuesta.context["tareas"]), [vencida])
