# Dashboard_Financial_Mongo (Power BI Project)

Fuente: MongoDB `Financial` (localhost:27017) mediante el conector `scripts/26_powerbi_mongo_dashboard.py`,
incrustado en la consulta compartida `MongoFinancial`. Generado con `python scripts/30_generar_powerbi_pbip.py`.

### Cómo abrirlo
1. MongoDB en ejecución con la base `Financial` cargada (script 22/23 o `Financial_mongo_dump.gz`).
2. *Archivo → Opciones → Scripts de Python*: selecciona el Python que tiene `pymongo` y `pandas`.
3. Doble clic en `Dashboard_Financial_Mongo.pbip` → *Inicio → Actualizar*. Acepta el aviso de privacidad del script de Python.
4. Comprueba las cifras de control de la guía 07 (sección 9.3): deben ser idénticas a las de Kimball.

### Ajustes finales en Power BI Desktop (≈ 5 minutos)
Estos pasos no se pueden guardar de forma fiable en el archivo del proyecto; hazlos una vez y guarda (Ctrl+S):
1. **Drill-through:** en la página *D1 Detalle Distrito*, arrastra `m_distritos[nombre_distrito]` al campo *Obtener detalles* del panel
   Visualizaciones. En *D2 Ficha Cliente 360*, arrastra `m_clientes[cliente]`. Después, clic derecho en cada pestaña D1/D2 → *Ocultar página*.
2. **Barras de error** (panel *Análisis* de cada gráfico → *Barras de error* → límites superior/inferior):
   - P1 y P2 tasa de mora → `Mora Limite Superior` / `Mora Limite Inferior`
   - P2 monto promedio → `Prestamo Limite Superior` / `Prestamo Limite Inferior`
   - P4 ticket promedio → `Transaccion Limite Superior` / `Transaccion Limite Inferior`
   - P6 incumplimiento por edad → `Incumplimiento Limite Superior` / `Incumplimiento Limite Inferior`
3. **Tema de colores:** *Vista → Temas → Buscar temas* → `tema_financial.json` (esta carpeta).
4. **Treemap (P2):** *Formato → Colores → fx* → degradado por `Tasa Mora Vigente` (blanco → naranja).
5. **Top 10 (P2, P3):** en el gráfico de distritos, panel *Filtros* → `m_distritos[nombre_distrito]` → *N superior* = 10 por la medida del eje Y.
6. **Línea de referencia (P3):** *Análisis → Línea constante* = 0.5238 en el ratio de absorción por región.
