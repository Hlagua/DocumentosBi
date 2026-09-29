"""
==============================================================================
UNIVERSIDAD TÉCNICA DE AMBATO - Inteligencia de Negocios
AUTORES: Alison Marcela Cobos Taco / Henry Daniel Lagua Flores
==============================================================================
REPARAR_TODO.py — deja listo este equipo para abrir los dashboards

USO (desde la carpeta del repositorio, después de "git pull"):
    python REPARAR_TODO.py

QUÉ HACE (solo lo que falta; se puede ejecutar varias veces sin problema):
  1. Instala las librerías de Python que falten (pandas, numpy, scipy, pyodbc,
     pymysql, pymongo, matplotlib).
  2. Arranca SQL Server LocalDB (MSSQLLocalDB).
  3. KIMBALL: si el Data Mart DM_Financial_Kimball_v2 no existe, está incompleto
     o es de una versión anterior, lo recarga desde la base remota
     (scripts 31 --recrear, 32, 33 y 34; necesita internet, tarda varios minutos).
  4. Crea la vista del dashboard (sql/04_Vistas_PowerBI_Kimball.sql).
  5. MONGODB: si MongoDB está instalado y su base Financial no está al día, la
     migra desde Kimball (script 35).
  6. Carga las recomendaciones del Informe 04 y las tablas de las páginas R1–R3
     en los dos motores (scripts 42 y 43).
  7. Verifica todo con las cifras de control y dice qué hacer en Power BI.

No modifica ningún script del proyecto: los ejecuta en el orden correcto.
==============================================================================
"""
import importlib
import json
import os
import re
import subprocess
import sys
import time

RAIZ = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.join(RAIZ, "scripts")
SERVIDOR = r"(localdb)\MSSQLLocalDB"
BD = "DM_Financial_Kimball_v2"
MODELO = os.path.join(RAIZ, "dashboards", "Dashboard_Financial_Kimball", "Dashboard_Financial_Kimball.Dataset", "model.bim")
LIBRERIAS = {"pandas": "pandas", "numpy": "numpy", "scipy": "scipy", "pyodbc": "pyodbc", "pymysql": "pymysql",
             "pymongo": "pymongo", "matplotlib": "matplotlib"}

# Cifras de control del Data Mart (Informes 09 y 10) y de MongoDB (Informe 05)
CONTROL_KIMBALL = {"Fact_Prestamos": 682, "Fact_Ordenes": 6471, "Fact_Transacciones": 1056320,
                   "Fact_Saldo_Cuenta_Mensual": 185615, "Dim_Cliente": 5369, "Dim_Cuenta": 4500, "Dim_Distrito": 77}
COLUMNAS_KIMBALL = {"Fact_Prestamos": ["banda_capacidad", "ratio_cuota_saldo_previo", "saldo_pendiente_estimado"],
                    "Dim_Operacion": ["categoria_analitica"], "Dim_Cuenta": ["tiene_credito_externo"],
                    "Dim_Cliente": ["segmento_edad", "arquetipo_demografico", "calificacion_pago_desc"]}
CONTROL_DASHBOARD = {"Recomendacion_Cuenta": 4500, "Dim_Producto": 8, "Recomendacion_Producto": 26986,
                     "Adopcion_Producto": 8604, "Capacidad_Prestamo": 4500, "Evaluacion_Recomendador": 8,
                     "Asociacion_Producto": 56, "Regla_Capacidad": 7}
CONTROL_MONGO = {"distritos": 77, "prestamos": 682, "ordenes": 6471, "FinancialMongo": 5369,
                 "transacciones": 1056320, "saldos_mensuales": 185615}
CONTROL_MONGO_DASHBOARD = {"recomendaciones": 4500, "dim_producto": 8, "recomendacion_producto": 26986,
                           "adopcion_producto": 8604, "capacidad_prestamo": 4500, "evaluacion_recomendador": 8,
                           "asociacion_producto": 56, "regla_capacidad": 7}


def titulo(texto):
    print("\n" + "=" * 78 + f"\n{texto}\n" + "=" * 78, flush=True)


