-- ==============================================================================
-- UNIVERSIDAD TÉCNICA DE AMBATO
-- FACULTAD DE INGENIERÍA EN SISTEMAS ELECTRÓNICA E INDUSTRIAL
-- CARRERA DE SOFTWARE - CICLO ACADÉMICO: AGOSTO 2026 – DICIEMBRE 2026
-- ASIGNATURA: Inteligencia de Negocios
-- DOCENTE: Ing. Ruben Nogales, Mg.
-- AUTORES: Alison Marcela Cobos Taco / Henry Daniel Lagua Flores
-- ==============================================================================
-- ARCHIVO: 02_DDL_Inmon_EDW_Financial.sql
-- DESCRIPCIÓN: Estructura física DDL del Enterprise Data Warehouse (EDW) 
--              corporativo bajo la metodología de Bill Inmon (Corporate 
--              Information Factory - CIF).
--              - Repositorio central en Tercera Forma Normal (3FN).
--              - Organizado por áreas de negocio (Subject Areas).
--              - Mapeo y derivación de Data Marts departamentales en vistas.
-- ==============================================================================

USE master;
GO

-- 1. CREACIÓN DE LA BASE DE DATOS CORPORATIVA INMON
IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = 'EDW_Financial_Inmon')
BEGIN
    CREATE DATABASE EDW_Financial_Inmon;
    PRINT 'Base de datos EDW_Financial_Inmon creada exitosamente.';
END
GO

USE EDW_Financial_Inmon;
GO

-- ==============================================================================
-- 2. DOMINIO 1: CONTEXTO GEOGRÁFICO Y SOCIOECONÓMICO (DISTRICTS)
-- ==============================================================================

CREATE TABLE EDW_Distrito (
    id_distrito INT PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL,
    region VARCHAR(50) NOT NULL,
    poblacion INT NOT NULL,
    salario_promedio DECIMAL(10,2) NULL,
    tasa_desempleo DECIMAL(5,2) NULL,        -- Maneja '?' como NULL
    tasa_criminalidad DECIMAL(10,2) NULL     -- Maneja '?' como NULL
);
GO

-- ==============================================================================
-- 2. DOMINIO 2: SUJETOS / CLIENTES (CLIENTS, DISPS, TKEYS)
-- ==============================================================================

-- Entidad de Clientes (Perfil Demográfico Normalizado)
CREATE TABLE EDW_Cliente (
    id_cliente INT PRIMARY KEY,
    fecha_nacimiento DATE NOT NULL,
    sexo CHAR(1) NOT NULL,                   -- 'M' o 'F'
    edad_corte INT NULL,                     -- Referenciada al 31/12/1998
    id_distrito INT NOT NULL,
    CONSTRAINT FK_EDW_Cliente_Distrito FOREIGN KEY (id_distrito) 
        REFERENCES EDW_Distrito(id_distrito)
);
GO

-- ==============================================================================
-- 3. DOMINIO 3: CONTRATOS Y CUENTAS (ACCOUNTS, CARDS)
-- ==============================================================================

-- Entidad de Cuentas Pasivas
CREATE TABLE EDW_Cuenta (
    id_cuenta INT PRIMARY KEY,
    frecuencia VARCHAR(50) NOT NULL,
    fecha_apertura DATE NOT NULL,
    id_distrito INT NOT NULL,
    CONSTRAINT FK_EDW_Cuenta_Distrito FOREIGN KEY (id_distrito) 
        REFERENCES EDW_Distrito(id_distrito)
);
GO

-- Entidad Asociativa Disposición (Resuelve relación M:N entre Cliente y Cuenta)
CREATE TABLE EDW_Disposicion (
    id_disposicion INT PRIMARY KEY,
    id_cliente INT NOT NULL,
    id_cuenta INT NOT NULL,
    tipo_disposicion VARCHAR(20) NOT NULL,   -- 'OWNER' o 'DISPONENT'
    CONSTRAINT FK_EDW_Disp_Cliente FOREIGN KEY (id_cliente) 
        REFERENCES EDW_Cliente(id_cliente),
    CONSTRAINT FK_EDW_Disp_Cuenta FOREIGN KEY (id_cuenta) 
        REFERENCES EDW_Cuenta(id_cuenta)
);
GO

