"""
Genera el informe en Word de la Tarea 2 del 2do Parcial:
  - 2parcial/Tarea2_Regresion_Logistica/Informe_Tarea2_Regresion_Logistica.docx
  - Copia también en: 2parcial/Informe_Tarea2_Regresion_Logistica.docx

Sigue exactamente la plantilla y el formato de Informe_Final_Perceptron.docx
(Times New Roman 12, interlineado 1.5, ecuaciones OMML numeradas, tablas con bordes
y leyendas automáticas, pie de página "Página X de Y").
"""

import copy
import shutil
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
import scipy
import sklearn
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Cm, Pt

sys.path.insert(0, str(Path(__file__).resolve().parent))
from informe_docx import (  # noqa: E402
    FUENTE,
    Informe,
    acento,
    agregar_texto,
    casos,
    delim,
    formato,
    frac,
    func,
    fuente_run,
    pie_pagina_numerado,
    poner_carrera,
    r,
    raiz,
    sub,
    subsup,
    sup,
    suma,
    tx,
)

RAIZ = Path(__file__).resolve().parents[1]
DIR_2P = RAIZ / "2parcial"
TAREA2 = DIR_2P / "Tarea2_Regresion_Logistica"
RES = TAREA2 / "resultados"
CAP = TAREA2 / "capturas"
PLANTILLA = RAIZ / "scripts" / "plantillas" / "Taller_Perceptron_plantilla.docx"
SALIDA = TAREA2 / "Informe_Tarea2_Regresion_Logistica.docx"
SALIDA_COPIA = DIR_2P / "Informe_Tarea2_Regresion_Logistica.docx"

tabla_res = pd.read_csv(RES / "tabla_resultados_tarea2.csv", encoding="utf-8-sig")
pesos_todos = pd.read_csv(RES / "vectores_pesos_beta_todos.csv", encoding="utf-8-sig")
capturas = sorted(CAP.glob("vscode_ejecucion_*.png"))

versiones = {
    "Python": sys.version.split()[0],
    "NumPy": np.__version__,
    "pandas": pd.__version__,
    "SciPy": scipy.__version__,
    "scikit-learn": sklearn.__version__,
    "Matplotlib": matplotlib.__version__,
}


def pct(v, d=2):
    return f"{100.0 * float(v):.{d}f} %"


def num(v, d=4):
    return f"{float(v):.{d}f}".replace("-", "−")


def miles(n):
    return f"{int(n):,}".replace(",", " ")


# ----------------------------------------------------------------------------
# Plantilla: portada, encabezado y pie
# ----------------------------------------------------------------------------
doc = Document(PLANTILLA)


def buscar(inicio):
    for p in doc.paragraphs:
        if p.text.strip().startswith(inicio):
            return p
    raise ValueError(f"No se encontró: {inicio}")


def eliminar(p):
    p._p.getparent().remove(p._p)


poner_carrera(doc)
pie_pagina_numerado(doc)

portada = [
    (
        "Tema:",
        "Entrenamiento de Regresión Logística Binaria mediante Entropía Cruzada y Gradiente "
        "Descendente en los 4 Data Marts de Financial_ijs",
    ),
    ("Unidad de Organización Curricular:", "Profesional"),
    ("Nivel y Paralelo:", 'Sexto semestre - Paralelo: "A"'),
    ("Alumnos participantes:", "Cobos Taco Alison Marcela"),
    ("", "Lagua Flores Henry Daniel"),
    ("", ""),
    ("Asignatura:", "Inteligencia de Negocios"),
    ("Docente:", "Ing. Rubén Nogales Portero, Ph.D."),
]
lineas = [
    buscar("Tema:"),
    buscar("Unidad de Organización"),
    buscar("Nivel y Paralelo:"),
    buscar("Alumnos participantes:"),
]
lineas += [q for q in doc.paragraphs if q.text.strip().startswith("_____")]
lineas += [buscar("Asignatura:"), buscar("Docente:")]
for q, (etiqueta, valor) in zip(lineas, portada):
    for run in list(q.runs):
        run._element.getparent().remove(run._element)
    if not valor:
        eliminar(q)
        continue
    agregar_texto(q, f"{etiqueta}\t{valor}")
    formato(
        q,
        WD_ALIGN_PARAGRAPH.LEFT,
        sangria=Cm(6.6),
        interlineado=1.15,
        despues=2,
        primera=Cm(-6.6),
    )
    q.paragraph_format.tab_stops.add_tab_stop(Cm(6.6))

ppr_seccion = copy.deepcopy(buscar("2.1 Objetivos")._p.pPr)
ancla = [q for q in doc.paragraphs if q.text.strip() == "INFORME DE GUÍA PRÁCTICA"][-1]
cuerpo = doc.element.body
siguiente = ancla._p.getnext()
while siguiente is not None and siguiente.tag != qn("w:sectPr"):
    borrar, siguiente = siguiente, siguiente.getnext()
    cuerpo.remove(borrar)

inf = Informe(doc, ancla._p)


def seccion(texto):
    p = inf._nuevo()
    p._p.insert(0, copy.deepcopy(ppr_seccion))
    agregar_texto(p, texto, negrita=True)
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.keep_with_next = True
    return p


def actividad(texto):
    return inf.titulo(texto, sangria=0, antes=12)


def casillas(items):
    for marcado, texto in items:
        p = inf._nuevo()
        agregar_texto(p, ("☒ " if marcado else "☐ ") + texto)
        formato(p, WD_ALIGN_PARAGRAPH.LEFT, sangria=Cm(1.27), interlineado=1.15, despues=0)


