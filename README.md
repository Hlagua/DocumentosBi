# UNIVERSIDAD TÉCNICA DE AMBATO
## FACULTAD DE INGENIERÍA EN SISTEMAS ELECTRÓNICA E INDUSTRIAL
### CARRERA DE SOFTWARE
### CICLO ACADÉMICO: AGOSTO 2026 – DICIEMBRE 2026

---

# INFORME DE GUÍA PRÁCTICA

## I. PORTADA

| Campo | Detalle |
| :--- | :--- |
| **Tema:** | Carta de Diseño (v6 — Versión Definitiva: Corrección de Métricas Semiaditivas, Dimensión de Catálogo SCD 0, Semántica de Riesgo `tkeys`, Preservación Decimal y Arquitectura Dimensional Kimball) |
| **Unidad de Organización Curricular:** | PROFESIONAL |
| **Nivel y Paralelo:** | 6to Software "A" |
| **Alumnos participantes:** | Cobos Taco Alison Marcela / Lagua Flores Henry Daniel |
| **Asignatura:** | Inteligencia de Negocios |
| **Docente:** | Ing. Ruben Nogales, Mg. |

---

## II. INFORME DE GUÍA PRÁCTICA

### 2.1 Objetivos

#### General:
Diseñar e implementar una solución integral de Inteligencia de Negocios para la gestión del riesgo crediticio, control de morosidad, monitoreo de liquidez institucional y análisis transaccional a partir de la base de datos `Financial_ijs`, formulando la Carta de Diseño oficial y justificando técnicamente la adopción de la arquitectura dimensional de Ralph Kimball frente a la metodología corporativa de Bill Inmon para la optimización de la toma de decisiones estratégicas.

#### Específicos:
1. **Estructurar el levantamiento formal de requisitos analíticos** mediante la Carta de Diseño, identificando los procesos de negocio críticos, fuentes operativas, reglas de calidad de datos, transformaciones ETL requeridas y métricas clave (tasa de morosidad activa vigente, tasa de incumplimiento histórico y ratio de absorción de depósitos).
2. **Modelar una arquitectura dimensional bajo la metodología de Ralph Kimball**, definiendo el grano atómico por proceso de negocio, la Matriz de Bus de Datos Corporativo (*Bus Matrix*), dimensiones conformadas (`Dim_Cliente`, `Dim_Cuenta`, `Dim_Distrito`, `Dim_Tiempo`), dimensiones de catálogo estables (`Dim_Estado_Prestamo`, `Dim_Operacion`, `Dim_Orden`) y un esquema en constelación (*galaxy schema*) para préstamos, órdenes y transacciones monetarias.
3. **Evaluar comparativamente las arquitecturas de Ralph Kimball y Bill Inmon**, fundamentando por qué el enfoque *bottom-up* con esquemas estrella e integración por dimensiones conformadas supera en agilidad, desempeño OLAP y coste de mantenimiento al enfoque *top-down* (EDW normalizado en 3FN) cuando se parte de una fuente transaccional relacional única.
4. **Definir con rigor técnico la tipología de Slowly Changing Dimensions (SCD)** y el tratamiento de métricas semiaditivas, clasificando los catálogos como SCD Tipo 0, la demografía como SCD Tipo 1 y especificando el cálculo de liquidez institucional mediante el último saldo temporal registrado en transacciones.

### 2.2 Modalidad
Presencial

### 2.3 Tiempo de duración
* **Presenciales:** 6 horas
* **No presenciales:** 0 horas

### 2.4 Instrucciones
Seguir el formato oficial e ir completando las secciones correspondientes al trabajo desarrollado en clase, aplicando los estándares de modelado dimensional y diseño analítico sobre el caso de estudio bancario `Financial_ijs`.

### 2.5 Listado de equipos, materiales y recursos
* **Materiales generales:** Computador, Internet, Apuntes de clase, Herramientas de consulta SQL (SSMS, Python, DBeaver).
* **TAC (Tecnologías para el Aprendizaje y Conocimiento):**
  * [x] Plataformas educativas
  * [ ] Simuladores y laboratorios virtuales
  * [x] Aplicaciones educativas (SQL Server Developer, SSIS, Visual Studio)
  * [ ] Recursos audiovisuales
  * [ ] Gamificación
  * [x] Inteligencia Artificial
  * [ ] Otros

### 2.6 Actividades por desarrollar
Detalladas en la guía práctica provista por el docente de la cátedra.

---

### 2.7 Resultados obtenidos

#### Datos Generales del levantamiento

