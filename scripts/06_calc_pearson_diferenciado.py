"""
Script 06: Correlación de Pearson sobre Series Mensuales Diferenciadas (Δx_t).
Calcula la correlación entre flujos mensuales de tesorería de los 5 servicios transaccionales
para eliminar la tendencia determinista (estacionariedad).
"""
import os
import pandas as pd
import numpy as np

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
data_path = os.path.join(base_dir, "dataframes", "df_transacciones_completado.csv.gz")

print("=== SCRIPT 06: CORRELACION TEMPORAL DIFERENCIADA (Delta x_t) ===")
df_tx = pd.read_csv(data_path, compression='gzip', low_memory=False)

concept_map = {
    'amortización de cuota de préstamo': 'PRESTAMO',
    'pago de póliza de seguro': 'SEGURO',
    'servicios básicos del hogar': 'SERVICIOS_HOGAR',
    'retiro en efectivo (gastos personales)': 'TARJETA_DEBITO',
    'transferencia bancaria saliente': 'TRANSF_EXTERNA'
}

df_tx['producto'] = df_tx['concepto_movimiento_traducido'].str.lower().map(concept_map)
df_sub = df_tx.dropna(subset=['producto']).copy()

date_col = [c for c in df_sub.columns if 'fecha' in c or 'date' in c][0]
df_sub['year_month'] = pd.to_datetime(df_sub[date_col]).dt.to_period('M')

# Agregación mensual por montos
amt_monthly = df_sub.groupby(['year_month', 'producto'])['monto_transaccion'].sum().unstack(fill_value=0)
diff_amt = amt_monthly.diff().dropna()

prods = ['PRESTAMO', 'SEGURO', 'SERVICIOS_HOGAR', 'TARJETA_DEBITO', 'TRANSF_EXTERNA']
diff_amt = diff_amt[prods]
corr_diff = diff_amt.corr(method='pearson')

print(f"Total meses evaluados: {len(diff_amt)} (1993 a 1998)")
print("\nMatriz de Correlación sobre Series Mensuales Diferenciadas (Tabla VII-B):")
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 1000)
print(corr_diff.round(4))
