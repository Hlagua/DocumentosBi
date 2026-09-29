-- ==============================================================================
-- UNIVERSIDAD TÉCNICA DE AMBATO
-- FACULTAD DE INGENIERÍA EN SISTEMAS ELECTRÓNICA E INDUSTRIAL
-- CARRERA DE SOFTWARE - CICLO ACADÉMICO: AGOSTO 2026 – DICIEMBRE 2026
-- ASIGNATURA: Inteligencia de Negocios
-- DOCENTE: Ing. Ruben Nogales, Mg.
-- AUTORES: Alison Marcela Cobos Taco / Henry Daniel Lagua Flores
-- ==============================================================================
-- ARCHIVO: 02_DDL_Inmon_EDW_Financial.sql   (versión alineada con la Carta v8)
-- DESCRIPCIÓN: Enterprise Data Warehouse (Bill Inmon, Corporate Information
--              Factory) en Tercera Forma Normal, organizado por áreas temáticas,
--              y data marts departamentales derivados como vistas.
-- CRITERIOS 3FN:
--   * Toda traducción o descripción depende de un código y vive en un catálogo,
--     no se repite en cada transacción u orden.
--   * No se almacenan atributos derivados (edad, etiqueta de buen pagador,
--     categoría analítica): se calculan en los data marts.
--   * tkeys se conserva tal como viene de la fuente (1 = impago).
-- ESTADO: estructura de referencia comparativa. El proyecto implementa y carga
--         Kimball; este EDW no se carga en producción.
-- ==============================================================================

USE master;
GO

IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = 'EDW_Financial_Inmon')
BEGIN
    CREATE DATABASE EDW_Financial_Inmon;
    PRINT 'Base de datos EDW_Financial_Inmon creada.';
END
GO

USE EDW_Financial_Inmon;
GO

-- ==============================================================================
-- ÁREA TEMÁTICA 0: CATÁLOGOS DE REFERENCIA
-- ==============================================================================

CREATE TABLE EDW_Frecuencia_Extracto (
    codigo_frecuencia VARCHAR(30) PRIMARY KEY,   -- POPLATEK MESICNE / TYDNE / PO OBRATU
    descripcion VARCHAR(60) NOT NULL             -- Extracto mensual / semanal / después de cada transacción
);
GO

CREATE TABLE EDW_Estado_Prestamo (
    codigo_estado CHAR(1) PRIMARY KEY,           -- A, B, C, D
    condicion VARCHAR(20) NOT NULL,              -- Cerrado / Vigente
    descripcion VARCHAR(100) NOT NULL
);
GO

-- Una fila por combinación real type + operation + k_symbol (15 filas).
CREATE TABLE EDW_Tipo_Operacion (
    id_tipo_operacion INT PRIMARY KEY,
    tipo VARCHAR(20) NOT NULL,                   -- PRIJEM / VYDAJ / VYBER
    operacion VARCHAR(20) NOT NULL,              -- VKLAD, VYBER, ... o SIN_ESPECIFICAR
    k_symbol VARCHAR(20) NOT NULL,               -- UROK, SIPO, ... o SIN_ESPECIFICAR
    operacion_traducida VARCHAR(50) NOT NULL,
    concepto_traducido VARCHAR(60) NOT NULL,
    CONSTRAINT UQ_EDW_Tipo_Operacion UNIQUE (tipo, operacion, k_symbol)
);
GO

CREATE TABLE EDW_Proposito_Orden (
    k_symbol VARCHAR(20) PRIMARY KEY,            -- SIPO, UVER, POJISTNE, LEASING, SIN_ESPECIFICAR
    descripcion VARCHAR(60) NOT NULL
);
GO

-- ==============================================================================
-- ÁREA TEMÁTICA 1: TERRITORIO
-- ==============================================================================

CREATE TABLE EDW_Distrito (
    id_distrito INT PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL,
    region VARCHAR(50) NOT NULL,
    poblacion INT NOT NULL,
    salario_promedio DECIMAL(10,2) NULL,
    tasa_desempleo_1995 DECIMAL(5,2) NULL,       -- NULL en la fuente para el distrito 69
    tasa_desempleo_1996 DECIMAL(5,2) NULL,
    tasa_criminalidad_1995 INT NULL,             -- NULL en la fuente para el distrito 69
    tasa_criminalidad_1996 INT NULL
);
GO

-- ==============================================================================
-- ÁREA TEMÁTICA 2: SUJETOS (CLIENTES Y EVALUACIÓN)
-- ==============================================================================

