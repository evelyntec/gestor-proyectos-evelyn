import django.core.validators
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Proyecto',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=120, validators=[django.core.validators.MinLengthValidator(3)], verbose_name='nombre')),
                ('descripcion', models.TextField(blank=True, verbose_name='descripción')),
                ('estado', models.CharField(choices=[('planificado', 'Planificado'), ('en_curso', 'En curso'), ('finalizado', 'Finalizado')], default='planificado', max_length=20, verbose_name='estado')),
                ('fecha_inicio', models.DateField(default=django.utils.timezone.localdate, verbose_name='fecha de inicio')),
                ('fecha_limite', models.DateField(blank=True, null=True, verbose_name='fecha límite')),
                ('creado', models.DateTimeField(auto_now_add=True, verbose_name='creado')),
                ('actualizado', models.DateTimeField(auto_now=True, verbose_name='actualizado')),
                ('propietario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='proyectos', to=settings.AUTH_USER_MODEL, verbose_name='propietario')),
            ],
            options={
                'verbose_name': 'proyecto',
                'verbose_name_plural': 'proyectos',
                'ordering': ['-actualizado'],
            },
        ),
        migrations.CreateModel(
            name='Tarea',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('titulo', models.CharField(max_length=150, validators=[django.core.validators.MinLengthValidator(3)], verbose_name='título')),
                ('descripcion', models.TextField(blank=True, verbose_name='descripción')),
                ('prioridad', models.CharField(choices=[('baja', 'Baja'), ('media', 'Media'), ('alta', 'Alta')], default='media', max_length=10, verbose_name='prioridad')),
                ('fecha_limite', models.DateField(blank=True, null=True, verbose_name='fecha límite')),
                ('completada', models.BooleanField(default=False, verbose_name='completada')),
                ('creada', models.DateTimeField(auto_now_add=True, verbose_name='creada')),
                ('actualizada', models.DateTimeField(auto_now=True, verbose_name='actualizada')),
                ('proyecto', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tareas', to='proyectos.proyecto', verbose_name='proyecto')),
            ],
            options={
                'verbose_name': 'tarea',
                'verbose_name_plural': 'tareas',
                'ordering': ['completada', models.OrderBy(models.F('fecha_limite'), nulls_last=True), '-creada'],
            },
        ),
        migrations.AddConstraint(
            model_name='proyecto',
            constraint=models.UniqueConstraint(fields=('propietario', 'nombre'), name='proyecto_unico_por_usuario'),
        ),
    ]
