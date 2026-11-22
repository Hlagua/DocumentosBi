"""
==============================================================================
UNIVERSIDAD TÉCNICA DE AMBATO - Inteligencia de Negocios
AUTORES: Alison Marcela Cobos Taco / Henry Daniel Lagua Flores
==============================================================================
ARCHIVO: modelos_literatura_berka/01_generar_datasets.py

Construye los 5 datasets correspondientes a las tareas clásicas de la
literatura sobre la base PKDD'99 / Berka (`DM_Financial_Kimball_v2` /
carpeta `dataframes/`), sin modificar `proyecto_final/`:

  M1. Riesgo de impago de préstamos (Binaria — salida SIGMOIDE)
      * Fuente: Fact_Prestamos + historial previo (fecha < fecha_otorgamiento)
      * Etiqueta: 1 = Impago (B, D), 0 = Paga sin problemas (A, C)
      * Sin fuga temporal: solo transacciones estrictamente anteriores al préstamo.

  M2. Propensión / Recomendación de tarjeta de crédito (Binaria — salida SIGMOIDE)
      * Fuente: rs_adopcion (RETIRO_TARJETA) + historial transaccional SIN
        movimientos de tarjeta (`operation != 'VYBER KARTOU'`) + perfil/distrito.
      * Etiqueta: 1 = Adopta/usa tarjeta de crédito, 0 = Sin tarjeta.
      * Sin fuga: excluye operaciones de tarjeta al construir las X.

  M3. Segmentación y perfilamiento de clientes (Multiclase 4 — salida SOFTMAX)
      * Fuente: perfil financiero de las 4,500 cuentas (saldo, depósitos,
        retiros, movimientos, órdenes, meses de vida).
      * Etiqueta: 4 segmentos descubiertos con K-Means (ajustado solo en
        entrenamiento para evitar fuga de datos) y nombrados según sus centroides.

  M4. Detección de fuga o abandono silencioso — Churn (Binaria — salida SIGMOIDE)
      * Fuente: transacciones iniciadas por el cliente (sin intereses UROK).
      * Ventana X: primer semestre de 1998 (ene–jun 1998).
      * Etiqueta y (futura, jul–dic 1998): 1 = Fuga / caída severa de actividad
        (volumen cae >= 40 % o saldo promedio cae >= 30 % en H2 1998), 0 = Activo.

  M5. Pronóstico de transacciones — Monto mensual futuro (Regresión — salida LINEAL)
      * Fuente: saldo y volumen transaccional mensual por cuenta (sin intereses).
      * X: comportamiento de la cuenta en el mes t (volumen, movimientos,
        depósitos, retiros, saldo, tendencias).
      * y (continua): monto total transaccionado en el mes siguiente (t + 1).
      * Partición agrupada por cuenta (60/20/20) para que no se repitan cuentas
        entre entrenamiento, validación y prueba.

Salidas en `modelos_literatura_berka/datos/`:
  M1_impago_prestamos.csv, M2_propension_tarjeta.csv,
  M3_segmentacion_clientes.csv, M4_fuga_clientes.csv,
  M5_pronostico_transacciones.csv, distritos.csv,
  diccionario_caracteristicas.json, resumen_datasets.json
==============================================================================
"""

import json
import math
import sys
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

BASE_DIR = Path(__file__).resolve().parents[1]
DF_DIR = BASE_DIR / "dataframes"
OUT_DIR = Path(__file__).resolve().parent / "datos"
OUT_DIR.mkdir(parents=True, exist_ok=True)

SEMILLA = 42
DELTA = 0.05
EPS_OBJETIVO = 0.02
COL_DISTRITO = ["poblacion", "salario_promedio", "tasa_desempleo", "tasa_criminalidad"]


def normalizar_texto(texto):
    texto = unicodedata.normalize("NFKD", str(texto))
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return " ".join(texto.lower().split())


def n_test_hoeffding(eps, delta=DELTA):
    return math.ceil(math.log(2 / delta) / (2 * eps**2))


def eps_hoeffding(n_test, delta=DELTA):
    return math.sqrt(math.log(2 / delta) / (2 * n_test))


def particion_estratificada(y, semilla=SEMILLA, proporciones=(0.6, 0.2, 0.2)):
    rng = np.random.default_rng(semilla)
    etiquetas = np.empty(len(y), dtype=object)
    y = np.asarray(y)
    for clase in np.unique(y):
        idx = np.flatnonzero(y == clase)
        rng.shuffle(idx)
        n_tr = int(round(proporciones[0] * len(idx)))
        n_va = int(round(proporciones[1] * len(idx)))
        etiquetas[idx[:n_tr]] = "entrenamiento"
        etiquetas[idx[n_tr:n_tr + n_va]] = "validacion"
        etiquetas[idx[n_tr + n_va:]] = "prueba"
    return etiquetas


