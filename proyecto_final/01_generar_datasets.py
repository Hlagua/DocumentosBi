"""
==============================================================================
UNIVERSIDAD TÉCNICA DE AMBATO - Inteligencia de Negocios (Proyecto final)
AUTORES: Alison Marcela Cobos Taco / Henry Daniel Lagua Flores
==============================================================================
ARCHIVO: proyecto_final/01_generar_datasets.py

Fase 1 del proyecto final: construye los 3 datasets MULTICLASE (uno por cada
sistema predictivo) a partir de los DataFrames extraídos del Data Mart Kimball
`DM_Financial_Kimball_v2` (carpeta `dataframes/`, generada por el script 32).

Reglas que cumple cada dataset:
  * La etiqueta `y` es la VERDADERA del banco o de los datos (no se calcula
    a partir de las X).
  * Todas las características X son datos que una persona puede ESCRIBIR en el
    formulario del aplicativo (no se carga nada desde la base al predecir),
    salvo los 4 indicadores del distrito, que se obtienen del nombre del
    distrito escrito por el usuario.
  * Limpieza: sin nulos, sin duplicados exactos y con rangos válidos.
  * Partición 60/20/20 (entrenamiento / validación / prueba) con semilla
    fija, guardada en la columna `particion` para que todos los modelos usen
    exactamente las mismas filas. En S1, S2 y S3 la partición es POR CUENTA
    (estratificada por clase): todas las filas de una cuenta quedan en un solo
    lado, así la prueba responde "¿y si es un cliente nuevo?". En S4 cada
    fila ya es una cuenta distinta.
  * Tamaño mínimo de prueba calculado con la desigualdad de Hoeffding:
        P[|E_out_estimado - E_out| > eps] <= 2·exp(-2·eps²·N_test)
        =>  N_test >= ln(2/delta) / (2·eps²)

Sistemas (todos multiclase, salida softmax):
  S1. Tipo de transacción (4 clases): depósito en efectivo, retiro,
      transferencia enviada y transferencia recibida.
  S2. Propósito de una orden permanente (4 clases): hogar (SIPO),
      préstamo (UVER), seguro (POJISTNE) y arrendamiento (LEASING).
  S3. Estado del saldo de la cuenta el mes siguiente (3 clases): estable o
      creciente, caída sin sobregiro y sobregiro.
  S4. Mora al corte del 31/12/1998 de un préstamo (2 clases, también con
      softmax): al día (A, C) o en mora/impago (B, D) en esa fecha. Los
      préstamos C siguen abiertos y podrían caer en mora después del corte,
      por eso la etiqueta es "al corte" y no "pagará o no pagará". Es el
      sistema binario permitido; las X son datos que el banco conoce al
      aprobar el préstamo.

Salidas en `proyecto_final/datos/`:
  S1_transacciones.csv, S2_ordenes.csv, S3_saldo_mensual.csv,
  distritos.csv (tabla para traducir el nombre del distrito a sus indicadores),
  diccionario_caracteristicas.json (campos del formulario, orden de X, rangos)
  resumen_datasets.json (limpieza, clases, partición y Hoeffding).
==============================================================================
"""

import json
import math
import sys
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]
DF_DIR = BASE_DIR / "dataframes"
OUT_DIR = Path(__file__).resolve().parent / "datos"
OUT_DIR.mkdir(parents=True, exist_ok=True)

SEMILLA = 42
DELTA = 0.05          # confianza 95 % en Hoeffding
EPS_OBJETIVO = 0.02   # margen deseado de ±2 puntos en la exactitud de prueba
MUESTRA_POR_CLASE_S1 = 6000
MUESTRA_POR_CLASE_S3 = 2000   # para las clases 1 y 2; la clase 3 usa todos sus casos

COLUMNAS_DISTRITO = ["poblacion", "salario_promedio", "tasa_desempleo", "tasa_criminalidad"]


