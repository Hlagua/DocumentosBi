-- ==============================================================================
-- UNIVERSIDAD TÉCNICA DE AMBATO
-- FACULTAD DE INGENIERÍA EN SISTEMAS ELECTRÓNICA E INDUSTRIAL
-- CARRERA DE SOFTWARE - CICLO ACADÉMICO: AGOSTO 2026 – DICIEMBRE 2026
-- ASIGNATURA: Inteligencia de Negocios
-- DOCENTE: Ing. Ruben Nogales, Mg.
-- AUTORES: Alison Marcela Cobos Taco / Henry Daniel Lagua Flores
-- ==============================================================================
-- ARCHIVO: 01_DDL_Kimball_DM_Financial.sql
-- DESCRIPCIÓN: Estructura física DDL del Data Warehouse Dimensional bajo la 
--              metodología de Ralph Kimball (Data Mart Bus Architecture / 
--              Galaxy Schema) para el caso de estudio Financial_ijs.
-- ==============================================================================

USE master;
GO

-- 1. CREACIÓN DE LA BASE DE DATOS ANALÍTICA KIMBALL
IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = 'DM_Financial_Kimball_v2')
BEGIN
    CREATE DATABASE DM_Financial_Kimball_v2;
    PRINT 'Base de datos DM_Financial_Kimball_v2 creada exitosamente.';
END
GO

USE DM_Financial_Kimball_v2;
GO

-- ==============================================================================
-- 2. DIMENSIONES CONFORMADAS Y CATÁLOGOS ESPECÍFICOS
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- Dim_Tiempo: Calendario Continuo Diario (Conformada)
-- ------------------------------------------------------------------------------
CREATE TABLE Dim_Tiempo (
    sk_tiempo INT IDENTITY(1,1) PRIMARY KEY,
    fecha DATE NOT NULL UNIQUE,
    anio SMALLINT NOT NULL,
    semestre TINYINT NOT NULL,
    trimestre TINYINT NOT NULL,
    mes TINYINT NOT NULL,
    nombre_mes VARCHAR(20) NOT NULL,
    dia TINYINT NOT NULL,
    dia_semana TINYINT NOT NULL,
    nombre_dia VARCHAR(20) NOT NULL,
    es_fin_de_semana BIT NOT NULL
);
GO

-- ------------------------------------------------------------------------------
-- Dim_Distrito: Contexto Geográfico y Socioeconómico (Conformada - SCD Tipo 0)
-- ------------------------------------------------------------------------------
CREATE TABLE Dim_Distrito (
    sk_distrito INT IDENTITY(1,1) PRIMARY KEY,
    id_distrito_bk INT NOT NULL UNIQUE,
    nombre_distrito VARCHAR(50) NOT NULL,
    region VARCHAR(50) NOT NULL,
    poblacion INT NOT NULL,
    salario_promedio DECIMAL(10,2) NULL,
    tasa_desempleo DECIMAL(5,2) NULL,        -- Almacena NULL para '?' del distrito 69
    tasa_criminalidad DECIMAL(10,2) NULL     -- Almacena NULL para '?' del distrito 69
);
GO

-- ------------------------------------------------------------------------------
-- Dim_Cuenta: Catálogo de Cuentas Pasivas (Conformada - SCD Tipo 1)
-- ------------------------------------------------------------------------------
CREATE TABLE Dim_Cuenta (
    sk_cuenta INT IDENTITY(1,1) PRIMARY KEY,
    id_cuenta_bk INT NOT NULL UNIQUE,
    frecuencia_emision_estado VARCHAR(50) NOT NULL,
    fecha_apertura DATE NOT NULL,
    sk_distrito INT NOT NULL,
    CONSTRAINT FK_Dim_Cuenta_Distrito FOREIGN KEY (sk_distrito) 
        REFERENCES Dim_Distrito(sk_distrito)
);
GO

