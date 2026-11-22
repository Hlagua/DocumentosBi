# Proyecto final — Inteligencia de Negocios

Sistemas predictivos **multiclase** con redes neuronales sobre el Data Mart Kimball `DM_Financial_Kimball_v2` (banco `Financial_ijs`), con un aplicativo donde se **escriben datos nuevos** y un dashboard de la red.

## Estado

| Fase | Contenido | Estado |
| :--- | :--- | :--- |
| 1 | Datasets multiclase limpios, partición 60/20/20 y Hoeffding | ✅ `01_generar_datasets.py` |
| 2 | Redes neuronales (Keras) y comparación con modelos base | ✅ `02_entrenar_redes.py` |
| 3 | Aplicativo con formulario (sin combos) y registro de predicciones | ✅ `app/` |
| 4 | Dashboard de la red neuronal | ✅ `app/dashboard.py`, páginas `/red/S#` y `/resumen` |
| 5 | Pruebas con datos escritos a mano, informe y defensa | ⏳ |

## Los tres sistemas

| Sistema | Pregunta de negocio | Clases | Filas | X |
| :--- | :--- | :---: | ---: | :---: |
| S1 | ¿Qué tipo de movimiento es una transacción nueva? | 4 (depósito, retiro, transferencia enviada, transferencia recibida) | 24,000 | 12 |
| S2 | ¿Para qué es una orden de pago permanente nueva? | 4 (hogar, préstamo, seguro, arrendamiento) | 5,092 | 13 |
| S3 | ¿Cómo estará el saldo de la cuenta el próximo mes? | 3 (estable, caída, sobregiro) | 4,708 | 15 |
| S4 | ¿Un préstamo nuevo terminará en impago? | 2 (paga sin problemas, impago) | 682 | 16 |

- La etiqueta de cada fila es la **verdadera** (operación, propósito de la orden o saldo real del mes siguiente).
- Las X son datos que se pueden **escribir** en el formulario. El distrito se escribe por su nombre y el aplicativo lo traduce a sus 4 indicadores con `datos/distritos.csv`.
- La columna `particion` fija qué filas son de entrenamiento, validación y prueba (semilla 42).

## Redes neuronales (fase 2)

Cada red se eligió en validación. La búsqueda probó todas las X frente a PCA al 95 % y 5 arquitecturas. Todas usan Keras, salida softmax, entropía cruzada, Adam, lotes de 15, parada temprana y pesos por clase. Resultados en **prueba** (evaluada una sola vez):

| Sistema | Arquitectura elegida | Parámetros | Red | Softmax lineal | Clase mayoritaria | Aleatorio | E_in | E_out | Error CV-5 |
| :--- | :--- | ---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| S1 | 12 → 128 → 64 → 32 → 4, ReLU | 12,132 | **76.8 %** | 58.3 % | 25.0 % | 25.0 % | 20.4 % | 23.2 % | 22.7 % ± 0.3 |
| S2 | 13 → 64 → 32 → 4, tanh | 3,108 | **81.4 %** (bal. 83.3 %) | 73.6 % | 68.7 % | 25.0 % | 16.1 % | 18.6 % | 18.4 % ± 1.9 |
| S3 | 15 → 64 → 32 → 3, tanh | 3,203 | **63.6 %** (bal. 68.5 %) | 58.3 % | 42.5 % | 33.3 % | 35.7 % | 36.5 % | 37.3 % ± 1.3 |
| S4 | 16 → PCA 10 → 128 → 64 → 32 → 2, ReLU | 11,810 | **79.4 %** (bal. 68.0 %, AUC 0.795) | 80.9 % (bal. 77.6 %) | 89.0 % (bal. 50 %) | 50.0 % | 17.3 % | 20.6 % | 16.1 % ± 0.5 |

**S4 (préstamos):**
- Es el sistema binario permitido. Usa solo datos que el banco conoce al aprobar: monto, plazo, la cuota calculada y el historial de la cuenta antes del préstamo.
- Es el único sistema donde **PCA ganó** en validación: hay pocos datos (682) para 16 características.
- En prueba solo hay 15 impagos (ε = ±11.7 %). Ahí el softmax lineal queda por encima de la red, así que se debe presentar con esa cautela.
- La red detecta 8 de 15 impagos. La clase mayoritaria tiene 89 % de exactitud pero no detecta ninguno.
- El aplicativo calcula además el **monto máximo sugerido**: el mayor monto, con el mismo perfil y plazo, cuya probabilidad de impago es menor que 50 %. El riesgo crece con el monto, por eso el resultado tiene sentido.

- En los tres sistemas la red supera al softmax lineal, y E_out − E_in queda por debajo de 5 puntos: no hay sobreajuste.
- **PCA no ayudó** en ninguno: perdió entre 2 y 11 puntos en validación. Por eso se usan todas las características, que además son pocas (12 a 15).
- Los modelos, el preprocesamiento (orden de X, medias, desviaciones) y las métricas completas (curvas, matriz de confusión, métricas por clase y búsqueda) están en `modelos/`.
- **Tiempo:** S1 tardó unas 21 horas (14,400 filas, lotes de 15 y 10 configuraciones más 5 pliegues). S2 tardó 26 minutos y S3, 7. Para volver a entrenar un solo sistema: `python proyecto_final/02_entrenar_redes.py S2`.

