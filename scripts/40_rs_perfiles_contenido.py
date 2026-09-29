"""
==============================================================================
UNIVERSIDAD TÉCNICA DE AMBATO - Inteligencia de Negocios
AUTORES: Alison Marcela Cobos Taco / Henry Daniel Lagua Flores
==============================================================================
ARCHIVO: 40_rs_perfiles_contenido.py
SISTEMAS DE RECOMENDACIÓN (Informe 04 v2) — PUNTOS 6 Y 8, UTILIDAD E HÍBRIDO
DESCRIPCIÓN:
  Punto 6 — modelar productos, comportamientos y perfiles:
    * Productos: atributos de los 8 productos y catálogo de préstamos por plazo.
    * Comportamientos: diferencia de comportamiento entre quienes tienen y no
      tienen cada producto (tamaño del efecto).
    * Perfiles: 9 arquetipos (macro-región x edad) y su adopción, con χ² y Holm.
  Punto 8 — sistema basado en contenidos:
    * Vector de atributos de cada producto; perfil del cliente = promedio de los
      vectores de sus productos; puntaje = coseno perfil-producto.
    * Variante TF-IDF sobre la descripción de cada producto, construida con sus
      atributos reales (no con textos inventados).
  Otros recomendadores: demográfico, kNN usuario-usuario (por productos y por perfil).
  Utilidad financiera: regla de capacidad de pago para préstamos (Carta v8).
  Híbrido final con pesos fijados de antemano y recomendaciones para los 4,500 titulares.
USO: python scripts/40_rs_perfiles_contenido.py
==============================================================================
"""
import itertools
import os

import numpy as np
import pandas as pd
from scipy import stats

from rs_comun import (DF, SEMILLA, SEMILLA_CONFIRMACION, cargar, comparar_con_popularidad, evaluar, guardar,
                      particion_loo, popularidad, tabla)

K_VECINOS = 30
UMBRAL_CUOTA_SALDO = 0.057   # límite de la banda de capacidad "Baja" (Carta v8)
REFERENCIA_SESGADA = "kNN usuario-usuario (perfil con comportamiento) [referencia sesgada]"


def estandarizar(perfiles, variables):
    X = perfiles[variables].assign(mujer=(perfiles.sexo == "F").astype(float))
    X = pd.concat([X, pd.get_dummies(perfiles.macro_region).astype(float)], axis=1)
    return ((X - X.mean()) / X.std()).values


def puntuar_condicional(train):
    """Ítem a ítem con probabilidad condicional P(j | i) (misma función del script 39)."""
    X = train.values.astype(float)
    inter = X.T @ X
    P = inter / np.diag(inter)[:, None]
    np.fill_diagonal(P, 0)
    n = X.sum(axis=1, keepdims=True)
    sc = np.where(n > 0, (X @ P) / np.maximum(n - X, 1), train.mean().values)
    return pd.DataFrame(sc, index=train.index, columns=train.columns)


def auc(puntaje, positivo):
    """AUC = P(puntaje de un positivo > puntaje de un negativo), vía Mann-Whitney."""
    pos, neg = puntaje[positivo], puntaje[~positivo]
    u = stats.mannwhitneyu(pos, neg, alternative="two-sided").statistic
    return float(u / (len(pos) * len(neg)))


def holm(p):
    p = np.asarray(p)
    orden = np.argsort(p)
    ajustado = np.empty_like(p, dtype=float)
    ajustado[orden] = np.minimum(1, np.maximum.accumulate(p[orden] * (len(p) - np.arange(len(p)))))
    return ajustado


def coseno_filas(A, B):
    A = A / np.maximum(np.linalg.norm(A, axis=1, keepdims=True), 1e-12)
    B = B / np.maximum(np.linalg.norm(B, axis=1, keepdims=True), 1e-12)
    return A @ B.T