-- Entidad de Medios de Disposición / Tarjetas Plásticas
CREATE TABLE EDW_Tarjeta (
    id_tarjeta INT PRIMARY KEY,
    id_disposicion INT NOT NULL,
    tipo_tarjeta VARCHAR(20) NOT NULL,       -- 'classic', 'junior', 'gold'
    fecha_emision DATE NOT NULL,
    CONSTRAINT FK_EDW_Tarjeta_Disp FOREIGN KEY (id_disposicion) 
        REFERENCES EDW_Disposicion(id_disposicion)
);
GO

-- ==============================================================================
-- 4. DOMINIO 4: CRÉDITO Y CARTERA (LOANS)
-- ==============================================================================

CREATE TABLE EDW_Prestamo (
    id_prestamo INT PRIMARY KEY,
    id_cuenta INT NOT NULL,
    fecha DATE NOT NULL,
    monto DECIMAL(12,2) NOT NULL,
    plazo INT NOT NULL,
    cuota DECIMAL(12,2) NOT NULL,
    estado CHAR(1) NOT NULL,                 -- 'A', 'B', 'C', 'D'
    CONSTRAINT FK_EDW_Prestamo_Cuenta FOREIGN KEY (id_cuenta) 
        REFERENCES EDW_Cuenta(id_cuenta)
);
GO

-- Entidad de Evaluación Histórica de Crédito (Derivada de tkeys en benchmark)
CREATE TABLE EDW_EtiquetaCliente (
    id_etiqueta INT IDENTITY(1,1) PRIMARY KEY,
    id_cliente INT NOT NULL,
    id_prestamo INT NULL,
    buen_pagador BIT NOT NULL,               -- 1 = Estado A cumplido, 0 = Estado B moroso
    CONSTRAINT FK_EDW_Etiqueta_Cliente FOREIGN KEY (id_cliente) 
        REFERENCES EDW_Cliente(id_cliente),
    CONSTRAINT FK_EDW_Etiqueta_Prestamo FOREIGN KEY (id_prestamo) 
        REFERENCES EDW_Prestamo(id_prestamo)
);
GO

-- ==============================================================================
-- 5. DOMINIO 5: TRANSACCIONALIDAD MONETARIA Y ÓRDENES (TRANS, ORDERS)
-- ==============================================================================

CREATE TABLE EDW_Transaccion (
    id_transaccion BIGINT PRIMARY KEY,
    id_cuenta INT NOT NULL,
    fecha DATE NOT NULL,
    tipo VARCHAR(50) NOT NULL,               -- 'PRIJEM', 'VYDAJ', 'VYBER'
    operacion VARCHAR(50) NULL,              -- 'VKLAD', 'VYBER', 'PREVOD'
    monto DECIMAL(12,2) NOT NULL,
    saldo DECIMAL(12,2) NOT NULL,
    k_symbol VARCHAR(50) NULL,
    banco_destino_hash VARCHAR(64) NULL,     -- Anonimización PII SHA-256
    cuenta_destino_hash VARCHAR(64) NULL,    -- Anonimización PII SHA-256
    CONSTRAINT FK_EDW_Trans_Cuenta FOREIGN KEY (id_cuenta) 
        REFERENCES EDW_Cuenta(id_cuenta)
);
GO

CREATE TABLE EDW_Orden (
    id_orden INT PRIMARY KEY,
    id_cuenta INT NOT NULL,
    banco_destino_hash VARCHAR(64) NULL,     -- Anonimización PII SHA-256
    cuenta_destino_hash VARCHAR(64) NULL,    -- Anonimización PII SHA-256
    monto DECIMAL(12,2) NOT NULL,            -- DECIMAL(12,2) estricto
    k_symbol VARCHAR(50) NULL,               -- 'SIPO', 'UVER', 'LEASING', 'POJISTNE'
    CONSTRAINT FK_EDW_Orden_Cuenta FOREIGN KEY (id_cuenta) 
        REFERENCES EDW_Cuenta(id_cuenta)
);
GO

