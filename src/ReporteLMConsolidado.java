import com.lowagie.text.*;
import com.lowagie.text.pdf.*;
import java.awt.Color;
import java.io.FileOutputStream;
import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.List;

/**
 * PDF consolidado: GASTOS POR MARCA/MODELO - LAST MILE
 * Columnas: MARCA, MODELO, UNIDADES, GASTOS OT, GASTOS REF, TOTAL
 * + Gráficas de marcas con más gastos
 */
public class ReporteLMConsolidado {

    // Colores corporativos
    static final Color AZUL = new Color(0, 51, 102);
    static final Color AZUL_CLARO = new Color(0, 102, 178);
    static final Color VERDE = new Color(0, 153, 76);
    static final Color NARANJA = new Color(204, 102, 0);
    static final Color ROJO = new Color(180, 30, 30);
    static final Color GRIS_OSCURO = new Color(50, 50, 50);
    static final Color GRIS_CLARO = new Color(240, 242, 245);
    static final Color BLANCO = Color.WHITE;

    // BaseFont para cb.setFontAndSize()
    static BaseFont bf;
    static BaseFont bfBold;

    public static void generar(List<String[]> rows, List<String[]> marcas, BigDecimal grandTotal, int grandUnid) {
        try {
            bf = BaseFont.createFont(BaseFont.HELVETICA, BaseFont.WINANSI, BaseFont.NOT_EMBEDDED);
            bfBold = BaseFont.createFont(BaseFont.HELVETICA_BOLD, BaseFont.WINANSI, BaseFont.NOT_EMBEDDED);

            Document doc = new Document(PageSize.LETTER.rotate(), 30, 30, 30, 30);
            PdfWriter writer = PdfWriter.getInstance(doc, new FileOutputStream(
                "C:\\Users\\Sistemas\\as400\\Gastos_LastMile_Consolidado.pdf"));
            doc.open();

            PdfContentByte cb = writer.getDirectContent();

            // ==================== PAGINA 1: RESUMEN EJECUTIVO ====================
            drawHeader(cb, "REPORTE DE GASTOS POR MARCA Y MODELO", "UNIDADES LAST MILE (ENTREGA)", "Periodo: 2020 - 2026");

            float y = 720;

            // KPI Cards
            drawKpiCard(cb, "TOTAL GASTOS", "$" + formatNum(grandTotal), 40, y - 50, 160, 55, AZUL);
            drawKpiCard(cb, "TOTAL UNIDADES", String.valueOf(grandUnid) + " uni.", 220, y - 50, 160, 55, VERDE);
            drawKpiCard(cb, "MODELOS", String.valueOf(rows.size()), 400, y - 50, 160, 55, NARANJA);
            drawKpiCard(cb, "MARCAS", String.valueOf(marcas.size()), 580, y - 50, 160, 55, ROJO);

            y -= 80;

            // ==================== TABLA CONSOLIDADA ====================
            drawSectionTitle(cb, "DETALLE POR MARCA Y MODELO", 40, y);
            y -= 25;

            // Encabezados de tabla
            float[] widths = {130, 130, 60, 80, 80, 90};
            String[] headers = {"MARCA", "MODELO", "UNID.", "GASTO OT", "GASTO REF", "TOTAL"};
            float x = 40;
            float tableWidth = 0;
            for (float w : widths) tableWidth += w;

            // Header row
            cb.setColorFill(AZUL);
            cb.rectangle(40, y - 18, tableWidth, 20);
            cb.fill();
            cb.setColorFill(BLANCO);
            cb.setFontAndSize(bfBold, 8);
            x = 40;
            for (int i = 0; i < headers.length; i++) {
                drawCell(cb, headers[i], x, y - 15, widths[i], Element.ALIGN_CENTER);
                x += widths[i];
            }
            y -= 20;

            // Data rows
            int row = 0;
            for (String[] r : rows) {
                if (y < 60) {
                    doc.newPage();
                    y = 760;
                    cb.setColorFill(AZUL);
                    cb.rectangle(40, y - 18, tableWidth, 20);
                    cb.fill();
                    cb.setColorFill(BLANCO);
                    cb.setFontAndSize(bfBold, 8);
                    x = 40;
                    for (int i = 0; i < headers.length; i++) {
                        drawCell(cb, headers[i], x, y - 15, widths[i], Element.ALIGN_CENTER);
                        x += widths[i];
                    }
                    y -= 20;
                }

                Color bgColor = (row % 2 == 0) ? GRIS_CLARO : BLANCO;
                cb.setColorFill(bgColor);
                cb.rectangle(40, y - 16, tableWidth, 18);
                cb.fill();
                cb.setColorFill(GRIS_OSCURO);
                cb.setFontAndSize(bf, 7.5f);

                x = 40;
                drawCell(cb, r[0], x, y - 13, widths[0], Element.ALIGN_LEFT); x += widths[0];
                drawCell(cb, r[1], x, y - 13, widths[1], Element.ALIGN_LEFT); x += widths[1];
                drawCell(cb, r[2], x, y - 13, widths[2], Element.ALIGN_CENTER); x += widths[2];
                drawCell(cb, "$" + formatDbl(r[3]), x, y - 13, widths[3], Element.ALIGN_RIGHT); x += widths[3];
                drawCell(cb, "$" + formatDbl(r[4]), x, y - 13, widths[4], Element.ALIGN_RIGHT); x += widths[4];
                cb.setFontAndSize(bfBold, 7.5f);
                drawCell(cb, "$" + formatDbl(r[5]), x, y - 13, widths[5], Element.ALIGN_RIGHT); x += widths[5];
                cb.setFontAndSize(bf, 7.5f);
                y -= 18;
                row++;
            }

            // Fila total
            y -= 4;
            cb.setColorFill(AZUL);
            cb.rectangle(40, y - 18, tableWidth, 20);
            cb.fill();
            cb.setColorFill(BLANCO);
            cb.setFontAndSize(bfBold, 8);
            x = 40;
            drawCell(cb, "TOTAL GENERAL", x, y - 15, widths[0] + widths[1], Element.ALIGN_LEFT); x += widths[0] + widths[1];
            drawCell(cb, String.valueOf(grandUnid), x, y - 15, widths[2], Element.ALIGN_CENTER); x += widths[2];
            drawCell(cb, "", x, y - 15, widths[3], Element.ALIGN_CENTER); x += widths[3];
            drawCell(cb, "", x, y - 15, widths[4], Element.ALIGN_CENTER); x += widths[4];
            drawCell(cb, "$" + formatNum(grandTotal), x, y - 15, widths[5], Element.ALIGN_RIGHT);

            // ==================== PAGINA 2: GRAFICAS ====================
            doc.newPage();
            drawHeader(cb, "ANALISIS DE GASTOS POR MARCA", "DISTRIBUCION Y TENDENCIAS", "Last Mile - Unidades con prefijo W");

            y = 710;

            // --- GRAFICA 1: BARRAS HORIZONTALES - Gastos por marca ---
            drawSectionTitle(cb, "GASTOS POR MARCA (BARRAS)", 40, y);
            y -= 20;

            if (marcas.size() > 0) {
                BigDecimal maxTotal = marcas.get(0) != null ? new BigDecimal(marcas.get(0)[2]) : BigDecimal.ONE;
                float barMaxWidth = 350;
                float barHeight = 22;
                float barY = y;
                String[] coloresHex = {"#0066B2", "#00994C", "#CC6600", "#B41E1E", "#7B2D8E"};

                for (int i = 0; i < Math.min(marcas.size(), 8); i++) {
                    String[] m = marcas.get(i);
                    BigDecimal total = new BigDecimal(m[2]);
                    float barW = maxTotal.compareTo(BigDecimal.ZERO) > 0 ?
                        (float)(total.doubleValue() / maxTotal.doubleValue() * barMaxWidth) : 0;

                    int colorIdx = i % coloresHex.length;
                    Color barColor = hexToColor(coloresHex[colorIdx]);

                    // Label
                    cb.setColorFill(GRIS_OSCURO);
                    cb.setFontAndSize(bf, 8);
                    drawCell(cb, m[0], 40, barY - 14, 150, Element.ALIGN_LEFT);
                    drawCell(cb, m[1] + " uni", 190, barY - 14, 50, Element.ALIGN_CENTER);

                    // Bar
                    cb.setColorFill(barColor);
                    cb.roundRectangle(245, barY - 16, barW, barHeight, 3);
                    cb.fill();

                    // Value
                    cb.setColorFill(GRIS_OSCURO);
                    cb.setFontAndSize(bf, 7.5f);
                    drawCell(cb, "$" + formatNum(total), 250 + barW, barY - 14, 100, Element.ALIGN_LEFT);

                    barY -= 30;
                }
                y = barY - 15;
            }

            // --- GRAFICA 2: BARRAS - Gastos por modelo (Top 8) ---
            drawSectionTitle(cb, "TOP 8 MODELOS POR GASTOS", 40, y);
            y -= 20;

            if (rows.size() > 0) {
                BigDecimal maxModelo = new BigDecimal(rows.get(0)[5]);
                float barMaxW = 350;
                String[] coloresHex2 = {"#0066B2", "#00994C", "#CC6600", "#B41E1E", "#7B2D8E", "#00A3A3", "#CC3399", "#666600"};

                for (int i = 0; i < Math.min(rows.size(), 8); i++) {
                    String[] r = rows.get(i);
                    BigDecimal total = new BigDecimal(r[5]);
                    float barW = maxModelo.compareTo(BigDecimal.ZERO) > 0 ?
                        (float)(total.doubleValue() / maxModelo.doubleValue() * barMaxW) : 0;
                    Color barColor = hexToColor(coloresHex2[i % coloresHex2.length]);

                    cb.setColorFill(GRIS_OSCURO);
                    cb.setFontAndSize(bf, 8);
                    drawCell(cb, r[0] + " " + r[1], 40, y - 14, 200, Element.ALIGN_LEFT);

                    cb.setColorFill(barColor);
                    cb.roundRectangle(245, y - 16, barW, 20, 3);
                    cb.fill();

                    cb.setFontAndSize(bf, 7.5f);
                    drawCell(cb, r[2] + " uni | $" + formatNum(total), 250 + barW, y - 14, 140, Element.ALIGN_LEFT);

                    y -= 28;
                }
            }

            // --- PAGINA 3: TABLA RESUMEN POR MARCA ---
            doc.newPage();
            drawHeader(cb, "RESUMEN POR MARCA", "AGREGADO DE GASTOS Y UNIDADES", "Last Mile");
            y = 720;

            drawSectionTitle(cb, "TABLA RESUMEN POR MARCA", 40, y);
            y -= 25;

            // Header
            float[] wm = {180, 100, 140, 140};
            String[] hm = {"MARCA", "UNIDADES", "TOTAL GASTOS", "% DEL TOTAL"};
            float twm = 0; for (float w : wm) twm += w;

            cb.setColorFill(AZUL);
            cb.rectangle(40, y - 18, twm, 20);
            cb.fill();
            cb.setColorFill(BLANCO);
            cb.setFontAndSize(bf, 9);
            x = 40;
            for (int i = 0; i < hm.length; i++) {
                drawCell(cb, hm[i], x, y - 15, wm[i], Element.ALIGN_CENTER);
                x += wm[i];
            }
            y -= 20;

            row = 0;
            for (String[] m : marcas) {
                BigDecimal total = new BigDecimal(m[2]);
                BigDecimal pct = grandTotal.compareTo(BigDecimal.ZERO) > 0 ?
                    total.multiply(new BigDecimal(100)).divide(grandTotal, 1, RoundingMode.HALF_UP) : BigDecimal.ZERO;

                Color bg = (row % 2 == 0) ? GRIS_CLARO : BLANCO;
                cb.setColorFill(bg);
                cb.rectangle(40, y - 16, twm, 18);
                cb.fill();
                cb.setColorFill(GRIS_OSCURO);
                cb.setFontAndSize(bf, 8);

                x = 40;
                drawCell(cb, m[0], x, y - 13, wm[0], Element.ALIGN_LEFT); x += wm[0];
                drawCell(cb, m[1], x, y - 13, wm[1], Element.ALIGN_CENTER); x += wm[1];
                cb.setFontAndSize(bfBold, 8);
                drawCell(cb, "$" + formatNum(total), x, y - 13, wm[2], Element.ALIGN_RIGHT); x += wm[2];
                cb.setFontAndSize(bf, 8);

                // Barra de porcentaje
                float barW2 = (float)(pct.doubleValue() / 100.0 * 80);
                cb.setColorFill(hexToColor("#0066B2"));
                cb.roundRectangle(x + 5, y - 14, barW2, 14, 2);
                cb.fill();
                cb.setColorFill(BLANCO);
                drawCell(cb, pct + "%", x + 5, y - 13, barW2, Element.ALIGN_CENTER);

                y -= 18;
                row++;
            }

            // Total
            y -= 4;
            cb.setColorFill(AZUL);
            cb.rectangle(40, y - 18, twm, 20);
            cb.fill();
            cb.setColorFill(BLANCO);
            cb.setFontAndSize(bfBold, 9);
            x = 40;
            drawCell(cb, "TOTAL GENERAL", x, y - 15, wm[0], Element.ALIGN_LEFT); x += wm[0];
            drawCell(cb, String.valueOf(grandUnid), x, y - 15, wm[1], Element.ALIGN_CENTER); x += wm[1];
            drawCell(cb, "$" + formatNum(grandTotal), x, y - 15, wm[2], Element.ALIGN_RIGHT); x += wm[2];
            drawCell(cb, "100%", x, y - 15, wm[3], Element.ALIGN_CENTER);

            // Pie de pagina
            drawFooter(cb);

            doc.close();
            System.out.println("PDF generado correctamente.");

        } catch (Exception e) {
            System.err.println("Error: " + e.getMessage());
            e.printStackTrace();
        }
    }