def ejecutar(script, *argumentos, obligatorio=True):
    """Ejecuta un script del proyecto con este mismo Python."""
    print(f"\n>>> python scripts/{script} {' '.join(argumentos)}", flush=True)
    r = subprocess.run([sys.executable, os.path.join(SCRIPTS, script), *argumentos], cwd=RAIZ,
                       env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    if r.returncode != 0 and obligatorio:
        sys.exit(f"\nERROR: falló scripts/{script}. Revise el mensaje de arriba y vuelva a ejecutar REPARAR_TODO.py.")
    return r.returncode == 0


# ---------------------------------------------------------------- 1. Python
def paso_librerias():
    titulo("1/7 · Librerías de Python")
    print(f"Python: {sys.executable} ({sys.version.split()[0]})")
    faltan = []
    for modulo, paquete in LIBRERIAS.items():
        try:
            importlib.import_module(modulo)
        except ImportError:
            faltan.append(paquete)
    if faltan:
        print(f"Instalando: {', '.join(faltan)}")
        subprocess.run([sys.executable, "-m", "pip", "install", "--quiet", *faltan], check=True)
        importlib.invalidate_caches()
    print("OK: librerías disponibles.")


# ---------------------------------------------------------------- 2. SQL Server
def conectar(base="master", intentos=6):
    import pyodbc
    if "ODBC Driver 17 for SQL Server" not in pyodbc.drivers():
        sys.exit("ERROR: falta el 'ODBC Driver 17 for SQL Server'. Descárguelo de Microsoft "
                 "(https://learn.microsoft.com/sql/connect/odbc/download-odbc-driver-for-sql-server), instálelo "
                 "y vuelva a ejecutar REPARAR_TODO.py.")
    ultimo = None
    for _ in range(intentos):
        try:
            return pyodbc.connect(f"Driver={{ODBC Driver 17 for SQL Server}};Server={SERVIDOR};Database={base};"
                                  "Trusted_Connection=yes;", timeout=30, autocommit=True)
        except pyodbc.Error as e:
            ultimo = e
            time.sleep(10)
    raise ultimo


def liberar_localdb():
    """Si quedó un proceso de LocalDB colgado (la instancia figura detenida pero el proceso sigue vivo),
    lo cierra: es el proceso de SQL Server de ESTE usuario para la instancia MSSQLLocalDB."""
    salida = subprocess.run(["powershell", "-NoProfile", "-Command",
                             "Get-CimInstance Win32_Process -Filter \"Name='sqlservr.exe'\" | "
                             "Where-Object { $_.CommandLine -like '*LocalDB*MSSQLLocalDB*' } | "
                             "ForEach-Object { Stop-Process -Id $_.ProcessId -Force; $_.ProcessId }"],
                            capture_output=True, text=True)
    if salida.stdout.strip():
        print(f"Se cerró un proceso de LocalDB colgado (PID {salida.stdout.strip()}).")


def paso_sql_server():
    titulo("2/7 · SQL Server LocalDB")
    if subprocess.run(["sqllocaldb", "info"], capture_output=True).returncode != 0:
        sys.exit("ERROR: no se encontró SQL Server LocalDB. Instálelo (SQL Server Express LocalDB) y vuelva a ejecutar.")
    if subprocess.run(["sqllocaldb", "info", "MSSQLLocalDB"], capture_output=True).returncode != 0:
        subprocess.run(["sqllocaldb", "create", "MSSQLLocalDB"], capture_output=True)
    if subprocess.run(["sqllocaldb", "start", "MSSQLLocalDB"], capture_output=True).returncode != 0:
        liberar_localdb()
        time.sleep(3)
        subprocess.run(["sqllocaldb", "start", "MSSQLLocalDB"], capture_output=True)
    cn = conectar()
    cn.close()
    print("OK: LocalDB en ejecución.")


# ---------------------------------------------------------------- 3 y 4. Kimball
def estado_kimball():
    """Devuelve la lista de problemas del Data Mart (vacía = completo y de la versión actual)."""
    cn = conectar()
    if not cn.cursor().execute("SELECT DB_ID(?)", BD).fetchone()[0]:
        return [f"la base {BD} no existe"]
    cn.close()
    cur = conectar(BD).cursor()
    problemas = []
    tablas = {t for (t,) in cur.execute("SELECT name FROM sys.tables")}
    for tabla, esperado in CONTROL_KIMBALL.items():
        if tabla not in tablas:
            problemas.append(f"falta la tabla {tabla}")
        else:
            n = cur.execute(f"SELECT COUNT(*) FROM {tabla}").fetchone()[0]
            if n != esperado:
                problemas.append(f"{tabla} tiene {n:,} filas (se esperaban {esperado:,})")
    for tabla, columnas in COLUMNAS_KIMBALL.items():
        existentes = {c for (c,) in cur.execute("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = ?", tabla)}
        for c in columnas:
            if existentes and c not in existentes:
                problemas.append(f"a {tabla} le falta la columna {c} (versión anterior)")
    if "Fact_Transacciones" in tablas and \
            cur.execute("SELECT COUNT(*) FROM Fact_Transacciones WHERE sk_concepto IS NULL").fetchone()[0]:
        problemas.append("la completitud de datos no se aplicó (scripts 32 a 34)")
    return problemas


def paso_kimball():
    titulo("3/7 · Data Mart Kimball")
    problemas = estado_kimball()
    if not problemas:
        print("OK: el Data Mart está completo y es de la versión actual (Carta v8).")
        return
    print("El Data Mart necesita recargarse:\n  - " + "\n  - ".join(problemas))
    print("\nSe recarga desde la base remota relational.fel.cvut.cz (requiere internet; tarda varios minutos).")
    print("Si ya existe una versión anterior, el script 31 la conserva como respaldo antes de crear la nueva.")
    ejecutar("31_etl_oltp_a_kimball.py", "--recrear")
    ejecutar("32_extraer_dataframes_kimball.py")
    ejecutar("33_completitud_datos.py")
    ejecutar("34_carga_completitud_kimball.py")
    problemas = estado_kimball()
    if problemas:
        sys.exit("ERROR: el Data Mart sigue incompleto:\n  - " + "\n  - ".join(problemas))
    print("OK: Data Mart recargado.")


def paso_vista():
    titulo("4/7 · Vista del dashboard (sql/04)")
    texto = open(os.path.join(RAIZ, "sql", "04_Vistas_PowerBI_Kimball.sql"), encoding="utf-8").read()
    cur = conectar(BD).cursor()
    for lote in re.split(r"^\s*GO\s*$", texto, flags=re.M | re.I):
        sentencia = "\n".join(l for l in lote.splitlines() if not l.strip().upper().startswith("USE "))
        sin_comentarios = re.sub(r"--.*", "", sentencia).strip()
        if sin_comentarios and not sin_comentarios.upper().startswith("SELECT"):
            cur.execute(sentencia)
    n = cur.execute("SELECT SUM(num_transacciones) FROM vw_PBI_Trans_Anual_Cuenta").fetchone()[0]
    if n != CONTROL_KIMBALL["Fact_Transacciones"]:
        sys.exit(f"ERROR: la vista suma {n} movimientos (se esperaban {CONTROL_KIMBALL['Fact_Transacciones']:,}).")
    print("OK: vw_PBI_Trans_Anual_Cuenta creada (1,056,320 movimientos).")


# ---------------------------------------------------------------- 5. MongoDB
def mongo():
    """Base Financial de MongoDB, o None si MongoDB no está disponible en este equipo."""
    import pymongo
    for intento in range(2):
        try:
            cliente = pymongo.MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=5000)
            cliente.admin.command("ping")
            return cliente["Financial"]
        except Exception:
            if intento == 0:   # intenta iniciar el servicio de Windows (puede requerir administrador)
                subprocess.run(["net", "start", "MongoDB"], capture_output=True)
                time.sleep(5)
    return None


