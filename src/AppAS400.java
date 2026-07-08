import com.formdev.flatlaf.FlatDarkLaf;
import javax.swing.*;
import javax.swing.table.*;
import javax.swing.border.*;
import java.awt.*;
import java.awt.event.*;
import java.awt.geom.*;
import java.sql.*;
import java.util.*;
import java.util.Date;
import java.text.SimpleDateFormat;
import java.util.regex.Pattern;

public class AppAS400 extends JFrame {

    static final String DB_URL = "jdbc:as400://192.168.0.240;user=AYUDATX;password=MXTAC23;libraries=TESTLIB;prompt=false";
    static Connection conn;
    static String usuarioActual = "ADMIN";
    static AppAS400 instance;

    JPanel contentPanel;
    CardLayout cardLayout;
    JButton btnActive;

    static final Color BG = new Color(12, 18, 32);
    static final Color SURF = new Color(18, 25, 45);
    static final Color SURF2 = new Color(24, 34, 56);
    static final Color SURF3 = new Color(32, 44, 68);
    static final Color INP = new Color(15, 22, 38);
    static final Color BLUE = new Color(56, 120, 255);
    static final Color BLUE2 = new Color(96, 145, 255);
    static final Color BLUEG = new Color(56, 120, 255, 30);
    static final Color GREEN = new Color(16, 185, 129);
    static final Color GREEN2 = new Color(52, 211, 153);
    static final Color RED = new Color(239, 68, 68);
    static final Color RED2 = new Color(252, 129, 129);
    static final Color AMBER = new Color(245, 158, 11);
    static final Color PURPLE = new Color(139, 92, 246);
    static final Color CYAN = new Color(6, 182, 212);
    static final Color PINK = new Color(236, 72, 153);
    static final Color T1 = new Color(248, 250, 252);
    static final Color T2 = new Color(186, 198, 218);
    static final Color T3 = new Color(120, 140, 170);
    static final Color T4 = new Color(71, 85, 105);
    static final Color BR = new Color(40, 55, 80);
    static final Color BR2 = new Color(55, 70, 95);

    public static void main(String[] args) {
        try { UIManager.setLookAndFeel(new FlatDarkLaf()); } catch (Exception e) {}
        UIManager.put("Table.alternateRowColor", SURF);
        UIManager.put("Table.selectionBackground", BLUE);
        UIManager.put("Table.selectionForeground", Color.WHITE);
        UIManager.put("Table.showHorizontalLines", true);
        UIManager.put("Table.intercellSpacing", new Dimension(0, 1));
        UIManager.put("ScrollBar.thumbArc", 999);
        UIManager.put("ScrollBar.width", 8);
        UIManager.put("Button.arc", 8);
        UIManager.put("Component.arc", 6);
        UIManager.put("TextComponent.arc", 6);
        SwingUtilities.invokeLater(() -> new LoginDialog());
    }

    static Connection getConn() throws Exception {
        if (conn == null || conn.isClosed()) {
            Class.forName("com.ibm.as400.access.AS400JDBCDriver");
            conn = DriverManager.getConnection(DB_URL);
            conn.setAutoCommit(true);
        }
        return conn;
    }

    static ArrayList<HashMap<String, String>> queryList(String sql) {
        ArrayList<HashMap<String, String>> list = new ArrayList<>();
        try {
            ResultSet rs = getConn().createStatement().executeQuery(sql);
            ResultSetMetaData m = rs.getMetaData();
            int c = m.getColumnCount();
            while (rs.next()) {
                HashMap<String, String> row = new HashMap<>();
                for (int i = 1; i <= c; i++) row.put(m.getColumnLabel(i).toLowerCase(), rs.getString(i) != null ? rs.getString(i).trim() : "");
                list.add(row);
            }
            rs.close();
        } catch (Exception e) { e.printStackTrace(); }
        return list;
    }

    static double scalar(String sql) {
        try { ResultSet rs = getConn().createStatement().executeQuery(sql); double v = rs.next() ? rs.getDouble(1) : 0; rs.close(); return v; }
        catch (Exception e) { return 0; }
    }

    static void execute(String sql) {
        try { getConn().createStatement().executeUpdate(sql); } catch (Exception e) { e.printStackTrace(); }
    }

    // ============ COMPONENTES ============
    static JTextField mkIn(String t) {
        JTextField f = new JTextField(t);
        f.setBackground(INP); f.setForeground(T1); f.setCaretColor(T1);
        f.setFont(new Font("Segoe UI", Font.PLAIN, 13));
        f.setBorder(BorderFactory.createCompoundBorder(new LineBorder(BR, 1, true), BorderFactory.createEmptyBorder(8, 12, 8, 12)));
        f.setPreferredSize(new Dimension(0, 38));
        f.addFocusListener(new FocusAdapter() {
            public void focusGained(FocusEvent e) { f.setBorder(BorderFactory.createCompoundBorder(new LineBorder(BLUE, 2, true), BorderFactory.createEmptyBorder(7, 11, 7, 11))); }
            public void focusLost(FocusEvent e) { f.setBorder(BorderFactory.createCompoundBorder(new LineBorder(BR, 1, true), BorderFactory.createEmptyBorder(8, 12, 8, 12))); }
        });
        return f;
    }

    static JComboBox<String> mkCmb(String[] items) {
        JComboBox<String> c = new JComboBox<>(items);
        c.setBackground(INP); c.setForeground(T1);
        c.setFont(new Font("Segoe UI", Font.PLAIN, 13));
        c.setPreferredSize(new Dimension(0, 38));
        c.setBorder(BorderFactory.createLineBorder(BR, 1, true));
        return c;
    }

    static JPanel mkFld(String label, JComponent field) {
        JPanel p = new JPanel(new BorderLayout(0, 4));
        p.setOpaque(false);
        JLabel l = new JLabel(label);
        l.setForeground(T3); l.setFont(new Font("Segoe UI", Font.BOLD, 11));
        p.add(l, BorderLayout.NORTH);
        p.add(field, BorderLayout.CENTER);
        return p;
    }

    static JButton mkAction(String text, Color bg, int w) {
        JButton b = new JButton(text) {
            boolean hover = false;
            { addMouseListener(new MouseAdapter() { public void mouseEntered(MouseEvent e) { hover = true; repaint(); } public void mouseExited(MouseEvent e) { hover = false; repaint(); } }); }
            protected void paintComponent(Graphics g) {
                Graphics2D g2 = (Graphics2D) g.create();
                g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
                Color c = hover ? bg.brighter() : bg;
                g2.setColor(c);
                g2.fillRoundRect(0, 0, getWidth(), getHeight(), 8, 8);
                g2.dispose();
                super.paintComponent(g);
            }
        };
        b.setForeground(Color.WHITE);
        b.setFont(new Font("Segoe UI", Font.BOLD, 12));
        b.setPreferredSize(new Dimension(w, 36));
        b.setFocusPainted(false); b.setBorderPainted(false); b.setContentAreaFilled(false); b.setOpaque(false);
        b.setCursor(Cursor.getPredefinedCursor(Cursor.HAND_CURSOR));
        return b;
    }

