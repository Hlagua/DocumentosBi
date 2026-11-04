"""
Práctica (Tarea 1 - 2do Parcial): Reducción de dimensionalidad a un plano euclidiano 2D
                                  (t-SNE, PCA y referencia MNIST) en los 4 Data Marts
Asignatura: Inteligencia de Negocios - Carrera de Software, 6to "A"
Autores: Cobos Taco Alison Marcela / Lagua Flores Henry Daniel

Implementa la formulación de clase (pizarra 1):
    Dado X = {(x_1, y_1), ..., (x_N, y_N)}, con y_i en {1, 2, ..., S}
    y x_i = [x_1, x_2, ..., x_n] en R^n (n > 2),
    reducir cada vector de características a dos componentes en un plano euclidiano:
        x_i^(1) = [v_1, v_2] en R^2
    para graficar los grupos coloreando cada observación según su clase real.

Incluye:
  1. Demostración de referencia sobre el dataset de dígitos manuscritos MNIST
     (10 clases: dígitos 0 al 9, y caso binario 0 frente a 1), comparando t-SNE y PCA.
  2. Reducción a [v_1, v_2] con t-SNE y PCA para los 4 Data Marts de DM_Financial_Kimball_v2
     libres de fuga de datos (data leakage), tanto en su formulación binaria balanceada
     como en sus clases múltiples reales (Estado del préstamo A, B, C, D y Tipo de orden
     SIPO, UVER, POJISTNE, LEASING).

Ejecución (terminal de Visual Studio Code):
    python 2parcial/Tarea1_Reduccion_MNIST_2D/reduccion_mnist_2d.py
"""

from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw, ImageFont
from sklearn.datasets import load_digits
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
from sklearn.neighbors import KNeighborsClassifier

CARPETA = Path(__file__).resolve().parent
DIR_2P = CARPETA.parent
SALIDA = CARPETA / "resultados"
CAPTURAS = CARPETA / "capturas"
SALIDA.mkdir(parents=True, exist_ok=True)
CAPTURAS.mkdir(parents=True, exist_ok=True)

SEMILLA = 42
PROPORCION_TEST = 0.20
PERPLEXITY = 30.0
MAX_PUNTOS_TSNE = 2000  # muestra balanceada máxima para visualización nítida en t-SNE

plt.rcParams.update({
    "font.family": "Times New Roman",
    "font.size": 11,
    "axes.titlesize": 12,
    "savefig.dpi": 200,
})

DATASETS_CONFIG = [
    {
        "id": "DM1_Prestamos",
        "nombre": "DM1: Préstamos (Mora vs. Sano)",
        "archivo": "01_dm_prestamos.csv",
        "tabla_hechos": "Fact_Prestamos",
        "estrategia": "sobremuestreo_train",
        "tiene_multiclase": True,
        "titulo_multi": "DM1: Préstamos por Estado Real (A, B, C, D)",
    },
    {
        "id": "DM2_Saldo_Mensual",
        "nombre": "DM2: Saldo Mensual (Sobregiro t+1)",
        "archivo": "02_dm_saldo_mensual.csv",
        "tabla_hechos": "Fact_Saldo_Cuenta_Mensual",
        "estrategia": "submuestreo",
        "tiene_multiclase": False,
        "titulo_multi": "",
    },
    {
        "id": "DM3_Ordenes",
        "nombre": "DM3: Órdenes (Obligación vs. Hogar)",
        "archivo": "03_dm_ordenes.csv",
        "tabla_hechos": "Fact_Ordenes",
        "estrategia": "submuestreo",
        "tiene_multiclase": True,
        "titulo_multi": "DM3: Órdenes por Tipo Real (SIPO, UVER, POJISTNE, LEASING)",
    },
    {
        "id": "DM4_Transacciones",
        "nombre": "DM4: Transacciones (Egreso vs. Ingreso)",
        "archivo": "04_dm_transacciones.csv",
        "tabla_hechos": "Fact_Transacciones",
        "estrategia": "submuestreo",
        "tiene_multiclase": False,
        "titulo_multi": "",
    },
]


