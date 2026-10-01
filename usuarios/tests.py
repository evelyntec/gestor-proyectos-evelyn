from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .forms import RegistroForm


class RegistroFormTests(TestCase):
    def datos(self, **cambios):
        datos = {
            "username": "evelyn",
            "first_name": "Evelyn",
            "last_name": "Álvarez",
            "email": "evelyn@ejemplo.cl",
            "password1": "Clave-Segura-2026",
            "password2": "Clave-Segura-2026",
        }
        datos.update(cambios)
        return datos

    def test_formulario_valido(self):
        self.assertTrue(RegistroForm(data=self.datos()).is_valid())

    def test_correo_duplicado_no_es_valido(self):
        User.objects.create_user("otra", "evelyn@ejemplo.cl", "Clave-Segura-2026")
        form = RegistroForm(data=self.datos(email="EVELYN@ejemplo.cl"))
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_contrasenas_distintas_no_son_validas(self):
        form = RegistroForm(data=self.datos(password2="Otra-Clave-2026"))
        self.assertFalse(form.is_valid())
        self.assertIn("password2", form.errors)

    def test_contrasena_debil_no_es_valida(self):
        form = RegistroForm(data=self.datos(password1="12345678", password2="12345678"))
        self.assertFalse(form.is_valid())


class AutenticacionViewsTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user("evelyn", "evelyn@ejemplo.cl", "Clave-Segura-2026", first_name="Evelyn")

    def test_registro_crea_usuario_e_inicia_sesion(self):
        respuesta = self.client.post(
            reverse("registro"),
            {
                "username": "nueva",
                "first_name": "Ana",
                "last_name": "Rojas",
                "email": "ana@ejemplo.cl",
                "password1": "Clave-Segura-2026",
                "password2": "Clave-Segura-2026",
            },
        )
        self.assertRedirects(respuesta, reverse("proyectos:resumen"))
        self.assertTrue(User.objects.filter(username="nueva").exists())
        self.assertEqual(int(self.client.session["_auth_user_id"]), User.objects.get(username="nueva").pk)

    def test_login_redirige_al_resumen(self):
        respuesta = self.client.post(reverse("login"), {"username": "evelyn", "password": "Clave-Segura-2026"})
        self.assertRedirects(respuesta, reverse("proyectos:resumen"))

    def test_login_con_clave_incorrecta_muestra_error(self):
        respuesta = self.client.post(reverse("login"), {"username": "evelyn", "password": "incorrecta"})
        self.assertEqual(respuesta.status_code, 200)
        self.assertFalse(respuesta.context["form"].is_valid())

    def test_logout_por_post_redirige_al_login(self):
        self.client.force_login(self.usuario)
        respuesta = self.client.post(reverse("logout"))
        self.assertRedirects(respuesta, reverse("login"))
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_usuario_autenticado_no_ve_registro(self):
        self.client.force_login(self.usuario)
        respuesta = self.client.get(reverse("registro"))
        self.assertRedirects(respuesta, reverse("proyectos:resumen"))

    def test_login_exige_token_csrf(self):
        cliente = self.client_class(enforce_csrf_checks=True)
        respuesta = cliente.post(reverse("login"), {"username": "evelyn", "password": "Clave-Segura-2026"})
        self.assertEqual(respuesta.status_code, 403)
