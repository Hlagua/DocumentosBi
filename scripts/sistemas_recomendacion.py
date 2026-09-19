import os
import time
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

# Configuración visual para publicaciones académicas
plt.rcParams['font.sans-serif'] = 'DejaVu Sans'
plt.rcParams['axes.edgecolor'] = '#333333'
plt.rcParams['axes.linewidth'] = 0.8

print("=== INICIANDO PIPELINE DE SISTEMAS DE RECOMENDACIÓN ===")
t0 = time.time()

base_dir = r"C:\Users\henry\.gemini\antigravity\scratch\DocumentosBi"
data_dir = os.path.join(base_dir, "dataframes")
img_dir = os.path.join(base_dir, "img")
os.makedirs(img_dir, exist_ok=True)

# 1. Cargar DataFrames limpios
print("\n1. Cargando DataFrames limpios...")
df_clientes = pd.read_csv(os.path.join(data_dir, "df_cliente_consolidado_clean.csv"))
df_ordenes = pd.read_csv(os.path.join(data_dir, "df_ordenes_clean.csv"))
df_trans = pd.read_csv(os.path.join(data_dir, "df_transacciones_completado.csv.gz"))

print(f"   -> Clientes: {len(df_clientes):,} filas")
print(f"   -> Órdenes: {len(df_ordenes):,} filas")
print(f"   -> Transacciones: {len(df_trans):,} filas")

# 2. Construcción de la Matriz de Interacción Usuario-Producto (Ratings 1.0 a 5.0)
print("\n2. Construyendo Matriz de Interacción Cliente x Producto Financiero...")

# Definir los 6 productos financieros clave
productos = ['PRESTAMO', 'SEGURO', 'SERVICIOS_HOGAR', 'LEASING', 'TARJETA', 'TRANSF_EXTERNA']

# Mapear transacciones por concepto y cliente
trans_counts = df_trans.groupby(['id_cliente', 'k_symbol']).size().unstack(fill_value=0)

# Mapear tenencia de órdenes
ordenes_counts = df_ordenes.groupby(['id_cliente', 'k_symbol']).size().unstack(fill_value=0)

# Mapear tarjetas
tarjetas_cliente = df_trans[df_trans['operation'] == 'VYBER KARTOU'].groupby('id_cliente').size()

# Crear matriz base de clientes
matriz_ratings = pd.DataFrame(index=df_clientes['id_cliente'], columns=productos, dtype=float)

# Llenar ratings para cada producto basado en intensidad de uso
# A) PRESTAMO (UVER)
prestamo_users = df_clientes[df_clientes['tiene_prestamo'] == True]['id_cliente']
matriz_ratings.loc[prestamo_users, 'PRESTAMO'] = 4.0
if 'UVER' in trans_counts.columns:
    uver_freq = trans_counts['UVER']
    for uid in prestamo_users:
        freq = uver_freq.get(uid, 0)
        matriz_ratings.loc[uid, 'PRESTAMO'] = min(5.0, 3.5 + np.log1p(freq) * 0.4)

# B) SEGURO (POJISTNE)
if 'POJISTNE' in trans_counts.columns:
    seguro_freq = trans_counts['POJISTNE']
    for uid, cnt in seguro_freq[seguro_freq > 0].items():
        if uid in matriz_ratings.index:
            matriz_ratings.loc[uid, 'SEGURO'] = min(5.0, 2.5 + np.log1p(cnt) * 0.6)
if 'POJISTNE' in ordenes_counts.columns:
    for uid in ordenes_counts[ordenes_counts['POJISTNE'] > 0].index:
        if uid in matriz_ratings.index and pd.isna(matriz_ratings.loc[uid, 'SEGURO']):
            matriz_ratings.loc[uid, 'SEGURO'] = 3.5

# C) SERVICIOS HOGAR (SIPO)
if 'SIPO' in trans_counts.columns:
    sipo_freq = trans_counts['SIPO']
    for uid, cnt in sipo_freq[sipo_freq > 0].items():
        if uid in matriz_ratings.index:
            matriz_ratings.loc[uid, 'SERVICIOS_HOGAR'] = min(5.0, 2.0 + np.log1p(cnt) * 0.6)

