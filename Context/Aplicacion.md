# Aplicación

La implementación deberá convertir los requisitos de `Context/` en modelos,
formularios, vistas y plantillas de Django.

## Orden recomendado

1. Crear la aplicación Django de dominio.
2. Definir los modelos `Mascota`, `CategoriaGasto`, `Gasto` y
   `Medicamento`.
3. Crear migraciones y registrar los modelos en el administrador.
4. Implementar formularios y validaciones.
5. Implementar las vistas de altas, consultas, edición y eliminación.
6. Añadir filtros y resúmenes de gastos.
7. Proteger las vistas con autenticación y verificar permisos por usuario.

## Entidades principales

```text
Usuario 1 ─── N Mascota 1 ─── N Gasto N ─── 1 CategoriaGasto
                    └────── N Medicamento
```

La relación con la mascota es obligatoria tanto para un gasto como para un
medicamento, porque el sistema debe poder explicar cuánto cuesta cuidar a cada
animal.