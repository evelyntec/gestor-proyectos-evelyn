from django.urls import path

from . import views

app_name = "proyectos"

urlpatterns = [
    path("", views.ResumenView.as_view(), name="resumen"),
    path("proyectos/", views.ProyectoListView.as_view(), name="lista"),
    path("proyectos/nuevo/", views.ProyectoCreateView.as_view(), name="crear"),
    path("proyectos/<int:pk>/", views.ProyectoDetailView.as_view(), name="detalle"),
    path("proyectos/<int:pk>/editar/", views.ProyectoUpdateView.as_view(), name="editar"),
    path("proyectos/<int:pk>/eliminar/", views.ProyectoDeleteView.as_view(), name="eliminar"),
    path("proyectos/<int:proyecto_pk>/tareas/nueva/", views.TareaCreateView.as_view(), name="tarea_crear"),
    path("tareas/", views.MisTareasView.as_view(), name="mis_tareas"),
    path("tareas/<int:pk>/editar/", views.TareaUpdateView.as_view(), name="tarea_editar"),
    path("tareas/<int:pk>/eliminar/", views.TareaDeleteView.as_view(), name="tarea_eliminar"),
    path("tareas/<int:pk>/alternar/", views.TareaAlternarView.as_view(), name="tarea_alternar"),
]