# D) LEASING
if 'LEASING' in trans_counts.columns:
    leasing_freq = trans_counts['LEASING']
    for uid, cnt in leasing_freq[leasing_freq > 0].items():
        if uid in matriz_ratings.index:
            matriz_ratings.loc[uid, 'LEASING'] = min(5.0, 3.0 + np.log1p(cnt) * 0.5)
if 'LEASING' in ordenes_counts.columns:
    for uid in ordenes_counts[ordenes_counts['LEASING'] > 0].index:
        if uid in matriz_ratings.index and pd.isna(matriz_ratings.loc[uid, 'LEASING']):
            matriz_ratings.loc[uid, 'LEASING'] = 3.8

# E) TARJETA
for uid, cnt in tarjetas_cliente.items():
    if uid in matriz_ratings.index:
        matriz_ratings.loc[uid, 'TARJETA'] = min(5.0, 2.5 + np.log1p(cnt) * 0.7)

# F) TRANSFERENCIA EXTERNA
if 'TRANSFERENCIA_EXTERNA' in trans_counts.columns:
    transf_freq = trans_counts['TRANSFERENCIA_EXTERNA']
    for uid, cnt in transf_freq[transf_freq > 0].items():
        if uid in matriz_ratings.index:
            matriz_ratings.loc[uid, 'TRANSF_EXTERNA'] = min(5.0, 2.0 + np.log1p(cnt) * 0.7)

print("   -> Matriz Usuario-Producto construida exitosamente:")
print(f"      Dimensiones: {matriz_ratings.shape[0]:,} clientes x {matriz_ratings.shape[1]} productos.")
print("      Valores no nulos por producto:")
for p in productos:
    print(f"      * {p:<20}: {matriz_ratings[p].notna().sum():>5,} clientes")

# ------------------------------------------------------------------------------
# FIGURA 1: SISTEMA DEMOGRÁFICO (Clustering K-Means & Arquetipos de Clientes)
# ------------------------------------------------------------------------------
print("\n3. [SISTEMA DEMOGRÁFICO] Entrenando K-Means y generando Figura 1...")
features_demog = ['edad_corte', 'salario_promedio', 'poblacion', 'saldo_promedio']
X_demog = df_clientes[features_demog].fillna(df_clientes[features_demog].median())
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X_demog)

kmeans = KMeans(n_clusters=4, random_state=42, n_init=10)
df_clientes['cluster_demografico'] = kmeans.fit_predict(X_scaled)

arquetipos = {
    0: "Clúster 1: Adultos Ahorradores (Saldo Alto, Salario Medio)",
    1: "Clúster 2: Jóvenes Urbanos (Salario Alto, Praga/Urbano)",
    2: "Clúster 3: Perfil Estándar (Ingreso Medio, Saldo Moderado)",
    3: "Clúster 4: Adultos Mayores Rurales (Baja Criminalidad/Población)"
}

fig, ax = plt.subplots(figsize=(10, 6), dpi=300)
colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']

for c_id in range(4):
    sub = df_clientes[df_clientes['cluster_demografico'] == c_id]
    ax.scatter(sub['edad_corte'], sub['salario_promedio'],
               label=f"{arquetipos[c_id]} (n={len(sub):,})",
               color=colors[c_id], alpha=0.65, s=28, edgecolors='none')

centers_orig = scaler.inverse_transform(kmeans.cluster_centers_)
ax.scatter(centers_orig[:, 0], centers_orig[:, 1], c='black', marker='X', s=160,
           linewidths=1.5, edgecolors='white', label='Centroides de Clúster', zorder=5)

ax.set_title("Sistema de Recomendación Demográfico: Segmentación de Clientes (K-Means)\nEmparejamiento entre Estereotipo Sociodemográfico y Cartera de Productos",
             fontsize=12, fontweight='bold', pad=15)
