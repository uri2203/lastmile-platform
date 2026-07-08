import com.sun.net.httpserver.HttpServer;
import com.sun.net.httpserver.HttpHandler;
import com.sun.net.httpserver.HttpExchange;
import java.net.InetSocketAddress;
import java.io.*;

public class DashboardDemo {
    
    private static String dashboardHTML;
    
    public static void main(String[] args) throws Exception {
        dashboardHTML = new String(java.nio.file.Files.readAllBytes(
            java.nio.file.Paths.get("src/index.html")));
        
        HttpServer server = HttpServer.create(new InetSocketAddress(8080), 0);
        server.createContext("/", new MainHandler());
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
        System.out.println("  DASHBOARD AS/400 - MODO DEMO");
        System.out.println("  http://localhost:8080");
        System.out.println("========================================");
        System.out.println("El AS/400 no esta disponible.");
        System.out.println("Mostrando datos simulados.");
    }
    
    static void send(HttpExchange ex, String body, int code, String type) {
        try {
            byte[] b = body.getBytes("UTF-8");
            ex.getResponseHeaders().set("Content-Type", type + "; charset=UTF-8");
            ex.getResponseHeaders().set("Access-Control-Allow-Origin", "*");
            ex.sendResponseHeaders(code, b.length);
            OutputStream os = ex.getResponseBody();
            os.write(b);
            os.close();
        } catch (Exception e) { e.printStackTrace(); }
    }
    
    static class MainHandler implements HttpHandler {
        public void handle(HttpExchange ex) throws IOException {
            send(ex, dashboardHTML, 200, "text/html");
        }
    }
    
    static class KPIsHandler implements HttpHandler {
        public void handle(HttpExchange ex) throws IOException {
            send(ex, "{\"ventasAnuales\":2850463.96,\"numFacturas\":420,\"productosStockBajo\":15,\"clientesMorosos\":8,\"devoluciones\":125430.50}", 200, "application/json");
        }
    }
    
    static class VentasHandler implements HttpHandler {
        public void handle(HttpExchange ex) throws IOException {
            send(ex, "[{\"MES\":1,\"FACTURAS\":35,\"VENTAS\":450000},{\"MES\":2,\"FACTURAS\":42,\"VENTAS\":520000},{\"MES\":3,\"FACTURAS\":38,\"VENTAS\":480000},{\"MES\":4,\"FACTURAS\":40,\"VENTAS\":510000},{\"MES\":5,\"FACTURAS\":45,\"VENTAS\":580000},{\"MES\":6,\"FACTURAS\":39,\"VENTAS\":495000},{\"MES\":7,\"FACTURAS\":43,\"VENTAS\":550000},{\"MES\":8,\"FACTURAS\":41,\"VENTAS\":530000},{\"MES\":9,\"FACTURAS\":37,\"VENTAS\":470000},{\"MES\":10,\"FACTURAS\":44,\"VENTAS\":565000},{\"MES\":11,\"FACTURAS\":46,\"VENTAS\":590000},{\"MES\":12,\"FACTURAS\":48,\"VENTAS\":620000}]", 200, "application/json");
        }
    }
    
    static class InventarioHandler implements HttpHandler {
        public void handle(HttpExchange ex) throws IOException {
            send(ex, "[{\"ARTCOD\":1,\"ARTNOM\":\"Laptop Dell\",\"ARTSTK\":25,\"ARTPRE\":15999,\"CATNOM\":\"Electrónica\",\"VALOR\":399975},{\"ARTCOD\":2,\"ARTNOM\":\"Teclado Mecánico\",\"ARTSTK\":150,\"ARTPRE\":1299,\"CATNOM\":\"Accesorios\",\"VALOR\":194850},{\"ARTCOD\":3,\"ARTNOM\":\"Monitor Samsung 27\",\"ARTSTK\":40,\"ARTPRE\":8499,\"CATNOM\":\"Electrónica\",\"VALOR\":339960},{\"ARTCOD\":4,\"ARTNOM\":\"Mouse Inalámbrico\",\"ARTSTK\":200,\"ARTPRE\":450,\"CATNOM\":\"Accesorios\",\"VALOR\":90000},{\"ARTCOD\":5,\"ARTNOM\":\"Impresora HP\",\"ARTSTK\":15,\"ARTPRE\":4500,\"CATNOM\":\"Oficina\",\"VALOR\":67500}]", 200, "application/json");
        }
    }
    
    static class ClientesHandler implements HttpHandler {
        public void handle(HttpExchange ex) throws IOException {
            send(ex, "[{\"CLICOD\":1,\"CLINOM\":\"Grupo Industrial MX\",\"CLICIUDAD\":\"Monterrey\",\"COMPRAS\":24,\"MONTO\":485000},{\"CLICOD\":2,\"CLINOM\":\"Distribuidora Norte\",\"CLICIUDAD\":\"Guadalajara\",\"COMPRAS\":18,\"MONTO\":320000},{\"CLICOD\":3,\"CLINOM\":\"Comercializadora Sur\",\"CLICIUDAD\":\"CDMX\",\"COMPRAS\":15,\"MONTO\":275000},{\"CLICOD\":4,\"CLINOM\":\"Soluciones Tecnológicas\",\"CLICIUDAD\":\"Querétaro\",\"COMPRAS\":12,\"MONTO\":198000},{\"CLICOD\":5,\"CLINOM\":\"Almacenes Generales\",\"CLICIUDAD\":\"Puebla\",\"COMPRAS\":10,\"MONTO\":156000}]", 200, "application/json");
        }
    }
    
    static class AlertasHandler implements HttpHandler {
        public void handle(HttpExchange ex) throws IOException {
            send(ex, "[{\"tipo\":\"STOCK_CRITICO\",\"producto\":\"Laptop Dell\",\"stock\":3,\"severidad\":\"ALTA\"},{\"tipo\":\"STOCK_CRITICO\",\"producto\":\"Monitor Samsung\",\"stock\":2,\"severidad\":\"ALTA\"},{\"tipo\":\"CLIENTE_MOROSO\",\"cliente\":\"Distribuidora Norte\",\"deuda\":25000,\"severidad\":\"MEDIA\"}]", 200, "application/json");
        }
    }
    
    static class PrediccionesHandler implements HttpHandler {
        public void handle(HttpExchange ex) throws IOException {
            send(ex, "{\"predicciones\":[{\"mes\":\"Julio\",\"prediccion\":585000,\"confianza\":85},{\"mes\":\"Agosto\",\"prediccion\":610000,\"confianza\":75},{\"mes\":\"Septiembre\",\"prediccion\":635000,\"confianza\":65}]", 200, "application/json");
        }
    }
    
    static class DashboardHandler implements HttpHandler {
        public void handle(HttpExchange ex) throws IOException {
            send(ex, "{\"ventasAnuales\":2850463.96,\"totalProductos\":200,\"totalClientes\":50,\"status\":\"DEMO\",\"timestamp\":\"" + new java.util.Date() + "\"}", 200, "application/json");
        }
    }
}