# ----------------------------------------------------------------------------
# 2.1 a 2.5
# ----------------------------------------------------------------------------
seccion("2.1 Objetivos")
inf.titulo("General:", antes=2)
inf.texto(
    "Implementar y entrenar desde cero un clasificador de Regresión Logística Binaria sobre "
    "todas las características de los cuatro Data Marts del modelo dimensional "
    "DM_Financial_Kimball_v2, utilizando exclusivamente la función de pérdida de Entropía "
    "Cruzada y su optimización mediante Gradiente Descendente, entregando para cada Data Mart "
    "el vector de pesos final β, la exactitud de entrenamiento (Acc. Train), la exactitud de "
    "prueba (Acc. Test) y las figuras de convergencia y frontera de decisión."
)
inf.titulo("Específicos:", antes=4)
inf.lista([
    "Formular matemáticamente el modelo de Regresión Logística Binaria (combinación lineal "
    "z = x̃^T^β, función de activación sigmoide σ(z), función de costo de Entropía Cruzada "
    "J(β) y vector gradiente ∇J(β)).",
    "Aplicar en los cuatro Data Marts el flujo de preprocesamiento libre de fuga de datos: "
    "partición estratificada 80 % entrenamiento y 20 % prueba primero, balanceo de clases "
    "(sobremuestreo solo en entrenamiento para Préstamos y submuestreo 50/50 para los demás) "
    "y escalado z-score ajustado exclusivamente con la media y desviación del entrenamiento.",
    "Programar en Python el algoritmo de Gradiente Descendente sobre la Entropía Cruzada (sin "
    "utilizar la clase LogisticRegression de scikit-learn) y verificar la convergencia del "
    "vector de pesos β frente al optimizador numérico de SciPy sobre la misma función J(β).",
    "Reportar e interpretar para los cuatro Data Marts el vector de pesos final β = [β~0~, "
    "β~1~, ..., β~n~]^T^, Acc. Train, Acc. Test, matrices de confusión, intervalos de confianza "
    "y fronteras de decisión 2D de apoyo proyectadas con PCA.",
])

seccion("2.2 Modalidad")
inf.texto("Práctica de laboratorio. Trabajo en parejas.")

seccion("2.3 Tiempo de duración")
inf.texto("Presenciales: 120 minutos.", despues=0)
inf.texto("No presenciales: 60 minutos para análisis de pesos e integración del informe.")

seccion("2.4 Instrucciones")
inf.texto("Instrucciones de la práctica (Tema 2 - Pizarra 2):")
inf.lista([
    "Entrenar un modelo de Regresión Logística Binaria empleando todas las características "
    "numéricas X de cada Data Mart reducido a dos clases (y~i~ en {0, 1}).",
    "No utilizar la clase LogisticRegression de scikit-learn ni funciones caja negra que "
    "entrenen el clasificador completo de forma automática.",
    "Se permite utilizar únicamente las formulaciones y funciones para evaluar la Entropía "
    "Cruzada y la optimización por Gradiente Descendente.",
    "Dividir cada dataset en conjunto de entrenamiento (80 %) y conjunto de prueba (20 %), "
    "respetando el balanceo de clases y el escalado sin fuga de información.",
    "Entregar para cada Data Mart: el vector de pesos final β = [β~0~, β~1~, ..., β~n~]^T^, "
    "la exactitud de entrenamiento (Acc. Train), la exactitud de prueba (Acc. Test) y las "
    "figuras de soporte (convergencia, matrices de confusión, sigmoide y frontera 2D).",
], numerada=True)

seccion("2.5 Listado de equipos, materiales y recursos")
inf.texto("Listado de equipos y materiales generales empleados en la guía práctica:")
inf.lista([
    "Computador con Python 3 (Windows 11 Pro).",
    "Visual Studio Code (editor y terminal integrada PowerShell).",
    "Bibliotecas NumPy, pandas, SciPy (expit y optimize.minimize), scikit-learn (solo PCA "
    "para la gráfica 2D de apoyo) y Matplotlib.",
    "Cuatro datasets etiquetados libres de fuga en 2parcial/: 01_dm_prestamos.csv, "
    "02_dm_saldo_mensual.csv, 03_dm_ordenes.csv y 04_dm_transacciones.csv.",
    "Apuntes de clase (Pizarra 2: Regresión Logística, Entropía Cruzada y entregables).",
])
inf.texto("TAC (Tecnologías para el Aprendizaje y Conocimiento) empleados en la guía práctica:")
casillas([
    (False, "Plataformas educativas"),
    (False, "Simuladores y laboratorios virtuales"),
    (True, "Aplicaciones educativas"),
    (True, "Recursos audiovisuales"),
    (False, "Gamificación"),
    (True, "Inteligencia Artificial"),
])
inf.texto("Otros (Especifique): Python 3, NumPy, SciPy y Visual Studio Code.")
inf.titulo("Software utilizado en la práctica:")
inf.texto(
    "El código regresion_logistica.py se desarrolló y ejecutó en Visual Studio Code. "
    "La Tabla {tab:software2} resume las versiones utilizadas."
)
inf.tabla(
    "Software y bibliotecas utilizados en la Tarea 2",
    ["Software / Biblioteca", "Versión", "Uso en la práctica"],
    [
        ["Windows 11 Pro", "10.0.26300", "Sistema operativo del equipo de trabajo."],
        ["Visual Studio Code", "1.142.0", "Edición y ejecución en terminal PowerShell."],
        ["Python", versiones["Python"], "Lenguaje de programación del experimento."],
        ["NumPy", versiones["NumPy"], "Cálculo matricial del gradiente y actualización de pesos β."],
        ["SciPy", versiones["SciPy"], "Función sigmoide estable (expit) y verificación BFGS de J(β)."],
        ["pandas", versiones["pandas"], "Lectura de CSV y exportación de tablas de pesos y métricas."],
        ["scikit-learn", versiones["scikit-learn"], "Únicamente PCA 2D para graficar la frontera de apoyo."],
        ["Matplotlib", versiones["Matplotlib"], "Gráficos de convergencia, sigmoide, confusión y fronteras."],
        ["Microsoft Word", "16.0", "Redacción y maquetación del informe."],
    ],
    clave="software2",
    anchos=[3.8, 2.4, 8.8],
    alinear=[WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.CENTER, WD_ALIGN_PARAGRAPH.LEFT],
)
inf.titulo("Reproducibilidad de los resultados:")
inf.texto(
    "Para obtener exactamente los mismos vectores de pesos β, tablas y figuras basta con "
    "ejecutar python 2parcial/Tarea2_Regresion_Logistica/regresion_logistica.py desde la raíz "
    "del proyecto. La semilla aleatoria fija (42) garantiza resultados idénticos en cada corrida."
)

