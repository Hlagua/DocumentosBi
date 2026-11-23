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
| S4 | ¿Un préstamo estaría en mora al corte del 31/12/1998? | 2 (al día al corte, en mora o impago al corte) | 682 | 16 |

- La etiqueta de cada fila es la **verdadera** (operación, propósito de la orden o saldo real del mes siguiente).
- Las X son datos que se pueden **escribir** en el formulario. El distrito se escribe por su nombre y el aplicativo lo traduce a sus 4 indicadores con `datos/distritos.csv`.
- La columna `particion` fija qué filas son de entrenamiento, validación y prueba (60/20/20, semilla 42).
- **En S1, S2 y S3 la partición es por cuenta:** todas las filas de una cuenta quedan en un solo lado, y la validación cruzada también agrupa por cuenta. Así la prueba responde "¿y si es un cliente nuevo?". En S4 cada fila ya es una cuenta distinta.
- **S4 se llama "mora al corte":** los 403 préstamos vigentes al día (estado C) siguen abiertos y podrían caer en mora después de 1998, así que la etiqueta no es "pagará o no pagará".

## Redes neuronales (fase 2)

Cada red se eligió en validación. La búsqueda probó todas las X frente a PCA al 95 % y 5 arquitecturas. Todas usan Keras, salida softmax, entropía cruzada, Adam, lotes de 15 y parada temprana. Resultados en **prueba** (evaluada una sola vez) **de la versión que usa el aplicativo**, con partición por cuenta:

| Sistema | Versión | Arquitectura elegida | Parámetros | Red | Softmax lineal | Clase mayoritaria | Aleatorio | E_in | E_out | Error CV-5 |
| :--- | :--- | :--- | ---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| S1 | dataset balanceado | 12 → 64 → 32 → 4, ReLU | 3,044 | **76.9 %** | 58.4 % | 25.0 % | 25.0 % | 21.4 % | 23.1 % | 24.1 % ± 0.9 |
| S2 | sobremuestreo 50/50 | 13 → 128 → 64 → 32 → 4, ReLU | 12,260 | **81.9 %** (bal. 84.6 %) | 75.0 % (bal. 78.5 %) | 68.8 % | 25.0 % | 15.9 % | 18.1 % | 18.3 % ± 1.1 |
| S3 | sobremuestreo 50/50 | 15 → 64 → 32 → 3, tanh | 3,203 | **62.1 %** (bal. 67.5 %) | 57.2 % (bal. 64.5 %) | 42.5 % | 33.3 % | 32.7 % | 37.9 % | 37.3 % ± 1.2 |
| S4 | sobremuestreo 50/50 | 16 → 128 → 64 → 32 → 2, ReLU | 12,578 | **84.6 %** (bal. 73.8 %, AUC 0.856) | 76.5 % (bal. **78.0 %**) | 89.0 % (bal. 50 %) | 50.0 % | 10.2 % | 15.4 % | 15.6 % ± 2.7 |

**Partición por cuenta: qué cambió.** Antes, en S1 el 94 % de la prueba eran cuentas ya vistas al entrenar (S3 54 %, S2 33 %). Ahora ninguna cuenta está en dos particiones. Las cifras de antes y de ahora no se comparan para sacar conclusiones, porque cambiaron a la vez la red (S1 era 128 → 64 → 32 y ahora es 64 → 32) y las filas de prueba. Lo que sí se afirma es el resultado actual: en S1, la red acierta 76.9 % en 857 cuentas que no vio al entrenar.

**Lo que hay que decir en la defensa:**
- **S1:** la red supera al lineal por 18 puntos en 857 cuentas que no vio al entrenar (76.9 %). Las 10,000 transacciones "nunca vistas" (76.3 % balanceada) **no son otro grupo de clientes**: salen de 1,057 cuentas, de las cuales 857 son las mismas de la prueba. Sirven para confirmar, con otros movimientos de esos clientes, que la prueba se sostiene; no para decir que hay otra población donde también da 76 %.
- **S2:** la orden de préstamo suele tener monto = cuota. La regla de una línea "si el monto coincide con la cuota, es préstamo; si no, es hogar" acierta **81.6 %**, casi lo mismo que la red, pero su exactitud **balanceada es 47.7 %**: nunca reconoce seguro ni arrendamiento. La red llega a 84.6 % balanceada. Hay que mostrar esa regla al lado de la red.
- **S3:** el dataset tiene 2,000 / 2,000 / 708 meses, pero en el banco el sobregiro es ~0.4 % de los meses. Con la **proporción real** (87,170 meses de cuentas nuevas), la red acierta 57.9 %, **por debajo del 60.7 % de responder siempre "estable"**. Esa comparación sí es nueva, porque casi todos esos meses no están en la prueba. El **87 % de sobregiros detectados sale de la prueba oficial**: los 142 sobregiros de la proporción real son exactamente los 142 de la prueba, porque todos los sobregiros del banco ya estaban en el dataset y no quedó ninguno aparte para medir. La exactitud balanceada (68.4 % frente a 33.3 % de "siempre estable") también se apoya en esos 142 casos. Se presenta como **alerta de riesgo**, no como pronóstico del estado de cualquier mes.
- **S4:** es el binario permitido, con "mora al corte". **La regresión logística lo empata o lo supera:** con sobremuestreo, 78.0 % balanceada frente a 73.8 % de la red; con pesos, 77.6 % frente a 68.0 %. Con 15 casos de mora en prueba (ε = ±11.7 %) esas diferencias caben en el ruido. La red se presenta como el sistema pedido, no como una mejora. Además, E_out − E_in = 5.2 puntos, apenas sobre el límite de 5.
- El aplicativo calcula además el **monto máximo sugerido** en S4: el mayor monto, con el mismo perfil y plazo, cuya probabilidad de mora es menor que 50 %. El riesgo crece con el monto.
- **PCA** solo ganó en S4 con pesos por clase (pocos datos para 16 características). En los demás se usan todas las X.
- Los modelos, el preprocesamiento y las métricas completas están en `modelos/` y `modelos_sobremuestreo/`. Reentrenar todo toma entre 20 y 30 minutos (S1 es el más largo, unos 23 minutos).

