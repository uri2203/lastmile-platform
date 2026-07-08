import com.sun.net.httpserver.HttpServer;
import com.sun.net.httpserver.HttpHandler;
import com.sun.net.httpserver.HttpExchange;
import java.net.InetSocketAddress;
import java.sql.*;
import java.util.*;
import java.io.*;

public class DashboardServer {
    
    private static final String DB_URL = "jdbc:as400://192.168.0.240;user=AYUDATX;password=MXTAC23;libraries=TESTLIB;prompt=false";
    private static Connection conn;
    private static String dashboardHTML;
    
    private static Connection getConn() throws Exception {
        if (conn == null || conn.isClosed()) {
            Class.forName("com.ibm.as400.access.AS400JDBCDriver");
            conn = DriverManager.getConnection(DB_URL);
            conn.setAutoCommit(true);
        }
        return conn;
    }
    
    public static void main(String[] args) throws Exception {
        dashboardHTML = new String(java.nio.file.Files.readAllBytes(
            java.nio.file.Paths.get("src/index.html")));
        
        getConn();
        System.out.println("✅ Conectado al AS/400 - 192.168.0.240");
        
        HttpServer server = HttpServer.create(new InetSocketAddress(8080), 0);
        server.createContext("/", new MainHandler());
        
        // CRUD Endpoints
        server.createContext("/api/clientes", new ClientesHandler());
        server.createContext("/api/productos", new ProductosHandler());
        server.createContext("/api/proveedores", new ProveedoresHandler());
        server.createContext("/api/facturas", new FacturasHandler());
        server.createContext("/api/entradas", new EntradasHandler());
        server.createContext("/api/salidas", new SalidasHandler());
        server.createContext("/api/devoluciones", new DevolucionesHandler());
        server.createContext("/api/pagos", new PagosHandler());
        server.createContext("/api/kpis", new KPIsHandler());
        
        server.setExecutor(null);
        server.start();
        
        System.out.println("========================================");
        System.out.println("  DASHBOARD AS/400 - DATOS REALES");
        System.out.println("  http://localhost:8080");
        System.out.println("========================================");
    }
    
    // ========== UTILIDADES ==========
    static String query(String sql) throws Exception {
        ResultSet rs = getConn().createStatement().executeQuery(sql);
        ResultSetMetaData m = rs.getMetaData();
        int c = m.getColumnCount();
        StringBuilder sb = new StringBuilder("[");
        boolean f = true;
        while (rs.next()) {
            if (!f) sb.append(",");
            sb.append("{");
            for (int i = 1; i <= c; i++) {
                if (i > 1) sb.append(",");
                sb.append("\"").append(m.getColumnLabel(i).toLowerCase()).append("\":");
                Object v = rs.getObject(i);
                if (v == null) sb.append("null");
                else if (v instanceof Number) sb.append(v);
                else sb.append("\"").append(String.valueOf(v).replace("\\","\\\\").replace("\"","\\\"")).append("\"");
            }
            sb.append("}");
            f = false;
        }
        rs.close();
        return sb.append("]").toString();
    }
    
    static double scalar(String sql) throws Exception {
        ResultSet rs = getConn().createStatement().executeQuery(sql);
        double v = rs.next() ? rs.getDouble(1) : 0;
        rs.close();
        return v;
    }
    
    static int executeUpdate(String sql) throws Exception {
        return getConn().createStatement().executeUpdate(sql);
    }
    
    static void send(HttpExchange ex, String body, int code, String type) {
        try {
            byte[] b = body.getBytes("UTF-8");
            ex.getResponseHeaders().set("Content-Type", type + "; charset=UTF-8");
            ex.getResponseHeaders().set("Access-Control-Allow-Origin", "*");
            ex.getResponseHeaders().set("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS");
            ex.getResponseHeaders().set("Access-Control-Allow-Headers", "Content-Type, Accept");
            ex.sendResponseHeaders(code, b.length);
            OutputStream os = ex.getResponseBody();
            os.write(b);
            os.close();
        } catch (Exception e) { e.printStackTrace(); }
    }
    
