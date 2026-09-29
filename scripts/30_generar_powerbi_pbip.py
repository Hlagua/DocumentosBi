"""
==============================================================================
UNIVERSIDAD TÉCNICA DE AMBATO - Inteligencia de Negocios
AUTORES: Alison Marcela Cobos Taco / Henry Daniel Lagua Flores
==============================================================================
ARCHIVO: 30_generar_powerbi_pbip.py   (Guía 07 v4)
DESCRIPCIÓN: Genera los dos proyectos de Power BI Desktop (.pbip) de la Guía 07 v4:
               dashboards/Dashboard_Financial_Kimball/  (SQL Server)
               dashboards/Dashboard_Financial_Mongo/    (MongoDB vía el conector Python 26)
             y el archivo sql/05_Medidas_DAX_PowerBI.dax con las mismas medidas.
             Cada proyecto incluye:
               * Modelo semántico (model.bim): consultas M, relaciones (sección 6 de
                 la guía) y las medidas DAX (secciones 6.3 y 7), con los mismos
                 nombres en los dos modelos.
               * Informe (report.json): 9 páginas (Inicio, P1–P6, D1, D2), cabecera
                 de KPIs en todas, segmentadores sincronizados, navegación y la
                 paleta de Okabe e Ito (sección 4).
               * Tema (tema_financial.json) y README con los pasos manuales.
             Una sola lista de medidas alimenta los dos modelos y el .dax: no pueden
             quedar desalineados.
USO:         python scripts/30_generar_powerbi_pbip.py
==============================================================================
"""
import json
import os
import shutil
import uuid

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(BASE_DIR, "dashboards")
CONECTOR_MONGO = os.path.join(BASE_DIR, "scripts", "26_powerbi_mongo_dashboard.py")
ARCHIVO_DAX = os.path.join(BASE_DIR, "sql", "05_Medidas_DAX_PowerBI.dax")

W, H = 1280, 720

# ---- Paleta de la Guía 07 v4, sección 4.1 (Okabe e Ito) ----
EST_A, EST_C, EST_B, EST_D = "#0072B2", "#56B4E9", "#D55E00", "#E69F00"
ALERTA, GRIS, TINTA, BLANCO = "#D55E00", "#7F7F7F", "#333333", "#FFFFFF"
GRIS_BORDE, GRIS_FONDO = "#E0E0E0", "#F5F5F5"
BANDAS = {"Baja": "#FBE3D3", "Media-baja": "#F2B48C", "Media-alta": "#E5813F", "Alta": "#D55E00"}
ESTADOS = {"A · Cerrado al día": EST_A, "B · Cerrado con deuda": EST_B,
           "C · Vigente al día": EST_C, "D · Vigente en mora": EST_D}
ORDENES = {"Servicios del Hogar": "#009E73", "Cuota de Prestamo": "#CC79A7", "Pago de Seguros": "#F0E442",
           "Arrendamiento / Leasing": "#000000", "Sin Especificar": "#C8C8C8"}

# Interfaz (banda superior, fondo, tarjetas): azul marino institucional y grises neutros.
# No compite con los colores de los datos (Okabe e Ito), que siguen significando lo mismo.
NAVY, NAVY_2, AMBAR = "#0F2A4A", "#24466E", "#F2A900"
FONDO_PAG, PANEL, BORDE, TXT_SUAVE, TITULO = "#EEF1F5", "#E3E8F0", "#DDE3EB", "#5B6B7F", "#1F2D3D"

MONEDA = '"$"#,0'
MONEDA2 = '"$"#,0.00'
PORC = "0.00%"
ENTERO = "#,0"
INDICE = "0.00"


# ==========================================================================
# 1. MODELO SEMÁNTICO
# ==========================================================================
def col(nombre, tipo="string", fmt=None, oculto=False, orden_por=None):
    c = {"name": nombre, "dataType": tipo, "sourceColumn": nombre, "summarizeBy": "none"}
    if fmt:
        c["formatString"] = fmt
    if oculto:
        c["isHidden"] = True
    if orden_por:
        c["sortByColumn"] = orden_por
    return c


def col_calc(nombre, expresion, tipo="string", oculto=False, orden_por=None):
    c = {"type": "calculated", "name": nombre, "dataType": tipo, "expression": expresion, "summarizeBy": "none"}
    if oculto:
        c["isHidden"] = True
    if orden_por:
        c["sortByColumn"] = orden_por
    return c


M_TIPOS = {"string": "type text", "int64": "Int64.Type", "double": "type number", "dateTime": "type datetime",
           "boolean": "type logical"}


def _particion(nombre, lineas):
    return [{"name": nombre, "mode": "import", "source": {"type": "m", "expression": lineas}}]


def tabla_sql(nombre, columnas, calculadas=(), orden_m=None):
    """orden_m = (columna_nueva, columna_texto, {valor: posición}): columna de orden creada en Power Query.
    Debe ser una columna de origen: ordenar por una columna calculada DAX que depende de la misma
    columna produce una dependencia circular en el motor."""
    lista = ", ".join(f'"{c["name"]}"' for c in columnas)
    tipos = ", ".join(f'{{"{c["name"]}", {M_TIPOS[c["dataType"]]}}}' for c in columnas)
    pasos = ["let",
             "    Origen = Sql.Database(ServidorSQL, BaseDatosSQL),",
             f'    Tabla = Origen{{[Schema="dbo", Item="{nombre}"]}}[Data],',
             f"    Columnas = Table.SelectColumns(Tabla, {{{lista}}}),",
             f"    Tipos = Table.TransformColumnTypes(Columnas, {{{tipos}}})"]
    columnas = list(columnas)
    if orden_m:
        nueva, origen, mapa = orden_m
        regla = " else ".join(f'if Text.Contains([{origen}], "{v}") then {i}' for v, i in mapa.items()) + " else 0"
        pasos[-1] += ","
        pasos.append(f'    Orden = Table.AddColumn(Tipos, "{nueva}", each {regla}, Int64.Type)')
        columnas.append(col(nueva, "int64", oculto=True))
    pasos += ["in", "    " + pasos[-1].split("=")[0].strip()]
    return {"name": nombre, "columns": columnas + list(calculadas), "partitions": _particion(nombre, pasos)}


def tabla_python(nombre, columnas, calculadas=()):
    lista = ", ".join(f'"{c["name"]}"' for c in columnas)
    tipos = ", ".join(f'{{"{c["name"]}", {M_TIPOS[c["dataType"]]}}}' for c in columnas)
    return {"name": nombre, "columns": list(columnas) + list(calculadas), "partitions": _particion(nombre, [
        "let",
        "    Origen = MongoFinancial,",
        f'    Tabla = Origen{{[Name="{nombre}"]}}[Value],',
        f"    Columnas = Table.SelectColumns(Tabla, {{{lista}}}),",
        # El puente de Python entrega los números como texto con punto decimal ("541200.0"): se convierten
        # con cultura en-US; con la del modelo (es-ES) el punto se lee como separador de miles (x10)
        f'    Tipos = Table.TransformColumnTypes(Columnas, {{{tipos}}}, "en-US")',
        "in",
        "    Tipos"])}


def tabla_composicion():
    """Tabla estática de la cascada de P3: saldo neto -> (-) cartera vigente -> total = liquidez libre."""
    return {"name": "Composicion_Liquidez",
            "columns": [col("concepto", orden_por="orden"), col("orden", "int64", oculto=True)],
            "partitions": _particion("Composicion_Liquidez", [
                "let",
                '    Origen = #table(type table [concepto = text, orden = Int64.Type], '
                '{{"Saldo neto al corte", 1}, {"Cartera vigente", 2}})',
                "in",
                "    Origen"])}


def rel(desde, col_desde, hacia, col_hacia, activa=True):
    r = {"name": str(uuid.uuid5(uuid.NAMESPACE_URL, f"{desde}.{col_desde}->{hacia}.{col_hacia}")),
         "fromTable": desde, "fromColumn": col_desde, "toTable": hacia, "toColumn": col_hacia}
    if not activa:
        r["isActive"] = False
    return r


def wilson(base, k, n):
    """Límites de Wilson con z = 1 (Guía 07 v4, sección 6.3)."""
    cuerpo = (f"VAR n = {n} VAR p = DIVIDE({k} + 0, n) "
              "VAR c = DIVIDE(p + 1 / (2 * n), 1 + 1 / n) "
              "VAR m = DIVIDE(1, 1 + 1 / n) * SQRT(p * (1 - p) / n + 1 / (4 * n * n)) ")
    return [(f"{base} Wilson Inferior", cuerpo + "RETURN IF(n > 0, c - m)", PORC,
             f"Límite inferior de Wilson (z = 1) de {base.lower()}"),
            (f"{base} Wilson Superior", cuerpo + "RETURN IF(n > 0, c + m)", PORC,
             f"Límite superior de Wilson (z = 1) de {base.lower()}")]


