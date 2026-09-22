"""
Script 05: Recomendador sobre Órdenes Domiciliadas (df_ordenes_clean.csv).
Calcula:
1. Factores de Ponderación de Frecuencia Inversa (ITF) sobre cuentas con órdenes.
2. Matriz de Similitud Coseno Binario (5x5).
3. Matriz de Correlación de Pearson sobre Órdenes (5x5).
4. Simulación de Reordenamiento Top-N con y sin penalización ITF.
"""
import os
import pandas as pd
import numpy as np

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
data_path = os.path.join(base_dir, "dataframes", "df_ordenes_clean.csv")

print("=== SCRIPT 05: MODELOS DE RECOMENDACIÓN EN DF_ORDENES ===")
df = pd.read_csv(data_path)
total_cuentas = df['id_cuenta'].nunique()
print(f"Total de cuentas únicas con órdenes: {total_cuentas:,}")

# 1. Ponderación por Frecuencia Inversa (ITF)
cat_map = {
    'SIPO': 'Servicios del Hogar',
    'SIN_ESPECIFICAR': 'Sin Especificar',
    'UVER': 'Cuota de Préstamo',
    'POJISTNE': 'Pago de Seguros',
    'LEASING': 'Arrendamiento / Leasing'
}

cols_order = ['SIPO', 'SIN_ESPECIFICAR', 'UVER', 'POJISTNE', 'LEASING']

print("\n--- 1. FACTORES DE ESPECIFICIDAD ITF (Tabla IX) ---")
itf_data = []
for k in cols_order:
    n_cuentas = df[df['k_symbol'] == k]['id_cuenta'].nunique()
    pct = (n_cuentas / total_cuentas) * 100
    itf = np.log(total_cuentas / n_cuentas)
    itf_data.append({
        'k_symbol': k,
        'categoria': cat_map[k],
        'cuentas': n_cuentas,
        'penetracion_pct': round(pct, 2),
        'factor_itf': round(itf, 4)
    })

df_itf = pd.DataFrame(itf_data)
for idx, r in df_itf.iterrows():
    print(f"  {r['categoria']:25s} (k={r['k_symbol']:15s}): N={r['cuentas']:>4d} ({r['penetracion_pct']:>5.2f}%) | ITF = {r['factor_itf']:.4f}")

# 2. Matriz Binaria Cuenta x Categoría
piv = df.pivot_table(index='id_cuenta', columns='k_symbol', aggfunc='size', fill_value=0)
bin_mat = (piv > 0).astype(int)[cols_order]

# Coseno Binario 5x5
dot = bin_mat.T.dot(bin_mat).values
norms = np.sqrt(np.diag(dot))
cos_bin = dot / np.outer(norms, norms)
df_cos = pd.DataFrame(cos_bin, index=[cat_map[c] for c in cols_order], columns=[cat_map[c] for c in cols_order])

print("\n--- 2. MATRIZ DE SIMILITUD COSENO BINARIO (Tabla VIII, 5x5) ---")
print(df_cos.round(4))

# 3. Correlación de Pearson 5x5
corr_pearson = bin_mat.corr(method='pearson')
df_pearson = pd.DataFrame(corr_pearson.values, index=[cat_map[c] for c in cols_order], columns=[cat_map[c] for c in cols_order])

print("\n--- 3. MATRIZ DE CORRELACIÓN DE PEARSON EN ÓRDENES (Tabla X, 5x5) ---")
print(df_pearson.round(4))

# 4. Simulación comparativa con y sin ITF para cuenta con solo Préstamo (UVER)
print("\n--- 4. SIMULACIÓN COMPARATIVA PARA CUENTA CON PRÉSTAMO ---")
# Similitud base con UVER
uver_sims = df_cos.loc['Cuota de Préstamo']
itf_dict = dict(zip([r['categoria'] for r in itf_data], [r['factor_itf'] for r in itf_data]))

for cat in [c for c in df_cos.index if c != 'Cuota de Préstamo']:
    base_s = uver_sims[cat]
    w = itf_dict[cat]
    itf_s = base_s * w
    print(f"  {cat:25s}: Sim Coseno = {base_s:.4f} x ITF {w:.4f} = Score ITF {itf_s:.4f}")
