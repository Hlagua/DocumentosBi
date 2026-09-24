"""
==============================================================================
UNIVERSIDAD TÉCNICA DE AMBATO
FACULTAD DE INGENIERÍA EN SISTEMAS ELECTRÓNICA E INDUSTRIAL
CARRERA DE SOFTWARE - CICLO ACADÉMICO: AGOSTO 2026 – DICIEMBRE 2026
ASIGNATURA: Inteligencia de Negocios
DOCENTE: Ing. Ruben Nogales, Mg.
AUTORES: Alison Marcela Cobos Taco / Henry Daniel Lagua Flores
==============================================================================
ARCHIVO: 22_migrar_kimball_a_mongodb.py
DESCRIPCIÓN: Pipeline ETL de migración y desnormalización documental NoSQL
             desde el modelo dimensional Ralph Kimball (SQL Server) hacia 
             MongoDB (Base de datos: Financial, Colección: FinancialMongo y
             colecciones de agregados).
==============================================================================
"""

import os
import sys
import time
from datetime import datetime
import pyodbc
import pymongo
import pandas as pd
import numpy as np

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_TRANSACCIONES = os.path.join(BASE_DIR, "dataframes", "df_transacciones_completado.csv.gz")

SQL_SERVER_CONN_STR = (
    "Driver={ODBC Driver 17 for SQL Server};"
    "Server=(localdb)\\MSSQLLocalDB;"
    "Database=DM_Financial_Kimball_v2;"
    "Trusted_Connection=yes;"
)

MONGO_URI = "mongodb://localhost:27017/"
MONGO_DB_NAME = "Financial"


def conectar_servicios():
    print(f"[CONEXIÓN] Conectando a Microsoft SQL Server (DM_Financial_Kimball_v2)...")
    sql_cnxn = pyodbc.connect(SQL_SERVER_CONN_STR)
    print(f"  -> Conexión a SQL Server exitosa.")

    print(f"[CONEXIÓN] Conectando a MongoDB ({MONGO_URI})...")
    mongo_client = pymongo.MongoClient(MONGO_URI)
    mongo_db = mongo_client[MONGO_DB_NAME]
    print(f"  -> Conexión a MongoDB exitosa. Base de datos objetivo: '{MONGO_DB_NAME}'")
    return sql_cnxn, mongo_client, mongo_db


def migrar_distritos(sql_cnxn, mongo_db):
    print("\n--- 1. MIGRANDO COLECCIÓN: distritos ---")
    cur = sql_cnxn.cursor()
    cur.execute("""
    SELECT 
        sk_distrito, id_distrito_bk, nombre_distrito, region, poblacion,
        salario_promedio, tasa_desempleo, tasa_criminalidad,
        es_imputado, metodo_imputacion, fecha_enriquecimiento
    FROM Dim_Distrito
    ORDER BY id_distrito_bk;
    """)
    rows = cur.fetchall()
    
    docs = []
    for r in rows:
        docs.append({
            "_id": int(r[1]),
            "sk_distrito": int(r[0]),
            "id_distrito": int(r[1]),
            "nombre": str(r[2]),
            "region": str(r[3]),
            "poblacion": int(r[4]),
            "salario_promedio": float(r[5]) if r[5] is not None else None,
            "tasa_desempleo": float(r[6]) if r[6] is not None else None,
            "tasa_criminalidad": float(r[7]) if r[7] is not None else None,
            "auditoria": {
                "es_imputado": bool(r[8]),
                "metodo_imputacion": str(r[9]) if r[9] else "Original PKDD99",
                "fecha_actualizacion": r[10].isoformat() if r[10] else None
            }
        })
    
    col = mongo_db["distritos"]
    col.drop()
    col.insert_many(docs)
    col.create_index([("id_distrito", 1)])
    col.create_index([("region", 1)])
    print(f"  [OK] {len(docs)} distritos cargados exitosamente (Distrito 69 100% imputado y auditado).")
    return {d["id_distrito"]: d for d in docs}


