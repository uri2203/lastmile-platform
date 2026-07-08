import java.sql.*;

public class LastMile_Fase1D_Corregir {
    public static void main(String[] args) throws Exception {
        Connection c = DriverManager.getConnection(
            "jdbc:as400://192.168.0.240;errors=full", "AYUDATX", "MXTAC23");
        Statement s = c.createStatement();
        System.out.println("Corrigiendo tablas SLA...\n");

        try {
            s.executeUpdate(
                "CREATE TABLE TESTLIB.SLA_CONFIGURACION (" +
                "SLA_ID INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY, " +
                "EMP_ID INTEGER NOT NULL, " +
                "CLI_ID INTEGER, " +
                "SLA_NOMBRE VARCHAR(50) NOT NULL, " +
                "SLA_TIEMPO_MAX_HORAS INTEGER DEFAULT 24, " +
                "SLA_TASA_MINIMA_EXITO DECIMAL(5,2) DEFAULT 95.00, " +
                "SLA_PENALIZACION_PCT DECIMAL(5,2) DEFAULT 5.00, " +
                "SLA_PENALIZACION_MAX DECIMAL(10,2) DEFAULT 500.00, " +
                "SLA_ESTATUS VARCHAR(10) DEFAULT 'ACTIVO')");
            System.out.println("  OK SLA_CONFIGURACION");
        } catch (Exception e) {
            System.out.println("  ERROR SLA_CONFIGURACION: " + e.getMessage().split("\n")[0]);
        }

        try {
            s.executeUpdate(
                "CREATE TABLE TESTLIB.SLA_RESULTADOS (" +
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
                "SLR_PENALIZACION DECIMAL(10,2) DEFAULT 0)");
            System.out.println("  OK SLA_RESULTADOS");
        } catch (Exception e) {
            System.out.println("  ERROR SLA_RESULTADOS: " + e.getMessage().split("\n")[0]);
        }

        c.close();
        System.out.println("\nDone.");
    }
}
