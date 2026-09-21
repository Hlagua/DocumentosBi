import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
import os

os.makedirs('img', exist_ok=True)

def generate_anexo_a_flowchart():
    fig, ax = plt.subplots(figsize=(12, 7.5), dpi=300)
    ax.axis('off')
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)

    # Title
    ax.text(50, 96, "DIAGRAMA DE FLUJO DEL CICLO ANALÍTICO Y SISTEMAS DE RECOMENDACIÓN",
            ha='center', va='center', fontsize=12, fontweight='bold', color='#1A365D')
    ax.text(50, 92.5, "Banco Comercial (Financial_ijs) - Inteligencia de Negocios (Ralph Kimball DW)",
            ha='center', va='center', fontsize=9.5, fontstyle='italic', color='#4A5568')

    # Styles
    box_blue = dict(boxstyle="round,pad=0.5", facecolor="#EBF8FF", edgecolor="#2B6CB0", linewidth=1.5)
    box_green = dict(boxstyle="round,pad=0.5", facecolor="#F0FFF4", edgecolor="#2F855A", linewidth=1.5)
    box_yellow = dict(boxstyle="round,pad=0.5", facecolor="#FEFCBF", edgecolor="#D69E2E", linewidth=1.5)
    box_purple = dict(boxstyle="round,pad=0.5", facecolor="#FAF5FF", edgecolor="#6B46C1", linewidth=1.5)
    box_gray = dict(boxstyle="round,pad=0.5", facecolor="#F7FAFC", edgecolor="#4A5568", linewidth=1.2)

    # 1. Source: Data Warehouse
    ax.text(12, 80, "DATAMART BANCARIO\nFinancial_ijs (Kimball DW)\n- FactTransaccion\n- FactOrden\n- FactPrestamo\n- DimCliente / DimCuenta",
            ha='center', va='center', fontsize=8, bbox=box_blue)

    # Arrow 1 -> ETL
    ax.annotate('', xy=(27, 80), xytext=(22, 80),
                arrowprops=dict(arrowstyle="->", color="#2B6CB0", lw=2))

    # 2. ETL: Organizar, Clasificar, Filtrar
    ax.text(37, 80, "PREPARACIÓN DE DATOS\n• Organizar por grano\n• Clasificar productos\n• Filtrar ruido / Pareto\n• Escalamiento [1.0, 5.0]",
            ha='center', va='center', fontsize=8, bbox=box_yellow)

    # Arrow 2 -> 4 DataFrames
    ax.annotate('', xy=(52, 80), xytext=(47, 80),
                arrowprops=dict(arrowstyle="->", color="#D69E2E", lw=2))

    # 3. Four DataFrames
    df_boxes = [
        (65, 87, "df_transacciones\n(1,056,320 regs)", "#3182CE"),
        (65, 77, "df_ordenes\n(6,471 regs)", "#38A169"),
        (65, 67, "df_prestamos\n(682 contratos)", "#D69E2E"),
        (65, 57, "df_cliente_consolidado\n(5,369 clientes)", "#805AD5")
    ]
    for x, y, txt, col in df_boxes:
        ax.text(x, y, txt, ha='center', va='center', fontsize=7.5,
                bbox=dict(boxstyle="round,pad=0.3", facecolor="#FFFFFF", edgecolor=col, linewidth=1.2))

    # Connecting bracket
    ax.plot([52, 55, 55], [80, 80, 87], color="#4A5568", lw=1)
    ax.plot([55, 55], [87, 57], color="#4A5568", lw=1)
    for _, y, _, _ in df_boxes:
        ax.plot([55, 57], [y, y], color="#4A5568", lw=1)

    # 4. Recommendation Engines & Modeling
    # Connect DataFrames to Algorithms
    models = [
        (88, 87, "SLOPE ONE & ITEM-TO-ITEM\n• Slope One ponderado (|S(j,i)|)\n• Coseno Ajustado (centrado)\n• Pearson Temporal 72 meses (Δx_t)", "#2B6CB0"),
        (88, 77, "CO-ADQUISICIÓN & CONTENIDO\n• Coseno Binario (Jaccard/Lift)\n• Inverse Term Frequency (ITF)\n• Pearson Cuentas Domiciliadas", "#2F855A"),
        (88, 67, "BASADO EN CONTENIDOS & SCORING\n• TF-IDF Cláusulas de Crédito\n• Coseno de Plazos e Intereses\n• Scoring de Utilidad & Riesgo 3-Tier", "#B7791F"),
        (88, 57, "DEMOGRÁFICO & PERFILES\n• Estereotipos Sociodemográficos\n• User-to-User kNN (AUC = 0.79)\n• Pearson Perfil Multidimensional", "#6B46C1")
    ]
    for i in range(4):
        ax.annotate('', xy=(74, df_boxes[i][1]), xytext=(72, df_boxes[i][1]),
                    arrowprops=dict(arrowstyle="->", color="#4A5568", lw=1.5))
        ax.text(models[i][0], models[i][1], models[i][2], ha='center', va='center', fontsize=7,
                bbox=dict(boxstyle="round,pad=0.4", facecolor="#FFFFFF", edgecolor=models[i][3], linewidth=1.3))

    # Connecting down to Evaluation & Delivery
    ax.plot([88, 88], [51, 38], color="#4A5568", lw=1.2)
    ax.plot([50, 88], [38, 38], color="#4A5568", lw=1.2)
    ax.annotate('', xy=(50, 32), xytext=(50, 38),
                arrowprops=dict(arrowstyle="->", color="#4A5568", lw=1.5))

    # 5. Evaluation Layer
    ax.text(50, 26, "EVALUACIÓN EXPERIMENTAL & MÉTRICAS AUDITADAS\n"
                    "• 5-Fold Cross Validation (MAE = 0.2593 ± 0.0052, mejora 36.18%)\n"
                    "• Top-N Ranking Leave-One-Out (Hit-Rate@1 = 91.79%, MRR = 0.9567)\n"
                    "• Leave-One-Product-Out TF-IDF (Precisión 8/8 = 100%)\n"
                    "• Validación Predictiva kNN (AUC = 0.7905, Brier = 0.1098)\n"
                    "• Pruebas de Hipótesis: Chi-cuadrado (χ² = 10.62, p = 0.0011) y Fisher Exacto",
            ha='center', va='center', fontsize=8, bbox=box_green)

    # Arrow to Deployment
    ax.annotate('', xy=(50, 15), xytext=(50, 19),
                arrowprops=dict(arrowstyle="->", color="#2F855A", lw=2))

    # 6. Final Bank Architecture
    ax.text(50, 8, "ARQUITECTURA DE DESPLIEGUE BANCARIO EN DOS FASES\n"
                   "Fase 1: Generación de Candidatos por Afinidad (Slope One / Contenidos / Demográfico)  →  "
                   "Fase 2: Compuerta Prudencial de Riesgo (Política 3-Tier: Verde ≤30%, Amarillo 30-50%, Rojo >50%)\n"
                   "Entrega en Canales: Banca Electrónica, Cajeros Automáticos y Plataforma de Asesores Comerciales",
            ha='center', va='center', fontsize=8, bbox=box_purple)

    plt.tight_layout()
    out_path = 'img/fig_anexo_a_diagrama_flujo.png'
    plt.savefig(out_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Generated {out_path}")

def generate_anexo_b_matriz_grafica():
    fig, ax = plt.subplots(figsize=(11, 6.5), dpi=300)
    ax.axis('off')
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)

    # Title
    ax.text(50, 95, "MATRIZ GRÁFICA DE ASIGNACIÓN Y VIABILIDAD TÉCNICA",
            ha='center', va='center', fontsize=12, fontweight='bold', color='#1A365D')
    ax.text(50, 91.5, "Evaluación Multicriterio de Familias de Algoritmos sobre los 4 DataFrames del Banco",
            ha='center', va='center', fontsize=9.5, fontstyle='italic', color='#4A5568')

    # Grid table layout
    # Columns: DataFrame, Slope One, Item-to-Item Coseno, Item-to-Item Pearson, Contenidos TF-IDF, Demográfico / Utilidad
    cols = ["DataFrame Analítico", "Slope One\n(Colaborativo)", "Item-to-Item\n(Coseno)", "Item-to-Item\n(Pearson)", "Basado en Contenidos\n(TF-IDF)", "Demográfico /\nUtilidad y Riesgo"]
    x_positions = [12, 30, 47, 64, 80, 94]
    widths = [20, 15, 15, 15, 15, 15]

    # Draw header
    for i, col_name in enumerate(cols):
        ax.text(x_positions[i], 84, col_name, ha='center', va='center', fontsize=8, fontweight='bold',
                bbox=dict(boxstyle="square,pad=0.4", facecolor="#2B6CB0", edgecolor="#1A365D", alpha=0.9), color="white")

    rows = [
        ("df_transacciones\n(1,056,320 regs)\nGrano: Cliente-Producto",
         ("ÓPTIMO", "MAE: 0.2593\nHR@1: 91.79%\nMejora: 36.18%", "#C6F6D5", "#22543D"),
         ("COMPLEMENTARIO", "Coseno Ajustado\nsim: -0.75 a +0.34\nCentrado en media", "#BEE3F8", "#2A4365"),
         ("COMPLEMENTARIO", "Pearson Temporal\nr: -0.02 a +0.72\nSeries 72 meses", "#BEE3F8", "#2A4365"),
         ("INVIABLE", "Sin texto en\ntransacciones\n(No aplica)", "#FED7D7", "#742A2A"),
         ("LIMITADO", "Sin variables\nsociodemográficas\nen transacciones", "#FEEBC8", "#7B341E")),

        ("df_ordenes\n(6,471 regs)\nGrano: Cuenta-Orden",
         ("INVIABLE", "Sin rating continuo\n(Solo binario\ndomiciliación)", "#FED7D7", "#742A2A"),
         ("ÓPTIMO", "Coseno Binario\nsim: 0.00 a 0.67\n+ ITF Ponderado", "#C6F6D5", "#22543D"),
         ("COMPLEMENTARIO", "Pearson Cuotas\nr: -0.41 a +0.71\n(Segregación)", "#BEE3F8", "#2A4365"),
         ("INVIABLE", "Sin cláusulas\nen órdenes\n(No aplica)", "#FED7D7", "#742A2A"),
         ("LIMITADO", "Solo montos\nde pago\n(No perfil)", "#FEEBC8", "#7B341E")),

        ("df_prestamos\n(682 contratos)\nGrano: Cuenta-Préstamo",
         ("INVIABLE", "Soporte = 1 contrato\npor cuenta\n|S(j,i)| = 0", "#FED7D7", "#742A2A"),
         ("COMPLEMENTARIO", "Coseno Plazos\nsim: -0.99 a +0.99\n(Dipolaridad)", "#BEE3F8", "#2A4365"),
         ("INVIABLE", "Sin series ni\nco-ocurrencia\n(Un préstamo)", "#FED7D7", "#742A2A"),
         ("ÓPTIMO", "TF-IDF Cláusulas\nPrecisión: 8/8 (100%)\nLOPO Sustitutos", "#C6F6D5", "#22543D"),
         ("ÓPTIMO", "Scoring & Riesgo\nPolítica 3-Tier\nχ²: 10.62, p: 0.001", "#C6F6D5", "#22543D")),

        ("df_cliente_consolidado\n(5,369 clientes)\nGrano: Cliente-Distrito",
         ("INVIABLE", "Sin calificaciones\nde producto en\nel perfil", "#FED7D7", "#742A2A"),
         ("COMPLEMENTARIO", "Coseno Perfil\n(Espacio vectorial\nde atributos)", "#BEE3F8", "#2A4365"),
         ("COMPLEMENTARIO", "Pearson Perfil\nr: -0.47 a +0.88\n(Endeudamiento)", "#BEE3F8", "#2A4365"),
         ("INVIABLE", "Sin descripciones\ntextuales en cliente", "#FED7D7", "#742A2A"),
         ("ÓPTIMO", "Estereotipos & kNN\nkNN AUC: 0.7905\nBrier: 0.1098", "#C6F6D5", "#22543D"))
    ]

    y_pos = [68, 51, 34, 17]
    for row_idx, r in enumerate(rows):
        y = y_pos[row_idx]
        # DataFrame name
        ax.text(x_positions[0], y, r[0], ha='center', va='center', fontsize=7.5, fontweight='bold',
                bbox=dict(boxstyle="round,pad=0.3", facecolor="#EDF2F7", edgecolor="#718096", linewidth=1.2))
        
        # Alg cells
        for c_idx in range(1, 6):
            status, desc, bg_col, fg_col = r[c_idx]
            cell_text = f"{status}\n{desc}"
            ax.text(x_positions[c_idx], y, cell_text, ha='center', va='center', fontsize=6.8,
                    bbox=dict(boxstyle="round,pad=0.3", facecolor=bg_col, edgecolor=fg_col, linewidth=1.2), color=fg_col)

    # Legend at bottom
    ax.text(50, 4, "Convenciones: [ÓPTIMO: Algoritmo líder para el DataFrame] | [COMPLEMENTARIO: Algoritmo de soporte analítico] | [INVIABLE: Matemáticamente impedido]",
            ha='center', va='center', fontsize=8, fontstyle='italic', color='#2D3748')

    plt.tight_layout()
    out_path = 'img/fig_anexo_b_matriz_grafica.png'
    plt.savefig(out_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Generated {out_path}")

if __name__ == '__main__':
    generate_anexo_a_flowchart()
    generate_anexo_b_matriz_grafica()