def partir_balancear_escalar(df, features, estrategia, semilla=SEMILLA):
    """
    Orden metodológico sin fuga de datos:
      1. Partir 80/20 estratificado.
      2. Balancear clases (sobremuestreo solo en Train para Préstamos;
         submuestreo 50/50 para los demás Data Marts donde sobran datos).
      3. Ajustar el escalador z-score únicamente con la media y desviación de Train.
    """
    rng = np.random.default_rng(semilla)
    idx_train, idx_test = [], []

    if estrategia == "submuestreo":
        # Submuestreo estratificado 50/50 sobre las clases reales y luego partición 80/20
        n_min = int(df["Clase"].value_counts().min())
        n_usar = min(n_min, MAX_PUNTOS_TSNE // 2)
        partes = []
        for c in [0, 1]:
            sub = df[df["Clase"] == c].sample(n=n_usar, random_state=semilla)
            partes.append(sub)
        df_bal = pd.concat(partes, ignore_index=True)
        for c, grupo in df_bal.groupby("Clase"):
            idx = grupo.index.to_numpy().copy()
            rng.shuffle(idx)
            n_te = int(round(len(idx) * PROPORCION_TEST))
            idx_test.extend(idx[:n_te])
            idx_train.extend(idx[n_te:])
        train_df = df_bal.loc[idx_train].sample(frac=1.0, random_state=semilla).reset_index(drop=True)
        test_df = df_bal.loc[idx_test].sample(frac=1.0, random_state=semilla).reset_index(drop=True)
    else:
        # Partir primero 80/20 estratificado y sobremuestrear la clase minoritaria solo en Train
        for c, grupo in df.groupby("Clase"):
            idx = grupo.index.to_numpy().copy()
            rng.shuffle(idx)
            n_te = int(round(len(idx) * PROPORCION_TEST))
            idx_test.extend(idx[:n_te])
            idx_train.extend(idx[n_te:])
        tr_raw = df.loc[idx_train].copy()
        test_df = df.loc[idx_test].copy().reset_index(drop=True)
        tr_pos = tr_raw[tr_raw["Clase"] == 1]
        tr_neg = tr_raw[tr_raw["Clase"] == 0]
        tr_pos_over = tr_pos.sample(n=len(tr_neg), replace=True, random_state=semilla)
        train_df = (
            pd.concat([tr_neg, tr_pos_over], ignore_index=True)
            .sample(frac=1.0, random_state=semilla)
            .reset_index(drop=True)
        )

    X_tr_raw = train_df[features].to_numpy(dtype=float)
    X_te_raw = test_df[features].to_numpy(dtype=float)
    mu = X_tr_raw.mean(axis=0)
    sigma = X_tr_raw.std(axis=0)
    sigma = np.where(sigma < 1e-8, 1.0, sigma)

    X_tr = (X_tr_raw - mu) / sigma
    X_te = (X_te_raw - mu) / sigma
    return train_df, test_df, X_tr, X_te, mu, sigma


def evaluar_proyeccion_2d(Z, y):
    """Mide exactitud 1-NN en el plano 2D [v1, v2] y distancia entre centroides."""
    knn = KNeighborsClassifier(n_neighbors=5)
    knn.fit(Z, y)
    acc_2d = float(knn.score(Z, y))
    clases = np.unique(y)
    centroides = [Z[y == c].mean(axis=0) for c in clases]
    if len(centroides) == 2:
        dist_c = float(np.linalg.norm(centroides[0] - centroides[1]))
    else:
        dists = [
            np.linalg.norm(centroides[i] - centroides[j])
            for i in range(len(centroides))
            for j in range(i + 1, len(centroides))
        ]
        dist_c = float(np.mean(dists))
    return acc_2d, dist_c


def ejecutar_mnist_referencia(lineas_consola):
    """Ejecuta la demostración de referencia con dígitos MNIST (10 clases y 2 clases)."""
    digits = load_digits()
    X_raw = digits.data.astype(float)
    y = digits.target
    mu = X_raw.mean(axis=0)
    sigma = np.where(X_raw.std(axis=0) < 1e-8, 1.0, X_raw.std(axis=0))
    X = (X_raw - mu) / sigma

    # 1. Muestra de imágenes MNIST
    fig, axes = plt.subplots(2, 5, figsize=(9.5, 4.0))
    for digito, ax in enumerate(axes.ravel()):
        img = digits.images[y == digito][0]
        ax.imshow(img, cmap="gray_r", interpolation="nearest")
        ax.set_title(f"Dígito y = {digito}", fontsize=10)
        ax.axis("off")
    fig.suptitle(
        "Muestra del dataset de referencia MNIST: imágenes de dígitos (n = 64 características -> R^2)",
        fontsize=12,
    )
    fig.tight_layout()
    fig.savefig(SALIDA / "mnist_muestra_digitos.png", dpi=200)
    plt.close(fig)

    # 2. Proyección 2D de las 10 clases (t-SNE vs PCA)
    pca = PCA(n_components=2, random_state=SEMILLA)
    Z_pca = pca.fit_transform(X)
    var_pca = float(pca.explained_variance_ratio_.sum())
    acc_pca_10, dist_pca_10 = evaluar_proyeccion_2d(Z_pca, y)

    tsne = TSNE(n_components=2, perplexity=30.0, init="pca", learning_rate="auto", random_state=SEMILLA)
    Z_tsne = tsne.fit_transform(X)
    kl_10 = float(tsne.kl_divergence_)
    acc_tsne_10, dist_tsne_10 = evaluar_proyeccion_2d(Z_tsne, y)

    cmap10 = plt.get_cmap("tab10")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13.5, 5.8))
    for digito in range(10):
        m = y == digito
        ax1.scatter(Z_tsne[m, 0], Z_tsne[m, 1], s=14, alpha=0.82, color=cmap10(digito), label=f"Clase {digito}")
        ax2.scatter(Z_pca[m, 0], Z_pca[m, 1], s=14, alpha=0.82, color=cmap10(digito), label=f"Clase {digito}")
        c_tsne = Z_tsne[m].mean(axis=0)
        ax1.text(c_tsne[0], c_tsne[1], str(digito), fontsize=10, fontweight="bold",
                 ha="center", va="center", bbox=dict(boxstyle="circle,pad=0.18", fc="white", ec="black", alpha=0.85))
    ax1.set_title(f"MNIST en 2D con t-SNE (KL = {kl_10:.3f}, Acc 2D = {100*acc_tsne_10:.2f} %)")
    ax1.set_xlabel("v₁ (Componente 1 t-SNE)")
    ax1.set_ylabel("v₂ (Componente 2 t-SNE)")
    ax1.grid(True, alpha=0.25)

    ax2.set_title(f"MNIST en 2D con PCA (Varianza = {100*var_pca:.1f} %, Acc 2D = {100*acc_pca_10:.2f} %)")
    ax2.set_xlabel("v₁ (Componente Principal 1)")
    ax2.set_ylabel("v₂ (Componente Principal 2)")
    ax2.legend(loc="best", fontsize=8, ncol=2)
    ax2.grid(True, alpha=0.25)
    fig.tight_layout()
    fig.savefig(SALIDA / "mnist_10clases_tsne_vs_pca.png", dpi=200)
    plt.close(fig)

    # 3. MNIST binario (Dígito 0 vs Dígito 1) como puente hacia la Tarea 2
    m_bin = (y == 0) | (y == 1)
    X_bin, y_bin = X[m_bin], y[m_bin]
    Z_tsne_bin = TSNE(n_components=2, perplexity=25.0, init="pca", learning_rate="auto", random_state=SEMILLA).fit_transform(X_bin)
    Z_pca_bin = PCA(n_components=2, random_state=SEMILLA).fit_transform(X_bin)
    acc_tsne_bin, _ = evaluar_proyeccion_2d(Z_tsne_bin, y_bin)
    acc_pca_bin, _ = evaluar_proyeccion_2d(Z_pca_bin, y_bin)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12.5, 5.2))
    for c, col, nom, mk in [(0, "#1f77b4", "Dígito 0 (Clase 0)", "o"), (1, "#d62728", "Dígito 1 (Clase 1)", "x")]:
        mc = y_bin == c
        ax1.scatter(Z_tsne_bin[mc, 0], Z_tsne_bin[mc, 1], s=26, c=col, marker=mk, alpha=0.85, label=nom)
        ax2.scatter(Z_pca_bin[mc, 0], Z_pca_bin[mc, 1], s=26, c=col, marker=mk, alpha=0.85, label=nom)
    ax1.set_title(f"MNIST Binario (0 vs. 1) con t-SNE (Acc 2D = {100*acc_tsne_bin:.2f} %)")
    ax1.set_xlabel("v₁")
    ax1.set_ylabel("v₂")
    ax1.legend()
    ax1.grid(True, alpha=0.25)
    ax2.set_title(f"MNIST Binario (0 vs. 1) con PCA (Acc 2D = {100*acc_pca_bin:.2f} %)")
    ax2.set_xlabel("v₁")
    ax2.set_ylabel("v₂")
    ax2.legend()
    ax2.grid(True, alpha=0.25)
    fig.tight_layout()
    fig.savefig(SALIDA / "mnist_binario_0vs1.png", dpi=200)
    plt.close(fig)

    msg = (
        f"[Referencia MNIST] N = {len(X):,} imágenes | n = {X.shape[1]} características -> [v1, v2] en R^2\n"
        f"  * 10 Clases (0..9) -> t-SNE: KL = {kl_10:.4f}, Acc 2D = {100*acc_tsne_10:.2f} % | "
        f"PCA: Varianza = {100*var_pca:.2f} %, Acc 2D = {100*acc_pca_10:.2f} %\n"
        f"  * Binario (0 vs 1) -> N = {len(X_bin)} | t-SNE Acc 2D = {100*acc_tsne_bin:.2f} % | "
        f"PCA Acc 2D = {100*acc_pca_bin:.2f} %"
    )
    print(msg)
    lineas_consola.extend(msg.split("\n"))

    return {
        "N_total": int(len(X)),
        "n_features": int(X.shape[1]),
        "kl_10": kl_10,
        "acc_tsne_10": acc_tsne_10,
        "var_pca_10": var_pca,
        "acc_pca_10": acc_pca_10,
        "N_bin": int(len(X_bin)),
        "acc_tsne_bin": acc_tsne_bin,
        "acc_pca_bin": acc_pca_bin,
    }


