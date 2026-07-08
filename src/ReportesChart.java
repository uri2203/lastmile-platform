import org.jfree.chart.*;
import org.jfree.chart.axis.*;
import org.jfree.chart.labels.*;
import org.jfree.chart.plot.*;
import org.jfree.chart.renderer.category.*;
import org.jfree.chart.renderer.xy.*;
import org.jfree.chart.util.Rotation;
import org.jfree.data.category.*;
import org.jfree.data.general.*;
import org.jfree.data.xy.*;
import javax.swing.*;
import javax.swing.border.*;
import javax.swing.table.*;
import java.awt.*;
import java.awt.event.*;
import java.util.*;

public class ReportesChart {

    static final Color BG = new Color(12, 18, 32);
    static final Color SURF = new Color(18, 25, 45);
    static final Color SURF2 = new Color(24, 34, 56);
    static final Color SURF3 = new Color(32, 44, 68);
    static final Color INP = new Color(15, 22, 38);
    static final Color T1 = new Color(248, 250, 252);
    static final Color T2 = new Color(186, 198, 218);
    static final Color T3 = new Color(120, 140, 170);
    static final Color T4 = new Color(71, 85, 105);
    static final Color BLUE = new Color(56, 120, 255);
    static final Color GREEN = new Color(16, 185, 129);
    static final Color RED = new Color(239, 68, 68);
    static final Color AMBER = new Color(245, 158, 11);
    static final Color PURPLE = new Color(139, 92, 246);
    static final Color CYAN = new Color(6, 182, 212);
    static final Color BR = new Color(40, 55, 80);
    static Color[] PAL = {BLUE, GREEN, PURPLE, AMBER, CYAN, RED, new Color(249,115,22), new Color(20,184,166)};

    static Font FTitle = new Font("Segoe UI", Font.BOLD, 18);
    static Font FSub = new Font("Segoe UI", Font.PLAIN, 12);
    static Font FBold = new Font("Segoe UI", Font.BOLD, 12);
    static Font FNormal = new Font("Segoe UI", Font.PLAIN, 12);
    static Font FSmall = new Font("Segoe UI", Font.PLAIN, 11);

    // ====== UTILITIES ======
    static JPanel mkScreen(String title, String sub) {
        JPanel p = new JPanel(new BorderLayout(0, 0));
        p.setBackground(BG);
        return p;
    }

    static JPanel mkTopBar(String title, String sub, Component... extra) {
        JPanel bar = new JPanel(new BorderLayout());
        bar.setBackground(SURF);
        bar.setBorder(BorderFactory.createCompoundBorder(
            BorderFactory.createMatteBorder(0,0,1,0,BR),
            BorderFactory.createEmptyBorder(18,28,18,28)));
        JPanel left = new JPanel(new BorderLayout());
        left.setOpaque(false);
        JLabel t = new JLabel(title);
        t.setFont(FTitle);
        t.setForeground(T1);
        JLabel s = new JLabel(sub);
        s.setFont(FSub);
        s.setForeground(T3);
        left.add(t, BorderLayout.NORTH);
        left.add(s, BorderLayout.SOUTH);
        bar.add(left, BorderLayout.WEST);
        if (extra.length > 0) {
            JPanel right = new JPanel(new FlowLayout(FlowLayout.RIGHT, 10, 0));
            right.setOpaque(false);
            for (Component c : extra) right.add(c);
            bar.add(right, BorderLayout.EAST);
        }
        return bar;
    }

    static JButton mkFilter(String text, Color bg) {
        JButton b = new JButton(text) {
            boolean h = false;
            { addMouseListener(new MouseAdapter() { public void mouseEntered(MouseEvent e) { h=true; repaint(); } public void mouseExited(MouseEvent e) { h=false; repaint(); } }); }
            protected void paintComponent(Graphics g) {
                Graphics2D g2 = (Graphics2D) g.create();
                g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
                g2.setColor(h ? bg.brighter() : bg);
                g2.fillRoundRect(0,0,getWidth(),getHeight(),8,8);
                g2.dispose();
                super.paintComponent(g);
            }
        };
        b.setForeground(Color.WHITE);
        b.setFont(FBold);
        b.setPreferredSize(new Dimension(110, 34));
        b.setFocusPainted(false); b.setBorderPainted(false); b.setContentAreaFilled(false); b.setOpaque(false);
        b.setCursor(Cursor.getPredefinedCursor(Cursor.HAND_CURSOR));
        return b;
    }

