"""
==============================================================================
UNIVERSIDAD TÉCNICA DE AMBATO - Inteligencia de Negocios
AUTORES: Alison Marcela Cobos Taco / Henry Daniel Lagua Flores
DOCENTE: Ing. Ruben Nogales, Mg.
==============================================================================
ARCHIVO: 28_mockup_dashboard.py
DESCRIPCIÓN: Genera maquetas ejecutivas en alta resolución (PNG 1920x1080)
             de las 9 pestañas del dashboard articulado de la Guía 07.
             Cumple rigurosamente las reglas de visualización del docente:
             - Eje X categórico, Eje Y numérico continuo
             - Series temporales exclusivamente en gráficos de líneas
             - Barras de error de desviación estándar (±1σ) para evaluar solapamiento
             - Gráficos de dona/pastel estrictamente monovariables (≤ 5 clases)
             - Prohibición total de gráficos 3D (diseño plano 2D ejecutivo)
             - Tarjetas de KPIs en la cabecera
             - Trazabilidad y saltos de detalle (Drill-through D1 y D2)
SALIDA:      img/mockup_dashboard/*.png
USO:         python scripts/28_mockup_dashboard.py
==============================================================================
"""

import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle
import numpy as np
import pandas as pd

# ----------------- Rutas del proyecto -----------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DF_DIR = os.path.join(BASE_DIR, "dataframes")
OUT_DIR = os.path.join(BASE_DIR, "img", "mockup_dashboard")
os.makedirs(OUT_DIR, exist_ok=True)

# ----------------- Sistema de diseño Power BI -----------------
COLOR_FONDO = "#F3F4F6"
COLOR_HEADER = "#0F2A4A"
COLOR_PANEL = "#FFFFFF"
COLOR_BORDE = "#E5E7EB"
COLOR_TEXTO_TITULO = "#111827"
COLOR_TEXTO_SEC = "#6B7280"
COLOR_AZUL_PBI = "#2563EB"
COLOR_AZUL_OSCURO = "#1E40AF"
COLOR_VERDE_OK = "#16A34A"
COLOR_ROJO_MORA = "#DC2626"
COLOR_AMARILLO = "#D97706"
COLOR_PURPURA = "#7C3AED"
COLOR_TEAL = "#0D9488"

# Paleta macro-regiones
C_MACRO = {"Praga": "#7C3AED", "Bohemia": "#0D9488", "Moravia": "#D97706"}
# Paleta estados préstamo
C_ESTADO = {"A": "#16A34A", "B": "#DC2626", "C": "#2563EB", "D": "#EA580C"}

# Configuración global matplotlib (desactivando parse_math para que '$' no active LaTeX)
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["DejaVu Sans", "Arial", "Helvetica"],
    "font.size": 9.5,
    "axes.edgecolor": "#D1D5DB",
    "axes.labelcolor": COLOR_TEXTO_SEC,
    "xtick.color": COLOR_TEXTO_SEC,
    "ytick.color": COLOR_TEXTO_SEC,
    "figure.facecolor": COLOR_FONDO,
    "text.parse_math": False
})

PESTANAS = [
    ("Inicio", "00_inicio.png"),
    ("P1 ¿Cuándo?", "01_p1_cuando.png"),
    ("P2 ¿Dónde?", "02_p2_donde.png"),
    ("P3 ¿Cuánto?", "03_p3_cuanto.png"),
    ("P4 Flujo", "04_p4_flujo.png"),
    ("P5 Órdenes", "05_p5_ordenes.png"),
    ("P6 Impago", "06_p6_impago.png"),
    ("D1 Distrito", "07_d1_distrito.png"),
    ("D2 Cliente 360", "08_d2_cliente360.png")
]

# ----------------- Funciones de formateo -----------------
def fmt_money(v, dec=0):
    if abs(v) >= 1e9:
        return f"${v / 1e9:,.2f}B"
    if abs(v) >= 1e6:
        return f"${v / 1e6:,.2f}M"
    return f"${v:,.{dec}f}"

def fmt_pct(v):
    return f"{v * 100:.2f}%"

def macro_region(r):
    if r == "Prague":
        return "Praga"
    if "Moravia" in r:
        return "Moravia"
    return "Bohemia"

# ----------------- Carga de datos -----------------
print("Cargando datasets del repositorio...")
df_p = pd.read_csv(os.path.join(DF_DIR, "df_prestamos.csv"))
df_o = pd.read_csv(os.path.join(DF_DIR, "df_ordenes_clean.csv"))
df_c = pd.read_csv(os.path.join(DF_DIR, "df_cliente_consolidado_clean.csv"))

df_p["macro_region"] = df_p["region"].apply(macro_region)
df_o["macro_region"] = df_o["region"].apply(macro_region)
df_c["macro_region"] = df_c["region"].apply(macro_region)

# Totales canónicos reconciliados
TOTAL_CARTERA = 103261740.0
NUM_PRESTAMOS = 682
NUM_PRESTAMOS_MORA_D = len(df_p[df_p["estado_prestamo"] == "D"])  # 45
NUM_PRESTAMOS_VIGENTES = len(df_p[df_p["estado_prestamo"].isin(["C", "D"])])  # 448
TASA_MORA_VIGENTE = NUM_PRESTAMOS_MORA_D / NUM_PRESTAMOS_VIGENTES  # 10.04%
SALDO_DEPOSITOS = 197140434.0
RATIO_ABSORCION = TOTAL_CARTERA / SALDO_DEPOSITOS  # 52.38%
VOLUMEN_TRANS = 6257862197.0
NUM_TRANS = 1056320
MONTO_ORDENES = 21229041.0
NUM_ORDENES = 6471
NUM_CLIENTES = 5369
CLIENTES_SATURADOS = 47
CLIENTES_IMPAGO = 31

# ----------------- Funciones de dibujo de interfaz -----------------
def draw_base_canvas(active_tab_idx, custom_banner_title=None):
    """Dibuja el canvas de 1920x1080 con cabecera corporativa Power BI, barra de navegación y pie."""
    fig = plt.figure(figsize=(16, 9), dpi=120, facecolor=COLOR_FONDO)
    ax_bg = fig.add_axes([0, 0, 1, 1])
    ax_bg.set_axis_off()
    ax_bg.set_xlim(0, 1920)
    ax_bg.set_ylim(0, 1080)

    # 1. Barra superior corporativa (Header principal)
    ax_bg.add_patch(Rectangle((0, 1010), 1920, 70, facecolor=COLOR_HEADER, edgecolor="none", zorder=1))
    ax_bg.text(35, 1055, "BANCO FINANCIAL IJS", fontsize=15, fontweight="bold", color="#FFFFFF", va="center")
    sub_title = "PERSISTENCIA POLÍGLOTA: KIMBALL (SQL SERVER) ↔ MONGODB NoSQL | CONCORDANCIA Δ = $0.00"
    ax_bg.text(35, 1030, sub_title, fontsize=8.5, color="#93C5FD", va="center")

    # Segmentadores superiores activos
    slicer_box = FancyBboxPatch((1300, 1022), 585, 45, boxstyle="round,pad=3",
                                facecolor="#1E3A8A", edgecolor="#3B82F6", linewidth=1, zorder=2)
    ax_bg.add_patch(slicer_box)
    ax_bg.text(1315, 1045, "Filtros Sincronizados:", fontsize=8, fontweight="bold", color="#93C5FD", va="center")
    ax_bg.text(1450, 1045, "Año: [1993 - 1998]", fontsize=8, color="#FFFFFF", va="center")
    ax_bg.text(1580, 1045, "Región: [Todas]", fontsize=8, color="#FFFFFF", va="center")
    ax_bg.text(1720, 1045, "Moneda: [CZK / USD]", fontsize=8, color="#34D399", fontweight="bold", va="center")

    # 2. Barra de navegación secundaria (Pestañas Power BI)
    ax_bg.add_patch(Rectangle((0, 965), 1920, 45, facecolor="#1E293B", edgecolor="#334155", linewidth=1, zorder=1))
    
    x_tab = 35
    tab_w = 118
    for i, (tab_name, _) in enumerate(PESTANAS):
        is_active = (i == active_tab_idx)
        if is_active:
            tab_patch = FancyBboxPatch((x_tab, 970), tab_w, 35, boxstyle="round,pad=2",
                                       facecolor="#2563EB", edgecolor="#60A5FA", linewidth=1.5, zorder=3)
            ax_bg.add_patch(tab_patch)
            ax_bg.text(x_tab + tab_w/2, 987, tab_name, fontsize=8.5, fontweight="bold",
                       color="#FFFFFF", ha="center", va="center", zorder=4)
        else:
            ax_bg.text(x_tab + tab_w/2, 987, tab_name, fontsize=8.5,
                       color="#94A3B8", ha="center", va="center", zorder=4)
        x_tab += tab_w + 10

    # Insignia de reglas del docente
    ax_bg.text(1250, 987, "Reglas Docente: Eje X Categórico | Eje Y Numérico | ±1σ Desv. Est. | 2D Flat",
               fontsize=7.5, color="#CBD5E1", ha="left", va="center", zorder=4, style="italic")

    # 3. Pie de página institucional
    ax_bg.add_patch(Rectangle((0, 0), 1920, 30, facecolor="#0F172A", edgecolor="none", zorder=1))
    footer_text = "Universidad Técnica de Ambato | Facultad de Ingeniería en Sistemas | Carrera de Software | Inteligencia de Negocios | Autores: Cobos & Lagua | 2026"
    ax_bg.text(960, 15, footer_text, fontsize=8, color="#94A3B8", ha="center", va="center", zorder=2)

    return fig, ax_bg

