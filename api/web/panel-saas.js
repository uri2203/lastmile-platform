const API_BASE=window.location.origin;
const HEADERS={'X-Emp-Id': localStorage.getItem('lm-emp-id') || localStorage.getItem('empId') || '1','Content-Type':'application/json'};

let DB_TENANTS=[],DB_USUARIOS=[],DB_PEDIDOS=[],DB_SUSCRIPCIONES=[],DB_COBROS=[];
let chartRevenue=null,chartPlanes=null;

/* ==========================================
   NAVIGATION
   ========================================== */
document.querySelectorAll('.nav-item[data-section]').forEach(item=>{
  item.addEventListener('click',function(){
    const sec=this.getAttribute('data-section');
    document.querySelectorAll('.section').forEach(s=>s.classList.remove('active'));
    document.querySelectorAll('.nav-item').forEach(n=>n.classList.remove('active'));
    document.getElementById('section-'+sec).classList.add('active');
    this.classList.add('active');
    loadSection(sec);
  });
});

function toggleSidebar(){
  const sb=document.getElementById('sidebar');
  const mc=document.getElementById('mainContent');
  if(sb)sb.classList.toggle('collapsed');
  if(mc)mc.classList.toggle('expanded');
}

function getTheme(){try{return typeof ThemeManager!=='undefined'?ThemeManager.get():'dark';}catch(e){return 'dark';}}

/* ==========================================
   HELPERS
   ========================================== */
function statusBadge(s){
  const c={ACTIVA:'badge-success',PENDIENTE:'badge-warning',COMPLETADO:'badge-success',PAGADO:'badge-success',TRIAL:'badge-info',SUSPENDIDA:'badge-danger',CANCELADA:'badge-danger',EN_RUTA:'badge-info',ENTREGADO:'badge-success',CANCELADO:'badge-danger',admin:'badge-warning',operacion:'badge-info',chofer:'badge-success',cliente:'badge-gray',activo:'badge-success',inactivo:'badge-gray'};
  const labels={ACTIVA:'saas.estado_activo',PENDIENTE:'saas.filtro_pendiente',COMPLETADO:'saas.filtro_entregado',PAGADO:'saas.kpi_cobrado',TRIAL:'saas.kpi_trial',SUSPENDIDA:'saas.estado_suspendida',CANCELADA:'saas.kpi_canceladas',EN_RUTA:'saas.filtro_en_ruta',ENTREGADO:'saas.filtro_entregado',CANCELADO:'saas.filtro_cancelado',admin:'col_rol',operacion:'col_rol',chofer:'col_rol',cliente:'col_rol',activo:'saas.kpi_activos',inactivo:'saas.kpi_suspendidos'};
  const lbl=window.i18n&&window.i18n.t?window.i18n.t(labels[s]||''):s;
  return '<span class="badge '+(c[s]||'badge-gray')+'">'+lbl+'</span>';
}
function planBadge(p){
  const c={STARTER:'badge-gray',PRO:'badge-info',ENTERPRISE:'badge-warning',Starter:'badge-gray',Pro:'badge-info',Enterprise:'badge-warning'};
  return '<span class="badge '+(c[p]||'badge-gray')+'">'+p+'</span>';
}
function formatCurrency(v){return '$'+(parseFloat(v)||0).toLocaleString('es-MX',{minimumFractionDigits:0,maximumFractionDigits:0})}
function openModal(id){const m=document.getElementById(id);if(m)m.classList.add('show')}
function closeModal(id){const m=document.getElementById(id);if(m)m.classList.remove('show')}
function showToast(msg,type){
  const c=document.querySelector('.toast-container');if(!c)return;
  const t=document.createElement('div');t.className='toast toast-'+(type||'info');t.innerHTML='<i class="fas fa-'+(type==='success'?'check-circle':type==='error'?'exclamation-circle':'info-circle')+'"></i> '+msg;
  c.appendChild(t);setTimeout(()=>t.remove(),3000);
}
function apiGet(path){return fetch(API_BASE+path,{headers:HEADERS}).then(r=>r.json()).catch(e=>({success:false,data:[],error:e.message}))}
function apiPost(path,data){return fetch(API_BASE+path,{method:'POST',headers:HEADERS,body:JSON.stringify(data)}).then(r=>r.json()).catch(e=>({success:false,error:e.message}))}
function apiPut(path,data){return fetch(API_BASE+path,{method:'PUT',headers:HEADERS,body:JSON.stringify(data)}).then(r=>r.json()).catch(e=>({success:false,error:e.message}))}

function loadSection(sec){
  switch(sec){
    case 'dashboard': loadDashboard(); break;
    case 'tenants': loadTenants(); break;
    case 'usuarios': loadUsuarios(); break;
    case 'pedidos': loadPedidosGlobal(); break;
    case 'suscripciones': loadSuscripciones(); break;
    case 'cobros': loadCobros(); break;
    case 'planes': loadPlanes(); break;
    case 'auditoria': loadAuditoria(); break;
  }
}

/* ==========================================
   DASHBOARD
   ========================================== */
