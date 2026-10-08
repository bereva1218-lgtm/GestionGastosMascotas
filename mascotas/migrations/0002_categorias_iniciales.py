from django.db import migrations

CATEGORIAS = ['Medicamentos', 'Comida', 'Juguetes']


def crear_categorias(apps, schema_editor):
    CategoriaGasto = apps.get_model('mascotas', 'CategoriaGasto')
    for nombre in CATEGORIAS:
        CategoriaGasto.objects.get_or_create(nombre=nombre)


def borrar_categorias(apps, schema_editor):
    apps.get_model('mascotas', 'CategoriaGasto').objects.filter(nombre__in=CATEGORIAS).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('mascotas', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(crear_categorias, borrar_categorias),
    ]
