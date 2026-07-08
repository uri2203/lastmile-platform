import java.sql.*;
import java.util.Random;
import java.math.BigDecimal;
import java.math.RoundingMode;

/**
 * FASE 1B: Generar datos de prueba realistas para Last Mile
 * 3 empresas multi-tenant con datos completos
 */
public class LastMile_Fase1B {
    
    static Connection c;
    static Statement s;
    static Random r = new Random();
    static int totalRegistros = 0;

    // Datos realistas
    static String[] empresas = {
        "DELIVERY EXPRESS MX|DEL123456789|Av. Reforma 100, CDMX|5551234567|contacto@deliveryexpress.com|PLAN_PRO|15|25|2000",
        "TRANSPORTE RAPIDO SA|TRA987654321|Blvd. Insurgentes 200, GDL|3331234567|info@transporterapido.com|PLAN_EMPRESA|20|40|5000",
        "LOGISTICA INTEGRAL MX|LOG456789123|Av. Universidad 300, MTY|8181234567|ventas@logisticaintegral.com|PLAN_PRO|10|20|1500"
    };

    static String[] nombresChoferes = {
        "CARLOS GARCIA|MARIA RODRIGUEZ|JUAN LOPEZ|ANA MARTINEZ|PEDRO SANCHEZ|LAURA HERNANDEZ|JOSE GONZALEZ|TERESA RAMIREZ|FRANCISCO DIAZ|SILVIA TORRES",
        "ROBERTO FLORES|ELENA VARGAS|RICARDO MORALES|ADRIANA CASTILLO|MIGUEL ANGEL RUiz|CARMEN ORTIZ|FERNANDO GUERRERO|PATRICIA REYES|DANIEL CRUZ|MONICA DELGADO",
        "ALEJANDRO NAVARRO|VERONICA SOTO|HECTOR PEREZ|IRENE FUENTES|OSCAR MEDINA|GABRIELA SILVA|RUBEN CASTRO|NORMA DOMINGUEZ|ARTURO RIOS|LAURA MENDEZ"
    };

    static String[] marcasVehiculos = {"KANGOO|Renault|2020|PICKUP|150|2.5",
        "PROMASTER|RAM|2021|VAN|800|8.0",
        "PARTNER|Peugeot|2022|VAN|600|6.0",
        "KWID|Renault|2023|AUTO|80|1.5",
        "NISSAN NP300|Nissan|2020|PICKUP|200|3.0",
        "VW SPRINTER|Volkswagen|2021|VAN|1000|10.0",
        "FORD TRANSIT|Ford|2022|VAN|900|9.0",
        "CHEVROLET S10|Chevrolet|2019|PICKUP|180|2.8"};

    static String[] colonias = {
        "POLANCO|CONDESA|ROMA|CENTRO|DEL VALLE|NAPOLES|HIPÓDROMO|CHAPULTEPEC|SANTA FE|TEPEYAC",
        "PROVIDENCIA|CHAPALITA|SANTUARIO|MONTECALVO|VALLARTA|AMERICANA|CENTRO|REFORMA|PROGRESO|LAURELES",
        "SAN PEDRO|GOB. CERVANTES|MICHOACAN|CONSTITUCION|CENTRO|INDUSTRIAL|UNIVERSIDAD|FUENTES|MATAMOROS|OBRERA"
    };

    static String[] ciudades = {"CIUDAD DE MEXICO|CDMX|MEXICO",
        "GUADALAJARA|GDL|JALISCO",
        "MONTERREY|MTY|NUEVO LEON"};

    static String[] motivosFallo = {
        "CLIENTE NO PRESENTE|DIRECCION INCORRECTA|PUERTA CERRADA|RECHAZO DEL CLIENTE|PAQUETE DAÑADO|SIN ACCESO AL EDIFICIO|TELÉFONO NO CONTESTA|HORARIO NO DISPONIBLE"
    };

