import java.sql.*;
import java.util.*;
import java.math.BigDecimal;

/**
 * REPORTE: GASTOS POR MODELO DE UNIDAD - EDGAR
 * Consulta directa al AS/400, genera PDF ejecutivo
 */
public class GastosPorModelo {

    static final String URL = "jdbc:as400://192.168.0.240;libraries=EDGAR;errors=full";
    static final String USER = "AYUDATX";
    static final String PASS = "MXTAC23";

    // Data containers
    static List<String[]> dataOtPorModelo = new ArrayList<>();
    static List<String[]> dataRefacciones = new ArrayList<>();
    static List<String[]> dataCajaChica = new ArrayList<>();
    static List<String[]> dataUnidades = new ArrayList<>();
    static BigDecimal totalGeneralOt = BigDecimal.ZERO;
    static BigDecimal totalGeneralRef = BigDecimal.ZERO;
    static BigDecimal totalGeneralCaja = BigDecimal.ZERO;

    public static void main(String[] args) throws Exception {
        System.out.println("Conectando a EDGAR...");
        Connection conn = DriverManager.getConnection(URL, USER, PASS);
        System.out.println("[OK] Conectado\n");

        // 1. Gastos por modelo (OTs + costos)
        System.out.println("--- 1. GASTOS POR MODELO (Ordenes de Trabajo) ---");
        queryOtPorModelo(conn);

        // 2. Gastos por refaccion
        System.out.println("\n--- 2. GASTOS POR REFACCION ---");
        queryRefacciones(conn);

        // 3. Gastos caja chica por unidad
        System.out.println("\n--- 3. GASTOS CAJA CHICA POR UNIDAD ---");
        queryCajaChica(conn);

        // 4. Unidades por modelo
        System.out.println("\n--- 4. UNIDADES POR MODELO ---");
        queryUnidades(conn);

        conn.close();

        // Generar PDF
        System.out.println("\nGenerando PDF...");
        String path = "C:\\Users\\Sistemas\\as400\\Gastos_por_Modelo_EDGAR.pdf";
        ReporteGastosPDF.generate(dataOtPorModelo, dataRefacciones, dataCajaChica, dataUnidades,
            totalGeneralOt, totalGeneralRef, totalGeneralCaja, path);
        System.out.println("PDF generado: " + path);
    }

    static void queryOtPorModelo(Connection conn) throws Exception {
        String sql = "SELECT OTMARC AS MODELO, COUNT(*) AS OTS, " +
            "SUM(CCTOTA01) AS TOTAL_COSTO " +
            "FROM EDGAR.OTSXMARCA2 " +
            "GROUP BY OTMARC ORDER BY TOTAL_COSTO DESC";
        Statement stmt = conn.createStatement();
        ResultSet rs = stmt.executeQuery(sql);
        totalGeneralOt = BigDecimal.ZERO;
        while (rs.next()) {
            String modelo = rs.getString("MODELO") != null ? rs.getString("MODELO").trim() : "SIN MODELO";
            int ots = rs.getInt("OTS");
            BigDecimal total = rs.getBigDecimal("TOTAL_COSTO");
            if (total == null) total = BigDecimal.ZERO;
            totalGeneralOt = totalGeneralOt.add(total);
            dataOtPorModelo.add(new String[]{modelo, String.valueOf(ots), total.toPlainString()});
            System.out.println("  " + modelo + " | OTs: " + ots + " | $" + total);
        }
        rs.close();
        System.out.println("  TOTAL: $" + totalGeneralOt);
    }

    static void queryRefacciones(Connection conn) throws Exception {
        String sql = "SELECT OTMARC AS MODELO, COUNT(*) AS PARTES, " +
            "SUM(RETOTA) AS TOTAL_REFACCION " +
            "FROM EDGAR.REFACTALLE R " +
            "JOIN EDGAR.OTSXMARCA O ON R.OTNUOT = O.OTNUOT " +
            "GROUP BY OTMARC ORDER BY TOTAL_REFACCION DESC";
        Statement stmt = conn.createStatement();
        ResultSet rs = stmt.executeQuery(sql);
        totalGeneralRef = BigDecimal.ZERO;
        while (rs.next()) {
            String modelo = rs.getString("MODELO") != null ? rs.getString("MODELO").trim() : "SIN MODELO";
            int partes = rs.getInt("PARTES");
            BigDecimal total = rs.getBigDecimal("TOTAL_REFACCION");
            if (total == null) total = BigDecimal.ZERO;
            totalGeneralRef = totalGeneralRef.add(total);
            dataRefacciones.add(new String[]{modelo, String.valueOf(partes), total.toPlainString()});
            System.out.println("  " + modelo + " | Partes: " + partes + " | $" + total);
        }
        rs.close();
        System.out.println("  TOTAL: $" + totalGeneralRef);
    }

    static void queryCajaChica(Connection conn) throws Exception {
        String sql = "SELECT CAJ_CLAVET AS UNIDAD, " +
            "SUM(CAJ_EGRESO) AS TOTAL_EGRESOS, " +
            "SUM(CAJ_INGRES) AS TOTAL_INGRESOS, " +
            "COUNT(*) AS MOVIMIENTOS " +
            "FROM EDGAR.GASTOSELEC " +
            "GROUP BY CAJ_CLAVET ORDER BY TOTAL_EGRESOS DESC";
        Statement stmt = conn.createStatement();
        ResultSet rs = stmt.executeQuery(sql);
        totalGeneralCaja = BigDecimal.ZERO;
        while (rs.next()) {
            String unidad = rs.getString("UNIDAD") != null ? rs.getString("UNIDAD").trim() : "SIN UNIDAD";
            BigDecimal egresos = rs.getBigDecimal("TOTAL_EGRESOS");
            BigDecimal ingresos = rs.getBigDecimal("TOTAL_INGRESOS");
            int movs = rs.getInt("MOVIMIENTOS");
            if (egresos == null) egresos = BigDecimal.ZERO;
            if (ingresos == null) ingresos = BigDecimal.ZERO;
            totalGeneralCaja = totalGeneralCaja.add(egresos);
            dataCajaChica.add(new String[]{unidad, egresos.toPlainString(), ingresos.toPlainString(), String.valueOf(movs)});
            System.out.println("  " + unidad + " | Egresos: $" + egresos + " | Ingresos: $" + ingresos);
        }
        rs.close();
        System.out.println("  TOTAL EGRESOS: $" + totalGeneralCaja);
    }

    static void queryUnidades(Connection conn) throws Exception {
        String sql = "SELECT RVMARC AS MARCA, RVMODL AS MODELO, " +
            "COUNT(*) AS CANTIDAD " +
            "FROM EDGAR.UNIDADESTA " +
            "GROUP BY RVMARC, RVMODL ORDER BY CANTIDAD DESC";
        Statement stmt = conn.createStatement();
        ResultSet rs = stmt.executeQuery(sql);
        while (rs.next()) {
            String marca = rs.getString("MARCA") != null ? rs.getString("MARCA").trim() : "S/M";
            String modelo = rs.getString("MODELO") != null ? rs.getString("MODELO").trim() : "S/M";
            int cant = rs.getInt("CANTIDAD");
            dataUnidades.add(new String[]{marca, modelo, String.valueOf(cant)});
            System.out.println("  " + marca + " " + modelo + " | Cantidad: " + cant);
        }
        rs.close();
    }
}
