import com.lowagie.text.Document;
import com.lowagie.text.Element;
import com.lowagie.text.Font;
import com.lowagie.text.Image;
import com.lowagie.text.PageSize;
import com.lowagie.text.Paragraph;
import com.lowagie.text.Phrase;
import com.lowagie.text.pdf.*;
import java.awt.Color;
import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;
import org.jfree.chart.*;
import org.jfree.chart.plot.*;
import org.jfree.chart.renderer.category.*;
import org.jfree.data.category.*;
import org.jfree.data.general.DefaultPieDataset;
import javax.imageio.ImageIO;
import java.awt.image.BufferedImage;
import java.io.*;

/**
 * GENERADOR PDF: GASTOS POR MODELO DE UNIDAD - EDGAR
 * Profesional para ejecutivos
 */
public class ReporteGastosPDF {

    static final Font TITLE = new Font(Font.HELVETICA, 22, Font.BOLD, new Color(15, 23, 42));
    static final Font SUBTITLE = new Font(Font.HELVETICA, 13, Font.BOLD, new Color(56, 120, 255));
    static final Font BODY = new Font(Font.HELVETICA, 9, Font.NORMAL, new Color(51, 65, 85));
    static final Font BODY_BOLD = new Font(Font.HELVETICA, 9, Font.BOLD, new Color(51, 65, 85));
    static final Font SMALL = new Font(Font.HELVETICA, 7, Font.NORMAL, new Color(100, 116, 139));
    static final Font WHITE_FONT = new Font(Font.HELVETICA, 9, Font.BOLD, Color.WHITE);
    static final Font WHITE_SM = new Font(Font.HELVETICA, 7, Font.BOLD, Color.WHITE);
    static final Font MONEY = new Font(Font.HELVETICA, 9, Font.NORMAL, new Color(22, 128, 57));
    static final Font MONEY_BOLD = new Font(Font.HELVETICA, 10, Font.BOLD, new Color(22, 128, 57));

