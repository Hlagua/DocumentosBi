"""
Extrae la tabla `cards` de Financial_ijs y la deja en dataframes/ junto con
la disposición (titular o disponente) y la cuenta a la que pertenece.

La Carta de diseño dejó `cards` fuera del Data Mart (892 tarjetas). Para el
proyecto final se incorpora como un dataframe más, con el mismo estilo que
los otros: nombres en español y fechas en formato AAAA-MM-DD.

Salidas: dataframes/df_tarjetas.csv y dataframes/df_disposiciones.csv
  id_tarjeta, id_disposicion, id_cliente, id_cuenta, tipo_disposicion,
  tipo_tarjeta (junior / classic / gold), fecha_emision

Uso: python scripts/49_extraer_tarjetas.py
"""
import sys
from pathlib import Path

import warnings

import pandas as pd
import pymysql

sys.stdout.reconfigure(encoding="utf-8")
warnings.filterwarnings("ignore", message="pandas only supports SQLAlchemy")

RAIZ = Path(__file__).resolve().parent.parent
SALIDA = RAIZ / "dataframes" / "df_tarjetas.csv"
SALIDA_DISP = RAIZ / "dataframes" / "df_disposiciones.csv"
MYSQL = dict(host="relational.fel.cvut.cz", port=3306, user="guest",
             password="ctu-relational", database="Financial_ijs", charset="utf8mb4")


def main():
    cn = pymysql.connect(connect_timeout=30, **MYSQL)
    cards = pd.read_sql("SELECT * FROM cards", cn)
    disps = pd.read_sql("SELECT * FROM disps", cn)
    cn.close()
    print(f"cards {len(cards):,} filas · disps {len(disps):,} filas")

    pd.DataFrame({"id_disposicion": disps["id"], "id_cliente": disps["client_id"],
                  "id_cuenta": disps["account_id"], "tipo_disposicion": disps["type"]}
                 ).to_csv(SALIDA_DISP, index=False, encoding="utf-8")
    print(f"Guardado {SALIDA_DISP.relative_to(RAIZ)} ({len(disps):,} disposiciones)")

    df = cards.merge(disps, left_on="disp_id", right_on="id", suffixes=("", "_disp"), validate="one_to_one")
    df = pd.DataFrame({
        "id_tarjeta": df["id"],
        "id_disposicion": df["disp_id"],
        "id_cliente": df["client_id"],
        "id_cuenta": df["account_id"],
        "tipo_disposicion": df["type_disp"] if "type_disp" in df else df["type"],
        "tipo_tarjeta": df["type"],
        "fecha_emision": pd.to_datetime(df["issued"]).dt.strftime("%Y-%m-%d"),
    }).sort_values("id_tarjeta")
    df.to_csv(SALIDA, index=False, encoding="utf-8")
    print(f"Guardado {SALIDA.relative_to(RAIZ)} ({len(df):,} tarjetas)")
    print(df["tipo_tarjeta"].value_counts().to_string())
    print(df["tipo_disposicion"].value_counts().to_string())
    print("Cuentas con más de una tarjeta:", int((df.groupby("id_cuenta").size() > 1).sum()))
    print("Emisión:", df["fecha_emision"].min(), "→", df["fecha_emision"].max())


if __name__ == "__main__":
    main()