    // ============ LOGIN ============
    static class LoginDialog extends JDialog {
        LoginDialog() {
            setUndecorated(true);
            setSize(520, 440);
            setLocationRelativeTo(null);

            JPanel root = new JPanel(null) {
                float t = 0f;
                {
                    javax.swing.Timer timer = new javax.swing.Timer(20, e -> { t += 0.02f; if (t > 1f) t = 0f; repaint(); });
                    timer.start();
                }
                protected void paintComponent(Graphics g) {
                    super.paintComponent(g);
                    Graphics2D g2 = (Graphics2D) g;
                    g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
                    // Animated gradient background
                    int x2 = (int)(getWidth() * t);
                    GradientPaint gp = new GradientPaint(x2, 0, new Color(15, 23, 42), getWidth()-x2, getHeight(), new Color(30, 58, 138));
                    g2.setPaint(gp);
                    g2.fillRect(0, 0, getWidth(), getHeight());
                    // Decorative circles
                    g2.setColor(new Color(56, 120, 255, 15));
                    g2.fillOval(-80, -80, 250, 250);
                    g2.fillOval(getWidth()-120, getHeight()-120, 200, 200);
                    g2.setColor(new Color(139, 92, 246, 10));
                    g2.fillOval(getWidth()/2-60, 50, 120, 120);
                }
            };

            // Close
            JButton btnX = new JButton("\u2715");
            btnX.setBounds(478, 10, 32, 32);
            btnX.setBackground(new Color(255,255,255,15)); btnX.setForeground(new Color(255,255,255,150));
            btnX.setBorderPainted(false); btnX.setFocusPainted(false);
            btnX.setFont(new Font("Segoe UI", Font.BOLD, 14));
            btnX.setCursor(Cursor.getPredefinedCursor(Cursor.HAND_CURSOR));
            btnX.addMouseListener(new MouseAdapter() {
                public void mouseEntered(MouseEvent e) { btnX.setBackground(RED); btnX.setForeground(Color.WHITE); }
                public void mouseExited(MouseEvent e) { btnX.setBackground(new Color(255,255,255,15)); btnX.setForeground(new Color(255,255,255,150)); }
            });
            btnX.addActionListener(e -> System.exit(0));
            root.add(btnX);

            // Icon
            JLabel icon = new JLabel("\u2B22");
            icon.setBounds(215, 25, 90, 65);
            icon.setFont(new Font("Segoe UI Emoji", Font.PLAIN, 52));
            icon.setForeground(BLUE);
            icon.setHorizontalAlignment(SwingConstants.CENTER);
            root.add(icon);

            // Title
            JLabel title = new JLabel("AS/400  INTEGRAL");
            title.setBounds(0, 90, 520, 38);
            title.setFont(new Font("Segoe UI", Font.BOLD, 26));
            title.setForeground(Color.WHITE);
            title.setHorizontalAlignment(SwingConstants.CENTER);
            root.add(title);

            JLabel sub = new JLabel("Sistema de Gestion Empresarial v5.0");
            sub.setBounds(0, 128, 520, 18);
            sub.setFont(new Font("Segoe UI", Font.PLAIN, 12));
            sub.setForeground(new Color(148, 163, 184));
            sub.setHorizontalAlignment(SwingConstants.CENTER);
            root.add(sub);

            // Divider line
            JPanel line = new JPanel() { protected void paintComponent(Graphics g) {
                Graphics2D g2 = (Graphics2D) g;
                g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
                g2.setColor(new Color(56, 120, 255, 60));
                g2.fillRoundRect(0, 0, getWidth(), 2, 2, 2);
            }};
            line.setBounds(80, 160, 360, 2);
            line.setOpaque(false);
            root.add(line);

            // Form fields
            JLabel ul = new JLabel("USUARIO");
            ul.setBounds(80, 180, 360, 16);
            ul.setFont(new Font("Segoe UI", Font.BOLD, 10));
            ul.setForeground(new Color(120, 140, 170));
            root.add(ul);

            JTextField txtUser = new JTextField("AYUDATX") {
                boolean focus = false;
                { addFocusListener(new FocusAdapter() { public void focusGained(FocusEvent e) { focus = true; } public void focusLost(FocusEvent e) { focus = false; } }); }
                protected void paintComponent(Graphics g) {
                    Graphics2D g2 = (Graphics2D) g;
                    g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
                    g2.setColor(focus ? new Color(56, 120, 255, 30) : INP);
                    g2.fillRoundRect(0, 0, getWidth(), getHeight(), 8, 8);
                    super.paintComponent(g);
                    if (focus) {
                        g2.setColor(BLUE);
                        g2.setStroke(new BasicStroke(2));
                        g2.drawRoundRect(0, 0, getWidth()-1, getHeight()-1, 8, 8);
                    }
                }
            };
            txtUser.setBounds(80, 200, 360, 42);
            txtUser.setOpaque(false);
            txtUser.setForeground(Color.WHITE);
            txtUser.setCaretColor(Color.WHITE);
            txtUser.setFont(new Font("Segoe UI", Font.PLAIN, 14));
            txtUser.setBorder(BorderFactory.createEmptyBorder(5, 15, 5, 15));
            root.add(txtUser);

            JLabel pl = new JLabel("CONTRASENA");
            pl.setBounds(80, 252, 360, 16);
            pl.setFont(new Font("Segoe UI", Font.BOLD, 10));
            pl.setForeground(new Color(120, 140, 170));
            root.add(pl);

            JPasswordField txtPass = new JPasswordField("MXTAC23") {
                boolean focus = false;
                { addFocusListener(new FocusAdapter() { public void focusGained(FocusEvent e) { focus = true; } public void focusLost(FocusEvent e) { focus = false; } }); }
                protected void paintComponent(Graphics g) {
                    Graphics2D g2 = (Graphics2D) g;
                    g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
                    g2.setColor(focus ? new Color(56, 120, 255, 30) : INP);
                    g2.fillRoundRect(0, 0, getWidth(), getHeight(), 8, 8);
                    super.paintComponent(g);
                    if (focus) {
                        g2.setColor(BLUE);
                        g2.setStroke(new BasicStroke(2));
                        g2.drawRoundRect(0, 0, getWidth()-1, getHeight()-1, 8, 8);
                    }
                }
            };
            txtPass.setBounds(80, 272, 360, 42);
            txtPass.setOpaque(false);
            txtPass.setForeground(Color.WHITE);
            txtPass.setCaretColor(Color.WHITE);
            txtPass.setFont(new Font("Segoe UI", Font.PLAIN, 14));
            txtPass.setBorder(BorderFactory.createEmptyBorder(5, 15, 5, 15));
            root.add(txtPass);

            // Login button with gradient
            JButton btnLogin = new JButton("INICIAR SESION  \u2192") {
                boolean hover = false;
                { addMouseListener(new MouseAdapter() { public void mouseEntered(MouseEvent e) { hover = true; repaint(); } public void mouseExited(MouseEvent e) { hover = false; repaint(); } }); }
                protected void paintComponent(Graphics g) {
                    Graphics2D g2 = (Graphics2D) g.create();
                    g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
                    GradientPaint gp = new GradientPaint(0, 0, hover ? BLUE2 : BLUE, getWidth(), 0, hover ? PURPLE : new Color(99, 102, 241));
                    g2.setPaint(gp);
                    g2.fillRoundRect(0, 0, getWidth(), getHeight(), 10, 10);
                    g2.dispose();
                    super.paintComponent(g);
                }
            };
            btnLogin.setBounds(80, 340, 360, 46);
            btnLogin.setForeground(Color.WHITE);
            btnLogin.setFont(new Font("Segoe UI", Font.BOLD, 14));
            btnLogin.setFocusPainted(false); btnLogin.setBorderPainted(false);
            btnLogin.setContentAreaFilled(false); btnLogin.setOpaque(false);
            btnLogin.setCursor(Cursor.getPredefinedCursor(Cursor.HAND_CURSOR));
            btnLogin.addActionListener(e -> {
                try { getConn(); usuarioActual = txtUser.getText(); dispose(); instance = new AppAS400(); }
                catch (Exception ex) { JOptionPane.showMessageDialog(root, "Error: " + ex.getMessage(), "Error", JOptionPane.ERROR_MESSAGE); }
            });
            root.add(btnLogin);

            txtPass.addKeyListener(new KeyAdapter() { public void keyPressed(KeyEvent e) { if (e.getKeyCode() == KeyEvent.VK_ENTER) btnLogin.doClick(); } });

            // Footer
            JLabel foot = new JLabel("Produced by TAC Software \u00B7 2026");
            foot.setBounds(0, 400, 520, 16);
            foot.setFont(new Font("Segoe UI", Font.PLAIN, 10));
            foot.setForeground(new Color(71, 85, 105));
            foot.setHorizontalAlignment(SwingConstants.CENTER);
            root.add(foot);

            setContentPane(root);
            setVisible(true);
        }
    }

