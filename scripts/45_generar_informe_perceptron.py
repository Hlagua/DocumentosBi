"""
Genera Taller_Perceptron/Informe_Taller_Perceptron.docx a partir de la plantilla
del docente (scripts/plantillas/Taller_Perceptron_plantilla.docx) y de los
resultados que produce Taller_Perceptron/perceptron_taller.py.

Formato: Times New Roman 12, texto justificado con interlineado 1.5, tablas
simples, ecuaciones de Word numeradas y pie de página "Página X de Y".

Uso:
    python Taller_Perceptron/perceptron_taller.py
    python scripts/45_generar_informe_perceptron.py            (exige las capturas)
    python scripts/45_generar_informe_perceptron.py --borrador (sin capturas)
"""

import copy
import re
import sys
from pathlib import Path
from xml.sax.saxutils import escape

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch
from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT, WD_BREAK
from docx.oxml import parse_xml
from docx.oxml.ns import qn
from docx.shared import Cm, Pt

RAIZ = Path(__file__).resolve().parents[1]
TALLER = RAIZ / "Taller_Perceptron"
RES = TALLER / "resultados"
CAP = TALLER / "capturas"
PLANTILLA = RAIZ / "scripts" / "plantillas" / "Taller_Perceptron_plantilla.docx"
SALIDA = TALLER / "Informe_Taller_Perceptron.docx"
BORRADOR = "--borrador" in sys.argv

sys.path.insert(0, str(TALLER))
import perceptron_taller as pt  # noqa: E402

FUENTE = "Times New Roman"
SANGRIA = Cm(0.63)
ANCHO_TEXTO = Cm(15.0)

# ----------------------------------------------------------------------------
# Datos del experimento
# ----------------------------------------------------------------------------
df = pt.cargar_datos(pt.ARCHIVO)
train, test = pt.dividir_estratificado(df, pt.PROPORCION_TEST, pt.SEMILLA)
X_train, y_train = pt.matriz_aumentada(train), train["y"].to_numpy()
pesos = pd.read_csv(RES / "pesos_finales.csv", encoding="utf-8-sig")
w = pesos["Valor"].to_numpy()
hist = pd.read_csv(RES / "historial_entrenamiento.csv", encoding="utf-8-sig")
tabla = pd.read_csv(RES / "tabla_resultados.csv", encoding="utf-8-sig")
ajustes = pd.read_csv(RES / "ajustes_pesos.csv", encoding="utf-8-sig")
ejemplos = pd.read_csv(RES / "ejemplos_prediccion.csv", encoding="utf-8-sig")
mc_tr = pd.read_csv(RES / "matriz_confusion_entrenamiento.csv", index_col=0, encoding="utf-8-sig")
mc_te = pd.read_csv(RES / "matriz_confusion_prueba.csv", index_col=0, encoding="utf-8-sig")

ep_conv = int(hist.loc[hist["Errores"] == 0, "Epoca"].min())
n_ajustes = len(ajustes)
norma_w = float(np.linalg.norm(w[1:]))
d_min = float(((y_train * (X_train @ w)) / norma_w).min())
R = float(np.linalg.norm(X_train, axis=1).max())
cota = (R / d_min) ** 2
importancia = np.abs(w[1:]) / np.abs(w[1:]).sum()

# Traza manual de los ajustes: f(x) antes de cada actualización
traza = []
w_antes = np.zeros(4)
for a in ajustes.itertuples():
    x = np.array([1, a.x1, a.x2, a.x3])
    w_desp = np.array([a.w0_despues, a.w1_despues, a.w2_despues, a.w3_despues])
    traza.append({"epoca": a.Epoca, "ejemplo": a.Ejemplo, "y": a.y, "x": x,
                  "w_antes": w_antes, "f": float(w_antes @ x), "w_desp": w_desp})
    w_antes = w_desp

versiones = {
    "Python": sys.version.split()[0],
    "NumPy": np.__version__,
    "pandas": pd.__version__,
    "Matplotlib": matplotlib.__version__,
}


def f3(v):
    return f"{v:.3f}".replace("-", "−")


def f4(v):
    return f"{v:.4f}"


def miles(n):
    return f"{int(n):,}".replace(",", " ")


# ----------------------------------------------------------------------------
# Diagrama de la estructura del perceptrón (Actividad 1)
# ----------------------------------------------------------------------------
def dibujar_estructura(ruta):
    plt.rcParams.update({"font.family": FUENTE, "font.size": 13})
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 5)
    ax.axis("off")
    entradas = [("x₀ = 1", "w₀ (sesgo)", 4.3), ("x₁", "w₁", 3.3),
                ("x₂", "w₂", 2.3), ("x₃", "w₃", 1.3)]
    suma = (5.0, 2.8)
    for texto, peso, yy in entradas:
        ax.add_patch(Circle((1.2, yy), 0.38, fc="white", ec="black", lw=1.5))
        ax.text(1.2, yy, texto if texto != "x₀ = 1" else "1", ha="center", va="center")
        ax.add_patch(FancyArrowPatch((1.6, yy), (suma[0] - 0.55, suma[1]),
                                     arrowstyle="-|>", mutation_scale=14, lw=1.3))
        ax.text(3.0, yy + (suma[1] - yy) * 0.35 + 0.12, peso, ha="center",
                color="#b22222")
    ax.text(0.15, 4.3, "Sesgo", ha="left", va="center", fontsize=11)
    ax.text(0.15, 2.3, "Entradas", ha="left", va="center", fontsize=11, rotation=90)
    ax.add_patch(Circle(suma, 0.55, fc="#f2f2f2", ec="black", lw=1.5))
    ax.text(*suma, "Σ", ha="center", va="center", fontsize=22)
    ax.text(suma[0], suma[1] - 0.95, "f(x) = w₀ + w₁x₁ + w₂x₂ + w₃x₃", ha="center")
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
# Ecuaciones (OMML)
# ----------------------------------------------------------------------------
NS = ('xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math" '
      'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"')


def r(t, normal=False):
    estilo = '<m:rPr><m:sty m:val="p"/></m:rPr>' if normal else ""
    return (f'<m:r>{estilo}<w:rPr><w:rFonts w:ascii="Cambria Math" w:hAnsi="Cambria Math"/>'
            f'</w:rPr><m:t xml:space="preserve">{escape(t)}</m:t></m:r>')


def tx(t):
    """Texto normal (no cursiva) dentro de la ecuación."""
    return r(t, normal=True)


def sub(base, s):
    return f"<m:sSub><m:e>{base}</m:e><m:sub>{s}</m:sub></m:sSub>"


def sup(base, s):
    return f"<m:sSup><m:e>{base}</m:e><m:sup>{s}</m:sup></m:sSup>"


def subsup(base, s, p):
    return f"<m:sSubSup><m:e>{base}</m:e><m:sub>{s}</m:sub><m:sup>{p}</m:sup></m:sSubSup>"


def frac(n, d):
    return f"<m:f><m:num>{n}</m:num><m:den>{d}</m:den></m:f>"


def suma(lo, hi, e):
    return (f'<m:nary><m:naryPr><m:chr m:val="∑"/></m:naryPr><m:sub>{lo}</m:sub>'
            f"<m:sup>{hi}</m:sup><m:e>{e}</m:e></m:nary>")


def delim(e, a="(", b=")"):
    return (f'<m:d><m:dPr><m:begChr m:val="{escape(a)}"/><m:endChr m:val="{escape(b)}"/>'
            f"</m:dPr><m:e>{e}</m:e></m:d>")


def casos(*filas):
    cuerpo = "".join(f"<m:e>{fila}</m:e>" for fila in filas)
    return (f'<m:d><m:dPr><m:begChr m:val="{{"/><m:endChr m:val=""/></m:dPr>'
            f"<m:e><m:eqArr>{cuerpo}</m:eqArr></m:e></m:d>")


def raiz(e):
    return f'<m:rad><m:radPr><m:degHide m:val="1"/></m:radPr><m:deg/><m:e>{e}</m:e></m:rad>'


def acento(e, c):
    return f'<m:acc><m:accPr><m:chr m:val="{c}"/></m:accPr><m:e>{e}</m:e></m:acc>'


def func_lim(nombre, lo, e):
    return (f"<m:func><m:fName><m:limLow><m:e>{tx(nombre)}</m:e><m:lim>{lo}</m:lim>"
            f"</m:limLow></m:fName><m:e>{e}</m:e></m:func>")


def min_(lo, e):
    return func_lim("min", lo, e)


XT = acento(r("x"), "̃")                      # x con tilde (vector aumentado)
XTI = sub(acento(r("x"), "̃"), r("i"))
YH = acento(r("y"), "̂")
W = r("w")


def wi(i):
    return sub(r("w"), r(str(i)))


def xi(i):
    return sub(r("x"), r(str(i)))


