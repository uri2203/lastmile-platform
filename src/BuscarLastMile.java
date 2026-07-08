import java.sql.*;

public class BuscarLastMile {
    public static void main(String[] args) throws Exception {
        Connection conn = DriverManager.getConnection(
            "jdbc:as400://192.168.0.240;libraries=EDGAR;errors=full", "AYUDATX", "MXTAC23");
        System.out.println("=== BUSCANDO PATRON LAST MILE ===\n");

        // 1. Ver campo OTUNLM en OTSXMARCA
        System.out.println("--- 1. MUESTRA OTUNLM (Unidades Last Mile) ---");
        Statement s = conn.createStatement();
        ResultSet rs = s.executeQuery("SELECT OTUNLM, COUNT(*) AS CANT FROM EDGAR.OTSXMARCA GROUP BY OTUNLM ORDER BY CANT DESC FETCH FIRST 20 ROWS ONLY");
        while (rs.next()) System.out.println("  " + rs.getString("OTUNLM").trim() + " | OTs: " + rs.getInt("CANT"));
        rs.close();

        // 2. Ver patron de prefijos
        System.out.println("\n--- 2. PREFIJOS DE UNIDADES ---");
        rs = s.executeQuery("SELECT SUBSTR(OTUNLM,1,1) AS PREFIJO, COUNT(*) AS CANT FROM EDGAR.OTSXMARCA GROUP BY SUBSTR(OTUNLM,1,1) ORDER BY CANT DESC");
        while (rs.next()) System.out.println("  Prefijo '" + rs.getString("PREFIJO") + "' | OTs: " + rs.getInt("CANT"));
        rs.close();

        // 3. Unidades con "LM" en OTREPA (Last Mile?)
        System.out.println("\n--- 3. OTREPA (Reparacion a cargo) ---");
        rs = s.executeQuery("SELECT OTREPA, COUNT(*) AS CANT FROM EDGAR.REFACTALLE GROUP BY OTREPA ORDER BY CANT DESC");
        while (rs.next()) System.out.println("  " + rs.getString("OTREPA").trim() + " | Parts: " + rs.getInt("CANT"));
        rs.close();

        // 4. Buscar en OTSXMARCA2 que tiene CCTOTA01
        System.out.println("\n--- 4. OTSXMARCA2 - OTUNLM con costos ---");
        rs = s.executeQuery("SELECT OTUNLM, COUNT(*) AS OTS, SUM(CCTOTA01) AS TOTAL FROM EDGAR.OTSXMARCA2 GROUP BY OTUNLM ORDER BY TOTAL DESC FETCH FIRST 15 ROWS ONLY");
        while (rs.next()) System.out.println("  " + rs.getString("OTUNLM").trim() + " | OTs: " + rs.getInt("OTS") + " | $" + rs.getBigDecimal("TOTAL"));
        rs.close();

        // 5. Unidades en UNIDADESTA con prefijo W (posible Last Mile)
        System.out.println("\n--- 5. UNIDADESTA - Unidades W (posible LM) ---");
        rs = s.executeQuery("SELECT RVNEUN, RVMARC, RVMODL, RVESTA FROM EDGAR.UNIDADESTA WHERE RVNEUN LIKE 'W%' FETCH FIRST 15 ROWS ONLY");
        while (rs.next()) System.out.println("  " + rs.getString("RVNEUN").trim() + " | " + rs.getString("RVMARC").trim() + " | " + rs.getString("RVMODL").trim() + " | " + rs.getString("RVESTA"));
        rs.close();

        // 6. Unidades en UNIDADESTA con prefijo T (Taxis?)
        System.out.println("\n--- 6. UNIDADESTA - Unidades T (Taxis?) ---");
        rs = s.executeQuery("SELECT RVNEUN, RVMARC, RVMODL, RVESTA FROM EDGAR.UNIDADESTA WHERE RVNEUN LIKE 'T%' FETCH FIRST 10 ROWS ONLY");
        while (rs.next()) System.out.println("  " + rs.getString("RVNEUN").trim() + " | " + rs.getString("RVMARC").trim() + " | " + rs.getString("RVMODL").trim() + " | " + rs.getString("RVESTA"));
        rs.close();

        // 7. Verificar si hay tabla de clasificacion de unidades
        System.out.println("\n--- 7. BUSCAR TABLA CLASIFICACION ---");
        rs = s.executeQuery("SELECT TABLE_NAME, TABLE_TEXT FROM QSYS2.SYSTABLES WHERE TABLE_SCHEMA = 'EDGAR' AND (UPPER(TABLE_NAME) LIKE '%LAST%' OR UPPER(TABLE_NAME) LIKE '%LM%' OR UPPER(TABLE_NAME) LIKE '%MILE%' OR UPPER(TABLE_NAME) LIKE '%CLASIF%' OR UPPER(TABLE_NAME) LIKE '%TIPO%') ORDER BY TABLE_NAME");
        while (rs.next()) System.out.println("  " + rs.getString("TABLE_NAME") + " - " + rs.getString("TABLE_TEXT"));
        rs.close();

        // 8. Buscar en catalogo de servicios si hay clasificacion
        System.out.println("\n--- 8. TARIFAS (Clasificacion servicios) ---");
        rs = s.executeQuery("SELECT MSCVSE, MSDESS, MSTIPS FROM EDGAR.TARIFAS ORDER BY MSCVSE");
        while (rs.next()) System.out.println("  " + rs.getInt("MSCVSE") + " | " + rs.getString("MSDESS").trim() + " | Tipo: " + rs.getInt("MSTIPS"));
        rs.close();

        // 9. Ver RELACION entre OTSXMARCA y REFACTALLE por OTUNLM
        System.out.println("\n--- 9. GASTOS TOTALES POR OTUNLM (via REFACTALLE) ---");
        rs = s.executeQuery("SELECT R.OTUNLM, COUNT(*) AS PARTES, SUM(R.RETOTAL) AS TOTAL FROM EDGAR.REFACTALLE R GROUP BY R.OTUNLM ORDER BY TOTAL DESC FETCH FIRST 20 ROWS ONLY");
        while (rs.next()) System.out.println("  " + rs.getString("OTUNLM").trim() + " | Parts: " + rs.getInt("PARTES") + " | $" + rs.getBigDecimal("TOTAL"));
        rs.close();

        // 10. Diferentes prefijos de unidades
        System.out.println("\n--- 10. PREFIJOS UNIDADESTA ---");
        rs = s.executeQuery("SELECT SUBSTR(RVNEUN,1,1) AS PREF, COUNT(*) AS CANT FROM EDGAR.UNIDADESTA GROUP BY SUBSTR(RVNEUN,1,1) ORDER BY CANT DESC");
        while (rs.next()) System.out.println("  '" + rs.getString("PREF") + "' | Unidades: " + rs.getInt("CANT"));
        rs.close();

        conn.close();
        System.out.println("\n[OK] Listo");
    }
}
