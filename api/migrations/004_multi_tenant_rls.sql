-- ========================================
-- MULTI-TENANT RLS - COMPLETE MIGRATION
-- Last Mile Delivery Platform
-- ========================================
-- Ejecutar UNA VEZ en Supabase SQL Editor
-- Extiende y completa la migracion 003_rls_tenant_isolation.sql
-- Cubre TODAS las tablas del schema con RLS completo
-- ========================================
-- REQUISITOS PREVIOS:
--   - Migracion 003_rls_tenant_isolation.sql ejecutada
--   - Todas las tablas del schema_postgres.sql creadas
-- ========================================

-- ========================================
-- 0. FUNCIONES AUXILIARES
-- ========================================

-- Funcion para establecer el tenant actual en la sesion PostgreSQL
CREATE OR REPLACE FUNCTION set_current_tenant(tenant_id INT)
RETURNS VOID AS 
BEGIN
  PERFORM set_config('app.current_emp_id', tenant_id::text, true);
END;
 LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION set_current_tenant(INT) IS
  'Establece el tenant (empresa) actual para RLS. Llamar antes de cada operacion.';

-- Funcion trigger para auto-establecer EMP_ID en INSERT
CREATE OR REPLACE FUNCTION auto_set_tenant_on_insert()
RETURNS TRIGGER AS 
BEGIN
  IF NEW.EMP_ID IS NULL THEN
    NEW.EMP_ID := current_setting('app.current_emp_id', true)::int;
  END IF;
  RETURN NEW;
END;
 LANGUAGE plpgsql SECURITY DEFINER;

-- Funcion trigger para prevenir cambio de tenant en UPDATE
CREATE OR REPLACE FUNCTION prevent_tenant_change()
RETURNS TRIGGER AS 
BEGIN
  IF NEW.EMP_ID IS DISTINCT FROM OLD.EMP_ID THEN
    RAISE EXCEPTION 'No se permite cambiar el tenant (EMP_ID) de un registro';
  END IF;
  RETURN NEW;
END;
 LANGUAGE plpgsql SECURITY DEFINER;

-- ========================================
-- 1. ASEGURAR COLUMNA EMP_ID EN TABLAS
-- ========================================

ALTER TABLE CFDI_TIMBRADO_LOG
  ADD COLUMN IF NOT EXISTS EMP_ID INTEGER;

-- ========================================
-- 2. HABILITAR RLS EN TODAS LAS TABLAS
-- ========================================

ALTER TABLE EMPRESAS ENABLE ROW LEVEL SECURITY;
ALTER TABLE USUARIOS ENABLE ROW LEVEL SECURITY;
ALTER TABLE CHOFERES ENABLE ROW LEVEL SECURITY;
ALTER TABLE VEHICULOS ENABLE ROW LEVEL SECURITY;
ALTER TABLE CLIENTES_LM ENABLE ROW LEVEL SECURITY;
ALTER TABLE PEDIDOS ENABLE ROW LEVEL SECURITY;
ALTER TABLE PEDIDO_HISTORIAL ENABLE ROW LEVEL SECURITY;
ALTER TABLE TRACKING ENABLE ROW LEVEL SECURITY;
ALTER TABLE ZONAS ENABLE ROW LEVEL SECURITY;
ALTER TABLE ZONA_TARIFAS ENABLE ROW LEVEL SECURITY;
ALTER TABLE CFDI_EMPRESA_FISCAL ENABLE ROW LEVEL SECURITY;
ALTER TABLE CFDI_FOLIOS ENABLE ROW LEVEL SECURITY;
ALTER TABLE CFDI_FACTURAS ENABLE ROW LEVEL SECURITY;
ALTER TABLE CFDI_TIMBRADO_LOG ENABLE ROW LEVEL SECURITY;
ALTER TABLE CFDI_CONCEPTOS_CATALOGO ENABLE ROW LEVEL SECURITY;
ALTER TABLE PAGOS_METODOS ENABLE ROW LEVEL SECURITY;
ALTER TABLE PAGOS_TRANSACCIONES ENABLE ROW LEVEL SECURITY;
ALTER TABLE NOTIF_PUSH ENABLE ROW LEVEL SECURITY;
ALTER TABLE NOTIF_DISPOSITIVOS ENABLE ROW LEVEL SECURITY;
ALTER TABLE EMAIL_ENVIADOS ENABLE ROW LEVEL SECURITY;
ALTER TABLE SMS_ENVIADOS ENABLE ROW LEVEL SECURITY;
ALTER TABLE AUDIT_LOG ENABLE ROW LEVEL SECURITY;
ALTER TABLE REPORTES_GENERADOS ENABLE ROW LEVEL SECURITY;
ALTER TABLE ENTREGAS ENABLE ROW LEVEL SECURITY;
ALTER TABLE INCIDENCIAS ENABLE ROW LEVEL SECURITY;
ALTER TABLE KPI_DIARIO ENABLE ROW LEVEL SECURITY;
ALTER TABLE CLIENTE_FINAL ENABLE ROW LEVEL SECURITY;
ALTER TABLE SAAS_PLANES ENABLE ROW LEVEL SECURITY;
ALTER TABLE SAAS_SUSCRIPCIONES ENABLE ROW LEVEL SECURITY;
ALTER TABLE SAAS_COBROS ENABLE ROW LEVEL SECURITY;
ALTER TABLE SAAS_USO_RECURSOS ENABLE ROW LEVEL SECURITY;
ALTER TABLE SAAS_USO_MES ENABLE ROW LEVEL SECURITY;
ALTER TABLE LEGAL_ACCEPTANCE ENABLE ROW LEVEL SECURITY;
ALTER TABLE REFERRALS ENABLE ROW LEVEL SECURITY;
ALTER TABLE TENANT_FISCAL_CONFIG ENABLE ROW LEVEL SECURITY;
ALTER TABLE TENANT_FISCAL_DATA ENABLE ROW LEVEL SECURITY;
ALTER TABLE FISCAL_DOCUMENTS ENABLE ROW LEVEL SECURITY;

