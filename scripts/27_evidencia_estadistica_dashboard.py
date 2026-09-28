"""
==============================================================================
UNIVERSIDAD TÉCNICA DE AMBATO - Inteligencia de Negocios
AUTORES: Alison Marcela Cobos Taco / Henry Daniel Lagua Flores
==============================================================================
ARCHIVO: 27_evidencia_estadistica_dashboard.py
DESCRIPCIÓN: Reproduce TODAS las cifras y pruebas estadísticas que se citan en
             los dashboards de Power BI (guía 07). Usa solo los DataFrames del
             repositorio, por lo que cualquier persona puede verificarlas sin
             SQL Server ni MongoDB.
SALIDA:      metricas_dashboard_07.json + resumen en consola.
USO:         python scripts/27_evidencia_estadistica_dashboard.py
==============================================================================
"""
import json
import os

import numpy as np
import pandas as pd
from scipy import stats

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DF = os.path.join(BASE_DIR, "dataframes")
SALIDA = os.path.join(BASE_DIR, "metricas_dashboard_07.json")


def macro_region(region):
    if region == "Prague":
        return "Praga"
    return "Moravia" if "Moravia" in region else "Bohemia"


def segmento_edad(edad):
    if edad <= 25:
        return "Joven (<=25)"
    if edad <= 40:
        return "Adulto joven (26-40)"
    if edad <= 60:
        return "Adulto (41-60)"
    return "Mayor (>60)"


def tasa_con_error(df, grupo, positivo, universo):
    """Tasa de una categoría con error estándar binomial sqrt(p(1-p)/n)."""
    base = df[df["estado_prestamo"].isin(universo)]
    g = base.groupby(grupo)["estado_prestamo"].agg(
        n="size", casos=lambda s: (s == positivo).sum())
    g["tasa"] = g["casos"] / g["n"]
    g["error_estandar"] = np.sqrt(g["tasa"] * (1 - g["tasa"]) / g["n"])
    return g


def chi2(tabla):
    est, p, gl, esperados = stats.chi2_contingency(tabla)
    return {"chi2": round(float(est), 4), "gl": int(gl), "p_valor": round(float(p), 4),
            "celdas_esperado_menor_5": int((esperados < 5).sum()), "celdas": int(esperados.size)}


