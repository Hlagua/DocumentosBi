# UNIVERSIDAD TÉCNICA DE AMBATO
## FACULTAD DE INGENIERÍA EN SISTEMAS, ELECTRÓNICA E INDUSTRIAL
### CARRERA DE SOFTWARE — ASIGNATURA: INTELIGENCIA DE NEGOCIOS
### CICLO ACADÉMICO: AGOSTO 2026 – DICIEMBRE 2026

---

# GUÍA 11 — PRESENTACIÓN DEL DASHBOARD GERENCIAL `Financial_ijs`

**Autores:** Alison Marcela Cobos Taco / Henry Daniel Lagua Flores  
**Docente:** Ing. Ruben Nogales, Mg.  
**Duración sugerida:** 15 minutos de exposición + preguntas  
**Complementa a:** Guía 06 (uso e interpretación de cada gráfico) y Guía 07 (diseño y fundamentos)

> Todas las cifras de esta guía son las del tablero **sin filtros** (corte 31/12/1998) y están verificadas en el motor de Power BI Desktop. Si una cifra en pantalla no coincide, revise que los filtros globales estén en "Todas".

---

## 1. PREPARACIÓN (el día de la presentación, 20 minutos antes)

| # | Qué hacer | Cómo comprobarlo |
| :-: | :--- | :--- |
| 1 | `git pull` en la carpeta del repositorio | "Already up to date" o descarga los cambios |
| 2 | Arrancar SQL Server: `sqllocaldb start MSSQLLocalDB` | "Instancia 'MSSQLLocalDB' de LocalDB iniciada" |
| 3 | Comprobar que MongoDB está en ejecución (servicio *MongoDB* o MongoDB Compass conecta a `localhost:27017`) | Compass muestra la base `Financial` |
| 4 | `python REPARAR_TODO.py` | Termina en **LISTO** |
| 5 | Abrir `dashboards/Dashboard_Financial_Kimball/Dashboard_Financial_Kimball.pbip` → **Inicio → Actualizar** | En Inicio: mora **10.04%**, incumplimiento **13.25%**, cartera vigente **$80.30M**, saldo **$197.14M**, absorción **40.73%**, sobregiro **39** |
| 6 | Abrir `Dashboard_Financial_Mongo.pbip` en otra ventana → **Actualizar** | Las mismas seis cifras |
| 7 | En **P2**, abrir el árbol de descomposición: **+** → región → distrito → cliente | Se ve north Moravia → Karvina → clientes |
| 8 | Dejar los 8 filtros globales en **"Todas"** y volver a **Inicio** | — |
| 9 | Si Power BI pregunta por el formato **TMDL**: **No actualizar** | — |
| 10 | Tener abiertos, minimizados: SQL Server Management Studio (o Azure Data Studio) conectado a `(localdb)\MSSQLLocalDB`, y MongoDB Compass | Para la demostración de conexiones |

**Recomendación:** presentar desde el tablero **Kimball** y usar el de **MongoDB** solo en la demostración de conexiones y en la comparación final. Maximizar la ventana de Power BI y contraer los paneles *Filtros*, *Visualizaciones* y *Datos* (flecha **»** de cada panel) para que el lienzo ocupe toda la pantalla; en **Ver** elegir *Ajustar a la página*.

---

## 2. GUION (15 MINUTOS)

El reparto entre expositores es una sugerencia; pueden intercambiarlo. Las frases entre comillas son ideas para decir con sus palabras, no para leer.

### 2.1 Apertura — 1 minuto (Henry)

**Pantalla:** Inicio.

"Construimos un tablero para la gerencia del banco `Financial_ijs` que responde las seis preguntas de nuestra Carta de Diseño v8 y agrega tres páginas de recomendación. Los datos vienen de la base transaccional remota, pasan por un Data Mart Kimball en SQL Server y se replican en MongoDB. Los dos tableros son idénticos y dan las mismas cifras."

Señalar la **banda azul** (navegación), el **panel de filtros** a la izquierda y la **fila de KPIs**: "Arriba siempre está la pregunta que responde la página; en cada gráfico, el título es la respuesta."

### 2.2 Cómo se conecta — 2 minutos (Alison)

**Kimball:**
1. **Inicio → Transformar datos.** Mostrar los parámetros `ServidorSQL = (localdb)\MSSQLLocalDB` y `BaseDatosSQL = DM_Financial_Kimball_v2`.
2. Seleccionar `Fact_Prestamos` → **Editor avanzado**: `Sql.Database(ServidorSQL, BaseDatosSQL)`. "Conector nativo de SQL Server, en modo importación."
3. Cerrar y abrir la **vista de Modelo**: "Esquema en estrella: los hechos (préstamos, saldos mensuales, órdenes, transacciones) al centro y las dimensiones alrededor."