def medidas(t):
    """Medidas de la Guía 07 v4. `t` traduce los nombres de tabla y columna de cada modelo.
    Devuelve (sección, [(nombre, expresión, formato, comentario), ...])."""
    E = t["estado"]
    ultimo_mes = (f"VAR ultimoMes = CALCULATE(MAX({t['fecha']}), {t['saldo']}) "
                  f"RETURN CALCULATE({{}}, FILTER(ALL({t['tiempo']}), {t['fecha']} = ultimoMes))")
    ficha = lambda c: f"CALCULATE(SELECTEDVALUE({c}), {t['saldo']})"
    return [
        ("1. PRÉSTAMOS Y RIESGO (Inicio, P1, P2, P6, D1)", [
            ("Num Prestamos", f"COUNTROWS({t['prest']})", ENTERO, "Préstamos otorgados (682)"),
            ("Prestamos en Mora", f'CALCULATE([Num Prestamos], {E} = "D")', ENTERO, "Vigentes en mora, estado D (45)"),
            ("Prestamos Vigentes", f'CALCULATE([Num Prestamos], {E} IN {{"C", "D"}})', ENTERO, "Estados C + D (448)"),
            ("Prestamos Incumplidos", f'CALCULATE([Num Prestamos], {E} = "B")', ENTERO, "Cerrados con deuda, estado B (31)"),
            ("Prestamos Cerrados", f'CALCULATE([Num Prestamos], {E} IN {{"A", "B"}})', ENTERO, "Estados A + B (234)"),
            ("Prestamos con Impago", f'CALCULATE([Num Prestamos], {E} IN {{"B", "D"}})', ENTERO, "Estados B + D (76)"),
            ("Tasa Mora Vigente", "IF([Prestamos Vigentes] > 0, DIVIDE([Prestamos en Mora] + 0, [Prestamos Vigentes]))", PORC,
             "D / (C + D) = 10.04%; 0% (no vacío) si hay vigentes sin mora, p. ej. north Bohemia 0/41"),
            ("Tasa Incumplimiento", "IF([Prestamos Cerrados] > 0, DIVIDE([Prestamos Incumplidos] + 0, [Prestamos Cerrados]))",
             PORC, "B / (A + B) = 13.25%"),
            ("Tasa Impago", "IF([Num Prestamos] > 0, DIVIDE([Prestamos con Impago] + 0, [Num Prestamos]))", PORC,
             "(B + D) / total = 11.14%; es la tasa de P6 por banda de capacidad"),
            *wilson("Mora", "[Prestamos en Mora]", "[Prestamos Vigentes]"),
            *wilson("Incumplimiento", "[Prestamos Incumplidos]", "[Prestamos Cerrados]"),
            *wilson("Impago", "[Prestamos con Impago]", "[Num Prestamos]"),
            ("Tasa Mora Banco", f"CALCULATE([Tasa Mora Vigente], REMOVEFILTERS({t['dist']}))", PORC,
             "Referencia de P2: la tasa del banco, sin el filtro de distrito"),
            ("Tasa Impago Banco", f"CALCULATE([Tasa Impago], REMOVEFILTERS({t['banda']}, {t['orden_banda']}))", PORC,
             "Referencia de P6: impago de todas las bandas"),
            ("Tasa Incumplimiento Banco", f"CALCULATE([Tasa Incumplimiento], REMOVEFILTERS({t['cli']}))", PORC,
             "Referencia de P6: incumplimiento de todos los segmentos de edad"),
            ("Tasa Impago Banda Baja", f'CALCULATE([Tasa Impago], KEEPFILTERS({t["banda"]} = "Baja"))', PORC,
             "Impago de la banda Baja (2.92%); KEEPFILTERS respeta los demás filtros"),
            ("Tasa Impago Banda Alta", f'CALCULATE([Tasa Impago], KEEPFILTERS({t["banda"]} = "Alta"))', PORC,
             "Impago de la banda Alta (23.26%)"),
            ("Cartera Total", f"SUM({t['prest']}[monto_prestamo])", MONEDA, "Monto original de todos los préstamos ($103,261,740)"),
            ("Cartera Vigente", f'CALCULATE([Cartera Total], {E} IN {{"C", "D"}})', MONEDA, "Monto original C + D ($80,296,176)"),
            ("Saldo por Cobrar Estimado",
             f'CALCULATE(SUM({t["prest"]}[saldo_pendiente_estimado]), {E} IN {{"C", "D"}})', MONEDA,
             "Capital pendiente estimado de la cartera vigente ($46,620,926)"),
            ("Monto Original en Riesgo", f'CALCULATE([Cartera Total], {E} IN {{"B", "D"}})', MONEDA,
             "Monto original de los préstamos B + D ($15,580,152)"),
            ("Monto Incumplido", f'CALCULATE([Cartera Total], {E} = "B")', MONEDA, "Monto original de los préstamos B"),
            ("Cuota Mensual", f"SUM({t['prest']}[pago_mensual])", MONEDA, "Cuota mensual de los préstamos del contexto"),
            ("Clientes con Impago", f'CALCULATE(DISTINCTCOUNT({t["prest_cli"]}), {E} = "B")', ENTERO,
             "Titulares con préstamo B (31): lista de denegación"),
            ("Cartera Distritos Sobre Mora Banco",
             f"VAR moraBanco = CALCULATE([Tasa Mora Vigente], REMOVEFILTERS({t['dist']})) "
             f"RETURN CALCULATE([Cartera Vigente], FILTER(VALUES({t['dist_nombre']}), [Tasa Mora Vigente] > moraBanco))",
             MONEDA, "CALCULATE + FILTER: cartera vigente de los distritos con mora sobre la del banco"),
            ("Distritos Sobre Mora Banco",
             f"VAR moraBanco = CALCULATE([Tasa Mora Vigente], REMOVEFILTERS({t['dist']})) "
             f"RETURN COUNTROWS(FILTER(VALUES({t['dist_nombre']}), [Tasa Mora Vigente] > moraBanco))",
             ENTERO, "Distritos con tasa de mora vigente sobre la del banco"),
            ("Region Mayor Mora",
             f"VAR r = TOPN(1, FILTER(VALUES({t['region']}), [Prestamos Vigentes] > 0), [Tasa Mora Vigente], DESC) "
             f'RETURN CONCATENATEX(r, {t["region"]} & " · " & FORMAT([Tasa Mora Vigente], "0.0%"), ", ")',
             None, "north Moravia · 15.8%"),
            ("Distrito Mayor Morosos",
             f"VAR d = TOPN(1, FILTER(VALUES({t['dist_nombre']}), [Prestamos en Mora] > 0), [Prestamos en Mora], DESC) "
             f'RETURN CONCATENATEX(d, {t["dist_nombre"]} & " · " & [Prestamos en Mora] & " en mora", ", ")',
             None, "Hl.m. Praha · 4 en mora"),
            ("Estado Prestamo",
             f'IF([Num Prestamos] > 0, CALCULATE(CONCATENATEX(VALUES({t["estado_lbl"]}), {t["estado_lbl"]}, ", "), {t["prest"]}))',
             None, "Estado del préstamo del cliente o de la cuenta (fichas)"),
            ("Banda Capacidad",
             f'IF([Num Prestamos] > 0, CONCATENATEX(VALUES({t["banda"]}), {t["banda"]}, ", "))', None,
             "Banda de capacidad de pago (ratio cuota / saldo previo)"),
            ("Distrito Prestamo",
             f'IF([Num Prestamos] > 0, CALCULATE(CONCATENATEX(VALUES({t["dist_nombre"]}), {t["dist_nombre"]}, ", "), {t["prest"]}))',
             None, "Distrito de la cuenta del préstamo"),
            ("Banda Capacidad Impago", f'CALCULATE([Banda Capacidad], {E} = "B")', None, "Banda del préstamo B (lista de P6)"),
            ("Distrito Impago", f'CALCULATE([Distrito Prestamo], {E} = "B")', None, "Distrito del préstamo B (lista de P6)"),
        ]),
        ("2. SALDOS: FOTO MENSUAL SEMIADITIVA (Inicio, P3, P4, D1, D2)", [
            ("Saldo Neto Corte", ultimo_mes.format(f"SUM({t['saldo']}[saldo_fin_mes])"), MONEDA,
             "Saldo al cierre del último mes del contexto ($197,140,434 en dic-1998)"),
            ("Cuentas Activas Corte", ultimo_mes.format(f"COUNTROWS({t['saldo']})"), ENTERO,
             "Cuentas con foto en el último mes del contexto (4,500 en dic-1998)"),
            ("Cuentas en Sobregiro", ultimo_mes.format(f"CALCULATE(COUNTROWS({t['saldo']}), {t['saldo']}[en_sobregiro] = TRUE())"),
             ENTERO, "Cuentas con saldo negativo al cierre del último mes (39 en dic-1998)"),
            ("Saldo Promedio por Cuenta", "DIVIDE([Saldo Neto Corte], [Cuentas Activas Corte])", MONEDA,
             "Saldo por cuenta activa: aísla el crecimiento por apertura de cuentas"),
            ("Saldo Promedio Banco", f"CALCULATE([Saldo Promedio por Cuenta], REMOVEFILTERS({t['dist']}))", MONEDA,
             "Referencia gris de D1"),
            ("Umbral Sobregiro", "IF(NOT ISBLANK([Saldo Neto Corte]), 0)", MONEDA2, "Línea en 0 de la ficha D2"),
            ("Saldo Neto Corte Total", f"CALCULATE([Saldo Neto Corte], {t['sin_tiempo']})", MONEDA,
             "Saldo al corte dic-1998, sin importar el año elegido"),
            ("Cartera Vigente Corte", f"CALCULATE([Cartera Vigente], {t['sin_tiempo']})", MONEDA,
             "Cartera vigente al corte, sin importar el año elegido"),
            ("Absorcion Vigente", "DIVIDE([Cartera Vigente Corte], [Saldo Neto Corte Total])", PORC,
             "KPI de liquidez de la Carta v8: cartera vigente / saldo neto al corte (40.73%)"),
            ("Absorcion Cartera Total", f"DIVIDE(CALCULATE([Cartera Total], {t['sin_tiempo']}), [Saldo Neto Corte Total])", PORC,
             "Referencia histórica: cartera total / saldo neto (52.38%)"),
            ("Absorcion Banco", f"CALCULATE([Absorcion Vigente], REMOVEFILTERS({t['dist']}))", PORC,
             "Referencia de P3: absorción del banco"),
            ("Liquidez Libre", "[Saldo Neto Corte Total] - [Cartera Vigente Corte]", MONEDA,
             "Saldo que no respalda cartera vigente ($116,844,258)"),
            ("Valor Composicion Liquidez",
             'SWITCH(SELECTEDVALUE(Composicion_Liquidez[concepto]), "Saldo neto al corte", [Saldo Neto Corte Total], '
             '"Cartera vigente", -[Cartera Vigente Corte])', MONEDA, "Cascada de P3; el total es la liquidez libre"),
        ]),
        ("3. TRANSACCIONES POR CATEGORÍA ANALÍTICA (P4, D2)", [
            ("Volumen Transaccionado", f"SUM({t['trans']}[monto_total])", MONEDA, "$6,257,862,197"),
            ("Num Transacciones", f"SUM({t['trans']}[num_transacciones])", ENTERO, "1,056,320"),
            ("Ticket Promedio", "DIVIDE([Volumen Transaccionado], [Num Transacciones])", MONEDA2, "Monto promedio por movimiento"),
            ("Desv Est Transaccion",
             f"VAR n = [Num Transacciones] VAR s = [Volumen Transaccionado] VAR sq = SUM({t['trans']}[suma_cuadrados]) "
             "RETURN IF(n > 1, SQRT(DIVIDE(sq - s * s / n, n - 1)))", MONEDA2,
             "σ muestral exacta desde la suma y la suma de cuadrados"),
            ("Ticket Limite Superior", "[Ticket Promedio] + [Desv Est Transaccion]", MONEDA2, "Promedio + 1σ"),
            ("Ticket Limite Inferior", "MAX(0, [Ticket Promedio] - [Desv Est Transaccion])", MONEDA2, "Promedio − 1σ (no negativo)"),
            ("EE Ticket", "DIVIDE([Desv Est Transaccion], SQRT([Num Transacciones]))", MONEDA2, "Error estándar (tooltip)"),
            ("Saldo Promedio Historico",
             f"DIVIDE(SUMX({t['trans']}, {t['trans']}[saldo_promedio] * {t['trans']}[num_transacciones]), [Num Transacciones])",
             MONEDA, "Saldo promedio de la cuenta ponderado por movimientos"),
        ]),
        ("4. ÓRDENES Y CAPACIDAD DE PAGO (P5, D2)", [
            ("Compromiso Ordenes", f"SUM({t['ord']}[monto_orden])", MONEDA, "Órdenes fijas mensuales ($21,229,041)"),
            ("Num Ordenes", f"COUNTROWS({t['ord']})", ENTERO, "6,471 órdenes"),
            ("Pct Ordenes", f"DIVIDE([Num Ordenes], CALCULATE([Num Ordenes], REMOVEFILTERS({t['cat_orden']})))", PORC,
             "Participación de cada propósito"),
            ("Indice Saturacion",
             f"DIVIDE([Compromiso Ordenes], CALCULATE([Saldo Promedio Historico], {t['sin_tiempo']}, REMOVEFILTERS({t['cat_trans']})))",
             INDICE, "Órdenes mensuales / saldo promedio histórico de la cuenta (cuenta 2335: 2.14)"),
            ("Cuentas Saturadas", f"COUNTROWS(FILTER(VALUES({t['cuenta']}), [Indice Saturacion] > 0.5))", ENTERO,
             "CALCULATE + FILTER: cuentas con índice > 0.5 (47)"),
            ("Cuentas Sobre Saldo", f"COUNTROWS(FILTER(VALUES({t['cuenta']}), [Indice Saturacion] > 1))", ENTERO,
             "Cuentas cuyas órdenes superan su saldo promedio (1)"),
            ("Cuentas con Credito Externo", f"CALCULATE(DISTINCTCOUNT({t['ord_cta']}), {t['cred']} = TRUE())", ENTERO,
             "Cuentas que pagan un préstamo a otra entidad (35)"),
            ("Credito Externo Mensual", f'CALCULATE([Compromiso Ordenes], {t["cred"]} = TRUE(), {t["ks"]} = "UVER")', MONEDA,
             "Cuotas mensuales a otras entidades ($177,154)"),
            ("Indice Saturacion Alerta", "VAR i = [Indice Saturacion] RETURN IF(i > 0.5, i)", INDICE, "Solo cuentas en alerta"),
            ("Compromiso Alerta", "IF([Indice Saturacion] > 0.5, [Compromiso Ordenes])", MONEDA, "Solo cuentas en alerta"),
            ("Saldo Promedio Alerta",
             f"IF([Indice Saturacion] > 0.5, CALCULATE([Saldo Promedio Historico], {t['sin_tiempo']}, REMOVEFILTERS({t['cat_trans']})))",
             MONEDA, "Solo cuentas en alerta"),
            ("Credito Externo Alerta", "IF([Indice Saturacion] > 0.5, [Credito Externo Mensual])", MONEDA, "Solo cuentas en alerta"),
            ("Cliente Titular Alerta", f"IF([Indice Saturacion] > 0.5, {ficha(t['cli_nombre'])})", None, "Solo cuentas en alerta"),
            ("Cuenta Alerta", f"IF([Indice Saturacion] > 0.5, {ficha(t['cuenta_lbl'])})", None, "Cuenta del titular en alerta"),
        ]),
        ("5. FICHAS D1 Y D2, RECOMENDACIONES Y TÍTULOS DINÁMICOS", [
            ("Titulo Distrito",
             f'"Distrito: " & SELECTEDVALUE({t["dist_nombre"]}, "(varios)") & " (" & SELECTEDVALUE({t["region"]}, "varias regiones") & ")"',
             None, "Título dinámico de D1"),
            ("Region del Distrito", f'SELECTEDVALUE({t["region"]})', None, "Región del distrito (tooltip del treemap de P2)"),
            ("Poblacion Distrito", f"SELECTEDVALUE({t['dist']}[poblacion])", ENTERO, "Habitantes"),
            ("Salario Promedio Distrito", f"SELECTEDVALUE({t['dist']}[salario_promedio])", MONEDA, "Salario promedio"),
            ("Desempleo Distrito 1995", f"SELECTEDVALUE({t['dist']}[tasa_desempleo])", "0.00", "Tasa de desempleo 1995 (%)"),
            ("Origen Indicadores",
             f'IF(HASONEVALUE({t["dist"]}[es_imputado]), IF(VALUES({t["dist"]}[es_imputado]), "Imputado (Informe 10)", "Fuente original"))',
             None, "Marca el distrito 69 con indicadores imputados"),
            ("Cliente Ficha", ficha(t["cli_nombre"]), None, "Titular de la cuenta (vale si se llega por cliente o por cuenta)"),
            ("Cuenta Ficha", ficha(t["cuenta_lbl"]), None, "Cuenta del titular"),
            ("Titulo Cliente",
             f'"Ficha 360 · " & COALESCE([Cliente Ficha], SELECTEDVALUE({t["cli_nombre"]}, "(varios clientes)")) & '
             '" · " & COALESCE([Cuenta Ficha], "sin cuenta propia")', None, "Título dinámico de D2"),
            ("Edad Cliente", ficha(f"{t['cli']}[edad_corte]"), ENTERO, "Edad al 31/12/1998"),
            ("Segmento Cliente", ficha(t["segmento"]), None, "Segmento de edad (3 grupos del Data Mart)"),
            ("Arquetipo Cliente", ficha(f"{t['cli']}[arquetipo_demografico]"), None, "Macro-región y segmento"),
            ("Calificacion Cliente", ficha(t["calificacion"]), None, "Buen / Mal pagador / Sin evaluar"),
            ("Distrito Cuenta", ficha(t["dist_nombre"]), None, "Distrito de la cuenta"),
            ("Cuota Maxima Prudente", f"SUM({t['rec']}[prestamo_cuota_maxima])", MONEDA,
             "Cuota que deja el ratio en la banda Baja (Informe 04)"),
            ("Monto Maximo Prudente", f"SUM({t['rec']}[prestamo_monto_maximo_36m])", MONEDA,
             "Monto a 36 meses con esa cuota (Informe 04)"),
        ]),
        ("6. RECOMENDADORES (R1–R3; sistemas elegidos en el Informe 04, script 43)", [
            ("Recomendaciones Demograficas", f'CALCULATE(COUNTROWS({t["recp"]}), {t["recp"]}[sistema] = "Demográfico")', ENTERO,
             "Productos en el top 3 del recomendador demográfico (el más preciso: Hit@1 66.0%)"),
            ("Primera Opcion", f"CALCULATE([Recomendaciones Demograficas], {t['recp']}[posicion] = 1)", ENTERO,
             "Veces que el producto es la primera recomendación"),
            ("Recomendaciones kNN", f'CALCULATE(COUNTROWS({t["recp"]}), {t["recp"]}[sistema] = "kNN perfil")', ENTERO,
             "Productos en el top 3 del kNN por perfil exógeno"),
            ("Descubrimientos kNN", f"CALCULATE([Recomendaciones kNN], {t['recp']}[es_descubrimiento] = TRUE())", ENTERO,
             "Ofertas del kNN que el demográfico no tiene en su top 3 (2,731)"),
            ("Clientes con Recomendacion", f'CALCULATE(DISTINCTCOUNT({t["recp_cta"]}), {t["recp"]}[sistema] = "Demográfico")', ENTERO,
             "Titulares con al menos una recomendación"),
            ("Cuentas que ya lo Usan", f"COUNTROWS({t['adp']})", ENTERO, "Cuentas que ya usan el producto (adopción actual)"),
            ("Titulares", f"COUNTROWS({t['cap']})", ENTERO, "Titulares (una cuenta cada uno: 4,500)"),
            ("Penetracion Actual", "DIVIDE([Cuentas que ya lo Usan], [Titulares])", PORC,
             "Cuentas que ya usan el producto / titulares del contexto"),
            ("Producto Mas Recomendado",
             f"VAR x = TOPN(1, VALUES({t['prod']}[producto]), [Primera Opcion], DESC) "
             f'RETURN CONCATENATEX(x, {t["prod"]}[producto] & " · " & FORMAT([Primera Opcion], "#,0"), ", ")', None,
             "Primera recomendación más frecuente en el contexto"),
            ("Recomendacion 1", f'CALCULATE(SELECTEDVALUE({t["recp"]}[producto]), {t["recp"]}[sistema] = "Demográfico", {t["recp"]}[posicion] = 1)',
             None, "Primera recomendación del titular"),
            ("Recomendacion 2", f'CALCULATE(SELECTEDVALUE({t["recp"]}[producto]), {t["recp"]}[sistema] = "Demográfico", {t["recp"]}[posicion] = 2)',
             None, "Segunda recomendación del titular"),
            ("Recomendacion 3", f'CALCULATE(SELECTEDVALUE({t["recp"]}[producto]), {t["recp"]}[sistema] = "Demográfico", {t["recp"]}[posicion] = 3)',
             None, "Tercera recomendación del titular"),
            ("Descubrimiento kNN",
             f'CALCULATE(CONCATENATEX(VALUES({t["recp"]}[producto]), {t["recp"]}[producto], ", "), '
             f'{t["recp"]}[sistema] = "kNN perfil", {t["recp"]}[es_descubrimiento] = TRUE())', None,
             "Productos que el kNN añade para el titular"),
            ("Acierto Elegido", f'CALCULATE(MAX({t["evalr"]}[hit_1]), {t["evalr"]}[modelo] = "Demográfico (arquetipo)")', PORC,
             "Hit@1 del demográfico (66.0%, semilla 42)"),
            ("Acierto Popularidad", f'CALCULATE(MAX({t["evalr"]}[hit_1]), {t["evalr"]}[modelo] = "Popularidad")', PORC,
             "Hit@1 de recomendar lo más popular (58.5%): la línea base"),
            ("Acierto Cola Larga kNN",
             f'CALCULATE(MAX({t["evalr"]}[hit_1_cola_larga]), {t["evalr"]}[modelo] = "kNN usuario-usuario (perfil exógeno)")', PORC,
             "Hit@1 del kNN en productos poco comunes (37.2%)"),
            ("Acierto Cola Larga Popularidad",
             f'CALCULATE(MAX({t["evalr"]}[hit_1_cola_larga]), {t["evalr"]}[modelo] = "Popularidad")', PORC,
             "Hit@1 de la popularidad en productos poco comunes (6.3%)"),
            ("Acierto Hit1", f"SUM({t['evalr']}[hit_1])", PORC, "Hit@1 del modelo (gráfico comparativo)"),
            ("Acierto Cola Larga", f"SUM({t['evalr']}[hit_1_cola_larga])", PORC, "Hit@1 en la cola larga (gráfico comparativo)"),
            ("MRR Modelo", f"SUM({t['evalr']}[mrr])", "0.000", "Rango recíproco medio"),
            ("MRR Confirmacion", f"SUM({t['evalr']}[mrr_confirmacion])", "0.000", "MRR con la semilla 2026"),
            ("Titulares sin Prestamo", f"CALCULATE([Titulares], {t['cap']}[tiene_prestamo] = FALSE())", ENTERO, "3,818"),
            ("Prestamos Prudentes Recomendados", f"CALCULATE([Titulares], {t['cap']}[prestamo_recomendado] = TRUE())", ENTERO,
             "Titulares con préstamo en su top 3 (1,721)"),
            ("Cuota Prudente Mediana", f"CALCULATE(MEDIAN({t['cap']}[cuota_prudente]), {t['cap']}[tiene_prestamo] = FALSE())", MONEDA2,
             "5.7% del saldo promedio, mediana de los titulares sin préstamo (1,873)"),
            ("Pueden Pagar Prestamo Tipico", f"CALCULATE([Titulares], {t['cap']}[puede_pagar_prestamo_tipico] = TRUE())", ENTERO,
             "Titulares sin préstamo cuya cuota prudente cubre la cuota mediana otorgada (71)"),
            ("Monto Prudente Ofrecible 36m", f"CALCULATE(SUM({t['cap']}[monto_maximo_36m]), {t['cap']}[prestamo_recomendado] = TRUE())",
             MONEDA, "Suma de montos máximos a 36 meses de los préstamos recomendados"),
            ("Saldo Promedio Oferta", f"CALCULATE(SUM({t['cap']}[saldo_promedio]), {t['cap']}[prestamo_recomendado] = TRUE())", MONEDA,
             "Saldo promedio del titular con préstamo recomendado"),
            ("Cuota Prudente Oferta", f"CALCULATE(SUM({t['cap']}[cuota_prudente]), {t['cap']}[prestamo_recomendado] = TRUE())", MONEDA,
             "Cuota prudente del titular con préstamo recomendado"),
            ("Monto 12m Oferta", f"CALCULATE(SUM({t['cap']}[monto_maximo_12m]), {t['cap']}[prestamo_recomendado] = TRUE())", MONEDA,
             "Monto máximo a 12 meses"),
            ("Monto 36m Oferta", f"CALCULATE(SUM({t['cap']}[monto_maximo_36m]), {t['cap']}[prestamo_recomendado] = TRUE())", MONEDA,
             "Monto máximo a 36 meses"),
            ("Monto 60m Oferta", f"CALCULATE(SUM({t['cap']}[monto_maximo_60m]), {t['cap']}[prestamo_recomendado] = TRUE())", MONEDA,
             "Monto máximo a 60 meses"),
            ("AUC Regla", f"MAX({t['regla']}[auc])", "0.000", "AUC de la regla para predecir el impago"),
            ("AUC Regla Elegida", f'CALCULATE([AUC Regla], {t["regla"]}[regla] = "Carta v8: cuota / saldo previo")', "0.000", "0.717"),
            ("AUC Regla Anterior", f'CALCULATE([AUC Regla], {t["regla"]}[regla] = "Anterior: cuota / salario del distrito")', "0.000",
             "0.659"),
            ("P Destino dado Origen", f"SUM({t['asoc']}[p_destino_dado_origen])", PORC,
             "De quienes tienen el producto de origen, % que también tiene el de destino"),
            ("Lift Asociacion", f"SUM({t['asoc']}[lift])", "0.00", "Lift: > 1 van juntos más de lo esperado por azar"),
            ("Regla Mas Fuerte",
             f"VAR x = TOPN(1, FILTER({t['asoc']}, {t['asoc']}[cuentas_ambos] >= 100), {t['asoc']}[lift], DESC, {t['asoc']}[p_destino_dado_origen], DESC) "
             f'RETURN CONCATENATEX(x, {t["asoc"]}[producto_origen] & " → " & {t["asoc"]}[producto_destino] & " · " & '
             f'FORMAT({t["asoc"]}[p_destino_dado_origen], "0.0%"), ", ")', None,
             "Par con mayor lift (al menos 100 cuentas), en la dirección de mayor P(j|i): Seguro → Transferencias 99.8%"),
        ]),
        ("7. COLORES CONDICIONALES (formato por valor de campo)", [
            ("Color Mora", f"VAR x = [Tasa Mora Vigente] RETURN SWITCH(TRUE(), ISBLANK(x), \"#FFFFFF\", x < 0.05, \"{BANDAS['Baja']}\", "
                           f"x < 0.10, \"{BANDAS['Media-baja']}\", x < 0.15, \"{BANDAS['Media-alta']}\", \"{BANDAS['Alta']}\")", None,
             "Treemap de P2: escala secuencial blanco → bermellón por tasa de mora"),
            ("Color Saturacion", f"VAR x = [Indice Saturacion] RETURN IF(x > 1, \"{ALERTA}\", IF(x > 0.5, \"{EST_D}\", \"{GRIS}\"))", None,
             "Dispersión de P5: bermellón > 1, naranja > 0.5, gris el resto"),
            ("Color Modelo", f"IF(SELECTEDVALUE({t['evalr']}[elegido]) = TRUE(), \"{EST_A}\", \"#BDBDBD\")", None,
             "R1: modelos elegidos en azul, el resto en gris"),
            ("Color Regla", f'IF(SELECTEDVALUE({t["regla"]}[regla]) = "Carta v8: cuota / saldo previo", \"{EST_A}\", \"#BDBDBD\")', None,
             "R2: regla elegida en azul"),
        ]),
    ]


