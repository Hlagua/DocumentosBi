"""
Genera Taller_Perceptron_Bayes/Informe_Final_Perceptron.docx sobre la plantilla de la guía
(scripts/plantillas/Taller_Perceptron_plantilla.docx), con los resultados de
Taller_Perceptron_Bayes/perceptron_bayes.py.

El informe sigue las secciones y actividades de la guía (Hombre = 1, Mujer = −1, seudocódigo
de la diapositiva 4, pesos y sesgo en cero, 200 épocas) y tiene como eje los datos generados
aleatoriamente con p0 = 0.5 y α = 2.5, la elección justificada de la partición y el cálculo de
los errores frente al clasificador de Bayes. El dataset CSV de la guía se usa como verificación.

Uso:
    python Taller_Perceptron_Bayes/perceptron_bayes.py
    python scripts/46_generar_informe_perceptron_bayes.py            (exige las capturas)
    python scripts/46_generar_informe_perceptron_bayes.py --borrador (sin capturas)
"""

import copy
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Cm, Pt

sys.path.insert(0, str(Path(__file__).resolve().parent))
from informe_docx import (FUENTE, Informe, acento, agregar_texto, casos, delim, formato,  # noqa: E402
                          frac, func, func_lim, fuente_run, pie_pagina_numerado, poner_carrera,
                          r, raiz, sub, sup, suma, tx)

RAIZ = Path(__file__).resolve().parents[1]
TALLER = RAIZ / "Taller_Perceptron_Bayes"
RES = TALLER / "resultados"
CAP = TALLER / "capturas"
PLANTILLA = RAIZ / "scripts" / "plantillas" / "Taller_Perceptron_plantilla.docx"
SALIDA = TALLER / "Informe_Final_Perceptron.docx"
BORRADOR = "--borrador" in sys.argv

sys.path.insert(0, str(TALLER))
import perceptron_bayes as pb  # noqa: E402

# ----------------------------------------------------------------------------
# Resultados del experimento
# ----------------------------------------------------------------------------
tabla = pd.read_csv(RES / "tabla_resultados.csv", encoding="utf-8-sig")
gen = tabla[tabla["Datos"].str.startswith("Datos generados")].iloc[0]
csv = tabla[tabla["Datos"] == "Dataset CSV"].iloc[0]
barrido = pd.read_csv(RES / "barrido_alpha.csv", encoding="utf-8-sig")
hist_gen = pd.read_csv(RES / "historial_generado.csv", encoding="utf-8-sig")
hist_iter_gen = pd.read_csv(RES / "historial_iteraciones_generado.csv", encoding="utf-8-sig")
mc_gen = pd.read_csv(RES / "matriz_confusion_generado.csv", index_col=0, encoding="utf-8-sig")
mc_csv = pd.read_csv(RES / "matriz_confusion_csv.csv", index_col=0, encoding="utf-8-sig")
comp = pd.read_csv(RES / "comparacion_particiones.csv", encoding="utf-8-sig",
                   float_precision="round_trip")
df_csv = pd.read_csv(pb.ARCHIVO_CSV, encoding="utf-8-sig")
df_gen = pd.read_csv(pb.ARCHIVO_GENERADO, encoding="utf-8-sig")
capturas = sorted(CAP.glob("vscode_ejecucion_*.png"))
if not capturas and not BORRADOR:
    raise SystemExit(f"Faltan las capturas en {CAP}")

A = f"{pb.ALPHA:g}"                                   # α como texto
EB = float(gen["Error_Bayes_teorico"])                # error de Bayes teórico (datos generados)
TR, VA, TE = pb.PARTICION
DIV = pb.nombre_division(pb.PARTICION)
M_MIN = 10 / EB                                       # prueba mínima (aproximación normal)
M_META = 1.96 ** 2 * (1 - EB) / (0.1 ** 2 * EB)       # prueba para un margen del 10 % del error
DIVISIONES = [(pb.nombre_division(d), d) for d in pb.PARTICIONES_COMPARADAS]
SEMI = {d[2]: 1.96 * np.sqrt(EB * (1 - EB) / (pb.N_GENERADO * d[2])) for _, d in DIVISIONES}
REL = {te: 100 * v / EB for te, v in SEMI.items()}

w_gen = gen[["w1", "w2", "w3"]].to_numpy(dtype=float)
wb = pb.ALPHA * np.ones(3) / np.sqrt(3)
angulo = float(np.degrees(np.arccos(w_gen @ wb / (np.linalg.norm(w_gen) * np.linalg.norm(wb)))))
act_media = float(hist_gen["Actualizaciones"].mean())
actualizaciones_totales = int(hist_gen["Actualizaciones"].sum())
iteraciones_totales = int(gen["Epocas"] * gen["Entrenamiento"])
PICO_AZUL = float(hist_iter_gen.loc[
    (hist_iter_gen["Iteracion"] > 0) &
    (hist_iter_gen["Iteracion"] <= pb.EPOCAS_FIGURA2 * gen["Entrenamiento"]),
    "Error_entrenamiento"].max())
VP, FN = mc_gen.iloc[0]
FP, VN = mc_gen.iloc[1]
CONV_CSV = int(csv["Epoca_convergencia"])
importancia = np.abs(w_gen) / np.abs(w_gen).sum()
versiones = {"Python": sys.version.split()[0], "NumPy": np.__version__, "pandas": pd.__version__,
             "Matplotlib": matplotlib.__version__}


def partes_de(df):
    return pb.particionar(*pb.cargar(df), pb.PARTICION, pb.SEMILLA)


def conteo_por_clase(df):
    return {k: (int((y == 1).sum()), int((y == -1).sum())) for k, (_, y) in partes_de(df).items()}


def primeras_correcciones(df):
    """Repite la primera época con la misma semilla para documentar las primeras correcciones."""
    p = partes_de(df)
    (X_tr, y_tr), (X_va, y_va) = p["entrenamiento"], p["validacion"]
    _, hist, _ = pb.entrenar_perceptron(X_tr, y_tr, X_va, y_va, 1, pb.SEMILLA, registrar=True)
    return hist.attrs["primeros_ajustes"]


conteo_csv, conteo_gen = conteo_por_clase(df_csv), conteo_por_clase(df_gen)

# Diferencia entre el error de prueba y el de entrenamiento
GAP = float(gen["E_out"] - gen["E_in"])
E_MEDIO = float((gen["E_in"] + gen["E_out"]) / 2)
SE_DIF = float(np.sqrt(E_MEDIO * (1 - E_MEDIO) * (1 / gen["Entrenamiento"] + 1 / gen["Prueba"])))
D_VC, DELTA = 4, 0.05
COTA_VC = float(np.sqrt(8 / gen["Entrenamiento"] *
                        np.log(4 * ((2 * gen["Entrenamiento"]) ** D_VC + 1) / DELTA)))
HOEFF = float(np.sqrt(np.log(2 / DELTA) / (2 * gen["Prueba"])))
SE_BAYES = float(np.sqrt(EB * (1 - EB) / gen["Prueba"]))
SE_BARRIDO = [float(np.sqrt(max((b["E_in"] + b["E_out"]) / 2, 1e-4) *
                            (1 - (b["E_in"] + b["E_out"]) / 2) *
                            (1 / b["Entrenamiento"] + 1 / b["Prueba"])))
              for b in barrido.to_dict("records")]
SI_BARRIDO = sum(abs(b["E_out"] - b["E_in"]) <= 1.96 * sd
                 for b, sd in zip(barrido.to_dict("records"), SE_BARRIDO))
traza_gen = primeras_correcciones(df_gen)


def pct(v, d=2):
    return f"{100 * v:.{d}f} %"


def num(v, d=3):
    return f"{v:.{d}f}".replace("-", "−")


def miles(n):
    return f"{int(n):,}".replace(",", " ")


def vec(v, d=3):
    return "(" + ", ".join(num(x, d) for x in v) + ")"


# ----------------------------------------------------------------------------
# Diagrama de la estructura del perceptrón (Actividad 1)
# ----------------------------------------------------------------------------
def dibujar_estructura(ruta):
    plt.rcParams.update({"font.family": FUENTE, "font.size": 13})
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 5)
    ax.axis("off")
    suma_xy = (5.0, 2.8)
    for texto, peso, yy in [("1", "w₀ (sesgo)", 4.3), ("x₁", "w₁", 3.3), ("x₂", "w₂", 2.3),
                            ("x₃", "w₃", 1.3)]:
        ax.add_patch(Circle((1.2, yy), 0.38, fc="white", ec="black", lw=1.5))
        ax.text(1.2, yy, texto, ha="center", va="center")
        ax.add_patch(FancyArrowPatch((1.6, yy), (suma_xy[0] - 0.55, suma_xy[1]),
                                     arrowstyle="-|>", mutation_scale=14, lw=1.3))
        ax.text(3.0, yy + (suma_xy[1] - yy) * 0.35 + 0.12, peso, ha="center", color="#b22222")
    ax.text(0.15, 4.3, "Sesgo", ha="left", va="center", fontsize=11)
    ax.text(0.15, 2.3, "Entradas", ha="left", va="center", fontsize=11, rotation=90)
    ax.add_patch(Circle(suma_xy, 0.55, fc="#f2f2f2", ec="black", lw=1.5))
    ax.text(*suma_xy, "Σ", ha="center", va="center", fontsize=22)
    ax.text(suma_xy[0], suma_xy[1] - 0.95, "f(x) = w₀ + w₁x₁ + w₂x₂ + w₃x₃", ha="center")
    ax.add_patch(FancyArrowPatch((5.55, 2.8), (6.5, 2.8), arrowstyle="-|>",
                                 mutation_scale=14, lw=1.3))
    ax.add_patch(FancyBboxPatch((6.5, 2.2), 1.3, 1.2, boxstyle="round,pad=0.05",
                                fc="white", ec="black", lw=1.5))
    ax.plot([6.7, 7.15, 7.15, 7.6], [2.45, 2.45, 3.15, 3.15], color="black", lw=2)
    ax.text(7.15, 1.85, "Escalón", ha="center")
    ax.add_patch(FancyArrowPatch((7.85, 2.8), (8.7, 2.8), arrowstyle="-|>",
                                 mutation_scale=14, lw=1.3))
    ax.text(8.8, 3.1, "ŷ = +1  Hombre", va="center")
    ax.text(8.8, 2.5, "ŷ = −1  Mujer", va="center")
    fig.tight_layout()
    fig.savefig(ruta, dpi=200)
    plt.close(fig)