    // ==================== METODOS DE DIBUJO ====================

    static void drawHeader(PdfContentByte cb, String title, String subtitle, String period) {
        cb.setColorFill(AZUL);
        cb.rectangle(0, 780, 792, 55);
        cb.fill();
        cb.setColorFill(BLANCO);
        cb.setFontAndSize(bfBold, 16);
        showText(cb, title, 380, 808, Element.ALIGN_CENTER);
        cb.setFontAndSize(bf, 10);
        showText(cb, subtitle + "  |  " + period, 380, 795, Element.ALIGN_CENTER);
    }

    static void drawSectionTitle(PdfContentByte cb, String text, float x, float y) {
        cb.setColorFill(AZUL_CLARO);
        cb.roundRectangle(x - 3, y - 3, 300, 16, 3);
        cb.fill();
        cb.setColorFill(BLANCO);
        cb.setFontAndSize(bfBold, 9);
        showText(cb, text, x + 145, y + 1, Element.ALIGN_CENTER);
    }

    static void drawKpiCard(PdfContentByte cb, String label, String value, float x, float y, float w, float h, Color color) {
        cb.setColorFill(color);
        cb.roundRectangle(x, y, w, h, 5);
        cb.fill();
        cb.setColorFill(BLANCO);
        cb.setFontAndSize(bf, 7);
        showText(cb, label, x + w / 2, y + h - 14, Element.ALIGN_CENTER);
        cb.setFontAndSize(bfBold, 11);
        showText(cb, value, x + w / 2, y + 10, Element.ALIGN_CENTER);
    }

