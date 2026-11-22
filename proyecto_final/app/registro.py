"""
Registro de cada predicción hecha en el aplicativo.

Se guarda siempre en SQLite (archivo local, para que el aplicativo funcione en
cualquier equipo) y, si está disponible, también en el Data Mart Kimball de
SQL Server, en la tabla dbo.Prediccion_Red_Neuronal (write-back), para que
Power BI pueda mostrar el historial junto al resto del modelo dimensional.
"""

import json
import os
import sqlite3
from datetime import datetime
from pathlib import Path

ARCHIVO_SQLITE = Path(__file__).resolve().parent / "predicciones.sqlite"
SERVIDOR_SQL = os.environ.get("BI_SQL_SERVIDOR", r"(localdb)\MSSQLLocalDB")
BASE_SQL = os.environ.get("BI_SQL_BASE", "DM_Financial_Kimball_v2")

COLUMNAS = "fecha_hora, sistema, titulo, entradas, vector_x, dimension_x, clase_predicha, probabilidad, probabilidades"

DDL_SQLITE = """
CREATE TABLE IF NOT EXISTS prediccion (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha_hora TEXT NOT NULL,
    sistema TEXT NOT NULL,
    titulo TEXT NOT NULL,
    entradas TEXT NOT NULL,
    vector_x TEXT NOT NULL,
    dimension_x INTEGER NOT NULL,
    clase_predicha TEXT NOT NULL,
    probabilidad REAL NOT NULL,
    probabilidades TEXT NOT NULL
)"""

DDL_SQLSERVER = """
IF OBJECT_ID('dbo.Prediccion_Red_Neuronal') IS NULL
CREATE TABLE dbo.Prediccion_Red_Neuronal (
    id INT IDENTITY(1,1) PRIMARY KEY,
    fecha_hora DATETIME2 NOT NULL,
    sistema VARCHAR(4) NOT NULL,
    titulo NVARCHAR(100) NOT NULL,
    entradas NVARCHAR(MAX) NOT NULL,
    vector_x NVARCHAR(MAX) NOT NULL,
    dimension_x INT NOT NULL,
    clase_predicha NVARCHAR(100) NOT NULL,
    probabilidad FLOAT NOT NULL,
    probabilidades NVARCHAR(MAX) NOT NULL
)"""


def _fila(sistema, titulo, entradas, resultado):
    return (
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        sistema,
        titulo,
        json.dumps(entradas, ensure_ascii=False),
        json.dumps(resultado["x"]),
        resultado["dimension_x"],
        resultado["clase"],
        resultado["probabilidades"][resultado["clase"]],
        json.dumps(resultado["probabilidades"], ensure_ascii=False),
    )


def guardar(sistema, titulo, entradas, resultado):
    """Guarda la predicción. Devuelve la lista de destinos donde quedó registrada."""
    fila = _fila(sistema, titulo, entradas, resultado)
    destinos = []
    with sqlite3.connect(ARCHIVO_SQLITE) as cn:
        cn.execute(DDL_SQLITE)
        cn.execute(f"INSERT INTO prediccion ({COLUMNAS}) VALUES (?,?,?,?,?,?,?,?,?)", fila)
    destinos.append("SQLite local")
    try:
        import pyodbc

        cn = pyodbc.connect(
            f"Driver={{ODBC Driver 17 for SQL Server}};Server={SERVIDOR_SQL};Database={BASE_SQL};"
            "Trusted_Connection=yes;TrustServerCertificate=yes;",
            timeout=5,
            autocommit=True,
        )
        cn.execute(DDL_SQLSERVER)
        cn.execute(f"INSERT INTO dbo.Prediccion_Red_Neuronal ({COLUMNAS}) VALUES (?,?,?,?,?,?,?,?,?)", fila)
        cn.close()
        destinos.append(f"SQL Server ({BASE_SQL}.dbo.Prediccion_Red_Neuronal)")
    except Exception:
        pass
    return destinos


def historial(limite=50, sistema=None):
    if not ARCHIVO_SQLITE.exists():
        return []
    with sqlite3.connect(ARCHIVO_SQLITE) as cn:
        cn.row_factory = sqlite3.Row
        sql = "SELECT * FROM prediccion"
        args = []
        if sistema:
            sql += " WHERE sistema = ?"
            args.append(sistema)
        sql += " ORDER BY id DESC LIMIT ?"
        args.append(limite)
        filas = [dict(r) for r in cn.execute(sql, args)]
    for f in filas:
        f["entradas"] = json.loads(f["entradas"])
        f["probabilidades"] = json.loads(f["probabilidades"])
        f["x"] = json.loads(f["vector_x"])
        dos = sorted(f["probabilidades"].values(), reverse=True)[:2]
        f["margen"] = dos[0] - dos[1] if len(dos) == 2 else 1.0
        f["en_frontera"] = f["margen"] < 0.10
    return filas
