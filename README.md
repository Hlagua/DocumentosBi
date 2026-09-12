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

Este repositorio contiene la documentación metodológica oficial, el modelado de arquitecturas de almacenamiento de datos corporativos (DW/BI), los scripts DDL y el pipeline de carga ETL automatizado para el caso de estudio `Financial_ijs`:

#### 1. Documentación Metodológica y Guías Prácticas
* 📄 **[01. Carta de Diseño Oficial (v6 Definitiva)](01_Carta_de_Diseno_Financial_ijs.md)**  
  *Levantamiento formal de requisitos analíticos, diagnóstico de negocio (morosidad activa del 10.04%, ratio de absorción de depósitos del 52.38%), especificación de métricas, resolución de la relación cuenta-cliente (`OWNER`), estrategias de Slowly Changing Dimensions (SCD), calidad de datos en staging y plan de validación.*
* 📄 **[02. Análisis y Modelado de Arquitecturas: Ralph Kimball vs. Bill Inmon](02_Analisis_Arquitecturas_Kimball_Inmon.md)**  
  *Diseño comparativo entre el enfoque Bottom-Up (Data Mart Bus Architecture con esquema en constelación) y el enfoque Top-Down (Corporate Information Factory con EDW en 3FN y data marts derivados), Matriz de Bus Corporativa, Source-to-Target Mapping y evaluación técnica de rendimiento.*

#### 2. Scripts DDL de Implementación Física (SQL Server)
* 💾 **[`sql/01_DDL_Kimball_DM_Financial.sql`](sql/01_DDL_Kimball_DM_Financial.sql)**  
  *Script DDL completo para la arquitectura dimensional de Ralph Kimball (`DM_Financial_Kimball_v2`). Define las 4 dimensiones conformadas (`Tiempo`, `Cuenta`, `Cliente`, `Distrito`), los catálogos específicos (`Estado_Prestamo`, `Operacion`, `Orden`) y las tablas de hechos atómicas (`Fact_Prestamos`, `Fact_Transacciones`, `Fact_Ordenes`) con tipos monetarios exactos `DECIMAL(12,2)`.*
* 💾 **[`sql/02_DDL_Inmon_EDW_Financial.sql`](sql/02_DDL_Inmon_EDW_Financial.sql)**  
  *Script DDL documental para la arquitectura corporativa de Bill Inmon (`EDW_Financial_Inmon`). Modela el repositorio central en Tercera Forma Normal (3FN) organizado por áreas temáticas y las vistas analíticas departamentales derivadas.*

#### 3. Pipeline ETL Automatizado (Python)
* ⚙️ **[`scripts/etl_populate_kimball_v2.py`](scripts/etl_populate_kimball_v2.py)**  
  *Script ETL optimizado para extraer los datos desde la base de datos remota MySQL (`Financial_ijs`), aplicar reglas de limpieza (distritos, edad de corte, etiquetas de pago) y poblar el modelo Kimball en SQL Server.*

---

### 🚀 Cómo Ejecutar o Volver a Poblar el Modelo Kimball

Para poblar la base de datos `DM_Financial_Kimball_v2` desde cero en cualquier momento:

#### Requisitos:
```bash
pip install pymysql pyodbc
```

#### Ejecución normal (verifica y puebla tablas vacías):
```bash
python scripts/etl_populate_kimball_v2.py
```

#### Ejecución con reinicio total (limpia tablas y repuebla desde la fuente remota):
```bash
python scripts/etl_populate_kimball_v2.py --reset
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
    end

    OLTP --> ETL_K --> DM_K --> Dashboards
    OLTP --> ETL_I --> EDW --> DM_I --> Dashboards
```