ax.set_xlabel("Edad del Cliente (Años al Corte de 1998)", fontsize=10, fontweight='bold')
ax.set_ylabel("Salario Promedio del Distrito (CZK)", fontsize=10, fontweight='bold')
ax.grid(True, linestyle='--', alpha=0.4)
ax.legend(loc='upper left', frameon=True, facecolor='white', framealpha=0.9, fontsize=8)
plt.tight_layout()

fig1_path = os.path.join(img_dir, "fig_01_sistema_demografico_clusters.png")
plt.savefig(fig1_path, dpi=300)
plt.close()
print(f"   -> Guardada: {fig1_path}")

# ------------------------------------------------------------------------------
# FIGURA 2: SISTEMA COLABORATIVO - SLOPE ONE (Lemire et al., 2005)
# ------------------------------------------------------------------------------
print("\n4. [SISTEMA COLABORATIVO] Calculando Slope One y generando Figura 2...")

# Calcular matriz de diferencias y matriz de conteos
diff_matrix = pd.DataFrame(0.0, index=productos, columns=productos)
count_matrix = pd.DataFrame(0, index=productos, columns=productos)

for p1 in productos:
    for p2 in productos:
        if p1 != p2:
            valid_mask = matriz_ratings[p1].notna() & matriz_ratings[p2].notna()
            cnt = valid_mask.sum()
            count_matrix.loc[p1, p2] = cnt
            if cnt > 0:
                diff_matrix.loc[p1, p2] = (matriz_ratings.loc[valid_mask, p1] - matriz_ratings.loc[valid_mask, p2]).mean()

# Función de predicción Slope One
def predecir_slope_one(cliente_id):
    ratings_u = matriz_ratings.loc[cliente_id].dropna()
    predicciones = {}
    for target in productos:
        if target not in ratings_u.index:
            num = 0.0
            den = 0
            for item, r_i in ratings_u.items():
                c = count_matrix.loc[target, item]
                if c > 0:
                    d = diff_matrix.loc[target, item]
                    num += c * (r_i + d)
                    den += c
            if den > 0:
                predicciones[target] = round(num / den, 2)
            else:
                predicciones[target] = np.nan
    return predicciones

# Generar tabla visual de diferencias Slope One y predicciones
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6), dpi=300, gridspec_kw={'width_ratios': [1.2, 1]})

# Matriz de diferencias b_{i,j}
sns.heatmap(diff_matrix, annot=True, fmt=".2f", cmap="vlag", center=0, cbar=True,
            ax=ax1, linewidths=0.5, annot_kws={"size": 9, "weight": "bold"})
ax1.set_title("Matriz de Desviaciones Medias (b_i,j)\nSlope One: f(x) = x + b", fontsize=11, fontweight='bold', pad=10)
ax1.set_xticklabels(productos, rotation=35, ha='right', fontsize=8)
ax1.set_yticklabels(productos, rotation=0, fontsize=8)

# Simular predicciones para 3 clientes muestra
clientes_muestra = [2, 19, 45]
tabla_pred_data = []
for cid in clientes_muestra:
    preds = predecir_slope_one(cid)
    prods_actuales = list(matriz_ratings.loc[cid].dropna().index)
    top_rec = sorted(preds.items(), key=lambda x: x[1], reverse=True)[:2]
    top_str = ", ".join([f"{k} ({v})" for k, v in top_rec])
    tabla_pred_data.append([f"Cliente {cid}", ", ".join(prods_actuales[:2]), top_str])

ax2.axis('off')
tabla_cols = ["ID Cliente", "Productos Actuales", "Top-2 Recomendados (Score)"]
tbl = ax2.table(cellText=tabla_pred_data, colLabels=tabla_cols, cellLoc='center', loc='center')
tbl.auto_set_font_size(False)
tbl.set_fontsize(9)
tbl.scale(1.1, 2.2)
for (row, col), cell in tbl.get_celld().items():
    if row == 0:
        cell.set_facecolor('#2c3e50')
        cell.set_text_props(color='white', weight='bold')
    else:
        cell.set_facecolor('#ecf0f1' if row % 2 == 0 else '#ffffff')

