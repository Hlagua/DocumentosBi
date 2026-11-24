# Modelos de la Literatura PKDD'99 / Berka con Redes Neuronales

Proyecto paralelo e independiente (no modifica `proyecto_final/` ni el Data Mart) que implementa las **5 tareas clásicas de la literatura sobre la base bancaria checa PKDD'99 / Berka** (`DM_Financial_Kimball_v2` / `dataframes/`) utilizando las tres capas de salida estudiadas en clase: **Sigmoide**, **Softmax** y **Lineal (Regresión)**.

## Los 5 modelos

| Código | Tarea de la literatura | Tipo | Capa de salida / Pérdida | Filas | Variables (X) |
| :---: | :--- | :--- | :--- | ---: | :---: |
| **M1** | Riesgo de impago de préstamos | Clasificación binaria | `sigmoid` / `binary_crossentropy` | 682 | 16 |
| **M2** | Qué tarjeta ofrecer: sin tarjeta, classic o gold | Clasificación multiclase (3) | `softmax` / `sparse_categorical_crossentropy` | 3,988 | 17 |
| **M3** | Segmentación y perfilamiento de clientes (K-Means 4 segmentos) | Clasificación multiclase (4) | `softmax` / `sparse_categorical_crossentropy` | 4,500 | 14 |
| **M4** | Detección de fuga o abandono silencioso (*Churn* H1→H2 1998) | Clasificación binaria | `sigmoid` / `binary_crossentropy` | 4,490 | 15 |
| **M5** | Pronóstico de transacciones (monto mensual del mes siguiente $t+1$) | Regresión continua | `linear` / `mse` | 17,870 | 14 |

## M2 con la tabla `cards` (2026-11-22)

La tabla `cards` (892 tarjetas: 659 classic, 145 junior, 88 gold) se extrae con `python scripts/49_extraer_tarjetas.py` a `dataframes/df_tarjetas.csv`, junto con `df_disposiciones.csv`.

- **Antes**, M2 era binaria y su etiqueta era "ya hizo un retiro con tarjeta", con datos de toda la historia. Eso mide uso de la tarjeta, no a quién ofrecerla, y por eso daba 79.4 % balanceada.
- **Ahora** responde "¿qué tarjeta ofrecer?" con tres clases: sin tarjeta (3,252), classic (649) y gold (87). Solo entran titulares de 21 años o más, porque la junior se emite únicamente a menores de 21: con ella la red aprendería solo la edad.
- **Resultado en prueba (799 cuentas):** exactitud 75.5 %, balanceada 65.2 %. El softmax lineal llega a 70.3 % balanceada, así que la red **no lo supera**. Responder siempre "sin tarjeta" da 81.5 % de exactitud, pero 33.3 % balanceada.
- **Por clase:** detecta 82 % de las classic y 7 de las 18 gold de prueba. Con 18 casos, el resultado de gold tiene un margen muy amplio.
- E_out − E_in = 3.8 puntos; validación cruzada 24.4 % ± 1.1 de error.
- Lo que más pesa es el saldo (promedio, máximo y final) y el ingreso mensual. El año de la fecha de referencia no agrega nada (un bosque aleatorio da lo mismo con y sin él), así que la fecha no delata la clase.

## Funciones de activación de las capas ocultas (2026-11-23)

Por indicación del docente, las capas ocultas **no usan ReLU**. La búsqueda en validación elige entre **tangente hiperbólica** (`tanh`, centrada en cero: tanh(z) = 2·σ(2z) − 1) con 32, 64-32 y 128-64-32 neuronas, y una red 64-32 con **sigmoide logística**. La capa de salida no cambia (sigmoide, softmax o lineal según la tarea).

| Código | Elegida | Prueba | Modelo lineal | Antes, con ReLU |
| :---: | :--- | :--- | :--- | :--- |
| M1 | 64-32 sigmoide | AUC 0.858 · bal. 76.3 % · E_out − E_in 1.6 | AUC 0.865 · bal. 83.0 % | AUC 0.867 · bal. 74.2 % · 6.2 |
| M2 | 128-64-32 tanh | 75.5 % · bal. 65.2 % · 3.8 | bal. 70.3 % | 74.5 % · bal. 67.6 % · 5.9 |
| M3 | 64-32 sigmoide | 98.9 % · bal. 99.1 % · 0.5 | 98.2 % | 98.8 % (ya era tanh) |
| M4 | 32 tanh | AUC 0.763 · bal. 69.5 % · 7.0 | AUC 0.747 · bal. 70.5 % | AUC 0.817 · bal. 72.0 % · 6.3 |
| M5 | 64-32 tanh | R² 0.512 | — | R² 0.512 (ya era tanh) |

- Los cambios son pequeños, salvo M4, que pierde unos 5 puntos de AUC. En M1, M2 y M4 la red **no supera claramente** al modelo lineal; hay que decirlo en la defensa.
- La sigmoide ganó en M1 y M3: con 2 capas ocultas no aparece el desvanecimiento del gradiente que sí afecta a redes profundas.

## Control anti-fuga de datos (*Data Leakage*)
- **M1:** solo transacciones con `fecha < fecha_otorgamiento` (0 fuga temporal).
- **M2:** solo movimientos **anteriores a la emisión** de la tarjeta. Las cuentas sin tarjeta usan una fecha de referencia sorteada con la misma antigüedad que las cuentas que sí la recibieron. Los 8,036 retiros con tarjeta (`VYBER KARTOU`) son todos posteriores a la emisión, así que no entra ninguno.
- **M3:** partición agrupada por cuenta; K-Means ajustado **solo** en entrenamiento.
- **M4:** variables `X` estrictamente del primer semestre de 1998 (H1) y etiqueta futura `y` del segundo semestre de 1998 (H2), excluyendo intereses automáticos (`UROK`).
- **M5:** partición agrupada por cuenta (0 cuentas compartidas entre entrenamiento, validación y prueba); z-score y escalado de `y` ajustados solo en entrenamiento.

## Cómo ejecutar

### Abrir el aplicativo web (puerto 5001)
Doble clic en `modelos_literatura_berka\iniciar_app.bat` (reutiliza el entorno virtual de `proyecto_final\.venv` si ya existe) o desde la raíz de `DocumentosBi`:

```bash
proyecto_final\.venv\Scripts\python modelos_literatura_berka\app\app.py
```

Abrir en el navegador: **http://127.0.0.1:5001**

### Regenerar datasets, modelos o Playground
```bash
proyecto_final\.venv\Scripts\python modelos_literatura_berka\01_generar_datasets.py
proyecto_final\.venv\Scripts\python modelos_literatura_berka\02_entrenar_modelos.py
proyecto_final\.venv\Scripts\python modelos_literatura_berka\03_grabar_entrenamiento.py
```

El **Playground interactivo época por época** está disponible en **http://127.0.0.1:5001/playground/M1** (y `M2`…`M5`), soportando salidas `sigmoid`, `softmax` y superficie continua `linear` (regresión).
