import java.sql.*;

/**
 * Corregir tablas con campos VARCHAR demasiado cortos
 */
public class CopiarLM_Corregir {
    public static void main(String[] args) throws Exception {
        Connection c = DriverManager.getConnection(
            "jdbc:as400://192.168.0.240;errors=full", "AYUDATX", "MXTAC23");
        Statement s = c.createStatement();

        System.out.println("=== CORRIGIENDO TABLAS CON VARCHAR CORTO ===\n");

        // REFACTALLE - REREFA necesita ser mas grande
        String[][] tablasCorregir = {
            {"REFACTALLE", "OTNUOT DECIMAL(7,0), OTREPA CHAR(10), OTUNTA DECIMAL(7,0), OTUNLM CHAR(10), OTTALL CHAR(20), REREFA CHAR(80), REPREU DECIMAL(10,2), REIVAR DECIMAL(10,2), RECANR DECIMAL(5,0), RERETE DECIMAL(10,2), RETOTA DECIMAL(10,2)"},
            {"GASTOSELEC", "CAJ_CONCEP CHAR(150), CAJ_NUMDOC DECIMAL(7,0), CAJ_CUEPAG DECIMAL(4,0), CAJ_USUAUT CHAR(10), CAJ_USUREC CHAR(10), CAJ_EGRESO DECIMAL(11,2), CAJ_INGRES DECIMAL(11,2), CAJ_FECTRA DECIMAL(8,0), CAJ_FECCAP DECIMAL(8,0), CAJ_HORCAP CHAR(10), CAJ_USUCAP CHAR(10), CAJ_CLAVET CHAR(10)"},
            {"MOVCAJA", "CTE_CONCEP CHAR(150), CTE_CLVEHI CHAR(10), CTE_CLAVET CHAR(10), CTE_NUMDOC DECIMAL(7,0), CTE_CUEPAG DECIMAL(4,0), CTE_USUAUT CHAR(10), CTE_USUREC CHAR(10), CTE_INGRES DECIMAL(11,2), CTE_EGRESO DECIMAL(11,2)"},
            {"OTLLANTASC", "RENUOT DECIMAL(7,0), REREFA CHAR(80), REPREU DECIMAL(10,2), REIVAR DECIMAL(10,2), RECANR DECIMAL(5,0), RERETE DECIMAL(10,2), RETOTA DECIMAL(10,2)"}
        };

        for (String[] t : tablasCorregir) {
            String tabla = t[0];
            String cols = t[1];

            try {
                // Eliminar tabla existente
                try { s.executeUpdate("DROP TABLE TESTLIB." + tabla); } catch(Exception e) {}

                // Crear con columnas correctas
                String sql = "CREATE TABLE TESTLIB." + tabla + " (" + cols + ")";
                System.out.println("Creando TESTLIB." + tabla + "...");
                s.executeUpdate(sql);

                // Copiar datos
                String insertSQL = "INSERT INTO TESTLIB." + tabla + " SELECT * FROM EDGAR." + tabla;
                int copied = s.executeUpdate(insertSQL);
                System.out.println("  OK - " + copied + " registros copiados");

            } catch (Exception e) {
                String msg = e.getMessage();
                if (msg != null) msg = msg.split("\n")[0];
                System.out.println("ERROR " + tabla + ": " + msg);
            }
        }

        // Verificación final
        System.out.println("\n=== VERIFICACION FINAL ===");
        String[] todas = {"UNIDADESTA", "UNIDADES", "FLOTILLA",
            "OTSXMARCA", "OTSXMARCA2", "OTSXMARCA3", "OTSXMARCA4", "OTSXMARCA5", "OTSXMARCA6", "OTSXMARCA7",
            "OTSXVEHIC", "OTSXVEHIC1", "OTSXVEHIC2", "OTSXVEHIC3", "OTSXVEHIC4", "OTSXVEHIC5", "OTSXVEHIC6", "OTSXVEHIC7",
            "REFACTALLE", "GASTOSELEC", "GASTOSPROM", "MOVCAJA",
            "OTLLANTAS", "OTLLANTASC", "TARIFAS", "TARIFASPRO"};

        int totalOrigen = 0, totalDestino = 0, ok = 0, fail = 0;
        for (String tabla : todas) {
            try {
                ResultSet rs1 = s.executeQuery("SELECT COUNT(*) FROM EDGAR." + tabla);
                rs1.next(); int o = rs1.getInt(1); rs1.close();
                ResultSet rs2 = s.executeQuery("SELECT COUNT(*) FROM TESTLIB." + tabla);
                rs2.next(); int d = rs2.getInt(1); rs2.close();
                totalOrigen += o; totalDestino += d;
                String st = (o == d) ? "OK" : "DIF";
                if (o == d) ok++; else fail++;
                System.out.println("  " + tabla + " | " + o + " -> " + d + " | " + st);
            } catch (Exception e) {
                fail++;
                System.out.println("  " + tabla + " | NO EXISTE EN TESTLIB");
            }
        }
        System.out.println("\nTOTAL EDGAR: " + totalOrigen + " | TOTAL TESTLIB: " + totalDestino + " | OK: " + ok + " | FAIL: " + fail);

        c.close();
        System.out.println("\n=== FIN ===");
    }
}