def main():
    p = pd.read_csv(os.path.join(DF, "df_prestamos.csv"))
    o = pd.read_csv(os.path.join(DF, "df_ordenes_clean.csv"))
    c = pd.read_csv(os.path.join(DF, "df_cliente_consolidado_clean.csv"))
    t = pd.read_csv(os.path.join(DF, "df_transacciones_completado.csv.gz"),
                    usecols=["id_transaccion", "id_cuenta", "fecha", "anio",
                             "tipo_operacion_traducido", "monto_transaccion", "saldo_cuenta"])
    p["macro_region"] = p["region"].map(macro_region)
    p["segmento_edad"] = p["edad_cliente"].map(segmento_edad)
    r = {}

    # ---------------- Cabeceras (valores de control) ----------------
    saldo = (t.sort_values(["fecha", "id_transaccion"])
              .groupby("id_cuenta")["saldo_cuenta"].last().sum())
    r["kpi"] = {
        "cartera_total": float(p["monto_prestamo"].sum()),
        "num_prestamos": int(len(p)),
        "prestamos_mora_D": int((p["estado_prestamo"] == "D").sum()),
        "tasa_mora_vigente": round((p["estado_prestamo"] == "D").sum()
                                   / p["estado_prestamo"].isin(["C", "D"]).sum(), 4),
        "tasa_incumplimiento": round((p["estado_prestamo"] == "B").sum()
                                     / p["estado_prestamo"].isin(["A", "B"]).sum(), 4),
        "saldo_depositos": float(saldo),
        "ratio_absorcion": round(p["monto_prestamo"].sum() / saldo, 4),
        "volumen_transaccionado": float(t["monto_transaccion"].sum()),
        "num_transacciones": int(len(t)),
        "ticket_promedio_transaccion": round(float(t["monto_transaccion"].mean()), 2),
        "compromiso_ordenes": float(o["monto_orden"].sum()),
        "num_ordenes": int(len(o)),
        "monto_en_riesgo_BD": float(p.loc[p["estado_prestamo"].isin(["B", "D"]),
                                          "saldo_pendiente_estimado"].sum()),
        "clientes_con_impago_B": int(p.loc[p["estado_prestamo"] == "B", "id_cliente"].nunique()),
        "clientes_totales": int(len(c)),
    }

    # ---------------- P1: evolución por año (todas las categorías) ----------------
    r["p1_estado_por_anio"] = pd.crosstab(p["anio_otorgamiento"], p["estado_prestamo"]).to_dict(orient="index")
    mora_anio = tasa_con_error(p, "anio_otorgamiento", "D", ["C", "D"])
    r["p1_tasa_mora_por_cosecha"] = mora_anio.round(4).to_dict(orient="index")
    v = p[p["estado_prestamo"].isin(["C", "D"]) & p["anio_otorgamiento"].between(1994, 1997)]
    r["p1_chi2_mora_vs_cosecha_1994_1997"] = chi2(pd.crosstab(v["anio_otorgamiento"], v["estado_prestamo"]))

    # ---------------- P2: riesgo geográfico ----------------
    r["p2_tasa_mora_region"] = tasa_con_error(p, "region", "D", ["C", "D"]).round(4).to_dict(orient="index")
    v = p[p["estado_prestamo"].isin(["C", "D"])]
    r["p2_chi2_mora_vs_region"] = chi2(pd.crosstab(v["region"], v["estado_prestamo"]))
    r["p2_chi2_mora_vs_macro_region"] = chi2(pd.crosstab(v["macro_region"], v["estado_prestamo"]))

    def fisher(a, b):
        fila = lambda reg: [int(((v["region"] == reg) & (v["estado_prestamo"] == e)).sum()) for e in ("D", "C")]
        _, pv = stats.fisher_exact([fila(a), fila(b)])
        return round(float(pv), 4)
    r["p2_fisher_north_moravia_vs"] = {b: fisher("north Moravia", b) for b in
                                       ["north Bohemia", "south Moravia", "Prague", "east Bohemia"]}

    g = p.groupby("macro_region")["monto_prestamo"]
    r["p2_monto_por_macro_region"] = pd.DataFrame({
        "n": g.size(), "media": g.mean(), "desv_est": g.std(),
        "error_estandar": g.std() / np.sqrt(g.size())}).round(2).to_dict(orient="index")
    grupos = [s.values for _, s in g]
    r["p2_anova_monto_macro_region"] = {"F": round(float(stats.f_oneway(*grupos).statistic), 4),
                                        "p_valor": round(float(stats.f_oneway(*grupos).pvalue), 4),
                                        "kruskal_p": round(float(stats.kruskal(*grupos).pvalue), 4)}
    tm = p.groupby(["region", "nombre_distrito"])["monto_prestamo"].sum()
    r["p2_treemap_cartera_region"] = (p.groupby("region")["monto_prestamo"].sum()
                                      .sort_values(ascending=False).to_dict())
    r["p2_treemap_mayor_distrito"] = {"distrito": tm.idxmax()[1], "monto": float(tm.max())}

    # ---------------- P3: liquidez ----------------
    ult = t.sort_values(["fecha", "id_transaccion"]).groupby("id_cuenta").tail(1)
    dist_cuenta = pd.concat([p[["id_cuenta", "region"]], o[["id_cuenta", "region"]]]).drop_duplicates("id_cuenta")
    tt = pd.read_csv(os.path.join(DF, "df_transacciones_completado.csv.gz"),
                     usecols=["id_cuenta", "region"]).drop_duplicates("id_cuenta")
    dist_cuenta = pd.concat([dist_cuenta, tt]).drop_duplicates("id_cuenta")
    ult = ult.merge(dist_cuenta, on="id_cuenta")
    liq = pd.DataFrame({"cartera": p.groupby("region")["monto_prestamo"].sum(),
                        "saldo": ult.groupby("region")["saldo_cuenta"].sum()})
    liq["ratio_absorcion"] = liq["cartera"] / liq["saldo"]
    r["p3_absorcion_region"] = liq.sort_values("ratio_absorcion", ascending=False).round(4).to_dict(orient="index")

    # ---------------- P4: flujo transaccional ----------------
    g = t.groupby("tipo_operacion_traducido")["monto_transaccion"]
    r["p4_ticket_por_operacion"] = pd.DataFrame({
        "n": g.size(), "volumen": g.sum(), "media": g.mean(), "desv_est": g.std(),
        "error_estandar": g.std() / np.sqrt(g.size()),
        "pct_volumen": g.sum() / t["monto_transaccion"].sum()}).round(4).to_dict(orient="index")
    grupos = [s.values for _, s in g]
    anova = stats.f_oneway(*grupos)
    media_global = t["monto_transaccion"].mean()
    ss_entre = sum(len(s) * (s.mean() - media_global) ** 2 for s in grupos)
    ss_total = ((t["monto_transaccion"] - media_global) ** 2).sum()
    r["p4_anova_ticket_operacion"] = {"F": round(float(anova.statistic), 2),
                                      "p_valor": float(anova.pvalue),
                                      "eta_cuadrado": round(float(ss_entre / ss_total), 4)}
    a = t.loc[t["tipo_operacion_traducido"] == "Ingreso / Deposito", "monto_transaccion"]
    b = t.loc[t["tipo_operacion_traducido"] == "Retiro en Efectivo", "monto_transaccion"]
    w = stats.ttest_ind(a, b, equal_var=False)
    r["p4_welch_ingreso_vs_retiro"] = {"t": round(float(w.statistic), 2), "p_valor": float(w.pvalue)}
    r["p4_volumen_operacion_por_anio"] = (t.pivot_table(index="anio", columns="tipo_operacion_traducido",
                                                        values="monto_transaccion", aggfunc="sum")
                                           .to_dict(orient="index"))

    # ---------------- P5: órdenes ----------------
    r["p5_ordenes_categoria_pct"] = (o["categoria_orden"].value_counts(normalize=True).round(4).to_dict())
    r["p5_compromiso_categoria"] = o.groupby("categoria_orden")["monto_orden"].sum().to_dict()
    saldo_prom = t.groupby("id_cuenta")["saldo_cuenta"].mean()
    sat = (o.groupby("id_cuenta")["monto_orden"].sum() / saldo_prom).dropna()
    r["p5_indice_saturacion"] = {"cuentas_mayor_0_5": int((sat > 0.5).sum()),
                                 "cuentas_mayor_1": int((sat > 1).sum()),
                                 "maximo": {"id_cuenta": int(sat.idxmax()), "indice": round(float(sat.max()), 4)}}

    # ---------------- P6: impago histórico ----------------
    r["p6_incumplimiento_segmento_edad"] = tasa_con_error(p, "segmento_edad", "B", ["A", "B"]).round(4).to_dict(orient="index")
    q = p[p["estado_prestamo"].isin(["A", "B"])]
    r["p6_chi2_incumplimiento_vs_edad"] = chi2(pd.crosstab(q["segmento_edad"], q["estado_prestamo"]))

    with open(SALIDA, "w", encoding="utf-8") as f:
        json.dump(r, f, ensure_ascii=False, indent=2, default=float)

    print("=" * 78)
    print("EVIDENCIA ESTADÍSTICA DEL DASHBOARD (guía 07)")
    print("=" * 78)
    for k, val in r["kpi"].items():
        print(f"  {k:<30} {val:>20,}")
    print("\nPruebas:")
    for k in ["p1_chi2_mora_vs_cosecha_1994_1997", "p2_chi2_mora_vs_region", "p2_chi2_mora_vs_macro_region",
              "p2_fisher_north_moravia_vs", "p2_anova_monto_macro_region", "p4_anova_ticket_operacion",
              "p4_welch_ingreso_vs_retiro", "p5_indice_saturacion", "p6_chi2_incumplimiento_vs_edad"]:
        print(f"  {k}: {r[k]}")
    print(f"\nJSON completo: {SALIDA}")


if __name__ == "__main__":
    main()