    static JPanel mkTable(java.util.List<HashMap<String,String>> data, String[] cols, String[] keys) {
        DefaultTableModel m = new DefaultTableModel(cols, 0) {
            public boolean isCellEditable(int r, int c) { return false; }
        };
        for (HashMap<String,String> row : data) {
            Object[] vals = new Object[cols.length];
            for (int i = 0; i < keys.length; i++) vals[i] = row.get(keys[i].toLowerCase()) != null ? row.get(keys[i].toLowerCase()) : "";
            m.addRow(vals);
        }
        JTable t = new JTable(m);
        t.setFont(FNormal);
        t.setRowHeight(36);
        t.setBackground(BG);
        t.setForeground(T1);
        t.setSelectionBackground(BLUE);
        t.setSelectionForeground(Color.WHITE);
        t.setGridColor(BR);
        t.setShowGrid(true);
        t.setIntercellSpacing(new Dimension(0,1));
        t.getTableHeader().setFont(FBold);
        t.getTableHeader().setBackground(SURF2);
        t.getTableHeader().setForeground(T2);
        t.getTableHeader().setPreferredSize(new Dimension(0,40));
        t.getTableHeader().setBorder(new MatteBorder(0,0,2,0,BLUE));
        t.setDefaultRenderer(Object.class, new DefaultTableCellRenderer() {
            public Component getTableCellRendererComponent(JTable tb, Object val, boolean sel, boolean foc, int row, int col) {
                JLabel c = (JLabel)super.getTableCellRendererComponent(tb, val, sel, foc, row, col);
                if (!sel) c.setBackground(row%2==0 ? BG : SURF);
                c.setBorder(BorderFactory.createEmptyBorder(0,12,0,12));
                String v = String.valueOf(val);
                if (v.startsWith("$")) { c.setForeground(BLUE); c.setFont(new Font("Segoe UI",Font.BOLD,12)); c.setHorizontalAlignment(SwingConstants.RIGHT); }
                else if (v.contains("\u2714")) { c.setForeground(GREEN); c.setFont(FBold); }
                else if (v.contains("\u23F3")) { c.setForeground(AMBER); c.setFont(FBold); }
                else if (v.contains("\u2716")) { c.setForeground(RED); c.setFont(FBold); }
                else { c.setForeground(T1); c.setFont(FNormal); c.setHorizontalAlignment(SwingConstants.LEFT); }
                return c;
            }
        });
        JScrollPane sc = new JScrollPane(t);
        sc.setBorder(BorderFactory.createEmptyBorder());
        sc.getViewport().setBackground(BG);
        JPanel wrapper = new JPanel(new BorderLayout());
        wrapper.setBackground(BG);
        wrapper.add(sc, BorderLayout.CENTER);
        JLabel cnt = new JLabel("  " + data.size() + " registros");
        cnt.setForeground(T4); cnt.setFont(FSmall);
        cnt.setBorder(BorderFactory.createEmptyBorder(6,10,6,0));
        wrapper.add(cnt, BorderLayout.SOUTH);
        return wrapper;
    }

    static JPanel mkChartPanel(JFreeChart ch, int w, int h) {
        ChartPanel cp = new ChartPanel(ch);
        cp.setPreferredSize(new Dimension(w, h));
        cp.setMinimumSize(new Dimension(400, 300));
        cp.setOpaque(false);
        cp.setBorder(BorderFactory.createLineBorder(BR, 1));
        JPanel wrap = new JPanel(new BorderLayout());
        wrap.setBackground(SURF);
        wrap.setBorder(BorderFactory.createEmptyBorder(10,10,10,10));
        wrap.add(cp, BorderLayout.CENTER);
        return wrap;
    }

    // ====== REPORTE 1: VENTAS MENSUALES ======
    static JPanel rptVentasMensuales() {
        JPanel screen = mkScreen("Ventas Mensuales", "");
        String[] meses = {"Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic"};
        JComboBox<String> cmbYear = new JComboBox<>(new String[]{"2020","2021","2022","2023","2024","2025","2026"});
        cmbYear.setSelectedItem("2026");
        cmbYear.setBackground(INP); cmbYear.setForeground(T1); cmbYear.setFont(FNormal);
        cmbYear.setPreferredSize(new Dimension(100,34));
        JButton btnFiltrar = mkFilter("Consultar", BLUE);
        JButton btnExport = mkFilter("Exportar", PURPLE);

        JPanel center = new JPanel(new GridLayout(1, 2, 15, 0));
        center.setBackground(BG);
        center.setBorder(BorderFactory.createEmptyBorder(15,20,15,20));

        JPanel tablePanel = new JPanel(new BorderLayout());
        tablePanel.setBackground(BG);
        JLabel tblTitle = new JLabel("Detalle de Ventas por Mes");
        tblTitle.setFont(FBold); tblTitle.setForeground(T2);
        tblTitle.setBorder(BorderFactory.createEmptyBorder(0,5,8,0));
        tablePanel.add(tblTitle, BorderLayout.NORTH);

        JPanel chartPanel = new JPanel(new BorderLayout());
        chartPanel.setBackground(BG);
        JLabel chTitle = new JLabel("Grafica de Ventas");
        chTitle.setFont(FBold); chTitle.setForeground(T2);
        chTitle.setBorder(BorderFactory.createEmptyBorder(0,5,8,0));
        chartPanel.add(chTitle, BorderLayout.NORTH);

        // Data holders
        final JPanel[] dataHolder = new JPanel[1];
        final JPanel[] chartHolder = new JPanel[1];

        Runnable loadData = () -> {
            String year = (String) cmbYear.getSelectedItem();
            ArrayList<HashMap<String,String>> data = AppAS400.queryList(
                "SELECT MONTH(FACFEC) AS MES, COALESCE(SUM(FACTOT),0) AS TOTAL, COUNT(*) AS FACTURAS FROM TESTLIB.FAC001 WHERE YEAR(FACFEC)=" + year + " GROUP BY MONTH(FACFEC) ORDER BY MONTH(FACFEC)");

            // Table
            String[] cols = {"MES", "VENTAS", "FACTURAS"};
            String[] keys = {"mes", "total", "facturas"};
            java.util.List<HashMap<String,String>> tableData = new java.util.ArrayList<>();
            for (HashMap<String,String> r : data) {
                HashMap<String,String> row = new HashMap<>();
                int m = Integer.parseInt(r.get("mes"));
                row.put("mes", meses[m-1]);
                row.put("total", String.format("$%,.2f", Double.parseDouble(r.get("total"))));
                row.put("facturas", r.get("facturas"));
                tableData.add(row);
            }
            if (dataHolder[0] != null) tablePanel.remove(dataHolder[0]);
            dataHolder[0] = mkTable(tableData, cols, keys);
            tablePanel.add(dataHolder[0], BorderLayout.CENTER);

            // Chart
            DefaultCategoryDataset ds = new DefaultCategoryDataset();
            for (HashMap<String,String> r : data) ds.addValue(Double.parseDouble(r.get("total")), "Ventas", meses[Integer.parseInt(r.get("mes"))-1]);
            JFreeChart ch = ChartFactory.createBarChart(null, "Mes", "Monto ($)", ds, PlotOrientation.VERTICAL, false, false, false);
            CategoryPlot p = ch.getCategoryPlot();
            p.setBackgroundPaint(SURF);
            p.setOutlinePaint(BR);
            p.setRangeGridlinePaint(BR);
            p.setDomainGridlinePaint(BR);
            p.getDomainAxis().setTickLabelFont(FSmall);
            p.getDomainAxis().setLabelFont(FNormal);
            p.getRangeAxis().setTickLabelFont(FSmall);
            p.getRangeAxis().setLabelFont(FNormal);
            BarRenderer r = (BarRenderer) p.getRenderer();
            r.setSeriesPaint(0, BLUE);
            r.setDrawBarOutline(false);
            r.setMaximumBarWidth(0.08);
            ch.setBackgroundPaint(BG);
            ch.getTitle().setPaint(T1);
            ch.getTitle().setFont(FTitle);
            if (chartHolder[0] != null) chartPanel.remove(chartHolder[0]);
            chartHolder[0] = mkChartPanel(ch, 600, 380);
            chartPanel.add(chartHolder[0], BorderLayout.CENTER);

            screen.revalidate();
            screen.repaint();
        };

        btnFiltrar.addActionListener(e -> loadData.run());
        loadData.run();

        screen.add(mkTopBar("Ventas Mensuales " + cmbYear.getSelectedItem(), "Comparativo de ingresos por mes", cmbYear, btnFiltrar, btnExport), BorderLayout.NORTH);
        screen.add(center, BorderLayout.CENTER);
        center.add(tablePanel);
        center.add(chartPanel);
        return screen;
    }

