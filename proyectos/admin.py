from django.contrib import admin, messages
from django.db.models import Count, Q

from .models import Proyecto, Tarea

admin.site.site_header = "Gestor de Proyectos · Evelyn Álvarez"
admin.site.site_title = "Administración | Evelyn Álvarez"
admin.site.index_title = "Panel de administración"


class TareaInline(admin.TabularInline):
    model = Tarea
    extra = 0
    fields = ("titulo", "prioridad", "fecha_limite", "completada")
    show_change_link = True


@admin.register(Proyecto)
class ProyectoAdmin(admin.ModelAdmin):
    list_display = (
        "nombre",
        "propietario",
        "estado",
        "fecha_inicio",
        "fecha_limite",
        "cantidad_tareas",
        "porcentaje_avance",
    )
    list_editable = ("estado",)
    list_filter = ("estado", "fecha_inicio", "propietario")
    search_fields = ("nombre", "descripcion", "propietario__username", "propietario__email")
    date_hierarchy = "fecha_inicio"
    autocomplete_fields = ("propietario",)
    readonly_fields = ("creado", "actualizado")
    list_select_related = ("propietario",)
    inlines = [TareaInline]
    actions = ["marcar_en_curso", "marcar_finalizados"]
    fieldsets = (
        (None, {"fields": ("propietario", "nombre", "descripcion")}),
        ("Planificación", {"fields": ("estado", "fecha_inicio", "fecha_limite")}),
        ("Registro", {"fields": ("creado", "actualizado"), "classes": ("collapse",)}),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            num_tareas=Count("tareas"),
            num_completadas=Count("tareas", filter=Q(tareas__completada=True)),
        )

    @admin.display(description="Tareas", ordering="num_tareas")
    def cantidad_tareas(self, obj):
        return obj.num_tareas

    @admin.display(description="Avance")
    def porcentaje_avance(self, obj):
        return f"{obj.avance} %"

    @admin.action(description="Marcar como en curso")
    def marcar_en_curso(self, request, queryset):
        total = queryset.update(estado=Proyecto.Estado.EN_CURSO)
        self.message_user(request, f"{total} proyecto(s) en curso.", messages.SUCCESS)

    @admin.action(description="Marcar como finalizados")
    def marcar_finalizados(self, request, queryset):
        total = queryset.update(estado=Proyecto.Estado.FINALIZADO)
        self.message_user(request, f"{total} proyecto(s) finalizado(s).", messages.SUCCESS)


@admin.register(Tarea)
class TareaAdmin(admin.ModelAdmin):
    list_display = ("titulo", "proyecto", "responsable", "prioridad", "fecha_limite", "completada", "esta_vencida")
    list_editable = ("prioridad", "completada")
    list_filter = ("completada", "prioridad", "fecha_limite", "proyecto__estado")
    search_fields = ("titulo", "descripcion", "proyecto__nombre", "proyecto__propietario__username")
    autocomplete_fields = ("proyecto",)
    list_select_related = ("proyecto", "proyecto__propietario")
    readonly_fields = ("creada", "actualizada")
    actions = ["marcar_completadas", "marcar_pendientes"]

    @admin.display(description="Responsable", ordering="proyecto__propietario__username")
    def responsable(self, obj):
        return obj.proyecto.propietario

    @admin.display(description="Vencida", boolean=True)
    def esta_vencida(self, obj):
        return obj.vencida

    @admin.action(description="Marcar como completadas")
    def marcar_completadas(self, request, queryset):
        total = queryset.update(completada=True)
        self.message_user(request, f"{total} tarea(s) completada(s).", messages.SUCCESS)

    @admin.action(description="Marcar como pendientes")
    def marcar_pendientes(self, request, queryset):
        total = queryset.update(completada=False)
        self.message_user(request, f"{total} tarea(s) pendiente(s).", messages.INFO)
