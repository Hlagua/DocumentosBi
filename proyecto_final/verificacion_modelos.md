# Verificación de las redes neuronales (pesos por clase frente a sobremuestreo)

Pruebas pedidas para la defensa: (A) datos parecidos al dataset, (B) datos que el modelo nunca vio, (C) casos en la frontera de decisión y (D) búsqueda de atajos con importancia por permutación y datos sintéticos extremos. S1 ya estaba balanceado, por eso sus dos columnas usan el mismo modelo.

**Control:** los datos nunca vistos se recalcularon con el mismo procedimiento del dataset. Al recalcular las filas que sí están en el dataset, coinciden exactamente: S1 = True (24,000 filas), S3 = True (4,708 filas).

## S1 · Tipo de transacción

| Prueba | Pesos por clase | Sobremuestreo 50/50 |
| :--- | :---: | :---: |
| Prueba original: exactitud balanceada | 76.8 % | 76.8 % |
| A. Parecidos (ruido 5 %): exactitud balanceada | 73.5 % | 73.5 % |
| A. Parecidos: predicciones que no cambian | 93.2 % | 93.2 % |
| B. Nunca vistos: casos | 10,000 | 10,000 |
| B. Nunca vistos: exactitud | 76.8 % | 76.8 % |
| B. Nunca vistos: exactitud balanceada | 76.8 % | 76.8 % |
| B. Nunca vistos: sensibilidad por clase (— = sin casos) | 59.8 % · 71.0 % · 87.6 % · 88.8 % | 59.8 % · 71.0 % · 87.6 % · 88.8 % |
| Prueba original: sensibilidad por clase | 59.8 % · 69.7 % · 87.6 % · 90.2 % | 59.8 % · 69.7 % · 87.6 % · 90.2 % |
| C. Casos en frontera (margen < 10 pts) | 6.9 % (1,020) | 6.9 % (1,020) |
| C. Acierto en frontera / fuera | 49.0 % / 78.9 % | 49.0 % / 78.9 % |
| C. Clase real entre las dos más probables | 92.5 % | 92.5 % |
| D. Característica más influyente (peso relativo) | monto (34.5 %) | monto (34.5 %) |

**D. Importancia por permutación (pesos por clase):** monto +29.7 · dia +26.0 · edad +13.9 · saldo_despues +8.1 · poblacion +3.1 (puntos de exactitud balanceada que se pierden al desordenarla)
**D. Extremos sintéticos (pesos por clase):** monto:muy_bajo → Transferencia enviada 99.8 %; saldo_despues:muy_alto → Depósito en efectivo 98.3 %; saldo_despues:muy_bajo → Depósito en efectivo 99.8 %

**D. Importancia por permutación (sobremuestreo):** monto +29.7 · dia +26.0 · edad +13.9 · saldo_despues +8.1 · poblacion +3.1 (puntos de exactitud balanceada que se pierden al desordenarla)
**D. Extremos sintéticos (sobremuestreo):** monto:muy_bajo → Transferencia enviada 99.8 %; saldo_despues:muy_alto → Depósito en efectivo 98.3 %; saldo_despues:muy_bajo → Depósito en efectivo 99.8 %

## S2 · Propósito de la orden permanente

| Prueba | Pesos por clase | Sobremuestreo 50/50 |
| :--- | :---: | :---: |
| Prueba original: exactitud balanceada | 83.3 % | 83.6 % |
| A. Parecidos (ruido 5 %): exactitud balanceada | 84.0 % | 83.4 % |
| A. Parecidos: predicciones que no cambian | 98.7 % | 98.4 % |
| B. Nunca vistos | no hay datos reales sin usar | no hay datos reales sin usar |
| C. Casos en frontera (margen < 10 pts) | 3.3 % (34) | 3.4 % (35) |
| C. Acierto en frontera / fuera | 44.1 % / 82.7 % | 34.3 % / 83.9 % |
| C. Clase real entre las dos más probables | 91.2 % | 85.7 % |
| D. Característica más influyente (peso relativo) | monto_orden (29.1 %) | monto_orden (28.7 %) |