    // ====== REPORTE 2: TOP CLIENTES ======
    static JPanel rptTopClientes() {
        JPanel screen = mkScreen("Top Clientes", "");
        JComboBox<String> cmbTop = new JComboBox<>(new String[]{"5","10","15","20"});
        cmbTop.setSelectedItem("10");
        cmbTop.setBackground(INP); cmbTop.setForeground(T1); cmbTop.setFont(FNormal);
        cmbTop.setPreferredSize(new Dimension(80,34));
        JButton btnFiltrar = mkFilter("Consultar", BLUE);

        JPanel center = new JPanel(new GridLayout(1, 2, 15, 0));
        center.setBackground(BG);
        center.setBorder(BorderFactory.createEmptyBorder(15,20,15,20));

        JPanel tableP = new JPanel(new BorderLayout());
        tableP.setBackground(BG);
        JLabel t1 = new JLabel("Clientes con Mayor Volumen de Compra");
        t1.setFont(FBold); t1.setForeground(T2); t1.setBorder(BorderFactory.createEmptyBorder(0,5,8,0));
        tableP.add(t1, BorderLayout.NORTH);

        JPanel chartP = new JPanel(new BorderLayout());
        chartP.setBackground(BG);
        JLabel t2 = new JLabel("Comparativa de Compras");
        t2.setFont(FBold); t2.setForeground(T2); t2.setBorder(BorderFactory.createEmptyBorder(0,5,8,0));
        chartP.add(t2, BorderLayout.NORTH);

        final JPanel[] dH = new JPanel[1], cH = new JPanel[1];

        Runnable loadData = () -> {
            int top = Integer.parseInt((String)cmbTop.getSelectedItem());
            ArrayList<HashMap<String,String>> data = AppAS400.queryList(
                "SELECT C.CLINOM AS NOMBRE, C.CLICIUDAD AS CIUDAD, COALESCE(SUM(F.FACTOT),0) AS TOTAL, COUNT(*) AS COMPRA FROM TESTLIB.FAC001 F JOIN TESTLIB.CLI001 C ON F.CLICOD=C.CLICOD GROUP BY C.CLINOM, C.CLICIUDAD ORDER BY SUM(F.FACTOT) DESC FETCH FIRST " + top + " ROWS ONLY");

            String[] cols = {"CLIENTE", "CIUDAD", "TOTAL COMPRADO", "FACTURAS"};
            String[] keys = {"nombre", "ciudad", "total", "compra"};
            java.util.List<HashMap<String,String>> td = new java.util.ArrayList<>();
            for (HashMap<String,String> r : data) {
                HashMap<String,String> row = new HashMap<>();
                row.put("nombre", r.get("nombre"));
                row.put("ciudad", r.get("ciudad"));
                row.put("total", String.format("$%,.2f", Double.parseDouble(r.get("total"))));
                row.put("compra", r.get("compra"));
                td.add(row);
            }
            if (dH[0] != null) tableP.remove(dH[0]);
            dH[0] = mkTable(td, cols, keys);
            tableP.add(dH[0], BorderLayout.CENTER);

            DefaultCategoryDataset ds = new DefaultCategoryDataset();
            for (HashMap<String,String> r : data) {
                String n = r.get("nombre");
                ds.addValue(Double.parseDouble(r.get("total")), "Compras", n.length()>15 ? n.substring(0,15)+"..." : n);
            }
            JFreeChart ch = ChartFactory.createBarChart(null, "Cliente", "Monto ($)", ds, PlotOrientation.HORIZONTAL, false, false, false);
            CategoryPlot p = ch.getCategoryPlot();
            p.setBackgroundPaint(SURF); p.setOutlinePaint(BR); p.setRangeGridlinePaint(BR);
            p.getDomainAxis().setTickLabelFont(new Font("Segoe UI",Font.PLAIN,9));
            p.getRangeAxis().setTickLabelFont(FSmall);
            BarRenderer r = (BarRenderer) p.getRenderer();
            r.setSeriesPaint(0, GREEN); r.setDrawBarOutline(false); r.setMaximumBarWidth(0.06);
            ch.setBackgroundPaint(BG); ch.getTitle().setPaint(T1);
            if (cH[0] != null) chartP.remove(cH[0]);
            cH[0] = mkChartPanel(ch, 600, 380);
            chartP.add(cH[0], BorderLayout.CENTER);
            screen.revalidate(); screen.repaint();
        };

        btnFiltrar.addActionListener(e -> loadData.run());
        loadData.run();

        screen.add(mkTopBar("Top Clientes", "Mayores compradores del periodo", cmbTop, btnFiltrar), BorderLayout.NORTH);
        screen.add(center, BorderLayout.CENTER);
        center.add(tableP); center.add(chartP);
        return screen;
    }

