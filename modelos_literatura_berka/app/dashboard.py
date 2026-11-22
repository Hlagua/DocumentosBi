"""
Gráficos offline (matplotlib -> PNG base64) para el dashboard de los 5 modelos
de la literatura PKDD'99 / Berka (clasificación sigmoide/softmax y regresión lineal).
"""

import base64
import io
import textwrap
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
    return ["\n".join(textwrap.wrap(n, largo)) for n in nombres]


def grafico_red(m, dim_entrada, usa_pca):
    capas = [("Entrada X", dim_entrada, "")]
    if usa_pca:
        capas.append(("PCA 95%", m["arquitectura"]["capas"][0]["forma_W"][0], ""))
    for c in m["arquitectura"]["capas"]:
        n = c["nombre"].replace("oculta_", "Oculta ").replace("sigmoide", "Sigmoide").replace("softmax", "Softmax").replace("lineal", "Lineal")
        capas.append((n, c["neuronas"], f"W {c['forma_W'][0]}×{c['forma_W'][1]}\n{c['activacion']}"))
    fig, ax = plt.subplots(figsize=(9, 3.0))
    ax.axis("off")
    maximo = 8
    pos = []
    for i, (_, n, _) in enumerate(capas):
        mostrar = min(n, maximo)
        ys = np.linspace(-1, 1, mostrar) if mostrar > 1 else np.array([0.0])
        pos.append((i, ys, n > maximo))
    for (i, ys, _), (j, ys2, _) in zip(pos[:-1], pos[1:]):
        for y1 in ys:
            for y2 in ys2:
                ax.plot([i, j], [y1, y2], color="#c5ced8", lw=0.4, zorder=1)
    for k, ((nombre, n, detalle), (i, ys, cortado)) in enumerate(zip(capas, pos)):
        color = PALETA[2] if k == len(capas) - 1 else (PALETA[4] if k == 0 else PALETA[0])
        ax.scatter([i] * len(ys), ys, s=110, color=color, edgecolors="#fff", zorder=3)
        unidad = "variables" if k == 0 else "neuronas"
        rot = f"{nombre}\n{n} {unidad}" + (f"\n(muestra {maximo})" if cortado else "")
        ax.text(i, 1.25, rot, ha="center", va="bottom", fontsize=8, fontweight="bold")
        if detalle:
            ax.text(i, -1.45, detalle, ha="center", va="top", fontsize=7.5, color="#45515f")
    ax.set_xlim(-0.6, len(capas) - 0.4)
    ax.set_ylim(-2.0, 2.2)
    ax.set_title(f"Arquitectura · {m['arquitectura']['parametros_totales']:,} parámetros entrenables")
    return a_png(fig)


def grafico_curvas(m):
    h = m["historial"]
    ep = np.arange(1, len(h["loss"]) + 1)
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9, 3.1))
    a1.plot(ep, h["loss"], color=PALETA[0], label="Entrenamiento")
    a1.plot(ep, h["val_loss"], color=PALETA[1], label="Validación")
    a1.set_title("Pérdida (" + m["hiperparametros_fijos"]["perdida"] + ")")
    a1.set_xlabel("Época")
    mejor = int(np.argmin(h["val_loss"])) + 1
    a1.axvline(mejor, color=GRIS, ls="--", lw=1)

    met_k = "mae" if m["tipo"] == "regresion" else "accuracy"
    a2.plot(ep, h[met_k], color=PALETA[0], label="Entrenamiento")
    a2.plot(ep, h["val_" + met_k], color=PALETA[1], label="Validación")
    a2.set_title("MAE escalado" if met_k == "mae" else "Exactitud")
    a2.set_xlabel("Época")
    a2.axvline(mejor, color=GRIS, ls="--", lw=1)
    for a in (a1, a2):
        a.legend(fontsize=8, frameon=False)
    return a_png(fig)