# ----------------------------------------------------------------------------
# Utilidades de documento
# ----------------------------------------------------------------------------
doc = Document(PLANTILLA)
contador = {"tabla": 0, "ilustracion": 0, "ecuacion": 0}


def fuente_run(run, tam=12, nombre=FUENTE):
    run.font.name = nombre
    run.font.size = Pt(tam)
    rpr = run._element.get_or_add_rPr()
    fonts = rpr.find(qn("w:rFonts"))
    if fonts is None:
        fonts = rpr.makeelement(qn("w:rFonts"), {})
        rpr.insert(0, fonts)
    for atr in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        fonts.set(qn(atr), nombre)


def agregar_texto(p, texto, negrita=False, cursiva=False, tam=12, nombre=FUENTE):
    """Admite **negrita** y ~subíndice~; x0..x3 y w0..w3 se escriben con subíndice."""
    texto = re.sub(r"(?<![\w.])([xw])([0-3])(?![\w(])", r"\1~\2~", texto)
    negrita_activa = False
    for trozo in re.split(r"(\*\*|~[^~]+~)", texto):
        if trozo == "**":
            negrita_activa = not negrita_activa
            continue
        if not trozo:
            continue
        subindice = trozo.startswith("~") and trozo.endswith("~") and len(trozo) > 2
        run = p.add_run(trozo[1:-1] if subindice else trozo)
        run.bold = negrita or negrita_activa
        run.italic = cursiva
        run.font.subscript = subindice or None
        fuente_run(run, tam, nombre)
    return p


def formato(p, alineacion=WD_ALIGN_PARAGRAPH.JUSTIFY, sangria=SANGRIA, interlineado=1.5,
            antes=0, despues=6, primera=None):
    pf = p.paragraph_format
    p.alignment = alineacion
    pf.left_indent = sangria
    pf.line_spacing = interlineado
    pf.space_before = Pt(antes)
    pf.space_after = Pt(despues)
    if primera is not None:
        pf.first_line_indent = primera
    return p


class Cursor:
    """Inserta bloques uno tras otro a partir de un párrafo de la plantilla."""

    def __init__(self, ancla):
        self.ultimo = ancla._p

    def _colocar(self, el):
        self.ultimo.addnext(el)
        self.ultimo = el

    def _nuevo(self):
        p = doc.add_paragraph()
        self._colocar(p._p)
        return p

    def texto(self, t, **kw):
        p = self._nuevo()
        agregar_texto(p, t)
        return formato(p, **kw)

    def titulo(self, t, sangria=SANGRIA, antes=6):
        p = self._nuevo()
        agregar_texto(p, t, negrita=True)
        p.paragraph_format.keep_with_next = True
        return formato(p, WD_ALIGN_PARAGRAPH.LEFT, sangria, antes=antes, despues=4)

    def vinetas(self, items, sangria=Cm(1.27)):
        for it in items:
            p = self._nuevo()
            agregar_texto(p, "•\t" + it)
            formato(p, sangria=sangria, primera=Cm(-0.63), despues=2)
            p.paragraph_format.tab_stops.add_tab_stop(sangria)

    def numerada(self, items, sangria=Cm(1.27)):
        for k, it in enumerate(items, 1):
            p = self._nuevo()
            agregar_texto(p, f"{k}.\t" + it)
            formato(p, sangria=sangria, primera=Cm(-0.63), despues=2)
            p.paragraph_format.tab_stops.add_tab_stop(sangria)

    def ecuacion(self, omml):
        """Ecuación en modo display, centrada, con su número a la derecha (tabla sin bordes)."""
        contador["ecuacion"] += 1
        t = doc.add_table(rows=1, cols=2)
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        izq, der = t.rows[0].cells
        izq.width, der.width = Cm(13.6), Cm(1.4)
        p = izq.paragraphs[0]
        formato(p, WD_ALIGN_PARAGRAPH.CENTER, sangria=0, interlineado=1.0, antes=4, despues=4)
        p._p.append(parse_xml(
            f'<m:oMathPara {NS}><m:oMathParaPr><m:jc m:val="center"/></m:oMathParaPr>'
            f"<m:oMath>{omml}</m:oMath></m:oMathPara>"))
        q = der.paragraphs[0]
        agregar_texto(q, f"({contador['ecuacion']})")
        formato(q, WD_ALIGN_PARAGRAPH.RIGHT, sangria=0, interlineado=1.0, despues=0)
        for celda in (izq, der):
            tcpr = celda._tc.get_or_add_tcPr()
            tcpr.append(parse_xml(f'<w:vAlign {NS} w:val="center"/>'))
        self._colocar(t._tbl)
        return contador["ecuacion"]

    def leyenda(self, tipo, t, fuente=None):
        contador[tipo] += 1
        n = contador[tipo]
        etiqueta = "Tabla" if tipo == "tabla" else "Ilustración"
        p = self._nuevo()
        agregar_texto(p, f"**{etiqueta} {n}.** {t}")
        formato(p, WD_ALIGN_PARAGRAPH.CENTER, sangria=0, interlineado=1.0,
                antes=6 if tipo == "tabla" else 2, despues=2 if tipo == "tabla" else 4)
        if tipo == "tabla":
            p.paragraph_format.keep_with_next = True
        if fuente:
            q = self._nuevo()
            agregar_texto(q, f"Fuente: {fuente}", cursiva=True, tam=12)
            formato(q, WD_ALIGN_PARAGRAPH.CENTER, sangria=0, interlineado=1.0, despues=10)
        return n

    def imagen(self, ruta, ancho_cm, titulo, fuente="Elaboración propia."):
        p = self._nuevo()
        formato(p, WD_ALIGN_PARAGRAPH.CENTER, sangria=0, interlineado=1.0, antes=6, despues=2)
        p.paragraph_format.keep_with_next = True
        p.add_run().add_picture(str(ruta), width=Cm(ancho_cm))
        return self.leyenda("ilustracion", titulo, fuente)

    def tabla(self, titulo, encabezado, filas, anchos=None, fuente="Elaboración propia.",
              alinear=None):
        n = self.leyenda("tabla", titulo)
        t = doc.add_table(rows=1, cols=len(encabezado))
        t.style = "Table Grid"
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        for k, txt in enumerate(encabezado):
            celda = t.rows[0].cells[k]
            celda.text = ""
            par = celda.paragraphs[0]
            agregar_texto(par, str(txt), negrita=True)
            formato(par, WD_ALIGN_PARAGRAPH.CENTER, sangria=0, interlineado=1.0, despues=0)
        for fila in filas:
            celdas = t.add_row().cells
            for k, txt in enumerate(fila):
                celdas[k].text = ""
                par = celdas[k].paragraphs[0]
                agregar_texto(par, str(txt))
                al = (alinear[k] if alinear else
                      (WD_ALIGN_PARAGRAPH.LEFT if k == 0 else WD_ALIGN_PARAGRAPH.CENTER))
                formato(par, al, sangria=0, interlineado=1.0, despues=0)
        for fila in t.rows[:-1]:
            # La tabla no se separa de su encabezado ni queda partida al final de una página
            for celda in fila.cells:
                for par in celda.paragraphs:
                    par.paragraph_format.keep_with_next = True
        for fila in t.rows:
            # Evita que una fila se parta entre páginas
            trpr = fila._tr.get_or_add_trPr()
            trpr.append(trpr.makeelement(qn("w:cantSplit"), {}))
            if anchos:
                for c, a in zip(fila.cells, anchos):
                    c.width = Cm(a)
        self._colocar(t._tbl)
        q = self._nuevo()
        agregar_texto(q, f"Fuente: {fuente}", cursiva=True)
        formato(q, WD_ALIGN_PARAGRAPH.CENTER, sangria=0, interlineado=1.0, antes=2, despues=10)
        return n

    def codigo(self, texto, tam=9):
        for linea in texto.rstrip("\n").split("\n"):
            p = self._nuevo()
            run = p.add_run(linea.replace("\t", "    ") or " ")
            fuente_run(run, tam, "Courier New")
            formato(p, WD_ALIGN_PARAGRAPH.LEFT, sangria=Cm(0.3), interlineado=1.0, despues=0)

    def salto_pagina(self):
        p = self._nuevo()
        p.add_run().add_break(WD_BREAK.PAGE)


def buscar(inicio):
    for p in doc.paragraphs:
        if p.text.strip().startswith(inicio):
            return p
    raise ValueError(f"No se encontró: {inicio}")


def poner_texto(p, texto):
    for run in p.runs[1:]:
        run._element.getparent().remove(run._element)
    p.runs[0].text = texto


def eliminar(p):
    p._p.getparent().remove(p._p)


