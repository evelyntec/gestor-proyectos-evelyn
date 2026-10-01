from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView

from .forms import RegistroForm


class AccesoView(LoginView):
    template_name = "registration/login.html"
    redirect_authenticated_user = True

    def form_valid(self, form):
        respuesta = super().form_valid(form)
        usuario = form.get_user()
        messages.success(self.request, f"Hola de nuevo, {usuario.first_name or usuario.username}.")
        return respuesta


class SalidaView(LogoutView):
    def post(self, request, *args, **kwargs):
        respuesta = super().post(request, *args, **kwargs)
        messages.info(request, "Cerraste sesión correctamente.")
        return respuesta


class RegistroView(CreateView):
    form_class = RegistroForm
    template_name = "registration/registro.html"
    success_url = reverse_lazy("proyectos:resumen")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(self.success_url)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        usuario = form.save()
        login(self.request, usuario)
        messages.success(self.request, f"Cuenta creada. Te damos la bienvenida, {usuario.first_name}.")
        return redirect(self.success_url)