| Campo | Detalle | Campo | Detalle |
| :--- | :--- | :--- | :--- |
| **Institución / Empresa** | Banco Comercial Checo / `Financial_ijs` | **Área analizada** | Gestión de Riesgo Crediticio, Cartera de Préstamos y Operaciones Financieras |
| **Carrera / Asignatura** | Ingeniería de Software / Inteligencia de Negocios | **Periodo académico** | Agosto 2026 – Diciembre 2026 |
| **Integrantes** | Henry Daniel Lagua Flores; Alison Marcela Cobos Taco | **Docente** | Ing. Ruben Nogales, Mg. |
| **Fecha de levantamiento** | 24 de agosto de 2026 (Revisión v6: 12 de septiembre de 2026) | **Versión** | 6.0 (Definitiva) |
| **Persona entrevistada** | N/A — Proyecto basado en dataset benchmark público (CTU Prague / PKDD 1999) | **Cargo** | N/A |

---

#### Proceso o unidad de negocio
Gestión y colocación de cartera de crédito, control de morosidad, seguimiento de órdenes de pago programadas y monitoreo de liquidez transaccional institucional.

---

#### Necesidad del negocio o problema a resolver

| Campo | Contenido |
| :--- | :--- |
| **Problema detectado** | La institución financiera presenta tres vulnerabilidades críticas detectadas en sus datos históricos (1993–1998):<br>1. **Aceleración de la morosidad crediticia:** De los 682 préstamos otorgados, 45 créditos se encuentran en mora activa irrecuperable (**Estado D**). Al evaluarse sobre la cartera vigente (403 créditos en estado C al día + 45 en mora D = 448 préstamos), la **Tasa de Morosidad Activa Vigente alcanza un alarmante 10.04%** (sobre cartera histórica total es del 6.60%). Más crítico aún es la tendencia temporal: los préstamos que entraron en mora se dispararon de **2 casos en 1994 a 23 casos en 1997** (un incremento del 1,050%). En los 234 créditos ya finalizados, el **13.25% (31 créditos, Estado B)** terminó en quebranto con deuda impaga.<br>2. **Exposición de liquidez:** La cartera colocada en préstamos asciende a **\$103,261,740.00**, lo que compromete el **52.38% del saldo total de depósitos** captados (\$197,140,434.00 al cierre del periodo), exponiendo al banco a tensiones de liquidez ante retiros masivos.<br>3. **Falta de integración analítica:** Las órdenes de débito automático (cuotas de leasing, préstamos `UVER` y servicios `SIPO`), las transacciones diarias y la colocación crediticia operan en silos aislados, impidiendo evaluar la capacidad de endeudamiento global del cliente. |
| **Decisión que se desea mejorar** | Optimizar el otorgamiento de créditos mediante políticas de riesgo basadas en historial y capacidad de pago; focalizar acciones de cobranza temprana en distritos con alta morosidad; monitorear la cobertura de liquidez entre saldos de captación y desembolsos crediticios; y detectar patrones operativos atípicos en cuentas corrientes. |
| **Usuarios del análisis** | Gerencia de Riesgo y Crédito, Oficiales de Cobranza, Gerencia de Operaciones y Tesorería, Analistas de Inteligencia de Negocios. |
| **Preguntas clave que debe responder el sistema** | 1. ¿Cómo evoluciona la morosidad activa año a año y cuál es la tasa de pérdida en préstamos cerrados?<br>2. ¿Qué distritos geográficos concentran el mayor riesgo crediticio y mora relativa?<br>3. ¿Qué porcentaje del saldo disponible de los clientes está comprometido en la cartera de créditos colocada?<br>4. ¿Qué tipos de operaciones bancarias concentran el mayor flujo monetario y cómo varía el balance promedio?<br>5. ¿Qué cuentas tienen órdenes de débito programadas que saturan su saldo operativo habitual?<br>6. ¿Cuáles son los clientes con antecedentes de impago histórico (`Estado B`) para denegarles nuevos productos? |
| **Alcance del análisis** | Datos bancarios del periodo 1993–1998 correspondientes a 4,500 cuentas, 5,369 clientes, 682 préstamos otorgados, 6,471 órdenes recurrentes y 1,056,320 transacciones financieras. El análisis de tarjetas plásticas (`cards`, 892 registros) se delimita formalmente para una fase complementaria. |
| **Beneficio esperado** | Reducción de la morosidad mediante alertas preventivas de riesgo geográfico y crediticio; control diario de la posición de liquidez institucional; detección oportuna de clientes insolventes; y autonomía de consulta para usuarios de negocio mediante cubos y tableros interactivos. |

---

#### Objetivos analíticos del modelo OLAP

