"""
Script 18: Cálculo de Similitud Coseno Ajustado (Mean-Centered Cosine).
Calcula la matriz centrando los ratings por la media de cada usuario sobre clientes activos.
"""
import os
import pandas as pd
import numpy as np

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
data_path = os.path.join(base_dir, "dataframes", "df_transacciones_completado.csv.gz")

print("Calculando Coseno Ajustado (Mean-Centered)...")
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

piv = counts.pivot(index='id_cliente', columns='producto', values='rating')

user_means = piv.mean(axis=1)
piv_centered = piv.sub(user_means, axis=0).fillna(0)

dot = piv_centered.T.dot(piv_centered)
norms = np.sqrt(np.diag(dot))
adj_cos = dot / np.outer(norms, norms)

print("\nMatriz de Similitud Coseno Ajustado (Tabla VI-B):")
print(adj_cos.round(4))