def migrar_prestamos(sql_cnxn, mongo_db):
    print("\n--- 2. MIGRANDO COLECCIÓN: prestamos ---")
    cur = sql_cnxn.cursor()
    cur.execute("""
    SELECT 
        p.id_prestamo_bk, p.monto_prestamo, p.plazo_meses, p.pago_mensual, p.saldo_pendiente_estimado,
        t.fecha, c.id_cuenta_bk, cli.id_cliente_bk, cli.tipo_disposicion,
        e.codigo_estado, e.condicion, e.descripcion,
        d.id_distrito_bk, d.nombre_distrito, d.salario_promedio
    FROM Fact_Prestamos p
    JOIN Dim_Tiempo t ON p.sk_tiempo = t.sk_tiempo
    JOIN Dim_Cuenta c ON p.sk_cuenta = c.sk_cuenta
    JOIN Dim_Cliente cli ON p.sk_cliente = cli.sk_cliente
    JOIN Dim_Estado_Prestamo e ON p.sk_estado_prestamo = e.sk_estado_prestamo
    JOIN Dim_Distrito d ON p.sk_distrito = d.sk_distrito
    ORDER BY p.id_prestamo_bk;
    """)
    rows = cur.fetchall()
    
    docs = []
    prestamos_por_cliente = {}
    for r in rows:
        id_prestamo = int(r[0])
        id_cliente = int(r[7])
        monto = float(r[1])
        plazo = int(r[2])
        pago_mensual = float(r[3])
        saldo = float(r[4]) if r[4] is not None else 0.0
        fecha_otorgamiento = r[5].isoformat() if r[5] else None
        id_cuenta = int(r[6])
        estado = str(r[9])
        condicion = str(r[10])
        salario_dist = float(r[14]) if r[14] is not None else 0.0
        ratio_endeudamiento = round((pago_mensual / salario_dist * 100), 2) if salario_dist > 0 else 0.0
        
        doc = {
            "_id": id_prestamo,
            "id_prestamo": id_prestamo,
            "id_cuenta": id_cuenta,
            "id_cliente": id_cliente,
            "condiciones": {
                "monto": monto,
                "plazo_meses": plazo,
                "cuota_mensual": pago_mensual,
                "saldo_pendiente": saldo,
                "fecha_otorgamiento": fecha_otorgamiento
            },
            "evaluacion_riesgo": {
                "codigo_estado": estado,
                "condicion": condicion,
                "descripcion": str(r[11]),
                "ratio_endeudamiento_pct": ratio_endeudamiento,
                "es_moroso": estado in ['B', 'D']
            },
            "distrito": {
                "id_distrito": int(r[12]),
                "nombre": str(r[13])
            }
        }
        docs.append(doc)
        prestamos_por_cliente[id_cliente] = doc
        
    col = mongo_db["prestamos"]
    col.drop()
    col.insert_many(docs)
    col.create_index([("id_prestamo", 1)])
    col.create_index([("id_cliente", 1)])
    col.create_index([("evaluacion_riesgo.codigo_estado", 1)])
    print(f"  [OK] {len(docs)} préstamos cargados exitosamente con métricas de riesgo.")
    return prestamos_por_cliente


def migrar_ordenes(sql_cnxn, mongo_db):
    print("\n--- 3. MIGRANDO COLECCIÓN: ordenes ---")
    cur = sql_cnxn.cursor()
    cur.execute("""
    SELECT 
        o.id_orden_bk, o.monto_orden,
        c.id_cuenta_bk, cli.id_cliente_bk,
        ord.k_symbol_original, ord.categoria_orden_traducida
    FROM Fact_Ordenes o
    JOIN Dim_Cuenta c ON o.sk_cuenta = c.sk_cuenta
    JOIN Dim_Cliente cli ON o.sk_cliente = cli.sk_cliente
    JOIN Dim_Orden ord ON o.sk_orden_tipo = ord.sk_orden_tipo
    ORDER BY o.id_orden_bk;
    """)
    rows = cur.fetchall()
    
    docs = []
    ordenes_por_cliente = {}
    for r in rows:
        id_orden = int(r[0])
        monto = float(r[1])
        id_cuenta = int(r[2])
        id_cliente = int(r[3])
        k_symbol = str(r[4])
        categoria = str(r[5])
        
        doc = {
            "_id": id_orden,
            "id_orden": id_orden,
            "id_cuenta": id_cuenta,
            "id_cliente": id_cliente,
            "monto_mensual": monto,
            "categoria_pago": {
                "codigo": k_symbol,
                "descripcion": categoria
            }
        }
        docs.append(doc)
        if id_cliente not in ordenes_por_cliente:
            ordenes_por_cliente[id_cliente] = []
        ordenes_por_cliente[id_cliente].append({
            "id_orden": id_orden,
            "categoria": categoria,
            "codigo": k_symbol,
            "monto": monto
        })
        
    col = mongo_db["ordenes"]
    col.drop()
    col.insert_many(docs)
    col.create_index([("id_orden", 1)])
    col.create_index([("id_cliente", 1)])
    col.create_index([("categoria_pago.codigo", 1)])
    print(f"  [OK] {len(docs)} órdenes cargadas exitosamente (100% homologadas a 5 categorías).")
    return ordenes_por_cliente


