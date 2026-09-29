"""
==============================================================================
UNIVERSIDAD TÉCNICA DE AMBATO - Inteligencia de Negocios
AUTORES: Alison Marcela Cobos Taco / Henry Daniel Lagua Flores
==============================================================================
ARCHIVO: 37_rs_preparacion.py
SISTEMAS DE RECOMENDACIÓN (Informe 04 v2) — PUNTOS 1 A 4 DE LA CONSIGNA
DESCRIPCIÓN: A partir de los DataFrames que salen del Data Mart Kimball
             (scripts 32 y 33), organiza, clasifica y filtra la información
             para los recomendadores:
               * Catálogo de 8 productos que el cliente elige tener, definido
                 con los datos (no inventado).
               * Unidad de análisis: la cuenta y su titular (4,500).
               * Matriz de adopción cuenta x producto (binaria).
               * Matriz de intensidad: monto mensual por producto, escalado
                 a un rating 1-5 con logaritmo (Slope One, coseno ajustado).
               * Perfiles de titulares (demografía y comportamiento) y
                 atributos de los productos (para el modelo de contenidos).
SALIDAS: dataframes/rs_adopcion.csv, rs_ratings.csv, rs_perfiles.csv,
         rs_productos.csv y la sección "preparacion" de metricas_recomendadores.json
USO: python scripts/37_rs_preparacion.py
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
CORTE = pd.Timestamp("1998-12-31")

# Catálogo: servicios que el cliente decide tener. Se excluyen los universales (depósito y retiro
# en efectivo: 100% de las cuentas, no discriminan) y los cargos o abonos automáticos del banco.
PRODUCTOS = {
    "SERVICIOS_HOGAR": "Pago domiciliado de servicios del hogar (SIPO)",
    "TRANSF_SALIENTE": "Transferencias salientes a otros bancos",
    "INGRESO_TRANSF": "Ingresos recibidos por transferencia",
    "RETIRO_TARJETA": "Retiros con tarjeta en cajero",
    "PENSION": "Abono de pensión (DUCHOD)",
    "PRESTAMO": "Préstamo del banco",
    "SEGURO": "Pago de pólizas de seguro (POJISTNE)",
    "LEASING": "Orden permanente de leasing",
}


def cargar_json():
    return json.load(open(METRICAS, encoding="utf-8")) if os.path.exists(METRICAS) else {}


def macro_region(r):
    return "Praga" if r == "Prague" else ("Bohemia" if "Bohemia" in r else "Moravia")


def main():
    print("=" * 78 + "\nSISTEMAS DE RECOMENDACIÓN — PREPARACIÓN (puntos 1 a 4)\n" + "=" * 78)
    t = pd.read_csv(os.path.join(DF, "df_transacciones_completado.csv.gz"),
                    usecols=["id_cuenta", "id_cliente", "fecha", "tipo_transaccion", "operation", "k_symbol",
                             "canal", "tipo_contraparte", "metodo_concepto", "monto_transaccion", "saldo_cuenta"])
    o = pd.read_csv(os.path.join(DF, "df_ordenes_clean.csv"))
    p = pd.read_csv(os.path.join(DF, "df_prestamos_clean.csv"))
    c = pd.read_csv(os.path.join(DF, "df_cliente_consolidado_clean.csv"))
    t["fecha"] = pd.to_datetime(t.fecha)
    res = {"punto_1_dataframes": {
        "df_transacciones_completado": len(t), "df_ordenes_clean": len(o), "df_prestamos_clean": len(p),
        "df_cliente_consolidado_clean": len(c)}}

    # ---------------- PUNTO 2: ORGANIZAR — unidad cuenta/titular y meses de vida ----------------
    titulares = c[c.es_titular == 1][["id_cliente", "sexo", "edad_corte", "region", "salario_promedio",
                                      "tasa_desempleo", "calificacion_pago"]]
    vida = t.groupby("id_cuenta").agg(id_cliente=("id_cliente", "first"), primera=("fecha", "min"))
    vida["meses_vida"] = ((CORTE - vida.primera).dt.days / 30.4375).round(2)
    cuentas = vida.reset_index().merge(titulares, on="id_cliente", how="left")
    res["punto_2_organizar"] = {
        "unidad": "cuenta con su titular (OWNER)", "cuentas": len(cuentas),
        "cotitulares_excluidos": int((c.es_titular == 0).sum()),
        "meses_vida": {k: round(float(v), 1) for k, v in cuentas.meses_vida.describe()[["min", "50%", "max"]].items()}}

    # ---------------- PUNTO 3: CLASIFICAR — cada transacción u orden en un producto ----------------
    t["producto"] = None
    t.loc[t.k_symbol == "SIPO", "producto"] = "SERVICIOS_HOGAR"
    t.loc[t.k_symbol == "TRANSFERENCIA_EXTERNA", "producto"] = "TRANSF_SALIENTE"
    t.loc[t.k_symbol == "INGRESO_ORDINARIO", "producto"] = "INGRESO_TRANSF"
    t.loc[t.operation == "VYBER KARTOU", "producto"] = "RETIRO_TARJETA"
    t.loc[t.k_symbol == "DUCHOD", "producto"] = "PENSION"
    t.loc[t.k_symbol == "POJISTNE", "producto"] = "SEGURO"
    clasif = t.producto.fillna("NO_ES_PRODUCTO").value_counts().to_dict()
    no_producto = t[t.producto.isna()].k_symbol.value_counts().to_dict()

    # Monto mensual por cuenta y producto
    mov = t.dropna(subset=["producto"]).groupby(["id_cuenta", "producto"]).agg(
        movimientos=("monto_transaccion", "size"), monto=("monto_transaccion", "sum")).reset_index()
    mov = mov.merge(vida[["meses_vida"]], left_on="id_cuenta", right_index=True)
    mov["monto_mensual"] = mov.monto / mov.meses_vida
    prest = p[["id_cuenta", "pago_mensual"]].rename(columns={"pago_mensual": "monto_mensual"}).assign(producto="PRESTAMO", movimientos=np.nan)
    leas = o[o.k_symbol == "LEASING"].groupby("id_cuenta").monto_orden.sum().rename("monto_mensual").reset_index().assign(
        producto="LEASING", movimientos=np.nan)
    uso = pd.concat([mov[["id_cuenta", "producto", "movimientos", "monto_mensual"]], prest, leas], ignore_index=True)
    uso = uso[uso.monto_mensual > 0]

    # ---------------- PUNTO 4: FILTRAR — asimetría, escala logarítmica y rating 1-5 ----------------
    asimetria_bruta = float(stats.skew(uso.monto_mensual))
    uso["log_monto"] = np.log1p(uso.monto_mensual)
    asimetria_log = float(stats.skew(uso.log_monto))
    lmin, lmax = uso.log_monto.min(), uso.log_monto.max()
    uso["rating"] = (1 + 4 * (uso.log_monto - lmin) / (lmax - lmin)).round(4)
    adop = (uso.pivot_table(index="id_cuenta", columns="producto", values="rating", aggfunc="size").reindex(
        index=cuentas.id_cuenta, columns=list(PRODUCTOS)).notna().astype(int))
    n_prod = adop.sum(axis=1)
    dispersion = 1 - adop.values.sum() / adop.size

    res["punto_3_clasificar"] = {
        "productos": PRODUCTOS,
        "transacciones_por_clase": {k: int(v) for k, v in clasif.items()},
        "conceptos_que_no_son_producto": {k: int(v) for k, v in no_producto.items()},
        "motivo_exclusion": {"DEPOSITO_EFECTIVO / RETIRO_EFECTIVO": "Los usan las 4,500 cuentas: no distinguen a nadie",
                             "UROK / SLUZBY / SANKC. UROK": "Los genera el banco automáticamente, no los elige el cliente",
                             "UVER": "Es la cuota del préstamo: el producto PRESTAMO se toma de loans"},
        "cuentas_por_producto": {k: int(v) for k, v in adop.sum().sort_values(ascending=False).items()},
    }
    res["punto_4_filtrar"] = {
        "celdas_observadas": int(adop.values.sum()), "celdas_posibles": int(adop.size),
        "dispersion": round(float(dispersion), 4),
        "asimetria_monto_mensual_bruto": round(asimetria_bruta, 3), "asimetria_tras_log": round(asimetria_log, 3),
        "escala_rating": {"formula": "1 + 4 * (ln(1+monto) - min) / (max - min)",
                          "ln_min": round(float(lmin), 4), "ln_max": round(float(lmax), 4)},
        "cuentas_por_numero_de_productos": {int(k): int(v) for k, v in n_prod.value_counts().sort_index().items()},
        "cuentas_con_2_o_mas_productos": int((n_prod >= 2).sum()),
        "monto_mensual_mediano_por_producto": {k: round(float(v), 2) for k, v in uso.groupby("producto").monto_mensual.median().items()},
    }

    # ---------------- Perfiles de titulares (demografía y comportamiento, sin productos) ----------------
    deposito = t[t.k_symbol == "DEPOSITO_EFECTIVO"].groupby("id_cuenta").monto_transaccion.sum()
    # Solo retiros en ventanilla: los retiros con tarjeta (VYBER KARTOU) son el producto RETIRO_TARJETA
    retiro = t[(t.k_symbol == "RETIRO_EFECTIVO") & (t.operation != "VYBER KARTOU")].groupby("id_cuenta").monto_transaccion.sum()
    saldo = t.groupby("id_cuenta").saldo_cuenta.mean()
    sobregiro = t[t.k_symbol == "SANKC. UROK"].groupby("id_cuenta").size()
    perf = cuentas.set_index("id_cuenta")
    perf["macro_region"] = perf.region.map(macro_region)
    perf["segmento_edad"] = pd.cut(perf.edad_corte, [0, 30, 50, 120], right=False,
                                   labels=["Joven (<30)", "Adulto (30-50)", "Adulto Mayor (>50)"]).astype(str)
    perf["arquetipo"] = perf.macro_region + " - " + perf.segmento_edad
    perf["deposito_mensual"] = (deposito / perf.meses_vida).reindex(perf.index).fillna(0).round(2)
    perf["retiro_mensual"] = (retiro / perf.meses_vida).reindex(perf.index).fillna(0).round(2)
    perf["saldo_promedio"] = saldo.reindex(perf.index).round(2)
    perf["sanciones_sobregiro"] = sobregiro.reindex(perf.index).fillna(0).astype(int)
    perf = perf[["id_cliente", "sexo", "edad_corte", "region", "macro_region", "segmento_edad", "arquetipo",
                 "salario_promedio", "tasa_desempleo", "meses_vida", "deposito_mensual", "retiro_mensual",
                 "saldo_promedio", "sanciones_sobregiro", "calificacion_pago"]]

    # ---------------- Atributos de los productos (modelo de contenidos) ----------------
    item = []
    for prod, desc in PRODUCTOS.items():
        u = uso[uso.producto == prod]
        if prod in ("PRESTAMO", "LEASING"):
            canal, contraparte, direccion, regularidad = "Orden o contrato", "Banco" if prod == "PRESTAMO" else "Entidad externa registrada", "Salida", 1.0
        else:
            filas = t[t.producto == prod]
            canal = filas.canal.mode()[0]
            contraparte = filas.tipo_contraparte.mode()[0]
            direccion = "Entrada" if filas.tipo_transaccion.iloc[0] == "PRIJEM" else "Salida"
            # regularidad: fracción de meses de vida con al menos un movimiento del producto
            m = filas.assign(mes=filas.fecha.dt.to_period("M")).groupby("id_cuenta").mes.nunique()
            regularidad = float((m / vida.meses_vida.reindex(m.index)).clip(upper=1).median())
        item.append({"producto": prod, "descripcion": desc, "direccion": direccion, "canal": canal,
                     "contraparte": contraparte, "es_credito": int(prod in ("PRESTAMO", "LEASING")),
                     "es_recurrente_fijo": int(prod in ("SERVICIOS_HOGAR", "PENSION", "PRESTAMO", "SEGURO", "LEASING")),
                     "regularidad_mensual": round(regularidad, 3), "monto_mensual_mediano": round(float(u.monto_mensual.median()), 2),
                     "cuentas": int(adop[prod].sum()), "penetracion": round(float(adop[prod].mean()), 4)})
    items = pd.DataFrame(item)
    res["productos"] = items.set_index("producto").to_dict(orient="index")

    adop.reset_index().to_csv(os.path.join(DF, "rs_adopcion.csv"), index=False, encoding="utf-8-sig")
    uso.to_csv(os.path.join(DF, "rs_ratings.csv"), index=False, encoding="utf-8-sig")
    perf.reset_index().to_csv(os.path.join(DF, "rs_perfiles.csv"), index=False, encoding="utf-8-sig")
    items.to_csv(os.path.join(DF, "rs_productos.csv"), index=False, encoding="utf-8-sig")

    metricas = cargar_json()
    metricas["preparacion"] = res
    json.dump(metricas, open(METRICAS, "w", encoding="utf-8"), ensure_ascii=False, indent=2, default=str)
    for k, v in res.items():
        print(f"\n{k}: {json.dumps(v, ensure_ascii=False, default=str)[:600]}")
    print(f"\nSalidas en dataframes/rs_*.csv y {METRICAS}")


if __name__ == "__main__":
    main()
