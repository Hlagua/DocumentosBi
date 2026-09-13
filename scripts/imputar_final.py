import pandas as pd
import numpy as np

# ==============================================================
# 1. CARGA DE DATOS
# ==============================================================
df = pd.read_csv('df_cliente_consolidado.csv')

# ==============================================================
# 2. TABLA DE DISTRITOS UNICA (77 filas, no 5369 clientes)
# ==============================================================
columnas_distrito = [
    'id_distrito', 'nombre_distrito', 'region',
    'poblacion', 'salario_promedio',
    'tasa_desempleo', 'tasa_criminalidad'
]
dist = df[columnas_distrito].drop_duplicates(subset='id_distrito').reset_index(drop=True)
print(f"Distritos unicos encontrados: {len(dist)}")

objetivo = dist[dist['id_distrito'] == 69].copy()
resto = dist[dist['id_distrito'] != 69].copy()

if objetivo.empty:
    raise ValueError("No se encontro el distrito 69 en el archivo. Revisa la ruta/columna.")

# ==============================================================
# 3. VARIABLES JUSTIFICADAS POR CORRELACION
#    poblacion  -> correlaciona 0.978 con tasa_criminalidad
#    region     -> el norte de Moravia/Bohemia tiene desempleo mucho
#                  mas alto que el resto (region explica desempleo,
#                  poblacion casi no: correlacion de solo -0.10)
# ==============================================================
num_resto = resto[['poblacion', 'salario_promedio']]
num_obj = objetivo[['poblacion', 'salario_promedio']]

media = num_resto.mean()
desv = num_resto.std()
num_resto_z = (num_resto - media) / desv
num_obj_z = (num_obj - media) / desv

cat_resto = pd.get_dummies(resto['region'], prefix='region').astype(float)
cat_obj = pd.get_dummies(objetivo['region'], prefix='region') \
            .reindex(columns=cat_resto.columns, fill_value=0).astype(float)

X = np.hstack([num_resto_z.values, cat_resto.values]).astype(float)
punto_objetivo = np.hstack([num_obj_z.values[0], cat_obj.values[0]]).astype(float)


# ==============================================================
# 4. K-MEANS, UNA SOLA CORRIDA
# ==============================================================
def correr_kmeans(X, k, seed, max_iteraciones=200):
    rng = np.random.RandomState(seed)
    idx_iniciales = rng.choice(len(X), k, replace=False)
    centroides = X[idx_iniciales]

    for iteracion in range(max_iteraciones):
        distancias = np.sqrt(((X[:, np.newaxis, :] - centroides[np.newaxis, :, :]) ** 2).sum(axis=2))
        asignaciones = np.argmin(distancias, axis=1)
        nuevos_centroides = np.array([
            X[asignaciones == c].mean(axis=0) if np.any(asignaciones == c) else centroides[c]
            for c in range(k)
        ])
        if np.allclose(nuevos_centroides, centroides):
            break
        centroides = nuevos_centroides

    inercia = sum(((X[asignaciones == c] - centroides[c]) ** 2).sum() for c in range(k))
    return asignaciones, centroides, inercia


# ==============================================================
# 5. MULTI-REINICIO: 50 corridas con semillas distintas,
#    nos quedamos con la de menor inercia
# ==============================================================
k = 9
N_REINICIOS = 50

mejor_inercia = np.inf
mejor_asignaciones, mejor_centroides = None, None

for seed in range(N_REINICIOS):
    asignaciones, centroides, inercia = correr_kmeans(X, k, seed)
    if inercia < mejor_inercia:
        mejor_inercia = inercia
        mejor_asignaciones = asignaciones
        mejor_centroides = centroides

print(f"Mejor inercia encontrada tras {N_REINICIOS} reinicios: {mejor_inercia:.2f}")
resto['cluster'] = mejor_asignaciones

# ==============================================================
# 6. UBICAR A QUE CLUSTER PERTENECE JESENIK
# ==============================================================
distancias_objetivo = np.sqrt(((mejor_centroides - punto_objetivo) ** 2).sum(axis=1))
cluster_jesenik = np.argmin(distancias_objetivo)
print(f"Jesenik (distrito 69) pertenece al cluster {cluster_jesenik}")

# ==============================================================
# 7. IMPUTACION: mediana del resto de distritos del mismo cluster
# ==============================================================
companeros = resto[resto['cluster'] == cluster_jesenik]
print(f"\nDistritos en el mismo cluster que Jesenik ({len(companeros)}):")
print(companeros[['nombre_distrito', 'region', 'poblacion', 'tasa_desempleo', 'tasa_criminalidad']]
      .to_string(index=False))

desempleo_imputado = companeros['tasa_desempleo'].median()
criminalidad_imputada = companeros['tasa_criminalidad'].median()

print(f"tasa_desempleo    = {desempleo_imputado}")
print(f"tasa_criminalidad = {criminalidad_imputada}")