    // ====== REPORTE 3: CATEGORIAS ======
    static JPanel rptCategorias() {
        JPanel screen = mkScreen("Distribucion por Categoria", "");
        JButton btnFiltrar = mkFilter("Actualizar", BLUE);

        JPanel center = new JPanel(new GridLayout(1, 2, 15, 0));
        center.setBackground(BG);
        center.setBorder(BorderFactory.createEmptyBorder(15,20,15,20));

        JPanel tableP = new JPanel(new BorderLayout());
        tableP.setBackground(BG);
        JLabel t1 = new JLabel("Ventas por Categoria de Producto");
        t1.setFont(FBold); t1.setForeground(T2); t1.setBorder(BorderFactory.createEmptyBorder(0,5,8,0));
        tableP.add(t1, BorderLayout.NORTH);

        JPanel chartP = new JPanel(new BorderLayout());
        chartP.setBackground(BG);
        JLabel t2 = new JLabel("Participacion por Categoria");
        t2.setFont(FBold); t2.setForeground(T2); t2.setBorder(BorderFactory.createEmptyBorder(0,5,8,0));
        chartP.add(t2, BorderLayout.NORTH);

        final JPanel[] dH = new JPanel[1], cH = new JPanel[1];

        Runnable loadData = () -> {
            ArrayList<HashMap<String,String>> data = AppAS400.queryList(
                "SELECT C.CATNOM AS CAT, COALESCE(SUM(F.FADTOT),0) AS TOTAL, COUNT(*) AS ITEMS FROM TESTLIB.FAD001 F JOIN TESTLIB.ART001 A ON F.ARTCOD=A.ARTCOD JOIN TESTLIB.CAT001 C ON A.CATCOD=C.CATCOD GROUP BY C.CATNOM ORDER BY SUM(F.FADTOT) DESC");

            double grandTotal = 0;
            for (HashMap<String,String> r : data) grandTotal += Double.parseDouble(r.get("total"));

            String[] cols = {"CATEGORIA", "VENTAS", "PARTICIPACION"};
            String[] keys = {"cat", "total", "part"};
            java.util.List<HashMap<String,String>> td = new java.util.ArrayList<>();
            for (HashMap<String,String> r : data) {
                HashMap<String,String> row = new HashMap<>();
                row.put("cat", r.get("cat"));
                row.put("total", String.format("$%,.2f", Double.parseDouble(r.get("total"))));
                double pct = grandTotal > 0 ? Double.parseDouble(r.get("total")) / grandTotal * 100 : 0;
                row.put("part", String.format("%.1f%%", pct));
                td.add(row);
            }
            if (dH[0] != null) tableP.remove(dH[0]);
            dH[0] = mkTable(td, cols, keys);
            tableP.add(dH[0], BorderLayout.CENTER);

            DefaultPieDataset ds = new DefaultPieDataset();
            for (HashMap<String,String> r : data) ds.setValue(r.get("cat"), Double.parseDouble(r.get("total")));
            JFreeChart ch = ChartFactory.createPieChart(null, ds, true, true, false);
            PiePlot pl = (PiePlot) ch.getPlot();
            pl.setBackgroundPaint(SURF); pl.setOutlinePaint(BR); pl.setSectionOutlinesVisible(false);
            pl.setLabelFont(new Font("Segoe UI",Font.BOLD,11)); pl.setLabelPaint(T1);
            pl.setLabelBackgroundPaint(SURF2); pl.setLabelOutlinePaint(BR);
            pl.setInteriorGap(0.30);
            int i = 0;
            for (Object key : ds.getKeys()) pl.setSectionPaint((String)key, PAL[i++ % PAL.length]);
            ch.setBackgroundPaint(BG); ch.getTitle().setPaint(T1);
            if (cH[0] != null) chartP.remove(cH[0]);
            cH[0] = mkChartPanel(ch, 600, 380);
            chartP.add(cH[0], BorderLayout.CENTER);
            screen.revalidate(); screen.repaint();
        };

        btnFiltrar.addActionListener(e -> loadData.run());
        loadData.run();

        screen.add(mkTopBar("Categorias", "Distribucion de ventas por tipo de producto", btnFiltrar), BorderLayout.NORTH);
        screen.add(center, BorderLayout.CENTER);
        center.add(tableP); center.add(chartP);
        return screen;
    }

