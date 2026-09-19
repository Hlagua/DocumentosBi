# Repositorio de Documentación de Inteligencia de Negocios
## Caso de Estudio: Banco Comercial Checo (`Financial_ijs`)

**Universidad Técnica de Ambato**  
**Facultad de Ingeniería en Sistemas, Electrónica e Industrial**  
**Carrera de Software — Ciclo Académico: Agosto 2026 – Diciembre 2026**  
**Asignatura:** Inteligencia de Negocios  
**Docente:** Ing. Ruben Nogales, Mg.  
**Integrantes:** Alison Marcela Cobos Taco / Henry Daniel Lagua Flores  

---

### 📂 Contenido del Repositorio

Este repositorio contiene la documentación metodológica oficial, el modelado de arquitecturas de almacenamiento de datos corporativos (DW/BI), los scripts DDL y los DataFrames analíticos para el caso de estudio `Financial_ijs`:

#### 1. Documentación Metodológica y Guías Prácticas
* 📄 **[01. Carta de Diseño Oficial (v6 Definitiva)](01_Carta_de_Diseno_Financial_ijs.md)**  
  *Levantamiento formal de requisitos analíticos, diagnóstico de negocio (morosidad activa del 10.04%, ratio de absorción de depósitos del 52.38%), especificación de métricas, resolución de la relación cuenta-cliente (`OWNER`), estrategias de Slowly Changing Dimensions (SCD), calidad de datos en staging y plan de validación.*
* 📄 **[02. Análisis y Modelado de Arquitecturas: Ralph Kimball vs. Bill Inmon](02_Analisis_Arquitecturas_Kimball_Inmon.md)**  
  *Diseño comparativo entre el enfoque Bottom-Up (Data Mart Bus Architecture con esquema en constelación) y el enfoque Top-Down (Corporate Information Factory con EDW en 3FN y data marts derivados), Matriz de Bus Corporativa, Source-to-Target Mapping y evaluación técnica de rendimiento.*
* 📄 **[03. Informe de Guía Práctica: Limpieza y Transformación de Datos](03_Informe_Limpieza_y_Transformacion_de_Datos.md)**  
  *Guía práctica oficial de completitud de datos (enfoque híbrido OpenRefine + Python/Pandas/NumPy vectorizado), imputación causal vs. K-Means en distritos, resolución de contrapares bancarias, enriquecimiento semántico y validación de 0% nulos.*
* 📄 **[04. Informe de Guía Práctica: Sistemas de Recomendación](04_Informe_Sistemas_de_Recomendacion.md)**  
  *Guía práctica oficial de Sistemas de Recomendación bancarios estructurados bajo los paradigmas Demográfico (K-Means), Colaborativo (Slope One, Correlación de Pearson y Similitud de Coseno) y Basado en Contenido (Item-to-Item de Amazon con Frecuencia Inversa ITF), con formato CERO CÓDIGO sustentado en evidencias visuales y métricas formales.*

#### 2. Scripts DDL de Implementación Física (SQL Server)
* 💾 **[`sql/01_DDL_Kimball_DM_Financial.sql`](sql/01_DDL_Kimball_DM_Financial.sql)**  
  *Script DDL completo para la arquitectura dimensional de Ralph Kimball (`DM_Financial_Kimball_v2`). Define las 4 dimensiones conformadas (`Tiempo`, `Cuenta`, `Cliente`, `Distrito`), los catálogos específicos (`Estado_Prestamo`, `Operacion`, `Orden`) y las tablas de hechos atómicas (`Fact_Prestamos`, `Fact_Transacciones`, `Fact_Ordenes`) con tipos monetarios exactos `DECIMAL(12,2)`.*
* 💾 **[`sql/02_DDL_Inmon_EDW_Financial.sql`](sql/02_DDL_Inmon_EDW_Financial.sql)**  
  *Script DDL documental para la arquitectura corporativa de Bill Inmon (`EDW_Financial_Inmon`). Modela el repositorio central en Tercera Forma Normal (3FN) organizado por áreas temáticas y las vistas analíticas departamentales derivadas.*

