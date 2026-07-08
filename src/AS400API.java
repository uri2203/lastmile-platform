// AS400API.java - API REST para AS/400 (sin dependencias externas)
import com.sun.net.httpserver.HttpServer;
import com.sun.net.httpserver.HttpHandler;
import com.sun.net.httpserver.HttpExchange;
import java.net.InetSocketAddress;
import java.sql.*;
import java.util.*;
import java.io.*;

public class AS400API {
    
    private static Connection conn;
    
    public static void main(String[] args) throws Exception {
        conn = DriverManager.getConnection(
            "jdbc:as400://192.168.0.240;user=AYUDATX;password=MXTAC23;libraries=TESTLIB;prompt=false"
        );
        System.out.println("Conectado al AS/400");
        
        HttpServer server = HttpServer.create(new InetSocketAddress(8080), 0);
        server.createContext("/api/ventas", new VentasHandler());
        server.createContext("/api/inventario", new InventarioHandler());
        server.createContext("/api/clientes", new ClientesHandler());
        server.createContext("/api/kpis", new KPIsHandler());
        server.createContext("/api/alertas", new AlertasHandler());
        server.createContext("/api/predicciones", new PrediccionesHandler());
        server.createContext("/api/dashboard", new DashboardHandler());
        server.setExecutor(null);
        server.start();
        
        System.out.println("========================================");
        System.out.println("  API REST AS/400 - INICIADA");
        System.out.println("  Puerto: 8080");
        System.out.println("========================================");
        System.out.println("Endpoints:");
        System.out.println("  http://localhost:8080/api/kpis");
        System.out.println("  http://localhost:8080/api/ventas");
        System.out.println("  http://localhost:8080/api/inventario");
        System.out.println("  http://localhost:8080/api/clientes");
        System.out.println("  http://localhost:8080/api/alertas");
        System.out.println("  http://localhost:8080/api/predicciones");
        System.out.println("========================================");
    }
    
    static String q(String sql) throws Exception {
        ResultSet rs = conn.createStatement().executeQuery(sql);
        ResultSetMetaData m = rs.getMetaData();
        int c = m.getColumnCount();
        StringBuilder sb = new StringBuilder("[");
        boolean f = true;
        while (rs.next()) {
            if (!f) sb.append(",");
            sb.append("{");
            for (int i = 1; i <= c; i++) {
                if (i > 1) sb.append(",");
                sb.append("\"").append(m.getColumnName(i)).append("\":");
                Object v = rs.getObject(i);
                if (v == null) sb.append("null");
                else if (v instanceof Number) sb.append(v);
                else sb.append("\"").append(String.valueOf(v).replace("\"", "\\\"")).append("\"");
            }
            sb.append("}");
            f = false;
        }
        rs.close();
        return sb.append("]").toString();
    }
    
    static void send(HttpExchange ex, String r, int code) {
        try {
            byte[] b = r.getBytes("UTF-8");
            ex.getResponseHeaders().set("Content-Type", "application/json; charset=UTF-8");
            ex.getResponseHeaders().set("Access-Control-Allow-Origin", "*");
            ex.sendResponseHeaders(code, b.length);
            OutputStream os = ex.getResponseBody();
            os.write(b);
            os.close();
        } catch (Exception e) { e.printStackTrace(); }
    }
    
    static double scalar(String sql) throws Exception {
        ResultSet rs = conn.createStatement().executeQuery(sql);
        double v = rs.next() ? rs.getDouble(1) : 0;
        rs.close();
        return v;
    }
    
    static class VentasHandler implements HttpHandler {
        public void handle(HttpExchange ex) throws IOException {
            try {
                String q = ex.getRequestURI().getQuery();
                String per = "2026";
                if (q != null && q.contains("periodo=")) per = q.split("periodo=")[1].split("&")[0];
                send(ex, q("SELECT MONTH(FACFEC) MES, COUNT(*) FACTURAS, SUM(FACTOT) VENTAS FROM TESTLIB.FAC001 WHERE YEAR(FACFEC)=" + per + " GROUP BY MONTH(FACFEC) ORDER BY MES"), 200);
            } catch (Exception e) { send(ex, "{\"error\":\"" + e.getMessage() + "\"}", 500); }
        }
    }
    
    static class InventarioHandler implements HttpHandler {
        public void handle(HttpExchange ex) throws IOException {
            try {
                send(ex, q("SELECT A.ARTCOD, A.ARTNOM, A.ARTSTK, A.ARTPRE, C.CATNOM, (A.ARTSTK*A.ARTPRE) VALOR FROM TESTLIB.ART001 A JOIN TESTLIB.CAT001 C ON A.CATCOD=C.CATCOD ORDER BY VALOR DESC"), 200);
            } catch (Exception e) { send(ex, "{\"error\":\"" + e.getMessage() + "\"}", 500); }
        }
    }
    
    static class ClientesHandler implements HttpHandler {
        public void handle(HttpExchange ex) throws IOException {
            try {
                String q = ex.getRequestURI().getQuery();
                String top = "10";
                if (q != null && q.contains("top=")) top = q.split("top=")[1].split("&")[0];
                send(ex, q("SELECT C.CLICOD, C.CLINOM, C.CLICIUDAD, COUNT(F.FACNUM) COMPRAS, SUM(F.FACTOT) MONTO FROM TESTLIB.CLI001 C JOIN TESTLIB.FAC001 F ON C.CLICOD=F.CLICOD GROUP BY C.CLICOD, C.CLINOM, C.CLICIUDAD ORDER BY MONTO DESC FETCH FIRST " + top + " ROWS ONLY"), 200);
            } catch (Exception e) { send(ex, "{\"error\":\"" + e.getMessage() + "\"}", 500); }
        }
    }
    
