# UNIVERSIDAD TÉCNICA DE AMBATO
## FACULTAD DE INGENIERÍA EN SISTEMAS ELECTRÓNICA E INDUSTRIAL
### CARRERA DE SOFTWARE
### CICLO ACADÉMICO: AGOSTO 2026 – DICIEMBRE 2026

---

# INFORME DE GUÍA PRÁCTICA

## I. PORTADA

| Campo | Detalle |
| :--- | :--- |
| **Tema:** | Implementación y Evaluación de Sistemas de Recomendación Colaborativos, Demográficos y Basados en Contenido sobre el Modelo Transaccional de la Banca Comercial (`Financial_ijs`) |
| **Unidad de Organización Curricular:** | PROFESIONAL |
| **Nivel y Paralelo:** | 6to Software "A" |
| **Alumnos participantes:** | Cobos Taco Alison Marcela <br> Lagua Flores Henry Daniel |
| **Asignatura:** | Inteligencia de Negocios |
| **Docente:** | Ing. Ruben Nogales, Mg. |

---

## II. INFORME DE GUÍA PRÁCTICA

### 2.1 Objetivos

#### General:
Diseñar, implementar y evaluar sistemas de recomendación aplicando las técnicas de filtrado colaborativo (Slope One e Item-to-Item), similitud vectorial (Coseno), correlación lineal (Pearson) y frecuencia inversa (ITF) sobre el historial transaccional del banco `Financial_ijs`, garantizando recomendaciones no triviales y personalizadas para la fidelización y venta cruzada (*cross-selling*).

#### Específicos:
* **Construir la matriz de interacción implícita cliente-producto:** Mapear la intensidad transaccional y tenencia de contratos de los 5,369 clientes hacia una escala de afinidad estandarizada de 1.0 a 5.0 sobre los productos financieros clave.
* **Implementar y clasificar los sistemas de recomendación bajo sus paradigmas formales:** Evaluar experimentalmente el enfoque **Demográfico** (estereotipos con K-Means), **Colaborativo** (Slope One, Correlación de Pearson y Similitud de Coseno) y **Basado en Contenido** (Item-to-Item de Amazon con ponderación ITF).
* **Comparar la eficacia analítica y pertinencia de las recomendaciones:** Contrastar los resultados de los modelos sobre perfiles de clientes muestra, analizando su capacidad para mitigar el problema de arranque en frío (*Cold Start*) y su viabilidad de integración en la arquitectura DW/BI.

### 2.2 Modalidad
Presencial

### 2.3 Tiempo de duración
* **Presenciales:** 6 horas
* **No presenciales:** 0 horas

### 2.4 Instrucciones
Seguir las directrices metodológicas de la guía práctica oficial de Inteligencia de Negocios, estructurando el informe bajo la plantilla institucional con un enfoque 100% analítico sustentado exclusivamente en evidencias visuales y métricas formales, omitiendo bloques de código fuente en el cuerpo del documento.

### 2.5 Listado de equipos, materiales y recursos

#### Listado de equipos y materiales generales empleados en la guía práctica:
* Computador portátil con procesador multinúcleo y soporte para cálculo matricial en memoria.
* Entorno de ciencia de datos Python 3.12 (NumPy, Pandas, SciPy, Matplotlib, Seaborn, Scikit-Learn).
* DataFrames analíticos limpios del caso de estudio `Financial_ijs`.
* Repositorio de control de versiones Git / GitHub.

#### TAC (Tecnologías para el Aprendizaje y Conocimiento) empleados en la guía práctica:
* [x] Plataformas educativas
* [ ] Simuladores y laboratorios virtuales
* [x] Aplicaciones educativas (Visual Studio Code, Jupyter Notebooks)
* [ ] Recursos audiovisuales
* [ ] Gamificación
* [x] Inteligencia Artificial
* Otros: _____________________

---

### 2.6 Actividades por desarrollar

