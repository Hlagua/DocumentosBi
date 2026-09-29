# UNIVERSIDAD TÉCNICA DE AMBATO
## FACULTAD DE INGENIERÍA EN SISTEMAS, ELECTRÓNICA E INDUSTRIAL
### CARRERA DE SOFTWARE — ASIGNATURA: INTELIGENCIA DE NEGOCIOS
### CICLO ACADÉMICO: AGOSTO 2026 – DICIEMBRE 2026

---

# GUÍA 07 — DISEÑO DEL DASHBOARD ARTICULADO EN POWER BI (KIMBALL Y MONGODB)

**Autores:** Alison Marcela Cobos Taco / Henry Daniel Lagua Flores  
**Docente:** Ing. Ruben Nogales, Mg.  
**Versión:** 4.0 (28/09/2026) — rediseño a partir de la Carta de Diseño v8, del Data Mart cargado y verificado (Informes 09 y 10), de la réplica MongoDB (Informe 05) y de la investigación de gráficos de Power BI realizada por el equipo  
**Entregables:** `dashboards/Dashboard_Financial_Kimball` y `dashboards/Dashboard_Financial_Mongo` (proyectos `.pbip` idénticos en diseño, distinta fuente)

> **Qué cambia respecto a la versión 3.1.** La v3.1 respondía las preguntas de la Carta anterior. La Carta v8 cambió tres cosas que el tablero debe mostrar: (1) la mora crece por **volumen**, no por deterioro; (2) el impago depende de la **capacidad de pago**; (3) la liquidez se mide sobre la **cartera vigente** (40.73%, no 52.38%) con un saldo **mensual** y sin ambigüedad. Además, el Data Mart ahora tiene la foto mensual de saldos, las 4 categorías de operación, el concepto completado de cada transacción, la capacidad de pago y las recomendaciones del Informe 04.

---

## 1. PRINCIPIOS DEL DISEÑO

Cada decisión de este tablero se toma por una de estas razones. Si un elemento no se puede justificar con alguna, no entra.

| # | Principio | Consecuencia en el tablero | Fundamento |
| :-: | :--- | :--- | :--- |
| P1 | **Todo responde a la Carta de Diseño** | Cada página responde una pregunta de la Carta v8 y cada visual tiene una fila en la matriz de trazabilidad (sección 5). | Kimball y Ross (2013): el modelo sirve a procesos y preguntas de negocio |
| P2 | **La posición es el canal más preciso** | Comparaciones con columnas sobre un eje común que empieza en cero; ángulos y áreas solo cuando la pregunta es "qué parte del total" o "qué es lo más grande". | Cleveland y McGill (1984) |
| P3 | **El color se usa poco y siempre significa lo mismo** | Solo hay color donde codifica algo (estado del préstamo, alerta, intensidad). Lo demás va en gris. | Few (2012); Ware (2012) |
| P4 | **Legible para personas con daltonismo** | Paleta de Okabe e Ito, distinguible con deuteranopía y protanopía; nunca rojo frente a verde como única diferencia. | Okabe e Ito (2008); Wong (2011) |
| P5 | **Primero el estado general, después el detalle** | Cabecera de KPIs arriba a la izquierda; lectura en Z; máximo 6 visuales por página además de la cabecera. | Few (2006) |
| P6 | **El título dice la conclusión** | Cada visual lleva un título que responde (p. ej. "La tasa de mora no cambia por año: la colocación sí"), no solo el nombre del gráfico. | Knaflic (2015) |
| P7 | **Honestidad estadística** | Tasas con su intervalo; promedios con ±1σ y su error estándar en el tooltip; la significancia se afirma solo con prueba (Informe 04 y script 27). | Cumming y Finch (2005); Cumming, Fidler y Vaux (2007) |
| P8 | **No se inventan metas** | La Carta no fija objetivos numéricos; las referencias son el promedio del banco o el periodo anterior, nunca una "meta" supuesta. | Carta v8, sección 2 |

---

## 2. LAS REGLAS DEL ING. NOGALES Y CÓMO SE CUMPLEN

Tomado de la investigación del equipo y verificado contra el diseño de esta guía:

| # | Regla | Cómo se cumple aquí |
| :-: | :--- | :--- |
| 1 | Eje X categórico, eje Y numérico | Se usan **columnas** (no barras horizontales): las categorías quedan en el eje X. Única excepción justificada: ninguna. |
| 2 | Series temporales con líneas | Toda evolución (año o mes) va en líneas. En P1 se combina con columnas (volumen) porque son dos escalas distintas. |
| 3 | Desviación estándar en comparativas grandes | Promedios de muchos datos (ticket de transacción, monto de préstamo) con **barras de error ±1σ**. Las **tasas** usan el intervalo de **Wilson** equivalente a ±1 error estándar (ver 6.3). Las barras de error solo existen en columnas agrupadas, líneas y el combinado; por eso esos visuales se eligen donde hay que mostrarlas. |
| 4 | Pastel: una variable, en porcentajes | Solo **dos anillos**, cada uno con una variable y ≤ 5 clases, etiquetas en % del total: órdenes por propósito (P5) y estado de los préstamos del distrito (D1). |
| 5 | Nada de 3D | Power BI no trae 3D nativo; no se instala ningún visual 3D de AppSource. |
| 6 | Cabeceras con los valores | Cada página abre con **una tarjeta de varias tarjetas** (visual "Tarjeta" nuevo) con los números de la pregunta y su valor de referencia. |
| 7 | Gráfico de jerarquía cuando hay mucha información | **Treemap** región → distrito en P2: área = cartera vigente, color = tasa de mora. |
| 8 | Todas las categorías en todos los años | **Matriz año × categoría** con *Mostrar elementos sin datos* en P1 (estado del préstamo) y P4 (categoría de operación), con escala de color de fondo. Los años del dataset son 1993–1998. |
| 9 | `CALCULATE` junto con `FILTER` | Medidas del modelo que usan `CALCULATE` con `FILTER` cuando la condición depende de otra medida (sección 7). |

El ejemplo del Ing. ("producto más vendido → su proveedor → lo que ofrece ese proveedor") se implementa con el **árbol de descomposición** de P2 y con los *drill-through* a D1 y D2: **mora → región → distrito → cliente → qué más tiene y qué ofrecerle**.

---

## 3. DECISIONES DE DISEÑO

| Decisión | Elegido | Alternativas descartadas | Fundamento |
| :--- | :--- | :--- | :--- |
| **Segmentación de edad** | **3 grupos del Data Mart**: Joven (< 30), Adulto (30–50), Adulto Mayor (> 50) — `Dim_Cliente[segmento_edad]` | 4 grupos calculados en DAX (≤ 25, 26–40, 41–60, > 60) | (1) Una sola definición en el Data Mart (fuente única, la misma del Informe 04). (2) Con 4 grupos, el grupo > 60 tiene solo 10 préstamos cerrados y 2 celdas quedan con frecuencia esperada < 5 (regla de Cochran incumplida). Con 3 grupos, los tres tienen 56 a 107 préstamos cerrados y ninguna celda < 5 (χ² = 2.28, p = 0.32). |
| **Recomendaciones del Informe 04** | **Sí**, en la ficha del cliente (D2) | Página propia de recomendaciones | La Carta v8 quiere mejorar el otorgamiento con la capacidad de pago: la ficha muestra el top 3 del recomendador y, si incluye préstamo, la cuota y el monto máximo prudentes. Cierra el ciclo "analizar → actuar". No se hace una página aparte porque no hay una pregunta de la Carta sobre recomendaciones. |
| **KPI de liquidez** | **Ratio de absorción de cartera vigente (40.73%)** | Cartera total / saldo (52.38%) | Los préstamos cerrados ya no inmovilizan fondos (Carta v8, sección 7). El 52.38% aparece solo en el tooltip como referencia histórica. |
| **Saldo en el tiempo** | Foto mensual (`Fact_Saldo_Cuenta_Mensual`): **saldo promedio por cuenta activa** y saldo total | Suma de `saldo_cuenta` de las transacciones | El saldo es semiaditivo; sumar movimientos no tiene sentido. Además, el saldo total crece de $0.66M (enero 1993) a $197.14M (diciembre 1998) sobre todo porque se abren cuentas: mostrar solo el total sugiere un crecimiento que no es por cliente. |
| **Intervalo de las tasas** | **Wilson** con z = 1 (equivalente a ±1 EE) | ±1 EE de Wald recortado en 0 | Con tasas cercanas a 0 (north Bohemia 0/41, banda Baja 5/171) el intervalo de Wald colapsa a ancho 0 y aparenta certeza total. Wilson da un intervalo con sentido (Wilson, 1927; Agresti y Coull, 1998). |
| **Metas en los KPI** | Referencias: **promedio del banco** o **año anterior** | "Meta de mora ≤ 8%" | La Carta no define metas; inventarlas quitaría seriedad a la defensa (principio P8). |
| **Mapas geográficos** | No | Mapa, Azure Maps | Los nombres de los 77 distritos checos se geolocalizan mal sin archivo de formas; el treemap y las columnas responden lo mismo sin ese riesgo. |
| **Visuales de IA** | Solo el **árbol de descomposición** | Influenciadores clave, narrativa inteligente | El árbol solo reorganiza medidas calculadas. Los influenciadores clave "descubren" factores con 31 casos de impago que las pruebas no confirman (edad p = 0.32, sexo p = 0.70). |
| **Previsión y anomalías** | No | Panel Análisis → Previsión | Los datos terminan en 1998: no hay nada que prever para la gerencia de este caso. |

---

## 4. SISTEMA VISUAL

### 4.1 Paleta (Okabe e Ito, apta para daltonismo)

