# UNIVERSIDAD TÉCNICA DE AMBATO
## FACULTAD DE INGENIERÍA EN SISTEMAS ELECTRÓNICA E INDUSTRIAL
### CARRERA DE SOFTWARE — ASIGNATURA: INTELIGENCIA DE NEGOCIOS
### CICLO ACADÉMICO: AGOSTO 2026 – DICIEMBRE 2026

---

# INFORME 10 — DATAFRAMES, COMPLETITUD DE DATOS Y CARGA EN KIMBALL

**Autores:** Alison Marcela Cobos Taco / Henry Daniel Lagua Flores  
**Docente:** Ing. Ruben Nogales, Mg.  
**Antecede:** Informe 09 (carga OLTP → Kimball, script 31)  
**Reglas de completitud:** Informe 03 (Limpieza y Transformación de Datos)  
**Scripts:** `scripts/32_extraer_dataframes_kimball.py` → `scripts/33_completitud_datos.py` → `scripts/34_carga_completitud_kimball.py`  
**Evidencia:** `metricas_completitud_datos.json`, `metricas_carga_completitud.json` y tabla `Auditoria_Carga`

---

## 1. Resumen

| Paso | Script | Resultado | Tiempo |
| :-: | :--- | :--- | ---: |
| 1. Extraer DataFrames | `32_extraer_dataframes_kimball.py` | 5 DataFrames desde el Data Mart + columnas originales del OLTP con sus huecos | 51 s |
| 2. Completar y verificar | `33_completitud_datos.py` | 7 columnas con huecos reales completadas; huecos estructurales conservados; **14 de 14 verificaciones OK** | 52 s |
| 3. Cargar en Kimball | `34_carga_completitud_kimball.py` | Distrito 69, 5,369 clientes y 1,056,320 transacciones actualizados; **12 de 12 pruebas OK** | 48 s |

Después de la carga, `scripts/27_evidencia_estadistica_dashboard.py` se volvió a ejecutar sobre los DataFrames nuevos. Todas sus cifras y pruebas estadísticas (KPIs, χ², Fisher, ANOVA, Welch) salen **idénticas** a las ya citadas en la Guía 07. La única diferencia es la etiqueta de la categoría de intereses, que pasa de "Intereses Ganados / Abono Bancario" a "Intereses Ganados".

---

## 2. Cómo ejecutar la cadena completa

```bash
python scripts/31_etl_oltp_a_kimball.py
```

```bash
python scripts/32_extraer_dataframes_kimball.py
```

```bash
python scripts/33_completitud_datos.py
```

```bash
python scripts/34_carga_completitud_kimball.py
```

* El script 31 recarga el Data Mart desde el OLTP y deja sin asignar los datos que completa esta etapa (distrito 69, enriquecimiento de clientes y concepto de las transacciones). Por eso los scripts 32 a 34 se ejecutan siempre después del 31.
* El script 34 se niega a cargar si el 33 no terminó con todas sus verificaciones en OK.
* Ningún script sobrescribe los DataFrames de entrada: el 33 escribe versiones `_clean` / `_completado`.

---

## 3. Paso 1 — DataFrames generados (script 32)

| Archivo | Filas × columnas | Origen | Huecos detectados |
| :--- | :--- | :--- | :--- |
| `dataframes/df_distritos.csv` | 77 × 9 | `Dim_Distrito` | Desempleo y criminalidad 1995 del distrito 69 |
| `dataframes/df_prestamos.csv` | 682 × 28 | `Fact_Prestamos` + dimensiones | Desempleo y criminalidad del distrito 69 (8 préstamos) |
| `dataframes/df_ordenes.csv` | 6,471 × 14 | `Fact_Ordenes` + `orders` (OLTP: `k_symbol`, `bank_to`, `account_to`) | `k_symbol`: 1,379 |
| `dataframes/df_cliente_consolidado.csv` | 5,369 × 29 | `Dim_Cliente` + agregados de los tres hechos | Etiqueta 5,080 · distrito 69: 61 · préstamo: 4,687 · promedio de órdenes: 1,611 · saldos: 869 |
| `dataframes/df_transacciones.csv.gz` | 1,056,320 × 21 | `Fact_Transacciones` + `trans` (OLTP: `operation`, `k_symbol`, `bank`, `account`) | `operation` 183,114 · `k_symbol` 535,314 · `bank` 760,931 · `account` 782,812 |

