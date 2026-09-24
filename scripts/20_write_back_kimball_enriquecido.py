"""
==============================================================================
UNIVERSIDAD TÉCNICA DE AMBATO
FACULTAD DE INGENIERÍA EN SISTEMAS ELECTRÓNICA E INDUSTRIAL
CARRERA DE SOFTWARE - CICLO ACADÉMICO: AGOSTO 2026 – DICIEMBRE 2026
ASIGNATURA: Inteligencia de Negocios
DOCENTE: Ing. Ruben Nogales, Mg.
AUTORES: Alison Marcela Cobos Taco / Henry Daniel Lagua Flores
==============================================================================
ARCHIVO: 20_write_back_kimball_enriquecido.py
DESCRIPCIÓN: Script de retroalimentación analítica (Write-Back / Closed-Loop BI)
             que devuelve los datos limpios, imputados y enriquecidos a la base
             de datos dimensional Ralph Kimball en SQL Server (DM_Financial_Kimball_v2).
==============================================================================
"""

import os
import sys
import pyodbc
import pandas as pd
from datetime import datetime

# Rutas base
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_CLIENTE = os.path.join(BASE_DIR, "dataframes", "df_cliente_consolidado_clean.csv")

# Intentar servidores comunes
SERVERS = ["(localdb)\\MSSQLLocalDB", ".\\SQLEXPRESS", "localhost"]
DATABASE = "DM_Financial_Kimball_v2"

def obtener_conexion():
    for server in SERVERS:
        conn_str = (
            f"Driver={{ODBC Driver 17 for SQL Server}};"
            f"Server={server};"
            f"Database={DATABASE};"
            f"Trusted_Connection=yes;"
            f"TrustServerCertificate=yes;"
        )
        try:
            cnxn = pyodbc.connect(conn_str, timeout=5)
            print(f"[CONEXIÓN] Conectado exitosamente a SQL Server: {server} -> DB: {DATABASE}")
            return cnxn
        except Exception:
            continue
    # Probar con Driver 18 si falla el 17
    for server in SERVERS:
        conn_str = (
            f"Driver={{ODBC Driver 18 for SQL Server}};"
            f"Server={server};"
            f"Database={DATABASE};"
            f"Trusted_Connection=yes;"
            f"TrustServerCertificate=yes;"
        )
        try:
            cnxn = pyodbc.connect(conn_str, timeout=5)
            print(f"[CONEXIÓN] Conectado exitosamente a SQL Server (Driver 18): {server} -> DB: {DATABASE}")
            return cnxn
        except Exception:
            continue
    raise RuntimeError("No se pudo conectar a ninguna instancia de SQL Server con la base DM_Financial_Kimball_v2.")


def enriquecer_dim_distrito(cnxn):
    print("\n--- PASO 1: ENRIQUECIMIENTO Y AUDITORÍA EN Dim_Distrito ---")
    cursor = cnxn.cursor()
    
    # 1. Agregar columnas de trazabilidad y auditoría si no existen
    columnas_sql = [
        ("es_imputado", "BIT NOT NULL DEFAULT 0"),
        ("metodo_imputacion", "VARCHAR(50) NULL"),
        ("fecha_enriquecimiento", "DATETIME NULL")
    ]
    for col_name, col_type in columnas_sql:
        check_col = f"""
        IF NOT EXISTS (
            SELECT 1 FROM sys.columns 
            WHERE object_id = OBJECT_ID('Dim_Distrito') AND name = '{col_name}'
        )
        BEGIN
            ALTER TABLE Dim_Distrito ADD {col_name} {col_type};
            PRINT 'Columna {col_name} agregada a Dim_Distrito.';
        END
        """
        cursor.execute(check_col)
    cnxn.commit()
    
    # 2. Inicializar los 76 distritos originales con trazabilidad
    init_sql = """
    UPDATE Dim_Distrito
    SET es_imputado = 0,
        metodo_imputacion = 'Original PKDD99',
        fecha_enriquecimiento = GETDATE()
    WHERE id_distrito_bk <> 69 AND es_imputado = 0;
    """
    cursor.execute(init_sql)
    cnxn.commit()
    
    # 3. Imputar valores científicos de K-Means para el Distrito 69 (Jesenik)
    # Tasa desempleo = 5.0%, Tasa criminalidad = 3736.0
    update_69_sql = """
    UPDATE Dim_Distrito
    SET tasa_desempleo = 5.00,
        tasa_criminalidad = 3736.00,
        es_imputado = 1,
        metodo_imputacion = 'K-Means Clustered',
        fecha_enriquecimiento = GETDATE()
    WHERE id_distrito_bk = 69;
    """
    cursor.execute(update_69_sql)
    cnxn.commit()
    
    # Verificar
    cursor.execute("SELECT id_distrito_bk, nombre_distrito, region, tasa_desempleo, tasa_criminalidad, es_imputado, metodo_imputacion FROM Dim_Distrito WHERE id_distrito_bk = 69")
    row = cursor.fetchone()
    print(f"Distrito 69 actualizado exitosamente:")
    print(f"  ID: {row[0]}, Nombre: {row[1]}, Región: {row[2]}")
    print(f"  Tasa Desempleo: {row[3]}%, Criminalidad: {row[4]}")
    print(f"  Es Imputado: {row[5]}, Método: {row[6]}")