dibujar_estructura(RES / "estructura_perceptron.png")

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
    ("Tema:", "Desarrollo y entrenamiento de un perceptrón para clasificación binaria: datos "
              "aleatorios, partición de los datos y comparación con el clasificador de Bayes"),
    ("Unidad de Organización Curricular:", "Profesional"),
    ("Nivel y Paralelo:", 'Sexto semestre - Paralelo: "A"'),
    ("Alumnos participantes:", "Cobos Taco Alison Marcela"),
    ("", "Lagua Flores Henry Daniel"),
    ("", ""),
    ("Asignatura:", "Inteligencia de Negocios"),
    ("Docente:", "Ing. Rubén Nogales Portero, Ph.D."),
]
lineas = [buscar("Tema:"), buscar("Unidad de Organización"), buscar("Nivel y Paralelo:"),
          buscar("Alumnos participantes:")]
lineas += [q for q in doc.paragraphs if q.text.strip().startswith("_____")]
lineas += [buscar("Asignatura:"), buscar("Docente:")]
for q, (etiqueta, valor) in zip(lineas, portada):
    for run in list(q.runs):
        run._element.getparent().remove(run._element)
    if not valor:
        eliminar(q)
        continue
    agregar_texto(q, f"{etiqueta}\t{valor}")
    formato(q, WD_ALIGN_PARAGRAPH.LEFT, sangria=Cm(6.6), interlineado=1.15, despues=2,
            primera=Cm(-6.6))
    q.paragraph_format.tab_stops.add_tab_stop(Cm(6.6))

# Se conserva el formato de los títulos de la plantilla y se reescribe el cuerpo con sus
# mismas secciones.
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


# Símbolos de las ecuaciones
X = r("x")
XT = acento(r("x"), "̃")
XTI = sub(acento(r("x"), "̃"), r("i"))
W = r("w")
MUM, MUH = sub(r("μ"), r("−1")), sub(r("μ"), r("+1"))
SIGMA_INV = sup(r("Σ"), r("−1"))
EIN, EOUT = sub(r("E"), tx("in")), sub(r("E"), tx("out"))
YH = acento(r("y"), "̂")
EBY = sub(r("E"), tx("Bayes"))


def wi(i):
    return sub(r("w"), r(str(i)))


def xi(i):
    return sub(r("x"), r(str(i)))


def indicadora(e):
    return r("I") + delim(e, "[", "]")


# ----------------------------------------------------------------------------
# 2.1 a 2.5
# ----------------------------------------------------------------------------
seccion("2.1 Objetivos")
inf.titulo("General:", antes=2)
inf.texto("Implementar y entrenar un perceptrón de una sola neurona para clasificar dos clases a "
          "partir de tres características numéricas, comprendiendo el papel de las entradas, "
          "pesos, sesgo, función escalón y regla de actualización, y verificar que su "
          "entrenamiento es correcto comparando su error con el del clasificador de Bayes en "
          f"datos generados aleatoriamente (p~0~ = 0.5, α = {A}) con una partición de los datos "
          "elegida y justificada.")
inf.titulo("Específicos:", antes=4)
inf.lista([
    "Identificar en el modelo las entradas x1, x2 y x3, los pesos w1, w2 y w3, el sesgo w0 y la "
    "salida binaria.",
    "Implementar desde cero el algoritmo de entrenamiento del perceptrón usando Python, pandas y "
    "NumPy.",
    f"Generar datos aleatorios de dos clases cuya superposición se controla con α y elegir, con "
    f"criterios matemáticos y experimentales, la división en entrenamiento, validación y prueba "
    f"({DIV}).",
    "Evaluar el desempeño del clasificador mediante exactitud, matriz de confusión y análisis de "
    "la convergencia, y calcular el error de Bayes, el error de entrada E~in~ y el error de "
    "salida E~out~.",
])

seccion("2.2 Modalidad")
inf.texto("Práctica de laboratorio. Trabajo en parejas.")
seccion("2.3 Tiempo de duración")
inf.texto("Presenciales: 120 minutos.", despues=0)
inf.texto("No presenciales: 30 minutos para organizar el informe y anexos.")

seccion("2.4 Instrucciones")
inf.texto("Instrucciones de la guía práctica:")
inf.lista([
    "Utilice el archivo dataset_Perceptron_5000_continuo_menos1_a_1.csv proporcionado por el "
    "docente.",
    "El dataset es sintético y se utiliza únicamente con fines didácticos; sus variables no "
    "representan características reales asociadas a hombres o mujeres.",
    "Codifique la clase como Hombre = 1 y Mujer = −1.",
    "No utilice la clase Perceptron de scikit-learn. El objetivo es programar el entrenamiento "
    "desde cero.",
    "Puede utilizar pandas para leer el archivo y NumPy para las operaciones matemáticas.",
    "Use como valores iniciales: pesos = 0, sesgo = 0 y 200 épocas al menos.",
    "Mantenga el trabajo enfocado en un perceptrón simple: no utilice capas ocultas, "
    "backpropagation ni redes multicapa.",
], numerada=True)
inf.texto("Indicaciones adicionales dadas en clase:")
inf.lista([
    f"Crear datos aleatorios con una distribución de clases p~0~ = 0.5 y α = {A}, donde α "
    f"controla cuánto se superponen las distribuciones, para verificar que el entrenamiento es "
    f"correcto.",
    "El grupo decide la división de los datos en entrenamiento, validación y prueba, y debe "
    f"justificarla. En este trabajo se usó {DIV} (Actividad 2).",
    "Validar la exactitud del modelo con los datos de prueba, que conservan su clase verdadera.",
    "Reportar el error de Bayes, el clasificador, las clases bien definidas, el error del "
    "perceptrón, el error de entrada, el error de salida y la distribución de las clases.",
], numerada=True)

seccion("2.5 Listado de equipos, materiales y recursos")
inf.texto("Listado de equipos y materiales generales empleados en la guía práctica:")
inf.lista(["Computador con Python 3 (Windows 11 Pro).",
           "Visual Studio Code (editor y terminal integrada).",
           "Bibliotecas pandas, NumPy y Matplotlib.",
           "Dataset: dataset_Perceptron_5000_continuo_menos1_a_1.csv y datos generados por el "
           "script.",
           "Documento ANN.pdf, diapositivas 1 a 4."])
inf.texto("TAC (Tecnologías para el Aprendizaje y Conocimiento) empleados en la guía práctica:",
          despues=2)
casillas([(False, "Plataformas educativas"), (False, "Simuladores y laboratorios virtuales"),
          (True, "Aplicaciones educativas"), (True, "Recursos audiovisuales"),
          (False, "Gamificación"), (False, "Inteligencia Artificial")])
inf.texto("Otros (Especifique): Python 3 y Visual Studio Code", sangria=Cm(1.27))
inf.titulo("Software utilizado en la práctica:", antes=8)
inf.texto("El código se escribió y ejecutó en Visual Studio Code, desde su terminal integrada "
          "(PowerShell). La Tabla {tab:software} resume las versiones con las que se obtuvieron "
          "los resultados.")
inf.tabla("Software y bibliotecas utilizados", ["Software", "Versión", "Uso en la práctica"], [
    ["Windows 11 Pro", "10.0.26300", "Sistema operativo del equipo de trabajo."],
    ["Visual Studio Code", "1.142.0", "Edición del script y ejecución en la terminal integrada."],
    ["Python", versiones["Python"], "Lenguaje de programación del experimento."],
    ["NumPy", versiones["NumPy"], "Generación de datos aleatorios y cálculo vectorial."],
    ["pandas", versiones["pandas"], "Lectura y escritura de CSV y tablas de resultados."],
    ["Matplotlib", versiones["Matplotlib"], "Gráficos de clases, historial y barrido de α."],
    ["Microsoft Word", "16.0", "Redacción y maquetación del informe."],
], clave="software", anchos=[3.6, 2.6, 8.8])
inf.titulo("Reproducibilidad de los resultados:", antes=8)
inf.texto("Para obtener exactamente los resultados de este informe basta con tener Python 3 con "
          "NumPy, pandas y Matplotlib, colocar perceptron_bayes.py en la misma carpeta que "
          "dataset_Perceptron_5000_continuo_menos1_a_1.csv y ejecutar python perceptron_bayes.py. "
          "El script genera los datos aleatorios, compara las particiones, entrena, evalúa y "
          "guarda las tablas y las figuras en la carpeta resultados/ en unos 2 minutos. Como todas "
          "las operaciones aleatorias usan la semilla 42, cada ejecución produce los mismos números.")

# ----------------------------------------------------------------------------
# 2.6 Actividades
# ----------------------------------------------------------------------------
seccion("2.6 Actividades por desarrollar")

# Actividad 1 --------------------------------------------------------------
actividad("Actividad 1. Reconocer la estructura del perceptrón (15 min)")
inf.titulo("Objetivo de la actividad", antes=2)
inf.texto("Identificar las entradas, los pesos, el sesgo, la función de activación y la salida "
          "del perceptrón (diapositivas 2 a 4 de ANN.pdf [1]) y conocer el clasificador de Bayes, "
          "que es el punto de referencia para saber si el perceptrón está bien entrenado.")
inf.titulo("Estructura del perceptrón")
inf.texto("El perceptrón, propuesto por Rosenblatt [6], recibe tres entradas, una por cada "
          "característica, y una entrada constante igual a 1 que multiplica al sesgo. Cada "
          "entrada se multiplica por su peso y los productos se suman (Ecuación ({eq:fx})).")
inf.ecuacion(r("f") + delim(X) + r("=") + wi(0) + r("+") +
             suma(r("i=1"), r("3"), sub(r("w"), r("i")) + sub(r("x"), r("i"))) + r("=") +
             wi(0) + r("+") + wi(1) + xi(1) + r("+") + wi(2) + xi(2) + r("+") + wi(3) + xi(3),
             clave="fx")
