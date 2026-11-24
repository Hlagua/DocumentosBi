# Proyecto final — Inteligencia de Negocios

Sistemas predictivos **multiclase** con redes neuronales sobre el Data Mart Kimball `DM_Financial_Kimball_v2` (banco `Financial_ijs`), con un aplicativo donde se **escriben datos nuevos** y un dashboard de la red.

## Estado

| Fase | Contenido | Estado |
| :--- | :--- | :--- |
| 1 | Datasets multiclase limpios, partición 60/20/20 y Hoeffding | ✅ `01_generar_datasets.py` |
| 2 | Redes neuronales (Keras) y comparación con modelos base | ✅ `02_entrenar_redes.py` |
| 3 | Aplicativo con formulario (sin combos) y registro de predicciones | ✅ `app/` |
| 4 | Dashboard de la red neuronal | ✅ `app/dashboard.py`, página `/red/S#` |
| 5 | Pruebas con datos escritos a mano, informe y defensa | ⏳ |

## Los sistemas (uno por cada data mart)

| Sistema | Pregunta de negocio | Clases | Filas | X |
| :--- | :--- | :---: | ---: | :---: |
| S1 | ¿Qué tipo de movimiento es una transacción nueva? | 4 (depósito, retiro, transferencia enviada, transferencia recibida) | 24,000 | 12 |
| S2 | ¿Para qué es una orden de pago permanente nueva? | 4 (hogar, préstamo, seguro, arrendamiento) | 5,092 | 13 |
| S4 | ¿Un préstamo estaría en mora al corte del 31/12/1998? | 2 (al día al corte, en mora o impago al corte) | 682 | 16 |

Data mart de origen: S1 Transacciones, S2 Órdenes y S4 Préstamos. S1 y S2 son multiclase con softmax; S4 es el binario permitido (también con softmax de 2 neuronas). Los códigos se mantienen: S3 y S5 se entrenaron y se descartaron (ver más abajo).

- La etiqueta de cada fila es la **verdadera** (operación, propósito de la orden, estado del préstamo al corte o movimiento real del mes siguiente).
- Las X son datos que se pueden **escribir** en el formulario. El distrito se escribe por su nombre y el aplicativo lo traduce a sus 4 indicadores con `datos/distritos.csv`.
- La columna `particion` fija qué filas son de entrenamiento, validación y prueba (60/20/20, semilla 42).
- **En S1 y S2 la partición es por cuenta:** todas las filas de una cuenta quedan en un solo lado, y la validación cruzada también agrupa por cuenta. Así la prueba responde "¿y si es un cliente nuevo?". En S4 cada fila ya es una cuenta distinta.
- **S4 se llama "mora al corte":** los 403 préstamos vigentes al día (estado C) siguen abiertos y podrían caer en mora después de 1998, así que la etiqueta no es "pagará o no pagará".

## Redes neuronales (fase 2)

Cada red se eligió en validación. La búsqueda probó todas las X frente a PCA al 95 % y 5 arquitecturas. **Por indicación del docente, las capas ocultas no usan ReLU:** se elige entre tangente hiperbólica (32, 64-32 con y sin L1, 128-64-32) y una red 64-32 con sigmoide logística. Todas usan Keras, salida softmax, entropía cruzada, Adam, lotes de 15 y parada temprana. Resultados en **prueba** (evaluada una sola vez) **de la versión que usa el aplicativo**, con partición por cuenta:

| Sistema | Versión | Arquitectura elegida | Parámetros | Red | Softmax lineal | Clase mayoritaria | Aleatorio | E_in | E_out | Error CV-5 |
| :--- | :--- | :--- | ---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| S1 | dataset balanceado | 12 → 64 → 32 → 4, sigmoide | 3,044 | **76.9 %** | 58.4 % | 25.0 % | 25.0 % | 22.5 % | 23.1 % | 23.9 % ± 0.9 |
| S2 | sobremuestreo 50/50 | 13 → 64 → 32 → 4, sigmoide | 3,108 | **82.2 %** (bal. 85.4 %) | 75.0 % (bal. 78.5 %) | 68.8 % | 25.0 % | 16.1 % | 17.8 % | 18.7 % ± 0.8 |
| S4 | pesos por clase | PCA 16 → 10, 10 → 64 → 32 → 2, tanh | 2,850 | **83.1 %** (bal. **81.7 %**, AUC 0.829) | 80.9 % (bal. 77.6 %) | 89.0 % (bal. 50 %) | 50.0 % | 16.1 % | 16.9 % | 17.8 % ± 3.8 |

