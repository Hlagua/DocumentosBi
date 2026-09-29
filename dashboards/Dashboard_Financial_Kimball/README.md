# Dashboard_Financial_Kimball (Power BI Project)

Fuente: SQL Server `DM_Financial_Kimball_v2`. Diseño: Guía 07 v4. Generado con `python scripts/30_generar_powerbi_pbip.py`.

### Cómo abrirlo
1. La base debe estar cargada (scripts 31, 34 y 42) y con la vista de `sql/04_Vistas_PowerBI_Kimball.sql`.
2. Doble clic en `Dashboard_Financial_Kimball.pbip` (Power BI Desktop).
3. Si tu servidor no es `(localdb)\MSSQLLocalDB`: *Transformar datos → Editar parámetros* → `ServidorSQL`.
4. *Inicio → Actualizar* y compara con las cifras de control.

### Cifras de control (sin filtros; deben coincidir en Kimball y MongoDB)
| KPI | Valor |
| :--- | ---: |
| Préstamos / en mora (D) | 682 / 45 |
| Tasa de mora vigente · incumplimiento | 10.04% · 13.25% |
| Cartera vigente · saldo neto al cierre | $80.30M · $197.14M |
| Absorción vigente (ref. cartera total) | 40.73% (52.38%) |
| Cuentas en sobregiro al cierre · cuentas con índice > 0.5 | 39 · 47 |
| Volumen · movimientos | $6.26bn · 1,056,320 |
| Impago banda Baja · Alta | 2.92% · 23.26% |

### Cómo lo usa el gerente
* **Panel izquierdo (en todas las páginas):** navegación a Inicio, P1–P6 y R1–R3, y los filtros **Año**, **Zona**
  (macro-región › región › distrito) y **Segmento de edad**. Están sincronizados: lo que elija sigue activo al
  cambiar de página.
* **Clic en un gráfico:** filtra los demás gráficos de esa misma página (comportamiento estándar de Power BI).
* **Clic derecho en un cliente o distrito → Obtener detalles:** abre la ficha D2 (cliente) o D1 (distrito)
  **con todos los filtros aplicados**; el botón *Atrás* vuelve a la página de origen. D1 y D2 están ocultas en
  las pestañas porque solo tienen sentido para un cliente o distrito concreto.

### Ya configurado desde el código (no hay que tocarlo)
Tema Okabe–Ito incrustado; drill-through de D1 (`Dim_Distrito[nombre_distrito]`) y D2 (`Dim_Cliente[Cliente]`) manteniendo los filtros;
filtros sincronizados; color por tasa de mora en el treemap de P2; semáforo del índice de saturación en la
dispersión de P5; mapas de calor en las matrices de P1, P4, R1 y R3; colores de estados, bandas y modelos.

### Ajustes opcionales en Power BI Desktop (el formato `report.json` no los guarda de forma fiable)
1. **Árbol de descomposición (P2):** clic en **+** → región → distrito → cliente (o *Valor alto* en cada nivel).
2. **Barras de error** (*Análisis → Barras de error*): P1 y P2 → `Mora Wilson Inferior/Superior`;
   P4 → `Ticket Limite Inferior/Superior`; P6 y R2 → `Impago Wilson Inferior/Superior`; P6 edad →
   `Incumplimiento Wilson Inferior/Superior`. Los mismos límites ya aparecen en el tooltip de cada gráfico.
3. **Dispersión (P5):** *Análisis → Sombreado de simetría* = activado.
4. **Múltiplos pequeños (P4):** mover la categoría de *Leyenda* a *Múltiplos pequeños* en el gráfico de volumen.
5. **Tablas:** barras de datos en la tasa de P2; *Mostrar elementos sin datos* en el estado de la matriz de P1.
6. Si algún combinado con referencia ("Banco") muestra un eje secundario: *Formato → Eje Y secundario → Desactivado*.