-- ==============================================================================
-- 6. CAPA DE DATA MARTS DEPARTAMENTALES DERIVADOS (VISTAS ANALÍTICAS EN 3FN)
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- Data Mart Departamental 1: Gestión de Riesgo Crediticio y Cartera
-- ------------------------------------------------------------------------------

-- Vista 1.1: Tasa de Morosidad por Distrito (Préstamos Vigentes C y D)
CREATE VIEW Vista_Mora_Distrito AS
SELECT 
    d.id_distrito,
    d.nombre AS nombre_distrito,
    d.region,
    COUNT(p.id_prestamo) AS total_prestamos_vigentes,
    SUM(CASE WHEN p.estado = 'C' THEN 1 ELSE 0 END) AS prestamos_al_dia,
    SUM(CASE WHEN p.estado = 'D' THEN 1 ELSE 0 END) AS prestamos_en_mora,
    SUM(p.monto) AS saldo_cartera_vigente,
    CAST(
        (CAST(SUM(CASE WHEN p.estado = 'D' THEN 1 ELSE 0 END) AS FLOAT) / 
         NULLIF(COUNT(p.id_prestamo), 0)) * 100 
        AS DECIMAL(5,2)
    ) AS tasa_morosidad_activa_pct
FROM EDW_Distrito d
INNER JOIN EDW_Cuenta c ON d.id_distrito = c.id_distrito
INNER JOIN EDW_Prestamo p ON c.id_cuenta = p.id_cuenta
WHERE p.estado IN ('C', 'D')
GROUP BY d.id_distrito, d.nombre, d.region;
GO

-- Vista 1.2: Calidad Histórica de Cartera (Préstamos Cerrados A y B)
CREATE VIEW Vista_Calidad_Historica AS
SELECT 
    d.id_distrito,
    d.nombre AS nombre_distrito,
    COUNT(p.id_prestamo) AS total_prestamos_cerrados,
    SUM(CASE WHEN p.estado = 'A' THEN 1 ELSE 0 END) AS prestamos_pagados_sin_problema,
    SUM(CASE WHEN p.estado = 'B' THEN 1 ELSE 0 END) AS prestamos_terminados_con_deuda,
    CAST(
        (CAST(SUM(CASE WHEN p.estado = 'B' THEN 1 ELSE 0 END) AS FLOAT) / 
         NULLIF(COUNT(p.id_prestamo), 0)) * 100 
        AS DECIMAL(5,2)
    ) AS tasa_incumplimiento_historico_pct
FROM EDW_Distrito d
INNER JOIN EDW_Cuenta c ON d.id_distrito = c.id_distrito
INNER JOIN EDW_Prestamo p ON c.id_cuenta = p.id_cuenta
WHERE p.estado IN ('A', 'B')
GROUP BY d.id_distrito, d.nombre;
GO

-- ------------------------------------------------------------------------------
-- Data Mart Departamental 2: Operaciones y Liquidez Institucional
-- ------------------------------------------------------------------------------

-- Vista 2.1: Volumen y Flujo Transaccional por Tipo de Movimiento
CREATE VIEW Vista_Volumen_Operaciones AS
SELECT 
    YEAR(t.fecha) AS anio,
    MONTH(t.fecha) AS mes,
    t.tipo AS tipo_operacion,
    t.operacion AS canal_operacion,
    COUNT(t.id_transaccion) AS numero_transacciones,
    SUM(t.monto) AS monto_total_transaccionado,
    AVG(t.monto) AS ticket_promedio
FROM EDW_Transaccion t
GROUP BY YEAR(t.fecha), MONTH(t.fecha), t.tipo, t.operacion;
GO

-- Vista 2.2: Resumen de Órdenes Permanentes de Débito
CREATE VIEW Vista_Ordenes_Recurrentes AS
SELECT 
    ISNULL(o.k_symbol, 'SIN_ESPECIFICAR') AS categoria_orden,
    COUNT(o.id_orden) AS total_ordenes,
    SUM(o.monto) AS monto_total_comprometido,
    AVG(o.monto) AS monto_promedio_orden
FROM EDW_Orden o
GROUP BY o.k_symbol;
GO

PRINT 'Esquema corporativo Bill Inmon (3FN) y Data Marts departamentales creados exitosamente.';
GO
