import pandas as pd
import numpy as np
import os
import time

print("=== INICIANDO PIPELINE DE COMPLETITUD DE DATOS: df_transacciones ===")
t0 = time.time()

data_dir = r"C:\Users\henry\.gemini\antigravity\scratch\dataframes"
parquet_input = os.path.join(data_dir, "df_transacciones.parquet")

# 1. Cargar DataFrames
print("\n1. Cargando DataFrames en memoria...")
df_trans = pd.read_parquet(parquet_input)
df_prest = pd.read_csv(os.path.join(data_dir, "df_prestamos.csv"))
df_ord = pd.read_csv(os.path.join(data_dir, "df_ordenes.csv"))

print(f"   -> df_transacciones cargado: {len(df_trans):,} filas.")
print(f"   -> df_prestamos cargado: {len(df_prest):,} filas.")
print(f"   -> df_ordenes cargado: {len(df_ord):,} filas.")

# Estandarizar cadenas vacías o con solo espacios a NaN
print("\n--- NORMALIZANDO HUECOS (STRINGS VACÍOS Y NULOS) ---")
for col in ['operation', 'k_symbol', 'bank', 'account']:
    if col in df_trans.columns:
        df_trans[col] = df_trans[col].replace(r'^\s*$', np.nan, regex=True)

# Diagnóstico inicial de nulos y vacíos
print("\n--- DIAGNÓSTICO INICIAL DE HUECOS EN df_transacciones ---")
nulls_iniciales = df_trans.isnull().sum()
print(nulls_iniciales[nulls_iniciales > 0])

# ------------------------------------------------------------------------------
# FASE 1: COMPLETITUD DE 'operation', 'tipo_operacion_traducido' y 'canal'
# ------------------------------------------------------------------------------
print("\n2. [FASE 1] Completando 'operation', 'tipo_operacion_traducido' y 'canal' (183,114 nulos)...")

# Regla 1.1: Si es PRIJEM y k_symbol == 'UROK' -> Abono de Intereses del Banco
cond_urok = (df_trans['operation'].isna()) & (df_trans['tipo_transaccion'] == 'PRIJEM') & (df_trans['k_symbol'] == 'UROK')
n_urok = cond_urok.sum()
df_trans.loc[cond_urok, 'operation'] = 'ABONO_INTERESES'
df_trans.loc[cond_urok, 'tipo_operacion_traducido'] = 'Intereses Ganados / Abono Bancario'
df_trans.loc[cond_urok, 'canal'] = 'Proceso Automatico / Sistema Central'
print(f"   -> Imputadas {n_urok:,} transacciones como 'ABONO_INTERESES' (Sistema Central).")

# Regla 1.2: Si es PRIJEM y k_symbol != 'UROK' o nulo -> Depósito directo en cuenta
cond_prijem_rem = (df_trans['operation'].isna()) & (df_trans['tipo_transaccion'] == 'PRIJEM')
n_prijem_rem = cond_prijem_rem.sum()
df_trans.loc[cond_prijem_rem, 'operation'] = 'VKLAD_DIRECTO'
df_trans.loc[cond_prijem_rem, 'tipo_operacion_traducido'] = 'Ingreso / Deposito en Cuenta'
df_trans.loc[cond_prijem_rem, 'canal'] = 'Ventanilla Bancaria / Abono'
print(f"   -> Imputadas {n_prijem_rem:,} transacciones como 'VKLAD_DIRECTO' (Ventanilla/Abono).")

# Regla 1.3: Cualquier otra operación nula residual
cond_op_residual = df_trans['operation'].isna()
if cond_op_residual.sum() > 0:
    df_trans.loc[cond_op_residual, 'operation'] = 'OPERACION_INTERNA'
    df_trans.loc[cond_op_residual, 'tipo_operacion_traducido'] = 'Movimiento Operativo Interno'
    df_trans.loc[cond_op_residual, 'canal'] = 'Canal Interno'

print(f"   Resultado operación: {df_trans['operation'].isnull().sum()} nulos.")

# ------------------------------------------------------------------------------
# FASE 2: COMPLETITUD DE 'k_symbol' (463,450 nulos) MEDIANTE CRUCES Y HEURÍSTICA
# ------------------------------------------------------------------------------
print("\n3. [FASE 2] Completando 'k_symbol' (463,450 nulos)...")

