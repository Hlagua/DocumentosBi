import os
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Set style
sns.set_theme(style="white", font="DejaVu Sans")
plt.rcParams['font.size'] = 9.5
plt.rcParams['axes.labelsize'] = 10
plt.rcParams['axes.titlesize'] = 11
plt.rcParams['xtick.labelsize'] = 9
plt.rcParams['ytick.labelsize'] = 9

os.makedirs('img/individual', exist_ok=True)

# =============================================================================
# FIGURA 1: SLOPE ONE (Tabla V)
# =============================================================================
def make_fig_1a():
    items = ['PRESTAMO', 'SEGURO', 'SERVICIOS_HOGAR', 'TARJETA_DEBITO', 'TRANSF_EXTERNA']
    # b(j, i)
    devs = np.array([
        [0.0000, -0.5687, -0.5006, -1.1674, -0.6370],
        [+0.5687, 0.0000, -0.0024, -0.4546, +0.1876],
        [+0.5006, +0.0024, 0.0000, -0.4522, +0.0844],
        [+1.1674, +0.4546, +0.4522, 0.0000, +0.3550],
        [+0.6370, -0.1876, -0.0844, -0.3550, 0.0000]
    ])
    supps = np.array([
        [682, 114, 468, 682, 233],
        [114, 532, 532, 532, 531],
        [468, 532, 3365, 3365, 1197],
        [682, 532, 3365, 3653, 1197],
        [233, 531, 1197, 1197, 1197]
    ])
    
    annot = np.empty((5, 5), dtype=object)
    for i in range(5):
        for j in range(5):
            sign = "+" if devs[i, j] > 0 else ""
            annot[i, j] = f"{sign}{devs[i, j]:.4f}\n(S={supps[i, j]})"
            
    fig, ax = plt.subplots(figsize=(7.2, 5.4), dpi=300)
    sns.heatmap(devs, annot=annot, fmt="", cmap="coolwarm", center=0, vmin=-1.2, vmax=1.2,
                xticklabels=items, yticklabels=items, cbar_kws={'label': 'Desviación Media Relativa b(j, i)'},
                linewidths=0.5, linecolor='gray', ax=ax)
    ax.set_title("Matriz de Desviaciones Medias b(j, i) y Soportes S(j, i) - Slope One\n(df_transacciones: 1,056,320 registros)", pad=12, fontweight='bold')
    ax.set_xlabel("Producto Evaluado (i)", labelpad=8, fontweight='bold')
    ax.set_ylabel("Producto a Predecir (j)", labelpad=8, fontweight='bold')
    plt.xticks(rotation=20, ha='right')
    plt.yticks(rotation=0)
    plt.tight_layout()
    fig.savefig('img/individual/fig_1a_slope_one.png', dpi=300)
    plt.close(fig)
    print("Generada: fig_1a_slope_one.png")

# =============================================================================
# FIGURA 2: COSENO AJUSTADO (Tabla VI-B)
# =============================================================================
def make_fig_1b():
    items = ['PRESTAMO', 'SEGURO', 'SERVICIOS_HOGAR', 'TARJETA_DEBITO', 'TRANSF_EXTERNA']
    cos_adj = np.array([
        [1.0000, +0.0229, -0.0003, -0.7507, -0.1433],
        [+0.0229, 1.0000, +0.3360, -0.2791, -0.3107],
        [-0.0003, +0.3360, 1.0000, -0.6001, +0.0877],
        [-0.7507, -0.2791, -0.6001, 1.0000, -0.1687],
        [-0.1433, -0.3107, +0.0877, -0.1687, 1.0000]
    ])
    
    annot = np.empty((5, 5), dtype=object)
    for i in range(5):
        for j in range(5):
            sign = "+" if cos_adj[i, j] > 0 and cos_adj[i, j] < 1.0 else ""
            annot[i, j] = f"{sign}{cos_adj[i, j]:.4f}"
            
    fig, ax = plt.subplots(figsize=(7.0, 5.2), dpi=300)
    sns.heatmap(cos_adj, annot=annot, fmt="", cmap="vlag", center=0, vmin=-0.8, vmax=1.0,
                xticklabels=items, yticklabels=items, cbar_kws={'label': 'Similitud Coseno Ajustado'},
                linewidths=0.5, linecolor='gray', ax=ax)
    ax.set_title("Matriz de Similitud del Coseno Ajustado (Centrado en Medias de Usuario)\n(df_transacciones: 3,653 clientes activos)", pad=12, fontweight='bold')
    plt.xticks(rotation=20, ha='right')
    plt.yticks(rotation=0)
    plt.tight_layout()
    fig.savefig('img/individual/fig_1b_coseno.png', dpi=300)
    plt.close(fig)
    print("Generada: fig_1b_coseno.png")

