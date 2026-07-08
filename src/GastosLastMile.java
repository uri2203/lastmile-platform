import java.sql.*;
import java.math.BigDecimal;
import java.util.*;
import java.math.RoundingMode;

/**
 * REPORTE GASTOS POR MODELO - SOLO LAST MILE (prefijo W)
 */
public class GastosLastMile {

    static final String URL = "jdbc:as400://192.168.0.240;libraries=EDGAR;errors=full";
    static final String USER = "AYUDATX";
    static final String PASS = "MXTAC23";

    static List<String[]> dataOt = new ArrayList<>();
    static List<String[]> dataRef = new ArrayList<>();
    static List<String[]> dataCaja = new ArrayList<>();
    static List<String[]> dataUnid = new ArrayList<>();
    static BigDecimal totOt = BigDecimal.ZERO;
    static BigDecimal totRef = BigDecimal.ZERO;
    static BigDecimal totCaja = BigDecimal.ZERO;

    public static void main(String[] args) throws Exception {
        System.out.println("Conectando a EDGAR - Filtro LAST MILE (W*)...\n");
        Connection conn = DriverManager.getConnection(URL, USER, PASS);

        // 1. OTs por modelo - Solo unidades W (Last Mile)
        System.out.println("--- 1. GASTOS OT POR MODELO (LAST MILE) ---");
        String sql1 = "SELECT OTMARC AS MODELO, COUNT(*) AS OTS, SUM(CCTOTA01) AS TOTAL " +
            "FROM EDGAR.OTSXMARCA2 WHERE OTUNLM LIKE 'W%' GROUP BY OTMARC ORDER BY TOTAL DESC";
        Statement s = conn.createStatement();
        ResultSet rs = s.executeQuery(sql1);
        while (rs.next()) {
            String m = rs.getString("MODELO") != null ? rs.getString("MODELO").trim() : "SIN MODELO";
            int ots = rs.getInt("OTS");
            BigDecimal t = rs.getBigDecimal("TOTAL"); if (t == null) t = BigDecimal.ZERO;
            totOt = totOt.add(t);
            dataOt.add(new String[]{m, String.valueOf(ots), t.toPlainString()});
            System.out.println("  " + m + " | OTs: " + ots + " | $" + t);
        }
        rs.close();
        System.out.println("  TOTAL OT: $" + totOt);

        // 2. Refacciones por modelo - via REFACTALLE + OTSXMARCA (filtro W)
        System.out.println("\n--- 2. REFACCIONES POR MODELO (LAST MILE) ---");
        String sql2 = "SELECT O.OTMARC AS MODELO, COUNT(*) AS PARTES, SUM(R.RETOTA) AS TOTAL " +
            "FROM EDGAR.REFACTALLE R " +
            "JOIN EDGAR.OTSXMARCA O ON R.OTNUOT = O.OTNUOT " +
            "WHERE O.OTUNLM LIKE 'W%' " +
            "GROUP BY O.OTMARC ORDER BY TOTAL DESC";
        rs = s.executeQuery(sql2);
        while (rs.next()) {
            String m = rs.getString("MODELO") != null ? rs.getString("MODELO").trim() : "SIN MODELO";
            int p = rs.getInt("PARTES");
            BigDecimal t = rs.getBigDecimal("TOTAL"); if (t == null) t = BigDecimal.ZERO;
            totRef = totRef.add(t);
            dataRef.add(new String[]{m, String.valueOf(p), t.toPlainString()});
            System.out.println("  " + m + " | Partes: " + p + " | $" + t);
        }
        rs.close();
        System.out.println("  TOTAL REF: $" + totRef);

        // 3. Caja chica - unidades W
        System.out.println("\n--- 3. CAJA CHICA (LAST MILE) ---");
        String sql3 = "SELECT CAJ_CLAVET AS UNIDAD, SUM(CAJ_EGRESO) AS EGRESOS, " +
            "SUM(CAJ_INGRES) AS INGRESOS, COUNT(*) AS MOVS " +
            "FROM EDGAR.GASTOSELEC WHERE CAJ_CLAVET LIKE 'W%' GROUP BY CAJ_CLAVET ORDER BY EGRESOS DESC";
        rs = s.executeQuery(sql3);
        while (rs.next()) {
            String u = rs.getString("UNIDAD") != null ? rs.getString("UNIDAD").trim() : "?";
            BigDecimal eg = rs.getBigDecimal("EGRESOS"); if (eg == null) eg = BigDecimal.ZERO;
            BigDecimal ig = rs.getBigDecimal("INGRESOS"); if (ig == null) ig = BigDecimal.ZERO;
            int mv = rs.getInt("MOVS");
            totCaja = totCaja.add(eg);
            dataCaja.add(new String[]{u, eg.toPlainString(), ig.toPlainString(), String.valueOf(mv)});
            System.out.println("  " + u + " | Egr: $" + eg + " | Ing: $" + ig);
        }
        rs.close();
        System.out.println("  TOTAL CAJA: $" + totCaja);

        // Si no hay caja chica para W, buscar por concepto que contenga E (estilo E02)
        if (dataCaja.isEmpty()) {
            System.out.println("\n  Buscando caja chica por concepto Last Mile...");
            String sql3b = "SELECT CAJ_CLAVET AS UNIDAD, SUM(CAJ_EGRESO) AS EGRESOS, " +
                "SUM(CAJ_INGRES) AS INGRESOS, COUNT(*) AS MOVS " +
                "FROM EDGAR.GASTOSELEC WHERE CAJ_CLAVET LIKE 'E%' GROUP BY CAJ_CLAVET ORDER BY EGRESOS DESC";
            rs = s.executeQuery(sql3b);
            while (rs.next()) {
                String u = rs.getString("UNIDAD") != null ? rs.getString("UNIDAD").trim() : "?";
                BigDecimal eg = rs.getBigDecimal("EGRESOS"); if (eg == null) eg = BigDecimal.ZERO;
                BigDecimal ig = rs.getBigDecimal("INGRESOS"); if (ig == null) ig = BigDecimal.ZERO;
                int mv = rs.getInt("MOVS");
                totCaja = totCaja.add(eg);
                dataCaja.add(new String[]{u, eg.toPlainString(), ig.toPlainString(), String.valueOf(mv)});
                System.out.println("  " + u + " | Egr: $" + eg);
            }
            rs.close();
        }

        // 4. Unidades Last Mile por modelo
        System.out.println("\n--- 4. UNIDADES LAST MILE POR MODELO ---");
        String sql4 = "SELECT RVMARC AS MARCA, RVMODL AS MODELO, COUNT(*) AS CANT " +
            "FROM EDGAR.UNIDADESTA WHERE RVNEUN LIKE 'W%' GROUP BY RVMARC, RVMODL ORDER BY CANT DESC";
        rs = s.executeQuery(sql4);
        while (rs.next()) {
            String mar = rs.getString("MARCA") != null ? rs.getString("MARCA").trim() : "?";
            String mod = rs.getString("MODELO") != null ? rs.getString("MODELO").trim() : "?";
            int c = rs.getInt("CANT");
            dataUnid.add(new String[]{mar, mod, String.valueOf(c)});
            System.out.println("  " + mar + " " + mod + " | " + c);
        }
        rs.close();

        // 5. Resumen por tipo de gasto en OTs Last Mile
        System.out.println("\n--- 5. TOP 10 UNIDADES LAST MILE (MAS GASTO OT) ---");
        String sql5 = "SELECT OTUNLM AS UNIDAD, COUNT(*) AS OTS, SUM(CCTOTA01) AS TOTAL " +
            "FROM EDGAR.OTSXMARCA2 WHERE OTUNLM LIKE 'W%' GROUP BY OTUNLM ORDER BY TOTAL DESC FETCH FIRST 10 ROWS ONLY";
        rs = s.executeQuery(sql5);
        while (rs.next()) System.out.println("  " + rs.getString("UNIDAD").trim() + " | OTs: " + rs.getInt("OTS") + " | $" + rs.getBigDecimal("TOTAL"));
        rs.close();

        conn.close();

        // Generar PDF
        System.out.println("\nGenerando PDF Last Mile...");
        String path = "C:\\Users\\Sistemas\\as400\\Gastos_LastMile_EDGAR.pdf";
        ReporteGastosPDF.generate(dataOt, dataRef, dataCaja, dataUnid, totOt, totRef, totCaja, path);
        System.out.println("PDF generado: " + path);
    }
}
