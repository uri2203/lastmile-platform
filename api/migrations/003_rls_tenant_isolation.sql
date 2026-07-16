-- ========================================
-- ROW-LEVEL SECURITY (RLS) MIGRATION
-- Last Mile Delivery Platform
-- ========================================
-- Run this ONCE in Supabase SQL Editor
-- Enables RLS on all tenant tables with EMP_ID-based policies

-- ========================================
-- 1. ENABLE RLS ON ALL TABLES
-- ========================================
ALTER TABLE EMPRESAS ENABLE ROW LEVEL SECURITY;
ALTER TABLE USUARIOS ENABLE ROW LEVEL SECURITY;
ALTER TABLE CHOFERES ENABLE ROW LEVEL SECURITY;
ALTER TABLE VEHICULOS ENABLE ROW LEVEL SECURITY;
ALTER TABLE CLIENTES_LM ENABLE ROW LEVEL SECURITY;
ALTER TABLE PEDIDOS ENABLE ROW LEVEL SECURITY;
ALTER TABLE PEDIDO_HISTORIAL ENABLE ROW LEVEL SECURITY;
ALTER TABLE TRACKING ENABLE ROW LEVEL SECURITY;
ALTER TABLE TARIFAS ENABLE ROW LEVEL SECURITY;
ALTER TABLE ZONAS ENABLE ROW LEVEL SECURITY;
ALTER TABLE ZONA_TARIFAS ENABLE ROW LEVEL SECURITY;
ALTER TABLE PAGOS_TRANSACCIONES ENABLE ROW LEVEL SECURITY;
ALTER TABLE SAAS_PLANES ENABLE ROW LEVEL SECURITY;
ALTER TABLE SAAS_SUSCRIPCIONES ENABLE ROW LEVEL SECURITY;
ALTER TABLE SAAS_COBROS ENABLE ROW LEVEL SECURITY;
ALTER TABLE SAAS_USO_MES ENABLE ROW LEVEL SECURITY;
ALTER TABLE NOTIFICACIONES ENABLE ROW LEVEL SECURITY;
ALTER TABLE FACTURAS ENABLE ROW LEVEL SECURITY;
ALTER TABLE FACTURA_DETALLES ENABLE ROW LEVEL SECURITY;
ALTER TABLE TIMBRADO_LOG ENABLE ROW LEVEL SECURITY;
ALTER TABLE EMPRESA_FISCAL ENABLE ROW LEVEL SECURITY;
ALTER TABLE USO_CFDI ENABLE ROW LEVEL SECURITY;
ALTER TABLE RUTAS ENABLE ROW LEVEL SECURITY;
ALTER TABLE RUTA_PUNTOS ENABLE ROW LEVEL SECURITY;
ALTER TABLE INVENTARIO ENABLE ROW LEVEL SECURITY;
ALTER TABLE REPARTO ENABLE ROW LEVEL SECURITY;
ALTER TABLE COMISIONES ENABLE ROW LEVEL SECURITY;
ALTER TABLE NOMINA ENABLE ROW LEVEL SECURITY;
ALTER TABLE INCIDENCIAS ENABLE ROW LEVEL SECURITY;
ALTER TABLE CAPACITACIONES ENABLE ROW LEVEL SECURITY;
ALTER TABLE EVALUACIONES ENABLE ROW LEVEL SECURITY;
ALTER TABLE TAREAS ENABLE ROW LEVEL SECURITY;
ALTER TABLE MANTENIMIENTOS ENABLE ROW LEVEL SECURITY;
ALTER TABLE COMBUSTIBLE ENABLE ROW LEVEL SECURITY;
ALTER TABLE ACCESOS ENABLE ROW LEVEL SECURITY;
ALTER TABLE SESIONES ENABLE ROW LEVEL SECURITY;
ALTER TABLE AUDITORIA ENABLE ROW LEVEL SECURITY;
ALTER TABLE REPORTES ENABLE ROW LEVEL SECURITY;
ALTER TABLE CACHE ENABLE ROW LEVEL SECURITY;
ALTER TABLE CONFIGURACION ENABLE ROW LEVEL SECURITY;

-- ========================================
-- 2. SERVICE ROLE BYPASS POLICIES
-- The service_role key (used by backend) bypasses RLS
-- These policies ensure normal users CANNOT cross tenants
-- ========================================

-- ========================================
-- 3. TENANT-ISOLATION POLICIES
-- Each policy checks: current_setting('app.current_emp_id') = EMP_ID
-- ========================================

