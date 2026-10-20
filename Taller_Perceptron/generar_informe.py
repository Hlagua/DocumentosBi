"""
Rellena la plantilla del taller (plantilla_taller.docx) con los resultados
generados por perceptron_taller.py y guarda Informe_Taller_Perceptron.docx.

Uso:  python perceptron_taller.py  &&  python generar_informe.py
"""

import copy
from pathlib import Path

import pandas as pd
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Emu, Inches, Pt, RGBColor
from docx.table import Table
from docx.text.paragraph import Paragraph

CARPETA = Path(__file__).resolve().parent
RES = CARPETA / "resultados"
PLANTILLA = CARPETA / "plantilla_taller.docx"
SALIDA = CARPETA / "Informe_Taller_Perceptron.docx"
SANGRIA = Emu(228600)

doc = Document(PLANTILLA)
pesos = pd.read_csv(RES / "pesos_finales.csv", encoding="utf-8-sig")
w = dict(zip(pesos["Parametro"], pesos["Valor"]))
hist = pd.read_csv(RES / "historial_entrenamiento.csv", encoding="utf-8-sig")
tabla = pd.read_csv(RES / "tabla_resultados.csv", encoding="utf-8-sig")
mc_tr = pd.read_csv(RES / "matriz_confusion_entrenamiento.csv", index_col=0, encoding="utf-8-sig")
mc_te = pd.read_csv(RES / "matriz_confusion_prueba.csv", index_col=0, encoding="utf-8-sig")
df = pd.read_csv(CARPETA / "dataset_Perceptron_5000_continuo_menos1_a_1.csv", encoding="utf-8-sig")
ep_conv = int(hist.loc[hist["Errores"] == 0, "Epoca"].min())
actualizaciones = int(hist["Errores"].sum())


# ----------------------------------------------------------------------------
# Utilidades para insertar contenido después de un párrafo de la plantilla
# ----------------------------------------------------------------------------
class Cursor:
    def __init__(self, parrafo):
        self.ultimo = parrafo._p

    def _colocar(self, elemento):
        self.ultimo.addnext(elemento)
        self.ultimo = elemento

    def parrafo(self, texto="", negrita=False, cursiva=False, sangria=SANGRIA,
                centrado=False, tam=None, mono=False):
        p = doc.add_paragraph()
        self._colocar(p._p)
        p.paragraph_format.left_indent = sangria
        p.paragraph_format.space_after = Pt(4)
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER if centrado else WD_ALIGN_PARAGRAPH.JUSTIFY
        # Permite **negritas** dentro del texto
        for k, trozo in enumerate(texto.split("**")):
            if not trozo:
                continue
            r = p.add_run(trozo)
            r.bold = negrita or k % 2 == 1
            r.italic = cursiva
            if tam:
                r.font.size = Pt(tam)
            if mono:
                r.font.name = "Consolas"
                r._element.rPr.rFonts.set(qn("w:eastAsia"), "Consolas")
        return p

    def vineta(self, texto):
        p = self.parrafo("• " + texto, sangria=Emu(SANGRIA + 228600))
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        return p

    def codigo(self, texto):
        for linea in texto.strip("\n").split("\n"):
            p = self.parrafo(linea if linea else " ", mono=True, tam=8.5,
                             sangria=Emu(SANGRIA + 114300))
            p.paragraph_format.space_after = Pt(0)
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        self.parrafo("")

    def imagen(self, ruta, ancho=5.3, pie=None):
        p = self.parrafo("", centrado=True, sangria=0)
        p.add_run().add_picture(str(ruta), width=Inches(ancho))
        if pie:
            self.parrafo(pie, cursiva=True, centrado=True, sangria=0, tam=9)

    def tabla(self, encabezado, filas, pie=None, anchos=None):
        t = doc.add_table(rows=1, cols=len(encabezado))
        t.style = "Table Grid"
        t.alignment = 1
        for c, txt in zip(t.rows[0].cells, encabezado):
            c.text = ""
            r = c.paragraphs[0].add_run(str(txt))
            r.bold = True
            r.font.size = Pt(9.5)
            r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
            sombra = c._tc.get_or_add_tcPr().makeelement(qn("w:shd"), {
                qn("w:val"): "clear", qn("w:color"): "auto", qn("w:fill"): "1F4E79"})
            c._tc.get_or_add_tcPr().append(sombra)
        for fila in filas:
            celdas = t.add_row().cells
            for c, txt in zip(celdas, fila):
                c.text = ""
                r = c.paragraphs[0].add_run(str(txt))
                r.font.size = Pt(9.5)
        if anchos:
            for fila in t.rows:
                for c, a in zip(fila.cells, anchos):
                    c.width = Inches(a)
        self._colocar(t._tbl)
        if pie:
            self.parrafo(pie, cursiva=True, centrado=True, sangria=0, tam=9)
        else:
            self.parrafo("")


