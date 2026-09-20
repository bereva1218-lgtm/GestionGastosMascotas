# Funcionalidades prioritarias

## Versión inicial

1. Registrar y administrar una o varias mascotas.
2. Registrar gastos de medicamentos, comida y juguetes.
3. Asociar cada gasto con una mascota.
4. Consultar el historial completo de gastos.
5. Filtrar por categoría y fecha.
6. Ver totales por mascota y categoría.
7. Registrar dosis y frecuencia de medicamentos.

## Reglas de negocio

- Una mascota pertenece a un usuario.
- Un gasto pertenece a una sola mascota y a una categoría.
- Las categorías iniciales son `Medicamentos`, `Comida` y `Juguetes`.
- El total del gasto se obtiene de `cantidad x valor unitario`.
- La fecha del gasto es obligatoria.
- La cantidad y los valores monetarios deben ser mayores que cero.
- Retirar una mascota no debe borrar automáticamente su historial financiero.

## Evolución posterior

- Alertas para medicamentos próximos a terminarse.
- Presupuesto mensual por mascota.
- Adjuntar facturas o fórmulas veterinarias.
- Exportar reportes a CSV o PDF.