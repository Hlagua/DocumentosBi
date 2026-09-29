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

### Ajustes finales en Power BI Desktop (≈ 15 minutos, una sola vez; luego Ctrl+S)
El formato heredado `report.json` no guarda de forma fiable estas opciones; se configuran a mano:

1. **Tema:** ya viene incrustado (Okabe e Ito). Si no se aplicara: *Vista → Temas → Buscar temas* →
   `tema_financial.json` (esta carpeta). Los colores con significado (estados, bandas, alertas, propósitos)
   están fijados en cada visual.
2. **Drill-through:** en *D1 Distrito* arrastra `Dim_Distrito[nombre_distrito]` a *Obtener detalles*; en *D2 Cliente 360* arrastra
   `Dim_Cliente[Cliente]` **y** `Dim_Cuenta[Cuenta]` (P5 llega por cuenta; P2, P6 y D1 por cliente). Luego clic derecho en las
   pestañas D1 y D2 → *Ocultar página*.
3. **Árbol de descomposición (P2):** clic en **+** → `region` → **+** → `nombre_distrito` → **+** → `Cliente`
   (o *Valor alto* en cada nivel).
4. **Barras de error** (*Análisis → Barras de error*, límites superior/inferior):
   - P1 línea y P2 columnas de tasa de mora → `Mora Wilson Superior` / `Mora Wilson Inferior`
   - P4 ticket promedio → `Ticket Limite Superior` / `Ticket Limite Inferior`
   - P6 bandas → `Impago Wilson Superior/Inferior`; P6 edad → `Incumplimiento Wilson Superior/Inferior`
   (Los mismos límites ya están en el tooltip de cada gráfico.)
5. **Treemap (P2):** *Formato → Colores → fx* → degradado por `Tasa Mora Vigente`, mínimo `#FFFFFF`, máximo `#D55E00`.
6. **Dispersión (P5):** *Análisis → Sombreado de simetría* = activado. *Formato → Marcadores → Color → fx* →
   reglas por `Indice Saturacion`: > 1 → `#D55E00`, > 0.5 → `#E69F00`, resto `#7F7F7F`.
7. **Múltiplos pequeños (P4):** en el gráfico de líneas de volumen, mueve `categoria_analitica` de *Leyenda* a
   *Múltiplos pequeños* (un panel por categoría, sin colores).
8. **Formato condicional:** matrices de P1 y P4 → *Color de fondo* escala `#FFFFFF` → `#D55E00`; matriz de P1 →
   clic derecho en `Estado` → *Mostrar elementos sin datos*. Tabla de P2 → *Barras de datos* en `Tasa`.
   Tabla de P5 → *Iconos* en `Índice de saturación` (> 1 bermellón, > 0.5 naranja).
9. **Combinados con referencia (P2, P3, P6):** la línea "Banco" usa el mismo eje que las columnas (eje Y
   secundario desactivado). Si Power BI lo muestra en otra escala, *Formato → Eje Y secundario → Desactivado*.
10. **Opcional (sección 8 de la guía):** página de tooltip *TT Distrito* y marcador *Restablecer filtros*.