**Partición por cuenta: qué cambió.** Antes, en S1 el 94 % de la prueba eran cuentas ya vistas al entrenar (S2 33 %). Ahora ninguna cuenta está en dos particiones. Las cifras de antes y de ahora no se comparan para sacar conclusiones, porque cambiaron a la vez la red (S1 era 128 → 64 → 32 y ahora es 64 → 32) y las filas de prueba. Lo que sí se afirma es el resultado actual: en S1, la red acierta 76.9 % en 857 cuentas que no vio al entrenar.

**Lo que hay que decir en la defensa:**
- **S1:** la red supera al lineal por 18 puntos en 857 cuentas que no vio al entrenar (76.9 %). Las 10,000 transacciones "nunca vistas" (76.2 % balanceada) **no son otro grupo de clientes**: salen de 1,057 cuentas, de las cuales 857 son las mismas de la prueba. Sirven para confirmar, con otros movimientos de esos clientes, que la prueba se sostiene; no para decir que hay otra población donde también da 76 %.
- **S2:** la orden de préstamo suele tener monto = cuota. La regla de una línea "si el monto coincide con la cuota, es préstamo; si no, es hogar" acierta **81.6 %**, casi lo mismo que la red, pero su exactitud **balanceada es 47.7 %**: nunca reconoce seguro ni arrendamiento. La red llega a 85.4 % balanceada. Hay que mostrar esa regla al lado de la red.
- **S4:** es el binario permitido, con "mora al corte". Con tanh y pesos por clase la red llega a **81.7 % balanceada** frente a 77.6 % de la regresión logística, y E_out − E_in = 0.8 puntos. Con 15 casos de mora en prueba (ε = ±11.7 %) esa ventaja cabe en el ruido, así que la red se presenta como el sistema pedido, no como una mejora demostrada. Con ReLU y sobremuestreo la logística ganaba (78.0 % frente a 73.8 %).
- El aplicativo calcula además el **monto máximo sugerido** en S4: el mayor monto, con el mismo perfil y plazo, cuya probabilidad de mora es menor que 50 %. El riesgo crece con el monto.
- **PCA** ganó en S4 (pocos datos para 16 características: 10 componentes). S1 y S2 usan todas las X.
- Los modelos, el preprocesamiento y las métricas completas están en `modelos/` y `modelos_sobremuestreo/`. Reentrenar todo toma entre 30 minutos y más de 2 horas según el equipo y si está conectado a la corriente (S1 es el más largo). Los sistemas se pueden entrenar en paralelo, uno por proceso: cada uno fija su semilla y da el mismo resultado.

## Sistemas descartados: S3 y S5

**S3 (2026-11-23).** "¿Cómo estará el saldo de la cuenta el próximo mes?" (estable, caída o sobregiro) se entrenó y verificó, pero **no se presenta**:
- Con la proporción real de meses del banco (87,170 meses de cuentas nuevas, sobregiro ~0.4 %) acertaba 57.9 %, **por debajo del 60.7 % de responder siempre "estable"**.
- Frente al softmax lineal ganaba solo 3 puntos (67.5 % frente a 64.5 % balanceada).
- Su 87 % de sobregiros detectados salía de los mismos 142 casos de la prueba: no había sobregiros aparte para medirlo.

**S5 (2026-11-24).** "¿El dinero que mueve la cuenta bajará más de 20 %, se mantendrá o subirá más de 20 % el próximo mes?" (3 clases, 9,000 meses) tampoco se presenta:
- La red acertaba **61.6 %** en prueba (softmax lineal 48.3 %) y 63.8 % con la proporción real de meses, frente a 44.8 % de responder siempre "estable".
- E_out − E_in = 6.2 puntos, sobre el límite de 5.
- Para acercarlo a 70 % hacía falta agregar el historial de los últimos 6 meses de la cuenta y duplicar los datos (un Gradient Boosting de prueba llegó a ~70 % balanceada con eso), y no hubo tiempo de reentrenarlo.

Por eso el data mart Saldo mensual queda sin sistema presentado. Los archivos de S3 y S5 (datasets, modelos y playground) quedan en el repositorio como respaldo; el aplicativo y la verificación ya no los usan. Para volver a mostrar uno basta con agregarlo a `SISTEMAS` en `app/nucleo.py` y a `ARCHIVOS` en `04_verificar_modelos.py`.

## Balanceo de clases: dos versiones (en evaluación)

S2 y S4 tienen clases desbalanceadas reales; S1 (6,000 por clase) ya está balanceado y tiene una sola versión. Hay dos versiones entrenadas con la misma partición:

| Carpeta | Estrategia | Uso actual |
| :--- | :--- | :--- |
| `modelos/` | Datos reales y **pesos por clase** en la pérdida | El aplicativo la usa en S1 (ya balanceado) y en **S4** (desde el 2026-11-23) |
| `modelos_sobremuestreo/` | Entrenamiento **50/50**: se repiten casos de las clases pequeñas solo en entrenamiento; validación y prueba quedan con la proporción real | **La usa el aplicativo en S2** (decisión del 2026-11-22) |

La versión de cada sistema se cambia en `VERSION_POR_SISTEMA`, en `app/nucleo.py`.

La comparación completa está en [`comparacion_balanceo.md`](comparacion_balanceo.md) (`python proyecto_final/03_comparar_balanceo.py`). En resumen:
- En S2 las dos versiones quedan iguales (balanceada 85.3 % con pesos y 85.4 % con sobremuestreo).
- En S4, con tanh, **los pesos por clase ganan**: balanceada 81.7 % frente a 68.4 %, AUC 0.829 frente a 0.798, y E_out − E_in 0.8 frente a 11.1 puntos (el sobremuestreo memoriza los 46 casos de mora repetidos). Por eso el aplicativo pasó S4 a `modelos/`.

Para reentrenar con sobremuestreo: `python proyecto_final/02_entrenar_redes.py S2 S4 --balanceo sobremuestreo --salida modelos_sobremuestreo`.

## Verificación de los modelos

`python proyecto_final/04_verificar_modelos.py` (~40 s) genera [`verificacion_modelos.md`](verificacion_modelos.md). Prueba las dos versiones con:
- (A) datos parecidos al dataset, con ruido del 5 %;
- (B) datos reales que el modelo nunca vio, **solo de cuentas que no se usaron para entrenar ni validar**: 10,000 transacciones en S1. Estas cuentas incluyen las de la prueba (en S1, 857 de 1,057), así que B confirma la prueba; no mide otra población;
- (E) S2 frente a la regla de una línea "monto = cuota → préstamo";
- (C) casos en la frontera de decisión;
- (D) atajos: importancia por permutación y valores sintéticos extremos.

## Cómo correrlo en otro computador (después de `git pull`)