Los huecos coinciden exactamente con el diagnóstico del Informe 03.

---

## 4. Paso 2 — Completitud (script 33)

### 4.1 Clasificación de los huecos

| Tipo | Columnas | Tratamiento |
| :--- | :--- | :--- |
| **Estructural:** el cliente no tiene el producto | `etiqueta_buen_pagador` (5,080), `id_prestamo` y `plazo_prestamo` (4,687), `monto_promedio_orden` (1,611), `saldo_*` de los 869 cotitulares | Se conservan como nulos. Se añaden marcas explícitas: `es_titular`, `tiene_ordenes` y `calificacion_pago` (Buen Pagador / Mal Pagador / Sin evaluar) |
| **Real:** el dato existe en el negocio pero falta | Distrito 69 (1995), `orders.k_symbol`, `trans.operation`, `trans.k_symbol`, `trans.bank`, `trans.account` | Se completan con las reglas siguientes |

El script verifica que los nulos que quedan son **exactamente** los estructurales. Por ejemplo, los 869 nulos de saldo corresponden uno a uno a los 869 cotitulares, y los 4,687 nulos de préstamo a los clientes que no son titulares de un préstamo.

### 4.2 Distrito 69 (Jeseník): cambio de método respecto al Informe 03

El Informe 03 imputó a Jeseník los valores de 1995 de Šumperk (desempleo 5.0, criminalidad 3,736). Al revisar los datos se encontró un problema con la criminalidad:

| Distrito | Población | Delitos 1995 | Delitos 1996 |
| :--- | ---: | ---: | ---: |
| Šumperk | 127,369 | 3,736 | 2,807 |
| Jeseník | 42,821 | — | 1,358 |

Los delitos de Šumperk caen 929 de 1995 a 1996, justo cuando Jeseník se separa. Es decir, **la cifra de 1995 de Šumperk incluye el territorio de Jeseník**. Además, la criminalidad es un conteo, no una tasa, así que copiarlo a un distrito con un tercio de la población lo sobrestima unas 2.7 veces.

**Método adoptado:** tomar el valor de 1996 **del propio Jeseník** y ajustarlo con la razón mediana 1995/1996 de los otros distritos. Ambos indicadores cambian muy poco de un año al otro (correlación 1995–1996 entre distritos: 0.956 en desempleo y 0.998 en criminalidad).

| Indicador | Valor 1996 de Jeseník | Razón mediana 1995/1996 | Valor imputado 1995 |
| :--- | ---: | ---: | ---: |
| Desempleo (%) | 7.00 | 0.8333 | **5.83** |
| Criminalidad (delitos) | 1,358 | 0.9766 | **1,326** |

**Validación del método:** se aplicó a cada uno de los 75 distritos que tienen ambos años (dejando ese distrito fuera del cálculo de la razón) y se comparó con su valor real de 1995. El error absoluto medio fue de **0.46 puntos** en desempleo y el error relativo medio de **7.3%** en criminalidad.

| Alternativa | Desempleo | Criminalidad | Motivo de descarte |
| :--- | ---: | ---: | :--- |
| Copiar Šumperk 1995 (Informe 03) | 5.00 | 3,736 | El conteo de 1995 de Šumperk incluye a Jeseník |
| K-Means, mediana del clúster (Informe 03, anexo) | 5.00 | 4,063 | Estima con distritos parecidos teniendo el dato real del propio distrito en 1996 |
| **Razón 1995/1996 sobre el dato 1996 (adoptado)** | **5.83** | **1,326** | Usa el dato del propio distrito; error verificable en los otros 75 |

En el Data Mart queda `es_imputado = 1` y `metodo_imputacion = 'Razon 1995/1996 sobre dato 1996'`; los otros 76 distritos quedan como `Original PKDD99`.

### 4.3 Órdenes

Los 1,379 `k_symbol` vacíos pasan a `SIN_ESPECIFICAR`. Es el mismo criterio que se aplicó en OpenRefine (Informe 03, imágenes 1–7), ahora reproducible por código.

### 4.4 Transacciones (1,056,320 filas, pipeline vectorizado)

