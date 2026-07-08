/**
 * LAST MILE DELIVERY SYSTEM - JavaScript Principal
 * Maneja API, autenticación, y renderizado
 */

const API_BASE = 'http://localhost:5000';
let currentEmpId = 1;
let currentUser = null;

// ========================================
// API Helper
// ========================================
async function api(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`;
  const headers = {
    'Content-Type': 'application/json',
    'X-Emp-Id': currentEmpId,
    ...options.headers
  };
  
  try {
    const response = await fetch(url, { ...options, headers });
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('API Error:', error);
    return { success: false, error: error.message };
  }
}

// ========================================
// AUTH
// ========================================
function login(empId, user, pass) {
  currentEmpId = empId;
  currentUser = user;
  localStorage.setItem('empId', empId);
  localStorage.setItem('user', user);
  window.location.href = '/panel-operacion.html';
}

function logout() {
  localStorage.removeItem('empId');
  localStorage.removeItem('user');
  window.location.href = '/index.html';
}

function checkAuth() {
  const empId = localStorage.getItem('empId');
  if (!empId && !window.location.href.includes('index.html')) {
    window.location.href = '/index.html';
  }
  currentEmpId = parseInt(empId || '1');
}

// ========================================
// RENDERIZADO
// ========================================
function formatCurrency(amount) {
  return '$' + parseFloat(amount || 0).toLocaleString('es-MX', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function formatDate(dateStr) {
  if (!dateStr) return '-';
  const d = new Date(dateStr);
  return d.toLocaleDateString('es-MX');
}

function formatDateTime(dateStr) {
  if (!dateStr) return '-';
  const d = new Date(dateStr);
  return d.toLocaleDateString('es-MX') + ' ' + d.toLocaleTimeString('es-MX', { hour: '2-digit', minute: '2-digit' });
}

function getBadgeEstado(estado) {
  const classes = {
    'PENDIENTE': 'badge-pendiente',
    'ASIGNADO': 'badge-asignado',
    'EN_RUTA': 'badge-ruta',
    'ENTREGADO': 'badge-entregado',
    'FALLIDO': 'badge-fallido',
    'CANCELADO': 'badge-cancelado',
    'NO_ENTREGADO': 'badge-fallido'
  };
  return `<span class="badge ${classes[estado] || ''}">${estado}</span>`;
}

function getBadgePrioridad(prioridad) {
  const classes = {
    'URGENTE': 'badge-urgente',
    'ALTA': 'badge-alta',
    'NORMAL': 'badge-normal',
    'BAJA': 'badge-baja'
  };
  return `<span class="badge ${classes[prioridad] || ''}">${prioridad}</span>`;
}

// ========================================
// DASHBOARD
// ========================================
async function loadDashboard() {
  const result = await api(`/api/dashboard/${currentEmpId}`);
  if (result.success && result.data) {
    const d = result.data;
    document.getElementById('kpi-pedidos').textContent = d.TOTAL_PEDIDOS || 0;
    document.getElementById('kpi-pendientes').textContent = d.PENDIENTES || 0;
    document.getElementById('kpi-ruta').textContent = d.EN_RUTA || 0;
    document.getElementById('kpi-entregados').textContent = d.ENTREGADOS || 0;
    document.getElementById('kpi-fallidos').textContent = d.FALLIDOS || 0;
    document.getElementById('kpi-choferes').textContent = d.CHOFERES_ACTIVOS || 0;
    document.getElementById('kpi-vehiculos').textContent = d.VEHICULOS_ACTIVOS || 0;
    document.getElementById('kpi-ingresos').textContent = formatCurrency(d.INGRESO_TOTAL);
  }
}

// ========================================
// PEDIDOS
// ========================================
async function loadPedidos(estado = '') {
  const endpoint = estado ? `/api/pedidos?estado=${estado}&limite=50` : '/api/pedidos?limite=50';
  const result = await api(endpoint);
  
  if (result.success) {
    const tbody = document.getElementById('pedidos-tbody');
    if (!tbody) return;
    tbody.innerHTML = '';
    
    result.data.forEach(p => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td><strong>${p.PED_NUMERO || ''}</strong></td>
        <td>${p.PED_CLIENTE_NOMBRE || ''}</td>
        <td>${(p.PED_DESTINO_DIR || '').substring(0, 30)}...</td>
        <td>${p.PED_DESTINO_COL || ''}</td>
        <td>${p.PED_BULTOS || 0}</td>
        <td>${formatCurrency(p.PED_COSTO_TOTAL)}</td>
        <td>${getBadgePrioridad(p.PED_PRIORIDAD)}</td>
        <td>${getBadgeEstado(p.PED_ESTADO)}</td>
        <td>${p.CHOFER_ASIGNADO || '-'}</td>
        <td>${formatDateTime(p.PED_FECHA_PEDIDO)}</td>
        <td>
          <button class="btn btn-sm btn-primary" onclick="verPedido(${p.PED_ID})">Ver</button>
        </td>
      `;
      tbody.appendChild(tr);
    });
    
    document.getElementById('pedidos-count').textContent = `${result.data.length} pedidos`;
  }
}

