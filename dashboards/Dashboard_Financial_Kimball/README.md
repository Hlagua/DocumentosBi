# Dashboard_Financial_Kimball (Power BI Project)

Fuente: SQL Server `DM_Financial_Kimball_v2`. Generado con `python scripts/30_generar_powerbi_pbip.py`.

### Cómo abrirlo
1. Ejecuta antes `sql/04_Vistas_PowerBI_Kimball.sql` en la base (crea las 2 vistas del modelo).
2. Doble clic en `Dashboard_Financial_Kimball.pbip` (Power BI Desktop).
3. Si tu servidor no es `(localdb)\MSSQLLocalDB`: *Transformar datos → Editar parámetros* → `ServidorSQL`.
4. *Inicio → Actualizar*. Comprueba las cifras de control de la guía 07 (sección 9.3).

### Ajustes finales en Power BI Desktop (≈ 5 minutos)
Estos pasos no se pueden guardar de forma fiable en el archivo del proyecto; hazlos una vez y guarda (Ctrl+S):
1. **Drill-through:** en la página *D1 Detalle Distrito*, arrastra `Dim_Distrito[nombre_distrito]` al campo *Obtener detalles* del panel
   Visualizaciones. En *D2 Ficha Cliente 360*, arrastra `Dim_Cliente[Cliente]`. Después, clic derecho en cada pestaña D1/D2 → *Ocultar página*.
2. **Barras de error** (panel *Análisis* de cada gráfico → *Barras de error* → límites superior/inferior):
   - P1 y P2 tasa de mora → `Mora Limite Superior` / `Mora Limite Inferior`
   - P2 monto promedio → `Prestamo Limite Superior` / `Prestamo Limite Inferior`
   - P4 ticket promedio → `Transaccion Limite Superior` / `Transaccion Limite Inferior`
   - P6 incumplimiento por edad → `Incumplimiento Limite Superior` / `Incumplimiento Limite Inferior`
3. **Tema de colores:** *Vista → Temas → Buscar temas* → `tema_financial.json` (esta carpeta).
4. **Treemap (P2):** *Formato → Colores → fx* → degradado por `Tasa Mora Vigente` (blanco → naranja).
5. **Top 10 (P2, P3):** en el gráfico de distritos, panel *Filtros* → `Dim_Distrito[nombre_distrito]` → *N superior* = 10 por la medida del eje Y.
6. **Línea de referencia (P3):** *Análisis → Línea constante* = 0.5238 en el ratio de absorción por región.