    static boolean handleCORS(HttpExchange ex) throws IOException {
        if (ex.getRequestMethod().equalsIgnoreCase("OPTIONS")) {
            ex.getResponseHeaders().set("Access-Control-Allow-Origin", "*");
            ex.getResponseHeaders().set("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS");
            ex.getResponseHeaders().set("Access-Control-Allow-Headers", "Content-Type, Accept");
            ex.sendResponseHeaders(204, -1);
            return true;
        }
        return false;
    }
    
    static String readBody(HttpExchange ex) throws Exception {
        BufferedReader br = new BufferedReader(new InputStreamReader(ex.getRequestBody(), "UTF-8"));
        StringBuilder sb = new StringBuilder();
        String line;
        while ((line = br.readLine()) != null) sb.append(line);
        return sb.toString();
    }
    
    static Map<String, String> parseJSON(String json) {
        Map<String, String> map = new HashMap<>();
        json = json.replace("{", "").replace("}", "").replace("\"", "");
        for (String pair : json.split(",")) {
            int idx = pair.indexOf(':');
            if (idx > 0) {
                String key = pair.substring(0, idx).trim();
                String val = pair.substring(idx + 1).trim();
                map.put(key, val);
            }
        }
        return map;
    }
    
    // ========== MAIN HANDLER ==========
    static class MainHandler implements HttpHandler {
        public void handle(HttpExchange ex) throws IOException {
            ex.getResponseHeaders().set("Cache-Control", "no-cache, no-store, must-revalidate");
            ex.getResponseHeaders().set("Pragma", "no-cache");
            ex.getResponseHeaders().set("Expires", "0");
            send(ex, dashboardHTML, 200, "text/html");
        }
    }
    
    // ========== KPIs ==========
    static class KPIsHandler implements HttpHandler {
        public void handle(HttpExchange ex) throws IOException {
            try {
                if (handleCORS(ex)) return;
                String r = "{" +
                    "\"ventasAnuales\":" + scalar("SELECT COALESCE(SUM(FACTOT),0) FROM TESTLIB.FAC001 WHERE YEAR(FACFEC)=2026") +
                    ",\"numFacturas\":" + (int)scalar("SELECT COUNT(*) FROM TESTLIB.FAC001 WHERE YEAR(FACFEC)=2026") +
                    ",\"totalProductos\":" + (int)scalar("SELECT COUNT(*) FROM TESTLIB.ART001") +
                    ",\"totalClientes\":" + (int)scalar("SELECT COUNT(*) FROM TESTLIB.CLI001") +
                    ",\"productosStockBajo\":" + (int)scalar("SELECT COUNT(*) FROM TESTLIB.ART001 WHERE ARTSTK<10") +
                    ",\"clientesMorosos\":" + (int)scalar("SELECT COUNT(DISTINCT CLICOD) FROM TESTLIB.FAC001 WHERE FACEST='P'") +
                    ",\"devoluciones\":" + scalar("SELECT COALESCE(SUM(DEVTOT),0) FROM TESTLIB.DEV001 WHERE YEAR(DEVFEC)=2026") +
                    "}";
                send(ex, r, 200, "application/json");
            } catch (Exception e) { send(ex, "{\"error\":\"" + e.getMessage() + "\"}", 500, "application/json"); }
        }
    }
    
