"""
==============================================================================
UNIVERSIDAD TÉCNICA DE AMBATO
FACULTAD DE INGENIERÍA EN SISTEMAS ELECTRÓNICA E INDUSTRIAL
CARRERA DE SOFTWARE - CICLO ACADÉMICO: AGOSTO 2026 – DICIEMBRE 2026
ASIGNATURA: Inteligencia de Negocios
DOCENTE: Ing. Ruben Nogales, Mg.
AUTORES: Alison Marcela Cobos Taco / Henry Daniel Lagua Flores
==============================================================================
ARCHIVO: generar_4_dataframes.py
DESCRIPCIÓN: Script para extraer y consolidar los 4 DataFrames analíticos
             a partir del modelo dimensional Ralph Kimball (DM_Financial_Kimball_v2)
             y enriquecerlos con campos operativos de la base remota:

             1. df_prestamos (682 filas): Cartera, riesgo y morosidad.
             2. df_ordenes (6,471 filas): Débitos automáticos programados.
             3. df_cliente_consolidado (5,369 filas): Matriz Cliente 360.
             4. df_transacciones (1,056,320 filas): Movimientos contables.

REQUISITOS:
    pip install pandas pyodbc pymysql pyarrow
==============================================================================
"""

import pyodbc
import pymysql
import pandas as pd
import os
import time
import sys

# 1. Rutas y configuración de conexiones
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "dataframes")
os.makedirs(OUTPUT_DIR, exist_ok=True)

SQL_SERVER_CONN_STR = (
    "Driver={ODBC Driver 18 for SQL Server};"
    "Server=(localdb)\\MSSQLLocalDB;"
    "Database=DM_Financial_Kimball_v2;"
    "Trusted_Connection=yes;"
    "TrustServerCertificate=yes;"
)

MYSQL_CONFIG = {
    'host': 'relational.fel.cvut.cz',
    'port': 3306,
    'user': 'guest',
    'password': 'ctu-relational',
    'database': 'Financial_ijs',
    'charset': 'utf8mb4'
}