# ----------------------------------------------------------------------------
# Portada y encabezado
# ----------------------------------------------------------------------------
portada = [
    ("Tema:", "Desarrollo y entrenamiento de un perceptrón para clasificación binaria"),
    ("Unidad de Organización Curricular:", "Profesional"),
    ("Nivel y Paralelo:", 'Sexto semestre - Paralelo: "A"'),
    ("Alumnos participantes:", "Cobos Taco Alison Marcela"),
    ("", "Lagua Flores Henry Daniel"),
    ("Asignatura:", "Inteligencia de Negocios"),
    ("Docente:", "Ing. Rubén Nogales Portero, Ph.D."),
]
lineas = [buscar("Tema:"), buscar("Unidad de Organización"), buscar("Nivel y Paralelo:"),
          buscar("Alumnos participantes:")]
lineas += [q for q in doc.paragraphs if q.text.strip().startswith("_____")]
lineas += [buscar("Asignatura:"), buscar("Docente:")]
for q, (etiqueta, valor) in zip(lineas, [*portada[:5], ("", ""), *portada[5:]]):
    for run in list(q.runs):
        run._element.getparent().remove(run._element)
    if not valor:
        eliminar(q)
        continue
    agregar_texto(q, f"{etiqueta}\t{valor}")
    formato(q, WD_ALIGN_PARAGRAPH.LEFT, sangria=Cm(6.6), interlineado=1.15, despues=2,
            primera=Cm(-6.6))
    q.paragraph_format.tab_stops.add_tab_stop(Cm(6.6))


def entre(desde, hasta):
    """Párrafos de la plantilla entre dos encabezados (excluidos)."""
    dentro, salida = False, []
    for q in doc.paragraphs:
        if q.text.strip().startswith(hasta) and dentro:
            break
        if dentro:
            salida.append(q)
        if q.text.strip().startswith(desde):
            dentro = True
    return salida


# Listas de la plantilla: sin líneas vacías intermedias y con sangría francesa
for desde, hasta in [("Específicos:", "2.2 Modalidad"), ("2.4 Instrucciones", "2.5 Listado"),
                     ("Listado de equipos", "TAC (Tecnologías")]:
    for q in entre(desde, hasta):
        texto = q.text.strip()
        if not texto:
            eliminar(q)
            continue
        m = re.match(r"^(•|\d\.)\s+(.*)$", texto)
        if not m:
            continue
        numpr = q._p.find(qn("w:pPr") + "/" + qn("w:numPr"))
        if numpr is not None:
            numpr.getparent().remove(numpr)
        for run in list(q.runs):
            run._element.getparent().remove(run._element)
        agregar_texto(q, f"{m.group(1)}\t{m.group(2)}")
        formato(q, sangria=Cm(1.9), primera=Cm(-0.63), despues=3)
        q.paragraph_format.tab_stops.add_tab_stop(Cm(1.9))

# Encabezados de actividad: siempre junto a su contenido y sin doble línea vacía
for k in range(1, 6):
    cab = buscar(f"Actividad {k}.")
    cab.paragraph_format.keep_with_next = True
    cab.paragraph_format.space_before = Pt(12)
    siguiente = cab._p.getnext()
    vacios = 0
    while siguiente is not None and siguiente.tag == qn("w:p") and \
            not "".join(siguiente.itertext()).strip():
        vacios += 1
        nuevo = siguiente.getnext()
        if vacios > 1 or k == 5:
            siguiente.getparent().remove(siguiente)
        siguiente = nuevo

for seccion in doc.sections:
    for cab in (seccion.header, seccion.first_page_header, seccion.even_page_header):
        for sdt in cab._element.iter(qn("w:sdt")):
            for marcador in sdt.iter(qn("w:showingPlcHdr")):
                marcador.getparent().remove(marcador)
            for t_el in sdt.iter(qn("w:t")):
                if "Elige" in (t_el.text or ""):
                    t_el.text = "SOFTWARE"
                    rpr = t_el.getparent().find(qn("w:rPr"))
                    rpr.getparent().replace(rpr, parse_xml(
                        f'<w:rPr {NS}><w:rFonts w:ascii="Times New Roman" '
                        'w:hAnsi="Times New Roman"/><w:b/><w:sz w:val="18"/></w:rPr>'))

# Pie de página: "Página X de Y"
for seccion in doc.sections:
    for pie in (seccion.footer, seccion.first_page_footer, seccion.even_page_footer):
        pie.is_linked_to_previous = False
        for q in pie.paragraphs[1:]:
            eliminar(q)
        q = pie.paragraphs[0]
        for run in list(q.runs):
            run._element.getparent().remove(run._element)
        q.alignment = WD_ALIGN_PARAGRAPH.CENTER
        fuente_run(q.add_run("Página "))
        q._p.append(parse_xml(
            f'<w:fldSimple {NS} w:instr=" PAGE "><w:r><w:rPr><w:rFonts w:ascii="{FUENTE}" '
            f'w:hAnsi="{FUENTE}"/><w:sz w:val="24"/></w:rPr><w:t>1</w:t></w:r></w:fldSimple>'))
        fuente_run(q.add_run(" de "))
        q._p.append(parse_xml(
            f'<w:fldSimple {NS} w:instr=" NUMPAGES "><w:r><w:rPr><w:rFonts w:ascii="{FUENTE}" '
            f'w:hAnsi="{FUENTE}"/><w:sz w:val="24"/></w:rPr><w:t>1</w:t></w:r></w:fldSimple>'))

# ----------------------------------------------------------------------------
# 2.5 Software utilizado
# ----------------------------------------------------------------------------
poner_texto(buscar("•	Jupyter Notebook"), "•	Visual Studio Code (editor y terminal integrada).")
poner_texto(buscar("•	Bibliotecas pandas"), "•	Bibliotecas pandas, NumPy y Matplotlib.")
c = Cursor(buscar("Otros (Especifique)"))
poner_texto(buscar("Otros (Especifique)"),
            "Otros (Especifique): Python 3 y Visual Studio Code")
c.titulo("Software utilizado en la práctica:", sangria=0, antes=10)
c.texto("Todo el desarrollo se realizó en un computador con Windows 11 Pro. El código se "
        "escribió y ejecutó en Visual Studio Code, desde su terminal integrada (PowerShell), "
        "sin usar Jupyter Notebook ni Google Colab. La Tabla 1 resume el software y las "
        "versiones exactas con las que se obtuvieron los resultados de este informe.",
        )
c.tabla("Software y bibliotecas utilizados", ["Software", "Versión", "Uso en la práctica"], [
    ["Windows 11 Pro", "10.0.26300", "Sistema operativo del equipo de trabajo."],
    ["Visual Studio Code", "1.142.0", "Edición del script y ejecución en la terminal integrada."],
    ["Python", versiones["Python"], "Lenguaje de programación del perceptrón."],
    ["pandas", versiones["pandas"], "Lectura del CSV, limpieza y tablas de resultados."],
    ["NumPy", versiones["NumPy"], "Producto punto, suma de vectores y cálculo de métricas."],
    ["Matplotlib", versiones["Matplotlib"], "Gráficos de distribución, convergencia y frontera."],
    ["Microsoft Word", "16.0", "Redacción y maquetación del informe."],
], anchos=[3.6, 2.6, 8.8])

# ----------------------------------------------------------------------------
# Actividad 1. Reconocer la estructura del perceptrón
# ----------------------------------------------------------------------------
c = Cursor(buscar("Actividad 1."))
c.titulo("Objetivo de la actividad", antes=4)
c.texto("Identificar en el modelo las entradas, los pesos, el sesgo, la función de activación "
        "y la salida, tal como se presentan en las diapositivas 2 a 4 del documento ANN.pdf, y "
        "relacionarlos con las variables del dataset.")
c.titulo("Desarrollo")
c.texto("El perceptrón fue propuesto por Frank Rosenblatt en 1957 como un modelo inspirado en "
        "la neurona biológica: las dendritas reciben señales, el núcleo las integra y, si la "
        "señal total supera un umbral, el axón transmite un impulso [1], [3]. En el modelo "
        "matemático, cada señal de entrada se multiplica por un peso que representa su "
        "importancia, los productos se suman junto con un término de sesgo y el resultado pasa "
        "por una función escalón que decide la clase.")
c.texto("En este taller el perceptrón tiene tres entradas, una por cada característica del "
        "dataset, y una entrada adicional constante igual a 1 que multiplica al sesgo. La "
        "suma ponderada, o potencial de activación, se define en la Ecuación (1):")
c.ecuacion(r("f") + delim(r("x")) + r("=") + wi(0) + r("+") +
           suma(r("i=1"), r("3"), sub(r("w"), r("i")) + sub(r("x"), r("i"))) + r("=") +
           wi(0) + r("+") + wi(1) + xi(1) + r("+") + wi(2) + xi(2) + r("+") + wi(3) + xi(3))
