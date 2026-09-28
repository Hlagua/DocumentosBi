"""
==============================================================================
UNIVERSIDAD TÉCNICA DE AMBATO - Inteligencia de Negocios
AUTORES: Alison Marcela Cobos Taco / Henry Daniel Lagua Flores
==============================================================================
ARCHIVO: 30_generar_powerbi_pbip.py
DESCRIPCIÓN: Genera los dos proyectos de Power BI Desktop (.pbip) de la guía 07:
               dashboards/Dashboard_Financial_Kimball/  (SQL Server)
               dashboards/Dashboard_Financial_Mongo/    (MongoDB vía Python)
             Cada proyecto incluye:
               * Modelo semántico (model.bim) con consultas M reales, relaciones
                 de la sección 8 de la guía, columnas calculadas y las medidas DAX
                 de la sección 9 (mismos nombres en los dos modelos).
               * Informe (report.json) con las 9 páginas, KPIs de cabecera,
                 gráficos, segmentadores sincronizados y botones de navegación.
               * Tema de colores (tema_financial.json) de la sección 3.
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

W, H = 1280, 720
AZUL, NARANJA, TINTA, GRIS_CLARO = "#1565C0", "#EF6C00", "#0F2A4A", "#E8EEF6"

MONEDA = '"$"#,0'
MONEDA2 = '"$"#,0.00'
PORC = "0.00%"
ENTERO = "#,0"


# ==========================================================================
# 1. MODELO SEMÁNTICO
# ==========================================================================
def col(nombre, tipo="string", fmt=None, oculto=False):
    c = {"name": nombre, "dataType": tipo, "sourceColumn": nombre, "summarizeBy": "none"}
    if fmt:
        c["formatString"] = fmt
    if oculto:
        c["isHidden"] = True
    return c


def col_calc(nombre, expresion, tipo="string"):
    return {"type": "calculated", "name": nombre, "dataType": tipo, "expression": expresion, "summarizeBy": "none"}


M_TIPOS = {"string": "type text", "int64": "Int64.Type", "double": "type number", "dateTime": "type datetime",
           "boolean": "type logical"}


def tabla_sql(nombre, columnas, calculadas=(), origen=None, oculta=False):
    origen = origen or nombre
    lista = ", ".join(f'"{c["name"]}"' for c in columnas)
    tipos = ", ".join(f'{{"{c["name"]}", {M_TIPOS[c["dataType"]]}}}' for c in columnas)
    expr = [
        "let",
        '    Origen = Sql.Database(ServidorSQL, BaseDatosSQL),',
        f'    Tabla = Origen{{[Schema="dbo", Item="{origen}"]}}[Data],',
        f"    Columnas = Table.SelectColumns(Tabla, {{{lista}}}),",
        f"    Tipos = Table.TransformColumnTypes(Columnas, {{{tipos}}})",
        "in",
        "    Tipos",
    ]
    t = {"name": nombre, "columns": list(columnas) + list(calculadas),
         "partitions": [{"name": nombre, "mode": "import", "source": {"type": "m", "expression": expr}}]}
    if oculta:
        t["isHidden"] = True
    return t


def tabla_python(nombre, columnas, calculadas=()):
    tipos = ", ".join(f'{{"{c["name"]}", {M_TIPOS[c["dataType"]]}}}' for c in columnas)
    lista = ", ".join(f'"{c["name"]}"' for c in columnas)
    expr = [
        "let",
        "    Origen = MongoFinancial,",
        f'    Tabla = Origen{{[Name="{nombre}"]}}[Value],',
        f"    Columnas = Table.SelectColumns(Tabla, {{{lista}}}),",
        f"    Tipos = Table.TransformColumnTypes(Columnas, {{{tipos}}})",
        "in",
        "    Tipos",
    ]
    return {"name": nombre, "columns": list(columnas) + list(calculadas),
            "partitions": [{"name": nombre, "mode": "import", "source": {"type": "m", "expression": expr}}]}


def rel(desde, col_desde, hacia, col_hacia, activa=True):
    r = {"name": str(uuid.uuid5(uuid.NAMESPACE_URL, f"{desde}.{col_desde}->{hacia}.{col_hacia}")),
         "fromTable": desde, "fromColumn": col_desde, "toTable": hacia, "toColumn": col_hacia}
    if not activa:
        r["isActive"] = False
    return r


def medidas(t):
    """Medidas de la guía 07 (secciones 9.1, 9.2 y 9.4). `t` traduce nombres de tabla/columna."""
    m = [
        ("Cartera Total", f"SUM({t['prest']}[monto_prestamo])", MONEDA),
        ("Num Prestamos", f"COUNTROWS({t['prest']})", ENTERO),
        ("Prestamos en Mora", f"CALCULATE([Num Prestamos], {t['estado']} = \"D\")", ENTERO),
        ("Prestamos Vigentes", f"CALCULATE([Num Prestamos], {t['estado']} IN {{\"C\", \"D\"}})", ENTERO),
        ("Prestamos Incumplidos", f"CALCULATE([Num Prestamos], {t['estado']} = \"B\")", ENTERO),
        ("Prestamos Cerrados", f"CALCULATE([Num Prestamos], {t['estado']} IN {{\"A\", \"B\"}})", ENTERO),
        ("Tasa Mora Vigente", "DIVIDE([Prestamos en Mora], [Prestamos Vigentes])", PORC),
        ("Tasa Incumplimiento", "DIVIDE([Prestamos Incumplidos], [Prestamos Cerrados])", PORC),
        ("Monto en Riesgo", f"CALCULATE(SUM({t['prest']}[saldo_pendiente_estimado]), {t['estado']} IN {{\"B\", \"D\"}})", MONEDA),
        ("Monto Incumplido", f"CALCULATE([Cartera Total], {t['estado']} = \"B\")", MONEDA),
        ("Monto Promedio Prestamo", f"AVERAGE({t['prest']}[monto_prestamo])", MONEDA),
        ("Desv Est Prestamo", f"STDEV.S({t['prest']}[monto_prestamo])", MONEDA),
        ("Prestamo Limite Superior", "[Monto Promedio Prestamo] + [Desv Est Prestamo]", MONEDA),
        ("Prestamo Limite Inferior", "[Monto Promedio Prestamo] - [Desv Est Prestamo]", MONEDA),
        ("EE Prestamo", "DIVIDE([Desv Est Prestamo], SQRT([Num Prestamos]))", MONEDA),
        ("Cuota Mensual", f"SUM({t['prest']}[pago_mensual])", MONEDA),
        ("Plazo Meses", f"MAX({t['prest']}[plazo_meses])", ENTERO),
        ("Saldo Pendiente", f"SUM({t['prest']}[saldo_pendiente_estimado])", MONEDA),
        ("Distritos con Prestamos", f"DISTINCTCOUNT({t['prest']}[{t['prest_dist']}])", ENTERO),
        ("Clientes con Impago", f"CALCULATE(DISTINCTCOUNT({t['prest']}[{t['prest_cli']}]), {t['estado']} = \"B\")", ENTERO),

        ("Saldo Depositos", f"SUM({t['saldo']}[saldo_final])", MONEDA),
        ("Ratio Absorcion", f"DIVIDE(CALCULATE([Cartera Total], {t['sin_tiempo']}), [Saldo Depositos])", PORC),
        ("Liquidez Libre", f"[Saldo Depositos] - CALCULATE([Cartera Total], {t['sin_tiempo']})", MONEDA),

        ("Volumen Transaccionado", f"SUM({t['trans']}[monto_total])", MONEDA),
        ("Num Transacciones", f"SUM({t['trans']}[num_transacciones])", ENTERO),
        ("Ticket Promedio Transaccion", "DIVIDE([Volumen Transaccionado], [Num Transacciones])", MONEDA2),
        ("Desv Est Transaccion",
         f"VAR n = [Num Transacciones] VAR s = [Volumen Transaccionado] "
         f"VAR sq = SUM({t['trans']}[suma_cuadrados]) RETURN SQRT(DIVIDE(sq - s * s / n, n - 1))", MONEDA2),
        ("Transaccion Limite Superior", "[Ticket Promedio Transaccion] + [Desv Est Transaccion]", MONEDA2),
        ("Transaccion Limite Inferior", "[Ticket Promedio Transaccion] - [Desv Est Transaccion]", MONEDA2),
        ("EE Transaccion", "DIVIDE([Desv Est Transaccion], SQRT([Num Transacciones]))", MONEDA2),
        ("Saldo Promedio Historico",
         f"DIVIDE(SUMX({t['trans']}, {t['trans']}[saldo_promedio] * {t['trans']}[num_transacciones]), [Num Transacciones])",
         MONEDA),

        ("Compromiso Ordenes", f"SUM({t['ord']}[monto_orden])", MONEDA),
        ("Num Ordenes", f"COUNTROWS({t['ord']})", ENTERO),
        ("Indice Saturacion",
         f"DIVIDE([Compromiso Ordenes], CALCULATE([Saldo Promedio Historico], {t['sin_tiempo']}, REMOVEFILTERS({t['op_rf']})))",
         "0.00"),
        ("Indice Saturacion Alerta", "VAR i = [Indice Saturacion] RETURN IF(i > 0.5, i)", "0.00"),
        ("Compromiso Alerta", "IF([Indice Saturacion] > 0.5, [Compromiso Ordenes])", MONEDA),
        ("Saldo Promedio Alerta", "IF([Indice Saturacion] > 0.5, [Saldo Promedio Historico])", MONEDA),
        ("Clientes Saturados", f"COUNTROWS(FILTER(VALUES({t['cli_key']}), [Indice Saturacion] > 0.5))", ENTERO),
        ("Clientes Totales", f"COUNTROWS({t['cli']})", ENTERO),

        ("EE Mora", "SQRT(DIVIDE([Tasa Mora Vigente] * (1 - [Tasa Mora Vigente]), [Prestamos Vigentes]))", PORC),
        ("Mora Limite Superior", "[Tasa Mora Vigente] + [EE Mora]", PORC),
        ("Mora Limite Inferior", "MAX(0, [Tasa Mora Vigente] - [EE Mora])", PORC),
        ("EE Incumplimiento", "SQRT(DIVIDE([Tasa Incumplimiento] * (1 - [Tasa Incumplimiento]), [Prestamos Cerrados]))", PORC),
        ("Incumplimiento Limite Superior", "[Tasa Incumplimiento] + [EE Incumplimiento]", PORC),
        ("Incumplimiento Limite Inferior", "MAX(0, [Tasa Incumplimiento] - [EE Incumplimiento])", PORC),

        ("Pct Ordenes", f"DIVIDE([Num Ordenes], CALCULATE([Num Ordenes], REMOVEFILTERS({t['cat_rf']})))", PORC),
        ("Pct Volumen", f"DIVIDE([Volumen Transaccionado], CALCULATE([Volumen Transaccionado], REMOVEFILTERS({t['op_rf']})))", PORC),
        ("Pct Cartera", f"DIVIDE([Cartera Total], CALCULATE([Cartera Total], REMOVEFILTERS({t['dist']})))", PORC),

        ("Region Mayor Mora",
         f"VAR t = TOPN(1, VALUES({t['region']}), [Tasa Mora Vigente], DESC) "
         f"RETURN MAXX(t, {t['region']}) & \" · \" & FORMAT(MAXX(t, [Tasa Mora Vigente]), \"0.00%\")", None),
        ("Region Mayor Cartera",
         f"VAR t = TOPN(1, VALUES({t['region']}), [Cartera Total], DESC) "
         f"RETURN MAXX(t, {t['region']}) & \" · \" & FORMAT(MAXX(t, [Pct Cartera]), \"0.0%\")", None),
        ("Region Mayor Absorcion",
         f"VAR t = TOPN(1, VALUES({t['region']}), [Ratio Absorcion], DESC) "
         f"RETURN MAXX(t, {t['region']}) & \" · \" & FORMAT(MAXX(t, [Ratio Absorcion]), \"0.00%\")", None),
        ("Operacion Mayor Volumen",
         f"VAR t = TOPN(1, VALUES({t['op']}), [Volumen Transaccionado], DESC) "
         f"RETURN MAXX(t, {t['op']}) & \" · \" & FORMAT(MAXX(t, [Pct Volumen]), \"0.00%\")", None),
        ("Categoria Principal Orden",
         f"VAR t = TOPN(1, VALUES({t['cat']}), [Num Ordenes], DESC) "
         f"RETURN MAXX(t, {t['cat']}) & \" · \" & FORMAT(MAXX(t, [Pct Ordenes]), \"0.00%\")", None),

        ("Titulo Distrito", f"\"Detalle del distrito: \" & SELECTEDVALUE({t['dist_nombre']}, \"(varios)\")", None),
        ("Titulo Cliente", f"\"Ficha 360 · \" & SELECTEDVALUE({t['cli_nombre']}, \"(varios clientes)\")", None),
    ]
    salida = []
    for nombre, expr, fmt in m:
        d = {"name": nombre, "expression": expr}
        if fmt:
            d["formatString"] = fmt
        salida.append(d)
    return salida


def tabla_medidas(lista_medidas):
    return {"name": "_Medidas",
            "columns": [{"name": "Medidas", "dataType": "string", "isHidden": True, "sourceColumn": "Medidas",
                         "summarizeBy": "none"}],
            "partitions": [{"name": "_Medidas", "mode": "import",
                            "source": {"type": "m", "expression": [
                                "let",
                                '    Origen = #table(type table [Medidas = text], {{"Guía 07"}})',
                                "in",
                                "    Origen"]}}],
            "measures": lista_medidas}


def modelo_base(nombre, tablas, relaciones, expresiones):
    return {
        "name": nombre,
        "compatibilityLevel": 1550,
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


MACRO_REGION = ('SWITCH(TRUE(), Dim_Distrito[region] = "Prague", "Praga", '
                'CONTAINSSTRING(Dim_Distrito[region], "Moravia"), "Moravia", "Bohemia")')
SEGMENTO_EDAD = ('SWITCH(TRUE(), Dim_Cliente[edad_corte] <= 25, "Joven (<=25)", '
                 'Dim_Cliente[edad_corte] <= 40, "Adulto joven (26-40)", '
                 'Dim_Cliente[edad_corte] <= 60, "Adulto (41-60)", "Mayor (>60)")')


def modelo_kimball():
    k = "int64"
    tablas = [
        tabla_sql("Dim_Tiempo", [col("sk_tiempo", k, oculto=True), col("fecha", "dateTime"), col("anio", k),
                                 col("mes", k), col("nombre_mes")]),
        {"name": "Dim_Anio", "columns": [col("anio", k)],
         "partitions": [{"name": "Dim_Anio", "mode": "import", "source": {"type": "m", "expression": [
             "let",
             "    Origen = Sql.Database(ServidorSQL, BaseDatosSQL),",
             '    Tiempo = Origen{[Schema="dbo", Item="Dim_Tiempo"]}[Data],',
             '    Anios = Table.Distinct(Table.SelectColumns(Tiempo, {"anio"})),',
             '    Tipos = Table.TransformColumnTypes(Anios, {{"anio", Int64.Type}})',
             "in",
             "    Tipos"]}}]},
        tabla_sql("Dim_Distrito", [col("sk_distrito", k, oculto=True), col("id_distrito_bk", k), col("nombre_distrito"),
                                   col("region"), col("poblacion", k), col("salario_promedio", "double", MONEDA),
                                   col("tasa_desempleo", "double", "0.00"), col("tasa_criminalidad", "double", ENTERO)],
                  [col_calc("Macro Region", MACRO_REGION)]),
        tabla_sql("Dim_Cliente", [col("sk_cliente", k, oculto=True), col("id_cliente_bk", k), col("sexo"),
                                  col("edad_corte", k), col("tipo_disposicion")],
                  [col_calc("Cliente", '"Cliente " & Dim_Cliente[id_cliente_bk]'),
                   col_calc("Segmento Edad", SEGMENTO_EDAD)]),
        tabla_sql("Dim_Cuenta", [col("sk_cuenta", k, oculto=True), col("id_cuenta_bk", k), col("frecuencia_emision_estado")]),
        tabla_sql("Dim_Estado_Prestamo", [col("sk_estado_prestamo", k, oculto=True), col("codigo_estado"),
                                          col("condicion"), col("descripcion")]),
        tabla_sql("Dim_Operacion", [col("sk_operacion", k, oculto=True), col("tipo_operacion_original"),
                                    col("tipo_operacion_traducido"), col("canal")]),
        tabla_sql("Dim_Orden", [col("sk_orden_tipo", k, oculto=True), col("k_symbol_original"),
                                col("categoria_orden_traducida")]),
        tabla_sql("Fact_Prestamos", [col(c, k, oculto=True) for c in
                                     ("sk_prestamo", "sk_tiempo", "sk_cuenta", "sk_cliente", "sk_distrito", "sk_estado_prestamo")]
                  + [col("id_prestamo_bk", k), col("monto_prestamo", "double", MONEDA), col("plazo_meses", k),
                     col("pago_mensual", "double", MONEDA), col("saldo_pendiente_estimado", "double", MONEDA)]),
        tabla_sql("Fact_Ordenes", [col(c, k, oculto=True) for c in
                                   ("sk_orden", "sk_tiempo", "sk_cuenta", "sk_cliente", "sk_distrito", "sk_orden_tipo")]
                  + [col("id_orden_bk", k), col("monto_orden", "double", MONEDA)]),
        tabla_sql("vw_PBI_Trans_Anual_Cuenta", [col(c, k, oculto=True) for c in
                                                ("sk_cuenta", "sk_cliente", "sk_distrito", "sk_operacion")]
                  + [col("anio", k), col("num_transacciones", k), col("monto_total", "double", MONEDA),
                     col("suma_cuadrados", "double", oculto=True), col("saldo_promedio", "double", MONEDA)]),
        tabla_sql("vw_PBI_Saldo_Final_Cuenta", [col(c, k, oculto=True) for c in ("sk_cuenta", "sk_cliente", "sk_distrito")]
                  + [col("fecha_ultimo_movimiento", "dateTime"), col("saldo_final", "double", MONEDA)]),
    ]
    t = dict(prest="Fact_Prestamos", ord="Fact_Ordenes", trans="vw_PBI_Trans_Anual_Cuenta",
             saldo="vw_PBI_Saldo_Final_Cuenta", cli="Dim_Cliente", dist="Dim_Distrito",
             estado="Dim_Estado_Prestamo[codigo_estado]", prest_dist="sk_distrito", prest_cli="sk_cliente",
             sin_tiempo="REMOVEFILTERS(Dim_Anio), REMOVEFILTERS(Dim_Tiempo)", op="Dim_Operacion[tipo_operacion_traducido]",
             op_rf="Dim_Operacion", cat="Dim_Orden[categoria_orden_traducida]", cat_rf="Dim_Orden",
             region="Dim_Distrito[region]", cli_key="Dim_Cliente[sk_cliente]",
             dist_nombre="Dim_Distrito[nombre_distrito]", cli_nombre="Dim_Cliente[Cliente]")
    tablas.append(tabla_medidas(medidas(t)))
    hechos = ["Fact_Prestamos", "Fact_Ordenes", "vw_PBI_Trans_Anual_Cuenta", "vw_PBI_Saldo_Final_Cuenta"]
    rels = []
    for f in hechos:
        rels += [rel(f, "sk_distrito", "Dim_Distrito", "sk_distrito"), rel(f, "sk_cliente", "Dim_Cliente", "sk_cliente"),
                 rel(f, "sk_cuenta", "Dim_Cuenta", "sk_cuenta")]
    rels += [rel("Fact_Prestamos", "sk_estado_prestamo", "Dim_Estado_Prestamo", "sk_estado_prestamo"),
             rel("Fact_Ordenes", "sk_orden_tipo", "Dim_Orden", "sk_orden_tipo"),
             rel("vw_PBI_Trans_Anual_Cuenta", "sk_operacion", "Dim_Operacion", "sk_operacion"),
             rel("Fact_Prestamos", "sk_tiempo", "Dim_Tiempo", "sk_tiempo"),
             rel("Fact_Ordenes", "sk_tiempo", "Dim_Tiempo", "sk_tiempo", activa=False),
             rel("Dim_Tiempo", "anio", "Dim_Anio", "anio"),
             rel("vw_PBI_Trans_Anual_Cuenta", "anio", "Dim_Anio", "anio")]
    expresiones = [
        {"name": "ServidorSQL", "kind": "m",
         "expression": '"(localdb)\\MSSQLLocalDB" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]'},
        {"name": "BaseDatosSQL", "kind": "m",
         "expression": '"DM_Financial_Kimball_v2" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]'},
    ]
    return modelo_base("Dashboard_Financial_Kimball", tablas, rels, expresiones)


def modelo_mongo():
    k, d = "int64", "double"
    tablas = [
        tabla_python("m_distritos", [col("id_distrito", k), col("nombre_distrito"), col("region"), col("poblacion", k),
                                     col("salario_promedio", d, MONEDA), col("tasa_desempleo", d, "0.00"),
                                     col("tasa_criminalidad", d, ENTERO), col("macro_region")]),
        tabla_python("m_clientes", [col("id_cliente", k), col("cliente"), col("sexo"), col("edad_corte", k),
                                    col("segmento_edad"), col("tipo_disposicion"), col("calificacion_pago")]),
        tabla_python("m_anios", [col("anio", k)]),
        tabla_python("m_prestamos", [col("id_prestamo", k), col("id_cuenta", k), col("id_cliente", k, oculto=True),
                                     col("id_distrito", k, oculto=True), col("fecha_otorgamiento", "dateTime"),
                                     col("anio", k), col("monto_prestamo", d, MONEDA), col("plazo_meses", k),
                                     col("pago_mensual", d, MONEDA), col("saldo_pendiente_estimado", d, MONEDA),
                                     col("codigo_estado"), col("condicion"), col("descripcion_estado")]),
        tabla_python("m_ordenes", [col("id_orden", k), col("id_cuenta", k), col("id_cliente", k, oculto=True),
                                   col("id_distrito", k, oculto=True), col("k_symbol"), col("categoria_orden"),
                                   col("monto_orden", d, MONEDA)]),
        tabla_python("m_trans_anual", [col("id_cuenta", k), col("id_cliente", k, oculto=True),
                                       col("id_distrito", k, oculto=True), col("anio", k), col("tipo_operacion"),
                                       col("canal"), col("num_transacciones", k), col("monto_total", d, MONEDA),
                                       col("suma_cuadrados", d, oculto=True), col("saldo_promedio", d, MONEDA)]),
        tabla_python("m_saldo_cuenta", [col("id_cuenta", k), col("id_cliente", k, oculto=True),
                                        col("id_distrito", k, oculto=True), col("fecha_ultimo_movimiento", "dateTime"),
                                        col("saldo_final", d, MONEDA)]),
    ]
    t = dict(prest="m_prestamos", ord="m_ordenes", trans="m_trans_anual", saldo="m_saldo_cuenta", cli="m_clientes",
             dist="m_distritos", estado="m_prestamos[codigo_estado]", prest_dist="id_distrito", prest_cli="id_cliente",
             sin_tiempo="REMOVEFILTERS(m_anios)", op="m_trans_anual[tipo_operacion]", op_rf="m_trans_anual[tipo_operacion]",
             cat="m_ordenes[categoria_orden]", cat_rf="m_ordenes[categoria_orden]", region="m_distritos[region]",
             cli_key="m_clientes[id_cliente]", dist_nombre="m_distritos[nombre_distrito]", cli_nombre="m_clientes[cliente]")
    tablas.append(tabla_medidas(medidas(t)))
    rels = []
    for f in ["m_prestamos", "m_ordenes", "m_trans_anual", "m_saldo_cuenta"]:
        rels += [rel(f, "id_distrito", "m_distritos", "id_distrito"), rel(f, "id_cliente", "m_clientes", "id_cliente")]
    rels += [rel("m_prestamos", "anio", "m_anios", "anio"), rel("m_trans_anual", "anio", "m_anios", "anio")]

    script = open(CONECTOR_MONGO, encoding="utf-8").read()
    script_m = script.replace('"', '""').replace("\r\n", "\n").replace("\n", "#(lf)")
    expresiones = [{"name": "MongoFinancial", "kind": "m",
                    "expression": ["let", f'    Origen = Python.Execute("{script_m}")', "in", "    Origen"]}]
    return modelo_base("Dashboard_Financial_Mongo", tablas, rels, expresiones)


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


class Pagina:
    def __init__(self, nombre, titulo, campos):
        self.nombre = nombre
        self.titulo = titulo
        self.id = "ReportSection" + vid("pagina", nombre)
        self.visuales = []
        self.z = 0
        self.F = campos

    def _contenedor(self, x, y, w, h, single):
        self.z += 1
        nombre = vid(self.nombre, self.z, single["visualType"])
        cfg = {"name": nombre, "layouts": [{"id": 0, "position": {"x": x, "y": y, "z": self.z, "width": w, "height": h}}],
               "singleVisual": single}
        self.visuales.append({"x": x, "y": y, "z": self.z, "width": w, "height": h,
                              "config": json.dumps(cfg, ensure_ascii=False), "filters": "[]"})

    def visual(self, tipo, x, y, w, h, roles, titulo=None, orden=None, objetos=None, extra=None):
        """roles: {rol: [campo, ...]} donde campo es una clave lógica de self.F o 'm:Nombre medida'."""
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
        if objetos:
            single["objects"] = objetos
        vc = {}
        if titulo:
            vc["title"] = [{"properties": {"show": lit(True), "text": lit(titulo), "fontSize": lit(11)}}]
        single["vcObjects"] = {**vc, **{"background": [{"properties": {"show": lit(True), "color": color("#FFFFFF")}}],
                                         "border": [{"properties": {"show": lit(True), "color": color("#E5E7EB")}}]}}
        if extra:
            single.update(extra)
        self._contenedor(x, y, w, h, single)

    def _resolver(self, c):
        if c.startswith("m:"):
            return "_Medidas", c[2:], True
        ent, prop = self.F[c]
        return ent, prop, False

    def texto(self, x, y, w, h, texto, tam=12, negrita=False, col=TINTA):
        parrafos = [{"textRuns": [{"value": linea, "textStyle": {"fontSize": f"{tam}pt", "color": col,
                                                                   **({"fontWeight": "bold"} if negrita else {})}}]}
                    for linea in texto.split("\n")]
        self._contenedor(x, y, w, h, {"visualType": "textbox", "drillFilterOtherVisuals": True,
                                      "objects": {"general": [{"properties": {"paragraphs": parrafos}}]}})

    def boton(self, x, y, w, h, texto, destino=None, tipo="PageNavigation", fondo=AZUL, col_texto="#FFFFFF"):
        enlace = {"show": lit(True), "type": lit(tipo)}
        if destino:
            enlace["navigationSection"] = lit(destino)
        self._contenedor(x, y, w, h, {
            "visualType": "actionButton", "drillFilterOtherVisuals": True,
            "objects": {
                "icon": [{"properties": {"shapeType": lit("blank")}, "selector": {"id": "default"}}],
                "text": [{"properties": {"show": lit(True), "text": lit(texto), "fontColor": color(col_texto),
                                         "fontSize": lit(10)}, "selector": {"id": "default"}}],
                "fill": [{"properties": {"show": lit(True), "fillColor": color(fondo), "transparency": lit(0)},
                          "selector": {"id": "default"}}],
                "outline": [{"properties": {"show": lit(False)}, "selector": {"id": "default"}}],
            },
            "vcObjects": {"visualLink": [{"properties": enlace}]}})

    def seccion(self, oculta=False):
        cfg = {"visibility": 1} if oculta else {}
        return {"config": json.dumps(cfg), "displayName": self.nombre, "displayOption": 1, "filters": "[]",
                "height": float(H), "name": self.id, "visualContainers": self.visuales, "width": float(W)}


def construir_informe(F):
    nombres = ["Inicio", "P1 ¿Cuándo?", "P2 ¿Dónde?", "P3 ¿Cuánto?", "P4 Flujo", "P5 Órdenes", "P6 Impago",
               "D1 Detalle Distrito", "D2 Ficha Cliente 360"]
    titulos = ["¿Cómo está el banco? — Panorama de la Carta de Diseño",
               "P1 · ¿Cómo evoluciona la morosidad activa año a año?",
               "P2 · ¿Qué distritos concentran el mayor riesgo crediticio?",
               "P3 · ¿Qué porcentaje de los depósitos está comprometido en préstamos?",
               "P4 · ¿Qué operaciones mueven más dinero y cómo varía el saldo?",
               "P5 · ¿Qué cuentas tienen órdenes que saturan su saldo?",
               "P6 · ¿A qué clientes no se les deben dar nuevos productos?",
               "Detalle del distrito (drill-through)", "Ficha Cliente 360 (drill-through)"]
    pags = [Pagina(n, t, F) for n, t in zip(nombres, titulos)]
    ids = {p.nombre: p.id for p in pags}

    def cabecera(p, detalle=False):
        p.texto(12, 6, 700 if not detalle else 1000, 38, p.titulo, 15, True)
        if detalle:
            p.boton(1150, 12, 115, 34, "◀ Atrás", tipo="Back", fondo="#34557A")
            return
        x = 12
        for n in nombres[:7]:
            ancho = 86 if n == "Inicio" else 88
            activa = n == p.nombre
            p.boton(x, 48, ancho, 24, n, ids[n], fondo="#F9A825" if activa else "#34557A",
                    col_texto=TINTA if activa else "#FFFFFF")
            x += ancho + 4
        sync = lambda g: {"syncGroup": {"groupName": g, "fieldChanges": True, "filterChanges": True}}
        modo = {"data": [{"properties": {"mode": lit("Dropdown")}}]}
        p.visual("slicer", 890, 8, 185, 58, {"Values": ["anio"]}, "Año", objetos=modo, extra=sync("anio"))
        p.visual("slicer", 1083, 8, 185, 58, {"Values": ["macro"]}, "Macro-región", objetos=modo, extra=sync("macro"))

    def kpis(p, lista, y=80, h=78):
        n = len(lista)
        ancho = (W - 24 - 8 * (n - 1)) / n
        for i, m in enumerate(lista):
            p.visual("card", round(12 + i * (ancho + 8)), y, round(ancho), h, {"Values": ["m:" + m]})

    etiquetas = {"labels": [{"properties": {"show": lit(True)}}]}
    dona = {"labels": [{"properties": {"show": lit(True), "labelStyle": lit("Category, percent of total")}}],
            "legend": [{"properties": {"show": lit(True), "position": lit("Bottom")}}]}

    # ---- 0 Inicio
    p = pags[0]
    cabecera(p)
    kpis(p, ["Cartera Total", "Saldo Depositos", "Ratio Absorcion", "Tasa Mora Vigente", "Tasa Incumplimiento",
             "Volumen Transaccionado"])
    preguntas = ["P1 · ¿Cómo evoluciona la morosidad año a año?", "P2 · ¿Qué distritos concentran el mayor riesgo?",
                 "P3 · ¿Qué % de los depósitos está prestado?", "P4 · ¿Qué operaciones mueven más dinero?",
                 "P5 · ¿Qué cuentas tienen órdenes que saturan su saldo?", "P6 · ¿A quién no darle nuevos productos?"]
    for i, (txt, dest) in enumerate(zip(preguntas, nombres[1:7])):
        p.boton(12 + (i % 2) * 418, 178 + (i // 2) * 176, 410, 166, txt, ids[dest], fondo="#FFFFFF", col_texto=AZUL)
    p.texto(850, 178, 418, 520,
            "Ruta de análisis\n\n"
            "1. P1 ¿Cuándo? 23 morosos en 1997; la tasa por año es estable (χ² p = 0.93).\n"
            "2. P2 ¿Dónde? north Moravia: 12 de 45 morosos (15.79%).\n"
            "3. D1 Distrito: Karvina, 3 en mora de 15 vigentes.\n"
            "4. D2 Cliente 2823: $541,200 a 60 meses, estado D.\n"
            "5. ¿Qué más tiene? 4 órdenes = $14,286/mes; saldo final −$2,803.\n"
            "6. P5 ¿Es aislado? Índice de saturación 2.14: único > 1 de 47.", 11)

    # ---- P1
    p = pags[1]
    cabecera(p)
    kpis(p, ["Num Prestamos", "Prestamos en Mora", "Tasa Mora Vigente", "Prestamos Incumplidos", "Tasa Incumplimiento"])
    p.visual("lineChart", 12, 166, 624, 280, {"Category": ["anio"], "Y": ["m:Num Prestamos"], "Series": ["estado"]},
             "Los morosos (D) pasan de 2 a 23 mientras la colocación se duplica", objetos=etiquetas)
    p.visual("lineChart", 644, 166, 624, 280, {"Category": ["anio"], "Y": ["m:Tasa Mora Vigente"]},
             "La tasa de mora por año es estable (12–15%); 1998 aún es reciente", objetos=etiquetas)
    p.visual("pivotTable", 12, 454, 900, 256, {"Rows": ["anio"], "Columns": ["estado"], "Values": ["m:Num Prestamos"]},
             "Matriz Año × Estado — todas las categorías, todos los años")
    p.boton(920, 640, 348, 70, "Ver dónde ocurre →", ids["P2 ¿Dónde?"])

    # ---- P2
    p = pags[2]
    cabecera(p)
    kpis(p, ["Region Mayor Mora", "Region Mayor Cartera", "Monto en Riesgo", "Distritos con Prestamos"])
    p.visual("treemap", 12, 166, 620, 544, {"Group": ["region"], "Details": ["distrito"], "Values": ["m:Cartera Total"]},
             "Treemap: área = cartera por región y distrito")
    p.visual("clusteredColumnChart", 640, 166, 628, 272, {"Category": ["region"], "Y": ["m:Tasa Mora Vigente"]},
             "north Moravia tiene la mayor tasa de mora (±1 EE)", orden=("m:Tasa Mora Vigente", "desc"), objetos=etiquetas)
    p.visual("clusteredColumnChart", 640, 446, 310, 264, {"Category": ["macro"], "Y": ["m:Monto Promedio Prestamo"]},
             "Monto promedio por macro-región (±1σ)", objetos=etiquetas)
    p.visual("clusteredColumnChart", 958, 446, 310, 264, {"Category": ["distrito"], "Y": ["m:Prestamos en Mora"]},
             "Distritos con más préstamos en mora", orden=("m:Prestamos en Mora", "desc"), objetos=etiquetas)

    # ---- P3
    p = pags[3]
    cabecera(p)
    kpis(p, ["Cartera Total", "Saldo Depositos", "Ratio Absorcion", "Region Mayor Absorcion"])
    p.visual("clusteredColumnChart", 12, 166, 480, 544,
             {"Category": ["macro"], "Y": ["m:Cartera Total", "m:Saldo Depositos"]},
             "La cartera es poco más de la mitad de los depósitos", objetos=etiquetas)
    p.visual("clusteredColumnChart", 500, 166, 768, 272, {"Category": ["region"], "Y": ["m:Ratio Absorcion"]},
             "Ratio de absorción por región (referencia: 52.38%)", orden=("m:Ratio Absorcion", "desc"), objetos=etiquetas)
    p.visual("clusteredColumnChart", 500, 446, 768, 264, {"Category": ["distrito"], "Y": ["m:Ratio Absorcion"]},
             "Distritos con mayor presión de liquidez", orden=("m:Ratio Absorcion", "desc"))

    # ---- P4
    p = pags[4]
    cabecera(p)
    kpis(p, ["Volumen Transaccionado", "Num Transacciones", "Ticket Promedio Transaccion", "Operacion Mayor Volumen"])
    p.visual("clusteredColumnChart", 12, 166, 412, 272, {"Category": ["operacion"], "Y": ["m:Volumen Transaccionado"]},
             "Volumen por tipo de operación", orden=("m:Volumen Transaccionado", "desc"), objetos=etiquetas)
    p.visual("clusteredColumnChart", 432, 166, 412, 272, {"Category": ["operacion"], "Y": ["m:Ticket Promedio Transaccion"]},
             "Ticket promedio por operación (±1σ)", objetos=etiquetas)
    p.visual("lineChart", 852, 166, 416, 272, {"Category": ["anio"], "Y": ["m:Volumen Transaccionado"],
                                               "Series": ["operacion"]}, "Todas las operaciones crecen cada año")
    p.visual("pivotTable", 12, 446, 620, 264, {"Rows": ["anio"], "Columns": ["operacion"],
                                               "Values": ["m:Volumen Transaccionado"]},
             "Matriz Año × Operación — todas las categorías, todos los años")
    p.visual("lineChart", 640, 446, 300, 264, {"Category": ["anio"], "Y": ["m:Saldo Promedio Historico"]},
             "Cómo varía el balance promedio", objetos=etiquetas)
    p.visual("tableEx", 948, 446, 320, 264, {"Values": ["cliente", "m:Volumen Transaccionado", "m:Num Transacciones"]},
             "Clientes con mayor volumen", orden=("m:Volumen Transaccionado", "desc"))

    # ---- P5
    p = pags[5]
    cabecera(p)
    kpis(p, ["Num Ordenes", "Compromiso Ordenes", "Categoria Principal Orden", "Clientes Saturados"])
    p.visual("donutChart", 12, 166, 400, 544, {"Category": ["categoria"], "Y": ["m:Num Ordenes"]},
             "Órdenes por categoría (%)", objetos=dona)
    p.visual("clusteredColumnChart", 420, 166, 848, 272, {"Category": ["categoria"], "Y": ["m:Compromiso Ordenes"]},
             "Servicios del hogar comprometen $13.97M al mes", orden=("m:Compromiso Ordenes", "desc"), objetos=etiquetas)
    p.visual("tableEx", 420, 446, 848, 264, {"Values": ["cliente", "distrito", "m:Compromiso Alerta",
                                                        "m:Saldo Promedio Alerta", "m:Indice Saturacion Alerta"]},
             "Cuentas en alerta (índice de saturación > 0.5) — clic derecho → Obtener detalles",
             orden=("m:Indice Saturacion Alerta", "desc"))

    # ---- P6
    p = pags[6]
    cabecera(p)
    kpis(p, ["Clientes con Impago", "Tasa Incumplimiento", "Monto en Riesgo", "Prestamos Cerrados"])
    p.visual("tableEx", 12, 166, 620, 544, {"Values": ["cliente", "distrito", "m:Monto Incumplido", "m:Cuota Mensual"]},
             "Lista de denegación: clientes con préstamo en estado B", orden=("m:Monto Incumplido", "desc"))
    p.visual("clusteredColumnChart", 640, 166, 628, 272, {"Category": ["segmento"], "Y": ["m:Tasa Incumplimiento"]},
             "La edad no predice el impago (±1 EE; χ² p = 0.64)", objetos=etiquetas)
    p.visual("clusteredColumnChart", 640, 446, 628, 264, {"Category": ["region"], "Y": ["m:Prestamos Incumplidos"]},
             "Incumplidos por región", orden=("m:Prestamos Incumplidos", "desc"), objetos=etiquetas)

    # ---- D1
    p = pags[7]
    cabecera(p, detalle=True)
    p.visual("card", 12, 56, 700, 40, {"Values": ["m:Titulo Distrito"]})
    kpis(p, ["Num Prestamos", "Prestamos en Mora", "Tasa Mora Vigente", "Cartera Total", "Ratio Absorcion"], y=100)
    p.visual("donutChart", 12, 186, 380, 524, {"Category": ["estado"], "Y": ["m:Num Prestamos"]},
             "Estado de los préstamos del distrito (%)", objetos=dona)
    p.visual("lineChart", 400, 186, 868, 250, {"Category": ["anio"], "Y": ["m:Num Prestamos", "m:Prestamos en Mora"]},
             "Préstamos otorgados y en mora por año", objetos=etiquetas)
    p.visual("tableEx", 400, 444, 868, 266, {"Values": ["cliente", "id_prestamo", "estado", "m:Cartera Total",
                                                        "m:Cuota Mensual", "m:Plazo Meses"]},
             "Préstamos del distrito — clic derecho en un cliente → Obtener detalles",
             orden=("m:Cartera Total", "desc"))

    # ---- D2
    p = pags[8]
    cabecera(p, detalle=True)
    p.visual("card", 12, 56, 700, 40, {"Values": ["m:Titulo Cliente"]})
    kpis(p, ["Cartera Total", "Cuota Mensual", "Compromiso Ordenes", "Indice Saturacion", "Saldo Depositos"], y=100)
    p.visual("tableEx", 12, 186, 300, 524, {"Values": ["cliente", "sexo", "edad", "segmento"]}, "Perfil")
    p.visual("clusteredColumnChart", 320, 186, 470, 262, {"Category": ["categoria"], "Y": ["m:Compromiso Ordenes"]},
             "Órdenes fijas del cliente", orden=("m:Compromiso Ordenes", "desc"), objetos=etiquetas)
    p.visual("lineChart", 798, 186, 470, 262, {"Category": ["anio"], "Y": ["m:Saldo Promedio Historico"]},
             "Saldo promedio por año", objetos=etiquetas)
    p.visual("clusteredColumnChart", 320, 456, 948, 254, {"Category": ["operacion"], "Y": ["m:Volumen Transaccionado"]},
             "Movimientos de su cuenta por tipo de operación", objetos=etiquetas)

    secciones = [pg.seccion() for pg in pags]
    config = {"version": "5.50", "themeCollection": {"baseTheme": {"name": "CY24SU08", "version": "5.55", "type": 2}},
              "activeSectionIndex": 0, "defaultDrillFilterOtherVisuals": True}
    return {"config": json.dumps(config), "layoutOptimization": 0, "sections": secciones}


CAMPOS_KIMBALL = {
    "anio": ("Dim_Anio", "anio"), "macro": ("Dim_Distrito", "Macro Region"), "region": ("Dim_Distrito", "region"),
    "distrito": ("Dim_Distrito", "nombre_distrito"), "estado": ("Dim_Estado_Prestamo", "codigo_estado"),
    "cliente": ("Dim_Cliente", "Cliente"), "segmento": ("Dim_Cliente", "Segmento Edad"), "sexo": ("Dim_Cliente", "sexo"),
    "edad": ("Dim_Cliente", "edad_corte"), "operacion": ("Dim_Operacion", "tipo_operacion_traducido"),
    "categoria": ("Dim_Orden", "categoria_orden_traducida"), "id_prestamo": ("Fact_Prestamos", "id_prestamo_bk"),
}
CAMPOS_MONGO = {
    "anio": ("m_anios", "anio"), "macro": ("m_distritos", "macro_region"), "region": ("m_distritos", "region"),
    "distrito": ("m_distritos", "nombre_distrito"), "estado": ("m_prestamos", "codigo_estado"),
    "cliente": ("m_clientes", "cliente"), "segmento": ("m_clientes", "segmento_edad"), "sexo": ("m_clientes", "sexo"),
    "edad": ("m_clientes", "edad_corte"), "operacion": ("m_trans_anual", "tipo_operacion"),
    "categoria": ("m_ordenes", "categoria_orden"), "id_prestamo": ("m_prestamos", "id_prestamo"),
}

TEMA = {
    "name": "Financial_ijs Guia 07",
    "dataColors": ["#1565C0", "#00897B", "#F9A825", "#5E35B1", "#EF6C00", "#8E1B1B", "#2E7D32", "#90A4AE"],
    "background": "#F3F4F6", "foreground": TINTA, "tableAccent": AZUL,
    "good": "#2E7D32", "neutral": "#F9A825", "bad": NARANJA,
}


# ==========================================================================
# 3. ESCRITURA Y VALIDACIÓN
# ==========================================================================
def validar(modelo, informe):
    """Comprueba que cada campo usado en el informe exista en el modelo."""
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
    return errores


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
    guardar(os.path.join(carpeta, "tema_financial.json"), TEMA)
    with open(os.path.join(carpeta, "README.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write(leeme)


PASOS_MANUALES = """
### Ajustes finales en Power BI Desktop (≈ 5 minutos)
Estos pasos no se pueden guardar de forma fiable en el archivo del proyecto; hazlos una vez y guarda (Ctrl+S):
1. **Drill-through:** en la página *D1 Detalle Distrito*, arrastra `{distrito}` al campo *Obtener detalles* del panel
   Visualizaciones. En *D2 Ficha Cliente 360*, arrastra `{cliente}`. Después, clic derecho en cada pestaña D1/D2 → *Ocultar página*.
