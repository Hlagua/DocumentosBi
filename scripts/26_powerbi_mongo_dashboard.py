"""
==============================================================================
UNIVERSIDAD TÉCNICA DE AMBATO - Inteligencia de Negocios
AUTORES: Alison Marcela Cobos Taco / Henry Daniel Lagua Flores
==============================================================================
ARCHIVO: 26_powerbi_mongo_dashboard.py
USO EN POWER BI: Obtener datos -> Más... -> Script de Python -> pegar TODO
                 este archivo -> Aceptar -> marcar las 7 tablas m_*.

Construye el modelo estrella del Dashboard_Financial_Mongo.pbix a partir de
la base documental 'Financial' (MongoDB). Las transacciones y el saldo final
se calculan DENTRO de MongoDB con Aggregation Pipelines ($group), de modo que
Power BI recibe ~54 mil filas en lugar de 1,056,320.

Funciona con los dos esquemas de carga del proyecto:
  * Esquema documental anidado (script 22 / Financial_mongo_dump.gz)
  * Esquema plano (script 23, restauración desde CSV)

Tablas resultantes (mismas claves y nombres de columnas que el modelo Kimball
para reutilizar las medidas DAX de la guía 07):
  m_distritos        77 filas     (dimensión)
  m_clientes      5,369 filas     (dimensión, Cliente 360)
  m_anios             6 filas     (dimensión de tiempo anual 1993-1998)
  m_prestamos       682 filas     (hecho)
  m_ordenes       6,471 filas     (hecho)
  m_trans_anual  ~54,298 filas    (hecho agregado cuenta-año-operación)
  m_saldo_cuenta  4,500 filas     (hecho semiaditivo: último saldo)
==============================================================================
"""
import pandas as pd
import pymongo

MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "Financial"

client = pymongo.MongoClient(MONGO_URI)
db = client[DB_NAME]


def campo(doc, *rutas, defecto=None):
    """Devuelve el primer valor existente entre varias rutas 'a.b.c'."""
    for ruta in rutas:
        valor = doc
        for parte in ruta.split("."):
            if isinstance(valor, dict) and parte in valor:
                valor = valor[parte]
            else:
                valor = None
                break
        if valor is not None and not (isinstance(valor, float) and pd.isna(valor)):
            return valor
    return defecto


# ------------------------------------------------------------------------------
# 1. DIMENSIÓN DISTRITO
# ------------------------------------------------------------------------------
m_distritos = pd.DataFrame([{
    "id_distrito": int(campo(d, "id_distrito", "_id")),
    "nombre_distrito": campo(d, "nombre", "nombre_distrito"),
    "region": campo(d, "region"),
    "poblacion": campo(d, "poblacion"),
    "salario_promedio": campo(d, "salario_promedio"),
    "tasa_desempleo": campo(d, "indicadores_1995.tasa_desempleo", "tasa_desempleo"),
    "tasa_criminalidad": campo(d, "indicadores_1995.tasa_criminalidad", "tasa_criminalidad"),
    "es_imputado": bool(campo(d, "auditoria.es_imputado", "es_imputado", defecto=False)),
} for d in db.distritos.find({})])

MACRO = {"Prague": "Praga"}
m_distritos["macro_region"] = m_distritos["region"].map(
    lambda r: MACRO.get(r, "Moravia" if "Moravia" in str(r) else "Bohemia"))
region_de = m_distritos.set_index("id_distrito")["region"].to_dict()

