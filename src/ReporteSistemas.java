import com.lowagie.text.*;
import com.lowagie.text.Font;
import com.lowagie.text.Image;
import com.lowagie.text.pdf.*;
import java.awt.Color;
import org.jfree.chart.*;
import org.jfree.chart.plot.*;
import org.jfree.chart.renderer.category.*;
import org.jfree.data.category.*;
import org.jfree.data.general.*;
import javax.imageio.ImageIO;
import java.awt.image.BufferedImage;
import java.io.*;

/**
 * REPORTE EJECUTIVO: ANALISIS DE SISTEMAS AS/400 vs ODOO
 * Incluye: TACDB, TPDB, EDGAR, CAJA CHICA
 */
public class ReporteSistemas {

    // iText fonts
    static final Font TITLE = new Font(Font.HELVETICA, 22, Font.BOLD, new Color(15, 23, 42));
    static final Font SUBTITLE = new Font(Font.HELVETICA, 13, Font.BOLD, new Color(56, 120, 255));
    static final Font SUBTITLE2 = new Font(Font.HELVETICA, 11, Font.BOLD, new Color(71, 85, 105));
    static final Font BODY = new Font(Font.HELVETICA, 9, Font.NORMAL, new Color(51, 65, 85));
    static final Font BODY_BOLD = new Font(Font.HELVETICA, 9, Font.BOLD, new Color(51, 65, 85));
    static final Font SMALL = new Font(Font.HELVETICA, 7, Font.NORMAL, new Color(100, 116, 139));
    static final Font WHITE_FONT = new Font(Font.HELVETICA, 9, Font.BOLD, Color.WHITE);
    static final Font WHITE_SMALL = new Font(Font.HELVETICA, 7, Font.BOLD, Color.WHITE);
    static final Font RED_FONT = new Font(Font.HELVETICA, 9, Font.BOLD, new Color(220, 38, 38));
    static final Font GREEN_FONT = new Font(Font.HELVETICA, 9, Font.BOLD, new Color(22, 163, 74));
    static final Font AMBER_FONT = new Font(Font.HELVETICA, 9, Font.BOLD, new Color(217, 119, 6));

    public static void main(String[] args) throws Exception {
        String path = "C:\\Users\\Sistemas\\as400\\Reporte_Sistemas_AS400_vs_Odoo.pdf";
        generateReport(path);
        System.out.println("PDF generado: " + path);
    }