# ----------------------------------------------------------------------------
# Utilidades
# ----------------------------------------------------------------------------
def normalizar_texto(texto):
    """Minúsculas, sin tildes y sin espacios repetidos (para comparar nombres)."""
    texto = unicodedata.normalize("NFKD", str(texto))
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return " ".join(texto.lower().split())


def n_test_hoeffding(eps, delta=DELTA):
    """Número mínimo de datos de prueba para que |Ê_out - E_out| <= eps con prob. 1 - delta."""
    return math.ceil(math.log(2 / delta) / (2 * eps**2))


def eps_hoeffding(n_test, delta=DELTA):
    """Margen eps que se garantiza con n_test datos de prueba."""
    return math.sqrt(math.log(2 / delta) / (2 * n_test))


def muestrear_por_clase(df, n_por_clase, conservar_completas=()):
    """Toma hasta n_por_clase filas de cada clase; las clases en conservar_completas van enteras."""
    partes = []
    for clase in sorted(df["clase"].unique()):
        g = df[df["clase"] == clase]
        if clase not in conservar_completas and len(g) > n_por_clase:
            g = g.sample(n=n_por_clase, random_state=SEMILLA)
        partes.append(g)
    return pd.concat(partes, ignore_index=True)


def particion_por_cuenta(y, cuentas, semilla=SEMILLA):
    """
    60/20/20 agrupado por cuenta y estratificado por clase: se arman 5 bloques
    de cuentas con la misma proporción de clases (3 de entrenamiento, 1 de
    validación y 1 de prueba). Ninguna cuenta aparece en dos particiones.
    """
    from sklearn.model_selection import StratifiedGroupKFold

    etiquetas = np.empty(len(y), dtype=object)
    bloques = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=semilla).split(
        np.zeros(len(y)), np.asarray(y), np.asarray(cuentas))
    for k, (_, idx) in enumerate(bloques):
        etiquetas[idx] = "entrenamiento" if k < 3 else ("validacion" if k == 3 else "prueba")
    return etiquetas


def particion_estratificada(y, semilla=SEMILLA, proporciones=(0.6, 0.2, 0.2)):
    """Devuelve un arreglo con 'entrenamiento' / 'validacion' / 'prueba' estratificado por clase."""
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


def limpiar(df, columnas_x, nombre):
    """Quita nulos y duplicados exactos en X + y; devuelve el df limpio y un reporte."""
    reporte = {"filas_iniciales": int(len(df))}
    reporte["nulos_por_columna"] = {c: int(v) for c, v in df[columnas_x].isna().sum().items() if v}
    df = df.dropna(subset=columnas_x + ["clase"])
    reporte["filas_tras_quitar_nulos"] = int(len(df))
    antes = len(df)
    df = df.drop_duplicates(subset=columnas_x + ["clase"])
    reporte["duplicados_eliminados"] = int(antes - len(df))
    # Una misma X con dos clases distintas es ruido irreducible: se informa, no se borra.
    conflictos = df.duplicated(subset=columnas_x, keep=False).sum()
    reporte["filas_con_X_repetida_y_clase_distinta"] = int(conflictos)
    reporte["filas_finales"] = int(len(df))
    print(f"      [{nombre}] limpieza: {reporte}")
    return df.reset_index(drop=True), reporte


def resumir(df, columnas_x, nombres_clase, reporte_limpieza, descripcion):
    conteo = df["clase"].value_counts().sort_index()
    n_prueba = int((df["particion"] == "prueba").sum())
    return {
        "descripcion": descripcion,
        "n_filas": int(len(df)),
        "n_caracteristicas": len(columnas_x),
        "caracteristicas": columnas_x,
        "clases": {nombres_clase[int(k)]: int(v) for k, v in conteo.items()},
        "clase_mayoritaria_prop": round(float(conteo.max() / conteo.sum()), 4),
        "clasificador_aleatorio_error": round((len(conteo) - 1) / len(conteo), 4),
        "particion": {p: int((df["particion"] == p).sum()) for p in ["entrenamiento", "validacion", "prueba"]},
        "hoeffding": {
            "delta": DELTA,
            "eps_objetivo": EPS_OBJETIVO,
            "n_test_minimo_para_eps_objetivo": n_test_hoeffding(EPS_OBJETIVO),
            "n_test_real": n_prueba,
            "eps_garantizado_con_n_test_real": round(eps_hoeffding(n_prueba), 4),
        },
        "limpieza": reporte_limpieza,
        "rangos_X": {
            c: {"min": float(df[c].min()), "max": float(df[c].max()), "media": round(float(df[c].mean()), 4)}
            for c in columnas_x
        },
    }