function loadDashboard(){
  apiGet('/api/saas/global-stats').then(res=>{
    if(!res.success||!res.data)return;
    const d=res.data;
    const el=id=>document.getElementById(id);
    if(el('kpi-mrr'))el('kpi-mrr').textContent=formatCurrency(d.mrr);
    if(el('kpi-tenants'))el('kpi-tenants').textContent=d.empresas_activas+'/'+d.empresas_total;
    if(el('kpi-pedidos-mes'))el('kpi-pedidos-mes').textContent=d.pedidos_mes;
    if(el('kpi-sus'))el('kpi-sus').textContent=d.sus_activas;
    if(el('kpi-pagos-pend'))el('kpi-pagos-pend').textContent=formatCurrency(d.pagos_pend_monto);
  });

  apiGet('/api/saas/revenue-chart').then(res=>{
    if(!res.success||!res.data)return;
    initRevenueChart(res.data);
  });

  apiGet('/api/saas/tenants-chart').then(res=>{
    if(!res.success||!res.data)return;
    initPlanesChart(res.data);
  });

  apiGet('/api/saas/tenants').then(res=>{
    if(!res.data)return;
    const sorted=[...res.data].sort((a,b)=>(b.TOTAL_PEDIDOS||0)-(a.TOTAL_PEDIDOS||0)).slice(0,5);
    const el=document.getElementById('topTenants');
    if(!el)return;
    el.innerHTML=sorted.map(t=>{
      const color=['var(--accent)','var(--success)','var(--warning)','var(--danger)','#8b5cf6'][Math.floor(Math.random()*5)];
      return '<div style="display:flex;align-items:center;gap:12px;padding:10px 0;border-bottom:1px solid var(--border-primary);">'+
        '<div class="avatar" style="background:'+color+'20;color:'+color+';">'+(t.EMP_NOMBRE||'?').substring(0,2).toUpperCase()+'</div>'+
        '<div style="flex:1;"><div style="font-size:12px;font-weight:500;">'+(t.EMP_NOMBRE||'-')+'</div><div style="font-size:10px;color:var(--text-muted);">'+(t.EMP_PLAN||'STARTER')+'</div></div>'+
        '<div style="text-align:right;"><div style="font-size:12px;font-weight:600;">'+(t.TOTAL_PEDIDOS||0)+'</div><div style="font-size:10px;color:var(--text-muted);">'+window.i18n.t('saas.col_pedidos')+'</div></div></div>';
    }).join('');
  });

  apiGet('/api/saas/audit').then(res=>{
    if(!res.data)return;
    const el=document.getElementById('recentActivity');
    if(!el)return;
    const items=res.data.slice(0,8);
    el.innerHTML=items.length?items.map(a=>{
      const color=a.AUD_ACCION==='LOGIN'?'var(--success)':a.AUD_ACCION==='DELETE'?'var(--danger)':'var(--accent)';
      return '<div style="display:flex;align-items:flex-start;gap:10px;padding:8px 0;border-bottom:1px solid var(--border-primary);">'+
        '<div style="width:6px;height:6px;border-radius:50%;background:'+color+';margin-top:5px;flex-shrink:0;"></div>'+
        '<div><div style="font-size:12px;">'+(a.AUD_ACCION||'')+'</div><div style="font-size:10px;color:var(--text-muted);">'+(a.AUD_FECHA||'')+'</div></div></div>';
    }).join(''):'<div style="text-align:center;padding:20px;color:var(--text-muted);font-size:12px;">'+window.i18n.t('saas.actividad_reciente')+'</div>';
  });
}

function initRevenueChart(data){
  const ctx=document.getElementById('chartRevenue');
  if(!ctx||typeof Chart==='undefined')return;
  if(chartRevenue)chartRevenue.destroy();
  const isDark=getTheme()==='dark';
  const labels=data.map(d=>d.mes||'');
  const totals=data.map(d=>parseFloat(d.total||0));
  const cobrados=data.map(d=>parseFloat(d.cobrado||0));
  chartRevenue=new Chart(ctx,{type:'bar',data:{labels,datasets:[{label:window.i18n.t('saas.col_total'),data:totals,backgroundColor:'rgba(99,102,241,0.5)',borderRadius:4},{label:window.i18n.t('saas.kpi_cobrado'),data:cobrados,backgroundColor:'rgba(16,185,129,0.5)',borderRadius:4}]},options:{responsive:true,scales:{y:{beginAtZero:true,ticks:{color:isDark?'#9ca3af':'#6b7280',font:{size:10}},grid:{color:isDark?'rgba(75,85,99,0.3)':'rgba(209,213,219,0.5)'}},x:{ticks:{color:isDark?'#9ca3af':'#6b7280',font:{size:10}},grid:{display:false}}},plugins:{legend:{labels:{color:isDark?'#9ca3af':'#6b7280',font:{size:11}}}}}});
}

function initPlanesChart(data){
  const ctx=document.getElementById('chartPlanes');
  if(!ctx||typeof Chart==='undefined')return;
  if(chartPlanes)chartPlanes.destroy();
  const isDark=getTheme()==='dark';
  chartPlanes=new Chart(ctx,{type:'doughnut',data:{labels:data.map(d=>d.PLAN_ID||''),datasets:[{data:data.map(d=>parseInt(d.total||0)),backgroundColor:['var(--accent)','var(--success)','var(--warning)','#8b5cf6'],borderWidth:0}]},options:{responsive:true,plugins:{legend:{position:'bottom',labels:{color:isDark?'#9ca3af':'#6b7280',font:{size:11}}}}}});
}