# ------------------------------------------------------------------------------
# 2. DIMENSIÓN CLIENTE 360 (colección FinancialMongo)
# ------------------------------------------------------------------------------
m_clientes = pd.DataFrame([{
    "id_cliente": int(campo(c, "id_cliente", "_id")),
    "sexo": campo(c, "datos_personales.sexo", "sexo"),
    "edad_corte": campo(c, "datos_personales.edad_al_corte_1998", "edad_corte"),
    "tipo_disposicion": campo(c, "datos_personales.tipo_disposicion", "tipo_disposicion"),
    "calificacion_pago": str(campo(c, "evaluacion_crediticia.calificacion",
                                   "etiqueta_buen_pagador", defecto="Sin evaluar")),
    "tiene_prestamo": bool(campo(c, "evaluacion_crediticia.tiene_prestamo",
                                 "tiene_prestamo", defecto=False)),
    "id_distrito_residencia": campo(c, "distrito.id_distrito", "id_distrito"),
    "total_ordenes_activas": campo(c, "perfil_analitico.total_ordenes_activas",
                                   "total_ordenes_activas", defecto=0),
} for c in db.FinancialMongo.find({}, {"ordenes_recurrentes": 0, "prestamo_asociado": 0})])

m_clientes["calificacion_pago"] = m_clientes["calificacion_pago"].replace(
    {"True": "Buen pagador", "False": "Moroso historico", "1": "Buen pagador", "0": "Moroso historico"})
m_clientes["cliente"] = "Cliente " + m_clientes["id_cliente"].astype(str)
m_clientes["segmento_edad"] = pd.cut(
    m_clientes["edad_corte"], bins=[0, 25, 40, 60, 200],
    labels=["Joven (<=25)", "Adulto joven (26-40)", "Adulto (41-60)", "Mayor (>60)"]
).astype(str)

# ------------------------------------------------------------------------------
# 3. HECHO PRÉSTAMOS
# ------------------------------------------------------------------------------
m_prestamos = pd.DataFrame([{
    "id_prestamo": int(campo(p, "id_prestamo", "_id")),
    "id_cuenta": int(campo(p, "id_cuenta")),
    "id_cliente": int(campo(p, "id_cliente")),
    "id_distrito": int(campo(p, "distrito.id_distrito", "id_distrito")),
    "fecha_otorgamiento": campo(p, "condiciones.fecha_otorgamiento", "fecha_otorgamiento"),
    "monto_prestamo": float(campo(p, "condiciones.monto", "monto_prestamo")),
    "plazo_meses": int(campo(p, "condiciones.plazo_meses", "plazo_meses")),
    "pago_mensual": float(campo(p, "condiciones.cuota_mensual", "pago_mensual")),
    "saldo_pendiente_estimado": float(campo(p, "condiciones.saldo_pendiente_estimado", "condiciones.saldo_pendiente",
                                            "saldo_pendiente_estimado", defecto=0)),
    "codigo_estado": campo(p, "evaluacion_riesgo.codigo_estado", "estado_prestamo"),
    "condicion": campo(p, "evaluacion_riesgo.condicion", "condicion_prestamo"),
    "descripcion_estado": campo(p, "evaluacion_riesgo.descripcion", "descripcion_estado"),
} for p in db.prestamos.find({})])

m_prestamos["fecha_otorgamiento"] = pd.to_datetime(m_prestamos["fecha_otorgamiento"])
m_prestamos["anio"] = m_prestamos["fecha_otorgamiento"].dt.year

# ------------------------------------------------------------------------------
# 4. HECHO ÓRDENES PERMANENTES
# ------------------------------------------------------------------------------
m_ordenes = pd.DataFrame([{
    "id_orden": int(campo(o, "id_orden", "_id")),
    "id_cuenta": int(campo(o, "id_cuenta")),
    "id_cliente": int(campo(o, "id_cliente")),
    "id_distrito": campo(o, "id_distrito"),
    "k_symbol": campo(o, "categoria_pago.codigo", "k_symbol"),
    "categoria_orden": campo(o, "categoria_pago.descripcion", "categoria_orden"),
    "monto_orden": float(campo(o, "monto_mensual", "monto_orden")),
} for o in db.ordenes.find({})])

