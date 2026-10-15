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

Aplicación funcional: registro e inicio de sesión, CRUD de mascotas, gastos y
medicamentos, filtros con total filtrado y reportes. Cada usuario ve solo sus
registros. La entrega del parcial 2 de TPA (TDD) está en
[entrega/Parcial2_TDD.md](entrega/Parcial2_TDD.md). Ver [Memory](Memory.md).

## Ejecución local

Requiere Python 3.12 o superior.

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py datos_demo     # opcional: datos de prueba
python manage.py runserver      # http://127.0.0.1:8000/
python manage.py test
```