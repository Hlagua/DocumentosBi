"""
==============================================================================
UNIVERSIDAD TÉCNICA DE AMBATO - Inteligencia de Negocios (Proyecto final)
AUTORES: Alison Marcela Cobos Taco / Henry Daniel Lagua Flores
==============================================================================
ARCHIVO: proyecto_final/entrenar_S4.py

Entrena la red neuronal del sistema S4 · Mora al corte (31/12/1998) de un préstamo.

  Pregunta:  ¿Un préstamo estaría al día o en mora al corte del 31/12/1998?
  Clases:    al día al corte (A o C), en mora o impago al corte (B o D) (2 clases, softmax de 2 neuronas)
  Datos:     datos/S4_prestamos.csv (682 préstamos, 16 X, partición 60/20/20 estratificada (un préstamo por cuenta))
  Balanceo:  Las clases están desbalanceadas (606 frente a 76): se usan pesos por clase en la pérdida.
  Resultado: PCA 16 → 10 y 64 → 32 neuronas con tanh; 83.1 % en prueba (81.7 % balanceada, AUC 0.829)

El procedimiento es el mismo para todos los sistemas y está en
02_entrenar_redes.py (función entrenar_sistema): z-score, todas las X frente a
PCA al 95 %, búsqueda de 5 arquitecturas tanh/sigmoide en validación, Adam con
lotes de 15 y parada temprana, softmax lineal de referencia, validación cruzada
estratificada de 5 pliegues agrupada por cuenta y evaluación final en prueba.

Guarda en proyecto_final/modelos/: S4_red.keras, S4_preprocesamiento.json y
S4_metricas.json (los mismos archivos que usa el aplicativo).

Uso (desde la raíz del repositorio):   python proyecto_final/entrenar_S4.py
Tiempo aproximado: unos 5 minutos.
==============================================================================
"""

import importlib.util
import sys
from pathlib import Path

DIR = Path(__file__).resolve().parent

SISTEMA = "S4"
BALANCEO = "pesos"
CARPETA = "modelos"          # carpeta de la que el aplicativo carga este sistema


def cargar_procedimiento():
    """Importa 02_entrenar_redes.py (su nombre empieza con un número, por eso no se usa import directo)."""
    spec = importlib.util.spec_from_file_location("entrenar_redes", DIR / "02_entrenar_redes.py")
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


if __name__ == "__main__":
    # Opcional: --salida OTRA_CARPETA para entrenar sin reemplazar el modelo del aplicativo
    salida = sys.argv[sys.argv.index("--salida") + 1] if "--salida" in sys.argv else CARPETA
    cargar_procedimiento().entrenar_sistema(SISTEMA, balanceo=BALANCEO, salida=salida)
