"""
Script 17: Pruebas de Significancia Estadística (Chi-cuadrado y Exacto de Fisher).
Evalúa la dependencia de los 9 estereotipos demográficos y el riesgo en los 3 tramos de endeudamiento.
"""
import os
import pandas as pd
from scipy.stats import chi2_contingency, fisher_exact

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 1. Chi-cuadrado de Estereotipos en df_cliente
print("=== 1. PRUEBA CHI-CUADRADO EN ESTEREOTIPOS DEMOGRÁFICOS ===")
df_cli = pd.read_csv(os.path.join(base_dir, "dataframes", "df_cliente_consolidado_clean.csv"))

def get_region(r):
    r_str = str(r).lower()
    if 'prague' in r_str or 'praga' in r_str: return 'Praga'
    if 'bohemia' in r_str: return 'Bohemia'
    return 'Moravia'

df_cli['macro_region'] = df_cli['region'].apply(get_region)
df_cli['segmento_edad'] = pd.cut(df_cli['edad_corte'], bins=[0, 30, 50, 120], labels=['Joven (<30)', 'Adulto (30-50)', 'Adulto Mayor (>50)'], right=False)
df_cli['arquetipo'] = df_cli['macro_region'] + ' - ' + df_cli['segmento_edad'].astype(str)

ct_cli = pd.crosstab(df_cli['arquetipo'], df_cli['tiene_prestamo'])
chi2_cli, p_cli, dof_cli, _ = chi2_contingency(ct_cli)
print(f"Chi-cuadrado: {chi2_cli:.4f}, gl: {dof_cli}, valor p: {p_cli:.4e}")

# 2. Chi-cuadrado de Tramos de Endeudamiento en df_prestamos
print("\n=== 2. PRUEBA CHI-CUADRADO EN TRAMOS DE ENDEUDAMIENTO (RIESGO) ===")
df_pres = pd.read_csv(os.path.join(base_dir, "dataframes", "df_prestamos.csv"))
df_pres['ratio'] = df_pres['pago_mensual'] / df_pres['salario_distrito'] * 100
df_pres['mora'] = df_pres['estado_prestamo'].isin(['B', 'D']).astype(int)

t1 = df_pres[df_pres['ratio'] <= 30]
t2 = df_pres[(df_pres['ratio'] > 30) & (df_pres['ratio'] <= 50)]
t3 = df_pres[df_pres['ratio'] > 50]

tbl_3 = [[t1['mora'].sum(), len(t1) - t1['mora'].sum()],
         [t2['mora'].sum(), len(t2) - t2['mora'].sum()],
         [t3['mora'].sum(), len(t3) - t3['mora'].sum()]]
chi2_3, p_3, dof_3, _ = chi2_contingency(tbl_3)
print(f"Tabla 3 Tramos (2 gl): Chi-cuadrado = {chi2_3:.4f}, valor p = {p_3:.4f}")

# Contraste de Extremos con y sin Yates
tbl_extremos = [[t1['mora'].sum(), len(t1) - t1['mora'].sum()],
                [t3['mora'].sum(), len(t3) - t3['mora'].sum()]]
chi2_yates, p_yates, _, _ = chi2_contingency(tbl_extremos, correction=True)
chi2_raw, p_raw, _, _ = chi2_contingency(tbl_extremos, correction=False)
odds, p_fisher = fisher_exact(tbl_extremos)
print(f"Extremos (<=30% vs >50%):")
print(f"  Chi2 con corrección de Yates: {chi2_yates:.4f} (p = {p_yates:.4f})")
print(f"  Chi2 sin corrección:          {chi2_raw:.4f} (p = {p_raw:.4f})")
print(f"  Test Exacto de Fisher:        Odds Ratio = {odds:.4f}, valor p = {p_fisher:.4f}")