| Uso | Color | Código | Por qué este color |
| :--- | :--- | :--- | :--- |
| Estado **A** — cerrado, pagado | Azul | `#0072B2` | **Tono frío = situación en regla**; oscuro = cerrado |
| Estado **C** — vigente, al día | Celeste | `#56B4E9` | Tono frío, claro = vigente |
| Estado **B** — cerrado, con deuda | Bermellón | `#D55E00` | **Tono cálido = problema**; oscuro = cerrado |
| Estado **D** — vigente, en mora | Naranja | `#E69F00` | Tono cálido, claro = vigente |
| **Alerta** (sobre el umbral: índice > 1, banda Alta, tasa sobre el banco) | Bermellón | `#D55E00` | El mismo color del impago: "esto es riesgo" en todo el tablero |
| Contexto, referencias, series sin categoría | Gris | `#7F7F7F` | No compite con lo que sí tiene significado |
| Texto | Gris oscuro | `#333333` | Contraste alto sin la dureza del negro puro |
| Escala continua (mapa de calor, color del treemap) | Blanco → bermellón | `#FFFFFF` → `#D55E00` | Un solo tono que aumenta con el valor: más oscuro = más riesgo (Brewer, 2003) |
| Bandas de capacidad (ordinal: Baja < Media-baja < Media-alta < Alta) | 4 pasos de bermellón | `#FBE3D3`, `#F2B48C`, `#E5813F`, `#D55E00` | Ordinal → escala secuencial, no colores distintos |
| Propósito de las órdenes (anillo, 5 clases nominales) | Verde azulado, púrpura, amarillo, negro y **gris claro para "Sin especificar"** | `#009E73`, `#CC79A7`, `#F0E442`, `#000000`, `#C8C8C8` | Colores de Okabe e Ito no usados por los estados; el dato no especificado va en gris por convención |

**Lectura de la paleta de estados:** el **tono** dice si hay problema (frío/cálido) y la **luminosidad** si el préstamo está cerrado u abierto. Así, sin leyenda, se ve que naranja y bermellón son "problemas" y que el naranja es el que todavía se puede cobrar.

Las regiones, operaciones y segmentos **no** llevan color: ya están nombrados en el eje. Colorearlos sería redundante y agotaría la paleta (Few, 2012).

### 4.2 Tipografía, lienzo y formato

| Elemento | Especificación | Fundamento |
| :--- | :--- | :--- |
| Lienzo | 1280 × 720 px (16:9) | Tamaño predeterminado de Power BI y de proyectores |
| Fuente | Segoe UI (predeterminada de Power BI) | Disponible en todo Windows; no hay que incrustar fuentes |
| Título de página | 14 pt en **una línea**, la **pregunta** de la Carta (la de P5 tiene 125 caracteres: a 18 pt no cabe sin tapar la navegación) | P1 y P6 |
| Título de visual | 12 pt, la **respuesta** | Knaflic (2015) |
| Etiquetas y ejes | 10 pt; sin cuadrícula secundaria; eje Y desde 0 en columnas | Tufte (2001): menos tinta que no es dato |
| Números | Moneda `$#,0` (tarjetas en millones con 2 decimales); tasas `0.00%` (las mismas cifras que citan la Carta y los informes: 10.04%, 13.25%); conteos `#,0` | Coherencia entre páginas y documentos |
| Distribución | Fila 1: pregunta. Fila 2: navegación (7 botones) y segmentadores. Fila 3: cabecera de KPIs. Debajo: visual principal a la izquierda y detalle a la derecha y abajo | Lectura en Z (Few, 2006) |

Estos valores se guardan en `tema_financial.json`, **incrustado en cada informe** (`StaticResources/RegisteredResources`) y copiado junto al `.pbip`. Los colores con significado (estados, bandas, alertas, propósitos, referencias en gris) se fijan además en cada visual, para que no dependan del tema.

---

## 5. PÁGINAS Y MATRIZ DE TRAZABILIDAD

Nueve páginas: **Inicio**, seis de preguntas (**P1–P6**, una por pregunta de la Carta v8) y dos de detalle por *drill-through* (**D1** distrito, **D2** cliente). Todas comparten los segmentadores **Año** y **Macro-región** (botones, sincronizados).

### Inicio — "¿Cómo está el banco?"

| Visual | Gráfico | Contenido | Por qué |
| :--- | :--- | :--- | :--- |
| Cabecera | Tarjeta (varias tarjetas) | Tasa de mora vigente 10.04% · Incumplimiento 13.25% · Cartera vigente $80.30M · Saldo neto $197.14M · Absorción vigente 40.73% · Cuentas en sobregiro 39 | Los 6 números que resumen los 3 problemas (regla 6) |
| Problemas | Cuadros de texto | Los 3 problemas de la Carta v8 en una línea cada uno | Contexto antes de navegar |
| Navegación | 6 botones | Uno por pregunta (P1–P6) | Articulación entre páginas |

### P1 — ¿Cómo evolucionan la cantidad y la tasa de mora por año de otorgamiento?