    // ========== CLIENTES ==========
    static class ClientesHandler implements HttpHandler {
        public void handle(HttpExchange ex) throws IOException {
            try {
                if (handleCORS(ex)) return;
                String method = ex.getRequestMethod();
                
                if (method.equals("GET")) {
                    send(ex, query("SELECT CLICOD AS id, CLINOM AS nombre, CLIRFC AS rfc, CLICIUDAD AS ciudad, CLITEL AS telefono, CLIMAIL AS email, CLIACTIVO AS estado FROM TESTLIB.CLI001 ORDER BY CLICOD"), 200, "application/json");
                    
                } else if (method.equals("POST")) {
                    Map<String, String> d = parseJSON(readBody(ex));
                    executeUpdate("INSERT INTO TESTLIB.CLI001 (CLICOD, CLINOM, CLIRFC, CLIDIR, CLITEL, CLIMAIL, CLICIUDAD, CLIACTIVO, CLIFREG) VALUES (" +
                        d.get("id") + ",'" + d.get("nombre") + "','" + d.get("rfc") + "','','" + d.get("telefono") + "','" + d.get("email") + "','" + d.get("ciudad") + "','" + d.get("estado") + "',CURRENT_DATE)");
                    send(ex, "{\"ok\":true}", 200, "application/json");
                    
                } else if (method.equals("PUT")) {
                    Map<String, String> d = parseJSON(readBody(ex));
                    executeUpdate("UPDATE TESTLIB.CLI001 SET CLINOM='" + d.get("nombre") + "', CLIRFC='" + d.get("rfc") + "', CLITEL='" + d.get("telefono") + "', CLIMAIL='" + d.get("email") + "', CLICIUDAD='" + d.get("ciudad") + "', CLIACTIVO='" + d.get("estado") + "' WHERE CLICOD=" + d.get("id"));
                    send(ex, "{\"ok\":true}", 200, "application/json");
                    
                } else if (method.equals("DELETE")) {
                    String q = ex.getRequestURI().getQuery();
                    String id = q.split("=")[1].trim().replace("%22", "").replace("\"", "");
                    executeUpdate("DELETE FROM TESTLIB.CLI001 WHERE CLICOD=" + id);
                    send(ex, "{\"ok\":true}", 200, "application/json");
                }
            } catch (Exception e) { send(ex, "{\"error\":\"" + e.getMessage() + "\"}", 500, "application/json"); }
        }
    }
    
    // ========== PRODUCTOS ==========
    static class ProductosHandler implements HttpHandler {
        public void handle(HttpExchange ex) throws IOException {
            try {
                if (handleCORS(ex)) return;
                String method = ex.getRequestMethod();
                
                if (method.equals("GET")) {
                    send(ex, query("SELECT A.ARTCOD AS id, A.ARTNOM AS nombre, C.CATNOM AS categoria, A.ARTPRE AS precio, A.ARTSTK AS stock, A.ARTACTIVO AS estado FROM TESTLIB.ART001 A JOIN TESTLIB.CAT001 C ON A.CATCOD=C.CATCOD ORDER BY A.ARTCOD"), 200, "application/json");
                    
                } else if (method.equals("POST")) {
                    Map<String, String> d = parseJSON(readBody(ex));
                    executeUpdate("INSERT INTO TESTLIB.ART001 (ARTCOD, ARTNOM, ARTDSC, CATCOD, ARTPRE, ARTCOS, ARTSTK, ARTSTM, ARTUNI, ARTACTIVO) VALUES (" +
                        d.get("id") + ",'" + d.get("nombre") + "','','" + d.get("catcod") + "'," + d.get("precio") + "," + d.get("precio") + "," + d.get("stock") + ",10,'pza','" + d.get("estado") + "')");
                    send(ex, "{\"ok\":true}", 200, "application/json");
                    
                } else if (method.equals("PUT")) {
                    Map<String, String> d = parseJSON(readBody(ex));
                    executeUpdate("UPDATE TESTLIB.ART001 SET ARTNOM='" + d.get("nombre") + "', ARTPRE=" + d.get("precio") + ", ARTSTK=" + d.get("stock") + ", ARTACTIVO='" + d.get("estado") + "' WHERE ARTCOD=" + d.get("id"));
                    send(ex, "{\"ok\":true}", 200, "application/json");
                    
                } else if (method.equals("DELETE")) {
                    String q = ex.getRequestURI().getQuery();
                    String id = q.split("=")[1].trim().replace("%22", "").replace("\"", "");
                    executeUpdate("DELETE FROM TESTLIB.ART001 WHERE ARTCOD=" + id);
                    send(ex, "{\"ok\":true}", 200, "application/json");
                }
            } catch (Exception e) { send(ex, "{\"error\":\"" + e.getMessage() + "\"}", 500, "application/json"); }
        }
    }
    
