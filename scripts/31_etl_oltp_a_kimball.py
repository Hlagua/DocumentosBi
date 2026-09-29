"""
==============================================================================
UNIVERSIDAD TÉCNICA DE AMBATO - Inteligencia de Negocios
AUTORES: Alison Marcela Cobos Taco / Henry Daniel Lagua Flores
==============================================================================
ARCHIVO: 31_etl_oltp_a_kimball.py
DESCRIPCIÓN: ETL completo OLTP -> OLAP según la Carta de Diseño v8.
             Extrae las 9 tablas de Financial_ijs (MySQL remoto), las
             transforma en staging (pandas) y carga el Data Mart Kimball
             DM_Financial_Kimball_v2 (SQL Server): 7 dimensiones y 4 hechos.
             Al final ejecuta el plan de validación de la Carta (12.3),
             lo registra en Auditoria_Carga / Auditoria_Anomalias y guarda
             el resumen en metricas_carga_kimball.json.
USO:
    python scripts/31_etl_oltp_a_kimball.py              # vacía y recarga el Data Mart
    python scripts/31_etl_oltp_a_kimball.py --recrear    # además recrea las bases desde
                                                        # sql/01 y sql/02 (la base Kimball
                                                        # anterior se renombra como respaldo)
REQUISITOS: pip install pymysql pyodbc pandas numpy scipy
==============================================================================
"""
import json
import os
import re
import sys
import time
from datetime import date, datetime

import numpy as np
import pandas as pd
import pymysql
import pyodbc
from scipy import stats

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SALIDA_JSON = os.path.join(BASE_DIR, "metricas_carga_kimball.json")
DDL_KIMBALL = os.path.join(BASE_DIR, "sql", "01_DDL_Kimball_DM_Financial.sql")
DDL_INMON = os.path.join(BASE_DIR, "sql", "02_DDL_Inmon_EDW_Financial.sql")

MYSQL = dict(host="relational.fel.cvut.cz", port=3306, user="guest",
             password="ctu-relational", database="Financial_ijs", charset="utf8mb4")
SERVIDOR = r"(localdb)\MSSQLLocalDB"
BD_KIMBALL = "DM_Financial_Kimball_v2"
BD_INMON = "EDW_Financial_Inmon"
FECHA_CORTE = date(1998, 12, 31)
ID_EJECUCION = datetime.now().strftime("%Y%m%d_%H%M%S")


def conexion_sql(base):
    return pyodbc.connect(f"Driver={{ODBC Driver 17 for SQL Server}};Server={SERVIDOR};"
                          f"Database={base};Trusted_Connection=yes;", timeout=120)


def paso(texto):
    print(f"\n{'-' * 78}\n{texto}\n{'-' * 78}")


# ==============================================================================
# 0. CREACIÓN DE LAS BASES (opcional, --recrear)
# ==============================================================================
def ejecutar_ddl(ruta):
    sql = open(ruta, encoding="utf-8").read()
    cn = pyodbc.connect(f"Driver={{ODBC Driver 17 for SQL Server}};Server={SERVIDOR};"
                        "Database=master;Trusted_Connection=yes;", autocommit=True, timeout=120)
    cur = cn.cursor()
    for lote in re.split(r"^\s*GO\s*$", sql, flags=re.M):
        if lote.strip():
            cur.execute(lote)
    cn.close()


def recrear_bases():
    paso("0. Recreando las bases desde los DDL del repositorio")
    cn = pyodbc.connect(f"Driver={{ODBC Driver 17 for SQL Server}};Server={SERVIDOR};"
                        "Database=master;Trusted_Connection=yes;", autocommit=True, timeout=120)
    cur = cn.cursor()
    respaldo = f"{BD_KIMBALL}_respaldo_{ID_EJECUCION[:8]}"
    if cur.execute(f"SELECT DB_ID('{BD_KIMBALL}')").fetchone()[0]:
        if cur.execute(f"SELECT DB_ID('{respaldo}')").fetchone()[0]:
            sys.exit(f"Ya existe {respaldo}; elimínelo o renómbrelo antes de recrear.")
        cur.execute(f"ALTER DATABASE [{BD_KIMBALL}] SET SINGLE_USER WITH ROLLBACK IMMEDIATE")
        cur.execute(f"ALTER DATABASE [{BD_KIMBALL}] MODIFY NAME = [{respaldo}]")
        cur.execute(f"ALTER DATABASE [{respaldo}] SET MULTI_USER")
        print(f"  Base anterior renombrada como respaldo: {respaldo}")
    if cur.execute(f"SELECT DB_ID('{BD_INMON}')").fetchone()[0]:
        cur.execute(f"ALTER DATABASE [{BD_INMON}] SET SINGLE_USER WITH ROLLBACK IMMEDIATE")
        cur.execute(f"DROP DATABASE [{BD_INMON}]")
        print(f"  {BD_INMON} anterior eliminada (estructura sin datos)")
    # El respaldo conserva los archivos .mdf/.ldf originales: la base nueva usa archivos propios.
    ruta = cur.execute("SELECT CAST(SERVERPROPERTY('InstanceDefaultDataPath') AS NVARCHAR(400))").fetchone()[0]
    for base in (BD_KIMBALL, BD_INMON):
        archivo = os.path.join(ruta, f"{base}_{ID_EJECUCION}")
        cur.execute(f"CREATE DATABASE [{base}] ON (NAME = '{base}', FILENAME = '{archivo}.mdf') "
                    f"LOG ON (NAME = '{base}_log', FILENAME = '{archivo}_log.ldf')")
    cn.close()
    ejecutar_ddl(DDL_KIMBALL)
    print(f"  {BD_KIMBALL} creada con sql/01_DDL_Kimball_DM_Financial.sql")
    ejecutar_ddl(DDL_INMON)
    print(f"  {BD_INMON} creada con sql/02_DDL_Inmon_EDW_Financial.sql")


