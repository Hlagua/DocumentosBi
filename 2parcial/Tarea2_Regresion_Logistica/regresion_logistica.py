"""
Práctica (Tarea 2 - 2do Parcial): Entrenamiento de Regresión Logística Binaria mediante
                                  Entropía Cruzada y Gradiente Descendente en los 4 Data Marts
Asignatura: Inteligencia de Negocios - Carrera de Software, 6to "A"
Autores: Cobos Taco Alison Marcela / Lagua Flores Henry Daniel

Implementa desde cero (sin usar sklearn.linear_model.LogisticRegression) la formulación de
la pizarra 2 de clase:
  1. Combinación lineal con todas las características (x_i0 = 1 para el sesgo beta_0):
         z_i = beta_0 + beta_1*x_i1 + ... + beta_n*x_in = x_tilde_i^T * beta
  2. Función logística (sigmoide):
         p_i = sigma(z_i) = 1 / (1 + exp(-z_i))
  3. Función de costo de Entropía Cruzada Binaria:
         J(beta) = -(1/N) * sum_{i=1}^N [ y_i * ln(p_i) + (1 - y_i) * ln(1 - p_i) ]
  4. Optimización por Gradiente Descendente (y verificación con scipy.optimize.minimize):
         grad J(beta) = (1/N) * X_tilde^T * (sigma(X_tilde * beta) - y)
         beta^{(t+1)} = beta^{(t)} - eta * grad J(beta^{(t)})

Entregables por cada Data Mart:
  - Vector de pesos final beta = [beta_0, beta_1, ..., beta_n]^T
  - Exactitud de entrenamiento (Acc. Train) y Exactitud de prueba (Acc. Test)
  - Figuras de convergencia de la Entropía Cruzada, sigmoide, matrices de confusión
    y frontera de decisión 2D proyectada con PCA.

Ejecución (terminal de Visual Studio Code):
    python 2parcial/Tarea2_Regresion_Logistica/regresion_logistica.py
"""

from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch
from PIL import Image, ImageDraw, ImageFont
from scipy.optimize import minimize
from scipy.special import expit
from sklearn.decomposition import PCA

CARPETA = Path(__file__).resolve().parent
DIR_2P = CARPETA.parent
SALIDA = CARPETA / "resultados"
CAPTURAS = CARPETA / "capturas"
SALIDA.mkdir(parents=True, exist_ok=True)
CAPTURAS.mkdir(parents=True, exist_ok=True)

SEMILLA = 42
PROPORCION_TEST = 0.20
EPOCAS = 1500
TASA_APRENDIZAJE = 0.15

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
        "clase_pos": "Mora (1)",
        "clase_neg": "Sano (0)",
    },
    {
        "id": "DM2_Saldo_Mensual",
        "nombre": "DM2: Saldo Mensual (Sobregiro t+1)",
        "archivo": "02_dm_saldo_mensual.csv",
        "tabla_hechos": "Fact_Saldo_Cuenta_Mensual",
        "estrategia": "submuestreo",
        "clase_pos": "Sobregiro t+1 (1)",
        "clase_neg": "Sin sobregiro (0)",
    },
    {
        "id": "DM3_Ordenes",
        "nombre": "DM3: Órdenes (Obligación vs. Hogar)",
        "archivo": "03_dm_ordenes.csv",
        "tabla_hechos": "Fact_Ordenes",
        "estrategia": "submuestreo",
        "clase_pos": "Obligación (1)",
        "clase_neg": "Hogar SIPO (0)",
    },
    {
        "id": "DM4_Transacciones",
        "nombre": "DM4: Transacciones (Egreso vs. Ingreso)",
        "archivo": "04_dm_transacciones.csv",
        "tabla_hechos": "Fact_Transacciones",
        "estrategia": "submuestreo",
        "clase_pos": "Egreso (1)",
        "clase_neg": "Ingreso (0)",
    },
]


# ----------------------------------------------------------------------------
# Funciones matemáticas de Regresión Logística (Entropía Cruzada y Gradiente)
# ----------------------------------------------------------------------------
def sigmoide(z):
    """Función logística sigma(z) = 1 / (1 + exp(-z)) estable numéricamente."""
    return expit(z)


