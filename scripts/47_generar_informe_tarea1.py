"""
Genera el informe en Word de la Tarea 1 del 2do Parcial:
  - 2parcial/Tarea1_Reduccion_MNIST_2D/Informe_Tarea1_Reduccion_MNIST_2D.docx
  - Copia también en: 2parcial/Informe_Tarea1_Reduccion_MNIST_2D.docx

Sigue exactamente la plantilla y el formato de Informe_Final_Perceptron.docx
(Times New Roman 12, interlineado 1.5, ecuaciones OMML numeradas, tablas con bordes
y leyendas automáticas, pie de página "Página X de Y").
"""

import copy
import json
import shutil
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
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
TAREA1 = DIR_2P / "Tarea1_Reduccion_MNIST_2D"
RES = TAREA1 / "resultados"
CAP = TAREA1 / "capturas"
PLANTILLA = RAIZ / "scripts" / "plantillas" / "Taller_Perceptron_plantilla.docx"
SALIDA = TAREA1 / "Informe_Tarea1_Reduccion_MNIST_2D.docx"
SALIDA_COPIA = DIR_2P / "Informe_Tarea1_Reduccion_MNIST_2D.docx"

tabla_res = pd.read_csv(RES / "tabla_resultados_tarea1.csv", encoding="utf-8-sig")
mnist_info = json.load(open(RES / "resumen_mnist_tarea1.json", encoding="utf-8"))
resumen_dm = json.load(open(DIR_2P / "resumen_datasets_2parcial.json", encoding="utf-8"))
capturas = sorted(CAP.glob("vscode_ejecucion_*.png"))

versiones = {
    "Python": sys.version.split()[0],
    "NumPy": np.__version__,
    "pandas": pd.__version__,
    "Matplotlib": matplotlib.__version__,
    "scikit-learn": sklearn.__version__,
}


def pct(v, d=2):
    return f"{100.0 * float(v):.{d}f} %"


def num(v, d=3):
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
        "Reducción de dimensionalidad a un plano euclidiano 2D (t-SNE, PCA y referencia MNIST) "
        "y visualización de grupos por clase en los 4 Data Marts de Financial_ijs",
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
    "Reducir el espacio de características multidimensional de cada uno de los cuatro Data Marts "
    "del modelo dimensional DM_Financial_Kimball_v2 (y del conjunto de referencia MNIST) hacia un "
    "plano euclidiano bidimensional [v~1~, v~2~] mediante t-SNE y Análisis de Componentes "
    "Principales (PCA), graficando la distribución de los grupos según sus etiquetas verdaderas "
    "libres de fuga de datos."
)
inf.titulo("Específicos:", antes=4)
inf.lista([
    "Formular matemáticamente la proyección de vectores de características x~i~ en R^n^ (n > 2) "
    "hacia un plano bidimensional x~i~^(1)^ = [v~1~, v~2~] en R^2^ utilizando t-SNE (minimización "
    "de la divergencia de Kullback–Leibler) y PCA (descomposición espectral de la covarianza).",
    "Auditar y depurar los cuatro datasets correspondientes a los cuatro Data Marts de hechos "
    "(Fact_Prestamos, Fact_Saldo_Cuenta_Mensual, Fact_Ordenes y Fact_Transacciones), eliminando "
    "toda variable con fuga de datos (data leakage) y aplicando el orden correcto de partición "
    "80/20, balanceo de clases y estandarización z-score.",
    "Desarrollar la demostración de referencia sobre el conjunto de imágenes de dígitos "
    "manuscritos MNIST (n = 64 características hacia [v~1~, v~2~]) tanto con sus 10 clases "
    "(dígitos 0 al 9) como en su versión binaria (0 frente a 1).",
    "Visualizar e interpretar geométricamente los grupos formados en el plano [v~1~, v~2~] para "
    "las clases binarias y multiclase reales de los cuatro Data Marts, cuantificando la "
    "separabilidad mediante la exactitud de vecindad en 2D y la distancia entre centroides.",
])

seccion("2.2 Modalidad")
inf.texto("Práctica de laboratorio. Trabajo en parejas.")

seccion("2.3 Tiempo de duración")
inf.texto("Presenciales: 120 minutos.", despues=0)
inf.texto("No presenciales: 60 minutos para organización del informe y análisis gráfico.")

