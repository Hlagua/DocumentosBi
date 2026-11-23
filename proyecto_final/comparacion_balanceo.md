# Comparación: pesos por clase frente a sobremuestreo 50/50

Las dos versiones usan los mismos datos, la misma partición 60/20/20 y la misma búsqueda de arquitectura. Cambia solo cómo se trata el desbalance **en el entrenamiento**; validación y prueba conservan la proporción real.

## S2 · Propósito de la orden permanente

| Métrica | Pesos por clase | Sobremuestreo 50/50 |
| :--- | :---: | :---: |
| Entrenamiento por clase | 2101 / 430 / 320 / 205 | 2101 / 2101 / 2101 / 2101 |
| Arquitectura elegida | 64-32 relu | 128-64-32 relu |
| Exactitud (prueba) | 80.8 % | 81.9 % |
| Exactitud balanceada (prueba) | 84.3 % | 84.6 % |
| F1 macro (prueba) | 0.743 | 0.753 |
| E_in (entrenamiento real) | 16.5 % | 15.9 % |
| E_out (prueba) | 19.2 % | 18.1 % |
| E_out − E_in (límite 5 puntos) | +2.6 ✅ | +2.2 ✅ |
| Error CV-5 (promedio ± σ) | 18.0 ± 1.2 % | 18.3 ± 1.1 % |
| Softmax lineal, exactitud balanceada | 78.5 % | 78.5 % |
| Épocas (mejor época) | 80 (60) | 30 (10) |
| Tiempo total del proceso | 5.7 min | 5.4 min |

**Sensibilidad por clase (prueba):**

| Clase | Pesos por clase | Sobremuestreo 50/50 |
| :--- | :---: | :---: |
| Hogar (SIPO) | 77.6 % | 79.3 % |
| Préstamo (UVER) | 92.4 % | 93.8 % |
| Seguro (POJISTNE) | 87.7 % | 83.0 % |
| Arrendamiento (LEASING) | 79.4 % | 82.3 % |

## S3 · Estado del saldo el mes siguiente

| Métrica | Pesos por clase | Sobremuestreo 50/50 |
| :--- | :---: | :---: |
| Entrenamiento por clase | 1200 / 1200 / 424 | 1200 / 1200 / 1200 |
| Arquitectura elegida | 128-64-32 relu | 64-32 tanh |
| Exactitud (prueba) | 62.8 % | 62.1 % |
| Exactitud balanceada (prueba) | 68.4 % | 67.5 % |
| F1 macro (prueba) | 0.656 | 0.667 |
| E_in (entrenamiento real) | 33.1 % | 32.6 % |
| E_out (prueba) | 37.1 % | 37.9 % |
| E_out − E_in (límite 5 puntos) | +4.0 ✅ | +5.2 ⚠ |
| Error CV-5 (promedio ± σ) | 37.8 ± 1.5 % | 37.3 ± 1.1 % |
| Softmax lineal, exactitud balanceada | 65.3 % | 64.5 % |
| Épocas (mejor época) | 43 (23) | 72 (52) |
| Tiempo total del proceso | 4.4 min | 4.0 min |

**Sensibilidad por clase (prueba):**

| Clase | Pesos por clase | Sobremuestreo 50/50 |
| :--- | :---: | :---: |
| Saldo estable o creciente | 36.0 % | 48.5 % |
| Caída de saldo sin sobregiro | 80.5 % | 66.8 % |
| Sobregiro | 88.7 % | 87.3 % |

## S4 · Mora al corte (31/12/1998) de un préstamo

| Métrica | Pesos por clase | Sobremuestreo 50/50 |
| :--- | :---: | :---: |
| Entrenamiento por clase | 364 / 46 | 364 / 364 |
| Arquitectura elegida | PCA → 128-64-32 relu | 128-64-32 relu |
| Exactitud (prueba) | 79.4 % | 84.6 % |
| Exactitud balanceada (prueba) | 68.0 % | 73.8 % |
| F1 macro (prueba) | 0.620 | 0.686 |
| AUC (prueba) | 0.795 | 0.856 |
| E_in (entrenamiento real) | 17.3 % | 10.2 % |
| E_out (prueba) | 20.6 % | 15.4 % |
| E_out − E_in (límite 5 puntos) | +3.3 ✅ | +5.2 ⚠ |
| Error CV-5 (promedio ± σ) | 19.0 ± 4.2 % | 15.6 ± 2.7 % |
| Softmax lineal, exactitud balanceada | 77.6 % | 78.0 % |
| Épocas (mejor época) | 27 (7) | 24 (4) |
| Tiempo total del proceso | 1.2 min | 0.9 min |

**Sensibilidad por clase (prueba):**

| Clase | Pesos por clase | Sobremuestreo 50/50 |
| :--- | :---: | :---: |
| Al día al corte (A o C) | 82.6 % | 87.6 % |
| En mora o impago al corte (B o D) | 53.3 % | 60.0 % |