-- EMPRESAS - tenants can only see their own
CREATE POLICY IF NOT EXISTS tenant_isolation_empresas ON EMPRESAS
    FOR ALL USING (EMP_ID::text = current_setting('app.current_emp_id', true));

-- USUARIOS - tenant isolation via USU_EMP_ID
CREATE POLICY IF NOT EXISTS tenant_isolation_usuarios ON USUARIOS
    FOR ALL USING (USU_EMP_ID::text = current_setting('app.current_emp_id', true));

-- CHOFERES
CREATE POLICY IF NOT EXISTS tenant_isolation_choferes ON CHOFERES
    FOR ALL USING (EMP_ID::text = current_setting('app.current_emp_id', true));

-- VEHICULOS
CREATE POLICY IF NOT EXISTS tenant_isolation_vehiculos ON VEHICULOS
    FOR ALL USING (EMP_ID::text = current_setting('app.current_emp_id', true));

-- CLIENTES_LM
CREATE POLICY IF NOT EXISTS tenant_isolation_clientes ON CLIENTES_LM
    FOR ALL USING (EMP_ID::text = current_setting('app.current_emp_id', true));

-- PEDIDOS
CREATE POLICY IF NOT EXISTS tenant_isolation_pedidos ON PEDIDOS
    FOR ALL USING (EMP_ID::text = current_setting('app.current_emp_id', true));

-- PEDIDO_HISTORIAL (via PEDIDOS)
CREATE POLICY IF NOT EXISTS tenant_isolation_historial ON PEDIDO_HISTORIAL
    FOR ALL USING (
        PED_ID IN (SELECT PED_ID FROM PEDIDOS WHERE EMP_ID::text = current_setting('app.current_emp_id', true))
    );

-- TRACKING
CREATE POLICY IF NOT EXISTS tenant_isolation_tracking ON TRACKING
    FOR ALL USING (EMP_ID::text = current_setting('app.current_emp_id', true));

-- TARIFAS
CREATE POLICY IF NOT EXISTS tenant_isolation_tarifas ON TARIFAS
    FOR ALL USING (EMP_ID::text = current_setting('app.current_emp_id', true));

-- ZONAS
CREATE POLICY IF NOT EXISTS tenant_isolation_zonas ON ZONAS
    FOR ALL USING (ZON_EMP_ID::text = current_setting('app.current_emp_id', true));

-- ZONA_TARIFAS
CREATE POLICY IF NOT EXISTS tenant_isolation_zona_tarifas ON ZONA_TARIFAS
    FOR ALL USING (
        ZTA_ID IN (SELECT ZTA_ID FROM ZONAS WHERE ZON_EMP_ID::text = current_setting('app.current_emp_id', true))
    );

-- PAGOS_TRANSACCIONES
CREATE POLICY IF NOT EXISTS tenant_isolation_pagos ON PAGOS_TRANSACCIONES
    FOR ALL USING (EMP_ID::text = current_setting('app.current_emp_id', true));

-- SAAS tables (admin-only, but still isolated)
CREATE POLICY IF NOT EXISTS tenant_isolation_saas_suscripciones ON SAAS_SUSCRIPCIONES
    FOR ALL USING (EMP_ID::text = current_setting('app.current_emp_id', true));

CREATE POLICY IF NOT EXISTS tenant_isolation_saas_cobros ON SAAS_COBROS
    FOR ALL USING (EMP_ID::text = current_setting('app.current_emp_id', true));

CREATE POLICY IF NOT EXISTS tenant_isolation_saas_uso ON SAAS_USO_MES
    FOR ALL USING (EMP_ID::text = current_setting('app.current_emp_id', true));

-- NOTIFICACIONES
CREATE POLICY IF NOT EXISTS tenant_isolation_notificaciones ON NOTIFICACIONES
    FOR ALL USING (EMP_ID::text = current_setting('app.current_emp_id', true));

-- FACTURAS
CREATE POLICY IF NOT EXISTS tenant_isolation_facturas ON FACTURAS
    FOR ALL USING (EMP_ID::text = current_setting('app.current_emp_id', true));

-- FACTURA_DETALLES (via FACTURAS)
CREATE POLICY IF NOT EXISTS tenant_isolation_factura_detalles ON FACTURA_DETALLES
    FOR ALL USING (
        FAC_ID IN (SELECT FAC_ID FROM FACTURAS WHERE EMP_ID::text = current_setting('app.current_emp_id', true))
    );

-- TIMBRADO_LOG
CREATE POLICY IF NOT EXISTS tenant_isolation_timbrado ON TIMBRADO_LOG
    FOR ALL USING (EMP_ID::text = current_setting('app.current_emp_id', true));

