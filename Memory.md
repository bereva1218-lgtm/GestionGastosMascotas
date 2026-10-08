# Memory

Bitácora del proceso de construcción de la aplicación. Cada entrada indica qué
se hizo, qué se decidió y por qué, para que cualquier persona pueda continuar.
Agregar las entradas nuevas al final.

## Cómo levantar el proyecto

Django 6.1 necesita **Python 3.12 o superior**.

```bash
python -m venv venv            # o: uv venv venv --python 3.12
venv\Scripts\activate          # Windows
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver     # http://127.0.0.1:8000/admin/
python manage.py test
```

## Registro

### 2026-10-08 — Proyecto base y documentación

- Proyecto Django inicial con SQLite.
- Documentación funcional en `Context/` (requisitos, módulos, reglas de negocio).
- `CLAUDE.md` con la guía para trabajar con Claude Code.

### 2026-10-08 — Arquitectura y modelos

- Arquitectura documentada en [`Context/Arquitectura.md`](Context/Arquitectura.md).
- Aplicación de dominio `mascotas` con los modelos `Mascota`, `CategoriaGasto`,
  `Gasto` y `Medicamento`, registrados en el administrador.
- Migración `0002_categorias_iniciales` crea Medicamentos, Comida y Juguetes.
- Configuración regional: `es-co`, zona horaria `America/Bogota`.
- Pruebas de reglas de negocio en `mascotas/tests.py` (4 pruebas, todas pasan).

Decisiones:

- **Una sola app** (`mascotas`) para todo el dominio: el proyecto es pequeño y
  las entidades están muy relacionadas.
- **Retirar ≠ borrar**: las mascotas tienen el campo `activa`, y los gastos y
  medicamentos usan `on_delete=PROTECT` para no perder el historial financiero.
- **`valor_total` calculado** en `Gasto.save()`, no lo escribe el usuario.
- **Valores positivos** validados dos veces: en formularios (`MinValueValidator`)
  y en la base de datos (`CheckConstraint`).
- `cantidad` es decimal para permitir compras por peso (por ejemplo 1.5 kg de comida).

## Próximos pasos

1. Formularios (`ModelForm`) para mascotas, gastos y medicamentos.
2. Vistas CRUD con login obligatorio, filtradas por `request.user`.
3. Plantillas HTML + CSS y mensajes de confirmación o error.
4. Filtros de gastos por mascota, categoría y rango de fechas.
5. Reportes: totales por mascota, por categoría y por mes.
6. Registro e inicio de sesión de usuarios.