def buscar(texto_inicio):
    for p in doc.paragraphs:
        if p.text.strip().startswith(texto_inicio):
            return p
    raise ValueError(f"No se encontró el párrafo: {texto_inicio}")


def reemplazar_texto(parrafo, texto):
    for r in parrafo.runs[1:]:
        r._element.getparent().remove(r._element)
    parrafo.runs[0].text = texto


def f4(v):
    return f"{v:.4f}"


# ----------------------------------------------------------------------------
# Actividad 1. Estructura del perceptrón
# ----------------------------------------------------------------------------
c = Cursor(buscar("Actividad 1."))
c.parrafo("Siguiendo la diapositiva 4 de ANN.pdf, el perceptrón es una sola neurona "
          "que recibe un vector de entradas X aumentado con una entrada constante igual "
          "a 1. Cada entrada se multiplica por su peso, se suman los productos y el "
          "resultado pasa por una función escalón que entrega la clase.")
c.tabla(["Elemento", "Símbolo", "En este taller"], [
    ["Entrada 1", "x1", "Caracteristica_1 (continua en [-1, 1])"],
    ["Entrada 2", "x2", "Caracteristica_2 (continua en [-1, 1])"],
    ["Entrada 3", "x3", "Caracteristica_3 (continua en [-1, 1])"],
    ["Entrada de sesgo", "x0 = 1", "Columna de unos agregada a la matriz X"],
    ["Pesos", "w1, w2, w3", "Importancia de cada característica (inician en 0)"],
    ["Sesgo", "w0", "Desplaza la frontera de decisión (inicia en 0)"],
    ["Suma ponderada", "f(x)", "f(x) = w0 + w1·x1 + w2·x2 + w3·x3"],
    ["Activación", "escalón", "ŷ = 1 (Hombre) si f(x) ≥ 0; ŷ = -1 (Mujer) en otro caso"],
], pie="Tabla 1. Componentes del perceptrón identificados en el modelo.",
   anchos=[1.4, 1.0, 3.3])
c.parrafo("La diapositiva usa salidas 1/0; como la guía pide codificar Hombre = 1 y "
          "Mujer = -1, la función escalón se expresa con salidas +1/-1. Así la condición "
          "de error del seudocódigo, y·f(x) ≤ 0, se cumple exactamente cuando el signo "
          "de la predicción no coincide con la clase real.")

# ----------------------------------------------------------------------------
# Actividad 2. Preparación de los datos
# ----------------------------------------------------------------------------
c = Cursor(buscar("Actividad 2."))
c.parrafo(f"El archivo se leyó con pandas: {len(df):,}".replace(",", " ") + " registros, 3 características "
          f"numéricas y la columna Clase. No hay valores nulos ({int(df.isna().sum().sum())}) "
          f"ni filas duplicadas ({int(df.duplicated().sum())}), y las clases están "
          f"balanceadas (2 500 Hombre y 2 500 Mujer).")
c.vineta("Codificación de la clase: Hombre → 1, Mujer → -1 (columna y).")
c.vineta("Se agregó la columna x0 = 1 para tratar el sesgo w0 como un peso más.")
c.vineta("División estratificada 80/20 con semilla 42: 4 000 registros de "
         "entrenamiento y 1 000 de prueba, 50 % de cada clase en ambos.")