# ------------------------------------------------------------------------------
# 5. HECHOS DE TRANSACCIONES (agregados en MongoDB)
# ------------------------------------------------------------------------------
pipeline_anual = [
    {"$group": {
        "_id": {"id_cuenta": "$id_cuenta", "anio": "$anio",
                "tipo_operacion": "$tipo_operacion_traducido"},
        "id_cliente": {"$first": "$id_cliente"},
        "id_distrito": {"$first": "$id_distrito"},
        "canal": {"$first": "$canal"},
        "num_transacciones": {"$sum": 1},
        "monto_total": {"$sum": "$monto_transaccion"},
        "suma_cuadrados": {"$sum": {"$multiply": ["$monto_transaccion", "$monto_transaccion"]}},
        "saldo_promedio": {"$avg": "$saldo_cuenta"},
    }},
]
m_trans_anual = pd.json_normalize(
    list(db.transacciones.aggregate(pipeline_anual, allowDiskUse=True)))
m_trans_anual.columns = [c.replace("_id.", "") for c in m_trans_anual.columns]

pipeline_saldo = [
    {"$sort": {"id_cuenta": 1, "fecha": -1, "_id": -1}},
    {"$group": {
        "_id": "$id_cuenta",
        "id_cliente": {"$first": "$id_cliente"},
        "id_distrito": {"$first": "$id_distrito"},
        "fecha_ultimo_movimiento": {"$first": "$fecha"},
        "saldo_final": {"$first": "$saldo_cuenta"},
    }},
]
m_saldo_cuenta = pd.DataFrame(
    list(db.transacciones.aggregate(pipeline_saldo, allowDiskUse=True))
).rename(columns={"_id": "id_cuenta"})
m_saldo_cuenta["fecha_ultimo_movimiento"] = pd.to_datetime(m_saldo_cuenta["fecha_ultimo_movimiento"])

# ------------------------------------------------------------------------------
# 6. DISTRITO DE LA CUENTA en cada hecho (si el documento no lo trae, se hereda
#    de la cuenta a través de préstamos/órdenes o, en último caso, del cliente).
#    Igual que en Kimball: el distrito del hecho es el de la CUENTA.
# ------------------------------------------------------------------------------
distrito_cuenta = (
    pd.concat([m_prestamos[["id_cuenta", "id_distrito"]],
               m_ordenes[["id_cuenta", "id_distrito"]],
               m_trans_anual[["id_cuenta", "id_distrito"]] if "id_distrito" in m_trans_anual else None])
    .dropna().drop_duplicates("id_cuenta").set_index("id_cuenta")["id_distrito"]
)
distrito_cliente = m_clientes.set_index("id_cliente")["id_distrito_residencia"]
for df in (m_ordenes, m_trans_anual, m_saldo_cuenta):
    if "id_distrito" not in df:
        df["id_distrito"] = None
    df["id_distrito"] = (df["id_distrito"]
                         .fillna(df["id_cuenta"].map(distrito_cuenta))
                         .fillna(df["id_cliente"].map(distrito_cliente))
                         .astype(int))

# ------------------------------------------------------------------------------
# 7. DIMENSIÓN AÑO
# ------------------------------------------------------------------------------
m_anios = pd.DataFrame({"anio": range(1993, 1999)})

# El puente Python de Power BI no reconoce el tipo StringDtype de pandas >= 3.
for df in (m_distritos, m_clientes, m_prestamos, m_ordenes, m_trans_anual, m_saldo_cuenta):
    for col in df.columns:
        if pd.api.types.is_string_dtype(df[col]) and not pd.api.types.is_object_dtype(df[col]):
            df[col] = df[col].astype(object)

client.close()

print("Tablas MongoDB listas para Power BI:")
for nombre in ["m_distritos", "m_clientes", "m_anios", "m_prestamos",
               "m_ordenes", "m_trans_anual", "m_saldo_cuenta"]:
    print(f"  - {nombre:<15} {len(globals()[nombre]):>8,} filas")