def particion_por_cuenta(cuentas, semilla=SEMILLA, proporciones=(0.6, 0.2, 0.2)):
    """Divide 60/20/20 por cuenta única para evitar fuga entre train/val/test."""
    rng = np.random.default_rng(semilla)
    unicas = np.unique(cuentas)
    rng.shuffle(unicas)
    n_tr = int(round(proporciones[0] * len(unicas)))
    n_va = int(round(proporciones[1] * len(unicas)))
    mapa = {}
    for c in unicas[:n_tr]:
        mapa[c] = "entrenamiento"
    for c in unicas[n_tr:n_tr + n_va]:
        mapa[c] = "validacion"
    for c in unicas[n_tr + n_va:]:
        mapa[c] = "prueba"
    return pd.Series(cuentas).map(mapa).to_numpy()


def limpiar(df, columnas_x, col_y, nombre):
    rep = {"filas_iniciales": int(len(df))}
    df = df.replace([np.inf, -np.inf], np.nan)
    rep["nulos_por_columna"] = {c: int(v) for c, v in df[columnas_x + [col_y]].isna().sum().items() if v}
    df = df.dropna(subset=columnas_x + [col_y])
    rep["filas_tras_quitar_nulos"] = int(len(df))
    antes = len(df)
    df = df.drop_duplicates(subset=columnas_x + [col_y])
    rep["duplicados_eliminados"] = int(antes - len(df))
    rep["filas_finales"] = int(len(df))
    print(f"  [{nombre}] limpieza: {rep}")
    return df.reset_index(drop=True), rep


def resumir_clasificacion(df, columnas_x, nombres_clase, rep, descripcion, tipo_salida):
    conteo = df["clase"].value_counts().sort_index()
    n_prueba = int((df["particion"] == "prueba").sum())
    return {
        "tipo": "clasificacion",
        "tipo_salida": tipo_salida,
        "descripcion": descripcion,
        "n_filas": int(len(df)),
        "n_caracteristicas": len(columnas_x),
        "caracteristicas": columnas_x,
        "clases": {nombres_clase[int(k)]: int(v) for k, v in conteo.items()},
        "clase_mayoritaria_prop": round(float(conteo.max() / conteo.sum()), 4),
        "particion": {p: int((df["particion"] == p).sum()) for p in ["entrenamiento", "validacion", "prueba"]},
        "hoeffding": {
            "delta": DELTA,
            "eps_objetivo": EPS_OBJETIVO,
            "n_test_minimo_para_eps_objetivo": n_test_hoeffding(EPS_OBJETIVO),
            "n_test_real": n_prueba,
            "eps_garantizado_con_n_test_real": round(eps_hoeffding(n_prueba), 4),
        },
        "limpieza": rep,
        "rangos_X": {
            c: {"min": float(df[c].min()), "max": float(df[c].max()), "media": round(float(df[c].mean()), 4)}
            for c in columnas_x
        },
    }


def resumir_regresion(df, columnas_x, rep, descripcion):
    n_prueba = int((df["particion"] == "prueba").sum())
    y = df["objetivo"]
    return {
        "tipo": "regresion",
        "tipo_salida": "linear",
        "descripcion": descripcion,
        "n_filas": int(len(df)),
        "n_caracteristicas": len(columnas_x),
        "caracteristicas": columnas_x,
        "objetivo_stats": {
            "min": round(float(y.min()), 2),
            "max": round(float(y.max()), 2),
            "media": round(float(y.mean()), 2),
            "desv": round(float(y.std()), 2),
        },
        "particion": {p: int((df["particion"] == p).sum()) for p in ["entrenamiento", "validacion", "prueba"]},
        "hoeffding": {
            "delta": DELTA,
            "eps_objetivo": EPS_OBJETIVO,
            "n_test_minimo_para_eps_objetivo": n_test_hoeffding(EPS_OBJETIVO),
            "n_test_real": n_prueba,
            "eps_garantizado_con_n_test_real": round(eps_hoeffding(n_prueba), 4),
        },
        "limpieza": rep,
        "rangos_X": {
            c: {"min": float(df[c].min()), "max": float(df[c].max()), "media": round(float(df[c].mean()), 4)}
            for c in columnas_x
        },
    }


def cargar_fuentes():
    print("Cargando DataFrames desde DocumentosBi/dataframes/ ...")
    distritos = pd.read_csv(DF_DIR / "df_distritos_clean.csv", encoding="utf-8-sig")
    distritos = distritos.rename(
        columns={"tasa_desempleo_1996": "tasa_desempleo", "tasa_criminalidad_1996": "tasa_criminalidad"}
    )[["id_distrito", "nombre_distrito", "region"] + COL_DISTRITO]
    distritos["nombre_normalizado"] = distritos["nombre_distrito"].map(normalizar_texto)

    clientes = pd.read_csv(DF_DIR / "df_cliente_consolidado_clean.csv", encoding="utf-8-sig")
    perfiles = pd.read_csv(DF_DIR / "rs_perfiles.csv", encoding="utf-8-sig")
    adopcion = pd.read_csv(DF_DIR / "rs_adopcion.csv", encoding="utf-8-sig")
    prestamos = pd.read_csv(DF_DIR / "df_prestamos_clean.csv", encoding="utf-8-sig")
    trans = pd.read_csv(
        DF_DIR / "df_transacciones_completado.csv.gz",
        encoding="utf-8-sig",
        usecols=["id_transaccion", "id_cuenta", "fecha", "monto_transaccion", "saldo_cuenta",
                 "tipo_transaccion", "operation", "k_symbol"],
    )
    trans["fecha_dt"] = pd.to_datetime(trans["fecha"])
    return distritos, clientes, perfiles, adopcion, prestamos, trans