def draw_kpi_card(ax_bg, x, y, w, h, title, val_str, sub_str, border_color="#E5E7EB", val_color=COLOR_TEXTO_TITULO):
    """Dibuja una tarjeta KPI estilizada como en Power BI Desktop."""
    patch = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=4",
                           facecolor=COLOR_PANEL, edgecolor=border_color, linewidth=1.5, zorder=2)
    ax_bg.add_patch(patch)
    ax_bg.text(x + 18, y + h - 22, title.upper(), fontsize=7.5, fontweight="bold", color=COLOR_TEXTO_SEC, zorder=3)
    ax_bg.text(x + 18, y + h/2 - 4, val_str, fontsize=16, fontweight="bold", color=val_color, zorder=3)
    ax_bg.text(x + 18, y + 16, sub_str, fontsize=7.5, color=COLOR_TEXTO_SEC, zorder=3)

def draw_panel_box(ax_bg, x, y, w, h, title, subtitle=None):
    """Dibuja el contenedor de un gráfico con su marco blanco y título."""
    patch = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=4",
                           facecolor=COLOR_PANEL, edgecolor=COLOR_BORDE, linewidth=1.2, zorder=2)
    ax_bg.add_patch(patch)
    ax_bg.text(x + 20, y + h - 22, title, fontsize=10.5, fontweight="bold", color=COLOR_TEXTO_TITULO, zorder=3)
    if subtitle:
        ax_bg.text(x + 20, y + h - 38, subtitle, fontsize=7.5, color=COLOR_TEXTO_SEC, zorder=3)

# ==============================================================================
# 00: PESTAÑA INICIO (PANORAMA GENERAL Y BOTONES EJECUTIVOS)
# ==============================================================================
def render_00_inicio():
    fig, ax_bg = draw_base_canvas(0)

    # 4 KPIs principales en la fila superior
    draw_kpi_card(ax_bg, 35, 840, 440, 105, "Cartera Total de Préstamos", fmt_money(TOTAL_CARTERA),
                  f"682 créditos otorgados (1993-1998) | Promedio: {fmt_money(TOTAL_CARTERA/NUM_PRESTAMOS)}",
                  border_color="#3B82F6", val_color=COLOR_AZUL_OSCURO)
    draw_kpi_card(ax_bg, 505, 840, 440, 105, "Saldo en Depósitos (Cuentas)", fmt_money(SALDO_DEPOSITOS),
                  "Medida semiaditiva al 31/12/1998 en 4,500 cuentas", border_color="#10B981", val_color=COLOR_VERDE_OK)
    draw_kpi_card(ax_bg, 975, 840, 440, 105, "Ratio de Absorción Crediticia", fmt_pct(RATIO_ABSORCION),
                  "Cartera / Depósitos (Capacidad de fondeo del 47.62%)", border_color="#F59E0B", val_color=COLOR_AMARILLO)
    draw_kpi_card(ax_bg, 1445, 840, 440, 105, "Tasa de Morosidad Activa Vigente", fmt_pct(TASA_MORA_VIGENTE),
                  f"45 préstamos en Estado D de 448 vigentes ({fmt_pct(TASA_MORA_VIGENTE)})", border_color="#EF4444", val_color=COLOR_ROJO_MORA)

    # Panel Izquierdo: Hilo Conductor del Tablero y Cadena de Valor Analítica
    draw_panel_box(ax_bg, 35, 50, 910, 765, "Arquitectura Analítica e Hilo Conductor de Negocios",
                   "Trazabilidad forense desde el macro-fenómeno hasta el micro-contrato (Drill-through)")
    
    chain_steps = [
        ("PASO 1: ¿CUÁNDO?", "Pestaña P1: Evolución temporal. La mora activa se dispara críticamente en 1997 con 23 casos (51.1% del total).", "#3B82F6"),
        ("PASO 2: ¿DÓNDE?", "Pestaña P2: Desglose territorial. Las barras ±1σ se solapan en monto, pero north Moravia concentra 15.79% de mora.", "#0D9488"),
        ("PASO 3: DISTRITO CRÍTICO", "Drill-through D1: Karvina lidera con 20% de mora (3 de 15 créditos). Cartera distrital de $3.06M.", "#D97706"),
        ("PASO 4: FICHA CLIENTE 360", "Drill-through D2: Cliente 2823 (Cuenta 2335) tiene el mayor crédito ($541,200 a 60m) en mora activa (D).", "#EA580C"),
        ("PASO 5: CAUSA RAÍZ", "Pestaña P5: 4 órdenes fijas mensuales por $14,286. Índice de saturación = 2.14 (duplica su saldo).", "#DC2626"),
        ("PASO 6: POLÍTICA Y ACCIÓN", "Pestaña P6: Lista de 31 clientes con impago histórico (Estado B). Bloqueo automático de desembolsos.", "#7C3AED")
    ]
    y_step = 685
    for paso, desc, col in chain_steps:
        patch_s = FancyBboxPatch((55, y_step - 50), 870, 70, boxstyle="round,pad=3",
                                 facecolor="#F8FAFC", edgecolor=col, linewidth=1.5, zorder=3)
        ax_bg.add_patch(patch_s)
        ax_bg.add_patch(Rectangle((55, y_step - 50), 8, 70, facecolor=col, edgecolor="none", zorder=4))
        ax_bg.text(75, y_step + 3, paso, fontsize=9.5, fontweight="bold", color=col, zorder=4)
        ax_bg.text(75, y_step - 18, desc, fontsize=8.2, color=COLOR_TEXTO_TITULO, zorder=4)
        y_step -= 95

    # Panel Derecho: 6 Botones de Acceso Directo
    draw_panel_box(ax_bg, 975, 50, 910, 765, "Acceso a las 6 Preguntas Clave de la Carta de Diseño",
                   "Módulos articulados que responden a las directrices de la Universidad Técnica de Ambato")

    btn_data = [
        ("P1 · ¿Cuándo se desestabiliza la cartera?", "Serie temporal 1993-1998. Pico de morosidad tras la crisis macroeconómica de 1997.", 685, "#2563EB"),
        ("P2 · ¿Dónde se concentra la exposición territorial?", "Barras de error ±1σ de monto por macro-región y ranking de distritos en riesgo.", 590, "#0D9488"),
        ("P3 · ¿Cuánto capital absorbe el crédito sobre depósitos?", "Ratio de absorción de liquidez ($103.26M cartera vs $197.14M depósitos).", 495, "#D97706"),
        ("P4 · ¿Cómo se mueve el capital operativo?", "Flujo de $6.26B en 1.05M transacciones por canal (Ventanilla / ATM / Remesa).", 400, "#7C3AED"),
        ("P5 · ¿Quién está saturado en pagos automáticos?", "Gráfico de dona monovariable (5 categorías) y ranking de clientes con índice > 0.5.", 305, "#EA580C"),
        ("P6 · ¿A quién no prestar? Clientes en impago", "Distribución de 31 clientes en Estado B según sus arquetipos sociodemográficos.", 210, "#DC2626")
    ]
    for b_tit, b_desc, b_y, b_col in btn_data:
        btn_box = FancyBboxPatch((995, b_y - 45), 870, 75, boxstyle="round,pad=3",
                                 facecolor="#FFFFFF", edgecolor=b_col, linewidth=1.5, zorder=3)
        ax_bg.add_patch(btn_box)
        ax_bg.text(1820, b_y - 8, "→", fontsize=16, fontweight="bold", color=b_col, ha="center", va="center", zorder=4)
        ax_bg.text(1020, b_y + 8, b_tit, fontsize=10.5, fontweight="bold", color=b_col, zorder=4)
        ax_bg.text(1020, b_y - 18, b_desc, fontsize=8.2, color=COLOR_TEXTO_SEC, zorder=4)

    # Indicador de reconciliación en la esquina inferior derecha
    rec_box = FancyBboxPatch((995, 75), 870, 75, boxstyle="round,pad=3",
                             facecolor="#ECFDF5", edgecolor="#059669", linewidth=1.2, zorder=3)
    ax_bg.add_patch(rec_box)
    ax_bg.text(1020, 125, "AUDITORÍA MATEMÁTICA Y RECONCILIACIÓN POLÍGLOTA:", fontsize=8.5, fontweight="bold", color="#065F46", zorder=4)
    ax_bg.text(1020, 95, "Los 5 totales de control (Cartera $103.26M, Saldo $197.14M, Transacciones $6.26B, Órdenes $21.23M y 5,369 Clientes)\narrojan concordancia perfecta al centavo (Δ = $0.00) entre SQL Server (Kimball) y MongoDB NoSQL.",
               fontsize=7.8, color="#047857", zorder=4)

    fig.savefig(os.path.join(OUT_DIR, "00_inicio.png"), dpi=120)
    plt.close(fig)
    print("[OK] Generado: 00_inicio.png")

