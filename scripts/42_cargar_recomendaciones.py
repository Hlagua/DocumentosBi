"""
==============================================================================
UNIVERSIDAD TÉCNICA DE AMBATO - Inteligencia de Negocios
AUTORES: Alison Marcela Cobos Taco / Henry Daniel Lagua Flores
==============================================================================
ARCHIVO: 42_cargar_recomendaciones.py
DESCRIPCIÓN: Carga las recomendaciones del Informe 04 (dataframes/rs_recomendaciones.csv,
             script 40) en los dos motores para que el dashboard las muestre en la
             ficha Cliente 360 (Guía 07 v4):
               * SQL Server: tabla Recomendacion_Cuenta (una fila por cuenta).
               * MongoDB: colección recomendaciones y campo "recomendaciones" en
                 el documento del titular en FinancialMongo.
             Los nombres de los productos se guardan en español legible.
USO: python scripts/42_cargar_recomendaciones.py
==============================================================================
"""
import os

import pandas as pd
import pymongo
import pyodbc

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KIMBALL = ("Driver={ODBC Driver 17 for SQL Server};Server=(localdb)\\MSSQLLocalDB;"
           "Database=DM_Financial_Kimball_v2;Trusted_Connection=yes;")
NOMBRES = {"SERVICIOS_HOGAR": "Domiciliar servicios del hogar", "TRANSF_SALIENTE": "Transferencias a otros bancos",
           "INGRESO_TRANSF": "Recibir ingresos por transferencia", "RETIRO_TARJETA": "Tarjeta de débito",
           "PENSION": "Domiciliar la pensión", "PRESTAMO": "Préstamo", "SEGURO": "Seguro domiciliado",
           "LEASING": "Leasing"}


def num(v):
    return None if pd.isna(v) else float(v)


def main():
    r = pd.read_csv(os.path.join(BASE_DIR, "dataframes", "rs_recomendaciones.csv"))
    modelo = pd.read_json(os.path.join(BASE_DIR, "metricas_recomendadores.json"), typ="series")["perfiles_contenido"]["modelo_elegido"]["nombre"]
    for c in ["recomendacion_1", "recomendacion_2", "recomendacion_3"]:
        r[c] = r[c].map(NOMBRES).astype(object).where(r[c].notna(), None)   # sin recomendación -> NULL, no NaN

    # ---------------- SQL Server ----------------
    cn = pyodbc.connect(KIMBALL, timeout=120)
    cur = cn.cursor()
    cur.execute("""IF OBJECT_ID('Recomendacion_Cuenta') IS NULL
        CREATE TABLE Recomendacion_Cuenta (
            sk_cuenta INT NOT NULL PRIMARY KEY, sk_cliente INT NOT NULL, modelo VARCHAR(60) NOT NULL,
            recomendacion_1 VARCHAR(40) NULL, recomendacion_2 VARCHAR(40) NULL, recomendacion_3 VARCHAR(40) NULL,
            prestamo_cuota_maxima DECIMAL(12,2) NULL, prestamo_monto_maximo_36m DECIMAL(12,2) NULL,
            CONSTRAINT FK_Recomendacion_Cuenta FOREIGN KEY (sk_cuenta) REFERENCES Dim_Cuenta(sk_cuenta),
            CONSTRAINT FK_Recomendacion_Cliente FOREIGN KEY (sk_cliente) REFERENCES Dim_Cliente(sk_cliente))""")
    cur.execute("DELETE FROM Recomendacion_Cuenta")
    sk_cta = {a: b for a, b in cur.execute("SELECT id_cuenta_bk, sk_cuenta FROM Dim_Cuenta")}
    sk_cli = {a: b for a, b in cur.execute("SELECT id_cliente_bk, sk_cliente FROM Dim_Cliente")}
    # Sin fast_executemany: las columnas decimales empiezan con nulos y el modo rápido infiere mal su tipo
    cur.executemany("INSERT INTO Recomendacion_Cuenta VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    [(sk_cta[int(x.id_cuenta)], sk_cli[int(x.id_cliente)], modelo, x.recomendacion_1, x.recomendacion_2,
                      x.recomendacion_3, num(x.prestamo_cuota_maxima), num(x.prestamo_monto_maximo_36m)) for x in r.itertuples()])
    cn.commit()
    n_sql = cur.execute("SELECT COUNT(*) FROM Recomendacion_Cuenta").fetchone()[0]
    con_prestamo = cur.execute("SELECT COUNT(*) FROM Recomendacion_Cuenta WHERE prestamo_cuota_maxima IS NOT NULL").fetchone()[0]
    cn.close()

    # ---------------- MongoDB ----------------
    db = pymongo.MongoClient("mongodb://localhost:27017/")["Financial"]
    docs = [{"_id": int(x.id_cuenta), "id_cuenta": int(x.id_cuenta), "id_cliente": int(x.id_cliente), "modelo": modelo,
             "recomendaciones": [v for v in (x.recomendacion_1, x.recomendacion_2, x.recomendacion_3) if isinstance(v, str)],
             "prestamo_cuota_maxima": num(x.prestamo_cuota_maxima),
             "prestamo_monto_maximo_36m": num(x.prestamo_monto_maximo_36m)} for x in r.itertuples()]
    db.drop_collection("recomendaciones")
    db.recomendaciones.insert_many(docs)
    db.recomendaciones.create_index("id_cliente")
    # El campo en FinancialMongo se agrega sin cambiar el validador (no es obligatorio)
    for d in docs:
        db.FinancialMongo.update_one({"_id": d["id_cliente"]}, {"$set": {"recomendaciones": {
            "modelo": modelo, "productos": d["recomendaciones"], "prestamo_cuota_maxima": d["prestamo_cuota_maxima"],
            "prestamo_monto_maximo_36m": d["prestamo_monto_maximo_36m"]}}})
    n_mongo = db.recomendaciones.count_documents({})
    n_fm = db.FinancialMongo.count_documents({"recomendaciones": {"$exists": True}})

    print(f"SQL Server Recomendacion_Cuenta: {n_sql} filas ({con_prestamo} con préstamo ofrecido)")
    print(f"MongoDB recomendaciones: {n_mongo} documentos · FinancialMongo con recomendaciones: {n_fm}")
    assert n_sql == n_mongo == n_fm == len(r), "Los conteos no coinciden"
    print("OK: los dos motores tienen las mismas recomendaciones.")


if __name__ == "__main__":
    main()
