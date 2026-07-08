package alertas;

import java.sql.*;
import java.util.*;
import javax.mail.*;
import javax.mail.internet.*;
import java.io.*;
import java.net.HttpURLConnection;
import java.net.URL;

public class SistemaAlertas {
    
    private static Connection conn;
    private static Properties config;
    
    public static void main(String[] args) throws Exception {
        config = new Properties();
        config.load(new FileInputStream("config/alertas.properties"));
        
        conn = DriverManager.getConnection(
            "jdbc:as400://192.168.0.240;user=AYUDATX;password=MXTAC23;libraries=TESTLIB;prompt=false"
        );
        
        System.out.println("=== SISTEMA DE ALERTAS INTELIGENTE ===");
        System.out.println("Monitoreando AS/400 cada 60 segundos...");
        
        while (true) {
            try {
                List<Alerta> alertas = new ArrayList<>();
                alertas.addAll(verificarStockCritico());
                alertas.addAll(verificarClientesMorosos());
                alertas.addAll(verificarDevolucionesAltas());
                alertas.addAll(verificarMetasVentas());
                
                if (!alertas.isEmpty()) {
                    enviarNotificaciones(alertas);
                }
                
                System.out.println("[" + new java.util.Date() + "] Monitoreo completado. Alertas: " + alertas.size());
            } catch (Exception e) {
                System.err.println("Error en monitoreo: " + e.getMessage());
            }
            
            Thread.sleep(60000);
        }
    }
    
    static List<Alerta> verificarStockCritico() throws Exception {
        List<Alerta> alertas = new ArrayList<>();
        ResultSet rs = conn.createStatement().executeQuery(
            "SELECT A.ARTCOD, A.ARTNOM, A.ARTSTK, A.ALMCOD, C.CATNOM " +
            "FROM TESTLIB.ART001 A JOIN TESTLIB.CAT001 C ON A.CATCOD = C.CATCOD " +
            "WHERE A.ARTSTK < 5 ORDER BY A.ARTSTK"
        );
        
        while (rs.next()) {
            Alerta a = new Alerta();
            a.tipo = "STOCK_CRITICO";
            a.severidad = rs.getInt("ARTSTK") == 0 ? "CRITICA" : "ALTA";
            a.mensaje = String.format("Stock crítico: %s (Código: %s) en almacén %s. Stock actual: %d unidades",
                rs.getString("ARTNOM"), rs.getString("ARTCOD"), rs.getString("ALMCOD"), rs.getInt("ARTSTK"));
            a.destinatario = config.getProperty("email.admin");
            alertas.add(a);
        }
        rs.close();
        return alertas;
    }
    
    static List<Alerta> verificarClientesMorosos() throws Exception {
        List<Alerta> alertas = new ArrayList<>();
        ResultSet rs = conn.createStatement().executeQuery(
            "SELECT C.CLICOD, C.CLINOM, C.CLISAL, C.CLITEF " +
            "FROM TESTLIB.CLI001 C WHERE C.CLISAL > 5000 ORDER BY C.CLISAL DESC"
        );
        
        while (rs.next()) {
            Alerta a = new Alerta();
            a.tipo = "CLIENTE_MOROSO";
            a.severidad = rs.getDouble("CLISAL") > 20000 ? "CRITICA" : "ALTA";
            a.mensaje = String.format("Cliente moroso: %s debe $%,.2f. Teléfono: %s",
                rs.getString("CLINOM"), rs.getDouble("CLISAL"), rs.getString("CLITEF"));
            a.destinatario = config.getProperty("email.cobranza");
            alertas.add(a);
        }
        rs.close();
        return alertas;
    }
    
    static List<Alerta> verificarDevolucionesAltas() throws Exception {
        List<Alerta> alertas = new ArrayList<>();
        ResultSet rs = conn.createStatement().executeQuery(
            "SELECT D.DEVCOD, D.ARTCOD, D.DEVIMP, D.DEVMOT, C.CLINOM " +
            "FROM TESTLIB.DEV001 D JOIN TESTLIB.FAC001 F ON D.FACNUM = F.FACNUM " +
            "JOIN TESTLIB.CLI001 C ON F.CLICOD = C.CLICOD " +
            "WHERE D.DEVIMP > 10000 ORDER BY D.DEVIMP DESC"
        );
        
        while (rs.next()) {
            Alerta a = new Alerta();
            a.tipo = "DEVOLUCION_ALTA";
            a.severidad = rs.getDouble("DEVIMP") > 50000 ? "CRITICA" : "MEDIA";
            a.mensaje = String.format("Devolución significativa: %s por $%,.2f. Motivo: %s",
                rs.getString("CLINOM"), rs.getDouble("DEVIMP"), rs.getString("DEVMOT"));
            a.destinatario = config.getProperty("email.ventas");
            alertas.add(a);
        }
        rs.close();
        return alertas;
    }
    