#### Marco Teórico y Taxonomía de Sistemas de Recomendación (Montaner et al., 2003)
En el contexto de la Inteligencia de Negocios y la minería de datos, los sistemas de recomendación constituyen herramientas analíticas orientadas a mitigar la sobrecarga de información, prediciendo la afinidad o propensión de un usuario hacia un determinado producto o servicio. De acuerdo con la taxonomía formal de Montaner et al. (2003), los sistemas se clasifican según la fuente de información y la técnica de emparejamiento utilizada:
1. **Filtrado Demográfico:** Emparejamiento entre **estereotipo** y **contenidos**. Utiliza información sociodemográfica (edad, ingresos, ubicación geográfica) para caracterizar grupos de usuarios homogéneos y formular sugerencias generales sin requerir historial transaccional previo.
2. **Filtrado Colaborativo:** Emparejamiento entre **perfiles de usuarios** ($Usuario \leftrightarrow Usuario$). Explota el comportamiento colectivo de la comunidad, infiriendo que usuarios con patrones de consumo históricos similares mantendrán preferencias afines en el futuro. Se divide en dos vertientes:
   * *Basado en Usuarios (User-Based):* Identifica vecinos cercanos para proyectar valoraciones sobre ítems no adquiridos (ej. algoritmo Slope One y Correlación de Pearson).
   * *Basado en Ítems (Item-Based):* Evalúa la co-adquisición o similitud directa entre productos a partir de las valoraciones de los clientes (ej. algoritmo Item-to-Item de Amazon y Similitud de Coseno).
3. **Filtrado Basado en Contenido:** Emparejamiento entre **perfil de usuario** y **atributos del contenido**. Compara los metadatos intrínsecos de los productos ya consumidos por el cliente con el resto del catálogo, incorporando técnicas como la Frecuencia Inversa de Ítems (ITF) para ponderar la especificidad de los artículos.

#### Arquitectura de Cómputo Empresarial: Offline, Nearline y Online
En arquitecturas de producción a gran escala (como las implementadas por Netflix y Amazon Web Services), los motores de recomendación desacoplan sus procesos en tres capas temporales para garantizar escalabilidad y baja latencia:
* **Capa Offline (Batch):** Procesa periódicamente volúmenes masivos en el Data Warehouse (entrenamiento de clústeres K-Means, matrices de diferencias Slope One y matrices de similitud de Coseno).
* **Capa Nearline (Streaming):** Captura eventos recientes en tiempo casi real mediante colas de mensajes, actualizando los perfiles de usuario sin bloquear las interfaces de consulta.
* **Capa Online (Real-Time):** Responde en menos de 50 milisegundos a las solicitudes transaccionales del cliente en la banca móvil, aplicando filtros de contexto y entregando el ranking Top-$K$ precalculado.

#### Construcción de la Matriz de Interacción Cliente-Producto Financiero
Dado que en las entidades bancarias los clientes no otorgan calificaciones explícitas de 1 a 5 estrellas, se diseñó un modelo de **retroalimentación implícita** (*implicit feedback*). Sobre la base de los 5,369 clientes y más de un millón de transacciones consolidadas, se estructuraron seis productos financieros fundamentales del banco:
1. `PRESTAMO` (`UVER`): Créditos personales concedidos y amortizaciones mensuales activas.
2. `SEGURO` (`POJISTNE`): Contratación y pago periódico de pólizas aseguradoras.
3. `SERVICIOS_HOGAR` (`SIPO`): Domiciliación recurrente de servicios básicos (agua, electricidad, gas).
4. `LEASING`: Contratos de arrendamiento financiero comercial y vehicular.
5. `TARJETA`: Operaciones activas con tarjeta de débito/crédito en cajeros y terminales punto de venta.
6. `TRANSF_EXTERNA`: Uso recurrente de canales interbancarios de envío de fondos.

La intensidad de interacción de cada cliente $u$ con el producto $i$ se estandarizó en una escala continua de $1.0$ a $5.0$ combinando la tenencia contractual con la frecuencia transaccional mediante una escala logarítmica:
$$R(u, i) = 	ext{Base} + 3.0 	imes \min\left(1.0, rac{\ln(1 + 	ext{Frecuencia}_{u,i})}{\ln(1 + 20)}ight)$$
Aquellos productos con los que el cliente nunca ha interactuado permanecen como valores vacíos (`NaN`), constituyendo el espacio de búsqueda que los algoritmos deben predecir.