    // ============ MAIN APP ============
    AppAS400() {
        setTitle("AS/400 Sistema Integral v5.0");
        setSize(1440, 880);
        setMinimumSize(new Dimension(1200, 750));
        setDefaultCloseOperation(EXIT_ON_CLOSE);
        setLocationRelativeTo(null);

        JPanel root = new JPanel(new BorderLayout());
        root.setBackground(BG);

        // ===== SIDEBAR =====
        JPanel sidebar = new JPanel() {
            protected void paintComponent(Graphics g) {
                super.paintComponent(g);
                Graphics2D g2 = (Graphics2D) g;
                g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
                g2.setColor(SURF);
                g2.fillRect(0, 0, getWidth(), getHeight());
                g2.setColor(BR);
                g2.drawLine(getWidth()-1, 0, getWidth()-1, getHeight());
            }
        };
        sidebar.setPreferredSize(new Dimension(260, 0));
        sidebar.setLayout(new BoxLayout(sidebar, BoxLayout.Y_AXIS));

        // Brand header
        JPanel brand = new JPanel() {
            protected void paintComponent(Graphics g) {
                Graphics2D g2 = (Graphics2D) g;
                g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
                GradientPaint gp = new GradientPaint(0, 0, BLUE, getWidth(), getHeight(), PURPLE);
                g2.setPaint(gp);
                g2.fillRoundRect(8, 8, getWidth()-16, getHeight()-16, 12, 12);
            }
        };
        brand.setOpaque(false);
        brand.setMaximumSize(new Dimension(260, 72));
        brand.setPreferredSize(new Dimension(260, 72));
        brand.setLayout(new BorderLayout());
        brand.setBorder(BorderFactory.createEmptyBorder(0, 22, 0, 22));
        JLabel bName = new JLabel("AS/400");
        bName.setFont(new Font("Segoe UI", Font.BOLD, 22));
        bName.setForeground(Color.WHITE);
        JLabel bVer = new JLabel("v5.0");
        bVer.setFont(new Font("Segoe UI", Font.PLAIN, 11));
        bVer.setForeground(new Color(255,255,255,180));
        brand.add(bName, BorderLayout.WEST);
        brand.add(bVer, BorderLayout.EAST);
        sidebar.add(brand);
        sidebar.add(Box.createVerticalStrut(12));

        // User
        JPanel userP = new JPanel(new BorderLayout());
        userP.setOpaque(false);
        userP.setMaximumSize(new Dimension(260, 45));
        userP.setBorder(BorderFactory.createEmptyBorder(0, 22, 0, 22));
        JLabel uIcon = new JLabel("\u25CF");
        uIcon.setFont(new Font("Dialog", Font.PLAIN, 10));
        uIcon.setForeground(GREEN);
        JLabel uName = new JLabel(usuarioActual + "  ");
        uName.setForeground(T1);
        uName.setFont(new Font("Segoe UI", Font.BOLD, 12));
        JLabel uRole = new JLabel("Administrador");
        uRole.setForeground(T3);
        uRole.setFont(new Font("Segoe UI", Font.PLAIN, 10));
        JPanel uInfo = new JPanel(new BorderLayout());
        uInfo.setOpaque(false);
        uInfo.add(uName, BorderLayout.NORTH);
        uInfo.add(uRole, BorderLayout.SOUTH);
        userP.add(uIcon, BorderLayout.WEST);
        userP.add(uInfo, BorderLayout.CENTER);
        sidebar.add(userP);
        sidebar.add(Box.createVerticalStrut(5));

        // Separator
        JSeparator sep1 = new JSeparator(); sep1.setMaximumSize(new Dimension(260, 1)); sep1.setForeground(BR);
        sidebar.add(sep1);

        sidebar.add(mkLbl("PRINCIPAL"));
        sidebar.add(mkNav("\u2302  Dashboard", "dashboard"));
        JSeparator sep2 = new JSeparator(); sep2.setMaximumSize(new Dimension(260, 1)); sep2.setForeground(BR);
        sidebar.add(sep2);

        sidebar.add(mkLbl("CATALOGOS"));
        sidebar.add(mkNav("\u2630  Clientes", "clientes"));
        sidebar.add(mkNav("\u2630  Productos", "productos"));
        sidebar.add(mkNav("\u2630  Proveedores", "proveedores"));
        JSeparator sep3 = new JSeparator(); sep3.setMaximumSize(new Dimension(260, 1)); sep3.setForeground(BR);
        sidebar.add(sep3);

        sidebar.add(mkLbl("OPERACIONES"));
        sidebar.add(mkNav("\u2630  Facturas / Ventas", "facturas"));
        sidebar.add(mkNav("\u2630  Entradas Inventario", "entradas"));
        sidebar.add(mkNav("\u2630  Salidas Inventario", "salidas"));
        sidebar.add(mkNav("\u2630  Devoluciones", "devoluciones"));
        sidebar.add(mkNav("\u2630  Pagos", "pagos"));

        JSeparator sep4 = new JSeparator(); sep4.setMaximumSize(new Dimension(260, 1)); sep4.setForeground(BR);
        sidebar.add(sep4);

        sidebar.add(mkLbl("REPORTES"));
        sidebar.add(mkNav("\uD83D\uDCCA  Ventas Mensuales", "rpt_ventas"));
        sidebar.add(mkNav("\uD83D\uDCCA  Top Clientes", "rpt_topcli"));
        sidebar.add(mkNav("\uD83D\uDCCA  Categorias", "rpt_categorias"));
        sidebar.add(mkNav("\uD83D\uDCCA  Tendencia Historica", "rpt_tendencia"));
        sidebar.add(mkNav("\uD83D\uDCCA  Cuentas x Cobrar", "rpt_cobrar"));
        sidebar.add(mkNav("\uD83D\uDCCA  Metodos de Pago", "rpt_pagos"));
        sidebar.add(mkNav("\uD83D\uDCCA  Inventario", "rpt_inventario"));

        JSeparator sep5 = new JSeparator(); sep5.setMaximumSize(new Dimension(260, 1)); sep5.setForeground(BR);
        sidebar.add(sep5);

        sidebar.add(mkLbl("ANALISIS"));
        sidebar.add(mkNav("\u26A1  Resumen Ejecutivo", "ana_resumen"));
        sidebar.add(mkNav("\u26A1  Proyecciones", "ana_proyecciones"));
        sidebar.add(Box.createVerticalGlue());

        // Status
        JPanel stP = new JPanel(new FlowLayout(FlowLayout.LEFT, 8, 0));
        stP.setOpaque(false);
        stP.setMaximumSize(new Dimension(260, 35));
        stP.setBorder(BorderFactory.createEmptyBorder(0, 22, 10, 0));
        JLabel dot = new JLabel("\u25CF");
        dot.setFont(new Font("Dialog", Font.PLAIN, 8));
        dot.setForeground(GREEN);
        JLabel st = new JLabel("Conectado al AS/400");
        st.setForeground(GREEN);
        st.setFont(new Font("Segoe UI", Font.PLAIN, 10));
        stP.add(dot);
        stP.add(st);
        sidebar.add(stP);

        root.add(sidebar, BorderLayout.WEST);

        // ===== CONTENT =====
        contentPanel = new JPanel();
        cardLayout = new CardLayout();
        contentPanel.setLayout(cardLayout);
        contentPanel.setBackground(BG);
        contentPanel.add(mkDashboard(), "dashboard");
        contentPanel.add(mkCrud("clientes"), "clientes");
        contentPanel.add(mkCrud("productos"), "productos");
        contentPanel.add(mkCrud("proveedores"), "proveedores");
        contentPanel.add(mkCrud("facturas"), "facturas");
        contentPanel.add(mkCrud("entradas"), "entradas");
        contentPanel.add(mkCrud("salidas"), "salidas");
        contentPanel.add(mkCrud("devoluciones"), "devoluciones");
        contentPanel.add(mkCrud("pagos"), "pagos");
        // Reportes - placeholders lazy load
        contentPanel.add(mkPlaceholder("rpt_ventas"), "rpt_ventas");
        contentPanel.add(mkPlaceholder("rpt_topcli"), "rpt_topcli");
        contentPanel.add(mkPlaceholder("rpt_categorias"), "rpt_categorias");
        contentPanel.add(mkPlaceholder("rpt_tendencia"), "rpt_tendencia");
        contentPanel.add(mkPlaceholder("rpt_cobrar"), "rpt_cobrar");
        contentPanel.add(mkPlaceholder("rpt_pagos"), "rpt_pagos");
        contentPanel.add(mkPlaceholder("rpt_inventario"), "rpt_inventario");
        contentPanel.add(mkPlaceholder("ana_resumen"), "ana_resumen");
        contentPanel.add(mkPlaceholder("ana_proyecciones"), "ana_proyecciones");
        root.add(contentPanel, BorderLayout.CENTER);
        setContentPane(root);
        setVisible(true);
        // Activate dashboard
        cardLayout.show(contentPanel, "dashboard");
        loadKpis();
    }

    JPanel mkPlaceholder(String name) {
        JPanel p = new JPanel(new BorderLayout());
        p.setBackground(BG);
        p.setName("ph_" + name);
        JLabel lbl = new JLabel("Cargando...", SwingConstants.CENTER);
        lbl.setForeground(T3);
        lbl.setFont(new Font("Segoe UI", Font.BOLD, 16));
        p.add(lbl, BorderLayout.CENTER);
        return p;
    }

    void loadReport(String panel) {
        int idx = -1;
        for (int i = 0; i < contentPanel.getComponentCount(); i++) {
            if (((CardLayout)contentPanel.getLayout()).toString().contains(panel) || contentPanel.getComponent(i).getName() != null && contentPanel.getComponent(i).getName().equals("ph_" + panel)) {
                idx = i; break;
            }
        }
        // Find by checking all components
        for (int i = 0; i < contentPanel.getComponentCount(); i++) {
            Component c = contentPanel.getComponent(i);
            if (c.getName() != null && c.getName().equals("ph_" + panel)) {
                idx = i;
                break;
            }
        }
        if (idx < 0) return;

        JPanel real;
        switch (panel) {
            case "rpt_ventas": real = ReportesChart.rptVentasMensuales(); break;
            case "rpt_topcli": real = ReportesChart.rptTopClientes(); break;
            case "rpt_categorias": real = ReportesChart.rptCategorias(); break;
            case "rpt_tendencia": real = ReportesChart.rptTendencia(); break;
            case "rpt_cobrar": real = ReportesChart.rptCobrar(); break;
            case "rpt_pagos": real = ReportesChart.rptPagos(); break;
            case "rpt_inventario": real = ReportesChart.rptInventario(); break;
            case "ana_resumen": real = ReportesChart.resumenEjecutivo(); break;
            case "ana_proyecciones": real = ReportesChart.resumenEjecutivo(); break; // reuse
            default: return;
        }
        contentPanel.remove(idx);
        contentPanel.add(real, panel, idx);
        contentPanel.revalidate();
        contentPanel.repaint();
    }

    JLabel mkLbl(String t) {
        JLabel l = new JLabel("   " + t);
        l.setForeground(T4);
        l.setFont(new Font("Segoe UI", Font.BOLD, 10));
        l.setBorder(BorderFactory.createEmptyBorder(10, 10, 5, 0));
        l.setMaximumSize(new Dimension(260, 24));
        return l;
    }

    JButton mkNav(String text, String panel) {
        JButton btn = new JButton(text);
        btn.setActionCommand(panel);
        btn.setFont(new Font("Segoe UI", Font.PLAIN, 13));
        btn.setForeground(T2);
        btn.setBackground(SURF);
        btn.setBorderPainted(false);
        btn.setFocusPainted(false);
        btn.setHorizontalAlignment(SwingConstants.LEFT);
        btn.setMaximumSize(new Dimension(260, 42));
        btn.setPreferredSize(new Dimension(260, 42));
        btn.setBorder(BorderFactory.createEmptyBorder(0, 22, 0, 10));
        btn.setCursor(Cursor.getPredefinedCursor(Cursor.HAND_CURSOR));
        btn.addMouseListener(new MouseAdapter() {
            public void mouseEntered(MouseEvent e) { if (btn != btnActive) { btn.setBackground(SURF2); btn.setForeground(T1); } }
            public void mouseExited(MouseEvent e) { if (btn != btnActive) { btn.setBackground(SURF); btn.setForeground(T2); } }
        });
        btn.addActionListener(e -> {
            if (btnActive != null) { btnActive.setBackground(SURF); btnActive.setForeground(T2); }
            btnActive = btn;
            btn.setBackground(BLUEG);
            btn.setForeground(BLUE);
            cardLayout.show(contentPanel, panel);
            if (!panel.equals("dashboard") && !panel.startsWith("rpt_") && !panel.startsWith("ana_")) refreshTable(panel);
            if (panel.startsWith("rpt_") || panel.startsWith("ana_")) loadReport(panel);
        });
        return btn;
    }