# ----------------------------------------------------------------------------
# 2.6 Actividades por desarrollar
# ----------------------------------------------------------------------------
seccion("2.6 Actividades por desarrollar")

# Actividad 1
actividad("Actividad 1. Estructura de la Regresión Logística y Entropía Cruzada (20 min)")
inf.titulo("Objetivo de la actividad", antes=2)
inf.texto(
    "Identificar la estructura matemática de una neurona logística (entradas, sesgo, pesos β, "
    "función sigmoide) y deducir la función de costo de Entropía Cruzada Binaria junto con su "
    "gradiente respecto al vector de pesos."
)
inf.titulo("Combinación lineal y activación logística (sigmoide)")
inf.texto(
    "A diferencia del perceptrón de Rosenblatt, cuya salida es un escalón discontinuo ±1, la "
    "Regresión Logística modela la probabilidad condicional P(y = 1 | x) de pertenecer a la "
    "clase positiva [2], [3]. Para una observación con n características x~i~ = (x~i1~, ..., "
    "x~in~)^T^ y entrada de sesgo constante x~i0~ = 1, se define el vector aumentado "
    "x̃~i~ = (1, x~i1~, ..., x~in~)^T^ y el vector de parámetros β = (β~0~, β~1~, ..., β~n~)^T^. "
    "El sumador lineal calcula el logit z~i~ (Ecuación ({eq:logit})):"
)
inf.ecuacion(
    sub(r("z"), r("i")) + r("=") + sub(r("β"), r("0")) + r("+") +
    suma(r("j=1"), r("n"), sub(r("β"), r("j")) + sub(r("x"), r("ij"))) + r("=") +
    sup(sub(acento(r("x"), "̃"), r("i")), r("T")) + r("β"),
    clave="logit",
)
inf.texto(
    "El logit z~i~ atraviesa la función logística o sigmoide σ(z), que transforma cualquier "
    "número real en una probabilidad acotada en el intervalo abierto (0, 1) (Ecuación ({eq:sigmoide})):"
)
inf.ecuacion(
    sub(acento(r("y"), "̂"), r("i")) + r("=P") + delim(sub(r("y"), r("i")) + r("=1∣") + sub(r("x"), r("i"))) +
    r("=σ") + delim(sub(r("z"), r("i"))) + r("=") +
    frac(r("1"), r("1+") + sup(r("e"), r("−") + sub(r("z"), r("i")))),
    clave="sigmoide",
)
inf.texto(
    "La decisión binaria se toma con el umbral natural de probabilidad 0.5, que equivale "
    "exactamente al hiperplano z~i~ = x̃~i~^T^β = 0 (Ecuación ({eq:regla})):"
)
inf.ecuacion(
    sub(acento(r("c"), "̂"), r("i")) + r("=") +
    casos(
        r("1,   ") + tx("si ") + r("σ") + delim(sub(r("z"), r("i"))) + r("≥0.5   ") + delim(sub(r("z"), r("i")) + r("≥0")),
        r("0,   ") + tx("si ") + r("σ") + delim(sub(r("z"), r("i"))) + r("<0.5   ") + delim(sub(r("z"), r("i")) + r("<0")),
    ),
    clave="regla",
)
inf.imagen(
    RES / "estructura_regresion_logistica.png",
    14.8,
    "Estructura del modelo de Regresión Logística: entradas, pesos β, sumador lineal y activación sigmoide.",
    clave="estructura_log",
    fuente="Elaboración propia a partir de los apuntes de clase (Pizarra 2).",
)

