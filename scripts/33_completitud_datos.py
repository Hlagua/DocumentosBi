"""
==============================================================================
UNIVERSIDAD TÉCNICA DE AMBATO - Inteligencia de Negocios
AUTORES: Alison Marcela Cobos Taco / Henry Daniel Lagua Flores
==============================================================================
ARCHIVO: 33_completitud_datos.py
PASO 2 DE 3 DE LA COMPLETITUD DE DATOS (32 -> 33 -> 34)
DESCRIPCIÓN: Diagnostica los huecos de los DataFrames generados por el script 32,
             aplica las reglas de completitud del Informe 03 y verifica el
             resultado. No modifica los archivos de entrada: escribe versiones
             nuevas (_clean / _completado).

  Huecos ESTRUCTURALES (se conservan como nulos, el cliente no tiene el producto):
    etiqueta_buen_pagador, id_prestamo, plazo_prestamo, monto_promedio_orden,
    saldo_promedio / minimo / maximo de los cotitulares.
  Huecos REALES (se completan):
    distrito 69 (desempleo y criminalidad 1995), orders.k_symbol,
    trans.operation, trans.k_symbol, trans.bank, trans.account.

SALIDAS:
    dataframes/df_distritos_clean.csv
    dataframes/df_prestamos_clean.csv
    dataframes/df_ordenes_clean.csv
    dataframes/df_cliente_consolidado_clean.csv
    dataframes/df_transacciones_completado.csv.gz
    metricas_completitud_datos.json   (diagnóstico, reglas aplicadas y verificación)
USO: python scripts/33_completitud_datos.py
==============================================================================
"""
import json
import os
import sys
import time

import numpy as np
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DF = os.path.join(BASE_DIR, "dataframes")
SALIDA_JSON = os.path.join(BASE_DIR, "metricas_completitud_datos.json")
DISTRITO_OBJETIVO = 69  # Jesenik

CONCEPTOS = {
    "UROK": "Intereses Ganados en Cuenta",
    "SLUZBY": "Comisión por Mantenimiento / Servicios",
    "SIPO": "Servicios Básicos del Hogar",
    "DUCHOD": "Abono de Pensión / Jubilación",
    "POJISTNE": "Pago de Póliza de Seguro",
    "UVER": "Amortización de Cuota de Préstamo",
    "SANKC. UROK": "Interés Moratorio por Sobregiro",
    "LEASING": "Cuota de Arrendamiento Financiero (Leasing)",
    "RETIRO_EFECTIVO": "Retiro en Efectivo (Gastos Personales)",
    "DEPOSITO_EFECTIVO": "Depósito en Efectivo de Fondos Propios",
    "TRANSFERENCIA_EXTERNA": "Transferencia Bancaria Saliente",
    "INGRESO_ORDINARIO": "Ingreso Bancario Ordinario",
}

informe = {"diagnostico_inicial": {}, "reglas": {}, "diagnostico_final": {}, "verificacion": []}


def diagnostico(nombre, df):
    nulos = df.isna().sum()
    return {"filas": int(len(df)), "nulos": {k: int(v) for k, v in nulos[nulos > 0].items()}}


def verificar(descripcion, condicion, detalle=""):
    informe["verificacion"].append({"prueba": descripcion, "resultado": "OK" if condicion else "FALLA", "detalle": str(detalle)})
    print(f"  [{'OK' if condicion else 'FALLA':<5}] {descripcion} {detalle}")


# ==============================================================================
# 1. DISTRITO 69: diagnóstico de alternativas e imputación
# ==============================================================================
def kmeans_mediana(dist):
    """Alternativa evaluada en el Informe 03 (anexo 3): K-Means k=9, 50 reinicios, mediana del clúster."""
    resto, obj = dist[dist.id_distrito != DISTRITO_OBJETIVO], dist[dist.id_distrito == DISTRITO_OBJETIVO]
    num = ["poblacion", "salario_promedio"]
    media, desv = resto[num].mean(), resto[num].std()
    dummies = pd.get_dummies(resto.region).astype(float)
    X = np.hstack([((resto[num] - media) / desv).values, dummies.values])
    punto = np.hstack([((obj[num] - media) / desv).values[0],
                       pd.get_dummies(obj.region).reindex(columns=dummies.columns, fill_value=0).astype(float).values[0]])
    mejor = (np.inf, None, None)
    for semilla in range(50):
        rng = np.random.RandomState(semilla)
        cent = X[rng.choice(len(X), 9, replace=False)]
        for _ in range(200):
            asig = np.argmin(((X[:, None, :] - cent[None]) ** 2).sum(axis=2), axis=1)
            nuevo = np.array([X[asig == c].mean(axis=0) if np.any(asig == c) else cent[c] for c in range(9)])
            if np.allclose(nuevo, cent):
                break
            cent = nuevo
        inercia = sum(((X[asig == c] - cent[c]) ** 2).sum() for c in range(9))
        if inercia < mejor[0]:
            mejor = (inercia, asig, cent)
    cluster = np.argmin(((mejor[2] - punto) ** 2).sum(axis=1))
    comp = resto[mejor[1] == cluster]
    return float(comp.tasa_desempleo_1995.median()), float(comp.tasa_criminalidad_1995.median())


