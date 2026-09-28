-- ==============================================================================
-- UNIVERSIDAD TÉCNICA DE AMBATO
-- FACULTAD DE INGENIERÍA EN SISTEMAS ELECTRÓNICA E INDUSTRIAL
-- CARRERA DE SOFTWARE - CICLO ACADÉMICO: AGOSTO 2026 – DICIEMBRE 2026
-- ASIGNATURA: Inteligencia de Negocios
-- DOCENTE: Ing. Ruben Nogales, Mg.
-- AUTORES: Alison Marcela Cobos Taco / Henry Daniel Lagua Flores
-- ==============================================================================
-- ARCHIVO: 04_Vistas_PowerBI_Kimball.sql
-- DESCRIPCIÓN: Vistas de apoyo para el Dashboard articulado de Power BI
--              (Dashboard_Financial_Kimball.pbix). Ver guía 07.
--   1. vw_PBI_Saldo_Final_Cuenta     -> medida SEMIADITIVA (último saldo por cuenta)
--   2. vw_PBI_Trans_Anual_Cuenta     -> agregado anual de Fact_Transacciones
--                                       (1,056,320 filas -> ~54,298 filas)
-- Las tablas Fact_* y Dim_* se importan directamente; estas vistas solo
-- resuelven lo que no se debe calcular sumando filas atómicas.
-- ==============================================================================

USE DM_Financial_Kimball_v2;
GO

-- ------------------------------------------------------------------------------
-- 1. SALDO FINAL POR CUENTA (Semiaditiva)
--    El saldo NO se suma en el tiempo: se toma la última transacción de cada
--    cuenta (fecha más reciente; desempate por id de transacción).
--    Control: SUM(saldo_final) = 197,140,434.00
-- ------------------------------------------------------------------------------
CREATE OR ALTER VIEW dbo.vw_PBI_Saldo_Final_Cuenta AS
SELECT
    x.sk_cuenta,
    x.sk_cliente,
    x.sk_distrito,
    x.fecha_ultimo_movimiento,
    x.saldo_final
FROM (
    SELECT
        f.sk_cuenta,
        f.sk_cliente,
        f.sk_distrito,
        t.fecha AS fecha_ultimo_movimiento,
        f.saldo_cuenta AS saldo_final,
        ROW_NUMBER() OVER (
            PARTITION BY f.sk_cuenta
            ORDER BY t.fecha DESC, f.id_transaccion_bk DESC
        ) AS rn
    FROM Fact_Transacciones f
    JOIN Dim_Tiempo t ON t.sk_tiempo = f.sk_tiempo
) x
WHERE x.rn = 1;
GO

-- ------------------------------------------------------------------------------
-- 2. TRANSACCIONES AGREGADAS POR CUENTA, AÑO Y OPERACIÓN
--    Mantiene todas las claves del hecho para que los filtros cruzados y el
--    drill-through (Región -> Distrito -> Cliente) sigan funcionando.
--    Incluye suma de cuadrados para calcular la desviación estándar exacta
--    en DAX sin volver al grano atómico.
--    Control: SUM(monto_total) = 6,257,862,197.00 ; SUM(num_transacciones) = 1,056,320
-- ------------------------------------------------------------------------------
CREATE OR ALTER VIEW dbo.vw_PBI_Trans_Anual_Cuenta AS
SELECT
    f.sk_cuenta,
    f.sk_cliente,
    f.sk_distrito,
    f.sk_operacion,
    t.anio,
    COUNT_BIG(*)                                        AS num_transacciones,
    SUM(CAST(f.monto_transaccion AS DECIMAL(18,2)))     AS monto_total,
    SUM(CAST(f.monto_transaccion AS FLOAT) * f.monto_transaccion) AS suma_cuadrados,
    AVG(CAST(f.saldo_cuenta AS DECIMAL(18,2)))          AS saldo_promedio
FROM Fact_Transacciones f
JOIN Dim_Tiempo t ON t.sk_tiempo = f.sk_tiempo
GROUP BY f.sk_cuenta, f.sk_cliente, f.sk_distrito, f.sk_operacion, t.anio;
GO

-- ------------------------------------------------------------------------------
-- 3. CONSULTAS DE CONTROL (ejecutar antes de abrir Power BI)
-- ------------------------------------------------------------------------------
SELECT 'Saldo total depósitos' AS control, SUM(saldo_final) AS valor, 197140434.00 AS esperado
FROM dbo.vw_PBI_Saldo_Final_Cuenta
UNION ALL
SELECT 'Volumen transaccionado', SUM(monto_total), 6257862197.00
FROM dbo.vw_PBI_Trans_Anual_Cuenta
UNION ALL
SELECT 'Número de transacciones', SUM(num_transacciones), 1056320
FROM dbo.vw_PBI_Trans_Anual_Cuenta;
GO
