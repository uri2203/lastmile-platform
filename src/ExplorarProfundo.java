import java.sql.*;
import java.util.*;

/**
 * EXPLORADOR PROFUNDO - Estructura de tablas y volumen de datos
 * Solo lectura - NO modifica nada
 */
public class ExplorarProfundo {

    static final String URL = "jdbc:as400://192.168.0.240;libraries=QSYS2;errors=full";
    static final String USER = "AYUDATX";
    static final String PASS = "MXTAC23";

    public static void main(String[] args) throws Exception {
        System.out.println("========================================");
        System.out.println(" EXPLORADOR PROFUNDO AS/400 - SOLO LECTURA");
        System.out.println("========================================\n");

        Connection conn = DriverManager.getConnection(URL, USER, PASS);
        System.out.println("[OK] Conexion establecida\n");

        // Analizar TACDB (principal)
        String[] libs = {"TACDB", "TPDB", "ROMDB", "SITDB", "SLMDB", "WRKDBF", "EDGAR"};
        
        for (String lib : libs) {
            System.out.println("\n========================================");
            System.out.println(" LIBRERIA: " + lib);
            System.out.println("========================================");
            
            // Contar registros por tabla
            countRecords(conn, lib);
            
            // Estructura de tablas clave
            if (lib.equals("TACDB") || lib.equals("TPDB") || lib.equals("ROMDB")) {
                exploreKeyTables(conn, lib);
            }
        }

        conn.close();
        System.out.println("\n[OK] Exploracion completada");
    }

    static void countRecords(Connection conn, String lib) throws Exception {
        System.out.println("\n  --- VOLUMEN DE DATOS ---");
        
        String sql = "SELECT TABLE_NAME FROM QSYS2.SYSTABLES " +
                     "WHERE TABLE_SCHEMA = '" + lib + "' " +
                     "AND TABLE_TYPE = 'T' ORDER BY TABLE_NAME";
        
        Statement stmt = conn.createStatement();
        ResultSet rs;
        try {
            rs = stmt.executeQuery(sql);
        } catch (Exception e) {
            // fallback sin TABLE_TYPE
            sql = "SELECT TABLE_NAME FROM QSYS2.SYSTABLES " +
                  "WHERE TABLE_SCHEMA = '" + lib + "' ORDER BY TABLE_NAME";
            rs = stmt.executeQuery(sql);
        }
        
        List<String> tables = new ArrayList<>();
        while (rs.next()) {
            tables.add(rs.getString("TABLE_NAME"));
        }
        rs.close();
        
        long totalRecords = 0;
        for (String table : tables) {
            long count = 0;
            try {
                Statement countStmt = conn.createStatement();
                ResultSet countRs = countStmt.executeQuery(
                    "SELECT COUNT(*) AS CNT FROM " + lib + "." + table);
                if (countRs.next()) {
                    count = countRs.getLong("CNT");
                }
                countRs.close();
                countStmt.close();
            } catch (Exception e) {
                count = -1; // Error
            }
            
            if (count > 0 || count == -1) {
                System.out.println("    " + padRight(table, 20) + 
                    (count >= 0 ? count + " registros" : "ERROR"));
                totalRecords += Math.max(0, count);
            }
        }
        System.out.println("    -----------------------------------");
        System.out.println("    TOTAL " + lib + ": " + totalRecords + " registros");
    }

    static void exploreKeyTables(Connection conn, String lib) throws Exception {
        System.out.println("\n  --- ESTRUCTURA DE TABLAS CLAVE ---");
        
        String[] keyTables = {"CLIENF", "CONTRF", "VEHICF", "HISPAF", "VEKAF", "KARVEH", 
                              "CORCCF", "RECUCF", "RECUDF", "TALCOF", "AUTORF", "PERSEF"};
        
        for (String table : keyTables) {
            try {
                exploreTable(conn, lib, table);
            } catch (Exception e) {
                // tabla no existe en esta librería
            }
        }
    }

    static void exploreTable(Connection conn, String lib, String table) throws Exception {
        String sql = "SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH, " +
                     "NUMERIC_PRECISION, NUMERIC_SCALE, IS_NULLABLE, COLUMN_TEXT " +
                     "FROM QSYS2.SYSCOLUMNS " +
                     "WHERE TABLE_SCHEMA = '" + lib + "' " +
                     "AND TABLE_NAME = '" + table + "' " +
                     "ORDER BY ORDINAL_POSITION";
        
        Statement stmt = conn.createStatement();
        ResultSet rs;
        try {
            rs = stmt.executeQuery(sql);
        } catch (Exception e) {
            return;
        }
        
        List<String[]> cols = new ArrayList<>();
        while (rs.next()) {
            cols.add(new String[]{
                rs.getString("COLUMN_NAME"),
                rs.getString("DATA_TYPE"),
                rs.getString("CHARACTER_MAXIMUM_LENGTH"),
                rs.getString("NUMERIC_PRECISION"),
                rs.getString("NUMERIC_SCALE"),
                rs.getString("IS_NULLABLE"),
                rs.getString("COLUMN_TEXT")
            });
        }
        rs.close();
        
        if (!cols.isEmpty()) {
            System.out.println("\n    === " + lib + "." + table + " (" + cols.size() + " campos) ===");
            for (String[] c : cols) {
                String type = c[1];
                if ("CHARACTER".equals(type) || "VARCHAR".equals(type)) {
                    type += "(" + c[2] + ")";
                } else if ("DECIMAL".equals(type) || "NUMERIC".equals(type)) {
                    type += "(" + c[3] + "," + c[4] + ")";
                }
                System.out.println("      " + padRight(c[0], 20) + 
                    padRight(type, 22) + 
                    (c[6] != null ? c[6].trim() : ""));
            }
        }
    }

    static String padRight(String s, int n) {
        if (s == null) s = "";
        return String.format("%-" + n + "s", s);
    }
}
