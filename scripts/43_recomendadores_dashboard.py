"""
==============================================================================
UNIVERSIDAD TÉCNICA DE AMBATO - Inteligencia de Negocios
AUTORES: Alison Marcela Cobos Taco / Henry Daniel Lagua Flores
==============================================================================
ARCHIVO: 43_recomendadores_dashboard.py   (Guía 07 v5, páginas R1–R3)
DESCRIPCIÓN: Aplica a los 4,500 titulares los sistemas de recomendación que el
             Informe 04 v2 señaló como los mejores, con el mismo protocolo de
             evaluación, y los carga en SQL Server (Kimball) y MongoDB para las
             páginas de recomendación del dashboard:

   Pregunta del gerente              Sistema elegido (Informe 04)          Evidencia
   --------------------------------  ------------------------------------  -----------------------------
   ¿Qué producto ofrecer?            Demográfico (arquetipo)               Hit@1 66.0%, MRR 0.776 (mejor)
   ¿Qué producto menos obvio?        kNN usuario-usuario, perfil exógeno   Hit@1 cola larga 37.2% (mejor)
   ¿A quién prestar y cuánto?        Regla de capacidad cuota/saldo previo AUC 0.717 (vs 0.659)
   ¿Qué productos van juntos?        Ítem a ítem P(j|i)                    Asociaciones con χ² + Holm
   Descartados: popularidad (línea base), contenidos, kNN por productos, coseno/ITF/Pearson,
   Slope One (para estimar montos la media del producto lo supera: MAE 0.285 vs 0.330).

TABLAS (mismo contenido en los dos motores; en MongoDB colecciones del mismo nombre en minúsculas):
   Dim_Producto              8     catálogo con nombre en español y penetración
   Recomendacion_Producto    27k   top 3 por cuenta de cada sistema (formato largo)
   Adopcion_Producto         8.6k  productos que cada cuenta ya usa
   Capacidad_Prestamo        4.5k  cuota prudente y montos máximos por cuenta
   Evaluacion_Recomendador   ~12   métricas del protocolo común (Informe 04)
   Asociacion_Producto       56    P(destino | origen) y lift entre productos
   Regla_Capacidad           7     tasa de impago por tramo de cada regla y su AUC
USO: python scripts/43_recomendadores_dashboard.py   (después de los scripts 37 a 42)
==============================================================================
"""
import importlib.util
import json
import os
import sys

import numpy as np
import pandas as pd
import pymongo
import pyodbc

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE_DIR, "scripts"))
from rs_comun import DF, cargar  # noqa: E402

KIMBALL = ("Driver={ODBC Driver 17 for SQL Server};Server=(localdb)\\MSSQLLocalDB;"
           "Database=DM_Financial_Kimball_v2;Trusted_Connection=yes;")
NOMBRES = {"SERVICIOS_HOGAR": "Domiciliar servicios del hogar", "TRANSF_SALIENTE": "Transferencias a otros bancos",
           "INGRESO_TRANSF": "Recibir ingresos por transferencia", "RETIRO_TARJETA": "Tarjeta de débito",
           "PENSION": "Domiciliar la pensión", "PRESTAMO": "Préstamo", "SEGURO": "Seguro domiciliado",
           "LEASING": "Leasing"}
SISTEMA_DEMO, SISTEMA_KNN = "Demográfico", "kNN perfil"
UMBRAL_CUOTA_SALDO = 0.057          # límite de la banda Baja (Carta v8)
TRAMOS_36M = [(-np.inf, 20000, "< 20 mil", 1), (20000, 40000, "20–40 mil", 2), (40000, 80000, "40–80 mil", 3),
              (80000, 150000, "80–150 mil", 4), (150000, np.inf, "> 150 mil", 5)]


def modulo(nombre, archivo):
    spec = importlib.util.spec_from_file_location(nombre, os.path.join(BASE_DIR, "scripts", archivo))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def top3(puntaje, adop, cuota_max, cuota_minima):
    """Top 3 de productos que la cuenta no tiene; el préstamo solo si la cuota prudente alcanza la mínima otorgada."""
    salida = {}
    for cta in adop.index:
        cand = [j for j in adop.columns if adop.loc[cta, j] == 0]
        if cuota_max.loc[cta] < cuota_minima:
            cand = [j for j in cand if j != "PRESTAMO"]
        salida[cta] = sorted(cand, key=lambda j: -puntaje.loc[cta, j])[:3]
    return salida