# =============================================================================
# FIGURA 3: PEARSON TEMPORAL DIFERENCIADO (Tabla VII-B)
# =============================================================================
def make_fig_1c():
    items = ['PRESTAMO', 'SEGURO', 'SERVICIOS_HOGAR', 'TARJETA_DEBITO', 'TRANSF_EXTERNA']
    r_temp = np.array([
        [1.0000, +0.1952, +0.2464, +0.0557, +0.1613],
        [+0.1952, 1.0000, +0.5977, -0.0245, +0.5096],
        [+0.2464, +0.5977, 1.0000, +0.1010, +0.7192],
        [+0.0557, -0.0245, +0.1010, 1.0000, +0.0278],
        [+0.1613, +0.5096, +0.7192, +0.0278, 1.0000]
    ])
    
    annot = np.empty((5, 5), dtype=object)
    for i in range(5):
        for j in range(5):
            sign = "+" if r_temp[i, j] > 0 and r_temp[i, j] < 1.0 else ""
            annot[i, j] = f"{sign}{r_temp[i, j]:.4f}"
            
    fig, ax = plt.subplots(figsize=(7.0, 5.2), dpi=300)
    sns.heatmap(r_temp, annot=annot, fmt="", cmap="coolwarm", center=0, vmin=-0.1, vmax=1.0,
                xticklabels=items, yticklabels=items, cbar_kws={'label': 'Coeficiente r de Pearson'},
                linewidths=0.5, linecolor='gray', ax=ax)
    ax.set_title("Correlación de Pearson sobre Series Mensuales Diferenciadas (Δx_t)\n(df_transacciones: 71 meses estacionarios)", pad=12, fontweight='bold')
    plt.xticks(rotation=20, ha='right')
    plt.yticks(rotation=0)
    plt.tight_layout()
    fig.savefig('img/individual/fig_1c_pearson.png', dpi=300)
    plt.close(fig)
    print("Generada: fig_1c_pearson.png")

# =============================================================================
# FIGURA 4: COSENO BINARIO (Tabla VIII)
# =============================================================================
def make_fig_2a():
    items = ['Arrendamiento', 'Préstamo', 'Seguros', 'Serv. Hogar', 'Sin Espec.']
    cos_bin = np.array([
        [1.0000, 0.0000, 0.1174, 0.1951, 0.1580],
        [0.0000, 1.0000, 0.1975, 0.2936, 0.2633],
        [0.1174, 0.1975, 1.0000, 0.3976, 0.6664],
        [0.1951, 0.2936, 0.3976, 1.0000, 0.5967],
        [0.1580, 0.2633, 0.6664, 0.5967, 1.0000]
    ])
    
    fig, ax = plt.subplots(figsize=(7.0, 5.2), dpi=300)
    sns.heatmap(cos_bin, annot=True, fmt=".4f", cmap="Blues", vmin=0.0, vmax=1.0,
                xticklabels=items, yticklabels=items, cbar_kws={'label': 'Similitud Coseno Binario'},
                linewidths=0.5, linecolor='gray', ax=ax)
    ax.set_title("Similitud del Coseno Binario entre Contratos Domiciliados\n(df_ordenes: 3,758 cuentas con órdenes permanentes)", pad=12, fontweight='bold')
    plt.xticks(rotation=15, ha='right')
    plt.yticks(rotation=0)
    plt.tight_layout()
    fig.savefig('img/individual/fig_2a_coseno_binario.png', dpi=300)
    plt.close(fig)
    print("Generada: fig_2a_coseno_binario.png")

