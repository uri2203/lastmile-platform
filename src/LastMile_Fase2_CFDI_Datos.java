import java.sql.*;

/**
 * Registra journaling en las tablas CFDI y Pagos, luego inserta datos
 */
public class LastMile_Fase2_CFDI_Datos {

    static final String DB_URL = "jdbc:as400://192.168.0.240;errors=full";
    static final String USER = "AYUDATX";
    static final String PASS = "MXTAC23";

    public static void main(String[] args) throws Exception {
        Class.forName("com.ibm.as400.access.AS400JDBCDriver");
        Connection conn = DriverManager.getConnection(DB_URL, USER, PASS);
        conn.setAutoCommit(false);

        System.out.println("=== REGISTRANDO JOURNALING Y DATOS ===\n");

        // Registrar tablas en journal
        String[] tables = {
            "CFDI_EMPRESA_FISCAL", "CFDI_CONCEPTOS_CATALOGO", "CFDI_FACTURAS",
            "CFDI_FACTURAS_DET", "CFDI_COMPLEMENTO_PAGO", "CFDI_TIMBRADO_LOG",
            "CFDI_FOLIOS", "PAGOS_METODOS", "PAGOS_TRANSACCIONES",
            "PAGOS_OXXO", "PAGOS_SPEI", "PAGOS_MERCADOPAGO", "PAGOS_CONCILIACION"
        };

        // Primero intentamos registrar el journal
        Statement stmtJrn = conn.createStatement();
        for (String t : tables) {
            try {
                stmtJrn.executeUpdate(
                    "CALL QSYS2.QCMDEXC('STRJRNPF JRNFILE(TESTLIB/" + t + ") JRN(QTEMP/TESTJRN) MNGRCDE(*SYSTEM) IGNOPTCTL(*NO) OMTJRNE(*NO) ENTRYCCSID(*SYSVAL)') ");
                System.out.println("  [JRN] " + t + " registrado");
            } catch (SQLException e) {
                // Puede que ya exista, intentar activar
                try {
                    stmtJrn.executeUpdate(
                        "CALL QSYS2.QCMDEXC('CHGJRN JRNFILE(TESTLIB/" + t + ") JRNRCV(*SAME) IGNOPTCTL(*NO)') ");
                    System.out.println("  [JRN] " + t + " activado");
                } catch (SQLException e2) {
                    System.out.println("  [JRN] " + t + " skip: " + e2.getMessage().substring(0, Math.min(50, e2.getMessage().length())));
                }
            }
        }
        stmtJrn.close();

        // Esperar un momento
        Thread.sleep(2000);

        int registros = 0;

        // Datos fiscales
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

        // Catálogo de conceptos
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
                "VALUES (?, ?, ?, ?, ?, ?, ?)", c);
        }
        System.out.println("  [OK] 9 conceptos catalogo");

        // Folios
        registros += executeInsert(conn, "INSERT INTO TESTLIB.CFDI_FOLIOS (EMP_ID, FOL_SERIE, FOL_SIGUIENTE, FOL_FINAL) VALUES (1, 'A', 1, 999999)", new String[]{});
        registros += executeInsert(conn, "INSERT INTO TESTLIB.CFDI_FOLIOS (EMP_ID, FOL_SERIE, FOL_SIGUIENTE, FOL_FINAL) VALUES (2, 'B', 1, 999999)", new String[]{});
        registros += executeInsert(conn, "INSERT INTO TESTLIB.CFDI_FOLIOS (EMP_ID, FOL_SERIE, FOL_SIGUIENTE, FOL_FINAL) VALUES (3, 'C', 1, 999999)", new String[]{});
        System.out.println("  [OK] 3 folios");

        // Métodos de pago
        String[][] metodos = {
            {"1", "EFECTIVO", "Efectivo"}, {"1", "OXXO", "Deposito OXXO"},
            {"1", "SPEI", "Transferencia SPEI"}, {"1", "MERCADOPAGO", "Mercado Pago"},
            {"1", "TARJETA_CREDITO", "Tarjeta de Credito"}, {"1", "TARJETA_DEBITO", "Tarjeta de Debito"},
            {"2", "EFECTIVO", "Efectivo"}, {"2", "SPEI", "Transferencia SPEI"},
            {"3", "EFECTIVO", "Efectivo"}, {"3", "MERCADOPAGO", "Mercado Pago"},
        };
        for (String[] m : metodos) {
            registros += executeInsert(conn,
                "INSERT INTO TESTLIB.PAGOS_METODOS (EMP_ID, PMT_TIPO, PMT_NOMBRE) VALUES (?, ?, ?)", m);
        }
        System.out.println("  [OK] 10 metodos de pago");

        // Transacciones
        String[][] transacciones = {
            {"1", "1", "OXXO-2026-001", "194.86", "OXXO", "PAGADO"},
            {"1", "2", "SPEI-2026-001", "200.32", "SPEI", "PAGADO"},
            {"2", "3", "MP-2026-001", "135.75", "MERCADOPAGO", "PENDIENTE"},
            {"1", "5", "EF-2026-001", "215.66", "EFECTIVO", "PAGADO"},
            {"3", "4", "MP-2026-002", "175.41", "MERCADOPAGO", "PAGADO"},
        };
        for (String[] t : transacciones) {
            registros += executeInsert(conn,
                "INSERT INTO TESTLIB.PAGOS_TRANSACCIONES (EMP_ID, PED_ID, TRP_NUM_REFERENCIA, TRP_MONTO, TRP_METODO, TRP_ESTATUS) VALUES (?, ?, ?, ?, ?, ?)", t);
        }
        System.out.println("  [OK] 5 transacciones ejemplo");

        conn.commit();
        conn.close();

        System.out.println("\n=== COMPLETADO: " + registros + " registros insertados ===");
    }

    static int executeInsert(Connection conn, String sql, String[] params) throws SQLException {
        PreparedStatement ps = conn.prepareStatement(sql);
        for (int i = 0; i < params.length; i++) {
            ps.setString(i + 1, params[i]);
        }
        int rows = ps.executeUpdate();
        ps.close();
        return rows;
    }
}