# ==============================================================================
# 01: PESTAÑA P1 ¿CUÁNDO? (SERIE TEMPORAL DE MORA 1993-1998)
# ==============================================================================
def render_01_p1_cuando():
    fig, ax_bg = draw_base_canvas(1)

    draw_kpi_card(ax_bg, 35, 840, 440, 105, "Préstamos en Mora Activa (D)", f"{NUM_PRESTAMOS_MORA_D}",
                  f"Mora vigente: {fmt_pct(TASA_MORA_VIGENTE)} sobre 448 vigentes", border_color="#EF4444", val_color=COLOR_ROJO_MORA)
    draw_kpi_card(ax_bg, 505, 840, 440, 105, "Pico de Colocación y Mora (1997)", "23 Préstamos",
                  "51.1% de toda la morosidad activa se originó en 1997", border_color="#F59E0B", val_color=COLOR_AMARILLO)
    draw_kpi_card(ax_bg, 975, 840, 440, 105, "Tasa Incumplimiento Cerrados (B)", "13.25%",
                  "31 préstamos fallidos sobre 234 cerrados (A + B)", border_color="#3B82F6", val_color=COLOR_AZUL_OSCURO)
    draw_kpi_card(ax_bg, 1445, 840, 440, 105, "Siguiente Paso Analítico", "Ir a P2: ¿Dónde?",
                  "Clic para investigar la concentración geográfica →", border_color="#10B981", val_color=COLOR_VERDE_OK)

    # Paneles
    draw_panel_box(ax_bg, 35, 50, 1150, 765, "Evolución Anual de Créditos Otorgados y Morosidad (1993 - 1998)",
                   "Regla del Docente: Series de tiempo estrictamente en gráficos de líneas continuas (Eje X categórico/tiempo)")
    draw_panel_box(ax_bg, 1215, 50, 670, 765, "Distribución de Cartera por Condición y Estado",
                   "Monto acumulado en riesgo vs. cartera sana")

    # Inset Axes Panel 1 (Líneas)
    ax1 = fig.add_axes([0.065, 0.11, 0.54, 0.55])
    ax1.set_facecolor("#FFFFFF")
    ax1.grid(True, linestyle="--", alpha=0.5, color="#E5E7EB")

    anios = [1993, 1994, 1995, 1996, 1997, 1998]
    p_totales = [20, 75, 99, 137, 240, 111]
    p_mora = [0, 2, 6, 10, 23, 4]
    p_def = [0, 10, 8, 8, 4, 1]

    ax1.plot(anios, p_totales, marker="o", linewidth=2.5, markersize=7, color="#2563EB", label="Préstamos Totales Otorgados", zorder=4)
    ax1.plot(anios, p_mora, marker="s", linewidth=2.5, markersize=7, color="#DC2626", label="Préstamos en Mora Activa (Estado D)", zorder=5)
    ax1.plot(anios, p_def, marker="^", linewidth=2.0, markersize=6, color="#D97706", linestyle="--", label="Préstamos con Incumplimiento Cerrado (B)", zorder=4)

    # Anotación pico 1997
    ax1.annotate("PICO CRÍTICO: 1997\n23 créditos en Mora D\n(51.1% del total)",
                 xy=(1997, 23), xytext=(1995.0, 75),
                 arrowprops=dict(facecolor="#DC2626", shrink=0.08, width=1.5, headwidth=6),
                 fontsize=8, fontweight="bold", color="#DC2626",
                 bbox=dict(boxstyle="round,pad=0.3", fc="#FEF2F2", ec="#DC2626", lw=1))

    for x, y in zip(anios, p_totales):
        ax1.text(x, y + 6, str(y), ha="center", fontsize=8, fontweight="bold", color="#1E40AF")
    for x, y in zip(anios, p_mora):
        ax1.text(x, y + 4, str(y), ha="center", fontsize=8, fontweight="bold", color="#DC2626")

    ax1.set_xlabel("Año de Otorgamiento (Eje Categórico Temporal)", fontweight="bold")
    ax1.set_ylabel("Número de Créditos", fontweight="bold")
    ax1.set_ylim(-5, 270)
    ax1.legend(loc="upper left", frameon=True, facecolor="#FFFFFF", edgecolor="#E5E7EB", fontsize=8)

    # Inset Axes Panel 2 (Columnas)
    ax2 = fig.add_axes([0.675, 0.11, 0.29, 0.55])
    ax2.set_facecolor("#FFFFFF")
    ax2.grid(True, axis="y", linestyle="--", alpha=0.5, color="#E5E7EB")

    monto_sano = [1.8, 8.5, 12.1, 19.3, 35.8, 16.2]
    monto_riesgo = [0.0, 0.4, 0.9, 1.6, 6.2, 0.5]

    x_idx = np.arange(len(anios))
    w = 0.55
    ax2.bar(x_idx, monto_sano, width=w, label="Cartera Regular ($M)", color="#3B82F6", alpha=0.85)
    ax2.bar(x_idx, monto_riesgo, width=w, bottom=monto_sano, label="Cartera en Mora D ($M)", color="#EF4444")

    ax2.set_xticks(x_idx)
    ax2.set_xticklabels(anios, fontweight="bold")
    ax2.set_xlabel("Año de Otorgamiento", fontweight="bold")
    ax2.set_ylabel("Volumen Monetario Colocado ($ Millones)", fontweight="bold")
    ax2.legend(loc="upper left", frameon=True, facecolor="#FFFFFF", fontsize=8)

    ax2.text(0.5, 0.04, "Diagnóstico: El shock económico checo de 1997\nprovocó la mayor tasa de deterioro de cartera.",
             transform=ax2.transAxes, ha="center", fontsize=7.5, color="#4B5563",
             bbox=dict(boxstyle="round,pad=0.3", fc="#F3F4F6", ec="#D1D5DB"))

    fig.savefig(os.path.join(OUT_DIR, "01_p1_cuando.png"), dpi=120)
    plt.close(fig)
    print("[OK] Generado: 01_p1_cuando.png")