def grafico_busqueda(m):
    filas = m["busqueda"]
    nombres = [f"{'PCA ' if f['pca'] else ''}{'-'.join(map(str, f['ocultas']))} {f['activacion']}" for f in filas]
    if m["tipo"] == "regresion":
        valores = [f["r2_val"] * 100 for f in filas]
        ylab = "R² en validación (%)"
    elif m["salida"] == "sigmoid":
        valores = [f["auc_val"] * 100 for f in filas]
        ylab = "AUC-ROC en validación (%)"
    else:
        valores = [f["exactitud_balanceada_val"] * 100 for f in filas]
        ylab = "Exactitud balanceada en validación (%)"

    colores = [PALETA[1] if f["pca"] else PALETA[0] for f in filas]
    elegida = next(i for i, f in enumerate(filas)
                   if f["pca"] == m["elegida"]["pca"] and f["ocultas"] == m["elegida"]["ocultas"]
                   and f["activacion"] == m["elegida"]["activacion"])
    fig, ax = plt.subplots(figsize=(9, 3.1))
    barras = ax.bar(range(len(filas)), valores, color=colores)
    barras[elegida].set_edgecolor("#000")
    barras[elegida].set_linewidth(2)
    ax.bar_label(barras, fmt="%.1f", fontsize=7)
    ax.set_xticks(range(len(filas)), nombres, rotation=30, ha="right", fontsize=7.5)
    ax.set_ylabel(ylab)
    ax.set_ylim(max(0, min(valores) - 10), min(105, max(valores) + 10))
    ax.set_title("Búsqueda de arquitectura (azul: todas las X · naranja: PCA 95 % · borde negro: elegida)")
    return a_png(fig)


def grafico_evaluacion_clasificacion(sistema, m, df):
    # 1. Clases por partición
    clases = sistema.clases
    fig, ax = plt.subplots(figsize=(6.2, 3.1))
    ancho = 0.27
    x = np.arange(len(clases))
    for i, p in enumerate(["entrenamiento", "validacion", "prueba"]):
        conteo = df[df["particion"] == p]["clase"].value_counts().reindex(range(len(clases)), fill_value=0)
        b = ax.bar(x + (i - 1) * ancho, conteo.values, ancho, label=p.capitalize(), color=PALETA[i])
        ax.bar_label(b, fontsize=7)
    ax.set_xticks(x, etiquetas_cortas(clases), fontsize=8)
    ax.set_ylabel("Observaciones")
    ax.set_title("Observaciones por clase y partición (60/20/20)", pad=20)
    ax.legend(fontsize=8, frameon=False, ncol=3, loc="lower center", bbox_to_anchor=(0.5, 1.0))
    g_clases = a_png(fig)

    # 2. Matriz de confusión
    cm = np.array(m["prueba"]["matriz_confusion"])
    prop = cm / cm.sum(axis=1, keepdims=True)
    fig, ax = plt.subplots(figsize=(4.6, 3.8))
    ax.imshow(prop, cmap="Blues", vmin=0, vmax=1)
    for i in range(len(cm)):
        for j in range(len(cm)):
            ax.text(j, i, f"{cm[i, j]}\n{prop[i, j]:.0%}", ha="center", va="center", fontsize=8,
                    color="white" if prop[i, j] > 0.55 else "#1d2733")
    cortas = etiquetas_cortas(clases, 14)
    ax.set_xticks(range(len(cm)), cortas, rotation=25, ha="right", fontsize=8)
    ax.set_yticks(range(len(cm)), cortas, fontsize=8)
    ax.set_xlabel("Predicha")
    ax.set_ylabel("Verdadera")
    ax.set_title("Matriz de confusión (prueba)")
    for s in ax.spines.values():
        s.set_visible(False)
    g_cm = a_png(fig)

    # 3. Comparación con referencias
    c = m["comparacion_prueba"]
    modelos = ["Red neuronal", c["modelo_lineal"]["nombre"].split(" (")[0], "Mayoritaria", "Aleatorio"]
    claves = ["red_neuronal", "modelo_lineal", "clase_mayoritaria", "aleatorio"]
    exac = [c[k]["exactitud"] * 100 for k in claves]
    bal = [c[k]["exactitud_balanceada"] * 100 for k in claves]
    x = np.arange(len(modelos))
    fig, ax = plt.subplots(figsize=(6.2, 3.1))
    b1 = ax.bar(x - 0.2, exac, 0.4, label="Exactitud", color=PALETA[0])
    b2 = ax.bar(x + 0.2, bal, 0.4, label="Exactitud balanceada", color=PALETA[2])
    ax.bar_label(b1, fmt="%.1f", fontsize=7)
    ax.bar_label(b2, fmt="%.1f", fontsize=7)
    ax.set_xticks(x, modelos, fontsize=8)
    ax.set_ylabel("%")
    ax.set_ylim(0, 108)
    ax.set_title("Comparación con modelos de referencia (prueba)")
    ax.legend(fontsize=8, frameon=False)
    g_comp = a_png(fig)

    # 4. CV-5
    err = np.array(m["validacion_cruzada_5"]["errores"]) * 100
    fig, ax = plt.subplots(figsize=(5.6, 3.0))
    b = ax.bar([f"Pliegue {i}" for i in range(1, 6)], err, color=PALETA[4])
    ax.bar_label(b, fmt="%.1f", fontsize=7)
    ax.axhline(err.mean(), color=PALETA[0], lw=1.5, label=f"Promedio {err.mean():.1f} ± {err.std():.1f} %")
    ax.axhline(m["E_out"] * 100, color=PALETA[5], ls="--", lw=1.5, label=f"E_out prueba {m['E_out']*100:.1f} %")
    ax.set_ylabel("Error (%)")
    ax.set_ylim(0, max(err.max(), m["E_out"] * 100) * 1.65)
    ax.set_title("Validación cruzada (5 pliegues)")
    ax.legend(fontsize=8, frameon=False)
    g_cv = a_png(fig)

    return {"principal_1": g_clases, "principal_2": g_cm, "comparacion": g_comp, "pliegues": g_cv}