| Visual | Gráfico | Configuración | Por qué este gráfico |
| :--- | :--- | :--- | :--- |
| Cabecera | Tarjeta | Préstamos 682 · En mora 45 · Tasa vigente 10.04% · Incumplimiento 13.25% | Regla 6 |
| **Principal** | **Líneas y columnas** | Eje X: año de otorgamiento. Columnas (gris): préstamos otorgados. Línea (naranja): tasa de mora de la cosecha con **barras de error Wilson**. | Muestra en un solo visual el hallazgo del problema 1: **las columnas suben (101 → 196), la línea no (12.2%–15.4%, χ² p = 0.93)**. Dos escalas distintas → combinado (regla 2). |
| Composición | Matriz año × estado | Filas: año; columnas: A, B, C, D; valores: número de préstamos; fondo con escala blanco → bermellón; *mostrar elementos sin datos* | Regla 8: todas las categorías en todos los años |
| Nota | Cuadro de texto | "1998: préstamos recientes, aún sin tiempo para caer en mora (2.5%)" | Limitación declarada en la Carta v8 |

### P2 — ¿Qué regiones y distritos concentran la cartera y la mora?

| Visual | Gráfico | Configuración | Por qué |
| :--- | :--- | :--- | :--- |
| Cabecera | Tarjeta | Región con más mora · Distrito con más morosos · Tasa del banco 10.04% | Regla 6 |
| **Principal** | **Árbol de descomposición** | Analizar: préstamos en mora. Explicar por: región → distrito → cliente, con "valor más alto" | Es el ejemplo del Ing. llevado a nuestros datos: north Moravia (12) → Karvina (3) → los clientes en mora |
| Jerarquía | Treemap | Categoría: región; Detalles: distrito; Valores: cartera vigente; color: tasa de mora (blanco → bermellón); etiquetas en % | Regla 7: el área dice "cuánto" y el color "qué tan riesgoso" |
| Comparación | Columnas | Eje X: región (orden descendente); Y: tasa de mora con **Wilson**; línea constante: tasa del banco | Comparación precisa que el treemap no permite (P2). north Moravia 15.8% es la más alta; north Bohemia 0/41 |
| Tabla | Tabla con formato condicional | Distritos: préstamos vigentes (*n*), en mora, tasa; barra de datos en la tasa | Regla de muestra mínima de la Carta v8: la tasa de un distrito siempre con su *n* (70 de 77 distritos tienen < 10 vigentes) |

*Drill-through* a D1 desde cualquier distrito. **Tooltip de página** "TT Distrito" (cartera, mora, absorción) al pasar el mouse.

### P3 — ¿Qué proporción del saldo está comprometida en la cartera vigente y cómo evoluciona el saldo?

| Visual | Gráfico | Configuración | Por qué |
| :--- | :--- | :--- | :--- |
| Cabecera | Tarjeta | Absorción vigente 40.73% (referencia: 52.38% con cartera total, en el tooltip) · Cartera vigente $80.30M · Saldo neto $197.14M · Saldo por cobrar estimado $46.62M | Regla 6; KPI de la Carta v8 |
| **Principal** | **Columnas** | Eje X: región (orden descendente); Y: ratio de absorción vigente; **línea constante 40.73%** (promedio del banco) | Quién está sobre el promedio: east Bohemia 51.6% la más expuesta; north Bohemia 28.2% la más holgada |
| Evolución | Líneas | Eje X: mes (1993–1998); Y: **saldo promedio por cuenta activa**; tooltip: saldo total y cuentas activas | Regla 2 con la medida correcta: el total solo crece porque se abren cuentas |
| Composición | Cascada | Saldo neto → cartera vigente → liquidez libre | Explica visualmente el 40.73% (suma y resta) |

### P4 — ¿Qué operaciones concentran el flujo, cómo varía el saldo promedio y cuántas cuentas caen en sobregiro?

| Visual | Gráfico | Configuración | Por qué |
| :--- | :--- | :--- | :--- |
| Cabecera | Tarjeta | Volumen $6.26B · Movimientos 1,056,320 · Ticket promedio · Cuentas en sobregiro (último mes) | Regla 6 |
| **Principal** | **Columnas** | Eje X: categoría analítica (4); Y: ticket promedio con **±1σ**; tooltip: error estándar | Regla 3: miles de movimientos por categoría |
| Evolución | Líneas con **múltiplos pequeños** | Un panel por categoría; eje X: año; Y: volumen | Cuatro series sin enredarse (Tufte, 2001) y sin necesidad de colores |
| Todas las categorías | Matriz año × categoría | Volumen con fondo en escala | Regla 8 |
| Sobregiro | Líneas | Eje X: mes; Y: cuentas con saldo negativo al cierre del mes | Pregunta 4 de la Carta v8 (193 cuentas pasaron por sobregiro; máximo 43 en noviembre de 1998) |

### P5 — ¿Qué cuentas comprometen en cuotas y órdenes fijas una proporción alta de su saldo, incluidas deudas con otras entidades?

