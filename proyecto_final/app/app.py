"""
==============================================================================
UNIVERSIDAD TÉCNICA DE AMBATO - Inteligencia de Negocios (Proyecto final)
AUTORES: Alison Marcela Cobos Taco / Henry Daniel Lagua Flores
==============================================================================
Aplicativo web de los sistemas predictivos con redes neuronales.

  * Cada sistema tiene un formulario donde se ESCRIBEN datos nuevos: solo
    cajas de texto, sin listas desplegables (el distrito sugiere nombres
    mientras se escribe). La dirección raíz abre el dashboard de S1.
  * Lo escrito se convierte en el vector X con la misma dimensión que la red,
    se aplica el preprocesamiento del entrenamiento y la red devuelve la
    clase con las probabilidades de la capa softmax.
  * Cada predicción queda registrada (SQLite y, si está disponible, el Data
    Mart Kimball en SQL Server).

Ejecutar desde la raíz del repositorio:
    python proyecto_final/app/app.py
y abrir http://127.0.0.1:5000
==============================================================================
"""

import sys
from pathlib import Path

from flask import Flask, abort, redirect, render_template, request, url_for

sys.path.insert(0, str(Path(__file__).resolve().parent))
import dashboard  # noqa: E402
import nucleo  # noqa: E402
import registro  # noqa: E402

app = Flask(__name__)
SISTEMAS = nucleo.cargar_sistemas()


@app.route("/")
def inicio():
    # No hay página de inicio: la dirección raíz abre el dashboard de la red del primer sistema.
    return redirect(url_for("red", codigo=next(iter(SISTEMAS))))


@app.route("/predecir/<codigo>", methods=["GET", "POST"])
def predecir(codigo):
    sistema = SISTEMAS.get(codigo.upper())
    if sistema is None:
        abort(404)
    escrito, errores, avisos, resultado, montos, destinos = {}, {}, [], None, None, []
    if request.method == "POST":
        escrito = {c["campo"]: request.form.get(c["campo"], "").strip() for c in sistema.campos}
        X, lista_errores, avisos = sistema.construir_X(escrito)
        errores = dict(lista_errores)
        if X is not None:
            resultado = sistema.predecir(X)
            resultado["X"] = X
            montos = sistema.monto_maximo(X)
            destinos = registro.guardar(sistema.codigo, sistema.titulo, escrito, resultado)
    return render_template(
        "formulario.html", s=sistema, escrito=escrito, errores=errores, avisos=avisos,
        resultado=resultado, montos=montos, destinos=destinos, sistemas=SISTEMAS,
    )


@app.route("/red/<codigo>")
def red(codigo):
    sistema = SISTEMAS.get(codigo.upper())
    if sistema is None:
        abort(404)
    nuevos = registro.historial(30, sistema.codigo)
    figs = dashboard.figuras(sistema, nucleo.ARCHIVOS[sistema.codigo], nuevos)
    return render_template("red.html", s=sistema, m=sistema.metricas, figs=figs, nuevos=nuevos,
                           fuente=nucleo.FUENTES[sistema.codigo], sistemas=SISTEMAS)


@app.route("/playground/")
@app.route("/playground/<codigo>")
def playground(codigo="S1"):
    sistema = SISTEMAS.get(codigo.upper())
    if sistema is None:
        abort(404)
    grabado = (nucleo.RAIZ / "playground" / f"{sistema.codigo}_entrenamiento.json").exists()
    return render_template("playground.html", s=sistema, sistemas=SISTEMAS, grabado=grabado)


@app.route("/playground/<codigo>/datos.json")
def playground_datos(codigo):
    from flask import send_from_directory

    if codigo.upper() not in SISTEMAS:
        abort(404)
    return send_from_directory(nucleo.RAIZ / "playground", f"{codigo.upper()}_entrenamiento.json",
                               mimetype="application/json", max_age=0)


@app.route("/historial")
def historial():
    return render_template("historial.html", filas=registro.historial(100), sistemas=SISTEMAS)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