    // ====== REPORTE 4: TENDENCIA ======
    static JPanel rptTendencia() {
        JPanel screen = mkScreen("Tendencia Historica", "");
        JButton btnFiltrar = mkFilter("Actualizar", BLUE);

        JPanel center = new JPanel(new GridLayout(1, 2, 15, 0));
        center.setBackground(BG);
        center.setBorder(BorderFactory.createEmptyBorder(15,20,15,20));

        JPanel tableP = new JPanel(new BorderLayout());
        tableP.setBackground(BG);
        JLabel t1 = new JLabel("Evolucion Anual de Ventas");
        t1.setFont(FBold); t1.setForeground(T2); t1.setBorder(BorderFactory.createEmptyBorder(0,5,8,0));
        tableP.add(t1, BorderLayout.NORTH);

        JPanel chartP = new JPanel(new BorderLayout());
        chartP.setBackground(BG);
        JLabel t2 = new JLabel("Grafica de Tendencia");
        t2.setFont(FBold); t2.setForeground(T2); t2.setBorder(BorderFactory.createEmptyBorder(0,5,8,0));
        chartP.add(t2, BorderLayout.NORTH);

        final JPanel[] dH = new JPanel[1], cH = new JPanel[1];

        Runnable loadData = () -> {
            ArrayList<HashMap<String,String>> data = AppAS400.queryList(
                "SELECT YEAR(FACFEC) AS ANIO, COALESCE(SUM(FACTOT),0) AS TOTAL, COUNT(*) AS FACTURAS FROM TESTLIB.FAC001 GROUP BY YEAR(FACFEC) ORDER BY YEAR(FACFEC)");

            String[] cols = {"ANO", "VENTAS TOTALES", "FACTURAS"};
            String[] keys = {"anio", "total", "facturas"};
            java.util.List<HashMap<String,String>> td = new java.util.ArrayList<>();
            for (HashMap<String,String> r : data) {
                HashMap<String,String> row = new HashMap<>();
                row.put("anio", r.get("anio"));
                row.put("total", String.format("$%,.2f", Double.parseDouble(r.get("total"))));
                row.put("facturas", r.get("facturas"));
                td.add(row);
            }
            if (dH[0] != null) tableP.remove(dH[0]);
            dH[0] = mkTable(td, cols, keys);
            tableP.add(dH[0], BorderLayout.CENTER);

            XYSeries s = new XYSeries("Ventas");
            for (HashMap<String,String> r : data) s.add(Integer.parseInt(r.get("anio")), Double.parseDouble(r.get("total")));
            XYSeriesCollection ds = new XYSeriesCollection(s);
            JFreeChart ch = ChartFactory.createXYLineChart(null, "Ano", "Monto ($)", ds, PlotOrientation.VERTICAL, false, false, false);
            XYPlot pl = ch.getXYPlot();
            pl.setBackgroundPaint(SURF); pl.setOutlinePaint(BR);
            pl.setRangeGridlinePaint(BR); pl.setDomainGridlinePaint(BR);
            pl.getDomainAxis().setTickLabelFont(FSmall); pl.getDomainAxis().setLabelFont(FNormal);
            pl.getRangeAxis().setTickLabelFont(FSmall);
            XYLineAndShapeRenderer r = (XYLineAndShapeRenderer) pl.getRenderer();
            r.setSeriesPaint(0, CYAN); r.setSeriesStroke(0, new BasicStroke(3f));
            r.setSeriesShapesVisible(0, true);
            r.setSeriesShape(0, new java.awt.geom.Ellipse2D.Double(-5,-5,10,10));
            ch.setBackgroundPaint(BG); ch.getTitle().setPaint(T1);
            if (cH[0] != null) chartP.remove(cH[0]);
            cH[0] = mkChartPanel(ch, 600, 380);
            chartP.add(cH[0], BorderLayout.CENTER);
            screen.revalidate(); screen.repaint();
        };

        btnFiltrar.addActionListener(e -> loadData.run());
        loadData.run();

        screen.add(mkTopBar("Tendencia Historica", "Evolucion de ingresos 2020-2026", btnFiltrar), BorderLayout.NORTH);
        screen.add(center, BorderLayout.CENTER);
        center.add(tableP); center.add(chartP);
        return screen;
    }

    // ====== REPORTE 5: CUENTAS POR COBRAR ======
    static JPanel rptCobrar() {
        JPanel screen = mkScreen("Cuentas por Cobrar", "");
        JButton btnFiltrar = mkFilter("Actualizar", BLUE);

        JPanel center = new JPanel(new GridLayout(1, 2, 15, 0));
        center.setBackground(BG);
        center.setBorder(BorderFactory.createEmptyBorder(15,20,15,20));

        JPanel tableP = new JPanel(new BorderLayout());
        tableP.setBackground(BG);
        JLabel t1 = new JLabel("Detalle de Cuentas Pendientes");
        t1.setFont(FBold); t1.setForeground(T2); t1.setBorder(BorderFactory.createEmptyBorder(0,5,8,0));
        tableP.add(t1, BorderLayout.NORTH);

        JPanel chartP = new JPanel(new BorderLayout());
        chartP.setBackground(BG);
        JLabel t2 = new JLabel("Estado de Cobranza");
        t2.setFont(FBold); t2.setForeground(T2); t2.setBorder(BorderFactory.createEmptyBorder(0,5,8,0));
        chartP.add(t2, BorderLayout.NORTH);

        final JPanel[] dH = new JPanel[1], cH = new JPanel[1];

        Runnable loadData = () -> {
            ArrayList<HashMap<String,String>> data = AppAS400.queryList(
                "SELECT F.FACNUM AS ID, C.CLINOM AS CLIENTE, CAST(F.FACFEC AS VARCHAR(10)) AS FECHA, F.FACTOT AS TOTAL, F.FACEST AS ESTADO FROM TESTLIB.FAC001 F JOIN TESTLIB.CLI001 C ON F.CLICOD=C.CLICOD WHERE F.FACEST='P' ORDER BY F.FACFEC DESC");

            String[] cols = {"FACTURA", "CLIENTE", "FECHA", "MONTO", "ESTADO"};
            String[] keys = {"id", "cliente", "fecha", "total", "estado"};
            java.util.List<HashMap<String,String>> td = new java.util.ArrayList<>();
            for (HashMap<String,String> r : data) {
                HashMap<String,String> row = new HashMap<>();
                row.put("id", r.get("id"));
                row.put("cliente", r.get("cliente"));
                row.put("fecha", r.get("fecha"));
                row.put("total", String.format("$%,.2f", Double.parseDouble(r.get("total"))));
                row.put("estado", "\u23F3 Pendiente");
                td.add(row);
            }
            if (dH[0] != null) tableP.remove(dH[0]);
            dH[0] = mkTable(td, cols, keys);
            tableP.add(dH[0], BorderLayout.CENTER);

            double pagadas = AppAS400.scalar("SELECT COUNT(*) FROM TESTLIB.FAC001 WHERE FACEST='C' AND YEAR(FACFEC)=2026");
            double pendientes = AppAS400.scalar("SELECT COUNT(*) FROM TESTLIB.FAC001 WHERE FACEST='P' AND YEAR(FACFEC)=2026");
            DefaultPieDataset ds = new DefaultPieDataset();
            ds.setValue("Pagadas (" + (int)pagadas + ")", pagadas);
            ds.setValue("Pendientes (" + (int)pendientes + ")", pendientes);
            JFreeChart ch = ChartFactory.createPieChart(null, ds, true, true, false);
            PiePlot pl = (PiePlot) ch.getPlot();
            pl.setBackgroundPaint(SURF); pl.setOutlinePaint(BR); pl.setSectionOutlinesVisible(false);
            pl.setLabelFont(new Font("Segoe UI",Font.BOLD,12)); pl.setLabelPaint(T1);
            pl.setLabelBackgroundPaint(SURF2);
            pl.setSectionPaint("Pagadas (" + (int)pagadas + ")", GREEN);
            pl.setSectionPaint("Pendientes (" + (int)pendientes + ")", AMBER);
            pl.setStartAngle(90); pl.setDirection(Rotation.CLOCKWISE); pl.setInteriorGap(0.35);
            ch.setBackgroundPaint(BG); ch.getTitle().setPaint(T1);
            if (cH[0] != null) chartP.remove(cH[0]);
            cH[0] = mkChartPanel(ch, 600, 380);
            chartP.add(cH[0], BorderLayout.CENTER);
            screen.revalidate(); screen.repaint();
        };

        btnFiltrar.addActionListener(e -> loadData.run());
        loadData.run();

        screen.add(mkTopBar("Cuentas por Cobrar", "Facturas pendientes de cobro", btnFiltrar), BorderLayout.NORTH);
        screen.add(center, BorderLayout.CENTER);
        center.add(tableP); center.add(chartP);
        return screen;
    }

