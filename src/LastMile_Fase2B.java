import java.sql.*;

/**
 * Fase 2B: Tablas de Notificaciones, Email, SMS, Billing SaaS
 */
public class LastMile_Fase2B {

    static final String DB_URL = "jdbc:as400://192.168.0.240;errors=full";
    static final String USER = "AYUDATX";
    static final String PASS = "MXTAC23";

    public static void main(String[] args) throws Exception {
        Class.forName("com.ibm.as400.access.AS400JDBCDriver");
        Connection conn = DriverManager.getConnection(DB_URL, USER, PASS);
        conn.setAutoCommit(true);
        Statement s = conn.createStatement();

        System.out.println("=== FASE 2B: NOTIFICACIONES + EMAIL + BILLING ===\n");

        // ========================================
        // 1. NOTIFICACIONES PUSH
        // ========================================
        try { s.execute("DROP TABLE TESTLIB.NOTIF_PUSH"); } catch(Exception e) {}
        s.execute("CREATE TABLE TESTLIB.NOTIF_PUSH (" +
            "NPUSH_ID INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY, " +
            "EMP_ID INTEGER NOT NULL, " +
            "USR_ID INTEGER, " +
            "CHO_ID INTEGER, " +
            "NPUSH_TIPO VARCHAR(30) NOT NULL, " +
            "NPUSH_TITULO VARCHAR(200) NOT NULL, " +
            "NPUSH_CUERPO VARCHAR(500) NOT NULL, " +
            "NPUSH_DATA VARCHAR(1000) DEFAULT '{}', " +
            "NPUSH_ENVIADO CHAR(1) DEFAULT 'N', " +
            "NPUSH_LEIDO CHAR(1) DEFAULT 'N', " +
            "NPUSH_FECHA_REGISTRO TIMESTAMP DEFAULT CURRENT_TIMESTAMP, " +
            "NPUSH_FECHA_ENVIO TIMESTAMP, " +
            "NPUSH_ERROR VARCHAR(500) DEFAULT ''" +
            ")");
        System.out.println("  [OK] NOTIF_PUSH");

        // ========================================
        // 2. DISPOSITIVOS (tokens push)
        // ========================================
        try { s.execute("DROP TABLE TESTLIB.NOTIF_DISPOSITIVOS"); } catch(Exception e) {}
        s.execute("CREATE TABLE TESTLIB.NOTIF_DISPOSITIVOS (" +
            "DISP_ID INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY, " +
            "EMP_ID INTEGER NOT NULL, " +
            "USR_ID INTEGER, " +
            "CHO_ID INTEGER, " +
            "DISP_TOKEN VARCHAR(500) NOT NULL, " +
            "DISP_PLATAFORMA VARCHAR(20) DEFAULT 'WEB', " +
            "DISP_ACTIVO CHAR(1) DEFAULT 'S', " +
            "DISP_FECHA_REGISTRO TIMESTAMP DEFAULT CURRENT_TIMESTAMP, " +
            "DISP_ULTIMO_USO TIMESTAMP" +
            ")");
        System.out.println("  [OK] NOTIF_DISPOSITIVOS");

        // ========================================
        // 3. EMAILS TRANSCACIONALES
        // ========================================
        try { s.execute("DROP TABLE TESTLIB.EMAIL_ENVIADOS"); } catch(Exception e) {}
        s.execute("CREATE TABLE TESTLIB.EMAIL_ENVIADOS (" +
            "EMAIL_ID INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY, " +
            "EMP_ID INTEGER NOT NULL, " +
            "PED_ID INTEGER, " +
            "FAC_ID INTEGER, " +
            "EMAIL_DESTINATARIO VARCHAR(150) NOT NULL, " +
            "EMAIL_ASUNTO VARCHAR(300) NOT NULL, " +
            "EMAIL_TIPO VARCHAR(50) NOT NULL, " +
            "EMAIL_BODY_HTML CLOB, " +
            "EMAIL_ENVIADO CHAR(1) DEFAULT 'N', " +
            "EMAIL_FECHA_REGISTRO TIMESTAMP DEFAULT CURRENT_TIMESTAMP, " +
            "EMAIL_FECHA_ENVIO TIMESTAMP, " +
            "EMAIL_ERROR VARCHAR(500) DEFAULT ''" +
            ")");
        System.out.println("  [OK] EMAIL_ENVIADOS");

        // ========================================
        // 4. SMS / WHATSAPP
        // ========================================
        try { s.execute("DROP TABLE TESTLIB.SMS_ENVIADOS"); } catch(Exception e) {}
        s.execute("CREATE TABLE TESTLIB.SMS_ENVIADOS (" +
            "SMS_ID INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY, " +
            "EMP_ID INTEGER NOT NULL, " +
            "PED_ID INTEGER, " +
            "SMS_TELEFONO VARCHAR(15) NOT NULL, " +
            "SMS_MENSAJE VARCHAR(500) NOT NULL, " +
            "SMS_PLATAFORMA VARCHAR(15) DEFAULT 'SMS', " +
            "SMS_ENVIADO CHAR(1) DEFAULT 'N', " +
            "SMS_FECHA_REGISTRO TIMESTAMP DEFAULT CURRENT_TIMESTAMP, " +
            "SMS_FECHA_ENVIO TIMESTAMP, " +
            "SMS_COSTO DECIMAL(8,4) DEFAULT 0, " +
            "SMS_ERROR VARCHAR(500) DEFAULT ''" +
            ")");
        System.out.println("  [OK] SMS_ENVIADOS");

        // ========================================
        // 5. REPORTES GENERADOS
        // ========================================
        try { s.execute("DROP TABLE TESTLIB.REPORTES_GENERADOS"); } catch(Exception e) {}
        s.execute("CREATE TABLE TESTLIB.REPORTES_GENERADOS (" +
            "RPT_ID INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY, " +
            "EMP_ID INTEGER NOT NULL, " +
            "RPT_TIPO VARCHAR(50) NOT NULL, " +
            "RPT_NOMBRE VARCHAR(200) NOT NULL, " +
            "RPT_PARAMETROS VARCHAR(1000) DEFAULT '{}', " +
            "RPT_ARCHIVO_URL VARCHAR(500), " +
            "RPT_FECHA_GENERACION TIMESTAMP DEFAULT CURRENT_TIMESTAMP, " +
            "RPT_GENERADO_POR VARCHAR(50) DEFAULT 'SYSTEM', " +
            "RPT_TAMANO_BYTES INTEGER DEFAULT 0" +
            ")");
        System.out.println("  [OK] REPORTES_GENERADOS");

        // ========================================
        // 6. BILLING: Planes SaaS
        // ========================================
        try { s.execute("DROP TABLE TESTLIB.SAAS_PLANES"); } catch(Exception e) {}
        s.execute("CREATE TABLE TESTLIB.SAAS_PLANES (" +
            "PLAN_ID INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY, " +
            "PLAN_NOMBRE VARCHAR(50) NOT NULL, " +
            "PLAN_DESCRIPCION VARCHAR(300), " +
            "PLAN_PRECIO_MENSUAL DECIMAL(12,2) NOT NULL, " +
            "PLAN_PRECIO_ANUAL DECIMAL(12,2), " +
            "PLAN_MAX_CHOFERES INTEGER DEFAULT 5, " +
            "PLAN_MAX_ENVIOS_MES INTEGER DEFAULT 1000, " +
            "PLAN_MAX_USUARIOS INTEGER DEFAULT 3, " +
            "PLAN_MAX_SUCURSALES INTEGER DEFAULT 1, " +
            "PLAN_FEATURES VARCHAR(2000) DEFAULT '{}', " +
            "PLAN_ACTIVO CHAR(1) DEFAULT 'S', " +
            "PLAN_ORDEN INTEGER DEFAULT 0" +
            ")");
        System.out.println("  [OK] SAAS_PLANES");

        // ========================================
        // 7. BILLING: Suscripciones de clientes
        // ========================================
        try { s.execute("DROP TABLE TESTLIB.SAAS_SUSCRIPCIONES"); } catch(Exception e) {}
        s.execute("CREATE TABLE TESTLIB.SAAS_SUSCRIPCIONES (" +
            "SUS_ID INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY, " +
            "EMP_ID INTEGER NOT NULL, " +
            "PLAN_ID INTEGER NOT NULL, " +
            "SUS_ESTADO VARCHAR(20) DEFAULT 'TRIAL', " +
            "SUS_FECHA_INICIO DATE, " +
            "SUS_FECHA_FIN DATE, " +
            "SUS_FECHA_PROXIMO_COBRO DATE, " +
            "SUS_FACTURACION_CICLO VARCHAR(10) DEFAULT 'MENSUAL', " +
            "SUS_METODO_PAGO VARCHAR(30) DEFAULT 'MERCADOPAGO', " +
            "SUS_MP_CUSTOMER_ID VARCHAR(100), " +
            "SUS_MP_SUBSCRIPTION_ID VARCHAR(100), " +
            "SUS_STRIPE_CUSTOMER_ID VARCHAR(100), " +
            "SUS_STRIPE_SUBSCRIPTION_ID VARCHAR(100), " +
            "SUS_TOTAL_COBRADO DECIMAL(12,2) DEFAULT 0, " +
            "SUS_FECHA_REGISTRO TIMESTAMP DEFAULT CURRENT_TIMESTAMP, " +
            "SUS_NOTAS VARCHAR(500) DEFAULT ''" +
            ")");
        System.out.println("  [OK] SAAS_SUSCRIPCIONES");

        // ========================================
        // 8. BILLING: Historial de cobros
        // ========================================
        try { s.execute("DROP TABLE TESTLIB.SAAS_COBROS"); } catch(Exception e) {}
        s.execute("CREATE TABLE TESTLIB.SAAS_COBROS (" +
            "COB_ID INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY, " +
            "SUS_ID INTEGER NOT NULL, " +
            "EMP_ID INTEGER NOT NULL, " +
            "COB_MONTO DECIMAL(12,2) NOT NULL, " +
            "COB_MONEDA VARCHAR(5) DEFAULT 'MXN', " +
            "COB_CONCEPTO VARCHAR(200) NOT NULL, " +
            "COB_ESTATUS VARCHAR(20) DEFAULT 'PENDIENTE', " +
            "COB_METODO_PAGO VARCHAR(30), " +
            "COB_REFERENCIA_PAGO VARCHAR(200), " +
            "COB_FECHA_COBRO TIMESTAMP DEFAULT CURRENT_TIMESTAMP, " +
            "COB_FECHA_APLICADO TIMESTAMP, " +
            "COB_FACTURA_ID INTEGER, " +
            "COB_JSON_RESPUESTA CLOB, " +
            "COB_NOTAS VARCHAR(500) DEFAULT ''" +
            ")");
        System.out.println("  [OK] SAAS_COBROS");

        // ========================================
        // 9. USO DE RECURSOS (para billing por uso)
        // ========================================
        try { s.execute("DROP TABLE TESTLIB.SAAS_USO_RECURSOS"); } catch(Exception e) {}
        s.execute("CREATE TABLE TESTLIB.SAAS_USO_RECURSOS (" +
            "USR_ID INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY, " +
            "EMP_ID INTEGER NOT NULL, " +
            "USR_FECHA DATE NOT NULL, " +
            "USR_PEDIDOS_CREADOS INTEGER DEFAULT 0, " +
            "USR_PEDIDOS_ENTREGADOS INTEGER DEFAULT 0, " +
            "USR_ENVIOS_SMS INTEGER DEFAULT 0, " +
            "USR_ENVIOS_EMAIL INTEGER DEFAULT 0, " +
            "USR_API_CALLS INTEGER DEFAULT 0, " +
            "USR_STORAGE_MB DECIMAL(10,2) DEFAULT 0, " +
            "USR_NOTAS VARCHAR(500) DEFAULT ''" +
            ")");
        System.out.println("  [OK] SAAS_USO_RECURSOS");

        // ========================================
        // 10. CLIENTE FINAL (destinatarios tracking)
        // ========================================
        try { s.execute("DROP TABLE TESTLIB.CLIENTE_FINAL"); } catch(Exception e) {}
        s.execute("CREATE TABLE TESTLIB.CLIENTE_FINAL (" +
            "CLIF_ID INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY, " +
            "EMP_ID INTEGER NOT NULL, " +
            "PED_ID INTEGER, " +
            "CLIF_NOMBRE VARCHAR(200) NOT NULL, " +
            "CLIF_TELEFONO VARCHAR(15), " +
            "CLIF_EMAIL VARCHAR(150), " +
            "CLIF_TOKEN_TRACKING VARCHAR(64), " +
            "CLIF_NOTIF_SMS CHAR(1) DEFAULT 'S', " +
            "CLIF_NOTIF_WHATSAPP CHAR(1) DEFAULT 'S', " +
            "CLIF_NOTIF_EMAIL CHAR(1) DEFAULT 'S', " +
            "CLIF_FECHA_REGISTRO TIMESTAMP DEFAULT CURRENT_TIMESTAMP" +
            ")");
        System.out.println("  [OK] CLIENTE_FINAL");

        // ========================================
        // DATOS DE EJEMPLO
        // ========================================
        System.out.println("\n--- DATOS ---");
        int total = 0;

        // Planes SaaS
        PreparedStatement ps = conn.prepareStatement("INSERT INTO TESTLIB.SAAS_PLANES (PLAN_NOMBRE, PLAN_DESCRIPCION, PLAN_PRECIO_MENSUAL, PLAN_PRECIO_ANUAL, PLAN_MAX_CHOFERES, PLAN_MAX_ENVIOS_MES, PLAN_MAX_USUARIOS, PLAN_MAX_SUCURSALES, PLAN_FEATURES, PLAN_ORDEN) VALUES (?,?,?,?,?,?,?,?,?,?)");
        
        ps.setString(1,"Starter"); ps.setString(2,"Para negocios pequeños"); ps.setBigDecimal(3,new java.math.BigDecimal("999")); ps.setBigDecimal(4,new java.math.BigDecimal("9590")); ps.setInt(5,5); ps.setInt(6,1000); ps.setInt(7,3); ps.setInt(8,1); ps.setString(9,"{cfdi:true,whitelabel:false,api:false}"); ps.setInt(10,1); total += ps.executeUpdate();
        
        ps.setString(1,"Pro"); ps.setString(2,"El más popular"); ps.setBigDecimal(3,new java.math.BigDecimal("2499")); ps.setBigDecimal(4,new java.math.BigDecimal("23990")); ps.setInt(5,25); ps.setInt(6,10000); ps.setInt(7,10); ps.setInt(8,1); ps.setString(9,"{cfdi:true,whitelabel:true,api:false,pagos:true}"); ps.setInt(10,2); total += ps.executeUpdate();
        
        ps.setString(1,"Enterprise"); ps.setString(2,"Multi-sucursal ilimitado"); ps.setBigDecimal(3,new java.math.BigDecimal("5999")); ps.setBigDecimal(4,new java.math.BigDecimal("57590")); ps.setInt(5,999); ps.setInt(6,999999); ps.setInt(7,999); ps.setInt(8,999); ps.setString(9,"{cfdi:true,whitelabel:true,api:true,pagos:true,soporte:true}"); ps.setInt(10,3); total += ps.executeUpdate();
        ps.close();
        System.out.println("  [OK] 3 planes SaaS");

        // Suscripciones de ejemplo
        ps = conn.prepareStatement("INSERT INTO TESTLIB.SAAS_SUSCRIPCIONES (EMP_ID, PLAN_ID, SUS_ESTADO, SUS_FECHA_INICIO, SUS_FECHA_FIN, SUS_FECHA_PROXIMO_COBRO) VALUES (?,?,?,?,?,?)");
        ps.setInt(1,1); ps.setInt(2,2); ps.setString(3,"ACTIVA"); ps.setDate(4,java.sql.Date.valueOf("2026-07-01")); ps.setDate(5,java.sql.Date.valueOf("2026-12-31")); ps.setDate(6,java.sql.Date.valueOf("2026-08-01")); total += ps.executeUpdate();
        ps.setInt(1,2); ps.setInt(2,1); ps.setString(3,"ACTIVA"); ps.setDate(4,java.sql.Date.valueOf("2026-07-01")); ps.setDate(5,java.sql.Date.valueOf("2026-12-31")); ps.setDate(6,java.sql.Date.valueOf("2026-08-01")); total += ps.executeUpdate();
        ps.setInt(1,3); ps.setInt(2,3); ps.setString(3,"TRIAL"); ps.setDate(4,java.sql.Date.valueOf("2026-07-07")); ps.setDate(5,java.sql.Date.valueOf("2026-08-07")); ps.setDate(6,java.sql.Date.valueOf("2026-08-07")); total += ps.executeUpdate();
        ps.close();
        System.out.println("  [OK] 3 suscripciones");

        // Cobros de ejemplo
        ps = conn.prepareStatement("INSERT INTO TESTLIB.SAAS_COBROS (SUS_ID, EMP_ID, COB_MONTO, COB_CONCEPTO, COB_ESTATUS, COB_METODO_PAGO) VALUES (?,?,?,?,?,?)");
        ps.setInt(1,1); ps.setInt(2,1); ps.setBigDecimal(3,new java.math.BigDecimal("2499")); ps.setString(4,"Mensualidad Plan Pro Julio 2026"); ps.setString(5,"PAGADO"); ps.setString(6,"MERCADOPAGO"); total += ps.executeUpdate();
        ps.setInt(1,2); ps.setInt(2,2); ps.setBigDecimal(3,new java.math.BigDecimal("999")); ps.setString(4,"Mensualidad Plan Starter Julio 2026"); ps.setString(5,"PAGADO"); ps.setString(6,"SPEI"); total += ps.executeUpdate();
        ps.close();
        System.out.println("  [OK] 2 cobros");

        // Uso de recursos
        ps = conn.prepareStatement("INSERT INTO TESTLIB.SAAS_USO_RECURSOS (EMP_ID, USR_FECHA, USR_PEDIDOS_CREADOS, USR_PEDIDOS_ENTREGADOS, USR_ENVIOS_SMS, USR_ENVIOS_EMAIL, USR_API_CALLS) VALUES (?,?,?,?,?,?,?)");
        ps.setInt(1,1); ps.setDate(2,java.sql.Date.valueOf("2026-07-07")); ps.setInt(3,45); ps.setInt(4,38); ps.setInt(5,38); ps.setInt(6,38); ps.setInt(7,520); total += ps.executeUpdate();
        ps.setInt(1,1); ps.setDate(2,java.sql.Date.valueOf("2026-07-06")); ps.setInt(3,52); ps.setInt(4,48); ps.setInt(5,48); ps.setInt(6,48); ps.setInt(7,610); total += ps.executeUpdate();
        ps.setInt(1,2); ps.setDate(2,java.sql.Date.valueOf("2026-07-07")); ps.setInt(3,12); ps.setInt(4,10); ps.setInt(5,10); ps.setInt(6,10); ps.setInt(7,145); total += ps.executeUpdate();
        ps.close();
        System.out.println("  [OK] 3 registros de uso");

        // Cliente final ejemplo
        ps = conn.prepareStatement("INSERT INTO TESTLIB.CLIENTE_FINAL (EMP_ID, PED_ID, CLIF_NOMBRE, CLIF_TELEFONO, CLIF_EMAIL, CLIF_TOKEN_TRACKING) VALUES (?,?,?,?,?,?)");
        ps.setInt(1,1); ps.setInt(2,1); ps.setString(3,"Juan Perez Garcia"); ps.setString(4,"5512345678"); ps.setString(5,"juan@email.com"); ps.setString(6,"tk_abc123def456"); total += ps.executeUpdate();
        ps.setInt(1,1); ps.setInt(2,30); ps.setString(3,"Maria Lopez"); ps.setString(4,"5598765432"); ps.setString(5,"maria@email.com"); ps.setString(6,"tk_xyz789ghi012"); total += ps.executeUpdate();
        ps.close();
        System.out.println("  [OK] 2 clientes finales");

        // Emails de ejemplo
        ps = conn.prepareStatement("INSERT INTO TESTLIB.EMAIL_ENVIADOS (EMP_ID, PED_ID, EMAIL_DESTINATARIO, EMAIL_ASUNTO, EMAIL_TIPO, EMAIL_ENVIADO) VALUES (?,?,?,?,?,?)");
        ps.setInt(1,1); ps.setInt(2,1); ps.setString(3,"juan@email.com"); ps.setString(4,"Tu paquete esta en camino"); ps.setString(5,"TRACKING"); ps.setString(6,"S"); total += ps.executeUpdate();
        ps.setInt(1,1); ps.setInt(2,30); ps.setString(3,"maria@email.com"); ps.setString(4,"Factura CFDI disponible"); ps.setString(5,"CFDI"); ps.setString(6,"S"); total += ps.executeUpdate();
        ps.close();
        System.out.println("  [OK] 2 emails");

        conn.commit();
        System.out.println("\n=== COMPLETADO: " + total + " registros ===");
        s.close(); conn.close();
    }
}
