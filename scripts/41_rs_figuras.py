"""
==============================================================================
UNIVERSIDAD TÉCNICA DE AMBATO - Inteligencia de Negocios
AUTORES: Alison Marcela Cobos Taco / Henry Daniel Lagua Flores
==============================================================================
ARCHIVO: 41_rs_figuras.py
SISTEMAS DE RECOMENDACIÓN (Informe 04 v2) — FIGURAS
DESCRIPCIÓN: Genera las figuras del informe EXCLUSIVAMENTE a partir de
             metricas_recomendadores.json (scripts 37 a 40): ningún valor se
             escribe a mano. Salida: img/recomendadores/fig_rs_*.png (200 DPI).
USO: python scripts/41_rs_figuras.py
==============================================================================
"""
import json
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SALIDA = os.path.join(BASE_DIR, "img", "recomendadores")
M = json.load(open(os.path.join(BASE_DIR, "metricas_recomendadores.json"), encoding="utf-8"))
AZUL, NARANJA, GRIS, VERDE, ROJO = "#1565C0", "#EF6C00", "#9E9E9E", "#2E7D32", "#8E1B1B"
NOMBRES = {"SERVICIOS_HOGAR": "Serv. hogar", "TRANSF_SALIENTE": "Transf. saliente", "INGRESO_TRANSF": "Ingreso transf.",
           "RETIRO_TARJETA": "Retiro tarjeta", "PENSION": "Pensión", "PRESTAMO": "Préstamo", "SEGURO": "Seguro", "LEASING": "Leasing"}
plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False, "figure.dpi": 100})