def completar_distrito():
    print("\n1. Distrito 69 (Jesenik)")
    dist = pd.read_csv(os.path.join(DF, "df_distritos.csv"))
    informe["diagnostico_inicial"]["df_distritos"] = diagnostico("df_distritos", dist)
    obj = dist[dist.id_distrito == DISTRITO_OBJETIVO].iloc[0]
    otros = dist[dist.id_distrito != DISTRITO_OBJETIVO]

    # Método adoptado: valor 1996 del propio distrito x razón mediana 1995/1996 de los otros 76 distritos.
    validos = otros[(otros.tasa_desempleo_1996 > 0) & (otros.tasa_criminalidad_1996 > 0)]
    r_des = float((validos.tasa_desempleo_1995 / validos.tasa_desempleo_1996).median())
    r_cri = float((validos.tasa_criminalidad_1995 / validos.tasa_criminalidad_1996).median())
    desempleo = round(obj.tasa_desempleo_1996 * r_des, 2)
    criminalidad = float(round(obj.tasa_criminalidad_1996 * r_cri))

    # Respaldo empírico: el mismo método aplicado a cada uno de los 76 distritos con dato real (dejando uno fuera).
    err_des, err_cri = [], []
    for i, fila in validos.iterrows():
        resto = validos.drop(i)
        err_des.append(abs(fila.tasa_desempleo_1996 * (resto.tasa_desempleo_1995 / resto.tasa_desempleo_1996).median() - fila.tasa_desempleo_1995))
        err_cri.append(abs(fila.tasa_criminalidad_1996 * (resto.tasa_criminalidad_1995 / resto.tasa_criminalidad_1996).median()
                           - fila.tasa_criminalidad_1995) / fila.tasa_criminalidad_1995)
    sumperk = dist[dist.nombre_distrito == "Sumperk"].iloc[0]
    km_des, km_cri = kmeans_mediana(dist)

    informe["reglas"]["distrito_69"] = {
        "metodo_adoptado": "Valor 1996 del propio distrito x razón mediana 1995/1996 de los otros distritos",
        "razon_mediana_desempleo": round(r_des, 4), "razon_mediana_criminalidad": round(r_cri, 4),
        "valores_1996_jesenik": {"desempleo": float(obj.tasa_desempleo_1996), "criminalidad": float(obj.tasa_criminalidad_1996)},
        "imputado": {"tasa_desempleo_1995": desempleo, "tasa_criminalidad_1995": criminalidad},
        "validacion_dejando_uno_fuera": {"distritos": len(validos),
                                         "error_absoluto_medio_desempleo_pp": round(float(np.mean(err_des)), 3),
                                         "error_relativo_medio_criminalidad_pct": round(100 * float(np.mean(err_cri)), 2)},
        "alternativas_descartadas": {
            "copiar_sumperk_1995": {"desempleo": float(sumperk.tasa_desempleo_1995), "criminalidad": float(sumperk.tasa_criminalidad_1995),
                                    "motivo": f"En 1995 Sumperk incluía el territorio de Jesenik: sus delitos caen de "
                                              f"{sumperk.tasa_criminalidad_1995:,.0f} (1995) a {sumperk.tasa_criminalidad_1996:,.0f} (1996) "
                                              f"al separarse. Copiar el conteo a un distrito de {obj.poblacion:,} habitantes "
                                              f"({obj.poblacion / sumperk.poblacion:.0%} de Sumperk) lo sobrestima."},
            "kmeans_mediana_cluster": {"desempleo": km_des, "criminalidad": km_cri,
                                       "motivo": "Estima a partir de distritos parecidos teniendo el dato real del propio distrito en 1996."},
        },
    }
    print(f"  Razón mediana 1995/1996: desempleo {r_des:.4f}, criminalidad {r_cri:.4f}")
    print(f"  Imputado: desempleo {desempleo} | criminalidad {criminalidad:,.0f}")
    print(f"  Alternativas: Sumperk {sumperk.tasa_desempleo_1995}/{sumperk.tasa_criminalidad_1995:,.0f} | K-Means {km_des}/{km_cri:,.0f}")

    limpio = dist.copy()
    limpio.loc[limpio.id_distrito == DISTRITO_OBJETIVO, ["tasa_desempleo_1995", "tasa_criminalidad_1995"]] = [desempleo, criminalidad]
    limpio["es_imputado"] = (limpio.id_distrito == DISTRITO_OBJETIVO).astype(int)
    limpio["metodo_imputacion"] = np.where(limpio.es_imputado == 1, "Razon 1995/1996 sobre dato 1996", "Original PKDD99")
    limpio.to_csv(os.path.join(DF, "df_distritos_clean.csv"), index=False, encoding="utf-8-sig")
    informe["diagnostico_final"]["df_distritos_clean"] = diagnostico("df_distritos_clean", limpio)
    verificar("Distritos sin nulos tras imputar", limpio.isna().sum().sum() == 0)
    return desempleo, criminalidad