# =============================================================================
# FIGURA 5: ITF FACTORES (Tabla IX)
# =============================================================================
def make_fig_2b():
    cats = ['Servicios Hogar (SIPO)', 'Sin Especificar', 'Cuota de Préstamo', 'Pago de Seguros', 'Arrendamiento / Leasing']
    itf = [0.1105, 1.1432, 1.6566, 1.9550, 2.3998]
    pop = [89.54, 31.88, 19.08, 14.16, 9.07]
    n_cuentas = [3365, 1198, 717, 532, 341]
    
    y = np.arange(len(cats))
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8.5, 4.4), dpi=300, sharey=True)
    
    # Left: ITF Score
    bars1 = ax1.barh(y, itf, color=['#b0bec5', '#78909c', '#42a5f5', '#1e88e5', '#0d47a1'], height=0.55)
    ax1.set_xlabel('Factor ITF ln(N / n_i) - Mayor Penalización a lo Común', fontweight='bold')
    ax1.set_title('Factor de Especificidad ITF', fontweight='bold', pad=8)
    ax1.set_yticks(y)
    ax1.set_yticklabels(cats, fontweight='bold')
    ax1.set_xlim(0, 2.8)
    ax1.grid(axis='x', linestyle='--', alpha=0.5)
    for bar in bars1:
        w = bar.get_width()
        ax1.text(w + 0.05, bar.get_y() + bar.get_height()/2, f"{w:.4f}", va='center', fontsize=9, fontweight='bold')
        
    # Right: Popularity %
    bars2 = ax2.barh(y, pop, color=['#ff7043', '#ffa726', '#ffca28', '#81c784', '#4db6ac'], height=0.55)
    ax2.set_xlabel('Popularidad de Contratación en Cuentas (%)', fontweight='bold')
    ax2.set_title('Popularidad en Cartera (3,758 cuentas)', fontweight='bold', pad=8)
    ax2.set_xlim(0, 100)
    ax2.grid(axis='x', linestyle='--', alpha=0.5)
    for idx, bar in enumerate(bars2):
        w = bar.get_width()
        ax2.text(w + 1.5, bar.get_y() + bar.get_height()/2, f"{w:.1f}% (N={n_cuentas[idx]})", va='center', fontsize=8.5)
        
    plt.suptitle("Ponderación ITF vs Popularidad en Órdenes Permanentes (df_ordenes)", fontsize=11, fontweight='bold', y=1.02)
    plt.tight_layout()
    fig.savefig('img/individual/fig_2b_itf.png', dpi=300, bbox_inches='tight')
    plt.close(fig)
    print("Generada: fig_2b_itf.png")