# ----------------------------------------------------------------------------
# Carga de los DataFrames del Data Mart
# ----------------------------------------------------------------------------
def cargar():
    print("Cargando DataFrames del Data Mart Kimball (carpeta dataframes/)...")
    distritos = pd.read_csv(DF_DIR / "df_distritos_clean.csv", encoding="utf-8-sig")
    distritos = distritos.rename(
        columns={"tasa_desempleo_1996": "tasa_desempleo", "tasa_criminalidad_1996": "tasa_criminalidad"}
    )[["id_distrito", "nombre_distrito", "region"] + COLUMNAS_DISTRITO]
    distritos["nombre_normalizado"] = distritos["nombre_distrito"].map(normalizar_texto)
    assert distritos["nombre_normalizado"].is_unique, "Hay nombres de distrito repetidos"

    clientes = pd.read_csv(DF_DIR / "df_cliente_consolidado_clean.csv", encoding="utf-8-sig")
    perfiles = pd.read_csv(DF_DIR / "rs_perfiles.csv", encoding="utf-8-sig")
    ordenes = pd.read_csv(DF_DIR / "df_ordenes_clean.csv", encoding="utf-8-sig")
    trans = pd.read_csv(DF_DIR / "df_transacciones_completado.csv.gz", encoding="utf-8-sig")
    prestamos = pd.read_csv(DF_DIR / "df_prestamos_clean.csv", encoding="utf-8-sig")
    return distritos, clientes, perfiles, ordenes, trans, prestamos


# ----------------------------------------------------------------------------
# S1. Tipo de transacción (4 clases)
# ----------------------------------------------------------------------------
NOMBRES_S1 = {
    0: "Depósito en efectivo",
    1: "Retiro (efectivo o tarjeta)",
    2: "Transferencia enviada",
    3: "Transferencia recibida",
}
X_S1 = [
    "monto", "saldo_despues", "anio", "mes", "dia", "dia_semana",
    "edad", "es_mujer",
] + COLUMNAS_DISTRITO


def construir_s1(trans, distritos):
    print("\n[S1] Tipo de transacción (Fact_Transacciones)")
    t = trans[~trans["k_symbol"].isin(["UROK", "SANKC. UROK"])].copy()
    mapa = {"VKLAD": 0, "VYBER": 1, "VYBER KARTOU": 1, "PREVOD NA UCET": 2, "PREVOD Z UCTU": 3}
    t["clase"] = t["operation"].map(mapa)
    t = t.dropna(subset=["clase"])
    t["clase"] = t["clase"].astype(int)
    print(f"      Movimientos con operación válida (sin intereses): {len(t):,}")
    print(f"      Población por clase: {t['clase'].value_counts().sort_index().to_dict()}")

    # Muestra balanceada: igual número de movimientos por clase
    t = muestrear_por_clase(t, MUESTRA_POR_CLASE_S1)
    t = t.merge(distritos[["id_distrito", "nombre_distrito"] + COLUMNAS_DISTRITO], on="id_distrito", how="left",
                suffixes=("_orig", ""))
    fecha = pd.to_datetime(t["fecha"])
    t["monto"] = t["monto_transaccion"].abs()          # sin signo: el signo delataría la clase
    t["saldo_despues"] = t["saldo_cuenta"]
    t["anio"], t["mes"], t["dia"] = fecha.dt.year, fecha.dt.month, fecha.dt.day
    t["dia_semana"] = fecha.dt.dayofweek               # 0 = lunes; se calcula de la fecha escrita
    t["edad"] = t["edad_cliente"]
    t["es_mujer"] = (t["sexo_cliente"] == "F").astype(int)
    t["fecha"] = fecha.dt.strftime("%Y-%m-%d")

    t = t[t["monto"] > 0]
    t, rep = limpiar(t, X_S1, "S1")
    t["particion"] = particion_por_cuenta(t["clase"].values, t["id_cuenta"].values)
    t["nombre_clase"] = t["clase"].map(NOMBRES_S1)
    cols = ["id_transaccion", "id_cuenta", "fecha", "nombre_distrito"] + X_S1 + ["clase", "nombre_clase", "particion"]
    t = t[cols]
    t.to_csv(OUT_DIR / "S1_transacciones.csv", index=False, encoding="utf-8")
    return resumir(t, X_S1, NOMBRES_S1, rep,
                   "Predice el tipo de un movimiento bancario nuevo a partir del monto, el saldo, la fecha y el cliente.")