# ==============================================================================
# 2. PRÉSTAMOS, ÓRDENES Y CLIENTE 360
# ==============================================================================
def completar_tablas_medianas(desempleo, criminalidad):
    print("\n2. Préstamos, órdenes y Cliente 360")
    # Préstamos: solo el distrito 69
    p = pd.read_csv(os.path.join(DF, "df_prestamos.csv"))
    informe["diagnostico_inicial"]["df_prestamos"] = diagnostico("df_prestamos", p)
    m = p.id_distrito == DISTRITO_OBJETIVO
    p.loc[m, ["desempleo_distrito", "crimen_distrito"]] = [desempleo, criminalidad]
    p.to_csv(os.path.join(DF, "df_prestamos_clean.csv"), index=False, encoding="utf-8-sig")
    informe["reglas"]["prestamos_distrito_69"] = int(m.sum())
    informe["diagnostico_final"]["df_prestamos_clean"] = diagnostico("df_prestamos_clean", p)
    verificar("Préstamos sin nulos", p.isna().sum().sum() == 0, f"({int(m.sum())} préstamos del distrito 69 completados)")

    # Órdenes: k_symbol vacío -> SIN_ESPECIFICAR (mismo criterio aplicado en OpenRefine)
    o = pd.read_csv(os.path.join(DF, "df_ordenes.csv"))
    informe["diagnostico_inicial"]["df_ordenes"] = diagnostico("df_ordenes", o)
    vacias = int(o.k_symbol.isna().sum())
    o["k_symbol"] = o.k_symbol.fillna("SIN_ESPECIFICAR")
    o.to_csv(os.path.join(DF, "df_ordenes_clean.csv"), index=False, encoding="utf-8-sig")
    informe["reglas"]["ordenes_k_symbol_sin_especificar"] = vacias
    informe["diagnostico_final"]["df_ordenes_clean"] = diagnostico("df_ordenes_clean", o)
    verificar("Órdenes sin nulos", o.isna().sum().sum() == 0, f"({vacias:,} k_symbol -> SIN_ESPECIFICAR)")
    verificar("Monto de órdenes sin cambios", round(o.monto_orden.sum(), 2) == 21229041.0, f"({o.monto_orden.sum():,.2f})")

    # Cliente 360: huecos reales (distrito 69) y marcas para los estructurales
    c = pd.read_csv(os.path.join(DF, "df_cliente_consolidado.csv"))
    informe["diagnostico_inicial"]["df_cliente_consolidado"] = diagnostico("df_cliente_consolidado", c)
    m = c.id_distrito == DISTRITO_OBJETIVO
    c.loc[m, ["tasa_desempleo", "tasa_criminalidad"]] = [desempleo, criminalidad]
    c.insert(c.columns.get_loc("tipo_disposicion") + 1, "es_titular", (c.tipo_disposicion == "OWNER").astype(int))
    c.insert(c.columns.get_loc("etiqueta_buen_pagador") + 1, "calificacion_pago",
             c.etiqueta_buen_pagador.map({1: "Buen Pagador", 0: "Mal Pagador", True: "Buen Pagador", False: "Mal Pagador"})
             .fillna("Sin evaluar"))
    c["tiene_ordenes"] = (c.total_ordenes_activas > 0).astype(int)
    c.to_csv(os.path.join(DF, "df_cliente_consolidado_clean.csv"), index=False, encoding="utf-8-sig")
    informe["reglas"]["cliente_distrito_69"] = int(m.sum())
    final = diagnostico("df_cliente_consolidado_clean", c)
    informe["diagnostico_final"]["df_cliente_consolidado_clean"] = final
    estructurales = {"etiqueta_buen_pagador", "id_prestamo", "plazo_prestamo", "monto_promedio_orden",
                     "saldo_promedio", "saldo_minimo", "saldo_maximo"}
    verificar("Cliente 360: solo quedan nulos estructurales", set(final["nulos"]) <= estructurales, final["nulos"])
    verificar("Nulos de saldo = cotitulares sin movimientos propios",
              int(c.saldo_promedio.isna().sum()) == int((c.es_titular == 0).sum()) == 869)
    verificar("Nulos de préstamo = clientes sin préstamo como titular",
              int(c.id_prestamo.isna().sum()) == int((c.tiene_prestamo == 0).sum()))
    verificar("Nulos de promedio de órdenes = clientes sin órdenes",
              int(c.monto_promedio_orden.isna().sum()) == int((c.tiene_ordenes == 0).sum()))