| Regla | Condición | Valor asignado | Filas |
| :--- | :--- | :--- | ---: |
| 1.1 | `operation` nula, `PRIJEM` y `k_symbol = UROK` | `operation = ABONO_INTERESES` | 183,114 |
| 2.1 | `k_symbol` nulo, `VYDAJ` y monto = cuota del préstamo de la cuenta | `UVER` | 21 |
| 2.2 | `k_symbol` nulo, `VYDAJ` y (cuenta, monto) = una única orden permanente con propósito conocido | `SIPO` 10,103 · `POJISTNE` 809 | 10,912 |
| 2.3 | `k_symbol` nulo y `operation` en `VYBER`, `VYBER KARTOU` | `RETIRO_EFECTIVO` | 282,657 |
| 2.4 | `k_symbol` nulo y `operation = VKLAD` | `DEPOSITO_EFECTIVO` | 156,743 |
| 2.5 | `k_symbol` nulo y `VYDAJ` (residual) | `TRANSFERENCIA_EXTERNA` | 50,093 |
| 2.6 | `k_symbol` nulo y `PRIJEM` (residual) | `INGRESO_ORDINARIO` | 34,888 |
| 3.1 | Sin banco y concepto `UROK`, `SLUZBY` o `SANKC. UROK` | Contraparte "Sistema central" (`SISTEMA_CENTRAL_BANCO` / `TESORERIA_INTERNA`) | 340,523 |
| 3.2 | Sin banco y operación de caja (`VKLAD`, `VYBER`, `VYBER KARTOU`) | Contraparte "Caja propia" (`BANCO_PROPIO_LOCAL` / `CAJA_VENTANILLA_ATM`) | 420,407 |
| 3.3 | Sin banco en el resto | Contraparte "Entidad externa no registrada" | 1 |
| 3.4 | Con banco pero sin cuenta | `account = CUENTA_EXTERNA_NO_REGISTRADA` | 21,881 |

Diferencias con el script anterior (`completar_transacciones.py`):

* **Orden de la regla de contraparte corregido.** Las 155,832 comisiones y los 1,577 intereses sancionatorios vienen con `operation = VYBER`. La regla de caja se evaluaba primero y los clasificaba como retiros en ventanilla; ahora se reconocen como cargos del sistema central.
* **Se elimina la heurística de comisiones de fin de mes** (montos 14.60, 25, 30…). No asignaba ninguna transacción: los montos de la fuente son enteros y las 155,832 comisiones ya vienen etiquetadas.
* **Se agregan dos columnas de trazabilidad:** `metodo_concepto` (Fuente / Cruce con préstamos / Cruce con órdenes / Regla de canal / Residual) y `tipo_contraparte`.
* **Ruta relativa al repositorio** en lugar de una carpeta fija del equipo de un integrante. Se deja de generar el Parquet, que no se versiona; queda el CSV comprimido.

**Advertencias sobre la confianza de algunas inferencias:** las 21 cuotas `UVER` inferidas y 33 de las 10,912 órdenes cruzadas corresponden a **retiros en efectivo** cuyo monto coincide con la cuota o la orden. Son pocas (0.005% de las transacciones) y quedan identificadas por `metodo_concepto` y `tipo_contraparte = Caja propia`, así que pueden excluirse de cualquier análisis.

**Distribución final** (coincide con la tabla 2 del Informe 03):

| Concepto | Transacciones | Del cual inferido |
| :--- | ---: | ---: |
| Retiro en efectivo | 282,657 | 282,657 |
| Intereses ganados (`UROK`) | 183,114 | 0 |
| Depósito en efectivo | 156,743 | 156,743 |
| Comisión por servicios (`SLUZBY`) | 155,832 | 0 |
| Servicios del hogar (`SIPO`) | 128,168 | 10,103 |
| Transferencia saliente | 50,093 | 50,093 |
| Ingreso ordinario | 34,888 | 34,888 |
| Pensión (`DUCHOD`) | 30,338 | 0 |
| Seguro (`POJISTNE`) | 19,309 | 809 |
| Cuota de préstamo (`UVER`) | 13,601 | 21 |
| Interés sancionatorio (`SANKC. UROK`) | 1,577 | 0 |
| **Total** | **1,056,320** | **535,314** |