-- EMPRESA_FISCAL
CREATE POLICY IF NOT EXISTS tenant_isolation_empresa_fiscal ON EMPRESA_FISCAL
    FOR ALL USING (EMP_ID::text = current_setting('app.current_emp_id', true));

-- USO_CFDI
CREATE POLICY IF NOT EXISTS tenant_isolation_uso_cfdi ON USO_CFDI
    FOR ALL USING (EMP_ID::text = current_setting('app.current_emp_id', true));

-- RUTAS
CREATE POLICY IF NOT EXISTS tenant_isolation_rutas ON RUTAS
    FOR ALL USING (EMP_ID::text = current_setting('app.current_emp_id', true));

-- RUTA_PUNTOS (via RUTAS)
CREATE POLICY IF NOT EXISTS tenant_isolation_ruta_puntos ON RUTA_PUNTOS
    FOR ALL USING (
        RUTA_ID IN (SELECT RUTA_ID FROM RUTAS WHERE EMP_ID::text = current_setting('app.current_emp_id', true))
    );

-- INVENTARIO
CREATE POLICY IF NOT EXISTS tenant_isolation_inventario ON INVENTARIO
    FOR ALL USING (EMP_ID::text = current_setting('app.current_emp_id', true));

-- REPARTO
CREATE POLICY IF NOT EXISTS tenant_isolation_reparto ON REPARTO
    FOR ALL USING (EMP_ID::text = current_setting('app.current_emp_id', true));

-- COMISIONES
CREATE POLICY IF NOT EXISTS tenant_isolation_comisiones ON COMISIONES
    FOR ALL USING (EMP_ID::text = current_setting('app.current_emp_id', true));

-- NOMINA
CREATE POLICY IF NOT EXISTS tenant_isolation_nomina ON NOMINA
    FOR ALL USING (EMP_ID::text = current_setting('app.current_emp_id', true));

-- INCIDENCIAS
CREATE POLICY IF NOT EXISTS tenant_isolation_incidencias ON INCIDENCIAS
    FOR ALL USING (EMP_ID::text = current_setting('app.current_emp_id', true));

-- CAPACITACIONES
CREATE POLICY IF NOT EXISTS tenant_isolation_capacitaciones ON CAPACITACIONES
    FOR ALL USING (EMP_ID::text = current_setting('app.current_emp_id', true));

-- EVALUACIONES
CREATE POLICY IF NOT EXISTS tenant_isolation_evaluaciones ON EVALUACIONES
    FOR ALL USING (EMP_ID::text = current_setting('app.current_emp_id', true));

-- TAREAS
CREATE POLICY IF NOT EXISTS tenant_isolation_tareas ON TAREAS
    FOR ALL USING (EMP_ID::text = current_setting('app.current_emp_id', true));

-- MANTENIMIENTOS
CREATE POLICY IF NOT EXISTS tenant_isolation_mantenimientos ON MANTENIMIENTOS
    FOR ALL USING (EMP_ID::text = current_setting('app.current_emp_id', true));

-- COMBUSTIBLE
CREATE POLICY IF NOT EXISTS tenant_isolation_combustible ON COMBUSTIBLE
    FOR ALL USING (EMP_ID::text = current_setting('app.current_emp_id', true));

-- ACCESOS
CREATE POLICY IF NOT EXISTS tenant_isolation_accesos ON ACCESOS
    FOR ALL USING (EMP_ID::text = current_setting('app.current_emp_id', true));

-- SESIONES
CREATE POLICY IF NOT EXISTS tenant_isolation_sesiones ON SESIONES
    FOR ALL USING (EMP_ID::text = current_setting('app.current_emp_id', true));

-- AUDITORIA
CREATE POLICY IF NOT EXISTS tenant_isolation_auditoria ON AUDITORIA
    FOR ALL USING (EMP_ID::text = current_setting('app.current_emp_id', true));

-- REPORTES
CREATE POLICY IF NOT EXISTS tenant_isolation_reportes ON REPORTES
    FOR ALL USING (EMP_ID::text = current_setting('app.current_emp_id', true));

-- CONFIGURACION
CREATE POLICY IF NOT EXISTS tenant_isolation_configuracion ON CONFIGURACION
    FOR ALL USING (EMP_ID::text = current_setting('app.current_emp_id', true));

-- ========================================
-- 4. SAAS_PLANES - public read (all tenants see plans)
-- ========================================
CREATE POLICY IF NOT EXISTS plans_public_read ON SAAS_PLANES
    FOR SELECT USING (PLAN_ACTIVO = 'S');

-- ========================================
-- DONE
-- ========================================