inf.texto("La guía pide codificar Hombre = 1 y Mujer = −1, así que la función escalón entrega "
          "+1 o −1 (Ecuación ({eq:escalon})). La frontera de decisión es f(x) = 0: un plano en el "
          "espacio (x1, x2, x3).")
inf.ecuacion(YH + r("=") + casos(r("+1") + tx("  (Hombre),   si ") + r("f") + delim(X) + r("≥0"),
                                 r("−1") + tx("  (Mujer),   si ") + r("f") + delim(X) + r("<0")),
             clave="escalon")
inf.texto("Con el vector aumentado x̃ = (1, x1, x2, x3) y w = (w0, w1, w2, w3), la suma ponderada "
          "es un producto punto, f(x) = w·x̃, que en Python se calcula con np.dot.")
inf.imagen(RES / "estructura_perceptron.png", 14.5,
           "Estructura del perceptrón: entradas, pesos, sumador y función escalón.",
           clave="estructura", fuente="Elaboración propia a partir de ANN.pdf [1].")
inf.tabla("Elementos del perceptrón identificados en el modelo",
          ["Elemento", "Símbolo", "En esta práctica"], [
              ["Entradas", "x1, x2, x3", "Caracteristica_1, Caracteristica_2, Caracteristica_3."],
              ["Entrada de sesgo", "x0 = 1", "Constante que multiplica al sesgo."],
              ["Pesos", "w1, w2, w3", "Importancia de cada característica; inician en 0."],
              ["Sesgo", "w0", "Desplaza la frontera; inicia en 0."],
              ["Suma ponderada", "f(x)", "w0 + w1·x1 + w2·x2 + w3·x3."],
              ["Activación", "Escalón", "+1 si f(x) ≥ 0; −1 en otro caso."],
              ["Salida binaria", "ŷ", "+1 = Hombre, −1 = Mujer."],
          ], clave="elementos", anchos=[3.6, 2.6, 8.8])
inf.titulo("Clasificador de Bayes: el mejor resultado posible")
inf.texto("Para saber si el perceptrón aprende bien no basta con ver su exactitud: hay que "
          "compararla con el mejor clasificador posible. El clasificador de Bayes asigna cada "
          "observación a la clase más probable según el teorema de Bayes (Ecuación ({eq:bayes})) "
          "[3], [7]. Ningún clasificador tiene, en promedio, un error menor; ese mínimo es el "
          "**error de Bayes** y depende solo de cuánto se superponen las clases.")
inf.ecuacion(r("P") + delim(r("y=k") + r("∣") + X) + r("=") +
             frac(r("p") + delim(X + r("∣") + r("y=k")) + r("P") + delim(r("y=k")), r("p") + delim(X)) +
             tx(",      ") + r("k∈") + delim(r("−1, +1"), "{", "}"), clave="bayes")
inf.texto("Si cada clase sigue una normal con media μ~k~ y covarianza Σ común, la regla de Bayes "
          "es lineal: un plano con los pesos de la Ecuación ({eq:bayeslineal}), donde p~−1~ = p~0~ "
          "es la probabilidad de la clase Mujer [7]. Por eso tiene sentido compararla con el "
          "perceptrón, que también traza un plano.")
inf.ecuacion(sub(r("w"), tx("B")) + r("=") + SIGMA_INV + delim(MUH + r("−") + MUM) +
             tx(",      ") + sub(r("w"), tx("B0")) + r("=−") + frac(r("1"), r("2")) +
             sup(delim(MUH + r("+") + MUM), r("T")) + sub(r("w"), tx("B")) + r("+") +
             func("ln", frac(sub(r("p"), r("+1")), sub(r("p"), r("−1")))), clave="bayeslineal")
inf.texto("La separación entre las clases se mide con la distancia de Mahalanobis α entre sus "
          "medias (Ecuación ({eq:alpha})): cuántas desviaciones estándar separan un centro del "
          "otro. Con clases equiprobables, el error de Bayes tiene la forma cerrada de la Ecuación "
          "({eq:errorbayes}), donde Φ es la distribución acumulada de la normal estándar [3].")
inf.ecuacion(r("α=") + raiz(sup(delim(MUH + r("−") + MUM), r("T")) + SIGMA_INV +
                            delim(MUH + r("−") + MUM)), clave="alpha")
inf.ecuacion(EBY + r("=Φ") + delim(r("−") + frac(r("α"), r("2"))) + tx(",      con ") +
             sub(r("p"), r("0")) + r("=0.5"), clave="errorbayes")
inf.texto(f"Con α = {A}: E~Bayes~ = Φ(−{num(pb.ALPHA / 2, 2)}) = {pct(EB, 4)}. Aun el mejor "
          f"clasificador se equivoca en unas {100 * EB:.0f} de cada 100 observaciones, porque las "
          f"clases se superponen.")
inf.titulo("Error de entrada y error de salida")
inf.texto("El **error de entrada** E~in~ es la proporción de observaciones de entrenamiento mal "
          "clasificadas (Ecuación ({eq:ein})). El **error de salida** E~out~ es la probabilidad de "
          "equivocarse con datos nuevos; se estima con el conjunto de prueba, que el modelo nunca "
          "vio y que conserva su clase verdadera (Ecuación ({eq:eout})) [4].")
inf.ecuacion(EIN + r("=") + frac(r("1"), r("N")) +
             suma(r("i=1"), r("N"), indicadora(YH + delim(sub(r("x"), r("i"))) + r("≠") +
                                              sub(r("y"), r("i")))), clave="ein")
inf.ecuacion(EOUT + r("=P") + delim(YH + delim(X) + r("≠y")) + r("≈") + frac(r("1"), r("M")) +
             suma(r("i=1"), r("M"), indicadora(YH + delim(sub(r("x"), r("i"))) + r("≠") +
                                              sub(r("y"), r("i")))), clave="eout")
inf.texto("Un entrenamiento correcto cumple dos cosas: E~in~ ≈ E~out~ (el modelo generaliza) y "
          "E~out~ ≈ E~Bayes~ (el modelo llega al mejor resultado posible). Esas son las dos "
          "pruebas con las que se verifica el perceptrón en este informe.")

# Actividad 2 --------------------------------------------------------------
actividad("Actividad 2. Preparar los datos (20 min)")
inf.titulo("Objetivo de la actividad", antes=2)
inf.texto("Generar los datos aleatorios con los que se verifica el entrenamiento, preparar el "
          "dataset de la guía, codificar la clase y elegir la división en entrenamiento, "
          "validación y prueba.")
inf.titulo(f"Datos aleatorios con p~0~ = 0.5 y α = {A}")
inf.texto("El dataset de la guía no sirve por sí solo para verificar el entrenamiento: sus clases "
          f"están tan separadas (α ≈ {num(csv['alpha'], 2)}) que el error de Bayes es prácticamente "
          "cero y cualquier plano entre ellas acierta todo. Para comprobar que el perceptrón "
          "llega al mejor resultado posible hace falta conocer ese resultado de antemano, y eso "
          "solo es posible con datos generados a partir de una distribución conocida.")
inf.texto(f"Se generaron {miles(len(df_gen))} registros aleatorios con la misma estructura del CSV "
          f"(tres características y la columna Clase). Cada clase sigue una normal con covarianza "
          f"identidad y sus centros están sobre la diagonal (1, 1, 1), uno a cada lado del origen "
          f"(Ecuación ({{eq:generacion}})), así que la distancia de Mahalanobis entre ellas es "
          f"exactamente α. La mitad de los registros es de cada clase (p~0~ = 0.5) y se usó la "
          f"semilla 42. El script genera estos datos en cada ejecución y los guarda en "
          f"{pb.ARCHIVO_GENERADO.name}.")
inf.ecuacion(X + r("∣") + delim(r("y=k")) + r("∼") + r("N") + delim(sub(r("μ"), r("k")) + tx(", ") +
             r("I")) + tx(",      ") + MUM + r("=−") + frac(r("α"), r("2")) + r("u") + tx(",   ") +
             MUH + r("=") + frac(r("α"), r("2")) + r("u") + tx(",   ") + r("u=") +
             frac(sup(delim(r("1, 1, 1")), r("T")), raiz(r("3"))), clave="generacion")
inf.texto(f"Con estos parámetros, la Ecuación ({{eq:bayeslineal}}) da los pesos de Bayes "
          f"w~B~ = α·u = {vec(wb)} y w~B0~ = 0: la frontera óptima pasa por el origen. La "
          f"Ilustración {{fig:distgen}} muestra las dos clases proyectadas sobre la dirección que "
          f"las separa: dos campanas centradas en ±{num(pb.ALPHA / 2, 2)} que se superponen "
          f"alrededor del umbral. Las observaciones que caen del lado equivocado forman el "
          f"{pct(EB)} de error de Bayes.")
inf.imagen(RES / "distribucion_generado.png", 14.5,
           "Distribución de las clases de los datos aleatorios sobre la dirección que las separa.",
           clave="distgen", fuente="Elaboración propia con Python y Matplotlib.")
inf.titulo("Dataset de la guía")
inf.texto(f"El archivo dataset_Perceptron_5000_continuo_menos1_a_1.csv se leyó con pandas: "
          f"{miles(len(df_csv))} registros, tres características continuas en [−1, 1], sin valores "
          f"nulos ni filas duplicadas, y 2 500 registros de cada clase. Se usa como segunda "
          f"verificación: con clases separadas, el perceptrón debe converger y no cometer errores.")
inf.titulo("Codificación de la clase")
inf.texto("Siguiendo la instrucción 3, la columna Clase se transformó en la variable objetivo de "
          "la Ecuación ({eq:codificacion}), que coincide con la salida de la función escalón.")
inf.ecuacion(r("y=") + casos(r("+1") + tx(",   si Clase = Hombre"),
                             r("−1") + tx(",   si Clase = Mujer")), clave="codificacion")
inf.titulo("Partición de los datos")
inf.texto(f"Los dos conjuntos se dividieron con una partición estratificada {DIV} (Tabla "
          f"{{tab:particion}}), con la semilla 42:")
