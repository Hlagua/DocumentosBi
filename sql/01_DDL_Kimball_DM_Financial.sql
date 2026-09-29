-- ==============================================================================
-- UNIVERSIDAD TÉCNICA DE AMBATO
-- FACULTAD DE INGENIERÍA EN SISTEMAS ELECTRÓNICA E INDUSTRIAL
-- CARRERA DE SOFTWARE - CICLO ACADÉMICO: AGOSTO 2026 – DICIEMBRE 2026
-- ASIGNATURA: Inteligencia de Negocios
-- DOCENTE: Ing. Ruben Nogales, Mg.
-- AUTORES: Alison Marcela Cobos Taco / Henry Daniel Lagua Flores
-- ==============================================================================
-- ARCHIVO: 01_DDL_Kimball_DM_Financial.sql   (versión alineada con la Carta v8)
-- DESCRIPCIÓN: Estructura física del Data Mart dimensional (Ralph Kimball,
--              esquema en constelación) para Financial_ijs.
--              4 hechos: Fact_Prestamos, Fact_Transacciones,
--                        Fact_Saldo_Cuenta_Mensual (foto periódica), Fact_Ordenes
--              7 dimensiones: Tiempo, Distrito, Cuenta, Cliente (conformadas),
--                             Estado_Prestamo, Operacion, Orden (catálogos)
-- REGLAS DE GRANO (Carta v8, sección 9):
--   * sk_cliente de todos los hechos = titular OWNER de la cuenta.
--   * sk_distrito de todos los hechos = distrito de la CUENTA (accounts.district_id).
--   * Fact_Ordenes no tiene fecha de evento: sk_tiempo_apertura_cuenta es un rol
--     de Dim_Tiempo y no sirve para series temporales de órdenes.
-- ==============================================================================

USE master;
GO

IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = 'DM_Financial_Kimball_v2')
BEGIN
    CREATE DATABASE DM_Financial_Kimball_v2;
    PRINT 'Base de datos DM_Financial_Kimball_v2 creada.';
END
GO

USE DM_Financial_Kimball_v2;
GO

-- ==============================================================================
-- 1. DIMENSIONES CONFORMADAS
-- ==============================================================================

-- Dim_Tiempo: calendario diario continuo 1993-01-01 a 1998-12-31 (2,191 días).
-- El último día de cada mes (es_fin_de_mes = 1) es la fila que usa la foto mensual.
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
    es_fin_de_semana BIT NOT NULL,
    es_fin_de_mes BIT NOT NULL
);
GO

-- Dim_Distrito: 77 distritos (SCD 0). Indicadores de 1995 (A12, A15) y 1996 (A13, A16).
-- El distrito 69 (Jesenik) trae NULL en 1995; se imputa y se marca es_imputado.
CREATE TABLE Dim_Distrito (
    sk_distrito INT IDENTITY(1,1) PRIMARY KEY,
    id_distrito_bk INT NOT NULL UNIQUE,
    nombre_distrito VARCHAR(50) NOT NULL,
    region VARCHAR(50) NOT NULL,
    poblacion INT NOT NULL,
    salario_promedio DECIMAL(10,2) NULL,
    tasa_desempleo DECIMAL(5,2) NULL,             -- 1995 (A12)
    tasa_criminalidad DECIMAL(10,2) NULL,         -- 1995 (A15)
    tasa_desempleo_1996 DECIMAL(5,2) NULL,        -- A13
    tasa_criminalidad_1996 DECIMAL(10,2) NULL,    -- A16
    es_imputado BIT NOT NULL DEFAULT 0,
    metodo_imputacion VARCHAR(50) NULL,
    fecha_enriquecimiento DATETIME NULL
);
GO

-- Dim_Cuenta: 4,500 cuentas (SCD 1). Eje de integración entre procesos (drill-across).
CREATE TABLE Dim_Cuenta (
    sk_cuenta INT IDENTITY(1,1) PRIMARY KEY,
    id_cuenta_bk INT NOT NULL UNIQUE,
    frecuencia_emision_estado VARCHAR(50) NOT NULL,     -- Traducida: 'Extracto mensual', etc.
    fecha_apertura DATE NOT NULL,
    sk_distrito INT NOT NULL,                           -- Distrito de la cuenta
    tiene_credito_externo BIT NOT NULL DEFAULT 0,       -- Orden UVER sin préstamo en loans (35 cuentas)
    monto_credito_externo DECIMAL(12,2) NOT NULL DEFAULT 0,
    CONSTRAINT FK_Dim_Cuenta_Distrito FOREIGN KEY (sk_distrito)
        REFERENCES Dim_Distrito(sk_distrito)
);
GO