# ----------------------------------------------------------------------------
# S2. Propósito de la orden permanente (4 clases)
# ----------------------------------------------------------------------------
NOMBRES_S2 = {
    0: "Hogar (SIPO)",
    1: "Préstamo (UVER)",
    2: "Seguro (POJISTNE)",
    3: "Arrendamiento (LEASING)",
}
X_S2 = [
    "monto_orden", "edad", "es_mujer",
    "tiene_prestamo", "cuota_prestamo", "ordenes_activas_cuenta",
    "saldo_promedio_cuenta", "deposito_mensual", "retiro_mensual",
] + COLUMNAS_DISTRITO


def construir_s2(ordenes, clientes, perfiles, distritos):
    print("\n[S2] Propósito de la orden permanente (Fact_Ordenes)")
    o = ordenes.copy()
    o["k"] = o["k_symbol"].fillna("").str.strip()
    mapa = {"SIPO": 0, "UVER": 1, "POJISTNE": 2, "LEASING": 3}
    print(f"      Órdenes sin propósito (excluidas, no tienen y verdadera): {(~o['k'].isin(mapa)).sum():,}")
    o = o[o["k"].isin(mapa)].copy()
    o["clase"] = o["k"].map(mapa).astype(int)

    cli = clientes[["id_cliente", "tiene_prestamo", "cuota_mensual_prestamo", "total_ordenes_activas"]]
    per = perfiles[["id_cuenta", "saldo_promedio", "deposito_mensual", "retiro_mensual"]]
    o = (
        o.merge(cli, on="id_cliente", how="left")
        .merge(per, on="id_cuenta", how="left")
        .merge(distritos[["id_distrito"] + COLUMNAS_DISTRITO], on="id_distrito", how="left")
    )
    o["edad"] = o["edad_cliente"]
    o["es_mujer"] = (o["sexo_cliente"] == "F").astype(int)
    o["cuota_prestamo"] = o["cuota_mensual_prestamo"].fillna(0.0)
    o["tiene_prestamo"] = o["tiene_prestamo"].fillna(0).astype(int)
    o["ordenes_activas_cuenta"] = o["total_ordenes_activas"]
    o["saldo_promedio_cuenta"] = o["saldo_promedio"]

    o, rep = limpiar(o, X_S2, "S2")
    o["particion"] = particion_por_cuenta(o["clase"].values, o["id_cuenta"].values)
    o["nombre_clase"] = o["clase"].map(NOMBRES_S2)
    cols = ["id_orden", "id_cuenta", "nombre_distrito"] + X_S2 + ["clase", "nombre_clase", "particion"]
    o = o[cols]
    o.to_csv(OUT_DIR / "S2_ordenes.csv", index=False, encoding="utf-8")
    return resumir(o, X_S2, NOMBRES_S2, rep,
                   "Predice para qué es una orden de pago permanente nueva (hogar, préstamo, seguro o arrendamiento).")