def lista_medidas(t):
    salida = []
    for _, grupo in medidas(t):
        for nombre, expr, fmt, coment in grupo:
            d = {"name": nombre, "expression": expr, "description": coment}
            if fmt:
                d["formatString"] = fmt
            salida.append(d)
    return salida


def tabla_medidas(t):
    return {"name": "_Medidas",
            "columns": [{"name": "Medidas", "dataType": "string", "isHidden": True, "sourceColumn": "Medidas",
                         "summarizeBy": "none"}],
            "partitions": _particion("_Medidas", ["let", '    Origen = #table(type table [Medidas = text], {{"Guía 07 v4"}})',
                                                  "in", "    Origen"]),
            "measures": lista_medidas(t)}


def modelo_base(nombre, tablas, relaciones, expresiones):
    return {
        "name": nombre,
        "compatibilityLevel": 1606,
        "model": {
            "culture": "es-ES",
            "dataAccessOptions": {"legacyRedirects": True, "returnErrorValuesAsNull": True},
            "defaultPowerBIDataSourceVersion": "powerBI_V3",
            "sourceQueryCulture": "es-ES",
            "tables": tablas,
            "relationships": relaciones,
            "expressions": expresiones,
            "annotations": [{"name": "__PBI_TimeIntelligenceEnabled", "value": "0"}],
        },
    }


def ESTADO_LBL(c):
    return (f'SWITCH({c}, "A", "A · Cerrado al día", "B", "B · Cerrado con deuda", '
            f'"C", "C · Vigente al día", "D", "D · Vigente en mora")')


# Orden de las categorías ordinales (se evalúa en ese orden: "Media-baja" antes que "Baja")
ORDEN_BANDA = {"Media-baja": 2, "Media-alta": 3, "Baja": 1, "Alta": 4}
ORDEN_SEGMENTO = {"Joven": 1, "Mayor": 3, "Adulto": 2}


MACRO_REGION = ('SWITCH(TRUE(), Dim_Distrito[region] = "Prague", "Praga", '
                'CONTAINSSTRING(Dim_Distrito[region], "Moravia"), "Moravia", "Bohemia")')


def columnas_filtro_cliente(cli, prest, estado_lbl, banda, orden_banda, recp, cap):
    """Atributos del TITULAR calculados desde los hechos. Van en la dimensión cliente para que un filtro sobre
    ellos llegue a TODOS los hechos (préstamos, saldos, órdenes, transacciones, recomendaciones): así la
    selección del gerente vale para todo el proyecto y no solo para las páginas de préstamos."""
    return [
        col_calc("Estado del Prestamo",
                 f'VAR e = CALCULATE(MAX({estado_lbl}), CALCULATETABLE({prest})) RETURN IF(ISBLANK(e), "Sin préstamo", e)'),
        col_calc("Banda de Capacidad",
                 f'VAR b = CALCULATE(MAX({banda}), CALCULATETABLE({prest})) RETURN IF(ISBLANK(b), "Sin préstamo", b)',
                 orden_por="Orden Banda Cliente"),
        col_calc("Orden Banda Cliente", f"VAR o = CALCULATE(MAX({orden_banda}), CALCULATETABLE({prest})) RETURN IF(ISBLANK(o), 5, o)",
                 "int64", oculto=True),
        col_calc("Alerta de Saturacion",
                 'VAR i = [Indice Saturacion] RETURN SWITCH(TRUE(), ISBLANK(i), "Sin órdenes", i > 1, "Crítica (> 1)", '
                 'i > 0.5, "Alta (> 0.5)", "Normal")'),
        col_calc("Primera Oferta",
                 f'VAR x = CALCULATE(MAX({recp}[producto]), {recp}[sistema] = "Demográfico", {recp}[posicion] = 1) '
                 'RETURN IF(ISBLANK(x), "Sin recomendación", x)'),
        col_calc("Prestamo Recomendado",
                 f'IF(CALCULATE(COUNTROWS({cap})) = 0, "Sin cuenta propia", '
                 f'IF(CALCULATE(COUNTROWS({cap}), {cap}[prestamo_recomendado] = TRUE()) > 0, "Sí", "No"))'),
    ]


def modelo_kimball():
    k, d, b = "int64", "double", "boolean"
    oc = lambda *nombres: [col(n, k, oculto=True) for n in nombres]
    tablas = [
        tabla_sql("Dim_Tiempo", oc("sk_tiempo") + [col("fecha", "dateTime", "dd/mm/yyyy"), col("anio", k), col("mes", k),
                                                   col("nombre_mes"), col("es_fin_de_mes", b)]),
        {"name": "Dim_Anio", "columns": [col("anio", k)], "partitions": _particion("Dim_Anio", [
            "let",
            "    Origen = Sql.Database(ServidorSQL, BaseDatosSQL),",
            '    Tiempo = Origen{[Schema="dbo", Item="Dim_Tiempo"]}[Data],',
            '    Anios = Table.Distinct(Table.SelectColumns(Tiempo, {"anio"})),',
            '    Tipos = Table.TransformColumnTypes(Anios, {{"anio", Int64.Type}})',
            "in",
            "    Tipos"])},
        tabla_sql("Dim_Distrito", oc("sk_distrito") + [
            col("id_distrito_bk", k), col("nombre_distrito"), col("region"), col("poblacion", k),
            col("salario_promedio", d, MONEDA), col("tasa_desempleo", d, "0.00"), col("tasa_criminalidad", d, "0.00"),
            col("es_imputado", b)], [col_calc("Macro Region", MACRO_REGION)]),
        tabla_sql("Dim_Cliente", oc("sk_cliente") + [
            col("id_cliente_bk", k), col("sexo"), col("edad_corte", k), col("tipo_disposicion"),
            col("segmento_edad", orden_por="Orden Segmento"), col("arquetipo_demografico"), col("calificacion_pago_desc")],
            [col_calc("Cliente", '"Cliente " & Dim_Cliente[id_cliente_bk]')]
            + columnas_filtro_cliente("Dim_Cliente", "Fact_Prestamos", "Dim_Estado_Prestamo[Estado]",
                                      "Fact_Prestamos[banda_capacidad]", "Fact_Prestamos[Orden Banda]",
                                      "Recomendacion_Producto", "Capacidad_Prestamo"),
            orden_m=("Orden Segmento", "segmento_edad", ORDEN_SEGMENTO)),
        tabla_sql("Dim_Cuenta", oc("sk_cuenta") + [
            col("id_cuenta_bk", k), col("frecuencia_emision_estado"), col("fecha_apertura", "dateTime", "dd/mm/yyyy"),
            col("tiene_credito_externo", b), col("monto_credito_externo", d, MONEDA)],
            [col_calc("Cuenta", '"Cuenta " & Dim_Cuenta[id_cuenta_bk]')]),
        tabla_sql("Dim_Estado_Prestamo", oc("sk_estado_prestamo") + [col("codigo_estado"), col("condicion"), col("descripcion")],
                  [col_calc("Estado", ESTADO_LBL("Dim_Estado_Prestamo[codigo_estado]"))]),
        tabla_sql("Dim_Orden", oc("sk_orden_tipo") + [col("k_symbol_original"), col("categoria_orden_traducida")]),
        tabla_sql("Fact_Prestamos", oc("sk_prestamo", "sk_tiempo", "sk_cuenta", "sk_cliente", "sk_distrito", "sk_estado_prestamo") + [
            col("id_prestamo_bk", k), col("monto_prestamo", d, MONEDA), col("plazo_meses", k), col("pago_mensual", d, MONEDA),
            col("meses_transcurridos_al_corte", k), col("saldo_pendiente_estimado", d, MONEDA),
            col("saldo_promedio_previo", d, MONEDA), col("ratio_cuota_saldo_previo", d, PORC),
            col("banda_capacidad", orden_por="Orden Banda")],
            orden_m=("Orden Banda", "banda_capacidad", ORDEN_BANDA)),
        tabla_sql("Fact_Ordenes", oc("sk_orden", "sk_tiempo_apertura_cuenta", "sk_cuenta", "sk_cliente", "sk_distrito",
                                     "sk_orden_tipo") + [col("id_orden_bk", k), col("monto_orden", d, MONEDA)]),
        tabla_sql("Fact_Saldo_Cuenta_Mensual", oc("sk_cuenta", "sk_mes", "sk_cliente", "sk_distrito") + [
            col("saldo_fin_mes", d, MONEDA), col("saldo_promedio_mes", d, MONEDA), col("num_movimientos_mes", k),
            col("en_sobregiro", b)]),
        tabla_sql("vw_PBI_Trans_Anual_Cuenta", oc("sk_cuenta", "sk_cliente", "sk_distrito") + [
            col("categoria_analitica"), col("anio", k), col("num_transacciones", k), col("monto_total", d, MONEDA),
            col("suma_cuadrados", d, oculto=True), col("saldo_promedio", d, MONEDA)]),
        tabla_sql("Recomendacion_Cuenta", oc("sk_cuenta", "sk_cliente") + [
            col("modelo"), col("recomendacion_1"), col("recomendacion_2"), col("recomendacion_3"),
            col("prestamo_cuota_maxima", d, MONEDA), col("prestamo_monto_maximo_36m", d, MONEDA)]),
        tabla_sql("Dim_Producto", [col("producto", orden_por="orden"), col("codigo"), col("descripcion"),
                                   col("penetracion", d, PORC), col("orden", k, oculto=True)]),
        tabla_sql("Recomendacion_Producto", oc("sk_cuenta", "sk_cliente", "sk_distrito") + [
            col("sistema"), col("producto"), col("posicion", k), col("puntaje", d, "0.0000"), col("es_descubrimiento", b)]),
        tabla_sql("Adopcion_Producto", oc("sk_cuenta", "sk_cliente", "sk_distrito") + [col("producto")]),
        tabla_sql("Capacidad_Prestamo", oc("sk_cuenta", "sk_cliente", "sk_distrito") + [
            col("tiene_prestamo", b), col("saldo_promedio", d, MONEDA), col("cuota_prudente", d, MONEDA),
            col("monto_maximo_12m", d, MONEDA), col("monto_maximo_36m", d, MONEDA), col("monto_maximo_60m", d, MONEDA),
            col("tramo_monto_36m", orden_por="orden_tramo"), col("orden_tramo", k, oculto=True),
            col("puede_pagar_prestamo_tipico", b), col("prestamo_recomendado", b)]),
        tabla_sql("Evaluacion_Recomendador", [
            col("modelo", orden_por="orden"), col("familia"), col("rol"), col("hit_1", d, PORC), col("hit_3", d, PORC),
            col("mrr", d, "0.000"), col("hit_1_cola_larga", d, PORC), col("mrr_confirmacion", d, "0.000"),
            col("orden", k, oculto=True), col("elegido", b)]),
        tabla_sql("Asociacion_Producto", [col("producto_origen"), col("producto_destino"),
                                          col("p_destino_dado_origen", d, PORC), col("lift", d, "0.00"), col("cuentas_ambos", k)]),
        tabla_sql("Regla_Capacidad", [col("regla"), col("tramo", orden_por="orden"), col("orden", k, oculto=True),
                                      col("prestamos", k), col("impagos", k), col("tasa_impago", d, PORC), col("auc", d, "0.000")]),
        tabla_composicion(),
    ]
    t = dict(prest="Fact_Prestamos", ord="Fact_Ordenes", trans="vw_PBI_Trans_Anual_Cuenta", saldo="Fact_Saldo_Cuenta_Mensual",
             tiempo="Dim_Tiempo", fecha="Dim_Tiempo[fecha]", cli="Dim_Cliente", dist="Dim_Distrito", rec="Recomendacion_Cuenta",
             estado="Dim_Estado_Prestamo[codigo_estado]", estado_lbl="Dim_Estado_Prestamo[Estado]",
             banda="Fact_Prestamos[banda_capacidad]", orden_banda="Fact_Prestamos[Orden Banda]",
             prest_cli="Fact_Prestamos[sk_cliente]", ord_cta="Fact_Ordenes[sk_cuenta]",
             sin_tiempo="REMOVEFILTERS(Dim_Anio), REMOVEFILTERS(Dim_Tiempo)",
             cat_trans="vw_PBI_Trans_Anual_Cuenta[categoria_analitica]", cat_orden="Dim_Orden[categoria_orden_traducida]",
             ks="Dim_Orden[k_symbol_original]", cred="Dim_Cuenta[tiene_credito_externo]",
             cuenta="Dim_Cuenta[id_cuenta_bk]", cuenta_lbl="Dim_Cuenta[Cuenta]", region="Dim_Distrito[region]",
             dist_nombre="Dim_Distrito[nombre_distrito]", cli_nombre="Dim_Cliente[Cliente]",
             segmento="Dim_Cliente[segmento_edad]", calificacion="Dim_Cliente[calificacion_pago_desc]",
             recp="Recomendacion_Producto", adp="Adopcion_Producto", cap="Capacidad_Prestamo", evalr="Evaluacion_Recomendador",
             asoc="Asociacion_Producto", regla="Regla_Capacidad", prod="Dim_Producto", recp_cta="Recomendacion_Producto[sk_cuenta]")
    tablas.append(tabla_medidas(t))
    rels = []
    for f in ["Fact_Prestamos", "Fact_Ordenes", "Fact_Saldo_Cuenta_Mensual", "vw_PBI_Trans_Anual_Cuenta"]:
        rels += [rel(f, "sk_distrito", "Dim_Distrito", "sk_distrito"), rel(f, "sk_cliente", "Dim_Cliente", "sk_cliente"),
                 rel(f, "sk_cuenta", "Dim_Cuenta", "sk_cuenta")]
    rels += [rel("Fact_Prestamos", "sk_estado_prestamo", "Dim_Estado_Prestamo", "sk_estado_prestamo"),
             rel("Fact_Prestamos", "sk_tiempo", "Dim_Tiempo", "sk_tiempo"),
             rel("Fact_Saldo_Cuenta_Mensual", "sk_mes", "Dim_Tiempo", "sk_tiempo"),
             rel("Fact_Ordenes", "sk_orden_tipo", "Dim_Orden", "sk_orden_tipo"),
             # Rol de Dim_Tiempo: la apertura de la cuenta NO es la fecha de la orden -> inactiva
             rel("Fact_Ordenes", "sk_tiempo_apertura_cuenta", "Dim_Tiempo", "sk_tiempo", activa=False),
             rel("Dim_Tiempo", "anio", "Dim_Anio", "anio"),
             rel("vw_PBI_Trans_Anual_Cuenta", "anio", "Dim_Anio", "anio"),
             rel("Recomendacion_Cuenta", "sk_cuenta", "Dim_Cuenta", "sk_cuenta"),
             rel("Recomendacion_Cuenta", "sk_cliente", "Dim_Cliente", "sk_cliente")]
    for f in ["Recomendacion_Producto", "Adopcion_Producto", "Capacidad_Prestamo"]:
        rels += [rel(f, "sk_cuenta", "Dim_Cuenta", "sk_cuenta"), rel(f, "sk_cliente", "Dim_Cliente", "sk_cliente"),
                 rel(f, "sk_distrito", "Dim_Distrito", "sk_distrito")]
    rels += [rel("Recomendacion_Producto", "producto", "Dim_Producto", "producto"),
             rel("Adopcion_Producto", "producto", "Dim_Producto", "producto")]
    expresiones = [
        {"name": "ServidorSQL", "kind": "m",
         "expression": '"(localdb)\\MSSQLLocalDB" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]'},
        {"name": "BaseDatosSQL", "kind": "m",
         "expression": '"DM_Financial_Kimball_v2" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]'},
    ]
    return modelo_base("Dashboard_Financial_Kimball", tablas, rels, expresiones), t