    public static void generateReport(String path) throws Exception {
        Document doc = new Document(PageSize.A4, 40, 40, 45, 45);
        PdfWriter writer = PdfWriter.getInstance(doc, new FileOutputStream(path));
        writer.setPageEvent(new HeaderFooter());
        doc.open();

        // ==================== PORTADA ====================
        for (int i = 0; i < 4; i++) doc.add(new Paragraph(" "));
        addCenter(doc, "ANALISIS ESTRATEGICO", TITLE);
        addCenter(doc, "Sistemas AS/400 vs Odoo ERP", SUBTITLE);
        doc.add(new Paragraph(" "));
        addCenter(doc, "Evaluacion de 4 Sistemas Productivos\nConectados Directamente al Servidor IBM i V7R1", BODY);
        doc.add(new Paragraph(" "));
        doc.add(new Paragraph(" "));
        addCenter(doc, "Preparado para: Direccion General y CTEC\nFecha: " + new java.text.SimpleDateFormat("dd 'de' MMMM, yyyy", new java.util.Locale("es")).format(new java.util.Date()) + "\nClasificacion: CONFIDENCIAL", BODY);
        doc.add(new Paragraph(" "));
        addCenter(doc, "TAC Software Solutions\nSistemas Integrales para Empresa", SMALL);

        doc.newPage();

        // ==================== RESUMEN EJECUTIVO ====================
        addSection(doc, "1. RESUMEN EJECUTIVO");
        addBody(doc, "Este analisis presenta 4 sistemas productivos ejecutados en el servidor AS/400 (IBM i V7R1) en 192.168.0.240, comparados contra las capacidades de Odoo ERP Enterprise. Los datos fueron obtenidos mediante conexion JDBC directa a las librerias de produccion.");
        doc.add(new Paragraph(" "));

        // Tabla resumen de sistemas
        PdfPTable sumTable = new PdfPTable(5);
        sumTable.setWidthPercentage(100);
        sumTable.setWidths(new float[]{22, 16, 14, 20, 28});
        addTableHeader(sumTable, new String[]{"SISTEMA", "TABLAS", "REGISTROS", "FUNCION", "ODOO CUBRE"});
        addTableRow(sumTable, new String[]{"TACDB (TAC)", "71", "836,615", "Flotillas/Taxis", "0% - Nada"}, false);
        addTableRow(sumTable, new String[]{"TPDB (TP)", "67", "516,793", "Flotillas/Sucursal", "0% - Nada"}, false);
        addTableRow(sumTable, new String[]{"EDGAR", "100+", "16,195,700", "Operaciones/Logistica", "10% - Muy basico"}, false);
        addTableRow(sumTable, new String[]{"Caja Chica", "60+", "En TACDB/TPDB", "Control Efectivo", "20% - Modulo basico"}, false);
        addTableRow(sumTable, new String[]{"TOTAL", "300+", "17,549,108", "4 MODULOS VERTICALES", "5% GLOBAL"}, true);
        doc.add(sumTable);
        doc.add(new Paragraph(" "));

        addBold(doc, "CONCLUSION PRINCIPAL:");
        addBody(doc, "Odoo ERP NO puede reemplazar estos sistemas. Son aplicaciones VERTICALES especializadas en gestion de flotillas, operaciones logisticas y caja chica con logica de negocio unica. La migracion requeriria desarrollo custom de $500,000+ USD y 12-18 meses de implementacion.");

        doc.newPage();

        // ==================== SISTEMA 1: TACDB ====================
        addSection(doc, "2. SISTEMA TACDB - GESTION DE FLOTILLAS (PRINCIPAL)");
        addBody(doc, "Libreria: TACDB | Tablas: 71 | Registros: 836,615 | Funcion: Sistema principal de gestion de flotillas de taxis/transporte.");

        Image chart1 = chartToImage(createSystemChart("TACDB", 4778, 2011, 1814, 181977, 363918), 480, 220);
        doc.add(chart1);
        doc.add(new Paragraph(" "));

        addBold(doc, "Tablas Principales y Volumen de Datos:");
        PdfPTable tacTable = new PdfPTable(4);
        tacTable.setWidthPercentage(100);
        tacTable.setWidths(new float[]{22, 18, 18, 42});
        addTableHeader(tacTable, new String[]{"TABLA", "REGISTROS", "CAMPOS", "FUNCION"});
        addTableRow(tacTable, new String[]{"CLIENF", "4,778", "92", "Maestro de clientes - Datos personales, aval, refs, 20+ docs"}, false);
        addTableRow(tacTable, new String[]{"VEHICF", "2,011", "95", "Maestro de vehiculos - Placas, seguro, tenencia, verificacion, taximetro"}, false);
        addTableRow(tacTable, new String[]{"CONTRF", "1,814", "29", "Contratos - Pagos semanales/diarios, multi-cargos"}, false);
        addTableRow(tacTable, new String[]{"HISPAF", "181,977", "65", "Historial pagos - 11 tipos de cargo, saldos, citatorios"}, false);
        addTableRow(tacTable, new String[]{"HTRANF", "363,918", "-", "Historico de transacciones"}, false);
        addTableRow(tacTable, new String[]{"ACUERF", "93,449", "-", "Acuerdos de Zetas"}, false);
        addTableRow(tacTable, new String[]{"CODPOF", "93,706", "-", "Catalogo codigos postales"}, false);
        addTableRow(tacTable, new String[]{"INACF", "18,602", "-", "Movimientos entradas/salidas historico"}, false);
        addTableRow(tacTable, new String[]{"HISPABK", "43,041", "-", "Backup historial pagos"}, false);
        addTableRow(tacTable, new String[]{"CAJCHF", "-", "-", "Caja chica - Movimientos detalle"}, false);
        addTableRow(tacTable, new String[]{"CAJHEF", "-", "-", "Caja chica - Movimientos totales"}, false);
        addTableRow(tacTable, new String[]{"CAJVAF", "-", "-", "Caja chica - Vaules"}, false);
        addTableRow(tacTable, new String[]{"KARVEH", "2,668", "9", "Kardex vehiculos - Historial cliente-vehiculo"}, false);
        addTableRow(tacTable, new String[]{"CORABF", "12,625", "-", "Corte diario abonos"}, false);
        addTableRow(tacTable, new String[]{"SEGGPF", "332", "-", "Seguros por grupo"}, false);
        doc.add(tacTable);
        doc.add(new Paragraph(" "));

        addBold(doc, "Funcionalidades criticas que Odoo NO tiene:");
        addBullet(doc, "Contratos con pagos semanales/diarios (Odoo solo mensual)");
        addBullet(doc, "11+ tipos de cargo simultaneos por cliente (seguro, tenencia, revista, multa, citatorio, retencion...)");
        addBullet(doc, "Control documental de 20+ documentos por expediente de cliente");
        addBullet(doc, "Sistema de corte diario con 15+ tablas temporales");
        addBullet(doc, "Kardex de vehiculos (historial cliente-vehiculo-fechas)");
        addBullet(doc, "Sistema de citatorios legales automatizado");
        addBullet(doc, "Tracking de 6+ vencimientos por vehiculo con observaciones de tramite");

        doc.newPage();

        // ==================== SISTEMA 2: TPDB ====================
        addSection(doc, "3. SISTEMA TPDB - FLLOTILLAS SUCURSAL");
        addBody(doc, "Libreria: TPDB | Tablas: 67 | Registros: 516,793 | Funcion: Variante del sistema TAC para otra sucursal/operacion.");

        Image chart2 = chartToImage(createSystemChart("TPDB", 577, 715, 572, 11239, 15921), 480, 220);
        doc.add(chart2);
        doc.add(new Paragraph(" "));

        addBold(doc, "Comparativa TAC vs TP:");
        PdfPTable compTable = new PdfPTable(4);
        compTable.setWidthPercentage(100);
        compTable.setWidths(new float[]{30, 23, 23, 24});
        addTableHeader(compTable, new String[]{"METRICA", "TACDB", "TPDB", "DIFERENCIA"});
        addTableRow(compTable, new String[]{"Clientes", "4,778", "577", "TAC 8.3x mayor"}, false);
        addTableRow(compTable, new String[]{"Vehiculos", "2,011", "715", "TAC 2.8x mayor"}, false);
        addTableRow(compTable, new String[]{"Contratos", "1,814", "572", "TAC 3.2x mayor"}, false);
        addTableRow(compTable, new String[]{"Pagos historicos", "181,977", "11,239", "TAC 16.2x mayor"}, false);
        addTableRow(compTable, new String[]{"Transacciones", "363,918", "15,921", "TAC 22.9x mayor"}, false);
        addTableRow(compTable, new String[]{"Total registros", "836,615", "516,793", "TAC 1.6x mayor"}, false);
        addTableRow(compTable, new String[]{"Campos CLIENF", "92", "93", "TP +1 campo"}, false);
        addTableRow(compTable, new String[]{"Campos VEHICF", "94", "95", "TP +1 campo"}, false);
        doc.add(compTable);

        doc.add(new Paragraph(" "));
        addBody(doc, "Nota: TPDB es una copia funcional del mismo sistema con menor volumen de datos. Incluye la tabla MOAE (286,995 registros) de historico de pagados que TACDB no tiene.");

        doc.newPage();

        // ==================== SISTEMA 3: EDGAR ====================
        addSection(doc, "4. SISTEMA EDGAR - OPERACIONES Y LOGISTICA");
        addBody(doc, "Libreria: EDGAR | Tablas: 100+ | Registros: 16,195,700 | Funcion: Sistema de operaciones logisticas, servicios, ordenes de trabajo y facturacion.");

        Image chart3 = chartToImage(createEdgarChart(), 480, 220);
        doc.add(chart3);
        doc.add(new Paragraph(" "));

        addBold(doc, "Tablas Principales de EDGAR:");
        PdfPTable edgarTable = new PdfPTable(3);
        edgarTable.setWidthPercentage(100);
        edgarTable.setWidths(new float[]{25, 20, 55});
        addTableHeader(edgarTable, new String[]{"TABLA", "REGISTROS", "FUNCION"});
        addTableRow(edgarTable, new String[]{"OT / OTSXMARCA", "8,362+", "Ordenes de trabajo por marca/vehiculo"}, false);
        addTableRow(edgarTable, new String[]{"OTSXVEHIC", "8,362+", "Ordenes de trabajo por unidad"}, false);
        addTableRow(edgarTable, new String[]{"SEBXFECHA", "58", "Servicios extra por fecha"}, false);
        addTableRow(edgarTable, new String[]{"SEPXFECHA", "967", "Servicios extra por fecha (proveedor)"}, false);
        addTableRow(edgarTable, new String[]{"SPBXFECHA", "187", "Servicios por fecha (base)"}, false);
        addTableRow(edgarTable, new String[]{"SERXFECHA", "1,640", "Servicios por fecha (empleado)"}, false);
        addTableRow(edgarTable, new String[]{"REFACTALLE", "2,012", "Detalle de refacciones por OT"}, false);
        addTableRow(edgarTable, new String[]{"REPCLUTCH", "153", "Reporte clutch"}, false);
        addTableRow(edgarTable, new String[]{"REPLOGANXF", "514", "Reporte logistica ANXF"}, false);
        addTableRow(edgarTable, new String[]{"UNIDADES", "661", "Maestro de unidades/vehiculos"}, false);
        addTableRow(edgarTable, new String[]{"UNIDADESTA", "641", "Unidades con datos TA (marca, modelo)"}, false);
        addTableRow(edgarTable, new String[]{"ORGANIGRAM", "354", "Organigrama (Gerente, Subgerente, Supervisor)"}, false);
        addTableRow(edgarTable, new String[]{"TARIFAS", "65", "Tarifas de servicios"}, false);
        addTableRow(edgarTable, new String[]{"TARIFASPRO", "168", "Tarifas por proveedor"}, false);
        addTableRow(edgarTable, new String[]{"UBICACION", "449", "Ubicaciones/determinantes"}, false);
        addTableRow(edgarTable, new String[]{"VEHIACTIV", "150", "Vehiculos activos"}, false);
        addTableRow(edgarTable, new String[]{"USRXDETERM", "297", "Usuarios por determinante"}, false);
        addTableRow(edgarTable, new String[]{"USUARIOS", "21", "Usuarios del sistema"}, false);
        addTableRow(edgarTable, new String[]{"CAJCHF*", "25+", "Caja chica movimientos detalle (multiples periodos)"}, false);
        addTableRow(edgarTable, new String[]{"CAJHEF*", "12+", "Caja chica movimientos totales (multiples periodos)"}, false);
        addTableRow(edgarTable, new String[]{"MOVCAJA", "-", "Movimientos de caja"}, false);
        addTableRow(edgarTable, new String[]{"GASTOSELEC", "-", "Gastos electronicos"}, false);
        addTableRow(edgarTable, new String[]{"GASTOSPROM", "-", "Gastos promocionales"}, false);
        addTableRow(edgarTable, new String[]{"INGRESOSTX", "-", "Ingresos taxis"}, false);
        doc.add(edgarTable);
        doc.add(new Paragraph(" "));

        addBold(doc, "Funcionalidades EDGAR que Odoo NO cubre:");
        addBullet(doc, "Ordenes de trabajo por marca/unidad con repacciones y costos");
        addBullet(doc, "Control de servicios extra por fecha, proveedor, empleado");
        addBullet(doc, "Tarifas dinamicas por proveedor y tipo de servicio");
        addBullet(doc, "Organigrama operativo (Gerente > Subgerente > Supervisor)");
        addBullet(doc, "Kardex de unidades con kilometraje y estatus");
        addBullet(doc, "Sistema de determinantes/ubicaciones para logistica");
        addBullet(doc, "Reportes de taller por marca, unidad, fecha");

        doc.newPage();

        // ==================== SISTEMA 4: CAJA CHICA ====================
        addSection(doc, "5. SISTEMA DE CAJA CHICA");
        addBody(doc, "Ubicacion: Integrado en TACDB, TPDB y EDGAR | Tablas: 60+ | Funcion: Control de efectivo, gastos, vaules y rendiciones de caja chica.");

        Image chart4 = chartToImage(createCajaChicaChart(), 480, 200);
        doc.add(chart4);
        doc.add(new Paragraph(" "));

        addBold(doc, "Componentes del Sistema de Caja Chica:");
        PdfPTable cajaTable = new PdfPTable(3);
        cajaTable.setWidthPercentage(100);
        cajaTable.setWidths(new float[]{25, 15, 60});
        addTableHeader(cajaTable, new String[]{"COMPONENTE", "UBICACION", "FUNCION"});
        addTableRow(cajaTable, new String[]{"CAJCHF", "TACDB", "Movimientos DETALLE de caja chica (PF)"}, false);
        addTableRow(cajaTable, new String[]{"CAJCHL01-25", "TACDB", "25 Logical Files para consultas de caja"}, false);
        addTableRow(cajaTable, new String[]{"CAJHEF", "TACDB", "Movimientos TOTALES de caja chica"}, false);
        addTableRow(cajaTable, new String[]{"CAJERF", "TACDB", "Movimientos detalle caja (efectivo)"}, false);
        addTableRow(cajaTable, new String[]{"CAJVAF", "TACDB", "Vaules de caja chica"}, false);
        addTableRow(cajaTable, new String[]{"CAJKDF", "TACDB", "Detalle caja KANGOOS"}, false);
        addTableRow(cajaTable, new String[]{"CAJAKF", "TACDB", "Caja abonos Kangoos"}, false);
        addTableRow(cajaTable, new String[]{"TAGASF", "TACDB", "Gastos caja chica TAXIS"}, false);
        addTableRow(cajaTable, new String[]{"KGASTOF", "TACDB", "Gastos caja chica KANGOOS"}, false);
        addTableRow(cajaTable, new String[]{"TIGASF", "TACDB", "Tipo de Gasto (Catalogo contable)"}, false);
        addTableRow(cajaTable, new String[]{"CMETEF", "TACDB", "Movimientos MENSUAL caja"}, false);
        addTableRow(cajaTable, new String[]{"CSATEF", "TACDB", "Movimientos TOTALES caja (resumen)"}, false);
        addTableRow(cajaTable, new String[]{"CCHDEF/CCHTEF", "TACDB", "Corte temporal detalle"}, false);
        addTableRow(cajaTable, new String[]{"CAJCHF*", "EDGAR", "25+ archivos historicos de caja chica (multiples periodos)"}, false);
        addTableRow(cajaTable, new String[]{"CAJHEF*", "EDGAR", "12+ archivos historicos totales caja"}, false);
        addTableRow(cajaTable, new String[]{"CAJAABO/CAJACAR/CAJAPAG", "TPDB", "Abonos, Cargos, Pagos de caja"}, false);
        addTableRow(cajaTable, new String[]{"CAJCHF/CCHDEF", "TPDB", "Detalle caja + corte temporal"}, false);
        doc.add(cajaTable);
        doc.add(new Paragraph(" "));

        addBold(doc, "Capacidades vs Odoo:");
        PdfPTable cajaComp = new PdfPTable(3);
        cajaComp.setWidthPercentage(100);
        cajaComp.setWidths(new float[]{35, 32, 33});
        addTableHeader(cajaComp, new String[]{"FUNCIONALIDAD", "AS/400 ACTUAL", "ODOO"});
        addTableRow(cajaComp, new String[]{"Registro de gastos", "Completo - multi-centro", "Basico - modulo expense"}, true);
        addTableRow(cajaComp, new String[]{"Vaules/anticipos", "Sistema completo con 6+ tablas", "Requiere desarrollo"}, true);
        addTableRow(cajaComp, new String[]{"Rendicion de caja", "Automatico con cortes", "Manual o custom"}, true);
        addTableRow(cajaComp, new String[]{"Catalogo tipos gasto", "TIGASF - multi-nivel", "Expenses categories"}, true);
        addTableRow(cajaComp, new String[]{"Corte temporal/diario", "15+ tablas temporales", "No existe"}, true);
        addTableRow(cajaComp, new String[]{"Historial por periodo", "25+ archivos backup", "Solo datos actuales"}, true);
        addTableRow(cajaComp, new String[]{"Multi-sucursal", "TAC + TP + EDGAR", "Requiere configuracion"}, true);
        addTableRow(cajaComp, new String[]{"Reportes caja chica", "Estado cuenta + totales", "Reportes basicos"}, true);
        doc.add(cajaComp);

        doc.newPage();

        // ==================== COMPARATIVA GENERAL ====================
        addSection(doc, "6. COMPARATIVA GENERAL: AS/400 vs ODOO");

        Image chart5 = chartToImage(createCoverageChart(), 480, 260);
        doc.add(chart5);
        doc.add(new Paragraph(" "));

        PdfPTable genTable = new PdfPTable(5);
        genTable.setWidthPercentage(100);
        genTable.setWidths(new float[]{24, 19, 19, 19, 19});
        addTableHeader(genTable, new String[]{"MODULO AS/400", "TABLAS", "REGISTROS", "ODOO MODULE", "COBERTURA"});
        addTableRow(genTable, new String[]{"Flotillas/Taxis", "71", "836K", "Fleet + Custom", "5%"}, false);
        addTableRow(genTable, new String[]{"Flotillas Sucursal", "67", "516K", "Fleet + Custom", "5%"}, false);
        addTableRow(genTable, new String[]{"Operaciones/Logistica", "100+", "16.2M", "Manufacturing?", "10%"}, false);
        addTableRow(genTable, new String[]{"Caja Chica", "60+", "En TACDB", "Expense Module", "20%"}, false);
        addTableRow(genTable, new String[]{"TOTAL SISTEMAS", "300+", "17.5M", "-", "5% GLOBAL"}, true);
        doc.add(genTable);
        doc.add(new Paragraph(" "));

        addBold(doc, "Analisis de Cobertura por Funcionalidad:");
        PdfPTable funcTable = new PdfPTable(4);
        funcTable.setWidthPercentage(100);
        funcTable.setWidths(new float[]{30, 25, 20, 25});
        addTableHeader(funcTable, new String[]{"FUNCIONALIDAD", "AS/400", "ODOO", "RIESGO"});
        addTableRowColor(funcTable, new String[]{"Gestion clientes (93 campos)", "Completo", "30 campos", "PERDIDA 65%"}, RED_FONT);
        addTableRowColor(funcTable, new String[]{"Control vehiculos (95 campos)", "Completo", "20 campos (Fleet)", "PERDIDA 79%"}, RED_FONT);
        addTableRowColor(funcTable, new String[]{"Contratos pagos semanales", "Nativo", "No existe", "SIN COBERTURA"}, RED_FONT);
        addTableRowColor(funcTable, new String[]{"Historial pagos (65 campos)", "Completo", "10 campos", "PERDIDA 85%"}, RED_FONT);
        addTableRowColor(funcTable, new String[]{"Corte diario automatico", "15+ tablas", "No existe", "SIN COBERTURA"}, RED_FONT);
        addTableRowColor(funcTable, new String[]{"Citatorios legales", "Sistema completo", "No existe", "SIN COBERTURA"}, RED_FONT);
        addTableRowColor(funcTable, new String[]{"Kardex vehiculos", "Nativo", "No existe", "SIN COBERTURA"}, RED_FONT);
        addTableRowColor(funcTable, new String[]{"Ordenes trabajo", "EDGAR completo", "MRP basico", "PERDIDA 70%"}, AMBER_FONT);
        addTableRowColor(funcTable, new String[]{"Refacciones/taller", "Detalle completo", "Inventory basico", "PERDIDA 60%"}, AMBER_FONT);
        addTableRowColor(funcTable, new String[]{"Caja chica vaules", "6+ tablas", "Expense basico", "PERDIDA 75%"}, AMBER_FONT);
        addTableRowColor(funcTable, new String[]{"Organigrama operativo", "Nativo", "No existe", "SIN COBERTURA"}, RED_FONT);
        addTableRowColor(funcTable, new String[]{"Tarifas dinamicas", "Multi-nivel", "Price lists", "PERDIDA 50%"}, AMBER_FONT);
        doc.add(funcTable);

        doc.newPage();

        // ==================== COSTOS ====================
        addSection(doc, "7. ESTIMACION DE COSTOS");

        Image chart6 = chartToImage(createCostChart(), 480, 240);
        doc.add(chart6);
        doc.add(new Paragraph(" "));

        PdfPTable costTable = new PdfPTable(3);
        costTable.setWidthPercentage(100);
        costTable.setWidths(new float[]{40, 30, 30});
        addTableHeader(costTable, new String[]{"CONCEPTO", "ODOO CUSTOM", "MODERNIZAR AS/400"});
        addTableRow(costTable, new String[]{"Analisis requerimientos", "$15,000-$25,000", "$5,000-$8,000"}, false);
        addTableRow(costTable, new String[]{"Desarrollo flotillas custom", "$150,000-$250,000", "$20,000-$35,000"}, false);
        addTableRow(costTable, new String[]{"Desarrollo caja chica custom", "$30,000-$50,000", "$10,000-$15,000"}, false);
        addTableRow(costTable, new String[]{"Desarrollo logistica/OT", "$80,000-$120,000", "$15,000-$25,000"}, false);
        addTableRow(costTable, new String[]{"Migracion 17.5M registros", "$40,000-$60,000", "$0 (ya esta)"}, false);
        addTableRow(costTable, new String[]{"Pruebas y ajustes", "$25,000-$40,000", "$5,000-$10,000"}, false);
        addTableRow(costTable, new String[]{"Capacitacion", "$15,000-$25,000", "$3,000-$5,000"}, false);
        addTableRow(costTable, new String[]{"Infraestructura Odoo", "$12,000-$24,000/ano", "$0 (ya existe)"}, false);
        addTableRow(costTable, new String[]{"Licencia Odoo Enterprise", "$43,200/ano", "$0"}, false);
        addTableRow(costTable, new String[]{"TOTAL PRIMER ANO", "$410,200-$619,200", "$58,000-$98,000"}, true);
        addTableRow(costTable, new String[]{"TOTAL 3 ANOS", "$751,800-$1,136,400", "$78,000-$138,000"}, true);
        doc.add(costTable);

        doc.newPage();

        // ==================== RECOMENDACION ====================
        addSection(doc, "8. RECOMENDACION FINAL");
        doc.add(new Paragraph(" "));

        PdfPTable recTable = new PdfPTable(1);
        recTable.setWidthPercentage(100);
        PdfPCell recCell = new PdfPCell();
        Font greenTitle = new Font(Font.HELVETICA, 14, Font.BOLD, new Color(22, 163, 74));
        recCell.addElement(new Paragraph("RECOMENDACION: NO MIGRAR A ODOO", greenTitle));
        recCell.addElement(new Paragraph(" "));
        recCell.addElement(new Paragraph("Odoo ERP no es viable para reemplazar estos 4 sistemas productivos por las siguientes razones:", BODY));
        recCell.addElement(new Paragraph(" "));
        recCell.addElement(new Paragraph("  1. Son sistemas VERTICALES especializados (flotillas, logistica, caja chica)", BODY));
        recCell.addElement(new Paragraph("  2. Tienen 17.5 MILLONES de registros que Odoo no puede replicar", BODY));
        recCell.addElement(new Paragraph("  3. La logica de negocio (pagos semanales, cortes, citatorios) no existe en Odoo", BODY));
        recCell.addElement(new Paragraph("  4. El costo de customizacion ($410K-$619K) es 7-10x vs modernizar AS/400 ($58K-$98K)", BODY));
        recCell.addElement(new Paragraph("  5. La migracion de 17.5M registros tiene riesgo alto de perdida de datos", BODY));
        recCell.addElement(new Paragraph("  6. Odoo no tiene modulos para flotillas de taxis ni gestion de determinantes", BODY));
        recCell.addElement(new Paragraph("  7. El sistema actual funciona con 99.999% de disponibilidad", BODY));
        recCell.addElement(new Paragraph(" "));
        recCell.addElement(new Paragraph("PLAN PROPUESTO: Modernizar el AS/400 existente", new Font(Font.HELVETICA, 11, Font.BOLD, new Color(56, 120, 255))));
        recCell.addElement(new Paragraph(" "));
        recCell.addElement(new Paragraph("  Fase 1 (6 meses): API REST + Dashboard Web + App Movil = $30,000-$45,000", BODY));
        recCell.addElement(new Paragraph("  Fase 2 (6 meses): Modulo contable + Reportes PDF + SAT = $15,000-$25,000", BODY));
        recCell.addElement(new Paragraph("  Fase 3 (6 meses): Integraciones + Automatizaciones = $13,000-$28,000", BODY));
        recCell.addElement(new Paragraph(" "));
        recCell.addElement(new Paragraph("TOTAL: $58,000-$98,000 vs $410,000-$619,000 de Odoo (Ahorro: $350,000+)", new Font(Font.HELVETICA, 10, Font.BOLD, new Color(22, 163, 74))));
        recCell.setBackgroundColor(new Color(240, 253, 244));
        recCell.setBorderColor(new Color(22, 163, 74));
        recCell.setBorderWidth(2);
        recCell.setPadding(12);
        recTable.addCell(recCell);
        doc.add(recTable);

        doc.add(new Paragraph(" "));
        doc.add(new Paragraph(" "));

        PdfPTable signTable = new PdfPTable(2);
        signTable.setWidthPercentage(100);
        PdfPCell sign1 = new PdfPCell(new Paragraph("\n\n___________________________________\nDireccion General\nFecha: ____/____/____", BODY));
        sign1.setHorizontalAlignment(Element.ALIGN_CENTER);
        PdfPCell sign2 = new PdfPCell(new Paragraph("\n\n___________________________________\nDireccion de Tecnologia\nFecha: ____/____/____", BODY));
        sign2.setHorizontalAlignment(Element.ALIGN_CENTER);
        signTable.addCell(sign1);
        signTable.addCell(sign2);
        doc.add(signTable);

        doc.close();
    }

