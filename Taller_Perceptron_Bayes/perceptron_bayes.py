"""
Taller: Perceptrón frente al clasificador de Bayes
Asignatura: Inteligencia de Negocios - Carrera de Software, 6to "A"
Autores: Lagua Flores Henry Daniel / Cobos Taco Alison Marcela

Se entrena un perceptrón con clases 0/1 tal como indican las diapositivas 13-15:

    y_pred = 1 si z >= 0, en otro caso 0
    error  = y - y_pred
    si error != 0:
        w  = w  + 0.1 * error * x
        w0 = w0 + 0.1 * error

y se compara su error con el error de Bayes en dos conjuntos de datos:
  1. El CSV del taller anterior (clases casi perfectamente separadas).
  2. Datos generados con dos clases normales, probabilidad p0 = 0.5 y una
     separación alpha = 5 entre los centros, medida en desviaciones estándar.
     Mientras menor es alpha, más se superponen las distribuciones.

Partición de los datos: 70 % entrenamiento, 15 % validación y 15 % prueba.
La validación se usa para conservar el mejor perceptrón (los pesos con menor
error de validación); la prueba solo se usa al final para medir E_out.

Ejecución (terminal de Visual Studio Code):  python perceptron_bayes.py
"""

from math import erf, sqrt
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

CARPETA = Path(__file__).resolve().parent
ARCHIVO_CSV = CARPETA / "dataset_Perceptron_5000_continuo_menos1_a_1.csv"
ARCHIVO_GENERADO = CARPETA / "dataset_generado_p0_0.5_alpha_5.csv"
SALIDA = CARPETA / "resultados"
SALIDA.mkdir(exist_ok=True)

COLUMNAS = ["Caracteristica_1", "Caracteristica_2", "Caracteristica_3"]
P0 = 0.5                 # probabilidad a priori de la clase Mujer (0)
ALPHA = 5.0              # separación entre las clases en desviaciones estándar
N_GENERADO = 20000       # registros generados
PARTICION = (0.70, 0.15, 0.15)
ETA = 0.1                # tasa de aprendizaje (diapositiva 14)
EPOCAS = 200
SEMILLA = 42
ALPHAS_BARRIDO = [1, 2, 3, 4, 5, 6, 8]
COLORES = {1: "#d62728", 0: "#1f77b4"}
NOMBRES = {1: "Hombre (1)", 0: "Mujer (0)"}

plt.rcParams.update({"font.family": "Times New Roman", "font.size": 12,
                     "axes.titlesize": 13, "savefig.dpi": 200})


def titulo(texto):
    print("\n" + "=" * 70)
    print(texto)
    print("=" * 70)


def phi(t):
    """Función de distribución acumulada de la normal estándar."""
    return 0.5 * (1 + erf(t / sqrt(2)))


# ----------------------------------------------------------------------------
# Datos
# ----------------------------------------------------------------------------
def generar_datos(n, p0, alpha, semilla):
    """Dos clases normales con covarianza identidad y centros separados alpha.

    Los centros están sobre la diagonal (1, 1, 1), en -alpha/2 y +alpha/2, de modo
    que la distancia de Mahalanobis entre las clases es exactamente alpha.
    """
    rng = np.random.default_rng(semilla)
    u = np.ones(3) / np.sqrt(3)
    mu0, mu1 = -alpha / 2 * u, alpha / 2 * u
    n0 = int(round(n * p0))
    X = np.vstack([rng.normal(mu0, 1.0, size=(n0, 3)),
                   rng.normal(mu1, 1.0, size=(n - n0, 3))])
    y = np.concatenate([np.zeros(n0, dtype=int), np.ones(n - n0, dtype=int)])
    orden = rng.permutation(n)
    df = pd.DataFrame(X[orden].round(4), columns=COLUMNAS)
    df["Clase"] = np.where(y[orden] == 1, "Hombre", "Mujer")
    parametros = {"mu0": mu0, "mu1": mu1, "cov": np.eye(3), "p0": p0}
    return df, parametros


def cargar(df):
    """Codificación de la diapositiva 15: Hombre = 1, Mujer = 0."""
    X = df[COLUMNAS].to_numpy(dtype=float)
    y = (df["Clase"] == "Hombre").astype(int).to_numpy()
    return X, y