### 4.5 Verificaciones del script 33 (14 de 14 OK)

| Verificación | Resultado |
| :--- | :-: |
| Distritos sin nulos tras imputar | OK |
| Préstamos sin nulos (8 del distrito 69 completados) | OK |
| Órdenes sin nulos y monto sin cambios ($21,229,041) | OK |
| Cliente 360: solo quedan nulos estructurales | OK |
| Nulos de saldo = 869 cotitulares | OK |
| Nulos de préstamo = clientes sin préstamo como titular | OK |
| Nulos de promedio de órdenes = clientes sin órdenes | OK |
| Transacciones sin nulos | OK |
| Filas de transacciones sin cambios (1,056,320) | OK |
| Monto de transacciones sin cambios ($6,257,862,197) | OK |
| Conceptos que venían de la fuente no modificados | OK |
| Todos los conceptos tienen traducción | OK |
| Categoría analítica intacta (intereses = 183,114) | OK |

---

## 5. Paso 3 — Carga en Kimball (script 34)

### 5.1 Qué se escribe en el Data Mart

| Tabla | Columnas | Origen |
| :--- | :--- | :--- |
| `Dim_Distrito` | `tasa_desempleo`, `tasa_criminalidad` (1995), `es_imputado`, `metodo_imputacion`, `fecha_enriquecimiento` | `df_distritos_clean.csv` |
| `Dim_Cliente` | `macro_region`, `segmento_edad`, `arquetipo_demografico`, `tiene_prestamo`, `total_ordenes_activas`, `saldo_promedio`, `calificacion_pago_desc`, `fecha_enriquecimiento` | `df_cliente_consolidado_clean.csv` |
| `Dim_Concepto_Movimiento` (**nueva**) | 19 combinaciones de concepto × método × contraparte | `df_transacciones_completado.csv.gz` |
| `Fact_Transacciones` | `sk_concepto` (**nueva clave**) en las 1,056,320 filas | `df_transacciones_completado.csv.gz` |

**¿Por qué una dimensión nueva y no modificar `Dim_Operacion`?** `Dim_Operacion` conserva las 15 combinaciones **tal como vienen de la fuente** (Carta v8, sección 11). El concepto completado es información derivada. Al guardarlo en una dimensión aparte, cada transacción conserva ambas versiones: lo que dijo el banco y lo que se infirió, con el método usado. El DDL (`sql/01`) ya incluye esta dimensión, así que una recreación desde cero la crea.

**Segmentación de edad en `Dim_Cliente`:** se mantiene la de los estereotipos del Informe 04 (Joven < 30, Adulto 30–50, Adulto Mayor > 50) para no alterar ese análisis. El dashboard (pestaña P6) usa otra segmentación de 4 grupos, calculada en DAX. Unificarlas queda como decisión pendiente.

**Saldo promedio de los cotitulares:** queda en `NULL`, porque sus movimientos se registran en la cuenta del titular. El *write-back* anterior lo ponía en 0, lo que inventaba un saldo nulo para 869 clientes.

### 5.2 Pruebas del script 34 (12 de 12 OK)

| Prueba | Esperado | Obtenido |
| :--- | :--- | :--- |
| Distrito 69 imputado (desempleo, criminalidad, marca) | 5.83 · 1,326 · sí | 5.83 · 1,326 · sí |
| Distritos sin nulos en indicadores 1995 | 0 | 0 |
| Clientes con macro-región, segmento y arquetipo | 5,369 | 5,369 |
| Clientes titulares de préstamo | 682 | 682 |
| Órdenes asignadas a clientes | 6,471 | 6,471 |
| Saldo promedio nulo solo en cotitulares | 869 | 869 |
| Calificación de pago | Buen 258 · Mal 31 · Sin evaluar 5,080 | Idéntico |
| Transacciones sin concepto asignado | 0 | 0 |
| Transacciones por código de concepto (11 códigos) | Igual al DataFrame completado | Idéntico |
| Transacciones con concepto inferido | 535,314 | 535,314 |
| Monto de transacciones sin cambios | $6,257,862,197.00 | $6,257,862,197.00 |
| Saldo neto al corte sin cambios | $197,140,434.00 | $197,140,434.00 |

### 5.3 `Dim_Concepto_Movimiento` cargada