# ==============================================================================
# 1. EXTRACCIÓN
# ==============================================================================
def extraer():
    paso("1. Extracción desde MySQL remoto (Financial_ijs)")
    cn = pymysql.connect(connect_timeout=30, **MYSQL)
    src = {}
    for tabla in ["districts", "accounts", "clients", "disps", "loans", "orders", "cards", "tkeys"]:
        src[tabla] = pd.read_sql(f"SELECT * FROM `{tabla}`", cn)
    src["trans"] = pd.read_sql("SELECT id, account_id, date, type, operation, amount, balance, "
                               "k_symbol, bank, account FROM trans", cn)
    cn.close()
    for tabla, df in src.items():
        print(f"  {tabla:<10} {len(df):>10,} filas")
    return src


# ==============================================================================
# 2. TRANSFORMACIÓN (staging)
# ==============================================================================
MESES = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto",
         "Septiembre", "Octubre", "Noviembre", "Diciembre"]
DIAS = ["Lunes", "Martes", "Miercoles", "Jueves", "Viernes", "Sabado", "Domingo"]
FRECUENCIA = {"POPLATEK MESICNE": "Extracto mensual", "POPLATEK TYDNE": "Extracto semanal",
              "POPLATEK PO OBRATU": "Extracto despues de cada transaccion"}
ESTADOS = [("A", "Cerrado", "Pagado sin problemas"), ("B", "Cerrado", "Pagado, contrato terminado con deuda"),
           ("C", "Vigente", "En curso, al dia"), ("D", "Vigente", "En curso, en mora")]
ORDENES = {"SIPO": "Servicios del Hogar", "UVER": "Cuota de Prestamo", "POJISTNE": "Pago de Seguros",
           "LEASING": "Arrendamiento / Leasing", "SIN_ESPECIFICAR": "Sin Especificar"}
TIPO_MOV = {"PRIJEM": "Ingreso", "VYDAJ": "Egreso", "VYBER": "Retiro"}
OPERACION = {"VKLAD": "Deposito en efectivo", "PREVOD Z UCTU": "Transferencia entrante",
             "PREVOD NA UCET": "Transferencia saliente", "VYBER": "Retiro en efectivo",
             "VYBER KARTOU": "Retiro con tarjeta", "SIN_ESPECIFICAR": "Abono bancario"}
CONCEPTO = {"SIN_ESPECIFICAR": "Sin especificar", "DUCHOD": "Pension", "UROK": "Intereses ganados",
            "SLUZBY": "Comision por servicios", "SIPO": "Servicios del hogar", "POJISTNE": "Pago de seguro",
            "UVER": "Cuota de prestamo", "SANKC. UROK": "Interes sancionatorio por sobregiro"}
LIMITES_BANDA = [(0.057, "Baja"), (0.090, "Media-baja"), (0.123, "Media-alta"), (np.inf, "Alta")]


def normalizar(valor):
    """NULL y cadena vacía -> SIN_ESPECIFICAR (Carta v8, sección 10)."""
    return valor.strip() if isinstance(valor, str) and valor.strip() else "SIN_ESPECIFICAR"


def categoria_analitica(tipo, k_symbol):
    if tipo == "PRIJEM":
        return "Intereses Ganados" if k_symbol == "UROK" else "Ingreso / Deposito"
    return "Egreso / Gasto" if tipo == "VYDAJ" else "Retiro en Efectivo"


def banda(ratio):
    return next(nombre for limite, nombre in LIMITES_BANDA if ratio <= limite)


