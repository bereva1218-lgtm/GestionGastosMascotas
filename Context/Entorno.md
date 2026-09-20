# Entorno

## 1. Propósito

Crear una aplicación web que permita a una persona registrar una o varias
mascotas, guardar sus características y controlar los gastos de su cuidado.
El sistema debe facilitar la consulta del historial y el análisis del dinero
invertido en medicamentos, comida y juguetes para cada mascota.

## 2. Tecnologías base

- **Lenguaje:** Python.
- **Framework web:** Django.
- **Base de datos inicial:** SQLite.
- **Interfaz:** plantillas HTML de Django y CSS.
- **Control de versiones:** Git.
- **Entorno de ejecución:** entorno virtual de Python.

## 3. Componentes de la aplicación

- **Usuarios:** acceso y administración básica de la información.
- **Mascotas:** nombre, especie, raza, sexo, fecha de nacimiento, peso, color,
  estado de salud y observaciones.
- **Categorías de gasto:** medicamentos, comida y juguetes.
- **Registro de gastos:** producto, fecha, cantidad, valor unitario, valor
  total, proveedor, mascota relacionada y notas.
- **Seguimiento de medicamentos:** nombre, dosis, frecuencia, fechas de inicio
  y finalización, y observaciones veterinarias.
- **Consultas y reportes:** historial por mascota, categoría y periodo.

## 4. Requisitos funcionales iniciales

1. El sistema debe permitir registrar, consultar, editar y eliminar mascotas.
2. El sistema debe conservar las características de cada mascota y permitir
   administrar varias mascotas dentro de una misma cuenta.
3. El sistema debe registrar gastos de medicamentos, comida y juguetes.
4. Cada gasto debe quedar asociado a una mascota, una categoría y una fecha.
5. El sistema debe calcular el valor total de cada registro y de los gastos
   filtrados.
6. El sistema debe permitir consultar gastos por mascota, categoría y rango de
   fechas.
7. El sistema debe permitir registrar la información de uso de un medicamento.
8. El sistema debe validar que los valores monetarios y las cantidades sean
   positivos.
9. El sistema debe mostrar mensajes de confirmación o error después de cada
   operación.
10. El sistema debe proteger la información para que cada usuario consulte
    únicamente sus propios registros.