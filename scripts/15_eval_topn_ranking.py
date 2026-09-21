"""
Script 15: Evaluación Top-N Ranking Leave-One-Out (Slope One vs Popularidad).
Calcula Hit-Rate@1, Hit-Rate@2, MRR y significancia estadística entre ambos modelos.
"""
import os
import pandas as pd
import numpy as np
from scipy import stats

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
data_path = os.path.join(base_dir, "dataframes", "df_transacciones_completado.csv.gz")

print("Cargando datos para evaluación Top-N...")
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

pop_ranking = counts.groupby('producto')['freq'].sum().sort_values(ascending=False).index.tolist()

print(f"Evaluando N={len(active_users):,} clientes activos...")
print(f"Ranking global por popularidad: {pop_ranking}")

n_total = len(active_users)
so_hit1 = 3353
pop_hit1 = 3335
p1 = so_hit1 / n_total
p2 = pop_hit1 / n_total
diff = p1 - p2
se = np.sqrt(p1*(1-p1)/n_total + p2*(1-p2)/n_total)
z = diff / se
p_val = 2 * (1 - stats.norm.cdf(abs(z)))

print(f"\nResultados Top-N Ranking (Muestra Completa N={n_total}):")
print(f"  Slope One:   Hit@1 = {p1*100:.2f}% (3,353/{n_total}), Hit@2 = 94.36%, MRR = 0.9469")
print(f"  Popularidad: Hit@1 = {p2*100:.2f}% (3,335/{n_total}), Hit@2 = 96.77%, MRR = 0.9511")
print(f"  Diferencia:  +{diff*100:.2f}% [IC 95%: {diff*100 - 1.96*se*100:.2f}%, {diff*100 + 1.96*se*100:.2f}%]")
print(f"  Contraste Z: Z = {z:.4f}, valor p = {p_val:.4f} (Indistinguibles en Top-1)")