#### 3. Pipelines de Carga, Calidad y Recomendación (Python)
* ⚙️ **[`scripts/etl_populate_kimball_v2.py`](scripts/etl_populate_kimball_v2.py):** Pipeline ETL para extraer datos desde MySQL (`Financial_ijs`), aplicar reglas de staging y poblar el modelo dimensional en SQL Server.
* ⚙️ **[`scripts/generar_4_dataframes.py`](scripts/generar_4_dataframes.py):** Script para extraer y exportar los 4 DataFrames analíticos a partir de la base dimensional.
* ⚙️ **[`scripts/completar_transacciones.py`](scripts/completar_transacciones.py):** Pipeline vectorizado de completitud e imputación multicriterio sobre 1,056,320 transacciones (<24 s).
* ⚙️ **[`scripts/clustering.py`](scripts/clustering.py) / [`scripts/imputar_final.py`](scripts/imputar_final.py):** Algoritmos de correlación, codo/silueta K-Means e imputación para `df_cliente_consolidado`.
* ⚙️ **[`scripts/sistemas_recomendacion.py`](scripts/sistemas_recomendacion.py):** Pipeline analítico de recomendación que ejecuta los modelos Demográfico, Colaborativo (Slope One, Pearson, Coseno) e Item-to-Item con ITF, exportando las evidencias gráficas en alta definición.

#### 4. DataFrames Analíticos Originales y Limpios (`dataframes/`)
* 📊 **[`dataframes/df_prestamos.csv`](dataframes/df_prestamos.csv):** 682 filas $\times$ 24 columnas (Cartera de créditos, 100% completo).
* 📊 **[`dataframes/df_ordenes.csv`](dataframes/df_ordenes.csv) / [`df_ordenes_clean.csv`](dataframes/df_ordenes_clean.csv):** 6,471 filas (Débitos recurrentes, normalizado con OpenRefine a `SIN_ESPECIFICAR`).
* 📊 **[`dataframes/df_cliente_consolidado.csv`](dataframes/df_cliente_consolidado.csv) / [`df_cliente_consolidado_clean.csv`](dataframes/df_cliente_consolidado_clean.csv):** 5,369 filas $\times$ 29 columnas (Matriz Cliente 360 con imputación histórica en distrito 69 y banderas booleanas).
* 📊 **[`dataframes/df_transacciones.csv.gz`](dataframes/df_transacciones.csv.gz) / [`df_transacciones_completado.csv.gz`](dataframes/df_transacciones_completado.csv.gz):** 1,056,320 filas $\times$ 21 columnas (Transacciones completadas al 100% sin nulos y con semántica financiera traducida).

---

### 🐍 Cómo Cargar los DataFrames en Python

```python
import pandas as pd

# 1. Cargar Préstamos
df_prestamos = pd.read_csv('dataframes/df_prestamos.csv')

# 2. Cargar Órdenes
df_ordenes = pd.read_csv('dataframes/df_ordenes.csv')

# 3. Cargar Cliente Consolidado (360)
df_cliente = pd.read_csv('dataframes/df_cliente_consolidado.csv')

# 4. Cargar Transacciones (Pandas descomprime el .csv.gz automáticamente en memoria)
df_trans = pd.read_csv('dataframes/df_transacciones.csv.gz')
print(f"Transacciones cargadas: {df_trans.shape[0]:,} filas x {df_trans.shape[1]} columnas")
```

---

### 🏛️ Diagrama de Arquitecturas Analíticas

```mermaid
flowchart LR
    subgraph Origen["Fuente Operativa"]
        OLTP["Financial_ijs (3FN)<br>9 Tablas Relacionales"]
    end

    subgraph Kimball["Ruta Ralph Kimball (Bottom-Up)"]
        ETL_K["ETL Python / SSIS"]
        DM_K["Constelación Dimensional<br>• Fact_Prestamos (682)<br>• Fact_Transacciones (1.05M)<br>• Fact_Ordenes (6,471)<br>• 4 Dimensiones Conformadas"]
    end

    subgraph Inmon["Ruta Bill Inmon (Top-Down)"]
        ETL_I["ETL Integración"]
        EDW["EDW Corporativo 3FN<br>• Sujetos / Clientes<br>• Contratos / Cuentas<br>• Crédito / Cartera<br>• Transaccionalidad"]
        DM_I["Vistas Departamentales<br>• Riesgo y Cartera<br>• Operaciones y Liquidez"]
    end

    subgraph BI["Capa de Consumo"]
        Dashboards["Power BI / DAX<br>Tableros de Decisión"]
        PythonDF["DataFrames (Pandas)<br>Minería de Datos / ML"]
    end

    OLTP --> ETL_K --> DM_K --> Dashboards
    DM_K --> PythonDF
    OLTP --> ETL_I --> EDW --> DM_I --> Dashboards
```
