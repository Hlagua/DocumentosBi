"""
Taller: Desarrollo y entrenamiento de un perceptrón para clasificación binaria
Asignatura: Inteligencia de Negocios

Implementación desde cero (sin scikit-learn) del seudocódigo de la diapositiva 4
de ANN.pdf:

    Input : (x_1, y_1), ..., (x_n, y_n)
    Output: perceptrón definido por (w_0, w_1, ..., w_d)
    Begin
      2. Inicializar w_j = 0  para todo j en {0, ..., d}
      3. Repetir hasta converger
      4.   Para cada ejemplo x_i, i en {1, ..., n}
      5.     si y_i * f(x_i) <= 0          # ¿error?
      6.       w_j := w_j + y_i * x_ij      # ajustar los pesos
    End

Donde f(x) = w_0 * 1 + w_1*x_1 + w_2*x_2 + w_3*x_3 y la salida es la función
escalón: +1 (Hombre) si f(x) >= 0, -1 (Mujer) en otro caso.
"""

from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

CARPETA = Path(__file__).resolve().parent
ARCHIVO = CARPETA / "dataset_Perceptron_5000_continuo_menos1_a_1.csv"
SALIDA = CARPETA / "resultados"
SALIDA.mkdir(exist_ok=True)

EPOCAS = 200          # al menos 200 épocas (instrucción 6)
PROPORCION_TEST = 0.2
SEMILLA = 42


# ----------------------------------------------------------------------------
# Actividad 2. Preparar los datos
# ----------------------------------------------------------------------------
def cargar_datos(ruta):
    df = pd.read_csv(ruta, encoding="utf-8-sig")
    # Codificación de la clase: Hombre = 1, Mujer = -1 (instrucción 3)
    df["y"] = df["Clase"].map({"Hombre": 1, "Mujer": -1})
    return df


def dividir_estratificado(df, proporcion_test, semilla):
    """Separa entrenamiento/prueba manteniendo el 50/50 de cada clase."""
    rng = np.random.default_rng(semilla)
    idx_test = []
    for _, grupo in df.groupby("y"):
        idx = grupo.index.to_numpy().copy()
        rng.shuffle(idx)
        idx_test.extend(idx[: int(len(idx) * proporcion_test)])
    test = df.loc[sorted(idx_test)]
    train = df.drop(index=test.index)
    # Barajar el entrenamiento para que las clases no lleguen ordenadas
    train = train.sample(frac=1, random_state=semilla)
    return train, test


def matriz_aumentada(df):
    """Agrega la entrada constante x0 = 1 que multiplica al sesgo w0."""
    X = df[["Caracteristica_1", "Caracteristica_2", "Caracteristica_3"]].to_numpy()
    return np.hstack([np.ones((len(X), 1)), X])


# ----------------------------------------------------------------------------
# Actividad 1 y 3. Estructura y entrenamiento del perceptrón
# ----------------------------------------------------------------------------
def f(w, x):
    """Suma ponderada: w0*1 + w1*x1 + w2*x2 + w3*x3."""
    return np.dot(w, x)


def escalon(z):
    """Función de activación escalón con salidas +1 / -1."""
    return np.where(z >= 0, 1, -1)


def entrenar_perceptron(X, y, epocas):
    w = np.zeros(X.shape[1])                 # paso 2: pesos y sesgo en 0
    historial = []
    epoca_convergencia = None
    for epoca in range(1, epocas + 1):       # paso 3: repetir
        errores = 0
        for xi, yi in zip(X, y):             # paso 4: para cada ejemplo
            if yi * f(w, xi) <= 0:           # paso 5: ¿error?
                w = w + yi * xi              # paso 6: ajustar los pesos
                errores += 1
        exactitud = np.mean(escalon(X @ w) == y)
        historial.append({"Epoca": epoca, "Errores": errores,
                          "Exactitud_entrenamiento": exactitud,
                          "w0": w[0], "w1": w[1], "w2": w[2], "w3": w[3]})
        if errores == 0 and epoca_convergencia is None:
            epoca_convergencia = epoca
    return w, pd.DataFrame(historial), epoca_convergencia


# ----------------------------------------------------------------------------
# Actividad 4. Evaluar el clasificador
# ----------------------------------------------------------------------------
def matriz_confusion(y_real, y_pred):
    vp = int(np.sum((y_real == 1) & (y_pred == 1)))
    fn = int(np.sum((y_real == 1) & (y_pred == -1)))
    fp = int(np.sum((y_real == -1) & (y_pred == 1)))
    vn = int(np.sum((y_real == -1) & (y_pred == -1)))
    return pd.DataFrame([[vp, fn], [fp, vn]],
                        index=["Real Hombre (1)", "Real Mujer (-1)"],
                        columns=["Pred. Hombre (1)", "Pred. Mujer (-1)"])


def metricas(mc):
    vp, fn = mc.iloc[0]
    fp, vn = mc.iloc[1]
    total = vp + fn + fp + vn
    precision = vp / (vp + fp) if vp + fp else 0.0
    sensibilidad = vp / (vp + fn) if vp + fn else 0.0
    especificidad = vn / (vn + fp) if vn + fp else 0.0
    f1 = (2 * precision * sensibilidad / (precision + sensibilidad)
          if precision + sensibilidad else 0.0)
    return {"Exactitud": (vp + vn) / total, "Precision": precision,
            "Sensibilidad": sensibilidad, "Especificidad": especificidad,
            "F1": f1}