-- ========================================
-- 3. POLITICAS DE AISLAMIENTO POR TENANT
-- ========================================
-- Cada tabla tiene una politica que compara EMP_ID con la variable de sesion.
-- service_role (backend) bypasea RLS automaticamente.
-- usuarios normales solo ven registros de su propio tenant.

-- EMPRESAS
DROP POLICY IF EXISTS tenant_isolation_empresas ON EMPRESAS;
CREATE POLICY tenant_isolation_empresas ON EMPRESAS
  FOR ALL USING (EMP_ID::text = current_setting('app.current_emp_id', true));

-- USUARIOS (via USU_EMP_ID)
DROP POLICY IF EXISTS tenant_isolation_usuarios ON USUARIOS;
CREATE POLICY tenant_isolation_usuarios ON USUARIOS
  FOR ALL USING (USU_EMP_ID::text = current_setting('app.current_emp_id', true));

-- CHOFERES
DROP POLICY IF EXISTS tenant_isolation_choferes ON CHOFERES;
CREATE POLICY tenant_isolation_choferes ON CHOFERES
  FOR ALL USING (EMP_ID::text = current_setting('app.current_emp_id', true));

-- VEHICULOS
DROP POLICY IF EXISTS tenant_isolation_vehiculos ON VEHICULOS;
CREATE POLICY tenant_isolation_vehiculos ON VEHICULOS
  FOR ALL USING (EMP_ID::text = current_setting('app.current_emp_id', true));

-- CLIENTES_LM
DROP POLICY IF EXISTS tenant_isolation_clientes ON CLIENTES_LM;
CREATE POLICY tenant_isolation_clientes ON CLIENTES_LM
  FOR ALL USING (EMP_ID::text = current_setting('app.current_emp_id', true));

-- PEDIDOS
DROP POLICY IF EXISTS tenant_isolation_pedidos ON PEDIDOS;
CREATE POLICY tenant_isolation_pedidos ON PEDIDOS
  FOR ALL USING (EMP_ID::text = current_setting('app.current_emp_id', true));

-- PEDIDO_HISTORIAL (via subquery a PEDIDOS)
DROP POLICY IF EXISTS tenant_isolation_historial ON PEDIDO_HISTORIAL;
CREATE POLICY tenant_isolation_historial ON PEDIDO_HISTORIAL
  FOR ALL USING (
    PED_ID IN (
      SELECT PED_ID FROM PEDIDOS
      WHERE EMP_ID::text = current_setting('app.current_emp_id', true)
    )
  );

-- TRACKING
DROP POLICY IF EXISTS tenant_isolation_tracking ON TRACKING;
CREATE POLICY tenant_isolation_tracking ON TRACKING
  FOR ALL USING (EMP_ID::text = current_setting('app.current_emp_id', true));

-- ZONAS (via ZON_EMP_ID)
DROP POLICY IF EXISTS tenant_isolation_zonas ON ZONAS;
CREATE POLICY tenant_isolation_zonas ON ZONAS
  FOR ALL USING (ZON_EMP_ID::text = current_setting('app.current_emp_id', true));

-- ZONA_TARIFAS (via subquery a ZONAS)
DROP POLICY IF EXISTS tenant_isolation_zona_tarifas ON ZONA_TARIFAS;
CREATE POLICY tenant_isolation_zona_tarifas ON ZONA_TARIFAS
  FOR ALL USING (
    ZTA_ZON_ID IN (
      SELECT ZON_ID FROM ZONAS
      WHERE ZON_EMP_ID::text = current_setting('app.current_emp_id', true)
    )
  );

-- CFDI_EMPRESA_FISCAL
DROP POLICY IF EXISTS tenant_isolation_cfdi_empresa_fiscal ON CFDI_EMPRESA_FISCAL;
CREATE POLICY tenant_isolation_cfdi_empresa_fiscal ON CFDI_EMPRESA_FISCAL
  FOR ALL USING (EMP_ID::text = current_setting('app.current_emp_id', true));

-- CFDI_FOLIOS
DROP POLICY IF EXISTS tenant_isolation_cfdi_folios ON CFDI_FOLIOS;
CREATE POLICY tenant_isolation_cfdi_folios ON CFDI_FOLIOS
  FOR ALL USING (EMP_ID::text = current_setting('app.current_emp_id', true));

-- CFDI_FACTURAS
DROP POLICY IF EXISTS tenant_isolation_cfdi_facturas ON CFDI_FACTURAS;
CREATE POLICY tenant_isolation_cfdi_facturas ON CFDI_FACTURAS
  FOR ALL USING (EMP_ID::text = current_setting('app.current_emp_id', true));

-- CFDI_TIMBRADO_LOG (doble acceso: EMP_ID directo O via FAC_ID)
DROP POLICY IF EXISTS tenant_isolation_cfdi_timbrado ON CFDI_TIMBRADO_LOG;
CREATE POLICY tenant_isolation_cfdi_timbrado ON CFDI_TIMBRADO_LOG
  FOR ALL USING (
    EMP_ID::text = current_setting('app.current_emp_id', true)
    OR
    FAC_ID IN (
      SELECT FAC_ID FROM CFDI_FACTURAS
      WHERE EMP_ID::text = current_setting('app.current_emp_id', true)
    )
  );

