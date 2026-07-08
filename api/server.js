/**
 * LAST MILE DELIVERY SYSTEM - Backend API
 * Conecta a AS/400 (TESTLIB) via JDBC
 * Multi-tenant: cada request lleva EMP_ID
 */

const express = require('express');
const cors = require('cors');
const ibmi = require('ibmi_db2');
require('dotenv').config();

const app = express();
app.use(cors());
app.use(express.json());

// ========================================
// CONFIGURACIÓN
// ========================================
const CONFIG = {
  port: process.env.PORT || 3000,
  db: {
    host: '192.168.0.240',
    database: '*LOCAL',
    user: 'AYUDATX',
    password: 'MXTAC23'
  }
};

// ========================================
// MIDDLEWARE: Extraer EMP_ID del token/header
// ========================================
app.use((req, res, next) => {
  req.empId = parseInt(req.headers['x-emp-id'] || '1');
  next();
});

// ========================================
// HEALTH CHECK
// ========================================
app.get('/api/health', (req, res) => {
  res.json({ status: 'OK', timestamp: new Date().toISOString(), version: '1.0.0' });
});

// ========================================
// MÓDULO: EMPRESAS
// ========================================
app.get('/api/empresas', async (req, res) => {
  try {
    const conn = await ibmi.getConnection(CONFIG.db);
    const result = await conn.query('SELECT * FROM TESTLIB.EMPRESAS ORDER BY EMP_ID');
    await conn.close();
    res.json({ success: true, data: result });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

app.get('/api/empresas/:id', async (req, res) => {
  try {
    const conn = await ibmi.getConnection(CONFIG.db);
    const result = await conn.query('SELECT * FROM TESTLIB.EMPRESAS WHERE EMP_ID = ?', [req.params.id]);
    await conn.close();
    res.json({ success: true, data: result[0] || null });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// ========================================
// MÓDULO: DASHBOARD
// ========================================
app.get('/api/dashboard/:empId', async (req, res) => {
  try {
    const conn = await ibmi.getConnection(CONFIG.db);
    const result = await conn.query('SELECT * FROM TESTLIB.V_DASHBOARD_RESUMEN WHERE EMP_ID = ?', [req.params.empId]);
    await conn.close();
    res.json({ success: true, data: result[0] || {} });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// ========================================
// MÓDULO: PEDIDOS
// ========================================
app.get('/api/pedidos', async (req, res) => {
  try {
    const conn = await ibmi.getConnection(CONFIG.db);
    const { estado, limite } = req.query;
    let sql = 'SELECT * FROM TESTLIB.V_PEDIDOS_COMPLETO WHERE EMP_ID = ?';
    const params = [req.empId];
    if (estado) { sql += ' AND PED_ESTADO = ?'; params.push(estado); }
    sql += ' ORDER BY PED_FECHA_PEDIDO DESC';
    if (limite) { sql += ' FETCH FIRST ' + parseInt(limite) + ' ROWS ONLY'; }
    const result = await conn.query(sql, params);
    await conn.close();
    res.json({ success: true, data: result, total: result.length });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

app.get('/api/pedidos/:id', async (req, res) => {
  try {
    const conn = await ibmi.getConnection(CONFIG.db);
    const result = await conn.query('SELECT * FROM TESTLIB.V_PEDIDOS_COMPLETO WHERE PED_ID = ? AND EMP_ID = ?', [req.params.id, req.empId]);
    await conn.close();
    res.json({ success: true, data: result[0] || null });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

app.post('/api/pedidos', async (req, res) => {
  try {
    const conn = await ibmi.getConnection(CONFIG.db);
    const p = req.body;
    const result = await conn.query(
      `INSERT INTO TESTLIB.PEDIDOS (EMP_ID, PED_NUMERO, CLI_ID, PED_CLIENTE_NOMBRE, 
       PED_CLIENTE_TELEFONO, PED_DESTINO_DIR, PED_DESTINO_COL, PED_DESTINO_CIUDAD,
       PED_PESO_KG, PED_BULTOS, PED_COSTO_TOTAL, PED_FORMA_PAGO, PED_ESTADO, PED_PRIORIDAD)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'PENDIENTE', ?)`,
      [req.empId, p.pedNumero, p.cliId, p.clienteNombre, p.clienteTelefono,
       p.destinoDir, p.destinoCol, p.destinoCiudad, p.pesoKg, p.bultos,
       p.costoTotal, p.formaPago, p.prioridad]
    );
    await conn.close();
    res.json({ success: true, data: { id: result.insertId } });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

app.put('/api/pedidos/:id/estado', async (req, res) => {
  try {
    const conn = await ibmi.getConnection(CONFIG.db);
    await conn.query('UPDATE TESTLIB.PEDIDOS SET PED_ESTADO = ? WHERE PED_ID = ? AND EMP_ID = ?',
      [req.body.estado, req.params.id, req.empId]);
    await conn.query('INSERT INTO TESTLIB.PEDIDO_HISTORIAL (PED_ID, HIS_ESTADO, HIS_USUARIO) VALUES (?, ?, ?)',
      [req.params.id, req.body.estado, req.body.usuario || 'SYSTEM']);
    await conn.close();
    res.json({ success: true });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// ========================================
// MÓDULO: CHOFERES
// ========================================
app.get('/api/choferes', async (req, res) => {
  try {
    const conn = await ibmi.getConnection(CONFIG.db);
    const result = await conn.query('SELECT * FROM TESTLIB.CHOFERES WHERE EMP_ID = ? ORDER BY CHO_NOMBRE', [req.empId]);
    await conn.close();
    res.json({ success: true, data: result });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

app.get('/api/choferes/rendimiento', async (req, res) => {
  try {
    const conn = await ibmi.getConnection(CONFIG.db);
    const result = await conn.query('SELECT * FROM TESTLIB.V_RENDIMIENTO_CHOFERES WHERE EMP_ID = ? ORDER BY TASA_EXITO DESC', [req.empId]);
    await conn.close();
    res.json({ success: true, data: result });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// ========================================
// MÓDULO: VEHÍCULOS
// ========================================
app.get('/api/vehiculos', async (req, res) => {
  try {
    const conn = await ibmi.getConnection(CONFIG.db);
    const result = await conn.query('SELECT * FROM TESTLIB.VEHICULOS WHERE EMP_ID = ? ORDER BY VEH_UNIDAD', [req.empId]);
    await conn.close();
    res.json({ success: true, data: result });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

app.get('/api/vehiculos/flota', async (req, res) => {
  try {
    const conn = await ibmi.getConnection(CONFIG.db);
    const result = await conn.query('SELECT * FROM TESTLIB.V_ESTADO_FLOTA WHERE EMP_ID = ?', [req.empId]);
    await conn.close();
    res.json({ success: true, data: result });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// ========================================
// MÓDULO: RUTAS
// ========================================
app.get('/api/rutas', async (req, res) => {
  try {
    const conn = await ibmi.getConnection(CONFIG.db);
    const result = await conn.query('SELECT * FROM TESTLIB.V_COSTOS_RUTA WHERE EMP_ID = ? ORDER BY RUT_FECHA DESC', [req.empId]);
    await conn.close();
    res.json({ success: true, data: result });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// ========================================
// MÓDULO: ENTREGAS
// ========================================
app.get('/api/entregas', async (req, res) => {
  try {
    const conn = await ibmi.getConnection(CONFIG.db);
    const result = await conn.query('SELECT * FROM TESTLIB.ENTREGAS WHERE EMP_ID = ? ORDER BY ENT_FECHA_LLEGADA DESC FETCH FIRST 50 ROWS ONLY', [req.empId]);
    await conn.close();
    res.json({ success: true, data: result });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

app.get('/api/entregas/chofer/:choId', async (req, res) => {
  try {
    const conn = await ibmi.getConnection(CONFIG.db);
    const result = await conn.query(
      `SELECT E.*, P.PED_NUMERO, P.PED_CLIENTE_NOMBRE, P.PED_DESTINO_DIR 
       FROM TESTLIB.ENTREGAS E 
       JOIN TESTLIB.PEDIDOS P ON E.PED_ID = P.PED_ID 
       WHERE E.CHO_ID = ? AND E.EMP_ID = ? 
       ORDER BY E.ENT_FECHA_LLEGADA DESC`, [req.params.choId, req.empId]);
    await conn.close();
    res.json({ success: true, data: result });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// ========================================
// MÓDULO: CLIENTES
// ========================================
app.get('/api/clientes', async (req, res) => {
  try {
    const conn = await ibmi.getConnection(CONFIG.db);
    const result = await conn.query('SELECT * FROM TESTLIB.CLIENTES_LM WHERE EMP_ID = ? ORDER BY CLI_RAZON_SOCIAL', [req.empId]);
    await conn.close();
    res.json({ success: true, data: result });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

app.get('/api/clientes/top', async (req, res) => {
  try {
    const conn = await ibmi.getConnection(CONFIG.db);
    const result = await conn.query('SELECT * FROM TESTLIB.V_TOP_CLIENTES WHERE EMP_ID = ? ORDER BY TOTAL_GASTADO DESC FETCH FIRST 10 ROWS ONLY', [req.empId]);
    await conn.close();
    res.json({ success: true, data: result });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// ========================================
// MÓDULO: KPIs
// ========================================
app.get('/api/kpis', async (req, res) => {
  try {
    const conn = await ibmi.getConnection(CONFIG.db);
    const result = await conn.query('SELECT * FROM TESTLIB.V_KPI_CONSOLIDADO WHERE EMP_ID = ?', [req.empId]);
    await conn.close();
    res.json({ success: true, data: result[0] || {} });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

app.get('/api/kpis/diario', async (req, res) => {
  try {
    const conn = await ibmi.getConnection(CONFIG.db);
    const result = await conn.query(
      'SELECT * FROM TESTLIB.KPI_DIARIO WHERE EMP_ID = ? ORDER BY KPI_FECHA DESC FETCH FIRST 30 ROWS ONLY', [req.empId]);
    await conn.close();
    res.json({ success: true, data: result });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// ========================================
// MÓDULO: INCIDENCIAS
// ========================================
app.get('/api/incidencias', async (req, res) => {
  try {
    const conn = await ibmi.getConnection(CONFIG.db);
    const result = await conn.query('SELECT * FROM TESTLIB.INCIDENCIAS WHERE EMP_ID = ? ORDER BY INC_FECHA DESC', [req.empId]);
    await conn.close();
    res.json({ success: true, data: result });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

app.get('/api/incidencias/resumen', async (req, res) => {
  try {
    const conn = await ibmi.getConnection(CONFIG.db);
    const result = await conn.query('SELECT * FROM TESTLIB.V_INCIDENCIAS_RESUMEN WHERE EMP_ID = ?', [req.empId]);
    await conn.close();
    res.json({ success: true, data: result });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// ========================================
// MÓDULO: TRACKING GPS
// ========================================
app.get('/api/tracking/:choId', async (req, res) => {
  try {
    const conn = await ibmi.getConnection(CONFIG.db);
    const result = await conn.query(
      'SELECT * FROM TESTLIB.TRACKING WHERE CHO_ID = ? AND EMP_ID = ? ORDER BY TRK_FECHA DESC FETCH FIRST 10 ROWS ONLY',
      [req.params.choId, req.empId]);
    await conn.close();
    res.json({ success: true, data: result });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

app.post('/api/tracking', async (req, res) => {
  try {
    const conn = await ibmi.getConnection(CONFIG.db);
    const t = req.body;
    await conn.query(
      `INSERT INTO TESTLIB.TRACKING (EMP_ID, CHO_ID, VEH_ID, TRK_LATITUD, TRK_LONGITUD, TRK_VELOCIDAD, TRK_RUMBO, TRK_BATERIA)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?)`,
      [req.empId, t.choId, t.vehId, t.latitud, t.longitud, t.velocidad || 0, t.rumbo || 0, t.bateria || 100]);
    await conn.close();
    res.json({ success: true });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// ========================================
// MÓDULO: ZONAS
// ========================================
app.get('/api/zonas', async (req, res) => {
  try {
    const conn = await ibmi.getConnection(CONFIG.db);
    const result = await conn.query('SELECT * FROM TESTLIB.ZONAS WHERE EMP_ID = ? ORDER BY ZON_NOMBRE', [req.empId]);
    await conn.close();
    res.json({ success: true, data: result });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// ========================================
// MÓDULO: TARIFAS
// ========================================
app.get('/api/tarifas', async (req, res) => {
  try {
    const conn = await ibmi.getConnection(CONFIG.db);
    const result = await conn.query('SELECT * FROM TESTLIB.TARIFAS_LM WHERE EMP_ID = ? ORDER BY TAR_NOMBRE', [req.empId]);
    await conn.close();
    res.json({ success: true, data: result });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// ========================================
// MÓDULO: NOTIFICACIONES
// ========================================
app.get('/api/notificaciones', async (req, res) => {
  try {
    const conn = await ibmi.getConnection(CONFIG.db);
    const result = await conn.query('SELECT * FROM TESTLIB.NOTIFICACIONES WHERE EMP_ID = ? ORDER BY NOT_FECHA_ENVIO DESC FETCH FIRST 50 ROWS ONLY', [req.empId]);
    await conn.close();
    res.json({ success: true, data: result });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// ========================================
// MÓDULO: AUDITORÍA
// ========================================
app.get('/api/audit', async (req, res) => {
  try {
    const conn = await ibmi.getConnection(CONFIG.db);
    const result = await conn.query('SELECT * FROM TESTLIB.AUDIT_LOG WHERE EMP_ID = ? ORDER BY AUD_FECHA DESC FETCH FIRST 100 ROWS ONLY', [req.empId]);
    await conn.close();
    res.json({ success: true, data: result });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// ========================================
// MÓDULO: EDGAR DATA (Mantenimiento)
// ========================================
app.get('/api/mantenimiento/unidades', async (req, res) => {
  try {
    const conn = await ibmi.getConnection(CONFIG.db);
    const result = await conn.query('SELECT * FROM TESTLIB.UNIDADESTA ORDER BY RVNEUN');
    await conn.close();
    res.json({ success: true, data: result });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

app.get('/api/mantenimiento/ots', async (req, res) => {
  try {
    const conn = await ibmi.getConnection(CONFIG.db);
    const result = await conn.query('SELECT * FROM TESTLIB.OTSXMARCA2 ORDER BY CCTOTA01 DESC FETCH FIRST 50 ROWS ONLY');
    await conn.close();
    res.json({ success: true, data: result });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// ========================================
// INICIAR SERVIDOR
// ========================================
app.listen(CONFIG.port, () => {
  console.log(`\n  ========================================`);
  console.log(`  LAST MILE API - v1.0.0`);
  console.log(`  Puerto: ${CONFIG.port}`);
  console.log(`  Base de datos: AS/400 (TESTLIB)`);
  console.log(`  Multi-tenant: SÍ`);
  console.log(`  ========================================\n`);
  console.log(`  Endpoints disponibles:`);
  console.log(`    GET  /api/health`);
  console.log(`    GET  /api/empresas`);
  console.log(`    GET  /api/dashboard/:empId`);
  console.log(`    GET  /api/pedidos`);
  console.log(`    GET  /api/pedidos/:id`);
  console.log(`    POST /api/pedidos`);
  console.log(`    PUT  /api/pedidos/:id/estado`);
  console.log(`    GET  /api/choferes`);
  console.log(`    GET  /api/choferes/rendimiento`);
  console.log(`    GET  /api/vehiculos`);
  console.log(`    GET  /api/vehiculos/flota`);
  console.log(`    GET  /api/rutas`);
  console.log(`    GET  /api/entregas`);
  console.log(`    GET  /api/clientes`);
  console.log(`    GET  /api/clientes/top`);
  console.log(`    GET  /api/kpis`);
  console.log(`    GET  /api/kpis/diario`);
  console.log(`    GET  /api/incidencias`);
  console.log(`    GET  /api/tracking/:choId`);
  console.log(`    POST /api/tracking`);
  console.log(`    GET  /api/zonas`);
  console.log(`    GET  /api/tarifas`);
  console.log(`    GET  /api/notificaciones`);
  console.log(`    GET  /api/audit`);
  console.log(`    GET  /api/mantenimiento/unidades`);
  console.log(`    GET  /api/mantenimiento/ots`);
  console.log(`\n  Header requerido: X-Emp-Id: 1|2|3\n`);
});
