import java.sql.*;

/**
 * FASE 1D: Módulos adicionales del sistema Last Mile
 * Portal Cliente, API, Gamificación, Notificaciones, Logística Inversa, etc.
 */
public class LastMile_Fase1D {
    
    static Connection c;
    static Statement s;
    static int tablasCreadas = 0;

    public static void main(String[] args) throws Exception {
        c = DriverManager.getConnection(
            "jdbc:as400://192.168.0.240;errors=full", "AYUDATX", "MXTAC23");
        s = c.createStatement();

        System.out.println("=== MODULOS ADICIONALES - LAST MILE ===\n");

        // ========================================
        // MÓDULO 15: PORTAL DEL CLIENTE
        // ========================================
        System.out.println("--- MÓDULO 15: PORTAL DEL CLIENTE ---");
        
        crearTabla("CLIENTE_USUARIOS",
            "CUS_ID INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY, " +
            "EMP_ID INTEGER NOT NULL, " +
            "CLI_ID INTEGER NOT NULL, " +
            "CUS_NOMBRE VARCHAR(100) NOT NULL, " +
            "CUS_EMAIL VARCHAR(100) NOT NULL, " +
            "CUS_PASS VARCHAR(100) NOT NULL, " +
            "CUS_TELEFONO VARCHAR(20) DEFAULT '', " +
            "CUS_ROL VARCHAR(20) DEFAULT 'CONSULTA', " +
            "CUS_ESTATUS VARCHAR(10) DEFAULT 'ACTIVO', " +
            "CUS_ULTIMO_LOGIN TIMESTAMP, " +
            "CUS_FECHA_ALTA DATE DEFAULT CURRENT_DATE"
        );

        crearTabla("CLIENTE_API_KEYS",
            "API_ID INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY, " +
            "EMP_ID INTEGER NOT NULL, " +
            "CLI_ID INTEGER NOT NULL, " +
            "API_KEY VARCHAR(64) NOT NULL, " +
            "API_SECRET VARCHAR(64) NOT NULL, " +
            "API_NOMBRE VARCHAR(50) DEFAULT '', " +
            "API_PERMISOS VARCHAR(200) DEFAULT 'READ', " +
            "API_RATE_LIMIT INTEGER DEFAULT 100, " +
            "API_ESTATUS VARCHAR(10) DEFAULT 'ACTIVO', " +
            "API_FECHA_CREACION TIMESTAMP DEFAULT CURRENT_TIMESTAMP, " +
            "API_ULTIMO_USO TIMESTAMP, " +
            "API_CONTADOR_USOS INTEGER DEFAULT 0"
        );

        crearTabla("CLIENTE_NOTIFICACIONES_CONFIG",
            "CNC_ID INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY, " +
            "EMP_ID INTEGER NOT NULL, " +
            "CLI_ID INTEGER NOT NULL, " +
            "CNC_EMAIL_ACTIVO VARCHAR(5) DEFAULT 'SI', " +
            "CNC_SMS_ACTIVO VARCHAR(5) DEFAULT 'NO', " +
            "CNC_WHATSAPP_ACTIVO VARCHAR(5) DEFAULT 'NO', " +
            "CNC_PUSH_ACTIVO VARCHAR(5) DEFAULT 'NO', " +
            "CNC_EMAIL_DIRECCION VARCHAR(100) DEFAULT '', " +
            "CNC_SMS_TELEFONO VARCHAR(20) DEFAULT '', " +
            "CNC_WHATSAPP_TELEFONO VARCHAR(20) DEFAULT '', " +
            "CNC_NOTIF_ASIGNACION VARCHAR(5) DEFAULT 'SI', " +
            "CNC_NOTIF_RUTA VARCHAR(5) DEFAULT 'SI', " +
            "CNC_NOTIF_ENTREGA VARCHAR(5) DEFAULT 'SI', " +
            "CNC_NOTIF_INCIDENCIA VARCHAR(5) DEFAULT 'SI'"
        );

        // ========================================
        // MÓDULO 16: GAMIFICACIÓN DE CHOFERES
        // ========================================
        System.out.println("\n--- MÓDULO 16: GAMIFICACIÓN ---");
        
        crearTabla("CHOFER_PUNTOS",
            "CPT_ID INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY, " +
            "EMP_ID INTEGER NOT NULL, " +
            "CHO_ID INTEGER NOT NULL, " +
            "CPT_FECHA DATE DEFAULT CURRENT_DATE, " +
            "CPT_PUNTOS_HOY INTEGER DEFAULT 0, " +
            "CPT_PUNTOS_MES INTEGER DEFAULT 0, " +
            "CPT_PUNTOS_TOTALES INTEGER DEFAULT 0, " +
            "CPT_ENTREGAS_SIN_FALLA INTEGER DEFAULT 0, " +
            "CPT_RACHA_DIAS INTEGER DEFAULT 0, " +
            "CPT_RACHA_MAXIMA INTEGER DEFAULT 0"
        );

        crearTabla("CHOFER_INSIGNIAS",
            "CIN_ID INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY, " +
            "EMP_ID INTEGER NOT NULL, " +
            "CHO_ID INTEGER NOT NULL, " +
            "CIN_INSIGNIA VARCHAR(50) NOT NULL, " +
            "CIN_DESCRIPCION VARCHAR(200) DEFAULT '', " +
            "CIN_FECHA_OBTENIDA TIMESTAMP DEFAULT CURRENT_TIMESTAMP, " +
            "CIN_NIVEL INTEGER DEFAULT 1"
        );

        crearTabla("CHOFER_RANKING",
            "CRK_ID INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY, " +
            "EMP_ID INTEGER NOT NULL, " +
            "CHO_ID INTEGER NOT NULL, " +
            "CRK_PERIODO VARCHAR(20) DEFAULT 'MENSUAL', " +
            "CRK_FECHA_INICIO DATE, " +
            "CRK_FECHA_FIN DATE, " +
            "CRK_POSICION INTEGER DEFAULT 0, " +
            "CRK_PUNTOS INTEGER DEFAULT 0, " +
            "CRK_ENTREGAS INTEGER DEFAULT 0, " +
            "CRK_TASA_EXITO DECIMAL(5,2) DEFAULT 0, " +
            "CRK_BONO DECIMAL(10,2) DEFAULT 0"
        );

        // ========================================
        // MÓDULO 17: NOTIFICACIONES AVANZADAS
        // ========================================
        System.out.println("\n--- MÓDULO 17: NOTIFICACIONES ---");
        
        crearTabla("NOTIF_PLANTILLAS",
            "NPL_ID INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY, " +
            "EMP_ID INTEGER NOT NULL, " +
            "NPL_NOMBRE VARCHAR(50) NOT NULL, " +
            "NPL_EVENTO VARCHAR(50) NOT NULL, " +
            "NPL_CANAL VARCHAR(20) DEFAULT 'EMAIL', " +
            "NPL_ASUNTO VARCHAR(200) DEFAULT '', " +
            "NPL_CUERPO VARCHAR(2000) DEFAULT '', " +
            "NPL_ACTIVA VARCHAR(5) DEFAULT 'SI'"
        );

        crearTabla("NOTIF_ENVIOS",
            "NEV_ID INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY, " +
            "EMP_ID INTEGER NOT NULL, " +
            "PED_ID INTEGER, " +
            "CLI_ID INTEGER, " +
            "CHO_ID INTEGER, " +
            "NEV_CANAL VARCHAR(20) NOT NULL, " +
            "NEV_DESTINATARIO VARCHAR(100) NOT NULL, " +
            "NEV_ASUNTO VARCHAR(200) DEFAULT '', " +
            "NEV_MENSAJE VARCHAR(2000) DEFAULT '', " +
            "NEV_ESTADO VARCHAR(20) DEFAULT 'PENDIENTE', " +
            "NEV_INTENTOS INTEGER DEFAULT 0, " +
            "NEV_FECHA_ENVIO TIMESTAMP, " +
            "NEV_FECHA_LEIDO TIMESTAMP, " +
            "NEV_ERROR VARCHAR(300) DEFAULT ''"
        );

        // ========================================
        // MÓDULO 18: LOGÍSTICA INVERSA (DEVOLUCIONES)
        // ========================================
        System.out.println("\n--- MÓDULO 18: LOGÍSTICA INVERSA ---");
        
        crearTabla("DEVOLUCIONES",
            "DEV_ID INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY, " +
            "EMP_ID INTEGER NOT NULL, " +
            "PED_ID INTEGER NOT NULL, " +
            "CHO_ID INTEGER NOT NULL, " +
            "DEV_MOTIVO VARCHAR(100) NOT NULL, " +
            "DEV_DESCRIPCION VARCHAR(500) DEFAULT '', " +
            "DEV_ESTADO VARCHAR(20) DEFAULT 'PENDIENTE', " +
            "DEV_FECHA_REGISTRO TIMESTAMP DEFAULT CURRENT_TIMESTAMP, " +
            "DEV_FECHA_RESOLUCION TIMESTAMP, " +
            "DEV_TIPO_RESOLUCION VARCHAR(30) DEFAULT '', " +
            "DEV_COSTO DECIMAL(10,2) DEFAULT 0, " +
            "DEV_LATITUD DECIMAL(10,7) DEFAULT 0, " +
            "DEV_LONGITUD DECIMAL(10,7) DEFAULT 0, " +
            "DEV_FOTO_URL VARCHAR(500) DEFAULT ''"
        );

        // ========================================
        // MÓDULO 19: CONTROL DE FRAUDE
        // ========================================
        System.out.println("\n--- MÓDULO 19: CONTROL DE FRAUDE ---");
        
        crearTabla("FRAUDE_ALERTAS",
            "FRA_ID INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY, " +
            "EMP_ID INTEGER NOT NULL, " +
            "CHO_ID INTEGER, " +
            "PED_ID INTEGER, " +
            "FRA_TIPO VARCHAR(50) NOT NULL, " +
            "FRA_DESCRIPCION VARCHAR(500) DEFAULT '', " +
            "FRA_SEVERIDAD VARCHAR(10) DEFAULT 'MEDIA', " +
            "FRA_ESTADO VARCHAR(20) DEFAULT 'ABIERTA', " +
            "FRA_FECHA TIMESTAMP DEFAULT CURRENT_TIMESTAMP, " +
            "FRA_FECHA_RESOLUCION TIMESTAMP, " +
            "FRA_RESUELTA_POR VARCHAR(50) DEFAULT '', " +
            "FRA_NOTAS VARCHAR(300) DEFAULT ''"
        );

        crearTabla("FRAUDE_UBICACIONES",
            "FUB_ID INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY, " +
            "EMP_ID INTEGER NOT NULL, " +
            "CHO_ID INTEGER NOT NULL, " +
            "PED_ID INTEGER, " +
            "FUB_LAT_ENTREGA DECIMAL(10,7) NOT NULL, " +
            "FUB_LON_ENTREGA DECIMAL(10,7) NOT NULL, " +
            "FUB_LAT_GPS DECIMAL(10,7) NOT NULL, " +
            "FUB_LON_GPS DECIMAL(10,7) NOT NULL, " +
            "FUB_DISTANCIA_METROS INTEGER DEFAULT 0, " +
            "FUB_FECHA TIMESTAMP DEFAULT CURRENT_TIMESTAMP, " +
            "FUB_ES_FRAUDE VARCHAR(5) DEFAULT 'NO'"
        );

        // ========================================
        // MÓDULO 20: SLA (ACUERDO DE NIVEL DE SERVICIO)
        // ========================================
        System.out.println("\n--- MÓDULO 20: SLA ---");
        
        crearTabla("SLA_CONFIGURACION",
            "SLA_ID INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY, " +
            "EMP_ID INTEGER NOT NULL, " +
            "CLI_ID INTEGER, " +
            "SLA_NOMBRE VARCHAR(50) NOT NULL, " +
            "SLA_TIEMPO_MAX_HORAS INTEGER DEFAULT 24, " +
            "SLA_TASA_MINIMA_EXITO DECIMAL(5,2) DEFAULT 95.00, " +
            "SLA Penalizacion_PCT DECIMAL(5,2) DEFAULT 5.00, " +
            "SLA Penalizacion_MAX DECIMAL(10,2) DEFAULT 500.00, " +
            "SLA_ESTATUS VARCHAR(10) DEFAULT 'ACTIVO'"
        );

        crearTabla("SLA_RESULTADOS",
            "SLR_ID INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY, " +
            "EMP_ID INTEGER NOT NULL, " +
            "CLI_ID INTEGER NOT NULL, " +
            "SLA_ID INTEGER NOT NULL, " +
            "SLR_PERIODO VARCHAR(20) DEFAULT 'MENSUAL', " +
            "SLR_FECHA_INICIO DATE, " +
            "SLR_FECHA_FIN DATE, " +
            "SLR_TOTAL_PEDIDOS INTEGER DEFAULT 0, " +
            "SLR_ENTREGAS_A_TIEMPO INTEGER DEFAULT 0, " +
            "SLR_TASA_CUMPLIMIENTO DECIMAL(5,2) DEFAULT 0, " +
            "SLR_CUMPLE VARCHAR(5) DEFAULT 'SI', " +
            "SLR Penalizacion DECIMAL(10,2) DEFAULT 0"
        );

        // ========================================
        // MÓDULO 21: WHITELABEL
        // ========================================
        System.out.println("\n--- MÓDULO 21: WHITELABEL ---");
        
        crearTabla("WHITELABEL_CONFIG",
            "WHL_ID INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY, " +
            "EMP_ID INTEGER NOT NULL, " +
            "WHL_LOGO_URL VARCHAR(500) DEFAULT '', " +
            "WHL_COLOR_PRIMARY VARCHAR(10) DEFAULT '#0066B2', " +
            "WHL_COLOR_SECONDARY VARCHAR(10) DEFAULT '#00994C', " +
            "WHL_COLOR_BG VARCHAR(10) DEFAULT '#FFFFFF', " +
            "WHL_NOMBRE_PUBLICO VARCHAR(100) DEFAULT '', " +
            "WHL_DOMINIO VARCHAR(100) DEFAULT '', " +
            "WHL_EMAIL_FROM VARCHAR(100) DEFAULT '', " +
            "WHL_FOOTER_TEXT VARCHAR(300) DEFAULT '', " +
            "WHL_ACTIVO VARCHAR(5) DEFAULT 'NO'"
        );

        // ========================================
        // MÓDULO 22: FACTURACIÓN AUTOMÁTICA
        // ========================================
        System.out.println("\n--- MÓDULO 22: FACTURACIÓN SaaS ---");
        
        crearTabla("SAAS_SUSCRIPCIONES",
            "SUS_ID INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY, " +
            "EMP_ID INTEGER NOT NULL, " +
            "SUS_PLAN VARCHAR(30) NOT NULL, " +
            "SUS_PRECIO_MENSUAL DECIMAL(10,2) DEFAULT 0, " +
            "SUS_MAX_PEDIDOS_MES INTEGER DEFAULT 500, " +
            "SUS_MAX_USUARIOS INTEGER DEFAULT 5, " +
            "SUS_MAX_CHOFERES INTEGER DEFAULT 10, " +
            "SUS_API_ACCESO VARCHAR(5) DEFAULT 'NO', " +
            "SUS_WHITELABEL VARCHAR(5) DEFAULT 'NO', " +
            "SUS_NOTIF_SMS VARCHAR(5) DEFAULT 'NO', " +
            "SUS_NOTIF_WHATSAPP VARCHAR(5) DEFAULT 'NO', " +
            "SUS_FECHA_INICIO DATE DEFAULT CURRENT_DATE, " +
            "SUS_FECHA_FIN DATE, " +
            "SUS_ESTADO VARCHAR(15) DEFAULT 'ACTIVA', " +
            "SUS_METODO_PAGO VARCHAR(20) DEFAULT 'TARJETA'"
        );

        crearTabla("SAAS_FACTURACION",
            "SAF_ID INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY, " +
            "EMP_ID INTEGER NOT NULL, " +
            "SUS_ID INTEGER NOT NULL, " +
            "SAF_FACTURA_NUM VARCHAR(20) NOT NULL, " +
            "SAF_PERIODO VARCHAR(20) DEFAULT '', " +
            "SAF_MONTO_BASE DECIMAL(10,2) DEFAULT 0, " +
            "SAF_MONTO_EXTRA DECIMAL(10,2) DEFAULT 0, " +
            "SAF_MONTO_DESCUENTO DECIMAL(10,2) DEFAULT 0, " +
            "SAF_MONTO_TOTAL DECIMAL(10,2) DEFAULT 0, " +
            "SAF_ESTADO VARCHAR(20) DEFAULT 'PENDIENTE', " +
            "SAF_FECHA_EMISION DATE DEFAULT CURRENT_DATE, " +
            "SAF_FECHA_PAGO DATE, " +
            "SAF_METODO_PAGO VARCHAR(20) DEFAULT '', " +
            "SAF_NOTAS VARCHAR(300) DEFAULT ''"
        );

        // ========================================
        // MÓDULO 23: AUDITORÍA / AUDIT TRAIL
        // ========================================
        System.out.println("\n--- MÓDULO 23: AUDITORÍA ---");
        
        crearTabla("AUDIT_LOG",
            "AUD_ID INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY, " +
            "EMP_ID INTEGER NOT NULL, " +
            "AUD_USUARIO VARCHAR(50) NOT NULL, " +
            "AUD_ROL VARCHAR(30) DEFAULT '', " +
            "AUD_ACCION VARCHAR(30) NOT NULL, " +
            "AUD_TABLA VARCHAR(50) DEFAULT '', " +
            "AUD_REGISTRO_ID INTEGER DEFAULT 0, " +
            "AUD_CAMPO VARCHAR(50) DEFAULT '', " +
            "AUD_VALOR_ANTERIOR VARCHAR(300) DEFAULT '', " +
            "AUD_VALOR_NUEVO VARCHAR(300) DEFAULT '', " +
            "AUD_IP VARCHAR(50) DEFAULT '', " +
            "AUD_FECHA TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
        );

        // ========================================
        // MÓDULO 24: RUTAS AUTOMÁTICAS
        // ========================================
        System.out.println("\n--- MÓDULO 24: OPTIMIZACIÓN DE RUTAS ---");
        
        crearTabla("RUTA_OPTIMIZADA",
            "ROP_ID INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY, " +
            "EMP_ID INTEGER NOT NULL, " +
            "ROP_FECHA DATE DEFAULT CURRENT_DATE, " +
            "CHO_ID INTEGER, " +
            "VEH_ID INTEGER, " +
            "ROP_TOTAL_STOPS INTEGER DEFAULT 0, " +
            "ROP_DISTANCIA_TOTAL_KM DECIMAL(10,2) DEFAULT 0, " +
            "ROP_TIEMPO_TOTAL_MIN INTEGER DEFAULT 0, " +
            "ROP_HORA_INICIO TIMESTAMP, " +
            "ROP_HORA_FIN_EST TIMESTAMP, " +
            "ROP_ESTADO VARCHAR(20) DEFAULT 'GENERADA', " +
            "ROP_ALGORITMO VARCHAR(30) DEFAULT 'NEAREST_NEIGHBOR'"
        );

        crearTabla("RUTA_OPTIMIZADA_DETALLE",
            "ROD_ID INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY, " +
            "ROP_ID INTEGER NOT NULL, " +
            "PED_ID INTEGER NOT NULL, " +
            "ROD_ORDEN INTEGER DEFAULT 0, " +
            "ROD_LAT_DESTINO DECIMAL(10,7) DEFAULT 0, " +
            "ROD_LON_DESTINO DECIMAL(10,7) DEFAULT 0, " +
            "ROD_DISTANCIA_KM DECIMAL(8,2) DEFAULT 0, " +
            "ROD_TIEMPO_EST_MIN INTEGER DEFAULT 0, " +
            "ROD_VENTANA_INICIO TIMESTAMP, " +
            "ROD_VENTANA_FIN TIMESTAMP"
        );

        // ========================================
        // MÓDULO 25: MÉTRICAS COMPARTIDAS CLIENTE
        // ========================================
        System.out.println("\n--- MÓDULO 25: MÉTRICAS CLIENTE ---");
        
        crearTabla("CLIENTE_METRICAS",
            "CME_ID INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY, " +
            "EMP_ID INTEGER NOT NULL, " +
            "CLI_ID INTEGER NOT NULL, " +
            "CME_PERIODO VARCHAR(20) DEFAULT 'MENSUAL', " +
            "CME_FECHA_INICIO DATE, " +
            "CME_FECHA_FIN DATE, " +
            "CME_TOTAL_ENVIOS INTEGER DEFAULT 0, " +
            "CME_ENVIOS_ENTREGADOS INTEGER DEFAULT 0, " +
            "CME_ENVIOS_FALLIDOS INTEGER DEFAULT 0, " +
            "CME_ENVIOS_DEVUELTOS INTEGER DEFAULT 0, " +
            "CME_TASA_EXITO DECIMAL(5,2) DEFAULT 0, " +
            "CME_TIEMPO_PROMedio_HRS DECIMAL(5,1) DEFAULT 0, " +
            "CME_COSTO_TOTAL DECIMAL(12,2) DEFAULT 0, " +
            "CME_COSTO_PROMedio_ENVIO DECIMAL(10,2) DEFAULT 0, " +
            "CME_INCIDENCIAS INTEGER DEFAULT 0, " +
            "CME_SATISFACCION_PROMedio DECIMAL(3,1) DEFAULT 0"
        );

        // ========================================
        // RESUMEN
        // ========================================
        System.out.println("\n========================================");
        System.out.println("MÓDULOS ADICIONALES CREADOS: 11");
        System.out.println("TABLAS NUEVAS: " + tablasCreadas);
        System.out.println("========================================");

        c.close();
        System.out.println("\n=== FIN FASE 1D - MÓDULOS ADICIONALES ===");
    }

    static void crearTabla(String nombre, String columnas) {
        try {
            try {
                ResultSet rs = s.executeQuery("SELECT COUNT(*) FROM QSYS2.SYSTABLES WHERE TABLE_SCHEMA = 'TESTLIB' AND TABLE_NAME = '" + nombre + "'");
                rs.next();
                if (rs.getInt(1) > 0) {
                    System.out.println("  SKIP " + nombre + " (ya existe)");
                    rs.close();
                    return;
                }
                rs.close();
            } catch (Exception e) {}

            String sql = "CREATE TABLE TESTLIB." + nombre + " (" + columnas + ")";
            s.executeUpdate(sql);
            tablasCreadas++;
            System.out.println("  OK " + nombre);

        } catch (Exception e) {
            String msg = e.getMessage();
            if (msg != null) msg = msg.split("\n")[0];
            System.out.println("  ERROR " + nombre + ": " + msg);
        }
    }
}
