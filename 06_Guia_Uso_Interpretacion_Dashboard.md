# UNIVERSIDAD TÉCNICA DE AMBATO
## FACULTAD DE INGENIERÍA EN SISTEMAS, ELECTRÓNICA E INDUSTRIAL
### CARRERA DE SOFTWARE — ASIGNATURA: INTELIGENCIA DE NEGOCIOS
### CICLO ACADÉMICO: AGOSTO 2026 – DICIEMBRE 2026

---

# GUÍA 06 — USO E INTERPRETACIÓN DEL DASHBOARD GERENCIAL `Financial_ijs` (v5)

**Autores:** Alison Marcela Cobos Taco / Henry Daniel Lagua Flores  
**Docente:** Ing. Ruben Nogales, Mg.  
**Versión:** 2.0 (29/09/2026) — reemplaza la guía 06 anterior (tablero de 2 páginas)  
**Proyectos:** `dashboards/Dashboard_Financial_Kimball/` (SQL Server) y `dashboards/Dashboard_Financial_Mongo/` (MongoDB). Los dos tienen **las mismas 12 páginas, los mismos gráficos y las mismas 127 medidas**; solo cambia la fuente de datos.

> **Para quién es esta guía.** Para el gerente que usa el tablero y para quien lo defiende ante el docente. Explica cómo se conecta, qué medida alimenta cada gráfico, qué muestra, por qué se eligió ese gráfico, cómo usarlo y cómo leer el resultado. El **diseño** (colores, reglas del Ing. Nogales, fundamentos) está en la Guía 07; las fórmulas DAX completas, en `sql/05_Medidas_DAX_PowerBI.dax`.
>
> **Cifras de esta guía:** son las del corte 31/12/1998 **sin filtros**, verificadas en el motor de Power BI Desktop (Guía 07, sección 10.1). Con filtros, los valores cambian; la forma de leerlos, no.

---

## Índice