-- Evaluación de préstamos cerrados, fiel a tkeys (234 filas).
-- good_client = 1 identifica los 31 préstamos B (impago), 0 los 203 A.
CREATE TABLE EDW_Evaluacion_Credito (
    id_evaluacion INT PRIMARY KEY,               -- tkeys.id
    good_client BIT NOT NULL                     -- Valor original de la fuente
);
GO

CREATE TABLE EDW_Cliente (
    id_cliente INT PRIMARY KEY,
    fecha_nacimiento DATE NOT NULL,              -- Derivada de birth_number en staging
    sexo CHAR(1) NOT NULL,
    id_distrito INT NOT NULL,                    -- Residencia
    id_evaluacion INT NULL,                      -- clients.tkey_id (289 clientes)
    CONSTRAINT FK_EDW_Cliente_Distrito FOREIGN KEY (id_distrito) REFERENCES EDW_Distrito(id_distrito),
    CONSTRAINT FK_EDW_Cliente_Evaluacion FOREIGN KEY (id_evaluacion) REFERENCES EDW_Evaluacion_Credito(id_evaluacion)
);
GO

-- ==============================================================================
-- ÁREA TEMÁTICA 3: CONTRATOS (CUENTAS, DISPOSICIONES, TARJETAS)
-- ==============================================================================

CREATE TABLE EDW_Cuenta (
    id_cuenta INT PRIMARY KEY,
    codigo_frecuencia VARCHAR(30) NOT NULL,
    fecha_apertura DATE NOT NULL,
    id_distrito INT NOT NULL,                    -- Distrito de la cuenta
    CONSTRAINT FK_EDW_Cuenta_Frecuencia FOREIGN KEY (codigo_frecuencia) REFERENCES EDW_Frecuencia_Extracto(codigo_frecuencia),
    CONSTRAINT FK_EDW_Cuenta_Distrito FOREIGN KEY (id_distrito) REFERENCES EDW_Distrito(id_distrito)
);
GO

-- Resuelve la relación M:N cliente-cuenta. En la fuente: 1 cuenta por cliente,
-- 1 OWNER por cuenta y 0 o 1 DISPONENT.
CREATE TABLE EDW_Disposicion (
    id_disposicion INT PRIMARY KEY,
    id_cliente INT NOT NULL UNIQUE,
    id_cuenta INT NOT NULL,
    tipo_disposicion VARCHAR(20) NOT NULL,
    CONSTRAINT FK_EDW_Disp_Cliente FOREIGN KEY (id_cliente) REFERENCES EDW_Cliente(id_cliente),
    CONSTRAINT FK_EDW_Disp_Cuenta FOREIGN KEY (id_cuenta) REFERENCES EDW_Cuenta(id_cuenta),
    CONSTRAINT CK_EDW_Disp_Tipo CHECK (tipo_disposicion IN ('OWNER', 'DISPONENT'))
);
GO

-- Un único titular por cuenta.
CREATE UNIQUE INDEX UX_EDW_Disp_Owner ON EDW_Disposicion (id_cuenta) WHERE tipo_disposicion = 'OWNER';
GO

CREATE TABLE EDW_Tarjeta (
    id_tarjeta INT PRIMARY KEY,
    id_disposicion INT NOT NULL UNIQUE,          -- 0 o 1 tarjeta por disposición
    tipo_tarjeta VARCHAR(20) NOT NULL,
    fecha_emision DATE NOT NULL,
    CONSTRAINT FK_EDW_Tarjeta_Disp FOREIGN KEY (id_disposicion) REFERENCES EDW_Disposicion(id_disposicion)
);
GO

-- ==============================================================================
-- ÁREA TEMÁTICA 4: CRÉDITO
-- ==============================================================================

CREATE TABLE EDW_Prestamo (
    id_prestamo INT PRIMARY KEY,
    id_cuenta INT NOT NULL UNIQUE,               -- 0 o 1 préstamo por cuenta
    fecha DATE NOT NULL,
    monto DECIMAL(12,2) NOT NULL,
    plazo INT NOT NULL,
    cuota DECIMAL(12,2) NOT NULL,
    codigo_estado CHAR(1) NOT NULL,
    CONSTRAINT FK_EDW_Prestamo_Cuenta FOREIGN KEY (id_cuenta) REFERENCES EDW_Cuenta(id_cuenta),
    CONSTRAINT FK_EDW_Prestamo_Estado FOREIGN KEY (codigo_estado) REFERENCES EDW_Estado_Prestamo(codigo_estado)
);
GO

-- ==============================================================================
-- ÁREA TEMÁTICA 5: MOVIMIENTOS Y ÓRDENES
-- ==============================================================================