# =============================================================================
# FIGURA 6: PEARSON ORDENES (Tabla X)
# =============================================================================
def make_fig_2c():
    items = ['Arrendamiento', 'Préstamo', 'Seguros', 'Serv. Hogar', 'Sin Espec.']
    r_ord = np.array([
        [1.0000, -0.1534, +0.0046, -0.2917, -0.0153],
        [-0.1534, 1.0000, +0.0398, -0.4117, +0.0224],
        [+0.0046, +0.0398, 1.0000, +0.1388, +0.5936],
        [-0.2917, -0.4117, +0.1388, 1.0000, +0.2338],
        [-0.0153, +0.0224, +0.5936, +0.2338, 1.0000]
    ])
    
    annot = np.empty((5, 5), dtype=object)
    for i in range(5):
        for j in range(5):
            sign = "+" if r_ord[i, j] > 0 and r_ord[i, j] < 1.0 else ""
            annot[i, j] = f"{sign}{r_ord[i, j]:.4f}"
            
    fig, ax = plt.subplots(figsize=(7.0, 5.2), dpi=300)
    sns.heatmap(r_ord, annot=annot, fmt="", cmap="vlag", center=0, vmin=-0.5, vmax=1.0,
                xticklabels=items, yticklabels=items, cbar_kws={'label': 'Coeficiente r de Pearson'},
                linewidths=0.5, linecolor='gray', ax=ax)
    ax.set_title("Correlación de Pearson en Órdenes Domiciliadas (df_ordenes)\n(r = -0.4117 entre Hogar y Préstamo: Segregación Presupuestaria)", pad=12, fontweight='bold')
    plt.xticks(rotation=15, ha='right')
    plt.yticks(rotation=0)
    plt.tight_layout()
    fig.savefig('img/individual/fig_2c_pearson.png', dpi=300)
    plt.close(fig)
    print("Generada: fig_2c_pearson.png")

# =============================================================================
# FIGURA 7: TF-IDF PRESTAMOS (Tabla XI)
# =============================================================================
def make_fig_3a():
    items = ['P01: Personal', 'P02: Familiar', 'P03: Hipotec', 'P04: Comercial',
             'P05: VidaSalud', 'P06: Desgravam', 'P07: Hogar', 'P08: Leasing']
    tfidf_sim = np.array([
        [1.0000, 0.1611, 0.1257, 0.0909, 0.0409, 0.0000, 0.0244, 0.0251],
        [0.1611, 1.0000, 0.1193, 0.0863, 0.2116, 0.0321, 0.0616, 0.0541],
        [0.1257, 0.1193, 1.0000, 0.1432, 0.0407, 0.1026, 0.0243, 0.0806],
        [0.0909, 0.0863, 0.1432, 1.0000, 0.0000, 0.0000, 0.0000, 0.0507],
        [0.0409, 0.2116, 0.0407, 0.0000, 1.0000, 0.2957, 0.0381, 0.0301],
        [0.0000, 0.0321, 0.1026, 0.0000, 0.2957, 1.0000, 0.0000, 0.0324],
        [0.0244, 0.0616, 0.0243, 0.0000, 0.0381, 0.0000, 1.0000, 0.0234],
        [0.0251, 0.0541, 0.0806, 0.0507, 0.0301, 0.0324, 0.0234, 1.0000]
    ])
    
    fig, ax = plt.subplots(figsize=(7.8, 6.0), dpi=300)
    sns.heatmap(tfidf_sim, annot=True, fmt=".4f", cmap="YlGnBu", vmin=0.0, vmax=0.35,
                xticklabels=items, yticklabels=items, cbar_kws={'label': 'Similitud Coseno TF-IDF'},
                linewidths=0.5, linecolor='gray', ax=ax)
    ax.set_title("Similitud Coseno TF-IDF entre Cláusulas Contractuales de Crédito\n(Resolución de Item Cold Start - Afinidad P01-P02: 0.1611)", pad=12, fontweight='bold')
    plt.xticks(rotation=30, ha='right')
    plt.yticks(rotation=0)
    plt.tight_layout()
    fig.savefig('img/individual/fig_3a_tfidf.png', dpi=300)
    plt.close(fig)
    print("Generada: fig_3a_tfidf.png")

