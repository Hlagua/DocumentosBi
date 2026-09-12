-- ==============================================================================
-- SCRIPT DE CORRECCIONES PARA EL MODELO KIMBALL (DM_Financial_Kimball)
-- Asignatura: Inteligencia de Negocios
-- Caso de Estudio: Banco Comercial Checo (Financial_ijs)
-- Autores: Alison Marcela Cobos Taco / Henry Daniel Lagua Flores
-- ==============================================================================

USE DM_Financial_Kimball;
GO

PRINT 'Iniciando aplicacion de correcciones en DM_Financial_Kimball...';

-- ------------------------------------------------------------------------------
-- 1. CORRECCION DE EDAD EN Dim_Cliente
-- Se calcula la edad referenciada estrictamente a la fecha de corte del dataset
-- (31 de diciembre de 1998) y no con GETDATE(), para no falsear el analisis historico.
-- ------------------------------------------------------------------------------
PRINT '1. Actualizando edad calculada al 31/12/1998 en Dim_Cliente...';

UPDATE Dim_Cliente
SET edad = DATEDIFF(YEAR, fecha_nacimiento, '1998-12-31') - 
           CASE 
               WHEN DATEADD(YEAR, DATEDIFF(YEAR, fecha_nacimiento, '1998-12-31'), fecha_nacimiento) > '1998-12-31' 
               THEN 1 ELSE 0 
           END;

-- ------------------------------------------------------------------------------
-- 2. CORRECCION DE LOGICA INVERTIDA EN etiqueta_buen_pagador
-- En el dataset de benchmark (PKDD 1999 / IJS), goodClient = 1 codificaba la clase
-- de interes/riesgo (Estado B, prestamos en mora/quiebra).
-- Se reasigna:
--   Estado A (Pagado sin problemas)  -> 1 (Buen Pagador)
--   Estado B (Cerrado con deuda)     -> 0 (Moroso / Default)
--   Estados C y D / Sin prestamo     -> NULL
-- ------------------------------------------------------------------------------
PRINT '2. Corrigiendo etiqueta_buen_pagador en Dim_Cliente...';

UPDATE c
SET c.etiqueta_buen_pagador = CASE 
    WHEN ep.codigo_estado = 'A' THEN 1
    WHEN ep.codigo_estado = 'B' THEN 0
    ELSE NULL
END
FROM Dim_Cliente c
INNER JOIN Fact_Prestamos fp ON c.sk_cliente = fp.sk_cliente
INNER JOIN Dim_Estado_Prestamo ep ON fp.sk_estado_prestamo = ep.sk_estado_prestamo;

-- ------------------------------------------------------------------------------
-- 3. HOMOLOGACION LINGUISTICA EN Dim_Operacion (Checo -> Espanol)
-- ------------------------------------------------------------------------------
PRINT '3. Poblando traducciones y canales en Dim_Operacion...';

UPDATE Dim_Operacion
SET tipo_operacion_traducido = CASE 
        WHEN tipo_operacion_original = 'PRIJEM' THEN 'Ingreso / Deposito'
        WHEN tipo_operacion_original = 'VYDAJ' THEN 'Egreso / Gasto'
        WHEN tipo_operacion_original = 'VYBER' THEN 'Retiro en Efectivo'
        ELSE tipo_operacion_original
    END,
    canal = CASE 
        WHEN tipo_operacion_original = 'PRIJEM' THEN 'Ventanilla Bancaria'
        WHEN tipo_operacion_original = 'VYDAJ' THEN 'Compensacion / Ventanilla'
        WHEN tipo_operacion_original = 'VYBER' THEN 'Ventanilla / ATM'
        ELSE 'Canal Electronico'
    END;

-- ------------------------------------------------------------------------------
-- 4. HOMOLOGACION LINGUISTICA EN Dim_Orden (Checo -> Espanol)
-- ------------------------------------------------------------------------------
PRINT '4. Poblando categorias traducidas en Dim_Orden...';

UPDATE Dim_Orden
SET categoria_orden_traducida = CASE 
    WHEN k_symbol_original = 'SIPO' THEN 'Servicios del Hogar'
    WHEN k_symbol_original = 'UVER' THEN 'Cuota de Prestamo'
    WHEN k_symbol_original = 'POJISTNE' THEN 'Seguro'
    WHEN k_symbol_original = 'LEASING' THEN 'Arrendamiento / Leasing'
    WHEN k_symbol_original = '' OR k_symbol_original IS NULL THEN 'Sin Especificar'
    ELSE k_symbol_original
END;

PRINT 'Correcciones aplicadas exitosamente en DM_Financial_Kimball.';
GO