    static void drawCell(PdfContentByte cb, String text, float x, float y, float width, int align) {
        ColumnText ct = new ColumnText(cb);
        ct.setSimpleColumn(new Phrase(text, getFont()), x, y - 5, x + width, y + 10, 12, align);
        try { ct.go(); } catch (Exception e) {}
    }

    static void showText(PdfContentByte cb, String text, float x, float y, int align) {
        ColumnText ct = new ColumnText(cb);
        Phrase phrase = new Phrase(text, getFont());
        ct.setSimpleColumn(phrase, x - 200, y - 5, x + 200, y + 10, 12, align);
        try { ct.go(); } catch (Exception e) {}
    }

    static void drawFooter(PdfContentByte cb) {
        cb.setColorFill(GRIS_CLARO);
        cb.rectangle(0, 0, 792, 25);
        cb.fill();
        cb.setColorFill(GRIS_OSCURO);
        cb.setFontAndSize(bf, 7);
        showText(cb, "Generado por Sistema Integral AS/400  |  Datos reales del servidor 192.168.0.240  |  " + java.time.LocalDate.now(), 380, 8, Element.ALIGN_CENTER);
    }

    // ==================== UTILIDADES ====================

    static Font getFont() {
        return FontFactory.getFont(FontFactory.HELVETICA, 8, Font.NORMAL, GRIS_OSCURO);
    }
    static Font getFontBold() {
        return FontFactory.getFont(FontFactory.HELVETICA_BOLD, 8, Font.NORMAL, GRIS_OSCURO);
    }

    static String formatNum(BigDecimal n) {
        return n.setScale(0, RoundingMode.HALF_UP)
            .toString().replaceAll("(\\d)(?=(\\d{3})+(?!\\d))", "$1,");
    }
    static String formatDbl(String s) {
        try { return formatNum(new BigDecimal(s)); } catch (Exception e) { return s; }
    }

    static Color hexToColor(String hex) {
        hex = hex.replace("#", "");
        return new Color(
            Integer.parseInt(hex.substring(0, 2), 16),
            Integer.parseInt(hex.substring(2, 4), 16),
            Integer.parseInt(hex.substring(4, 6), 16));
    }
}