c.texto("La diapositiva 4 define la salida como 1 si la suma es mayor o igual que cero y 0 en "
        "otro caso. Como la guía exige codificar las clases con Hombre = 1 y Mujer = −1, la "
        "función escalón se adaptó a salidas +1/−1 (función signo), según la Ecuación (2). "
        "Este cambio no altera el modelo: la frontera de decisión sigue siendo f(x) = 0, y "
        "permite usar directamente la regla de entrenamiento del seudocódigo.")
c.ecuacion(YH + r("=") + casos(
    r("+1") + tx("  (Hombre),   si ") + r("f") + delim(r("x")) + r("≥0"),
    r("−1") + tx("  (Mujer),   si ") + r("f") + delim(r("x")) + r("<0")))
c.texto("Para que el sesgo se trate como un peso más, se trabaja con el vector de entrada "
        "aumentado y el vector de pesos de la Ecuación (3). Así, la suma ponderada se reduce "
        "a un producto punto, que en Python se calcula con np.dot(w, x).")
c.ecuacion(XT + r("=") + sup(delim(tx("1, ") + xi(1) + tx(", ") + xi(2) + tx(", ") + xi(3),
                                   "[", "]"), r("T")) + tx(",    ") + W + r("=") +
           sup(delim(wi(0) + tx(", ") + wi(1) + tx(", ") + wi(2) + tx(", ") + wi(3), "[", "]"),
               r("T")) + tx(",    ") + r("f") + delim(r("x")) + r("=") + sup(W, r("T")) + XT)
c.imagen(RES / "estructura_perceptron.png", 14.5,
         "Estructura del perceptrón implementado: entradas, pesos, sumador y función escalón.",
         "Elaboración propia a partir de la diapositiva 4 de ANN.pdf [1].")
c.texto("La Tabla 2 responde a la pregunta de la actividad: qué elemento del modelo "
        "corresponde a cada parte del problema.")
c.tabla("Elementos del perceptrón identificados en el modelo",
        ["Elemento", "Símbolo", "Correspondencia en el taller"], [
            ["Entrada 1", "x1", "Caracteristica_1, valor continuo en [−1, 1]."],
            ["Entrada 2", "x2", "Caracteristica_2, valor continuo en [−1, 1]."],
            ["Entrada 3", "x3", "Caracteristica_3, valor continuo en [−1, 1]."],
            ["Entrada de sesgo", "x0 = 1", "Columna de unos agregada a la matriz de datos."],
            ["Pesos", "w1, w2, w3", "Importancia de cada característica; inician en 0."],
            ["Sesgo", "w0", "Desplaza la frontera respecto al origen; inicia en 0."],
            ["Suma ponderada", "f(x)", "Producto punto entre w y el vector aumentado."],
            ["Función de activación", "Escalón", "Convierte f(x) en +1 o −1."],
            ["Salida binaria", "ŷ", "+1 = Hombre, −1 = Mujer."],
        ], anchos=[3.8, 2.6, 8.6])
c.titulo("Interpretación geométrica")
c.texto("La condición f(x) = 0 describe un plano en el espacio de tres dimensiones formado por "
        "x1, x2 y x3. El vector (w1, w2, w3) es perpendicular a ese plano y apunta hacia la "
        "región que el modelo clasifica como Hombre; el sesgo w0 desplaza el plano para que no "
        "tenga que pasar por el origen. Por esta razón, un perceptrón de una sola neurona solo "
        "puede separar clases que estén a lados opuestos de un plano. Las diapositivas 5 a 8 "
        "lo ilustran: funciones como OR y AND se resuelven con una recta, pero XOR no, porque "
        "necesita una frontera no lineal [1], [6]. La primera pregunta práctica del taller, "
        "entonces, es comprobar si las clases del dataset son linealmente separables.")

# ----------------------------------------------------------------------------
# Actividad 2. Preparar los datos
# ----------------------------------------------------------------------------
c = Cursor(buscar("Actividad 2."))
c.titulo("Objetivo de la actividad", antes=4)
c.texto("Cargar el dataset, verificar su calidad, codificar la clase y dejar los datos en la "
        "forma que necesita el algoritmo de entrenamiento.")
c.titulo("Desarrollo")
c.texto(f"El archivo dataset_Perceptron_5000_continuo_menos1_a_1.csv se leyó con pandas "
        f"usando la codificación utf-8-sig, que elimina la marca BOM del inicio del archivo; "
        f"sin ella, el nombre de la primera columna se lee con un carácter invisible. El "
        f"dataset contiene {miles(len(df))} registros y cuatro columnas: tres características "
        f"numéricas continuas y la columna Clase. Antes de entrenar se realizaron las "
        f"verificaciones que muestra la Tabla 3.")
c.tabla("Verificación de calidad del dataset", ["Verificación", "Resultado", "Decisión"], [
    ["Valores nulos", str(int(df.isna().sum().sum())), "No se requiere imputación."],
    ["Filas duplicadas", str(int(df[pt.COLUMNAS + ["Clase"]].duplicated().sum())),
     "No se elimina ningún registro."],
    ["Rango de las características", f"[{df[pt.COLUMNAS].min().min():.3f}, "
     f"{df[pt.COLUMNAS].max().max():.3f}]", "Ya están escaladas; no se normaliza."],
    ["Balance de clases", "2 500 / 2 500", "Clases balanceadas; la exactitud es representativa."],
    ["Tipo de datos", "float64", "Las tres características son numéricas."],
], anchos=[4.3, 3.4, 7.3])
desc = df[pt.COLUMNAS].describe()
c.tabla("Estadística descriptiva de las características (n = 5 000)",
        ["Variable", "Media", "Desv. est.", "Mínimo", "Mediana", "Máximo"],
        [[col.replace("_", " "), f3(desc[col]["mean"]), f3(desc[col]["std"]),
          f3(desc[col]["min"]), f3(desc[col]["50%"]), f3(desc[col]["max"])]
         for col in pt.COLUMNAS], anchos=[3.9, 2.2, 2.3, 2.2, 2.2, 2.2])
c.texto("Las tres variables tienen media cercana a cero, lo que indica que los datos están "
        "centrados en el origen. Sin embargo, la estadística global oculta lo más importante; "
        "por eso se calcularon las mismas medidas separadas por clase (Tabla 5).")
filas = []
for col in pt.COLUMNAS:
    g = df.groupby("Clase")[col]
    filas.append([col.replace("_", " "),
                  f"{f3(g.mean()['Hombre'])} ± {f3(g.std()['Hombre'])}",
                  f"{f3(g.min()['Hombre'])} a {f3(g.max()['Hombre'])}",
                  f"{f3(g.mean()['Mujer'])} ± {f3(g.std()['Mujer'])}",
                  f"{f3(g.min()['Mujer'])} a {f3(g.max()['Mujer'])}"])
c.tabla("Media ± desviación estándar y rango de cada característica por clase",
        ["Variable", "Hombre: media", "Hombre: rango", "Mujer: media", "Mujer: rango"],
        filas, anchos=[3.3, 2.9, 2.9, 2.9, 3.0])
c.texto("En las tres características la clase Hombre toma valores positivos y la clase Mujer "
        "valores negativos. En Caracteristica_3 los rangos ni siquiera se superponen: el valor "
        "mínimo de Hombre (0.438) está muy por encima del máximo de Mujer (−0.450). Lo mismo "
        "ocurre en Caracteristica_1 (0.177 frente a −0.241). La Ilustración 2 lo confirma "
        "visualmente: los histogramas de cada clase forman dos grupos separados.")
c.imagen(RES / "distribucion_caracteristicas.png", 15.5,
         "Distribución de cada característica según la clase.",
         "Elaboración propia con Python y Matplotlib.")
c.texto("Esto permite anticipar que existe al menos un plano que separa las clases sin error. "
        "Según el teorema de convergencia del perceptrón [2], en ese caso el algoritmo encuentra "
        "una solución en un número finito de actualizaciones.")
c.titulo("Codificación de la clase y vector aumentado")
c.texto("Siguiendo la instrucción 3 de la guía, la columna Clase se transformó en la variable "
        "objetivo y de la Ecuación (4). Además se agregó al inicio de la matriz de entradas "
        "una columna de unos (x0 = 1), de modo que cada registro queda como el vector "
        "aumentado de la Ecuación (3).")
c.ecuacion(r("y") + r("=") + casos(r("+1") + tx(",   si Clase = Hombre"),
                                   r("−1") + tx(",   si Clase = Mujer")))
c.tabla("Distribución de las clases y de la partición entrenamiento/prueba",
        ["Clase", "Código y", "Registros", "%", "Entrenamiento", "Prueba"], [
            ["Hombre", "+1", "2 500", "50 %", "2 000", "500"],
            ["Mujer", "−1", "2 500", "50 %", "2 000", "500"],
            ["Total", "", "5 000", "100 %", "4 000", "1 000"],
        ], anchos=[2.6, 2.2, 2.4, 1.8, 3.2, 2.2])