inf.lista([
    f"**Entrenamiento ({100 * TR:.0f} %):** el perceptrón ajusta sus pesos; aquí se mide E~in~.",
    f"**Validación ({100 * VA:.0f} %):** al final de cada época se mide el error y se guarda el "
    f"mejor perceptrón, sin usar los datos de prueba.",
    f"**Prueba ({100 * TE:.0f} %):** solo se usa al final, con la clase verdadera, para estimar "
    f"E~out~ y la exactitud.",
])
filas = []
for nombre, conteo in [(f"Datos aleatorios (α = {A})", conteo_gen), ("Dataset CSV", conteo_csv)]:
    for parte, etiqueta in [("entrenamiento", "Entrenamiento"), ("validacion", "Validación"),
                            ("prueba", "Prueba")]:
        h, m = conteo[parte]
        filas.append([nombre if parte == "entrenamiento" else "", etiqueta, miles(h), miles(m),
                      miles(h + m), f"{100 * h / (h + m):.0f} / {100 * m / (h + m):.0f}"])
inf.tabla(f"Partición estratificada {DIV}: observaciones por clase en cada parte",
          ["Conjunto de datos", "Parte", "Hombre (+1)", "Mujer (−1)", "Total", "% Hombre / Mujer"],
          filas, clave="particion", anchos=[3.6, 2.6, 2.1, 2.1, 1.9, 2.7],
          alinear=[WD_ALIGN_PARAGRAPH.LEFT] + [WD_ALIGN_PARAGRAPH.CENTER] * 5)
inf.titulo("Por qué cada parte tiene 50 % de cada clase")
inf.texto(f"La división se aplica por separado a cada clase, así el entrenamiento de los datos "
          f"aleatorios tiene exactamente {miles(conteo_gen['entrenamiento'][0])} observaciones de "
          f"cada clase. Este balance es necesario por tres razones:")
inf.lista([
    "**Evita que el perceptrón se incline hacia una respuesta.** El perceptrón solo corrige con "
    "las observaciones que clasifica mal; si una clase fuera más frecuente, aportaría más "
    "correcciones y el plano se desplazaría hacia la otra.",
    "**Mantiene la regla de Bayes.** En la Ecuación ({eq:bayeslineal}) el término ln(p~+1~/p~−1~) "
    "desplaza la frontera. Con 50/50 vale 0; con 70/30 valdría ln(0.7/0.3) = 0.85 y la frontera se "
    f"correría 0.85/α = {num(np.log(7 / 3) / pb.ALPHA, 2)} desviaciones estándar.",
    "**La exactitud no se infla.** Con prueba balanceada, un clasificador que siempre responde "
    "lo mismo obtiene 50 %, y la exactitud es el promedio de la sensibilidad y la especificidad.",
])
inf.titulo(f"Por qué se eligió {DIV}")
inf.texto("La división se comparó con otras tres (70/15/15, 70/20/10 y 80/10/10). El perceptrón "
          "en tres dimensiones tiene cuatro parámetros (w0 a w3), es decir, una dimensión VC de "
          "d~VC~ = 4, y la regla práctica N ≥ 10·d~VC~ = 40 [4] se cumple con mucha holgura en "
          "cualquiera de ellas (12 000 a 16 000 observaciones de entrenamiento). Agrandar el "
          "entrenamiento, entonces, casi no mejora el modelo; lo que importa es que validación y "
          "prueba sean grandes, porque de ellas dependen la elección del mejor perceptrón y la "
          "medición de su error. Se usaron dos criterios.")
inf.titulo("Criterio 1: precisión del error medido en prueba", antes=4)
inf.texto(f"El intervalo de confianza del error (Ecuación ({{eq:ic}})) usa la aproximación normal "
          f"de la binomial, confiable si se esperan al menos 10 errores [8]; con E~Bayes~ = "
          f"{pct(EB)} eso exige solo M ≥ {M_MIN:.0f}. Se pidió algo más útil: que el margen no "
          f"supere el 10 % del propio error (±{pct(0.1 * EB)}). Al despejar M se obtiene la "
          f"Ecuación ({{eq:mminimo}}).")
inf.ecuacion(r("1.96") + raiz(frac(EBY + delim(r("1−") + EBY), r("M"))) + r("≤0.1·") + EBY +
             tx("   ⟹   ") + r("M≥") +
             frac(sup(r("1.96"), r("2")) + delim(r("1−") + EBY), sup(r("0.1"), r("2")) + EBY),
             clave="mminimo")
inf.texto(f"Con E~Bayes~ = {num(EB, 4)} resulta M ≥ {miles(round(M_META))} observaciones de prueba. "
          f"La Tabla {{tab:divisiones}} aplica este criterio a las cuatro divisiones.")
filas = []
for etiqueta, (tr, va, te) in DIVISIONES:
    m = int(pb.N_GENERADO * te)
    filas.append([etiqueta, miles(m), f"± {pct(SEMI[te])}", f"{REL[te]:.1f} %",
                  "Sí" if m >= M_META else "No"])
inf.tabla(f"Criterio 1: precisión de la medición en prueba (N = {miles(pb.N_GENERADO)}, error de {pct(EB)})",
          ["División", "Observaciones de prueba (M)", "Semiancho IC 95 %", "Margen relativo",
           "¿Cumple la meta?"], filas, clave="divisiones",
          anchos=[2.8, 3.4, 3.0, 3.0, 2.8], alinear=[WD_ALIGN_PARAGRAPH.CENTER] * 5)
inf.texto(f"Solo {DIV} cumple la meta: con {miles(int(pb.N_GENERADO * TE))} observaciones de prueba "
          f"el margen es ±{pct(SEMI[TE])}, el {REL[TE]:.1f} % del error.")
inf.titulo("Criterio 2: comparación experimental", antes=4)
inf.texto(f"Con los mismos datos (p~0~ = 0.5, α = {A}, {miles(pb.N_GENERADO)} registros) se entrenó "
          f"el perceptrón con cada división y {len(pb.SEMILLAS_COMPARACION)} semillas distintas "
          f"({', '.join(map(str, pb.SEMILLAS_COMPARACION))}): "
          f"{len(pb.PARTICIONES_COMPARADAS) * len(pb.SEMILLAS_COMPARACION)} entrenamientos completos "
          f"de 200 épocas. En cada uno se midieron tres diferencias, mejores cuanto más cerca de cero: "
          f"E~out~ − error de Bayes (qué tan lejos queda el perceptrón del mejor clasificador), "
          f"E~out~ − E~val~ (cuánto se engaña la validación al elegir el mejor perceptrón) y "
          f"|E~in~ − E~out~| (si generaliza).")


def p2(v):
    return f"{100 * v:.2f}".replace("-", "−")


filas = [[f["Division"], p2(f["E_in_mean"]), p2(f["Error_validacion_mean"]), p2(f["E_out_mean"]),
          f"{p2(f['Exceso_sobre_Bayes_mean'])} ± {p2(f['Exceso_sobre_Bayes_std'])}",
          f"{p2(f['Optimismo_validacion_mean'])} ± {p2(f['Optimismo_validacion_std'])}",
          p2(f["Diferencia_Ein_Eout_mean"])] for _, f in comp.iterrows()]
inf.tabla(f"Criterio 2: promedio de {len(pb.SEMILLAS_COMPARACION)} entrenamientos por división, "
          f"en % (media ± desviación estándar)",
          ["División", "E~in~", "E~val~", "E~out~", "E~out~ − Bayes", "E~out~ − E~val~",
           "|E~in~ − E~out~|"], filas, clave="comparacion",
          anchos=[1.9, 1.5, 1.5, 1.5, 3.1, 3.1, 2.4], alinear=[WD_ALIGN_PARAGRAPH.CENTER] * 7)
inf.imagen(RES / "comparacion_particiones.png", 14.5,
           "Comparación experimental de las cuatro divisiones (barras: media; líneas: desviación "
           "estándar entre semillas).", clave="comparacion",
           fuente="Elaboración propia con Python y Matplotlib.")
fila = comp.set_index("Division")
mejor_div = fila["Exceso_sobre_Bayes_mean"].idxmin()
if mejor_div != DIV:
    raise SystemExit(f"La división con menor exceso es {mejor_div}, no {DIV}: revisar la elección.")
otra = fila.drop(index=DIV)["Exceso_sobre_Bayes_mean"].idxmin()
inf.texto(f"El E~in~ casi no cambia entre divisiones ({pct(comp['E_in_mean'].min())} a "
          f"{pct(comp['E_in_mean'].max())}): más datos de entrenamiento no mejoran el modelo. Con "
          f"2 000 observaciones de validación (80/10/10) el mejor perceptrón parece "
          f"{pct(fila.loc['80/10/10', 'Optimismo_validacion_mean'])} mejor de lo que es; con 4 000 "
          f"({DIV}) solo {pct(fila.loc[DIV, 'Optimismo_validacion_mean'])}. Y {DIV} es la división "
          f"cuyo perceptrón queda más cerca del error de Bayes: "
          f"{pct(fila.loc[DIV, 'Exceso_sobre_Bayes_mean'])} por encima en promedio, frente a "
          f"{pct(fila.loc[otra, 'Exceso_sobre_Bayes_mean'])} de la siguiente mejor ({otra}).")
inf.texto(f"**Decisión:** se usó {DIV}, la única que cumple el criterio de precisión y la que, en "
          f"los experimentos, deja al perceptrón más cerca del error de Bayes con la validación "
          f"menos optimista. Los {miles(pb.N_GENERADO)} registros generados son suficientes: dejan "
          f"{miles(int(pb.N_GENERADO * TE))} observaciones de prueba, más que las "
          f"{miles(round(M_META))} de la Ecuación ({{eq:mminimo}}). El dataset CSV se dividió igual "
          f"para comparar ambos conjuntos en las mismas condiciones.")