def guardar(fig, nombre):
    fig.tight_layout()
    fig.savefig(os.path.join(SALIDA, nombre), dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("  img/recomendadores/" + nombre)


def mapa_calor(ax, df, titulo, fmt="{:.2f}", cmap="RdBu_r", vmin=-1, vmax=1):
    etiquetas = [NOMBRES.get(c, c) for c in df.columns]
    im = ax.imshow(df.values.astype(float), cmap=cmap, vmin=vmin, vmax=vmax)
    ax.set_xticks(range(len(df.columns)), etiquetas, rotation=45, ha="right")
    ax.set_yticks(range(len(df.index)), [NOMBRES.get(i, i) for i in df.index])
    divergente = cmap in ("RdBu_r", "RdBu")
    for (i, j), v in np.ndenumerate(df.values.astype(float)):
        if not np.isnan(v):
            # Texto blanco solo sobre celdas oscuras: extremos en escalas divergentes, valores altos en las secuenciales
            oscuro = abs(v - (vmin + vmax) / 2) > (vmax - vmin) * 0.3 if divergente else (v - vmin) > (vmax - vmin) * 0.6
            ax.text(j, i, fmt.format(v), ha="center", va="center", fontsize=7, color="white" if oscuro else "black")
    ax.set_title(titulo, fontweight="bold")
    ax.spines[:].set_visible(False)
    return im


def main():
    os.makedirs(SALIDA, exist_ok=True)
    prep, so, ii, pc = M["preparacion"], M["slope_one"], M["item_item"], M["perfiles_contenido"]
    print("Generando figuras:")

    # 1. Catálogo: cuentas por producto y productos por cuenta
    fig, (a, b) = plt.subplots(1, 2, figsize=(10, 3.6))
    cp = pd.Series(prep["punto_3_clasificar"]["cuentas_por_producto"])
    a.barh([NOMBRES[k] for k in cp.index][::-1], cp.values[::-1], color=AZUL)
    for y, v in enumerate(cp.values[::-1]):
        a.text(v + 40, y, f"{v:,} ({v / 4500:.0%})", va="center", fontsize=8)
    a.set_title("Cuentas que tienen cada producto (de 4,500)", fontweight="bold")
    a.set_xlim(0, cp.max() * 1.3)
    npc = pd.Series(prep["punto_4_filtrar"]["cuentas_por_numero_de_productos"])
    b.bar(npc.index.astype(str), npc.values, color=[GRIS if int(k) < 2 else AZUL for k in npc.index])
    for x, v in enumerate(npc.values):
        b.text(x, v + 20, f"{v:,}", ha="center", fontsize=8)
    b.set_title(f"Productos por cuenta (dispersión {prep['punto_4_filtrar']['dispersion']:.1%})", fontweight="bold")
    b.set_xlabel("Número de productos (azul: evaluables, 2 o más)")
    guardar(fig, "fig_rs_01_catalogo.png")

    # 2. Slope One: desviaciones
    fig, ax = plt.subplots(figsize=(6.5, 5.2))
    mapa_calor(ax, pd.DataFrame(so["matriz_desviaciones"]).T, "Slope One: desviación media b(j, i)\n(fila j = producto a predecir)", vmin=-1.5, vmax=1.5)
    guardar(fig, "fig_rs_02_slope_one_desviaciones.png")

    # 3. Validación 5-fold
    cv = so["validacion_5fold"]["modelos"]
    etiquetas = {"slope_one": "Slope One", "media_producto": "Media del producto", "sesgos": "Sesgos (global + cliente + producto)",
                 "media_global": "Media global", "media_cliente": "Media del cliente"}
    orden = sorted(cv, key=lambda k: cv[k]["mae"])
    fig, ax = plt.subplots(figsize=(7, 3.2))
    ax.barh([etiquetas[k] for k in orden][::-1], [cv[k]["mae"] for k in orden][::-1],
            xerr=[cv[k]["mae_desv"] for k in orden][::-1], color=[NARANJA if k == "slope_one" else GRIS for k in orden][::-1])
    for y, k in enumerate(orden[::-1]):
        ax.text(cv[k]["mae"] + 0.01, y, f"{cv[k]['mae']:.3f}", va="center", fontsize=8)
    ax.set_xlabel("MAE en validación cruzada 5-fold (menor es mejor)")
    ax.set_title("Slope One frente a los baselines al predecir la intensidad de uso", fontweight="bold")
    guardar(fig, "fig_rs_03_slope_one_5fold.png")

    # 4. Ítem a ítem: coseno binario y phi
    fig, (a, b) = plt.subplots(1, 2, figsize=(11, 4.8))
    mapa_calor(a, pd.DataFrame(ii["adopcion"]["coseno_binario"]).T, "Coseno binario (co-adquisición)", cmap="Blues", vmin=0, vmax=1)
    mapa_calor(b, pd.DataFrame(ii["adopcion"]["pearson_phi"]).T, "Pearson (phi) sobre la adopción")
    guardar(fig, "fig_rs_04_item_item.png")

    # 5. Comparación de recomendadores (partición de selección)
    evals = {**{"Slope One": so["ranking"]["Slope One"]},
             **{k: v for k, v in ii["ranking"].items() if k != "Popularidad"},
             **pc["ranking"]["seleccion"]}
    # Sin la referencia sesgada ni el duplicado de P(j|i) que el script 40 reevalúa para elegir el modelo
    evals = {k: v for k, v in evals.items() if "referencia sesgada" not in k and k != "Ítem a ítem P(j|i)"}
    orden = sorted(evals, key=lambda k: evals[k]["mrr"])
    fig, ax = plt.subplots(figsize=(9, 5.2))
    y = np.arange(len(orden))
    ax.barh(y + 0.2, [evals[k]["hit_1"] for k in orden], 0.4, color=AZUL, label="Hit@1 global")
    ax.barh(y - 0.2, [evals[k]["cola_larga"]["hit_1"] for k in orden], 0.4, color=NARANJA, label="Hit@1 en la cola larga")
    ax.set_yticks(y, orden)
    for i, k in enumerate(orden):
        ax.text(evals[k]["hit_1"] + 0.01, i + 0.2, f"{evals[k]['hit_1']:.0%}", va="center", fontsize=7)
        ax.text(evals[k]["cola_larga"]["hit_1"] + 0.01, i - 0.2, f"{evals[k]['cola_larga']['hit_1']:.0%}", va="center", fontsize=7)
    ax.set_xlim(0, 1)
    ax.legend(loc="lower right")
    ax.set_title("Recomendadores con el mismo protocolo (ordenados por MRR)\nCola larga: el producto oculto no es servicios del hogar ni transferencia saliente",
                 fontweight="bold")
    guardar(fig, "fig_rs_05_comparacion_modelos.png")

    # 6. Perfiles: adopción por arquetipo
    fig, ax = plt.subplots(figsize=(9, 4.6))
    arq = pd.DataFrame(pc["punto_6_perfiles"]["adopcion_por_arquetipo"]).T
    mapa_calor(ax, arq, "Adopción de cada producto por arquetipo (proporción de cuentas)", cmap="Oranges", vmin=0, vmax=1)
    guardar(fig, "fig_rs_06_arquetipos.png")

    # 7. Utilidad: impago por regla
    u = pc["utilidad"]
    fig, (a, b) = plt.subplots(1, 2, figsize=(10, 3.6), sharey=True)
    for ax, datos, titulo, color in [
        (a, u["regla_anterior_cuota_salario_distrital"]["tramos"],
         f"Regla anterior: cuota / salario del distrito\nAUC = {u['regla_anterior_cuota_salario_distrital']['auc_impago']:.3f}", GRIS),
        (b, u["regla_carta_v8_cuota_saldo_previo"]["bandas"],
         f"Carta v8: cuota / saldo previo del cliente\nAUC = {u['regla_carta_v8_cuota_saldo_previo']['auc_impago']:.3f}", NARANJA)]:
        ks = list(datos)
        ax.bar(ks, [datos[k]["tasa"] for k in ks], color=color)
        for x, k in enumerate(ks):
            ax.text(x, datos[k]["tasa"] + 0.005, f"{datos[k]['tasa']:.1%}\n({datos[k]['impagos']}/{datos[k]['prestamos']})", ha="center", fontsize=8)
        ax.set_title(titulo, fontweight="bold")
    a.set_ylabel("Tasa de impago (B o D)")
    a.set_ylim(0, 0.3)
    guardar(fig, "fig_rs_07_utilidad_prestamos.png")

    # 8. Contenidos: similitud entre productos por atributos
    fig, ax = plt.subplots(figsize=(6.5, 5.2))
    mapa_calor(ax, pd.DataFrame(pc["punto_8_contenidos"]["similitud_atributos"]).T, "Contenidos: coseno entre vectores de atributos",
               cmap="Greens", vmin=0, vmax=1)
    guardar(fig, "fig_rs_08_contenidos.png")


if __name__ == "__main__":
    main()