| Objetivo específico | Pregunta de negocio | Indicador asociado |
| :--- | :--- | :--- |
| **Analizar la evolución de la morosidad activa** | ¿Cómo se incrementan los créditos en mora (Estado D) año a año? | Cantidad de préstamos en mora D y Tasa de Morosidad Activa Vigente (10.04%). |
| **Medir la calidad histórica de originación** | ¿Qué porcentaje de los créditos concedidos que ya terminaron cerraron con pérdidas no recuperadas? | Tasa de Incumplimiento Histórico (Estado B / [A+B] = 13.25%). |
| **Evaluar la concentración geográfica del riesgo** | ¿Qué distritos concentran la mayor cantidad y monto de préstamos y cuál es su tasa de mora relativa? | Préstamos por distrito, Monto colocado por distrito y Tasa de mora distrital. |
| **Monitorear la liquidez y cobertura de cartera** | ¿Qué porcentaje del dinero depositado por los ahorristas está inmovilizado en préstamos? | Ratio de Absorción Crediticia: $\frac{\sum \text{Monto Préstamos}}{\text{Saldo Total Depósitos al Corte}}$ (52.38%). |
| **Caracterizar el comportamiento transaccional** | ¿Qué operaciones mueven el mayor flujo de capital y cómo impactan en el balance de las cuentas? | Conteo de transacciones, Monto total acumulado y Monto promedio por tipo de operación (`Dim_Operacion`). |
| **Monitorear compromisos de órdenes recurrentes** | ¿Qué volumen y monto de pagos fijos automáticos tienen programados las cuentas deudoras? | Conteo y Monto promedio de órdenes por símbolo (`SIPO`, `UVER`, `POJISTNE`, `LEASING`). |

---

#### Procesos del negocio a modelar

| Proceso | Descripción breve | Evento medible | Sistema fuente | Prioridad |
| :--- | :--- | :--- | :--- | :--- |
| **1. Colocación y Gestión de Cartera Crediticia** | Otorgamiento de préstamos personales/comerciales, seguimiento de amortización y monitoreo del estado de pago (A, B, C, D). | Concesión y liquidación de crédito | `loans` | **Alta (Crítica)** |
| **2. Ejecución Transaccional Monetaria** | Movimientos operativos de fondos en cuentas corrientes (depósitos, retiros por ventanilla, transferencias entre cuentas). | Débito o crédito asentado en cuenta | `trans` | **Alta (Crítica)** |
| **3. Procesamiento de Órdenes Recurrentes** | Ejecución de pagos programados recurrentes de servicios, cuotas de préstamos bancarios, leasing y seguros. | Emisión / Débito de orden permanente | `orders` | **Media-Alta** |
| **4. Administración de Cuentas Pasivas** | Apertura de cuentas de depósito y vinculación de clientes titulares y cotitulares. | Apertura de cuenta bancaria | `accounts`, `clients`, `disps` | **Media** |

> [!NOTE]
> **Delimitación de Alcance de Tarjetas:**  
> La tabla `cards` (892 tarjetas de crédito/débito emitidas: 659 *classic*, 145 *junior*, 88 *gold*) no se incluye en la primera iteración de tablas de hechos para enfocar los recursos de cómputo y modelado en la problemática urgente de morosidad y liquidez. Se incorporará en una fase posterior como una dimensión complementaria asociada a las cuentas.

---

#### Datos requeridos para el análisis

| Categoría | Dato requerido | Campo o atributo origen | Unidad / Formato | Periodicidad | Observaciones metodológicas |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Colocación** | Monto otorgado | `loans.amount` | Monetario (\$) | Por préstamo | Medida aditiva base para el total colocado y ticket promedio. |
| **Colocación** | Plazo del crédito | `loans.duration` | Meses (Entero) | Por préstamo | Duraciones estándar: 12, 24, 36, 48 y 60 meses. |
| **Colocación** | Cuota de pago mensual | `loans.payments` | Monetario (\$) | Por préstamo | Permite proyectar el flujo de amortización mensual. |
| **Cartera** | Estado del préstamo | `loans.status` | Categórico (A, B, C, D) | Por préstamo | Clasifica la cartera en vigente (C, D) y cerrada (A, B). |
| **Cartera** | Fecha de otorgamiento | `loans.date` | Fecha (`YYYY-MM-DD`) | Por préstamo | Se descompone en año, trimestre, mes y día para `Dim_Tiempo`. |
| **Clientes** | Demografía del cliente | `clients.birth_number` | Numérico / Derivado | Por cliente | Codifica fecha de nacimiento y sexo (+50 en mes para mujeres). |
| **Clientes** | Edad al corte analítico | Calculado (`31/12/1998`) | Años (Entero) | Por cliente | Calculada estrictamente respecto al cierre del dataset (1998). |
| **Clientes** | Rol de titularidad | `disps.type` | Categórico (`OWNER`/`DISPONENT`) | Por vinculación | Permite aislar al titular único (`OWNER`) para evitar *fan-out*. |
| **Clientes** | Antecedente de pago | `tkeys.goodClient` | Binario (`0` / `1`) | Por cliente evaluado | Corregido semánticamente: 1 = Mora/Default, 0 = Cumplido. |
| **Finanzas** | Saldo de cuenta corriente | `trans.balance` | Monetario (\$) | Por transacción | **Medida semiaditiva.** El saldo institucional se obtiene del último saldo registrado por cuenta a una fecha dada. |
| **Operaciones** | Tipo y canal transaccional | `trans.type`, `trans.operation` | Categórico | Por transacción | Se homologan términos del checo al español. |
| **Operaciones** | Monto transaccionado | `trans.amount` | Monetario (\$) | Por transacción | Medida aditiva base para el volumen operativo. |
| **Órdenes** | Monto orden permanente | `orders.amount` | Monetario (`DECIMAL(12,2)`) | Por orden | Preservar precisión decimal para evitar discrepancia de -\$47.40. |
| **Órdenes** | Propósito del pago | `orders.k_symbol` | Categórico | Por orden | Homologado al español (`SIPO`, `UVER`, `POJISTNE`, `LEASING`). |
| **Geografía** | Indicadores del distrito | `districts.A2` a `A16` | Categórico / Numérico | Por distrito | Nombre, región, población, salario, desempleo y crimen. |

