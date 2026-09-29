"""
==============================================================================
UNIVERSIDAD TÉCNICA DE AMBATO - Inteligencia de Negocios
AUTORES: Alison Marcela Cobos Taco / Henry Daniel Lagua Flores
==============================================================================
ARCHIVO: 38_rs_slope_one.py
SISTEMAS DE RECOMENDACIÓN (Informe 04 v2) — PUNTO 5: SLOPE ONE
DESCRIPCIÓN: Slope One ponderado (Lemire y Maclachlan, 2005) sobre la matriz
             de intensidad (rating 1-5 del monto mensual por producto):
               1. Matriz de desviaciones b(j,i) y soportes |S(j,i)|.
               2. Trazabilidad de la predicción para dos clientes reales.
               3. Validación cruzada 5-fold (MAE, RMSE) frente a 4 baselines:
                  media global, media del producto, media del cliente y
                  modelo de sesgos (media global + sesgo de cliente + de producto).
               4. Evaluación de ranking con el protocolo común (rs_comun.py).
USO: python scripts/38_rs_slope_one.py
==============================================================================
"""
import warnings

import numpy as np
import pandas as pd

from rs_comun import SEMILLA, cargar, comparar_con_popularidad, evaluar, guardar, particion_loo, popularidad, tabla


warnings.filterwarnings("ignore", message="Mean of empty slice")  # clientes con un solo producto: se usa la media del producto


def pliegues(n, k=5):
    """Partición aleatoria reproducible en k pliegues (equivalente a KFold con shuffle)."""
    idx = np.random.RandomState(SEMILLA).permutation(n)
    for te in np.array_split(idx, k):
        yield np.setdiff1d(idx, te), te


def entrenar(R):
    """Devuelve desviaciones b[j, i] = media(r_j - r_i) y soportes |S(j, i)| sobre los clientes con ambos productos."""
    X = R.values
    n = X.shape[1]
    dev, sop = np.zeros((n, n)), np.zeros((n, n))
    for j in range(n):
        for i in range(n):
            ambos = ~np.isnan(X[:, j]) & ~np.isnan(X[:, i])
            sop[j, i] = ambos.sum()
            if sop[j, i] and j != i:
                dev[j, i] = np.mean(X[ambos, j] - X[ambos, i])
    return dev, sop


def predecir(fila, dev, sop):
    """Slope One ponderado: sum_i |S(j,i)| (r_i + b(j,i)) / sum_i |S(j,i)|, para cada producto j."""
    conocidos = np.flatnonzero(~np.isnan(fila))
    pred = np.full(len(fila), np.nan)
    for j in range(len(fila)):
        idx = [i for i in conocidos if i != j and sop[j, i] > 0]
        if idx:
            w = sop[j, idx]
            pred[j] = np.sum(w * (fila[idx] + dev[j, idx])) / w.sum()
    return pred