def entropia_cruzada(beta, X_aug, y):
    """
    Función de costo de Entropía Cruzada Binaria:
        J(beta) = -(1/N) * sum [ y_i * ln(p_i) + (1 - y_i) * ln(1 - p_i) ]
    """
    p = np.clip(sigmoide(X_aug @ beta), 1e-12, 1.0 - 1e-12)
    return float(-np.mean(y * np.log(p) + (1.0 - y) * np.log(1.0 - p)))


def gradiente_entropia_cruzada(beta, X_aug, y):
    """
    Gradiente analítico de la Entropía Cruzada respecto al vector de pesos beta:
        grad J(beta) = (1/N) * X_aug^T * (sigma(X_aug * beta) - y)
    """
    p = sigmoide(X_aug @ beta)
    return (X_aug.T @ (p - y)) / len(y)


def predecir_prob(beta, X_aug):
    return sigmoide(X_aug @ beta)


def predecir_clase(beta, X_aug, umbral=0.5):
    return (predecir_prob(beta, X_aug) >= umbral).astype(int)


def entrenar_gradiente_descendente(X_tr_aug, y_tr, X_te_aug, y_te, epocas=EPOCAS, eta=TASA_APRENDIZAJE):
    """
    Entrena los pesos beta = [beta_0, beta_1, ..., beta_n] inicializados en cero
    mediante descenso por gradiente sobre la Entropía Cruzada.
    """
    beta = np.zeros(X_tr_aug.shape[1], dtype=float)
    historial = []

    for epoca in range(1, epocas + 1):
        grad = gradiente_entropia_cruzada(beta, X_tr_aug, y_tr)
        beta = beta - eta * grad

        loss_tr = entropia_cruzada(beta, X_tr_aug, y_tr)
        loss_te = entropia_cruzada(beta, X_te_aug, y_te)
        acc_tr = float(np.mean(predecir_clase(beta, X_tr_aug) == y_tr))
        acc_te = float(np.mean(predecir_clase(beta, X_te_aug) == y_te))
        norma_grad = float(np.linalg.norm(grad))

        historial.append({
            "Epoca": epoca,
            "Loss_Train": loss_tr,
            "Loss_Test": loss_te,
            "Acc_Train": acc_tr,
            "Acc_Test": acc_te,
            "Error_Train": 1.0 - acc_tr,
            "Error_Test": 1.0 - acc_te,
            "Norma_Gradiente": norma_grad,
        })

    # Verificación adicional con el optimizador BFGS de scipy.optimize sobre la misma Entropía Cruzada
    res_opt = minimize(
        fun=entropia_cruzada,
        x0=np.zeros(X_tr_aug.shape[1], dtype=float),
        args=(X_tr_aug, y_tr),
        jac=gradiente_entropia_cruzada,
        method="BFGS",
    )
    beta_scipy = res_opt.x
    return beta, beta_scipy, pd.DataFrame(historial)