/* ==========================================
   TENANTS
   ========================================== */
function loadTenants(){
  apiGet('/api/saas/tenants').then(res=>{
    if(!res.data)return;
    DB_TENANTS=res.data;
    const activos=DB_TENANTS.filter(t=>t.EMP_ESTATUS==='ACTIVA').length;
    const susp=DB_TENANTS.filter(t=>t.EMP_ESTATUS==='SUSPENDIDA').length;
    document.getElementById('t-activos').textContent=activos;
    document.getElementById('t-suspendidos').textContent=susp;
    document.getElementById('t-total').textContent=DB_TENANTS.length;
    renderTenants();
  });

  apiGet('/api/saas/suscripciones').then(res=>{
    if(!res.data)return;
    const trial=res.data.filter(s=>s.SUS_ESTADO==='TRIAL').length;
    document.getElementById('t-trial').textContent=trial;
  });
}

function renderTenants(){
  const search=(document.getElementById('tenantSearch').value||'').toLowerCase();
  const statusFilter=document.getElementById('tenantStatusFilter').value;
  let filtered=DB_TENANTS.filter(t=>{
    const nombre=(t.EMP_NOMBRE||'').toLowerCase();
    const matchSearch=!search||nombre.includes(search);
    const matchStatus=!statusFilter||t.EMP_ESTATUS===statusFilter;
    return matchSearch&&matchStatus;
  });
  const tbody=document.getElementById('tenantsTableBody');
  if(!tbody)return;
  tbody.innerHTML=filtered.map(t=>{
    const id=t.EMP_ID;
    const estatus=t.EMP_ESTATUS||'ACTIVA';
    return '<tr class="tenant-row" onclick="viewTenant('+id+')">'+
      '<td>#'+id+'</td>'+
      '<td><div style="display:flex;align-items:center;gap:8px;"><div class="avatar" style="background:var(--accent-bg);color:var(--accent);">'+(t.EMP_NOMBRE||'?').substring(0,2).toUpperCase()+'</div><div><div style="font-weight:500;">'+(t.EMP_NOMBRE||'-')+'</div><div style="font-size:10px;color:var(--text-muted);">'+(t.EMP_EMAIL||'')+'</div></div></div></td>'+
      '<td>'+planBadge(t.EMP_PLAN||'STARTER')+'</td>'+
      '<td style="font-weight:500;">'+(t.TOTAL_PEDIDOS||0)+'</td>'+
      '<td>'+(t.TOTAL_CHOFERES||0)+'</td>'+
      '<td>'+(t.TOTAL_CLIENTES||0)+'</td>'+
      '<td>'+statusBadge(estatus)+'</td>'+
      '<td><div style="display:flex;gap:4px;" onclick="event.stopPropagation()">'+
        '<button class="btn btn-ghost btn-sm" onclick="editTenant('+id+')" title="Editar"><i class="fas fa-pen" style="font-size:10px;"></i></button>'+
        (estatus==='ACTIVA'?'<button class="btn btn-ghost btn-sm" onclick="suspendTenant('+id+')" title="Suspender" style="color:var(--warning);"><i class="fas fa-pause" style="font-size:10px;"></i></button>':
        '<button class="btn btn-ghost btn-sm" onclick="activateTenant('+id+')" title="Activar" style="color:var(--success);"><i class="fas fa-play" style="font-size:10px;"></i></button>')+
      '</div></td></tr>';
  }).join('');
}

function createTenant(){
  const data={
    nombre:document.getElementById('nt-nombre').value.trim(),
    rfc:document.getElementById('nt-rfc').value.trim(),
    email:document.getElementById('nt-email').value.trim(),
    telefono:document.getElementById('nt-telefono').value.trim(),
    plan:document.getElementById('nt-plan').value,
    admin_user:document.getElementById('nt-user').value.trim()||'admin',
    admin_pass:document.getElementById('nt-pass').value||'admin123'
  };
  if(!data.nombre){showToast(window.i18n.t('saas.modal_empresa_nombre'),'error');return;}
  apiPost('/api/saas/tenants',data).then(res=>{
    if(res.success){
      showToast('Tenant "'+data.nombre+'" '+window.i18n.t('saas.btn_crear_tenant'),'success');
      closeModal('modalNuevoTenant');
      loadTenants();
      document.getElementById('nt-nombre').value='';
      document.getElementById('nt-rfc').value='';
      document.getElementById('nt-email').value='';
      document.getElementById('nt-telefono').value='';
    }else{
      showToast(res.error||window.i18n.t('common.error'),'error');
    }
  });
}