CREATE TABLE EDW_Transaccion (
    id_transaccion INT PRIMARY KEY,
    id_cuenta INT NOT NULL,
    fecha DATE NOT NULL,
    id_tipo_operacion INT NOT NULL,
    monto DECIMAL(12,2) NOT NULL,
    saldo DECIMAL(12,2) NOT NULL,
    banco_contraparte VARCHAR(2) NULL,           -- Código de banco (no es dato personal)
    cuenta_contraparte_hash CHAR(64) NULL,       -- SHA2_256 del número de cuenta externo
    CONSTRAINT FK_EDW_Trans_Cuenta FOREIGN KEY (id_cuenta) REFERENCES EDW_Cuenta(id_cuenta),
    CONSTRAINT FK_EDW_Trans_Tipo FOREIGN KEY (id_tipo_operacion) REFERENCES EDW_Tipo_Operacion(id_tipo_operacion)
);
GO

CREATE INDEX IX_EDW_Trans_Cuenta_Fecha ON EDW_Transaccion (id_cuenta, fecha, id_transaccion);
GO

CREATE TABLE EDW_Orden (
    id_orden INT PRIMARY KEY,
    id_cuenta INT NOT NULL,
    k_symbol VARCHAR(20) NOT NULL,
    monto DECIMAL(12,2) NOT NULL,
    banco_destino VARCHAR(2) NOT NULL,
    cuenta_destino_hash CHAR(64) NOT NULL,       -- SHA2_256 del número de cuenta destino
    CONSTRAINT FK_EDW_Orden_Cuenta FOREIGN KEY (id_cuenta) REFERENCES EDW_Cuenta(id_cuenta),
    CONSTRAINT FK_EDW_Orden_Proposito FOREIGN KEY (k_symbol) REFERENCES EDW_Proposito_Orden(k_symbol)
);
GO

-- ==============================================================================
-- DATA MARTS DEPARTAMENTALES DERIVADOS (VISTAS)
-- Reglas de la Carta v8: distrito = distrito de la cuenta; último saldo con
-- desempate por id_transaccion; razones calculadas sobre agregados.
-- ==============================================================================

-- ---------------------------- Riesgo y cartera ---------------------------------

-- Mora por distrito (C y D). Tasa descriptiva: mostrar siempre con su n.
CREATE VIEW Vista_Mora_Distrito AS
SELECT
    d.id_distrito,
    d.nombre AS nombre_distrito,
    d.region,
    COUNT(*) AS prestamos_vigentes,
    SUM(CASE WHEN p.codigo_estado = 'D' THEN 1 ELSE 0 END) AS prestamos_en_mora,
    SUM(p.monto) AS cartera_vigente,
    CAST(100.0 * SUM(CASE WHEN p.codigo_estado = 'D' THEN 1 ELSE 0 END) / COUNT(*) AS DECIMAL(5,2)) AS tasa_mora_pct
FROM EDW_Prestamo p
JOIN EDW_Cuenta c ON c.id_cuenta = p.id_cuenta
JOIN EDW_Distrito d ON d.id_distrito = c.id_distrito
WHERE p.codigo_estado IN ('C', 'D')
GROUP BY d.id_distrito, d.nombre, d.region;
GO

-- Incumplimiento histórico por región (A y B).
CREATE VIEW Vista_Calidad_Historica AS
SELECT
    d.region,
    COUNT(*) AS prestamos_cerrados,
    SUM(CASE WHEN p.codigo_estado = 'B' THEN 1 ELSE 0 END) AS prestamos_con_deuda,
    CAST(100.0 * SUM(CASE WHEN p.codigo_estado = 'B' THEN 1 ELSE 0 END) / COUNT(*) AS DECIMAL(5,2)) AS tasa_incumplimiento_pct
FROM EDW_Prestamo p
JOIN EDW_Cuenta c ON c.id_cuenta = p.id_cuenta
JOIN EDW_Distrito d ON d.id_distrito = c.id_distrito
WHERE p.codigo_estado IN ('A', 'B')
GROUP BY d.region;
GO

-- Capacidad de pago por préstamo: cuota / saldo promedio de la cuenta antes del otorgamiento.
CREATE VIEW Vista_Capacidad_Pago AS
SELECT
    p.id_prestamo,
    p.id_cuenta,
    p.codigo_estado,
    p.cuota,
    x.saldo_promedio_previo,
    CAST(p.cuota / x.saldo_promedio_previo AS DECIMAL(9,4)) AS ratio_cuota_saldo_previo,
    CASE
        WHEN p.cuota / x.saldo_promedio_previo <= 0.057 THEN 'Baja'
        WHEN p.cuota / x.saldo_promedio_previo <= 0.090 THEN 'Media-baja'
        WHEN p.cuota / x.saldo_promedio_previo <= 0.123 THEN 'Media-alta'
        ELSE 'Alta'
    END AS banda_capacidad,
    CASE WHEN p.codigo_estado IN ('B', 'D') THEN 1 ELSE 0 END AS con_impago
