import java.sql.*;

/**
 * Copiar tablas Last Mile de EDGAR a TESTLIB sin tocar nada en EDGAR
 */
public class CopiarLM_Paso2 {
    public static void main(String[] args) throws Exception {
        Connection c = DriverManager.getConnection(
            "jdbc:as400://192.168.0.240;errors=full", "AYUDATX", "MXTAC23");
        Statement s = c.createStatement();

        System.out.println("=== COPIA LAST MILE: EDGAR -> TESTLIB ===\n");

        // Primero: obtener estructura exacta de cada tabla desde SYSCOLUMNS
        String[] tablas = {
            "UNIDADESTA", "UNIDADES", "FLOTILLA",
            "OTSXMARCA", "OTSXMARCA2", "OTSXMARCA3", "OTSXMARCA4", "OTSXMARCA5", "OTSXMARCA6", "OTSXMARCA7",
            "OTSXVEHIC", "OTSXVEHIC1", "OTSXVEHIC2", "OTSXVEHIC3", "OTSXVEHIC4", "OTSXVEHIC5", "OTSXVEHIC6", "OTSXVEHIC7",
            "REFACTALLE", "GASTOSELEC", "GASTOSPROM", "MOVCAJA",
            "OTLLANTAS", "OTLLANTASC", "TARIFAS", "TARIFASPRO"
        };

        for (String tabla : tablas) {
            try {
                // Contar registros origen
                ResultSet rs = s.executeQuery("SELECT COUNT(*) FROM EDGAR." + tabla);
                rs.next();
                int countOrigen = rs.getInt(1);
                rs.close();

                if (countOrigen == 0) {
                    System.out.println("SKIP " + tabla + " (0 registros)");
                    continue;
                }

                // Verificar si ya existe en TESTLIB
                try {
                    ResultSet rs2 = s.executeQuery("SELECT COUNT(*) FROM TESTLIB." + tabla);
                    rs2.next();
                    int countDest = rs2.getInt(1);
                    rs2.close();
                    System.out.println("SKIP " + tabla + " (ya existe en TESTLIB con " + countDest + " registros)");
                    continue;
                } catch (Exception e) {
                    // No existe, OK para crear
                }

                // Obtener estructura de columnas
                rs = s.executeQuery(
                    "SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH, NUMERIC_PRECISION, NUMERIC_SCALE " +
                    "FROM QSYS2.SYSCOLUMNS WHERE TABLE_SCHEMA = 'EDGAR' AND TABLE_NAME = '" + tabla + "' " +
                    "ORDER BY ORDINAL_POSITION");

                StringBuilder createSQL = new StringBuilder();
                createSQL.append("CREATE TABLE TESTLIB.").append(tabla).append(" (");

                boolean first = true;
                while (rs.next()) {
                    String col = rs.getString("COLUMN_NAME").trim();
                    String type = rs.getString("DATA_TYPE").trim();
                    String charLen = rs.getString("CHARACTER_MAXIMUM_LENGTH");
                    String numPrec = rs.getString("NUMERIC_PRECISION");
                    String numScale = rs.getString("NUMERIC_SCALE");

                    if (!first) createSQL.append(", ");
                    first = false;

                    if (type.equals("CHARACTER")) {
                        int len = (charLen != null && !charLen.equals("N")) ? Integer.parseInt(charLen.trim()) : 10;
                        createSQL.append(col).append(" CHAR(").append(len).append(") DEFAULT ''");
                    } else if (type.equals("VARCHAR")) {
                        int len = (charLen != null && !charLen.equals("N")) ? Integer.parseInt(charLen.trim()) : 50;
                        createSQL.append(col).append(" VARCHAR(").append(len).append(") DEFAULT ''");
                    } else if (type.equals("DECIMAL") || type.equals("NUMERIC")) {
                        int prec = (numPrec != null && !numPrec.equals("N")) ? Integer.parseInt(numPrec.trim()) : 15;
                        int scale = (numScale != null && !numScale.equals("N")) ? Integer.parseInt(numScale.trim()) : 0;
                        createSQL.append(col).append(" DECIMAL(").append(prec).append(",").append(scale).append(") DEFAULT 0");
                    } else if (type.equals("INTEGER")) {
                        createSQL.append(col).append(" INTEGER DEFAULT 0");
                    } else if (type.equals("SMALLINT")) {
                        createSQL.append(col).append(" SMALLINT DEFAULT 0");
                    } else if (type.equals("BIGINT")) {
                        createSQL.append(col).append(" BIGINT DEFAULT 0");
                    } else if (type.equals("DATE")) {
                        createSQL.append(col).append(" DATE");
                    } else if (type.equals("TIMESTAMP")) {
                        createSQL.append(col).append(" TIMESTAMP");
                    } else {
                        createSQL.append(col).append(" VARCHAR(50) DEFAULT ''");
                    }
                }
                rs.close();
                createSQL.append(")");

                // Crear tabla
                System.out.println("Creando TESTLIB." + tabla + "...");
                s.executeUpdate(createSQL.toString());

                // Copiar datos con INSERT ... SELECT
                String insertSQL = "INSERT INTO TESTLIB." + tabla + " SELECT * FROM EDGAR." + tabla;
                int copied = s.executeUpdate(insertSQL);

                System.out.println("  OK - " + copied + " registros copiados");

            } catch (Exception e) {
                String msg = e.getMessage();
                if (msg != null) msg = msg.split("\n")[0];
                System.out.println("ERROR " + tabla + ": " + msg);
            }
        }

        // Verificar
        System.out.println("\n=== VERIFICACION ===");
        for (String tabla : tablas) {
            try {
                ResultSet rs1 = s.executeQuery("SELECT COUNT(*) FROM EDGAR." + tabla);
                rs1.next();
                int origen = rs1.getInt(1);
                rs1.close();

                ResultSet rs2 = s.executeQuery("SELECT COUNT(*) FROM TESTLIB." + tabla);
                rs2.next();
                int destino = rs2.getInt(1);
                rs2.close();

                String status = (origen == destino) ? "OK" : "DIFERENTE";
                System.out.println("  " + tabla + " | EDGAR: " + origen + " | TESTLIB: " + destino + " | " + status);
            } catch (Exception e) {
                // No existe en TESTLIB
            }
        }

        c.close();
        System.out.println("\n=== FIN ===");
    }
}
