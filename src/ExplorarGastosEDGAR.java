import java.sql.*;
import java.util.*;

/**
 * EXPLORAR GASTOS Y VEHICULOS EN EDGAR
 * Solo lectura
 */
public class ExplorarGastosEDGAR {

    static final String URL = "jdbc:as400://192.168.0.240;libraries=QSYS2;errors=full";
    static final String USER = "AYUDATX";
    static final String PASS = "MXTAC23";

    public static void main(String[] args) throws Exception {
        System.out.println("=== EXPLORANDO GASTOS Y VEHICULOS EN EDGAR ===\n");
        Connection conn = DriverManager.getConnection(URL, USER, PASS);

        // 1. Ver estructura de tablas de gastos
        System.out.println("--- 1. ESTRUCTURA TABLAS DE GASTOS ---");
        showCols(conn, "EDGAR", "GASTOSELEC");
        showCols(conn, "EDGAR", "GASTOSPROM");
        showCols(conn, "EDGAR", "MOVCAJA");
        showCols(conn, "EDGAR", "INGRESOSTX");
        showCols(conn, "EDGAR", "INGRESOTX");

        // 2. Ver estructura de tablas de unidades/vehiculos
        System.out.println("\n--- 2. ESTRUCTURA TABLAS DE VEHICULOS ---");
        showCols(conn, "EDGAR", "UNIDADES");
        showCols(conn, "EDGAR", "UNIDADESTA");
        showCols(conn, "EDGAR", "VEHIACTIV");

        // 3. Ver estructura de OT/ordenes de trabajo
        System.out.println("\n--- 3. ESTRUCTURA ORDENES DE TRABAJO ---");
        showCols(conn, "EDGAR", "OTSXMARCA");
        showCols(conn, "EDGAR", "REFACTALLE");
        showCols(conn, "EDGAR", "REPCLUTCH");

        // 4. Ver estructura de servicios
        System.out.println("\n--- 4. ESTRUCTURA SERVICIOS ---");
        showCols(conn, "EDGAR", "SEBXFECHA");
        showCols(conn, "EDGAR", "SEPXFECHA");
        showCols(conn, "EDGAR", "SERXFECHA");
        showCols(conn, "EDGAR", "TARIFAS");

        // 5. Contar registros en tablas clave
        System.out.println("\n--- 5. VOLUMEN ---");
        countTable(conn, "EDGAR", "GASTOSELEC");
        countTable(conn, "EDGAR", "GASTOSPROM");
        countTable(conn, "EDGAR", "MOVCAJA");
        countTable(conn, "EDGAR", "INGRESOSTX");
        countTable(conn, "EDGAR", "UNIDADES");
        countTable(conn, "EDGAR", "UNIDADESTA");
        countTable(conn, "EDGAR", "VEHIACTIV");
        countTable(conn, "EDGAR", "OTSXMARCA");
        countTable(conn, "EDGAR", "REFACTALLE");
        countTable(conn, "EDGAR", "SEPXFECHA");
        countTable(conn, "EDGAR", "SERXFECHA");

        // 6. Muestra de datos de GASTOSELEC
        System.out.println("\n--- 6. MUESTRA GASTOSELEC ---");
        sampleData(conn, "EDGAR", "GASTOSELEC", 5);

        // 7. Muestra de datos de UNIDADESTA
        System.out.println("\n--- 7. MUESTRA UNIDADESTA ---");
        sampleData(conn, "EDGAR", "UNIDADESTA", 5);

        // 8. Muestra de OTSXMARCA
        System.out.println("\n--- 8. MUESTRA OTSXMARCA ---");
        sampleData(conn, "EDGAR", "OTSXMARCA", 5);

        // 9. Muestra REFACTALLE
        System.out.println("\n--- 9. MUESTRA REFACTALLE ---");
        sampleData(conn, "EDGAR", "REFACTALLE", 5);

        // 10. Buscar relacion entre tablas
        System.out.println("\n--- 10. INTENTO DE CONSULTA GASTOS POR MODELO ---");
        tryGastosPorModelo(conn);

        conn.close();
        System.out.println("\n[OK] Exploracion completada");
    }