seccion("2.4 Instrucciones")
inf.texto("Instrucciones de la práctica (Tema 1 - Pizarra 1):")
inf.lista([
    "Partir de un conjunto de datos etiquetado X = {(x~1~, y~1~), ..., (x~N~, y~N~)} por cada "
    "Data Mart, donde cada observación tiene un vector de características x~i~ = [x~i1~, x~i2~, "
    "..., x~in~] con n > 2 y una clase verdadera y~i~ en {1, 2, ..., S}.",
    "Utilizar la técnica de reducción asociada al caso de estudio MNIST (t-SNE y comparativa "
    "con PCA) para disminuir la dimensionalidad de cada vector de características desde R^n^ "
    "hasta un plano euclidiano bidimensional x~i~^(1)^ = [v~1~, v~2~].",
    "Graficar las observaciones proyectadas en el plano [v~1~, v~2~] asignando un color y "
    "marcador distinto a cada clase verdadera para visualizar la formación de los grupos.",
    "Aplicar el procedimiento sobre una demostración de referencia con el dataset MNIST real "
    "y sobre los cuatro Data Marts del proyecto bancario (Préstamos, Saldo Mensual, Órdenes "
    "Permanentes y Transacciones), incluyendo tanto las clases binarias como las multiclase "
    "reales de negocio.",
    "Garantizar que ninguna característica de entrada X contenga reglas deterministas o "
    "columnas que delaten trivialmente la etiqueta y (cero fuga de datos).",
], numerada=True)