ax2.set_title("Inferencia Slope One: Proyección de Calificaciones\n(Clientes Muestra del Banco)", fontsize=11, fontweight='bold', pad=10)
plt.tight_layout()

fig2_path = os.path.join(img_dir, "fig_02_slope_one_desviaciones_prediccion.png")
plt.savefig(fig2_path, dpi=300)
plt.close()
print(f"   -> Guardada: {fig2_path}")

# ------------------------------------------------------------------------------
# FIGURA 3: SISTEMA COLABORATIVO - CORRELACIÓN DE PEARSON (Diapositiva 11)
# ------------------------------------------------------------------------------
print("\n5. [SISTEMA COLABORATIVO] Calculando Correlación de Pearson y generando Figura 3...")

# Correlación de Pearson sobre productos (centrado en la media)
pearson_corr = matriz_ratings.corr(method='pearson')

fig, ax = plt.subplots(figsize=(9, 7), dpi=300)
mask = np.triu(np.ones_like(pearson_corr, dtype=bool), k=1)
sns.heatmap(pearson_corr, annot=True, fmt=".3f", cmap="coolwarm", vmin=-1.0, vmax=1.0,
            center=0, square=True, linewidths=0.7, cbar_kws={"shrink": 0.8, "label": "Coeficiente de Pearson (r)"},
            ax=ax, annot_kws={"size": 10, "weight": "bold"})

ax.set_title("Sistema de Recomendación Colaborativo: Correlación de Pearson\nPatrones de Afinidad Lineal y Contratación Simultánea entre Productos",
             fontsize=11, fontweight='bold', pad=15)
ax.set_xticklabels(productos, rotation=35, ha='right', fontsize=9)
ax.set_yticklabels(productos, rotation=0, fontsize=9)
plt.tight_layout()

fig3_path = os.path.join(img_dir, "fig_03_correlacion_pearson_heatmap.png")
plt.savefig(fig3_path, dpi=300)
plt.close()
print(f"   -> Guardada: {fig3_path}")

# ------------------------------------------------------------------------------
# FIGURA 4: SISTEMA COLABORATIVO - SIMILITUD DE COSENO (Diapositiva 11)
# ------------------------------------------------------------------------------
print("\n6. [SISTEMA COLABORATIVO] Calculando Similitud de Coseno y generando Figura 4...")

# Rellenar con 0 para producto punto en espacio euclidiano
matriz_imputada_cero = matriz_ratings.fillna(0.0)
dot_product = matriz_imputada_cero.T.dot(matriz_imputada_cero)
norms = np.linalg.norm(matriz_imputada_cero, axis=0)
norm_matrix = np.outer(norms, norms)
norm_matrix[norm_matrix == 0] = 1e-9
coseno_sim = pd.DataFrame(dot_product / norm_matrix, index=productos, columns=productos)

fig, ax = plt.subplots(figsize=(9, 7), dpi=300)
sns.heatmap(coseno_sim, annot=True, fmt=".3f", cmap="YlGnBu", vmin=0.0, vmax=1.0,
            square=True, linewidths=0.7, cbar_kws={"shrink": 0.8, "label": "Similitud Coseno (cos θ)"},
            ax=ax, annot_kws={"size": 10, "weight": "bold"})

ax.set_title("Sistema de Recomendación Colaborativo: Similitud de Coseno\nProximidad Angular entre Vectores de Consumo de Productos Financieros",
             fontsize=11, fontweight='bold', pad=15)
ax.set_xticklabels(productos, rotation=35, ha='right', fontsize=9)
ax.set_yticklabels(productos, rotation=0, fontsize=9)
plt.tight_layout()

fig4_path = os.path.join(img_dir, "fig_04_similitud_coseno_heatmap.png")
plt.savefig(fig4_path, dpi=300)
plt.close()
print(f"   -> Guardada: {fig4_path}")

# ------------------------------------------------------------------------------
# FIGURA 5: SISTEMA BASADO EN CONTENIDO - ITEM-TO-ITEM & ITF (Diapositivas 15-18)
# ------------------------------------------------------------------------------
print("\n7. [SISTEMA CONTENIDO / ÍTEMS] Calculando Item-to-Item con ITF y generando Figura 5...")

