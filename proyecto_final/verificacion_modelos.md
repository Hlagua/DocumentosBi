# Verificación de las redes neuronales (pesos por clase frente a sobremuestreo)

Pruebas pedidas para la defensa: (A) datos parecidos al dataset, (B) datos que el modelo nunca vio, (C) casos en la frontera de decisión y (D) búsqueda de atajos con importancia por permutación y datos sintéticos extremos. S1 ya estaba balanceado, por eso sus dos columnas usan el mismo modelo.

**Control:** los datos nunca vistos se recalcularon con el mismo procedimiento del dataset. Al recalcular las filas que sí están en el dataset, coinciden exactamente: S1 = True (24,000 filas), S3 = True (4,708 filas).

**Partición por cuenta:** en S1, S2 y S3 ninguna cuenta está en dos particiones. Los "nunca vistos" (B) salen solo de cuentas que no se usaron para entrenar ni validar (S1: 1057 cuentas; S3: 2431 cuentas), pero no son un grupo de clientes aparte: incluyen las cuentas de la prueba (S1: 857 de las 1057). Por eso (B) confirma, con otros movimientos de esos mismos clientes, que el resultado de la prueba se sostiene; no demuestra que la red acierte igual en otra población.

(E) compara S2 con una regla de una línea. (F) evalúa S3 con la proporción real de meses del banco. Los 142 sobregiros de (F) son exactamente los mismos de la prueba, porque todos los sobregiros del banco ya estaban en el dataset; la sensibilidad de sobregiro en (F) repite la de la prueba y no es una medida nueva. Lo nuevo de (F) es la exactitud global frente a "siempre estable", porque casi todos esos meses estables y de caída no están en la prueba.

## S1 · Tipo de transacción

| Prueba | Pesos por clase | Sobremuestreo 50/50 |
| :--- | :---: | :---: |
| Prueba original: exactitud balanceada | 76.9 % | 76.9 % |
| A. Parecidos (ruido 5 %): exactitud balanceada | 74.5 % | 74.5 % |
| A. Parecidos: predicciones que no cambian | 93.9 % | 93.9 % |
| B. Nunca vistos: casos | 10,000 | 10,000 |
| B. Nunca vistos: exactitud | 76.2 % | 76.2 % |
| B. Nunca vistos: exactitud balanceada | 76.2 % | 76.2 % |
| B. Nunca vistos: sensibilidad por clase (— = sin casos) | 61.4 % · 69.5 % · 86.4 % · 87.8 % | 61.4 % · 69.5 % · 86.4 % · 87.8 % |
| Prueba original: sensibilidad por clase | 63.2 % · 70.1 % · 87.0 % · 87.5 % | 63.2 % · 70.1 % · 87.0 % · 87.5 % |
| C. Casos en frontera (margen < 10 pts) | 7.5 % (1,104) | 7.5 % (1,104) |
| C. Acierto en frontera / fuera | 47.5 % / 78.8 % | 47.5 % / 78.8 % |
| C. Clase real entre las dos más probables | 90.4 % | 90.4 % |
| D. Característica más influyente (peso relativo) | monto (39.2 %) | monto (39.2 %) |

**D. Importancia por permutación (pesos por clase):** monto +30.6 · dia +26.7 · edad +13.3 · saldo_despues +5.5 · es_mujer +0.7 (puntos de exactitud balanceada que se pierden al desordenarla)
**D. Extremos sintéticos (pesos por clase):** ningún valor extremo manda el 90 % de los casos a una sola clase

**D. Importancia por permutación (sobremuestreo):** monto +30.6 · dia +26.7 · edad +13.3 · saldo_despues +5.5 · es_mujer +0.7 (puntos de exactitud balanceada que se pierden al desordenarla)
**D. Extremos sintéticos (sobremuestreo):** ningún valor extremo manda el 90 % de los casos a una sola clase

## S2 · Propósito de la orden permanente

