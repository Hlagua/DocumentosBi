"""
==============================================================================
UNIVERSIDAD TÉCNICA DE AMBATO - Inteligencia de Negocios (Proyecto final)
AUTORES: Alison Marcela Cobos Taco / Henry Daniel Lagua Flores
==============================================================================
ARCHIVO: proyecto_final/04_verificar_modelos.py

Verifica las redes de las dos versiones de balanceo (`modelos/` con pesos por
clase y `modelos_sobremuestreo/`) con cuatro pruebas:

  A. Datos PARECIDOS al dataset: casos de prueba con pequeñas variaciones
     (ruido del 5 % de la desviación en las características numéricas).
     La clase esperada es la original; se mide el acierto y cuántas
     predicciones se mantienen iguales.
  B. Datos NUNCA VISTOS: casos reales del Data Mart que no están en el
     dataset (ni en entrenamiento, ni en validación, ni en prueba).
       S1: transacciones que no se usaron (hay más de 800 mil).
       S3: meses cuenta x mes que no se usaron (de las clases 1 y 2; los
           708 sobregiros reales ya están todos en el dataset).
       S2 y S4: la base no tiene más órdenes con propósito ni más
           préstamos; se informa y se usan solo las pruebas A, C y D.
  C. FRONTERA DE DECISIÓN: casos donde las dos clases más probables están
     a menos de 10 puntos de probabilidad. La red los asigna siempre a una
     de las dos (argmax de softmax); se mide cuántos son y cuánto acierta.
  D. ATAJOS: (1) importancia por permutación: cuánto cae la exactitud
     balanceada si se desordena una característica; si una sola explica
     casi todo, el modelo depende de ella. (2) datos sintéticos extremos:
     cada característica numérica se lleva muy por encima y muy por debajo
     de lo visto, dejando el resto igual, y se mira si la predicción se
     dispara hacia una sola clase y con qué confianza.

Salida: proyecto_final/verificacion_modelos.md y verificacion_modelos.json
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
from sklearn.metrics import accuracy_score, balanced_accuracy_score, recall_score

DIR = Path(__file__).resolve().parent
RAIZ = DIR.parent
DATOS = DIR / "datos"
DF_DIR = RAIZ / "dataframes"
SEMILLA = 42
ARCHIVOS = {"S1": "S1_transacciones.csv", "S2": "S2_ordenes.csv", "S3": "S3_saldo_mensual.csv", "S4": "S4_prestamos.csv"}
VERSIONES = {"pesos": DIR / "modelos", "sobremuestreo": DIR / "modelos_sobremuestreo"}
COL_DISTRITO = ["poblacion", "salario_promedio", "tasa_desempleo", "tasa_criminalidad"]

# Características numéricas que una persona escribe (se varían en A y D).
# Año, mes, día, sexo, tiene_prestamo y los indicadores del distrito no se varían.
NUMERICAS = {
    "S1": ["monto", "saldo_despues", "edad"],
    "S2": ["monto_orden", "edad", "cuota_prestamo", "ordenes_activas_cuenta", "saldo_promedio_cuenta",
           "deposito_mensual", "retiro_mensual"],
    "S3": ["saldo_fin_mes", "saldo_promedio_mes", "saldo_min_mes", "saldo_max_mes", "cambio_saldo_mes",
           "num_movimientos_mes", "monto_medio_mov", "edad"],
    "S4": ["monto_prestamo", "plazo_meses", "saldo_promedio_previo", "saldo_minimo_previo", "ingreso_mensual",
           "egreso_mensual", "movimientos_mes", "meses_historial", "edad"],
}
ENTERAS = {"edad", "ordenes_activas_cuenta", "num_movimientos_mes", "plazo_meses", "meses_historial"}


# ----------------------------------------------------------------------------
# Modelos
# ----------------------------------------------------------------------------
class Modelo:
    def __init__(self, carpeta, s):
        if not (carpeta / f"{s}_red.keras").exists():      # S1 solo existe con pesos (ya estaba balanceado)
            carpeta = VERSIONES["pesos"]
        self.carpeta = carpeta.name
        self.red = keras.models.load_model(carpeta / f"{s}_red.keras")
        with open(carpeta / f"{s}_preprocesamiento.json", encoding="utf-8") as f:
            self.pre = json.load(f)
        self.orden = self.pre["orden_X"]
        self.media, self.desv = np.array(self.pre["media"]), np.array(self.pre["desviacion"])
        self.pca = np.array(self.pre["pca_componentes"]) if self.pre["usa_pca"] else None

    def probabilidades(self, df):
        z = (df[self.orden].to_numpy(float) - self.media) / self.desv
        if self.pca is not None:
            z = z @ self.pca.T
        return self.red.predict(z, verbose=0, batch_size=2048)


def consistente(s, df):
    """Recalcula las características derivadas para que el dato siga siendo coherente."""
    df = df.copy()
    for c in ENTERAS & set(df.columns):
        df[c] = df[c].round().clip(lower=0 if c != "edad" else 18)
    if s == "S4":
        df["plazo_meses"] = df["plazo_meses"].clip(lower=1)
        df["cuota_mensual"] = df["monto_prestamo"] / df["plazo_meses"]
        df["ratio_cuota_saldo"] = df["cuota_mensual"] / df["saldo_promedio_previo"].where(df["saldo_promedio_previo"] > 0, 1.0)
    if s == "S2":
        df.loc[df["tiene_prestamo"] == 0, "cuota_prestamo"] = 0.0
    return df


def metricas(y, p, n_clases):
    """La exactitud balanceada promedia solo las clases presentes; una clase sin casos queda en None."""
    y = np.asarray(y)
    presentes = set(np.unique(y).tolist())
    sens = recall_score(y, p, labels=list(range(n_clases)), average=None, zero_division=0)
    return {
        "n": int(len(y)),
        "exactitud": round(float(accuracy_score(y, p)), 4),
        "exactitud_balanceada": round(float(balanced_accuracy_score(y, p)), 4),
        "sensibilidad_por_clase": [round(float(v), 4) if k in presentes else None for k, v in enumerate(sens)],
    }


# ----------------------------------------------------------------------------
# Datos nunca vistos (reconstruidos con el mismo cálculo de 01_generar_datasets.py)
# ----------------------------------------------------------------------------
def distritos():
    d = pd.read_csv(DATOS / "distritos.csv")
    return d[["id_distrito"] + COL_DISTRITO]


def s1_completo(trans):
    t = trans[~trans["k_symbol"].isin(["UROK", "SANKC. UROK"])].copy()
    t["clase"] = t["operation"].map({"VKLAD": 0, "VYBER": 1, "VYBER KARTOU": 1, "PREVOD NA UCET": 2, "PREVOD Z UCTU": 3})
    t = t.dropna(subset=["clase"]).merge(distritos(), on="id_distrito", how="left")
    fecha = pd.to_datetime(t["fecha"])
    t["clase"] = t["clase"].astype(int)
    t["monto"] = t["monto_transaccion"].abs()
    t["saldo_despues"] = t["saldo_cuenta"]
    t["anio"], t["mes"], t["dia"], t["dia_semana"] = fecha.dt.year, fecha.dt.month, fecha.dt.day, fecha.dt.dayofweek
    t["edad"] = t["edad_cliente"]
    t["es_mujer"] = (t["sexo_cliente"] == "F").astype(int)
    return t[t["monto"] > 0]


def s3_completo(trans):
    perfiles = pd.read_csv(DF_DIR / "rs_perfiles.csv", encoding="utf-8-sig")
    clientes = pd.read_csv(DF_DIR / "df_cliente_consolidado_clean.csv", encoding="utf-8-sig")
    dist = pd.read_csv(DATOS / "distritos.csv")
    tr = trans[["id_transaccion", "id_cuenta", "fecha", "monto_transaccion", "saldo_cuenta"]].copy()
    tr["fecha_dt"] = pd.to_datetime(tr["fecha"])
    tr = tr.sort_values(["id_cuenta", "fecha_dt", "id_transaccion"])
    tr["mes_per"] = tr["fecha_dt"].dt.to_period("M")
    g = tr.groupby(["id_cuenta", "mes_per"])
    mensual = pd.DataFrame({
        "saldo_fin_mes": g["saldo_cuenta"].last(), "saldo_promedio_mes": g["saldo_cuenta"].mean(),
        "saldo_min_mes": g["saldo_cuenta"].min(), "saldo_max_mes": g["saldo_cuenta"].max(),
        "num_movimientos_mes": g.size(), "monto_medio_mov": g["monto_transaccion"].apply(lambda v: v.abs().mean()),
    }).reset_index()
    partes = []
    for cuenta, grupo in mensual.groupby("id_cuenta"):
        meses = pd.period_range(grupo["mes_per"].min(), pd.Period("1998-12", "M"), freq="M")
        partes.append(grupo.set_index("mes_per").reindex(meses).rename_axis("mes_per").reset_index().assign(id_cuenta=cuenta))
    m = pd.concat(partes, ignore_index=True)
    m["saldo_fin_mes"] = m.groupby("id_cuenta")["saldo_fin_mes"].ffill()
    for c in ["saldo_promedio_mes", "saldo_min_mes", "saldo_max_mes"]:
        m[c] = m[c].fillna(m["saldo_fin_mes"])
    m["num_movimientos_mes"] = m["num_movimientos_mes"].fillna(0).astype(int)
    m["monto_medio_mov"] = m["monto_medio_mov"].fillna(0.0)
    m["cambio_saldo_mes"] = (m["saldo_fin_mes"] - m.groupby("id_cuenta")["saldo_fin_mes"].shift(1)).fillna(0.0)
    sig = m.groupby("id_cuenta")["saldo_fin_mes"].shift(-1)
    m = m[sig.notna()].copy()
    sig = sig[sig.notna()]
    m["clase"] = np.where(sig < 0, 2, np.where(sig - m["saldo_fin_mes"] < 0, 1, 0)).astype(int)
    m["anio"], m["mes"] = m["mes_per"].dt.year.astype(int), m["mes_per"].dt.month.astype(int)
    tit = clientes[clientes["es_titular"] == 1][["id_cliente", "id_distrito"]]
    ctx = perfiles[["id_cuenta", "id_cliente", "sexo", "edad_corte"]].merge(tit, on="id_cliente", how="left")
    ctx = ctx.merge(dist[["id_distrito"] + COL_DISTRITO], on="id_distrito", how="left")
    m = m.merge(ctx, on="id_cuenta", how="left")
    m["edad"] = m["edad_corte"]
    m["es_mujer"] = (m["sexo"] == "F").astype(int)
    m["periodo"] = m["mes_per"].astype(str)
    return m


def comprobar_reconstruccion(completo, dataset, claves, columnas):
    """Las filas del dataset recalculadas aquí deben ser idénticas (prueba de que el cálculo es el mismo)."""
    unido = dataset[claves + columnas + ["clase"]].merge(completo[claves + columnas + ["clase"]], on=claves,
                                                         suffixes=("", "_r"))
    iguales = all(np.allclose(unido[c], unido[c + "_r"], equal_nan=True) for c in columnas + ["clase"])
    return iguales, len(unido)


def datos_nunca_vistos():
    print("Reconstruyendo datos nunca vistos desde dataframes/ ...", flush=True)
    trans = pd.read_csv(DF_DIR / "df_transacciones_completado.csv.gz", encoding="utf-8-sig")
    rng_estado = SEMILLA + 1
    salida, control = {}, {}

    ds1 = pd.read_csv(DATOS / ARCHIVOS["S1"])
    c1 = s1_completo(trans)
    columnas1 = [c for c in ds1.columns if c in c1.columns and c not in ("id_transaccion", "fecha", "nombre_distrito",
                                                                       "nombre_clase", "particion", "clase", "id_cuenta")]
    control["S1"] = comprobar_reconstruccion(c1, ds1, ["id_transaccion"], columnas1)
    # Nunca vistos = movimientos que no están en el dataset y cuya CUENTA tampoco se usó para
    # entrenar ni validar (cuentas de prueba o cuentas que no entraron al dataset).
    vistas1 = set(ds1.loc[ds1["particion"] != "prueba", "id_cuenta"])
    libres = c1[~c1["id_transaccion"].isin(ds1["id_transaccion"]) & ~c1["id_cuenta"].isin(vistas1)]
    control["S1_cuentas_nuevas"] = int(libres["id_cuenta"].nunique())
    salida["S1"] = pd.concat([g.sample(min(2500, len(g)), random_state=rng_estado) for _, g in libres.groupby("clase")])
    control["S1_disponibles"] = {int(k): int(v) for k, v in libres["clase"].value_counts().sort_index().items()}

    ds3 = pd.read_csv(DATOS / ARCHIVOS["S3"])
    c3 = s3_completo(trans)
    columnas3 = [c for c in ds3.columns if c in c3.columns and c not in ("id_cuenta", "periodo", "nombre_distrito",
                                                                       "nombre_clase", "particion", "clase")]
    control["S3"] = comprobar_reconstruccion(c3, ds3, ["id_cuenta", "periodo"], columnas3)
    usados = set(zip(ds3["id_cuenta"], ds3["periodo"]))
    vistas3 = set(ds3.loc[ds3["particion"] != "prueba", "id_cuenta"])
    nuevas3 = ~c3["id_cuenta"].isin(vistas3)
    libres3 = c3[nuevas3 & np.array([(a, b) not in usados for a, b in zip(c3["id_cuenta"], c3["periodo"])])]
    salida["S3"] = pd.concat([g.sample(min(2500, len(g)), random_state=rng_estado) for _, g in libres3.groupby("clase")])
    control["S3_disponibles"] = {int(k): int(v) for k, v in libres3["clase"].value_counts().sort_index().items()}
    control["S3_cuentas_nuevas"] = int(libres3["id_cuenta"].nunique())
    # Prueba con la PROPORCIÓN REAL del banco: todos los meses de las cuentas que no se usaron para
    # entrenar ni validar (en el banco el sobregiro es ~0.4 % de los meses).
    salida["S3_real"] = c3[nuevas3].copy()
    control["S3_real_por_clase"] = {int(k): int(v) for k, v in salida["S3_real"]["clase"].value_counts().sort_index().items()}
    for s in ("S1", "S3"):
        print(f"  {s}: reconstrucción idéntica al dataset = {control[s][0]} ({control[s][1]:,} filas comparadas); "
              f"nunca vistos disponibles por clase {control[s + '_disponibles']}", flush=True)
    return salida, control


# ----------------------------------------------------------------------------
# Pruebas
# ----------------------------------------------------------------------------
def prueba_parecidos(s, modelo, prueba, n_clases, repeticiones=5):
    rng = np.random.default_rng(SEMILLA)
    base = modelo.probabilidades(prueba).argmax(1)
    aciertos, estables = [], []
    for _ in range(repeticiones):
        ruidoso = prueba.copy()
        for c in NUMERICAS[s]:
            ruidoso[c] = ruidoso[c] + rng.normal(0, 0.05 * prueba[c].std(), len(prueba))
        ruidoso = consistente(s, ruidoso)
        p = modelo.probabilidades(ruidoso).argmax(1)
        aciertos.append(balanced_accuracy_score(prueba["clase"], p))
        estables.append((p == base).mean())
    return {
        "exactitud_balanceada_original": round(float(balanced_accuracy_score(prueba["clase"], base)), 4),
        "exactitud_balanceada_con_ruido": round(float(np.mean(aciertos)), 4),
        "predicciones_iguales_con_ruido": round(float(np.mean(estables)), 4),
    }


def prueba_frontera(modelo, datos, umbral=0.10):
    p = modelo.probabilidades(datos)
    orden = np.sort(p, axis=1)
    margen = orden[:, -1] - orden[:, -2]
    en_frontera = margen < umbral
    pred = p.argmax(1)
    y = datos["clase"].to_numpy()
    top2 = np.argsort(p, axis=1)[:, -2:]
    verdad_entre_las_dos = np.array([y[i] in top2[i] for i in range(len(y))])
    return {
        "umbral_margen": umbral,
        "proporcion_en_frontera": round(float(en_frontera.mean()), 4),
        "n_en_frontera": int(en_frontera.sum()),
        "acierto_en_frontera": round(float((pred[en_frontera] == y[en_frontera]).mean()), 4) if en_frontera.any() else None,
        "acierto_fuera_de_frontera": round(float((pred[~en_frontera] == y[~en_frontera]).mean()), 4),
        "clase_verdadera_entre_las_dos_mas_probables": round(float(verdad_entre_las_dos[en_frontera].mean()), 4)
        if en_frontera.any() else None,
        "asignados_a_una_de_las_dos": 1.0,
    }


def prueba_atajos(s, modelo, prueba, n_clases, repeticiones=5):
    rng = np.random.default_rng(SEMILLA)
    y = prueba["clase"].to_numpy()
    base = balanced_accuracy_score(y, modelo.probabilidades(prueba).argmax(1))
    importancia = {}
    for c in modelo.orden:
        if c in ("cuota_mensual", "ratio_cuota_saldo"):
            continue                                       # derivadas: se permutan junto con monto
        caidas = []
        for _ in range(repeticiones):
            mezcla = prueba.copy()
            mezcla[c] = rng.permutation(mezcla[c].to_numpy())
            mezcla = consistente(s, mezcla)
            caidas.append(base - balanced_accuracy_score(y, modelo.probabilidades(mezcla).argmax(1)))
        importancia[c] = round(float(np.mean(caidas)), 4)
    total = sum(max(v, 0) for v in importancia.values()) or 1.0
    orden = sorted(importancia.items(), key=lambda kv: -kv[1])

    extremos = {}
    for c in NUMERICAS[s]:
        sd = prueba[c].std()
        for nombre, valor in (("muy_alto", prueba[c].max() + 10 * sd), ("muy_bajo", prueba[c].min() - 10 * sd)):
            if c in ENTERAS and valor < 0:
                continue
            sint = prueba.copy()
            sint[c] = valor
            sint = consistente(s, sint)
            p = modelo.probabilidades(sint)
            pred = p.argmax(1)
            dist = np.bincount(pred, minlength=n_clases) / len(pred)
            extremos[f"{c}:{nombre}"] = {
                "valor": round(float(valor), 2),
                "clase_dominante": int(dist.argmax()),
                "proporcion_clase_dominante": round(float(dist.max()), 4),
                "confianza_media": round(float(p.max(1).mean()), 4),
            }
    return {
        "exactitud_balanceada_base": round(float(base), 4),
        "importancia_permutacion": dict(orden),
        "caracteristica_principal": orden[0][0],
        "peso_relativo_principal": round(max(orden[0][1], 0) / total, 4),
        "extremos": extremos,
    }


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    t0 = time.time()
    nuevos, control = datos_nunca_vistos()
    with open(DATOS / "diccionario_caracteristicas.json", encoding="utf-8") as f:
        dic = json.load(f)
    resultados = {"control_reconstruccion": {k: v for k, v in control.items()}, "sistemas": {}}
    for s, archivo in ARCHIVOS.items():
        nombres = [dic[s]["clases"][str(i)] for i in range(len(dic[s]["clases"]))]
        n = len(nombres)
        df = pd.read_csv(DATOS / archivo)
        prueba = df[df["particion"] == "prueba"].reset_index(drop=True)
        resultados["sistemas"][s] = {"titulo": dic[s]["titulo"], "clases": nombres, "versiones": {}}
        for version, carpeta in VERSIONES.items():
            modelo = Modelo(carpeta, s)
            print(f"\n{s} · versión {version} (carpeta {modelo.carpeta})", flush=True)
            r = {"carpeta": modelo.carpeta,
                 "prueba": metricas(prueba["clase"], modelo.probabilidades(prueba).argmax(1), n),
                 "A_parecidos": prueba_parecidos(s, modelo, prueba, n)}
            if s in nuevos:
                nv = nuevos[s]
                r["B_nunca_vistos"] = metricas(nv["clase"], modelo.probabilidades(nv).argmax(1), n)
                frontera_datos = pd.concat([prueba, nv[prueba.columns.intersection(nv.columns)]], ignore_index=True)
            else:
                r["B_nunca_vistos"] = None
                frontera_datos = prueba
            r["C_frontera"] = prueba_frontera(modelo, frontera_datos)
            r["D_atajos"] = prueba_atajos(s, modelo, prueba, n)
            if s == "S2":
                # Atajo dentro de la fila: la orden de préstamo suele tener monto == cuota del préstamo.
                # Regla de una línea: "si el monto coincide con la cuota, es préstamo; si no, es hogar".
                regla = np.where(np.isclose(prueba["monto_orden"], prueba["cuota_prestamo"]), 1, 0)
                r["E_regla_monto_cuota"] = metricas(prueba["clase"], regla, n)
            if s == "S3":
                # Misma red evaluada con la proporción REAL de meses (cuentas no usadas para entrenar)
                real = nuevos["S3_real"]
                p_real = modelo.probabilidades(real).argmax(1)
                r["F_proporcion_real"] = metricas(real["clase"], p_real, n)
                r["F_proporcion_real"]["siempre_estable"] = metricas(real["clase"], np.zeros(len(real), dtype=int), n)
            resultados["sistemas"][s]["versiones"][version] = r
            print(f"  prueba bal {r['prueba']['exactitud_balanceada']} | parecidos bal "
                  f"{r['A_parecidos']['exactitud_balanceada_con_ruido']} (iguales {r['A_parecidos']['predicciones_iguales_con_ruido']})"
                  + (f" | nunca vistos bal {r['B_nunca_vistos']['exactitud_balanceada']} n={r['B_nunca_vistos']['n']}"
                     if r["B_nunca_vistos"] else "")
                  + f" | frontera {r['C_frontera']['proporcion_en_frontera']} | principal "
                    f"{r['D_atajos']['caracteristica_principal']} ({r['D_atajos']['peso_relativo_principal']})", flush=True)
    resultados["segundos"] = round(time.time() - t0, 1)
    with open(DIR / "verificacion_modelos.json", "w", encoding="utf-8") as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2, default=lambda o: bool(o) if isinstance(o, np.bool_) else str(o))
    escribir_markdown(resultados)
    print(f"\nListo en {resultados['segundos']} s -> proyecto_final/verificacion_modelos.md")


def pct(v):
    return "—" if v is None else f"{v * 100:.1f} %"


def escribir_markdown(r):
    L = ["# Verificación de las redes neuronales (pesos por clase frente a sobremuestreo)", "",
         "Pruebas pedidas para la defensa: (A) datos parecidos al dataset, (B) datos que el modelo nunca vio, "
         "(C) casos en la frontera de decisión y (D) búsqueda de atajos con importancia por permutación y datos "
         "sintéticos extremos. S1 ya estaba balanceado, por eso sus dos columnas usan el mismo modelo.", ""]
    ctrl = r["control_reconstruccion"]
    cuentas_prueba = {s: pd.read_csv(DATOS / ARCHIVOS[s], usecols=["id_cuenta", "particion"])
                      .query("particion == 'prueba'")["id_cuenta"].nunique() for s in ("S1", "S3")}
    real3 = ctrl.get("S3_real_por_clase", {})
    L += ["**Control:** los datos nunca vistos se recalcularon con el mismo procedimiento del dataset. "
          f"Al recalcular las filas que sí están en el dataset, coinciden exactamente: S1 = {ctrl['S1'][0]} "
          f"({ctrl['S1'][1]:,} filas), S3 = {ctrl['S3'][0]} ({ctrl['S3'][1]:,} filas).", "",
          "**Partición por cuenta:** en S1, S2 y S3 ninguna cuenta está en dos particiones. "
          "Los \"nunca vistos\" (B) salen solo de cuentas que no se usaron para entrenar ni validar "
          f"(S1: {ctrl.get('S1_cuentas_nuevas', '—')} cuentas; S3: {ctrl.get('S3_cuentas_nuevas', '—')} cuentas), "
          "pero no son un grupo de clientes aparte: incluyen las cuentas de la prueba "
          f"(S1: {cuentas_prueba['S1']} de las {ctrl.get('S1_cuentas_nuevas', '—')}). "
          "Por eso (B) confirma, con otros movimientos de esos mismos clientes, que el resultado de la prueba se sostiene; "
          "no demuestra que la red acierte igual en otra población.", "",
          "(E) compara S2 con una regla de una línea. (F) evalúa S3 con la proporción real de meses del banco. "
          f"Los {real3.get('2', '—')} sobregiros de (F) son exactamente los mismos de la prueba, porque todos los "
          "sobregiros del banco ya estaban en el dataset; la sensibilidad de sobregiro en (F) repite la de la prueba y no es "
          "una medida nueva. Lo nuevo de (F) es la exactitud global frente a \"siempre estable\", porque casi todos esos "
          "meses estables y de caída no están en la prueba.", ""]
    for s, info in r["sistemas"].items():
        v = info["versiones"]
        L += [f"## {s} · {info['titulo']}", "", "| Prueba | Pesos por clase | Sobremuestreo 50/50 |", "| :--- | :---: | :---: |"]
        fila = lambda nombre, f: L.append(f"| {nombre} | {f(v['pesos'])} | {f(v['sobremuestreo'])} |")
        fila("Prueba original: exactitud balanceada", lambda x: pct(x["prueba"]["exactitud_balanceada"]))
        fila("A. Parecidos (ruido 5 %): exactitud balanceada", lambda x: pct(x["A_parecidos"]["exactitud_balanceada_con_ruido"]))
        fila("A. Parecidos: predicciones que no cambian", lambda x: pct(x["A_parecidos"]["predicciones_iguales_con_ruido"]))
        if v["pesos"]["B_nunca_vistos"]:
            fila("B. Nunca vistos: casos", lambda x: f"{x['B_nunca_vistos']['n']:,}")
            fila("B. Nunca vistos: exactitud", lambda x: pct(x["B_nunca_vistos"]["exactitud"]))
            fila("B. Nunca vistos: exactitud balanceada", lambda x: pct(x["B_nunca_vistos"]["exactitud_balanceada"]))
            fila("B. Nunca vistos: sensibilidad por clase (— = sin casos)",
                 lambda x: " · ".join(pct(a) for a in x["B_nunca_vistos"]["sensibilidad_por_clase"]))
            fila("Prueba original: sensibilidad por clase",
                 lambda x: " · ".join(pct(a) for a in x["prueba"]["sensibilidad_por_clase"]))
        else:
            L.append("| B. Nunca vistos | no hay datos reales sin usar | no hay datos reales sin usar |")
        fila("C. Casos en frontera (margen < 10 pts)", lambda x: f"{pct(x['C_frontera']['proporcion_en_frontera'])} ({x['C_frontera']['n_en_frontera']:,})")
        fila("C. Acierto en frontera / fuera", lambda x: f"{pct(x['C_frontera']['acierto_en_frontera'])} / {pct(x['C_frontera']['acierto_fuera_de_frontera'])}")
        fila("C. Clase real entre las dos más probables", lambda x: pct(x["C_frontera"]["clase_verdadera_entre_las_dos_mas_probables"]))
        fila("D. Característica más influyente (peso relativo)",
             lambda x: f"{x['D_atajos']['caracteristica_principal']} ({pct(x['D_atajos']['peso_relativo_principal'])})")
        if "E_regla_monto_cuota" in v["pesos"]:
            fila("E. Regla de una línea (monto = cuota → préstamo; si no, hogar): exactitud / balanceada",
                 lambda x: f"{pct(x['E_regla_monto_cuota']['exactitud'])} / {pct(x['E_regla_monto_cuota']['exactitud_balanceada'])}")
            fila("E. Red neuronal en la misma prueba: exactitud / balanceada",
                 lambda x: f"{pct(x['prueba']['exactitud'])} / {pct(x['prueba']['exactitud_balanceada'])}")
            fila("E. Sensibilidad de la regla por clase",
                 lambda x: " · ".join(pct(a) for a in x["E_regla_monto_cuota"]["sensibilidad_por_clase"]))
        if "F_proporcion_real" in v["pesos"]:
            fila("F. Proporción real de meses: casos", lambda x: f"{x['F_proporcion_real']['n']:,}")
            fila("F. Proporción real: exactitud / balanceada de la red",
                 lambda x: f"{pct(x['F_proporcion_real']['exactitud'])} / {pct(x['F_proporcion_real']['exactitud_balanceada'])}")
            fila("F. Proporción real: \"siempre estable\" (exactitud)",
                 lambda x: pct(x["F_proporcion_real"]["siempre_estable"]["exactitud"]))
            fila("F. Proporción real: sensibilidad por clase",
                 lambda x: " · ".join(pct(a) for a in x["F_proporcion_real"]["sensibilidad_por_clase"]))
        L.append("")
        for version, etiqueta in (("pesos", "pesos por clase"), ("sobremuestreo", "sobremuestreo")):
            d = v[version]["D_atajos"]
            top = list(d["importancia_permutacion"].items())[:5]
            L.append(f"**D. Importancia por permutación ({etiqueta}):** " + " · ".join(f"{k} {x * 100:+.1f}" for k, x in top)
                     + " (puntos de exactitud balanceada que se pierden al desordenarla)")
            saturados = [f"{k} → {info['clases'][e['clase_dominante']]} {pct(e['proporcion_clase_dominante'])}"
                         for k, e in d["extremos"].items() if e["proporcion_clase_dominante"] >= 0.9]
            L.append(f"**D. Extremos sintéticos ({etiqueta}):** "
                     + ("; ".join(saturados) if saturados else "ningún valor extremo manda el 90 % de los casos a una sola clase"))
            L.append("")
    (DIR / "verificacion_modelos.md").write_text("\n".join(L), encoding="utf-8")


if __name__ == "__main__":
    main()