-- CFDI_CONCEPTOS_CATALOGO
DROP POLICY IF EXISTS tenant_isolation_cfdi_conceptos ON CFDI_CONCEPTOS_CATALOGO;
CREATE POLICY tenant_isolation_cfdi_conceptos ON CFDI_CONCEPTOS_CATALOGO
  FOR ALL USING (EMP_ID::text = current_setting('app.current_emp_id', true));

-- PAGOS_METODOS
DROP POLICY IF EXISTS tenant_isolation_pagos_metodos ON PAGOS_METODOS;
CREATE POLICY tenant_isolation_pagos_metodos ON PAGOS_METODOS
  FOR ALL USING (EMP_ID::text = current_setting('app.current_emp_id', true));

-- PAGOS_TRANSACCIONES
DROP POLICY IF EXISTS tenant_isolation_pagos ON PAGOS_TRANSACCIONES;
CREATE POLICY tenant_isolation_pagos ON PAGOS_TRANSACCIONES
  FOR ALL USING (EMP_ID::text = current_setting('app.current_emp_id', true));

-- NOTIF_PUSH
DROP POLICY IF EXISTS tenant_isolation_notif_push ON NOTIF_PUSH;
CREATE POLICY tenant_isolation_notif_push ON NOTIF_PUSH
  FOR ALL USING (EMP_ID::text = current_setting('app.current_emp_id', true));

-- NOTIF_DISPOSITIVOS
DROP POLICY IF EXISTS tenant_isolation_notif_dispositivos ON NOTIF_DISPOSITIVOS;
CREATE POLICY tenant_isolation_notif_dispositivos ON NOTIF_DISPOSITIVOS
  FOR ALL USING (EMP_ID::text = current_setting('app.current_emp_id', true));

-- EMAIL_ENVIADOS
DROP POLICY IF EXISTS tenant_isolation_email ON EMAIL_ENVIADOS;
CREATE POLICY tenant_isolation_email ON EMAIL_ENVIADOS
  FOR ALL USING (EMP_ID::text = current_setting('app.current_emp_id', true));

-- SMS_ENVIADOS
DROP POLICY IF EXISTS tenant_isolation_sms ON SMS_ENVIADOS;
CREATE POLICY tenant_isolation_sms ON SMS_ENVIADOS
  FOR ALL USING (EMP_ID::text = current_setting('app.current_emp_id', true));

-- AUDIT_LOG
DROP POLICY IF EXISTS tenant_isolation_audit_log ON AUDIT_LOG;
CREATE POLICY tenant_isolation_audit_log ON AUDIT_LOG
  FOR ALL USING (EMP_ID::text = current_setting('app.current_emp_id', true));

-- REPORTES_GENERADOS
DROP POLICY IF EXISTS tenant_isolation_reportes ON REPORTES_GENERADOS;
CREATE POLICY tenant_isolation_reportes ON REPORTES_GENERADOS
  FOR ALL USING (EMP_ID::text = current_setting('app.current_emp_id', true));

-- ENTREGAS
DROP POLICY IF EXISTS tenant_isolation_entregas ON ENTREGAS;
CREATE POLICY tenant_isolation_entregas ON ENTREGAS
  FOR ALL USING (EMP_ID::text = current_setting('app.current_emp_id', true));

-- INCIDENCIAS
DROP POLICY IF EXISTS tenant_isolation_incidencias ON INCIDENCIAS;
CREATE POLICY tenant_isolation_incidencias ON INCIDENCIAS
  FOR ALL USING (EMP_ID::text = current_setting('app.current_emp_id', true));

-- KPI_DIARIO
DROP POLICY IF EXISTS tenant_isolation_kpi ON KPI_DIARIO;
CREATE POLICY tenant_isolation_kpi ON KPI_DIARIO
  FOR ALL USING (EMP_ID::text = current_setting('app.current_emp_id', true));

-- CLIENTE_FINAL
DROP POLICY IF EXISTS tenant_isolation_cliente_final ON CLIENTE_FINAL;
CREATE POLICY tenant_isolation_cliente_final ON CLIENTE_FINAL
  FOR ALL USING (EMP_ID::text = current_setting('app.current_emp_id', true));

-- SAAS_PLANES: lectura publica para todos los tenants
DROP POLICY IF EXISTS tenant_isolation_saas_planes ON SAAS_PLANES;
CREATE POLICY tenant_isolation_saas_planes ON SAAS_PLANES
  FOR SELECT USING (PLAN_ACTIVO = 'S');

-- SAAS_SUSCRIPCIONES
DROP POLICY IF EXISTS tenant_isolation_saas_suscripciones ON SAAS_SUSCRIPCIONES;
CREATE POLICY tenant_isolation_saas_suscripciones ON SAAS_SUSCRIPCIONES
  FOR ALL USING (EMP_ID::text = current_setting('app.current_emp_id', true));

-- SAAS_COBROS
DROP POLICY IF EXISTS tenant_isolation_saas_cobros ON SAAS_COBROS;
CREATE POLICY tenant_isolation_saas_cobros ON SAAS_COBROS
  FOR ALL USING (EMP_ID::text = current_setting('app.current_emp_id', true));

-- SAAS_USO_RECURSOS
DROP POLICY IF EXISTS tenant_isolation_saas_uso_recursos ON SAAS_USO_RECURSOS;
CREATE POLICY tenant_isolation_saas_uso_recursos ON SAAS_USO_RECURSOS
  FOR ALL USING (EMP_ID::text = current_setting('app.current_emp_id', true));

-- SAAS_USO_MES
DROP POLICY IF EXISTS tenant_isolation_saas_uso_mes ON SAAS_USO_MES;
CREATE POLICY tenant_isolation_saas_uso_mes ON SAAS_USO_MES
  FOR ALL USING (EMP_ID::text = current_setting('app.current_emp_id', true));

