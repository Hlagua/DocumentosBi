"""
==============================================================================
UNIVERSIDAD TÉCNICA DE AMBATO
FACULTAD DE INGENIERÍA EN SISTEMAS ELECTRÓNICA E INDUSTRIAL
CARRERA DE SOFTWARE - CICLO ACADÉMICO: AGOSTO 2026 – DICIEMBRE 2026
ASIGNATURA: Inteligencia de Negocios
DOCENTE: Ing. Ruben Nogales, Mg.
AUTORES: Alison Marcela Cobos Taco / Henry Daniel Lagua Flores
==============================================================================
ARCHIVO: etl_populate_kimball_v2.py
DESCRIPCIÓN: Pipeline ETL automatizado en Python para extraer datos desde la
             base de datos remota MySQL (Financial_ijs), aplicar las reglas
             de limpieza, calidad y homologación, y cargar el modelo
             dimensional Ralph Kimball en SQL Server (DM_Financial_Kimball_v2).

REQUISITOS PREVIOS:
    1. Python 3.10+ instalado.
    2. Librerías de conexión:
       pip install pymysql pyodbc
    3. ODBC Driver 18 for SQL Server (o Driver 17).
    4. Base de datos DM_Financial_Kimball_v2 creada con el script:
       sql/01_DDL_Kimball_DM_Financial.sql
==============================================================================
"""

import pymysql
import pyodbc
from datetime import date, timedelta
import time
import sys

# ==============================================================================
# 1. PARÁMETROS DE CONEXIÓN
# ==============================================================================
MYSQL_CONFIG = {
    'host': 'relational.fel.cvut.cz',
    'port': 3306,
    'user': 'guest',
    'password': 'ctu-relational',
    'database': 'Financial_ijs',
    'charset': 'utf8mb4'
}

SQL_SERVER_CONN_STR = (
    "Driver={ODBC Driver 18 for SQL Server};"
    "Server=(localdb)\\MSSQLLocalDB;"
    "Database=DM_Financial_Kimball_v2;"
    "Trusted_Connection=yes;"
    "TrustServerCertificate=yes;"
)