def particionar(X, y, proporciones, semilla):
    """Partición estratificada entrenamiento / validación / prueba."""
    rng = np.random.default_rng(semilla)
    partes = {"entrenamiento": [], "validacion": [], "prueba": []}
    for clase in (0, 1):
        idx = np.flatnonzero(y == clase)
        rng.shuffle(idx)
        n_tr = int(round(len(idx) * proporciones[0]))
        n_va = int(round(len(idx) * proporciones[1]))
        partes["entrenamiento"].extend(idx[:n_tr])
        partes["validacion"].extend(idx[n_tr:n_tr + n_va])
        partes["prueba"].extend(idx[n_tr + n_va:])
    salida = {}
    for nombre, idx in partes.items():
        idx = rng.permutation(np.array(idx))         # mezcla las dos clases
        salida[nombre] = (X[idx], y[idx])
    return salida


# ----------------------------------------------------------------------------
# Perceptrón (diapositivas 13 a 15)
# ----------------------------------------------------------------------------
def escalon(z):
    """Salida escalón explícita: 1 si z >= 0, en otro caso 0."""
    return np.where(z >= 0, 1, 0)


def predecir(w, w0, X):
    return escalon(X @ w + w0)


def tasa_error(w, w0, X, y):
    return float(np.mean(predecir(w, w0, X) != y))


def entrenar_perceptron(X, y, X_val, y_val, eta, epocas, semilla):
    """Perceptrón con clases 0/1 y conservación del mejor perceptrón (validación)."""
    rng = np.random.default_rng(semilla)
    w = np.zeros(X.shape[1])
    w0 = 0.0
    mejor = {"w": w.copy(), "w0": w0, "epoca": 0, "error_val": 1.0}
    historial = []
    for epoca in range(1, epocas + 1):
        errores = 0
        for i in rng.permutation(len(X)):            # recorrer las observaciones
            z = np.dot(w, X[i]) + w0                 # suma ponderada
            y_pred = 1 if z >= 0 else 0              # salida escalón
            error = y[i] - y_pred                    # error = y - predicción
            if error != 0:                           # solo se corrige si falla
                w = w + eta * error * X[i]
                w0 = w0 + eta * error
                errores += 1
        e_tr = tasa_error(w, w0, X, y)
        e_va = tasa_error(w, w0, X_val, y_val)
        if e_va < mejor["error_val"]:
            mejor = {"w": w.copy(), "w0": w0, "epoca": epoca, "error_val": e_va}
        historial.append({"Epoca": epoca, "Actualizaciones": errores,
                          "Error_entrenamiento": e_tr, "Error_validacion": e_va,
                          "Mejor_error_validacion": mejor["error_val"]})
        if errores == 0:                              # convergencia (diapositiva 13)
            break
    return mejor, pd.DataFrame(historial)


# ----------------------------------------------------------------------------
# Clasificador de Bayes
# ----------------------------------------------------------------------------
def bayes_lineal(mu0, mu1, cov, p0):
    """Regla de Bayes para dos normales con la misma covarianza: frontera lineal."""
    inv = np.linalg.inv(cov)
    w = inv @ (mu1 - mu0)
    w0 = -0.5 * (mu1 + mu0) @ w + np.log((1 - p0) / p0)
    delta = float(np.sqrt((mu1 - mu0) @ inv @ (mu1 - mu0)))
    return w, w0, delta


def error_bayes_teorico(delta, p0):
    """Error de Bayes para dos normales con covarianza común y distancia delta."""
    p1 = 1 - p0
    if p0 == p1:
        return phi(-delta / 2)
    k = np.log(p0 / p1) / delta
    return p1 * phi(-delta / 2 + k) + p0 * phi(-delta / 2 - k)


def estimar_bayes(X, y):
    """Bayes con parámetros estimados (medias, covarianza común y p0 de los datos)."""
    mu0, mu1 = X[y == 0].mean(axis=0), X[y == 1].mean(axis=0)
    cov = (np.cov(X[y == 0].T) * (np.sum(y == 0) - 1) +
           np.cov(X[y == 1].T) * (np.sum(y == 1) - 1)) / (len(y) - 2)
    return bayes_lineal(mu0, mu1, cov, float(np.mean(y == 0)))


# ----------------------------------------------------------------------------
# Evaluación
# ----------------------------------------------------------------------------
def matriz_confusion(y, y_pred):
    return pd.DataFrame([[int(np.sum((y == 1) & (y_pred == 1))), int(np.sum((y == 1) & (y_pred == 0)))],
                         [int(np.sum((y == 0) & (y_pred == 1))), int(np.sum((y == 0) & (y_pred == 0)))]],
                        index=["Real Hombre (1)", "Real Mujer (0)"],
                        columns=["Pred. Hombre (1)", "Pred. Mujer (0)"])


