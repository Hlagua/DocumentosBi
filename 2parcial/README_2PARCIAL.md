# Datasets y Prácticas del 2do Parcial — Inteligencia de Negocios

Esta carpeta contiene los **4 datasets etiquetados** (uno por cada Data Mart de hechos del modelo dimensional `DM_Financial_Kimball_v2`) libres de fuga de datos (*data leakage*), junto con las dos entregas prácticas solicitadas:

1. **Tarea 1 (`Tarea1_Reduccion_MNIST_2D/`):** Reducción de dimensionalidad a un plano euclidiano bidimensional $\mathbb{R}^n \to [v_1, v_2]$ con **t-SNE** (y demostración de referencia con el dataset **MNIST**), graficando la separación por clases binarias y multiclase reales de los 4 Data Marts.
2. **Tarea 2 (`Tarea2_Regresion_Logistica/`):** Entrenamiento desde cero de **Regresión Logística Binaria** empleando únicamente la función de pérdida de **Entropía Cruzada** y optimización por **Gradiente Descendente** (sin usar `LogisticRegression` de `scikit-learn`), reportando el vector de pesos final $\beta$, la exactitud de entrenamiento (`Acc. Train`), la exactitud de prueba (`Acc. Test`) y las fronteras de decisión proyectadas en 2D mediante **PCA**.

---

## Resumen de los 4 Datasets por Data Mart

| Archivo CSV | Data Mart Kimball | Filas | Variables $X$ | Variable Objetivo Binaria (`Clase`) | Versión Multiclase Real (Tarea 1) | Estrategia de Balanceo (tras partir 80/20) |
| :--- | :--- | :---: | :---: | :--- | :--- | :--- |
| `01_dm_prestamos.csv` | `Fact_Prestamos` | 682 | 16 | `1` = Mora (`B, D`: 76) vs. `0` = Sano (`A, C`: 606) | Estado del préstamo: `A`, `B`, `C`, `D` (4 clases) | Sobremuestreo (*oversampling*) solo en entrenamiento |
| `02_dm_saldo_mensual.csv` | `Fact_Saldo_Cuenta_Mensual` | 5,000 *(de 181,115 meses)* | 15 | `1` = Sobregiro el mes siguiente ($t+1$: 708) vs. `0` = Sin sobregiro (4,292) | Binaria (2 clases) | Submuestreo (*undersampling* 708 vs. 708) |
| `03_dm_ordenes.csv` | `Fact_Ordenes` | 5,092 | 10 | `1` = Obligación financiera (`UVER, POJISTNE, LEASING`: 1,590) vs. `0` = Hogar (`SIPO`: 3,502) | Tipo de orden: `SIPO`, `UVER`, `POJISTNE`, `LEASING` (4 clases) | Submuestreo (*undersampling* 1,590 vs. 1,590) |
| `04_dm_transacciones.csv` | `Fact_Transacciones` | 20,000 *(de 871,629 sin intereses)* | 11 | `1` = Egreso (10,000) vs. `0` = Ingreso (10,000) | Binaria (2 clases) | Balanceado 50/50 por submuestreo estratificado |