-- Dim_Cliente: 5,369 clientes, titulares y cotitulares (SCD 1).
-- sk_distrito es el distrito de RESIDENCIA (difiere del de la cuenta en 409 titulares).
-- Las columnas desde macro_region las agrega el write-back (sql/03, Informe 04).
CREATE TABLE Dim_Cliente (
    sk_cliente INT IDENTITY(1,1) PRIMARY KEY,
    id_cliente_bk INT NOT NULL UNIQUE,
    sexo CHAR(1) NOT NULL,                       -- 'M' o 'F'
    fecha_nacimiento DATE NOT NULL,
    edad_corte INT NULL,                         -- Al 31/12/1998
    tipo_disposicion VARCHAR(20) NOT NULL,       -- 'OWNER' o 'DISPONENT'
    etiqueta_buen_pagador BIT NULL,              -- 1 = préstamo terminó en A, 0 = en B, NULL = sin préstamo cerrado
    sk_distrito INT NOT NULL,                    -- Residencia
    macro_region VARCHAR(20) NULL,
    segmento_edad VARCHAR(30) NULL,
    arquetipo_demografico VARCHAR(50) NULL,
    tiene_prestamo BIT NOT NULL DEFAULT 0,
    total_ordenes_activas INT NOT NULL DEFAULT 0,
    saldo_promedio DECIMAL(12,2) NULL,
    calificacion_pago_desc VARCHAR(20) NOT NULL DEFAULT 'Sin evaluar',
    fecha_enriquecimiento DATETIME NULL,
    CONSTRAINT FK_Dim_Cliente_Distrito FOREIGN KEY (sk_distrito)
        REFERENCES Dim_Distrito(sk_distrito)
);
GO

-- Puente_Cuenta_Cliente: resuelve la relación multivaluada cuenta-cliente (disps).
-- Los hechos se unen solo al titular; esta tabla permite llegar a los 869 cotitulares
-- (Carta v8, sección 9.2). Una fila por cliente: 4,500 OWNER + 869 DISPONENT.
CREATE TABLE Puente_Cuenta_Cliente (
    sk_cuenta INT NOT NULL,
    sk_cliente INT NOT NULL UNIQUE,              -- En la fuente cada cliente tiene una sola cuenta
    tipo_disposicion VARCHAR(20) NOT NULL,       -- OWNER / DISPONENT
    CONSTRAINT PK_Puente_Cuenta_Cliente PRIMARY KEY (sk_cuenta, sk_cliente),
    CONSTRAINT FK_Puente_Cuenta FOREIGN KEY (sk_cuenta) REFERENCES Dim_Cuenta(sk_cuenta),
    CONSTRAINT FK_Puente_Cliente FOREIGN KEY (sk_cliente) REFERENCES Dim_Cliente(sk_cliente)
);
GO

-- ==============================================================================
-- 2. DIMENSIONES DE CATÁLOGO (SCD 0)
-- ==============================================================================

-- Dim_Estado_Prestamo: A, B, C, D.
CREATE TABLE Dim_Estado_Prestamo (
    sk_estado_prestamo INT IDENTITY(1,1) PRIMARY KEY,
    codigo_estado CHAR(1) NOT NULL UNIQUE,
    condicion VARCHAR(20) NOT NULL,              -- 'Vigente' (C, D) / 'Cerrado' (A, B)
    descripcion VARCHAR(100) NOT NULL
);
GO

-- Dim_Operacion: grano = combinación real type + operation + k_symbol normalizado
-- (15 filas, Carta v8 sección 11). NULL y '' se normalizan a 'SIN_ESPECIFICAR'.
CREATE TABLE Dim_Operacion (
    sk_operacion INT IDENTITY(1,1) PRIMARY KEY,
    tipo_original VARCHAR(20) NOT NULL,          -- PRIJEM / VYDAJ / VYBER
    operacion_original VARCHAR(20) NOT NULL,     -- VKLAD, PREVOD Z UCTU, ... o 'SIN_ESPECIFICAR'
    k_symbol_original VARCHAR(20) NOT NULL,      -- UROK, SIPO, ... o 'SIN_ESPECIFICAR'
    tipo_movimiento VARCHAR(20) NOT NULL,        -- Ingreso / Egreso / Retiro
    operacion_traducida VARCHAR(50) NOT NULL,    -- Depósito en efectivo, Transferencia entrante, ...
    concepto_traducido VARCHAR(60) NOT NULL,     -- Pensión, Intereses ganados, ...
    categoria_analitica VARCHAR(40) NOT NULL,    -- 4 valores comunes a Kimball, Mongo y tableros
    CONSTRAINT UQ_Dim_Operacion UNIQUE (tipo_original, operacion_original, k_symbol_original)
);
GO