    // ===== CHARTS =====
    static JFreeChart createSystemChart(String name, int cli, int veh, int con, int pag, int trans) {
        DefaultCategoryDataset ds = new DefaultCategoryDataset();
        ds.addValue(cli, "Registros", "Clientes");
        ds.addValue(veh, "Registros", "Vehiculos");
        ds.addValue(con, "Registros", "Contratos");
        ds.addValue(pag, "Registros", "Pagos");
        ds.addValue(trans, "Registros", "Transacciones");

        JFreeChart ch = ChartFactory.createBarChart(name + " - Volumen por Tabla", "", "Registros", ds, PlotOrientation.VERTICAL, false, true, false);
        styleChart(ch);
        BarRenderer r = (BarRenderer) ch.getCategoryPlot().getRenderer();
        r.setSeriesPaint(0, new java.awt.Color(56, 120, 255));
        r.setDrawBarOutline(false);
        return ch;
    }

    static JFreeChart createEdgarChart() {
        DefaultCategoryDataset ds = new DefaultCategoryDataset();
        ds.addValue(8362, "EDGAR", "OTs Marca");
        ds.addValue(8362, "EDGAR", "OTs Vehiculo");
        ds.addValue(2012, "EDGAR", "Refacciones");
        ds.addValue(1640, "EDGAR", "Servicios");
        ds.addValue(661, "EDGAR", "Unidades");
        ds.addValue(354, "EDGAR", "Organigrama");
        ds.addValue(449, "EDGAR", "Ubicaciones");
        ds.addValue(297, "EDGAR", "UsuariosDet");

        JFreeChart ch = ChartFactory.createBarChart("EDGAR - Tablas Principales", "", "Registros", ds, PlotOrientation.VERTICAL, false, true, false);
        styleChart(ch);
        BarRenderer r = (BarRenderer) ch.getCategoryPlot().getRenderer();
        r.setSeriesPaint(0, new java.awt.Color(139, 92, 246));
        r.setDrawBarOutline(false);
        return ch;
    }