def modelo_mongo():
    k, d, b = "int64", "double", "boolean"
    oc = lambda *nombres: [col(n, k, oculto=True) for n in nombres]
    tablas = [
        tabla_python("m_distritos", [col("id_distrito", k), col("nombre_distrito"), col("region"), col("poblacion", k),
                                     col("salario_promedio", d, MONEDA), col("tasa_desempleo", d, "0.00"),
                                     col("tasa_criminalidad", d, "0.00"), col("es_imputado", b), col("macro_region")]),
        tabla_python("m_clientes", [col("id_cliente", k), col("cliente"), col("sexo"), col("edad_corte", k),
                                    col("tipo_disposicion"), col("segmento_edad", orden_por="orden_segmento"),
                                    col("arquetipo_demografico"), col("calificacion_pago"), col("orden_segmento", k, oculto=True)],
                     columnas_filtro_cliente("m_clientes", "m_prestamos", "m_prestamos[estado]", "m_prestamos[banda_capacidad]",
                                             "m_prestamos[orden_banda]", "m_recomendacion_producto", "m_capacidad_prestamo")),
        tabla_python("m_cuentas", [col("id_cuenta", k), col("frecuencia_extracto"), col("fecha_apertura", "dateTime", "dd/mm/yyyy"),
                                   col("tiene_credito_externo", b), col("monto_credito_externo", d, MONEDA)],
                     [col_calc("cuenta", '"Cuenta " & m_cuentas[id_cuenta]')]),
        tabla_python("m_anios", [col("anio", k)]),
        tabla_python("m_meses", [col("fecha_mes", "dateTime", "dd/mm/yyyy"), col("anio", k), col("mes", k)]),
        tabla_python("m_prestamos", [col("id_prestamo", k)] + oc("id_cuenta", "id_cliente", "id_distrito") + [
            col("fecha_otorgamiento", "dateTime", "dd/mm/yyyy"), col("anio", k), col("monto_prestamo", d, MONEDA),
            col("plazo_meses", k), col("pago_mensual", d, MONEDA), col("saldo_pendiente_estimado", d, MONEDA),
            col("meses_transcurridos_al_corte", k), col("codigo_estado"), col("condicion"), col("descripcion_estado"),
            col("saldo_promedio_previo", d, MONEDA), col("ratio_cuota_saldo_previo", d, PORC),
            col("banda_capacidad", orden_por="orden_banda"), col("orden_banda", k, oculto=True)],
            [col_calc("estado", ESTADO_LBL("m_prestamos[codigo_estado]"))]),
        tabla_python("m_ordenes", [col("id_orden", k)] + oc("id_cuenta", "id_cliente", "id_distrito") + [
            col("k_symbol"), col("categoria_orden"), col("monto_orden", d, MONEDA)]),
        tabla_python("m_trans_anual", oc("id_cuenta", "id_cliente", "id_distrito") + [
            col("anio", k), col("categoria_analitica"), col("num_transacciones", k), col("monto_total", d, MONEDA),
            col("suma_cuadrados", d, oculto=True), col("saldo_promedio", d, MONEDA)]),
        tabla_python("m_saldo_mensual", oc("id_cuenta", "id_cliente", "id_distrito", "anio", "mes") + [
            col("fecha_mes", "dateTime", "dd/mm/yyyy"), col("saldo_fin_mes", d, MONEDA), col("saldo_promedio_mes", d, MONEDA),
            col("num_movimientos_mes", k), col("en_sobregiro", b)]),
        tabla_python("m_recomendaciones", oc("id_cuenta", "id_cliente") + [
            col("modelo"), col("recomendacion_1"), col("recomendacion_2"), col("recomendacion_3"),
            col("prestamo_cuota_maxima", d, MONEDA), col("prestamo_monto_maximo_36m", d, MONEDA)]),
        tabla_python("m_dim_producto", [col("producto", orden_por="orden"), col("codigo"), col("descripcion"),
                                   col("penetracion", d, PORC), col("orden", k, oculto=True)]),
        tabla_python("m_recomendacion_producto", oc("id_cuenta", "id_cliente", "id_distrito") + [
            col("sistema"), col("producto"), col("posicion", k), col("puntaje", d, "0.0000"), col("es_descubrimiento", b)]),
        tabla_python("m_adopcion_producto", oc("id_cuenta", "id_cliente", "id_distrito") + [col("producto")]),
        tabla_python("m_capacidad_prestamo", oc("id_cuenta", "id_cliente", "id_distrito") + [
            col("tiene_prestamo", b), col("saldo_promedio", d, MONEDA), col("cuota_prudente", d, MONEDA),
            col("monto_maximo_12m", d, MONEDA), col("monto_maximo_36m", d, MONEDA), col("monto_maximo_60m", d, MONEDA),
            col("tramo_monto_36m", orden_por="orden_tramo"), col("orden_tramo", k, oculto=True),
            col("puede_pagar_prestamo_tipico", b), col("prestamo_recomendado", b)]),
        tabla_python("m_evaluacion_recomendador", [
            col("modelo", orden_por="orden"), col("familia"), col("rol"), col("hit_1", d, PORC), col("hit_3", d, PORC),
            col("mrr", d, "0.000"), col("hit_1_cola_larga", d, PORC), col("mrr_confirmacion", d, "0.000"),
            col("orden", k, oculto=True), col("elegido", b)]),
        tabla_python("m_asociacion_producto", [col("producto_origen"), col("producto_destino"),
                                          col("p_destino_dado_origen", d, PORC), col("lift", d, "0.00"), col("cuentas_ambos", k)]),
        tabla_python("m_regla_capacidad", [col("regla"), col("tramo", orden_por="orden"), col("orden", k, oculto=True),
                                      col("prestamos", k), col("impagos", k), col("tasa_impago", d, PORC), col("auc", d, "0.000")]),
        tabla_composicion(),
    ]
    t = dict(prest="m_prestamos", ord="m_ordenes", trans="m_trans_anual", saldo="m_saldo_mensual",
             tiempo="m_meses", fecha="m_meses[fecha_mes]", cli="m_clientes", dist="m_distritos", rec="m_recomendaciones",
             estado="m_prestamos[codigo_estado]", estado_lbl="m_prestamos[estado]",
             banda="m_prestamos[banda_capacidad]", orden_banda="m_prestamos[orden_banda]",
             prest_cli="m_prestamos[id_cliente]", ord_cta="m_ordenes[id_cuenta]",
             sin_tiempo="REMOVEFILTERS(m_anios), REMOVEFILTERS(m_meses)",
             cat_trans="m_trans_anual[categoria_analitica]", cat_orden="m_ordenes[categoria_orden]",
             ks="m_ordenes[k_symbol]", cred="m_cuentas[tiene_credito_externo]",
             cuenta="m_cuentas[id_cuenta]", cuenta_lbl="m_cuentas[cuenta]", region="m_distritos[region]",
             dist_nombre="m_distritos[nombre_distrito]", cli_nombre="m_clientes[cliente]",
             segmento="m_clientes[segmento_edad]", calificacion="m_clientes[calificacion_pago]",
             recp="m_recomendacion_producto", adp="m_adopcion_producto", cap="m_capacidad_prestamo",
             evalr="m_evaluacion_recomendador", asoc="m_asociacion_producto", regla="m_regla_capacidad", prod="m_dim_producto",
             recp_cta="m_recomendacion_producto[id_cuenta]")
    tablas.append(tabla_medidas(t))
    rels = []
    for f in ["m_prestamos", "m_ordenes", "m_trans_anual", "m_saldo_mensual"]:
        rels += [rel(f, "id_distrito", "m_distritos", "id_distrito"), rel(f, "id_cliente", "m_clientes", "id_cliente"),
                 rel(f, "id_cuenta", "m_cuentas", "id_cuenta")]
    rels += [rel("m_prestamos", "anio", "m_anios", "anio"), rel("m_trans_anual", "anio", "m_anios", "anio"),
             rel("m_saldo_mensual", "fecha_mes", "m_meses", "fecha_mes"), rel("m_meses", "anio", "m_anios", "anio"),
             rel("m_recomendaciones", "id_cuenta", "m_cuentas", "id_cuenta"),
             rel("m_recomendaciones", "id_cliente", "m_clientes", "id_cliente")]
    for f in ["m_recomendacion_producto", "m_adopcion_producto", "m_capacidad_prestamo"]:
        rels += [rel(f, "id_cuenta", "m_cuentas", "id_cuenta"), rel(f, "id_cliente", "m_clientes", "id_cliente"),
                 rel(f, "id_distrito", "m_distritos", "id_distrito")]
    rels += [rel("m_recomendacion_producto", "producto", "m_dim_producto", "producto"),
             rel("m_adopcion_producto", "producto", "m_dim_producto", "producto")]

    script = open(CONECTOR_MONGO, encoding="utf-8").read()
    script_m = script.replace('"', '""').replace("\r\n", "\n").replace("\n", "#(lf)")
    expresiones = [{"name": "MongoFinancial", "kind": "m",
                    "expression": ["let", f'    Origen = Python.Execute("{script_m}")', "in", "    Origen"]}]
    return modelo_base("Dashboard_Financial_Mongo", tablas, rels, expresiones), t


# ==========================================================================
# 2. INFORME (report.json)
# ==========================================================================
def lit(v):
    if isinstance(v, bool):
        return {"expr": {"Literal": {"Value": "true" if v else "false"}}}
    if isinstance(v, (int, float)):
        return {"expr": {"Literal": {"Value": f"{v}D"}}}
    return {"expr": {"Literal": {"Value": "'" + str(v).replace("'", "''") + "'"}}}


def color(hexa):
    return {"solid": {"color": lit(hexa)}}


def vid(*partes):
    return uuid.uuid5(uuid.NAMESPACE_URL, "/".join(map(str, partes))).hex[:20]


X_CONTENIDO = 188                      # a la izquierda, panel fijo de navegación y filtros globales (180 px)
ESCALA_X = (W - X_CONTENIDO - 8) / 1256  # las páginas se diseñan en 12..1268 y se comprimen al área de contenido


class Pagina:
    def __init__(self, nombre, titulo, campos):
        self.nombre = nombre
        self.titulo = titulo
        self.id = "ReportSection" + vid("pagina", nombre)
        self.visuales = []
        self.z = 0
        self.F = campos
        self.crudo = False      # True: coordenadas sin transformar (panel lateral)
        self.filtros = []       # filtros de página (el de drill-through en D1 y D2)

    def _contenedor(self, x, y, w, h, single):
        if not self.crudo:
            x, w = round(X_CONTENIDO + (x - 12) * ESCALA_X), round(w * ESCALA_X)
        self.z += 1
        nombre = vid(self.nombre, self.z, single["visualType"])
        cfg = {"name": nombre, "layouts": [{"id": 0, "position": {"x": x, "y": y, "z": self.z, "width": w, "height": h}}],
               "singleVisual": single}
        self.visuales.append({"x": x, "y": y, "z": self.z, "width": w, "height": h,
                              "config": json.dumps(cfg, ensure_ascii=False), "filters": "[]"})

    def _resolver(self, c):
        if c.startswith("m:"):
            return "_Medidas", c[2:], True
        ent, prop = self.F[c]
        return ent, prop, False

    def ref(self, c):
        ent, prop, _ = self._resolver(c)
        return f"{ent}.{prop}"

    def visual(self, tipo, x, y, w, h, roles, titulo=None, orden=None, objetos=None, extra=None, etiquetas=None,
               titulo_tam=12, titulo_color=TITULO):
        """roles: {rol: [campo, ...]}; campo = clave de self.F o 'm:Nombre medida'.
        etiquetas: {campo: 'Nombre visible'} para encabezados de tablas y leyendas."""
        alias, desde, select, proy = {}, [], [], {}
        for rol, campos in roles.items():
            proy[rol] = []
            for c in campos:
                ent, prop, es_medida = self._resolver(c)
                if ent not in alias:
                    alias[ent] = f"t{len(alias)}"
                    desde.append({"Name": alias[ent], "Entity": ent, "Type": 0})
                ref = f"{ent}.{prop}"
                expr = {"Expression": {"SourceRef": {"Source": alias[ent]}}, "Property": prop}
                if not any(s["Name"] == ref for s in select):
                    select.append({("Measure" if es_medida else "Column"): expr, "Name": ref})
                proy[rol].append({"queryRef": ref, **({"active": True} if rol in ("Category", "Rows", "Group") else {})})
        single = {"visualType": tipo, "projections": proy,
                  "prototypeQuery": {"Version": 2, "From": desde, "Select": select},
                  "drillFilterOtherVisuals": True}
        if orden:
            campo, direccion = orden
            ent, prop, es_medida = self._resolver(campo)
            single["prototypeQuery"]["OrderBy"] = [{"Direction": 2 if direccion == "desc" else 1, "Expression": {
                ("Measure" if es_medida else "Column"): {"Expression": {"SourceRef": {"Source": alias[ent]}},
                                                          "Property": prop}}}]
        if etiquetas:
            single["columnProperties"] = {self.ref(c): {"displayName": e} for c, e in etiquetas.items()}
        if tipo == "tableEx":
            objetos = {"total": [{"properties": {"totals": lit(False)}}], **(objetos or {})}
        if objetos:
            single["objects"] = objetos
        vc = {"background": [{"properties": {"show": lit(True), "color": color(BLANCO)}}],
              "border": [{"properties": {"show": lit(True), "color": color(BORDE), "radius": lit(8)}}]}
        if titulo:
            vc["title"] = [{"properties": {"show": lit(True), "text": lit(titulo), "fontSize": lit(titulo_tam),
                                           "fontColor": color(titulo_color)}}]
        single["vcObjects"] = vc
        if extra:
            single.update(extra)
        self._contenedor(x, y, w, h, single)

    def texto(self, x, y, w, h, texto, tam=12, negrita=False, col=TINTA, fondo=None):
        parrafos = [{"textRuns": [{"value": linea, "textStyle": {"fontSize": f"{tam}pt", "color": col,
                                                                   **({"fontWeight": "bold"} if negrita else {})}}]}
                    for linea in texto.split("\n")]
        single = {"visualType": "textbox", "drillFilterOtherVisuals": True,
                  "objects": {"general": [{"properties": {"paragraphs": parrafos}}]}}
        # Sin fondo explícito Power BI pinta los cuadros de texto en blanco y taparían la banda y el panel
        single["vcObjects"] = {"background": [{"properties": {"show": lit(bool(fondo)), **({"color": color(fondo)} if fondo else {})}}]}
        self._contenedor(x, y, w, h, single)

    def texto_rico(self, x, y, w, h, parrafos, fondo=None, borde=None):
        """parrafos = [[(texto, tamaño, negrita, color, cursiva), ...], ...]: un párrafo por lista de tramos."""
        ps = [{"textRuns": [{"value": t or " ", "textStyle": {"fontSize": f"{tam}pt", "color": col,
                                                             **({"fontWeight": "bold"} if neg else {}),
                                                             **({"fontStyle": "italic"} if cur else {})}}
                            for (t, tam, neg, col, cur) in tramos]} for tramos in parrafos]
        single = {"visualType": "textbox", "drillFilterOtherVisuals": True,
                  "objects": {"general": [{"properties": {"paragraphs": ps}}]}}
        vc = {"background": [{"properties": {"show": lit(bool(fondo)), **({"color": color(fondo)} if fondo else {})}}]}
        if borde:
            vc["border"] = [{"properties": {"show": lit(True), "color": color(borde), "radius": lit(10)}}]
        single["vcObjects"] = vc
        self._contenedor(x, y, w, h, single)

    def boton(self, x, y, w, h, texto, destino=None, tipo="PageNavigation", fondo=TINTA, col_texto=BLANCO, tam=10,
              transparente=False):
        enlace = {"show": lit(True), "type": lit(tipo)}
        if destino:
            enlace["navigationSection"] = lit(destino)
        self._contenedor(x, y, w, h, {
            "visualType": "actionButton", "drillFilterOtherVisuals": True,
            "objects": {
                # "show" es una propiedad general (sin selector); texto, colores y relleno van por estado
                "icon": [{"properties": {"show": lit(False)}},
                         {"properties": {"shapeType": lit("blank")}, "selector": {"id": "default"}}],
                "text": [{"properties": {"show": lit(True)}},
                         {"properties": {"text": lit(texto), "fontColor": color(col_texto), "fontSize": lit(tam),
                                         "bold": lit(True)}, "selector": {"id": "default"}}],
                "fill": [{"properties": {"show": lit(True)}},
                         {"properties": {"fillColor": color(fondo), "transparency": lit(100 if transparente else 0)},
                          "selector": {"id": "default"}}],
                "outline": [{"properties": {"show": lit(fondo == BLANCO and not transparente)}},
                            {"properties": {"lineColor": color(GRIS_BORDE)}, "selector": {"id": "default"}}],
            },
            "vcObjects": {"visualLink": [{"properties": enlace}]}})

    def seccion(self, oculta=False):
        cfg = {"visibility": 1} if oculta else {}
        return {"config": json.dumps(cfg), "displayName": self.nombre, "displayOption": 1,
                "filters": json.dumps(self.filtros, ensure_ascii=False),
                "height": float(H), "name": self.id, "visualContainers": self.visuales, "width": float(W)}


