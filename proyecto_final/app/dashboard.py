"""
Gráficos del dashboard de la red neuronal.

Se dibujan con matplotlib en el servidor y se envían como imágenes PNG
incrustadas, así el dashboard funciona sin internet el día de la defensa.

Reglas de visualización del docente que se respetan:
  * eje X categórico y eje Y numérico en las comparaciones (columnas);
  * series en el tiempo (épocas) con líneas;
  * ±1 desviación estándar en comparaciones con varias mediciones (pliegues);
  * nada en 3D; colores de la paleta de Okabe e Ito (apta para daltonismo).
"""

import base64
import io
import json
from functools import lru_cache

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

PALETA = ["#0072B2", "#E69F00", "#009E73", "#CC79A7", "#56B4E9", "#D55E00", "#F0E442", "#000000"]
GRIS = "#8c96a3"
plt.rcParams.update({
    "font.size": 10, "axes.spines.top": False, "axes.spines.right": False,
    "axes.titleweight": "bold", "axes.titlesize": 11, "figure.dpi": 110,
})


def a_png(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def etiquetas_cortas(nombres, largo=16):
    """Parte los nombres largos en varias líneas (sin cortarlos, para no confundir clases)."""
    import textwrap

    return ["\n".join(textwrap.wrap(n, largo)) for n in nombres]


# ----------------------------------------------------------------------------
# Gráficos por sistema
# ----------------------------------------------------------------------------
def grafico_clases(sistema, df):
    clases = sistema.clases
    partes = ["entrenamiento", "validacion", "prueba"]
    fig, ax = plt.subplots(figsize=(6.4, 3.2))
    ancho = 0.27
    x = np.arange(len(clases))
    for i, p in enumerate(partes):
        conteo = df[df["particion"] == p]["clase"].value_counts().reindex(range(len(clases)), fill_value=0)
        barras = ax.bar(x + (i - 1) * ancho, conteo.values, ancho, label=p.capitalize(), color=PALETA[i])
        ax.bar_label(barras, fontsize=7)
    ax.set_xticks(x, etiquetas_cortas(clases), rotation=0, fontsize=8)
    ax.set_ylabel("Observaciones")
    ax.set_title("Observaciones por clase y partición (60/20/20)", pad=22)
    ax.legend(fontsize=8, frameon=False, ncol=3, loc="lower center", bbox_to_anchor=(0.5, 1.0))
    ax.set_ylim(0, ax.get_ylim()[1] * 1.08)
    return a_png(fig)


def grafico_curvas(m):
    h = m["historial"]
    epocas = np.arange(1, len(h["loss"]) + 1)
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9, 3.2))
    a1.plot(epocas, h["loss"], color=PALETA[0], label="Entrenamiento")
    a1.plot(epocas, h["val_loss"], color=PALETA[1], label="Validación")
    a1.set_title("Pérdida (entropía cruzada)")
    a1.set_xlabel("Época")
    mejor = int(np.argmin(h["val_loss"])) + 1
    a1.axvline(mejor, color=GRIS, ls="--", lw=1)
    a1.annotate(f"mejor época {mejor}", (mejor, max(h["val_loss"])), fontsize=8, color=GRIS, ha="left")
    a2.plot(epocas, h["accuracy"], color=PALETA[0], label="Entrenamiento")
    a2.plot(epocas, h["val_accuracy"], color=PALETA[1], label="Validación")
    a2.set_title("Exactitud")
    a2.set_xlabel("Época")
    a2.axvline(mejor, color=GRIS, ls="--", lw=1)
    for a in (a1, a2):
        a.legend(fontsize=8, frameon=False)
    return a_png(fig)


def grafico_confusion(m, clases):
    cm = np.array(m["prueba"]["matriz_confusion"])
    prop = cm / cm.sum(axis=1, keepdims=True)
    fig, ax = plt.subplots(figsize=(4.8, 4.0))
    ax.imshow(prop, cmap="Blues", vmin=0, vmax=1)
    for i in range(len(cm)):
        for j in range(len(cm)):
            ax.text(j, i, f"{cm[i, j]}\n{prop[i, j]:.0%}", ha="center", va="center", fontsize=8,
                    color="white" if prop[i, j] > 0.55 else "#1d2733")
    cortas = etiquetas_cortas(clases, 14)
    ax.set_xticks(range(len(cm)), cortas, rotation=30, ha="right", fontsize=8)
    ax.set_yticks(range(len(cm)), cortas, fontsize=8)
    ax.set_xlabel("Clase predicha")
    ax.set_ylabel("Clase verdadera")
    ax.set_title("Matriz de confusión (prueba)")
    for s in ax.spines.values():
        s.set_visible(False)
    return a_png(fig)