async function verPedido(pedId) {
  const result = await api(`/api/pedidos/${pedId}`);
  if (result.success && result.data) {
    const p = result.data;
    let html = `
      <p><strong>Número:</strong> ${p.PED_NUMERO}</p>
      <p><strong>Cliente:</strong> ${p.PED_CLIENTE_NOMBRE}</p>
      <p><strong>Teléfono:</strong> ${p.PED_CLIENTE_TELEFONO}</p>
      <p><strong>Destino:</strong> ${p.PED_DESTINO_DIR}, ${p.PED_DESTINO_COL}</p>
      <p><strong>Peso:</strong> ${p.PED_PESO_KG} kg | Bultos: ${p.PED_BULTOS}</p>
      <p><strong>Costo:</strong> ${formatCurrency(p.PED_COSTO_TOTAL)}</p>
      <p><strong>Estado:</strong> ${getBadgeEstado(p.PED_ESTADO)}</p>
      <p><strong>Chofer:</strong> ${p.CHOFER_ASIGNADO || 'Sin asignar'}</p>
      <p><strong>Fecha:</strong> ${formatDateTime(p.PED_FECHA_PEDIDO)}</p>
    `;
    document.getElementById('pedido-detail').innerHTML = html;
    document.getElementById('modal-pedido').classList.add('active');
  }
}

function closeModal(id) {
  document.getElementById(id).classList.remove('active');
}

// ========================================
// CHOFERES
// ========================================
async function loadChoferes() {
  const result = await api('/api/choferes/rendimiento');
  
  if (result.success) {
    const tbody = document.getElementById('choferes-tbody');
    if (!tbody) return;
    tbody.innerHTML = '';
    
    result.data.forEach(ch => {
      const tr = document.createElement('tr');
      const tasaClass = ch.TASA_EXITO >= 85 ? 'text-success' : ch.TASA_EXITO >= 70 ? 'text-warning' : 'text-danger';
      tr.innerHTML = `
        <td><strong>${ch.CHO_NOMBRE || ''} ${ch.CHO_APELLIDO || ''}</strong></td>
        <td>${ch.TOTAL_ENTREGAS || 0}</td>
        <td>${ch.ENTREGAS_EXITOSAS || 0}</td>
        <td>${ch.ENTREGAS_FALLIDAS || 0}</td>
        <td class="${tasaClass}"><strong>${ch.TASA_EXITO || 0}%</strong></td>
        <td>${ch.TIEMPO_PROM_ESPERA || 0} min</td>
      `;
      tbody.appendChild(tr);
    });
  }
}

// ========================================
// VEHÍCULOS
// ========================================
async function loadVehiculos() {
  const result = await api('/api/vehiculos');
  
  if (result.success) {
    const tbody = document.getElementById('vehiculos-tbody');
    if (!tbody) return;
    tbody.innerHTML = '';
    
    result.data.forEach(v => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td><strong>${v.VEH_UNIDAD || ''}</strong></td>
        <td>${v.VEH_MARCA || ''}</td>
        <td>${v.VEH_MODELO || ''}</td>
        <td>${v.VEH_AÑO || ''}</td>
        <td>${v.VEH_TIPO || ''}</td>
        <td>${v.VEH_CAPACIDAD_KG || 0} kg</td>
        <td>${getBadgeEstado(v.VEH_ESTATUS)}</td>
      `;
      tbody.appendChild(tr);
    });
  }
}

// ========================================
// CLIENTES
// ========================================
async function loadClientes() {
  const result = await api('/api/clientes');
  
  if (result.success) {
    const tbody = document.getElementById('clientes-tbody');
    if (!tbody) return;
    tbody.innerHTML = '';
    
    result.data.forEach(c => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td><strong>${c.CLI_RAZON_SOCIAL || ''}</strong></td>
        <td>${c.CLI_COLONIA || ''}</td>
        <td>${c.CLI_TELEFONO || ''}</td>
        <td>${c.CLI_TIPO_CLIENTE || ''}</td>
        <td>${getBadgeEstado(c.CLI_ESTATUS)}</td>
      `;
      tbody.appendChild(tr);
    });
  }
}

