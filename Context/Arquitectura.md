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
  reglas.py                Reglas puras sin BD (valor total, total mensual)
  models.py                Mascota, CategoriaGasto, Gasto, Medicamento
  forms.py                 Formularios y filtros con validación
  views.py                 Vistas CRUD, inicio y reportes (login + filtro por usuario)
  reportes.py              Agregaciones: totales por mascota, categoría, mes, productos
  urls.py                  Rutas de la app (namespace `mascotas`)
  templates/, static/      Plantillas HTML y estilos CSS
  admin.py                 Registro en el administrador
  migrations/              Esquema, categorías iniciales (0002), usuario PROTECT (0003)
  management/commands/     `datos_demo`: datos de prueba para desarrollo
  tests.py, test_*.py      Pruebas de modelos, reglas, formularios, vistas y reportes
entrega/                   Parcial 2 TPA: hoja de entrega y evidencias del ciclo TDD
Context/                   Documentación funcional
```

### Capas y responsabilidades

- **`reglas.py`**: funciones puras con una sola responsabilidad
  (`calcular_valor_total`, `validar_mes`, `es_del_mes`, `total_mensual`).
  Se prueban sin base de datos y las usan el modelo y las vistas.
- **`reportes.py`**: consultas de resumen sobre un queryset ya filtrado por usuario.
- **Vistas**: `DelUsuarioMixin` exige sesión y filtra `get_queryset()` por el
  usuario actual; un registro ajeno responde 404.

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
| Una mascota pertenece a un usuario | `Mascota.usuario` (FK obligatoria, `PROTECT`) |
| Un gasto pertenece a una mascota y una categoría | FKs obligatorias en `Gasto` |
| Categorías iniciales | Migración `0002_categorias_iniciales` |
| Total = cantidad × valor unitario | `reglas.calcular_valor_total()`, usado por `Gasto.save()` (`valor_total` no editable) |
| Cantidad y valores > 0 | Validadores (formularios) + `CheckConstraint` (base de datos) |
| Retirar una mascota no borra su historial | `Mascota.activa=False`; FKs con `PROTECT` impiden borrar mascotas con gastos o medicamentos |
| Fecha fin ≥ fecha inicio del medicamento | `CheckConstraint` en `Medicamento` |
| Cada usuario ve solo sus registros | `DelUsuarioMixin` (login obligatorio + consultas filtradas por `request.user`); los formularios solo ofrecen mascotas propias |
| Mensaje tras cada operación | Framework `messages` (`SuccessMessageMixin` y `messages.error`) |
| Total de los gastos filtrados | `GastoFiltroForm` + `reportes.total()` |

## Pendiente

Funcionalidades de evolución posterior (`funcionalidades.md`): alertas de
medicamentos, presupuesto mensual, adjuntar facturas y exportar reportes.
El avance se registra en [`Memory.md`](../Memory.md).
