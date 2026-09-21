# -*- coding: utf-8 -*-
"""
Módulo Parte 1: Portada, Objetivos, Metodología, Marco Conceptual,
Origen de Datos y Preparación Matemática con Trazabilidad Exhaustiva.
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
        ["Tema:", "Implementación, Validación Experimental y Evaluación Multicriterio de Sistemas de Recomendación Colaborativos, Basados en Contenidos, Demográficos y de Utilidad sobre los Cuatro DataFrames del Banco Comercial (Financial_ijs)"],
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
    add_paragraph(doc, "Desarrollar, evaluar, contrastar empíricamente y desplegar en una arquitectura analítica coherente múltiples sistemas de recomendación sobre cada uno de los cuatro DataFrames limpios del banco comercial Financial_ijs (PKDD'99 Financial Discovery Challenge), aplicando para cada conjunto de datos los algoritmos canónicos válidos según su nivel de agregación, granularidad temporal y naturaleza de información, incorporando sus respectivas formulaciones matemáticas rigurosas, procedimientos metodológicos paso a paso, matrices numéricas auditadas, gráficos individuales en alta definición (300 DPI), ejemplos numéricos de cálculo paso a paso con clientes reales de la entidad e interpretaciones comerciales profundas que fundamenten las conclusiones y recomendaciones estratégicas de negocio para cada método evaluado.")
    
    add_heading(doc, 4, "Específicos:")
    add_numbered(doc, 1, "Modelar y estructurar los cuatro DataFrames analíticos limpios procedentes del Data Warehouse bancario bajo la metodología dimensional de Ralph Kimball (df_transacciones, df_ordenes, df_prestamos y df_cliente_consolidado), resolviendo inconsistencias de grano, auditando las claves foráneas y evaluando sistemáticamente la viabilidad matemática de las 20 combinaciones matriciales posibles (5 familias de algoritmos × 4 DataFrames).", "Objetivo Específico 1:")
    add_numbered(doc, 2, "Implementar, verificar y documentar doce motores de recomendación con su ciclo analítico completo: fundamento teórico, formulación matemática en ecuaciones estándar, procedimiento metodológico paso a paso, trazabilidad numérica manual sobre clientes reales, matrices de resultados auditadas, representaciones gráficas individuales y análisis pormenorizado de implicaciones financieras.", "Objetivo Específico 2:")
    add_numbered(doc, 3, "Emitir un dictamen técnico riguroso y cuantitativamente respaldado al cierre de cada DataFrame que determine el mejor método para ese entorno operativo, contrastando sus ventajas frente a los modelos alternativos con base en métricas objetivas de error de intensidad (MAE, RMSE), capacidad de ordenamiento (Hit-Rate@k, MRR), capacidad discriminativa (AUC, Brier Score) y mitigación del riesgo crediticio.", "Objetivo Específico 3:")
    add_numbered(doc, 4, "Demostrar analítica y empíricamente las patologías matemáticas que motivaron el descarte de la co-ocurrencia transaccional cruda frente a los modelos refinados, y sintetizar el rendimiento global de los doce sistemas en un mapa estratégico de cobertura frente a personalización, definiendo una arquitectura de despliegue bancario en dos fases gobernada transversalmente por compuertas prudenciales de solvencia y riesgo de impago.", "Objetivo Específico 4:")
    
    # 2.2 Modalidad
    add_heading(doc, 3, "2.2 Modalidad")
    add_paragraph(doc, "Práctica de laboratorio desarrollada en modalidad presencial, complementada con sesiones autónomas de modelado matemático, programación analítica en Python, validación cruzada 5-fold, pruebas de hipótesis estadísticas y verificación cruzada de matrices de cálculo.")
    
    # 2.3 Tiempo de duración
    add_heading(doc, 3, "2.3 Tiempo de duración")
    add_bullet(doc, "2 horas de sesión guiada en laboratorio para la calibración del entorno analítico, discusión de requisitos de negocio y presentación de la arquitectura de datos.", "Presenciales:")
    add_bullet(doc, "6 horas de trabajo autónomo dedicadas a la ingeniería de características, procesamiento matricial intensivo, validación cruzada de pliegues, cálculo de métricas de ranking y redacción del informe técnico.", "No presenciales:")
    
    # 2.4 Instrucciones
    add_heading(doc, 3, "2.4 Instrucciones")
    add_paragraph(doc, "Tomando como base los cuatro DataFrames analíticos limpios y consolidados de la entidad bancaria Financial_ijs, estructurar para cada algoritmo la matriz de datos que proporcione la señal analítica adecuada. Programar los motores de recomendación respetando los estándares de reproducibilidad científica (semilla aleatoria fijada seed = 42), evaluar los errores predictivos y niveles de afinidad, e interpretar los hallazgos en función de la toma de decisiones comerciales, la fidelización del cliente y la gestión prudencial del riesgo de la institución bancaria.")
    
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
    add_paragraph(doc, "La investigación experimental y el modelado analítico se articularon a través de ocho actividades metodológicas secuenciales y rigurosamente interconectadas:")
    add_numbered(doc, 1, "Auditoría de integridad relacional, reconciliación de entidades y consolidación dimensional del Data Warehouse bancario Financial_ijs en esquema de estrella bajo principios de Ralph Kimball.", "Actividad 1:")
    add_numbered(doc, 2, "Evaluación sistemática de la viabilidad técnica y matemática de las 20 combinaciones cruzadas posibles (5 familias de algoritmos de recomendación × 4 DataFrames analíticos).", "Actividad 2:")
    add_numbered(doc, 3, "Implementación, cálculo paso a paso, validación cruzada 5-fold, pruebas de ranking Top-N y dictamen técnico de los modelos colaborativos y temporales sobre df_transacciones.", "Actividad 3:")
    add_numbered(doc, 4, "Modelado de co-adquisición contractual, penalización de frecuencia inversa (ITF), análisis de correlación y dictamen técnico sobre df_ordenes.", "Actividad 4:")
    add_numbered(doc, 5, "Vectorización semántica TF-IDF sobre cláusulas, mapeo geométrico de plazos y diseño del filtro de solvencia con función de utilidad financiera (regla del 30%) sobre df_prestamos.", "Actividad 5:")
    add_numbered(doc, 6, "Segmentación demográfica por estereotipos (resolución de User Cold Start), filtrado colaborativo Usuario a Usuario (kNN) y análisis multivariante sobre df_cliente_consolidado.", "Actividad 6:")
    add_numbered(doc, 7, "Demostración analítica y cuantitativa de las patologías matemáticas que justificaron el descarte empírico de la co-ocurrencia transaccional cruda.", "Actividad 7:")
    add_numbered(doc, 8, "Síntesis comparativa global de los doce recomendadores, construcción de la frontera estratégica de cobertura frente a personalización y diseño de la arquitectura bancaria en dos fases.", "Actividad 8:")
    
    # =========================================================================
    # 2.7 RESULTADOS OBTENIDOS
    # =========================================================================
    add_heading(doc, 3, "2.7 Resultados obtenidos")
    
    # 2.7.1 Marco conceptual aplicado y taxonomía
    add_heading(doc, 4, "2.7.1 Marco conceptual aplicado y taxonomía de sistemas de recomendación en la banca comercial")
    add_paragraph(doc, "En el ecosistema bancario contemporáneo, un sistema de recomendación (Recommender System, RS) constituye una herramienta analítica avanzada diseñada para estimar la propensión, interés o afinidad de un cliente hacia productos financieros específicos que no posee activamente. A diferencia del comercio electrónico generalista (donde prima la compra por impulso), los servicios bancarios involucran compromisos contractuales de largo plazo, riesgo de crédito, requerimientos de liquidez y normativas regulatorias estrictas. En consecuencia, un motor de recomendación financiero no solo debe identificar qué producto atrae al cliente, sino también si dicho producto es coherente con su capacidad de pago y si preserva la salud patrimonial de la institución.")
    
    add_paragraph(doc, "Formulación matemática general del problema de recomendación: Sea U = {u_1, u_2, ..., u_M} el conjunto universal de clientes de la entidad financiera, y sea I = {i_1, i_2, ..., i_N} el catálogo de productos y servicios ofertados por la institución. El historial de interacciones se representa matricialmente mediante R en el espacio real R^(M x N), donde cada elemento escalar r_{u, i} cuantifica la intensidad de preferencia observada. En el ámbito bancario, la gran mayoría de las combinaciones cliente-producto carecen de interacción previa, dando lugar a una matriz con una densidad sumamente baja. La dispersión analítica se formula como:")
    add_block_math(doc, r"S = 1 - \frac{|R_{\text{observados}}|}{|U| \times |I|}")
    add_paragraph(doc, "donde |R_observados| es el recuento de contratos o movimientos existentes. En la banca comercial minorista, este índice de dispersión S supera típicamente el 85%, lo que impone restricciones severas a los algoritmos que requieren solapamiento denso. La meta algorítmica es aprender una función de correspondencia f: U x I -> R que estime las calificaciones implícitas latentes rhat_{u, j} para todos los productos j no pertenecientes a la cartera activa del cliente u, de modo que se minimice el error de predicción sobre las preferencias futuras y se maximice la precisión del ranking Top-N resultante.")
    
    add_paragraph(doc, "De acuerdo con la literatura científica clásica y las directrices curriculares de la asignatura Inteligencia de Negocios, los sistemas de recomendación se estructuran en tres familias metodológicas principales, enriquecidas por una cuarta categoría transversal de gobernanza financiera:")
    
    add_bullet(doc, "Se fundamenta en la premisa socioconductual de que clientes con hábitos de consumo o transaccionalidad similares en el pasado mantendrán preferencias convergentes en el futuro. No requiere conocer los atributos contractuales intrínsecos de los productos ni el perfil demográfico del usuario; opera exclusivamente sobre la matriz de interacciones usuario-producto. Dentro de esta familia coexisten dos grandes orientaciones: (a) Enfoques basados en usuarios (User-to-User), que localizan gemelos comportamentales para transferir recomendaciones; y (b) Enfoques basados en productos o ítems (Item-to-Item, como Slope One y Coseno Ajustado), que calculan la proximidad o diferencias relativas entre pares de servicios sobre clientes comunes. En el ámbito académico (diapositivas de clase), los métodos colaborativos suelen agruparse bajo el término general 'filtrado basado en usuarios' en contraposición al de contenidos, si bien técnicamente Slope One e Item-kNN operan sobre vectores columna de productos.", "Familia de Filtrado Colaborativo (Collaborative Filtering):")
    
    add_bullet(doc, "Recomienda productos comparando las características técnicas, legales y funcionales del catálogo bancario con los antecedentes de consumo del cliente. Modela tanto el perfil del producto como las preferencias del usuario a través de representaciones vectoriales de atributos (plazos, cláusulas de amortización, coberturas de seguro, requisitos de colateral). Es el enfoque canónico para superar el arranque en frío de productos (Item Cold Start): un crédito recién creado puede ser sugerido inmediatamente al mapear sus descriptores textuales mediante técnicas de Procesamiento de Lenguaje Natural como TF-IDF.", "Familia de Filtrado Basado en Contenidos (Content-Based Filtering):")
    
    add_bullet(doc, "Explota los atributos sociodemográficos del cliente (edad, sexo, macro-región geográfica, nivel salarial distrital) bajo el postulado de que usuarios pertenecientes al mismo estrato poblacional exhiben necesidades bancarias homogéneas. Basado en la teoría clásica de estereotipos (Rich, 1979), este enfoque resulta indispensable para resolver el arranque en frío de nuevos usuarios (User Cold Start): en el momento exacto en que un ciudadano abre su primera cuenta de ahorros y carece por completo de historial transaccional, el banco puede asignarle ofertas personalizadas acordes al consumo promedio de su arquetipo demográfico.", "Familia de Filtrado Demográfico (Demographic Filtering):")
    
    add_bullet(doc, "A diferencia de los modelos puramente asociativos o estadísticos, estos sistemas incorporan conocimiento explícito del negocio crediticio, reglas de política monetaria y funciones matemáticas de utilidad. Evalúan de manera determinista si la contratación de un producto cumple con las compuertas de solvencia de la entidad (por ejemplo, verificando que la cuota de amortización no sobrepase el 30% del salario distrital promedio del cliente y bloqueando a usuarios con morosidad histórica). Actúan como una capa transversal de prudencia bancaria que previene activamente el sobreendeudamiento.", "Modelos Basados en el Conocimiento y en la Utilidad Financiera (Knowledge & Utility-Based):")
    
    add_paragraph(doc, "Naturaleza de los ratings implícitos en banca: En la operativa bancaria real, los clientes no otorgan puntuaciones explícitas de 1 a 5 estrellas a sus transferencias o débitos automáticos. Por consiguiente, las calificaciones deben inferirse matemáticamente a partir de señales de comportamiento implícito: la recurrencia de movimientos contables, la contratación formal de órdenes domiciliadas y la tenencia de préstamos. Siguiendo el marco conceptual formalizado por Hu, Koren y Volinsky (2008), la retroalimentación implícita en finanzas presenta dos propiedades críticas: (1) Ausencia de señales negativas explícitas: el hecho de que un cliente no mantenga un seguro de vida no significa aversión, sino posiblemente falta de exposición o necesidad temporal; y (2) La frecuencia operacional x_{u, i} actúa como una medida monótona de confianza c_{u, i} en la preferencia del usuario, no como una satisfacción hedónica directa. Para procesar estas señales, se normalizan y escalan rigurosamente para alimentar las matrices analíticas.")
    
    add_paragraph(doc, "Taxonomía del problema de arranque en frío (Cold Start) en la industria bancaria: El fenómeno de arranque en frío representa el reto de ingeniería predictiva más agudo en instituciones financieras. Se manifiesta en tres vertientes operacionales: (a) Arranque en Frío de Usuario (User Cold Start), que afecta a cada cliente que se vincula por primera vez al banco; al carecer de meses de depósitos o transacciones, los métodos colaborativos puros colapsan en indeterminación matemática. (b) Arranque en Frío de Producto (Item Cold Start), que surge cuando la institución diseña una nueva línea de financiamiento verde o un seguro de ciber-riesgo sin clientes históricos asociados. (c) Arranque en Frío del Sistema (System Cold Start), correspondiente a la puesta en marcha de una nueva filial bancaria. Como se demostrará cuantitativamente a lo largo del informe, la solución óptima radica en una arquitectura híbrida donde el Filtrado Demográfico (Modelo 4A) y el Filtrado Basado en Contenidos con TF-IDF (Modelo 3A) operan como amortiguadores iniciales con cobertura total (100%), transfiriendo progresivamente los clientes a los modelos colaborativos (Slope One, ITF y kNN) conforme su huella transaccional madura.")
    
    # 2.7.2 Origen de los datos (PÁRRAFO ÚNICO CONCISO)
    add_heading(doc, 4, "2.7.2 Origen de los datos y arquitectura del Data Warehouse Bancario (Financial_ijs)")
    add_paragraph(doc, "Para el desarrollo experimental de la práctica se tomó como fuente la base de datos bancaria Financial_ijs (correspondiente al benchmark internacional PKDD'99 Financial Discovery Challenge), la cual contiene registros operacionales, cuentas, contratos y clientes de un banco comercial a lo largo de un período de seis años (1993 a 1998). A partir de este repositorio relacional transaccional, se construyó un Data Warehouse bajo la metodología dimensional de Ralph Kimball en esquema de estrella con dimensiones conformadas compartidas, desde el cual se extrajeron y consolidaron los cuatro DataFrames analíticos limpios utilizados en los modelos de recomendación: df_transacciones (1,056,320 movimientos contables y pagos), df_ordenes (6,471 órdenes de débito permanente domiciliadas en 3,758 cuentas), df_prestamos (682 contratos de crédito con sus plazos y cuotas) y df_cliente_consolidado (visión 360° sociodemográfica y financiera de 5,369 clientes). Las características de las entidades originales se detallan en la Tabla 1.")
    
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
    add_table(doc, "Tabla 1: Inventario de Objetos del Sistema Transaccional Bancario (Financial_ijs).", tbl1_headers, tbl1_rows)
    
    # 2.7.3 Metodología de preparación de datos
    add_heading(doc, 4, "2.7.3 Metodología de preparación de datos: Organizar, Clasificar, Filtrar y Modelar")
    add_paragraph(doc, "A partir del DataMart dimensional de Ralph Kimball, se llevó a cabo un proceso sistemático y estructurado de ingeniería analítica para transformar los registros transaccionales en conjuntos aptos para la inferencia de preferencias. Este procedimiento comprendió cuatro etapas deterministas:")
    
    add_paragraph(doc, "1. Organizar la información a partir del DataMart: La tabla de hechos atómica registra eventos puntuales ('retiro en cajero automático'). Para alimentar modelos de recomendación comercial, la información se reorganizó agregando los eventos en función de entidades de decisión de negocio: el Cliente Titular (client_id con rol 'OWNER') y la Cuenta Bancaria (account_id). Esta agregación elevó el grano de análisis desde movimientos microscópicos hacia vectores consolidados de tenencia y frecuencia de servicios financieros.")
    
    add_paragraph(doc, "2. Clasificar la información: Se estableció una taxonomía rigurosa de los servicios bancarios para superar la ambigüedad de los códigos operacionales crudos. Las transacciones se clasificaron en cinco categorías de servicio: Tarjeta de Débito (retiros con tarjeta), Servicios del Hogar (gastos corrientes domésticos), Préstamo (pagos de amortización), Seguro (coberturas patrimoniales y médicas) y Transferencias Externas (remesas interbancarias). En las órdenes domiciliadas se tipificaron cuatro conceptos de pago (Hogar, Seguro, Préstamo y Leasing). Adicionalmente, los clientes se clasificaron sociodemográficamente mediante la interacción cruzada entre rango etario y macro-región geográfica, definiendo arquetipos poblacionales homogéneos.")
    
    add_paragraph(doc, "3. Filtrar la información: El filtrado de datos abordó tres problemáticas críticas de sesgo y calidad: (a) Se filtraron cuentas secundarias ('DISPONENT') para no duplicar el consumo familiar; (b) Se aplicó un filtro de Pareto para mitigar el sesgo por hiperactividad y antigüedad; y (c) Se implementaron compuertas de solvencia crediticia para descartar clientes en mora histórica. En Financial_ijs, las frecuencias transaccionales siguen una distribución asimétrica de ley de potencias (asimetría g_1 > 3.5). Para estabilizar esta varianza extrema y comprimir la escala sin alterar el orden relativo, se aplicó la transformación logarítmica monótona cóncava:")
    add_block_math(doc, r"y_{u, i} = \ln(1 + x_{u, i})")
    add_paragraph(doc, "donde x_{u, i} representa el recuento bruto de operaciones del cliente u en el producto i. Posteriormente, se escalaron linealmente los valores al rango continuo [1.0, 5.0]:")
    add_block_math(doc, r"r_{u, i} = 1.0 + 4.0 \cdot \left(\frac{y_{u, i} - y_{\min}}{y_{\max} - y_{\min}}\right) \approx 1.0 + 0.822 \cdot \ln(1 + x_{u, i})")
    
    add_paragraph(doc, "4. Modelar productos, comportamientos y perfiles: Con los DataFrames organizados, clasificados y filtrados, se parametrizaron las tres entidades del ecosistema bancario: (a) Modelado de Productos: Atributos contractuales de plazo, tasa y cláusulas legales vectorizadas mediante TF-IDF; (b) Modelado de Comportamientos: Matrices implícitas de co-ocurrencia transaccional, hábitos de débito automático y series temporales mensuales diferenciadas (Δx_t, 72 meses); y (c) Modelado de Perfiles: Arquetipos sociodemográficos distritales y espacios de características para localización de gemelos comportamentales (kNN).")
    
    add_paragraph(doc, "Trazabilidad de dos clientes reales (#2 y #45): La Tabla 2 ilustra el recorrido completo a través de las etapas de transformación matemática, permitiendo auditar el cálculo exacto de ratings implícitos y predicciones de Slope One:")
    
    tbl2_headers = ["Cliente ID", "Producto Financiero", "Frecuencia Bruta (x)", "Tras log(1+x)", "Rating Escalado r_{u,i} [1, 5]", "Desviaciones Slope One (b_{j,i})", "Predicción Final / Estado"]
    tbl2_rows = [
        ["Cliente #2", "TARJETA_DEBITO", "172 retiros", "5.1533", "4.67", "— (Posee el producto)", "Activo recurrente"],
        ["Cliente #2", "SERVICIOS_HOGAR", "65 pagos", "4.1897", "3.88", "— (Posee el producto)", "Activo recurrente"],
        ["Cliente #2", "PRESTAMO", "24 cuotas", "3.2189", "3.08", "— (Posee el producto)", "Activo recurrente"],
        ["Cliente #2", "SEGURO", "0 transacciones", "0.0000", "No observado", "+0.5687 / -0.0024 / -0.4546", "4.01 (Recomendado Prioritario)"],
        ["Cliente #2", "TRANSF_EXTERNA", "0 transacciones", "0.0000", "No observado", "+0.6370 / -0.0844 / -0.3550", "4.03 (Sugerido Complementario)"],
        ["Cliente #45", "TRANSF_EXTERNA", "84 envíos", "4.4427", "4.09", "— (Posee el producto)", "Activo recurrente"],
        ["Cliente #45", "TARJETA_DEBITO", "52 retiros", "3.9703", "3.70", "— (Posee el producto)", "Activo recurrente"],
        ["Cliente #45", "PRESTAMO", "36 cuotas", "3.6109", "3.43", "— (Posee el producto)", "Activo recurrente"],
        ["Cliente #45", "SERVICIOS_HOGAR", "0 transacciones", "0.0000", "No observado", "+0.5006 / -0.4522 / +0.0844", "3.53 (Sugerido Secundario)"],
        ["Cliente #45", "SEGURO", "0 transacciones", "0.0000", "No observado", "+0.5687 / -0.4546 / +0.1876", "3.78 (Recomendado Prioritario)"]
    ]
    add_table(doc, "Tabla 2: Recorrido de Dos Clientes Reales a través de la Preparación y Predicción Matricial.", tbl2_headers, tbl2_rows, [Inches(0.8), Inches(1.1), Inches(0.8), Inches(0.7), Inches(0.8), Inches(1.0), Inches(0.91)])
    
    add_paragraph(doc, "Auditoría matemática detallada de los cálculos en la Tabla 2:")
    add_bullet(doc, "Para Cliente #2, las calificaciones implícitas conocidas son: Tarjeta = 4.67 (x = 172 retiros), Hogar = 3.88 (x = 65 débitos) y Préstamo = 3.08 (x = 24 amortizaciones). Al predecir SEGURO a partir de las desviaciones canónicas de la Tabla 5 (b(Seguro, Préstamo) = +0.5687 con S = 114; b(Seguro, Hogar) = -0.0024 con S = 532; b(Seguro, Tarjeta) = -0.4546 con S = 532):", "Cliente #2 (Cálculo de Seguro):")
    add_block_math(doc, r"\hat{r}_{2, \text{Seguro}} = \frac{114(3.08 + 0.5687) + 532(3.88 - 0.0024) + 532(4.67 - 0.4546)}{114 + 532 + 532} = \frac{415.9318 + 2062.9232 + 2242.5768}{1178} = \frac{4721.4318}{1178} = \mathbf{4.0080} \approx \mathbf{4.01}")
    add_bullet(doc, "Para Cliente #2, al predecir TRANSF_EXTERNA utilizando las desviaciones correspondientes (b(Transf, Préstamo) = +0.6370 con S = 233; b(Transf, Hogar) = -0.0844 con S = 1197; b(Transf, Tarjeta) = -0.3550 con S = 1197):", "Cliente #2 (Cálculo de Transferencia Externa):")
    add_block_math(doc, r"\hat{r}_{2, \text{Transf}} = \frac{233(3.08 + 0.6370) + 1197(3.88 - 0.0844) + 1197(4.67 - 0.3550)}{233 + 1197 + 1197} = \frac{866.0610 + 4543.3332 + 5165.0550}{2627} = \frac{10574.4492}{2627} = \mathbf{4.0253} \approx \mathbf{4.03}")
    add_paragraph(doc, "Interpretación de Cliente #2: Ambos productos presentan una afinidad estimada sobresaliente (4.01 y 4.03). Aunque Transferencia Externa arroja un score aritmético marginalmente superior (4.03 vs 4.01), el comité de producto prioriza comercialmente SEGURO (4.01) debido a que representa un producto de cobertura patrimonial con un margen de contribución financiera sustancialmente más elevado para la institución bancaria.")
    
    add_bullet(doc, "Para Cliente #45, los ratings implícitos escalados calculados con la misma fórmula lineal resultan en: Préstamo = 3.43 (x = 36 cuotas, y = 3.6109), Tarjeta = 3.70 (x = 52 retiros, y = 3.9703) y Transferencia = 4.09 (x = 84 envíos, y = 4.4427). Evaluando la predicción para SERVICIOS_HOGAR tomando los signos rigurosos de la Tabla 5 (b(Hogar, Préstamo) = +0.5006 con S = 468; b(Hogar, Tarjeta) = -0.4522 con S = 3365; b(Hogar, Transf) = +0.0844 con S = 1197):", "Cliente #45 (Cálculo de Servicios del Hogar):")
    add_block_math(doc, r"\hat{r}_{45, \text{Hogar}} = \frac{468(3.43 + 0.5006) + 3365(3.70 - 0.4522) + 1197(4.09 + 0.0844)}{468 + 3365 + 1197} = \frac{1839.5608 + 10928.8970 + 4996.7728}{5030} = \frac{17765.2306}{5030} = \mathbf{3.5319} \approx \mathbf{3.53}")
    add_bullet(doc, "Evaluando ahora la predicción para SEGURO para Cliente #45 con los valores de la Tabla 5 (b(Seguro, Préstamo) = +0.5687 con S = 114; b(Seguro, Tarjeta) = -0.4546 con S = 532; b(Seguro, Transf) = +0.1876 con S = 531):", "Cliente #45 (Cálculo de Seguro):")
    add_block_math(doc, r"\hat{r}_{45, \text{Seguro}} = \frac{114(3.43 + 0.5687) + 532(3.70 - 0.4546) + 531(4.09 + 0.1876)}{114 + 532 + 531} = \frac{455.8318 + 1726.5528 + 2271.4356}{1177} = \frac{4453.8202}{1177} = \mathbf{3.7840} \approx \mathbf{3.78}")
    add_paragraph(doc, "Demostración de la inversión del orden en Cliente #45: En modelos aditivos simples no ponderados por soporte o que arrastran signos incorrectos, Servicios del Hogar parecía predominar. Sin embargo, al aplicar rigurosamente las desviaciones con soporte de la Tabla 5, la predicción de SEGURO (3.78) supera de manera concluyente a la de SERVICIOS_HOGAR (3.53). Esto demuestra el poder de Slope One: a pesar de que el cliente no tiene débitos domésticos, su fuerte volumen en transferencias y tarjetas, combinado con su condición de prestatario, genera una señal de propensión prioritaria hacia seguros de protección crediticia.")
    
    add_paragraph(doc, "Las variables operacionales y transformadas se resumen en el diccionario analítico de la Tabla 3:")
    
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
    
    add_paragraph(doc, "Evaluación de viabilidad técnica (5 Algoritmos × 4 DataFrames): No todos los algoritmos son aplicables de forma válida sobre todos los conjuntos. La viabilidad técnica depende directamente de la granularidad y la naturaleza de las variables. La Tabla 4 documenta la matriz de viabilidad sobre las 20 combinaciones posibles:")
    
    tbl4_headers = ["DataFrame Base", "1. Slope One", "2. Similitud Coseno", "3. Correlación Pearson", "4. TF-IDF (Contenidos)", "5. Demográfico (Estereotipos)"]
    tbl4_rows = [
        ["df_transacciones\n(1,056,320 movs)", "SELECCIONADO (1A)\nMasa crítica de transacciones repetidas cliente-producto.", "SELECCIONADO (1B)\nCoseno ajustado sobre vectores centrados en medias.", "COMPLEMENTARIO (1C)\nSeries mensuales diferenciadas (Δx_t) para aislar covariaciones.", "NO APLICABLE\nNo contiene texto descriptivo; solo importes y fechas.", "VIABLE (Vía JOIN)\nRequiere desnormalizar atributos sociodemográficos."],
        ["df_ordenes\n(6,471 órdenes)", "VIABLE (Secundario)\nMenor varianza de frecuencias que en transacciones diarias.", "SELECCIONADO (2A)\nMatriz binaria limpia de co-contratación de débitos fijos.", "COMPLEMENTARIO (2C)\nCorrelación de adopción de órdenes fijas entre cuentas.", "SELECCIONADO (2B: ITF)\nPonderación logarítmica de frecuencia inversa de ítems.", "VIABLE (Vía JOIN)\nAgregación de órdenes promedio por perfil."],
        ["df_prestamos\n(682 créditos)", "INVÁLIDO (Degenerado)\nClientes poseen un único crédito; soporte conjunto card(S(j,i)) ≈ 0.", "COMPLEMENTARIO (3B)\nProximidad numérica sobre condiciones [monto, plazo, cuota].", "SECUNDARIO\nVolumen mensual de concesión; muestra reducida (682 filas).", "SELECCIONADO (3A)\nCláusulas contractuales, garantías y condiciones de crédito.", "SELECCIONADO (3C: Utilidad)\nReglas de scoring de riesgo y cuota ≤ 30% salario."],
        ["df_cliente_consolidado\n(5,369 clientes)", "NO APLICABLE\nVariables estáticas de usuario; no representa matriz de ítems.", "SELECCIONADO (4B)\nSimilitud Coseno Usuario a Usuario (gemelos financieros).", "COMPLEMENTARIO (4C)\nCorrelación multivariante de perfil (edad, saldo, salario).", "NO APLICABLE\nAtributos numéricos y discretos; no posee corpus textual.", "SELECCIONADO (4A)\nDimensión maestra para construir arquetipos de negocio."]
    ]
    add_table(doc, "Tabla 4: Matriz Cruzada de Viabilidad Técnica (5 Algoritmos × 4 DataFrames).", tbl4_headers, tbl4_rows, [Inches(1.2), Inches(1.0), Inches(1.0), Inches(1.0), Inches(1.0), Inches(0.91)])