# A) Matriz binaria de adquisiciones (0 y 1) estilo Amazon (Linden et al., 2003)
matriz_binaria = (matriz_ratings.notna()).astype(int)

# B) Cálculo de Frecuencia Inversa de Ítems (ITF)
N_total = len(matriz_binaria)
n_items = matriz_binaria.sum()
itf_weights = np.log(N_total / n_items)

# Matriz Item-to-Item Coseno Binario
dot_bin = matriz_binaria.T.dot(matriz_binaria)
norms_bin = np.linalg.norm(matriz_binaria, axis=0)
norm_bin_matrix = np.outer(norms_bin, norms_bin)
norm_bin_matrix[norm_bin_matrix == 0] = 1e-9
item_to_item_sim = pd.DataFrame(dot_bin / norm_bin_matrix, index=productos, columns=productos)

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6), dpi=300, gridspec_kw={'width_ratios': [1.1, 1]})

# Mapa de calor de Coseno Binario Amazon
sns.heatmap(item_to_item_sim, annot=True, fmt=".2f", cmap="Blues", vmin=0, vmax=1,
            square=True, ax=ax1, linewidths=0.5, annot_kws={"size": 9, "weight": "bold"})
ax1.set_title("A. Matriz Item-to-Item de Amazon (Linden 2003)\nSimilitud Coseno sobre Adquisiciones Binarias (0/1)",
              fontsize=10, fontweight='bold', pad=10)
ax1.set_xticklabels(productos, rotation=35, ha='right', fontsize=8)
ax1.set_yticklabels(productos, rotation=0, fontsize=8)

# Gráfico de barras de ITF vs Popularidad
y_pos = np.arange(len(productos))
ax2_twin = ax2.twinx()

bars1 = ax2.barh(y_pos - 0.2, n_items.values, height=0.35, color='#34495e', label='Popularidad (# Clientes)')
bars2 = ax2_twin.barh(y_pos + 0.2, itf_weights.values, height=0.35, color='#e67e22', label='Peso ITF (Especificidad)')

ax2.set_yticks(y_pos)
ax2.set_yticklabels(productos, fontsize=9)
ax2.set_xlabel("Número Total de Clientes con el Producto", color='#34495e', fontweight='bold', fontsize=9)
ax2_twin.set_xlabel("Peso ITF = ln(N / n_i) [Mayor = Más Especializado]", color='#e67e22', fontweight='bold', fontsize=9)
ax2.set_title("B. Ponderación por Frecuencia Inversa (ITF)\nPenalización de Comodines vs. Premiación de Especializados",
              fontsize=10, fontweight='bold', pad=10)

# Unir leyendas
lines1, labels1 = ax2.get_legend_handles_labels()
lines2, labels2 = ax2_twin.get_legend_handles_labels()
ax2.legend(lines1 + lines2, labels1 + labels2, loc='lower right', fontsize=8, framealpha=0.9)
plt.tight_layout()

fig5_path = os.path.join(img_dir, "fig_05_item_to_item_itf_pesos.png")
plt.savefig(fig5_path, dpi=300)
plt.close()
print(f"   -> Guardada: {fig5_path}")

# ------------------------------------------------------------------------------
# FIGURA 6: CUADRO COMPARATIVO E INFERENCIA HÍBRIDA
# ------------------------------------------------------------------------------
print("\n8. [SISTEMA HÍBRIDO] Generando Cuadro Comparativo de Inferencia (Figura 6)...")

# Funciones de recomendación para cada técnica
def top_rec_pearson(cid, top_n=2):
    user_p = matriz_ratings.loc[cid].dropna()
    cands = [p for p in productos if p not in user_p.index]
    scores = {}
    for c in cands:
        sims = pearson_corr.loc[c, user_p.index].dropna()
        if len(sims) > 0 and sims.sum() > 0:
            scores[c] = round((user_p * sims).sum() / sims.sum(), 2)
        else:
            scores[c] = round(matriz_ratings[c].mean(), 2)
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_n]

