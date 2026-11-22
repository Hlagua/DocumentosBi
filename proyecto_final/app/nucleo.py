"""
Núcleo del aplicativo: convierte lo que el usuario ESCRIBE en el formulario en
el vector X del modelo, comprueba que tenga exactamente la misma dimensión
que la red, aplica el mismo preprocesamiento del entrenamiento y predice con
la red neuronal (salida softmax).

No usa Flask: se puede probar desde la consola.
"""

import json
import os
import re
import unicodedata
from datetime import date, datetime
from pathlib import Path

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")
os.environ.setdefault("TF_ENABLE_ONEDNN_OPTS", "0")

import numpy as np
import pandas as pd
import keras

RAIZ = Path(__file__).resolve().parents[1]
DATOS = RAIZ / "datos"
MODELOS = RAIZ / "modelos"

# Versión de la red que usa el aplicativo en cada sistema:
#   "modelos"               -> datos reales con pesos por clase
#   "modelos_sobremuestreo" -> entrenamiento con clases balanceadas 50/50
# S1 ya estaba balanceado (6,000 por clase), por eso solo tiene una versión.
# Decisión del 2026-11-22: clases balanceadas en S2, S3 y S4.
VERSION_POR_SISTEMA = {
    "S1": "modelos",
    "S2": "modelos_sobremuestreo",
    "S3": "modelos_sobremuestreo",
    "S4": "modelos_sobremuestreo",
}
SISTEMAS = ["S1", "S2", "S3", "S4"]
UMBRAL_FRONTERA = 0.10   # diferencia de probabilidad entre las dos clases más probables
ARCHIVOS = {
    "S1": DATOS / "S1_transacciones.csv",
    "S2": DATOS / "S2_ordenes.csv",
    "S3": DATOS / "S3_saldo_mensual.csv",
    "S4": DATOS / "S4_prestamos.csv",
}
FUENTES = {
    "S1": "Fact_Transacciones (1,056,320 movimientos) + Dim_Cliente + Dim_Distrito",
    "S2": "Fact_Ordenes (6,471 órdenes; 5,092 con propósito) + Dim_Cliente + Dim_Cuenta + Dim_Distrito",
    "S3": "Fact_Saldo_Cuenta_Mensual (185,615 meses cuenta × mes) + Dim_Cliente + Dim_Distrito",
    "S4": "Fact_Prestamos (682 préstamos) + historial previo de Fact_Transacciones + Dim_Distrito",
}


class ErrorEntrada(ValueError):
    """Error en un dato escrito por el usuario (se muestra junto al campo)."""

    def __init__(self, campo, mensaje):
        super().__init__(mensaje)
        self.campo = campo
        self.mensaje = mensaje


def normalizar(texto):
    texto = unicodedata.normalize("NFKD", str(texto))
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return " ".join(texto.lower().replace("_", " ").split())


# ----------------------------------------------------------------------------
# Lectura de valores escritos a mano
# ----------------------------------------------------------------------------
RE_DECIMAL = re.compile(r"^-?\d+([.,]\d+)?$")
RE_ENTERO = re.compile(r"^-?\d+$")
RE_FECHA = re.compile(r"^\d{4}-\d{2}-\d{2}$")
RE_PERIODO = re.compile(r"^\d{4}-\d{2}$")
RE_NOMBRE = re.compile(r"^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ .\-]+$")

# Campos numéricos que SÍ pueden ser negativos (saldos y cambios de saldo).
NEGATIVOS = {"saldo_despues", "saldo_fin_mes", "saldo_promedio_mes", "saldo_min_mes", "saldo_max_mes",
             "cambio_saldo_mes", "saldo_minimo_previo"}
# Rangos lógicos (no de entrenamiento): valores imposibles se rechazan.
LIMITES = {"edad": (10, 110), "plazo_meses": (1, 360), "ordenes_activas_cuenta": (1, 50),
           "num_movimientos_mes": (0, 500), "meses_historial": (0, 600)}
ANIOS = (1900, 2100)


def formato_de(campo):
    """Cómo se escribe cada campo: lo usan el servidor y el formulario (máscara en el navegador)."""
    nombre, tipo = campo["campo"], campo["tipo"]
    if nombre == "distrito":
        return "nombre"
    if nombre == "sexo":
        return "sexo"
    if nombre == "tiene_prestamo":
        return "sino"
    return tipo  # decimal, entero, fecha, periodo