# ---- Objetos de formato reutilizables ----
def colores_series(pagina, colores):
    """Color fijo por medida (serie): {'m:Medida': '#hex'}. En Power BI 2.157 el selector 'metadata'
    colorea líneas; las COLUMNAS lo ignoran y necesitan 'defaultColor' (ver obj_combo)."""
    return [{"properties": {"fill": color(h)}, "selector": {"metadata": pagina.ref(c)}} for c, h in colores.items()]


def colores_categorias(pagina, campo, colores):
    """Color fijo por valor de categoría: estados, bandas, propósito de la orden."""
    ent, prop, _ = pagina._resolver(campo)
    return [{"properties": {"fill": color(h)}, "selector": {"data": [{"scopeId": {"Comparison": {
        "ComparisonKind": 0, "Left": {"Column": {"Expression": {"SourceRef": {"Entity": ent}}, "Property": prop}},
        "Right": {"Literal": {"Value": "'" + v.replace("'", "''") + "'"}}}}}]}} for v, h in colores.items()]


def _medida_expr(medida):
    return {"Measure": {"Expression": {"SourceRef": {"Entity": "_Medidas"}}, "Property": medida}}


def color_por_medida(medida):
    """Formato condicional por valor de campo: la medida devuelve el color (#hex) de cada punto."""
    return [{"properties": {"fill": {"solid": {"color": {"expr": _medida_expr(medida)}}}},
             "selector": {"data": [{"dataViewWildcard": {"matchingOption": 1}}]}}]


def mapa_calor(medida, maximo=ALERTA):
    """Fondo de las celdas de una matriz: degradado blanco -> maximo según la medida (Brewer, secuencial)."""
    regla = {"FillRule": {"Input": _medida_expr(medida), "FillRule": {"linearGradient2": {
        "min": {"color": {"Literal": {"Value": "'#FFFFFF'"}}}, "max": {"color": {"Literal": {"Value": f"'{maximo}'"}}},
        "nullColoringStrategy": {"strategy": {"Literal": {"Value": "'asZero'"}}}}}}}
    return {"values": [{"properties": {"backColor": {"solid": {"color": {"expr": regla}}}},
                        "selector": {"data": [{"dataViewWildcard": {"matchingOption": 1}}], "metadata": f"_Medidas.{medida}"}}]}


ETIQUETAS = [{"properties": {"show": lit(True), "fontSize": lit(10), "color": color(TINTA)}}]
SIN_CUADRICULA = [{"properties": {"gridlineShow": lit(False), "fontSize": lit(10)}}]
LEYENDA_ABAJO = [{"properties": {"show": lit(True), "position": lit("Bottom"), "fontSize": lit(10)}}]
EJE_CATEGORICO = [{"properties": {"axisType": lit("Categorical"), "fontSize": lit(10)}}]


def obj_columnas(p, colores_cat=None, campo_cat=None, serie=GRIS, extra=None):
    o = {"labels": ETIQUETAS, "valueAxis": SIN_CUADRICULA, "categoryAxis": EJE_CATEGORICO,
         "dataPoint": [{"properties": {"defaultColor": color(serie)}}]}
    if colores_cat:
        o["dataPoint"] += colores_categorias(p, campo_cat, colores_cat)
    if extra:
        o.update(extra)
    return o


def obj_combo(p, col_columnas, lineas, eje_secundario, categorias=None, campo_cat=None):
    """Columnas + línea. Columnas con 'defaultColor' (y color por categoría si se pide); líneas con 'metadata'.
    eje_secundario=False: la línea es una referencia en la MISMA escala (promedio del banco)."""
    dp = [{"properties": {"defaultColor": color(col_columnas)}}] + colores_series(p, lineas)
    if categorias:
        dp += colores_categorias(p, campo_cat, categorias)
    # Las referencias (misma escala) no llevan etiqueta: repetir "10.04%" en cada categoría es ruido
    etiquetas = ETIQUETAS + ([] if eje_secundario else
                             [{"properties": {"showSeries": lit(False)}, "selector": {"metadata": p.ref(c)}} for c in lineas])
    return {"labels": etiquetas, "dataPoint": dp, "categoryAxis": EJE_CATEGORICO,
            "valueAxis": [{"properties": {"gridlineShow": lit(False), "secShow": lit(eje_secundario), "fontSize": lit(10)}}],
            "legend": LEYENDA_ABAJO}


# Tarjetas de moneda en millones con 2 decimales ($80.30M) — Guía 07, sección 4.2
UNIDADES = {MONEDA: {"labelDisplayUnits": lit(1000000), "labelPrecision": lit(2)},
            ENTERO: {"labelDisplayUnits": lit(1)}}   # conteos completos: 1,056,320 y no "1 mill."
FORMATOS = {}   # nombre de medida -> formato; lo llena main() desde el modelo


