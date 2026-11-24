"""
==============================================================================
UNIVERSIDAD TÉCNICA DE AMBATO - Inteligencia de Negocios (Proyecto final)
AUTORES: Alison Marcela Cobos Taco / Henry Daniel Lagua Flores
==============================================================================
ARCHIVO: proyecto_final/03_comparar_balanceo.py

Compara las dos formas de tratar el desbalance de clases en S2 y S4:
  * modelos/                 -> pesos por clase en la pérdida (datos reales)
  * modelos_sobremuestreo/   -> entrenamiento 50/50 por sobremuestreo
Ambas versiones se evalúan sobre la MISMA partición de prueba (proporción real).

Genera `comparacion_balanceo.md` con las métricas lado a lado.
==============================================================================
"""

import json
import sys
from pathlib import Path

DIR = Path(__file__).resolve().parent
VERSIONES = {"Pesos por clase": DIR / "modelos", "Sobremuestreo 50/50": DIR / "modelos_sobremuestreo"}


def cargar(carpeta, s):
    with open(carpeta / f"{s}_metricas.json", encoding="utf-8") as f:
        return json.load(f)


def pct(v):
    return f"{v * 100:.1f} %"


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    lineas = [
        "# Comparación: pesos por clase frente a sobremuestreo 50/50",
        "",
        "Las dos versiones usan los mismos datos, la misma partición 60/20/20 y la misma búsqueda de arquitectura. "
        "Cambia solo cómo se trata el desbalance **en el entrenamiento**; validación y prueba conservan la proporción real.",
        "",
    ]
    for s in ["S2", "S4"]:
        m = {v: cargar(c, s) for v, c in VERSIONES.items()}
        ref = next(iter(m.values()))
        lineas += [f"## {s} · {ref['titulo']}", ""]
        filas = [
            ("Entrenamiento por clase", lambda x: " / ".join(str(v) for v in
                                                              (x.get("balanceo", {}).get("entrenamiento_usado_por_clase")
                                                               or x["balanceo"]["entrenamiento_original_por_clase"]).values())
             if "balanceo" in x else "datos reales"),
            ("Arquitectura elegida", lambda x: f"{'PCA → ' if x['elegida']['pca'] else ''}"
                                               f"{'-'.join(map(str, x['elegida']['ocultas']))} {x['elegida']['activacion']}"),
            ("Exactitud (prueba)", lambda x: pct(x["prueba"]["exactitud"])),
            ("Exactitud balanceada (prueba)", lambda x: pct(x["prueba"]["exactitud_balanceada"])),
            ("F1 macro (prueba)", lambda x: f"{x['prueba']['f1_macro']:.3f}"),
        ]
        if "auc" in ref["prueba"]:
            filas.append(("AUC (prueba)", lambda x: f"{x['prueba']['auc']:.3f}"))
        filas += [
            ("E_in (entrenamiento real)", lambda x: pct(x["E_in"])),
            ("E_out (prueba)", lambda x: pct(x["E_out"])),
            ("E_out − E_in (límite 5 puntos)", lambda x: f"{x['diferencia_E_out_E_in'] * 100:+.1f}"
                                                         + (" ⚠" if x["diferencia_E_out_E_in"] > 0.05 else " ✅")),
            ("Error CV-5 (promedio ± σ)", lambda x: f"{x['validacion_cruzada_5']['error_promedio'] * 100:.1f} ± "
                                                    f"{x['validacion_cruzada_5']['desviacion'] * 100:.1f} %"),
            ("Softmax lineal, exactitud balanceada", lambda x: pct(x["comparacion_prueba"]["softmax_lineal"]["exactitud_balanceada"])),
            ("Épocas (mejor época)", lambda x: f"{len(x['historial']['loss'])} "
                                               f"({x['historial']['val_loss'].index(min(x['historial']['val_loss'])) + 1})"),
            ("Tiempo total del proceso", lambda x: f"{x['segundos'] / 60:.1f} min"),
        ]
        cab = "| Métrica | " + " | ".join(VERSIONES) + " |"
        lineas += [cab, "| :--- | " + " | ".join(":---:" for _ in VERSIONES) + " |"]
        for nombre, f in filas:
            lineas.append(f"| {nombre} | " + " | ".join(f(m[v]) for v in VERSIONES) + " |")
        lineas += ["", "**Sensibilidad por clase (prueba):**", "",
                   "| Clase | " + " | ".join(VERSIONES) + " |",
                   "| :--- | " + " | ".join(":---:" for _ in VERSIONES) + " |"]
        for clase in ref["prueba"]["por_clase"]:
            lineas.append(f"| {clase} | " + " | ".join(pct(m[v]["prueba"]["por_clase"][clase]["sensibilidad"])
                                                     for v in VERSIONES) + " |")
        lineas.append("")
    salida = DIR / "comparacion_balanceo.md"
    salida.write_text("\n".join(lineas), encoding="utf-8")
    print("\n".join(lineas))
    print(f"\nGuardado en {salida.relative_to(DIR.parent)}")


if __name__ == "__main__":
    main()