function editTenant(id){
  const t=DB_TENANTS.find(x=>x.EMP_ID===id);
  if(!t)return;
  document.getElementById('et-id').value=id;
  document.getElementById('et-nombre').value=t.EMP_NOMBRE||'';
  document.getElementById('et-rfc').value=t.EMP_RFC||'';
  document.getElementById('et-email').value=t.EMP_EMAIL||'';
  document.getElementById('et-telefono').value=t.EMP_TELEFONO||'';
  document.getElementById('et-plan').value=t.EMP_PLAN||'STARTER';
  document.getElementById('et-estatus').value=t.EMP_ESTATUS||'ACTIVA';
  openModal('modalEditarTenant');
}

function updateTenant(){
  const id=document.getElementById('et-id').value;
  apiPut('/api/saas/tenants/'+id,{
    nombre:document.getElementById('et-nombre').value.trim(),
    rfc:document.getElementById('et-rfc').value.trim(),
    email:document.getElementById('et-email').value.trim(),
    telefono:document.getElementById('et-telefono').value.trim(),
    plan:document.getElementById('et-plan').value,
    estatus:document.getElementById('et-estatus').value
  }).then(res=>{
    if(res.success){
      showToast(window.i18n.t('saas.btn_guardar')+' '+window.i18n.t('saas.modal_editar_tenant'),'success');
      closeModal('modalEditarTenant');
      loadTenants();
    }else{
      showToast(res.error||window.i18n.t('common.error'),'error');
    }
  });
}

function suspendTenant(id){
  if(!confirm(window.i18n.t('saas.kpi_suspendidos')+'? '+window.i18n.t('saas.modal_detalle_tenant')))return;
  apiPost('/api/saas/tenants/'+id+'/suspend',{}).then(res=>{
    if(res.success){showToast(window.i18n.t('saas.kpi_suspendidos'),'success');loadTenants();}
    else showToast(res.error||window.i18n.t('common.error'),'error');
  });
}

function activateTenant(id){
  apiPost('/api/saas/tenants/'+id+'/activate',{}).then(res=>{
    if(res.success){showToast(window.i18n.t('saas.kpi_activos'),'success');loadTenants();}
    else showToast(res.error||window.i18n.t('common.error'),'error');
  });
}

function viewTenant(id){
  apiGet('/api/saas/tenants/'+id).then(res=>{
    if(!res.success||!res.data){showToast(window.i18n.t('common.error'),'error');return;}
    const t=res.data;
    document.getElementById('dt-title').textContent=t.EMP_NOMBRE||'Tenant #'+id;
    const body=document.getElementById('dt-body');
    const plan=t.suscripcion?{nombre:t.suscripcion.PLAN_NOMBRE,precio:t.suscripcion.PLAN_PRECIO_MENSUAL}:{nombre:t.EMP_PLAN,precio:0};
    body.innerHTML='<div style="padding:24px;">'+
      '<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:20px;">'+
        '<div style="text-align:center;padding:16px;background:var(--bg-primary);border-radius:8px;border:1px solid var(--border-primary);"><div style="font-size:22px;font-weight:700;color:var(--accent);">'+(t.TOTAL_PEDIDOS||0)+'</div><div style="font-size:10px;color:var(--text-muted);">'+window.i18n.t('saas.col_pedidos')+'</div></div>'+
        '<div style="text-align:center;padding:16px;background:var(--bg-primary);border-radius:8px;border:1px solid var(--border-primary);"><div style="font-size:22px;font-weight:700;color:var(--success);">'+(t.TOTAL_CHOFERES||0)+'</div><div style="font-size:10px;color:var(--text-muted);">'+window.i18n.t('saas.col_choferes')+'</div></div>'+
        '<div style="text-align:center;padding:16px;background:var(--bg-primary);border-radius:8px;border:1px solid var(--border-primary);"><div style="font-size:22px;font-weight:700;color:var(--warning);">'+(t.TOTAL_CLIENTES||0)+'</div><div style="font-size:10px;color:var(--text-muted);">'+window.i18n.t('saas.col_clientes')+'</div></div>'+
        '<div style="text-align:center;padding:16px;background:var(--bg-primary);border-radius:8px;border:1px solid var(--border-primary);"><div style="font-size:22px;font-weight:700;color:#8b5cf6;">'+(t.TOTAL_USUARIOS||0)+'</div><div style="font-size:10px;color:var(--text-muted);">'+window.i18n.t('saas.usuarios_titulo')+'</div></div>'+
      '</div>'+
      '<div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:20px;">'+
        '<div><h4 style="font-size:12px;font-weight:600;margin-bottom:8px;">'+window.i18n.t('saas.config_nombre')+'</h4>'+
          '<div style="font-size:12px;line-height:2;color:var(--text-secondary);">'+
            '<div><span style="color:var(--text-muted);">RFC:</span> '+(t.EMP_RFC||'-')+'</div>'+
            '<div><span style="color:var(--text-muted);">'+window.i18n.t('saas.col_email')+':</span> '+(t.EMP_EMAIL||'-')+'</div>'+
            '<div><span style="color:var(--text-muted);">'+window.i18n.t('saas.modal_telefono')+':</span> '+(t.EMP_TELEFONO||'-')+'</div>'+
            '<div><span style="color:var(--text-muted);">'+window.i18n.t('saas.col_plan')+':</span> '+planBadge(t.EMP_PLAN||'STARTER')+' ('+formatCurrency(plan.precio)+'/'+window.i18n.t('saas.kpi_pagos_pend').replace('.','').toLowerCase()+')</div>'+
            '<div><span style="color:var(--text-muted);">'+window.i18n.t('saas.col_estado')+':</span> '+statusBadge(t.EMP_ESTATUS)+'</div>'+
          '</div></div>'+
        '<div><h4 style="font-size:12px;font-weight:600;margin-bottom:8px;">'+window.i18n.t('saas.usuarios_titulo')+'</h4>'+
          (t.usuarios||[]).map(u=>'<div style="display:flex;align-items:center;gap:8px;padding:6px 0;border-bottom:1px solid var(--border-primary);">'+
            '<div class="avatar" style="background:var(--accent-bg);color:var(--accent);width:24px;height:24px;font-size:9px;">'+(u.USU_NOMBRE||'?').substring(0,2).toUpperCase()+'</div>'+
            '<div style="flex:1;"><div style="font-size:12px;font-weight:500;">'+(u.USU_NOMBRE||'-')+'</div><div style="font-size:10px;color:var(--text-muted);">'+(u.USU_USUARIO||'')+'</div></div>'+
            statusBadge(u.USU_ROL||'')+
          '</div>').join('')+
        '</div>'+
      '</div>'+
      (t.pagos_recientes&&t.pagos_recientes.length?'<h4 style="font-size:12px;font-weight:600;margin-bottom:8px;">'+window.i18n.t('saas.cobros_titulo')+'</h4>'+
        '<table><thead><tr><th>'+window.i18n.t('saas.col_fecha')+'</th><th>'+window.i18n.t('saas.col_total')+'</th><th>'+window.i18n.t('saas.col_estado')+'</th></tr></thead><tbody>'+
        t.pagos_recientes.map(p=>'<tr><td>'+(p.COB_FECHA_COBRO||'-')+'</td><td style="font-weight:500;color:var(--success);">'+formatCurrency(p.COB_MONTO)+'</td><td>'+statusBadge(p.COB_ESTATUS||'PENDIENTE')+'</td></tr>').join('')+
        '</tbody></table>':'')+
      '</div>';
    openModal('modalDetalleTenant');
  });
}