def vectores_producto(productos):
    """Atributos del producto: dirección, canal, contraparte (one-hot) + banderas + regularidad y monto (0-1)."""
    X = pd.get_dummies(productos[["direccion", "canal", "contraparte"]]).astype(float)
    X["es_credito"] = productos.es_credito
    X["es_recurrente_fijo"] = productos.es_recurrente_fijo
    X["regularidad"] = productos.regularidad_mensual
    lm = np.log1p(productos.monto_mensual_mediano)
    X["monto"] = (lm - lm.min()) / (lm.max() - lm.min())
    return X


def tfidf_producto(productos):
    """Documento de cada producto armado con sus atributos del Data Mart; TF-IDF suavizado."""
    docs = {p: " ".join([r.direccion, r.canal, r.contraparte, "credito" if r.es_credito else "no_credito",
                         "recurrente" if r.es_recurrente_fijo else "variable", r.descripcion]).lower().replace("(", "").replace(")", "").split()
            for p, r in productos.iterrows()}
    vocab = sorted({w for d in docs.values() for w in d})
    tf = pd.DataFrame([[d.count(w) / len(d) for w in vocab] for d in docs.values()], index=list(docs), columns=vocab)
    df = (tf > 0).sum()
    idf = np.log((1 + len(docs)) / (1 + df)) + 1
    return tf * idf, {p: " ".join(d) for p, d in docs.items()}


def puntuar_contenido(train, V):
    """perfil(u) = promedio de los vectores de sus productos; score(u, j) = coseno(perfil, vector_j)."""
    X = train.values.astype(float)
    n = X.sum(axis=1, keepdims=True)
    perfil = (X @ V.loc[train.columns].values) / np.maximum(n, 1)
    sc = coseno_filas(perfil, V.loc[train.columns].values)
    sc[n[:, 0] == 0] = np.nan
    return pd.DataFrame(sc, index=train.index, columns=train.columns).fillna(popularidad(train))


def puntuar_demografico(train, perfiles):
    grupo = perfiles.arquetipo.reindex(train.index)
    tasa = train.groupby(grupo).mean()
    return tasa.reindex(grupo.values).set_axis(train.index)


def puntuar_knn(train, S):
    """kNN usuario-usuario: promedio ponderado de la adopción de los K vecinos más similares (sin contarse a sí mismo)."""
    S = S.copy()
    np.fill_diagonal(S, -np.inf)
    idx = np.argpartition(-S, K_VECINOS, axis=1)[:, :K_VECINOS]
    w = np.take_along_axis(S, idx, axis=1).clip(min=0)
    X = train.values.astype(float)
    sc = np.einsum("uk,ukj->uj", w, X[idx]) / np.maximum(w.sum(axis=1, keepdims=True), 1e-12)
    return pd.DataFrame(sc, index=train.index, columns=train.columns)


def rango_normalizado(sc):
    """Convierte puntajes a rangos 0-1 por cliente, para poder promediar modelos de escalas distintas."""
    return sc.rank(axis=1, pct=True)