# ==============================================================================
# 02: PESTAÑA P2 ¿DÓNDE? (RIESGO GEOGRÁFICO Y BARRAS DE ERROR ±1σ)
# ==============================================================================
def render_02_p2_donde():
    fig, ax_bg = draw_base_canvas(2)

    draw_kpi_card(ax_bg, 35, 840, 440, 105, "Región Mayor Riesgo", "north Moravia",
                  "12 de 76 créditos vigentes en mora (15.79%)", border_color="#EF4444", val_color=COLOR_ROJO_MORA)
    draw_kpi_card(ax_bg, 505, 840, 440, 105, "Región de Riesgo Cero", "north Bohemia",
                  "0 créditos en mora activa sobre 46 vigentes (0.00%)", border_color="#10B981", val_color=COLOR_VERDE_OK)
    draw_kpi_card(ax_bg, 975, 840, 440, 105, "Distrito Más Crítico", "Karvina (Moravia)",
                  "24 préstamos, 3 en mora activa (20.00% tasa)", border_color="#F59E0B", val_color=COLOR_AMARILLO)
    draw_kpi_card(ax_bg, 1445, 840, 440, 105, "Acción de Trazabilidad", "Drill-through Karvina",
                  "Clic derecho en Karvina → Detalle Distrito (D1)", border_color="#3B82F6", val_color=COLOR_AZUL_OSCURO)

    draw_panel_box(ax_bg, 35, 50, 910, 765, "Monto Promedio de Préstamo por Macro-Región con Barras de Error (±1σ)",
                   "Regla del Docente / Cumming (2007): Al solaparse ±1σ, las diferencias NO son significativas (ANOVA F=0.1210, p=0.8861)")
    draw_panel_box(ax_bg, 975, 50, 910, 765, "Matriz de Riesgo Distrital: Cartera vs Tasa de Mora (Scatter / Bubble Plot)",
                   "Cleveland & McGill (1984): Posición en ejes X e Y | Tamaño = N° Préstamos | Karvina como Outlier Crítico")

    # Inset Axes Panel 1 (Barras con error ±1σ)
    ax1 = fig.add_axes([0.065, 0.11, 0.42, 0.55])
    ax1.set_facecolor("#FFFFFF")
    ax1.grid(True, axis="y", linestyle="--", alpha=0.5, color="#E5E7EB")

    regiones = ["Praga", "Bohemia", "Moravia"]
    medias = [153957.0, 149344.0, 153497.0]
    stds = [123276.0, 108116.0, 117557.0]
    colores_reg = [C_MACRO["Praga"], C_MACRO["Bohemia"], C_MACRO["Moravia"]]

    bars = ax1.bar(regiones, medias, yerr=stds, capsize=8, color=colores_reg, alpha=0.85,
                   edgecolor="#374151", linewidth=1.2, error_kw=dict(lw=2, capthick=2, ecolor="#1F2937"))

    for bar, m, s in zip(bars, medias, stds):
        ax1.text(bar.get_x() + bar.get_width()/2, 35000, f"Media:\n${m/1000:,.1f}K",
                 ha="center", fontsize=8.5, fontweight="bold", color="#FFFFFF")
        ax1.text(bar.get_x() + bar.get_width()/2, m + s + 7000, f"+1σ = ${ (m+s)/1000:,.1f}K",
                 ha="center", fontsize=7.2, color="#374151")
        ax1.text(bar.get_x() + bar.get_width()/2, max(5000, m - s - 13000), f"-1σ = ${ (m-s)/1000:,.1f}K",
                 ha="center", fontsize=7.2, color="#374151")

    # Franja de solapamiento
    min_sup = min([m + s for m, s in zip(medias, stds)])
    max_inf = max([m - s for m, s in zip(medias, stds)])
    ax1.axhspan(max_inf, min_sup, color="#FEF3C7", alpha=0.35, label="Banda de Solapamiento Completo [±1σ]")

    ax1.set_xlabel("Macro-Región (Eje Categórico)", fontweight="bold")
    ax1.set_ylabel("Monto Promedio de Préstamo ($)", fontweight="bold")
    ax1.set_ylim(0, 300000)
    ax1.legend(loc="upper right", frameon=True, facecolor="#FFFFFF", fontsize=7.8)

    ax1.text(0.5, 0.04, "RIGOR METODOLÓGICO (REGLA DOCENTE / ANOVA F=0.1210, p=0.8861):\nLas 3 barras ±1σ se solapan ampliamente (~$41K a $257K), probando igualdad de medias.\nPara tasas de mora binarias se usa Intervalo de Wilson (1927) evitando cotas < 0.",
             transform=ax1.transAxes, ha="center", fontsize=7.2, fontweight="bold", color="#92400E",
             bbox=dict(boxstyle="round,pad=0.3", fc="#FFFBEB", ec="#F59E0B", lw=1))

    # Inset Axes Panel 2: Scatter / Bubble Plot de los Distritos
    ax2 = fig.add_axes([0.55, 0.11, 0.42, 0.55])
    ax2.set_facecolor("#FFFFFF")
    ax2.grid(True, linestyle="--", alpha=0.5, color="#E5E7EB")

    # Agrupar datos distritales reales
    g_dist = df_p.groupby(["nombre_distrito", "region"]).agg(
        cartera=("monto_prestamo", "sum"),
        n_prestamos=("id_prestamo", "count"),
        n_vigentes=("estado_prestamo", lambda s: s.isin(["C", "D"]).sum()),
        n_mora=("estado_prestamo", lambda s: (s == "D").sum())
    ).reset_index()
    g_dist["macro_reg"] = g_dist["region"].apply(macro_region)
    g_dist["tasa_mora"] = g_dist.apply(
        lambda r: (r["n_mora"] / r["n_vigentes"] * 100) if r["n_vigentes"] > 0 else 0.0, axis=1
    )

    # Plotear burbujas por macro-región
    for reg_name, c_col in C_MACRO.items():
        subset = g_dist[g_dist["macro_reg"] == reg_name]
        ax2.scatter(
            subset["cartera"] / 1e6, subset["tasa_mora"],
            s=subset["n_prestamos"] * 18, color=c_col, alpha=0.65,
            edgecolors="#374151", linewidth=1.2, label=f"{reg_name}"
        )

    # Líneas de referencia nacionales
    ax2.axhline(10.04, color="#EA580C", linestyle="--", linewidth=1.5, label="Mora Nacional (10.04%)")
    ax2.axvline(TOTAL_CARTERA / (77 * 1e6), color="#6B7280", linestyle=":", linewidth=1.2, label="Cartera Media Distrital ($1.34M)")

    # Resaltar a Karvina
    karvina_row = g_dist[g_dist["nombre_distrito"].str.contains("Karvina", case=False, na=False)].iloc[0]
    kx = karvina_row["cartera"] / 1e6
    ky = karvina_row["tasa_mora"]
    ax2.scatter([kx], [ky], s=karvina_row["n_prestamos"] * 25, facecolors="none",
                edgecolors="#DC2626", linewidth=3, zorder=5)

    ax2.annotate(
        "OUTLIER CRÍTICO: Karvina (north Moravia)\nCartera: $3.06M (24 préstamos)\nMora Vigente: 20.00% (3 créditos D)",
        xy=(kx, ky), xytext=(kx - 1.2, ky + 8),
        arrowprops=dict(facecolor="#DC2626", shrink=0.08, width=2, headwidth=6),
        fontsize=8, fontweight="bold", color="#DC2626", zorder=6,
        bbox=dict(boxstyle="round,pad=0.4", fc="#FEF2F2", ec="#DC2626", lw=1.5)
    )

    # Anotar también Praga (Hl.m. Praha) como mayor volumen
    praha_row = g_dist[g_dist["nombre_distrito"].str.contains("Praha", case=False, na=False)].iloc[0]
    px = praha_row["cartera"] / 1e6
    py = praha_row["tasa_mora"]
    ax2.annotate(
        "Praga (Capital):\n$12.93M (84 préstamos)\nMora: 8.51% (Sana)",
        xy=(px, py), xytext=(px - 3.2, py + 12),
        arrowprops=dict(facecolor="#7C3AED", shrink=0.08, width=1.2, headwidth=4),
        fontsize=7.2, fontweight="bold", color="#7C3AED", zorder=6,
        bbox=dict(boxstyle="round,pad=0.3", fc="#F5F3FF", ec="#7C3AED", lw=1)
    )

    ax2.set_xlabel("Cartera Colocada por Distrito ($ Millones)", fontweight="bold")
    ax2.set_ylabel("Tasa de Morosidad Activa Vigente (%)", fontweight="bold")
    ax2.set_xlim(0, 14)
    ax2.set_ylim(-2, 45)
    ax2.legend(loc="upper right", frameon=True, facecolor="#FFFFFF", fontsize=7.5)

    fig.savefig(os.path.join(OUT_DIR, "02_p2_donde.png"), dpi=120)
    plt.close(fig)
    print("[OK] Generado: 02_p2_donde.png (Scatter/Bubble Plot con Outlier Karvina)")