def grafico_evaluacion_regresion(sistema, m, df):
    te = df[df["particion"] == "prueba"]
    Xte = te[sistema.orden_X].to_numpy(float)
    y_real = te["objetivo"].to_numpy(float)
    y_pred = np.clip(sistema.red.predict(sistema.transformar(Xte), verbose=0, batch_size=1024).ravel() * sistema.y_desv + sistema.y_media, 0, None)

    # 1. Real vs Predicho
    fig, ax = plt.subplots(figsize=(5.5, 3.6))
    ax.scatter(y_real, y_pred, s=8, alpha=0.35, color=PALETA[0])
    lim = np.percentile(np.concatenate([y_real, y_pred]), 99)
    ax.plot([0, lim], [0, lim], color=PALETA[5], ls="--", lw=1.5, label="Ideal (y = ŷ)")
    ax.set_xlim(0, lim)
    ax.set_ylim(0, lim)
    ax.set_xlabel("Monto real mes t+1 (CZK)")
    ax.set_ylabel("Monto predicho mes t+1 (CZK)")
    ax.set_title(f"Real vs. Predicho en prueba (R² = {m['prueba']['r2']:.3f})")
    ax.legend(fontsize=8, frameon=False)
    g_scatter = a_png(fig)

    # 2. Distribución de errores
    res = y_pred - y_real
    lo, hi = np.percentile(res, [2, 98])
    fig, ax = plt.subplots(figsize=(5.5, 3.6))
    ax.hist(res[(res >= lo) & (res <= hi)], bins=35, color=PALETA[4], edgecolor="#fff")
    ax.axvline(0, color=PALETA[5], ls="--", lw=1.5)
    ax.set_xlabel("Error (predicho − real, CZK)")
    ax.set_ylabel("Frecuencia")
    ax.set_title(f"Distribución de errores (MAE = {m['prueba']['mae']:,.0f} CZK)")
    g_hist = a_png(fig)

    # 3. Comparación R² con referencias
    c = m["comparacion_prueba"]
    nombres = ["Red neuronal", "Regresión lineal", "Persistencia (mes t)", "Media constante"]
    claves = ["red_neuronal", "regresion_lineal", "persistencia_mes_anterior", "media_constante"]
    r2s = [c[k]["r2"] * 100 for k in claves]
    fig, ax = plt.subplots(figsize=(6.2, 3.1))
    b = ax.bar(nombres, r2s, color=[PALETA[0], PALETA[1], PALETA[2], GRIS])
    ax.bar_label(b, fmt="%.1f", fontsize=7.5)
    ax.set_ylabel("R² en prueba (%)")
    ax.set_ylim(min(0, min(r2s) - 10), 100)
    ax.set_title("Comparación de R² con modelos de referencia (prueba)")
    g_comp = a_png(fig)

    # 4. CV-5 R²
    r2_cv = np.array(m["validacion_cruzada_5"]["r2_pliegues"]) * 100
    fig, ax = plt.subplots(figsize=(5.6, 3.0))
    b = ax.bar([f"Pliegue {i}" for i in range(1, 6)], r2_cv, color=PALETA[2])
    ax.bar_label(b, fmt="%.1f", fontsize=7.5)
    ax.axhline(r2_cv.mean(), color=PALETA[0], lw=1.5, label=f"Promedio {r2_cv.mean():.1f} ± {r2_cv.std():.1f} %")
    ax.axhline(m["prueba"]["r2"] * 100, color=PALETA[5], ls="--", lw=1.5, label=f"Prueba {m['prueba']['r2']*100:.1f} %")
    ax.set_ylabel("R² (%)")
    ax.set_ylim(0, 100)
    ax.set_title("Validación cruzada (5 pliegues)")
    ax.legend(fontsize=8, frameon=False)
    g_cv = a_png(fig)

    return {"principal_1": g_scatter, "principal_2": g_hist, "comparacion": g_comp, "pliegues": g_cv}