-- LEGAL_ACCEPTANCE
DROP POLICY IF EXISTS tenant_isolation_legal ON LEGAL_ACCEPTANCE;
CREATE POLICY tenant_isolation_legal ON LEGAL_ACCEPTANCE
  FOR ALL USING (EMP_ID::text = current_setting('app.current_emp_id', true));

-- REFERRALS (ambas columnas son tenants)
DROP POLICY IF EXISTS tenant_isolation_referrals ON REFERRALS;
CREATE POLICY tenant_isolation_referrals ON REFERRALS
  FOR ALL USING (
    REF_REFERRER_EMP_ID::text = current_setting('app.current_emp_id', true)
    OR
    REFREFERRED_EMP_ID::text = current_setting('app.current_emp_id', true)
  );

-- TENANT_FISCAL_CONFIG
DROP POLICY IF EXISTS tenant_isolation_fiscal_config ON TENANT_FISCAL_CONFIG;
CREATE POLICY tenant_isolation_fiscal_config ON TENANT_FISCAL_CONFIG
  FOR ALL USING (EMP_ID::text = current_setting('app.current_emp_id', true));

-- TENANT_FISCAL_DATA
DROP POLICY IF EXISTS tenant_isolation_fiscal_data ON TENANT_FISCAL_DATA;
CREATE POLICY tenant_isolation_fiscal_data ON TENANT_FISCAL_DATA
  FOR ALL USING (EMP_ID::text = current_setting('app.current_emp_id', true));

-- FISCAL_DOCUMENTS
DROP POLICY IF EXISTS tenant_isolation_fiscal_docs ON FISCAL_DOCUMENTS;
CREATE POLICY tenant_isolation_fiscal_docs ON FISCAL_DOCUMENTS
  FOR ALL USING (EMP_ID::text = current_setting('app.current_emp_id', true));

-- ========================================
-- 4. TRIGGERS AUTO-SET TENANT
-- ========================================
-- BEFORE INSERT: rellena EMP_ID desde la sesion si es NULL
-- BEFORE UPDATE: previene cambio de EMP_ID (anti-escape)

-- PEDIDOS
DROP TRIGGER IF EXISTS trg_auto_tenant_pedidos ON PEDIDOS;
CREATE TRIGGER trg_auto_tenant_pedidos
  BEFORE INSERT ON PEDIDOS
  FOR EACH ROW EXECUTE FUNCTION auto_set_tenant_on_insert();

DROP TRIGGER IF EXISTS trg_protect_tenant_pedidos ON PEDIDOS;
CREATE TRIGGER trg_protect_tenant_pedidos
  BEFORE UPDATE ON PEDIDOS
  FOR EACH ROW EXECUTE FUNCTION prevent_tenant_change();

-- CHOFERES
DROP TRIGGER IF EXISTS trg_auto_tenant_choferes ON CHOFERES;
CREATE TRIGGER trg_auto_tenant_choferes
  BEFORE INSERT ON CHOFERES
  FOR EACH ROW EXECUTE FUNCTION auto_set_tenant_on_insert();

DROP TRIGGER IF EXISTS trg_protect_tenant_choferes ON CHOFERES;
CREATE TRIGGER trg_protect_tenant_choferes
  BEFORE UPDATE ON CHOFERES
  FOR EACH ROW EXECUTE FUNCTION prevent_tenant_change();

-- VEHICULOS
DROP TRIGGER IF EXISTS trg_auto_tenant_vehiculos ON VEHICULOS;
CREATE TRIGGER trg_auto_tenant_vehiculos
  BEFORE INSERT ON VEHICULOS
  FOR EACH ROW EXECUTE FUNCTION auto_set_tenant_on_insert();

DROP TRIGGER IF EXISTS trg_protect_tenant_vehiculos ON VEHICULOS;
CREATE TRIGGER trg_protect_tenant_vehiculos
  BEFORE UPDATE ON VEHICULOS
  FOR EACH ROW EXECUTE FUNCTION prevent_tenant_change();

-- CLIENTES_LM
DROP TRIGGER IF EXISTS trg_auto_tenant_clientes ON CLIENTES_LM;
CREATE TRIGGER trg_auto_tenant_clientes
  BEFORE INSERT ON CLIENTES_LM
  FOR EACH ROW EXECUTE FUNCTION auto_set_tenant_on_insert();

DROP TRIGGER IF EXISTS trg_protect_tenant_clientes ON CLIENTES_LM;
CREATE TRIGGER trg_protect_tenant_clientes
  BEFORE UPDATE ON CLIENTES_LM
  FOR EACH ROW EXECUTE FUNCTION prevent_tenant_change();

-- TRACKING
DROP TRIGGER IF EXISTS trg_auto_tenant_tracking ON TRACKING;
CREATE TRIGGER trg_auto_tenant_tracking
  BEFORE INSERT ON TRACKING
  FOR EACH ROW EXECUTE FUNCTION auto_set_tenant_on_insert();

DROP TRIGGER IF EXISTS trg_protect_tenant_tracking ON TRACKING;
CREATE TRIGGER trg_protect_tenant_tracking
  BEFORE UPDATE ON TRACKING
  FOR EACH ROW EXECUTE FUNCTION prevent_tenant_change();

-- ZONAS
DROP TRIGGER IF EXISTS trg_auto_tenant_zonas ON ZONAS;
CREATE TRIGGER trg_auto_tenant_zonas
  BEFORE INSERT ON ZONAS
  FOR EACH ROW EXECUTE FUNCTION auto_set_tenant_on_insert();

DROP TRIGGER IF EXISTS trg_protect_tenant_zonas ON ZONAS;
CREATE TRIGGER trg_protect_tenant_zonas
  BEFORE UPDATE ON ZONAS
  FOR EACH ROW EXECUTE FUNCTION prevent_tenant_change();

