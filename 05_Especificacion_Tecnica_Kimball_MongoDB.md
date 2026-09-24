# UNIVERSIDAD TÉCNICA DE AMBATO
## FACULTAD DE INGENIERÍA EN SISTEMAS, ELECTRÓNICA E INDUSTRIAL
### CARRERA DE SOFTWARE — ASIGNATURA: INTELIGENCIA DE NEGOCIOS
### CICLO ACADÉMICO: AGOSTO 2026 – DICIEMBRE 2026

---

# INFORME TÉCNICO Y ESPECIFICACIÓN ARQUITECTÓNICA: MODELO DIMENSIONAL KIMBALL (SQL SERVER) Y SU DERIVACIÓN DOCUMENTAL NoSQL (MONGODB)

**Autores:** Alison Marcela Cobos Taco / Henry Daniel Lagua Flores  
**Docente:** Ing. Ruben Nogales, Mg.  
**Caso de Estudio:** Base de Datos Bancaria `Financial_ijs` (PKDD'99 Financial Discovery Challenge)  
**Versión:** 1.0 — Definitiva con Reconciliación Matemática y Gobernanza `$jsonSchema`

---

## 1. RESUMEN EJECUTIVO Y JUSTIFICACIÓN ARQUITECTÓNICA (PERSISTENCIA POLÍGLOTA)

El presente documento formaliza la coexistencia y justificación técnica entre dos paradigmas de almacenamiento de datos construidos a partir del caso de estudio bancario:

1. **Capa Analítica Corporativa (OLAP / Data Warehouse en SQL Server):**
   * **Motor:** Microsoft SQL Server (`DM_Financial_Kimball_v2`).
   * **Arquitectura:** Esquema en Constelación (*Galaxy Schema*) bajo la metodología de Ralph Kimball, integrado mediante dimensiones conformadas (`Dim_Cliente`, `Dim_Cuenta`, `Dim_Distrito`, `Dim_Tiempo`), catálogos estables y tres tablas de hechos atómicas (`Fact_Prestamos`, `Fact_Ordenes`, `Fact_Transacciones`).
   * **Propósito:** Agregaciones multidimensionales complejas, control de morosidad, auditoría histórica, evaluación de riesgo crediticio y alimentación de algoritmos de recomendación (Slope One, Coseno, Pearson, ITF).

2. **Capa Operacional y de Servicio de Baja Latencia (Serving Layer / NoSQL en MongoDB):**
   * **Motor:** MongoDB Community Server (`Financial`).
   * **Arquitectura:** Almacén documental orientado a agregados (*Domain-Driven Aggregate Pattern*), liderado por la colección **`FinancialMongo` (Cliente 360)** y colecciones departamentales de apoyo.
   * **Propósito:** Desacoplar el Data Warehouse de las aplicaciones cliente (banca web, móvil, CRM de sucursal). Permite a los sistemas transaccionales y comerciales consultar el perfil integral del cliente, sus domiciliaciones activas y su situación de crédito en tiempo $O(1)$ sin incurrir en costosos `JOINs` relacionales.

---

## 2. RESOLUCIÓN DE OBSERVACIONES Y CRITERIOS DE DISEÑO

### Observación 1: Redundancia Controlada y Fuente de Verdad
* **Patrón NoSQL:** Se implementó formalmente el **Patrón Híbrido Embebido/Referencial (*Hybrid Reference/Embed Pattern*)**.
* **Fuente Única de Verdad (*Single Source of Truth - SSOT*):** La base de datos relacional dimensional en **SQL Server (`DM_Financial_Kimball_v2`)** constituye la fuente de verdad maestra corporativa.
* **Justificación de la redundancia:**
  * En `FinancialMongo`, los arreglos `ordenes_recurrentes` y el objeto `prestamo_asociado` están desnormalizados para atender el 90% de las consultas de front-office (pantallas de atención al cliente) en una sola operación de lectura por clave `_id`.
  * Las colecciones independientes `ordenes` y `prestamos` existen para procesos departamentales batch específicos (e.g. ejecución diaria de la cámara de compensación de débitos o auditorías de la cartera vencida) sin tener que recorrer o desarmar el documento completo del cliente.
* **Mantenimiento de Consistencia:** La actualización se gobierna mediante el pipeline ETL programado ([`scripts/22_migrar_kimball_a_mongodb.py`](file:///C:/Users/henry/.gemini/antigravity/scratch/DocumentosBi/scripts/22_migrar_kimball_a_mongodb.py)), garantizando consistencia eventual estricta tras cada cierre contable.

---

### Observación 2: Semántica de `fecha_enriquecimiento` vs. Fechas Históricas
* **Aclaración Temporal:** Los datos transaccionales, cuentas y préstamos pertenecen al periodo histórico de la banca checa (**1993–1998**).
* **Campo de Metadatos:** El campo `fecha_actualizacion` / `fecha_enriquecimiento` registrado en las dimensiones y documentos corresponde exclusivamente a la **marca temporal de auditoría técnica del proceso ETL y ejecución del modelo K-Means**. No representa la fecha del negocio, sino el timestamp de gobernanza que certifica cuándo fue procesado el dato.

---

### Observación 3: Unificación del Criterio de Imputación del Distrito 69
Se unificó de forma simétrica el estándar en ambos motores:
* **Distrito 69 (Jeseník):**
  * `tasa_desempleo = 5.00%`
  * `tasa_criminalidad = 3736.00`
  * `es_imputado = true` (en SQL Server `BIT = 1`)
  * `metodo_imputacion = 'K-Means Clustered'`
* **Distritos 1 al 68 y 70 al 77 (76 distritos originales):**
  * `es_imputado = false` (en SQL Server `BIT = 0`)
  * `metodo_imputacion = 'Original PKDD99'` (estandarizado de forma idéntica en SQL Server y MongoDB, eliminando cualquier inconsistencia de nulos).

---

### Observación 4: Definición Formal del Arquetipo Demográfico y la Prueba $\chi^2$
* **Definición Estructural:** El atributo `arquetipo_demografico` proviene de la matriz ortogonal de 9 cuadrantes:
  $$\text{Macro-Región} \in \{\text{Praga}, \text{Bohemia}, \text{Moravia}\} \times \text{Tramo Etario} \in \{\text{Joven } (<30), \text{Adulto } (30\text{-}50), \text{Adulto Mayor } (>50)\}$$
* **Sustento del $\chi^2$:** La prueba estadística formal ejecutada sobre la tabla de contingencia de estos 9 arquetipos frente a la tenencia de crédito arrojó:
  $$\chi^2 = 63.7832 \quad (\text{gl} = 8, \; p = 8.39 \times 10^{-11})$$
  Esta prueba demuestra rigurosamente que la propensión al crédito **no es homogénea ni aleatoria** entre las regiones y edades, validando científicamente el uso de estos 9 arquetipos como base del perfilamiento bancario.

---

### Observación 5: Hechos Transaccionales Masivos y Pérdida de Claves
* **Tratamiento en MongoDB:**
  * En la colección `transacciones` ($1,056,320$ documentos), se preservaron las claves naturales operativas (`id_cuenta`, `id_cliente`), las variables temporales descompuestas (`anio`, `mes`, `dia`) y las tipologías homologadas (`tipo_transaccion`, `canal`, `k_symbol`).
  * Para evitar redundancia excesiva en un conjunto de datos que representa el 98% del volumen, no se duplica la información geográfica en cada línea transaccional, ya que esta se resuelve directamente navegando hacia el cliente o la cuenta.
* **Índices de Alto Rendimiento:** Se configuró el índice compuesto nativo:
  `db.transacciones.create_index([("id_cuenta", 1), ("fecha", 1)])`
  Permitiendo lecturas de estados de cuenta cronológicos en menos de 5 milisegundos.
* **Evolución Arquitectónica:** En un entorno productivo de MongoDB 5.0+, esta colección se define nativamente como una **Colección de Series de Tiempo (*Time Series Collection*)** utilizando `fecha` como campo de tiempo (*timeField*) y `id_cuenta` como metadato (*metaField*).

---

### Observación 6: Manejo de Métricas Semiaditivas (`saldo_cuenta`) en NoSQL
* **Restricción Matemática Fundamental:** El saldo bancario (`saldo_cuenta`) es una **métrica semiaditiva**. Es aditiva a través de las cuentas en un instante fijo, pero **estrictamente no aditiva a lo largo de la dimensión temporal**.
* **Directriz de Consulta en MongoDB:**
  * Queda **técnicamente prohibido** utilizar el acumulador `$sum` sobre `saldo_cuenta` en etapas de agrupamiento `$group` que involucren intervalos de tiempo (produciría sumas infladas sin significado financiero).
  * Para obtener el saldo vigente o de cierre de periodo en MongoDB, se deben utilizar los acumuladores posicionales temporales:
    ```javascript
    // Consulta correcta del saldo de cierre por cuenta:
    db.transacciones.aggregate([
      { $sort: { id_cuenta: 1, fecha: 1 } },
      { $group: {
          _id: "$id_cuenta",
          saldo_cierre: { $last: "$saldo_cuenta" },
          fecha_ultimo_movimiento: { $last: "$fecha" }
      }}
    ])
    ```

---

### Observación 7: Gobernanza con `$jsonSchema` y Reconciliación Cuantitativa

#### A. Validadores `$jsonSchema` Activos en MongoDB
Se aplicaron validadores estrictos mediante el comando `collMod` en las colecciones de la base de datos `Financial`:
* **`FinancialMongo`:** Valida la presencia y tipado obligatorio de `id_cliente`, `datos_personales.sexo`, `evaluacion_crediticia.calificacion`, `perfil_analitico.arquetipo_demografico` y subdocumento `distrito`.
* **`distritos`:** Valida que `tasa_desempleo` y `tasa_criminalidad` sean numéricas y que el bloque `auditoria.es_imputado` sea booleano obligatorio.
* **`prestamos`:** Exige que `codigo_estado` pertenezca al catálogo enumerado `['A', 'B', 'C', 'D']` y que `cuota_mensual` sea numérica positiva.
* **`ordenes`:** Restringe las categorías a códigos estructurados.

#### B. Resultados de la Reconciliación Matemática (Script `scripts/24_reconciliacion_kimball_mongo.py`)

La ejecución determinista de validación cruzada entre Microsoft SQL Server y MongoDB arrojó una **concordancia absoluta**:

| Entidad / Proceso de Negocio | Registros SQL Server | Documentos MongoDB | Diferencia ($\Delta$) | Medida Monetaria SQL Server | Medida Monetaria MongoDB | Delta Financiero | Estado |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Distritos Administrativos** | 77 | 77 | **0** | N/A | N/A | $0.00 | 🟢 100% Idéntico |
| **Clientes Totales** | 5,369 | 5,369 | **0** | N/A | N/A | $0.00 | 🟢 100% Idéntico |
| **Clientes con Crédito** | 682 | 682 | **0** | N/A | N/A | $0.00 | 🟢 100% Idéntico |
| **Cartera de Préstamos** | 682 | 682 | **0** | **\$103,261,740.00** | **\$103,261,740.00** | **\$0.00** | 🟢 100% Al Centavo |
| **Cuotas Mensuales Crédito** | 682 | 682 | **0** | **\$2,858,033.00** | **\$2,858,033.00** | **\$0.00** | 🟢 100% Al Centavo |
| **Débitos de Órdenes Fijas** | 6,471 | 6,471 | **0** | **\$21,229,041.00** | **\$21,229,041.00** | **\$0.00** | 🟢 100% Al Centavo |
| **Movimientos Transaccionales** | 1,056,320 | 1,056,320 | **0** | **\$6,257,862,197.00** | **\$6,257,862,197.00** | **\$0.00** | 🟢 100% Al Centavo |

---

### Observación 8 y 9: Verificación de la Constelación (*Galaxy Schema*) y Claves en Kimball
* **Verificación de Claves:** Se certificó en el DDL físico que `Fact_Prestamos` cuenta con la clave foránea obligatoria `sk_cliente INT NOT NULL` referenciando directamente a `Dim_Cliente(sk_cliente)` con integridad referencial activa.
* **Topología:** El modelo es formalmente un **Esquema en Constelación (*Galaxy Schema*)** dado que las tres tablas de hechos (`Fact_Prestamos`, `Fact_Transacciones` y `Fact_Ordenes`) comparten cuatro dimensiones conformadas canónicas: `Dim_Tiempo`, `Dim_Cuenta`, `Dim_Cliente` y `Dim_Distrito`.

---

## 3. CONCLUSIÓN TÉCNICA

La coexistencia entre **Kimball (SQL Server)** y **MongoDB (`Financial`)** no constituye una redundancia arbitraria, sino una implementación canónica de **Arquitectura de Datos Híbrida / Políglota**:
* **SQL Server** garantiza integridad referencial ACID, rigor dimensional para minería de datos, control analítico de morosidad y consistencia en el cálculo de recomendadores.
* **MongoDB** actúa como la capa de persistencia y despacho de alto rendimiento, exponiendo un modelo documental pre-agregado que elimina la sobrecarga de consultas analíticas sobre los sistemas operacionales.

Los scripts de validación, esquemas y reconciliación quedan completamente respaldados en el repositorio:
* [`scripts/24_reconciliacion_kimball_mongo.py`](file:///C:/Users/henry/.gemini/antigravity/scratch/DocumentosBi/scripts/24_reconciliacion_kimball_mongo.py)
* [`scripts/25_aplicar_jsonschema_mongo.py`](file:///C:/Users/henry/.gemini/antigravity/scratch/DocumentosBi/scripts/25_aplicar_jsonschema_mongo.py)
* Archivo binario dump: `Financial_mongo_dump.gz` (22 MB).