---

### 2.7 Resultados obtenidos

A continuación se presentan los resultados analíticos y funcionales obtenidos tras la ejecución de los modelos de recomendación sobre el conjunto de datos bancarios. Conforme a las directrices de entrega, esta sección prescinde de código fuente y se sustenta exclusivamente en representaciones visuales, matrices de cálculo y análisis descriptivos de negocio.

---

#### 2.7.1 Sistema de Recomendación Demográfico (Estereotipos y Clústeres)

Este enfoque resuelve el problema crítico de **Arranque en Frío** (*Cold Start*), permitiendo al banco formular sugerencias comerciales inmediatas a clientes recién incorporados que carecen de historial transaccional.

![Figura 1. Sistema de Recomendación Demográfico: Segmentación K-Means](img/fig_01_sistema_demografico_clusters.png)
*Figura 1. Segmentación sociodemográfica de clientes mediante K-Means (Lloyd) sobre variables de edad y salario distrital, mostrando centroides y arquetipos de negocio.*

##### Análisis Descriptivo y de Negocio (Figura 1):
La Figura 1 ilustra la distribución de los 5,369 clientes del banco agrupados en cuatro arquetipos sociodemográficos mediante el algoritmo K-Means, evaluado sobre las dimensiones de edad, salario medio del distrito, población y saldo bancario:
* **Clúster 1 (Adultos Ahorradores - Azul):** Clientes maduros (40 a 65 años) con ingresos estables en distritos consolidados y un volumen elevado de saldo pasivo. El arquetipo demanda productos de inversión segura y seguros de retiro (`SEGURO`, `SERVICIOS_HOGAR`).
* **Clúster 2 (Jóvenes Urbanos - Naranja):** Segmento joven (18 a 35 años) radicado en distritos de alta renta (como Praga y capitales regionales) con salarios superiores a 11,000 CZK. Este grupo presenta la mayor propensión a la adopción digital y consumo a crédito, siendo el candidato óptimo para la asignación inmediata de `TARJETA` y `LEASING`.
* **Clúster 3 (Perfil Estándar - Verde):** Grupo intermedio con niveles moderados de salario (8,500 - 9,500 CZK) y transaccionalidad balanceada. Representa el núcleo operativo tradicional para la domiciliación de pagos (`SIPO`).
* **Clúster 4 (Adultos Mayores Rurales - Rojo):** Concentrado en regiones periféricas con menor densidad poblacional. Su interacción prioritaria se restringe al cobro de pensiones y operaciones en ventanilla.

**Impacto analítico:** Cuando un cliente nuevo ingresa al sistema sin transacciones, el motor demográfico determina su distancia euclídea al centroide más cercano en tiempo $O(k)$ y le asigna el catálogo predilecto de su clúster, eliminando la ceguera inicial del banco.

---

#### 2.7.2 Sistema de Recomendación Colaborativo

El filtrado colaborativo explota la inteligencia colectiva y el historial de interacción de toda la masa de clientes. Se evaluaron las dos vertientes fundamentales: basada en usuarios y basada en ítems.

##### A. Sub-enfoque Basado en Usuarios: Algoritmo Slope One (Lemire et al., 2005)
El algoritmo Slope One predice la valoración esperada mediante una relación lineal simple $f(x) = x + b$, donde $b$ representa la desviación media aritmética de calificaciones entre pares de productos evaluados simultáneamente por la comunidad.

![Figura 2. Matriz de Desviaciones y Predicciones Slope One](img/fig_02_slope_one_desviaciones_prediccion.png)
*Figura 2. Matriz de desviaciones medias b_{i,j} entre productos financieros y tabla de inferencia predictiva para clientes muestra bajo el algoritmo Slope One.*

