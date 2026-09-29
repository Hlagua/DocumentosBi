-- ==============================================================================
-- UNIVERSIDAD TÉCNICA DE AMBATO
-- FACULTAD DE INGENIERÍA EN SISTEMAS ELECTRÓNICA E INDUSTRIAL
-- CARRERA DE SOFTWARE - CICLO ACADÉMICO: AGOSTO 2026 – DICIEMBRE 2026
-- ASIGNATURA: Inteligencia de Negocios
-- DOCENTE: Ing. Ruben Nogales, Mg.
-- AUTORES: Alison Marcela Cobos Taco / Henry Daniel Lagua Flores
-- ==============================================================================
-- ARCHIVO: 04_Vistas_PowerBI_Kimball.sql   (Guía 07 v4)
-- DESCRIPCIÓN: Vista de apoyo para el dashboard de Power BI.
--   vw_PBI_Trans_Anual_Cuenta -> Fact_Transacciones agregado por cuenta, año y
--                                CATEGORÍA ANALÍTICA (4), con suma de cuadrados
--                                para la desviación estándar exacta en DAX.
-- El saldo ya no necesita vista: el dashboard usa la foto mensual
-- Fact_Saldo_Cuenta_Mensual (semiaditiva, sin ambigüedad de desempate).
-- La ejecuta también scripts/31_etl_oltp_a_kimball.py después de cada carga.
-- ==============================================================================

USE DM_Financial_Kimball_v2;
GO

IF OBJECT_ID('dbo.vw_PBI_Saldo_Final_Cuenta', 'V') IS NOT NULL
    DROP VIEW dbo.vw_PBI_Saldo_Final_Cuenta;
GO

-- ------------------------------------------------------------------------------
-- Transacciones agregadas por cuenta, año y categoría analítica
-- Control: SUM(monto_total) = 6,257,862,197.00 ; SUM(num_transacciones) = 1,056,320
-- ------------------------------------------------------------------------------
CREATE OR ALTER VIEW dbo.vw_PBI_Trans_Anual_Cuenta AS
SELECT
    f.sk_cuenta,
    f.sk_cliente,
    f.sk_distrito,
    o.categoria_analitica,
    t.anio,
    COUNT_BIG(*)                                                  AS num_transacciones,
    SUM(CAST(f.monto_transaccion AS DECIMAL(18,2)))               AS monto_total,
    SUM(CAST(f.monto_transaccion AS FLOAT) * f.monto_transaccion) AS suma_cuadrados,
    AVG(CAST(f.saldo_cuenta AS DECIMAL(18,2)))                    AS saldo_promedio
FROM Fact_Transacciones f
JOIN Dim_Tiempo t ON t.sk_tiempo = f.sk_tiempo
JOIN Dim_Operacion o ON o.sk_operacion = f.sk_operacion
GROUP BY f.sk_cuenta, f.sk_cliente, f.sk_distrito, o.categoria_analitica, t.anio;
GO

-- ------------------------------------------------------------------------------
-- Consultas de control (ejecutar antes de abrir Power BI)
-- ------------------------------------------------------------------------------
SELECT 'Volumen transaccionado' AS control, SUM(monto_total) AS valor, 6257862197.00 AS esperado
FROM dbo.vw_PBI_Trans_Anual_Cuenta
UNION ALL
SELECT 'Número de transacciones', SUM(num_transacciones), 1056320
FROM dbo.vw_PBI_Trans_Anual_Cuenta
UNION ALL
SELECT 'Saldo neto al corte (foto dic-1998)', SUM(s.saldo_fin_mes), 197140434.00
FROM Fact_Saldo_Cuenta_Mensual s JOIN Dim_Tiempo t ON t.sk_tiempo = s.sk_mes
WHERE t.anio = 1998 AND t.mes = 12;
GO