## Balanceo de clases: dos versiones (en evaluación)

S2, S3 y S4 tienen clases desbalanceadas reales; S1 ya está balanceado (6,000 por clase). Hay dos versiones entrenadas con la misma partición:

| Carpeta | Estrategia | Uso actual |
| :--- | :--- | :--- |
| `modelos/` | Datos reales y **pesos por clase** en la pérdida | El aplicativo la usa solo para S1, que ya estaba balanceado |
| `modelos_sobremuestreo/` | Entrenamiento **50/50**: se repiten casos de las clases pequeñas solo en entrenamiento; validación y prueba quedan con la proporción real | **La usa el aplicativo en S2, S3 y S4** (decisión del 2026-11-22) |

La versión de cada sistema se cambia en `VERSION_POR_SISTEMA`, en `app/nucleo.py`.

La comparación completa está en [`comparacion_balanceo.md`](comparacion_balanceo.md) (`python proyecto_final/03_comparar_balanceo.py`). En resumen:
- El sobremuestreo mejora un poco a S2 (balanceada 84.3 % → 84.6 %) y claramente a S4 (AUC 0.795 → 0.856).
- En S3, con pesos por clase la balanceada es algo mayor (68.4 % frente a 67.5 %) y E_out − E_in queda en 4.0 puntos. Con sobremuestreo, ese valor es 5.2.
- En S4 con sobremuestreo, E_out − E_in = 5.2 puntos, justo por encima del límite de 5.

Para reentrenar con sobremuestreo: `python proyecto_final/02_entrenar_redes.py S2 S3 S4 --balanceo sobremuestreo --salida modelos_sobremuestreo`.

## Verificación de los modelos

`python proyecto_final/04_verificar_modelos.py` (~40 s) genera [`verificacion_modelos.md`](verificacion_modelos.md). Prueba las dos versiones con:
- (A) datos parecidos al dataset, con ruido del 5 %;
- (B) datos reales que el modelo nunca vio, **solo de cuentas que no se usaron para entrenar ni validar**: 10,000 transacciones en S1 y 5,000 meses en S3. Estas cuentas incluyen las de la prueba (en S1, 857 de 1,057), así que B confirma la prueba; no mide otra población;
- (E) S2 frente a la regla de una línea "monto = cuota → préstamo";
- (F) S3 con la proporción real de meses del banco (87,170 meses, sobregiro ~0.4 %). Sus 142 sobregiros son los mismos de la prueba, así que lo nuevo es la exactitud global frente a "siempre estable";
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
- Volver a entrenar las redes no es necesario. Si se hace, S1 tarda unas 21 horas.

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

## Playground (entrenamiento época por época)

Las rutas `/playground/S1` … `/playground/S4` muestran una reproducción interactiva del entrenamiento real de cada red (al estilo de TensorFlow Playground), abriendo por defecto en la mejor época (★):
- **Controles:** botón reproducir/pausar (▶), reinicio a época 0 y deslizador de épocas.
- **Visualización:** mapas de calor de entradas y neuronas ocultas sobre el plano PCA 2D, aristas SVG con los pesos reales (azul positivo, naranja negativo, grosor proporcional a |w|), frontera de decisión con casillas para datos de entrenamiento, datos de prueba y errores de prueba, y curvas de pérdida/exactitud.
- **Datos grabados:** se almacenan en `proyecto_final/playground/S1..S4_entrenamiento.json` (1.2 a 3.2 MB cada uno) y reproducen exactamente la exactitud en prueba del aplicativo.
- **Cómo regenerarlo** (tarda alrededor de 2 minutos en total para los 4 sistemas, o se puede indicar uno solo):
  ```bash
  python proyecto_final/05_grabar_entrenamiento.py
  ```

El primer script genera en `proyecto_final/datos/`: los 3 CSV, `distritos.csv`, `diccionario_caracteristicas.json` (campos del formulario y orden de X) y `resumen_datasets.json` (limpieza, clases, partición y Hoeffding).