##### Análisis Descriptivo y de Negocio (Figura 2):
La parte izquierda de la Figura 2 exhibe la matriz simétrica de diferencias $b_{i,j}$. Un valor positivo indica que el producto de la fila suele recibir una calificación implícita superior al de la columna:
* Se evidencia que `PRESTAMO` registra una desviación positiva sistemática respecto a `SERVICIOS_HOGAR` ($+0.42$) y `TARJETA` ($+0.35$), lo que refleja que los clientes que acceden a un crédito mantienen un nivel de compromiso financiero y volumen transaccional superior al promedio de servicios básicos.
* Por el contrario, la relación entre `LEASING` y `SEGURO` presenta una diferencia cercana a cero ($-0.04$), demostrando una paridad en la intensidad de uso de ambos productos de protección y financiamiento vehicular.

En la parte derecha, se observa la inferencia sobre clientes reales del banco:
* Para el **Cliente 2**, cuyos productos activos son `PRESTAMO` y `SERVICIOS_HOGAR`, el modelo proyecta que sus dos mayores afinidades insatisfechas corresponden a `SEGURO` (Score: 3.82) y `TARJETA` (Score: 3.65). Esto valida una regla de negocio coherente: quien ya tiene un crédito activo se beneficia directamente de contratar una póliza de desgravamen y una tarjeta vinculada a la cuenta.
* La gran ventaja competitiva de Slope One radica en su coste computacional: actualizar una predicción ante una nueva transacción no requiere recalcular distancias vectoriales globales, sino únicamente acumular sumas y conteos aritméticos.

---

##### B. Sub-enfoque Basado en Usuarios: Correlación de Pearson
La correlación de Pearson evalúa la tendencia de variación conjunta lineal entre las valoraciones de los productos, normalizando las desviaciones respecto a la media de cada cliente para neutralizar el sesgo de clientes hiperactivos o pasivos.

![Figura 3. Heatmap de Correlación de Pearson](img/fig_03_correlacion_pearson_heatmap.png)
*Figura 3. Matriz de Correlación de Pearson entre productos financieros en escala de -1.0 (correlación inversa) a +1.0 (correlación perfecta).*

##### Análisis Descriptivo y de Negocio (Figura 3):
El mapa de calor de la Figura 3 revela patrones determinantes de asociación financiera:
* **Fuerte correlación positiva entre `PRESTAMO` y `LEASING` ($r = +0.638$):** Existe una marcada complementariedad entre los clientes que demandan créditos personales y aquellos que gestionan arrendamiento financiero. Ambos perfiles comparten una necesidad activa de apalancamiento de capital.
* **Correlación positiva entre `SEGURO` y `SERVICIOS_HOGAR` ($r = +0.512$):** Los clientes que domicilian el pago de consumos domésticos (`SIPO`) muestran una propensión natural a domiciliar pólizas de seguros familiares (`POJISTNE`). Este hallazgo fundamenta campañas de empaquetamiento (*bundling*) donde se ofrezca un descuento en la póliza al vincularla a la orden de débito mensual.
* **Correlaciones cercanas a cero o ligeramente negativas entre `TARJETA` y `LEASING` ($r = -0.042$):** Indican independencia operativa; el uso transaccional de tarjetas de débito en cajero no predice ni condiciona la contratación de contratos de leasing corporativo, evitando recomendaciones cruzadas ineficaces.

---

##### C. Sub-enfoque Basado en Ítems: Similitud de Coseno
A diferencia de Pearson, la Similitud de Coseno mide la proximidad geométrica angular entre los vectores continuos de consumo, evaluando si dos productos son contratados por los mismos clientes independientemente de las diferencias en el saldo monetario individual.

![Figura 4. Heatmap de Similitud de Coseno](img/fig_04_similitud_coseno_heatmap.png)
*Figura 4. Matriz de Similitud de Coseno continua entre vectores de uso de productos financieros (valores de 0.0 a 1.0).*

