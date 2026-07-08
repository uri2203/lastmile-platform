import java.sql.*;
import java.util.*;

/**
 * EXPLORADOR DE SISTEMAS AS/400 PRODUCTIVOS - V7R1 compatible
 * Solo lectura - NO modifica nada
 */
public class ExplorarSistemas {

    static final String URL = "jdbc:as400://192.168.0.240;libraries=QSYS2;errors=full";
    static final String USER = "AYUDATX";
    static final String PASS = "MXTAC23";

    // Librerías de interés (los 2 sistemas productivos)
    static final String[] SYSTEM_LIBS = {
        "TACCOM", "TACDB", "TPCOM", "TPDB", "SITDB", "SLMDB", "ROMCOM", "ROMDB",
        "EDGAR", "SLMOBJ", "SLMSRC", "WRKDBF", "LIBRARY"
    };

    public static void main(String[] args) throws Exception {
        System.out.println("========================================");
        System.out.println(" EXPLORADOR AS/400 - SOLO LECTURA");
        System.out.println(" Conectando a 192.168.0.240...");
        System.out.println("========================================\n");

        Connection conn = DriverManager.getConnection(URL, USER, PASS);
        System.out.println("[OK] Conexion establecida\n");

        // 1. Listar tablas por librería de interés
        System.out.println("=== 1. TABLAS POR LIBRERIA ===\n");
        for (String lib : SYSTEM_LIBS) {
            exploreLibrary(conn, lib);
        }

        // 2. Programas
        System.out.println("\n=== 2. PROGRAMAS RPG/CL POR LIBRERIA ===\n");
        for (String lib : SYSTEM_LIBS) {
            explorePrograms(conn, lib);
        }

        conn.close();
        System.out.println("\n[OK] Conexion cerrada");
    }

    static void exploreLibrary(Connection conn, String lib) throws Exception {
        // Obtener tablas usando FILES del esquema
        String sql = "SELECT TABLE_NAME, TABLE_TEXT, LAST_ALTERED_TIMESTAMP " +
                     "FROM QSYS2.SYSTABLES " +
                     "WHERE TABLE_SCHEMA = '" + lib + "' " +
                     "AND TABLE_TYPE = 'T' " +
                     "ORDER BY TABLE_NAME";
        
        Statement stmt = conn.createStatement();
        ResultSet rs;
        try {
            rs = stmt.executeQuery(sql);
        } catch (Exception e) {
            // Si TABLE_TYPE no existe, intentar sin filtro
            sql = "SELECT TABLE_NAME, TABLE_TEXT, LAST_ALTERED_TIMESTAMP " +
                  "FROM QSYS2.SYSTABLES " +
                  "WHERE TABLE_SCHEMA = '" + lib + "' " +
                  "ORDER BY TABLE_NAME";
            rs = stmt.executeQuery(sql);
        }
        
        List<String[]> tables = new ArrayList<>();
        while (rs.next()) {
            tables.add(new String[]{
                rs.getString("TABLE_NAME"),
                rs.getString("TABLE_TEXT"),
                rs.getString("LAST_ALTERED_TIMESTAMP")
            });
        }
        rs.close();
        
        if (!tables.isEmpty()) {
            System.out.println("  --- " + lib + " (" + tables.size() + " tablas) ---");
            for (int i = 0; i < tables.size(); i++) {
                String[] t = tables.get(i);
                System.out.println("    [" + (i+1) + "] " + t[0] + 
                    (t[1] != null && !t[1].trim().isEmpty() ? " - " + t[1].trim() : "") +
                    (t[2] != null ? " [Mod: " + t[2].substring(0, Math.min(10, t[2].length())) + "]" : ""));
            }
            System.out.println();
        }
    }

    static void explorePrograms(Connection conn, String lib) throws Exception {
        String sql = "SELECT PROGRAM_NAME, PROGRAM_TYPE, PROGRAM_TEXT, LAST_USED_TIMESTAMP " +
                     "FROM QSYS2.PROGRAM_INFO " +
                     "WHERE PROGRAM_SCHEMA = '" + lib + "' " +
                     "ORDER BY PROGRAM_NAME";
        
        Statement stmt = conn.createStatement();
        ResultSet rs;
        try {
            rs = stmt.executeQuery(sql);
        } catch (Exception e) {
            return; // Si no tiene programas, skip
        }
        
        List<String[]> progs = new ArrayList<>();
        while (rs.next()) {
            String type = rs.getString("PROGRAM_TYPE");
            if (type != null && (type.contains("RPG") || type.contains("CL") || type.equals("PGM"))) {
                progs.add(new String[]{
                    rs.getString("PROGRAM_NAME"),
                    type,
                    rs.getString("PROGRAM_TEXT"),
                    rs.getString("LAST_USED_TIMESTAMP")
                });
            }
        }
        rs.close();
        
        if (!progs.isEmpty()) {
            System.out.println("  --- PROGRAMAS EN " + lib + " (" + progs.size() + ") ---");
            for (int i = 0; i < progs.size(); i++) {
                String[] p = progs.get(i);
                System.out.println("    [" + (i+1) + "] " + p[0] + " [" + p[1] + "]" +
                    (p[2] != null && !p[2].trim().isEmpty() ? " - " + p[2].trim() : "") +
                    (p[3] != null ? " [Usado: " + p[3].substring(0, Math.min(10, p[3].length())) + "]" : ""));
            }
            System.out.println();
        }
    }
}