inf.titulo("Función de pérdida: Entropía Cruzada Binaria")
inf.texto(
    "Dado que las etiquetas reales son bernoullianas y~i~ en {0, 1}, la verosimilitud de N "
    "observaciones independientes es Π~i=1~^N^ ŷ~i~^y_i^ (1 − ŷ~i~)^(1−y_i)^. Tomando el "
    "negativo del logaritmo natural promedio se obtiene la función de pérdida de **Entropía "
    "Cruzada Binaria** J(β) anotada en la pizarra (Ecuación ({eq:ce})):"
)
inf.ecuacion(
    r("J") + delim(r("β")) + r("=−") + frac(r("1"), r("N")) +
    suma(
        r("i=1"),
        r("N"),
        delim(
            sub(r("y"), r("i")) + func("ln", sub(acento(r("y"), "̂"), r("i"))) + r("+") +
            delim(r("1−") + sub(r("y"), r("i"))) + func("ln", r("1−") + sub(acento(r("y"), "̂"), r("i"))),
            "[",
            "]",
        ),
    ),
    clave="ce",
)
inf.texto(
    "La función J(β) es estrictamente convexa respecto a β, por lo que no posee mínimos "
    "locales falsos: todo mínimo local es el mínimo global único [3]."
)

# Actividad 2
actividad("Actividad 2. Preparación de los 4 Data Marts: partición 80/20, balanceo y escalado (20 min)")
inf.titulo("Objetivo de la actividad", antes=2)
inf.texto(
    "Preparar los cuatro datasets de los Data Marts para la clasificación binaria con una "
    "partición 80 % entrenamiento y 20 % prueba, asegurando el balance de clases y el escalado "
    "sin filtración de información entre prueba y entrenamiento."
)
inf.titulo("Partición 80/20 y estrategia de balanceo por Data Mart")
inf.texto(
    "Siguiendo la pizarra de clase, donde se evalúan directamente la exactitud de entrenamiento "
    "(Acc. Train) y la exactitud de prueba (Acc. Test), y dado que la función convexa J(β) "
    "converge de manera monótona sin requerir selección heurística de época por bolsillo, se "
    "adoptó la partición estratificada **80 % entrenamiento / 20 % prueba** utilizada en el "
    "taller del Perceptrón. El balanceo de clases se ejecutó respetando el tamaño muestral de "
    "cada Data Mart (Tabla {tab:particion2}):"
)
inf.lista([
    "**Fact_Prestamos (N = 682; 76 en mora vs. 606 sanos):** si se realizara submuestreo antes "
    "de partir (76 vs. 76 = 152), el 20 % de prueba quedaría con solo 30 préstamos, dando una "
    "cota de Hoeffding demasiado ancha. Por ello, primero se partió 80/20 de forma estratificada "
    "(reservando 136 préstamos reales intactos para prueba) y se aplicó **sobremuestreo "
    "(oversampling) exclusivamente en el entrenamiento** (485 sanos y 485 en mora = 970 filas "
    "de entrenamiento).",
    "**Fact_Saldo_Cuenta_Mensual (708 con sobregiro en t+1 vs. 708 sin sobregiro = 1 416):** "
    "como sobran meses sin sobregiro (180 407), se aplicó **submuestreo** 50/50 y partición "
    "estratificada 80/20, obteniendo 1 132 observaciones de entrenamiento (566 por clase) y "
    "284 de prueba (142 por clase).",
    "**Fact_Ordenes (1 590 obligaciones financieras vs. 1 590 pagos SIPO = 3 180):** mediante "
    "**submuestreo** 50/50 y partición 80/20 se obtuvieron 2 544 filas de entrenamiento "
    "(1 272 por clase) y 636 de prueba (318 por clase).",
    "**Fact_Transacciones (10 000 egresos vs. 10 000 ingresos = 20 000):** mediante "
    "**submuestreo** 50/50 y partición 80/20 se obtuvieron 16 000 filas de entrenamiento "
    "(8 000 por clase) y 4 000 de prueba (2 000 por clase).",
])

filas_part = []
for row in tabla_res.itertuples():
    est_txt = (
        "Sobremuestreo en Train (485 vs. 485)"
        if row.Estrategia_Balanceo == "sobremuestreo_train"
        else "Submuestreo 50/50 (Train y Test)"
    )
    filas_part.append([
        row.Data_Mart,
        row.Tabla_Hechos,
        str(row.n_Caracteristicas),
        miles(row.N_Train),
        miles(row.N_Test),
        est_txt,
    ])
inf.tabla(
    "Partición 80/20 y balanceo de clases aplicado en los 4 Data Marts",
    ["Data Mart", "Tabla de Hechos", "Variables X (n)", "N Train (80 %)", "N Test (20 %)", "Estrategia de Balanceo"],
    filas_part,
    clave="particion2",
    anchos=[2.7, 3.2, 1.8, 1.9, 1.8, 3.6],
)