FROM EDW_Prestamo p
CROSS APPLY (
    SELECT AVG(t.saldo) AS saldo_promedio_previo
    FROM EDW_Transaccion t
    WHERE t.id_cuenta = p.id_cuenta AND t.fecha < p.fecha
) x;
GO

-- ---------------------------- Saldos y liquidez --------------------------------

-- Último saldo por cuenta al corte (desempate por id_transaccion mayor).
CREATE VIEW Vista_Saldo_Final_Cuenta AS
SELECT id_cuenta, id_distrito, fecha AS fecha_ultimo_movimiento, saldo AS saldo_final
FROM (
    SELECT t.id_cuenta, c.id_distrito, t.fecha, t.saldo,
           ROW_NUMBER() OVER (PARTITION BY t.id_cuenta ORDER BY t.fecha DESC, t.id_transaccion DESC) AS rn
    FROM EDW_Transaccion t
    JOIN EDW_Cuenta c ON c.id_cuenta = t.id_cuenta
) x
WHERE rn = 1;
GO

-- Ratio de absorción de la cartera vigente por región (se agregan por separado y luego se dividen).
CREATE VIEW Vista_Absorcion_Region AS
WITH cartera AS (
    SELECT d.region, SUM(p.monto) AS cartera_vigente
    FROM EDW_Prestamo p
    JOIN EDW_Cuenta c ON c.id_cuenta = p.id_cuenta
    JOIN EDW_Distrito d ON d.id_distrito = c.id_distrito
    WHERE p.codigo_estado IN ('C', 'D')
    GROUP BY d.region
), saldo AS (
    SELECT d.region, SUM(s.saldo_final) AS saldo_neto,
           SUM(CASE WHEN s.saldo_final < 0 THEN 1 ELSE 0 END) AS cuentas_sobregiro
    FROM Vista_Saldo_Final_Cuenta s
    JOIN EDW_Distrito d ON d.id_distrito = s.id_distrito
    GROUP BY d.region
)
SELECT s.region, c.cartera_vigente, s.saldo_neto, s.cuentas_sobregiro,
       CAST(c.cartera_vigente / s.saldo_neto AS DECIMAL(9,4)) AS ratio_absorcion_vigente
FROM saldo s
JOIN cartera c ON c.region = s.region;
GO

-- ---------------------------- Operaciones --------------------------------------

-- Volumen por año y categoría analítica (la categoría se deriva aquí, no se almacena).
CREATE VIEW Vista_Volumen_Operaciones AS
SELECT
    YEAR(t.fecha) AS anio,
    CASE
        WHEN o.tipo = 'PRIJEM' AND o.k_symbol = 'UROK' THEN 'Intereses Ganados'
        WHEN o.tipo = 'PRIJEM' THEN 'Ingreso / Deposito'
        WHEN o.tipo = 'VYDAJ' THEN 'Egreso / Gasto'
        ELSE 'Retiro en Efectivo'
    END AS categoria_analitica,
    COUNT(*) AS numero_transacciones,
    SUM(t.monto) AS monto_total,
    AVG(t.monto) AS ticket_promedio
FROM EDW_Transaccion t
JOIN EDW_Tipo_Operacion o ON o.id_tipo_operacion = t.id_tipo_operacion
GROUP BY YEAR(t.fecha),
    CASE
        WHEN o.tipo = 'PRIJEM' AND o.k_symbol = 'UROK' THEN 'Intereses Ganados'
        WHEN o.tipo = 'PRIJEM' THEN 'Ingreso / Deposito'
        WHEN o.tipo = 'VYDAJ' THEN 'Egreso / Gasto'
        ELSE 'Retiro en Efectivo'
    END;
GO

-- Órdenes por propósito.
CREATE VIEW Vista_Ordenes_Recurrentes AS
SELECT
    po.descripcion AS categoria_orden,
    COUNT(*) AS total_ordenes,
    SUM(o.monto) AS monto_total_comprometido,
    AVG(o.monto) AS monto_promedio_orden
FROM EDW_Orden o
JOIN EDW_Proposito_Orden po ON po.k_symbol = o.k_symbol
GROUP BY po.descripcion;
GO

PRINT 'EDW Inmon (3FN, Carta v8): 13 tablas y 7 vistas de data marts creadas.';
GO