def intervalo_confianza(error, n, z=1.96):
    """Intervalo de confianza del 95 % para una proporción de error.

    Con cero errores la fórmula normal da un intervalo vacío, así que se usa la
    regla del tres: el límite superior al 95 % es 3/n.
    """
    if error == 0:
        return 0.0, 3 / n, 3 / n
    margen = z * sqrt(error * (1 - error) / n)
    return max(0.0, error - margen), min(1.0, error + margen), margen


def experimento(nombre, df, bayes_real, etiqueta, mostrar=True):
    """Particiona, entrena el perceptrón y compara con Bayes en un conjunto de datos."""
    X, y = cargar(df)
    partes = particionar(X, y, PARTICION, SEMILLA)
    (X_tr, y_tr), (X_va, y_va), (X_te, y_te) = (partes["entrenamiento"],
                                                partes["validacion"], partes["prueba"])
    mejor, hist = entrenar_perceptron(X_tr, y_tr, X_va, y_va, ETA, EPOCAS, SEMILLA)
    w, w0 = mejor["w"], mejor["w0"]

    if bayes_real is not None:
        wb, wb0, delta = bayes_lineal(bayes_real["mu0"], bayes_real["mu1"],
                                      bayes_real["cov"], bayes_real["p0"])
        origen = "parámetros reales de la distribución generadora"
    else:
        wb, wb0, delta = estimar_bayes(X_tr, y_tr)
        origen = "parámetros estimados con los datos de entrenamiento"
    p0 = float(np.mean(y == 0))

    res = {
        "Datos": nombre, "Registros": len(y), "Entrenamiento": len(y_tr),
        "Validacion": len(y_va), "Prueba": len(y_te), "p0": p0, "alpha": delta,
        "Error_Bayes_teorico": error_bayes_teorico(delta, p0),
        "Error_Bayes_prueba": tasa_error(wb, wb0, X_te, y_te),
        "E_in": tasa_error(w, w0, X_tr, y_tr),
        "Error_validacion": tasa_error(w, w0, X_va, y_va),
        "E_out": tasa_error(w, w0, X_te, y_te),
        "Mejor_epoca": mejor["epoca"], "Epocas": len(hist),
        "w0": w0, "w1": w[0], "w2": w[1], "w3": w[2],
    }
    res["Accuracy_Bayes"] = 1 - res["Error_Bayes_prueba"]
    res["Accuracy_perceptron"] = 1 - res["E_out"]
    li, ls, margen = intervalo_confianza(res["E_out"], len(y_te))
    res.update({"IC95_inferior": li, "IC95_superior": ls, "IC95_margen": margen})
    mc = matriz_confusion(y_te, predecir(w, w0, X_te))

    if mostrar:
        titulo(f"{nombre.upper()}")
        print(f"Registros: {len(y)} | p0 (Mujer) = {p0:.2f} | alpha = {delta:.2f}")
        print(f"Partición 70/15/15 -> entrenamiento: {len(y_tr)} | validación: {len(y_va)} "
              f"| prueba: {len(y_te)}")
        print(f"Bayes calculado con {origen}")
        print(f"Épocas ejecutadas: {len(hist)} | mejor perceptrón en la época {mejor['epoca']}")
        print(f"Pesos del mejor perceptrón: w0 = {w0:.4f}, w = {np.round(w, 4)}")
        print(f"Error de Bayes (teórico)      = {100 * res['Error_Bayes_teorico']:.4f} %")
        print(f"Error de Bayes (prueba)       = {100 * res['Error_Bayes_prueba']:.2f} %")
        print(f"Error de entrada  E_in        = {100 * res['E_in']:.2f} %")
        print(f"Error de validación           = {100 * res['Error_validacion']:.2f} %")
        print(f"Error de salida   E_out       = {100 * res['E_out']:.2f} %  (error del perceptrón en prueba)")
        print(f"Accuracy de Bayes             = {100 * res['Accuracy_Bayes']:.2f} %")
        print(f"Accuracy del perceptrón       = {100 * res['Accuracy_perceptron']:.2f} %")
        detalle = (f"E_out ± {100 * margen:.2f} %" if res["E_out"] > 0
                   else "sin errores: regla del tres, 3/n")
        print(f"Intervalo de confianza 95 %   = [{100 * li:.2f} %, {100 * ls:.2f} %] ({detalle})")
        print(f"|E_in - E_out|                = {100 * abs(res['E_in'] - res['E_out']):.2f} %")
        print("Matriz de confusión (prueba):")
        print(mc.to_string())

        hist.to_csv(SALIDA / f"historial_{etiqueta}.csv", index=False, encoding="utf-8-sig")
        mc.to_csv(SALIDA / f"matriz_confusion_{etiqueta}.csv", encoding="utf-8-sig")
    return res, hist, mc, (X, y, w, w0, wb, wb0)


