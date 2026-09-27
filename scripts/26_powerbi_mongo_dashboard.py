"""
==============================================================================
UNIVERSIDAD TÉCNICA DE AMBATO - Inteligencia de Negocios
AUTORES: Alison Marcela Cobos Taco / Henry Daniel Lagua Flores
==============================================================================
ARCHIVO: 26_powerbi_mongo_dashboard.py
DESCRIPCIÓN: Conector de Power BI (Script de Python) que construye el modelo
             estrella desnormalizado para el dashboard MongoDB ('Financial').
             Ejecuta Aggregation Pipelines nativos dentro de MongoDB para
             calcular el saldo final semiaditivo ($197.14M) y agregar el millón
             de transacciones en segundos (Total: $6.26B).
USO EN POWER BI:
    1. Obtener datos -> Más... -> Script de Python.
    2. Pegar este código completo.
    3. Seleccionar las 7 tablas generadas con prefijo 'm_*'.
==============================================================================
"""

import pymongo
import pandas as pd
import numpy as np

MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "Financial"

client = pymongo.MongoClient(MONGO_URI)
db = client[DB_NAME]

print("Conectado a MongoDB 'Financial'. Procesando agregaciones para Power BI...")

# ------------------------------------------------------------------------------
# 1. m_distritos (77 filas)
# ------------------------------------------------------------------------------
docs_dist = list(db.distritos.find({}, {"_id": 0, "auditoria": 0}))
m_distritos = pd.DataFrame(docs_dist)
if not m_distritos.empty:
    m_distritos['macro_region'] = m_distritos['region'].apply(
        lambda r: "Praga" if r == "Prague" else ("Moravia" if "Moravia" in str(r) else "Bohemia")
    )

# ------------------------------------------------------------------------------
# 2. m_clientes (5,369 filas)
# ------------------------------------------------------------------------------
docs_cli = list(db.FinancialMongo.find({}, {"_id": 0, "ordenes_recurrentes": 0, "prestamo_asociado": 0}))
if docs_cli:
    m_clientes = pd.DataFrame(docs_cli)
    m_clientes['cliente'] = "Cliente " + m_clientes['id_cliente'].astype(str)
    m_clientes['sexo'] = m_clientes['datos_personales'].apply(lambda x: str(x.get('sexo', '')))
    m_clientes['edad_corte'] = m_clientes['datos_personales'].apply(lambda x: x.get('edad_al_corte_1998'))
    m_clientes['tipo_disposicion'] = m_clientes['datos_personales'].apply(lambda x: str(x.get('tipo_disposicion', '')))
    m_clientes['tiene_prestamo'] = m_clientes['evaluacion_crediticia'].apply(lambda x: bool(x.get('tiene_prestamo', False)))
    m_clientes['calificacion_pago'] = m_clientes['evaluacion_crediticia'].apply(lambda x: str(x.get('calificacion', '')))
    m_clientes['macro_region'] = m_clientes['perfil_analitico'].apply(lambda x: str(x.get('macro_region', '')))
    m_clientes['segmento_edad'] = m_clientes['perfil_analitico'].apply(lambda x: str(x.get('segmento_edad', '')))
    m_clientes['arquetipo_demografico'] = m_clientes['perfil_analitico'].apply(lambda x: str(x.get('arquetipo_demografico', '')))
    m_clientes['total_ordenes_activas'] = m_clientes['perfil_analitico'].apply(lambda x: int(x.get('total_ordenes_activas', 0)))
    m_clientes['saldo_promedio'] = m_clientes['perfil_analitico'].apply(lambda x: float(x.get('saldo_promedio_historico', 0.0)))
    m_clientes['id_distrito'] = m_clientes['distrito'].apply(lambda x: int(x.get('id_distrito', 0)))
    m_clientes['nombre_distrito'] = m_clientes['distrito'].apply(lambda x: str(x.get('nombre', '')))
    m_clientes = m_clientes.drop(columns=['datos_personales', 'evaluacion_crediticia', 'perfil_analitico', 'distrito'])
else:
    m_clientes = pd.DataFrame()

# ------------------------------------------------------------------------------
# 3. m_prestamos (682 filas)
# ------------------------------------------------------------------------------
docs_pres = list(db.prestamos.find({}, {"_id": 0}))
if docs_pres:
    m_prestamos = pd.DataFrame(docs_pres)
    m_prestamos['monto_prestamo'] = m_prestamos['condiciones'].apply(lambda x: float(x['monto']))
    m_prestamos['plazo_meses'] = m_prestamos['condiciones'].apply(lambda x: int(x['plazo_meses']))
    m_prestamos['pago_mensual'] = m_prestamos['condiciones'].apply(lambda x: float(x['cuota_mensual']))
    m_prestamos['saldo_pendiente_estimado'] = m_prestamos['condiciones'].apply(lambda x: float(x.get('saldo_pendiente', 0.0)))
    m_prestamos['fecha_otorgamiento'] = pd.to_datetime(m_prestamos['condiciones'].apply(lambda x: x['fecha_otorgamiento']))
    m_prestamos['anio'] = m_prestamos['fecha_otorgamiento'].dt.year
    m_prestamos['codigo_estado'] = m_prestamos['evaluacion_riesgo'].apply(lambda x: str(x['codigo_estado']))
    m_prestamos['condicion'] = m_prestamos['evaluacion_riesgo'].apply(lambda x: str(x['condicion']))
    m_prestamos['descripcion'] = m_prestamos['evaluacion_riesgo'].apply(lambda x: str(x['descripcion']))
    m_prestamos['es_moroso'] = m_prestamos['evaluacion_riesgo'].apply(lambda x: bool(x['es_moroso']))
    m_prestamos['ratio_endeudamiento_pct'] = m_prestamos['evaluacion_riesgo'].apply(lambda x: float(x['ratio_endeudamiento_pct']))
    m_prestamos['id_distrito'] = m_prestamos['distrito'].apply(lambda x: int(x['id_distrito']))
    m_prestamos['nombre_distrito'] = m_prestamos['distrito'].apply(lambda x: str(x['nombre']))
    m_prestamos = m_prestamos.drop(columns=['condiciones', 'evaluacion_riesgo', 'distrito'])