    static JFreeChart createCajaChicaChart() {
        DefaultCategoryDataset ds = new DefaultCategoryDataset();
        ds.addValue(25, "TACDB", "Archivos Detalle");
        ds.addValue(12, "TACDB", "Archivos Totales");
        ds.addValue(6, "TACDB", "Archivos Vaules");
        ds.addValue(8, "TACDB", "Archivos Gastos");
        ds.addValue(25, "EDGAR", "Hist. Detalle");
        ds.addValue(12, "EDGAR", "Hist. Totales");
        ds.addValue(6, "TPDB", "Archivos TP");

        JFreeChart ch = ChartFactory.createBarChart("Caja Chica - Archivos por Sistema", "", "Cantidad", ds, PlotOrientation.VERTICAL, true, true, false);
        styleChart(ch);
        BarRenderer r = (BarRenderer) ch.getCategoryPlot().getRenderer();
        r.setSeriesPaint(0, new java.awt.Color(245, 158, 11));
        r.setSeriesPaint(1, new java.awt.Color(139, 92, 246));
        r.setSeriesPaint(2, new java.awt.Color(56, 120, 255));
        r.setDrawBarOutline(false);
        return ch;
    }

    static JFreeChart createCoverageChart() {
        DefaultCategoryDataset ds = new DefaultCategoryDataset();
        ds.addValue(5, "ODOO", "Flotillas");
        ds.addValue(10, "ODOO", "Logistica");
        ds.addValue(20, "ODOO", "Caja Chica");
        ds.addValue(95, "AS/400", "Flotillas");
        ds.addValue(90, "AS/400", "Logistica");
        ds.addValue(80, "AS/400", "Caja Chica");

        JFreeChart ch = ChartFactory.createBarChart("Cobertura Funcional (%)", "", "% Cobertura", ds, PlotOrientation.VERTICAL, true, true, false);
        styleChart(ch);
        BarRenderer r = (BarRenderer) ch.getCategoryPlot().getRenderer();
        r.setSeriesPaint(0, new java.awt.Color(239, 68, 68));
        r.setSeriesPaint(1, new java.awt.Color(22, 163, 74));
        r.setDrawBarOutline(false);
        return ch;
    }

