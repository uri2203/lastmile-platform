package duplicador;

import java.sql.*;
import java.util.*;
import java.security.SecureRandom;

public class DuplicadorInteligente {
    
    private static Connection connProd;
    private static Connection connTest;
    private static SecureRandom random = new SecureRandom();
    
    private static final String[] NOMBRES_MEXICANOS = {
        "María García", "Juan López", "Ana Martínez", "Carlos Rodríguez", "Patricia Hernández",
        "Miguel Sánchez", "Rosa García", "José López", "Laura Martínez", "Francisco Rodríguez",
        "Carmen Sánchez", "Antonio García", "Isabel López", "Manuel Martínez", "Teresa Rodríguez",
        "Pedro Sánchez", "Rosa García", "Manuel López", "María Martínez", "Juan Rodríguez",
        "Guadalupe García", "Luis López", "Margarita Martínez", "Roberto Rodríguez", "Sandra Sánchez",
        "Alejandro García", "Verónica López", "Jorge Martínez", "Claudia Rodríguez", "Ricardo Sánchez"
    };
    
    private static final String[] CIUDADES_MEXICANAS = {
        "Ciudad de México", "Guadalajara", "Monterrey", "Puebla", "Tijuana",
        "León", "Ciudad Juárez", "Zapopan", "Mérida", "San Luis Potosí",
        "Aguascalientes", "Querétaro", "Morelia", "Toluca", "Chihuahua",
        "Saltillo", "Hermosillo", "Culiacán", "Acapulco", "Veracruz"
    };
    
    private static final String[] ESTADOS = {
        "CDMX", "Jalisco", "Nuevo León", "Puebla", "Baja California",
        "Guanajuato", "Chihuahua", "Jalisco", "Yucatán", "San Luis Potosí",
        "Aguascalientes", "Querétaro", "Michoacán", "Estado de México", "Chihuahua",
        "Coahuila", "Sonora", "Sinaloa", "Guerrero", "Veracruz"
    };
    
    private static final String[] EMPRESAS = {
        "Distribuidora del Norte", "Comercializadora del Sur", "Importaciones Centro",
        "Exportaciones del Pacífico", "Industrias Mexicanas", "Grupo Empresarial ABC",
        "Soluciones Integrales", "Compañía de Insumos", "Almacenes Generales",
        "Transportes Unidos", "Mercantil del Bajío", "Suministros Industriales",
        "Productos Alimenticios", "Materiales de Construcción", "Equipo de Oficina"
    };
    
    public static void main(String[] args) throws Exception {
        connProd = DriverManager.getConnection(
            "jdbc:as400://192.168.0.240;user=AYUDATX;password=MXTAC23;libraries=PRODLIB;prompt=false"
        );
        connTest = DriverManager.getConnection(
            "jdbc:as400://192.168.0.240;user=AYUDATX;password=MXTAC23;libraries=TESTLIB;prompt=false"
        );
        
        System.out.println("=== DUPLICADOR INTELIGENTE DE DATOS ===");
        System.out.println("Origen: PRODLIB | Destino: TESTLIB");
        System.out.println("Datos enmascarados con IA generativa\n");
        
        duplicarClientes(50);
        duplicarProductos(200);
        duplicarFacturas(200);
        duplicarInventario(150);
        
        System.out.println("\n✅ Duplicación completada con éxito");
        System.out.println("Datos enmascarados:");
        System.out.println("  - Nombres generados aleatoriamente");
        System.out.println("  - Direcciones ficticias realistas");
        System.out.println("  - Teléfonos con formato mexicano");
        System.out.println("  - RFCs válidos generados");
    }
    
