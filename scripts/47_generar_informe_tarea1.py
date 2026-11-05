"""
Genera el informe en Word de la Tarea 1 del 2do Parcial:
  - 2parcial/Tarea1_Reduccion_MNIST_2D/Informe_Tarea1_Reduccion_MNIST_2D.docx

Sigue exactamente la plantilla y el formato de Informe_Final_Perceptron.docx
(Times New Roman 12, interlineado 1.5, ecuaciones OMML numeradas, tablas con bordes
y leyendas automáticas, pie de página "Página X de Y").
"""

import copy
import json
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
        "Reducción de dimensionalidad a un plano euclidiano 2D (t-SNE, Isomap y referencia MNIST) "
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
    "plano euclidiano bidimensional [v~1~, v~2~] mediante t-SNE e Isomap, usando todas las "
    "características y graficando un punto por cada observación real coloreado según su "
    "etiqueta verdadera (tanto multiclase de 3 a 4 categorías como binaria) libre de fuga de datos."
)
inf.titulo("Específicos:", antes=4)
inf.lista([
    "Formular matemáticamente la proyección de vectores de características x~i~ en R^n^ (n > 2) "
    "hacia un plano bidimensional x~i~^(1)^ = [v~1~, v~2~] en R^2^ utilizando t-SNE (minimización "
    "de la divergencia de Kullback–Leibler) e Isomap (distancias geodésicas y escalamiento "
    "multidimensional clásico).",
    "Auditar y depurar los cuatro datasets correspondientes a los cuatro Data Marts de hechos "
    "(Fact_Prestamos, Fact_Saldo_Cuenta_Mensual, Fact_Ordenes y Fact_Transacciones), eliminando "
    "toda variable con fuga de datos (data leakage) y estandarizando cada característica con "
    "z-score.",
    "Desarrollar la demostración de referencia sobre el conjunto real de dígitos manuscritos "
    "MNIST (imágenes de 28 × 28 píxeles, n = 784 características hacia [v~1~, v~2~]) tanto con "
    "sus 10 clases (dígitos 0 al 9) como en su versión binaria (0 frente a 1).",
    "Visualizar e interpretar geométricamente los grupos formados en el plano [v~1~, v~2~] para "
    "las cuatro versiones multiclase reales (3 a 4 colores por Data Mart) y las cuatro versiones "
    "binarias, cuantificando la separabilidad mediante la exactitud de un clasificador kNN en 2D "
    "evaluado con validación cruzada de 5 pliegues, comparada siempre con la exactitud de la "
    "clase mayoritaria.",
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
    "Utilizar la técnica de reducción asociada al caso de estudio MNIST (t-SNE, comparada con "
    "Isomap) para disminuir la dimensionalidad de cada vector de características desde R^n^ "
    "hasta un plano euclidiano bidimensional x~i~^(1)^ = [v~1~, v~2~].",
    "Graficar las observaciones proyectadas en el plano [v~1~, v~2~] asignando un color "
    "distinto a cada clase verdadera (un punto por observación) para visualizar la formación de "
    "los grupos.",
    "Aplicar el procedimiento sobre una demostración de referencia con el dataset MNIST real "
    "y sobre los cuatro Data Marts del proyecto bancario (Préstamos, Saldo Mensual, Órdenes "
    "Permanentes y Transacciones), generando los cuatro gráficos multiclase reales (3 a 4 colores "
    "por Data Mart) y los cuatro gráficos binarios.",
    "Garantizar que ninguna característica de entrada X contenga reglas deterministas o "
    "columnas que delaten trivialmente la etiqueta y (cero fuga de datos).",
], numerada=True)