c.vineta("Los datos ya están en el rango [-1, 1], por lo que no se requiere normalizar.")
filas = []
for col in ["Caracteristica_1", "Caracteristica_2", "Caracteristica_3"]:
    g = df.groupby("Clase")[col]
    filas.append([col,
                  f"{g.mean()['Hombre']:.3f} ({g.min()['Hombre']:.3f} a {g.max()['Hombre']:.3f})",
                  f"{g.mean()['Mujer']:.3f} ({g.min()['Mujer']:.3f} a {g.max()['Mujer']:.3f})"])
c.tabla(["Variable", "Hombre: media (mín. a máx.)", "Mujer: media (mín. a máx.)"], filas,
        pie="Tabla 2. Estadística descriptiva por clase.", anchos=[1.6, 2.1, 2.1])
c.parrafo("Las medias de cada característica son positivas para Hombre y negativas para "
          "Mujer, y en Caracteristica_3 los rangos ni siquiera se tocan (Hombre ≥ 0.438, "
          "Mujer ≤ -0.450). Esto anticipa que las clases son linealmente separables, "
          "condición bajo la cual el perceptrón converge (diapositiva 4).")
c.codigo('''
df = pd.read_csv("dataset_Perceptron_5000_continuo_menos1_a_1.csv", encoding="utf-8-sig")
df["y"] = df["Clase"].map({"Hombre": 1, "Mujer": -1})
train, test = dividir_estratificado(df, 0.2, semilla=42)
X = np.hstack([np.ones((len(train), 1)), train[["Caracteristica_1",
               "Caracteristica_2", "Caracteristica_3"]].to_numpy()])   # x0 = 1
''')

# ----------------------------------------------------------------------------
# Actividad 3. Entrenamiento
# ----------------------------------------------------------------------------
c = Cursor(buscar("Actividad 3."))
c.parrafo("El entrenamiento traduce línea por línea el seudocódigo de la diapositiva 4. "
          "No se usa scikit-learn: solo NumPy para el producto punto y la suma de vectores.")
c.tabla(["Paso del seudocódigo", "Implementación en Python"], [
    ["2. Inicializar wj = 0, ∀j ∈ {0,…,d}", "w = np.zeros(4)  →  w0 = w1 = w2 = w3 = 0"],
    ["3. Repetir hasta convergencia", "for epoca in range(1, 201)  (200 épocas)"],
    ["4. Para cada ejemplo xi", "for xi, yi in zip(X, y)"],
    ["5. Si yi·f(xi) ≤ 0  (¿error?)", "if yi * np.dot(w, xi) <= 0"],
    ["6. wj := wj + yi·xij  (ajustar pesos)", "w = w + yi * xi"],
], pie="Tabla 3. Correspondencia entre el seudocódigo y el código.", anchos=[2.6, 3.1])
c.codigo('''
def entrenar_perceptron(X, y, epocas=200):
    w = np.zeros(X.shape[1])                 # paso 2: pesos y sesgo en 0
    for epoca in range(1, epocas + 1):       # paso 3: repetir
        errores = 0
        for xi, yi in zip(X, y):             # paso 4: para cada ejemplo
            if yi * np.dot(w, xi) <= 0:      # paso 5: ¿error?
                w = w + yi * xi              # paso 6: ajustar los pesos
                errores += 1
    return w
''')
c.parrafo(f"Resultado: en la época 1 el modelo cometió solo {int(hist.loc[0, 'Errores'])} "
          f"errores (los dos primeros ejemplos vistos, cuando los pesos aún valían 0). El "
          f"primero, un Hombre, sumó su vector a w; el segundo, una Mujer, lo restó. Desde "
          f"la época {ep_conv} no hubo ningún error y los pesos permanecieron constantes "
          f"hasta completar las 200 épocas. En total se hicieron {actualizaciones} "
          f"actualizaciones de pesos.")