def paso_mongo():
    titulo("5/7 · MongoDB")
    db = mongo()
    if db is None:
        print("AVISO: MongoDB no está en ejecución en localhost:27017. Se prepara solo SQL Server (dashboard Kimball).\n"
              "       Para el dashboard MongoDB: instale/inicie MongoDB y vuelva a ejecutar REPARAR_TODO.py.")
        return False
    existentes = set(db.list_collection_names())
    malas = [c for c, n in CONTROL_MONGO.items() if c not in existentes or db[c].estimated_document_count() != n]
    if not malas and db.saldos_mensuales.find_one({}, {"en_sobregiro": 1}) is not None:
        print("OK: la base Financial de MongoDB está al día.")
        return True
    print(f"La base Financial necesita migrarse ({', '.join(malas) or 'versión anterior'}).")
    ejecutar("35_migrar_kimball_a_mongodb.py")
    print("OK: MongoDB migrado desde Kimball.")
    return True


# ---------------------------------------------------------------- 6. Recomendaciones
def conteos_sql(tablas):
    cur = conectar(BD).cursor()
    existentes = {t for (t,) in cur.execute("SELECT name FROM sys.tables")}
    return {t: (cur.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] if t in existentes else 0) for t in tablas}


def paso_recomendaciones(hay_mongo):
    titulo("6/7 · Recomendaciones (Informe 04) y páginas R1–R3")
    # Los scripts 42 y 43 cargan SQL Server y luego MongoDB. Sin MongoDB la parte de SQL Server queda
    # cargada igual y el error de conexión a MongoDB se ignora.
    ejecutar("42_cargar_recomendaciones.py", obligatorio=hay_mongo)
    ejecutar("43_recomendadores_dashboard.py", obligatorio=hay_mongo)
    conteos = conteos_sql(CONTROL_DASHBOARD)
    malas = {t: n for t, n in conteos.items() if n != CONTROL_DASHBOARD[t]}
    if malas:
        sys.exit(f"ERROR: tablas del dashboard incompletas en SQL Server: {malas}")
    print("OK: recomendaciones cargadas.")