| sk | Código | Método | Contraparte | Transacciones |
| :-: | :--- | :--- | :--- | ---: |
| 1 | DEPOSITO_EFECTIVO | Regla de canal | Caja propia | 156,743 |
| 2 | DUCHOD | Fuente | Entidad externa registrada | 30,338 |
| 3 | INGRESO_ORDINARIO | Residual | Entidad externa registrada | 34,888 |
| 4 | POJISTNE | Cruce con órdenes | Caja propia | 7 |
| 5 | POJISTNE | Cruce con órdenes | Entidad externa registrada | 802 |
| 6 | POJISTNE | Fuente | Entidad externa registrada | 18,500 |
| 7 | RETIRO_EFECTIVO | Regla de canal | Caja propia | 263,626 |
| 8 | RETIRO_EFECTIVO | Regla de canal | Entidad externa registrada | 19,031 |
| 9 | SANKC. UROK | Fuente | Sistema central | 1,577 |
| 10 | SIPO | Cruce con órdenes | Caja propia | 24 |
| 11 | SIPO | Cruce con órdenes | Entidad externa registrada | 10,079 |
| 12 | SIPO | Fuente | Entidad externa registrada | 118,065 |
| 13 | SLUZBY | Fuente | Sistema central | 155,832 |
| 14 | TRANSFERENCIA_EXTERNA | Residual | Entidad externa registrada | 50,093 |
| 15 | UROK | Fuente | Sistema central | 183,114 |
| 16 | UVER | Cruce con préstamos | Caja propia | 7 |
| 17 | UVER | Cruce con préstamos | Entidad externa registrada | 14 |
| 18 | UVER | Fuente | Entidad externa no registrada | 1 |
| 19 | UVER | Fuente | Entidad externa registrada | 13,579 |

---

## 6. Archivos generados

| Archivo | Descripción |
| :--- | :--- |
| `scripts/32_extraer_dataframes_kimball.py` | Paso 1: DataFrames desde Kimball + OLTP |
| `scripts/33_completitud_datos.py` | Paso 2: reglas de completitud y verificación |
| `scripts/34_carga_completitud_kimball.py` | Paso 3: carga en Kimball y pruebas |
| `dataframes/df_distritos.csv` / `_clean.csv` | Distritos antes y después de imputar |
| `dataframes/df_prestamos.csv` / `_clean.csv` | Préstamos antes y después |
| `dataframes/df_ordenes.csv` / `_clean.csv` | Órdenes antes y después |
| `dataframes/df_cliente_consolidado.csv` / `_clean.csv` | Cliente 360 antes y después |
| `dataframes/df_transacciones.csv.gz` / `_completado.csv.gz` | Transacciones antes y después |
| `metricas_completitud_datos.json` | Diagnóstico inicial y final, conteo de cada regla, alternativas del distrito 69 y verificaciones |
| `metricas_carga_completitud.json` | Pruebas de la carga y contenido de `Dim_Concepto_Movimiento` |
| `sql/01_DDL_Kimball_DM_Financial.sql` | Incluye `Dim_Concepto_Movimiento` y `Fact_Transacciones.sk_concepto` |
| `scripts/27_evidencia_estadistica_dashboard.py` | `monto_en_riesgo_BD` usa el monto original B + D (Carta v8), ya que `saldo_pendiente_estimado` ahora es el saldo por cobrar |

Los scripts anteriores (`completar_transacciones.py`, `imputar_final.py`, `20_write_back_kimball_enriquecido.py`, `00_generar_4_dataframes.py`) se conservan como antecedente, pero **ya no forman parte de la cadena**: fueron reemplazados por los scripts 32 a 34.

---

## 7. Pendientes

| # | Pendiente | Motivo |
| :-: | :--- | :--- |
| 1 | Actualizar los documentos 05 y 08, que citan la imputación anterior del distrito 69 (5.00 / 3,736, "K-Means Clustered") | Cambio de método de esta etapa |
| 2 | Decidir una única segmentación de edad para `Dim_Cliente` y el dashboard | Hoy conviven 3 grupos (Informe 04) y 4 grupos (P6) |
| 3 | Proyecto Power BI Kimball, medidas DAX y réplica MongoDB | Siguen pendientes desde el Informe 09 |
