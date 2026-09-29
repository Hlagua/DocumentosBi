# Dashboard_Financial_Mongo (Power BI Project)

Fuente: MongoDB `Financial` (localhost:27017) mediante el conector `scripts/26_powerbi_mongo_dashboard.py`,
incrustado en la consulta compartida `MongoFinancial`. Diseño: Guía 07 v4. Generado con `python scripts/30_generar_powerbi_pbip.py`.

### Cómo abrirlo
1. MongoDB en ejecución con la base `Financial` (scripts 35 y 42, o `mongorestore --gzip --archive=Financial_mongo_dump.gz`).
2. **Python de python.org, no el de Microsoft Store.** Power BI Desktop no puede ejecutar el Python de la
   Store (carpeta `WindowsApps`): la actualización falla con *"Acceso denegado"* (comprobado en
   Power BI 2.157). Instala Python 3.12 desde https://www.python.org (o
   `winget install --id Python.Python.3.12 --scope user`) y luego, con ese Python:
   `python -m pip install pandas==3.0.5 pymongo==4.18.1 matplotlib==3.10.7`
   Power BI siempre ejecuta `import matplotlib.pyplot`; en este equipo Windows App Control bloquea la DLL
   `_image` de matplotlib 3.11.2 y deja cargar la 3.10.7 (las versiones fijadas son las probadas).
   Elige la carpeta de ese Python en *Archivo → Opciones → Scripts de Python*
   (`%LOCALAPPDATA%\Programs\Python\Python312`).
3. Doble clic en `Dashboard_Financial_Mongo.pbip` → *Inicio → Actualizar*. Acepta el aviso de privacidad del script.
4. Compara con las cifras de control: deben ser idénticas a las de Kimball.

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
2. **Drill-through:** en *D1 Distrito* arrastra `m_distritos[nombre_distrito]` a *Obtener detalles*; en *D2 Cliente 360* arrastra
   `m_clientes[cliente]` **y** `m_cuentas[cuenta]` (P5 llega por cuenta; P2, P6 y D1 por cliente). Luego clic derecho en las
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
