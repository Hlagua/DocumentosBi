"""
==============================================================================
UNIVERSIDAD TÉCNICA DE AMBATO - Inteligencia de Negocios
AUTORES: Alison Marcela Cobos Taco / Henry Daniel Lagua Flores
==============================================================================
ARCHIVO: 35_migrar_kimball_a_mongodb.py
DESCRIPCIÓN: Migra el Data Mart Kimball (DM_Financial_Kimball_v2, ya cargado y
             completado por los scripts 31 a 34) a MongoDB (base Financial).
             Todo se lee del Data Mart, que es la fuente única de verdad.

  Colección            Documentos   Origen en Kimball
  distritos                    77   Dim_Distrito
  prestamos                   682   Fact_Prestamos + dimensiones
  ordenes                   6,471   Fact_Ordenes + dimensiones
  FinancialMongo            5,369   Dim_Cliente + Dim_Cuenta + préstamo y órdenes embebidos (Cliente 360)
  transacciones         1,056,320   Fact_Transacciones + Dim_Operacion + Dim_Concepto_Movimiento
  saldos_mensuales        185,615   Fact_Saldo_Cuenta_Mensual

  Reglas de la Carta v8 que se conservan en MongoDB:
    * id_cliente de préstamos, órdenes, transacciones y saldos = titular (OWNER).
    * id_distrito de esos documentos = distrito de la CUENTA (no la residencia).
    * El saldo es semiaditivo: la posición al corte se consulta en saldos_mensuales.
  Cada colección se crea con un validador $jsonSchema (validationLevel strict).
USO: python scripts/35_migrar_kimball_a_mongodb.py
==============================================================================
"""
import json
import os
import time
import warnings

import pandas as pd
import pymongo
import pyodbc

warnings.filterwarnings("ignore", message="pandas only supports SQLAlchemy")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SALIDA_JSON = os.path.join(BASE_DIR, "metricas_migracion_mongo.json")
KIMBALL = ("Driver={ODBC Driver 17 for SQL Server};Server=(localdb)\\MSSQLLocalDB;"
           "Database=DM_Financial_Kimball_v2;Trusted_Connection=yes;")
MONGO_URI = "mongodb://localhost:27017/"
MONGO_DB = "Financial"
LOTE = 50_000

NUM = ["double", "int", "long", "decimal"]
NUM_NULO = NUM + ["null"]


def esquema(requeridos, propiedades):
    return {"$jsonSchema": {"bsonType": "object", "required": requeridos, "properties": propiedades}}


