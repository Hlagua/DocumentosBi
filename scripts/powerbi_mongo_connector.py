"""
==============================================================================
Script auxiliar: powerbi_mongo_connector.py
Uso en Power BI: Obtener datos -> Script de Python -> Pegar este código.
Carga las 4 colecciones analíticas de MongoDB ('Financial') como tablas
relacionales aplanadas listas para el Dashboard en Power BI.
==============================================================================
"""
import pymongo
import pandas as pd

MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "Financial"

client = pymongo.MongoClient(MONGO_URI)
db = client[DB_NAME]

# 1. Tabla de Préstamos Aplanada (Hecho de Riesgo)
df_raw_prestamos = list(db.prestamos.find({}, {"_id": 0}))
if df_raw_prestamos:
    df_prestamos = pd.DataFrame(df_raw_prestamos)
    df_prestamos['monto_prestamo'] = df_prestamos['condiciones'].apply(lambda x: float(x['monto']))
    df_prestamos['plazo_meses'] = df_prestamos['condiciones'].apply(lambda x: int(x['plazo_meses']))
    df_prestamos['pago_mensual'] = df_prestamos['condiciones'].apply(lambda x: float(x['cuota_mensual']))
    df_prestamos['saldo_pendiente'] = df_prestamos['condiciones'].apply(lambda x: float(x.get('saldo_pendiente', 0)))
    df_prestamos['fecha_otorgamiento'] = pd.to_datetime(df_prestamos['condiciones'].apply(lambda x: x['fecha_otorgamiento']))
    df_prestamos['anio'] = df_prestamos['fecha_otorgamiento'].dt.year
    df_prestamos['codigo_estado'] = df_prestamos['evaluacion_riesgo'].apply(lambda x: str(x['codigo_estado']))
    df_prestamos['condicion'] = df_prestamos['evaluacion_riesgo'].apply(lambda x: str(x['condicion']))
    df_prestamos['descripcion_estado'] = df_prestamos['evaluacion_riesgo'].apply(lambda x: str(x['descripcion']))
    df_prestamos['es_moroso'] = df_prestamos['evaluacion_riesgo'].apply(lambda x: bool(x['es_moroso']))
    df_prestamos['ratio_endeudamiento_pct'] = df_prestamos['evaluacion_riesgo'].apply(lambda x: float(x['ratio_endeudamiento_pct']))
    df_prestamos['id_distrito'] = df_prestamos['distrito'].apply(lambda x: int(x['id_distrito']))
    df_prestamos['nombre_distrito'] = df_prestamos['distrito'].apply(lambda x: str(x['nombre']))
    df_prestamos = df_prestamos.drop(columns=['condiciones', 'evaluacion_riesgo', 'distrito'])
else:
    df_prestamos = pd.DataFrame()

# 2. Tabla de Órdenes Permanentes (Hecho de Pagos Fijos)
df_raw_ordenes = list(db.ordenes.find({}, {"_id": 0}))
if df_raw_ordenes:
    df_ordenes = pd.DataFrame(df_raw_ordenes)
    df_ordenes['codigo_k_symbol'] = df_ordenes['categoria_pago'].apply(lambda x: str(x['codigo']))
    df_ordenes['categoria_orden'] = df_ordenes['categoria_pago'].apply(lambda x: str(x['descripcion']))
    df_ordenes = df_ordenes.drop(columns=['categoria_pago'])
else:
    df_ordenes = pd.DataFrame()

# 3. Tabla de Clientes 360 (Dimensión Enriquecida)
df_raw_clientes = list(db.FinancialMongo.find({}, {"_id": 0, "ordenes_recurrentes": 0, "prestamo_asociado": 0}))
if df_raw_clientes:
    df_clientes = pd.DataFrame(df_raw_clientes)
    df_clientes['sexo'] = df_clientes['datos_personales'].apply(lambda x: str(x['sexo']))
    df_clientes['edad'] = df_clientes['datos_personales'].apply(lambda x: int(x['edad_al_corte_1998']) if x.get('edad_al_corte_1998') else None)
    df_clientes['tipo_disposicion'] = df_clientes['datos_personales'].apply(lambda x: str(x['tipo_disposicion']))
    df_clientes['tiene_prestamo'] = df_clientes['evaluacion_crediticia'].apply(lambda x: bool(x['tiene_prestamo']))
    df_clientes['calificacion_pago'] = df_clientes['evaluacion_crediticia'].apply(lambda x: str(x['calificacion']))
    df_clientes['macro_region'] = df_clientes['perfil_analitico'].apply(lambda x: str(x['macro_region']))
    df_clientes['segmento_edad'] = df_clientes['perfil_analitico'].apply(lambda x: str(x['segmento_edad']))
    df_clientes['arquetipo_demografico'] = df_clientes['perfil_analitico'].apply(lambda x: str(x['arquetipo_demografico']))
    df_clientes['total_ordenes_activas'] = df_clientes['perfil_analitico'].apply(lambda x: int(x['total_ordenes_activas']))
    df_clientes['saldo_promedio'] = df_clientes['perfil_analitico'].apply(lambda x: float(x['saldo_promedio_historico']))
    df_clientes['id_distrito'] = df_clientes['distrito'].apply(lambda x: int(x['id_distrito']))
    df_clientes['nombre_distrito'] = df_clientes['distrito'].apply(lambda x: str(x['nombre']))
    df_clientes['tasa_desempleo'] = df_clientes['distrito'].apply(lambda x: float(x['tasa_desempleo']))
    df_clientes['tasa_criminalidad'] = df_clientes['distrito'].apply(lambda x: float(x['tasa_criminalidad']))
    df_clientes['distrito_es_imputado'] = df_clientes['distrito'].apply(lambda x: bool(x.get('imputacion', {}).get('es_imputado', False)))
    df_clientes = df_clientes.drop(columns=['datos_personales', 'evaluacion_crediticia', 'perfil_analitico', 'distrito'])
else:
    df_clientes = pd.DataFrame()

# 4. Tabla de Distritos
df_raw_distritos = list(db.distritos.find({}, {"_id": 0, "auditoria": 0}))
df_distritos = pd.DataFrame(df_raw_distritos) if df_raw_distritos else pd.DataFrame()

print("Datos de MongoDB aplanados listos para Power BI:")
print(f"  - df_prestamos: {len(df_prestamos)} filas")
print(f"  - df_ordenes:   {len(df_ordenes)} filas")
print(f"  - df_clientes:  {len(df_clientes)} filas")
print(f"  - df_distritos: {len(df_distritos)} filas")