# ============================================================================
# M1. Riesgo de impago de préstamos (Binaria — SIGMOIDE)
# ============================================================================
NOMBRES_M1 = {0: "Paga sin problemas (A o C)", 1: "Impago (B o D)"}
X_M1 = [
    "monto_prestamo", "plazo_meses", "cuota_mensual", "ratio_cuota_saldo",
    "saldo_promedio_previo", "saldo_minimo_previo", "ingreso_mensual", "egreso_mensual",
    "movimientos_mes", "meses_historial", "edad", "es_mujer",
] + COL_DISTRITO


def construir_m1(prestamos, trans, distritos):
    print("\n[M1] Riesgo de impago de préstamos (Binaria — sigmoide)")
    p = prestamos.copy()
    p["clase"] = p["estado_prestamo"].isin(["B", "D"]).astype(int)
    p["fecha_otorgamiento"] = pd.to_datetime(p["fecha_otorgamiento"])

    # Historial ESTRICTAMENTE anterior a la fecha del préstamo (0 fuga temporal)
    t = trans[trans["id_cuenta"].isin(p["id_cuenta"])].merge(
        p[["id_cuenta", "fecha_otorgamiento"]], on="id_cuenta"
    )
    t = t[t["fecha_dt"] < t["fecha_otorgamiento"]].copy()
    t["ingreso"] = np.where(t["tipo_transaccion"] == "PRIJEM", t["monto_transaccion"].abs(), 0.0)
    t["egreso"] = np.where(t["tipo_transaccion"] != "PRIJEM", t["monto_transaccion"].abs(), 0.0)
    t["mes_per"] = t["fecha_dt"].dt.to_period("M")
    g = t.groupby("id_cuenta")
    meses = g["mes_per"].nunique()
    previo = pd.DataFrame({
        "saldo_promedio_previo_calc": g["saldo_cuenta"].mean(),
        "saldo_minimo_previo": g["saldo_cuenta"].min(),
        "ingreso_mensual": g["ingreso"].sum() / meses,
        "egreso_mensual": g["egreso"].sum() / meses,
        "movimientos_mes": g.size() / meses,
        "meses_historial": meses,
    }).reset_index()

    p = p.merge(previo, on="id_cuenta", how="left")
    p = p.merge(distritos[["id_distrito"] + COL_DISTRITO], on="id_distrito", how="left")
    p["saldo_promedio_previo"] = p["saldo_promedio_previo_calc"]
    p["cuota_mensual"] = p["monto_prestamo"] / p["plazo_meses"]
    p["ratio_cuota_saldo"] = p["cuota_mensual"] / p["saldo_promedio_previo"].clip(lower=1.0)
    p["edad"] = p["edad_cliente"]
    p["es_mujer"] = (p["sexo_cliente"] == "F").astype(int)

    p, rep = limpiar(p, X_M1, "clase", "M1")
    p["particion"] = particion_estratificada(p["clase"].values)
    p["nombre_clase"] = p["clase"].map(NOMBRES_M1)
    cols = ["id_prestamo", "id_cuenta", "nombre_distrito"] + X_M1 + ["clase", "nombre_clase", "particion"]
    p[cols].to_csv(OUT_DIR / "M1_impago_prestamos.csv", index=False, encoding="utf-8")
    return resumir_clasificacion(
        p, X_M1, NOMBRES_M1, rep,
        "Predice si un préstamo nuevo terminará en impago usando solo datos previos al otorgamiento (salida sigmoide).",
        "sigmoid",
    )


# ============================================================================
# M2. Propensión a tarjeta de crédito (Binaria — SIGMOIDE)
# ============================================================================
NOMBRES_M2 = {0: "Sin tarjeta de crédito", 1: "Propenso / con tarjeta de crédito"}
X_M2 = [
    "saldo_promedio_cuenta", "saldo_minimo_cuenta", "saldo_maximo_cuenta",
    "ingreso_mensual", "egreso_mensual", "movimientos_mes", "meses_vida",
    "tiene_prestamo", "ordenes_activas", "edad", "es_mujer",
] + COL_DISTRITO