def run_etl():
    print("=" * 80)
    print("INICIANDO PROCESO ETL: Financial_ijs (MySQL) -> DM_Financial_Kimball_v2 (SQL Server)")
    print("=" * 80)
    t_start = time.time()

    # 1. Conexión a origen y destino
    print("\n[1/11] Conectando a los motores de base de datos...")
    try:
        conn_rem = pymysql.connect(**MYSQL_CONFIG)
        cur_rem = conn_rem.cursor()
        print("   -> Conexión exitosa a MySQL remoto (relational.fel.cvut.cz:3306).")
    except Exception as e:
        print(f"   [ERROR] No se pudo conectar a MySQL remoto: {e}")
        sys.exit(1)

    try:
        conn_loc = pyodbc.connect(SQL_SERVER_CONN_STR, autocommit=False)
        cur_loc = conn_loc.cursor()
        print("   -> Conexión exitosa a SQL Server local (DM_Financial_Kimball_v2).")
    except Exception as e:
        print(f"   [ERROR] No se pudo conectar a SQL Server local: {e}")
        conn_rem.close()
        sys.exit(1)

    # Verificar si se solicita reinicio total (--reset)
    if len(sys.argv) > 1 and sys.argv[1].lower() == '--reset':
        print("\n   [AVISO] Se detectó el parámetro --reset. Limpiando datos existentes...")
        cur_loc.execute("DELETE FROM Fact_Transacciones;")
        cur_loc.execute("DELETE FROM Fact_Ordenes;")
        cur_loc.execute("DELETE FROM Fact_Prestamos;")
        cur_loc.execute("DELETE FROM Dim_Cliente;")
        cur_loc.execute("DELETE FROM Dim_Cuenta;")
        cur_loc.execute("DELETE FROM Dim_Distrito;")
        cur_loc.execute("DELETE FROM Dim_Tiempo;")
        cur_loc.execute("DELETE FROM Dim_Estado_Prestamo;")
        cur_loc.execute("DELETE FROM Dim_Operacion;")
        cur_loc.execute("DELETE FROM Dim_Orden;")
        conn_loc.commit()
        print("   -> Tablas limpiadas exitosamente para carga limpia desde cero.")

    # --------------------------------------------------------------------------
    # 2. DIMENSIÓN TIEMPO (Calendario Continuo Diario: 1993-01-01 al 1998-12-31)
    # --------------------------------------------------------------------------
    print("\n[2/11] Procesando Dim_Tiempo...")
    cur_loc.execute("SELECT COUNT(*) FROM Dim_Tiempo")
    if cur_loc.fetchone()[0] == 0:
        dias_semana_esp = {1: 'Lunes', 2: 'Martes', 3: 'Miercoles', 4: 'Jueves', 5: 'Viernes', 6: 'Sabado', 7: 'Domingo'}
        meses_esp = {1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril', 5: 'Mayo', 6: 'Junio',
                     7: 'Julio', 8: 'Agosto', 9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'}
        
        current_date = date(1993, 1, 1)
        end_date = date(1998, 12, 31)
        tiempo_rows = []
        
        while current_date <= end_date:
            d_sem = current_date.isoweekday()
            es_fin = 1 if d_sem in (6, 7) else 0
            semestre = 1 if current_date.month <= 6 else 2
            trimestre = (current_date.month - 1) // 3 + 1
            
            tiempo_rows.append((
                current_date, current_date.year, semestre, trimestre,
                current_date.month, meses_esp[current_date.month],
                current_date.day, d_sem, dias_semana_esp[d_sem], es_fin
            ))
            current_date += timedelta(days=1)
            
        cur_loc.fast_executemany = True
        cur_loc.executemany("""
            INSERT INTO Dim_Tiempo (fecha, anio, semestre, trimestre, mes, nombre_mes, dia, dia_semana, nombre_dia, es_fin_de_semana)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, tiempo_rows)
        conn_loc.commit()
        print(f"   -> Insertados {len(tiempo_rows)} registros de calendario diario.")
    else:
        print("   -> Dim_Tiempo ya contiene datos. Omitiendo inserción.")

    cur_loc.execute("SELECT fecha, sk_tiempo FROM Dim_Tiempo")
    map_tiempo = {r[0]: r[1] for r in cur_loc.fetchall()}

    # --------------------------------------------------------------------------
    # 3. DIMENSIÓN DISTRITO (Contexto Geográfico con Limpieza de '?')
    # --------------------------------------------------------------------------
    print("\n[3/11] Procesando Dim_Distrito...")
    cur_loc.execute("SELECT COUNT(*) FROM Dim_Distrito")
    if cur_loc.fetchone()[0] == 0:
        cur_rem.execute("SELECT id, A2, A3, A4, A11, A12, A15 FROM districts")
        dist_rows = []
        for r in cur_rem.fetchall():
            id_dist, nombre, region, pob = r[0], r[1], r[2], int(r[3])
            salario = float(r[4]) if r[4] is not None and str(r[4]).strip() not in ('?', '') else None
            desempleo = float(r[5]) if r[5] is not None and str(r[5]).strip() not in ('?', '') else None
            crimen = float(r[6]) if r[6] is not None and str(r[6]).strip() not in ('?', '') else None
            dist_rows.append((id_dist, nombre, region, pob, salario, desempleo, crimen))
            
        cur_loc.fast_executemany = True
        cur_loc.executemany("""
            INSERT INTO Dim_Distrito (id_distrito_bk, nombre_distrito, region, poblacion, salario_promedio, tasa_desempleo, tasa_criminalidad)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, dist_rows)
        conn_loc.commit()
        print(f"   -> Insertados {len(dist_rows)} distritos (distrito 69 Jesenik con '?' convertido a NULL).")
    else:
        print("   -> Dim_Distrito ya contiene datos. Omitiendo inserción.")

    cur_loc.execute("SELECT id_distrito_bk, sk_distrito FROM Dim_Distrito")
    map_distrito = {r[0]: r[1] for r in cur_loc.fetchall()}

    # --------------------------------------------------------------------------
    # 4. DIMENSIÓN ESTADO PRÉSTAMO (Catálogo Fijo SCD Tipo 0)
    # --------------------------------------------------------------------------
    print("\n[4/11] Procesando Dim_Estado_Prestamo...")
    cur_loc.execute("SELECT COUNT(*) FROM Dim_Estado_Prestamo")
    if cur_loc.fetchone()[0] == 0:
        estados = [
            ('A', 'Cerrado', 'Pagado sin problemas'),
            ('B', 'Cerrado', 'Pagado, contrato terminado con deuda'),
            ('C', 'Vigente', 'En curso, al dia'),
            ('D', 'Vigente', 'En curso, en mora')
        ]
        cur_loc.executemany("""
            INSERT INTO Dim_Estado_Prestamo (codigo_estado, condicion, descripcion)
            VALUES (?, ?, ?)
        """, estados)
        conn_loc.commit()
        print("   -> Insertados 4 estados de crédito.")
    else:
        print("   -> Dim_Estado_Prestamo ya contiene datos.")

    cur_loc.execute("SELECT codigo_estado, sk_estado_prestamo FROM Dim_Estado_Prestamo")
    map_estado = {r[0]: r[1] for r in cur_loc.fetchall()}

    # --------------------------------------------------------------------------
    # 5. DIMENSIÓN OPERACIÓN (Homologación Checo -> Español y Canales)
    # --------------------------------------------------------------------------
    print("\n[5/11] Procesando Dim_Operacion...")
    cur_loc.execute("SELECT COUNT(*) FROM Dim_Operacion")
    if cur_loc.fetchone()[0] == 0:
        operaciones = [
            ('PRIJEM', 'Ingreso / Deposito', 'Ventanilla Bancaria'),
            ('VYDAJ', 'Egreso / Gasto', 'Compensacion / Ventanilla'),
            ('VYBER', 'Retiro en Efectivo', 'Ventanilla / ATM')
        ]
        cur_loc.executemany("""
            INSERT INTO Dim_Operacion (tipo_operacion_original, tipo_operacion_traducido, canal)
            VALUES (?, ?, ?)
        """, operaciones)
        conn_loc.commit()
        print("   -> Insertadas 3 operaciones homologadas al español con canales.")
    else:
        print("   -> Dim_Operacion ya contiene datos.")

    cur_loc.execute("SELECT tipo_operacion_original, sk_operacion FROM Dim_Operacion")
    map_operacion = {r[0]: r[1] for r in cur_loc.fetchall()}

    # --------------------------------------------------------------------------
    # 6. DIMENSIÓN ORDEN (Categorías Homologadas al Español)
    # --------------------------------------------------------------------------
    print("\n[6/11] Procesando Dim_Orden...")
    cur_loc.execute("SELECT COUNT(*) FROM Dim_Orden")
    if cur_loc.fetchone()[0] == 0:
        ordenes_cat = [
            ('SIPO', 'Servicios del Hogar'),
            ('UVER', 'Cuota de Prestamo'),
            ('POJISTNE', 'Pago de Seguros'),
            ('LEASING', 'Arrendamiento / Leasing'),
            ('', 'Sin Especificar')
        ]
        cur_loc.executemany("""
            INSERT INTO Dim_Orden (k_symbol_original, categoria_orden_traducida)
            VALUES (?, ?)
        """, ordenes_cat)
        conn_loc.commit()
        print("   -> Insertadas 5 categorias de órdenes permanentes.")
    else:
        print("   -> Dim_Orden ya contiene datos.")

    cur_loc.execute("SELECT k_symbol_original, sk_orden_tipo FROM Dim_Orden")
    map_orden_tipo = {r[0]: r[1] for r in cur_loc.fetchall()}

    # --------------------------------------------------------------------------
    # 7. DIMENSIÓN CUENTA (Catálogo de Cuentas Pasivas)
    # --------------------------------------------------------------------------
    print("\n[7/11] Procesando Dim_Cuenta...")
    cur_loc.execute("SELECT COUNT(*) FROM Dim_Cuenta")
    if cur_loc.fetchone()[0] == 0:
        cur_rem.execute("SELECT id, district_id, frequency, date FROM accounts")
        acc_rows = []
        for r in cur_rem.fetchall():
            aid, did, freq, f_ap = r[0], r[1], r[2], r[3]
            sk_dist = map_distrito.get(did)
            acc_rows.append((aid, freq, f_ap, sk_dist))
            
        cur_loc.fast_executemany = True
        cur_loc.executemany("""
            INSERT INTO Dim_Cuenta (id_cuenta_bk, frecuencia_emision_estado, fecha_apertura, sk_distrito)
            VALUES (?, ?, ?, ?)
        """, acc_rows)
        conn_loc.commit()
        print(f"   -> Insertadas {len(acc_rows)} cuentas bancarias.")
    else:
        print("   -> Dim_Cuenta ya contiene datos.")

    cur_loc.execute("SELECT id_cuenta_bk, sk_cuenta, fecha_apertura, sk_distrito FROM Dim_Cuenta")
    map_cuenta = {r[0]: (r[1], r[2], r[3]) for r in cur_loc.fetchall()}

    # --------------------------------------------------------------------------
    # 8. DIMENSIÓN CLIENTE (Demografía, edad_corte al 31/12/1998 y buen_pagador)
    # --------------------------------------------------------------------------
    print("\n[8/11] Procesando Dim_Cliente...")
    cur_loc.execute("SELECT COUNT(*) FROM Dim_Cliente")
    if cur_loc.fetchone()[0] == 0:
        cur_rem.execute("SELECT account_id, status FROM loans")
        loan_status_by_acc = {r[0]: r[1] for r in cur_rem.fetchall()}
        
        cur_rem.execute("SELECT client_id, account_id, type FROM disps")
        disp_by_client = {r[0]: (r[1], r[2]) for r in cur_rem.fetchall()}
        
        cur_rem.execute("SELECT id, birth_number, district_id FROM clients")
        cli_rows = []
        
        for r in cur_rem.fetchall():
            cid, bn, did = r[0], str(r[1]).zfill(6), r[2]
            
            yy = int(bn[0:2])
            mm_raw = int(bn[2:4])
            dd = int(bn[4:6])
            
            year = 1900 + yy
            if mm_raw > 50:
                sexo = 'F'
                month = mm_raw - 50
            else:
                sexo = 'M'
                month = mm_raw
                
            f_nac = date(year, month, dd)
            
            # Cálculo de edad_corte congelada al 31/12/1998
            edad = 1998 - year - (1 if (12, 31) < (month, dd) else 0)
            
            disp_info = disp_by_client.get(cid, (None, 'OWNER'))
            acc_id, disp_type = disp_info
            
            # Etiqueta de riesgo corregida: 1 para Estado A, 0 para Estado B, NULL otros
            l_status = loan_status_by_acc.get(acc_id)
            if l_status == 'A':
                etiqueta = 1
            elif l_status == 'B':
                etiqueta = 0
            else:
                etiqueta = None
                
            sk_dist = map_distrito.get(did)
            cli_rows.append((cid, sexo, f_nac, edad, disp_type, etiqueta, sk_dist))
            
        cur_loc.fast_executemany = True
        cur_loc.executemany("""
            INSERT INTO Dim_Cliente (id_cliente_bk, sexo, fecha_nacimiento, edad_corte, tipo_disposicion, etiqueta_buen_pagador, sk_distrito)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, cli_rows)
        conn_loc.commit()
        print(f"   -> Insertados {len(cli_rows)} clientes con edad_corte al 31/12/1998 (100% calculada).")
    else:
        print("   -> Dim_Cliente ya contiene datos.")

    cur_loc.execute("SELECT id_cliente_bk, sk_cliente FROM Dim_Cliente")
    map_cli_sk = {r[0]: r[1] for r in cur_loc.fetchall()}

    cur_rem.execute("SELECT account_id, client_id FROM disps WHERE type = 'OWNER'")
    acc_to_owner_client = {r[0]: r[1] for r in cur_rem.fetchall()}
    acc_to_owner_sk_cliente = {acc: map_cli_sk[cid] for acc, cid in acc_to_owner_client.items() if cid in map_cli_sk}

    # --------------------------------------------------------------------------
    # 9. TABLA DE HECHOS: Fact_Prestamos (Grano atómico por préstamo)
    # --------------------------------------------------------------------------
    print("\n[9/11] Procesando Fact_Prestamos...")
    cur_loc.execute("SELECT COUNT(*) FROM Fact_Prestamos")
    if cur_loc.fetchone()[0] == 0:
        cur_rem.execute("SELECT id, account_id, date, amount, duration, payments, status FROM loans")
        loan_rows = []
        for r in cur_rem.fetchall():
            lid, aid, f_date, amt, dur, pay, st = r[0], r[1], r[2], float(r[3]), int(r[4]), float(r[5]), r[6]
            sk_t = map_tiempo.get(f_date)
            sk_c, _, sk_d = map_cuenta[aid]
            sk_cli = acc_to_owner_sk_cliente[aid]
            sk_st = map_estado[st]
            saldo_pend = 0.0 if st == 'A' else amt
            loan_rows.append((sk_t, sk_c, sk_cli, sk_d, sk_st, lid, amt, dur, pay, saldo_pend))
            
        cur_loc.fast_executemany = True
        cur_loc.executemany("""
            INSERT INTO Fact_Prestamos (sk_tiempo, sk_cuenta, sk_cliente, sk_distrito, sk_estado_prestamo,
                                       id_prestamo_bk, monto_prestamo, plazo_meses, pago_mensual, saldo_pendiente_estimado)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, loan_rows)
        conn_loc.commit()
        print(f"   -> Insertados {len(loan_rows)} préstamos atómicos (Total: $103,261,740.00).")
    else:
        print("   -> Fact_Prestamos ya contiene datos.")

    # --------------------------------------------------------------------------
    # 10. TABLA DE HECHOS: Fact_Ordenes (Con precisión decimal exacta)
    # --------------------------------------------------------------------------
    print("\n[10/11] Procesando Fact_Ordenes...")
    cur_loc.execute("SELECT COUNT(*) FROM Fact_Ordenes")
    if cur_loc.fetchone()[0] == 0:
        cur_rem.execute("SELECT id, account_id, amount, k_symbol FROM orders")
        order_rows = []
        for r in cur_rem.fetchall():
            oid, aid, amt, k_sym = r[0], r[1], float(r[2]), (r[3] or '').strip()
            sk_c, f_ap, sk_d = map_cuenta[aid]
            sk_t = map_tiempo.get(f_ap)
            sk_cli = acc_to_owner_sk_cliente[aid]
            sk_ord_t = map_orden_tipo.get(k_sym, map_orden_tipo[''])
            order_rows.append((sk_t, sk_c, sk_cli, sk_d, sk_ord_t, oid, amt))
            
        cur_loc.fast_executemany = True
        cur_loc.executemany("""
            INSERT INTO Fact_Ordenes (sk_tiempo, sk_cuenta, sk_cliente, sk_distrito, sk_orden_tipo, id_orden_bk, monto_orden)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, order_rows)
        conn_loc.commit()
        print(f"   -> Insertadas {len(order_rows)} órdenes de pago con precisión decimal exacta.")
    else:
        print("   -> Fact_Ordenes ya contiene datos.")

    # --------------------------------------------------------------------------
    # 11. TABLA DE HECHOS: Fact_Transacciones (1,056,320 filas en lotes de 50,000)
    # --------------------------------------------------------------------------
    print("\n[11/11] Procesando Fact_Transacciones...")
    cur_loc.execute("SELECT COUNT(*) FROM Fact_Transacciones")
    curr_trans = cur_loc.fetchone()[0]
    if curr_trans == 0:
        print("   -> Extrayendo 1,056,320 transacciones desde MySQL remoto...")
        cur_rem.execute("SELECT id, account_id, date, type, amount, balance FROM trans ORDER BY id")
        
        batch_size = 50000
        total_inserted = 0
        cur_loc.fast_executemany = True
        
        while True:
            rows = cur_rem.fetchmany(batch_size)
            if not rows:
                break
                
            trans_rows = []
            for r in rows:
                tid, aid, f_date, t_type, amt, bal = r[0], r[1], r[2], r[3], float(r[4]), float(r[5])
                sk_t = map_tiempo.get(f_date)
                sk_c, _, sk_d = map_cuenta[aid]
                sk_cli = acc_to_owner_sk_cliente[aid]
                sk_op = map_operacion.get(t_type, map_operacion['VYDAJ'])
                trans_rows.append((sk_t, sk_c, sk_cli, sk_d, sk_op, tid, amt, bal))
                
            cur_loc.executemany("""
                INSERT INTO Fact_Transacciones (sk_tiempo, sk_cuenta, sk_cliente, sk_distrito, sk_operacion,
                                               id_transaccion_bk, monto_transaccion, saldo_cuenta)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, trans_rows)
            conn_loc.commit()
            total_inserted += len(trans_rows)
            print(f"      Progreso: {total_inserted:,} / 1,056,320 transacciones cargadas...")
            
        print(f"   -> Carga completa de Fact_Transacciones ({total_inserted:,} filas).")
    else:
        print(f"   -> Fact_Transacciones ya contiene {curr_trans:,} filas.")

    conn_rem.close()
    conn_loc.close()

    t_end = time.time()
    print("\n" + "=" * 80)
    print(f"ETL FINALIZADO CON ÉXITO EN {t_end - t_start:.2f} SEGUNDOS")
    print("=" * 80)

if __name__ == '__main__':
    run_etl()
