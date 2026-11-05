"""
Práctica (Tarea 1 - 2do Parcial): Reducción de dimensionalidad a un plano euclidiano 2D
                                  (t-SNE e Isomap, con referencia MNIST) en los 4 Data Marts
Asignatura: Inteligencia de Negocios - Carrera de Software, 6to "A"
Autores: Cobos Taco Alison Marcela / Lagua Flores Henry Daniel

Implementa la formulación de clase (pizarra 1):
    Dado X = {(x_1, y_1), ..., (x_N, y_N)}, con y_i en {1, 2, ..., S}
    y x_i = [x_1, x_2, ..., x_n] en R^n (n > 2),
    reducir cada vector de características a dos componentes en un plano euclidiano:
        x_i^(1) = [v_1, v_2] en R^2
    para graficar los grupos coloreando cada observación según su clase real.

Criterios:
  - Se usan TODAS las características X de cada dataset y TODAS sus observaciones
    reales (un punto por observación), sin balancear ni muestrear: el balanceo solo
    se necesita para entrenar un clasificador (Tarea 2), no para visualizar.
  - Cada característica se estandariza (z-score) para que ninguna domine la distancia.
  - Dos reducciones no lineales lado a lado: t-SNE e Isomap.
  - Se generan los 4 gráficos individuales multiclase (3 a 4 colores por Data Mart,
    t-SNE frente a Isomap) y los 4 gráficos individuales binarios (2 colores).

Incluye:
  1. Demostración de referencia sobre el dataset MNIST real (OpenML `mnist_784`:
     70,000 imágenes de 28 x 28 = 784 píxeles), con una muestra estratificada de
     3,000 imágenes (300 por dígito): 10 clases y caso binario 0 frente a 1.
  2. Reducción a [v_1, v_2] de los 4 Data Marts de DM_Financial_Kimball_v2, tanto en
     sus clases múltiples reales (3 a 4 clases por Data Mart) como en su versión binaria.

Ejecución (desde la raíz del repositorio):
    python 2parcial/Tarea1_Reduccion_MNIST_2D/reduccion_mnist_2d.py
"""

from pathlib import Path
import json
import time
import warnings

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw, ImageFont
from scipy.sparse.csgraph import connected_components
from sklearn.datasets import fetch_openml
from sklearn.manifold import TSNE, Isomap
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.neighbors import KNeighborsClassifier, kneighbors_graph

# Isomap completa por sí mismo el grafo cuando queda dividido; se informa en consola
warnings.filterwarnings("ignore", message="The number of connected components")
warnings.filterwarnings("ignore", category=UserWarning, module="scipy.sparse")
warnings.filterwarnings("ignore", message="Changing the sparsity structure")

CARPETA = Path(__file__).resolve().parent
DIR_2P = CARPETA.parent
SALIDA = CARPETA / "resultados"
CAPTURAS = CARPETA / "capturas"
SALIDA.mkdir(parents=True, exist_ok=True)
CAPTURAS.mkdir(parents=True, exist_ok=True)

SEMILLA = 42
PERPLEXITY = 30.0
VECINOS_ISOMAP = 20  # con 10 o 15 vecinos el grafo queda dividido en Saldo Mensual y Órdenes
MNIST_POR_DIGITO = 300  # 300 x 10 = 3,000 imágenes reales de MNIST

plt.rcParams.update({
    "font.family": "Times New Roman",
    "font.size": 11,
    "axes.titlesize": 12,
    "savefig.dpi": 200,
})

PALETA = {1: "#1f77b4", 2: "#2ca02c", 3: "#d62728", 4: "#ff7f0e", 5: "#9467bd"}
PALETA_BIN = {0: "#1f77b4", 1: "#d62728"}

