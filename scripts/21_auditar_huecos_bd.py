"""
==============================================================================
Script 21: Auditoría exhaustiva de nulos, vacíos y huecos en DM_Financial_Kimball_v2
==============================================================================
"""
import pyodbc

conn_str = 'Driver={ODBC Driver 17 for SQL Server};Server=(localdb)\\MSSQLLocalDB;Database=DM_Financial_Kimball_v2;Trusted_Connection=yes;'
cnxn = pyodbc.connect(conn_str)
cur = cnxn.cursor()

cur.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE' AND TABLE_NAME != 'sysdiagrams'")
tables = [r[0] for r in cur.fetchall()]

print("=" * 80)
print("AUDITORÍA EXHAUSTIVA DE NULOS Y HUECOS EN LA BASE DE DATOS KIMBALL")
print("=" * 80)

for t in tables:
    cur.execute(f"SELECT COUNT(*) FROM {t}")
    total_rows = cur.fetchone()[0]
    print(f"\nTABLA: {t:<22} | Filas: {total_rows:>10,}")
    print("-" * 80)
    
    cur.execute(f"SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{t}'")
    cols = cur.fetchall()
    
    table_has_alerts = False
    for c_name, c_type in cols:
        cur.execute(f"SELECT COUNT(*) FROM {t} WHERE {c_name} IS NULL")
        null_count = cur.fetchone()[0]
        
        empty_count = 0
        qmark_count = 0
        if c_type in ['varchar', 'nvarchar', 'char', 'nchar', 'text']:
            cur.execute(f"SELECT COUNT(*) FROM {t} WHERE LTRIM(RTRIM({c_name})) = ''")
            empty_count = cur.fetchone()[0]
            cur.execute(f"SELECT COUNT(*) FROM {t} WHERE {c_name} = '?'")
            qmark_count = cur.fetchone()[0]
            
        if null_count > 0 or empty_count > 0 or qmark_count > 0:
            table_has_alerts = True
            pct = (null_count / total_rows) * 100 if total_rows > 0 else 0
            details = []
            if null_count > 0:
                details.append(f"{null_count:,} NULLs ({pct:.2f}%)")
            if empty_count > 0:
                details.append(f"{empty_count:,} Vacíos ('')")
            if qmark_count > 0:
                details.append(f"{qmark_count:,} Signos '?'")
            print(f"  [ALERTA]  {c_name:<28} ({c_type:<10}): {', '.join(details)}")
            
    if not table_has_alerts:
        print("  [PERFECTO] Cero nulos, cero vacíos y cero anomalías.")

cnxn.close()