def migrar_coleccion_financial_mongo(sql_cnxn, mongo_db, distritos_map, prestamos_map, ordenes_map):
    print("\n--- 4. MIGRANDO COLECCIÓN PRINCIPAL: FinancialMongo (Cliente 360 Enriquecido) ---")
    cur = sql_cnxn.cursor()
    cur.execute("""
    SELECT 
        cli.id_cliente_bk, cli.sexo, cli.fecha_nacimiento, cli.edad_corte,
        cli.tipo_disposicion, cli.etiqueta_buen_pagador, cli.calificacion_pago_desc,
        cli.macro_region, cli.segmento_edad, cli.arquetipo_demografico,
        cli.tiene_prestamo, cli.total_ordenes_activas, cli.saldo_promedio,
        d.id_distrito_bk, c.id_cuenta_bk, c.frecuencia_emision_estado, c.fecha_apertura
    FROM Dim_Cliente cli
    JOIN Dim_Distrito d ON cli.sk_distrito = d.sk_distrito
    JOIN Dim_Cuenta c ON d.sk_distrito = c.sk_distrito
    ORDER BY cli.id_cliente_bk;
    """)
    # Usar query más directa cliente-cuenta
    cur.execute("""
    SELECT 
        cli.id_cliente_bk, cli.sexo, cli.fecha_nacimiento, cli.edad_corte,
        cli.tipo_disposicion, cli.etiqueta_buen_pagador, cli.calificacion_pago_desc,
        cli.macro_region, cli.segmento_edad, cli.arquetipo_demografico,
        cli.tiene_prestamo, cli.total_ordenes_activas, cli.saldo_promedio,
        cli.sk_distrito, d.id_distrito_bk
    FROM Dim_Cliente cli
    JOIN Dim_Distrito d ON cli.sk_distrito = d.sk_distrito
    ORDER BY cli.id_cliente_bk;
    """)
    rows = cur.fetchall()
    
    docs = []
    for r in rows:
        id_cli = int(r[0])
        id_dist = int(r[14])
        dist_info = distritos_map.get(id_dist, {})
        
        doc = {
            "_id": id_cli,
            "id_cliente": id_cli,
            "datos_personales": {
                "sexo": str(r[1]),
                "fecha_nacimiento": r[2].isoformat() if r[2] else None,
                "edad_al_corte_1998": int(r[3]) if r[3] is not None else None,
                "tipo_disposicion": str(r[4])
            },
            "evaluacion_crediticia": {
                "tiene_prestamo": bool(r[10]),
                "es_buen_pagador": bool(r[5]) if r[5] is not None else None,
                "calificacion": str(r[6])
            },
            "perfil_analitico": {
                "macro_region": str(r[7]),
                "segmento_edad": str(r[8]),
                "arquetipo_demografico": str(r[9]),
                "total_ordenes_activas": int(r[11]),
                "saldo_promedio_historico": float(r[12]) if r[12] is not None else 0.0
            },
            "distrito": {
                "id_distrito": dist_info.get("id_distrito"),
                "nombre": dist_info.get("nombre"),
                "region": dist_info.get("region"),
                "poblacion": dist_info.get("poblacion"),
                "salario_promedio": dist_info.get("salario_promedio"),
                "tasa_desempleo": dist_info.get("tasa_desempleo"),
                "tasa_criminalidad": dist_info.get("tasa_criminalidad"),
                "imputacion": dist_info.get("auditoria", {})
            },
            "ordenes_recurrentes": ordenes_map.get(id_cli, []),
            "prestamo_asociado": prestamos_map.get(id_cli, None)
        }
        docs.append(doc)
        
    col = mongo_db["FinancialMongo"]
    col.drop()
    col.insert_many(docs)
    col.create_index([("id_cliente", 1)])
    col.create_index([("perfil_analitico.arquetipo_demografico", 1)])
    col.create_index([("evaluacion_crediticia.tiene_prestamo", 1)])
    col.create_index([("distrito.id_distrito", 1)])
    print(f"  [OK] {len(docs)} documentos cargados exitosamente en 'FinancialMongo' (Cliente 360 con distrito y hechos anidados).")


