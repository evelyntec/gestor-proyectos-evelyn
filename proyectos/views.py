from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Count, F, Q
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.http import url_has_allowed_host_and_scheme
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, ListView, TemplateView, UpdateView

from .forms import ProyectoForm, TareaForm
from .models import Proyecto, Tarea


def proyectos_con_avance(usuario):
    return Proyecto.objects.filter(propietario=usuario).annotate(
        num_tareas=Count("tareas"),
        num_completadas=Count("tareas", filter=Q(tareas__completada=True)),
    ).order_by("-actualizado")


def tareas_de(usuario):
    return Tarea.objects.filter(proyecto__propietario=usuario).select_related("proyecto")


class ResumenView(LoginRequiredMixin, TemplateView):
    template_name = "proyectos/resumen.html"

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        hoy = timezone.localdate()
        usuario = self.request.user
        tareas = tareas_de(usuario)
        conteo = tareas.aggregate(
            pendientes=Count("id", filter=Q(completada=False)),
            completadas=Count("id", filter=Q(completada=True)),
            vencidas=Count("id", filter=Q(completada=False, fecha_limite__lt=hoy)),
        )
        contexto.update(
            {
                "hoy": hoy,
                "proyectos": proyectos_con_avance(usuario).exclude(estado=Proyecto.Estado.FINALIZADO)[:6],
                "total_proyectos": usuario.proyectos.count(),
                "proyectos_en_curso": usuario.proyectos.filter(estado=Proyecto.Estado.EN_CURSO).count(),
                "tareas_pendientes": conteo["pendientes"],
                "tareas_completadas": conteo["completadas"],
                "tareas_vencidas": conteo["vencidas"],
                "proximas_tareas": tareas.filter(completada=False).order_by(
                    F("fecha_limite").asc(nulls_last=True), "-creada"
                )[:5],
            }
        )
        return contexto


class ProyectoListView(LoginRequiredMixin, ListView):
    template_name = "proyectos/proyecto_list.html"
    context_object_name = "proyectos"
    paginate_by = 9

    def get_queryset(self):
        self.estado = self.request.GET.get("estado", "")
        self.busqueda = self.request.GET.get("q", "").strip()
        proyectos = proyectos_con_avance(self.request.user)
        if self.estado in Proyecto.Estado.values:
            proyectos = proyectos.filter(estado=self.estado)
        if self.busqueda:
            proyectos = proyectos.filter(Q(nombre__icontains=self.busqueda) | Q(descripcion__icontains=self.busqueda))
        return proyectos

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        filtros = {clave: valor for clave, valor in {"estado": self.estado, "q": self.busqueda}.items() if valor}
        contexto.update(
            {
                "estados": Proyecto.Estado.choices,
                "estado_actual": self.estado,
                "busqueda": self.busqueda,
                "filtros": urlencode(filtros),
            }
        )
        return contexto


class ProyectoDetailView(LoginRequiredMixin, DetailView):
    template_name = "proyectos/proyecto_detail.html"
    context_object_name = "proyecto"

    def get_queryset(self):
        return proyectos_con_avance(self.request.user)

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto["tareas"] = self.object.tareas.all()
        return contexto


class ProyectoFormularioMixin(LoginRequiredMixin, SuccessMessageMixin):
    form_class = ProyectoForm
    template_name = "proyectos/proyecto_form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["usuario"] = self.request.user
        return kwargs


class ProyectoCreateView(ProyectoFormularioMixin, CreateView):
    success_message = "Proyecto «%(nombre)s» creado."

    def form_valid(self, form):
        form.instance.propietario = self.request.user
        return super().form_valid(form)


class ProyectoUpdateView(ProyectoFormularioMixin, UpdateView):
    success_message = "Cambios guardados en «%(nombre)s»."

    def get_queryset(self):
        return Proyecto.objects.filter(propietario=self.request.user)


class ProyectoDeleteView(LoginRequiredMixin, SuccessMessageMixin, DeleteView):
    template_name = "proyectos/proyecto_confirm_delete.html"
    context_object_name = "proyecto"
    success_url = reverse_lazy("proyectos:lista")

    def get_queryset(self):
        return proyectos_con_avance(self.request.user)

    def get_success_message(self, cleaned_data):
        return f"Proyecto «{self.object.nombre}» eliminado."


class TareaCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    form_class = TareaForm
    template_name = "proyectos/tarea_form.html"
    success_message = "Tarea «%(titulo)s» agregada."

    @cached_property
    def proyecto(self):
        return get_object_or_404(Proyecto, pk=self.kwargs["proyecto_pk"], propietario=self.request.user)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["proyecto"] = self.proyecto
        return kwargs

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto["proyecto"] = self.proyecto
        return contexto

    def get_success_url(self):
        return self.proyecto.get_absolute_url()


class TareaDelUsuarioMixin(LoginRequiredMixin):
    def get_queryset(self):
        return tareas_de(self.request.user)

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto["proyecto"] = self.object.proyecto
        return contexto

    def get_success_url(self):
        return self.object.proyecto.get_absolute_url()


class TareaUpdateView(TareaDelUsuarioMixin, SuccessMessageMixin, UpdateView):
    form_class = TareaForm
    template_name = "proyectos/tarea_form.html"
    success_message = "Cambios guardados en «%(titulo)s»."


class TareaDeleteView(TareaDelUsuarioMixin, SuccessMessageMixin, DeleteView):
    template_name = "proyectos/tarea_confirm_delete.html"
    context_object_name = "tarea"

    def get_success_message(self, cleaned_data):
        return f"Tarea «{self.object.titulo}» eliminada."


class TareaAlternarView(LoginRequiredMixin, View):
    http_method_names = ["post"]

    def post(self, request, pk):
        tarea = get_object_or_404(tareas_de(request.user), pk=pk)
        tarea.completada = not tarea.completada
        tarea.save(update_fields=["completada", "actualizada"])
        if tarea.completada:
            messages.success(request, f"«{tarea.titulo}» quedó completada.")
        else:
            messages.info(request, f"«{tarea.titulo}» volvió a pendientes.")
        destino = request.POST.get("siguiente", "")
        if not url_has_allowed_host_and_scheme(destino, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
            destino = tarea.proyecto.get_absolute_url()
        return HttpResponseRedirect(destino)


class MisTareasView(LoginRequiredMixin, ListView):
    template_name = "proyectos/tarea_list.html"
    context_object_name = "tareas"
    paginate_by = 15
    filtros = {
        "pendientes": ("Pendientes", Q(completada=False)),
        "vencidas": ("Vencidas", None),
        "completadas": ("Completadas", Q(completada=True)),
        "todas": ("Todas", Q()),
    }

    def get_queryset(self):
        self.filtro = self.request.GET.get("filtro", "pendientes")
        if self.filtro not in self.filtros:
            self.filtro = "pendientes"
        tareas = tareas_de(self.request.user)
        if self.filtro == "vencidas":
            return tareas.filter(completada=False, fecha_limite__lt=timezone.localdate())
        return tareas.filter(self.filtros[self.filtro][1])

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto["filtro_actual"] = self.filtro
        contexto["opciones_filtro"] = [(clave, datos[0]) for clave, datos in self.filtros.items()]
        return contexto