inf.titulo("Parámetros del experimento")
inf.tabla("Parámetros utilizados y su justificación", ["Parámetro", "Valor", "Justificación"], [
    ["Codificación", "+1 / −1", "Instrucción 3: Hombre = 1, Mujer = −1."],
    ["Pesos y sesgo iniciales", "0", "Instrucción 6; punto de partida que no favorece a ninguna clase."],
    ["Épocas", str(pb.EPOCAS), f"Instrucción 6. El mejor perceptrón apareció en la época {int(gen['Mejor_epoca'])}; las demás no lo mejoraron."],
    ["Registros generados", miles(pb.N_GENERADO), f"Dejan {miles(int(pb.N_GENERADO * TE))} de prueba ≥ {miles(round(M_META))} (Ecuación ({{eq:mminimo}}))."],
    ["Probabilidad p~0~", str(pb.P0), "Indicación de clase; clases equiprobables."],
    ["Separación α", A, f"Indicación de clase; error de Bayes de {pct(EB)}."],
    ["Covarianza", "Identidad", "La distancia de Mahalanobis coincide con la euclidiana."],
    ["Partición", DIV, "Estratificada, 50 % de cada clase; criterios 1 y 2 (Tablas {tab:divisiones} y {tab:comparacion})."],
    ["Semilla aleatoria", str(pb.SEMILLA), "Reproduce los datos, la partición y el orden de entrenamiento."],
], clave="parametros", anchos=[3.6, 2.2, 9.2], alinear=[WD_ALIGN_PARAGRAPH.LEFT,
                                                         WD_ALIGN_PARAGRAPH.CENTER,
                                                         WD_ALIGN_PARAGRAPH.LEFT])

# Actividad 3 --------------------------------------------------------------
actividad("Actividad 3. Programar el entrenamiento del perceptrón (40 min)")
inf.titulo("Objetivo de la actividad", antes=2)
inf.texto("Programar desde cero, sin la clase Perceptron de scikit-learn, el seudocódigo de la "
          "diapositiva 4 de ANN.pdf, con pesos y sesgo iniciales en cero y 200 épocas.")
inf.titulo("Seudocódigo y regla de actualización")
inf.texto("El seudocódigo inicializa todos los pesos en cero y recorre los ejemplos: si un ejemplo "
          "está mal clasificado, corrige los pesos. Gracias a la codificación ±1, la condición de "
          "error es la Ecuación ({eq:condicion}): y~i~·f(x~i~) es positivo solo cuando el signo "
          "de f coincide con la clase real.")
inf.ecuacion(sub(r("y"), r("i")) + r("·f") + delim(sub(r("x"), r("i"))) + r("≤0"), clave="condicion")
inf.texto("Cuando se cumple, se aplica la regla de la Ecuación ({eq:actualizacion}); como "
          "x~i0~ = 1, el sesgo también se corrige (w0 ← w0 + y~i~).")
inf.ecuacion(sub(r("w"), r("j")) + r("←") + sub(r("w"), r("j")) + r("+") + sub(r("y"), r("i")) +
             sub(r("x"), r("ij")) + tx(",      ") + r("j=0, 1, 2, 3"), clave="actualizacion")
inf.texto("¿Por qué esta regla corrige el error? Al reemplazar los pesos nuevos en la condición "
          "se obtiene la Ecuación ({eq:mejora}): como ‖x̃~i~‖² > 0, cada corrección aumenta "
          "y~i~·f(x~i~) y empuja el ejemplo hacia el lado correcto de la frontera.")
inf.ecuacion(sub(r("y"), r("i")) + sup(delim(W + r("+") + sub(r("y"), r("i")) + XTI), r("T")) +
             XTI + r("=") + sub(r("y"), r("i")) + sup(W, r("T")) + XTI + r("+") +
             sup(delim(XTI, "‖", "‖"), r("2")), clave="mejora")
inf.texto("La regla no usa tasa de aprendizaje. No hace falta: como los pesos comienzan en cero, "
          "multiplicar todas las correcciones por cualquier η > 0 solo cambia la escala de los "
          "pesos, no el signo de f(x), así que las predicciones serían las mismas.")
inf.tabla("Correspondencia entre el seudocódigo y la implementación",
          ["Paso del seudocódigo", "Implementación en perceptron_bayes.py"], [
              ["2. Inicializar w~j~ = 0", "Pesos w1, w2, w3 y sesgo w0 en cero."],
              ["3. Repetir hasta convergencia", "200 épocas completas (instrucción 6)."],
              ["4. Para cada ejemplo x~i~", "Se recorren los ejemplos de entrenamiento en orden aleatorio."],
              ["5. Si y~i~·f(x~i~) ≤ 0", "Se calcula f(x~i~) con un producto punto y se compara su signo con y~i~."],
              ["6. w~j~ ← w~j~ + y~i~·x~ij~", "Se suma y~i~·x~i~ a los pesos y y~i~ al sesgo."],
          ], clave="pasos", anchos=[5.0, 10.0], alinear=[WD_ALIGN_PARAGRAPH.LEFT] * 2)
inf.titulo("Traza de las primeras correcciones (datos aleatorios)")
filas = []
w0_t, w_t = 0.0, np.zeros(3)
for a in traza_gen:
    w0_n, w_n = a["w0"] + a["y"], a["w"] + a["y"] * a["x"]
    filas.append([str(a["Iteracion"]), vec(a["x"]), f"{a['y']:+d}".replace("-", "−"),
                  num(a["f"]), f"({num(w0_n, 0)}; {vec(w_n)[1:-1]})"])
inf.tabla("Primeras correcciones de pesos en la época 1",
          ["Iteración", "x = (x1, x2, x3)", "y", "f(x) antes", "w después (w0; w1, w2, w3)"],
          filas, clave="traza", anchos=[1.8, 5.2, 0.9, 2.0, 5.1])
t1, t2 = traza_gen[0], traza_gen[1]
w1 = t1["y"] * t1["x"]
inf.texto(f"En la primera iteración todos los pesos valen cero, así que f(x) = 0 y y·f(x) = 0 ≤ 0: "
          f"se cuenta como error y, como y = +1, se suma el ejemplo (w0 = 1, w = {vec(w1)}). En la "
          f"iteración {t2['Iteracion']}, f(x) = 1 + ({num(w1[0])})({num(t2['x'][0])}) + "
          f"({num(w1[1])})({num(t2['x'][1])}) + ({num(w1[2])})({num(t2['x'][2])}) = {num(t2['f'])}; "
          f"el modelo dijo Hombre para una Mujer (y = −1), así que se resta el ejemplo y el sesgo "
          f"vuelve a 0.")
inf.titulo("Mejora: conservar el mejor perceptrón")
conv_txt = "ninguna época" if pd.isna(gen["Epoca_convergencia"]) else f"la época {int(gen['Epoca_convergencia'])}"
inf.texto(f"En los datos aleatorios las clases se superponen, no existe un plano sin errores y el "
          f"perceptrón nunca converge: en {conv_txt} quedó sin errores, y hizo en promedio "
          f"{act_media:.0f} correcciones por época. Cada corrección acierta un ejemplo de la zona de "
          f"traslape pero puede equivocar otros, así que los pesos de la última época no son "
          f"necesariamente buenos. Por eso, al final de cada época se mide el error en validación y "
          f"se guarda el mejor perceptrón (Ecuación ({{eq:pocket}})), la idea del algoritmo "
          f"«pocket» [5]. Es una mejora que no cambia el modelo: sigue siendo un perceptrón simple "
          f"entrenado con la misma regla.")
inf.ecuacion(sup(r("w"), r("∗")) + r("=") +
             func_lim("arg min", r("t=1,…,200"), sub(r("E"), tx("val")) + delim(sub(r("w"), r("t")))),
             clave="pocket")

# Actividad 4 --------------------------------------------------------------
actividad("Actividad 4. Evaluar el clasificador (25 min)")
inf.titulo("Objetivo de la actividad", antes=2)
inf.texto("Medir el desempeño del perceptrón con la exactitud, la matriz de confusión y el "
          "análisis de la convergencia, y verificar el entrenamiento comparándolo con el "
          "clasificador de Bayes.")
inf.titulo("Desarrollo")
inf.texto("Con los pesos del mejor perceptrón se clasificaron los conjuntos de entrenamiento, "
          "validación y prueba. Con la clase positiva Hombre (+1), la matriz de confusión cuenta "
          "VP (Hombres acertados), VN (Mujeres acertadas), FP (Mujeres clasificadas como Hombre) y "
          "FN (Hombres clasificados como Mujer). A partir de ella se calcularon la exactitud "
          "(Ecuación ({eq:exactitud})), la sensibilidad y la especificidad.")
VPt, VNt, FPt, FNt = (tx(s) for s in ("VP", "VN", "FP", "FN"))
inf.ecuacion(tx("Exactitud") + r("=") + frac(VPt + r("+") + VNt, VPt + r("+") + VNt + r("+") + FPt +
                                            r("+") + FNt) + r("=1−") + EOUT, clave="exactitud")
inf.texto("Además se calcularon el error de Bayes teórico (Ecuación ({eq:errorbayes})), el error "
          "de Bayes en la misma muestra de prueba (aplicando la regla de la Ecuación "
          "({eq:bayeslineal})) y el intervalo de confianza del 95 % de E~out~ (Ecuación ({eq:ic})). "
          "Si no hay errores en prueba, se usa la regla del tres: el error real es menor que 3/M "
          "con 95 % de confianza.")
inf.ecuacion(EOUT + r("±1.96") + raiz(frac(EOUT + delim(r("1−") + EOUT), r("M"))) +
             tx(",      si ") + EOUT + r("=0:") + tx("  ") +
             delim(r("0, ") + frac(r("3"), r("M")), "[", "]"), clave="ic")
inf.texto(f"En los datos aleatorios: {VP} VP, {VN} VN, {FP} FP y {FN} FN, es decir, exactitud = "
          f"({VP} + {VN}) / {miles(VP + VN + FP + FN)} = {pct(gen['Accuracy_perceptron'])} y "
          f"E~out~ = {pct(gen['E_out'])}, con un intervalo de [{pct(gen['IC95_inferior'])}, "
          f"{pct(gen['IC95_superior'])}] que contiene al error de Bayes teórico ({pct(EB)}).")
