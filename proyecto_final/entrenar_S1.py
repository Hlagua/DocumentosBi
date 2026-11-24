"""
==============================================================================
UNIVERSIDAD TÉCNICA DE AMBATO - Inteligencia de Negocios (Proyecto final)
AUTORES: Alison Marcela Cobos Taco / Henry Daniel Lagua Flores
==============================================================================
ARCHIVO: proyecto_final/entrenar_S1.py

Entrena la red neuronal del sistema S1 · Tipo de transacción.

  Pregunta:  ¿Qué tipo de movimiento es una transacción nueva?
  Clases:    depósito en efectivo, retiro, transferencia enviada, transferencia recibida (4 clases, softmax)
  Datos:     datos/S1_transacciones.csv (24,000 transacciones (6,000 por clase), 12 X, partición 60/20/20 por cuenta)
  Balanceo:  El dataset ya está balanceado, así que se entrena con datos reales (los pesos por clase quedan iguales).
  Resultado: 64 → 32 neuronas con sigmoide; 76.9 % en prueba frente a 58.4 % del softmax lineal

El procedimiento es el mismo para todos los sistemas y está en
02_entrenar_redes.py (función entrenar_sistema): z-score, todas las X frente a
PCA al 95 %, búsqueda de 5 arquitecturas tanh/sigmoide en validación, Adam con
lotes de 15 y parada temprana, softmax lineal de referencia, validación cruzada
estratificada de 5 pliegues agrupada por cuenta y evaluación final en prueba.

Guarda en proyecto_final/modelos/: S1_red.keras, S1_preprocesamiento.json y
S1_metricas.json (los mismos archivos que usa el aplicativo).

Uso (desde la raíz del repositorio):   python proyecto_final/entrenar_S1.py
Tiempo aproximado: unos 25 minutos con el equipo enchufado (más de 2 horas con batería).
==============================================================================
"""

import importlib.util
import sys
from pathlib import Path

DIR = Path(__file__).resolve().parent

SISTEMA = "S1"
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