    static class KPIsHandler implements HttpHandler {
        public void handle(HttpExchange ex) throws IOException {
            try {
                String r = "{" +
                    "\"ventasAnuales\":" + scalar("SELECT COALESCE(SUM(FACTOT),0) FROM TESTLIB.FAC001 WHERE YEAR(FACFEC)=2026") +
                    ",\"numFacturas\":" + (int)scalar("SELECT COUNT(*) FROM TESTLIB.FAC001 WHERE YEAR(FACFEC)=2026") +
                    ",\"productosStockBajo\":" + (int)scalar("SELECT COUNT(*) FROM TESTLIB.ART001 WHERE ARTSTK<10") +
                    ",\"clientesMorosos\":" + (int)scalar("SELECT COUNT(DISTINCT CLICOD) FROM TESTLIB.FAC001 WHERE FACEST='P'") +
                    ",\"devoluciones\":" + scalar("SELECT COALESCE(SUM(DEVTOT),0) FROM TESTLIB.DEV001 WHERE YEAR(DEVFEC)=2026") +
                    "}";
                send(ex, r, 200);
            } catch (Exception e) { send(ex, "{\"error\":\"" + e.getMessage() + "\"}", 500); }
        }
    }
    
    static class AlertasHandler implements HttpHandler {
        public void handle(HttpExchange ex) throws IOException {
            try {
                StringBuilder a = new StringBuilder("[");
                boolean f = true;
                
                ResultSet rs = conn.createStatement().executeQuery("SELECT ARTNOM, ARTSTK FROM TESTLIB.ART001 WHERE ARTSTK<5");
                while (rs.next()) {
                    if (!f) a.append(",");
                    a.append("{\"tipo\":\"STOCK_CRITICO\",\"producto\":\"").append(rs.getString("ARTNOM").replace("\"","\\\""))
                     .append("\",\"stock\":").append(rs.getInt("ARTSTK")).append(",\"severidad\":\"ALTA\"}");
                    f = false;
                }
                rs.close();
                
                rs = conn.createStatement().executeQuery("SELECT C.CLINOM, SUM(F.FACTOT)-COALESCE(P.TOT,0) DEUDA FROM TESTLIB.CLI001 C JOIN TESTLIB.FAC001 F ON C.CLICOD=F.CLICOD LEFT JOIN (SELECT CLICOD, SUM(PAGIMP) TOT FROM TESTLIB.PAG001 GROUP BY CLICOD) P ON C.CLICOD=P.CLICOD GROUP BY C.CLINOM, P.TOT HAVING SUM(F.FACTOT)-COALESCE(P.TOT,0)>10000");
                while (rs.next()) {
                    if (!f) a.append(",");
                    a.append("{\"tipo\":\"CLIENTE_MOROSO\",\"cliente\":\"").append(rs.getString("CLINOM").replace("\"","\\\""))
                     .append("\",\"deuda\":").append(rs.getDouble("DEUDA")).append(",\"severidad\":\"MEDIA\"}");
                    f = false;
                }
                rs.close();
                
                a.append("]");
                send(ex, a.toString(), 200);
            } catch (Exception e) { send(ex, "{\"error\":\"" + e.getMessage() + "\"}", 500); }
        }
    }
    
    static class PrediccionesHandler implements HttpHandler {
        public void handle(HttpExchange ex) throws IOException {
            try {
                ResultSet rs = conn.createStatement().executeQuery("SELECT MONTH(FACFEC) MES, SUM(FACTOT) VENTAS FROM TESTLIB.FAC001 WHERE YEAR(FACFEC)=2026 GROUP BY MONTH(FACFEC) ORDER BY MES");
                List<double[]> d = new ArrayList<>();
                while (rs.next()) d.add(new double[]{rs.getInt("MES"), rs.getDouble("VENTAS")});
                rs.close();
                
                double sx=0,sy=0,sxy=0,sx2=0; int n=d.size();
                for (double[] p : d) { sx+=p[0]; sy+=p[1]; sxy+=p[0]*p[1]; sx2+=p[0]*p[0]; }
                double m=(n*sxy-sx*sy)/(n*sx2-sx*sx), b=(sy-m*sx)/n;
                
                String[] meses={"Enero","Febrero","Marzo","Abril","Mayo","Junio","Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"};
                StringBuilder p = new StringBuilder("{\"predicciones\":[");
                for (int i=1;i<=3;i++) {
                    if(i>1)p.append(",");
                    int me=n+i; double va=Math.round((m*me+b)*100.0)/100.0;
                    p.append("{\"mes\":\"").append(meses[me-1]).append("\",\"prediccion\":").append(va).append(",\"confianza\":").append(95-i*10).append("}");
                }
                p.append("]}");
                send(ex, p.toString(), 200);
            } catch (Exception e) { send(ex, "{\"error\":\"" + e.getMessage() + "\"}", 500); }
        }
    }
    
    static class DashboardHandler implements HttpHandler {
        public void handle(HttpExchange ex) throws IOException {
            try {
                String r = "{" +
                    "\"ventasAnuales\":" + scalar("SELECT COALESCE(SUM(FACTOT),0) FROM TESTLIB.FAC001 WHERE YEAR(FACFEC)=2026") +
                    ",\"totalProductos\":" + (int)scalar("SELECT COUNT(*) FROM TESTLIB.ART001") +
                    ",\"totalClientes\":" + (int)scalar("SELECT COUNT(*) FROM TESTLIB.CLI001") +
                    ",\"status\":\"ONLINE\",\"timestamp\":\"" + new java.util.Date() + "\"}";
                send(ex, r, 200);
            } catch (Exception e) { send(ex, "{\"error\":\"" + e.getMessage() + "\"}", 500); }
        }
    }
}