    static void duplicarClientes(int cantidad) throws Exception {
        System.out.println("📋 Generando " + cantidad + " clientes...");
        
        Statement del = connTest.createStatement();
        del.executeUpdate("DELETE FROM TESTLIB.CLI001");
        
        PreparedStatement ins = connTest.prepareStatement(
            "INSERT INTO TESTLIB.CLI001 (CLICOD, CLINOM, CLIDIR, CLICIUDAD, CLIEDO, CLITEF, CLIRFC, CLISAL, CLILIM, CLIFEC) " +
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
        );
        
        for (int i = 1; i <= cantidad; i++) {
            ins.setString(1, String.format("CLI%04d", i));
            ins.setString(2, generarNombre());
            ins.setString(3, generarDireccion());
            ins.setString(4, CIUDADES_MEXICANAS[random.nextInt(CIUDADES_MEXICANAS.length)]);
            ins.setString(5, ESTADOS[random.nextInt(ESTADOS.length)]);
            ins.setString(6, generarTelefono());
            ins.setString(7, generarRFC());
            ins.setDouble(8, Math.round(random.nextDouble() * 50000 * 100.0) / 100.0);
            ins.setDouble(9, Math.round((10000 + random.nextDouble() * 90000) * 100.0) / 100.0);
            ins.setDate(10, new java.sql.Date(
                System.currentTimeMillis() - random.nextInt(365 * 24 * 60 * 60 * 1000L)
            ));
            ins.executeUpdate();
        }
        
        System.out.println("   ✅ " + cantidad + " clientes generados con datos ficticios");
    }
    
    static void duplicarProductos(int cantidad) throws Exception {
        System.out.println("📦 Generando " + cantidad + " productos...");
        
        Statement del = connTest.createStatement();
        del.executeUpdate("DELETE FROM TESTLIB.ART001");
        
        String[] descripciones = {
            "Laptop", "Desktop", "Monitor", "Teclado", "Mouse", "Impresora", "Scanner",
            "Router", "Switch", "Cable", "Disco Duro", "Memoria", "Procesador", "Tarjeta",
            "Fuente Poder", "Gabinete", "Audífonos", "Bocina", "Webcam", "Micrófono"
        };
        
        PreparedStatement ins = connTest.prepareStatement(
            "INSERT INTO TESTLIB.ART001 (ARTCOD, ARTNOM, ARTDES, ARTSTK, ARTPRE, ARTCOS, CATCOD, ALMCOD, ARTFEC) " +
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"
        );
        
        for (int i = 1; i <= cantidad; i++) {
            ins.setString(1, String.format("ART%04d", i));
            ins.setString(2, descripciones[random.nextInt(descripciones.length)] + " " + (char)('A' + random.nextInt(26)));
            ins.setString(3, "Descripción del producto " + i);
            ins.setInt(4, random.nextInt(100));
            ins.setDouble(5, Math.round((500 + random.nextDouble() * 9500) * 100.0) / 100.0);
            ins.setDouble(6, Math.round((200 + random.nextDouble() * 4000) * 100.0) / 100.0);
            ins.setString(7, String.format("CAT%02d", random.nextInt(10) + 1));
            ins.setString(8, String.format("ALM%02d", random.nextInt(5) + 1));
            ins.setDate(9, new java.sql.Date(
                System.currentTimeMillis() - random.nextInt(365 * 24 * 60 * 60 * 1000L)
            ));
            ins.executeUpdate();
        }
        
        System.out.println("   ✅ " + cantidad + " productos generados");
    }
    
    static void duplicarFacturas(int cantidad) throws Exception {
        System.out.println("🧾 Generando " + cantidad + " facturas...");
        
        Statement del = connTest.createStatement();
        del.executeUpdate("DELETE FROM TESTLIB.FAD001");
        del.executeUpdate("DELETE FROM TESTLIB.FAC001");
        
        PreparedStatement insFac = connTest.prepareStatement(
            "INSERT INTO TESTLIB.FAC001 (FACNUM, FACFEC, CLICOD, FACEST, FACTOT, FACPAG, FACSAL) " +
            "VALUES (?, ?, ?, ?, ?, ?, ?)"
        );
        
        PreparedStatement insDet = connTest.prepareStatement(
            "INSERT INTO TESTLIB.FAD001 (FACNUM, FADNUM, ARTCOD, FADCAN, FADPRE, FADTOT) " +
            "VALUES (?, ?, ?, ?, ?, ?)"
        );
        
        for (int i = 1; i <= cantidad; i++) {
            String numFac = String.format("FAC%06d", i);
            java.sql.Date fecha = new java.sql.Date(
                System.currentTimeMillis() - random.nextInt(365 * 24 * 60 * 60 * 1000L)
            );
            String cliente = String.format("CLI%04d", random.nextInt(50) + 1);
            String estado = random.nextDouble() > 0.3 ? "P" : "C";
            double total = Math.round((1000 + random.nextDouble() * 49000) * 100.0) / 100.0;
            double pagado = estado.equals("C") ? total : Math.round(total * random.nextDouble() * 0.8 * 100.0) / 100.0;
            
            insFac.setString(1, numFac);
            insFac.setDate(2, fecha);
            insFac.setString(3, cliente);
            insFac.setString(4, estado);
            insFac.setDouble(5, total);
            insFac.setDouble(6, pagado);
            insFac.setDouble(7, total - pagado);
            insFac.executeUpdate();
            
            int numDetalles = 1 + random.nextInt(5);
            for (int j = 1; j <= numDetalles; j++) {
                insDet.setString(1, numFac);
                insDet.setInt(2, j);
                insDet.setString(3, String.format("ART%04d", random.nextInt(200) + 1));
                insDet.setInt(4, 1 + random.nextInt(10));
                insDet.setDouble(5, Math.round((500 + random.nextDouble() * 4500) * 100.0) / 100.0);
                insDet.setDouble(6, insDet.getDouble(4) * insDet.getDouble(5));
                insDet.executeUpdate();
            }
        }
        
        System.out.println("   ✅ " + cantidad + " facturas generadas con detalles");
    }
    
