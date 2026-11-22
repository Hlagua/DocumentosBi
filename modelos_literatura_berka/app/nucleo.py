"""
Núcleo de inferencia para los 5 modelos de la literatura PKDD'99 / Berka.
Soporta las 3 capas de salida vistas en clase:
  * sigmoid (clasificación binaria: M1, M2, M4)
  * softmax (clasificación multiclase: M3)
  * linear  (regresión continua: M5)
"""

import json
import os
import re
import unicodedata
from pathlib import Path

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")
os.environ.setdefault("TF_ENABLE_ONEDNN_OPTS", "0")

import numpy as np
import pandas as pd
import keras

RAIZ = Path(__file__).resolve().parents[1]
DATOS = RAIZ / "datos"
MODELOS = RAIZ / "modelos"

CODIGOS = ["M1", "M2", "M3", "M4", "M5"]
UMBRAL_FRONTERA = 0.10

ARCHIVOS = {
    "M1": DATOS / "M1_impago_prestamos.csv",
    "M2": DATOS / "M2_propension_tarjeta.csv",
    "M3": DATOS / "M3_segmentacion_clientes.csv",
    "M4": DATOS / "M4_fuga_clientes.csv",
    "M5": DATOS / "M5_pronostico_transacciones.csv",
}

FUENTES = {
    "M1": "Fact_Prestamos (682 préstamos) + Fact_Transacciones (< fecha_otorgamiento) + Dim_Distrito",
    "M2": "Adopcion_Producto (RETIRO_TARJETA, 4,500 cuentas) + Fact_Transacciones (sin retiros con tarjeta) + Dim_Distrito",
    "M3": "Perfiles financieros de 4,500 cuentas (K-Means 4 segmentos en entrenamiento) + Dim_Distrito",
    "M4": "Fact_Transacciones 1998 sin intereses (X = H1 1998, y = fuga/caída en H2 1998) + Dim_Distrito",
    "M5": "Fact_Transacciones 1997–1998 sin intereses (X = mes t y t-1, y = monto mes t+1) + Dim_Distrito",
}

RE_DECIMAL = re.compile(r"^-?\d+([.,]\d+)?$")
RE_ENTERO = re.compile(r"^-?\d+$")
RE_NOMBRE = re.compile(r"^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ .\-]+$")

NEGATIVOS = {
    "saldo_minimo_previo", "saldo_minimo_cuenta", "saldo_min_h1",
    "saldo_fin_h1", "saldo_fin_mes_t", "saldo_prom_mes_t",
}
LIMITES = {
    "edad": (10, 110), "plazo_meses": (1, 360), "ordenes_activas": (0, 50),
    "meses_historial": (1, 600), "meses_vida": (1, 600), "meses_activos_h1": (1, 6),
    "mes": (1, 12), "num_movimientos_t": (0, 500),
}


class ErrorEntrada(ValueError):
    def __init__(self, campo, mensaje):
        super().__init__(mensaje)
        self.campo = campo
        self.mensaje = mensaje


def normalizar(texto):
    texto = unicodedata.normalize("NFKD", str(texto))
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return " ".join(texto.lower().replace("_", " ").split())


def formato_de(campo):
    n = campo["campo"]
    if n == "distrito":
        return "nombre"
    if n == "sexo":
        return "sexo"
    if n == "tiene_prestamo":
        return "sino"
    return campo["tipo"]


def leer_decimal(campo, texto, negativo=False):
    t = str(texto).strip().replace(" ", "")
    if not t:
        raise ErrorEntrada(campo, "Este dato es obligatorio.")
    if not RE_DECIMAL.match(t):
        raise ErrorEntrada(campo, f"«{texto}» no es un número válido.")
    v = float(t.replace(",", "."))
    if v < 0 and not negativo:
        raise ErrorEntrada(campo, "Este dato no puede ser negativo.")
    return v