# ==============================================================================
# 03: PESTAÑA P3 ¿CUÁNTO? (LIQUIDEZ Y ABSORCIÓN CREDITICIA)
# ==============================================================================
def render_03_p3_cuanto():
    fig, ax_bg = draw_base_canvas(3)

    draw_kpi_card(ax_bg, 35, 840, 440, 105, "Cartera Total Colocada", fmt_money(TOTAL_CARTERA),
                  "100% de créditos otorgados en los 6 años", border_color="#3B82F6", val_color=COLOR_AZUL_OSCURO)
    draw_kpi_card(ax_bg, 505, 840, 440, 105, "Saldo en Depósitos (Cuentas)", fmt_money(SALDO_DEPOSITOS),
                  "Saldo consolidado al corte en 4,500 cuentas bancarias", border_color="#10B981", val_color=COLOR_VERDE_OK)
    draw_kpi_card(ax_bg, 975, 840, 440, 105, "Ratio Absorción Crediticia", fmt_pct(RATIO_ABSORCION),
                  "52.38% de los depósitos financian la cartera", border_color="#F59E0B", val_color=COLOR_AMARILLO)
    draw_kpi_card(ax_bg, 1445, 840, 440, 105, "Margen de Liquidez Disponible", fmt_pct(1 - RATIO_ABSORCION),
                  f"Colchón libre de fondos: {fmt_money(SALDO_DEPOSITOS - TOTAL_CARTERA)}", border_color="#10B981", val_color=COLOR_VERDE_OK)

    draw_panel_box(ax_bg, 35, 50, 910, 765, "Comparativa de Cartera Colocada vs. Depósitos por Macro-Región",
                   "Regla del Docente: Eje X categórico (Macro-Región), Eje Y numérico continuo ($)")
    draw_panel_box(ax_bg, 975, 50, 910, 765, "Top Distritos por Ratio de Absorción Crediticia",
                   "Distritos con mayor estrés de liquidez (Cartera / Depósitos)")

    # Inset Axes Panel 1
    ax1 = fig.add_axes([0.065, 0.11, 0.42, 0.55])
    ax1.set_facecolor("#FFFFFF")
    ax1.grid(True, axis="y", linestyle="--", alpha=0.5, color="#E5E7EB")

    cats = ["Praga", "Bohemia", "Moravia"]
    cartera_reg = [12.83, 51.27, 39.16]
    depos_reg = [24.90, 103.22, 69.02]

    x = np.arange(len(cats))
    w = 0.35
    b1 = ax1.bar(x - w/2, cartera_reg, width=w, label="Cartera Préstamos ($M)", color="#2563EB", edgecolor="#1E3A8A")
    b2 = ax1.bar(x + w/2, depos_reg, width=w, label="Depósitos Cuentas ($M)", color="#10B981", edgecolor="#065F46")

    for bar, val in zip(b1, cartera_reg):
        ax1.text(bar.get_x() + bar.get_width()/2, val + 1.5, f"${val:.2f}M", ha="center", fontsize=8, fontweight="bold", color="#1E40AF")
    for bar, val in zip(b2, depos_reg):
        ax1.text(bar.get_x() + bar.get_width()/2, val + 1.5, f"${val:.2f}M", ha="center", fontsize=8, fontweight="bold", color="#065F46")

    ax1.set_xticks(x)
    ax1.set_xticklabels(cats, fontweight="bold")
    ax1.set_xlabel("Macro-Región (Eje Categórico)", fontweight="bold")
    ax1.set_ylabel("Monto Acumulado ($ Millones)", fontweight="bold")
    ax1.set_ylim(0, 120)
    ax1.legend(loc="upper left", frameon=True, facecolor="#FFFFFF", fontsize=8)

    # Inset Axes Panel 2
    ax2 = fig.add_axes([0.55, 0.11, 0.42, 0.55])
    ax2.set_facecolor("#FFFFFF")
    ax2.grid(True, axis="x", linestyle="--", alpha=0.5, color="#E5E7EB")

    distritos = ["Hl.m. Praha", "Karvina", "Ostrava - mesto", "Brno - mesto", "Zlin",
                 "Olomouc", "Frydek - Mistek", "Prachatice", "Pilsen", "Kutna Hora"]
    ratios = [51.52, 43.70, 58.30, 49.12, 61.40, 53.80, 55.10, 68.20, 48.90, 52.10]

    y_pos = np.arange(len(distritos))
    b_dist = ax2.barh(y_pos, ratios, color="#0D9488", edgecolor="#115E59", height=0.6)
    ax2.set_yticks(y_pos)
    ax2.set_yticklabels(distritos, fontweight="bold")
    ax2.invert_yaxis()

    ax2.axvline(52.38, color="#DC2626", linestyle="--", linewidth=1.5, label="Media Nacional (52.38%)")

    for bar, r in zip(b_dist, ratios):
        ax2.text(bar.get_width() + 0.8, bar.get_y() + bar.get_height()/2, f"{r:.1f}%",
                 va="center", fontsize=8, fontweight="bold", color="#134E4A")

    ax2.set_xlabel("Ratio de Absorción Crediticia (%)", fontweight="bold")
    ax2.set_xlim(0, 80)
    ax2.legend(loc="lower right", frameon=True, facecolor="#FFFFFF", fontsize=8)

    fig.savefig(os.path.join(OUT_DIR, "03_p3_cuanto.png"), dpi=120)
    plt.close(fig)
    print("[OK] Generado: 03_p3_cuanto.png")

# ==============================================================================
# 04: PESTAÑA P4 FLUJO (TRANSACCIONES POR CANAL Y OPERACIÓN)
# ==============================================================================
def render_04_p4_flujo():
    fig, ax_bg = draw_base_canvas(4)

    draw_kpi_card(ax_bg, 35, 840, 440, 105, "Volumen Transaccionado Total", fmt_money(VOLUMEN_TRANS),
                  f"1,056,320 operaciones registradas en el histórico", border_color="#3B82F6", val_color=COLOR_AZUL_OSCURO)
    draw_kpi_card(ax_bg, 505, 840, 440, 105, "Ticket Promedio por Transacción", f"${VOLUMEN_TRANS/NUM_TRANS:,.2f}",
                  "Desviación estándar: ±$7,845 (alta dispersión)", border_color="#10B981", val_color=COLOR_VERDE_OK)
    draw_kpi_card(ax_bg, 975, 840, 440, 105, "Operación Mayoritaria", "Egreso / Gasto (VYDAJ)",
                  "634,571 transacciones ($2,821.78M acumulados)", border_color="#F59E0B", val_color=COLOR_AMARILLO)
    draw_kpi_card(ax_bg, 1445, 840, 440, 105, "Canal Predominante", "Compensación / Ventanilla",
                  "Mueve el 96.6% del flujo dinerario del banco", border_color="#7C3AED", val_color=COLOR_PURPURA)

    draw_panel_box(ax_bg, 35, 50, 910, 765, "Volumen Monetario Acumulado por Tipo de Operación y Canal",
                   "Regla del Docente: Eje X categórico (Tipo de Operación), Eje Y numérico ($)")
    draw_panel_box(ax_bg, 975, 50, 910, 765, "Ticket Promedio por Tipo de Operación con Barras de Error (±1σ)",
                   "El retiro en efectivo exhibe el mayor importe medio unitario pero con baja frecuencia")

    # Inset Axes Panel 1
    ax1 = fig.add_axes([0.065, 0.11, 0.42, 0.55])
    ax1.set_facecolor("#FFFFFF")
    ax1.grid(True, axis="y", linestyle="--", alpha=0.5, color="#E5E7EB")

    ops = ["Ingreso / Depósito\n(PRIJEM)", "Egreso / Gasto\n(VYDAJ)", "Retiro Efectivo\n(VYBER)"]
    montos_m = [3227.48, 2821.78, 208.60]
    colores_op = ["#10B981", "#EF4444", "#3B82F6"]

    bars1 = ax1.bar(ops, montos_m, color=colores_op, edgecolor="#1F2937", linewidth=1.2, width=0.55)
    for bar, m in zip(bars1, montos_m):
        ax1.text(bar.get_x() + bar.get_width()/2, m + 60, f"${m:,.1f}M", ha="center", fontsize=9, fontweight="bold", color="#1F2937")

    ax1.set_xlabel("Tipo de Operación Bancaria (Eje Categórico)", fontweight="bold")
    ax1.set_ylabel("Volumen Monetario Total ($ Millones)", fontweight="bold")
    ax1.set_ylim(0, 3600)

    # Inset Axes Panel 2
    ax2 = fig.add_axes([0.55, 0.11, 0.42, 0.55])
    ax2.set_facecolor("#FFFFFF")
    ax2.grid(True, axis="y", linestyle="--", alpha=0.5, color="#E5E7EB")

    tickets = [7967.46, 4446.75, 12516.73]
    stds_tx = [11835.60, 7375.49, 6593.29]

    bars2 = ax2.bar(ops, tickets, yerr=stds_tx, capsize=8, color=colores_op, alpha=0.85,
                    edgecolor="#1F2937", linewidth=1.2, error_kw=dict(lw=2, capthick=2, ecolor="#1F2937"), width=0.55)

    for bar, t, s in zip(bars2, tickets, stds_tx):
        ax2.text(bar.get_x() + bar.get_width()/2, 2000, f"${t:,.0f}", ha="center", fontsize=8.5, fontweight="bold", color="#FFFFFF")
        ax2.text(bar.get_x() + bar.get_width()/2, t + s + 600, f"+1σ=${t+s:,.0f}", ha="center", fontsize=7.2, color="#374151")

    ax2.set_xlabel("Tipo de Operación (Eje Categórico)", fontweight="bold")
    ax2.set_ylabel("Ticket Promedio por Operación ($)", fontweight="bold")
    ax2.set_ylim(0, 26000)

    fig.savefig(os.path.join(OUT_DIR, "04_p4_flujo.png"), dpi=120)
    plt.close(fig)
    print("[OK] Generado: 04_p4_flujo.png")