def estandarizar_dim_orden(cnxn):
    print("\n--- PASO 2: HOMOLOGACIÓN CATEGÓRICA EN Dim_Orden ---")
    cursor = cnxn.cursor()
    # Asegurar que el registro vacío se rotule formalmente como 'SIN_ESPECIFICAR'
    sql_orden = """
    UPDATE Dim_Orden
    SET k_symbol_original = 'SIN_ESPECIFICAR',
        categoria_orden_traducida = 'Sin Especificar'
    WHERE k_symbol_original = '' OR k_symbol_original IS NULL;
    """
    cursor.execute(sql_orden)
    cnxn.commit()
    
    cursor.execute("SELECT sk_orden_tipo, k_symbol_original, categoria_orden_traducida FROM Dim_Orden")
    rows = cursor.fetchall()
    print("Catálogo Dim_Orden homologado:")
    for r in rows:
        print(f"  SK {r[0]}: {r[1]} -> {r[2]}")


def enriquecer_dim_cliente(cnxn):
    print("\n--- PASO 3: ENRIQUECIMIENTO ANALÍTICO EN Dim_Cliente ---")
    cursor = cnxn.cursor()
    
    # 1. Agregar columnas analíticas de segmentación y perfil si no existen
    columnas_cli = [
        ("macro_region", "VARCHAR(20) NULL"),
        ("segmento_edad", "VARCHAR(30) NULL"),
        ("arquetipo_demografico", "VARCHAR(50) NULL"),
        ("tiene_prestamo", "BIT NOT NULL DEFAULT 0"),
        ("total_ordenes_activas", "INT NOT NULL DEFAULT 0"),
        ("saldo_promedio", "DECIMAL(12,2) NULL"),
        ("fecha_enriquecimiento", "DATETIME NULL")
    ]
    for col_name, col_type in columnas_cli:
        check_col = f"""
        IF NOT EXISTS (
            SELECT 1 FROM sys.columns 
            WHERE object_id = OBJECT_ID('Dim_Cliente') AND name = '{col_name}'
        )
        BEGIN
            ALTER TABLE Dim_Cliente ADD {col_name} {col_type};
            PRINT 'Columna {col_name} agregada a Dim_Cliente.';
        END
        """
        cursor.execute(check_col)
    cnxn.commit()
    
    # 2. Cargar DataFrame limpio y preparar features
    print(f"Cargando dataset analítico: {CSV_CLIENTE}...")
    df_cli = pd.read_csv(CSV_CLIENTE)
    
    def get_macro_region(r):
        r_str = str(r).lower()
        if 'prague' in r_str or 'praga' in r_str: return 'Praga'
        if 'bohemia' in r_str: return 'Bohemia'
        return 'Moravia'
    
    df_cli['macro_region'] = df_cli['region'].apply(get_macro_region)
    df_cli['segmento_edad'] = pd.cut(
        df_cli['edad_corte'], 
        bins=[0, 30, 50, 120], 
        labels=['Joven (<30)', 'Adulto (30-50)', 'Adulto Mayor (>50)'], 
        right=False
    ).astype(str)
    df_cli['arquetipo_demografico'] = df_cli['macro_region'] + ' - ' + df_cli['segmento_edad']
    df_cli['tiene_prestamo'] = df_cli['tiene_prestamo'].fillna(0).astype(int)
    df_cli['total_ordenes_activas'] = df_cli['total_ordenes_activas'].fillna(0).astype(int)
    df_cli['saldo_promedio'] = df_cli['saldo_promedio'].fillna(0.0).round(2)
    
    # 3. Batch Update utilizando tabla temporal para máxima velocidad
    print("Creando tabla temporal de staging para actualización por lotes...")
    create_staging = """
    IF OBJECT_ID('tempdb..#StagingClienteEnriquecido') IS NOT NULL
        DROP TABLE #StagingClienteEnriquecido;

    CREATE TABLE #StagingClienteEnriquecido (
        id_cliente_bk INT PRIMARY KEY,
        macro_region VARCHAR(20),
        segmento_edad VARCHAR(30),
        arquetipo_demografico VARCHAR(50),
        tiene_prestamo BIT,
        total_ordenes_activas INT,
        saldo_promedio DECIMAL(12,2)
    );
    """
    cursor.execute(create_staging)
    
    # Inserción en staging
    insert_staging = """
    INSERT INTO #StagingClienteEnriquecido (
        id_cliente_bk, macro_region, segmento_edad, arquetipo_demografico,
        tiene_prestamo, total_ordenes_activas, saldo_promedio
    ) VALUES (?, ?, ?, ?, ?, ?, ?);
    """
    
    records = []
    for _, row in df_cli.iterrows():
        records.append((
            int(row['id_cliente']),
            str(row['macro_region']),
            str(row['segmento_edad']),
            str(row['arquetipo_demografico']),
            int(row['tiene_prestamo']),
            int(row['total_ordenes_activas']),
            float(row['saldo_promedio'])
        ))
    
    cursor.fast_executemany = True
    cursor.executemany(insert_staging, records)
    print(f"Cargados {len(records)} registros en tabla de staging temporal.")
    
    # Actualización masiva de Dim_Cliente
    update_dim_cli = """
    UPDATE c
    SET c.macro_region = s.macro_region,
        c.segmento_edad = s.segmento_edad,
        c.arquetipo_demografico = s.arquetipo_demografico,
        c.tiene_prestamo = s.tiene_prestamo,
        c.total_ordenes_activas = s.total_ordenes_activas,
        c.saldo_promedio = s.saldo_promedio,
        c.fecha_enriquecimiento = GETDATE()
    FROM Dim_Cliente c
    INNER JOIN #StagingClienteEnriquecido s ON c.id_cliente_bk = s.id_cliente_bk;
    """
    cursor.execute(update_dim_cli)
    cnxn.commit()
    print("Actualización masiva de Dim_Cliente completada exitosamente.")
    
    # Verificación de distribución de arquetipos en la base dimensional
    cursor.execute("""
    SELECT arquetipo_demografico, COUNT(*) AS total_clientes, SUM(CAST(tiene_prestamo AS INT)) AS con_prestamo
    FROM Dim_Cliente
    GROUP BY arquetipo_demografico
    ORDER BY total_clientes DESC;
    """)
    print("\nDistribución final de Estereotipos en SQL Server (Dim_Cliente):")
    for r in cursor.fetchall():
        pct = (r[2] / r[1]) * 100 if r[1] > 0 else 0
        print(f"  {r[0]:<35} : {r[1]:>5} clientes | {r[2]:>4} con préstamo ({pct:.1f}%)")