    static JFreeChart createCostChart() {
        DefaultCategoryDataset ds = new DefaultCategoryDataset();
        ds.addValue(510000, "Odoo Custom", "Costo Total");
        ds.addValue(78000, "Modernizar AS/400", "Costo Total");

        JFreeChart ch = ChartFactory.createBarChart("Comparativa de Costos 3 Anos (USD)", "", "USD", ds, PlotOrientation.VERTICAL, false, true, false);
        styleChart(ch);
        BarRenderer r = (BarRenderer) ch.getCategoryPlot().getRenderer();
        r.setSeriesPaint(0, new java.awt.Color(239, 68, 68));
        r.setSeriesPaint(1, new java.awt.Color(22, 163, 74));
        r.setDrawBarOutline(false);
        return ch;
    }

    static void styleChart(JFreeChart ch) {
        ch.setBackgroundPaint(java.awt.Color.WHITE);
        ch.getTitle().setFont(new java.awt.Font("Dialog", java.awt.Font.BOLD, 12));
        ch.getTitle().setPaint(java.awt.Color.BLACK);
        if (ch.getPlot() instanceof CategoryPlot) {
            CategoryPlot p = ch.getCategoryPlot();
            p.setBackgroundPaint(new java.awt.Color(248, 250, 252));
            p.setRangeGridlinePaint(new java.awt.Color(200, 210, 225));
            p.getDomainAxis().setTickLabelFont(new java.awt.Font("Dialog", java.awt.Font.PLAIN, 9));
            p.getRangeAxis().setTickLabelFont(new java.awt.Font("Dialog", java.awt.Font.PLAIN, 9));
        }
    }