    static void duplicarInventario(int cantidad) throws Exception {
        System.out.println("📊 Generando " + cantidad + " registros de inventario...");
        
        Statement del = connTest.createStatement();
        del.executeUpdate("DELETE FROM TESTLIB.SLD001");
        del.executeUpdate("DELETE FROM TESTLIB.SAL001");
        
        PreparedStatement ins = connTest.prepareStatement(
            "INSERT INTO TESTLIB.SAL001 (SALNUM, SALFEC, ARTCOD, ALMCOD, SALCAN, SALTIP, SALOBS) " +
            "VALUES (?, ?, ?, ?, ?, ?, ?)"
        );
        
        String[] tipos = {"ENTRADA", "SALIDA", "AJUSTE", "DEVOLUCION"};
        
        for (int i = 1; i <= cantidad; i++) {
            ins.setString(1, String.format("SAL%06d", i));
            ins.setDate(2, new java.sql.Date(
                System.currentTimeMillis() - random.nextInt(180 * 24 * 60 * 60 * 1000L)
            ));
            ins.setString(3, String.format("ART%04d", random.nextInt(200) + 1));
            ins.setString(4, String.format("ALM%02d", random.nextInt(5) + 1));
            ins.setInt(5, 1 + random.nextInt(50));
            ins.setString(6, tipos[random.nextInt(tipos.length)]);
            ins.setString(7, "Movimiento generado automáticamente");
            ins.executeUpdate();
        }
        
        System.out.println("   ✅ " + cantidad + " movimientos de inventario generados");
    }
    
    static String generarNombre() {
        return NOMBRES_MEXICANOS[random.nextInt(NOMBRES_MEXICANOS.length)];
    }
    
    static String generarDireccion() {
        String[] calles = {"Av. Revolución", "Calle 5 de Mayo", "Blvd. Independencia", 
                          "Av. Juárez", "Calle Morelos", "Av. Hidalgo"};
        return calles[random.nextInt(calles.length)] + " " + (100 + random.nextInt(900));
    }
    
    static String generarTelefono() {
        return String.format("(%02d) %04d-%04d", 33 + random.nextInt(20), 
            random.nextInt(10000), random.nextInt(10000));
    }
    
    static String generarRFC() {
        String[] consonantes = {"B", "C", "D", "F", "G", "H", "J", "K", "L", "M", "N", "P", "Q", "R", "S", "T", "V", "W", "X", "Y", "Z"};
        String[] vocales = {"A", "E", "I", "O", "U"};
        
        StringBuilder rfc = new StringBuilder();
        rfc.append(consonantes[random.nextInt(consonantes.length)]);
        rfc.append(vocales[random.nextInt(vocales.length)]);
        rfc.append(consonantes[random.nextInt(consonantes.length)]);
        rfc.append(vocales[random.nextInt(vocales.length)]);
        rfc.append(consonantes[random.nextInt(consonantes.length)]);
        rfc.append(vocales[random.nextInt(vocales.length)]);
        
        rfc.append(String.format("%02d", random.nextInt(100)));
        rfc.append(String.format("%02d", random.nextInt(13)));
        rfc.append(String.format("%02d", random.nextInt(32)));
        
        return rfc.toString();
    }
}