    // ====== REPORTE 6: METODOS DE PAGO ======
    static JPanel rptPagos() {
        JPanel screen = mkScreen("Metodos de Pago", "");
        JButton btnFiltrar = mkFilter("Actualizar", BLUE);

        JPanel center = new JPanel(new GridLayout(1, 2, 15, 0));
        center.setBackground(BG);
        center.setBorder(BorderFactory.createEmptyBorder(15,20,15,20));

        JPanel tableP = new JPanel(new BorderLayout());
        tableP.setBackground(BG);
        JLabel t1 = new JLabel("Detalle por Metodo de Cobro");
        t1.setFont(FBold); t1.setForeground(T2); t1.setBorder(BorderFactory.createEmptyBorder(0,5,8,0));
        tableP.add(t1, BorderLayout.NORTH);

        JPanel chartP = new JPanel(new BorderLayout());
        chartP.setBackground(BG);
        JLabel t2 = new JLabel("Distribucion de Pagos");
        t2.setFont(FBold); t2.setForeground(T2); t2.setBorder(BorderFactory.createEmptyBorder(0,5,8,0));
        chartP.add(t2, BorderLayout.NORTH);

        final JPanel[] dH = new JPanel[1], cH = new JPanel[1];

        Runnable loadData = () -> {
            ArrayList<HashMap<String,String>> data = AppAS400.queryList(
                "SELECT P.PAGMET AS METODO, COUNT(*) AS CANT, COALESCE(SUM(P.PAGMON),0) AS TOTAL FROM TESTLIB.PAG001 P GROUP BY P.PAGMET ORDER BY SUM(P.PAGMON) DESC");

            String[] cols = {"METODO", "CANTIDAD", "MONTO TOTAL"};
            String[] keys = {"metodo", "cant", "total"};
            java.util.List<HashMap<String,String>> td = new java.util.ArrayList<>();
            for (HashMap<String,String> r : data) {
                HashMap<String,String> row = new HashMap<>();
                row.put("metodo", r.get("metodo"));
                row.put("cant", r.get("cant"));
                row.put("total", String.format("$%,.2f", Double.parseDouble(r.get("total"))));
                td.add(row);
            }
            if (dH[0] != null) tableP.remove(dH[0]);
            dH[0] = mkTable(td, cols, keys);
            tableP.add(dH[0], BorderLayout.CENTER);

            DefaultCategoryDataset ds = new DefaultCategoryDataset();
            for (HashMap<String,String> r : data) ds.addValue(Double.parseDouble(r.get("total")), "Monto", r.get("metodo"));
            JFreeChart ch = ChartFactory.createBarChart(null, "Metodo", "Monto ($)", ds, PlotOrientation.VERTICAL, false, false, false);
            CategoryPlot p = ch.getCategoryPlot();
            p.setBackgroundPaint(SURF); p.setOutlinePaint(BR); p.setRangeGridlinePaint(BR);
            p.getDomainAxis().setTickLabelFont(FSmall); p.getRangeAxis().setTickLabelFont(FSmall);
            BarRenderer r = (BarRenderer) p.getRenderer();
            r.setSeriesPaint(0, PURPLE); r.setDrawBarOutline(false); r.setMaximumBarWidth(0.1);
            ch.setBackgroundPaint(BG); ch.getTitle().setPaint(T1);
            if (cH[0] != null) chartP.remove(cH[0]);
            cH[0] = mkChartPanel(ch, 600, 380);
            chartP.add(cH[0], BorderLayout.CENTER);
            screen.revalidate(); screen.repaint();
        };

        btnFiltrar.addActionListener(e -> loadData.run());
        loadData.run();

        screen.add(mkTopBar("Metodos de Pago", "Analisis de cobros por metodo", btnFiltrar), BorderLayout.NORTH);
        screen.add(center, BorderLayout.CENTER);
        center.add(tableP); center.add(chartP);
        return screen;
    }