| Visual | Gráfico | Configuración | Por qué |
| :--- | :--- | :--- | :--- |
| Cabecera | Tarjeta | Compromiso mensual $21.23M · Órdenes 6,471 · Cuentas con índice > 0.5: 47 · Cuentas con crédito externo: 35 | Regla 6 |
| **Principal** | **Dispersión** | X: saldo promedio de la cuenta; Y: órdenes mensuales; un punto por cuenta; **sombreado de simetría** (Análisis); puntos con índice > 1 en bermellón | El índice de saturación se *ve*: sobre la diagonal, la cuenta compromete más de lo que suele tener. La cuenta 2335 (cliente 2823, índice 2.14) queda sola |
| Composición | **Anillo** | Órdenes por propósito (5 clases) en % | Regla 4: una variable, ≤ 5 clases |
| Alerta | Tabla | Cuentas con índice > 0.5: índice con **icono de semáforo** (> 1 bermellón, > 0.5 naranja), órdenes, saldo, crédito externo | Lista de acción para cobranza temprana |

### P6 — ¿Qué clientes tienen impago histórico y en qué medida la capacidad de pago previa lo anticipa?

| Visual | Gráfico | Configuración | Por qué |
| :--- | :--- | :--- | :--- |
| Cabecera | Tarjeta | Clientes con impago (B) 31 · Impago banda Baja 2.9% · Impago banda Alta 23.3% · Monto original en riesgo B + D $15.58M | Regla 6 y problema 2 de la Carta |
| **Principal** | **Columnas** | Eje X: banda de capacidad (Baja → Alta); Y: tasa de impago (B o D) con **Wilson**; colores de la escala ordinal | El hallazgo más fuerte del proyecto: impago de 2.9% a 23.3% (χ² = 38.58, p < 0.001) |
| Contraste | Columnas | Eje X: segmento de edad (3); Y: tasa de incumplimiento con Wilson | Muestra que la edad **no** separa el impago (χ² p = 0.32): se decide por capacidad, no por perfil demográfico |
| Lista | Tabla | Clientes con préstamo B: distrito, monto, banda de capacidad | Lista de denegación de la Carta |

### D1 — Detalle del distrito (*drill-through* desde P2)

| Visual | Gráfico | Contenido |
| :--- | :--- | :--- |
| Título dinámico | Tarjeta | "Distrito: Karvina (north Moravia)" |
| Cabecera | Tarjeta de varias filas | Préstamos, vigentes, en mora, cartera vigente, saldo, absorción; población, salario, desempleo (marca de imputado si aplica) |
| Estado | **Anillo** | Préstamos por estado A/B/C/D en % (colores de estado) |
| Evolución | Líneas | Saldo promedio por cuenta del distrito por mes, frente al del banco en gris |
| Tabla | Tabla | Préstamos del distrito con estado, cuota y banda de capacidad; *drill-through* a D2 |

### D2 — Ficha Cliente 360 (*drill-through* desde P2, P5, P6 o D1)

| Visual | Gráfico | Contenido |
| :--- | :--- | :--- |
| Título dinámico | Tarjeta | "Cliente 2823 · Cuenta 2335" |
| Perfil | Tarjeta de varias filas | Edad, segmento, arquetipo, distrito, rol, calificación de pago |
| Situación | Tarjeta de varias filas | Préstamo (monto, cuota, estado, banda de capacidad), órdenes mensuales, índice de saturación, crédito externo |
| Evolución | Líneas | Saldo al cierre de cada mes (foto mensual) con línea constante en 0 (sobregiro) |
| Órdenes | Tabla | Órdenes de la cuenta por propósito |
| **Qué ofrecerle** | Tabla | Top 3 del recomendador (Informe 04) y, si hay préstamo, cuota y monto máximo prudentes |

### Matriz de trazabilidad

| Problema (Carta v8) | Pregunta | Página | Visual principal | Medida o prueba que sustenta el título |
| :--- | :-: | :-: | :--- | :--- |
| 1. Impago y mora por volumen | 1 | P1 | Líneas y columnas | χ² tasa × año, p = 0.93 |
| 1. Impago y mora | 2 | P2 | Árbol de descomposición + treemap | Tasa por región con Wilson; *n* por distrito |
| 3. Medición de saldos | 3 | P3 | Columnas con línea constante | Ratio de absorción vigente; foto mensual |
| 3. Medición de saldos | 4 | P4 | Columnas ±1σ | ANOVA y η² del ticket (script 27) |
| 2. Capacidad de pago | 5 | P5 | Dispersión con simetría | Índice de saturación |
| 2. Capacidad de pago | 6 | P6 | Columnas por banda con Wilson | χ² = 38.58, AUC = 0.717 (Informe 04) |

---

## 6. MODELO DE DATOS PARA LOS TABLEROS

### 6.1 Kimball

Tablas que importa Power BI (14):
* Dimensiones: `Dim_Tiempo`, `Dim_Anio` (años distintos de `Dim_Tiempo`, para el segmentador), `Dim_Distrito`, `Dim_Cliente`, `Dim_Cuenta`, `Dim_Estado_Prestamo`, `Dim_Orden`.
* Hechos: `Fact_Prestamos`, `Fact_Ordenes`, `Fact_Saldo_Cuenta_Mensual` y la vista `vw_PBI_Trans_Anual_Cuenta` **por categoría analítica** (en lugar de las 15 operaciones), con suma de cuadrados para σ exacta. `Dim_Operacion` y `Dim_Concepto_Movimiento` no se importan: la vista ya trae la categoría.
* `Recomendacion_Cuenta`: top 3 del Informe 04 por cuenta, cargado por `scripts/42_cargar_recomendaciones.py` (tabla del Data Mart, no vista).
* `Composicion_Liquidez`: tabla estática de dos filas para la cascada de P3.
* `Puente_Cuenta_Cliente` **no** se importa: los hechos ya llevan al titular y ningún visual necesita a los cotitulares.

