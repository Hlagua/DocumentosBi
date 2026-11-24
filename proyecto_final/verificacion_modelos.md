# Verificación de las redes neuronales (pesos por clase frente a sobremuestreo)

Pruebas pedidas para la defensa: (A) datos parecidos al dataset, (B) datos que el modelo nunca vio, (C) casos en la frontera de decisión y (D) búsqueda de atajos con importancia por permutación y datos sintéticos extremos. S1 ya estaba balanceado, por eso sus dos columnas usan el mismo modelo.

**Control:** los datos nunca vistos se recalcularon con el mismo procedimiento del dataset. Al recalcular las filas que sí están en el dataset, coinciden exactamente: S1 = True (24,000 filas).

**Partición por cuenta:** en S1 y S2 ninguna cuenta está en dos particiones (en S4 cada fila es una cuenta). Los "nunca vistos" (B) salen solo de cuentas que no se usaron para entrenar ni validar. En S1 son 1057 cuentas, pero no son un grupo de clientes aparte: incluyen las 857 cuentas de la prueba. Por eso en S1 (B) confirma, con otros movimientos de esos mismos clientes, que el resultado de la prueba se sostiene; no demuestra que la red acierte igual en otra población.

(E) compara S2 con una regla de una línea.

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