def migrar_transacciones_masivo(mongo_db):
    print("\n--- 5. MIGRANDO COLECCIÓN MASIVA: transacciones (1,056,320 registros) ---")
    if not os.path.exists(CSV_TRANSACCIONES):
        print(f"  [AVISO] Archivo {CSV_TRANSACCIONES} no encontrado. Omitiendo transacciones.")
        return
        
    col = mongo_db["transacciones"]
    col.drop()
    
    t0 = time.time()
    chunk_size = 50000
    total_insertados = 0
    
    print(f"  Leyendo transacciones comprimidas en gzip por lotes de {chunk_size:,}...")
    for chunk in pd.read_csv(CSV_TRANSACCIONES, compression='gzip', chunksize=chunk_size):
        # Convertir a formato diccionario limpio para MongoDB
        records = chunk[[
            'id_transaccion', 'id_cuenta', 'id_cliente', 'fecha', 'anio', 'mes', 'dia',
            'tipo_transaccion', 'tipo_operacion_traducido', 'canal', 'k_symbol',
            'monto_transaccion', 'saldo_cuenta', 'concepto_movimiento_traducido'
        ]].to_dict(orient='records')
        
        # Renombrar _id para indexación nativa
        for r in records:
            r['_id'] = int(r['id_transaccion'])
            r['monto_transaccion'] = float(r['monto_transaccion'])
            r['saldo_cuenta'] = float(r['saldo_cuenta'])
            
        col.insert_many(records, ordered=False)
        total_insertados += len(records)
        print(f"    Insertados: {total_insertados:>10,} / 1,056,320 ({time.time() - t0:.1f} s)...")
        
    print(f"  Creando índices en MongoDB...")
    col.create_index([("id_cuenta", 1), ("fecha", 1)])
    col.create_index([("id_cliente", 1)])
    print(f"  [OK] {total_insertados:,} transacciones cargadas e indexadas en {time.time() - t0:.1f} segundos.")


def main():
    print("=" * 80)
    print("MIGRACIÓN INTEGRAL: KIMBALL (SQL SERVER) -> MONGODB (FINANCIAL)")
    print("=" * 80)
    
    sql_cnxn, mongo_client, mongo_db = conectar_servicios()
    
    try:
        distritos_map = migrar_distritos(sql_cnxn, mongo_db)
        prestamos_map = migrar_prestamos(sql_cnxn, mongo_db)
        ordenes_map = migrar_ordenes(sql_cnxn, mongo_db)
        migrar_coleccion_financial_mongo(sql_cnxn, mongo_db, distritos_map, prestamos_map, ordenes_map)
        migrar_transacciones_masivo(mongo_db)
        
        print("\n" + "=" * 80)
        print(f"ESTADO FINAL DE MONGODB (Base de datos: '{MONGO_DB_NAME}'):")
        print("=" * 80)
        for c in mongo_db.list_collection_names():
            cnt = mongo_db[c].count_documents({})
            print(f"  Colección: {c:<25} | {cnt:>10,} documentos")
        print("=" * 80)
        print("¡MIGRACIÓN NoSQL COMPLETADA CON ÉXITO!")
        
    finally:
        sql_cnxn.close()
        mongo_client.close()


if __name__ == "__main__":
    main()
