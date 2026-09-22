# -*- coding: utf-8 -*-
"""
Módulo Parte 4: Punto 7 (Ítem a Ítem: Cosenos y Pearson), Punto 8 (Basado en Contenidos y Utilidad),
Evaluación Comparativa Global, Descarte Empírico, MLOps, Conclusiones y Anexos A-E.
"""
from docx.shared import Inches, Pt
from helpers_informe_4 import (
    add_heading, add_paragraph, add_bullet, add_numbered,
    add_block_math, add_figure, add_table, add_checkbox
)

def build_part4(doc):
    # -------------------------------------------------------------------------
    # PUNTO 7: Sistema de recomendación item to item (similitud de cosenos y Pearson)
    # -------------------------------------------------------------------------
    add_heading(doc, 4, "2.7.7 Sistema de recomendación item to item (similitud de cosenos y Pearson)")
    add_paragraph(doc, "Los sistemas de recomendación ítem a ítem (Item-to-Item Collaborative Filtering) operan bajo el principio de que la afinidad entre dos productos puede estimarse cuantificando el grado de coincidencia o correlación en los patrones de consumo de los clientes comunes. En esta práctica se implementaron modelos basados en proximidad angular (Similitud del Coseno) y en interdependencia lineal (Correlación de Pearson) sobre los DataFrames de transacciones (df_transacciones) y órdenes domiciliadas (df_ordenes):")
    
    # =========================================================================
    # A. SIMILITUD DE COSENOS ÍTEM A ÍTEM
    # =========================================================================
    add_heading(doc, 5, "A. Sistemas Ítem a Ítem Basados en Similitud del Coseno")
    
    # Modelo 1B
    add_heading(doc, 6, "Modelo 1B: Similitud del Coseno Ajustado sobre Calificaciones de Transacciones")
    add_paragraph(doc, "Fundamento teórico y formulación: Cuando las calificaciones son estrictamente positivas, el coseno tradicional se comprime en valores elevados. El Coseno Ajustado (Sarwar et al., 2001) resta a cada calificación la media personal del usuario bar{r}_u, expandiendo el rango a [-1.0, +1.0]:")
    add_block_math(doc, r"\cos_{\text{adj}}(\vec{p}_A, \vec{p}_B) = \frac{\sum_{u \in U} (r_{u, A} - \bar{r}_u)(r_{u, B} - \bar{r}_u)}{\sqrt{\sum_{u \in U} (r_{u, A} - \bar{r}_u)^2} \cdot \sqrt{\sum_{u \in U} (r_{u, B} - \bar{r}_u)^2}}")
    
    add_paragraph(doc, "La Tabla 6 presenta la matriz del Coseno Ajustado sobre los 3,653 clientes activos de df_transacciones:")
    
    tbl6_headers = ["Producto Financiero", "PRESTAMO", "SEGURO", "SERVICIOS_HOGAR", "TARJETA_DEBITO", "TRANSF_EXTERNA"]
    tbl6_rows = [
        ["PRESTAMO", "1.0000", "+0.0229", "-0.0003", "-0.7507", "-0.1433"],
        ["SEGURO", "+0.0229", "1.0000", "+0.3360", "-0.2791", "-0.3107"],
        ["SERVICIOS_HOGAR", "-0.0003", "+0.3360", "1.0000", "-0.5401", "-0.2644"],
        ["TARJETA_DEBITO", "-0.7507", "-0.2791", "-0.5401", "1.0000", "+0.0768"],
        ["TRANSF_EXTERNA", "-0.1433", "-0.3107", "-0.2644", "+0.0768", "1.0000"]
    ]
    add_table(doc, "Tabla 6: Matriz de Similitud del Coseno Ajustado entre Servicios Financieros (df_transacciones).", tbl6_headers, tbl6_rows)
    add_figure(doc, "img/individual/fig_1b_coseno.png", "Figura 2: Matriz de Similitud del Coseno Ajustado Centrado en Medias.", 4.8)
    
    add_paragraph(doc, "Interpretación analítica y de negocio: La asociación positiva más destacada ocurre entre Seguro y Servicios del Hogar (+0.3360), reflejando que los clientes con disciplina de pagos domésticos tienen una disposición natural hacia pólizas de seguro. En contraste, Tarjeta de Débito exhibe correlaciones fuertemente negativas con Préstamo (-0.7507) y Hogar (-0.5401).")
    
    # Modelo 2A
    add_heading(doc, 6, "Modelo 2A: Similitud del Coseno Binario sobre Órdenes Domiciliadas")
    add_paragraph(doc, "Fundamento teórico y formulación: Sobre los contratos de débito permanente en df_ordenes, la interacción es binaria (posee o no posee orden). La similitud de co-adquisición se formula como el producto escalar normalizado:")
    add_block_math(doc, r"\cos(\vec{a}, \vec{b}) = \frac{\vec{a} \cdot \vec{b}}{\|\vec{a}\| \|\vec{b}\|} = \frac{|U_a \cap U_b|}{\sqrt{|U_a| \cdot |U_b|}}")
    
    add_paragraph(doc, "Métricas de reglas de asociación y Lift: El soporte conjunto del par {Seguro, Hogar} es de 532 cuentas sobre 3,758 activas. El Lift asociado resulta:")
    add_block_math(doc, r"\text{Lift}(\text{Seguro} \to \text{Hogar}) = \frac{P(\text{Seguro} \cap \text{Hogar})}{P(\text{Seguro}) \cdot P(\text{Hogar})} = \frac{532 / 3758}{(532 / 3758) \cdot (3365 / 3758)} = \frac{3758}{3365} \approx \mathbf{1.12}")
    add_paragraph(doc, "Un Lift de 1.12 confirma una asociación estadística positiva pero débil entre ambos servicios contractuales.")
    
    add_paragraph(doc, "La Tabla 8 detalla la matriz de similitud del coseno binario en df_ordenes:")
    
    tbl8_headers = ["Categoría de Orden", "Leasing (Arrendamiento)", "Pago de Seguros", "Cuota de Préstamo", "Servicios del Hogar"]
    tbl8_rows = [
        ["Leasing (Arrendamiento)", "1.0000", "0.0000", "0.0000", "0.1866"],
        ["Pago de Seguros", "0.0000", "1.0000", "0.1975", "0.3976"],
        ["Cuota de Préstamo", "0.0000", "0.1975", "1.0000", "0.2936"],
        ["Servicios del Hogar", "0.1866", "0.3976", "0.2936", "1.0000"]
    ]
    add_table(doc, "Tabla 8: Matriz de Similitud del Coseno Binario entre Contratos Domiciliados (df_ordenes).", tbl8_headers, tbl8_rows)
    add_figure(doc, "img/individual/fig_2a_coseno_binario.png", "Figura 4: Matriz de Similitud del Coseno Binario de Co-adquisición en Órdenes.", 4.8)
    
    add_paragraph(doc, "Interpretación analítica y de negocio: El valor de 0.3976 entre Seguros y Hogar representa el techo geométrico posible para coberturas dispares (532 frente a 3,365 cuentas). El análisis revela una jerarquía anidada: Seguros (532) ⊂ Servicios del Hogar (3,365). El ratio Lift asociado es de 1.12, reflejando una asociación positiva pero débil: la co-ocurrencia apenas supera lo esperado por azar debido a la omnipresencia del débito doméstico (89.54% de cuentas). Por ende, el empaquetamiento (bundling) no se fundamenta en una fuerte sinergia espontánea, sino en una estrategia comercial deliberada para utilizar el débito del hogar como canal operativo natural de recaudación para seguros.")
    
    # Modelo 2B
    add_heading(doc, 6, "Modelo 2B: Ponderación de Frecuencia Inversa (ITF) para Rescate de Nichos")
    add_paragraph(doc, "Fundamento teórico y formulación: Para evitar que Servicios del Hogar monopolice las recomendaciones, se penaliza logarítmicamente a los productos masivos mediante el factor ITF:")
    add_block_math(doc, r"\text{ITF}(i) = \ln\left(\frac{N_{\text{cuentas}}}{n_i}\right), \quad \text{Score}(u, i) = \sum_{j \in I_u} \cos(\vec{a}_i, \vec{a}_j) \cdot \text{ITF}(i)")
    
    add_paragraph(doc, "La Tabla 9 documenta los factores de penalización ITF y las coberturas poblacionales:")
    
    tbl9_headers = ["Categoría Contractual", "Cuentas Activas", "Penetración (%)", "Factor ITF ln(N/n_i)", "Efecto de Ponderación"]
    tbl9_rows = [
        ["Servicios del Hogar", "3,365", "89.54%", "0.1105", "Fuerte penalización (ítem masivo trivial)"],
        ["Sin Especificar", "1,198", "31.88%", "1.1432", "Ponderación neutra intermedia"],
        ["Cuota de Préstamo", "717", "19.08%", "1.6566", "Rescate selectivo para prestatarios"],
        ["Pago de Seguros", "532", "14.16%", "1.9550", "Impulso prioritario de producto estratégico"],
        ["Leasing (Arrendamiento)", "117", "3.11%", "2.3998", "Máxima bonificación a producto de nicho"]
    ]
    add_table(doc, "Tabla 9: Factores de Ponderación Inversa (ITF) Calculados sobre Cuentas con Órdenes.", tbl9_headers, tbl9_rows)
    add_figure(doc, "img/individual/fig_2b_itf.png", "Figura 5: Similitud Coseno Ponderada por Frecuencia Inversa (ITF) en Órdenes.", 4.8)
    
    add_paragraph(doc, "Simulación comparativa de ordenamiento con y sin ITF: Considérese una cuenta activa que domicilia exclusivamente Cuota de Préstamo (717 cuentas). Bajo un recomendador no ponderado, el producto sugerido sería Servicios del Hogar (cos = 0.2936). Con ponderación ITF, el score de Seguros asciende a 0.1975 × 1.9550 = 0.3861, mientras que Servicios del Hogar se comprime a 0.2936 × 0.1105 = 0.0324 (reduciéndose en un factor de 9.05 veces frente a su valor no ponderado, resultando casi 12 veces menor que el score de Seguros: 0.0324 vs 0.3861). El orden se reestructura completamente, posicionando a Seguros en primer lugar absoluto.")
    
    add_heading(doc, 5, "Conclusión y Dictamen del Mejor Método sobre df_ordenes")
    add_paragraph(doc, "Dictamen Técnico: En órdenes domiciliadas, la Ponderación ITF (Modelo 2B) es el método ganador indiscutible frente al Coseno Binario simple (2A). Su capacidad para castigar la omnipresencia trivial de servicios básicos rescata productos de alto margen (Seguros y Leasing).")
    
    # =========================================================================
    # B. CORRELACIÓN DE PEARSON ÍTEM A ÍTEM
    # =========================================================================
    add_heading(doc, 5, "B. Sistemas Ítem a Ítem Basados en Correlación de Pearson")
    
    # Modelo 1C
    add_heading(doc, 6, "Modelo 1C: Correlación de Pearson sobre Ratings Continuos de Transacciones")
    add_paragraph(doc, "Fundamento teórico y formulación: Pearson evalúa la interdependencia lineal entre las calificaciones implícitas centradas:")
    add_block_math(doc, r"r(X, Y) = \frac{\sum (x_i - \bar{x})(y_i - \bar{y})}{\sqrt{\sum (x_i - \bar{x})^2} \cdot \sqrt{\sum (y_i - \bar{y})^2}}")
    
    add_paragraph(doc, "La Tabla 7-A expone la matriz de correlación de Pearson sobre calificaciones de transacciones:")
    
    tbl7a_headers = ["Servicio Financiero", "PRESTAMO", "SEGURO", "SERVICIOS_HOGAR", "TARJETA_DEBITO", "TRANSF_EXTERNA"]
    tbl7a_rows = [
        ["PRESTAMO", "1.0000", "+0.9634", "+0.8658", "+0.7303", "+0.7328"],
        ["SEGURO", "+0.9634", "1.0000", "+0.9686", "+0.9329", "+0.9388"],
        ["SERVICIOS_HOGAR", "+0.8658", "+0.9686", "1.0000", "+0.9856", "+0.9840"],
        ["TARJETA_DEBITO", "+0.7303", "+0.9329", "+0.9856", "1.0000", "+0.9957"],
        ["TRANSF_EXTERNA", "+0.7328", "+0.9388", "+0.9840", "+0.9957", "1.0000"]
    ]
    add_table(doc, "Tabla 7-A: Matriz de Correlación de Pearson sobre Calificaciones de Transacciones (df_transacciones).", tbl7a_headers, tbl7a_rows)
    
    add_paragraph(doc, "Trazabilidad manual paso a paso de Pearson entre Tarjeta de Débito y Transferencia Externa (r = +0.9957): Sobre los 1,197 clientes activos comunes, las medias de calificación son bar{x}_tarjeta = 4.3541 y bar{y}_transf = 3.9991. La covarianza muestral es Cov(X, Y) = 0.3845, con varianzas s_x² = 0.3892 y s_y² = 0.3831. Aplicando la fórmula:")
    add_block_math(doc, r"r = \frac{0.3845}{\sqrt{0.3892 \cdot 0.3831}} = \frac{0.3845}{\sqrt{0.1491}} = \frac{0.3845}{0.3861} = \mathbf{+0.9957}")
    
    # Modelo 2C
    add_heading(doc, 6, "Modelo 2C: Correlación de Pearson sobre Órdenes Domiciliadas")
    add_paragraph(doc, "La Tabla 10 documenta la correlación entre contratos domiciliados en df_ordenes:")
    
    tbl10_headers = ["Categoría de Contrato", "Leasing (Arrendamiento)", "Pago de Seguros", "Cuota de Préstamo", "Servicios del Hogar"]
    tbl10_rows = [
        ["Leasing (Arrendamiento)", "1.0000", "-0.0725", "-0.0867", "+0.0381"],
        ["Pago de Seguros", "-0.0725", "1.0000", "+0.0768", "-0.0345"],
        ["Cuota de Préstamo", "-0.0867", "+0.0768", "1.0000", "-0.4117"],
        ["Servicios del Hogar", "+0.0381", "-0.0345", "-0.4117", "1.0000"]
    ]
    add_table(doc, "Tabla 10: Matriz de Correlación de Pearson entre Órdenes Domiciliadas (df_ordenes).", tbl10_headers, tbl10_rows)
    add_figure(doc, "img/individual/fig_2c_pearson.png", "Figura 6: Matriz de Correlación de Pearson sobre Órdenes Domiciliadas.", 4.8)
    
    add_paragraph(doc, "Interpretación analítica: La correlación negativa entre Hogar y Préstamo (r = -0.4117) revela un fenómeno de exclusión presupuestaria: las cuentas que pagan cuotas crediticias reducen sus domiciliaciones domésticas en la entidad, alertando sobre estrés financiero.")
    
    # -------------------------------------------------------------------------
    # PUNTO 8: Sistema de recomendación basado en contenidos
    # -------------------------------------------------------------------------
    add_heading(doc, 4, "2.7.8 Sistema de recomendación basado en contenidos")
    add_paragraph(doc, "En df_prestamos, cada cliente posee estrictamente un crédito en la historia, provocando que los soportes conjuntos de co-ocurrencia sean nulos (|S(j, i)| = 0), lo que invalida cualquier filtrado colaborativo tradicional. El sistema de recomendación basado en contenidos supera esta limitación modelando el texto técnico y las cláusulas legales de los contratos bancarios:")
    
    # Modelo 3A
    add_heading(doc, 5, "Modelo 3A: Filtrado Basado en Contenidos con TF-IDF sobre Cláusulas Contractuales")
    add_paragraph(doc, "Fundamento teórico y formulación: Transforma el texto de los contratos en vectores de características léxicas bajo el Modelo de Espacio Vectorial (VSM):")
    add_block_math(doc, r"\text{TF-IDF}(t, d) = \text{TF}(t, d) \cdot \ln\left(\frac{1 + |D|}{1 + \text{DF}(t)}\right) + 1")
    add_block_math(doc, r"\text{Sim}(d_A, d_B) = \cos(\vec{w}_A, \vec{w}_B) = \frac{\vec{w}_A \cdot \vec{w}_B}{\|\vec{w}_A\| \|\vec{w}_B\|}")
    
    add_paragraph(doc, "La Tabla 11 presenta la matriz de similitud léxica TF-IDF sobre el catálogo de 8 productos arquetípicos:")
    
    tbl11_headers = ["Producto Financiero", "P01: Personal", "P02: Consumo", "P03: Hipoteca", "P04: PyME", "P05: Vida", "P06: Desgrav", "P07: Hogar", "P08: Leasing"]
    tbl11_rows = [
        ["P01: Personal", "1.0000", "0.1611", "0.1257", "0.0909", "0.0712", "0.0543", "0.0210", "0.0345"],
        ["P02: Consumo", "0.1611", "1.0000", "0.0892", "0.0654", "0.2116", "0.0876", "0.0616", "0.0541"],
        ["P03: Hipoteca", "0.1257", "0.0892", "1.0000", "0.1432", "0.0945", "0.1026", "0.0154", "0.0806"],
        ["P04: PyME", "0.0909", "0.0654", "0.1432", "1.0000", "0.0412", "0.0310", "0.0000", "0.0654"],
        ["P05: Vida y Salud", "0.0712", "0.2116", "0.0945", "0.0412", "1.0000", "0.2957", "0.0381", "0.0210"],
        ["P06: Desgravamen", "0.0543", "0.0876", "0.1026", "0.0310", "0.2957", "1.0000", "0.0198", "0.0154"],
        ["P07: Hogar", "0.0210", "0.0616", "0.0154", "0.0000", "0.0381", "0.0198", "1.0000", "0.0000"],
        ["P08: Leasing", "0.0345", "0.0541", "0.0806", "0.0654", "0.0210", "0.0154", "0.0000", "1.0000"]
    ]
    add_table(doc, "Tabla 11: Matriz de Similitud Léxica TF-IDF entre Cláusulas Contractuales de Productos Financieros.", tbl11_headers, tbl11_rows)
    add_figure(doc, "img/individual/fig_3a_tfidf.png", "Figura 7: Matriz de Similitud Léxica TF-IDF entre Cláusulas de Crédito.", 4.8)
    
    add_paragraph(doc, "Validación Leave-One-Product-Out (LOPO): Ocultando cada contrato, el motor recuperó con precisión del 100% (8 de 8 productos) a su contraparte complementaria más coherente en el Top-2 (P01 recupera P02 con sim=0.1611; P05 recupera P06 con sim=0.2957). Se aclara que el corpus es un catálogo curado de 8 productos arquetípicos representativo de la cartera bancaria. La tasa de acierto del 100% en Top-2 es consistente con que el motor semántico captura con fidelidad las relaciones técnicas entre productos.")
    
    # Modelo 3C
    add_heading(doc, 5, "Modelo 3C: Reglas de Scoring y Función de Utilidad Financiera")
    add_paragraph(doc, "Fundamento teórico y formulación: Para evitar el sobreendeudamiento, se define una función de utilidad bancaria determinista:")
    add_block_math(doc, r"U(u, i) = \text{Score}_{\text{afinidad}}(u, i) \cdot \mathbb{I}(\text{Solvente}_u) \cdot (1 - \text{Mora}_i)")
    add_block_math(doc, r"\text{Ratio Esfuerzo} = \frac{\text{Cuota Mensual}}{\text{Salario Distrital Promedio}} \le 0.30")
    
    add_paragraph(doc, "La Tabla 13 expone la distribución de créditos y morosidad real por tramo de endeudamiento:")
    
    tbl13_headers = ["Tramo de Endeudamiento", "Contratos (N)", "% Cartera", "Créditos Morosos", "Tasa de Mora Real (%)", "Decisión del Sistema"]
    tbl13_rows = [
        ["≤ 30% (Prudencial)", "213", "31.23%", "14", "6.57%", "Aprobación Automática (Oferta Prioritaria)"],
        ["30% - 50% (Riesgo Moderado)", "208", "30.50%", "18", "8.65%", "Revisión Condicionada a Mayor Plazo"],
        ["> 50% (Sobreendeudamiento)", "261", "38.27%", "44", "16.86%", "Rechazo Obligatorio (Bloqueo Automático)"],
        ["TOTAL / PROMEDIO CARTERA", "682", "100.0%", "76", "11.14%", "Tasa Base de Impago Bancario"]
    ]
    add_table(doc, "Tabla 13: Distribución de Créditos y Tasa de Morosidad Real por Tramo de Endeudamiento (df_prestamos).", tbl13_headers, tbl13_rows)
    add_figure(doc, "img/individual/fig_3c_scoring_utilidad.png", "Figura 9: Distribución de Tasa de Mora Real según Capacidad de Endeudamiento.", 4.8)
    
    add_paragraph(doc, "Validación estadística de la regla del 30%: La asociación entre sobreendeudamiento (> 50%) y morosidad real es altamente significativa (Chi-cuadrado χ² = 10.62, p = 0.0011; Test de Fisher p = 0.0007). Los créditos prudenciales registran una mora de solo 6.57%, frente a 16.86% en tramo crítico, validando la regla del 30% como compuerta de solvencia indispensable.")
    
    add_heading(doc, 5, "Conclusión y Dictamen del Mejor Método sobre df_prestamos")
    add_paragraph(doc, "Dictamen Técnico: Se dictamina como solución óptima el sistema Híbrido Basado en Contenidos (TF-IDF, Modelo 3A) gobernado por Reglas de Utilidad Financiera (Modelo 3C). Es el único enfoque técnicamente viable ante la ausencia de co-ocurrencia, garantizando además mitigación activa del riesgo crediticio.")
    
    # -------------------------------------------------------------------------
    # Evaluación Comparativa Global
    # -------------------------------------------------------------------------
    add_heading(doc, 4, "2.7.9 Evaluación comparativa global de los sistemas sobre los cuatro DataFrames")
    add_paragraph(doc, "La Tabla 17 y la Figura 14 consolidan la síntesis comparativa exhaustiva de los doce modelos de recomendación implementados:")
    
    tbl17_headers = ["DataFrame", "Sistema / Técnica", "Tipo de Modelo", "Familia Analítica", "Dimensiones de Salida", "Métrica Clave Obtenida", "Cobertura", "Rol de Negocio en la Entidad"]
    tbl17_rows = [
        ["df_transacciones", "Slope One (1A)", "Recomendador", "Colaborativo Ítem-Ítem", "18,265 predicciones", "MAE: 0.2593 ± 0.0052 (5-fold CV)", "68.0%", "Calibración de intensidad y venta cruzada fina."],
        ["df_transacciones", "Coseno Ajustado (1B)", "Recomendador", "Colaborativo Ítem-Ítem", "Matriz 5 × 5", "cos_adj(Seguro, Hogar) = +0.3360", "68.0%", "Orientación angular centrada en medias de usuario."],
        ["df_transacciones", "Pearson Ítem-Ítem (1C)", "Complementario", "Colaborativo / Temporal", "Matrices 5 × 5", "r_calif = +0.9957, r_Δmes = +0.7192", "100.0%", "Correlación lineal de ratings y sincronización de tesorería."],
        ["df_ordenes", "Coseno Binario (2A)", "Recomendador", "Colaborativo de Co-adquisición", "Matriz 5 × 5", "cos(Seguro, Hogar) = 0.3976", "83.5%", "Detección de co-adquisición y empaquetamiento (bundling)."],
        ["df_ordenes", "Ponderación ITF (2B)", "Recomendador", "Colaborativo Ítem-Ítem con Penalización", "5 factores especificidad", "Factor ITF Leasing: 2.3998 (vs Hogar: 0.1105)", "83.5%", "Corrección de sesgo de popularidad hacia nichos no triviales."],
        ["df_ordenes", "Pearson Órdenes (2C)", "Complementario", "Asociación de Contratos", "Matriz 5 × 5", "r(Hogar, Préstamo) = -0.4117", "83.5%", "Detección de disociación y exclusión contractual."],
        ["df_prestamos", "TF-IDF Contratos (3A)", "Recomendador", "Basado en Contenidos", "Matriz 8 × 8 léxica", "Sim: 0.1611 (LOPO: 8/8, 100%)", "100.0%", "Resolución de Item Cold Start para productos nuevos."],
        ["df_prestamos", "Coseno Numérico (3B)", "Complementario", "Geométrico Centroidal", "Matriz 5 × 5 (plazos)", "cos(12m, 60m) = -0.9991", "100.0%", "Mapeo estructural de distancias entre plazos crediticios."],
        ["df_prestamos", "Scoring y Utilidad (3C)", "Recomendador / Control", "Conocimiento y Utilidad", "682 contratos", "Mora ≤ 30%: 6.57% (vs > 50%: 16.86%)", "100.0%", "Filtro prudencial de capacidad de pago y control de riesgo."],
        ["df_cliente", "Demográfico (4A)", "Recomendador", "Filtrado Demográfico", "9 arquetipos", "Adopción Adultos: 16.9% (χ²=63.78)", "100.0%", "Resolución de User Cold Start en apertura de cuenta."],
        ["df_cliente", "User-to-User kNN (4B)", "Recomendador", "Colaborativo Usuario-Usuario", "4,500 titulares", "AUC: 0.7905, Brier Score: 0.1098", "83.8%", "Exploración de vecindarios y gemelos financieros."],
        ["df_cliente", "Pearson Perfil (4C)", "Complementario", "Exploratorio Multivariante", "Matriz 6 × 6", "r(Tx, Órdenes) = +0.4965", "100.0%", "Marco de gobernanza estructural y segmentación macro."]
    ]
    add_table(doc, "Tabla 17: Síntesis Comparativa de los 12 Modelos de Recomendación Implementados por DataFrame.", tbl17_headers, tbl17_rows, [Inches(1.0), Inches(0.9), Inches(0.8), Inches(0.9), Inches(0.8), Inches(1.1), Inches(0.5), Inches(1.11)])
    add_figure(doc, "img/fig_06_comparativa_global.png", "Figura 14: Mapa Estratégico de Cobertura de Cartera vs. Nivel de Personalización.", 5.3)
    
    add_paragraph(doc, "Arquitectura bancaria en dos fases con gobernanza prudencial transversal:")
    add_bullet(doc, "Al momento de abrir la cuenta bancaria, se activa el Filtrado Demográfico por Estereotipos (Modelo 4A) combinado con TF-IDF (Modelo 3A). Sin requerir transacciones previas, el sistema ofrece el paquete de bienvenida según el arquetipo geográfico y etario, logrando una cobertura del 100%.", "Fase 1 (Arranque en Frío / Onboarding):")
    add_bullet(doc, "Conforme el cliente acumula transacciones y domicilia servicios (a partir de 3 meses o 15 movimientos), entran en operación Slope One (Modelo 1A), Ponderación ITF (Modelo 2B) y User-to-User kNN (Modelo 4B), afinando la recomendación hacia el producto específico de mayor afinidad individual.", "Fase 2 (Cartera Transaccional Madura):")
    add_bullet(doc, "Cualquier sugerencia crediticia emitida por los modelos colaborativos debe superar obligatoriamente las reglas de Scoring y Utilidad Financiera (Modelo 3C), bloqueando automáticamente a clientes morosos históricos (estados B y D) y aplicando la política escalonada de endeudamiento (≤ 30% preaprobado, 30%-50% con mitigaciones, >50% rechazado).", "Capa Transversal de Gobernanza y Riesgo:")
    
    # -------------------------------------------------------------------------
    # Descarte Empírico
    # -------------------------------------------------------------------------
    add_heading(doc, 4, "2.7.10 Comprobación que motivó el descarte empírico de la co-ocurrencia transaccional cruda")
    add_paragraph(doc, "La co-ocurrencia sobre frecuencias brutas transaccionales colapsa el espacio angular en un rango hiper-comprimido (0.9339 a 0.9610) con varianza casi nula (σ² = 0.00009), haciendo indistinguible cualquier servicio. La Tabla 13-B y la Figura 13 demuestran este hallazgo:")
    
    tbl_desc_headers = ["Enfoque de Recomendación", "Rango de Similitud Observado", "Varianza Angular (σ²)", "Diagnóstico Matemático", "Decisión Analítica"]
    tbl_desc_rows = [
        ["Co-ocurrencia Transaccional Cruda", "[0.9339, 0.9610]", "0.00009", "Colapso dimensional y compresión extrema", "DESCARTADO FORMALMENTE"],
        ["Coseno Binario sobre Órdenes", "[0.0000, 0.3976]", "0.03970", "Incremento de varianza de 450 veces", "ACEPTADO (Co-adquisición)"],
        ["Coseno Ajustado en Transacciones", "[-0.7507, +0.3360]", "0.09420", "Incremento de varianza de 1,000+ veces", "ACEPTADO (Centrado en Medias)"]
    ]
    add_table(doc, "Tabla 13-B: Comparación de Dispersión y Diagnóstico de Descarte de Co-ocurrencia Transaccional Cruda.", tbl_desc_headers, tbl_desc_rows)
    add_figure(doc, "img/fig_05_descarte_empirico_comparativa.png", "Figura 13: Comprobación del Descarte Empírico: Colapso de Varianza en Co-ocurrencia Cruda.", 5.3)
    
    # MLOps
    add_heading(doc, 4, "2.7.11 Arquitectura tecnológica de despliegue y flujo productivo MLOps en el banco comercial")
    add_paragraph(doc, "Para garantizar que los modelos operen con alta disponibilidad y latencia <50 ms, se estructura el pipeline tecnológico: (1) Capa de Ingesta y Feature Store en Kafka; (2) Inferencia Híbrida en FastAPI; (3) Compuerta de Gobernanza; y (4) Monitoreo Continuo con tests de deriva poblacional (PSI) y Kolmogorov-Smirnov.")
    
    # Habilidades Blandas
    add_heading(doc, 3, "2.8 Habilidades blandas empleadas en la práctica")
    add_paragraph(doc, "Durante el desarrollo de la práctica se ejercitaron habilidades profesionales clave:")
    add_bullet(doc, "Capacidad para contrastar la teoría matemática con la realidad empírica de los datos.", "Pensamiento crítico y rigor analítico:")
    add_bullet(doc, "Colaboración entre integrantes mediante control de versiones Git.", "Trabajo en equipo y distribución de tareas:")
    add_bullet(doc, "Priorización de la solvencia del cliente frente a incentivos comerciales.", "Ética profesional y gobernanza de datos:")
    
    # III. CONCLUSIONES
    add_heading(doc, 2, "III. CONCLUSIONES")
    add_numbered(doc, 1, "Cobertura Metodológica Exhaustiva de la Consigna: Se implementaron y evaluaron con rigor los 8 puntos solicitados por el docente, cubriendo las tres familias clásicas (Colaborativo, Contenidos y Demográfico) complementadas por una cuarta categoría transversal de gobernanza (Modelos de Conocimiento y Utilidad Financiera) sobre los cuatro DataFrames canónicos del Data Warehouse Kimball.", "1. Cobertura Metodológica Exhaustiva:")
    add_numbered(doc, 2, "Precisión Predictiva de Slope One: En validación cruzada 5-fold sobre df_transacciones, Slope One redujo el error absoluto medio (MAE = 0.2593 ± 0.0052) en un 36.18% frente a la media de usuario (0.4063) y un 43.70% frente a la media global (0.4606), empatando técnicamente en Hit-Rate@1 con la popularidad pura (91.79% vs 91.29%, Z = 0.7634, p = 0.4452) y permitiendo calibrar montos personalizados.", "2. Precisión Predictiva de Slope One:")
    add_numbered(doc, 3, "Validez del Descarte Empírico: Se demostró cuantitativamente que la co-ocurrencia transaccional cruda colapsa el espacio angular (similitudes entre 0.93 y 0.96, σ² = 0.00009). La migración a órdenes (σ² = 0.0397) y al Coseno Ajustado (σ² = 0.0942) multiplicó la dispersión en 450 y 1,000+ veces, restaurando la capacidad discriminativa.", "3. Validez del Descarte Empírico:")
    add_numbered(doc, 4, "Arranque en Frío y Control Prudencial de Riesgo: El Filtrado Demográfico otorga cobertura del 100% desde la apertura de cuenta (validado con χ² = 63.7832, p < 0.0001), mientras que TF-IDF resuelve el arranque en frío de productos con 100% de precisión LOPO (8/8). La compuerta de utilidad crediticia (ratio cuota/salario ≤ 30%) se fundamenta en la evidencia real: la morosidad en endeudamiento ≤ 30% es de solo 6.57%, frente a 16.86% en sobreendeudamiento > 50% (χ² = 10.62, p = 0.0011).", "4. Arranque en Frío y Control de Riesgo:")
    
    # IV. RECOMENDACIONES
    add_heading(doc, 2, "IV. RECOMENDACIONES")
    add_numbered(doc, 1, "Desplegar comercialmente la arquitectura bancaria en dos fases: Fase 1 (Demográfico 4A + TF-IDF 3A) para clientes en onboarding, y Fase 2 (Slope One 1A, Ponderación ITF 2B y kNN 4B) a partir de los 90 días o 15 transacciones.", "1. Despliegue en Dos Fases:")
    add_numbered(doc, 2, "Incorporar factores de decaimiento temporal (e^{-λ·t}) en el recálculo matricial periódico de Slope One para atenuar operaciones antiguas y priorizar hábitos financieros recientes.", "2. Decaimiento Temporal Dinámico:")
    add_numbered(doc, 3, "Implementar una política escalonada de riesgo (Risk Tiering): Tramo Verde (≤ 30%, preaprobación con mora 6.57%), Tramo Amarillo (30%-50%, condicionado a mayor plazo) y Tramo Rojo (> 50%, denegación automática).", "3. Política Escalonada de Riesgo:")
    add_numbered(doc, 4, "Establecer auditorías periódicas de fuga de información (Data Leakage) en el modelo kNN usuario a usuario para garantizar que las variables de entrada excluyan débitos del propio crédito evaluado.", "4. Auditoría de Fugas de Información:")
    
    # V. BIBLIOGRAFÍA
    add_heading(doc, 2, "V. BIBLIOGRAFÍA")
    add_bullet(doc, "D. Lemire and A. Maclachlan, 'Slope One Predictors for Collaborative Filtering: Simple and Efficient and Yet Accurately Differentiating Between Users and Items,' in Proceedings of the 2005 SIAM International Conference on Data Mining (SDM), Newport Beach, CA, 2005, pp. 471–475.", "[1]")
    add_bullet(doc, "G. Adomavicius and A. Tuzhilin, 'Toward the Next Generation of Recommender Systems: A Survey of the State-of-the-Art and Possible Extensions,' IEEE Transactions on Knowledge and Data Engineering, vol. 17, no. 6, pp. 734–749, Jun. 2005.", "[2]")
    add_bullet(doc, "P. Resnick, N. Iacovou, M. Suchak, P. Bergstrom, and J. Riedl, 'GroupLens: An Open Architecture for Collaborative Filtering of Netnews,' in Proceedings of the 1994 ACM Conference on Computer Supported Cooperative Work (CSCW), Chapel Hill, NC, 1994, pp. 175–186.", "[3]")
    add_bullet(doc, "B. Sarwar, G. Karypis, J. Konstan, and J. Riedl, 'Item-based collaborative filtering recommendation algorithms,' in Proceedings of the 10th International Conference on World Wide Web (WWW), Hong Kong, 2001, pp. 285–295.", "[4]")
    add_bullet(doc, "E. Rich, 'User modeling via stereotypes,' Cognitive Science, vol. 3, no. 4, pp. 329–354, 1979.", "[5]")
    add_bullet(doc, "G. Salton and C. Buckley, 'Term-weighting approaches in automatic text retrieval,' Information Processing & Management, vol. 24, no. 5, pp. 513–523, 1988.", "[6]")
    add_bullet(doc, "R. Kimball and M. Ross, The Data Warehouse Toolkit: The Definitive Guide to Dimensional Modeling, 3rd ed. Indianapolis, IN: John Wiley & Sons, 2013.", "[7]")
    
    # ANEXOS
    add_heading(doc, 2, "VI. ANEXOS")
    add_heading(doc, 3, "Anexo A. Diagrama de Flujo del Ciclo Analítico y Motores de Recomendación")
    add_figure(doc, "img/fig_anexo_a_diagrama_flujo.png", "Figura 15: Diagrama de Flujo de la Arquitectura Analítica de Sistemas de Recomendación Bancarios.", 5.4)
    
    add_heading(doc, 3, "Anexo B. Representación Gráfica de la Matriz de Asignación y Viabilidad Técnica")
    add_figure(doc, "img/fig_anexo_b_matriz_grafica.png", "Figura 16: Representación Gráfica de la Matriz de Asignación y Viabilidad Técnica de los Algoritmos sobre los Cuatro DataFrames.", 5.4)
    
    add_heading(doc, 3, "Anexo C. Programas Desarrollados y Artefactos de Salida")
    tbl18_headers = ["Archivo de Código / Script", "Sistema / Módulo que Implementa", "Salida Analítica Generada"]
    tbl18_rows = [
        ["00_generar_4_dataframes.py", "ETL Dimensional y Extracción desde Kimball DW", "4 DataFrames canónicos limpios (.csv.gz) con auditoría de claves."],
        ["14_eval_5fold_slope_one.py", "Validación Cruzada 5-Fold de Slope One (Punto 5)", "Métricas de error: MAE = 0.2593 ± 0.0052 y RMSE sobre 5 pliegues."],
        ["15_eval_topn_ranking.py", "Evaluación de Ranking Top-N Leave-One-Out (Punto 5)", "Curvas Hit-Rate@k (HR@1 = 91.79%) y MRR = 0.9567."],
        ["16_eval_lopo_tfidf.py", "Validación Leave-One-Product-Out de TF-IDF (Punto 8)", "Matriz de similitud léxica 8 × 8 y 100% de acierto Top-2 en LOPO."],
        ["17_test_chi2_estereotipos_riesgo.py", "Pruebas de Hipótesis Chi² y Test de Fisher (Puntos 6 y 8)", "Significancia de mora: χ² = 10.62 (p = 0.0011) y estereotipos: χ² = 63.78."],
        ["18_calc_coseno_ajustado.py", "Coseno Ajustado Centrado en Medias de Usuario (Punto 7)", "Matriz 5 × 5 de similitud angular centrada sin compresión."],
        ["19_calc_pearson_item_item.py", "Cálculo de Pearson Ítem-Ítem sobre Ratings (Punto 7)", "Matriz 5 × 5 de correlación lineal y cálculo pedagógico paso a paso."],
        ["generate_14_figures_from_04.py", "Generador de Figuras Individuales en Alta Definición", "12 Figuras individuales a 300 DPI para los cuatro DataFrames analíticos."],
        ["generate_figures_13_14.py", "Generador de Descarte Empírico y Mapa Estratégico", "Figura 13 (Descarte Empírico) y Figura 14 (Lienzo Estratégico)."],
        ["generate_annex_figures.py", "Generador Gráfico de Diagramas de Anexos", "Figura 15 (Diagrama de Flujo) y Figura 16 (Matriz Gráfica 5 × 4)."],
        ["build_final_04_word.py", "Constructor Maestro del Informe Institucional Word", "04_Informe_Sistemas_de_Recomendacion.docx con formato oficial UTA."]
    ]
    add_table(doc, "Tabla 18: Programas Analíticos Desarrollados en la Práctica y Archivos que Generan.", tbl18_headers, tbl18_rows, [Inches(2.1), Inches(2.2), Inches(1.81)])
    
    add_heading(doc, 3, "Anexo D. Resumen Cuantitativo de la Práctica y Glosario Técnico de Recomendadores")
    add_bullet(doc, "df_transacciones (1,056,320 registros), df_ordenes (6,471 registros), df_prestamos (682 registros) y df_cliente_consolidado (5,369 registros).", "4 DataFrames analizados:")
    add_bullet(doc, "Evaluados y contrastados a través de los cuatro DataFrames (3 modelos por DataFrame).", "12 modelos de recomendación implementados:")
    add_bullet(doc, "Las tres familias clásicas (Filtrado Colaborativo, Basado en Contenidos y Demográfico), complementadas con una cuarta categoría transversal de gobernanza: Modelos Basados en el Conocimiento y en la Utilidad Financiera.", "Cobertura de 4 familias metodológicas:")
    add_bullet(doc, "En la combinación global de la arquitectura en dos fases.", "100% de clientes y productos cubiertos:")
    add_bullet(doc, "37.61% de reducción frente a la media de usuario en partición 80/20 (MAE = 0.2535 frente a 0.4063) y 36.18% en validación cruzada 5-fold (MAE = 0.2593 ± 0.0052 frente a 0.4063, y 43.70% frente a media global de 0.4606).", "Reducción del error absoluto (MAE) en Slope One:")
    add_bullet(doc, "Empate estadístico en ranking Top-N con la popularidad pura (91.79% vs 91.29%, Z = 0.7634, p = 0.4452).", "Hit-Rate@1 de Slope One:")
    add_bullet(doc, "Contratos con endeudamiento ≤ 30% registran mora de 6.57%, frente a 16.86% en endeudamiento > 50% (confirmado con χ² = 10.62, p = 0.0011; Fisher p = 0.0007).", "Evidencia transversal de mora en la regla del 30%:")
    add_bullet(doc, "Cada DataFrame y punto metodológico cuenta con su dictamen técnico que determina el método óptimo para ese grano operacional.", "Dictamen técnico por DataFrame:")
    
    add_heading(doc, 3, "Anexo E. Matriz de Gobernanza Ética, Cumplimiento Regulatorio y Mitigación de Sesgos Algorítmicos")
    tbl_e_headers = ["Dimensión de Gobernanza", "Riesgo Algorítmico Identificado", "Mecanismo de Mitigación Implementado en la Práctica", "Normativa de Referencia"]
    tbl_e_rows = [
        ["No Discriminación", "Sesgo demográfico por edad o distrito en asignación de tasas o créditos.", "El modelo 4A se restringe estrictamente a ofertas de bienvenida; la evaluación de solvencia (3C) depende de capacidad objetiva de pago, no del estereotipo.", "Equal Credit Opportunity Act (ECOA) / Basilea II"],
        ["Transparencia y Explicabilidad", "Decisiones opacas en redes o cajas negras que impidan explicar una denegación.", "Slope One, Coseno Ajustado y Reglas de Utilidad son algoritmos de caja blanca con trazabilidad matemática auditable paso a paso.", "Reglamento General de Protección de Datos (RGPD) Art. 22"],
        ["Prevención de Sobreendeudamiento", "Recomendación de créditos a clientes vulnerables con alta propensión pero baja liquidez.", "Compuerta obligatoria de utilidad (ratio cuota/salario ≤ 30%) y bloqueo histórico del 11.15% por mora en estados B y D.", "Directiva Europea de Crédito al Consumo (CCD)"],
        ["Integridad y Fuga de Datos", "Sobreestimación del poder predictivo por inclusión de cuotas en variables transaccionales.", "Protocolo de aislamiento estricto de variables en 4B, excluyendo débitos crediticios del vector de características de entrada.", "Estándares ISO/IEC 23894 para Gestión de Riesgos de IA"],
        ["Estabilidad Temporal", "Degradación del rendimiento por cambios en la macroeconomía (inflación, desempleo).", "Monitoreo semanal de Concept Drift con tests de Kolmogorov-Smirnov y reentrenamiento trimestral de matrices b(j, i).", "Guía de Gestión de Modelos de Riesgo SR 11-7 (Fed)"]
    ]
    add_table(doc, "Tabla 19: Matriz de Gobernanza Ética y Mitigación de Riesgos en Modelos de Recomendación Bancarios.", tbl_e_headers, tbl_e_rows, [Inches(1.2), Inches(1.5), Inches(2.2), Inches(1.21)])
