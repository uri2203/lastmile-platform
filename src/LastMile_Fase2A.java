import java.sql.*;

/**
 * FASE 2A: Procedimientos almacenados y vistas SQL en AS/400
 * Lógica de negocio en la base de datos
 */
public class LastMile_Fase2A {

    static Connection c;
    static Statement s;
    static int objetos = 0;

    public static void main(String[] args) throws Exception {
        c = DriverManager.getConnection(
            "jdbc:as400://192.168.0.240;errors=full", "AYUDATX", "MXTAC23");
        s = c.createStatement();

        System.out.println("=== FASE 2A: VISTAS Y PROCEDIMIENTOS SQL ===\n");

        // ========================================
        // VISTAS PARA REPORTES
        // ========================================
        System.out.println("--- VISTAS ---");

        // Vista 1: Dashboard resumen por empresa
        crearVista("V_DASHBOARD_RESUMEN",
            "SELECT E.EMP_ID, E.EMP_NOMBRE, " +
            "(SELECT COUNT(*) FROM TESTLIB.PEDIDOS P WHERE P.EMP_ID = E.EMP_ID) AS TOTAL_PEDIDOS, " +
            "(SELECT COUNT(*) FROM TESTLIB.PEDIDOS P2 WHERE P2.EMP_ID = E.EMP_ID AND P2.PED_ESTADO = 'PENDIENTE') AS PENDIENTES, " +
            "(SELECT COUNT(*) FROM TESTLIB.PEDIDOS P3 WHERE P3.EMP_ID = E.EMP_ID AND P3.PED_ESTADO = 'EN_RUTA') AS EN_RUTA, " +
            "(SELECT COUNT(*) FROM TESTLIB.PEDIDOS P4 WHERE P4.EMP_ID = E.EMP_ID AND P4.PED_ESTADO = 'ENTREGADO') AS ENTREGADOS, " +
            "(SELECT COUNT(*) FROM TESTLIB.PEDIDOS P5 WHERE P5.EMP_ID = E.EMP_ID AND P5.PED_ESTADO = 'FALLIDO') AS FALLIDOS, " +
            "(SELECT COUNT(*) FROM TESTLIB.CHOFERES CH WHERE CH.EMP_ID = E.EMP_ID AND CH.CHO_ESTATUS = 'ACTIVO') AS CHOFERES_ACTIVOS, " +
            "(SELECT COUNT(*) FROM TESTLIB.VEHICULOS V WHERE V.EMP_ID = E.EMP_ID AND V.VEH_ESTATUS = 'ACTIVO') AS VEHICULOS_ACTIVOS, " +
            "(SELECT COALESCE(SUM(P6.PED_COSTO_TOTAL),0) FROM TESTLIB.PEDIDOS P6 WHERE P6.EMP_ID = E.EMP_ID AND P6.PED_ESTADO = 'ENTREGADO') AS INGRESO_TOTAL " +
            "FROM TESTLIB.EMPRESAS E");

        // Vista 2: Pedidos con info completa
        crearVista("V_PEDIDOS_COMPLETO",
            "SELECT P.PED_ID, P.EMP_ID, P.PED_NUMERO, " +
            "P.PED_CLIENTE_NOMBRE, P.PED_CLIENTE_TELEFONO, " +
            "P.PED_DESTINO_DIR, P.PED_DESTINO_COL, P.PED_DESTINO_CIUDAD, " +
            "P.PED_PESO_KG, P.PED_BULTOS, P.PED_COSTO_TOTAL, " +
            "P.PED_ESTADO, P.PED_PRIORIDAD, P.PED_FECHA_PEDIDO, " +
            "P.PED_FECHA_ENTREGA_REAL, " +
            "CH.CHO_NOMBRE || ' ' || CH.CHO_APELLIDO AS CHOFER_ASIGNADO, " +
            "V.VEH_UNIDAD AS UNIDAD_ASIGNADA, " +
            "CL.CLI_RAZON_SOCIAL AS CLIENTE_RAZON_SOCIAL " +
            "FROM TESTLIB.PEDIDOS P " +
            "LEFT JOIN TESTLIB.ASIGNACIONES A ON P.PED_ID = A.PED_ID AND P.EMP_ID = A.EMP_ID " +
            "LEFT JOIN TESTLIB.CHOFERES CH ON A.CHO_ID = CH.CHO_ID AND A.EMP_ID = CH.EMP_ID " +
            "LEFT JOIN TESTLIB.VEHICULOS V ON A.VEH_ID = V.VEH_ID AND A.EMP_ID = V.EMP_ID " +
            "LEFT JOIN TESTLIB.CLIENTES_LM CL ON P.CLI_ID = CL.CLI_ID AND P.EMP_ID = CL.EMP_ID");

        // Vista 3: Rendimiento choferes
        crearVista("V_RENDIMIENTO_CHOFERES",
            "SELECT CH.CHO_ID, CH.EMP_ID, CH.CHO_NOMBRE, CH.CHO_APELLIDO, " +
            "COUNT(E.ENT_ID) AS TOTAL_ENTREGAS, " +
            "SUM(CASE WHEN E.ENT_ESTADO = 'ENTREGADO' THEN 1 ELSE 0 END) AS ENTREGAS_EXITOSAS, " +
            "SUM(CASE WHEN E.ENT_ESTADO = 'NO_ENTREGADO' THEN 1 ELSE 0 END) AS ENTREGAS_FALLIDAS, " +
            "CASE WHEN COUNT(E.ENT_ID) > 0 " +
            "  THEN ROUND(SUM(CASE WHEN E.ENT_ESTADO = 'ENTREGADO' THEN 1.0 ELSE 0 END) * 100.0 / COUNT(E.ENT_ID), 1) " +
            "  ELSE 0 END AS TASA_EXITO, " +
            "ROUND(AVG(E.ENT_TIEMPO_ESPERA_MIN), 1) AS TIEMPO_PROM_ESPERA " +
            "FROM TESTLIB.CHOFERES CH " +
            "LEFT JOIN TESTLIB.ENTREGAS E ON CH.CHO_ID = E.CHO_ID AND CH.EMP_ID = E.EMP_ID " +
            "GROUP BY CH.CHO_ID, CH.EMP_ID, CH.CHO_NOMBRE, CH.CHO_APELLIDO");

        // Vista 4: Costos por ruta
        crearVista("V_COSTOS_RUTA",
            "SELECT R.RUT_ID, R.EMP_ID, R.RUT_NOMBRE, R.RUT_FECHA, " +
            "CH.CHO_NOMBRE || ' ' || CH.CHO_APELLIDO AS CHOFER, " +
            "V.VEH_UNIDAD, " +
            "R.RUT_TOTAL_PEDIDOS, R.RUT_TOTAL_ENTREGAS, " +
            "R.RUT_TOTAL_KM, R.RUT_TOTAL_TIEMPO_MIN, R.RUT_COSTO_TOTAL, " +
            "CASE WHEN R.RUT_TOTAL_ENTREGAS > 0 " +
            "  THEN ROUND(R.RUT_COSTO_TOTAL / R.RUT_TOTAL_ENTREGAS, 2) ELSE 0 END AS COSTO_PROM_ENTREGA, " +
            "CASE WHEN R.RUT_TOTAL_KM > 0 " +
            "  THEN ROUND(R.RUT_COSTO_TOTAL / R.RUT_TOTAL_KM, 2) ELSE 0 END AS COSTO_PROM_KM " +
            "FROM TESTLIB.RUTAS R " +
            "LEFT JOIN TESTLIB.CHOFERES CH ON R.CHO_ID = CH.CHO_ID AND R.EMP_ID = CH.EMP_ID " +
            "LEFT JOIN TESTLIB.VEHICULOS V ON R.VEH_ID = V.VEH_ID AND R.EMP_ID = V.EMP_ID");

        // Vista 5: KPIs consolidados por empresa
        crearVista("V_KPI_CONSOLIDADO",
            "SELECT K.EMP_ID, " +
            "SUM(K.KPI_PEDIDOS_NUEVOS) AS TOTAL_NUEVOS, " +
            "SUM(K.KPI_PEDIDOS_ENTREGADOS) AS TOTAL_ENTREGADOS, " +
            "SUM(K.KPI_PEDIDOS_FALLIDOS) AS TOTAL_FALLIDOS, " +
            "SUM(K.KPI_PEDIDOS_CANCELADOS) AS TOTAL_CANCELADOS, " +
            "SUM(K.KPI_ENTREGAS_A_TIEMPO) AS TOTAL_A_TIEMPO, " +
            "SUM(K.KPI_ENTREGAS_TARDIAS) AS TOTAL_TARDIAS, " +
            "ROUND(AVG(K.KPI_TIEMPO_PROMedio_MIN), 1) AS TIEMPO_PROM_General, " +
            "ROUND(SUM(K.KPI_KM_TOTAL), 2) AS KM_TOTAL, " +
            "ROUND(SUM(K.KPI_COSTO_TOTAL), 2) AS COSTO_TOTAL, " +
            "ROUND(SUM(K.KPI_INGRESO_TOTAL), 2) AS INGRESO_TOTAL, " +
            "ROUND(SUM(K.KPI_UTILIDAD), 2) AS UTILIDAD_TOTAL, " +
            "ROUND(AVG(K.KPI_CHOFERES_ACTIVOS), 0) AS PROM_CHOFERES, " +
            "ROUND(AVG(K.KPI_VEHICULOS_ACTIVOS), 0) AS PROM_VEHICULOS " +
            "FROM TESTLIB.KPI_DIARIO K " +
            "GROUP BY K.EMP_ID");

        // Vista 6: Incidencias por tipo
        crearVista("V_INCIDENCIAS_RESUMEN",
            "SELECT I.EMP_ID, I.INC_TIPO, " +
            "COUNT(*) AS CANTIDAD, " +
            "SUM(CASE WHEN I.INC_ESTADO = 'ABIERTA' THEN 1 ELSE 0 END) AS ABIERTAS, " +
            "SUM(CASE WHEN I.INC_ESTADO = 'RESUELTA' THEN 1 ELSE 0 END) AS RESUELTAS " +
            "FROM TESTLIB.INCIDENCIAS I " +
            "GROUP BY I.EMP_ID, I.INC_TIPO");

        // Vista 7: Top clientes por empresa
        crearVista("V_TOP_CLIENTES",
            "SELECT CL.EMP_ID, CL.CLI_ID, CL.CLI_RAZON_SOCIAL, CL.CLI_COLONIA, " +
            "COUNT(P.PED_ID) AS TOTAL_PEDIDOS, " +
            "SUM(P.PED_COSTO_TOTAL) AS TOTAL_GASTADO, " +
            "SUM(P.PED_BULTOS) AS TOTAL_BULTOS, " +
            "ROUND(AVG(P.PED_COSTO_TOTAL), 2) AS PROMedio_PEDIDO " +
            "FROM TESTLIB.CLIENTES_LM CL " +
            "JOIN TESTLIB.PEDIDOS P ON CL.CLI_ID = P.CLI_ID AND CL.EMP_ID = P.EMP_ID " +
            "GROUP BY CL.EMP_ID, CL.CLI_ID, CL.CLI_RAZON_SOCIAL, CL.CLI_COLONIA");

        // Vista 8: Estado de flota
        crearVista("V_ESTADO_FLOTA",
            "SELECT V.EMP_ID, V.VEH_ID, V.VEH_UNIDAD, V.VEH_MARCA, V.VEH_MODELO, " +
            "CH.CHO_NOMBRE || ' ' || CH.CHO_APELLIDO AS CHOFER_ASIGNADO, " +
            "V.VEH_ESTATUS, " +
            "(SELECT COUNT(*) FROM TESTLIB.TRACKING T WHERE T.VEH_ID = V.VEH_ID AND T.EMP_ID = V.EMP_ID) AS REGISTROS_GPS, " +
            "(SELECT T2.TRK_VELOCIDAD FROM TESTLIB.TRACKING T2 WHERE T2.VEH_ID = V.VEH_ID AND T2.EMP_ID = V.EMP_ID ORDER BY T2.TRK_FECHA DESC FETCH FIRST 1 ROW ONLY) AS ULTIMA_VELOCIDAD " +
            "FROM TESTLIB.VEHICULOS V " +
            "LEFT JOIN TESTLIB.CHOFERES CH ON V.EMP_ID = CH.EMP_ID AND CH.CHO_ESTATUS = 'ACTIVO' " +
            "LEFT JOIN TESTLIB.ASIGNACIONES A ON V.VEH_ID = A.VEH_ID AND V.EMP_ID = A.EMP_ID AND A.ASI_ESTADO = 'ASIGNADO'");

        // ========================================
        // PROCEDIMIENTOS ALMACENADOS
        // ========================================
        System.out.println("\n--- PROCEDIMIENTOS ALMACENADOS ---");

        // SP 1: Obtener pedidos por empresa y estado
        crearProcedimiento("SP_PEDIDOS_POR_ESTADO",
            "CREATE PROCEDURE TESTLIB.SP_PEDIDOS_POR_ESTADO(" +
            "IN P_EMP_ID INTEGER, IN P_ESTADO VARCHAR(20)) " +
            "RESULT SETS 1 " +
            "LANGUAGE SQL " +
            "BEGIN " +
            "DECLARE C1 CURSOR WITH RETURN FOR " +
            "SELECT PED_ID, PED_NUMERO, PED_CLIENTE_NOMBRE, PED_DESTINO_DIR, " +
            "PED_DESTINO_COL, PED_COSTO_TOTAL, PED_PRIORIDAD, PED_FECHA_PEDIDO " +
            "FROM TESTLIB.PEDIDOS " +
            "WHERE EMP_ID = P_EMP_ID AND PED_ESTADO = P_ESTADO " +
            "ORDER BY PED_FECHA_PEDIDO DESC; " +
            "OPEN C1; " +
            "END");

        // SP 2: Resumen diario de un chofer
        crearProcedimiento("SP_RESUMEN_CHOFER",
            "CREATE PROCEDURE TESTLIB.SP_RESUMEN_CHOFER(" +
            "IN P_CHO_ID INTEGER, IN P_FECHA DATE) " +
            "RESULT SETS 1 " +
            "LANGUAGE SQL " +
            "BEGIN " +
            "DECLARE C1 CURSOR WITH RETURN FOR " +
            "SELECT E.ENT_ID, P.PED_NUMERO, P.PED_CLIENTE_NOMBRE, P.PED_DESTINO_DIR, " +
            "E.ENT_ESTADO, E.ENT_RECEPTOR_NOMBRE, E.ENT_FECHA_ENTREGA, E.ENT_TIEMPO_ESPERA_MIN " +
            "FROM TESTLIB.ENTREGAS E " +
            "JOIN TESTLIB.PEDIDOS P ON E.PED_ID = P.PED_ID " +
            "WHERE E.CHO_ID = P_CHO_ID " +
            "AND DATE(E.ENT_FECHA_LLEGADA) = P_FECHA " +
            "ORDER BY E.ENT_FECHA_LLEGADA; " +
            "OPEN C1; " +
            "END");

        // SP 3: Calcular costo de entrega
        crearProcedimiento("SP_CALCULAR_COSTO",
            "CREATE PROCEDURE TESTLIB.SP_CALCULAR_COSTO(" +
            "IN P_EMP_ID INTEGER, IN P_PESO_KG DECIMAL(8,2), " +
            "IN P_DISTANCIA_KM DECIMAL(8,2), IN P_TIPO_ENVIO VARCHAR(20)) " +
            "RESULT SETS 1 " +
            "LANGUAGE SQL " +
            "BEGIN " +
            "DECLARE C1 CURSOR WITH RETURN FOR " +
            "SELECT TAR_NOMBRE, " +
            "TAR_MONTO_BASE + (P_DISTANCIA_KM * TAR_MONTO_KM) + (P_PESO_KG * TAR_MONTO_KG) AS COSTO_TOTAL " +
            "FROM TESTLIB.TARIFAS_LM " +
            "WHERE EMP_ID = P_EMP_ID AND TAR_ESTATUS = 'ACTIVO' " +
            "AND TAR_TIPO = CASE WHEN P_TIPO_ENVIO = 'PESADA' THEN 'POR_KG' ELSE 'POR_ENTREGA' END " +
            "ORDER BY COSTO_TOTAL ASC " +
            "FETCH FIRST 1 ROW ONLY; " +
            "OPEN C1; " +
            "END");

        // SP 4: Dashboard del cliente
        crearProcedimiento("SP_DASHBOARD_CLIENTE",
            "CREATE PROCEDURE TESTLIB.SP_DASHBOARD_CLIENTE(" +
            "IN P_EMP_ID INTEGER, IN P_CLI_ID INTEGER) " +
            "RESULT SETS 1 " +
            "LANGUAGE SQL " +
            "BEGIN " +
            "DECLARE C1 CURSOR WITH RETURN FOR " +
            "SELECT " +
            "COUNT(*) AS TOTAL_ENVIOS, " +
            "SUM(CASE WHEN PED_ESTADO = 'ENTREGADO' THEN 1 ELSE 0 END) AS ENTREGADOS, " +
            "SUM(CASE WHEN PED_ESTADO = 'FALLIDO' THEN 1 ELSE 0 END) AS FALLIDOS, " +
            "SUM(CASE WHEN PED_ESTADO IN ('PENDIENTE','ASIGNADO','EN_RUTA') THEN 1 ELSE 0 END) AS EN_PROCESO, " +
            "SUM(CASE WHEN PED_ESTADO = 'ENTREGADO' THEN PED_COSTO_TOTAL ELSE 0 END) AS TOTAL_GASTADO, " +
            "ROUND(AVG(CASE WHEN PED_ESTADO = 'ENTREGADO' THEN PED_COSTO_TOTAL END), 2) AS PROMedio_GASTO, " +
            "SUM(PED_BULTOS) AS TOTAL_BULTOS " +
            "FROM TESTLIB.PEDIDOS " +
            "WHERE EMP_ID = P_EMP_ID AND CLI_ID = P_CLI_ID; " +
            "OPEN C1; " +
            "END");

        // ========================================
        // RESUMEN
        // ========================================
        System.out.println("\n========================================");
        System.out.println("OBJETOS SQL CREADOS: " + objetos);
        System.out.println("========================================");

        c.close();
        System.out.println("\n=== FIN FASE 2A ===");
    }

    static void crearVista(String nombre, String sql) {
        try {
            // Eliminar si existe
            try { s.executeUpdate("DROP VIEW TESTLIB." + nombre); } catch (Exception e) {}
            s.executeUpdate("CREATE VIEW TESTLIB." + nombre + " AS " + sql);
            objetos++;
            System.out.println("  OK " + nombre);
        } catch (Exception e) {
            String msg = e.getMessage();
            if (msg != null) msg = msg.split("\n")[0];
            System.out.println("  ERROR " + nombre + ": " + msg);
        }
    }

    static void crearProcedimiento(String nombre, String sql) {
        try {
            // Eliminar si existe
            try { s.executeUpdate("DROP PROCEDURE TESTLIB." + nombre); } catch (Exception e) {}
            s.executeUpdate(sql);
            objetos++;
            System.out.println("  OK " + nombre);
        } catch (Exception e) {
            String msg = e.getMessage();
            if (msg != null) msg = msg.split("\n")[0];
            System.out.println("  ERROR " + nombre + ": " + msg);
        }
    }
}