# =============================================================================
# FIGURA 8: COSENO PLAZOS (Tabla XII)
# =============================================================================
def make_fig_3b():
    plazos = ['12 meses', '24 meses', '36 meses', '48 meses', '60 meses']
    cos_plazos = np.array([
        [1.0000, 0.9943, 0.4645, -0.9893, -0.9991],
        [0.9943, 1.0000, 0.5534, -0.9983, -0.9978],
        [0.4645, 0.5534, 1.0000, -0.5879, -0.4967],
        [-0.9893, -0.9983, -0.5879, 1.0000, 0.9934],
        [-0.9991, -0.9978, -0.4967, 0.9934, 1.0000]
    ])
    
    annot = np.empty((5, 5), dtype=object)
    for i in range(5):
        for j in range(5):
            sign = "+" if cos_plazos[i, j] > 0 and cos_plazos[i, j] < 1.0 else ""
            annot[i, j] = f"{sign}{cos_plazos[i, j]:.4f}"
            
    fig, ax = plt.subplots(figsize=(7.0, 5.2), dpi=300)
    sns.heatmap(cos_plazos, annot=annot, fmt="", cmap="coolwarm", center=0, vmin=-1.0, vmax=1.0,
                xticklabels=plazos, yticklabels=plazos, cbar_kws={'label': 'Similitud Coseno Numérico'},
                linewidths=0.5, linecolor='gray', ax=ax)
    ax.set_title("Similitud del Coseno Numérico entre Plazos Arquetípicos de Crédito\n(df_prestamos: [monto, plazo, cuota] estandarizados)", pad=12, fontweight='bold')
    plt.xticks(rotation=15, ha='right')
    plt.yticks(rotation=0)
    plt.tight_layout()
    fig.savefig('img/individual/fig_3b_coseno_plazos.png', dpi=300)
    plt.close(fig)
    print("Generada: fig_3b_coseno_plazos.png")

# =============================================================================
# FIGURA 9: SCORING Y UTILIDAD (Tabla XIII & Chi-cuadrado)
# =============================================================================
def make_fig_3c():
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8.8, 4.6), dpi=300)
    
    # Left: Simulación de ratio de endeudamiento por plazo (100k CZK, salario 10k)
    plazos = ['12 m', '24 m', '36 m', '48 m', '60 m']
    ratios = [86.99, 45.23, 31.34, 24.41, 20.28]
    colors = ['#d32f2f', '#d32f2f', '#f57c00', '#388e3c', '#2e7d32']
    
    bars = ax1.bar(plazos, ratios, color=colors, width=0.55, edgecolor='black', linewidth=0.8)
    ax1.axhline(30.0, color='blue', linestyle='--', linewidth=1.5, label='Umbral Máx. Utilidad (30%)')
    ax1.set_ylabel('Ratio de Endeudamiento (Cuota / Salario %)', fontweight='bold')
    ax1.set_xlabel('Plazo Crediticio Evaluado', fontweight='bold')
    ax1.set_title('Simulación de Esfuerzo Financiero\n(Crédito 100,000 CZK, Salario 10,000 CZK)', fontweight='bold', pad=8)
    ax1.set_ylim(0, 100)
    ax1.grid(axis='y', linestyle=':', alpha=0.6)
    ax1.legend(loc='upper right', frameon=True)
    
    for bar in bars:
        h = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2, h + 1.5, f"{h:.1f}%", ha='center', fontweight='bold', fontsize=9)
        
    # Right: Validación empírica de tasa de mora real (N=682)
    grupos = ['Endeudamiento ≤ 30%\n(N=213)', 'Endeudamiento > 50%\n(N=261)']
    mora = [6.57, 16.86]
    
    bars2 = ax2.bar(grupos, mora, color=['#388e3c', '#d32f2f'], width=0.45, edgecolor='black', linewidth=0.8)
    ax2.set_ylabel('Tasa de Mora Real (Estados B y D, %)', fontweight='bold')
    ax2.set_title('Validación Empírica en Cartera Real\n(χ² = 10.62, p = 0.0011; Fisher p = 0.0007)', fontweight='bold', pad=8)
    ax2.set_ylim(0, 22)
    ax2.grid(axis='y', linestyle=':', alpha=0.6)
    
    for bar in bars2:
        h = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2, h + 0.6, f"{h:.2f}%\n(Mora)", ha='center', fontweight='bold', fontsize=9.5)
        
    plt.suptitle("Evaluación de Reglas de Scoring y Función de Utilidad Financiera (df_prestamos)", fontsize=11, fontweight='bold', y=1.01)
    plt.tight_layout()
    fig.savefig('img/individual/fig_3c_scoring_utilidad.png', dpi=300, bbox_inches='tight')
    plt.close(fig)
    print("Generada: fig_3c_scoring_utilidad.png")

