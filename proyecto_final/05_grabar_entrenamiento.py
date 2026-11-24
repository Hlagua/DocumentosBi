"""
==============================================================================
UNIVERSIDAD TÉCNICA DE AMBATO - Inteligencia de Negocios (Proyecto final)
AUTORES: Alison Marcela Cobos Taco / Henry Daniel Lagua Flores
==============================================================================
ARCHIVO: proyecto_final/05_grabar_entrenamiento.py

Graba el entrenamiento de cada red ÉPOCA POR ÉPOCA para verlo en el
"playground" del aplicativo (al estilo de TensorFlow Playground).

Para cada sistema se vuelve a entrenar la red elegida con exactamente la
misma configuración (arquitectura, activación, dropout, L1, balanceo,
lotes de 15, Adam, parada temprana y semilla 42) y se guardan los pesos al
final de cada época. Con esos pesos se calcula, en cada época:
  * pérdida y exactitud en entrenamiento, validación y prueba;
  * la frontera de decisión sobre un plano 2D (las 2 componentes
    principales de los datos estandarizados);
  * lo que "ve" cada neurona oculta (su activación sobre ese plano);
  * los pesos de las conexiones que se dibujan en el diagrama.

La versión de cada sistema es la misma que usa el aplicativo
(VERSION_POR_SISTEMA en app/nucleo.py).

Uso:  python proyecto_final/05_grabar_entrenamiento.py [S1 S2 S3 S4]
Salida: proyecto_final/playground/S#_entrenamiento.json
==============================================================================
"""

import base64
import importlib.util
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

DIR = Path(__file__).resolve().parent
DATOS = DIR / "datos"
SALIDA = DIR / "playground"
SALIDA.mkdir(exist_ok=True)

# Mismo entrenamiento que 02_entrenar_redes.py (se reutilizan sus funciones)
_spec = importlib.util.spec_from_file_location("entrenar_redes", DIR / "02_entrenar_redes.py")
E = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(E)

sys.path.insert(0, str(DIR / "app"))
from nucleo import VERSION_POR_SISTEMA  # noqa: E402

ARCHIVOS = {"S1": "S1_transacciones.csv", "S2": "S2_ordenes.csv", "S3": "S3_saldo_mensual.csv", "S4": "S4_prestamos.csv"}
REJILLA = 40          # celdas por lado del mapa 2D
NEURONAS_POR_CAPA = 6  # neuronas que se dibujan por capa oculta (las de mayor influencia)
MAX_CUADROS = 80       # épocas que se guardan como cuadros de la animación
PUNTOS = 500           # puntos de entrenamiento y de prueba que se dibujan


def b64(arr):
    return base64.b64encode(np.ascontiguousarray(arr, dtype=np.uint8).tobytes()).decode()


def entropia_cruzada(p, y):
    return float(-np.mean(np.log(np.clip(p[np.arange(len(y)), y], 1e-12, 1.0))))