**MongoDB** (cambiar a la ventana del tablero Mongo):
1. **Transformar datos → `MongoFinancial` → Editor avanzado:** `Python.Execute(...)` con `pymongo.MongoClient("mongodb://localhost:27017/")` y `client["Financial"]`.
2. "Power BI Desktop no tiene un conector directo para un MongoDB local; lo leemos con el driver oficial `pymongo`. Cada DataFrame del script llega como una tabla (`m_prestamos`, `m_saldo_mensual`…). Este tablero no toca SQL Server."
3. Opcional: mostrar la base `Financial` en MongoDB Compass.

**Frase de cierre:** "MongoDB se llenó migrando el Data Mart (script 35); por eso los dos tableros deben coincidir, y coinciden."

### 2.3 Inicio — 1 minuto (Henry)

**Pantalla:** Inicio. Leer los tres problemas del panel derecho:
1. **Impago y mora:** 45 préstamos vigentes en mora (10.04%) y 31 cerrados con deuda (13.25%).
2. **Capacidad de pago:** la cuota comparada con el saldo del cliente separa el impago de 2.9% a 23.3%.
3. **Medición de saldos:** $197.14M al corte; la cartera vigente absorbe el 40.73%.

"Cada tarjeta es una pregunta; con un clic vamos a su página." Clic en la tarjeta **P1**.

### 2.4 Preguntas P1 a P6 — 6 minutos

| Página | Quién | Qué mostrar (clic) | Qué decir |
| :-: | :-: | :--- | :--- |
| **P1** | Henry | Gráfico de columnas y línea; pasar el mouse por 1997 | "La colocación se duplica (101 préstamos en 1994, 196 en 1997) y la tasa de mora de cada cosecha no sube: se queda entre 12.2% y 15.4% (χ², p = 0.93). **Hay más morosos porque prestamos más, no porque prestemos peor.** 1998 aparece bajo (2.5%) porque sus préstamos son recientes." |
| **P2** | Alison | Árbol ya expandido; columnas por región; treemap | "north Moravia tiene la mayor mora (15.8%, 12 de 76), por encima del banco (10.04%, línea gris). El árbol baja a Karvina y a sus clientes. En el treemap, más oscuro = más mora; tamaño = cartera. La tabla muestra cada tasa con su *n* y su intervalo de Wilson: 70 de 77 distritos tienen menos de 10 préstamos vigentes, así que no sacamos conclusiones de una tasa sola." |
| **D1** | Alison | Clic derecho en **Karvina** (tabla o treemap) → *Obtener detalles* | "La ficha del distrito se abre con todos los filtros: 24 préstamos, 15 vigentes, 3 en mora (20%)." |
| **D2** | Alison | En la tabla de D1, clic derecho en **Cliente 2823** → *Obtener detalles* | "Ficha Cliente 360: préstamo en mora de $541,200 con cuota de $9,020; paga $14,286 al mes en órdenes; su índice de saturación es 2.14 (paga más de lo que suele tener) y su saldo terminó en −$2,803. Abajo: lo que el recomendador le ofrecería." Luego **◀ Atrás**. |
| **P3** | Henry | Columnas por región con la línea del banco; cascada | "El 40.73% del saldo respalda préstamos activos. east Bohemia está más expuesta (51.6%); north Bohemia tiene holgura (28.2%). La cascada lo explica: $197.14M − $80.30M = $116.84M libres. Mostramos el saldo **por cuenta**, porque el total crece sobre todo porque se abren cuentas." |
| **P4** | Henry | Ticket por categoría; línea de sobregiro | "$6,257.86M en 1,056,320 movimientos. Los depósitos y retiros en efectivo son los movimientos grandes. Las cuentas en sobregiro crecen hasta 43 en noviembre de 1998: señal temprana de problemas de liquidez." |
| **P5** | Alison | Dispersión (punto bermellón); tabla de alerta | "Cada punto es un titular: saldo contra órdenes fijas. Naranja: compromete más de la mitad de su saldo; bermellón: más de lo que tiene. Son **47 cuentas** en alerta; la 2335 (el mismo cliente 2823) es la única sobre 1. La tabla es la lista para cobranza temprana." |
| **P6** | Alison | Columnas por banda; columnas por edad | "**El hallazgo más fuerte:** con la regla cuota / saldo previo el impago va de 2.9% (banda Baja) a 23.3% (banda Alta), χ² = 38.58. En cambio la edad no separa el impago (p = 0.32). **Se presta según la capacidad, no según el perfil.** La tabla de abajo es la lista de denegación: 31 clientes con deuda." |

