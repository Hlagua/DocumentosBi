"""
==============================================================================
UNIVERSIDAD TÉCNICA DE AMBATO - Inteligencia de Negocios (Proyecto final)
AUTORES: Alison Marcela Cobos Taco / Henry Daniel Lagua Flores
==============================================================================
ARCHIVO: proyecto_final/entrenar_S2.py

Entrena la red neuronal del sistema S2 · Propósito de la orden permanente.

  Pregunta:  ¿Para qué es una orden de pago permanente nueva?
  Clases:    hogar (SIPO), préstamo (UVER), seguro (POJISTNE), arrendamiento (LEASING) (4 clases, softmax)
  Datos:     datos/S2_ordenes.csv (5,092 órdenes, 13 X, partición 60/20/20 por cuenta)
  Balanceo:  Las clases están desbalanceadas: se repiten casos de las clases pequeñas solo en entrenamiento (sobremuestreo 50/50).
  Resultado: 64 → 32 neuronas con sigmoide; 82.2 % en prueba (85.4 % balanceada) frente a 75.0 % (78.5 %) del softmax lineal

El procedimiento es el mismo para todos los sistemas y está en
02_entrenar_redes.py (función entrenar_sistema): z-score, todas las X frente a
PCA al 95 %, búsqueda de 5 arquitecturas tanh/sigmoide en validación, Adam con
lotes de 15 y parada temprana, softmax lineal de referencia, validación cruzada
estratificada de 5 pliegues agrupada por cuenta y evaluación final en prueba.

Guarda en proyecto_final/modelos_sobremuestreo/: S2_red.keras, S2_preprocesamiento.json y
S2_metricas.json (los mismos archivos que usa el aplicativo).

Uso (desde la raíz del repositorio):   python proyecto_final/entrenar_S2.py
Tiempo aproximado: unos 10 minutos con el equipo enchufado.
==============================================================================
"""

import importlib.util
import sys
from pathlib import Path

DIR = Path(__file__).resolve().parent

SISTEMA = "S2"
BALANCEO = "sobremuestreo"
CARPETA = "modelos_sobremuestreo"          # carpeta de la que el aplicativo carga este sistema


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
