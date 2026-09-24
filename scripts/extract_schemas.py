import pyodbc
import pymongo
import json
from bson import json_util

print("="*80)
print("1. MODELO DIMENSIONAL RALPH KIMBALL (SQL SERVER: DM_Financial_Kimball_v2)")
print("="*80)
cnxn = pyodbc.connect('Driver={ODBC Driver 17 for SQL Server};Server=(localdb)\\MSSQLLocalDB;Database=DM_Financial_Kimball_v2;Trusted_Connection=yes;')
cur = cnxn.cursor()
cur.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE='BASE TABLE' AND TABLE_NAME != 'sysdiagrams' ORDER BY TABLE_NAME")
tables = [r[0] for r in cur.fetchall()]

for t in tables:
    cur.execute(f"SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, CHARACTER_MAXIMUM_LENGTH FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='{t}' ORDER BY ORDINAL_POSITION")
    cols = []
    for r in cur.fetchall():
        dtype = f"{r[1]}({r[3]})" if r[3] else r[1]
        nullable = "NULL" if r[2] == "YES" else "NOT NULL"
        cols.append(f"  - {r[0]}: {dtype} {nullable}")
    cur.execute(f"SELECT COUNT(*) FROM {t}")
    cnt = cur.fetchone()[0]
    print(f"\n[TABLA] {t} ({cnt:,} registros)")
    print("\n".join(cols))

print("\n" + "="*80)
print("2. MODELO DOCUMENTAL NoSQL (MONGODB: Base de datos 'Financial')")
print("="*80)
client = pymongo.MongoClient('mongodb://localhost:27017/')
db = client['Financial']
for c in sorted(db.list_collection_names()):
    cnt = db[c].count_documents({})
    doc = db[c].find_one()
    indexes = list(db[c].list_indexes())
    idx_str = [f"{i['name']} -> {dict(i['key'])}" for i in indexes]
    print(f"\n[COLECCIÓN] {c} ({cnt:,} documentos)")
    print(f"  Índices: {idx_str}")
    print("  Estructura JSON (Documento Tipo):")
    sample_json = json.dumps(json.loads(json_util.dumps(doc)), indent=4)
    print("  " + "\n  ".join(sample_json.split("\n")[:35]))