Relaciones: cada hecho → distrito, cliente y cuenta; `Fact_Prestamos` → estado y tiempo (otorgamiento); `Fact_Saldo_Cuenta_Mensual` → tiempo (mes); `Dim_Tiempo` y la vista → `Dim_Anio`; `Fact_Ordenes` → tiempo **inactiva** (la apertura de la cuenta no es la fecha de la orden, por eso el segmentador de año no filtra las órdenes); `Recomendacion_Cuenta` → cuenta y cliente. Las categorías ordinales se ordenan por columnas creadas en Power Query (`Orden Banda`, `Orden Segmento`): una columna calculada DAX derivada de la misma columna produce una dependencia circular en el motor.

La vista `vw_PBI_Saldo_Final_Cuenta` deja de ser necesaria: el saldo al corte sale de la foto mensual.

### 6.2 MongoDB

El conector del script 26 lee las mismas entidades y entrega 10 tablas con **los mismos nombres de columnas y medidas** (`m_distritos`, `m_clientes`, `m_cuentas`, `m_anios`, `m_meses`, `m_prestamos`, `m_ordenes`, `m_trans_anual`, `m_saldo_mensual`, `m_recomendaciones`). El agregado anual por categoría se calcula dentro de MongoDB con `$group`. Las cifras de control del conector coinciden con Kimball: saldo al corte $197,140,434, volumen $6,257,862,197, bandas 171/167/172/172 y segmentos 1,282/1,924/2,163.

### 6.3 Medidas estadísticas

* **Tasas con intervalo de Wilson (z = 1):**
  $$\text{centro} = \frac{p + \frac{z^2}{2n}}{1 + \frac{z^2}{n}} \qquad \text{margen} = \frac{z}{1 + \frac{z^2}{n}}\sqrt{\frac{p(1-p)}{n} + \frac{z^2}{4n^2}}$$
* **Promedios con ±1σ exacta** desde la suma y la suma de cuadrados agregadas; el **error estándar** σ/√n va en el tooltip.
* Todas las cifras de control se contrastan con `scripts/27_evidencia_estadistica_dashboard.py` y con los Informes 04, 09 y 10.

---

## 7. `CALCULATE` Y `FILTER` (REGLA 9)

`CALCULATE` evalúa una expresión cambiando el contexto de filtro; `FILTER` devuelve las filas que cumplen una condición y es **obligatorio** cuando la condición usa una medida o depende del contexto. Medidas del tablero que los usan juntos:

```dax
-- P2: cartera vigente de los distritos cuya tasa de mora supera la del banco
Cartera Distritos Sobre Mora Banco =
    VAR moraBanco = CALCULATE ( [Tasa Mora Vigente], REMOVEFILTERS ( Dim_Distrito ) )
    RETURN
        CALCULATE (
            [Cartera Vigente],
            FILTER ( VALUES ( Dim_Distrito[nombre_distrito] ), [Tasa Mora Vigente] > moraBanco )
        )

-- P5: cuentas cuyo índice de saturación supera 0.5 (la condición es una medida → FILTER)
Cuentas Saturadas =
    COUNTROWS ( FILTER ( VALUES ( Dim_Cuenta[id_cuenta_bk] ), [Indice Saturacion] > 0.5 ) )

-- P6: impago de la banda Alta, respetando otros filtros del usuario (KEEPFILTERS)
Tasa Impago Banda Alta =
    CALCULATE ( [Tasa Impago], KEEPFILTERS ( Fact_Prestamos[banda_capacidad] = "Alta" ) )

-- P3: saldo neto al corte (último mes del contexto) desde la foto mensual
Saldo Neto Corte =
    VAR ultimoMes = CALCULATE ( MAX ( Dim_Tiempo[fecha] ), Fact_Saldo_Cuenta_Mensual )
    RETURN
        CALCULATE ( SUM ( Fact_Saldo_Cuenta_Mensual[saldo_fin_mes] ), FILTER ( ALL ( Dim_Tiempo ), Dim_Tiempo[fecha] = ultimoMes ) )
```

Errores que se evitan: filtrar la tabla de hechos completa con `FILTER` (lento); pisar la selección del usuario con un filtro simple (se usa `KEEPFILTERS`); dividir con `/` en lugar de `DIVIDE`.

---

## 8. INTERACCIÓN