VALIDADORES = {
    "distritos": esquema(
        ["id_distrito", "nombre", "region", "poblacion", "indicadores_1995", "indicadores_1996", "auditoria"],
        {"id_distrito": {"bsonType": "int"}, "nombre": {"bsonType": "string"}, "region": {"bsonType": "string"},
         "poblacion": {"bsonType": "int"},
         "indicadores_1995": {"bsonType": "object", "required": ["tasa_desempleo", "tasa_criminalidad"],
                              "properties": {"tasa_desempleo": {"bsonType": NUM}, "tasa_criminalidad": {"bsonType": NUM}}},
         "auditoria": {"bsonType": "object", "required": ["es_imputado", "metodo_imputacion"],
                       "properties": {"es_imputado": {"bsonType": "bool"}, "metodo_imputacion": {"bsonType": "string"}}}}),
    "prestamos": esquema(
        ["id_prestamo", "id_cuenta", "id_cliente", "id_distrito", "anio", "condiciones", "evaluacion_riesgo", "capacidad_pago"],
        {"id_prestamo": {"bsonType": "int"}, "id_cuenta": {"bsonType": "int"}, "id_cliente": {"bsonType": "int"},
         "id_distrito": {"bsonType": "int"}, "anio": {"bsonType": "int"},
         "condiciones": {"bsonType": "object", "required": ["monto", "plazo_meses", "cuota_mensual", "saldo_pendiente_estimado"],
                         "properties": {"monto": {"bsonType": NUM, "minimum": 0}, "plazo_meses": {"enum": [12, 24, 36, 48, 60]},
                                        "cuota_mensual": {"bsonType": NUM, "minimum": 0},
                                        "saldo_pendiente_estimado": {"bsonType": NUM, "minimum": 0}}},
         "evaluacion_riesgo": {"bsonType": "object", "required": ["codigo_estado", "condicion", "con_impago"],
                               "properties": {"codigo_estado": {"enum": ["A", "B", "C", "D"]},
                                              "condicion": {"enum": ["Vigente", "Cerrado"]}, "con_impago": {"bsonType": "bool"}}},
         "capacidad_pago": {"bsonType": "object", "required": ["ratio_cuota_saldo_previo", "banda_capacidad"],
                            "properties": {"banda_capacidad": {"enum": ["Baja", "Media-baja", "Media-alta", "Alta"]}}}}),
    "ordenes": esquema(
        ["id_orden", "id_cuenta", "id_cliente", "id_distrito", "monto_mensual", "categoria_pago"],
        {"id_orden": {"bsonType": "int"}, "id_cuenta": {"bsonType": "int"}, "id_cliente": {"bsonType": "int"},
         "id_distrito": {"bsonType": "int"}, "monto_mensual": {"bsonType": NUM, "minimum": 0},
         "categoria_pago": {"bsonType": "object", "required": ["codigo", "descripcion"],
                            "properties": {"codigo": {"enum": ["SIPO", "UVER", "POJISTNE", "LEASING", "SIN_ESPECIFICAR"]}}}}),
    "FinancialMongo": esquema(
        ["id_cliente", "datos_personales", "cuenta", "evaluacion_crediticia", "perfil_analitico", "distrito"],
        {"id_cliente": {"bsonType": "int"},
         "datos_personales": {"bsonType": "object", "required": ["sexo", "tipo_disposicion", "edad_al_corte_1998"],
                              "properties": {"sexo": {"enum": ["M", "F"]}, "tipo_disposicion": {"enum": ["OWNER", "DISPONENT"]}}},
         "cuenta": {"bsonType": "object", "required": ["id_cuenta", "id_distrito", "tiene_credito_externo"]},
         "evaluacion_crediticia": {"bsonType": "object", "required": ["tiene_prestamo", "calificacion"],
                                   "properties": {"calificacion": {"enum": ["Buen Pagador", "Mal Pagador", "Sin evaluar"]}}},
         "perfil_analitico": {"bsonType": "object", "required": ["macro_region", "segmento_edad", "arquetipo_demografico",
                                                                  "total_ordenes_activas", "saldo_promedio_historico"],
                              "properties": {"saldo_promedio_historico": {"bsonType": NUM_NULO}}},
         "distrito": {"bsonType": "object", "required": ["id_distrito", "nombre", "region", "tasa_desempleo", "tasa_criminalidad"]}}),
    "transacciones": esquema(
        ["id_transaccion", "id_cuenta", "id_cliente", "id_distrito", "fecha", "anio", "tipo_transaccion",
         "tipo_operacion_traducido", "concepto", "monto_transaccion", "saldo_cuenta"],
        {"id_transaccion": {"bsonType": "int"}, "id_cuenta": {"bsonType": "int"}, "id_cliente": {"bsonType": "int"},
         "id_distrito": {"bsonType": "int"}, "fecha": {"bsonType": "string", "pattern": "^199[3-8]-[0-1][0-9]-[0-3][0-9]$"},
         "anio": {"bsonType": "int", "minimum": 1993, "maximum": 1998}, "tipo_transaccion": {"enum": ["PRIJEM", "VYDAJ", "VYBER"]},
         "tipo_operacion_traducido": {"enum": ["Ingreso / Deposito", "Intereses Ganados", "Egreso / Gasto", "Retiro en Efectivo"]},
         "concepto": {"bsonType": "object", "required": ["codigo", "descripcion", "metodo", "contraparte"]},
         "monto_transaccion": {"bsonType": NUM, "minimum": 0}, "saldo_cuenta": {"bsonType": NUM}}),
    "saldos_mensuales": esquema(
        ["id_cuenta", "id_cliente", "id_distrito", "anio", "mes", "saldo_fin_mes", "en_sobregiro"],
        {"id_cuenta": {"bsonType": "int"}, "id_cliente": {"bsonType": "int"}, "id_distrito": {"bsonType": "int"},
         "anio": {"bsonType": "int"}, "mes": {"bsonType": "int", "minimum": 1, "maximum": 12},
         "saldo_fin_mes": {"bsonType": NUM}, "en_sobregiro": {"bsonType": "bool"}}),
}