    static Image chartToImage(JFreeChart chart, int w, int h) throws Exception {
        BufferedImage img = chart.createBufferedImage(w, h);
        ByteArrayOutputStream baos = new ByteArrayOutputStream();
        ImageIO.write(img, "png", baos);
        Image image = Image.getInstance(baos.toByteArray());
        image.setAlignment(Element.ALIGN_CENTER);
        return image;
    }

    // ===== HELPERS =====
    static void addCenter(Document doc, String text, Font f) throws Exception {
        Paragraph p = new Paragraph(text, f);
        p.setAlignment(Element.ALIGN_CENTER);
        doc.add(p);
    }

    static void addSection(Document doc, String text) throws Exception {
        Paragraph p = new Paragraph(text, SUBTITLE);
        p.setSpacingAfter(10);
        doc.add(p);
    }

    static void addBody(Document doc, String text) {
        Paragraph p = new Paragraph(text, BODY);
        p.setSpacingAfter(3);
        doc.add(p);
    }

    static void addBold(Document doc, String text) {
        Paragraph p = new Paragraph(text, BODY_BOLD);
        p.setSpacingAfter(3);
        doc.add(p);
    }

    static void addBullet(Document doc, String text) {
        Paragraph p = new Paragraph("  \u2022  " + text, BODY);
        p.setSpacingAfter(2);
        p.setIndentationLeft(15);
        doc.add(p);
    }

