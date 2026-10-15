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
python manage.py datos_demo    # opcional: usuarios demo/otro con datos
python manage.py runserver     # http://127.0.0.1:8000/
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

### 2026-10-09 — Vistas de práctica (`gastoMascota`)

- Un compañero agregó la app `gastoMascota` con vistas de prueba: `/` (inicio),
  `/cm/` (mensaje) y `/objeto/` (objeto de ejemplo).
- Las plantillas están en `gestion_gastos_mascotas/templates/`, configurada en
  `TEMPLATES['DIRS']`.

### 2026-10-12 — Integración de ramas

- Se integraron los cambios de `gastoMascota` con la app `mascotas`. Las dos
  quedan en `INSTALLED_APPS`; pruebas y páginas funcionan.
- Pendiente decidir en equipo: unificar las vistas en `mascotas` o mantener
  `gastoMascota` para la interfaz.

### 2026-10-15 — Parcial 2 TPA (TDD) y aplicación completa

- Repositorio git inicializado; cada fase quedó en su propio commit.
- **Parcial:** regla `total_mensual(gastos, anio, mes)` en `mascotas/reglas.py`
  con 5 pruebas en `mascotas/test_reglas.py`, escritas antes del código.
  Ciclo rojo → verde → refactor con evidencias en `entrega/evidencias/` y hoja
  de entrega en `entrega/Parcial2_TDD.md`.
- **Refactor (responsabilidad única):** el cálculo del total salió de
  `Gasto.save()` a `reglas.calcular_valor_total()`.
- Se retiró la app de práctica `gastoMascota`; la interfaz vive en `mascotas`.
- `Mascota.usuario` pasa a `PROTECT` (migración 0003): borrar un usuario no
  debe borrar historial financiero.
- Registro e inicio de sesión (`/registro/`, `/cuentas/login/`).
- CRUD de mascotas (con retirar/reactivar), gastos y medicamentos; filtros de
  gastos por mascota, categoría y rango con total filtrado; reportes por
  mascota, categoría, mes y productos; el inicio muestra el total del mes con
  `total_mensual`.
- Comando `datos_demo` para probar localmente.
- 44 pruebas, todas pasan.

Decisiones:

- **Reglas puras en `reglas.py`** y **consultas en `reportes.py`**: separar
  cálculo, consulta y presentación facilita probar y reutilizar.
- **Eliminar vs. retirar:** eliminar solo se permite sin historial; si hay
  gastos o medicamentos se muestra un error y se sugiere retirar.
- Los formularios solo ofrecen mascotas activas del usuario; el filtro de
  gastos incluye las retiradas para consultar su historial.
- Las pruebas crean usuarios sin contraseña y usan `force_login` (sin el costo
  de calcular hashes).

### 2026-10-15 — Rediseño profesional del frontend

- Sistema de diseño documentado en `Context/DisenoUI.md`: tokens con modo
  claro/oscuro, barra lateral, componentes (indicadores, tablas apilables,
  formularios por secciones, insignias, gráficos en CSS) e iconos SVG.
- Librería de plantillas `mascotas/templatetags/ui.py` (`icono`, `moneda`,
  `edad`, `campo`, `clase_categoria`, `tono`…).
- Panel de inicio con tendencia de 6 meses (reutiliza `total_mensual`),
  variación frente al mes anterior, distribución por categoría y tratamientos.
- Nuevas reglas puras con pruebas: `variacion_porcentual`, `ultimos_meses`,
  `calcular_edad`; propiedades `Medicamento.activo` y `dias_restantes`.
- Mascotas con búsqueda y filtro por estado; gastos con búsqueda y paginación;
  reportes con rangos predefinidos e impresión; páginas 404/403/500 propias.
- Las vistas se rediseñaron por grupos (acceso, mascotas, formularios, gastos,
  medicamentos, reportes) con revisión cruzada; `test_ui.py` recorre todas las
  páginas como prueba de humo.

Decisiones:

- **Sin librerías de frontend:** CSS propio con tokens y gráficos con CSS
  (`widthratio`), para no depender de internet ni de un empaquetador. Solo la
  fuente Inter se carga de Google Fonts (con respaldo a fuentes del sistema).
- En los indicadores de gasto, **subir es rojo y bajar es verde**.

## Próximos pasos

1. Edición de datos básicos del usuario (módulo de usuarios).
2. Evolución posterior: alertas de medicamentos por terminar, presupuesto
   mensual por mascota, adjuntar facturas y exportar reportes a CSV/PDF.
3. Antes de desplegar: mover `SECRET_KEY` a variable de entorno y `DEBUG=False`.
