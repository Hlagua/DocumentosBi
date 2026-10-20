"""Arma perceptron_taller.ipynb a partir de perceptron_taller.py, una celda por actividad."""

import json
import re
from pathlib import Path

CARPETA = Path(__file__).resolve().parent
codigo = (CARPETA / "perceptron_taller.py").read_text(encoding="utf-8")
# En Jupyter/Colab no existe __file__ ni hace falta el backend Agg
codigo = codigo.replace("Path(__file__).resolve().parent", "Path.cwd()")
codigo = codigo.replace('matplotlib.use("Agg")\n', "")
codigo = codigo.replace('if __name__ == "__main__":\n    main()\n', "main()\n")

separador = "# " + "-" * 76 + "\n"
bloques = re.split(rf"{re.escape(separador)}(# .+\n){re.escape(separador)}", codigo)

def md(texto):
    return {"cell_type": "markdown", "metadata": {}, "source": texto}

def cod(texto):
    return {"cell_type": "code", "metadata": {}, "execution_count": None,
            "outputs": [], "source": texto.strip("\n") + "\n"}

celdas = [md("# Taller: perceptrón para clasificación binaria\n"
             "Inteligencia de Negocios. Implementación desde cero del seudocódigo de la "
             "diapositiva 4 de ANN.pdf. Coloque el CSV del dataset en la misma carpeta "
             "del notebook antes de ejecutar.")]
encabezado = bloques[0]
celdas.append(cod(encabezado.split('"""', 2)[2]))
for titulo, cuerpo in zip(bloques[1::2], bloques[2::2]):
    celdas.append(md("## " + titulo.lstrip("# ").strip()))
    if "def main" in cuerpo:
        defs, ejecucion = cuerpo.split("def main", 1)
        celdas.append(cod(defs))
        celdas.append(md("## Actividad 5. Ejecutar e interpretar el resultado"))
        celdas.append(cod("def main" + ejecucion))
    else:
        celdas.append(cod(cuerpo))

nb = {"cells": celdas, "metadata": {"kernelspec": {"display_name": "Python 3",
      "language": "python", "name": "python3"}, "language_info": {"name": "python"}},
      "nbformat": 4, "nbformat_minor": 5}
(CARPETA / "perceptron_taller.ipynb").write_text(json.dumps(nb, ensure_ascii=False, indent=1),
                                                encoding="utf-8")
print(len(celdas), "celdas")
