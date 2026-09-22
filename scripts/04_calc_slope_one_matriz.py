"""
Script 04: Matriz Canónica de Desviaciones y Soportes de Slope One (df_transacciones).
Calcula:
1. Ratings implícitos normalizados con transformación logarítmica y escalamiento [1.0, 5.0].
2. Matriz completa de desviaciones medias b(j, i) y soportes conjuntos S(j, i).
3. Predicciones paso a paso para los Clientes #2 y #45.
"""
import os
import pandas as pd
import numpy as np

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
data_path = os.path.join(base_dir, "dataframes", "df_transacciones_completado.csv.gz")

print("=== SCRIPT 04: MATRIZ DE DESVIACIONES Y SOPORTES SLOPE ONE ===")
df_tx = pd.read_csv(data_path, compression='gzip', low_memory=False)

concept_map = {
    'amortización de cuota de préstamo': 'PRESTAMO',
    'pago de póliza de seguro': 'SEGURO',
    'servicios básicos del hogar': 'SERVICIOS_HOGAR',
    'retiro en efectivo (gastos personales)': 'TARJETA_DEBITO',
    'transferencia bancaria saliente': 'TRANSF_EXTERNA'
}

df_tx['producto'] = df_tx['concepto_movimiento_traducido'].str.lower().map(concept_map)
df_sub = df_tx.dropna(subset=['producto'])

counts = df_sub.groupby(['id_cliente', 'producto']).size().reset_index(name='freq')
counts['log_freq'] = np.log1p(counts['freq'])
min_v, max_v = counts['log_freq'].min(), counts['log_freq'].max()
counts['rating'] = 1.0 + 4.0 * (counts['log_freq'] - min_v) / (max_v - min_v)

user_counts = counts.groupby('id_cliente').size()
active_users = user_counts[user_counts >= 2].index
counts = counts[counts['id_cliente'].isin(active_users)].copy()

prods = ['PRESTAMO', 'SEGURO', 'SERVICIOS_HOGAR', 'TARJETA_DEBITO', 'TRANSF_EXTERNA']

# Pivot table: usuarios x productos
R = counts.pivot(index='id_cliente', columns='producto', values='rating')[prods]

# Cálculo de desviaciones b(j, i) y soportes S(j, i)
# b(j, i) = mean(r_{u, j} - r_{u, i})
dev_matrix = pd.DataFrame(0.0, index=prods, columns=prods)
supp_matrix = pd.DataFrame(0, index=prods, columns=prods)

for j in prods:
    for i in prods:
        if j != i:
            valid = R[j].notna() & R[i].notna()
            s = valid.sum()
            supp_matrix.loc[j, i] = s
            if s > 0:
                dev_matrix.loc[j, i] = (R.loc[valid, j] - R.loc[valid, i]).mean()
        else:
            supp_matrix.loc[j, i] = R[j].notna().sum()

print("\n1. MATRIZ DE DESVIACIONES MEDIAS b(j, i) [Tabla V]:")
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 1000)
print(dev_matrix.round(4))

print("\n2. MATRIZ DE SOPORTES CONJUNTOS S(j, i):")
print(supp_matrix)

# 3. Trazabilidad Clientes #2 y #45
print("\n3. TRAZABILIDAD CLIENTES #2 Y #45:")
for cid in [2, 45]:
    r_u = R.loc[cid].dropna()
    print(f"\nCliente #{cid}:")
    print(f"  Productos conocidos: {dict(r_u.round(2))}")
    for target in prods:
        if target not in r_u.index:
            num = sum(supp_matrix.loc[target, i] * (r_u[i] + dev_matrix.loc[target, i]) for i in r_u.index)
            den = sum(supp_matrix.loc[target, i] for i in r_u.index)
            pred = num / den if den > 0 else 0
            print(f"  -> Prediccion para {target:18s}: {pred:.4f} (denominador soporte={den})")