# ==============================================================================
# 3. TRANSACCIONES (pipeline vectorizado)
# ==============================================================================
def completar_transacciones():
    print("\n3. Transacciones (1,056,320 filas)")
    t = pd.read_csv(os.path.join(DF, "df_transacciones.csv.gz"), low_memory=False,
                    dtype={"operation": "object", "k_symbol": "object", "bank": "object", "account": "object"})
    p = pd.read_csv(os.path.join(DF, "df_prestamos.csv"))
    o = pd.read_csv(os.path.join(DF, "df_ordenes.csv"))
    informe["diagnostico_inicial"]["df_transacciones"] = diagnostico("df_transacciones", t)
    monto_inicial, filas_iniciales = round(t.monto_transaccion.sum(), 2), len(t)
    ks_original = t.k_symbol.copy()
    r = {}

    # Fase 1: operation
    m = t.operation.isna() & (t.tipo_transaccion == "PRIJEM") & (t.k_symbol == "UROK")
    t.loc[m, "operation"] = "ABONO_INTERESES"
    r["1.1 operation -> ABONO_INTERESES (PRIJEM + UROK)"] = int(m.sum())
    r["1.2 operation nula residual"] = int(t.operation.isna().sum())

    # Fase 2: k_symbol
    metodo = pd.Series(np.where(ks_original.notna(), "Fuente", None), index=t.index, dtype=object)
    cuota = p.set_index("id_cuenta").pago_mensual
    m = t.k_symbol.isna() & (t.tipo_transaccion == "VYDAJ") & (t.monto_transaccion == t.id_cuenta.map(cuota))
    t.loc[m, "k_symbol"], metodo[m] = "UVER", "Cruce con prestamos"
    r["2.1 k_symbol -> UVER (monto = cuota del préstamo de la cuenta)"] = int(m.sum())
    r["2.1 detalle por operación"] = t.loc[m, "operation"].value_counts().to_dict()

    conocidas = o[o.k_symbol.notna()].drop_duplicates(["id_cuenta", "monto_orden"], keep=False)
    clave = conocidas.set_index(["id_cuenta", "monto_orden"]).k_symbol
    candidata = t.k_symbol.isna() & (t.tipo_transaccion == "VYDAJ")
    encontrado = pd.Series(pd.MultiIndex.from_arrays([t.loc[candidata, "id_cuenta"], t.loc[candidata, "monto_transaccion"]])
                           .map(lambda k: clave.get(k)), index=t.index[candidata])
    encontrado = encontrado.dropna()
    t.loc[encontrado.index, "k_symbol"], metodo[encontrado.index] = encontrado, "Cruce con ordenes"
    r["2.2 k_symbol por (cuenta, monto) de una orden única"] = encontrado.value_counts().to_dict()
    r["2.2 detalle por operación"] = t.loc[encontrado.index, "operation"].value_counts().to_dict()

    reglas_canal = [("2.3 k_symbol -> RETIRO_EFECTIVO (VYBER / VYBER KARTOU)", t.operation.isin(["VYBER", "VYBER KARTOU"]), "RETIRO_EFECTIVO"),
                    ("2.4 k_symbol -> DEPOSITO_EFECTIVO (VKLAD)", t.operation == "VKLAD", "DEPOSITO_EFECTIVO"),
                    ("2.5 k_symbol -> TRANSFERENCIA_EXTERNA (egreso residual)", t.tipo_transaccion == "VYDAJ", "TRANSFERENCIA_EXTERNA"),
                    ("2.6 k_symbol -> INGRESO_ORDINARIO (ingreso residual)", t.tipo_transaccion == "PRIJEM", "INGRESO_ORDINARIO")]
    for nombre, cond, valor in reglas_canal:
        m = t.k_symbol.isna() & cond
        t.loc[m, "k_symbol"], metodo[m] = valor, "Regla de canal" if "residual" not in nombre else "Residual"
        r[nombre] = int(m.sum())
    r["2.7 k_symbol nula residual"] = int(t.k_symbol.isna().sum())

    # Fase 3: contraparte (bank / account)
    contraparte = pd.Series("Entidad externa registrada", index=t.index, dtype=object)
    # Primero los cargos y abonos que genera el propio banco (intereses, comisiones, sanciones):
    # vienen con operation VYBER, pero no son retiros en caja.
    sistema = t.k_symbol.isin(["UROK", "SLUZBY", "SANKC. UROK"]) & t.bank.isna()
    caja = t.operation.isin(["VKLAD", "VYBER", "VYBER KARTOU"]) & t.bank.isna() & ~sistema
    externa = t.bank.isna() & ~caja & ~sistema
    contraparte[caja], contraparte[sistema], contraparte[externa] = "Caja propia", "Sistema central", "Entidad externa no registrada"
    for m, banco, cuenta in [(caja, "BANCO_PROPIO_LOCAL", "CAJA_VENTANILLA_ATM"),
                             (sistema, "SISTEMA_CENTRAL_BANCO", "TESORERIA_INTERNA"),
                             (externa, "OTRA_ENTIDAD_NO_REGISTRADA", "CUENTA_EXTERNA_NO_REGISTRADA")]:
        t.loc[m, "bank"] = banco
        t.loc[m & t.account.isna(), "account"] = cuenta
    sin_cuenta = t.account.isna()
    t.loc[sin_cuenta, "account"] = "CUENTA_EXTERNA_NO_REGISTRADA"
    r["3 contraparte por tipo"] = contraparte.value_counts().to_dict()
    r["3 cuentas faltantes con banco registrado"] = int(sin_cuenta.sum())

    # Fase 4: concepto traducido y trazabilidad
    t["concepto_movimiento_traducido"] = t.k_symbol.map(CONCEPTOS)
    t["metodo_concepto"] = metodo
    t["tipo_contraparte"] = contraparte
    informe["reglas"]["transacciones"] = r
    for k, v in r.items():
        print(f"  {k}: {v}")

    t.to_csv(os.path.join(DF, "df_transacciones_completado.csv.gz"), index=False, encoding="utf-8-sig", compression="gzip")
    informe["diagnostico_final"]["df_transacciones_completado"] = diagnostico("df_transacciones_completado", t)
    informe["distribucion_conceptos"] = t.concepto_movimiento_traducido.value_counts().to_dict()
    informe["distribucion_metodo_concepto"] = t.metodo_concepto.value_counts().to_dict()

    verificar("Transacciones sin nulos", int(t.isna().sum().sum()) == 0)
    verificar("Filas sin cambios", len(t) == filas_iniciales == 1056320)
    verificar("Monto total sin cambios", round(t.monto_transaccion.sum(), 2) == monto_inicial, f"({monto_inicial:,.2f})")
    verificar("Conceptos de la fuente no modificados", bool((t.k_symbol[ks_original.notna()] == ks_original.dropna()).all()))
    verificar("Todos los conceptos tienen traducción", t.concepto_movimiento_traducido.notna().all())
    verificar("Categoría analítica intacta (Intereses = 183,114)", int((t.tipo_operacion_traducido == "Intereses Ganados").sum()) == 183114)


def main():
    t0 = time.time()
    print("=" * 78 + "\nCOMPLETITUD DE DATOS (Informe 03) sobre los DataFrames del script 32\n" + "=" * 78)
    desempleo, criminalidad = completar_distrito()
    completar_tablas_medianas(desempleo, criminalidad)
    completar_transacciones()
    informe["duracion_segundos"] = round(time.time() - t0, 1)
    fallas = [v for v in informe["verificacion"] if v["resultado"] != "OK"]
    informe["resultado"] = "OK" if not fallas else f"{len(fallas)} FALLAS"
    with open(SALIDA_JSON, "w", encoding="utf-8") as f:
        json.dump(informe, f, ensure_ascii=False, indent=2, default=str)
    print(f"\n{len(informe['verificacion']) - len(fallas)}/{len(informe['verificacion'])} verificaciones OK "
          f"en {informe['duracion_segundos']} s. Resumen: {SALIDA_JSON}")
    if fallas:
        sys.exit("Hay verificaciones fallidas: no cargue estos datos en Kimball.")
    print("Siguiente paso: python scripts/34_carga_completitud_kimball.py")


if __name__ == "__main__":
    main()
