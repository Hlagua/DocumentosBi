-- ==============================================================================
-- UNIVERSIDAD TÉCNICA DE AMBATO
-- FACULTAD DE INGENIERÍA EN SISTEMAS, ELECTRÓNICA E INDUSTRIAL
-- CARRERA DE SOFTWARE - CICLO ACADÉMICO: AGOSTO 2026 – DICIEMBRE 2026
-- ASIGNATURA: Inteligencia de Negocios
-- DOCENTE: Ing. Ruben Nogales, Mg.
-- AUTORES: Alison Marcela Cobos Taco / Henry Daniel Lagua Flores
-- ==============================================================================
-- ARCHIVO: 04_Vistas_PowerBI_Kimball.sql
-- DESCRIPCIÓN: Vistas optimizadas para el Dashboard en Power BI conectado a
--              DM_Financial_Kimball_v2:
--              1. vw_PBI_Saldo_Final_Cuenta: Resuelve la medida semiaditiva del
--                 saldo final institucional ($197,140,434.00) por cuenta.
--              2. vw_PBI_Trans_Anual_Cuenta: Agrega las 1,056,320 transacciones
--                 por cuenta-año-operación conservando el total de $6,257,862,197.00.
-- ==============================================================================

USE DM_Financial_Kimball_v2;
GO

-- 1. VISTA: Saldo Final por Cuenta (Medida Semiaditiva Institucional)
IF OBJECT_ID('vw_PBI_Saldo_Final_Cuenta', 'V') IS NOT NULL
    DROP VIEW vw_PBI_Saldo_Final_Cuenta;
GO

CREATE VIEW vw_PBI_Saldo_Final_Cuenta AS
WITH UltimaTransaccion AS (
    SELECT 
        sk_cuenta,
        sk_cliente,
        sk_distrito,
        saldo_cuenta AS saldo_final,
        ROW_NUMBER() OVER (
            PARTITION BY sk_cuenta 
            ORDER BY sk_tiempo DESC, sk_transaccion DESC
        ) AS rn
    FROM Fact_Transacciones
)
SELECT 
    sk_cuenta,
    sk_cliente,
    sk_distrito,
    saldo_final
FROM UltimaTransaccion
WHERE rn = 1;
GO

-- 2. VISTA: Transacciones Agregadas Anuales por Cuenta y Operación
IF OBJECT_ID('vw_PBI_Trans_Anual_Cuenta', 'V') IS NOT NULL
    DROP VIEW vw_PBI_Trans_Anual_Cuenta;
GO

CREATE VIEW vw_PBI_Trans_Anual_Cuenta AS
SELECT 
    t.sk_cuenta,
    t.sk_cliente,
    t.sk_distrito,
    t.sk_operacion,
    tm.anio,
    SUM(t.monto_transaccion) AS monto_total,
    COUNT(*) AS num_transacciones,
    AVG(t.saldo_cuenta) AS saldo_promedio,
    SUM(CAST(t.monto_transaccion AS FLOAT) * CAST(t.monto_transaccion AS FLOAT)) AS suma_cuadrados
FROM Fact_Transacciones t
JOIN Dim_Tiempo tm ON t.sk_tiempo = tm.sk_tiempo
GROUP BY 
    t.sk_cuenta,
    t.sk_cliente,
    t.sk_distrito,
    t.sk_operacion,
    tm.anio;
GO

-- 3. CONSULTA DE CONTROL Y VALIDACIÓN
PRINT '==============================================================================';
PRINT 'VALIDACIÓN DE VISTAS EN DM_Financial_Kimball_v2:';
SELECT 'vw_PBI_Saldo_Final_Cuenta' AS Vista, COUNT(*) AS Filas, SUM(saldo_final) AS TotalControl
FROM vw_PBI_Saldo_Final_Cuenta;

SELECT 'vw_PBI_Trans_Anual_Cuenta' AS Vista, COUNT(*) AS Filas, SUM(monto_total) AS TotalControl
FROM vw_PBI_Trans_Anual_Cuenta;
PRINT '==============================================================================';
GO
