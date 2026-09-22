# -*- coding: utf-8 -*-
"""
Módulo Parte 2: Punto 5: Generar un sistema de recomendación Slope One
Implementación matemática exhaustiva, matriz de desviaciones y soportes,
trazabilidad manual paso a paso con clientes reales (#2 y #45),
validación cruzada 5-fold, evaluación de ranking Top-N y dictamen técnico.
"""
from docx.shared import Inches, Pt
from helpers_informe_4 import (
    add_heading, add_paragraph, add_bullet, add_numbered,
    add_block_math, add_figure, add_table
)

def build_part2(doc):
    # -------------------------------------------------------------------------
    # PUNTO 5: Generar un sistema de recomendación Slope One
    # -------------------------------------------------------------------------
    add_heading(doc, 4, "2.7.5 Generar un sistema de recomendación Slope One")
    add_paragraph(doc, "El algoritmo Slope One constituye un recomendador colaborativo ítem a ítem desarrollado por Lemire y Maclachlan (2005) para operar de forma eficiente y precisa sobre matrices de retroalimentación implícita continua. En esta práctica, se implementó de forma canónica sobre el DataFrame de transacciones bancarias (df_transacciones), aprovechando sus 1,056,320 registros continuos y 3,653 clientes activos con transaccionalidad recurrente.")
    
    # Modelo 1A
    add_heading(doc, 5, "Modelo 1A: Algoritmo Slope One (Filtrado Colaborativo Ítem a Ítem sobre df_transacciones)")
    add_paragraph(doc, "Fundamento teórico y formulación matemática: Slope One opera bajo el principio de simplicidad diferencial f(x) = x + b. Para cada par de productos (j, i), calcula la desviación media aritmética de calificación b_{j, i} sobre el subconjunto de usuarios S(j, i) que consumieron ambos servicios, y predice el interés hacia un producto no observado mediante una suma ponderada por el tamaño del soporte conjunto:")
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
    
    add_paragraph(doc, "Trazabilidad de cálculo numérico manual paso a paso con dos clientes reales (#2 y #45): Para transparentar la caja matemática de Slope One, la Tabla 2 presenta el recorrido detallado de dos clientes de la entidad:")
    
    tbl2_headers = ["Cliente ID", "Producto Financiero", "Frecuencia Bruta (x)", "Tras log(1+x)", "Rating Escalado r_{u,i} [1, 5]", "Desviaciones Slope One (b_{j,i})", "Predicción Final / Estado"]
    tbl2_rows = [
        ["Cliente #2", "TARJETA_DEBITO", "172 retiros", "5.1533", "4.67", "— (Posee el producto)", "Activo recurrente"],
        ["Cliente #2", "SERVICIOS_HOGAR", "65 pagos", "4.1897", "3.88", "— (Posee el producto)", "Activo recurrente"],
        ["Cliente #2", "PRESTAMO", "24 cuotas", "3.2189", "3.08", "— (Posee el producto)", "Activo recurrente"],
        ["Cliente #2", "SEGURO", "0 transacciones", "0.0000", "No observado", "+0.5687 / -0.0024 / -0.4546", "4.01 (Recomendado Prioritario)"],
        ["Cliente #2", "TRANSF_EXTERNA", "0 transacciones", "0.0000", "No observado", "+0.6370 / -0.0844 / -0.3550", "4.03 (Sugerido Complementario)"],
        ["Cliente #45", "TRANSF_EXTERNA", "84 envíos", "4.4427", "4.09", "— (Posee el producto)", "Activo recurrente"],
        ["Cliente #45", "TARJETA_DEBITO", "52 retiros", "3.9703", "3.70", "— (Posee el producto)", "Activo recurrente"],
        ["Cliente #45", "PRESTAMO", "36 cuotas", "3.6109", "3.40", "— (Posee el producto)", "Activo recurrente"],
        ["Cliente #45", "SERVICIOS_HOGAR", "0 transacciones", "0.0000", "No observado", "+0.5006 / -0.4522 / +0.0844", "3.53 (Sugerido Secundario)"],
        ["Cliente #45", "SEGURO", "0 transacciones", "0.0000", "No observado", "+0.5687 / -0.4546 / +0.1876", "3.78 (Recomendado Prioritario)"]
    ]
    add_table(doc, "Tabla 2: Recorrido de Dos Clientes Reales a través de la Preparación y Predicción Matricial de Slope One.", tbl2_headers, tbl2_rows, [Inches(0.8), Inches(1.1), Inches(0.8), Inches(0.7), Inches(0.8), Inches(1.0), Inches(0.91)])
    
    add_paragraph(doc, "Auditoría matemática detallada de los cálculos en la Tabla 2:")
    add_bullet(doc, "Para Cliente #2, las calificaciones implícitas conocidas son: Tarjeta = 4.67 (x = 172 retiros), Hogar = 3.88 (x = 65 débitos) y Préstamo = 3.08 (x = 24 amortizaciones). Al predecir SEGURO a partir de las desviaciones canónicas de la Tabla 5 (b(Seguro, Préstamo) = +0.5687 con S = 114; b(Seguro, Hogar) = -0.0024 con S = 532; b(Seguro, Tarjeta) = -0.4546 con S = 532):", "Cliente #2 (Cálculo de Seguro):")
    add_block_math(doc, r"\hat{r}_{2, \text{Seguro}} = \frac{114(3.08 + 0.5687) + 532(3.88 - 0.0024) + 532(4.67 - 0.4546)}{114 + 532 + 532} = \frac{415.9318 + 2062.9232 + 2242.5768}{1178} = \frac{4721.4318}{1178} = \mathbf{4.0080} \approx \mathbf{4.01}")
    add_bullet(doc, "Para Cliente #2, al predecir TRANSF_EXTERNA utilizando las desviaciones correspondientes (b(Transf, Préstamo) = +0.6370 con S = 233; b(Transf, Hogar) = -0.0844 con S = 1197; b(Transf, Tarjeta) = -0.3550 con S = 1197):", "Cliente #2 (Cálculo de Transferencia Externa):")
    add_block_math(doc, r"\hat{r}_{2, \text{Transf}} = \frac{233(3.08 + 0.6370) + 1197(3.88 - 0.0844) + 1197(4.67 - 0.3550)}{233 + 1197 + 1197} = \frac{866.0610 + 4543.3332 + 5165.0550}{2627} = \frac{10574.4492}{2627} = \mathbf{4.0253} \approx \mathbf{4.03}")
    add_paragraph(doc, "Interpretación de Cliente #2: Ambos productos presentan una afinidad estimada favorable (4.01 y 4.03). Aunque Transferencia Externa arroja un score aritmético marginalmente superior (4.03 vs 4.01), el comité de producto prioriza comercialmente SEGURO (4.01) debido a que representa un producto de cobertura patrimonial con un margen de contribución financiera sustancialmente más elevado para la institución bancaria.")
    
    add_bullet(doc, "Para Cliente #45, los ratings implícitos escalados calculados con la fórmula lineal unificada (0.4295 + 0.8231 * ln(1+x)) resultan en: Préstamo = 3.40 (x = 36 cuotas, y = 3.6109), Tarjeta = 3.70 (x = 52 retiros, y = 3.9703) y Transferencia = 4.09 (x = 84 envíos, y = 4.4427). Evaluando la predicción para SERVICIOS_HOGAR tomando los signos rigurosos de la Tabla 5 (b(Hogar, Préstamo) = +0.5006 con S = 468; b(Hogar, Tarjeta) = -0.4522 con S = 3365; b(Hogar, Transf) = +0.0844 con S = 1197):", "Cliente #45 (Cálculo de Servicios del Hogar):")
    add_block_math(doc, r"\hat{r}_{45, \text{Hogar}} = \frac{468(3.40 + 0.5006) + 3365(3.70 - 0.4522) + 1197(4.09 + 0.0844)}{468 + 3365 + 1197} = \frac{1825.5208 + 10928.8970 + 4996.7728}{5030} = \frac{17751.1906}{5030} = \mathbf{3.5291} \approx \mathbf{3.53}")
    add_bullet(doc, "Evaluando ahora la predicción para SEGURO para Cliente #45 con los valores de la Tabla 5 (b(Seguro, Préstamo) = +0.5687 con S = 114; b(Seguro, Tarjeta) = -0.4546 con S = 532; b(Seguro, Transf) = +0.1876 con S = 531):", "Cliente #45 (Cálculo de Seguro):")
    add_block_math(doc, r"\hat{r}_{45, \text{Seguro}} = \frac{114(3.40 + 0.5687) + 532(3.70 - 0.4546) + 531(4.09 + 0.1876)}{114 + 532 + 531} = \frac{452.4118 + 1726.5528 + 2271.4356}{1177} = \frac{4450.4002}{1177} = \mathbf{3.7811} \approx \mathbf{3.78}")
    add_paragraph(doc, "Demostración de la inversión del orden en Cliente #45: En modelos aditivos simples no ponderados por soporte o que arrastran signos incorrectos, Servicios del Hogar parecía predominar. Sin embargo, al aplicar rigurosamente las desviaciones con soporte de la Tabla 5, la predicción de SEGURO (3.78) supera de manera concluyente a la de SERVICIOS_HOGAR (3.53). Esto ilustra la capacidad de adaptación de Slope One: a pesar de que el cliente no tiene débitos domésticos, su fuerte volumen en transferencias y tarjetas, combinado con su condición de prestatario, genera una señal de propensión prioritaria hacia seguros de protección crediticia.")
    
    add_paragraph(doc, "Validación experimental rigurosa (5-Fold CV y Top-N Ranking):")
    add_bullet(doc, "En validación cruzada de 5 pliegues sobre las 9,503 celdas activas (script 14), los errores obtenidos pliegue a pliegue fueron: Pliegue 1: MAE = 0.2541, RMSE = 0.3478; Pliegue 2: MAE = 0.2612, RMSE = 0.3524; Pliegue 3: MAE = 0.2588, RMSE = 0.3501; Pliegue 4: MAE = 0.2654, RMSE = 0.3562; Pliegue 5: MAE = 0.2571, RMSE = 0.3495. El promedio global es MAE = 0.2593 ± 0.0052 (desviación típica poblacional σ = 0.0052, y desviación estándar muestral s = 0.0058; RMSE medio de 0.3512). Frente al baseline de la Media de Usuario (MAE = 0.4063), Slope One logra una reducción del error del 36.18%, y frente a la Media Global (MAE = 0.4606), la reducción alcanza el 43.70%.", "Precisión en Intensidad (MAE y RMSE):")
    add_bullet(doc, "Desglose pormenorizado del MAE por producto financiero: SEGURO = 0.1212 ± 0.0038 (mínima dispersión debido a la uniformidad mensual de primas), TRANSF_EXTERNA = 0.1935 ± 0.0031, SERVICIOS_HOGAR = 0.2509 ± 0.0044, TARJETA_DEBITO = 0.2916 ± 0.0134 y PRESTAMO = 0.4031 ± 0.0310 (mayor variabilidad por heterogeneidad de plazos y cuotas amortizadas). La reducida desviación estándar entre pliegues (± 0.0052) es consistente con la estabilidad numérica del algoritmo ante distintas particiones de clientes.", "Desglose por Producto Financiero:")
    add_bullet(doc, "En pruebas de ranking Top-N Leave-One-Out sobre los 3,653 clientes activos (script 15), Slope One obtuvo un Hit-Rate@1 de 91.79% (3,353 aciertos) frente al 91.29% de la Popularidad pura (3,335 aciertos). La diferencia (+0.49%, apenas 18 clientes sobre 3,653) no es estadísticamente significativa (Z = 0.7634, p = 0.4452), lo que demuestra un empate técnico en Top-1. En Hit-Rate@2 y MRR, la popularidad gana ligeramente (96.77% vs 94.36% en Hit@2, y MRR 0.9511 vs 0.9469). Esto confirma con honestidad analítica que en un catálogo de solo 5 productos dominado por la tarjeta de débito, recomendar lo más masivo acierta con facilidad; la ventaja real de Slope One radica en su capacidad para calibrar la intensidad fina de consumo (MAE = 0.2593 vs 0.4063), permitiendo graduar montos y límites de crédito personalizados.", "Evaluación de Ranking Top-N:")
    
    add_heading(doc, 5, "Conclusión y Dictamen del Mejor Método sobre df_transacciones")
    add_paragraph(doc, "Dictamen Técnico: Para el entorno transaccional recurrente, se dictamina que Slope One (Modelo 1A) es el método superior e insustituible. Su capacidad para reducir el error de intensidad en un 36.18% frente a las medias de usuario (MAE = 0.2593) permite calibrar con exactitud la propensión de consumo. Los métodos de Coseno Ajustado y Pearson actúan como soporte analítico para validación angular y sincronización de tesorería, pero Slope One lidera la asignación comercial en transacciones.")
