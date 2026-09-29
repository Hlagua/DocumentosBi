"""
==============================================================================
UNIVERSIDAD TÉCNICA DE AMBATO - Inteligencia de Negocios
AUTORES: Alison Marcela Cobos Taco / Henry Daniel Lagua Flores
==============================================================================
ARCHIVO: 39_rs_item_item.py
SISTEMAS DE RECOMENDACIÓN (Informe 04 v2) — PUNTO 7: ÍTEM A ÍTEM (COSENO Y PEARSON)
DESCRIPCIÓN:
  Sobre la matriz de ADOPCIÓN (cuenta x producto, binaria):
    * Coseno binario: |A ∩ B| / sqrt(|A| |B|)
    * Pearson (coeficiente phi) y lift, con prueba χ² por par y corrección de Holm
    * Coseno ponderado por frecuencia inversa (ITF = ln(N / n_j))
  Sobre la matriz de INTENSIDAD (rating 1-5 del monto mensual):
    * Coseno ajustado (Sarwar et al., 2001) y Pearson sobre clientes que
      tienen ambos productos, con su tamaño de muestra y p-valor.
  Cada variante se evalúa como recomendador con el protocolo común.
USO: python scripts/39_rs_item_item.py
==============================================================================
"""
import itertools

import numpy as np
import pandas as pd
from scipy import stats

from rs_comun import cargar, comparar_con_popularidad, evaluar, guardar, particion_loo, popularidad, tabla


def coseno_binario(A):
    X = A.values.astype(float)
    inter = X.T @ X
    n = np.diag(inter)
    return pd.DataFrame(inter / np.sqrt(np.outer(n, n)), index=A.columns, columns=A.columns)


def phi(A):
    return A.astype(float).corr(method="pearson")


def coseno_ajustado(R):
    """Resta a cada rating la media del cliente y calcula el coseno sobre los clientes con ambos productos."""
    C = R.sub(R.mean(axis=1), axis=0)
    prods = R.columns
    M = pd.DataFrame(np.nan, index=prods, columns=prods)
    for a in prods:
        for b in prods:
            ambos = C[a].notna() & C[b].notna()
            x, y = C.loc[ambos, a], C.loc[ambos, b]
            den = np.sqrt((x ** 2).sum() * (y ** 2).sum())
            M.loc[a, b] = (x * y).sum() / den if den > 0 else np.nan
    return M


def condicional(A):
    """Coseno asimétrico / probabilidad condicional P(j | i) = |i ∩ j| / |i| (Deshpande y Karypis, 2004)."""
    X = A.values.astype(float)
    inter = X.T @ X
    return pd.DataFrame(inter / np.diag(inter)[:, None], index=A.columns, columns=A.columns)


def puntuar_condicional(train):
    """score(u, j) = promedio de P(j | i) sobre los productos i que tiene el cliente (popularidad si no tiene ninguno)."""
    P = condicional(train).to_numpy(copy=True)
    np.fill_diagonal(P, 0)
    X = train.values.astype(float)
    n = X.sum(axis=1, keepdims=True)
    sc = np.where(n > 0, (X @ P) / np.maximum(n - X, 1), train.mean().values)
    return pd.DataFrame(sc, index=train.index, columns=train.columns)


def puntuar(train, S, peso=None, solo_positivos=False):
    """score(u, j) = sum_{i tenido por u} S(i, j) [* peso_j]."""
    valores = S.fillna(0).to_numpy(copy=True)
    np.fill_diagonal(valores, 0)
    S = pd.DataFrame(valores, index=S.index, columns=S.columns)
    if solo_positivos:
        S = S.clip(lower=0)
    sc = train.astype(float) @ S
    if peso is not None:
        sc = sc * peso
    return sc