def construir_m2(perfiles, clientes, adopcion, trans, distritos):
    print("\n[M2] Propensión / recomendación de tarjeta de crédito (Binaria — sigmoide)")
    # Excluimos operaciones de tarjeta (VYBER KARTOU) para evitar fuga directa
    t = trans[trans["operation"] != "VYBER KARTOU"].copy()
    t["ingreso"] = np.where(t["tipo_transaccion"] == "PRIJEM", t["monto_transaccion"].abs(), 0.0)
    t["egreso"] = np.where(t["tipo_transaccion"] != "PRIJEM", t["monto_transaccion"].abs(), 0.0)
    t["mes_per"] = t["fecha_dt"].dt.to_period("M")
    g = t.groupby("id_cuenta")
    meses = g["mes_per"].nunique().clip(lower=1)
    agg = pd.DataFrame({
        "saldo_promedio_cuenta": g["saldo_cuenta"].mean(),
        "saldo_minimo_cuenta": g["saldo_cuenta"].min(),
        "saldo_maximo_cuenta": g["saldo_cuenta"].max(),
        "ingreso_mensual": g["ingreso"].sum() / meses,
        "egreso_mensual": g["egreso"].sum() / meses,
        "movimientos_mes": g.size() / meses,
    }).reset_index()

    tit = clientes[clientes["es_titular"] == 1][
        ["id_cliente", "id_distrito", "tiene_prestamo", "total_ordenes_activas"]
    ]
    df = (
        perfiles[["id_cuenta", "id_cliente", "sexo", "edad_corte", "meses_vida"]]
        .merge(adopcion[["id_cuenta", "RETIRO_TARJETA"]], on="id_cuenta", how="inner")
        .merge(agg, on="id_cuenta", how="inner")
        .merge(tit, on="id_cliente", how="left")
        .merge(distritos[["id_distrito", "nombre_distrito"] + COL_DISTRITO], on="id_distrito", how="left")
    )
    df["clase"] = df["RETIRO_TARJETA"].astype(int)
    df["tiene_prestamo"] = df["tiene_prestamo"].fillna(0).astype(int)
    df["ordenes_activas"] = df["total_ordenes_activas"].fillna(0).astype(int)
    df["edad"] = df["edad_corte"]
    df["es_mujer"] = (df["sexo"] == "F").astype(int)

    df, rep = limpiar(df, X_M2, "clase", "M2")
    df["particion"] = particion_estratificada(df["clase"].values)
    df["nombre_clase"] = df["clase"].map(NOMBRES_M2)
    cols = ["id_cuenta", "nombre_distrito"] + X_M2 + ["clase", "nombre_clase", "particion"]
    df[cols].to_csv(OUT_DIR / "M2_propension_tarjeta.csv", index=False, encoding="utf-8")
    return resumir_clasificacion(
        df, X_M2, NOMBRES_M2, rep,
        "Estima la propensión de un cliente a adoptar tarjeta de crédito según su perfil financiero sin incluir retiros con tarjeta (salida sigmoide).",
        "sigmoid",
    )


# ============================================================================
# M3. Segmentación y perfilamiento de clientes (K-Means + Red SOFTMAX)
# ============================================================================
X_M3 = [
    "saldo_promedio", "deposito_mensual", "retiro_mensual", "ratio_retiro_deposito",
    "movimientos_mes", "meses_vida", "ordenes_activas", "tiene_prestamo",
    "edad", "es_mujer",
] + COL_DISTRITO
CLUSTER_COLS_M3 = ["saldo_promedio", "deposito_mensual", "retiro_mensual", "movimientos_mes", "meses_vida", "ordenes_activas"]


def construir_m3(perfiles, clientes, trans, distritos):
    print("\n[M3] Segmentación y perfilamiento de clientes (K-Means 4 segmentos + Red softmax)")
    t = trans[~trans["k_symbol"].isin(["UROK", "SANKC. UROK"])].copy()
    t["mes_per"] = t["fecha_dt"].dt.to_period("M")
    g = t.groupby("id_cuenta")
    mov_mes = (g.size() / g["mes_per"].nunique().clip(lower=1)).rename("movimientos_mes").reset_index()

    tit = clientes[clientes["es_titular"] == 1][
        ["id_cliente", "id_distrito", "tiene_prestamo", "total_ordenes_activas"]
    ]
    df = (
        perfiles[["id_cuenta", "id_cliente", "sexo", "edad_corte", "meses_vida",
                  "deposito_mensual", "retiro_mensual", "saldo_promedio"]]
        .merge(mov_mes, on="id_cuenta", how="left")
        .merge(tit, on="id_cliente", how="left")
        .merge(distritos[["id_distrito", "nombre_distrito"] + COL_DISTRITO], on="id_distrito", how="left")
    )
    df["movimientos_mes"] = df["movimientos_mes"].fillna(0.0)
    df["tiene_prestamo"] = df["tiene_prestamo"].fillna(0).astype(int)
    df["ordenes_activas"] = df["total_ordenes_activas"].fillna(0).astype(int)
    df["ratio_retiro_deposito"] = df["retiro_mensual"] / df["deposito_mensual"].clip(lower=1.0)
    df["edad"] = df["edad_corte"]
    df["es_mujer"] = (df["sexo"] == "F").astype(int)

    # Partición 60/20/20 primero por cuenta; K-Means ajustado SOLO en entrenamiento
    df = df.dropna(subset=X_M3).reset_index(drop=True)
    df["particion"] = particion_por_cuenta(df["id_cuenta"].values)
    tr_mask = df["particion"] == "entrenamiento"

    Xc_tr = df.loc[tr_mask, CLUSTER_COLS_M3].to_numpy(float)
    mu, sd = Xc_tr.mean(axis=0), Xc_tr.std(axis=0)
    sd[sd == 0] = 1.0
    km = KMeans(n_clusters=4, random_state=SEMILLA, n_init=20).fit((Xc_tr - mu) / sd)
    raw_clusters = km.predict((df[CLUSTER_COLS_M3].to_numpy(float) - mu) / sd)
    sil = float(silhouette_score((Xc_tr - mu) / sd, km.labels_))

    # Ordenar los 4 segmentos de menor a mayor saldo promedio para nombres claros y estables
    orden_saldos = np.argsort([df.loc[raw_clusters == c, "saldo_promedio"].mean() for c in range(4)])
    mapa_seg = {int(orig): int(nuevo) for nuevo, orig in enumerate(orden_saldos)}
    df["clase"] = pd.Series(raw_clusters).map(mapa_seg).astype(int)

    nombres_m3 = {
        0: "Básico / Bajo saldo",
        1: "Estándar / Flujo moderado",
        2: "Activo / Alto movimiento",
        3: "Premium / Alto patrimonio",
    }
    df, rep = limpiar(df, X_M3, "clase", "M3")
    rep["kmeans_silhouette_train"] = round(sil, 4)
    df["nombre_clase"] = df["clase"].map(nombres_m3)
    cols = ["id_cuenta", "nombre_distrito"] + X_M3 + ["clase", "nombre_clase", "particion"]
    df[cols].to_csv(OUT_DIR / "M3_segmentacion_clientes.csv", index=False, encoding="utf-8")
    res = resumir_clasificacion(
        df, X_M3, nombres_m3, rep,
        "Clasifica a un cliente nuevo en 1 de 4 perfiles financieros descubiertos con K-Means sobre entrenamiento (salida softmax).",
        "softmax",
    )
    res["kmeans_silhouette_train"] = round(sil, 4)
    return res, nombres_m3


