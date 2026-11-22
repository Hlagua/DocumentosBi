# Modelos de la Literatura PKDD'99 / Berka con Redes Neuronales

Proyecto paralelo e independiente (no modifica `proyecto_final/` ni el Data Mart) que implementa las **5 tareas clásicas de la literatura sobre la base bancaria checa PKDD'99 / Berka** (`DM_Financial_Kimball_v2` / `dataframes/`) utilizando las tres capas de salida estudiadas en clase: **Sigmoide**, **Softmax** y **Lineal (Regresión)**.

## Los 5 modelos

| Código | Tarea de la literatura | Tipo | Capa de salida / Pérdida | Filas | Variables (X) |
| :---: | :--- | :--- | :--- | ---: | :---: |
| **M1** | Riesgo de impago de préstamos | Clasificación binaria | `sigmoid` / `binary_crossentropy` | 682 | 16 |
| **M2** | Propensión / recomendación de tarjeta de crédito | Clasificación binaria | `sigmoid` / `binary_crossentropy` | 4,500 | 15 |
| **M3** | Segmentación y perfilamiento de clientes (K-Means 4 segmentos) | Clasificación multiclase (4) | `softmax` / `sparse_categorical_crossentropy` | 4,500 | 14 |
| **M4** | Detección de fuga o abandono silencioso (*Churn* H1→H2 1998) | Clasificación binaria | `sigmoid` / `binary_crossentropy` | 4,490 | 15 |
| **M5** | Pronóstico de transacciones (monto mensual del mes siguiente $t+1$) | Regresión continua | `linear` / `mse` | 17,870 | 14 |

## Control anti-fuga de datos (*Data Leakage*)
- **M1:** solo transacciones con `fecha < fecha_otorgamiento` (0 fuga temporal).
- **M2:** excluye `operation == 'VYBER KARTOU'` al construir el perfil transaccional.
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