---

#### Fuentes de información

| Fuente | Tipo | Responsable | Acceso | Calidad percibida | Notas técnicas |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Base de datos operativa** | MySQL / MariaDB Relacional (`Financial_ijs` en 3FN) | Servidor `relational.fel.cvut.cz`, puerto 3306 | Remoto público con credenciales `guest` | Alta para benchmark académico | 9 tablas relacionales: `accounts`, `clients`, `disps`, `loans`, `orders`, `trans`, `cards`, `districts`, `tkeys`. |
| **Dataset Benchmark CTU** | Repositorio PKDD / ECML 1999 (Praga) | Czech Technical University (CTU) | Acceso académico abierto | Estándar internacional | Dataset de referencia en minería de datos e Inteligencia de Negocios. |

---

#### Métricas e indicadores preliminares

| Categoría | Indicador / KPI | Fórmula matemática o definición | Nivel de análisis | Tipo de medida |
| :--- | :--- | :--- | :--- | :--- |
| **Colocación** | Monto Total Colocado | $\sum(\text{loans.amount})$ | Año / Distrito / Plazo | Aditiva |
| **Colocación** | Ticket Promedio de Préstamo | $\text{AVG}(\text{loans.amount})$ | Año / Distrito | No aditiva (Calculada) |
| **Cartera** | Tasa de Morosidad Activa (Vigente) | $\frac{\text{COUNT}(\text{status} = 'D')}{\text{COUNT}(\text{status IN ('C','D')})} \times 100$ | Año / Distrito | Razón calculada (10.04%) |
| **Cartera** | Tasa de Morosidad Histórica (Total) | $\frac{\text{COUNT}(\text{status} = 'D')}{\text{COUNT}(\text{loans.id})} \times 100$ | Año / Distrito | Razón calculada (6.60%) |
| **Cartera** | Tasa de Incumplimiento Histórico | $\frac{\text{COUNT}(\text{status} = 'B')}{\text{COUNT}(\text{status IN ('A','B')})} \times 100$ | Año / Distrito | Razón calculada (13.25%) |
| **Finanzas** | Saldo Total de Depósitos Institucionales | $\sum (\text{Último } \texttt{trans.balance} \text{ por cuenta})$ | Fecha de corte / Distrito | **Semiaditiva** |
| **Finanzas** | Ratio de Absorción Crediticia | $\frac{\sum(\text{loans.amount})}{\text{Saldo Total Depósitos al Corte}}$ | Corte institucional | Razón calculada (52.38%) |
| **Operaciones** | Flujo Total Transaccional | $\sum(\text{trans.amount})$ | Tiempo / Tipo Operación | Aditiva |
| **Operaciones** | Ticket Promedio por Transacción | $\text{AVG}(\text{trans.amount})$ | Tiempo / Canal | No aditiva (Calculada) |
| **Órdenes** | Compromiso de Débitos Automáticos | $\sum(\text{orders.amount})$ | Símbolo / Distrito | Aditiva |

---

#### Definición de hechos y dimensiones (Modelo Dimensional Kimball)

