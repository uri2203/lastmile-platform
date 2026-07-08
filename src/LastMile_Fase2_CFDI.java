import java.sql.*;
import java.math.BigDecimal;

/**
 * Last Mile Fase 2A: Tablas CFDI 4.0 + Pagos para México
 * Crea tablas de facturación electrónica y cobranza
 */
public class LastMile_Fase2_CFDI {

    static final String DB_URL = "jdbc:as400://192.168.0.240;errors=full";
    static final String USER = "AYUDATX";
    static final String PASS = "MXTAC23";

    public static void main(String[] args) throws Exception {
        Class.forName("com.ibm.as400.access.AS400JDBCDriver");
        Connection conn = DriverManager.getConnection(DB_URL, USER, PASS);
        conn.setAutoCommit(false);

        System.out.println("==========================================");
        System.out.println("  FASE 2A: CFDI 4.0 + PAGOS (MEXICO)");
        System.out.println("==========================================\n");

        int tablas = 0;
        int registros = 0;

        // 1. Datos fiscales del cliente (empresas tenant)
        tablas += executeDDL(conn, "DROP TABLE TESTLIB.CFDI_EMPRESA_FISCAL IF EXISTS");
        tablas += executeDDL(conn, "CREATE TABLE TESTLIB.CFDI_EMPRESA_FISCAL (" +
            "FISC_ID INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY, " +
            "EMP_ID INTEGER NOT NULL, " +
            "FISC_RFC VARCHAR(13) NOT NULL, " +
            "FISC_RAZON_SOCIAL VARCHAR(200) NOT NULL, " +
            "FISC_REGIMEN_FISCAL VARCHAR(10) NOT NULL, " +
            "FISC_CODIGO_POSTAL VARCHAR(5) NOT NULL, " +
            "FISC_COLONIA VARCHAR(100), " +
            "FISC_CALLE VARCHAR(150), " +
            "FISC_NUMERO_EXTERIOR VARCHAR(20), " +
            "FISC_NUMERO_INTERIOR VARCHAR(20), " +
            "FISC_MUNICIPIO VARCHAR(100), " +
            "FISC_ESTADO VARCHAR(50), " +
            "FISC_PAIS VARCHAR(50) DEFAULT 'MEXICO', " +
            "FISC_TELEFONO VARCHAR(15), " +
            "FISC_EMAIL VARCHAR(150), " +
            "FISC_TIPO_PERSONA VARCHAR(1) DEFAULT 'M', " +
            "FISC_CERTIFICADO_CER VARCHAR(500), " +
            "FISC_CERTIFICADO_KEY VARCHAR(500), " +
            "FISC_CONTRASENA_KEY VARCHAR(200), " +
            "FISC_ESCFDI_DEFAULT CHAR(1) DEFAULT 'S', " +
            "FISC_FECHA_ALTA TIMESTAMP DEFAULT CURRENT_TIMESTAMP, " +
            "FISC_ESTATUS VARCHAR(15) DEFAULT 'ACTIVO'" +
            ")");
        System.out.println("  [OK] CFDI_EMPRESA_FISCAL");

        // 2. Catálogo de conceptos/prestaciones
        tablas += executeDDL(conn, "DROP TABLE TESTLIB.CFDI_CONCEPTOS_CATALOGO IF EXISTS");
        tablas += executeDDL(conn, "CREATE TABLE TESTLIB.CFDI_CONCEPTOS_CATALOGO (" +
            "COC_ID INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY, " +
            "EMP_ID INTEGER NOT NULL, " +
            "COC_CLAVE_PROD_SERV VARCHAR(20) NOT NULL, " +
            "COC_CLAVE_UNIDAD VARCHAR(10) NOT NULL, " +
            "COC_UNIDAD VARCHAR(50) NOT NULL, " +
            "COC_DESCRIPCION VARCHAR(250) NOT NULL, " +
            "COC_VALOR_UNITARIO DECIMAL(12,2) DEFAULT 0, " +
            "COC_IVA_TASA DECIMAL(5,4) DEFAULT 0.1600, " +
            "COC_ISR_TASA DECIMAL(5,4) DEFAULT 0.0000, " +
            "COC_RETENCION_IVA_TASA DECIMAL(5,4) DEFAULT 0.0000, " +
            "COC_OBJETO_IMPUESTO VARCHAR(5) DEFAULT '002', " +
            "COC_ESTATUS VARCHAR(10) DEFAULT 'ACTIVO'" +
            ")");
        System.out.println("  [OK] CFDI_CONCEPTOS_CATALOGO");

        // 3. Facturas CFDI
        tablas += executeDDL(conn, "DROP TABLE TESTLIB.CFDI_FACTURAS IF EXISTS");
        tablas += executeDDL(conn, "CREATE TABLE TESTLIB.CFDI_FACTURAS (" +
            "FAC_ID INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY, " +
            "EMP_ID INTEGER NOT NULL, " +
            "FAC_UUID VARCHAR(40), " +
            "FAC_SERIE VARCHAR(25), " +
            "FAC_FOLIO VARCHAR(25), " +
            "FAC_FECHA_EMISION TIMESTAMP DEFAULT CURRENT_TIMESTAMP, " +
            "FAC_FECHA_TIMBRADO TIMESTAMP, " +
            "FAC_FORMA_PAGO VARCHAR(5) NOT NULL DEFAULT '01', " +
            "FAC_METODO_PAGO VARCHAR(3) NOT NULL DEFAULT 'PUE', " +
            "FAC_CONDICION_PAGO VARCHAR(25) DEFAULT 'Contado', " +
            "FAC_NUM_PARCIALIDADES INTEGER DEFAULT 0, " +
            "FAC_SUBTOTAL DECIMAL(14,2) DEFAULT 0, " +
            "FAC_DESCUENTO DECIMAL(14,2) DEFAULT 0, " +
            "FAC_TOTAL_IVA DECIMAL(14,2) DEFAULT 0, " +
            "FAC_TOTAL_ISR DECIMAL(14,2) DEFAULT 0, " +
            "FAC_TOTAL_RETENCIONES DECIMAL(14,2) DEFAULT 0, " +
            "FAC_TOTAL DECIMAL(14,2) DEFAULT 0, " +
            "FAC_MONEDA VARCHAR(5) DEFAULT 'MXN', " +
            "FAC_TIPO_CAMBIO DECIMAL(10,4) DEFAULT 1.0000, " +
            "FAC_RECEPTOR_RFC VARCHAR(13), " +
            "FAC_RECEPTOR_RAZON VARCHAR(200), " +
            "FAC_RECEPTOR_REGIMEN VARCHAR(10), " +
            "FAC_RECEPTOR_CP VARCHAR(5), " +
            "FAC_RECEPTOR_USO_CFDI VARCHAR(3) DEFAULT 'G03', " +
            "FAC_RECEPTOR_EMAIL VARCHAR(150), " +
            "FAC_PED_ID INTEGER, " +
            "FAC_RUT_ID INTEGER, " +
            "FAC_XML_TIMBRADO CLOB, " +
            "FAC_PDF_URL VARCHAR(500), " +
            "FAC_ESTATUS VARCHAR(15) DEFAULT 'PENDIENTE', " +
            "FAC_MOTIVO_CANCELACION VARCHAR(200), " +
            "FAC_UUID_SUSTITUCION VARCHAR(40), " +
            "FAC_TIPO_DOCUMENTO VARCHAR(10) DEFAULT 'INGRESO', " +
            "FAC_NOTAS VARCHAR(500), " +
            "FAC_FECHA_REGISTRO TIMESTAMP DEFAULT CURRENT_TIMESTAMP" +
            ")");
        System.out.println("  [OK] CFDI_FACTURAS");

        // 4. Conceptos de cada factura
        tablas += executeDDL(conn, "DROP TABLE TESTLIB.CFDI_FACTURAS_DET IF EXISTS");
        tablas += executeDDL(conn, "CREATE TABLE TESTLIB.CFDI_FACTURAS_DET (" +
            "FAD_ID INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY, " +
            "FAC_ID INTEGER NOT NULL, " +
            "FAD_NO_SECUENCIA INTEGER NOT NULL, " +
            "FAD_CLAVE_PROD_SERV VARCHAR(20) NOT NULL, " +
            "FAD_CLAVE_UNIDAD VARCHAR(10) NOT NULL, " +
            "FAD_UNIDAD VARCHAR(50) NOT NULL, " +
            "FAD_DESCRIPCION VARCHAR(250) NOT NULL, " +
            "FAD_CANTIDAD DECIMAL(12,4) DEFAULT 1, " +
            "FAD_VALOR_UNITARIO DECIMAL(12,2) DEFAULT 0, " +
            "FAD_DESCUENTO DECIMAL(12,2) DEFAULT 0, " +
            "FAD_SUBTOTAL DECIMAL(14,2) DEFAULT 0, " +
            "FAD_IVA_DECIMAL DECIMAL(14,2) DEFAULT 0, " +
            "FAD_ISR DECIMAL(14,2) DEFAULT 0, " +
            "FAD_RETENCIONES DECIMAL(14,2) DEFAULT 0, " +
            "FAD_TOTAL DECIMAL(14,2) DEFAULT 0, " +
            "FAD_OBJETO_IMPUESTO VARCHAR(5) DEFAULT '002', " +
            "FAD_IVA_TASA DECIMAL(5,4) DEFAULT 0.1600" +
            ")");
        System.out.println("  [OK] CFDI_FACTURAS_DET");

        // 5. Complemento de pagos
        tablas += executeDDL(conn, "DROP TABLE TESTLIB.CFDI_COMPLEMENTO_PAGO IF EXISTS");
        tablas += executeDDL(conn, "CREATE TABLE TESTLIB.CFDI_COMPLEMENTO_PAGO (" +
            "CPG_ID INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY, " +
            "FAC_ID_PAGO INTEGER NOT NULL, " +
            "CPG_UUID_PAGO VARCHAR(40), " +
            "CPG_FECHA_PAGO TIMESTAMP DEFAULT CURRENT_TIMESTAMP, " +
            "CPG_FORMA_PAGO_RPC VARCHAR(5) NOT NULL, " +
            "CPG_MONTO_PAGO DECIMAL(14,2) NOT NULL, " +
            "CPG_MONEDA_PAGO VARCHAR(5) DEFAULT 'MXN', " +
            "CPG_NUM_OPERACION VARCHAR(100), " +
            "CPG_BANCO_EMISOR VARCHAR(100), " +
            "CPG_CTA_EMISOR VARCHAR(20), " +
            "CPG_BANCO_RECEPTOR VARCHAR(100), " +
            "CPG_CTA_RECEPTOR VARCHAR(20), " +
            "CPG_REFERENCIA VARCHAR(100), " +
            "CPG_ESTATUS VARCHAR(15) DEFAULT 'PENDIENTE'" +
            ")");
        System.out.println("  [OK] CFDI_COMPLEMENTO_PAGO");

        // 6. Logs de timbrado (PAC)
        tablas += executeDDL(conn, "DROP TABLE TESTLIB.CFDI_TIMBRADO_LOG IF EXISTS");
        tablas += executeDDL(conn, "CREATE TABLE TESTLIB.CFDI_TIMBRADO_LOG (" +
            "TIM_ID INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY, " +
            "FAC_ID INTEGER NOT NULL, " +
            "TIM_PAC VARCHAR(50) NOT NULL, " +
            "TIM_REQUEST CLOB, " +
            "TIM_RESPONSE CLOB, " +
            "TIM_CODIGO_RESPUESTA VARCHAR(20), " +
            "TIM_MENSAJE VARCHAR(500), " +
            "TIM_FECHA TIMESTAMP DEFAULT CURRENT_TIMESTAMP, " +
            "TIM_EXITOSO CHAR(1) DEFAULT 'N'" +
            ")");
        System.out.println("  [OK] CFDI_TIMBRADO_LOG");

        // 7. Secuencias de folios por empresa
        tablas += executeDDL(conn, "DROP TABLE TESTLIB.CFDI_FOLIOS IF EXISTS");
        tablas += executeDDL(conn, "CREATE TABLE TESTLIB.CFDI_FOLIOS (" +
            "FOL_ID INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY, " +
            "EMP_ID INTEGER NOT NULL, " +
            "FOL_SERIE VARCHAR(25) NOT NULL, " +
            "FOL_SIGUIENTE INTEGER DEFAULT 1, " +
            "FOL_FINAL INTEGER DEFAULT 999999, " +
            "FOL_ESTATUS VARCHAR(10) DEFAULT 'ACTIVO'" +
            ")");
        System.out.println("  [OK] CFDI_FOLIOS");

        conn.commit();

        // ========================================
        // TABLAS DE PAGOS
        // ========================================
        System.out.println("\n--- PAGOS ---");

        // 8. Métodos de pago del tenant
        tablas += executeDDL(conn, "DROP TABLE TESTLIB.PAGOS_METODOS IF EXISTS");
        tablas += executeDDL(conn, "CREATE TABLE TESTLIB.PAGOS_METODOS (" +
            "PMT_ID INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY, " +
            "EMP_ID INTEGER NOT NULL, " +
            "PMT_TIPO VARCHAR(30) NOT NULL, " +
            "PMT_NOMBRE VARCHAR(100) NOT NULL, " +
            "PMT_ACTIVO CHAR(1) DEFAULT 'S', " +
            "PMT_CONFIG JSON DEFAULT '{}'" +
            ")");
        System.out.println("  [OK] PAGOS_METODOS");

        // 9. Transacciones de pago
        tablas += executeDDL(conn, "DROP TABLE TESTLIB.PAGOS_TRANSACCIONES IF EXISTS");
        tablas += executeDDL(conn, "CREATE TABLE TESTLIB.PAGOS_TRANSACCIONES (" +
            "TRP_ID INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY, " +
            "EMP_ID INTEGER NOT NULL, " +
            "PED_ID INTEGER, " +
            "FAC_ID INTEGER, " +
            "TRP_NUM_REFERENCIA VARCHAR(100), " +
            "TRP_MONTO DECIMAL(14,2) NOT NULL, " +
            "TRP_MONEDA VARCHAR(5) DEFAULT 'MXN', " +
            "TRP_METODO VARCHAR(30) NOT NULL, " +
            "TRP_ESTATUS VARCHAR(20) DEFAULT 'PENDIENTE', " +
            "TRP_FECHA_REGISTRO TIMESTAMP DEFAULT CURRENT_TIMESTAMP, " +
            "TRP_FECHA_CONCILIACION TIMESTAMP, " +
            "TRP_CONCILIADO CHAR(1) DEFAULT 'N', " +
            "TRP_NOTAS VARCHAR(500), " +
            "TRP_JSON_RESPUESTA CLOB" +
            ")");
        System.out.println("  [OK] PAGOS_TRANSACCIONES");

        // 10. Referencias OXXO
        tablas += executeDDL(conn, "DROP TABLE TESTLIB.PAGOS_OXXO IF EXISTS");
        tablas += executeDDL(conn, "CREATE TABLE TESTLIB.PAGOS_OXXO (" +
            "OXX_ID INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY, " +
            "TRP_ID INTEGER NOT NULL, " +
            "OXX_REFERENCIA VARCHAR(50) NOT NULL, " +
            "OXX_CODIGO_BARRAS VARCHAR(500), " +
            "OXX_FECHA_VENCIMIENTO DATE, " +
            "OXX_MONTO_PAGO DECIMAL(14,2), " +
            "OXX_FECHA_PAGO TIMESTAMP, " +
            "OXX_NUM_CAJERO VARCHAR(20), " +
            "OXX_ESTATUS VARCHAR(15) DEFAULT 'PENDIENTE'" +
            ")");
        System.out.println("  [OK] PAGOS_OXXO");

        // 11. Transferencias SPEI
        tablas += executeDDL(conn, "DROP TABLE TESTLIB.PAGOS_SPEI IF EXISTS");
        tablas += executeDDL(conn, "CREATE TABLE TESTLIB.PAGOS_SPEI (" +
            "SPE_ID INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY, " +
            "TRP_ID INTEGER NOT NULL, " +
            "SPE_CLAVE_RASTREO VARCHAR(30), " +
            "SPE_BANCO_EMISOR VARCHAR(10), " +
            "SPE_CTA_EMISOR VARCHAR(20), " +
            "SPE_BANCO_RECEPTOR VARCHAR(10), " +
            "SPE_CTA_RECEPTOR VARCHAR(20), " +
            "SPE_MONTO DECIMAL(14,2), " +
            "SPE_FECHA TIMESTAMP DEFAULT CURRENT_TIMESTAMP, " +
            "SPE_CONCEPTO VARCHAR(200), " +
            "SPE_ESTATUS VARCHAR(15) DEFAULT 'ENVIADO'" +
            ")");
        System.out.println("  [OK] PAGOS_SPEI");

        // 12. Mercado Pago
        tablas += executeDDL(conn, "DROP TABLE TESTLIB.PAGOS_MERCADOPAGO IF EXISTS");
        tablas += executeDDL(conn, "CREATE TABLE TESTLIB.PAGOS_MERCADOPAGO (" +
            "MPG_ID INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY, " +
            "TRP_ID INTEGER NOT NULL, " +
            "MPG_MP_PAYMENT_ID VARCHAR(50), " +
            "MPG_MP_PREFERENCE_ID VARCHAR(50), " +
            "MPG_MP_STATUS VARCHAR(30), " +
            "MPG_MP_STATUS_DETAIL VARCHAR(50), " +
            "MPG_MP_APPROVED CHAR(1) DEFAULT 'N', " +
            "MPG_MP_AMOUNT DECIMAL(14,2), " +
            "MPG_MP_CURRENCY VARCHAR(5), " +
            "MPG_MP_PAYMENT_METHOD VARCHAR(30), " +
            "MPG_MP_DATE_created TIMESTAMP, " +
            "MPG_MP_DATE_APPROVED TIMESTAMP, " +
            "MPG_WEBHOOK_RAW CLOB, " +
            "MPG_ESTATUS_LOCAL VARCHAR(15) DEFAULT 'PENDIENTE'" +
            ")");
        System.out.println("  [OK] PAGOS_MERCADOPAGO");

        // 13. Conciliación bancaria
        tablas += executeDDL(conn, "DROP TABLE TESTLIB.PAGOS_CONCILIACION IF EXISTS");
        tablas += executeDDL(conn, "CREATE TABLE TESTLIB.PAGOS_CONCILIACION (" +
            "CON_ID INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY, " +
            "EMP_ID INTEGER NOT NULL, " +
            "CON_FECHA_MOV DATE NOT NULL, " +
            "CON_DESCRIPCION VARCHAR(300), " +
            "CON_MONTO_MOV DECIMAL(14,2), " +
            "CON_TIPO_MOV VARCHAR(10), " +
            "CON_REFERENCIA VARCHAR(100), " +
            "CON_TRP_ID INTEGER, " +
            "CON_CONCILIADO CHAR(1) DEFAULT 'N', " +
            "CON_USUARIO VARCHAR(50), " +
            "CON_FECHA_CONCILIACION TIMESTAMP" +
            ")");
        System.out.println("  [OK] PAGOS_CONCILIACION");

        conn.commit();

        // ========================================
        // DATOS DE EJEMPLO
        // ========================================
        System.out.println("\n--- DATOS DE EJEMPLO ---");

        // Datos fiscales Emp 1
        registros += executeInsert(conn,
            "INSERT INTO TESTLIB.CFDI_EMPRESA_FISCAL (EMP_ID, FISC_RFC, FISC_RAZON_SOCIAL, FISC_REGIMEN_FISCAL, FISC_CODIGO_POSTAL, FISC_COLONIA, FISC_CALLE, FISC_NUMERO_EXTERIOR, FISC_MUNICIPIO, FISC_ESTADO, FISC_TELEFONO, FISC_EMAIL, FISC_TIPO_PERSONA) " +
            "VALUES (1, 'DEL123456789', 'DELIVERY EXPRESS MX SA DE CV', '601', '06140', 'CONDESA', 'AV REVOLUCION', '1234', 'CIUDAD DE MEXICO', 'CDMX', '5512345678', 'facturacion@delmx.com', 'M')");

        registros += executeInsert(conn,
            "INSERT INTO TESTLIB.CFDI_EMPRESA_FISCAL (EMP_ID, FISC_RFC, FISC_RAZON_SOCIAL, FISC_REGIMEN_FISCAL, FISC_CODIGO_POSTAL, FISC_COLONIA, FISC_CALLE, FISC_NUMERO_EXTERIOR, FISC_MUNICIPIO, FISC_ESTADO, FISC_TELEFONO, FISC_EMAIL, FISC_TIPO_PERSONA) " +
            "VALUES (2, 'TRA987654321', 'TRANSPORTE RAPIDO SA DE CV', '601', '44100', 'CENTRO', 'CALLE 5 DE MAYO', '500', 'GUADALAJARA', 'JALISCO', '3312345678', 'facturacion@trapido.com', 'M')");

        registros += executeInsert(conn,
            "INSERT INTO TESTLIB.CFDI_EMPRESA_FISCAL (EMP_ID, FISC_RFC, FISC_RAZON_SOCIAL, FISC_REGIMEN_FISCAL, FISC_CODIGO_POSTAL, FISC_COLONIA, FISC_CALLE, FISC_NUMERO_EXTERIOR, FISC_MUNICIPIO, FISC_ESTADO, FISC_TELEFONO, FISC_EMAIL, FISC_TIPO_PERSONA) " +
            "VALUES (3, 'LOI555666777', 'LOGISTICA INTEGRAL MX SA DE CV', '601', '64000', 'MONTERREY', 'AV CONSTITUCION', '800', 'MONTERREY', 'NUEVO LEON', '8112345678', 'facturacion@loint.com', 'M')");

        System.out.println("  [OK] 3 datos fiscales");

        // Catálogo de conceptos (servicios last mile)
        String[][] conceptos = {
            {"1", "84111506", "E48", "SERVICIO", "Servicio de envio/entrega last mile", "89.00", "002"},
            {"1", "84111506", "E48", "SERVICIO", "Servicio de recoleccion/inversa", "120.00", "002"},
            {"1", "84111506", "E48", "SERVICIO", "Servicio de almacenaje diario", "45.00", "002"},
            {"1", "78101800", "H87", "PIEZA", "Material de embalaje", "12.50", "002"},
            {"1", "84132000", "E48", "SERVICIO", "Flete urgentes/mismo dia", "180.00", "002"},
            {"2", "84111506", "E48", "SERVICIO", "Envio paqueteria estandar", "75.00", "002"},
            {"2", "84111506", "E48", "SERVICIO", "Envio express 24hrs", "150.00", "002"},
            {"3", "84111506", "E48", "SERVICIO", "Entrega last mile zona metropolitana", "95.00", "002"},
            {"3", "84111506", "E48", "SERVICIO", "Entrega zona foranea", "210.00", "002"},
        };
        for (String[] c : conceptos) {
            registros += executeInsert(conn,
                "INSERT INTO TESTLIB.CFDI_CONCEPTOS_CATALOGO (EMP_ID, COC_CLAVE_PROD_SERV, COC_CLAVE_UNIDAD, COC_UNIDAD, COC_DESCRIPCION, COC_VALOR_UNITARIO, COC_OBJETO_IMPUESTO) " +
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                c[0], c[1], c[2], c[3], c[4], c[5], c[6]);
        }
        System.out.println("  [OK] 9 conceptos catalogo");

        // Folios por empresa
        registros += executeInsert(conn, "INSERT INTO TESTLIB.CFDI_FOLIOS (EMP_ID, FOL_SERIE, FOL_SIGUIENTE, FOL_FINAL) VALUES (1, 'A', 1, 999999)");
        registros += executeInsert(conn, "INSERT INTO TESTLIB.CFDI_FOLIOS (EMP_ID, FOL_SERIE, FOL_SIGUIENTE, FOL_FINAL) VALUES (2, 'B', 1, 999999)");
        registros += executeInsert(conn, "INSERT INTO TESTLIB.CFDI_FOLIOS (EMP_ID, FOL_SERIE, FOL_SIGUIENTE, FOL_FINAL) VALUES (3, 'C', 1, 999999)");
        System.out.println("  [OK] 3 folios");

        // Métodos de pago
        registros += executeInsert(conn, "INSERT INTO TESTLIB.PAGOS_METODOS (EMP_ID, PMT_TIPO, PMT_NOMBRE) VALUES (1, 'EFECTIVO', 'Efectivo')");
        registros += executeInsert(conn, "INSERT INTO TESTLIB.PAGOS_METODOS (EMP_ID, PMT_TIPO, PMT_NOMBRE) VALUES (1, 'OXXO', 'Deposito OXXO')");
        registros += executeInsert(conn, "INSERT INTO TESTLIB.PAGOS_METODOS (EMP_ID, PMT_TIPO, PMT_NOMBRE) VALUES (1, 'SPEI', 'Transferencia SPEI')");
        registros += executeInsert(conn, "INSERT INTO TESTLIB.PAGOS_METODOS (EMP_ID, PMT_TIPO, PMT_NOMBRE) VALUES (1, 'MERCADOPAGO', 'Mercado Pago')");
        registros += executeInsert(conn, "INSERT INTO TESTLIB.PAGOS_METODOS (EMP_ID, PMT_TIPO, PMT_NOMBRE) VALUES (1, 'TARJETA_CREDITO', 'Tarjeta de Credito')");
        registros += executeInsert(conn, "INSERT INTO TESTLIB.PAGOS_METODOS (EMP_ID, PMT_TIPO, PMT_NOMBRE) VALUES (1, 'TARJETA_DEBITO', 'Tarjeta de Debito')");
        registros += executeInsert(conn, "INSERT INTO TESTLIB.PAGOS_METODOS (EMP_ID, PMT_TIPO, PMT_NOMBRE) VALUES (2, 'EFECTIVO', 'Efectivo')");
        registros += executeInsert(conn, "INSERT INTO TESTLIB.PAGOS_METODOS (EMP_ID, PMT_TIPO, PMT_NOMBRE) VALUES (2, 'SPEI', 'Transferencia SPEI')");
        registros += executeInsert(conn, "INSERT INTO TESTLIB.PAGOS_METODOS (EMP_ID, PMT_TIPO, PMT_NOMBRE) VALUES (3, 'EFECTIVO', 'Efectivo')");
        registros += executeInsert(conn, "INSERT INTO TESTLIB.PAGOS_METODOS (EMP_ID, PMT_TIPO, PMT_NOMBRE) VALUES (3, 'MERCADOPAGO', 'Mercado Pago')");
        System.out.println("  [OK] 10 metodos de pago");

        // Algunas transacciones de ejemplo
        registros += executeInsert(conn,
            "INSERT INTO TESTLIB.PAGOS_TRANSACCIONES (EMP_ID, PED_ID, TRP_NUM_REFERENCIA, TRP_MONTO, TRP_METODO, TRP_ESTATUS) " +
            "VALUES (1, 1, 'OXXO-2026-001', 194.86, 'OXXO', 'PAGADO')");
        registros += executeInsert(conn,
            "INSERT INTO TESTLIB.PAGOS_TRANSACCIONES (EMP_ID, PED_ID, TRP_NUM_REFERENCIA, TRP_MONTO, TRP_METODO, TRP_ESTATUS) " +
            "VALUES (1, 2, 'SPEI-2026-001', 200.32, 'SPEI', 'PAGADO')");
        registros += executeInsert(conn,
            "INSERT INTO TESTLIB.PAGOS_TRANSACCIONES (EMP_ID, PED_ID, TRP_NUM_REFERENCIA, TRP_MONTO, TRP_METODO, TRP_ESTATUS) " +
            "VALUES (2, 3, 'MP-2026-001', 135.75, 'MERCADOPAGO', 'PENDIENTE')");
        registros += executeInsert(conn,
            "INSERT INTO TESTLIB.PAGOS_TRANSACCIONES (EMP_ID, PED_ID, TRP_NUM_REFERENCIA, TRP_MONTO, TRP_METODO, TRP_ESTATUS) " +
            "VALUES (1, 5, 'EF-2026-001', 215.66, 'EFECTIVO', 'PAGADO')");
        registros += executeInsert(conn,
            "INSERT INTO TESTLIB.PAGOS_TRANSACCIONES (EMP_ID, PED_ID, TRP_NUM_REFERENCIA, TRP_MONTO, TRP_METODO, TRP_ESTATUS) " +
            "VALUES (3, 4, 'MP-2026-002', 175.41, 'MERCADOPAGO', 'PAGADO')");
        System.out.println("  [OK] 5 transacciones ejemplo");

        conn.commit();
        conn.close();

        System.out.println("\n==========================================");
        System.out.println("  COMPLETADO");
        System.out.println("  Tablas creadas:  " + tablas);
        System.out.println("  Registros:       " + registros);
        System.out.println("==========================================");
    }

    static int executeDDL(Connection conn, String sql) throws SQLException {
        Statement stmt = conn.createStatement();
        try { stmt.execute(sql); } catch (SQLException e) {
            if (!e.getMessage().contains("does not exist")) {
                System.out.println("  WARN: " + e.getMessage().substring(0, Math.min(60, e.getMessage().length())));
            }
        }
        stmt.close();
        return 1;
    }

    static int executeInsert(Connection conn, String sql, Object... params) throws SQLException {
        PreparedStatement ps = conn.prepareStatement(sql);
        for (int i = 0; i < params.length; i++) {
            ps.setString(i + 1, params[i].toString());
        }
        int rows = ps.executeUpdate();
        ps.close();
        return rows;
    }
}