DATASETS_CONFIG = [
    {
        "id": "DM1_Prestamos",
        "nombre": "DM1: Préstamos (Mora vs. Sano)",
        "archivo": "01_dm_prestamos.csv",
        "tabla_hechos": "Fact_Prestamos",
        "tiene_multiclase": True,
        "titulo_multi": "DM1: Préstamos por Estado Real (A, B, C, D)",
    },
    {
        "id": "DM2_Saldo_Mensual",
        "nombre": "DM2: Saldo Mensual (Sobregiro t+1)",
        "archivo": "02_dm_saldo_mensual.csv",
        "tabla_hechos": "Fact_Saldo_Cuenta_Mensual",
        "tiene_multiclase": True,
        "titulo_multi": "DM2: Saldo Mensual por Liquidez en t+1 (Estable, Caída, Sobregiro)",
    },
    {
        "id": "DM3_Ordenes",
        "nombre": "DM3: Órdenes (Obligación vs. Hogar)",
        "archivo": "03_dm_ordenes.csv",
        "tabla_hechos": "Fact_Ordenes",
        "tiene_multiclase": True,
        "titulo_multi": "DM3: Órdenes por Tipo Real (SIPO, UVER, POJISTNE, LEASING)",
    },
    {
        "id": "DM4_Transacciones",
        "nombre": "DM4: Transacciones (Egreso vs. Ingreso)",
        "archivo": "04_dm_transacciones.csv",
        "tabla_hechos": "Fact_Transacciones",
        "tiene_multiclase": True,
        "titulo_multi": "DM4: Transacciones por Operación Real (VKLAD, VYBER, PREVOD)",
    },
]


def estandarizar(X_raw):
    """z-score de cada característica con la media y desviación de todas las observaciones."""
    mu = X_raw.mean(axis=0)
    sigma = X_raw.std(axis=0)
    sigma = np.where(sigma < 1e-8, 1.0, sigma)
    return (X_raw - mu) / sigma


def reducir_tsne(X):
    tsne = TSNE(n_components=2, perplexity=PERPLEXITY, init="pca", learning_rate="auto", random_state=SEMILLA)
    Z = tsne.fit_transform(X)
    return Z, float(tsne.kl_divergence_)


def reducir_isomap(X, vecinos=VECINOS_ISOMAP):
    """Isomap: distancias geodésicas sobre el grafo de k vecinos y escalamiento clásico a 2D."""
    n_comp = connected_components(kneighbors_graph(X, vecinos), directed=False)[0]
    iso = Isomap(n_neighbors=vecinos, n_components=2, eigen_solver="arpack")
    Z = iso.fit_transform(X)
    return Z, float(iso.reconstruction_error()), int(n_comp)


def evaluar_proyeccion_2d(Z, y):
    """
    Mide qué tan separadas quedan las clases en el plano 2D [v1, v2]:
      - Exactitud de un kNN (k = 5) con validación cruzada estratificada de 5
        pliegues: cada punto se clasifica con vecinos de OTROS pliegues, así que
        no se evalúa sobre los mismos puntos con los que se ajustó.
      - Distancia euclidiana media entre los centroides de las clases.
    """
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEMILLA)
    acc_2d = float(cross_val_score(KNeighborsClassifier(n_neighbors=5), Z, y, cv=cv).mean())
    clases = np.unique(y)
    centroides = [Z[y == c].mean(axis=0) for c in clases]
    dists = [
        np.linalg.norm(centroides[i] - centroides[j])
        for i in range(len(centroides))
        for j in range(i + 1, len(centroides))
    ]
    return acc_2d, float(np.mean(dists))


def tam_punto(n):
    """Tamaño de punto según la cantidad de observaciones (un punto por observación)."""
    if n <= 1000:
        return 14
    if n <= 6000:
        return 6
    return 2.5


def dispersion(ax, Z, y, nombres, paleta, titulo, xlabel="v₁", ylabel="v₂"):
    """Dibuja un punto por observación con un color por clase; la clase más grande va al fondo."""
    clases = sorted(np.unique(y), key=lambda c: -(y == c).sum())
    s = tam_punto(len(y))
    for c in clases:
        m = y == c
        ax.scatter(Z[m, 0], Z[m, 1], s=s, c=paleta[c], alpha=0.65, linewidths=0,
                   label=f"{nombres[c]} (n = {int(m.sum()):,})")
    ax.set_title(titulo)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.grid(True, alpha=0.25)
    leg = ax.legend(loc="best", fontsize=8.5, markerscale=max(1.0, 12 / s))
    for h in leg.legend_handles:
        h.set_alpha(1.0)