2. **Barras de error** (panel *Análisis* de cada gráfico → *Barras de error* → límites superior/inferior):
   - P1 y P2 tasa de mora → `Mora Limite Superior` / `Mora Limite Inferior`
   - P2 monto promedio → `Prestamo Limite Superior` / `Prestamo Limite Inferior`
   - P4 ticket promedio → `Transaccion Limite Superior` / `Transaccion Limite Inferior`
   - P6 incumplimiento por edad → `Incumplimiento Limite Superior` / `Incumplimiento Limite Inferior`
3. **Tema de colores:** *Vista → Temas → Buscar temas* → `tema_financial.json` (esta carpeta).
4. **Treemap (P2):** *Formato → Colores → fx* → degradado por `Tasa Mora Vigente` (blanco → naranja).
5. **Top 10 (P2, P3):** en el gráfico de distritos, panel *Filtros* → `{distrito}` → *N superior* = 10 por la medida del eje Y.
6. **Línea de referencia (P3):** *Análisis → Línea constante* = 0.5238 en el ratio de absorción por región.
"""


def main():
    km, mm = modelo_kimball(), modelo_mongo()
    ki, mi = construir_informe(CAMPOS_KIMBALL), construir_informe(CAMPOS_MONGO)
    for n, mod, inf in (("Kimball", km, ki), ("Mongo", mm, mi)):
        err = validar(mod, inf)
        if err:
            raise SystemExit(f"[{n}] errores de validación:\n  " + "\n  ".join(err))

    escribir("Dashboard_Financial_Kimball", km, ki, f"""# Dashboard_Financial_Kimball (Power BI Project)

