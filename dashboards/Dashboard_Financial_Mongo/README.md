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

### Cómo lo usa el gerente
* **Panel izquierdo (en todas las páginas):** navegación a Inicio, P1–P6 y R1–R3, y los filtros **Año**, **Zona**
  (macro-región › región › distrito) y **Segmento de edad**. Están sincronizados: lo que elija sigue activo al
  cambiar de página.
* **Clic en un gráfico:** filtra los demás gráficos de esa misma página (comportamiento estándar de Power BI).
* **Clic derecho en un cliente o distrito → Obtener detalles:** abre la ficha D2 (cliente) o D1 (distrito)
  **con todos los filtros aplicados**; el botón *Atrás* vuelve a la página de origen. D1 y D2 están ocultas en
  las pestañas porque solo tienen sentido para un cliente o distrito concreto.

### Ya configurado desde el código (no hay que tocarlo)
Tema Okabe–Ito incrustado; drill-through de D1 (`m_distritos[nombre_distrito]`) y D2 (`m_clientes[cliente]`) manteniendo los filtros;
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