@lru_cache(maxsize=8)
def _leer_csv(ruta):
    return pd.read_csv(ruta)


_CACHE = {}


def figuras(sistema, ruta_csv, nuevos):
    if sistema.codigo not in _CACHE:
        df = _leer_csv(str(ruta_csv))
        m = sistema.metricas
        base = {
            "red": grafico_red(m, len(sistema.orden_X), sistema.pre["usa_pca"]),
            "curvas": grafico_curvas(m),
            "busqueda": grafico_busqueda(m),
        }
        if sistema.tipo == "regresion":
            base.update(grafico_evaluacion_regresion(sistema, m, df))
        else:
            base.update(grafico_evaluacion_clasificacion(sistema, m, df))
        _CACHE[sistema.codigo] = base
    return _CACHE[sistema.codigo]


def grafico_resumen(sistemas):
    codigos = list(sistemas)
    etiquetas, vals_red, vals_lin = [], [], []
    for c in codigos:
        s = sistemas[c]
        m = s.metricas
        if s.tipo == "regresion":
            vals_red.append(m["prueba"]["r2"] * 100)
            vals_lin.append(m["comparacion_prueba"]["regresion_lineal"]["r2"] * 100)
            etiquetas.append(f"{c}\n(R² lineal)")
        elif s.salida == "sigmoid":
            vals_red.append(m["prueba"]["auc"] * 100)
            vals_lin.append(m["comparacion_prueba"]["modelo_lineal"]["auc"] * 100)
            etiquetas.append(f"{c}\n(AUC sigmoide)")
        else:
            vals_red.append(m["prueba"]["exactitud_balanceada"] * 100)
            vals_lin.append(m["comparacion_prueba"]["modelo_lineal"]["exactitud_balanceada"] * 100)
            etiquetas.append(f"{c}\n(Bal. softmax)")
    x = np.arange(len(codigos))
    fig, ax = plt.subplots(figsize=(8.6, 3.3))
    b1 = ax.bar(x - 0.2, vals_red, 0.38, label="Red neuronal (MLP)", color=PALETA[0])
    b2 = ax.bar(x + 0.2, vals_lin, 0.38, label="Modelo lineal (0 capas ocultas)", color=PALETA[1])
    ax.bar_label(b1, fmt="%.1f", fontsize=7.5)
    ax.bar_label(b2, fmt="%.1f", fontsize=7.5)
    ax.set_xticks(x, etiquetas, fontsize=8.5)
    ax.set_ylabel("Métrica principal en prueba (%)")
    ax.set_ylim(0, 108)
    ax.set_title("Los 5 modelos de la literatura PKDD'99 / Berka frente a sus baselines lineales")
    ax.legend(fontsize=8.5, frameon=False)
    return a_png(fig)
