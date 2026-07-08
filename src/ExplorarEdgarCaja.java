import java.sql.*;
import java.util.*;

/**
 * EXPLORADOR EDGAR + BUSQUEDA CAJA CHICA
 * Solo lectura - NO modifica nada
 */
public class ExplorarEdgarCaja {

    static final String URL = "jdbc:as400://192.168.0.240;libraries=QSYS2;errors=full";
    static final String USER = "AYUDATX";
    static final String PASS = "MXTAC23";

    public static void main(String[] args) throws Exception {
        System.out.println("========================================");
        System.out.println(" EXPLORADOR EDGAR + CAJA CHICA");
        System.out.println("========================================\n");

        Connection conn = DriverManager.getConnection(URL, USER, PASS);
        System.out.println("[OK] Conexion establecida\n");

        // 1. Explorar EDGAR a fondo
        System.out.println("========================================");
        System.out.println(" SISTEMA EDGAR");
        System.out.println("========================================");
        exploreLibraryFull(conn, "EDGAR");

        // 2. Buscar tablas con "CAJA" o "CHICA" o "EFECT" en TODAS las librerías
        System.out.println("\n========================================");
        System.out.println(" BUSQUEDA: CAJA CHICA / EFECTIVO");
        System.out.println("========================================");
        searchCajaChica(conn);

        // 3. Buscar por tablas financieras en todas las libs
        System.out.println("\n========================================");
        System.out.println(" BUSQUEDA: TABLAS FINANCIERAS");
        System.out.println("========================================");
        searchFinancialTables(conn);

        // 4. Explorar libs TACCOM, TPCOM, ROMCOM (código fuente)
        System.out.println("\n========================================");
        System.out.println(" EXPLORAR LIBRERÍAS DE CÓDIGO");
        System.out.println("========================================");
        exploreSourceLib(conn, "TACCOM");
        exploreSourceLib(conn, "TPCOM");
        exploreSourceLib(conn, "ROMCOM");
        exploreSourceLib(conn, "SLMSRC");
        exploreSourceLib(conn, "SLMOBJ");

        conn.close();
        System.out.println("\n[OK] Exploracion completada");
    }

    static void exploreLibraryFull(Connection conn, String lib) throws Exception {
        // Tablas
        String sql = "SELECT TABLE_NAME, TABLE_TEXT FROM QSYS2.SYSTABLES " +
                     "WHERE TABLE_SCHEMA = '" + lib + "' ORDER BY TABLE_NAME";
        Statement stmt = conn.createStatement();
        ResultSet rs;
        try {
            rs = stmt.executeQuery(sql);
        } catch (Exception e) {
            System.out.println("  Librería " + lib + " no encontrada o sin tablas");
            return;
        }

        List<String[]> tables = new ArrayList<>();
        while (rs.next()) {
            tables.add(new String[]{rs.getString("TABLE_NAME"), rs.getString("TABLE_TEXT")});
        }
        rs.close();

        if (tables.isEmpty()) {
            System.out.println("  Sin tablas de datos en " + lib);
            return;
        }

        System.out.println("  Tablas encontradas: " + tables.size());
        for (int i = 0; i < tables.size(); i++) {
            String[] t = tables.get(i);
            System.out.println("    [" + (i+1) + "] " + t[0] +
                (t[1] != null && !t[1].trim().isEmpty() ? " - " + t[1].trim() : ""));
        }

        // Contar registros y mostrar estructura
        System.out.println("\n  --- VOLUMEN Y ESTRUCTURA ---");
        long totalRecords = 0;
        for (String[] t : tables) {
            String table = t[0];
            long count = 0;
            try {
                Statement cs = conn.createStatement();
                ResultSet cr = cs.executeQuery("SELECT COUNT(*) AS CNT FROM " + lib + "." + table);
                if (cr.next()) count = cr.getLong("CNT");
                cr.close(); cs.close();
            } catch (Exception e) { count = -1; }

            if (count > 0) {
                System.out.println("    " + padRight(table, 20) + count + " registros");
                totalRecords += count;

                // Mostrar estructura de las principales
                if (count > 10) {
                    showColumns(conn, lib, table);
                }
            }
        }
        System.out.println("    TOTAL " + lib + ": " + totalRecords + " registros");
    }

    static void showColumns(Connection conn, String lib, String table) throws Exception {
        String sql = "SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH, " +
                     "NUMERIC_PRECISION, NUMERIC_SCALE, COLUMN_TEXT " +
                     "FROM QSYS2.SYSCOLUMNS " +
                     "WHERE TABLE_SCHEMA = '" + lib + "' " +
                     "AND TABLE_NAME = '" + table + "' " +
                     "ORDER BY ORDINAL_POSITION";
        Statement stmt = conn.createStatement();
        ResultSet rs;
        try {
            rs = stmt.executeQuery(sql);
        } catch (Exception e) { return; }

        List<String[]> cols = new ArrayList<>();
        while (rs.next()) {
            cols.add(new String[]{
                rs.getString("COLUMN_NAME"),
                rs.getString("DATA_TYPE"),
                rs.getString("CHARACTER_MAXIMUM_LENGTH"),
                rs.getString("NUMERIC_PRECISION"),
                rs.getString("NUMERIC_SCALE"),
                rs.getString("COLUMN_TEXT")
            });
        }
        rs.close();

        if (!cols.isEmpty()) {
            System.out.println("      Estructura de " + table + " (" + cols.size() + " campos):");
            for (String[] c : cols) {
                String type = c[1];
                if ("CHARACTER".equals(type) || "VARCHAR".equals(type)) type += "(" + c[2] + ")";
                else if ("DECIMAL".equals(type) || "NUMERIC".equals(type)) type += "(" + c[3] + "," + c[4] + ")";
                System.out.println("        " + padRight(c[0], 22) + padRight(type, 20) +
                    (c[5] != null ? c[5].trim() : ""));
            }
        }
    }

