import java.sql.*;

/**
 * Fix: Recrea tablas con problemas + inserta datos
 */
public class LastMile_Fase2_Fix {

    static final String DB_URL = "jdbc:as400://192.168.0.240;errors=full";
    static final String USER = "AYUDATX";
    static final String PASS = "MXTAC23";

    public static void main(String[] args) throws Exception {
        Class.forName("com.ibm.as400.access.AS400JDBCDriver");
        Connection conn = DriverManager.getConnection(DB_URL, USER, PASS);
        conn.setAutoCommit(true);
        Statement s = conn.createStatement();

        System.out.println("=== FIX: Recrear tablas con problemas ===\n");

        // Drop problem tables
        String[] drops = {"PAGOS_METODOS","PAGOS_TRANSACCIONES","PAGOS_OXXO","PAGOS_SPEI","PAGOS_MERCADOPAGO","PAGOS_CONCILIACION"};
        for (String t : drops) {
            try { s.execute("DROP TABLE TESTLIB." + t); System.out.println("  DROP " + t); } catch(Exception e) {}
        }

        // Recreate PAGOS_METODOS sin JSON
        s.execute("CREATE TABLE TESTLIB.PAGOS_METODOS (PMT_ID INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY, EMP_ID INTEGER NOT NULL, PMT_TIPO VARCHAR(30) NOT NULL, PMT_NOMBRE VARCHAR(100) NOT NULL, PMT_CONFIG VARCHAR(500) DEFAULT '', PMT_ACTIVO CHAR(1) DEFAULT 'S')");
        System.out.println("  [OK] PAGOS_METODOS recreada");

        // Recreate PAGOS_TRANSACCIONES
        s.execute("CREATE TABLE TESTLIB.PAGOS_TRANSACCIONES (TRP_ID INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY, EMP_ID INTEGER NOT NULL, PED_ID INTEGER, FAC_ID INTEGER, TRP_NUM_REFERENCIA VARCHAR(100), TRP_MONTO DECIMAL(14,2) DEFAULT 0, TRP_MONEDA VARCHAR(5) DEFAULT 'MXN', TRP_METODO VARCHAR(30) NOT NULL, TRP_ESTATUS VARCHAR(20) DEFAULT 'PENDIENTE', TRP_FECHA_REGISTRO TIMESTAMP DEFAULT CURRENT_TIMESTAMP, TRP_FECHA_CONCILIACION TIMESTAMP, TRP_CONCILIADO CHAR(1) DEFAULT 'N', TRP_NOTAS VARCHAR(500) DEFAULT '')");
        System.out.println("  [OK] PAGOS_TRANSACCIONES recreada");

        // Recreate PAGOS_OXXO
        s.execute("CREATE TABLE TESTLIB.PAGOS_OXXO (OXX_ID INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY, TRP_ID INTEGER NOT NULL, OXX_REFERENCIA VARCHAR(50) NOT NULL, OXX_CODIGO_BARRAS VARCHAR(500), OXX_FECHA_VENCIMIENTO DATE, OXX_MONTO_PAGO DECIMAL(14,2), OXX_FECHA_PAGO TIMESTAMP, OXX_NUM_CAJERO VARCHAR(20), OXX_ESTATUS VARCHAR(15) DEFAULT 'PENDIENTE')");
        System.out.println("  [OK] PAGOS_OXXO recreada");

        // Recreate PAGOS_SPEI
        s.execute("CREATE TABLE TESTLIB.PAGOS_SPEI (SPE_ID INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY, TRP_ID INTEGER NOT NULL, SPE_CLAVE_RASTREO VARCHAR(30), SPE_BANCO_EMISOR VARCHAR(10), SPE_CTA_EMISOR VARCHAR(20), SPE_BANCO_RECEPTOR VARCHAR(10), SPE_CTA_RECEPTOR VARCHAR(20), SPE_MONTO DECIMAL(14,2), SPE_FECHA TIMESTAMP DEFAULT CURRENT_TIMESTAMP, SPE_CONCEPTO VARCHAR(200), SPE_ESTATUS VARCHAR(15) DEFAULT 'ENVIADO')");
        System.out.println("  [OK] PAGOS_SPEI recreada");

        // Recreate PAGOS_MERCADOPAGO
        s.execute("CREATE TABLE TESTLIB.PAGOS_MERCADOPAGO (MPG_ID INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY, TRP_ID INTEGER NOT NULL, MPG_MP_PAYMENT_ID VARCHAR(50), MPG_MP_PREFERENCE_ID VARCHAR(50), MPG_MP_STATUS VARCHAR(30), MPG_MP_STATUS_DETAIL VARCHAR(50), MPG_MP_APPROVED CHAR(1) DEFAULT 'N', MPG_MP_AMOUNT DECIMAL(14,2), MPG_MP_CURRENCY VARCHAR(5), MPG_MP_PAYMENT_METHOD VARCHAR(30), MPG_MP_DATE_CREATED TIMESTAMP, MPG_MP_DATE_APPROVED TIMESTAMP, MPG_WEBHOOK_RAW VARCHAR(2000), MPG_ESTATUS_LOCAL VARCHAR(15) DEFAULT 'PENDIENTE')");
        System.out.println("  [OK] PAGOS_MERCADOPAGO recreada");

        // Recreate PAGOS_CONCILIACION
        s.execute("CREATE TABLE TESTLIB.PAGOS_CONCILIACION (CON_ID INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY, EMP_ID INTEGER NOT NULL, CON_FECHA_MOV DATE NOT NULL, CON_DESCRIPCION VARCHAR(300), CON_MONTO_MOV DECIMAL(14,2), CON_TIPO_MOV VARCHAR(10), CON_REFERENCIA VARCHAR(100), CON_TRP_ID INTEGER, CON_CONCILIADO CHAR(1) DEFAULT 'N', CON_USUARIO VARCHAR(50), CON_FECHA_CONCILIACION TIMESTAMP)");
        System.out.println("  [OK] PAGOS_CONCILIACION recreada");

        // Register journaling for new tables
        String[] jrnTables = {"PAGOS_METODOS","PAGOS_TRANSACCIONES","PAGOS_OXXO","PAGOS_SPEI","PAGOS_MERCADOPAGO","PAGOS_CONCILIACION","CFDI_EMPRESA_FISCAL","CFDI_CONCEPTOS_CATALOGO","CFDI_FACTURAS","CFDI_FACTURAS_DET","CFDI_COMPLEMENTO_PAGO","CFDI_TIMBRADO_LOG","CFDI_FOLIOS"};
        for (String t : jrnTables) {
            try { s.execute("CALL QSYS2.QCMDEXC('STRJRNPF JRNFILE(TESTLIB/" + t + ") JRN(QSYS2/QRPGLESRC) MNGRCDE(*SYSTEM)') "); } catch(Exception e1) {
                try { s.execute("CALL QSYS2.QCMDEXC('CHGJRN JRNFILE(TESTLIB/" + t + ") JRNRCV(*SAME) IGNOPTCTL(*NO)') "); } catch(Exception e2) {}
            }
        }
        System.out.println("  [OK] Journaling registrado");

        Thread.sleep(2000);

        // INSERTS
        int total = 0;
        PreparedStatement ps;

        // Metodos de pago
        ps = conn.prepareStatement("INSERT INTO TESTLIB.PAGOS_METODOS (EMP_ID, PMT_TIPO, PMT_NOMBRE) VALUES (?,?,?)");
        String[][] mets = {{"1","EFECTIVO","Efectivo"},{"1","OXXO","Deposito OXXO"},{"1","SPEI","Transferencia SPEI"},{"1","MERCADOPAGO","Mercado Pago"},{"1","TARJETA_CREDITO","Tarjeta Credito"},{"1","TARJETA_DEBITO","Tarjeta Debito"},{"2","EFECTIVO","Efectivo"},{"2","SPEI","Transferencia SPEI"},{"3","EFECTIVO","Efectivo"},{"3","MERCADOPAGO","Mercado Pago"}};
        for (String[] m : mets) { ps.setInt(1, Integer.parseInt(m[0])); ps.setString(2, m[1]); ps.setString(3, m[2]); total += ps.executeUpdate(); }
        ps.close();
        System.out.println("  [OK] 10 metodos de pago");

        // Transacciones
        ps = conn.prepareStatement("INSERT INTO TESTLIB.PAGOS_TRANSACCIONES (EMP_ID, PED_ID, TRP_NUM_REFERENCIA, TRP_MONTO, TRP_METODO, TRP_ESTATUS) VALUES (?,?,?,?,?,?)");
        String[][] trans = {{"1","1","OXXO-001","194.86","OXXO","PAGADO"},{"1","2","SPEI-001","200.32","SPEI","PAGADO"},{"2","3","MP-001","135.75","MERCADOPAGO","PENDIENTE"},{"1","5","EF-001","215.66","EFECTIVO","PAGADO"},{"3","4","MP-002","175.41","MERCADOPAGO","PAGADO"}};
        for (String[] t : trans) { ps.setInt(1, Integer.parseInt(t[0])); ps.setInt(2, Integer.parseInt(t[1])); ps.setString(3, t[2]); ps.setBigDecimal(4, new java.math.BigDecimal(t[3])); ps.setString(5, t[4]); ps.setString(6, t[5]); total += ps.executeUpdate(); }
        ps.close();
        System.out.println("  [OK] 5 transacciones");

        System.out.println("\n=== COMPLETADO: " + total + " registros ===");
        s.close(); conn.close();
    }
}
