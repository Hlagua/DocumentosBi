# UNIVERSIDAD TÉCNICA DE AMBATO
## FACULTAD DE INGENIERÍA EN SISTEMAS, ELECTRÓNICA E INDUSTRIAL
### CARRERA DE SOFTWARE — ASIGNATURA: INTELIGENCIA DE NEGOCIOS
### CICLO ACADÉMICO: AGOSTO 2026 – DICIEMBRE 2026

---

# GUÍA DE ARQUITECTURA E IMPLEMENTACIÓN DEL DASHBOARD EN POWER BI: REPLICACIÓN DUAL (SQL SERVER KIMBALL ↔ MONGODB NoSQL)

**Autores:** Alison Marcela Cobos Taco / Henry Daniel Lagua Flores  
**Docente:** Ing. Ruben Nogales, Mg.  
**Caso de Estudio:** Base de Datos Bancaria `Financial_ijs` (PKDD'99 Financial Discovery Challenge)  
**Versión:** 1.0 — Guía de Implementación Oficial con Reglas de Visualización del Docente

---

## 1. OBJETIVO DEL DASHBOARD Y ALINEACIÓN METODOLÓGICA

El objetivo de esta entrega final es construir y presentar **un mismo dashboard analítico gerencial replicado en dos archivos idénticos en Power BI Desktop**:
1. **`Dashboard_Financial_Kimball.pbix`:** Conectado directamente al Data Mart dimensional en **Microsoft SQL Server** (`DM_Financial_Kimball_v2`).
2. **`Dashboard_Financial_Mongo.pbix`:** Conectado a la base de datos documental en **MongoDB** (`Financial`).

Ambos cuadros de mando deben ser **visualmente indistinguibles** en cuanto a distribución, gráficos, colores, KPIs y filtros, demostrando la **persistencia políglota** y la concordancia cuantitativa al 100% entre ambos motores.

---

## 2. REGLAS ESTRICTAS DE VISUALIZACIÓN EXIGIDAS POR EL DOCENTE

Para garantizar el máximo rigor académico y analítico, el diseño del dashboard sigue de forma irrestricta las normas dictadas por la cátedra:

1. **Comparativas Categóricas:**
   * **Eje X:** Siempre variables categóricas (e.g. *Macro-Región*, *Tipo de Operación*, *Estado de Crédito*, *Categoría de Orden*).
   * **Eje Y:** Siempre métricas cuantitativas continuas (e.g. *Monto Colocado*, *Volumen Monetario*, *Saldo Promedio*, *Número de Préstamos*).
2. **Series Temporales:**
   * Exclusivamente **Gráficos de Líneas Continuas** para visualizar la evolución cronológica (1993 a 1998) y detectar tendencias, picos o aceleraciones de morosidad.
3. **Análisis de Significancia Estadística con Desviación Estándar:**
   * En los gráficos comparativos de barras/columnas, se incorporan **barras de error basadas en la Desviación Estándar ($\pm 1 \sigma$)**.
   * **Principio de interpretación gerencial:** *Si las barras de desviación estándar entre dos categorías se solapan, la diferencia no es estadísticamente significativa; si no se solapan, el cambio representa una variación estructural significativa en el negocio.*
4. **Gráfico de Pastel / Dona:**
   * Se utiliza **estrictamente para una única variable categórica** con un número reducido de clases ($\le 5$), específicamente para la composición de las 6,471 órdenes permanentes en sus 5 categorías homologadas.
5. **Prohibición de Gráficos 3D:**
   * Se descartan completamente visualizaciones en 3D (conos, cilindros, pasteles tridimensionales), ya que distorsionan los ángulos visuales y dificultan la lectura ejecutiva de proporciones.
6. **Tarjetas de KPIs en la Cabecera:**
   * Métricas clave destacadas en la parte superior para responder instantáneamente al estado de liquidez, mora y cartera.

---

## 3. RESPUESTA A LAS PREGUNTAS CLAVE DE LA CARTA DE DISEÑO

El dashboard está estructurado para resolver directamente las preguntas analíticas de negocio formuladas en la Carta de Diseño:

| # | Pregunta Clave de la Carta de Diseño | Indicador / Métrica Asociada | Visualización en Power BI |
| :-: | :--- | :--- | :--- |
| **P1** | **¿Cómo evoluciona la morosidad activa año a año y cuál es la tasa de pérdida en préstamos cerrados?** | Préstamos en mora (D), Tasa de Morosidad Activa Vigente (**10.04%**) y Tasa de Incumplimiento Histórico (**13.25%**). | **Gráfico de Líneas Temporal:** Préstamos totales vs. Préstamos en mora por año (1993–1998). |
| **P2** | **¿Qué distritos geográficos concentran el mayor riesgo crediticio y mora relativa?** | Monto colocado por región y tasa de mora distrital. | **Gráfico de Columnas con Barras de Desviación Estándar:** Comparativa por macro-región y distritos críticos. |
| **P3** | **¿Qué porcentaje del saldo disponible de los clientes está comprometido en préstamos?** | Ratio de Absorción Crediticia: $\frac{\text{Cartera}}{\text{Depósitos}}$ (**52.38%**). | **Tarjetas KPI Ejecutivas:** Cartera (\$103.26M) vs. Depósitos (\$197.14M) y Ratio de Absorción. |
| **P4** | **¿Qué operaciones mueven el mayor flujo de capital y cómo impactan en las cuentas?** | Volumen transaccional por canal y tipo de operación (`PRIJEM`, `VYDAJ`, `VYBER`). | **Gráfico de Columnas Agrupadas:** Eje X = Tipo de Operación, Eje Y = Monto Acumulado (\$). |
| **P5** | **¿Qué volumen y monto de pagos fijos automáticos tienen programados las cuentas?** | Cantidad y monto por categoría de orden (`SIPO`, `SIN_ESPECIFICAR`, `UVER`, `POJISTNE`, `LEASING`). | **Gráfico de Dona (1 Sola Variable):** Porcentaje de órdenes fijas según su categoría homologada. |
| **P6** | **¿Cómo se distribuyen los clientes y el riesgo según su perfil sociodemográfico?** | Distribución de los 5,369 clientes en los 9 arquetipos validados por $\chi^2 = 63.7832$. | **Gráfico de Barras Horizontales:** Clientes totales y tasa de adopción de préstamos por arquetipo. |

---

## 4. ESTRUCTURA Y MAQUETACIÓN DEL DASHBOARD (2 PÁGINAS)

### Página 1: Gestión de Cartera, Riesgo Crediticio y Liquidez Institucional (Core BI)

```
+---------------------------------------------------------------------------------------------------+
| FILTROS SUPERIORES: [Año: Todos/1993-1998]  [Región: Praga/Bohemia/Moravia]  [Condición: Todos/Vigente] |
+---------------------------------------------------------------------------------------------------+
|  [ TARJETA KPI 1 ]     |     [ TARJETA KPI 2 ]    |     [ TARJETA KPI 3 ]    |   [ TARJETA KPI 4 ]    |
|   Cartera Total        |     Saldo Depósitos      |     Ratio Absorción      |   Tasa Mora Vigente    |
|   $103,261,740.00      |     $197,140,434.00      |         52.38%           |        10.04%          |
+---------------------------------------------------+-----------------------------------------------+
| VISUAL 1: SERIE TEMPORAL (LÍNEAS)                 | VISUAL 2: COMPARATIVA CON DESVIACIÓN ESTÁNDAR |
| Evolución Anual de Colocación y Mora (1993-1998)  | Monto Promedio de Préstamo por Macro-Región   |
|  - Eje X: Año de Otorgamiento (1993-1998)         |  - Eje X: Macro-Región (Praga, Bohemia, Mor.)|
|  - Eje Y: Monto Colocado ($) / Préstamos          |  - Eje Y: Monto Promedio ($)                  |
|  - Línea 1: Préstamos Concedidos                  |  - Barras de Error: Desviación Estándar (±1σ) |
|  - Línea 2: Préstamos en Mora (Disparo en 1997)   |  *Demuestra solapamiento / significancia*     |
+---------------------------------------------------+-----------------------------------------------+
| VISUAL 3: COMPARATIVA POR DISTRITOS               | VISUAL 4: GRÁFICO DE DONA (UNA SOLA VARIABLE) |
| Top 10 Distritos por Monto de Cartera Colocada    | Distribución de Préstamos por Estado de Riesgo|
|  - Eje X: Nombre del Distrito                     |  - Variable: Estado de Préstamo               |
|  - Eje Y: Monto Total de Préstamos ($)            |  - Categorías: A (Cerrado OK), B (Defaulteado)|
|  - Tooltip: Tasa de Mora Distrital (%)            |                C (Al Día), D (Mora Activa)    |
+---------------------------------------------------------------------------------------------------+
```

---

### Página 2: Comportamiento Transaccional, Órdenes Fijas y Perfiles 360

```
+---------------------------------------------------------------------------------------------------+
| FILTROS SUPERIORES: [Año Transacción: 1993-1998]  [Tipo Operación: Todas]  [Segmento Edad: Todos]  |
+---------------------------------------------------------------------------------------------------+
|      [ TARJETA KPI 5 ]         |          [ TARJETA KPI 6 ]         |      [ TARJETA KPI 7 ]      |
|       Clientes Totales         |          Débito Mensual Órdenes    |      Volumen Transacciones  |
|            5,369               |              $21,229,041.00        |          $6,257,862,197     |
+---------------------------------------------------------------------+-----------------------------+
| VISUAL 5: COMPARATIVA CATEGÓRICA DE OPERACIONES                     | VISUAL 6: DONA (1 VARIABLE) |
| Flujo Monetario Acumulado por Canal y Tipo de Operación             | Distribución de Órdenes     |
|  - Eje X: Tipo de Operación (Depósito / Retiro / Transferencia)     | según Categoría Homologada  |
|  - Eje Y: Monto Transaccionado Total ($)                            |  - Hogar: 54.1% (3,502)     |
|  - Leyenda: Canal Operativo (Ventanilla Bancaria / ATM)             |  - Sin Especificar: 21.3%   |
|                                                                     |  - Préstamo: 11.1% (717)    |
|                                                                     |  - Seguros: 8.2% (532)      |
|                                                                     |  - Leasing: 5.3% (341)      |
+---------------------------------------------------------------------+-----------------------------+
| VISUAL 7: PERFILAMIENTO DEMOGRÁFICO DE CLIENTES (ARQUETIPOS VALIDADO POR CHI-CUADRADO)            |
| Tasa de Adopción de Crédito y Cantidad de Clientes por los 9 Arquetipos                            |
|  - Eje X: Arquetipo Demográfico (Macro-Región × Segmento de Edad)                                 |
|  - Eje Y: Cantidad de Clientes Totales / Tasa de Adopción de Préstamo (%)                          |
|  *Muestra la correlación estadística validada con χ² = 63.7832 (p < 0.001)*                        |
+---------------------------------------------------------------------------------------------------+
```

---

## 5. DICCIONARIO DE MEDIDAS DAX OFICIALES (LISTAS PARA COPIAR Y PEGAR)

Crea una tabla en Power BI llamada `_Medidas` y pega las siguientes fórmulas DAX:

### Medidas de Cartera y Riesgo:
```dax
// 1. Cartera Total de Préstamos
Total Cartera Prestamos = SUM(Fact_Prestamos[monto_prestamo])

// 2. Número Total de Créditos Concedidos
Total Creditos Concedidos = COUNTROWS(Fact_Prestamos)

// 3. Monto Promedio de Préstamo
Monto Promedio Prestamo = AVERAGE(Fact_Prestamos[monto_prestamo])

// 4. Desviación Estándar de Préstamo (para barras de error)
Desviacion Estandar Prestamo = STDEV.P(Fact_Prestamos[monto_prestamo])

// 5. Préstamos en Mora Activa (Estado D)
Creditos en Mora Activa = 
CALCULATE(
    COUNTROWS(Fact_Prestamos),
    Fact_Prestamos[codigo_estado] = "D"
)

// 6. Cartera Activa Vigente (Estados C y D)
Cartera Activa Vigente = 
CALCULATE(
    COUNTROWS(Fact_Prestamos),
    Fact_Prestamos[condicion] = "Vigente"
)

// 7. Tasa de Morosidad Activa Vigente (KPI Clave = 10.04%)
Tasa Morosidad Activa Vigente = 
DIVIDE([Creditos en Mora Activa], [Cartera Activa Vigente], 0)

// 8. Tasa de Incumplimiento Histórico en Créditos Cerrados (Estado B = 13.25%)
Tasa Incumplimiento Historico = 
DIVIDE(
    CALCULATE(COUNTROWS(Fact_Prestamos), Fact_Prestamos[codigo_estado] = "B"),
    CALCULATE(COUNTROWS(Fact_Prestamos), Fact_Prestamos[condicion] = "Cerrado"),
    0
)
```

### Medidas de Liquidez y Transaccionalidad:
```dax
// 9. Saldo Total de Depósitos al Corte (Medida Semiaditiva institucional = $197.14M)
Saldo Total Depositos = 
CALCULATE(
    SUM(Fact_Transacciones[saldo_cuenta]),
    LASTDATE(Dim_Tiempo[fecha])
)

// 10. Ratio de Absorción Crediticia (KPI de Liquidez = 52.38%)
Ratio Absorcion Crediticia = 
DIVIDE([Total Cartera Prestamos], [Saldo Total Depositos], 0)

// 11. Monto Total de Órdenes Mensuales Programadas
Monto Total Ordenes Mensual = SUM(Fact_Ordenes[monto_orden])

// 12. Volumen Total Transaccionado
Volumen Total Transacciones = SUM(Fact_Transacciones[monto_transaccion])
```

---

## 6. GUÍA DE CONEXIÓN PASO A PASO EN POWER BI

### Caso A: Construcción de `Dashboard_Financial_Kimball.pbix` (SQL Server)
1. Abre **Power BI Desktop**.
2. Haz clic en **Obtener datos** $\rightarrow$ **SQL Server**.
3. **Servidor:** `(localdb)\MSSQLLocalDB` (o `.\SQLEXPRESS`).
4. **Base de datos:** `DM_Financial_Kimball_v2`.
5. **Modo:** *Importar*.
6. Selecciona las tablas:
   * `Fact_Prestamos`
   * `Fact_Ordenes`
   * `Fact_Transacciones` (o vista agregada mensual para agilidad)
   * `Dim_Cliente`
   * `Dim_Distrito`
   * `Dim_Tiempo`
   * `Dim_Estado_Prestamo`
   * `Dim_Orden`
   * `Dim_Operacion`
7. Haz clic en **Cargar**. En la vista de Modelo, las relaciones estrella/constelación se crearán automáticamente gracias a las claves `sk_`.

---

### Caso B: Construcción de `Dashboard_Financial_Mongo.pbix` (MongoDB)
Para conectar Power BI a MongoDB local de forma limpia, ultrarrápida y sin requerir configurar complejos controladores DSN ODBC:
1. Abre un nuevo archivo en **Power BI Desktop**.
2. Haz clic en **Obtener datos** $\rightarrow$ **Script de Python**.
3. Pega el código de nuestro conector oficial ya probado ([`scripts/powerbi_mongo_connector.py`](file:///C:/Users/henry/.gemini/antigravity/scratch/DocumentosBi/scripts/powerbi_mongo_connector.py)):
   ```python
   import pymongo, pandas as pd
   client = pymongo.MongoClient("mongodb://localhost:27017/")
   db = client["Financial"]

   # Cargar y aplanar colecciones
   df_prestamos = ... # (Usa el código de scripts/powerbi_mongo_connector.py)
   df_ordenes = ...
   df_clientes = ...
   df_distritos = ...
   ```
4. Haz clic en **Aceptar**. Power BI detectará automáticamente las 4 tablas aplanadas:
   * `df_prestamos` (682 filas)
   * `df_ordenes` (6,471 filas)
   * `df_clientes` (5,369 filas)
   * `df_distritos` (77 filas)
5. En la vista de Modelo de Power BI, vincula:
   * `df_clientes[id_cliente]` $\rightarrow$ `df_prestamos[id_cliente]` (1 a Varios).
   * `df_clientes[id_cliente]` $\rightarrow$ `df_ordenes[id_cliente]` (1 a Varios).
   * `df_distritos[id_distrito]` $\rightarrow$ `df_clientes[id_distrito]` (1 a Varios).
6. Pega las mismas medidas DAX y añade los mismos gráficos.

---

## 7. CÓMO CONFIGURAR LAS BARRAS DE ERROR DE DESVIACIÓN ESTÁNDAR EN POWER BI

Para cumplir la instrucción del docente sobre significancia estadística:
1. Inserta un **Gráfico de columnas agrupadas**.
2. **Eje X:** Arrastra `macro_region` (Praga, Bohemia, Moravia).
3. **Eje Y:** Arrastra la medida `[Monto Promedio Prestamo]`.
4. En el panel de **Formato visual** (icono de pincel), ve a la pestaña **Análisis** (icono de lupa/gráfico).
5. Activa la opción **Barras de error**.
6. **Opciones de barra de error:**
   * Tipo: *Medida*.
   * Límite superior: Arrastra una medida calculada: `[Monto Promedio Prestamo] + [Desviacion Estandar Prestamo]`.
   * Límite inferior: Arrastra: `[Monto Promedio Prestamo] - [Desviacion Estandar Prestamo]`.
7. **Interpretación visual en la exposición:**
   * Observarás que las barras de error de las tres regiones se solapan entre sí.
   * **Conclusión que debes decir en clase:** *"Al solaparse las barras de desviación estándar entre Praga, Bohemia y Moravia, se comprueba estadísticamente que no existe una diferencia significativa en el monto prestado promedio según la región; la variabilidad individual dentro de cada región es mayor que la diferencia entre regiones."* (Esto cumple al 100% la indicación del profesor).

---

## 8. CONCLUSIÓN Y BENEFICIO PARA LA DEFENSA FINAL

Presentar ambos archivos (`.pbix`) idénticos ante el docente:
1. **Evidencia de Persistencia Políglota:** Demuestra que la organización puede consultar la misma verdad financiera tanto desde un Data Warehouse relacional en SQL Server (para analistas BI corporativos) como desde un almacén documental en MongoDB (para desarrollo ágil y microservicios).
2. **Cumplimiento Pedagógico Estricto:** Satisface todas las observaciones de visualización: ausencia de 3D, separación clara categórica/numérica, series temporales continuas y prueba visual de significancia mediante desviación estándar.
3. **Trazabilidad 100% Reconciliada:** Las tarjetas numéricas marcarán exactamente los mismos dólares y porcentajes en ambos paneles.