    public static void main(String[] args) throws Exception {
        c = DriverManager.getConnection(
            "jdbc:as400://192.168.0.240;errors=full", "AYUDATX", "MXTAC23");
        s = c.createStatement();

        System.out.println("=== GENERANDO DATOS DE PRUEBA LAST MILE ===\n");

        // 1. Empresas
        System.out.println("--- 1. EMPRESAS ---");
        for (int i = 0; i < empresas.length; i++) {
            String[] d = empresas[i].split("\\|");
            ejecutar("INSERT INTO TESTLIB.EMPRESAS (EMP_NOMBRE,EMP_RFC,EMP_DIRECCION,EMP_TELEFONO,EMP_EMAIL,EMP_PLAN,EMP_MAX_USUARIOS,EMP_MAX_CHOFERES,EMP_MAX_PEDIDOS_MES) VALUES ('" +
                d[0] + "','" + d[1] + "','" + d[2] + "','" + d[3] + "','" + d[4] + "','" + d[5] + "'," + d[6] + "," + d[7] + "," + d[8] + ")");
            System.out.println("  " + d[0]);
        }

        // 2. Usuarios (3 por empresa)
        System.out.println("\n--- 2. USUARIOS ---");
        String[] roles = {"ADMIN|admin|admin123", "OPERADOR|oper|oper123", "CONSULTA|cons|cons123"};
        for (int emp = 1; emp <= 3; emp++) {
            for (String rol : roles) {
                String[] d = rol.split("\\|");
                ejecutar("INSERT INTO TESTLIB.USUARIOS (EMP_ID,USR_NOMBRE,USR_USER,USR_PASS,USR_ROL) VALUES (" +
                    emp + ",'" + d[0] + "','user" + emp + d[1] + "','" + d[2] + "','" + d[0] + "')");
            }
            System.out.println("  Empresa " + emp + ": 3 usuarios creados");
        }

        // 3. Choferes (10 por empresa)
        System.out.println("\n--- 3. CHOFERES ---");
        String[][] listasChoferes = {
            {"CARLOS GARCIA","MARIA RODRIGUEZ","JUAN LOPEZ","ANA MARTINEZ","PEDRO SANCHEZ","LAURA HERNANDEZ","JOSE GONZALEZ","TERESA RAMIREZ","FRANCISCO DIAZ","SILVIA TORRES"},
            {"ROBERTO FLORES","ELENA VARGAS","RICARDO MORALES","ADRIANA CASTILLO","MIGUEL ANGEL RUIZ","CARMEN ORTIZ","FERNANDO GUERRERO","PATRICIA REYES","DANIEL CRUZ","MONICA DELGADO"},
            {"ALEJANDRO NAVARRO","VERONICA SOTO","HECTOR PEREZ","IRENE FUENTES","OSCAR MEDINA","GABRIELA SILVA","RUBEN CASTRO","NORMA DOMINGUEZ","ARTURO RIOS","LAURA MENDEZ"}
        };
        for (int emp = 0; emp < 3; emp++) {
            String[] nombres = listasChoferes[emp];
            for (int i = 0; i < nombres.length; i++) {
                String[] d = nombres[i].trim().split("\\s+");
                String nombre = d[0];
                String apellido = d.length > 1 ? d[1] : "";
                String lic = "LIC" + (10000000 + r.nextInt(90000000));
                String tel = "55" + (10000000 + r.nextInt(90000000));
                double salario = 8000 + r.nextDouble() * 7000;
                double comision = 5 + r.nextDouble() * 10;
                ejecutar("INSERT INTO TESTLIB.CHOFERES (EMP_ID,CHO_NOMBRE,CHO_APELLIDO,CHO_LICENCIA,CHO_TELEFONO,CHO_SALARIO_BASE,CHO_COMISION_PCT) VALUES (" +
                    (emp + 1) + ",'" + nombre + "','" + apellido + "','" + lic + "','" + tel + "'," +
                    BigDecimal.valueOf(salario).setScale(2, RoundingMode.HALF_UP) + "," +
                    BigDecimal.valueOf(comision).setScale(2, RoundingMode.HALF_UP) + ")");
            }
            System.out.println("  Empresa " + (emp + 1) + ": 10 choferes creados");
        }

        // 4. Vehículos (8 por empresa)
        System.out.println("\n--- 4. VEHICULOS ---");
        for (int emp = 1; emp <= 3; emp++) {
            for (int i = 0; i < marcasVehiculos.length; i++) {
                String[] d = marcasVehiculos[i].split("\\|");
                String unidad = "W" + String.format("%03d", (emp * 100 + i + 1));
                ejecutar("INSERT INTO TESTLIB.VEHICULOS (EMP_ID,VEH_UNIDAD,VEH_MARCA,VEH_MODELO,VEH_AÑO,VEH_TIPO,VEH_CAPACIDAD_KG,VEH_CAPACIDAD_M3) VALUES (" +
                    emp + ",'" + unidad + "','" + d[1] + "','" + d[0] + "'," + d[2] + ",'" + d[3] + "'," + d[4] + "," + d[5] + ")");
            }
            System.out.println("  Empresa " + emp + ": 8 vehículos creados");
        }

        // 5. Clientes (25 por empresa)
        System.out.println("\n--- 5. CLIENTES ---");
        String[] tiposCliente = {"REGULAR|0|0", "FRECUENTE|50000|15000", "PREMIUM|100000|30000", "CORPORATIVO|200000|60000"};
        for (int emp = 0; emp < 3; emp++) {
            String[] cols = colonias[emp].split("\\|");
            for (int i = 0; i < 25; i++) {
                String tipo = tiposCliente[r.nextInt(tiposCliente.length)];
                String[] td = tipo.split("\\|");
                String col = cols[r.nextInt(cols.length)];
                String ciudad = ciudades[emp].split("\\|")[0];
                double lat = 19.0 + r.nextDouble() * 4.5;
                double lon = -99.0 - r.nextDouble() * 3.0;
                ejecutar("INSERT INTO TESTLIB.CLIENTES_LM (EMP_ID,CLI_RAZON_SOCIAL,CLI_TELEFONO,CLI_DIRECCION,CLI_COLONIA,CLI_CIUDAD,CLI_ESTADO,CLI_LATITUD,CLI_LONGITUD,CLI_TIPO_CLIENTE,CLI_CREDITO,CLI_SALDO) VALUES (" +
                    (emp + 1) + ",'Cliente " + (i + 1) + " Emp" + (emp + 1) + "','55" + (10000000 + r.nextInt(90000000)) +
                    "','Calle " + (r.nextInt(200) + 1) + " #" + (r.nextInt(50) + 1) + "','" + col + "','" + ciudad +
                    "','MEXICO'," + BigDecimal.valueOf(lat).setScale(7, RoundingMode.HALF_UP) + "," +
                    BigDecimal.valueOf(lon).setScale(7, RoundingMode.HALF_UP) + ",'" + td[0] + "'," + td[1] + "," + td[2] + ")");
            }
            System.out.println("  Empresa " + (emp + 1) + ": 25 clientes creados");
        }

        // 6. Zonas (5 por empresa)
        System.out.println("\n--- 6. ZONAS ---");
        String[] zonas = {"CENTRO|Zona centro de la ciudad|19.40,-99.18,19.45,-99.12",
            "NORTE|Zona norte|19.45,-99.20,19.50,-99.15",
            "SUR|Zona sur|19.30,-99.20,19.35,-99.15",
            "ORIENTE|Zona oriente|19.35,-99.10,19.40,-99.05",
            "PONIENTE|Zona poniente|19.38,-99.25,19.42,-99.20"};
        for (int emp = 1; emp <= 3; emp++) {
            for (String z : zonas) {
                String[] d = z.split("\\|");
                String[] coords = d[2].split(",");
                ejecutar("INSERT INTO TESTLIB.ZONAS (EMP_ID,ZON_NOMBRE,ZON_DESCRIPCION,ZON_LAT_MIN,ZON_LAT_MAX,ZON_LON_MIN,ZON_LON_MAX) VALUES (" +
                    emp + ",'" + d[0] + "','" + d[1] + "'," + coords[0] + "," + coords[1] + "," + coords[2] + "," + coords[3] + ")");
            }
            System.out.println("  Empresa " + emp + ": 5 zonas creadas");
        }

        // 7. Tarifas (3 por empresa)
        System.out.println("\n--- 7. TARIFAS ---");
        String[] tarifas = {"BASICA|POR_ENTREGA|45.00|5.50|0.50|0|25.00|35.00",
            "EXPRESS|POR_ENTREGA|75.00|7.00|0.80|0|40.00|50.00",
            "PESADA|POR_KG|120.00|8.00|2.50|0.30|50.00|60.00"};
        for (int emp = 1; emp <= 3; emp++) {
            for (String t : tarifas) {
                String[] d = t.split("\\|");
                ejecutar("INSERT INTO TESTLIB.TARIFAS_LM (EMP_ID,TAR_NOMBRE,TAR_TIPO,TAR_MONTO_BASE,TAR_MONTO_KM,TAR_MONTO_KG,TAR_MONTO_M3,TAR_MONTO_ESPERA_MIN,TAR_MONTO_ENTREGA_EXT) VALUES (" +
                    emp + ",'" + d[0] + "','" + d[1] + "'," + d[2] + "," + d[3] + "," + d[4] + "," + d[5] + "," + d[6] + "," + d[7] + ")");
            }
            System.out.println("  Empresa " + emp + ": 3 tarifas creadas");
        }

        // 8. Pedidos (200 por empresa, 600 total)
        System.out.println("\n--- 8. PEDIDOS ---");
        String[] estados = {"PENDIENTE|20", "ASIGNADO|15", "EN_RUTA|25", "ENTREGADO|30", "FALLIDO|5", "CANCELADO|5"};
        String[] prioridades = {"URGENTE|15", "ALTA|25", "NORMAL|50", "BAJA|10"};
        String[] formasPago = {"EFECTIVO|40", "TARJETA|30", "TRANSFERENCIA|20", "CREDITO|10"};

        for (int emp = 1; emp <= 3; emp++) {
            for (int i = 0; i < 200; i++) {
                String numPedido = "PED" + String.format("%04d", emp) + String.format("%06d", (i + 1));
                int clienteId = (emp - 1) * 25 + r.nextInt(25) + 1;
                
                // Seleccionar estado ponderado
                String estado = ponderado(estados);
                String prioridad = ponderado(prioridades);
                String formaPago = ponderado(formasPago);

                double peso = 0.5 + r.nextDouble() * 49.5;
                double volumen = 0.01 + r.nextDouble() * 0.99;
                int bultos = 1 + r.nextInt(5);
                double valorDecl = 100 + r.nextDouble() * 9900;
                double costoEnvio = 45 + r.nextDouble() * 155;
                double costoTotal = costoEnvio + valorDecl * 0.01;

                // Fechas
                int diasAtras = r.nextInt(365);
                String fechaPedido = "2025-" + String.format("%02d", 1 + r.nextInt(12)) + "-" + String.format("%02d", 1 + r.nextInt(28)) +
                    " " + String.format("%02d", 6 + r.nextInt(14)) + ":" + String.format("%02d", r.nextInt(60)) + ":00";

                ejecutar("INSERT INTO TESTLIB.PEDIDOS (EMP_ID,PED_NUMERO,CLI_ID,PED_CLIENTE_NOMBRE,PED_CLIENTE_TELEFONO,PED_DESTINO_DIR,PED_DESTINO_COL,PED_DESTINO_CIUDAD,PED_DESTINO_ESTADO,PED_PESO_KG,PED_VOLUMEN_M3,PED_BULTOS,PED_VALOR_DECLARADO,PED_COSTO_ENVIO,PED_COSTO_TOTAL,PED_FORMA_PAGO,PED_ESTADO,PED_PRIORIDAD,PED_FECHA_PEDIDO,PED_DESCRIPCION) VALUES (" +
                    emp + ",'" + numPedido + "'," + clienteId + ",'Cliente " + clienteId + "','55" + (10000000 + r.nextInt(90000000)) +
                    "','Calle " + (r.nextInt(200) + 1) + " #" + (r.nextInt(50) + 1) + "','" + colonias[emp-1].split("\\|")[r.nextInt(5)] +
                    "','" + ciudades[emp-1].split("\\|")[0] + "','MEXICO'," +
                    BigDecimal.valueOf(peso).setScale(2, RoundingMode.HALF_UP) + "," +
                    BigDecimal.valueOf(volumen).setScale(2, RoundingMode.HALF_UP) + "," + bultos + "," +
                    BigDecimal.valueOf(valorDecl).setScale(2, RoundingMode.HALF_UP) + "," +
                    BigDecimal.valueOf(costoEnvio).setScale(2, RoundingMode.HALF_UP) + "," +
                    BigDecimal.valueOf(costoTotal).setScale(2, RoundingMode.HALF_UP) + ",'" +
                    formaPago + "','" + estado + "','" + prioridad + "','" + fechaPedido + "','Paquete " + (i + 1) + "')");
            }
            System.out.println("  Empresa " + emp + ": 200 pedidos creados");
        }

        // 9. Rutas (10 por empresa)
        System.out.println("\n--- 9. RUTAS ---");
        for (int emp = 1; emp <= 3; emp++) {
            for (int i = 0; i < 10; i++) {
                int choferId = (emp - 1) * 10 + r.nextInt(10) + 1;
                int vehId = (emp - 1) * 8 + r.nextInt(8) + 1;
                String fecha = "2025-" + String.format("%02d", 1 + r.nextInt(12)) + "-" + String.format("%02d", 1 + r.nextInt(28));
                int totalPedidos = 5 + r.nextInt(16);
                int totalEntregas = (int)(totalPedidos * (0.7 + r.nextDouble() * 0.3));
                double totalKm = 20 + r.nextDouble() * 180;
                int totalTiempo = 60 + r.nextInt(300);
                double costoTotal = totalKm * 5.50 + totalTiempo * 0.50;

                ejecutar("INSERT INTO TESTLIB.RUTAS (EMP_ID,RUT_NOMBRE,RUT_FECHA,CHO_ID,VEH_ID,RUT_ESTADO,RUT_TOTAL_PEDIDOS,RUT_TOTAL_ENTREGAS,RUT_TOTAL_KM,RUT_TOTAL_TIEMPO_MIN,RUT_COSTO_TOTAL) VALUES (" +
                    emp + ",'Ruta " + (i + 1) + " Emp" + emp + "','" + fecha + "'," + choferId + "," + vehId + ",'COMPLETADA'," +
                    totalPedidos + "," + totalEntregas + "," +
                    BigDecimal.valueOf(totalKm).setScale(2, RoundingMode.HALF_UP) + "," + totalTiempo + "," +
                    BigDecimal.valueOf(costoTotal).setScale(2, RoundingMode.HALF_UP) + ")");
            }
            System.out.println("  Empresa " + emp + ": 10 rutas creadas");
        }

        // 10. Entregas (300 por empresa)
        System.out.println("\n--- 10. ENTREGAS ---");
        String[] estadosEntrega = {"ENTREGADO|80", "NO_ENTREGADO|20"};
        for (int emp = 1; emp <= 3; emp++) {
            for (int i = 0; i < 300; i++) {
                int pedId = (emp - 1) * 200 + r.nextInt(200) + 1;
                int choferId = (emp - 1) * 10 + r.nextInt(10) + 1;
                String estado = ponderado(estadosEntrega);
                String receptor = "Receptor " + (i + 1);
                int espera = r.nextInt(30);
                double lat = 19.35 + r.nextDouble() * 0.15;
                double lon = -99.20 + r.nextDouble() * 0.20;

                ejecutar("INSERT INTO TESTLIB.ENTREGAS (EMP_ID,PED_ID,CHO_ID,ENT_RECEPTOR_NOMBRE,ENT_ESTADO,ENT_TIEMPO_ESPERA_MIN,ENT_LATITUD,ENT_LONGITUD,ENT_INTENTOS) VALUES (" +
                    emp + "," + pedId + "," + choferId + ",'" + receptor + "','" + estado + "'," + espera + "," +
                    BigDecimal.valueOf(lat).setScale(7, RoundingMode.HALF_UP) + "," +
                    BigDecimal.valueOf(lon).setScale(7, RoundingMode.HALF_UP) + "," + (1 + r.nextInt(3)) + ")");
            }
            System.out.println("  Empresa " + emp + ": 300 entregas creadas");
        }

        // 11. Incidencias (50 por empresa)
        System.out.println("\n--- 11. INCIDENCIAS ---");
        String[] tiposIncidencia = {"CLIENTE NO PRESENTE|15", "DIRECCION INCORRECTA|10", "PUERTA CERRADA|12",
            "RECHAZO DEL CLIENTE|5", "PAQUETE DAÑADO|3", "SIN ACCESO|8", "TEL_NO_CONTESTA|7"};
        for (int emp = 1; emp <= 3; emp++) {
            for (int i = 0; i < 50; i++) {
                int pedId = (emp - 1) * 200 + r.nextInt(200) + 1;
                int choferId = (emp - 1) * 10 + r.nextInt(10) + 1;
                String tipo = ponderado(tiposIncidencia);
                String[] td = tipo.split("\\|");
                double lat = 19.35 + r.nextDouble() * 0.15;
                double lon = -99.20 + r.nextDouble() * 0.20;

                ejecutar("INSERT INTO TESTLIB.INCIDENCIAS (EMP_ID,PED_ID,CHO_ID,INC_TIPO,INC_DESCRIPCION,INC_LATITUD,INC_LONGITUD) VALUES (" +
                    emp + "," + pedId + "," + choferId + ",'" + td[0] + "','Incidencia " + (i + 1) + " - " + td[0] + "'," +
                    BigDecimal.valueOf(lat).setScale(7, RoundingMode.HALF_UP) + "," +
                    BigDecimal.valueOf(lon).setScale(7, RoundingMode.HALF_UP) + ")");
            }
            System.out.println("  Empresa " + emp + ": 50 incidencias creadas");
        }

        // 12. Tracking (20 registros por chofer por empresa)
        System.out.println("\n--- 12. TRACKING ---");
        for (int emp = 1; emp <= 3; emp++) {
            for (int ch = 1; ch <= 10; ch++) {
                int choferId = (emp - 1) * 10 + ch;
                for (int t = 0; t < 20; t++) {
                    double lat = 19.35 + r.nextDouble() * 0.15;
                    double lon = -99.20 + r.nextDouble() * 0.20;
                    int vel = r.nextInt(80);
                    int rumbo = r.nextInt(360);
                    int bateria = 20 + r.nextInt(81);
                    String fecha = "2025-" + String.format("%02d", 1 + r.nextInt(12)) + "-" + String.format("%02d", 1 + r.nextInt(28)) +
                        " " + String.format("%02d", 6 + r.nextInt(14)) + ":" + String.format("%02d", r.nextInt(60)) + ":00";

                    ejecutar("INSERT INTO TESTLIB.TRACKING (EMP_ID,CHO_ID,TRK_LATITUD,TRK_LONGITUD,TRK_VELOCIDAD,TRK_RUMBO,TRK_FECHA,TRK_BATERIA) VALUES (" +
                        emp + "," + choferId + "," +
                        BigDecimal.valueOf(lat).setScale(7, RoundingMode.HALF_UP) + "," +
                        BigDecimal.valueOf(lon).setScale(7, RoundingMode.HALF_UP) + "," +
                        vel + "," + rumbo + ",'" + fecha + "'," + bateria + ")");
                }
            }
            System.out.println("  Empresa " + emp + ": 200 registros de tracking");
        }

        // 13. KPIs diarios (30 días por empresa)
        System.out.println("\n--- 13. KPIs DIARIOS ---");
        for (int emp = 1; emp <= 3; emp++) {
            for (int dia = 1; dia <= 30; dia++) {
                int nuevos = 15 + r.nextInt(25);
                int entregados = (int)(nuevos * (0.75 + r.nextDouble() * 0.2));
                int fallidos = nuevos - entregados - r.nextInt(3);
                int cancelados = r.nextInt(3);
                int aTiempo = (int)(entregados * (0.8 + r.nextDouble() * 0.15));
                int tardias = entregados - aTiempo;
                int tiempoProm = 25 + r.nextInt(40);
                double kmTotal = 80 + r.nextDouble() * 120;
                double costoTotal = kmTotal * 5.50 + tiempoProm * entregados * 0.50;
                double ingresoTotal = entregados * (45 + r.nextDouble() * 55);
                double utilidad = ingresoTotal - costoTotal;
                int choferesActivos = 6 + r.nextInt(5);
                int vehiculosActivos = 5 + r.nextInt(4);

                String fecha = "2025-06-" + String.format("%02d", dia);

                ejecutar("INSERT INTO TESTLIB.KPI_DIARIO (EMP_ID,KPI_FECHA,KPI_PEDIDOS_NUEVOS,KPI_PEDIDOS_ENTREGADOS,KPI_PEDIDOS_FALLIDOS,KPI_PEDIDOS_CANCELADOS,KPI_ENTREGAS_A_TIEMPO,KPI_ENTREGAS_TARDIAS,KPI_TIEMPO_PROMedio_MIN,KPI_KM_TOTAL,KPI_COSTO_TOTAL,KPI_INGRESO_TOTAL,KPI_UTILIDAD,KPI_CHOFERES_ACTIVOS,KPI_VEHICULOS_ACTIVOS) VALUES (" +
                    emp + ",'" + fecha + "'," + nuevos + "," + entregados + "," + Math.max(0, fallidos) + "," + cancelados + "," +
                    aTiempo + "," + tardias + "," + tiempoProm + "," +
                    BigDecimal.valueOf(kmTotal).setScale(2, RoundingMode.HALF_UP) + "," +
                    BigDecimal.valueOf(costoTotal).setScale(2, RoundingMode.HALF_UP) + "," +
                    BigDecimal.valueOf(ingresoTotal).setScale(2, RoundingMode.HALF_UP) + "," +
                    BigDecimal.valueOf(utilidad).setScale(2, RoundingMode.HALF_UP) + "," +
                    choferesActivos + "," + vehiculosActivos + ")");
            }
            System.out.println("  Empresa " + emp + ": 30 días de KPIs");
        }

        c.close();
        System.out.println("\n========================================");
        System.out.println("TOTAL REGISTROS INSERTADOS: " + totalRegistros);
        System.out.println("========================================");
        System.out.println("\n=== FIN FASE 1B - DATOS DE PRUEBA ===");
    }

    static String ponderado(String[] opciones) {
        int total = 0;
        for (String o : opciones) total += Integer.parseInt(o.split("\\|")[1]);
        int random = r.nextInt(total);
        int acum = 0;
        for (String o : opciones) {
            acum += Integer.parseInt(o.split("\\|")[1]);
            if (random < acum) return o.split("\\|")[0];
        }
        return opciones[0].split("\\|")[0];
    }

    static void ejecutar(String sql) {
        try {
            s.executeUpdate(sql);
            totalRegistros++;
        } catch (Exception e) {
            // Silenciar errores individuales
        }
    }
}