| Elemento | Nombre propuesto | Grano / Descripción | Jerarquías | Claves | Tipo / Tratamiento SCD |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Hecho** | `Fact_Prestamos` | **Grano:** Una fila por cada préstamo otorgado (682 filas). Registra métricas financieras y claves a las dimensiones de contexto. | Tiempo, Distrito, Cuenta, Cliente, Estado | `sk_prestamo` (PK), `sk_tiempo`, `sk_cuenta`, `sk_cliente`, `sk_distrito`, `sk_estado_prestamo` | Hecho transaccional de evento |
| **Hecho** | `Fact_Transacciones` | **Grano:** Una fila por cada movimiento operativo en cuenta (1,056,320 filas). Registra monto operado y saldo resultante. | Tiempo, Operación, Cuenta, Cliente, Distrito | `sk_transaccion` (PK), `sk_tiempo`, `sk_cuenta`, `sk_cliente`, `sk_distrito`, `sk_operacion` | Hecho transaccional |
| **Hecho** | `Fact_Ordenes` | **Grano:** Una fila por cada orden de débito permanente registrada (6,471 filas). Preserva precisión con `DECIMAL(12,2)`. | Cuenta, Cliente, Distrito, Propósito Orden | `sk_orden` (PK), `sk_tiempo`, `sk_cuenta`, `sk_cliente`, `sk_distrito`, `sk_orden_tipo` | Hecho transaccional |
| **Dimensión** | `Dim_Tiempo` | Calendario diario continuo (1993-01-01 a 1998-12-31, 2,191 días exactos). | Año > Semestre > Trimestre > Mes > Día | `sk_tiempo` (PK), `fecha`, `anio`, `mes`, `nombre_mes`, `dia` | Conformada |
| **Dimensión** | `Dim_Cliente` | Perfil demográfico completo de los 5,369 clientes. Contiene atributos derivados de edad y género. | Región > Distrito > Cliente | `sk_cliente` (PK), `id_cliente_bk`, `sexo`, `fecha_nacimiento`, `edad_corte`, `tipo_disposicion`, `etiqueta_buen_pagador` | Conformada (SCD 1) |
| **Dimensión** | `Dim_Cuenta` | Catálogo de las 4,500 cuentas corrientes y su frecuencia de emisión de extracto. | Frecuencia > Cuenta | `sk_cuenta` (PK), `id_cuenta_bk`, `frecuencia_emision_estado`, `fecha_apertura` | Conformada (SCD 1) |
| **Dimensión** | `Dim_Distrito` | Los 77 distritos geográficos con indicadores socioeconómicos (salario, desempleo, criminalidad). | Región > Distrito | `sk_distrito` (PK), `id_distrito_bk`, `nombre_distrito`, `region`, `salario_promedio`, `tasa_desempleo`, `tasa_crimen` | Conformada (SCD 0) |
| **Dimensión** | `Dim_Estado_Prestamo` | Dimensión de catálogo (Outrigger) de 4 filas fijas: A, B, C, D. | Condición (Vigente/Cerrado) > Estado | `sk_estado_prestamo` (PK), `codigo_estado`, `condicion`, `descripcion` | **SCD Tipo 0 (Fijo / Catálogo)** |
| **Dimensión** | `Dim_Operacion` | Tipología y canal de las transacciones homologadas al español. | Canal > Tipo Operación | `sk_operacion` (PK), `tipo_operacion_original`, `tipo_operacion_traducido`, `canal` | SCD Tipo 0 |
| **Dimensión** | `Dim_Orden` | Clasificación del propósito de las órdenes permanentes homologadas al español. | Categoría > Símbolo | `sk_orden_tipo` (PK), `k_symbol_original`, `categoria_orden_traducida` | SCD Tipo 0 |

---

#### Resolución de la Relación Multivaluada Cuenta–Cliente

En el dominio del banco `Financial_ijs`, la relación entre cuentas y clientes no es estrictamente 1:1. La auditoría SQL directa a la tabla asociativa `disps` reveló:

| Tipo de Relación | Total Cuentas / Clientes | Porcentaje |
| :--- | :--- | :--- |
| **Cuentas individuales (único titular `OWNER`)** | 3,631 cuentas | 80.7% |
| **Cuentas mancomunadas (`OWNER` + cotitular `DISPONENT`)** | 869 cuentas (1,738 clientes) | 19.3% |
| **Total Cuentas** | **4,500 cuentas** | 100.0% |
| **Total Clientes** | **5,369 clientes** | 100.0% |

> [!IMPORTANT]
> **Decisión de Diseño Dimensional Adoptada:**  
> 1. Para evitar el problema clásico de *fan-out* (duplicación artificial de filas y montos en `Fact_Prestamos`, `Fact_Transacciones` y `Fact_Ordenes`), en el pipeline ETL las tablas de hechos se unen con `Dim_Cliente` **exclusivamente a través del cliente titular (`disps.type = 'OWNER'`)**.
> 2. `Dim_Cliente` almacena a la totalidad de los **5,369 clientes**, preservando el atributo `tipo_disposicion` para no perder la información demográfica de los cotitulares.
> 3. Esta decisión garantiza que las sumas de hechos coincidan al centavo con el sistema origen sin inflar métricas, dejando abierta la incorporación de una *Bridge Table* (*Cuenta-Cliente*) si en el futuro se requiriera analizar específicamente a los cotitulares `DISPONENT`.

