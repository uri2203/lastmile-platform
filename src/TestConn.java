import java.sql.*;

public class TestConn {
    public static void main(String[] args) throws Exception {
        System.out.println("Conectando a AS/400...");
        Connection c = DriverManager.getConnection("jdbc:as400://192.168.0.240;errors=full", "AYUDATX", "MXTAC23");
        System.out.println("OK - Conectado: " + c.getMetaData().getDatabaseProductVersion());

        Statement s = c.createStatement();

        System.out.println("\n=== LIBRERIAS PRODUCTIVAS ===");
        ResultSet rs = s.executeQuery(
            "SELECT TABLE_SCHEMA, COUNT(*) AS TABLAS FROM QSYS2.SYSTABLES " +
            "WHERE TABLE_SCHEMA IN ('TACDB','TPDB','EDGAR','TESTLIB','SITDB','SLMDB') " +
            "GROUP BY TABLE_SCHEMA ORDER BY TABLAS DESC");
        while(rs.next()) System.out.println("  " + rs.getString(1).trim() + " - " + rs.getInt(2) + " tablas");
        rs.close();

        System.out.println("\n=== TABLAS TESTLIB ===");
        rs = s.executeQuery("SELECT TABLE_NAME FROM QSYS2.SYSTABLES WHERE TABLE_SCHEMA = 'TESTLIB' ORDER BY TABLE_NAME");
        while(rs.next()) System.out.println("  " + rs.getString(1).trim());
        rs.close();

        System.out.println("\n=== FECHA/HORA SERVIDOR ===");
        rs = s.executeQuery("SELECT CURRENT_TIMESTAMP FROM SYSIBM.SYSDUMMY1");
        if(rs.next()) System.out.println("  " + rs.getTimestamp(1));
        rs.close();

        c.close();
        System.out.println("\nDone.");
    }
}