##### Análisis Descriptivo y de Negocio (Figura 4):
La Figura 4 evidencia la convergencia vectorial en el espacio de usuarios:
* El producto `SERVICIOS_HOGAR` registra la mayor proximidad angular global frente a todos los demás ítems (valores de coseno entre $0.78$ y $0.86$), debido a su carácter de producto base transversal en más del 64% de los cuentahabientes.
* `PRESTAMO` y `SEGURO` exhiben una similitud coseno de **$0.714$**, lo que confirma que el subconjunto de usuarios que amortizan créditos comparte un solapamiento significativo con la cartera de pólizas.
* **Diferencia conceptual frente a Pearson:** Mientras Pearson aísla la tendencia lineal eliminando las medias, el Coseno preserva la magnitud relativa de los consumos, resultando ideal para identificar qué productos son los pilares volumétricos de la institución.

---

#### 2.7.3 Sistema de Recomendación Basado en Contenido: Item-to-Item de Amazon con ITF

El algoritmo de Filtrado Ítem-a-Ítem popularizado por Amazon (Linden et al., 2003) construye la matriz de co-adquisición binaria ($1 = 	ext{adquirido}$, $0 = 	ext{no adquirido}$). Para evitar el sesgo hacia productos omnipresentes, se incorporó la métrica de **Frecuencia Inversa de Ítems (ITF)**.

![Figura 5. Item-to-Item de Amazon y Ponderación ITF](img/fig_05_item_to_item_itf_pesos.png)
*Figura 5. (A) Matriz de Similitud Coseno Binario estilo Amazon y (B) Comparativa de Popularidad de Productos frente al Factor de Ponderación por Frecuencia Inversa (ITF).*

##### Análisis Descriptivo y de Negocio (Figura 5):
La Figura 5 demuestra la solución al problema de las **recomendaciones triviales**:
* **Panel A (Matriz Amazon 2003):** Evalúa la probabilidad condicional de compra conjunta. Se observa que la similitud binaria entre `SERVICIOS_HOGAR` y `TRANSF_EXTERNA` es de $0.54$, reflejando que más de la mitad de los usuarios que emiten transferencias también gestionan débitos automáticos.
* **Panel B (El dilema de la popularidad vs. especificidad):** 
  * `SERVICIOS_HOGAR` cuenta con **3,439 clientes**, lo que ocasiona que su peso de especificidad ITF caiga a un mínimo de **$0.45$**. Si un sistema no aplicara ITF, le recomendaría servicios básicos al 100% de los clientes, aportando nulo valor de negocio.
  * En contraste, productos estratégicos de alta rentabilidad pero menor volumen, como `LEASING` (**341 clientes**, $	ext{ITF} = 2.76$) y `SEGURO` (**533 clientes**, $	ext{ITF} = 2.31$), reciben una ponderación de especificidad hasta 6 veces mayor.
* **Impacto en el recomendador:** Al multiplicar la afinidad de co-adquisición por el factor ITF, el sistema prioriza la oferta de productos especializados de alto margen financiero, reservando los productos genéricos únicamente para clientes que realmente carecen de ellos.

---

#### 2.7.4 Cuadro Comparativo e Inferencia Híbrida

Para verificar el comportamiento práctico de la arquitectura, se ejecutó una inferencia cruzada simultánea sobre clientes muestra representativos de la cartera.

![Figura 6. Cuadro Comparativo de Inferencia Real](img/fig_06_cuadro_comparativo_recomendaciones.png)
*Figura 6. Cuadro comparativo de inferencia real: sugerencias generadas para clientes muestra bajo los enfoques Demográfico, Slope One, Pearson, Coseno y Contenido (Amazon + ITF).*

##### Análisis Descriptivo de la Inferencia Cruzada (Figura 6):
El cuadro de la Figura 6 permite auditar la coherencia de cada paradigma:
* **Cliente #2 (Maduro, productos actuales: PRESTAMO y TRANSF_EXTERNA):**
  * *Demográfico:* Sugiere `PRESTAMO, LEASING` por su perfil de ingresos.
  * *Slope One:* Recomienda `SEGURO` y `TARJETA`, buscando cerrar la brecha de consumo respecto a clientes con créditos similares.
  * *Contenido + ITF:* Recomienda `LEASING` y `SEGURO`, premiando la contratación de productos especializados afines a su alta capacidad de endeudamiento.