# =============================================================================
# FIGURA 10: ESTEREOTIPOS DEMOGRAFICOS (Tabla XIV)
# =============================================================================
def make_fig_4a():
    arquetipos = [
        'Praga - Joven (<30)',
        'Praga - Adulto (30-50)',
        'Praga - Mayor (>50)',
        'Bohemia - Joven (<30)',
        'Bohemia - Adulto (30-50)',
        'Bohemia - Mayor (>50)',
        'Moravia - Joven (<30)',
        'Moravia - Adulto (30-50)',
        'Moravia - Mayor (>50)'
    ]
    adopcion_prestamo = [14.9, 16.0, 6.6, 12.1, 16.7, 8.8, 15.2, 16.9, 9.3]
    n_clientes = [154, 238, 271, 695, 1013, 1141, 433, 673, 751]
    
    y = np.arange(len(arquetipos))
    fig, ax = plt.subplots(figsize=(7.6, 5.0), dpi=300)
    
    colors = ['#1565c0', '#1976d2', '#42a5f5',
              '#2e7d32', '#388e3c', '#66bb6a',
              '#e65100', '#f57c00', '#ffa726']
    
    bars = ax.barh(y, adopcion_prestamo, color=colors, height=0.6, edgecolor='black', linewidth=0.6)
    ax.axvline(12.7, color='red', linestyle='--', linewidth=1.5, label='Media Global de Cartera (12.7%)')
    
    ax.set_yticks(y)
    ax.set_yticklabels(arquetipos, fontweight='bold')
    ax.set_xlabel('Tasa de Adopción de Créditos (%)', fontweight='bold')
    ax.set_xlim(0, 24)
    ax.set_title('Tasa de Adopción Crediticia por los 9 Estereotipos Demográficos\n(df_cliente_consolidado: 5,369 clientes - Resolución de User Cold Start)', pad=12, fontweight='bold')
    ax.grid(axis='x', linestyle=':', alpha=0.6)
    ax.legend(loc='lower right', frameon=True)
    
    for idx, bar in enumerate(bars):
        w = bar.get_width()
        ax.text(w + 0.3, bar.get_y() + bar.get_height()/2, f"{w:.1f}% (N={n_clientes[idx]})", va='center', fontsize=8.5, fontweight='bold')
        
    ax.invert_yaxis()
    plt.tight_layout()
    fig.savefig('img/individual/fig_4a_estereotipos.png', dpi=300)
    plt.close(fig)
    print("Generada: fig_4a_estereotipos.png")