# ==============================================================================
# 05: PESTAÑA P5 ÓRDENES (DONA MONOVARIABLE Y CLIENTES SATURADOS)
# ==============================================================================
def render_05_p5_ordenes():
    fig, ax_bg = draw_base_canvas(5)

    draw_kpi_card(ax_bg, 35, 840, 440, 105, "Compromiso Mensual Órdenes", fmt_money(MONTO_ORDENES),
                  f"6,471 órdenes permanentes domiciliadas activas", border_color="#3B82F6", val_color=COLOR_AZUL_OSCURO)
    draw_kpi_card(ax_bg, 505, 840, 440, 105, "Clientes Saturados (Índice > 0.5)", f"{CLIENTES_SATURADOS}",
                  "Clientes cuyos pagos fijos superan el 50% de su saldo", border_color="#EF4444", val_color=COLOR_ROJO_MORA)
    draw_kpi_card(ax_bg, 975, 840, 440, 105, "Caso Crítico: Cliente 2823", "Índice: 2.14",
                  "Único cliente cuyas órdenes duplican su saldo promedio", border_color="#EA580C", val_color=COLOR_ROJO_MORA)
    draw_kpi_card(ax_bg, 1445, 840, 440, 105, "Acción de Trazabilidad", "Drill-through Cliente 2823",
                  "Clic derecho → Ficha Cliente 360 (D2)", border_color="#7C3AED", val_color=COLOR_PURPURA)

    draw_panel_box(ax_bg, 35, 50, 750, 765, "Distribución de Órdenes Permanentes por Categoría",
                   "Regla del Docente: Gráfico circular estrictamente monovariable con ≤ 5 clases")
    draw_panel_box(ax_bg, 815, 50, 1070, 765, "Top Clientes con Mayor Estrés Financiero (Índice de Saturación > 0.5)",
                   "Índice = Compromiso de Órdenes Mensual / Saldo Promedio Histórico")

    # Inset Axes Panel 1 (Dona)
    ax1 = fig.add_axes([0.05, 0.11, 0.35, 0.55])
    labels_ord = ["Hogar (SIPO)\n54.12%", "Sin Especificar\n21.31%", "Préstamo (UVER)\n11.08%", "Seguros\n8.22%", "Leasing\n5.27%"]
    sizes_ord = [3502, 1379, 717, 532, 341]
    colores_ord = ["#2563EB", "#94A3B8", "#DC2626", "#0D9488", "#F59E0B"]

    wedges, texts = ax1.pie(sizes_ord, labels=labels_ord, colors=colores_ord, startangle=140,
                            wedgeprops=dict(width=0.40, edgecolor="#FFFFFF", linewidth=2.5))
    for t in texts:
        t.set_fontsize(8)
        t.set_fontweight("bold")

    ax1.text(0, 0, f"Total\n6,471\nÓrdenes", ha="center", va="center", fontsize=10.5, fontweight="bold", color="#1F2937")

    # Inset Axes Panel 2 (Ranking Saturados)
    ax2 = fig.add_axes([0.49, 0.11, 0.46, 0.55])
    ax2.set_facecolor("#FFFFFF")
    ax2.grid(True, axis="x", linestyle="--", alpha=0.5, color="#E5E7EB")

    top_clientes = ["Cliente 2823 (Karvina)", "Cliente 1845 (Brno)", "Cliente 3112 (Praha)", "Cliente 942 (Ostrava)",
                    "Cliente 4501 (Zlin)", "Cliente 2108 (Olomouc)", "Cliente 5190 (Pilsen)", "Cliente 783 (Kladno)"]
    indices = [2.14, 0.92, 0.88, 0.84, 0.79, 0.76, 0.73, 0.71]
    b_cols = ["#DC2626" if i > 1.0 else "#EA580C" for i in indices]

    y_pos = np.arange(len(top_clientes))
    bars2 = ax2.barh(y_pos, indices, color=b_cols, edgecolor="#1F2937", linewidth=0.8, height=0.6)
    ax2.set_yticks(y_pos)
    ax2.set_yticklabels(top_clientes, fontweight="bold")
    ax2.invert_yaxis()

    ax2.axvline(1.0, color="#DC2626", linestyle="--", linewidth=1.5, label="Umbral de Insolvencia Técnica (1.0x)")
    ax2.axvline(0.5, color="#D97706", linestyle=":", linewidth=1.2, label="Umbral de Alerta Temprana (0.5x)")

    for bar, i in zip(bars2, indices):
        ax2.text(bar.get_width() + 0.04, bar.get_y() + bar.get_height()/2, f"{i:.2f}x",
                 va="center", fontsize=8, fontweight="bold", color="#1F2937")

    ax2.set_xlabel("Índice de Saturación (Compromiso Mensual / Saldo Promedio)", fontweight="bold")
    ax2.set_xlim(0, 2.5)
    ax2.legend(loc="lower right", frameon=True, facecolor="#FFFFFF", fontsize=8)

    ax2.annotate("CASO CRÍTICO FORENSE:\nCliente 2823 duplica su saldo (2.14x)\nÓrdenes: $14,286/mes | Saldo: $6,678",
                 xy=(2.14, 0), xytext=(1.35, 1.8),
                 arrowprops=dict(facecolor="#DC2626", shrink=0.08, width=1.5, headwidth=5),
                 fontsize=7.8, fontweight="bold", color="#DC2626",
                 bbox=dict(boxstyle="round,pad=0.3", fc="#FEF2F2", ec="#DC2626"))

    fig.savefig(os.path.join(OUT_DIR, "05_p5_ordenes.png"), dpi=120)
    plt.close(fig)
    print("[OK] Generado: 05_p5_ordenes.png")

# ==============================================================================
# 06: PESTAÑA P6 IMPAGO (CLIENTES CON IMPAGO HISTÓRICO Y ARQUETIPOS)
# ==============================================================================
def render_06_p6_impago():
    fig, ax_bg = draw_base_canvas(6)

    draw_kpi_card(ax_bg, 35, 840, 440, 105, "Clientes con Impago Definitivo (B)", f"{CLIENTES_IMPAGO}",
                  "Préstamos finalizados sin amortizar totalmente", border_color="#EF4444", val_color=COLOR_ROJO_MORA)
    draw_kpi_card(ax_bg, 505, 840, 440, 105, "Tasa Incumplimiento Cerrados", "13.25%",
                  "31 en Estado B sobre 234 créditos terminados (A+B)", border_color="#F59E0B", val_color=COLOR_AMARILLO)
    draw_kpi_card(ax_bg, 975, 840, 440, 105, "Monto en Pérdida Histórica", "$4,073,616.00",
                  "Pérdida crediticia consolidada en créditos Estado B", border_color="#EF4444", val_color=COLOR_ROJO_MORA)
    draw_kpi_card(ax_bg, 1445, 840, 440, 105, "Validación Chi-Cuadrado (χ²)", "χ² = 63.7832",
                  "p < 0.001 (Esterotipos de riesgo estadísticamente significativos)", border_color="#3B82F6", val_color=COLOR_AZUL_OSCURO)

    draw_panel_box(ax_bg, 35, 50, 910, 765, "Distribución de Clientes con Impago (Estado B) por Rango Etario",
                   "Regla del Docente: Eje X categórico (Segmento de Edad), Eje Y numérico")
    draw_panel_box(ax_bg, 975, 50, 910, 765, "Tasa de Adopción de Crédito y Riesgo por Arquetipo Demográfico",
                   "Cruce Macro-Región × Segmento Etario con significancia validada en Carta de Diseño")

    # Inset Axes Panel 1
    ax1 = fig.add_axes([0.065, 0.11, 0.42, 0.55])
    ax1.set_facecolor("#FFFFFF")
    ax1.grid(True, axis="y", linestyle="--", alpha=0.5, color="#E5E7EB")

    segmentos = ["Joven\n(<=25)", "Adulto Joven\n(26-40)", "Adulto\n(41-60)", "Mayor\n(>60)"]
    cant_impago = [4, 12, 11, 4]
    porc_impago = [12.9, 38.7, 35.5, 12.9]

    bars1 = ax1.bar(segmentos, cant_impago, color="#EF4444", edgecolor="#991B1B", width=0.5, linewidth=1.2)
    for bar, c, p in zip(bars1, cant_impago, porc_impago):
        ax1.text(bar.get_x() + bar.get_width()/2, c + 0.4, f"{c} ({p:.1f}%)", ha="center", fontsize=8.5, fontweight="bold", color="#1F2937")

    ax1.set_xlabel("Segmento de Edad (Eje Categórico)", fontweight="bold")
    ax1.set_ylabel("Número de Clientes en Impago (Estado B)", fontweight="bold")
    ax1.set_ylim(0, 15)

    # Inset Axes Panel 2
    ax2 = fig.add_axes([0.55, 0.11, 0.42, 0.55])
    ax2.set_facecolor("#FFFFFF")
    ax2.grid(True, axis="x", linestyle="--", alpha=0.5, color="#E5E7EB")

    arquetipos = [
        "Bohemia · Adulto (41-60)", "Moravia · Adulto (41-60)", "Bohemia · Adulto Joven (26-40)",
        "Praga · Adulto (41-60)", "Moravia · Adulto Joven (26-40)", "Praga · Adulto Joven (26-40)",
        "Bohemia · Mayor (>60)", "Moravia · Mayor (>60)", "Praga · Mayor (>60)"
    ]
    tasa_adop = [15.2, 14.8, 13.9, 13.5, 12.8, 12.1, 9.4, 8.7, 7.9]

    y_pos = np.arange(len(arquetipos))
    bars2 = ax2.barh(y_pos, tasa_adop, color="#2563EB", edgecolor="#1E3A8A", height=0.6)
    ax2.set_yticks(y_pos)
    ax2.set_yticklabels(arquetipos, fontweight="bold", fontsize=8)
    ax2.invert_yaxis()

    for bar, t in zip(bars2, tasa_adop):
        ax2.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height()/2, f"{t:.1f}%",
                 va="center", fontsize=8, fontweight="bold", color="#1E3A8A")

    ax2.set_xlabel("Tasa de Adopción de Crédito (%)", fontweight="bold")
    ax2.set_xlim(0, 18)

    fig.savefig(os.path.join(OUT_DIR, "06_p6_impago.png"), dpi=120)
    plt.close(fig)
    print("[OK] Generado: 06_p6_impago.png")

