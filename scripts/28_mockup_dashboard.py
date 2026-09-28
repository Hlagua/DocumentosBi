"""
==============================================================================
UNIVERSIDAD TÉCNICA DE AMBATO - Inteligencia de Negocios
AUTORES: Alison Marcela Cobos Taco / Henry Daniel Lagua Flores
==============================================================================
ARCHIVO: 28_mockup_dashboard.py
DESCRIPCIÓN: Genera maquetas (PNG) de las 9 pestañas del dashboard articulado
             de la guía 07, con los datos reales del repositorio. Sirven como
             referencia visual para construir los .pbix en Power BI.
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

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DF = os.path.join(BASE_DIR, "dataframes")
OUT = os.path.join(BASE_DIR, "img", "mockup_dashboard")
os.makedirs(OUT, exist_ok=True)

# ---------------- Sistema visual (guía 07, sección 3) ----------------
C_ESTADO = {"A": "#2E7D32", "B": "#8E1B1B", "C": "#1565C0", "D": "#EF6C00"}
C_MACRO = {"Praga": "#5E35B1", "Bohemia": "#00897B", "Moravia": "#F9A825"}
ALERTA = "#EF6C00"
BASE = "#1565C0"
GRIS = "#6B7280"
TINTA = "#1F2937"
FONDO = "#F3F4F6"
PANEL = "#FFFFFF"
BARRA = "#0F2A4A"

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9,
                     "axes.edgecolor": "#D1D5DB", "axes.labelcolor": GRIS,
                     "xtick.color": GRIS, "ytick.color": GRIS,
                     "text.parse_math": False})

PESTANAS = ["Inicio", "P1 ¿Cuándo?", "P2 ¿Dónde?", "P3 ¿Cuánto?", "P4 Flujo",
            "P5 Órdenes", "P6 Impago"]


def money(v, dec=0):
    if abs(v) >= 1e6:
        return f"${v / 1e6:,.2f}M"
    return f"${v:,.{dec}f}"


# ---------------- Datos ----------------
def macro(r):
    return "Praga" if r == "Prague" else ("Moravia" if "Moravia" in r else "Bohemia")


def seg(e):
    return ("Joven (<=25)" if e <= 25 else "Adulto joven (26-40)" if e <= 40
            else "Adulto (41-60)" if e <= 60 else "Mayor (>60)")


p = pd.read_csv(os.path.join(DF, "df_prestamos.csv"))
o = pd.read_csv(os.path.join(DF, "df_ordenes_clean.csv"))
t = pd.read_csv(os.path.join(DF, "df_transacciones_completado.csv.gz"),
                usecols=["id_transaccion", "id_cuenta", "id_cliente", "fecha", "anio",
                         "tipo_operacion_traducido", "monto_transaccion", "saldo_cuenta", "region"])
p["macro"] = p["region"].map(macro)
p["segmento"] = p["edad_cliente"].map(seg)
t["tipo"] = t["tipo_operacion_traducido"].replace(
    {"Intereses Ganados / Abono Bancario": "Intereses", "Ingreso / Deposito": "Ingreso / Depósito"})

ult = t.sort_values(["fecha", "id_transaccion"]).groupby("id_cuenta").tail(1)
SALDO = ult["saldo_cuenta"].sum()
CARTERA = p["monto_prestamo"].sum()


def tasa(df, grupo, pos, univ):
    b = df[df["estado_prestamo"].isin(univ)]
    g = b.groupby(grupo)["estado_prestamo"].agg(n="size", k=lambda s: (s == pos).sum())
    g["p"] = g["k"] / g["n"]
    g["ee"] = np.sqrt(g["p"] * (1 - g["p"]) / g["n"])
    return g


# ---------------- Primitivas de página ----------------
def pagina(nombre_archivo, pregunta, activa, detalle=None):
    fig = plt.figure(figsize=(16, 9), dpi=110)
    fig.patch.set_facecolor(FONDO)
    fig.add_artist(Rectangle((0, 0.915), 1, 0.085, transform=fig.transFigure,
                             color=BARRA, zorder=0))
    fig.text(0.015, 0.968, "Financial_ijs · Dashboard Kimball", color="#9CC3F5",
             fontsize=9, va="center")
    fig.text(0.015, 0.94, pregunta, color="white", fontsize=15, weight="bold", va="center")
    if detalle:
        fig.text(0.985, 0.94, "◀ Atrás", color="white", fontsize=11, ha="right", va="center",
                 bbox=dict(boxstyle="round,pad=0.4", fc="#34557A", ec="none"))
        fig.text(0.90, 0.94, f"Drill-through: {detalle}", color="#9CC3F5", fontsize=9,
                 ha="right", va="center")
    else:
        x = 0.985
        for nombre in reversed(PESTANAS):
            w = 0.0062 * len(nombre) + 0.018
            x -= w
            act = nombre == activa
            fig.add_artist(FancyBboxPatch((x, 0.952), w - 0.006, 0.03,
                                          boxstyle="round,pad=0.002,rounding_size=0.008",
                                          transform=fig.transFigure,
                                          fc="#F9A825" if act else "#34557A", ec="none"))
            fig.text(x + (w - 0.006) / 2, 0.967, nombre, color=BARRA if act else "white",
                     fontsize=8, ha="center", va="center", weight="bold" if act else "normal")
        for i, (lab, val) in enumerate([("Año", "Todos"), ("Macro-región", "Todas")]):
            xx = 0.63 + i * 0.12
            fig.text(xx, 0.93, f"{lab}: {val} ▾", color=TINTA, fontsize=8, va="center",
                     bbox=dict(boxstyle="round,pad=0.35", fc="white", ec="none"))
        fig.text(0.87, 0.93, "⟲ Restablecer", color="white", fontsize=8, va="center",
                 bbox=dict(boxstyle="round,pad=0.35", fc="#34557A", ec="none"))
    return fig


def kpis(fig, items, y=0.80, h=0.095):
    n = len(items)
    gap = 0.01
    w = (0.97 - gap * (n - 1)) / n
    for i, it in enumerate(items):
        lab, val = it[0], it[1]
        alerta = len(it) > 2 and it[2]
        x = 0.015 + i * (w + gap)
        fig.add_artist(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=0.006",
                                      transform=fig.transFigure, fc=PANEL, ec="#E5E7EB"))
        fig.add_artist(Rectangle((x, y), 0.004, h, transform=fig.transFigure,
                                 color=ALERTA if alerta else BASE))
        fig.text(x + 0.012, y + h - 0.022, lab, fontsize=8.5, color=GRIS, va="center")
        fig.text(x + 0.012, y + 0.032, val, fontsize=17 if len(val) < 16 else 13,
                 weight="bold", color=ALERTA if alerta else TINTA, va="center")


def panel(fig, rect, titulo, regla=None):
    x, y, w, h = rect
    fig.add_artist(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=0.006",
                                  transform=fig.transFigure, fc=PANEL, ec="#E5E7EB"))
    fig.text(x + 0.01, y + h - 0.022, titulo, fontsize=10, weight="bold", color=TINTA, va="center")
    if regla:
        fig.text(x + w - 0.01, y + 0.012, regla, fontsize=7.5, color=GRIS, ha="right",
                 va="center", style="italic")
    ax = fig.add_axes([x + 0.045, y + 0.055, w - 0.065, h - 0.11])
    ax.set_facecolor(PANEL)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.grid(axis="y", color="#EEF0F3", lw=0.8)
    ax.set_axisbelow(True)
    return ax


def etiquetas(ax, barras, fmt, dy=0.0, color=TINTA):
    for b in barras:
        ax.annotate(fmt(b.get_height()), (b.get_x() + b.get_width() / 2, b.get_height() + dy),
                    ha="center", va="bottom", fontsize=8, color=color,
                    xytext=(0, 2), textcoords="offset points")


def tabla(fig, rect, titulo, columnas, filas, anchos, resaltar=None, regla=None):
    x, y, w, h = rect
    fig.add_artist(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=0.006",
                                  transform=fig.transFigure, fc=PANEL, ec="#E5E7EB"))
    fig.text(x + 0.01, y + h - 0.022, titulo, fontsize=10, weight="bold", color=TINTA, va="center")
    if regla:
        fig.text(x + w - 0.01, y + 0.012, regla, fontsize=7.5, color=GRIS, ha="right",
                 va="center", style="italic")
    fila_h = min(0.032, (h - 0.07) / (len(filas) + 1))
    yy = y + h - 0.055
    xs = [x + 0.01 + sum(anchos[:i]) * (w - 0.02) for i in range(len(anchos))]
    fig.add_artist(Rectangle((x + 0.005, yy - fila_h / 2), w - 0.01, fila_h,
                             transform=fig.transFigure, color="#EEF2F7"))
    for xi, c in zip(xs, columnas):
        fig.text(xi, yy, c, fontsize=8, weight="bold", color=TINTA, va="center")
    for r, fila in enumerate(filas):
        yy -= fila_h
        if resaltar and resaltar(r, fila):
            fig.add_artist(Rectangle((x + 0.005, yy - fila_h / 2), w - 0.01, fila_h,
                                     transform=fig.transFigure, color="#FFF1E6"))
        for xi, v in zip(xs, fila):
            fig.text(xi, yy, str(v), fontsize=8, color=TINTA, va="center")


def guardar(fig, nombre):
    ruta = os.path.join(OUT, nombre)
    for ax in fig.axes:  # los gráficos van encima de los fondos de panel
        ax.set_zorder(5)
    fig.savefig(ruta, facecolor=fig.get_facecolor())
    plt.close(fig)
    print("  ->", ruta)


# ---------------- Treemap (algoritmo squarified, Bruls et al. 2000) ----------------
def _peor(fila, lado):
    s = sum(fila)
    return max(max(lado ** 2 * r / s ** 2, s ** 2 / (lado ** 2 * r)) for r in fila)


def squarify(valores, x, y, w, h):
    valores = list(valores)
    total = sum(valores)
    areas = [v * w * h / total for v in valores]
    rects = []
    while areas:
        lado = min(w, h)
        fila = [areas.pop(0)]
        while areas and _peor(fila + [areas[0]], lado) <= _peor(fila, lado):
            fila.append(areas.pop(0))
        s = sum(fila)
        if w >= h:
            ancho = s / h
            yy = y
            for a in fila:
                rects.append((x, yy, ancho, a / ancho))
                yy += a / ancho
            x += ancho
            w -= ancho
        else:
            alto = s / w
            xx = x
            for a in fila:
                rects.append((xx, y, a / alto, alto))
                xx += a / alto
            y += alto
            h -= alto
    return rects


def color_mora(tasa_v, vmax=0.25):
    c0, c1 = np.array([1.0, 0.96, 0.92]), np.array([0.94, 0.42, 0.0])
    f = min(max(tasa_v / vmax, 0), 1)
    return tuple(c0 + (c1 - c0) * f)


# ==========================================================================
# PÁGINAS
# ==========================================================================
def pg_inicio():
    fig = pagina("inicio", "¿Cómo está el banco? — Panorama de la Carta de Diseño", "Inicio")
    tm = (p["estado_prestamo"] == "D").sum() / p["estado_prestamo"].isin(["C", "D"]).sum()
    ti = (p["estado_prestamo"] == "B").sum() / p["estado_prestamo"].isin(["A", "B"]).sum()
    kpis(fig, [("Cartera total", money(CARTERA)), ("Saldo depósitos (31/12/1998)", money(SALDO)),
               ("Ratio de absorción", f"{CARTERA / SALDO:.2%}"),
               ("Tasa de mora vigente", f"{tm:.2%}", True),
               ("Tasa de incumplimiento", f"{ti:.2%}", True),
               ("Volumen transaccionado", money(t['monto_transaccion'].sum()))])
    preguntas = [
        ("P1", "¿Cómo evoluciona la morosidad año a año\ny cuál es la tasa de pérdida?"),
        ("P2", "¿Qué distritos concentran el mayor\nriesgo crediticio y mora relativa?"),
        ("P3", "¿Qué % del saldo de los clientes está\ncomprometido en la cartera?"),
        ("P4", "¿Qué operaciones mueven más dinero\ny cómo varía el balance promedio?"),
        ("P5", "¿Qué cuentas tienen órdenes que\nsaturan su saldo habitual?"),
        ("P6", "¿Qué clientes tienen impago histórico\npara denegarles productos?"),
    ]
    respuestas = [
        "Morosos 2 → 23 (1994–97); tasa estable\n12–15%. Incumplimiento: 13.25%",
        "north Moravia: 15.79% de mora.\nMayor cartera: south Moravia (19.1%)",
        "52.38% de los depósitos está prestado.\nMás expuesta: south Bohemia (60.55%)",
        "Ingreso/Depósito mueve el 51.14%\ndel volumen ($3,200M)",
        "47 cuentas con índice > 0.5;\nsolo 1 supera 1 (cliente 2823: 2.14)",
        "31 clientes con impago (estado B).\nMonto en riesgo B + D: $15.58M",
    ]
    fig.text(0.015, 0.765, "Preguntas de la Carta de Diseño (clic para ir a la pestaña)",
             fontsize=11, weight="bold", color=TINTA)
    for i, (cod, txt) in enumerate(preguntas):
        col, fil = i % 3, i // 3
        x, y = 0.015 + col * 0.215, 0.43 - fil * 0.31
        fig.add_artist(FancyBboxPatch((x, y), 0.205, 0.29,
                                      boxstyle="round,pad=0,rounding_size=0.01",
                                      transform=fig.transFigure, fc=PANEL, ec=BASE, lw=1.4))
        fig.text(x + 0.012, y + 0.25, cod, fontsize=18, weight="bold", color=BASE, va="center")
        fig.text(x + 0.012, y + 0.185, txt, fontsize=10, color=TINTA, va="center")
        fig.text(x + 0.012, y + 0.09, respuestas[i], fontsize=9, color=GRIS, va="center",
                 style="italic")
        fig.text(x + 0.195, y + 0.02, "Ir →", fontsize=9, color=BASE, ha="right", weight="bold")
    x, y, w, h = 0.67, 0.12, 0.315, 0.60
    fig.add_artist(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=0.01",
                                  transform=fig.transFigure, fc=PANEL, ec="#E5E7EB"))
    fig.text(x + 0.012, y + h - 0.03, "Ruta de análisis", fontsize=11, weight="bold", color=TINTA)
    pasos = [("P1 ¿Cuándo?", "23 morosos en 1997; tasa estable (χ² p=0.93)"),
             ("P2 ¿Dónde?", "north Moravia: 12 de 45 morosos (15.79%)"),
             ("D1 Distrito", "Karvina: 3 en mora de 15 vigentes"),
             ("D2 Cliente", "2823: $541,200 a 60 meses, estado D"),
             ("¿Qué más?", "4 órdenes = $14,286/mes; saldo −$2,803"),
             ("P5 ¿Aislado?", "Índice saturación 2.14: único > 1 de 47")]
    for i, (a, b) in enumerate(pasos):
        yy = y + h - 0.09 - i * 0.078
        fig.add_artist(FancyBboxPatch((x + 0.012, yy - 0.022), 0.085, 0.044,
                                      boxstyle="round,pad=0,rounding_size=0.008",
                                      transform=fig.transFigure,
                                      fc=ALERTA if i in (3, 5) else BASE, ec="none"))
        fig.text(x + 0.0545, yy, a, fontsize=8, color="white", ha="center", va="center", weight="bold")
        fig.text(x + 0.105, yy, b, fontsize=8.5, color=TINTA, va="center")
        if i < len(pasos) - 1:
            fig.text(x + 0.0545, yy - 0.039, "▼", fontsize=8, color=GRIS, ha="center", va="center")
    fig.text(0.015, 0.035, "Fuente: DM_Financial_Kimball_v2 (SQL Server). El dashboard MongoDB replica la "
             "misma estructura y cifras (Δ = 0.00).", fontsize=8, color=GRIS)
    guardar(fig, "00_inicio.png")


def pg_p1():
    fig = pagina("p1", "P1 · ¿Cómo evoluciona la morosidad activa año a año?", "P1 ¿Cuándo?")
    kpis(fig, [("Préstamos otorgados", "682"), ("En mora (D)", "45", True),
               ("Tasa de mora vigente", "10.04%", True), ("Incumplidos (B)", "31"),
               ("Tasa de incumplimiento", "13.25%")])
    ct = pd.crosstab(p["anio_otorgamiento"], p["estado_prestamo"])
    ax = panel(fig, (0.015, 0.40, 0.48, 0.38),
               "Los morosos (D) pasan de 2 a 23 mientras la colocación se duplica", "R2 · líneas")
    for e in "ABCD":
        ax.plot(ct.index, ct[e], marker="o", color=C_ESTADO[e], lw=2.2, label=f"Estado {e}")
    for xx, yy in zip(ct.index, ct["D"]):
        ax.annotate(str(yy), (xx, yy), xytext=(0, 6), textcoords="offset points",
                    ha="center", fontsize=8, color=C_ESTADO["D"], weight="bold")
    ax.set_ylabel("Préstamos")
    ax.set_ylim(0)
    ax.legend(ncol=4, fontsize=8, frameon=False, loc="upper left")

    g = tasa(p, "anio_otorgamiento", "D", ["C", "D"])
    ax = panel(fig, (0.505, 0.40, 0.48, 0.38),
               "La tasa de mora por año es estable (12–15%); 1998 aún es reciente",
               "R2 + R6 · ±1 error estándar")
    ax.errorbar(g.index, g["p"] * 100, yerr=g["ee"] * 100, color=ALERTA, marker="o", lw=2.2,
                capsize=5, elinewidth=1.3)
    for xx, yy in zip(g.index, g["p"] * 100):
        ax.annotate(f"{yy:.1f}%", (xx, yy), xytext=(12, 4), textcoords="offset points",
                    fontsize=8, color=TINTA)
    ax.set_ylabel("Tasa de mora vigente (%)")
    ax.set_ylim(0, 25)
    ax.set_xticks(g.index)
    ax.text(0.98, 0.94, "χ² (1994–97) = 0.44 · p = 0.93", transform=ax.transAxes, ha="right",
            fontsize=8.5, color=GRIS, bbox=dict(fc="#F9FAFB", ec="#E5E7EB"))

    filas = [[a] + [ct.loc[a, e] for e in "ABCD"] + [ct.loc[a].sum()] for a in ct.index]
    filas.append(["Total"] + [ct[e].sum() for e in "ABCD"] + [ct.values.sum()])
    tabla(fig, (0.015, 0.05, 0.60, 0.33), "Matriz Año × Estado — todas las categorías, todos los años",
          ["Año", "A · Pagado", "B · Incumplido", "C · Al día", "D · En mora", "Total"], filas,
          [0.14, 0.17, 0.17, 0.17, 0.17, 0.18], resaltar=lambda r, f: f[0] == 1997)
    x, y, w, h = 0.625, 0.05, 0.36, 0.33
    fig.add_artist(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=0.006",
                                  transform=fig.transFigure, fc=PANEL, ec="#E5E7EB"))
    fig.text(x + 0.015, y + h - 0.04, "Lectura", fontsize=11, weight="bold", color=TINTA)
    fig.text(x + 0.015, y + h - 0.08,
             "• El aumento de morosos se debe al volumen:\n  se colocaron 196 préstamos en 1997.\n"
             "• El riesgo por préstamo no cambió entre\n  cosechas (χ², p = 0.93).\n"
             "• 1998 = 2.5% por censura: son préstamos\n  que todavía no tuvieron tiempo de caer en mora.",
             fontsize=9, color=TINTA, va="top", linespacing=1.5)
    fig.text(x + w - 0.015, y + 0.03, "Ver dónde ocurre  →", fontsize=10, color="white", ha="right",
             weight="bold", bbox=dict(boxstyle="round,pad=0.5", fc=BASE, ec="none"))
    guardar(fig, "01_p1_cuando.png")


def pg_p2():
    fig = pagina("p2", "P2 · ¿Qué distritos concentran el mayor riesgo crediticio?", "P2 ¿Dónde?")
    kpis(fig, [("Región con mayor mora", "north Moravia · 15.79%", True),
               ("Región con mayor cartera", "south Moravia · 19.1%"),
               ("Monto en riesgo (B + D)", money(p.loc[p['estado_prestamo'].isin(['B', 'D']),
                                                         'saldo_pendiente_estimado'].sum())),
               ("Distritos con préstamos", f"{p['nombre_distrito'].nunique()}")])
    # Treemap
    x, y, w, h = 0.015, 0.05, 0.47, 0.73
    fig.add_artist(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=0.006",
                                  transform=fig.transFigure, fc=PANEL, ec="#E5E7EB"))
    fig.text(x + 0.01, y + h - 0.022, "La mayor cartera está en south Moravia; el naranja marca dónde es mayor la mora",
             fontsize=10, weight="bold", color=TINTA, va="center")
    fig.text(x + w - 0.01, y + h - 0.05, "R5 · treemap: área = cartera · color = tasa de mora",
             fontsize=7.5, color=GRIS, ha="right", style="italic")
    ax = fig.add_axes([x + 0.008, y + 0.05, w - 0.016, h - 0.125])
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")
    reg = p.groupby("region")["monto_prestamo"].sum().sort_values(ascending=False)
    tr = tasa(p, "region", "D", ["C", "D"])["p"]
    td = tasa(p, "nombre_distrito", "D", ["C", "D"])["p"]
    for (rx, ry, rw, rh), rn in zip(squarify(reg.values, 0, 0, 100, 100), reg.index):
        dis = p[p["region"] == rn].groupby("nombre_distrito")["monto_prestamo"].sum().sort_values(ascending=False)
        for (dx, dy, dw, dh), dn in zip(squarify(dis.values, rx, ry, rw, rh), dis.index):
            ax.add_patch(Rectangle((dx, dy), dw, dh, fc=color_mora(td.get(dn, 0)), ec="white", lw=0.8))
            if dw > 7 and dh > 4:
                ax.text(dx + 0.6, dy + dh - 1.2, dn, fontsize=6.5, va="top", color=TINTA)
        ax.add_patch(Rectangle((rx, ry), rw, rh, fc="none", ec=BARRA, lw=2.2))
        ax.text(rx + rw / 2, ry + rh / 2,
                f"{rn}\n{money(reg[rn])} · {reg[rn] / reg.sum():.1%}\nmora {tr[rn]:.1%}",
                fontsize=8.5, weight="bold", ha="center", va="center", color=BARRA,
                bbox=dict(boxstyle="round,pad=0.25", fc=(1, 1, 1, 0.8), ec="none"))
    cax = fig.add_axes([x + 0.02, y + 0.018, 0.2, 0.012])
    cax.imshow(np.array([[color_mora(v) for v in np.linspace(0, 0.25, 50)]]), aspect="auto")
    cax.set_xticks([0, 49])
    cax.set_xticklabels(["0%", "25%+ mora"], fontsize=7)
    cax.set_yticks([])

    g = tasa(p, "region", "D", ["C", "D"]).sort_values("p", ascending=False)
    ax = panel(fig, (0.495, 0.43, 0.49, 0.35),
               "north Moravia tiene la mayor tasa; solo difiere significativamente de north Bohemia",
               "R1 + R6 · ±1 EE")
    col = [ALERTA if r == "north Moravia" else BASE for r in g.index]
    b = ax.bar(range(len(g)), g["p"] * 100, color=col, width=0.65,
               yerr=g["ee"] * 100, capsize=4, error_kw=dict(ecolor=TINTA, lw=1))
    ax.set_xticks(range(len(g)))
    ax.set_xticklabels([r.replace(" ", "\n") for r in g.index], fontsize=8)
    for bi, v in zip(b, g["p"] * 100):
        ax.text(bi.get_x() + bi.get_width() / 2, 1, f"{v:.1f}%", ha="center", fontsize=8,
                color="white", weight="bold")
    ax.set_ylabel("Tasa de mora (%)")
    ax.text(0.98, 0.92, "χ² global p = 0.239 · Fisher NM vs NB p = 0.008", transform=ax.transAxes,
            ha="right", fontsize=8, color=GRIS, bbox=dict(fc="#F9FAFB", ec="#E5E7EB"))

    m = p.groupby("macro")["monto_prestamo"].agg(["mean", "std"]).loc[["Praga", "Moravia", "Bohemia"]]
    ax = panel(fig, (0.495, 0.05, 0.24, 0.37), "Monto promedio: no depende de la región",
               "±1σ")
    b = ax.bar(m.index, m["mean"] / 1000, yerr=m["std"] / 1000, capsize=6,
               color=[C_MACRO[i] for i in m.index], width=0.6, error_kw=dict(ecolor=TINTA, lw=1))
    for bi, v in zip(b, m["mean"] / 1000):
        ax.text(bi.get_x() + bi.get_width() / 2, 8, f"${v:,.0f}k", ha="center", fontsize=8,
                color="white", weight="bold")
    ax.set_ylabel("Miles $")
    ax.text(0.5, 0.97, "ANOVA p = 0.886", transform=ax.transAxes, ha="center", va="top",
            fontsize=8, color=GRIS)

    d = p[p["estado_prestamo"] == "D"].groupby("nombre_distrito").size().sort_values(ascending=False).head(10)
    ax = panel(fig, (0.745, 0.05, 0.24, 0.37), "Top 10 distritos por préstamos en mora", "R1")
    col = [ALERTA if n == "Karvina" else BASE for n in d.index]
    b = ax.bar(range(len(d)), d.values, color=col, width=0.7)
    ax.set_xticks(range(len(d)))
    ax.set_xticklabels(d.index, rotation=60, ha="right", fontsize=7)
    etiquetas(ax, b, lambda v: f"{v:.0f}")
    ax.set_ylim(0, 5)
    ax.annotate("clic derecho → Obtener detalles", xy=(1, 3), xytext=(3.5, 4.4), fontsize=7.5,
                color=ALERTA, arrowprops=dict(arrowstyle="->", color=ALERTA))
    guardar(fig, "02_p2_donde.png")


def pg_p3():
    fig = pagina("p3", "P3 · ¿Qué porcentaje de los depósitos está comprometido en préstamos?", "P3 ¿Cuánto?")
    kpis(fig, [("Cartera total", money(CARTERA)), ("Saldo depósitos", money(SALDO)),
               ("Ratio de absorción", f"{CARTERA / SALDO:.2%}"),
               ("Región más expuesta", "south Bohemia · 60.55%", True)])
    dist = pd.concat([p[["id_cuenta", "region", "nombre_distrito"]], o[["id_cuenta", "region", "nombre_distrito"]]]
                     ).drop_duplicates("id_cuenta")
    u = ult.drop(columns="region").merge(
        pd.concat([dist, t[["id_cuenta", "region"]].drop_duplicates("id_cuenta")]).drop_duplicates("id_cuenta"),
        on="id_cuenta")
    u["macro"] = u["region"].map(macro)
    mc = pd.DataFrame({"c": p.groupby("macro")["monto_prestamo"].sum(), "s": u.groupby("macro")["saldo_cuenta"].sum()})
    ax = panel(fig, (0.015, 0.05, 0.36, 0.73),
               "En las 3 macro-regiones la cartera es poco más de la mitad de los depósitos", "R1")
    xs = np.arange(3)
    b1 = ax.bar(xs - 0.2, mc["c"] / 1e6, 0.38, color=BASE, label="Cartera")
    b2 = ax.bar(xs + 0.2, mc["s"] / 1e6, 0.38, color="#93C5FD", label="Saldo depósitos")
    etiquetas(ax, b1, lambda v: f"${v:.1f}M")
    etiquetas(ax, b2, lambda v: f"${v:.1f}M")
    ax.set_xticks(xs)
    ax.set_xticklabels([f"{i}\nratio {mc.loc[i, 'c'] / mc.loc[i, 's']:.1%}" for i in mc.index])
    ax.set_ylabel("Millones $")
    ax.legend(frameon=False)
    r = pd.DataFrame({"c": p.groupby("region")["monto_prestamo"].sum(),
                      "s": u.groupby("region")["saldo_cuenta"].sum()})
    r["r"] = r["c"] / r["s"]
    r = r.sort_values("r", ascending=False)
    ax = panel(fig, (0.385, 0.05, 0.60, 0.73),
               "south Bohemia (60.55%) y east Bohemia (58.93%) superan el promedio; north Bohemia es la más holgada",
               "R1 · línea de referencia = promedio banco")
    col = [ALERTA if v > CARTERA / SALDO else BASE for v in r["r"]]
    b = ax.bar(range(len(r)), r["r"] * 100, color=col, width=0.65)
    etiquetas(ax, b, lambda v: f"{v:.1f}%")
    ax.axhline(CARTERA / SALDO * 100, color=TINTA, ls="--", lw=1.2)
    ax.text(len(r) - 0.5, CARTERA / SALDO * 100 + 1, "Promedio banco 52.38%", ha="right", fontsize=8.5)
    ax.set_xticks(range(len(r)))
    ax.set_xticklabels(r.index)
    ax.set_ylabel("Ratio de absorción (%)")
    ax.set_ylim(0, 70)
    guardar(fig, "03_p3_cuanto.png")


def pg_p4():
    fig = pagina("p4", "P4 · ¿Qué operaciones mueven más dinero y cómo varía el saldo promedio?", "P4 Flujo")
    kpis(fig, [("Volumen transaccionado", money(t["monto_transaccion"].sum())),
               ("Nº de transacciones", f"{len(t):,}"),
               ("Ticket promedio", money(t["monto_transaccion"].mean(), 2)),
               ("Operación con mayor volumen", "Ingreso / Depósito · 51.14%")])
    g = t.groupby("tipo")["monto_transaccion"].agg(["sum", "mean", "std"]).sort_values("sum", ascending=False)
    ax = panel(fig, (0.015, 0.43, 0.32, 0.35), "Ingresos y egresos mueven el 96% del dinero", "R1")
    b = ax.bar(range(len(g)), g["sum"] / 1e6, color=BASE, width=0.6)
    etiquetas(ax, b, lambda v: f"${v:,.0f}M")
    ax.set_xticks(range(len(g)))
    ax.set_xticklabels([s.replace(" / ", "/\n").replace(" en ", "\nen ") for s in g.index], fontsize=8)
    ax.set_ylabel("Millones $")
    ax = panel(fig, (0.345, 0.43, 0.32, 0.35), "Depósitos y retiros son las operaciones de mayor monto",
               "R6 · ±1σ")
    b = ax.bar(range(len(g)), g["mean"] / 1000, yerr=g["std"] / 1000, capsize=5, color=BASE, width=0.6,
               error_kw=dict(ecolor=TINTA, lw=1))
    for bi, v in zip(b, g["mean"]):
        ax.text(bi.get_x() + bi.get_width() / 2, 0.5, f"${v:,.0f}", ha="center", fontsize=8,
                color="white" if v > 2000 else TINTA, weight="bold")
    ax.set_xticks(range(len(g)))
    ax.set_xticklabels([s.replace(" / ", "/\n").replace(" en ", "\nen ") for s in g.index], fontsize=8)
    ax.set_ylabel("Miles $")
    ax.text(0.98, 0.95, "ANOVA p < 0.001 · η² = 0.25", transform=ax.transAxes, ha="right", va="top",
            fontsize=8, color=GRIS, bbox=dict(fc="#F9FAFB", ec="#E5E7EB"))
    pv = t.pivot_table(index="anio", columns="tipo", values="monto_transaccion", aggfunc="sum")[g.index]
    ax = panel(fig, (0.675, 0.43, 0.31, 0.35), "Todas las operaciones crecen cada año", "R2 · líneas")
    for c, colr in zip(pv.columns, [BASE, "#00897B", "#F9A825", "#8E24AA"]):
        ax.plot(pv.index, pv[c] / 1e6, marker="o", color=colr, lw=2, label=c)
    ax.set_ylabel("Millones $")
    ax.legend(fontsize=7, frameon=False)
    filas = [[a] + [f"${pv.loc[a, c] / 1e6:,.1f}M" for c in pv.columns] + [f"${pv.loc[a].sum() / 1e6:,.1f}M"]
             for a in pv.index]
    tabla(fig, (0.015, 0.05, 0.55, 0.36), "Matriz Año × Operación — todas las categorías, todos los años",
          ["Año"] + list(pv.columns) + ["Total"], filas, [0.1, 0.19, 0.19, 0.19, 0.16, 0.17])
    sp = t.groupby("anio")["saldo_cuenta"].mean()
    ax = panel(fig, (0.575, 0.05, 0.41, 0.36), "Cómo varía el balance promedio de las cuentas", "R2 · líneas")
    ax.plot(sp.index, sp / 1000, marker="o", color=BASE, lw=2.2)
    for xx, yy in zip(sp.index, sp / 1000):
        ax.annotate(f"${yy:,.1f}k", (xx, yy), xytext=(0, 6), textcoords="offset points", ha="center", fontsize=8)
    ax.set_ylabel("Saldo promedio (miles $)")
    ax.set_ylim(0, sp.max() / 1000 * 1.25)
    guardar(fig, "04_p4_flujo.png")


def pg_p5():
    fig = pagina("p5", "P5 · ¿Qué cuentas tienen órdenes que saturan su saldo?", "P5 Órdenes")
    kpis(fig, [("Órdenes permanentes", f"{len(o):,}"), ("Compromiso mensual", money(o['monto_orden'].sum())),
               ("Categoría principal", "Servicios del Hogar · 54.12%"),
               ("Cuentas saturadas (índice > 0.5)", "47", True)])
    cnt = o["categoria_orden"].value_counts()
    x, y, w, h = 0.015, 0.05, 0.30, 0.73
    ax = panel(fig, (x, y, w, h), "Más de la mitad de las órdenes son servicios del hogar",
               "R3 · una variable, %")
    ax.grid(False)
    ax.axis("off")
    colores = ["#1565C0", "#90A4AE", "#26A69A", "#7E57C2", "#A1887F"]
    ax.pie(cnt.values, colors=colores, startangle=90, counterclock=False,
           wedgeprops=dict(width=0.38, edgecolor="white"),
           autopct=lambda v: f"{v:.2f}%", pctdistance=0.8,
           textprops=dict(fontsize=8.5, color="white", weight="bold"))
    ax.text(0, 0, f"{len(o):,}\nórdenes", ha="center", va="center", fontsize=12, weight="bold", color=TINTA)
    ax.legend(cnt.index, loc="lower center", bbox_to_anchor=(0.5, -0.18), ncol=2, fontsize=8, frameon=False)
    m = o.groupby("categoria_orden")["monto_orden"].sum().sort_values(ascending=False)
    ax = panel(fig, (0.325, 0.43, 0.66, 0.35), "Servicios del hogar comprometen $13.97M al mes (65.78% del monto)", "R1")
    b = ax.bar(range(len(m)), m / 1e6, color=BASE, width=0.55)
    etiquetas(ax, b, lambda v: f"${v:,.2f}M")
    ax.set_xticks(range(len(m)))
    ax.set_xticklabels(m.index)
    ax.set_ylabel("Millones $ / mes")
    sp = t.groupby("id_cuenta").agg(saldo=("saldo_cuenta", "mean"), cli=("id_cliente", "first"),
                                    reg=("region", "first"))
    oc = o.groupby("id_cuenta")["monto_orden"].sum()
    s = sp.join(oc.rename("ord"), how="inner")
    s["idx"] = s["ord"] / s["saldo"]
    s = s[s["idx"] > 0.5].sort_values("idx", ascending=False).head(8)
    dn = o.drop_duplicates("id_cuenta").set_index("id_cuenta")["nombre_distrito"]
    filas = [[f"Cliente {int(r.cli)}", dn.get(i, r.reg), f"${r.ord:,.0f}", f"${r.saldo:,.0f}", f"{r.idx:.2f}"]
             for i, r in s.iterrows()]
    tabla(fig, (0.325, 0.05, 0.66, 0.36), "Un cliente compromete más del doble de su saldo (índice > 0.5, 8 primeras de 47)",
          ["Cliente", "Distrito", "Órdenes / mes", "Saldo promedio", "Índice saturación"], filas,
          [0.2, 0.22, 0.19, 0.19, 0.2], resaltar=lambda r, f: float(f[-1]) > 1,
          regla="naranja = índice > 1 · clic derecho → Ficha Cliente")
    guardar(fig, "05_p5_ordenes.png")


def pg_p6():
    fig = pagina("p6", "P6 · ¿A qué clientes no se les deben dar nuevos productos?", "P6 Impago")
    kpis(fig, [("Clientes con impago (B)", "31", True), ("Tasa de incumplimiento", "13.25%"),
               ("Monto en riesgo (B + D)", money(p.loc[p['estado_prestamo'].isin(['B', 'D']),
                                                        'saldo_pendiente_estimado'].sum())),
               ("Préstamos cerrados evaluados", "234")])
    b = p[p["estado_prestamo"] == "B"].sort_values("saldo_pendiente_estimado", ascending=False).head(12)
    filas = [[f"Cliente {r.id_cliente}", r.nombre_distrito, f"${r.monto_prestamo:,.0f}",
              f"${r.pago_mensual:,.0f}", f"${r.saldo_pendiente_estimado:,.0f}"] for r in b.itertuples()]
    tabla(fig, (0.015, 0.05, 0.47, 0.73), "Lista de denegación: 31 clientes (12 primeros por saldo pendiente)",
          ["Cliente", "Distrito", "Monto", "Cuota", "Saldo pendiente"], filas, [0.2, 0.26, 0.18, 0.16, 0.2],
          regla="clic derecho → Ficha Cliente")
    orden = ["Joven (<=25)", "Adulto joven (26-40)", "Adulto (41-60)", "Mayor (>60)"]
    g = tasa(p, "segmento", "B", ["A", "B"]).loc[orden]
    ax = panel(fig, (0.495, 0.43, 0.49, 0.35), "La edad no predice el impago (barras solapadas)", "R1 + R6 · ±1 EE")
    bb = ax.bar(range(4), g["p"] * 100, yerr=g["ee"] * 100, capsize=6, color=BASE, width=0.6,
                error_kw=dict(ecolor=TINTA, lw=1))
    for bi, (v, n) in zip(bb, zip(g["p"] * 100, g["n"])):
        ax.text(bi.get_x() + bi.get_width() / 2, 1, f"{v:.1f}%\nn={n}", ha="center", fontsize=8,
                color="white", weight="bold")
    ax.set_xticks(range(4))
    ax.set_xticklabels(orden)
    ax.set_ylabel("Tasa de incumplimiento (%)")
    ax.text(0.98, 0.95, "χ² = 1.68 · p = 0.64", transform=ax.transAxes, ha="right", va="top", fontsize=8,
            color=GRIS, bbox=dict(fc="#F9FAFB", ec="#E5E7EB"))
    r = p[p["estado_prestamo"] == "B"].groupby("region").size().reindex(p["region"].unique(), fill_value=0)
    r = r.sort_values(ascending=False)
    ax = panel(fig, (0.495, 0.05, 0.49, 0.36), "Los incumplidos se reparten entre regiones", "R1")
    bb = ax.bar(range(len(r)), r.values, color=C_ESTADO["B"], width=0.6)
    etiquetas(ax, bb, lambda v: f"{v:.0f}")
    ax.set_xticks(range(len(r)))
    ax.set_xticklabels([s.replace(" ", "\n") for s in r.index], fontsize=8)
    ax.set_ylim(0, 8)
    guardar(fig, "06_p6_impago.png")


def pg_d1():
    fig = pagina("d1", "Detalle del distrito: Karvina", None, detalle="P2 → Karvina")
    k = p[p["nombre_distrito"] == "Karvina"]
    tk = (k["estado_prestamo"] == "D").sum() / k["estado_prestamo"].isin(["C", "D"]).sum()
    r0 = k.iloc[0]
    kpis(fig, [("Préstamos / en mora", f"{len(k)} / {(k['estado_prestamo'] == 'D').sum()}"),
               ("Tasa de mora vigente", f"{tk:.2%}", True), ("Cartera", money(k['monto_prestamo'].sum())),
               ("Salario promedio", f"${r0.salario_distrito:,.0f}"),
               ("Desempleo", f"{r0.desempleo_distrito:.2f}%"), ("Criminalidad", f"{r0.crimen_distrito:,.0f}")])
    cnt = k["estado_prestamo"].value_counts().reindex(list("ABCD"), fill_value=0)
    ax = panel(fig, (0.015, 0.05, 0.28, 0.73), "Estado de los 24 préstamos", "R3 · una variable, %")
    ax.axis("off")
    nz = cnt[cnt > 0]
    ax.pie(nz.values, colors=[C_ESTADO[e] for e in nz.index], startangle=90, counterclock=False,
           wedgeprops=dict(width=0.38, edgecolor="white"), autopct=lambda v: f"{v:.1f}%", pctdistance=0.8,
           textprops=dict(fontsize=9, color="white", weight="bold"))
    ax.legend([f"{e} · {n}" for e, n in nz.items()], loc="lower center", bbox_to_anchor=(0.5, -0.12),
              ncol=4, frameon=False, fontsize=8.5)
    ct = pd.crosstab(k["anio_otorgamiento"], k["estado_prestamo"] == "D").reindex(range(1993, 1999), fill_value=0)
    ax = panel(fig, (0.305, 0.43, 0.68, 0.35), "Préstamos otorgados y en mora por año en Karvina", "R2 · líneas")
    ax.plot(ct.index, ct.sum(axis=1), marker="o", color=BASE, lw=2.2, label="Otorgados")
    ax.plot(ct.index, ct.get(True, 0), marker="o", color=ALERTA, lw=2.2, label="En mora (D)")
    ax.legend(frameon=False)
    ax.set_ylim(0)
    kk = k.sort_values(["estado_prestamo", "monto_prestamo"], ascending=[False, False]).head(9)
    filas = [[f"Cliente {r.id_cliente}", r.id_prestamo, f"${r.monto_prestamo:,.0f}", f"${r.pago_mensual:,.0f}",
              r.plazo_meses, r.estado_prestamo] for r in kk.itertuples()]
    tabla(fig, (0.305, 0.05, 0.68, 0.36), "Préstamos del distrito (morosos primero)",
          ["Cliente", "Préstamo", "Monto", "Cuota", "Plazo", "Estado"], filas, [0.2, 0.15, 0.2, 0.17, 0.13, 0.15],
          resaltar=lambda r, f: f[-1] == "D", regla="clic derecho en Cliente 2823 → Ficha Cliente 360")
    guardar(fig, "07_d1_distrito.png")


def pg_d2():
    fig = pagina("d2", "Ficha 360 · Cliente 2823", None, detalle="D1 Karvina → Cliente 2823")
    cta = 2335
    pr = p[p["id_cuenta"] == cta].iloc[0]
    oc = o[o["id_cuenta"] == cta].groupby("categoria_orden")["monto_orden"].sum().sort_values(ascending=False)
    tc = t[t["id_cuenta"] == cta]
    sp = tc["saldo_cuenta"].mean()
    fin = tc.sort_values(["fecha", "id_transaccion"])["saldo_cuenta"].iloc[-1]
    kpis(fig, [("Préstamo · plazo", f"{money(pr.monto_prestamo)} · {pr.plazo_meses}m"),
               ("Cuota · estado", f"${pr.pago_mensual:,.0f} · {pr.estado_prestamo}", True),
               ("Compromiso en órdenes", f"${oc.sum():,.0f}/mes"),
               ("Índice de saturación", f"{oc.sum() / sp:.2f}", True),
               ("Saldo final", f"-${abs(fin):,.0f}" if fin < 0 else f"${fin:,.0f}", True)])
    x, y, w, h = 0.015, 0.05, 0.22, 0.73
    fig.add_artist(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=0.006",
                                  transform=fig.transFigure, fc=PANEL, ec="#E5E7EB"))
    fig.text(x + 0.01, y + h - 0.022, "Perfil", fontsize=10, weight="bold", color=TINTA, va="center")
    info = [("Sexo", pr.sexo_cliente), ("Edad al corte", f"{pr.edad_cliente} años"),
            ("Segmento", pr.segmento), ("Distrito", pr.nombre_distrito), ("Región", pr.region),
            ("Cuenta", str(cta)), ("Otorgado", pr.fecha_otorgamiento), ("Frecuencia extracto", pr.frecuencia_emision_estado)]
    for i, (a, b) in enumerate(info):
        fig.text(x + 0.012, y + h - 0.075 - i * 0.075, a, fontsize=8, color=GRIS)
        fig.text(x + 0.012, y + h - 0.1 - i * 0.075, str(b), fontsize=10.5, color=TINTA, weight="bold")
    ax = panel(fig, (0.245, 0.43, 0.36, 0.35), f"4 órdenes fijas suman ${oc.sum():,.0f} al mes", "R1")
    b = ax.bar(range(len(oc)), oc.values, color=[ALERTA if "Prestamo" in c else BASE for c in oc.index], width=0.6)
    etiquetas(ax, b, lambda v: f"${v:,.0f}")
    ax.set_xticks(range(len(oc)))
    ax.set_xticklabels(oc.index, fontsize=8)
    ax.set_ylabel("$ / mes")
    s = tc.groupby("anio")["saldo_cuenta"].mean()
    ax = panel(fig, (0.615, 0.43, 0.37, 0.35), "Su saldo promedio se desplomó tras el préstamo", "R2 · líneas")
    ax.plot(s.index, s.values, marker="o", color=ALERTA, lw=2.4)
    for xx, yy in zip(s.index, s.values):
        ax.annotate(f"${yy:,.0f}", (xx, yy), xytext=(0, 7), textcoords="offset points", ha="center", fontsize=8.5)
    ax.axvline(1997.86, color=GRIS, ls=":", lw=1)
    ax.text(1997.8, s.max() * 0.9, "préstamo\n12/11/1997", fontsize=7.5, color=GRIS, ha="right")
    ax.set_xticks(s.index)
    ax.set_ylim(0, s.max() * 1.25)
    v = tc.groupby("tipo")["monto_transaccion"].sum().sort_values(ascending=False)
    ax = panel(fig, (0.245, 0.05, 0.36, 0.36), "Movimientos de su cuenta por tipo de operación", "R1")
    b = ax.bar(range(len(v)), v.values / 1000, color=BASE, width=0.6)
    etiquetas(ax, b, lambda x_: f"${x_:,.0f}k")
    ax.set_xticks(range(len(v)))
    ax.set_xticklabels([s_.replace(" / ", "/\n").replace(" en ", "\nen ") for s_ in v.index], fontsize=8)
    ax.set_ylabel("Miles $")
    x, y, w, h = 0.615, 0.05, 0.37, 0.36
    fig.add_artist(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=0.006",
                                  transform=fig.transFigure, fc="#FFF7ED", ec=ALERTA, lw=1.5))
    fig.text(x + 0.015, y + h - 0.04, "Conclusión del recorrido", fontsize=11, weight="bold", color=ALERTA)
    fig.text(x + 0.015, y + h - 0.08,
             f"• Órdenes fijas = {oc.sum() / sp:.2f} × su saldo promedio.\n"
             "• Único cliente del banco con índice > 1\n  (47 cuentas en alerta con índice > 0.5).\n"
             "• Ni el año ni la región explicaban la mora;\n  la capacidad de pago sí.\n"
             "• Propuesta: alerta temprana por índice\n  de saturación antes de otorgar crédito.",
             fontsize=9.5, color=TINTA, va="top", linespacing=1.5)
    guardar(fig, "08_d2_cliente360.png")


if __name__ == "__main__":
    print("Generando maquetas del dashboard...")
    for f in (pg_inicio, pg_p1, pg_p2, pg_p3, pg_p4, pg_p5, pg_p6, pg_d1, pg_d2):
        f()