    // ========== PROVEEDORES ==========
    static class ProveedoresHandler implements HttpHandler {
        public void handle(HttpExchange ex) throws IOException {
            try {
                if (handleCORS(ex)) return;
                String method = ex.getRequestMethod();
                
                if (method.equals("GET")) {
                    send(ex, query("SELECT PROCOD AS id, PRONOM AS nombre, PRORFC AS rfc, PROCIUDAD AS ciudad, PROTEL AS telefono, PROMAIL AS email, PROACTIVO AS estado FROM TESTLIB.PRO001 ORDER BY PROCOD"), 200, "application/json");
                    
                } else if (method.equals("POST")) {
                    Map<String, String> d = parseJSON(readBody(ex));
                    executeUpdate("INSERT INTO TESTLIB.PRO001 (PROCOD, PRONOM, PRORFC, PRODIR, PROTEL, PROMAIL, PROCIUDAD, PROACTIVO) VALUES (" +
                        d.get("id") + ",'" + d.get("nombre") + "','" + d.get("rfc") + "','','" + d.get("telefono") + "','" + d.get("email") + "','" + d.get("ciudad") + "','" + d.get("estado") + "')");
                    send(ex, "{\"ok\":true}", 200, "application/json");
                    
                } else if (method.equals("PUT")) {
                    Map<String, String> d = parseJSON(readBody(ex));
                    executeUpdate("UPDATE TESTLIB.PRO001 SET PRONOM='" + d.get("nombre") + "', PRORFC='" + d.get("rfc") + "', PROTEL='" + d.get("telefono") + "', PROMAIL='" + d.get("email") + "', PROCIUDAD='" + d.get("ciudad") + "', PROACTIVO='" + d.get("estado") + "' WHERE PROCOD=" + d.get("id"));
                    send(ex, "{\"ok\":true}", 200, "application/json");
                    
                } else if (method.equals("DELETE")) {
                    String q = ex.getRequestURI().getQuery();
                    String id = q.split("=")[1].trim().replace("%22", "").replace("\"", "");
                    executeUpdate("DELETE FROM TESTLIB.PRO001 WHERE PROCOD=" + id);
                    send(ex, "{\"ok\":true}", 200, "application/json");
                }
            } catch (Exception e) { send(ex, "{\"error\":\"" + e.getMessage() + "\"}", 500, "application/json"); }
        }
    }
    
    // ========== FACTURAS ==========
    static class FacturasHandler implements HttpHandler {
        public void handle(HttpExchange ex) throws IOException {
            try {
                if (handleCORS(ex)) return;
                String method = ex.getRequestMethod();
                
                if (method.equals("GET")) {
                    send(ex, query("SELECT F.FACNUM AS id, F.FACFEC AS fecha, C.CLINOM AS cliente, F.FACSUB AS subtotal, F.FACAIV AS iva, F.FACTOT AS total, F.FACEST AS estado FROM TESTLIB.FAC001 F JOIN TESTLIB.CLI001 C ON F.CLICOD=C.CLICOD ORDER BY F.FACFEC DESC"), 200, "application/json");
                    
                } else if (method.equals("POST")) {
                    Map<String, String> d = parseJSON(readBody(ex));
                    String num = "FAC" + String.format("%06d", (int)(scalar("SELECT COALESCE(MAX(CAST(SUBSTRING(FACNUM,4) AS INT)),0)+1 FROM TESTLIB.FAC001")));
                    executeUpdate("INSERT INTO TESTLIB.FAC001 (FACNUM, FACFEC, CLICOD, ALMCOD, FACSUB, FACAIV, FACTOT, FACEST, FACUSU) VALUES (" +
                        "'" + num + "','" + d.get("fecha") + "'," + d.get("clicode") + ",1," + d.get("subtotal") + "," + d.get("iva") + "," + d.get("total") + ",'" + d.get("estado") + "','WEB')");
                    send(ex, "{\"ok\":true,\"num\":\"" + num + "\"}", 200, "application/json");
                    
                } else if (method.equals("DELETE")) {
                    String q = ex.getRequestURI().getQuery();
                    String id = q.split("=")[1].replace("%22", "").replace("\"", "");
                    executeUpdate("DELETE FROM TESTLIB.FAD001 WHERE FACNUM='" + id + "'");
                    executeUpdate("DELETE FROM TESTLIB.FAC001 WHERE FACNUM='" + id + "'");
                    send(ex, "{\"ok\":true}", 200, "application/json");
                }
            } catch (Exception e) { send(ex, "{\"error\":\"" + e.getMessage() + "\"}", 500, "application/json"); }
        }
    }
    