def ejecutar_mnist_referencia(lineas_consola):
    """Ejecuta la demostración de referencia con MNIST real (10 clases y 2 clases)."""
    mnist = fetch_openml("mnist_784", version=1, as_frame=False, parser="auto")
    X_todo = mnist.data.astype(float)
    y_todo = mnist.target.astype(int)
    rng = np.random.default_rng(SEMILLA)
    idx = np.concatenate([
        rng.choice(np.flatnonzero(y_todo == d), size=MNIST_POR_DIGITO, replace=False)
        for d in range(10)
    ])
    X = X_todo[idx] / 255.0
    y = y_todo[idx]
    imagenes = X.reshape(-1, 28, 28)

    # 1. Muestra de imágenes MNIST
    fig, axes = plt.subplots(2, 5, figsize=(9.5, 4.0))
    for digito, ax in enumerate(axes.ravel()):
        ax.imshow(imagenes[y == digito][0], cmap="gray_r", interpolation="nearest")
        ax.set_title(f"Dígito y = {digito}", fontsize=10)
        ax.axis("off")
    fig.suptitle("Muestra del dataset MNIST real: imágenes de 28 x 28 píxeles (n = 784 características -> R^2)",
                 fontsize=12)
    fig.tight_layout()
    fig.savefig(SALIDA / "mnist_muestra_digitos.png", dpi=200)
    plt.close(fig)

    # 2. Proyección 2D de las 10 clases (t-SNE vs Isomap)
    Z_tsne, kl_10 = reducir_tsne(X)
    Z_iso, err_iso_10, _ = reducir_isomap(X, 10)
    acc_tsne_10, _ = evaluar_proyeccion_2d(Z_tsne, y)
    acc_iso_10, _ = evaluar_proyeccion_2d(Z_iso, y)

    cmap10 = plt.get_cmap("tab10")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13.5, 5.8))
    for ax, Z in ((ax1, Z_tsne), (ax2, Z_iso)):
        for digito in range(10):
            m = y == digito
            ax.scatter(Z[m, 0], Z[m, 1], s=10, alpha=0.75, color=cmap10(digito), linewidths=0,
                       label=f"Dígito {digito}")
            c = Z[m].mean(axis=0)
            ax.text(c[0], c[1], str(digito), fontsize=10, fontweight="bold", ha="center", va="center",
                    bbox=dict(boxstyle="circle,pad=0.18", fc="white", ec="black", alpha=0.85))
        ax.set_xlabel("v₁")
        ax.set_ylabel("v₂")
        ax.grid(True, alpha=0.25)
    ax1.set_title(f"t-SNE, {len(X):,} imágenes (KL = {kl_10:.3f}, Acc 2D = {100*acc_tsne_10:.2f} %)")
    ax2.set_title(f"Isomap, {len(X):,} imágenes (Acc 2D = {100*acc_iso_10:.2f} %)")
    ax2.legend(loc="best", fontsize=8, ncol=2, markerscale=1.6)
    fig.suptitle("MNIST: dispersión v₁ contra v₂, un color por clase y un punto por imagen", fontsize=13)
    fig.tight_layout()
    fig.savefig(SALIDA / "mnist_10clases_tsne_vs_isomap.png", dpi=200)
    plt.close(fig)

    # 3. MNIST binario (Dígito 0 vs Dígito 1) como puente hacia la Tarea 2
    m_bin = (y == 0) | (y == 1)
    X_bin, y_bin = X[m_bin], y[m_bin]
    Z_tsne_bin, _ = reducir_tsne(X_bin)
    Z_iso_bin, _, _ = reducir_isomap(X_bin, 10)
    acc_tsne_bin, _ = evaluar_proyeccion_2d(Z_tsne_bin, y_bin)
    acc_iso_bin, _ = evaluar_proyeccion_2d(Z_iso_bin, y_bin)

    nombres_bin = {0: "Dígito 0", 1: "Dígito 1"}
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12.5, 5.2))
    dispersion(ax1, Z_tsne_bin, y_bin, nombres_bin, PALETA_BIN,
               f"t-SNE, MNIST 0 vs. 1 (Acc 2D = {100*acc_tsne_bin:.2f} %)")
    dispersion(ax2, Z_iso_bin, y_bin, nombres_bin, PALETA_BIN,
               f"Isomap, MNIST 0 vs. 1 (Acc 2D = {100*acc_iso_bin:.2f} %)")
    fig.tight_layout()
    fig.savefig(SALIDA / "mnist_binario_0vs1.png", dpi=200)
    plt.close(fig)

    msg = (
        f"[Referencia MNIST] N = {len(X):,} imágenes (de {len(X_todo):,}) | n = {X.shape[1]} características -> [v1, v2]\n"
        f"  * 10 Clases (0..9) -> t-SNE: KL = {kl_10:.4f}, Acc 2D = {100*acc_tsne_10:.2f} % | "
        f"Isomap: Acc 2D = {100*acc_iso_10:.2f} %\n"
        f"  * Binario (0 vs 1) -> N = {len(X_bin)} | t-SNE Acc 2D = {100*acc_tsne_bin:.2f} % | "
        f"Isomap Acc 2D = {100*acc_iso_bin:.2f} %"
    )
    print(msg)
    lineas_consola.extend(msg.split("\n"))

    return {
        "N_total": int(len(X)),
        "N_mnist_completo": int(len(X_todo)),
        "n_features": int(X.shape[1]),
        "kl_10": kl_10,
        "acc_tsne_10": acc_tsne_10,
        "acc_isomap_10": acc_iso_10,
        "error_isomap_10": err_iso_10,
        "N_bin": int(len(X_bin)),
        "acc_tsne_bin": acc_tsne_bin,
        "acc_isomap_bin": acc_iso_bin,
    }