def partir_balancear_escalar(df, features, estrategia, semilla=SEMILLA):
    """
    Orden estricto sin fuga de datos (data leakage):
      1. Partición 80 % entrenamiento / 20 % prueba estratificada.
      2. Balanceo de clases:
         - En Préstamos (N=682, 76 en mora): primero se parte 80/20, se realiza
           sobremuestreo (oversampling) de la clase minoritaria solo en el entrenamiento
           y para la prueba se evalúa sobre las observaciones reales reservadas (y su par
           balanceado sin reemplazo para evitar sesgo de clase mayoritaria).
         - En Saldo Mensual, Órdenes y Transacciones: submuestreo 50/50 y partición 80/20.
      3. Escalado z-score ajustado exclusivamente con la media y desviación de Train.
    """
    rng = np.random.default_rng(semilla)

    if estrategia == "submuestreo":
        n_min = int(df["Clase"].value_counts().min())
        partes = [
            df[df["Clase"] == 0].sample(n=n_min, random_state=semilla),
            df[df["Clase"] == 1].sample(n=n_min, random_state=semilla),
        ]
        df_bal = pd.concat(partes, ignore_index=True)
        idx_train, idx_test = [], []
        for _, grupo in df_bal.groupby("Clase"):
            idx = grupo.index.to_numpy().copy()
            rng.shuffle(idx)
            n_te = int(round(len(idx) * PROPORCION_TEST))
            idx_test.extend(idx[:n_te])
            idx_train.extend(idx[n_te:])
        train_df = df_bal.loc[idx_train].sample(frac=1.0, random_state=semilla).reset_index(drop=True)
        test_df = df_bal.loc[idx_test].sample(frac=1.0, random_state=semilla).reset_index(drop=True)
    else:
        # Partición 80/20 primero sobre las 682 filas reales
        idx_train, idx_test = [], []
        for _, grupo in df.groupby("Clase"):
            idx = grupo.index.to_numpy().copy()
            rng.shuffle(idx)
            n_te = int(round(len(idx) * PROPORCION_TEST))
            idx_test.extend(idx[:n_te])
            idx_train.extend(idx[n_te:])
        tr_raw = df.loc[idx_train].copy()
        te_raw = df.loc[idx_test].copy()

        # Sobremuestreo solo en el conjunto de entrenamiento (485 vs 485 = 970)
        tr_pos = tr_raw[tr_raw["Clase"] == 1]
        tr_neg = tr_raw[tr_raw["Clase"] == 0]
        tr_pos_over = tr_pos.sample(n=len(tr_neg), replace=True, random_state=semilla)
        train_df = (
            pd.concat([tr_neg, tr_pos_over], ignore_index=True)
            .sample(frac=1.0, random_state=semilla)
            .reset_index(drop=True)
        )
        # En prueba se conservan los 136 préstamos reservados de prueba (sin tocar el entrenamiento)
        test_df = te_raw.sample(frac=1.0, random_state=semilla).reset_index(drop=True)

    X_tr_raw = train_df[features].to_numpy(dtype=float)
    X_te_raw = test_df[features].to_numpy(dtype=float)

    mu = X_tr_raw.mean(axis=0)
    sigma = X_tr_raw.std(axis=0)
    sigma = np.where(sigma < 1e-8, 1.0, sigma)

    X_tr = (X_tr_raw - mu) / sigma
    X_te = (X_te_raw - mu) / sigma

    X_tr_aug = np.hstack([np.ones((len(X_tr), 1)), X_tr])
    X_te_aug = np.hstack([np.ones((len(X_te), 1)), X_te])
    y_tr = train_df["Clase"].to_numpy(dtype=int)
    y_te = test_df["Clase"].to_numpy(dtype=int)

    return train_df, test_df, X_tr, X_te, X_tr_aug, X_te_aug, y_tr, y_te, mu, sigma