---

#### Estrategia de Slowly Changing Dimensions (SCD)

| Dimensión | Estrategia SCD | Justificación Metodológica |
| :--- | :--- | :--- |
| `Dim_Estado_Prestamo` | **SCD Tipo 0 (Fijo)** | **Corrección conceptual:** Los estados A, B, C y D representan definiciones de dominio que no cambian en el tiempo. 'A' siempre significará *Pagado sin problemas*. Quien cambia de estado a través del tiempo es el crédito individual en los hechos, no la dimensión. |
| `Dim_Distrito` | **SCD Tipo 0 (Fijo)** | Los indicadores demográficos (A4 a A16) reflejan el censo y contexto socioeconómico estático provisto por el benchmark para el periodo analizado. |
| `Dim_Cliente` | **SCD Tipo 1 (Sobrescritura)** | Los atributos de cliente (género, fecha de nacimiento, residencia) son inmutables o se actualizan sobre el registro actual por simplicidad analítica. |
| `Dim_Cuenta` | **SCD Tipo 1 (Sobrescritura)** | La frecuencia de extracto (`frequency`) no presenta variaciones temporales en el histórico. |
| `Dim_Operacion` / `Dim_Orden` | **SCD Tipo 0 (Fijo)** | Catálogos fijos de homologación de términos de negocio checo-español. |

---

#### Corrección Relacional y Semántica: Tabla `tkeys`

* **Desajuste Conceptual Previo:**  
  Versiones preliminares asumían una clave foránea inexistente `tkeys.client_id -> clients.id` y consideraban a ciegas que `tkeys.goodClient = 1` denotaba literalmente "buen pagador".
* **Realidad Estructural de `Financial_ijs`:**  
  La clave foránea reside en la tabla de clientes: `clients.tkey_id -> tkeys.id`. La tabla `tkeys` contiene exactamente 234 filas correspondientes a los 234 créditos concluidos (203 de Estado A y 31 de Estado B).
* **Corrección Semántica Crítica:**  
  En el benchmark original de minería de datos (PKDD 1999), `goodClient` fue definida como la variable target donde la **clase positiva / minoritaria (`1`) representa el evento de morosidad/quiebra (Estado B, 31 créditos)**, mientras que **`0` representa el cumplimiento normal (Estado A, 203 créditos)**.  
  *Transformación ETL aplicada:* Para que la etiqueta en el Data Mart tenga coherencia en los reportes de negocio:
  $$\texttt{etiqueta\_buen\_pagador} = \begin{cases} 
  1 \text{ (Verdadero)}, & \text{si préstamo finalizó en Estado 'A'} \\
  0 \text{ (Falso)}, & \text{si préstamo finalizó en Estado 'B'} \\
  \text{NULL}, & \text{si el crédito sigue activo ('C','D') o no tiene préstamo}
  \end{cases}$$

---

#### Calidad y Preparación de Datos

| Criterio | Estado actual en `Financial_ijs` | Riesgo detectado | Acción de Limpieza y Transformación |
| :--- | :--- | :--- | :--- |
| **Datos Incompletos** | El distrito 69 (*Jesenik*) contiene `'?'` en las columnas de desempleo y crimen de 1995 (`A12` y `A15`). | Fallo de conversión a tipos numéricos en SQL Server. | Convertir `'?'` a `NULL` explícito en la extracción hacia staging; imputar con el promedio regional si se requiere en tableros de BI. |
| **Valores Decimales** | `orders.amount` contiene valores con un decimal (ej. \$3,372.70). | Pérdida de precisión al castear a enteros, provocando un desbalance de -\$47.40 en 499 registros. | Definir `monto_orden` con tipo de dato `DECIMAL(12,2)` tanto en Staging como en `Fact_Ordenes` para mantener exactitud al centavo. |
| **Codificación Lingüística** | Columnas `operation`, `type` y `k_symbol` almacenan valores en idioma checo (`PRIJEM`, `VYBER`, `SIPO`, etc.). | Reportes gerenciales ilegibles para la toma de decisiones en español. | Implementar tabla de homologación en el pipeline ETL para poblar atributos descriptivos traducidos. |
| **Formato de Fechas** | Fechas almacenadas como enteros compactos en formato `YYMMDD`. | Interpretaciones erróneas de siglo o fallas al unir con el calendario. | Transformar mediante SSIS a formato estándar `DATE` (`YYYY-MM-DD`). |
| **Atributo `birth_number`** | Codifica fecha de nacimiento y género sumando 50 al mes en mujeres (`AAMMDD`). | Violación de PII y complejidad de cálculo para usuarios finales. | Descomponer en columnas analíticas directas: `fecha_nacimiento` y `sexo` ('M' / 'F'). Calcular `edad_corte` referenciada al **31/12/1998**. |