# =============================================================================
# FIGURA 11: USER TO USER (Tabla XV)
# =============================================================================
def make_fig_4b():
    clients = ['Cliente #2', 'Cliente #19', 'Cliente #47', 'Cliente #107', 'Cliente #212', 'Cliente #321']
    u2u = np.array([
        [1.0000, -0.9455, +0.1478, +0.9902, -0.7514, +0.6442],
        [-0.9455, 1.0000, -0.4089, -0.9640, +0.6056, -0.5522],
        [+0.1478, -0.4089, 1.0000, +0.2432, +0.2647, -0.4172],
        [+0.9902, -0.9640, +0.2432, 1.0000, -0.6532, +0.5598],
        [-0.7514, +0.6056, +0.2647, -0.6532, 1.0000, -0.8420],
        [+0.6442, -0.5522, -0.4172, +0.5598, -0.8420, 1.0000]
    ])
    
    annot = np.empty((6, 6), dtype=object)
    for i in range(6):
        for j in range(6):
            sign = "+" if u2u[i, j] > 0 and u2u[i, j] < 1.0 else ""
            annot[i, j] = f"{sign}{u2u[i, j]:.4f}"
            
    fig, ax = plt.subplots(figsize=(7.2, 5.4), dpi=300)
    sns.heatmap(u2u, annot=annot, fmt="", cmap="coolwarm", center=0, vmin=-1.0, vmax=1.0,
                xticklabels=clients, yticklabels=clients, cbar_kws={'label': 'Similitud Coseno Usuario-Usuario'},
                linewidths=0.5, linecolor='gray', ax=ax)
    ax.set_title("Similitud Coseno Usuario a Usuario entre Titulares Activos\n(df_cliente_consolidado: Gemelos Financieros #2 y #107 con cos = +0.9902)", pad=12, fontweight='bold')
    plt.xticks(rotation=20, ha='right')
    plt.yticks(rotation=0)
    plt.tight_layout()
    fig.savefig('img/individual/fig_4b_user_to_user.png', dpi=300)
    plt.close(fig)
    print("Generada: fig_4b_user_to_user.png")

# =============================================================================
# FIGURA 12: PEARSON PERFIL (Tabla XVI)
# =============================================================================
def make_fig_4c():
    vars_perfil = ['Edad', 'Salario Distrital', 'Saldo Promedio', 'Transacciones (Tx)', 'Órdenes Activas', 'Propensión Crédito']
    r_perfil = np.array([
        [1.0000, -0.0023, -0.2448, -0.0979, -0.0457, -0.1082],
        [-0.0023, 1.0000, +0.0134, +0.0100, +0.0054, -0.0119],
        [-0.2448, +0.0134, 1.0000, +0.2258, +0.0378, +0.2304],
        [-0.0979, +0.0100, +0.2258, 1.0000, +0.4965, +0.2217],
        [-0.0457, +0.0054, +0.0378, +0.4965, 1.0000, +0.3375],
        [-0.1082, -0.0119, +0.2304, +0.2217, +0.3375, 1.0000]
    ])
    
    annot = np.empty((6, 6), dtype=object)
    for i in range(6):
        for j in range(6):
            sign = "+" if r_perfil[i, j] > 0 and r_perfil[i, j] < 1.0 else ""
            annot[i, j] = f"{sign}{r_perfil[i, j]:.4f}"
            
    fig, ax = plt.subplots(figsize=(7.6, 5.6), dpi=300)
    sns.heatmap(r_perfil, annot=annot, fmt="", cmap="vlag", center=0, vmin=-0.3, vmax=1.0,
                xticklabels=vars_perfil, yticklabels=vars_perfil, cbar_kws={'label': 'Coeficiente r de Pearson'},
                linewidths=0.5, linecolor='gray', ax=ax)
    ax.set_title("Matriz de Correlación Multivariante de Perfil Financiero y Demográfico\n(df_cliente_consolidado: r = +0.4965 entre Tx y Órdenes Activas)", pad=12, fontweight='bold')
    plt.xticks(rotation=25, ha='right')
    plt.yticks(rotation=0)
    plt.tight_layout()
    fig.savefig('img/individual/fig_4c_pearson_perfil.png', dpi=300)
    plt.close(fig)
    print("Generada: fig_4c_pearson_perfil.png")

if __name__ == '__main__':
    make_fig_1a()
    make_fig_1b()
    make_fig_1c()
    make_fig_2a()
    make_fig_2b()
    make_fig_2c()
    make_fig_3a()
    make_fig_3b()
    make_fig_3c()
    make_fig_4a()
    make_fig_4b()
    make_fig_4c()
    print("¡Todas las 12 figuras individuales han sido generadas fielmente a partir de 04!")