    // ========== ENTRADAS ==========
    static class EntradasHandler implements HttpHandler {
        public void handle(HttpExchange ex) throws IOException {
            try {
                if (handleCORS(ex)) return;
                String method = ex.getRequestMethod();
                
                if (method.equals("GET")) {
                    send(ex, query("SELECT E.ENTNUM AS id, E.ENTFEC AS fecha, P.PRONOM AS proveedor, E.ALMCOD AS almacen, E.ENTTOT AS total, E.ENTEST AS estado FROM TESTLIB.ENT001 E JOIN TESTLIB.PRO001 P ON E.PROCOD=P.PROCOD ORDER BY E.ENTFEC DESC"), 200, "application/json");
                    
                } else if (method.equals("POST")) {
                    Map<String, String> d = parseJSON(readBody(ex));
                    String num = "ENT" + String.format("%06d", (int)(scalar("SELECT COALESCE(MAX(CAST(SUBSTRING(ENTNUM,4) AS INT)),0)+1 FROM TESTLIB.ENT001")));
                    executeUpdate("INSERT INTO TESTLIB.ENT001 (ENTNUM, ENTFEC, PROCOD, ALMCOD, ENTREF, ENTTOT, ENTEST) VALUES (" +
                        "'" + num + "','" + d.get("fecha") + "'," + d.get("procod") + "," + d.get("almcod") + ",'',0,'" + d.get("estado") + "')");
                    send(ex, "{\"ok\":true,\"num\":\"" + num + "\"}", 200, "application/json");
                    
                } else if (method.equals("DELETE")) {
                    String q = ex.getRequestURI().getQuery();
                    String id = q.split("=")[1].replace("%22", "").replace("\"", "");
                    executeUpdate("DELETE FROM TESTLIB.ETD001 WHERE ENTNUM='" + id + "'");
                    executeUpdate("DELETE FROM TESTLIB.ENT001 WHERE ENTNUM='" + id + "'");
                    send(ex, "{\"ok\":true}", 200, "application/json");
                }
            } catch (Exception e) { send(ex, "{\"error\":\"" + e.getMessage() + "\"}", 500, "application/json"); }
        }
    }
    
    // ========== SALIDAS ==========
    static class SalidasHandler implements HttpHandler {
        public void handle(HttpExchange ex) throws IOException {
            try {
                if (handleCORS(ex)) return;
                String method = ex.getRequestMethod();
                
                if (method.equals("GET")) {
                    send(ex, query("SELECT S.SALNUM AS id, S.SALFEC AS fecha, COALESCE(S.SALMOT,'') AS tipo, S.ALMCOD AS almacen, COALESCE((SELECT SUM(SL.SLDTOT) FROM TESTLIB.SLD001 SL WHERE SL.SALNUM=S.SALNUM),0) AS total, S.SALEST AS estado FROM TESTLIB.SAL001 S ORDER BY S.SALFEC DESC"), 200, "application/json");
                    
                } else if (method.equals("POST")) {
                    Map<String, String> d = parseJSON(readBody(ex));
                    String num = "SAL" + String.format("%06d", (int)(scalar("SELECT COALESCE(MAX(CAST(SUBSTRING(SALNUM,4) AS INT)),0)+1 FROM TESTLIB.SAL001")));
                    executeUpdate("INSERT INTO TESTLIB.SAL001 (SALNUM, SALFEC, ALMCOD, SALREF, SALMOT, SALEST) VALUES (" +
                        "'" + num + "','" + d.get("fecha") + "'," + d.get("almcod") + ",'','" + d.get("tipo") + "','" + d.get("estado") + "')");
                    send(ex, "{\"ok\":true,\"num\":\"" + num + "\"}", 200, "application/json");
                    
                } else if (method.equals("DELETE")) {
                    String q = ex.getRequestURI().getQuery();
                    String id = q.split("=")[1].replace("%22", "").replace("\"", "");
                    executeUpdate("DELETE FROM TESTLIB.SLD001 WHERE SALNUM='" + id + "'");
                    executeUpdate("DELETE FROM TESTLIB.SAL001 WHERE SALNUM='" + id + "'");
                    send(ex, "{\"ok\":true}", 200, "application/json");
                }
            } catch (Exception e) { send(ex, "{\"error\":\"" + e.getMessage() + "\"}", 500, "application/json"); }
        }
    }
    