-- ZONA_TARIFAS
DROP TRIGGER IF EXISTS trg_auto_tenant_zona_tarifas ON ZONA_TARIFAS;
CREATE TRIGGER trg_auto_tenant_zona_tarifas
  BEFORE INSERT ON ZONA_TARIFAS
  FOR EACH ROW EXECUTE FUNCTION auto_set_tenant_on_insert();

DROP TRIGGER IF EXISTS trg_protect_tenant_zona_tarifas ON ZONA_TARIFAS;
CREATE TRIGGER trg_protect_tenant_zona_tarifas
  BEFORE UPDATE ON ZONA_TARIFAS
  FOR EACH ROW EXECUTE FUNCTION prevent_tenant_change();

-- CFDI_FACTURAS
DROP TRIGGER IF EXISTS trg_auto_tenant_cfdi_facturas ON CFDI_FACTURAS;
CREATE TRIGGER trg_auto_tenant_cfdi_facturas
  BEFORE INSERT ON CFDI_FACTURAS
  FOR EACH ROW EXECUTE FUNCTION auto_set_tenant_on_insert();

DROP TRIGGER IF EXISTS trg_protect_tenant_cfdi_facturas ON CFDI_FACTURAS;
CREATE TRIGGER trg_protect_tenant_cfdi_facturas
  BEFORE UPDATE ON CFDI_FACTURAS
  FOR EACH ROW EXECUTE FUNCTION prevent_tenant_change();

-- CFDI_FOLIOS
DROP TRIGGER IF EXISTS trg_auto_tenant_cfdi_folios ON CFDI_FOLIOS;
CREATE TRIGGER trg_auto_tenant_cfdi_folios
  BEFORE INSERT ON CFDI_FOLIOS
  FOR EACH ROW EXECUTE FUNCTION auto_set_tenant_on_insert();

DROP TRIGGER IF EXISTS trg_protect_tenant_cfdi_folios ON CFDI_FOLIOS;
CREATE TRIGGER trg_protect_tenant_cfdi_folios
  BEFORE UPDATE ON CFDI_FOLIOS
  FOR EACH ROW EXECUTE FUNCTION prevent_tenant_change();

-- CFDI_CONCEPTOS_CATALOGO
DROP TRIGGER IF EXISTS trg_auto_tenant_cfdi_conceptos ON CFDI_CONCEPTOS_CATALOGO;
CREATE TRIGGER trg_auto_tenant_cfdi_conceptos
  BEFORE INSERT ON CFDI_CONCEPTOS_CATALOGO
  FOR EACH ROW EXECUTE FUNCTION auto_set_tenant_on_insert();

DROP TRIGGER IF EXISTS trg_protect_tenant_cfdi_conceptos ON CFDI_CONCEPTOS_CATALOGO;
CREATE TRIGGER trg_protect_tenant_cfdi_conceptos
  BEFORE UPDATE ON CFDI_CONCEPTOS_CATALOGO
  FOR EACH ROW EXECUTE FUNCTION prevent_tenant_change();

-- PAGOS_METODOS
DROP TRIGGER IF EXISTS trg_auto_tenant_pagos_metodos ON PAGOS_METODOS;
CREATE TRIGGER trg_auto_tenant_pagos_metodos
  BEFORE INSERT ON PAGOS_METODOS
  FOR EACH ROW EXECUTE FUNCTION auto_set_tenant_on_insert();

DROP TRIGGER IF EXISTS trg_protect_tenant_pagos_metodos ON PAGOS_METODOS;
CREATE TRIGGER trg_protect_tenant_pagos_metodos
  BEFORE UPDATE ON PAGOS_METODOS
  FOR EACH ROW EXECUTE FUNCTION prevent_tenant_change();

-- PAGOS_TRANSACCIONES
DROP TRIGGER IF EXISTS trg_auto_tenant_pagos ON PAGOS_TRANSACCIONES;
CREATE TRIGGER trg_auto_tenant_pagos
  BEFORE INSERT ON PAGOS_TRANSACCIONES
  FOR EACH ROW EXECUTE FUNCTION auto_set_tenant_on_insert();

DROP TRIGGER IF EXISTS trg_protect_tenant_pagos ON PAGOS_TRANSACCIONES;
CREATE TRIGGER trg_protect_tenant_pagos
  BEFORE UPDATE ON PAGOS_TRANSACCIONES
  FOR EACH ROW EXECUTE FUNCTION prevent_tenant_change();

-- NOTIF_PUSH
DROP TRIGGER IF EXISTS trg_auto_tenant_notif_push ON NOTIF_PUSH;
CREATE TRIGGER trg_auto_tenant_notif_push
  BEFORE INSERT ON NOTIF_PUSH
  FOR EACH ROW EXECUTE FUNCTION auto_set_tenant_on_insert();

DROP TRIGGER IF EXISTS trg_protect_tenant_notif_push ON NOTIF_PUSH;
CREATE TRIGGER trg_protect_tenant_notif_push
  BEFORE UPDATE ON NOTIF_PUSH
  FOR EACH ROW EXECUTE FUNCTION prevent_tenant_change();

-- NOTIF_DISPOSITIVOS
DROP TRIGGER IF EXISTS trg_auto_tenant_notif_disp ON NOTIF_DISPOSITIVOS;
CREATE TRIGGER trg_auto_tenant_notif_disp
  BEFORE INSERT ON NOTIF_DISPOSITIVOS
  FOR EACH ROW EXECUTE FUNCTION auto_set_tenant_on_insert();

DROP TRIGGER IF EXISTS trg_protect_tenant_notif_disp ON NOTIF_DISPOSITIVOS;
CREATE TRIGGER trg_protect_tenant_notif_disp
  BEFORE UPDATE ON NOTIF_DISPOSITIVOS
  FOR EACH ROW EXECUTE FUNCTION prevent_tenant_change();