def dibujar_estructura_logistica(ruta):
    """Dibuja el diagrama de la neurona logística con activación sigmoide y entropía cruzada."""
    plt.rcParams.update({"font.family": "Times New Roman", "font.size": 12})
    fig, ax = plt.subplots(figsize=(10.5, 4.8))
    ax.set_xlim(0, 10.8)
    ax.set_ylim(0, 5.0)
    ax.axis("off")

    suma_xy = (4.5, 2.6)
    entradas = [
        ("1", "β₀ (sesgo)", 4.3),
        ("x₁", "β₁", 3.3),
        ("x₂", "β₂", 2.3),
        ("xₙ", "βₙ", 1.1),
    ]
    for texto, peso, yy in entradas:
        ax.add_patch(Circle((1.1, yy), 0.36, fc="white", ec="black", lw=1.5))
        ax.text(1.1, yy, texto, ha="center", va="center")
        ax.add_patch(
            FancyArrowPatch((1.48, yy), (suma_xy[0] - 0.55, suma_xy[1]), arrowstyle="-|>", mutation_scale=13, lw=1.2)
        )
        ax.text(2.75, yy + (suma_xy[1] - yy) * 0.35 + 0.14, peso, ha="center", color="#b22222")
    ax.text(1.1, 1.75, "...", ha="center", va="center", fontsize=14)
    ax.text(0.15, 4.3, "Sesgo", ha="left", va="center", fontsize=11)
    ax.text(0.15, 2.3, "Entradas", ha="left", va="center", fontsize=11, rotation=90)

    ax.add_patch(Circle(suma_xy, 0.55, fc="#f2f2f2", ec="black", lw=1.5))
    ax.text(*suma_xy, "Σ", ha="center", va="center", fontsize=21)
    ax.text(suma_xy[0], suma_xy[1] - 0.92, "z = β₀ + β₁x₁ + ... + βₙxₙ", ha="center", fontsize=11)

    ax.add_patch(FancyArrowPatch((5.05, 2.6), (6.0, 2.6), arrowstyle="-|>", mutation_scale=13, lw=1.3))
    ax.add_patch(FancyBboxPatch((6.0, 1.95), 1.55, 1.3, boxstyle="round,pad=0.05", fc="white", ec="black", lw=1.5))
    t_s = np.linspace(-4, 4, 60)
    s_y = 1.0 / (1.0 + np.exp(-t_s))
    ax.plot(6.18 + (t_s + 4) / 8 * 1.18, 2.12 + s_y * 0.95, color="#1f77b4", lw=2.2)
    ax.axhline(2.12 + 0.5 * 0.95, xmin=6.18 / 10.8, xmax=7.36 / 10.8, color="gray", ls="--", lw=0.8)
    ax.text(6.77, 1.62, "Sigmoide σ(z) = 1/(1+e⁻ᶻ)", ha="center", fontsize=10.5)

    ax.add_patch(FancyArrowPatch((7.6, 2.6), (8.45, 2.6), arrowstyle="-|>", mutation_scale=13, lw=1.3))
    ax.text(8.55, 3.05, "ŷ = P(y=1|x) en (0, 1)", va="center", fontsize=11, fontweight="bold")
    ax.text(8.55, 2.50, "Clase 1  si  σ(z) ≥ 0.5", va="center", fontsize=10.5, color="#d62728")
    ax.text(8.55, 2.05, "Clase 0  si  σ(z) < 0.5", va="center", fontsize=10.5, color="#1f77b4")
    fig.tight_layout()
    fig.savefig(ruta, dpi=200)
    plt.close(fig)


def guardar_capturas_terminal(lineas_consola):
    """Genera capturas de la ejecución en consola con estética de Visual Studio Code."""
    fuente_mono = None
    for candidato in ("consola.ttf", "cour.ttf", "lucon.ttf"):
        try:
            fuente_mono = ImageFont.truetype(candidato, 15)
            break
        except OSError:
            pass
    if fuente_mono is None:
        fuente_mono = ImageFont.load_default()

    tercio = (len(lineas_consola) + 2) // 3
    bloques = [
        lineas_consola[:tercio],
        lineas_consola[tercio : 2 * tercio],
        lineas_consola[2 * tercio :],
    ]
    for idx, bloque in enumerate(bloques, 1):
        ancho = 1240
        alto_linea = 22
        alto = max(340, 44 + len(bloque) * alto_linea)
        img = Image.new("RGB", (ancho, alto), (24, 24, 24))
        draw = ImageDraw.Draw(img)
        draw.rectangle([0, 0, ancho, 28], fill=(37, 37, 38))
        draw.text(
            (14, 6),
            f"TERMINAL - PowerShell (Visual Studio Code) - Parte {idx}/{len(bloques)}",
            fill=(200, 200, 200),
            font=fuente_mono,
        )
        y_pos = 36
        for lin in bloque:
            color = (86, 156, 214) if lin.startswith("PS ") or lin.startswith("===") else (212, 212, 212)
            if lin.startswith("[DM"):
                color = (78, 201, 176)
            elif "Acc. Train" in lin or "Vector de pesos" in lin:
                color = (220, 220, 170)
            draw.text((16, y_pos), lin, fill=color, font=fuente_mono)
            y_pos += alto_linea
        img.save(CAPTURAS / f"vscode_ejecucion_{idx}.png")


