import os
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_theme(style="white", font="DejaVu Sans")
plt.rcParams['font.size'] = 9.0

# =============================================================================
# FIGURA 13: DESCARTE EMPÍRICO (fig_05_descarte_empirico_comparativa.png)
# =============================================================================
def generate_fig_13():
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.0, 5.2), dpi=300)
    
    # Panel A: Matriz Cruda Descartada
    cats_a = ['Egreso / Gasto', 'Ingreso / Dep.', 'Intereses Gan.', 'Retiro Efectivo']
    mat_a = np.array([
        [1.0000, 0.9610, 0.9339, 0.9542],
        [0.9610, 1.0000, 0.9412, 0.9488],
        [0.9339, 0.9412, 1.0000, 0.9385],
        [0.9542, 0.9488, 0.9385, 1.0000]
    ])
    
    sns.heatmap(mat_a, annot=True, fmt=".4f", cmap="Reds", vmin=0.90, vmax=1.00,
                xticklabels=cats_a, yticklabels=cats_a, cbar_kws={'label': 'Similitud Coseno Crudo'},
                linewidths=0.6, linecolor='gray', ax=ax1)
    ax1.set_title("A. Matriz Transaccional Cruda (DESCARTADA)\nColapso en Hiper-Octante Positivo [0.9339, 0.9610]\nVarianza σ² = 0.00009 (Incapaz de Discriminar)",
                  fontweight='bold', pad=10, color='#b71c1c')
    ax1.tick_params(axis='x', rotation=20)
    ax1.tick_params(axis='y', rotation=0)
    
    # Panel B: Matriz de Órdenes Refinada Adoptada (Tabla 8)
    cats_b = ['Leasing', 'Préstamo', 'Seguros', 'Hogar', 'Sin Espec.']
    mat_b = np.array([
        [1.0000, 0.0000, 0.1174, 0.1951, 0.1580],
        [0.0000, 1.0000, 0.1975, 0.2936, 0.2633],
        [0.1174, 0.1975, 1.0000, 0.3976, 0.6664],
        [0.1951, 0.2936, 0.3976, 1.0000, 0.5967],
        [0.1580, 0.2633, 0.6664, 0.5967, 1.0000]
    ])
    
    sns.heatmap(mat_b, annot=True, fmt=".4f", cmap="Blues", vmin=0.0, vmax=1.0,
                xticklabels=cats_b, yticklabels=cats_b, cbar_kws={'label': 'Similitud Coseno Binario'},
                linewidths=0.6, linecolor='gray', ax=ax2)
    ax2.set_title("B. Matriz de Órdenes Domiciliadas (ADOPTADA)\nEstructura Contractual Discriminativa [0.0000, 0.6664]\nVarianza σ² = 0.0397 (450× Mayor Dispersión)",
                  fontweight='bold', pad=10, color='#1b5e20')
    ax2.tick_params(axis='x', rotation=20)
    ax2.tick_params(axis='y', rotation=0)
    
    plt.suptitle("Comprobación del Descarte Empírico: Co-ocurrencia Transaccional Cruda vs. Modelo de Órdenes Refinado",
                 fontsize=11.5, fontweight='bold', y=0.98)
    plt.tight_layout()
    fig.savefig('img/fig_05_descarte_empirico_comparativa.png', dpi=300, bbox_inches='tight')
    plt.close(fig)
    print("Generada con éxito: img/fig_05_descarte_empirico_comparativa.png")

