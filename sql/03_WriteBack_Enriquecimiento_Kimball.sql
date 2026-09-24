-- ==============================================================================
-- UNIVERSIDAD TÉCNICA DE AMBATO
-- FACULTAD DE INGENIERÍA EN SISTEMAS ELECTRÓNICA E INDUSTRIAL
-- CARRERA DE SOFTWARE - CICLO ACADÉMICO: AGOSTO 2026 – DICIEMBRE 2026
-- ASIGNATURA: Inteligencia de Negocios
-- DOCENTE: Ing. Ruben Nogales, Mg.
-- AUTORES: Alison Marcela Cobos Taco / Henry Daniel Lagua Flores
-- ==============================================================================
-- ARCHIVO: 03_WriteBack_Enriquecimiento_Kimball.sql
-- DESCRIPCIÓN: Procedimiento de retroalimentación analítica (Write-Back)
--              para devolver datos limpios, imputados y perfiles a SQL Server.
-- ==============================================================================

USE DM_Financial_Kimball_v2;
GO

-- 1. ACTUALIZACIÓN Y TRAZABILIDAD EN Dim_Distrito
IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('Dim_Distrito') AND name = 'es_imputado')
BEGIN
    ALTER TABLE Dim_Distrito ADD es_imputado BIT NOT NULL DEFAULT 0;
    ALTER TABLE Dim_Distrito ADD metodo_imputacion VARCHAR(50) NULL;
    ALTER TABLE Dim_Distrito ADD fecha_enriquecimiento DATETIME NULL;
END
GO

-- Inicializar auditoría para distritos históricos
UPDATE Dim_Distrito
SET es_imputado = 0,
    metodo_imputacion = 'Original PKDD99',
    fecha_enriquecimiento = GETDATE()
WHERE id_distrito_bk <> 69;
GO

-- Imputar valores científicos calculados mediante K-Means para el Distrito 69 (Jesenik)
UPDATE Dim_Distrito
SET tasa_desempleo = 5.00,
    tasa_criminalidad = 3736.00,
    es_imputado = 1,
    metodo_imputacion = 'K-Means Clustered',
    fecha_enriquecimiento = GETDATE()
WHERE id_distrito_bk = 69;
GO

-- 2. HOMOLOGACIÓN CATEGÓRICA EN Dim_Orden
UPDATE Dim_Orden
SET k_symbol_original = 'SIN_ESPECIFICAR',
    categoria_orden_traducida = 'Sin Especificar'
WHERE k_symbol_original = '' OR k_symbol_original IS NULL;
GO

-- 3. COLUMNAS DE PERFIL Y SEGMENTACIÓN EN Dim_Cliente
IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('Dim_Cliente') AND name = 'arquetipo_demografico')
BEGIN
    ALTER TABLE Dim_Cliente ADD macro_region VARCHAR(20) NULL;
    ALTER TABLE Dim_Cliente ADD segmento_edad VARCHAR(30) NULL;
    ALTER TABLE Dim_Cliente ADD arquetipo_demografico VARCHAR(50) NULL;
    ALTER TABLE Dim_Cliente ADD tiene_prestamo BIT NOT NULL DEFAULT 0;
    ALTER TABLE Dim_Cliente ADD total_ordenes_activas INT NOT NULL DEFAULT 0;
    ALTER TABLE Dim_Cliente ADD saldo_promedio DECIMAL(12,2) NULL;
    ALTER TABLE Dim_Cliente ADD calificacion_pago_desc VARCHAR(20) NOT NULL DEFAULT 'Sin evaluar';
    ALTER TABLE Dim_Cliente ADD fecha_enriquecimiento DATETIME NULL;
END
GO

-- Homologar calificacion_pago_desc segun etiqueta_buen_pagador
UPDATE Dim_Cliente
SET calificacion_pago_desc = CASE 
    WHEN etiqueta_buen_pagador = 1 THEN 'Buen Pagador'
    WHEN etiqueta_buen_pagador = 0 THEN 'Mal Pagador'
    ELSE 'Sin evaluar'
END;
GO

PRINT 'Estructura dimensional preparada y enriquecida para Closed-Loop BI.';
GO