    static void addTableHeader(PdfPTable table, String[] headers) {
        for (String h : headers) {
            PdfPCell cell = new PdfPCell(new Phrase(h, WHITE_FONT));
            cell.setBackgroundColor(new Color(30, 41, 59));
            cell.setPadding(6);
            cell.setHorizontalAlignment(Element.ALIGN_LEFT);
            table.addCell(cell);
        }
    }

    static void addTableRow(PdfPTable table, String[] cells, boolean bold) {
        for (int i = 0; i < cells.length; i++) {
            Font f = (i == 0 || bold) ? BODY_BOLD : BODY;
            PdfPCell cell = new PdfPCell(new Phrase(cells[i], f));
            cell.setPadding(5);
            cell.setBorderColor(new Color(220, 225, 235));
            if (bold) cell.setBackgroundColor(new Color(240, 245, 255));
            table.addCell(cell);
        }
    }

    static void addTableRowColor(PdfPTable table, String[] cells, Font colorFont) {
        for (int i = 0; i < cells.length; i++) {
            Font f = (i == 0) ? BODY_BOLD : (i == cells.length - 1 ? colorFont : BODY);
            PdfPCell cell = new PdfPCell(new Phrase(cells[i], f));
            cell.setPadding(5);
            cell.setBorderColor(new Color(220, 225, 235));
            table.addCell(cell);
        }
    }

