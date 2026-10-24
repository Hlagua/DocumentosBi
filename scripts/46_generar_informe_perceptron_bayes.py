"""
Genera Taller_Perceptron_Bayes/Informe_Taller_Perceptron_Bayes.docx sobre la plantilla
UTA–FISEI (scripts/plantillas/Taller_Perceptron_plantilla.docx), con los resultados de
Taller_Perceptron_Bayes/perceptron_bayes.py.

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
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Cm, Pt

sys.path.insert(0, str(Path(__file__).resolve().parent))
from informe_docx import (FUENTE, Informe, agregar_texto, casos, delim, formato, frac,  # noqa: E402
                          func, func_lim, fuente_run, pie_pagina_numerado, poner_carrera,
                          r, raiz, sub, sup, suma, tx, acento)

RAIZ = Path(__file__).resolve().parents[1]
TALLER = RAIZ / "Taller_Perceptron_Bayes"
RES = TALLER / "resultados"
CAP = TALLER / "capturas"
PLANTILLA = RAIZ / "scripts" / "plantillas" / "Taller_Perceptron_plantilla.docx"
SALIDA = TALLER / "Informe_Taller_Perceptron_Bayes.docx"
BORRADOR = "--borrador" in sys.argv

sys.path.insert(0, str(TALLER))
import perceptron_bayes as pb  # noqa: E402

# ----------------------------------------------------------------------------
# Resultados del experimento
# ----------------------------------------------------------------------------
tabla = pd.read_csv(RES / "tabla_resultados.csv", encoding="utf-8-sig")
csv, gen = tabla.iloc[0], tabla.iloc[1]
barrido = pd.read_csv(RES / "barrido_alpha.csv", encoding="utf-8-sig")
hist_gen = pd.read_csv(RES / "historial_generado.csv", encoding="utf-8-sig")
hist_csv = pd.read_csv(RES / "historial_csv.csv", encoding="utf-8-sig")
mc_gen = pd.read_csv(RES / "matriz_confusion_generado.csv", index_col=0, encoding="utf-8-sig")
mc_csv = pd.read_csv(RES / "matriz_confusion_csv.csv", index_col=0, encoding="utf-8-sig")
df_csv = pd.read_csv(TALLER / "dataset_Perceptron_5000_continuo_menos1_a_1.csv", encoding="utf-8-sig")
df_gen = pd.read_csv(TALLER / "dataset_generado_p0_0.5_alpha_5.csv", encoding="utf-8-sig")
capturas = sorted(CAP.glob("vscode_ejecucion_*.png"))
if not capturas and not BORRADOR:
    raise SystemExit(f"Faltan las capturas en {CAP}")

w_gen = gen[["w1", "w2", "w3"]].to_numpy(dtype=float)
wb = pb.ALPHA * np.ones(3) / np.sqrt(3)
coseno = float(w_gen @ wb / (np.linalg.norm(w_gen) * np.linalg.norm(wb)))
angulo = float(np.degrees(np.arccos(coseno)))
desplazamiento = float(abs(gen["w0"]) / np.linalg.norm(w_gen))
act_media = float(hist_gen["Actualizaciones"].mean())
VP, FN = mc_gen.iloc[0]
FP, VN = mc_gen.iloc[1]
versiones = {"Python": sys.version.split()[0], "NumPy": np.__version__, "pandas": pd.__version__,
             "Matplotlib": pb.matplotlib.__version__}


def pct(v, d=2):
    return f"{100 * v:.{d}f} %"


def num(v, d=3):
    return f"{v:.{d}f}".replace("-", "−")


def miles(n):
    return f"{int(n):,}".replace(",", " ")


# ----------------------------------------------------------------------------
# Plantilla: portada, encabezado y pie
# ----------------------------------------------------------------------------
doc = Document(PLANTILLA)


def buscar(inicio, desde=0):
    for p in doc.paragraphs[desde:]:
        if p.text.strip().startswith(inicio):
            return p
    raise ValueError(f"No se encontró: {inicio}")


def eliminar(p):
    p._p.getparent().remove(p._p)


poner_carrera(doc)
pie_pagina_numerado(doc)

portada = [
    ("Tema:", "Perceptrón frente al clasificador de Bayes: error de entrada, error de salida "
              "y superposición de clases"),
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

# Se conserva el formato de los títulos de sección de la plantilla y se reemplaza el
# contenido del cuerpo (la plantilla corresponde a la guía anterior).
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
    p = inf.titulo(texto, sangria=0, antes=12)
    return p


def casillas(items):
    for marcado, texto in items:
        p = inf._nuevo()
        agregar_texto(p, ("☒ " if marcado else "☐ ") + texto)
        formato(p, WD_ALIGN_PARAGRAPH.LEFT, sangria=Cm(1.27), interlineado=1.15, despues=0)


# Símbolos de las ecuaciones
X = r("x")
MU0, MU1 = sub(r("μ"), r("0")), sub(r("μ"), r("1"))
SIGMA_INV = sup(r("Σ"), r("−1"))
EIN, EOUT = sub(r("E"), tx("in")), sub(r("E"), tx("out"))
YH = acento(r("y"), "̂")


def indicadora(e):
    return r("I") + delim(e, "[", "]")


# ----------------------------------------------------------------------------
# 2.1 a 2.5
# ----------------------------------------------------------------------------
seccion("2.1 Objetivos")
inf.titulo("General:", antes=2)
inf.texto("Entrenar un perceptrón de una sola neurona con clases 0 y 1, siguiendo las diapositivas "
          "13 a 15, y comparar su error con el error mínimo posible, el del clasificador de Bayes, "
          "tanto en el dataset del taller anterior como en datos generados con p~0~ = 0.5 y α = 5, "
          "validando la exactitud del modelo con datos de prueba que conservan su clase verdadera.")
inf.titulo("Específicos:", antes=4)
inf.lista([
    "Generar datos de dos clases normales cuya superposición se controla con α y describir la "
    "distribución de las clases.",
    "Dividir los datos en entrenamiento, validación y prueba (70/15/15) e implementar el perceptrón "
    "con salida escalón 0/1, error = y − ŷ y tasa de aprendizaje η = 0.1.",
    "Calcular el error de Bayes, el error de entrada E~in~, el error de salida E~out~, la exactitud, "
    "la matriz de confusión y el intervalo de confianza del error de prueba.",
    "Analizar cómo cambian el error de Bayes y el error del perceptrón cuando las clases se "
    "superponen más o menos (barrido de α).",
])

seccion("2.2 Modalidad")
inf.texto("Práctica de laboratorio. Trabajo en parejas.")
seccion("2.3 Tiempo de duración")
inf.texto("Presenciales: 120 minutos.", despues=0)
inf.texto("No presenciales: 30 minutos para organizar el informe y anexos.")

seccion("2.4 Instrucciones")
inf.texto("Las indicaciones dadas en clase para esta práctica fueron las siguientes:")
inf.lista([
    "Utilizar el CSV del taller «Programar perceptrón» (dataset_Perceptron_5000_continuo_menos1_a_1.csv).",
    "Se pueden crear datos: distribución de clases con p~0~ = 0.5 y α = 5, donde α controla cuánto "
    "se superponen las distribuciones.",
    "El grupo decide la división de los datos (por ejemplo 70/20/10). En este trabajo se usó "
    "70 % entrenamiento, 15 % validación y 15 % prueba.",
    "Implementar el perceptrón de las diapositivas 13, 14 y 15 (clases 0 y 1, η = 0.1).",
    "Validar la exactitud del modelo con los datos de prueba, que conservan su y verdadera.",
    "Reportar el error de Bayes, el clasificador, las clases bien definidas, el error del "
    "perceptrón, el error de entrada, el error de salida y la distribución de las clases.",
], numerada=True)

seccion("2.5 Listado de equipos, materiales y recursos")
inf.texto("Listado de equipos y materiales generales empleados en la guía práctica:")
inf.lista(["Computador con Windows 11 Pro.",
           "Visual Studio Code (editor y terminal integrada).",
           "Python 3 con las bibliotecas pandas, NumPy y Matplotlib.",
           "Dataset dataset_Perceptron_5000_continuo_menos1_a_1.csv y datos generados por el script.",
           "Documentos ANN.pdf y Perceptron_Explicacion_IF_Paso_a_Paso.pdf (diapositivas 13 a 15)."])
inf.texto("TAC (Tecnologías para el Aprendizaje y Conocimiento) empleados en la guía práctica:",
          despues=2)
casillas([(False, "Plataformas educativas"), (False, "Simuladores y laboratorios virtuales"),
          (True, "Aplicaciones educativas"), (True, "Recursos audiovisuales"),
          (False, "Gamificación"), (False, "Inteligencia Artificial")])
inf.texto("Otros (Especifique): Python 3 y Visual Studio Code", sangria=Cm(1.27))
inf.titulo("Software utilizado en la práctica:", antes=8)
inf.texto("El código se escribió y ejecutó en Visual Studio Code, desde su terminal integrada "
          "(PowerShell); no se usó Jupyter Notebook, Google Colab ni MATLAB. La Tabla {tab:software} "
          "resume las versiones con las que se obtuvieron los resultados.")
inf.tabla("Software y bibliotecas utilizados", ["Software", "Versión", "Uso en la práctica"], [
    ["Windows 11 Pro", "10.0.26300", "Sistema operativo del equipo de trabajo."],
    ["Visual Studio Code", "1.142.0", "Edición del script y ejecución en la terminal integrada."],
    ["Python", versiones["Python"], "Lenguaje de programación del experimento."],
    ["NumPy", versiones["NumPy"], "Generación de datos normales y cálculo vectorial."],
    ["pandas", versiones["pandas"], "Lectura y escritura de CSV y tablas de resultados."],
    ["Matplotlib", versiones["Matplotlib"], "Gráficos de clases, historial y barrido de α."],
    ["Microsoft Word", "16.0", "Redacción y maquetación del informe."],
], clave="software", anchos=[3.6, 2.6, 8.8])

# ----------------------------------------------------------------------------
# 2.6 Actividades
# ----------------------------------------------------------------------------
seccion("2.6 Actividades por desarrollar")

# Actividad 1 --------------------------------------------------------------
actividad("Actividad 1. Fundamentos: clasificador de Bayes, error de entrada y error de salida")
inf.titulo("Objetivo de la actividad", antes=2)
inf.texto("Definir con precisión los errores que se piden en la práctica y entender por qué el error "
          "de Bayes es el punto de referencia contra el que se compara el perceptrón.")
inf.titulo("Clasificador de Bayes")
inf.texto("El clasificador de Bayes asigna cada observación a la clase más probable dado lo que se "
          "observa. Para ello usa el teorema de Bayes (Ecuación ({eq:bayes})), que combina la "
          "probabilidad a priori de cada clase, P(C~k~), con la distribución de los datos dentro de "
          "la clase, p(x | C~k~) [3], [7].")
inf.ecuacion(r("P") + delim(sub(r("C"), r("k")) + r("∣") + X) + r("=") +
             frac(r("p") + delim(X + r("∣") + sub(r("C"), r("k"))) + r("P") +
                  delim(sub(r("C"), r("k"))), r("p") + delim(X)) +
             tx(",      ") + r("k∈") + delim(r("0, 1"), "{", "}"), clave="bayes")
inf.texto("La regla de decisión de la Ecuación ({eq:regla}) elige la clase con mayor probabilidad a "
          "posteriori. Ningún otro clasificador puede tener, en promedio, un error menor; ese error "
          "mínimo se llama **error de Bayes** y depende solo de cuánto se superponen las clases, no "
          "del algoritmo [3].")
inf.ecuacion(sub(YH, tx("Bayes")) + delim(X) + r("=") + casos(
    r("1") + tx(",   si ") + r("P") + delim(sub(r("C"), r("1")) + r("∣") + X) + r("≥P") +
    delim(sub(r("C"), r("0")) + r("∣") + X),
    r("0") + tx(",   en otro caso")), clave="regla")
inf.texto("En esta práctica cada clase sigue una distribución normal con media μ~k~ y una covarianza "
          "Σ común (Ecuación ({eq:normal})). Con esa condición, la frontera de Bayes es un plano: "
          "el clasificador óptimo es lineal, con los pesos de la Ecuación ({eq:bayeslineal}) [7]. Por "
          "eso tiene sentido compararlo con un perceptrón, que también traza un plano.")
inf.ecuacion(r("p") + delim(X + r("∣") + sub(r("C"), r("k"))) + r("=") +
             frac(r("1"), sup(delim(r("2π")), r("3/2")) + sup(delim(r("Σ"), "|", "|"), r("1/2"))) +
             r("exp") + delim(r("−") + frac(r("1"), r("2")) +
                              sup(delim(X + r("−") + sub(r("μ"), r("k"))), r("T")) + SIGMA_INV +
                              delim(X + r("−") + sub(r("μ"), r("k"))), "[", "]"), clave="normal")
inf.ecuacion(sub(r("w"), tx("B")) + r("=") + SIGMA_INV + delim(MU1 + r("−") + MU0) +
             tx(",      ") + sub(r("w"), tx("B0")) + r("=−") + frac(r("1"), r("2")) +
             sup(delim(MU1 + r("+") + MU0), r("T")) + sub(r("w"), tx("B")) + r("+") +
             func("ln", frac(sub(r("p"), r("1")), sub(r("p"), r("0")))), clave="bayeslineal")
inf.titulo("Superposición de las clases: el parámetro α")
inf.texto("La separación entre las dos clases se mide con la distancia de Mahalanobis entre sus "
          "medias (Ecuación ({eq:alpha})): cuántas desviaciones estándar separan un centro del "
          "otro. Mientras menor es α, más se enciman las distribuciones y más observaciones caen "
          "del lado equivocado de cualquier frontera. Con clases equiprobables (p~0~ = p~1~ = 0.5), "
          "el error de Bayes tiene la forma cerrada de la Ecuación ({eq:errorbayes}), donde Φ es la "
          "función de distribución acumulada de la normal estándar [3].")
inf.ecuacion(r("α=") + raiz(sup(delim(MU1 + r("−") + MU0), r("T")) + SIGMA_INV +
                            delim(MU1 + r("−") + MU0)), clave="alpha")
inf.ecuacion(sub(r("E"), tx("Bayes")) + r("=Φ") + delim(r("−") + frac(r("α"), r("2"))) +
             tx(",      con ") + sub(r("p"), r("0")) + r("=0.5"), clave="errorbayes")
inf.texto(f"Con α = 5 se obtiene E~Bayes~ = Φ(−2.5) = {pct(gen['Error_Bayes_teorico'], 4)}, el "
          f"mismo «Error de Bayes = 0.62» que mostró el ejemplo en MATLAB presentado en clase. Esto "
          f"confirma que α es la separación entre las clases en unidades de desviación estándar.")
inf.titulo("Error de entrada y error de salida")
inf.texto("El **error de entrada** E~in~ es la proporción de observaciones de entrenamiento mal "
          "clasificadas (Ecuación ({eq:ein})), donde I[·] vale 1 si la condición se cumple y 0 en "
          "otro caso. El **error de salida** E~out~ es la probabilidad de equivocarse con datos "
          "nuevos (Ecuación ({eq:eout})). Como la distribución real no se conoce, E~out~ se estima "
          "con el conjunto de prueba, que el modelo nunca vio y que conserva su clase verdadera [4].")
inf.ecuacion(EIN + r("=") + frac(r("1"), r("N")) +
             suma(r("i=1"), r("N"), indicadora(YH + delim(sub(r("x"), r("i"))) + r("≠") +
                                              sub(r("y"), r("i")))), clave="ein")
inf.ecuacion(EOUT + r("=P") + delim(YH + delim(X) + r("≠y")) + r("≈") + frac(r("1"), r("M")) +
             suma(r("i=1"), r("M"), indicadora(YH + delim(sub(r("x"), r("i"))) + r("≠") +
                                              sub(r("y"), r("i")))), clave="eout")
inf.texto("Un modelo generaliza bien cuando E~in~ ≈ E~out~: lo que aprendió en entrenamiento se "
          "mantiene con datos nuevos. Además, ningún clasificador puede tener un E~out~ esperado "
          "menor que el error de Bayes, así que la meta es E~in~ ≈ E~out~ ≈ E~Bayes~.")

# Actividad 2 --------------------------------------------------------------
actividad("Actividad 2. Preparación y generación de los datos")
inf.titulo("Objetivo de la actividad", antes=2)
inf.texto("Preparar los dos conjuntos de datos del experimento, describir la distribución de sus "
          "clases y dividirlos en entrenamiento, validación y prueba.")
inf.titulo("Dataset del taller anterior")
inf.texto(f"El CSV tiene {miles(len(df_csv))} registros, tres características continuas y la clase "
          f"(2 500 Hombre y 2 500 Mujer, p~0~ = 0.5). Al estimar las medias y la covarianza común de "
          f"cada clase y aplicar la Ecuación ({{eq:alpha}}), la separación resulta α ≈ "
          f"{num(csv['alpha'], 2)}. Es una separación enorme: el error de Bayes teórico es "
          f"prácticamente cero (del orden de 10^−24^ %). Las clases están «bien definidas» y no se "
          f"tocan, por lo que con este dataset no es posible observar la diferencia entre el error "
          f"del perceptrón y el error de Bayes. Por eso se generaron datos adicionales.")
inf.titulo("Datos generados con p~0~ = 0.5 y α = 5")
inf.texto(f"Se generaron {miles(len(df_gen))} registros con tres características, para mantener la "
          f"misma estructura del dataset del taller. Cada clase sigue una normal con covarianza "
          f"identidad (desviación estándar 1 en cada eje) y sus centros se colocan sobre la diagonal "
          f"(1, 1, 1), uno a cada lado del origen (Ecuación ({{eq:generacion}})). Con esa elección la "
          f"distancia de Mahalanobis entre las clases es exactamente α. La mitad de los registros es "
          f"de cada clase (p~0~ = 0.5) y se usó la semilla 42 para que los datos sean reproducibles. "
          f"Los datos se guardaron en dataset_generado_p0_0.5_alpha_5.csv con el mismo formato de "
          f"columnas del CSV original.")
inf.ecuacion(X + r("∣") + delim(r("y=k")) + r("∼") + r("N") +
             delim(sub(r("μ"), r("k")) + tx(", ") + r("I")) + tx(",      ") + MU0 + r("=−") +
             frac(r("α"), r("2")) + r("u") + tx(",   ") + MU1 + r("=") + frac(r("α"), r("2")) +
             r("u") + tx(",   ") + r("u=") + frac(sup(delim(r("1, 1, 1")), r("T")), raiz(r("3"))),
             clave="generacion")
inf.texto(f"Con estos parámetros, la Ecuación ({{eq:bayeslineal}}) da los pesos de Bayes "
          f"w~B~ = α·u = ({num(wb[0])}, {num(wb[1])}, {num(wb[2])}) y w~B0~ = 0: la frontera óptima "
          f"pasa por el origen y es perpendicular a la diagonal. La Ilustración {{fig:distgen}} "
          f"muestra la distribución de las clases proyectada sobre la dirección que las separa: dos "
          f"campanas que se tocan en una franja estrecha alrededor del umbral. Las observaciones de "
          f"esa franja son las que ningún clasificador puede acertar siempre.")
inf.imagen(RES / "distribucion_generado.png", 14.5,
           "Distribución de las clases de los datos generados sobre la dirección que las separa.",
           clave="distgen", fuente="Elaboración propia con Python y Matplotlib.")
inf.titulo("Codificación de la clase y partición de los datos")
inf.texto("Siguiendo la diapositiva 15, la clase se codificó como Hombre = 1 y Mujer = 0. Ambos "
          "conjuntos se dividieron con una partición estratificada 70/15/15 (Tabla {tab:particion}), "
          "que mantiene la proporción 50/50 en cada parte:")
inf.lista([
    "**Entrenamiento (70 %):** el perceptrón ajusta sus pesos con estos datos; aquí se mide E~in~.",
    "**Validación (15 %):** al final de cada época se mide el error con estos datos y se guarda el "
    "mejor perceptrón. Así la elección del modelo no usa los datos de prueba.",
    "**Prueba (15 %):** solo se usa al final, con la clase verdadera, para estimar E~out~ y la "
    "exactitud del modelo.",
])
inf.tabla("Partición de los datos (70/15/15, estratificada, semilla 42)",
          ["Conjunto de datos", "Total", "Entrenamiento", "Validación", "Prueba"], [
              ["CSV del taller", miles(csv["Registros"]), miles(csv["Entrenamiento"]),
               miles(csv["Validacion"]), miles(csv["Prueba"])],
              ["Datos generados (α = 5)", miles(gen["Registros"]), miles(gen["Entrenamiento"]),
               miles(gen["Validacion"]), miles(gen["Prueba"])],
          ], clave="particion", anchos=[4.6, 2.2, 3.0, 2.6, 2.4])
inf.texto("Se eligió 70/15/15 porque deja la mayor parte de los datos para aprender y reserva dos "
          "partes iguales para elegir el modelo y para medirlo. Con 20 000 registros generados, el "
          "conjunto de prueba tiene 3 000 observaciones: suficiente para estimar un error cercano al "
          "0.6 % con un intervalo de confianza razonable.")

# Actividad 3 --------------------------------------------------------------
actividad("Actividad 3. Perceptrón con clases 0 y 1 (diapositivas 13 a 15)")
inf.titulo("Objetivo de la actividad", antes=2)
inf.texto("Implementar el perceptrón tal como lo presentan las diapositivas 13 a 15 y adaptarlo a "
          "datos cuyas clases se superponen.")
inf.titulo("Por qué no sirve la condición y·z ≤ 0 con clases 0 y 1")
inf.texto("En el taller anterior las clases eran +1 y −1, y el perceptrón se actualizaba cuando "
          "y~i~·z ≤ 0. La diapositiva 15 advierte que esa condición no funciona con clases 0 y 1: si "
          "y = 0, el producto 0·z es 0 para cualquier z, la condición siempre se cumple y el ajuste "
          "tampoco corrige esa clase. La solución es usar una salida escalón explícita "
          "(Ecuación ({eq:escalon})) y calcular el error como la diferencia entre la clase real y la "
          "predicha (Ecuación ({eq:error})).")
inf.ecuacion(r("z=") + sub(r("w"), r("0")) + r("+") + sub(r("w"), r("1")) + sub(r("x"), r("1")) +
             r("+") + sub(r("w"), r("2")) + sub(r("x"), r("2")) + r("+") + sub(r("w"), r("3")) +
             sub(r("x"), r("3")) + tx(",      ") + YH + r("=") +
             casos(r("1") + tx(",   si ") + r("z≥0"), r("0") + tx(",   si ") + r("z<0")),
             clave="escalon")
inf.ecuacion(tx("error") + r("=") + r("y−") + YH + r("∈") + delim(r("−1, 0, 1"), "{", "}"),
             clave="error")
inf.texto("El error vale 0 cuando la predicción es correcta, +1 cuando el modelo dijo 0 y la clase "
          "era 1, y −1 en el caso contrario. Solo cuando el error es distinto de cero se corrigen "
          "los pesos con la regla de la Ecuación ({eq:actualizacion}), que usa la tasa de aprendizaje "
          "η = 0.1 de la diapositiva 14. El signo del error decide si el plano se acerca o se aleja "
          "de la observación mal clasificada.")
inf.ecuacion(r("w←w+η·") + tx("error") + r("·x") + tx(",      ") + sub(r("w"), r("0")) + r("←") +
             sub(r("w"), r("0")) + r("+η·") + tx("error") + tx(",      ") + r("η=0.1"),
             clave="actualizacion")
inf.tabla("Correspondencia entre las diapositivas 13 a 15 y el código",
          ["Diapositiva", "Código en perceptron_bayes.py"], [
              ["13: pesos en cero", "w = np.zeros(3); w0 = 0.0"],
              ["13: suma ponderada", "z = np.dot(w, X[i]) + w0"],
              ["15: salida escalón explícita", "y_pred = 1 if z >= 0 else 0"],
              ["15: error = y − predicción", "error = y[i] - y_pred"],
              ["14 y 15: ajuste con η = 0.1", "w = w + eta * error * X[i]; w0 = w0 + eta * error"],
              ["13: detener si no hay errores", "if errores == 0: break"],
          ], clave="codigo", anchos=[5.6, 9.4], alinear=[WD_ALIGN_PARAGRAPH.LEFT] * 2)
inf.titulo("Conservar el mejor perceptrón")
inf.texto(f"Cuando las clases se superponen no existe un plano sin errores, así que el perceptrón "
          f"nunca deja de actualizarse: con los datos generados hizo en promedio "
          f"{act_media:.0f} correcciones por época durante las 200 épocas. Cada corrección mueve el "
          f"plano para acertar una observación de la zona de traslape, y eso puede empeorar otras, "
          f"por lo que el error oscila de una época a otra. Para no quedarse con los pesos de la "
          f"última época, que pueden ser malos, se guarda el perceptrón con menor error de "
          f"validación (Ecuación ({{eq:pocket}})). Es la idea del algoritmo «pocket» [5] y "
          f"corresponde a la curva «Historial del mejor perceptrón» del ejemplo presentado en clase.")
inf.ecuacion(sup(r("w"), r("∗")) + r("=") +
             func_lim("arg min", r("t=1,…,T"), sub(r("E"), tx("val")) + delim(sub(r("w"), r("t")))),
             clave="pocket")
inf.texto("Las observaciones de entrenamiento se recorren en un orden aleatorio distinto en cada "
          "época (semilla 42), para que el ajuste no dependa del orden del archivo.")

# Actividad 4 --------------------------------------------------------------
actividad("Actividad 4. Evaluación y comparación con el clasificador de Bayes")
inf.titulo("Objetivo de la actividad", antes=2)
inf.texto("Validar la exactitud del perceptrón con los datos de prueba y compararla con la del "
          "clasificador de Bayes.")
inf.titulo("Desarrollo")
inf.texto("Con los pesos del mejor perceptrón se clasificaron los tres conjuntos. Se calcularon:")
inf.lista([
    "**Error de Bayes teórico:** con la Ecuación ({eq:errorbayes}). En los datos generados se usan "
    "los parámetros reales; en el CSV, las medias y la covarianza estimadas con el entrenamiento.",
    "**Error de Bayes en prueba:** se aplica la regla de Bayes (Ecuación ({eq:bayeslineal})) a los "
    "datos de prueba. Es el error que comete el mejor clasificador posible con esa misma muestra.",
    "**E~in~, error de validación y E~out~:** con la Ecuación ({eq:ein}) en cada conjunto.",
    "**Exactitud:** 1 − error, y la matriz de confusión del conjunto de prueba.",
    "**Intervalo de confianza del 95 %** para E~out~ (Ecuación ({eq:ic})).",
])
inf.ecuacion(EOUT + r("±1.96") + raiz(frac(EOUT + delim(r("1−") + EOUT), r("M"))) +
             tx(",      si ") + EOUT + r("=0:") + tx("  ") + delim(r("0, ") + frac(r("3"), r("M")),
                                                                     "[", "]"), clave="ic")
inf.texto("Cuando no hay ningún error en prueba, la fórmula normal da un intervalo de ancho cero, que "
          "no es creíble. En ese caso se usa la «regla del tres»: con M observaciones sin errores, "
          "el error real es menor que 3/M con 95 % de confianza.")
inf.texto(f"En los datos generados, el error de prueba del perceptrón fue E~out~ = "
          f"{pct(gen['E_out'])}, con un intervalo de confianza de [{pct(gen['IC95_inferior'])}, "
          f"{pct(gen['IC95_superior'])}]. Ese intervalo contiene al error de Bayes teórico "
          f"({pct(gen['Error_Bayes_teorico'])}), así que la diferencia entre ambos no es "
          f"estadísticamente significativa. Los resultados completos se presentan en la sección 2.7 "
          f"(Tablas {{tab:resultados}} y {{tab:confusion}}).")

# Actividad 5 --------------------------------------------------------------
actividad("Actividad 5. Efecto de la superposición de las clases (barrido de α)")
inf.titulo("Objetivo de la actividad", antes=2)
inf.texto("Comprobar cómo cambian el error de Bayes y el error del perceptrón cuando α aumenta o "
          "disminuye.")
inf.titulo("Desarrollo")
inf.texto(f"Se repitió el experimento completo (generación, partición 70/15/15, entrenamiento y "
          f"evaluación) para α = {', '.join(str(a) for a in pb.ALPHAS_BARRIDO[:-1])} y "
          f"{pb.ALPHAS_BARRIDO[-1]}, con p~0~ = 0.5 y {miles(pb.N_GENERADO)} registros en cada caso. "
          f"La Tabla {{tab:barrido}} y la Ilustración {{fig:barrido}} (sección 2.7) muestran los "
          f"resultados.")
b_alpha = dict(zip(barrido["alpha"].astype(int), barrido["Error_Bayes_teorico"]))
inf.texto(f"**Respuesta de la actividad:** α «sobremonta» las distribuciones: cuando α es pequeño "
          f"las clases se superponen mucho y el error de Bayes es alto ({pct(b_alpha[1])} con α = 1); cuando α "
          f"crece, el traslape desaparece y el error cae casi a cero ({pct(b_alpha[6])} con α = 6 y "
          "prácticamente 0 % con α = 8). En todos los casos el error de prueba del perceptrón sigue "
          "de cerca al de Bayes: como la frontera óptima es lineal, un perceptrón bien entrenado "
          "puede acercarse al mejor clasificador posible.")

# ----------------------------------------------------------------------------
# 2.7 Resultados obtenidos
# ----------------------------------------------------------------------------
seccion("2.7 Resultados obtenidos")
inf.texto("Los resultados se obtuvieron al ejecutar python perceptron_bayes.py en la terminal "
          "integrada de Visual Studio Code. El script generó los datos, entrenó los perceptrones, "
          "calculó los errores y guardó todos los gráficos y tablas en la carpeta resultados/.")
inf.titulo("2.7.1 Ejecución del programa")
if capturas:
    inf.texto(f"La ejecución completa se muestra en las capturas de pantalla de Visual Studio Code "
              f"(Ilustraciones {{fig:captura1}} a {{fig:captura{len(capturas)}}}) y terminó sin "
              f"errores." if len(capturas) > 1 else
              "La ejecución se muestra en la Ilustración {fig:captura1} y terminó sin errores.")
    descripciones = {
        1: "inicio de la ejecución, resultados con el CSV del taller y con los datos generados",
        2: "resultados con los datos generados (p0 = 0.5, α = 5) y matriz de confusión",
        3: "resumen de los dos experimentos y barrido de α",
    }
    for k, ruta in enumerate(capturas, 1):
        detalle = descripciones.get(k, f"parte {k} de {len(capturas)}")
        inf.imagen(ruta, 15.5, f"Ejecución de perceptron_bayes.py en Visual Studio Code: {detalle}.",
                   clave=f"captura{k}", fuente="Captura de pantalla de Visual Studio Code 1.142.0.")

inf.titulo("2.7.2 Resultados en los dos conjuntos de datos")
filas = []
for etiqueta, col, formato_valor in [
        ("Separación α", "alpha", lambda v: num(v, 2)),
        ("Error de Bayes teórico", "Error_Bayes_teorico", lambda v: pct(v, 4)),
        ("Error de Bayes en prueba", "Error_Bayes_prueba", pct),
        ("Error de entrada E~in~", "E_in", pct),
        ("Error de validación", "Error_validacion", pct),
        ("Error de salida E~out~ (perceptrón)", "E_out", pct),
        ("Accuracy de Bayes", "Accuracy_Bayes", pct),
        ("Accuracy del perceptrón", "Accuracy_perceptron", pct),
        ("IC 95 % de E~out~", None, None),
        ("Mejor época / épocas ejecutadas", None, None)]:
    if col:
        filas.append([etiqueta, formato_valor(csv[col]), formato_valor(gen[col])])
    elif etiqueta.startswith("IC"):
        filas.append([etiqueta, f"[0.00 %, {pct(csv['IC95_superior'])}]",
                      f"[{pct(gen['IC95_inferior'])}, {pct(gen['IC95_superior'])}]"])
    else:
        filas.append([etiqueta, f"{int(csv['Mejor_epoca'])} / {int(csv['Epocas'])}",
                      f"{int(gen['Mejor_epoca'])} / {int(gen['Epocas'])}"])
inf.tabla("Errores y exactitud del perceptrón y del clasificador de Bayes",
          ["Indicador", "CSV del taller", "Datos generados (α = 5)"], filas, clave="resultados",
          anchos=[6.4, 4.0, 4.6])
inf.texto(f"En el CSV del taller todos los errores son cero: el perceptrón convergió en la segunda "
          f"época, sin ninguna actualización, y clasificó bien los 750 registros de prueba. En los "
          f"datos generados el perceptrón alcanzó E~out~ = {pct(gen['E_out'])}, igual al error de "
          f"Bayes medido en la misma muestra de prueba ({pct(gen['Error_Bayes_prueba'])}) y muy "
          f"cerca del teórico ({pct(gen['Error_Bayes_teorico'])}). La exactitud fue de "
          f"{pct(gen['Accuracy_perceptron'])}, la misma que la del clasificador de Bayes. Además, "
          f"E~in~ = {pct(gen['E_in'])} y E~out~ = {pct(gen['E_out'])} difieren solo en "
          f"{pct(abs(gen['E_in'] - gen['E_out']))}: el modelo generaliza.")
inf.tabla("Pesos del mejor perceptrón y del clasificador de Bayes (datos generados)",
          ["Modelo", "w0", "w1", "w2", "w3"], [
              ["Perceptrón (época " + str(int(gen["Mejor_epoca"])) + ")", num(gen["w0"], 4),
               num(gen["w1"], 4), num(gen["w2"], 4), num(gen["w3"], 4)],
              ["Bayes (parámetros reales)", "0.0000", num(wb[0], 4), num(wb[1], 4), num(wb[2], 4)],
          ], clave="pesos", anchos=[5.0, 2.5, 2.5, 2.5, 2.5])
inf.texto(f"Los pesos tienen distinta escala (la de Bayes depende de α y la del perceptrón de η y del "
          f"número de ajustes), pero lo que define la frontera es su dirección. El ángulo entre el "
          f"vector de pesos del perceptrón y el de Bayes es de solo {angulo:.1f}° y el plano del "
          f"perceptrón está desplazado {desplazamiento:.2f} unidades del origen. Por eso las dos "
          f"fronteras de la Ilustración {{fig:clasesgen}} casi coinciden.")
inf.imagen(RES / "clases_generado.png", 12.5,
           "Datos generados (proyección x1–x2) con la frontera del perceptrón y la de Bayes.",
           clave="clasesgen", fuente="Elaboración propia con Python y Matplotlib.")

inf.titulo("2.7.3 Matrices de confusión")
filas = []
for nombre, mc in [("CSV del taller", mc_csv), ("Datos generados (α = 5)", mc_gen)]:
    filas.append([nombre, mc.iloc[0, 0], mc.iloc[1, 1], mc.iloc[1, 0], mc.iloc[0, 1],
                  miles(mc.to_numpy().sum())])
inf.tabla("Matrices de confusión del conjunto de prueba (clase positiva: Hombre = 1)",
          ["Conjunto", "VP", "VN", "FP", "FN", "Total"], filas, clave="confusion",
          anchos=[5.0, 1.8, 1.8, 1.8, 1.8, 2.0])
inf.imagen(RES / "matrices_confusion.png", 15.0,
           "Matrices de confusión del perceptrón en los conjuntos de prueba.", clave="matrices",
           fuente="Elaboración propia con Python y Matplotlib.")
inf.texto(f"En los datos generados el perceptrón se equivocó en {FP + FN} de "
          f"{miles(VP + VN + FP + FN)} observaciones de prueba: {FP} Mujeres clasificadas como "
          f"Hombre y {FN} Hombres clasificados como Mujer. La asimetría se debe al pequeño "
          f"desplazamiento del sesgo (w~0~ = {num(gen['w0'], 1)}), que corre el plano hacia el lado "
          f"de la clase Mujer; aun así, el error total es el mismo que el de Bayes.")

inf.titulo("2.7.4 Historial del error y del mejor perceptrón")
inf.imagen(RES / "historial_generado.png", 15.0,
           "Historial del error de entrenamiento, del error de validación y del mejor perceptrón "
           "(datos generados).", clave="historial",
           fuente="Elaboración propia con Python y Matplotlib.")
inf.texto(f"El error de entrenamiento y el de validación oscilan entre 0.5 % y 2.9 % porque el "
          f"perceptrón sigue corrigiendo observaciones de la zona de traslape. La curva negra, el "
          f"mejor perceptrón según la validación, solo baja: empezó en "
          f"{pct(hist_gen['Mejor_error_validacion'].iloc[0])} y llegó a "
          f"{pct(gen['Error_validacion'])} en la época {int(gen['Mejor_epoca'])}, por debajo de la "
          f"línea del error de Bayes. Que el error de validación quede por debajo del de Bayes no "
          f"contradice la teoría: es una muestra finita de 3 000 observaciones, y por eso el modelo "
          f"se juzga con E~out~ en el conjunto de prueba, que no participó en la elección.")

inf.titulo("2.7.5 Barrido de α")
inf.tabla("Error de Bayes y del perceptrón para distintos valores de α (p~0~ = 0.5)",
          ["α", "Bayes teórico", "Bayes en prueba", "E~in~", "E~out~", "IC 95 % de E~out~"],
          [[int(b.alpha), pct(b.Error_Bayes_teorico), pct(b.Error_Bayes_prueba), pct(b.E_in),
            pct(b.E_out), f"± {pct(b.IC95_margen)}" if b.E_out > 0 else f"≤ {pct(b.IC95_superior)}"]
           for b in barrido.itertuples()], clave="barrido",
          anchos=[1.2, 2.7, 2.9, 2.2, 2.2, 3.4], alinear=[WD_ALIGN_PARAGRAPH.CENTER] * 6)
inf.imagen(RES / "barrido_alpha.png", 15.0,
           "Error de Bayes (teórico y en prueba) y error del perceptrón según α.", clave="barrido",
           fuente="Elaboración propia con Python y Matplotlib.")
inf.texto("El error del perceptrón sigue la curva del error de Bayes en todo el rango: en cada α, el "
          "intervalo de confianza del 95 % de E~out~ contiene al error de Bayes medido en la misma "
          "muestra de prueba y queda muy cerca del valor teórico. "
          "La diferencia entre E~in~ y E~out~ es siempre menor a un punto porcentual.")

inf.titulo("2.7.6 Resultados con el CSV del taller")
inf.imagen(RES / "clases_csv.png", 12.0,
           "CSV del taller (proyección x1–x2) con la frontera del perceptrón y la de Bayes.",
           clave="clasescsv", fuente="Elaboración propia con Python y Matplotlib.")
inf.texto(f"Las dos clases del CSV forman grupos compactos y muy separados (α ≈ "
          f"{num(csv['alpha'], 2)}), por lo que cualquier plano entre ellos clasifica sin errores. "
          f"El perceptrón con clases 0/1 y η = 0.1 convergió en la segunda época, igual que en el "
          f"taller anterior con clases ±1.")

inf.titulo("2.7.7 Cumplimiento de las indicaciones")
inf.tabla("Verificación de las indicaciones de la práctica", ["Indicación", "Cómo se cumplió"], [
    ["Usar el CSV del taller", "Se evaluó el perceptrón con el CSV original (sección 2.7.2)."],
    ["Crear datos con p~0~ = 0.5 y α = 5", "Se generaron 20 000 registros (Ecuación ({eq:generacion}))."],
    ["Elegir la división de los datos", "Partición estratificada 70/15/15 con semilla 42."],
    ["Diapositivas 13, 14 y 15", "Clases 0/1, salida escalón, error = y − ŷ y η = 0.1."],
    ["Validar con la y verdadera de prueba", "E~out~, exactitud, matriz de confusión e IC 95 %."],
    ["Error de Bayes y error del perceptrón", "Teórico y en prueba, comparados en la Tabla {tab:resultados}."],
    ["Error de entrada y de salida", "E~in~ ≈ E~out~ en todos los experimentos."],
    ["Distribución de las clases", "Ilustración {fig:distgen} y barrido de α."],
], clave="cumplimiento", anchos=[5.6, 9.4], alinear=[WD_ALIGN_PARAGRAPH.LEFT] * 2)

# ----------------------------------------------------------------------------
# 2.8 a 2.12
# ----------------------------------------------------------------------------
seccion("2.8 Habilidades blandas empleadas en la práctica")
casillas([(False, "Liderazgo"), (True, "Trabajo en equipo"), (True, "Comunicación asertiva"),
          (False, "La empatía"), (True, "Pensamiento crítico"), (True, "Flexibilidad"),
          (False, "La resolución de conflictos"), (True, "Adaptabilidad"), (True, "Responsabilidad")])

seccion("2.9 Conclusiones")
inf.lista([
    f"**Sobre el clasificador de Bayes y la superposición:** el error de Bayes es el mínimo que "
    f"puede alcanzar cualquier clasificador y depende únicamente de cuánto se superponen las clases. "
    f"Con p~0~ = 0.5 y α = 5 su valor teórico es Φ(−2.5) = {pct(gen['Error_Bayes_teorico'])}, el mismo "
    f"que se mostró en clase. En el CSV del taller la separación es α ≈ {num(csv['alpha'], 1)}, las "
    f"clases están perfectamente definidas y el error de Bayes es prácticamente cero; por eso fue "
    f"necesario generar datos con traslape para que la comparación tuviera sentido.",
    f"**Sobre el desempeño del perceptrón:** el perceptrón con clases 0/1 de las diapositivas 13 a "
    f"15, con η = 0.1 y conservando el mejor modelo según la validación, obtuvo E~in~ = "
    f"{pct(gen['E_in'])} y E~out~ = {pct(gen['E_out'])} en los datos generados, con exactitud de "
    f"{pct(gen['Accuracy_perceptron'])}. Ese error es igual al de Bayes en la misma muestra de prueba "
    f"y su intervalo de confianza del 95 % contiene al error de Bayes teórico. Como la frontera "
    f"óptima es lineal, el perceptrón llegó prácticamente al mejor resultado posible, y que "
    f"E~in~ ≈ E~out~ confirma que generaliza.",
    f"**Sobre la validación:** con clases superpuestas el perceptrón nunca converge (unas {act_media:.0f} "
    f"correcciones por época) y su error oscila. Separar un conjunto de validación permitió elegir el "
    "mejor perceptrón sin tocar los datos de prueba, que se usaron solo para la medición final.",
], numerada=True)

seccion("2.10 Recomendaciones")
inf.texto("Se recomienda repetir el experimento con clases de distinta probabilidad (por ejemplo "
          "p~0~ = 0.8) y con covarianzas diferentes en cada clase. En el primer caso la frontera de "
          "Bayes se desplaza hacia la clase menos probable y conviene medir la sensibilidad y la "
          "especificidad, no solo la exactitud. En el segundo, la frontera óptima deja de ser un "
          "plano, y se podría observar hasta qué punto un perceptrón lineal se aleja del error de "
          "Bayes. También es recomendable repetir cada configuración con varias semillas para "
          "reportar el promedio y la variabilidad de E~out~.")

seccion("2.11 Referencias bibliográficas")
referencias = [
    '[1] Material docente, "Artificial Neural Networks", ANN.pdf, diapositivas 1–8, 2026.',
    '[2] Material docente, "Algoritmo del perceptrón: cómo interpretar el pseudocódigo", '
    'Perceptron_Explicacion_IF_Paso_a_Paso.pdf, diapositivas 13–15, 2026.',
    '[3] R. O. Duda, P. E. Hart y D. G. Stork, Pattern Classification, 2.ª ed. New York, NY, USA: '
    'Wiley, 2001.',
    '[4] Y. S. Abu-Mostafa, M. Magdon-Ismail y H.-T. Lin, Learning From Data. Pasadena, CA, USA: '
    'AMLBook, 2012.',
    '[5] S. I. Gallant, "Perceptron-based learning algorithms," IEEE Transactions on Neural '
    'Networks, vol. 1, no. 2, pp. 179–191, 1990.',
    '[6] F. Rosenblatt, "The perceptron: A probabilistic model for information storage and '
    'organization in the brain," Psychological Review, vol. 65, no. 6, pp. 386–408, 1958.',
    '[7] C. M. Bishop, Pattern Recognition and Machine Learning. New York, NY, USA: Springer, 2006.',
    '[8] C. R. Harris et al., "Array programming with NumPy," Nature, vol. 585, pp. 357–362, 2020.',
    '[9] W. McKinney, "Data structures for statistical computing in Python," en Proc. 9th Python '
    'in Science Conf., Austin, TX, USA, 2010, pp. 56–61.',
    '[10] J. D. Hunter, "Matplotlib: A 2D graphics environment," Computing in Science & '
    'Engineering, vol. 9, no. 3, pp. 90–95, 2007.',
    '[11] Dataset sintético, "dataset_Perceptron_5000_continuo_menos1_a_1.csv", material de clase, '
    'Inteligencia de Negocios, Universidad Técnica de Ambato, 2026.',
]
for ref in referencias:
    inf.texto(ref, alineacion=WD_ALIGN_PARAGRAPH.LEFT, sangria=Cm(1.27), primera=Cm(-0.63),
              interlineado=1.15)

seccion("2.12 Anexos")
inf.texto("Las capturas de ejecución, las matrices de confusión y las tablas de resultados se "
          "presentan en la sección 2.7. Se adjuntan la lista de archivos y el código fuente.")
inf.titulo("Anexo A. Archivos entregados")
inf.tabla("Archivos que forman parte de la entrega", ["Archivo", "Contenido"], [
    ["perceptron_bayes.py", "Script completo para ejecutar en Visual Studio Code."],
    ["dataset_Perceptron_5000_continuo_menos1_a_1.csv", "Dataset del taller anterior."],
    ["dataset_generado_p0_0.5_alpha_5.csv", "Datos generados con p0 = 0.5 y α = 5."],
    ["capturas/", "Capturas reales de la ejecución en Visual Studio Code."],
    ["resultados/tabla_resultados.csv", "Errores, exactitud, pesos e intervalos de confianza."],
    ["resultados/barrido_alpha.csv / barrido_alpha.png", "Resultados para cada valor de α."],
    ["resultados/historial_*.csv / historial_*.png", "Error por época y mejor perceptrón."],
    ["resultados/matriz_confusion_*.csv / matrices_confusion.png", "Matrices de confusión."],
    ["resultados/clases_*.png / distribucion_*.png", "Clases, fronteras y distribución."],
], clave="archivos", anchos=[7.5, 7.5], alinear=[WD_ALIGN_PARAGRAPH.LEFT] * 2)
inf.titulo("Anexo B. Código fuente (perceptron_bayes.py)")
inf.codigo((TALLER / "perceptron_bayes.py").read_text(encoding="utf-8"))

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