# Actividad 3
actividad("Actividad 3. Programación de la Entropía Cruzada y Gradiente Descendente (40 min)")
inf.titulo("Objetivo de la actividad", antes=2)
inf.texto(
    "Derivar e implementar en código Python el gradiente analítico de la Entropía Cruzada y la "
    "regla de actualización iterativa de Gradiente Descendente para hallar el vector de pesos β."
)
inf.titulo("Derivación del gradiente y regla de actualización")
inf.texto(
    "Como la derivada de la función sigmoide cumple σ'(z) = σ(z)(1 − σ(z)), al aplicar la "
    "regla de la cadena a la Entropía Cruzada de la Ecuación ({eq:ce}) respecto a cada peso "
    "β~j~ los denominadores σ(z~i~)(1 − σ(z~i~)) se cancelan exactamente, dando lugar a la "
    "forma matricial del gradiente (Ecuación ({eq:gradiente})):"
)
inf.ecuacion(
    r("∇J") + delim(r("β")) + r("=") + frac(r("1"), r("N")) +
    suma(r("i=1"), r("N"), delim(r("σ") + delim(sup(sub(acento(r("x"), "̃"), r("i")), r("T")) + r("β")) + r("−") + sub(r("y"), r("i"))) + sub(acento(r("x"), "̃"), r("i"))) +
    r("=") + frac(r("1"), r("N")) + sup(acento(r("X"), "̃"), r("T")) +
    delim(r("σ") + delim(acento(r("X"), "̃") + r("β")) + r("−y")),
    clave="gradiente",
)
inf.texto(
    "Partiendo de pesos iniciales nulos β^(0)^ = 0, en cada época t = 0, 1, ..., T − 1 el "
    "algoritmo de Gradiente Descendente actualiza el vector de pesos completo en sentido "
    "opuesto al gradiente con tasa de aprendizaje η = 0.15 durante T = 1 500 épocas "
    "(Ecuación ({eq:gd})):"
)
inf.ecuacion(
    sup(r("β"), delim(r("t+1"))) + r("=") + sup(r("β"), delim(r("t"))) + r("−η·∇J") + delim(sup(r("β"), delim(r("t")))),
    clave="gd",
)
inf.texto(
    "Adicionalmente, para verificar con rigor numérico que nuestro bucle de Gradiente "
    "Descendente alcanza el mínimo global exacto de la Entropía Cruzada, se contrastó el "
    "resultado con scipy.optimize.minimize (método cuasi-Newton BFGS) alimentado únicamente con "
    "nuestras funciones entropia_cruzada y gradiente_entropia_cruzada."
)

# Actividad 4
actividad("Actividad 4. Evaluación del clasificador en los 4 Data Marts (25 min)")
inf.titulo("Objetivo de la actividad", antes=2)
inf.texto(
    "Evaluar cada modelo entrenado mediante la exactitud de entrenamiento (Acc. Train), la "
    "exactitud de prueba (Acc. Test), la matriz de confusión, la sensibilidad, la especificidad "
    "y las cotas estadísticas de generalización."
)
inf.titulo("Métricas de evaluación y generalización")
inf.texto(
    "En el conjunto de prueba de tamaño M, cada predicción se compara con la clase real y~i~ "
    "para contabilizar verdaderos positivos (VP), verdaderos negativos (VN), falsos positivos "
    "(FP) y falsos negativos (FN). La exactitud es el complemento del error de clasificación "
    "(Ecuación ({eq:acc})), y el intervalo de confianza al 95 % de E~out~ junto con la cota de "
    "Hoeffding (con δ = 0.05) vienen dados por la Ecuación ({eq:hoeff2}):"
)
VPt, VNt, FPt, FNt = (tx(s) for s in ("VP", "VN", "FP", "FN"))
inf.ecuacion(
    tx("Acc") + r("=") + frac(VPt + r("+") + VNt, VPt + r("+") + VNt + r("+") + FPt + r("+") + FNt) +
    r("=1−E"),
    clave="acc",
)
inf.ecuacion(
    sub(r("IC"), r("95%")) + r("=") + sub(r("E"), tx("out")) + r("±1.96") +
    raiz(frac(sub(r("E"), tx("out")) + delim(r("1−") + sub(r("E"), tx("out"))), r("M"))) +
    tx(",      ") + sub(r("ε"), tx("Hoeffding")) + r("=") +
    raiz(frac(func("ln", frac(r("2"), r("δ"))), r("2M"))),
    clave="hoeff2",
)

# Actividad 5
actividad("Actividad 5. Interpretación del vector de pesos β y frontera 2D con PCA (15 min)")
inf.titulo("Objetivo de la actividad", antes=2)
inf.texto(
    "Interpretar el signo y magnitud de los coeficientes β aprendidos en cada Data Mart y "
    "visualizar la frontera de decisión en 2D empleando Análisis de Componentes Principales (PCA)."
)
inf.titulo("Por qué la frontera 2D se grafica con PCA y no con t-SNE")
inf.texto(
    "El modelo principal de cada Data Mart se entrena con **todas** las características "
    "originales (10 a 16 variables). Para dibujar una figura bidimensional de apoyo con la "
    "recta de frontera P(y = 1 | v~1~, v~2~) = 0.5 y proyectar sobre ella el conjunto de "
    "prueba sin fuga de datos, se requiere una transformación paramétrica que aplique la misma "
    "matriz aprendida en el entrenamiento a la malla del plano y a los puntos de prueba. "
    "t-SNE no posee transformación fuera de la muestra, mientras que PCA sí define la proyección "
    "lineal exacta V = X̃ U~2~. Por ello, la figura de frontera 2D se construye sobre los dos "
    "primeros componentes principales ajustados con el entrenamiento."
)

# ----------------------------------------------------------------------------
# 2.7 Resultados obtenidos
# ----------------------------------------------------------------------------
seccion("2.7 Resultados obtenidos")
inf.texto(
    "Los resultados se generaron al ejecutar python 2parcial/Tarea2_Regresion_Logistica/"
    "regresion_logistica.py en la terminal integrada de Visual Studio Code."
)

inf.titulo("2.7.1 Ejecución del programa")
if capturas:
    inf.texto(
        f"La salida completa en consola se muestra en las Ilustraciones {{fig:cap2_1}} a "
        f"{{fig:cap2_{len(capturas)}}}."
    )
    for k, ruta in enumerate(capturas, 1):
        inf.imagen(
            ruta,
            15.5,
            f"Ejecución de regresion_logistica.py en Visual Studio Code (parte {k} de {len(capturas)}).",
            clave=f"cap2_{k}",
            fuente="Captura de la terminal integrada de Visual Studio Code.",
        )