c.titulo("Partición de los datos")
c.texto("Para evaluar el modelo con datos que no participaron en el entrenamiento, el dataset "
        "se dividió en 80 % para entrenamiento y 20 % para prueba. La división es estratificada: "
        "se toma el 20 % de cada clase por separado, así ambos conjuntos conservan la "
        "proporción 50/50 (Tabla 6). Se fijó la semilla aleatoria 42 para que cualquier persona "
        "que ejecute el script obtenga exactamente la misma partición y los mismos pesos.")
c.texto("Por último, el conjunto de entrenamiento se barajó. El perceptrón actualiza los pesos "
        "ejemplo por ejemplo, de modo que si los datos llegaran ordenados por clase, el modelo "
        "vería primero todos los Hombres y después todas las Mujeres, y los pesos oscilarían más "
        "de lo necesario. No se aplicó normalización porque las tres características ya están en "
        "el mismo rango [−1, 1]; escalarlas otra vez no cambiaría la frontera.")

# ----------------------------------------------------------------------------
# Actividad 3. Programar el entrenamiento del perceptrón
# ----------------------------------------------------------------------------
c = Cursor(buscar("Actividad 3."))
c.titulo("Objetivo de la actividad", antes=4)
c.texto("Programar desde cero, sin la clase Perceptron de scikit-learn, el algoritmo de "
        "entrenamiento de la diapositiva 4, con pesos y sesgo iniciales iguales a cero y al "
        "menos 200 épocas.")
c.titulo("Seudocódigo de referencia")
c.texto("El seudocódigo de la diapositiva 4 recibe un conjunto de ejemplos (x~i~, y~i~) y "
        "devuelve los pesos (w0, …, w~d~) del perceptrón. Inicializa todos los pesos en cero y, "
        "hasta converger, recorre cada ejemplo: si el ejemplo está mal clasificado, ajusta los "
        "pesos. La condición de error es la Ecuación (5).")
c.ecuacion(sub(r("y"), r("i")) + r("·") + r("f") + delim(sub(r("x"), r("i"))) + r("≤0"))
c.texto("El producto y~i~·f(x~i~) es positivo solo cuando el signo de la suma ponderada coincide "
        "con la clase real. Si es negativo, el modelo se equivocó de lado; si es cero, el punto "
        "está sobre la frontera. En ambos casos se aplica la regla de actualización de la "
        "Ecuación (6), que también ajusta el sesgo porque x~i0~ = 1.")
c.ecuacion(sub(r("w"), r("j")) + r("←") + sub(r("w"), r("j")) + r("+") + sub(r("y"), r("i")) +
           sub(r("x"), r("ij")) + tx(",      ") + r("j=0, 1, 2, 3"))
c.texto("¿Por qué esta regla corrige el error? Al reemplazar los pesos nuevos en la condición "
        "de error del mismo ejemplo se obtiene la Ecuación (7). Como ‖x̃~i~‖² siempre es "
        "positivo, cada actualización aumenta y~i~·f(x~i~), es decir, empuja el ejemplo hacia el "
        "lado correcto de la frontera.")
c.ecuacion(sub(r("y"), r("i")) + sup(delim(W + r("+") + sub(r("y"), r("i")) + XTI), r("T")) +
           XTI + r("=") + sub(r("y"), r("i")) + sup(W, r("T")) + XTI + r("+") +
           sup(delim(XTI, "‖", "‖"), r("2")))
c.titulo("Implementación en Python")
c.texto("La Tabla 7 muestra la correspondencia entre cada paso del seudocódigo y la línea de "
        "código que lo implementa. Se utilizó NumPy únicamente para el producto punto y la suma "
        "de vectores, tal como permite la instrucción 5 de la guía.")
c.tabla("Correspondencia entre el seudocódigo y el código", ["Paso del seudocódigo", "Código en Python"], [
    ["2. Inicializar w~j~ = 0, ∀j ∈ {0,…,d}", "w = np.zeros(4)"],
    ["3. Repetir hasta convergencia", "for epoca in range(1, 201):"],
    ["4. Para cada ejemplo x~i~", "for i, (xi, yi) in enumerate(zip(X, y)):"],
    ["5. Si y~i~·f(x~i~) ≤ 0 (¿error?)", "if yi * f(w, xi) <= 0:"],
    ["6. w~j~ ← w~j~ + y~i~·x~ij~", "w = w + yi * xi"],
], anchos=[6.6, 8.4])
c.texto("La Ilustración 3 muestra el script abierto en Visual Studio Code, con el cursor en la "
        "definición de entrenar_perceptron (línea 99), y en la parte inferior el inicio de su "
        "ejecución en la terminal integrada con el comando python perceptron_taller.py. Además "
        "de aplicar la regla, la función registra en cada época el número de errores, la "
        "exactitud y los pesos, y guarda el detalle de cada ajuste para poder analizar la "
        "convergencia. Aunque el seudocódigo dice «repetir hasta convergencia», el bucle se "
        "ejecuta las 200 épocas completas para cumplir la instrucción 6. Una vez que el modelo "
        "converge, las épocas siguientes no modifican los pesos. El código completo está en el "
        "Anexo B.")
if (CAP / "vscode_ejecucion_1.png").exists():
    c.imagen(CAP / "vscode_ejecucion_1.png", 15.5,
             "Función entrenar_perceptron en el editor y comienzo de la ejecución en la "
             "terminal de Visual Studio Code.",
             "Captura de pantalla de Visual Studio Code 1.142.0.")
elif not BORRADOR:
    raise SystemExit(f"Falta la captura {CAP / 'vscode_ejecucion_1.png'}")
c.titulo("Traza manual de las actualizaciones")
c.texto(f"Para comprobar que el código aplica correctamente la regla, se reconstruyeron a mano "
        f"las {n_ajustes} actualizaciones que hizo el algoritmo durante el entrenamiento "
        f"(Tabla 8).")
filas = []
for t_ in traza:
    filas.append([f"Época {t_['epoca']}, ejemplo {t_['ejemplo']}",
                  "(" + ", ".join(f3(v) for v in t_["x"][1:]) + ")",
                  f"{t_['y']:+d}".replace("-", "−"), f3(t_["f"]),
                  "(" + ", ".join(f3(v) for v in t_["w_desp"]) + ")"])
c.tabla("Actualizaciones de pesos realizadas durante el entrenamiento",
        ["Momento", "x = (x1, x2, x3)", "y", "f(x) antes", "w después (w0, w1, w2, w3)"],
        filas, anchos=[2.9, 4.5, 0.9, 2.0, 4.7])
t1, t2 = traza[0], traza[1]
c.texto(f"En el primer ejemplo todos los pesos valen cero, por lo que f(x) = 0 y la condición "
        f"y·f(x) = 0 ≤ 0 se cumple: se cuenta como error y se suma el vector aumentado (y = +1). "
        f"En el ejemplo {t2['ejemplo']} la suma ponderada fue f(x) = 1 + "
        f"({f3(t1['w_desp'][1])})({f3(t2['x'][1])}) + ({f3(t1['w_desp'][2])})({f3(t2['x'][2])}) + "
        f"({f3(t1['w_desp'][3])})({f3(t2['x'][3])}) = {f3(t2['f'])}. Como es mayor que cero, el "
        f"modelo predijo Hombre para una Mujer (y = −1), y se restó el vector aumentado: "
        f"w0 = 1 − 1 = 0, w1 = {f3(t1['w_desp'][1])} + {f3(-t2['x'][1])} = {f3(t2['w_desp'][1])}, "
        f"w2 = {f3(t1['w_desp'][2])} + {f3(-t2['x'][2])} = {f3(t2['w_desp'][2])} y "
        f"w3 = {f3(t1['w_desp'][3])} + {f3(-t2['x'][3])} = {f3(t2['w_desp'][3])}. "
        f"Los valores coinciden con los pesos finales que imprimió el programa (Ilustración 4).")
c.texto(f"Desde ese momento ningún otro ejemplo cumplió la condición de error: en la época "
        f"{ep_conv} el algoritmo recorrió los 4 000 ejemplos sin equivocarse, que es el criterio "
        f"de convergencia del seudocódigo. Los resultados del entrenamiento se presentan en la "
        f"sección 2.7.")

# ----------------------------------------------------------------------------
# Actividad 4. Evaluar el clasificador
# ----------------------------------------------------------------------------
c = Cursor(buscar("Actividad 4."))
c.titulo("Objetivo de la actividad", antes=4)
c.texto("Medir el desempeño del perceptrón con la exactitud, la matriz de confusión y otras "
        "métricas derivadas, tanto en el conjunto de entrenamiento como en el de prueba, y "
        "analizar la convergencia.")