| Prueba | Pesos por clase | Sobremuestreo 50/50 |
| :--- | :---: | :---: |
| Prueba original: exactitud balanceada | 85.3 % | 85.4 % |
| A. Parecidos (ruido 5 %): exactitud balanceada | 85.0 % | 85.2 % |
| A. Parecidos: predicciones que no cambian | 99.0 % | 98.6 % |
| B. Nunca vistos | no hay datos reales sin usar | no hay datos reales sin usar |
| C. Casos en frontera (margen < 10 pts) | 5.0 % (51) | 2.5 % (25) |
| C. Acierto en frontera / fuera | 37.2 % / 83.5 % | 28.0 % / 83.6 % |
| C. Clase real entre las dos más probables | 92.2 % | 80.0 % |
| D. Característica más influyente (peso relativo) | monto_orden (27.8 %) | monto_orden (29.7 %) |
| E. Regla de una línea (monto = cuota → préstamo; si no, hogar): exactitud / balanceada | 81.6 % / 47.7 % | 81.6 % / 47.7 % |
| E. Red neuronal en la misma prueba: exactitud / balanceada | 81.1 % / 85.3 % | 82.2 % / 85.4 % |
| E. Sensibilidad de la regla por clase | 100.0 % · 91.0 % · 0.0 % · 0.0 % | 100.0 % · 91.0 % · 0.0 % · 0.0 % |

**D. Importancia por permutación (pesos por clase):** monto_orden +32.4 · tiene_prestamo +24.8 · cuota_prestamo +22.5 · ordenes_activas_cuenta +19.5 · retiro_mensual +14.1 (puntos de exactitud balanceada que se pierden al desordenarla)
**D. Extremos sintéticos (pesos por clase):** monto_orden:muy_alto → Hogar (SIPO) 100.0 %; retiro_mensual:muy_bajo → Hogar (SIPO) 97.4 %

**D. Importancia por permutación (sobremuestreo):** monto_orden +34.9 · tiene_prestamo +24.6 · cuota_prestamo +21.2 · ordenes_activas_cuenta +17.6 · retiro_mensual +13.3 (puntos de exactitud balanceada que se pierden al desordenarla)
**D. Extremos sintéticos (sobremuestreo):** monto_orden:muy_alto → Hogar (SIPO) 100.0 %; edad:muy_alto → Hogar (SIPO) 93.1 %; deposito_mensual:muy_alto → Hogar (SIPO) 90.6 %; retiro_mensual:muy_bajo → Hogar (SIPO) 95.4 %

## S3 · Estado del saldo el mes siguiente

| Prueba | Pesos por clase | Sobremuestreo 50/50 |
| :--- | :---: | :---: |
| Prueba original: exactitud balanceada | 67.4 % | 67.5 % |
| A. Parecidos (ruido 5 %): exactitud balanceada | 67.5 % | 67.4 % |
| A. Parecidos: predicciones que no cambian | 98.7 % | 97.5 % |
| B. Nunca vistos: casos | 5,000 | 5,000 |
| B. Nunca vistos: exactitud | 59.1 % | 59.9 % |
| B. Nunca vistos: exactitud balanceada | 59.1 % | 59.9 % |
| B. Nunca vistos: sensibilidad por clase (— = sin casos) | 46.2 % · 72.0 % · — | 54.4 % · 65.5 % · — |
| Prueba original: sensibilidad por clase | 42.5 % · 73.0 % · 86.6 % | 48.5 % · 66.8 % · 87.3 % |
| C. Casos en frontera (margen < 10 pts) | 26.4 % (1,571) | 31.7 % (1,885) |
| C. Acierto en frontera / fuera | 49.4 % / 63.2 % | 51.8 % / 64.2 % |
| C. Clase real entre las dos más probables | 98.7 % | 99.2 % |
| D. Característica más influyente (peso relativo) | saldo_min_mes (35.3 %) | saldo_promedio_mes (31.9 %) |
| F. Proporción real de meses: casos | 87,170 | 87,170 |
| F. Proporción real: exactitud / balanceada de la red | 56.6 % / 68.5 % | 57.9 % / 68.4 % |
| F. Proporción real: "siempre estable" (exactitud) | 60.7 % | 60.7 % |
| F. Proporción real: sensibilidad por clase | 46.3 % · 72.4 % · 86.6 % | 53.7 % · 64.3 % · 87.3 % |

**D. Importancia por permutación (pesos por clase):** saldo_min_mes +14.3 · saldo_fin_mes +8.5 · saldo_promedio_mes +6.8 · num_movimientos_mes +4.1 · monto_medio_mov +3.4 (puntos de exactitud balanceada que se pierden al desordenarla)
**D. Extremos sintéticos (pesos por clase):** saldo_fin_mes:muy_bajo → Sobregiro 100.0 %; saldo_promedio_mes:muy_bajo → Sobregiro 100.0 %; saldo_min_mes:muy_bajo → Sobregiro 100.0 %; saldo_max_mes:muy_alto → Caída de saldo sin sobregiro 98.9 %; cambio_saldo_mes:muy_bajo → Sobregiro 96.3 %; monto_medio_mov:muy_alto → Sobregiro 97.7 %; monto_medio_mov:muy_bajo → Saldo estable o creciente 99.6 %

