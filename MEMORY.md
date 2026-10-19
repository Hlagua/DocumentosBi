# 🧠 MEMORY BANK — PROYECTO BI: Financial_ijs
> **Archivo de Memoria Persistente para IAs / Chats de Desarrollo**  
> *Inspirado en el estándar de memoria persistente de Gentle AI / Roo-Code / Cursor.*  
> **Última sincronización:** 18 de Octubre de 2026 | **Rama:** `main` | **Último Commit:** `ec4bc43`  
> **Autores:** Alison Marcela Cobos Taco / Henry Daniel Lagua Flores  
> **Asignatura:** Inteligencia de Negocios — UTA | **Docente:** Ing. Ruben Nogales, Mg.

---

## 1. 📌 IDENTIDAD Y ESTADO GENERAL DEL PROYECTO

* **Caso de estudio:** Banco comercial checo (`Financial_ijs`), periodo analizado 1993–1998 con fecha de corte oficial **31/12/1998**.
* **Arquitectura:** Persistencia políglota integrada:
  1. **OLTP Remoto:** MySQL (`relational.fel.cvut.cz`).
  2. **Data Mart Dimensional:** Ralph Kimball en Microsoft SQL Server (`DM_Financial_Kimball_v2`).
  3. **NoSQL Documental:** MongoDB Local (`Financial`) con validadores `$jsonSchema`.
  4. **Business Intelligence:** Dos proyectos Power BI Desktop (`.pbip`) idénticos en interfaz, KPIs y 12 páginas.
* **Cifras de Control Inviolables (Globales sin filtros al 31/12/1998):**
  * Tasa de mora activa: **10.04%** (45 préstamos morosos activos C/D sobre 448 vigentes).
  * Incumplimiento histórico: **13.25%** (31 préstamos liquidados con deuda B sobre 234 cerrados).
  * Cartera vigente neta: **$80.30M** ($80,302,400.00).
  * Saldo total de depósitos en cuentas: **$197.14M** ($197,140,434.00 semiaditivo).
  * Ratio de Absorción de Cartera Vigente: **40.73%** ($80.30M / $197.14M) [Carta v8].
  * Cuentas en sobregiro: **39 cuentas**.
  * Cuentas totales: **4,500** | Clientes: **5,369** | Distritos: **77**.
  * Transacciones: **1,056,320** ($6,257,862,197.00).
  * Saldos mensuales acumulados (`Fact_Saldo_Cuenta_Mensual`): **185,615**.

---

## 2. 🔑 PARÁMETROS Y CREDENCIALES DE CONEXIÓN

Cualquier IA que interactúe con el entorno debe utilizar estos parámetros exactos:

| Servicio | Servidor / Host | Base de Datos / Catálogo | Usuario / Auth | Conector / Driver |
| :--- | :--- | :--- | :--- | :--- |
| **SQL Server Local** | `(localdb)\MSSQLLocalDB` | `DM_Financial_Kimball_v2` | Windows Auth (`Trusted_Connection=yes`) | `ODBC Driver 17 / 18 for SQL Server` |
| **MongoDB Local** | `localhost:27017` | `Financial` | Sin credenciales (local) | `pymongo.MongoClient("mongodb://localhost:27017/")` |
| **MySQL Remoto** | `relational.fel.cvut.cz:3306`| `Financial_ijs` | `guest` / `ctu-relational` | `pymysql` (charset `utf8mb4`) |
| **GitHub Repo** | `https://github.com/Hlagua/DocumentosBi.git` | Rama `main` | Usuario `Hlagua` (`hlagua6116@uta.edu.ec`) | Git Credential Manager (`manager`) |
| **Power BI Projects**| `dashboards/Dashboard_Financial_Kimball/` y `Dashboard_Financial_Mongo/` | Parámetros M: `ServidorSQL` y `BaseDatosSQL` | Modo Importación | `.pbip` (Power BI Desktop Agosto 2026+) |

---

## 3. ✅ LO REALIZADO Y VERIFICADO (COMMITS HASTA `ec4bc43`)

1. **Carta de Diseño v8 y Arquitecturas (`01`, `02`):**
   * Definición canónica de problemas de negocio, KPIs y resolución de la relación cuenta-cliente (`OWNER`).
   * Scripts DDL de Kimball (`DM_Financial_Kimball_v2`) y modelo comparativo Inmon en 3FN (`EDW_Financial_Inmon`).
2. **Cadena ETL reproducible y completitud (`09`, `10`, scripts `31`–`34`):**
   * Script `31_etl_oltp_a_kimball.py`: 23/23 pruebas pasadas, crea los 4 hechos y 8 dimensiones.
   * `33_completitud_datos.py` y `34_carga_completitud_kimball.py`: 0% de huecos o nulos residuales.
   * Imputación K-Means oficial del Distrito 69: Tasa de desempleo **5.83** y Tasa de criminalidad **1,326**.
3. **Persistencia NoSQL y Reconciliación Dual (`05`, scripts `35`, `36`):**
   * Migración Kimball ➔ MongoDB con validadores `$jsonSchema` estrictos.
   * Reconciliación cruzada por desgloses (33/33 pruebas) con delta exacto de **$0.00**. Respaldo en `Financial_mongo_dump.gz`.
4. **Sistemas de Recomendación v2 (`04`, scripts `37`–`41`):**
   * Catálogo real de 8 productos bancarios, sin fugas de información.
   * Modelos Colaborativo (Slope One, Item-Item Pearson), Demográfico y Basado en Contenido (TF-IDF / Coseno).
   * Generación de recomendaciones y matrices para los 4,500 titulares.