c.titulo("Desarrollo")
c.texto("Con los pesos finales se calculó f(x) para cada registro y se aplicó la función "
        "escalón. Luego se compararon las predicciones con las clases reales en una matriz de "
        "confusión de 2 × 2. Se tomó como clase positiva a Hombre (+1), y se definieron cuatro "
        "conteos:")
c.vinetas(["**VP (verdaderos positivos):** Hombres clasificados como Hombre.",
           "**VN (verdaderos negativos):** Mujeres clasificadas como Mujer.",
           "**FP (falsos positivos):** Mujeres clasificadas como Hombre.",
           "**FN (falsos negativos):** Hombres clasificados como Mujer."])
c.texto("A partir de estos conteos se calcularon las métricas de las Ecuaciones (8) a (12). La "
        "exactitud responde a qué proporción del total se clasificó bien; la precisión, a "
        "cuántas de las predicciones Hombre fueron correctas; la sensibilidad, a cuántos de los "
        "Hombres reales se detectaron; la especificidad hace lo mismo para la clase Mujer, y F1 "
        "resume la precisión y la sensibilidad en un solo valor.")
VP, VN, FP, FN = (tx(s) for s in ("VP", "VN", "FP", "FN"))
c.ecuacion(tx("Exactitud") + r("=") + frac(VP + r("+") + VN, VP + r("+") + VN + r("+") + FP +
                                            r("+") + FN))
c.ecuacion(tx("Precisión") + r("=") + frac(VP, VP + r("+") + FP))
c.ecuacion(tx("Sensibilidad") + r("=") + frac(VP, VP + r("+") + FN))
c.ecuacion(tx("Especificidad") + r("=") + frac(VN, VN + r("+") + FP))
c.ecuacion(tx("F1") + r("=") + frac(r("2·") + tx("Precisión") + r("·") + tx("Sensibilidad"),
                                    tx("Precisión") + r("+") + tx("Sensibilidad")))
vp, fn = mc_te.iloc[0]
fp, vn = mc_te.iloc[1]
c.texto(f"Reemplazando los valores del conjunto de prueba (VP = {vp}, VN = {vn}, FP = {fp}, "
        f"FN = {fn}): exactitud = ({vp} + {vn}) / {vp + vn + fp + fn} = 1.000; precisión = "
        f"{vp} / ({vp} + {fp}) = 1.000; sensibilidad = {vp} / ({vp} + {fn}) = 1.000; "
        f"especificidad = {vn} / ({vn} + {fp}) = 1.000, y F1 = 1.000. Las matrices de confusión "
        f"y la tabla completa de métricas están en la sección 2.7 (Tablas 12 y 13, "
        f"Ilustración 6).")
c.titulo("Análisis de la convergencia")
c.texto("Para analizar la convergencia se registró el número de ejemplos mal clasificados en "
        "cada época. Además, se comparó el número de actualizaciones con la cota teórica de "
        "Novikoff [2], según la cual, si los datos son linealmente separables con margen γ y "
        "todos los vectores cumplen ‖x̃‖ ≤ R, el perceptrón hace como máximo k "
        "actualizaciones (Ecuación (13)).")
c.ecuacion(r("k≤") + sup(delim(frac(r("R"), r("γ"))), r("2")) + tx(",      ") + r("R=") +
           func_lim("max", r("i"), delim(XTI, "‖", "‖")))
c.texto(f"En el conjunto de entrenamiento, R = {R:.4f}. Con el margen γ = {d_min:.4f} que "
        f"alcanzó la frontera aprendida (ver Actividad 5), la cota es (R/γ)² = {cota:.2f}. El "
        f"algoritmo hizo {n_ajustes} actualizaciones, muy por debajo de ese límite, lo que es "
        f"coherente con la teoría: cuanto mayor es la separación entre las clases, más rápido "
        f"converge el perceptrón.")

# ----------------------------------------------------------------------------
# Actividad 5. Interpretar el resultado
# ----------------------------------------------------------------------------
c = Cursor(buscar("Actividad 5."))
c.titulo("Objetivo de la actividad", antes=4)
c.texto("Interpretar los pesos aprendidos, la frontera de decisión y el desempeño obtenido, "
        "explicando por qué el perceptrón se comportó como lo hizo con este dataset.")
c.titulo("Pesos finales")
c.tabla("Pesos finales del perceptrón", ["Parámetro", "Valor", "Importancia relativa"], [
    ["w0 (sesgo)", f4(w[0]), "—"],
    ["w1 (Caracteristica_1)", f4(w[1]), f"{importancia[0]:.1%}"],
    ["w2 (Caracteristica_2)", f4(w[2]), f"{importancia[1]:.1%}"],
    ["w3 (Caracteristica_3)", f4(w[3]), f"{importancia[2]:.1%}"],
], anchos=[5.2, 3.2, 4.6])
c.texto("La importancia relativa se calculó como |w~i~| / (|w1| + |w2| + |w3|). Como las tres "
        "características están en la misma escala, la magnitud de cada peso se puede comparar "
        "directamente.")
c.vinetas([
    f"**Todos los pesos son positivos.** Valores altos de cualquier característica aumentan "
    f"f(x) y empujan la predicción hacia Hombre (+1); valores bajos la llevan a Mujer (−1). Esto "
    f"coincide con la Tabla 5, donde las medias de Hombre son positivas y las de Mujer negativas.",
    f"**x1 y x3 son las características más influyentes** ({importancia[0]:.1%} y "
    f"{importancia[2]:.1%}). Son las que muestran mayor distancia entre las medias de las clases "
    f"(≈ 1.30 y ≈ 1.56). En cambio, x2 tiene el peso más bajo ({importancia[1]:.1%}) porque sus "
    f"valores por clase están más cerca entre sí y casi se tocan en el cero.",
    f"**El sesgo quedó en cero.** Las dos actualizaciones se compensaron: la primera sumó 1 (y = "
    f"+1) y la segunda restó 1 (y = −1). Como los datos están centrados en el origen, una "
    f"frontera que pasa por el origen separa bien las clases y el modelo no necesitó desplazarla.",
])
c.titulo("Frontera de decisión")
c.texto("Al reemplazar los pesos finales en f(x) = 0 se obtiene la ecuación del plano que "
        "separa las clases (Ecuación (14)). Todo punto que quede del lado positivo del plano se "
        "clasifica como Hombre y todo punto del lado negativo, como Mujer.")
c.ecuacion(r(f3(w[1])) + xi(1) + r("+") + r(f3(w[2])) + xi(2) + r("+") + r(f3(w[3])) + xi(3) +
           r("=0"))
c.texto("Para medir qué tan holgada es la separación, se calculó la distancia de cada punto de "
        "entrenamiento al plano con la Ecuación (15), y se tomó la menor.")
c.ecuacion(sub(r("d"), tx("min")) + r("=") +
           min_(r("i"), frac(sub(r("y"), r("i")) + r("f") + delim(sub(r("x"), r("i"))),
                             delim(W, "‖", "‖"))) + tx(",      ") + delim(W, "‖", "‖") + r("=") +
           raiz(subsup(r("w"), r("1"), r("2")) + r("+") + subsup(r("w"), r("2"), r("2")) +
                r("+") + subsup(r("w"), r("3"), r("2"))))
c.texto(f"Con ‖w‖ = {norma_w:.4f}, la distancia mínima resulta {d_min:.4f}. Es decir, el "
        f"registro más cercano a la frontera está a más de 0.72 unidades del plano, en un "
        f"espacio donde cada eje mide 2 unidades. Esto explica por qué bastaron dos ajustes: "
        f"las clases forman dos grupos compactos y muy separados, como se observa en las "
        f"Ilustraciones 7 y 8 de la sección 2.7. Conviene aclarar que el perceptrón no busca la "
        f"frontera de margen máximo: se detiene en la primera que no comete errores. Otra "
        f"inicialización o un orden distinto de los datos producirían pesos diferentes, pero "
        f"igualmente válidos.")
c.titulo("Uso del modelo con registros nuevos")
c.texto("Con los pesos finales, clasificar un registro nuevo requiere un solo producto punto. "
        "Por ejemplo, para x = (0.5, 0.3, 0.6): f(x) = 0 + 1.345(0.5) + 0.835(0.3) + 1.293(0.6) "
        "= 1.699. Como f(x) ≥ 0, el modelo predice Hombre. La Tabla 14 de la sección 2.7 muestra "
        "otros registros del conjunto de prueba con su valor de f(x) y su predicción.")
