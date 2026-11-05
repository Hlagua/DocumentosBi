# Datasets y Prácticas del 2do Parcial — Inteligencia de Negocios

Esta carpeta contiene los **4 datasets etiquetados** (uno por cada Data Mart de hechos del modelo dimensional `DM_Financial_Kimball_v2`) libres de fuga de datos (*data leakage*), junto con las dos entregas prácticas solicitadas:

1. **Tarea 1 (`Tarea1_Reduccion_MNIST_2D/`):** reducción de dimensionalidad a un plano euclidiano bidimensional $\mathbb{R}^n \to [v_1, v_2]$ con **t-SNE** e **Isomap**, usando **todas las características y todas las observaciones** de cada dataset (un punto por observación, sin balancear), con una demostración de referencia sobre el **MNIST real** (OpenML `mnist_784`: 70,000 imágenes de 28 × 28; se usa una muestra estratificada de 3,000). Incluye los **4 gráficos individuales multiclase (3 a 4 colores por Data Mart)** y los **4 gráficos individuales binarios (2 colores)** comparando `t-SNE` frente a `Isomap`.
2. **Tarea 2 (`Tarea2_Regresion_Logistica/`):** **Regresión Logística Binaria** programada desde cero (sin `LogisticRegression` de `scikit-learn`) con **Entropía Cruzada** y **Gradiente Descendente** ($\eta = 1.0$, parada cuando $\lVert\nabla J\rVert < 10^{-6}$). Se entrega el vector de pesos final $\beta$, `Acc. Train`, `Acc. Test` y las figuras. `scipy.optimize.minimize` (BFGS) se usa solo para verificar que el gradiente descendente llegó al mínimo.

Cada tarea tiene su informe Word dentro de su carpeta.

---

## Resumen de los 4 Datasets por Data Mart

| Archivo CSV | Data Mart Kimball | Filas | Variables $X$ | Variable Objetivo Binaria (`Clase` — Tarea 2) | Versión Multiclase Real (`Clase_Multiclase` — Tarea 1) | Balanceo (Tarea 2) |
| :--- | :--- | :---: | :---: | :--- | :--- | :--- |
| `01_dm_prestamos.csv` | `Fact_Prestamos` | 682 | 14 | `1` = Mora (`B, D`: 76) vs. `0` = Sano (`A, C`: 606) | **4 clases:** Estado del préstamo (`A`, `B`, `C`, `D`) | Se parte 80/20 y luego se sobremuestrea **solo el entrenamiento**; la prueba conserva la proporción real |
| `02_dm_saldo_mensual.csv` | `Fact_Saldo_Cuenta_Mensual` | 5,000 *(de 181,115 meses)* | 15 | `1` = Sobregiro el mes siguiente ($t+1$: 708) vs. `0` = Sin sobregiro (4,292) | **3 clases en $t+1$ (definidas por el equipo con el saldo de $t+1$):** `1` Saldo estable/creciente, `2` Caída sin sobregiro, `3` En sobregiro | Submuestreo 708 vs. 708 **antes** de partir 80/20 |
| `03_dm_ordenes.csv` | `Fact_Ordenes` | 5,092 | 10 | `1` = Obligación financiera (`UVER, POJISTNE, LEASING`: 1,590) vs. `0` = Hogar (`SIPO`: 3,502) | **4 clases:** Tipo de orden (`SIPO`, `UVER`, `POJISTNE`, `LEASING`) | Submuestreo 1,590 vs. 1,590 **antes** de partir 80/20 |
| `04_dm_transacciones.csv` | `Fact_Transacciones` | 20,000 *(de 871,629 sin intereses)* | 11 | `1` = Egreso (10,000) vs. `0` = Ingreso (10,000) | **4 clases:** Operación bancaria (`VKLAD`, `VYBER`, `PREVOD NA UCET`, `PREVOD Z UCTU`) | Ya balanceado 50/50 en el CSV |

En los tres Data Marts submuestreados la prueba también queda balanceada (línea base 50 %). En Préstamos la línea base de la prueba es 88.97 % (responder siempre «sano»).

**Notas importantes:**

- En Préstamos se excluyeron `meses_transcurridos_al_corte` y `saldo_pendiente_estimado`: se miden al corte de 1998, no al otorgar el crédito, y separan por sí solas los contratos terminados (A, B) de los vigentes (C, D).
- En Saldo Mensual el CSV guarda **todos** los positivos (708) y 4,292 negativos al azar. La proporción de 14 % es una muestra de trabajo: en la población solo el 0.39 % de los meses termina en sobregiro al mes siguiente. Además, 388 de los 708 positivos ya estaban en sobregiro en el mes $t$ (el sobregiro persiste).
- La exactitud 2D de la Tarea 1 es un kNN ($k = 5$) con validación cruzada de 5 pliegues, comparada con la clase mayoritaria. El balanceo solo se aplica al entrenar (Tarea 2).

## Resultados de la Tarea 2

| Data Mart | Acc. Train | Acc. Test | Línea base Test | Sensibilidad / Especificidad |
| :--- | :---: | :---: | :---: | :---: |
| Préstamos | 74.74 % | 73.53 % | 88.97 % | 53.3 % / 76.0 % |
| Saldo Mensual | 90.19 % | 92.61 % | 50.00 % | 92.3 % / 93.0 % |
| Órdenes | 75.55 % | 74.53 % | 50.00 % | 74.8 % / 74.2 % |
| Transacciones | 72.89 % | 72.05 % | 50.00 % | 75.1 % / 69.0 % |

## Cómo reproducir

Desde la raíz del repositorio:

```bash
python scripts/44_generar_datasets_2parcial.py
python 2parcial/Tarea1_Reduccion_MNIST_2D/reduccion_mnist_2d.py
python 2parcial/Tarea2_Regresion_Logistica/regresion_logistica.py
python scripts/47_generar_informe_tarea1.py
python scripts/48_generar_informe_tarea2.py
```

La primera ejecución de la Tarea 1 descarga MNIST desde OpenML (queda en caché en `~/scikit_learn_data`).
