import java.sql.*;

/**
 * Paso 1: Explorar estructura completa de tablas Last Mile en EDGAR
 */
public class CopiarLM_Paso1 {
    public static void main(String[] args) throws Exception {
        Connection c = DriverManager.getConnection(
            "jdbc:as400://192.168.0.240;libraries=EDGAR;errors=full", "AYUDATX", "MXTAC23");
        Statement s = c.createStatement();
        ResultSet rs;

        String[] tablas = {
            "UNIDADESTA", "UNIDADES", "FLOTILLA",
            "OTSXMARCA", "OTSXMARCA2", "OTSXMARCA3", "OTSXMARCA4", "OTSXMARCA5", "OTSXMARCA6", "OTSXMARCA7",
            "OTSXVEHIC", "OTSXVEHIC1", "OTSXVEHIC2", "OTSXVEHIC3", "OTSXVEHIC4", "OTSXVEHIC5", "OTSXVEHIC6", "OTSXVEHIC7",
            "REFACTALLE", "GASTOSELEC", "GASTOSPROM", "MOVCAJA",
            "OTLLANTAS", "OTLLANTASC",
            "TARIFAS", "TARIFASPRO"
        };

        System.out.println("=== ESTRUCTURA DE TABLAS LAST MILE EN EDGAR ===\n");

        for (String tabla : tablas) {
            try {
                // Contar registros
                rs = s.executeQuery("SELECT COUNT(*) FROM EDGAR." + tabla);
                rs.next();
                int count = rs.getInt(1);
                rs.close();

                if (count == 0) {
                    System.out.println("--- " + tabla + " (0 registros, skip) ---\n");
                    continue;
                }

                System.out.println("--- " + tabla + " (" + count + " registros) ---");

                // Obtener estructura
                rs = s.executeQuery(
                    "SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH, NUMERIC_PRECISION, NUMERIC_SCALE, IS_NULLABLE " +
                    "FROM QSYS2.SYSCOLUMNS WHERE TABLE_SCHEMA = 'EDGAR' AND TABLE_NAME = '" + tabla + "' ORDER BY ORDINAL_POSITION");

                while (rs.next()) {
                    String col = rs.getString("COLUMN_NAME").trim();
                    String type = rs.getString("DATA_TYPE").trim();
                    String charLen = rs.getString("CHARACTER_MAXIMUM_LENGTH");
                    String numPrec = rs.getString("NUMERIC_PRECISION");
                    String numScale = rs.getString("NUMERIC_SCALE");
                    String nullable = rs.getString("IS_NULLABLE").trim();

                    String tipo = type;
                    if (type.equals("CHARACTER") || type.equals("VARCHAR")) {
                        tipo = type + "(" + (charLen != null ? charLen : "?") + ")";
                    } else if (type.equals("DECIMAL") || type.equals("NUMERIC")) {
                        tipo = type + "(" + (numPrec != null ? numPrec : "?") + "," + (numScale != null ? numScale : "0") + ")";
                    }

                    System.out.println("  " + col + " | " + tipo + " | " + nullable);
                }
                rs.close();
                System.out.println();
            } catch (Exception e) {
                System.out.println("--- " + tabla + " (ERROR: " + e.getMessage().split("\n")[0] + ") ---\n");
            }
        }

        c.close();
        System.out.println("=== FIN ===");
    }
}
