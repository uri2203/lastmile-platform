import java.sql.*;

public class TestConexion {
    public static void main(String[] args) throws Exception {
        System.out.println("Conectando a AS/400 192.168.0.240...");
        Connection conn = DriverManager.getConnection(
            "jdbc:as400://192.168.0.240;libraries=QSYS2;errors=full",
            "AYUDATX", "MXTAC23");
        System.out.println("[OK] CONECTADO - Usuario: AYUDATX");
        
        Statement stmt = conn.createStatement();
        ResultSet rs = stmt.executeQuery("SELECT CURRENT_TIMESTAMP AS AHORA FROM QSYS2.SYSCOLUMNS FETCH FIRST 1 ROW ONLY");
        if (rs.next()) {
            System.out.println("[OK] Hora servidor: " + rs.getString("AHORA"));
        }
        rs.close();
        
        rs = stmt.executeQuery("SELECT TABLE_SCHEMA, TABLE_NAME FROM QSYS2.SYSTABLES WHERE TABLE_SCHEMA = 'TACDB' FETCH FIRST 5 ROWS ONLY");
        System.out.println("\nPrimeras 5 tablas en TACDB:");
        while (rs.next()) {
            System.out.println("  " + rs.getString("TABLE_SCHEMA") + "." + rs.getString("TABLE_NAME"));
        }
        rs.close();
        stmt.close();
        conn.close();
        System.out.println("\n[OK] Conexion exitosa - todo funciona");
    }
}