| Herramienta | Uso | Por qué |
| :--- | :--- | :--- |
| Segmentadores **desplegables** (Año, Macro-región), sincronizados | Páginas Inicio y P1–P6 | Mismo filtro en todo el tablero; el desplegable muestra el valor activo. Se probaron botones: 6 años + 3 macro-regiones necesitan ~700 px y no caben junto a la navegación |
| Árbol de descomposición | P2 | Recorrido "el mayor → dentro de ese → …" |
| *Drill-through* | Distrito → D1; cliente → D2; con botón Atrás | Detalle sin perder el contexto |
| Tooltip de página | Distritos (P2, P3) | Detalle sin cambiar de página |
| Marcador "Restablecer filtros" | Botón en la barra | Volver al estado inicial |
| Formato condicional | Semáforo del índice de saturación; mapa de calor en matrices; barras de datos en tasas | Alertas legibles sin leer cada número |

No se usan **parámetros de campo** para cambiar la métrica de un gráfico: cada página responde una pregunta concreta y un selector de métricas cambiaría el significado del título (principio P6).

---

## 9. QUÉ SE TOMÓ DE LA INVESTIGACIÓN DEL EQUIPO Y QUÉ SE CORRIGIÓ

| Se tomó | Se corrigió o descartó |
| :--- | :--- |
| Tabla de reglas del Ing. y su implementación en Power BI (sección 2) | "Meta de mora ≤ 8%": no existe en la Carta → referencia al promedio del banco |
| Columnas en lugar de barras para cumplir "X categórico" | Línea constante en 52.38% → 40.73% (Carta v8) |
| Árbol de descomposición como el ejemplo del Ing. | "47 clientes saturados" → son **47 cuentas** (el índice es por cuenta) |
| Dispersión con sombreado de simetría para el índice de saturación | Barras de error "±1 EE" de Wald en tasas → Wilson |
| Líneas y columnas en P1; matrices como mapa de calor; múltiplos pequeños | Segmentación de 4 grupos de edad → 3 grupos del Data Mart |
| Tarjeta nueva de varias tarjetas; tarjeta de varias filas en D1/D2 | Influenciadores clave, medidor, mapas, previsión: descartados (sección 3) |
| Tooltips de página, marcadores, formato condicional | Estado del proyecto de la sección 6 (desactualizado): los `.pbip` hoy **no cargan** y deben regenerarse |
| Sección de `CALCULATE` y `FILTER` | "Kimball 3 y Mongo 4 categorías": ya unificado en 4 (Informe 05) |

---

## 10. PLAN DE IMPLEMENTACIÓN

| # | Paso | Archivos | Estado |
| :-: | :--- | :--- | :-: |
| 1 | Cargar las recomendaciones en el Data Mart y en MongoDB (4,500 cuentas en cada motor) | `scripts/42_cargar_recomendaciones.py`, `sql/01` | ✅ |
| 2 | Actualizar la vista de transacciones por categoría (54,298 filas; controles de volumen, conteo y saldo OK) | `sql/04_Vistas_PowerBI_Kimball.sql` | ✅ |
| 3 | Medidas DAX según esta guía (85 medidas: Wilson, absorción vigente, capacidad, foto mensual, `CALCULATE` + `FILTER`). El archivo `.dax` lo genera el script 30 desde la misma lista que usan los dos modelos | `sql/05_Medidas_DAX_PowerBI.dax` | ✅ |
| 4 | Conector de MongoDB con las mismas tablas y columnas que Kimball | `scripts/26_powerbi_mongo_dashboard.py` | ✅ |
| 5 | Regenerar los dos proyectos `.pbip` (9 páginas, KPIs en todas, tema incrustado) | `scripts/30_generar_powerbi_pbip.py`, `dashboards/*` | ✅ |
| 6 | Recalcular la evidencia estadística de cada título con la Carta v8 (Wilson, 3 grupos de edad, bandas, absorción vigente, foto mensual): χ² cosecha p = 0.93, bandas χ² = 38.58 y AUC 0.717, edad χ² = 2.28 (p = 0.32), 193 cuentas pasaron por sobregiro (máx. 43 en nov-1998) | `scripts/27_evidencia_estadistica_dashboard.py`, `metricas_dashboard_07.json` | ✅ |
| 7 | Abrir ambos proyectos en Power BI Desktop, verificar las cifras de control y hacer los ajustes que no se pueden guardar desde el código | `dashboards/*/README.md` | Kimball y Mongo verificados (sección 10.1); ajustes manuales pendientes |
| 8 | Actualizar el Dossier 08, la demo HTML y el README | `08_*`, `demo_dashboard.html` | Pendiente |

### 10.1 Verificación en el motor de Power BI Desktop

El modelo Kimball se abrió en Power BI Desktop 2.157, se actualizó contra `DM_Financial_Kimball_v2` y las medidas se ejecutaron con consultas DAX sobre el motor local del propio Desktop (el mismo que usa el informe):

