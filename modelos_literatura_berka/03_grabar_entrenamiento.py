"""
==============================================================================
UNIVERSIDAD TÉCNICA DE AMBATO - Inteligencia de Negocios
AUTORES: Alison Marcela Cobos Taco / Henry Daniel Lagua Flores
==============================================================================
ARCHIVO: modelos_literatura_berka/03_grabar_entrenamiento.py

Graba el entrenamiento época por época de los 5 modelos de la literatura
PKDD'99 / Berka (M1–M5) para el Playground interactivo:
  * M1, M4     -> clasificación binaria (salida SIGMOIDE)
  * M2, M3     -> clasificación multiclase, 3 y 4 clases (salida SOFTMAX)
  * M5         -> regresión continua (salida LINEAL)

Uso:    python modelos_literatura_berka/03_grabar_entrenamiento.py [M1..M5]
Salida: modelos_literatura_berka/playground/M#_entrenamiento.json
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
from sklearn.metrics import r2_score

DIR = Path(__file__).resolve().parent
DATOS = DIR / "datos"
MODELOS = DIR / "modelos"
SALIDA = DIR / "playground"
SALIDA.mkdir(exist_ok=True)

_spec = importlib.util.spec_from_file_location("entrenar_berka", DIR / "02_entrenar_modelos.py")
E = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(E)

REJILLA = 40
NEURONAS_POR_CAPA = 6
MAX_CUADROS = 80
PUNTOS = 500


def b64(arr):
    return base64.b64encode(np.ascontiguousarray(arr, dtype=np.uint8).tobytes()).decode()


def bce(p, y):
    p = np.clip(np.asarray(p, dtype=np.float64), 1e-12, 1.0 - 1e-12)
    y = np.asarray(y, dtype=np.float64)
    return float(-np.mean(y * np.log(p) + (1.0 - y) * np.log(1.0 - p)))


def sce(p, y):
    p = np.asarray(p, dtype=np.float64)
    return float(-np.mean(np.log(np.clip(p[np.arange(len(y)), y], 1e-12, 1.0))))


def grabar(codigo):
    t0 = time.time()
    met = json.loads((MODELOS / f"{codigo}_metricas.json").read_text(encoding="utf-8"))
    pre = json.loads((MODELOS / f"{codigo}_preprocesamiento.json").read_text(encoding="utf-8"))
    el = met["elegida"]
    tipo = met["tipo"]           # "clasificacion" | "regresion"
    salida_tipo = met["salida"]  # "sigmoid" | "softmax" | "linear"
    clases = pre.get("clases", [])
    n_clases = len(clases) if tipo == "clasificacion" else 1
    orden = pre["orden_X"]
    media, desv = np.array(pre["media"]), np.array(pre["desviacion"])
    pca = np.array(pre["pca_componentes"]) if pre["usa_pca"] else None
    lote = met["hiperparametros_fijos"]["lote"]

    df = pd.read_csv(DATOS / E.ARCHIVOS[codigo])
    part = {p: df[df["particion"] == p] for p in ["entrenamiento", "validacion", "prueba"]}
    X = {p: part[p][orden].to_numpy(float) for p in part}
    if tipo == "regresion":
        y_raw = {p: part[p]["objetivo"].to_numpy(float) for p in part}
        y_media, y_desv = float(pre["y_media"]), float(pre["y_desv"])
        y = {p: (y_raw[p] - y_media) / y_desv for p in part}
        pesos = None
    else:
        y = {p: part[p]["clase"].to_numpy(int) for p in part}
        pesos = E.pesos_por_clase(y["entrenamiento"])

    a_z = lambda A: (A - media) / desv
    a_red = lambda Z: Z @ pca.T if pca is not None else Z
    Z = {p: a_z(X[p]) for p in X}
    R = {p: a_red(Z[p]) for p in Z}

    # Reentrenamiento idéntico grabando pesos de cada época
    keras.utils.set_random_seed(E.SEMILLA)
    red = E.construir_red(R["entrenamiento"].shape[1], salida_tipo, n_clases,
                          el["ocultas"], el["activacion"], el["dropout"], el["l1"])
    fotos = [[w.copy() for w in red.get_weights()]]
    grabadora = keras.callbacks.LambdaCallback(
        on_epoch_end=lambda ep, logs: fotos.append([w.copy() for w in red.get_weights()])
    )
    print(f"\n{codigo} ({salida_tipo}): reentrenando {el['ocultas']} {el['activacion']} ...", flush=True)
    parada = keras.callbacks.EarlyStopping(monitor="val_loss", patience=E.PACIENCIA, restore_best_weights=True)
    h = red.fit(
        R["entrenamiento"], y["entrenamiento"],
        validation_data=(R["validacion"], y["validacion"]),
        epochs=E.EPOCAS_MAX, batch_size=lote, class_weight=pesos,
        callbacks=[grabadora, parada], verbose=0, shuffle=True,
    ).history
    mejor = int(np.argmin(h["val_loss"])) + 1
    epocas = len(fotos) - 1

    # Plano 2D PCA sobre datos estandarizados de entrenamiento
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
    gy = np.linspace(hi[1], lo[1], REJILLA)
    malla = np.array([[x, yv] for yv in gy for x in gx])
    Zg = centro + malla @ V2
    Rg = a_red(Zg)

    # Neuronas más influyentes por capa
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
    elegidas.append(list(range(W_final[-1].shape[1])))
    multi = keras.Model(red.input, [l.output for l in densas])

    if epocas + 1 <= MAX_CUADROS:
        cuadros = list(range(epocas + 1))
    else:
        cuadros = sorted(set(np.linspace(0, epocas, MAX_CUADROS).round().astype(int).tolist()) | {mejor, epocas})

    ind_tr = np.random.default_rng(0).choice(len(y["entrenamiento"]), min(PUNTOS, len(y["entrenamiento"])), replace=False)
    ind_te = np.random.default_rng(1).choice(len(y["prueba"]), min(PUNTOS, len(y["prueba"])), replace=False)

    activaciones, curvas, salida_cuadros = [], [], []
    if tipo == "regresion":
        y_lo = float(np.percentile(y_raw["entrenamiento"], 5))
        y_hi = float(np.percentile(y_raw["entrenamiento"], 95))
        y_span = max(y_hi - y_lo, 1.0)

    for e in range(epocas + 1):
        red.set_weights(fotos[e])
        p_tr = red.predict(R["entrenamiento"], verbose=0, batch_size=4096)
        p_te = red.predict(R["prueba"], verbose=0, batch_size=4096)

        if tipo == "regresion":
            pr_tr = np.clip(p_tr.ravel() * y_desv + y_media, 0, None)
            pr_te = np.clip(p_te.ravel() * y_desv + y_media, 0, None)
            curvas.append({
                "epoca": e,
                "perdida_entrenamiento": round(float(np.mean((p_tr.ravel() - y["entrenamiento"]) ** 2)), 5),
                "perdida_prueba": round(float(np.mean((p_te.ravel() - y["prueba"]) ** 2)), 5),
                "metrica_entrenamiento": round(float(r2_score(y_raw["entrenamiento"], pr_tr)), 4),
                "metrica_prueba": round(float(r2_score(y_raw["prueba"], pr_te)), 4),
            })
        elif salida_tipo == "sigmoid":
            pr_tr, pr_te = p_tr.ravel(), p_te.ravel()
            curvas.append({
                "epoca": e,
                "perdida_entrenamiento": round(bce(pr_tr, y["entrenamiento"]), 5),
                "perdida_prueba": round(bce(pr_te, y["prueba"]), 5),
                "metrica_entrenamiento": round(float(((pr_tr >= 0.5).astype(int) == y["entrenamiento"]).mean()), 4),
                "metrica_prueba": round(float(((pr_te >= 0.5).astype(int) == y["prueba"]).mean()), 4),
            })
        else:
            curvas.append({
                "epoca": e,
                "perdida_entrenamiento": round(sce(p_tr, y["entrenamiento"]), 5),
                "perdida_prueba": round(sce(p_te, y["prueba"]), 5),
                "metrica_entrenamiento": round(float((p_tr.argmax(1) == y["entrenamiento"]).mean()), 4),
                "metrica_prueba": round(float((p_te.argmax(1) == y["prueba"]).mean()), 4),
            })

        if e in cuadros:
            salidas = multi.predict(Rg, verbose=0, batch_size=4096)
            activaciones.append([salidas[i][:, elegidas[i]] for i in range(len(densas) - 1)])
            Ws = [d.get_weights()[0] for d in densas]
            pesos_aristas = []
            previas = list(range(Rg.shape[1]))
            for i, sel in enumerate(elegidas):
                pesos_aristas.append(np.round(Ws[i][np.ix_(previas, sel)], 4).tolist())
                previas = sel

            item = {"epoca": e, "aristas": pesos_aristas}
            if tipo == "regresion":
                val_g = np.clip(salidas[-1].ravel() * y_desv + y_media, 0, None)
                norm_g = np.clip((val_g - y_lo) / y_span, 0, 1) * 255
                item["valor_mapa"] = b64(norm_g)
                err_te = np.abs(pr_te[ind_te] - y_raw["prueba"][ind_te]) > met["prueba"]["mae"]
                item["pred_prueba"] = b64(err_te.astype(np.uint8))
            elif salida_tipo == "sigmoid":
                p1 = np.clip(salidas[-1].ravel(), 0, 1)
                cls = (p1 >= 0.5).astype(np.uint8)
                conf = np.maximum(p1, 1 - p1)
                item["clase"] = b64(cls)
                item["confianza"] = b64(conf * 255)
                item["pred_prueba"] = b64((p_te.ravel()[ind_te] >= 0.5).astype(np.uint8))
            else:
                prob = salidas[-1]
                item["clase"] = b64(prob.argmax(1))
                item["confianza"] = b64(np.clip(prob.max(1), 0, 1) * 255)
                item["pred_prueba"] = b64(p_te[ind_te].argmax(1))
            salida_cuadros.append(item)

    for capa in range(len(densas) - 1):
        bloque = np.stack([a[capa] for a in activaciones])
        if el["activacion"] == "sigmoid":
            bloque = 2 * bloque - 1                                       # sigmoide [0, 1] -> [-1, 1]
        escala = 1.0 if el["activacion"] in ("tanh", "sigmoid") else np.maximum(np.abs(bloque).max(axis=(0, 1)), 1e-9)
        normal = np.clip(bloque / escala, -1, 1)
        for k, cuadro in enumerate(salida_cuadros):
            cuadro.setdefault("neuronas", []).append(
                [b64((normal[k][:, j] + 1) / 2 * 255) for j in range(normal.shape[2])]
            )

    entradas = (Rg - Rg.mean(0)) / (Rg.std(0) + 1e-9)
    nombres_entrada = orden if pca is None else [f"PC{i + 1}" for i in range(Rg.shape[1])]

    if tipo == "regresion":
        puntos = {
            "entrenamiento": {
                "xy": np.round(P["entrenamiento"][ind_tr], 3).tolist(),
                "valor": np.round(np.clip((y_raw["entrenamiento"][ind_tr] - y_lo) / y_span, 0, 1), 3).tolist(),
            },
            "prueba": {
                "xy": np.round(P["prueba"][ind_te], 3).tolist(),
                "valor": np.round(np.clip((y_raw["prueba"][ind_te] - y_lo) / y_span, 0, 1), 3).tolist(),
            },
        }
        met_app = met["prueba"]["r2"]
        met_repro = curvas[mejor]["metrica_prueba"]
    else:
        puntos = {
            "entrenamiento": {"xy": np.round(P["entrenamiento"][ind_tr], 3).tolist(), "clase": y["entrenamiento"][ind_tr].tolist()},
            "prueba": {"xy": np.round(P["prueba"][ind_te], 3).tolist(), "clase": y["prueba"][ind_te].tolist()},
        }
        met_app = met["prueba"]["exactitud"]
        met_repro = curvas[mejor]["metrica_prueba"]

    resultado = {
        "codigo": codigo,
        "titulo": met["titulo"],
        "tipo": tipo,
        "salida": salida_tipo,
        "clases": clases if tipo == "clasificacion" else ["Monto predicho (CZK)"],
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
        "entrenamiento": {
            "lote": lote,
            "epocas": epocas,
            "mejor_epoca": mejor,
            "metrica_reentrenamiento": met_repro,
            "metrica_aplicativo": met_app,
            "n_entrenamiento": int(len(y["entrenamiento"])),
            "n_prueba": int(len(y["prueba"])),
        },
        "plano": {
            "rejilla": REJILLA,
            "x": [float(lo[0]), float(hi[0])],
            "y": [float(lo[1]), float(hi[1])],
            "varianza_explicada": round(varianza_2d, 4),
        },
        "mapas_entrada": [b64((np.clip(entradas[:, j], -3, 3) / 3 + 1) / 2 * 255) for j in range(Rg.shape[1])],
        "puntos": puntos,
        "curvas": curvas,
        "cuadros": salida_cuadros,
        "segundos": round(time.time() - t0, 1),
    }

    destino = SALIDA / f"{codigo}_entrenamiento.json"
    destino.write_text(json.dumps(resultado, ensure_ascii=False, separators=(",", ":"), allow_nan=False), encoding="utf-8")
    print(f"  {codigo}: {len(salida_cuadros)} cuadros | mejor={mejor}/{epocas} | "
          f"repro={met_repro:.4f} vs app={met_app:.4f} | {destino.stat().st_size / 1e6:.2f} MB ({resultado['segundos']}s)", flush=True)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    for c in (sys.argv[1:] or list(E.ARCHIVOS)):
        grabar(c)


if __name__ == "__main__":
    main()