# Crear columna de categoría traducida y homologada para k_symbol
# Diccionario de conceptos conocidos en checo
dict_ksymbol_trad = {
    'UROK': 'Intereses Bancarios',
    'SLUZBY': 'Comision por Servicios Bancarios',
    'SIPO': 'Servicios del Hogar (Luz/Agua/Gas)',
    'DUCHOD': 'Pension / Jubilacion',
    'POJISTNE': 'Pago de Poliza de Seguros',
    'UVER': 'Cuota de Prestamo Bancario',
    'SANKC. UROK': 'Interes Penalizatorio por Sobregiro',
    'LEASING': 'Arrendamiento / Leasing'
}

# Regla 2.1: Cruce con df_prestamos para detectar cuotas de crédito ocultas
# Extraer diccionario de {id_cuenta: pago_mensual}
prestamos_cuotas = df_prest[['id_cuenta', 'pago_mensual']].dropna().drop_duplicates()
dict_cuotas = dict(zip(prestamos_cuotas['id_cuenta'], prestamos_cuotas['pago_mensual']))

cond_uver_candidato = (
    df_trans['k_symbol'].isna() &
    (df_trans['tipo_transaccion'] == 'VYDAJ') &
    (df_trans['id_cuenta'].isin(dict_cuotas.keys()))
)

# Comparar montos
cuotas_mapeadas = df_trans.loc[cond_uver_candidato, 'id_cuenta'].map(dict_cuotas)
matches_uver = cond_uver_candidato & (np.abs(df_trans['monto_transaccion'] - cuotas_mapeadas) < 0.05)
n_uver = matches_uver.sum()
df_trans.loc[matches_uver, 'k_symbol'] = 'UVER'
print(f"   -> [Cruce Préstamos] Imputadas {n_uver:,} transacciones como cuota de préstamo ('UVER').")

# Regla 2.2: Cruce con df_ordenes para detectar pagos recurrentes (SIPO, Seguros, Leasing)
# Crear mapa de (id_cuenta, monto_orden) -> k_symbol
ord_validas = df_ord[df_ord['k_symbol'].notna() & (df_ord['k_symbol'] != '')][['id_cuenta', 'monto_orden', 'k_symbol']].drop_duplicates()
# Para evitar ambigüedades, tomar órdenes únicas por (id_cuenta, monto_orden)
ord_validas_unicas = ord_validas.drop_duplicates(subset=['id_cuenta', 'monto_orden'])
dict_ordenes = ord_validas_unicas.set_index(['id_cuenta', 'monto_orden'])['k_symbol'].to_dict()

cond_orden_candidata = (df_trans['k_symbol'].isna()) & (df_trans['tipo_transaccion'] == 'VYDAJ')
indices_cand = df_trans[cond_orden_candidata].index
cuentas_montos = list(zip(df_trans.loc[indices_cand, 'id_cuenta'], df_trans.loc[indices_cand, 'monto_transaccion']))
simbolos_orden = [dict_ordenes.get(cm, None) for cm in cuentas_montos]

# Asignar los encontrados
series_simb = pd.Series(simbolos_orden, index=indices_cand)
indices_imputar = series_simb.dropna().index
n_ordenes_imputadas = len(indices_imputar)
df_trans.loc[indices_imputar, 'k_symbol'] = series_simb.loc[indices_imputar]
print(f"   -> [Cruce Órdenes] Imputadas {n_ordenes_imputadas:,} transacciones por coincidencia de órdenes recurrentes.")

# Regla 2.3: Heurística de Fin de Mes para Comisiones Bancarias de Mantenimiento (SLUZBY)
# En el dataset checo, cargos de fin de mes por importes específicos (14.60, 25.00, 30.00, 50.00) son 'SLUZBY'
montos_comision = [14.60, 25.00, 30.00, 50.00, 10.00, 20.00]
cond_sluzby = (
    df_trans['k_symbol'].isna() &
    (df_trans['tipo_transaccion'] == 'VYDAJ') &
    (df_trans['dia'] >= 28) &
    (df_trans['monto_transaccion'].isin(montos_comision))
)
n_sluzby = cond_sluzby.sum()
df_trans.loc[cond_sluzby, 'k_symbol'] = 'SLUZBY'
print(f"   -> [Heurística Fin de Mes] Imputadas {n_sluzby:,} transacciones como comisiones de servicio ('SLUZBY').")