1. [Cómo se conecta](#1-cómo-se-conecta)
2. [El modelo de datos que usan los gráficos](#2-el-modelo-de-datos-que-usan-los-gráficos)
3. [Cómo navegar y filtrar](#3-cómo-navegar-y-filtrar)
4. [Conceptos y medidas que se repiten](#4-conceptos-y-medidas-que-se-repiten)
5. [Página por página](#5-página-por-página) — Inicio · P1 · P2 · P3 · P4 · P5 · P6 · R1 · R2 · R3 · D1 · D2
6. [Recorridos de decisión (ejemplos)](#6-recorridos-de-decisión-ejemplos)
7. [Cuidados al interpretar](#7-cuidados-al-interpretar)
8. [Anexo: medidas por página](#8-anexo-medidas-por-página)

---

## 1. CÓMO SE CONECTA

### 1.1 Cadena de datos

```
MySQL remoto Financial_ijs (OLTP, relational.fel.cvut.cz)
   │  scripts 31 (ETL) → 32–34 (completitud)            → Informes 09 y 10
   ▼
SQL Server LocalDB · DM_Financial_Kimball_v2 (Data Mart Kimball)
   │  scripts 42 y 43 (recomendaciones del Informe 04)
   │  sql/04 (vista vw_PBI_Trans_Anual_Cuenta)
   ├──────────────────────────────► Dashboard_Financial_Kimball.pbip   (Power Query: Sql.Database)
   │
   │  script 35 (migración) + 42 + 43                    → Informe 05
   ▼
MongoDB localhost:27017 · base Financial
   └──► conector Python scripts/26 ─► Dashboard_Financial_Mongo.pbip   (Power Query: Python.Execute)
```

Los dos `.pbip` los **genera** `scripts/30_generar_powerbi_pbip.py` a partir de una sola definición (tablas, relaciones, medidas y páginas). Por eso no pueden quedar distintos.

### 1.2 Abrir el tablero Kimball (SQL Server)

1. Tener cargado el Data Mart (`python scripts/31_etl_oltp_a_kimball.py --recrear`, luego 32, 33, 34, 42 y 43) y la vista de `sql/04_Vistas_PowerBI_Kimball.sql`.
2. Doble clic en `dashboards/Dashboard_Financial_Kimball/Dashboard_Financial_Kimball.pbip`.
3. Si el servidor no es `(localdb)\MSSQLLocalDB`: *Transformar datos → Editar parámetros* → `ServidorSQL` (y `BaseDatosSQL` si cambió el nombre).
4. *Inicio → Actualizar*. Un `.pbip` no guarda datos: **siempre** hay que actualizar al abrirlo.
5. Comprobar las cifras de control de la tabla 1.4.

### 1.3 Abrir el tablero MongoDB

1. MongoDB en ejecución con la base `Financial` (scripts 35, 42 y 43, o `mongorestore --gzip --archive=Financial_mongo_dump.gz`).
2. **Python de python.org** (no el de Microsoft Store, que Power BI no puede ejecutar) con las versiones que admite el control de aplicaciones de Windows:
   ```bash
   python -m pip install pandas==3.0.5 pymongo==4.18.1 matplotlib==3.10.7
   ```
3. En Power BI: *Archivo → Opciones → Scripts de Python* → carpeta de ese Python (`%LOCALAPPDATA%\Programs\Python\Python312`).
4. Doble clic en `Dashboard_Financial_Mongo.pbip` → *Actualizar* → aceptar el aviso de privacidad del script.
5. Las cifras de control deben ser **idénticas** a las de Kimball.

La consulta compartida `MongoFinancial` ejecuta el script 26, que lee las colecciones y entrega 17 tablas (`m_distritos`, `m_prestamos`, `m_saldo_mensual`, `m_recomendacion_producto`, …). Las tablas `m_*` convierten los números con cultura `en-US`, porque el puente de Python los entrega como texto con punto decimal; sin esa conversión los importes saldrían multiplicados por 10.

### 1.4 Cifras de control (sin filtros)

| Control | Valor | Página |
| :--- | ---: | :-: |
| Préstamos · en mora (D) | 682 · 45 | P1 |
| Tasa de mora vigente · incumplimiento | 10.04% · 13.25% | Inicio |
| Cartera vigente · saldo neto al cierre | $80.30M · $197.14M | Inicio, P3 |
| Absorción vigente (referencia con cartera total) | 40.73% (52.38%) | P3 |
| Volumen · movimientos | $6,257.86M · 1,056,320 | P4 |
| Cuentas en sobregiro al cierre · con índice > 0.5 | 39 · 47 | P4, P5 |
| Impago banda Baja · Alta | 2.92% · 23.26% | P6 |
| Titulares sin préstamo · préstamo recomendado · pueden pagar la cuota típica | 3,818 · 1,721 · 71 | R2 |
| Acierto del recomendador · de la popularidad | 65.96% · 58.48% | R1 |

---

## 2. EL MODELO DE DATOS QUE USAN LOS GRÁFICOS

Esquema en estrella (Kimball). Cada hecho se une a sus dimensiones por clave sustituta:

| Tabla | Grano | La usan |
| :--- | :--- | :--- |
| `Fact_Prestamos` | Un préstamo (682) | P1, P2, P3, P6, R2, D1, D2 |
| `Fact_Saldo_Cuenta_Mensual` | Cuenta × mes (185,615) | Inicio, P3, P4, D1, D2 |
| `vw_PBI_Trans_Anual_Cuenta` | Cuenta × año × categoría (54,298) | P4, P5 |
| `Fact_Ordenes` | Una orden permanente (6,471) | P5, D2 |
| `Recomendacion_Producto` | Cuenta × sistema × posición (26,986) | R1, R3 |
| `Adopcion_Producto` | Cuenta × producto que ya usa (8,604) | R1 |
| `Capacidad_Prestamo` | Un titular (4,500) | R2 |
| `Evaluacion_Recomendador`, `Asociacion_Producto`, `Regla_Capacidad` | Tablas de resultados del Informe 04 | R1, R2, R3 |
| Dimensiones | `Dim_Tiempo`, `Dim_Anio`, `Dim_Distrito`, `Dim_Cliente`, `Dim_Cuenta`, `Dim_Estado_Prestamo`, `Dim_Orden`, `Dim_Producto` | Todas |

Reglas del modelo que el gerente debe conocer, porque cambian la lectura:

* **El saldo no se suma en el tiempo** (es semiaditivo). "Saldo neto al cierre" toma el **último mes** del periodo filtrado: con el año 1996 muestra el saldo de diciembre de 1996.
* **Las órdenes no tienen fecha** en la fuente. El filtro de año **no** las afecta (la relación con el tiempo está inactiva a propósito).
* **Los hechos están a nombre del titular** (OWNER). Los cotitulares no tienen préstamos ni saldos propios.
* **La zona es la del distrito de la cuenta**, no la de residencia del cliente.
* **Absorción, liquidez y cartera "al corte"** ignoran el filtro de año: siempre miden la foto a diciembre de 1998.

---

## 3. CÓMO NAVEGAR Y FILTRAR

### 3.1 El panel lateral (todas las páginas)

| Elemento | Qué hace |
| :--- | :--- |
| Botones **Inicio, P1–P6, R1–R3** | Cambian de página. El botón azul es la página actual. |
| Filtro **Año** | Filtra por año del hecho: otorgamiento del préstamo, año de las transacciones, mes del saldo. |
| Filtro **Zona** | Jerárquico: macro-región (Bohemia, Moravia, Praga) › región › distrito. Se abre con la flecha y se puede elegir un nivel o varios elementos. |
| Filtro **Edad** | Joven (< 30), Adulto (30–50), Adulto Mayor (50 o más). |

**Los tres filtros están sincronizados:** lo que elija en una página sigue elegido en todas las demás. Así el gerente puede fijar, por ejemplo, *Moravia · Adulto Mayor* y recorrer P1 → P6 → R1–R3 viendo siempre el mismo grupo.

### 3.2 Clics dentro de una página

* **Clic en una barra, un sector o una fila:** filtra los demás gráficos **de esa página** (filtro cruzado). Otro clic en el mismo elemento lo quita. Ctrl + clic selecciona varios.
* **Pasar el mouse:** el *tooltip* muestra el detalle (intervalos, *n*, error estándar). En esta guía se indica qué trae cada tooltip.
* El clic en un gráfico **no viaja** a otras páginas (así funciona Power BI). Para llevar una selección a otra página se usan el panel lateral o el *drill-through*.

### 3.3 Drill-through a las fichas (D1 y D2)

* **Clic derecho en un distrito** (P2) → *Obtener detalles* → **D1 Distrito**.
* **Clic derecho en un cliente** (P2, P5, P6, R1, R2, R3, D1) → *Obtener detalles* → **D2 Cliente 360**.
* La ficha se abre **con todos los filtros** de la página de origen. El botón **◀ Atrás** regresa.
* D1 y D2 no aparecen en las pestañas: solo tienen sentido para un distrito o un cliente concreto.

### 3.4 Qué significan los colores

| Color | Significado en todo el tablero |
| :--- | :--- |
| Azul `#0072B2` | Préstamo cerrado al día (A); en R1–R3, el sistema o la regla elegida |
| Celeste `#56B4E9` | Préstamo vigente al día (C) |
| Naranja `#E69F00` | Préstamo vigente en mora (D); en R1, "recomendado" |
| Bermellón `#D55E00` | Cerrado con deuda (B) y **alertas**: KPI en rojo, índice > 1, banda Alta |
| Degradado blanco → bermellón | Más oscuro = más riesgo (treemap, matrices, bandas de capacidad) |
| Gris | Contexto o referencia (el "Banco", modelos descartados, cuentas sin alerta) |

La paleta es la de Okabe e Ito: se distingue con daltonismo. Las regiones y categorías **no** llevan color porque ya están nombradas en el eje.

---

## 4. CONCEPTOS Y MEDIDAS QUE SE REPITEN

| Concepto | Medida DAX | Definición | Cómo leerla |
| :--- | :--- | :--- | :--- |
| Tasa de mora vigente | `Tasa Mora Vigente` | Préstamos D / préstamos vigentes (C + D) | Qué parte de la cartera **activa** está atrasada. Banco: 10.04% |
| Tasa de incumplimiento | `Tasa Incumplimiento` | Préstamos B / préstamos cerrados (A + B) | Qué parte de los préstamos **terminados** quedó con deuda. Banco: 13.25% |
| Tasa de impago | `Tasa Impago` | (B + D) / todos los préstamos | Problema de pago en cualquier momento. Banco: 11.14% |
| Intervalo de Wilson | `Mora Wilson Inferior/Superior` (y de Impago e Incumplimiento) | Intervalo de confianza de una tasa (z = 1, equivale a ±1 error estándar) | Si los intervalos de dos grupos se solapan mucho, la diferencia puede ser azar. Con pocos casos el intervalo es ancho |
| Referencia "Banco" | `Tasa Mora Banco`, `Absorcion Banco`, `Tasa Impago Banco` | La misma medida sin el filtro de la categoría del eje | La línea gris: por encima, peor que el banco |
| Saldo neto al cierre | `Saldo Neto Corte` | Suma del saldo al cierre del **último mes** del contexto | Nunca suma meses. Banco: $197.14M (dic-1998) |
| Absorción vigente | `Absorcion Vigente` | Cartera vigente / saldo neto al corte | Qué parte del dinero de los clientes respalda préstamos activos. Banco: 40.73% |
| Índice de saturación | `Indice Saturacion` | Órdenes fijas mensuales / saldo promedio histórico de la cuenta | > 0.5: la cuenta compromete más de la mitad de su saldo típico; > 1: más de lo que suele tener |
| Banda de capacidad | columna `banda_capacidad` | Cuota / saldo promedio antes del préstamo: Baja ≤ 5.7% · Media-baja ≤ 9.0% · Media-alta ≤ 12.3% · Alta | La regla de crédito de la Carta v8 |
| Acierto (Hit@1) | `Acierto Hit1`, `Acierto Elegido` | % de veces que el recomendador acierta en su **primera** sugerencia el producto que el cliente sí tiene (producto oculto) | Mide la precisión del sistema, con el mismo protocolo para todos |
| AUC | `AUC Regla` | Probabilidad de que la regla ponga a un moroso por encima de un buen pagador | 0.5 = azar; 1 = perfecto. Regla elegida 0.717 |
| P(j \| i) | `P Destino dado Origen` | De quienes tienen el producto *i*, % que también tiene *j* | Regla de venta cruzada |

Todas las divisiones usan `DIVIDE` (no fallan con cero) y las medidas que filtran por otra medida usan `CALCULATE` + `FILTER` (por ejemplo, `Cuentas Saturadas` y `Cartera Distritos Sobre Mora Banco`).

---

## 5. PÁGINA POR PÁGINA

Cada página tiene la misma estructura: **título = pregunta de la Carta**, una **fila de KPIs** y debajo los gráficos. El título de cada gráfico es la **respuesta** a la pregunta con los datos sin filtrar.

---

### Inicio — ¿Cómo está el banco?

**Para qué sirve:** resumen en 10 segundos y puerta de entrada a las demás páginas.

**KPIs**

| KPI | Medida | Valor | Lectura |
| :--- | :--- | ---: | :--- |
| Tasa de mora vigente | `Tasa Mora Vigente` | 10.04% | 1 de cada 10 préstamos activos está atrasado (en bermellón: es alerta) |
| Incumplimiento | `Tasa Incumplimiento` | 13.25% | De los préstamos ya cerrados, 13 de cada 100 quedaron con deuda |
| Cartera vigente (C + D) | `Cartera Vigente` | $80.30M | Monto original de los préstamos activos |
| Saldo neto al cierre | `Saldo Neto Corte` | $197.14M | Dinero de los clientes al último mes del periodo |
| Absorción vigente | `Absorcion Vigente` | 40.73% | 41 de cada 100 dólares de saldo respaldan préstamos activos |
| Cuentas en sobregiro | `Cuentas en Sobregiro` | 39 | Cuentas con saldo negativo al cierre |

**Contenido:** los **3 problemas** de la Carta v8 (impago y mora, capacidad de pago, medición de saldos) con su cifra clave y las páginas que los responden, y **9 botones** a las preguntas P1–P6 y R1–R3.

**Cómo usarla:** elija primero la zona o la edad en el panel; los KPIs se recalculan. Después entre a la pregunta que le interese.

---

### P1 — ¿Cómo evolucionan la cantidad y la tasa de mora por año de otorgamiento?

**KPIs:** Préstamos otorgados (`Num Prestamos`, 682) · Vigentes en mora (`Prestamos en Mora`, 45) · Tasa de mora vigente (10.04%) · Tasa de incumplimiento (13.25%).

#### Gráfico 1 — Líneas y columnas: préstamos otorgados y tasa de mora por cosecha

| | |
| :--- | :--- |
| **Muestra** | Columnas grises: préstamos otorgados cada año. Línea naranja: tasa de mora de los préstamos otorgados ese año (su "cosecha") |
| **Campos y medidas** | Eje: `Dim_Anio[anio]` · Columnas: `Num Prestamos` · Línea (eje derecho): `Tasa Mora Vigente` · Tooltip: `Mora Wilson Inferior`, `Mora Wilson Superior`, `Prestamos Vigentes`, `Prestamos en Mora` |
| **Por qué este gráfico** | Dos magnitudes distintas (cantidad y porcentaje) en el tiempo: el combinado permite comparar su evolución con dos escalas |
| **Cómo usarlo** | Pase el mouse por cada punto de la línea para ver el intervalo de Wilson y cuántos préstamos vigentes lo sustentan |
| **Cómo interpretarlo** | La colocación se duplica (101 en 1994 → 196 en 1997) pero la tasa se mantiene entre 12.2% y 15.4% (χ² p = 0.93). **Hay más morosos porque se presta más, no porque los préstamos sean peores.** 1998 (2.5%) es bajo porque esos préstamos son recientes; 1993 no tiene tasa porque sus 20 préstamos ya están cerrados |

#### Gráfico 2 — Matriz año × estado (mapa de calor)

| | |
| :--- | :--- |
| **Muestra** | Cuántos préstamos de cada año están en cada estado A, B, C, D |
| **Campos y medidas** | Filas: año · Columnas: `Dim_Estado_Prestamo[Estado]` · Valor: `Num Prestamos` · Fondo: degradado por el mismo valor |
| **Por qué** | Regla del docente: mostrar **todas** las combinaciones categoría × tiempo |
| **Cómo interpretarlo** | Los préstamos antiguos están cerrados (A, B) y los recientes vigentes (C, D). Las celdas más oscuras son las combinaciones con más préstamos |

**Nota fija de la página:** explica por qué 1993 y 1998 no se comparan con el resto.

---

### P2 — ¿Qué regiones y distritos concentran la cartera y la mora?

**KPIs:** Región con mayor tasa de mora (`Region Mayor Mora`: north Moravia · 15.8%) · Distrito con más préstamos en mora (`Distrito Mayor Morosos`: Hl.m. Praha · 4) · Tasa de mora del banco (`Tasa Mora Banco`, 10.04%) · Cartera vigente sobre la mora del banco (`Cartera Distritos Sobre Mora Banco`, $32.53M: cartera activa en los 26 distritos cuya mora supera la del banco).

#### Gráfico 1 — Árbol de descomposición

| | |
| :--- | :--- |
| **Muestra** | Los 45 préstamos en mora abiertos por región → distrito → cliente |
| **Campos y medidas** | Analizar: `Prestamos en Mora` · Explicar por: región, distrito, `Dim_Cliente[Cliente]` |
| **Por qué** | Es el recorrido que pide el docente: "el mayor → dentro de ese → …" |
| **Cómo usarlo** | Clic en **+** de cada nivel (o *Valor alto* para que Power BI elija la rama mayor). Al llegar al cliente, clic derecho → *Obtener detalles* |
| **Cómo interpretarlo** | north Moravia (12) → Karvina (3) → clientes concretos, por ejemplo el 2823 |

#### Gráfico 2 — Treemap

| | |
| :--- | :--- |
| **Muestra** | Rectángulos por región y distrito. **Área** = cartera vigente; **color** = tasa de mora (blanco → bermellón) |
| **Campos y medidas** | Grupo: región · Detalle: distrito · Valor: `Cartera Vigente` · Color: `Color Mora` · Tooltip: `Tasa Mora Vigente`, `Prestamos Vigentes` |
| **Por qué** | Muestra a la vez **cuánto** hay en juego y **qué tan riesgoso** es |
| **Cómo interpretarlo** | Rectángulo grande y oscuro = mucho dinero con mucha mora (prioridad de cobranza). Grande y claro = cartera sana. Pequeño y oscuro = tasa alta pero con pocos préstamos (revise el *n*) |

#### Gráfico 3 — Columnas + línea: tasa de mora por región

| | |
| :--- | :--- |
| **Muestra** | Tasa de mora de cada región (naranja), ordenada de mayor a menor; línea gris = banco |
| **Campos y medidas** | Eje: región · Columnas: `Tasa Mora Vigente` · Línea: `Tasa Mora Banco` · Tooltip: Wilson inferior/superior, `Prestamos Vigentes` |
| **Por qué** | La comparación precisa de tasas que el treemap no permite |
| **Cómo interpretarlo** | Sobre la línea gris = peor que el banco: north Moravia 15.8% (12 de 76) y east Bohemia 13.8%. north Bohemia: 0 de 41 (su intervalo va de 0% a 2.4%) |

#### Gráfico 4 — Tabla de distritos

| | |
| :--- | :--- |
| **Muestra** | Por distrito: vigentes (*n*), en mora, tasa y su intervalo de Wilson |
| **Campos y medidas** | `nombre_distrito`, `Prestamos Vigentes`, `Prestamos en Mora`, `Tasa Mora Vigente`, `Mora Wilson Inferior`, `Mora Wilson Superior` |
| **Por qué** | La Carta exige mostrar cada tasa con su *n*: 70 de 77 distritos tienen menos de 10 vigentes |
| **Cómo interpretarlo** | Una tasa de 66.7% con 3 préstamos (Bruntal) es poco confiable: su intervalo va de 38.6% a 86.4%. Priorice distritos con *n* alto y límite inferior alto |

---

### P3 — ¿Qué proporción del saldo está comprometida en la cartera vigente y cómo evoluciona el saldo?

**KPIs:** Absorción vigente (40.73%; referencia con cartera total 52.38%) · Cartera vigente al corte ($80.30M) · Saldo neto al cierre ($197.14M) · Saldo por cobrar estimado C + D (`Saldo por Cobrar Estimado`, $46.62M: capital que aún falta cobrar de los préstamos activos).

#### Gráfico 1 — Columnas + línea: absorción vigente por región

| | |
| :--- | :--- |
| **Muestra** | % del saldo de cada región comprometido en préstamos activos; línea gris = banco (40.73%) |
| **Campos y medidas** | Eje: región · Columnas: `Absorcion Vigente` · Línea: `Absorcion Banco` · Tooltip: `Cartera Vigente Corte`, `Saldo Neto Corte Total`, `Absorcion Cartera Total` |
| **Por qué** | Indicador de liquidez de la Carta v8, comparado contra el banco |
| **Cómo interpretarlo** | east Bohemia (51.6%) es la más expuesta: la mitad de su saldo respalda préstamos. north Bohemia (28.2%) tiene más holgura para prestar. Este indicador ignora el filtro de año |

#### Gráfico 2 — Líneas: saldo promedio por cuenta activa

| | |
| :--- | :--- |
| **Muestra** | Saldo promedio por cuenta al cierre de cada mes (1993–1998) |
| **Campos y medidas** | Eje: `Dim_Tiempo[fecha]` (cierres de mes) · Línea: `Saldo Promedio por Cuenta` · Tooltip: `Saldo Neto Corte`, `Cuentas Activas Corte` |
| **Por qué** | El saldo **total** crece de $0.66M a $197.14M sobre todo porque se abren cuentas (96 → 4,500). El promedio por cuenta muestra la salud real de cada cliente |
| **Cómo interpretarlo** | El promedio sube de unos $6,900 a $43,800 por cuenta. Las caídas periódicas son estacionales |

#### Gráfico 3 — Cascada: de saldo a liquidez libre

| | |
| :--- | :--- |
| **Muestra** | Saldo neto al corte → menos cartera vigente → total = liquidez libre |
| **Campos y medidas** | Categoría: `Composicion_Liquidez[concepto]` · Valor: `Valor Composicion Liquidez` |
| **Por qué** | Explica visualmente el 40.73% como una resta |
| **Cómo interpretarlo** | $197.14M − $80.30M = **$116.84M libres** para nuevos préstamos o reservas |

---

### P4 — ¿Qué operaciones concentran el flujo, cómo varía el saldo promedio y cuántas cuentas caen en sobregiro?

**KPIs:** Volumen transaccionado ($6,257.86M) · Movimientos (1,056,320) · Ticket promedio (`Ticket Promedio`, $5,924) · Cuentas en sobregiro al cierre (39, en bermellón).

#### Gráfico 1 — Columnas: ticket promedio por categoría

| | |
| :--- | :--- |
| **Muestra** | Monto promedio de cada movimiento en las 4 categorías analíticas |
| **Campos y medidas** | Eje: `categoria_analitica` · Valor: `Ticket Promedio` · Tooltip: `Ticket Limite Inferior/Superior` (±1σ), `EE Ticket` (error estándar), `Num Transacciones` |
| **Por qué** | Miles de movimientos por categoría: el promedio con su dispersión (regla del docente) |
| **Cómo interpretarlo** | Los depósitos ($14,416) y retiros en efectivo ($12,517) son los movimientos grandes; los intereses ($150) los pequeños. La σ es tan grande como el promedio: los montos varían mucho entre clientes |

#### Gráfico 2 — Líneas: volumen anual por categoría

| | |
| :--- | :--- |
| **Muestra** | Volumen de cada categoría por año |
| **Campos y medidas** | Eje: año · Valor: `Volumen Transaccionado` · Leyenda: categoría |
| **Cómo interpretarlo** | Ingresos y egresos crecen juntos año a año; los retiros en efectivo y los intereses son marginales en volumen |

#### Gráfico 3 — Matriz año × categoría (mapa de calor)

| | |
| :--- | :--- |
| **Muestra** | Volumen de cada categoría en cada año, con fondo azul más intenso a mayor volumen |
| **Campos y medidas** | Filas: año · Columnas: categoría · Valor: `Volumen Transaccionado` |
| **Por qué** | Todas las combinaciones, con las cifras exactas que las líneas no muestran |

#### Gráfico 4 — Líneas: cuentas en sobregiro por mes

| | |
| :--- | :--- |
| **Muestra** | Cuántas cuentas cierran cada mes con saldo negativo |
| **Campos y medidas** | Eje: fecha de cierre · Valor: `Cuentas en Sobregiro` · Tooltip: `Cuentas Activas Corte` |
| **Cómo interpretarlo** | El sobregiro crece en 1997–1998 hasta un máximo de **43 cuentas en noviembre de 1998**; 193 cuentas pasaron alguna vez por sobregiro. Es una señal temprana de problemas de liquidez de los clientes |

---

### P5 — ¿Qué cuentas comprometen en cuotas y órdenes fijas una parte alta de su saldo, incluidas deudas externas?

**KPIs:** Compromiso mensual en órdenes (`Compromiso Ordenes`, $21.23M) · Órdenes (6,471) · Cuentas con índice > 0.5 (`Cuentas Saturadas`, 47) · Cuentas con crédito externo (`Cuentas con Credito Externo`, 35: pagan un préstamo a otra entidad).

#### Gráfico 1 — Dispersión: saldo frente a órdenes mensuales

| | |
| :--- | :--- |
| **Muestra** | Un punto por titular. X = saldo promedio de su cuenta; Y = lo que paga cada mes en órdenes fijas |
| **Campos y medidas** | Detalle: `Dim_Cliente[Cliente]` · X: `Saldo Promedio Historico` · Y: `Compromiso Ordenes` · Color: `Color Saturacion` · Tooltip: `Indice Saturacion`, `Cuenta Ficha` |
| **Por qué** | Relación entre dos variables numéricas por cliente: el índice de saturación **se ve** |
| **Colores** | Gris: índice ≤ 0.5 · Naranja: índice > 0.5 · **Bermellón: índice > 1** (paga más de lo que suele tener) |
| **Cómo interpretarlo** | Los puntos arriba a la izquierda son los peligrosos: poco saldo y muchas órdenes. La cuenta 2335 (cliente 2823, índice 2.14) está sola en bermellón |

#### Gráfico 2 — Anillo: órdenes por propósito

| | |
| :--- | :--- |
| **Muestra** | % de las órdenes de cada propósito |
| **Campos y medidas** | Categoría: `Dim_Orden[categoria_orden_traducida]` · Valor: `Num Ordenes` |
| **Por qué** | Una variable con pocas clases (5): regla del docente para el anillo |
| **Cómo interpretarlo** | Servicios del hogar 54.1%, sin especificar 21.3%, cuota de préstamo 11.1%, seguros 8.2%, leasing 5.3% |

#### Gráfico 3 — Tabla de alerta (cobranza temprana)

| | |
| :--- | :--- |
| **Muestra** | Las 47 cuentas con índice > 0.5, de mayor a menor riesgo |
| **Campos y medidas** | `Cliente`, `Cuenta Alerta`, `Indice Saturacion Alerta`, `Compromiso Alerta`, `Saldo Promedio Alerta`, `Credito Externo Alerta` (solo toman valor si el índice supera 0.5) |
| **Cómo usarla** | Es la lista de trabajo de cobranza: clic derecho en un cliente → *Obtener detalles* para ver su ficha completa |

---

### P6 — ¿Qué clientes tienen impago histórico y en qué medida la capacidad de pago previa lo anticipa?

**KPIs:** Clientes con impago B (`Clientes con Impago`, 31) · Impago banda Baja (`Tasa Impago Banda Baja`, 2.92%) · Impago banda Alta (`Tasa Impago Banda Alta`, 23.26%) · Monto original en riesgo B + D (`Monto Original en Riesgo`, $15.58M).

#### Gráfico 1 — Columnas + línea: impago por banda de capacidad

| | |
| :--- | :--- |
| **Muestra** | Tasa de impago (B o D) en cada banda de la regla cuota / saldo previo; línea gris = banco |
| **Campos y medidas** | Eje: `Fact_Prestamos[banda_capacidad]` (ordenada Baja → Alta) · Columnas: `Tasa Impago` · Línea: `Tasa Impago Banco` · Tooltip: `Impago Wilson Inferior/Superior`, `Num Prestamos`, `Prestamos con Impago` |
| **Por qué** | Es el hallazgo más fuerte del proyecto: la capacidad de pago anticipa el impago |
| **Cómo interpretarlo** | De 2.9% en la banda Baja a **23.3% en la Alta** (χ² = 38.58, p < 0.001): quien compromete en la cuota más del 12.3% de su saldo tiene 8 veces más impago. Los colores van de claro a oscuro porque las bandas son ordinales |

#### Gráfico 2 — Columnas + línea: incumplimiento por edad

| | |
| :--- | :--- |
| **Muestra** | Tasa de incumplimiento de cada segmento de edad frente al banco |
| **Campos y medidas** | Eje: `segmento_edad` · Columnas: `Tasa Incumplimiento` · Línea: `Tasa Incumplimiento Banco` · Tooltip: Wilson, `Prestamos Cerrados` |
| **Por qué** | Contraste: ¿el perfil demográfico explica el impago? |
| **Cómo interpretarlo** | Aunque el grupo de 50 años o más parece mayor (18.3%), la diferencia **no es significativa** (χ² = 2.28, p = 0.32): los intervalos se solapan. **Se decide por capacidad, no por edad** |

#### Gráfico 3 — Lista de denegación

| | |
| :--- | :--- |
| **Muestra** | Los 31 titulares con un préstamo cerrado con deuda: distrito, monto y banda |
| **Campos y medidas** | `Cliente`, `Distrito Impago`, `Monto Incumplido`, `Banda Capacidad Impago` |
| **Cómo usarla** | Antes de aprobar un nuevo crédito, verifique que el cliente no esté aquí |

---

### R1 — ¿Qué producto ofrecer a cada cliente? (recomendador demográfico)

**Sistema:** demográfico por arquetipo (zona × edad), el más preciso de los 8 evaluados en el Informe 04. Recomienda a cada titular los productos que **no tiene** y que más usan los clientes de su mismo arquetipo.

**KPIs:** Titulares con recomendación (`Clientes con Recomendacion`, 4,500) · Acierto del recomendador (`Acierto Elegido`, 65.96%) · Acierto ofreciendo lo más popular (`Acierto Popularidad`, 58.48%) · Primera oferta más frecuente (`Producto Mas Recomendado`: Transferencias a otros bancos · 1,817).

**Cómo leer el acierto:** a cada cliente con 2 o más productos se le ocultó uno. El sistema acierta en su **primera** sugerencia el producto oculto en el 66% de los casos; ofrecer siempre lo más popular acierta el 58%.

#### Gráfico 1 — Columnas: dónde crecer

| | |
| :--- | :--- |
| **Muestra** | Por producto: cuentas que ya lo usan (gris) y cuentas a las que se les recomienda (naranja) |
| **Campos y medidas** | Eje: `Dim_Producto[producto]` · Valores: `Cuentas que ya lo Usan`, `Recomendaciones Demograficas` · Tooltip: `Penetracion Actual`, `Primera Opcion` |
| **Por qué** | Compara la base actual con la oportunidad, producto por producto |
| **Cómo interpretarlo** | Barra naranja alta sobre gris baja = mucho potencial. Transferencias a otros bancos (1,197 la usan, 3,303 recomendaciones) e ingresos por transferencia (866, 3,083) son las mayores oportunidades. Cambie la zona o la edad en el panel y observe cómo se mueve la oportunidad |

#### Gráfico 2 — Matriz arquetipo × producto (mapa de calor)

| | |
| :--- | :--- |
| **Muestra** | Cuántos clientes de cada arquetipo reciben cada producto como **primera** oferta |
| **Campos y medidas** | Filas: `Dim_Cliente[arquetipo_demografico]` · Columnas: producto · Valor: `Primera Opcion` |
| **Por qué** | En un modelo demográfico la matriz **es** el modelo: explicable en una mirada |
| **Cómo interpretarlo** | Cada fila dice qué ofrecer primero a ese perfil. Por ejemplo, con el filtro Edad = Adulto Mayor la primera oferta más frecuente es domiciliar la pensión (766 titulares) |

#### Gráfico 3 — Barras: por qué este sistema

| | |
| :--- | :--- |
| **Muestra** | Acierto (Hit@1) de los 8 recomendadores evaluados; en azul los elegidos |
| **Campos y medidas** | Eje: `Evaluacion_Recomendador[modelo]` · Valor: `Acierto Hit1` · Color: `Color Modelo` · Tooltip: `MRR Modelo`, `Acierto Cola Larga`, `MRR Confirmacion` |
| **Por qué** | La decisión se fundamenta con evidencia, no por preferencia |
| **Cómo interpretarlo** | Demográfico 66.0% > kNN por perfil 65.3% > popularidad 58.5% > P(j\|i) 48.9% > Slope One 28.1% > contenidos 20.1% > kNN por productos 18.7% > TF-IDF 8.1%. El MRR de confirmación (semilla 2026) repite el orden |

#### Gráfico 4 — Tabla: ofertas por titular

| | |
| :--- | :--- |
| **Muestra** | Para cada cliente: su 1.ª, 2.ª y 3.ª oferta y, si se le ofrece préstamo, la cuota máxima prudente |
| **Campos y medidas** | `Cliente`, `Recomendacion 1`, `Recomendacion 2`, `Recomendacion 3`, `Cuota Maxima Prudente` |
| **Cómo usarla** | Filtre la zona o la edad y exporte la lista (*… → Exportar datos*) para la fuerza comercial. Clic derecho en un cliente → ficha D2 |

---

### R2 — ¿A quién prestar y hasta cuánto? (regla de capacidad de pago)

**Sistema:** la cuota prudente de cada titular es el **5.7% de su saldo promedio** (el límite de la banda Baja, donde el impago es 2.9%). El préstamo solo se recomienda si esa cuota alcanza la cuota mínima que el banco ha otorgado, y siempre con un monto máximo.

**KPIs:** Titulares sin préstamo (`Titulares sin Prestamo`, 3,818) · Préstamo recomendado (`Prestamos Prudentes Recomendados`, 1,721) · Cuota prudente mediana (`Cuota Prudente Mediana`, $1,873) · Pueden pagar la cuota típica (`Pueden Pagar Prestamo Tipico`, 71, en bermellón).

**Lectura clave:** la cuota prudente mediana ($1,873) es menos de la mitad de la cuota típica del banco ($3,934): solo 71 titulares podrían pagar un préstamo "normal". Por eso el préstamo se ofrece **con monto máximo por cliente**.

#### Gráfico 1 — Columnas + línea: validación de la regla

Igual que el gráfico 1 de P6 (`Tasa Impago` por `banda_capacidad`, línea `Tasa Impago Banco`). Se repite aquí porque es la evidencia que justifica la cuota prudente: ofrecer solo la cuota de la banda Baja mantiene el impago esperado cerca del 3%.

#### Gráfico 2 — Columnas: AUC de cada regla

| | |
| :--- | :--- |
| **Muestra** | Capacidad de cada regla de anticipar el impago |
| **Campos y medidas** | Eje: `Regla_Capacidad[regla]` · Valor: `AUC Regla` · Color: `Color Regla` (azul = elegida) |
| **Cómo interpretarlo** | Cuota / saldo previo (Carta v8): **0.717**. Cuota / salario del distrito (anterior): 0.659. La regla nueva discrimina mejor porque usa el dinero real del cliente |

#### Gráfico 3 — Columnas: cuánto se les puede prestar a 36 meses

| | |
| :--- | :--- |
| **Muestra** | Titulares sin préstamo por tramo de monto máximo a 36 meses |
| **Campos y medidas** | Eje: `Capacidad_Prestamo[tramo_monto_36m]` · Valor: `Titulares sin Prestamo` |
| **Cómo interpretarlo** | La mayoría puede recibir entre $40 mil y $150 mil a 36 meses; solo 34 más de $150 mil |

#### Gráfico 4 — Columnas: monto prudente por región

| | |
| :--- | :--- |
| **Muestra** | Suma de los montos máximos a 36 meses de los préstamos recomendados, por región |
| **Campos y medidas** | Eje: región · Valor: `Monto Prudente Ofrecible 36m` · Tooltip: `Prestamos Prudentes Recomendados` |
| **Cómo usarlo** | Para asignar metas de colocación por zona. Crúcelo con P3: una región con poca absorción (holgura) y mucho monto prudente es la mejor para colocar |

#### Gráfico 5 — Tabla: a quién ofrecer y hasta cuánto

| | |
| :--- | :--- |
| **Muestra** | Los 1,721 titulares con préstamo recomendado: saldo promedio, cuota máxima y montos máximos a 12, 36 y 60 meses |
| **Campos y medidas** | `Cliente`, `Saldo Promedio Oferta`, `Cuota Prudente Oferta`, `Monto 12m Oferta`, `Monto 36m Oferta`, `Monto 60m Oferta` |
| **Cómo usarla** | Ordenada de mayor a menor monto. Antes de ofertar, abra la ficha D2 del cliente (clic derecho) y verifique que no esté en la lista de denegación de P6 ni en alerta en P5 |

---

### R3 — ¿Qué más ofrecer? (venta cruzada y descubrimiento)

**Sistemas:** P(j | i) ítem a ítem, para reglas de venta cruzada explicables, y **kNN por perfil**, que busca los 30 titulares más parecidos (edad, sexo, zona, salario y desempleo del distrito, antigüedad) y es el mejor para descubrir productos poco comunes.

**KPIs:** Ofertas nuevas que aporta el kNN (`Descubrimientos kNN`, 2,731: productos que el demográfico no tenía en su top 3) · Acierto kNN en productos poco comunes (`Acierto Cola Larga kNN`, 37.23%) · Popularidad en productos poco comunes (`Acierto Cola Larga Popularidad`, 6.31%) · Venta cruzada más fuerte (`Regla Mas Fuerte`: Seguro domiciliado → Transferencias a otros bancos · 99.8%).

#### Gráfico 1 — Matriz de venta cruzada P(j | i) (mapa de calor)

| | |
| :--- | :--- |
| **Muestra** | Para cada par de productos: de quienes tienen el de la **fila**, qué % también tiene el de la **columna** |
| **Campos y medidas** | Filas: `producto_origen` · Columnas: `producto_destino` · Valor: `P Destino dado Origen` |
| **Por qué** | Traduce el modelo a reglas de campaña: "a quien tiene X, ofrecerle Y" |
| **Cómo interpretarlo** | Lea por filas. Celda oscura = regla fuerte: el 99.8% de quienes pagan seguro también hacen transferencias; todos los pensionistas domicilian servicios. Celda en 0%: ese par **no** se da (ningún pensionista tiene préstamo; no ofrezca préstamo a pensionistas por esta vía) |

#### Gráfico 2 — Barras: qué descubre el kNN

| | |
| :--- | :--- |
| **Muestra** | Cuántas ofertas nuevas (fuera del top 3 demográfico) propone el kNN, por producto |
| **Campos y medidas** | Eje: producto · Valor: `Descubrimientos kNN` |
| **Cómo interpretarlo** | Seguro (890), préstamo (623) y leasing (542): productos menos comunes que la popularidad casi nunca sugiere |

#### Gráfico 3 — Tabla: segunda oferta por titular

| | |
| :--- | :--- |
| **Muestra** | Oferta principal (demográfico) y "además, ofrecer" (kNN) para cada cliente |
| **Campos y medidas** | `Cliente`, `Recomendacion 1`, `Descubrimiento kNN` |
| **Cómo usarla** | La segunda oferta es para clientes que ya aceptaron la primera o para campañas de productos específicos |

---

### D1 — Detalle del distrito (drill-through)

**Cómo se llega:** clic derecho en un distrito de P2 → *Obtener detalles*. El título dice qué distrito y región se está viendo (`Titulo Distrito`).

| Visual | Medidas | Lectura |
| :--- | :--- | :--- |
| Tarjeta de varias filas "Indicadores del distrito" | `Num Prestamos`, `Prestamos Vigentes`, `Prestamos en Mora`, `Tasa Mora Vigente`, `Cartera Vigente`, `Saldo Neto Corte`, `Absorcion Vigente`, `Poblacion Distrito`, `Salario Promedio Distrito`, `Desempleo Distrito 1995`, `Origen Indicadores` | Karvina: 24 préstamos, 15 vigentes, 3 en mora (20%), absorción 33.0%. "Indicadores: imputado" marca el distrito 69, cuyos indicadores se estimaron (Informe 10) |
| Anillo por estado | `Num Prestamos` por `Estado` | Cómo se reparte la cartera del distrito entre A, B, C y D |
| Líneas | `Saldo Promedio por Cuenta` (azul) y `Saldo Promedio Banco` (gris) por mes | Si la línea azul está bajo la gris, los clientes del distrito tienen menos saldo que el promedio del banco |
| Tabla de préstamos | `Cliente`, `Estado Prestamo`, `Cartera Total`, `Cuota Mensual`, `Banda Capacidad` | Clic derecho en un cliente → D2 |

---

### D2 — Ficha Cliente 360 (drill-through)

**Cómo se llega:** clic derecho en un cliente de P2, P5, P6, R1, R2, R3 o D1 → *Obtener detalles*. Título: `Titulo Cliente` (por ejemplo, "Ficha 360 · Cliente 2823 · Cuenta 2335").

| Visual | Medidas | Lectura (cliente 2823) |
| :--- | :--- | :--- |
| Perfil | `Edad Cliente`, `Segmento Cliente`, `Arquetipo Cliente`, `Distrito Cuenta`, `Calificacion Cliente` | 52 años, Moravia · Adulto Mayor, Karvina, sin calificación (su préstamo no ha terminado) |
| Situación | `Estado Prestamo`, `Cartera Total`, `Cuota Mensual`, `Banda Capacidad`, `Compromiso Ordenes`, `Indice Saturacion`, `Credito Externo Mensual` | Préstamo D de $541,200 con cuota de $9,020 (banda Alta); órdenes por $14,286/mes; índice 2.14 |
| Líneas | `Saldo Neto Corte` por mes y `Umbral Sobregiro` (0) | Cae de $12,867 (1996) a −$2,803 (1998): bajo la línea gris está en sobregiro |
| Órdenes fijas | `categoria_orden_traducida`, `Num Ordenes`, `Compromiso Ordenes` | A qué paga cada mes: cuota, servicios, seguros |
| Qué ofrecerle | `recomendacion_1/2/3` (R1), `Cuota Maxima Prudente`, `Monto Maximo Prudente` (R2), `Descubrimiento kNN` (R3) | Domiciliar la pensión, recibir ingresos por transferencia y tarjeta de débito. **No** se le ofrece préstamo: su capacidad no lo permite |

**Uso típico:** es la pantalla que el ejecutivo abre antes de llamar a un cliente. Junta el riesgo (mora, saturación, sobregiro) y la oportunidad (qué ofrecer y hasta cuánto).

---

## 6. RECORRIDOS DE DECISIÓN (EJEMPLOS)

**A. ¿Dónde reforzar la cobranza?**
1. P2 → la columna de north Moravia está sobre la línea del banco (15.8%).
2. Clic derecho en Karvina (treemap o tabla) → D1: 3 en mora de 15 vigentes.
3. En la tabla de D1, clic derecho en el cliente 2823 → D2: préstamo D, índice 2.14, saldo negativo.
4. P5 confirma que no es un caso aislado: 47 cuentas en alerta, lista para cobranza temprana.

**B. Campaña de crédito prudente en una zona**
1. Panel → Zona = Moravia (queda fijo en todas las páginas).
2. P3 → ¿hay holgura de liquidez en sus regiones?
3. R2 → 855 préstamos recomendados en Moravia y el monto a colocar por región.
4. Tabla de R2 → clientes y montos máximos; antes de ofertar, D2 de cada uno y la lista de denegación de P6.

**C. ¿Qué ofrecer a los clientes mayores?**
1. Panel → Edad = Adulto Mayor.
2. R1 → la primera oferta más frecuente pasa a ser "Domiciliar la pensión" (766).
3. R3 → la matriz muestra que los pensionistas también domicilian servicios y **no** tienen préstamo ni transferencias salientes.

**D. ¿Subir o bajar el límite de crédito?**
1. P6 → el impago depende de la banda de capacidad, no de la edad.
2. R2 → la regla cuota / saldo anticipa mejor el impago (AUC 0.717). El límite debe fijarse por cliente con la cuota prudente, no con un monto estándar.

---

## 7. CUIDADOS AL INTERPRETAR

* **Pocos casos, tasas extremas.** Una tasa con menos de 10 préstamos casi siempre tiene un intervalo muy ancho. Mire siempre el *n* y el intervalo de Wilson del tooltip antes de concluir.
* **1998 es un año censurado.** Sus préstamos no han tenido tiempo de caer en mora; su tasa baja no significa mejor calidad.
* **Filtro de año.** Afecta a préstamos (por otorgamiento), transacciones y saldo (último mes del año elegido), pero **no** a las órdenes ni a la absorción, liquidez y recomendaciones, que son fotos al corte.
* **Correlación no es causa.** Que la banda Alta tenga más impago justifica usarla para decidir, pero no prueba que la cuota sea la única causa.
* **Recomendaciones.** Son propuestas basadas en clientes parecidos, no una garantía de compra. El acierto (66%) se midió ocultando productos que los clientes sí tenían.
* **Datos del caso.** La base es un banco checo real de 1993–1998 anonimizado. Los montos están en la unidad de la fuente (coronas checas), mostradas con el símbolo `$` por convención del formato.

---

## 8. ANEXO: MEDIDAS POR PÁGINA

Todas están en la tabla `_Medidas` de los dos modelos, con la misma fórmula. La fórmula completa y su comentario están en `sql/05_Medidas_DAX_PowerBI.dax`.

| Página | Medidas |
| :--- | :--- |
| Inicio | Tasa Mora Vigente, Tasa Incumplimiento, Cartera Vigente, Saldo Neto Corte, Absorcion Vigente, Cuentas en Sobregiro |
| P1 | Num Prestamos, Prestamos en Mora, Prestamos Vigentes, Tasa Mora Vigente, Tasa Incumplimiento, Mora Wilson Inferior, Mora Wilson Superior |
| P2 | Region Mayor Mora, Distrito Mayor Morosos, Tasa Mora Banco, Cartera Distritos Sobre Mora Banco, Prestamos en Mora, Cartera Vigente, Color Mora, Tasa Mora Vigente, Prestamos Vigentes, Mora Wilson Inferior/Superior |
| P3 | Absorcion Vigente, Absorcion Banco, Absorcion Cartera Total, Cartera Vigente Corte, Saldo Neto Corte, Saldo Neto Corte Total, Saldo por Cobrar Estimado, Saldo Promedio por Cuenta, Cuentas Activas Corte, Valor Composicion Liquidez |
| P4 | Volumen Transaccionado, Num Transacciones, Ticket Promedio, Ticket Limite Inferior/Superior, EE Ticket, Cuentas en Sobregiro, Cuentas Activas Corte |
| P5 | Compromiso Ordenes, Num Ordenes, Cuentas Saturadas, Cuentas con Credito Externo, Saldo Promedio Historico, Indice Saturacion, Color Saturacion, Cuenta Ficha, Cuenta Alerta, Indice Saturacion Alerta, Compromiso Alerta, Saldo Promedio Alerta, Credito Externo Alerta |
| P6 | Clientes con Impago, Tasa Impago Banda Baja, Tasa Impago Banda Alta, Monto Original en Riesgo, Tasa Impago, Tasa Impago Banco, Impago Wilson Inferior/Superior, Prestamos con Impago, Tasa Incumplimiento, Tasa Incumplimiento Banco, Incumplimiento Wilson Inferior/Superior, Prestamos Cerrados, Distrito Impago, Monto Incumplido, Banda Capacidad Impago |
| R1 | Clientes con Recomendacion, Acierto Elegido, Acierto Popularidad, Producto Mas Recomendado, Cuentas que ya lo Usan, Recomendaciones Demograficas, Penetracion Actual, Primera Opcion, Acierto Hit1, Color Modelo, MRR Modelo, Acierto Cola Larga, MRR Confirmacion, Recomendacion 1/2/3, Cuota Maxima Prudente |
| R2 | Titulares sin Prestamo, Prestamos Prudentes Recomendados, Cuota Prudente Mediana, Pueden Pagar Prestamo Tipico, Tasa Impago, Tasa Impago Banco, AUC Regla, Color Regla, Monto Prudente Ofrecible 36m, Saldo Promedio Oferta, Cuota Prudente Oferta, Monto 12m/36m/60m Oferta |
| R3 | Descubrimientos kNN, Acierto Cola Larga kNN, Acierto Cola Larga Popularidad, Regla Mas Fuerte, P Destino dado Origen, Recomendacion 1, Descubrimiento kNN |
| D1 | Titulo Distrito, Num Prestamos, Prestamos Vigentes, Prestamos en Mora, Tasa Mora Vigente, Cartera Vigente, Saldo Neto Corte, Absorcion Vigente, Poblacion Distrito, Salario Promedio Distrito, Desempleo Distrito 1995, Origen Indicadores, Saldo Promedio por Cuenta, Saldo Promedio Banco, Estado Prestamo, Cartera Total, Cuota Mensual, Banda Capacidad |
| D2 | Titulo Cliente, Edad Cliente, Segmento Cliente, Arquetipo Cliente, Distrito Cuenta, Calificacion Cliente, Estado Prestamo, Cartera Total, Cuota Mensual, Banda Capacidad, Compromiso Ordenes, Indice Saturacion, Credito Externo Mensual, Saldo Neto Corte, Umbral Sobregiro, Num Ordenes, Cuota Maxima Prudente, Monto Maximo Prudente, Descubrimiento kNN |

**Documentos relacionados:** Carta de Diseño v8 (`01`), Informe 04 (recomendadores), Guía 07 (diseño y fundamentos), Informes 09 y 10 (carga y completitud), `scripts/27` (evidencia estadística de cada título).