-- Dim_Orden: propósito de la orden permanente (5 filas).
CREATE TABLE Dim_Orden (
    sk_orden_tipo INT IDENTITY(1,1) PRIMARY KEY,
    k_symbol_original VARCHAR(20) NOT NULL UNIQUE,   -- SIPO, UVER, POJISTNE, LEASING, SIN_ESPECIFICAR
    categoria_orden_traducida VARCHAR(100) NOT NULL
);
GO

-- Dim_Concepto_Movimiento: concepto de cada transacción DESPUÉS de la completitud
-- (Informe 03, scripts 33 y 34). Complementa a Dim_Operacion, que conserva la
-- combinación original de la fuente. metodo_concepto indica si el concepto viene
-- de la fuente o fue inferido (cruce con préstamos / órdenes, regla de canal, residual).
CREATE TABLE Dim_Concepto_Movimiento (
    sk_concepto INT IDENTITY(1,1) PRIMARY KEY,
    codigo_concepto VARCHAR(30) NOT NULL,        -- k_symbol original o inferido (RETIRO_EFECTIVO, ...)
    concepto_traducido VARCHAR(60) NOT NULL,
    metodo_concepto VARCHAR(30) NOT NULL,        -- Fuente / Cruce con prestamos / Cruce con ordenes / Regla de canal / Residual
    tipo_contraparte VARCHAR(40) NOT NULL,       -- Caja propia / Sistema central / Entidad externa (no) registrada
    CONSTRAINT UQ_Dim_Concepto UNIQUE (codigo_concepto, metodo_concepto, tipo_contraparte)
);
GO

-- ==============================================================================
-- 3. TABLAS DE HECHOS
-- ==============================================================================

-- Fact_Prestamos. Grano: un préstamo (682). Hecho de evento (otorgamiento) con
-- estado al corte 31/12/1998.
--   Aditivas:     monto_prestamo, pago_mensual, saldo_pendiente_estimado
--   No aditivas:  plazo_meses, meses_transcurridos_al_corte,
--                 saldo_promedio_previo, ratio_cuota_saldo_previo (se promedian, nunca se suman)
CREATE TABLE Fact_Prestamos (
    sk_prestamo INT IDENTITY(1,1) PRIMARY KEY,
    sk_tiempo INT NOT NULL,                          -- Fecha de otorgamiento
    sk_cuenta INT NOT NULL,
    sk_cliente INT NOT NULL,                         -- Titular OWNER
    sk_distrito INT NOT NULL,                        -- Distrito de la cuenta
    sk_estado_prestamo INT NOT NULL,
    id_prestamo_bk INT NOT NULL UNIQUE,
    monto_prestamo DECIMAL(12,2) NOT NULL,           -- = pago_mensual * plazo_meses en la fuente
    plazo_meses INT NOT NULL,
    pago_mensual DECIMAL(12,2) NOT NULL,
    meses_transcurridos_al_corte INT NOT NULL,       -- Meses entre el mes de otorgamiento y dic-1998
    saldo_pendiente_estimado DECIMAL(12,2) NOT NULL, -- max(0, monto - cuota * min(plazo, meses)); A = 0
    saldo_promedio_previo DECIMAL(12,2) NOT NULL,    -- Promedio de trans.balance antes del otorgamiento
    ratio_cuota_saldo_previo DECIMAL(9,4) NOT NULL,  -- pago_mensual / saldo_promedio_previo
    banda_capacidad VARCHAR(12) NOT NULL,            -- Baja <=5.7% | Media-baja <=9.0% | Media-alta <=12.3% | Alta
    CONSTRAINT FK_FactPrestamos_Tiempo FOREIGN KEY (sk_tiempo) REFERENCES Dim_Tiempo(sk_tiempo),
    CONSTRAINT FK_FactPrestamos_Cuenta FOREIGN KEY (sk_cuenta) REFERENCES Dim_Cuenta(sk_cuenta),
    CONSTRAINT FK_FactPrestamos_Cliente FOREIGN KEY (sk_cliente) REFERENCES Dim_Cliente(sk_cliente),
    CONSTRAINT FK_FactPrestamos_Distrito FOREIGN KEY (sk_distrito) REFERENCES Dim_Distrito(sk_distrito),
    CONSTRAINT FK_FactPrestamos_Estado FOREIGN KEY (sk_estado_prestamo) REFERENCES Dim_Estado_Prestamo(sk_estado_prestamo),
    CONSTRAINT CK_FactPrestamos_Banda CHECK (banda_capacidad IN ('Baja', 'Media-baja', 'Media-alta', 'Alta'))
);
GO

