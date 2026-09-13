import numpy as np
import pandas as pd
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

# Cargar dataset
df = pd.read_csv('df_cliente_consolidado.csv')

# Filtrar distritos únicos
dist = (
    df[[
        'id_distrito',
        'nombre_distrito',
        'region',
        'poblacion',
        'salario_promedio',
        'tasa_desempleo',
        'tasa_criminalidad',
    ]]
    .drop_duplicates(subset='id_distrito')
    .reset_index(drop=True)
)

# Excluir el distrito 69
resto = dist[dist['id_distrito'] != 69].copy()

# One-Hot Encoding para la columna categórica 'region'
features = pd.get_dummies(
    resto[['poblacion', 'salario_promedio', 'region']], columns=['region']
)

# Escalamiento de variables
X = StandardScaler().fit_transform(features)


# Implementación manual de K-Means
def kmeans_manual(X, k, seed):
  np.random.seed(seed)
  idx = np.random.choice(len(X), k, replace=False)
  centroides = X[idx]

  for _ in range(100):
    d = np.sqrt(((X[:, None, :] - centroides[None, :, :]) ** 2).sum(axis=2))
    asign = np.argmin(d, axis=1)
    nuevos = np.array([
        (
            X[asign == c].mean(axis=0)
            if np.any(asign == c)
            else centroides[c]
        )
        for c in range(k)
    ])
    if np.allclose(nuevos, centroides):
      break
    centroides = nuevos

  inercia = sum(((X[asign == c] - centroides[c]) ** 2).sum() for c in range(k))
  return asign, centroides, inercia


# Evaluación con método del codo e índice de silueta
print(f"{'k':<3} | {'inercia (codo)':<14} | {'silueta (mas alto = mejor)':<25}")
print('-' * 48)

for k in range(2, 11):
  asign, cen, inercia = kmeans_manual(X, k, seed=42)
  sil = silhouette_score(X, asign) if len(set(asign)) > 1 else float('nan')
  print(f'{k:<3} | {inercia:14.1f} | {sil:25.3f}')