    // ============ DASHBOARD ============
    JPanel mkDashboard() {
        JPanel p = new JPanel(new BorderLayout(0, 20));
        p.setBackground(BG);
        p.setBorder(BorderFactory.createEmptyBorder(25, 30, 25, 30));

        // Header
        JPanel hdr = new JPanel(new BorderLayout());
        hdr.setOpaque(false);
        JPanel hLeft = new JPanel(new BorderLayout());
        hLeft.setOpaque(false);
        JLabel title = new JLabel("Dashboard General");
        title.setFont(new Font("Segoe UI", Font.BOLD, 26));
        title.setForeground(T1);
        JLabel date = new JLabel(new SimpleDateFormat("EEEE dd 'de' MMMM, yyyy", new Locale("es")).format(new Date()));
        date.setFont(new Font("Segoe UI", Font.PLAIN, 12));
        date.setForeground(T3);
        hLeft.add(title, BorderLayout.NORTH);
        hLeft.add(date, BorderLayout.SOUTH);
        hdr.add(hLeft, BorderLayout.WEST);

        // Time
        JLabel time = new JLabel(new SimpleDateFormat("HH:mm:ss").format(new Date()));
        time.setFont(new Font("Segoe UI", Font.BOLD, 14));
        time.setForeground(T2);
        hdr.add(time, BorderLayout.EAST);
        p.add(hdr, BorderLayout.NORTH);

        // KPI Cards - 2 rows of 4
        JPanel cards = new JPanel(new GridLayout(2, 4, 16, 16));
        cards.setOpaque(false);
        cards.add(mkKpi("VENTAS TOTALES", "$0", "\uD83D\uDCB0", BLUE, "+12% vs 2025"));
        cards.add(mkKpi("FACTURAS EMITIDAS", "0", "\uD83D\uDCC4", GREEN, "Periodo 2026"));
        cards.add(mkKpi("CLIENTES ACTIVOS", "0", "\uD83D\uDC65", CYAN, "Base de datos"));
        cards.add(mkKpi("PRODUCTOS", "0", "\uD83D\uDCE6", PURPLE, "Inventario"));
        cards.add(mkKpi("STOCK BAJO", "0", "\u26A0\uFE0F", AMBER, "Requiere atencion"));
        cards.add(mkKpi("CLIENTES MOROSOS", "0", "\u274C", RED, "Cuentas por cobrar"));
        cards.add(mkKpi("DEVOLUCIONES", "$0", "\u21BA", new Color(249,115,22), "Periodo 2026"));
        cards.add(mkKpi("ENTRADAS COMPRA", "$0", "\u2B06\uFE0F", new Color(20,184,166), "Proveedores"));
        p.add(cards, BorderLayout.CENTER);
        return p;
    }

    JPanel mkKpi(String title, String value, String icon, Color color, String sub) {
        JPanel card = new JPanel(new BorderLayout(0, 8)) {
            boolean h = false;
            { addMouseListener(new MouseAdapter() { public void mouseEntered(MouseEvent e) { h = true; repaint(); } public void mouseExited(MouseEvent e) { h = false; repaint(); } }); }
            protected void paintComponent(Graphics g) {
                Graphics2D g2 = (Graphics2D) g;
                g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
                // Shadow
                g2.setColor(new Color(0, 0, 0, 30));
                g2.fillRoundRect(3, 3, getWidth()-3, getHeight()-3, 14, 14);
                // Background
                g2.setColor(h ? SURF3 : SURF);
                g2.fillRoundRect(0, 0, getWidth()-3, getHeight()-3, 14, 14);
                // Top accent line
                g2.setColor(color);
                g2.fillRoundRect(0, 0, getWidth()-3, 3, 14, 14);
                g2.fillRect(7, 0, getWidth()-17, 3);
            }
        };
        card.setOpaque(false);
        card.setBorder(BorderFactory.createEmptyBorder(15, 18, 15, 18));

        JPanel top = new JPanel(new BorderLayout());
        top.setOpaque(false);
        JLabel iconLbl = new JLabel(icon);
        iconLbl.setFont(new Font("Segoe UI Emoji", Font.PLAIN, 20));
        top.add(iconLbl, BorderLayout.WEST);
        JLabel titleLbl = new JLabel(title);
        titleLbl.setForeground(T3);
        titleLbl.setFont(new Font("Segoe UI", Font.BOLD, 10));
        top.add(titleLbl, BorderLayout.CENTER);

        JPanel center = new JPanel(new BorderLayout());
        center.setOpaque(false);
        JLabel valLbl = new JLabel(value);
        valLbl.setName("kpi_" + title);
        valLbl.setForeground(T1);
        valLbl.setFont(new Font("Segoe UI", Font.BOLD, 28));
        JLabel subLbl = new JLabel(sub);
        subLbl.setForeground(T4);
        subLbl.setFont(new Font("Segoe UI", Font.PLAIN, 10));
        center.add(valLbl, BorderLayout.NORTH);
        center.add(subLbl, BorderLayout.SOUTH);

        card.add(top, BorderLayout.NORTH);
        card.add(center, BorderLayout.CENTER);
        return card;
    }

    void loadKpis() {
        SwingUtilities.invokeLater(() -> {
            try {
                JPanel dash = (JPanel) contentPanel.getComponent(0);
                JPanel cards = null;
                for (Component c : dash.getComponents()) {
                    if (c instanceof JPanel && ((JPanel)c).getLayout() instanceof GridLayout) { cards = (JPanel) c; break; }
                }
                if (cards != null && cards.getComponentCount() >= 8) {
                    Component[] cc = cards.getComponents();
                    setKpiVal(cc[0], String.format("$%,.2f", scalar("SELECT COALESCE(SUM(FACTOT),0) FROM TESTLIB.FAC001 WHERE YEAR(FACFEC)=2026")));
                    setKpiVal(cc[1], "" + (int)scalar("SELECT COUNT(*) FROM TESTLIB.FAC001 WHERE YEAR(FACFEC)=2026"));
                    setKpiVal(cc[2], "" + (int)scalar("SELECT COUNT(*) FROM TESTLIB.CLI001"));
                    setKpiVal(cc[3], "" + (int)scalar("SELECT COUNT(*) FROM TESTLIB.ART001"));
                    setKpiVal(cc[4], "" + (int)scalar("SELECT COUNT(*) FROM TESTLIB.ART001 WHERE ARTSTK<10"));
                    setKpiVal(cc[5], "" + (int)scalar("SELECT COUNT(DISTINCT CLICOD) FROM TESTLIB.FAC001 WHERE FACEST='P'"));
                    setKpiVal(cc[6], String.format("$%,.2f", scalar("SELECT COALESCE(SUM(DEVTOT),0) FROM TESTLIB.DEV001 WHERE YEAR(DEVFEC)=2026")));
                    setKpiVal(cc[7], String.format("$%,.2f", scalar("SELECT COALESCE(SUM(ENTTOT),0) FROM TESTLIB.ENT001 WHERE YEAR(ENTFEC)=2026")));
                }
            } catch (Exception e) { e.printStackTrace(); }
        });
    }

    void setKpiVal(Component c, String val) {
        if (!(c instanceof JPanel)) return;
        for (Component inner : ((JPanel)c).getComponents()) {
            if (inner instanceof JPanel) {
                for (Component deep : ((JPanel)inner).getComponents()) {
                    if (deep instanceof JLabel && deep.getName() != null && deep.getName().startsWith("kpi_")) {
                        ((JLabel)deep).setText(val);
                        return;
                    }
                }
            }
        }
    }

    // ============ CRUD PANELS ============
    JPanel mkCrud(String type) {
        JPanel p = new JPanel(new BorderLayout(0, 0));
        p.setBackground(BG);

        // Top header bar
        JPanel topBar = new JPanel() {
            protected void paintComponent(Graphics g) {
                Graphics2D g2 = (Graphics2D) g;
                g2.setColor(SURF);
                g2.fillRect(0, 0, getWidth(), getHeight());
                g2.setColor(BR);
                g2.drawLine(0, getHeight()-1, getWidth(), getHeight()-1);
            }
        };
        topBar.setOpaque(false);
        topBar.setLayout(new BorderLayout());
        topBar.setPreferredSize(new Dimension(0, 68));

        JPanel titleArea = new JPanel(new BorderLayout());
        titleArea.setOpaque(false);
        titleArea.setBorder(BorderFactory.createEmptyBorder(0, 30, 0, 0));
        String title = type.substring(0, 1).toUpperCase() + type.substring(1);
        JLabel lblTitle = new JLabel(title);
        lblTitle.setFont(new Font("Segoe UI", Font.BOLD, 22));
        lblTitle.setForeground(T1);
        JLabel lblSub = new JLabel("Gestion y administracion de registros");
        lblSub.setFont(new Font("Segoe UI", Font.PLAIN, 11));
        lblSub.setForeground(T3);
        titleArea.add(lblTitle, BorderLayout.NORTH);
        titleArea.add(lblSub, BorderLayout.SOUTH);
        topBar.add(titleArea, BorderLayout.WEST);

        JPanel actions = new JPanel(new FlowLayout(FlowLayout.RIGHT, 12, 0));
        actions.setOpaque(false);
        actions.setBorder(BorderFactory.createEmptyBorder(0, 0, 0, 20));

        JTextField search = new JTextField(16);
        search.setBackground(INP); search.setForeground(T1); search.setCaretColor(T1);
        search.setFont(new Font("Segoe UI", Font.PLAIN, 12));
        search.setBorder(BorderFactory.createCompoundBorder(new LineBorder(BR, 1, true), BorderFactory.createEmptyBorder(6, 12, 6, 12)));
        search.setPreferredSize(new Dimension(200, 36));
        search.putClientProperty("JTextField.placeholderText", "\uD83D\uDD0D  Buscar...");
        final String ftype = type;
        search.addKeyListener(new KeyAdapter() {
            public void keyReleased(KeyEvent e) {
                JTable tbl = findTable(ftype);
                if (tbl == null) return;
                String s = search.getText();
                TableRowSorter<DefaultTableModel> sorter = new TableRowSorter<>((DefaultTableModel) tbl.getModel());
                sorter.setRowFilter(s.isEmpty() ? null : RowFilter.regexFilter("(?i)" + Pattern.quote(s)));
                tbl.setRowSorter(sorter);
            }
        });

        JButton btnRefresh = mkAction("\u21BB Actualizar", BLUE, 130);
        JButton btnNew = mkAction("+ Nuevo", GREEN, 120);
        btnRefresh.addActionListener(e -> refreshTable(ftype));
        btnNew.addActionListener(e -> openDialog(ftype));

        actions.add(search);
        actions.add(btnRefresh);
        actions.add(btnNew);
        topBar.add(actions, BorderLayout.EAST);
        p.add(topBar, BorderLayout.NORTH);

        // Table
        JTable table = new JTable() {
            public boolean getScrollableTracksViewportWidth() { return true; }
        };
        table.setName("table_" + type);
        table.setFont(new Font("Segoe UI", Font.PLAIN, 12));
        table.setRowHeight(42);
        table.setBackground(BG);
        table.setForeground(T1);
        table.setSelectionBackground(BLUE);
        table.setSelectionForeground(Color.WHITE);
        table.setGridColor(new Color(30, 42, 62));
        table.setShowGrid(true);
        table.setIntercellSpacing(new Dimension(0, 1));
        table.getTableHeader().setFont(new Font("Segoe UI", Font.BOLD, 11));
        table.getTableHeader().setBackground(SURF);
        table.getTableHeader().setForeground(T3);
        table.getTableHeader().setPreferredSize(new Dimension(0, 44));
        table.getTableHeader().setBorder(new MatteBorder(0, 0, 2, 0, BLUE));
        table.setSelectionMode(ListSelectionModel.SINGLE_SELECTION);
        table.setRowMargin(1);
        table.setIntercellSpacing(new Dimension(0, 1));

        // Custom renderer for striped rows + status badges
        table.setDefaultRenderer(Object.class, new DefaultTableCellRenderer() {
            public Component getTableCellRendererComponent(JTable t, Object val, boolean sel, boolean foc, int row, int col) {
                JLabel c = (JLabel) super.getTableCellRendererComponent(t, val, sel, foc, row, col);
                if (!sel) c.setBackground(row % 2 == 0 ? BG : SURF);
                c.setBorder(BorderFactory.createEmptyBorder(0, 12, 0, 12));

                // Status badge
                if (val != null) {
                    String s = String.valueOf(val);
                    if (s.contains("\u2714 Activo")) {
                        c.setForeground(GREEN);
                        c.setFont(new Font("Segoe UI", Font.BOLD, 11));
                    } else if (s.contains("\u23F3 Pendiente")) {
                        c.setForeground(AMBER);
                        c.setFont(new Font("Segoe UI", Font.BOLD, 11));
                    } else if (s.contains("\u2716 Inactivo")) {
                        c.setForeground(RED);
                        c.setFont(new Font("Segoe UI", Font.BOLD, 11));
                    } else if (s.startsWith("$")) {
                        c.setForeground(BLUE2);
                        c.setFont(new Font("Segoe UI", Font.BOLD, 12));
                        c.setHorizontalAlignment(SwingConstants.RIGHT);
                    } else {
                        c.setForeground(sel ? Color.WHITE : T1);
                        c.setFont(new Font("Segoe UI", Font.PLAIN, 12));
                        c.setHorizontalAlignment(SwingConstants.LEFT);
                    }
                }
                return c;
            }
        });

        JScrollPane scroll = new JScrollPane(table);
        scroll.setBorder(BorderFactory.createEmptyBorder());
        scroll.getViewport().setBackground(BG);
        p.add(scroll, BorderLayout.CENTER);

        // Bottom bar
        JPanel bottomBar = new JPanel() {
            protected void paintComponent(Graphics g) {
                Graphics2D g2 = (Graphics2D) g;
                g2.setColor(SURF);
                g2.fillRect(0, 0, getWidth(), getHeight());
                g2.setColor(BR);
                g2.drawLine(0, 0, getWidth(), 0);
            }
        };
        bottomBar.setOpaque(false);
        bottomBar.setLayout(new BorderLayout());
        bottomBar.setPreferredSize(new Dimension(0, 40));
        bottomBar.setBorder(BorderFactory.createEmptyBorder(0, 30, 0, 30));
        JLabel count = new JLabel("0 registros");
        count.setName("count_" + type);
        count.setForeground(T4);
        count.setFont(new Font("Segoe UI", Font.PLAIN, 11));
        bottomBar.add(count, BorderLayout.WEST);
        p.add(bottomBar, BorderLayout.SOUTH);

        return p;
    }