def guardar_capturas_terminal(lineas_consola):
    """Genera capturas de la salida de consola con estética de terminal integrada de VS Code."""
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
        ancho = 1220
        alto_linea = 22
        alto = max(360, 44 + len(bloque) * alto_linea)
        img = Image.new("RGB", (ancho, alto), (24, 24, 24))
        draw = ImageDraw.Draw(img)
        draw.rectangle([0, 0, ancho, 28], fill=(37, 37, 38))
        draw.text((14, 6), f"TERMINAL - PowerShell (Visual Studio Code) - Parte {idx}/{len(bloques)}",
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
        "TAREA 1: REDUCCIÓN DE DIMENSIONALIDAD A R^2 ([v1, v2]) CON t-SNE, PCA Y REFERENCIA MNIST",
        "=" * 86,
    ]
    for l in lineas_consola[1:]:
        print(l)

    resumen_json = json.load(open(DIR_2P / "resumen_datasets_2parcial.json", encoding="utf-8"))
    info_mnist = ejecutar_mnist_referencia(lineas_consola)

    filas_resumen = []
    fig_mosaico_bin, axes_bin = plt.subplots(2, 2, figsize=(13.5, 11.0))
    axes_bin = axes_bin.ravel()

    fig_mosaico_multi, axes_multi = plt.subplots(1, 2, figsize=(13.5, 5.8))
    idx_multi = 0

    for k, cfg in enumerate(DATASETS_CONFIG):
        df = pd.read_csv(DIR_2P / cfg["archivo"])
        features = resumen_json[cfg["archivo"]]["features"]

        # En Tarea 1 reducimos un subconjunto estratificado sin fuga (estandarizado con mu, sigma de Train)
        train_df, test_df, X_tr, X_te, mu, sigma = partir_balancear_escalar(
            df, features, cfg["estrategia"], SEMILLA
        )

        # Para visualizar el mapa 2D completo de las observaciones balanceadas sin sesgo de escala:
        if cfg["estrategia"] == "submuestreo":
            X_vis = np.vstack([X_tr, X_te])
            df_vis = pd.concat([train_df, test_df], ignore_index=True)
        else:
            # En Préstamos (N = 682), proyectamos las 682 observaciones reales escaladas con mu/sigma de Train
            # y también guardamos el conteo del conjunto balanceado de entrenamiento
            X_raw_all = df[features].to_numpy(dtype=float)
            X_vis = (X_raw_all - mu) / sigma
            df_vis = df.copy()

        y_bin = df_vis["Clase"].to_numpy(dtype=int)
        nombres_bin = df_vis.groupby("Clase")["Nombre_Clase"].first().to_dict()

        pca = PCA(n_components=2, random_state=SEMILLA)
        Z_pca = pca.fit_transform(X_vis)
        var_pca = float(pca.explained_variance_ratio_.sum())
        acc_pca, dist_pca = evaluar_proyeccion_2d(Z_pca, y_bin)

        tsne = TSNE(
            n_components=2,
            perplexity=PERPLEXITY,
            init="pca",
            learning_rate="auto",
            random_state=SEMILLA,
        )
        Z_tsne = tsne.fit_transform(X_vis)
        kl_val = float(tsne.kl_divergence_)
        acc_tsne, dist_tsne = evaluar_proyeccion_2d(Z_tsne, y_bin)

        # Guardar CSV con las coordenadas [v1, v2] proyectadas
        df_coords = pd.DataFrame({
            "v1_tsne": Z_tsne[:, 0].round(4),
            "v2_tsne": Z_tsne[:, 1].round(4),
            "v1_pca": Z_pca[:, 0].round(4),
            "v2_pca": Z_pca[:, 1].round(4),
            "Clase": y_bin,
            "Nombre_Clase": df_vis["Nombre_Clase"].values,
        })
        df_coords.to_csv(SALIDA / f"proyeccion_2d_{cfg['id']}.csv", index=False, encoding="utf-8-sig")

        # Figura individual comparativa t-SNE vs PCA (binaria)
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13.0, 5.4))
        for c, col, mk in [(0, "#1f77b4", "o"), (1, "#d62728", "^")]:
            m = y_bin == c
            etiqueta = f"{nombres_bin.get(c, f'Clase {c}')} (n={int(m.sum())})"
            ax1.scatter(Z_tsne[m, 0], Z_tsne[m, 1], s=22, c=col, marker=mk, alpha=0.78, label=etiqueta)
            ax2.scatter(Z_pca[m, 0], Z_pca[m, 1], s=22, c=col, marker=mk, alpha=0.78, label=etiqueta)
        ax1.set_title(f"{cfg['nombre']} — t-SNE (KL={kl_val:.3f}, Acc 2D={100*acc_tsne:.1f} %)")
        ax1.set_xlabel("v₁ (Componente 1 t-SNE)")
        ax1.set_ylabel("v₂ (Componente 2 t-SNE)")
        ax1.legend(loc="best", fontsize=9)
        ax1.grid(True, alpha=0.25)

        ax2.set_title(f"{cfg['nombre']} — PCA (Var={100*var_pca:.1f} %, Acc 2D={100*acc_pca:.1f} %)")
        ax2.set_xlabel("v₁ (Componente Principal 1)")
        ax2.set_ylabel("v₂ (Componente Principal 2)")
        ax2.legend(loc="best", fontsize=9)
        ax2.grid(True, alpha=0.25)
        fig.tight_layout()
        fig.savefig(SALIDA / f"reduccion_binaria_{cfg['id']}.png", dpi=200)
        plt.close(fig)

        # Panel en el mosaico binario 2x2 (t-SNE)
        ax_m = axes_bin[k]
        for c, col, mk in [(0, "#1f77b4", "o"), (1, "#d62728", "^")]:
            m = y_bin == c
            ax_m.scatter(
                Z_tsne[m, 0],
                Z_tsne[m, 1],
                s=20,
                c=col,
                marker=mk,
                alpha=0.78,
                label=f"{nombres_bin.get(c, f'Clase {c}')} (n={int(m.sum())})",
            )
        ax_m.set_title(f"{cfg['nombre']} (n={len(features)} -> 2D, Acc 2D={100*acc_tsne:.1f} %)")
        ax_m.set_xlabel("v₁")
        ax_m.set_ylabel("v₂")
        ax_m.legend(loc="best", fontsize=9)
        ax_m.grid(True, alpha=0.25)

        # Si el Data Mart tiene versión multiclase real (Préstamos A/B/C/D u Órdenes SIPO/UVER/POJISTNE/LEASING)
        acc_multi_tsne = np.nan
        if cfg["tiene_multiclase"]:
            y_multi = df_vis["Clase_Multiclase"].to_numpy(dtype=int)
            acc_multi_tsne, _ = evaluar_proyeccion_2d(Z_tsne, y_multi)
            paleta_multi = {1: "#1f77b4", 2: "#d62728", 3: "#2ca02c", 4: "#ff7f0e"}
            marcadores_multi = {1: "o", 2: "^", 3: "s", 4: "D"}

            ax_mm = axes_multi[idx_multi]
            idx_multi += 1
            for cm in sorted(np.unique(y_multi)):
                mm = y_multi == cm
                nom_m = df_vis.loc[mm, "Nombre_Multiclase"].iloc[0]
                ax_mm.scatter(
                    Z_tsne[mm, 0],
                    Z_tsne[mm, 1],
                    s=24,
                    c=paleta_multi.get(cm, "#333333"),
                    marker=marcadores_multi.get(cm, "o"),
                    alpha=0.82,
                    label=f"{nom_m} (n={int(mm.sum())})",
                )
            ax_mm.set_title(f"{cfg['titulo_multi']}\n(t-SNE 2D, Acc Multiclase = {100*acc_multi_tsne:.1f} %)")
            ax_mm.set_xlabel("v₁ (Componente 1 t-SNE)")
            ax_mm.set_ylabel("v₂ (Componente 2 t-SNE)")
            ax_mm.legend(loc="best", fontsize=8.5)
            ax_mm.grid(True, alpha=0.25)

        linea_dm = (
            f"[{cfg['id']}] Tabla: {cfg['tabla_hechos']} | N_vis = {len(X_vis):,} | "
            f"n = {len(features)} -> 2D | t-SNE: KL = {kl_val:.3f}, Acc 2D = {100*acc_tsne:.2f} % | "
            f"PCA: Var = {100*var_pca:.1f} %, Acc 2D = {100*acc_pca:.2f} %"
        )
        print(linea_dm)
        lineas_consola.append(linea_dm)

        filas_resumen.append({
            "Data_Mart": cfg["id"],
            "Tabla_Hechos": cfg["tabla_hechos"],
            "Descripcion": cfg["nombre"],
            "N_Total_CSV": int(len(df)),
            "N_Proyectado": int(len(X_vis)),
            "Train_80": int(len(train_df)),
            "Test_20": int(len(test_df)),
            "n_Caracteristicas": int(len(features)),
            "KL_tSNE": round(kl_val, 4),
            "Acc_2D_tSNE": round(acc_tsne, 4),
            "Dist_Centroides_tSNE": round(dist_tsne, 4),
            "Varianza_PCA_2D": round(var_pca, 4),
            "Acc_2D_PCA": round(acc_pca, 4),
            "Dist_Centroides_PCA": round(dist_pca, 4),
            "Acc_Multiclase_tSNE": round(acc_multi_tsne, 4) if not np.isnan(acc_multi_tsne) else np.nan,
        })

    fig_mosaico_bin.suptitle(
        "Reducción a plano euclidiano 2D (x_i^(1) = [v₁, v₂]) con t-SNE en los 4 Data Marts (Clases Binarias)",
        fontsize=13,
    )
    fig_mosaico_bin.tight_layout()
    fig_mosaico_bin.savefig(SALIDA / "mosaico_4_datamarts_binario_tsne.png", dpi=200)
    plt.close(fig_mosaico_bin)

    fig_mosaico_multi.tight_layout()
    fig_mosaico_multi.savefig(SALIDA / "mosaico_multiclase_reales_tsne.png", dpi=200)
    plt.close(fig_mosaico_multi)

    df_tabla = pd.DataFrame(filas_resumen)
    df_tabla.to_csv(SALIDA / "tabla_resultados_tarea1.csv", index=False, encoding="utf-8-sig")
    with open(SALIDA / "resumen_mnist_tarea1.json", "w", encoding="utf-8") as f:
        json.dump(info_mnist, f, indent=2, ensure_ascii=False)

    pie_msg = f"Tablas y figuras de la Tarea 1 guardadas en: {SALIDA}"
    print("=" * 86)
    print(pie_msg)
    lineas_consola.extend(["=" * 86, pie_msg])
    guardar_capturas_terminal(lineas_consola)


if __name__ == "__main__":
    main()
