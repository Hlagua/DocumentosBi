# -*- coding: utf-8 -*-
"""
Módulo Parte 3: Modelos sobre df_prestamos (Eje 3) y df_cliente_consolidado (Eje 4)
con validaciones estadísticas avanzadas, matrices auditadas y dictámenes técnicos.
"""
from docx.shared import Inches, Pt
from helpers_informe_4 import (
    add_heading, add_paragraph, add_bullet, add_numbered,
    add_block_math, add_figure, add_table
)

def build_part3(doc):
    # -------------------------------------------------------------------------
    # 2.7.6 EJE 3: df_prestamos
    # -------------------------------------------------------------------------
    add_heading(doc, 4, "2.7.6 EJE 3: Modelos sobre el DataFrame de Préstamos (df_prestamos)")
    add_paragraph(doc, "df_prestamos reúne 682 contratos formales de crédito con montos desembolsados (4,980 a 590,820 CZK), plazos de amortización (12 a 60 meses), cuotas y estatus oficial de pago. Dado que en banca comercial un cliente casi invariablemente posee un único crédito activo, la co-adquisición entre créditos es nula (card(S(j,i)) ≈ 0), haciendo inviable el filtrado colaborativo tradicional.")
    
    # Modelo 3A
    add_heading(doc, 5, "Modelo 3A: Filtrado Basado en Contenidos con TF-IDF sobre Cláusulas Contractuales")
    add_paragraph(doc, "Fundamento teórico y formulación: Modela los términos textuales y condiciones de 8 productos arquetípicos de cartera (P01 a P08) mediante la ponderación TF-IDF con suavizado logarítmico, calculando la similitud semántica mediante el coseno vectorial:")
    add_block_math(doc, r"\text{tf-idf}(t, d) = \text{tf}(t, d) \cdot \left[\ln\left(\frac{1 + n}{1 + \text{df}(t)}\right) + 1\right], \quad \cos(\vec{c}_i, \vec{c}_j) = \frac{\vec{c}_i \cdot \vec{c}_j}{\|\vec{c}_i\| \|\vec{c}_j\|}")
    
    add_paragraph(doc, "Ingeniería de características textuales: El corpus analítico se estructuró a partir de los documentos legales y fichas técnicas de los 8 productos de cartera. Tras un preprocesamiento de tokenización, lematización léxica y eliminación de palabras vacías (stopwords financieras en checo y español), se extrajo un vocabulario de 48 descriptores normativos clave (ej. amortización, colateral, desgravamen, hipoteca, vehicular, solvencia, pyme, desembolso, plazo, tasa). La vectorización con normalización L2 proyecta cada contrato en una esfera unitaria en R^48, permitiendo medir la afinidad temática libre de sesgos por longitud del texto.")
    
    add_paragraph(doc, "La Tabla 11 expone la matriz de similitud léxica TF-IDF entre los 8 contratos de cartera:")
    
    tbl11_headers = ["Producto Contractual", "P_Personal", "C_Familiar", "P_Hipotec", "C_Comercial", "S_VidaSalud", "S_Desgravam", "SIPO_Hogar", "Leasing"]
    tbl11_rows = [
        ["Prestamo Personal Express (P01)", "1.0000", "0.1611", "0.1257", "0.0909", "0.0409", "0.0000", "0.0244", "0.0251"],
        ["Credito Consumo Familiar (P02)", "0.1611", "1.0000", "0.1193", "0.0863", "0.2116", "0.0321", "0.0616", "0.0541"],
        ["Prestamo Hipotecario Vivienda (P03)", "0.1257", "0.1193", "1.0000", "0.1432", "0.0407", "0.1026", "0.0243", "0.0806"],
        ["Credito Comercial PyME (P04)", "0.0909", "0.0863", "0.1432", "1.0000", "0.0000", "0.0000", "0.0000", "0.0507"],
        ["Poliza Seguro Vida y Salud (P05)", "0.0409", "0.2116", "0.0407", "0.0000", "1.0000", "0.2957", "0.0381", "0.0301"],
        ["Seguro Desgravamen e Invalidez (P06)", "0.0000", "0.0321", "0.1026", "0.0000", "0.2957", "1.0000", "0.0000", "0.0324"],
        ["Domiciliacion Servicios Hogar (P07)", "0.0244", "0.0616", "0.0243", "0.0000", "0.0381", "0.0000", "1.0000", "0.0234"],
        ["Arrendamiento / Leasing (P08)", "0.0251", "0.0541", "0.0806", "0.0507", "0.0301", "0.0324", "0.0234", "1.0000"]
    ]
    add_table(doc, "Tabla 11: Matriz de Similitud Coseno TF-IDF entre Cláusulas Contractuales de Cartera (df_prestamos).", tbl11_headers, tbl11_rows)
    add_figure(doc, "img/individual/fig_3a_tfidf.png", "Figura 7: Matriz de Similitud Léxica TF-IDF entre Cláusulas de Crédito.", 4.8)
    
    add_paragraph(doc, "Validación Leave-One-Product-Out (LOPO): Para verificar objetivamente la capacidad de recuperación semántica ante el arranque en frío de productos (Item Cold Start), se ejecutó una evaluación LOPO sobre los 8 contratos (script 16). Ocultando cada producto, el motor identificó con una precisión del 100.0% (8 de 8 productos) a su contraparte complementaria más coherente en el Top-2:")
    add_bullet(doc, "P01 (Préstamo Personal Express) recupera en Top-1 a P02 (Consumo Familiar) con similitud exacta de 0.1611 y en Top-2 a P03 (Hipotecario) con 0.1257.", "1. Préstamo Personal (P01):")
    add_bullet(doc, "P02 (Consumo Familiar) recupera en Top-1 a P05 (Póliza de Vida y Salud) con 0.2116 y en Top-2 a P01 con 0.1611.", "2. Consumo Familiar (P02):")
    add_bullet(doc, "P03 (Préstamo Hipotecario) recupera en Top-1 a P04 (Comercial PyME) con 0.1432 y en Top-2 a P01 con 0.1257, asociando además en Top-3 a P06 (Desgravamen) con 0.1026.", "3. Préstamo Hipotecario (P03):")
    add_bullet(doc, "P04 (Comercial PyME) recupera en Top-1 a P03 (Hipotecario) con 0.1432 y en Top-2 a P01 (Personal Express) con 0.0909.", "4. Comercial PyME (P04):")
    add_bullet(doc, "P05 (Seguro Vida y Salud) recupera en Top-1 a P06 (Seguro Desgravamen) con 0.2957 y en Top-2 a P02 (Consumo Familiar) con 0.2116.", "5. Seguro Vida y Salud (P05):")
    add_bullet(doc, "P06 (Seguro Desgravamen) recupera en Top-1 a P05 (Vida y Salud) con 0.2957 y en Top-2 a P03 (Hipotecario) con 0.1026.", "6. Seguro Desgravamen (P06):")
    add_bullet(doc, "P07 (Servicios Hogar) recupera en Top-1 a P02 (Consumo Familiar) con 0.0616 y en Top-2 a P05 (Vida y Salud) con 0.0381.", "7. Servicios del Hogar (P07):")
    add_bullet(doc, "P08 (Arrendamiento / Leasing) recupera en Top-1 a P03 (Hipotecario) con 0.0806 y en Top-2 a P02 (Consumo Familiar) con 0.0541.", "8. Arrendamiento / Leasing (P08):")
    add_paragraph(doc, "Se aclara que el corpus analizado es un catálogo curado de 8 productos arquetípicos representativo de la cartera bancaria. La tasa de acierto del 100% en Top-2 demuestra que el motor semántico captura con fidelidad las relaciones técnicas entre productos.")
    add_paragraph(doc, "Recomendación estratégica de producto: Configurar el recomendador TF-IDF en el módulo de diseño de nuevos productos para pre-etiquetar ofertas verdes o créditos educativos y asociarlos a seguros vinculados sin esperar meses de transacciones.")
    
    # Modelo 3B
    add_heading(doc, 5, "Modelo 3B: Similitud del Coseno Numérico sobre Condiciones de Crédito")
    add_paragraph(doc, "Fundamento teórico y formulación: Proyecta los contratos en el espacio tridimensional estandarizado Z-Score [monto promedio, plazo en meses, cuota mensual], calculando la proximidad centroidal entre los cinco plazos estándar de la cartera (12, 24, 36, 48 y 60 meses). La Tabla 12 presenta la matriz resultante:")
    
    tbl12_headers = ["Plazo Arquetípico", "12 meses", "24 meses", "36 meses", "48 meses", "60 meses"]
    tbl12_rows = [
        ["12 meses", "1.0000", "+0.9943", "+0.4645", "-0.9893", "-0.9991"],
        ["24 meses", "+0.9943", "1.0000", "+0.5534", "-0.9983", "-0.9978"],
        ["36 meses", "+0.4645", "+0.5534", "1.0000", "-0.5879", "-0.4967"],
        ["48 meses", "-0.9893", "-0.9983", "-0.5879", "1.0000", "+0.9934"],
        ["60 meses", "-0.9991", "-0.9978", "-0.4967", "+0.9934", "1.0000"]
    ]
    add_table(doc, "Tabla 12: Matriz de Similitud del Coseno Numérico entre Plazos Arquetípicos de Crédito (df_prestamos).", tbl12_headers, tbl12_rows)
    add_figure(doc, "img/individual/fig_3b_coseno_plazos.png", "Figura 8: Similitud del Coseno Numérico entre Plazos Crediticios.", 4.8)
    
    add_paragraph(doc, "Interpretación analítica y de negocio: La matriz expone una estructura dipolar casi perfecta: los plazos adyacentes de corto plazo (12 y 24 meses: +0.9943) y de largo plazo (48 y 60 meses: +0.9934) forman clusters altamente afines. En contraste, la oposición entre los extremos 12 y 60 meses es diametral (-0.9991). Es fundamental aclarar que este valor de -0.9991 surge casi por construcción geométrica del z-score al comparar centroides opuestos (alta cuota a 12 meses vs baja cuota a 60 meses), actuando como mapa estructural para refinanciamiento.")
    add_paragraph(doc, "Recomendación estratégica de producto: En solicitudes de reestructuración crediticia, ofertar exclusivamente plazos contiguos en el espacio angular (ej. migrar de 36 a 48 meses) para evitar desajustes abruptos en la cuota mensual.")
    
    # Modelo 3C
    add_heading(doc, 5, "Modelo 3C: Reglas de Scoring y Función de Utilidad Financiera")
    add_paragraph(doc, "Fundamento teórico y compuertas de solvencia: El modelo impone dos reglas de gobernanza prudencial bancaria:")
    add_bullet(doc, "De los 682 créditos formalizados, se auditaron los estatus según la norma PKDD'99: Estado A (203 finalizados al día, 29.77%), Estado C (403 vigentes al día, 59.09%), Estado B (31 créditos fallidos con deuda impaga, 4.55%) y Estado D (45 contratos en mora activa con cuotas impagas, 6.60%). La Regla 1 bloquea automáticamente al 11.15% de clientes morosos históricos (estados B y D, 76 contratos).", "Regla de Scoring 1 (Bloqueo de Mora Histórica):")
    add_bullet(doc, "La cuota periódica calculada por el sistema de amortización francés no puede sobrepasar el umbral prudencial del 30% del salario distrital promedio del solicitante, definiendo la Zona de Utilidad Sostenible:", "Regla de Utilidad 2 (Límite Prudencial de Endeudamiento ≤ 30%):")
    add_block_math(doc, r"\text{Cuota}(P, r, n) = P \cdot \frac{r(1+r)^n}{(1+r)^n - 1}, \quad \text{Utilidad} = \begin{cases} 1 & \text{si } \frac{\text{Cuota}}{\text{Salario}} \le 0.30 \\ 0 & \text{si } \frac{\text{Cuota}}{\text{Salario}} > 0.30 \end{cases}")
    
    add_paragraph(doc, "Validación empírica y significancia estadística (Script 17): En los 682 contratos históricos de la entidad, los préstamos en mora o fallidos (estados B y D) exhiben ratios de esfuerzo promedio sustancialmente más elevados (57.53% y 57.42%) que los contratos sanos de estados A y C (45.21% y 42.21%). Al segmentar la cartera:")
    add_bullet(doc, "Contratos con ratio ≤ 30% (N = 213): registran una tasa de mora real de apenas 6.57% (14 casos en mora).", "Zona Prudencial (≤ 30%):")
    add_bullet(doc, "Contratos con ratio 30% - 50% (N = 208): registran una tasa de mora intermedia de 8.65% (18 casos en mora).", "Zona de Alerta (30% - 50%):")
    add_bullet(doc, "Contratos con ratio > 50% (N = 261): la tasa de mora escala al 16.86% (44 casos en mora), 2.5 veces superior al tramo prudencial.", "Zona Crítica (> 50%):")
    add_paragraph(doc, "La diferencia entre tramos es altamente significativa: Chi-cuadrado global χ² = 14.4043, p = 0.0007; Chi-cuadrado con corrección de Yates entre extremos (≤30% vs >50%) χ² = 10.6159, p = 0.0011; y Test Exacto de Fisher con p = 0.0007 y Odds Ratio de 0.3470 (IC 95%: [0.18, 0.65]). No se trata de una reducción temporal longitudinal observada tras aplicar la regla, sino de la evidencia transversal que justifica fijar el umbral prudencial en el 30% para contener el impago.")
    
    add_paragraph(doc, "Reconciliación y Análisis Costo-Beneficio (Risk Tiering): En la cartera histórica sana de la entidad, el ratio medio observado es del 42.21% - 45.21% (mediana del 39.95%). Si el banco hubiera rechazado tajantemente todo crédito por encima del 30%, habría denegado 469 de 682 créditos (68.77%), sacrificando una enorme masa de ingresos por intereses. Para balancear riesgo y volumen comercial, se formula una política escalonada por tramos (Risk Tiering):")
    add_bullet(doc, "Tranche Verde (≤ 30%, N = 213): Aprobación automática preaprobada inmediata en banca virtual. Registra la tasa de mora más reducida de la institución (6.57%).", "1. Tranche Verde (Fast-Track):")
    add_bullet(doc, "Tranche Amarillo (30% - 50%, N = 208): Aprobación condicionada a mecanismos de mitigación de riesgo. Se exige extender el plazo de amortización a 48 o 60 meses para forzar el descenso de la cuota hacia el tramo verde, o bien la presentación de colaterales y avales solidarios. Permite recuperar el 91.35% de los clientes cumplidos de este rango.", "2. Tranche Amarillo (Mitigación):")
    add_bullet(doc, "Tranche Rojo (> 50%, N = 261): Denegación mandatoria por sobreendeudamiento crítico. En este segmento la tasa de mora escala a 16.86% (44 casos de impago), concentrando más del 57% de todas las pérdidas crediticias de la entidad.", "3. Tranche Rojo (Denegación Mandatoria):")
    
    add_paragraph(doc, "La Tabla 13 expone la simulación de amortización francesa sobre una solicitud de 100,000 CZK al 8% de interés anual frente a un salario referencial de 10,000 CZK:")
    
    tbl13_headers = ["Plazo Evaluado", "Cuota Mensual Estimada", "Salario Referencial", "Ratio Endeudamiento", "Condición de Utilidad (≤ 30%)", "Decisión del Sistema de Recomendación"]
    tbl13_rows = [
        ["12 meses", "8,698.84 CZK", "10,000 CZK", "86.99%", "Inviable (> 30%)", "Rechazado: Alto riesgo de insolvencia / sobreendeudamiento"],
        ["24 meses", "4,522.73 CZK", "10,000 CZK", "45.23%", "Inviable (> 30%)", "Rechazado: Cuota asfixiante sobre el presupuesto familiar"],
        ["36 meses", "3,133.64 CZK", "10,000 CZK", "31.34%", "Inviable (> 30%)", "Rechazado marginal: Supera el umbral prudencial bancario"],
        ["48 meses", "2,441.29 CZK", "10,000 CZK", "24.41%", "Viable (≤ 30%)", "Recomendado: Zona de Utilidad Financiera Sostenible"],
        ["60 meses", "2,027.64 CZK", "10,000 CZK", "20.28%", "Viable (≤ 30%)", "Recomendado Preferente: Máxima holgura de pago y menor mora"]
    ]
    add_table(doc, "Tabla 13: Evaluación de Reglas de Scoring y Simulación de Utilidad Financiera (df_prestamos).", tbl13_headers, tbl13_rows)
    add_figure(doc, "img/individual/fig_3c_scoring_utilidad.png", "Figura 9: Evaluación de Reglas de Scoring y Capacidad de Pago.", 5.1)
    
    add_paragraph(doc, "Interpretación analítica y recomendación de negocio: Los plazos de 12 a 36 meses comprometen más del 30% del salario (llegando al 86.99% en 12 meses), lo que induciría a mora inminente. Por tanto, el recomendador descarta estos plazos y canaliza la oferta exclusivamente hacia 48 meses (24.41%) y 60 meses (20.28%), asegurando que el cliente mantenga capacidad de amortización y solvencia patrimonial sostenida.")
    
    # Dictamen Eje 3
    add_heading(doc, 5, "Conclusión y Dictamen del Mejor Método sobre df_prestamos")
    add_paragraph(doc, "Dictamen Técnico: El Sistema Basado en Reglas de Scoring y Función de Utilidad Financiera (Modelo 3C) es el método rector indispensable para df_prestamos, salvaguardando la solvencia institucional. Como motor secundario, TF-IDF (Modelo 3A) resuelve óptimamente el arranque en frío de productos crediticios a partir de sus cláusulas contractuales.")
    
    # -------------------------------------------------------------------------
    # 2.7.7 EJE 4: df_cliente_consolidado
    # -------------------------------------------------------------------------
    add_heading(doc, 4, "2.7.7 EJE 4: Modelos sobre el DataFrame de Clientes (df_cliente_consolidado)")
    add_paragraph(doc, "df_cliente_consolidado consolida la visión integral 360° de los 5,369 clientes bancarios con 30 variables sociodemográficas y de comportamiento financiero acumulado. Es la base maestra para resolver el arranque en frío de usuarios (User Cold Start) y realizar agrupaciones cliente a cliente.")
    
    # Modelo 4A
    add_heading(doc, 5, "Modelo 4A: Filtrado Demográfico por Estereotipos (Afinidad por Brecha)")
    add_paragraph(doc, "Fundamento teórico y formulación: Basado en Rich (1979), segmenta la cartera en 9 arquetipos demográficos exhaustivos cruzando tres macro-regiones (Metropolitana Praga, Bohemia Centro-Oeste y Moravia Este) con tres intervalos etarios (Jóvenes <30 años, Adultos 30-50 años y Adultos Mayores >50 años). La recomendación se genera calculando la brecha insatisfecha entre el consumo medio del arquetipo y lo contratado por el cliente individual:")
    add_block_math(doc, r"\text{Afinidad}(u, i) = \overline{C}_{\text{estereotipo}(u), i} - C_{u, i}")
    
    add_paragraph(doc, "La Tabla 14 resume las características operativas y tasas medias de adopción de los 9 estereotipos:")
    
    tbl14_headers = ["Macro-Región", "Rango Etario", "Clientes (N)", "% Cartera", "Adopción Préstamos (%)", "Órdenes Activas Prom.", "Saldo Promedio (CZK)"]
    tbl14_rows = [
        ["Metropolitana (Praga)", "Joven (<30)", "154", "2.9%", "18.8%", "1.34", "39,094.48"],
        ["Metropolitana (Praga)", "Adulto (30-50)", "245", "4.6%", "18.0%", "1.37", "39,804.66"],
        ["Metropolitana (Praga)", "Adulto Mayor (>50)", "264", "4.9%", "10.6%", "1.15", "33,594.09"],
        ["Bohemia (Centro-Oeste)", "Joven (<30)", "695", "12.9%", "13.5%", "1.25", "38,522.71"],
        ["Bohemia (Centro-Oeste)", "Adulto (30-50)", "1,075", "20.0%", "13.6%", "1.23", "39,658.97"],
        ["Bohemia (Centro-Oeste)", "Adulto Mayor (>50)", "1,079", "20.1%", "11.4%", "1.16", "32,233.85"],
        ["Moravia (Este)", "Joven (<30)", "433", "8.1%", "12.5%", "1.20", "37,614.83"],
        ["Moravia (Este)", "Adulto (30-50)", "709", "13.2%", "12.6%", "1.23", "39,322.29"],
        ["Moravia (Este)", "Adulto Mayor (>50)", "715", "13.3%", "11.5%", "1.13", "32,765.23"],
        ["TOTAL / MEDIA GLOBAL", "—", "5,369", "100.0%", "12.7%", "1.21", "36,187.35"]
    ]
    add_table(doc, "Tabla 14: Caracterización y Consumo Medio de los 9 Estereotipos Sociodemográficos (df_cliente_consolidado).", tbl14_headers, tbl14_rows)
    add_figure(doc, "img/individual/fig_4a_estereotipos.png", "Figura 10: Tasa de Adopción Crediticia por los 9 Estereotipos Demográficos.", 4.8)
    
    add_paragraph(doc, "Validación estadística y de negocio: La dependencia entre estereotipo y adopción crediticia es estadísticamente rotunda (Chi-cuadrado χ² = 63.7832, 8 gl, p = 8.39 × 10^(-11) < 0.0001). Los jóvenes de Praga presentan la tasa de adopción crediticia más elevada (18.8%), mientras que en adultos mayores de Bohemia y Moravia la adopción desciende a 11.4% y 11.5%, reflejando el ciclo biológico de desendeudamiento en edades de jubilación. Este modelo otorga cobertura perfecta del 100% de la cartera desde el día cero.")
    add_paragraph(doc, "Recomendación estratégica de producto: Configurar paquetes de bienvenida diferenciados por región: préstamos de consumo y tarjetas en Praga, y productos de ahorro pasivo en Moravia.")
    
    # Modelo 4B
    add_heading(doc, 5, "Modelo 4B: Filtrado Colaborativo Usuario a Usuario (User-to-User Cosine)")
    add_paragraph(doc, "Fundamento teórico y formulación: Localiza vecinos o 'gemelos financieros' calculando la similitud del coseno sobre las variables numéricas estandarizadas de los 4,500 clientes titulares independientes, prediciendo la afinidad hacia un producto mediante el promedio ponderado de sus k vecinos más cercanos (k = 5):")
    add_block_math(doc, r"\cos(\vec{x}_u, \vec{x}_v) = \frac{\vec{x}_u \cdot \vec{x}_v}{\|\vec{x}_u\| \|\vec{x}_v\|}, \quad \text{Score}(u, i) = \frac{\sum_{v \in N_k(u)} \cos(\vec{x}_u, \vec{x}_v) \cdot r_{v, i}}{\sum_{v \in N_k(u)} |\cos(\vec{x}_u, \vec{x}_v)|}")
    
    add_paragraph(doc, "Distinción entre validación predictiva y recomendación en producción:")
    add_bullet(doc, "En la validación experimental Leave-One-Out (k=5 vecinos sobre 4,500 titulares), se ocultó la etiqueta real de préstamo de cada titular. Para el Cliente #2 (quien en la realidad posee crédito), sus 5 vecinos más cercanos en R^5 arrojaron un score ponderado de 0.6002, prediciendo exitosamente su condición de prestatario como verdadero positivo. El modelo global alcanzó un AUC de 0.7905 y un Brier Score de 0.1098, superando al baseline ingenuo (Brier = 0.1286, AUC = 0.50).", "Validación Predictiva (Leave-One-Out):")
    add_bullet(doc, "En un entorno comercial productivo, recomendar un préstamo al Cliente #2 carece de sentido porque ya lo tiene contratado. El sistema evalúa entonces los servicios no poseídos: concretamente SEGURO. Al auditar la vecindad, 3 de sus 5 vecinos más cercanos (Cliente #9173, #6922 y #2235) poseen póliza activa, arrojando un score ponderado de propensión de 0.6002 hacia seguros, cinco veces superior a la tasa base de seguros en titulares (11.82%, 532 de 4,500). Se aclara que este score ponderado representa un índice relativo de afinidad para ordenamiento Top-N, no una probabilidad calibrada en sentido bayesiano estricto.", "Recomendación Comercial en Producción:")
    add_bullet(doc, "Se precisa que la tasa base de crédito es del 15.16% en los 4,500 titulares independientes evaluados en 4B (682 / 4,500), frente al 12.70% en la población total de 5,369 clientes (que incluye disponentes sin cuentas).", "Aclaración de Tasas Base:")
    
    add_paragraph(doc, "Advertencia metodológica sobre riesgo de fuga (Data Leakage): Las variables de comportamiento acumulado (total_transacciones y monto_total_ordenes_mensual) incluyen contablemente las cuotas de amortización crediticia para quienes obtuvieron préstamo. Esto explica parte del elevado poder predictivo observado (AUC = 0.7905 frente a baseline ingenuo de 0.50 y regresión logística de 0.8380). En producción, el vector debe calcularse sobre variables no crediticias.")
    
    add_paragraph(doc, "Mecanismo matemático del Coseno 1.0000 en disponentes: En análisis iniciales, clientes autorizados arrojaban similitud unitaria debido a que sus variables brutas eran cero; al estandarizar Z-Score, los vectores nulos colapsaban en el mismo punto (-mu / sigma). Al restringir el espacio a los 4,500 titulares independientes, este artefacto desaparece, revelando gemelos financieros genuinos (ej. Cliente #2 y Cliente #107 con cos = +0.9902). La Tabla 15 expone la matriz de similitud entre clientes titulares:")
    
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
    
    add_paragraph(doc, "Interpretación analítica y recomendación de negocio: La alta correlación entre Cliente #2 y Cliente #107 (+0.9902) confirma la viabilidad de transferir sugerencias comerciales entre gemelos comportamentales maduros. Asimismo, la divergencia pronunciada con Cliente #19 (-0.9455) previene ofertar productos de consumo acelerado a clientes patrimoniales pasivos.")
    
    # Modelo 4C
    add_heading(doc, 5, "Modelo 4C: Correlación de Pearson Multivariante de Perfil Financiero")
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
    
    add_paragraph(doc, "Interpretación analítica y recomendación de negocio: La asociación más fuerte ocurre entre Transacciones y Órdenes Activas (r = +0.4965), indicando que los clientes con alta operatividad diaria son el público ideal para campañas de domiciliación. La correlación entre Órdenes y Préstamo (+0.3375) tiene un vínculo estructural mecánico (el crédito genera la orden de amortización). La correlación negativa entre Edad y Saldo (-0.2448) y con Préstamos (-0.1082) confirma la contracción del gasto en etapas avanzadas de la vida.")
    
    # Dictamen Eje 4
    add_heading(doc, 5, "Conclusión y Dictamen del Mejor Método sobre df_cliente_consolidado")
    add_paragraph(doc, "Dictamen Técnico: Se dictamina una arquitectura híbrida en dos fases: Filtrado Demográfico por Estereotipos (Modelo 4A) como motor imprescindible de bienvenida (cobertura 100%), complementado con Filtrado Colaborativo Usuario a Usuario (Modelo 4B, AUC = 0.7905) para la cartera madura con historial transaccional consolidado.")