    JTable findTable(String type) { return findComp(contentPanel, "table_" + type); }

    @SuppressWarnings("unchecked")
    <T extends Component> T findComp(Container c, String name) {
        for (Component comp : c.getComponents()) {
            if (name.equals(comp.getName())) return (T) comp;
            if (comp instanceof Container) { T f = findComp((Container) comp, name); if (f != null) return f; }
        }
        return null;
    }

    // ============ REFRESH ============
    void refreshTable(String type) {
        SwingWorker<Void, Void> worker = new SwingWorker<>() {
            ArrayList<HashMap<String, String>> data;
            String[] cols;
            String sql;
            protected Void doInBackground() {
                switch (type) {
                    case "clientes": sql = "SELECT CLICOD AS ID, CLINOM AS NOMBRE, CLIRFC AS RFC, CLICIUDAD AS CIUDAD, CLITEL AS TELEFONO, CLIMAIL AS EMAIL, CLIACTIVO AS ESTADO FROM TESTLIB.CLI001 ORDER BY CLICOD"; cols = new String[]{"ID","NOMBRE","RFC","CIUDAD","TELEFONO","EMAIL","ESTADO"}; break;
                    case "productos": sql = "SELECT A.ARTCOD AS ID, A.ARTNOM AS NOMBRE, C.CATNOM AS CATEGORIA, A.ARTPRE AS PRECIO, A.ARTSTK AS STOCK, A.ARTACTIVO AS ESTADO FROM TESTLIB.ART001 A LEFT JOIN TESTLIB.CAT001 C ON A.CATCOD=C.CATCOD ORDER BY A.ARTCOD"; cols = new String[]{"ID","NOMBRE","CATEGORIA","PRECIO","STOCK","ESTADO"}; break;
                    case "proveedores": sql = "SELECT PROCOD AS ID, PRONOM AS NOMBRE, PRORFC AS RFC, PROCIUDAD AS CIUDAD, PROTEL AS TELEFONO, PROMAIL AS EMAIL, PROACTIVO AS ESTADO FROM TESTLIB.PRO001 ORDER BY PROCOD"; cols = new String[]{"ID","NOMBRE","RFC","CIUDAD","TELEFONO","EMAIL","ESTADO"}; break;
                    case "facturas": sql = "SELECT F.FACNUM AS ID, CAST(F.FACFEC AS VARCHAR(10)) AS FECHA, C.CLINOM AS CLIENTE, F.FACSUB AS SUBTOTAL, F.FACAIV AS IVA, F.FACTOT AS TOTAL, F.FACEST AS ESTADO FROM TESTLIB.FAC001 F LEFT JOIN TESTLIB.CLI001 C ON F.CLICOD=C.CLICOD ORDER BY F.FACFEC DESC"; cols = new String[]{"ID","FECHA","CLIENTE","SUBTOTAL","IVA","TOTAL","ESTADO"}; break;
                    case "entradas": sql = "SELECT E.ENTNUM AS ID, CAST(E.ENTFEC AS VARCHAR(10)) AS FECHA, P.PRONOM AS PROVEEDOR, CAST(E.ALMCOD AS VARCHAR(5)) AS ALMACEN, E.ENTTOT AS TOTAL, E.ENTEST AS ESTADO FROM TESTLIB.ENT001 E LEFT JOIN TESTLIB.PRO001 P ON E.PROCOD=P.PROCOD ORDER BY E.ENTFEC DESC"; cols = new String[]{"ID","FECHA","PROVEEDOR","ALMACEN","TOTAL","ESTADO"}; break;
                    case "salidas": sql = "SELECT S.SALNUM AS ID, CAST(S.SALFEC AS VARCHAR(10)) AS FECHA, COALESCE(S.SALMOT,'') AS TIPO, CAST(S.ALMCOD AS VARCHAR(5)) AS ALMACEN, COALESCE((SELECT SUM(SL.SLDTOT) FROM TESTLIB.SLD001 SL WHERE SL.SALNUM=S.SALNUM),0) AS TOTAL, S.SALEST AS ESTADO FROM TESTLIB.SAL001 S ORDER BY S.SALFEC DESC"; cols = new String[]{"ID","FECHA","TIPO","ALMACEN","TOTAL","ESTADO"}; break;
                    case "devoluciones": sql = "SELECT D.DEVNUM AS ID, CAST(D.DEVFEC AS VARCHAR(10)) AS FECHA, D.FACNUM AS FACTURA, C.CLINOM AS CLIENTE, D.DEVMOT AS MOTIVO, D.DEVTOT AS TOTAL, D.DEVEST AS ESTADO FROM TESTLIB.DEV001 D LEFT JOIN TESTLIB.CLI001 C ON D.CLICOD=C.CLICOD ORDER BY D.DEVFEC DESC"; cols = new String[]{"ID","FECHA","FACTURA","CLIENTE","MOTIVO","TOTAL","ESTADO"}; break;
                    case "pagos": sql = "SELECT P.PAGNUM AS ID, CAST(P.PAGFEC AS VARCHAR(10)) AS FECHA, P.FACNUM AS FACTURA, C.CLINOM AS CLIENTE, P.PAGMET AS METODO, P.PAGMON AS MONTO, P.PAGEST AS ESTADO FROM TESTLIB.PAG001 P LEFT JOIN TESTLIB.CLI001 C ON P.CLICOD=C.CLICOD ORDER BY P.PAGFEC DESC"; cols = new String[]{"ID","FECHA","FACTURA","CLIENTE","METODO","MONTO","ESTADO"}; break;
                    default: sql = ""; cols = new String[]{};
                }
                data = queryList(sql);
                return null;
            }
            protected void done() {
                try {
                    JTable tbl = findTable(type);
                    if (tbl == null) return;
                    String[] moneyCols = {"SUBTOTAL","IVA","TOTAL","MONTO","PRECIO"};
                    DefaultTableModel model = new DefaultTableModel(cols, 0) {
                        public boolean isCellEditable(int r, int c) { return c == cols.length; }
                    };
                    for (HashMap<String, String> row : data) {
                        Object[] vals = new Object[cols.length + 1];
                        for (int i = 0; i < cols.length; i++) {
                            String val = row.get(cols[i].toLowerCase());
                            boolean isMoney = false;
                            for (String mc : moneyCols) if (cols[i].equals(mc)) isMoney = true;
                            if (isMoney) {
                                try { vals[i] = String.format("$%,.2f", Double.parseDouble(val != null ? val : "0")); } catch (Exception ex) { vals[i] = "$0.00"; }
                            } else if (cols[i].equals("ESTADO")) {
                                String v = val != null ? val : "";
                                if (v.equals("C") || v.equals("S") || v.equals("A")) vals[i] = "\u2714 Activo";
                                else if (v.equals("P")) vals[i] = "\u23F3 Pendiente";
                                else if (v.equals("I")) vals[i] = "\u2716 Inactivo";
                                else vals[i] = v;
                            } else vals[i] = val != null ? val : "";
                        }
                        vals[cols.length] = "";
                        model.addRow(vals);
                    }
                    tbl.setModel(model);
                    TableColumn actionCol = new TableColumn();
                    actionCol.setHeaderValue("ACCIONES");
                    actionCol.setPreferredWidth(160);
                    actionCol.setMinWidth(160);
                    actionCol.setCellRenderer(new ActRenderer());
                    actionCol.setCellEditor(new ActEditor(tbl, type));
                    tbl.getColumnModel().addColumn(actionCol);
                    JLabel count = findComp(contentPanel, "count_" + type);
                    if (count != null) count.setText(data.size() + " registros");
                } catch (Exception e) { e.printStackTrace(); }
            }
        };
        worker.execute();
    }

