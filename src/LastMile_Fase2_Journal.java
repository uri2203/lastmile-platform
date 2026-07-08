import java.sql.*;

/**
 * Registra journaling en tablas CFDI/Pagos y crea los datos
 */
public class LastMile_Fase2_Journal {

    static final String DB_URL = "jdbc:as400://192.168.0.240;errors=full";
    static final String USER = "AYUDATX";
    static final String PASS = "MXTAC23";

    public static void main(String[] args) throws Exception {
        Class.forName("com.ibm.as400.access.AS400JDBCDriver");
        Connection conn = DriverManager.getConnection(DB_URL, USER, PASS);
        conn.setAutoCommit(true);

        System.out.println("=== REGISTRANDO JOURNALING ===\n");

        String[] tables = {
            "CFDI_EMPRESA_FISCAL", "CFDI_CONCEPTOS_CATALOGO", "CFDI_FACTURAS",
            "CFDI_FACTURAS_DET", "CFDI_COMPLEMENTO_PAGO", "CFDI_TIMBRADO_LOG",
            "CFDI_FOLIOS", "PAGOS_METODOS", "PAGOS_TRANSACCIONES",
            "PAGOS_OXXO", "PAGOS_SPEI", "PAGOS_MERCADOPAGO", "PAGOS_CONCILIACION"
        };

        Statement stmt = conn.createStatement();
        for (String t : tables) {
            try {
                // Crear journal si no existe
                stmt.execute("CALL QSYS2.QCMDEXC('CRTJRN JRN(QTEMP/TESTJRN) JRNRCV(*GEN 1) MNGRCDE(*SYSTEM) DLTRCV(*NO)') ");
            } catch (Exception e) { /* ya existe */ }

            try {
                stmt.execute("CALL QSYS2.QCMDEXC('STRJRNPF JRNFILE(TESTLIB/" + t + ") JRN(QTEMP/TESTJRN) MNGRCDE(*SYSTEM) OMTJRNE(*NO)') ");
                System.out.println("  [OK] " + t + " - journal registrado");
            } catch (Exception e) {
                try {
                    stmt.execute("CALL QSYS2.QCMDEXC('CHGJRN JRNFILE(TESTLIB/" + t + ") JRNRCV(*SAME) IGNOPTCTL(*NO)') ");
                    System.out.println("  [OK] " + t + " - journal activado");
                } catch (Exception e2) {
                    System.out.println("  [WARN] " + t + ": " + e2.getMessage().substring(0, Math.min(60, e2.getMessage().length())));
                }
            }
        }
        stmt.close();

        Thread.sleep(3000);
        System.out.println("\n=== INSERTANDO DATOS ===\n");

        int total = 0;
        PreparedStatement ps;

        // 1. Datos fiscales
        ps = conn.prepareStatement("INSERT INTO TESTLIB.CFDI_EMPRESA_FISCAL (EMP_ID, FISC_RFC, FISC_RAZON_SOCIAL, FISC_REGIMEN_FISCAL, FISC_CODIGO_POSTAL, FISC_COLONIA, FISC_CALLE, FISC_NUMERO_EXTERIOR, FISC_MUNICIPIO, FISC_ESTADO, FISC_TELEFONO, FISC_EMAIL, FISC_TIPO_PERSONA) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)");
        ps.setInt(1, 1); ps.setString(2, "DEL123456789"); ps.setString(3, "DELIVERY EXPRESS MX SA DE CV"); ps.setString(4, "601"); ps.setString(5, "06140"); ps.setString(6, "CONDESA"); ps.setString(7, "AV REVOLUCION"); ps.setString(8, "1234"); ps.setString(9, "CIUDAD DE MEXICO"); ps.setString(10, "CDMX"); ps.setString(11, "5512345678"); ps.setString(12, "facturacion@delmx.com"); ps.setString(13, "M"); total += ps.executeUpdate(); ps.close();

        ps = conn.prepareStatement("INSERT INTO TESTLIB.CFDI_EMPRESA_FISCAL (EMP_ID, FISC_RFC, FISC_RAZON_SOCIAL, FISC_REGIMEN_FISCAL, FISC_CODIGO_POSTAL, FISC_COLONIA, FISC_CALLE, FISC_NUMERO_EXTERIOR, FISC_MUNICIPIO, FISC_ESTADO, FISC_TELEFONO, FISC_EMAIL, FISC_TIPO_PERSONA) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)");
        ps.setInt(1, 2); ps.setString(2, "TRA987654321"); ps.setString(3, "TRANSPORTE RAPIDO SA DE CV"); ps.setString(4, "601"); ps.setString(5, "44100"); ps.setString(6, "CENTRO"); ps.setString(7, "CALLE 5 DE MAYO"); ps.setString(8, "500"); ps.setString(9, "GUADALAJARA"); ps.setString(10, "JALISCO"); ps.setString(11, "3312345678"); ps.setString(12, "facturacion@trapido.com"); ps.setString(13, "M"); total += ps.executeUpdate(); ps.close();

        ps = conn.prepareStatement("INSERT INTO TESTLIB.CFDI_EMPRESA_FISCAL (EMP_ID, FISC_RFC, FISC_RAZON_SOCIAL, FISC_REGIMEN_FISCAL, FISC_CODIGO_POSTAL, FISC_COLONIA, FISC_CALLE, FISC_NUMERO_EXTERIOR, FISC_MUNICIPIO, FISC_ESTADO, FISC_TELEFONO, FISC_EMAIL, FISC_TIPO_PERSONA) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)");
        ps.setInt(1, 3); ps.setString(2, "LOI555666777"); ps.setString(3, "LOGISTICA INTEGRAL MX SA DE CV"); ps.setString(4, "601"); ps.setString(5, "64000"); ps.setString(6, "MONTERREY"); ps.setString(7, "AV CONSTITUCION"); ps.setString(8, "800"); ps.setString(9, "MONTERREY"); ps.setString(10, "NUEVO LEON"); ps.setString(11, "8112345678"); ps.setString(12, "facturacion@loint.com"); ps.setString(13, "M"); total += ps.executeUpdate(); ps.close();
        System.out.println("  [OK] 3 datos fiscales");

        // 2. Conceptos
        String[][] conceptos = {
            {"1","84111506","E48","SERVICIO","Envio/entrega last mile","89.00","002"},
            {"1","84111506","E48","SERVICIO","Recoleccion inversa","120.00","002"},
            {"1","84111506","E48","SERVICIO","Almacenaje diario","45.00","002"},
            {"1","78101800","H87","PIEZA","Material embalaje","12.50","002"},
            {"1","84132000","E48","SERVICIO","Flete urgente mismo dia","180.00","002"},
            {"2","84111506","E48","SERVICIO","Paqueteria estandar","75.00","002"},
            {"2","84111506","E48","SERVICIO","Envio express 24hrs","150.00","002"},
            {"3","84111506","E48","SERVICIO","Last mile zona metro","95.00","002"},
            {"3","84111506","E48","SERVICIO","Zona foranea","210.00","002"},
        };
        ps = conn.prepareStatement("INSERT INTO TESTLIB.CFDI_CONCEPTOS_CATALOGO (EMP_ID, COC_CLAVE_PROD_SERV, COC_CLAVE_UNIDAD, COC_UNIDAD, COC_DESCRIPCION, COC_VALOR_UNITARIO, COC_OBJETO_IMPUESTO) VALUES (?,?,?,?,?,?,?)");
        for (String[] c : conceptos) {
            ps.setInt(1, Integer.parseInt(c[0])); ps.setString(2, c[1]); ps.setString(3, c[2]); ps.setString(4, c[3]); ps.setString(5, c[4]); ps.setBigDecimal(6, new java.math.BigDecimal(c[5])); ps.setString(7, c[6]);
            total += ps.executeUpdate();
        }
        ps.close();
        System.out.println("  [OK] 9 conceptos");

        // 3. Folios
        ps = conn.prepareStatement("INSERT INTO TESTLIB.CFDI_FOLIOS (EMP_ID, FOL_SERIE, FOL_SIGUIENTE, FOL_FINAL) VALUES (?,?,?,?)");
        ps.setInt(1, 1); ps.setString(2, "A"); ps.setInt(3, 1); ps.setInt(4, 999999); total += ps.executeUpdate();
        ps.setInt(1, 2); ps.setString(2, "B"); ps.setInt(3, 1); ps.setInt(4, 999999); total += ps.executeUpdate();
        ps.setInt(1, 3); ps.setString(2, "C"); ps.setInt(3, 1); ps.setInt(4, 999999); total += ps.executeUpdate();
        ps.close();
        System.out.println("  [OK] 3 folios");

        // 4. Metodos de pago
        ps = conn.prepareStatement("INSERT INTO TESTLIB.PAGOS_METODOS (EMP_ID, PMT_TIPO, PMT_NOMBRE) VALUES (?,?,?)");
        String[][] metodos = {{"1","EFECTIVO","Efectivo"},{"1","OXXO","Deposito OXXO"},{"1","SPEI","Transferencia SPEI"},{"1","MERCADOPAGO","Mercado Pago"},{"1","TARJETA_CREDITO","Tarjeta Credito"},{"1","TARJETA_DEBITO","Tarjeta Debito"},{"2","EFECTIVO","Efectivo"},{"2","SPEI","Transferencia SPEI"},{"3","EFECTIVO","Efectivo"},{"3","MERCADOPAGO","Mercado Pago"}};
        for (String[] m : metodos) { ps.setInt(1, Integer.parseInt(m[0])); ps.setString(2, m[1]); ps.setString(3, m[2]); total += ps.executeUpdate(); }
        ps.close();
        System.out.println("  [OK] 10 metodos de pago");

        // 5. Transacciones
        ps = conn.prepareStatement("INSERT INTO TESTLIB.PAGOS_TRANSACCIONES (EMP_ID, PED_ID, TRP_NUM_REFERENCIA, TRP_MONTO, TRP_METODO, TRP_ESTATUS) VALUES (?,?,?,?,?,?)");
        String[][] trans = {{"1","1","OXXO-001","194.86","OXXO","PAGADO"},{"1","2","SPEI-001","200.32","SPEI","PAGADO"},{"2","3","MP-001","135.75","MERCADOPAGO","PENDIENTE"},{"1","5","EF-001","215.66","EFECTIVO","PAGADO"},{"3","4","MP-002","175.41","MERCADOPAGO","PAGADO"}};
        for (String[] t : trans) { ps.setInt(1, Integer.parseInt(t[0])); ps.setInt(2, Integer.parseInt(t[1])); ps.setString(3, t[2]); ps.setBigDecimal(4, new java.math.BigDecimal(t[3])); ps.setString(5, t[4]); ps.setString(6, t[5]); total += ps.executeUpdate(); }
        ps.close();
        System.out.println("  [OK] 5 transacciones");

        System.out.println("\n=== COMPLETADO: " + total + " registros ===");
        conn.close();
    }
}