-- ------------------------------------------------------------------------------
-- Dim_Cliente: Perfil Demográfico de Clientes (Conformada - SCD Tipo 1)
-- ------------------------------------------------------------------------------
CREATE TABLE Dim_Cliente (
    sk_cliente INT IDENTITY(1,1) PRIMARY KEY,
    id_cliente_bk INT NOT NULL UNIQUE,
    sexo CHAR(1) NOT NULL,                   -- 'M' o 'F'
    fecha_nacimiento DATE NOT NULL,
    edad_corte INT NULL,                     -- Referenciada al 31/12/1998
    tipo_disposicion VARCHAR(20) NOT NULL,   -- 'OWNER' o 'DISPONENT'
    etiqueta_buen_pagador BIT NULL,          -- 1 = Cumplido (A), 0 = Moroso (B), NULL = Sin evaluar
    sk_distrito INT NOT NULL,
    CONSTRAINT FK_Dim_Cliente_Distrito FOREIGN KEY (sk_distrito) 
        REFERENCES Dim_Distrito(sk_distrito)
);
GO

-- ------------------------------------------------------------------------------
-- Dim_Estado_Prestamo: Catálogo Fijo de Condiciones de Préstamo (SCD Tipo 0)
-- ------------------------------------------------------------------------------
CREATE TABLE Dim_Estado_Prestamo (
    sk_estado_prestamo INT IDENTITY(1,1) PRIMARY KEY,
    codigo_estado CHAR(1) NOT NULL UNIQUE,   -- 'A', 'B', 'C', 'D'
    condicion VARCHAR(20) NOT NULL,          -- 'Vigente', 'Cerrado'
    descripcion VARCHAR(100) NOT NULL        -- 'Pagado sin problemas', 'En mora', etc.
);
GO

-- ------------------------------------------------------------------------------
-- Dim_Operacion: Homologación Lingüística y Canales de Operación (SCD Tipo 0)
-- ------------------------------------------------------------------------------
CREATE TABLE Dim_Operacion (
    sk_operacion INT IDENTITY(1,1) PRIMARY KEY,
    tipo_operacion_original VARCHAR(50) NOT NULL, -- 'PRIJEM', 'VYDAJ', 'VYBER'
    tipo_operacion_traducido VARCHAR(50) NULL,    -- 'Ingreso / Deposito', etc.
    canal VARCHAR(50) NULL                        -- 'Ventanilla', 'ATM', etc.
);
GO

-- ------------------------------------------------------------------------------
-- Dim_Orden: Categoría de Débitos Recurrentes (SCD Tipo 0)
-- ------------------------------------------------------------------------------
CREATE TABLE Dim_Orden (
    sk_orden_tipo INT IDENTITY(1,1) PRIMARY KEY,
    k_symbol_original VARCHAR(50) NOT NULL,       -- 'SIPO', 'UVER', 'LEASING', 'POJISTNE'
    categoria_orden_traducida VARCHAR(100) NULL   -- 'Servicios del Hogar', 'Cuota de Prestamo', etc.
);
GO

-- ==============================================================================
-- 3. TABLAS DE HECHOS (ESQUEMA CONSTELACIÓN - GALAXY SCHEMA)
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- Fact_Prestamos (Grano Atómico: 1 fila por préstamo concedido)
-- ------------------------------------------------------------------------------
CREATE TABLE Fact_Prestamos (
    sk_prestamo INT IDENTITY(1,1) PRIMARY KEY,
    sk_tiempo INT NOT NULL,
    sk_cuenta INT NOT NULL,
    sk_cliente INT NOT NULL,                 -- Enlace exclusivo con titular 'OWNER'
    sk_distrito INT NOT NULL,
    sk_estado_prestamo INT NOT NULL,
    id_prestamo_bk INT NOT NULL,
    monto_prestamo DECIMAL(12,2) NOT NULL,   -- Preservación de centavos
    plazo_meses INT NOT NULL,                -- Atributo numérico no aditivo
    pago_mensual DECIMAL(12,2) NOT NULL,
    saldo_pendiente_estimado DECIMAL(12,2) NULL,
    CONSTRAINT FK_FactPrestamos_Tiempo FOREIGN KEY (sk_tiempo) REFERENCES Dim_Tiempo(sk_tiempo),
    CONSTRAINT FK_FactPrestamos_Cuenta FOREIGN KEY (sk_cuenta) REFERENCES Dim_Cuenta(sk_cuenta),
    CONSTRAINT FK_FactPrestamos_Cliente FOREIGN KEY (sk_cliente) REFERENCES Dim_Cliente(sk_cliente),
    CONSTRAINT FK_FactPrestamos_Distrito FOREIGN KEY (sk_distrito) REFERENCES Dim_Distrito(sk_distrito),
    CONSTRAINT FK_FactPrestamos_Estado FOREIGN KEY (sk_estado_prestamo) REFERENCES Dim_Estado_Prestamo(sk_estado_prestamo)
);
GO