# ============================================================================
# M4. Detección de fuga o abandono silencioso — Churn (Binaria — SIGMOIDE)
# ============================================================================
NOMBRES_M4 = {0: "Cliente retenido (actividad estable)", 1: "Fuga / caída severa de actividad"}
X_M4 = [
    "vol_h1_mensual", "mov_h1_mensual", "saldo_prom_h1", "saldo_min_h1",
    "saldo_fin_h1", "ratio_retiro_ingreso_h1", "meses_activos_h1",
    "tiene_prestamo", "ordenes_activas", "edad", "es_mujer",
] + COL_DISTRITO


def construir_m4(perfiles, clientes, trans, distritos):
    print("\n[M4] Detección de fuga o abandono silencioso — Churn H1->H2 1998 (Binaria — sigmoide)")
    cli_tr = trans[~trans["k_symbol"].isin(["UROK", "SANKC. UROK"])].copy()
    cli_tr["abs_m"] = cli_tr["monto_transaccion"].abs()
    cli_tr["ing"] = np.where(cli_tr["tipo_transaccion"] == "PRIJEM", cli_tr["abs_m"], 0.0)
    cli_tr["egr"] = np.where(cli_tr["tipo_transaccion"] != "PRIJEM", cli_tr["abs_m"], 0.0)
    cli_tr["mes_per"] = cli_tr["fecha_dt"].dt.to_period("M")

    # Ventana de observación X: H1 1998 (ene–jun 1998)
    h1 = cli_tr[(cli_tr["fecha_dt"] >= "1998-01-01") & (cli_tr["fecha_dt"] <= "1998-06-30")].sort_values(
        ["id_cuenta", "fecha_dt", "id_transaccion"]
    )
    g1 = h1.groupby("id_cuenta")
    f1 = pd.DataFrame({
        "vol_h1_total": g1["abs_m"].sum(),
        "vol_h1_mensual": g1["abs_m"].sum() / 6.0,
        "mov_h1_mensual": g1.size() / 6.0,
        "saldo_prom_h1": g1["saldo_cuenta"].mean(),
        "saldo_min_h1": g1["saldo_cuenta"].min(),
        "saldo_fin_h1": g1["saldo_cuenta"].last(),
        "ing_h1": g1["ing"].sum(),
        "egr_h1": g1["egr"].sum(),
        "meses_activos_h1": g1["mes_per"].nunique(),
    }).reset_index()
    f1["ratio_retiro_ingreso_h1"] = f1["egr_h1"] / f1["ing_h1"].clip(lower=1.0)

    # Ventana futura y: H2 1998 (jul–dic 1998) — NUNCA entra en X
    h2 = cli_tr[(cli_tr["fecha_dt"] >= "1998-07-01") & (cli_tr["fecha_dt"] <= "1998-12-31")]
    g2 = h2.groupby("id_cuenta")
    f2 = pd.DataFrame({
        "vol_h2_total": g2["abs_m"].sum(),
        "saldo_prom_h2": g2["saldo_cuenta"].mean(),
    }).reset_index()

    df = f1.merge(f2, on="id_cuenta", how="left").fillna({"vol_h2_total": 0.0, "saldo_prom_h2": 0.0})
    # Churn silencioso: caída >= 40 % del volumen transaccional O caída >= 30 % del saldo promedio en H2
    df["clase"] = ((df["vol_h2_total"] < 0.60 * df["vol_h1_total"]) | (df["saldo_prom_h2"] < 0.70 * df["saldo_prom_h1"])).astype(int)

    tit = clientes[clientes["es_titular"] == 1][
        ["id_cliente", "id_distrito", "tiene_prestamo", "total_ordenes_activas"]
    ]
    df = (
        df.merge(perfiles[["id_cuenta", "id_cliente", "sexo", "edad_corte"]], on="id_cuenta", how="inner")
        .merge(tit, on="id_cliente", how="left")
        .merge(distritos[["id_distrito", "nombre_distrito"] + COL_DISTRITO], on="id_distrito", how="left")
    )
    df["tiene_prestamo"] = df["tiene_prestamo"].fillna(0).astype(int)
    df["ordenes_activas"] = df["total_ordenes_activas"].fillna(0).astype(int)
    df["edad"] = df["edad_corte"]
    df["es_mujer"] = (df["sexo"] == "F").astype(int)

    df, rep = limpiar(df, X_M4, "clase", "M4")
    df["particion"] = particion_estratificada(df["clase"].values)
    df["nombre_clase"] = df["clase"].map(NOMBRES_M4)
    cols = ["id_cuenta", "nombre_distrito"] + X_M4 + ["clase", "nombre_clase", "particion"]
    df[cols].to_csv(OUT_DIR / "M4_fuga_clientes.csv", index=False, encoding="utf-8")
    return resumir_clasificacion(
        df, X_M4, NOMBRES_M4, rep,
        "Detecta fuga o caída severa de actividad del cliente en el siguiente semestre a partir de su comportamiento previo (salida sigmoide).",
        "sigmoid",
    )


