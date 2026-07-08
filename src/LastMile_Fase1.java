import java.sql.*;

/**
 * FASE 1: Diseñar y crear el sistema Last Mile completo en TESTLIB
 * Multi-cliente (SaaS) - Licencia mensual
 */
public class LastMile_Fase1 {
    
    static Connection c;
    static Statement s;
    static int tablasCreadas = 0;
    static int registrosInsertados = 0;

    public static void main(String[] args) throws Exception {
        c = DriverManager.getConnection(
            "jdbc:as400://192.168.0.240;errors=full", "AYUDATX", "MXTAC23");
        s = c.createStatement();

        System.out.println("=== SISTEMA LAST MILE COMPLETO - FASE 1 ===\n");
        System.out.println("Creando tablas multi-cliente en TESTLIB...\n");

        // ========================================
        // MÓDULO 1: EMPRESAS / MULTI-TENANT
        // ========================================
        System.out.println("--- MÓDULO 1: EMPRESAS / MULTI-TENANT ---");
        
        crearTabla("EMPRESAS",
            "EMP_ID INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY, " +
            "EMP_NOMBRE VARCHAR(100) NOT NULL, " +
            "EMP_RFC VARCHAR(20) DEFAULT '', " +
            "EMP_DIRECCION VARCHAR(200) DEFAULT '', " +
            "EMP_TELEFONO VARCHAR(20) DEFAULT '', " +
            "EMP_EMAIL VARCHAR(100) DEFAULT '', " +
            "EMP_CONTACTO VARCHAR(100) DEFAULT '', " +
            "EMP_FECHA_ALTA DATE DEFAULT CURRENT_DATE, " +
            "EMP_ESTATUS VARCHAR(10) DEFAULT 'ACTIVO', " +
            "EMP_PLAN VARCHAR(20) DEFAULT 'BASICO', " +
            "EMP_MAX_USUARIOS INTEGER DEFAULT 5, " +
            "EMP_MAX_CHOFERES INTEGER DEFAULT 10, " +
            "EMP_MAX_PEDIDOS_MES INTEGER DEFAULT 500"
        );

        crearTabla("USUARIOS",
            "USR_ID INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY, " +
            "EMP_ID INTEGER NOT NULL, " +
            "USR_NOMBRE VARCHAR(100) NOT NULL, " +
            "USR_USER VARCHAR(50) NOT NULL, " +
            "USR_PASS VARCHAR(100) NOT NULL, " +
            "USR_EMAIL VARCHAR(100) DEFAULT '', " +
            "USR_TELEFONO VARCHAR(20) DEFAULT '', " +
            "USR_ROL VARCHAR(30) DEFAULT 'OPERADOR', " +
            "USR_ESTATUS VARCHAR(10) DEFAULT 'ACTIVO', " +
            "USR_ULTIMO_LOGIN TIMESTAMP"
        );

        // ========================================
        // MÓDULO 2: CHOFERES / REPARTIDORES
        // ========================================
        System.out.println("\n--- MÓDULO 2: CHOFERES ---");
        
        crearTabla("CHOFERES",
            "CHO_ID INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY, " +
            "EMP_ID INTEGER NOT NULL, " +
            "CHO_NOMBRE VARCHAR(100) NOT NULL, " +
            "CHO_APELLIDO VARCHAR(100) DEFAULT '', " +
            "CHO_RFC VARCHAR(20) DEFAULT '', " +
            "CHO_LICENCIA VARCHAR(30) DEFAULT '', " +
            "CHO_TELEFONO VARCHAR(20) DEFAULT '', " +
            "CHO_EMAIL VARCHAR(100) DEFAULT '', " +
            "CHO_FECHA_ALTA DATE DEFAULT CURRENT_DATE, " +
            "CHO_ESTATUS VARCHAR(10) DEFAULT 'ACTIVO', " +
            "CHO_TIPO VARCHAR(20) DEFAULT 'PROPIO', " +
            "CHO_SALARIO_BASE DECIMAL(10,2) DEFAULT 0, " +
            "CHO_COMISION_PCT DECIMAL(5,2) DEFAULT 0"
        );

        crearTabla("VEHICULOS",
            "VEH_ID INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY, " +
            "EMP_ID INTEGER NOT NULL, " +
            "VEH_UNIDAD VARCHAR(20) NOT NULL, " +
            "VEH_MARCA VARCHAR(30) DEFAULT '', " +
            "VEH_MODELO VARCHAR(30) DEFAULT '', " +
            "VEH_AÑO INTEGER DEFAULT 0, " +
            "VEH_PLACAS VARCHAR(20) DEFAULT '', " +
            "VEH_COLOR VARCHAR(20) DEFAULT '', " +
            "VEH_TIPO VARCHAR(20) DEFAULT 'PICKUP', " +
            "VEH_CAPACIDAD_KG DECIMAL(8,2) DEFAULT 0, " +
            "VEH_CAPACIDAD_M3 DECIMAL(8,2) DEFAULT 0, " +
            "VEH_ESTATUS VARCHAR(10) DEFAULT 'ACTIVO', " +
            "VEH_GPS_ACTIVO VARCHAR(5) DEFAULT 'NO', " +
            "VEH_ULTIMA_VELOCIDAD INTEGER DEFAULT 0"
        );

        // ========================================
        // MÓDULO 3: CLIENTES / DESTINOS
        // ========================================
        System.out.println("\n--- MÓDULO 3: CLIENTES ---");
        
        crearTabla("CLIENTES_LM",
            "CLI_ID INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY, " +
            "EMP_ID INTEGER NOT NULL, " +
            "CLI_RAZON_SOCIAL VARCHAR(150) NOT NULL, " +
            "CLI_RFC VARCHAR(20) DEFAULT '', " +
            "CLI_CONTACTO VARCHAR(100) DEFAULT '', " +
            "CLI_TELEFONO VARCHAR(20) DEFAULT '', " +
            "CLI_EMAIL VARCHAR(100) DEFAULT '', " +
            "CLI_DIRECCION VARCHAR(250) DEFAULT '', " +
            "CLI_COLONIA VARCHAR(100) DEFAULT '', " +
            "CLI_CIUDAD VARCHAR(100) DEFAULT '', " +
            "CLI_ESTADO VARCHAR(50) DEFAULT '', " +
            "CLI_CP VARCHAR(10) DEFAULT '', " +
            "CLI_LATITUD DECIMAL(10,7) DEFAULT 0, " +
            "CLI_LONGITUD DECIMAL(10,7) DEFAULT 0, " +
            "CLI_ZONA VARCHAR(30) DEFAULT '', " +
            "CLI_ESTATUS VARCHAR(10) DEFAULT 'ACTIVO', " +
            "CLI_FECHA_ALTA DATE DEFAULT CURRENT_DATE, " +
            "CLI_TIPO_CLIENTE VARCHAR(20) DEFAULT 'REGULAR', " +
            "CLI_CREDITO DECIMAL(12,2) DEFAULT 0, " +
            "CLI_SALDO DECIMAL(12,2) DEFAULT 0"
        );

        // ========================================
        // MÓDULO 4: ZONAS / COBERTURA
        // ========================================
        System.out.println("\n--- MÓDULO 4: ZONAS ---");
        
        crearTabla("ZONAS",
            "ZON_ID INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY, " +
            "EMP_ID INTEGER NOT NULL, " +
            "ZON_NOMBRE VARCHAR(50) NOT NULL, " +
            "ZON_DESCRIPCION VARCHAR(200) DEFAULT '', " +
            "ZON_COLOR VARCHAR(10) DEFAULT '#0066B2', " +
            "ZON_LAT_MIN DECIMAL(10,7) DEFAULT 0, " +
            "ZON_LAT_MAX DECIMAL(10,7) DEFAULT 0, " +
            "ZON_LON_MIN DECIMAL(10,7) DEFAULT 0, " +
            "ZON_LON_MAX DECIMAL(10,7) DEFAULT 0, " +
            "ZON_ESTATUS VARCHAR(10) DEFAULT 'ACTIVO'"
        );

        // ========================================
        // MÓDULO 5: TARIFAS / PRECIOS
        // ========================================
        System.out.println("\n--- MÓDULO 5: TARIFAS ---");
        
        crearTabla("TARIFAS_LM",
            "TAR_ID INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY, " +
            "EMP_ID INTEGER NOT NULL, " +
            "TAR_NOMBRE VARCHAR(50) NOT NULL, " +
            "TAR_TIPO VARCHAR(30) DEFAULT 'POR_ENTREGA', " +
            "TAR_MONTO_BASE DECIMAL(10,2) DEFAULT 0, " +
            "TAR_MONTO_KM DECIMAL(10,2) DEFAULT 0, " +
            "TAR_MONTO_KG DECIMAL(10,2) DEFAULT 0, " +
            "TAR_MONTO_M3 DECIMAL(10,2) DEFAULT 0, " +
            "TAR_MONTO_ESPERA_MIN DECIMAL(10,2) DEFAULT 0, " +
            "TAR_MONTO_ENTREGA_EXT DECIMAL(10,2) DEFAULT 0, " +
            "TAR_ESTATUS VARCHAR(10) DEFAULT 'ACTIVO', " +
            "TAR_FECHA_INICIO DATE DEFAULT CURRENT_DATE, " +
            "TAR_FECHA_FIN DATE"
        );

        // ========================================
        // MÓDULO 6: PEDIDOS / ÓRDENES DE ENTREGA
        // ========================================
        System.out.println("\n--- MÓDULO 6: PEDIDOS ---");
        
        crearTabla("PEDIDOS",
            "PED_ID INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY, " +
            "EMP_ID INTEGER NOT NULL, " +
            "PED_NUMERO VARCHAR(20) NOT NULL, " +
            "CLI_ID INTEGER NOT NULL, " +
            "PED_CLIENTE_NOMBRE VARCHAR(150) DEFAULT '', " +
            "PED_CLIENTE_TELEFONO VARCHAR(20) DEFAULT '', " +
            "PED_CLIENTE_EMAIL VARCHAR(100) DEFAULT '', " +
            "PED_ORIGEN_DIR VARCHAR(250) DEFAULT '', " +
            "PED_ORIGEN_LAT DECIMAL(10,7) DEFAULT 0, " +
            "PED_ORIGEN_LON DECIMAL(10,7) DEFAULT 0, " +
            "PED_DESTINO_DIR VARCHAR(250) DEFAULT '', " +
            "PED_DESTINO_COL VARCHAR(100) DEFAULT '', " +
            "PED_DESTINO_CIUDAD VARCHAR(100) DEFAULT '', " +
            "PED_DESTINO_ESTADO VARCHAR(50) DEFAULT '', " +
            "PED_DESTINO_CP VARCHAR(10) DEFAULT '', " +
            "PED_DESTINO_LAT DECIMAL(10,7) DEFAULT 0, " +
            "PED_DESTINO_LON DECIMAL(10,7) DEFAULT 0, " +
            "PED_DESCRIPCION VARCHAR(500) DEFAULT '', " +
            "PED_REFERENCIA VARCHAR(100) DEFAULT '', " +
            "PED_PESO_KG DECIMAL(8,2) DEFAULT 0, " +
            "PED_VOLUMEN_M3 DECIMAL(8,2) DEFAULT 0, " +
            "PED_BULTOS INTEGER DEFAULT 1, " +
            "PED_VALOR_DECLARADO DECIMAL(12,2) DEFAULT 0, " +
            "PED_COSTO_ENVIO DECIMAL(10,2) DEFAULT 0, " +
            "PED_COSTO_TOTAL DECIMAL(10,2) DEFAULT 0, " +
            "PED_FORMA_PAGO VARCHAR(20) DEFAULT 'EFECTIVO', " +
            "PED_ESTADO VARCHAR(20) DEFAULT 'PENDIENTE', " +
            "PED_PRIORIDAD VARCHAR(10) DEFAULT 'NORMAL', " +
            "PED_FECHA_PEDIDO TIMESTAMP DEFAULT CURRENT_TIMESTAMP, " +
            "PED_FECHA_RECOLECTA TIMESTAMP, " +
            "PED_FECHA_ENTREGA_EST TIMESTAMP, " +
            "PED_FECHA_ENTREGA_REAL TIMESTAMP, " +
            "PED_INSTRUCCIONES VARCHAR(500) DEFAULT '', " +
            "PED_NOTASInternas VARCHAR(500) DEFAULT ''"
        );

        crearTabla("PEDIDO_HISTORIAL",
            "HIS_ID INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY, " +
            "PED_ID INTEGER NOT NULL, " +
            "HIS_ESTADO VARCHAR(20) NOT NULL, " +
            "HIS_FECHA TIMESTAMP DEFAULT CURRENT_TIMESTAMP, " +
            "HIS_USUARIO VARCHAR(50) DEFAULT '', " +
            "HIS_OBSERVACIONES VARCHAR(300) DEFAULT ''"
        );

        // ========================================
        // MÓDULO 7: RUTAS / ITINERARIOS
        // ========================================
        System.out.println("\n--- MÓDULO 7: RUTAS ---");
        
        crearTabla("RUTAS",
            "RUT_ID INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY, " +
            "EMP_ID INTEGER NOT NULL, " +
            "RUT_NOMBRE VARCHAR(50) NOT NULL, " +
            "RUT_FECHA DATE DEFAULT CURRENT_DATE, " +
            "CHO_ID INTEGER, " +
            "VEH_ID INTEGER, " +
            "RUT_ESTADO VARCHAR(20) DEFAULT 'PENDIENTE', " +
            "RUT_TOTAL_PEDIDOS INTEGER DEFAULT 0, " +
            "RUT_TOTAL_ENTREGAS INTEGER DEFAULT 0, " +
            "RUT_TOTAL_KM DECIMAL(8,2) DEFAULT 0, " +
            "RUT_TOTAL_TIEMPO_MIN INTEGER DEFAULT 0, " +
            "RUT_HORA_INICIO TIMESTAMP, " +
            "RUT_HORA_FIN TIMESTAMP, " +
            "RUT_COSTO_TOTAL DECIMAL(10,2) DEFAULT 0"
        );

        crearTabla("RUTA_DETALLE",
            "RDE_ID INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY, " +
            "RUT_ID INTEGER NOT NULL, " +
            "PED_ID INTEGER NOT NULL, " +
            "RDE_ORDEN INTEGER DEFAULT 0, " +
            "RDE_ESTADO VARCHAR(20) DEFAULT 'PENDIENTE', " +
            "RDE_DISTANCIA_KM DECIMAL(8,2) DEFAULT 0, " +
            "RDE_TIEMPO_EST_MIN INTEGER DEFAULT 0, " +
            "RDE_HORA_LLEGADA TIMESTAMP, " +
            "RDE_HORA_SALIDA TIMESTAMP, " +
            "RDE_NOTAS VARCHAR(300) DEFAULT ''"
        );

        // ========================================
        // MÓDULO 8: ASIGNACIONES
        // ========================================
        System.out.println("\n--- MÓDULO 8: ASIGNACIONES ---");
        
        crearTabla("ASIGNACIONES",
            "ASI_ID INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY, " +
            "EMP_ID INTEGER NOT NULL, " +
            "PED_ID INTEGER NOT NULL, " +
            "CHO_ID INTEGER NOT NULL, " +
            "VEH_ID INTEGER, " +
            "RUT_ID INTEGER, " +
            "ASI_FECHA_ASIG TIMESTAMP DEFAULT CURRENT_TIMESTAMP, " +
            "ASI_ESTADO VARCHAR(20) DEFAULT 'ASIGNADO', " +
            "ASI_ORDEN INTEGER DEFAULT 0"
        );

        // ========================================
        // MÓDULO 9: ENTREGAS / PROOF OF DELIVERY
        // ========================================
        System.out.println("\n--- MÓDULO 9: ENTREGAS ---");
        
        crearTabla("ENTREGAS",
            "ENT_ID INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY, " +
            "EMP_ID INTEGER NOT NULL, " +
            "PED_ID INTEGER NOT NULL, " +
            "CHO_ID INTEGER NOT NULL, " +
            "ENT_FECHA_LLEGADA TIMESTAMP DEFAULT CURRENT_TIMESTAMP, " +
            "ENT_FECHA_ENTREGA TIMESTAMP, " +
            "ENT_RECEPTOR_NOMBRE VARCHAR(150) DEFAULT '', " +
            "ENT_RECEPTOR_ID VARCHAR(50) DEFAULT '', " +
            "ENT_FIRMA_BLOB BLOB, " +
            "ENT_FOTO_URL VARCHAR(500) DEFAULT '', " +
            "ENT_LATITUD DECIMAL(10,7) DEFAULT 0, " +
            "ENT_LONGITUD DECIMAL(10,7) DEFAULT 0, " +
            "ENT_ESTADO VARCHAR(20) DEFAULT 'ENTREGADO', " +
            "ENT_MOTIVO_NO VARCHAR(100) DEFAULT '', " +
            "ENT_NOTAS VARCHAR(300) DEFAULT '', " +
            "ENT_TIEMPO_ESPERA_MIN INTEGER DEFAULT 0, " +
            "ENT_INTENTOS INTEGER DEFAULT 1"
        );

        // ========================================
        // MÓDULO 10: INCIDENCIAS
        // ========================================
        System.out.println("\n--- MÓDULO 10: INCIDENCIAS ---");
        
        crearTabla("INCIDENCIAS",
            "INC_ID INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY, " +
            "EMP_ID INTEGER NOT NULL, " +
            "PED_ID INTEGER, " +
            "CHO_ID INTEGER, " +
            "INC_TIPO VARCHAR(50) NOT NULL, " +
            "INC_DESCRIPCION VARCHAR(500) DEFAULT '', " +
            "INC_FECHA TIMESTAMP DEFAULT CURRENT_TIMESTAMP, " +
            "INC_ESTADO VARCHAR(20) DEFAULT 'ABIERTA', " +
            "INC_RESOLUCION VARCHAR(300) DEFAULT '', " +
            "INC_FECHA_RESOLUCION TIMESTAMP, " +
            "INC_LATITUD DECIMAL(10,7) DEFAULT 0, " +
            "INC_LONGITUD DECIMAL(10,7) DEFAULT 0, " +
            "INC_FOTO_URL VARCHAR(500) DEFAULT ''"
        );

        // ========================================
        // MÓDULO 11: TRACKING GPS
        // ========================================
        System.out.println("\n--- MÓDULO 11: TRACKING ---");
        
        crearTabla("TRACKING",
            "TRK_ID INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY, " +
            "EMP_ID INTEGER NOT NULL, " +
            "CHO_ID INTEGER NOT NULL, " +
            "VEH_ID INTEGER, " +
            "TRK_LATITUD DECIMAL(10,7) NOT NULL, " +
            "TRK_LONGITUD DECIMAL(10,7) NOT NULL, " +
            "TRK_VELOCIDAD INTEGER DEFAULT 0, " +
            "TRK_RUMBO INTEGER DEFAULT 0, " +
            "TRK_FECHA TIMESTAMP DEFAULT CURRENT_TIMESTAMP, " +
            "TRK_BATERIA INTEGER DEFAULT 100"
        );

        // ========================================
        // MÓDULO 12: NOTIFICACIONES
        // ========================================
        System.out.println("\n--- MÓDULO 12: NOTIFICACIONES ---");
        
        crearTabla("NOTIFICACIONES",
            "NOT_ID INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY, " +
            "EMP_ID INTEGER NOT NULL, " +
            "PED_ID INTEGER, " +
            "CLI_ID INTEGER, " +
            "NOT_TIPO VARCHAR(30) DEFAULT 'EMAIL', " +
            "NOT_DESTINATARIO VARCHAR(100) DEFAULT '', " +
            "NOT_ASUNTO VARCHAR(200) DEFAULT '', " +
            "NOT_MENSAJE VARCHAR(1000) DEFAULT '', " +
            "NOT_ESTADO VARCHAR(20) DEFAULT 'PENDIENTE', " +
            "NOT_FECHA_ENVIO TIMESTAMP, " +
            "NOT_FECHA_LECTURA TIMESTAMP"
        );

        // ========================================
        // MÓDULO 13: FACTURACIÓN
        // ========================================
        System.out.println("\n--- MÓDULO 13: FACTURACIÓN ---");
        
        crearTabla("FACTURAS_LM",
            "FAC_ID INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY, " +
            "EMP_ID INTEGER NOT NULL, " +
            "FAC_NUMERO VARCHAR(20) NOT NULL, " +
            "CLI_ID INTEGER NOT NULL, " +
            "FAC_FECHA DATE DEFAULT CURRENT_DATE, " +
            "FAC_SUBTOTAL DECIMAL(12,2) DEFAULT 0, " +
            "FAC_IVA DECIMAL(12,2) DEFAULT 0, " +
            "FAC_TOTAL DECIMAL(12,2) DEFAULT 0, " +
            "FAC_ESTADO VARCHAR(20) DEFAULT 'PENDIENTE', " +
            "FAC_FORMA_PAGO VARCHAR(20) DEFAULT 'CONTADO', " +
            "FAC_FECHA_PAGO DATE, " +
            "FAC_NOTAS VARCHAR(300) DEFAULT ''"
        );

        crearTabla("FACTURA_DETALLE",
            "FDE_ID INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY, " +
            "FAC_ID INTEGER NOT NULL, " +
            "PED_ID INTEGER, " +
            "FDE_CONCEPTO VARCHAR(100) DEFAULT '', " +
            "FDE_CANTIDAD INTEGER DEFAULT 1, " +
            "FDE_PRECIO_UNIT DECIMAL(10,2) DEFAULT 0, " +
            "FDE_SUBTOTAL DECIMAL(12,2) DEFAULT 0, " +
            "FDE_DESCUENTO DECIMAL(10,2) DEFAULT 0, " +
            "FDE_TOTAL DECIMAL(12,2) DEFAULT 0"
        );

        // ========================================
        // MÓDULO 14: KPIs / MÉTRICAS DIARIAS
        // ========================================
        System.out.println("\n--- MÓDULO 14: MÉTRICAS ---");
        
        crearTabla("KPI_DIARIO",
            "KPI_ID INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY, " +
            "EMP_ID INTEGER NOT NULL, " +
            "KPI_FECHA DATE DEFAULT CURRENT_DATE, " +
            "KPI_PEDIDOS_NUEVOS INTEGER DEFAULT 0, " +
            "KPI_PEDIDOS_ENTREGADOS INTEGER DEFAULT 0, " +
            "KPI_PEDIDOS_FALLIDOS INTEGER DEFAULT 0, " +
            "KPI_PEDIDOS_CANCELADOS INTEGER DEFAULT 0, " +
            "KPI_ENTREGAS_A_TIEMPO INTEGER DEFAULT 0, " +
            "KPI_ENTREGAS_TARDIAS INTEGER DEFAULT 0, " +
            "KPI_TIEMPO_PROMedio_MIN INTEGER DEFAULT 0, " +
            "KPI_KM_TOTAL DECIMAL(10,2) DEFAULT 0, " +
            "KPI_COSTO_TOTAL DECIMAL(12,2) DEFAULT 0, " +
            "KPI_INGRESO_TOTAL DECIMAL(12,2) DEFAULT 0, " +
            "KPI_UTILIDAD DECIMAL(12,2) DEFAULT 0, " +
            "KPI_CHOFERES_ACTIVOS INTEGER DEFAULT 0, " +
            "KPI_VEHICULOS_ACTIVOS INTEGER DEFAULT 0"
        );

        // ========================================
        // RESUMEN
        // ========================================
        System.out.println("\n========================================");
        System.out.println("TABLAS CREADAS: " + tablasCreadas);
        System.out.println("========================================");

        c.close();
        System.out.println("\n=== FIN FASE 1A - DISEÑO DE TABLAS ===");
    }

    static void crearTabla(String nombre, String columnas) {
        try {
            // Verificar si ya existe
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