-- ------------------------------------------------------------------------------
-- Fact_Transacciones (Grano Atómico: 1 fila por movimiento contable)
-- ------------------------------------------------------------------------------
CREATE TABLE Fact_Transacciones (
    sk_transaccion BIGINT IDENTITY(1,1) PRIMARY KEY, -- BIGINT para soportar > 1M filas
    sk_tiempo INT NOT NULL,
    sk_cuenta INT NOT NULL,
    sk_cliente INT NOT NULL,
    sk_distrito INT NOT NULL,
    sk_operacion INT NOT NULL,
    id_transaccion_bk INT NOT NULL,
    monto_transaccion DECIMAL(12,2) NOT NULL,
    saldo_cuenta DECIMAL(12,2) NOT NULL,     -- Medida semiaditiva
    CONSTRAINT FK_FactTrans_Tiempo FOREIGN KEY (sk_tiempo) REFERENCES Dim_Tiempo(sk_tiempo),
    CONSTRAINT FK_FactTrans_Cuenta FOREIGN KEY (sk_cuenta) REFERENCES Dim_Cuenta(sk_cuenta),
    CONSTRAINT FK_FactTrans_Cliente FOREIGN KEY (sk_cliente) REFERENCES Dim_Cliente(sk_cliente),
    CONSTRAINT FK_FactTrans_Distrito FOREIGN KEY (sk_distrito) REFERENCES Dim_Distrito(sk_distrito),
    CONSTRAINT FK_FactTrans_Operacion FOREIGN KEY (sk_operacion) REFERENCES Dim_Operacion(sk_operacion)
);
GO

-- ------------------------------------------------------------------------------
-- Fact_Ordenes (Grano Atómico: 1 fila por orden recurrente programada)
-- ------------------------------------------------------------------------------
CREATE TABLE Fact_Ordenes (
    sk_orden INT IDENTITY(1,1) PRIMARY KEY,
    sk_tiempo INT NOT NULL,
    sk_cuenta INT NOT NULL,
    sk_cliente INT NOT NULL,
    sk_distrito INT NOT NULL,
    sk_orden_tipo INT NOT NULL,
    id_orden_bk INT NOT NULL,
    monto_orden DECIMAL(12,2) NOT NULL,      -- DECIMAL(12,2) para evitar desbalance de -$47.40
    CONSTRAINT FK_FactOrdenes_Tiempo FOREIGN KEY (sk_tiempo) REFERENCES Dim_Tiempo(sk_tiempo),
    CONSTRAINT FK_FactOrdenes_Cuenta FOREIGN KEY (sk_cuenta) REFERENCES Dim_Cuenta(sk_cuenta),
    CONSTRAINT FK_FactOrdenes_Cliente FOREIGN KEY (sk_cliente) REFERENCES Dim_Cliente(sk_cliente),
    CONSTRAINT FK_FactOrdenes_Distrito FOREIGN KEY (sk_distrito) REFERENCES Dim_Distrito(sk_distrito),
    CONSTRAINT FK_FactOrdenes_OrdenTipo FOREIGN KEY (sk_orden_tipo) REFERENCES Dim_Orden(sk_orden_tipo)
);
GO

PRINT 'Esquema dimensional Ralph Kimball estructurado e indexado exitosamente.';
GO
