# Multi-Tenant RLS - Guia Completa

## Arquitectura de Aislamiento

Last Mile Platform usa **Row-Level Security (RLS)** de PostgreSQL para garantizar que cada tenant (empresa) solo pueda acceder a sus propios datos. Cada fila en la base de datos tiene un campo EMP_ID que identifica a que tenant pertenece.

### Flujo de una Request

`
1. Request HTTP llega con JWT token
2. Flask middleware (server.py:418) decodifica el token
3. extrae emp_id del token (NUNCA del header)
4. llama a set_tenant_context(emp_id) en db.py:98
5. PostgreSQL ejecuta: SET app.current_emp_id = '<emp_id>'
6. Todas las queries posteriores filtran automaticamente via RLS
7. El usuario SOLO ve datos de su tenant
`

### Capas de Proteccion

| Capa | Mecanismo | Ubicacion |
|------|-----------|-----------|
| API Gateway | JWT validation + role check | server.py:418-470 |
| Anti-IDOR | URL emp_id != token emp_id => 403 | server.py:457-463 |
| DB Session | SET app.current_emp_id per-request | db.py:98-111 |
| PostgreSQL RLS | WHERE EMP_ID = session var | 004_multi_tenant_rls.sql |
| Trigger | Auto-rellena EMP_ID si es NULL | 004_multi_tenant_rls.sql |
| Anti-Change | Trigger que impide UPDATE de EMP_ID | 004_multi_tenant_rls.sql |

## Tablas Protegidas

RLS esta habilitado en **37 tablas**:

### Tablas Base
- EMPRESAS, USUARIOS, CHOFERES, VEHICULOS, CLIENTES_LM

### Operaciones
- PEDIDOS, PEDIDO_HISTORIAL, TRACKING, ENTREGAS, INCIDENCIAS, KPI_DIARIO

### Zonas
- ZONAS, ZONA_TARIFAS

### Facturacion CFDI
- CFDI_EMPRESA_FISCAL, CFDI_FOLIOS, CFDI_FACTURAS, CFDI_TIMBRADO_LOG, CFDI_CONCEPTOS_CATALOGO

### Pagos
- PAGOS_METODOS, PAGOS_TRANSACCIONES

### Notificaciones
- NOTIF_PUSH, NOTIF_DISPOSITIVOS

### Comunicaciones
- EMAIL_ENVIADOS, SMS_ENVIADOS

### Auditoria y Reportes
- AUDIT_LOG, REPORTES_GENERADOS

### SaaS Billing
- SAAS_PLANES (lectura publica), SAAS_SUSCRIPCIONES, SAAS_COBROS, SAAS_USO_RECURSOS, SAAS_USO_MES

### Otros
- CLIENTE_FINAL, LEGAL_ACCEPTANCE, REFERRALS

### Multi-Pais Fiscal
- TENANT_FISCAL_CONFIG, TENANT_FISCAL_DATA, FISCAL_DOCUMENTS

## Como Configurar el Tenant Actual

### Automatico (Backend Python)

El backend configura el tenant automaticamente en cada request via db.py:98:

`python
from db import set_tenant_context

# Se ejecuta en before_request (server.py:466-471)
set_tenant_context(emp_id)
`

### Manual (SQL - testing/debugging)

`sql
-- Establecer tenant para la sesion actual
SELECT set_current_tenant(1);

-- Verificar
SHOW app.current_emp_id;

-- Ahora solo ves datos del tenant 1
SELECT * FROM PEDIDOS;  -- solo muestra pedidos de empresa 1
`

### En Supabase SQL Editor

`sql
-- 1. Establecer tenant
SELECT set_current_tenant(2);

-- 2. Verificar aislamiento
SELECT COUNT(*) FROM PEDIDOS;  -- solo cuenta pedidos de empresa 2
`

## Como Verificar que RLS Funciona

### Test 1: Aislamiento basico

`sql
-- Conectar como service_role (bypasea RLS)
SELECT set_current_tenant(1);
SELECT COUNT(*) FROM PEDIDOS;  -- Resultado: N

SELECT set_current_tenant(2);
SELECT COUNT(*) FROM PEDIDOS;  -- Resultado: M (diferente)
`

### Test 2: Cross-tenant access

`sql
-- Establecer tenant 1
SELECT set_current_tenant(1);

-- Intentar ver datos del tenant 2 (deberia fallar o retornar 0)
SELECT * FROM PEDIDOS WHERE EMP_ID = 2;  -- 0 rows (RLS bloquea)
`

### Test 3: Insert con trigger

`sql
SELECT set_current_tenant(3);

-- EMP_ID se rellena automaticamente
INSERT INTO PEDIDOS (PED_CLIENTE_NOMBRE, PED_DESTINO_DIR, PED_DESTINO_CIUDAD)
VALUES ('Test', 'Direccion 1', 'CDMX');

-- Verificar que EMP_ID = 3
SELECT EMP_ID FROM PEDIDOS ORDER BY PED_ID DESC LIMIT 1;  -- 3
`

### Test 4: Proteccion anti-cambio

`sql
SELECT set_current_tenant(1);
-- Intentar cambiar EMP_ID de un registro existente
UPDATE PEDIDOS SET EMP_ID = 999 WHERE PED_ID = 1;
-- ERROR: No se permite cambiar el tenant (EMP_ID) de un registro
`

### Test 5: Verificar indices

`sql
-- Verificar que los indices existen
SELECT indexname, tablename
FROM pg_indexes
WHERE tablename LIKE 'idx_%_emp'
ORDER BY tablename;
`

### Script de Verificacion Completa