# ============================================================================
# M5. Pronóstico de transacciones — Monto mensual t+1 (Regresión — LINEAL)
# ============================================================================
X_M5 = [
    "mes", "volumen_mes_t", "volumen_mes_t_1", "depositos_mes_t", "retiros_mes_t",
    "num_movimientos_t", "saldo_fin_mes_t", "saldo_prom_mes_t",
    "edad", "es_mujer",
] + COL_DISTRITO


def construir_m5(perfiles, clientes, trans, distritos):
    print("\n[M5] Pronóstico de monto transaccional del mes siguiente t+1 (Regresión — salida lineal)")
    cli_tr = trans[~trans["k_symbol"].isin(["UROK", "SANKC. UROK"])].copy()
    cli_tr["abs_m"] = cli_tr["monto_transaccion"].abs()
    cli_tr["dep"] = np.where(cli_tr["tipo_transaccion"] == "PRIJEM", cli_tr["abs_m"], 0.0)
    cli_tr["ret"] = np.where(cli_tr["tipo_transaccion"] != "PRIJEM", cli_tr["abs_m"], 0.0)
    cli_tr = cli_tr.sort_values(["id_cuenta", "fecha_dt", "id_transaccion"])
    cli_tr["mes_per"] = cli_tr["fecha_dt"].dt.to_period("M")

    # Solo meses de 1998 (y dic 1997 para rezago t-1) para un dataset ágil y representativo
    sub = cli_tr[cli_tr["fecha_dt"] >= "1997-11-01"]
    g = sub.groupby(["id_cuenta", "mes_per"])
    m = pd.DataFrame({
        "volumen_mes_t": g["abs_m"].sum(),
        "depositos_mes_t": g["dep"].sum(),
        "retiros_mes_t": g["ret"].sum(),
        "num_movimientos_t": g.size(),
        "saldo_fin_mes_t": g["saldo_cuenta"].last(),
        "saldo_prom_mes_t": g["saldo_cuenta"].mean(),
    }).reset_index().sort_values(["id_cuenta", "mes_per"])

    m["volumen_mes_t_1"] = m.groupby("id_cuenta")["volumen_mes_t"].shift(1)
    m["objetivo"] = m.groupby("id_cuenta")["volumen_mes_t"].shift(-1)
    m["mes"] = m["mes_per"].dt.month.astype(int)
    m = m.dropna(subset=["volumen_mes_t_1", "objetivo"]).copy()

    # Muestra representativa de hasta 12,000 cuenta×mes (agrupado por cuenta para 0 fuga)
    rng = np.random.default_rng(SEMILLA)
    if len(m) > 12000:
        cuentas = m["id_cuenta"].unique()
        rng.shuffle(cuentas)
        sel_cuentas = set(cuentas[:1500])
        m = m[m["id_cuenta"].isin(sel_cuentas)].copy()

    tit = clientes[clientes["es_titular"] == 1][["id_cliente", "id_distrito"]]
    m = (
        m.merge(perfiles[["id_cuenta", "id_cliente", "sexo", "edad_corte"]], on="id_cuenta", how="inner")
        .merge(tit, on="id_cliente", how="left")
        .merge(distritos[["id_distrito", "nombre_distrito"] + COL_DISTRITO], on="id_distrito", how="left")
    )
    m["edad"] = m["edad_corte"]
    m["es_mujer"] = (m["sexo"] == "F").astype(int)
    m["periodo"] = m["mes_per"].astype(str)

    m, rep = limpiar(m, X_M5, "objetivo", "M5")
    m["particion"] = particion_por_cuenta(m["id_cuenta"].values)
    cols = ["id_cuenta", "periodo", "nombre_distrito"] + X_M5 + ["objetivo", "particion"]
    m[cols].to_csv(OUT_DIR / "M5_pronostico_transacciones.csv", index=False, encoding="utf-8")
    return resumir_regresion(
        m, X_M5, rep,
        "Pronostica el monto total transaccionado de la cuenta en el mes siguiente (t+1) mediante regresión neuronal (salida lineal, pérdida MSE).",
    )