Fuente: SQL Server `DM_Financial_Kimball_v2`. Generado con `python scripts/30_generar_powerbi_pbip.py`.

### Cómo abrirlo
1. Ejecuta antes `sql/04_Vistas_PowerBI_Kimball.sql` en la base (crea las 2 vistas del modelo).
2. Doble clic en `Dashboard_Financial_Kimball.pbip` (Power BI Desktop).
3. Si tu servidor no es `(localdb)\\MSSQLLocalDB`: *Transformar datos → Editar parámetros* → `ServidorSQL`.
4. *Inicio → Actualizar*. Comprueba las cifras de control de la guía 07 (sección 9.3).
{PASOS_MANUALES.format(distrito="Dim_Distrito[nombre_distrito]", cliente="Dim_Cliente[Cliente]")}""")
    escribir("Dashboard_Financial_Mongo", mm, mi, f"""# Dashboard_Financial_Mongo (Power BI Project)

Fuente: MongoDB `Financial` (localhost:27017) mediante el conector `scripts/26_powerbi_mongo_dashboard.py`,
incrustado en la consulta compartida `MongoFinancial`. Generado con `python scripts/30_generar_powerbi_pbip.py`.

### Cómo abrirlo
1. MongoDB en ejecución con la base `Financial` cargada (script 22/23 o `Financial_mongo_dump.gz`).
2. *Archivo → Opciones → Scripts de Python*: selecciona el Python que tiene `pymongo` y `pandas`.
3. Doble clic en `Dashboard_Financial_Mongo.pbip` → *Inicio → Actualizar*. Acepta el aviso de privacidad del script de Python.
4. Comprueba las cifras de control de la guía 07 (sección 9.3): deben ser idénticas a las de Kimball.
{PASOS_MANUALES.format(distrito="m_distritos[nombre_distrito]", cliente="m_clientes[cliente]")}""")

    for n, mod, inf in (("Kimball", km, ki), ("Mongo", mm, mi)):
        nvis = sum(len(s["visualContainers"]) for s in inf["sections"])
        nmed = len(mod["model"]["tables"][-1]["measures"])
        print(f"[OK] Dashboard_Financial_{n}: {len(mod['model']['tables'])} tablas, "
              f"{len(mod['model']['relationships'])} relaciones, {nmed} medidas, "
              f"{len(inf['sections'])} páginas, {nvis} visuales")


if __name__ == "__main__":
    main()
