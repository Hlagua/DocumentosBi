"""
==============================================================================
UNIVERSIDAD TÉCNICA DE AMBATO - Inteligencia de Negocios
AUTORES: Alison Marcela Cobos Taco / Henry Daniel Lagua Flores
==============================================================================
ARCHIVO: 34_carga_completitud_kimball.py
PASO 3 DE 3 DE LA COMPLETITUD DE DATOS (32 -> 33 -> 34)
DESCRIPCIÓN: Carga en DM_Financial_Kimball_v2 los datos completados y
             verificados por el script 33 (write-back), y valida el resultado:
               * Dim_Distrito: imputación del distrito 69 y trazabilidad
               * Dim_Cliente: atributos de enriquecimiento (macro-región,
                 segmento, arquetipo, préstamo, órdenes, saldo, calificación)
               * Dim_Concepto_Movimiento + Fact_Transacciones.sk_concepto:
                 concepto completado de cada transacción
             Registra las pruebas en Auditoria_Carga y el resumen en
             metricas_carga_completitud.json.
REQUISITO: haber ejecutado 31 (carga), 32 (DataFrames) y 33 (completitud) sin fallas.
USO: python scripts/34_carga_completitud_kimball.py
==============================================================================
"""
import json
import os
import sys
import time
import unicodedata
from datetime import datetime

import numpy as np
import pandas as pd
import pyodbc

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DF = os.path.join(BASE_DIR, "dataframes")
SALIDA_JSON = os.path.join(BASE_DIR, "metricas_carga_completitud.json")
KIMBALL = ("Driver={ODBC Driver 17 for SQL Server};Server=(localdb)\\MSSQLLocalDB;"
           "Database=DM_Financial_Kimball_v2;Trusted_Connection=yes;")
ID_EJECUCION = "C" + datetime.now().strftime("%Y%m%d_%H%M%S")


def sin_tildes(texto):
    return unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")


def macro_region(region):
    return "Praga" if region == "Prague" else ("Bohemia" if "Bohemia" in region else "Moravia")


def asegurar_estructura(cur):
    """Crea Dim_Concepto_Movimiento y la clave en Fact_Transacciones si la base se creó con un DDL anterior."""
    cur.execute("""
    IF OBJECT_ID('Dim_Concepto_Movimiento') IS NULL
        CREATE TABLE Dim_Concepto_Movimiento (
            sk_concepto INT IDENTITY(1,1) PRIMARY KEY,
            codigo_concepto VARCHAR(30) NOT NULL, concepto_traducido VARCHAR(60) NOT NULL,
            metodo_concepto VARCHAR(30) NOT NULL, tipo_contraparte VARCHAR(40) NOT NULL,
            CONSTRAINT UQ_Dim_Concepto UNIQUE (codigo_concepto, metodo_concepto, tipo_contraparte));
    IF COL_LENGTH('Fact_Transacciones', 'sk_concepto') IS NULL
    BEGIN
        ALTER TABLE Fact_Transacciones ADD sk_concepto INT NULL;
        ALTER TABLE Fact_Transacciones ADD CONSTRAINT FK_FactTrans_Concepto
            FOREIGN KEY (sk_concepto) REFERENCES Dim_Concepto_Movimiento(sk_concepto);
    END""")


def cargar_distritos(cur):
    d = pd.read_csv(os.path.join(DF, "df_distritos_clean.csv"))
    cur.executemany("""UPDATE Dim_Distrito SET tasa_desempleo = ?, tasa_criminalidad = ?, es_imputado = ?,
                       metodo_imputacion = ?, fecha_enriquecimiento = SYSDATETIME() WHERE id_distrito_bk = ?""",
                    [(float(r.tasa_desempleo_1995), float(r.tasa_criminalidad_1995), int(r.es_imputado),
                      r.metodo_imputacion, int(r.id_distrito)) for r in d.itertuples()])
    print(f"  Dim_Distrito: {len(d)} distritos actualizados ({int(d.es_imputado.sum())} imputado)")