else:
    m_prestamos = pd.DataFrame()

# ------------------------------------------------------------------------------
# 4. m_ordenes (6,471 filas)
# ------------------------------------------------------------------------------
docs_ord = list(db.ordenes.find({}, {"_id": 0}))
if docs_ord:
    m_ordenes = pd.DataFrame(docs_ord)
    m_ordenes['monto_orden'] = m_ordenes['monto_mensual'].astype(float)
    m_ordenes['k_symbol'] = m_ordenes['categoria_pago'].apply(lambda x: str(x['codigo']))
    m_ordenes['categoria_orden'] = m_ordenes['categoria_pago'].apply(lambda x: str(x['descripcion']))
    m_ordenes = m_ordenes.drop(columns=['monto_mensual', 'categoria_pago'])
else:
    m_ordenes = pd.DataFrame()

# ------------------------------------------------------------------------------
# 5. m_saldo_cuenta (4,500 filas - Medida Semiaditiva institucional: $197,140,434)
# Pipeline nativo en MongoDB con $sort y $group por cuenta
# ------------------------------------------------------------------------------
pipeline_saldo = [
    {"$sort": {"id_cuenta": 1, "fecha": 1, "id_transaccion": 1}},
    {"$group": {
        "_id": "$id_cuenta",
        "id_cuenta": {"$last": "$id_cuenta"},
        "id_cliente": {"$last": "$id_cliente"},
        "saldo_final": {"$last": "$saldo_cuenta"}
    }}
]
docs_saldo = list(db.transacciones.aggregate(pipeline_saldo, allowDiskUse=True))
m_saldo_cuenta = pd.DataFrame(docs_saldo).drop(columns=['_id'])

# ------------------------------------------------------------------------------
# 6. m_trans_anual (Transacciones agregadas por cuenta, año y operación: $6.26B)
# ------------------------------------------------------------------------------
pipeline_trans_anual = [
    {"$group": {
        "_id": {
            "id_cuenta": "$id_cuenta",
            "id_cliente": "$id_cliente",
            "anio": "$anio",
            "tipo_operacion": "$tipo_operacion_traducido",
            "canal": "$canal"
        },
        "monto_total": {"$sum": "$monto_transaccion"},
        "num_transacciones": {"$sum": 1},
        "saldo_promedio": {"$avg": "$saldo_cuenta"},
        "suma_cuadrados": {"$sum": {"$multiply": ["$monto_transaccion", "$monto_transaccion"]}}
    }},
    {"$project": {
        "_id": 0,
        "id_cuenta": "$_id.id_cuenta",
        "id_cliente": "$_id.id_cliente",
        "anio": "$_id.anio",
        "tipo_operacion": "$_id.tipo_operacion",
        "canal": "$_id.canal",
        "monto_total": 1,
        "num_transacciones": 1,
        "saldo_promedio": 1,
        "suma_cuadrados": 1
    }}
]
docs_trans = list(db.transacciones.aggregate(pipeline_trans_anual, allowDiskUse=True))
m_trans_anual = pd.DataFrame(docs_trans)

# ------------------------------------------------------------------------------
# 7. m_anios (Tabla de fechas/años para segmentación uniforme)
# ------------------------------------------------------------------------------
m_anios = pd.DataFrame({"anio": sorted(m_trans_anual['anio'].unique())})

print("=" * 80)
print("TABLAS MONGODB APLANADAS Y LISTAS PARA POWER BI:")
print(f"  1. m_distritos    : {len(m_distritos):>6} filas")
print(f"  2. m_clientes     : {len(m_clientes):>6} filas")
print(f"  3. m_prestamos    : {len(m_prestamos):>6} filas | Cartera: ${m_prestamos['monto_prestamo'].sum():,.2f}")
print(f"  4. m_ordenes      : {len(m_ordenes):>6} filas | Débito:  ${m_ordenes['monto_orden'].sum():,.2f}")
print(f"  5. m_saldo_cuenta : {len(m_saldo_cuenta):>6} filas | Saldo:   ${m_saldo_cuenta['saldo_final'].sum():,.2f}")
print(f"  6. m_trans_anual  : {len(m_trans_anual):>6} filas | Total:   ${m_trans_anual['monto_total'].sum():,.2f}")
print(f"  7. m_anios        : {len(m_anios):>6} filas")
print("=" * 80)
