"""
Script 07: Modelos sobre Cartera Crediticia (df_prestamos.csv).
Calcula:
1. Similitud Coseno Numérico entre Plazos Arquetípicos (12, 24, 36, 48, 60 meses) en espacio Z-Score.
2. Análisis de Morosidad por Tramos de Endeudamiento (Regla del 30% vs >50%).
3. Significancia Estadística: Chi-cuadrado con corrección de Yates y Test Exacto de Fisher.
"""
import os
import pandas as pd
import numpy as np
from scipy.stats import chi2_contingency, fisher_exact

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
data_path = os.path.join(base_dir, "dataframes", "df_prestamos.csv")

print("=== SCRIPT 07: MODELOS SOBRE DF_PRESTAMOS ===")
df = pd.read_csv(data_path)
print(f"Total créditos otorgados: {len(df):,}")

# 1. Similitud Coseno Numérico entre Plazos
plazos = [12, 24, 36, 48, 60]
agg = df.groupby('plazo_meses')[['monto_prestamo', 'plazo_meses', 'pago_mensual']].mean()
agg = agg.loc[plazos]

# Estandarización Z-Score
means = agg.mean()
stds = agg.std()
z_agg = (agg - means) / stds

dot = z_agg.dot(z_agg.T).values
norms = np.sqrt(np.diag(dot))
cos_num = dot / np.outer(norms, norms)
df_cos = pd.DataFrame(cos_num, index=[f"{p} meses" for p in plazos], columns=[f"{p} meses" for p in plazos])

print("\n--- 1. SIMILITUD COSENO NUMÉRICO ENTRE PLAZOS (Tabla XII) ---")
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 1000)
print(df_cos.round(4))

# 2. Análisis de Endeudamiento y Mora
print("\n--- 2. TRAMOS DE ENDEUDAMIENTO Y MOROSIDAD (Tabla XIII) ---")
df['ratio_endeudamiento'] = (df['pago_mensual'] / df['salario_distrito']) * 100
df['es_moroso'] = df['estado_prestamo'].isin(['B', 'D']).astype(int)

t1 = df[df['ratio_endeudamiento'] <= 30]
t2 = df[(df['ratio_endeudamiento'] > 30) & (df['ratio_endeudamiento'] <= 50)]
t3 = df[df['ratio_endeudamiento'] > 50]

for name, t in [("≤ 30% (Prudencial)", t1), ("30% - 50% (Riesgo Moderado)", t2), ("> 50% (Sobreendeudamiento)", t3)]:
    n_tot = len(t)
    n_mora = t['es_moroso'].sum()
    pct_mora = (n_mora / n_tot) * 100
    print(f"  Tramo {name:30s}: N={n_tot:>3d} | Morosos={n_mora:>2d} ({pct_mora:>5.2f}%)")

# 3. Pruebas Estadísticas
tbl_ext = [[t1['es_moroso'].sum(), len(t1) - t1['es_moroso'].sum()],
           [t3['es_moroso'].sum(), len(t3) - t3['es_moroso'].sum()]]
chi2_y, p_y, _, _ = chi2_contingency(tbl_ext, correction=True)
odds, p_f = fisher_exact(tbl_ext)

print("\n--- 3. SIGNIFICANCIA ESTADÍSTICA (<=30% vs >50%) ---")
print(f"  Chi-cuadrado con Yates: {chi2_y:.4f} (p = {p_y:.4f})")
print(f"  Test Exacto de Fisher:  Odds Ratio = {odds:.4f} (p = {p_f:.4f})")