def transformar(src):
    paso("2. Transformación en staging")
    st, anomalias = {}, []

    # ---- Dim_Tiempo -------------------------------------------------------------
    fechas = pd.date_range("1993-01-01", FECHA_CORTE)
    st["tiempo"] = pd.DataFrame({
        "fecha": fechas.date, "anio": fechas.year, "semestre": np.where(fechas.month <= 6, 1, 2),
        "trimestre": fechas.quarter, "mes": fechas.month, "nombre_mes": [MESES[m - 1] for m in fechas.month],
        "dia": fechas.day, "dia_semana": fechas.dayofweek + 1, "nombre_dia": [DIAS[d] for d in fechas.dayofweek],
        "es_fin_de_semana": (fechas.dayofweek >= 5).astype(int), "es_fin_de_mes": fechas.is_month_end.astype(int)})

    # ---- Dim_Distrito (A12/A15 = 1995, A13/A16 = 1996) --------------------------
    d = src["districts"]
    st["distrito"] = pd.DataFrame({
        "id_distrito_bk": d.id, "nombre_distrito": d.A2.str.strip(), "region": d.A3.str.strip(),
        "poblacion": d.A4, "salario_promedio": d.A11.astype(float),
        "tasa_desempleo": d.A12.astype(float), "tasa_criminalidad": d.A15.astype(float),
        "tasa_desempleo_1996": d.A13.astype(float), "tasa_criminalidad_1996": d.A16.astype(float)})
    for r in d[d.A12.isna() | d.A15.isna()].itertuples():
        anomalias.append(("districts", str(r.id), f"{r.A2}: desempleo y/o criminalidad 1995 en NULL "
                          f"(1996: {r.A13} y {r.A16})", "Se carga NULL; la imputación la aplica el write-back (script 20)"))

    # ---- Titular de cada cuenta y relación cliente -> cuenta ---------------------
    disps = src["disps"].assign(type=src["disps"].type.str.strip())
    titular = disps[disps.type == "OWNER"].set_index("account_id").client_id
    cuenta_de_cliente = disps.set_index("client_id")

    # ---- Dim_Cuenta ---------------------------------------------------------------
    a, o, l = src["accounts"], src["orders"], src["loans"]
    uver = o[o.k_symbol.str.strip() == "UVER"]
    externo = uver[~uver.account_id.isin(l.account_id)].groupby("account_id").amount.sum().astype(float)
    st["cuenta"] = pd.DataFrame({
        "id_cuenta_bk": a.id, "frecuencia_emision_estado": a.frequency.str.strip().map(FRECUENCIA),
        "fecha_apertura": a.date, "id_distrito_bk": a.district_id,
        "tiene_credito_externo": a.id.isin(externo.index).astype(int),
        "monto_credito_externo": a.id.map(externo).fillna(0.0)})

    # ---- Dim_Cliente --------------------------------------------------------------
    c = src["clients"]
    bn = c.birth_number.astype(str).str.zfill(6)
    anio, mes_raw, dia = 1900 + bn.str[:2].astype(int), bn.str[2:4].astype(int), bn.str[4:6].astype(int)
    mes = np.where(mes_raw > 50, mes_raw - 50, mes_raw)
    nacimiento = pd.to_datetime(dict(year=anio, month=mes, day=dia))
    estado_cuenta = l.set_index("account_id").status.str.strip()
    cuenta_cli = c.id.map(cuenta_de_cliente.account_id)
    estado_cli = cuenta_cli.map(estado_cuenta)
    st["cliente"] = pd.DataFrame({
        "id_cliente_bk": c.id, "sexo": np.where(mes_raw > 50, "F", "M"), "fecha_nacimiento": nacimiento.dt.date,
        "edad_corte": FECHA_CORTE.year - anio,   # corte al 31/12: el cumpleaños ya pasó
        "tipo_disposicion": c.id.map(cuenta_de_cliente.type),
        "etiqueta_buen_pagador": estado_cli.map({"A": 1, "B": 0}),
        "id_distrito_bk": c.district_id})
    tk_validos = set(src["tkeys"].id)
    for r in c[c.tkey_id.notna() & ~c.tkey_id.isin(tk_validos)].itertuples():
        anomalias.append(("clients", str(r.id), f"tkey_id = {int(r.tkey_id)} no existe en tkeys (ids 0-233)",
                          "No se usa tkeys; la etiqueta se deriva de loans.status"))

    # ---- Dim_Operacion (15 combinaciones reales) ----------------------------------
    t = src["trans"]
    t["operacion_n"] = t.operation.map(normalizar)
    t["k_symbol_n"] = t.k_symbol.map(normalizar)
    t["type"] = t.type.str.strip()
    comb = t[["type", "operacion_n", "k_symbol_n"]].drop_duplicates().sort_values(["type", "operacion_n", "k_symbol_n"])
    st["operacion"] = pd.DataFrame({
        "tipo_original": comb.type, "operacion_original": comb.operacion_n, "k_symbol_original": comb.k_symbol_n,
        "tipo_movimiento": comb.type.map(TIPO_MOV),
        "operacion_traducida": [("Cargo bancario" if k in ("SLUZBY", "SANKC. UROK") else OPERACION[op])
                                for op, k in zip(comb.operacion_n, comb.k_symbol_n)],
        "concepto_traducido": comb.k_symbol_n.map(CONCEPTO),
        "categoria_analitica": [categoria_analitica(tp, k) for tp, k in zip(comb.type, comb.k_symbol_n)]})

    # ---- Fact_Transacciones ----------------------------------------------------------
    t["fecha"] = pd.to_datetime(t.date)
    t["balance"] = t.balance.astype(float)
    t = t.sort_values(["account_id", "fecha", "id"])
    st["trans"] = t

    # ---- Fact_Prestamos -------------------------------------------------------------
    l = l.assign(fecha=pd.to_datetime(l.date), status=l.status.str.strip(),
                 amount=l.amount.astype(float), payments=l.payments.astype(float))
    previo = t.merge(l[["account_id", "fecha"]].rename(columns={"fecha": "f_prestamo"}), on="account_id")
    previo = previo[previo.fecha < previo.f_prestamo].groupby("account_id").balance.mean()
    l["meses_corte"] = (FECHA_CORTE.year - l.fecha.dt.year) * 12 + (FECHA_CORTE.month - l.fecha.dt.month)
    vigente = l.status.isin(["C", "D"])
    l["saldo_pendiente"] = np.where(vigente, (l.amount - l.payments * np.minimum(l.duration, l.meses_corte)).clip(lower=0), 0.0)
    l["saldo_previo"] = l.account_id.map(previo)
    l["ratio"] = l.payments / l.saldo_previo
    l["banda"] = l.ratio.map(banda)
    st["prestamos"] = l

    # ---- Fact_Saldo_Cuenta_Mensual (foto periódica con arrastre) ----------------------
    t["mes"] = t.fecha.dt.to_period("M")
    g = t.groupby(["account_id", "mes"])
    mensual = pd.DataFrame({"saldo_fin_mes": g.balance.last(), "saldo_promedio_mes": g.balance.mean(),
                            "num_movimientos_mes": g.size()}).reset_index()
    filas = []
    for cuenta, grupo in mensual.groupby("account_id"):
        meses = pd.period_range(grupo.mes.min(), pd.Period(FECHA_CORTE, "M"), freq="M")
        filas.append(grupo.set_index("mes").reindex(meses).rename_axis("mes").reset_index().assign(account_id=cuenta))
    mensual = pd.concat(filas, ignore_index=True)
    mensual["saldo_fin_mes"] = mensual.groupby("account_id").saldo_fin_mes.ffill()
    mensual["saldo_promedio_mes"] = mensual.saldo_promedio_mes.fillna(mensual.saldo_fin_mes)
    mensual["num_movimientos_mes"] = mensual.num_movimientos_mes.fillna(0).astype(int)
    mensual["en_sobregiro"] = (mensual.saldo_fin_mes < 0).astype(int)
    mensual["fecha_fin_mes"] = mensual.mes.dt.to_timestamp(how="end").dt.date
    st["saldo_mensual"] = mensual

    # ---- Fact_Ordenes ------------------------------------------------------------------
    st["ordenes"] = o.assign(k_symbol_n=o.k_symbol.map(normalizar), amount=o.amount.astype(float))

    st["titular"] = titular
    st["cuenta_distrito"] = a.set_index("id").district_id
    st["cuenta_apertura"] = a.set_index("id").date
    for nombre in ["tiempo", "distrito", "cuenta", "cliente", "operacion", "prestamos", "saldo_mensual", "ordenes"]:
        print(f"  {nombre:<14} {len(st[nombre]):>10,} filas preparadas")
    print(f"  anomalías de la fuente registradas: {len(anomalias)}")
    return st, anomalias