## Balanceo de clases: dos versiones (en evaluación)

S2, S3 y S4 tienen clases desbalanceadas reales; S1 ya está balanceado (6,000 por clase). Hay dos versiones entrenadas con la misma partición:

| Carpeta | Estrategia | Uso actual |
| :--- | :--- | :--- |
| `modelos/` | Datos reales y **pesos por clase** en la pérdida | El aplicativo la usa solo para S1, que ya estaba balanceado |
| `modelos_sobremuestreo/` | Entrenamiento **50/50**: se repiten casos de las clases pequeñas solo en entrenamiento; validación y prueba quedan con la proporción real | **La usa el aplicativo en S2, S3 y S4** (decisión del 2026-11-22) |

La versión de cada sistema se cambia en `VERSION_POR_SISTEMA`, en `app/nucleo.py`.

La comparación completa está en [`comparacion_balanceo.md`](comparacion_balanceo.md) (`python proyecto_final/03_comparar_balanceo.py`). En resumen:
- El sobremuestreo mejora un poco a S2 y claramente a S4 (AUC 0.795 → 0.856; detecta 9 de 15 impagos en vez de 8).
- S3 queda prácticamente igual.
- En S3 y S4, E_out − E_in sube a 5.2 puntos, justo por encima del límite de 5.

Para reentrenar con sobremuestreo: `python proyecto_final/02_entrenar_redes.py S2 S3 S4 --balanceo sobremuestreo --salida modelos_sobremuestreo`.

## Verificación de los modelos

`python proyecto_final/04_verificar_modelos.py` (~40 s) genera [`verificacion_modelos.md`](verificacion_modelos.md). Prueba las dos versiones con:
- (A) datos parecidos al dataset, con ruido del 5 %;
- (B) datos reales que el modelo nunca vio: 10,000 transacciones en S1 y 5,000 meses en S3;
- (C) casos en la frontera de decisión;
- (D) atajos: importancia por permutación y valores sintéticos extremos.

## Cómo ejecutar

Desde la raíz del repositorio:

```bash
python proyecto_final/01_generar_datasets.py
```

Luego `python proyecto_final/02_entrenar_redes.py`, que requiere `tensorflow` (probado con TF 2.21 y Keras 3.15).

**Aplicativo:** `python proyecto_final/app/app.py` y abrir http://127.0.0.1:5000.
- Cada sistema tiene un formulario **solo con cajas de texto**, sin listas desplegables ni autocompletado.
- El distrito se escribe por su nombre y se reconoce sin tildes ni mayúsculas.
- Se valida cada dato y se comprueba que el vector X tenga la dimensión del modelo. Se avisa si un valor está fuera del rango visto al entrenar.
- Se muestran la clase, las probabilidades softmax y el vector que entra a la red.
- **Frontera de decisión:** si las dos clases más probables difieren en menos de 10 puntos, aparece el aviso "Caso en la frontera de decisión entre X e Y". La red igual asigna una sola clase, la de mayor probabilidad (argmax de softmax). El historial y el dashboard marcan esos casos con la etiqueta *frontera*.
- Cada predicción se guarda en `app/predicciones.sqlite` (no se sube a git) y, si SQL Server está disponible, en `DM_Financial_Kimball_v2.dbo.Prediccion_Red_Neuronal`.
- Verificación: 40 filas de prueba de cada sistema escritas como texto dieron la misma predicción que el modelo directo (40/40 en los 4).

**Dashboard de la red** (`/red/S1` … `/red/S4`). Los gráficos se dibujan con matplotlib en el servidor, así que funcionan **sin internet**, y siguen las reglas de visualización del docente. Cada página muestra:
1. Datos: hecho del Data Mart de origen, clases por partición y cálculo de Hoeffding.
2. Arquitectura: diagrama de la red y tabla de capas con la forma de W, b y los parámetros.
3. Selección del modelo: las 10 configuraciones probadas, con y sin PCA.
4. Curvas de pérdida y exactitud por época.
5. Evaluación: matriz de confusión, precisión, sensibilidad y F1 por clase, comparación con softmax lineal, clase mayoritaria y aleatorio, y los 5 pliegues con ±1σ.
6. Mapa 2D con los datos nuevos escritos en el aplicativo (★) y su historial.

`/resumen` presenta la cadena completa del semestre (de la fuente OLTP a las redes) y compara los 4 sistemas.

El primer script genera en `proyecto_final/datos/`: los 3 CSV, `distritos.csv`, `diccionario_caracteristicas.json` (campos del formulario y orden de X) y `resumen_datasets.json` (limpieza, clases, partición y Hoeffding).