# ----------------------------------------------------------------------------
# Gráficos
# ----------------------------------------------------------------------------
def graficar_clases_2d(X, y, w, w0, wb, wb0, titulo_fig, ruta):
    """Proyección x1-x2 como la Figura 1 de MATLAB; x3 se fija en su media."""
    fig, ax = plt.subplots(figsize=(6.4, 5.2))
    for clase, marcador in [(0, "o"), (1, "x")]:
        sub = X[y == clase]
        ax.scatter(sub[:, 0], sub[:, 1], s=8, marker=marcador, alpha=0.35,
                   color=COLORES[clase], label=NOMBRES[clase],
                   facecolors="none" if marcador == "o" else None)
    x3 = X[:, 2].mean()
    xs = np.linspace(X[:, 0].min(), X[:, 0].max(), 50)
    ax.plot(xs, -(w0 + w[0] * xs + w[2] * x3) / w[1], color="black", lw=2,
            label="Frontera del perceptrón")
    ax.plot(xs, -(wb0 + wb[0] * xs + wb[2] * x3) / wb[1], "--", color="#2ca02c", lw=2,
            label="Frontera de Bayes")
    ax.set_xlim(X[:, 0].min() - 0.2, X[:, 0].max() + 0.2)
    ax.set_ylim(X[:, 1].min() - 0.2, X[:, 1].max() + 0.2)
    ax.set_xlabel("x1")
    ax.set_ylabel("x2")
    ax.set_title(titulo_fig)
    ax.grid(alpha=0.3)
    ax.legend(loc="upper left", markerscale=2, fontsize=10)
    fig.tight_layout()
    fig.savefig(ruta)
    plt.close(fig)


def graficar_distribucion(X, y, wb, wb0, alpha, ruta):
    """Distribución de las clases sobre la dirección de Bayes: muestra el traslape."""
    proy = (X @ wb + wb0) / np.linalg.norm(wb)
    fig, ax = plt.subplots(figsize=(7.5, 3.8))
    bins = np.linspace(proy.min(), proy.max(), 70)
    for clase in (0, 1):
        ax.hist(proy[y == clase], bins=bins, alpha=0.55, color=COLORES[clase],
                label=NOMBRES[clase], density=True)
    ax.axvline(0, color="black", lw=2, label="Umbral de Bayes")
    ax.set_xlabel("Proyección sobre la dirección que separa las clases")
    ax.set_ylabel("Densidad")
    ax.set_title(f"Distribución de las clases (p0 = {P0}, alpha = {alpha:g})")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(ruta)
    plt.close(fig)


def graficar_historial(hist, error_bayes, titulo_fig, ruta):
    """Historial del error y del mejor perceptrón, como la Figura 2 de MATLAB."""
    fig, ax = plt.subplots(figsize=(7.5, 4))
    ax.plot(hist["Epoca"], 100 * hist["Error_entrenamiento"], lw=1.2,
            label="Error de entrenamiento (E_in)")
    ax.plot(hist["Epoca"], 100 * hist["Error_validacion"], lw=1.2, alpha=0.8,
            label="Error de validación")
    ax.plot(hist["Epoca"], 100 * hist["Mejor_error_validacion"], color="black", lw=2,
            label="Historial del mejor perceptrón")
    ax.axhline(100 * error_bayes, color="#2ca02c", ls="--", lw=2, label="Error de Bayes")
    ax.set_xlabel("Época")
    ax.set_ylabel("Error (%)")
    ax.set_title(titulo_fig)
    ax.grid(alpha=0.3)
    ax.legend(fontsize=10)
    fig.tight_layout()
    fig.savefig(ruta)
    plt.close(fig)


def graficar_matrices(matrices, ruta):
    fig, ejes = plt.subplots(1, 2, figsize=(8.6, 3.8))
    for ax, (nombre, mc) in zip(ejes, matrices.items()):
        v = mc.to_numpy()
        ax.imshow(v, cmap="Blues")
        for i in range(2):
            for j in range(2):
                ax.text(j, i, str(v[i, j]), ha="center", va="center", fontsize=15,
                        color="white" if v[i, j] > v.max() / 2 else "black")
        ax.set_xticks([0, 1], mc.columns)
        ax.set_yticks([0, 1], mc.index)
        ax.set_title(f"{nombre} (prueba, n = {v.sum()})")
    fig.tight_layout()
    fig.savefig(ruta)
    plt.close(fig)


