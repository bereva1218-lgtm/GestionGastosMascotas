# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Django web app for tracking pet characteristics and the expenses of caring for them (medicines, food, toys). Initial scope is cats, but the model must allow other species. All docs, requirements and (by convention) domain naming are in **Spanish** — keep models, fields, templates and user messages in Spanish.

Current state: domain app `mascotas` has models, migrations (0002 seeds categories), admin and business-rule tests; no forms/views/templates yet. Architecture: `Context/Arquitectura.md`. Progress log: `Memory.md` — append an entry after each significant change. The functional spec lives in `Context/` and should be read before implementing features:

- `Context/Entorno.md` — purpose, tech stack, components, numbered functional requirements.
- `Context/Modulos.md` — modules (usuarios, mascotas, gastos, medicamentos, reportes) and their features.
- `Context/funcionalidades.md` — MVP priorities and **business rules**.
- `Context/Aplicacion.md` — recommended implementation order and entity diagram.

When a change implements or alters a requirement, update the related `Context/` doc (team convention from `Context/Colaboradores.md`).

## Commands

```bash
python -m venv venv && venv\Scripts\activate   # Windows; needs Python >= 3.12 (Django 6.1); venv/ is gitignored
pip install -r requirements.txt
python manage.py runserver
python manage.py makemigrations && python manage.py migrate
python manage.py createsuperuser
python manage.py test                           # all tests
python manage.py test mascotas.tests.ReglasDeNegocioTests.test_total_es_cantidad_por_valor_unitario  # single test
```

No linter/formatter is configured.

## Architecture

Project package: `gestion_gastos_mascotas/` (settings, root `urls.py`). Domain models live in `mascotas/` (its urls not yet included from the root `urls.py`). `gastoMascota/` is a teammate's practice app with demo views (`/`, `/cm/`, `/objeto/`) wired directly in the root `urls.py`; its templates are in `gestion_gastos_mascotas/templates/` (`TEMPLATES.DIRS`). App templates use `APP_DIRS=True`.

Entities (`Context/Aplicacion.md`):

```text
Usuario 1 ─── N Mascota 1 ─── N Gasto N ─── 1 CategoriaGasto
                    └────── N Medicamento
```

Business rules that shape the models/views:

- A `Mascota` belongs to a user; every view must scope queries to `request.user` (users see only their own records) and require login.
- `Gasto` and `Medicamento` must have a `Mascota` (required FK); `Gasto` also requires a `CategoriaGasto` and a date.
- Initial categories: `Medicamentos`, `Comida`, `Juguetes` (data migration `0002_categorias_iniciales`).
- `valor_total = cantidad × valor_unitario` — computed in `Gasto.save()`, not user-entered.
- Quantities and monetary values must be > 0 — enforced by `MinValueValidator` and DB `CheckConstraint`.
- "Retiring" a pet must **not** delete its financial history → set `Mascota.activa=False`; `Gasto`/`Medicamento` FKs are `PROTECT`.
- Show a success/error message (Django `messages` framework) after every operation.
- Reports: totals per pet, per category, monthly, and by date range.

Remaining build order: forms/validation → CRUD views → filters and summaries → auth/permission scoping.