# ==============================================================================
# 3. CARGA
# ==============================================================================
def insertar(cur, tabla, columnas, filas, lote=100_000):
    sql = f"INSERT INTO {tabla} ({', '.join(columnas)}) VALUES ({', '.join('?' * len(columnas))})"
    for i in range(0, len(filas), lote):
        cur.executemany(sql, filas[i:i + lote])
    print(f"  {tabla:<28} {len(filas):>10,} filas")


def nativo(v):
    """Convierte tipos de NumPy/pandas a tipos de Python y NaN a NULL."""
    if v is None or (isinstance(v, (float, np.floating)) and np.isnan(v)):
        return None
    return v.item() if isinstance(v, np.generic) else v


def filas(df):
    return [tuple(nativo(x) for x in r) for r in df.itertuples(index=False, name=None)]


def cargar(st):
    paso("3. Carga en SQL Server (DM_Financial_Kimball_v2)")
    cn = conexion_sql(BD_KIMBALL)
    cur = cn.cursor()
    cur.fast_executemany = True
    for tabla in ["Fact_Transacciones", "Fact_Saldo_Cuenta_Mensual", "Fact_Ordenes", "Fact_Prestamos",
                  "Dim_Cliente", "Dim_Cuenta", "Dim_Distrito", "Dim_Tiempo", "Dim_Estado_Prestamo",
                  "Dim_Operacion", "Dim_Orden"]:
        cur.execute(f"DELETE FROM {tabla}")
        # Reiniciar el contador solo si la tabla ya tuvo filas (si no, la primera clave sería 0)
        cur.execute(f"IF EXISTS (SELECT 1 FROM sys.identity_columns WHERE object_id = OBJECT_ID('{tabla}') "
                    f"AND last_value IS NOT NULL) DBCC CHECKIDENT ('{tabla}', RESEED, 0)")
    cn.commit()

    for tabla, clave in [("Dim_Tiempo", "tiempo"), ("Dim_Distrito", "distrito"), ("Dim_Operacion", "operacion")]:
        insertar(cur, tabla, list(st[clave].columns), filas(st[clave]))
    insertar(cur, "Dim_Estado_Prestamo", ["codigo_estado", "condicion", "descripcion"], ESTADOS)
    insertar(cur, "Dim_Orden", ["k_symbol_original", "categoria_orden_traducida"], list(ORDENES.items()))
    cn.commit()

    sk_tiempo = {r[0]: r[1] for r in cur.execute("SELECT fecha, sk_tiempo FROM Dim_Tiempo")}
    sk_distrito = {r[0]: r[1] for r in cur.execute("SELECT id_distrito_bk, sk_distrito FROM Dim_Distrito")}
    sk_estado = {r[0]: r[1] for r in cur.execute("SELECT codigo_estado, sk_estado_prestamo FROM Dim_Estado_Prestamo")}
    sk_orden = {r[0]: r[1] for r in cur.execute("SELECT k_symbol_original, sk_orden_tipo FROM Dim_Orden")}
    sk_operacion = {(r[0], r[1], r[2]): r[3] for r in
                    cur.execute("SELECT tipo_original, operacion_original, k_symbol_original, sk_operacion FROM Dim_Operacion")}

    cu = st["cuenta"]
    insertar(cur, "Dim_Cuenta", ["id_cuenta_bk", "frecuencia_emision_estado", "fecha_apertura", "sk_distrito",
                                 "tiene_credito_externo", "monto_credito_externo"],
             [(int(r.id_cuenta_bk), r.frecuencia_emision_estado, r.fecha_apertura, sk_distrito[r.id_distrito_bk],
               int(r.tiene_credito_externo), float(r.monto_credito_externo)) for r in cu.itertuples()])
    cl = st["cliente"]
    insertar(cur, "Dim_Cliente", ["id_cliente_bk", "sexo", "fecha_nacimiento", "edad_corte", "tipo_disposicion",
                                  "etiqueta_buen_pagador", "sk_distrito"],
             [(int(r.id_cliente_bk), r.sexo, r.fecha_nacimiento, int(r.edad_corte), r.tipo_disposicion,
               None if pd.isna(r.etiqueta_buen_pagador) else int(r.etiqueta_buen_pagador), sk_distrito[r.id_distrito_bk])
              for r in cl.itertuples()])
    cn.commit()

    sk_cuenta = {r[0]: r[1] for r in cur.execute("SELECT id_cuenta_bk, sk_cuenta FROM Dim_Cuenta")}
    sk_cliente = {r[0]: r[1] for r in cur.execute("SELECT id_cliente_bk, sk_cliente FROM Dim_Cliente")}
    titular, dist_cta = st["titular"], st["cuenta_distrito"]
    claves = lambda cta: (sk_cuenta[cta], sk_cliente[titular[cta]], sk_distrito[dist_cta[cta]])

    pr = st["prestamos"]
    insertar(cur, "Fact_Prestamos",
             ["sk_tiempo", "sk_cuenta", "sk_cliente", "sk_distrito", "sk_estado_prestamo", "id_prestamo_bk",
              "monto_prestamo", "plazo_meses", "pago_mensual", "meses_transcurridos_al_corte",
              "saldo_pendiente_estimado", "saldo_promedio_previo", "ratio_cuota_saldo_previo", "banda_capacidad"],
             [(sk_tiempo[r.fecha.date()], *claves(r.account_id), sk_estado[r.status], int(r.id), float(r.amount),
               int(r.duration), float(r.payments), int(r.meses_corte), round(float(r.saldo_pendiente), 2),
               round(float(r.saldo_previo), 2), round(float(r.ratio), 4), r.banda) for r in pr.itertuples()])

    od = st["ordenes"]
    apertura = st["cuenta_apertura"]
    insertar(cur, "Fact_Ordenes",
             ["sk_tiempo_apertura_cuenta", "sk_cuenta", "sk_cliente", "sk_distrito", "sk_orden_tipo", "id_orden_bk", "monto_orden"],
             [(sk_tiempo[apertura[r.account_id]], *claves(r.account_id), sk_orden[r.k_symbol_n], int(r.id), float(r.amount))
              for r in od.itertuples()])
    cn.commit()

    tr = st["trans"]
    insertar(cur, "Fact_Transacciones",
             ["sk_tiempo", "sk_cuenta", "sk_cliente", "sk_distrito", "sk_operacion", "id_transaccion_bk",
              "monto_transaccion", "saldo_cuenta"],
             [(sk_tiempo[f.date()], *claves(cta), sk_operacion[(tp, opn, ks)], int(i), float(m), float(b))
              for f, cta, tp, opn, ks, i, m, b in zip(tr.fecha, tr.account_id, tr.type, tr.operacion_n,
                                                       tr.k_symbol_n, tr.id, tr.amount, tr.balance)])
    cn.commit()

    sm = st["saldo_mensual"]
    insertar(cur, "Fact_Saldo_Cuenta_Mensual",
             ["sk_cuenta", "sk_mes", "sk_cliente", "sk_distrito", "saldo_fin_mes", "saldo_promedio_mes",
              "num_movimientos_mes", "en_sobregiro"],
             [(sk_cuenta[cta], sk_tiempo[fm], sk_cliente[titular[cta]], sk_distrito[dist_cta[cta]],
               float(s), round(float(p), 2), int(n), int(sb))
              for cta, fm, s, p, n, sb in zip(sm.account_id, sm.fecha_fin_mes, sm.saldo_fin_mes,
                                               sm.saldo_promedio_mes, sm.num_movimientos_mes, sm.en_sobregiro)])
    cn.commit()
    cn.close()