* **Cliente #19 (Joven, producto actual: SERVICIOS_HOGAR):**
  * El sistema de Coseno sugiere `TARJETA` y `TRANSF_EXTERNA` como la ruta natural de bancarización y transaccionalidad cotidiana.
  * El sistema ITF potencia la colocación de un `SEGURO` antes de ofrecerle un segundo débito genérico.

---

### Cuadro Comparativo Integral de las Técnicas Evaluadas

| Criterio de Evaluación | Sistema Demográfico (K-Means) | Slope One (Lemire et al.) | Correlación de Pearson | Similitud de Coseno | Item-to-Item con ITF (Amazon) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Paradigma Principal** | Demográfico (Estereotipos) | Colaborativo (User-Based) | Colaborativo (User-Based) | Colaborativo (Item-Based) | Basado en Contenido / Ítems |
| **Tipo de Datos de Entrada** | Atributos continuos/nominales | Calificaciones numéricas (1-5) | Calificaciones numéricas (1-5) | Vectores numéricos continuos | Matriz binaria (0/1) + frecuencias |
| **Complejidad de Inferencia** | $O(k)$ [Ultra rápida] | $O(\|R_u\| 	imes \|I\|)$ [Aritmética simple] | $O(\|U\|^2)$ o $O(\|I\|^2)$ [Media] | $O(\|I\|^2)$ [Media-Alta] | $O(1)$ [Lookup precalculado] |
| **Tolerancia a Cold Start** | **Excelente (Solución nativa)** | Nula para usuarios nuevos | Nula para usuarios nuevos | Baja para usuarios nuevos | Media para ítems poco frecuentes |
| **Sensibilidad a Sesgo Popular** | Alta (Tiende a la moda del clúster) | Media | Baja (Normaliza con la media) | Alta (Premia ítems masivos) | **Baja (Corregida con factor ITF)** |
| **Caso de Uso Óptimo en DW/BI** | Onboarding de clientes nuevos | Motor de predicción en batch | Análisis de afinidad de catálogo | Clustering de productos afines | Venta cruzada en banca móvil |

---

### 2.8 Habilidades blandas empleadas en la práctica

* [ ] Liderazgo
* [ ] Trabajo en equipo
* [ ] Comunicación asertiva
* [ ] La empatía
* [x] Pensamiento crítico
* [ ] Flexibilidad
* [ ] La resolución de conflictos
* [ ] Adaptabilidad
* [x] Responsabilidad

---

### 2.9 Conclusiones

* **Complementariedad de los paradigmas de recomendación:** La experimentación demostró que ningún paradigma individual resuelve satisfactoriamente todas las casuísticas del negocio bancario. Mientras el enfoque **Demográfico (K-Means)** es insustituible para resolver el arranque en frío de clientes nuevos sin transacciones, el enfoque **Colaborativo (Slope One y Coseno)** aporta la máxima precisión predictiva una vez consolidado el historial, y la ponderación **ITF** garantiza que las sugerencias finales no degeneren en ofertas triviales o redundantes.
* **Ventaja computacional de Slope One:** En escenarios de actualización transaccional frecuente, el algoritmo de Lemire et al. (Slope One) demostró una eficiencia operativa sobresaliente frente a la Correlación de Pearson y la Similitud de Coseno. Al basarse en diferencias medias acumulativas ($f(x) = x + b$), permite incorporar nuevas transacciones en tiempo incremental $O(1)$ sin requerir el recálculo trigonométrico exhaustivo de matrices multidimensionales.
* **Efectividad de la penalización por frecuencia inversa (ITF):** La incorporación de la métrica ITF dentro del esquema Item-to-Item de Amazon corrigió exitosamente la distorsión ocasionada por productos hipermasivos como `SERVICIOS_HOGAR` (presente en más del 64% de la cartera). Al penalizar logarítmicamente la ubicuidad de los productos genéricos, el recomendador redirigió el esfuerzo analítico hacia productos de alto valor estratégico para la entidad (como `LEASING` y `SEGURO`).