INDICES = {
    "distritos": [[("region", 1)]],
    "prestamos": [[("id_cliente", 1)], [("id_cuenta", 1)], [("id_distrito", 1)], [("evaluacion_riesgo.codigo_estado", 1)]],
    "ordenes": [[("id_cuenta", 1)], [("id_cliente", 1)], [("categoria_pago.codigo", 1)]],
    "FinancialMongo": [[("cuenta.id_cuenta", 1)], [("distrito.id_distrito", 1)], [("perfil_analitico.arquetipo_demografico", 1)]],
    "transacciones": [[("id_cuenta", 1), ("fecha", 1), ("_id", 1)], [("id_cliente", 1)], [("id_distrito", 1)],
                      [("anio", 1), ("tipo_operacion_traducido", 1)]],
    "saldos_mensuales": [[("anio", 1), ("mes", 1)], [("id_distrito", 1)]],
}


def f(v):
    return None if v is None or pd.isna(v) else float(v)


def fecha(v):
    return None if v is None or pd.isna(v) else pd.Timestamp(v).strftime("%Y-%m-%d")


def crear(db, nombre, docs):
    db.drop_collection(nombre)
    db.create_collection(nombre, validator=VALIDADORES[nombre], validationLevel="strict", validationAction="error")
    t0 = time.time()
    for i in range(0, len(docs), LOTE):
        db[nombre].insert_many(docs[i:i + LOTE], ordered=False)
    for indice in INDICES[nombre]:
        db[nombre].create_index(indice)
    print(f"  {nombre:<18} {db[nombre].count_documents({}):>10,} documentos ({time.time() - t0:.1f} s)")