-- EMAIL_ENVIADOS
DROP TRIGGER IF EXISTS trg_auto_tenant_email ON EMAIL_ENVIADOS;
CREATE TRIGGER trg_auto_tenant_email
  BEFORE INSERT ON EMAIL_ENVIADOS
  FOR EACH ROW EXECUTE FUNCTION auto_set_tenant_on_insert();

DROP TRIGGER IF EXISTS trg_protect_tenant_email ON EMAIL_ENVIADOS;
CREATE TRIGGER trg_protect_tenant_email
  BEFORE UPDATE ON EMAIL_ENVIADOS
  FOR EACH ROW EXECUTE FUNCTION prevent_tenant_change();

-- SMS_ENVIADOS
DROP TRIGGER IF EXISTS trg_auto_tenant_sms ON SMS_ENVIADOS;
CREATE TRIGGER trg_auto_tenant_sms
  BEFORE INSERT ON SMS_ENVIADOS
  FOR EACH ROW EXECUTE FUNCTION auto_set_tenant_on_insert();

DROP TRIGGER IF EXISTS trg_protect_tenant_sms ON SMS_ENVIADOS;
CREATE TRIGGER trg_protect_tenant_sms
  BEFORE UPDATE ON SMS_ENVIADOS
  FOR EACH ROW EXECUTE FUNCTION prevent_tenant_change();

-- AUDIT_LOG
DROP TRIGGER IF EXISTS trg_auto_tenant_audit ON AUDIT_LOG;
CREATE TRIGGER trg_auto_tenant_audit
  BEFORE INSERT ON AUDIT_LOG
  FOR EACH ROW EXECUTE FUNCTION auto_set_tenant_on_insert();

DROP TRIGGER IF EXISTS trg_protect_tenant_audit ON AUDIT_LOG;
CREATE TRIGGER trg_protect_tenant_audit
  BEFORE UPDATE ON AUDIT_LOG
  FOR EACH ROW EXECUTE FUNCTION prevent_tenant_change();

-- REPORTES_GENERADOS
DROP TRIGGER IF EXISTS trg_auto_tenant_reportes ON REPORTES_GENERADOS;
CREATE TRIGGER trg_auto_tenant_reportes
  BEFORE INSERT ON REPORTES_GENERADOS
  FOR EACH ROW EXECUTE FUNCTION auto_set_tenant_on_insert();

DROP TRIGGER IF EXISTS trg_protect_tenant_reportes ON REPORTES_GENERADOS;
CREATE TRIGGER trg_protect_tenant_reportes
  BEFORE UPDATE ON REPORTES_GENERADOS
  FOR EACH ROW EXECUTE FUNCTION prevent_tenant_change();

-- ENTREGAS
DROP TRIGGER IF EXISTS trg_auto_tenant_entregas ON ENTREGAS;
CREATE TRIGGER trg_auto_tenant_entregas
  BEFORE INSERT ON ENTREGAS
  FOR EACH ROW EXECUTE FUNCTION auto_set_tenant_on_insert();

DROP TRIGGER IF EXISTS trg_protect_tenant_entregas ON ENTREGAS;
CREATE TRIGGER trg_protect_tenant_entregas
  BEFORE UPDATE ON ENTREGAS
  FOR EACH ROW EXECUTE FUNCTION prevent_tenant_change();

-- INCIDENCIAS
DROP TRIGGER IF EXISTS trg_auto_tenant_incidencias ON INCIDENCIAS;
CREATE TRIGGER trg_auto_tenant_incidencias
  BEFORE INSERT ON INCIDENCIAS
  FOR EACH ROW EXECUTE FUNCTION auto_set_tenant_on_insert();

DROP TRIGGER IF EXISTS trg_protect_tenant_incidencias ON INCIDENCIAS;
CREATE TRIGGER trg_protect_tenant_incidencias
  BEFORE UPDATE ON INCIDENCIAS
  FOR EACH ROW EXECUTE FUNCTION prevent_tenant_change();

-- KPI_DIARIO
DROP TRIGGER IF EXISTS trg_auto_tenant_kpi ON KPI_DIARIO;
CREATE TRIGGER trg_auto_tenant_kpi
  BEFORE INSERT ON KPI_DIARIO
  FOR EACH ROW EXECUTE FUNCTION auto_set_tenant_on_insert();

DROP TRIGGER IF EXISTS trg_protect_tenant_kpi ON KPI_DIARIO;
CREATE TRIGGER trg_protect_tenant_kpi
  BEFORE UPDATE ON KPI_DIARIO
  FOR EACH ROW EXECUTE FUNCTION prevent_tenant_change();

-- CLIENTE_FINAL
DROP TRIGGER IF EXISTS trg_auto_tenant_cliente_final ON CLIENTE_FINAL;
CREATE TRIGGER trg_auto_tenant_cliente_final
  BEFORE INSERT ON CLIENTE_FINAL
  FOR EACH ROW EXECUTE FUNCTION auto_set_tenant_on_insert();

DROP TRIGGER IF EXISTS trg_protect_tenant_cliente_final ON CLIENTE_FINAL;
CREATE TRIGGER trg_protect_tenant_cliente_final
  BEFORE UPDATE ON CLIENTE_FINAL
  FOR EACH ROW EXECUTE FUNCTION prevent_tenant_change();

-- SAAS_SUSCRIPCIONES
DROP TRIGGER IF EXISTS trg_auto_tenant_saas_suscripciones ON SAAS_SUSCRIPCIONES;
CREATE TRIGGER trg_auto_tenant_saas_suscripciones
  BEFORE INSERT ON SAAS_SUSCRIPCIONES
  FOR EACH ROW EXECUTE FUNCTION auto_set_tenant_on_insert();