# Regla 2.4: Retiros en Efectivo Ordinarios (Gastos Personales)
cond_retiro_efectivo = (
    df_trans['k_symbol'].isna() &
    (df_trans['operation'].isin(['VYBER', 'VYBER KARTOU']))
)
n_retiros = cond_retiro_efectivo.sum()
df_trans.loc[cond_retiro_efectivo, 'k_symbol'] = 'RETIRO_EFECTIVO'
print(f"   -> [Caja Efectivo] Imputadas {n_retiros:,} transacciones como retiros ordinarios en efectivo.")

# Regla 2.5: Depósitos en Efectivo Ordinarios
cond_dep_efectivo = (
    df_trans['k_symbol'].isna() &
    (df_trans['operation'].isin(['VKLAD', 'VKLAD_DIRECTO']))
)
n_depositos = cond_dep_efectivo.sum()
df_trans.loc[cond_dep_efectivo, 'k_symbol'] = 'DEPOSITO_EFECTIVO'
print(f"   -> [Caja Efectivo] Imputadas {n_depositos:,} transacciones como depósitos ordinarios en efectivo.")

# Regla 2.6: Residual de transferencias salientes sin concepto
cond_transf_saliente = (
    df_trans['k_symbol'].isna() &
    (df_trans['tipo_transaccion'] == 'VYDAJ')
)
n_transf_sal = cond_transf_saliente.sum()
df_trans.loc[cond_transf_saliente, 'k_symbol'] = 'TRANSFERENCIA_EXTERNA'
print(f"   -> [Residual] Imputadas {n_transf_sal:,} transferencias salientes ordinarias.")

# Regla 2.7: Cualquier residual de ingreso restante
cond_residual_ingreso = df_trans['k_symbol'].isna()
n_res_ing = cond_residual_ingreso.sum()
if n_res_ing > 0:
    df_trans.loc[cond_residual_ingreso, 'k_symbol'] = 'INGRESO_ORDINARIO'
    print(f"   -> [Residual] Imputados {n_res_ing:,} ingresos ordinarios restantes.")

print(f"   Resultado k_symbol: {df_trans['k_symbol'].isnull().sum()} nulos.")

# ------------------------------------------------------------------------------
# FASE 3: COMPLETITUD DE 'bank' Y 'account' (760,931 y 782,812 nulos)
# ------------------------------------------------------------------------------
print("\n4. [FASE 3] Completando 'bank' y 'account' (Contrapares operativas)...")

# Regla 3.1: Operaciones físicas en caja/efectivo y cajero
# Cuando el cliente retira o deposita efectivo en ventanilla o ATM, no existe banco contraparte externo
cond_efectivo_caja = df_trans['operation'].isin(['VKLAD', 'VKLAD_DIRECTO', 'VYBER', 'VYBER KARTOU'])
df_trans.loc[cond_efectivo_caja & df_trans['bank'].isna(), 'bank'] = 'BANCO_PROPIO_LOCAL'
df_trans.loc[cond_efectivo_caja & df_trans['account'].isna(), 'account'] = 'CAJA_VENTANILLA_ATM'
print(f"   -> Imputadas contrapartes de caja física ('BANCO_PROPIO_LOCAL' / 'CAJA_VENTANILLA_ATM').")

# Regla 3.2: Procesos automáticos internos (Intereses, Comisiones del Banco)
cond_procesos_internos = df_trans['k_symbol'].isin(['UROK', 'SLUZBY', 'SANKC. UROK']) | (df_trans['operation'] == 'ABONO_INTERESES')
df_trans.loc[cond_procesos_internos & df_trans['bank'].isna(), 'bank'] = 'SISTEMA_CENTRAL_BANCO'
df_trans.loc[cond_procesos_internos & df_trans['account'].isna(), 'account'] = 'TESORERIA_INTERNA'
print(f"   -> Imputadas contrapartes del sistema bancario ('SISTEMA_CENTRAL_BANCO' / 'TESORERIA_INTERNA').")

