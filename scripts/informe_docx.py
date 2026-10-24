"""
Utilidades para armar informes de guía práctica (.docx) sobre la plantilla UTA–FISEI.

Formato: Times New Roman 12, texto justificado con interlineado 1.5, tablas simples,
ecuaciones de Word numeradas, leyendas "Tabla N." / "Ilustración N." y pie de página
"Página X de Y".

Las referencias cruzadas se escriben como {tab:clave}, {fig:clave} o {eq:clave} y se
reemplazan por su número al guardar, así el texto puede citar una tabla antes de que
aparezca.
"""

import re
from xml.sax.saxutils import escape

from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import parse_xml
from docx.oxml.ns import qn
from docx.shared import Cm, Pt

FUENTE = "Times New Roman"
SANGRIA = Cm(0.63)
NS = ('xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math" '
      'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"')

# ----------------------------------------------------------------------------
# Ecuaciones (OMML)
# ----------------------------------------------------------------------------


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


def func(nombre, e):
    return f"<m:func><m:fName>{tx(nombre)}</m:fName><m:e>{e}</m:e></m:func>"


def negrita(e):
    """Vector en negrita (estilo bi)."""
    return re.sub(r"<m:r>(?!<m:rPr>)", '<m:r><m:rPr><m:sty m:val="bi"/></m:rPr>', e)


# ----------------------------------------------------------------------------
# Texto
# ----------------------------------------------------------------------------


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
    """Admite **negrita**, ~subíndice~ y ^superíndice^; x0..x3 y w0..w3 van con subíndice."""
    texto = re.sub(r"(?<![\w.])([xw])([0-3])(?![\w(])", r"\1~\2~", texto)
    negrita_activa = False
    for trozo in re.split(r"(\*\*|~[^~]+~|\^[^^]+\^)", texto):
        if trozo == "**":
            negrita_activa = not negrita_activa
            continue
        if not trozo:
            continue
        subindice = trozo.startswith("~") and trozo.endswith("~") and len(trozo) > 2
        superindice = trozo.startswith("^") and trozo.endswith("^") and len(trozo) > 2
        run = p.add_run(trozo[1:-1] if subindice or superindice else trozo)
        run.bold = negrita or negrita_activa
        run.italic = cursiva
        # Ambos usan w:vertAlign: asignar None al otro borraría el que sí se aplicó
        if subindice:
            run.font.subscript = True
        elif superindice:
            run.font.superscript = True
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