def leer_decimal(campo, texto, negativo=False):
    t = str(texto).strip().replace(" ", "")
    if not t:
        raise ErrorEntrada(campo, "Este dato es obligatorio.")
    if not RE_DECIMAL.match(t):
        raise ErrorEntrada(campo, f"«{texto}» no es un número válido. Use solo dígitos y, si hace falta, "
                                  "un punto o coma decimal (por ejemplo 1250.50).")
    valor = float(t.replace(",", "."))
    if valor < 0 and not negativo:
        raise ErrorEntrada(campo, "Este dato no puede ser negativo.")
    return valor


def leer_entero(campo, texto, negativo=False):
    t = str(texto).strip().replace(" ", "")
    if not RE_ENTERO.match(t):
        raise ErrorEntrada(campo, f"«{texto}» no es un número entero (solo dígitos, sin decimales).")
    valor = int(t)
    if valor < 0 and not negativo:
        raise ErrorEntrada(campo, "Este dato no puede ser negativo.")
    if campo in LIMITES:
        lo, hi = LIMITES[campo]
        if not lo <= valor <= hi:
            raise ErrorEntrada(campo, f"Debe estar entre {lo} y {hi}.")
    return valor


def leer_fecha(campo, texto):
    t = str(texto).strip()
    if not RE_FECHA.match(t):
        raise ErrorEntrada(campo, "Escriba la fecha como AAAA-MM-DD (por ejemplo 1997-05-14).")
    try:
        d = datetime.strptime(t, "%Y-%m-%d").date()
    except ValueError:
        raise ErrorEntrada(campo, f"«{texto}» no es una fecha que exista.")
    if not ANIOS[0] <= d.year <= ANIOS[1]:
        raise ErrorEntrada(campo, f"El año debe estar entre {ANIOS[0]} y {ANIOS[1]}.")
    return d


def leer_periodo(campo, texto):
    t = str(texto).strip()
    if not RE_PERIODO.match(t):
        raise ErrorEntrada(campo, "Escriba el mes como AAAA-MM (por ejemplo 1997-05).")
    anio, mes = int(t[:4]), int(t[5:])
    if not 1 <= mes <= 12:
        raise ErrorEntrada(campo, "El mes debe estar entre 01 y 12.")
    if not ANIOS[0] <= anio <= ANIOS[1]:
        raise ErrorEntrada(campo, f"El año debe estar entre {ANIOS[0]} y {ANIOS[1]}.")
    return anio, mes


def leer_sexo(campo, texto):
    t = normalizar(texto)
    if t == "f":
        return 1
    if t == "m":
        return 0
    raise ErrorEntrada(campo, "Escriba solo M o F.")


def leer_si_no(campo, texto):
    t = normalizar(texto)
    if t == "si":
        return 1
    if t == "no":
        return 0
    raise ErrorEntrada(campo, "Escriba si o no.")


