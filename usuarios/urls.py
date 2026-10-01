from django.urls import path

from .views import AccesoView, RegistroView, SalidaView

urlpatterns = [
    path("ingresar/", AccesoView.as_view(), name="login"),
    path("salir/", SalidaView.as_view(), name="logout"),
    path("registro/", RegistroView.as_view(), name="registro"),
]
