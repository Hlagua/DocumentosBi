"""
==============================================================================
UNIVERSIDAD TÉCNICA DE AMBATO - Inteligencia de Negocios
AUTORES: Alison Marcela Cobos Taco / Henry Daniel Lagua Flores
==============================================================================
ARCHIVO: 32_extraer_dataframes_kimball.py
PASO 1 DE 3 DE LA COMPLETITUD DE DATOS (32 -> 33 -> 34)
DESCRIPCIÓN: Genera los DataFrames analíticos a partir del Data Mart Kimball
             (DM_Financial_Kimball_v2, cargado por el script 31) y les añade
             las columnas operativas originales del OLTP (con sus huecos),
             para diagnosticarlas y completarlas en el script 33.

             dataframes/df_distritos.csv            77 filas (indicadores 1995 y 1996)
             dataframes/df_prestamos.csv            682 filas
             dataframes/df_ordenes.csv              6,471 filas
             dataframes/df_cliente_consolidado.csv  5,369 filas (Cliente 360)
             dataframes/df_transacciones.csv.gz     1,056,320 filas
USO:         python scripts/32_extraer_dataframes_kimball.py
==============================================================================
"""
import os
import time
import warnings

import pandas as pd
import pymysql
import pyodbc

warnings.filterwarnings("ignore", message="pandas only supports SQLAlchemy")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SALIDA = os.path.join(BASE_DIR, "dataframes")
KIMBALL = ("Driver={ODBC Driver 17 for SQL Server};Server=(localdb)\\MSSQLLocalDB;"
           "Database=DM_Financial_Kimball_v2;Trusted_Connection=yes;")
MYSQL = dict(host="relational.fel.cvut.cz", port=3306, user="guest", password="ctu-relational",
             database="Financial_ijs", charset="utf8mb4", connect_timeout=30)


def vacio_a_nulo(serie):
    """En el OLTP los faltantes vienen como NULL o como cadena vacía: se unifican como NULL."""
    return serie.where(serie.isna() | (serie.astype(str).str.strip() != ""), None)


def guardar(df, nombre, comprimir=False):
    ruta = os.path.join(SALIDA, nombre)
    df.to_csv(ruta, index=False, encoding="utf-8-sig", compression="gzip" if comprimir else None)
    nulos = df.isna().sum()
    print(f"  {nombre:<32} {len(df):>10,} filas x {df.shape[1]:>2} columnas | "
          f"columnas con nulos: {nulos[nulos > 0].to_dict()}")