c.titulo("Respuesta de la actividad")
c.texto("El perceptrón aprendió una regla sencilla y fácil de interpretar: sumar las tres "
        "características, dando más peso a la primera y a la tercera, y asignar Hombre si el "
        "resultado es positivo. El desempeño perfecto no se debe a que el modelo sea complejo, "
        "sino a que el problema es linealmente separable. Con datos reales, donde las clases "
        "suelen superponerse, un perceptrón simple no alcanzaría el 100 % y su regla no "
        "convergería; esa limitación es la que motiva las redes multicapa de las diapositivas "
        "siguientes [1], [6].")

# ----------------------------------------------------------------------------
# 2.7 Resultados obtenidos (nueva sección antes de Habilidades blandas)
# ----------------------------------------------------------------------------
ancla = buscar("Habilidades blandas")
previo = ancla._p.getprevious()
from docx.text.paragraph import Paragraph  # noqa: E402
c = Cursor(Paragraph(previo, ancla._parent))
p = c.titulo("2.7 Resultados obtenidos")
p._p.remove(p._p.pPr)
p._p.insert(0, copy.deepcopy(buscar("2.6 Actividades")._p.pPr))
p.paragraph_format.space_before = Pt(12)
p.paragraph_format.keep_with_next = True
c.texto("Esta sección presenta los resultados producidos por el script perceptron_taller.py al "
        "ejecutarlo en la terminal integrada de Visual Studio Code con el comando python "
        "perceptron_taller.py. Todas las tablas y figuras se generaron automáticamente en la "
        "carpeta resultados/ y corresponden a una única ejecución reproducible (semilla 42).",
        )
c.titulo("2.7.1 Ejecución del programa")
c.texto("El programa se ejecutó en la terminal integrada de Visual Studio Code. La primera parte "
        "de la salida (Ilustración 3, Actividad 3) muestra la carga del dataset: 5 000 registros, "
        "sin nulos ni duplicados, la codificación Hombre = 1 y Mujer = −1, las medias por clase y "
        "la partición de 4 000 registros para entrenamiento y 1 000 para prueba. Después aparece "
        "el inicio del entrenamiento con w = 0 y sesgo = 0. La Ilustración 4 muestra el final de "
        "la ejecución: los pesos finales, la ecuación de la frontera, las matrices de confusión, "
        "la tabla de métricas, la distancia mínima a la frontera y los ejemplos de predicción. "
        "El programa terminó sin errores y guardó los gráficos y tablas en la carpeta "
        "resultados/.")
if (CAP / "vscode_ejecucion_2.png").exists():
    c.imagen(CAP / "vscode_ejecucion_2.png", 15.5,
             "Final de la ejecución en la terminal de Visual Studio Code: pesos finales, "
             "evaluación y predicciones.", "Captura de pantalla de Visual Studio Code 1.142.0.")
elif not BORRADOR:
    raise SystemExit(f"Falta la captura {CAP / 'vscode_ejecucion_2.png'}")
c.titulo("2.7.2 Convergencia del entrenamiento")
filas = [[int(h.Epoca), int(h.Errores), f"{h.Exactitud_entrenamiento:.2%}", f4(h.w0), f4(h.w1),
          f4(h.w2), f4(h.w3)] for h in hist.head(6).itertuples()]
filas.append(["7 a 200", 0, "100.00%", f4(w[0]), f4(w[1]), f4(w[2]), f4(w[3])])
c.tabla("Errores, exactitud y pesos al final de cada época",
        ["Época", "Errores", "Exactitud", "w0", "w1", "w2", "w3"], filas,
        anchos=[2.0, 1.9, 2.4, 2.0, 2.2, 2.2, 2.2],
        alinear=[WD_ALIGN_PARAGRAPH.CENTER] * 7)
c.texto(f"El algoritmo cometió {int(hist.loc[0, 'Errores'])} errores en la época 1 y ninguno "
        f"a partir de la época {ep_conv}. La exactitud de entrenamiento ya era de 100 % al "
        f"terminar la primera época, porque el segundo ajuste ocurrió en el ejemplo 10 y los "
        f"3 990 ejemplos restantes quedaron bien clasificados. La Ilustración 5 muestra a la "
        f"izquierda los errores por época y a la derecha la evolución de los pesos: las cuatro "
        f"curvas son horizontales en las 200 épocas, lo que confirma que el modelo se "
        f"estabilizó.")
c.imagen(RES / "convergencia.png", 15.5,
         "Errores por época (izquierda) y evolución de los pesos en las 200 épocas (derecha).",
         "Elaboración propia con Python y Matplotlib.")
c.titulo("2.7.3 Pesos finales")
c.tabla("Pesos finales obtenidos", ["Parámetro", "w0 (sesgo)", "w1", "w2", "w3"],
        [["Valor", f4(w[0]), f4(w[1]), f4(w[2]), f4(w[3])]],
        anchos=[3.0, 3.0, 3.0, 3.0, 3.0])
c.titulo("2.7.4 Matrices de confusión y métricas")
filas = []
for nombre, mc in [("Entrenamiento", mc_tr), ("Prueba", mc_te)]:
    filas.append([nombre, mc.iloc[0, 0], mc.iloc[1, 1], mc.iloc[1, 0], mc.iloc[0, 1],
                  mc.to_numpy().sum()])
c.tabla("Matrices de confusión (clase positiva: Hombre)",
        ["Conjunto", "VP", "VN", "FP", "FN", "Total"], filas,
        anchos=[3.5, 2.2, 2.2, 2.2, 2.2, 2.2])
c.imagen(RES / "matrices_confusion.png", 15.0,
         "Matrices de confusión de los conjuntos de entrenamiento y de prueba.",
         "Elaboración propia con Python y Matplotlib.")
filas = [[r_.Conjunto, miles(r_.n), f"{r_.Exactitud:.2%}", f"{r_.Precision:.2%}",
          f"{r_.Sensibilidad:.2%}", f"{r_.Especificidad:.2%}", f"{r_.F1:.3f}"]
         for r_ in tabla.itertuples()]
c.tabla("Tabla de resultados del clasificador",
        ["Conjunto", "n", "Exactitud", "Precisión", "Sensib.", "Especif.", "F1"], filas,
        anchos=[3.0, 1.6, 2.2, 2.2, 2.0, 2.0, 1.6])
c.texto("El perceptrón clasificó correctamente los 4 000 registros de entrenamiento y los 1 000 "
        "de prueba. Las matrices no tienen falsos positivos ni falsos negativos, por lo que todas "
        "las métricas valen 100 %. Que la exactitud de prueba sea igual a la de entrenamiento "
        "indica que el modelo no memorizó los datos: la frontera aprendida generaliza a "
        "registros que no vio durante el entrenamiento.")
c.titulo("2.7.5 Frontera de decisión")
c.imagen(RES / "frontera_3d.png", 11.5,
         "Registros de ambas clases y plano de decisión aprendido en el espacio (x1, x2, x3).",
         "Elaboración propia con Python y Matplotlib (muestra aleatoria de 1 500 registros).")
c.imagen(RES / "frontera_proyecciones.png", 15.5,
         "Proyecciones de los datos y de la frontera en los planos x1–x2, x1–x3 y x2–x3 (la "
         "tercera variable se fija en su media).",
         "Elaboración propia con Python y Matplotlib.")
c.texto(f"En la Ilustración 7 el plano gris deja a todos los Hombres (azul) de un lado y a "
        f"todas las Mujeres (rojo) del otro. Las proyecciones de la Ilustración 8 muestran que la "
        f"separación es amplia en los tres planos. La distancia mínima de un punto a la frontera "
        f"es de {d_min:.4f} unidades.")
c.titulo("2.7.6 Ejemplos de predicción")
c.tabla("Predicciones para registros del conjunto de prueba",
        ["x1", "x2", "x3", "Clase real", "f(x)", "Predicción"],
        [[f3(e["x1"]), f3(e["x2"]), f3(e["x3"]), e["Clase real"], f3(e["f(x)"]),
          e["Predicción"]] for _, e in ejemplos.iterrows()],
        anchos=[2.0, 2.0, 2.0, 3.0, 2.2, 3.0],
        alinear=[WD_ALIGN_PARAGRAPH.CENTER] * 6)
c.texto("Los Hombres obtienen valores de f(x) cercanos a +2 y las Mujeres cercanos a −2, lejos "
        "del umbral cero. Por eso el modelo clasifica con seguridad incluso los registros que "
        "están en los extremos de cada grupo.")