**D. Importancia por permutación (pesos por clase):** monto_orden +32.7 · tiene_prestamo +23.9 · cuota_prestamo +22.2 · ordenes_activas_cuenta +14.3 · retiro_mensual +10.9 (puntos de exactitud balanceada que se pierden al desordenarla)
**D. Extremos sintéticos (pesos por clase):** monto_orden:muy_alto → Hogar (SIPO) 100.0 %; monto_orden:muy_bajo → Seguro (POJISTNE) 94.2 %; retiro_mensual:muy_bajo → Hogar (SIPO) 97.1 %

**D. Importancia por permutación (sobremuestreo):** monto_orden +34.9 · tiene_prestamo +25.6 · cuota_prestamo +22.2 · ordenes_activas_cuenta +14.4 · retiro_mensual +13.6 (puntos de exactitud balanceada que se pierden al desordenarla)
**D. Extremos sintéticos (sobremuestreo):** monto_orden:muy_alto → Hogar (SIPO) 100.0 %; retiro_mensual:muy_bajo → Hogar (SIPO) 97.8 %

## S3 · Estado del saldo el mes siguiente

| Prueba | Pesos por clase | Sobremuestreo 50/50 |
| :--- | :---: | :---: |
| Prueba original: exactitud balanceada | 68.5 % | 68.6 % |
| A. Parecidos (ruido 5 %): exactitud balanceada | 68.3 % | 68.4 % |
| A. Parecidos: predicciones que no cambian | 98.0 % | 98.5 % |
| B. Nunca vistos: casos | 5,000 | 5,000 |
| B. Nunca vistos: exactitud | 58.5 % | 57.7 % |
| B. Nunca vistos: exactitud balanceada | 58.5 % | 57.7 % |
| B. Nunca vistos: sensibilidad por clase (— = sin casos) | 40.0 % · 77.0 % · — | 46.6 % · 68.9 % · — |
| Prueba original: sensibilidad por clase | 42.2 % · 76.8 % · 86.5 % | 46.5 % · 72.8 % · 86.5 % |
| C. Casos en frontera (margen < 10 pts) | 24.1 % (1,435) | 35.4 % (2,106) |
| C. Acierto en frontera / fuera | 49.8 % / 62.4 % | 49.3 % / 63.8 % |
| C. Clase real entre las dos más probables | 97.8 % | 98.8 % |
| D. Característica más influyente (peso relativo) | saldo_fin_mes (36.1 %) | saldo_fin_mes (26.2 %) |

**D. Importancia por permutación (pesos por clase):** saldo_fin_mes +14.7 · saldo_promedio_mes +10.8 · saldo_min_mes +4.3 · monto_medio_mov +3.4 · num_movimientos_mes +3.4 (puntos de exactitud balanceada que se pierden al desordenarla)
**D. Extremos sintéticos (pesos por clase):** saldo_fin_mes:muy_alto → Caída de saldo sin sobregiro 100.0 %; saldo_fin_mes:muy_bajo → Sobregiro 100.0 %; saldo_promedio_mes:muy_alto → Caída de saldo sin sobregiro 99.8 %; saldo_promedio_mes:muy_bajo → Sobregiro 100.0 %; saldo_min_mes:muy_alto → Saldo estable o creciente 99.8 %; saldo_min_mes:muy_bajo → Sobregiro 98.3 %; num_movimientos_mes:muy_alto → Sobregiro 90.8 %; monto_medio_mov:muy_alto → Sobregiro 100.0 %; monto_medio_mov:muy_bajo → Saldo estable o creciente 99.7 %

