"""
==============================================================================
UNIVERSIDAD TÉCNICA DE AMBATO - Inteligencia de Negocios
AUTORES: Alison Marcela Cobos Taco / Henry Daniel Lagua Flores
==============================================================================
ARCHIVO: rs_comun.py
DESCRIPCIÓN: Funciones comunes de los sistemas de recomendación (scripts 38-41):
             carga de las matrices del script 37, protocolo de evaluación
             único y registro de resultados en metricas_recomendadores.json.

PROTOCOLO DE EVALUACIÓN (igual para todos los modelos):
  * Se toman las cuentas con 2 o más productos.
  * A cada una se le oculta un producto elegido al azar (semilla 42 para
    comparar y elegir modelos; semilla 2026 para confirmar el elegido con
    otros productos ocultos).
  * El modelo se entrena sin esas celdas y ordena los productos que la cuenta
    no tiene en entrenamiento (entre ellos, el oculto).
  * Métricas: Hit@1, Hit@3 y MRR (rango recíproco medio).
  * Comparación con la popularidad mediante la prueba de McNemar sobre Hit@1
    (binomial exacta sobre los casos discordantes).
==============================================================================
"""
import json
import os

import numpy as np
import pandas as pd
from scipy import stats

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DF = os.path.join(BASE_DIR, "dataframes")
METRICAS = os.path.join(BASE_DIR, "metricas_recomendadores.json")
SEMILLA = 42                 # partición de SELECCIÓN de modelos
SEMILLA_CONFIRMACION = 2026  # partición independiente para CONFIRMAR el modelo elegido


def cargar():
    adop = pd.read_csv(os.path.join(DF, "rs_adopcion.csv")).set_index("id_cuenta")
    ratings = pd.read_csv(os.path.join(DF, "rs_ratings.csv"))
    perfiles = pd.read_csv(os.path.join(DF, "rs_perfiles.csv")).set_index("id_cuenta")
    productos = pd.read_csv(os.path.join(DF, "rs_productos.csv")).set_index("producto")
    R = ratings.pivot(index="id_cuenta", columns="producto", values="rating").reindex(index=adop.index, columns=adop.columns)
    return adop, R, perfiles, productos


def particion_loo(adop, semilla=SEMILLA):
    """Oculta un producto al azar por cada cuenta con 2 o más productos. Devuelve (matriz de entrenamiento, ocultos)."""
    rng = np.random.RandomState(semilla)
    elegibles = adop[adop.sum(axis=1) >= 2]
    ocultos = pd.Series({cta: rng.choice(np.flatnonzero(fila.values)) for cta, fila in elegibles.iterrows()})
    ocultos = ocultos.map(lambda j: adop.columns[j])
    train = adop.copy()
    for cta, prod in ocultos.items():
        train.loc[cta, prod] = 0
    return train, ocultos


def evaluar(nombre, puntajes, train, ocultos):
    """puntajes: DataFrame cuentas x productos (mayor = mejor). Solo se ordenan los productos no tenidos."""
    aciertos1, aciertos3, rr, top1 = [], [], [], []
    sc = puntajes.reindex(index=ocultos.index, columns=train.columns)
    tr = train.loc[ocultos.index]
    rng = np.random.RandomState(SEMILLA)
    for cta, oculto in ocultos.items():
        cand = tr.columns[tr.loc[cta].values == 0]
        # desempate aleatorio reproducible para no favorecer el orden de las columnas
        s = sc.loc[cta, cand].fillna(-np.inf).values + rng.uniform(0, 1e-9, len(cand))
        orden = cand[np.argsort(-s)]
        pos = int(np.flatnonzero(orden == oculto)[0]) + 1
        aciertos1.append(pos == 1)
        aciertos3.append(pos <= 3)
        rr.append(1 / pos)
        top1.append(orden[0])
    a1, a3, rr = np.array(aciertos1), np.array(aciertos3), np.array(rr)
    # Cola larga: casos en que el producto oculto NO es uno de los 2 más populares del entrenamiento.
    populares = train.sum().sort_values(ascending=False).index[:2]
    cola = ~ocultos.isin(populares).values
    r = {"modelo": nombre, "cuentas_evaluadas": len(ocultos),
         "hit_1": round(float(a1.mean()), 4), "hit_3": round(float(a3.mean()), 4), "mrr": round(float(rr.mean()), 4),
         "cola_larga": {"productos_excluidos": list(populares), "cuentas": int(cola.sum()),
                        "hit_1": round(float(a1[cola].mean()), 4), "hit_3": round(float(a3[cola].mean()), 4),
                        "mrr": round(float(rr[cola].mean()), 4)},
         "hit_1_por_producto_oculto": {k: round(float(v), 4) for k, v in pd.Series(a1, index=ocultos.values).groupby(level=0).mean().items()},
         "productos_distintos_en_top1": int(pd.Series(top1).nunique()),
         "top1_mas_frecuente": pd.Series(top1).value_counts().head(3).to_dict()}
    return r, a1, cola


def mcnemar(aciertos_modelo, aciertos_base, mascara=None):
    """Prueba de McNemar exacta sobre Hit@1 (opcionalmente solo en un subconjunto, p. ej. la cola larga)."""
    if mascara is not None:
        aciertos_modelo, aciertos_base = aciertos_modelo[mascara], aciertos_base[mascara]
    b = int(np.sum(aciertos_modelo & ~aciertos_base))   # acierta el modelo, falla la base
    c = int(np.sum(~aciertos_modelo & aciertos_base))   # falla el modelo, acierta la base
    p = stats.binomtest(b, b + c, 0.5).pvalue if b + c else 1.0
    return {"gana_modelo": b, "gana_popularidad": c, "p_valor": float(f"{p:.4g}")}


def comparar_con_popularidad(evaluaciones):
    """evaluaciones: {nombre: (resultado, aciertos, cola)}. Agrega McNemar global y en la cola larga."""
    _, a_pop, cola = evaluaciones["Popularidad"]
    salida = {}
    for nombre, (r, a, _) in evaluaciones.items():
        if nombre != "Popularidad":
            r["vs_popularidad"] = mcnemar(a, a_pop)
            r["vs_popularidad_cola_larga"] = mcnemar(a, a_pop, cola)
        salida[nombre] = r
    return salida


def popularidad(train):
    return pd.DataFrame(np.tile(train.mean().values, (len(train), 1)), index=train.index, columns=train.columns)


def guardar(seccion, datos):
    metricas = json.load(open(METRICAS, encoding="utf-8")) if os.path.exists(METRICAS) else {}
    metricas[seccion] = datos
    json.dump(metricas, open(METRICAS, "w", encoding="utf-8"), ensure_ascii=False, indent=2, default=str)


def tabla(df, decimales=4):
    return {str(i): {str(c): (round(float(v), decimales) if pd.notna(v) else None) for c, v in fila.items()}
            for i, fila in df.iterrows()}
