"""
Script 14: Validación Cruzada de 5 Pliegues (5-Fold CV) de Slope One, Baselines e Item-kNN.
Evalúa el error absoluto medio (MAE) y RMSE sobre las 9,503 celdas activas.
"""
import os
import pandas as pd
import numpy as np
from sklearn.model_selection import KFold

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
data_path = os.path.join(base_dir, "dataframes", "df_transacciones_completado.csv.gz")

print("Cargando datos transaccionales para 5-fold CV...")
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

users = sorted(counts['id_cliente'].unique())
prods = sorted(counts['producto'].unique())
u_map = {u: i for i, u in enumerate(users)}
p_map = {p: i for i, p in enumerate(prods)}

R = np.full((len(users), len(prods)), np.nan)
for _, r in counts.iterrows():
    R[u_map[r['id_cliente']], p_map[r['producto']]] = r['rating']

obs_u, obs_p = np.where(~np.isnan(R))
indices = np.arange(len(obs_u))

kf = KFold(n_splits=5, shuffle=True, random_state=42)
maes_so = []
maes_user = []
maes_global = []
prod_maes = {p: [] for p in prods}

for fold, (train_idx, test_idx) in enumerate(kf.split(indices)):
    R_tr = np.copy(R)
    R_tr[obs_u[test_idx], obs_p[test_idx]] = np.nan
    
    diff_sum = np.zeros((len(prods), len(prods)))
    diff_cnt = np.zeros((len(prods), len(prods)))
    for i in range(len(prods)):
        for j in range(len(prods)):
            if i != j:
                mask = ~np.isnan(R_tr[:, i]) & ~np.isnan(R_tr[:, j])
                diff_cnt[i, j] = np.sum(mask)
                if diff_cnt[i, j] > 0:
                    diff_sum[i, j] = np.sum(R_tr[mask, i] - R_tr[mask, j])
    dev = np.divide(diff_sum, diff_cnt, out=np.zeros_like(diff_sum), where=diff_cnt > 0)
    
    preds_so, preds_u, actuals = [], [], []
    p_errs = {p: [] for p in prods}
    g_mean = np.nanmean(R_tr)
    
    for idx in test_idx:
        u = obs_u[idx]
        p = obs_p[idx]
        act = R[u, p]
        
        rated = np.where(~np.isnan(R_tr[u, :]))[0]
        rated = rated[rated != p]
        
        if len(rated) > 0 and np.sum(diff_cnt[p, rated]) > 0:
            w = diff_cnt[p, rated]
            vals = R_tr[u, rated] + dev[p, rated]
            pred = np.sum(vals * w) / np.sum(w)
        else:
            pred = np.nanmean(R_tr[u, :])
            if np.isnan(pred): pred = g_mean
            
        u_mean = np.nanmean(R_tr[u, :])
        if np.isnan(u_mean): u_mean = g_mean
        
        preds_so.append(pred)
        preds_u.append(u_mean)
        actuals.append(act)
        p_errs[prods[p]].append(abs(pred - act))
        
    maes_so.append(np.mean(np.abs(np.array(preds_so) - np.array(actuals))))
    maes_user.append(np.mean(np.abs(np.array(preds_u) - np.array(actuals))))
    maes_global.append(np.mean(np.abs(g_mean - np.array(actuals))))
    for p in prods:
        if len(p_errs[p]) > 0:
            prod_maes[p].append(np.mean(p_errs[p]))

print(f"Resultados 5-Fold CV (N={len(indices)}):")
print(f"  Media Global: MAE = {np.mean(maes_global):.4f}")
print(f"  Media Usuario: MAE = {np.mean(maes_user):.4f}")
print(f"  Slope One:     MAE = {np.mean(maes_so):.4f} +- {np.std(maes_so):.4f}")
print("\nMAE por producto:")
for p in prods:
    print(f"  {p:15s}: {np.mean(prod_maes[p]):.4f} +- {np.std(prod_maes[p]):.4f}")
