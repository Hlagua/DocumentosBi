"""
==============================================================================
UNIVERSIDAD TÉCNICA DE AMBATO - Inteligencia de Negocios (Proyecto final)
AUTORES: Alison Marcela Cobos Taco / Henry Daniel Lagua Flores
==============================================================================
ARCHIVO: proyecto_final/02_entrenar_redes.py

Fase 2: entrena una red neuronal multiclase (salida softmax) por sistema con
Keras/TensorFlow, usando los datasets de la fase 1.

Proceso por sistema (S1, S2, S3):
  1. Escalado z-score ajustado SOLO con entrenamiento.
  2. Reducción de dimensionalidad: se compara usar todas las X frente a PCA
     (componentes que explican el 95 % de la varianza, ajustado con
     entrenamiento). Se queda la opción que gane en validación.
  3. Búsqueda de arquitectura en validación: número de capas ocultas,
     neuronas, activación, dropout y regularización L1.
     Entrenamiento con entropía cruzada categórica, optimizador Adam,
     lotes de 15 y parada temprana (early stopping) sobre la pérdida de
     validación. Las clases desbalanceadas se compensan con pesos por clase
     (por defecto) o, con --balanceo sobremuestreo, repitiendo casos de las
     clases pequeñas SOLO en entrenamiento hasta que todas queden iguales.
  4. Modelos de referencia con la misma partición:
       - clasificador aleatorio  (error teórico (M-1)/M)
       - clase mayoritaria
       - softmax lineal (red sin capas ocultas)
  5. Validación cruzada de 5 pliegues de la arquitectura elegida sobre
     entrenamiento + validación: el error del modelo es el promedio de los
     errores de los pliegues.
  6. Evaluación final UNA sola vez en prueba: exactitud, exactitud
     balanceada, matriz de confusión, precisión, sensibilidad y F1 por clase,
     E_in frente a E_out.
  7. Se guardan en `proyecto_final/modelos/`:
       S#_red.keras            modelo entrenado
       S#_preprocesamiento.json orden de X, medias, desviaciones y PCA
       S#_metricas.json         curvas, métricas, comparación y arquitectura
==============================================================================
"""

import json
import os
import sys
import time
from pathlib import Path

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")
os.environ.setdefault("TF_ENABLE_ONEDNN_OPTS", "0")

import numpy as np
import pandas as pd
import keras
from keras import layers, regularizers
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    confusion_matrix,
    precision_recall_fscore_support,
)
from sklearn.model_selection import StratifiedGroupKFold

DIR = Path(__file__).resolve().parent
DATOS = DIR / "datos"
MODELOS = DIR / "modelos"          # se puede cambiar con --salida
BALANCEO = "pesos"                 # "pesos" (por defecto) o "sobremuestreo" (--balanceo)

SEMILLA = 42
LOTE = 15                 # tamaño de lote visto en clase
EPOCAS_MAX = 300
PACIENCIA = 20
VARIANZA_PCA = 0.95

SISTEMAS = {
    "S1": "S1_transacciones.csv",
    "S2": "S2_ordenes.csv",
    "S3": "S3_saldo_mensual.csv",
    "S4": "S4_prestamos.csv",
    "S5": "S5_movimiento_mensual.csv",
}

# Arquitecturas candidatas: (capas ocultas, activación, dropout, L1)
# Por indicación del docente las capas ocultas no usan ReLU: tangente hiperbólica
# (centrada en cero, tanh(z) = 2·σ(2z) − 1) y una candidata con sigmoide logística.
CANDIDATAS = [
    ([32], "tanh", 0.0, 0.0),
    ([64, 32], "tanh", 0.2, 0.0),
    ([64, 32], "tanh", 0.2, 1e-5),
    ([128, 64, 32], "tanh", 0.2, 1e-5),
    ([64, 32], "sigmoid", 0.2, 1e-5),
]