### 2.5 Recomendaciones R1 a R3 — 3 minutos (Henry)

| Página | Qué mostrar | Qué decir |
| :-: | :--- | :--- |
| **R1** | Barras de modelos (azul = elegidos); gráfico gris/naranja; matriz por perfil | "Evaluamos 8 recomendadores con el mismo protocolo (ocultar un producto que el cliente sí tiene). El **demográfico** acierta el 66.0% en su primera sugerencia, frente a 58.5% de ofrecer lo más popular, y lo confirmamos con otra semilla. En gris, quién ya usa cada producto; en naranja, a quién se lo recomendamos: la mayor oportunidad son las transferencias a otros bancos." |
| **R2** | KPIs; columnas de AUC; tabla | "Para el préstamo usamos la regla de capacidad: anticipa el impago mejor que la regla anterior (AUC 0.717 contra 0.659). Hay 3,818 titulares sin préstamo; a 1,721 les ofrecemos uno **con monto máximo**, porque la cuota prudente mediana ($1,873) es menos de la mitad de la cuota típica del banco ($3,934): solo 71 podrían pagar un préstamo normal." |
| **R3** | Matriz de venta cruzada; barras del kNN | "La matriz se lee por filas: de quienes pagan seguro, el 99.8% también hace transferencias. El kNN por perfil es el mejor para productos poco comunes (37.2% de acierto contra 6.3% de la popularidad) y añade 2,731 ofertas que el demográfico no hace." |

### 2.6 Filtros que viajan entre páginas — 1 minuto (Alison)

1. En el panel izquierdo: **Banda de capacidad = Alta**.
2. Ir a **P6**: "172 préstamos, 23.3% de impago."
3. Ir a **P5**: "De las 47 cuentas saturadas, 23 son de esta banda."
4. Cambiar a **Edad = Adulto Mayor** (y Banda en "Todas") e ir a **R1**: "La primera oferta más frecuente pasa a ser domiciliar la pensión (766)."
5. Volver todos los filtros a **"Todas"**.

"Los filtros del panel son atributos del cliente, así que filtran todo el proyecto: préstamos, saldos, órdenes y recomendaciones. El clic dentro de un gráfico filtra su página; para llevar un clic a otra página usamos el clic derecho → *Obtener detalles*."

### 2.7 Cierre — 1 minuto (Henry)

Poner los dos tableros lado a lado en **Inicio**:

"Los dos tableros, uno sobre SQL Server y otro sobre MongoDB, tienen las mismas 128 medidas y dan las mismas cifras. En resumen: la mora crece por volumen y no por deterioro; el impago lo anticipa la capacidad de pago; y el tablero no solo diagnostica, también dice a quién prestar, cuánto y qué ofrecer."

---

## 3. PREGUNTAS PROBABLES DEL INGENIERO