**Requisito:** Python **3.12** de [python.org](https://www.python.org/downloads/), con la casilla "Add python.exe to PATH" marcada al instalar. No hace falta SQL Server ni MongoDB: los datasets y las redes entrenadas ya vienen en el repositorio.

**Opción fácil (Windows):**
1. `git pull` en la carpeta del repositorio.
2. Doble clic en `proyecto_final\iniciar_app.bat`.
   - La primera vez crea un entorno virtual en `proyecto_final\.venv` (no se sube a git) e instala las librerías de `requirements.txt`. Tarda varios minutos, porque TensorFlow pesa unos 500 MB.
   - Las siguientes veces abre el aplicativo directamente.
3. El navegador se abre solo en **http://127.0.0.1:5000** (si no carga a la primera, actualice la página). Para cerrarlo, presione `Ctrl + C` en la ventana negra.

**Opción manual (desde la raíz del repositorio):**
```
py -3.12 -m venv proyecto_final\.venv
proyecto_final\.venv\Scripts\python -m pip install -r proyecto_final\requirements.txt
proyecto_final\.venv\Scripts\python proyecto_final\app\app.py
```

**Para verificar el sistema** (unos 45 s): `proyecto_final\.venv\Scripts\python proyecto_final\04_verificar_modelos.py`. Regenera `verificacion_modelos.md`.

**Notas:**
- No abra los archivos de `app/templates/` con doble clic: son plantillas y solo se ven bien a través del servidor.
- Las predicciones se guardan en `app/predicciones.sqlite` de cada computador. Si ese equipo tiene la base `DM_Financial_Kimball_v2` en LocalDB, se guardan también ahí.
- Volver a entrenar las redes no es necesario. Si se hace, S1 es el más largo (de 25 minutos a más de 2 horas, según el equipo).

## Validación de los campos del formulario

Cada caja de texto acepta solo su tipo de dato mientras se escribe, y el servidor vuelve a validar todo:

| Tipo | Qué deja escribir | Ejemplo |
| :--- | :--- | :--- |
| Número | Dígitos y un punto o coma decimal. El signo "-" solo en saldos y en el cambio de saldo | `1250.50`, `-300,75` |
| Entero | Solo dígitos, con rangos lógicos (edad de 10 a 110, plazo de 1 a 360 meses) | `35` |
| Fecha | AAAA-MM-DD; los guiones se ponen solos y la fecha debe existir | `1997-05-14` |
| Mes | AAAA-MM, con mes de 01 a 12 | `1997-05` |
| Sexo | M o F | `F` |
| Sí/No | si o no | `si` |
| Distrito | Letras, espacios, puntos y guiones; se reconoce sin tildes ni mayúsculas | `pisek` |

Si falta un dato o está incompleto, el formulario no se envía y marca el campo.

## Cómo ejecutar

Desde la raíz del repositorio:

```bash
python proyecto_final/01_generar_datasets.py
```

Luego `python proyecto_final/02_entrenar_redes.py`, que requiere `tensorflow` (probado con TF 2.21 y Keras 3.15).

**Aplicativo:** `python proyecto_final/app/app.py` y abrir http://127.0.0.1:5000. La dirección raíz abre el dashboard de S1 (`/red/S1`); no hay página de inicio ni de resumen. Cada página del dashboard y del formulario trae los botones S1, S2 y S4 para cambiar de sistema.
- Cada sistema tiene un formulario **solo con cajas de texto**, sin listas desplegables. La caja del distrito, que sigue siendo de texto, sugiere desde la primera letra los distritos que empiezan con lo escrito (clic, o flechas y Enter). El formulario se abre en una **ventana modal** al entrar a `/predecir/S1`, `/predecir/S2` y `/predecir/S4`; se cierra con Cancelar, la × o Esc y se vuelve a abrir con el botón «Ingresar datos». Si falta un dato o hay un error, el modal se abre de nuevo con los campos marcados.
- El distrito se escribe por su nombre y se reconoce sin tildes ni mayúsculas.
- Se valida cada dato y se comprueba que el vector X tenga la dimensión del modelo. Se avisa si un valor está fuera del rango visto al entrenar.
- Se muestran la clase, las probabilidades softmax y el vector que entra a la red.
- **Frontera de decisión:** si las dos clases más probables difieren en menos de 10 puntos, aparece el aviso "Caso en la frontera de decisión entre X e Y". La red igual asigna una sola clase, la de mayor probabilidad (argmax de softmax). El historial y el dashboard marcan esos casos con la etiqueta *frontera*.
- Cada predicción se guarda en `app/predicciones.sqlite` (no se sube a git) y, si SQL Server está disponible, en `DM_Financial_Kimball_v2.dbo.Prediccion_Red_Neuronal`.
- Verificación: 40 filas de prueba de cada sistema escritas como texto dieron la misma predicción que el modelo directo (40/40 en los 4).

**Dashboard de la red** (`/red/S1`, `/red/S2` y `/red/S4`). Los gráficos se dibujan con matplotlib en el servidor, así que funcionan **sin internet**, y siguen las reglas de visualización del docente. Cada página muestra:
1. Datos: hecho del Data Mart de origen, clases por partición y cálculo de Hoeffding.
2. Arquitectura: diagrama de la red y tabla de capas con la forma de W, b y los parámetros.
3. Selección del modelo: las 10 configuraciones probadas, con y sin PCA.
4. Curvas de pérdida y exactitud por época.
5. Evaluación: matriz de confusión, precisión, sensibilidad y F1 por clase, comparación con softmax lineal, clase mayoritaria y aleatorio, y los 5 pliegues con ±1σ.
6. Mapa 2D con los datos nuevos escritos en el aplicativo (★) y su historial.

## Playground (entrenamiento época por época)

Las rutas `/playground/S1`, `/playground/S2` y `/playground/S4` muestran una reproducción interactiva del entrenamiento real de cada red (al estilo de TensorFlow Playground), abriendo por defecto en la mejor época (★):
- **Controles:** botón reproducir/pausar (▶), reinicio a época 0 y deslizador de épocas.
- **Visualización:** mapas de calor de entradas y neuronas ocultas sobre el plano PCA 2D, aristas SVG con los pesos reales (azul positivo, naranja negativo, grosor proporcional a |w|), frontera de decisión con casillas para datos de entrenamiento, datos de prueba y errores de prueba, y curvas de pérdida/exactitud.
- **Datos grabados:** se almacenan en `proyecto_final/playground/S#_entrenamiento.json` (1.6 a 3.8 MB cada uno) y reproducen exactamente la exactitud en prueba del aplicativo.
- **Cómo regenerarlo** (tarda alrededor de 2 minutos en total para los sistemas, o se puede indicar uno solo):
  ```bash
  python proyecto_final/05_grabar_entrenamiento.py
  ```

El primer script genera en `proyecto_final/datos/` (todos, o solo los sistemas que se indiquen, por ejemplo `S5`): los 5 CSV, `distritos.csv`, `diccionario_caracteristicas.json` (campos del formulario y orden de X) y `resumen_datasets.json` (limpieza, clases, partición y Hoeffding).