**D. Importancia por permutación (sobremuestreo):** saldo_promedio_mes +16.5 · saldo_fin_mes +11.9 · saldo_min_mes +7.5 · monto_medio_mov +5.0 · num_movimientos_mes +3.7 (puntos de exactitud balanceada que se pierden al desordenarla)
**D. Extremos sintéticos (sobremuestreo):** saldo_fin_mes:muy_alto → Caída de saldo sin sobregiro 100.0 %; saldo_fin_mes:muy_bajo → Sobregiro 100.0 %; saldo_promedio_mes:muy_alto → Caída de saldo sin sobregiro 93.4 %; saldo_promedio_mes:muy_bajo → Sobregiro 100.0 %; saldo_min_mes:muy_alto → Saldo estable o creciente 100.0 %; saldo_min_mes:muy_bajo → Sobregiro 98.6 %; cambio_saldo_mes:muy_bajo → Sobregiro 99.7 %; monto_medio_mov:muy_alto → Sobregiro 98.6 %

## S4 · Mora al corte (31/12/1998) de un préstamo

| Prueba | Pesos por clase | Sobremuestreo 50/50 |
| :--- | :---: | :---: |
| Prueba original: exactitud balanceada | 81.7 % | 68.4 % |
| A. Parecidos (ruido 5 %): exactitud balanceada | 79.3 % | 70.5 % |
| A. Parecidos: predicciones que no cambian | 97.5 % | 98.5 % |
| B. Nunca vistos | no hay datos reales sin usar | no hay datos reales sin usar |
| C. Casos en frontera (margen < 10 pts) | 4.4 % (6) | 2.2 % (3) |
| C. Acierto en frontera / fuera | 50.0 % / 84.6 % | 0.0 % / 87.2 % |
| C. Clase real entre las dos más probables | 100.0 % | 100.0 % |
| D. Característica más influyente (peso relativo) | saldo_minimo_previo (25.6 %) | saldo_minimo_previo (52.1 %) |

**D. Importancia por permutación (pesos por clase):** saldo_minimo_previo +22.6 · monto_prestamo +18.9 · tasa_desempleo +8.0 · saldo_promedio_previo +6.3 · plazo_meses +6.0 (puntos de exactitud balanceada que se pierden al desordenarla)
**D. Extremos sintéticos (pesos por clase):** monto_prestamo:muy_alto → En mora o impago al corte (B o D) 98.5 %; monto_prestamo:muy_bajo → Al día al corte (A o C) 100.0 %; plazo_meses:muy_alto → Al día al corte (A o C) 98.5 %; saldo_promedio_previo:muy_alto → Al día al corte (A o C) 99.3 %; saldo_promedio_previo:muy_bajo → En mora o impago al corte (B o D) 100.0 %; saldo_minimo_previo:muy_alto → Al día al corte (A o C) 100.0 %; saldo_minimo_previo:muy_bajo → En mora o impago al corte (B o D) 100.0 %; movimientos_mes:muy_alto → Al día al corte (A o C) 97.1 %; movimientos_mes:muy_bajo → En mora o impago al corte (B o D) 97.1 %; meses_historial:muy_alto → Al día al corte (A o C) 99.3 %

**D. Importancia por permutación (sobremuestreo):** saldo_minimo_previo +10.8 · monto_prestamo +6.0 · meses_historial +2.5 · tasa_desempleo +1.4 · salario_promedio -0.2 (puntos de exactitud balanceada que se pierden al desordenarla)
**D. Extremos sintéticos (sobremuestreo):** monto_prestamo:muy_alto → En mora o impago al corte (B o D) 96.3 %; monto_prestamo:muy_bajo → Al día al corte (A o C) 100.0 %; plazo_meses:muy_alto → En mora o impago al corte (B o D) 96.3 %; saldo_promedio_previo:muy_bajo → En mora o impago al corte (B o D) 100.0 %; saldo_minimo_previo:muy_alto → Al día al corte (A o C) 100.0 %; saldo_minimo_previo:muy_bajo → En mora o impago al corte (B o D) 100.0 %; movimientos_mes:muy_alto → Al día al corte (A o C) 94.8 %; meses_historial:muy_alto → Al día al corte (A o C) 97.1 %; edad:muy_alto → En mora o impago al corte (B o D) 97.1 %
