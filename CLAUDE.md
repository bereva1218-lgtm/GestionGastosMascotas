# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Django web app for tracking pet characteristics and the expenses of caring for them (medicines, food, toys). Initial scope is cats, but the model must allow other species. All docs, requirements and (by convention) domain naming are in **Spanish** — keep models, fields, templates and user messages in Spanish.

Current state: domain app `mascotas` is functional — models, migrations (0002 seeds categories, 0003 makes `Mascota.usuario` PROTECT), pure rules in `reglas.py`, forms, CBV views, templates, auth (`/registro/`, `/cuentas/login/`), reports (`reportes.py`) and tests (`tests.py`, `test_*.py`). `entrega/` holds the TPA parcial 2 (TDD) deliverable and evidence. Architecture: `Context/Arquitectura.md`. Progress log: `Memory.md` — append an entry after each significant change. The functional spec lives in `Context/` and should be read before implementing features:

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
python manage.py datos_demo                     # dev data: users demo/otro (password in the command file)
python manage.py test                           # all tests
python manage.py test mascotas.tests.ReglasDeNegocioTests.test_total_es_cantidad_por_valor_unitario  # single test
```

No linter/formatter is configured.

## Architecture

Project package: `gestion_gastos_mascotas/` (settings, root `urls.py` → `admin/`, `cuentas/` = `django.contrib.auth.urls`, `''` = `mascotas.urls`). Everything else lives in the single domain app `mascotas/` (namespace `mascotas`):

- `reglas.py` — pure business rules, no DB (`calcular_valor_total`, `total_mensual`); `Gasto.save()` delegates to it.
- `reportes.py` — aggregations over an already user-scoped `Gasto` queryset.
- `views.py` — CBVs; `DelUsuarioMixin` = login required + `get_queryset` filtered by `campo_usuario` (`usuario` or `mascota__usuario`), so foreign records 404. `FormConUsuarioMixin` passes `usuario` to forms.
- `forms.py` — `GastoForm`/`MedicamentoForm` take `usuario=` and limit `mascota` to the user's active pets.
- Templates in `mascotas/templates/` (`base.html` = app shell with sidebar, `base_publico.html` = login/registro, `includes/` = icon sprite, form field, messages). Design system and UI rules: `Context/DisenoUI.md` — read it before touching templates. All colors come from tokens in `mascotas/static/mascotas/estilos.css` (light/dark); page-specific CSS goes in `static/mascotas/css/<pagina>.css`, tokens only.
- `templatetags/ui.py` (`{% load ui %}`) — `icono`, `moneda`, `fecha_larga`, `porcentaje`, `icono_categoria`, `insignia_medicamento`, `campo` (form field), etc. Use them instead of re-implementing formatting in templates.
- `test_ui.py` smoke-tests every page; `test_integracion_ui.py` covers the presentation-facing context and filters.

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

Remaining work: user profile editing and the "evolución posterior" items in `Context/funcionalidades.md`. Tests create users without a password and use `force_login` (avoids slow hashing).