    static void searchCajaChica(Connection conn) throws Exception {
        String[] searchTerms = {"CAJA", "CHICA", "EFECT", "CHQ", "CHEQUE", "FONDO", "RENDICION", "GASTO", "COMPROBANTE"};
        String[] libs = {"TACDB", "TPDB", "ROMDB", "EDGAR", "SITDB", "SLMDB", "LIBRARY", "TACCOM", "TPCOM", "ROMCOM"};

        for (String lib : libs) {
            for (String term : searchTerms) {
                String sql = "SELECT TABLE_NAME, TABLE_TEXT FROM QSYS2.SYSTABLES " +
                             "WHERE TABLE_SCHEMA = '" + lib + "' " +
                             "AND (UPPER(TABLE_NAME) LIKE '%" + term + "%' " +
                             "OR UPPER(TABLE_TEXT) LIKE '%" + term + "%') " +
                             "ORDER BY TABLE_NAME";
                Statement stmt = conn.createStatement();
                try {
                    ResultSet rs = stmt.executeQuery(sql);
                    while (rs.next()) {
                        String name = rs.getString("TABLE_NAME");
                        String text = rs.getString("TABLE_TEXT");
                        System.out.println("  [" + lib + "] " + name +
                            (text != null && !text.trim().isEmpty() ? " - " + text.trim() : "") +
                            " (búsqueda: " + term + ")");
                    }
                    rs.close();
                } catch (Exception e) { }
            }
        }
    }

    static void searchFinancialTables(Connection conn) throws Exception {
        String sql = "SELECT TABLE_SCHEMA, TABLE_NAME, TABLE_TEXT " +
                     "FROM QSYS2.SYSTABLES " +
                     "WHERE TABLE_SCHEMA NOT LIKE 'Q%' " +
                     "AND TABLE_SCHEMA NOT LIKE 'IBM%' " +
                     "AND TABLE_SCHEMA NOT IN ('TOOLS', 'TESTLIB', 'SYSIBM', 'SYSIBMADM', 'SYSPROC', 'SYSTOOLS') " +
                     "AND (UPPER(TABLE_NAME) LIKE '%CAJA%' " +
                     "OR UPPER(TABLE_NAME) LIKE '%PAGO%' " +
                     "OR UPPER(TABLE_NAME) LIKE '%ABONO%' " +
                     "OR UPPER(TABLE_NAME) LIKE '%COBR%' " +
                     "OR UPPER(TABLE_NAME) LIKE '%FACT%' " +
                     "OR UPPER(TABLE_NAME) LIKE '%INGRE%' " +
                     "OR UPPER(TABLE_NAME) LIKE '%EGRESO%' " +
                     "OR UPPER(TABLE_NAME) LIKE '%POLIZA%' " +
                     "OR UPPER(TABLE_NAME) LIKE '%CONTAB%' " +
                     "OR UPPER(TABLE_NAME) LIKE '%BANC%' " +
                     "OR UPPER(TABLE_NAME) LIKE '%EFECT%' " +
                     "OR UPPER(TABLE_NAME) LIKE '%CHEQUE%' " +
                     "OR UPPER(TABLE_NAME) LIKE '%FONDO%' " +
                     "OR UPPER(TABLE_NAME) LIKE '%GASTO%' " +
                     "OR UPPER(TABLE_NAME) LIKE '%COMPROB%') " +
                     "ORDER BY TABLE_SCHEMA, TABLE_NAME";
        Statement stmt = conn.createStatement();
        ResultSet rs = stmt.executeQuery(sql);

        String currentLib = "";
        while (rs.next()) {
            String lib = rs.getString("TABLE_SCHEMA");
            String table = rs.getString("TABLE_NAME");
            String text = rs.getString("TABLE_TEXT");
            if (!lib.equals(currentLib)) {
                currentLib = lib;
                System.out.println("\n  --- " + lib + " ---");
            }
            System.out.println("    " + padRight(table, 20) +
                (text != null && !text.trim().isEmpty() ? text.trim() : ""));
        }
        rs.close();
    }

    static void exploreSourceLib(Connection conn, String lib) throws Exception {
        String sql = "SELECT TABLE_NAME, TABLE_TEXT FROM QSYS2.SYSTABLES " +
                     "WHERE TABLE_SCHEMA = '" + lib + "' ORDER BY TABLE_NAME";
        Statement stmt = conn.createStatement();
        ResultSet rs;
        try {
            rs = stmt.executeQuery(sql);
        } catch (Exception e) { return; }

        int count = 0;
        while (rs.next()) count++;
        rs.close();

        if (count > 0) {
            System.out.println("  " + lib + ": " + count + " objetos");
        }
    }

    static String padRight(String s, int n) {
        if (s == null) s = "";
        return String.format("%-" + n + "s", s);
    }
}