-- Fact_Transacciones. Grano: un movimiento en cuenta (1,056,320). Transaccional.
--   Aditiva: monto_transaccion. Semiaditiva: saldo_cuenta (nunca se suma en el tiempo).
CREATE TABLE Fact_Transacciones (
    sk_transaccion BIGINT IDENTITY(1,1) PRIMARY KEY,
    sk_tiempo INT NOT NULL,
    sk_cuenta INT NOT NULL,
    sk_cliente INT NOT NULL,                         -- Titular OWNER
    sk_distrito INT NOT NULL,                        -- Distrito de la cuenta
    sk_operacion INT NOT NULL,
    id_transaccion_bk INT NOT NULL UNIQUE,           -- Desempate del último saldo del día
    monto_transaccion DECIMAL(12,2) NOT NULL,
    saldo_cuenta DECIMAL(12,2) NOT NULL,
    sk_concepto INT NULL,                            -- Lo asigna la completitud (script 34); NULL tras el ETL 31
    CONSTRAINT FK_FactTrans_Tiempo FOREIGN KEY (sk_tiempo) REFERENCES Dim_Tiempo(sk_tiempo),
    CONSTRAINT FK_FactTrans_Concepto FOREIGN KEY (sk_concepto) REFERENCES Dim_Concepto_Movimiento(sk_concepto),
    CONSTRAINT FK_FactTrans_Cuenta FOREIGN KEY (sk_cuenta) REFERENCES Dim_Cuenta(sk_cuenta),
    CONSTRAINT FK_FactTrans_Cliente FOREIGN KEY (sk_cliente) REFERENCES Dim_Cliente(sk_cliente),
    CONSTRAINT FK_FactTrans_Distrito FOREIGN KEY (sk_distrito) REFERENCES Dim_Distrito(sk_distrito),
    CONSTRAINT FK_FactTrans_Operacion FOREIGN KEY (sk_operacion) REFERENCES Dim_Operacion(sk_operacion)
);
GO

-- Fact_Saldo_Cuenta_Mensual. Grano: cuenta x mes (185,615 filas: cada cuenta desde
-- su primer mes con movimientos hasta dic-1998, arrastrando el último saldo).
-- Foto periódica. Control: SUM(saldo_fin_mes) de dic-1998 = 197,140,434.00
--   Semiaditivas: saldo_fin_mes, saldo_promedio_mes (se suman entre cuentas, no entre meses)
--   Aditiva: num_movimientos_mes. Indicador: en_sobregiro (se cuenta).
CREATE TABLE Fact_Saldo_Cuenta_Mensual (
    sk_cuenta INT NOT NULL,
    sk_mes INT NOT NULL,                             -- sk_tiempo del último día del mes
    sk_cliente INT NOT NULL,                         -- Titular OWNER
    sk_distrito INT NOT NULL,                        -- Distrito de la cuenta
    saldo_fin_mes DECIMAL(12,2) NOT NULL,            -- Último movimiento del mes (desempate por id); arrastre si no hubo
    saldo_promedio_mes DECIMAL(12,2) NOT NULL,       -- Promedio de los saldos del mes; = saldo_fin_mes si no hubo movimientos
    num_movimientos_mes INT NOT NULL,
    en_sobregiro BIT NOT NULL,                       -- saldo_fin_mes < 0
    CONSTRAINT PK_Fact_Saldo_Cuenta_Mensual PRIMARY KEY (sk_cuenta, sk_mes),
    CONSTRAINT FK_FactSaldo_Cuenta FOREIGN KEY (sk_cuenta) REFERENCES Dim_Cuenta(sk_cuenta),
    CONSTRAINT FK_FactSaldo_Mes FOREIGN KEY (sk_mes) REFERENCES Dim_Tiempo(sk_tiempo),
    CONSTRAINT FK_FactSaldo_Cliente FOREIGN KEY (sk_cliente) REFERENCES Dim_Cliente(sk_cliente),
    CONSTRAINT FK_FactSaldo_Distrito FOREIGN KEY (sk_distrito) REFERENCES Dim_Distrito(sk_distrito)
);
GO

