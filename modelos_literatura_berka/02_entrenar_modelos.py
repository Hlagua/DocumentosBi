"""
==============================================================================
UNIVERSIDAD TÉCNICA DE AMBATO - Inteligencia de Negocios
AUTORES: Alison Marcela Cobos Taco / Henry Daniel Lagua Flores
==============================================================================
ARCHIVO: modelos_literatura_berka/02_entrenar_modelos.py

Entrena los 5 modelos predictivos de la literatura sobre la base PKDD'99 /
Berka usando redes neuronales (Keras/TensorFlow) con las 3 capas de salida
vistas en clase:
  * M1 (Riesgo de impago):              clasificación binaria  -> SIGMOIDE
  * M2 (Propensión a tarjeta):          clasificación binaria  -> SIGMOIDE
  * M3 (Segmentación de clientes):      clasificación 4 clases -> SOFTMAX
  * M4 (Fuga / Churn silencioso):       clasificación binaria  -> SIGMOIDE
  * M5 (Pronóstico de transacciones):   regresión continua     -> LINEAL

Proceso riguroso por modelo:
  1. Escalado z-score ajustado SOLO en entrenamiento.
  2. Comparación de todas las X frente a PCA (95 % de varianza) en validación.
  3. Búsqueda de arquitectura en validación (capas ocultas, activación,
     dropout, L1) con optimizador Adam y parada temprana (EarlyStopping).
  4. Comparación contra modelos de referencia (Regresión Logística / Softmax
     lineal / Regresión Lineal sin capas ocultas + baselines ingenuos).
  5. Validación cruzada de 5 pliegues sobre entrenamiento + validación.
  6. Evaluación final UNA sola vez en prueba.

Salidas en `modelos_literatura_berka/modelos/`:
  M#_red.keras, M#_preprocesamiento.json, M#_metricas.json
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
    mean_absolute_error,
    mean_squared_error,
    precision_recall_fscore_support,
    r2_score,
    roc_auc_score,
)
from sklearn.model_selection import KFold, StratifiedKFold

DIR = Path(__file__).resolve().parent
DATOS = DIR / "datos"
MODELOS = DIR / "modelos"
MODELOS.mkdir(exist_ok=True)

SEMILLA = 42
EPOCAS_MAX = 200
PACIENCIA = 18
VARIANZA_PCA = 0.95

ARCHIVOS = {
    "M1": "M1_impago_prestamos.csv",
    "M2": "M2_propension_tarjeta.csv",
    "M3": "M3_segmentacion_clientes.csv",
    "M4": "M4_fuga_clientes.csv",
    "M5": "M5_pronostico_transacciones.csv",
}

CANDIDATAS = [
    ([32], "relu", 0.0, 0.0),
    ([64, 32], "relu", 0.2, 1e-5),
    ([64, 32], "tanh", 0.2, 1e-5),
    ([128, 64, 32], "relu", 0.2, 1e-5),
]


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


def construir_red(dim_entrada, tipo_salida, n_clases, ocultas, activacion, dropout, l1):
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

    if tipo_salida == "sigmoid":
        salida = layers.Dense(1, activation="sigmoid", name="sigmoide")(h)
        loss = "binary_crossentropy"
        mets = ["accuracy"]
    elif tipo_salida == "softmax":
        salida = layers.Dense(n_clases, activation="softmax", name="softmax")(h)
        loss = "sparse_categorical_crossentropy"
        mets = ["accuracy"]
    else:  # linear (regresión)
        salida = layers.Dense(1, activation="linear", name="lineal")(h)
        loss = "mse"
        mets = ["mae"]

    red = keras.Model(entrada, salida)
    red.compile(optimizer=keras.optimizers.Adam(learning_rate=1e-3), loss=loss, metrics=mets)
    return red


def pesos_por_clase(y):
    clases, conteo = np.unique(y, return_counts=True)
    return {int(c): float(len(y) / (len(clases) * n)) for c, n in zip(clases, conteo)}


def entrenar(red, Xtr, ytr, Xva, yva, lote, pesos=None):
    parada = keras.callbacks.EarlyStopping(
        monitor="val_loss", patience=PACIENCIA, restore_best_weights=True
    )
    hist = red.fit(
        Xtr, ytr,
        validation_data=(Xva, yva),
        epochs=EPOCAS_MAX,
        batch_size=lote,
        class_weight=pesos,
        callbacks=[parada],
        verbose=0,
        shuffle=True,
    )
    return {k: [round(float(v), 5) for v in vals] for k, vals in hist.history.items()}


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


def metricas_clasificacion(y, pred, probs, nombres, tipo_salida):
    prec, rec, f1, sop = precision_recall_fscore_support(
        y, pred, labels=list(range(len(nombres))), zero_division=0
    )
    res = {
        "exactitud": round(float(accuracy_score(y, pred)), 4),
        "exactitud_balanceada": round(float(balanced_accuracy_score(y, pred)), 4),
        "error": round(float(1 - accuracy_score(y, pred)), 4),
        "matriz_confusion": confusion_matrix(y, pred, labels=list(range(len(nombres)))).tolist(),
        "por_clase": {
            nombres[i]: {
                "precision": round(float(prec[i]), 4),
                "sensibilidad": round(float(rec[i]), 4),
                "f1": round(float(f1[i]), 4),
                "soporte": int(sop[i]),
            }
            for i in range(len(nombres))
        },
        "f1_macro": round(float(np.mean(f1)), 4),
    }
    if tipo_salida == "sigmoid":
        res["auc"] = round(float(roc_auc_score(y, probs)), 4)
    return res


def metricas_regresion(y_real, y_pred):
    mae = float(mean_absolute_error(y_real, y_pred))
    rmse = float(np.sqrt(mean_squared_error(y_real, y_pred)))
    r2 = float(r2_score(y_real, y_pred))
    return {"mae": round(mae, 2), "rmse": round(rmse, 2), "r2": round(r2, 4)}


def predecir_clasificacion(red, Z, tipo_salida):
    raw = red.predict(Z, verbose=0, batch_size=1024)
    if tipo_salida == "sigmoid":
        probs = raw.ravel()
        pred = (probs >= 0.5).astype(int)
        return pred, probs
    pred = np.argmax(raw, axis=1)
    return pred, raw


def procesar_clasificacion(codigo, info, df):
    t0 = time.time()
    columnas = info["orden_X"]
    tipo_salida = info["salida"]
    nombres = [info["clases"][str(i)] for i in range(len(info["clases"]))]
    n_clases = len(nombres)
    lote = 15 if len(df) <= 1000 else 32

    part = {p: df[df["particion"] == p] for p in ["entrenamiento", "validacion", "prueba"]}
    X = {p: part[p][columnas].to_numpy(float) for p in part}
    y = {p: part[p]["clase"].to_numpy(int) for p in part}
    pesos = pesos_por_clase(y["entrenamiento"])

    print(f"\n{'=' * 78}\n{codigo}: {info['titulo']} ({tipo_salida.upper()}) | "
          f"X={len(columnas)} | clases={n_clases} | "
          f"tr/va/te={len(y['entrenamiento'])}/{len(y['validacion'])}/{len(y['prueba'])}", flush=True)

    busqueda, mejor = [], None
    for usar_pca in (False, True):
        pre = Preprocesador(columnas, usar_pca).ajustar(X["entrenamiento"])
        Ztr, Zva = pre.transformar(X["entrenamiento"]), pre.transformar(X["validacion"])
        for ocultas, act, drop, l1 in CANDIDATAS:
            keras.utils.set_random_seed(SEMILLA)
            red = construir_red(pre.dimension_salida, tipo_salida, n_clases, ocultas, act, drop, l1)
            hist = entrenar(red, Ztr, y["entrenamiento"], Zva, y["validacion"], lote, pesos)
            pva, pr_va = predecir_clasificacion(red, Zva, tipo_salida)
            bal = float(balanced_accuracy_score(y["validacion"], pva))
            acc = float(accuracy_score(y["validacion"], pva))
            fila = {
                "pca": usar_pca, "dimension_red": int(pre.dimension_salida),
                "ocultas": ocultas, "activacion": act, "dropout": drop, "l1": l1,
                "epocas": len(hist["loss"]),
                "exactitud_val": round(acc, 4),
                "exactitud_balanceada_val": round(bal, 4),
            }
            if tipo_salida == "sigmoid":
                fila["auc_val"] = round(float(roc_auc_score(y["validacion"], pr_va)), 4)
            busqueda.append(fila)
            print(f"  PCA={str(usar_pca):5} d={fila['dimension_red']:2} {str(ocultas):14} {act:4} | "
                  f"ep={fila['epocas']:3} | val acc={acc:.3f} bal={bal:.3f}"
                  + (f" auc={fila['auc_val']:.3f}" if "auc_val" in fila else ""), flush=True)
            criterio = fila["auc_val"] if tipo_salida == "sigmoid" else bal
            if mejor is None or criterio > mejor[0]:
                mejor = (criterio, fila, pre, red, hist)

    _, elegida, pre, red, hist = mejor
    Ztr, Zva, Zte = (pre.transformar(X[p]) for p in ["entrenamiento", "validacion", "prueba"])

    # Baseline lineal (Regresión Logística / Softmax lineal: 0 capas ocultas)
    keras.utils.set_random_seed(SEMILLA)
    lineal = construir_red(pre.dimension_salida, tipo_salida, n_clases, [], "linear", 0.0, 0.0)
    entrenar(lineal, Ztr, y["entrenamiento"], Zva, y["validacion"], lote, pesos)

    # CV-5 sobre entrenamiento + validación
    Xcv = np.vstack([X["entrenamiento"], X["validacion"]])
    ycv = np.concatenate([y["entrenamiento"], y["validacion"]])
    errores_cv = []
    for k, (itr, iva) in enumerate(StratifiedKFold(5, shuffle=True, random_state=SEMILLA).split(Xcv, ycv), 1):
        pre_k = Preprocesador(columnas, elegida["pca"]).ajustar(Xcv[itr])
        keras.utils.set_random_seed(SEMILLA)
        red_k = construir_red(pre_k.dimension_salida, tipo_salida, n_clases,
                              elegida["ocultas"], elegida["activacion"], elegida["dropout"], elegida["l1"])
        entrenar(red_k, pre_k.transformar(Xcv[itr]), ycv[itr],
                 pre_k.transformar(Xcv[iva]), ycv[iva], lote, pesos_por_clase(ycv[itr]))
        pk, _ = predecir_clasificacion(red_k, pre_k.transformar(Xcv[iva]), tipo_salida)
        errores_cv.append(round(float(1 - accuracy_score(ycv[iva], pk)), 4))

    # Evaluación final en prueba
    ptr, pr_tr = predecir_clasificacion(red, Ztr, tipo_salida)
    pva, pr_va = predecir_clasificacion(red, Zva, tipo_salida)
    pte, pr_te = predecir_clasificacion(red, Zte, tipo_salida)
    plin, pr_lin = predecir_clasificacion(lineal, Zte, tipo_salida)

    m_tr = metricas_clasificacion(y["entrenamiento"], ptr, pr_tr, nombres, tipo_salida)
    m_va = metricas_clasificacion(y["validacion"], pva, pr_va, nombres, tipo_salida)
    m_te = metricas_clasificacion(y["prueba"], pte, pr_te, nombres, tipo_salida)
    m_lin = metricas_clasificacion(y["prueba"], plin, pr_lin, nombres, tipo_salida)
    mayoritaria = int(np.bincount(y["entrenamiento"]).argmax())
    p_may = np.full_like(y["prueba"], mayoritaria)
    m_may = metricas_clasificacion(y["prueba"], p_may, np.zeros_like(y["prueba"], dtype=float), nombres, tipo_salida)

    nombre_lin = "Regresión logística (sigmoide lineal)" if tipo_salida == "sigmoid" else "Softmax lineal"
    resultado = {
        "codigo": codigo,
        "titulo": info["titulo"],
        "tipo": "clasificacion",
        "salida": tipo_salida,
        "clases": nombres,
        "hiperparametros_fijos": {
            "lote": lote, "epocas_max": EPOCAS_MAX, "paciencia": PACIENCIA,
            "optimizador": "Adam (lr = 0.001)",
            "perdida": "binary_crossentropy" if tipo_salida == "sigmoid" else "sparse_categorical_crossentropy",
            "pesos_por_clase": pesos,
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
        "validacion_cruzada_5": {
            "errores": errores_cv,
            "error_promedio": round(float(np.mean(errores_cv)), 4),
            "desviacion": round(float(np.std(errores_cv)), 4),
        },
        "comparacion_prueba": {
            "red_neuronal": {
                "exactitud": m_te["exactitud"],
                "exactitud_balanceada": m_te["exactitud_balanceada"],
                **({"auc": m_te["auc"]} if "auc" in m_te else {}),
            },
            "modelo_lineal": {
                "nombre": nombre_lin,
                "exactitud": m_lin["exactitud"],
                "exactitud_balanceada": m_lin["exactitud_balanceada"],
                **({"auc": m_lin["auc"]} if "auc" in m_lin else {}),
            },
            "clase_mayoritaria": {
                "exactitud": m_may["exactitud"],
                "exactitud_balanceada": m_may["exactitud_balanceada"],
            },
            "aleatorio": {
                "exactitud": round(1 / n_clases, 4),
                "exactitud_balanceada": round(1 / n_clases, 4),
            },
        },
        "segundos": round(time.time() - t0, 1),
    }

    red.save(MODELOS / f"{codigo}_red.keras")
    (MODELOS / f"{codigo}_preprocesamiento.json").write_text(
        json.dumps({**pre.a_dict(), "clases": nombres, "tipo": "clasificacion", "salida": tipo_salida, "codigo": codigo},
                   ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (MODELOS / f"{codigo}_metricas.json").write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  => ELEGIDA: {elegida['ocultas']} {elegida['activacion']} PCA={elegida['pca']} | "
          f"Prueba acc={m_te['exactitud']:.3f} bal={m_te['exactitud_balanceada']:.3f}"
          + (f" AUC={m_te['auc']:.3f}" if "auc" in m_te else "")
          + f" | E_out-E_in={resultado['diferencia_E_out_E_in']:+.3f} ({resultado['segundos']}s)", flush=True)
    return resultado


def procesar_regresion(codigo, info, df):
    t0 = time.time()
    columnas = info["orden_X"]
    lote = 64

    part = {p: df[df["particion"] == p] for p in ["entrenamiento", "validacion", "prueba"]}
    X = {p: part[p][columnas].to_numpy(float) for p in part}
    y = {p: part[p]["objetivo"].to_numpy(float) for p in part}

    # Escalamos y (target) con media/desv de entrenamiento para estabilidad numérica de la red lineal
    y_media = float(y["entrenamiento"].mean())
    y_desv = float(y["entrenamiento"].std()) or 1.0
    a_y_esc = lambda arr: (arr - y_media) / y_desv
    a_y_real = lambda arr: arr * y_desv + y_media

    print(f"\n{'=' * 78}\n{codigo}: {info['titulo']} (REGRESIÓN LINEAL) | "
          f"X={len(columnas)} | tr/va/te={len(y['entrenamiento'])}/{len(y['validacion'])}/{len(y['prueba'])}", flush=True)

    busqueda, mejor = [], None
    for usar_pca in (False, True):
        pre = Preprocesador(columnas, usar_pca).ajustar(X["entrenamiento"])
        Ztr, Zva = pre.transformar(X["entrenamiento"]), pre.transformar(X["validacion"])
        for ocultas, act, drop, l1 in CANDIDATAS:
            keras.utils.set_random_seed(SEMILLA)
            red = construir_red(pre.dimension_salida, "linear", 1, ocultas, act, drop, l1)
            hist = entrenar(red, Ztr, a_y_esc(y["entrenamiento"]), Zva, a_y_esc(y["validacion"]), lote)
            pva = np.clip(a_y_real(red.predict(Zva, verbose=0, batch_size=1024).ravel()), 0, None)
            mv = metricas_regresion(y["validacion"], pva)
            fila = {
                "pca": usar_pca, "dimension_red": int(pre.dimension_salida),
                "ocultas": ocultas, "activacion": act, "dropout": drop, "l1": l1,
                "epocas": len(hist["loss"]),
                "mae_val": mv["mae"], "rmse_val": mv["rmse"], "r2_val": mv["r2"],
            }
            busqueda.append(fila)
            print(f"  PCA={str(usar_pca):5} d={fila['dimension_red']:2} {str(ocultas):14} {act:4} | "
                  f"ep={fila['epocas']:3} | val R2={mv['r2']:.4f} MAE={mv['mae']:,.1f}", flush=True)
            if mejor is None or mv["r2"] > mejor[0]:
                mejor = (mv["r2"], fila, pre, red, hist)

    _, elegida, pre, red, hist = mejor
    Ztr, Zva, Zte = (pre.transformar(X[p]) for p in ["entrenamiento", "validacion", "prueba"])

    # Baseline 1: Regresión Lineal (red sin capas ocultas con salida lineal)
    keras.utils.set_random_seed(SEMILLA)
    lineal = construir_red(pre.dimension_salida, "linear", 1, [], "linear", 0.0, 0.0)
    entrenar(lineal, Ztr, a_y_esc(y["entrenamiento"]), Zva, a_y_esc(y["validacion"]), lote)

    # CV-5 (R2 en cada pliegue sobre entrenamiento + validación)
    Xcv = np.vstack([X["entrenamiento"], X["validacion"]])
    ycv = np.concatenate([y["entrenamiento"], y["validacion"]])
    r2_cv = []
    for itr, iva in KFold(5, shuffle=True, random_state=SEMILLA).split(Xcv, ycv):
        pre_k = Preprocesador(columnas, elegida["pca"]).ajustar(Xcv[itr])
        ym_k, ys_k = float(ycv[itr].mean()), float(ycv[itr].std()) or 1.0
        keras.utils.set_random_seed(SEMILLA)
        red_k = construir_red(pre_k.dimension_salida, "linear", 1,
                              elegida["ocultas"], elegida["activacion"], elegida["dropout"], elegida["l1"])
        entrenar(red_k, pre_k.transformar(Xcv[itr]), (ycv[itr] - ym_k) / ys_k,
                 pre_k.transformar(Xcv[iva]), (ycv[iva] - ym_k) / ys_k, lote)
        pk = np.clip(red_k.predict(pre_k.transformar(Xcv[iva]), verbose=0, batch_size=1024).ravel() * ys_k + ym_k, 0, None)
        r2_cv.append(round(float(r2_score(ycv[iva], pk)), 4))

    ptr = np.clip(a_y_real(red.predict(Ztr, verbose=0, batch_size=1024).ravel()), 0, None)
    pva = np.clip(a_y_real(red.predict(Zva, verbose=0, batch_size=1024).ravel()), 0, None)
    pte = np.clip(a_y_real(red.predict(Zte, verbose=0, batch_size=1024).ravel()), 0, None)
    plin = np.clip(a_y_real(lineal.predict(Zte, verbose=0, batch_size=1024).ravel()), 0, None)

    m_tr = metricas_regresion(y["entrenamiento"], ptr)
    m_va = metricas_regresion(y["validacion"], pva)
    m_te = metricas_regresion(y["prueba"], pte)
    m_lin = metricas_regresion(y["prueba"], plin)
    # Baseline 2: Persistencia (predecir el mismo volumen del mes actual t)
    m_per = metricas_regresion(y["prueba"], part["prueba"]["volumen_mes_t"].to_numpy(float))
    # Baseline 3: Media constante de entrenamiento
    m_med = metricas_regresion(y["prueba"], np.full_like(y["prueba"], y_media))

    resultado = {
        "codigo": codigo,
        "titulo": info["titulo"],
        "tipo": "regresion",
        "salida": "linear",
        "unidad": info.get("unidad", "CZK"),
        "hiperparametros_fijos": {
            "lote": lote, "epocas_max": EPOCAS_MAX, "paciencia": PACIENCIA,
            "optimizador": "Adam (lr = 0.001)", "perdida": "mse (Error Cuadrático Medio)",
        },
        "busqueda": busqueda,
        "elegida": elegida,
        "arquitectura": resumen_arquitectura(red),
        "historial": hist,
        "entrenamiento": m_tr,
        "validacion": m_va,
        "prueba": m_te,
        "validacion_cruzada_5": {
            "r2_pliegues": r2_cv,
            "r2_promedio": round(float(np.mean(r2_cv)), 4),
            "desviacion": round(float(np.std(r2_cv)), 4),
        },
        "comparacion_prueba": {
            "red_neuronal": m_te,
            "regresion_lineal": m_lin,
            "persistencia_mes_anterior": m_per,
            "media_constante": m_med,
        },
        "segundos": round(time.time() - t0, 1),
    }

    red.save(MODELOS / f"{codigo}_red.keras")
    (MODELOS / f"{codigo}_preprocesamiento.json").write_text(
        json.dumps({**pre.a_dict(), "tipo": "regresion", "salida": "linear", "codigo": codigo,
                    "y_media": y_media, "y_desv": y_desv}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (MODELOS / f"{codigo}_metricas.json").write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  => ELEGIDA: {elegida['ocultas']} {elegida['activacion']} PCA={elegida['pca']} | "
          f"Prueba R2={m_te['r2']:.4f} MAE={m_te['mae']:,.1f} | Lineal R2={m_lin['r2']:.4f} "
          f"({resultado['segundos']}s)", flush=True)
    return resultado


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    dic = json.loads((DATOS / "diccionario_caracteristicas.json").read_text(encoding="utf-8"))
    elegidos = sys.argv[1:] or list(ARCHIVOS)
    for codigo in elegidos:
        df = pd.read_csv(DATOS / ARCHIVOS[codigo])
        if dic[codigo]["tipo"] == "regresion":
            procesar_regresion(codigo, dic[codigo], df)
        else:
            procesar_clasificacion(codigo, dic[codigo], df)


if __name__ == "__main__":
    main()