| Pregunta | Respuesta corta | Dónde mostrarlo |
| :--- | :--- | :--- |
| ¿Por qué Kimball y no Inmon? | Las preguntas son analíticas y de un solo proceso de negocio (crédito y cuentas); el esquema en estrella es más simple de consultar y rinde mejor en Power BI. El análisis completo está en el Informe 02. | Vista de Modelo |
| ¿Cuál es el grano de los hechos? | Préstamo; transacción; orden; y **cuenta × mes** para los saldos (foto mensual). | Guía 07, sección 6 |
| ¿Por qué el saldo no se suma? | Es semiaditivo: sumar saldos de varios meses no tiene sentido. La medida toma el **último mes** del periodo filtrado. | P3, gráfico de saldo |
| ¿Cómo se conecta Mongo? | Script de Python con `pymongo` dentro de Power Query; no pasa por SQL Server. | Transformar datos → `MongoFinancial` |
| ¿Cómo sabe que Mongo tiene lo mismo? | Reconciliación de 33 controles en el Informe 05, y las 128 medidas dan igual en los dos tableros. | Los dos tableros lado a lado |
| ¿Qué son las barras / el intervalo de Wilson? | Intervalo de confianza de una tasa con *z* = 1 (±1 error estándar). Con pocos casos, el intervalo es ancho; con tasa 0, no colapsa a cero como el de Wald. | Tooltip de P1, P2 o P6 |
| ¿Por qué columnas y no barras? | Regla del docente: eje X categórico, eje Y numérico; las barras horizontales solo donde las etiquetas son largas (modelos, productos). | Guía 07, sección 2 |
| ¿Por qué el anillo en P5? | Una sola variable con 5 clases o menos, como pide la regla. | P5 |
| ¿Por qué no hay mapa? | Los 77 distritos checos se geolocalizan mal sin archivo de formas; el treemap y las columnas responden lo mismo. | Guía 07, sección 3 |
| ¿Qué pasa con los datos faltantes? | El distrito 69 tenía indicadores faltantes y se imputaron (Informe 10); la ficha D1 lo marca como "Imputado". | D1 de ese distrito |
| ¿Por qué el recomendador demográfico? | Mayor acierto con el mismo protocolo (66.0%, MRR 0.776), confirmado con otra semilla. Slope One se descartó porque para estimar montos la media del producto lo supera. | R1, barras de modelos |
| ¿Qué producto genera más ganancia? | La base no trae tasas, comisiones ni márgenes, así que no se puede calcular; el tablero mide uso y volumen, no ganancia. | — |
| ¿Se puede filtrar por un rango de edad cualquiera? | El panel trae los 3 grupos del Data Mart; un rango distinto se puede agregar arrastrando `edad_corte` al panel *Filtros*. | Panel Filtros de Power BI |
| ¿El clic en un gráfico filtra otras páginas? | No; en Power BI el filtro de un clic vive en su página. Para todo el proyecto usamos 8 filtros sincronizados y el clic derecho → *Obtener detalles*. | Sección 2.6 |

---

## 4. PLAN B (SI ALGO FALLA EN VIVO)

| Problema | Solución rápida |
| :--- | :--- |
| "No se puede conectar a SQL Server" | Terminal: `sqllocaldb start MSSQLLocalDB` y volver a **Actualizar** |
| El tablero Mongo falla al actualizar | Comprobar que MongoDB está iniciado; si el error menciona Python, revisar *Archivo → Opciones → Scripts de Python*. Si no se resuelve, continuar con el tablero Kimball y mostrar la conexión Mongo desde *Transformar datos* (el código se ve igual) |
| Aparece una página con cifras distintas a esta guía | Algún filtro global quedó elegido: poner los 8 en "Todas" |
| El árbol de P2 aparece cerrado | Clic en **+** → región → distrito → cliente |
| No aparece *Obtener detalles* al hacer clic derecho | Hacer clic derecho sobre el **nombre** del cliente o distrito (no sobre un número). Si aun así no aparece, navegar con los botones y mostrar D1/D2 explicando que se abren desde el clic derecho |
| Power BI pregunta por TMDL | **No actualizar** |
| Nada funciona | Mostrar las capturas y la Guía 06; las cifras de control de esta guía están verificadas en el motor |

---

## 5. CIFRAS PARA TENER A MANO

| Tema | Cifra |
| :--- | :--- |
| Préstamos · en mora (D) · cerrados con deuda (B) | 682 · 45 · 31 |
| Tasa de mora vigente · incumplimiento · impago total | 10.04% · 13.25% · 11.14% |
| Cartera total · vigente · saldo por cobrar estimado | $103.26M · $80.30M · $46.62M |
| Saldo neto al corte · absorción vigente (referencia total) · liquidez libre | $197.14M · 40.73% (52.38%) · $116.84M |
| Transacciones · volumen | 1,056,320 · $6,257.86M |
| Cuentas en sobregiro al corte · máximo mensual · alguna vez | 39 · 43 (nov-1998) · 193 |
| Cuentas saturadas (> 0.5) · sobre su saldo (> 1) · con crédito externo | 47 · 1 (cuenta 2335) · 35 |
| Impago por banda (Baja → Alta) · χ² · AUC | 2.9% → 23.3% · 38.58 · 0.717 |
| Edad e incumplimiento | χ² = 2.28, p = 0.32 (no significativo) |
| Recomendador demográfico · popularidad · kNN en cola larga | 66.0% · 58.5% · 37.2% |
| Titulares sin préstamo · préstamo prudente recomendado · pueden pagar la cuota típica | 3,818 · 1,721 · 71 |
| Cliente 2823 (cuenta 2335, Karvina) | Préstamo D $541,200 · cuota $9,020 · órdenes $14,286/mes · índice 2.14 · saldo −$2,803 |