def graficar_barrido(tabla, ruta):
    fig, ax = plt.subplots(figsize=(7.5, 4))
    ax.plot(tabla["alpha"], 100 * tabla["Error_Bayes_teorico"], "-", color="#2ca02c", lw=2,
            label="Error de Bayes (teórico)")
    ax.plot(tabla["alpha"], 100 * tabla["Error_Bayes_prueba"], "s", color="#2ca02c",
            label="Error de Bayes (prueba)")
    ax.errorbar(tabla["alpha"], 100 * tabla["E_out"], yerr=100 * tabla["IC95_margen"],
                fmt="o", color="black", capsize=4, label="Error del perceptrón (E_out ± IC 95 %)")
    ax.set_xlabel("alpha (separación entre clases)")
    ax.set_ylabel("Error (%)")
    ax.set_yscale("symlog", linthresh=0.5)
    ax.set_title("Error de Bayes y del perceptrón según la superposición")
    ax.grid(alpha=0.3)
    ax.legend(fontsize=10)
    fig.tight_layout()
    fig.savefig(ruta)
    plt.close(fig)


def main():
    # 1. Datos generados con p0 = 0.5 y alpha = 5
    df_gen, param = generar_datos(N_GENERADO, P0, ALPHA, SEMILLA)
    df_gen.to_csv(ARCHIVO_GENERADO, index=False, encoding="utf-8-sig")
    print(f"Datos generados: {ARCHIVO_GENERADO.name} ({len(df_gen)} registros)")

    # 2. CSV del taller anterior
    df_csv = pd.read_csv(ARCHIVO_CSV, encoding="utf-8-sig")

    resultados, matrices = [], {}
    for nombre, df, real, etiqueta in [
            ("CSV del taller", df_csv, None, "csv"),
            (f"Datos generados (p0 = {P0}, alpha = {ALPHA:g})", df_gen, param, "generado")]:
        res, hist, mc, (X, y, w, w0, wb, wb0) = experimento(nombre, df, real, etiqueta)
        resultados.append(res)
        matrices[nombre.split(" (")[0]] = mc
        graficar_clases_2d(X, y, w, w0, wb, wb0, nombre, SALIDA / f"clases_{etiqueta}.png")
        graficar_distribucion(X, y, wb, wb0, res["alpha"], SALIDA / f"distribucion_{etiqueta}.png")
        graficar_historial(hist, res["Error_Bayes_teorico"], f"Historial de error - {nombre}",
                           SALIDA / f"historial_{etiqueta}.png")
    graficar_matrices(matrices, SALIDA / "matrices_confusion.png")

    tabla = pd.DataFrame(resultados)
    tabla.to_csv(SALIDA / "tabla_resultados.csv", index=False, encoding="utf-8-sig")
    titulo("RESUMEN")
    resumen = tabla[["Datos", "alpha", "Error_Bayes_teorico", "Error_Bayes_prueba", "E_in",
                     "Error_validacion", "E_out", "Accuracy_perceptron"]].copy()
    for col in resumen.columns[2:]:
        resumen[col] = (100 * resumen[col]).map(lambda v: f"{v:.2f} %")
    resumen["alpha"] = resumen["alpha"].map(lambda v: f"{v:.2f}")
    print(resumen.to_string(index=False))

    # 3. Barrido de alpha: cómo cambian los errores cuando las clases se superponen
    titulo("BARRIDO DE ALPHA (p0 = 0.5, datos generados)")
    barrido = []
    for a in ALPHAS_BARRIDO:
        df_a, param_a = generar_datos(N_GENERADO, P0, a, SEMILLA)
        res_a = experimento(f"alpha = {a}", df_a, param_a, f"alpha_{a}", mostrar=False)[0]
        barrido.append(res_a)
        print(f"alpha = {a}: Bayes teórico = {100 * res_a['Error_Bayes_teorico']:6.2f} % | "
              f"Bayes prueba = {100 * res_a['Error_Bayes_prueba']:6.2f} % | "
              f"E_in = {100 * res_a['E_in']:6.2f} % | E_out = {100 * res_a['E_out']:6.2f} %")
    tabla_b = pd.DataFrame(barrido)
    tabla_b.to_csv(SALIDA / "barrido_alpha.csv", index=False, encoding="utf-8-sig")
    graficar_barrido(tabla_b, SALIDA / "barrido_alpha.png")
    print(f"\nGráficos y tablas guardados en: {SALIDA}")


if __name__ == "__main__":
    main()
