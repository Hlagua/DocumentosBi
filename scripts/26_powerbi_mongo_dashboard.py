"""
==============================================================================
UNIVERSIDAD TÉCNICA DE AMBATO - Inteligencia de Negocios
AUTORES: Alison Marcela Cobos Taco / Henry Daniel Lagua Flores
==============================================================================
ARCHIVO: 26_powerbi_mongo_dashboard.py   (Guía 07 v4)
USO EN POWER BI: el script 30 lo incrusta en la consulta MongoFinancial del
                 proyecto Dashboard_Financial_Mongo.pbip. También se puede
                 ejecutar suelto para revisar las tablas.

Construye, desde la base documental 'Financial' (cargada por el script 35 y
completada por el 42), las mismas tablas que el modelo Kimball, con los mismos
nombres de columnas, para que las medidas DAX sean idénticas:

  m_distritos         77   (Dim_Distrito)
  m_clientes       5,369   (Dim_Cliente)
  m_cuentas        4,500   (Dim_Cuenta)
  m_anios              6   (Dim_Anio)
  m_meses             72   (meses de la foto de saldos)
  m_prestamos        682   (Fact_Prestamos)
  m_ordenes        6,471   (Fact_Ordenes)
  m_trans_anual   54,298   (vw_PBI_Trans_Anual_Cuenta: agregado en MongoDB con $group)
  m_saldo_mensual 185,615  (Fact_Saldo_Cuenta_Mensual)
  m_recomendaciones 4,500  (Recomendacion_Cuenta)
==============================================================================
"""
import pandas as pd
import pymongo

MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "Financial"

client = pymongo.MongoClient(MONGO_URI)
db = client[DB_NAME]


def macro(region):
    return "Praga" if region == "Prague" else ("Moravia" if "Moravia" in str(region) else "Bohemia")


# ---- Dimensiones ----
m_distritos = pd.DataFrame([{
    "id_distrito": d["id_distrito"], "nombre_distrito": d["nombre"], "region": d["region"], "poblacion": d["poblacion"],
    "salario_promedio": d["salario_promedio"], "tasa_desempleo": d["indicadores_1995"]["tasa_desempleo"],
    "tasa_criminalidad": d["indicadores_1995"]["tasa_criminalidad"], "es_imputado": d["auditoria"]["es_imputado"],
} for d in db.distritos.find({})])
m_distritos["macro_region"] = m_distritos.region.map(macro)

filas_cli, filas_cta = [], {}
for c in db.FinancialMongo.find({}, {"ordenes_recurrentes": 0, "prestamo_asociado": 0}):
    filas_cli.append({
        "id_cliente": c["id_cliente"], "cliente": f"Cliente {c['id_cliente']}", "sexo": c["datos_personales"]["sexo"],
        "edad_corte": c["datos_personales"]["edad_al_corte_1998"], "tipo_disposicion": c["datos_personales"]["tipo_disposicion"],
        "segmento_edad": c["perfil_analitico"]["segmento_edad"], "arquetipo_demografico": c["perfil_analitico"]["arquetipo_demografico"],
        "calificacion_pago": c["evaluacion_crediticia"]["calificacion"]})
    cta = c["cuenta"]
    filas_cta[cta["id_cuenta"]] = {"id_cuenta": cta["id_cuenta"], "frecuencia_extracto": cta["frecuencia_extracto"],
                                   "fecha_apertura": cta["fecha_apertura"], "tiene_credito_externo": cta["tiene_credito_externo"],
                                   "monto_credito_externo": cta["monto_credito_externo"]}
m_clientes = pd.DataFrame(filas_cli)
# Columnas de orden de las categorías ordinales (Power BI ordena por ellas, no alfabéticamente)
m_clientes["orden_segmento"] = m_clientes.segmento_edad.map(
    lambda s: 1 if "Joven" in s else (3 if "Mayor" in s else 2)).astype("int64")
m_cuentas = pd.DataFrame(list(filas_cta.values()))
m_cuentas["fecha_apertura"] = pd.to_datetime(m_cuentas.fecha_apertura)
m_anios = pd.DataFrame({"anio": range(1993, 1999)})
m_meses = pd.DataFrame({"fecha_mes": pd.date_range("1993-01-31", "1998-12-31", freq="ME")})
m_meses["anio"] = m_meses.fecha_mes.dt.year
m_meses["mes"] = m_meses.fecha_mes.dt.month