DROP TRIGGER IF EXISTS trg_protect_tenant_saas_suscripciones ON SAAS_SUSCRIPCIONES;
CREATE TRIGGER trg_protect_tenant_saas_suscripciones
  BEFORE UPDATE ON SAAS_SUSCRIPCIONES
  FOR EACH ROW EXECUTE FUNCTION prevent_tenant_change();

-- SAAS_COBROS
DROP TRIGGER IF EXISTS trg_auto_tenant_saas_cobros ON SAAS_COBROS;
CREATE TRIGGER trg_auto_tenant_saas_cobros
  BEFORE INSERT ON SAAS_COBROS
  FOR EACH ROW EXECUTE FUNCTION auto_set_tenant_on_insert();

DROP TRIGGER IF EXISTS trg_protect_tenant_saas_cobros ON SAAS_COBROS;
CREATE TRIGGER trg_protect_tenant_saas_cobros
  BEFORE UPDATE ON SAAS_COBROS
  FOR EACH ROW EXECUTE FUNCTION prevent_tenant_change();

-- SAAS_USO_RECURSOS
DROP TRIGGER IF EXISTS trg_auto_tenant_saas_uso ON SAAS_USO_RECURSOS;
CREATE TRIGGER trg_auto_tenant_saas_uso
  BEFORE INSERT ON SAAS_USO_RECURSOS
  FOR EACH ROW EXECUTE FUNCTION auto_set_tenant_on_insert();

DROP TRIGGER IF EXISTS trg_protect_tenant_saas_uso ON SAAS_USO_RECURSOS;
CREATE TRIGGER trg_protect_tenant_saas_uso
  BEFORE UPDATE ON SAAS_USO_RECURSOS
  FOR EACH ROW EXECUTE FUNCTION prevent_tenant_change();

-- SAAS_USO_MES
DROP TRIGGER IF EXISTS trg_auto_tenant_saas_uso_mes ON SAAS_USO_MES;
CREATE TRIGGER trg_auto_tenant_saas_uso_mes
  BEFORE INSERT ON SAAS_USO_MES
  FOR EACH ROW EXECUTE FUNCTION auto_set_tenant_on_insert();

DROP TRIGGER IF EXISTS trg_protect_tenant_saas_uso_mes ON SAAS_USO_MES;
CREATE TRIGGER trg_protect_tenant_saas_uso_mes
  BEFORE UPDATE ON SAAS_USO_MES
  FOR EACH ROW EXECUTE FUNCTION prevent_tenant_change();

-- LEGAL_ACCEPTANCE
DROP TRIGGER IF EXISTS trg_auto_tenant_legal ON LEGAL_ACCEPTANCE;
CREATE TRIGGER trg_auto_tenant_legal
  BEFORE INSERT ON LEGAL_ACCEPTANCE
  FOR EACH ROW EXECUTE FUNCTION auto_set_tenant_on_insert();

DROP TRIGGER IF EXISTS trg_protect_tenant_legal ON LEGAL_ACCEPTANCE;
CREATE TRIGGER trg_protect_tenant_legal
  BEFORE UPDATE ON LEGAL_ACCEPTANCE
  FOR EACH ROW EXECUTE FUNCTION prevent_tenant_change();

-- TENANT_FISCAL_CONFIG
DROP TRIGGER IF EXISTS trg_auto_tenant_tfc ON TENANT_FISCAL_CONFIG;
CREATE TRIGGER trg_auto_tenant_tfc
  BEFORE INSERT ON TENANT_FISCAL_CONFIG
  FOR EACH ROW EXECUTE FUNCTION auto_set_tenant_on_insert();

DROP TRIGGER IF EXISTS trg_protect_tenant_tfc ON TENANT_FISCAL_CONFIG;
CREATE TRIGGER trg_protect_tenant_tfc
  BEFORE UPDATE ON TENANT_FISCAL_CONFIG
  FOR EACH ROW EXECUTE FUNCTION prevent_tenant_change();

-- TENANT_FISCAL_DATA
DROP TRIGGER IF EXISTS trg_auto_tenant_tfd ON TENANT_FISCAL_DATA;
CREATE TRIGGER trg_auto_tenant_tfd
  BEFORE INSERT ON TENANT_FISCAL_DATA
  FOR EACH ROW EXECUTE FUNCTION auto_set_tenant_on_insert();

DROP TRIGGER IF EXISTS trg_protect_tenant_tfd ON TENANT_FISCAL_DATA;
CREATE TRIGGER trg_protect_tenant_tfd
  BEFORE UPDATE ON TENANT_FISCAL_DATA
  FOR EACH ROW EXECUTE FUNCTION prevent_tenant_change();

-- FISCAL_DOCUMENTS
DROP TRIGGER IF EXISTS trg_auto_tenant_fiscal_docs ON FISCAL_DOCUMENTS;
CREATE TRIGGER trg_auto_tenant_fiscal_docs
  BEFORE INSERT ON FISCAL_DOCUMENTS
  FOR EACH ROW EXECUTE FUNCTION auto_set_tenant_on_insert();

DROP TRIGGER IF EXISTS trg_protect_tenant_fiscal_docs ON FISCAL_DOCUMENTS;
CREATE TRIGGER trg_protect_tenant_fiscal_docs
  BEFORE UPDATE ON FISCAL_DOCUMENTS
  FOR EACH ROW EXECUTE FUNCTION prevent_tenant_change();

-- ========================================
-- 5. INDICES PARA PERFORMANCE DE RLS
-- ========================================
-- RLS filtra por EMP_ID en CADA query. Estos indices aceleran el filtrado.

