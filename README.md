# Gestión de gastos de mascotas

Sistema web para registrar las características de una o varias mascotas y
controlar los gastos relacionados con su cuidado. El alcance inicial está
enfocado en gatos, pero el modelo permite agregar otras mascotas en el futuro.

## Estructura de la documentación

- [Contexto](Context/README.md): equipo, propósito, tecnologías, componentes,
	requisitos y funcionalidades iniciales.
- [Arquitectura](Context/Arquitectura.md): capas, modelo de datos y cómo se
	cumplen las reglas de negocio.
- [Memory](Memory.md): bitácora del proceso y próximos pasos.
- [Aplicación](Context/Aplicacion.md): propuesta de módulos, datos principales
	y orden recomendado de implementación.

## Estado actual

Aplicación `mascotas` con los modelos, migraciones (incluye las categorías
iniciales), administrador y pruebas de reglas de negocio. Faltan vistas,
plantillas y reportes; ver [Memory](Memory.md).

## Ejecución local

Requiere Python 3.12 o superior.

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```