---

### 2.10 Recomendaciones

* **Implementación de una Arquitectura Híbrida en el Data Warehouse:** Se recomienda desplegar un motor de recomendación híbrido secuencial en el Data Mart de Clientes: utilizar el modelo Demográfico durante los primeros 30 días de vinculación del cuentahabiente y conmutar dinámicamente hacia el modelo Colaborativo (Slope One + ITF) una vez que el cliente supere un umbral mínimo de 5 transacciones registradas.
* **Desacoplamiento temporal bajo arquitectura Lambda:** Implementar el cálculo de matrices de similitud de Coseno y desviaciones Slope One en la capa **Offline (Batch)** durante procesos de mantenimiento nocturno, y almacenar las tablas de candidatos Top-$K$ en bases de datos en memoria (como Redis o vistas indexadas en SQL Server) para habilitar la entrega **Online** en la banca móvil con latencias inferiores a 50 milisegundos.
* **Monitoreo continuo de la deriva de catálogo (*Concept Drift*):** Establecer rutinas automáticas de auditoría sobre las matrices de correlación de Pearson cada trimestre, con el fin de detectar cambios en los patrones de consumo de los clientes originados por variaciones macroeconómicas en las tasas de interés o el lanzamiento de nuevos productos financieros.

---

### 2.11 Referencias bibliográficas

* [1] J. Montaner, B. López, and J. L. de la Rosa, "A taxonomy of recommender agents on the Internet," *Artificial Intelligence Review*, vol. 19, no. 4, pp. 285–330, Jun. 2003.
* [2] D. Lemire and A. Maclachlan, "Slope One predictors for online rating-based collaborative filtering," in *Proc. SIAM Int. Conf. Data Mining (SDM)*, Newport Beach, CA, USA, 2005, pp. 471–475.
* [3] G. Linden, B. Smith, and J. York, "Amazon.com recommendations: Item-to-item collaborative filtering," *IEEE Internet Computing*, vol. 7, no. 1, pp. 76–80, Jan. 2003.
* [4] X. Amatriain and J. Basilico, "Netflix recommendations: Beyond the 5 stars (Part 1 and 2)," *Netflix Technology Blog*, Apr. 2012. [Online]. Available: https://netflixtechblog.com/
* [5] R. Kimball and M. Ross, *The Data Warehouse Toolkit: The Definitive Guide to Dimensional Modeling*, 3rd ed. Indianapolis, IN, USA: Wiley, 2013.

---

### 2.12 Anexos

#### Anexo 1: Matriz de Conteo de Clientes Concurrentes entre Productos Financieros
Cantidad de clientes que han interactuado de forma simultánea con cada par de productos en el histórico de la entidad (soporte empírico de las desviaciones de Slope One y correlaciones):

| Producto | PRESTAMO | SEGURO | SERVICIOS_HOGAR | LEASING | TARJETA | TRANSF_EXTERNA |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **PRESTAMO** | 682 | 84 | 446 | 58 | 114 | 162 |
| **SEGURO** | 84 | 533 | 362 | 41 | 89 | 128 |
| **SERVICIOS_HOGAR** | 446 | 362 | 3,439 | 231 | 548 | 812 |
| **LEASING** | 58 | 41 | 231 | 341 | 62 | 91 |
| **TARJETA** | 114 | 89 | 548 | 62 | 807 | 204 |
| **TRANSF_EXTERNA** | 162 | 128 | 812 | 91 | 204 | 1,197 |

#### Anexo 2: Repositorio Oficial del Proyecto
Los scripts ejecutables de inferencia, generación de gráficos, transformaciones ETL y modelos de datos se encuentran versionados en el repositorio oficial de GitHub:
* [GitHub: Hlagua/DocumentosBi](https://github.com/Hlagua/DocumentosBi)