def guardar_capturas_terminal(lineas_consola):
    """Guarda como imagen la salida de consola registrada durante la ejecución."""
    fuente_mono = None
    for candidato in ("consola.ttf", "cour.ttf", "lucon.ttf"):
        try:
            fuente_mono = ImageFont.truetype(candidato, 15)
            break
        except OSError:
            pass
    if fuente_mono is None:
        fuente_mono = ImageFont.load_default()

    mitad = (len(lineas_consola) + 1) // 2
    bloques = [lineas_consola[:mitad], lineas_consola[mitad:]]
    for idx, bloque in enumerate(bloques, 1):
        ancho = 1500
        alto_linea = 22
        alto = max(360, 44 + len(bloque) * alto_linea)
        img = Image.new("RGB", (ancho, alto), (24, 24, 24))
        draw = ImageDraw.Draw(img)
        draw.rectangle([0, 0, ancho, 28], fill=(37, 37, 38))
        draw.text((14, 6), f"Salida de consola - reduccion_mnist_2d.py - Parte {idx}/{len(bloques)}",
                  fill=(200, 200, 200), font=fuente_mono)
        y_pos = 36
        for lin in bloque:
            color = (86, 156, 214) if lin.startswith("PS ") or lin.startswith("===") else (212, 212, 212)
            if lin.startswith("[DM") or lin.startswith("[Referencia"):
                color = (78, 201, 176)
            draw.text((16, y_pos), lin, fill=color, font=fuente_mono)
            y_pos += alto_linea
        img.save(CAPTURAS / f"vscode_ejecucion_{idx}.png")