def main():
    print("=" * 78 + "\nPUNTO 5 — SLOPE ONE\n" + "=" * 78)
    adop, R, perfiles, _ = cargar()
    prods = list(R.columns)
    dev, sop = entrenar(R)
    res = {"matriz_desviaciones": tabla(pd.DataFrame(dev, index=prods, columns=prods)),
           "matriz_soportes": {p: {q: int(sop[a, b]) for b, q in enumerate(prods)} for a, p in enumerate(prods)},
           "antisimetria_max_error": float(np.abs(dev + dev.T).max())}

    # ---- Trazabilidad con dos clientes reales (titulares con 3 productos) ----
    traza = {}
    for id_cliente in [2, 45]:
        cta = int(perfiles.index[perfiles.id_cliente == id_cliente][0])
        fila = R.loc[cta].values
        pred = predecir(fila, dev, sop)
        conocidos = {prods[i]: round(float(fila[i]), 4) for i in np.flatnonzero(~np.isnan(fila))}
        detalle = {}
        for j in np.flatnonzero(np.isnan(fila)):
            terminos = [{"desde": prods[i], "r_i": round(float(fila[i]), 4), "b_ji": round(float(dev[j, i]), 4),
                         "soporte": int(sop[j, i])} for i in np.flatnonzero(~np.isnan(fila)) if sop[j, i] > 0]
            detalle[prods[j]] = {"prediccion": round(float(pred[j]), 4), "terminos": terminos}
        traza[f"cliente_{id_cliente}"] = {"id_cuenta": cta, "productos_conocidos": conocidos,
                                          "predicciones": dict(sorted(detalle.items(), key=lambda kv: -kv[1]["prediccion"]))}
    res["trazabilidad"] = traza

    # ---- Validación cruzada 5-fold sobre las celdas observadas ----
    obs = np.argwhere(~np.isnan(R.values))
    errores = {m: {"mae": [], "rmse": []} for m in ["slope_one", "media_global", "media_producto", "media_cliente", "sesgos"]}
    por_producto = {p: [] for p in prods}
    cobertura = []
    for tr, te in pliegues(len(obs)):
        X = R.values.copy()
        prueba = obs[te]
        reales = X[prueba[:, 0], prueba[:, 1]].copy()
        X[prueba[:, 0], prueba[:, 1]] = np.nan
        d, s = entrenar(pd.DataFrame(X))
        mu = np.nanmean(X)
        m_prod = np.nanmean(X, axis=0)
        with np.errstate(all="ignore"):
            m_cli = np.nanmean(X, axis=1)
        b_prod = m_prod - mu
        b_cli = np.nanmean(X - mu - b_prod, axis=1)
        preds = {m: [] for m in errores}
        sin_pred = 0
        for (u, j), real in zip(prueba, reales):
            so = predecir(X[u], d, s)[j]
            if np.isnan(so):          # el cliente no tiene otro producto en entrenamiento
                so, sin_pred = m_prod[j], sin_pred + 1
            preds["slope_one"].append(so)
            preds["media_global"].append(mu)
            preds["media_producto"].append(m_prod[j])
            preds["media_cliente"].append(m_cli[u] if not np.isnan(m_cli[u]) else m_prod[j])
            preds["sesgos"].append(mu + b_prod[j] + (b_cli[u] if not np.isnan(b_cli[u]) else 0))
        cobertura.append(1 - sin_pred / len(prueba))
        for m, pr in preds.items():
            e = np.array(pr) - reales
            errores[m]["mae"].append(np.mean(np.abs(e)))
            errores[m]["rmse"].append(np.sqrt(np.mean(e ** 2)))
        e_so = np.abs(np.array(preds["slope_one"]) - reales)
        for j, p in enumerate(prods):
            por_producto[p].append(float(e_so[prueba[:, 1] == j].mean()))
    cv = {m: {"mae": round(float(np.mean(v["mae"])), 4), "mae_desv": round(float(np.std(v["mae"], ddof=1)), 4),
              "rmse": round(float(np.mean(v["rmse"])), 4), "mae_por_pliegue": [round(float(x), 4) for x in v["mae"]]}
          for m, v in errores.items()}
    for m in cv:
        if m != "slope_one":
            cv[m]["mejora_slope_one_pct"] = round(100 * (1 - cv["slope_one"]["mae"] / cv[m]["mae"]), 2)
    res["validacion_5fold"] = {"celdas": len(obs), "cobertura_slope_one": round(float(np.mean(cobertura)), 4),
                               "modelos": cv, "mae_slope_one_por_producto": {p: round(float(np.mean(v)), 4) for p, v in por_producto.items()}}

    # ---- Ranking con el protocolo común ----
    train, ocultos = particion_loo(adop)
    Rtr = R.where(train.astype(bool))
    d, s = entrenar(Rtr)
    puntajes = pd.DataFrame([predecir(Rtr.loc[c].values, d, s) for c in ocultos.index], index=ocultos.index, columns=prods)
    res["ranking"] = comparar_con_popularidad({"Slope One": evaluar("Slope One", puntajes, train, ocultos),
                                               "Popularidad": evaluar("Popularidad", popularidad(train), train, ocultos)})
    r_so, r_pop = res["ranking"]["Slope One"], res["ranking"]["Popularidad"]

    guardar("slope_one", res)
    print("Desviaciones b(j,i):\n", pd.DataFrame(dev, index=prods, columns=prods).round(3))
    print("\nTrazabilidad:", {k: {p: v["prediccion"] for p, v in t["predicciones"].items()} for k, t in traza.items()})
    print("\n5-fold:", {m: (v["mae"], v["mae_desv"]) for m, v in cv.items()})
    print("MAE Slope One por producto:", res["validacion_5fold"]["mae_slope_one_por_producto"])
    print("\nRanking:", r_so, "\nPopularidad:", r_pop)


if __name__ == "__main__":
    main()