def main():
    m40 = modulo("rs40", "40_rs_perfiles_contenido.py")
    m39 = modulo("rs39", "39_rs_item_item.py")
    adop, _, perfiles, productos = cargar()
    prestamos = pd.read_csv(os.path.join(DF, "df_prestamos_clean.csv"))
    metricas = json.load(open(os.path.join(BASE_DIR, "metricas_recomendadores.json"), encoding="utf-8"))
    cuota_max = (UMBRAL_CUOTA_SALDO * perfiles.saldo_promedio).clip(lower=0)
    cuota_minima = float(prestamos.pago_mensual.min())
    cuota_tipica = float(prestamos.pago_mensual.median())

    # ---------- 1. Recomendaciones de los dos sistemas elegidos (entrenados con toda la adopción) ----------
    demo = m40.puntuar_demografico(adop, perfiles)
    z_exo = m40.estandarizar(perfiles.reindex(adop.index), ["edad_corte", "salario_promedio", "tasa_desempleo", "meses_vida"])
    knn = m40.puntuar_knn(adop, m40.coseno_filas(z_exo, z_exo))
    lista_demo = top3(demo, adop, cuota_max, cuota_minima)
    lista_knn = top3(knn, adop, cuota_max, cuota_minima)
    # El demográfico debe reproducir exactamente la lista final del Informe 04 (rs_recomendaciones.csv)
    final = pd.read_csv(os.path.join(DF, "rs_recomendaciones.csv")).set_index("id_cuenta")
    iguales = sum(lista_demo[c] == [x for x in final.loc[c, ["recomendacion_1", "recomendacion_2", "recomendacion_3"]]
                                    if isinstance(x, str)] for c in adop.index)
    assert iguales == len(adop), f"El demográfico no reproduce rs_recomendaciones.csv ({iguales}/{len(adop)})"
    filas = []
    for sistema, lista, puntaje in ((SISTEMA_DEMO, lista_demo, demo), (SISTEMA_KNN, lista_knn, knn)):
        for cta, prods in lista.items():
            for pos, prod in enumerate(prods, start=1):
                filas.append({"id_cuenta": int(cta), "id_cliente": int(perfiles.loc[cta, "id_cliente"]), "sistema": sistema,
                              "producto": NOMBRES[prod], "posicion": pos, "puntaje": round(float(puntaje.loc[cta, prod]), 4),
                              # descubrimiento: el kNN lo propone y el demográfico no lo tiene en su top 3
                              "es_descubrimiento": bool(sistema == SISTEMA_KNN and prod not in lista_demo[cta])})
    rec = pd.DataFrame(filas)

    # ---------- 2. Adopción actual ----------
    ad = adop.stack().rename("tiene").reset_index().query("tiene == 1")
    adopcion = pd.DataFrame({"id_cuenta": ad.id_cuenta.astype(int), "id_cliente": ad.id_cuenta.map(perfiles.id_cliente).astype(int),
                             "producto": ad.iloc[:, 1].map(NOMBRES)})

    # ---------- 3. Capacidad de pago (regla de la Carta v8) ----------
    cap = pd.DataFrame({"id_cuenta": adop.index.astype(int), "id_cliente": perfiles.reindex(adop.index).id_cliente.astype(int).values,
                        "tiene_prestamo": adop.PRESTAMO.astype(bool).values,
                        "saldo_promedio": perfiles.reindex(adop.index).saldo_promedio.round(2).values,
                        "cuota_prudente": cuota_max.reindex(adop.index).round(2).values})
    for meses in (12, 36, 60):
        cap[f"monto_maximo_{meses}m"] = (cap.cuota_prudente * meses).round(0)
    tramo = pd.cut(cap.monto_maximo_36m, [t[0] for t in TRAMOS_36M] + [np.inf], labels=[t[2] for t in TRAMOS_36M], right=False)
    cap["tramo_monto_36m"] = tramo.astype(str)
    cap["orden_tramo"] = cap.tramo_monto_36m.map({t[2]: t[3] for t in TRAMOS_36M}).astype(int)
    cap["puede_pagar_prestamo_tipico"] = (~cap.tiene_prestamo) & (cap.cuota_prudente >= cuota_tipica)
    cap["prestamo_recomendado"] = cap.id_cuenta.map(lambda c: "PRESTAMO" in lista_demo[c]).astype(bool)

    # ---------- 4. Evaluación de todos los recomendadores (protocolo común, semilla 42 y 2026) ----------
    sel = metricas["perfiles_contenido"]["ranking"]["seleccion"]
    conf = metricas["perfiles_contenido"]["ranking"]["confirmacion"]
    rol = {"Demográfico (arquetipo)": "Elegido: qué ofrecer", "kNN usuario-usuario (perfil exógeno)": "Elegido: descubrir",
           "Ítem a ítem P(j|i)": "Elegido: venta cruzada", "Popularidad": "Línea base"}
    familia = {"Popularidad": "Línea base", "Demográfico (arquetipo)": "Perfil", "kNN usuario-usuario (perfil exógeno)": "Perfil",
               "kNN usuario-usuario (productos)": "Colaborativo", "Ítem a ítem P(j|i)": "Ítem a ítem",
               "Contenidos (atributos)": "Contenidos", "Contenidos (TF-IDF)": "Contenidos"}
    ev = []
    for nombre, r in sel.items():
        if "referencia sesgada" in nombre:
            continue            # fuga de información detectada en el Informe 04: no se compara
        ev.append({"modelo": nombre, "familia": familia.get(nombre, "Otro"), "rol": rol.get(nombre, "Descartado"),
                   "hit_1": r["hit_1"], "hit_3": r["hit_3"], "mrr": r["mrr"], "hit_1_cola_larga": r["cola_larga"]["hit_1"],
                   "mrr_confirmacion": conf.get(nombre, {}).get("mrr")})
    so = metricas["slope_one"]["ranking"]["Slope One"]
    ev.append({"modelo": "Slope One", "familia": "Intensidad", "rol": "Descartado", "hit_1": so["hit_1"], "hit_3": so["hit_3"],
               "mrr": so["mrr"], "hit_1_cola_larga": so["cola_larga"]["hit_1"], "mrr_confirmacion": None})
    evaluacion = pd.DataFrame(ev).sort_values("hit_1", ascending=False).reset_index(drop=True)
    evaluacion["orden"] = evaluacion.index + 1
    evaluacion["elegido"] = evaluacion.rol.str.startswith("Elegido")

    # ---------- 5. Asociaciones ítem a ítem P(j|i) y lift ----------
    P = m39.condicional(adop)
    n = len(adop)
    asoc = []
    for i in adop.columns:
        for j in adop.columns:
            if i == j:
                continue
            ambos = int((adop[i] & adop[j]).sum())
            asoc.append({"producto_origen": NOMBRES[i], "producto_destino": NOMBRES[j], "p_destino_dado_origen": round(float(P.loc[i, j]), 4),
                         "lift": round(ambos * n / (adop[i].sum() * adop[j].sum()), 4), "cuentas_ambos": ambos})
    asociacion = pd.DataFrame(asoc)

    # ---------- 6. Reglas de capacidad comparadas (Informe 04, utilidad financiera) ----------
    u = metricas["perfiles_contenido"]["utilidad"]
    regla = []
    for nombre, clave, tramos in (("Anterior: cuota / salario del distrito", "regla_anterior_cuota_salario_distrital", "tramos"),
                                  ("Carta v8: cuota / saldo previo", "regla_carta_v8_cuota_saldo_previo", "bandas")):
        for k, (tr, v) in enumerate(u[clave][tramos].items(), start=1):
            regla.append({"regla": nombre, "tramo": tr, "orden": k, "prestamos": v["prestamos"], "impagos": v["impagos"],
                          "tasa_impago": v["tasa"], "auc": u[clave]["auc_impago"]})
    regla = pd.DataFrame(regla)

    catalogo = pd.DataFrame({"producto": [NOMBRES[p] for p in productos.index], "codigo": productos.index,
                             "descripcion": productos.descripcion.values, "penetracion": productos.penetracion.values})
    catalogo = catalogo.sort_values("penetracion", ascending=False).reset_index(drop=True)
    catalogo["orden"] = catalogo.index + 1

    # ---------- 7. Carga en SQL Server ----------
    cn = pyodbc.connect(KIMBALL, timeout=120)
    cur = cn.cursor()
    sk_cta = dict(cur.execute("SELECT id_cuenta_bk, sk_cuenta FROM Dim_Cuenta").fetchall())
    sk_cli = dict(cur.execute("SELECT id_cliente_bk, sk_cliente FROM Dim_Cliente").fetchall())
    dist_cta = {a: (b, c) for a, b, c in cur.execute(
        "SELECT c.id_cuenta_bk, c.sk_distrito, d.id_distrito_bk FROM Dim_Cuenta c JOIN Dim_Distrito d ON d.sk_distrito = c.sk_distrito")}
    for df in (rec, adopcion, cap):
        df["id_distrito"] = df.id_cuenta.map(lambda c: dist_cta[c][1]).astype(int)
    ddl = open(os.path.join(BASE_DIR, "sql", "01_DDL_Kimball_DM_Financial.sql"), encoding="utf-8").read()
    inicio, fin = ddl.index("-- >>> RECOMENDADORES DASHBOARD"), ddl.index("-- <<< RECOMENDADORES DASHBOARD")
    lotes = [b[b.index("CREATE TABLE"):] for b in ddl[inicio:fin].split("\nGO") if "CREATE TABLE" in b]
    tablas = [b.split("CREATE TABLE")[1].split("(")[0].strip() for b in lotes]
    for tabla in reversed(tablas):        # primero las que tienen claves foráneas hacia Dim_Producto
        cur.execute(f"IF OBJECT_ID('{tabla}') IS NOT NULL DROP TABLE {tabla}")
    for lote in lotes:
        cur.execute(lote)
    cn.commit()

    def insertar(tabla, filas):
        cur.fast_executemany = True
        marcas = ", ".join("?" * len(filas[0]))
        cur.executemany(f"INSERT INTO {tabla} VALUES ({marcas})", filas)

    llaves = lambda r: (sk_cta[r.id_cuenta], sk_cli[r.id_cliente], dist_cta[r.id_cuenta][0])
    insertar("Dim_Producto", [(r.producto, r.codigo, r.descripcion, float(r.penetracion), int(r.orden)) for r in catalogo.itertuples()])
    insertar("Recomendacion_Producto", [(*llaves(r), r.sistema, r.producto, int(r.posicion), float(r.puntaje), bool(r.es_descubrimiento))
                                        for r in rec.itertuples()])
    insertar("Adopcion_Producto", [(*llaves(r), r.producto) for r in adopcion.itertuples()])
    insertar("Capacidad_Prestamo", [(*llaves(r), bool(r.tiene_prestamo), float(r.saldo_promedio), float(r.cuota_prudente),
                                     float(r.monto_maximo_12m), float(r.monto_maximo_36m), float(r.monto_maximo_60m),
                                     r.tramo_monto_36m, int(r.orden_tramo), bool(r.puede_pagar_prestamo_tipico), bool(r.prestamo_recomendado))
                                    for r in cap.itertuples()])
    cur.fast_executemany = False   # hay un NULL decimal (Slope One sin confirmación)
    cur.executemany("INSERT INTO Evaluacion_Recomendador VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    [(r.modelo, r.familia, r.rol, float(r.hit_1), float(r.hit_3), float(r.mrr), float(r.hit_1_cola_larga),
                      None if pd.isna(r.mrr_confirmacion) else float(r.mrr_confirmacion), int(r.orden), bool(r.elegido))
                     for r in evaluacion.itertuples()])
    insertar("Asociacion_Producto", [(r.producto_origen, r.producto_destino, float(r.p_destino_dado_origen), float(r.lift), int(r.cuentas_ambos))
                                     for r in asociacion.itertuples()])
    insertar("Regla_Capacidad", [(r.regla, r.tramo, int(r.orden), int(r.prestamos), int(r.impagos), float(r.tasa_impago), float(r.auc))
                                 for r in regla.itertuples()])
    cn.commit()
    conteo_sql = {t: cur.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in
                  ("Dim_Producto", "Recomendacion_Producto", "Adopcion_Producto", "Capacidad_Prestamo",
                   "Evaluacion_Recomendador", "Asociacion_Producto", "Regla_Capacidad")}
    cn.close()

    # ---------- 8. Carga en MongoDB (mismas columnas, con los identificadores de negocio) ----------
    db = pymongo.MongoClient("mongodb://localhost:27017/")["Financial"]
    colecciones = {"dim_producto": catalogo, "recomendacion_producto": rec, "adopcion_producto": adopcion,
                   "capacidad_prestamo": cap, "evaluacion_recomendador": evaluacion, "asociacion_producto": asociacion,
                   "regla_capacidad": regla}
    conteo_mongo = {}
    for nombre, df in colecciones.items():
        db.drop_collection(nombre)
        docs = json.loads(df.to_json(orient="records", force_ascii=False))
        db[nombre].insert_many(docs)
        conteo_mongo[nombre] = db[nombre].count_documents({})

    # ---------- 9. Controles ----------
    print("SQL Server:", conteo_sql)
    print("MongoDB:   ", conteo_mongo)
    for (t_sql, n_sql), n_mongo in zip(conteo_sql.items(), conteo_mongo.values()):
        assert n_sql == n_mongo, f"{t_sql}: SQL {n_sql} vs Mongo {n_mongo}"
    sin = cap[~cap.tiene_prestamo]
    print(f"Demográfico = lista final del Informe 04 en {iguales}/{len(adop)} cuentas")
    print(f"Titulares sin préstamo {len(sin)}, préstamo recomendado {int(cap.prestamo_recomendado.sum())}, "
          f"cuota prudente mediana {sin.cuota_prudente.median():,.2f}, pueden pagar la cuota típica {int(sin.puede_pagar_prestamo_tipico.sum())}")
    print(f"Descubrimientos del kNN (fuera del top 3 demográfico): {int(rec.es_descubrimiento.sum())}")
    print("OK: los dos motores tienen los mismos datos de recomendación.")


if __name__ == "__main__":
    main()