CREATE INDEX IF NOT EXISTS idx_pedidos_emp ON PEDIDOS(EMP_ID);
CREATE INDEX IF NOT EXISTS idx_choferes_emp ON CHOFERES(EMP_ID);
CREATE INDEX IF NOT EXISTS idx_vehiculos_emp ON VEHICULOS(EMP_ID);
CREATE INDEX IF NOT EXISTS idx_clientes_emp ON CLIENTES_LM(EMP_ID);
CREATE INDEX IF NOT EXISTS idx_tracking_emp ON TRACKING(EMP_ID);
CREATE INDEX IF NOT EXISTS idx_zonas_emp ON ZONAS(ZON_EMP_ID);
CREATE INDEX IF NOT EXISTS idx_zona_tarifas_emp ON ZONA_TARIFAS(ZTA_EMP_ID);
CREATE INDEX IF NOT EXISTS idx_cfdi_facturas_emp ON CFDI_FACTURAS(EMP_ID);
CREATE INDEX IF NOT EXISTS idx_cfdi_folios_emp ON CFDI_FOLIOS(EMP_ID);
CREATE INDEX IF NOT EXISTS idx_cfdi_empresa_fiscal_emp ON CFDI_EMPRESA_FISCAL(EMP_ID);
CREATE INDEX IF NOT EXISTS idx_cfdi_timbrado_emp ON CFDI_TIMBRADO_LOG(EMP_ID);
CREATE INDEX IF NOT EXISTS idx_cfdi_conceptos_emp ON CFDI_CONCEPTOS_CATALOGO(EMP_ID);
CREATE INDEX IF NOT EXISTS idx_pagos_metodos_emp ON PAGOS_METODOS(EMP_ID);
CREATE INDEX IF NOT EXISTS idx_pagos_transacciones_emp ON PAGOS_TRANSACCIONES(EMP_ID);
CREATE INDEX IF NOT EXISTS idx_notif_push_emp ON NOTIF_PUSH(EMP_ID);
CREATE INDEX IF NOT EXISTS idx_notif_dispositivos_emp ON NOTIF_DISPOSITIVOS(EMP_ID);
CREATE INDEX IF NOT EXISTS idx_email_enviados_emp ON EMAIL_ENVIADOS(EMP_ID);
CREATE INDEX IF NOT EXISTS idx_sms_enviados_emp ON SMS_ENVIADOS(EMP_ID);
CREATE INDEX IF NOT EXISTS idx_audit_log_emp ON AUDIT_LOG(EMP_ID);
CREATE INDEX IF NOT EXISTS idx_reportes_emp ON REPORTES_GENERADOS(EMP_ID);
CREATE INDEX IF NOT EXISTS idx_entregas_emp ON ENTREGAS(EMP_ID);
CREATE INDEX IF NOT EXISTS idx_incidencias_emp ON INCIDENCIAS(EMP_ID);
CREATE INDEX IF NOT EXISTS idx_kpi_emp ON KPI_DIARIO(EMP_ID);
CREATE INDEX IF NOT EXISTS idx_cliente_final_emp ON CLIENTE_FINAL(EMP_ID);
CREATE INDEX IF NOT EXISTS idx_saas_suscripciones_emp ON SAAS_SUSCRIPCIONES(EMP_ID);
CREATE INDEX IF NOT EXISTS idx_saas_cobros_emp ON SAAS_COBROS(EMP_ID);
CREATE INDEX IF NOT EXISTS idx_saas_uso_recursos_emp ON SAAS_USO_RECURSOS(EMP_ID);
CREATE INDEX IF NOT EXISTS idx_saas_uso_mes_emp ON SAAS_USO_MES(EMP_ID);
CREATE INDEX IF NOT EXISTS idx_legal_emp ON LEGAL_ACCEPTANCE(EMP_ID);
CREATE INDEX IF NOT EXISTS idx_referrals_referrer ON REFERRALS(REF_REFERRER_EMP_ID);
CREATE INDEX IF NOT EXISTS idx_referrals_referred ON REFERRALS(REFREFERRED_EMP_ID);
CREATE INDEX IF NOT EXISTS idx_tfc_emp ON TENANT_FISCAL_CONFIG(EMP_ID);
CREATE INDEX IF NOT EXISTS idx_tfd_emp ON TENANT_FISCAL_DATA(EMP_ID);
CREATE INDEX IF NOT EXISTS idx_fd_emp ON FISCAL_DOCUMENTS(EMP_ID);
CREATE INDEX IF NOT EXISTS idx_historial_ped ON PEDIDO_HISTORIAL(PED_ID);

-- Indices compuestos para queries frecuentes
CREATE INDEX IF NOT EXISTS idx_pedidos_emp_estado ON PEDIDOS(EMP_ID, PED_ESTADO);
CREATE INDEX IF NOT EXISTS idx_pedidos_emp_fecha ON PEDIDOS(EMP_ID, PED_FECHA_PEDIDO);
CREATE INDEX IF NOT EXISTS idx_choferes_emp_estatus ON CHOFERES(EMP_ID, CHO_ESTATUS);
CREATE INDEX IF NOT EXISTS idx_clientes_emp_estatus ON CLIENTES_LM(EMP_ID, CLI_ESTATUS);
CREATE INDEX IF NOT EXISTS idx_entregas_emp_estado ON ENTREGAS(EMP_ID, ENT_ESTADO);

-- ========================================
-- 6. PERMISOS PARA SERVICE_ROLE
-- ========================================
-- Supabase service_role bypasea RLS, pero asegurar GRANT por si acaso.
-- Los usuarios anon/authenticated NO reciben grants directos.

REVOKE ALL ON ALL TABLES IN SCHEMA public FROM authenticated;
REVOKE ALL ON ALL TABLES IN SCHEMA public FROM anon;

-- ========================================
-- DONE - Migracion 004 completada
-- ========================================
