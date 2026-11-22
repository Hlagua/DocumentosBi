# Comparación: pesos por clase frente a sobremuestreo 50/50

Las dos versiones usan los mismos datos, la misma partición 60/20/20 y la misma búsqueda de arquitectura. Cambia solo cómo se trata el desbalance **en el entrenamiento**; validación y prueba conservan la proporción real.

## S2 · Propósito de la orden permanente

| Métrica | Pesos por clase | Sobremuestreo 50/50 |
| :--- | :---: | :---: |
| Entrenamiento por clase | datos reales | 2101 / 2101 / 2101 / 2101 |
| Arquitectura elegida | 64-32 tanh | 64-32 tanh |
| Exactitud (prueba) | 81.4 % | 82.2 % |
| Exactitud balanceada (prueba) | 83.3 % | 83.6 % |
| F1 macro (prueba) | 0.743 | 0.754 |
| E_in (entrenamiento real) | 16.1 % | 13.8 % |
| E_out (prueba) | 18.6 % | 17.8 % |
| E_out − E_in (límite 5 puntos) | +2.6 ✅ | +4.1 ✅ |
| Error CV-5 (promedio ± σ) | 18.4 ± 1.9 % | 17.7 ± 2.5 % |
| Softmax lineal, exactitud balanceada | 76.3 % | 76.0 % |
| Épocas (mejor época) | 144 (124) | 101 (81) |
| Tiempo total del proceso | 25.7 min | 8.2 min |

**Sensibilidad por clase (prueba):**

| Clase | Pesos por clase | Sobremuestreo 50/50 |
| :--- | :---: | :---: |
| Hogar (SIPO) | 78.5 % | 79.9 % |
| Préstamo (UVER) | 94.4 % | 94.4 % |
| Seguro (POJISTNE) | 89.7 % | 85.0 % |
| Arrendamiento (LEASING) | 70.6 % | 75.0 % |

## S3 · Estado del saldo el mes siguiente

| Métrica | Pesos por clase | Sobremuestreo 50/50 |
| :--- | :---: | :---: |
| Entrenamiento por clase | datos reales | 1200 / 1200 / 1200 |
| Arquitectura elegida | 64-32 tanh | 64-32 relu |
| Exactitud (prueba) | 63.5 % | 63.7 % |
| Exactitud balanceada (prueba) | 68.5 % | 68.6 % |
| F1 macro (prueba) | 0.669 | 0.679 |
| E_in (entrenamiento real) | 35.7 % | 31.1 % |
| E_out (prueba) | 36.4 % | 36.3 % |
| E_out − E_in (límite 5 puntos) | +0.7 ✅ | +5.2 ⚠ |
| Error CV-5 (promedio ± σ) | 37.3 ± 1.3 % | 37.2 ± 0.7 % |
| Softmax lineal, exactitud balanceada | 65.0 % | 64.5 % |
| Épocas (mejor época) | 63 (43) | 42 (22) |
| Tiempo total del proceso | 7.0 min | 8.1 min |

**Sensibilidad por clase (prueba):**

| Clase | Pesos por clase | Sobremuestreo 50/50 |
| :--- | :---: | :---: |
| Saldo estable o creciente | 42.2 % | 46.5 % |
| Caída de saldo sin sobregiro | 76.8 % | 72.8 % |
| Sobregiro | 86.5 % | 86.5 % |

## S4 · Riesgo de impago de un préstamo nuevo

| Métrica | Pesos por clase | Sobremuestreo 50/50 |
| :--- | :---: | :---: |
| Entrenamiento por clase | datos reales | 364 / 364 |
| Arquitectura elegida | PCA → 128-64-32 relu | 128-64-32 relu |
| Exactitud (prueba) | 79.4 % | 84.6 % |
| Exactitud balanceada (prueba) | 68.0 % | 73.8 % |
| F1 macro (prueba) | 0.620 | 0.686 |
| AUC (prueba) | 0.795 | 0.856 |
| E_in (entrenamiento real) | 17.3 % | 10.2 % |
| E_out (prueba) | 20.6 % | 15.4 % |
| E_out − E_in (límite 5 puntos) | +3.3 ✅ | +5.2 ⚠ |
| Error CV-5 (promedio ± σ) | 16.1 ± 0.5 % | 14.5 ± 3.1 % |
| Softmax lineal, exactitud balanceada | 77.6 % | 78.0 % |
| Épocas (mejor época) | 27 (7) | 24 (4) |
| Tiempo total del proceso | 4.6 min | 2.6 min |

**Sensibilidad por clase (prueba):**

| Clase | Pesos por clase | Sobremuestreo 50/50 |
| :--- | :---: | :---: |
| Paga sin problemas (A o C) | 82.6 % | 87.6 % |
| Impago (B o D) | 53.3 % | 60.0 % |