def cargar_clientes(cur):
    c = pd.read_csv(os.path.join(DF, "df_cliente_consolidado_clean.csv"))
    c["macro_region"] = c.region.map(macro_region)
    # Segmentación de los estereotipos del Informe 04 (sistemas de recomendación)
    c["segmento_edad"] = pd.cut(c.edad_corte, bins=[0, 30, 50, 120], right=False,
                                labels=["Joven (<30)", "Adulto (30-50)", "Adulto Mayor (>50)"]).astype(str)
    c["arquetipo_demografico"] = c.macro_region + " - " + c.segmento_edad
    cur.execute("""CREATE TABLE #cliente (id_cliente_bk INT PRIMARY KEY, macro_region VARCHAR(20), segmento_edad VARCHAR(30),
                   arquetipo_demografico VARCHAR(50), tiene_prestamo BIT, total_ordenes_activas INT,
                   saldo_promedio DECIMAL(12,2) NULL, calificacion_pago_desc VARCHAR(20))""")
    cur.executemany("INSERT INTO #cliente VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    [(int(r.id_cliente), r.macro_region, r.segmento_edad, r.arquetipo_demografico, int(r.tiene_prestamo),
                      int(r.total_ordenes_activas), None if pd.isna(r.saldo_promedio) else round(float(r.saldo_promedio), 2),
                      r.calificacion_pago) for r in c.itertuples()])
    cur.execute("""UPDATE d SET d.macro_region = s.macro_region, d.segmento_edad = s.segmento_edad,
                       d.arquetipo_demografico = s.arquetipo_demografico, d.tiene_prestamo = s.tiene_prestamo,
                       d.total_ordenes_activas = s.total_ordenes_activas, d.saldo_promedio = s.saldo_promedio,
                       d.calificacion_pago_desc = s.calificacion_pago_desc, d.fecha_enriquecimiento = SYSDATETIME()
                   FROM Dim_Cliente d JOIN #cliente s ON s.id_cliente_bk = d.id_cliente_bk""")
    print(f"  Dim_Cliente: {cur.rowcount:,} clientes enriquecidos")
    cur.execute("DROP TABLE #cliente")
    return c


def cargar_conceptos(cur):
    t = pd.read_csv(os.path.join(DF, "df_transacciones_completado.csv.gz"),
                    usecols=["id_transaccion", "k_symbol", "concepto_movimiento_traducido", "metodo_concepto", "tipo_contraparte"])
    combos = (t[["k_symbol", "concepto_movimiento_traducido", "metodo_concepto", "tipo_contraparte"]]
              .drop_duplicates().sort_values(["k_symbol", "metodo_concepto", "tipo_contraparte"]))
    cur.execute("UPDATE Fact_Transacciones SET sk_concepto = NULL")
    cur.execute("DELETE FROM Dim_Concepto_Movimiento")
    # Reiniciar el contador solo si la tabla ya tuvo filas (si no, la primera clave sería 0)
    cur.execute("IF IDENT_CURRENT('Dim_Concepto_Movimiento') IS NOT NULL AND EXISTS (SELECT 1 FROM sys.identity_columns "
                "WHERE object_id = OBJECT_ID('Dim_Concepto_Movimiento') AND last_value IS NOT NULL) "
                "DBCC CHECKIDENT ('Dim_Concepto_Movimiento', RESEED, 0)")
    cur.executemany("INSERT INTO Dim_Concepto_Movimiento (codigo_concepto, concepto_traducido, metodo_concepto, tipo_contraparte) "
                    "VALUES (?, ?, ?, ?)", [(k, sin_tildes(c), m, tc) for k, c, m, tc in combos.itertuples(index=False)])
    sk = {(r[0], r[1], r[2]): r[3] for r in
          cur.execute("SELECT codigo_concepto, metodo_concepto, tipo_contraparte, sk_concepto FROM Dim_Concepto_Movimiento")}
    print(f"  Dim_Concepto_Movimiento: {len(sk)} filas")
    t["sk"] = [sk[k] for k in zip(t.k_symbol, t.metodo_concepto, t.tipo_contraparte)]
    cur.execute("CREATE TABLE #concepto (id_transaccion_bk INT PRIMARY KEY, sk_concepto INT NOT NULL)")
    filas = list(zip(t.id_transaccion.astype(int).tolist(), t.sk.astype(int).tolist()))
    for i in range(0, len(filas), 100_000):
        cur.executemany("INSERT INTO #concepto VALUES (?, ?)", filas[i:i + 100_000])
    cur.execute("""UPDATE f SET f.sk_concepto = c.sk_concepto
                   FROM Fact_Transacciones f JOIN #concepto c ON c.id_transaccion_bk = f.id_transaccion_bk""")
    print(f"  Fact_Transacciones: {cur.rowcount:,} filas con sk_concepto")
    cur.execute("DROP TABLE #concepto")
    return t