inf.titulo("Análisis de la convergencia")
inf.texto(f"El comportamiento de la convergencia es la verificación más directa del "
          f"entrenamiento. En el dataset CSV, con clases separadas, el perceptrón convergió en la "
          f"época {CONV_CSV} (una época completa sin correcciones), como predice el teorema de "
          f"convergencia [12]. En los datos aleatorios no converge, porque ningún plano separa "
          f"clases que se superponen; lo correcto entonces es que su error se acerque al de Bayes, "
          f"y eso es lo que muestran los resultados de la sección 2.7.")

# Actividad 5 --------------------------------------------------------------
actividad("Actividad 5. Interpretar el resultado (20 min)")
inf.titulo("Objetivo de la actividad", antes=2)
inf.texto("Interpretar los pesos aprendidos, la frontera de decisión y el efecto de la "
          "superposición de las clases.")
inf.titulo("Pesos finales")
inf.texto(f"El mejor perceptrón en los datos aleatorios tiene w0 = {num(gen['w0'], 4)}, w1 = "
          f"{num(gen['w1'], 4)}, w2 = {num(gen['w2'], 4)} y w3 = {num(gen['w3'], 4)}. Los tres "
          f"pesos son positivos y parecidos (importancia relativa de {importancia[0]:.0%}, "
          f"{importancia[1]:.0%} y {importancia[2]:.0%}), igual que los de Bayes, que son iguales "
          f"entre sí porque los datos se generaron con las tres características igual de "
          f"informativas. El ángulo entre ambos vectores de pesos es de {angulo:.1f}° y el sesgo "
          f"es cero: la frontera del perceptrón pasa por el origen, como la óptima. Esa pequeña "
          f"inclinación explica que el perceptrón quede apenas "
          f"{pct(gen['E_out'] - gen['Error_Bayes_prueba'])} por encima de Bayes en prueba.")
inf.texto(f"En el dataset CSV, los pesos son w1 = {num(csv['w1'], 3)}, w2 = {num(csv['w2'], 3)} y "
          f"w3 = {num(csv['w3'], 3)}, con w0 = {num(csv['w0'], 0)}: la frontera "
          f"{num(csv['w1'], 3)}·x1 + {num(csv['w2'], 3)}·x2 + {num(csv['w3'], 3)}·x3 = 0 separa por "
          f"completo las dos clases.")
inf.titulo("Efecto de la superposición (barrido de α)")
b_alpha = dict(zip(barrido["alpha"].round(2), barrido["Error_Bayes_teorico"]))
inf.texto(f"Se repitió el experimento completo para α = "
          f"{', '.join(f'{a:g}' for a in pb.ALPHAS_BARRIDO[:-1])} y {pb.ALPHAS_BARRIDO[-1]:g}. "
          f"α «sobremonta» las distribuciones: con α = 1 las clases se superponen mucho y el error "
          f"de Bayes es {pct(b_alpha[1])}; con α = 6 baja a {pct(b_alpha[6])} y con α = 8 es "
          f"prácticamente 0 %. En todos los casos el error de prueba del perceptrón sigue al de "
          f"Bayes (Tabla {{tab:barrido}} e Ilustración {{fig:barrido}}): el entrenamiento es "
          f"correcto para cualquier grado de superposición.")

# ----------------------------------------------------------------------------
# 2.7 Resultados obtenidos
# ----------------------------------------------------------------------------
seccion("2.7 Resultados obtenidos")
inf.texto("Los resultados se obtuvieron al ejecutar python perceptron_bayes.py en la terminal "
          "integrada de Visual Studio Code. Todas las tablas y figuras se generaron "
          "automáticamente en la carpeta resultados/. El proceso que sigue el programa, en orden, "
          "es el siguiente:")
inf.lista([
    f"**Generar los datos aleatorios:** {miles(pb.N_GENERADO)} registros de dos clases normales con "
    f"p~0~ = 0.5 y α = {A} (Ecuación ({{eq:generacion}})), guardados en {pb.ARCHIVO_GENERADO.name}.",
    f"**Elegir la partición:** entrenar el perceptrón con cuatro divisiones y "
    f"{len(pb.SEMILLAS_COMPARACION)} semillas, y quedarse con {DIV} (Tablas {{tab:divisiones}} y "
    f"{{tab:comparacion}}).",
    f"**Particionar:** dividir cada conjunto en entrenamiento, validación y prueba, con 50 % de cada "
    f"clase en cada parte (Tabla {{tab:particion}}).",
    "**Entrenar:** aplicar la regla de la diapositiva 4 durante 200 épocas, con pesos y sesgo en "
    "cero, guardando al final de cada época el mejor perceptrón según la validación.",
    "**Evaluar:** calcular E~in~, el error de validación, E~out~, la matriz de confusión, la "
    "exactitud, el intervalo de confianza y el error de Bayes teórico y en prueba.",
    "**Verificar:** repetir el entrenamiento con el dataset CSV (clases separadas) y con distintos "
    "valores de α (barrido).",
], numerada=True)
inf.titulo("2.7.1 Ejecución del programa")
if capturas:
    inf.texto(f"La ejecución completa se muestra en las capturas de pantalla de Visual Studio Code "
              f"(Ilustraciones {{fig:captura1}} a {{fig:captura{len(capturas)}}}) y terminó sin "
              f"errores." if len(capturas) > 1 else
              "La ejecución se muestra en la Ilustración {fig:captura1} y terminó sin errores.")
    for k, ruta in enumerate(capturas, 1):
        inf.imagen(ruta, 15.5, f"Ejecución de perceptron_bayes.py en Visual Studio Code "
                               f"(parte {k} de {len(capturas)}).",
                   clave=f"captura{k}", fuente="Captura de pantalla de Visual Studio Code 1.142.0.")

inf.titulo("2.7.2 Tabla de resultados")
filas = []
for etiqueta, col, fv in [
        ("Separación α", "alpha", lambda v: num(v, 2)),
        ("Error de Bayes teórico", "Error_Bayes_teorico", lambda v: pct(v, 4)),
        ("Error de Bayes en prueba", "Error_Bayes_prueba", pct),
        ("Error de entrada E~in~", "E_in", pct),
        ("Error de validación", "Error_validacion", pct),
        ("Error de salida E~out~ (perceptrón)", "E_out", pct),
        ("Exactitud de Bayes", "Accuracy_Bayes", pct),
        ("Exactitud del perceptrón", "Accuracy_perceptron", pct),
        ("Sensibilidad / especificidad", None, None),
        ("IC 95 % de E~out~", None, None),
        ("Convergencia / mejor época", None, None)]:
    if col:
        filas.append([etiqueta, fv(gen[col]), fv(csv[col])])
    elif etiqueta.startswith("Sensibilidad"):
        filas.append([etiqueta] + [f"{pct(t['Sensibilidad'])} / {pct(t['Especificidad'])}"
                                   for t in (gen, csv)])
    elif etiqueta.startswith("IC"):
        filas.append([etiqueta, f"[{pct(gen['IC95_inferior'])}, {pct(gen['IC95_superior'])}]",
                      f"[0.00 %, {pct(csv['IC95_superior'])}]"])
    else:
        filas.append([etiqueta, f"No converge / época {int(gen['Mejor_epoca'])}",
                      f"Época {CONV_CSV} / época {int(csv['Mejor_epoca'])}"])
inf.tabla("Tabla de resultados del perceptrón y del clasificador de Bayes",
          ["Indicador", f"Datos aleatorios (α = {A})", "Dataset CSV"], filas, clave="resultados",
          anchos=[6.0, 4.8, 4.2])
inf.texto(f"En los datos aleatorios el perceptrón alcanzó E~out~ = {pct(gen['E_out'])}, solo "
          f"{pct(gen['E_out'] - gen['Error_Bayes_prueba'])} por encima del error de Bayes en la "
          f"misma muestra ({pct(gen['Error_Bayes_prueba'])}), y el error de Bayes teórico "
          f"({pct(EB)}) está dentro de su intervalo de confianza. E~in~ = {pct(gen['E_in'])} y "
          f"E~out~ = {pct(gen['E_out'])} son prácticamente iguales: el modelo generaliza. Las dos "
          f"pruebas de la Actividad 1 se cumplen, así que el entrenamiento es correcto. En el "
          f"dataset CSV todos los errores son cero.")

inf.titulo("2.7.3 Error de entrenamiento frente a error de prueba")
inf.texto("Esta sección compara los errores de cada conjunto y explica de dónde sale cada "
          "diferencia, para mostrar que el entrenamiento es correcto y que el modelo no está "
          "sobreajustado. La Tabla {tab:errores} reúne todos los errores de los datos aleatorios.")
inf.tabla("Errores del mejor perceptrón en cada conjunto (datos aleatorios)",
          ["Error", "Valor", "Qué mide", "Diferencia con E~out~"], [
              ["E~in~ (entrenamiento)", pct(gen["E_in"]), f"Ajuste a los {miles(gen['Entrenamiento'])} ejemplos de entrenamiento.",
               f"{num(100 * (gen['E_in'] - gen['E_out']), 2)} puntos"],
              ["E~val~ (validación)", pct(gen["Error_validacion"]), "Con estos datos se eligió el mejor perceptrón.",
               f"{num(100 * (gen['Error_validacion'] - gen['E_out']), 2)} puntos"],
              ["E~out~ (prueba)", pct(gen["E_out"]), f"Error con {miles(gen['Prueba'])} datos nuevos: la medida honesta.", "—"],
              ["Bayes en prueba", pct(gen["Error_Bayes_prueba"]), "Mejor clasificador posible en la misma muestra.",
               f"{num(100 * (gen['Error_Bayes_prueba'] - gen['E_out']), 2)} puntos"],
              ["Bayes teórico", pct(EB, 2), "Mejor resultado posible con infinitos datos.",
               f"{num(100 * (EB - gen['E_out']), 2)} puntos"],
          ], clave="errores", anchos=[3.6, 2.0, 6.6, 2.8],
          alinear=[WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.CENTER, WD_ALIGN_PARAGRAPH.LEFT,
                   WD_ALIGN_PARAGRAPH.CENTER])
