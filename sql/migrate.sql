-- ============================================
-- LAST MILE PLATFORM - PostgreSQL Schema
-- Migracion desde sistema legacy
-- ============================================

-- ========================================
-- CORE: Empresas (Multi-tenant)
-- ========================================
CREATE TABLE IF NOT EXISTS empresas (
    emp_id SERIAL PRIMARY KEY,
    emp_nombre VARCHAR(200) NOT NULL,
    emp_direccion VARCHAR(500),
    emp_telefono VARCHAR(15),
    emp_email VARCHAR(150),
    emp_contacto VARCHAR(200),
    emp_fecha_alta TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    emp_estatus VARCHAR(15) DEFAULT 'ACTIVO',
    emp_plan VARCHAR(30) DEFAULT 'STARTER',
    emp_max_choferes INT DEFAULT 5,
    emp_max_pedidos_mes INT DEFAULT 1000,
    emp_max_usuarios INT DEFAULT 3
);

-- ========================================
-- CORE: Usuarios
-- ========================================
CREATE TABLE IF NOT EXISTS usuarios (
    usr_id SERIAL PRIMARY KEY,
    emp_id INT NOT NULL REFERENCES empresas(emp_id),
    usr_nombre VARCHAR(200) NOT NULL,
    usr_email VARCHAR(150) UNIQUE NOT NULL,
    usr_password_hash VARCHAR(256) NOT NULL,
    usr_rol VARCHAR(30) DEFAULT 'OPERADOR',
    usr_telefono VARCHAR(15),
    usr_activo BOOLEAN DEFAULT TRUE,
    usr_ultimo_acceso TIMESTAMP,
    usr_fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ========================================
-- CORE: Choferes
-- ========================================
CREATE TABLE IF NOT EXISTS choferes (
    cho_id SERIAL PRIMARY KEY,
    emp_id INT NOT NULL REFERENCES empresas(emp_id),
    cho_nombre VARCHAR(100) NOT NULL,
    cho_apellido VARCHAR(100) NOT NULL,
    cho_telefono VARCHAR(15),
    cho_email VARCHAR(150),
    cho_num_licencia VARCHAR(50),
    cho_estatus VARCHAR(15) DEFAULT 'ACTIVO',
    cho_fecha_alta TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ========================================
-- CORE: Vehiculos
-- ========================================
CREATE TABLE IF NOT EXISTS vehiculos (
    veh_id SERIAL PRIMARY KEY,
    emp_id INT NOT NULL REFERENCES empresas(emp_id),
    veh_unidad VARCHAR(20) NOT NULL,
    veh_marca VARCHAR(50),
    veh_modelo VARCHAR(50),
    veh_anio INT,
    veh_tipo VARCHAR(30),
    veh_capacidad_kg DECIMAL(10,2),
    veh_capacidad_m3 DECIMAL(10,2),
    veh_color VARCHAR(30),
    veh_placas VARCHAR(20),
    veh_estatus VARCHAR(15) DEFAULT 'ACTIVO',
    veh_gps_activo VARCHAR(3) DEFAULT 'NO'
);

-- ========================================
-- CORE: Clientes
-- ========================================
CREATE TABLE IF NOT EXISTS clientes (
    cli_id SERIAL PRIMARY KEY,
    emp_id INT NOT NULL REFERENCES empresas(emp_id),
    cli_razon_social VARCHAR(200) NOT NULL,
    cli_nombre_comercial VARCHAR(200),
    cli_rfc VARCHAR(13),
    cli_direccion VARCHAR(500),
    cli_colonia VARCHAR(100),
    cli_ciudad VARCHAR(100),
    cli_estado VARCHAR(50),
    cli_cp VARCHAR(5),
    cli_telefono VARCHAR(15),
    cli_email VARCHAR(150),
    cli_contacto VARCHAR(200),
    cli_latitud DECIMAL(12,8),
    cli_longitud DECIMAL(12,8),
    cli_tipo_cliente VARCHAR(30) DEFAULT 'REGULAR',
    cli_credito DECIMAL(12,2) DEFAULT 0,
    cli_estatus VARCHAR(15) DEFAULT 'ACTIVO',
    cli_fecha_alta TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ========================================
-- CORE: Pedidos
-- ========================================
CREATE TABLE IF NOT EXISTS pedidos (
    ped_id SERIAL PRIMARY KEY,
    emp_id INT NOT NULL REFERENCES empresas(emp_id),
    cli_id INT REFERENCES clientes(cli_id),
    ped_numero VARCHAR(25) UNIQUE NOT NULL,
    ped_cliente_nombre VARCHAR(200),
    ped_cliente_telefono VARCHAR(15),
    ped_origen_dir VARCHAR(500),
    ped_origen_col VARCHAR(100),
    ped_origen_ciudad VARCHAR(100),
    ped_destino_dir VARCHAR(500) NOT NULL,
    ped_destino_col VARCHAR(100),
    ped_destino_ciudad VARCHAR(100),
    ped_destino_cp VARCHAR(5),
    ped_peso_kg DECIMAL(8,2) DEFAULT 0,
    ped_bultos INT DEFAULT 1,
    ped_costo_total DECIMAL(12,2) DEFAULT 0,
    ped_forma_pago VARCHAR(30) DEFAULT 'EFECTIVO',
    ped_estado VARCHAR(20) DEFAULT 'PENDIENTE',
    ped_prioridad VARCHAR(15) DEFAULT 'NORMAL',
    chofer_asignado VARCHAR(200),
    unidad_asignada VARCHAR(20),
    ped_fecha_pedido TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ped_fecha_asignacion TIMESTAMP,
    ped_fecha_salida TIMESTAMP,
    ped_fecha_entrega TIMESTAMP,
    ped_fecha_entrega_real TIMESTAMP,
    ped_indicaciones VARCHAR(500)
);

CREATE INDEX IF NOT EXISTS idx_pedidos_emp ON pedidos(emp_id);
CREATE INDEX IF NOT EXISTS idx_pedidos_estado ON pedidos(ped_estado);
CREATE INDEX IF NOT EXISTS idx_pedidos_fecha ON pedidos(ped_fecha_pedido);

-- ========================================
-- CORE: Rutas
-- ========================================
CREATE TABLE IF NOT EXISTS rutas (
    rut_id SERIAL PRIMARY KEY,
    emp_id INT NOT NULL REFERENCES empresas(emp_id),
    rut_nombre VARCHAR(100) NOT NULL,
    rut_fecha DATE,
    cho_id INT REFERENCES choferes(cho_id),
    veh_id INT REFERENCES vehiculos(veh_id),
    rut_total_pedidos INT DEFAULT 0,
    rut_total_entregas INT DEFAULT 0,
    rut_total_km DECIMAL(8,2) DEFAULT 0,
    rut_costo_total DECIMAL(12,2) DEFAULT 0,
    rut_tiempo_total_min INT DEFAULT 0,
    rut_estado VARCHAR(15) DEFAULT 'PLANIFICADA'
);

-- ========================================
-- CORE: Entregas
-- ========================================
CREATE TABLE IF NOT EXISTS entregas (
    ent_id SERIAL PRIMARY KEY,
    emp_id INT NOT NULL REFERENCES empresas(emp_id),
    ped_id INT REFERENCES pedidos(ped_id),
    rut_id INT REFERENCES rutas(rut_id),
    cho_id INT REFERENCES choferes(cho_id),
    veh_id INT REFERENCES vehiculos(veh_id),
    ent_estado VARCHAR(20) DEFAULT 'PENDIENTE',
    ent_fecha_llegada TIMESTAMP,
    ent_hora_entrega TIMESTAMP,
    ent_tiempo_espera_min INT DEFAULT 0,
    ent_evidencia VARCHAR(500),
    ent_firma VARCHAR(500),
    ent_foto VARCHAR(500),
    ent_motivo_falla VARCHAR(200)
);

-- ========================================
-- CORE: Tracking GPS
-- ========================================
CREATE TABLE IF NOT EXISTS tracking (
    trk_id SERIAL PRIMARY KEY,
    emp_id INT NOT NULL REFERENCES empresas(emp_id),
    cho_id INT REFERENCES choferes(cho_id),
    veh_id INT REFERENCES vehiculos(veh_id),
    trk_latitud DECIMAL(12,8),
    trk_longitud DECIMAL(12,8),
    trk_velocidad DECIMAL(6,2) DEFAULT 0,
    trk_rumbo DECIMAL(6,2) DEFAULT 0,
    trk_bateria INT DEFAULT 100,
    trk_fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_tracking_cho ON tracking(cho_id);
CREATE INDEX IF NOT EXISTS idx_tracking_fecha ON tracking(trk_fecha);

-- ========================================
-- CORE: Incidencias
-- ========================================
CREATE TABLE IF NOT EXISTS incidencias (
    inc_id SERIAL PRIMARY KEY,
    emp_id INT NOT NULL REFERENCES empresas(emp_id),
    ped_id INT REFERENCES pedidos(ped_id),
    ent_id INT REFERENCES entregas(ent_id),
    cho_id INT REFERENCES choferes(cho_id),
    inc_tipo VARCHAR(50) NOT NULL,
    inc_descripcion VARCHAR(500),
    inc_foto VARCHAR(500),
    inc_estado VARCHAR(15) DEFAULT 'ABIERTA',
    inc_fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    inc_resuelta_fecha TIMESTAMP,
    inc_resuelta_por VARCHAR(50)
);

-- ========================================
-- CORE: Zonas y Tarifas
-- ========================================
CREATE TABLE IF NOT EXISTS zonas (
    zon_id SERIAL PRIMARY KEY,
    emp_id INT NOT NULL REFERENCES empresas(emp_id),
    zon_nombre VARCHAR(100) NOT NULL,
    zon_colonias TEXT,
    zon_ciudad VARCHAR(100),
    zon_estado VARCHAR(50),
    zon_latitud_center DECIMAL(12,8),
    zon_longitud_center DECIMAL(12,8),
    zon_radio_km DECIMAL(8,2),
    zon_estatus VARCHAR(10) DEFAULT 'ACTIVA'
);

CREATE TABLE IF NOT EXISTS tarifas (
    tar_id SERIAL PRIMARY KEY,
    emp_id INT NOT NULL REFERENCES empresas(emp_id),
    tar_nombre VARCHAR(100) NOT NULL,
    tar_tipo VARCHAR(30),
    tar_zona_origen INT REFERENCES zonas(zon_id),
    tar_zona_destino INT REFERENCES zonas(zon_id),
    tar_peso_min_kg DECIMAL(8,2) DEFAULT 0,
    tar_peso_max_kg DECIMAL(8,2) DEFAULT 999,
    tar_monto_base DECIMAL(10,2) DEFAULT 0,
    tar_monto_por_kg DECIMAL(10,2) DEFAULT 0,
    tar_monto_por_km DECIMAL(10,2) DEFAULT 0,
    tar_estatus VARCHAR(10) DEFAULT 'ACTIVA'
);

-- ========================================
-- CORE: KPIs Diarios
-- ========================================
CREATE TABLE IF NOT EXISTS kpi_diario (
    kpi_id SERIAL PRIMARY KEY,
    emp_id INT NOT NULL REFERENCES empresas(emp_id),
    kpi_fecha DATE NOT NULL,
    kpi_total_nuevos INT DEFAULT 0,
    kpi_total_entregados INT DEFAULT 0,
    kpi_total_fallidos INT DEFAULT 0,
    kpi_total_cancelados INT DEFAULT 0,
    kpi_ingreso_total DECIMAL(12,2) DEFAULT 0,
    kpi_costo_total DECIMAL(12,2) DEFAULT 0,
    kpi_utilidad DECIMAL(12,2) DEFAULT 0,
    kpi_km_total DECIMAL(10,2) DEFAULT 0,
    kpi_tiempo_promedio_min INT DEFAULT 0,
    kpi_choferes_activos INT DEFAULT 0,
    kpi_vehiculos_activos INT DEFAULT 0,
    UNIQUE(emp_id, kpi_fecha)
);

-- ========================================
-- CORE: Pedido Historial
-- ========================================
CREATE TABLE IF NOT EXISTS pedido_historial (
    his_id SERIAL PRIMARY KEY,
    ped_id INT NOT NULL REFERENCES pedidos(ped_id),
    his_estado VARCHAR(20) NOT NULL,
    his_usuario VARCHAR(50),
    his_notas VARCHAR(500),
    his_fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ========================================
-- CORE: Audit Log
-- ========================================
CREATE TABLE IF NOT EXISTS audit_log (
    aud_id SERIAL PRIMARY KEY,
    emp_id INT,
    aud_usuario VARCHAR(50),
    aud_accion VARCHAR(50),
    aud_tabla VARCHAR(50),
    aud_registro_id INT,
    aud_detalles VARCHAR(500),
    aud_fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ========================================
-- CFDI: Facturacion Electronica
-- ========================================
CREATE TABLE IF NOT EXISTS cfdi_empresa_fiscal (
    fisc_id SERIAL PRIMARY KEY,
    emp_id INT UNIQUE NOT NULL REFERENCES empresas(emp_id),
    fisc_rfc VARCHAR(13) NOT NULL,
    fisc_razon_social VARCHAR(200) NOT NULL,
    fisc_regimen_fiscal VARCHAR(10) NOT NULL,
    fisc_codigo_postal VARCHAR(5) NOT NULL,
    fisc_colonia VARCHAR(100),
    fisc_calle VARCHAR(150),
    fisc_numero_exterior VARCHAR(20),
    fisc_municipio VARCHAR(100),
    fisc_estado VARCHAR(50),
    fisc_pais VARCHAR(50) DEFAULT 'MEXICO',
    fisc_telefono VARCHAR(15),
    fisc_email VARCHAR(150),
    fisc_tipo_persona VARCHAR(1) DEFAULT 'M',
    fisc_certificado_cer TEXT,
    fisc_certificado_key TEXT,
    fisc_contraseña_key VARCHAR(200),
    fisc_es_default BOOLEAN DEFAULT TRUE,
    fisc_estatus VARCHAR(15) DEFAULT 'ACTIVO'
);

CREATE TABLE IF NOT EXISTS cfdi_folios (
    fol_id SERIAL PRIMARY KEY,
    emp_id INT NOT NULL REFERENCES empresas(emp_id),
    fol_serie VARCHAR(25) NOT NULL,
    fol_siguiente INT DEFAULT 1,
    fol_final INT DEFAULT 999999,
    fol_estatus VARCHAR(10) DEFAULT 'ACTIVO'
);

CREATE TABLE IF NOT EXISTS cfdi_facturas (
    fac_id SERIAL PRIMARY KEY,
    emp_id INT NOT NULL REFERENCES empresas(emp_id),
    fac_uuid VARCHAR(40),
    fac_serie VARCHAR(25),
    fac_folio VARCHAR(25),
    fac_fecha_emision TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fac_fecha_timbrado TIMESTAMP,
    fac_forma_pago VARCHAR(5) DEFAULT '01',
    fac_metodo_pago VARCHAR(3) DEFAULT 'PUE',
    fac_subtotal DECIMAL(14,2) DEFAULT 0,
    fac_descuento DECIMAL(14,2) DEFAULT 0,
    fac_total_iva DECIMAL(14,2) DEFAULT 0,
    fac_total DECIMAL(14,2) DEFAULT 0,
    fac_moneda VARCHAR(5) DEFAULT 'MXN',
    fac_receptor_rfc VARCHAR(13),
    fac_receptor_razon VARCHAR(200),
    fac_receptor_regimen VARCHAR(10),
    fac_receptor_cp VARCHAR(5),
    fac_receptor_uso_cfdi VARCHAR(3) DEFAULT 'G03',
    fac_receptor_email VARCHAR(150),
    fac_ped_id INT REFERENCES pedidos(ped_id),
    fac_xml_timbrado TEXT,
    fac_estatus VARCHAR(15) DEFAULT 'PENDIENTE',
    fac_motivo_cancelacion VARCHAR(200),
    fac_tipo_documento VARCHAR(10) DEFAULT 'INGRESO'
);

CREATE TABLE IF NOT EXISTS cfdi_facturas_det (
    fad_id SERIAL PRIMARY KEY,
    fac_id INT NOT NULL REFERENCES cfdi_facturas(fac_id),
    fad_no_secuencia INT NOT NULL,
    fad_clave_prod_serv VARCHAR(20) NOT NULL,
    fad_clave_unidad VARCHAR(10) NOT NULL,
    fad_unidad VARCHAR(50) NOT NULL,
    fad_descripcion VARCHAR(250) NOT NULL,
    fad_cantidad DECIMAL(12,4) DEFAULT 1,
    fad_valor_unitario DECIMAL(12,2) DEFAULT 0,
    fad_descuento DECIMAL(12,2) DEFAULT 0,
    fad_subtotal DECIMAL(14,2) DEFAULT 0,
    fad_iva DECIMAL(14,2) DEFAULT 0,
    fad_total DECIMAL(14,2) DEFAULT 0,
    fad_objeto_impuesto VARCHAR(5) DEFAULT '002'
);

CREATE TABLE IF NOT EXISTS cfdi_timbrado_log (
    tim_id SERIAL PRIMARY KEY,
    fac_id INT NOT NULL REFERENCES cfdi_facturas(fac_id),
    tim_pac VARCHAR(50) NOT NULL,
    tim_codigo_respuesta VARCHAR(20),
    tim_mensaje VARCHAR(500),
    tim_fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    tim_exitoso BOOLEAN DEFAULT FALSE
);

-- ========================================
-- PAGOS
-- ========================================
CREATE TABLE IF NOT EXISTS pagos_metodos (
    pmt_id SERIAL PRIMARY KEY,
    emp_id INT NOT NULL REFERENCES empresas(emp_id),
    pmt_tipo VARCHAR(30) NOT NULL,
    pmt_nombre VARCHAR(100) NOT NULL,
    pmt_config VARCHAR(500) DEFAULT '',
    pmt_activo BOOLEAN DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS pagos_transacciones (
    trp_id SERIAL PRIMARY KEY,
    emp_id INT NOT NULL REFERENCES empresas(emp_id),
    ped_id INT REFERENCES pedidos(ped_id),
    fac_id INT REFERENCES cfdi_facturas(fac_id),
    trp_num_referencia VARCHAR(100),
    trp_monto DECIMAL(14,2) DEFAULT 0,
    trp_moneda VARCHAR(5) DEFAULT 'MXN',
    trp_metodo VARCHAR(30) NOT NULL,
    trp_estatus VARCHAR(20) DEFAULT 'PENDIENTE',
    trp_fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    trp_conciliado BOOLEAN DEFAULT FALSE
);

-- ========================================
-- NOTIFICACIONES
-- ========================================
CREATE TABLE IF NOT EXISTS notif_push (
    npush_id SERIAL PRIMARY KEY,
    emp_id INT NOT NULL REFERENCES empresas(emp_id),
    usr_id INT,
    cho_id INT,
    npush_tipo VARCHAR(30) NOT NULL,
    npush_titulo VARCHAR(200) NOT NULL,
    npush_cuerpo VARCHAR(500) NOT NULL,
    npush_data VARCHAR(1000) DEFAULT '{}',
    npush_enviado BOOLEAN DEFAULT FALSE,
    npush_leido BOOLEAN DEFAULT FALSE,
    npush_fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS notif_dispositivos (
    disp_id SERIAL PRIMARY KEY,
    emp_id INT NOT NULL REFERENCES empresas(emp_id),
    usr_id INT,
    cho_id INT,
    disp_token VARCHAR(500) NOT NULL,
    disp_plataforma VARCHAR(20) DEFAULT 'WEB',
    disp_activo BOOLEAN DEFAULT TRUE,
    disp_fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ========================================
-- EMAIL / SMS
-- ========================================
CREATE TABLE IF NOT EXISTS email_enviados (
    email_id SERIAL PRIMARY KEY,
    emp_id INT NOT NULL REFERENCES empresas(emp_id),
    ped_id INT,
    fac_id INT,
    email_destinatario VARCHAR(150) NOT NULL,
    email_asunto VARCHAR(300) NOT NULL,
    email_tipo VARCHAR(50) NOT NULL,
    email_body_html TEXT,
    email_enviado BOOLEAN DEFAULT FALSE,
    email_fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sms_enviados (
    sms_id SERIAL PRIMARY KEY,
    emp_id INT NOT NULL REFERENCES empresas(emp_id),
    ped_id INT,
    sms_telefono VARCHAR(15) NOT NULL,
    sms_mensaje VARCHAR(500) NOT NULL,
    sms_plataforma VARCHAR(15) DEFAULT 'SMS',
    sms_enviado BOOLEAN DEFAULT FALSE,
    sms_fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sms_costo DECIMAL(8,4) DEFAULT 0
);

-- ========================================
-- CLIENTE FINAL (tracking)
-- ========================================
CREATE TABLE IF NOT EXISTS cliente_final (
    clif_id SERIAL PRIMARY KEY,
    emp_id INT NOT NULL REFERENCES empresas(emp_id),
    ped_id INT REFERENCES pedidos(ped_id),
    clif_nombre VARCHAR(200) NOT NULL,
    clif_telefono VARCHAR(15),
    clif_email VARCHAR(150),
    clif_token_tracking VARCHAR(64) UNIQUE NOT NULL,
    clif_notif_sms BOOLEAN DEFAULT TRUE,
    clif_notif_whatsapp BOOLEAN DEFAULT TRUE,
    clif_notif_email BOOLEAN DEFAULT TRUE,
    clif_fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ========================================
-- SaaS BILLING
-- ========================================
CREATE TABLE IF NOT EXISTS saas_planes (
    plan_id SERIAL PRIMARY KEY,
    plan_nombre VARCHAR(50) NOT NULL,
    plan_descripcion VARCHAR(300),
    plan_precio_mensual DECIMAL(12,2) NOT NULL,
    plan_precio_anual DECIMAL(12,2),
    plan_max_choferes INT DEFAULT 5,
    plan_max_envios_mes INT DEFAULT 1000,
    plan_max_usuarios INT DEFAULT 3,
    plan_max_sucursales INT DEFAULT 1,
    plan_activo BOOLEAN DEFAULT TRUE,
    plan_orden INT DEFAULT 0
);

CREATE TABLE IF NOT EXISTS saas_suscripciones (
    sus_id SERIAL PRIMARY KEY,
    emp_id INT UNIQUE NOT NULL REFERENCES empresas(emp_id),
    plan_id INT NOT NULL REFERENCES saas_planes(plan_id),
    sus_estado VARCHAR(20) DEFAULT 'TRIAL',
    sus_fecha_inicio DATE,
    sus_fecha_fin DATE,
    sus_fecha_proximo_cobro DATE,
    sus_facturacion_ciclo VARCHAR(10) DEFAULT 'MENSUAL',
    sus_metodo_pago VARCHAR(30) DEFAULT 'MERCADOPAGO',
    sus_mp_customer_id VARCHAR(100),
    sus_mp_subscription_id VARCHAR(100),
    sus_total_cobrado DECIMAL(12,2) DEFAULT 0,
    sus_fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS saas_cobros (
    cob_id SERIAL PRIMARY KEY,
    sus_id INT NOT NULL REFERENCES saas_suscripciones(sus_id),
    emp_id INT NOT NULL REFERENCES empresas(emp_id),
    cob_monto DECIMAL(12,2) NOT NULL,
    cob_moneda VARCHAR(5) DEFAULT 'MXN',
    cob_concepto VARCHAR(200) NOT NULL,
    cob_estatus VARCHAR(20) DEFAULT 'PENDIENTE',
    cob_metodo_pago VARCHAR(30),
    cob_referencia_pago VARCHAR(200),
    cob_fecha_cobro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    cob_factura_id INT
);

CREATE TABLE IF NOT EXISTS saas_uso_recursos (
    usr_id SERIAL PRIMARY KEY,
    emp_id INT NOT NULL REFERENCES empresas(emp_id),
    usr_fecha DATE NOT NULL,
    usr_pedidos_creados INT DEFAULT 0,
    usr_pedidos_entregados INT DEFAULT 0,
    usr_envios_sms INT DEFAULT 0,
    usr_envios_email INT DEFAULT 0,
    usr_api_calls INT DEFAULT 0,
    UNIQUE(emp_id, usr_fecha)
);

-- ========================================
-- REPORTES
-- ========================================
CREATE TABLE IF NOT EXISTS reportes_generados (
    rpt_id SERIAL PRIMARY KEY,
    emp_id INT NOT NULL REFERENCES empresas(emp_id),
    rpt_tipo VARCHAR(50) NOT NULL,
    rpt_nombre VARCHAR(200) NOT NULL,
    rpt_parametros VARCHAR(1000) DEFAULT '{}',
    rpt_fecha_generacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    rpt_generado_por VARCHAR(50) DEFAULT 'SYSTEM'
);

-- ========================================
-- DATOS INICIALES
-- ========================================

-- Empresas
INSERT INTO empresas (emp_id, emp_nombre, emp_direccion, emp_email, emp_contacto, emp_plan) VALUES
(1, 'DELIVERY EXPRESS MX', 'Av. Reforma 100, CDMX', 'contacto@delmx.com', 'Juan Perez', 'PRO'),
(2, 'TRANSPORTE RAPIDO SA', 'Calle 5 de Mayo 500, GDL', 'contacto@trapido.com', 'Maria Lopez', 'STARTER'),
(3, 'LOGISTICA INTEGRAL MX', 'Av Constitucion 800, MTY', 'contacto@loint.com', 'Carlos Garcia', 'ENTERPRISE');
SELECT setval('empresas_emp_id_seq', 3);

-- Planes SaaS
INSERT INTO saas_planes (plan_nombre, plan_descripcion, plan_precio_mensual, plan_precio_anual, plan_max_choferes, plan_max_envios_mes, plan_max_usuarios, plan_max_sucursales, plan_orden) VALUES
('Starter', 'Para negocios pequenos', 999, 9590, 5, 1000, 3, 1, 1),
('Pro', 'El mas popular', 2499, 23990, 25, 10000, 10, 1, 2),
('Enterprise', 'Multi-sucursal ilimitado', 5999, 57590, 999, 999999, 999, 999, 3);

-- Suscripciones
INSERT INTO saas_suscripciones (emp_id, plan_id, sus_estado, sus_fecha_inicio, sus_fecha_fin) VALUES
(1, 2, 'ACTIVA', '2026-07-01', '2026-12-31'),
(2, 1, 'ACTIVA', '2026-07-01', '2026-12-31'),
(3, 3, 'TRIAL', '2026-07-07', '2026-08-07');

-- Datos fiscales
INSERT INTO cfdi_empresa_fiscal (emp_id, fisc_rfc, fisc_razon_social, fisc_regimen_fiscal, fisc_codigo_postal, fisc_colonia, fisc_calle, fisc_numero_exterior, fisc_municipio, fisc_estado, fisc_telefono, fisc_email) VALUES
(1, 'DEL123456789', 'DELIVERY EXPRESS MX SA DE CV', '601', '06140', 'CONDESA', 'AV REVOLUCION', '1234', 'CIUDAD DE MEXICO', 'CDMX', '5512345678', 'facturacion@delmx.com'),
(2, 'TRA987654321', 'TRANSPORTE RAPIDO SA DE CV', '601', '44100', 'CENTRO', 'CALLE 5 DE MAYO', '500', 'GUADALAJARA', 'JALISCO', '3312345678', 'facturacion@trapido.com'),
(3, 'LOI555666777', 'LOGISTICA INTEGRAL MX SA DE CV', '601', '64000', 'MONTERREY', 'AV CONSTITUCION', '800', 'MONTERREY', 'NUEVO LEON', '8112345678', 'facturacion@loint.com');

-- Folios CFDI
INSERT INTO cfdi_folios (emp_id, fol_serie, fol_siguiente, fol_final) VALUES (1, 'A', 1, 999999), (2, 'B', 1, 999999), (3, 'C', 1, 999999);

-- Metodos de pago
INSERT INTO pagos_metodos (emp_id, pmt_tipo, pmt_nombre) VALUES
(1, 'EFECTIVO', 'Efectivo'), (1, 'OXXO', 'Deposito OXXO'), (1, 'SPEI', 'Transferencia SPEI'),
(1, 'MERCADOPAGO', 'Mercado Pago'), (1, 'TARJETA_CREDITO', 'Tarjeta Credito'),
(2, 'EFECTIVO', 'Efectivo'), (2, 'SPEI', 'Transferencia SPEI'),
(3, 'EFECTIVO', 'Efectivo'), (3, 'MERCADOPAGO', 'Mercado Pago');

-- Datos de prueba: Usuarios
INSERT INTO usuarios (emp_id, usr_nombre, usr_email, usr_password_hash, usr_rol) VALUES
(1, 'Admin DelMX', 'admin@delmx.com', 'hashed_password_here', 'ADMIN'),
(2, 'Admin Trapido', 'admin@trapido.com', 'hashed_password_here', 'ADMIN'),
(3, 'Admin LoInt', 'admin@loint.com', 'hashed_password_here', 'ADMIN');

-- Datos de prueba: Choferes
INSERT INTO choferes (emp_id, cho_nombre, cho_apellido, cho_telefono, cho_estatus) VALUES
(1, 'TERESA', 'RAMIREZ', '5511111111', 'ACTIVO'),
(1, 'LAURA', 'HERNANDEZ', '5522222222', 'ACTIVO'),
(1, 'CARLOS', 'GARCIA', '5533333333', 'ACTIVO'),
(1, 'MARIA', 'RODRIGUEZ', '5544444444', 'ACTIVO'),
(1, 'JUAN', 'LOPEZ', '5555555555', 'ACTIVO'),
(2, 'PEDRO', 'SANCHEZ', '3311111111', 'ACTIVO'),
(2, 'ANA', 'MARTINEZ', '3322222222', 'ACTIVO'),
(3, 'FRANCISCO', 'DIAZ', '8111111111', 'ACTIVO'),
(3, 'SILVIA', 'TORRES', '8122222222', 'ACTIVO'),
(3, 'JOSE', 'GONZALEZ', '8133333333', 'ACTIVO');

-- Datos de prueba: Vehiculos
INSERT INTO vehiculos (emp_id, veh_unidad, veh_marca, veh_modelo, veh_anio, veh_tipo, veh_capacidad_kg, veh_estatus) VALUES
(1, 'W101', 'Renault', 'KANGOO', 2020, 'PICKUP', 150, 'ACTIVO'),
(1, 'W102', 'Nissan', 'NP300', 2021, 'PICKUP', 200, 'ACTIVO'),
(1, 'W103', 'Volkswagen', 'VENTO', 2022, 'SEDAN', 100, 'ACTIVO'),
(1, 'W104', 'Fiat', 'DUCATO', 2020, 'VAN', 500, 'ACTIVO'),
(2, 'T01', 'Chevrolet', 'S10', 2021, 'PICKUP', 180, 'ACTIVO'),
(3, 'L01', 'Ford', 'TRANSIT', 2022, 'VAN', 600, 'ACTIVO');

-- Datos de prueba: Clientes
INSERT INTO clientes (emp_id, cli_razon_social, cli_colonia, cli_ciudad, cli_estado, cli_cp, cli_telefono, cli_latitud, cli_longitud, cli_tipo_cliente) VALUES
(1, 'Cliente 1', 'POLANCO', 'CIUDAD DE MEXICO', 'CDMX', '11560', '5534990001', 19.4326, -99.1890, 'REGULAR'),
(1, 'Cliente 2', 'CONDESA', 'CIUDAD DE MEXICO', 'CDMX', '06140', '5534990002', 19.4126, -99.1790, 'PREMIUM'),
(1, 'Cliente 3', 'ROMA', 'CIUDAD DE MEXICO', 'CDMX', '06700', '5534990003', 19.4226, -99.1690, 'REGULAR'),
(1, 'Cliente 4', 'DEL VALLE', 'CIUDAD DE MEXICO', 'CDMX', '03100', '5534990004', 19.3926, -99.1790, 'REGULAR'),
(1, 'Cliente 5', 'CENTRO', 'CIUDAD DE MEXICO', 'CDMX', '06000', '5534990005', 19.4326, -99.1390, 'MAYORISTA');

-- Datos de prueba: Pedidos (20 de ejemplo)
INSERT INTO pedidos (emp_id, cli_id, ped_numero, ped_cliente_nombre, ped_cliente_telefono, ped_destino_dir, ped_destino_col, ped_destino_ciudad, ped_peso_kg, ped_bultos, ped_costo_total, ped_estado, ped_prioridad, chofer_asignado) VALUES
(1, 1, 'PED-000001', 'Cliente 1', '5534990001', 'Av Insurgentes 500', 'POLANCO', 'CDMX', 5, 3, 185.50, 'ENTREGADO', 'NORMAL', 'TERESA RAMIREZ'),
(1, 2, 'PED-000002', 'Cliente 2', '5534990002', 'Calle Amsterdam 30', 'CONDESA', 'CDMX', 2, 1, 92.10, 'ENTREGADO', 'NORMAL', 'LAURA HERNANDEZ'),
(1, 3, 'PED-000003', 'Cliente 3', '5534990003', 'Calle Orizaba 120', 'ROMA', 'CDMX', 8, 4, 245.00, 'EN_RUTA', 'ALTA', 'CARLOS GARCIA'),
(1, 4, 'PED-000004', 'Cliente 4', '5534990004', 'Av Universidad 800', 'DEL VALLE', 'CDMX', 3, 2, 135.75, 'EN_RUTA', 'NORMAL', 'MARIA RODRIGUEZ'),
(1, 5, 'PED-000005', 'Cliente 5', '5534990005', 'Calle Madero 200', 'CENTRO', 'CDMX', 15, 5, 420.00, 'PENDIENTE', 'URGENTE', NULL),
(1, 1, 'PED-000006', 'Cliente 1', '5534990001', 'Av Masaryk 400', 'POLANCO', 'CDMX', 1, 1, 89.00, 'PENDIENTE', 'NORMAL', NULL),
(1, 2, 'PED-000007', 'Cliente 2', '5534990002', 'Calle Tamaulipas 100', 'CONDESA', 'CDMX', 4, 2, 167.80, 'ENTREGADO', 'NORMAL', 'JUAN LOPEZ'),
(1, 3, 'PED-000008', 'Cliente 3', '5534990003', 'Calle Alvaro Obregon 50', 'ROMA', 'CDMX', 6, 3, 210.50, 'FALLIDO', 'NORMAL', 'TERESA RAMIREZ'),
(2, 1, 'PED-000009', 'Cliente A', '3311111111', 'Av Vallarta 500', 'CENTRO', 'GUADALAJARA', 10, 3, 310.00, 'ENTREGADO', 'NORMAL', 'PEDRO SANCHEZ'),
(2, 2, 'PED-000010', 'Cliente B', '3322222222', 'Calle Independencia 200', 'CENTRO', 'GUADALAJARA', 7, 2, 195.00, 'EN_RUTA', 'ALTA', 'ANA MARTINEZ');
SELECT setval('pedidos_ped_id_seq', 10);

-- Datos de prueba: Rutas
INSERT INTO rutas (emp_id, rut_nombre, rut_fecha, cho_id, veh_id, rut_total_pedidos, rut_total_entregas, rut_total_km, rut_costo_total) VALUES
(1, 'Ruta Polanco-Condesa', CURRENT_DATE, 1, 1, 5, 4, 45.5, 280.00),
(1, 'Ruta Roma-Del Valle', CURRENT_DATE, 2, 2, 4, 3, 38.2, 245.00),
(1, 'Ruta Centro', CURRENT_DATE, 3, 3, 6, 5, 22.1, 165.00),
(2, 'Ruta Centro GDL', CURRENT_DATE, 6, 5, 3, 2, 18.5, 140.00);

-- Datos de prueba: Cobros SaaS
INSERT INTO saas_cobros (sus_id, emp_id, cob_monto, cob_concepto, cob_estatus, cob_metodo_pago) VALUES
(1, 1, 2499.00, 'Mensualidad Plan Pro Julio 2026', 'PAGADO', 'MERCADOPAGO'),
(2, 2, 999.00, 'Mensualidad Plan Starter Julio 2026', 'PAGADO', 'SPEI');

-- Datos de prueba: Clientes finales (tracking)
INSERT INTO cliente_final (emp_id, ped_id, clif_nombre, clif_telefono, clif_email, clif_token_tracking) VALUES
(1, 3, 'Juan Perez Garcia', '5512345678', 'juan@email.com', 'tk_abc123def456'),
(1, 4, 'Maria Lopez', '5598765432', 'maria@email.com', 'tk_xyz789ghi012');

COMMENT ON DATABASE lastmile IS 'Last Mile Delivery Platform - SaaS para Mexico';
