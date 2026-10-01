from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.db.models import Count


admin.site.unregister(User)


@admin.register(User)
class UsuarioAdmin(UserAdmin):
    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "total_proyectos",
        "is_active",
        "is_staff",
        "date_joined",
    )
    list_filter = ("is_active", "is_staff", "is_superuser", "groups", "date_joined")
    search_fields = ("username", "first_name", "last_name", "email")
    ordering = ("-date_joined",)
    actions = ["activar_cuentas", "desactivar_cuentas", "dar_acceso_admin", "quitar_acceso_admin"]

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(num_proyectos=Count("proyectos"))

    @admin.display(description="Proyectos", ordering="num_proyectos")
    def total_proyectos(self, obj):
        return obj.num_proyectos

    @admin.action(description="Activar cuentas seleccionadas")
    def activar_cuentas(self, request, queryset):
        total = queryset.update(is_active=True)
        self.message_user(request, f"{total} cuenta(s) activada(s).", messages.SUCCESS)

    @admin.action(description="Desactivar cuentas seleccionadas")
    def desactivar_cuentas(self, request, queryset):
        total = queryset.exclude(pk=request.user.pk).update(is_active=False)
        self.message_user(request, f"{total} cuenta(s) desactivada(s).", messages.WARNING)

    @admin.action(description="Dar acceso al panel de administración")
    def dar_acceso_admin(self, request, queryset):
        total = queryset.update(is_staff=True)
        self.message_user(request, f"{total} usuario(s) ahora pueden entrar al panel.", messages.SUCCESS)

    @admin.action(description="Quitar acceso al panel de administración")
    def quitar_acceso_admin(self, request, queryset):
        total = queryset.exclude(pk=request.user.pk).filter(is_superuser=False).update(is_staff=False)
        self.message_user(request, f"{total} usuario(s) ya no pueden entrar al panel.", messages.WARNING)