    // ============ ACTION CELLS ============
    class ActRenderer extends JPanel implements TableCellRenderer {
        ActRenderer() {
            setLayout(new FlowLayout(FlowLayout.CENTER, 6, 6));
            setOpaque(true);
            add(smallBtn("Editar", BLUE));
            add(smallBtn("Eliminar", RED));
        }
        JPanel smallBtn(String t, Color c) {
            JPanel p = new JPanel(new BorderLayout());
            p.setBackground(c);
            p.setPreferredSize(new Dimension(78, 28));
            p.setBorder(BorderFactory.createEmptyBorder(2, 0, 2, 0));
            JLabel l = new JLabel(t, SwingConstants.CENTER);
            l.setForeground(Color.WHITE);
            l.setFont(new Font("Segoe UI", Font.BOLD, 10));
            p.add(l);
            return p;
        }
        public Component getTableCellRendererComponent(JTable t, Object v, boolean sel, boolean foc, int row, int col) {
            setBackground(sel ? BLUE : (row % 2 == 0 ? BG : SURF));
            return this;
        }
    }

    class ActEditor extends AbstractCellEditor implements TableCellEditor {
        JPanel panel = new JPanel(new FlowLayout(FlowLayout.CENTER, 6, 6));
        JButton editBtn, delBtn;
        JTable table; String type;

        ActEditor(JTable table, String type) {
            this.table = table; this.type = type;
            panel.setOpaque(true);
            panel.setBackground(BG);

            editBtn = mkEditorBtn("Editar", BLUE);
            delBtn = mkEditorBtn("Eliminar", RED);
            panel.add(editBtn);
            panel.add(delBtn);

            editBtn.addActionListener(e -> {
                int row = table.getEditingRow();
                fireEditingStopped();
                if (row >= 0) editItem(type, table.convertRowIndexToModel(row));
            });
            delBtn.addActionListener(e -> {
                int row = table.getEditingRow();
                fireEditingStopped();
                if (row >= 0) deleteItem(type, table.convertRowIndexToModel(row));
            });
        }

        JButton mkEditorBtn(String t, Color c) {
            JButton b = new JButton(t);
            b.setBackground(c); b.setForeground(Color.WHITE);
            b.setFont(new Font("Segoe UI", Font.BOLD, 10));
            b.setPreferredSize(new Dimension(78, 28));
            b.setFocusPainted(false); b.setBorderPainted(false); b.setOpaque(true);
            b.setCursor(Cursor.getPredefinedCursor(Cursor.HAND_CURSOR));
            return b;
        }

        public Component getTableCellEditorComponent(JTable t, Object v, boolean sel, int row, int col) { return panel; }
        public Object getCellEditorValue() { return ""; }
    }

    // ============ CRUD OPS ============
    void openDialog(String type) {
        switch (type) {
            case "clientes": new ClienteDlg(this, null); break;
            case "productos": new ProductoDlg(this, null); break;
            case "proveedores": new ProveedorDlg(this, null); break;
            case "facturas": new FacturaDlg(this); break;
            case "entradas": new EntradaDlg(this); break;
            case "salidas": new SalidaDlg(this); break;
            case "devoluciones": new DevolucionDlg(this); break;
            case "pagos": new PagoDlg(this); break;
        }
    }

    void editItem(String type, int modelRow) {
        JTable tbl = findTable(type);
        if (tbl == null || modelRow < 0 || modelRow >= tbl.getRowCount()) return;
        String id = String.valueOf(tbl.getValueAt(modelRow, 0));
        switch (type) {
            case "clientes": ArrayList<HashMap<String, String>> cl = queryList("SELECT * FROM TESTLIB.CLI001 WHERE CLICOD=" + id); if (!cl.isEmpty()) new ClienteDlg(this, cl.get(0)); break;
            case "productos": ArrayList<HashMap<String, String>> pr = queryList("SELECT * FROM TESTLIB.ART001 WHERE ARTCOD=" + id); if (!pr.isEmpty()) new ProductoDlg(this, pr.get(0)); break;
            case "proveedores": ArrayList<HashMap<String, String>> pv = queryList("SELECT * FROM TESTLIB.PRO001 WHERE PROCOD=" + id); if (!pv.isEmpty()) new ProveedorDlg(this, pv.get(0)); break;
            default: JOptionPane.showMessageDialog(this, "Edicion no disponible para " + type);
        }
    }

    void deleteItem(String type, int modelRow) {
        JTable tbl = findTable(type);
        if (tbl == null || modelRow < 0 || modelRow >= tbl.getRowCount()) return;
        String id = String.valueOf(tbl.getValueAt(modelRow, 0));
        int c = JOptionPane.showConfirmDialog(this, "\u274C Eliminar registro " + id + "?", "Confirmar", JOptionPane.YES_NO_OPTION, JOptionPane.WARNING_MESSAGE);
        if (c == JOptionPane.YES_OPTION) {
            switch (type) {
                case "clientes": execute("DELETE FROM TESTLIB.CLI001 WHERE CLICOD=" + id); break;
                case "productos": execute("DELETE FROM TESTLIB.ART001 WHERE ARTCOD=" + id); break;
                case "proveedores": execute("DELETE FROM TESTLIB.PRO001 WHERE PROCOD=" + id); break;
                case "facturas": execute("DELETE FROM TESTLIB.FAD001 WHERE FACNUM='" + id + "'"); execute("DELETE FROM TESTLIB.FAC001 WHERE FACNUM='" + id + "'"); break;
                case "entradas": execute("DELETE FROM TESTLIB.ETD001 WHERE ENTNUM='" + id + "'"); execute("DELETE FROM TESTLIB.ENT001 WHERE ENTNUM='" + id + "'"); break;
                case "salidas": execute("DELETE FROM TESTLIB.SLD001 WHERE SALNUM='" + id + "'"); execute("DELETE FROM TESTLIB.SAL001 WHERE SALNUM='" + id + "'"); break;
                case "devoluciones": execute("DELETE FROM TESTLIB.DVD001 WHERE DEVNUM='" + id + "'"); execute("DELETE FROM TESTLIB.DEV001 WHERE DEVNUM='" + id + "'"); break;
                case "pagos": execute("DELETE FROM TESTLIB.PAG001 WHERE PAGNUM='" + id + "'"); break;
            }
            refreshTable(type);
        }
    }

    // ============ DIALOG BASE ============
    static class Dlg extends JDialog {
        Dlg(JFrame parent, String title, int w, int h) {
            super(parent, title, true);
            setSize(w, h);
            setLocationRelativeTo(parent);
            getContentPane().setBackground(BG);
            setLayout(new BorderLayout());
        }
        JPanel form(int rows) {
            JPanel f = new JPanel(new GridLayout(rows, 1, 0, 12));
            f.setOpaque(false);
            f.setBorder(BorderFactory.createEmptyBorder(25, 35, 15, 35));
            return f;
        }
        JPanel btns(JButton... bs) {
            JPanel p = new JPanel(new FlowLayout(FlowLayout.CENTER, 15, 12));
            p.setBackground(SURF);
            p.setBorder(BorderFactory.createMatteBorder(1, 0, 0, 0, BR));
            for (JButton b : bs) p.add(b);
            return p;
        }
    }

    static class ClienteDlg extends Dlg {
        ClienteDlg(JFrame p, HashMap<String, String> ed) {
            super(p, ed == null ? "\u2795 Nuevo Cliente" : "\u270F Editar Cliente", 520, 520);
            JPanel f = form(6);
            JTextField n = mkIn(ed != null ? ed.get("clinom") : "");
            JTextField r = mkIn(ed != null ? ed.get("clirfc") : "");
            JTextField ci = mkIn(ed != null ? ed.get("cliciudad") : "");
            JTextField t = mkIn(ed != null ? ed.get("clitel") : "");
            JTextField e = mkIn(ed != null ? ed.get("climail") : "");
            JComboBox<String> es = mkCmb(new String[]{"S - Activo", "I - Inactivo"});
            if (ed != null && "I".equals(ed.get("cliautivo"))) es.setSelectedIndex(1);
            f.add(mkFld("Nombre *", n)); f.add(mkFld("RFC", r)); f.add(mkFld("Ciudad", ci));
            f.add(mkFld("Telefono", t)); f.add(mkFld("Email", e)); f.add(mkFld("Estado", es));
            add(f, BorderLayout.CENTER);
            JButton save = mkAction("\u2714 Guardar", GREEN, 150);
            JButton cancel = mkAction("\u2716 Cancelar", RED, 130);
            add(btns(save, cancel), BorderLayout.SOUTH);
            save.addActionListener(ev -> {
                if (n.getText().trim().isEmpty()) { JOptionPane.showMessageDialog(this, "Nombre obligatorio"); return; }
                String est = ((String)es.getSelectedItem()).substring(0, 1);
                if (ed != null) execute("UPDATE TESTLIB.CLI001 SET CLINOM='"+n.getText().trim()+"', CLIRFC='"+r.getText().trim()+"', CLICIUDAD='"+ci.getText().trim()+"', CLITEL='"+t.getText().trim()+"', CLIMAIL='"+e.getText().trim()+"', CLIACTIVO='"+est+"' WHERE CLICOD="+ed.get("clicod"));
                else { int nid = (int)scalar("SELECT COALESCE(MAX(CLICOD),0)+1 FROM TESTLIB.CLI001"); execute("INSERT INTO TESTLIB.CLI001 (CLICOD,CLINOM,CLIRFC,CLIDIR,CLITEL,CLIMAIL,CLICIUDAD,CLIACTIVO,CLIFREG) VALUES ("+nid+",'"+n.getText().trim()+"','"+r.getText().trim()+"','"+ci.getText().trim()+"','"+t.getText().trim()+"','"+e.getText().trim()+"','"+ci.getText().trim()+"','"+est+"',CURRENT_DATE)"); }
                dispose();
                if (p instanceof AppAS400) ((AppAS400)p).refreshTable("clientes");
                JOptionPane.showMessageDialog(p, "\u2714 Cliente guardado");
            });
            cancel.addActionListener(ev -> dispose());
            setVisible(true);
        }
    }