/* ==========================================
   USUARIOS
   ========================================== */
function loadUsuarios(){
  apiGet('/api/saas/all-users').then(res=>{
    if(!res.data)return;
    DB_USUARIOS=res.data;
    renderUsuarios();
  });
}

function renderUsuarios(){
  const search=(document.getElementById('userSearch').value||'').toLowerCase();
  const rolFilter=document.getElementById('userRolFilter').value;
  let filtered=DB_USUARIOS.filter(u=>{
    const nombre=(u.USU_NOMBRE||'').toLowerCase();
    const usuario=(u.USU_USUARIO||'').toLowerCase();
    const matchSearch=!search||nombre.includes(search)||usuario.includes(search);
    const matchRol=!rolFilter||u.USU_ROL===rolFilter;
    return matchSearch&&matchRol;
  });
  const tbody=document.getElementById('usuariosTableBody');
  if(!tbody)return;
  tbody.innerHTML=filtered.map(u=>{
    const activo=u.USU_ACTIVO==='S';
    return '<tr>'+
      '<td>#'+u.USU_ID+'</td>'+
      '<td><div style="display:flex;align-items:center;gap:8px;"><div class="avatar" style="background:var(--accent-bg);color:var(--accent);">'+(u.USU_NOMBRE||'?').substring(0,2).toUpperCase()+'</div><span style="font-weight:500;">'+(u.USU_NOMBRE||'-')+'</span></div></td>'+
      '<td>'+(u.USU_USUARIO||'-')+'</td>'+
      '<td>'+planBadge(u.USU_ROL||'')+'</td>'+
      '<td style="font-size:12px;">'+(u.EMP_NOMBRE||'-')+'</td>'+
      '<td style="font-size:12px;">'+(u.USU_EMAIL||'-')+'</td>'+
      '<td>'+(activo?statusBadge('activo'):statusBadge('inactivo'))+'</td></tr>';
  }).join('');
}

/* ==========================================
   PEDIDOS GLOBAL
   ========================================== */
function loadPedidosGlobal(){
  apiGet('/api/saas/all-pedidos').then(res=>{
    if(!res.data)return;
    DB_PEDIDOS=res.data;
    const tenants=[...new Set(DB_PEDIDOS.map(p=>p.EMP_NOMBRE).filter(Boolean))];
    const sel=document.getElementById('pedGlobalTenant');
    if(sel){
      const current=sel.value;
      sel.innerHTML='<option value="">'+window.i18n.t('saas.filtro_todos_tenants')+'</option>'+tenants.map(t=>'<option value="'+t+'">'+t+'</option>').join('');
      sel.value=current;
    }
    renderPedidosGlobal();
  });
}