# ==============================================================================
# 4. VALIDACIÓN (Carta v8, sección 12.3) Y AUDITORÍA
# ==============================================================================
def validar(src, st, anomalias):
    paso("4. Validación contra la fuente y registro de auditoría")
    cn = conexion_sql(BD_KIMBALL)
    cur = cn.cursor()
    q = lambda s: cur.execute(s).fetchall()
    uno = lambda s: q(s)[0][0]
    pruebas = []

    def registrar(prueba, esperado, obtenido, estado=None):
        estado = estado or ("OK" if str(esperado) == str(obtenido) else "FALLA")
        pruebas.append({"prueba": prueba, "esperado": str(esperado), "obtenido": str(obtenido), "resultado": estado})
        print(f"  [{estado:<5}] {prueba}: esperado {esperado} | obtenido {obtenido}")

    l, t, o = src["loans"], src["trans"], src["orders"]
    # 1. Conteos
    a_python = lambda d: {k: (float(v) if isinstance(v, (float, np.floating)) else int(v)) for k, v in sorted(d.items())}
    estados_src = a_python(l.status.str.strip().value_counts().to_dict())
    estados_dm = dict(q("SELECT e.codigo_estado, COUNT(*) FROM Fact_Prestamos f JOIN Dim_Estado_Prestamo e "
                        "ON e.sk_estado_prestamo = f.sk_estado_prestamo GROUP BY e.codigo_estado ORDER BY 1"))
    registrar("1. Préstamos por estado", estados_src, estados_dm)
    for tabla, n_src, n_dm in [("trans -> Fact_Transacciones", len(t), uno("SELECT COUNT(*) FROM Fact_Transacciones")),
                               ("orders -> Fact_Ordenes", len(o), uno("SELECT COUNT(*) FROM Fact_Ordenes")),
                               ("clients -> Dim_Cliente", len(src["clients"]), uno("SELECT COUNT(*) FROM Dim_Cliente")),
                               ("accounts -> Dim_Cuenta", len(src["accounts"]), uno("SELECT COUNT(*) FROM Dim_Cuenta")),
                               ("districts -> Dim_Distrito", len(src["districts"]), uno("SELECT COUNT(*) FROM Dim_Distrito"))]:
        registrar(f"1. Conteo {tabla}", n_src, n_dm)
    # 2. Totales monetarios
    registrar("2. Monto de préstamos", f"{l.amount.astype(float).sum():,.2f}", f"{uno('SELECT SUM(monto_prestamo) FROM Fact_Prestamos'):,.2f}")
    registrar("2. Monto de transacciones", f"{t.amount.astype(float).sum():,.2f}", f"{uno('SELECT SUM(monto_transaccion) FROM Fact_Transacciones'):,.2f}")
    registrar("2. Monto de órdenes", f"{o.amount.astype(float).sum():,.2f}", f"{uno('SELECT SUM(monto_orden) FROM Fact_Ordenes'):,.2f}")
    # 3. Medida semiaditiva
    saldo_src = st["trans"].groupby("account_id").balance.last().sum()
    saldo_dic = uno("SELECT SUM(s.saldo_fin_mes) FROM Fact_Saldo_Cuenta_Mensual s JOIN Dim_Tiempo t ON t.sk_tiempo = s.sk_mes "
                    "WHERE t.anio = 1998 AND t.mes = 12")
    registrar("3. Saldo neto al corte (foto dic-1998)", f"{saldo_src:,.2f}", f"{saldo_dic:,.2f}")
    registrar("3. Cuentas en sobregiro al corte", 39, uno("SELECT COUNT(*) FROM Fact_Saldo_Cuenta_Mensual s JOIN Dim_Tiempo t "
                                                          "ON t.sk_tiempo = s.sk_mes WHERE t.anio = 1998 AND t.mes = 12 AND s.en_sobregiro = 1"))
    registrar("3. Filas de la foto mensual", 185615, uno("SELECT COUNT(*) FROM Fact_Saldo_Cuenta_Mensual"))
    # 4. Integridad referencial (las FK están declaradas; se confirma cero nulos en claves)
    huerfanas = sum(uno(f"SELECT COUNT(*) FROM {h} WHERE {k} IS NULL") for h, k in
                    [("Fact_Prestamos", "sk_cliente"), ("Fact_Transacciones", "sk_operacion"), ("Fact_Ordenes", "sk_orden_tipo")])
    registrar("4. Claves nulas en hechos (FK declaradas)", 0, huerfanas)
    # 5. Categoría analítica de operación
    cat = dict(q("SELECT o.categoria_analitica, COUNT(*) FROM Fact_Transacciones f JOIN Dim_Operacion o "
                 "ON o.sk_operacion = f.sk_operacion GROUP BY o.categoria_analitica"))
    registrar("5. Movimientos por categoría", {"Egreso / Gasto": 634571, "Ingreso / Deposito": 221969,
                                               "Intereses Ganados": 183114, "Retiro en Efectivo": 16666},
              dict(sorted(cat.items())))
    registrar("5. Filas de Dim_Operacion", 15, uno("SELECT COUNT(*) FROM Dim_Operacion"))
    # 6. Desglose por región (fuente con distrito de la cuenta vs Data Mart)
    reg = src["districts"].set_index("id").A3.str.strip()
    cta_reg = src["accounts"].set_index("id").district_id.map(reg)
    cartera_src = l.assign(r=l.account_id.map(cta_reg)).groupby("r").amount.sum().astype(float).round(2).to_dict()
    cartera_dm = {k: float(v) for k, v in q("SELECT d.region, SUM(f.monto_prestamo) FROM Fact_Prestamos f JOIN Dim_Distrito d "
                                            "ON d.sk_distrito = f.sk_distrito GROUP BY d.region")}
    registrar("6. Cartera por región", a_python(cartera_src), a_python(cartera_dm))
    saldo_reg_src = st["trans"].groupby("account_id").balance.last().groupby(cta_reg).sum().round(2).to_dict()
    saldo_reg_dm = {k: float(v) for k, v in q("SELECT d.region, SUM(s.saldo_fin_mes) FROM Fact_Saldo_Cuenta_Mensual s "
                                              "JOIN Dim_Tiempo t ON t.sk_tiempo = s.sk_mes JOIN Dim_Distrito d ON d.sk_distrito = s.sk_distrito "
                                              "WHERE t.anio = 1998 AND t.mes = 12 GROUP BY d.region")}
    registrar("6. Saldo al corte por región", a_python(saldo_reg_src), a_python(saldo_reg_dm))
    # 7. Capacidad de pago
    bandas = {b: (n, i) for b, n, i in q("SELECT banda_capacidad, COUNT(*), SUM(CASE WHEN e.codigo_estado IN ('B','D') THEN 1 ELSE 0 END) "
                                        "FROM Fact_Prestamos f JOIN Dim_Estado_Prestamo e ON e.sk_estado_prestamo = f.sk_estado_prestamo "
                                        "GROUP BY banda_capacidad")}
    registrar("7. Bandas de capacidad (préstamos, impagos)",
              {"Alta": (172, 40), "Baja": (171, 5), "Media-alta": (172, 15), "Media-baja": (167, 16)}, dict(sorted(bandas.items())))
    registrar("7. Cuentas con crédito externo", 35, uno("SELECT COUNT(*) FROM Dim_Cuenta WHERE tiene_credito_externo = 1"))
    registrar("7. Saldo por cobrar estimado C + D", "46,620,926.00",
              f"{uno('SELECT SUM(saldo_pendiente_estimado) FROM Fact_Prestamos'):,.2f}")
    # 8. Reproducibilidad estadística desde el Data Mart
    fp = pd.DataFrame([tuple(r) for r in q("SELECT t.anio, e.codigo_estado, f.ratio_cuota_saldo_previo FROM Fact_Prestamos f "
                                           "JOIN Dim_Tiempo t ON t.sk_tiempo = f.sk_tiempo JOIN Dim_Estado_Prestamo e "
                                           "ON e.sk_estado_prestamo = f.sk_estado_prestamo")], columns=["anio", "estado", "ratio"])
    fp["ratio"] = fp.ratio.astype(float)
    v = fp[fp.estado.isin(["C", "D"]) & fp.anio.between(1994, 1997)]
    chi_anio = stats.chi2_contingency(pd.crosstab(v.anio, v.estado))
    registrar("8. χ² mora × año 1994-1997 (p)", 0.93, round(chi_anio[1], 2))
    fp["q"] = pd.qcut(fp.ratio.rank(method="first"), 4, labels=False)
    chi_cap = stats.chi2_contingency(pd.crosstab(fp.q, fp.estado.isin(["B", "D"])))
    registrar("8. χ² impago × cuartil de capacidad", 39.01, round(chi_cap[0], 2))

    # ---- Registro de auditoría -------------------------------------------------------
    cur.fast_executemany = True
    cur.executemany("INSERT INTO Auditoria_Carga (id_ejecucion, prueba, valor_esperado, valor_obtenido, resultado) "
                    "VALUES (?, ?, ?, ?, ?)", [(ID_EJECUCION, p["prueba"], p["esperado"][:200], p["obtenido"][:200], p["resultado"])
                                               for p in pruebas])
    if anomalias:
        cur.executemany("INSERT INTO Auditoria_Anomalias (id_ejecucion, tabla_origen, clave_origen, descripcion, tratamiento) "
                        "VALUES (?, ?, ?, ?, ?)", [(ID_EJECUCION, *a) for a in anomalias])
    cn.commit()
    filas = {tb: uno(f"SELECT COUNT(*) FROM {tb}") for tb in
             ["Dim_Tiempo", "Dim_Distrito", "Dim_Cuenta", "Dim_Cliente", "Dim_Estado_Prestamo", "Dim_Operacion", "Dim_Orden",
              "Fact_Prestamos", "Fact_Transacciones", "Fact_Saldo_Cuenta_Mensual", "Fact_Ordenes"]}
    cn.close()
    return pruebas, filas