def construir_informe(F, fuente):
    nombres = ["Inicio", "P1 Cosechas", "P2 Regiones", "P3 Liquidez", "P4 Flujo", "P5 Órdenes", "P6 Impago",
               "R1 Qué ofrecer", "R2 Préstamo", "R3 Venta cruzada", "D1 Distrito", "D2 Cliente 360"]
    titulos = [
        "¿Cómo está el banco? — Financial_ijs, corte 31/12/1998",
        "P1 · ¿Cómo evolucionan la cantidad y la tasa de mora por año de otorgamiento?",
        "P2 · ¿Qué regiones y distritos concentran la cartera y la mora?",
        "P3 · ¿Qué proporción del saldo está comprometida en la cartera vigente y cómo evoluciona el saldo?",
        "P4 · ¿Qué operaciones concentran el flujo, cómo varía el saldo promedio y cuántas cuentas caen en sobregiro?",
        "P5 · ¿Qué cuentas comprometen en cuotas y órdenes fijas una parte alta de su saldo, incluidas deudas externas?",
        "P6 · ¿Qué clientes tienen impago histórico y en qué medida la capacidad de pago previa lo anticipa?",
        "R1 · ¿Qué producto ofrecer a cada cliente? — recomendador demográfico (el más preciso del Informe 04)",
        "R2 · ¿A quién prestar y hasta cuánto? — regla de capacidad de pago (cuota / saldo previo)",
        "R3 · ¿Qué más ofrecer? — venta cruzada P(j|i) y descubrimiento con kNN por perfil",
        "D1 · Detalle del distrito", "D2 · Ficha Cliente 360"]
    pags = [Pagina(n, t, F) for n, t in zip(nombres, titulos)]
    ids = {p.nombre: p.id for p in pags}
    Y0 = 148            # inicio del área de gráficos, debajo de la banda superior y de la fila de KPIs
    ALTO = H - Y0 - 8   # 564
    sync = lambda g: {"syncGroup": {"groupName": g, "fieldChanges": True, "filterChanges": True}}
    desplegable = {"data": [{"properties": {"mode": lit("Dropdown")}}],
                   "header": [{"properties": {"show": lit(False)}}],
                   "items": [{"properties": {"fontSize": lit(9)}}]}

    # Filtros globales: se sincronizan en todas las páginas (lo elegido sigue activo al cambiar de página).
    # Los cinco últimos son atributos del cliente, por lo que filtran todos los hechos del proyecto.
    FILTROS = [("anio", "Año"), ("zona", "Zona"), ("segmento", "Edad"),
               ("estado_cli", "Estado del préstamo"), ("banda_cli", "Banda de capacidad"), ("alerta_cli", "Alerta de saturación"),
               ("oferta_cli", "Primera oferta"), ("prestamo_cli", "Préstamo prudente")]

    CORTOS = {"R1 Qué ofrecer": "R1 Ofrecer", "R3 Venta cruzada": "R3 Cruzada"}

    def marco(p):
        """Fondo gris, banda azul con navegación y panel de filtros globales (coordenadas reales del lienzo)."""
        p.crudo = True
        p.texto(0, 0, W, H, " ", 8, False, TINTA, FONDO_PAG)
        p.texto(0, 0, W, 70, " ", 8, False, BLANCO, NAVY)
        p.texto(8, 0, 430, 32, f"Financial_ijs · Dashboard {fuente}", 9, False, "#AFC3DA")
        for k, n in enumerate(nombres[:10]):
            activa = n == p.nombre
            p.boton(444 + k * 83, 6, 80, 24, CORTOS.get(n, n), ids[n], fondo=AMBAR if activa else NAVY_2,
                    col_texto=NAVY if activa else BLANCO, tam=8)
        # Panel de filtros globales: se sincronizan en todas las páginas (lo elegido sigue activo al cambiar de página).
        p.texto(0, 70, 180, H - 70, " ", 8, False, TINTA, PANEL)
        p.texto(4, 72, 172, 30, "Filtros globales", 10, True, NAVY)
        for k, (clave, titulo) in enumerate(FILTROS):
            campos = ["macro", "region", "distrito"] if clave == "zona" else [clave]
            p.visual("slicer", 6, 100 + k * 62, 168, 58, {"Values": campos}, titulo, objetos=desplegable, extra=sync(clave),
                     titulo_tam=10)
        p.texto(6, 598, 168, 118, "Siguen activos en todas las páginas.\nClic derecho en una región, distrito o cliente "
                "→ Obtener detalles.", 8, False, TXT_SUAVE)

    def cabecera(p):
        marco(p)
        p.texto(10, 30, 1260, 38, p.titulo, 14, True, BLANCO)
        p.crudo = False

    def detalle(p, medida_titulo):
        marco(p)
        p.visual("card", 10, 28, 1140, 42, {"Values": ["m:" + medida_titulo]},
                 objetos={"labels": [{"properties": {"fontSize": lit(15), "color": color(BLANCO)}}],
                          "categoryLabels": [{"properties": {"show": lit(False)}}]},
                 extra={"vcObjects": {"background": [{"properties": {"show": lit(False)}}],
                                      "border": [{"properties": {"show": lit(False)}}]}})
        p.boton(1168, 36, 104, 28, "◀ Atrás", tipo="Back", fondo=AMBAR, col_texto=NAVY)
        p.crudo = False

    def kpis(p, lista, y=78, h=62):
        """Cabecera de KPIs (regla 6): tarjeta blanca con barra de color a la izquierda (azul = indicador,
        bermellón = alerta), etiqueta gris arriba y valor grande. lista = [(medida, etiqueta, es_alerta)]."""
        n = len(lista)
        ancho = (1256 - 10 * (n - 1)) / n
        for k, (m, etiqueta, alerta) in enumerate(lista):
            x = round(12 + k * (ancho + 10))
            p.visual("card", x + 6, y, round(ancho) - 6, h, {"Values": ["m:" + m]}, etiqueta, titulo_tam=10, titulo_color=TXT_SUAVE,
                     objetos={"labels": [{"properties": {"fontSize": lit(20 if FORMATOS.get(m) else 13),
                                                         "color": color(ALERTA if alerta else NAVY),
                                                         **UNIDADES.get(FORMATOS.get(m), {})}}],
                              "categoryLabels": [{"properties": {"show": lit(False)}}]})
            p.texto(x, y, 6, h, " ", 8, False, BLANCO, ALERTA if alerta else EST_A)

    def drill(p, campo, nombre):
        """Página de detalle por drill-through: filtro de página (howCreated 5 = Drillthrough) + pod enlazado.
        Sin 'acceptsFilterContext' el pod usa el valor por defecto: MANTENER todos los filtros del origen."""
        ent, prop, _ = p._resolver(campo)
        p.filtros = [{"name": nombre, "expression": {"Column": {"Expression": {"SourceRef": {"Entity": ent}}, "Property": prop}},
                      "type": "Categorical", "howCreated": 5}]
        return {"name": "Pod" + nombre, "boundSection": p.id, "config": "{}", "type": 1,
                "parameters": json.dumps([{"name": "Param" + nombre, "boundFilter": nombre, "asAggregation": False}])}

    # ================= Inicio =================
    p = pags[0]
    cabecera(p)
    kpis(p, [("Tasa Mora Vigente", "Tasa de mora vigente", True),
             ("Tasa Incumplimiento", "Incumplimiento", True),
             ("Cartera Vigente", "Cartera vigente (C + D)", False),
             ("Saldo Neto Corte", "Saldo neto al cierre", False),
             ("Absorcion Vigente", "Absorción vigente", False),
             ("Cuentas en Sobregiro", "Cuentas en sobregiro", True)])
    VERDE = "#009E73"
    tarjetas = [
        ("P1", "¿Sube la tasa de mora cuando se presta más?", "Colocación 101 → 196; tasa estable 12–15% (χ² p = 0.93)"),
        ("P2", "¿Dónde se concentran la cartera y la mora?", "north Moravia 15.8% (12 de 76); north Bohemia 0 de 41"),
        ("P3", "¿Cuánto del saldo respalda la cartera vigente?", "Absorción 40.73%; east Bohemia la más expuesta (51.6%)"),
        ("P4", "¿Qué operaciones mueven el dinero?", "$6,257.86M en 1,056,320 movimientos; sobregiro máx. 43"),
        ("P5", "¿Qué cuentas están saturadas de órdenes?", "47 cuentas con índice > 0.5; la 2335 llega a 2.14"),
        ("P6", "¿La capacidad de pago anticipa el impago?", "Impago 2.9% en la banda Baja → 23.3% en la Alta"),
        ("R1", "¿Qué producto ofrecer a cada cliente?", "Demográfico: acierta 66.0% (popularidad 58.5%)"),
        ("R2", "¿A quién prestar y hasta cuánto?", "1,721 préstamos prudentes con monto máximo; AUC 0.717"),
        ("R3", "¿Qué más ofrecer (venta cruzada)?", "Seguro → Transferencias 99.8%; el kNN suma 2,731 ofertas"),
    ]
    for k, ((cod, pregunta, dato), dest) in enumerate(zip(tarjetas, nombres[1:10])):
        tono = EST_A if cod.startswith("P") else VERDE
        x, y = 12 + (k % 3) * 284, Y0 + (k // 3) * 188
        p.texto_rico(x, y, 276, 180, [[(cod, 20, True, tono, False)], [(pregunta, 11, False, TITULO, False)],
                                      [("", 6, False, TINTA, False)], [(dato, 10, False, TXT_SUAVE, True)],
                                      [("Ir →", 10, True, tono, False)]], fondo=BLANCO, borde=tono)
        p.boton(x, y, 276, 180, "", ids[dest], fondo=BLANCO, transparente=True)
    ruta = [("P2", "north Moravia supera al banco: 15.8% de mora"),
            ("D1", "clic derecho en Karvina: 3 en mora de 15 vigentes"),
            ("D2", "cliente 2823: préstamo D de $541,200, índice 2.14"),
            ("P5", "no es aislado: 47 cuentas en alerta de saturación"),
            ("R2", "a quién sí prestar: 1,721 titulares con monto máximo"),
            ("R1", "qué ofrecerle: pensión, transferencias, tarjeta")]
    panel = [[("Problemas de la Carta v8", 12, True, NAVY, False)],
             [("1 · Impago y mora: ", 10, True, ALERTA, False), ("45 en mora y 31 con deuda; crecen con el volumen.", 10, False, TITULO, False)],
             [("2 · Capacidad de pago: ", 10, True, ALERTA, False), ("la cuota / saldo separa el impago (2.9% → 23.3%).", 10, False, TITULO, False)],
             [("3 · Medición de saldos: ", 10, True, ALERTA, False), ("$197.14M al corte; absorción 40.73%.", 10, False, TITULO, False)],
             [("", 8, False, TINTA, False)],
             [("Ruta de análisis sugerida", 12, True, NAVY, False)]]
    for k, (cod, texto_paso) in enumerate(ruta, start=1):
        panel.append([(f"{k}. {cod}  ", 10, True, EST_A if cod[0] in "PD" else VERDE, False), (texto_paso, 10, False, TITULO, False)])
    p.texto_rico(864, Y0, 404, 556, panel, fondo=BLANCO, borde=BORDE)

    # ================= P1 =================
    p = pags[1]
    cabecera(p)
    kpis(p, [("Num Prestamos", "Préstamos otorgados", False), ("Prestamos en Mora", "Vigentes en mora (D)", True),
             ("Tasa Mora Vigente", "Tasa de mora vigente", True), ("Tasa Incumplimiento", "Tasa de incumplimiento", True)])
    p.visual("lineClusteredColumnComboChart", 12, Y0, 780, ALTO,
             {"Category": ["anio"], "Y": ["m:Num Prestamos"], "Y2": ["m:Tasa Mora Vigente"],
              "Tooltips": ["m:Mora Wilson Inferior", "m:Mora Wilson Superior", "m:Prestamos Vigentes", "m:Prestamos en Mora"]},
             "Se presta el doble (101 → 196) y la tasa de mora de cada cosecha no sube: 12.2%–15.4% (χ² p = 0.93)",
             orden=("anio", "asc"),
             objetos=obj_combo(p, GRIS, {"m:Tasa Mora Vigente": EST_D}, eje_secundario=True),
             etiquetas={"anio": "Año de otorgamiento", "m:Num Prestamos": "Préstamos otorgados",
                        "m:Tasa Mora Vigente": "Tasa de mora de la cosecha"})
    p.visual("pivotTable", 800, Y0, 468, ALTO - 168, {"Rows": ["anio"], "Columns": ["estado"], "Values": ["m:Num Prestamos"]},
             "Todas las combinaciones año × estado", objetos=mapa_calor("Num Prestamos"),
             etiquetas={"anio": "Año", "estado": "Estado"})
    p.texto(800, Y0 + ALTO - 160, 468, 160,
            "Nota de lectura\n1998: préstamos recientes, aún sin tiempo para caer en mora (2.5%).\n"
            "1993: los 20 préstamos ya están cerrados; no tiene tasa vigente.\n"
            "Tooltip de la línea: intervalo de Wilson (z = 1).", 10, False, TINTA, GRIS_FONDO)

    # ================= P2 =================
    p = pags[2]
    cabecera(p)
    kpis(p, [("Region Mayor Mora", "Región con mayor tasa de mora", True),
             ("Distrito Mayor Morosos", "Distrito con más préstamos en mora", True),
             ("Tasa Mora Banco", "Tasa de mora del banco", False),
             ("Cartera Distritos Sobre Mora Banco", "Cartera vigente sobre mora del banco", False)])
    p.visual("decompositionTreeVisual", 12, Y0, 620, 300,
             {"Analyze": ["m:Prestamos en Mora"], "ExplainBy": ["region", "distrito", "cliente"]},
             "Préstamos en mora: región → distrito → cliente")
    p.visual("treemap", 640, Y0, 628, 300,
             # Un solo nivel (distrito): Power BI desactiva el color condicional si el treemap tiene "Detalles"
             {"Group": ["distrito"], "Values": ["m:Cartera Vigente"],
              "Tooltips": ["m:Tasa Mora Vigente", "m:Prestamos Vigentes", "m:Region del Distrito"]},
             "Área = cartera vigente del distrito; color = tasa de mora (más oscuro, más riesgo)",
             objetos={"dataPoint": color_por_medida("Color Mora"), "labels": ETIQUETAS})
    p.visual("lineClusteredColumnComboChart", 12, Y0 + 308, 620, ALTO - 308,
             {"Category": ["region"], "Y": ["m:Tasa Mora Vigente"], "Y2": ["m:Tasa Mora Banco"],
              "Tooltips": ["m:Mora Wilson Inferior", "m:Mora Wilson Superior", "m:Prestamos Vigentes"]},
             "north Moravia tiene la mayor tasa de mora (15.8%, 12 de 76); north Bohemia 0 de 41",
             orden=("m:Tasa Mora Vigente", "desc"),
             objetos=obj_combo(p, EST_D, {"m:Tasa Mora Banco": GRIS}, eje_secundario=False),
             etiquetas={"region": "Región", "m:Tasa Mora Vigente": "Tasa de mora", "m:Tasa Mora Banco": "Banco"})
    p.visual("tableEx", 640, Y0 + 308, 628, ALTO - 308,
             {"Values": ["distrito", "m:Prestamos Vigentes", "m:Prestamos en Mora", "m:Tasa Mora Vigente",
                         "m:Mora Wilson Inferior", "m:Mora Wilson Superior"]},
             "Cada tasa con su n: 70 de 77 distritos tienen menos de 10 vigentes — clic derecho → Obtener detalles",
             orden=("m:Prestamos en Mora", "desc"),
             etiquetas={"distrito": "Distrito", "m:Prestamos Vigentes": "Vigentes (n)", "m:Prestamos en Mora": "En mora",
                        "m:Tasa Mora Vigente": "Tasa", "m:Mora Wilson Inferior": "Wilson inf.",
                        "m:Mora Wilson Superior": "Wilson sup."})

    # ================= P3 =================
    p = pags[3]
    cabecera(p)
    kpis(p, [("Absorcion Vigente", "Absorción vigente", False),
             ("Cartera Vigente Corte", "Cartera vigente", False), ("Saldo Neto Corte", "Saldo neto al cierre", False),
             ("Saldo por Cobrar Estimado", "Saldo por cobrar estimado (C + D)", False)])
    mitad = (ALTO - 8) // 2
    p.visual("lineClusteredColumnComboChart", 12, Y0, 620, ALTO,
             {"Category": ["region"], "Y": ["m:Absorcion Vigente"], "Y2": ["m:Absorcion Banco"],
              "Tooltips": ["m:Cartera Vigente Corte", "m:Saldo Neto Corte Total", "m:Absorcion Cartera Total"]},
             "east Bohemia compromete el 51.6% de su saldo; north Bohemia solo el 28.2% (banco 40.73%)",
             orden=("m:Absorcion Vigente", "desc"),
             objetos=obj_combo(p, EST_A, {"m:Absorcion Banco": GRIS}, eje_secundario=False),
             etiquetas={"region": "Región", "m:Absorcion Vigente": "Absorción vigente", "m:Absorcion Banco": "Banco"})
    p.visual("lineChart", 640, Y0, 628, mitad,
             {"Category": ["fecha_mes"], "Y": ["m:Saldo Promedio por Cuenta"],
              "Tooltips": ["m:Saldo Neto Corte", "m:Cuentas Activas Corte"]},
             "El saldo por cuenta activa, no el total: el total crece sobre todo porque se abren cuentas",
             objetos={"dataPoint": colores_series(p, {"m:Saldo Promedio por Cuenta": EST_A}), "valueAxis": SIN_CUADRICULA},
             etiquetas={"fecha_mes": "Mes", "m:Saldo Promedio por Cuenta": "Saldo promedio por cuenta"})
    p.visual("waterfallChart", 640, Y0 + mitad + 8, 628, mitad,
             {"Category": ["concepto"], "Y": ["m:Valor Composicion Liquidez"]},
             "Saldo neto − cartera vigente = liquidez libre", orden=("concepto", "asc"),
             objetos={"labels": ETIQUETAS, "valueAxis": SIN_CUADRICULA,
                      "sentimentColors": [{"properties": {"increaseFill": color(GRIS), "decreaseFill": color(EST_D),
                                                          "totalFill": color(EST_A)}}]},
             etiquetas={"concepto": "Concepto", "m:Valor Composicion Liquidez": "Monto"})

    # ================= P4 =================
    p = pags[4]
    cabecera(p)
    kpis(p, [("Volumen Transaccionado", "Volumen transaccionado", False), ("Num Transacciones", "Movimientos", False),
             ("Ticket Promedio", "Ticket promedio", False), ("Cuentas en Sobregiro", "Cuentas en sobregiro al cierre", True)])
    p.visual("clusteredColumnChart", 12, Y0, 620, mitad,
             {"Category": ["cat_trans"], "Y": ["m:Ticket Promedio"],
              "Tooltips": ["m:Ticket Limite Inferior", "m:Ticket Limite Superior", "m:EE Ticket", "m:Num Transacciones"]},
             "Ticket promedio por categoría (±1σ en el tooltip, con el error estándar)",
             orden=("m:Ticket Promedio", "desc"), objetos=obj_columnas(p),
             etiquetas={"cat_trans": "Categoría", "m:Ticket Promedio": "Ticket promedio"})
    p.visual("lineChart", 640, Y0, 628, mitad,
             {"Category": ["anio"], "Y": ["m:Volumen Transaccionado"], "Series": ["cat_trans"]},
             "Volumen anual por categoría", orden=("anio", "asc"),
             objetos={"valueAxis": SIN_CUADRICULA, "legend": LEYENDA_ABAJO, "categoryAxis": EJE_CATEGORICO},
             etiquetas={"anio": "Año", "cat_trans": "Categoría", "m:Volumen Transaccionado": "Volumen"})
    p.visual("pivotTable", 12, Y0 + mitad + 8, 620, mitad,
             {"Rows": ["anio"], "Columns": ["cat_trans"], "Values": ["m:Volumen Transaccionado"]},
             "Todas las categorías en todos los años", objetos=mapa_calor("Volumen Transaccionado", EST_A),
             etiquetas={"anio": "Año", "cat_trans": "Categoría"})
    p.visual("lineChart", 640, Y0 + mitad + 8, 628, mitad,
             {"Category": ["fecha_mes"], "Y": ["m:Cuentas en Sobregiro"], "Tooltips": ["m:Cuentas Activas Corte"]},
             "Cuentas en sobregiro al cierre de cada mes: máximo 43 en noviembre de 1998",
             objetos={"dataPoint": colores_series(p, {"m:Cuentas en Sobregiro": ALERTA}), "valueAxis": SIN_CUADRICULA},
             etiquetas={"fecha_mes": "Mes", "m:Cuentas en Sobregiro": "Cuentas en sobregiro"})

    # ================= P5 =================
    p = pags[5]
    cabecera(p)
    kpis(p, [("Compromiso Ordenes", "Compromiso mensual en órdenes", False), ("Num Ordenes", "Órdenes", False),
             ("Cuentas Saturadas", "Cuentas con índice > 0.5", True),
             ("Cuentas con Credito Externo", "Cuentas con crédito externo", True)])
    p.visual("scatterChart", 12, Y0, 780, 320,
             {"Category": ["cliente"], "X": ["m:Saldo Promedio Historico"], "Y": ["m:Compromiso Ordenes"],
              "Tooltips": ["m:Indice Saturacion", "m:Cuenta Ficha"]},
             "Cada punto es un titular: bermellón = sus órdenes superan su saldo promedio (cuenta 2335, índice 2.14)",
             objetos={"dataPoint": color_por_medida("Color Saturacion"), "valueAxis": SIN_CUADRICULA},
             etiquetas={"cliente": "Cliente", "m:Saldo Promedio Historico": "Saldo promedio de la cuenta",
                        "m:Compromiso Ordenes": "Órdenes mensuales"})
    p.visual("donutChart", 800, Y0, 468, 320, {"Category": ["cat_orden"], "Y": ["m:Num Ordenes"]},
             "Órdenes por propósito",
             objetos={"labels": [{"properties": {"show": lit(True), "labelStyle": lit("Category, percent of total")}}],
                      "legend": [{"properties": {"show": lit(False)}}],
                      "dataPoint": colores_categorias(p, "cat_orden", ORDENES)},
             etiquetas={"cat_orden": "Propósito", "m:Num Ordenes": "Órdenes"})
    p.visual("tableEx", 12, Y0 + 328, 1256, ALTO - 328,
             {"Values": ["cliente", "m:Cuenta Alerta", "m:Indice Saturacion Alerta", "m:Compromiso Alerta",
                         "m:Saldo Promedio Alerta", "m:Credito Externo Alerta"]},
             "47 cuentas en alerta (índice > 0.5) — lista para cobranza temprana; clic derecho → Obtener detalles",
             orden=("m:Indice Saturacion Alerta", "desc"),
             etiquetas={"cliente": "Titular", "m:Cuenta Alerta": "Cuenta",
                        "m:Indice Saturacion Alerta": "Índice de saturación", "m:Compromiso Alerta": "Órdenes mensuales",
                        "m:Saldo Promedio Alerta": "Saldo promedio", "m:Credito Externo Alerta": "Crédito externo mensual"})

    # ================= P6 =================
    p = pags[6]
    cabecera(p)
    kpis(p, [("Clientes con Impago", "Clientes con impago (B)", True),
             ("Tasa Impago Banda Baja", "Impago banda Baja", False),
             ("Tasa Impago Banda Alta", "Impago banda Alta", True),
             ("Monto Original en Riesgo", "Monto original en riesgo (B + D)", True)])
    p.visual("lineClusteredColumnComboChart", 12, Y0, 620, 320,
             {"Category": ["banda"], "Y": ["m:Tasa Impago"], "Y2": ["m:Tasa Impago Banco"],
              "Tooltips": ["m:Impago Wilson Inferior", "m:Impago Wilson Superior", "m:Num Prestamos", "m:Prestamos con Impago"]},
             "El impago sube de 2.9% (banda Baja) a 23.3% (banda Alta): χ² = 38.58, p < 0.001",
             orden=("banda", "asc"),
             objetos=obj_combo(p, GRIS, {"m:Tasa Impago Banco": GRIS}, eje_secundario=False, categorias=BANDAS, campo_cat="banda"),
             etiquetas={"banda": "Banda de capacidad (cuota / saldo previo)", "m:Tasa Impago": "Tasa de impago (B o D)",
                        "m:Tasa Impago Banco": "Banco"})
    p.visual("lineClusteredColumnComboChart", 640, Y0, 628, 320,
             {"Category": ["segmento"], "Y": ["m:Tasa Incumplimiento"], "Y2": ["m:Tasa Incumplimiento Banco"],
              "Tooltips": ["m:Incumplimiento Wilson Inferior", "m:Incumplimiento Wilson Superior", "m:Prestamos Cerrados"]},
             "La edad no separa el incumplimiento (χ² = 2.28, p = 0.32): se decide por capacidad, no por perfil",
             orden=("segmento", "asc"),
             objetos=obj_combo(p, GRIS, {"m:Tasa Incumplimiento Banco": TINTA}, eje_secundario=False),
             etiquetas={"segmento": "Segmento de edad", "m:Tasa Incumplimiento": "Tasa de incumplimiento",
                        "m:Tasa Incumplimiento Banco": "Banco"})
    p.visual("tableEx", 12, Y0 + 328, 1256, ALTO - 328,
             {"Values": ["cliente", "m:Distrito Impago", "m:Monto Incumplido", "m:Banda Capacidad Impago"]},
             "Lista de denegación: titulares con préstamo cerrado con deuda (B) — clic derecho → Obtener detalles",
             orden=("m:Monto Incumplido", "desc"),
             etiquetas={"cliente": "Cliente", "m:Distrito Impago": "Distrito", "m:Monto Incumplido": "Monto del préstamo B",
                        "m:Banda Capacidad Impago": "Banda de capacidad"})

    # ================= R1 · Qué ofrecer (demográfico) =================
    p = pags[7]
    cabecera(p)
    kpis(p, [("Clientes con Recomendacion", "Titulares con recomendación", False),
             ("Acierto Elegido", "Acierto del recomendador (Hit@1)", False),
             ("Acierto Popularidad", "Acierto ofreciendo lo más popular", False),
             ("Producto Mas Recomendado", "Primera oferta más frecuente", False)])
    p.visual("clusteredColumnChart", 12, Y0, 620, 300,
             {"Category": ["producto"], "Y": ["m:Cuentas que ya lo Usan", "m:Recomendaciones Demograficas"],
              "Tooltips": ["m:Penetracion Actual", "m:Primera Opcion"]},
             "Dónde crecer: cuentas que ya usan cada producto (gris) y a cuántas se les recomienda (naranja)",
             orden=("producto", "asc"),
             objetos={"labels": ETIQUETAS, "valueAxis": SIN_CUADRICULA, "categoryAxis": EJE_CATEGORICO, "legend": LEYENDA_ABAJO},
             etiquetas={"producto": "Producto", "m:Cuentas que ya lo Usan": "Ya lo usan",
                        "m:Recomendaciones Demograficas": "Recomendado (top 3)"})
    p.visual("pivotTable", 640, Y0, 628, 300, {"Rows": ["arquetipo"], "Columns": ["producto"], "Values": ["m:Primera Opcion"]},
             "Qué ofrecer primero según el perfil del cliente (arquetipo = zona × edad)",
             objetos=mapa_calor("Primera Opcion", EST_A), etiquetas={"arquetipo": "Arquetipo", "producto": "Producto"})
    p.visual("clusteredBarChart", 12, Y0 + 308, 620, ALTO - 308,
             {"Category": ["modelo"], "Y": ["m:Acierto Hit1"],
              "Tooltips": ["m:MRR Modelo", "m:Acierto Cola Larga", "m:MRR Confirmacion"]},
             "Por qué el demográfico: el mayor acierto con el mismo protocolo (azul = sistemas elegidos)",
             orden=("m:Acierto Hit1", "desc"),
             objetos={"labels": ETIQUETAS, "valueAxis": SIN_CUADRICULA, "dataPoint": color_por_medida("Color Modelo")},
             etiquetas={"modelo": "Modelo", "m:Acierto Hit1": "Acierto (Hit@1)"})
    p.visual("tableEx", 640, Y0 + 308, 628, ALTO - 308,
             {"Values": ["cliente", "m:Recomendacion 1", "m:Recomendacion 2", "m:Recomendacion 3", "m:Cuota Maxima Prudente"]},
             "Ofertas por titular — clic derecho en un cliente → Obtener detalles",
             etiquetas={"cliente": "Cliente", "m:Recomendacion 1": "1.ª oferta", "m:Recomendacion 2": "2.ª",
                        "m:Recomendacion 3": "3.ª", "m:Cuota Maxima Prudente": "Cuota préstamo máx."})

    # ================= R2 · Préstamo prudente (regla de capacidad) =================
    p = pags[8]
    cabecera(p)
    kpis(p, [("Titulares sin Prestamo", "Titulares sin préstamo", False),
             ("Prestamos Prudentes Recomendados", "Préstamo recomendado", False),
             ("Cuota Prudente Mediana", "Cuota prudente mediana", False),
             ("Pueden Pagar Prestamo Tipico", "Pueden pagar la cuota típica", True)])
    p.visual("lineClusteredColumnComboChart", 12, Y0, 620, 300,
             {"Category": ["banda"], "Y": ["m:Tasa Impago"], "Y2": ["m:Tasa Impago Banco"],
              "Tooltips": ["m:Impago Wilson Inferior", "m:Impago Wilson Superior", "m:Num Prestamos"]},
             "La regla funciona: impago de 2.9% (banda Baja) a 23.3% (Alta); se ofrece solo la cuota de la banda Baja",
             orden=("banda", "asc"),
             objetos=obj_combo(p, GRIS, {"m:Tasa Impago Banco": GRIS}, eje_secundario=False, categorias=BANDAS, campo_cat="banda"),
             etiquetas={"banda": "Banda de capacidad", "m:Tasa Impago": "Tasa de impago", "m:Tasa Impago Banco": "Banco"})
    p.visual("clusteredColumnChart", 640, Y0, 300, 300, {"Category": ["regla"], "Y": ["m:AUC Regla"]},
             "Qué tan bien anticipa el impago (AUC)", objetos={**obj_columnas(p), "dataPoint": color_por_medida("Color Regla")},
             etiquetas={"regla": "Regla", "m:AUC Regla": "AUC"})
    p.visual("clusteredColumnChart", 948, Y0, 320, 300, {"Category": ["tramo_cap"], "Y": ["m:Titulares sin Prestamo"]},
             "Cuánto se les puede prestar a 36 meses", orden=("tramo_cap", "asc"), objetos=obj_columnas(p, serie=EST_A),
             etiquetas={"tramo_cap": "Monto máximo a 36 meses", "m:Titulares sin Prestamo": "Titulares sin préstamo"})
    p.visual("clusteredColumnChart", 12, Y0 + 308, 620, ALTO - 308,
             {"Category": ["region"], "Y": ["m:Monto Prudente Ofrecible 36m"], "Tooltips": ["m:Prestamos Prudentes Recomendados"]},
             "Monto prudente que se puede colocar por región (préstamos recomendados, 36 meses)",
             orden=("m:Monto Prudente Ofrecible 36m", "desc"), objetos=obj_columnas(p, serie=EST_A),
             etiquetas={"region": "Región", "m:Monto Prudente Ofrecible 36m": "Monto a 36 meses"})
    p.visual("tableEx", 640, Y0 + 308, 628, ALTO - 308,
             {"Values": ["cliente", "m:Saldo Promedio Oferta", "m:Cuota Prudente Oferta", "m:Monto 12m Oferta",
                         "m:Monto 36m Oferta", "m:Monto 60m Oferta"]},
             "A quién ofrecer préstamo y hasta cuánto — clic derecho → Obtener detalles",
             orden=("m:Monto 36m Oferta", "desc"),
             etiquetas={"cliente": "Cliente", "m:Saldo Promedio Oferta": "Saldo promedio", "m:Cuota Prudente Oferta": "Cuota máx.",
                        "m:Monto 12m Oferta": "12 meses", "m:Monto 36m Oferta": "36 meses", "m:Monto 60m Oferta": "60 meses"})

    # ================= R3 · Venta cruzada y descubrimiento =================
    p = pags[9]
    cabecera(p)
    kpis(p, [("Descubrimientos kNN", "Ofertas nuevas que aporta el kNN", False),
             ("Acierto Cola Larga kNN", "Acierto kNN (poco comunes)", False),
             ("Acierto Cola Larga Popularidad", "Popularidad (poco comunes)", False),
             ("Regla Mas Fuerte", "Venta cruzada más fuerte", False)])
    p.visual("pivotTable", 12, Y0, 620, ALTO, {"Rows": ["origen"], "Columns": ["destino"], "Values": ["m:P Destino dado Origen"]},
             "Si ya tiene el producto de la fila, % que también tiene el de la columna — P(j|i)",
             objetos={**mapa_calor("P Destino dado Origen", EST_A),   # sumar porcentajes no tiene sentido: sin totales
                      "subTotals": [{"properties": {"rowSubtotals": lit(False), "columnSubtotals": lit(False)}}]},
             etiquetas={"origen": "Si ya tiene…", "destino": "…también tiene"})
    p.visual("clusteredBarChart", 640, Y0, 628, 290, {"Category": ["producto"], "Y": ["m:Descubrimientos kNN"]},
             "Qué productos descubre el kNN que el demográfico no ofrece", orden=("m:Descubrimientos kNN", "desc"),
             objetos={"labels": ETIQUETAS, "valueAxis": SIN_CUADRICULA, "dataPoint": [{"properties": {"defaultColor": color("#009E73")}}]},
             etiquetas={"producto": "Producto", "m:Descubrimientos kNN": "Ofertas nuevas"})
    p.visual("tableEx", 640, Y0 + 298, 628, ALTO - 298,
             {"Values": ["cliente", "m:Recomendacion 1", "m:Descubrimiento kNN"]},
             "Segunda oferta por titular (kNN por perfil) — clic derecho → Obtener detalles",
             etiquetas={"cliente": "Cliente", "m:Recomendacion 1": "Oferta principal", "m:Descubrimiento kNN": "Además, ofrecer"})

    # ================= D1 =================
    p = pags[10]
    detalle(p, "Titulo Distrito")
    p.visual("multiRowCard", 12, 78, 300, 630,
             {"Values": ["m:Num Prestamos", "m:Prestamos Vigentes", "m:Prestamos en Mora", "m:Tasa Mora Vigente",
                         "m:Cartera Vigente", "m:Saldo Neto Corte", "m:Absorcion Vigente", "m:Poblacion Distrito",
                         "m:Salario Promedio Distrito", "m:Desempleo Distrito 1995", "m:Origen Indicadores"]},
             "Indicadores del distrito",
             etiquetas={"m:Num Prestamos": "Préstamos", "m:Prestamos Vigentes": "Vigentes", "m:Prestamos en Mora": "En mora",
                        "m:Tasa Mora Vigente": "Tasa de mora vigente", "m:Cartera Vigente": "Cartera vigente",
                        "m:Saldo Neto Corte": "Saldo neto al cierre", "m:Absorcion Vigente": "Absorción vigente",
                        "m:Poblacion Distrito": "Población", "m:Salario Promedio Distrito": "Salario promedio",
                        "m:Desempleo Distrito 1995": "Desempleo 1995 (%)", "m:Origen Indicadores": "Indicadores"})
    p.visual("donutChart", 320, 78, 360, 300, {"Category": ["estado"], "Y": ["m:Num Prestamos"]},
             "Préstamos del distrito por estado",
             objetos={"labels": [{"properties": {"show": lit(True), "labelStyle": lit("Category, percent of total")}}],
                      "legend": [{"properties": {"show": lit(False)}}],
                      "dataPoint": colores_categorias(p, "estado", ESTADOS)},
             etiquetas={"estado": "Estado", "m:Num Prestamos": "Préstamos"})
    p.visual("lineChart", 688, 78, 580, 300,
             {"Category": ["fecha_mes"], "Y": ["m:Saldo Promedio por Cuenta", "m:Saldo Promedio Banco"]},
             "Saldo promedio por cuenta: el distrito frente al banco (gris)",
             objetos={"dataPoint": colores_series(p, {"m:Saldo Promedio por Cuenta": EST_A, "m:Saldo Promedio Banco": GRIS}),
                      "valueAxis": SIN_CUADRICULA, "legend": LEYENDA_ABAJO},
             etiquetas={"fecha_mes": "Mes", "m:Saldo Promedio por Cuenta": "Distrito", "m:Saldo Promedio Banco": "Banco"})
    p.visual("tableEx", 320, 386, 948, 322,
             {"Values": ["cliente", "m:Estado Prestamo", "m:Cartera Total", "m:Cuota Mensual", "m:Banda Capacidad"]},
             "Préstamos del distrito — clic derecho en un cliente → Obtener detalles → D2",
             orden=("m:Cartera Total", "desc"),
             etiquetas={"cliente": "Cliente", "m:Estado Prestamo": "Estado", "m:Cartera Total": "Monto",
                        "m:Cuota Mensual": "Cuota", "m:Banda Capacidad": "Banda de capacidad"})

    # ================= D2 =================
    p = pags[11]
    detalle(p, "Titulo Cliente")
    p.visual("multiRowCard", 12, 78, 300, 300,
             {"Values": ["m:Edad Cliente", "m:Segmento Cliente", "m:Arquetipo Cliente", "m:Distrito Cuenta",
                         "m:Calificacion Cliente"]}, "Perfil",
             etiquetas={"m:Edad Cliente": "Edad", "m:Segmento Cliente": "Segmento", "m:Arquetipo Cliente": "Arquetipo",
                        "m:Distrito Cuenta": "Distrito de la cuenta", "m:Calificacion Cliente": "Calificación de pago"})
    p.visual("multiRowCard", 12, 386, 300, 322,
             {"Values": ["m:Estado Prestamo", "m:Cartera Total", "m:Cuota Mensual", "m:Banda Capacidad",
                         "m:Compromiso Ordenes", "m:Indice Saturacion", "m:Credito Externo Mensual"]}, "Situación",
             etiquetas={"m:Estado Prestamo": "Préstamo", "m:Cartera Total": "Monto del préstamo", "m:Cuota Mensual": "Cuota",
                        "m:Banda Capacidad": "Banda de capacidad", "m:Compromiso Ordenes": "Órdenes mensuales",
                        "m:Indice Saturacion": "Índice de saturación", "m:Credito Externo Mensual": "Crédito externo mensual"})
    p.visual("lineChart", 320, 78, 948, 280,
             {"Category": ["fecha_mes"], "Y": ["m:Saldo Neto Corte", "m:Umbral Sobregiro"]},
             "Saldo al cierre de cada mes; bajo la línea gris la cuenta está en sobregiro",
             objetos={"dataPoint": colores_series(p, {"m:Saldo Neto Corte": EST_A, "m:Umbral Sobregiro": GRIS}),
                      "valueAxis": SIN_CUADRICULA, "legend": [{"properties": {"show": lit(False)}}]},
             etiquetas={"fecha_mes": "Mes", "m:Saldo Neto Corte": "Saldo al cierre", "m:Umbral Sobregiro": "Cero"})
    p.visual("tableEx", 320, 366, 440, 342, {"Values": ["cat_orden", "m:Num Ordenes", "m:Compromiso Ordenes"]},
             "Órdenes fijas de la cuenta", orden=("m:Compromiso Ordenes", "desc"),
             etiquetas={"cat_orden": "Propósito", "m:Num Ordenes": "Órdenes", "m:Compromiso Ordenes": "Monto mensual"})
    p.visual("tableEx", 768, 366, 500, 342,
             {"Values": ["rec1", "rec2", "rec3", "m:Cuota Maxima Prudente", "m:Monto Maximo Prudente", "m:Descubrimiento kNN"]},
             "Qué ofrecerle: demográfico (R1), préstamo prudente (R2) y kNN (R3)",
             etiquetas={"rec1": "1.ª oferta", "rec2": "2.ª", "rec3": "3.ª",
                        "m:Cuota Maxima Prudente": "Cuota máx. préstamo",
                        "m:Monto Maximo Prudente": "Monto máx. (36 m)", "m:Descubrimiento kNN": "Además (kNN)"})

    # Clic derecho sobre una región en cualquier gráfico -> Obtener detalles -> cualquier página P1–P6 / R1–R3,
    # con esa región y TODOS los filtros de la página de origen (el filtro de drill-through queda en la página destino).
    pods = [drill(pg, "region", "DrillRegion" + pg.nombre.split()[0]) for pg in pags[1:10]]
    pods += [drill(pags[10], "distrito", "DrillDistrito"), drill(pags[11], "cliente", "DrillCliente")]
    secciones = [pg.seccion(oculta=pg.nombre.startswith("D")) for pg in pags]
    config = {"version": "5.50", "themeCollection": {"baseTheme": {"name": "CY24SU08", "version": "5.55", "type": 2},
                                                     "customTheme": {"name": TEMA_ARCHIVO, "version": "5.55", "type": 1}},
              "activeSectionIndex": 0, "defaultDrillFilterOtherVisuals": True}
    recursos = [{"resourcePackage": {"name": "RegisteredResources", "type": 1, "disabled": False,
                                     "items": [{"type": 202, "path": TEMA_ARCHIVO, "name": TEMA_ARCHIVO}]}}]
    return {"config": json.dumps(config), "layoutOptimization": 0, "resourcePackages": recursos, "sections": secciones,
            "pods": pods}


CAMPOS_KIMBALL = {
    "anio": ("Dim_Anio", "anio"), "macro": ("Dim_Distrito", "Macro Region"), "region": ("Dim_Distrito", "region"),
    "distrito": ("Dim_Distrito", "nombre_distrito"), "estado": ("Dim_Estado_Prestamo", "Estado"),
    "cliente": ("Dim_Cliente", "Cliente"), "cuenta": ("Dim_Cuenta", "Cuenta"), "segmento": ("Dim_Cliente", "segmento_edad"),
    "arquetipo": ("Dim_Cliente", "arquetipo_demografico"),
    "cat_trans": ("vw_PBI_Trans_Anual_Cuenta", "categoria_analitica"), "cat_orden": ("Dim_Orden", "categoria_orden_traducida"),
    "banda": ("Fact_Prestamos", "banda_capacidad"), "fecha_mes": ("Dim_Tiempo", "fecha"),
    "concepto": ("Composicion_Liquidez", "concepto"), "rec1": ("Recomendacion_Cuenta", "recomendacion_1"),
    "rec2": ("Recomendacion_Cuenta", "recomendacion_2"), "rec3": ("Recomendacion_Cuenta", "recomendacion_3"),
    "producto": ("Dim_Producto", "producto"), "modelo": ("Evaluacion_Recomendador", "modelo"),
    "regla": ("Regla_Capacidad", "regla"), "tramo_cap": ("Capacidad_Prestamo", "tramo_monto_36m"),
    "origen": ("Asociacion_Producto", "producto_origen"), "destino": ("Asociacion_Producto", "producto_destino"),
    "estado_cli": ("Dim_Cliente", "Estado del Prestamo"), "banda_cli": ("Dim_Cliente", "Banda de Capacidad"),
    "alerta_cli": ("Dim_Cliente", "Alerta de Saturacion"), "oferta_cli": ("Dim_Cliente", "Primera Oferta"),
    "prestamo_cli": ("Dim_Cliente", "Prestamo Recomendado"),
}
CAMPOS_MONGO = {
    "anio": ("m_anios", "anio"), "macro": ("m_distritos", "macro_region"), "region": ("m_distritos", "region"),
    "distrito": ("m_distritos", "nombre_distrito"), "estado": ("m_prestamos", "estado"),
    "cliente": ("m_clientes", "cliente"), "cuenta": ("m_cuentas", "cuenta"), "segmento": ("m_clientes", "segmento_edad"),
    "arquetipo": ("m_clientes", "arquetipo_demografico"),
    "cat_trans": ("m_trans_anual", "categoria_analitica"), "cat_orden": ("m_ordenes", "categoria_orden"),
    "banda": ("m_prestamos", "banda_capacidad"), "fecha_mes": ("m_meses", "fecha_mes"),
    "concepto": ("Composicion_Liquidez", "concepto"), "rec1": ("m_recomendaciones", "recomendacion_1"),
    "rec2": ("m_recomendaciones", "recomendacion_2"), "rec3": ("m_recomendaciones", "recomendacion_3"),
    "producto": ("m_dim_producto", "producto"), "modelo": ("m_evaluacion_recomendador", "modelo"),
    "regla": ("m_regla_capacidad", "regla"), "tramo_cap": ("m_capacidad_prestamo", "tramo_monto_36m"),
    "origen": ("m_asociacion_producto", "producto_origen"), "destino": ("m_asociacion_producto", "producto_destino"),
    "estado_cli": ("m_clientes", "Estado del Prestamo"), "banda_cli": ("m_clientes", "Banda de Capacidad"),
    "alerta_cli": ("m_clientes", "Alerta de Saturacion"), "oferta_cli": ("m_clientes", "Primera Oferta"),
    "prestamo_cli": ("m_clientes", "Prestamo Recomendado"),
}

# Tema (Guía 07 v4, sección 4): la primera serie es gris (las categorías ya están nombradas en el eje).
# Se incrusta en el informe (StaticResources/RegisteredResources) y se deja una copia junto al .pbip.
TEMA_ARCHIVO = "tema_financial.json"
TEMA = {
    "name": "Financial_ijs Guia 07 v4 (Okabe-Ito)",
    "dataColors": [GRIS, EST_D, EST_A, EST_C, EST_B, "#009E73", "#CC79A7", "#F0E442"],
    "background": FONDO_PAG, "foreground": TINTA, "tableAccent": EST_A,
    "good": EST_A, "neutral": EST_D, "bad": ALERTA,
    "minimum": BLANCO, "center": "#F2B48C", "maximum": ALERTA,
    "textClasses": {
        "title": {"fontFace": "Segoe UI Semibold", "fontSize": 12, "color": TINTA},
        "label": {"fontFace": "Segoe UI", "fontSize": 10, "color": TINTA},
        "callout": {"fontFace": "Segoe UI", "fontSize": 18, "color": TINTA},
    },
}


# ==========================================================================
# 3. ESCRITURA Y VALIDACIÓN
# ==========================================================================
def validar(modelo, informe):
    """Comprueba que cada campo del informe y cada relación/orden existan en el modelo."""
    columnas = {(t["name"], c["name"]) for t in modelo["model"]["tables"] for c in t["columns"]}
    medidas_ = {m["name"] for t in modelo["model"]["tables"] for m in t.get("measures", [])}
    errores = []
    for s in informe["sections"]:
        for vc in s["visualContainers"]:
            sv = json.loads(vc["config"])["singleVisual"]
            for sel in sv.get("prototypeQuery", {}).get("Select", []):
                ent, prop = sel["Name"].split(".", 1)
                if "Measure" in sel and prop not in medidas_:
                    errores.append(f"{s['displayName']}: medida inexistente {prop}")
                if "Column" in sel and (ent, prop) not in columnas:
                    errores.append(f"{s['displayName']}: columna inexistente {ent}.{prop}")
    tablas = {t["name"] for t in modelo["model"]["tables"]}
    for r in modelo["model"]["relationships"]:
        for tb, cl in ((r["fromTable"], r["fromColumn"]), (r["toTable"], r["toColumn"])):
            if (tb, cl) not in columnas:
                errores.append(f"relación con columna inexistente {tb}.{cl}")
            if tb not in tablas:
                errores.append(f"relación con tabla inexistente {tb}")
    secciones = {s["name"] for s in informe["sections"]}
    for pod in informe.get("pods", []):
        if pod["boundSection"] not in secciones:
            errores.append(f"drill-through hacia una página inexistente {pod['boundSection']}")
    for t in modelo["model"]["tables"]:
        for c in t["columns"]:
            if "sortByColumn" in c and (t["name"], c["sortByColumn"]) not in columnas:
                errores.append(f"ordenar por columna inexistente {t['name']}.{c['sortByColumn']}")
    # Cada medida referenciada con [ ] dentro de otra medida debe existir
    import re
    for t in modelo["model"]["tables"]:
        for m in t.get("measures", []):
            for ref in re.findall(r"(?<![\w'\]])\[([^\]]+)\]", m["expression"]):
                if ref not in medidas_:
                    errores.append(f"medida {m['name']}: referencia desconocida [{ref}]")
    return errores


def escribir_dax(t):
    """sql/05_Medidas_DAX_PowerBI.dax: las mismas medidas del modelo Kimball, documentadas."""
    lineas = [
        "/*",
        "==============================================================================",
        "UNIVERSIDAD TÉCNICA DE AMBATO - INTELIGENCIA DE NEGOCIOS",
        "AUTORES: Alison Marcela Cobos Taco / Henry Daniel Lagua Flores",
        "DOCENTE: Ing. Ruben Nogales, Mg.",
        "==============================================================================",
        "ARCHIVO: 05_Medidas_DAX_PowerBI.dax   (Guía 07 v4)",
        "GENERADO POR: scripts/30_generar_powerbi_pbip.py — no editar a mano.",
        "DESCRIPCIÓN: Medidas del modelo Kimball. El modelo MongoDB tiene las mismas",
        "             medidas con los nombres de tabla m_* (mismo generador).",
        "             Las cifras entre paréntesis son los valores de control al corte",
        "             31/12/1998 sin filtros (Informes 09 y 10, Carta v8).",
        "REGLAS: tasas con intervalo de Wilson (z = 1); promedios con ±1σ exacta;",
        "        saldo semiaditivo desde la foto mensual; DIVIDE en lugar de '/';",
        "        CALCULATE + FILTER cuando la condición es una medida (sección 7).",
        "==============================================================================",
        "*/",
        "",
    ]
    for seccion, grupo in medidas(t):
        lineas += ["// " + "=" * 78, f"// {seccion}", "// " + "=" * 78, ""]
        for nombre, expr, fmt, coment in grupo:
            lineas.append(f"// {coment}" + (f"   [formato {fmt}]" if fmt else ""))
            lineas.append(f"'_Medidas'[{nombre}] =")
            lineas.append("    " + expr)
            lineas.append("")
    with open(ARCHIVO_DAX, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lineas))