def main():
    print("=" * 80)
    print("GENERACIÓN DE LOS 4 DATAFRAMES ANALÍTICOS (KIMBALL)")
    print("=" * 80)
    t0 = time.time()

    print("\n[1/5] Conectando a SQL Server local y MySQL remoto...")
    try:
        conn = pyodbc.connect(SQL_SERVER_CONN_STR)
        conn_rem = pymysql.connect(**MYSQL_CONFIG)
        print("   -> Conexiones establecidas con éxito.")
    except Exception as e:
        print(f"   [ERROR] Error al conectar: {e}")
        sys.exit(1)

    # --------------------------------------------------------------------------
    # DATAFRAME 1: df_prestamos (682 filas)
    # --------------------------------------------------------------------------
    print("\n[2/5] Generando DataFrame 1: df_prestamos (Cartera y Morosidad)...")
    query_prestamos = """
    SELECT 
        fp.id_prestamo_bk AS id_prestamo,
        t.fecha AS fecha_otorgamiento,
        t.anio AS anio_otorgamiento,
        t.mes AS mes_otorgamiento,
        c.id_cliente_bk AS id_cliente,
        c.sexo AS sexo_cliente,
        c.edad_corte AS edad_cliente,
        c.tipo_disposicion,
        cu.id_cuenta_bk AS id_cuenta,
        cu.frecuencia_emision_estado,
        d.id_distrito_bk AS id_distrito,
        d.nombre_distrito,
        d.region,
        d.poblacion AS poblacion_distrito,
        d.salario_promedio AS salario_distrito,
        d.tasa_desempleo AS desempleo_distrito,
        d.tasa_criminalidad AS crimen_distrito,
        ep.codigo_estado AS estado_prestamo,
        ep.condicion AS condicion_prestamo,
        ep.descripcion AS descripcion_estado,
        fp.monto_prestamo,
        fp.plazo_meses,
        fp.pago_mensual,
        fp.saldo_pendiente_estimado
    FROM Fact_Prestamos fp
    JOIN Dim_Tiempo t ON fp.sk_tiempo = t.sk_tiempo
    JOIN Dim_Cuenta cu ON fp.sk_cuenta = cu.sk_cuenta
    JOIN Dim_Cliente c ON fp.sk_cliente = c.sk_cliente
    JOIN Dim_Distrito d ON fp.sk_distrito = d.sk_distrito
    JOIN Dim_Estado_Prestamo ep ON fp.sk_estado_prestamo = ep.sk_estado_prestamo
    ORDER BY fp.id_prestamo_bk;
    """
    df_prestamos = pd.read_sql(query_prestamos, conn)
    csv_p = os.path.join(OUTPUT_DIR, "df_prestamos.csv")
    df_prestamos.to_csv(csv_p, index=False, encoding='utf-8-sig')
    print(f"   -> df_prestamos: {len(df_prestamos):,} filas x {df_prestamos.shape[1]} columnas guardado en CSV.")

    # --------------------------------------------------------------------------
    # DATAFRAME 2: df_ordenes (6,471 filas)
    # --------------------------------------------------------------------------
    print("\n[3/5] Generando DataFrame 2: df_ordenes (Débitos Recurrentes)...")
    query_ordenes = """
    SELECT 
        fo.id_orden_bk AS id_orden,
        cu.id_cuenta_bk AS id_cuenta,
        c.id_cliente_bk AS id_cliente,
        c.sexo AS sexo_cliente,
        c.edad_corte AS edad_cliente,
        t.fecha AS fecha_apertura_cuenta,
        d.id_distrito_bk AS id_distrito,
        d.nombre_distrito,
        d.region,
        o.k_symbol_original AS k_symbol,
        o.categoria_orden_traducida AS categoria_orden,
        fo.monto_orden
    FROM Fact_Ordenes fo
    JOIN Dim_Tiempo t ON fo.sk_tiempo = t.sk_tiempo
    JOIN Dim_Cuenta cu ON fo.sk_cuenta = cu.sk_cuenta
    JOIN Dim_Cliente c ON fo.sk_cliente = c.sk_cliente
    JOIN Dim_Distrito d ON fo.sk_distrito = d.sk_distrito
    JOIN Dim_Orden o ON fo.sk_orden_tipo = o.sk_orden_tipo
    ORDER BY fo.id_orden_bk;
    """
    df_ordenes = pd.read_sql(query_ordenes, conn)
    df_rem_orders = pd.read_sql("SELECT id AS id_orden, bank_to, account_to FROM orders", conn_rem)
    df_ordenes = df_ordenes.merge(df_rem_orders, on='id_orden', how='left')
    
    cols_ordenes = [
        'id_orden', 'id_cuenta', 'id_cliente', 'sexo_cliente', 'edad_cliente',
        'fecha_apertura_cuenta', 'id_distrito', 'nombre_distrito', 'region',
        'bank_to', 'account_to', 'k_symbol', 'categoria_orden', 'monto_orden'
    ]
    df_ordenes = df_ordenes[cols_ordenes]
    csv_o = os.path.join(OUTPUT_DIR, "df_ordenes.csv")
    df_ordenes.to_csv(csv_o, index=False, encoding='utf-8-sig')
    print(f"   -> df_ordenes: {len(df_ordenes):,} filas x {df_ordenes.shape[1]} columnas guardado en CSV.")

    # --------------------------------------------------------------------------
    # DATAFRAME 3: df_cliente_consolidado (5,369 filas - Cliente 360)
    # --------------------------------------------------------------------------
    print("\n[4/5] Generando DataFrame 3: df_cliente_consolidado (Cliente 360)...")
    df_cli_base = pd.read_sql("""
        SELECT 
            c.id_cliente_bk AS id_cliente,
            c.sexo,
            c.fecha_nacimiento,
            c.edad_corte,
            c.tipo_disposicion,
            c.etiqueta_buen_pagador,
            d.id_distrito_bk AS id_distrito,
            d.nombre_distrito,
            d.region,
            d.poblacion,
            d.salario_promedio,
            d.tasa_desempleo,
            d.tasa_criminalidad
        FROM Dim_Cliente c
        JOIN Dim_Distrito d ON c.sk_distrito = d.sk_distrito
    """, conn)

    df_prest_agg = pd.read_sql("""
        SELECT 
            c.id_cliente_bk AS id_cliente,
            1 AS tiene_prestamo,
            fp.id_prestamo_bk AS id_prestamo,
            fp.monto_prestamo,
            fp.plazo_meses AS plazo_prestamo,
            fp.pago_mensual AS cuota_mensual_prestamo,
            ep.codigo_estado AS estado_prestamo,
            ep.condicion AS condicion_prestamo
        FROM Fact_Prestamos fp
        JOIN Dim_Cliente c ON fp.sk_cliente = c.sk_cliente
        JOIN Dim_Estado_Prestamo ep ON fp.sk_estado_prestamo = ep.sk_estado_prestamo
    """, conn)

    df_ord_agg = pd.read_sql("""
        SELECT 
            c.id_cliente_bk AS id_cliente,
            COUNT(fo.id_orden_bk) AS total_ordenes_activas,
            SUM(fo.monto_orden) AS monto_total_ordenes_mensual,
            AVG(fo.monto_orden) AS monto_promedio_orden
        FROM Fact_Ordenes fo
        JOIN Dim_Cliente c ON fo.sk_cliente = c.sk_cliente
        GROUP BY c.id_cliente_bk
    """, conn)

    df_tr_agg = pd.read_sql("""
        SELECT 
            c.id_cliente_bk AS id_cliente,
            COUNT(ft.id_transaccion_bk) AS total_transacciones,
            SUM(CASE WHEN op.tipo_operacion_original = 'PRIJEM' THEN ft.monto_transaccion ELSE 0 END) AS total_depositos,
            SUM(CASE WHEN op.tipo_operacion_original IN ('VYDAJ', 'VYBER') THEN ft.monto_transaccion ELSE 0 END) AS total_retiros,
            AVG(ft.saldo_cuenta) AS saldo_promedio,
            MIN(ft.saldo_cuenta) AS saldo_minimo,
            MAX(ft.saldo_cuenta) AS saldo_maximo
        FROM Fact_Transacciones ft
        JOIN Dim_Cliente c ON ft.sk_cliente = c.sk_cliente
        JOIN Dim_Operacion op ON ft.sk_operacion = op.sk_operacion
        GROUP BY c.id_cliente_bk
    """, conn)

    df_cliente = df_cli_base.merge(df_prest_agg, on='id_cliente', how='left')
    df_cliente = df_cliente.merge(df_ord_agg, on='id_cliente', how='left')
    df_cliente = df_cliente.merge(df_tr_agg, on='id_cliente', how='left')

    df_cliente['tiene_prestamo'] = df_cliente['tiene_prestamo'].fillna(0).astype(int)
    df_cliente['monto_prestamo'] = df_cliente['monto_prestamo'].fillna(0.0)
    df_cliente['cuota_mensual_prestamo'] = df_cliente['cuota_mensual_prestamo'].fillna(0.0)
    df_cliente['estado_prestamo'] = df_cliente['estado_prestamo'].fillna('Sin Prestamo')
    df_cliente['condicion_prestamo'] = df_cliente['condicion_prestamo'].fillna('Sin Prestamo')
    df_cliente['total_ordenes_activas'] = df_cliente['total_ordenes_activas'].fillna(0).astype(int)
    df_cliente['monto_total_ordenes_mensual'] = df_cliente['monto_total_ordenes_mensual'].fillna(0.0)
    df_cliente['total_transacciones'] = df_cliente['total_transacciones'].fillna(0).astype(int)
    df_cliente['total_depositos'] = df_cliente['total_depositos'].fillna(0.0)
    df_cliente['total_retiros'] = df_cliente['total_retiros'].fillna(0.0)

    csv_c = os.path.join(OUTPUT_DIR, "df_cliente_consolidado.csv")
    df_cliente.to_csv(csv_c, index=False, encoding='utf-8-sig')
    print(f"   -> df_cliente_consolidado: {len(df_cliente):,} filas x {df_cliente.shape[1]} columnas guardado en CSV.")

    # --------------------------------------------------------------------------
    # DATAFRAME 4: df_transacciones (1,056,320 filas)
    # --------------------------------------------------------------------------
    print("\n[5/5] Generando DataFrame 4: df_transacciones (1,056,320 filas)...")
    query_trans = """
    SELECT 
        ft.id_transaccion_bk AS id_transaccion,
        t.fecha,
        t.anio,
        t.mes,
        t.dia,
        cu.id_cuenta_bk AS id_cuenta,
        c.id_cliente_bk AS id_cliente,
        c.sexo AS sexo_cliente,
        c.edad_corte AS edad_cliente,
        d.id_distrito_bk AS id_distrito,
        d.nombre_distrito,
        d.region,
        op.tipo_operacion_original AS tipo_transaccion,
        op.tipo_operacion_traducido,
        op.canal,
        ft.monto_transaccion,
        ft.saldo_cuenta
    FROM Fact_Transacciones ft
    JOIN Dim_Tiempo t ON ft.sk_tiempo = t.sk_tiempo
    JOIN Dim_Cuenta cu ON ft.sk_cuenta = cu.sk_cuenta
    JOIN Dim_Cliente c ON ft.sk_cliente = c.sk_cliente
    JOIN Dim_Distrito d ON ft.sk_distrito = d.sk_distrito
    JOIN Dim_Operacion op ON ft.sk_operacion = op.sk_operacion
    ORDER BY ft.id_transaccion_bk;
    """
    df_trans = pd.read_sql(query_trans, conn)
    df_rem_trans = pd.read_sql("SELECT id AS id_transaccion, operation, k_symbol, bank, account FROM trans ORDER BY id", conn_rem)
    df_trans = df_trans.merge(df_rem_trans, on='id_transaccion', how='left')

    cols_trans = [
        'id_transaccion', 'id_cuenta', 'id_cliente', 'sexo_cliente', 'edad_cliente',
        'id_distrito', 'nombre_distrito', 'region',
        'fecha', 'anio', 'mes', 'dia',
        'tipo_transaccion', 'tipo_operacion_traducido', 'canal',
        'operation', 'k_symbol', 'bank', 'account',
        'monto_transaccion', 'saldo_cuenta'
    ]
    df_trans = df_trans[cols_trans]

    # Guardar en CSV estándar, CSV comprimido (.gz) y Parquet
    csv_t = os.path.join(OUTPUT_DIR, "df_transacciones.csv")
    csv_t_gz = os.path.join(OUTPUT_DIR, "df_transacciones.csv.gz")
    parq_t = os.path.join(OUTPUT_DIR, "df_transacciones.parquet")

    df_trans.to_parquet(parq_t, index=False, engine='pyarrow')
    df_trans.to_csv(csv_t_gz, index=False, compression='gzip', encoding='utf-8-sig')
    df_trans.to_csv(csv_t, index=False, encoding='utf-8-sig')

    print(f"   -> df_transacciones: {len(df_trans):,} filas x {df_trans.shape[1]} columnas.")
    print(f"      - CSV: {csv_t} ({os.path.getsize(csv_t)/(1024*1024):.2f} MB)")
    print(f"      - CSV.GZ: {csv_t_gz} ({os.path.getsize(csv_t_gz)/(1024*1024):.2f} MB)")
    print(f"      - Parquet: {parq_t} ({os.path.getsize(parq_t)/(1024*1024):.2f} MB)")

    conn.close()
    conn_rem.close()

    t1 = time.time()
    print("\n" + "=" * 80)
    print(f"PROCESO COMPLETADO EXITOSAMENTE EN {t1 - t0:.2f} SEGUNDOS")
    print("=" * 80)

if __name__ == '__main__':
    main()