function renderPedidosGlobal(){
  const search=(document.getElementById('pedGlobalSearch').value||'').toLowerCase();
  const tenantFilter=document.getElementById('pedGlobalTenant').value;
  const statusFilter=document.getElementById('pedGlobalStatus').value;
  let filtered=DB_PEDIDOS.filter(p=>{
    const matchSearch=!search||(p.PED_NUMERO||'').toLowerCase().includes(search)||(p.PED_CLIENTE_NOMBRE||'').toLowerCase().includes(search);
    const matchTenant=!tenantFilter||p.EMP_NOMBRE===tenantFilter;
    const matchStatus=!statusFilter||p.PED_ESTADO===statusFilter;
    return matchSearch&&matchTenant&&matchStatus;
  }).slice(0,50);
  const tbody=document.getElementById('pedidosGlobalBody');
  if(!tbody)return;
  tbody.innerHTML=filtered.map(p=>'<tr>'+
    '<td style="font-weight:500;">#'+(p.PED_NUMERO||p.PED_ID)+'</td>'+
    '<td style="font-size:12px;">'+(p.EMP_NOMBRE||'-')+'</td>'+
    '<td>'+(p.PED_CLIENTE_NOMBRE||'-')+'</td>'+
    '<td style="font-size:12px;">'+(p.PED_DESTINO_DIR||'')+'</td>'+
    '<td>'+statusBadge((p.PED_ESTADO||'').toLowerCase())+'</td>'+
    '<td style="font-size:11px;">'+(p.PED_FECHA_PEDIDO||'')+'</td>'+
    '<td style="font-weight:500;">'+formatCurrency(p.PED_COSTO_TOTAL||p.PED_TOTAL||0)+'</td>'+
  '</tr>').join('');
}

/* ==========================================
   SUSCRIPCIONES
   ========================================== */
function loadSuscripciones(){
  apiGet('/api/saas/suscripciones').then(res=>{
    if(!res.data)return;
    DB_SUSCRIPCIONES=res.data;
    const activas=DB_SUSCRIPCIONES.filter(s=>s.SUS_ESTADO==='ACTIVA').length;
    const trial=DB_SUSCRIPCIONES.filter(s=>s.SUS_ESTADO==='TRIAL').length;
    const pausadas=DB_SUSCRIPCIONES.filter(s=>s.SUS_ESTADO==='PAUSADA').length;
    const canceladas=DB_SUSCRIPCIONES.filter(s=>s.SUS_ESTADO==='CANCELADA').length;
    document.getElementById('s-activas').textContent=activas;
    document.getElementById('s-trial').textContent=trial;
    document.getElementById('s-pausadas').textContent=pausadas;
    document.getElementById('s-canceladas').textContent=canceladas;
    renderSuscripciones();
  });
}

function renderSuscripciones(){
  const tbody=document.getElementById('suscripcionesBody');
  if(!tbody)return;
  tbody.innerHTML=DB_SUSCRIPCIONES.map(s=>'<tr>'+
    '<td style="font-weight:500;">'+(s.EMP_NOMBRE||'-')+'</td>'+
    '<td>'+planBadge(s.PLAN_NOMBRE||'')+'</td>'+
    '<td style="font-weight:500;">'+formatCurrency(s.PLAN_PRECIO_MENSUAL||0)+'/'+window.i18n.t('saas.kpi_pagos_pend').split('.')[0].toLowerCase()+'</td>'+
    '<td>'+statusBadge(s.SUS_ESTADO||'')+'</td>'+
    '<td style="font-size:11px;">'+(s.SUS_FECHA_INICIO||'-')+'</td>'+
    '<td style="font-size:11px;">'+(s.SUS_FECHA_PROXIMO_COBRO||'-')+'</td>'+
    '<td><div style="display:flex;gap:4px;">'+
      '<button class="btn btn-ghost btn-sm" onclick="showToast(\''+window.i18n.t('saas.col_detalle')+' '+s.SUS_ID+'\',\'info\')" title="'+window.i18n.t('common.view')+'"><i class="fas fa-eye" style="font-size:10px;"></i></button>'+
    '</div></td>'+
  '</tr>').join('');
}

/* ==========================================
   COBROS
   ========================================== */
function loadCobros(){
  apiGet('/api/saas/cobros/resumen').then(res=>{
    if(!res.success||!res.data)return;
    const d=res.data;
    document.getElementById('c-cobrado').textContent=formatCurrency(d.COBRADO);
    document.getElementById('c-pendiente').textContent=formatCurrency(d.PENDIENTE);
    document.getElementById('c-vencido').textContent=formatCurrency(d.VENCIDO);
    document.getElementById('c-total-cobros').textContent=d.TOTAL_COBROS||0;
  });

  apiGet('/api/saas/cobros').then(res=>{
    if(!res.data)return;
    DB_COBROS=res.data;
    renderCobros();
  });
}

function renderCobros(){
  const tbody=document.getElementById('cobrosBody');
  if(!tbody)return;
  tbody.innerHTML=DB_COBROS.map(c=>'<tr>'+
    '<td>#'+c.COB_ID+'</td>'+
    '<td style="font-weight:500;">'+(c.EMP_NOMBRE||'-')+'</td>'+
    '<td>'+planBadge(c.PLAN_NOMBRE||'')+'</td>'+
    '<td style="font-weight:500;color:var(--success);">'+formatCurrency(c.COB_MONTO||0)+'</td>'+
    '<td style="font-size:12px;">'+(c.COB_CONCEPTO||'-')+'</td>'+
    '<td style="font-size:12px;">'+(c.COB_METODO_PAGO||'-')+'</td>'+
    '<td>'+statusBadge(c.COB_ESTATUS||'PENDIENTE')+'</td>'+
    '<td style="font-size:11px;">'+(c.COB_FECHA_COBRO||'')+'</td>'+
  '</tr>').join('');
}