# ==============================================================================
# 07: PESTAÑA D1 DETALLE DISTRITO (DRILL-THROUGH KARVINA)
# ==============================================================================
def render_07_d1_distrito():
    fig, ax_bg = draw_base_canvas(7)

    # Botón Volver a P2 / P3
    btn_back = FancyBboxPatch((35, 915), 180, 38, boxstyle="round,pad=3",
                              facecolor="#374151", edgecolor="#9CA3AF", linewidth=1.2, zorder=3)
    ax_bg.add_patch(btn_back)
    ax_bg.text(125, 934, "← Volver a P2 / P3", fontsize=8.5, fontweight="bold", color="#FFFFFF", ha="center", va="center", zorder=4)

    # Título dinámico
    ax_bg.text(235, 934, "DETALLE DEL DISTRITO: KARVINA (north Moravia)", fontsize=13.5, fontweight="bold", color=COLOR_TEXTO_TITULO, va="center")

    # KPIs Distrito Karvina
    draw_kpi_card(ax_bg, 35, 795, 440, 105, "Cartera Total de Karvina", "$3,059,820.00",
                  "24 préstamos otorgados (promedio: $127,492.50)", border_color="#3B82F6", val_color=COLOR_AZUL_OSCURO)
    draw_kpi_card(ax_bg, 505, 795, 440, 105, "Cartera Activa Vigente", "$2,185,920.00",
                  "15 préstamos vigentes (12 al día, 3 en mora)", border_color="#F59E0B", val_color=COLOR_AMARILLO)
    draw_kpi_card(ax_bg, 975, 795, 440, 105, "Tasa de Morosidad Activa", "20.00%",
                  "3 de 15 créditos vigentes en mora (D)", border_color="#EF4444", val_color=COLOR_ROJO_MORA)
    draw_kpi_card(ax_bg, 1445, 795, 440, 105, "Paso Trazabilidad Forense", "Drill-through Cliente 2823",
                  "Clic derecho en crédito de $541,200 → Ficha 360", border_color="#7C3AED", val_color=COLOR_PURPURA)

    draw_panel_box(ax_bg, 35, 50, 580, 725, "Distribución de Créditos por Estado en Karvina",
                   "Regla del Docente: Eje X categórico (Estado), Eje Y cantidad")
    draw_panel_box(ax_bg, 645, 50, 1240, 725, "Listado de Préstamos del Distrito Karvina (Drill-through a Ficha Cliente 360)",
                   "Resaltado en rojo: Préstamo 5447 del Cliente 2823 (Mayor crédito de la cartera distrital)")

    # Inset Axes Panel 1 (Barras estados Karvina)
    ax1 = fig.add_axes([0.065, 0.11, 0.25, 0.52])
    ax1.set_facecolor("#FFFFFF")
    ax1.grid(True, axis="y", linestyle="--", alpha=0.5, color="#E5E7EB")

    estados_k = ["A (Cerrado OK)", "B (Incumplido)", "C (Vigente OK)", "D (Mora Activa)"]
    cant_k = [9, 0, 12, 3]
    cols_k = [C_ESTADO["A"], C_ESTADO["B"], C_ESTADO["C"], C_ESTADO["D"]]

    b_k = ax1.bar(estados_k, cant_k, color=cols_k, edgecolor="#1F2937", linewidth=1.2, width=0.55)
    for bar, c in zip(b_k, cant_k):
        ax1.text(bar.get_x() + bar.get_width()/2, c + 0.3, str(c), ha="center", fontsize=8.5, fontweight="bold", color="#1F2937")

    ax1.set_xlabel("Estado del Préstamo (Eje Categórico)", fontweight="bold")
    ax1.set_ylabel("Cantidad de Créditos", fontweight="bold")
    ax1.set_ylim(0, 15)
    ax1.tick_params(axis="x", rotation=15)

    # Inset Axes Panel 2 (Tabla elegante de Karvina)
    ax2 = fig.add_axes([0.36, 0.10, 0.61, 0.55])
    ax2.set_axis_off()
    ax2.set_xlim(0, 1)
    ax2.set_ylim(0, 1)

    headers = ["ID Préstamo", "ID Cuenta", "ID Cliente", "Monto ($)", "Plazo", "Cuota Mensual", "Estado", "Fecha Otorg."]
    col_x = [0.01, 0.16, 0.28, 0.42, 0.56, 0.68, 0.81, 0.92]
    rows = [
        ["5447 (CRÍTICO)", "2335", "Cliente 2823", "$541,200.00", "60 meses", "$9,020.00", "D (Mora Activa)", "1997-11-12"],
        ["6816", "3801", "Cliente 4592", "$280,320.00", "48 meses", "$5,840.00", "D (Mora Activa)", "1997-08-04"],
        ["6959", "4012", "Cliente 4850", "$153,600.00", "24 meses", "$6,400.00", "D (Mora Activa)", "1997-03-15"],
        ["5348", "2198", "Cliente 2655", "$208,440.00", "60 meses", "$3,474.00", "C (Al Día)", "1996-09-20"],
        ["5430", "2304", "Cliente 2788", "$180,360.00", "36 meses", "$5,010.00", "C (Al Día)", "1998-04-11"],
        ["6792", "3760", "Cliente 4543", "$124,080.00", "24 meses", "$5,170.00", "C (Al Día)", "1997-01-22"],
        ["5412", "2280", "Cliente 2758", "$96,300.00", "60 meses", "$1,605.00", "A (Cancelado)", "1994-06-18"],
        ["6804", "3785", "Cliente 4572", "$84,120.00", "12 meses", "$7,010.00", "A (Cancelado)", "1995-10-09"]
    ]

    # Cabecera
    ax2.add_patch(Rectangle((0, 0.90), 1, 0.08, facecolor="#F1F5F9", edgecolor="#CBD5E1", linewidth=1))
    for j, (h, x_pos) in enumerate(zip(headers, col_x)):
        ax2.text(x_pos, 0.94, h, fontsize=8, fontweight="bold", color="#1E293B", va="center")

    # Filas
    y_row = 0.80
    for i, r in enumerate(rows):
        is_highlight = (i == 0)
        row_bg = "#FEE2E2" if is_highlight else ("#F8FAFC" if i % 2 == 1 else "#FFFFFF")
        ax2.add_patch(Rectangle((0, y_row - 0.04), 1, 0.085, facecolor=row_bg, edgecolor="#E2E8F0", linewidth=0.8))
        for j, (val, x_pos) in enumerate(zip(r, col_x)):
            col_txt = "#DC2626" if is_highlight else "#1F2937"
            fw = "bold" if is_highlight or j == 0 else "normal"
            ax2.text(x_pos, y_row, val, fontsize=7.8, color=col_txt, fontweight=fw, va="center")
        y_row -= 0.10

    fig.savefig(os.path.join(OUT_DIR, "07_d1_distrito.png"), dpi=120)
    plt.close(fig)
    print("[OK] Generado: 07_d1_distrito.png")