def grafico_comparacion(m):
    c = m["comparacion_prueba"]
    modelos = ["Red neuronal", "Softmax lineal", "Clase mayoritaria", "Aleatorio"]
    claves = ["red_neuronal", "softmax_lineal", "clase_mayoritaria", "aleatorio"]
    exac = [c[k]["exactitud"] * 100 for k in claves]
    bal = [c[k]["exactitud_balanceada"] * 100 for k in claves]
    x = np.arange(len(modelos))
    fig, ax = plt.subplots(figsize=(6.4, 3.2))
    b1 = ax.bar(x - 0.2, exac, 0.4, label="Exactitud", color=PALETA[0])
    b2 = ax.bar(x + 0.2, bal, 0.4, label="Exactitud balanceada", color=PALETA[2])
    ax.bar_label(b1, fmt="%.1f", fontsize=7)
    ax.bar_label(b2, fmt="%.1f", fontsize=7)
    ax.set_xticks(x, modelos, fontsize=8)
    ax.set_ylabel("%")
    ax.set_ylim(0, 105)
    ax.set_title("Comparación con modelos de referencia (prueba)")
    ax.legend(fontsize=8, frameon=False, loc="upper right")
    return a_png(fig)


def grafico_busqueda(m):
    filas = m["busqueda"]
    nombres = [f"{'PCA ' if f['pca'] else ''}{'-'.join(map(str, f['ocultas']))} {f['activacion']}"
               + (" L1" if f["l1"] else "") for f in filas]
    valores = [f["exactitud_balanceada_val"] * 100 for f in filas]
    colores = [PALETA[1] if f["pca"] else PALETA[0] for f in filas]
    elegida = next(i for i, f in enumerate(filas)
                   if f["pca"] == m["elegida"]["pca"] and f["ocultas"] == m["elegida"]["ocultas"]
                   and f["activacion"] == m["elegida"]["activacion"] and f["l1"] == m["elegida"]["l1"]
                   and f["dropout"] == m["elegida"]["dropout"])
    fig, ax = plt.subplots(figsize=(9, 3.2))
    barras = ax.bar(range(len(filas)), valores, color=colores)
    barras[elegida].set_edgecolor("#000")
    barras[elegida].set_linewidth(2)
    ax.bar_label(barras, fmt="%.1f", fontsize=7)
    ax.set_xticks(range(len(filas)), nombres, rotation=35, ha="right", fontsize=7)
    ax.set_ylabel("Exactitud balanceada en validación (%)")
    ax.set_ylim(min(valores) - 10, 100)
    ax.set_title("Búsqueda de arquitectura (azul: todas las X · naranja: PCA 95 % · borde negro: elegida)")
    return a_png(fig)


def grafico_pliegues(m):
    cv = m["validacion_cruzada_5"]
    err = np.array(cv["errores"]) * 100
    fig, ax = plt.subplots(figsize=(5.6, 3.0))
    barras = ax.bar([f"Pliegue {i}" for i in range(1, 6)], err, color=PALETA[4])
    ax.bar_label(barras, fmt="%.1f", fontsize=7)
    ax.axhline(err.mean(), color=PALETA[0], lw=1.5, label=f"Promedio {err.mean():.1f} ± {err.std():.1f}")
    ax.axhspan(err.mean() - err.std(), err.mean() + err.std(), color=PALETA[0], alpha=0.12)
    ax.axhline(m["E_out"] * 100, color=PALETA[5], ls="--", lw=1.5, label=f"E_out (prueba) {m['E_out'] * 100:.1f}")
    ax.set_ylabel("Error (%)")
    ax.set_ylim(0, max(err.max(), m["E_out"] * 100) * 1.7)
    ax.set_title("Validación cruzada de 5 pliegues")
    ax.legend(fontsize=8, frameon=False, loc="upper left")
    return a_png(fig)