inf.titulo("2.7.2 Tabla consolidada de exactitud y Entropía Cruzada (Acc. Train y Acc. Test)")
filas_res2 = []
for row in tabla_res.itertuples():
    filas_res2.append([
        row.Data_Mart,
        str(row.n_Caracteristicas),
        num(row.Loss_Train, 4),
        num(row.Loss_SciPy_BFGS, 4),
        num(row.Loss_Test, 4),
        pct(row.Acc_Train, 2),
        pct(row.Acc_Test, 2),
        f"{pct(row.Sensibilidad, 1)} / {pct(row.Especificidad, 1)}",
    ])
inf.tabla(
    "Resultados de Entropía Cruzada y Exactitud de la Regresión Logística en los 4 Data Marts",
    [
        "Data Mart",
        "Dim. X",
        "J_train (GD)",
        "J_train (BFGS)",
        "J_test",
        "Acc. Train",
        "Acc. Test",
        "Sens. / Espec.",
    ],
    filas_res2,
    clave="resultados2",
    anchos=[2.7, 1.1, 1.8, 1.9, 1.6, 1.8, 1.8, 2.3],
)
inf.texto(
    "La Tabla {tab:resultados2} demuestra dos hechos fundamentales: primero, la Entropía "
    "Cruzada alcanzada por nuestro algoritmo de Gradiente Descendente (J~train~ GD) coincide "
    "hasta el tercer o cuarto decimal con el mínimo exacto de SciPy BFGS en los cuatro Data "
    "Marts; segundo, la exactitud de prueba (Acc. Test) es consistente con la de entrenamiento "
    "(Acc. Train) en todos los casos: **75.00 %** en Préstamos, **92.25 %** en Saldo Mensual "
    "(predicción de sobregiro en t + 1), **74.84 %** en Órdenes Permanentes y **72.38 %** en "
    "Transacciones."
)

inf.titulo("2.7.3 Vectores de pesos finales β entregados por cada Data Mart")
inf.texto(
    "Cumpliendo con el entregable exigido en la pizarra 2, las Tablas {tab:pesos_DM1_Prestamos} "
    "a {tab:pesos_DM4_Transacciones} reportan el vector completo de pesos finales β = [β~0~, "
    "β~1~, ..., β~n~]^T^ aprendido en cada Data Mart mediante Gradiente Descendente, su "
    "contraste con SciPy BFGS y la importancia relativa porcentual de cada característica."
)

for dm_id, titulo_dm in [
    ("DM1_Prestamos", "Data Mart 1 — Fact_Prestamos (Mora vs. Sano, 17 parámetros)"),
    ("DM2_Saldo_Mensual", "Data Mart 2 — Fact_Saldo_Cuenta_Mensual (Sobregiro t+1, 16 parámetros)"),
    ("DM3_Ordenes", "Data Mart 3 — Fact_Ordenes (Obligación vs. Hogar SIPO, 11 parámetros)"),
    ("DM4_Transacciones", "Data Mart 4 — Fact_Transacciones (Egreso vs. Ingreso, 12 parámetros)"),
]:
    sub_p = pesos_todos[pesos_todos["Data_Mart"] == dm_id]
    filas_p = []
    for r_p in sub_p.itertuples():
        imp_txt = "— (Sesgo)" if r_p.Parametro == "beta_0" else f"{r_p.Importancia_Relativa_Pct:.2f} %"
        filas_p.append([
            r_p.Parametro.replace("beta_", "β~") + ("~" if "beta_" in r_p.Parametro else ""),
            r_p.Variable,
            num(r_p.Peso_Gradiente_Descendente, 4),
            num(r_p.Peso_Optimizador_SciPy_BFGS, 4),
            imp_txt,
        ])
    inf.tabla(
        f"Vector de pesos final β para {titulo_dm}",
        ["Parámetro", "Característica asociada", "Peso β (Gradiente Desc.)", "Peso β (SciPy BFGS)", "Importancia Relativa"],
        filas_p,
        clave=f"pesos_{dm_id}",
        anchos=[2.0, 5.2, 2.7, 2.7, 2.4],
        alinear=[
            WD_ALIGN_PARAGRAPH.CENTER,
            WD_ALIGN_PARAGRAPH.LEFT,
            WD_ALIGN_PARAGRAPH.CENTER,
            WD_ALIGN_PARAGRAPH.CENTER,
            WD_ALIGN_PARAGRAPH.CENTER,
        ],
    )

inf.texto(
    "La inspección de los vectores β confirma la coherencia financiera de los cuatro modelos: "
    "en **Préstamos**, los mayores pesos corresponden al monto del préstamo, saldo pendiente y "
    "ratio cuota/saldo previo (mayor carga financiera incrementa la probabilidad de mora); en "
    "**Saldo Mensual**, los pesos negativos dominantes en saldo mínimo, saldo promedio y saldo "
    "de fin de mes del período t indican que la caída del colchón de liquidez en el mes actual "
    "dispara la probabilidad de sobregiro en el mes t + 1; en **Órdenes Permanentes**, el monto "
    "de la orden y la edad del cliente discriminan las obligaciones financieras frente al pago "
    "de servicios del hogar; y en **Transacciones**, la magnitud del movimiento y el día del "
    "mes concentran la mayor capacidad discriminante entre egresos e ingresos."
)