/* ==========================================
   PLANES
   ========================================== */
function loadPlanes(){
  apiGet('/api/saas/planes').then(res=>{
    if(!res.data||!res.data.length){
      apiGet('/api/billing/planes').then(res2=>{
        if(res2.data)renderPlanes(res2.data);
      });
      return;
    }
    renderPlanes(res.data);
  }).catch(()=>{
    apiGet('/api/billing/planes').then(res=>{
      if(res.data)renderPlanes(res.data);
    });
  });
}

function renderPlanes(planes){
  const el=document.getElementById('planesContainer');
  if(!el)return;
  el.innerHTML=planes.map(p=>{
    const price=p.price_mxn||p.PLAN_PRECIO_MENSUAL||0;
    const maxU=p.max_usuarios||p.PLAN_MAX_USUARIOS||0;
    const maxC=p.max_choferes||p.PLAN_MAX_CHOFERES||0;
    const maxP=p.max_pedidos_mes||p.PLAN_MAX_ENVIOS_MES||0;
    const features=(typeof p.features==='string'?p.features.split(' '):p.features)||[];
    return '<div class="card" style="text-align:center;">'+
      '<div style="width:48px;height:48px;background:var(--accent-bg);border-radius:12px;display:flex;align-items:center;justify-content:center;margin:0 auto 12px;"><i class="fas fa-'+(p.id==='ENTERPRISE'||p.PLAN_ID===3?'crown':'bolt')+'" style="color:var(--accent);font-size:18px;"></i></div>'+
      '<h3 style="font-size:16px;font-weight:600;margin-bottom:4px;">'+(p.name||p.PLAN_NOMBRE||'')+'</h3>'+
      '<div style="font-size:28px;font-weight:700;color:var(--accent);margin:8px 0;">$'+price.toLocaleString()+'<span style="font-size:12px;color:var(--text-muted);font-weight:400;">/mes</span></div>'+
      '<div style="font-size:12px;color:var(--text-muted);margin-bottom:16px;">'+maxP+' '+window.i18n.t('saas.kpi_pedidos_mes').toLowerCase()+'</div>'+
      '<div style="text-align:left;font-size:12px;color:var(--text-secondary);line-height:2.4;padding:0 16px;">'+
        '<div><i class="fas fa-check" style="color:var(--success);margin-right:8px;font-size:10px;"></i> '+maxU+' '+window.i18n.t('saas.col_choferes').toLowerCase()+'</div>'+
        '<div><i class="fas fa-check" style="color:var(--success);margin-right:8px;font-size:10px;"></i> '+maxC+' '+window.i18n.t('saas.col_choferes').toLowerCase()+'</div>'+
        (Array.isArray(features)?features.slice(0,3).map(f=>'<div><i class="fas fa-check" style="color:var(--success);margin-right:8px;font-size:10px;"></i> '+f.replace(/_/g,' ')+'</div>').join(''):'')+
      '</div>'+
      '<div style="margin-top:16px;padding-top:16px;border-top:1px solid var(--border-primary);font-size:11px;color:var(--text-muted);">'+
        p.stripe_available||p.mp_available?'<i class="fas fa-credit-card" style="color:var(--success);margin-right:4px;"></i> '+window.i18n.t('saas.kpi_cobrado'):'<i class="fas fa-info-circle" style="color:var(--text-muted);margin-right:4px;"></i> '+window.i18n.t('saas.btn_guardar_config')+
      '</div></div>';
  }).join('');
}

/* ==========================================
   AUDITORIA
   ========================================== */
function loadAuditoria(){
  apiGet('/api/saas/audit').then(res=>{
    if(!res.data)return;
    const tbody=document.getElementById('auditBody');
    if(!tbody)return;
    tbody.innerHTML=res.data.map(a=>'<tr>'+
      '<td>#'+a.AUD_ID+'</td>'+
      '<td style="font-size:12px;">'+(a.EMP_NOMBRE||'-')+'</td>'+
      '<td style="font-size:12px;">'+(a.AUD_USUARIO||'-')+'</td>'+
      '<td><span class="badge badge-info">'+(a.AUD_ACCION||'-')+'</span></td>'+
      '<td style="font-size:12px;">'+(a.AUD_TABLA||'-')+'</td>'+
      '<td style="font-size:11px;max-width:200px;overflow:hidden;text-overflow:ellipsis;">'+(a.AUD_DETALLE||'-')+'</td>'+
      '<td style="font-size:11px;">'+(a.AUD_FECHA||'')+'</td>'+
    '</tr>').join('');
  });
}

/* ==========================================
   GLOBAL SEARCH
   ========================================== */