def grafico_mapa(sistema, df, nuevos):
    """Proyección 2D (PCA de 2 componentes sobre los datos estandarizados) con los puntos nuevos."""
    muestra = df[df["particion"] == "prueba"]
    if len(muestra) > 2500:
        muestra = muestra.sample(2500, random_state=0)
    Z = (muestra[sistema.orden_X].to_numpy(float) - sistema.media) / sistema.desv
    _, _, vt = np.linalg.svd(Z - Z.mean(axis=0), full_matrices=False)
    P = Z @ vt[:2].T
    fig, ax = plt.subplots(figsize=(6.2, 4.2))
    for k, nombre in enumerate(sistema.clases):
        sel = muestra["clase"].to_numpy() == k
        ax.scatter(P[sel, 0], P[sel, 1], s=7, alpha=0.45, color=PALETA[k], label=nombre)
    if nuevos:
        Xn = np.array([n["x"] for n in nuevos], dtype=float)
        Pn = ((Xn - sistema.media) / sistema.desv) @ vt[:2].T
        colores = [PALETA[sistema.clases.index(n["clase_predicha"])] for n in nuevos]
        ax.scatter(Pn[:, 0], Pn[:, 1], s=180, marker="*", c=colores, edgecolors="#000", linewidths=1,
                   label="Datos escritos en el aplicativo", zorder=5)
    # Zoom al 1–99 % de los datos para que los valores extremos no aplasten el gráfico
    todos = P if not nuevos else np.vstack([P, Pn])
    for eje, fijar in ((0, ax.set_xlim), (1, ax.set_ylim)):
        lo, hi = np.percentile(P[:, eje], [1, 99])
        if nuevos:
            lo, hi = min(lo, todos[:, eje][len(P):].min()), max(hi, todos[:, eje][len(P):].max())
        margen = (hi - lo) * 0.08
        fijar(lo - margen, hi + margen)
    ax.set_xlabel("v1")
    ax.set_ylabel("v2")
    ax.set_title("Datos de prueba en 2D y datos nuevos (★)")
    ax.legend(fontsize=7, frameon=False, markerscale=1.5, loc="best")
    return a_png(fig)


def grafico_red(m, dim_entrada, usa_pca):
    """Diagrama de la arquitectura: una columna de neuronas por capa con la forma de W."""
    capas = [("Entrada X", dim_entrada, "")]
    if usa_pca:
        capas.append(("PCA", m["arquitectura"]["capas"][0]["forma_W"][0], ""))
    for c in m["arquitectura"]["capas"]:
        nombre = "Softmax" if c["nombre"] == "softmax" else c["nombre"].replace("oculta_", "Oculta ")
        capas.append((nombre, c["neuronas"], f"W {c['forma_W'][0]}×{c['forma_W'][1]}\n{c['activacion']}"))
    fig, ax = plt.subplots(figsize=(9, 3.1))
    ax.axis("off")
    maximo = 8
    posiciones = []
    for i, (_, n, _) in enumerate(capas):
        mostrar = min(n, maximo)
        ys = np.linspace(-1, 1, mostrar) if mostrar > 1 else np.array([0.0])
        posiciones.append((i, ys, n > maximo))
    for (i, ys, _), (j, ys2, _) in zip(posiciones[:-1], posiciones[1:]):
        for y1 in ys:
            for y2 in ys2:
                ax.plot([i, j], [y1, y2], color="#c5ced8", lw=0.4, zorder=1)
    for k, ((nombre, n, detalle), (i, ys, cortado)) in enumerate(zip(capas, posiciones)):
        color = PALETA[2] if k == len(capas) - 1 else (PALETA[4] if k == 0 else PALETA[0])
        ax.scatter([i] * len(ys), ys, s=110, color=color, edgecolors="#fff", zorder=3)
        unidad = "características" if k == 0 else "neuronas"
        rotulo = f"{nombre}\n{n} {unidad}" + (f"\n(se dibujan {maximo})" if cortado else "")
        ax.text(i, 1.25, rotulo, ha="center", va="bottom", fontsize=8, fontweight="bold")
        if detalle:
            ax.text(i, -1.45, detalle, ha="center", va="top", fontsize=7.5, color="#45515f")
    ax.set_xlim(-0.6, len(capas) - 0.4)
    ax.set_ylim(-2.0, 2.2)
    ax.set_title(f"Arquitectura de la red · {m['arquitectura']['parametros_totales']:,} parámetros entrenables")
    return a_png(fig)


def figuras(sistema, ruta_csv, nuevos):
    """Gráficos del sistema. Los fijos se calculan una vez; el mapa incluye los datos nuevos."""
    df = _leer_csv(str(ruta_csv))
    fijas = _fijas(sistema.codigo, str(ruta_csv), sistema)
    return {**fijas, "mapa": grafico_mapa(sistema, df, nuevos)}


@lru_cache(maxsize=8)
def _leer_csv(ruta):
    return pd.read_csv(ruta)


_CACHE = {}


def _fijas(codigo, ruta, sistema):
    if codigo not in _CACHE:
        df = _leer_csv(ruta)
        m = sistema.metricas
        _CACHE[codigo] = {
            "red": grafico_red(m, len(sistema.orden_X), sistema.pre["usa_pca"]),
            "clases": grafico_clases(sistema, df),
            "curvas": grafico_curvas(m),
            "confusion": grafico_confusion(m, sistema.clases),
            "comparacion": grafico_comparacion(m),
            "busqueda": grafico_busqueda(m),
            "pliegues": grafico_pliegues(m),
        }
    return _CACHE[codigo]