# ----------------------------------------------------------------------------
# S3. Estado del saldo el mes siguiente (3 clases)
# ----------------------------------------------------------------------------
NOMBRES_S3 = {
    0: "Saldo estable o creciente",
    1: "Caída de saldo sin sobregiro",
    2: "Sobregiro",
}
X_S3 = [
    "anio", "mes", "saldo_fin_mes", "saldo_promedio_mes", "saldo_min_mes", "saldo_max_mes",
    "cambio_saldo_mes", "num_movimientos_mes", "monto_medio_mov",
    "edad", "es_mujer",
] + COLUMNAS_DISTRITO


def construir_s3(trans, perfiles, clientes, distritos):
    print("\n[S3] Estado del saldo el mes siguiente (Fact_Saldo_Cuenta_Mensual)")
    tr = trans[["id_transaccion", "id_cuenta", "fecha", "monto_transaccion", "saldo_cuenta"]].copy()
    tr["fecha_dt"] = pd.to_datetime(tr["fecha"])
    tr = tr.sort_values(["id_cuenta", "fecha_dt", "id_transaccion"])
    tr["mes_per"] = tr["fecha_dt"].dt.to_period("M")
    g = tr.groupby(["id_cuenta", "mes_per"])
    mensual = pd.DataFrame({
        "saldo_fin_mes": g["saldo_cuenta"].last(),
        "saldo_promedio_mes": g["saldo_cuenta"].mean(),
        "saldo_min_mes": g["saldo_cuenta"].min(),
        "saldo_max_mes": g["saldo_cuenta"].max(),
        "num_movimientos_mes": g.size(),
        "monto_medio_mov": g["monto_transaccion"].apply(lambda s: s.abs().mean()),
    }).reset_index()

    # Foto mensual completa: cada cuenta desde su primer mes hasta diciembre de 1998
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

    # Etiqueta verdadera del mes t+1 (se observa en los datos; nunca entra en X)
    sig = m.groupby("id_cuenta")["saldo_fin_mes"].shift(-1)
    m = m[sig.notna()].copy()
    sig = sig[sig.notna()]
    m["clase"] = np.where(sig < 0, 2, np.where(sig - m["saldo_fin_mes"] < 0, 1, 0)).astype(int)
    m["anio"] = m["mes_per"].dt.year.astype(int)
    m["mes"] = m["mes_per"].dt.month.astype(int)
    print(f"      Meses cuenta x mes con mes siguiente: {len(m):,}")
    print(f"      Población por clase: {m['clase'].value_counts().sort_index().to_dict()}")

    titulares = clientes[clientes["es_titular"] == 1][["id_cliente", "id_distrito"]]
    ctx = perfiles[["id_cuenta", "id_cliente", "sexo", "edad_corte"]].merge(titulares, on="id_cliente", how="left")
    ctx = ctx.merge(distritos[["id_distrito", "nombre_distrito"] + COLUMNAS_DISTRITO], on="id_distrito", how="left")
    m = m.merge(ctx, on="id_cuenta", how="left")
    m["edad"] = m["edad_corte"]
    m["es_mujer"] = (m["sexo"] == "F").astype(int)

    # Muestra: todos los meses que terminan en sobregiro y 2,000 de cada una de las otras clases
    m = muestrear_por_clase(m, MUESTRA_POR_CLASE_S3, conservar_completas=(2,))
    m, rep = limpiar(m, X_S3, "S3")
    m["particion"] = particion_por_cuenta(m["clase"].values, m["id_cuenta"].values)
    m["nombre_clase"] = m["clase"].map(NOMBRES_S3)
    m["periodo"] = m["mes_per"].astype(str)
    cols = ["id_cuenta", "periodo", "nombre_distrito"] + X_S3 + ["clase", "nombre_clase", "particion"]
    m = m[cols]
    m.to_csv(OUT_DIR / "S3_saldo_mensual.csv", index=False, encoding="utf-8")
    return resumir(m, X_S3, NOMBRES_S3, rep,
                   "Predice si el saldo de una cuenta el próximo mes se mantendrá, caerá o quedará en sobregiro.")