    // ====== REPORTE 7: INVENTARIO ======
    static JPanel rptInventario() {
        JPanel screen = mkScreen("Inventario por Almacen", "");
        JButton btnFiltrar = mkFilter("Actualizar", BLUE);

        JPanel center = new JPanel(new GridLayout(1, 2, 15, 0));
        center.setBackground(BG);
        center.setBorder(BorderFactory.createEmptyBorder(15,20,15,20));

        JPanel tableP = new JPanel(new BorderLayout());
        tableP.setBackground(BG);
        JLabel t1 = new JLabel("Stock por Almacen");
        t1.setFont(FBold); t1.setForeground(T2); t1.setBorder(BorderFactory.createEmptyBorder(0,5,8,0));
        tableP.add(t1, BorderLayout.NORTH);

        JPanel chartP = new JPanel(new BorderLayout());
        chartP.setBackground(BG);
        JLabel t2 = new JLabel("Distribucion de Inventario");
        t2.setFont(FBold); t2.setForeground(T2); t2.setBorder(BorderFactory.createEmptyBorder(0,5,8,0));
        chartP.add(t2, BorderLayout.NORTH);

        final JPanel[] dH = new JPanel[1], cH = new JPanel[1];

        Runnable loadData = () -> {
            ArrayList<HashMap<String,String>> data = AppAS400.queryList(
                "SELECT CAST(ALMCOD AS VARCHAR(5)) AS ALM, COALESCE(SUM(ARTSTK),0) AS STOCK, COUNT(*) AS ARTS FROM TESTLIB.ART001 GROUP BY ALMCOD ORDER BY ALMCOD");

            String[] cols = {"ALMACEN", "STOCK TOTAL", "ARTICULOS"};
            String[] keys = {"alm", "stock", "arts"};
            java.util.List<HashMap<String,String>> td = new java.util.ArrayList<>();
            for (HashMap<String,String> r : data) {
                HashMap<String,String> row = new HashMap<>();
                row.put("alm", "ALM" + r.get("alm"));
                row.put("stock", r.get("stock"));
                row.put("arts", r.get("arts"));
                td.add(row);
            }
            if (dH[0] != null) tableP.remove(dH[0]);
            dH[0] = mkTable(td, cols, keys);
            tableP.add(dH[0], BorderLayout.CENTER);

            DefaultCategoryDataset ds = new DefaultCategoryDataset();
            for (HashMap<String,String> r : data) ds.addValue(Double.parseDouble(r.get("stock")), "Stock", "ALM" + r.get("alm"));
            JFreeChart ch = ChartFactory.createBarChart(null, "Almacen", "Unidades", ds, PlotOrientation.VERTICAL, false, false, false);
            BarRenderer r = (BarRenderer) ch.getCategoryPlot().getRenderer();
            r.setSeriesPaint(0, CYAN); r.setDrawBarOutline(false); r.setMaximumBarWidth(0.1);
            ch.getCategoryPlot().setBackgroundPaint(SURF); ch.getCategoryPlot().setOutlinePaint(BR);
            ch.getCategoryPlot().setRangeGridlinePaint(BR);
            ch.getCategoryPlot().getDomainAxis().setTickLabelFont(FSmall);
            ch.getCategoryPlot().getRangeAxis().setTickLabelFont(FSmall);
            ch.setBackgroundPaint(BG); ch.getTitle().setPaint(T1);
            if (cH[0] != null) chartP.remove(cH[0]);
            cH[0] = mkChartPanel(ch, 600, 380);
            chartP.add(cH[0], BorderLayout.CENTER);
            screen.revalidate(); screen.repaint();
        };

        btnFiltrar.addActionListener(e -> loadData.run());
        loadData.run();

        screen.add(mkTopBar("Inventario", "Stock por ubicacion de almacen", btnFiltrar), BorderLayout.NORTH);
        screen.add(center, BorderLayout.CENTER);
        center.add(tableP); center.add(chartP);
        return screen;
    }