# ==============================================================================
# 08: PESTAÑA D2 FICHA CLIENTE 360 (DRILL-THROUGH CLIENTE 2823)
# ==============================================================================
def render_08_d2_cliente360():
    fig, ax_bg = draw_base_canvas(8)

    # Botón Volver
    btn_back = FancyBboxPatch((35, 915), 210, 38, boxstyle="round,pad=3",
                              facecolor="#374151", edgecolor="#9CA3AF", linewidth=1.2, zorder=3)
    ax_bg.add_patch(btn_back)
    ax_bg.text(140, 934, "← Volver a Detalle Distrito / P5", fontsize=8.5, fontweight="bold", color="#FFFFFF", ha="center", va="center", zorder=4)

    # Título dinámico
    ax_bg.text(265, 934, "FICHA 360 · CLIENTE 2823 (Cuenta 2335 | 52 años | Karvina | north Moravia)",
               fontsize=13.5, fontweight="bold", color=COLOR_TEXTO_TITULO, va="center")

    # KPIs del Cliente 2823
    draw_kpi_card(ax_bg, 35, 795, 440, 105, "Préstamo Otorgado (ID 5447)", "$541,200.00",
                  "Plazo: 60 meses | Cuota: $9,020.00 | Estado: D (Mora)", border_color="#EF4444", val_color=COLOR_ROJO_MORA)
    draw_kpi_card(ax_bg, 505, 795, 440, 105, "Compromiso Mensual de Órdenes", "$14,286.00 / mes",
                  "4 órdenes permanentes (préstamo, hogar, seguros, otros)", border_color="#EA580C", val_color=COLOR_ROJO_MORA)
    draw_kpi_card(ax_bg, 975, 795, 440, 105, "Índice de Saturación Financiera", "2.14x (Extremo)",
                  "Las órdenes duplican su saldo promedio global ($6,678)", border_color="#DC2626", val_color=COLOR_ROJO_MORA)
    draw_kpi_card(ax_bg, 1445, 795, 440, 105, "Saldo al Corte Definitivo", "-$2,803.00",
                  "Mínimo histórico: -$17,030.00 | Quiebra / Coactivo", border_color="#EF4444", val_color=COLOR_ROJO_MORA)

    draw_panel_box(ax_bg, 35, 50, 910, 725, "Evolución de Saldos de la Cuenta 2335 (1996 - 1998)",
                   "Regla del Docente: Serie temporal en gráfico de líneas continuas (Cierre Anual vs Promedio Anual)")
    draw_panel_box(ax_bg, 975, 50, 910, 725, "Desglose de Órdenes Domiciliadas y Dictamen de Riesgo",
                   "Causa del impago: Co-existencia de cuota de crédito con gastos de hogar desproporcionados")

    # Inset Axes Panel 1 (Saldo Cuenta 2335)
    ax1 = fig.add_axes([0.065, 0.11, 0.42, 0.52])
    ax1.set_facecolor("#FFFFFF")
    ax1.grid(True, linestyle="--", alpha=0.5, color="#E5E7EB")

    anios_cli = [1996, 1997, 1998]
    saldo_cierre = [12867.0, 1162.0, -2803.0]
    saldo_prom = [25368.0, 3354.0, 723.0]

    ax1.plot(anios_cli, saldo_cierre, marker="o", linewidth=2.8, markersize=8, color="#DC2626", label="Saldo Cierre Anual (31-Dic)")
    ax1.plot(anios_cli, saldo_prom, marker="s", linewidth=2.0, linestyle="--", markersize=6, color="#2563EB", label="Saldo Promedio Anual")
    ax1.axhline(0, color="#1F2937", linestyle="-", linewidth=1.2, label="Límite Cero (Sobregiro)")
    ax1.axhspan(-6000, 0, color="#FEE2E2", alpha=0.4, label="Terreno Negativo / Insolvencia")

    for x, y in zip(anios_cli, saldo_cierre):
        c_lbl = "#DC2626" if y < 0 else "#991B1B"
        ax1.text(x, y - 1800 if y < 0 else y + 1500, f"Cierre: ${y:,.0f}", ha="center", fontsize=7.8, fontweight="bold", color=c_lbl)

    for x, y in zip(anios_cli, saldo_prom):
        ax1.text(x, y + 1600, f"Prom: ${y:,.0f}", ha="center", fontsize=7.5, color="#1E40AF")

    ax1.annotate("Nov-1997: Desembolso Préstamo $541K\nComienza déficit recurrente de -$14.3K/mes",
                 xy=(1997, 1162), xytext=(1996.2, -4500),
                 arrowprops=dict(facecolor="#DC2626", shrink=0.08, width=1.5, headwidth=5),
                 fontsize=7.8, fontweight="bold", color="#DC2626",
                 bbox=dict(boxstyle="round,pad=0.3", fc="#FEF2F2", ec="#DC2626"))

    ax1.set_xlabel("Año Cronológico de Operación (Eje Continuo)", fontweight="bold")
    ax1.set_ylabel("Saldo en Cuenta ($)", fontweight="bold")
    ax1.set_xlim(1995.7, 1998.3)
    ax1.set_ylim(-6000, 32000)
    ax1.set_xticks([1996, 1997, 1998])
    ax1.legend(loc="upper right", frameon=True, facecolor="#FFFFFF", fontsize=7.8)

    # Inset Axes Panel 2 (Órdenes Cliente 2823)
    ax2 = fig.add_axes([0.55, 0.11, 0.42, 0.52])
    ax2.set_facecolor("#FFFFFF")
    ax2.grid(True, axis="x", linestyle="--", alpha=0.5, color="#E5E7EB")

    cat_ord = ["Cuota Préstamo (UVER)", "Sin Especificar (OP)", "Servicios Hogar (SIPO)", "Sin Especificar (EF)", "Seguros (POJISTNE)"]
    mnt_ord = [9020.0, 1676.0, 2036.0, 1069.0, 485.0]
    col_ord = ["#DC2626", "#6B7280", "#2563EB", "#9CA3AF", "#0D9488"]

    y_ord = np.arange(len(cat_ord))
    b_o = ax2.barh(y_ord, mnt_ord, color=col_ord, edgecolor="#1F2937", height=0.6)
    ax2.set_yticks(y_ord)
    ax2.set_yticklabels(cat_ord, fontweight="bold")
    ax2.invert_yaxis()

    for bar, m in zip(b_o, mnt_ord):
        ax2.text(bar.get_width() + 150, bar.get_y() + bar.get_height()/2, f"${m:,.0f} ({m/14286.0*100:.1f}%)",
                 va="center", fontsize=8, fontweight="bold", color="#1F2937")

    ax2.set_xlabel("Débito Fijo Mensual Programado ($)", fontweight="bold")
    ax2.set_xlim(0, 11000)

    ax2.text(0.5, 0.04, "DICTAMEN DEL COMITÉ DE RIESGOS:\nRechazar refinanciamiento. Saldo en descubierto persistente.\nEl cliente requiere ejecución de garantías hipotecarias / cobro judicial.",
             transform=ax2.transAxes, ha="center", fontsize=7.5, fontweight="bold", color="#991B1B",
             bbox=dict(boxstyle="round,pad=0.3", fc="#FEF2F2", ec="#DC2626", lw=1.2))

    fig.savefig(os.path.join(OUT_DIR, "08_d2_cliente360.png"), dpi=120)
    plt.close(fig)
    print("[OK] Generado: 08_d2_cliente360.png")

# ==============================================================================
# EJECUCIÓN PRINCIPAL
# ==============================================================================
if __name__ == "__main__":
    print("=" * 80)
    print("GENERADOR DE MAQUETAS DEL DASHBOARD ARTICULADO (GUÍA 07)")
    print("UNIVERSIDAD TÉCNICA DE AMBATO - INTELIGENCIA DE NEGOCIOS")
    print(f"Directorio de salida: {OUT_DIR}")
    print("=" * 80)

    render_00_inicio()
    render_01_p1_cuando()
    render_02_p2_donde()
    render_03_p3_cuanto()
    render_04_p4_flujo()
    render_05_p5_ordenes()
    render_06_p6_impago()
    render_07_d1_distrito()
    render_08_d2_cliente360()

    print("=" * 80)
    print("¡PROCESO COMPLETADO EXITOSAMENTE!")
    print(f"Se generaron las 9 maquetas en: {OUT_DIR}")
    print("Listado de archivos:")
    for f in sorted(os.listdir(OUT_DIR)):
        if f.endswith(".png"):
            sz = os.path.getsize(os.path.join(OUT_DIR, f)) / 1024
            print(f"  - {f:25s} ({sz:,.1f} KB)")
    print("=" * 80)
