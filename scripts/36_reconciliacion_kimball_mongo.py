"""
==============================================================================
UNIVERSIDAD TÉCNICA DE AMBATO - Inteligencia de Negocios
AUTORES: Alison Marcela Cobos Taco / Henry Daniel Lagua Flores
==============================================================================
ARCHIVO: 36_reconciliacion_kimball_mongo.py
DESCRIPCIÓN: Reconciliación Kimball (SQL Server) <-> MongoDB después de la
             migración del script 35. A diferencia del script 24, no compara
             solo totales: compara también los desgloses que usa el dashboard
             (región, categoría de operación, concepto, estado, banda de
             capacidad, clientes) y ejecuta el conector de Power BI
             (script 26) para verificar lo que vería el tablero de Mongo.
             Resultado: metricas_reconciliacion_kimball_mongo.json y filas en
             Auditoria_Carga (id_ejecucion con prefijo 'M').
USO: python scripts/36_reconciliacion_kimball_mongo.py
==============================================================================
"""
import contextlib
import io
import json
import os
import runpy
import time
from datetime import datetime

import pymongo
import pyodbc

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SALIDA_JSON = os.path.join(BASE_DIR, "metricas_reconciliacion_kimball_mongo.json")
KIMBALL = ("Driver={ODBC Driver 17 for SQL Server};Server=(localdb)\\MSSQLLocalDB;"
           "Database=DM_Financial_Kimball_v2;Trusted_Connection=yes;")
ID_EJECUCION = "M" + datetime.now().strftime("%Y%m%d_%H%M%S")
CORTE = "t.anio = 1998 AND t.mes = 12"


def redondear(d):
    return {str(k): (round(float(v), 2) if isinstance(v, float) or hasattr(v, "as_tuple") else v) for k, v in sorted(d.items())}


