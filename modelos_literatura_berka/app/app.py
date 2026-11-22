"""
Aplicativo web Flask (puerto 5001) para los 5 modelos predictivos de la
literatura PKDD'99 / Berka con redes neuronales (sigmoide, softmax, lineal).
"""

import sys
from pathlib import Path

from flask import Flask, abort, render_template, request

sys.path.insert(0, str(Path(__file__).resolve().parent))
import dashboard  # noqa: E402
import nucleo  # noqa: E402
import registro  # noqa: E402

app = Flask(__name__)
SISTEMAS = nucleo.cargar_sistemas()


@app.route("/")
def inicio():
    return render_template("inicio.html", sistemas=SISTEMAS)


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
        resultado=resultado, montos=montos, destinos=destinos,
    )


@app.route("/red/<codigo>")
def red(codigo):
    sistema = SISTEMAS.get(codigo.upper())
    if sistema is None:
        abort(404)
    nuevos = registro.historial(30, sistema.codigo)
    figs = dashboard.figuras(sistema, nucleo.ARCHIVOS[sistema.codigo], nuevos)
    return render_template(
        "red.html", s=sistema, m=sistema.metricas, figs=figs, nuevos=nuevos,
        fuente=nucleo.FUENTES[sistema.codigo], sistemas=SISTEMAS,
    )


@app.route("/resumen")
def resumen():
    return render_template(
        "resumen.html", sistemas=SISTEMAS, grafico=dashboard.grafico_resumen(SISTEMAS),
        total=len(registro.historial(100000)),
    )


@app.route("/playground/")
@app.route("/playground/<codigo>")
def playground(codigo="M1"):
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
    return send_from_directory(
        nucleo.RAIZ / "playground", f"{codigo.upper()}_entrenamiento.json",
        mimetype="application/json", max_age=0,
    )


@app.route("/historial")
def historial():
    return render_template("historial.html", filas=registro.historial(100), sistemas=SISTEMAS)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5001, debug=False)
