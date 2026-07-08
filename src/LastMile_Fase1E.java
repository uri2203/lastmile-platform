import java.sql.*;

/**
 * FASE 1E: Documentación completa del sistema Last Mile
 * Inventario total de tablas, columnas, registros y relaciones
 */
public class LastMile_Fase1E {

    static Connection c;
    static Statement s;
    static int totalTablas = 0;
    static long totalRegistros = 0;

    public static void main(String[] args) throws Exception {
        c = DriverManager.getConnection(
            "jdbc:as400://192.168.0.240;libraries=TESTLIB;errors=full", "AYUDATX", "MXTAC23");
        s = c.createStatement();

        System.out.println("========================================================");
        System.out.println("  DOCUMENTACION COMPLETA - SISTEMA LAST MILE");
        System.out.println("  Base de Datos: TESTLIB en AS/400 (192.168.0.240)");
        System.out.println("  Fecha: " + java.time.LocalDate.now());
        System.out.println("========================================================\n");

        // ========================================
        // INVENTARIO DE TABLAS
        // ========================================
        System.out.println("1. INVENTARIO DE TABLAS\n");
        System.out.printf("  %-35s %10s %15s%n", "TABLA", "REGISTROS", "CATEGORÍA");
        System.out.println("  " + "-".repeat(65));

        // First collect all table names
        java.util.List<String> tablaNames = new java.util.ArrayList<>();
        ResultSet rs = s.executeQuery(
            "SELECT TABLE_NAME FROM QSYS2.SYSTABLES WHERE TABLE_SCHEMA = 'TESTLIB' ORDER BY TABLE_NAME");
        while (rs.next()) {
            tablaNames.add(rs.getString("TABLE_NAME").trim());
        }
        rs.close();

        // Now count each table separately
        for (String tabla : tablaNames) {
            int count = 0;
            try {
                ResultSet rs2 = s.executeQuery("SELECT COUNT(*) FROM TESTLIB." + tabla);
                if (rs2.next()) count = rs2.getInt(1);
                rs2.close();
            } catch (Exception e) {}

            String categoria = getCategoria(tabla);
            totalTablas++;
            totalRegistros += count;
            System.out.printf("  %-35s %,10d %15s%n", tabla, count, categoria);
        }

        System.out.println("\n  " + "=".repeat(65));
        System.out.printf("  %-35s %,10d %15s%n", "TOTAL", totalRegistros, "");
        System.out.println("  " + "=".repeat(65));

        // ========================================
        // ESTRUCTURA DETALLADA POR MÓDULO
        // ========================================
        System.out.println("\n\n2. ESTRUCTURA DETALLADA POR MÓDULO\n");

        String[] modulos = {
            "MULTI-TENANT|EMPRESAS,USUARIOS",
            "CHOFERES|CHOFERES,VEHICULOS",
            "CLIENTES|CLIENTES_LM",
            "ZONAS|ZONAS",
            "TARIFAS|TARIFAS_LM",
            "PEDIDOS|PEDIDOS,PEDIDO_HISTORIAL",
            "RUTAS|RUTAS,RUTA_DETALLE",
            "ASIGNACIONES|ASIGNACIONES",
            "ENTREGAS|ENTREGAS",
            "INCIDENCIAS|INCIDENCIAS",
            "TRACKING|TRACKING",
            "NOTIFICACIONES|NOTIFICACIONES",
            "FACTURACIÓN|FACTURAS_LM,FACTURA_DETALLE",
            "KPIs|KPI_DIARIO",
            "PORTAL CLIENTE|CLIENTE_USUARIOS,CLIENTE_API_KEYS,CLIENTE_NOTIFICACIONES_CONFIG",
            "GAMIFICACIÓN|CHOFER_PUNTOS,CHOFER_INSIGNIAS,CHOFER_RANKING",
            "NOTIF. AVANZADAS|NOTIF_PLANTILLAS,NOTIF_ENVIOS",
            "LOGÍSTICA INVERSA|DEVOLUCIONES",
            "CONTROL FRAUDE|FRAUDE_ALERTAS,FRAUDE_UBICACIONES",
            "SLA|SLA_CONFIGURACION,SLA_RESULTADOS",
            "WHITELABEL|WHITELABEL_CONFIG",
            "FACTURACIÓN SaaS|SAAS_SUSCRIPCIONES,SAAS_FACTURACION",
            "AUDITORÍA|AUDIT_LOG",
            "RUTAS AUTO|RUTA_OPTIMIZADA,RUTA_OPTIMIZADA_DETALLE",
            "MÉTRICAS CLIENTE|CLIENTE_METRICAS",
            "MANTENIMIENTO (EDGAR)|UNIDADESTA,UNIDADES,FLOTILLA,OTSXMARCA,OTSXMARCA2,OTSXMARCA3,OTSXMARCA4,OTSXMARCA5,OTSXMARCA6,OTSXMARCA7",
            "OTS VEHÍCULOS (EDGAR)|OTSXVEHIC,OTSXVEHIC1,OTSXVEHIC2,OTSXVEHIC3,OTSXVEHIC4,OTSXVEHIC5,OTSXVEHIC6,OTSXVEHIC7",
            "REFACCIONES (EDGAR)|REFACTALLE",
            "GASTOS (EDGAR)|GASTOSELEC,GASTOSPROM,MOVCAJA",
            "LLANTAS (EDGAR)|OTLLANTAS,OTLLANTASC",
            "TARIFAS (EDGAR)|TARIFAS,TARIFASPRO"
        };

        for (String modulo : modulos) {
            String[] parts = modulo.split("\\|");
            String nombre = parts[0];
            String tablasStr = parts[1];
            String[] tablas = tablasStr.split(",");

            System.out.println("  MÓDULO: " + nombre);
            for (String tabla : tablas) {
                tabla = tabla.trim();
                try {
                    ResultSet rsCol = s.executeQuery(
                        "SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH, NUMERIC_PRECISION, NUMERIC_SCALE " +
                        "FROM QSYS2.SYSCOLUMNS WHERE TABLE_SCHEMA = 'TESTLIB' AND TABLE_NAME = '" + tabla + "' ORDER BY ORDINAL_POSITION");

                    System.out.println("    " + tabla + ":");
                    while (rsCol.next()) {
                        String col = rsCol.getString("COLUMN_NAME").trim();
                        String type = rsCol.getString("DATA_TYPE").trim();
                        String charLen = rsCol.getString("CHARACTER_MAXIMUM_LENGTH");
                        String numPrec = rsCol.getString("NUMERIC_PRECISION");
                        String numScale = rsCol.getString("NUMERIC_SCALE");

                        String tipo = type;
                        if (type.equals("CHARACTER") || type.equals("VARCHAR")) {
                            tipo = type + "(" + (charLen != null ? charLen : "?") + ")";
                        } else if (type.equals("DECIMAL") || type.equals("NUMERIC")) {
                            tipo = type + "(" + (numPrec != null ? numPrec : "?") + "," + (numScale != null ? numScale : "0") + ")";
                        }

                        System.out.println("      " + col + " | " + tipo);
                    }
                    rsCol.close();
                } catch (Exception e) {
                    System.out.println("    " + tabla + " (error)");
                }
            }
            System.out.println();
        }

        // ========================================
        // RELACIONES ENTRE TABLAS
        // ========================================
        System.out.println("\n3. RELACIONES ENTRE TABLAS\n");

        String[] relaciones = {
            "EMPRESAS.EMP_ID → USUARIOS.EMP_ID",
            "EMPRESAS.EMP_ID → CHOFERES.EMP_ID",
            "EMPRESAS.EMP_ID → VEHICULOS.EMP_ID",
            "EMPRESAS.EMP_ID → CLIENTES_LM.EMP_ID",
            "EMPRESAS.EMP_ID → ZONAS.EMP_ID",
            "EMPRESAS.EMP_ID → TARIFAS_LM.EMP_ID",
            "EMPRESAS.EMP_ID → PEDIDOS.EMP_ID",
            "CLIENTES_LM.CLI_ID → PEDIDOS.CLI_ID",
            "PEDIDOS.PED_ID → PEDIDO_HISTORIAL.PED_ID",
            "PEDIDOS.PED_ID → ASIGNACIONES.PED_ID",
            "PEDIDOS.PED_ID → ENTREGAS.PED_ID",
            "PEDIDOS.PED_ID → INCIDENCIAS.PED_ID",
            "PEDIDOS.PED_ID → DEVOLUCIONES.PED_ID",
            "CHOFERES.CHO_ID → ASIGNACIONES.CHO_ID",
            "CHOFERES.CHO_ID → ENTREGAS.CHO_ID",
            "CHOFERES.CHO_ID → TRACKING.CHO_ID",
            "CHOFERES.CHO_ID → RUTAS.CHO_ID",
            "VEHICULOS.VEH_ID → ASIGNACIONES.VEH_ID",
            "VEHICULOS.VEH_ID → RUTAS.VEH_ID",
            "RUTAS.RUT_ID → RUTA_DETALLE.RUT_ID",
            "RUTA_DETALLE.PED_ID → PEDIDOS.PED_ID",
            "PEDIDOS.PED_ID → FACTURA_DETALLE.PED_ID",
            "FACTURAS_LM.FAC_ID → FACTURA_DETALLE.FAC_ID",
            "CLIENTES_LM.CLI_ID → CLIENTE_USUARIOS.CLI_ID",
            "CLIENTES_LM.CLI_ID → CLIENTE_API_KEYS.CLI_ID",
            "CLIENTES_LM.CLI_ID → CLIENTE_METRICAS.CLI_ID",
            "CHOFERES.CHO_ID → CHOFER_PUNTOS.CHO_ID",
            "CHOFERES.CHO_ID → CHOFER_INSIGNIAS.CHO_ID",
            "CHOFERES.CHO_ID → CHOFER_RANKING.CHO_ID",
            "CHOFERES.CHO_ID → FRAUDE_ALERTAS.CHO_ID",
            "SAAS_SUSCRIPCIONES.SUS_ID → SAAS_FACTURACION.SUS_ID",
            "SLA_CONFIGURACION.SLA_ID → SLA_RESULTADOS.SLA_ID",
            "RUTA_OPTIMIZADA.ROP_ID → RUTA_OPTIMIZADA_DETALLE.ROP_ID"
        };

        for (String rel : relaciones) {
            System.out.println("  " + rel);
        }

        // ========================================
        // RESUMEN EJECUTIVO
        // ========================================
        System.out.println("\n\n4. RESUMEN EJECUTIVO\n");
        System.out.println("  ┌─────────────────────────────────────────────────────┐");
        System.out.println("  │         SISTEMA LAST MILE - RESUMEN                 │");
        System.out.println("  ├─────────────────────────────────────────────────────┤");
        System.out.printf("  │  Total de tablas:           %-25s │%n", String.valueOf(totalTablas));
        System.out.printf("  │  Total de registros:        %-25s │%n", String.format("%,d", totalRegistros));
        System.out.println("  │  Módulos del sistema:       25                       │");
        System.out.println("  │  Relaciones documentadas:   " + relaciones.length + "                       │");
        System.out.println("  │  Multi-tenant:              SÍ (3 empresas)         │");
        System.out.println("  │  Base de datos:             DB2/400 (AS/400)        │");
        System.out.println("  │  Entorno:                   TESTLIB (pruebas)       │");
        System.out.println("  └─────────────────────────────────────────────────────┘");

        System.out.println("\n\n5. MÓDULOS PARA DESARROLLO WEB\n");
        System.out.println("  ┌──────────────────┬─────────────────────────────────────┐");
        System.out.println("  │ PANEL            │ MÓDULOS                             │");
        System.out.println("  ├──────────────────┼─────────────────────────────────────┤");
        System.out.println("  │ OPERACIÓN        │ Pedidos, Rutas, Asignaciones,       │");
        System.out.println("  │                  │ Tracking, Entregas, Incidencias     │");
        System.out.println("  ├──────────────────┼─────────────────────────────────────┤");
        System.out.println("  │ ADMIN            │ KPIs, Facturación, SLA, Gamificación│");
        System.out.println("  │                  │ Auditoría, Whitelabel, SaaS         │");
        System.out.println("  ├──────────────────┼─────────────────────────────────────┤");
        System.out.println("  │ CHOFER           │ Mis pedidos, Tracking, Entregas,    │");
        System.out.println("  │ (App Móvil)      │ Incidencias, Ranking, Notificaciones│");
        System.out.println("  ├──────────────────┼─────────────────────────────────────┤");
        System.out.println("  │ CLIENTE          │ Mis envíos, Tracking, Costos,       │");
        System.out.println("  │ (Portal Web)     │ Reportes, Métricas, API             │");
        System.out.println("  └──────────────────┴─────────────────────────────────────┘");

        c.close();
        System.out.println("\n=== FIN DOCUMENTACIÓN ===");
    }