inf.titulo("2.7.4 Análisis de generalización: entrenamiento frente a prueba")
filas_gen = []
for row in tabla_res.itertuples():
    gap = row.E_out - row.E_in
    e_med = 0.5 * (row.E_in + row.E_out)
    se_dif = np.sqrt(max(e_med * (1.0 - e_med), 1e-5) * (1.0 / row.N_Train + 1.0 / row.N_Test))
    dentro = "Sí" if abs(gap) <= 1.96 * se_dif else "No"
    filas_gen.append([
        row.Data_Mart,
        pct(row.E_in, 2),
        pct(row.E_out, 2),
        f"{num(100.0 * gap, 2)} pts",
        f"± {num(100.0 * 1.96 * se_dif, 2)} pts",
        f"± {pct(row.IC95_Semi, 2)}",
        dentro,
    ])
inf.tabla(
    "Comparación entre error de entrada E_in y error de prueba E_out en los 4 Data Marts",
    ["Data Mart", "E_in (Train)", "E_out (Test)", "E_out − E_in", "Azar ±1.96·σ_dif", "IC 95 % E_out", "¿Sin sobreajuste?"],
    filas_gen,
    clave="generalizacion2",
    anchos=[2.7, 1.9, 1.9, 2.0, 2.3, 2.1, 2.1],
)
inf.texto(
    "En los cuatro Data Marts la diferencia E~out~ − E~in~ se encuentra completamente dentro "
    "del margen ±1.96·σ~dif~ explicable por la variación muestral entre entrenamiento y prueba "
    "(Tabla {tab:generalizacion2}), descartando cualquier síntoma de sobreajuste."
)

inf.titulo("2.7.5 Curvas de convergencia de la Entropía Cruzada y de la Exactitud")
inf.imagen(
    RES / "convergencia_entropia_cruzada.png",
    15.2,
    "Convergencia de la Entropía Cruzada J(β) en entrenamiento y prueba durante las 1 500 épocas de Gradiente Descendente.",
    clave="conv_loss",
    fuente="Elaboración propia con Python, NumPy y Matplotlib.",
)
inf.imagen(
    RES / "convergencia_exactitud.png",
    15.2,
    "Evolución de la Exactitud de entrenamiento (Acc. Train) y de prueba (Acc. Test) por época.",
    clave="conv_acc",
    fuente="Elaboración propia con Python, NumPy y Matplotlib.",
)
inf.texto(
    "A diferencia del perceptrón simple —cuyo error oscila indefinidamente cuando las clases se "
    "superponen—, la Ilustración {fig:conv_loss} muestra que la Entropía Cruzada J(β) desciende "
    "de forma suave, monótona y asintótica hasta alcanzar el mínimo global en los cuatro Data "
    "Marts, estabilizando tanto Acc. Train como Acc. Test (Ilustración {fig:conv_acc})."
)

inf.titulo("2.7.6 Curvas sigmoide σ(z) y matrices de confusión en prueba")
inf.imagen(
    RES / "curvas_sigmoide_test.png",
    15.2,
    "Curvas logísticas σ(z) = 1 / (1 + e^-z) y probabilidades estimadas sobre el conjunto de prueba de cada Data Mart.",
    clave="sigmoide_fig",
    fuente="Elaboración propia con Python y Matplotlib.",
)
inf.imagen(
    RES / "matrices_confusion_test.png",
    14.5,
    "Matrices de confusión de la Regresión Logística evaluadas en el conjunto de prueba (20 %) de los 4 Data Marts.",
    clave="cm_fig",
    fuente="Elaboración propia con Python y Matplotlib.",
)

inf.titulo("2.7.7 Fronteras de decisión 2D de apoyo proyectadas con PCA")
inf.imagen(
    RES / "fronteras_decision_pca_2d.png",
    15.2,
    "Fronteras de decisión lineales P(y=1|v1, v2) = 0.5 proyectadas con PCA 2D sobre los conjuntos de prueba.",
    clave="pca_front",
    fuente="Elaboración propia con Python, scikit-learn (PCA) y Matplotlib.",
)

inf.titulo("2.7.8 Cumplimiento de las instrucciones")
inf.tabla(
    "Verificación de las instrucciones de clase para la Tarea 2",
    ["Instrucción", "Cumplimiento en este trabajo"],
    [
        [
            "1. Entrenar Regresión Logística con todas las características y 2 clases",
            "Entrenada con las 16, 15, 10 y 11 variables de los 4 Data Marts reducidos a Clase en {0, 1}.",
        ],
        [
            "2. No usar LogisticRegression de scikit-learn",
            "Programado desde cero en regresion_logistica.py sin importar ni invocar LogisticRegression.",
        ],
        [
            "3. Usar solo Entropía Cruzada y Gradiente Descendente",
            "Funciones explícitas entropia_cruzada y gradiente_entropia_cruzada optimizadas por descenso de gradiente y verificadas con scipy.optimize.minimize.",
        ],
        [
            "4. Entregar el vector de pesos final β",
            "Reportado completo en las Tablas {tab:pesos_DM1_Prestamos} a {tab:pesos_DM4_Transacciones} y en vectores_pesos_beta_todos.csv.",
        ],
        [
            "5. Entregar Acc. Train, Acc. Test y figuras",
            "Reportados en la Tabla {tab:resultados2} y en las Ilustraciones {fig:conv_loss} a {fig:pca_front}.",
        ],
    ],
    clave="cumplimiento2",
    anchos=[5.4, 9.6],
    alinear=[WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.LEFT],
)