// ========================================
// KPIs
// ========================================
async function loadKPIs() {
  const result = await api('/api/kpis');
  
  if (result.success && result.data) {
    const d = result.data;
    const kpiTotal = document.getElementById('kpi-total-envios');
    const kpiEntregados = document.getElementById('kpi-entregados-total');
    const kpiFallidos = document.getElementById('kpi-fallidos-total');
    const kpiUtilidad = document.getElementById('kpi-utilidad');
    const kpiKm = document.getElementById('kpi-km-total');
    const kpiTiempo = document.getElementById('kpi-tiempo-prom');
    
    if (kpiTotal) kpiTotal.textContent = d.TOTAL_NUEVOS || 0;
    if (kpiEntregados) kpiEntregados.textContent = d.TOTAL_ENTREGADOS || 0;
    if (kpiFallidos) kpiFallidos.textContent = d.TOTAL_FALLIDOS || 0;
    if (kpiUtilidad) kpiUtilidad.textContent = formatCurrency(d.UTILIDAD_TOTAL);
    if (kpiKm) kpiKm.textContent = parseFloat(d.KM_TOTAL || 0).toFixed(1) + ' km';
    if (kpiTiempo) kpiTiempo.textContent = d.TIEMPO_PROM_GENERAL || 0 + ' min';
  }
}

// ========================================
// INCIDENCIAS
// ========================================
async function loadIncidencias() {
  const result = await api('/api/incidencias/resumen');
  
  if (result.success) {
    const tbody = document.getElementById('incidencias-tbody');
    if (!tbody) return;
    tbody.innerHTML = '';
    
    result.data.forEach(i => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td><strong>${i.INC_TIPO || ''}</strong></td>
        <td>${i.CANTIDAD || 0}</td>
        <td>${i.ABIERTAS || 0}</td>
        <td>${i.RESUELTAS || 0}</td>
      `;
      tbody.appendChild(tr);
    });
  }
}

// ========================================
// RUTAS
// ========================================
async function loadRutas() {
  const result = await api('/api/rutas');
  
  if (result.success) {
    const tbody = document.getElementById('rutas-tbody');
    if (!tbody) return;
    tbody.innerHTML = '';
    
    result.data.forEach(r => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td><strong>${r.RUT_NOMBRE || ''}</strong></td>
        <td>${formatDate(r.RUT_FECHA)}</td>
        <td>${r.CHOFER || ''}</td>
        <td>${r.VEH_UNIDAD || ''}</td>
        <td>${r.RUT_TOTAL_PEDIDOS || 0}</td>
        <td>${r.RUT_TOTAL_ENTREGAS || 0}</td>
        <td>${parseFloat(r.RUT_TOTAL_KM || 0).toFixed(1)} km</td>
        <td>${formatCurrency(r.RUT_COSTO_TOTAL)}</td>
        <td>${formatCurrency(r.COSTO_PROM_ENTREGA)}</td>
      `;
      tbody.appendChild(tr);
    });
  }
}

// ========================================
// TRACKING
// ========================================
async function loadTracking(choId) {
  const result = await api(`/api/tracking/${choId}`);
  
  if (result.success) {
    const tbody = document.getElementById('tracking-tbody');
    if (!tbody) return;
    tbody.innerHTML = '';
    
    result.data.forEach(t => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td>${formatDateTime(t.TRK_FECHA)}</td>
        <td>${t.TRK_LATITUD}</td>
        <td>${t.TRK_LONGITUD}</td>
        <td>${t.TRK_VELOCIDAD} km/h</td>
        <td>${t.TRK_BATERIA}%</td>
      `;
      tbody.appendChild(tr);
    });
  }
}

// ========================================
// INICIALIZACIÓN
// ========================================
document.addEventListener('DOMContentLoaded', () => {
  checkAuth();
  
  // Detectar panel y cargar datos
  const page = window.location.pathname.split('/').pop();
  
  if (page === 'panel-operacion.html') {
    loadDashboard();
    loadPedidos();
  } else if (page === 'panel-admin.html') {
    loadKPIs();
    loadClientes();
    loadIncidencias();
  } else if (page === 'panel-chofer.html') {
    loadPedidos('EN_RUTA');
  } else if (page === 'panel-cliente.html') {
    loadPedidos();
  }
});
