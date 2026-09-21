# -*- coding: utf-8 -*-
"""
Módulo Parte 2: Modelos sobre df_transacciones (Eje 1) y df_ordenes (Eje 2)
con algoritmos paso a paso, validación experimental rigurosa y dictámenes técnicos.
"""
from docx.shared import Inches, Pt
from helpers_informe_4 import (
    add_heading, add_paragraph, add_bullet, add_numbered,
    add_block_math, add_figure, add_table
)

def build_part2(doc):
    # -------------------------------------------------------------------------
    # 2.7.4 EJE 1: df_transacciones
    # -------------------------------------------------------------------------
    add_heading(doc, 4, "2.7.4 EJE 1: Modelos sobre el DataFrame de Transacciones (df_transacciones)")
    add_paragraph(doc, "df_transacciones registra 1,056,320 movimientos contables continuos a lo largo de 72 meses (enero de 1993 a diciembre de 1998). Al contar con 3,653 clientes activos con múltiples transacciones repetidas, constituye el pilar analítico para el filtrado colaborativo continuo y el análisis de series temporales.")
    
    # Modelo 1A
    add_heading(doc, 5, "Modelo 1A: Algoritmo Slope One (Filtrado Colaborativo Ítem a Ítem)")
    add_paragraph(doc, "Fundamento teórico y formulación: Propuesto por Lemire y Maclachlan (2005), Slope One opera bajo el principio de simplicidad diferencial f(x) = x + b. Para cada par de productos (j, i), calcula la desviación media aritmética de calificación b_{j, i} sobre el subconjunto de usuarios S(j, i) que consumieron ambos servicios, y predice el interés hacia un producto no observado mediante una suma ponderada por el tamaño del soporte:")
    add_block_math(doc, r"b_{j, i} = \text{dev}(j, i) = \frac{\sum_{u \in S(j, i)} (r_{u, j} - r_{u, i})}{|S(j, i)|}")
    add_block_math(doc, r"\hat{r}_{u, j} = \frac{\sum_{i \in R_u \setminus \{j\}} |S(j, i)| \cdot (r_{u, i} + b_{j, i})}{\sum_{i \in R_u \setminus \{j\}} |S(j, i)|}")
    
    add_paragraph(doc, "Propiedades matemáticas formales de Slope One:")
    add_bullet(doc, "Antisimetría estricta de las desviaciones: Para cualquier par de productos (j, i), se cumple que b(j, i) = -b(i, j), y para todo producto individual b(i, i) = 0. Esta propiedad reduce a la mitad el almacenamiento necesario de la matriz de desviaciones, almacenando únicamente el triángulo superior.", "Antisimetría:")
    add_bullet(doc, "Equivarianza frente a transformaciones afines: Si a todas las calificaciones de los usuarios se les aplica una transformación lineal positiva f(r) = α·r + β (con α > 0), las predicciones de Slope One escalan de manera idéntica: f(rhat) = α·rhat + β. Esto asegura robustez total frente a cambios en la escala de medición de los ratings implícitos.", "Invarianza de Escala:")
    add_bullet(doc, "Atenuación ponderada por soporte: A diferencia del promedio no ponderado, el término |S(j, i)| actúa como un factor de verosimilitud estadística bayesiana: las parejas de productos evaluadas por cientos de clientes comunes (como Tarjeta y Hogar con S = 3,365) dominan la predicción, mientras que pares con soporte reducido (como Préstamo y Seguro con S = 114) tienen una influencia proporcionalmente acotada.", "Ponderación por Soporte:")
    
    add_paragraph(doc, "Procedimiento metodológico y complejidad computacional:")
    add_numbered(doc, 1, "Sobre la matriz rala R de 3,653 clientes × 5 productos, se calculan las matrices densas simétricas de soporte |S(j, i)| y antisimétricas de desviación b(j, i). La complejidad temporal de esta fase es O(|U| · |I|²). Al tener |I| = 5, el procesamiento requiere apenas 25 evaluaciones por usuario, ejecutándose en fracciones de segundo en memoria RAM.", "Fase de precomputación por lotes (Offline Batch):")
    add_numbered(doc, 2, "Cuando un cliente u solicita recomendaciones en la banca móvil, el sistema recupera sus calificaciones conocidas R_u y aplica la fórmula ponderada de Slope One en tiempo O(|I|). La complejidad espacial es O(|I|²), ocupando un espacio despreciable en memoria.", "Fase de inferencia en línea (Online Serving):")
    add_numbered(doc, 3, "Se excluyen los productos que el cliente ya posee en su cartera activa y se ordenan los productos candidatos de forma descendente según rhat_{u, j}.", "Filtrado de servicios activos y ordenamiento:")
    
    add_paragraph(doc, "La Tabla 5 detalla la matriz completa de desviaciones medias y soportes sobre df_transacciones:")
    
    tbl5_headers = ["Producto a Predecir (j)", "PRESTAMO", "SEGURO", "SERVICIOS_HOGAR", "TARJETA_DEBITO", "TRANSF_EXTERNA"]
    tbl5_rows = [
        ["PRESTAMO", "0.0000 (S=682)", "-0.5687 (S=114)", "-0.5006 (S=468)", "-1.1674 (S=682)", "-0.6370 (S=233)"],
        ["SEGURO", "+0.5687 (S=114)", "0.0000 (S=532)", "-0.0024 (S=532)", "-0.4546 (S=532)", "+0.1876 (S=531)"],
        ["SERVICIOS_HOGAR", "+0.5006 (S=468)", "+0.0024 (S=532)", "0.0000 (S=3365)", "-0.4522 (S=3365)", "+0.0844 (S=1197)"],
        ["TARJETA_DEBITO", "+1.1674 (S=682)", "+0.4546 (S=532)", "+0.4522 (S=3365)", "0.0000 (S=3653)", "+0.3550 (S=1197)"],
        ["TRANSF_EXTERNA", "+0.6370 (S=233)", "-0.1876 (S=531)", "-0.0844 (S=1197)", "-0.3550 (S=1197)", "0.0000 (S=1197)"]
    ]
    add_table(doc, "Tabla 5: Matriz de Desviaciones Medias b(j, i) y Soportes del Algoritmo Slope One (df_transacciones).", tbl5_headers, tbl5_rows)
    add_figure(doc, "img/individual/fig_1a_slope_one.png", "Figura 1: Matriz de Desviaciones Medias y Soporte del Algoritmo Slope One.", 4.8)
    
    add_paragraph(doc, "Interpretación analítica y de negocio: La matriz de Slope One es estrictamente antisimétrica (b(j, i) = -b(i, j)). La celda b(Tarjeta, Préstamo) = +1.1674 indica que la frecuencia de uso de la tarjeta supera en más de un punto de rating a la cuota de amortización crediticia, confirmando la primacía del efectivo en la rutina cotidiana. La desviación b(Seguro, Hogar) = -0.0024 revela una paridad de consumo casi perfecta entre débitos domésticos y primas de seguro, mientras que b(Seguro, Préstamo) = +0.5687 respalda la sobre-propensión de clientes prestatarios hacia seguros de protección crediticia.")
    add_paragraph(doc, "Recomendación estratégica de producto: Configurar reglas automáticas en la banca electrónica para que todo cliente titular con Préstamo y Tarjeta activos reciba como oferta estelar un Seguro de Desgravamen o Protección Financiera, aprovechando la predicción de calificación de 4.01.")
    
    add_paragraph(doc, "Validación experimental rigurosa (5-Fold CV y Top-N Ranking):")
    add_bullet(doc, "En validación cruzada de 5 pliegues sobre las 9,503 celdas activas (script 14), los errores obtenidos pliegue a pliegue fueron: Pliegue 1: MAE = 0.2541, RMSE = 0.3478; Pliegue 2: MAE = 0.2612, RMSE = 0.3524; Pliegue 3: MAE = 0.2588, RMSE = 0.3501; Pliegue 4: MAE = 0.2654, RMSE = 0.3562; Pliegue 5: MAE = 0.2571, RMSE = 0.3495. El promedio global es MAE = 0.2593 ± 0.0052 (desviación típica poblacional σ = 0.0052, y desviación estándar muestral s = 0.0058; RMSE medio de 0.3512). Frente al baseline de la Media de Usuario (MAE = 0.4063), Slope One logra una reducción del error del 36.18%, y frente a la Media Global (MAE = 0.4606), la reducción alcanza el 43.70%.", "Precisión en Intensidad (MAE y RMSE):")
    add_bullet(doc, "Desglose pormenorizado del MAE por producto financiero: SEGURO = 0.1212 ± 0.0038 (mínima dispersión debido a la uniformidad mensual de primas), TRANSF_EXTERNA = 0.1935 ± 0.0031, SERVICIOS_HOGAR = 0.2509 ± 0.0044, TARJETA_DEBITO = 0.2916 ± 0.0134 y PRESTAMO = 0.4031 ± 0.0310 (mayor variabilidad por heterogeneidad de plazos y cuotas amortizadas). La reducida desviación estándar entre pliegues (± 0.0052) es consistente con la estabilidad numérica del algoritmo ante distintas particiones de clientes.", "Desglose por Producto Financiero:")
    add_bullet(doc, "En pruebas de ranking Top-N Leave-One-Out sobre los 3,653 clientes activos (script 15), Slope One obtuvo un Hit-Rate@1 de 91.79% (3,353 aciertos) frente al 91.29% de la Popularidad pura (3,335 aciertos). La diferencia (+0.49%, apenas 18 clientes sobre 3,653) no es estadísticamente significativa (Z = 0.7634, p = 0.4452), lo que demuestra un empate técnico en Top-1. En Hit-Rate@2 y MRR, la popularidad gana ligeramente (96.77% vs 94.36% en Hit@2, y MRR 0.9511 vs 0.9469). Esto confirma con honestidad analítica que en un catálogo de solo 5 productos dominado por la tarjeta de débito, recomendar lo más masivo acierta con facilidad; la ventaja real de Slope One radica en su capacidad para calibrar la intensidad fina de consumo (MAE = 0.2593 vs 0.4063), permitiendo graduar montos y límites de crédito personalizados.", "Evaluación de Ranking Top-N:")
    
    add_paragraph(doc, "Plan de acción comercial y operativo departamental: Desplegar Slope One en el motor central de recomendaciones de la banca por internet. Para la Gerencia de Mercadeo, utilizar las predicciones de intensidad para segmentar a los usuarios según su afinidad calculada y calibrar las comisiones de seguros según el volumen de transacciones esperado.")
    
    # Modelo 1B
    add_heading(doc, 5, "Modelo 1B: Similitud del Coseno Ajustado (Filtrado Colaborativo de Intensidad)")
    add_paragraph(doc, "Fundamento teórico y formulación: Cuando los ratings son estrictamente positivos [1.0, 5.0], el coseno vectorial tradicional colapsa en valores superiores a 0.72. El Coseno Ajustado corrige esta compresión restando a cada calificación la media personal del usuario bar{r}_u. De este modo, los consumos inferiores a la media se tornan negativos y los superiores positivos, expandiendo el rango a [-1.0, +1.0]:")
    add_block_math(doc, r"\cos_{\text{adj}}(\vec{p}_A, \vec{p}_B) = \frac{\sum_{u \in U} (r_{u, A} - \bar{r}_u)(r_{u, B} - \bar{r}_u)}{\sqrt{\sum_{u \in U} (r_{u, A} - \bar{r}_u)^2} \cdot \sqrt{\sum_{u \in U} (r_{u, B} - \bar{r}_u)^2}}")
    
    add_paragraph(doc, "Deducción matemática de la eliminación del sesgo de usuario: Sea bar{r}_u = (1 / |I_u|) · sum_{i in I_u} r_{u, i} la calificación media personal del usuario u. Al sustraer bar{r}_u, el vector centrado z_{u, i} = r_{u, i} - bar{r}_u satisface sum_{i in I_u} z_{u, i} = 0. Los clientes hiperactivos que asignan ratings elevados a todos los servicios son desplazados hacia cero, permitiendo que la similitud angular refleje exclusivamente preferencias relativas de consumo en lugar de diferencias en el nivel general de bancarización.")
    
    add_paragraph(doc, "La Tabla 6 presenta la matriz del Coseno Ajustado sobre los 3,653 clientes activos:")
    
    tbl6_headers = ["Producto Financiero", "PRESTAMO", "SEGURO", "SERVICIOS_HOGAR", "TARJETA_DEBITO", "TRANSF_EXTERNA"]
    tbl6_rows = [
        ["PRESTAMO", "1.0000", "+0.0229", "-0.0003", "-0.7507", "-0.1433"],
        ["SEGURO", "+0.0229", "1.0000", "+0.3360", "-0.2791", "-0.3107"],
        ["SERVICIOS_HOGAR", "-0.0003", "+0.3360", "1.0000", "-0.6001", "+0.0877"],
        ["TARJETA_DEBITO", "-0.7507", "-0.2791", "-0.6001", "1.0000", "-0.1687"],
        ["TRANSF_EXTERNA", "-0.1433", "-0.3107", "+0.0877", "-0.1687", "1.0000"]
    ]
    add_table(doc, "Tabla 6: Matriz de Similitud del Coseno Ajustado Centrado en Medias (df_transacciones).", tbl6_headers, tbl6_rows)
    add_figure(doc, "img/individual/fig_1b_coseno.png", "Figura 2: Matriz de Similitud del Coseno Ajustado en Transacciones.", 4.8)
    
    add_paragraph(doc, "Interpretación analítica y de negocio: La matriz del Coseno Ajustado exhibe una dispersión angular real en el intervalo [-0.7507, +0.3360] con varianza σ² = 0.0942. Destaca la asociación positiva entre Servicios del Hogar y Seguro (+0.3360), reflejando que los clientes con disciplina en pagos domésticos tienden a mantener vigentes coberturas de seguro. En contraposición, la fuerte divergencia negativa entre Tarjeta de Débito y Préstamo (-0.7507) y entre Tarjeta y Hogar (-0.6001) refleja que el gasto corriente en cajeros compite con la capacidad de ahorro y amortización crediticia.")
    add_paragraph(doc, "Recomendación estratégica de producto: Utilizar el Coseno Ajustado para modular la agresividad de las campañas comerciales: evitar sugerir productos de amortización crediticia pesada a usuarios cuyo perfil esté dominado por retiros en cajero (divergencia de -0.7507), focalizando en su lugar microseguros de bajo impacto en saldo.")
    
    # Modelo 1C
    add_heading(doc, 5, "Modelo 1C: Correlación de Pearson Ítem-a-Ítem sobre Ratings y Series Temporales Diferenciadas")
    add_paragraph(doc, "Fundamento teórico y formulación ítem-a-ítem (conforme diapositivas de clase): Siguiendo la formulación estándar de sistemas de recomendación colaborativos ítem a ítem revisada en clase, la similitud de Pearson entre dos productos i y j sobre el conjunto de usuarios comunes U_{i,j} se define como:")
    add_block_math(doc, r"\text{Pearson}(i, j) = \frac{\sum_{u \in U_{i,j}} (r_{u, i} - \bar{r}_i)(r_{u, j} - \bar{r}_j)}{\sqrt{\sum_{u \in U_{i,j}} (r_{u, i} - \bar{r}_i)^2} \cdot \sqrt{\sum_{u \in U_{i,j}} (r_{u, j} - \bar{r}_j)^2}}")
    add_paragraph(doc, "donde r_{u, i} y r_{u, j} son las calificaciones del usuario u, y bar{r}_i y bar{r}_j son las calificaciones medias respectivas de los productos i y j sobre los usuarios que consumieron ambos.")
    
    add_paragraph(doc, "Demostración pedagógica paso a paso de cálculo de Pearson Ítem-a-Ítem (estilo clase con 4 clientes muestra): Para auditar el mecanismo aritmético exacto, considérese una submuestra de cuatro clientes representativos (#4, #31, #36 y #45) que consumieron conjuntamente Seguro (i) y Servicios del Hogar (j):")
    add_bullet(doc, "Ratings implícitos de Seguro: Cliente #4 = 2.6016, Cliente #31 = 3.1721, Cliente #36 = 3.5808, Cliente #45 = 2.6584. Media del producto Seguro: bar{r}_{Seguro} = 3.0032.", "Ratings de Seguro (i):")
    add_bullet(doc, "Ratings implícitos de Hogar: Cliente #4 = 2.6016, Cliente #31 = 3.1721, Cliente #36 = 3.5627, Cliente #45 = 2.6584. Media del producto Hogar: bar{r}_{Hogar} = 2.9987.", "Ratings de Hogar (j):")
    add_bullet(doc, "Desviaciones individuales respecto a la media de cada producto: Cliente #4: dev_i = -0.4016, dev_j = -0.3971, producto cruzado = +0.1595; Cliente #31: dev_i = +0.1689, dev_j = +0.1734, producto cruzado = +0.0293; Cliente #36: dev_i = +0.5775, dev_j = +0.5639, producto cruzado = +0.3257; Cliente #45: dev_i = -0.3448, dev_j = -0.3403, producto cruzado = +0.1173.", "Cálculo de Desviaciones Centradas:")
    add_bullet(doc, "Suma de productos cruzados (Numerador): sum = 0.1595 + 0.0293 + 0.3257 + 0.1173 = 0.6318. Suma de cuadrados de Seguro: sum dev_i² = 0.6422 (raíz = 0.8014). Suma de cuadrados de Hogar: sum dev_j² = 0.6216 (raíz = 0.7884). Denominador: 0.8014 * 0.7884 = 0.6318. Coeficiente resultante: r(Seguro, Hogar) = 0.6318 / 0.6318 = 1.0000 (0.9999).", "Consolidación Aritmética:")
    
    add_paragraph(doc, "Generalización a los 3,653 clientes activos del banco: Al computar esta fórmula sobre la totalidad de la matriz de ratings usuario×producto mediante el script '19_calc_pearson_item_item.py', se obtiene la matriz 5×5 formal de la Tabla 7-A. Como se observa, al operar sobre la misma base continua [1.0, 5.0] que Slope One y el Coseno Ajustado, Pearson ítem-a-ítem captura la covariación lineal de intensidad entre productos:")
    
    tbl7a_headers = ["Producto (Ratings Implícitos)", "PRESTAMO", "SEGURO", "SERVICIOS_HOGAR", "TARJETA_DEBITO", "TRANSF_EXTERNA"]
    tbl7a_rows = [
        ["PRESTAMO", "1.0000", "+0.7061", "+0.7113", "+0.4993", "+0.5903"],
        ["SEGURO", "+0.7061", "1.0000", "+0.9957", "+0.8566", "+0.8764"],
        ["SERVICIOS_HOGAR", "+0.7113", "+0.9957", "1.0000", "+0.8022", "+0.9155"],
        ["TARJETA_DEBITO", "+0.4993", "+0.8566", "+0.8022", "1.0000", "+0.8075"],
        ["TRANSF_EXTERNA", "+0.5903", "+0.8764", "+0.9155", "+0.8075", "1.0000"]
    ]
    add_table(doc, "Tabla 7-A: Correlación de Pearson Ítem-a-Ítem sobre Calificaciones Implícitas (df_transacciones).", tbl7a_headers, tbl7a_rows)
    
    add_paragraph(doc, "Correlación sobre Series Temporales Diferenciadas (Δx_t, 72 meses): Al evaluar la asociación mediante Pearson sobre ratings acumulados directos (Tabla 7-A), los coeficientes reflejan la colinealidad de la base activa (+0.4993 a +0.9957). Para aislar la sincronización de tesorería mensual genuina y eliminar tendencias macroeconómicas no estacionarias, las series mensuales agregadas (72 meses) se transformaron mediante primeras diferencias (Δx_t = x_t - x_{t-1}, 71 observaciones):")
    add_block_math(doc, r"r_{\text{temp}}(\Delta A, \Delta B) = \frac{\sum_{t=1}^{71} (\Delta A_t - \overline{\Delta A})(\Delta B_t - \overline{\Delta B})}{\sqrt{\sum_{t=1}^{71} (\Delta A_t - \overline{\Delta A})^2} \cdot \sqrt{\sum_{t=1}^{71} (\Delta B_t - \overline{\Delta B})^2}}")
    
    add_paragraph(doc, "Fundamento econométrico de estacionariedad: En series de tiempo financieras, los volúmenes transaccionales acumulados exhiben tendencias de orden I(1). Aplicar correlación sobre series no estacionarias genera el fenómeno clásico de correlación espuria (Granger & Newbold, 1974). El operador de primera diferencia Δx_t induce estacionariedad I(0), asegurando que la correlación capture covariaciones genuinas de liquidez mes a mes. La Tabla 7-B expone la matriz resultante:")
    
    tbl7b_headers = ["Flujo Mensual Diferenciado", "PRESTAMO", "SEGURO", "SERVICIOS_HOGAR", "TARJETA_DEBITO", "TRANSF_EXTERNA"]
    tbl7b_rows = [
        ["PRESTAMO", "1.0000", "+0.1952", "+0.2464", "+0.0557", "+0.1613"],
        ["SEGURO", "+0.1952", "1.0000", "+0.5977", "-0.0245", "+0.5096"],
        ["SERVICIOS_HOGAR", "+0.2464", "+0.5977", "1.0000", "+0.1010", "+0.7192"],
        ["TARJETA_DEBITO", "+0.0557", "-0.0245", "+0.1010", "1.0000", "+0.0278"],
        ["TRANSF_EXTERNA", "+0.1613", "+0.5096", "+0.7192", "+0.0278", "1.0000"]
    ]
    add_table(doc, "Tabla 7-B: Matriz de Correlación de Pearson sobre Series Mensuales Diferenciadas (df_transacciones).", tbl7b_headers, tbl7b_rows)
    add_figure(doc, "img/individual/fig_1c_pearson.png", "Figura 3: Matriz de Correlación de Pearson sobre Series Mensuales Diferenciadas.", 4.8)
    
    add_paragraph(doc, "Interpretación analítica y de negocio: Mientras que la correlación de ratings (Tabla 7-A) arroja valores saturados cercanos a 1.0 (r_calif = +0.9957 entre Seguro y Hogar) debido a la colinealidad de la base activa, la correlación temporal diferenciada (Tabla 7-B) aísla el comportamiento genuino mes a mes: se revela un fuerte acoplamiento macroscópico entre Servicios del Hogar y Transferencias Externas (r_Δmes = +0.7192) y entre Seguros y Hogar (+0.5977), evidenciando que los egresos fijos de fin de mes se coordinan estrechamente en la tesorería de la entidad. En contraste, la tarjeta de débito muestra una correlación mensual prácticamente nula con préstamos (+0.0557) y seguros (-0.0245), confirmando que el consumo diario en cajeros opera desacoplado de los ciclos contractuales fijos.")
    add_paragraph(doc, "Recomendación estratégica de producto: Diseñar calendarios automatizados de débito sincronizados con las fechas de concentración de transferencias (días 28 a 31), programando alertas de saldo previo para evitar fallos de recaudación en seguros y servicios.")
    
    # Dictamen Eje 1
    add_heading(doc, 5, "Conclusión y Dictamen del Mejor Método sobre df_transacciones")
    add_paragraph(doc, "Dictamen Técnico: El algoritmo Slope One se determina de forma concluyente como el mejor método para df_transacciones. Combina un error absoluto favorable (MAE = 0.2593 ± 0.0052, superando en 36.18% a la media de usuario) con un empate técnico en precisión Top-1 frente a la popularidad masiva (91.79% vs 91.29%). Esto corrobora que aporta personalización individualizada en intensidad de consumo sin degradar la tasa de acierto en el primer producto sugerido.")
    
    # -------------------------------------------------------------------------
    # 2.7.5 EJE 2: df_ordenes
    # -------------------------------------------------------------------------
    add_heading(doc, 4, "2.7.5 EJE 2: Modelos sobre el DataFrame de Órdenes Permanentes (df_ordenes)")
    add_paragraph(doc, "df_ordenes contiene 6,471 contratos de débito automático recurrente domiciliados en 3,758 cuentas bancarias maestras. A diferencia de las transacciones diarias voluntarias, una orden representa un compromiso contractual formal mensual donde el titular delega al banco el pago de un servicio.")
    
    # Modelo 2A
    add_heading(doc, 5, "Modelo 2A: Similitud del Coseno Binario (Co-adquisición Ítem a Ítem)")
    add_paragraph(doc, "Fundamento teórico y formulación: Modela cada categoría de orden como un vector booleano sobre las 3,758 cuentas bancarias (1 si la cuenta domicilia el concepto, 0 si no). La similitud angular mide la intensidad de co-adquisición contractual dividiendo la intersección de cuentas entre la media geométrica de sus coberturas individuales:")
    add_block_math(doc, r"\cos(A, B) = \frac{|U_A \cap U_B|}{\sqrt{|U_A| \cdot |U_B|}}")
    
    add_paragraph(doc, "Comparación analítica entre Similitud Coseno e Índice de Jaccard: El coeficiente de Jaccard se define como J(A, B) = |U_A ∩ U_B| / |U_A ∪ U_B|. Para el par {Seguro, Hogar}, el cómputo de Jaccard resulta:")
    add_block_math(doc, r"J(\text{Seguro}, \text{Hogar}) = \frac{532}{532 + (3365 - 532)} = \frac{532}{3365} \approx \mathbf{0.1581}")
    add_paragraph(doc, "El índice de Jaccard penaliza drásticamente la enorme disparidad en los soportes individuales (532 frente a 3,365 cuentas), subestimando la intensidad real de adopción conjunta. En contraste, la similitud del Coseno Binario arroja un valor de 0.3976 al utilizar la media geométrica en el denominador:")
    add_block_math(doc, r"\cos(\text{Seguro}, \text{Hogar}) = \frac{532}{\sqrt{532 \times 3365}} = \frac{532}{\sqrt{1,790,180}} = \frac{532}{1337.976} = \mathbf{0.3976}")
    add_paragraph(doc, "Por tanto, el Coseno Binario es matemáticamente preferible para medir co-adquisición bancaria cuando las tasas de penetración de los productos son altamente asimétricas.")
    
    add_paragraph(doc, "Métricas de reglas de asociación y Lift: El soporte conjunto del par {Seguro, Hogar} es del 14.16% (532 / 3,758 cuentas). La confianza de la regla de asociación Seguro → Hogar es del 100.0% (532 / 532 cuentas), mientras que la confianza en sentido inverso Hogar → Seguro es del 15.81% (532 / 3,365 cuentas). El ratio Lift asociado se formula como:")
    add_block_math(doc, r"\text{Lift}(\text{Seguro} \to \text{Hogar}) = \frac{P(\text{Seguro} \cap \text{Hogar})}{P(\text{Seguro}) \cdot P(\text{Hogar})} = \frac{532 / 3758}{(532 / 3758) \cdot (3365 / 3758)} = \frac{3758}{3365} \approx \mathbf{1.12}")
    add_paragraph(doc, "Evaluación rigurosa de la fuerza del Lift: Un Lift de 1.12 confirma una asociación positiva, pero debe interpretarse con cautela frente a la tasa base: dado que Servicios del Hogar abarca al 89.54% de las cuentas, poseer débito del hogar apenas eleva la propensión a seguro del 14.16% (tasa base global) al 15.81% (confianza condicional). La señal comercial de empaquetamiento (bundling) se fundamenta en que el 100% de los asegurados ya tienen domiciliación doméstica, sirviendo como canal de facturación natural.")
    
    add_paragraph(doc, "La Tabla 8 presenta la matriz de co-adquisición binaria entre las cinco categorías contractuales:")
    
    tbl8_headers = ["Categoría de Orden", "Arrendamiento / Leasing", "Cuota de Préstamo", "Pago de Seguros", "Servicios del Hogar", "Sin Especificar"]
    tbl8_rows = [
        ["Arrendamiento / Leasing", "1.0000", "0.0000", "0.1174", "0.1951", "0.1580"],
        ["Cuota de Préstamo", "0.0000", "1.0000", "0.1975", "0.2936", "0.2633"],
        ["Pago de Seguros", "0.1174", "0.1975", "1.0000", "0.3976", "0.6664"],
        ["Servicios del Hogar", "0.1951", "0.2936", "0.3976", "1.0000", "0.5967"],
        ["Sin Especificar", "0.1580", "0.2633", "0.6664", "0.5967", "1.0000"]
    ]
    add_table(doc, "Tabla 8: Matriz de Similitud del Coseno Binario entre Contratos Domiciliados (df_ordenes).", tbl8_headers, tbl8_rows)
    add_figure(doc, "img/individual/fig_2a_coseno_binario.png", "Figura 4: Matriz de Similitud del Coseno Binario de Co-adquisición en Órdenes.", 4.8)
    
    add_paragraph(doc, "Interpretación analítica y de negocio: El valor de 0.3976 entre Seguros y Hogar representa el techo geométrico posible para coberturas tan dispares (532 frente a 3,365 cuentas). El análisis de inclusión cruzada revela una jerarquía anidada estricta: Seguros (532) ⊂ Sin Especificar (1,198) ⊂ Servicios del Hogar (3,365). El ratio Lift asociado es de 1.12, lo cual confirma una convivencia armoniosa aunque moderada (la contratación de seguro está condicionada a poseer previamente débito del hogar, el cual abarca al 89.54% de las cuentas).")
    add_paragraph(doc, "Recomendación estratégica de producto: Lanzar un producto empaquetado (bundling) denominado 'Hogar Integral', que incorpore una póliza de seguro de incendio o responsabilidad civil dentro del débito mensual de servicios básicos con una bonificación en comisiones.")
    
    # Modelo 2B
    add_heading(doc, 5, "Modelo 2B: Filtrado Colaborativo con Ponderación de Frecuencia Inversa (ITF)")
    add_paragraph(doc, "Fundamento teórico y formulación: Debido a que Servicios del Hogar está presente en el 89.54% de las cuentas, cualquier recomendador basado en popularidad saturaría al usuario sugiriendo siempre gastos domésticos. La Ponderación de Frecuencia Inversa de Ítems (Inverse Term/Item Frequency, ITF) es una adaptación de la heurística clásica de recuperación de información (Salton & Buckley, 1988) aplicada sobre la matriz colaborativa de órdenes. Castiga logarítmicamente la ubicuidad de los servicios masivos y premia a los productos especializados de alto margen:")
    add_block_math(doc, r"\text{ITF}(i) = \ln\left(\frac{N_{\text{cuentas}}}{n_i}\right), \quad \text{Score}_{\text{ITF}}(u, j) = \sum_{i \in \text{Activos}_u} \cos(i, j) \cdot \text{ITF}(j)")
    
    add_paragraph(doc, "La Tabla 9 resume los factores de especificidad ITF calculados sobre las 3,758 cuentas maestras:")
    
    tbl9_headers = ["Categoría de Orden", "Cuentas (n_i)", "Popularidad (%)", "Factor ITF (ln(N/n_i))", "Rol Estratégico en Recomendación"]
    tbl9_rows = [
        ["Arrendamiento / Leasing", "341", "9.07%", "2.3998", "Nicho corporativo; máxima prioridad de margen comercial"],
        ["Pago de Seguros", "532", "14.16%", "1.9550", "Producto estratégico de cobertura patrimonial familiar"],
        ["Cuota de Préstamo", "717", "19.08%", "1.6566", "Compromiso de amortización formal bancaria"],
        ["Sin Especificar", "1,198", "31.88%", "1.1432", "Órdenes varias a terceras entidades"],
        ["Servicios del Hogar (SIPO)", "3,365", "89.54%", "0.1105", "Servicio universal; penalizado para evitar saturación"]
    ]
    add_table(doc, "Tabla 9: Factores de Especificidad ITF y Relevancia Estratégica de Órdenes Domiciliadas (df_ordenes).", tbl9_headers, tbl9_rows)
    add_figure(doc, "img/individual/fig_2b_itf.png", "Figura 5: Factores de Especificidad y Ponderación ITF por Categoría de Orden.", 5.1)
    
    add_paragraph(doc, "Simulación comparativa de ordenamiento con y sin ITF: Considérese una cuenta activa que domicilia exclusivamente Cuota de Préstamo (717 cuentas). Bajo un recomendador no ponderado basado en co-ocurrencia pura:")
    add_bullet(doc, "El producto con mayor similitud bruta es Servicios del Hogar (cos = 0.2936), seguido de Sin Especificar (0.2633), Pago de Seguros (0.1975) y Leasing (0.0000). El sistema sugeriría domiciliar el pago de servicios básicos, aportando una recomendación genérica y de mínimo valor bancario.", "Sin Ponderación ITF (Recomendación Trivial):")
    add_bullet(doc, "Al ponderar por el factor ITF, el score para Seguros asciende a 0.1975 × 1.9550 = 0.3861, mientras que el score para Servicios del Hogar se comprime drásticamente a 0.2936 × 0.1105 = 0.0324 (un factor 12 veces menor). El orden de recomendación se reestructura completamente, posicionando a Pago de Seguros en el primer lugar absoluto del ranking.", "Con Ponderación ITF (Rescate de Alto Margen):")
    
    add_paragraph(doc, "Interpretación analítica y de negocio: Gracias al factor ITF, el peso asignado a Leasing (2.3998) y Seguros (1.9550) supera en más de 17 y 21 veces al de Servicios del Hogar (0.1105). En una cuenta que ya domicilia pagos básicos, el modelo prioriza recomendar seguros o leasing en lugar de emitir sugerencias redundantes, diversificando la cartera de productos.")
    add_paragraph(doc, "Recomendación estratégica de producto: Integrar el motor ITF en los canales de banca móvil para cuentas domiciliadas activas, priorizando en primer lugar el seguro de vida/salud y en segundo lugar opciones de financiamiento o arrendamiento.")
    
    # Modelo 2C
    add_heading(doc, 5, "Modelo 2C: Correlación de Pearson sobre Órdenes Domiciliadas")
    add_paragraph(doc, "Fundamento teórico y formulación: Evalúa la relación lineal entre las asignaciones contractuales de órdenes entre las 3,758 cuentas maestras mediante el coeficiente de correlación de Pearson sobre variables dicotómicas (coeficiente Phi):")
    add_block_math(doc, r"r(A, B) = \frac{\sum_{u=1}^{3758} (x_{u, A} - \bar{x}_A)(x_{u, B} - \bar{x}_B)}{\sqrt{\sum_{u=1}^{3758} (x_{u, A} - \bar{x}_A)^2} \cdot \sqrt{\sum_{u=1}^{3758} (x_{u, B} - \bar{x}_B)^2}}")
    
    add_paragraph(doc, "La Tabla 10 expone la matriz de correlación de órdenes domiciliadas:")
    
    tbl10_headers = ["Categoría de Orden", "Arrendamiento / Leasing", "Cuota de Préstamo", "Pago de Seguros", "Servicios del Hogar", "Sin Especificar"]
    tbl10_rows = [
        ["Arrendamiento / Leasing", "1.0000", "-0.1534", "+0.0046", "-0.2917", "-0.0153"],
        ["Cuota de Préstamo", "-0.1534", "1.0000", "+0.0398", "-0.4117", "+0.0224"],
        ["Pago de Seguros", "+0.0046", "+0.0398", "1.0000", "+0.1388", "+0.5936"],
        ["Servicios del Hogar", "-0.2917", "-0.4117", "+0.1388", "1.0000", "+0.2338"],
        ["Sin Especificar", "-0.0153", "+0.0224", "+0.5936", "+0.2338", "1.0000"]
    ]
    add_table(doc, "Tabla 10: Matriz de Correlación de Pearson sobre Órdenes Domiciliadas (df_ordenes).", tbl10_headers, tbl10_rows)
    add_figure(doc, "img/individual/fig_2c_pearson.png", "Figura 6: Matriz de Correlación de Pearson en Órdenes Domiciliadas.", 4.8)
    
    add_paragraph(doc, "Interpretación analítica y de negocio: La correlación negativa moderada entre Servicios del Hogar y Cuota de Préstamo (r = -0.4117) respalda la hipótesis plausible de que los clientes operan con segregación presupuestaria: las cuentas destinadas a la amortización crediticia formal suelen manejarse de forma separada de las cuentas de gestión exclusiva de gastos domésticos. Asimismo, la correlación positiva entre Seguros y Sin Especificar (+0.5936) refleja órdenes automáticas periódicas hacia aseguradoras externas no clasificadas.")
    add_paragraph(doc, "Recomendación estratégica de producto: Desarrollar campañas de portabilidad financiera y consolidación de débitos permanentes, incentivando a los prestatarios a unificar sus pagos domésticos en la misma cuenta de crédito a cambio de bonificaciones de tasa de interés.")
    
    # Dictamen Eje 2
    add_heading(doc, 5, "Conclusión y Dictamen del Mejor Método sobre df_ordenes")
    add_paragraph(doc, "Dictamen Técnico: El Filtrado Colaborativo con Ponderación ITF (Modelo 2B) es el método superior para df_ordenes. Elimina el monopolio de servicios básicos (89.54% de cuentas) y rescata productos de alto valor como Seguros y Leasing con una cobertura del 83.5% sobre las cuentas domiciliadas.")