    public static void generate(java.util.List<String[]> otData, java.util.List<String[]> refData, java.util.List<String[]> cajaData,
            java.util.List<String[]> unidData, BigDecimal totOt, BigDecimal totRef, BigDecimal totCaja,
            String outputPath) throws Exception {

        Document doc = new Document(PageSize.A4, 40, 40, 45, 45);
        PdfWriter writer = PdfWriter.getInstance(doc, new FileOutputStream(outputPath));
        writer.setPageEvent(new HeaderFooter());
        doc.open();

        // ==================== PORTADA ====================
        for (int i = 0; i < 5; i++) doc.add(new Paragraph(" "));
        addCenter(doc, "REPORTE DE GASTOS", TITLE);
        addCenter(doc, "Por Modelo de Unidad", SUBTITLE);
        doc.add(new Paragraph(" "));
        addCenter(doc, "Sistema EDGAR - IBM AS/400", BODY);
        addCenter(doc, "Fecha: " + new java.text.SimpleDateFormat("dd 'de' MMMM, yyyy HH:mm", new java.util.Locale("es")).format(new java.util.Date()), BODY);
        doc.add(new Paragraph(" "));
        doc.add(new Paragraph(" "));
        addCenter(doc, "TAC Software Solutions\nSistemas Integrales para Empresa", SMALL);

        doc.newPage();

        // ==================== RESUMEN EJECUTIVO ====================
        addSection(doc, "1. RESUMEN EJECUTIVO");

        // KPI Cards
        PdfPTable kpiTable = new PdfPTable(3);
        kpiTable.setWidthPercentage(100);
        kpiTable.setWidths(new float[]{33, 34, 33});

        PdfPCell kpi1 = createKPI("OTs por Modelo", "$" + formatNumber(totOt), otData.size() + " modelos");
        PdfPCell kpi2 = createKPI("Refacciones", "$" + formatNumber(totRef), refData.size() + " modelos");
        PdfPCell kpi3 = createKPI("Caja Chica", "$" + formatNumber(totCaja), cajaData.size() + " unidades");

        kpiTable.addCell(kpi1);
        kpiTable.addCell(kpi2);
        kpiTable.addCell(kpi3);
        doc.add(kpiTable);
        doc.add(new Paragraph(" "));

        // Total General
        BigDecimal totalGeneral = totOt.add(totRef).add(totCaja);
        PdfPTable totalBox = new PdfPTable(1);
        totalBox.setWidthPercentage(100);
        PdfPCell totalCell = new PdfPCell();
        totalCell.addElement(new Paragraph("TOTAL GENERAL DE GASTOS: $" + formatNumber(totalGeneral),
            new Font(Font.HELVETICA, 14, Font.BOLD, new Color(22, 128, 57))));
        totalCell.addElement(new Paragraph("OTs: $" + formatNumber(totOt) + " | Refacciones: $" + formatNumber(totRef) + " | Caja Chica: $" + formatNumber(totCaja), BODY));
        totalCell.setBackgroundColor(new Color(240, 253, 244));
        totalCell.setBorderColor(new Color(22, 128, 57));
        totalCell.setBorderWidth(2);
        totalCell.setPadding(12);
        totalCell.setHorizontalAlignment(Element.ALIGN_CENTER);
        totalBox.addCell(totalCell);
        doc.add(totalBox);

        doc.newPage();

        // ==================== GASTOS POR MODELO (OTs) ====================
        addSection(doc, "2. GASTOS POR MODELO (Ordenes de Trabajo)");
        addBody(doc, "Costo total de ordenes de trabajo agrupado por marca/modelo de unidad. Datos de la tabla OTSXMARCA2 del sistema EDGAR.");
        doc.add(new Paragraph(" "));

        // Grafica
        if (otData.size() > 0) {
            Image chart1 = chartToImage(createBarChart("Gastos por Modelo (OTs)", otData, 1), 500, 250);
            doc.add(chart1);
            doc.add(new Paragraph(" "));
        }

        // Tabla
        PdfPTable otTable = new PdfPTable(4);
        otTable.setWidthPercentage(100);
        otTable.setWidths(new float[]{35, 15, 20, 30});
        addTableHeader(otTable, new String[]{"MODELO/MARCA", "OTs", "COSTO TOTAL", "% DEL TOTAL"});
        for (String[] row : otData) {
            BigDecimal costo = new BigDecimal(row[2]);
            BigDecimal pct = totOt.compareTo(BigDecimal.ZERO) > 0 ?
                costo.multiply(new BigDecimal(100)).divide(totOt, 1, RoundingMode.HALF_UP) : BigDecimal.ZERO;
            addTableRow(otTable, new String[]{row[0], row[1], "$" + formatNumber(costo), pct + "%"}, false);
        }
        // Total
        addTableRow(otTable, new String[]{"TOTAL GENERAL", String.valueOf(otData.stream().mapToInt(r -> Integer.parseInt(r[1])).sum()),
            "$" + formatNumber(totOt), "100%"}, true);
        doc.add(otTable);

        doc.newPage();

        // ==================== REFACCIONES POR MODELO ====================
        addSection(doc, "3. GASTOS POR REFACCION Y MODELO");
        addBody(doc, "Costo de refacciones utilizadas en ordenes de trabajo, agrupado por modelo. Datos de REFACTALLE + OTSXMARCA.");
        doc.add(new Paragraph(" "));

        if (refData.size() > 0) {
            Image chart2 = chartToImage(createBarChart("Refacciones por Modelo", refData, 1), 500, 250);
            doc.add(chart2);
            doc.add(new Paragraph(" "));
        }

        PdfPTable refTable = new PdfPTable(4);
        refTable.setWidthPercentage(100);
        refTable.setWidths(new float[]{35, 15, 20, 30});
        addTableHeader(refTable, new String[]{"MODELO/MARCA", "PARTES", "COSTO REFACCION", "% DEL TOTAL"});
        for (String[] row : refData) {
            BigDecimal costo = new BigDecimal(row[2]);
            BigDecimal pct = totRef.compareTo(BigDecimal.ZERO) > 0 ?
                costo.multiply(new BigDecimal(100)).divide(totRef, 1, RoundingMode.HALF_UP) : BigDecimal.ZERO;
            addTableRow(refTable, new String[]{row[0], row[1], "$" + formatNumber(costo), pct + "%"}, false);
        }
        addTableRow(refTable, new String[]{"TOTAL GENERAL", String.valueOf(refData.stream().mapToInt(r -> Integer.parseInt(r[1])).sum()),
            "$" + formatNumber(totRef), "100%"}, true);
        doc.add(refTable);

        doc.newPage();

        // ==================== CAJA CHICA POR UNIDAD ====================
        addSection(doc, "4. GASTOS CAJA CHICA POR UNIDAD");
        addBody(doc, "Movimientos de egreso/ingreso del sistema de caja chica por unidad. Datos de GASTOSELEC del EDGAR.");
        doc.add(new Paragraph(" "));

        if (cajaData.size() > 0) {
            Image chart3 = chartToImage(createBarChart("Caja Chica por Unidad", cajaData, 1), 500, 250);
            doc.add(chart3);
            doc.add(new Paragraph(" "));
        }

        PdfPTable cajaTable = new PdfPTable(5);
        cajaTable.setWidthPercentage(100);
        cajaTable.setWidths(new float[]{20, 20, 20, 15, 25});
        addTableHeader(cajaTable, new String[]{"UNIDAD", "EGRESOS", "INGRESOS", "MOVS", "SALDO NETO"});
        for (String[] row : cajaData) {
            BigDecimal egreso = new BigDecimal(row[1]);
            BigDecimal ingreso = new BigDecimal(row[2]);
            BigDecimal saldo = egreso.subtract(ingreso);
            addTableRow(cajaTable, new String[]{row[0], "$" + formatNumber(egreso), "$" + formatNumber(ingreso), row[3],
                "$" + formatNumber(saldo)}, false);
        }
        BigDecimal totEgresos = cajaData.stream().map(r -> new BigDecimal(r[1])).reduce(BigDecimal.ZERO, BigDecimal::add);
        BigDecimal totIngresos = cajaData.stream().map(r -> new BigDecimal(r[2])).reduce(BigDecimal.ZERO, BigDecimal::add);
        addTableRow(cajaTable, new String[]{"TOTAL", "$" + formatNumber(totEgresos), "$" + formatNumber(totIngresos),
            String.valueOf(cajaData.stream().mapToInt(r -> Integer.parseInt(r[3])).sum()),
            "$" + formatNumber(totEgresos.subtract(totIngresos))}, true);
        doc.add(cajaTable);

        doc.newPage();

        // ==================== UNIDADES POR MODELO ====================
        addSection(doc, "5. INVENTARIO DE UNIDADES POR MODELO");
        addBody(doc, "Catalogo de unidades activas en el sistema, agrupadas por marca y modelo. Datos de UNIDADESTA.");
        doc.add(new Paragraph(" "));

        if (unidData.size() > 0) {
            Image chart4 = chartToImage(createPieChart("Distribucion de Unidades", unidData), 450, 250);
            doc.add(chart4);
            doc.add(new Paragraph(" "));
        }

        PdfPTable unidTable = new PdfPTable(3);
        unidTable.setWidthPercentage(100);
        unidTable.setWidths(new float[]{40, 35, 25});
        addTableHeader(unidTable, new String[]{"MARCA", "MODELO/AÑO", "CANTIDAD"});
        for (String[] row : unidData) {
            addTableRow(unidTable, new String[]{row[0], row[1], row[2]}, false);
        }
        int totalUnid = unidData.stream().mapToInt(r -> Integer.parseInt(r[2])).sum();
        addTableRow(unidTable, new String[]{"TOTAL UNIDADES", "", String.valueOf(totalUnid)}, true);
        doc.add(unidTable);

        doc.newPage();

        // ==================== RESUMEN COMPARATIVO ====================
        addSection(doc, "6. RESUMEN COMPARATIVO POR MODELO");
        addBody(doc, "Comparacion consolidada de todos los gastos por modelo de unidad.");
        doc.add(new Paragraph(" "));

        // Merge data by model
        Map<String, BigDecimal[]> consolidated = new TreeMap<>();
        for (String[] row : otData) {
            consolidated.computeIfAbsent(row[0], k -> new BigDecimal[]{BigDecimal.ZERO, BigDecimal.ZERO, BigDecimal.ZERO});
            consolidated.get(row[0])[0] = new BigDecimal(row[2]);
        }
        for (String[] row : refData) {
            consolidated.computeIfAbsent(row[0], k -> new BigDecimal[]{BigDecimal.ZERO, BigDecimal.ZERO, BigDecimal.ZERO});
            consolidated.get(row[0])[1] = new BigDecimal(row[2]);
        }

        BigDecimal grandTotal = BigDecimal.ZERO;
        PdfPTable compTable = new PdfPTable(5);
        compTable.setWidthPercentage(100);
        compTable.setWidths(new float[]{28, 18, 20, 18, 16});
        addTableHeader(compTable, new String[]{"MODELO", "OTs + REF", "CAJA CHICA", "TOTAL", "%"});
        for (Map.Entry<String, BigDecimal[]> entry : consolidated.entrySet()) {
            String model = entry.getKey();
            BigDecimal otCost = entry.getValue()[0];
            BigDecimal refCost = entry.getValue()[1];
            BigDecimal modelTotal = otCost.add(refCost);
            grandTotal = grandTotal.add(modelTotal);
        }
        // Sort by total descending
        java.util.List<Map.Entry<String, BigDecimal[]>> sorted = new java.util.ArrayList<>(consolidated.entrySet());
        sorted.sort((a, b) -> {
            BigDecimal totalA = a.getValue()[0].add(a.getValue()[1]);
            BigDecimal totalB = b.getValue()[0].add(b.getValue()[1]);
            return totalB.compareTo(totalA);
        });
        grandTotal = BigDecimal.ZERO;
        for (Map.Entry<String, BigDecimal[]> entry : sorted) {
            BigDecimal modelTotal = entry.getValue()[0].add(entry.getValue()[1]);
            grandTotal = grandTotal.add(modelTotal);
        }
        BigDecimal finalGrand = grandTotal;
        for (Map.Entry<String, BigDecimal[]> entry : sorted) {
            BigDecimal modelTotal = entry.getValue()[0].add(entry.getValue()[1]);
            BigDecimal pct = finalGrand.compareTo(BigDecimal.ZERO) > 0 ?
                modelTotal.multiply(new BigDecimal(100)).divide(finalGrand, 1, RoundingMode.HALF_UP) : BigDecimal.ZERO;
            addTableRow(compTable, new String[]{entry.getKey(),
                "$" + formatNumber(entry.getValue()[0]),
                "-", "$" + formatNumber(modelTotal), pct + "%"}, false);
        }
        addTableRow(compTable, new String[]{"TOTAL GENERAL", "$" + formatNumber(grandTotal), "$" + formatNumber(totCaja),
            "$" + formatNumber(grandTotal.add(totCaja)), "100%"}, true);
        doc.add(compTable);

        doc.add(new Paragraph(" "));
        addCenter(doc, "Fin del Reporte", SMALL);
        addCenter(doc, "Generado automaticamente desde AS/400 EDGAR | " +
            new java.text.SimpleDateFormat("dd/MM/yyyy HH:mm:ss").format(new java.util.Date()), SMALL);

        doc.close();
    }

