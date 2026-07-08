import java.sql.*;

/**
 * Exploración profunda del sistema LAST MILE / DELIVERY en EDGAR
 */
public class ExplorarLastMile {
    public static void main(String[] args) throws Exception {
        Connection c = DriverManager.getConnection(
            "jdbc:as400://192.168.0.240;libraries=EDGAR;errors=full", "AYUDATX", "MXTAC23");
        Statement s = c.createStatement();
        ResultSet rs;

        System.out.println("=== SISTEMA LAST MILE / DELIVERY - EXPLORACION COMPLETA ===\n");

        // 1. Todas las tablas que contienen "LM", "LAST", "DELIV", "ENTREG", "REPARTO", "RUTA", "PEDIDO"
        System.out.println("--- 1. TABLAS RELACIONADAS CON LAST MILE ---");
        rs = s.executeQuery(
            "SELECT TABLE_NAME, TABLE_TYPE FROM QSYS2.SYSTABLES " +
            "WHERE TABLE_SCHEMA = 'EDGAR' " +
            "AND (TABLE_NAME LIKE '%LM%' OR TABLE_NAME LIKE '%LAST%' OR TABLE_NAME LIKE '%DELIV%' " +
            "OR TABLE_NAME LIKE '%ENTREG%' OR TABLE_NAME LIKE '%REPARTO%' OR TABLE_NAME LIKE '%RUTA%' " +
            "OR TABLE_NAME LIKE '%PEDIDO%' OR TABLE_NAME LIKE '%CLIENTE%' OR TABLE_NAME LIKE '%CLIENT%' " +
            "OR TABLE_NAME LIKE '%VENTA%' OR TABLE_NAME LIKE '%DISTRIB%' OR TABLE_NAME LIKE '%LOGIST%' " +
            "OR TABLE_NAME LIKE '%UNIDAD%' OR TABLE_NAME LIKE '%VEHIC%' OR TABLE_NAME LIKE '%CHOFER%' " +
            "OR TABLE_NAME LIKE '%CONDUCT%' OR TABLE_NAME LIKE '%CONDUCT%' " +
            "OR TABLE_NAME LIKE '%CAJA%' OR TABLE_NAME LIKE '%GASolina%' OR TABLE_NAME LIKE '%FUEL%' " +
            "OR TABLE_NAME LIKE '%GPS%' OR TABLE_NAME LIKE '%SEGUIM%' OR TABLE_NAME LIKE '%TRACK%') " +
            "ORDER BY TABLE_NAME");
        while(rs.next()) {
            String t = rs.getString("TABLE_NAME").trim();
            String ty = rs.getString("TABLE_TYPE") != null ? rs.getString("TABLE_TYPE").trim() : "?";
            System.out.println("  " + t + " [" + ty + "]");
        }
        rs.close();

        // 2. Todas las tablas que contienen "OT" (Ordenes de Trabajo / Entrega)
        System.out.println("\n--- 2. TABLAS CON OT (ORDENES/ENTREGAS) ---");
        rs = s.executeQuery(
            "SELECT TABLE_NAME FROM QSYS2.SYSTABLES " +
            "WHERE TABLE_SCHEMA = 'EDGAR' " +
            "AND (TABLE_NAME LIKE 'OT%' OR TABLE_NAME LIKE '%_OT' OR TABLE_NAME LIKE '%_OTS') " +
            "ORDER BY TABLE_NAME");
        while(rs.next()) System.out.println("  " + rs.getString("TABLE_NAME").trim());
        rs.close();

        // 3. Estructura de UNIDADESTA (unidades Last Mile)
        System.out.println("\n--- 3. ESTRUCTURA UNIDADESTA ---");
        rs = s.executeQuery("SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH FROM QSYS2.SYSCOLUMNS WHERE TABLE_SCHEMA = 'EDGAR' AND TABLE_NAME = 'UNIDADESTA' ORDER BY ORDINAL_POSITION");
        while(rs.next()) System.out.println("  " + rs.getString("COLUMN_NAME").trim() + " | " + rs.getString("DATA_TYPE").trim() + " | " + rs.getString("CHARACTER_MAXIMUM_LENGTH"));
        rs.close();

        // 4. Estructura de OTSXMARCA (ordenes de trabajo)
        System.out.println("\n--- 4. ESTRUCTURA OTSXMARCA ---");
        rs = s.executeQuery("SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH FROM QSYS2.SYSCOLUMNS WHERE TABLE_SCHEMA = 'EDGAR' AND TABLE_NAME = 'OTSXMARCA' ORDER BY ORDINAL_POSITION");
        while(rs.next()) System.out.println("  " + rs.getString("COLUMN_NAME").trim() + " | " + rs.getString("DATA_TYPE").trim() + " | " + rs.getString("CHARACTER_MAXIMUM_LENGTH"));
        rs.close();

        // 5. Estructura de OTSXMARCA2
        System.out.println("\n--- 5. ESTRUCTURA OTSXMARCA2 ---");
        rs = s.executeQuery("SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH FROM QSYS2.SYSCOLUMNS WHERE TABLE_SCHEMA = 'EDGAR' AND TABLE_NAME = 'OTSXMARCA2' ORDER BY ORDINAL_POSITION");
        while(rs.next()) System.out.println("  " + rs.getString("COLUMN_NAME").trim() + " | " + rs.getString("DATA_TYPE").trim() + " | " + rs.getString("CHARACTER_MAXIMUM_LENGTH"));
        rs.close();

        // 6. Datos de ejemplo OTSXMARCA2 - Last Mile
        System.out.println("\n--- 6. EJEMPLO OTSXMARCA2 (LAST MILE - W*) ---");
        rs = s.executeQuery(
            "SELECT * " +
            "FROM EDGAR.OTSXMARCA2 WHERE OTUNLM LIKE 'W%' ORDER BY CCTOTA01 DESC FETCH FIRST 10 ROWS ONLY");
        ResultSetMetaData meta = rs.getMetaData();
        System.out.print("  ");
        for(int i = 1; i <= meta.getColumnCount(); i++) System.out.print(meta.getColumnName(i).trim() + " | ");
        System.out.println();
        while(rs.next()) {
            System.out.print("  ");
            for(int i = 1; i <= meta.getColumnCount(); i++) {
                String v = rs.getString(i);
                System.out.print((v != null ? v.trim() : "NULL") + " | ");
            }
            System.out.println();
        }
        rs.close();

        // 7. Tabla de RUTAS si existe
        System.out.println("\n--- 7. TABLAS DE RUTAS/ITINERARIOS ---");
        rs = s.executeQuery(
            "SELECT TABLE_NAME FROM QSYS2.SYSTABLES " +
            "WHERE TABLE_SCHEMA = 'EDGAR' " +
            "AND (TABLE_NAME LIKE '%RUTA%' OR TABLE_NAME LIKE '%ROUTE%' OR TABLE_NAME LIKE '%ITINER%' " +
            "OR TABLE_NAME LIKE '%ZONA%' OR TABLE_NAME LIKE '%SECTOR%' OR TABLE_NAME LIKE '%REPARTO%' " +
            "OR TABLE_NAME LIKE '%DISTRIB%' OR TABLE_NAME LIKE '%ENTREG%') " +
            "ORDER BY TABLE_NAME");
        while(rs.next()) System.out.println("  " + rs.getString("TABLE_NAME").trim());
        rs.close();

        // 8. Tablas de CLIENTES/DESTINOS
        System.out.println("\n--- 8. TABLAS DE CLIENTES/DESTINOS ---");
        rs = s.executeQuery(
            "SELECT TABLE_NAME FROM QSYS2.SYSTABLES " +
            "WHERE TABLE_SCHEMA = 'EDGAR' " +
            "AND (TABLE_NAME LIKE '%CLIENT%' OR TABLE_NAME LIKE '%DESTINO%' OR TABLE_NAME LIKE '%CONSIGN%' " +
            "OR TABLE_NAME LIKE '%RECEPTOR%' OR TABLE_NAME LIKE '%DIRECC%' OR TABLE_NAME LIKE '%DOMICIL%') " +
            "ORDER BY TABLE_NAME");
        while(rs.next()) System.out.println("  " + rs.getString("TABLE_NAME").trim());
        rs.close();

        // 9. Tablas de CARGA/PAQUETE/PESO
        System.out.println("\n--- 9. TABLAS DE CARGA/PAQUETE/PESO ---");
        rs = s.executeQuery(
            "SELECT TABLE_NAME FROM QSYS2.SYSTABLES " +
            "WHERE TABLE_SCHEMA = 'EDGAR' " +
            "AND (TABLE_NAME LIKE '%CARGA%' OR TABLE_NAME LIKE '%PAQUET%' OR TABLE_NAME LIKE '%PESO%' " +
            "OR TABLE_NAME LIKE '%VOLUM%' OR TABLE_NAME LIKE '%CONTEN%' OR TABLE_NAME LIKE '%EMBAL%' " +
            "OR TABLE_NAME LIKE '%BULTO%') " +
            "ORDER BY TABLE_NAME");
        while(rs.next()) System.out.println("  " + rs.getString("TABLE_NAME").trim());
        rs.close();

        // 10. Todos los campos de la tabla principal de OTs - Last Mile
        System.out.println("\n--- 10. TODAS LAS COLUMNAS OTSXMARCA (RELATED TO LAST MILE) ---");
        rs = s.executeQuery(
            "SELECT COLUMN_NAME FROM QSYS2.SYSCOLUMNS WHERE TABLE_SCHEMA = 'EDGAR' AND TABLE_NAME = 'OTSXMARCA' " +
            "AND (COLUMN_NAME LIKE '%OT%' OR COLUMN_NAME LIKE '%KM%' OR COLUMN_NAME LIKE '%DIST%' " +
            "OR COLUMN_NAME LIKE '%FECHA%' OR COLUMN_NAME LIKE '%FEC%' OR COLUMN_NAME LIKE '%ENTREG%' " +
            "OR COLUMN_NAME LIKE '%ESTADO%' OR COLUMN_NAME LIKE '%STATUS%' OR COLUMN_NAME LIKE '%TIPO%' " +
            "OR COLUMN_NAME LIKE '%COSTO%' OR COLUMN_NAME LIKE '%MONTO%' OR COLUMN_NAME LIKE '%REPARTO%' " +
            "OR COLUMN_NAME LIKE '%RUTA%' OR COLUMN_NAME LIKE '%CLIENT%' OR COLUMN_NAME LIKE '%CHOFER%' " +
            "OR COLUMN_NAME LIKE '%UNIDAD%' OR COLUMN_NAME LIKE '%MARCA%' OR COLUMN_NAME LIKE '%MODELO%' " +
            "OR COLUMN_NAME LIKE '%REPARA%' OR COLUMN_NAME LIKE '%REFACC%' OR COLUMN_NAME LIKE '%FALLA%' " +
            "OR COLUMN_NAME LIKE '%DIAGN%' OR COLUMN_NAME LIKE '%KMS%' OR COLUMN_NAME LIKE '%GAS%' " +
            "OR COLUMN_NAME LIKE '%SEGUR%' OR COLUMN_NAME LIKE '%TENENC%' OR COLUMN_NAME LIKE '%VERIF%' " +
            "OR COLUMN_NAME LIKE '%PERMISO%') " +
            "ORDER BY ORDINAL_POSITION");
        while(rs.next()) System.out.println("  " + rs.getString("COLUMN_NAME").trim());
        rs.close();

        // 11. Todas las tablas con conteo de registros (para ver volumen real)
        System.out.println("\n--- 11. VOLUMEN DE REGISTROS - PRINCIPALES TABLAS ---");
        String[] tablas = {"OTSXMARCA", "OTSXMARCA2", "UNIDADESTA", "REFACTALLE", "GASTOSELEC",
            "GASTOSPROM", "MOVCAJA", "OTSXMARCA3", "CLIENTES", "CONDUCTORES", "CHOFERES",
            "RUTAS", "ENTREGAS", "PEDIDOS", "CAJAS", "FLOTILLAS", "SEGUROS", "TENENCIAS",
            "VERIFICACIONES", "PERMISOS", "COMBUSTIBLE"};
        for(String tbl : tablas) {
            try {
                rs = s.executeQuery("SELECT COUNT(*) FROM EDGAR." + tbl);
                if(rs.next()) {
                    int cnt = rs.getInt(1);
                    if(cnt > 0) System.out.println("  " + tbl + ": " + String.format("%,d", cnt) + " registros");
                }
                rs.close();
            } catch(Exception e) { /* tabla no existe */ }
        }

        // 12. Listar TODAS las tablas de EDGAR para ver cuáles no exploré
        System.out.println("\n--- 12. TODAS LAS TABLAS EDGAR (" + "COMPLETO) ---");
        rs = s.executeQuery("SELECT TABLE_NAME FROM QSYS2.SYSTABLES WHERE TABLE_SCHEMA = 'EDGAR' ORDER BY TABLE_NAME");
        int total = 0;
        while(rs.next()) {
            System.out.println("  " + rs.getString("TABLE_NAME").trim());
            total++;
        }
        rs.close();
        System.out.println("  TOTAL: " + total + " tablas");

        c.close();
        System.out.println("\n=== FIN EXPLORACION ===");
    }
}