def construir_diccionario(nombres_m3):
    distrito = {
        "campo": "distrito", "etiqueta": "Distrito (ciudad) del cliente", "tipo": "texto",
        "genera": COL_DISTRITO,
        "regla": "Nombre del distrito (se reconoce sin tildes ni mayúsculas desde distritos.csv).",
    }
    sexo = {"campo": "sexo", "etiqueta": "Sexo (M/F)", "tipo": "texto", "genera": ["es_mujer"], "regla": "F -> 1, M -> 0"}
    edad = {"campo": "edad", "etiqueta": "Edad (años)", "tipo": "entero", "genera": ["edad"]}
    tiene_prestamo = {"campo": "tiene_prestamo", "etiqueta": "¿Tiene préstamo? (si/no)", "tipo": "texto",
                      "genera": ["tiene_prestamo"], "regla": "si -> 1, no -> 0"}

    return {
        "M1": {
            "titulo": "Riesgo de impago de préstamos", "tipo": "clasificacion", "salida": "sigmoid",
            "orden_X": X_M1, "clases": {str(k): v for k, v in NOMBRES_M1.items()},
            "campos": [
                {"campo": "monto_prestamo", "etiqueta": "Monto del préstamo", "tipo": "decimal", "genera": ["monto_prestamo"]},
                {"campo": "plazo_meses", "etiqueta": "Plazo en meses", "tipo": "entero",
                 "genera": ["plazo_meses", "cuota_mensual", "ratio_cuota_saldo"],
                 "regla": "cuota = monto / plazo; ratio = cuota / saldo promedio previo"},
                {"campo": "saldo_promedio_previo", "etiqueta": "Saldo promedio previo", "tipo": "decimal", "genera": ["saldo_promedio_previo"]},
                {"campo": "saldo_minimo_previo", "etiqueta": "Saldo mínimo previo", "tipo": "decimal", "genera": ["saldo_minimo_previo"]},
                {"campo": "ingreso_mensual", "etiqueta": "Ingreso mensual promedio", "tipo": "decimal", "genera": ["ingreso_mensual"]},
                {"campo": "egreso_mensual", "etiqueta": "Egreso mensual promedio", "tipo": "decimal", "genera": ["egreso_mensual"]},
                {"campo": "movimientos_mes", "etiqueta": "Movimientos por mes", "tipo": "decimal", "genera": ["movimientos_mes"]},
                {"campo": "meses_historial", "etiqueta": "Meses de historial previo", "tipo": "entero", "genera": ["meses_historial"]},
                edad, sexo, distrito,
            ],
        },
        "M2": {
            "titulo": "Propensión a tarjeta de crédito", "tipo": "clasificacion", "salida": "sigmoid",
            "orden_X": X_M2, "clases": {str(k): v for k, v in NOMBRES_M2.items()},
            "campos": [
                {"campo": "saldo_promedio_cuenta", "etiqueta": "Saldo promedio de la cuenta", "tipo": "decimal", "genera": ["saldo_promedio_cuenta"]},
                {"campo": "saldo_minimo_cuenta", "etiqueta": "Saldo mínimo de la cuenta", "tipo": "decimal", "genera": ["saldo_minimo_cuenta"]},
                {"campo": "saldo_maximo_cuenta", "etiqueta": "Saldo máximo de la cuenta", "tipo": "decimal", "genera": ["saldo_maximo_cuenta"]},
                {"campo": "ingreso_mensual", "etiqueta": "Ingreso mensual promedio", "tipo": "decimal", "genera": ["ingreso_mensual"]},
                {"campo": "egreso_mensual", "etiqueta": "Egreso mensual promedio", "tipo": "decimal", "genera": ["egreso_mensual"]},
                {"campo": "movimientos_mes", "etiqueta": "Movimientos por mes (sin tarjeta)", "tipo": "decimal", "genera": ["movimientos_mes"]},
                {"campo": "meses_vida", "etiqueta": "Antigüedad de la cuenta (meses)", "tipo": "entero", "genera": ["meses_vida"]},
                tiene_prestamo,
                {"campo": "ordenes_activas", "etiqueta": "Órdenes permanentes activas", "tipo": "entero", "genera": ["ordenes_activas"]},
                edad, sexo, distrito,
            ],
        },
        "M3": {
            "titulo": "Segmentación y perfilamiento de clientes", "tipo": "clasificacion", "salida": "softmax",
            "orden_X": X_M3, "clases": {str(k): v for k, v in nombres_m3.items()},
            "campos": [
                {"campo": "saldo_promedio", "etiqueta": "Saldo promedio de la cuenta", "tipo": "decimal", "genera": ["saldo_promedio"]},
                {"campo": "deposito_mensual", "etiqueta": "Depósito mensual promedio", "tipo": "decimal",
                 "genera": ["deposito_mensual", "ratio_retiro_deposito"], "regla": "ratio = retiro / depósito"},
                {"campo": "retiro_mensual", "etiqueta": "Retiro mensual promedio", "tipo": "decimal", "genera": ["retiro_mensual"]},
                {"campo": "movimientos_mes", "etiqueta": "Movimientos por mes", "tipo": "decimal", "genera": ["movimientos_mes"]},
                {"campo": "meses_vida", "etiqueta": "Antigüedad de la cuenta (meses)", "tipo": "entero", "genera": ["meses_vida"]},
                {"campo": "ordenes_activas", "etiqueta": "Órdenes permanentes activas", "tipo": "entero", "genera": ["ordenes_activas"]},
                tiene_prestamo, edad, sexo, distrito,
            ],
        },
        "M4": {
            "titulo": "Detección de fuga de clientes (Churn)", "tipo": "clasificacion", "salida": "sigmoid",
            "orden_X": X_M4, "clases": {str(k): v for k, v in NOMBRES_M4.items()},
            "campos": [
                {"campo": "vol_h1_mensual", "etiqueta": "Volumen transaccional mensual (semestre previo)", "tipo": "decimal", "genera": ["vol_h1_mensual"]},
                {"campo": "mov_h1_mensual", "etiqueta": "Movimientos por mes (semestre previo)", "tipo": "decimal", "genera": ["mov_h1_mensual"]},
                {"campo": "saldo_prom_h1", "etiqueta": "Saldo promedio (semestre previo)", "tipo": "decimal", "genera": ["saldo_prom_h1"]},
                {"campo": "saldo_min_h1", "etiqueta": "Saldo mínimo (semestre previo)", "tipo": "decimal", "genera": ["saldo_min_h1"]},
                {"campo": "saldo_fin_h1", "etiqueta": "Saldo al cierre del semestre previo", "tipo": "decimal", "genera": ["saldo_fin_h1"]},
                {"campo": "ratio_retiro_ingreso_h1", "etiqueta": "Ratio retiros / ingresos (ej. 0.85)", "tipo": "decimal", "genera": ["ratio_retiro_ingreso_h1"]},
                {"campo": "meses_activos_h1", "etiqueta": "Meses con actividad en el semestre (1 a 6)", "tipo": "entero", "genera": ["meses_activos_h1"]},
                tiene_prestamo,
                {"campo": "ordenes_activas", "etiqueta": "Órdenes permanentes activas", "tipo": "entero", "genera": ["ordenes_activas"]},
                edad, sexo, distrito,
            ],
        },
        "M5": {
            "titulo": "Pronóstico de transacciones (mes siguiente)", "tipo": "regresion", "salida": "linear",
            "orden_X": X_M5, "unidad": "CZK (monto mensual)",
            "campos": [
                {"campo": "mes", "etiqueta": "Mes actual (1 a 12)", "tipo": "entero", "genera": ["mes"]},
                {"campo": "volumen_mes_t", "etiqueta": "Monto total transaccionado en el mes actual (t)", "tipo": "decimal", "genera": ["volumen_mes_t"]},
                {"campo": "volumen_mes_t_1", "etiqueta": "Monto total transaccionado en el mes anterior (t-1)", "tipo": "decimal", "genera": ["volumen_mes_t_1"]},
                {"campo": "depositos_mes_t", "etiqueta": "Total depósitos del mes actual", "tipo": "decimal", "genera": ["depositos_mes_t"]},
                {"campo": "retiros_mes_t", "etiqueta": "Total retiros del mes actual", "tipo": "decimal", "genera": ["retiros_mes_t"]},
                {"campo": "num_movimientos_t", "etiqueta": "Número de movimientos del mes actual", "tipo": "entero", "genera": ["num_movimientos_t"]},
                {"campo": "saldo_fin_mes_t", "etiqueta": "Saldo al cierre del mes actual", "tipo": "decimal", "genera": ["saldo_fin_mes_t"]},
                {"campo": "saldo_prom_mes_t", "etiqueta": "Saldo promedio del mes actual", "tipo": "decimal", "genera": ["saldo_prom_mes_t"]},
                edad, sexo, distrito,
            ],
        },
    }


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    distritos, clientes, perfiles, adopcion, prestamos, trans = cargar_fuentes()
    m1 = construir_m1(prestamos, trans, distritos)
    m2 = construir_m2(perfiles, clientes, adopcion, trans, distritos)
    m3, nombres_m3 = construir_m3(perfiles, clientes, trans, distritos)
    m4 = construir_m4(perfiles, clientes, trans, distritos)
    m5 = construir_m5(perfiles, clientes, trans, distritos)

    resumen = {
        "semilla": SEMILLA,
        "particion": "60/20/20 (estratificada en M1/M2/M4; agrupada por cuenta en M3/M5)",
        "hoeffding_formula": "N_test >= ln(2/delta) / (2*eps^2)",
        "M1": m1, "M2": m2, "M3": m3, "M4": m4, "M5": m5,
    }
    distritos.drop(columns="nombre_normalizado").to_csv(OUT_DIR / "distritos.csv", index=False, encoding="utf-8")
    (OUT_DIR / "resumen_datasets.json").write_text(json.dumps(resumen, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUT_DIR / "diccionario_caracteristicas.json").write_text(
        json.dumps(construir_diccionario(nombres_m3), ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("\nResumen final de datasets generados:")
    for k in ["M1", "M2", "M3", "M4", "M5"]:
        r = resumen[k]
        print(f"  {k} ({r['tipo_salida']:7}): {r['n_filas']:,} filas, {r['n_caracteristicas']} X, particion={r['particion']}")


if __name__ == "__main__":
    main()
