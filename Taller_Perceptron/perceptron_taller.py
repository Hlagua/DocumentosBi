"""
Taller: Desarrollo y entrenamiento de un perceptrón para clasificación binaria
Asignatura: Inteligencia de Negocios - Carrera de Software, 6to "A"
Autores: Lagua Flores Henry Daniel / Cobos Taco Alison Marcela

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

Ejecución (terminal de Visual Studio Code):  python perceptron_taller.py
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
COLUMNAS = ["Caracteristica_1", "Caracteristica_2", "Caracteristica_3"]
COLORES = {"Hombre": "#1f77b4", "Mujer": "#d62728"}

plt.rcParams.update({"font.family": "Times New Roman", "font.size": 12,
                     "axes.titlesize": 13, "savefig.dpi": 200})


def titulo(texto):
    print("\n" + "=" * 64)
    print(texto)
    print("=" * 64)


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
    X = df[COLUMNAS].to_numpy()
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
    ajustes = []
    epoca_convergencia = None
    for epoca in range(1, epocas + 1):       # paso 3: repetir
        errores = 0
        for i, (xi, yi) in enumerate(zip(X, y)):   # paso 4: para cada ejemplo
            if yi * f(w, xi) <= 0:           # paso 5: ¿error?
                antes = w.copy()
                w = w + yi * xi              # paso 6: ajustar los pesos
                errores += 1
                ajustes.append({"Epoca": epoca, "Ejemplo": i + 1, "x": xi[1:],
                                "y": yi, "w_antes": antes, "w_despues": w.copy()})
        exactitud = np.mean(escalon(X @ w) == y)
        historial.append({"Epoca": epoca, "Errores": errores,
                          "Exactitud_entrenamiento": exactitud,
                          "w0": w[0], "w1": w[1], "w2": w[2], "w3": w[3]})
        if errores == 0 and epoca_convergencia is None:
            epoca_convergencia = epoca
    return w, pd.DataFrame(historial), ajustes, epoca_convergencia


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


# ----------------------------------------------------------------------------
# Gráficos
# ----------------------------------------------------------------------------
def graficar_distribuciones(df, ruta):
    fig, ejes = plt.subplots(1, 3, figsize=(9, 3.3), sharey=True)
    for ax, col in zip(ejes, COLUMNAS):
        for clase, color in COLORES.items():
            ax.hist(df.loc[df["Clase"] == clase, col], bins=40, range=(-1, 1),
                    alpha=0.6, color=color, label=clase)
        ax.set_title(col.replace("_", " "))
        ax.set_xlabel("Valor")
        ax.grid(alpha=0.3)
    ejes[0].set_ylabel("Frecuencia")
    ejes[0].legend()
    fig.tight_layout()
    fig.savefig(ruta)
    plt.close(fig)


def graficar_3d(df, w, ruta):
    fig = plt.figure(figsize=(6.5, 5.2))
    ax = fig.add_subplot(projection="3d")
    muestra = df.sample(1500, random_state=SEMILLA)
    for clase, color in COLORES.items():
        sub = muestra[muestra["Clase"] == clase]
        ax.scatter(sub[COLUMNAS[0]], sub[COLUMNAS[1]], sub[COLUMNAS[2]], s=5,
                   alpha=0.5, color=color, label=clase)
    g1, g2 = np.meshgrid(np.linspace(-1, 1, 120), np.linspace(-1, 1, 120))
    g3 = -(w[0] + w[1] * g1 + w[2] * g2) / w[3]
    g3 = np.where(np.abs(g3) <= 1, g3, np.nan)
    ax.plot_surface(g1, g2, g3, color="gray", alpha=0.35, linewidth=0)
    for eje in (ax.set_xticks, ax.set_yticks, ax.set_zticks):
        eje([-1, -0.5, 0, 0.5, 1])
    ax.set_xlabel("x1")
    ax.set_ylabel("x2")
    ax.set_zlabel("x3")
    ax.set_zlim(-1, 1)
    ax.view_init(elev=18, azim=-60)
    ax.legend(loc="upper left")
    fig.tight_layout()
    fig.savefig(ruta)
    plt.close(fig)


def graficar_convergencia(hist, ruta):
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9, 3.4))
    a1.bar(hist["Epoca"], hist["Errores"], color="#1f77b4")
    a1.set_xlim(0.3, 20.7)
    a1.set_xticks(range(1, 21))
    a1.set_xlabel("Época")
    a1.set_ylabel("Ejemplos mal clasificados")
    a1.set_title("Errores por época (épocas 1 a 20)")
    a1.grid(alpha=0.3, axis="y")
    for nombre, estilo in [("w0", "--"), ("w1", "-"), ("w2", "-"), ("w3", "-")]:
        a2.plot(hist["Epoca"], hist[nombre], estilo, lw=2, label=nombre)
    a2.set_xlabel("Época")
    a2.set_ylabel("Valor del peso")
    a2.set_title(f"Evolución de los pesos ({len(hist)} épocas)")
    a2.legend(ncol=4, loc="upper center", bbox_to_anchor=(0.5, -0.2), frameon=False)
    a2.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(ruta)
    plt.close(fig)


def graficar_matrices(matrices, ruta):
    fig, ejes = plt.subplots(1, 2, figsize=(8.6, 3.8))
    for ax, (nombre, mc) in zip(ejes, matrices.items()):
        valores = mc.to_numpy()
        ax.imshow(valores, cmap="Blues")
        for i in range(2):
            for j in range(2):
                ax.text(j, i, str(valores[i, j]), ha="center", va="center",
                        fontsize=16,
                        color="white" if valores[i, j] > valores.max() / 2 else "black")
        ax.set_xticks([0, 1], mc.columns)
        ax.set_yticks([0, 1], mc.index)
        ax.set_title(f"Conjunto de {nombre.lower()} (n = {valores.sum()})")
    fig.tight_layout()
    fig.savefig(ruta)
    plt.close(fig)


def graficar_proyecciones(df, w, ruta):
    """Proyecciones 2D con la frontera; la variable no graficada se fija en su media."""
    pares = [(0, 1), (0, 2), (1, 2)]
    medias = df[COLUMNAS].mean().to_numpy()
    fig, ejes = plt.subplots(1, 3, figsize=(9.6, 3.7))
    for ax, (a, b) in zip(ejes, pares):
        c = 3 - a - b
        for clase, color in COLORES.items():
            sub = df[df["Clase"] == clase]
            ax.scatter(sub[COLUMNAS[a]], sub[COLUMNAS[b]], s=4, alpha=0.35,
                       color=color, label=clase)
        xa = np.linspace(-1, 1, 50)
        xb = -(w[0] + w[a + 1] * xa + w[c + 1] * medias[c]) / w[b + 1]
        ax.plot(xa, xb, color="black", lw=2, label="Frontera")
        ax.set_xlim(-1.05, 1.05)
        ax.set_ylim(-1.05, 1.05)
        ax.set_xlabel(f"x{a + 1}")
        ax.set_ylabel(f"x{b + 1}")
        ax.set_title(f"Plano x{a + 1}–x{b + 1}")
        ax.grid(alpha=0.3)
    manejadores, etiquetas = ejes[0].get_legend_handles_labels()
    fig.legend(manejadores, etiquetas, loc="lower center", ncol=3, markerscale=3)
    fig.tight_layout(rect=(0, 0.08, 1, 1))
    fig.savefig(ruta)
    plt.close(fig)


def main():
    titulo("1. CARGA Y PREPARACIÓN DE LOS DATOS")
    df = cargar_datos(ARCHIVO)
    print(f"Archivo: {ARCHIVO.name}")
    print(f"Registros: {len(df)} | Columnas: {df.shape[1] - 1} | "
          f"Nulos: {int(df.isna().sum().sum())} | Duplicados: {int(df.duplicated().sum())}")
    print("Codificación: Hombre = 1, Mujer = -1")
    print(df.groupby("Clase")[COLUMNAS].mean().round(3).to_string())

    train, test = dividir_estratificado(df, PROPORCION_TEST, SEMILLA)
    X_train, y_train = matriz_aumentada(train), train["y"].to_numpy()
    X_test, y_test = matriz_aumentada(test), test["y"].to_numpy()
    print(f"Entrenamiento: {len(train)} registros | Prueba: {len(test)} registros")

    titulo("2. ENTRENAMIENTO (w = 0, sesgo = 0, 200 épocas)")
    w, hist, ajustes, ep_conv = entrenar_perceptron(X_train, y_train, EPOCAS)
    for a in ajustes:
        print(f"Época {a['Epoca']}, ejemplo {a['Ejemplo']}: x = {np.round(a['x'], 3)}, "
              f"y = {a['y']:+d}")
        print(f"   w antes = {np.round(a['w_antes'], 3)} -> w después = "
              f"{np.round(a['w_despues'], 3)}")
    print(hist[["Epoca", "Errores", "Exactitud_entrenamiento"]].head(5)
          .to_string(index=False))
    print(f"Épocas ejecutadas: {EPOCAS} | Convergencia (0 errores): época {ep_conv}")
    print(f"Total de actualizaciones de pesos: {len(ajustes)}")

    titulo("3. PESOS FINALES")
    for nombre, valor in zip(["w0 (sesgo)", "w1", "w2", "w3"], w):
        print(f"  {nombre:<11}= {valor:.4f}")
    print(f"Frontera: {w[0]:.3f} + {w[1]:.3f}*x1 + {w[2]:.3f}*x2 + {w[3]:.3f}*x3 = 0")

    titulo("4. EVALUACIÓN")
    resultados, matrices = [], {}
    for nombre, X, y in [("Entrenamiento", X_train, y_train),
                         ("Prueba", X_test, y_test)]:
        y_pred = escalon(X @ w)
        mc = matriz_confusion(y, y_pred)
        matrices[nombre] = mc
        resultados.append({"Conjunto": nombre, "n": len(y), **metricas(mc)})
        print(f"Matriz de confusión - {nombre}")
        print(mc.to_string())
        mc.to_csv(SALIDA / f"matriz_confusion_{nombre.lower()}.csv",
                  encoding="utf-8-sig")
    tabla = pd.DataFrame(resultados)
    print("\nTabla de resultados")
    print(tabla.round(4).to_string(index=False))

    margen = (y_train * (X_train @ w)) / np.linalg.norm(w[1:])
    print(f"Distancia mínima de un punto a la frontera: {margen.min():.4f}")

    titulo("5. EJEMPLOS DE PREDICCIÓN (conjunto de prueba)")
    muestra = test.groupby("Clase").head(3)
    z = matriz_aumentada(muestra) @ w
    salida = muestra[COLUMNAS + ["Clase"]].copy()
    salida["f(x)"] = z.round(3)
    salida["Predicción"] = np.where(escalon(z) == 1, "Hombre", "Mujer")
    salida.columns = ["x1", "x2", "x3", "Clase real", "f(x)", "Predicción"]
    print(salida.to_string(index=False))

    tabla.to_csv(SALIDA / "tabla_resultados.csv", index=False, encoding="utf-8-sig")
    hist.to_csv(SALIDA / "historial_entrenamiento.csv", index=False,
                encoding="utf-8-sig")
    salida.to_csv(SALIDA / "ejemplos_prediccion.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame({"Parametro": ["w0", "w1", "w2", "w3"], "Valor": w}).to_csv(
        SALIDA / "pesos_finales.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame([{"Epoca": a["Epoca"], "Ejemplo": a["Ejemplo"], "y": a["y"],
                   **{f"x{k + 1}": v for k, v in enumerate(a["x"])},
                   **{f"w{k}_despues": v for k, v in enumerate(a["w_despues"])}}
                  for a in ajustes]).to_csv(SALIDA / "ajustes_pesos.csv", index=False,
                                            encoding="utf-8-sig")

    graficar_distribuciones(df, SALIDA / "distribucion_caracteristicas.png")
    graficar_3d(df, w, SALIDA / "frontera_3d.png")
    graficar_convergencia(hist, SALIDA / "convergencia.png")
    graficar_matrices(matrices, SALIDA / "matrices_confusion.png")
    graficar_proyecciones(df, w, SALIDA / "frontera_proyecciones.png")
    print(f"\nGráficos y tablas guardados en: {SALIDA}")


if __name__ == "__main__":
    main()
