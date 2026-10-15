# Segundo parcial TPA — TDD y organización del código

**Proyecto:** Gestión de gastos de mascotas · Universidad de San Buenaventura Cali · 2026B
**Equipo:** Valeria Becerra Rendón, Miguel Ángel Rodríguez Bravo, Jhon Ricky Chito Melo,
Nicolás Navarro J, Daniel Victoria, Juan Esteban Salazar.

## 1. Regla elegida: total mensual de gastos

Dado un conjunto de gastos, un año y un mes, la función devuelve cuánto se gastó
en ese mes. Responde al requisito funcional 5 ("calcular el valor total de los
gastos filtrados") y al resumen mensual del módulo de reportes.

```python
total_mensual(gastos, anio, mes) -> Decimal
```

| | Descripción |
|---|---|
| **Entradas** | `gastos`: lista de gastos, cada uno con `fecha` (date) y `valor_total` (Decimal). `anio`: entero. `mes`: entero de 1 a 12. |
| **Salida** | `Decimal` con la suma de `valor_total` de los gastos cuya fecha está en ese mes y año. `Decimal('0')` si no hay ninguno. |
| **Error** | `ValueError` si `mes` no está entre 1 y 12. |

- Función: [`mascotas/reglas.py`](../mascotas/reglas.py)
- Pruebas: [`mascotas/test_reglas.py`](../mascotas/test_reglas.py)

## 2. Casos probados

| # | Prueba | Entrada | Esperado | Tipo |
|---|---|---|---|---|
| 1 | `test_suma_solo_los_gastos_del_mes_pedido` | 2 gastos de oct-2026 (30 000 y 12 500,50) y 1 de sep-2026; mes 10/2026 | `42500.50` | Normal |
| 2 | `test_sin_gastos_el_total_es_cero` | Lista vacía | `0` | Vacío |
| 3 | `test_incluye_primer_y_ultimo_dia_y_excluye_mes_vecino` | 31-dic-2025, 1-ene, 31-ene y 1-feb-2026; mes 1/2026 | `300` (solo 1 y 31 de enero) | Valor límite |
| 4 | `test_mes_fuera_de_rango_es_invalido` | `mes = 0` y `mes = 13` | `ValueError` | Dato inválido |
| 5 | `test_mismo_mes_de_otro_anio_no_se_suma` | 15-oct-2025 y 15-oct-2026; mes 10/2026 | `250` | Límite (año) |

Las pruebas usan `SimpleTestCase` y objetos simples: no necesitan base de datos y
corren en milisegundos.

## 3. Ciclo TDD y evidencias

| Fase | Commit | Evidencia | Resultado |
|---|---|---|---|
| Prueba inicial (rojo) | `9c133c0` test: pruebas de total_mensual (rojo) | [`01_rojo.txt`](evidencias/01_rojo.txt) | 5 pruebas, `FAILED (errors=6)`; la función era un stub `NotImplementedError` |
| Implementación (verde) | `d6166cb` feat: total_mensual (verde) | [`02_verde.txt`](evidencias/02_verde.txt) | `Ran 5 tests … OK` |
| Refactorización | `1571a3b` refactor: reglas puras separadas del modelo | [`03_refactor.txt`](evidencias/03_refactor.txt) | Suite completa de la app: `Ran 9 tests … OK` |

Ver la secuencia con `git log --oneline`.

## 4. Mejora de organización: responsabilidad única

**Antes:**
- El cálculo `valor_total = cantidad × valor_unitario` vivía dentro de
  `Gasto.save()`. El modelo hacía dos cosas: calcular la regla y guardar en la
  base de datos. Para probar el cálculo había que crear un registro.
- La primera versión de `total_mensual` (fase verde) validaba el mes, filtraba
  por fecha y sumaba, todo en el mismo bloque.

**Después** (`mascotas/reglas.py`):

| Función | Única responsabilidad |
|---|---|
| `calcular_valor_total(cantidad, valor_unitario)` | Calcular el total de un gasto |
| `validar_mes(mes)` | Rechazar meses fuera de 1..12 |
| `es_del_mes(fecha, anio, mes)` | Decidir si una fecha pertenece al mes |
| `total_mensual(gastos, anio, mes)` | Componer las anteriores y sumar |

`Gasto.save()` ahora solo delega el cálculo y persiste:

```python
def save(self, *args, **kwargs):
    self.valor_total = calcular_valor_total(self.cantidad, self.valor_unitario)
    super().save(*args, **kwargs)
```

**Beneficios:** las reglas se prueban sin base de datos, cada función se lee en
una línea, y las vistas de reportes reutilizan las mismas funciones en lugar de
repetir la lógica. La prueba existente `test_total_es_cantidad_por_valor_unitario`
siguió pasando, lo que confirma que el refactor no cambió el comportamiento.

## 5. Cómo ejecutar

```bash
venv\Scripts\activate
python manage.py test mascotas.test_reglas -v 2
```