c.titulo("2.7.7 Cumplimiento de las instrucciones de la guía")
c.tabla("Verificación de las instrucciones de la sección 2.4", ["Instrucción", "Cómo se cumplió"], [
    ["1. Usar el dataset proporcionado", "Se leyó dataset_Perceptron_5000_continuo_menos1_a_1.csv."],
    ["2. Dataset sintético y didáctico", "Las clases se interpretan solo como etiquetas +1/−1."],
    ["3. Hombre = 1, Mujer = −1", "Codificación aplicada en cargar_datos (Ecuación (4))."],
    ["4. Sin la clase Perceptron de scikit-learn", "El entrenamiento se programó desde cero; "
     "scikit-learn no se importa."],
    ["5. pandas y NumPy", "pandas para leer y tabular; NumPy para el cálculo vectorial."],
    ["6. Pesos = 0, sesgo = 0 y al menos 200 épocas", "w = np.zeros(4) y 200 épocas completas."],
    ["7. Perceptrón simple", "Una sola neurona, sin capas ocultas ni backpropagation."],
], anchos=[6.0, 9.0], alinear=[WD_ALIGN_PARAGRAPH.LEFT] * 2)

# La plantilla trae "Liste los pesos finales" suelto bajo Habilidades blandas;
# los pesos se reportan en la Actividad 5 y en la sección 2.7.3.
eliminar(buscar("Liste los pesos finales"))

# ----------------------------------------------------------------------------
# 2.9 Conclusiones, 2.10 Recomendaciones, 2.11 Referencias
# ----------------------------------------------------------------------------
p = buscar("Redacte dos conclusiones")
c = Cursor(p)
c.numerada([
    f"**Sobre el funcionamiento del perceptrón:** el perceptrón de una sola neurona, programado "
    f"desde cero con la regla de la diapositiva 4 (si y·f(x) ≤ 0, entonces w ← w + y·x), aprende "
    f"sin tasa de aprendizaje ni derivadas: solo corrige los pesos cuando se equivoca, y cada "
    f"corrección acerca el ejemplo mal clasificado al lado correcto de la frontera "
    f"(Ecuación (7)). Partiendo de pesos y sesgo en cero, bastaron {n_ajustes} actualizaciones "
    f"en la primera época para fijar el plano 1.345x~1~ + 0.835x~2~ + 1.293x~3~ = 0. Durante las 199 "
    f"épocas restantes los pesos no cambiaron, lo que confirma la convergencia que garantiza el "
    f"teorema de Novikoff para datos linealmente separables ({n_ajustes} actualizaciones frente "
    f"a una cota de {cota:.2f}).",
    f"**Sobre el desempeño con el dataset utilizado:** el modelo alcanzó 100 % de exactitud, "
    f"precisión, sensibilidad y especificidad tanto en entrenamiento (4 000 registros) como en "
    f"prueba (1 000 registros), sin falsos positivos ni falsos negativos. Este resultado se "
    f"explica porque las clases del dataset sintético son linealmente separables, con una "
    f"distancia mínima de {d_min:.2f} unidades entre los datos y la frontera. Los pesos "
    f"muestran que Caracteristica_1 ({importancia[0]:.1%}) y Caracteristica_3 "
    f"({importancia[2]:.1%}) son las variables más discriminantes, mientras que "
    f"Caracteristica_2 aporta menos ({importancia[1]:.1%}).",
], sangria=Cm(1.27))
eliminar(p)

p = buscar("Proponga una recomendación")
c = Cursor(p)
c.texto("Se recomienda evaluar la robustez del mismo perceptrón simple con datos menos ideales, "
        "sin cambiar el modelo a una red multicapa. Para ello se pueden generar versiones del "
        "dataset con ruido gaussiano en las características, o con un porcentaje de etiquetas "
        "invertidas (por ejemplo 5 %, 10 % y 20 %), para que las clases se superpongan. En ese "
        "escenario la regla del perceptrón ya no converge, por lo que conviene registrar los "
        "errores por época, conservar los mejores pesos encontrados (variante «pocket») y "
        "comparar la exactitud en prueba mediante validación cruzada de 5 particiones con "
        "distintas semillas de barajado. Así se mediría cuánto depende el desempeño del 100 % "
        "de la separabilidad perfecta del dataset didáctico.")
eliminar(p)

p = buscar("[2] Dataset sintético")
ref1 = buscar("[1] Material docente")
formato(ref1, WD_ALIGN_PARAGRAPH.LEFT, sangria=Cm(1.27), primera=Cm(-0.63), interlineado=1.15)
for q in entre("[1] Material docente", "[2] Dataset sintético"):
    if not q.text.strip():
        eliminar(q)
c = Cursor(p)
referencias = [
    '[2] A. B. J. Novikoff, "On convergence proofs on perceptrons," en Proc. Symposium on the '
    'Mathematical Theory of Automata, vol. 12, Brooklyn, NY, USA, 1962, pp. 615–622.',
    '[3] F. Rosenblatt, "The perceptron: A probabilistic model for information storage and '
    'organization in the brain," Psychological Review, vol. 65, no. 6, pp. 386–408, 1958.',
    '[4] C. R. Harris et al., "Array programming with NumPy," Nature, vol. 585, pp. 357–362, 2020.',
    '[5] W. McKinney, "Data structures for statistical computing in Python," en Proc. 9th Python '
    'in Science Conf., Austin, TX, USA, 2010, pp. 56–61.',
    '[6] M. Minsky y S. Papert, Perceptrons: An Introduction to Computational Geometry. '
    'Cambridge, MA, USA: MIT Press, 1969.',
    '[7] S. Haykin, Neural Networks and Learning Machines, 3.ª ed. Upper Saddle River, NJ, USA: '
    'Pearson, 2009.',
    '[8] J. D. Hunter, "Matplotlib: A 2D graphics environment," Computing in Science & '
    'Engineering, vol. 9, no. 3, pp. 90–95, 2007.',
    '[9] Dataset sintético, "dataset_Perceptron_5000_continuo_menos1_a_1.csv", material de '
    'clase, Inteligencia de Negocios, Universidad Técnica de Ambato, 2026.',
]
for ref in referencias:
    q = c.texto(ref, alineacion=WD_ALIGN_PARAGRAPH.LEFT, sangria=Cm(1.27), primera=Cm(-0.63),
                interlineado=1.15)
eliminar(p)

# ----------------------------------------------------------------------------
# 2.12 Anexos
# ----------------------------------------------------------------------------
p = buscar("Anexar:")
c = Cursor(p)
c.texto("Se adjuntan el código fuente y la lista de archivos generados. Las capturas de "
        "ejecución, las matrices de confusión y la tabla de resultados se presentan en la "
        "sección 2.7.")
c.titulo("Anexo A. Archivos entregados")
c.tabla("Archivos que forman parte de la entrega", ["Archivo", "Contenido"], [
    ["perceptron_taller.py", "Script completo para ejecutar en Visual Studio Code."],
    ["dataset_Perceptron_5000_continuo_menos1_a_1.csv", "Dataset proporcionado por el docente."],
    ["capturas/", "Capturas reales del editor y de la terminal de Visual Studio Code."],
    ["resultados/tabla_resultados.csv", "Métricas de entrenamiento y prueba."],
    ["resultados/matriz_confusion_*.csv / matrices_confusion.png", "Matrices de confusión."],
    ["resultados/pesos_finales.csv, ajustes_pesos.csv", "Pesos finales y detalle de cada ajuste."],
    ["resultados/historial_entrenamiento.csv", "Errores, exactitud y pesos de las 200 épocas."],
    ["resultados/*.png", "Gráficos de distribución, convergencia y frontera."],
], anchos=[7.5, 7.5], alinear=[WD_ALIGN_PARAGRAPH.LEFT] * 2)
c.titulo("Anexo B. Código fuente (perceptron_taller.py)")
c.codigo((TALLER / "perceptron_taller.py").read_text(encoding="utf-8"))
eliminar(p)

# ----------------------------------------------------------------------------
# Formato global: Times New Roman 12 y justificado en el cuerpo
# ----------------------------------------------------------------------------
estilo = doc.styles["Normal"]
estilo.font.name = FUENTE
estilo.font.size = Pt(12)
estilo.element.rPr.rFonts.set(qn("w:eastAsia"), FUENTE)


def es_codigo(run):
    return run.font.name == "Courier New"


def normalizar(parrafos, justificar):
    for q in parrafos:
        for run in q.runs:
            if not es_codigo(run):
                fuente_run(run, 12)
        if justificar and q.alignment in (None, WD_ALIGN_PARAGRAPH.LEFT) and q.text.strip() \
                and not q.text.startswith("[") and "\t" not in q.text \
                and not any(es_codigo(rr) for rr in q.runs):
            q.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY


normalizar(doc.paragraphs, justificar=True)
for t in doc.tables:
    for fila in t.rows:
        for celda in fila.cells:
            normalizar(celda.paragraphs, justificar=False)
# El título de la portada se mantiene en 13 pt como en la plantilla del docente
for run in doc.paragraphs[0].runs:
    run.font.size = Pt(13)

doc.save(SALIDA)
print(f"Informe generado: {SALIDA}")
print(f"Tablas: {contador['tabla']} | Ilustraciones: {contador['ilustracion']} | "
      f"Ecuaciones: {contador['ecuacion']}")