def main():
    print("=" * 78 + "\nPUNTOS 6 Y 8 — PRODUCTOS, COMPORTAMIENTOS, PERFILES Y CONTENIDOS\n" + "=" * 78)
    adop, R, perfiles, productos = cargar()
    prods = list(adop.columns)
    perfiles = perfiles.reindex(adop.index)
    res = {}

    # ======================= PUNTO 6: PRODUCTOS =======================
    p = pd.read_csv(os.path.join(DF, "df_prestamos_clean.csv"))
    p["impago"] = p.estado_prestamo.isin(["B", "D"])
    catalogo = p.groupby("plazo_meses").agg(prestamos=("id_prestamo", "size"), monto_medio=("monto_prestamo", "mean"),
                                            cuota_media=("pago_mensual", "mean"), tasa_impago=("impago", "mean"),
                                            ratio_cuota_saldo_mediano=("ratio_cuota_saldo_previo", "median"))
    chi_plazo = stats.chi2_contingency(pd.crosstab(p.plazo_meses, p.impago))
    res["punto_6_productos"] = {"atributos": productos.to_dict(orient="index"), "prestamos_por_plazo": tabla(catalogo),
                                "chi2_impago_vs_plazo": {"chi2": round(float(chi_plazo[0]), 3), "gl": int(chi_plazo[2]),
                                                         "p": round(float(chi_plazo[1]), 4)}}

    # ======================= PUNTO 6: COMPORTAMIENTOS =======================
    comp_vars = ["deposito_mensual", "retiro_mensual", "saldo_promedio", "sanciones_sobregiro", "meses_vida"]
    efecto = {}
    for prod in prods:
        tiene = adop[prod] == 1
        efecto[prod] = {}
        for v in comp_vars:
            x = perfiles[v]
            d = (x[tiene].mean() - x[~tiene].mean()) / x.std()
            efecto[prod][v] = round(float(d), 3)
    res["punto_6_comportamientos"] = {"diferencia_estandarizada_tiene_vs_no_tiene": efecto,
                                      "nota": "Diferencia de medias en desviaciones estándar (d de Cohen aproximado)."}

    # ======================= PUNTO 6: PERFILES =======================
    arq = perfiles.arquetipo
    adop_arq = adop.groupby(arq).mean()
    pruebas = []
    for prod in prods:
        chi = stats.chi2_contingency(pd.crosstab(arq, adop[prod]))
        pruebas.append({"producto": prod, "chi2": round(float(chi[0]), 2), "gl": int(chi[2]), "p": float(chi[1]),
                        "v_cramer": round(float(np.sqrt(chi[0] / len(arq))), 4)})
    ph = holm([x["p"] for x in pruebas])
    for x, a in zip(pruebas, ph):
        x["p_holm"] = float(f"{a:.3g}")
        x["p"] = float(f"{x['p']:.3g}")
        x["significativo"] = bool(a < 0.05)
    res["punto_6_perfiles"] = {"clientes_por_arquetipo": arq.value_counts().to_dict(),
                               "adopcion_por_arquetipo": tabla(adop_arq), "chi2_por_producto": pruebas}

    # ======================= RECOMENDADORES (protocolo común) =======================
    V = vectores_producto(productos)
    T, docs = tfidf_producto(productos)
    # Perfil EXÓGENO: variables que no dependen de los productos (edad, sexo, región, distrito, antigüedad).
    Z_exo = estandarizar(perfiles, ["edad_corte", "salario_promedio", "tasa_desempleo", "meses_vida"])
    # Perfil con comportamiento (solo como referencia): depósitos y retiros en efectivo son CONSECUENCIA de
    # tener o no productos electrónicos (quien domicilia pagos retira menos efectivo), por lo que en la
    # evaluación conservan la "sombra" del producto oculto (causalidad inversa) e inflan el acierto.
    Z_comp = estandarizar(perfiles, ["edad_corte", "salario_promedio", "tasa_desempleo", "meses_vida",
                                     "deposito_mensual", "retiro_mensual"])

    def modelos(train):
        return {"Popularidad": popularidad(train),
                "Contenidos (atributos)": puntuar_contenido(train, V),
                "Contenidos (TF-IDF)": puntuar_contenido(train, T),
                "Demográfico (arquetipo)": puntuar_demografico(train, perfiles),
                "Ítem a ítem P(j|i)": puntuar_condicional(train),
                "kNN usuario-usuario (productos)": puntuar_knn(train, coseno_filas(train.values.astype(float), train.values.astype(float))),
                "kNN usuario-usuario (perfil exógeno)": puntuar_knn(train, coseno_filas(Z_exo, Z_exo)),
                REFERENCIA_SESGADA: puntuar_knn(train, coseno_filas(Z_comp, Z_comp))}

    evaluaciones = {}
    for nombre_part, semilla in [("seleccion", SEMILLA), ("confirmacion", SEMILLA_CONFIRMACION)]:
        train, ocultos = particion_loo(adop, semilla)
        evaluaciones[nombre_part] = comparar_con_popularidad({n: evaluar(n, s, train, ocultos) for n, s in modelos(train).items()})
    # Elección con la partición de selección (mayor MRR), excluyendo la referencia sesgada; se confirma con la otra.
    elegibles = {n: r for n, r in evaluaciones["seleccion"].items() if n != REFERENCIA_SESGADA}
    elegido = max(elegibles, key=lambda n: elegibles[n]["mrr"])
    res["punto_8_contenidos"] = {"vector_de_atributos": tabla(V, 3), "documentos_tfidf": docs,
                                 "similitud_atributos": tabla(pd.DataFrame(coseno_filas(V.values, V.values), index=V.index, columns=V.index)),
                                 "similitud_tfidf": tabla(pd.DataFrame(coseno_filas(T.values, T.values), index=T.index, columns=T.index))}
    res["ranking"] = evaluaciones
    res["modelo_elegido"] = {"nombre": elegido, "criterio": "mayor MRR en la partición de selección (semilla 42)",
                             "seleccion": {k: elegibles[elegido][k] for k in ("hit_1", "hit_3", "mrr", "cola_larga")},
                             "confirmacion": {k: evaluaciones["confirmacion"][elegido][k] for k in ("hit_1", "hit_3", "mrr", "cola_larga")}}
    evals = evaluaciones["seleccion"]

    # ======================= UTILIDAD FINANCIERA (préstamos) =======================
    ratio_viejo = p.pago_mensual / p.salario_distrito
    tramos = pd.cut(ratio_viejo, [0, 0.30, 0.50, np.inf], labels=["<= 30%", "30% - 50%", "> 50%"])
    viejo = p.groupby(tramos, observed=True).impago.agg(["size", "sum", "mean"])
    critico = (tramos == "> 50%")
    chi_viejo = stats.chi2_contingency(pd.crosstab(critico, p.impago))
    banda = p.groupby("banda_capacidad").impago.agg(["size", "sum", "mean"]).reindex(["Baja", "Media-baja", "Media-alta", "Alta"])
    chi_banda = stats.chi2_contingency(pd.crosstab(p.banda_capacidad, p.impago))
    res["utilidad"] = {
        "regla_anterior_cuota_salario_distrital": {
            "tramos": {str(k): {"prestamos": int(v["size"]), "impagos": int(v["sum"]), "tasa": round(float(v["mean"]), 4)} for k, v in viejo.iterrows()},
            "chi2_mas_50_vs_resto": round(float(chi_viejo[0]), 3), "p": round(float(chi_viejo[1]), 4),
            "auc_impago": round(auc(ratio_viejo.values, p.impago.values), 4)},
        "regla_carta_v8_cuota_saldo_previo": {
            "bandas": {k: {"prestamos": int(v["size"]), "impagos": int(v["sum"]), "tasa": round(float(v["mean"]), 4)} for k, v in banda.iterrows()},
            "chi2": round(float(chi_banda[0]), 3), "p": float(f"{chi_banda[1]:.3g}"),
            "auc_impago": round(auc(p.ratio_cuota_saldo_previo.values, p.impago.values), 4)},
    }
    # Capacidad de los titulares sin préstamo: cuota máxima prudente = 5.7% del saldo promedio
    sin_prestamo = perfiles[adop.PRESTAMO == 0].copy()
    sin_prestamo["cuota_maxima"] = (UMBRAL_CUOTA_SALDO * sin_prestamo.saldo_promedio).clip(lower=0)
    cuota_mediana_mercado = float(p.pago_mensual.median())
    res["utilidad"]["titulares_sin_prestamo"] = {
        "cuentas": len(sin_prestamo),
        "cuota_maxima_prudente_mediana": round(float(sin_prestamo.cuota_maxima.median()), 2),
        "cuota_mediana_de_los_prestamos_otorgados": cuota_mediana_mercado,
        "pueden_pagar_la_cuota_mediana": int((sin_prestamo.cuota_maxima >= cuota_mediana_mercado).sum()),
        "monto_maximo_mediano_por_plazo": {int(m): round(float((sin_prestamo.cuota_maxima * m).median()), 0) for m in [12, 24, 36, 48, 60]}}

    # ======================= RECOMENDACIONES FINALES =======================
    # Modelo elegido entrenado con toda la adopción + regla de utilidad para el préstamo:
    # se ofrece solo si la cuota prudente (5.7% del saldo promedio) alcanza al menos la cuota más baja
    # otorgada por el banco, y siempre con un monto máximo acorde a esa capacidad.
    puntaje = modelos(adop)[elegido]
    cuota_max = (UMBRAL_CUOTA_SALDO * perfiles.saldo_promedio).clip(lower=0)
    cuota_minima = float(p.pago_mensual.min())
    filas = []
    for cta in adop.index:
        cand = [j for j in prods if adop.loc[cta, j] == 0]
        if cuota_max.loc[cta] < cuota_minima:
            cand = [j for j in cand if j != "PRESTAMO"]
        top = sorted(cand, key=lambda j: -puntaje.loc[cta, j])[:3]
        filas.append({"id_cuenta": cta, "id_cliente": int(perfiles.loc[cta, "id_cliente"]), "arquetipo": perfiles.loc[cta, "arquetipo"],
                      **{f"recomendacion_{i + 1}": (top[i] if i < len(top) else None) for i in range(3)},
                      "prestamo_cuota_maxima": round(float(cuota_max.loc[cta]), 2) if "PRESTAMO" in top else None,
                      "prestamo_monto_maximo_36m": round(float(cuota_max.loc[cta] * 36), 0) if "PRESTAMO" in top else None})
    reco = pd.DataFrame(filas)
    reco.to_csv(os.path.join(DF, "rs_recomendaciones.csv"), index=False, encoding="utf-8-sig")
    top3 = reco[["recomendacion_1", "recomendacion_2", "recomendacion_3"]]
    res["recomendaciones_finales"] = {
        "modelo": elegido, "cuentas": len(reco), "archivo": "dataframes/rs_recomendaciones.csv",
        "recomendacion_1": reco.recomendacion_1.value_counts().to_dict(),
        "apariciones_en_top3": top3.stack().value_counts().to_dict(),
        "cuentas_con_prestamo_en_top3": int(top3.eq("PRESTAMO").any(axis=1).sum()),
        "cuentas_sin_prestamo_bloqueadas_por_capacidad": int(((adop.PRESTAMO == 0) & (cuota_max < cuota_minima)).sum()),
        "ejemplos": reco[reco.id_cliente.isin([2, 45])].to_dict(orient="records")}

    guardar("perfiles_contenido", res)
    print("Préstamos por plazo:\n", catalogo.round(3))
    print("\nComportamiento (d):", pd.DataFrame(efecto).round(2))
    print("\nχ² arquetipo:", [(x["producto"], x["chi2"], x["p_holm"], x["v_cramer"]) for x in pruebas])
    for k, v in evals.items():
        print(f"\n{k}: hit1={v['hit_1']} hit3={v['hit_3']} mrr={v['mrr']} | cola hit1={v['cola_larga']['hit_1']} hit3={v['cola_larga']['hit_3']}"
              f" | {v.get('vs_popularidad', '')} | cola {v.get('vs_popularidad_cola_larga', '')}")
    print("\nConfirmación:", {n: (r["hit_1"], r["mrr"], r["cola_larga"]["hit_1"]) for n, r in evaluaciones["confirmacion"].items()})
    print("\nModelo elegido:", res["modelo_elegido"])
    print("\nUtilidad:", res["utilidad"])
    print("\nRecomendaciones:", res["recomendaciones_finales"])


if __name__ == "__main__":
    main()