---

#### Matriz de Homologación Lingüística (Checo $\to$ Español)

##### Tabla de Operaciones (`Dim_Operacion`)
| Valor Original (`operation`) | Tipo Original (`type`) | Tipo Operación Traducido | Canal / Medio |
| :--- | :--- | :--- | :--- |
| `VKLAD` | `PRIJEM` | **Depósito en Efectivo** | Ventanilla Bancaria |
| `PREVOD Z UCTU` | `PRIJEM` | **Transferencia Entrante** | Compensación Interbancaria |
| `VYBER` | `VYDAJ` | **Retiro en Efectivo** | Ventanilla Bancaria |
| `PREVOD NA UCET` | `VYDAJ` | **Transferencia Saliente** | Compensación Interbancaria |
| `VYBER KARTOU` | `VYBER` | **Retiro con Tarjeta** | Cajero Automático (ATM) |

##### Tabla de Propósito de Órdenes (`Dim_Orden`)
| Código Original (`k_symbol`) | Categoría Traducida | Descripción de Negocio |
| :--- | :--- | :--- |
| `SIPO` | **Servicios del Hogar** | Pago programado recurrente de servicios básicos (luz, agua, teléfono) |
| `UVER` | **Cuota de Préstamo** | Amortización mensual programada de crédito bancario |
| `POJISTNE` | **Pago de Seguros** | Prima mensual de póliza de seguro |
| `LEASING` | **Arrendamiento / Leasing** | Pago programado de cuota de leasing |
| ` ` (Espacio / Vacío) | **Sin Especificar** | Orden permanente sin código de concepto declarado |

---

#### Comparativa Arquitectónica: Justificación de Ralph Kimball vs. Bill Inmon

| Criterio | Metodología Ralph Kimball (Adoptada) | Metodología Bill Inmon | Justificación de Elección para el Proyecto |
| :--- | :--- | :--- | :--- |
| **Filosofía de Arquitectura** | **Bottom-Up:** Construcción incremental de Data Marts por proceso de negocio unidos mediante dimensiones conformadas (*Bus Matrix*). | **Top-Down:** Construcción previa de un Enterprise Data Warehouse (EDW) corporativo centralizado y normalizado en 3FN. | **Se adopta Kimball:** Permite entregar valor inmediato al usuario final en ciclos cortos, modelando directamente el proceso urgente de riesgo y morosidad sin esperar a integrar toda la institución. |
| **Modelo Físico** | **Desnormalizado (Estrella / Constelación):** Tablas de hechos rodeadas por dimensiones directas. | **Normalizado (Tercera Forma Normal - 3FN):** Decenas de entidades altamente normalizadas. | **Ventaja de Kimball:** Las consultas analíticas en Power BI / DAX son directas, con un solo nivel de `JOIN`, optimizando drásticamente la velocidad de respuesta frente a modelos normalizados. |
| **Realidad de la Fuente** | Transforma la fuente en 3FN directamente hacia esquemas dimensionales analíticos. | Exige construir un EDW en 3FN a partir de una fuente que **ya está en 3FN** (`Financial_ijs`). | **Inconsistencia de Inmon en este caso:** Aplicar Inmon implicaría normalizar lo que ya está normalizado, duplicando esfuerzos de almacenamiento y pipelines ETL sin aportar valor real. |
| **Estado en el Plan** | **Físicamente Implementado:** Paquetes SSIS construidos y base `DM_Financial_Kimball` operativa en SQL Server. | **Pendiente / Teórico:** Marcado como fase futura de investigación comparativa. | La arquitectura de Kimball es la única que cumple los criterios de factibilidad técnica y cumplimiento de plazos académicos. |

---

#### Plan de Validación de Datos y Calidad

1. **Reconciliación de Conteos:**
   * 682 filas en `loans` deben coincidir exactamente con `Fact_Prestamos`.
   * 6,471 filas en `orders` deben coincidir con `Fact_Ordenes`.
   * 1,056,320 filas en `trans` deben coincidir con `Fact_Transacciones`.
   * 5,369 clientes en `Dim_Cliente` (4,500 titulares y 869 autorizados).
2. **Reconciliación de Métricas Financieras (Totales de Control):**
   * $\sum(\text{loans.amount}) = \mathbf{\$103,261,740.00}$ (Diferencia: \$0.00).
   * $\sum(\text{trans.amount}) = \mathbf{\$6,257,862,197.00}$ (Diferencia: \$0.00).
   * $\sum(\text{orders.amount}) = \mathbf{\$21,228,993.60}$ (Diferencia corregida: \$0.00 mediante `DECIMAL(12,2)`).