`sql
DO 
DECLARE
  t RECORD;
  total INT := 0;
BEGIN
  FOR t IN
    SELECT tablename FROM pg_tables
    WHERE schemaname = 'public'
    ORDER BY tablename
  LOOP
    IF EXISTS (
      SELECT 1 FROM pg_policies
      WHERE tablename = t.tablename
      AND policyname LIKE 'tenant_isolation_%'
    ) THEN
      total := total + 1;
      RAISE NOTICE 'RLS OK: %', t.tablename;
    ELSE
      RAISE WARNING 'RLS FALTA: %', t.tablename;
    END IF;
  END LOOP;
  RAISE NOTICE 'Total tablas con RLS: %', total;
END ;
`

## Tablas Especiales

### SAAS_PLANES - Lectura Publica

`sql
-- Politica especial: todos los tenants pueden LEER planes activos
-- Solo superadmin puede INSERT/UPDATE/DELETE
CREATE POLICY tenant_isolation_saas_planes ON SAAS_PLANES
  FOR SELECT USING (PLAN_ACTIVO = 'S');
`

### PEDIDO_HISTORIAL - Via Subquery

`sql
-- No tiene EMP_ID propio, se accede via PEDIDOS
CREATE POLICY tenant_isolation_historial ON PEDIDO_HISTORIAL
  FOR ALL USING (
    PED_ID IN (
      SELECT PED_ID FROM PEDIDOS
      WHERE EMP_ID::text = current_setting('app.current_emp_id', true)
    )
  );
`

### ZONA_TARIFAS - Via Subquery

`sql
-- No tiene EMP_ID directo (usa ZTA_ZON_ID)
-- Se accede via ZONAS que si tiene ZON_EMP_ID
CREATE POLICY tenant_isolation_zona_tarifas ON ZONA_TARIFAS
  FOR ALL USING (
    ZTA_ZON_ID IN (
      SELECT ZON_ID FROM ZONAS
      WHERE ZON_EMP_ID::text = current_setting('app.current_emp_id', true)
    )
  );
`

### REFERRALS - Dual Tenant

`sql
-- Un referral involucra dos tenants: referrer y referred
CREATE POLICY tenant_isolation_referrals ON REFERRALS
  FOR ALL USING (
    REF_REFERRER_EMP_ID::text = current_setting('app.current_emp_id', true)
    OR
    REFREFERRED_EMP_ID::text = current_setting('app.current_emp_id', true)
  );
`

## Troubleshooting

### Problema: Queries retornan 0 filas

**Causa mas comun:** Olvidaste configurar el tenant en la sesion.

`sql
-- Verificar si el tenant esta configurado
SHOW app.current_emp_id;

-- Si esta vacio, configurarlo:
SELECT set_current_tenant(1);
`

### Problema: ERROR "current setting not found"

`sql
-- La variable no esta configurada. Usar default:
SELECT current_setting('app.current_emp_id', true);
-- Retorna '' si no esta configurada

-- Configurar antes:
SELECT set_current_tenant(1);
`

### Problema: Backend no aislra correctamente

1. Verificar que DATABASE_URL usa PostgreSQL (no SQLite)
2. Verificar que la migracion 004 fue ejecutada
3. Verificar que set_tenant_context() se ejecuta en efore_request

`ash
# Ver logs de RLS
grep "set_tenant_context" api/logs/requests.log
`

### Problema: Service role no bypasea RLS

El service role de Supabase (la key SUPABASE_SERVICE_ROLE_KEY que usa el backend) **bypasea RLS automaticamente**. Si necesitas acceso directo desde SQL Editor, asegurate de ejecutar como postgres o supabase_admin.

### Problema: Tabla no tiene EMP_ID

Algunas tablas no tienen EMP_ID directo (PEDIDO_HISTORIAL, ZONA_TARIFAS). Sus políticas usan subqueries:

`sql
-- PEDIDO_HISTORIAL accede via PEDIDOS
-- ZONA_TARIFAS accede via ZONAS
-- CFDI_TIMBRADO_LOG accede via CFDI_FACTURAS
`

Si creas una tabla nueva, agrega EMP_ID y crea la política en la migracion 005.

### Problema: Performance lenta con RLS

RLS agrega un WHERE implicito a cada query. Los indices en EMP_ID son criticos:

`sql
-- Verificar indices existentes
SELECT indexname, indexdef
FROM pg_indexes
WHERE indexname LIKE 'idx_%_emp';

-- Crear indice faltante
CREATE INDEX IF NOT EXISTS idx_mi_tabla_emp ON MI_TABLA(EMP_ID);
`

## Funciones SQL Disponibles

### set_current_tenant(tenant_id INT)

Establece el tenant actual para la sesion PostgreSQL.

`sql
SELECT set_current_tenant(1);
`

### auto_set_tenant_on_insert()

Trigger que rellena EMP_ID automaticamente desde la sesion si es NULL.

`sql
-- Se ejecuta BEFORE INSERT en tablas con trigger
-- No necesita llamada manual
`

### prevent_tenant_change()

Trigger que impide cambiar EMP_ID en un UPDATE.

`sql
-- Se ejecuta BEFORE UPDATE en tablas con trigger
-- RAISE EXCEPTION si se intenta cambiar EMP_ID
`

## Migraciones Relacionadas

| Migracion | Contenido |
|-----------|-----------|
| 003_rls_tenant_isolation.sql | Politicas RLS iniciales (22 tablas) |
| 004_multi_tenant_rls.sql | RLS completo (37 tablas), functions, triggers, indexes |
| schema_postgres.sql | Schema base de todas las tablas |
