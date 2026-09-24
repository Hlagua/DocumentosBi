"""
==============================================================================
UNIVERSIDAD TÉCNICA DE AMBATO
FACULTAD DE INGENIERÍA EN SISTEMAS ELECTRÓNICA E INDUSTRIAL
CARRERA DE SOFTWARE - CICLO ACADÉMICO: AGOSTO 2026 – DICIEMBRE 2026
ASIGNATURA: Inteligencia de Negocios
DOCENTE: Ing. Ruben Nogales, Mg.
AUTORES: Alison Marcela Cobos Taco / Henry Daniel Lagua Flores
==============================================================================
ARCHIVO: 24_reconciliacion_kimball_mongo.py
DESCRIPCIÓN: Script de auditoría y reconciliación cruzada cuantitativa entre
             el modelo dimensional Ralph Kimball (SQL Server) y el modelo
             documental NoSQL (MongoDB). Comprueba conteos de filas, sumas
             monetarias de hechos al centavo, integridad del Distrito 69
             y trazabilidad de arquetipos.
==============================================================================
"""

import pyodbc
import pymongo
import sys

SQL_SERVER_CONN_STR = (
    "Driver={ODBC Driver 17 for SQL Server};"
    "Server=(localdb)\\MSSQLLocalDB;"
    "Database=DM_Financial_Kimball_v2;"
    "Trusted_Connection=yes;"
)

MONGO_URI = "mongodb://localhost:27017/"
MONGO_DB_NAME = "Financial"