def main():
    t0 = time.time()
    print("=" * 78 + "\nRECONCILIACIÓN KIMBALL <-> MONGODB (totales y desgloses)\n" + "=" * 78)
    cn = pyodbc.connect(KIMBALL, timeout=300)
    cur = cn.cursor()
    sql = lambda s: {r[0]: r[1] for r in cur.execute(s).fetchall()}
    uno = lambda s: cur.execute(s).fetchone()[0]
    db = pymongo.MongoClient("mongodb://localhost:27017/")["Financial"]
    agg = lambda col, pipe: {r["_id"]: r["v"] for r in db[col].aggregate(pipe, allowDiskUse=True)}
    region = {d["_id"]: d["region"] for d in db.distritos.find({}, {"region": 1})}
    por_region = lambda d: {k: sum(v for i, v in d.items() if region[i] == k) for k in sorted(set(region.values()))}
    pruebas = []

    def comparar(prueba, kimball, mongo):
        if isinstance(kimball, dict):
            # Un GROUP BY de SQL omite los grupos sin filas (p. ej., north Bohemia con 0 préstamos en mora): cuentan como 0
            claves = set(kimball) | set(mongo)
            kimball, mongo = {k: kimball.get(k, 0) for k in claves}, {k: mongo.get(k, 0) for k in claves}
        ok = redondear(kimball) == redondear(mongo) if isinstance(kimball, dict) else round(float(kimball), 2) == round(float(mongo), 2)
        pruebas.append({"prueba": prueba, "kimball": str(redondear(kimball) if isinstance(kimball, dict) else kimball),
                        "mongodb": str(redondear(mongo) if isinstance(mongo, dict) else mongo), "resultado": "OK" if ok else "FALLA"})
        print(f"  [{'OK' if ok else 'FALLA':<5}] {prueba}")

    print("\n1. Conteos")
    for tabla, col in [("Dim_Distrito", "distritos"), ("Fact_Prestamos", "prestamos"), ("Fact_Ordenes", "ordenes"),
                       ("Dim_Cliente", "FinancialMongo"), ("Fact_Transacciones", "transacciones"),
                       ("Fact_Saldo_Cuenta_Mensual", "saldos_mensuales")]:
        comparar(f"{tabla} = {col}", uno(f"SELECT COUNT(*) FROM {tabla}"), db[col].count_documents({}))

    print("\n2. Totales monetarios")
    comparar("Cartera total", uno("SELECT SUM(monto_prestamo) FROM Fact_Prestamos"),
             agg("prestamos", [{"$group": {"_id": 1, "v": {"$sum": "$condiciones.monto"}}}])[1])
    comparar("Cuotas mensuales", uno("SELECT SUM(pago_mensual) FROM Fact_Prestamos"),
             agg("prestamos", [{"$group": {"_id": 1, "v": {"$sum": "$condiciones.cuota_mensual"}}}])[1])
    comparar("Saldo por cobrar estimado", uno("SELECT SUM(saldo_pendiente_estimado) FROM Fact_Prestamos"),
             agg("prestamos", [{"$group": {"_id": 1, "v": {"$sum": "$condiciones.saldo_pendiente_estimado"}}}])[1])
    comparar("Órdenes", uno("SELECT SUM(monto_orden) FROM Fact_Ordenes"),
             agg("ordenes", [{"$group": {"_id": 1, "v": {"$sum": "$monto_mensual"}}}])[1])
    comparar("Transacciones", uno("SELECT SUM(monto_transaccion) FROM Fact_Transacciones"),
             agg("transacciones", [{"$group": {"_id": 1, "v": {"$sum": "$monto_transaccion"}}}])[1])
    comparar("Saldo neto al corte (dic-1998)",
             uno(f"SELECT SUM(s.saldo_fin_mes) FROM Fact_Saldo_Cuenta_Mensual s JOIN Dim_Tiempo t ON t.sk_tiempo = s.sk_mes WHERE {CORTE}"),
             agg("saldos_mensuales", [{"$match": {"anio": 1998, "mes": 12}}, {"$group": {"_id": 1, "v": {"$sum": "$saldo_fin_mes"}}}])[1])

    print("\n3. Desgloses por región (distrito de la cuenta)")
    comparar("Cartera por región", sql("SELECT d.region, SUM(f.monto_prestamo) FROM Fact_Prestamos f JOIN Dim_Distrito d ON d.sk_distrito = f.sk_distrito GROUP BY d.region"),
             por_region(agg("prestamos", [{"$group": {"_id": "$id_distrito", "v": {"$sum": "$condiciones.monto"}}}])))
    comparar("Saldo al corte por región", sql(f"SELECT d.region, SUM(s.saldo_fin_mes) FROM Fact_Saldo_Cuenta_Mensual s JOIN Dim_Tiempo t ON t.sk_tiempo = s.sk_mes JOIN Dim_Distrito d ON d.sk_distrito = s.sk_distrito WHERE {CORTE} GROUP BY d.region"),
             por_region(agg("saldos_mensuales", [{"$match": {"anio": 1998, "mes": 12}}, {"$group": {"_id": "$id_distrito", "v": {"$sum": "$saldo_fin_mes"}}}])))
    comparar("Órdenes por región", sql("SELECT d.region, SUM(f.monto_orden) FROM Fact_Ordenes f JOIN Dim_Distrito d ON d.sk_distrito = f.sk_distrito GROUP BY d.region"),
             por_region(agg("ordenes", [{"$group": {"_id": "$id_distrito", "v": {"$sum": "$monto_mensual"}}}])))
    comparar("Transacciones por región", sql("SELECT d.region, SUM(f.monto_transaccion) FROM Fact_Transacciones f JOIN Dim_Distrito d ON d.sk_distrito = f.sk_distrito GROUP BY d.region"),
             por_region(agg("transacciones", [{"$group": {"_id": "$id_distrito", "v": {"$sum": "$monto_transaccion"}}}])))
    comparar("Préstamos en mora (D) por región", sql("SELECT d.region, COUNT(*) FROM Fact_Prestamos f JOIN Dim_Distrito d ON d.sk_distrito = f.sk_distrito JOIN Dim_Estado_Prestamo e ON e.sk_estado_prestamo = f.sk_estado_prestamo WHERE e.codigo_estado = 'D' GROUP BY d.region"),
             por_region(agg("prestamos", [{"$match": {"evaluacion_riesgo.codigo_estado": "D"}}, {"$group": {"_id": "$id_distrito", "v": {"$sum": 1}}}])))

    print("\n4. Desgloses por categoría, concepto, estado y capacidad")
    comparar("Movimientos por categoría analítica", sql("SELECT o.categoria_analitica, COUNT(*) FROM Fact_Transacciones f JOIN Dim_Operacion o ON o.sk_operacion = f.sk_operacion GROUP BY o.categoria_analitica"),
             agg("transacciones", [{"$group": {"_id": "$tipo_operacion_traducido", "v": {"$sum": 1}}}]))
    comparar("Monto por categoría analítica", sql("SELECT o.categoria_analitica, SUM(f.monto_transaccion) FROM Fact_Transacciones f JOIN Dim_Operacion o ON o.sk_operacion = f.sk_operacion GROUP BY o.categoria_analitica"),
             agg("transacciones", [{"$group": {"_id": "$tipo_operacion_traducido", "v": {"$sum": "$monto_transaccion"}}}]))
    comparar("Movimientos por concepto completado", sql("SELECT c.codigo_concepto, COUNT(*) FROM Fact_Transacciones f JOIN Dim_Concepto_Movimiento c ON c.sk_concepto = f.sk_concepto GROUP BY c.codigo_concepto"),
             agg("transacciones", [{"$group": {"_id": "$concepto.codigo", "v": {"$sum": 1}}}]))
    comparar("Movimientos por método del concepto", sql("SELECT c.metodo_concepto, COUNT(*) FROM Fact_Transacciones f JOIN Dim_Concepto_Movimiento c ON c.sk_concepto = f.sk_concepto GROUP BY c.metodo_concepto"),
             agg("transacciones", [{"$group": {"_id": "$concepto.metodo", "v": {"$sum": 1}}}]))
    comparar("Préstamos por estado", sql("SELECT e.codigo_estado, COUNT(*) FROM Fact_Prestamos f JOIN Dim_Estado_Prestamo e ON e.sk_estado_prestamo = f.sk_estado_prestamo GROUP BY e.codigo_estado"),
             agg("prestamos", [{"$group": {"_id": "$evaluacion_riesgo.codigo_estado", "v": {"$sum": 1}}}]))
    comparar("Préstamos con impago por banda de capacidad", sql("SELECT f.banda_capacidad, SUM(CASE WHEN e.codigo_estado IN ('B','D') THEN 1 ELSE 0 END) FROM Fact_Prestamos f JOIN Dim_Estado_Prestamo e ON e.sk_estado_prestamo = f.sk_estado_prestamo GROUP BY f.banda_capacidad"),
             agg("prestamos", [{"$group": {"_id": "$capacidad_pago.banda_capacidad", "v": {"$sum": {"$cond": ["$evaluacion_riesgo.con_impago", 1, 0]}}}}]))
    comparar("Cuentas en sobregiro al corte", uno(f"SELECT COUNT(*) FROM Fact_Saldo_Cuenta_Mensual s JOIN Dim_Tiempo t ON t.sk_tiempo = s.sk_mes WHERE {CORTE} AND s.en_sobregiro = 1"),
             db.saldos_mensuales.count_documents({"anio": 1998, "mes": 12, "en_sobregiro": True}))

    print("\n5. Clientes y distritos")
    comparar("Clientes por calificación", sql("SELECT calificacion_pago_desc, COUNT(*) FROM Dim_Cliente GROUP BY calificacion_pago_desc"),
             agg("FinancialMongo", [{"$group": {"_id": "$evaluacion_crediticia.calificacion", "v": {"$sum": 1}}}]))
    comparar("Clientes por arquetipo", sql("SELECT arquetipo_demografico, COUNT(*) FROM Dim_Cliente GROUP BY arquetipo_demografico"),
             agg("FinancialMongo", [{"$group": {"_id": "$perfil_analitico.arquetipo_demografico", "v": {"$sum": 1}}}]))
    comparar("Clientes por distrito de su cuenta (titulares y cotitulares)",
             sql("SELECT d.region, COUNT(*) FROM Puente_Cuenta_Cliente p JOIN Dim_Cuenta c ON c.sk_cuenta = p.sk_cuenta JOIN Dim_Distrito d ON d.sk_distrito = c.sk_distrito GROUP BY d.region"),
             por_region(agg("FinancialMongo", [{"$group": {"_id": "$cuenta.id_distrito", "v": {"$sum": 1}}}])))
    comparar("Clientes sin saldo promedio (cotitulares)", uno("SELECT COUNT(*) FROM Dim_Cliente WHERE saldo_promedio IS NULL"),
             db.FinancialMongo.count_documents({"perfil_analitico.saldo_promedio_historico": None}))
    comparar("Órdenes embebidas en el Cliente 360", uno("SELECT COUNT(*) FROM Fact_Ordenes"),
             agg("FinancialMongo", [{"$group": {"_id": 1, "v": {"$sum": {"$size": "$ordenes_recurrentes"}}}}])[1])
    d69k = cur.execute("SELECT tasa_desempleo, tasa_criminalidad FROM Dim_Distrito WHERE id_distrito_bk = 69").fetchone()
    d69m = db.distritos.find_one({"_id": 69})["indicadores_1995"]
    comparar("Distrito 69 imputado", {"desempleo": float(d69k[0]), "criminalidad": float(d69k[1])},
             {"desempleo": d69m["tasa_desempleo"], "criminalidad": d69m["tasa_criminalidad"]})

    print("\n6. Lo que vería Power BI (conector del script 26)")
    with contextlib.redirect_stdout(io.StringIO()):
        g = runpy.run_path(os.path.join(BASE_DIR, "scripts", "26_powerbi_mongo_dashboard.py"))
    dist, sc, ta = g["m_distritos"].set_index("id_distrito").region, g["m_saldo_cuenta"], g["m_trans_anual"]
    comparar("Conector: saldo al corte por región", sql(f"SELECT d.region, SUM(s.saldo_fin_mes) FROM Fact_Saldo_Cuenta_Mensual s JOIN Dim_Tiempo t ON t.sk_tiempo = s.sk_mes JOIN Dim_Distrito d ON d.sk_distrito = s.sk_distrito WHERE {CORTE} GROUP BY d.region"),
             sc.assign(r=sc.id_distrito.map(dist)).groupby("r").saldo_final.sum().to_dict())
    comparar("Conector: monto por categoría", sql("SELECT o.categoria_analitica, SUM(f.monto_transaccion) FROM Fact_Transacciones f JOIN Dim_Operacion o ON o.sk_operacion = f.sk_operacion GROUP BY o.categoria_analitica"),
             ta.groupby("tipo_operacion").monto_total.sum().to_dict())
    comparar("Conector: cartera por región", sql("SELECT d.region, SUM(f.monto_prestamo) FROM Fact_Prestamos f JOIN Dim_Distrito d ON d.sk_distrito = f.sk_distrito GROUP BY d.region"),
             g["m_prestamos"].assign(r=g["m_prestamos"].id_distrito.map(dist)).groupby("r").monto_prestamo.sum().to_dict())

    ok = sum(p["resultado"] == "OK" for p in pruebas)
    cur.fast_executemany = True
    cur.executemany("INSERT INTO Auditoria_Carga (id_ejecucion, prueba, valor_esperado, valor_obtenido, resultado) VALUES (?, ?, ?, ?, ?)",
                    [(ID_EJECUCION, p["prueba"][:120], p["kimball"][:200], p["mongodb"][:200], p["resultado"]) for p in pruebas])
    cn.commit()
    cn.close()
    with open(SALIDA_JSON, "w", encoding="utf-8") as fh:
        json.dump({"id_ejecucion": ID_EJECUCION, "duracion_segundos": round(time.time() - t0, 1), "pruebas_ok": ok,
                   "pruebas_total": len(pruebas), "pruebas": pruebas}, fh, ensure_ascii=False, indent=2)
    print(f"\n{ok}/{len(pruebas)} pruebas OK en {time.time() - t0:.1f} s. Resumen: {SALIDA_JSON}")


if __name__ == "__main__":
    main()