    // ========== DEVOLUCIONES ==========
    static class DevolucionesHandler implements HttpHandler {
        public void handle(HttpExchange ex) throws IOException {
            try {
                if (handleCORS(ex)) return;
                String method = ex.getRequestMethod();
                
                if (method.equals("GET")) {
                    send(ex, query("SELECT D.DEVNUM AS id, D.DEVFEC AS fecha, D.FACNUM AS factura, C.CLINOM AS cliente, D.DEVMOT AS motivo, D.DEVTOT AS total FROM TESTLIB.DEV001 D JOIN TESTLIB.CLI001 C ON D.CLICOD=C.CLICOD ORDER BY D.DEVFEC DESC"), 200, "application/json");
                    
                } else if (method.equals("POST")) {
                    Map<String, String> d = parseJSON(readBody(ex));
                    String num = "DEV" + String.format("%06d", (int)(scalar("SELECT COALESCE(MAX(CAST(SUBSTRING(DEVNUM,4) AS INT)),0)+1 FROM TESTLIB.DEV001")));
                    executeUpdate("INSERT INTO TESTLIB.DEV001 (DEVNUM, DEVFEC, FACNUM, CLICOD, DEVTOT, DEVMOT, DEVEST) VALUES (" +
                        "'" + num + "','" + d.get("fecha") + "','" + d.get("factura") + "'," + d.get("clicode") + "," + d.get("total") + ",'" + d.get("motivo") + "','A')");
                    send(ex, "{\"ok\":true,\"num\":\"" + num + "\"}", 200, "application/json");
                    
                } else if (method.equals("DELETE")) {
                    String q = ex.getRequestURI().getQuery();
                    String id = q.split("=")[1].replace("%22", "").replace("\"", "");
                    executeUpdate("DELETE FROM TESTLIB.DVD001 WHERE DEVNUM='" + id + "'");
                    executeUpdate("DELETE FROM TESTLIB.DEV001 WHERE DEVNUM='" + id + "'");
                    send(ex, "{\"ok\":true}", 200, "application/json");
                }
            } catch (Exception e) { send(ex, "{\"error\":\"" + e.getMessage() + "\"}", 500, "application/json"); }
        }
    }
    
    // ========== PAGOS ==========
    static class PagosHandler implements HttpHandler {
        public void handle(HttpExchange ex) throws IOException {
            try {
                if (handleCORS(ex)) return;
                String method = ex.getRequestMethod();
                
                if (method.equals("GET")) {
                    send(ex, query("SELECT P.PAGNUM AS id, P.PAGFEC AS fecha, P.FACNUM AS factura, C.CLINOM AS cliente, P.PAGMET AS metodo, P.PAGIMP AS monto FROM TESTLIB.PAG001 P JOIN TESTLIB.CLI001 C ON P.CLICOD=C.CLICOD ORDER BY P.PAGFEC DESC"), 200, "application/json");
                    
                } else if (method.equals("POST")) {
                    Map<String, String> d = parseJSON(readBody(ex));
                    String num = "PAG" + String.format("%06d", (int)(scalar("SELECT COALESCE(MAX(CAST(SUBSTRING(PAGNUM,4) AS INT)),0)+1 FROM TESTLIB.PAG001")));
                    executeUpdate("INSERT INTO TESTLIB.PAG001 (PAGNUM, PAGFEC, FACNUM, CLICOD, PAGIMP, PAGMET, PAGREF, PAGEST) VALUES (" +
                        "'" + num + "','" + d.get("fecha") + "','" + d.get("factura") + "'," + d.get("clicode") + "," + d.get("monto") + ",'" + d.get("metodo") + "','','A')");
                    send(ex, "{\"ok\":true,\"num\":\"" + num + "\"}", 200, "application/json");
                    
                } else if (method.equals("DELETE")) {
                    String q = ex.getRequestURI().getQuery();
                    String id = q.split("=")[1].replace("%22", "").replace("\"", "");
                    executeUpdate("DELETE FROM TESTLIB.PAG001 WHERE PAGNUM='" + id + "'");
                    send(ex, "{\"ok\":true}", 200, "application/json");
                }
            } catch (Exception e) { send(ex, "{\"error\":\"" + e.getMessage() + "\"}", 500, "application/json"); }
        }
    }
}
