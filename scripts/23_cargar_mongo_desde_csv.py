"""
==============================================================================
Script 23: Carga directa a MongoDB desde archivos CSV locales (Sin requerir SQL Server)
==============================================================================
Uso: Permite a cualquier compañero de equipo restaurar la base de datos MongoDB
     completa en su máquina local ejecutando solo este script en Python.
"""
import os
import time
import pandas as pd
import pymongo

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_CLIENTE = os.path.join(BASE_DIR, "dataframes", "df_cliente_consolidado_clean.csv")
CSV_ORDENES = os.path.join(BASE_DIR, "dataframes", "df_ordenes_clean.csv")
CSV_PRESTAMOS = os.path.join(BASE_DIR, "dataframes", "df_prestamos.csv")
CSV_TRANS = os.path.join(BASE_DIR, "dataframes", "df_transacciones_completado.csv.gz")

MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "Financial"

def main():
    print("=" * 80)
    print("RESTAURACIÓN RÁPIDA DE MONGODB DESDE CSVs (COMPAÑEROS DE EQUIPO)")
    print("=" * 80)
    
    client = pymongo.MongoClient(MONGO_URI)
    db = client[DB_NAME]
    
    # 1. Distritos
    print("\n1. Cargando distritos...")
    df_cli = pd.read_csv(CSV_CLIENTE)
    cols_dist = ['id_distrito', 'nombre_distrito', 'region', 'poblacion', 'salario_promedio', 'tasa_desempleo', 'tasa_criminalidad']
    dist_unique = df_cli[cols_dist].drop_duplicates('id_distrito').to_dict('records')
    for d in dist_unique:
        d['_id'] = int(d['id_distrito'])
        d['es_imputado'] = (d['id_distrito'] == 69)
        d['metodo'] = 'K-Means Clustered' if d['id_distrito'] == 69 else 'Original PKDD99'
    db.distritos.drop()
    db.distritos.insert_many(dist_unique)
    print(f"  [OK] {len(dist_unique)} distritos cargados.")
    
    # 2. Prestamos
    print("\n2. Cargando prestamos...")
    df_pres = pd.read_csv(CSV_PRESTAMOS)
    pres_docs = df_pres.to_dict('records')
    for p in pres_docs:
        p['_id'] = int(p['id_prestamo'])
    db.prestamos.drop()
    db.prestamos.insert_many(pres_docs)
    print(f"  [OK] {len(pres_docs)} préstamos cargados.")
    
    # 3. Ordenes
    print("\n3. Cargando ordenes...")
    df_ord = pd.read_csv(CSV_ORDENES)
    ord_docs = df_ord.to_dict('records')
    for o in ord_docs:
        o['_id'] = int(o['id_orden'])
    db.ordenes.drop()
    db.ordenes.insert_many(ord_docs)
    print(f"  [OK] {len(ord_docs)} órdenes cargadas.")
    
    # 4. FinancialMongo (Cliente 360)
    print("\n4. Cargando FinancialMongo (Cliente 360)...")
    cli_docs = df_cli.to_dict('records')
    for c in cli_docs:
        c['_id'] = int(c['id_cliente'])
    db.FinancialMongo.drop()
    db.FinancialMongo.insert_many(cli_docs)
    print(f"  [OK] {len(cli_docs)} clientes consolidados cargados en FinancialMongo.")
    
    # 5. Transacciones
    if os.path.exists(CSV_TRANS):
        print("\n5. Cargando transacciones masivas (1,056,320 registros)...")
        db.transacciones.drop()
        t0 = time.time()
        tot = 0
        for chunk in pd.read_csv(CSV_TRANS, compression='gzip', chunksize=50000):
            recs = chunk.to_dict('records')
            for r in recs:
                r['_id'] = int(r['id_transaccion'])
            db.transacciones.insert_many(recs, ordered=False)
            tot += len(recs)
            print(f"    Insertados: {tot:>10,} / 1,056,320...")
        db.transacciones.create_index([("id_cuenta", 1), ("fecha", 1)])
        print(f"  [OK] Transacciones cargadas en {time.time() - t0:.1f} s.")
        
    print("\n" + "=" * 80)
    print(f"Base de datos '{DB_NAME}' restaurada exitosamente para tu compañero.")
    print("=" * 80)

if __name__ == "__main__":
    main()