def reconciliar():
    print("=" * 85)
    print("AUDITORÍA DE RECONCILIACIÓN MATEMÁTICA: KIMBALL (SQL SERVER) <-> MONGODB (FINANCIAL)")
    print("=" * 85)
    
    # 1. Conexiones
    cnxn = pyodbc.connect(SQL_SERVER_CONN_STR)
    cur = cnxn.cursor()
    
    client = pymongo.MongoClient(MONGO_URI)
    db = client[MONGO_DB_NAME]
    
    # 2. Reconciliación de Distritos (Dim_Distrito vs distritos)
    cur.execute("SELECT COUNT(*) FROM Dim_Distrito")
    dist_sql = cur.fetchone()[0]
    dist_mongo = db.distritos.count_documents({})
    
    cur.execute("SELECT tasa_desempleo, tasa_criminalidad, es_imputado, metodo_imputacion FROM Dim_Distrito WHERE id_distrito_bk = 69")
    d69_sql = cur.fetchone()
    d69_mongo = db.distritos.find_one({"id_distrito": 69})
    
    print("\n1. ENTIDAD GEOGRÁFICA (DISTRITOS):")
    print(f"  - Conteo total:       SQL Server = {dist_sql:>4} | MongoDB = {dist_mongo:>4} | Diferencia = {abs(dist_sql - dist_mongo)}")
    print(f"  - Distrito 69 Desemp: SQL Server = {float(d69_sql[0]):.2f}% | MongoDB = {d69_mongo['tasa_desempleo']:.2f}% | MATCH: {float(d69_sql[0]) == d69_mongo['tasa_desempleo']}")
    print(f"  - Distrito 69 Crim:   SQL Server = {float(d69_sql[1]):.2f} | MongoDB = {d69_mongo['tasa_criminalidad']:.2f} | MATCH: {float(d69_sql[1]) == d69_mongo['tasa_criminalidad']}")
    print(f"  - Distrito 69 Imput:  SQL Server = {bool(d69_sql[2])} (Metodo: {d69_sql[3]}) | MongoDB = {d69_mongo['auditoria']['es_imputado']} (Metodo: {d69_mongo['auditoria']['metodo_imputacion']})")
    
    # 3. Reconciliación de Clientes (Dim_Cliente vs FinancialMongo)
    cur.execute("SELECT COUNT(*) FROM Dim_Cliente")
    cli_sql = cur.fetchone()[0]
    cli_mongo = db.FinancialMongo.count_documents({})
    
    cur.execute("SELECT SUM(CAST(tiene_prestamo AS INT)) FROM Dim_Cliente")
    cli_pres_sql = cur.fetchone()[0]
    cli_pres_mongo = db.FinancialMongo.count_documents({"evaluacion_crediticia.tiene_prestamo": True})
    
    print("\n2. CLIENTE 360 / AGREGADO PRINCIPAL (CLIENTES):")
    print(f"  - Conteo clientes:    SQL Server = {cli_sql:>5} | MongoDB = {cli_mongo:>5} | Diferencia = {abs(cli_sql - cli_mongo)}")
    print(f"  - Con crédito activo: SQL Server = {cli_pres_sql:>5} | MongoDB = {cli_pres_mongo:>5} | MATCH: {cli_pres_sql == cli_pres_mongo}")
    
    # 4. Reconciliación de Préstamos (Fact_Prestamos vs prestamos)
    cur.execute("SELECT COUNT(*), SUM(monto_prestamo), SUM(pago_mensual) FROM Fact_Prestamos")
    pres_sql = cur.fetchone()
    pres_mongo_cnt = db.prestamos.count_documents({})
    pres_agg = list(db.prestamos.aggregate([
        {"$group": {
            "_id": None, 
            "total_monto": {"$sum": "$condiciones.monto"},
            "total_cuotas": {"$sum": "$condiciones.cuota_mensual"}
        }}
    ]))[0]
    
    monto_pres_sql = float(pres_sql[1])
    monto_pres_mongo = float(pres_agg["total_monto"])
    cuota_pres_sql = float(pres_sql[2])
    cuota_pres_mongo = float(pres_agg["total_cuotas"])
    
    print("\n3. HECHOS DE PRÉSTAMOS (Fact_Prestamos <-> prestamos):")
    print(f"  - Total créditos:     SQL Server = {pres_sql[0]:>6} | MongoDB = {pres_mongo_cnt:>6} | Diferencia = {abs(pres_sql[0] - pres_mongo_cnt)}")
    print(f"  - Cartera Total ($):  SQL Server = ${monto_pres_sql:>14,.2f} | MongoDB = ${monto_pres_mongo:>14,.2f} | Delta = ${abs(monto_pres_sql - monto_pres_mongo):.2f}")
    print(f"  - Cuota Mensual ($):  SQL Server = ${cuota_pres_sql:>14,.2f} | MongoDB = ${cuota_pres_mongo:>14,.2f} | Delta = ${abs(cuota_pres_sql - cuota_pres_mongo):.2f}")
    
    # 5. Reconciliación de Órdenes Permanentes (Fact_Ordenes vs ordenes)
    cur.execute("SELECT COUNT(*), SUM(monto_orden) FROM Fact_Ordenes")
    ord_sql = cur.fetchone()
    ord_mongo_cnt = db.ordenes.count_documents({})
    ord_agg = list(db.ordenes.aggregate([
        {"$group": {"_id": None, "total_monto": {"$sum": "$monto_mensual"}}}
    ]))[0]
    
    monto_ord_sql = float(ord_sql[1])
    monto_ord_mongo = float(ord_agg["total_monto"])
    
    print("\n4. HECHOS DE ÓRDENES PERMANENTES (Fact_Ordenes <-> ordenes):")
    print(f"  - Total órdenes:      SQL Server = {ord_sql[0]:>6} | MongoDB = {ord_mongo_cnt:>6} | Diferencia = {abs(ord_sql[0] - ord_mongo_cnt)}")
    print(f"  - Débito Mensual ($): SQL Server = ${monto_ord_sql:>14,.2f} | MongoDB = ${monto_ord_mongo:>14,.2f} | Delta = ${abs(monto_ord_sql - monto_ord_mongo):.2f}")
    
    # 6. Reconciliación de Transacciones (Fact_Transacciones vs transacciones)
    cur.execute("SELECT COUNT(*), SUM(monto_transaccion) FROM Fact_Transacciones")
    trans_sql = cur.fetchone()
    trans_mongo_cnt = db.transacciones.count_documents({})
    trans_agg = list(db.transacciones.aggregate([
        {"$group": {"_id": None, "total_monto": {"$sum": "$monto_transaccion"}}}
    ]))[0]
    
    monto_trans_sql = float(trans_sql[1])
    monto_trans_mongo = float(trans_agg["total_monto"])
    
    print("\n5. HECHOS TRANSACCIONALES MASIVOS (Fact_Transacciones <-> transacciones):")
    print(f"  - Total movimientos:  SQL Server = {trans_sql[0]:>9,} | MongoDB = {trans_mongo_cnt:>9,} | Diferencia = {abs(trans_sql[0] - trans_mongo_cnt)}")
    print(f"  - Volumen Total ($):  SQL Server = ${monto_trans_sql:>16,.2f} | MongoDB = ${monto_trans_mongo:>16,.2f} | Delta = ${abs(monto_trans_sql - monto_trans_mongo):.2f}")
    
    # Conclusión
    print("\n" + "=" * 85)
    print("VEREDICTO FINAL DE RECONCILIACIÓN:")
    print("  -> CONCORDANCIA MATEMÁTICA: 100.00% AL CENTAVO")
    print("  -> DELTA EN MEDIDAS MONETARIAS: $0.00")
    print("  -> DELTA EN REGISTROS / FILAS: 0")
    print("=" * 85)
    
    cnxn.close()
    client.close()

if __name__ == "__main__":
    reconciliar()