# ----------------------------------------------------------------------------
# Preprocesamiento (se guarda en JSON para que el aplicativo lo repita igual)
# ----------------------------------------------------------------------------
class Preprocesador:
    def __init__(self, columnas, usar_pca):
        self.columnas = columnas
        self.usar_pca = usar_pca

    def ajustar(self, X):
        self.media = X.mean(axis=0)
        self.desv = X.std(axis=0)
        self.desv[self.desv == 0] = 1.0
        Z = (X - self.media) / self.desv
        if self.usar_pca:
            # PCA por descomposición en valores singulares de la matriz centrada
            _, s, vt = np.linalg.svd(Z, full_matrices=False)
            var = s**2 / (len(Z) - 1)
            self.varianza_explicada = var / var.sum()
            acumulada = np.cumsum(self.varianza_explicada)
            k = int(np.searchsorted(acumulada, VARIANZA_PCA) + 1)
            self.componentes = vt[:k]
        return self

    def transformar(self, X):
        Z = (X - self.media) / self.desv
        return Z @ self.componentes.T if self.usar_pca else Z

    @property
    def dimension_salida(self):
        return self.componentes.shape[0] if self.usar_pca else len(self.columnas)

    def a_dict(self):
        d = {
            "orden_X": self.columnas,
            "dimension_entrada": len(self.columnas),
            "media": self.media.tolist(),
            "desviacion": self.desv.tolist(),
            "usa_pca": self.usar_pca,
            "dimension_red": int(self.dimension_salida),
        }
        if self.usar_pca:
            d["pca_componentes"] = self.componentes.tolist()
            d["pca_varianza_explicada"] = self.varianza_explicada.tolist()
        return d


# ----------------------------------------------------------------------------
# Red neuronal
# ----------------------------------------------------------------------------
def construir_red(dim_entrada, n_clases, ocultas, activacion, dropout, l1):
    entrada = keras.Input(shape=(dim_entrada,), name="X")
    h = entrada
    for i, n in enumerate(ocultas, start=1):
        h = layers.Dense(
            n,
            activation=activacion,
            kernel_initializer=keras.initializers.GlorotUniform(seed=SEMILLA + i),
            kernel_regularizer=regularizers.L1(l1) if l1 else None,
            name=f"oculta_{i}",
        )(h)
        if dropout:
            h = layers.Dropout(dropout, seed=SEMILLA + i, name=f"dropout_{i}")(h)
    salida = layers.Dense(n_clases, activation="softmax", name="softmax")(h)
    red = keras.Model(entrada, salida)
    red.compile(
        optimizer=keras.optimizers.Adam(learning_rate=1e-3),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )
    return red


def pesos_por_clase(y):
    clases, conteo = np.unique(y, return_counts=True)
    return {int(c): float(len(y) / (len(clases) * n)) for c, n in zip(clases, conteo)}


def balancear(X, y):
    """
    Prepara el conjunto de ENTRENAMIENTO según la estrategia elegida:
      * "pesos": deja los datos como están y devuelve pesos por clase.
      * "sobremuestreo": repite al azar casos de las clases pequeñas hasta que
        todas tengan tantos casos como la mayor (clases 50/50 o 1/M cada una).
        Solo se aplica al entrenamiento; validación y prueba conservan la
        proporción real.
    """
    if BALANCEO != "sobremuestreo":
        return X, y, pesos_por_clase(y)
    rng = np.random.default_rng(SEMILLA)
    clases, conteo = np.unique(y, return_counts=True)
    objetivo = conteo.max()
    indices = []
    for c, n in zip(clases, conteo):
        idx = np.flatnonzero(y == c)
        extra = rng.choice(idx, size=objetivo - n, replace=True) if n < objetivo else np.array([], dtype=int)
        indices.append(np.concatenate([idx, extra]))
    indices = rng.permutation(np.concatenate(indices))
    return X[indices], y[indices], None


def entrenar(red, Xtr, ytr, Xva, yva, pesos):
    parada = keras.callbacks.EarlyStopping(
        monitor="val_loss", patience=PACIENCIA, restore_best_weights=True
    )
    hist = red.fit(
        Xtr, ytr,
        validation_data=(Xva, yva),
        epochs=EPOCAS_MAX,
        batch_size=LOTE,
        class_weight=pesos,
        callbacks=[parada],
        verbose=0,
        shuffle=True,
    )
    return {k: [round(float(v), 5) for v in vals] for k, vals in hist.history.items()}


def predecir(red, X):
    return np.argmax(red.predict(X, verbose=0, batch_size=1024), axis=1)