def vistas_powerbi():
    """Recrea las vistas de sql/04 que consumen los tableros."""
    ruta = os.path.join(BASE_DIR, "sql", "04_Vistas_PowerBI_Kimball.sql")
    sql = open(ruta, encoding="utf-8").read()
    cn = conexion_sql(BD_KIMBALL)
    cn.autocommit = True
    for lote in re.split(r"^\s*GO\s*$", sql, flags=re.M):
        codigo = "\n".join(x for x in lote.splitlines() if not x.strip().startswith("--")).strip()
        if codigo.upper().startswith("CREATE"):
            cn.cursor().execute(lote)
    cn.close()
    print("  Vistas de sql/04 recreadas (vw_PBI_Saldo_Final_Cuenta, vw_PBI_Trans_Anual_Cuenta)")


def main():
    t0 = time.time()
    print("=" * 78)
    print(f"ETL Financial_ijs (MySQL) -> {BD_KIMBALL} (SQL Server) · ejecución {ID_EJECUCION}")
    print("=" * 78)
    if "--recrear" in sys.argv:
        recrear_bases()
    src = extraer()
    st, anomalias = transformar(src)
    cargar(st)
    vistas_powerbi()
    pruebas, filas = validar(src, st, anomalias)
    resumen = {
        "id_ejecucion": ID_EJECUCION,
        "fuente": f"{MYSQL['host']}/{MYSQL['database']}",
        "destino": f"{SERVIDOR}/{BD_KIMBALL}",
        "duracion_segundos": round(time.time() - t0, 1),
        "filas_extraidas": {k: int(len(v)) for k, v in src.items()},
        "filas_cargadas": filas,
        "pruebas": pruebas,
        "pruebas_ok": sum(p["resultado"] == "OK" for p in pruebas),
        "pruebas_total": len(pruebas),
        "anomalias_fuente": [dict(zip(["tabla", "clave", "descripcion", "tratamiento"], a)) for a in anomalias],
    }
    with open(SALIDA_JSON, "w", encoding="utf-8") as f:
        json.dump(resumen, f, ensure_ascii=False, indent=2)
    paso(f"Fin: {resumen['pruebas_ok']}/{resumen['pruebas_total']} pruebas OK en {resumen['duracion_segundos']} s")
    print(f"Resumen: {SALIDA_JSON}")


if __name__ == "__main__":
    main()