    static String getCategoria(String tabla) {
        if (tabla.startsWith("EMPRESAS") || tabla.startsWith("USUARIOS")) return "Multi-Tenant";
        if (tabla.startsWith("CHOFER") || tabla.startsWith("VEHICULOS")) return "Flotilla";
        if (tabla.startsWith("CLIENTES")) return "Clientes";
        if (tabla.startsWith("PEDIDOS") || tabla.startsWith("ASIGNACIONES")) return "Pedidos";
        if (tabla.startsWith("RUTAS") || tabla.startsWith("RUTA")) return "Rutas";
        if (tabla.startsWith("ENTREGAS")) return "Entregas";
        if (tabla.startsWith("INCIDENCIAS")) return "Incidencias";
        if (tabla.startsWith("TRACKING")) return "Tracking";
        if (tabla.startsWith("NOTIF")) return "Notificaciones";
        if (tabla.startsWith("FACTURAS") || tabla.startsWith("FACTURA")) return "Facturación";
        if (tabla.startsWith("KPI")) return "KPIs";
        if (tabla.startsWith("DEVOLUCIONES")) return "Log. Inversa";
        if (tabla.startsWith("FRAUDE")) return "Fraude";
        if (tabla.startsWith("SLA")) return "SLA";
        if (tabla.startsWith("WHL") || tabla.startsWith("WHITELABEL")) return "Whitelabel";
        if (tabla.startsWith("SAAS")) return "SaaS";
        if (tabla.startsWith("AUDIT")) return "Auditoría";
        if (tabla.startsWith("ZONAS")) return "Zonas";
        if (tabla.startsWith("TARIFAS")) return "Tarifas";
        if (tabla.startsWith("OT") || tabla.startsWith("UNIDAD") || tabla.startsWith("FLOTILLA")) return "Mantto(EDGAR)";
        if (tabla.startsWith("REF") || tabla.startsWith("REP")) return "Refacciones(EDGAR)";
        if (tabla.startsWith("CAJ") || tabla.startsWith("GAS") || tabla.startsWith("MOV")) return "Gastos(EDGAR)";
        if (tabla.startsWith("TOT")) return "Totales(EDGAR)";
        if (tabla.startsWith("MO")) return "Movimientos(EDGAR)";
        if (tabla.startsWith("USR") || tabla.startsWith("OBJ")) return "Sistema(EDGAR)";
        return "Otro";
    }
}
