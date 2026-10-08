# Arquitectura

## Estilo

Monolito Django con el patrón **MTV** (Modelo – Plantilla – Vista):

```text
Navegador ──HTTP──> urls.py ──> Vista ──> Formulario (validación)
                                  │              │
                                  ▼              ▼
                             Plantilla        Modelo ──ORM──> SQLite
                             (HTML+CSS)
```

- **Modelos** (`mascotas/models.py`): entidades y reglas de negocio que deben
  cumplirse siempre (cálculo del total, valores positivos, protección del
  historial).
- **Formularios**: validación de lo que escribe el usuario y mensajes de error.
- **Vistas**: autenticación, filtrado por `request.user` y mensajes de
  confirmación con el framework `messages`.
- **Plantillas**: interfaz HTML con CSS.
- **Administrador de Django**: gestión interna de los datos.

## Estructura

```text
gestion_gastos_mascotas/   Configuración del proyecto (settings, urls raíz)
mascotas/                  Aplicación de dominio: mascotas, gastos,
                           medicamentos y reportes
  models.py                Mascota, CategoriaGasto, Gasto, Medicamento
  admin.py                 Registro en el administrador
  migrations/              Esquema + categorías iniciales (0002)
  tests.py                 Pruebas de reglas de negocio
Context/                   Documentación funcional
```

Se usa **una sola aplicación** de dominio porque las entidades están muy
relacionadas y el proyecto es pequeño. Si un módulo crece (por ejemplo,
reportes), se puede separar en su propia aplicación.

Los usuarios usan el modelo `User` incluido en `django.contrib.auth`.

## Modelo de datos

```text
User 1 ─── N Mascota 1 ─── N Gasto N ─── 1 CategoriaGasto
                 └────── N Medicamento
```

| Entidad | Campos principales |
|---|---|
| Mascota | usuario, nombre, especie (por defecto `Gato`), raza, sexo, fecha_nacimiento, peso, color, estado_salud, observaciones, activa |
| CategoriaGasto | nombre (único) |
| Gasto | mascota, categoria, producto, fecha, cantidad, valor_unitario, valor_total, proveedor, notas |
| Medicamento | mascota, nombre, dosis, frecuencia, fecha_inicio, fecha_fin, observaciones |

## Cómo se cumplen las reglas de negocio

| Regla | Implementación |
|---|---|
| Una mascota pertenece a un usuario | `Mascota.usuario` (FK obligatoria) |
| Un gasto pertenece a una mascota y una categoría | FKs obligatorias en `Gasto` |
| Categorías iniciales | Migración `0002_categorias_iniciales` |
| Total = cantidad × valor unitario | `Gasto.save()` calcula `valor_total` (no editable) |
| Cantidad y valores > 0 | Validadores (formularios) + `CheckConstraint` (base de datos) |
| Retirar una mascota no borra su historial | `Mascota.activa=False`; FKs con `PROTECT` impiden borrar mascotas con gastos o medicamentos |
| Fecha fin ≥ fecha inicio del medicamento | `CheckConstraint` en `Medicamento` |
| Cada usuario ve solo sus registros | Pendiente: vistas con `LoginRequiredMixin` y consultas filtradas por `request.user` |

## Pendiente

Formularios, vistas CRUD, plantillas, filtros, reportes y autenticación.
El avance se registra en [`Memory.md`](../Memory.md).