def main():
    t0 = time.time()
    os.makedirs(SALIDA, exist_ok=True)
    cn = pyodbc.connect(KIMBALL, timeout=120)
    rem = pymysql.connect(**MYSQL)
    print("Generando DataFrames desde DM_Financial_Kimball_v2 (+ columnas originales del OLTP)")

    # 0. Distritos (necesario para imputar el distrito 69 con sus propios datos de 1996)
    guardar(pd.read_sql("""
        SELECT id_distrito_bk AS id_distrito, nombre_distrito, region, poblacion, salario_promedio,
               tasa_desempleo AS tasa_desempleo_1995, tasa_desempleo_1996,
               tasa_criminalidad AS tasa_criminalidad_1995, tasa_criminalidad_1996
        FROM Dim_Distrito ORDER BY id_distrito_bk""", cn), "df_distritos.csv")

    # 1. Préstamos
    guardar(pd.read_sql("""
        SELECT fp.id_prestamo_bk AS id_prestamo, t.fecha AS fecha_otorgamiento, t.anio AS anio_otorgamiento,
               t.mes AS mes_otorgamiento, c.id_cliente_bk AS id_cliente, c.sexo AS sexo_cliente,
               c.edad_corte AS edad_cliente, c.tipo_disposicion, cu.id_cuenta_bk AS id_cuenta,
               cu.frecuencia_emision_estado, d.id_distrito_bk AS id_distrito, d.nombre_distrito, d.region,
               d.poblacion AS poblacion_distrito, d.salario_promedio AS salario_distrito,
               d.tasa_desempleo AS desempleo_distrito, d.tasa_criminalidad AS crimen_distrito,
               ep.codigo_estado AS estado_prestamo, ep.condicion AS condicion_prestamo,
               ep.descripcion AS descripcion_estado, fp.monto_prestamo, fp.plazo_meses, fp.pago_mensual,
               fp.saldo_pendiente_estimado, fp.meses_transcurridos_al_corte, fp.saldo_promedio_previo,
               fp.ratio_cuota_saldo_previo, fp.banda_capacidad
        FROM Fact_Prestamos fp
        JOIN Dim_Tiempo t ON t.sk_tiempo = fp.sk_tiempo
        JOIN Dim_Cuenta cu ON cu.sk_cuenta = fp.sk_cuenta
        JOIN Dim_Cliente c ON c.sk_cliente = fp.sk_cliente
        JOIN Dim_Distrito d ON d.sk_distrito = fp.sk_distrito
        JOIN Dim_Estado_Prestamo ep ON ep.sk_estado_prestamo = fp.sk_estado_prestamo
        ORDER BY fp.id_prestamo_bk""", cn), "df_prestamos.csv")

    # 2. Órdenes: k_symbol, bank_to y account_to se toman del OLTP tal como vienen
    ordenes = pd.read_sql("""
        SELECT fo.id_orden_bk AS id_orden, cu.id_cuenta_bk AS id_cuenta, c.id_cliente_bk AS id_cliente,
               c.sexo AS sexo_cliente, c.edad_corte AS edad_cliente, t.fecha AS fecha_apertura_cuenta,
               d.id_distrito_bk AS id_distrito, d.nombre_distrito, d.region,
               o.categoria_orden_traducida AS categoria_orden, fo.monto_orden
        FROM Fact_Ordenes fo
        JOIN Dim_Tiempo t ON t.sk_tiempo = fo.sk_tiempo_apertura_cuenta
        JOIN Dim_Cuenta cu ON cu.sk_cuenta = fo.sk_cuenta
        JOIN Dim_Cliente c ON c.sk_cliente = fo.sk_cliente
        JOIN Dim_Distrito d ON d.sk_distrito = fo.sk_distrito
        JOIN Dim_Orden o ON o.sk_orden_tipo = fo.sk_orden_tipo""", cn)
    origen = pd.read_sql("SELECT id AS id_orden, bank_to, account_to, k_symbol FROM orders", rem)
    origen["k_symbol"] = vacio_a_nulo(origen.k_symbol)
    ordenes = ordenes.merge(origen, on="id_orden", how="left").sort_values("id_orden")
    guardar(ordenes[["id_orden", "id_cuenta", "id_cliente", "sexo_cliente", "edad_cliente", "fecha_apertura_cuenta",
                     "id_distrito", "nombre_distrito", "region", "bank_to", "account_to", "k_symbol",
                     "categoria_orden", "monto_orden"]], "df_ordenes.csv")

    # 3. Cliente 360
    base = pd.read_sql("""
        SELECT c.id_cliente_bk AS id_cliente, c.sexo, c.fecha_nacimiento, c.edad_corte, c.tipo_disposicion,
               c.etiqueta_buen_pagador, d.id_distrito_bk AS id_distrito, d.nombre_distrito, d.region, d.poblacion,
               d.salario_promedio, d.tasa_desempleo, d.tasa_criminalidad
        FROM Dim_Cliente c JOIN Dim_Distrito d ON d.sk_distrito = c.sk_distrito""", cn)
    prestamo = pd.read_sql("""
        SELECT c.id_cliente_bk AS id_cliente, 1 AS tiene_prestamo, fp.id_prestamo_bk AS id_prestamo,
               fp.monto_prestamo, fp.plazo_meses AS plazo_prestamo, fp.pago_mensual AS cuota_mensual_prestamo,
               ep.codigo_estado AS estado_prestamo, ep.condicion AS condicion_prestamo
        FROM Fact_Prestamos fp JOIN Dim_Cliente c ON c.sk_cliente = fp.sk_cliente
        JOIN Dim_Estado_Prestamo ep ON ep.sk_estado_prestamo = fp.sk_estado_prestamo""", cn)
    orden = pd.read_sql("""
        SELECT c.id_cliente_bk AS id_cliente, COUNT(*) AS total_ordenes_activas,
               SUM(fo.monto_orden) AS monto_total_ordenes_mensual, AVG(fo.monto_orden) AS monto_promedio_orden
        FROM Fact_Ordenes fo JOIN Dim_Cliente c ON c.sk_cliente = fo.sk_cliente GROUP BY c.id_cliente_bk""", cn)
    movimiento = pd.read_sql("""
        SELECT c.id_cliente_bk AS id_cliente, COUNT(*) AS total_transacciones,
               SUM(CASE WHEN o.tipo_original = 'PRIJEM' THEN ft.monto_transaccion ELSE 0 END) AS total_depositos,
               SUM(CASE WHEN o.tipo_original <> 'PRIJEM' THEN ft.monto_transaccion ELSE 0 END) AS total_retiros,
               AVG(ft.saldo_cuenta) AS saldo_promedio, MIN(ft.saldo_cuenta) AS saldo_minimo,
               MAX(ft.saldo_cuenta) AS saldo_maximo
        FROM Fact_Transacciones ft JOIN Dim_Cliente c ON c.sk_cliente = ft.sk_cliente
        JOIN Dim_Operacion o ON o.sk_operacion = ft.sk_operacion GROUP BY c.id_cliente_bk""", cn)
    cli = base.merge(prestamo, on="id_cliente", how="left").merge(orden, on="id_cliente", how="left") \
              .merge(movimiento, on="id_cliente", how="left").sort_values("id_cliente")
    # Ceros legítimos (conteos y sumas de cosas que el cliente no tiene); el resto de nulos se diagnostica en el script 33
    for col in ["tiene_prestamo", "total_ordenes_activas", "total_transacciones"]:
        cli[col] = cli[col].fillna(0).astype(int)
    for col in ["monto_prestamo", "cuota_mensual_prestamo", "monto_total_ordenes_mensual", "total_depositos", "total_retiros"]:
        cli[col] = cli[col].fillna(0.0)
    for col in ["estado_prestamo", "condicion_prestamo"]:
        cli[col] = cli[col].fillna("Sin Prestamo")
    guardar(cli, "df_cliente_consolidado.csv")

    # 4. Transacciones: operation, k_symbol, bank y account se toman del OLTP tal como vienen
    trans = pd.read_sql("""
        SELECT ft.id_transaccion_bk AS id_transaccion, cu.id_cuenta_bk AS id_cuenta, c.id_cliente_bk AS id_cliente,
               c.sexo AS sexo_cliente, c.edad_corte AS edad_cliente, d.id_distrito_bk AS id_distrito,
               d.nombre_distrito, d.region, t.fecha, t.anio, t.mes, t.dia, o.tipo_original AS tipo_transaccion,
               o.categoria_analitica AS tipo_operacion_traducido, o.operacion_traducida AS canal,
               ft.monto_transaccion, ft.saldo_cuenta
        FROM Fact_Transacciones ft
        JOIN Dim_Tiempo t ON t.sk_tiempo = ft.sk_tiempo
        JOIN Dim_Cuenta cu ON cu.sk_cuenta = ft.sk_cuenta
        JOIN Dim_Cliente c ON c.sk_cliente = ft.sk_cliente
        JOIN Dim_Distrito d ON d.sk_distrito = ft.sk_distrito
        JOIN Dim_Operacion o ON o.sk_operacion = ft.sk_operacion""", cn)
    origen = pd.read_sql("SELECT id AS id_transaccion, operation, k_symbol, bank, account FROM trans", rem)
    for col in ["operation", "k_symbol", "bank", "account"]:
        origen[col] = vacio_a_nulo(origen[col])
    trans = trans.merge(origen, on="id_transaccion", how="left").sort_values("id_transaccion")
    guardar(trans[["id_transaccion", "id_cuenta", "id_cliente", "sexo_cliente", "edad_cliente", "id_distrito",
                   "nombre_distrito", "region", "fecha", "anio", "mes", "dia", "tipo_transaccion",
                   "tipo_operacion_traducido", "canal", "operation", "k_symbol", "bank", "account",
                   "monto_transaccion", "saldo_cuenta"]], "df_transacciones.csv.gz", comprimir=True)

    cn.close()
    rem.close()
    print(f"Listo en {time.time() - t0:.1f} s. Siguiente paso: python scripts/33_completitud_datos.py")


if __name__ == "__main__":
    main()
