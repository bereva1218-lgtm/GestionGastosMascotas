# Gestión de gastos de mascotas

Sistema web para registrar las características de una o varias mascotas y
controlar los gastos relacionados con su cuidado. El alcance inicial está
enfocado en gatos, pero el modelo permite agregar otras mascotas en el futuro.

## Estructura de la documentación

- [Contexto](Context/README.md): equipo, propósito, tecnologías, componentes,
	requisitos y funcionalidades iniciales.
- [Aplicación](Context/Aplicacion.md): propuesta de módulos, datos principales
	y orden recomendado de implementación.

## Estado actual

El proyecto parte de una configuración base de Django con SQLite. La
documentación define el alcance antes de construir los modelos, vistas y
plantillas de la aplicación.

## Ejecución local

```bash
python manage.py runserver
```