def generar_script_sql():
    sql_path = os.path.join(BASE_DIR, "sql", "03_WriteBack_Enriquecimiento_Kimball.sql")
    sql_content = """-- ==============================================================================
-- UNIVERSIDAD TÉCNICA DE AMBATO
-- FACULTAD DE INGENIERÍA EN SISTEMAS ELECTRÓNICA E INDUSTRIAL
-- CARRERA DE SOFTWARE - CICLO ACADÉMICO: AGOSTO 2026 – DICIEMBRE 2026
-- ASIGNATURA: Inteligencia de Negocios
-- DOCENTE: Ing. Ruben Nogales, Mg.
-- AUTORES: Alison Marcela Cobos Taco / Henry Daniel Lagua Flores
-- ==============================================================================
-- ARCHIVO: 03_WriteBack_Enriquecimiento_Kimball.sql
-- DESCRIPCIÓN: Procedimiento de retroalimentación analítica (Write-Back)
--              para devolver datos limpios, imputados y perfiles a SQL Server.
-- ==============================================================================

USE DM_Financial_Kimball_v2;
GO

-- 1. ACTUALIZACIÓN Y TRAZABILIDAD EN Dim_Distrito
IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('Dim_Distrito') AND name = 'es_imputado')
BEGIN
    ALTER TABLE Dim_Distrito ADD es_imputado BIT NOT NULL DEFAULT 0;
    ALTER TABLE Dim_Distrito ADD metodo_imputacion VARCHAR(50) NULL;
    ALTER TABLE Dim_Distrito ADD fecha_enriquecimiento DATETIME NULL;
END
GO

-- Inicializar auditoría para distritos históricos
UPDATE Dim_Distrito
SET es_imputado = 0,
    metodo_imputacion = 'Original PKDD99',
    fecha_enriquecimiento = GETDATE()
WHERE id_distrito_bk <> 69;
GO

-- Imputar valores científicos calculados mediante K-Means para el Distrito 69 (Jesenik)
UPDATE Dim_Distrito
SET tasa_desempleo = 5.00,
    tasa_criminalidad = 3736.00,
    es_imputado = 1,
    metodo_imputacion = 'K-Means Clustered',
    fecha_enriquecimiento = GETDATE()
WHERE id_distrito_bk = 69;
GO

-- 2. HOMOLOGACIÓN CATEGÓRICA EN Dim_Orden
UPDATE Dim_Orden
SET k_symbol_original = 'SIN_ESPECIFICAR',
    categoria_orden_traducida = 'Sin Especificar'
WHERE k_symbol_original = '' OR k_symbol_original IS NULL;
GO

-- 3. COLUMNAS DE PERFIL Y SEGMENTACIÓN EN Dim_Cliente
IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('Dim_Cliente') AND name = 'arquetipo_demografico')
BEGIN
    ALTER TABLE Dim_Cliente ADD macro_region VARCHAR(20) NULL;
    ALTER TABLE Dim_Cliente ADD segmento_edad VARCHAR(30) NULL;
    ALTER TABLE Dim_Cliente ADD arquetipo_demografico VARCHAR(50) NULL;
    ALTER TABLE Dim_Cliente ADD tiene_prestamo BIT NOT NULL DEFAULT 0;
    ALTER TABLE Dim_Cliente ADD total_ordenes_activas INT NOT NULL DEFAULT 0;
    ALTER TABLE Dim_Cliente ADD saldo_promedio DECIMAL(12,2) NULL;
    ALTER TABLE Dim_Cliente ADD fecha_enriquecimiento DATETIME NULL;
END
GO

PRINT 'Estructura dimensional preparada y enriquecida para Closed-Loop BI.';
GO
"""
    with open(sql_path, "w", encoding="utf-8") as f:
        f.write(sql_content)
    print(f"\n[SQL] Script T-SQL formal generado en: {sql_path}")


def main():
    print("=" * 80)
    print("FASE 4: WRITE-BACK Y ENRIQUECIMIENTO DIMENSIONAL (KIMBALL)")
    print("=" * 80)
    
    # 1. Generar script T-SQL oficial
    generar_script_sql()
    
    # 2. Conectar a la base de datos SQL Server
    cnxn = obtener_conexion()
    
    try:
        # 3. Enriquecer Dim_Distrito
        enriquecer_dim_distrito(cnxn)
        
        # 4. Estandarizar Dim_Orden
        estandarizar_dim_orden(cnxn)
        
        # 5. Enriquecer Dim_Cliente
        enriquecer_dim_cliente(cnxn)
        
        print("\n" + "=" * 80)
        print("FASE 4 COMPLETADA CON ÉXITO: MODELO KIMBALL RETROALIMENTADO Y 100% LIMPIO")
        print("=" * 80)
    finally:
        cnxn.close()

if __name__ == "__main__":
    main()