**D. Importancia por permutación (sobremuestreo):** saldo_fin_mes +12.1 · saldo_promedio_mes +10.0 · saldo_min_mes +6.0 · num_movimientos_mes +3.9 · monto_medio_mov +2.5 (puntos de exactitud balanceada que se pierden al desordenarla)
**D. Extremos sintéticos (sobremuestreo):** saldo_fin_mes:muy_alto → Caída de saldo sin sobregiro 100.0 %; saldo_fin_mes:muy_bajo → Sobregiro 100.0 %; saldo_promedio_mes:muy_alto → Caída de saldo sin sobregiro 95.3 %; saldo_promedio_mes:muy_bajo → Sobregiro 100.0 %; saldo_min_mes:muy_alto → Saldo estable o creciente 98.6 %; saldo_min_mes:muy_bajo → Sobregiro 100.0 %; monto_medio_mov:muy_alto → Sobregiro 98.7 %; monto_medio_mov:muy_bajo → Saldo estable o creciente 95.4 %

## S4 · Riesgo de impago de un préstamo nuevo

| Prueba | Pesos por clase | Sobremuestreo 50/50 |
| :--- | :---: | :---: |
| Prueba original: exactitud balanceada | 68.0 % | 73.8 % |
| A. Parecidos (ruido 5 %): exactitud balanceada | 65.2 % | 73.2 % |
| A. Parecidos: predicciones que no cambian | 97.9 % | 97.8 % |
| B. Nunca vistos | no hay datos reales sin usar | no hay datos reales sin usar |
| C. Casos en frontera (margen < 10 pts) | 7.3 % (10) | 5.1 % (7) |
| C. Acierto en frontera / fuera | 50.0 % / 81.8 % | 57.1 % / 86.1 % |
| C. Clase real entre las dos más probables | 100.0 % | 100.0 % |
| D. Característica más influyente (peso relativo) | saldo_minimo_previo (45.0 %) | saldo_minimo_previo (33.3 %) |

**D. Importancia por permutación (pesos por clase):** saldo_minimo_previo +12.4 · monto_prestamo +10.5 · meses_historial +1.5 · tasa_desempleo +1.0 · es_mujer +0.7 (puntos de exactitud balanceada que se pierden al desordenarla)
**D. Extremos sintéticos (pesos por clase):** monto_prestamo:muy_alto → Impago (B o D) 99.3 %; monto_prestamo:muy_bajo → Paga sin problemas (A o C) 100.0 %; plazo_meses:muy_alto → Paga sin problemas (A o C) 99.3 %; saldo_promedio_previo:muy_alto → Paga sin problemas (A o C) 100.0 %; saldo_promedio_previo:muy_bajo → Impago (B o D) 100.0 %; saldo_minimo_previo:muy_alto → Paga sin problemas (A o C) 100.0 %; saldo_minimo_previo:muy_bajo → Impago (B o D) 100.0 %; ingreso_mensual:muy_alto → Paga sin problemas (A o C) 91.2 %; movimientos_mes:muy_alto → Paga sin problemas (A o C) 98.5 %; meses_historial:muy_alto → Paga sin problemas (A o C) 90.4 %

**D. Importancia por permutación (sobremuestreo):** saldo_minimo_previo +14.2 · monto_prestamo +13.5 · es_mujer +3.8 · meses_historial +3.5 · saldo_promedio_previo +3.5 (puntos de exactitud balanceada que se pierden al desordenarla)
**D. Extremos sintéticos (sobremuestreo):** monto_prestamo:muy_alto → Impago (B o D) 98.5 %; monto_prestamo:muy_bajo → Paga sin problemas (A o C) 100.0 %; plazo_meses:muy_alto → Paga sin problemas (A o C) 98.5 %; saldo_promedio_previo:muy_alto → Paga sin problemas (A o C) 100.0 %; saldo_promedio_previo:muy_bajo → Impago (B o D) 100.0 %; saldo_minimo_previo:muy_alto → Paga sin problemas (A o C) 100.0 %; saldo_minimo_previo:muy_bajo → Impago (B o D) 100.0 %; ingreso_mensual:muy_bajo → Paga sin problemas (A o C) 97.8 %; egreso_mensual:muy_alto → Impago (B o D) 97.1 %; egreso_mensual:muy_bajo → Paga sin problemas (A o C) 97.1 %; movimientos_mes:muy_bajo → Impago (B o D) 95.6 %; meses_historial:muy_alto → Paga sin problemas (A o C) 97.8 %