    static class ProductoDlg extends Dlg {
        ProductoDlg(JFrame p, HashMap<String, String> ed) {
            super(p, ed == null ? "\u2795 Nuevo Producto" : "\u270F Editar Producto", 520, 460);
            ArrayList<HashMap<String, String>> cats = queryList("SELECT CATCOD, CATNOM FROM TESTLIB.CAT001 ORDER BY CATCOD");
            String[] cn = new String[cats.size()];
            for (int i = 0; i < cats.size(); i++) cn[i] = cats.get(i).get("catcod") + " - " + cats.get(i).get("catnom");
            JPanel f = form(5);
            JTextField n = mkIn(ed != null ? ed.get("artnom") : "");
            JComboBox<String> cat = mkCmb(cn);
            JTextField pr = mkIn(ed != null ? ed.get("artpre") : "0");
            JTextField st = mkIn(ed != null ? ed.get("artstk") : "0");
            JComboBox<String> es = mkCmb(new String[]{"S - Activo", "I - Inactivo"});
            if (ed != null && "I".equals(ed.get("artactivo"))) es.setSelectedIndex(1);
            f.add(mkFld("Nombre *", n)); f.add(mkFld("Categoria", cat)); f.add(mkFld("Precio", pr));
            f.add(mkFld("Stock", st)); f.add(mkFld("Estado", es));
            add(f, BorderLayout.CENTER);
            JButton save = mkAction("\u2714 Guardar", GREEN, 150);
            JButton cancel = mkAction("\u2716 Cancelar", RED, 130);
            add(btns(save, cancel), BorderLayout.SOUTH);
            save.addActionListener(ev -> {
                if (n.getText().trim().isEmpty()) { JOptionPane.showMessageDialog(this, "Nombre obligatorio"); return; }
                String cs = ((String)cat.getSelectedItem()).split(" - ")[0];
                String est = ((String)es.getSelectedItem()).substring(0, 1);
                double pr2 = 0; int st2 = 0;
                try { pr2 = Double.parseDouble(pr.getText().trim()); } catch (Exception ex) {}
                try { st2 = Integer.parseInt(st.getText().trim()); } catch (Exception ex) {}
                if (ed != null) execute("UPDATE TESTLIB.ART001 SET ARTNOM='"+n.getText().trim()+"', CATCOD="+cs+", ARTPRE="+pr2+", ARTSTK="+st2+", ARTACTIVO='"+est+"' WHERE ARTCOD="+ed.get("artcod"));
                else { int nid = (int)scalar("SELECT COALESCE(MAX(ARTCOD),0)+1 FROM TESTLIB.ART001"); execute("INSERT INTO TESTLIB.ART001 (ARTCOD,ARTNOM,ARTDSC,CATCOD,ARTPRE,ARTCOS,ARTSTK,ARTSTM,ARTUNI,ARTACTIVO) VALUES ("+nid+",'"+n.getText().trim()+"','',"+cs+","+pr2+","+pr2+","+st2+",10,'pza','"+est+"')"); }
                dispose();
                if (p instanceof AppAS400) ((AppAS400)p).refreshTable("productos");
                JOptionPane.showMessageDialog(p, "\u2714 Producto guardado");
            });
            cancel.addActionListener(ev -> dispose());
            setVisible(true);
        }
    }

    static class ProveedorDlg extends Dlg {
        ProveedorDlg(JFrame p, HashMap<String, String> ed) {
            super(p, ed == null ? "\u2795 Nuevo Proveedor" : "\u270F Editar Proveedor", 520, 520);
            JPanel f = form(6);
            JTextField n = mkIn(ed != null ? ed.get("pronom") : "");
            JTextField r = mkIn(ed != null ? ed.get("prorfc") : "");
            JTextField ci = mkIn(ed != null ? ed.get("prociudad") : "");
            JTextField t = mkIn(ed != null ? ed.get("protel") : "");
            JTextField e = mkIn(ed != null ? ed.get("promail") : "");
            JComboBox<String> es = mkCmb(new String[]{"S - Activo", "I - Inactivo"});
            if (ed != null && "I".equals(ed.get("proactivo"))) es.setSelectedIndex(1);
            f.add(mkFld("Nombre *", n)); f.add(mkFld("RFC", r)); f.add(mkFld("Ciudad", ci));
            f.add(mkFld("Telefono", t)); f.add(mkFld("Email", e)); f.add(mkFld("Estado", es));
            add(f, BorderLayout.CENTER);
            JButton save = mkAction("\u2714 Guardar", GREEN, 150);
            JButton cancel = mkAction("\u2716 Cancelar", RED, 130);
            add(btns(save, cancel), BorderLayout.SOUTH);
            save.addActionListener(ev -> {
                if (n.getText().trim().isEmpty()) { JOptionPane.showMessageDialog(this, "Nombre obligatorio"); return; }
                String est = ((String)es.getSelectedItem()).substring(0, 1);
                if (ed != null) execute("UPDATE TESTLIB.PRO001 SET PRONOM='"+n.getText().trim()+"', PRORFC='"+r.getText().trim()+"', PROCIUDAD='"+ci.getText().trim()+"', PROTEL='"+t.getText().trim()+"', PROMAIL='"+e.getText().trim()+"', PROACTIVO='"+est+"' WHERE PROCOD="+ed.get("procod"));
                else { int nid = (int)scalar("SELECT COALESCE(MAX(PROCOD),0)+1 FROM TESTLIB.PRO001"); execute("INSERT INTO TESTLIB.PRO001 (PROCOD,PRONOM,PRORFC,PRODIR,PROTEL,PROMAIL,PROCIUDAD,PROACTIVO) VALUES ("+nid+",'"+n.getText().trim()+"','"+r.getText().trim()+"','','"+t.getText().trim()+"','"+e.getText().trim()+"','"+ci.getText().trim()+"','"+est+"')"); }
                dispose();
                if (p instanceof AppAS400) ((AppAS400)p).refreshTable("proveedores");
                JOptionPane.showMessageDialog(p, "\u2714 Proveedor guardado");
            });
            cancel.addActionListener(ev -> dispose());
            setVisible(true);
        }
    }

    static class FacturaDlg extends Dlg {
        FacturaDlg(JFrame p) {
            super(p, "\u2795 Nueva Factura", 560, 540);
            ArrayList<HashMap<String, String>> cls = queryList("SELECT CLICOD, CLINOM FROM TESTLIB.CLI001 ORDER BY CLICOD");
            String[] cn = new String[cls.size()];
            for (int i = 0; i < cls.size(); i++) cn[i] = cls.get(i).get("clicod") + " - " + cls.get(i).get("clinom");
            JPanel f = form(5);
            JTextField fe = mkIn(new SimpleDateFormat("yyyy-MM-dd").format(new Date()));
            JComboBox<String> cl = mkCmb(cn);
            JTextField sub = mkIn("0"), iva = mkIn("0"), tot = mkIn("0");
            iva.setEditable(false); tot.setEditable(false);
            sub.addKeyListener(new KeyAdapter() { public void keyReleased(KeyEvent e) { try { double s = Double.parseDouble(sub.getText().trim()); double i = s*0.16; iva.setText(String.format("%.2f",i)); tot.setText(String.format("%.2f",s+i)); } catch (Exception ex) {} } });
            f.add(mkFld("Fecha", fe)); f.add(mkFld("Cliente", cl));
            f.add(mkFld("Subtotal", sub)); f.add(mkFld("IVA (16%)", iva)); f.add(mkFld("Total", tot));
            add(f, BorderLayout.CENTER);
            JButton save = mkAction("\u2714 Crear Factura", GREEN, 160);
            JButton cancel = mkAction("\u2716 Cancelar", RED, 130);
            add(btns(save, cancel), BorderLayout.SOUTH);
            save.addActionListener(ev -> {
                String cid = ((String)cl.getSelectedItem()).split(" - ")[0];
                double s = 0; try { s = Double.parseDouble(sub.getText().trim()); } catch (Exception ex) {}
                double i = s*0.16;
                int n = (int)scalar("SELECT COALESCE(MAX(CAST(SUBSTRING(FACNUM,8) AS INT)),0)+1 FROM TESTLIB.FAC001 WHERE FACNUM LIKE 'FAC2026%'");
                String fn = "FAC2026"+String.format("%04d",n);
                execute("INSERT INTO TESTLIB.FAC001 (FACNUM,FACFEC,CLICOD,ALMCOD,FACSUB,FACAIV,FACTOT,FACEST,FACUSU) VALUES ('"+fn+"','"+fe.getText().trim()+"',"+cid+",1,"+s+","+i+","+(s+i)+",'P','"+usuarioActual+"')");
                dispose();
                if (p instanceof AppAS400) ((AppAS400)p).refreshTable("facturas");
                JOptionPane.showMessageDialog(p, "\u2714 Factura "+fn+" creada");
            });
            cancel.addActionListener(ev -> dispose());
            setVisible(true);
        }
    }