5. **Dashboards Articulados Power BI v5 (`07`, scripts `26`, `30`, `42`, `43`):**
   * Proyectos `.pbip` para Kimball y MongoDB con 12 páginas:
     * P0: Inicio (Renovado con banda azul y tarjetas ejecutivas).
     * P1: Demografía y Cartera.
     * P2: Transacciones y Descomposición.
     * P3: Crédito y Morosidad.
     * P4: Servicios y Órdenes.
     * P5: Tarjetas y Segmentación.
     * P6: Resumen Gerencial.
     * D1: Drill-Through Forense Distrito Karvina.
     * D2: Drill-Through Perfil 360 Cliente.
     * R1: Recomendación de Productos (Qué ofrecer).
     * R2: Capacidad y Límites de Préstamo Prudente.
     * R3: Venta Cruzada y Afinidad de Servicios.
   * Panel de filtros globales (Año, Zona, Segmento de Edad, Estado de Cuenta) sincronizados.
   * Vistas optimizadas en SQL Server: `vw_PBI_Saldo_Final_Cuenta` y `vw_PBI_Trans_Anual_Cuenta`.
6. **Guía de Uso e Interpretación (`06` v5):**
   * Explicación de cada visual, su justificación psicofísica (Cleveland, Few, Tufte) y su lectura para toma de decisiones.
7. **Guía de Sustentación de 15 Minutos (`11`):**
   * Reparto exacto de guion entre Henry y Alison, preparación 20 min antes, preguntas difíciles del tribunal y plan de contingencia.
8. **Automatizador Integral `REPARAR_TODO.py`:**
   * Script en la raíz que verifica dependencias, inicia motores, carga vistas, valida cifras de control y deja cualquier equipo listo para abrir los tableros.

---

## 4. ⏳ LO QUE SE ESTÁ HACIENDO / PENDIENTES INMEDIATOS

| Prioridad | Tarea Pendiente | Detalle / Archivos Involucrados |
| :---: | :--- | :--- |
| 🔴 **ALTA** | **Alinear Dossier 08 a Carta v8** | En [`08_Dossier_Auditoria_Externa_Dashboard.md`](file:///C:/Users/henry/.gemini/antigravity/scratch/DocumentosBi/08_Dossier_Auditoria_Externa_Dashboard.md) actualizar la tasa de absorción de 52.38% al valor canónico **40.73%**, y confirmar las cifras del Distrito 69 (5.83 y 1,326) para que cuadre al 100% con la Guía 07 v4. |
| 🟡 **MEDIA** | **Actualizar demo HTML interactivo** | En [`demo_dashboard.html`](file:///C:/Users/henry/.gemini/antigravity/scratch/DocumentosBi/demo_dashboard.html) sincronizar el KPI de absorción a 40.73% y verificar si se añaden las pestañas de recomendación R1–R3. |
| 🟡 **MEDIA** | **Regenerar Informe 04 en Word / PDF** | [`04_Informe_Sistemas_de_Recomendacion.md`](file:///C:/Users/henry/.gemini/antigravity/scratch/DocumentosBi/04_Informe_Sistemas_de_Recomendacion.md) ya tiene el contenido v2 completo, pero el `.docx` y `.pdf` en el repositorio corresponden a la v1 anterior. |
| 🟢 **BAJA** | **Actualizar tabla de estados en README.md** | Pasar las etapas 9b y 10 a estado ✅ en [`README.md`](file:///C:/Users/henry/.gemini/antigravity/scratch/DocumentosBi/README.md). |

---

## 5. 🎯 ASIGNACIÓN DE TAREAS ESPECÍFICAS PARA LOS CHATS / IAs

Para trabajar en paralelo o transferir trabajo entre agentes sin pisarse, se establece la siguiente división:

### 🤖 Chat / IA 1 (Este Agente — Entorno Local y Blindaje Técnico):
1. **Comprobar entorno local con `REPARAR_TODO.py`:** Asegurar que la máquina de Henry pase las 23/23 pruebas de Kimball y las cifras de control de Power BI.
2. **Auditar y blindar el Dossier 08:** Editar [`08_Dossier_Auditoria_Externa_Dashboard.md`](file:///C:/Users/henry/.gemini/antigravity/scratch/DocumentosBi/08_Dossier_Auditoria_Externa_Dashboard.md) para unificar las métricas a Carta v8 (40.73% absorción, 5.83/1326 distrito 69, 4 hechos).
3. **Actualizar el README.md:** Reflejar el estado completado de todas las etapas.

### 🤖 Chat / IA 2 (Otro Chat — Entregables Documentales y Sustentación):
1. **Compilar/Exportar el Informe 04 v2:** Generar a partir de `04_Informe_Sistemas_de_Recomendacion.md` los entregables finales formateados (`.docx` y `.pdf`) usando los scripts `build_final_04_word.py` y `helpers_informe_4.py`.
2. **Actualizar `demo_dashboard.html`:** Incorporar el nuevo diseño con banda azul y tarjetas ejecutivas, y actualizar el KPI a 40.73%.
3. **Simulador de Sustentación (Guía 11):** Entrenar con el usuario las respuestas a las preguntas del tribunal evaluador (Sección 3 de la Guía 11).

---

## 6. 🛡️ REGLAS OPERATIVAS OBLIGATORIAS PARA CUALQUIER IA
* **NO actualizar a TMDL:** Si Power BI Desktop muestra el mensaje emergente de migración a TMDL, seleccionar **"No actualizar"**. Los proyectos deben permanecer en formato PBIP canónico (`model.bim` en JSON UTF-8 sin BOM).
* **Mantener la Reconciliación $0.00:** Ningún cambio en medidas o consultas M debe alterar los controles monetarios ($197.14M depósitos, $80.30M cartera vigente).
* **Ejecutar `git pull` antes de cualquier sesión:** Confirmar que no hay desincronización con los commits remotos de Alison (`Itsuna18`).