def top_rec_coseno(cid, top_n=2):
    user_p = matriz_ratings.loc[cid].dropna()
    cands = [p for p in productos if p not in user_p.index]
    scores = {}
    for c in cands:
        sims = coseno_sim.loc[c, user_p.index]
        scores[c] = round((user_p * sims).sum() / (sims.sum() + 1e-9), 2)
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_n]

def top_rec_itf(cid, top_n=2):
    user_p = matriz_ratings.loc[cid].dropna()
    cands = [p for p in productos if p not in user_p.index]
    scores = {}
    for c in cands:
        sim_base = item_to_item_sim.loc[c, user_p.index].mean() if len(user_p) > 0 else 0.5
        scores[c] = round(sim_base * itf_weights[c] * 2.0, 2)
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_n]

clientes_eval = [2, 19, 45, 102]
filas_tabla = []

for cid in clientes_eval:
    c_info = df_clientes[df_clientes['id_cliente'] == cid].iloc[0]
    p_actuales = list(matriz_ratings.loc[cid].dropna().index)
    
    # Inferencia de los 4 métodos
    rec_demog = "PRESTAMO, LEASING" if c_info['cluster_demografico'] in [0, 1] else "SERVICIOS_HOGAR, SEGURO"
    rec_slope = ", ".join([f"{k}" for k, v in sorted(predecir_slope_one(cid).items(), key=lambda x: x[1], reverse=True)[:2]])
    rec_pear = ", ".join([f"{k}" for k, v in top_rec_pearson(cid, 2)])
    rec_cos = ", ".join([f"{k}" for k, v in top_rec_coseno(cid, 2)])
    rec_itf = ", ".join([f"{k}" for k, v in top_rec_itf(cid, 2)])
    
    filas_tabla.append([
        f"Cliente #{cid}\n(Edad {int(c_info['edad_corte'])})",
        "\n".join(p_actuales[:2]),
        rec_demog,
        rec_slope,
        rec_pear,
        rec_cos,
        rec_itf
    ])

fig, ax = plt.subplots(figsize=(15, 6), dpi=300)
ax.axis('off')

encabezados = [
    "Cliente",
    "Productos\nPoseídos",
    "Demográfico\n(K-Means)",
    "Slope One\n(Lemire)",
    "Correlación\n(Pearson)",
    "Similitud\n(Coseno)",
    "Contenido\n(Amazon + ITF)"
]

t_comp = ax.table(cellText=filas_tabla, colLabels=encabezados, cellLoc='center', loc='center')
t_comp.auto_set_font_size(False)
t_comp.set_fontsize(8.5)
t_comp.scale(1.0, 2.5)

for (row, col), cell in t_comp.get_celld().items():
    if row == 0:
        cell.set_facecolor('#1a252f')
        cell.set_text_props(color='white', weight='bold')
    else:
        if col in [2]:
            cell.set_facecolor('#e8f8f5' if row % 2 == 0 else '#ffffff')
        elif col in [3, 4, 5]:
            cell.set_facecolor('#ebf5fb' if row % 2 == 0 else '#ffffff')
        elif col in [6]:
            cell.set_facecolor('#fef9e7' if row % 2 == 0 else '#ffffff')
        else:
            cell.set_facecolor('#f8f9f9' if row % 2 == 0 else '#ffffff')

ax.set_title("Cuadro Comparativo de Inferencia Real: Evaluación Cruzada de los Sistemas de Recomendación\n(Demográfico, Colaborativo con Slope One / Pearson / Coseno, y Contenido con ITF)",
             fontsize=12, fontweight='bold', pad=15)
plt.tight_layout()

fig6_path = os.path.join(img_dir, "fig_06_cuadro_comparativo_recomendaciones.png")
plt.savefig(fig6_path, dpi=300)
plt.close()
print(f"   -> Guardada: {fig6_path}")

t1 = time.time()
print(f"\n=== PIPELINE DE RECOMENDACIÓN FINALIZADO EN {t1 - t0:.2f} SEGUNDOS ===")