    static void showCols(Connection conn, String lib, String table) throws Exception {
        String sql = "SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH, NUMERIC_PRECISION, NUMERIC_SCALE, COLUMN_TEXT " +
                     "FROM QSYS2.SYSCOLUMNS WHERE TABLE_SCHEMA = '" + lib + "' AND TABLE_NAME = '" + table + "' ORDER BY ORDINAL_POSITION";
        try {
            Statement stmt = conn.createStatement();
            ResultSet rs = stmt.executeQuery(sql);
            List<String[]> cols = new ArrayList<>();
            while (rs.next()) {
                cols.add(new String[]{rs.getString("COLUMN_NAME"), rs.getString("DATA_TYPE"),
                    rs.getString("CHARACTER_MAXIMUM_LENGTH"), rs.getString("NUMERIC_PRECISION"),
                    rs.getString("NUMERIC_SCALE"), rs.getString("COLUMN_TEXT")});
            }
            rs.close();
            if (!cols.isEmpty()) {
                System.out.println("\n  " + lib + "." + table + " (" + cols.size() + " campos):");
                for (String[] c : cols) {
                    String type = c[1];
                    if ("CHARACTER".equals(type) || "VARCHAR".equals(type)) type += "(" + c[2] + ")";
                    else if ("DECIMAL".equals(type) || "NUMERIC".equals(type)) type += "(" + c[3] + "," + c[4] + ")";
                    System.out.println("    " + String.format("%-22s", c[0]) + String.format("%-20s", type) + (c[5] != null ? c[5].trim() : ""));
                }
            }
        } catch (Exception e) {
            System.out.println("  " + table + ": No encontrada o sin acceso");
        }
    }

    static void countTable(Connection conn, String lib, String table) throws Exception {
        try {
            Statement stmt = conn.createStatement();
            ResultSet rs = stmt.executeQuery("SELECT COUNT(*) AS CNT FROM " + lib + "." + table);
            if (rs.next()) {
                long cnt = rs.getLong("CNT");
                if (cnt > 0) System.out.println("  " + String.format("%-20s", table) + cnt + " registros");
            }
            rs.close();
        } catch (Exception e) { }
    }

    static void sampleData(Connection conn, String lib, String table, int rows) throws Exception {
        try {
            Statement stmt = conn.createStatement();
            ResultSet rs = stmt.executeQuery("SELECT * FROM " + lib + "." + table + " FETCH FIRST " + rows + " ROWS ONLY");
            ResultSetMetaData meta = rs.getMetaData();
            int cols = meta.getColumnCount();
            System.out.println("  " + table + " - Columnas: " + cols);
            while (rs.next()) {
                StringBuilder sb = new StringBuilder("    ");
                for (int i = 1; i <= Math.min(cols, 10); i++) {
                    sb.append(meta.getColumnName(i) + "=" + rs.getString(i));
                    if (i < Math.min(cols, 10)) sb.append(" | ");
                }
                System.out.println(sb.toString());
            }
            rs.close();
        } catch (Exception e) {
            System.out.println("  " + table + ": Error - " + e.getMessage().substring(0, Math.min(80, e.getMessage().length())));
        }
    }

    static void tryGastosPorModelo(Connection conn) throws Exception {
        // Intento 1: GASTOSELEC con UNIDADESTA
        String[] queries = {
            // Buscar si GASTOSELEC tiene placa o numero economico
            "SELECT * FROM EDGAR.GASTOSELEC FETCH FIRST 3 ROWS ONLY",

            // Buscar si REFACTALLE tiene OTNUOT y podemos unir con OTSXMARCA
            "SELECT OTMARC, SUM(RETOTA) AS TOTAL_GASTO FROM EDGAR.REFACTALLE R " +
            "JOIN EDGAR.OTSXMARCA O ON R.OTNUOT = O.OTNUOT " +
            "GROUP BY OTMARC ORDER BY TOTAL_GASTO DESC",

            // Gastos por modelo directo de OTSXMARCA con costos
            "SELECT OTMARC, COUNT(*) AS OTS, SUM(CCTOTA01) AS TOTAL_COSTO " +
            "FROM EDGAR.OTSXMARCA2 GROUP BY OTMARC ORDER BY TOTAL_COSTO DESC",

            // Unidades con modelo
            "SELECT RVMARC, RVMODL, COUNT(*) AS CANTIDAD FROM EDGAR.UNIDADESTA GROUP BY RVMARC, RVMODL ORDER BY CANTIDAD DESC"
        };

        for (int i = 0; i < queries.length; i++) {
            System.out.println("\n  Query " + (i+1) + ":");
            try {
                Statement stmt = conn.createStatement();
                ResultSet rs = stmt.executeQuery(queries[i]);
                ResultSetMetaData meta = rs.getMetaData();
                int cols = meta.getColumnCount();
                // Header
                StringBuilder header = new StringBuilder("    ");
                for (int j = 1; j <= cols; j++) header.append(String.format("%-20s", meta.getColumnName(j)));
                System.out.println(header.toString());
                // Data
                int rowCount = 0;
                while (rs.next() && rowCount < 10) {
                    StringBuilder row = new StringBuilder("    ");
                    for (int j = 1; j <= cols; j++) row.append(String.format("%-20s", rs.getString(j)));
                    System.out.println(row.toString());
                    rowCount++;
                }
                rs.close();
            } catch (Exception e) {
                System.out.println("    Error: " + e.getMessage().substring(0, Math.min(100, e.getMessage().length())));
            }
        }
    }
}