# ----------------------------------------------------------------------------
# S4. Mora al corte (31/12/1998) de un préstamo (2 clases)
# ----------------------------------------------------------------------------
NOMBRES_S4 = {
    0: "Al día al corte (A o C)",
    1: "En mora o impago al corte (B o D)",
}
X_S4 = [
    "monto_prestamo", "plazo_meses", "cuota_mensual", "ratio_cuota_saldo",
    "saldo_promedio_previo", "saldo_minimo_previo", "ingreso_mensual", "egreso_mensual",
    "movimientos_mes", "meses_historial", "edad", "es_mujer",
] + COLUMNAS_DISTRITO


def construir_s4(prestamos, trans, distritos):
    print("\n[S4] Mora al corte (31/12/1998) de un préstamo (Fact_Prestamos)")
    p = prestamos.copy()
    p["clase"] = p["estado_prestamo"].isin(["B", "D"]).astype(int)
    p["fecha_otorgamiento"] = pd.to_datetime(p["fecha_otorgamiento"])

    # Historial de la cuenta ANTES de la fecha del préstamo (lo que el banco ve al aprobarlo)
    t = trans[trans["id_cuenta"].isin(p["id_cuenta"])][
        ["id_cuenta", "fecha", "monto_transaccion", "saldo_cuenta", "tipo_transaccion"]
    ].merge(p[["id_cuenta", "fecha_otorgamiento"]], on="id_cuenta")
    t["fecha"] = pd.to_datetime(t["fecha"])
    t = t[t["fecha"] < t["fecha_otorgamiento"]]
    t["ingreso"] = np.where(t["tipo_transaccion"] == "PRIJEM", t["monto_transaccion"].abs(), 0.0)
    t["egreso"] = np.where(t["tipo_transaccion"] != "PRIJEM", t["monto_transaccion"].abs(), 0.0)
    t["mes"] = t["fecha"].dt.to_period("M")
    g = t.groupby("id_cuenta")
    meses = g["mes"].nunique()
    previo = pd.DataFrame({
        "saldo_minimo_previo": g["saldo_cuenta"].min(),
        "ingreso_mensual": g["ingreso"].sum() / meses,
        "egreso_mensual": g["egreso"].sum() / meses,
        "movimientos_mes": g.size() / meses,
        "meses_historial": meses,
    }).reset_index()
    p = p.merge(previo, on="id_cuenta", how="left")
    p = p.merge(distritos[["id_distrito"] + COLUMNAS_DISTRITO], on="id_distrito", how="left")

    # La cuota sale del monto y el plazo (en la fuente monto = cuota x plazo):
    # en el formulario solo se piden monto y plazo, y la cuota se calcula.
    p["cuota_mensual"] = p["monto_prestamo"] / p["plazo_meses"]
    p["ratio_cuota_saldo"] = p["cuota_mensual"] / p["saldo_promedio_previo"]
    p["edad"] = p["edad_cliente"]
    p["es_mujer"] = (p["sexo_cliente"] == "F").astype(int)

    p, rep = limpiar(p, X_S4, "S4")
    p["particion"] = particion_estratificada(p["clase"].values)
    p["nombre_clase"] = p["clase"].map(NOMBRES_S4)
    p["estado_original"] = p["estado_prestamo"]
    cols = ["id_prestamo", "id_cuenta", "nombre_distrito", "estado_original"] + X_S4 + ["clase", "nombre_clase", "particion"]
    p = p[cols]
    p.to_csv(OUT_DIR / "S4_prestamos.csv", index=False, encoding="utf-8")
    return resumir(p, X_S4, NOMBRES_S4, rep,
                   "Estima si un préstamo estaría en mora o impago al corte del 31/12/1998 según el monto, el plazo y el "
                   "historial previo de la cuenta. Los préstamos vigentes al día (C) podrían caer en mora después del corte.")