seccion("2.5 Listado de equipos, materiales y recursos")
inf.texto("Listado de equipos y materiales generales empleados en la guía práctica:")
inf.lista([
    "Computador con Python 3 (Windows 11 Pro).",
    "Visual Studio Code (editor y terminal integrada PowerShell).",
    "Bibliotecas NumPy, pandas, Matplotlib y scikit-learn (TSNE, Isomap, kNN y descarga de MNIST desde OpenML).",
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
        ["scikit-learn", versiones["scikit-learn"], "Proyección t-SNE e Isomap, kNN de evaluación y descarga de MNIST (OpenML)."],
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
    "python 2parcial/Tarea1_Reduccion_MNIST_2D/reduccion_mnist_2d.py. La muestra de MNIST, "
    "la inicialización de t-SNE y la validación cruzada utilizan la semilla fija 42."
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
    "vecindad local (t-SNE) o las distancias medidas a lo largo de la variedad de los datos "
    "(Isomap)."
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
    "varía entre 10 y 15 variables, y en las imágenes de MNIST n = 784), no es posible visualizar "
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
inf.titulo("Reducción no lineal mediante Isomap (Isometric Mapping)")
inf.texto(
    "Isomap, propuesto por Tenenbaum, de Silva y Langford [7], parte de la idea de que los "
    "datos viven sobre una superficie curva (variedad) dentro de R^n^, y que la distancia "
    "relevante entre dos observaciones no es la línea recta sino el camino que recorre esa "
    "superficie. Para estimarla, conecta cada observación con sus k vecinos más cercanos "
    "(k = 20 en los Data Marts y k = 10 en MNIST) y calcula la **distancia geodésica** "
    "d~G~(x~i~, x~j~) como el camino más corto dentro de ese grafo (Ecuación ({eq:geodesica})):"
)
inf.ecuacion(
    sub(r("d"), r("G")) + delim(sub(r("x"), r("i")) + r(", ") + sub(r("x"), r("j"))) + r("=") +
    tx("min") + suma(r("(a,b)∈camino(i→j)"), r(""),
                     delim(sub(r("x"), r("a")) + r("−") + sub(r("x"), r("b")), "‖", "‖")),
    clave="geodesica",
)
inf.texto(
    "Luego aplica escalamiento multidimensional clásico: con la matriz D~G~^(2)^ de distancias "
    "geodésicas al cuadrado y la matriz de centrado J = I − (1/N)11^T^, obtiene "
    "B = −½ J D~G~^(2)^ J y toma sus dos mayores valores propios λ~1~ ≥ λ~2~ con sus vectores "
    "propios u~1~ y u~2~. Las coordenadas de cada observación en el plano son "
    "(Ecuación ({eq:isomap})):"
)
inf.ecuacion(
    delim(sub(r("v"), r("i1")) + r(", ") + sub(r("v"), r("i2")), "[", "]") + r("=") +
    delim(raiz(sub(r("λ"), r("1"))) + sub(r("u"), r("1i")) + r(", ") +
          raiz(sub(r("λ"), r("2"))) + sub(r("u"), r("2i")), "[", "]"),
    clave="isomap",
)
inf.texto(
    "A diferencia de t-SNE, que solo cuida que los vecinos cercanos sigan cerca, Isomap intenta "
    "conservar también las distancias grandes, por lo que su gráfica refleja mejor la forma "
    "global de los datos. Ninguno de los dos se usa para clasificar: solo sirven para ver los "
    "grupos."
)

# Actividad 2
actividad("Actividad 2. Depuración y preparación de los 4 Data Marts sin fuga de datos (25 min)")
inf.titulo("Objetivo de la actividad", antes=2)
inf.texto(
    "Construir un dataset limpio y etiquetado por cada uno de los cuatro Data Marts de hechos "
    "del modelo dimensional DM_Financial_Kimball_v2, garantizando que las variables predictoras "
    "X no contengan reglas derivadas ni columnas que filtren la etiqueta verdadera y."
)
inf.titulo("Corrección de fuga de datos (data leakage) y clases reales en los 4 Data Marts")
inf.texto(
    "Antes de proyectar o entrenar clasificadores, se verificó que ninguna etiqueta fuera "
    "calculada como fórmula determinista de las propias columnas de X. Cada uno de los cuatro "
    "Data Marts conserva tanto su **etiqueta multiclase real** (de 3 o 4 categorías para la "
    "visualización de grupos en la Tarea 1) como su **etiqueta binaria** (para la Regresión "
    "Logística de la Tarea 2), según se resume en la Tabla {tab:datamarts}:"
)
inf.lista([
    "**Data Mart 1 — Préstamos (Fact_Prestamos, N = 682, n = 14):** en su versión **multiclase "
    "real (4 colores)** distingue los cuatro estados del crédito (A: terminado sano, 203; "
    "B: terminado en mora, 31; C: vigente sano, 403; D: vigente en mora, 45). En su versión "
    "binaria agrupa Mora (B, D: 76) frente a Sano (A, C: 606). Se excluyeron "
    "meses_transcurridos_al_corte y saldo_pendiente_estimado porque se miden al corte de 1998 "
    "y separan por sí solas los contratos terminados de los vigentes.",
    "**Data Mart 2 — Saldo Mensual (Fact_Saldo_Cuenta_Mensual, N = 5 000, n = 15):** sobre los "
    "cierres mensuales que cuentan con mes siguiente observado, emplea únicamente las 15 "
    "variables medidas hasta el cierre del mes actual t para analizar el estado de liquidez en "
    "el mes siguiente (t + 1). En su versión **multiclase (3 colores)** distingue: "
    "1 = Saldo estable o creciente en t + 1, 2 = Caída de saldo sin sobregiro en t + 1, y "
    "3 = En sobregiro en t + 1 (708 casos). Estas tres clases no las registra el banco: las "
    "definió el equipo comparando el saldo observado al cierre de t + 1 con el de t, por lo que "
    "son un resultado real del mes siguiente, pero no una categoría bancaria. En su versión "
    "binaria separa Sobregiro en t + 1 (708) frente a Sin sobregiro en t + 1 (4 292). El CSV "
    "guarda los 708 positivos y 4 292 negativos al azar (N = 5 000); esa proporción de 14 % es "
    "una muestra de trabajo, porque en la población real solo el 0.39 % de los meses termina en "
    "sobregiro al mes siguiente. Lo mismo vale para las 3 clases de las gráficas.",
    "**Data Mart 3 — Órdenes Permanentes (Fact_Ordenes, N = 5 092, n = 10):** filtra las órdenes "
    "con símbolo bancario real y usa 10 características de la cuenta, cliente y distrito. En su "
    "versión **multiclase real (4 colores)** distingue las cuatro categorías reales de orden "
    "(SIPO: pago de hogar, 3 502; UVER: préstamo, 717; POJISTNE: seguro, 532; LEASING: "
    "arrendamiento, 341). En su versión binaria agrupa las obligaciones financieras (UVER, "
    "POJISTNE, LEASING: 1 590) frente a pagos de hogar SIPO (3 502).",
    "**Data Mart 4 — Transacciones (Fact_Transacciones, N = 20 000, n = 11):** excluye los "
    "asientos automáticos de intereses y elimina de X el código de operación, el símbolo, el "
    "canal, el banco contraparte y el saldo previo, dejando el monto en valor absoluto sin "
    "signo. En su versión **multiclase real (4 colores)** distingue las cuatro operaciones "
    "bancarias reales: 1 = VKLAD (depósito en efectivo, 7 078), 2 = VYBER (retiro en efectivo "
    "o tarjeta, 6 804), 3 = PREVOD NA UCET (transferencia enviada, 3 196) y 4 = PREVOD Z UCTU "
    "(transferencia recibida, 2 922). En su versión binaria separa Egreso (10 000) frente a "
    "Ingreso (10 000).",
])
inf.tabla(
    "Especificación de los 4 datasets por Data Mart libres de fuga de datos",
    ["Archivo CSV", "Data Mart (Tabla de Hechos)", "Filas CSV", "Dim. X (n)", "Multiclase Real (Tarea 1)", "Clase Binaria (Tarea 2)"],
    [
        [
            "01_dm_prestamos.csv",
            "Fact_Prestamos",
            "682",
            "14",
            "4 estados: A, B, C, D",
            "Mora B,D (76) vs. Sano A,C (606)",
        ],
        [
            "02_dm_saldo_mensual.csv",
            "Fact_Saldo_Cuenta_Mensual",
            "5 000",
            "15",
            "3 estados t+1 (definidos por el equipo): Estable, Caída, Sobregiro",
            "Sobregiro t+1 (708) vs. Normal (4 292)",
        ],
        [
            "03_dm_ordenes.csv",
            "Fact_Ordenes",
            "5 092",
            "10",
            "4 tipos: SIPO, UVER, POJISTNE, LEASING",
            "Obligación (1 590) vs. SIPO (3 502)",
        ],
        [
            "04_dm_transacciones.csv",
            "Fact_Transacciones",
            "20 000",
            "11",
            "4 operaciones: VKLAD, VYBER, PREVOD (×2)",
            "Egreso (10 000) vs. Ingreso (10 000)",
        ],
    ],
    clave="datamarts",
    anchos=[3.2, 3.2, 1.3, 1.2, 3.1, 3.0],
)
inf.titulo("Todas las observaciones, todas las características y escalado z-score")
inf.texto(
    "En esta tarea se grafica **un punto por cada observación real** de cada CSV, usando "
    "**todas sus características**: 682 préstamos, 5 000 cierres mensuales, 5 092 órdenes y "
    "20 000 transacciones. No se balancea ni se muestrea, porque el objetivo es ver cómo se "
    "distribuyen realmente las clases; por eso la leyenda de cada gráfica muestra el conteo "
    "real de cada clase. El balanceo y la partición 80/20 solo se aplican al entrenar el "
    "clasificador de la Tarea 2."
)
inf.texto(
    "Para que variables expresadas en decenas de miles de coronas checas (como población o "
    "monto del préstamo) no dominen la distancia euclidiana frente a variables binarias o "
    "tasas, cada característica se estandariza con su media μ~j~ y su desviación estándar "
    "σ~j~ (Ecuación ({eq:zscore})):"
)
inf.ecuacion(
    sub(acento(r("x"), "̃"), r("ij")) + r("=") +
    frac(sub(r("x"), r("ij")) + r("−") + sub(r("μ"), r("j")), sub(r("σ"), r("j"))),
    clave="zscore",
)

# Actividad 3
actividad("Actividad 3. Demostración de referencia con el dataset MNIST (25 min)")
inf.titulo("Objetivo de la actividad", antes=2)
inf.texto(
    "Ejecutar la reducción de dimensionalidad a [v~1~, v~2~] sobre el dataset clásico de "
    "dígitos manuscritos MNIST citado en la pizarra de clase, comparando la capacidad de t-SNE "
    "e Isomap para separar tanto las 10 clases de dígitos (0 al 9) como el caso binario (0 vs. 1)."
)
inf.titulo("Desarrollo sobre MNIST")
inf.texto(
    f"Se descargó el conjunto MNIST original desde OpenML (mnist_784 [2]), que contiene "
    f"{miles(mnist_info['N_mnist_completo'])} imágenes de dígitos manuscritos de 28 × 28 "
    f"píxeles; cada imagen se aplana en un vector de n = {mnist_info['n_features']} intensidades "
    f"en escala de grises, divididas para 255 para dejarlas en [0, 1]. Como t-SNE calcula "
    f"distancias entre todos los pares de puntos, se tomó una muestra estratificada de "
    f"{miles(mnist_info['N_total'])} imágenes (300 por dígito). Esa matriz se redujo desde "
    f"R^784^ hacia R^2^ (x~i~^(1)^ = [v~1~, v~2~]) con t-SNE (perplejidad 30) y con Isomap "
    f"(k = 10 vecinos). En las 10 clases, t-SNE alcanzó una divergencia KL = "
    f"{num(mnist_info['kl_10'], 4)} y agrupó los 10 dígitos con una exactitud kNN en 2D "
    f"(validación cruzada de 5 pliegues) de **{pct(mnist_info['acc_tsne_10'])}**, frente a "
    f"**{pct(mnist_info['acc_isomap_10'])}** de Isomap y al 10 % que se obtendría al azar con "
    f"10 clases equilibradas. Al restringir el conjunto a dos clases (dígito 0 frente a "
    f"dígito 1, N = {mnist_info['N_bin']}), t-SNE logró **{pct(mnist_info['acc_tsne_bin'])}** "
    f"e Isomap **{pct(mnist_info['acc_isomap_bin'])}** en 2D."
)

# Actividad 4
actividad("Actividad 4. Reducción a 2D y graficación en los 4 Data Marts (30 min)")
inf.titulo("Objetivo de la actividad", antes=2)
inf.texto(
    "Proyectar cada uno de los cuatro Data Marts bancarios hacia el plano euclidiano "
    "[v~1~, v~2~] y graficar los grupos coloreados por su clase verdadera (tanto en sus 3 a 4 "
    "clases reales como en su versión binaria)."
)
inf.titulo("Aplicación a los cuatro Data Marts")
inf.texto(
    "En cada Data Mart se proyectaron todas las observaciones estandarizadas hacia "
    "[v~1~, v~2~] mediante t-SNE (tasa de aprendizaje automática y perplejidad 30) y mediante "
    "Isomap (k = 20 vecinos; con 10 o 15 vecinos el grafo quedaba dividido en Saldo Mensual y "
    "Órdenes). Las coordenadas de cada observación se guardaron en archivos CSV dentro de "
    "resultados/, y se generaron tanto las **cuatro figuras individuales multiclase** (3 a 4 "
    "colores por Data Mart, comparando t-SNE frente a Isomap lado a lado) como las **cuatro "
    "figuras individuales binarias** (2 colores) y sus respectivos mosaicos 2 × 2."
)
divididos = [r.Data_Mart for r in tabla_res.itertuples() if r.Componentes_Grafo_Isomap > 1]
if divididos:
    inf.texto(
        f"En {', '.join(divididos)} el grafo de vecinos de Isomap quedó dividido en dos grupos "
        f"aun con k = 20. Isomap los une por el par de puntos más cercano y, por eso, uno de los "
        f"grupos aparece en su gráfica como una franja alargada y separada del resto. Esa franja "
        f"es un efecto del método y no indica una clase distinta."
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
    "La separabilidad en el plano se midió con un clasificador kNN (k = 5) evaluado con "
    "validación cruzada estratificada de 5 pliegues: cada punto se clasifica con vecinos de "
    "otros pliegues, de modo que no se evalúa sobre los mismos puntos con los que se ajustó. "
    "Cada exactitud se compara con la de la clase mayoritaria, que es lo que se obtendría "
    "respondiendo siempre la clase más frecuente."
)
inf.texto(
    f"En la versión **multiclase** (3 a 4 colores por Data Mart), t-SNE logra una "
    f"exactitud 2D de **{pct(r_dm1['Acc_Multiclase_tSNE'])}** en Préstamos (4 estados A, B, C, D, "
    f"frente a {pct(r_dm1['Acc_Mayoritaria_Multiclase'])} de la clase mayoritaria), "
    f"**{pct(r_dm2['Acc_Multiclase_tSNE'])}** en Saldo Mensual (3 estados en t + 1, frente a "
    f"{pct(r_dm2['Acc_Mayoritaria_Multiclase'])}), **{pct(r_dm3['Acc_Multiclase_tSNE'])}** en "
    f"Órdenes (4 tipos de orden, frente a {pct(r_dm3['Acc_Mayoritaria_Multiclase'])}) y "
    f"**{pct(r_dm4['Acc_Multiclase_tSNE'])}** en Transacciones (4 tipos de operación bancaria, "
    f"frente a {pct(r_dm4['Acc_Mayoritaria_Multiclase'])}). En la versión **binaria**, "
    f"**Fact_Saldo_Cuenta_Mensual** alcanza **{pct(r_dm2['Acc_2D_tSNE'])}** con t-SNE y "
    f"**{pct(r_dm2['Acc_2D_Isomap'])}** con Isomap; **Fact_Ordenes** logra "
    f"**{pct(r_dm3['Acc_2D_tSNE'])}** y **Fact_Transacciones** **{pct(r_dm4['Acc_2D_tSNE'])}**, "
    f"mientras que en **Fact_Prestamos** ({pct(r_dm1['Acc_2D_tSNE'])}) los 76 créditos en mora "
    f"quedan mezclados con los sanos en el plano, anticipando la dificultad de este Data Mart "
    f"en la Tarea 2."
)
sin_separacion = [
    nom for nom, r in [("Préstamos", r_dm1), ("Saldo Mensual", r_dm2), ("Órdenes", r_dm3), ("Transacciones", r_dm4)]
    if max(r["Acc_Multiclase_tSNE"], r["Acc_Multiclase_Isomap"]) <= r["Acc_Mayoritaria_Multiclase"]
]
if sin_separacion:
    inf.texto(
        f"En la versión multiclase de {', '.join(sin_separacion)}, ni t-SNE ni Isomap superan la "
        f"exactitud de responder siempre la clase más frecuente: en el plano no se forman grupos "
        f"propios por tipo, sino que las clases quedan mezcladas. En Órdenes esto se explica porque "
        f"los pagos de hogar (SIPO) son el {pct(r_dm3['Acc_Mayoritaria_Multiclase'])} de las órdenes "
        f"y se reparten por todo el plano."
    )
inf.texto(
    f"¿Por qué Saldo Mensual se separa tan bien en la versión binaria? Porque el sobregiro tiende "
    f"a persistir: 388 de los 708 meses que terminan en sobregiro en t + 1 ya estaban en "
    f"sobregiro en el mes t, y esas cuentas forman zonas propias en el plano. En Préstamos, en "
    f"cambio, los cuatro estados A, B, C y D se mezclan ({pct(r_dm1['Acc_Multiclase_tSNE'])} con "
    f"t-SNE frente a {pct(r_dm1['Acc_Mayoritaria_Multiclase'])} del estado más frecuente): las "
    f"variables que separaban los contratos terminados de los vigentes se midieron al corte de "
    f"1998 y se retiraron por ser posteriores al otorgamiento, de modo que con la información "
    f"disponible al otorgar el crédito los estados no forman grupos propios."
)

# ----------------------------------------------------------------------------
# 2.7 Resultados obtenidos
# ----------------------------------------------------------------------------
seccion("2.7 Resultados obtenidos")
inf.texto(
    "Los resultados se obtuvieron al ejecutar python 2parcial/Tarea1_Reduccion_MNIST_2D/"
    "reduccion_mnist_2d.py desde la raíz del repositorio."
)

inf.titulo("2.7.1 Ejecución del programa")
if capturas:
    inf.texto(
        f"La salida en consola de la ejecución se presenta en las Ilustraciones {{fig:cap1}} a "
        f"{{fig:cap{len(capturas)}}}; el script finalizó sin errores."
    )
    for k, ruta in enumerate(capturas, 1):
        inf.imagen(
            ruta,
            15.5,
            f"Salida en consola de reduccion_mnist_2d.py (parte {k} de {len(capturas)}).",
            clave=f"cap{k}",
            fuente="Salida de consola registrada por el propio script durante la ejecución.",
        )

inf.titulo("2.7.2 Tabla consolidada de resultados de reducción a 2D")
filas_t1 = []
for row in tabla_res.itertuples():
    multi_str = f"{pct(row.Acc_Multiclase_tSNE, 1)} / {pct(row.Acc_Multiclase_Isomap, 1)} ({int(row.Num_Clases_Multi)} clases)"
    filas_t1.append([
        row.Data_Mart,
        str(row.n_Caracteristicas),
        miles(row.N_Observaciones),
        num(row.KL_tSNE, 3),
        pct(row.Acc_2D_tSNE, 2),
        pct(row.Acc_2D_Isomap, 2),
        pct(row.Acc_Clase_Mayoritaria, 1),
        multi_str,
    ])
inf.tabla(
    "Métricas de reducción de dimensionalidad a R^2 ([v1, v2]) en los 4 Data Marts",
    [
        "Data Mart",
        "Dim. X (n)",
        "N (todas)",
        "KL t-SNE",
        "Acc 2D Bin. t-SNE",
        "Acc 2D Bin. Isomap",
        "Clase mayor. Bin.",
        "Multiclase t-SNE / Isomap",
    ],
    filas_t1,
    clave="resultados_t1",
    anchos=[2.6, 1.1, 1.4, 1.3, 1.7, 1.7, 1.6, 3.5],
)
mejoras = [(r.Data_Mart, 100 * (r.Acc_2D_tSNE - r.Acc_2D_Isomap)) for r in tabla_res.itertuples()]
gana_tsne = [d for d, m in mejoras if m > 0]
gana_tsne_multi = [r.Data_Mart for r in tabla_res.itertuples() if r.Acc_Multiclase_tSNE > r.Acc_Multiclase_Isomap]
inf.texto(
    f"t-SNE separa mejor las clases que Isomap en {len(gana_tsne)} de los 4 Data Marts en la "
    f"versión binaria y en {len(gana_tsne_multi)} de los 4 en la versión multiclase "
    f"(Tabla {{tab:resultados_t1}}), "
    f"porque se concentra en mantener juntos a los vecinos cercanos, mientras que Isomap "
    f"prioriza la forma global de los datos."
)

inf.titulo("2.7.3 Demostración de referencia con el dataset MNIST")
inf.imagen(
    RES / "mnist_muestra_digitos.png",
    14.0,
    "Muestra de imágenes de dígitos manuscritos del dataset MNIST (28 × 28 píxeles, n = 784 -> R^2).",
    clave="mnist_muestra",
    fuente="Elaboración propia con Python, scikit-learn y Matplotlib.",
)
inf.imagen(
    RES / "mnist_10clases_tsne_vs_isomap.png",
    15.2,
    "Proyección del dataset MNIST (10 clases, dígitos 0 al 9) al plano [v1, v2] con t-SNE e Isomap.",
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
    f"Las Ilustraciones {{fig:mnist_muestra}}, {{fig:mnist_10}} y {{fig:mnist_bin}} verifican "
    f"el concepto expuesto en la pizarra de clase: al proyectar vectores de 784 píxeles hacia "
    f"el plano bidimensional [v~1~, v~2~], t-SNE forma diez grupos correspondientes a los "
    f"dígitos 0..9 (exactitud kNN en 2D de {pct(mnist_info['acc_tsne_10'])}), con traslapes "
    f"entre dígitos de trazo parecido; cuando el problema se restringe a dos clases (0 frente "
    f"a 1), ambos grupos quedan separados en dos nubes disjuntas."
)

inf.titulo("2.7.4 Mapas bidimensionales [v1, v2] de los 4 Data Marts con Clases Múltiples Reales (3 y 4 colores)")
inf.imagen(
    RES / "mosaico_multiclase_reales_tsne.png",
    15.2,
    "Mosaico de proyecciones t-SNE en el plano [v1, v2] para los 4 Data Marts con sus clases múltiples reales (3 a 4 colores por Data Mart).",
    clave="mosaico_multi",
    fuente="Elaboración propia con Python, scikit-learn y Matplotlib.",
)
for cfg_id, desc in [
    ("DM1_Prestamos", "Data Mart 1 (Fact_Prestamos: 4 estados reales A, B, C, D)"),
    ("DM2_Saldo_Mensual", "Data Mart 2 (Fact_Saldo_Cuenta_Mensual: 3 estados de liquidez en t+1)"),
    ("DM3_Ordenes", "Data Mart 3 (Fact_Ordenes: 4 tipos reales SIPO, UVER, POJISTNE, LEASING)"),
    ("DM4_Transacciones", "Data Mart 4 (Fact_Transacciones: 4 tipos de operación VKLAD, VYBER, PREVOD NA UCET, PREVOD Z UCTU)"),
]:
    inf.imagen(
        RES / f"reduccion_multiclase_{cfg_id}.png",
        15.0,
        f"Dispersión v1 contra v2 con t-SNE e Isomap, un color por clase real y un punto por observación, en {desc}.",
        clave=f"multi_{cfg_id}",
        fuente="Elaboración propia con Python, scikit-learn y Matplotlib.",
    )

inf.titulo("2.7.5 Mapas bidimensionales [v1, v2] de los 4 Data Marts con Clases Binarias (2 colores, puente hacia la Tarea 2)")
inf.imagen(
    RES / "mosaico_4_datamarts_binario_tsne.png",
    15.2,
    "Mosaico de proyecciones t-SNE en el plano [v1, v2] para los 4 Data Marts (clases binarias de la Tarea 2).",
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
        f"Dispersión v1 contra v2 con t-SNE e Isomap (clases binarias), un punto por observación real, en {desc}.",
        clave=f"bin_{cfg_id}",
        fuente="Elaboración propia con Python, scikit-learn y Matplotlib.",
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
            "Se eliminaron las etiquetas calculadas por reglas, las columnas que delataban la clase y las medidas después del evento (meses transcurridos y saldo pendiente en Préstamos).",
        ],
        [
            "3. Demostración con MNIST",
            "MNIST real de OpenML (muestra de 3 000 imágenes de 28 × 28) en 10 clases (0..9) y en 2 clases (0 vs. 1), con figuras t-SNE e Isomap.",
        ],
        [
            "4. Reducción X_i -> [v1, v2] en R^2",
            "Todas las características (10 a 15) y todas las observaciones de cada dataset reducidas a dos coordenadas y exportadas a CSV y PNG.",
        ],
        [
            "5. Graficación por grupos de clase (multiclase y binaria)",
            "4 figuras individuales multiclase (3 a 4 colores por Data Mart, t-SNE vs. Isomap) y 4 figuras individuales binarias (2 colores), más sus mosaicos.",
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
    f"R^2^ mediante t-SNE preserva la estructura de vecindad local, mientras que Isomap "
    f"conserva mejor la forma global. En el dataset de referencia MNIST (n = 784), t-SNE "
    f"separó los 10 dígitos con una exactitud en 2D de {pct(mnist_info['acc_tsne_10'])} frente "
    f"a {pct(mnist_info['acc_isomap_10'])} de Isomap. En los cuatro Data Marts bancarios con "
    f"clases múltiples reales (3 a 4 colores), t-SNE alcanzó {pct(r_dm1['Acc_Multiclase_tSNE'])} "
    f"en Préstamos, {pct(r_dm2['Acc_Multiclase_tSNE'])} en Saldo Mensual, "
    f"{pct(r_dm3['Acc_Multiclase_tSNE'])} en Órdenes y {pct(r_dm4['Acc_Multiclase_tSNE'])} en "
    f"Transacciones.",
    "**Sobre la preparación de los datos sin fuga de información:** la eliminación de etiquetas "
    "artificiales y de variables medidas después del evento, y la graficación de todas las "
    "observaciones reales con todas sus características, garantizan que los grupos visualizados en el "
    "plano [v~1~, v~2~] reflejen patrones reales de negocio (estados del crédito, liquidez "
    "futura en el mes t + 1, tipos de orden permanente y tipos de operación transaccional) y "
    "dejan listos los cuatro conjuntos para el entrenamiento de la Regresión Logística en la Tarea 2.",
], numerada=True)

seccion("2.10 Recomendaciones")
inf.texto(
    "Se recomienda emplear t-SNE exclusivamente para la exploración visual y el diagnóstico de "
    "agrupamientos en el plano [v~1~, v~2~], y complementarlo con Isomap para revisar la forma "
    "global de los datos. Cuando se requiera proyectar datos nuevos de prueba o dibujar una "
    "frontera de decisión en 2D (Tarea 2) conviene un método lineal como PCA, porque t-SNE no "
    "define una transformación aplicable a observaciones nuevas."
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
    '[7] J. B. Tenenbaum, V. de Silva y J. C. Langford, "A global geometric framework for '
    'nonlinear dimensionality reduction," Science, vol. 290, no. 5500, pp. 2319–2323, 2000.',
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
    "La salida en consola de la ejecución (sección 2.7.1), la tabla consolidada de "
    "métricas 2D (Tabla {tab:resultados_t1}) y los mapas bidimensionales de MNIST y de los "
    "cuatro Data Marts (Ilustraciones {fig:mnist_muestra} a {fig:bin_DM4_Transacciones}) se integran en "
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
print(f"Informe Tarea 1 generado: {SALIDA}")
print(
    f"Tablas: {inf.contador['tab']} | Ilustraciones: {inf.contador['fig']} | "
    f"Ecuaciones: {inf.contador['eq']}"
)