def escribir(nombre, modelo, informe, leeme):
    carpeta = os.path.join(OUT_DIR, nombre)
    if os.path.isdir(carpeta):
        shutil.rmtree(carpeta)
    ds = os.path.join(carpeta, f"{nombre}.Dataset")
    rp = os.path.join(carpeta, f"{nombre}.Report")
    os.makedirs(ds)
    os.makedirs(rp)

    def guardar(ruta, obj):
        with open(ruta, "w", encoding="utf-8", newline="\n") as f:
            json.dump(obj, f, ensure_ascii=False, indent=2)

    guardar(os.path.join(carpeta, f"{nombre}.pbip"),
            {"version": "1.0", "artifacts": [{"report": {"path": f"{nombre}.Report"}}], "settings": {}})
    guardar(os.path.join(ds, "definition.pbism"), {"version": "1.0"})
    guardar(os.path.join(ds, "model.bim"), modelo)
    guardar(os.path.join(rp, "definition.pbir"),
            {"version": "1.0", "datasetReference": {"byPath": {"path": f"../{nombre}.Dataset"}, "byConnection": None}})
    guardar(os.path.join(rp, "report.json"), informe)
    os.makedirs(os.path.join(rp, "StaticResources", "RegisteredResources"))
    guardar(os.path.join(rp, "StaticResources", "RegisteredResources", TEMA_ARCHIVO), TEMA)
    guardar(os.path.join(carpeta, "tema_financial.json"), TEMA)
    with open(os.path.join(carpeta, "README.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write(leeme)


CONTROL = """
### Cifras de control (sin filtros; deben coincidir en Kimball y MongoDB)
| KPI | Valor |
| :--- | ---: |
| Préstamos / en mora (D) | 682 / 45 |
| Tasa de mora vigente · incumplimiento | 10.04% · 13.25% |
| Cartera vigente · saldo neto al cierre | $80.30M · $197.14M |
| Absorción vigente (ref. cartera total) | 40.73% (52.38%) |
| Cuentas en sobregiro al cierre · cuentas con índice > 0.5 | 39 · 47 |
| Volumen · movimientos | $6.26bn · 1,056,320 |
| Impago banda Baja · Alta | 2.92% · 23.26% |
"""

PASOS_MANUALES = """
### Cómo lo usa el gerente
* **Panel izquierdo (en todas las páginas):** navegación a Inicio, P1–P6 y R1–R3 y 8 filtros sincronizados: Año,
  Zona (macro-región › región › distrito), Edad, Estado del préstamo, Banda de capacidad, Alerta de saturación,
  Primera oferta y Préstamo prudente. Lo que elija sigue activo en TODAS las páginas; los cinco últimos son
  atributos del cliente y filtran todos los hechos (saldos, órdenes, transacciones, recomendaciones).
* **Clic en un gráfico:** filtra los demás gráficos de esa misma página (Power BI no comparte ese filtro entre páginas).
* **Clic derecho en una región → Obtener detalles:** lleva esa región y todos los filtros a cualquier página P1–P6 o R1–R3.
* **Clic derecho en un cliente o distrito → Obtener detalles:** abre la ficha D2 (cliente) o D1 (distrito)
  **con todos los filtros aplicados**; el botón *Atrás* vuelve a la página de origen. D1 y D2 están ocultas en
  las pestañas porque solo tienen sentido para un cliente o distrito concreto.

### Ya configurado desde el código (no hay que tocarlo)
Tema Okabe–Ito incrustado; drill-through de D1 (`{distrito}`) y D2 (`{cliente}`) manteniendo los filtros;
filtros sincronizados; color por tasa de mora en el treemap de P2; semáforo del índice de saturación en la
dispersión de P5; mapas de calor en las matrices de P1, P4, R1 y R3; colores de estados, bandas y modelos.

### Ajustes opcionales en Power BI Desktop (el formato `report.json` no los guarda de forma fiable)
1. **Árbol de descomposición (P2):** clic en **+** → región → distrito → cliente (o *Valor alto* en cada nivel).
2. **Barras de error** (*Análisis → Barras de error*): P1 y P2 → `Mora Wilson Inferior/Superior`;
   P4 → `Ticket Limite Inferior/Superior`; P6 y R2 → `Impago Wilson Inferior/Superior`; P6 edad →
   `Incumplimiento Wilson Inferior/Superior`. Los mismos límites ya aparecen en el tooltip de cada gráfico.
3. **Dispersión (P5):** *Análisis → Sombreado de simetría* = activado.
4. **Múltiplos pequeños (P4):** mover la categoría de *Leyenda* a *Múltiplos pequeños* en el gráfico de volumen.
5. **Tablas:** barras de datos en la tasa de P2; *Mostrar elementos sin datos* en el estado de la matriz de P1.
6. Si algún combinado con referencia ("Banco") muestra un eje secundario: *Formato → Eje Y secundario → Desactivado*.
"""


def main():
    (km, tk), (mm, tm) = modelo_kimball(), modelo_mongo()
    FORMATOS.update({m["name"]: m.get("formatString") for m in km["model"]["tables"][-1]["measures"]})
    ki, mi = construir_informe(CAMPOS_KIMBALL, "Kimball · SQL Server"), construir_informe(CAMPOS_MONGO, "MongoDB")
    for n, mod, inf in (("Kimball", km, ki), ("Mongo", mm, mi)):
        err = validar(mod, inf)
        if err:
            raise SystemExit(f"[{n}] errores de validación:\n  " + "\n  ".join(err))

    escribir("Dashboard_Financial_Kimball", km, ki, f"""# Dashboard_Financial_Kimball (Power BI Project)

Fuente: SQL Server `DM_Financial_Kimball_v2`. Diseño: Guía 07 v4. Generado con `python scripts/30_generar_powerbi_pbip.py`.

### Cómo abrirlo
1. La base debe estar cargada (scripts 31, 34 y 42) y con la vista de `sql/04_Vistas_PowerBI_Kimball.sql`.
2. Doble clic en `Dashboard_Financial_Kimball.pbip` (Power BI Desktop).
3. Si tu servidor no es `(localdb)\\MSSQLLocalDB`: *Transformar datos → Editar parámetros* → `ServidorSQL`.
4. *Inicio → Actualizar* y compara con las cifras de control.
{CONTROL}{PASOS_MANUALES.format(distrito="Dim_Distrito[nombre_distrito]", cliente="Dim_Cliente[Cliente]",
                                 cuenta="Dim_Cuenta[Cuenta]")}""")
    escribir("Dashboard_Financial_Mongo", mm, mi, f"""# Dashboard_Financial_Mongo (Power BI Project)

Fuente: MongoDB `Financial` (localhost:27017) mediante el conector `scripts/26_powerbi_mongo_dashboard.py`,
incrustado en la consulta compartida `MongoFinancial`. Diseño: Guía 07 v4. Generado con `python scripts/30_generar_powerbi_pbip.py`.

### Cómo abrirlo
1. MongoDB en ejecución con la base `Financial` (scripts 35 y 42, o `mongorestore --gzip --archive=Financial_mongo_dump.gz`).
2. **Python de python.org, no el de Microsoft Store.** Power BI Desktop no puede ejecutar el Python de la
   Store (carpeta `WindowsApps`): la actualización falla con *"Acceso denegado"* (comprobado en
   Power BI 2.157). Instala Python 3.12 desde https://www.python.org (o
   `winget install --id Python.Python.3.12 --scope user`) y luego, con ese Python:
   `python -m pip install pandas==3.0.5 pymongo==4.18.1 matplotlib==3.10.7`
   Power BI siempre ejecuta `import matplotlib.pyplot`; en este equipo Windows App Control bloquea la DLL
   `_image` de matplotlib 3.11.2 y deja cargar la 3.10.7 (las versiones fijadas son las probadas).
   Elige la carpeta de ese Python en *Archivo → Opciones → Scripts de Python*
   (`%LOCALAPPDATA%\\Programs\\Python\\Python312`).
3. Doble clic en `Dashboard_Financial_Mongo.pbip` → *Inicio → Actualizar*. Acepta el aviso de privacidad del script.
4. Compara con las cifras de control: deben ser idénticas a las de Kimball.
{CONTROL}{PASOS_MANUALES.format(distrito="m_distritos[nombre_distrito]", cliente="m_clientes[cliente]",
                                 cuenta="m_cuentas[cuenta]")}""")
    escribir_dax(tk)

    for n, mod, inf in (("Kimball", km, ki), ("Mongo", mm, mi)):
        nvis = sum(len(s["visualContainers"]) for s in inf["sections"])
        nmed = len(mod["model"]["tables"][-1]["measures"])
        print(f"[OK] Dashboard_Financial_{n}: {len(mod['model']['tables'])} tablas, "
              f"{len(mod['model']['relationships'])} relaciones, {nmed} medidas, "
              f"{len(inf['sections'])} páginas, {nvis} visuales")
    print(f"[OK] {os.path.relpath(ARCHIVO_DAX, BASE_DIR)} regenerado")


if __name__ == "__main__":
    main()