-- Fact_Ordenes. Grano: una orden permanente vigente (6,471). Foto sin fecha de evento.
CREATE TABLE Fact_Ordenes (
    sk_orden INT IDENTITY(1,1) PRIMARY KEY,
    sk_tiempo_apertura_cuenta INT NOT NULL,          -- Rol de Dim_Tiempo: NO es fecha de la orden
    sk_cuenta INT NOT NULL,
    sk_cliente INT NOT NULL,                         -- Titular OWNER
    sk_distrito INT NOT NULL,                        -- Distrito de la cuenta
    sk_orden_tipo INT NOT NULL,
    id_orden_bk INT NOT NULL UNIQUE,
    monto_orden DECIMAL(12,2) NOT NULL,              -- Total de control: 21,229,041.00
    CONSTRAINT FK_FactOrdenes_Tiempo FOREIGN KEY (sk_tiempo_apertura_cuenta) REFERENCES Dim_Tiempo(sk_tiempo),
    CONSTRAINT FK_FactOrdenes_Cuenta FOREIGN KEY (sk_cuenta) REFERENCES Dim_Cuenta(sk_cuenta),
    CONSTRAINT FK_FactOrdenes_Cliente FOREIGN KEY (sk_cliente) REFERENCES Dim_Cliente(sk_cliente),
    CONSTRAINT FK_FactOrdenes_Distrito FOREIGN KEY (sk_distrito) REFERENCES Dim_Distrito(sk_distrito),
    CONSTRAINT FK_FactOrdenes_OrdenTipo FOREIGN KEY (sk_orden_tipo) REFERENCES Dim_Orden(sk_orden_tipo)
);
GO

-- ==============================================================================
-- 4. AUDITORÍA DE CARGAS (Carta v8, sección 12.3)
-- ==============================================================================

-- Resultado de cada prueba de validación por ejecución del ETL.
CREATE TABLE Auditoria_Carga (
    id_auditoria INT IDENTITY(1,1) PRIMARY KEY,
    id_ejecucion VARCHAR(20) NOT NULL,           -- Marca de tiempo de la ejecución (AAAAMMDD_HHMMSS)
    fecha_registro DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
    prueba VARCHAR(120) NOT NULL,
    valor_esperado VARCHAR(200) NULL,
    valor_obtenido VARCHAR(200) NULL,
    resultado VARCHAR(10) NOT NULL               -- OK / FALLA / PENDIENTE
);
GO

-- Registros de la fuente que no cumplen una regla y cómo se trataron.
CREATE TABLE Auditoria_Anomalias (
    id_anomalia INT IDENTITY(1,1) PRIMARY KEY,
    id_ejecucion VARCHAR(20) NOT NULL,
    tabla_origen VARCHAR(30) NOT NULL,
    clave_origen VARCHAR(50) NOT NULL,
    descripcion VARCHAR(300) NOT NULL,
    tratamiento VARCHAR(200) NOT NULL
);
GO

-- ==============================================================================
-- 5. ÍNDICES DE APOYO A LAS CONSULTAS ANALÍTICAS
-- ==============================================================================
CREATE INDEX IX_FactTrans_Cuenta_Tiempo ON Fact_Transacciones (sk_cuenta, sk_tiempo, id_transaccion_bk);
CREATE INDEX IX_FactTrans_Operacion ON Fact_Transacciones (sk_operacion) INCLUDE (monto_transaccion);
CREATE INDEX IX_FactSaldo_Mes ON Fact_Saldo_Cuenta_Mensual (sk_mes) INCLUDE (saldo_fin_mes, sk_distrito);
CREATE INDEX IX_FactOrdenes_Cuenta ON Fact_Ordenes (sk_cuenta) INCLUDE (monto_orden);
GO

PRINT 'Esquema dimensional Kimball (Carta v8): 4 hechos y 7 dimensiones creados.';
GO