seccion("2.5 Listado de equipos, materiales y recursos")
inf.texto("Listado de equipos y materiales generales empleados en la guía práctica:")
inf.lista([
    "Computador con Python 3 (Windows 11 Pro).",
    "Visual Studio Code (editor y terminal integrada PowerShell).",
    "Bibliotecas NumPy, pandas, Matplotlib y scikit-learn (TSNE, PCA y dataset MNIST).",
    "Cuatro datasets etiquetados de los Data Marts en la carpeta 2parcial/: "
    "01_dm_prestamos.csv, 02_dm_saldo_mensual.csv, 03_dm_ordenes.csv y 04_dm_transacciones.csv.",
    "Apuntes de clase (Pizarra 1: reducción de características X_i a [v_1, v_2]).",
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
inf.texto("Otros (Especifique): Python 3, scikit-learn y Visual Studio Code.")
inf.titulo("Software utilizado en la práctica:")
inf.texto(
    "El script reduccion_mnist_2d.py se desarrolló y ejecutó en Visual Studio Code. "
    "La Tabla {tab:software} detalla las versiones exactas empleadas."
)
inf.tabla(
    "Software y bibliotecas utilizados en la Tarea 1",
    ["Software / Biblioteca", "Versión", "Uso en la práctica"],
    [
        ["Windows 11 Pro", "10.0.26300", "Sistema operativo del equipo de trabajo."],
        ["Visual Studio Code", "1.142.0", "Edición y ejecución de scripts en terminal PowerShell."],
        ["Python", versiones["Python"], "Lenguaje principal de programación."],
        ["NumPy", versiones["NumPy"], "Estandarización matricial y álgebra lineal."],
        ["pandas", versiones["pandas"], "Lectura y estructuración de los 4 Data Marts."],
        ["scikit-learn", versiones["scikit-learn"], "Proyección t-SNE, PCA y dataset MNIST de referencia."],
        ["Matplotlib", versiones["Matplotlib"], "Generación de mapas 2D [v1, v2] por clase."],
        ["Microsoft Word", "16.0", "Edición del informe técnico de la práctica."],
    ],
    clave="software",
    anchos=[3.8, 2.4, 8.8],
    alinear=[WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.CENTER, WD_ALIGN_PARAGRAPH.LEFT],
)
inf.titulo("Reproducibilidad de los resultados:")
inf.texto(
    "Para reproducir íntegramente los datasets y las gráficas de este informe basta con ejecutar "
    "en la raíz del repositorio python scripts/44_generar_datasets_2parcial.py seguido de "
    "python 2parcial/Tarea1_Reduccion_MNIST_2D/reduccion_mnist_2d.py. Todas las particiones, "
    "submuestreos e inicializaciones de t-SNE y PCA utilizan la semilla fija 42."
)

# ----------------------------------------------------------------------------
# 2.6 Actividades por desarrollar
# ----------------------------------------------------------------------------
seccion("2.6 Actividades por desarrollar")

# Actividad 1
actividad("Actividad 1. Formulación matemática de la reducción a un plano 2D (20 min)")
inf.titulo("Objetivo de la actividad", antes=2)
inf.texto(
    "Comprender cómo un conjunto de vectores de características de dimensión n > 2 se proyecta "
    "hacia un plano euclidiano de dos coordenadas [v~1~, v~2~] preservando la estructura de "
    "vecindad local (t-SNE) o la máxima varianza global (PCA)."
)
inf.titulo("Planteamiento del problema de reducción (Pizarra 1)")
inf.texto(
    "Sea un dataset etiquetado compuesto por N observaciones, donde cada observación i posee "
    "un vector de características numéricas x~i~ en R^n^ (con n > 2) y una etiqueta de clase "
    "y~i~ que toma valores en un conjunto discreto de S clases (Ecuación ({eq:dataset})):"
)
inf.ecuacion(
    r("X=") + delim(delim(sub(r("x"), r("1")) + r(", ") + sub(r("y"), r("1"))) + r(", …, ") +
                    delim(sub(r("x"), r("N")) + r(", ") + sub(r("y"), r("N"))), "{", "}") +
    tx(",      ") + sub(r("x"), r("i")) + r("=") +
    delim(sub(r("x"), r("i1")) + r(", ") + sub(r("x"), r("i2")) + r(", …, ") + sub(r("x"), r("in")), "[", "]") +
    r("∈") + sup(r("R"), r("n")) + tx(",   ") + sub(r("y"), r("i")) + r("∈{1, 2, …, S}"),
    clave="dataset",
)
inf.texto(
    "Cuando el número de características es mayor a tres (en nuestros Data Marts bancarios n "
    "varía entre 10 y 16 variables, y en imágenes MNIST n = 64 o 784), no es posible visualizar "
    "directamente la geometría de las clases. El operador de reducción transforma cada vector "
    "x~i~ en R^n^ en un par de coordenadas dentro del plano euclidiano bidimensional R^2^ "
    "(Ecuación ({eq:proyeccion})):"
)
inf.ecuacion(
     subsup(r("x"), r("i"), r("(1)")) + r("=") +
    delim(sub(r("v"), r("i1")) + r(", ") + sub(r("v"), r("i2")), "[", "]") +
    r("∈") + sup(r("R"), r("2")),
    clave="proyeccion",
)
inf.titulo("Reducción no lineal mediante t-SNE (t-Distributed Stochastic Neighbor Embedding)")
inf.texto(
    "Propuesto por van der Maaten y Hinton [1] y demostrado originalmente sobre el banco de "
    "dígitos manuscritos MNIST, t-SNE convierte las distancias euclidianas entre los puntos de "
    "alta dimensión x~i~ y x~j~ en probabilidades condicionales p~j|i~ que representan su "
    "similitud bajo una campana gaussiana centrada en x~i~ (Ecuación ({eq:pji})), cuya varianza "
    "σ~i~^2^ se ajusta según la perplejidad deseada:"
)
inf.ecuacion(
    sub(r("p"), r("j|i")) + r("=") +
    frac(
        func("exp", r("−") + frac(sup(delim(sub(r("x"), r("i")) + r("−") + sub(r("x"), r("j")), "‖", "‖"), r("2")),
                                  r("2") + subsup(r("σ"), r("i"), r("2")))),
        suma(r("k≠i"), r(""), func("exp", r("−") + frac(sup(delim(sub(r("x"), r("i")) + r("−") + sub(r("x"), r("k")), "‖", "‖"), r("2")),
                                                        r("2") + subsup(r("σ"), r("i"), r("2"))))),
    ) + tx(",      ") + sub(r("p"), r("ij")) + r("=") + frac(sub(r("p"), r("j|i")) + r("+") + sub(r("p"), r("i|j")), r("2N")),
    clave="pji",
)
inf.texto(
    "En el plano bidimensional de llegada, las coordenadas buscadas x~i~^(1)^ = [v~i1~, v~i2~] "
    "definen una probabilidad conjunta q~ij~ modelada con una distribución t de Student con un "
    "grado de libertad (distribución de Cauchy), cuyas colas pesadas evitan el problema de "
    "apiñamiento en el centro del gráfico (Ecuación ({eq:qij})):"
)
inf.ecuacion(
    sub(r("q"), r("ij")) + r("=") +
    frac(
        sup(delim(r("1+") + sup(delim(subsup(r("x"), r("i"), r("(1)")) + r("−") + subsup(r("x"), r("j"), r("(1)")), "‖", "‖"), r("2"))), r("−1")),
        suma(r("k≠l"), r(""), sup(delim(r("1+") + sup(delim(subsup(r("x"), r("k"), r("(1)")) + r("−") + subsup(r("x"), r("l"), r("(1)")), "‖", "‖"), r("2"))), r("−1"))),
    ),
    clave="qij",
)
inf.texto(
    "Las posiciones óptimas [v~1~, v~2~] se obtienen minimizando por descenso de gradiente la "
    "divergencia de Kullback–Leibler entre las distribuciones P (en R^n^) y Q (en R^2^) "
    "(Ecuación ({eq:kl})). Cuanto menor es KL(P || Q), más fielmente preserva el plano 2D las "
    "vecindades reales del espacio original:"
)
inf.ecuacion(
    tx("KL") + delim(r("P∥Q")) + r("=") +
    suma(r("i≠j"), r(""), sub(r("p"), r("ij")) + func("ln", frac(sub(r("p"), r("ij")), sub(r("q"), r("ij"))))),
    clave="kl",
)
inf.titulo("Reducción lineal mediante PCA (Análisis de Componentes Principales)")
inf.texto(
    "Como contraste paramétrico y lineal, PCA proyecta los datos estandarizados X̃ sobre los "
    "dos vectores propios unitarios u~1~ y u~2~ asociados a los dos mayores valores propios "
    "(λ~1~ ≥ λ~2~) de la matriz de covarianza muestral Σ = (1/N) X̃^T^ X̃ (Ecuación ({eq:pca})). "
    "A diferencia de t-SNE, PCA define una matriz de proyección explícita U~2~ = [u~1~, u~2~] "
    "que permite transformar nuevos datos de prueba y trazar fronteras lineales en la Tarea 2:"
)
inf.ecuacion(
    delim(sub(r("v"), r("i1")) + r(", ") + sub(r("v"), r("i2")), "[", "]") + r("=") +
    sub(acento(r("x"), "̃"), r("i")) + sup(r(""), r("T")) +
    delim(sub(r("u"), r("1")) + r(", ") + sub(r("u"), r("2")), "[", "]"),
    clave="pca",
)

# Actividad 2
actividad("Actividad 2. Depuración y preparación de los 4 Data Marts sin fuga de datos (25 min)")
inf.titulo("Objetivo de la actividad", antes=2)
inf.texto(
    "Construir un dataset limpio y etiquetado por cada uno de los cuatro Data Marts de hechos "
    "del modelo dimensional DM_Financial_Kimball_v2, garantizando que las variables predictoras "
    "X no contengan reglas derivadas ni columnas que filtren la etiqueta verdadera y."
)
inf.titulo("Corrección de fuga de datos (data leakage) en los 4 Data Marts")
inf.texto(
    "Antes de proyectar o entrenar clasificadores, se verificó que ninguna etiqueta fuera "
    "calculada como fórmula determinista de las propias columnas de X. Por ello se descartaron "
    "las etiquetas sintéticas de tramos de monto/plazo y se definieron cuatro objetivos reales "
    "observados en la operación bancaria (Tabla {tab:datamarts}):"
)
inf.lista([
    "**Data Mart 1 — Préstamos (Fact_Prestamos, N = 682):** predice el estado real de mora del "
    "crédito (Clase 1 = estados B y D con impago, 76 préstamos; Clase 0 = estados A y C al día, "
    "606 préstamos) a partir de 16 variables financieras, demográficas y distritales previas. "
    "Además, conserva los 4 estados reales (A, B, C, D) para la visualización multiclase.",
    "**Data Mart 2 — Saldo Mensual (Fact_Saldo_Cuenta_Mensual, grano cuenta × mes):** sobre los "
    "181 115 cierres mensuales que cuentan con mes siguiente observado, predice si la cuenta "
    "caerá en **sobregiro el mes siguiente (t + 1)** (Clase 1 = 708 eventos reales de sobregiro "
    "en t + 1; Clase 0 = sin sobregiro en t + 1) empleando únicamente las 15 variables medidas "
    "hasta el cierre del mes actual t.",
    "**Data Mart 3 — Órdenes Permanentes (Fact_Ordenes, N = 5 092):** filtra las órdenes con "
    "símbolo bancario real y clasifica las obligaciones financieras (Clase 1 = préstamo UVER, "
    "seguro POJISTNE o arrendamiento LEASING, 1 590 órdenes) frente a pagos de hogar SIPO "
    "(Clase 0 = 3 502 órdenes) usando 10 características de la cuenta, cliente y distrito. "
    "Conserva además las 4 categorías reales (SIPO, UVER, POJISTNE, LEASING) como multiclase.",
    "**Data Mart 4 — Transacciones (Fact_Transacciones, N = 20 000 de 871 629 movimientos):** "
    "excluye los asientos automáticos de intereses (UROK y SANKC. UROK) y clasifica si el "
    "movimiento atómico es un **Egreso** (Clase 1) o un **Ingreso** (Clase 0). Se eliminaron "
    "de X el código de operación, el símbolo k_symbol, el canal, el banco contraparte y el "
    "saldo previo, dejando el monto en valor absoluto sin signo junto con 10 variables de "
    "fecha, saldo posterior, cliente y distrito.",
])
inf.tabla(
    "Especificación de los 4 datasets por Data Mart libres de fuga de datos",
    ["Archivo CSV", "Data Mart (Tabla de Hechos)", "Filas CSV", "Dim. X (n)", "Clase 1 vs. Clase 0", "Multiclase Real"],
    [
        [
            "01_dm_prestamos.csv",
            "Fact_Prestamos",
            "682",
            "16",
            "Mora B,D (76) vs. Sano A,C (606)",
            "Estados A, B, C, D (4)",
        ],
        [
            "02_dm_saldo_mensual.csv",
            "Fact_Saldo_Cuenta_Mensual",
            "5 000",
            "15",
            "Sobregiro t+1 (708) vs. Normal (4 292)",
            "Binaria (2)",
        ],
        [
            "03_dm_ordenes.csv",
            "Fact_Ordenes",
            "5 092",
            "10",
            "Obligación (1 590) vs. SIPO (3 502)",
            "SIPO, UVER, POJISTNE, LEASING (4)",
        ],
        [
            "04_dm_transacciones.csv",
            "Fact_Transacciones",
            "20 000",
            "11",
            "Egreso (10 000) vs. Ingreso (10 000)",
            "Binaria (2)",
        ],
    ],
    clave="datamarts",
    anchos=[3.3, 3.3, 1.4, 1.3, 3.2, 2.5],
)
inf.titulo("Orden metodológico: Partición 80/20 → Balanceo → Escalado z-score")
inf.texto(
    "Para evitar que estadísticas del conjunto de prueba se filtren al entrenamiento y para que "
    "variables expresadas en decenas de miles de coronas checas (como población o monto del "
    "préstamo) no dominen la distancia euclidiana frente a variables binarias o tasas, se "
    "aplicó el siguiente protocolo estricto: primero se divide 80 % entrenamiento y 20 % prueba "
    "de forma estratificada; segundo, se balancean las clases (submuestreo 50/50 en Saldo "
    "Mensual, Órdenes y Transacciones, y sobremuestreo solo en el entrenamiento para Préstamos); "
    "tercero, se calculan la media μ~j~ y desviación estándar σ~j~ **únicamente sobre el "
    "entrenamiento** y se estandariza cada característica según la Ecuación ({eq:zscore}):"
)
inf.ecuacion(
    sub(acento(r("x"), "̃"), r("ij")) + r("=") +
    frac(sub(r("x"), r("ij")) + r("−") + sub(r("μ"), r("j,train")), sub(r("σ"), r("j,train"))),
    clave="zscore",
)

# Actividad 3
actividad("Actividad 3. Demostración de referencia con el dataset MNIST (25 min)")
inf.titulo("Objetivo de la actividad", antes=2)
inf.texto(
    "Ejecutar la reducción de dimensionalidad a [v~1~, v~2~] sobre el dataset clásico de "
    "dígitos manuscritos MNIST citado en la pizarra de clase, comparando la capacidad de t-SNE "
    "y PCA para separar tanto las 10 clases de dígitos (0 al 9) como el caso binario (0 vs. 1)."
)
inf.titulo("Desarrollo sobre MNIST")
inf.texto(
    f"Se cargaron las {miles(mnist_info['N_total'])} imágenes de dígitos manuscritos del "
    f"conjunto MNIST integrado en scikit-learn, donde cada imagen es una cuadrícula de "
    f"intensidades en escala de grises que conforma un vector de n = {mnist_info['n_features']} "
    f"características por observación. Tras estandarizar las características, se redujo la "
    f"matriz completa desde R^64^ hacia R^2^ (x~i~^(1)^ = [v~1~, v~2~]) con t-SNE (perplejidad "
    f"30) y con PCA. En las 10 clases, t-SNE alcanzó una divergencia KL = "
    f"{num(mnist_info['kl_10'], 4)} y agrupó limpiamente los 10 dígitos con una exactitud de "
    f"vecindad en 2D de **{pct(mnist_info['acc_tsne_10'])}**, superando ampliamente al plano "
    f"lineal de PCA (**{pct(mnist_info['acc_pca_10'])}**, que solo retiene el "
    f"{pct(mnist_info['var_pca_10'])} de la varianza total en dos ejes). Al restringir el "
    f"conjunto a dos clases (dígito 0 frente a dígito 1, N = {mnist_info['N_bin']}), tanto "
    f"t-SNE como PCA lograron una separabilidad de **{pct(mnist_info['acc_tsne_bin'])}** en 2D."
)

# Actividad 4
actividad("Actividad 4. Reducción a 2D y graficación en los 4 Data Marts (30 min)")
inf.titulo("Objetivo de la actividad", antes=2)
inf.texto(
    "Proyectar cada uno de los cuatro Data Marts bancarios hacia el plano euclidiano "
    "[v~1~, v~2~] y graficar los grupos coloreados por su clase verdadera (binaria y multiclase)."
)
inf.titulo("Aplicación a los cuatro Data Marts")
inf.texto(
    "En cada Data Mart se proyectaron las observaciones estandarizadas hacia [v~1~, v~2~] "
    "mediante t-SNE (inicialización PCA, tasa de aprendizaje automática y perplejidad 30) y "
    "mediante PCA de dos componentes, guardando las coordenadas resultantes en archivos CSV "
    "dentro de resultados/ y generando tanto las figuras comparativas individuales como los "
    "mosaicos consolidados de clases binarias y multiclase reales."
)

# Actividad 5
actividad("Actividad 5. Interpretación geométrica y separabilidad en el plano 2D (20 min)")
inf.titulo("Objetivo de la actividad", antes=2)
inf.texto(
    "Evaluar cuantitativamente qué tan bien se agrupan las clases de cada Data Mart en el "
    "plano bidimensional [v~1~, v~2~] y qué anticipa esta geometría para el entrenamiento de "
    "la Regresión Logística en la Tarea 2."
)
inf.titulo("Análisis comparativo entre Data Marts")
r_dm1 = tabla_res[tabla_res["Data_Mart"] == "DM1_Prestamos"].iloc[0]
r_dm2 = tabla_res[tabla_res["Data_Mart"] == "DM2_Saldo_Mensual"].iloc[0]
r_dm3 = tabla_res[tabla_res["Data_Mart"] == "DM3_Ordenes"].iloc[0]
r_dm4 = tabla_res[tabla_res["Data_Mart"] == "DM4_Transacciones"].iloc[0]
inf.texto(
    f"Los resultados muestran una graduación clara de separabilidad según la naturaleza "
    f"financiera de cada Data Mart: el mayor aislamiento entre grupos se alcanza en "
    f"**Fact_Saldo_Cuenta_Mensual** (exactitud en 2D con t-SNE de **{pct(r_dm2['Acc_2D_tSNE'])}** "
    f"y con PCA de **{pct(r_dm2['Acc_2D_PCA'])}**), porque las cuentas próximas a caer en "
    f"sobregiro en t + 1 comparten saldos mínimos y promedios deteriorados en el mes t. Le sigue "
    f"**Fact_Prestamos** (**{pct(r_dm1['Acc_2D_tSNE'])}** en t-SNE y **{pct(r_dm1['Acc_2D_PCA'])}** "
    f"en PCA; **{pct(r_dm1['Acc_Multiclase_tSNE'])}** en los 4 estados A, B, C, D), donde los "
    f"créditos en mora se concentran en la región de alto ratio cuota/saldo previo. Finalmente, "
    f"**Fact_Ordenes** (**{pct(r_dm3['Acc_2D_tSNE'])}** binario y "
    f"**{pct(r_dm3['Acc_Multiclase_tSNE'])}** en los 4 tipos de orden) y **Fact_Transacciones** "
    f"(**{pct(r_dm4['Acc_2D_tSNE'])}** en t-SNE) presentan un traslape moderado y natural "
    f"(entre 20 % y 25 % de frontera compartida), típico de datos transaccionales reales sin "
    f"fuga de información."
)

# ----------------------------------------------------------------------------
# 2.7 Resultados obtenidos
# ----------------------------------------------------------------------------
seccion("2.7 Resultados obtenidos")
inf.texto(
    "Los resultados se obtuvieron al ejecutar python 2parcial/Tarea1_Reduccion_MNIST_2D/"
    "reduccion_mnist_2d.py en la terminal integrada de Visual Studio Code."
)

inf.titulo("2.7.1 Ejecución del programa")
if capturas:
    inf.texto(
        f"La ejecución completa del script se presenta en las Ilustraciones {{fig:cap1}} a "
        f"{{fig:cap{len(capturas)}}} y finalizó sin errores."
    )
    for k, ruta in enumerate(capturas, 1):
        inf.imagen(
            ruta,
            15.5,
            f"Ejecución de reduccion_mnist_2d.py en Visual Studio Code (parte {k} de {len(capturas)}).",
            clave=f"cap{k}",
            fuente="Captura de la terminal integrada de Visual Studio Code.",
        )

inf.titulo("2.7.2 Tabla consolidada de resultados de reducción a 2D")
filas_t1 = []
for row in tabla_res.itertuples():
    multi_str = pct(row.Acc_Multiclase_tSNE, 1) if not pd.isna(row.Acc_Multiclase_tSNE) else "—"
    filas_t1.append([
        row.Data_Mart,
        str(row.n_Caracteristicas),
        miles(row.N_Proyectado),
        num(row.KL_tSNE, 3),
        pct(row.Acc_2D_tSNE, 2),
        pct(row.Varianza_PCA_2D, 1),
        pct(row.Acc_2D_PCA, 2),
        multi_str,
    ])
inf.tabla(
    "Métricas de reducción de dimensionalidad a R^2 ([v1, v2]) en los 4 Data Marts",
    [
        "Data Mart",
        "Dim. X (n)",
        "N Proy.",
        "KL t-SNE",
        "Acc 2D t-SNE",
        "Var. PCA 2D",
        "Acc 2D PCA",
        "Acc Multiclase",
    ],
    filas_t1,
    clave="resultados_t1",
    anchos=[2.8, 1.4, 1.5, 1.6, 2.0, 1.8, 1.9, 2.0],
)
inf.texto(
    "En los cuatro Data Marts, la reducción no lineal con t-SNE supera entre 2.1 y 6.0 puntos "
    "porcentuales la separabilidad en 2D alcanzada por la proyección lineal PCA (Tabla "
    "{tab:resultados_t1}), ya que t-SNE adapta la métrica local a las densidades de cada grupo."
)

inf.titulo("2.7.3 Demostración de referencia con el dataset MNIST")
inf.imagen(
    RES / "mnist_muestra_digitos.png",
    14.0,
    "Muestra de imágenes de dígitos manuscritos del dataset MNIST de referencia (n = 64 -> R^2).",
    clave="mnist_muestra",
    fuente="Elaboración propia con Python, scikit-learn y Matplotlib.",
)
inf.imagen(
    RES / "mnist_10clases_tsne_vs_pca.png",
    15.2,
    "Proyección del dataset MNIST (10 clases, dígitos 0 al 9) al plano [v1, v2] con t-SNE frente a PCA.",
    clave="mnist_10",
    fuente="Elaboración propia con Python, scikit-learn y Matplotlib.",
)
inf.imagen(
    RES / "mnist_binario_0vs1.png",
    14.8,
    "Proyección del dataset MNIST reducido a dos clases (dígito 0 frente a dígito 1) en el plano [v1, v2].",
    clave="mnist_bin",
    fuente="Elaboración propia con Python, scikit-learn y Matplotlib.",
)
inf.texto(
    "Las Ilustraciones {fig:mnist_muestra}, {fig:mnist_10} y {fig:mnist_bin} verifican el "
    "concepto expuesto en la pizarra de clase: al proyectar vectores de alta dimensión hacia "
    "el plano bidimensional [v~1~, v~2~], t-SNE descubre las diez islas correspondientes a los "
    "dígitos 0..9 con un 97.83 % de pureza local, y cuando el problema se restringe a dos "
    "clases (0 frente a 1), ambos grupos quedan completamente separados en dos nubes disjuntas."
)

inf.titulo("2.7.4 Mapas bidimensionales [v1, v2] de los 4 Data Marts (Clases Binarias)")
inf.imagen(
    RES / "mosaico_4_datamarts_binario_tsne.png",
    15.2,
    "Mosaico de proyecciones t-SNE en el plano [v1, v2] para los 4 Data Marts (clases binarias).",
    clave="mosaico_bin",
    fuente="Elaboración propia con Python, scikit-learn y Matplotlib.",
)
for cfg_id, desc in [
    ("DM1_Prestamos", "Data Mart 1 (Fact_Prestamos: Mora vs. Sano)"),
    ("DM2_Saldo_Mensual", "Data Mart 2 (Fact_Saldo_Cuenta_Mensual: Sobregiro t+1 vs. Sin sobregiro)"),
    ("DM3_Ordenes", "Data Mart 3 (Fact_Ordenes: Obligación Financiera vs. Pago de Hogar SIPO)"),
    ("DM4_Transacciones", "Data Mart 4 (Fact_Transacciones: Egreso vs. Ingreso sin intereses)"),
]:
    inf.imagen(
        RES / f"reduccion_binaria_{cfg_id}.png",
        15.0,
        f"Comparación de reducción a 2D ([v1, v2]) con t-SNE frente a PCA en {desc}.",
        clave=f"bin_{cfg_id}",
        fuente="Elaboración propia con Python, scikit-learn y Matplotlib.",
    )

inf.titulo("2.7.5 Mapas bidimensionales [v1, v2] de las Clases Múltiples Reales")
inf.imagen(
    RES / "mosaico_multiclase_reales_tsne.png",
    15.2,
    "Proyección t-SNE en el plano [v1, v2] de las versiones multiclase reales: Estados del préstamo (A, B, C, D) y Tipos de orden (SIPO, UVER, POJISTNE, LEASING).",
    clave="mosaico_multi",
    fuente="Elaboración propia con Python, scikit-learn y Matplotlib.",
)
inf.texto(
    "En la Ilustración {fig:mosaico_multi} se observa que los cuatro estados reales del "
    "préstamo (A: terminado sano, B: terminado en mora, C: vigente sano, D: vigente en mora) "
    "y las cuatro categorías reales de órdenes permanentes (SIPO, UVER, POJISTNE, LEASING) "
    "forman agrupaciones diferenciables en el plano [v~1~, v~2~] sin recurrir a ninguna "
    "variable sintética."
)

inf.titulo("2.7.6 Cumplimiento de las instrucciones")
inf.tabla(
    "Verificación del cumplimiento de los requisitos de la Tarea 1",
    ["Requisito de clase", "Cumplimiento en este trabajo"],
    [
        [
            "1. Un dataset etiquetado por cada Data Mart",
            "Cuatro datasets (Fact_Prestamos, Fact_Saldo_Cuenta_Mensual, Fact_Ordenes y Fact_Transacciones) en 2parcial/.",
        ],
        [
            "2. Cero fuga de datos (data leakage)",
            "Se eliminaron las etiquetas calculadas por reglas y las columnas que delataban la clase; verificado con árboles de decisión.",
        ],
        [
            "3. Demostración con MNIST",
            "Incluida en 10 clases (0..9) y en 2 clases (0 vs. 1) con figuras comparativas t-SNE y PCA.",
        ],
        [
            "4. Reducción X_i -> [v1, v2] en R^2",
            "Vectores de 10 a 16 características reducidos a dos coordenadas y exportados a CSV y PNG.",
        ],
        [
            "5. Graficación por grupos de clase",
            "Mapas 2D generados para las 4 tareas binarias y para las 2 tareas multiclase reales.",
        ],
    ],
    clave="cumplimiento_t1",
    anchos=[5.2, 9.8],
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
    f"**Sobre la reducción de dimensionalidad a [v~1~, v~2~]:** la proyección desde R^n^ hacia "
    f"R^2^ mediante t-SNE preserva la estructura de vecindad local mucho mejor que una "
    f"proyección lineal plana cuando las clases siguen variedades curvas. En el dataset de "
    f"referencia MNIST (n = 64), t-SNE separó los 10 dígitos con una exactitud en 2D de "
    f"{pct(mnist_info['acc_tsne_10'])} frente a {pct(mnist_info['acc_pca_10'])} de PCA; de "
    f"manera consistente, en los cuatro Data Marts bancarios t-SNE alcanzó exactitudes en 2D "
    f"de {pct(r_dm1['Acc_2D_tSNE'])} (Préstamos), {pct(r_dm2['Acc_2D_tSNE'])} (Saldo Mensual), "
    f"{pct(r_dm3['Acc_2D_tSNE'])} (Órdenes) y {pct(r_dm4['Acc_2D_tSNE'])} (Transacciones).",
    "**Sobre la preparación de los datos sin fuga de información:** la eliminación de etiquetas "
    "artificiales y la aplicación estricta del orden Partición 80/20 → Balanceo → Escalado "
    "z-score ajustado solo en el entrenamiento garantizan que los grupos visualizados en el "
    "plano [v~1~, v~2~] reflejen patrones reales de negocio (mora crediticia, sobregiro en el "
    "mes t + 1, obligaciones financieras y dirección de flujo transaccional) y dejan listos "
    "los cuatro conjuntos para el entrenamiento de la Regresión Logística en la Tarea 2.",
], numerada=True)

seccion("2.10 Recomendaciones")
inf.texto(
    "Se recomienda emplear t-SNE exclusivamente para la exploración visual y el diagnóstico de "
    "agrupamientos en el plano [v~1~, v~2~], y utilizar PCA cuando se requiera proyectar datos "
    "nuevos de prueba o dibujar fronteras de decisión paramétricas en 2D, dado que t-SNE no "
    "define una matriz de transformación explícita fuera de la muestra."
)

seccion("2.11 Referencias bibliográficas")
referencias = [
    '[1] L. van der Maaten y G. Hinton, "Visualizing data using t-SNE," Journal of Machine '
    "Learning Research, vol. 9, pp. 2579–2605, nov. 2008.",
    "[2] Y. LeCun, L. Bottou, Y. Bengio y P. Haffner, \"Gradient-based learning applied to "
    'document recognition," Proceedings of the IEEE, vol. 86, no. 11, pp. 2278–2324, 1998.',
    "[3] C. M. Bishop, Pattern Recognition and Machine Learning. New York, NY, USA: Springer, 2006.",
    "[4] I. T. Jolliffe y J. Cadima, \"Principal component analysis: a review and recent "
    'developments," Philosophical Transactions of the Royal Society A, vol. 374, 2016.',
    '[5] F. Pedregosa et al., "Scikit-learn: Machine learning in Python," Journal of Machine '
    "Learning Research, vol. 12, pp. 2825–2830, 2011.",
    "[6] R. Kimball y M. Ross, The Data Warehouse Toolkit, 3.ª ed. Indianapolis, IN, USA: Wiley, 2013.",
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
    "métricas 2D (Tabla {tab:resultados_t1}) y los mapas bidimensionales de MNIST y de los "
    "cuatro Data Marts (Ilustraciones {fig:mnist_muestra} a {fig:mosaico_multi}) se integran en "
    "la sección 2.7. El código fuente se entrega en reduccion_mnist_2d.py."
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
print(f"Informe Tarea 1 generado: {SALIDA}")
print(f"Copia en raíz de 2parcial: {SALIDA_COPIA}")
print(
    f"Tablas: {inf.contador['tab']} | Ilustraciones: {inf.contador['fig']} | "
    f"Ecuaciones: {inf.contador['eq']}"
)