    // ====== RESUMEN EJECUTIVO ======
    static JPanel resumenEjecutivo() {
        JPanel screen = mkScreen("Resumen Ejecutivo", "");
        JButton btnRefresh = mkFilter("Actualizar", BLUE);

        JPanel topCards = new JPanel(new GridLayout(1, 6, 12, 0));
        topCards.setBackground(BG);
        topCards.setBorder(BorderFactory.createEmptyBorder(15,20,10,20));

        double vtas = AppAS400.scalar("SELECT COALESCE(SUM(FACTOT),0) FROM TESTLIB.FAC001 WHERE YEAR(FACFEC)=2026");
        int facs = (int)AppAS400.scalar("SELECT COUNT(*) FROM TESTLIB.FAC001 WHERE YEAR(FACFEC)=2026");
        int cls = (int)AppAS400.scalar("SELECT COUNT(*) FROM TESTLIB.CLI001");
        double pag = AppAS400.scalar("SELECT COALESCE(SUM(PAGMON),0) FROM TESTLIB.PAG001 WHERE YEAR(PAGFEC)=2026");
        double mor = AppAS400.scalar("SELECT COALESCE(SUM(FACTOT),0) FROM TESTLIB.FAC001 WHERE FACEST='P' AND YEAR(FACFEC)=2026");
        int devs = (int)AppAS400.scalar("SELECT COUNT(*) FROM TESTLIB.DEV001 WHERE YEAR(DEVFEC)=2026");

        topCards.add(mkMiniCard("VENTAS", String.format("$%,.0f", vtas), BLUE));
        topCards.add(mkMiniCard("FACTURAS", ""+facs, GREEN));
        topCards.add(mkMiniCard("CLIENTES", ""+cls, CYAN));
        topCards.add(mkMiniCard("COBRADO", String.format("$%,.0f", pag), PURPLE));
        topCards.add(mkMiniCard("POR COBRAR", String.format("$%,.0f", mor), AMBER));
        topCards.add(mkMiniCard("DEVOLUCIONES", ""+devs, RED));

        JPanel bottom = new JPanel(new GridLayout(1, 2, 15, 0));
        bottom.setBackground(BG);
        bottom.setBorder(BorderFactory.createEmptyBorder(10,20,15,20));

        // Table
        JPanel tableP = new JPanel(new BorderLayout());
        tableP.setBackground(BG);
        JLabel t1 = new JLabel("Indicadores Clave de Rendimiento (KPIs)");
        t1.setFont(FBold); t1.setForeground(T2); t1.setBorder(BorderFactory.createEmptyBorder(0,5,8,0));
        tableP.add(t1, BorderLayout.NORTH);

        String[] cols = {"INDICADOR", "VALOR", "ESTADO"};
        java.util.List<HashMap<String,String>> td = new java.util.ArrayList<>();
        double tp = facs > 0 ? vtas / facs : 0;
        double ret = cls > 0 ? (int)AppAS400.scalar("SELECT COUNT(DISTINCT CLICOD) FROM TESTLIB.FAC001 WHERE YEAR(FACFEC)=2026")/(double)cls*100 : 0;
        td.add(mkRow("Ventas Totales 2026", String.format("$%,.2f", vtas), "\u2714"));
        td.add(mkRow("Facturas Emitidas", ""+facs, "\u2714"));
        td.add(mkRow("Ticket Promedio", String.format("$%,.2f", tp), "\u2714"));
        td.add(mkRow("Cobros Realizados", String.format("$%,.2f", pag), "\u2714"));
        td.add(mkRow("Cuentas por Cobrar", String.format("$%,.2f", mor), mor > 0 ? "\u23F3" : "\u2714"));
        td.add(mkRow("Devoluciones", ""+devs, "\u2714"));
        td.add(mkRow("Retencion Clientes", String.format("%.1f%%", ret), ret > 50 ? "\u2714" : "\u23F3"));
        td.add(mkRow("Cobranza", String.format("%.1f%%", vtas > 0 ? pag/vtas*100 : 0), "\u2714"));

        tableP.add(mkTable(td, cols, new String[]{"ind","val","est"}), BorderLayout.CENTER);
        bottom.add(tableP);

        // Pie
        JPanel chartP = new JPanel(new BorderLayout());
        chartP.setBackground(BG);
        JLabel t2 = new JLabel("Distribucion de Ingresos");
        t2.setFont(FBold); t2.setForeground(T2); t2.setBorder(BorderFactory.createEmptyBorder(0,5,8,0));
        chartP.add(t2, BorderLayout.NORTH);

        DefaultPieDataset ds = new DefaultPieDataset();
        ds.setValue("Cobrado", pag);
        ds.setValue("Por Cobrar", mor);
        ds.setValue("Devoluciones", AppAS400.scalar("SELECT COALESCE(SUM(DEVTOT),0) FROM TESTLIB.DEV001 WHERE YEAR(DEVFEC)=2026"));
        JFreeChart ch = ChartFactory.createPieChart(null, ds, true, true, false);
        PiePlot pl = (PiePlot) ch.getPlot();
        pl.setBackgroundPaint(SURF); pl.setOutlinePaint(BR); pl.setSectionOutlinesVisible(false);
        pl.setLabelFont(new Font("Segoe UI",Font.BOLD,12)); pl.setLabelPaint(T1);
        pl.setLabelBackgroundPaint(SURF2);
        pl.setSectionPaint("Cobrado", GREEN);
        pl.setSectionPaint("Por Cobrar", AMBER);
        pl.setSectionPaint("Devoluciones", RED);
        pl.setInteriorGap(0.30);
        ch.setBackgroundPaint(BG); ch.getTitle().setPaint(T1);
        chartP.add(mkChartPanel(ch, 500, 350), BorderLayout.CENTER);
        bottom.add(chartP);

        screen.add(mkTopBar("Resumen Ejecutivo 2026", "Panel de control gerencial", btnRefresh), BorderLayout.NORTH);
        JPanel centerP = new JPanel(new BorderLayout(0,0));
        centerP.setBackground(BG);
        centerP.add(topCards, BorderLayout.NORTH);
        centerP.add(bottom, BorderLayout.CENTER);
        screen.add(centerP, BorderLayout.CENTER);

        btnRefresh.addActionListener(e -> {
            screen.removeAll();
            screen.add(mkTopBar("Resumen Ejecutivo 2026", "Panel de control gerencial", btnRefresh), BorderLayout.NORTH);
            JPanel np = resumenEjecutivo();
            np.remove(0); // remove topbar
            centerP.removeAll();
            centerP.add(topCards, BorderLayout.NORTH);
            centerP.add(bottom, BorderLayout.CENTER);
            screen.revalidate();
            screen.repaint();
        });

        return screen;
    }

    static JPanel mkMiniCard(String title, String value, Color color) {
        JPanel card = new JPanel(new BorderLayout(0,4)) {
            protected void paintComponent(Graphics g) {
                Graphics2D g2 = (Graphics2D) g;
                g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
                g2.setColor(new Color(0,0,0,25));
                g2.fillRoundRect(2,2,getWidth()-2,getHeight()-2,10,10);
                g2.setColor(SURF2);
                g2.fillRoundRect(0,0,getWidth()-2,getHeight()-2,10,10);
                g2.setColor(color);
                g2.fillRect(0,0,getWidth()-2,3);
            }
        };
        card.setOpaque(false);
        card.setBorder(BorderFactory.createEmptyBorder(12,14,12,14));
        JLabel t = new JLabel(title);
        t.setForeground(T3); t.setFont(new Font("Segoe UI",Font.BOLD,9));
        JLabel v = new JLabel(value);
        v.setForeground(T1); v.setFont(new Font("Segoe UI",Font.BOLD,16));
        card.add(t, BorderLayout.NORTH);
        card.add(v, BorderLayout.CENTER);
        return card;
    }

    static HashMap<String,String> mkRow(String ind, String val, String est) {
        HashMap<String,String> r = new HashMap<>();
        r.put("ind", ind); r.put("val", val); r.put("est", est);
        return r;
    }
}
