# Verificación de las redes neuronales (pesos por clase frente a sobremuestreo)

Pruebas pedidas para la defensa: (A) datos parecidos al dataset, (B) datos que el modelo nunca vio, (C) casos en la frontera de decisión y (D) búsqueda de atajos con importancia por permutación y datos sintéticos extremos. S1 ya estaba balanceado, por eso sus dos columnas usan el mismo modelo.

**Control:** los datos nunca vistos se recalcularon con el mismo procedimiento del dataset. Al recalcular las filas que sí están en el dataset, coinciden exactamente: S1 = True (24,000 filas), S3 = True (4,708 filas).

**Partición por cuenta:** en S1, S2 y S3 ninguna cuenta está en dos particiones. Los "nunca vistos" (B) salen solo de cuentas que no se usaron para entrenar ni validar (S1: 1057 cuentas; S3: 2431 cuentas), pero no son un grupo de clientes aparte: incluyen las cuentas de la prueba (S1: 857 de las 1057). Por eso (B) confirma, con otros movimientos de esos mismos clientes, que el resultado de la prueba se sostiene; no demuestra que la red acierte igual en otra población.

(E) compara S2 con una regla de una línea. (F) evalúa S3 con la proporción real de meses del banco. Los 142 sobregiros de (F) son exactamente los mismos de la prueba, porque todos los sobregiros del banco ya estaban en el dataset; la sensibilidad de sobregiro en (F) repite la de la prueba y no es una medida nueva. Lo nuevo de (F) es la exactitud global frente a "siempre estable", porque casi todos esos meses estables y de caída no están en la prueba.

## S1 · Tipo de transacción

| Prueba | Pesos por clase | Sobremuestreo 50/50 |
| :--- | :---: | :---: |
| Prueba original: exactitud balanceada | 76.9 % | 76.9 % |
| A. Parecidos (ruido 5 %): exactitud balanceada | 73.9 % | 73.9 % |
| A. Parecidos: predicciones que no cambian | 93.3 % | 93.3 % |
| B. Nunca vistos: casos | 10,000 | 10,000 |
| B. Nunca vistos: exactitud | 76.3 % | 76.3 % |
| B. Nunca vistos: exactitud balanceada | 76.3 % | 76.3 % |
| B. Nunca vistos: sensibilidad por clase (— = sin casos) | 62.8 % · 70.8 % · 86.5 % · 85.2 % | 62.8 % · 70.8 % · 86.5 % · 85.2 % |
| Prueba original: sensibilidad por clase | 64.0 % · 71.4 % · 86.4 % · 85.8 % | 64.0 % · 71.4 % · 86.4 % · 85.8 % |
| C. Casos en frontera (margen < 10 pts) | 8.0 % (1,176) | 8.0 % (1,176) |
| C. Acierto en frontera / fuera | 52.5 % / 78.6 % | 52.5 % / 78.6 % |
| C. Clase real entre las dos más probables | 90.6 % | 90.6 % |
| D. Característica más influyente (peso relativo) | monto (35.3 %) | monto (35.3 %) |

**D. Importancia por permutación (pesos por clase):** monto +30.4 · dia +26.5 · edad +13.0 · saldo_despues +8.8 · tasa_criminalidad +2.7 (puntos de exactitud balanceada que se pierden al desordenarla)
**D. Extremos sintéticos (pesos por clase):** monto:muy_alto → Retiro (efectivo o tarjeta) 99.3 %; saldo_despues:muy_bajo → Depósito en efectivo 94.3 %

**D. Importancia por permutación (sobremuestreo):** monto +30.4 · dia +26.5 · edad +13.0 · saldo_despues +8.8 · tasa_criminalidad +2.7 (puntos de exactitud balanceada que se pierden al desordenarla)
**D. Extremos sintéticos (sobremuestreo):** monto:muy_alto → Retiro (efectivo o tarjeta) 99.3 %; saldo_despues:muy_bajo → Depósito en efectivo 94.3 %

## S2 · Propósito de la orden permanente