c.imagen(RES / "convergencia.png", 5.4,
         "Figura 1. Ejemplos mal clasificados por época (se muestran las primeras 20 de 200).")

# ----------------------------------------------------------------------------
# Actividad 4. Evaluación
# ----------------------------------------------------------------------------
c = Cursor(buscar("Actividad 4."))
c.parrafo("Con los pesos finales se clasificaron los conjuntos de entrenamiento y de "
          "prueba. La clase positiva es Hombre (1).")
for nombre, mc, n in [("entrenamiento", mc_tr, 4), ("prueba", mc_te, 5)]:
    c.tabla(["", mc.columns[0], mc.columns[1]],
            [[mc.index[i], mc.iloc[i, 0], mc.iloc[i, 1]] for i in range(2)],
            pie=f"Tabla {n}. Matriz de confusión del conjunto de {nombre}.",
            anchos=[1.8, 1.8, 1.8])
filas = [[r.Conjunto, int(r.n), f"{r.Exactitud:.2%}", f"{r.Precision:.2%}",
          f"{r.Sensibilidad:.2%}", f"{r.Especificidad:.2%}", f"{r.F1:.4f}"]
         for r in tabla.itertuples()]
c.tabla(["Conjunto", "n", "Exactitud", "Precisión", "Sensibilidad", "Especificidad", "F1"],
        filas, pie="Tabla 6. Tabla de resultados.")
c.parrafo("El perceptrón clasificó correctamente los 4 000 registros de entrenamiento y "
          "los 1 000 de prueba: no hay falsos positivos ni falsos negativos. La exactitud "
          "en prueba (100 %) confirma que el modelo generaliza a datos que no vio durante "
          "el entrenamiento.")
c.imagen(RES / "matriz_confusion_prueba.png", 3.6,
         "Figura 2. Matriz de confusión en el conjunto de prueba.")

# ----------------------------------------------------------------------------
# Actividad 5. Interpretación
# ----------------------------------------------------------------------------
c = Cursor(buscar("Actividad 5."))
c.parrafo("**Pesos finales del perceptrón:**")
c.tabla(["Parámetro", "Valor", "Interpretación"], [
    ["w0 (sesgo)", f4(w["w0"]), "La frontera pasa por el origen: las clases son simétricas respecto a 0."],
    ["w1", f4(w["w1"]), "Mayor peso: x1 es la característica más influyente."],
    ["w2", f4(w["w2"]), "Peso menor: x2 tiene menor rango y menor separación entre clases."],
    ["w3", f4(w["w3"]), "Peso alto: x3 separa por sí sola las dos clases."],
], pie="Tabla 7. Pesos finales.", anchos=[1.1, 0.9, 3.7])
c.parrafo(f"La frontera de decisión aprendida es el plano "
          f"**{w['w1']:.3f}·x1 + {w['w2']:.3f}·x2 + {w['w3']:.3f}·x3 = 0**. Todos los pesos "
          f"son positivos, de modo que valores altos de las características empujan la "
          f"predicción hacia Hombre (1) y valores bajos hacia Mujer (-1). El sesgo quedó en 0 "
          f"porque las dos actualizaciones se compensaron (+1 por el Hombre y -1 por la Mujer); "
          f"esto es coherente con datos centrados en el origen.")
c.parrafo("El punto más cercano al plano está a 0.72 unidades de distancia, un margen amplio "
          "frente al rango de los datos. Por eso bastaron dos ajustes: con un problema "
          "linealmente separable, el perceptrón encuentra un hiperplano que separa las "
          "clases, como indica la diapositiva 4. El perceptrón no busca el margen máximo; "
          "se detiene en la primera frontera que no comete errores.")
c.parrafo("Ejemplo de uso: para x = (0.5, 0.3, 0.6), f(x) = 0 + 1.345·0.5 + 0.835·0.3 + "
          "1.293·0.6 = 1.699 ≥ 0, por lo que el modelo predice Hombre.")
c.imagen(RES / "frontera_decision.png", 4.2,
         "Figura 3. Proyección x1–x3 de las clases y frontera de decisión (x2 fijada en su media).")