def graficar_convergencia(hist, ruta):
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(hist["Epoca"], hist["Errores"], marker="o", markersize=3)
    ax.set_xlabel("Época")
    ax.set_ylabel("Ejemplos mal clasificados (actualizaciones)")
    ax.set_title("Convergencia del perceptrón")
    ax.set_xlim(0.5, 20.5)
    ax.set_xticks(range(1, 21))
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(ruta, dpi=150)
    plt.close(fig)


def graficar_matriz(mc, titulo, ruta):
    fig, ax = plt.subplots(figsize=(4.8, 4))
    ax.imshow(mc.to_numpy(), cmap="Blues")
    for i in range(2):
        for j in range(2):
            v = mc.iloc[i, j]
            ax.text(j, i, str(v), ha="center", va="center", fontsize=14,
                    color="white" if v > mc.to_numpy().max() / 2 else "black")
    ax.set_xticks([0, 1], mc.columns)
    ax.set_yticks([0, 1], mc.index)
    ax.set_title(titulo)
    fig.tight_layout()
    fig.savefig(ruta, dpi=150)
    plt.close(fig)


def graficar_frontera(df, w, ruta):
    """Proyección x1–x3 con la frontera w0 + w1x1 + w2x2 + w3x3 = 0 (x2 en su media)."""
    fig, ax = plt.subplots(figsize=(6, 5))
    for clase, color in [("Hombre", "tab:blue"), ("Mujer", "tab:red")]:
        sub = df[df["Clase"] == clase]
        ax.scatter(sub["Caracteristica_1"], sub["Caracteristica_3"], s=6,
                   alpha=0.4, color=color, label=clase)
    x1 = np.linspace(-1, 1, 50)
    x2 = df["Caracteristica_2"].mean()
    x3 = -(w[0] + w[1] * x1 + w[2] * x2) / w[3]
    ax.plot(x1, x3, color="black", lw=2, label="Frontera de decisión")
    ax.set_xlim(-1.05, 1.05)
    ax.set_ylim(-1.05, 1.05)
    ax.set_xlabel("Característica 1 (x1)")
    ax.set_ylabel("Característica 3 (x3)")
    ax.set_title("Clases y frontera del perceptrón")
    ax.legend(loc="lower right")
    fig.tight_layout()
    fig.savefig(ruta, dpi=150)
    plt.close(fig)


def main():
    df = cargar_datos(ARCHIVO)
    print("Registros:", len(df), "| Valores nulos:", int(df.isna().sum().sum()))
    print(df["Clase"].value_counts().to_string(), "\n")

    train, test = dividir_estratificado(df, PROPORCION_TEST, SEMILLA)
    X_train, y_train = matriz_aumentada(train), train["y"].to_numpy()
    X_test, y_test = matriz_aumentada(test), test["y"].to_numpy()
    print(f"Entrenamiento: {len(train)}  |  Prueba: {len(test)}\n")

    w, hist, ep_conv = entrenar_perceptron(X_train, y_train, EPOCAS)

    print("Pesos finales")
    for nombre, valor in zip(["w0 (sesgo)", "w1", "w2", "w3"], w):
        print(f"  {nombre:<11}= {valor:.4f}")
    print(f"\nÉpoca de convergencia (0 errores): {ep_conv}")
    print("Errores en las primeras épocas:",
          hist["Errores"].head(10).tolist(), "\n")

    resultados = []
    for nombre, X, y in [("Entrenamiento", X_train, y_train),
                         ("Prueba", X_test, y_test)]:
        y_pred = escalon(X @ w)
        mc = matriz_confusion(y, y_pred)
        m = metricas(mc)
        resultados.append({"Conjunto": nombre, "n": len(y), **m})
        print(f"Matriz de confusión - {nombre}")
        print(mc.to_string(), "\n")
        mc.to_csv(SALIDA / f"matriz_confusion_{nombre.lower()}.csv",
                  encoding="utf-8-sig")
        graficar_matriz(mc, f"Matriz de confusión - {nombre}",
                        SALIDA / f"matriz_confusion_{nombre.lower()}.png")

    tabla = pd.DataFrame(resultados)
    print("Tabla de resultados")
    print(tabla.round(4).to_string(index=False))

    tabla.to_csv(SALIDA / "tabla_resultados.csv", index=False, encoding="utf-8-sig")
    hist.to_csv(SALIDA / "historial_entrenamiento.csv", index=False,
                encoding="utf-8-sig")
    pd.DataFrame({"Parametro": ["w0", "w1", "w2", "w3"], "Valor": w}).to_csv(
        SALIDA / "pesos_finales.csv", index=False, encoding="utf-8-sig")
    graficar_convergencia(hist, SALIDA / "convergencia.png")
    graficar_frontera(df, w, SALIDA / "frontera_decision.png")

    # Ejemplo de uso del modelo con un registro nuevo
    nuevo = np.array([1, 0.5, 0.3, 0.6])
    print(f"\nEjemplo x=(0.5, 0.3, 0.6) -> f(x)={f(w, nuevo):.3f} -> "
          f"{'Hombre' if escalon(f(w, nuevo)) == 1 else 'Mujer'}")


if __name__ == "__main__":
    main()
