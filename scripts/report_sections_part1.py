# -*- coding: utf-8 -*-
"""
Módulo Parte 1: Portada, Objetivos, Metodología, Equipos, Actividades,
Punto 1 (DataFrames desde DataMart), Punto 2 (Organizar), Punto 3 (Clasificar) y Punto 4 (Filtrar).
Alineado estrictamente con la consigna docente de Inteligencia de Negocios.
"""
from docx.shared import Inches, Pt
from helpers_informe_4 import (
    add_heading, add_paragraph, add_bullet, add_numbered,
    add_checkbox, add_block_math, add_table
)

def build_part1(doc):
    # =========================================================================
    # I. PORTADA INSTITUCIONAL
    # =========================================================================
    add_heading(doc, 1, "INFORME DE GUÍA PRÁCTICA")
    add_heading(doc, 2, "I. PORTADA")
    
    portada_headers = ["Campo Institucional", "Detalle de la Práctica"]
    portada_rows = [
        ["Tema:", "Tomando como base los datos que están siendo tratados genere al menos un sistema de recomendación de cada uno de los algoritmos revisados en clases (Financial_ijs):\n\n"
                 "Utilizando los datos con los que se encuentra trabajando genere:\n"
                 "1. Uno o varios dataframe a partir de un datamart\n"
                 "2. Organizar\n"
                 "3. Clasificar\n"
                 "4. Filtrar la información\n"
                 "5. Generar un sistema de recomendación Slope One\n"
                 "6. Modele productos, comportamientos, perfiles\n"
                 "7. Sistema de recomendación item to item (similitud de cosenos y Pearson)\n"
                 "8. Sistema de recomendación basado en contenidos"],
        ["Unidad de Organización Curricular:", "Unidad Profesional"],
        ["Nivel y Paralelo:", "Sexto Semestre – Software \"A\""],
        ["Alumnos participantes:", "Cobos Taco Alison Marcela\nLagua Flores Henry Daniel"],
        ["Asignatura:", "Inteligencia de Negocios"],
        ["Docente:", "Ing. Rubén Nogales, Mg."]
    ]
    add_table(doc, "", portada_headers, portada_rows, [Inches(2.2), Inches(3.91)])
    
    # =========================================================================
    # II. INFORME DE GUÍA PRÁCTICA
    # =========================================================================
    add_heading(doc, 2, "II. INFORME DE GUÍA PRÁCTICA")
    
    # 2.1 Objetivos
    add_heading(doc, 3, "2.1 Objetivos")
    add_heading(doc, 4, "General:")
    add_paragraph(doc, "Tomando como base los datos que están siendo tratados de la entidad bancaria Financial_ijs (PKDD'99 Financial Discovery Challenge), generar al menos un sistema de recomendación de cada uno de los algoritmos revisados en clases, modelando DataFrames desde un DataMart, organizando, clasificando y filtrando la información, generando un sistema de recomendación Slope One, modelando productos, comportamientos y perfiles, implementando sistemas ítem a ítem (similitud de cosenos y Pearson) y sistemas basados en contenidos y utilidades financieras, evaluando exhaustivamente sus métricas predictivas, ranking Top-N y viabilidad matemática.")
    
    add_heading(doc, 4, "Específicos:")
    add_numbered(doc, 1, "Generar y estructurar cuatro DataFrames limpios a partir del DataMart bancario de Ralph Kimball (df_transacciones, df_ordenes, df_prestamos y df_cliente_consolidado), resolviendo inconsistencias de grano y auditando las claves foráneas.", "Objetivo Específico 1 (Puntos 1 y 2):")
    add_numbered(doc, 2, "Organizar, clasificar y filtrar la información operativa aplicando taxonomías funcionales de servicios, arquetipos demográficos, estabilización logarítmica de Pareto y compuertas prudenciales de solvencia crediticia.", "Objetivo Específico 2 (Puntos 2, 3 y 4):")
    add_numbered(doc, 3, "Generar e implementar el algoritmo de recomendación Slope One con su formulación matemática rigurosa, matriz de desviaciones medias y soportes conjuntos, trazabilidad manual paso a paso con clientes reales (#2 y #45), validación cruzada 5-fold (MAE, RMSE) y evaluación de ranking Top-N Leave-One-Out.", "Objetivo Específico 3 (Punto 5):")
    add_numbered(doc, 4, "Modelar productos (espacio tridimensional Z-Score y cláusulas contractuales), comportamientos (dinámica mensual de tesorería y frecuencia inversa ITF) y perfiles sociodemográficos (estereotipos y vecindarios kNN) resolviendo el problema de arranque en frío.", "Objetivo Específico 4 (Punto 6):")
    add_numbered(doc, 5, "Implementar sistemas de recomendación ítem a ítem mediante similitud de cosenos (ajustado, binario e ITF) y correlación de Pearson sobre ratings continuos y contratos domiciliados, contrastando empíricamente sus niveles de dispersión.", "Objetivo Específico 5 (Punto 7):")
    add_numbered(doc, 6, "Desarrollar sistemas de recomendación basados en contenidos mediante vectorización léxica TF-IDF sobre cláusulas legales con validación Leave-One-Product-Out (LOPO), integrando compuertas de gobernanza y reglas de utilidad financiera.", "Objetivo Específico 6 (Punto 8):")
    
    # 2.2 Modalidad
    add_heading(doc, 3, "2.2 Modalidad")
    add_paragraph(doc, "Práctica de laboratorio desarrollada en modalidad presencial, complementada con sesiones autónomas de modelado matemático, programación analítica en Python, validación cruzada 5-fold, pruebas de hipótesis estadísticas y verificación cruzada de matrices de cálculo.")
    
    # 2.3 Tiempo de duración
    add_heading(doc, 3, "2.3 Tiempo de duración")
    add_bullet(doc, "2 horas de sesión guiada en laboratorio para la calibración del entorno analítico, discusión de requisitos de negocio y presentación de la arquitectura de datos.", "Presenciales:")
    add_bullet(doc, "6 horas de trabajo autónomo dedicadas a la ingeniería de características, procesamiento matricial intensivo, validación cruzada de pliegues, cálculo de métricas de ranking y redacción del informe técnico.", "No presenciales:")
    
    # 2.4 Instrucciones
    add_heading(doc, 3, "2.4 Instrucciones")
    add_paragraph(doc, "Tomando como base los cuatro DataFrames analíticos limpios y consolidados de la entidad bancaria Financial_ijs, estructurar para cada algoritmo la matriz de datos que proporcione la señal analítica adecuada. Desarrollar cada uno de los 8 puntos requeridos por la consigna docente de forma secuencial, programando los motores de recomendación respetando los estándares de reproducibilidad científica (semilla aleatoria fijada seed = 42), evaluando los errores predictivos y niveles de afinidad, e interpretando los hallazgos en función de la toma de decisiones comerciales, la fidelización del cliente y la gestión prudencial del riesgo de la institución bancaria.")
    
    # 2.5 Equipos y Materiales
    add_heading(doc, 3, "2.5 Listado de equipos, materiales y recursos")
    add_heading(doc, 4, "Listado de equipos y materiales generales empleados en la guía práctica:")
    add_bullet(doc, "Computador personal con arquitectura x86_64, 16 GB de memoria RAM, procesador multi-núcleo de alta velocidad y sistema operativo Microsoft Windows 11.", "Hardware:")
    add_bullet(doc, "Entorno de desarrollo integrado VS Code, terminal PowerShell y distribución científica Python 3.12 con librerías analíticas especializadas: Pandas (manipulación de datos), NumPy (álgebra matricial), Scikit-Learn (vectorización y métricas de evaluación), SciPy (tests estadísticos y distribuciones), Matplotlib y Seaborn (renderizado gráfico en alta resolución a 300 DPI).", "Software y Entorno Científico:")
    add_bullet(doc, "Los cuatro DataFrames analíticos limpios y consolidados de la entidad bancaria Financial_ijs (PKDD'99 Financial Discovery Challenge) en formatos CSV estructurados y comprimidos.", "Conjuntos de Datos:")
    add_bullet(doc, "Microsoft Excel para la auditoría manual independiente, verificación cruzada de sumas y comprobación de productos matriciales.", "Herramientas de Auditoría:")
    
    add_heading(doc, 4, "TAC (Tecnologías para el Aprendizaje y Conocimiento) empleados en la guía práctica:")
    add_checkbox(doc, False, "Plataformas educativas")
    add_checkbox(doc, True, "Simuladores y laboratorios virtuales (Jupyter Lab, Entornos Interactivos en Python)")
    add_checkbox(doc, True, "Aplicaciones educativas")
    add_checkbox(doc, False, "Recursos audiovisuales")
    add_checkbox(doc, False, "Gamificación")
    add_checkbox(doc, True, "Inteligencia Artificial (Asistentes de programación científica y verificación estadística)")
    add_paragraph(doc, "Otros (Especifique): Sistema de control de versiones distribuido Git y bibliotecas de procesamiento matricial optimizado.")
    
    # 2.6 Actividades por desarrollar
    add_heading(doc, 3, "2.6 Actividades por desarrollar")
    add_paragraph(doc, "En estricto cumplimiento de la consigna establecida por el docente, la investigación experimental y el modelado analítico se articularon a través de los ocho puntos secuenciales solicitados:")
    add_numbered(doc, 1, "Generación de uno o varios DataFrames a partir de un DataMart: Modelar y extraer los cuatro DataFrames canónicos desde el Data Warehouse bancario en esquema estrella de Ralph Kimball.", "Punto 1:")
    add_numbered(doc, 2, "Organizar la información: Elevar el grano desde eventos atómicos a cuentas/titulares, auditar claves foráneas y evaluar la viabilidad técnica de las 20 combinaciones algoritmo × DataFrame.", "Punto 2:")
    add_numbered(doc, 3, "Clasificar la información: Definir la taxonomía formal de servicios financieros transaccionales, tipologías de órdenes, arquetipos sociodemográficos y familias metodológicas de recomendadores.", "Punto 3:")
    add_numbered(doc, 4, "Filtrar la información: Aplicar estabilización logarítmica de Pareto, escalamiento a rango [1, 5], filtrado de cuentas secundarias y compuertas prudenciales de solvencia crediticia.", "Punto 4:")
    add_numbered(doc, 5, "Generar un sistema de recomendación Slope One: Implementar el algoritmo con cálculo de desviaciones medias, soportes, validación cruzada 5-fold, ranking Top-N y trazabilidad manual paso a paso con clientes reales.", "Punto 5:")
    add_numbered(doc, 6, "Modele productos, comportamientos, perfiles: Modelar productos (espacio Z-Score y TF-IDF), comportamientos (dinámica mensual de tesorería y frecuencia inversa ITF) y perfiles (estereotipos demográficos y vecindarios kNN).", "Punto 6:")
    add_numbered(doc, 7, "Sistema de recomendación item to item (similitud de cosenos y Pearson): Implementar Coseno Ajustado, Coseno Binario, ponderación ITF y correlación de Pearson sobre ratings y órdenes domiciliadas.", "Punto 7:")
    add_numbered(doc, 8, "Sistema de recomendación basado en contenidos: Desarrollar vectorización léxica TF-IDF con validación Leave-One-Product-Out (LOPO) y reglas de scoring con función de utilidad financiera.", "Punto 8:")
    
    # =========================================================================
    # 2.7 RESULTADOS OBTENIDOS
    # =========================================================================
    add_heading(doc, 3, "2.7 Resultados obtenidos")
    add_paragraph(doc, "Los resultados analíticos y computacionales obtenidos en la práctica de laboratorio se estructuran a continuación respondiendo con rigor científico a cada uno de los ocho requerimientos de la consigna docente:")
    
    # -------------------------------------------------------------------------
    # PUNTO 1: Uno o varios DataFrames a partir de un DataMart
    # -------------------------------------------------------------------------
    add_heading(doc, 4, "2.7.1 Uno o varios DataFrames a partir de un DataMart")
    add_paragraph(doc, "Marco conceptual y origen de datos: Para el desarrollo experimental de la práctica se tomó como fuente la base de datos bancaria Financial_ijs (correspondiente al benchmark internacional PKDD'99 Financial Discovery Challenge), la cual contiene registros operacionales, cuentas, contratos y clientes de un banco comercial a lo largo de un período de seis años (1993 a 1998). A partir de este repositorio relacional transaccional, se construyó un Data Warehouse bajo la metodología dimensional de Ralph Kimball en esquema de estrella con dimensiones conformadas compartidas, desde el cual se extrajeron y consolidaron los cuatro DataFrames analíticos limpios utilizados en los modelos de recomendación: df_transacciones (1,056,320 movimientos contables y pagos), df_ordenes (6,471 órdenes de débito permanente domiciliadas en 3,758 cuentas), df_prestamos (682 contratos de crédito con sus plazos y cuotas) y df_cliente_consolidado (visión 360° sociodemográfica y financiera de 5,369 clientes).")
    
    add_paragraph(doc, "Matriz de Trazabilidad Metodológica de la Consigna: Para facilitar la verificación exhaustiva de los ocho requerimientos técnicos estipulados en la guía práctica académica, la Tabla 1-A establece el mapeo directo entre cada punto de la consigna y su sección de desarrollo detallada:")
    
    tbl1a_headers = ["Punto de la Consigna", "Requerimiento Técnico Evaluado", "Sección(es) del Informe", "Evidencia / Tablas y Figuras"]
    tbl1a_rows = [
        ["1. DataFrames desde DataMart", "Derivar uno o varios DataFrames analíticos limpios a partir de un DataMart/DW relacional.", "Sección 2.7.1 (Punto 1)", "Tabla 1-B, Tabla 1-C y scripts ETL (00)"],
        ["2. Organizar la información", "Estructurar la información con diccionario de variables y matriz de viabilidad algoritmo × DataFrame.", "Sección 2.7.2 (Punto 2)", "Tabla 3 (Diccionario), Tabla 4 (Matriz 5×4) y Figura 16"],
        ["3. Clasificar la información", "Taxonomía formal de servicios financieros transaccionales y segmentación demográfica por arquetipos.", "Sección 2.7.3 (Punto 3)", "Taxonomías 5 servicios y 4 órdenes, 4 familias RS"],
        ["4. Filtrar la información", "Conectar el filtrado con escala [1, 5], mitigación de Pareto y compuertas de solvencia.", "Sección 2.7.4 (Punto 4)", "Filtro Pareto, escala [1, 5], exclusión disponentes y regla 30%"],
        ["5. Sistema Slope One completo", "Formulación formal f(x)=x+b, matriz antisimétrica con soportes y ejemplo numérico paso a paso con trazabilidad.", "Sección 2.7.5 (Punto 5)", "Tabla 2 (Trazabilidad Clientes #2 y #45), Tabla 5 (Matriz 5×5) y Figura 1"],
        ["6. Modelado de entidades", "Modelar productos (contenidos), comportamientos (transacciones/ratings) y perfiles (demográficos).", "Sección 2.7.6 (Punto 6)", "Productos: 3B/3A | Comportamientos: 1B/1C/2B | Perfiles: 4A/4B/4C"],
        ["7. Ítem-a-ítem con Coseno y Pearson", "Sistema ítem-a-ítem con Coseno Ajustado / Binario y Pearson sobre ratings (matriz 5×5 y cálculo de clase).", "Sección 2.7.7 (Punto 7)", "Tabla 6 (Coseno Ajustado), Tabla 7-A (Pearson ratings), Tablas 8, 9, 10"],
        ["8. Sistema basado en contenidos", "Filtrado basado en contenidos con TF-IDF sobre cláusulas textuales con LOPO y reglas de utilidad.", "Sección 2.7.8 (Punto 8)", "Tabla 11 (TF-IDF LOPO 8/8), Tabla 13 (Mora y Utilidad) y Figuras 7 y 9"]
    ]
    add_table(doc, "Tabla 1-A: Matriz de Trazabilidad Metodológica: Puntos de la Consigna de la Guía Práctica → Secciones del Informe.", tbl1a_headers, tbl1a_rows, [Inches(1.3), Inches(2.0), Inches(1.5), Inches(1.31)])
    
    add_paragraph(doc, "Las características de las entidades originales del Data Warehouse transaccional se detallan en la Tabla 1-B:")
    
    tbl1_headers = ["Tabla Origen", "Tipo de Entidad", "Grano de la Información", "Registros", "Claves Primarias / Foráneas"]
    tbl1_rows = [
        ["client", "Dimensión", "Un cliente registrado en la entidad", "5,369", "client_id, district_id"],
        ["account", "Dimensión", "Una cuenta bancaria matriz", "4,500", "account_id, district_id"],
        ["disp", "Relación / Puente", "Vínculo cliente - cuenta bancaria", "5,369", "disp_id, client_id, account_id"],
        ["trans", "Tabla de Hechos", "Un movimiento o transacción contable", "1,056,320", "trans_id, account_id, k_symbol"],
        ["order", "Tabla de Hechos", "Una orden de débito permanente", "6,471", "order_id, account_id, k_symbol"],
        ["loan", "Tabla de Hechos", "Un contrato formal de crédito", "682", "loan_id, account_id"],
        ["district", "Dimensión", "Un distrito demográfico y socioeconómico", "77", "district_id"]
    ]
    add_table(doc, "Tabla 1-B: Inventario de Objetos del Sistema Transaccional Bancario (Financial_ijs).", tbl1_headers, tbl1_rows)
    
    add_paragraph(doc, "A partir de estas tablas de hechos y dimensiones conformadas, el script ETL de extracción (00_generar_4_dataframes.py) produjo los cuatro DataFrames analíticos limpios y consolidados que constituyen la base de todos los experimentos. La Tabla 1-C sintetiza sus características dimensionales:")
    
    tbl1c_headers = ["DataFrame Generado", "Grano Operacional", "Registros", "Entidades Únicas", "Variables Clave Extraídas"]
    tbl1c_rows = [
        ["df_transacciones", "Mensual por Servicio Transaccional", "1,056,320", "4,500 cuentas / 3,653 activas", "account_id, k_symbol, anio_mes, monto, balance, freq"],
        ["df_ordenes", "Contrato de Débito Domiciliado", "6,471", "3,758 cuentas bancarias", "account_id, k_symbol, amount, bank_to, account_to"],
        ["df_prestamos", "Operación Formal de Crédito", "682", "682 cuentas con préstamo único", "loan_id, account_id, amount, duration, payments, status"],
        ["df_cliente_consolidado", "Perfil Dimensional 360°", "5,369", "5,369 clientes (4,500 titulares)", "client_id, age, gender, district, salary, balance_avg, tx_count"]
    ]
    add_table(doc, "Tabla 1-C: Resumen de Dimensiones y Características de los Cuatro DataFrames Analíticos Limpios.", tbl1c_headers, tbl1c_rows)
    
    # -------------------------------------------------------------------------
    # PUNTO 2: Organizar la información
    # -------------------------------------------------------------------------
    add_heading(doc, 4, "2.7.2 Organizar la información")
    add_paragraph(doc, "Elevación del grano operacional: Una tabla transaccional pura registra eventos atómicos ('retiro de 400 CZK en cajero automático a las 10:15'). Sugerir un retiro individual carece de valor comercial; el cliente contrata el servicio de Tarjeta de Débito o domicilia Pagos del Hogar. Por tanto, para alimentar los modelos de recomendación comercial, la información se reorganizó agregando los eventos microscópicos en función de entidades de decisión de negocio: el Cliente Titular (client_id con rol 'OWNER') y la Cuenta Bancaria (account_id). Esta agregación elevó el grano de análisis desde movimientos puntuales hacia vectores consolidados de tenencia y frecuencia de servicios financieros.")
    
    add_paragraph(doc, "Auditoría de claves foráneas y tabla puente disp: La relación entre clientes y cuentas no es 1:1, sino que involucra clientes autorizados ('DISPONENT'). Para evitar duplicar artificialmente el consumo de un mismo hogar, se aislaron formalmente los 4,500 clientes titulares independientes (OWNER), auditando la integridad referencial de todas las claves primarias y foráneas (account_id, client_id, district_id).")
    
    add_paragraph(doc, "Estructuración de la matriz Usuario-Ítem y dispersión analítica: Sea U = {u_1, u_2, ..., u_M} el conjunto universal de clientes y sea I = {i_1, i_2, ..., i_N} el catálogo de servicios. El historial de interacciones se organizó matricialmente mediante R en R^(M x N), donde cada escalar r_{u, i} cuantifica la intensidad de preferencia observada. En el entorno bancario, la dispersión analítica se cuantifica como:")
    add_block_math(doc, r"S = 1 - \frac{|R_{\text{observados}}|}{|U| \times |I|}")
    add_paragraph(doc, "donde |R_observados| es el recuento de contratos o movimientos existentes. En Financial_ijs, este índice de dispersión S supera el 68% en transacciones y el 83% en órdenes, imponiendo restricciones severas a los algoritmos que requieren solapamiento denso.")
    
    add_paragraph(doc, "Diccionario de variables analíticas organizadas: Las variables operacionales y transformadas se resumen en el diccionario analítico de la Tabla 3:")
    
    tbl3_headers = ["Variable Analítica", "Fuente Base", "Grano / Entidad", "Definición de Negocio", "Método de Cálculo"]
    tbl3_rows = [
        ["freq_prod", "df_transacciones", "Cliente × Producto", "Frecuencia de uso del servicio financiero", "Recuento de transacciones con concepto específico"],
        ["rating_log", "Calculada", "Cliente × Producto", "Nota normalizada de afinidad implícita", "1.0 + 4.0 × (ln(1 + freq) - min) / (max - min)"],
        ["orden_binaria", "df_ordenes", "Cuenta × Categoría", "Contratación formal de débito automático", "Indicador booleano: 1 si cuenta domicilia el servicio, 0 si no"],
        ["itf_score", "df_ordenes", "Categoría Producto", "Penalización de popularidad masiva", "ln(Total Cuentas / Cuentas con Orden_j)"],
        ["ratio_esfuerzo", "df_prestamos", "Contrato Crédito", "Carga mensual de amortización sobre ingreso", "cuota_mensual / salario_distrito_promedio"],
        ["estereotipo_id", "df_cliente", "Cliente Único", "Segmento sociodemográfico canónico", "Concatenación cruzada: Macro-Región × Rango Etario"]
    ]
    add_table(doc, "Tabla 3: Diccionario de Variables Analíticas Utilizadas en los Motores de Recomendación.", tbl3_headers, tbl3_rows)
    
    add_paragraph(doc, "Evaluación de viabilidad técnica (Matriz 5 Algoritmos × 4 DataFrames): No todos los algoritmos son aplicables de forma válida sobre todos los conjuntos. La viabilidad técnica depende directamente de la granularidad y la naturaleza de las variables. La Tabla 4 documenta la matriz de viabilidad sobre las 20 combinaciones posibles:")
    
    tbl4_headers = ["DataFrame Base", "1. Slope One", "2. Similitud Coseno", "3. Correlación Pearson", "4. TF-IDF (Contenidos)", "5. Demográfico (Estereotipos)"]
    tbl4_rows = [
        ["df_transacciones\n(1,056,320 movs)", "SELECCIONADO (1A)\nMasa crítica de transacciones repetidas cliente-producto.", "SELECCIONADO (1B)\nCoseno ajustado sobre vectores centrados en medias.", "COMPLEMENTARIO (1C)\nPearson sobre ratings implícitos y series mensuales (Δx_t).", "NO APLICABLE\nNo contiene texto descriptivo; solo importes y fechas.", "VIABLE (Vía JOIN)\nRequiere desnormalizar atributos sociodemográficos."],
        ["df_ordenes\n(6,471 órdenes)", "VIABLE (Secundario)\nMenor varianza de frecuencias que en transacciones diarias.", "SELECCIONADO (2A / 2B)\nCoseno binario y ponderación colaborativa ITF.", "COMPLEMENTARIO (2C)\nCorrelación de adopción de órdenes fijas entre cuentas.", "NO APLICABLE\nCarece de corpus textual (ITF es extensión colaborativa).", "VIABLE (Vía JOIN)\nAgregación de órdenes promedio por perfil."],
        ["df_prestamos\n(682 créditos)", "INVÁLIDO (Degenerado)\nClientes poseen un único crédito; soporte conjunto card(S(j,i)) ≈ 0.", "COMPLEMENTARIO (3B)\nProximidad numérica sobre condiciones [monto, plazo, cuota].", "SECUNDARIO\nVolumen mensual de concesión; muestra reducida (682 filas).", "SELECCIONADO (3A)\nCláusulas contractuales, garantías y condiciones de crédito.", "SELECCIONADO (3C: Utilidad)\nReglas de scoring de riesgo y cuota ≤ 30% salario."],
        ["df_cliente_consolidado\n(5,369 clientes)", "NO APLICABLE\nVariables estáticas de usuario; no representa matriz de ítems.", "SELECCIONADO (4B)\nSimilitud Coseno Usuario a Usuario (gemelos financieros).", "COMPLEMENTARIO (4C)\nCorrelación multivariante de perfil (edad, saldo, salario).", "NO APLICABLE\nAtributos numéricos y discretos; no posee corpus textual.", "SELECCIONADO (4A)\nDimensión maestra para construir arquetipos de negocio."]
    ]
    add_table(doc, "Tabla 4: Matriz Cruzada de Viabilidad Técnica (5 Algoritmos × 4 DataFrames).", tbl4_headers, tbl4_rows, [Inches(1.2), Inches(1.0), Inches(1.0), Inches(1.0), Inches(1.0), Inches(0.91)])
    
    # -------------------------------------------------------------------------
    # PUNTO 3: Clasificar la información
    # -------------------------------------------------------------------------
    add_heading(doc, 4, "2.7.3 Clasificar la información")
    add_paragraph(doc, "La clasificación de la información se ejecutó en tres niveles complementarios: clasificación taxonómica de servicios bancarios, clasificación sociodemográfica de clientes y clasificación metodológica de las familias de recomendación revisadas en clases:")
    
    add_paragraph(doc, "1. Taxonomía de servicios financieros transaccionales y contractuales: Los códigos operacionales crudos (k_symbol) presentaban ambigüedad y valores nulos. Para superarlo, se estableció una taxonomía formal de cinco categorías funcionales en transacciones: (1) TARJETA_DEBITO (retiros en cajeros y pagos POS con tarjeta); (2) SERVICIOS_HOGAR (débitos recurrentes de servicios domésticos); (3) PRESTAMO (cuotas de amortización crediticia); (4) SEGURO (primas de cobertura patrimonial o de vida); y (5) TRANSF_EXTERNA (transferencias interbancarias). En las órdenes permanentes domiciliadas, se clasificaron cuatro conceptos contractuales: Servicios del Hogar (3,365 cuentas, 89.54%), Cuota de Préstamo (717 cuentas, 19.08%), Pago de Seguros (532 cuentas, 14.16%) y Arrendamiento / Leasing (117 cuentas, 3.11%).")
    
    add_paragraph(doc, "2. Clasificación sociodemográfica de clientes: En el DataFrame dimensional df_cliente_consolidado, los 5,369 clientes se segmentaron en nueve arquetipos sociodemográficos canónicos cruzando tres macro-regiones geográficas (Metropolitana Praga, Bohemia Centro-Oeste y Moravia Este) con tres intervalos etarios vitales (Jóvenes <30 años, Adultos 30-50 años y Adultos Mayores >50 años), permitiendo capturar patrones heterogéneos de bancarización y endeudamiento.")
    
    add_paragraph(doc, "3. Clasificación de las cuatro familias de algoritmos revisadas en clases: Siguiendo el marco curricular de la asignatura Inteligencia de Negocios, los sistemas desarrollados se clasifican en cuatro familias analíticas fundamentales:")
    add_bullet(doc, "Explota la matriz de interacciones usuario-producto sin requerir atributos intrínsecos. Se subdivide en: (a) Métodos Ítem a Ítem (Slope One, Coseno Ajustado, Coseno Binario, Ponderación ITF, Pearson sobre ratings); y (b) Métodos Usuario a Usuario (kNN sobre perfiles transaccionales).", "Familia de Filtrado Colaborativo (Collaborative Filtering):")
    add_bullet(doc, "Recomienda productos comparando sus descriptores técnicos y cláusulas contractuales con las preferencias del usuario mediante Procesamiento de Lenguaje Natural (TF-IDF sobre cláusulas legales), resolviendo el Item Cold Start.", "Familia de Filtrado Basado en Contenidos (Content-Based Filtering):")
    add_bullet(doc, "Asocia a los usuarios con estereotipos poblacionales basados en edad, ubicación geográfica y estrato económico, otorgando una solución determinista al User Cold Start en apertura de cuenta.", "Familia de Filtrado Demográfico (Demographic Filtering):")
    add_bullet(doc, "Incorpora reglas de política bancaria, compuertas de solvencia (cuota ≤ 30% del salario distrital) y restricciones prudenciales de riesgo de impago, gobernando transversalmente las recomendaciones comerciales.", "Modelos Basados en el Conocimiento y en la Utilidad Financiera (Knowledge & Utility-Based):")
    
    # -------------------------------------------------------------------------
    # PUNTO 4: Filtrar la información
    # -------------------------------------------------------------------------
    add_heading(doc, 4, "2.7.4 Filtrar la información")
    add_paragraph(doc, "El filtrado analítico de la información abordó cuatro problemáticas críticas de sesgo poblacional, dispersión matemática y prudencia financiera:")
    
    add_paragraph(doc, "1. Filtro de Pareto y estabilización monótona logarítmica: En Financial_ijs, las frecuencias transaccionales brutas siguen una distribución de ley de potencias (coeficiente de asimetría g_1 > 3.5), donde una minoría hiperactiva acumula cientos de transacciones al mes mientras la mayoría mantiene baja actividad. Asimismo, las cuentas abiertas en 1993 acumulan mecánicamente seis veces más operaciones que las de 1997. Computar promedios aritméticos brutos sobre estas frecuencias provocaría que los clientes hiperactivos sesgaran las distancias euclidianas. Para resolver este sesgo estructural, se aplicó la transformación logarítmica monótona cóncava:")
    add_block_math(doc, r"y_{u, i} = \ln(1 + x_{u, i})")
    add_paragraph(doc, "donde x_{u, i} es el recuento bruto de transacciones. Con y_min = ln(1 + 1) = ln(2) ≈ 0.6931 e y_max = ln(1 + 257) = ln(258) ≈ 5.5530 observados en la muestra, los valores se escalaron linealmente al rango continuo [1.0, 5.0]:")
    add_block_math(doc, r"r_{u, i} = 1.0 + 4.0 \cdot \left(\frac{y_{u, i} - y_{\min}}{y_{\max} - y_{\min}}\right) = 1.0 + 0.8231 \cdot (y_{u, i} - 0.6931) \approx 0.4295 + 0.8231 \cdot \ln(1 + x_{u, i})")
    
    add_paragraph(doc, "2. Filtro de clientes disponentes y artefacto de similitud unitaria: En el modelado colaborativo Usuario a Usuario (Modelo 4B), se descubrió que incluir clientes autorizados ('DISPONENT') provocaba que 869 registros colapsaran en una similitud perfecta cos = 1.0000 con otros usuarios. Esto ocurría porque al no tener transacciones propias, sus vectores brutos eran cero y al estandarizar Z-score colapsaban en el mismo punto (-mu / sigma). El filtro aplicado restringió el espacio vectorial exclusivamente a los 4,500 titulares independientes, eliminando este artefacto espurio.")
    
    add_paragraph(doc, "3. Filtro prudencial de morosidad histórica (Regla de Negocio 1): Como compuerta obligatoria de control de riesgo, se aplicó un filtro determinista que bloquea automáticamente a cualquier cliente con antecedentes de incumplimiento en préstamos (estados 'B' de contrato no pagado y 'D' de deuda en mora judicial), excluyendo al 11.15% de prestatarios históricos de recibir cualquier oferta de nuevo endeudamiento.")
    
    add_paragraph(doc, "4. Filtro de capacidad de pago y solvencia crediticia (Regla del 30%): Se filtraron las recomendaciones crediticias condicionándolas a que la cuota de amortización no supere el 30% del salario distrital promedio estimado del cliente. La validez de este filtro se sustenta en la evidencia empírica transversal: los créditos en el rango prudencial (≤ 30%) registran una tasa de morosidad de apenas 6.57% (14 de 213), mientras que en clientes con endeudamiento crítico (> 50%) la mora se triplica al 16.86% (44 de 261), diferencia estadísticamente significativa confirmada con Chi-cuadrado (χ² = 10.62, p = 0.0011) y Test Exacto de Fisher (p = 0.0007).")