def main():
    t0 = time.time()
    print("=" * 78 + "\nMIGRACIÓN KIMBALL (DM_Financial_Kimball_v2) -> MONGODB (Financial)\n" + "=" * 78)
    cn = pyodbc.connect(KIMBALL, timeout=300)
    q = lambda s: pd.read_sql(s, cn)
    cliente = pymongo.MongoClient(MONGO_URI, serverSelectionTimeoutMS=10000)
    db = cliente[MONGO_DB]

    # ---------------- distritos ----------------
    d = q("""SELECT id_distrito_bk, nombre_distrito, region, poblacion, salario_promedio, tasa_desempleo, tasa_criminalidad,
                    tasa_desempleo_1996, tasa_criminalidad_1996, es_imputado, metodo_imputacion FROM Dim_Distrito""")
    distritos = {int(r.id_distrito_bk): {
        "_id": int(r.id_distrito_bk), "id_distrito": int(r.id_distrito_bk), "nombre": r.nombre_distrito, "region": r.region,
        "poblacion": int(r.poblacion), "salario_promedio": f(r.salario_promedio),
        "indicadores_1995": {"tasa_desempleo": f(r.tasa_desempleo), "tasa_criminalidad": f(r.tasa_criminalidad)},
        "indicadores_1996": {"tasa_desempleo": f(r.tasa_desempleo_1996), "tasa_criminalidad": f(r.tasa_criminalidad_1996)},
        "auditoria": {"es_imputado": bool(r.es_imputado), "metodo_imputacion": r.metodo_imputacion}} for r in d.itertuples()}

    # ---------------- prestamos ----------------
    p = q("""SELECT fp.id_prestamo_bk, cu.id_cuenta_bk, c.id_cliente_bk, d.id_distrito_bk, t.fecha, t.anio, fp.monto_prestamo,
                    fp.plazo_meses, fp.pago_mensual, fp.saldo_pendiente_estimado, fp.meses_transcurridos_al_corte,
                    e.codigo_estado, e.condicion, e.descripcion, fp.saldo_promedio_previo, fp.ratio_cuota_saldo_previo, fp.banda_capacidad
             FROM Fact_Prestamos fp JOIN Dim_Tiempo t ON t.sk_tiempo = fp.sk_tiempo JOIN Dim_Cuenta cu ON cu.sk_cuenta = fp.sk_cuenta
             JOIN Dim_Cliente c ON c.sk_cliente = fp.sk_cliente JOIN Dim_Distrito d ON d.sk_distrito = fp.sk_distrito
             JOIN Dim_Estado_Prestamo e ON e.sk_estado_prestamo = fp.sk_estado_prestamo""")
    prestamos = [{
        "_id": int(r.id_prestamo_bk), "id_prestamo": int(r.id_prestamo_bk), "id_cuenta": int(r.id_cuenta_bk),
        "id_cliente": int(r.id_cliente_bk), "id_distrito": int(r.id_distrito_bk), "anio": int(r.anio),
        "condiciones": {"fecha_otorgamiento": fecha(r.fecha), "monto": f(r.monto_prestamo), "plazo_meses": int(r.plazo_meses),
                        "cuota_mensual": f(r.pago_mensual), "saldo_pendiente_estimado": f(r.saldo_pendiente_estimado),
                        "meses_transcurridos_al_corte": int(r.meses_transcurridos_al_corte)},
        "evaluacion_riesgo": {"codigo_estado": r.codigo_estado, "condicion": r.condicion, "descripcion": r.descripcion,
                              "con_impago": r.codigo_estado in ("B", "D")},
        "capacidad_pago": {"saldo_promedio_previo": f(r.saldo_promedio_previo),
                           "ratio_cuota_saldo_previo": f(r.ratio_cuota_saldo_previo), "banda_capacidad": r.banda_capacidad},
    } for r in p.itertuples()]

    # ---------------- ordenes ----------------
    o = q("""SELECT fo.id_orden_bk, cu.id_cuenta_bk, c.id_cliente_bk, d.id_distrito_bk, fo.monto_orden,
                    ot.k_symbol_original, ot.categoria_orden_traducida
             FROM Fact_Ordenes fo JOIN Dim_Cuenta cu ON cu.sk_cuenta = fo.sk_cuenta JOIN Dim_Cliente c ON c.sk_cliente = fo.sk_cliente
             JOIN Dim_Distrito d ON d.sk_distrito = fo.sk_distrito JOIN Dim_Orden ot ON ot.sk_orden_tipo = fo.sk_orden_tipo""")
    ordenes = [{
        "_id": int(r.id_orden_bk), "id_orden": int(r.id_orden_bk), "id_cuenta": int(r.id_cuenta_bk), "id_cliente": int(r.id_cliente_bk),
        "id_distrito": int(r.id_distrito_bk), "monto_mensual": f(r.monto_orden),
        "categoria_pago": {"codigo": r.k_symbol_original, "descripcion": r.categoria_orden_traducida}} for r in o.itertuples()]

    # ---------------- FinancialMongo (Cliente 360) ----------------
    c = q("""SELECT c.id_cliente_bk, c.sexo, c.fecha_nacimiento, c.edad_corte, c.tipo_disposicion, c.etiqueta_buen_pagador,
                    c.calificacion_pago_desc, c.macro_region, c.segmento_edad, c.arquetipo_demografico, c.tiene_prestamo,
                    c.total_ordenes_activas, c.saldo_promedio, dr.id_distrito_bk AS id_distrito_residencia
             FROM Dim_Cliente c JOIN Dim_Distrito dr ON dr.sk_distrito = c.sk_distrito""")
    # Cuenta de cada cliente (titulares y cotitulares) a través de la tabla puente del Data Mart
    cu = q("""SELECT c.id_cliente_bk, cu.id_cuenta_bk, cu.frecuencia_emision_estado, cu.fecha_apertura,
                     cu.tiene_credito_externo, cu.monto_credito_externo, d.id_distrito_bk
              FROM Puente_Cuenta_Cliente pc JOIN Dim_Cliente c ON c.sk_cliente = pc.sk_cliente
              JOIN Dim_Cuenta cu ON cu.sk_cuenta = pc.sk_cuenta JOIN Dim_Distrito d ON d.sk_distrito = cu.sk_distrito""")
    cuentas = {int(r.id_cuenta_bk): {"id_cuenta": int(r.id_cuenta_bk), "frecuencia_extracto": r.frecuencia_emision_estado,
                                     "fecha_apertura": fecha(r.fecha_apertura), "id_distrito": int(r.id_distrito_bk),
                                     "tiene_credito_externo": bool(r.tiene_credito_externo),
                                     "monto_credito_externo": f(r.monto_credito_externo)} for r in cu.itertuples()}
    cuenta_de_cliente = {int(r.id_cliente_bk): int(r.id_cuenta_bk) for r in cu.itertuples()}
    prest_por_cliente = {x["id_cliente"]: x for x in prestamos}
    ord_por_cuenta = {}
    for x in ordenes:
        ord_por_cuenta.setdefault(x["id_cuenta"], []).append(
            {"id_orden": x["id_orden"], "codigo": x["categoria_pago"]["codigo"], "descripcion": x["categoria_pago"]["descripcion"],
             "monto": x["monto_mensual"]})
    clientes = []
    for r in c.itertuples():
        id_cli = int(r.id_cliente_bk)
        id_cta = cuenta_de_cliente[id_cli]
        dres = distritos[int(r.id_distrito_residencia)]
        pr = prest_por_cliente.get(id_cli)
        clientes.append({
            "_id": id_cli, "id_cliente": id_cli,
            "datos_personales": {"sexo": r.sexo, "fecha_nacimiento": fecha(r.fecha_nacimiento),
                                 "edad_al_corte_1998": int(r.edad_corte), "tipo_disposicion": r.tipo_disposicion},
            "cuenta": cuentas[id_cta],
            "evaluacion_crediticia": {"tiene_prestamo": bool(r.tiene_prestamo),
                                      "es_buen_pagador": None if pd.isna(r.etiqueta_buen_pagador) else bool(r.etiqueta_buen_pagador),
                                      "calificacion": r.calificacion_pago_desc},
            "perfil_analitico": {"macro_region": r.macro_region, "segmento_edad": r.segmento_edad,
                                 "arquetipo_demografico": r.arquetipo_demografico, "total_ordenes_activas": int(r.total_ordenes_activas),
                                 "saldo_promedio_historico": f(r.saldo_promedio)},
            "distrito": {"id_distrito": dres["id_distrito"], "nombre": dres["nombre"], "region": dres["region"],
                         "poblacion": dres["poblacion"], "salario_promedio": dres["salario_promedio"],
                         "tasa_desempleo": dres["indicadores_1995"]["tasa_desempleo"],
                         "tasa_criminalidad": dres["indicadores_1995"]["tasa_criminalidad"], "imputacion": dres["auditoria"]},
            # Préstamo y órdenes embebidos solo en el titular: son hechos de la cuenta y se registran una vez
            "prestamo_asociado": ({k: pr[k] for k in ("id_prestamo", "condiciones", "evaluacion_riesgo", "capacidad_pago")}
                                  if pr else None),
            "ordenes_recurrentes": ord_por_cuenta.get(id_cta, []) if r.tipo_disposicion == "OWNER" else [],
        })

    # ---------------- transacciones ----------------
    print("Leyendo Fact_Transacciones...")
    t = q("""SELECT ft.id_transaccion_bk, cu.id_cuenta_bk, c.id_cliente_bk, d.id_distrito_bk, ti.fecha, ti.anio, ti.mes, ti.dia,
                    o.tipo_original, o.operacion_original, o.operacion_traducida, o.k_symbol_original, o.categoria_analitica,
                    cm.codigo_concepto, cm.concepto_traducido, cm.metodo_concepto, cm.tipo_contraparte,
                    ft.monto_transaccion, ft.saldo_cuenta
             FROM Fact_Transacciones ft JOIN Dim_Tiempo ti ON ti.sk_tiempo = ft.sk_tiempo JOIN Dim_Cuenta cu ON cu.sk_cuenta = ft.sk_cuenta
             JOIN Dim_Cliente c ON c.sk_cliente = ft.sk_cliente JOIN Dim_Distrito d ON d.sk_distrito = ft.sk_distrito
             JOIN Dim_Operacion o ON o.sk_operacion = ft.sk_operacion
             JOIN Dim_Concepto_Movimiento cm ON cm.sk_concepto = ft.sk_concepto""")
    t["fecha"] = pd.to_datetime(t.fecha).dt.strftime("%Y-%m-%d")
    transacciones = [{
        "_id": int(r[0]), "id_transaccion": int(r[0]), "id_cuenta": int(r[1]), "id_cliente": int(r[2]), "id_distrito": int(r[3]),
        "fecha": r[4], "anio": int(r[5]), "mes": int(r[6]), "dia": int(r[7]), "tipo_transaccion": r[8],
        "operacion_fuente": r[9], "k_symbol_fuente": r[11], "canal": r[10], "tipo_operacion_traducido": r[12],
        "concepto": {"codigo": r[13], "descripcion": r[14], "metodo": r[15], "contraparte": r[16]},
        "monto_transaccion": float(r[17]), "saldo_cuenta": float(r[18]),
    } for r in t.itertuples(index=False, name=None)]
    del t

    # ---------------- saldos_mensuales ----------------
    s = q("""SELECT cu.id_cuenta_bk, c.id_cliente_bk, d.id_distrito_bk, ti.anio, ti.mes, s.saldo_fin_mes, s.saldo_promedio_mes,
                    s.num_movimientos_mes, s.en_sobregiro
             FROM Fact_Saldo_Cuenta_Mensual s JOIN Dim_Tiempo ti ON ti.sk_tiempo = s.sk_mes JOIN Dim_Cuenta cu ON cu.sk_cuenta = s.sk_cuenta
             JOIN Dim_Cliente c ON c.sk_cliente = s.sk_cliente JOIN Dim_Distrito d ON d.sk_distrito = s.sk_distrito""")
    saldos = [{
        "_id": f"{int(r[0])}-{int(r[3])}{int(r[4]):02d}", "id_cuenta": int(r[0]), "id_cliente": int(r[1]), "id_distrito": int(r[2]),
        "anio": int(r[3]), "mes": int(r[4]), "saldo_fin_mes": float(r[5]), "saldo_promedio_mes": float(r[6]),
        "num_movimientos_mes": int(r[7]), "en_sobregiro": bool(r[8]),
    } for r in s.itertuples(index=False, name=None)]
    cn.close()

    print("\nCargando MongoDB (colecciones recreadas con validador $jsonSchema estricto):")
    for nombre, docs in [("distritos", list(distritos.values())), ("prestamos", prestamos), ("ordenes", ordenes),
                         ("FinancialMongo", clientes), ("transacciones", transacciones), ("saldos_mensuales", saldos)]:
        crear(db, nombre, docs)
    resumen = {"duracion_segundos": round(time.time() - t0, 1),
               "colecciones": {n: db[n].count_documents({}) for n in VALIDADORES},
               "validadores": {n: db.command("listCollections", filter={"name": n})["cursor"]["firstBatch"][0]["options"]
                               .get("validationLevel") for n in VALIDADORES}}
    cliente.close()
    with open(SALIDA_JSON, "w", encoding="utf-8") as fh:
        json.dump(resumen, fh, ensure_ascii=False, indent=2)
    print(f"\nMigración completa en {resumen['duracion_segundos']} s. Siguiente paso: python scripts/36_reconciliacion_kimball_mongo.py")


if __name__ == "__main__":
    main()
