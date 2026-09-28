# UNIVERSIDAD TÉCNICA DE AMBATO
## FACULTAD DE INGENIERÍA EN SISTEMAS, ELECTRÓNICA E INDUSTRIAL
### CARRERA DE SOFTWARE — ASIGNATURA: INTELIGENCIA DE NEGOCIOS
### CICLO ACADÉMICO: AGOSTO 2026 – DICIEMBRE 2026

---

# DOSSIER MAESTRO DE AUDITORÍA EXTERNA: ESPECIFICACIÓN INTEGRAL DEL DASHBOARD ARTICULADO POLÍGLOTA (POWER BI · KIMBALL SQL SERVER & MONGODB NoSQL)

**Autores:** Alison Marcela Cobos Taco / Henry Daniel Lagua Flores  
**Docente de la Cátedra:** Ing. Ruben Nogales, Mg.  
**Caso de Estudio:** Base de Datos Bancaria `Financial_ijs` (PKDD'99 Financial Discovery Challenge / Czech Bank Benchmark)  
**Entregables Finales:** `Dashboard_Financial_Kimball.pbix` (SQL Server) y `Dashboard_Financial_Mongo.pbix` (MongoDB)  
**Versión del Dossier:** 2.1 — Definitiva con los 5 Puntos Críticos Auditados y Verificados en Base de Datos  

---

> ### 📋 INSTRUCCIÓN DE ENCABEZADO PARA LA INTELIGENCIA ARTIFICIAL REVISORA
> 
> *Actúa como un **Auditor Principal de Business Intelligence**, **Catedrático de Postgrado en Data Warehouse & Minería de Datos** y **Científico de Datos Senior**. Se te presenta el diseño, arquitectura, formulación matemática, datos canónicos, fundamentos perceptuales y especificación técnica de un proyecto final de Inteligencia de Negocios.*
> 
> *Tu labor consiste en: (1) Auditar exhaustivamente la solidez de la narrativa analítica articulada (storytelling de negocio) frente a los requisitos del docente; (2) Evaluar la idoneidad psicofísica y perceptiva de los gráficos seleccionados basándote en la literatura científica (Cleveland & McGill, Tufte, Few, Munzner, Cumming, Wilson); (3) Validar el rigor estadístico de las reglas metodológicas (solapamiento de barras de error ±1σ, ANOVA con datos reales, intervalos de Wilson para proporciones y Test de Fisher por regla de Cochran); (4) Revisar la equivalencia arquitectónica y el rendimiento entre el modelo dimensional Kimball (SQL Server) y el modelo documental NoSQL (MongoDB); y (5) Emitir recomendaciones críticas, identificar vulnerabilidades conceptuales y simular las preguntas más desafiantes que un tribunal evaluador o el docente titular formularían en la defensa oral.*

---

## 1. CONTEXTO ACADÉMICO Y REQUERIMIENTO DEL DOCENTE

### 1.1 El Reto Académico
En el marco de la asignatura de **Inteligencia de Negocios** de la Universidad Técnica de Ambato, el docente de la cátedra (Ing. Ruben Nogales, Mg.) ha establecido los siguientes requisitos de evaluación para el proyecto final:
1. **Persistencia Políglota Replicada (Kimball Completado ↔ MongoDB):** Construir **dos dashboards idénticos** en Power BI Desktop:
   - Uno conectado al Data Warehouse dimensional en **SQL Server** (`DM_Financial_Kimball_v2`), completado y enriquecido con métricas analíticas.
   - Otro conectado a la base de datos documental **NoSQL en MongoDB** (`Financial`), generada directamente a partir del modelo dimensional para garantizar paridad absoluta.
   - Ambos dashboards deben presentar exactamente las mismas páginas, métricas, títulos, visualizaciones e interactividad, comprobando que la inteligencia de negocios es independiente del motor de almacenamiento subyacente.
2. **Hilo Conductor Articulado (Storytelling de Negocio):** El docente enfatizó explícitamente:
   > *"No quiero dashboards dispersos con una pestaña de ventas aislada, otra de productos y otra de proveedores. El dashboard debe tener un hilo conductor que responda a preguntas de negocio articuladas: por ejemplo, ¿cuál es el producto más vendido? → ¿quién es su proveedor? → de ese proveedor, ¿qué otros productos tenemos? Todo debe estar enlazado mediante botones, segmentadores sincronizados y drill-through."*
3. **Respuesta a la Carta de Diseño:** El tablero debe dar respuesta rigurosa a las preguntas estratégicas formalizadas en la Carta de Diseño aprobada (v6).
4. **Gobierno y Reconciliación Matemática Estricta:** Las cifras clave deben cuadrar al centavo entre el origen de datos transaccional, el Data Warehouse dimensional y la base documental NoSQL ($\Delta = \$0.00$).

### 1.2 Reglas Metodológicas de Visualización del Docente (Alineadas con la Literatura Científica)
El docente dictó una serie de pautas estrictas de visualización de datos, las cuales fundamentamos con los autores canónicos de la ciencia de la percepción gráfica:

* **Regla 1 (Ejes Categóricos y Cuantitativos - Cleveland & McGill, 1984):** El eje $X$ se reserva para variables categóricas o discretas; el eje $Y$ siempre codifica magnitudes numéricas cuantitativas continuas. La posición a lo largo de una escala común alineada es el canal de percepción humana de mayor precisión psicofísica.
* **Regla 2 (Series Temporales Continuas - Tufte, 1983; Few, 2004):** Los gráficos de líneas continuas se utilizan estricta y únicamente para representar la evolución continua a través del tiempo (1993 a 1998). Maximizar el *Data-Ink Ratio* eliminando decoraciones innecesarias, cuadrículas pesadas y agregando etiquetas de datos directas. **No se permiten gráficos de áreas apiladas como sustitutos de líneas**, para evitar ambigüedades en la lectura de pendientes individuales y cumplir la letra de la regla del docente.
* **Regla 3 (Gráficos Circulares / Dona Monovariables - Stephen Few, 2007):** El gráfico de pastel o dona representa **una única variable** compositiva (partes de un todo). Se restringe estrictamente a un máximo de 2 a 5 categorías (ej. Distribución de Órdenes Permanentes en sus 5 conceptos canónicos). Nunca debe usarse para series temporales ni para variables con muchas categorías.
* **Regla 4 (Prohibición Absoluta de Visualizaciones 3D - Tufte, 1983; Munzner, 2014):** Los gráficos en 3D distorsionan las proporciones reales debido a la perspectiva geométrica, ocluyen puntos de datos y añaden ruido cognitivo (*chartjunk*). Están formalmente vetados en ambos tableros.
* **Regla 5 (Comparativas y Regla del Solapamiento de la Desviación Estándar - Regla del Docente / Cumming et al., 2007):** En comparativas categóricas de medias continuas, cuando se desea evaluar si las diferencias entre grupos son significativas, se incorporan barras de error de desviación estándar ($\pm 1\sigma$) o error estándar ($\pm 1\text{EE}$). **Al solaparse las barras de error entre categorías, las diferencias observadas NO son estadísticamente significativas.**
* **Regla 6 (Rigor Estadístico Diferenciado: Medias Continuas vs Proporciones Binarias - Wilson, 1927; Cochran, 1954; Fisher, 1922):** 
  - Para magnitudes monetarias continuas (monto de préstamo, ticket de transacción), se aplica $\bar{x} \pm 1\sigma$ o $\pm 1\text{EE}$ y se complementa con análisis de varianza (ANOVA).
  - Para tasas y proporciones binomiales ($p = \text{tasa de mora}$), las barras de error gaussianas $\pm 1\sigma$ generan cotas inferiores matemáticamente inválidas (negativas) cuando $p \to 0$ (como en north Bohemia con 0% de mora). Por ello, se aplica el **Intervalo de Puntuación de Wilson (Wilson Score Interval, 1927)**.
  - Para tablas de contingencia con frecuencias esperadas $< 5$, se aplica la **Regla de Cochran (1954)**: si más del 20% de las celdas o alguna celda esperada es $< 1$, la prueba asintótica $\chi^2$ pierde validez y se debe emplear el **Test Exacto de Fisher** (para tablas $2 \times 2$) o colapsar categorías para garantizar validez inferencial.

---

## 2. EL HILO CONDUCTOR BANCARIO (CADENA FORENSE ARTICULADA)

Para cumplir con la directriz del docente, se tradujo el ejemplo de compras (*"producto más vendido → proveedor → catálogo"*) a la operativa bancaria de alto impacto: **la trazabilidad forense del riesgo crediticio y la morosidad**.

```
[P1 · ¿CUÁNDO?] (La mora activa se dispara en 1997: 23 casos D, 51.1% del total histórico)
       │
       ▼ (Botón interactivo de navegación)
[P2 · ¿DÓNDE?] (Monto promedio entre regiones se solapa en ±1σ, ANOVA F=0.1210, p=0.8861; 
                pero la mora se concentra en north Moravia con 15.79%)
       │
       ▼ (Drill-through en Distrito)
[D1 · DETALLE DISTRITO] (Karvina lidera con 20.00% de mora distrital activa: 24 préstamos, $3.06M de cartera)
       │
       ▼ (Drill-through en Cliente)
[D2 · FICHA CLIENTE 360] (Cliente 2823 · Cuenta 2335 · 52 años: Préstamo $541,200 a 60 meses, cuota $9,020 en Estado D)
       │
       ├─► [P4 / D2] (Saldo promedio anual cayó de $25,368 en 1996 a $3,354 en 1997 y $723 en 1998; cierre: -$2,803.00)
       │
       ├─► [P5 · ¿QUIÉN ESTÁ SATURADO?] (Tiene 5 órdenes de pago automáticas en 4 categorías por $14,286/mes. Índice de saturación = 2.14)
       │
       ▼
[P6 · POLÍTICA DE MITIGACIÓN] (31 clientes con impago histórico Estado B: denegación automática y listas de interdicción)
```

### Tabla de Trazabilidad Forense
| Paso | Pregunta de Negocio | Hallazgo con Datos Canónicos Reales Verificados | Visualización y Acción en Power BI |
| :-: | :--- | :--- | :--- |
| **1** | ¿Cuándo se desestabiliza la cartera? | Préstamos en mora por año de concesión: 0 (1993), 2 (1994), 6 (1995), 10 (1996), **23 (1997)**, 4 (1998). El shock macroeconómico checo de 1997 detonó la cartera. | **P1 (¿Cuándo?):** Gráfico de líneas temporales continuas y barras de mora anual. Botón de navegación hacia P2. |
| **2** | ¿En qué territorio se localiza el riesgo? | El monto promedio prestado entre macro-regiones se solapa totalmente en $\pm 1\sigma$ (\$153.9K en Praga vs \$149.3K en Bohemia y \$153.5K en Moravia; ANOVA $F=0.1210, p=0.8861$). Sin embargo, la tasa de mora se concentra en **north Moravia (15.79%)**, mientras north Bohemia tiene 0.00%. | **P2 (¿Dónde?):** Barras con error $\pm 1\sigma$ por macro-región y Scatter Plot de distritos ($X = \text{Cartera}$, $Y = \text{Tasa Mora}$, $\text{Size} = \text{Préstamos}$). Karvina destaca nítidamente en el cuadrante superior derecho. |
| **3** | ¿Cuál es el distrito crítico de esa región? | **Karvina** (Distrito ID 73, north Moravia): Cartera de \$3,059,820 colocada en 24 préstamos; 3 créditos en mora activa sobre 15 vigentes (**20.00% de tasa distrital activa**). Depósitos captados: \$7,002,080 en 152 cuentas (**Ratio de Absorción Distrital = 43.70%**). | Clic derecho en Karvina en P2 $\rightarrow$ **Drill-through a D1 (Detalle Distrito)**. |
| **4** | ¿Quiénes explican la morosidad de Karvina? | Préstamos 5447, 6816 y 6959. El caso más voluminoso de todo el banco es el **Cliente 2823** (Cuenta 2335): Préstamo de \$541,200 a 60 meses (\$9,020/mes), concedido el 12/11/1997. Titular mujer de **52 años** (nacida el 18/12/1946). | Tabla de créditos de D1 $\rightarrow$ Clic derecho en Cliente 2823 $\rightarrow$ **Drill-through a D2 (Ficha Cliente 360)**. |
| **5** | ¿Cuál fue la causa de la insolvencia del cliente? | Posee **5 órdenes de débito permanente** (4 categorías) por **\$14,286 mensuales** (\$9,020 préstamo, \$2,036 vivienda, \$2,745 varios en 2 órdenes, \$485 seguro). Su saldo bancario promedio se evaporó de \$25,368.17 (1996) a \$3,354.26 (1997) y \$722.56 (1998), cerrando al corte en saldo rojo: **-\$2,803.00** (con mínimo histórico en sobregiro de -\$17,030.00). | **D2 (Ficha Cliente 360):** Gráfico de líneas temporales de saldos de la cuenta y tabla de órdenes activas. |
| **6** | ¿Es un caso aislado o un patrón institucional? | El Cliente 2823 encabeza la institución con un **Índice de Saturación de 2.14** (sus débitos fijos superan el 214% de su saldo medio). Es el caso más extremo dentro de un universo de **47 clientes con índice $> 0.5$**. | **P5 (Saturación):** Gráfico de dona monovariable de órdenes por concepto (5 categorías) y ranking institucional de clientes saturados. |
| **7** | ¿Qué acciones de contención se toman? | Se identifican **31 clientes en Estado B** (créditos cerrados con pérdidas no recuperadas por \$4.36M). Se establecen filtros de exclusión crediticia. | **P6 (Impago Histórico):** Gráficos de barras demográficas y tabla de interdicción crediticia con validación de Fisher exacto. |

---

## 3. GROUND TRUTH MATEMÁTICO: DATOS CANÓNICOS RECONCILIADOS

Las siguientes cifras fueron verificadas directamente contra el repositorio relacional original de la Universidad Técnica Checa (`relational.fel.cvut.cz`, base `Financial_ijs`), contra el Data Warehouse en SQL Server (`DM_Financial_Kimball_v2`) y contra la base documental en MongoDB (`Financial`). La discrepancia entre los tres entornos es **cero absoluto ($\Delta = \$0.00$)**.

| Dominio Analítico | Métrica / Indicador Canónico | Valor Exacto | Comprobación Técnica / Definición Matemática |
| :--- | :--- | ---: | :--- |
| **Colocación Crediticia** | Cartera Total Colocada | **\$103,261,740.00** | Suma total de `amount` en 682 contratos de préstamo (1993–1998). |
| | Cantidad Total de Préstamos | **682** | 682 operaciones de crédito únicas. |
| | Monto Promedio por Préstamo | **\$151,410.18** | $\sigma = \$74,180.42$ a nivel nacional. |
| **Estado de Préstamos** | Estado A (Cerrado al corriente) | **203** (\$18,604,800.00) | Contratos finalizados exitosamente sin deuda. |
| | Estado B (Cerrado con impago/defraudado) | **31** (\$4,364,520.00) | Contratos finalizados en pérdidas definitivas irrecuperables. |
| | Estado C (Vigente al corriente) | **403** (\$69,078,480.00) | Contratos en ejecución con pagos al día. |
| | Estado D (Vigente en mora activa) | **45** (\$11,213,940.00) | Contratos en ejecución con cuotas impagas en cobro coactivo. |
| **Calidad de Cartera** | **Tasa de Morosidad Activa Vigente** | **10.0446%** (10.04%) | $\frac{\text{Préstamos en Estado D}}{\text{Préstamos Vigentes (C + D)}} = \frac{45}{448} = 10.0446\%$. |
| | Tasa de Incumplimiento Histórico | **13.2478%** (13.25%) | $\frac{\text{Préstamos en Estado B}}{\text{Préstamos Cerrados (A + B)}} = \frac{31}{234} = 13.2478\%$. |
| | Cartera en Riesgo (B + D) | **\$15,578,460.00** | Monto original de préstamos con siniestralidad. |
| **Captación y Liquidez** | **Saldo Total en Depósitos (Cuentas)** | **\$197,140,434.00** | **Medida Semiaditiva:** Suma de los saldos finales de las 4,500 cuentas bancarias al corte del 31/12/1998. |
| | Cuentas Bancarias Activas | **4,500** | 4,500 cuentas corrientes en 77 distritos. |
| | **Ratio de Absorción Crediticia** | **52.3803%** (52.38%) | $\frac{\text{Cartera Total Colocada}}{\text{Saldo de Depósitos}} = \frac{\$103,261,740.00}{\$197,140,434.00} = 52.3803\%$. Cobertura de fondeo holgada (47.62% de liquidez libre). |
| **Flujo Operativo** | Volumen Transaccional Histórico | **\$6,257,862,197.00** | Suma del valor absoluto de todas las transacciones monetarias. |
| | Cantidad Total de Transacciones | **1,056,320** | Registros procesados (1993–1998). |
| | Ticket Promedio por Transacción | **\$5,924.21** | $\frac{\$6,257,862,197.00}{1,056,320}$. |
| **Órdenes de Pago** | Compromiso Mensual de Órdenes | **\$21,229,041.00** | Suma mensual programada en 6,471 órdenes de débito automático. |
| | Cantidad de Órdenes Permanentes | **6,471** | Pagos recurrentes domiciliados (5 categorías de `k_symbol`). |
| **Demografía y Clientes**| Clientes Totales del Banco | **5,369** | 4,500 titulares con disposición `OWNER` + 869 autorizados `DISPONENT`. |
| | Clientes Sobreendeudados (Saturados) | **47** | Clientes con Índice de Saturación ($\frac{\text{Compromiso Órdenes}}{\text{Saldo Promedio}}) > 0.5$. |
| | Clientes con Quiebra Histórica | **31** | Clientes únicos asociados a préstamos en Estado B. |
| | Distritos Monitoreados | **77** | 77 distritos checos agrupados en 8 regiones y 3 macro-regiones. |

---

## 4. ESPECIFICACIÓN DETALLADA PESTAÑA POR PESTAÑA: EL QUÉ, EL POR QUÉ Y EL CÓMO

Los dos archivos (`Dashboard_Financial_Kimball.pbix` y `Dashboard_Financial_Mongo.pbix`) están estructurados exactamente en **9 pestañas**:

### Pestaña 0: Inicio — Panorama Ejecutivo y Navegación Articulada
* **Objetivo de Negocio:** Presentar la salud macro del banco, resumir los 4 KPIs estratégicos, trazar visualmente el hilo conductor analítico y servir de portal de acceso directo mediante botones a las 6 preguntas de la Carta de Diseño.
* **KPIs en Fila Superior (Tarjetas Card):**
  1. *Cartera Total Colocada:* \$103.26M (682 préstamos).
  2. *Saldo en Depósitos:* \$197.14M (4,500 cuentas, corte semiaditivo al 31/12/1998).
  3. *Ratio de Absorción Crediticia:* 52.38% (cobertura saludable).
  4. *Tasa de Morosidad Activa Vigente:* 10.04% (45 créditos en Estado D sobre 448 vigentes).
* **Panel Izquierdo:** Diagrama del Hilo Conductor (Pasos 1 a 6) mostrando la cadena analítica desde el macro-fenómeno temporal de 1997 hasta la orden de pago del cliente moroso en Karvina.
* **Panel Derecho:** 6 Botones interactivos con enlaces directos a las páginas P1 a P6.
* **Banda de Auditoría Inferior:** Indicador visual de concordancia matemática ($\Delta = \$0.00$ entre SQL Server y MongoDB).

---

### Pestaña 1: P1 · ¿Cuándo? — Evolución Temporal de la Cartera y Desestabilización de la Mora
* **Pregunta de la Carta de Diseño:** *¿Cómo evoluciona la morosidad activa año a año y cuándo se produjo la pérdida de calidad crediticia?*
* **Gráfico 1 (Principal): Gráfico de Líneas Continuas con Marcadores y Etiquetas de Datos.**
  - **Métricas:** Evolución anual (1993 a 1998) de Préstamos Otorgados vs Préstamos que cayeron en Mora Activa (Estado D).
  - **Fundamento Académico (El Por Qué):** Cumplimiento estricto de la **Regla 2 del docente** y el principio de Tufte (1983): las líneas implican continuidad y correlación serial de un proceso temporal subyacente. El ojo percibe pendientes de aceleración de forma inmediata.
  - **Mapeo Visual (El Cómo):** Eje $X$ = Año cronológico (1993, 1994, 1995, 1996, 1997, 1998). Eje $Y$ = Número de operaciones y montos (\$M). Línea azul = Cartera colocada; Línea roja con marcadores = Casos en mora D. Destacar el salto abrupto de 1996 (10 casos) a 1997 (23 casos, $+130\%$).
* **Gráfico 2 (Secundario): Gráfico de Columnas Agrupadas.**
  - **Métricas:** Monto prestado en cartera sana (\$M) vs Cartera en riesgo por año.
  - **Fundamento (El Por Qué):** Cleveland & McGill (1984): la posición sobre una escala común alineada permite juzgar con máxima exactitud la proporción de capital arriesgado por cohorte anual.
* **Interacción:** Botón interactivo de salto rápido: *"Ver dónde ocurre territorialmente → Pestaña P2"*.

---

### Pestaña 2: P2 · ¿Dónde? — Riesgo Geográfico y Comparativa Territorial
* **Pregunta de la Carta de Diseño:** *¿Qué macro-regiones y distritos geográficos concentran la mayor colocación y la mayor mora relativa?*
* **Gráfico 1 (Izquierdo): Gráfico de Barras con Barras de Error de Desviación Estándar ($\pm 1\sigma$).**
  - **Métricas Reales Verificadas:** Monto promedio de préstamo por Macro-Región:
    - Praga ($n = 84$): media = \$153,957.29, $\sigma = \$123,275.73$
    - Bohemia ($n = 352$): media = \$149,344.23, $\sigma = \$108,115.52$
    - Moravia ($n = 246$): media = \$153,496.59, $\sigma = \$117,556.94$
  - **Fundamento Académico (El Por Qué):** Aplicación rigurosa de la **Regla 5 del docente** y Cumming et al. (2007): el solapamiento visual completo de las tres franjas de error demuestra de manera concluyente que **no existen diferencias estadísticamente significativas en el tamaño del crédito otorgado entre regiones**.
  - **Prueba Inferencial Formal:** ANOVA de un factor sobre `monto_prestamo`:
    $$\mathbf{F = 0.1210, \quad p = 0.8861}$$
    Dado que $p = 0.8861 \gg 0.05$, no se rechaza la hipótesis nula de medias iguales. *(Nota técnica: la cifra preliminar $F=1.17, p=0.32$ correspondió a una prueba sobre plazo_meses; el valor canónico para montos es $F=0.1210, p=0.8861$)*.
  - **Mapeo Visual (El Cómo):** Eje $X$ = Macro-Región (Praga, Bohemia, Moravia). Eje $Y$ = Monto promedio (\$). Barras de error en bigotes con límite superior ($+1\sigma$) e inferior ($-1\sigma$), complementado con una banda horizontal sombreada que hace explícito el solapamiento.
* **Gráfico 2 (Derecho): Gráfico de Dispersión / Burbujas por Distritos (Scatter / Bubble Plot).**
  - *(Sustituye al Treemap saturado en saturación de color y área, según Munzner 2014 y Cleveland & McGill 1984)*.
  - **Métricas:** Los 77 distritos checos calculados desde `Fact_Prestamos`. Eje $X$ = Cartera Colocada (\$), Eje $Y$ = Tasa de Mora Vigente (%), Tamaño de Burbuja = Número de Préstamos, Color = Macro-Región.
  - **Fundamento Académico (El Por Qué):** Los treemaps codifican información mediante áreas rectangulares y gradientes de color, canales que ocupan peldaños inferiores en la jerarquía psicofísica de Cleveland & McGill (1984). El Scatter Plot utiliza la **posición en dos escalas continuas ortogonales (X e Y)**, lo que permite aislar visualmente anomalías multivariadas en un solo golpe de vista.
  - **Mapeo Visual (El Cómo):** Líneas de referencia en $X = \text{Promedio de colocación distrital}$ (\$1.34M) y en $Y = \text{Promedio nacional de mora}$ (10.04%). El distrito **Karvina (Distrito 73, north Moravia)** se ubica nítidamente en el cuadrante superior derecho de máximo peligro (\$3.06M de cartera, 24 préstamos y 20.00% de mora activa sobre 15 vigentes), con flecha anotada.
* **Interacción:** Drill-through configurado en los distritos: Clic derecho en Karvina $\rightarrow$ *"Obtener detalles: D1 Detalle Distrito"*.

---

### Pestaña 3: P3 · ¿Cuánto? — Liquidez, Absorción Crediticia y Capacidad de Fondeo
* **Pregunta de la Carta de Diseño:** *¿Qué porcentaje de los depósitos de los clientes está absorbido por la cartera de crédito y cuál es la cobertura de liquidez?*
* **Gráfico 1: Gráfico de Columnas Agrupadas por Macro-Región (Cartera vs Depósitos).**
  - **Métricas:** Cartera Colocada (\$103.26M) vs Saldo en Depósitos (\$197.14M al corte).
  - **Fundamento (El Por Qué):** Cleveland & McGill (1984): la yuxtaposición de barras lado a lado permite contrastar la magnitud de los activos crediticios frente a los pasivos captados con base alineada en cero.
  - **Mapeo Visual (El Cómo):** Eje $X$ = Región. Eje $Y$ = Monto acumulado en millones de dólares (\$M). Barra azul = Préstamos; Barra verde = Depósitos. Se aprecia que en todas las regiones los depósitos prácticamente duplican a los créditos.
* **Gráfico 2: Gráfico de Barras Horizontales con Línea de Referencia de Tasa de Absorción.**
  - **Métricas:** Ratio de Absorción ($\frac{\text{Cartera}}{\text{Depósitos}}$) por región (Promedio institucional: 52.38%; Karvina distrital verificado: **43.70%**).
  - **Fundamento (El Por Qué):** Stephen Few (2013): barras horizontales con una línea de corte vertical son óptimas para comparar métricas de desempeño frente a un umbral normativo institucional.
* **KPIs Clave:** Cobertura de Liquidez Libre (\$93.88M, 47.62%), Ratio de Absorción (52.38%).

---

### Pestaña 4: P4 · ¿Cómo se mueve el capital? — Flujo Transaccional y Variabilidad Operativa
* **Pregunta de la Carta de Diseño:** *¿Qué canales operativos concentran el mayor flujo monetario y cómo varía el ticket promedio y su dispersión?*
* **Gráfico 1: Gráfico de Barras con Barras de Error de Desviación Estándar ($\pm 1\sigma$).**
  - **Métricas Reales Verificadas (1,056,320 transacciones por \$6,257.86M):**
    - **Retiro en Efectivo (`VYBER`):** Media = **\$12,516.73**, Desviación Estándar $\sigma = \mathbf{\$6,593.29}$ ($N = 16,666$, \$208.60M)
    - **Ingreso / Depósito (`PRIJEM`):** Media = **\$7,967.46**, Desviación Estándar $\sigma = \mathbf{\$11,835.60}$ ($N = 405,083$, \$3,227.48M)
    - **Egreso / Gasto (`VYDAJ`):** Media = **\$4,446.75**, Desviación Estándar $\sigma = \mathbf{\$7,375.49}$ ($N = 634,571$, \$2,821.78M)
  - **Fundamento (El Por Qué):** Regla del docente / Cumming et al. (2007): evaluar la dispersión de las operaciones bancarias continuas para dimensionar los límites de control en la operativa de ventanilla y cajeros.
  - **Mapeo Visual (El Cómo):** Eje $X$ = Tipo de Operación bancaria. Eje $Y$ = Monto promedio del movimiento (\$) con bigotes de $\pm 1\sigma$.
* **Gráfico 2: Gráfico de Líneas Múltiples Continuas (1993 a 1998) — Apego Estricto a la Regla 2.**
  - *(Se descarta el área apilada para acatar con exactitud literal la Regla 2 del docente)*.
  - **Métricas:** 3 líneas temporales continuas independientes (una por tipo: Ingreso, Egreso, Retiro en Efectivo) mostrando el volumen anual transaccionado a lo largo de los 6 años.
  - **Fundamento Académico (El Por Qué):** Tufte (1983) y Regla 2 del docente: las líneas continuas sobre fondo plano sin relleno permiten evaluar las tendencias y pendientes relativas de cada canal sin el sesgo perceptual de apilamiento donde las bandas superiores no parten de una línea base cero compartida (Cleveland & McGill, 1984).
  - **Mapeo Visual (El Cómo):** Eje $X$ = Año cronológico (1993–1998). Eje $Y$ = Volumen transaccionado en \$ Millones. Tres líneas con colores corporativos diferenciados, marcadores en cada año y etiquetas de datos directas.

---

### Pestaña 5: P5 · ¿Quién está saturado? — Compromiso de Órdenes y Capacidad de Pago
* **Pregunta de la Carta de Diseño:** *¿Qué clientes presentan órdenes de débito permanente que comprometen críticamente su saldo bancario promedio?*
* **Gráfico 1: Gráfico de Dona Monovariable (5 Categorías Canónicas de `k_symbol`).**
  - **Métricas Reales Verificadas:** Distribución exacta de las 6,471 órdenes por \$21,229,041.00 mensuales:
    | Categoría (`k_symbol`) | Concepto de Negocio | N° Órdenes | % Conteo | Monto Total ($) | % Monto |
    | :--- | :--- | ---: | ---: | ---: | ---: |
    | `SIPO` | Gastos del Hogar / Servicios | 3,502 | 54.12% | \$13,965,417.00 | 65.78% |
    | `SIN_ESPECIFICAR` | Sin símbolo declarado | 1,379 | 21.31% | \$2,781,938.00 | 13.10% |
    | `UVER` | Cuota de Préstamo | 717 | 11.08% | \$3,035,219.00 | 14.30% |
    | `POJISTNE` | Pagos de Seguro | 532 | 8.22% | \$686,927.00 | 3.24% |
    | `LEASING` | Arrendamiento Financiero | 341 | 5.27% | \$759,540.00 | 3.58% |
    | **TOTAL** | | **6,471** | **100.00%** | **\$21,229,041.00** | **100.00%** |
  - **Fundamento Académico (El Por Qué):** Aplicación estricta de la **Regla 3 del docente** y Stephen Few (2007): representa **una única variable** compositiva particionada en exactamente **5 clases legibles** (límite máximo recomendado por Few). En Power BI se grafica por porcentaje de frecuencia de órdenes (SIPO 54.12%, Sin Especificar 21.31%, UVER 11.08%, Seguro 8.22%, Leasing 5.27%) con etiquetas explícitas para eliminar ambigüedades angulares.
* **Gráfico 2: Ranking de Clientes con Mayor Índice de Saturación Financiera.**
  - **Métricas:** Clientes con Índice de Saturación $> 0.5$ ($\text{Índice} = \frac{\text{Monto Mensual de Órdenes}}{\text{Saldo Promedio Histórico}}$).
  - **Fundamento (El Por Qué):** Cleveland & McGill (1984): barras horizontales ordenadas descendentemente para comparar entidades individuales con identificadores alfanuméricos.
  - **Mapeo Visual (El Cómo):** Barras horizontales en rojo alertando a los clientes que superan el umbral de alerta (0.5). El **Cliente 2823 encabeza la tabla nacional con un índice de 2.14** (sus pagos mensuales superan en más del doble su saldo habitual).
* **Interacción:** Drill-through configurado en el cliente: Clic derecho en Cliente 2823 $\rightarrow$ *"Obtener detalles: D2 Ficha Cliente 360"*.

---

### Pestaña 6: P6 · ¿A quién no prestar? — Clientes en Quiebra Histórica (Estado B)
* **Pregunta de la Carta de Diseño:** *¿Quiénes son los clientes con antecedentes de impago histórico y cuáles son sus características sociodemográficas para denegarles nuevo crédito?*
* **Gráfico 1: Gráfico de Columnas por Segmento de Edad y Género de los Clientes Morosos.**
  - **Métricas Reales Verificadas:** 31 clientes únicos en Estado B (\$4.36M defraudados) distribuidos por segmento etario y sexo:
    - Adulto (41-60): 10 F / 6 M (16 casos)
    - Adulto joven (26-40): 4 F / 4 M (8 casos)
    - Joven ($\le 25$): 3 F / 2 M (5 casos)
    - Mayor ($> 60$): 0 F / 2 M (2 casos)
  - **Rigor Estadístico Formal (Regla de Cochran y Test de Fisher):**
    1. **Tabla Sexo vs Estado B ($2 \times 2$):** Frecuencias esperadas en B son 15.82 (F) y 15.18 (M), ambas $> 5$ (cumple regla de Cochran). El **Test Exacto de Fisher (2x2)** da $\text{OddsRatio} = 0.8518, \mathbf{p = 0.7156}$ ($\chi^2 = 0.0629, p = 0.8020$). No existe asociación entre sexo e impago.
    2. **Tabla Segmento Edad vs Estado B ($2 \times 4$):** Las frecuencias esperadas en Estado B para jóvenes ($4.91$) y mayores ($1.09$) son $< 5$, violando el criterio de Cochran (25% de celdas con esperado $< 5$).
    3. **Solución Metodológica Aplicada:**
       - Se calcula el **G-Test (Likelihood Ratio):** $G = 1.9146, p = 0.5903$.
       - Se colapsa la tabla a $2 \times 2$ ($\le 40$ años vs $> 40$ años), donde todas las celdas esperadas superan 14.5, y se aplica el **Test Exacto de Fisher (2x2)**: $\text{OddsRatio} = 1.4952, \mathbf{p = 0.3581}$.
    - **Conclusión de Negocio:** La edad y el género no son factores predictores de siniestralidad crediticia ($p > 0.35$), por lo que las políticas de crédito deben fundamentarse en solvencia financiera (índice de saturación y scoring) y no en sesgos demográficos discriminatorios.
* **Gráfico 2: Tabla de Interdicción y Bloqueo Crediticio.**
  - **Métricas:** ID Cliente, Nombre de Distrito, Monto del Préstamo Incumplido, Fecha de Liquidación, Saldo Pendiente.
  - **Fundamento (El Por Qué):** Stephen Few (2013): las tablas estructuradas son el mecanismo insustituible cuando el usuario de negocio necesita consultar valores numéricos individuales exactos e identificar sujetos de acción directa (lista negra de rechazo de solicitudes).

---

### Pestaña D1: Detalle Distrito (Página de Destino Drill-through)
* **Mecanismo de Activación:** Se accede haciendo clic derecho sobre cualquier distrito en P2 o P3 $\rightarrow$ *Obtener detalles (Drill-through)*.
* **Contenido Focalizado Verificado (Distrito Karvina · ID 73):**
  - Título dinámico mediante DAX: `"Detalle del distrito: Karvina (north Moravia)"`.
  - **4 KPIs distritales exactos:**
    1. *Cartera Total Distrital:* **\$3,059,820.00** (24 préstamos otorgados).
    2. *Cartera Activa Vigente:* **\$2,313,996.00** (15 préstamos vigentes: 12 en Estado C al día + 3 en Estado D en mora activa).
    3. *Tasa de Morosidad Activa:* **20.00%** (3 préstamos D sobre 15 vigentes; sobre el total de 24 préstamos representa el 12.50%).
    4. *Ratio de Absorción Distrital:* **43.70%** (Cartera de \$3,059,820.00 sobre Depósitos de \$7,002,080.00 en 152 cuentas activas).
  - **Desglose de Estados en Karvina:**
    - Estado A (Cancelado al corriente): 9 créditos (\$745,824.00)
    - Estado B (Incumplido histórico): 0 créditos (\$0.00) $\rightarrow$ Tasa de Incumplimiento Histórico = **0.00%**.
    - Estado C (Vigente al corriente): 12 créditos (\$1,613,124.00)
    - Estado D (Vigente en mora activa): 3 créditos (\$700,872.00)
  - Tabla de Contratos de Préstamo del Distrito: Listado de los 24 créditos con su ID de préstamo, ID de cliente, monto, plazo, estado y cuota mensual.
* **Enlace Siguiente en el Hilo Conductor:** En la tabla de préstamos se identifica el crédito 5447 del **Cliente 2823** (\$541,200). Al hacer clic derecho sobre el Cliente 2823 $\rightarrow$ *Obtener detalles $\rightarrow$ D2 Ficha Cliente 360*.
* **Navegación:** Botón superior *"← Volver al Dashboard General"* con acción nativa de Power BI Desktop.

---

### Pestaña D2: Ficha Cliente 360 (Página de Destino Drill-through)
* **Mecanismo de Activación:** Se accede desde la tabla de D1, desde el ranking de P5 o desde P6 $\rightarrow$ *Obtener detalles (Drill-through)*.
* **Contenido Focalizado Verificado (Cliente 2823 · Cuenta 2335):**
  - Título dinámico mediante DAX: `"Ficha 360 · Cliente 2823 (Cuenta 2335 | 52 años | Karvina | north Moravia)"`.
  - **Tarjetas de Perfil:**
    - Edad exacta al corte (31/12/1998): **52 años** (nacida el 18/12/1946).
    - Sexo: Femenino.
    - Distrito: Karvina.
    - Disposición: Titular única (`OWNER`).
  - **Tarjetas Crediticias:**
    - Préstamo Activo: ID 5447 por **\$541,200.00** a 60 meses (cuota mensual \$9,020.00, Estado D - Mora Activa irremediable).
    - Débito mensual por órdenes automáticas: **\$14,286.00 / mes** (5 órdenes fijas en 4 categorías).
    - Índice de Saturación Financiera: **2.14x** (las órdenes mensuales superan en más del doble su saldo promedio global de \$6,678).
    - Saldo final de la cuenta al corte (31/12/1998): **-\$2,803.00** (quiebra técnica, con sobregiro histórico extremo de -\$17,030.00 alcanzado en 1997).
  - **Gráfico de Líneas de Saldos de la Cuenta 2335 (329 movimientos entre 1996 y 1998):**
    - Muestra la trayectoria temporal continua contrastando el **Saldo de Cierre Anual (al 31 de diciembre)** y el **Saldo Promedio Anual**:
      * **Año 1996 (66 tx):** Saldo Cierre = **\$12,867.00** | Saldo Promedio = **\$25,368.17**
      * **Año 1997 (128 tx):** Saldo Cierre = **\$1,162.00** | Saldo Promedio = **\$3,354.26** (Desembolso del crédito en nov-1997 detona el déficit)
      * **Año 1998 (135 tx):** Saldo Cierre = **-\$2,803.00** | Saldo Promedio = **\$722.56** (Insolvencia definitiva)
  - **Tabla de Órdenes de Débito Automático:** Detalle de sus 5 órdenes (4 categorías) que totalizan \$14,286 mensuales (\$9,020 cuota crédito, \$2,036 servicios hogar, \$2,745 conceptos sin especificar en 2 órdenes, \$485 seguro).
  - Diagnóstico Automático en Tarjeta: `"DICTAMEN DEL COMITÉ DE RIESGOS: Insolvencia severa. Cuota de préstamo + débitos fijos superan el flujo de ingresos. Ejecución coactiva de garantías."`
* **Navegación:** Botón superior *"← Volver"*.

---

## 5. COMPARATIVA DE MOTORES: IMPLEMENTACIÓN TÉCNICA Y PERSISTENCIA POLÍGLOTA

El proyecto materializa la persistencia políglota a partir del **Data Warehouse Kimball completado**, el cual se migra hacia MongoDB garantizando concordancia $\Delta = \$0.00$.

### 5.1 Implementación en SQL Server (Arquitectura Dimensional Kimball Completada)
1. **Esquema en Constelación (*Galaxy Schema*):**
   - Dos tablas de hechos transaccionales puras: `Fact_Prestamos` (682 filas) y `Fact_Ordenes` (6,471 filas).
   - Cuatro dimensiones conformadas: `Dim_Distrito`, `Dim_Cliente`, `Dim_Cuenta`, `Dim_Tiempo`.
   - Tres dimensiones de catálogo de baja cardinalidad (SCD Tipo 0): `Dim_Estado_Prestamo`, `Dim_Orden`, `Dim_Operacion`.
2. **Optimización de Desempeño y Medidas Semiaditivas mediante Vistas SQL:**
   - **Manejo de Semiaditividad de Saldos (`vw_PBI_Saldo_Final_Cuenta`):** En Kimball, el saldo bancario no se puede sumar a través del tiempo. Se materializó una vista que toma exclusivamente el último movimiento registrado de cada una de las 4,500 cuentas al corte del 31/12/1998. Control exacto: **\$197,140,434.00**.
   - **Agregación Transaccional Precalculada (`vw_PBI_Trans_Anual_Cuenta`):** Para evitar que Power BI colapse al importar 1,056,320 registros brutos, la vista pre-agrega por cuenta, año y tipo de operación, reduciendo el volumen a 54,298 registros. Para preservar el cálculo exacto de la desviación estándar muestral en DAX, la vista incluye `monto_total`, `num_transacciones` y `suma_cuadrados` ($\sum x^2$). Control: **\$6,257,862,197.00**.
3. **Formulación DAX Estandarizada:**
   ```dax
   // Métrica Semiaditiva de Captación
   Saldo Depositos = SUM(vw_PBI_Saldo_Final_Cuenta[saldo_final])
   
   // Ratio de Absorción Institucional
   Ratio Absorcion = DIVIDE(
       CALCULATE([Cartera Total], REMOVEFILTERS(Dim_Anio), REMOVEFILTERS(Dim_Tiempo)),
       [Saldo Depositos]
   )
   
   // Desviación Estándar Muestral Exacta desde Agregación
   Desv Est Transaccion = 
       VAR n = [Num Transacciones]
       VAR s = [Volumen Transaccionado]
       VAR sq = SUM(vw_PBI_Trans_Anual_Cuenta[suma_cuadrados])
       RETURN SQRT(DIVIDE(sq - s * s / n, n - 1))
   ```

### 5.2 Implementación en MongoDB (Persistencia NoSQL Documental Generada desde Kimball)
1. **Derivación Documental desde Kimball:**
   - A partir del modelo Kimball completado, el script de migración estructuró colecciones documentales optimizadas en MongoDB (`cuentas`, `clientes`, `prestamos`, `transacciones`).
2. **Cómputo en el Servidor mediante *Aggregation Pipeline*:**
   - En lugar de transferir 1.05M de documentos a Power BI, se ejecutan agregaciones nativas (`$sort`, `$group`, `$project`) dentro del motor MongoDB.
   - El último saldo de cada cuenta se resuelve en Mongo con `$last` sobre los balances ordenados cronológicamente.
   - El script conector en Python (`scripts/26_powerbi_mongo_dashboard.py`) entrega a Power BI las 7 tablas equivalentes (`m_prestamos`, `m_ordenes`, `m_trans_anual`, `m_saldo_cuenta`, `m_distritos`, `m_clientes`, `m_anios`), logrando **conciliación matemática perfecta ($\Delta = \$0.00$)**.
3. **Gobernanza con `$jsonSchema`:**
   - Se validaron tipos de datos (`double`, `string`, `int`) y restricciones de nulidad en MongoDB para garantizar integridad referencial documental.

---

## 6. TABLA DE TRANSICIÓN METODOLÓGICA (CARTA V3 VS CARTA V6 / KIMBALL V2)

Para blindar la exposición ante cualquier pregunta sobre discrepancias entre borradores preliminares de la cátedra (v3) y la solución final (v6), se documenta la reconciliación técnica verificada:

| Concepto / Métrica | Valor Preliminar (Carta v3) | Valor Definitivo (Carta v6 / Kimball v2) | Justificación Técnica y Metodológica Verificada en Código |
| :--- | :--- | :--- | :--- |
| **Población de Clientes** | 5,369 clientes sin distinción | **4,500 Clientes Titulares (`OWNER`) / 5,369 Clientes Totales** | En v3 se mezclaron indistintamente los titulares de cuenta (`OWNER`) con los apoderados autorizados (`DISPONENT`, 869 personas). La responsabilidad legal y patrimonial de los créditos y órdenes recae exclusivamente en los titulares `OWNER` de las 4,500 cuentas. |
| **Tratamiento del Saldo (Depósitos)** | Sumas parciales de transacciones | **\$197,140,434.00 (Medida Semiaditiva al 31/12/1998)** | En v3 se cometía el error común en OLAP de sumar los saldos de transacciones a través de la dimensión tiempo. En v6 se corrigió implementando el corte semiaditivo estricto de Ralph Kimball. |
| **Tratamiento del Distrito 69 (Jesenik)** | Faltantes `'?'` en desempleo y crimen | **Imputación por K-Means ($k=9$, 50 reinicios) + Mediana de Cluster** | En la fuente cruda (`district.csv`), Jesenik tenía valores `'?'`. En `etl_populate_kimball_v2.py` se cargó como `NULL` para integridad. En el pipeline analítico (`scripts/imputar_final.py`), se aplicó **K-Means clustering** con población, salario y región como predictores, imputando la **mediana del Cluster 6: Desempleo = 5.0%, Criminalidad = 3,736**. |
| **Tasa de Morosidad** | 6.60% (sobre cartera histórica total) | **10.0446% (sobre Cartera Vigente C+D) / 13.2478% (Incumplimiento B sobre A+B)** | En v3 se calculaba una tasa de mora global cruda ($45/682 = 6.60\%$). Metodológicamente en banca, la morosidad activa se mide **únicamente sobre créditos vigentes** ($45/448 = 10.04\%$), y el riesgo histórico se mide sobre **créditos cerrados** ($31/234 = 13.25\%$). |
| **ANOVA de Montos por Región** | $p = 0.886$ (sin F reportado) vs $F=1.17, p=0.32$ (plazos) | **$F = 0.1210, \quad p = 0.8861$ (Monto de Préstamo oficial)** | Verificado en Python/SQL sobre los 682 contratos de `Fact_Prestamos`. El valor de $p=0.8861$ es exacto para el monto colocado entre macro-regiones, confirmando la validez del solapamiento visual $\pm 1\sigma$. |
| **Ratio de Absorción de Karvina** | 48.2% / 47.7% (aproximación distrital) | **43.70% (Cartera \$3.06M / Depósitos \$7.00M)** | Calculado formalmente sobre las 152 cuentas bancarias reales de Karvina y sus saldos finales al 31/12/1998. |

---

## 7. CUESTIONARIO DE AUDITORÍA EXTERNA: PREGUNTAS CLAVE PARA LA OTRA IA

Por favor, como Inteligencia Artificial revisora y auditora, analiza a fondo todo el contenido anterior y responde puntualmente a los siguientes 6 bloques de preguntas:

### Bloque 1: Coherencia y Storytelling del Hilo Conductor
1. ¿Consideras que la cadena articulada de preguntas de negocio (P1 $\rightarrow$ P2 $\rightarrow$ D1 $\rightarrow$ D2 $\rightarrow$ P4 $\rightarrow$ P5 $\rightarrow$ P6) satisface con contundencia la exigencia del docente de evitar "dashboards dispersos por tabla"?
2. ¿El caso forense seleccionado (Distrito Karvina $\rightarrow$ Cliente 2823 de 52 años $\rightarrow$ 5 órdenes por \$14.3K $\rightarrow$ saldo negativo $-\$2,803$ $\rightarrow$ índice de saturación 2.14) resulta natural, pedagógico y convincente para una presentación ejecutiva de 5 minutos?

### Bloque 2: Selección Gráfica y Fundamentación Psico-Física
3. Evalúa la idoneidad de sustituir el clásico Treemap en P2 por un Scatter/Bubble Plot de distritos ($X=\text{Cartera}$, $Y=\text{Tasa Mora}$, $\text{Size}=\text{Préstamos}$). ¿Es académicamente superior bajo los principios de Cleveland & McGill (1984) y Munzner (2014)?
4. ¿El uso de líneas múltiples continuas en P4 (descartando el área apilada) y la dona monovariable de 5 clases en P5 garantizan un cumplimiento blindado de las Reglas 2 y 3 del docente y los principios de Stephen Few y Edward Tufte?

### Bloque 3: Rigor Estadístico e Inferencial
5. Respecto a la inferencia estadística del proyecto:
   - ¿Es matemáticamente inobjetable el resultado de ANOVA ($F = 0.1210, p = 0.8861$) para justificar la regla del docente del solapamiento de barras $\pm 1\sigma$ en montos de crédito?
   - ¿Cómo evalúas la aplicación de la regla de Cochran (1954) y el Test Exacto de Fisher (2x2, $p = 0.3581$ y $p = 0.7156$) en P6 para demostrar formalmente la independencia de edad y género frente al impago histórico?

### Bloque 4: Persistencia Políglota y Desempeño Técnico
6. ¿La estrategia de pre-agregación en SQL Server (`vw_PBI_Trans_Anual_Cuenta` con suma de cuadrados) y el uso de *Aggregation Pipeline* nativo en MongoDB para mitigar el cuello de botella de 1.05M transacciones representan una solución óptima para el rendimiento de Power BI Desktop?
7. ¿Qué diferencias conceptuales clave entre el modelo en constelación Kimball y el modelo documental embebido NoSQL debemos enfatizar con mayor fuerza durante la defensa oral?

### Bloque 5: Simulación de la Defensa Oral y Preguntas Capciosas del Jurado
8. Si tú fueras el docente evaluador más exigente de la cátedra de Inteligencia de Negocios, ¿cuáles serían **las 3 preguntas más difíciles, técnicas o capciosas** que formularías al equipo durante la sustentación, y cuál es la respuesta exacta que deberíamos dar para obtener una calificación perfecta (10/10)?

### Bloque 6: Recomendaciones de Mejora y Oportunidades de Pulido
9. ¿Identificas algún ángulo muerto, riesgo no cubierto o mejora visual/funcional que convendría incorporar en los archivos `.pbix` antes de la entrega final?