| Prueba | Pesos por clase | Sobremuestreo 50/50 |
| :--- | :---: | :---: |
| Prueba original: exactitud balanceada | 84.3 % | 84.6 % |
| A. Parecidos (ruido 5 %): exactitud balanceada | 83.9 % | 84.2 % |
| A. Parecidos: predicciones que no cambian | 98.5 % | 98.6 % |
| B. Nunca vistos | no hay datos reales sin usar | no hay datos reales sin usar |
| C. Casos en frontera (margen < 10 pts) | 2.9 % (29) | 2.9 % (30) |
| C. Acierto en frontera / fuera | 51.7 % / 81.7 % | 50.0 % / 82.9 % |
| C. Clase real entre las dos más probables | 93.1 % | 86.7 % |
| D. Característica más influyente (peso relativo) | monto_orden (27.1 %) | monto_orden (27.6 %) |
| E. Regla de una línea (monto = cuota → préstamo; si no, hogar): exactitud / balanceada | 81.6 % / 47.7 % | 81.6 % / 47.7 % |
| E. Red neuronal en la misma prueba: exactitud / balanceada | 80.8 % / 84.3 % | 81.9 % / 84.6 % |
| E. Sensibilidad de la regla por clase | 100.0 % · 91.0 % · 0.0 % · 0.0 % | 100.0 % · 91.0 % · 0.0 % · 0.0 % |

**D. Importancia por permutación (pesos por clase):** monto_orden +32.3 · tiene_prestamo +25.6 · cuota_prestamo +19.7 · ordenes_activas_cuenta +18.9 · retiro_mensual +13.6 (puntos de exactitud balanceada que se pierden al desordenarla)
**D. Extremos sintéticos (pesos por clase):** monto_orden:muy_alto → Hogar (SIPO) 100.0 %; monto_orden:muy_bajo → Hogar (SIPO) 95.0 %; edad:muy_alto → Hogar (SIPO) 99.9 %; ordenes_activas_cuenta:muy_alto → Seguro (POJISTNE) 92.2 %; saldo_promedio_cuenta:muy_alto → Hogar (SIPO) 97.2 %; deposito_mensual:muy_alto → Hogar (SIPO) 97.9 %; deposito_mensual:muy_bajo → Hogar (SIPO) 93.2 %; retiro_mensual:muy_bajo → Hogar (SIPO) 100.0 %

**D. Importancia por permutación (sobremuestreo):** monto_orden +35.2 · tiene_prestamo +25.0 · cuota_prestamo +21.3 · ordenes_activas_cuenta +17.8 · retiro_mensual +14.0 (puntos de exactitud balanceada que se pierden al desordenarla)
**D. Extremos sintéticos (sobremuestreo):** monto_orden:muy_alto → Hogar (SIPO) 100.0 %; monto_orden:muy_bajo → Seguro (POJISTNE) 99.2 %; edad:muy_alto → Hogar (SIPO) 100.0 %; saldo_promedio_cuenta:muy_alto → Hogar (SIPO) 97.5 %; deposito_mensual:muy_alto → Hogar (SIPO) 93.5 %; retiro_mensual:muy_bajo → Hogar (SIPO) 100.0 %

## S3 · Estado del saldo el mes siguiente

| Prueba | Pesos por clase | Sobremuestreo 50/50 |
| :--- | :---: | :---: |
| Prueba original: exactitud balanceada | 68.4 % | 67.5 % |
| A. Parecidos (ruido 5 %): exactitud balanceada | 68.1 % | 67.4 % |
| A. Parecidos: predicciones que no cambian | 98.5 % | 97.5 % |
| B. Nunca vistos: casos | 5,000 | 5,000 |
| B. Nunca vistos: exactitud | 58.7 % | 59.9 % |
| B. Nunca vistos: exactitud balanceada | 58.7 % | 59.9 % |
| B. Nunca vistos: sensibilidad por clase (— = sin casos) | 39.3 % · 78.2 % · — | 54.4 % · 65.5 % · — |
| Prueba original: sensibilidad por clase | 36.0 % · 80.5 % · 88.7 % | 48.5 % · 66.8 % · 87.3 % |
| C. Casos en frontera (margen < 10 pts) | 30.6 % (1,816) | 31.7 % (1,885) |
| C. Acierto en frontera / fuera | 51.1 % / 63.0 % | 51.8 % / 64.2 % |
| C. Clase real entre las dos más probables | 98.4 % | 99.2 % |
| D. Característica más influyente (peso relativo) | saldo_fin_mes (26.1 %) | saldo_promedio_mes (31.9 %) |
| F. Proporción real de meses: casos | 87,170 | 87,170 |
| F. Proporción real: exactitud / balanceada de la red | 54.4 % / 68.7 % | 57.9 % / 68.4 % |
| F. Proporción real: "siempre estable" (exactitud) | 60.7 % | 60.7 % |
| F. Proporción real: sensibilidad por clase | 38.6 % · 78.7 % · 88.7 % | 53.7 % · 64.3 % · 87.3 % |