def main():
    print("=" * 78 + "\nPUNTO 7 — ÍTEM A ÍTEM (COSENO Y PEARSON)\n" + "=" * 78)
    adop, R, _, _ = cargar()
    prods = list(adop.columns)
    N = len(adop)
    res = {}

    # ---- Matrices sobre la adopción completa (descriptivas) ----
    cos_b = coseno_binario(adop)
    ph = phi(adop)
    n = adop.sum()
    itf = np.log(N / n)
    pares = []
    for a, b in itertools.combinations(prods, 2):
        ambos = int(((adop[a] == 1) & (adop[b] == 1)).sum())
        lift = ambos * N / (n[a] * n[b])
        tabla_c = pd.crosstab(adop[a], adop[b]).values
        chi2, p = stats.chi2_contingency(tabla_c)[:2]
        pares.append({"par": f"{a} - {b}", "ambos": ambos, "coseno": round(float(cos_b.loc[a, b]), 4),
                      "phi": round(float(ph.loc[a, b]), 4), "lift": round(float(lift), 3), "chi2": round(float(chi2), 2), "p": p})
    pares = pd.DataFrame(pares).sort_values("p")
    m = len(pares)
    pares["p_holm"] = np.minimum(1, np.maximum.accumulate(pares.p.values * (m - np.arange(m))))
    pares["significativo_holm"] = pares.p_holm < 0.05
    res["adopcion"] = {"coseno_binario": tabla(cos_b), "pearson_phi": tabla(ph),
                       "itf": {p: round(float(v), 4) for p, v in itf.items()},
                       "pares": [{**r, "p": float(f"{r['p']:.3g}"), "p_holm": float(f"{r['p_holm']:.3g}")}
                                 for r in pares.to_dict(orient="records")]}

    # ---- Matrices sobre la intensidad (clientes con ambos productos) ----
    pear_r, n_par, p_par = (pd.DataFrame(np.nan, index=prods, columns=prods) for _ in range(3))
    for a in prods:
        for b in prods:
            ambos = R[a].notna() & R[b].notna()
            n_par.loc[a, b] = ambos.sum()
            if ambos.sum() >= 10 and a != b:
                r, p = stats.pearsonr(R.loc[ambos, a], R.loc[ambos, b])
                pear_r.loc[a, b], p_par.loc[a, b] = r, p
    adj = coseno_ajustado(R)
    res["intensidad"] = {"pearson_r": tabla(pear_r), "pearson_n": tabla(n_par, 0), "pearson_p": tabla(p_par, 6),
                         "coseno_ajustado": tabla(adj),
                         "r_medio_absoluto": round(float(np.nanmean(np.abs(pear_r.values[~np.eye(len(prods), dtype=bool)]))), 4)}

    # ---- Evaluación como recomendadores (protocolo común) ----
    train, ocultos = particion_loo(adop)
    Rtr = R.where(train.astype(bool))
    itf_tr = np.log(N / train.sum().clip(lower=1))
    variantes = {
        "Popularidad": popularidad(train),
        "Coseno binario": puntuar(train, coseno_binario(train)),
        "Coseno binario x ITF": puntuar(train, coseno_binario(train), peso=itf_tr),
        "Pearson (phi), solo asociaciones positivas": puntuar(train, phi(train), solo_positivos=True),
        "Coseno ajustado sobre intensidad": puntuar(train, coseno_ajustado(Rtr), solo_positivos=True),
        "Coseno asimétrico P(j|i)": puntuar_condicional(train),
    }
    evals = comparar_con_popularidad({n: evaluar(n, sc, train, ocultos) for n, sc in variantes.items()})
    res["ranking"] = evals

    guardar("item_item", res)
    print("Coseno binario:\n", cos_b.round(3))
    print("\nPhi:\n", ph.round(3))
    print("\nPares significativos (Holm):\n", pares[pares.significativo_holm][["par", "ambos", "phi", "lift", "p_holm"]].to_string(index=False))
    print("\nPearson sobre intensidad (r):\n", pear_r.round(3))
    print("r medio absoluto:", res["intensidad"]["r_medio_absoluto"])
    for k, v in evals.items():
        print(f"\n{k}: hit1={v['hit_1']} hit3={v['hit_3']} mrr={v['mrr']} | cola larga hit1={v['cola_larga']['hit_1']} "
              f"hit3={v['cola_larga']['hit_3']} | {v.get('vs_popularidad', '')} | cola: {v.get('vs_popularidad_cola_larga', '')}")


if __name__ == "__main__":
    main()