# ----------------------------------------------------------------------------
# Sistema predictivo
# ----------------------------------------------------------------------------
class Sistema:
    def __init__(self, codigo, diccionario, resumen, distritos):
        self.codigo = codigo
        self.info = diccionario[codigo]
        self.titulo = self.info["titulo"]
        self.campos = [dict(c) for c in self.info["campos"]]
        ejemplos = {"fecha": "AAAA-MM-DD", "periodo": "AAAA-MM", "sexo": "M o F", "sino": "si o no",
                    "nombre": "nombre del distrito", "entero": "número entero", "decimal": "número"}
        for c in self.campos:
            c["formato"] = formato_de(c)
            c["negativo"] = c["campo"] in NEGATIVOS
            c["placeholder"] = ejemplos[c["formato"]] + (" (puede ser negativo)" if c["negativo"] else "")
            c["maxlength"] = {"fecha": 10, "periodo": 7, "sexo": 1, "sino": 2, "nombre": 40,
                              "entero": 6, "decimal": 15}[c["formato"]]
        self.resumen = resumen[codigo]
        self.rangos = resumen[codigo]["rangos_X"]
        self.descripcion = resumen[codigo]["descripcion"]
        self.distritos = distritos
        carpeta = RAIZ / VERSION_POR_SISTEMA.get(codigo, "modelos")
        if not (carpeta / f"{codigo}_red.keras").exists():
            carpeta = MODELOS
        self.carpeta_modelo = carpeta.name
        with open(carpeta / f"{codigo}_preprocesamiento.json", encoding="utf-8") as f:
            self.pre = json.load(f)
        with open(carpeta / f"{codigo}_metricas.json", encoding="utf-8") as f:
            self.metricas = json.load(f)
        self.red = keras.models.load_model(carpeta / f"{codigo}_red.keras")
        balanceo = self.metricas.get("balanceo", {})
        self.balanceo = {
            "estrategia": balanceo.get("estrategia", "pesos"),
            "texto": ("Clases balanceadas 50/50 en entrenamiento (sobremuestreo)"
                      if balanceo.get("estrategia") == "sobremuestreo"
                      else ("Clases balanceadas en el dataset" if codigo == "S1"
                            else "Datos reales con pesos por clase")),
            "por_clase": balanceo.get("entrenamiento_usado_por_clase"),
        }
        self.orden_X = self.pre["orden_X"]
        self.clases = self.pre["clases"]
        self.media = np.array(self.pre["media"])
        self.desv = np.array(self.pre["desviacion"])
        self.pca = np.array(self.pre["pca_componentes"]) if self.pre["usa_pca"] else None
        # La dimensión de entrada de la red debe coincidir con la del preprocesamiento
        assert self.red.input_shape[-1] == self.pre["dimension_red"]

    # -- formulario -> X ------------------------------------------------------
    def construir_X(self, formulario):
        """Devuelve (X como dict en orden_X, lista de errores, avisos)."""
        valores, errores = {}, []
        for campo in self.campos:
            nombre, tipo = campo["campo"], campo["tipo"]
            texto = formulario.get(nombre, "")
            try:
                if str(texto).strip() == "":
                    raise ErrorEntrada(nombre, "Este dato es obligatorio.")
                if nombre == "distrito":
                    if not RE_NOMBRE.match(str(texto).strip()):
                        raise ErrorEntrada(nombre, "El nombre del distrito solo lleva letras, espacios, puntos o guiones.")
                    clave = normalizar(texto)
                    fila = self.distritos.get(clave)
                    if fila is None:
                        raise ErrorEntrada(nombre, f"No existe un distrito llamado «{texto}» en el banco.")
                    for c in campo["genera"]:
                        valores[c] = float(fila[c])
                    valores["_distrito"] = fila["nombre_distrito"]
                elif nombre == "sexo":
                    valores["es_mujer"] = leer_sexo(nombre, texto)
                elif nombre == "tiene_prestamo":
                    valores["tiene_prestamo"] = leer_si_no(nombre, texto)
                elif tipo == "fecha":
                    d = leer_fecha(nombre, texto)
                    valores.update(anio=d.year, mes=d.month, dia=d.day, dia_semana=d.weekday())
                elif tipo == "periodo":
                    valores["anio"], valores["mes"] = leer_periodo(nombre, texto)
                elif tipo == "entero":
                    valores[campo["genera"][0]] = leer_entero(nombre, texto, nombre in NEGATIVOS)
                else:
                    valores[campo["genera"][0]] = leer_decimal(nombre, texto, nombre in NEGATIVOS)
            except ErrorEntrada as e:
                errores.append((e.campo, e.mensaje))

        if not errores:
            errores += self._derivados(valores)
        if errores:
            return None, errores, []

        X = {c: float(valores[c]) for c in self.orden_X}
        avisos = [
            f"{c} = {X[c]:,.2f} está fuera del rango visto al entrenar "
            f"({self.rangos[c]['min']:,.2f} a {self.rangos[c]['max']:,.2f}); la predicción es menos confiable."
            for c in self.orden_X
            if not (self.rangos[c]["min"] <= X[c] <= self.rangos[c]["max"])
        ]
        if "_distrito" in valores:
            X["_distrito"] = valores["_distrito"]
        return X, [], avisos

    def _derivados(self, v):
        errores = []
        if self.codigo == "S1":
            if v["monto"] <= 0:
                errores.append(("monto", "El monto debe ser mayor que cero."))
            v["monto"] = abs(v["monto"])
        if self.codigo == "S2":
            if v["monto_orden"] <= 0:
                errores.append(("monto_orden", "El monto debe ser mayor que cero."))
            if v["tiene_prestamo"] == 0 and v["cuota_prestamo"] != 0:
                errores.append(("cuota_prestamo", "Si la cuenta no tiene préstamo, la cuota debe ser 0."))
        if self.codigo == "S4":
            if v["plazo_meses"] <= 0:
                errores.append(("plazo_meses", "El plazo debe ser mayor que cero."))
            elif v["monto_prestamo"] <= 0:
                errores.append(("monto_prestamo", "El monto debe ser mayor que cero."))
            elif v["saldo_promedio_previo"] <= 0:
                errores.append(("saldo_promedio_previo", "El saldo promedio debe ser mayor que cero."))
            else:
                v["cuota_mensual"] = v["monto_prestamo"] / v["plazo_meses"]
                v["ratio_cuota_saldo"] = v["cuota_mensual"] / v["saldo_promedio_previo"]
        return errores

    # -- X -> predicción ------------------------------------------------------
    def vector(self, X):
        x = np.array([[X[c] for c in self.orden_X]], dtype=float)
        if x.shape[1] != self.pre["dimension_entrada"]:
            raise ValueError(
                f"Dimensión incorrecta: X nueva es 1×{x.shape[1]} y el modelo espera 1×{self.pre['dimension_entrada']}."
            )
        return x

    def transformar(self, x):
        z = (x - self.media) / self.desv
        return z @ self.pca.T if self.pca is not None else z

    def predecir(self, X, umbral_frontera=UMBRAL_FRONTERA):
        x = self.vector(X)
        z = self.transformar(x)
        p = self.red.predict(z, verbose=0)[0]
        k = int(np.argmax(p))
        # Frontera de decisión: las dos clases más probables casi empatadas.
        # La red igual asigna UNA clase (la de mayor probabilidad, argmax de softmax).
        segunda = int(np.argsort(p)[-2])
        margen = float(p[k] - p[segunda])
        return {
            "clase": self.clases[k],
            "indice": k,
            "frontera": {
                "en_frontera": margen < umbral_frontera,
                "margen": margen,
                "umbral": umbral_frontera,
                "clase_asignada": self.clases[k],
                "otra_clase": self.clases[segunda],
                "prob_asignada": float(p[k]),
                "prob_otra": float(p[segunda]),
            },
            "probabilidades": {c: float(v) for c, v in zip(self.clases, p)},
            "x": x[0].tolist(),
            "z": z[0].tolist(),
            "dimension_x": x.shape[1],
            "dimension_red": z.shape[1],
        }

    def monto_maximo(self, X, umbral=0.5, paso=1000, tope=600000):
        """Solo S4: mayor monto (mismo plazo y perfil) con probabilidad de impago menor que el umbral."""
        if self.codigo != "S4":
            return None
        montos = np.arange(paso, tope + paso, paso, dtype=float)
        filas = []
        for m in montos:
            fila = dict(X)
            fila["monto_prestamo"] = m
            fila["cuota_mensual"] = m / fila["plazo_meses"]
            fila["ratio_cuota_saldo"] = fila["cuota_mensual"] / fila["saldo_promedio_previo"]
            filas.append([fila[c] for c in self.orden_X])
        p_impago = self.red.predict(self.transformar(np.array(filas)), verbose=0, batch_size=1024)[:, 1]
        aceptables = montos[p_impago < umbral]
        return {
            "umbral": umbral,
            "monto_maximo": float(aceptables.max()) if len(aceptables) else None,
            "curva": [(float(m), float(p)) for m, p in zip(montos[::10], p_impago[::10])],
        }


def cargar_sistemas():
    with open(DATOS / "diccionario_caracteristicas.json", encoding="utf-8") as f:
        diccionario = json.load(f)
    with open(DATOS / "resumen_datasets.json", encoding="utf-8") as f:
        resumen = json.load(f)
    tabla = pd.read_csv(DATOS / "distritos.csv")
    distritos = {normalizar(r["nombre_distrito"]): r for r in tabla.to_dict("records")}
    return {s: Sistema(s, diccionario, resumen, distritos) for s in SISTEMAS}