inf.titulo("¿Es normal que E~out~ sea mayor que E~in~?", antes=4)
inf.texto(f"Sí. Los pesos se ajustaron con los datos de entrenamiento, así que el modelo suele "
          f"acertar un poco más con ellos que con datos nuevos: lo esperado es E~out~ ≥ E~in~. Aquí "
          f"la diferencia es E~out~ − E~in~ = {num(100 * GAP, 2)} puntos. Para saber si es grande, "
          f"se compara con la variación que produciría el azar al medir dos proporciones con "
          f"muestras independientes (Ecuación ({{eq:sediff}})).")
inf.ecuacion(sub(r("σ"), tx("dif")) + r("=") +
             raiz(r("e") + delim(r("1−e")) + delim(frac(r("1"), sub(r("N"), tx("ent"))) + r("+") +
                                                   frac(r("1"), sub(r("N"), tx("pru"))))) +
             tx(",      ") + r("e≈") + frac(EIN + r("+") + EOUT, r("2")), clave="sediff")
inf.texto(f"Con e ≈ {num(E_MEDIO, 4)}, N~ent~ = {miles(gen['Entrenamiento'])} y N~pru~ = "
          f"{miles(gen['Prueba'])}, resulta σ~dif~ = {num(100 * SE_DIF, 2)} puntos, y una diferencia "
          f"producida solo por el azar puede llegar a ±1.96·σ~dif~ = ±{num(100 * 1.96 * SE_DIF, 2)} "
          f"puntos. La diferencia observada ({num(100 * GAP, 2)}) es "
          f"{abs(GAP) / SE_DIF:.1f} veces σ~dif~: está dentro de lo que el azar explica, así que no "
          f"hay sobreajuste.")
inf.titulo("Cota teórica de generalización", antes=4)
inf.texto("La teoría del aprendizaje da además una garantía, aunque muy conservadora. Para un "
          "modelo con dimensión VC d~VC~ = 4 entrenado con N ejemplos, con 95 % de confianza "
          "(δ = 0.05), la cota de Vapnik–Chervonenkis de la Ecuación ({eq:vc}) acota cuánto puede "
          "alejarse E~out~ de E~in~ [4].")
inf.ecuacion(EOUT + r("≤") + EIN + r("+") +
             raiz(frac(r("8"), r("N")) + func("ln", frac(r("4") + delim(sup(delim(r("2N")), sub(r("d"), tx("VC"))) + r("+1")),
                                                     r("δ")))), clave="vc")
inf.texto(f"Con N = {miles(gen['Entrenamiento'])}, la cota permite una diferencia de hasta "
          f"{num(100 * COTA_VC, 1)} puntos. La diferencia real ({num(100 * GAP, 2)} puntos) es "
          f"muchísimo menor: la cota es una garantía para el peor caso, y un modelo de solo cuatro "
          f"parámetros con {miles(gen['Entrenamiento'])} ejemplos queda muy lejos de él. La otra "
          f"forma de verlo es con la desigualdad de Hoeffding sobre el conjunto de prueba: como el "
          f"modelo ya está fijo cuando se mide, E~out~ medido con M = {miles(gen['Prueba'])} se "
          f"aleja del error real a lo sumo √(ln(2/δ)/(2M)) = ±{num(100 * HOEFF, 2)} puntos con 95 % "
          f"de confianza. Por eso el error de prueba es la medida en la que se puede confiar.")
inf.titulo("¿Por qué el error de validación es el más bajo?", antes=4)
inf.texto(f"El error de validación ({pct(gen['Error_validacion'])}) es menor que E~in~ y que E~out~ "
          f"porque con él se eligió el mejor perceptrón: de las 200 épocas se tomó la que tuvo menor "
          f"error de validación, y elegir el mínimo de 200 mediciones favorece a la que tuvo suerte "
          f"con esa muestra. Por eso es optimista ({num(100 * (gen['E_out'] - gen['Error_validacion']), 2)} "
          f"puntos por debajo de E~out~) y no se usa para reportar el desempeño. Esta es la razón de "
          f"separar un conjunto de prueba que no participa en ninguna decisión.")
inf.titulo("Error de Bayes teórico frente a error de Bayes en prueba", antes=4)
inf.texto(f"El error de Bayes teórico ({pct(EB)}) es el que tendría el mejor clasificador con "
          f"infinitos datos. En la muestra de prueba ese mismo clasificador se equivocó en "
          f"{pct(gen['Error_Bayes_prueba'])}: {num(100 * (gen['Error_Bayes_prueba'] - EB), 2)} puntos "
          f"más, por azar de la muestra. Con M = {miles(gen['Prueba'])} el azar permite hasta "
          f"±{num(100 * SE_BAYES * 1.96, 2)} puntos, así que la diferencia es normal. Por eso el "
          f"perceptrón se compara con el error de Bayes en la misma muestra: los dos se miden con "
          f"los mismos {miles(gen['Prueba'])} ejemplos y el perceptrón queda solo "
          f"{num(100 * (gen['E_out'] - gen['Error_Bayes_prueba']), 2)} puntos por encima.")
inf.titulo("Evolución de los dos errores durante el entrenamiento", antes=4)
inf.imagen(RES / "entrenamiento_vs_prueba_generado.png", 15.0,
           "Error de entrenamiento y error de prueba por época, de los pesos de cada época y del "
           "mejor perceptrón (datos aleatorios).", clave="entrevsprueba",
           fuente="Elaboración propia con Python y Matplotlib.")
inf.texto(f"La Ilustración {{fig:entrevsprueba}} muestra, para cada época, el error de "
          f"entrenamiento y el de prueba. El error de prueba se anotó solo para documentar el "
          f"proceso: nunca se usó para elegir el modelo. Las líneas delgadas (pesos de cada época) "
          f"oscilan entre {pct(hist_gen['Error_entrenamiento'].min(), 1)} y "
          f"{pct(hist_gen['Error_prueba'].max(), 1)}, pero lo importante es que suben y bajan juntas: "
          f"cuando el plano es malo, lo es para los dos conjuntos. Las líneas gruesas (mejor "
          f"perceptrón) quedan estables y separadas por solo {num(100 * GAP, 2)} puntos, justo "
          f"encima del error de Bayes. Si el modelo estuviera sobreajustado, el error de "
          f"entrenamiento seguiría bajando mientras el de prueba sube; eso no ocurre.")
inf.titulo("La diferencia para todos los valores de α", antes=4)
inf.tabla("Diferencia entre el error de prueba y el de entrenamiento para cada α",
          ["α", "E~in~", "E~out~", "E~out~ − E~in~", "±1.96·σ~dif~", "¿Dentro del azar?"],
          [[f"{b['alpha']:g}", pct(b['E_in']), pct(b['E_out']),
            f"{num(100 * (b['E_out'] - b['E_in']), 2)} puntos", f"{num(100 * 1.96 * sd, 2)} puntos",
            "Sí" if abs(b['E_out'] - b['E_in']) <= 1.96 * sd else "No"]
           for b, sd in zip(barrido.to_dict("records"), SE_BARRIDO)],
          clave="gapalpha", anchos=[1.2, 2.2, 2.2, 3.0, 3.0, 2.8],
          alinear=[WD_ALIGN_PARAGRAPH.CENTER] * 6)
inf.texto(f"En {SI_BARRIDO} de los {len(barrido)} valores de α la diferencia entre E~out~ y E~in~ "
          f"está dentro de lo que explica el azar, y en todos es menor a 1.6 puntos. El "
          f"perceptrón generaliza igual de bien con clases muy superpuestas (α = 1) que con clases "
          f"casi separadas (α = 8).")

inf.titulo("2.7.4 Matrices de confusión")
inf.tabla("Matrices de confusión del conjunto de prueba (clase positiva: Hombre = +1)",
          ["Conjunto", "VP", "VN", "FP", "FN", "Total"],
          [[n, m.iloc[0, 0], m.iloc[1, 1], m.iloc[1, 0], m.iloc[0, 1], miles(m.to_numpy().sum())]
           for n, m in [(f"Datos aleatorios (α = {A})", mc_gen), ("Dataset CSV", mc_csv)]],
          clave="confusion", anchos=[5.0, 1.8, 1.8, 1.8, 1.8, 2.0])
inf.imagen(RES / "matrices_confusion.png", 15.0,
           "Matrices de confusión del perceptrón en los conjuntos de prueba.", clave="matrices",
           fuente="Elaboración propia con Python y Matplotlib.")
inf.texto(f"En los datos aleatorios hubo {FP} falsos positivos y {FN} falsos negativos: casi el "
          f"mismo número, porque el sesgo del mejor perceptrón es cero y el plano queda a igual "
          f"distancia de las dos clases.")

inf.titulo("2.7.5 Clases y frontera de decisión")
inf.imagen(RES / "figura1_clases_generado.png", 12.5,
           "Clases de los datos aleatorios y frontera del perceptrón.", clave="figura1gen",
           fuente="Elaboración propia con Python y Matplotlib.")
inf.imagen(RES / "clases_generado.png", 12.5,
           "Frontera del perceptrón frente a la frontera de Bayes (datos aleatorios).",
           clave="clasesgen", fuente="Elaboración propia con Python y Matplotlib.")
inf.texto(f"La Ilustración {{fig:figura1gen}} muestra la clase −1 (Mujer) con círculos y la clase "
          f"+1 (Hombre) con equis; las dos nubes se superponen en una franja ancha alrededor de la "
          f"frontera, donde están los errores. La Ilustración {{fig:clasesgen}} compara la "
          f"frontera del perceptrón con la de Bayes: pasan por el mismo punto y difieren "
          f"{angulo:.1f}°.")
inf.imagen(RES / "figura1_clases_csv.png", 11.5,
           "Clases del dataset CSV y frontera del perceptrón.", clave="clasescsv",
           fuente="Elaboración propia con Python y Matplotlib.")
inf.texto(f"En el dataset CSV (Ilustración {{fig:clasescsv}}) las dos clases forman grupos "
          f"separados (α ≈ {num(csv['alpha'], 2)}) y la frontera las divide sin errores.")

