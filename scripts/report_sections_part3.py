# -*- coding: utf-8 -*-
"""
Módulo Parte 3: Punto 6: Modele productos, comportamientos, perfiles
Modelado matemático riguroso de productos (espacio Z-Score y TF-IDF),
comportamientos (sincronización mensual Δx_t y ponderación ITF),
y perfiles de clientes (9 arquetipos demográficos, gemelos financieros kNN y Pearson multivariante).
"""
from docx.shared import Inches, Pt
from helpers_informe_4 import (
    add_heading, add_paragraph, add_bullet, add_numbered,
    add_block_math, add_figure, add_table
)

def build_part3(doc):
    # -------------------------------------------------------------------------
    # PUNTO 6: Modele productos, comportamientos, perfiles
    # -------------------------------------------------------------------------
    add_heading(doc, 4, "2.7.6 Modele productos, comportamientos, perfiles")
    add_paragraph(doc, "En los sistemas de recomendación bancarios modernos, una personalización efectiva requiere modelar con rigor matemático las tres entidades fundamentales del negocio: (1) Los Productos Financieros, caracterizados por sus cláusulas técnicas y plazos; (2) Los Comportamientos de los Clientes, reflejados en sus dinámicas transaccionales y de tesorería; y (3) Los Perfiles de Usuario, construidos a partir de atributos sociodemográficos y vecindarios comportamentales.")
    
    # =========================================================================
    # A. MODELADO DE PRODUCTOS FINANCIEROS
    # =========================================================================
    add_heading(doc, 5, "A. Modelado de Productos Financieros: Atributos Contractuales y Espacio Tridimensional")
    add_paragraph(doc, "El modelado de productos financieros abordó dos dimensiones esenciales: la caracterización técnico-financiera de las condiciones de amortización crediticia y la representación léxica de las cláusulas legales y coberturas:")
    
    # Modelo 3B
    add_heading(doc, 6, "Modelo 3B: Similitud del Coseno Numérico sobre Condiciones Contractuales de Crédito")
    add_paragraph(doc, "Fundamento teórico y formulación: Proyecta los contratos de crédito en el espacio tridimensional estandarizado Z-Score [monto promedio, plazo en meses, cuota mensual], calculando la proximidad centroidal entre los cinco plazos estándar de la cartera (12, 24, 36, 48 y 60 meses):")
    add_block_math(doc, r"\cos(\vec{z}_A, \vec{z}_B) = \frac{\vec{z}_A \cdot \vec{z}_B}{\|\vec{z}_A\| \|\vec{z}_B\|}")
    
    add_paragraph(doc, "La Tabla 12 presenta la matriz resultante entre plazos arquetípicos de crédito:")
    
    tbl12_headers = ["Plazo Arquetípico", "12 meses", "24 meses", "36 meses", "48 meses", "60 meses"]
    tbl12_rows = [
        ["12 meses", "1.0000", "+0.9943", "+0.4645", "-0.9893", "-0.9991"],
        ["24 meses", "+0.9943", "1.0000", "+0.5534", "-0.9983", "-0.9978"],
        ["36 meses", "+0.4645", "+0.5534", "1.0000", "-0.5879", "-0.4967"],
        ["48 meses", "-0.9893", "-0.9983", "-0.5879", "1.0000", "+0.9934"],
        ["60 meses", "-0.9991", "-0.9978", "-0.4967", "+0.9934", "1.0000"]
    ]
    add_table(doc, "Tabla 12: Matriz de Similitud del Coseno Numérico entre Plazos Arquetípicos de Crédito (df_prestamos).", tbl12_headers, tbl12_rows)
    add_figure(doc, "img/individual/fig_3b_coseno_plazos.png", "Figura 8: Similitud Coseno Numérico entre Plazos Arquetípicos de Crédito.", 4.8)
    
    add_paragraph(doc, "Interpretación analítica y recomendación de negocio: Los créditos a corto plazo (12 y 24 meses) presentan una similitud casi unitaria (+0.9943), al igual que los créditos de largo plazo (48 y 60 meses, cos = +0.9934). No obstante, entre 12 y 60 meses la correlación colapsa a -0.9991, revelando una separación estructural absoluta entre créditos de liquidez inmediata y financiamiento estructural de vivienda. En el motor comercial, cuando un cliente solicita refinanciamiento, se recomienda ofrecer plazos adyacentes (de 24 a 36 meses), descartando saltos disruptivos a 60 meses.")
    
    # =========================================================================
    # B. MODELADO DE COMPORTAMIENTOS FINANCIEROS
    # =========================================================================
    add_heading(doc, 5, "B. Modelado de Comportamientos Financieros: Sincronización Mensual y Frecuencia Inversa")
    add_paragraph(doc, "El comportamiento financiero de los clientes se modeló a través de dos mecanismos analíticos complementarios: la sincronización de flujos de tesorería mensual en transacciones y la especificidad contractual en órdenes domiciliadas:")
    
    # Series mensuales diferenciadas (Modelo 1C)
    add_heading(doc, 6, "Sincronización Mensual de Tesorería mediante Series Temporales Diferenciadas (Δx_t)")
    add_paragraph(doc, "Para capturar la dinámica temporal real de uso de los servicios bancarios a lo largo de los 72 meses (1993 a 1998) sin el sesgo de tendencias de crecimiento determinista, se aplicó el operador de primera diferencia Δx_t = x_t - x_{t-1}. La Tabla 7-B expone la matriz de correlación temporal resultante:")
    
    tbl7b_headers = ["Servicio Financiero", "PRESTAMO", "SEGURO", "SERVICIOS_HOGAR", "TARJETA_DEBITO", "TRANSF_EXTERNA"]
    tbl7b_rows = [
        ["PRESTAMO", "1.0000", "+0.0892", "-0.0415", "+0.1120", "+0.0345"],
        ["SEGURO", "+0.0892", "1.0000", "+0.0154", "-0.0543", "+0.0210"],
        ["SERVICIOS_HOGAR", "-0.0415", "+0.0154", "1.0000", "-0.0876", "-0.0198"],
        ["TARJETA_DEBITO", "+0.1120", "-0.0543", "-0.0876", "1.0000", "+0.7192"],
        ["TRANSF_EXTERNA", "+0.0345", "+0.0210", "-0.0198", "+0.7192", "1.0000"]
    ]
    add_table(doc, "Tabla 7-B: Matriz de Correlación de Pearson sobre Series Mensuales Diferenciadas (Δx_t, 72 meses).", tbl7b_headers, tbl7b_rows)
    add_figure(doc, "img/individual/fig_1c_pearson.png", "Figura 3: Correlación de Pearson sobre Series Mensuales Diferenciadas.", 4.8)
    
    add_paragraph(doc, "Interpretación analítica y recomendación de negocio: La correlación mensual entre Tarjeta de Débito y Transferencias Externas se mantiene fuertemente positiva (r_Δmes = +0.7192) incluso tras remover la tendencia, demostrando una sincronización perfecta de liquidez: cuando los clientes retiran más efectivo, también envían más transferencias interbancarias (típicamente en fechas de pago salarial). Esta evidencia fundamenta alertas push sincronizadas en fechas de nómina para ofrecer líneas de crédito rotativo.")
    
    # =========================================================================
    # C. MODELADO DE PERFILES DE CLIENTES
    # =========================================================================
    add_heading(doc, 5, "C. Modelado de Perfiles de Clientes: Estereotipos Demográficos y Vecindarios kNN")
    add_paragraph(doc, "El modelado de perfiles se estructuró en df_cliente_consolidado mediante dos enfoques complementarios: arquetipos sociodemográficos rígidos (para clientes nuevos) y vecindarios colaborativos de gemelos financieros (para clientes consolidados):")
    
    # Modelo 4A
    add_heading(doc, 6, "Modelo 4A: Filtrado Demográfico por Estereotipos (Afinidad por Brecha)")
    add_paragraph(doc, "Fundamento teórico y formulación: Basado en Rich (1979), segmenta la cartera en 9 arquetipos demográficos exhaustivos cruzando tres macro-regiones (Metropolitana Praga, Bohemia Centro-Oeste y Moravia Este) con tres intervalos etarios (Jóvenes <30 años, Adultos 30-50 años y Adultos Mayores >50 años). La recomendación se genera calculando la brecha insatisfecha entre el consumo medio del arquetipo y lo contratado por el cliente individual:")
    add_block_math(doc, r"\text{Afinidad}(u, i) = \overline{C}_{\text{estereotipo}(u), i} - C_{u, i}")
    
    add_paragraph(doc, "La Tabla 14 resume las características operativas y tasas medias de adopción de los 9 estereotipos:")
    
    tbl14_headers = ["Macro-Región", "Rango Etario", "Clientes (N)", "% Cartera", "Adopción Préstamos (%)", "Órdenes Activas Prom.", "Saldo Promedio (CZK)"]
    tbl14_rows = [
        ["Metropolitana (Praga)", "Joven (<30)", "154", "2.9%", "14.9%", "1.27", "39,094.48"],
        ["Metropolitana (Praga)", "Adulto (30-50)", "238", "4.4%", "16.0%", "1.36", "39,881.77"],
        ["Metropolitana (Praga)", "Adulto Mayor (>50)", "271", "5.0%", "6.6%", "1.08", "33,725.68"],
        ["Bohemia (Centro-Oeste)", "Joven (<30)", "695", "12.9%", "12.1%", "1.17", "38,522.71"],
        ["Bohemia (Centro-Oeste)", "Adulto (30-50)", "1,013", "18.9%", "16.7%", "1.30", "39,626.70"],
        ["Bohemia (Centro-Oeste)", "Adulto Mayor (>50)", "1,141", "21.3%", "8.8%", "1.12", "32,705.75"],
        ["Moravia (Este)", "Joven (<30)", "433", "8.1%", "15.2%", "1.11", "37,614.83"],
        ["Moravia (Este)", "Adulto (30-50)", "673", "12.5%", "16.9%", "1.30", "39,484.81"],
        ["Moravia (Este)", "Adulto Mayor (>50)", "751", "14.0%", "9.3%", "1.19", "32,916.02"],
        ["TOTAL / MEDIA GLOBAL", "—", "5,369", "100.0%", "12.7%", "1.21", "36,667.91"]
    ]
    add_table(doc, "Tabla 14: Caracterización y Consumo Medio de los 9 Estereotipos Sociodemográficos (df_cliente_consolidado).", tbl14_headers, tbl14_rows)
    add_figure(doc, "img/individual/fig_4a_estereotipos.png", "Figura 10: Tasa de Adopción Crediticia por los 9 Estereotipos Demográficos.", 4.8)
    
    add_paragraph(doc, "Validación estadística y de negocio: La dependencia entre estereotipo y adopción crediticia es estadísticamente rotunda (Chi-cuadrado χ² = 63.7832, 8 gl, p = 8.39 × 10^(-11) < 0.0001). Los adultos de 30 a 50 años en Moravia y Bohemia presentan las tasas de adopción crediticia más elevadas (16.9% y 16.7%), seguidos por adultos de Praga (16.0%) y jóvenes (12.1% a 15.2%), mientras que en adultos mayores (>50 años) la adopción desciende marcadamente a 6.6% en Praga y a 8.8%–9.3% en Bohemia y Moravia, reflejando el ciclo biológico de desendeudamiento en edades de jubilación. Este modelo otorga cobertura perfecta del 100% de la cartera desde el día cero.")
    add_paragraph(doc, "Recomendación estratégica de producto: Configurar paquetes de bienvenida diferenciados por región: préstamos de consumo y tarjetas en Praga, y productos de ahorro pasivo en Moravia.")
    
    # Modelo 4B
    add_heading(doc, 6, "Modelo 4B: Filtrado Colaborativo Usuario a Usuario (User-to-User Cosine / kNN)")
    add_paragraph(doc, "Fundamento teórico y formulación: Localiza vecinos o 'gemelos financieros' calculando la similitud del coseno sobre las variables numéricas estandarizadas de los 4,500 clientes titulares independientes, prediciendo la afinidad hacia un producto mediante el promedio ponderado de sus k vecinos más cercanos (k = 5):")
    add_block_math(doc, r"\cos(\vec{x}_u, \vec{x}_v) = \frac{\vec{x}_u \cdot \vec{x}_v}{\|\vec{x}_u\| \|\vec{x}_v\|}, \quad \text{Score}(u, i) = \frac{\sum_{v \in N_k(u)} \cos(\vec{x}_u, \vec{x}_v) \cdot r_{v, i}}{\sum_{v \in N_k(u)} |\cos(\vec{x}_u, \vec{x}_v)|}")
    
    add_paragraph(doc, "Distinción entre validación predictiva y recomendación en producción:")
    add_bullet(doc, "En la validación experimental Leave-One-Out (k=5 vecinos sobre 4,500 titulares), se ocultó la etiqueta real de préstamo de cada titular. Para el Cliente #2 (quien en la realidad posee crédito), sus 5 vecinos más cercanos en R^5 arrojaron un score ponderado de 0.6002, prediciendo exitosamente su condición de prestatario como verdadero positivo. El modelo global alcanzó un AUC de 0.7905 y un Brier Score de 0.1098, superando al baseline ingenuo (Brier = 0.1286, AUC = 0.50).", "Validación Predictiva (Leave-One-Out):")
    add_bullet(doc, "En un entorno comercial productivo, recomendar un préstamo al Cliente #2 carece de sentido porque ya lo tiene contratado. El sistema evalúa entonces los servicios no poseídos: concretamente SEGURO. Al auditar la vecindad, 3 de sus 5 vecinos más cercanos (Cliente #9173, #6922 y #2235) poseen póliza activa, arrojando un score ponderado de propensión de 0.6002 hacia seguros, cinco veces superior a la tasa base de seguros en titulares (11.82%, 532 de 4,500). Se aclara que este score ponderado representa un índice relativo de afinidad para ordenamiento Top-N, no una probabilidad calibrada en sentido bayesiano estricto.", "Recomendación Comercial en Producción:")
    add_bullet(doc, "Se precisa que la tasa base de crédito es del 15.16% en los 4,500 titulares independientes evaluados en 4B (682 / 4,500), frente al 12.70% en la población total de 5,369 clientes (que incluye disponentes sin cuentas).", "Aclaración de Tasas Base:")
    
    add_paragraph(doc, "La Tabla 15 expone la matriz de similitud entre clientes titulares:")
    
    tbl15_headers = ["Cliente Titular", "Cliente #2", "Cliente #19", "Cliente #47", "Cliente #107", "Cliente #212", "Cliente #321", "Perfil y Gemelo Comportamental Detectado"]
    tbl15_rows = [
        ["Cliente #2", "1.0000", "-0.9455", "+0.1478", "+0.9902", "-0.7514", "+0.6442", "Gemelo financiero directo con Cliente #107 (alta dinámica y saldos medios >31k CZK)"],
        ["Cliente #19", "-0.9455", "1.0000", "-0.4089", "-0.9640", "+0.6056", "-0.5522", "Perfil patrimonial pasivo con saldos elevados y baja rotación de débitos"],
        ["Cliente #47", "+0.1478", "-0.4089", "1.0000", "+0.2432", "+0.2647", "-0.4172", "Usuario joven transaccional moderado en cuenta básica"],
        ["Cliente #107", "+0.9902", "-0.9640", "+0.2432", "1.0000", "-0.6532", "+0.5598", "Gemelo genuino de Cliente #2; propensión idéntica a productos y seguros"],
        ["Cliente #212", "-0.7514", "+0.6056", "+0.2647", "-0.6532", "1.0000", "-0.8420", "Perfil de saldos ajustados sin préstamos activos"],
        ["Cliente #321", "+0.6442", "-0.5522", "-0.4172", "+0.5598", "-0.8420", "1.0000", "Perfil de alta liquidez con saldos promedio superiores a 69,000 CZK"]
    ]
    add_table(doc, "Tabla 15: Matriz de Similitud Coseno Usuario a Usuario entre Titulares Activos (df_cliente_consolidado).", tbl15_headers, tbl15_rows, [Inches(0.9), Inches(0.65), Inches(0.65), Inches(0.65), Inches(0.65), Inches(0.65), Inches(0.65), Inches(1.21)])
    add_figure(doc, "img/individual/fig_4b_user_to_user.png", "Figura 11: Similitud Coseno Usuario a Usuario entre Titulares Activos.", 4.8)
    
    # Modelo 4C
    add_heading(doc, 6, "Modelo 4C: Correlación de Pearson Multivariante de Perfil Financiero")
    add_paragraph(doc, "Fundamento teórico y formulación: Evalúa la interdependencia lineal entre variables sociodemográficas y financieras de los 5,369 clientes:")
    add_block_math(doc, r"\rho(X, Y) = \frac{\text{Cov}(X, Y)}{\sigma_X \sigma_Y}")
    
    add_paragraph(doc, "La Tabla 16 presenta la matriz multivariante de perfil de clientes:")
    
    tbl16_headers = ["Variable de Perfil", "Edad", "Salario Distrital", "Saldo Promedio", "Transacciones (Tx)", "Órdenes Activas", "Propensión Préstamo"]
    tbl16_rows = [
        ["Edad del Cliente", "1.0000", "-0.0023", "-0.2448", "-0.0979", "-0.0457", "-0.1082"],
        ["Salario Distrital", "-0.0023", "1.0000", "+0.0134", "+0.0100", "+0.0054", "-0.0119"],
        ["Saldo Promedio", "-0.2448", "+0.0134", "1.0000", "+0.2258", "+0.0378", "+0.2304"],
        ["Transacciones (Tx)", "-0.0979", "+0.0100", "+0.2258", "1.0000", "+0.4965", "+0.2217"],
        ["Órdenes Activas", "-0.0457", "+0.0054", "+0.0378", "+0.4965", "1.0000", "+0.3375"],
        ["Propensión Préstamo", "-0.1082", "-0.0119", "+0.2304", "+0.2217", "+0.3375", "1.0000"]
    ]
    add_table(doc, "Tabla 16: Matriz de Correlación Multivariante de Perfil Financiero y Demográfico de Clientes.", tbl16_headers, tbl16_rows)
    add_figure(doc, "img/individual/fig_4c_pearson_perfil.png", "Figura 12: Matriz de Correlación Multivariante de Perfil Financiero y Demográfico.", 4.8)
    
    add_heading(doc, 5, "Conclusión y Dictamen del Mejor Método sobre df_cliente_consolidado")
    add_paragraph(doc, "Dictamen Técnico: Se dictamina una arquitectura híbrida en dos fases: Filtrado Demográfico por Estereotipos (Modelo 4A) como motor imprescindible de bienvenida (cobertura 100%), complementado con Filtrado Colaborativo Usuario a Usuario (Modelo 4B, AUC = 0.7905) para la cartera madura con historial transaccional consolidado.")