# ---------------------------------------------------------------- 7. Verificación
def paso_verificacion(hay_mongo):
    titulo("7/7 · Verificación final")
    modelo = json.load(open(MODELO, encoding="utf-8"))
    objetos = sorted({m.group(1) for t in modelo["model"]["tables"]
                      for m in [re.search(r'Item="([^"]+)"', "\n".join(t["partitions"][0]["source"]["expression"]))] if m})
    cur = conectar(BD).cursor()
    existentes = {n for (n,) in cur.execute("SELECT name FROM sys.objects WHERE type IN ('U', 'V')")}
    faltan = [o for o in objetos if o not in existentes]
    if faltan:
        sys.exit(f"ERROR: al Data Mart le faltan objetos que usa el dashboard: {faltan}")
    print(f"SQL Server: los {len(objetos)} objetos que lee el dashboard Kimball existen.")
    saldo = cur.execute("SELECT SUM(s.saldo_fin_mes) FROM Fact_Saldo_Cuenta_Mensual s JOIN Dim_Tiempo t "
                        "ON t.sk_tiempo = s.sk_mes WHERE t.anio = 1998 AND t.mes = 12").fetchone()[0]
    print(f"  Préstamos 682 · transacciones 1,056,320 · saldo al corte {float(saldo):,.0f} (esperado 197,140,434)")
    if hay_mongo:
        db = mongo()
        malas = {c: db[c].estimated_document_count() for c in {**CONTROL_MONGO, **CONTROL_MONGO_DASHBOARD}
                 if db[c].estimated_document_count() != {**CONTROL_MONGO, **CONTROL_MONGO_DASHBOARD}[c]}
        if malas:
            sys.exit(f"ERROR: colecciones de MongoDB con conteos distintos a los esperados: {malas}")
        print(f"MongoDB: las {len(CONTROL_MONGO) + len(CONTROL_MONGO_DASHBOARD)} colecciones del dashboard están completas.")

    titulo("LISTO")
    print("Dashboard Kimball:  abra dashboards/Dashboard_Financial_Kimball/Dashboard_Financial_Kimball.pbip → Inicio → Actualizar.")
    if hay_mongo:
        print("Dashboard MongoDB:  abra dashboards/Dashboard_Financial_Mongo/Dashboard_Financial_Mongo.pbip → Actualizar.\n"
              "  Requisito de Power BI: Archivo → Opciones → Scripts de Python → un Python de python.org (NO el de la\n"
              "  Microsoft Store) con: python -m pip install pandas==3.0.5 pymongo==4.18.1 matplotlib==3.10.7")
        if "WindowsApps" in sys.executable:
            print("  AVISO: este Python es el de la Microsoft Store; Power BI no puede usarlo para el dashboard MongoDB.")
    print("Si Power BI pregunta por actualizar el modelo a TMDL: elija 'No actualizar'.")


def main():
    os.chdir(RAIZ)
    paso_librerias()
    paso_sql_server()
    paso_kimball()
    paso_vista()
    hay_mongo = paso_mongo()
    paso_recomendaciones(hay_mongo)
    paso_verificacion(hay_mongo)


if __name__ == "__main__":
    main()