# "Liste los pesos finales" quedó en la plantilla bajo Habilidades blandas;
# los pesos se reportan en la Actividad 5, así que se elimina esa línea suelta.
suelto = buscar("Liste los pesos finales")
suelto._p.getparent().remove(suelto._p)

# ----------------------------------------------------------------------------
# 2.9 Conclusiones y 2.10 Recomendaciones
# ----------------------------------------------------------------------------
p = buscar("Redacte dos conclusiones")
reemplazar_texto(p, "1. Sobre el funcionamiento: el perceptrón implementado desde cero con "
                 "la regla de la diapositiva 4 (si y·f(x) ≤ 0, entonces w := w + y·x) aprende "
                 "sin tasa de aprendizaje ni derivadas; solo corrige los pesos cuando se "
                 "equivoca. Partiendo de pesos y sesgo en 0, bastaron 2 actualizaciones en la "
                 "primera época para fijar la frontera, y en las 199 épocas restantes no hubo "
                 "ningún cambio, lo que evidencia la convergencia.")
c = Cursor(p)
c.parrafo("2. Sobre el desempeño: con el dataset sintético de 5 000 registros, el modelo "
          "alcanzó 100 % de exactitud, precisión, sensibilidad y especificidad tanto en "
          "entrenamiento (4 000) como en prueba (1 000), con matrices de confusión sin "
          "errores. Este resultado se explica porque las clases son linealmente separables "
          "(en x3 los rangos de Hombre y Mujer no se superponen), y los pesos finales "
          "(w1 = 1.345, w2 = 0.835, w3 = 1.293, w0 = 0) muestran que x1 y x3 son las "
          "características más discriminantes.")

p = buscar("Proponga una recomendación")
reemplazar_texto(p, "Evaluar la robustez del mismo perceptrón simple con datos menos ideales: "
                 "agregar ruido gaussiano a las características o invertir un porcentaje de "
                 "etiquetas (por ejemplo, 5 % y 10 %) para obtener clases que se superpongan. "
                 "En ese escenario el perceptrón ya no converge, por lo que conviene registrar "
                 "el número de errores por época, guardar los mejores pesos (variante "
                 "«pocket») y comparar la exactitud en prueba con validación cruzada de 5 "
                 "particiones y distintas semillas de barajado.")

# Referencia [2]: la plantilla cita el dataset de Bayes; se corrige al usado
p = buscar("[2] Dataset sintético")
reemplazar_texto(p, '[2] Dataset sintético, "dataset_Perceptron_5000_continuo_menos1_a_1.csv", '
                    'material de clase, 2026.')

# ----------------------------------------------------------------------------
# 2.12 Anexos
# ----------------------------------------------------------------------------
c = Cursor(buscar("Anexar:"))
c.parrafo("**Anexo A. Archivos entregados**", sangria=Emu(540385))
for linea in ["perceptron_taller.py: script completo (lectura, entrenamiento, evaluación y gráficos).",
              "perceptron_taller.ipynb: el mismo código organizado por actividades para Jupyter/Colab.",
              "resultados/: tabla_resultados.csv, pesos_finales.csv, historial_entrenamiento.csv, "
              "matrices de confusión (.csv y .png) y figuras."]:
    c.parrafo("• " + linea, sangria=Emu(540385 + 228600)).alignment = WD_ALIGN_PARAGRAPH.LEFT
c.parrafo("**Anexo B. Captura de ejecución (salida de consola)**", sangria=Emu(540385))
c.codigo((RES / "salida_consola.txt").read_text(encoding="utf-8"))
c.parrafo("**Anexo C. Matriz de confusión del conjunto de entrenamiento**", sangria=Emu(540385))
c.imagen(RES / "matriz_confusion_entrenamiento.png", 3.6)
c.parrafo("**Anexo D. Código fuente**", sangria=Emu(540385))
c.codigo((CARPETA / "perceptron_taller.py").read_text(encoding="utf-8"))

doc.save(SALIDA)
print("Informe generado:", SALIDA)