# =============================================================================
# FIGURA 14: MAPA ESTRATÉGICO GLOBAL (fig_06_comparativa_global.png)
# =============================================================================
def generate_fig_14():
    fig, ax = plt.subplots(figsize=(11.5, 7.0), dpi=300)
    
    # Data for the 12 models: (Name, Cobertura %, Resolucion_y, DataFrame, Metrica, Offset)
    # Resolucion_y: 1.0 (Macroscópico/Grupal), 2.0 (Ítem-Ítem/Contratos), 3.0 (Individualizado Fino)
    models = [
        ("1A: Slope One", 68.0, 3.20, "df_transacciones", "MAE: 0.2593 (5-fold CV)", (10, 8)),
        ("1B: Coseno Ajustado", 68.0, 2.75, "df_transacciones", "Dispersión: [-0.75, +0.34]", (-140, -18)),
        ("1C: Pearson Temporal", 100.0, 1.15, "df_transacciones", "r(Δmes): +0.7192", (-145, 8)),
        ("2A: Coseno Binario", 83.5, 2.15, "df_ordenes", "cos(Seg, Hog): 0.3976", (10, 8)),
        ("2B: Ponderación ITF", 83.5, 2.55, "df_ordenes", "ITF Leasing: 2.3998", (10, -15)),
        ("2C: Pearson Órdenes", 83.5, 1.80, "df_ordenes", "r(Hog, Pres): -0.4117", (-135, -15)),
        ("3A: TF-IDF Contratos", 100.0, 1.95, "df_prestamos", "Sim: 0.1611 (LOPO: 8/8)", (-145, 8)),
        ("3B: Coseno Numérico", 100.0, 1.55, "df_prestamos", "cos(12m, 60m): -0.9991", (-155, -15)),
        ("3C: Scoring y Utilidad", 100.0, 2.35, "df_prestamos", "Mora ≤30%: 6.57% (χ²=10.62)", (-175, 8)),
        ("4A: Demográfico Estereotipos", 100.0, 2.75, "df_cliente", "9 arquetipos (χ²=63.78)", (-160, 8)),
        ("4B: User-to-User kNN", 83.8, 3.10, "df_cliente", "AUC: 0.7905 (Brier: 0.1098)", (10, 8)),
        ("4C: Pearson Perfil", 100.0, 0.85, "df_cliente", "r(Tx, Ord): +0.4965", (-140, -15))
    ]
    
    color_map = {
        "df_transacciones": "#1976d2",   # Azul
        "df_ordenes": "#f57c00",         # Naranja
        "df_prestamos": "#388e3c",       # Verde
        "df_cliente": "#7b1fa2"          # Púrpura
    }
    
    # Shaded zones
    ax.axvspan(95, 103, color='#e8f5e9', alpha=0.5, label='Fase 1: Onboarding y Arranque en Frío (100% Cobertura)')
    ax.axvspan(65, 88, color='#e3f2fd', alpha=0.5, label='Fase 2: Cartera Madura (Personalización Fina)')
    
    # Plot points
    for name, cob, res, df_src, met, offset in models:
        c = color_map[df_src]
        ax.scatter(cob, res, color=c, s=130, edgecolor='black', linewidth=1.0, zorder=5)
        ax.annotate(f"{name}\n[{met}]",
                    xy=(cob, res), xytext=offset, textcoords='offset points',
                    fontsize=8.2, fontweight='bold',
                    bbox=dict(boxstyle="round,pad=0.25", fc="white", ec=c, alpha=0.9, lw=1.0),
                    arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=0.1", color=c, lw=0.8))
        
    ax.set_xlim(60, 105)
    ax.set_ylim(0.5, 3.6)
    ax.set_xlabel("Cobertura de Cartera de Clientes / Cuentas (%)", fontweight='bold', fontsize=10.5, labelpad=8)
    ax.set_ylabel("Nivel de Resolución y Personalización del Recomendador", fontweight='bold', fontsize=10.5, labelpad=8)
    ax.set_yticks([1.0, 2.0, 3.0])
    ax.set_yticklabels(["Macroscópico / Gobernanza\n(Segmentación y Tesorería)",
                        "Intermedio / Ítem a Ítem\n(Contratos y Afinidad)",
                        "Individualizado Fino\n(Personalización por Usuario)"], fontweight='bold', fontsize=9.0)
    
    # Custom legends
    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], marker='o', color='w', label='df_transacciones', markerfacecolor='#1976d2', markersize=10),
        Line2D([0], [0], marker='o', color='w', label='df_ordenes', markerfacecolor='#f57c00', markersize=10),
        Line2D([0], [0], marker='o', color='w', label='df_prestamos', markerfacecolor='#388e3c', markersize=10),
        Line2D([0], [0], marker='o', color='w', label='df_cliente_consolidado', markerfacecolor='#7b1fa2', markersize=10),
    ]
    leg1 = ax.legend(handles=legend_elements, loc='upper left', frameon=True, title="DataFrame Base", title_fontproperties={'weight':'bold'})
    ax.add_artist(leg1)
    
    ax.grid(True, linestyle=':', alpha=0.6)
    ax.set_title("Mapa Estratégico de Cobertura de Cartera frente al Nivel de Personalización\n(Consolidación de los 12 Sistemas de Recomendación del Banco Financial_ijs)",
                 fontsize=12, fontweight='bold', pad=14)
    
    plt.tight_layout()
    fig.savefig('img/fig_06_comparativa_global.png', dpi=300, bbox_inches='tight')
    plt.close(fig)
    print("Generada con éxito: img/fig_06_comparativa_global.png")

if __name__ == '__main__':
    generate_fig_13()
    generate_fig_14()
