"""
Script 19: Cálculo de la Matriz de Correlación de Pearson Ítem-a-Ítem sobre Calificaciones Implícitas (df_transacciones)
y Demostración Pedagógica de Cálculo Paso a Paso (Formato Clase Inteligencia de Negocios).
"""
import os
import pandas as pd
import numpy as np

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
data_path = os.path.join(base_dir, "dataframes", "df_transacciones_completado.csv.gz")

print("Cargando datos transaccionales para Pearson Ítem-a-Ítem...")
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

# Conteo y ratings escalados [1.0, 5.0]
counts = df_sub.groupby(['id_cliente', 'producto']).size().reset_index(name='freq')
counts['log_freq'] = np.log1p(counts['freq'])
min_v, max_v = counts['log_freq'].min(), counts['log_freq'].max()
counts['rating'] = 1.0 + 4.0 * (counts['log_freq'] - min_v) / (max_v - min_v)

# Filtro de clientes activos (al menos 2 productos)
user_counts = counts.groupby('id_cliente').size()
active_users = user_counts[user_counts >= 2].index
counts_active = counts[counts['id_cliente'].isin(active_users)].copy()

# Pivot table: usuarios x productos
pivot_ratings = counts_active.pivot(index='id_cliente', columns='producto', values='rating')

print(f"\n1. MATRIZ DE CORRELACIÓN DE PEARSON ÍTEM-A-ÍTEM (3,653 clientes activos):")
corr_matrix = pivot_ratings.corr(method='pearson')
print(corr_matrix.round(4))

# Ejemplo Pedagógico Paso a Paso (Estilo Clase: 4 Clientes muestra)
print("\n2. EJEMPLO PEDAGÓGICO DE CÁLCULO PASO A PASO (SEGURO vs SERVICIOS DEL HOGAR):")
sample_ids = [4, 31, 36, 45]
sample = pivot_ratings.loc[sample_ids, ['SEGURO', 'SERVICIOS_HOGAR']].copy()

r_seg = sample['SEGURO'].values
r_hog = sample['SERVICIOS_HOGAR'].values

mean_seg = np.mean(r_seg)
mean_hog = np.mean(r_hog)

dev_seg = r_seg - mean_seg
dev_hog = r_hog - mean_hog

num = np.sum(dev_seg * dev_hog)
den = np.sqrt(np.sum(dev_seg**2)) * np.sqrt(np.sum(dev_hog**2))
r_pearson = num / den

print(f"Media de Seguro (sobre 4 clientes): {mean_seg:.4f}")
print(f"Media de Hogar (sobre 4 clientes):  {mean_hog:.4f}")
print("\nDesviaciones individuales:")
for i, cid in enumerate(sample_ids):
    print(f"  Cliente #{cid:2d}: r_seg={r_seg[i]:.4f} (dev={dev_seg[i]:+.4f}), r_hog={r_hog[i]:.4f} (dev={dev_hog[i]:+.4f}), prod={dev_seg[i]*dev_hog[i]:+.4f}")

print(f"\nNumerador sum(dev_seg * dev_hog) = {num:.4f}")
print(f"Suma de cuadrados dev_seg^2     = {np.sum(dev_seg**2):.4f} (raiz = {np.sqrt(np.sum(dev_seg**2)):.4f})")
print(f"Suma de cuadrados dev_hog^2     = {np.sum(dev_hog**2):.4f} (raiz = {np.sqrt(np.sum(dev_hog**2)):.4f})")
print(f"Denominador                      = {den:.4f}")
print(f"Coeficiente de Pearson r         = {r_pearson:.4f}")