# ---- Hechos ----
m_prestamos = pd.DataFrame([{
    "id_prestamo": p["id_prestamo"], "id_cuenta": p["id_cuenta"], "id_cliente": p["id_cliente"], "id_distrito": p["id_distrito"],
    "fecha_otorgamiento": p["condiciones"]["fecha_otorgamiento"], "anio": p["anio"], "monto_prestamo": p["condiciones"]["monto"],
    "plazo_meses": p["condiciones"]["plazo_meses"], "pago_mensual": p["condiciones"]["cuota_mensual"],
    "saldo_pendiente_estimado": p["condiciones"]["saldo_pendiente_estimado"],
    "meses_transcurridos_al_corte": p["condiciones"]["meses_transcurridos_al_corte"],
    "codigo_estado": p["evaluacion_riesgo"]["codigo_estado"], "condicion": p["evaluacion_riesgo"]["condicion"],
    "descripcion_estado": p["evaluacion_riesgo"]["descripcion"],
    "saldo_promedio_previo": p["capacidad_pago"]["saldo_promedio_previo"],
    "ratio_cuota_saldo_previo": p["capacidad_pago"]["ratio_cuota_saldo_previo"],
    "banda_capacidad": p["capacidad_pago"]["banda_capacidad"],
} for p in db.prestamos.find({})])
m_prestamos["fecha_otorgamiento"] = pd.to_datetime(m_prestamos.fecha_otorgamiento)
m_prestamos["orden_banda"] = m_prestamos.banda_capacidad.map({"Baja": 1, "Media-baja": 2, "Media-alta": 3, "Alta": 4}).astype("int64")

m_ordenes = pd.DataFrame([{
    "id_orden": o["id_orden"], "id_cuenta": o["id_cuenta"], "id_cliente": o["id_cliente"], "id_distrito": o["id_distrito"],
    "k_symbol": o["categoria_pago"]["codigo"], "categoria_orden": o["categoria_pago"]["descripcion"], "monto_orden": o["monto_mensual"],
} for o in db.ordenes.find({})])

# Agregado anual por cuenta y categoría, calculado DENTRO de MongoDB
m_trans_anual = pd.json_normalize(list(db.transacciones.aggregate([
    {"$group": {"_id": {"id_cuenta": "$id_cuenta", "anio": "$anio", "categoria_analitica": "$tipo_operacion_traducido"},
                "id_cliente": {"$first": "$id_cliente"}, "id_distrito": {"$first": "$id_distrito"},
                "num_transacciones": {"$sum": 1}, "monto_total": {"$sum": "$monto_transaccion"},
                "suma_cuadrados": {"$sum": {"$multiply": ["$monto_transaccion", "$monto_transaccion"]}},
                "saldo_promedio": {"$avg": "$saldo_cuenta"}}}], allowDiskUse=True)))
m_trans_anual.columns = [c.replace("_id.", "") for c in m_trans_anual.columns]

m_saldo_mensual = pd.DataFrame(list(db.saldos_mensuales.find({}, {"_id": 0})))
m_saldo_mensual["fecha_mes"] = pd.to_datetime(dict(year=m_saldo_mensual.anio, month=m_saldo_mensual.mes, day=1)) + pd.offsets.MonthEnd(0)
m_saldo_mensual["en_sobregiro"] = m_saldo_mensual.en_sobregiro.astype(bool)

m_recomendaciones = pd.DataFrame([{
    "id_cuenta": r["id_cuenta"], "id_cliente": r["id_cliente"], "modelo": r["modelo"],
    "recomendacion_1": (r["recomendaciones"] + [None] * 3)[0], "recomendacion_2": (r["recomendaciones"] + [None] * 3)[1],
    "recomendacion_3": (r["recomendaciones"] + [None] * 3)[2],
    "prestamo_cuota_maxima": r["prestamo_cuota_maxima"], "prestamo_monto_maximo_36m": r["prestamo_monto_maximo_36m"],
} for r in db.recomendaciones.find({})])

# El puente Python de Power BI no reconoce StringDtype (pandas >= 3) ni fechas en microsegundos
for df in (m_meses, m_distritos, m_clientes, m_cuentas, m_prestamos, m_ordenes, m_trans_anual, m_saldo_mensual, m_recomendaciones):
    for col in df.columns:
        if pd.api.types.is_string_dtype(df[col]) and not pd.api.types.is_object_dtype(df[col]):
            df[col] = df[col].astype(object)
        elif pd.api.types.is_datetime64_any_dtype(df[col]):
            df[col] = df[col].astype("datetime64[ns]")   # resolución que espera el puente de Power BI

client.close()

print("Tablas MongoDB listas para Power BI:")
for nombre in ["m_distritos", "m_clientes", "m_cuentas", "m_anios", "m_meses", "m_prestamos", "m_ordenes",
               "m_trans_anual", "m_saldo_mensual", "m_recomendaciones"]:
    print(f"  - {nombre:<18} {len(globals()[nombre]):>8,} filas")