    // ===== CHARTS =====
    static JFreeChart createBarChart(String title, java.util.List<String[]> data, int valueCol) {
        DefaultCategoryDataset ds = new DefaultCategoryDataset();
        int limit = Math.min(data.size(), 15);
        for (int i = 0; i < limit; i++) {
            String[] row = data.get(i);
            ds.addValue(new BigDecimal(row[valueCol]), "Gastos", row[0]);
        }
        JFreeChart ch = ChartFactory.createBarChart(title, "", "Monto ($)", ds, PlotOrientation.VERTICAL, false, true, false);
        ch.setBackgroundPaint(java.awt.Color.WHITE);
        ch.getTitle().setFont(new java.awt.Font("Dialog", java.awt.Font.BOLD, 12));
        CategoryPlot p = ch.getCategoryPlot();
        p.setBackgroundPaint(new java.awt.Color(248, 250, 252));
        p.setRangeGridlinePaint(new java.awt.Color(200, 210, 225));
        p.getDomainAxis().setTickLabelFont(new java.awt.Font("Dialog", java.awt.Font.PLAIN, 8));
        p.getRangeAxis().setTickLabelFont(new java.awt.Font("Dialog", java.awt.Font.PLAIN, 8));
        BarRenderer r = (BarRenderer) p.getRenderer();
        r.setSeriesPaint(0, new java.awt.Color(56, 120, 255));
        r.setDrawBarOutline(false);
        return ch;
    }