def main():
    lineas_consola = [
        "PS C:\\Users\\henry\\.gemini\\antigravity\\scratch\\DocumentosBi> python 2parcial/Tarea1_Reduccion_MNIST_2D/reduccion_mnist_2d.py",
        "=" * 86,
        "TAREA 1: REDUCCIÓN DE DIMENSIONALIDAD A R^2 ([v1, v2]) CON t-SNE E ISOMAP, Y REFERENCIA MNIST",
        "=" * 86,
    ]
    for l in lineas_consola[1:]:
        print(l)

    for viejo in ["mnist_10clases_tsne_vs_pca.png"]:
        if (SALIDA / viejo).exists():
            (SALIDA / viejo).unlink()

    resumen_json = json.load(open(DIR_2P / "resumen_datasets_2parcial.json", encoding="utf-8"))
    info_mnist = ejecutar_mnist_referencia(lineas_consola)

    filas_resumen = []
    fig_mosaico_bin, axes_bin = plt.subplots(2, 2, figsize=(13.5, 11.0))
    axes_bin = axes_bin.ravel()
    fig_mosaico_multi, axes_multi = plt.subplots(2, 2, figsize=(13.5, 11.0))
    axes_multi = axes_multi.ravel()

    for k, cfg in enumerate(DATASETS_CONFIG):
        t0 = time.time()
        df = pd.read_csv(DIR_2P / cfg["archivo"])
        features = resumen_json[cfg["archivo"]]["features"]

        # Todas las características y todas las observaciones reales del dataset
        X = estandarizar(df[features].to_numpy(dtype=float))
        y_bin = df["Clase"].to_numpy(dtype=int)
        nombres_bin = df.groupby("Clase")["Nombre_Clase"].first().to_dict()

        Z_tsne, kl_val = reducir_tsne(X)
        Z_iso, err_iso, n_comp = reducir_isomap(X)
        acc_tsne, dist_tsne = evaluar_proyeccion_2d(Z_tsne, y_bin)
        acc_iso, dist_iso = evaluar_proyeccion_2d(Z_iso, y_bin)
        acc_may = float(np.bincount(y_bin).max() / len(y_bin))

        # CSV con las coordenadas [v1, v2] de cada observación
        pd.DataFrame({
            "v1_tsne": Z_tsne[:, 0].round(4),
            "v2_tsne": Z_tsne[:, 1].round(4),
            "v1_isomap": Z_iso[:, 0].round(4),
            "v2_isomap": Z_iso[:, 1].round(4),
            "Clase": y_bin,
            "Nombre_Clase": df["Nombre_Clase"].values,
            "Clase_Multiclase": df["Clase_Multiclase"].values,
            "Nombre_Multiclase": df["Nombre_Multiclase"].values,
        }).to_csv(SALIDA / f"proyeccion_2d_{cfg['id']}.csv", index=False, encoding="utf-8-sig")

        # 1. Figura individual: t-SNE e Isomap lado a lado (clases binarias, 2 colores)
        N = len(X)
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14.0, 5.8))
        dispersion(ax1, Z_tsne, y_bin, nombres_bin, PALETA_BIN,
                   f"t-SNE, {N:,} de {N:,} observaciones reales (Acc 2D = {100*acc_tsne:.1f} %)")
        dispersion(ax2, Z_iso, y_bin, nombres_bin, PALETA_BIN,
                   f"Isomap, las {N:,} observaciones reales (Acc 2D = {100*acc_iso:.1f} %)")
        fig.suptitle(f"{cfg['nombre']}: dispersión v₁ contra v₂ con las {len(features)} características, "
                     f"un color por clase y un punto por observación", fontsize=12.5)
        fig.tight_layout()
        fig.savefig(SALIDA / f"reduccion_binaria_{cfg['id']}.png", dpi=200)
        plt.close(fig)

        # Panel en el mosaico binario 2x2 (t-SNE)
        dispersion(axes_bin[k], Z_tsne, y_bin, nombres_bin, PALETA_BIN,
                   f"{cfg['nombre']}\nn = {len(features)} -> 2D, {N:,} observaciones (Acc 2D = {100*acc_tsne:.1f} %)")

        # 2. Figura individual multiclase (3 a 4 colores reales por Data Mart, t-SNE vs Isomap)
        y_multi = df["Clase_Multiclase"].to_numpy(dtype=int)
        nombres_multi = df.groupby("Clase_Multiclase")["Nombre_Multiclase"].first().to_dict()
        acc_multi_tsne, _ = evaluar_proyeccion_2d(Z_tsne, y_multi)
        acc_multi_iso, _ = evaluar_proyeccion_2d(Z_iso, y_multi)
        acc_may_multi = float(np.bincount(y_multi).max() / len(y_multi))

        fig_m, (axm1, axm2) = plt.subplots(1, 2, figsize=(14.0, 5.8))
        dispersion(axm1, Z_tsne, y_multi, nombres_multi, PALETA,
                   f"t-SNE, {N:,} de {N:,} observaciones reales (Acc 2D = {100*acc_multi_tsne:.1f} %)")
        dispersion(axm2, Z_iso, y_multi, nombres_multi, PALETA,
                   f"Isomap, las {N:,} observaciones reales (Acc 2D = {100*acc_multi_iso:.1f} %)")
        fig_m.suptitle(f"{cfg['titulo_multi']}: dispersión v₁ contra v₂ con las {len(features)} características, "
                       f"un color por clase y un punto por observación", fontsize=12.0)
        fig_m.tight_layout()
        fig_m.savefig(SALIDA / f"reduccion_multiclase_{cfg['id']}.png", dpi=200)
        plt.close(fig_m)

        # Panel en el mosaico multiclase 2x2 (los 4 Data Marts con varios colores en t-SNE)
        dispersion(axes_multi[k], Z_tsne, y_multi, nombres_multi, PALETA,
                   f"{cfg['titulo_multi']}\nn = {len(features)} -> 2D, {N:,} observaciones (Acc 2D = {100*acc_multi_tsne:.1f} %)")

        linea_dm = (
            f"[{cfg['id']}] {cfg['tabla_hechos']} | N = {N:,} | n = {len(features)} -> 2D | "
            f"Binario t-SNE/Iso: {100*acc_tsne:.1f}%/{100*acc_iso:.1f}% | "
            f"Multiclase ({len(nombres_multi)} clases) t-SNE/Iso: {100*acc_multi_tsne:.1f}%/{100*acc_multi_iso:.1f}% | "
            f"{time.time() - t0:.0f} s"
        )
        print(linea_dm)
        lineas_consola.append(linea_dm)

        filas_resumen.append({
            "Data_Mart": cfg["id"],
            "Tabla_Hechos": cfg["tabla_hechos"],
            "Descripcion": cfg["nombre"],
            "N_Observaciones": int(N),
            "n_Caracteristicas": int(len(features)),
            "Num_Clases_Multi": int(len(nombres_multi)),
            "Conteo_Clases": " / ".join(f"{int((y_bin == c).sum())}" for c in sorted(np.unique(y_bin))),
            "Conteo_Multiclase": " / ".join(f"{int((y_multi == c).sum())}" for c in sorted(np.unique(y_multi))),
            "KL_tSNE": round(kl_val, 4),
            "Acc_2D_tSNE": round(acc_tsne, 4),
            "Dist_Centroides_tSNE": round(dist_tsne, 4),
            "Acc_2D_Isomap": round(acc_iso, 4),
            "Dist_Centroides_Isomap": round(dist_iso, 4),
            "Error_Reconstruccion_Isomap": round(err_iso, 4),
            "Componentes_Grafo_Isomap": n_comp,
            "Acc_Clase_Mayoritaria": round(acc_may, 4),
            "Acc_Multiclase_tSNE": round(acc_multi_tsne, 4),
            "Acc_Multiclase_Isomap": round(acc_multi_iso, 4),
            "Acc_Mayoritaria_Multiclase": round(acc_may_multi, 4),
        })

    fig_mosaico_bin.suptitle(
        "Reducción a plano euclidiano 2D (x_i^(1) = [v₁, v₂]) con t-SNE en los 4 Data Marts "
        "(todas las observaciones, clases binarias)",
        fontsize=13,
    )
    fig_mosaico_bin.tight_layout()
    fig_mosaico_bin.savefig(SALIDA / "mosaico_4_datamarts_binario_tsne.png", dpi=200)
    plt.close(fig_mosaico_bin)

    fig_mosaico_multi.suptitle(
        "Reducción a plano euclidiano 2D (x_i^(1) = [v₁, v₂]) con t-SNE en los 4 Data Marts "
        "(todas las observaciones, clases múltiples reales de 3 y 4 colores)",
        fontsize=13,
    )
    fig_mosaico_multi.tight_layout()
    fig_mosaico_multi.savefig(SALIDA / "mosaico_multiclase_reales_tsne.png", dpi=200)
    plt.close(fig_mosaico_multi)

    pd.DataFrame(filas_resumen).to_csv(SALIDA / "tabla_resultados_tarea1.csv", index=False, encoding="utf-8-sig")
    with open(SALIDA / "resumen_mnist_tarea1.json", "w", encoding="utf-8") as f:
        json.dump(info_mnist, f, indent=2, ensure_ascii=False)

    pie_msg = f"Tablas y figuras de la Tarea 1 guardadas en: {SALIDA}"
    print("=" * 86)
    print(pie_msg)
    lineas_consola.extend(["=" * 86, pie_msg])
    guardar_capturas_terminal(lineas_consola)


if __name__ == "__main__":
    main()