def leer_entero(campo, texto):
    t = str(texto).strip().replace(" ", "")
    if not RE_ENTERO.match(t):
        raise ErrorEntrada(campo, f"«{texto}» no es un entero válido.")
    v = int(t)
    if v < 0:
        raise ErrorEntrada(campo, "Este dato no puede ser negativo.")
    if campo in LIMITES:
        lo, hi = LIMITES[campo]
        if not lo <= v <= hi:
            raise ErrorEntrada(campo, f"Debe estar entre {lo} y {hi}.")
    return v


class ModeloSistema:
    def __init__(self, codigo, diccionario, resumen, distritos):
        self.codigo = codigo
        self.info = diccionario[codigo]
        self.titulo = self.info["titulo"]
        self.tipo = self.info["tipo"]          # "clasificacion" | "regresion"
        self.salida = self.info["salida"]      # "sigmoid" | "softmax" | "linear"
        self.resumen = resumen[codigo]
        self.descripcion = self.resumen["descripcion"]
        self.rangos = self.resumen["rangos_X"]
        self.distritos = distritos

        ejemplos = {"sexo": "M o F", "sino": "si o no", "nombre": "nombre del distrito",
                    "entero": "número entero", "decimal": "número"}
        self.campos = [dict(c) for c in self.info["campos"]]
        for c in self.campos:
            c["formato"] = formato_de(c)
            c["negativo"] = c["campo"] in NEGATIVOS
            c["placeholder"] = ejemplos[c["formato"]] + (" (puede ser negativo)" if c["negativo"] else "")

        self.pre = json.loads((MODELOS / f"{codigo}_preprocesamiento.json").read_text(encoding="utf-8"))
        self.metricas = json.loads((MODELOS / f"{codigo}_metricas.json").read_text(encoding="utf-8"))
        self.red = keras.models.load_model(MODELOS / f"{codigo}_red.keras")
        self.orden_X = self.pre["orden_X"]
        self.clases = self.pre.get("clases", [])
        self.media = np.array(self.pre["media"])
        self.desv = np.array(self.pre["desviacion"])
        self.pca = np.array(self.pre["pca_componentes"]) if self.pre["usa_pca"] else None
        self.y_media = self.pre.get("y_media")
        self.y_desv = self.pre.get("y_desv")

    def construir_X(self, formulario):
        valores, errores = {}, []
        for campo in self.campos:
            nombre, tipo = campo["campo"], campo["tipo"]
            texto = formulario.get(nombre, "")
            try:
                if str(texto).strip() == "":
                    raise ErrorEntrada(nombre, "Este dato es obligatorio.")
                if nombre == "distrito":
                    if not RE_NOMBRE.match(str(texto).strip()):
                        raise ErrorEntrada(nombre, "Solo letras, espacios, puntos o guiones.")
                    fila = self.distritos.get(normalizar(texto))
                    if fila is None:
                        raise ErrorEntrada(nombre, f"No existe el distrito «{texto}».")
                    for c in campo["genera"]:
                        valores[c] = float(fila[c])
                    valores["_distrito"] = fila["nombre_distrito"]
                elif nombre == "sexo":
                    t = normalizar(texto)
                    if t not in ("m", "f"):
                        raise ErrorEntrada(nombre, "Escriba solo M o F.")
                    valores["es_mujer"] = 1 if t == "f" else 0
                elif nombre == "tiene_prestamo":
                    t = normalizar(texto)
                    if t not in ("si", "no"):
                        raise ErrorEntrada(nombre, "Escriba si o no.")
                    valores["tiene_prestamo"] = 1 if t == "si" else 0
                elif tipo == "entero":
                    valores[campo["genera"][0]] = leer_entero(nombre, texto)
                else:
                    valores[campo["genera"][0]] = leer_decimal(nombre, texto, nombre in NEGATIVOS)
            except ErrorEntrada as e:
                errores.append((e.campo, e.mensaje))

        if not errores:
            if self.codigo == "M1":
                if valores["monto_prestamo"] <= 0:
                    errores.append(("monto_prestamo", "El monto debe ser mayor que cero."))
                elif valores["saldo_promedio_previo"] <= 0:
                    errores.append(("saldo_promedio_previo", "El saldo promedio previo debe ser mayor que cero."))
                else:
                    valores["cuota_mensual"] = valores["monto_prestamo"] / valores["plazo_meses"]
                    valores["ratio_cuota_saldo"] = valores["cuota_mensual"] / valores["saldo_promedio_previo"]
            elif self.codigo == "M3":
                valores["ratio_retiro_deposito"] = valores["retiro_mensual"] / max(valores["deposito_mensual"], 1.0)

        if errores:
            return None, errores, []

        X = {c: float(valores[c]) for c in self.orden_X}
        avisos = [
            f"{c} = {X[c]:,.2f} fuera del rango visto al entrenar ({self.rangos[c]['min']:,.2f} a {self.rangos[c]['max']:,.2f})."
            for c in self.orden_X
            if not (self.rangos[c]["min"] <= X[c] <= self.rangos[c]["max"])
        ]
        if "_distrito" in valores:
            X["_distrito"] = valores["_distrito"]
        return X, [], avisos

    def transformar(self, x):
        z = (x - self.media) / self.desv
        return z @ self.pca.T if self.pca is not None else z

    def predecir(self, X):
        x = np.array([[X[c] for c in self.orden_X]], dtype=float)
        z = self.transformar(x)
        raw = self.red.predict(z, verbose=0)[0]

        if self.tipo == "regresion":
            valor = max(0.0, float(raw[0] * self.y_desv + self.y_media))
            return {
                "tipo": "regresion",
                "valor": valor,
                "unidad": self.info.get("unidad", "CZK"),
                "x": x[0].tolist(),
                "z": z[0].tolist(),
                "dimension_x": x.shape[1],
                "dimension_red": z.shape[1],
            }

        if self.salida == "sigmoid":
            p1 = float(raw[0])
            probs = np.array([1.0 - p1, p1])
        else:
            probs = np.array(raw, dtype=float)

        k = int(np.argmax(probs))
        segunda = int(np.argsort(probs)[-2])
        margen = float(probs[k] - probs[segunda])
        return {
            "tipo": "clasificacion",
            "clase": self.clases[k],
            "indice": k,
            "frontera": {
                "en_frontera": margen < UMBRAL_FRONTERA,
                "margen": margen,
                "umbral": UMBRAL_FRONTERA,
                "clase_asignada": self.clases[k],
                "otra_clase": self.clases[segunda],
                "prob_asignada": float(probs[k]),
                "prob_otra": float(probs[segunda]),
            },
            "probabilidades": {c: float(v) for c, v in zip(self.clases, probs)},
            "x": x[0].tolist(),
            "z": z[0].tolist(),
            "dimension_x": x.shape[1],
            "dimension_red": z.shape[1],
        }

    def monto_maximo(self, X, umbral=0.5, paso=1000, tope=600000):
        if self.codigo != "M1":
            return None
        montos = np.arange(paso, tope + paso, paso, dtype=float)
        filas = []
        for m in montos:
            f = dict(X)
            f["monto_prestamo"] = m
            f["cuota_mensual"] = m / f["plazo_meses"]
            f["ratio_cuota_saldo"] = f["cuota_mensual"] / f["saldo_promedio_previo"]
            filas.append([f[c] for c in self.orden_X])
        p_imp = self.red.predict(self.transformar(np.array(filas)), verbose=0, batch_size=1024).ravel()
        ok = montos[p_imp < umbral]
        return {"umbral": umbral, "monto_maximo": float(ok.max()) if len(ok) else None}


def cargar_sistemas():
    dic = json.loads((DATOS / "diccionario_caracteristicas.json").read_text(encoding="utf-8"))
    res = json.loads((DATOS / "resumen_datasets.json").read_text(encoding="utf-8"))
    tabla = pd.read_csv(DATOS / "distritos.csv")
    distritos = {normalizar(r["nombre_distrito"]): r for r in tabla.to_dict("records")}
    return {c: ModeloSistema(c, dic, res, distritos) for c in CODIGOS}