    static JFreeChart createPieChart(String title, java.util.List<String[]> data) {
        DefaultPieDataset ds = new DefaultPieDataset();
        int limit = Math.min(data.size(), 10);
        for (int i = 0; i < limit; i++) {
            ds.setValue(data.get(i)[0] + " " + data.get(i)[1], Double.parseDouble(data.get(i)[2]));
        }
        JFreeChart ch = ChartFactory.createPieChart(title, ds, true, false, false);
        ch.setBackgroundPaint(java.awt.Color.WHITE);
        PiePlot p = (PiePlot) ch.getPlot();
        p.setBackgroundPaint(new java.awt.Color(248, 250, 252));
        p.setSectionOutlinesVisible(false);
        p.setLabelFont(new java.awt.Font("Dialog", java.awt.Font.PLAIN, 8));
        p.setInteriorGap(0.25);
        java.awt.Color[] colors = {new java.awt.Color(56, 120, 255), new java.awt.Color(239, 68, 68),
            new java.awt.Color(16, 185, 129), new java.awt.Color(139, 92, 246), new java.awt.Color(245, 158, 11),
            new java.awt.Color(236, 72, 153), new java.awt.Color(20, 184, 166), new java.awt.Color(99, 102, 241),
            new java.awt.Color(244, 63, 94), new java.awt.Color(34, 197, 94)};
        for (int i = 0; i < limit; i++) {
            p.setSectionPaint((Comparable) ds.getKey(i), colors[i % colors.length]);
        }
        return ch;
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
    static String formatNumber(BigDecimal n) {
        if (n == null) return "0.00";
        return n.setScale(2, RoundingMode.HALF_UP).toString().replaceAll("(\\d)(?=(\\d{3})+(?!\\d))", "$1,");
    }

    static void addCenter(Document doc, String text, Font f) throws Exception {
        Paragraph p = new Paragraph(text, f);
        p.setAlignment(Element.ALIGN_CENTER);
        doc.add(p);
    }

    static void addSection(Document doc, String text) throws Exception {
        Paragraph p = new Paragraph(text, SUBTITLE);
        p.setSpacingAfter(8);
        doc.add(p);
    }

    static void addBody(Document doc, String text) {
        Paragraph p = new Paragraph(text, BODY);
        p.setSpacingAfter(3);
        doc.add(p);
    }

    static PdfPCell createKPI(String label, String value, String sub) {
        PdfPCell cell = new PdfPCell();
        cell.addElement(new Paragraph(label, new Font(Font.HELVETICA, 8, Font.NORMAL, new Color(100, 116, 139))));
        cell.addElement(new Paragraph(value, new Font(Font.HELVETICA, 14, Font.BOLD, new Color(56, 120, 255))));
        cell.addElement(new Paragraph(sub, new Font(Font.HELVETICA, 8, Font.NORMAL, new Color(100, 116, 139))));
        cell.setBackgroundColor(new Color(248, 250, 252));
        cell.setBorderColor(new Color(226, 232, 240));
        cell.setBorderWidth(1);
        cell.setPadding(10);
        cell.setHorizontalAlignment(Element.ALIGN_CENTER);
        return cell;
    }

    static void addTableHeader(PdfPTable table, String[] headers) {
        for (String h : headers) {
            PdfPCell cell = new PdfPCell(new Phrase(h, WHITE_FONT));
            cell.setBackgroundColor(new Color(30, 41, 59));
            cell.setPadding(6);
            table.addCell(cell);
        }
    }

    static void addTableRow(PdfPTable table, String[] cells, boolean bold) {
        for (int i = 0; i < cells.length; i++) {
            Font f = (i == 0 || bold) ? BODY_BOLD : BODY;
            if (i == cells.length - 1 && cells[i].startsWith("$")) f = bold ? MONEY_BOLD : MONEY;
            PdfPCell cell = new PdfPCell(new Phrase(cells[i], f));
            cell.setPadding(5);
            cell.setBorderColor(new Color(226, 232, 240));
            if (bold) cell.setBackgroundColor(new Color(240, 245, 255));
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
                cb.showText("GASTOS POR MODELO - EDGAR  |  CONFIDENCIAL");
                cb.endText();
                cb.setColorStroke(new Color(200, 210, 225));
                cb.moveTo(doc.left(), doc.bottom() - 8);
                cb.lineTo(doc.right(), doc.bottom() - 8);
                cb.stroke();
                cb.beginText();
                cb.setTextMatrix(doc.left(), doc.bottom() - 20);
                cb.showText("TAC Software Solutions  |  AS/400 192.168.0.240  |  " + new java.text.SimpleDateFormat("dd/MM/yyyy HH:mm").format(new java.util.Date()));
                cb.endText();
                cb.beginText();
                String pg = "Pag. " + doc.getPageNumber();
                cb.setTextMatrix(doc.right() - bf.getWidthPoint(pg, 7), doc.bottom() - 20);
                cb.showText(pg);
                cb.endText();
            } catch (Exception e) { }
            cb.restoreState();
        }
    }
}