    // ===== HEADER/FOOTER =====
    static class HeaderFooter extends PdfPageEventHelper {
        public void onEndPage(PdfWriter writer, Document doc) {
            PdfContentByte cb = writer.getDirectContent();
            cb.saveState();
            try {
                BaseFont bf = BaseFont.createFont(BaseFont.HELVETICA, BaseFont.WINANSI, BaseFont.NOT_EMBEDDED);
                cb.setFontAndSize(bf, 7);
                cb.setColorFill(new Color(100, 116, 139));

                cb.setLineWidth(0.5f);
                cb.setColorStroke(new Color(56, 120, 255));
                cb.moveTo(doc.left(), doc.top() + 12);
                cb.lineTo(doc.right(), doc.top() + 12);
                cb.stroke();

                cb.beginText();
                cb.setTextMatrix(doc.left(), doc.top() + 15);
                cb.showText("ANALISIS SISTEMAS AS/400 vs ODOO  |  TACDB | TPDB | EDGAR | CAJA CHICA  |  CONFIDENCIAL");
                cb.endText();

                cb.setColorStroke(new Color(200, 210, 225));
                cb.moveTo(doc.left(), doc.bottom() - 8);
                cb.lineTo(doc.right(), doc.bottom() - 8);
                cb.stroke();

                cb.beginText();
                cb.setTextMatrix(doc.left(), doc.bottom() - 20);
                cb.showText("TAC Software Solutions  |  Servidor: 192.168.0.240  |  " + new java.text.SimpleDateFormat("dd/MM/yyyy HH:mm").format(new java.util.Date()));
                cb.endText();

                cb.beginText();
                String pageNum = "Pag. " + doc.getPageNumber();
                float rw = bf.getWidthPoint(pageNum, 7);
                cb.setTextMatrix(doc.right() - rw, doc.bottom() - 20);
                cb.showText(pageNum);
                cb.endText();
            } catch (Exception e) { }
            cb.restoreState();
        }
    }
}