# ----------------------------------------------------------------------------
# Diccionario del formulario: qué escribe el usuario y cómo se convierte en X
# ----------------------------------------------------------------------------
def diccionario():
    distrito = {
        "campo": "distrito", "etiqueta": "Distrito (ciudad) del cliente", "tipo": "texto",
        "genera": COLUMNAS_DISTRITO,
        "regla": "Se escribe el nombre; se compara sin tildes ni mayúsculas con los 77 distritos de distritos.csv.",
    }
    sexo = {"campo": "sexo", "etiqueta": "Sexo (M/F)", "tipo": "texto", "genera": ["es_mujer"],
            "regla": "F -> 1, M -> 0"}
    edad = {"campo": "edad", "etiqueta": "Edad (años)", "tipo": "entero", "genera": ["edad"]}
    return {
        "S1": {"titulo": "Tipo de transacción", "orden_X": X_S1, "clases": NOMBRES_S1, "campos": [
            {"campo": "monto", "etiqueta": "Monto del movimiento", "tipo": "decimal", "genera": ["monto"],
             "regla": "Valor absoluto"},
            {"campo": "saldo_despues", "etiqueta": "Saldo de la cuenta después del movimiento", "tipo": "decimal",
             "genera": ["saldo_despues"]},
            {"campo": "fecha", "etiqueta": "Fecha (AAAA-MM-DD)", "tipo": "fecha",
             "genera": ["anio", "mes", "dia", "dia_semana"]},
            edad, sexo, distrito]},
        "S2": {"titulo": "Propósito de la orden permanente", "orden_X": X_S2, "clases": NOMBRES_S2, "campos": [
            {"campo": "monto_orden", "etiqueta": "Monto mensual de la orden", "tipo": "decimal", "genera": ["monto_orden"]},
            edad, sexo,
            {"campo": "tiene_prestamo", "etiqueta": "¿La cuenta tiene préstamo en el banco? (si/no)", "tipo": "texto",
             "genera": ["tiene_prestamo"], "regla": "si -> 1, no -> 0"},
            {"campo": "cuota_prestamo", "etiqueta": "Cuota mensual del préstamo (0 si no tiene)", "tipo": "decimal",
             "genera": ["cuota_prestamo"]},
            {"campo": "ordenes_activas_cuenta", "etiqueta": "Órdenes permanentes activas de la cuenta",
             "tipo": "entero", "genera": ["ordenes_activas_cuenta"]},
            {"campo": "saldo_promedio_cuenta", "etiqueta": "Saldo promedio de la cuenta", "tipo": "decimal",
             "genera": ["saldo_promedio_cuenta"]},
            {"campo": "deposito_mensual", "etiqueta": "Depósito mensual promedio", "tipo": "decimal",
             "genera": ["deposito_mensual"]},
            {"campo": "retiro_mensual", "etiqueta": "Retiro mensual promedio", "tipo": "decimal",
             "genera": ["retiro_mensual"]},
            distrito]},
        "S3": {"titulo": "Estado del saldo el mes siguiente", "orden_X": X_S3, "clases": NOMBRES_S3, "campos": [
            {"campo": "periodo", "etiqueta": "Mes evaluado (AAAA-MM)", "tipo": "periodo", "genera": ["anio", "mes"]},
            {"campo": "saldo_fin_mes", "etiqueta": "Saldo al cierre del mes", "tipo": "decimal", "genera": ["saldo_fin_mes"]},
            {"campo": "saldo_promedio_mes", "etiqueta": "Saldo promedio del mes", "tipo": "decimal",
             "genera": ["saldo_promedio_mes"]},
            {"campo": "saldo_min_mes", "etiqueta": "Saldo mínimo del mes", "tipo": "decimal", "genera": ["saldo_min_mes"]},
            {"campo": "saldo_max_mes", "etiqueta": "Saldo máximo del mes", "tipo": "decimal", "genera": ["saldo_max_mes"]},
            {"campo": "cambio_saldo_mes", "etiqueta": "Cambio del saldo frente al mes anterior", "tipo": "decimal",
             "genera": ["cambio_saldo_mes"]},
            {"campo": "num_movimientos_mes", "etiqueta": "Número de movimientos del mes", "tipo": "entero",
             "genera": ["num_movimientos_mes"]},
            {"campo": "monto_medio_mov", "etiqueta": "Monto medio por movimiento", "tipo": "decimal",
             "genera": ["monto_medio_mov"]},
            edad, sexo, distrito]},
        "S4": {"titulo": "Mora al corte (31/12/1998) de un préstamo", "orden_X": X_S4, "clases": NOMBRES_S4, "campos": [
            {"campo": "monto_prestamo", "etiqueta": "Monto solicitado", "tipo": "decimal", "genera": ["monto_prestamo"]},
            {"campo": "plazo_meses", "etiqueta": "Plazo en meses", "tipo": "entero",
             "genera": ["plazo_meses", "cuota_mensual", "ratio_cuota_saldo"],
             "regla": "cuota = monto / plazo; ratio = cuota / saldo promedio previo"},
            {"campo": "saldo_promedio_previo", "etiqueta": "Saldo promedio de la cuenta antes del préstamo",
             "tipo": "decimal", "genera": ["saldo_promedio_previo"]},
            {"campo": "saldo_minimo_previo", "etiqueta": "Saldo mínimo de la cuenta antes del préstamo",
             "tipo": "decimal", "genera": ["saldo_minimo_previo"]},
            {"campo": "ingreso_mensual", "etiqueta": "Ingreso mensual promedio de la cuenta", "tipo": "decimal",
             "genera": ["ingreso_mensual"]},
            {"campo": "egreso_mensual", "etiqueta": "Egreso mensual promedio de la cuenta", "tipo": "decimal",
             "genera": ["egreso_mensual"]},
            {"campo": "movimientos_mes", "etiqueta": "Movimientos por mes", "tipo": "decimal",
             "genera": ["movimientos_mes"]},
            {"campo": "meses_historial", "etiqueta": "Meses de historial de la cuenta", "tipo": "entero",
             "genera": ["meses_historial"]},
            edad, sexo, distrito]},
    }


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    distritos, clientes, perfiles, ordenes, trans, prestamos = cargar()
    resumen = {
        "semilla": SEMILLA,
        "particion": "60/20/20 estratificada (entrenamiento/validacion/prueba)",
        "hoeffding_formula": "N_test >= ln(2/delta) / (2*eps^2)",
        "S1": construir_s1(trans, distritos),
        "S2": construir_s2(ordenes, clientes, perfiles, distritos),
        "S3": construir_s3(trans, perfiles, clientes, distritos),
        "S4": construir_s4(prestamos, trans, distritos),
    }
    distritos.drop(columns="nombre_normalizado").to_csv(OUT_DIR / "distritos.csv", index=False, encoding="utf-8")
    with open(OUT_DIR / "resumen_datasets.json", "w", encoding="utf-8") as f:
        json.dump(resumen, f, ensure_ascii=False, indent=2)
    with open(OUT_DIR / "diccionario_caracteristicas.json", "w", encoding="utf-8") as f:
        json.dump(diccionario(), f, ensure_ascii=False, indent=2)

    print("\nResumen:")
    for s in ["S1", "S2", "S3", "S4"]:
        r = resumen[s]
        h = r["hoeffding"]
        print(f"  {s}: {r['n_filas']:,} filas, {r['n_caracteristicas']} X, clases {r['clases']}, "
              f"prueba {h['n_test_real']:,} -> eps = ±{h['eps_garantizado_con_n_test_real']:.3f} (95 %)")
    print(f"\nArchivos en: {OUT_DIR.relative_to(BASE_DIR)}")


if __name__ == "__main__":
    main()