class Informe:
    """Inserta bloques uno tras otro a partir de un elemento de la plantilla."""

    def __init__(self, doc, ancla):
        self.doc = doc
        self.ultimo = ancla
        self.contador = {"tab": 0, "fig": 0, "eq": 0}
        self.etiquetas = {}

    def _colocar(self, el):
        self.ultimo.addnext(el)
        self.ultimo = el

    def _nuevo(self):
        p = self.doc.add_paragraph()
        self._colocar(p._p)
        return p

    def _registrar(self, tipo, clave):
        self.contador[tipo] += 1
        if clave:
            self.etiquetas[f"{tipo}:{clave}"] = self.contador[tipo]
        return self.contador[tipo]

    def texto(self, t, **kw):
        p = self._nuevo()
        agregar_texto(p, t)
        return formato(p, **kw)

    def titulo(self, t, sangria=SANGRIA, antes=6):
        p = self._nuevo()
        agregar_texto(p, t, negrita=True)
        p.paragraph_format.keep_with_next = True
        return formato(p, WD_ALIGN_PARAGRAPH.LEFT, sangria, antes=antes, despues=4)

    def lista(self, items, numerada=False, sangria=Cm(1.27)):
        for k, it in enumerate(items, 1):
            p = self._nuevo()
            agregar_texto(p, (f"{k}." if numerada else "•") + "\t" + it)
            formato(p, sangria=sangria, primera=Cm(-0.63), despues=3)
            p.paragraph_format.tab_stops.add_tab_stop(sangria)

    def ecuacion(self, omml, clave=None):
        """Ecuación en modo display, centrada, con su número a la derecha (tabla sin bordes)."""
        n = self._registrar("eq", clave)
        t = self.doc.add_table(rows=1, cols=2)
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        izq, der = t.rows[0].cells
        izq.width, der.width = Cm(13.6), Cm(1.4)
        p = izq.paragraphs[0]
        formato(p, WD_ALIGN_PARAGRAPH.CENTER, sangria=0, interlineado=1.0, antes=4, despues=4)
        p._p.append(parse_xml(
            f'<m:oMathPara {NS}><m:oMathParaPr><m:jc m:val="center"/></m:oMathParaPr>'
            f"<m:oMath>{omml}</m:oMath></m:oMathPara>"))
        q = der.paragraphs[0]
        agregar_texto(q, f"({n})")
        formato(q, WD_ALIGN_PARAGRAPH.RIGHT, sangria=0, interlineado=1.0, despues=0)
        for celda in (izq, der):
            celda._tc.get_or_add_tcPr().append(parse_xml(f'<w:vAlign {NS} w:val="center"/>'))
        self._colocar(t._tbl)
        return n

    def _leyenda(self, tipo, clave, t, fuente=None):
        n = self._registrar(tipo, clave)
        p = self._nuevo()
        agregar_texto(p, f"**{'Tabla' if tipo == 'tab' else 'Ilustración'} {n}.** {t}")
        formato(p, WD_ALIGN_PARAGRAPH.CENTER, sangria=0, interlineado=1.0,
                antes=6 if tipo == "tab" else 2, despues=2 if tipo == "tab" else 4)
        if tipo == "tab":
            p.paragraph_format.keep_with_next = True
        if fuente:
            q = self._nuevo()
            agregar_texto(q, f"Fuente: {fuente}", cursiva=True)
            formato(q, WD_ALIGN_PARAGRAPH.CENTER, sangria=0, interlineado=1.0, despues=10)
        return n

    def imagen(self, ruta, ancho_cm, titulo, clave=None, fuente="Elaboración propia."):
        p = self._nuevo()
        formato(p, WD_ALIGN_PARAGRAPH.CENTER, sangria=0, interlineado=1.0, antes=6, despues=2)
        p.paragraph_format.keep_with_next = True
        p.add_run().add_picture(str(ruta), width=Cm(ancho_cm))
        return self._leyenda("fig", clave, titulo, fuente)

    def tabla(self, titulo, encabezado, filas, clave=None, anchos=None,
              fuente="Elaboración propia.", alinear=None):
        n = self._leyenda("tab", clave, titulo)
        t = self.doc.add_table(rows=1, cols=len(encabezado))
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
        self._nuevo().add_run().add_break(WD_BREAK.PAGE)

    def resolver_referencias(self):
        """Reemplaza {tab:x}, {fig:x} y {eq:x} por su número en todo el documento."""
        patron = re.compile(r"\{(tab|fig|eq):([\w-]+)\}")

        def numero(m):
            clave = f"{m.group(1)}:{m.group(2)}"
            if clave not in self.etiquetas:
                raise KeyError(f"Referencia sin destino: {clave}")
            return str(self.etiquetas[clave])

        for t_el in self.doc.element.body.iter(qn("w:t")):
            if t_el.text and "{" in t_el.text:
                t_el.text = patron.sub(numero, t_el.text)


def pie_pagina_numerado(doc):
    """Pie centrado "Página X de Y" en todas las variantes de pie de la sección."""
    campo = ('<w:fldSimple {ns} w:instr=" {instr} "><w:r><w:rPr><w:rFonts w:ascii="{f}" '
             'w:hAnsi="{f}"/><w:sz w:val="24"/></w:rPr><w:t>1</w:t></w:r></w:fldSimple>')
    for seccion in doc.sections:
        for pie in (seccion.footer, seccion.first_page_footer, seccion.even_page_footer):
            pie.is_linked_to_previous = False
            for q in pie.paragraphs[1:]:
                q._p.getparent().remove(q._p)
            q = pie.paragraphs[0]
            for run in list(q.runs):
                run._element.getparent().remove(run._element)
            q.alignment = WD_ALIGN_PARAGRAPH.CENTER
            fuente_run(q.add_run("Página "))
            q._p.append(parse_xml(campo.format(ns=NS, instr="PAGE", f=FUENTE)))
            fuente_run(q.add_run(" de "))
            q._p.append(parse_xml(campo.format(ns=NS, instr="NUMPAGES", f=FUENTE)))


def poner_carrera(doc, carrera="SOFTWARE"):
    """Rellena el desplegable "Carrera de ..." del encabezado de la plantilla."""
    for seccion in doc.sections:
        for cab in (seccion.header, seccion.first_page_header, seccion.even_page_header):
            for sdt in cab._element.iter(qn("w:sdt")):
                for marcador in list(sdt.iter(qn("w:showingPlcHdr"))):
                    marcador.getparent().remove(marcador)
                for t_el in sdt.iter(qn("w:t")):
                    if "Elige" in (t_el.text or ""):
                        t_el.text = carrera
                        rpr = t_el.getparent().find(qn("w:rPr"))
                        rpr.getparent().replace(rpr, parse_xml(
                            f'<w:rPr {NS}><w:rFonts w:ascii="{FUENTE}" w:hAnsi="{FUENTE}"/>'
                            '<w:b/><w:sz w:val="18"/></w:rPr>'))