# ----------------------------------------------------------------------------
# 2.8 a 2.12
# ----------------------------------------------------------------------------
seccion("Habilidades blandas empleadas en la práctica")
casillas([
    (False, "Liderazgo"),
    (True, "Trabajo en equipo"),
    (True, "Comunicación asertiva"),
    (False, "La empatía"),
    (True, "Pensamiento crítico"),
    (True, "Flexibilidad"),
    (False, "La resolución de conflictos"),
    (True, "Adaptabilidad"),
    (True, "Responsabilidad"),
])

seccion("2.9 Conclusiones")
inf.lista([
    "**Sobre la optimización de la Entropía Cruzada por Gradiente Descendente:** a diferencia "
    "de la regla discontinua del perceptrón, la función de pérdida de Entropía Cruzada Binaria "
    "J(β) es diferenciable y estrictamente convexa, lo que permitió que el descenso por "
    "gradiente programado desde cero convergiera de forma monótona al mismo mínimo global que "
    "el optimizador cuasi-Newton BFGS de SciPy en los cuatro Data Marts.",
    "**Sobre el desempeño y generalización en los 4 Data Marts:** utilizando todas las "
    "características libres de fuga de datos y respetando el orden Partición 80/20 → Balanceo "
    "→ Escalado z-score, la Regresión Logística alcanzó exactitudes de prueba (Acc. Test) de "
    "**75.00 %** en Préstamos (mora crediticia), **92.25 %** en Saldo Mensual (predicción "
    "anticipada del sobregiro en el mes t + 1), **74.84 %** en Órdenes Permanentes y "
    "**72.38 %** en Transacciones, con diferencias entre entrenamiento y prueba estadísticamente "
    "indistinguibles del azar.",
], numerada=True)

seccion("2.10 Recomendaciones")
inf.texto(
    "Se recomienda incorporar regularización L2 (penalización λ‖β‖^2^ sobre la Entropía "
    "Cruzada) y curvas ROC-AUC al evaluar costos asimétricos de negocio —por ejemplo, en "
    "Fact_Prestamos, donde conceder un préstamo que cae en mora (falso negativo) resulta más "
    "costoso para el banco que revisar manualmente una solicitud sana (falso positivo), lo que "
    "permite ajustar el umbral de decisión σ(z) por debajo de 0.5 para elevar la sensibilidad."
)

seccion("2.11 Referencias bibliográficas")
referencias = [
    '[1] Material docente, "Classification and Logistic Regression", apuntes de clase, '
    "Inteligencia de Negocios, Universidad Técnica de Ambato, 2026.",
    "[2] D. R. Cox, \"The regression analysis of binary sequences,\" Journal of the Royal "
    "Statistical Society: Series B, vol. 20, no. 2, pp. 215–232, 1958.",
    "[3] C. M. Bishop, Pattern Recognition and Machine Learning. New York, NY, USA: Springer, 2006.",
    "[4] Y. S. Abu-Mostafa, M. Magdon-Ismail y H.-T. Lin, Learning From Data. Pasadena, CA, USA: "
    "AMLBook, 2012.",
    "[5] T. Hastie, R. Tibshirani y J. Friedman, The Elements of Statistical Learning, 2.ª ed. "
    "New York, NY, USA: Springer, 2009.",
    '[6] P. Virtanen et al., "SciPy 1.0: fundamental algorithms for scientific computing in '
    'Python," Nature Methods, vol. 17, pp. 261–272, 2020.',
]
for ref in referencias:
    inf.texto(
        ref,
        alineacion=WD_ALIGN_PARAGRAPH.LEFT,
        sangria=Cm(1.27),
        primera=Cm(-0.63),
        interlineado=1.15,
    )

seccion("2.12 Anexos")
inf.texto(
    "Las capturas de ejecución en Visual Studio Code (sección 2.7.1), la tabla consolidada de "
    "resultados (Tabla {tab:resultados2}), los cuatro vectores completos de pesos finales β "
    "(Tablas {tab:pesos_DM1_Prestamos} a {tab:pesos_DM4_Transacciones}) y las figuras de "
    "convergencia, sigmoide, matrices de confusión y fronteras PCA 2D se encuentran integrados "
    "en la sección 2.7. El código fuente se entrega en regresion_logistica.py."
)

# ----------------------------------------------------------------------------
# Formato global y guardado
# ----------------------------------------------------------------------------
estilo = doc.styles["Normal"]
estilo.font.name = FUENTE
estilo.font.size = Pt(12)
estilo.element.rPr.rFonts.set(qn("w:eastAsia"), FUENTE)
for q in doc.paragraphs:
    for run in q.runs:
        if run.font.name != "Courier New":
            fuente_run(run, 12)
for run in doc.paragraphs[0].runs:
    run.font.size = Pt(13)

inf.resolver_referencias()
doc.save(SALIDA)
shutil.copy2(SALIDA, SALIDA_COPIA)
print(f"Informe Tarea 2 generado: {SALIDA}")
print(f"Copia en raíz de 2parcial: {SALIDA_COPIA}")
print(
    f"Tablas: {inf.contador['tab']} | Ilustraciones: {inf.contador['fig']} | "
    f"Ecuaciones: {inf.contador['eq']}"
)