def validar(cur, clientes, trans):
    pruebas = []
    uno = lambda s: cur.execute(s).fetchone()[0]

    def registrar(prueba, esperado, obtenido):
        estado = "OK" if str(esperado) == str(obtenido) else "FALLA"
        pruebas.append({"prueba": prueba, "esperado": str(esperado), "obtenido": str(obtenido), "resultado": estado})
        print(f"  [{estado:<5}] {prueba}: esperado {esperado} | obtenido {obtenido}")

    d69 = cur.execute("SELECT tasa_desempleo, tasa_criminalidad, es_imputado FROM Dim_Distrito WHERE id_distrito_bk = 69").fetchone()
    registrar("Distrito 69 imputado (desempleo, criminalidad, marca)", (5.83, 1326.0, True), (float(d69[0]), float(d69[1]), bool(d69[2])))
    registrar("Distritos sin nulos en desempleo/criminalidad 1995", 0,
              uno("SELECT COUNT(*) FROM Dim_Distrito WHERE tasa_desempleo IS NULL OR tasa_criminalidad IS NULL"))
    registrar("Clientes con macro-región, segmento y arquetipo", 5369,
              uno("SELECT COUNT(*) FROM Dim_Cliente WHERE macro_region IS NOT NULL AND segmento_edad IS NOT NULL AND arquetipo_demografico IS NOT NULL"))
    registrar("Clientes titulares de préstamo", 682, uno("SELECT SUM(CAST(tiene_prestamo AS INT)) FROM Dim_Cliente"))
    registrar("Órdenes asignadas a clientes", 6471, uno("SELECT SUM(total_ordenes_activas) FROM Dim_Cliente"))
    registrar("Saldo promedio nulo solo en cotitulares", 869,
              uno("SELECT COUNT(*) FROM Dim_Cliente WHERE saldo_promedio IS NULL AND tipo_disposicion = 'DISPONENT'"))
    registrar("Calificación de pago (buen / mal / sin evaluar)",
              clientes.calificacion_pago.value_counts().sort_index().to_dict(),
              {r[0]: r[1] for r in cur.execute("SELECT calificacion_pago_desc, COUNT(*) FROM Dim_Cliente GROUP BY calificacion_pago_desc ORDER BY 1")})
    registrar("Transacciones sin concepto asignado", 0, uno("SELECT COUNT(*) FROM Fact_Transacciones WHERE sk_concepto IS NULL"))
    registrar("Transacciones por código de concepto",
              trans.k_symbol.value_counts().sort_index().to_dict(),
              {r[0]: r[1] for r in cur.execute("SELECT c.codigo_concepto, COUNT(*) FROM Fact_Transacciones f JOIN Dim_Concepto_Movimiento c "
                                               "ON c.sk_concepto = f.sk_concepto GROUP BY c.codigo_concepto ORDER BY 1")})
    registrar("Transacciones con concepto inferido", int((trans.metodo_concepto != "Fuente").sum()),
              uno("SELECT COUNT(*) FROM Fact_Transacciones f JOIN Dim_Concepto_Movimiento c ON c.sk_concepto = f.sk_concepto "
                  "WHERE c.metodo_concepto <> 'Fuente'"))
    registrar("Monto de transacciones sin cambios", "6,257,862,197.00", f"{uno('SELECT SUM(monto_transaccion) FROM Fact_Transacciones'):,.2f}")
    registrar("Saldo neto al corte sin cambios", "197,140,434.00",
              f"{uno('SELECT SUM(s.saldo_fin_mes) FROM Fact_Saldo_Cuenta_Mensual s JOIN Dim_Tiempo t ON t.sk_tiempo = s.sk_mes WHERE t.anio = 1998 AND t.mes = 12'):,.2f}")
    return pruebas


def main():
    t0 = time.time()
    print("=" * 78 + f"\nCARGA DE LA COMPLETITUD EN KIMBALL · ejecución {ID_EJECUCION}\n" + "=" * 78)
    resumen33 = json.load(open(os.path.join(BASE_DIR, "metricas_completitud_datos.json"), encoding="utf-8"))
    if resumen33.get("resultado") != "OK":
        sys.exit("El script 33 no terminó con todas sus verificaciones en OK: no se carga.")
    cn = pyodbc.connect(KIMBALL, timeout=300)
    cur = cn.cursor()
    cur.fast_executemany = True
    asegurar_estructura(cur)
    cn.commit()
    cargar_distritos(cur)
    clientes = cargar_clientes(cur)
    trans = cargar_conceptos(cur)
    cn.commit()
    print("\nValidación")
    pruebas = validar(cur, clientes, trans)
    cur.executemany("INSERT INTO Auditoria_Carga (id_ejecucion, prueba, valor_esperado, valor_obtenido, resultado) VALUES (?, ?, ?, ?, ?)",
                    [(ID_EJECUCION, p["prueba"][:120], p["esperado"][:200], p["obtenido"][:200], p["resultado"]) for p in pruebas])
    cn.commit()
    conceptos = [dict(zip(["sk", "codigo", "concepto", "metodo", "contraparte", "transacciones"], r)) for r in cur.execute(
        "SELECT c.sk_concepto, c.codigo_concepto, c.concepto_traducido, c.metodo_concepto, c.tipo_contraparte, COUNT(*) "
        "FROM Dim_Concepto_Movimiento c JOIN Fact_Transacciones f ON f.sk_concepto = c.sk_concepto "
        "GROUP BY c.sk_concepto, c.codigo_concepto, c.concepto_traducido, c.metodo_concepto, c.tipo_contraparte ORDER BY c.sk_concepto")]
    cn.close()
    ok = sum(p["resultado"] == "OK" for p in pruebas)
    with open(SALIDA_JSON, "w", encoding="utf-8") as f:
        json.dump({"id_ejecucion": ID_EJECUCION, "duracion_segundos": round(time.time() - t0, 1),
                   "pruebas_ok": ok, "pruebas_total": len(pruebas), "pruebas": pruebas,
                   "dim_concepto_movimiento": conceptos}, f, ensure_ascii=False, indent=2, default=str)
    print(f"\n{ok}/{len(pruebas)} pruebas OK en {time.time() - t0:.1f} s. Resumen: {SALIDA_JSON}")


if __name__ == "__main__":
    main()