* **Las 85 medidas** se evalúan sin error y dan las cifras de control: 682 préstamos, 45 en mora, 10.04% y 13.25%, cartera vigente $80,296,176, saldo neto $197,140,434, absorción 40.73% (referencia 52.38%), 39 cuentas en sobregiro, 47 cuentas con índice > 0.5, 35 con crédito externo ($177,154/mes), bandas 2.92% → 23.26%.
* **Cortes de los visuales:** tasa por cosecha 12.5 / 15.4 / 12.2 / 15.0% (1994–1997) y 2.5% en 1998; north Moravia 15.8% (Wilson 12.1–20.4%) y north Bohemia 0% (Wilson 0–2.4%); absorción de east Bohemia 51.6% y de north Bohemia 28.2%; máximo de 43 cuentas en sobregiro en noviembre de 1998; la cascada da $197.14M − $80.30M.
* **Fichas:** D2 del cliente 2823 muestra la cuenta 2335, 52 años, Karvina, préstamo D de $541,200 con cuota de $9,020, banda Alta, órdenes de $14,286/mes, índice 2.14 y saldo de −$2,803 al cierre; da el mismo resultado si se llega por el cliente o por la cuenta. D1 de Karvina: 24 préstamos, 15 vigentes, 3 en mora (20%).

**Modelo MongoDB.** Se abrió en Power BI Desktop y se actualizó con el **conector Python real** (script 26 leyendo MongoDB). Las 10 tablas cargan (682 / 5,369 / 4,500 / 54,298 / 185,615 / 4,500 filas) y las 85 medidas, los cortes, las fichas D1 y D2 y los filtros dan **exactamente las mismas cifras que Kimball**. Para lograrlo hubo que resolver tres problemas del entorno:

1. Power BI no puede ejecutar el Python de Microsoft Store (*"Acceso denegado"*): se instaló Python 3.12 de python.org.
2. Power BI siempre importa `matplotlib.pyplot`, y Windows App Control bloquea la DLL `_image` de matplotlib 3.11.2: se fijó matplotlib 3.10.7 (y pandas 3.0.5, pymongo 4.18.1), versiones que el control de aplicaciones deja cargar. No se modificó ninguna política de seguridad.
3. El puente de Python entrega los números como texto con punto decimal y el modelo usa la cultura es-ES, así que los importes salían **multiplicados por 10**: las consultas de las tablas `m_*` convierten los tipos con cultura `en-US`.

La verificación encontró y corrigió tres defectos que el código solo no mostraba: una dependencia circular al ordenar las bandas, una tasa vacía (en lugar de 0%) en north Bohemia y un selector de color que Power BI ignora en las columnas (se usa `defaultColor`).

---

## 11. REFERENCIAS

* [1] W. S. Cleveland and R. McGill, "Graphical perception," *J. Amer. Statist. Assoc.*, vol. 79, no. 387, pp. 531–554, 1984.
* [2] S. Few, *Show Me the Numbers*, 2nd ed. Analytics Press, 2012.
* [3] S. Few, *Information Dashboard Design*. O'Reilly, 2006.
* [4] E. R. Tufte, *The Visual Display of Quantitative Information*, 2nd ed. Graphics Press, 2001.
* [5] C. Ware, *Information Visualization: Perception for Design*, 3rd ed. Morgan Kaufmann, 2012.
* [6] M. Okabe and K. Ito, "Color Universal Design (CUD): How to make figures and presentations that are friendly to colorblind people," J*Fly, 2008.
* [7] B. Wong, "Points of view: Color blindness," *Nature Methods*, vol. 8, no. 6, p. 441, 2011.
* [8] C. A. Brewer, "A transition in improving maps: The ColorBrewer example," *Cartography and Geographic Information Science*, vol. 30, no. 2, pp. 159–162, 2003.
* [9] C. N. Knaflic, *Storytelling with Data*. Wiley, 2015.
* [10] B. Shneiderman, "Tree visualization with tree-maps," *ACM Trans. Graphics*, vol. 11, no. 1, pp. 92–99, 1992.
* [11] G. Cumming and S. Finch, "Inference by eye," *American Psychologist*, vol. 60, no. 2, pp. 170–180, 2005.
* [12] G. Cumming, F. Fidler and D. L. Vaux, "Error bars in experimental biology," *J. Cell Biology*, vol. 177, no. 1, pp. 7–11, 2007.
* [13] E. B. Wilson, "Probable inference, the law of succession, and statistical inference," *J. Amer. Statist. Assoc.*, vol. 22, no. 158, pp. 209–212, 1927.
* [14] A. Agresti and B. A. Coull, "Approximate is better than 'exact' for interval estimation of binomial proportions," *The American Statistician*, vol. 52, no. 2, pp. 119–126, 1998.
* [15] W. G. Cochran, "Some methods for strengthening the common χ² tests," *Biometrics*, vol. 10, no. 4, pp. 417–451, 1954.
* [16] R. Kimball and M. Ross, *The Data Warehouse Toolkit*, 3rd ed. Wiley, 2013.
* [17] M. Russo and A. Ferrari, *The Definitive Guide to DAX*, 2nd ed. Microsoft Press, 2019.
* Microsoft Learn: panel Análisis, árbol de descomposición, múltiplos pequeños, `CALCULATE`, `FILTER`, `KEEPFILTERS` (enlaces en la investigación del equipo).