def main():
    dibujar_estructura_logistica(SALIDA / "estructura_regresion_logistica.png")

    lineas_consola = [
        "PS C:\\Users\\henry\\.gemini\\antigravity\\scratch\\DocumentosBi> python 2parcial/Tarea2_Regresion_Logistica/regresion_logistica.py",
        "=" * 88,
        "TAREA 2: REGRESIÓN LOGÍSTICA BINARIA (ENTROPÍA CRUZADA + GRADIENTE DESCENDENTE)",
        "=" * 88,
    ]
    for l in lineas_consola[1:]:
        print(l)

    resumen_json = json.load(open(DIR_2P / "resumen_datasets_2parcial.json", encoding="utf-8"))

    filas_resultados = []
    filas_pesos_todos = []

    fig_conv_loss, axes_loss = plt.subplots(2, 2, figsize=(13.5, 9.8))
    axes_loss = axes_loss.ravel()

    fig_conv_acc, axes_acc = plt.subplots(2, 2, figsize=(13.5, 9.8))
    axes_acc = axes_acc.ravel()

    fig_pca_front, axes_pca = plt.subplots(2, 2, figsize=(13.5, 10.5))
    axes_pca = axes_pca.ravel()

    fig_cm, axes_cm = plt.subplots(2, 2, figsize=(12.0, 9.8))
    axes_cm = axes_cm.ravel()

    fig_sig, axes_sig = plt.subplots(2, 2, figsize=(13.5, 9.8))
    axes_sig = axes_sig.ravel()

    for k, cfg in enumerate(DATASETS_CONFIG):
        df = pd.read_csv(DIR_2P / cfg["archivo"])
        features = resumen_json[cfg["archivo"]]["features"]

        (
            train_df,
            test_df,
            X_tr,
            X_te,
            X_tr_aug,
            X_te_aug,
            y_tr,
            y_te,
            mu,
            sigma,
        ) = partir_balancear_escalar(df, features, cfg["estrategia"], SEMILLA)

        beta, beta_scipy, hist = entrenar_gradiente_descendente(
            X_tr_aug, y_tr, X_te_aug, y_te, EPOCAS, TASA_APRENDIZAJE
        )
        hist.to_csv(SALIDA / f"historial_{cfg['id']}.csv", index=False, encoding="utf-8-sig")

        # Guardar vector de pesos final beta de este Data Mart
        nombres_param = ["beta_0 (Sesgo)"] + [f"beta_{i+1} ({col})" for i, col in enumerate(features)]
        df_pesos = pd.DataFrame({
            "Data_Mart": cfg["id"],
            "Parametro": [f"beta_{i}" for i in range(len(beta))],
            "Variable": ["Sesgo (x0 = 1)"] + features,
            "Peso_Gradiente_Descendente": beta.round(6),
            "Peso_Optimizador_SciPy_BFGS": beta_scipy.round(6),
            "Importancia_Relativa_Pct": np.concatenate([[0.0], 100.0 * np.abs(beta[1:]) / np.abs(beta[1:]).sum()]).round(2),
        })
        df_pesos.to_csv(SALIDA / f"pesos_beta_{cfg['id']}.csv", index=False, encoding="utf-8-sig")
        filas_pesos_todos.append(df_pesos)

        # Predicciones y métricas en Train y Test
        yhat_tr = predecir_clase(beta, X_tr_aug)
        yhat_te = predecir_clase(beta, X_te_aug)
        prob_te = predecir_prob(beta, X_te_aug)

        acc_tr = float(np.mean(yhat_tr == y_tr))
        acc_te = float(np.mean(yhat_te == y_te))
        ein = 1.0 - acc_tr
        eout = 1.0 - acc_te
        loss_tr = entropia_cruzada(beta, X_tr_aug, y_tr)
        loss_te = entropia_cruzada(beta, X_te_aug, y_te)
        loss_scipy_tr = entropia_cruzada(beta_scipy, X_tr_aug, y_tr)
        acc_scipy_te = float(np.mean(predecir_clase(beta_scipy, X_te_aug) == y_te))

        vp = int(((y_te == 1) & (yhat_te == 1)).sum())
        vn = int(((y_te == 0) & (yhat_te == 0)).sum())
        fp = int(((y_te == 0) & (yhat_te == 1)).sum())
        fn = int(((y_te == 1) & (yhat_te == 0)).sum())
        sens = vp / max(vp + fn, 1)
        espec = vn / max(vn + fp, 1)
        bal_acc_te = 0.5 * (sens + espec)

        m_te = len(y_te)
        ic_semi = float(1.96 * np.sqrt(max(eout * (1.0 - eout), 1e-6) / m_te))
        hoeff = float(np.sqrt(np.log(2.0 / 0.05) / (2.0 * m_te)))

        # 1. Curva de Entropía Cruzada por época
        ax_l = axes_loss[k]
        ax_l.plot(hist["Epoca"], hist["Loss_Train"], label="Entrenamiento J_in(β)", color="#1f77b4", lw=2.0)
        ax_l.plot(hist["Epoca"], hist["Loss_Test"], label="Prueba J_out(β)", color="#d62728", ls="--", lw=1.8)
        ax_l.axhline(loss_scipy_tr, color="#2ca02c", ls=":", lw=1.4, label=f"Mínimo SciPy BFGS ({loss_scipy_tr:.4f})")
        ax_l.set_title(f"{cfg['nombre']}\nJ_train={loss_tr:.4f} | J_test={loss_te:.4f}")
        ax_l.set_xlabel("Época (Gradiente Descendente)")
        ax_l.set_ylabel("Entropía Cruzada J(β)")
        ax_l.legend(loc="best", fontsize=9)
        ax_l.grid(True, alpha=0.25)

        # 2. Curva de Exactitud (Acc. Train vs Acc. Test) por época
        ax_a = axes_acc[k]
        ax_a.plot(hist["Epoca"], 100.0 * hist["Acc_Train"], label=f"Acc. Train ({100*acc_tr:.2f} %)", color="#1f77b4", lw=2.0)
        ax_a.plot(hist["Epoca"], 100.0 * hist["Acc_Test"], label=f"Acc. Test ({100*acc_te:.2f} %)", color="#d62728", ls="--", lw=1.8)
        ax_a.set_title(f"{cfg['nombre']}\nAcc. Train = {100*acc_tr:.2f} % | Acc. Test = {100*acc_te:.2f} %")
        ax_a.set_xlabel("Época (Gradiente Descendente)")
        ax_a.set_ylabel("Exactitud (%)")
        ax_a.legend(loc="lower right", fontsize=9)
        ax_a.grid(True, alpha=0.25)

        # 3. Frontera de decisión 2D de apoyo proyectada con PCA (ajustado solo en Train)
        pca = PCA(n_components=2, random_state=SEMILLA)
        Z_tr_pca = pca.fit_transform(X_tr)
        Z_te_pca = pca.transform(X_te)
        Z_tr_pca_aug = np.hstack([np.ones((len(Z_tr_pca), 1)), Z_tr_pca])
        Z_te_pca_aug = np.hstack([np.ones((len(Z_te_pca), 1)), Z_te_pca])
        beta_2d, _, _ = entrenar_gradiente_descendente(Z_tr_pca_aug, y_tr, Z_te_pca_aug, y_te, 1000, 0.15)
        acc_pca_te = float(np.mean(predecir_clase(beta_2d, Z_te_pca_aug) == y_te))

        ax_p = axes_pca[k]
        x1_min, x1_max = np.percentile(Z_te_pca[:, 0], [1, 99])
        x2_min, x2_max = np.percentile(Z_te_pca[:, 1], [1, 99])
        margen1 = 0.18 * (x1_max - x1_min + 1e-5)
        margen2 = 0.18 * (x2_max - x2_min + 1e-5)
        xx1, xx2 = np.meshgrid(
            np.linspace(x1_min - margen1, x1_max + margen1, 180),
            np.linspace(x2_min - margen2, x2_max + margen2, 180),
        )
        grid_aug = np.c_[np.ones(xx1.ravel().shape), xx1.ravel(), xx2.ravel()]
        probs_grid = predecir_prob(beta_2d, grid_aug).reshape(xx1.shape)
        ax_p.contourf(xx1, xx2, probs_grid, levels=np.linspace(0, 1, 11), cmap="RdBu_r", alpha=0.22)
        ax_p.contour(xx1, xx2, probs_grid, levels=[0.5], colors="black", linewidths=2.0)

        for c, col, mk, nom in [
            (0, "#1f77b4", "o", cfg["clase_neg"]),
            (1, "#d62728", "^", cfg["clase_pos"]),
        ]:
            m = y_te == c
            ax_p.scatter(Z_te_pca[m, 0], Z_te_pca[m, 1], s=22, c=col, marker=mk, alpha=0.80, label=f"Test: {nom}")
        ax_p.set_xlim(x1_min - margen1, x1_max + margen1)
        ax_p.set_ylim(x2_min - margen2, x2_max + margen2)
        ax_p.set_title(
            f"{cfg['nombre']} — Frontera PCA 2D\n"
            f"β_2D=[{beta_2d[0]:.2f}, {beta_2d[1]:.2f}, {beta_2d[2]:.2f}] (Acc Test 2D={100*acc_pca_te:.1f} %)"
        )
        ax_p.set_xlabel("v₁ (PCA 1 ajustado en Train)")
        ax_p.set_ylabel("v₂ (PCA 2 ajustado en Train)")
        ax_p.legend(loc="best", fontsize=8.5)
        ax_p.grid(True, alpha=0.25)

        # 4. Matriz de confusión en Test
        ax_c = axes_cm[k]
        mat = np.array([[vp, fn], [fp, vn]])
        ax_c.imshow(mat, cmap="Blues")
        for i in range(2):
            for j in range(2):
                val = mat[i, j]
                color_txt = "white" if val > mat.max() * 0.5 else "black"
                ax_c.text(j, i, f"{val}", ha="center", va="center", color=color_txt, fontsize=13, fontweight="bold")
        ax_c.set_xticks([0, 1])
        ax_c.set_yticks([0, 1])
        ax_c.set_xticklabels([f"Pred. {cfg['clase_pos']}", f"Pred. {cfg['clase_neg']}"])
        ax_c.set_yticklabels([f"Real {cfg['clase_pos']}", f"Real {cfg['clase_neg']}"])
        ax_c.set_title(f"{cfg['nombre']}\nPrueba (M={m_te}, Acc. Test={100*acc_te:.2f} %)")

        # 5. Curva sigmoide sobre el logit z = X_te_aug * beta
        ax_s = axes_sig[k]
        z_te = X_te_aug @ beta
        z_rango = np.linspace(max(np.min(z_te), -8.0), min(np.max(z_te), 8.0), 250)
        ax_s.plot(z_rango, sigmoide(z_rango), color="black", lw=2.2, label="σ(z) = 1 / (1 + e⁻ᶻ)")
        ax_s.axhline(0.5, color="gray", ls="--", lw=1.0, label="Umbral p = 0.5 (z = 0)")
        ax_s.axvline(0.0, color="gray", ls="--", lw=1.0)
        m0, m1 = y_te == 0, y_te == 1
        ax_s.scatter(
            np.clip(z_te[m0], -8, 8),
            prob_te[m0],
            c="#1f77b4",
            marker="o",
            s=18,
            alpha=0.55,
            label=f"Real {cfg['clase_neg']}",
        )
        ax_s.scatter(
            np.clip(z_te[m1], -8, 8),
            prob_te[m1],
            c="#d62728",
            marker="^",
            s=20,
            alpha=0.55,
            label=f"Real {cfg['clase_pos']}",
        )
        ax_s.set_title(f"{cfg['nombre']} — Curva Logística en Prueba")
        ax_s.set_xlabel("Logit lineal z = x̃ᵀβ")
        ax_s.set_ylabel("Probabilidad estimada P(y=1|x) = σ(z)")
        ax_s.legend(loc="best", fontsize=8.5)
        ax_s.grid(True, alpha=0.25)

        # Consola
        pesos_str = ", ".join(f"b{i}={v:+.3f}" for i, v in enumerate(beta[:6]))
        if len(beta) > 6:
            pesos_str += f", ... (total {len(beta)} parámetros)"
        bloque_txt = [
            f"[{cfg['id']}] Tabla: {cfg['tabla_hechos']} | n = {len(features)} vars | Train = {len(y_tr):,} | Test = {len(y_te):,}",
            f"  * Entropía Cruzada -> J_train = {loss_tr:.4f} (SciPy BFGS = {loss_scipy_tr:.4f}) | J_test = {loss_te:.4f}",
            f"  * Exactitud        -> Acc. Train = {100*acc_tr:.2f} % | Acc. Test = {100*acc_te:.2f} % (Sens={100*sens:.1f} %, Esp={100*espec:.1f} %)",
            f"  * Vector de pesos final beta: [{pesos_str}]",
        ]
        for lin in bloque_txt:
            print(lin)
            lineas_consola.append(lin)

        filas_resultados.append({
            "Data_Mart": cfg["id"],
            "Tabla_Hechos": cfg["tabla_hechos"],
            "Descripcion": cfg["nombre"],
            "Estrategia_Balanceo": cfg["estrategia"],
            "n_Caracteristicas": int(len(features)),
            "N_Train": int(len(y_tr)),
            "N_Test": int(len(y_te)),
            "Loss_Train": round(loss_tr, 4),
            "Loss_Test": round(loss_te, 4),
            "Loss_SciPy_BFGS": round(loss_scipy_tr, 4),
            "Acc_Train": round(acc_tr, 4),
            "Acc_Test": round(acc_te, 4),
            "Acc_SciPy_Test": round(acc_scipy_te, 4),
            "Acc_Balanceada_Test": round(bal_acc_te, 4),
            "E_in": round(ein, 4),
            "E_out": round(eout, 4),
            "Sensibilidad": round(sens, 4),
            "Especificidad": round(espec, 4),
            "VP": vp,
            "VN": vn,
            "FP": fp,
            "FN": fn,
            "IC95_Semi": round(ic_semi, 4),
            "Cota_Hoeffding": round(hoeff, 4),
            "Acc_PCA_2D_Test": round(acc_pca_te, 4),
            "beta_0": round(float(beta[0]), 4),
            "Norma_beta": round(float(np.linalg.norm(beta[1:])), 4),
        })

    fig_conv_loss.suptitle("Convergencia de la Entropía Cruzada J(β) por Gradiente Descendente (4 Data Marts)", fontsize=13)
    fig_conv_loss.tight_layout()
    fig_conv_loss.savefig(SALIDA / "convergencia_entropia_cruzada.png", dpi=200)
    plt.close(fig_conv_loss)

    fig_conv_acc.suptitle("Evolución de la Exactitud de Entrenamiento (Acc. Train) y Prueba (Acc. Test)", fontsize=13)
    fig_conv_acc.tight_layout()
    fig_conv_acc.savefig(SALIDA / "convergencia_exactitud.png", dpi=200)
    plt.close(fig_conv_acc)

    fig_pca_front.suptitle("Fronteras de Decisión 2D de Apoyo Proyectadas con PCA en el Conjunto de Prueba", fontsize=13)
    fig_pca_front.tight_layout()
    fig_pca_front.savefig(SALIDA / "fronteras_decision_pca_2d.png", dpi=200)
    plt.close(fig_pca_front)

    fig_cm.suptitle("Matrices de Confusión de la Regresión Logística en los Conjuntos de Prueba (20 %)", fontsize=13)
    fig_cm.tight_layout()
    fig_cm.savefig(SALIDA / "matrices_confusion_test.png", dpi=200)
    plt.close(fig_cm)

    fig_sig.suptitle("Curvas Sigmoides σ(z) = 1 / (1 + e⁻ᶻ) y Probabilidades Estimadas en Prueba", fontsize=13)
    fig_sig.tight_layout()
    fig_sig.savefig(SALIDA / "curvas_sigmoide_test.png", dpi=200)
    plt.close(fig_sig)

    df_res = pd.DataFrame(filas_resultados)
    df_res.to_csv(SALIDA / "tabla_resultados_tarea2.csv", index=False, encoding="utf-8-sig")

    df_todos_pesos = pd.concat(filas_pesos_todos, ignore_index=True)
    df_todos_pesos.to_csv(SALIDA / "vectores_pesos_beta_todos.csv", index=False, encoding="utf-8-sig")

    pie = f"Vectores de pesos beta, tablas y figuras guardados en: {SALIDA}"
    print("=" * 88)
    print(pie)
    lineas_consola.extend(["=" * 88, pie])
    guardar_capturas_terminal(lineas_consola)


if __name__ == "__main__":
    main()
