import java.sql.*;
import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.*;

public class GastosLM_Consolidado {
    public static void main(String[] args) throws Exception {
        Connection conn = DriverManager.getConnection(
            "jdbc:as400://192.168.0.240;libraries=EDGAR;errors=full", "AYUDATX", "MXTAC23");
        System.out.println("=== CONSOLIDADO GASTOS LAST MILE POR MARCA/MODELO ===\n");

        // Query principal: Marca + Modelo + Unidades + Total Gastos
        String sql = 
            "SELECT U.RVMARC AS MARCA, U.RVMODL AS MODELO, " +
            "COUNT(DISTINCT U.RVNEUN) AS UNIDADES, " +
            "COALESCE(OT.TOTAL_OT, 0) AS GASTOS_OT, " +
            "COALESCE(RF.TOTAL_REF, 0) AS GASTOS_REF, " +
            "COALESCE(OT.TOTAL_OT, 0) + COALESCE(RF.TOTAL_REF, 0) AS TOTAL_GASTOS " +
            "FROM EDGAR.UNIDADESTA U " +
            "LEFT JOIN (" +
            "  SELECT OTMARC, SUM(CCTOTA01) AS TOTAL_OT " +
            "  FROM EDGAR.OTSXMARCA2 WHERE OTUNLM LIKE 'W%' GROUP BY OTMARC" +
            ") OT ON U.RVMARC = OT.OTMARC " +
            "LEFT JOIN (" +
            "  SELECT O.OTMARC, SUM(R.RETOTA) AS TOTAL_REF " +
            "  FROM EDGAR.REFACTALLE R " +
            "  JOIN EDGAR.OTSXMARCA O ON R.OTNUOT = O.OTNUOT " +
            "  WHERE O.OTUNLM LIKE 'W%' GROUP BY O.OTMARC" +
            ") RF ON U.RVMARC = RF.OTMARC " +
            "WHERE U.RVNEUN LIKE 'W%' " +
            "GROUP BY U.RVMARC, U.RVMODL, OT.TOTAL_OT, RF.TOTAL_REF " +
            "ORDER BY TOTAL_GASTOS DESC";

        Statement s = conn.createStatement();
        ResultSet rs = s.executeQuery(sql);

        List<String[]> rows = new ArrayList<>();
        BigDecimal grandTotal = BigDecimal.ZERO;
        int grandUnid = 0;

        while (rs.next()) {
            String marca = rs.getString("MARCA") != null ? rs.getString("MARCA").trim() : "S/M";
            String modelo = rs.getString("MODELO") != null ? rs.getString("MODELO").trim() : "S/M";
            int unid = rs.getInt("UNIDADES");
            BigDecimal gOt = rs.getBigDecimal("GASTOS_OT"); if (gOt == null) gOt = BigDecimal.ZERO;
            BigDecimal gRef = rs.getBigDecimal("GASTOS_REF"); if (gRef == null) gRef = BigDecimal.ZERO;
            BigDecimal total = rs.getBigDecimal("TOTAL_GASTOS"); if (total == null) total = BigDecimal.ZERO;
            grandTotal = grandTotal.add(total);
            grandUnid += unid;
            rows.add(new String[]{marca, modelo, String.valueOf(unid),
                gOt.setScale(2, RoundingMode.HALF_UP).toString(),
                gRef.setScale(2, RoundingMode.HALF_UP).toString(),
                total.setScale(2, RoundingMode.HALF_UP).toString()});
            System.out.printf("  %-25s %-20s %3d  $%,14.2f  $%,14.2f  $%,14.2f%n",
                marca, modelo, unid, gOt, gRef, total);
        }
        rs.close();

        System.out.printf("%n  %-25s %-20s %3d  %15s  %15s  $%,14.2f%n",
            "TOTAL GENERAL", "", grandUnid, "", "", grandTotal);

        // Resumen por marca
        System.out.println("\n--- RESUMEN POR MARCA ---");
        String sqlMarca = 
            "SELECT U.RVMARC AS MARCA, " +
            "COUNT(DISTINCT U.RVNEUN) AS UNIDADES, " +
            "COALESCE(OT.TOTAL_OT, 0) + COALESCE(RF.TOTAL_REF, 0) AS TOTAL " +
            "FROM EDGAR.UNIDADESTA U " +
            "LEFT JOIN (" +
            "  SELECT OTMARC, SUM(CCTOTA01) AS TOTAL_OT " +
            "  FROM EDGAR.OTSXMARCA2 WHERE OTUNLM LIKE 'W%' GROUP BY OTMARC" +
            ") OT ON U.RVMARC = OT.OTMARC " +
            "LEFT JOIN (" +
            "  SELECT O.OTMARC, SUM(R.RETOTA) AS TOTAL_REF " +
            "  FROM EDGAR.REFACTALLE R " +
            "  JOIN EDGAR.OTSXMARCA O ON R.OTNUOT = O.OTNUOT " +
            "  WHERE O.OTUNLM LIKE 'W%' GROUP BY O.OTMARC" +
            ") RF ON U.RVMARC = RF.OTMARC " +
            "WHERE U.RVNEUN LIKE 'W%' " +
            "GROUP BY U.RVMARC, OT.TOTAL_OT, RF.TOTAL_REF " +
            "ORDER BY TOTAL DESC";
        rs = s.executeQuery(sqlMarca);
        List<String[]> marcas = new ArrayList<>();
        while (rs.next()) {
            String m = rs.getString("MARCA") != null ? rs.getString("MARCA").trim() : "?";
            int u = rs.getInt("UNIDADES");
            BigDecimal t = rs.getBigDecimal("TOTAL"); if (t == null) t = BigDecimal.ZERO;
            marcas.add(new String[]{m, String.valueOf(u), t.setScale(2, RoundingMode.HALF_UP).toString()});
            System.out.printf("  %-25s %3d unids  $%,14.2f%n", m, u, t);
        }
        rs.close();
        conn.close();

        // Generar PDF
        ReporteLMConsolidado.generar(rows, marcas, grandTotal, grandUnid);
        System.out.println("\nPDF: C:\\Users\\Sistemas\\as400\\Gastos_LastMile_Consolidado.pdf");
    }
}