def grabar(s):
    t0 = time.time()
    carpeta = DIR / VERSION_POR_SISTEMA[s]
    if not (carpeta / f"{s}_red.keras").exists():
        carpeta = DIR / "modelos"
    met = json.loads((carpeta / f"{s}_metricas.json").read_text(encoding="utf-8"))
    pre = json.loads((carpeta / f"{s}_preprocesamiento.json").read_text(encoding="utf-8"))
    E.BALANCEO = met.get("balanceo", {}).get("estrategia", "pesos")
    el = met["elegida"]
    clases = pre["clases"]
    M = len(clases)
    orden = pre["orden_X"]
    media, desv = np.array(pre["media"]), np.array(pre["desviacion"])
    pca = np.array(pre["pca_componentes"]) if pre["usa_pca"] else None

    df = pd.read_csv(DATOS / ARCHIVOS[s])
    part = {p: df[df["particion"] == p] for p in ["entrenamiento", "validacion", "prueba"]}
    X = {p: part[p][orden].to_numpy(float) for p in part}
    y = {p: part[p]["clase"].to_numpy(int) for p in part}
    a_z = lambda A: (A - media) / desv                                   # estandarizado (z-score)
    a_red = lambda Z: Z @ pca.T if pca is not None else Z               # entrada de la red
    Z = {p: a_z(X[p]) for p in X}
    R = {p: a_red(Z[p]) for p in Z}

    # --- reentrenamiento idéntico, guardando los pesos de cada época ---
    Xbal, ybal, pesos = E.balancear(X["entrenamiento"], y["entrenamiento"])
    keras.utils.set_random_seed(E.SEMILLA)
    red = E.construir_red(R["entrenamiento"].shape[1], M, el["ocultas"], el["activacion"], el["dropout"], el["l1"])
    fotos = [[w.copy() for w in red.get_weights()]]                     # época 0: pesos iniciales
    grabadora = keras.callbacks.LambdaCallback(
        on_epoch_end=lambda ep, logs: fotos.append([w.copy() for w in red.get_weights()]))
    print(f"\n{s}: reentrenando {el['ocultas']} {el['activacion']} (balanceo {E.BALANCEO}) ...", flush=True)
    parada = keras.callbacks.EarlyStopping(monitor="val_loss", patience=E.PACIENCIA, restore_best_weights=True)
    h = red.fit(a_red(a_z(Xbal)), ybal, validation_data=(R["validacion"], y["validacion"]), epochs=E.EPOCAS_MAX,
                batch_size=E.LOTE, class_weight=pesos, callbacks=[grabadora, parada], verbose=0, shuffle=True).history
    mejor = int(np.argmin(h["val_loss"])) + 1
    epocas = len(fotos) - 1
    final_te = float((red.predict(R["prueba"], verbose=0).argmax(1) == y["prueba"]).mean())
    print(f"  {epocas} épocas, mejor {mejor} | exactitud de prueba del reentrenamiento {final_te:.4f} "
          f"(modelo del aplicativo {met['prueba']['exactitud']})", flush=True)

    # --- plano 2D: 2 componentes principales de los datos estandarizados de entrenamiento ---
    centro = Z["entrenamiento"].mean(axis=0)
    _, sv, vt = np.linalg.svd(Z["entrenamiento"] - centro, full_matrices=False)
    V2 = vt[:2]
    varianza_2d = float((sv[:2] ** 2).sum() / (sv ** 2).sum())
    P = {p: (Z[p] - centro) @ V2.T for p in Z}
    lo = np.percentile(P["entrenamiento"], 1, axis=0)
    hi = np.percentile(P["entrenamiento"], 99, axis=0)
    margen = (hi - lo) * 0.08
    lo, hi = lo - margen, hi + margen
    gx = np.linspace(lo[0], hi[0], REJILLA)
    gy = np.linspace(hi[1], lo[1], REJILLA)                               # fila 0 = arriba
    malla = np.array([[x, yv] for yv in gy for x in gx])
    Zg = centro + malla @ V2                                             # vuelve al espacio de las X
    Rg = a_red(Zg)

    # --- neuronas que se dibujan: las de mayor peso de salida en el modelo final ---
    densas = [l for l in red.layers if isinstance(l, keras.layers.Dense)]
    W_final = [l.get_weights()[0] for l in densas]
    elegidas = []
    for i in range(len(densas) - 1):
        n = W_final[i].shape[1]
        if n <= NEURONAS_POR_CAPA:
            elegidas.append(list(range(n)))
        else:
            fuerza = np.linalg.norm(W_final[i + 1], axis=1)
            elegidas.append(sorted(np.argsort(fuerza)[-NEURONAS_POR_CAPA:].tolist()))
    elegidas.append(list(range(M)))
    multi = keras.Model(red.input, [l.output for l in densas])

    # --- cuadros de la animación ---
    if epocas + 1 <= MAX_CUADROS:
        cuadros = list(range(epocas + 1))
    else:
        cuadros = sorted(set(np.linspace(0, epocas, MAX_CUADROS).round().astype(int).tolist()) | {mejor, epocas})
    ind_tr = np.random.default_rng(0).choice(len(y["entrenamiento"]), min(PUNTOS, len(y["entrenamiento"])), replace=False)
    ind_te = np.random.default_rng(1).choice(len(y["prueba"]), min(PUNTOS, len(y["prueba"])), replace=False)

    activaciones, curvas, salida_cuadros = [], [], []
    for e in range(epocas + 1):
        red.set_weights(fotos[e])
        p_tr = red.predict(R["entrenamiento"], verbose=0, batch_size=4096)
        p_te = red.predict(R["prueba"], verbose=0, batch_size=4096)
        curvas.append({
            "epoca": e,
            "perdida_entrenamiento": round(entropia_cruzada(p_tr, y["entrenamiento"]), 5),
            "perdida_prueba": round(entropia_cruzada(p_te, y["prueba"]), 5),
            "exactitud_entrenamiento": round(float((p_tr.argmax(1) == y["entrenamiento"]).mean()), 4),
            "exactitud_prueba": round(float((p_te.argmax(1) == y["prueba"]).mean()), 4),
            "perdida_validacion": round(float(h["val_loss"][e - 1]), 5) if e else None,
            "exactitud_validacion": round(float(h["val_accuracy"][e - 1]), 4) if e else None,
        })
        if e in cuadros:
            salidas = multi.predict(Rg, verbose=0, batch_size=4096)
            prob = salidas[-1]
            activaciones.append([salidas[i][:, elegidas[i]] for i in range(len(densas) - 1)])
            pesos_aristas = []
            Ws = [d.get_weights()[0] for d in densas]
            previas = list(range(Rg.shape[1]))
            for i, sel in enumerate(elegidas):
                pesos_aristas.append(np.round(Ws[i][np.ix_(previas, sel)], 4).tolist())
                previas = sel
            salida_cuadros.append({
                "epoca": e,
                "clase": b64(prob.argmax(1)),
                "confianza": b64(np.clip(prob.max(1), 0, 1) * 255),
                "pred_prueba": b64(p_te[ind_te].argmax(1)),
                "aristas": pesos_aristas,
            })

    # Activaciones a 0..255: tanh ya está en [-1, 1] y la sigmoide se lleva de [0, 1] a [-1, 1];
    # otra activación (ReLU) se escalaría por el máximo de cada neurona
    # en cada época (así se ve la forma de lo que detecta aunque sus valores crezcan al entrenar)
    for capa in range(len(densas) - 1):
        bloque = np.stack([a[capa] for a in activaciones])               # cuadros x celdas x neuronas
        if el["activacion"] == "sigmoid":
            bloque = 2 * bloque - 1                                       # sigmoide [0, 1] -> [-1, 1]
        escala = 1.0 if el["activacion"] in ("tanh", "sigmoid") else np.maximum(np.abs(bloque).max(axis=1, keepdims=True), 1e-9)
        normal = np.clip(bloque / escala, -1, 1)
        for k, cuadro in enumerate(salida_cuadros):
            cuadro.setdefault("neuronas", []).append(
                [b64((normal[k][:, j] + 1) / 2 * 255) for j in range(normal.shape[2])])

    entradas = (Rg - Rg.mean(0)) / (Rg.std(0) + 1e-9)                    # mapas de cada entrada (fijos)
    nombres_entrada = orden if pca is None else [f"PC{i + 1}" for i in range(Rg.shape[1])]
    resultado = {
        "sistema": s,
        "titulo": met["titulo"],
        "clases": clases,
        "version": carpeta.name,
        "balanceo": E.BALANCEO,
        "arquitectura": {
            "entradas": nombres_entrada,
            "ocultas": el["ocultas"],
            "activacion": el["activacion"],
            "dropout": el["dropout"],
            "l1": el["l1"],
            "usa_pca": pca is not None,
            "parametros": int(red.count_params()),
            "neuronas_dibujadas": elegidas,
        },
        "entrenamiento": {"lote": E.LOTE, "optimizador": "Adam (lr 0.001)", "paciencia": E.PACIENCIA,
                          "epocas": epocas, "mejor_epoca": mejor,
                          "exactitud_prueba_reentrenamiento": round(final_te, 4),
                          "exactitud_prueba_aplicativo": met["prueba"]["exactitud"],
                          "n_entrenamiento": int(len(y["entrenamiento"])), "n_prueba": int(len(y["prueba"]))},
        "plano": {"rejilla": REJILLA, "x": [float(lo[0]), float(hi[0])], "y": [float(lo[1]), float(hi[1])],
                  "varianza_explicada": round(varianza_2d, 4)},
        "mapas_entrada": [b64((np.clip(entradas[:, j], -3, 3) / 3 + 1) / 2 * 255) for j in range(Rg.shape[1])],
        "puntos": {
            "entrenamiento": {"xy": np.round(P["entrenamiento"][ind_tr], 3).tolist(), "clase": y["entrenamiento"][ind_tr].tolist()},
            "prueba": {"xy": np.round(P["prueba"][ind_te], 3).tolist(), "clase": y["prueba"][ind_te].tolist()},
        },
        "curvas": curvas,
        "cuadros": salida_cuadros,
        "segundos": round(time.time() - t0, 1),
    }
    destino = SALIDA / f"{s}_entrenamiento.json"
    destino.write_text(json.dumps(resultado, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"  {len(salida_cuadros)} cuadros, plano 2D con {varianza_2d:.0%} de la varianza | "
          f"{destino.stat().st_size / 1e6:.1f} MB | {resultado['segundos']} s", flush=True)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    for s in (sys.argv[1:] or list(ARCHIVOS)):
        grabar(s)


if __name__ == "__main__":
    main()