def resumen_arquitectura(red):
    capas = []
    for capa in red.layers:
        if isinstance(capa, layers.Dense):
            W, b = capa.get_weights()
            capas.append({
                "nombre": capa.name,
                "neuronas": int(W.shape[1]),
                "activacion": capa.get_config()["activation"],
                "forma_W": list(W.shape),
                "forma_b": list(b.shape),
                "parametros": int(W.size + b.size),
            })
    return {"capas": capas, "parametros_totales": int(red.count_params())}


def metricas(y, p, nombres):
    prec, rec, f1, sop = precision_recall_fscore_support(y, p, labels=list(range(len(nombres))), zero_division=0)
    return {
        "exactitud": round(float(accuracy_score(y, p)), 4),
        "exactitud_balanceada": round(float(balanced_accuracy_score(y, p)), 4),
        "error": round(float(1 - accuracy_score(y, p)), 4),
        "matriz_confusion": confusion_matrix(y, p, labels=list(range(len(nombres)))).tolist(),
        "por_clase": {
            nombres[i]: {"precision": round(float(prec[i]), 4), "sensibilidad": round(float(rec[i]), 4),
                         "f1": round(float(f1[i]), 4), "soporte": int(sop[i])}
            for i in range(len(nombres))
        },
        "f1_macro": round(float(np.mean(f1)), 4),
    }


