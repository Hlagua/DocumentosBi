# Comparación: pesos por clase frente a sobremuestreo 50/50

Las dos versiones usan los mismos datos, la misma partición 60/20/20 y la misma búsqueda de arquitectura. Cambia solo cómo se trata el desbalance **en el entrenamiento**; validación y prueba conservan la proporción real.

## S2 · Propósito de la orden permanente

| Métrica | Pesos por clase | Sobremuestreo 50/50 |
| :--- | :---: | :---: |
| Entrenamiento por clase | 2101 / 430 / 320 / 205 | 2101 / 2101 / 2101 / 2101 |
| Arquitectura elegida | 128-64-32 tanh | 64-32 sigmoid |
| Exactitud (prueba) | 81.1 % | 82.2 % |
| Exactitud balanceada (prueba) | 85.3 % | 85.4 % |
| F1 macro (prueba) | 0.751 | 0.758 |
| E_in (entrenamiento real) | 16.6 % | 16.1 % |
| E_out (prueba) | 18.9 % | 17.8 % |
| E_out − E_in (límite 5 puntos) | +2.2 ✅ | +1.7 ✅ |
| Error CV-5 (promedio ± σ) | 17.8 ± 1.3 % | 18.7 ± 0.8 % |
| Softmax lineal, exactitud balanceada | 78.5 % | 78.5 % |
| Épocas (mejor época) | 82 (62) | 120 (100) |
| Tiempo total del proceso | 78.2 min | 85.0 min |

**Sensibilidad por clase (prueba):**

| Clase | Pesos por clase | Sobremuestreo 50/50 |
| :--- | :---: | :---: |
| Hogar (SIPO) | 77.4 % | 79.1 % |
| Préstamo (UVER) | 93.8 % | 93.8 % |
| Seguro (POJISTNE) | 87.7 % | 87.7 % |
| Arrendamiento (LEASING) | 82.3 % | 80.9 % |

## S4 · Mora al corte (31/12/1998) de un préstamo

| Métrica | Pesos por clase | Sobremuestreo 50/50 |
| :--- | :---: | :---: |
| Entrenamiento por clase | 364 / 46 | 364 / 364 |
| Arquitectura elegida | PCA → 64-32 tanh | PCA → 32 tanh |
| Exactitud (prueba) | 83.1 % | 85.3 % |
| Exactitud balanceada (prueba) | 81.7 % | 68.4 % |
| F1 macro (prueba) | 0.704 | 0.664 |
| AUC (prueba) | 0.829 | 0.798 |
| E_in (entrenamiento real) | 16.1 % | 3.7 % |
| E_out (prueba) | 16.9 % | 14.7 % |
| E_out − E_in (límite 5 puntos) | +0.8 ✅ | +11.1 ⚠ |
| Error CV-5 (promedio ± σ) | 17.8 ± 3.8 % | 15.9 ± 2.3 % |
| Softmax lineal, exactitud balanceada | 77.6 % | 74.7 % |
| Épocas (mejor época) | 48 (28) | 93 (73) |
| Tiempo total del proceso | 4.7 min | 4.1 min |

**Sensibilidad por clase (prueba):**

| Clase | Pesos por clase | Sobremuestreo 50/50 |
| :--- | :---: | :---: |
| Al día al corte (A o C) | 83.5 % | 90.1 % |
| En mora o impago al corte (B o D) | 80.0 % | 46.7 % |