**D. Importancia por permutación (pesos por clase):** saldo_fin_mes +10.8 · saldo_promedio_mes +9.5 · saldo_min_mes +6.9 · num_movimientos_mes +4.0 · monto_medio_mov +3.5 (puntos de exactitud balanceada que se pierden al desordenarla)
**D. Extremos sintéticos (pesos por clase):** saldo_fin_mes:muy_alto → Caída de saldo sin sobregiro 100.0 %; saldo_fin_mes:muy_bajo → Sobregiro 100.0 %; saldo_promedio_mes:muy_bajo → Sobregiro 100.0 %; saldo_min_mes:muy_bajo → Sobregiro 97.2 %; saldo_max_mes:muy_alto → Caída de saldo sin sobregiro 100.0 %; cambio_saldo_mes:muy_alto → Sobregiro 93.8 %; cambio_saldo_mes:muy_bajo → Sobregiro 100.0 %; monto_medio_mov:muy_alto → Sobregiro 98.0 %; monto_medio_mov:muy_bajo → Saldo estable o creciente 95.5 %

**D. Importancia por permutación (sobremuestreo):** saldo_promedio_mes +16.5 · saldo_fin_mes +11.9 · saldo_min_mes +7.5 · monto_medio_mov +5.0 · num_movimientos_mes +3.7 (puntos de exactitud balanceada que se pierden al desordenarla)
**D. Extremos sintéticos (sobremuestreo):** saldo_fin_mes:muy_alto → Caída de saldo sin sobregiro 100.0 %; saldo_fin_mes:muy_bajo → Sobregiro 100.0 %; saldo_promedio_mes:muy_alto → Caída de saldo sin sobregiro 93.4 %; saldo_promedio_mes:muy_bajo → Sobregiro 100.0 %; saldo_min_mes:muy_alto → Saldo estable o creciente 100.0 %; saldo_min_mes:muy_bajo → Sobregiro 98.6 %; cambio_saldo_mes:muy_bajo → Sobregiro 99.7 %; monto_medio_mov:muy_alto → Sobregiro 98.6 %

## S4 · Mora al corte (31/12/1998) de un préstamo

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
**D. Extremos sintéticos (pesos por clase):** monto_prestamo:muy_alto → En mora o impago al corte (B o D) 99.3 %; monto_prestamo:muy_bajo → Al día al corte (A o C) 100.0 %; plazo_meses:muy_alto → Al día al corte (A o C) 99.3 %; saldo_promedio_previo:muy_alto → Al día al corte (A o C) 100.0 %; saldo_promedio_previo:muy_bajo → En mora o impago al corte (B o D) 100.0 %; saldo_minimo_previo:muy_alto → Al día al corte (A o C) 100.0 %; saldo_minimo_previo:muy_bajo → En mora o impago al corte (B o D) 100.0 %; ingreso_mensual:muy_alto → Al día al corte (A o C) 91.2 %; movimientos_mes:muy_alto → Al día al corte (A o C) 98.5 %; meses_historial:muy_alto → Al día al corte (A o C) 90.4 %

**D. Importancia por permutación (sobremuestreo):** saldo_minimo_previo +14.2 · monto_prestamo +13.5 · es_mujer +3.8 · meses_historial +3.5 · saldo_promedio_previo +3.5 (puntos de exactitud balanceada que se pierden al desordenarla)
**D. Extremos sintéticos (sobremuestreo):** monto_prestamo:muy_alto → En mora o impago al corte (B o D) 98.5 %; monto_prestamo:muy_bajo → Al día al corte (A o C) 100.0 %; plazo_meses:muy_alto → Al día al corte (A o C) 98.5 %; saldo_promedio_previo:muy_alto → Al día al corte (A o C) 100.0 %; saldo_promedio_previo:muy_bajo → En mora o impago al corte (B o D) 100.0 %; saldo_minimo_previo:muy_alto → Al día al corte (A o C) 100.0 %; saldo_minimo_previo:muy_bajo → En mora o impago al corte (B o D) 100.0 %; ingreso_mensual:muy_bajo → Al día al corte (A o C) 97.8 %; egreso_mensual:muy_alto → En mora o impago al corte (B o D) 97.1 %; egreso_mensual:muy_bajo → Al día al corte (A o C) 97.1 %; movimientos_mes:muy_bajo → En mora o impago al corte (B o D) 95.6 %; meses_historial:muy_alto → Al día al corte (A o C) 97.8 %