# ----------------------------------------------------------------------------
# Proceso por sistema
# ----------------------------------------------------------------------------
def procesar(sistema, archivo, diccionario):
    t0 = time.time()
    info = diccionario[sistema]
    columnas = info["orden_X"]
    nombres = [info["clases"][str(i)] for i in range(len(info["clases"]))]
    n_clases = len(nombres)
    df = pd.read_csv(DATOS / archivo)
    part = {p: df[df["particion"] == p] for p in ["entrenamiento", "validacion", "prueba"]}
    X = {p: part[p][columnas].to_numpy(float) for p in part}
    y = {p: part[p]["clase"].to_numpy(int) for p in part}
    Xbal, ybal, pesos = balancear(X["entrenamiento"], y["entrenamiento"])
    conteo_bal = {int(c): int(n) for c, n in zip(*np.unique(ybal, return_counts=True))}
    print(f"\n{'=' * 78}\n{sistema}: {info['titulo']} | X = {len(columnas)} | clases = {n_clases} | "
          f"entrenamiento/validación/prueba = {len(y['entrenamiento'])}/{len(y['validacion'])}/{len(y['prueba'])}"
          f"\n  Balanceo: {BALANCEO} | entrenamiento por clase {conteo_bal}")

    # --- búsqueda: reducción de dimensión x arquitectura (decide la validación) ---
    busqueda = []
    mejor = None
    for usar_pca in (False, True):
        pre = Preprocesador(columnas, usar_pca).ajustar(X["entrenamiento"])
        Ztr, Zva = pre.transformar(X["entrenamiento"]), pre.transformar(X["validacion"])
        for ocultas, act, drop, l1 in CANDIDATAS:
            keras.utils.set_random_seed(SEMILLA)
            red = construir_red(pre.dimension_salida, n_clases, ocultas, act, drop, l1)
            hist = entrenar(red, pre.transformar(Xbal), ybal, Zva, y["validacion"], pesos)
            pva = predecir(red, Zva)
            fila = {
                "pca": usar_pca, "dimension_red": int(pre.dimension_salida), "ocultas": ocultas,
                "activacion": act, "dropout": drop, "l1": l1, "epocas": len(hist["loss"]),
                "exactitud_val": round(float(accuracy_score(y["validacion"], pva)), 4),
                "exactitud_balanceada_val": round(float(balanced_accuracy_score(y["validacion"], pva)), 4),
            }
            busqueda.append(fila)
            print(f"  PCA={str(usar_pca):5} d={fila['dimension_red']:2} {str(ocultas):14} {act:4} "
                  f"drop={drop} L1={l1:g} | épocas {fila['epocas']:3} | val acc {fila['exactitud_val']:.3f} "
                  f"bal {fila['exactitud_balanceada_val']:.3f}", flush=True)
            criterio = fila["exactitud_balanceada_val"]
            if mejor is None or criterio > mejor[0]:
                mejor = (criterio, fila, pre, red, hist)

    _, elegida, pre, red, hist = mejor
    Ztr, Zva, Zte = (pre.transformar(X[p]) for p in ["entrenamiento", "validacion", "prueba"])

    # --- softmax lineal (sin capas ocultas) con el mismo preprocesamiento ---
    keras.utils.set_random_seed(SEMILLA)
    lineal = construir_red(pre.dimension_salida, n_clases, [], "linear", 0.0, 0.0)
    entrenar(lineal, pre.transformar(Xbal), ybal, Zva, y["validacion"], pesos)

    # --- validación cruzada de 5 pliegues sobre entrenamiento + validación ---
    Xcv = np.vstack([X["entrenamiento"], X["validacion"]])
    ycv = np.concatenate([y["entrenamiento"], y["validacion"]])
    # Pliegues agrupados por cuenta: ninguna cuenta queda a la vez en el entrenamiento y en la
    # validación de un mismo pliegue (igual que la partición principal).
    gcv = np.concatenate([part["entrenamiento"]["id_cuenta"].to_numpy(), part["validacion"]["id_cuenta"].to_numpy()])
    errores = []
    pliegues = StratifiedGroupKFold(5, shuffle=True, random_state=SEMILLA).split(Xcv, ycv, gcv)
    for k, (itr, iva) in enumerate(pliegues, 1):
        pre_k = Preprocesador(columnas, elegida["pca"]).ajustar(Xcv[itr])
        keras.utils.set_random_seed(SEMILLA)
        red_k = construir_red(pre_k.dimension_salida, n_clases, elegida["ocultas"], elegida["activacion"],
                              elegida["dropout"], elegida["l1"])
        Xk, yk, pesos_k = balancear(Xcv[itr], ycv[itr])
        entrenar(red_k, pre_k.transformar(Xk), yk, pre_k.transformar(Xcv[iva]), ycv[iva], pesos_k)
        err = 1 - accuracy_score(ycv[iva], predecir(red_k, pre_k.transformar(Xcv[iva])))
        errores.append(round(float(err), 4))
        print(f"  pliegue {k}: error {err:.4f}", flush=True)

    # --- evaluación final en prueba (una sola vez) ---
    m_tr = metricas(y["entrenamiento"], predecir(red, Ztr), nombres)
    m_va = metricas(y["validacion"], predecir(red, Zva), nombres)
    m_te = metricas(y["prueba"], predecir(red, Zte), nombres)
    if n_clases == 2:
        from sklearn.metrics import roc_auc_score
        m_te["auc"] = round(float(roc_auc_score(y["prueba"], red.predict(Zte, verbose=0)[:, 1])), 4)
    m_lin = metricas(y["prueba"], predecir(lineal, Zte), nombres)
    mayoritaria = int(np.bincount(y["entrenamiento"]).argmax())
    m_may = metricas(y["prueba"], np.full_like(y["prueba"], mayoritaria), nombres)

    resultado = {
        "sistema": sistema,
        "titulo": info["titulo"],
        "clases": nombres,
        "criterio_seleccion": "mayor exactitud balanceada en validación",
        "hiperparametros_fijos": {"lote": LOTE, "epocas_max": EPOCAS_MAX, "paciencia": PACIENCIA,
                                  "optimizador": "Adam (lr = 0.001)", "perdida": "entropía cruzada categórica",
                                  "inicializacion": "Glorot uniforme", "pesos_por_clase": pesos},
        "balanceo": {
            "estrategia": BALANCEO,
            "descripcion": ("sobremuestreo aleatorio solo en entrenamiento hasta igualar las clases"
                            if BALANCEO == "sobremuestreo" else "datos reales con pesos por clase en la pérdida"),
            "entrenamiento_original_por_clase": {int(c): int(n) for c, n in zip(*np.unique(y["entrenamiento"], return_counts=True))},
            "entrenamiento_usado_por_clase": conteo_bal,
        },
        "busqueda": busqueda,
        "elegida": elegida,
        "arquitectura": resumen_arquitectura(red),
        "historial": hist,
        "entrenamiento": m_tr,
        "validacion": m_va,
        "prueba": m_te,
        "E_in": m_tr["error"],
        "E_out": m_te["error"],
        "diferencia_E_out_E_in": round(m_te["error"] - m_tr["error"], 4),
        "validacion_cruzada_5": {"errores": errores, "error_promedio": round(float(np.mean(errores)), 4),
                                 "desviacion": round(float(np.std(errores)), 4)},
        "comparacion_prueba": {
            "red_neuronal": {"exactitud": m_te["exactitud"], "exactitud_balanceada": m_te["exactitud_balanceada"]},
            "softmax_lineal": {"exactitud": m_lin["exactitud"], "exactitud_balanceada": m_lin["exactitud_balanceada"]},
            "clase_mayoritaria": {"exactitud": m_may["exactitud"], "exactitud_balanceada": m_may["exactitud_balanceada"]},
            "aleatorio": {"exactitud": round(1 / n_clases, 4), "exactitud_balanceada": round(1 / n_clases, 4)},
        },
        "segundos": round(time.time() - t0, 1),
    }
    red.save(MODELOS / f"{sistema}_red.keras")
    with open(MODELOS / f"{sistema}_preprocesamiento.json", "w", encoding="utf-8") as f:
        json.dump({**pre.a_dict(), "clases": nombres, "sistema": sistema}, f, ensure_ascii=False, indent=2)
    with open(MODELOS / f"{sistema}_metricas.json", "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)

    c = resultado["comparacion_prueba"]
    print(f"  ELEGIDA: {elegida['ocultas']} {elegida['activacion']} PCA={elegida['pca']} | "
          f"E_in {resultado['E_in']:.3f}  E_out {resultado['E_out']:.3f}  "
          f"(dif {resultado['diferencia_E_out_E_in']:+.3f}) | CV-5 error {resultado['validacion_cruzada_5']['error_promedio']:.3f}")
    print(f"  Prueba -> red {c['red_neuronal']['exactitud']:.3f} | lineal {c['softmax_lineal']['exactitud']:.3f} | "
          f"mayoritaria {c['clase_mayoritaria']['exactitud']:.3f} | aleatorio {c['aleatorio']['exactitud']:.3f} "
          f"({resultado['segundos']} s)", flush=True)
    return resultado


def entrenar_sistema(sistema, balanceo="pesos", salida="modelos"):
    """
    Entrena un solo sistema con el procedimiento común. Lo usan entrenar_S1.py,
    entrenar_S2.py y entrenar_S4.py, uno por cada sistema que se presenta.
    """
    global BALANCEO, MODELOS
    sys.stdout.reconfigure(encoding="utf-8")
    BALANCEO = balanceo
    MODELOS = DIR / salida
    MODELOS.mkdir(parents=True, exist_ok=True)
    print(f"TensorFlow/Keras {keras.__version__} | lote {LOTE} | semilla {SEMILLA} | "
          f"balanceo {BALANCEO} | salida {MODELOS.name}/")
    with open(DATOS / "diccionario_caracteristicas.json", encoding="utf-8") as f:
        diccionario = json.load(f)
    return procesar(sistema, SISTEMAS[sistema], diccionario)


def main():
    """
    Uso:
      python 02_entrenar_redes.py [S1 S2 S3 S4 S5] [--balanceo pesos|sobremuestreo] [--salida carpeta]
    Por defecto entrena todos los sistemas con pesos por clase y guarda en modelos/.
    Para los sistemas que se presentan hay un archivo por sistema: entrenar_S1.py, entrenar_S2.py
    y entrenar_S4.py. S3 y S5 se descartaron y quedan aquí solo como respaldo.
    """
    global BALANCEO, MODELOS
    import argparse

    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("sistemas", nargs="*", choices=list(SISTEMAS) + [], default=list(SISTEMAS))
    ap.add_argument("--balanceo", choices=["pesos", "sobremuestreo"], default="pesos")
    ap.add_argument("--salida", default="modelos", help="carpeta dentro de proyecto_final/")
    args = ap.parse_args()
    BALANCEO = args.balanceo
    MODELOS = DIR / args.salida
    MODELOS.mkdir(exist_ok=True)
    print(f"TensorFlow/Keras {keras.__version__} | lote {LOTE} | semilla {SEMILLA} | "
          f"balanceo {BALANCEO} | salida {MODELOS.name}/")
    with open(DATOS / "diccionario_caracteristicas.json", encoding="utf-8") as f:
        diccionario = json.load(f)
    elegidos = args.sistemas or list(SISTEMAS)
    for s in elegidos:
        procesar(s, SISTEMAS[s], diccionario)


if __name__ == "__main__":
    main()