inf.titulo("2.7.6 Convergencia: historial del error y del mejor perceptrón")
inf.imagen(RES / "figura2_historial_iteraciones_generado.png", 15.0,
           f"Historial de error y del mejor perceptrón por número de iteraciones (primeras "
           f"{pb.EPOCAS_FIGURA2} épocas, datos aleatorios).", clave="figura2gen",
           fuente="Elaboración propia con Python y Matplotlib.")
inf.texto(f"Cada iteración es la revisión de un ejemplo; en total hubo "
          f"{miles(iteraciones_totales)} iteraciones y {miles(actualizaciones_totales)} "
          f"correcciones. La curva azul es el error de entrenamiento de los pesos actuales: nunca se "
          f"estabiliza y sus picos llegan a {pct(PICO_AZUL, 0)}, porque una sola corrección puede "
          f"girar mucho el plano. La curva roja, el mejor perceptrón, cae en la primera época y se "
          f"mantiene cerca de {pct(gen['E_in'], 1)}, junto al error de Bayes ({pct(EB, 1)}). Con "
          f"los pesos en cero el error inicial es 50 %, porque todo se predice como +1.")
inf.imagen(RES / "historial_generado.png", 15.0,
           "Error de entrenamiento, error de validación y mejor perceptrón por época (datos "
           "aleatorios).", clave="historial", fuente="Elaboración propia con Python y Matplotlib.")
inf.texto(f"Por época, el error de entrenamiento y el de validación suben y bajan juntos (no hay "
          f"memorización). El mejor perceptrón llegó a {pct(gen['Error_validacion'])} de error de "
          f"validación en la época {int(gen['Mejor_epoca'])} y ninguna época posterior lo mejoró, "
          f"lo que confirma que 200 épocas son suficientes.")

inf.titulo("2.7.7 Barrido de α")
inf.tabla("Error de Bayes y del perceptrón para distintos valores de α (p~0~ = 0.5)",
          ["α", "Bayes teórico", "Bayes en prueba", "E~in~", "E~out~", "IC 95 % de E~out~"],
          [[f"{b.alpha:g}", pct(b.Error_Bayes_teorico), pct(b.Error_Bayes_prueba), pct(b.E_in),
            pct(b.E_out), f"± {pct(b.IC95_margen)}" if b.E_out > 0 else f"≤ {pct(b.IC95_superior)}"]
           for b in barrido.itertuples()], clave="barrido",
          anchos=[1.2, 2.7, 2.9, 2.2, 2.2, 3.4], alinear=[WD_ALIGN_PARAGRAPH.CENTER] * 6)
inf.imagen(RES / "barrido_alpha.png", 15.0,
           "Error de Bayes (teórico y en prueba) y error del perceptrón según α.", clave="barrido",
           fuente="Elaboración propia con Python y Matplotlib.")

inf.titulo("2.7.8 Cumplimiento de las instrucciones")
inf.tabla("Verificación de las instrucciones de la guía y de clase", ["Instrucción", "Cómo se cumplió"], [
    ["1. Usar el dataset de la guía", "Se usó como verificación (clases separadas); el análisis principal usa datos aleatorios."],
    ["2. Dataset didáctico", "Las clases se interpretan solo como etiquetas +1/−1."],
    ["3. Hombre = 1, Mujer = −1", "Ecuación ({eq:codificacion})."],
    ["4. Sin scikit-learn", "El entrenamiento se programó desde cero."],
    ["5. pandas y NumPy", "pandas para los datos; NumPy para el cálculo (y Matplotlib para los gráficos)."],
    ["6. Pesos = 0, sesgo = 0, ≥ 200 épocas", "Pesos y sesgo en cero y 200 épocas completas."],
    ["7. Perceptrón simple", "Una neurona; el mejor perceptrón por validación no agrega capas."],
    ["Datos aleatorios p~0~ = 0.5, α = " + A, f"{miles(pb.N_GENERADO)} registros (Ecuación ({{eq:generacion}}))."],
    ["División justificada", f"{DIV} con criterios 1 y 2 (Tablas {{tab:divisiones}} y {{tab:comparacion}})."],
    ["Errores pedidos", "Bayes, E~in~, E~out~, validación, exactitud e IC (Tabla {tab:resultados})."],
], clave="cumplimiento", anchos=[5.4, 9.6], alinear=[WD_ALIGN_PARAGRAPH.LEFT] * 2)

# ----------------------------------------------------------------------------
# 2.8 a 2.12
# ----------------------------------------------------------------------------
seccion("Habilidades blandas empleadas en la práctica")
casillas([(False, "Liderazgo"), (True, "Trabajo en equipo"), (True, "Comunicación asertiva"),
          (False, "La empatía"), (True, "Pensamiento crítico"), (True, "Flexibilidad"),
          (False, "La resolución de conflictos"), (True, "Adaptabilidad"), (True, "Responsabilidad")])

seccion("2.9 Conclusiones")
inf.lista([
    f"**Sobre el funcionamiento del perceptrón:** el perceptrón programado desde cero con la regla "
    f"de la diapositiva 4 (si y·f(x) ≤ 0, entonces w ← w + y·x), con Hombre = +1, Mujer = −1 y "
    f"pesos y sesgo iniciales en cero, corrige los pesos solo cuando se equivoca y cada corrección "
    f"acerca el ejemplo al lado correcto (Ecuación ({{eq:mejora}})). Con clases separadas "
    f"(dataset CSV) converge en la época {CONV_CSV}; con clases superpuestas (datos aleatorios) "
    f"nunca converge, y conservar el mejor perceptrón según la validación es lo que permite "
    f"obtener un buen modelo dentro de las 200 épocas.",
    f"**Sobre su desempeño:** en los datos aleatorios con p~0~ = 0.5 y α = {A}, cuyo error de "
    f"Bayes es {pct(EB)}, el perceptrón obtuvo E~in~ = {pct(gen['E_in'])} y E~out~ = "
    f"{pct(gen['E_out'])} (exactitud de {pct(gen['Accuracy_perceptron'])}), apenas "
    f"{pct(gen['E_out'] - gen['Error_Bayes_prueba'])} por encima del mejor clasificador posible en "
    f"la misma muestra y con el error de Bayes dentro de su intervalo de confianza. La diferencia "
    f"entre el error de prueba y el de entrenamiento ({num(100 * GAP, 2)} puntos) está dentro de lo "
    f"que explica el azar, así que el modelo no está sobreajustado; el barrido de "
    f"α confirma lo mismo para cualquier superposición, y en el dataset CSV la exactitud fue de "
    f"100 %. La partición {DIV}, elegida porque una validación y una prueba grandes eligen y miden "
    f"mejor el modelo, fue clave para llegar a este resultado.",
], numerada=True)

seccion("2.10 Recomendaciones")
inf.texto("Se recomienda repetir el experimento sin cambiar el modelo, pero con clases de distinta "
          "probabilidad (por ejemplo p~0~ = 0.8), y reportar la sensibilidad y la especificidad "
          "además de la exactitud. En ese caso la frontera de Bayes se desplaza hacia la clase "
          "menos probable y se podría verificar si el perceptrón también aprende ese "
          "desplazamiento, repitiendo cada configuración con varias semillas para estimar la "
          "variabilidad de E~out~.")

seccion("2.11 Referencias bibliográficas")
referencias = [
    '[1] Material docente, "Artificial Neural Networks", ANN.pdf, diapositivas 1–4, 2026.',
    '[2] Dataset sintético, "dataset_Perceptron_5000_continuo_menos1_a_1.csv", material de clase, '
    'Inteligencia de Negocios, Universidad Técnica de Ambato, 2026.',
    '[3] R. O. Duda, P. E. Hart y D. G. Stork, Pattern Classification, 2.ª ed. New York, NY, USA: '
    'Wiley, 2001.',
    '[4] Y. S. Abu-Mostafa, M. Magdon-Ismail y H.-T. Lin, Learning From Data. Pasadena, CA, USA: '
    'AMLBook, 2012.',
    '[5] S. I. Gallant, "Perceptron-based learning algorithms," IEEE Transactions on Neural '
    'Networks, vol. 1, no. 2, pp. 179–191, 1990.',
    '[6] F. Rosenblatt, "The perceptron: A probabilistic model for information storage and '
    'organization in the brain," Psychological Review, vol. 65, no. 6, pp. 386–408, 1958.',
    '[7] C. M. Bishop, Pattern Recognition and Machine Learning. New York, NY, USA: Springer, 2006.',
    '[8] D. C. Montgomery y G. C. Runger, Applied Statistics and Probability for Engineers, 7.ª ed. '
    'Hoboken, NJ, USA: Wiley, 2018.',
    '[9] C. R. Harris et al., "Array programming with NumPy," Nature, vol. 585, pp. 357–362, 2020.',
    '[10] W. McKinney, "Data structures for statistical computing in Python," en Proc. 9th Python '
    'in Science Conf., Austin, TX, USA, 2010, pp. 56–61.',
    '[11] J. D. Hunter, "Matplotlib: A 2D graphics environment," Computing in Science & '
    'Engineering, vol. 9, no. 3, pp. 90–95, 2007.',
    '[12] A. B. J. Novikoff, "On convergence proofs on perceptrons," en Proc. Symposium on the '
    'Mathematical Theory of Automata, vol. 12, Brooklyn, NY, USA, 1962, pp. 615–622.',
]
for ref in referencias:
    inf.texto(ref, alineacion=WD_ALIGN_PARAGRAPH.LEFT, sangria=Cm(1.27), primera=Cm(-0.63),
              interlineado=1.15)

seccion("2.12 Anexos")
inf.texto("Las capturas de ejecución (sección 2.7.1), la tabla de resultados (Tabla "
          "{tab:resultados}) y las matrices de confusión (Tabla {tab:confusion} e Ilustración "
          "{fig:matrices}) se presentan en la sección 2.7, y el análisis del error de "
          "entrenamiento frente al de prueba en la sección 2.7.3. El código fuente se entrega como "
          "archivo aparte (perceptron_bayes.py).")

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
print(f"Informe generado: {SALIDA}")
print(f"Tablas: {inf.contador['tab']} | Ilustraciones: {inf.contador['fig']} | "
      f"Ecuaciones: {inf.contador['eq']} | Capturas: {len(capturas)}")