# Regla 3.3: Transferencias sin banco o cuenta registrada
df_trans['bank'] = df_trans['bank'].fillna('OTRA_ENTIDAD_NO_REGISTRADA')
df_trans['account'] = df_trans['account'].fillna('CUENTA_EXTERNA_NO_REGISTRADA')

print(f"   Resultado bank: {df_trans['bank'].isnull().sum()} nulos.")
print(f"   Resultado account: {df_trans['account'].isnull().sum()} nulos.")

# ------------------------------------------------------------------------------
# FASE 4: ENRIQUECIMIENTO CON 'concepto_movimiento_traducido'
# ------------------------------------------------------------------------------
print("\n5. [FASE 4] Creando columna descriptiva 'concepto_movimiento_traducido'...")

dict_conceptos_completos = {
    'UROK': 'Intereses Ganados en Cuenta',
    'SLUZBY': 'Comisión por Mantenimiento / Servicios',
    'SIPO': 'Servicios Básicos del Hogar',
    'DUCHOD': 'Abono de Pensión / Jubilación',
    'POJISTNE': 'Pago de Póliza de Seguro',
    'UVER': 'Amortización de Cuota de Préstamo',
    'SANKC. UROK': 'Interés Moratorio por Sobregiro',
    'LEASING': 'Cuota de Arrendamiento Financiero (Leasing)',
    'RETIRO_EFECTIVO': 'Retiro en Efectivo (Gastos Personales)',
    'DEPOSITO_EFECTIVO': 'Depósito en Efectivo de Fondos Propios',
    'TRANSFERENCIA_EXTERNA': 'Transferencia Bancaria Saliente',
    'INGRESO_ORDINARIO': 'Ingreso Bancario Ordinario'
}

df_trans['concepto_movimiento_traducido'] = df_trans['k_symbol'].map(dict_conceptos_completos).fillna(df_trans['k_symbol'])

# ------------------------------------------------------------------------------
# FASE 5: VALIDACIÓN FINAL Y EXPORTACIÓN DEL NUEVO ARCHIVO
# ------------------------------------------------------------------------------
print("\n6. [FASE 5] Validación final de nulos en el DataFrame completado:")
nulls_finales = df_trans.isnull().sum()
nulos_totales = nulls_finales.sum()
print(f"   -> NULOS TOTALES RESTANTES: {nulos_totales}")

if nulos_totales == 0:
    print("   [OK] EXITO TOTAL: El DataFrame no contiene ningun valor nulo (100% completitud alcanzada).")
else:
    print("   [ALERTA] Columnas con nulos pendientes:")
    print(nulls_finales[nulls_finales > 0])

# Guardar en archivo NUEVO sin sobrescribir el existente
output_parquet = os.path.join(data_dir, "df_transacciones_completado.parquet")
output_csv_gz = os.path.join(data_dir, "df_transacciones_completado.csv.gz")

print(f"\n7. Guardando nuevo DataFrame en disco (sin reemplazar los existentes)...")
df_trans.to_parquet(output_parquet, index=False, engine='pyarrow')
df_trans.to_csv(output_csv_gz, index=False, compression='gzip', encoding='utf-8-sig')

size_parq = os.path.getsize(output_parquet) / (1024 * 1024)
size_gz = os.path.getsize(output_csv_gz) / (1024 * 1024)

print(f"   -> Guardado en Parquet: {output_parquet} ({size_parq:.2f} MB)")
print(f"   -> Guardado en CSV.GZ:  {output_csv_gz} ({size_gz:.2f} MB)")

# Resumen de distribución final
print("\n--- DISTRIBUCION FINAL DE CONCEPTOS EN df_transacciones_completado ---")
dist = df_trans['concepto_movimiento_traducido'].value_counts()
for cat, cnt in dist.items():
    pct = (cnt / len(df_trans)) * 100
    print(f"   - {cat:<45} : {cnt:>9,} transacciones ({pct:>5.2f}%)")

t1 = time.time()
print(f"\n=== PROCESO COMPLETADO EXITOSAMENTE EN {t1 - t0:.2f} SEGUNDOS ===")