function globalSearchFn(){
  const q=(document.getElementById('globalSearch').value||'').toLowerCase().trim();
  if(!q)return;
  if(DB_TENANTS.length){
    const match=DB_TENANTS.find(t=>(t.EMP_NOMBRE||'').toLowerCase().includes(q));
    if(match){
      document.querySelectorAll('.nav-item').forEach(n=>n.classList.remove('active'));
      document.querySelectorAll('.section').forEach(s=>s.classList.remove('active'));
      document.querySelector('.nav-item[data-section="tenants"]').classList.add('active');
      document.getElementById('section-tenants').classList.add('active');
      document.getElementById('tenantSearch').value=q;
      renderTenants();
    }
  }
}

/* ==========================================
   REFRESH
   ========================================== */
function refreshAll(){
  showToast(window.i18n.t('saas.refresh')+'...','info');
  const active=document.querySelector('.nav-item.active');
  if(active)loadSection(active.getAttribute('data-section'));
  setTimeout(()=>showToast(window.i18n.t('saas.refresh'),'success'),600);
}

/* ==========================================
   SUPPORT TICKETS
   ========================================== */
async function loadSaasTickets() {
  try {
    const r = await fetch(API_BASE + '/api/tickets', { headers: HEADERS });
    const data = await r.json();
    if (!data.success) return;
    const tickets = data.tickets || [];
    // Update KPIs
    const abiertos = tickets.filter(t => t.TICKET_ESTADO === 'ABIERTO').length;
    const progreso = tickets.filter(t => t.TICKET_ESTADO === 'EN_PROCESO').length;
    const cerrados = tickets.filter(t => ['RESUELTO','CERRADO'].includes(t.TICKET_ESTADO)).length;
    const el1 = document.getElementById('sp-abiertos'); if(el1) el1.textContent = abiertos;
    const el2 = document.getElementById('sp-progreso'); if(el2) el2.textContent = progreso;
    const el3 = document.getElementById('sp-cerrados'); if(el3) el3.textContent = cerrados;
    // Render table
    const tbody = document.getElementById('saasTicketsTableBody');
    if (!tbody) return;
    if (tickets.length === 0) {
      tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;padding:24px;color:var(--text-muted);">No hay tickets</td></tr>';
      return;
    }
    const prioridadColors = { ALTA: 'var(--danger)', MEDIA: 'var(--warning)', BAJA: 'var(--success)' };
    const estadoColors = { ABIERTO: 'var(--danger)', EN_PROCESO: 'var(--warning)', RESUELTO: 'var(--success)', CERRADO: 'var(--text-muted)' };
    tbody.innerHTML = tickets.slice(0, 50).map(t => `
      <tr>
        <td style="font-size:11px;font-weight:600;">${t.TICKET_NUM || t.TICKET_ID}</td>
        <td style="font-size:11px;">${t.TICKET_ASUNTO || ''}</td>
        <td><span style="font-size:10px;padding:2px 8px;border-radius:10px;background:${prioridadColors[t.TICKET_PRIORIDAD] || 'var(--text-muted)'}22;color:${prioridadColors[t.TICKET_PRIORIDAD] || 'var(--text-muted)'};">${t.TICKET_PRIORIDAD || ''}</span></td>
        <td><span style="font-size:10px;padding:2px 8px;border-radius:10px;background:${estadoColors[t.TICKET_ESTADO] || 'var(--text-muted)'}22;color:${estadoColors[t.TICKET_ESTADO] || 'var(--text-muted)'};">${t.TICKET_ESTADO || ''}</span></td>
        <td style="font-size:11px;">${t.TICKET_CATEGORIA || ''}</td>
        <td style="font-size:10px;color:var(--text-muted);">${t.TICKET_FECHA_CREACION ? new Date(t.TICKET_FECHA_CREACION).toLocaleDateString() : ''}</td>
      </tr>
    `).join('');
  } catch(e) { console.warn('SaaS tickets error:', e); }
}

document.addEventListener('DOMContentLoaded', () => { setTimeout(loadSaasTickets, 500); });

/* ==========================================
   SaaS CONFIG
   ========================================== */
async function saveSaasConfig() {
  try {
    const maintenanceToggle = document.querySelector('#section-config .toggle');
    const isMaintenance = maintenanceToggle ? maintenanceToggle.classList.contains('active') : false;
    const inputs = document.querySelectorAll('#section-config input[type="number"]');
    const config = {
      maintenance_mode: isMaintenance,
      max_free_tenants: inputs[0] ? parseInt(inputs[0].value) : 3,
      rate_limit: inputs[1] ? parseInt(inputs[1].value) : 200,
    };
    const r = await fetch(API_BASE + '/api/saas/config', {
      method: 'POST', headers: HEADERS,
      body: JSON.stringify(config)
    });
    const data = await r.json();
    if (data.success) {
      if (typeof showToast === 'function') showToast('Configuracion guardada', 'success');
    }
  } catch(e) { console.warn('Save config error:', e); }
}

/* ==========================================
   INIT
   ========================================== */
window.addEventListener('load',()=>{
  loadDashboard();
  loadTenants();
});
window.addEventListener('themechange',()=>{
  if(chartRevenue){chartRevenue.update()}
  if(chartPlanes){chartPlanes.update()}
});