    static List<Alerta> verificarMetasVentas() throws Exception {
        List<Alerta> alertas = new ArrayList<>();
        ResultSet rs = conn.createStatement().executeQuery(
            "SELECT SUM(F.FACTOT) AS VENTAS_ACTUALES " +
            "FROM TESTLIB.FAC001 F WHERE MONTH(F.FACFEC) = MONTH(CURRENT_DATE) AND YEAR(F.FACFEC) = YEAR(CURRENT_DATE)"
        );
        
        double ventasActuales = 0;
        if (rs.next()) ventasActuales = rs.getDouble("VENTAS_ACTUES");
        rs.close();
        
        double meta = Double.parseDouble(config.getProperty("meta.mensual", "500000"));
        double porcentaje = (ventasActuales / meta) * 100;
        
        if (porcentaje < 70) {
            Alerta a = new Alerta();
            a.tipo = "META_EN_RIESGO";
            a.severidad = "ALTA";
            a.mensaje = String.format("Meta mensual en riesgo: $%,.2f de $%,.2f (%.1f%%). Faltan $%,.2f",
                ventasActuales, meta, porcentaje, meta - ventasActuales);
            a.destinatario = config.getProperty("email.direccion");
            alertas.add(a);
        }
        
        return alertas;
    }
    
    static void enviarNotificaciones(List<Alerta> alertas) throws Exception {
        for (Alerta a : alertas) {
            enviarEmail(a);
            if (a.severidad.equals("CRITICA")) {
                enviarSMS(a);
            }
        }
    }
    
    static void enviarEmail(Alerta alerta) throws Exception {
        Properties props = new Properties();
        props.put("mail.smtp.host", config.getProperty("smtp.host", "smtp.gmail.com"));
        props.put("mail.smtp.port", config.getProperty("smtp.port", "587"));
        props.put("mail.smtp.auth", "true");
        props.put("mail.smtp.starttls.enable", "true");
        
        Session session = Session.getInstance(props, new Authenticator() {
            protected PasswordAuthentication getPasswordAuthentication() {
                return new PasswordAuthentication(
                    config.getProperty("smtp.usuario"),
                    config.getProperty("smtp.password")
                );
            }
        });
        
        Message msg = new MimeMessage(session);
        msg.setFrom(new InternetAddress(config.getProperty("smtp.from")));
        msg.setRecipients(Message.RecipientType.TO, InternetAddress.parse(alerta.destinatario));
        msg.setSubject("[AS/400] Alerta " + alerta.tipo + " - Severidad: " + alerta.severidad);
        
        String html = "<html><body style='font-family: Arial;'>" +
            "<h2 style='color: #d32f2f;'>⚠️ Alerta del Sistema AS/400</h2>" +
            "<div style='background: #f5f5f5; padding: 15px; border-radius: 8px;'>" +
            "<p><strong>Tipo:</strong> " + alerta.tipo + "</p>" +
            "<p><strong>Severidad:</strong> <span style='color: " + (alerta.severidad.equals("CRITICA") ? "red" : "orange") + ";'>" + alerta.severidad + "</span></p>" +
            "<p><strong>Mensaje:</strong> " + alerta.mensaje + "</p>" +
            "<p><strong>Fecha:</strong> " + new java.util.Date() + "</p>" +
            "</div>" +
            "<p style='color: #666; font-size: 12px;'>Sistema Integral AS/400 - V7R1</p>" +
            "</body></html>";
        
        msg.setContent(html, "text/html; charset=utf-8");
        Transport.send(msg);
    }
    
    static void enviarSMS(Alerta alerta) throws Exception {
        String apikey = config.getProperty("sms.apikey");
        String from = config.getProperty("sms.from", "+1234567890");
        String to = config.getProperty("sms.to", "+521234567890");
        
        if (apikey == null || apikey.isEmpty()) return;
        
        String urlStr = String.format("https://api.twilio.com/2010-04-01/Accounts/%s/Messages.json",
            config.getProperty("sms.accountsid"));
        
        URL url = new URL(urlStr);
        HttpURLConnection conn = (HttpURLConnection) url.openConnection();
        conn.setRequestMethod("POST");
        conn.setDoOutput(true);
        conn.setRequestProperty("Authorization", "Basic " + 
            java.util.Base64.getEncoder().encodeToString(
                (config.getProperty("sms.accountsid") + ":" + apikey).getBytes()
            ));
        
        String body = "From=" + from + "&To=" + to + "&Body=" + 
            java.net.URLEncoder.encode("[AS/400] " + alerta.tipo + ": " + alerta.mensaje, "UTF-8");
        
        OutputStream os = conn.getOutputStream();
        os.write(body.getBytes());
        os.close();
        
        conn.getResponseCode();
    }
    
    static class Alerta {
        String tipo;
        String severidad;
        String mensaje;
        String destinatario;
    }
}
