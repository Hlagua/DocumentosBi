"""
Registro local (SQLite) y opcional en SQL Server LocalDB para los 5 modelos
de la literatura PKDD'99 / Berka.
"""

import json
import os
import sqlite3
from datetime import datetime
from pathlib import Path

ARCHIVO_SQLITE = Path(__file__).resolve().parent / "predicciones_berka.sqlite"
SERVIDOR_SQL = os.environ.get("BI_SQL_SERVIDOR", r"(localdb)\MSSQLLocalDB")
BASE_SQL = os.environ.get("BI_SQL_BASE", "DM_Financial_Kimball_v2")

DDL_SQLITE = """
CREATE TABLE IF NOT EXISTS prediccion (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha_hora TEXT NOT NULL,
    codigo TEXT NOT NULL,
    titulo TEXT NOT NULL,
    tipo TEXT NOT NULL,
    entradas TEXT NOT NULL,
    vector_x TEXT NOT NULL,
    dimension_x INTEGER NOT NULL,
    resultado_texto TEXT NOT NULL,
    valor_numerico REAL NOT NULL,
    detalle TEXT NOT NULL
)"""


def guardar(codigo, titulo, entradas, resultado):
    if resultado["tipo"] == "regresion":
        texto = f"{resultado['valor']:,.2f} {resultado['unidad']}"
        valor = float(resultado["valor"])
        detalle = {"valor": valor, "unidad": resultado["unidad"]}
    else:
        texto = resultado["clase"]
        valor = float(resultado["probabilidades"][resultado["clase"]])
        detalle = resultado["probabilidades"]

    fila = (
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        codigo, titulo, resultado["tipo"],
        json.dumps(entradas, ensure_ascii=False),
        json.dumps(resultado["x"]),
        int(resultado["dimension_x"]),
        texto, valor, json.dumps(detalle, ensure_ascii=False),
    )
    with sqlite3.connect(ARCHIVO_SQLITE) as cn:
        cn.execute(DDL_SQLITE)
        cn.execute(
            "INSERT INTO prediccion (fecha_hora, codigo, titulo, tipo, entradas, vector_x, dimension_x, resultado_texto, valor_numerico, detalle) "
            "VALUES (?,?,?,?,?,?,?,?,?,?)",
            fila,
        )
    return ["SQLite local (predicciones_berka.sqlite)"]


def historial(limite=50, codigo=None):
    if not ARCHIVO_SQLITE.exists():
        return []
    with sqlite3.connect(ARCHIVO_SQLITE) as cn:
        cn.row_factory = sqlite3.Row
        sql = "SELECT * FROM prediccion"
        args = []
        if codigo:
            sql += " WHERE codigo = ?"
            args.append(codigo)
        sql += " ORDER BY id DESC LIMIT ?"
        args.append(limite)
        filas = [dict(r) for r in cn.execute(sql, args)]
    for f in filas:
        f["entradas"] = json.loads(f["entradas"])
        f["detalle"] = json.loads(f["detalle"])
        f["x"] = json.loads(f["vector_x"])
    return filas