3. **Integridad Referencial Estricta:**
   * Cero claves huérfanas en las tablas de hechos (`sk_tiempo`, `sk_cuenta`, `sk_cliente`, `sk_distrito`, `sk_estado_prestamo`, `sk_operacion`, `sk_orden_tipo`).
4. **Validación de Medida Semiaditiva:**
   * El saldo institucional de depósitos se calcula agrupando por cuenta y obteniendo el balance de la transacción más reciente al 31/12/1998, reconciliando los **\$197,140,434.00**.

---

### 2.8 Habilidades blandas empleadas en la práctica
* [ ] Liderazgo
* [ ] Trabajo en equipo
* [ ] Comunicación asertiva
* [ ] La empatía
* [x] Pensamiento crítico
* [ ] Flexibilidad
* [ ] La resolución de conflictos
* [ ] Adaptabilidad
* [x] Responsabilidad

---

### 2.9 Conclusiones

1. **La Carta de Diseño constituye el cimiento metodológico indispensable para el éxito de una solución de BI:** Permitió desacoplar los requerimientos de negocio de la complejidad del motor transaccional, identificando oportunamente que la morosidad bancaria activa del 10.04% y el incremento del 1,050% en los créditos en estado D entre 1994 y 1997 exigían un modelado dimensional centrado en procesos y no un simple reporte relacional.
2. **La metodología de Ralph Kimball demostró ser superior técnica y operativamente frente a Bill Inmon para este proyecto:** Dado que la fuente `Financial_ijs` ya se encuentra en 3FN, construir un EDW normalizado (Inmon) representaba una redundancia innecesaria. El enfoque dimensional en constelación (*Galaxy Schema*) permitió desacoplar préstamos, transacciones y órdenes en Data Marts independientes pero integrados por dimensiones conformadas, optimizando el rendimiento analítico para Power BI.
3. **La clasificación precisa de los tipos de SCD y la naturaleza de las medidas evita errores de arquitectura:** Se demostró que aplicar SCD Tipo 2 a una dimensión catálogo como `Dim_Estado_Prestamo` es un error metodológico (es SCD Tipo 0), y que el saldo bancario (`trans.balance`) es una medida semiaditiva que jamás debe sumarse a lo largo del tiempo sin una fecha de corte definida.
4. **La calidad de datos y la corrección semántica en el staging salvan la validez del análisis gerencial:** El descubrimiento de que la variable `goodClient` en el dataset de benchmark codificaba a los préstamos fallidos como `1` evitó invertir los reportes de riesgo, asegurando que la gerencia no considere erróneamente a los deudores morosos como buenos pagadores.

---

### 2.10 Recomendaciones

1. **Mantener la precisión decimal (`DECIMAL(12,2)`) en todas las capas del pipeline ETL:** Evitar conversiones implícitas a enteros en `Fact_Ordenes` para garantizar que no existan descalces monetarios entre el OLTP y el Data Warehouse.
2. **Ejecutar el cálculo de edad con fecha de corte cerrada (31/12/1998):** Asegurar que las rutinas SQL o de SSIS calculen la edad de los clientes respecto al fin del dataset y no con la función `GETDATE()`, para preservar la validez del análisis demográfico de los años 90.
3. **Incorporar la dimensión de tarjetas plásticas (`Dim_Tarjeta`) en una siguiente iteración:** Utilizar la relación `cards.disp_id -> disps.id` para habilitar el análisis de penetración de productos pasivos y medios de pago electrónicos sobre las cuentas activas.
4. **Automatizar las consultas de reconciliación en una tabla de auditoría de cargas:** Registrar fecha, filas insertadas, sumas de control y estado de ejecución en cada corrida del paquete SSIS para asegurar la gobernanza continua del Data Warehouse.

---

### 2.11 Referencias bibliográficas

* [1] R. Kimball and M. Ross, *The Data Warehouse Toolkit: The Definitive Guide to Dimensional Modeling*, 3rd ed. Indianapolis, IN, USA: Wiley, 2013.
* [2] W. H. Inmon, *Building the Data Warehouse*, 4th ed. Indianapolis, IN, USA: Wiley, 2005.
* [3] P. Berka, "Guide to the financial data set," in *PKDD'99 / PKDD 2000 Discovery Challenge Workshop Notes*, Prague, Czech Republic, 2000.
* [4] C. Ballard et al., *Dimensional Modeling: In a Business Intelligence Environment*, IBM Redbooks, 2006.
* [5] Asamblea Nacional del Ecuador, *Ley Orgánica de Protección de Datos Personales*, Registro Oficial Suplemento N.° 459, 26 de mayo de 2021.