    static class EntradaDlg extends Dlg {
        EntradaDlg(JFrame p) {
            super(p, "\u2795 Nueva Entrada", 520, 440);
            ArrayList<HashMap<String, String>> ps = queryList("SELECT PROCOD, PRONOM FROM TESTLIB.PRO001 ORDER BY PROCOD");
            String[] pn = new String[ps.size()];
            for (int i = 0; i < ps.size(); i++) pn[i] = ps.get(i).get("procod") + " - " + ps.get(i).get("pronom");
            JPanel f = form(4);
            JTextField fe = mkIn(new SimpleDateFormat("yyyy-MM-dd").format(new Date()));
            JComboBox<String> pr = mkCmb(pn);
            JComboBox<String> al = mkCmb(new String[]{"1 - ALM01", "2 - ALM02", "3 - ALM03"});
            JTextField tot = mkIn("0");
            f.add(mkFld("Fecha", fe)); f.add(mkFld("Proveedor", pr));
            f.add(mkFld("Almacen", al)); f.add(mkFld("Total", tot));
            add(f, BorderLayout.CENTER);
            JButton save = mkAction("\u2714 Registrar", GREEN, 150);
            JButton cancel = mkAction("\u2716 Cancelar", RED, 130);
            add(btns(save, cancel), BorderLayout.SOUTH);
            save.addActionListener(ev -> {
                String pid = ((String)pr.getSelectedItem()).split(" - ")[0];
                String aid = ((String)al.getSelectedItem()).split(" - ")[0];
                double t = 0; try { t = Double.parseDouble(tot.getText().trim()); } catch (Exception ex) {}
                int n = (int)scalar("SELECT COALESCE(MAX(CAST(SUBSTRING(ENTNUM,4) AS INT)),0)+1 FROM TESTLIB.ENT001");
                String en = "ENT"+String.format("%06d",n);
                execute("INSERT INTO TESTLIB.ENT001 (ENTNUM,ENTFEC,PROCOD,ALMCOD,ENTREF,ENTTOT,ENTEST) VALUES ('"+en+"','"+fe.getText().trim()+"',"+pid+","+aid+",'',"+t+",'A')");
                dispose();
                if (p instanceof AppAS400) ((AppAS400)p).refreshTable("entradas");
                JOptionPane.showMessageDialog(p, "\u2714 Entrada "+en+" registrada");
            });
            cancel.addActionListener(ev -> dispose());
            setVisible(true);
        }
    }

    static class SalidaDlg extends Dlg {
        SalidaDlg(JFrame p) {
            super(p, "\u2795 Nueva Salida", 520, 400);
            JPanel f = form(4);
            JTextField fe = mkIn(new SimpleDateFormat("yyyy-MM-dd").format(new Date()));
            JTextField mot = mkIn("");
            JComboBox<String> al = mkCmb(new String[]{"1 - ALM01", "2 - ALM02", "3 - ALM03"});
            JComboBox<String> es = mkCmb(new String[]{"A - Activa", "C - Completada"});
            f.add(mkFld("Fecha", fe)); f.add(mkFld("Motivo", mot));
            f.add(mkFld("Almacen", al)); f.add(mkFld("Estado", es));
            add(f, BorderLayout.CENTER);
            JButton save = mkAction("\u2714 Registrar", GREEN, 150);
            JButton cancel = mkAction("\u2716 Cancelar", RED, 130);
            add(btns(save, cancel), BorderLayout.SOUTH);
            save.addActionListener(ev -> {
                String aid = ((String)al.getSelectedItem()).split(" - ")[0];
                String est = ((String)es.getSelectedItem()).substring(0, 1);
                int n = (int)scalar("SELECT COALESCE(MAX(CAST(SUBSTRING(SALNUM,4) AS INT)),0)+1 FROM TESTLIB.SAL001");
                String sn = "SAL"+String.format("%06d",n);
                execute("INSERT INTO TESTLIB.SAL001 (SALNUM,SALFEC,ALMCOD,SALREF,SALMOT,SALEST) VALUES ('"+sn+"','"+fe.getText().trim()+"',"+aid+",'','"+mot.getText().trim()+"','"+est+"')");
                dispose();
                if (p instanceof AppAS400) ((AppAS400)p).refreshTable("salidas");
                JOptionPane.showMessageDialog(p, "\u2714 Salida "+sn+" registrada");
            });
            cancel.addActionListener(ev -> dispose());
            setVisible(true);
        }
    }

    static class DevolucionDlg extends Dlg {
        DevolucionDlg(JFrame p) {
            super(p, "\u2795 Nueva Devolucion", 560, 500);
            ArrayList<HashMap<String, String>> fs = queryList("SELECT FACNUM FROM TESTLIB.FAC001 ORDER BY FACFEC DESC FETCH FIRST 50 ROWS ONLY");
            String[] fn = new String[fs.size()]; for (int i = 0; i < fs.size(); i++) fn[i] = fs.get(i).get("facnum");
            ArrayList<HashMap<String, String>> cs = queryList("SELECT CLICOD, CLINOM FROM TESTLIB.CLI001 ORDER BY CLICOD");
            String[] cn = new String[cs.size()]; for (int i = 0; i < cs.size(); i++) cn[i] = cs.get(i).get("clicod") + " - " + cs.get(i).get("clinom");
            JPanel f = form(5);
            JTextField fe = mkIn(new SimpleDateFormat("yyyy-MM-dd").format(new Date()));
            JComboBox<String> fa = mkCmb(fn);
            JComboBox<String> cl = mkCmb(cn);
            JTextField mot = mkIn(""); JTextField tot = mkIn("0");
            f.add(mkFld("Fecha", fe)); f.add(mkFld("Factura", fa));
            f.add(mkFld("Cliente", cl)); f.add(mkFld("Motivo", mot)); f.add(mkFld("Total", tot));
            add(f, BorderLayout.CENTER);
            JButton save = mkAction("\u2714 Registrar", GREEN, 150);
            JButton cancel = mkAction("\u2716 Cancelar", RED, 130);
            add(btns(save, cancel), BorderLayout.SOUTH);
            save.addActionListener(ev -> {
                String cid = ((String)cl.getSelectedItem()).split(" - ")[0];
                double t = 0; try { t = Double.parseDouble(tot.getText().trim()); } catch (Exception ex) {}
                int n = (int)scalar("SELECT COALESCE(MAX(CAST(SUBSTRING(DEVNUM,4) AS INT)),0)+1 FROM TESTLIB.DEV001");
                String dn = "DEV"+String.format("%06d",n);
                execute("INSERT INTO TESTLIB.DEV001 (DEVNUM,DEVFEC,FACNUM,CLICOD,DEVTOT,DEVMOT,DEVEST) VALUES ('"+dn+"','"+fe.getText().trim()+"','"+fa.getSelectedItem()+"',"+cid+","+t+",'"+mot.getText().trim()+"','A')");
                dispose();
                if (p instanceof AppAS400) ((AppAS400)p).refreshTable("devoluciones");
                JOptionPane.showMessageDialog(p, "\u2714 Devolucion "+dn+" registrada");
            });
            cancel.addActionListener(ev -> dispose());
            setVisible(true);
        }
    }

    static class PagoDlg extends Dlg {
        PagoDlg(JFrame p) {
            super(p, "\u2795 Nuevo Pago", 560, 540);
            ArrayList<HashMap<String, String>> fs = queryList("SELECT FACNUM, CAST(FACTOT AS VARCHAR(20)) AS TOT FROM TESTLIB.FAC001 WHERE FACEST='P' ORDER BY FACFEC DESC");
            String[] fn = new String[fs.size()]; for (int i = 0; i < fs.size(); i++) fn[i] = fs.get(i).get("facnum") + " ($" + fs.get(i).get("tot") + ")";
            ArrayList<HashMap<String, String>> cs = queryList("SELECT CLICOD, CLINOM FROM TESTLIB.CLI001 ORDER BY CLICOD");
            String[] cn = new String[cs.size()]; for (int i = 0; i < cs.size(); i++) cn[i] = cs.get(i).get("clicod") + " - " + cs.get(i).get("clinom");
            JPanel f = form(5);
            JTextField fe = mkIn(new SimpleDateFormat("yyyy-MM-dd").format(new Date()));
            JComboBox<String> fa = mkCmb(fn);
            JComboBox<String> cl = mkCmb(cn);
            JComboBox<String> met = mkCmb(new String[]{"Efectivo", "Transferencia", "Tarjeta", "Cheque"});
            JTextField mon = mkIn("0");
            f.add(mkFld("Fecha", fe)); f.add(mkFld("Factura", fa));
            f.add(mkFld("Cliente", cl)); f.add(mkFld("Metodo", met)); f.add(mkFld("Monto", mon));
            add(f, BorderLayout.CENTER);
            JButton save = mkAction("\u2714 Registrar", GREEN, 150);
            JButton cancel = mkAction("\u2716 Cancelar", RED, 130);
            add(btns(save, cancel), BorderLayout.SOUTH);
            save.addActionListener(ev -> {
                String cid = ((String)cl.getSelectedItem()).split(" - ")[0];
                String fid = ((String)fa.getSelectedItem()).split(" \\(")[0];
                double m = 0; try { m = Double.parseDouble(mon.getText().trim()); } catch (Exception ex) {}
                String mt = ((String)met.getSelectedItem()).toUpperCase();
                int n = (int)scalar("SELECT COALESCE(MAX(CAST(SUBSTRING(PAGNUM,4) AS INT)),0)+1 FROM TESTLIB.PAG001");
                String pn = "PAG"+String.format("%04d",n);
                execute("INSERT INTO TESTLIB.PAG001 (PAGNUM,PAGFEC,FACNUM,CLICOD,PAGMON,PAGMET,PAGEST) VALUES ('"+pn+"','"+fe.getText().trim()+"','"+fid+"',"+cid+","+m+",'"+mt+"','A')");
                execute("UPDATE TESTLIB.FAC001 SET FACEST='C' WHERE FACNUM='"+fid+"'");
                dispose();
                if (p instanceof AppAS400) ((AppAS400)p).refreshTable("pagos");
                JOptionPane.showMessageDialog(p, "\u2714 Pago "+pn+" registrado");
            });
            cancel.addActionListener(ev -> dispose());
            setVisible(true);
        }
    }
}
