const API_BASE=window.location.origin;
const HEADERS={'X-Emp-Id':'1','Content-Type':'application/json'};

/* ==========================================
   GLOBAL STATE
   ========================================== */
let DB_ZONAS=[], DB_PEDIDOS=[], DB_CHOFERES=[], DB_VEHICULOS=[], DB_CLIENTES=[], DB_FACTURAS=[], DB_PAGOS=[], DB_USUARIOS=[], DB_SAAS=[];
let pedidosChart,revenueChart,dashboardMap,rutasMap,mrrChart,usageChart,cancelChart;

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
    if(sec==='rutas') setTimeout(initRutasMap,100);
  });
});

/* Sidebar toggle */
function toggleSidebar(){
  const sb=document.getElementById('sidebar');
  const mc=document.getElementById('mainContent');
  if(sb){sb.classList.toggle('collapsed');}
  if(mc){mc.classList.toggle('expanded');}
}

/* Pedidos filter */
let pedStatusFilter='';
function filterPedidos(status){
  pedStatusFilter=status;
  renderPedidos();
}

/* ==========================================
   HELPERS
   ========================================== */
function statusBadge(s){
  const c={pendiente:'badge-warning',transito:'badge-info',entregado:'badge-success',cancelado:'badge-danger',fallido:'badge-danger',activo:'badge-success',inactivo:'badge-gray',mantenimiento:'badge-warning',timbrada:'badge-success',completado:'badge-success',fallido_pago:'badge-danger',timbrando:'badge-info',borrador:'badge-gray'};
  return '<span class="badge '+(c[s]||'badge-gray')+'">'+s+'</span>';
}
function planBadge(p){
  const c={Starter:'badge-gray',Pro:'badge-info',Enterprise:'badge-warning',admin:'badge-warning',operacion:'badge-info',chofer:'badge-success',cliente:'badge-gray'};
  return '<span class="badge '+(c[p]||'badge-gray')+'">'+p+'</span>';
}
function formatCurrency(v){return '$'+(parseFloat(v)||0).toLocaleString('es-MX',{minimumFractionDigits:0,maximumFractionDigits:0})}
function getTheme(){try{return typeof ThemeManager!=='undefined'?ThemeManager.get():'dark';}catch(e){return 'dark';}}
function openModal(id){const m=document.getElementById(id);if(m)m.classList.add('show')}
function closeModal(id){const m=document.getElementById(id);if(m)m.classList.remove('show')}
function showToast(msg,type){
  const c=document.querySelector('.toast-container');if(!c)return;
  const t=document.createElement('div');t.className='toast toast-'+(type||'info');t.innerHTML='<i class="fas fa-'+(type==='success'?'check-circle':type==='error'?'exclamation-circle':'info-circle')+'"></i> '+msg;
  c.appendChild(t);setTimeout(()=>t.remove(),3000);
}

/* ==========================================
   API CALLS
   ========================================== */
function apiGet(path){return fetch(API_BASE+path,{headers:HEADERS}).then(r=>r.json()).catch(e=>({success:false,data:[],error:e.message}))}
function apiPost(path,data){return fetch(API_BASE+path,{method:'POST',headers:HEADERS,body:JSON.stringify(data)}).then(r=>r.json()).catch(e=>({success:false,error:e.message}))}
function apiPut(path,data){return fetch(API_BASE+path,{method:'PUT',headers:HEADERS,body:JSON.stringify(data)}).then(r=>r.json()).catch(e=>({success:false,error:e.message}))}
function apiDelete(path){return fetch(API_BASE+path,{method:'DELETE',headers:HEADERS}).then(r=>r.json()).catch(e=>({success:false,error:e.message}))}

/* ==========================================
   DASHBOARD
   ========================================== */
function loadDashboard(){
  apiGet('/api/dashboard/1').then(res=>{
    if(!res.success||!res.data)return;
    const d=res.data;
    const el=id=>document.getElementById(id);
    if(el('kpi-pedidos'))el('kpi-pedidos').textContent=d.PEDIDOS_HOY||0;
    if(el('kpi-entregas'))el('kpi-entregas').textContent=d.ENTREGAS_HOY||0;
    if(el('kpi-revenue'))el('kpi-revenue').textContent=formatCurrency(d.REVENUE_HOY||d.INGRESOS_HOY||0);
    if(el('kpi-choferes'))el('kpi-choferes').textContent=d.CHOFERES_ACTIVOS||0;
    if(el('kpi-tiempo'))el('kpi-tiempo').textContent=(d.TIEMPO_PROMEDIO||'28')+'m';
  }).catch(()=>{});

  // KPIs from pedidos
  apiGet('/api/pedidos').then(res=>{
    if(!res.data)return;
    DB_PEDIDOS=res.data;
    const el=id=>document.getElementById(id);
    const total=DB_PEDIDOS.length;
    const pendiente=DB_PEDIDOS.filter(p=>p.PED_ESTADO==='PENDIENTE'||p.PED_ESTADO==='pendiente').length;
    const transito=DB_PEDIDOS.filter(p=>p.PED_ESTADO==='EN_RUTA'||p.PED_ESTADO==='transito').length;
    const entregado=DB_PEDIDOS.filter(p=>p.PED_ESTADO==='ENTREGADO'||p.PED_ESTADO==='entregado').length;
    const cancelado=DB_PEDIDOS.filter(p=>p.PED_ESTADO==='CANCELADO'||p.PED_ESTADO==='cancelado').length;
    const revenue=DB_PEDIDOS.reduce((a,p)=>a+parseFloat(p.PED_TOTAL||p.total||0),0);
    if(el('ped-total'))el('ped-total').textContent=total;
    if(el('ped-pendiente'))el('ped-pendiente').textContent=pendiente;
    if(el('ped-transito'))el('ped-transito').textContent=transito;
    if(el('ped-entregado'))el('ped-entregado').textContent=entregado;
    if(el('kpi-revenue'))el('kpi-revenue').textContent=formatCurrency(revenue);
  }).catch(()=>{});
}

/* ==========================================
   PEDIDOS
   ========================================== */
function renderPedidos(){
  apiGet('/api/pedidos').then(res=>{
    if(!res.data)return;
    DB_PEDIDOS=res.data;
    let filtered=DB_PEDIDOS;
    if(pedStatusFilter){
      filtered=DB_PEDIDOS.filter(p=>(p.PED_ESTADO||'').toLowerCase()===pedStatusFilter.toLowerCase());
    }
    const tbody=document.getElementById('pedidosTableBody');
    if(!tbody)return;
    tbody.innerHTML=filtered.slice(0,50).map(p=>{
      const id=p.PED_ID||p.id;
      const folio=p.PED_NUMERO||'PED-'+id;
      const cliente=p.PED_CLIENTE_NOMBRE||'-';
      const destino=p.PED_DESTINO_DIR||'-';
      const chofer=p.CHOFER_ASIGNADO||'-';
      const estado=(p.PED_ESTADO||'pendiente').toLowerCase();
      const fecha=p.PED_FECHA_PEDIDO?new Date(p.PED_FECHA_PEDIDO).toLocaleDateString():'-';
      const total=p.PED_COSTO_TOTAL||0;
      return '<tr>'+
        '<td style="font-weight:500;color:var(--accent);">'+folio+'</td>'+
        '<td>'+cliente+'</td>'+
        '<td style="max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">'+destino+'</td>'+
        '<td>'+chofer+'</td>'+
        '<td>'+statusBadge(estado)+'</td>'+
        '<td>'+fecha+'</td>'+
        '<td style="font-weight:500;">'+formatCurrency(total)+'</td>'+
        '<td><div style="display:flex;gap:4px;">'+
          '<button class="btn btn-ghost btn-sm" onclick="verPedido('+id+')" title="Ver"><i class="fas fa-eye" style="font-size:10px;"></i></button>'+
          '<button class="btn btn-ghost btn-sm" onclick="eliminarPedido('+id+')" title="Eliminar" style="color:var(--danger,#ef4444);"><i class="fas fa-trash" style="font-size:10px;"></i></button>'+
        '</div></td></tr>';
    }).join('');
  }).catch(()=>showToast('Error cargando pedidos','error'));
}

function verPedido(id){
  const p=DB_PEDIDOS.find(x=>(x.PED_ID||x.id)==id);
  if(!p)return;
  showToast('Pedido: '+(p.PED_NUMERO||'PED-'+id)+' - '+(p.PED_ESTADO||''),'info');
}

function eliminarPedido(id){
  if(!confirm('Eliminar pedido #'+id+'?'))return;
  apiDelete('/api/pedidos/'+id).then(res=>{
    if(res.success){showToast('Pedido eliminado','success');renderPedidos();}
    else showToast(res.error||'Error al eliminar','error');
  });
}

/* ==========================================
   CHOFERES
   ========================================== */
function renderChoferes(){
  apiGet('/api/choferes').then(res=>{
    if(!res.data)return;
    DB_CHOFERES=res.data;
    const tbody=document.getElementById('choferesTableBody');
    if(!tbody)return;
    const activos=DB_CHOFERES.filter(c=>(c.CHO_ESTATUS||c.CHO_ESTADO||c.estado||'ACTIVO')==='ACTIVO').length;
    const inactivos=DB_CHOFERES.length-activos;
    const el=id=>document.getElementById(id);
    if(el('ch-activos'))el('ch-activos').textContent=activos;
    if(el('ch-inactivos'))el('ch-inactivos').textContent=inactivos;

    tbody.innerHTML=DB_CHOFERES.map(c=>{
      const id=c.CHO_ID||c.CHF_ID||c.id;
      const nombre=(c.CHO_NOMBRE||c.CHF_NOMBRE||c.nombre||'');
      const apellido=c.CHO_APELLIDO||c.CHF_APELLIDO||c.apellido||'';
      const full=(nombre+' '+apellido).trim()||'-';
      const tel=c.CHO_TELEFONO||c.CHF_TELEFONO||c.telefono||'-';
      const veh=c.CHO_VEHICULO||c.CHF_VEHICULO||c.vehiculo||'-';
      const estado=(c.CHO_ESTATUS||c.CHF_ESTADO||c.estado||'ACTIVO');
      return '<tr>'+
        '<td style="font-weight:500;">'+full+'</td>'+
        '<td>'+tel+'</td>'+
        '<td>'+veh+'</td>'+
        '<td>'+statusBadge(estado.toLowerCase())+'</td>'+
        '<td><div style="display:flex;gap:4px;">'+
          '<button class="btn btn-ghost btn-sm" onclick="editarChofer('+id+')" title="Editar"><i class="fas fa-pen" style="font-size:10px;"></i></button>'+
          '<button class="btn btn-ghost btn-sm" onclick="eliminarChofer('+id+',\''+full.replace(/'/g,"\\'")+'\')" title="Eliminar" style="color:var(--danger,#ef4444);"><i class="fas fa-trash" style="font-size:10px;"></i></button>'+
        '</div></td></tr>';
    }).join('');
  }).catch(()=>showToast('Error cargando choferes','error'));
}

function editarChofer(id){
  const c=DB_CHOFERES.find(x=>(x.CHO_ID||x.CHF_ID||x.id)==id);
  if(!c)return showToast('Chofer no encontrado','error');
  const modal=document.getElementById('modalNuevoChofer');
  if(!modal)return showToast('Modal no encontrado','error');
  const inputs=modal.querySelectorAll('input,select');
  inputs[0].value=c.CHO_NOMBRE||'';
  inputs[1].value=c.CHO_TELEFONO||'';
  inputs[2].value=c.CHO_LICENCIA||'';
  inputs[3].value='';
  inputs[4].value=c.CHO_EMAIL||'';
  inputs[5].value=(c.CHO_ESTATUS||'ACTIVO')==='ACTIVO'?'Activo':'Inactivo';
  modal.setAttribute('data-editing',id);
  const hdr=modal.querySelector('.modal-header h3');
  if(hdr)hdr.textContent='Editar Chofer';
  const btn=modal.querySelector('.modal-footer .btn-primary');
  if(btn)btn.innerHTML='<i class="fas fa-save" style="font-size:10px;"></i> Actualizar';
  openModal('modalNuevoChofer');
}

function saveChofer(){
  const modal=document.getElementById('modalNuevoChofer');
  if(!modal)return;
  const inputs=modal.querySelectorAll('input,select');
  const nombre=inputs[0].value.trim();
  const telefono=inputs[1].value.trim();
  const licencia=inputs[2].value.trim();
  const email=inputs[4].value.trim();
  const estatus=inputs[5].value==='Activo'?'ACTIVO':'INACTIVO';
  if(!nombre){showToast('Nombre requerido','error');return;}
  const data={nombre:nombre,telefono:telefono,licencia:licencia,email:email,estatus:estatus};
  const editingId=modal.getAttribute('data-editing');
  const isEdit=editingId&&editingId!=='';
  const promise=isEdit?apiPut('/api/choferes/'+editingId,data):apiPost('/api/choferes',data);
  promise.then(res=>{
    if(res.success){showToast(isEdit?'Chofer actualizado':'Chofer creado','success');closeModal('modalNuevoChofer');modal.removeAttribute('data-editing');renderChoferes();}
    else showToast(res.error||'Error al guardar','error');
  });
}
function eliminarChofer(id,nombre){
  if(!confirm('Eliminar chofer "'+nombre+'"'))return;
  apiDelete('/api/choferes/'+id).then(res=>{
    if(res.success){showToast('Chofer eliminado','success');renderChoferes();}
    else showToast(res.error||'Error al eliminar','error');
  });
}

/* ==========================================
   VEHICULOS
   ========================================== */
function renderVehiculos(){
  apiGet('/api/vehiculos').then(res=>{
    if(!res.data)return;
    DB_VEHICULOS=res.data;
    const tbody=document.getElementById('vehiculosTableBody');
    if(!tbody)return;

    tbody.innerHTML=DB_VEHICULOS.map(v=>{
      const id=v.VEH_ID||v.id;
      const unidad=v.VEH_UNIDAD||'-';
      const placa=v.VEH_PLACAS||v.VEH_PLACA||'-';
      const tipo=v.VEH_TIPO||v.tipo||'-';
      const marca=v.VEH_MARCA||v.marca||'-';
      const modelo=v.VEH_MODELO||v.modelo||'-';
      const chofer=v.CHOFER_NOMBRE||v.chofer||'-';
      const km=v.VEH_KM||v.km||0;
      const estado=(v.VEH_ESTATUS||v.VEH_ESTADO||v.estado||'DISPONIBLE');
      return '<tr>'+
        '<td style="font-weight:500;color:var(--accent);">'+unidad+'</td>'+
        '<td>'+placa+'</td>'+
        '<td>'+tipo+'</td>'+
        '<td>'+marca+' '+modelo+'</td>'+
        '<td>'+Number(km).toLocaleString()+'</td>'+
        '<td>'+statusBadge(estado.toLowerCase())+'</td>'+
        '<td><div style="display:flex;gap:4px;">'+
          '<button class="btn btn-ghost btn-sm" onclick="editarVehiculo('+id+')" title="Editar"><i class="fas fa-pen" style="font-size:10px;"></i></button>'+
        '</div></td></tr>';
    }).join('');
  }).catch(()=>showToast('Error cargando vehiculos','error'));
}

function editarVehiculo(id){
  const v=DB_VEHICULOS.find(x=>(x.VEH_ID||x.id)==id);
  if(!v)return showToast('Vehiculo no encontrado','error');
  const modal=document.getElementById('modalNuevoVehiculo');
  if(!modal)return;
  const inputs=modal.querySelectorAll('input,select');
  inputs[0].value=v.VEH_PLACAS||v.VEH_PLACA||'';
  inputs[1].value=v.VEH_TIPO||'CAMIONETA';
  inputs[2].value=v.VEH_MARCA||'';
  inputs[3].value=v.VEH_MODELO||'';
  inputs[4].value=v.VEH_ANIO||'';
  inputs[5].value=(v.VEH_ESTATUS||'DISPONIBLE')==='DISPONIBLE'?'Activo':'Mantenimiento';
  modal.setAttribute('data-editing',id);
  const hdr=modal.querySelector('.modal-header h3');
  if(hdr)hdr.textContent='Editar Vehiculo';
  const btn=modal.querySelector('.modal-footer .btn-primary');
  if(btn)btn.innerHTML='<i class="fas fa-save" style="font-size:10px;"></i> Actualizar';
  openModal('modalNuevoVehiculo');
}

function saveVehiculo(){
  const modal=document.getElementById('modalNuevoVehiculo');
  if(!modal)return;
  const inputs=modal.querySelectorAll('input,select');
  const placas=inputs[0].value.trim();
  const tipo=inputs[1].value;
  const marca=inputs[2].value.trim();
  const modelo=inputs[3].value.trim();
  const anio=inputs[4].value.trim();
  const estatus=inputs[5].value==='Activo'?'DISPONIBLE':'MANTENIMIENTO';
  if(!placas){showToast('Placas requeridas','error');return;}
  const data={unidad:placas,placas:placas,tipo:tipo,marca:marca,modelo:modelo,anio:anio,estatus:estatus};
  const editingId=modal.getAttribute('data-editing');
  const isEdit=editingId&&editingId!=='';
  const promise=isEdit?apiPut('/api/vehiculos/'+editingId,data):apiPost('/api/vehiculos',data);
  promise.then(res=>{
    if(res.success){showToast(isEdit?'Vehiculo actualizado':'Vehiculo creado','success');closeModal('modalNuevoVehiculo');modal.removeAttribute('data-editing');renderVehiculos();}
    else showToast(res.error||'Error al guardar','error');
  });
}

/* ==========================================
   CLIENTES
   ========================================== */
function renderClientes(){
  apiGet('/api/clientes').then(res=>{
    if(!res.data)return;
    DB_CLIENTES=res.data;
    const tbody=document.getElementById('clientesTableBody');
    if(!tbody)return;

    tbody.innerHTML=DB_CLIENTES.map(c=>{
      const id=c.CLI_ID||c.id;
      const nombre=c.CLI_RAZON_SOCIAL||c.CLI_NOMBRE||c.nombre||c.empresa||'-';
      const contacto=c.CLI_CONTACTO||c.contacto||'-';
      const email=c.CLI_EMAIL||c.email||'-';
      const tel=c.CLI_TELEFONO||c.telefono||'-';
      const estado=(c.CLI_ESTATUS||c.CLI_ESTADO||c.estado||'ACTIVO');
      return '<tr>'+
        '<td style="font-weight:500;">'+nombre+'</td>'+
        '<td>'+contacto+'</td>'+
        '<td>'+email+'</td>'+
        '<td>'+tel+'</td>'+
        '<td>'+statusBadge(estado.toLowerCase())+'</td>'+
        '<td><div style="display:flex;gap:4px;">'+
          '<button class="btn btn-ghost btn-sm" onclick="editarCliente('+id+')" title="Editar"><i class="fas fa-pen" style="font-size:10px;"></i></button>'+
          '<button class="btn btn-ghost btn-sm" onclick="eliminarCliente('+id+',\''+nombre.replace(/'/g,"\\'")+'\')" title="Eliminar" style="color:var(--danger,#ef4444);"><i class="fas fa-trash" style="font-size:10px;"></i></button>'+
        '</div></td></tr>';
    }).join('');
  }).catch(()=>showToast('Error cargando clientes','error'));
}

function editarCliente(id){
  const c=DB_CLIENTES.find(x=>(x.CLI_ID||x.id)==id);
  if(!c)return showToast('Cliente no encontrado','error');
  const modal=document.getElementById('modalNuevoCliente');
  if(!modal)return;
  const inputs=modal.querySelectorAll('input,select');
  inputs[0].value=c.CLI_RAZON_SOCIAL||c.CLI_NOMBRE||'';
  inputs[1].value=c.CLI_RFC||'';
  inputs[2].value=c.CLI_CONTACTO||'';
  inputs[3].value=c.CLI_EMAIL||'';
  inputs[4].value=c.CLI_TELEFONO||'';
  inputs[5].value=c.CLI_TIPO_CLIENTE||'GENERAL';
  modal.setAttribute('data-editing',id);
  const hdr=modal.querySelector('.modal-header h3');
  if(hdr)hdr.textContent='Editar Cliente';
  const btn=modal.querySelector('.modal-footer .btn-primary');
  if(btn)btn.innerHTML='<i class="fas fa-save" style="font-size:10px;"></i> Actualizar';
  openModal('modalNuevoCliente');
}

function saveCliente(){
  const modal=document.getElementById('modalNuevoCliente');
  if(!modal)return;
  const inputs=modal.querySelectorAll('input,select');
  const razon=inputs[0].value.trim();
  const rfc=inputs[1].value.trim();
  const contacto=inputs[2].value.trim();
  const email=inputs[3].value.trim();
  const telefono=inputs[4].value.trim();
  if(!razon){showToast('Razon social requerida','error');return;}
  const data={razon_social:razon,rfc:rfc,contacto:contacto,email:email,telefono:telefono};
  const editingId=modal.getAttribute('data-editing');
  const isEdit=editingId&&editingId!=='';
  const promise=isEdit?apiPut('/api/clientes/'+editingId,data):apiPost('/api/clientes',data);
  promise.then(res=>{
    if(res.success){showToast(isEdit?'Cliente actualizado':'Cliente creado','success');closeModal('modalNuevoCliente');modal.removeAttribute('data-editing');renderClientes();}
    else showToast(res.error||'Error al guardar','error');
  });
}
function eliminarCliente(id,nombre){
  if(!confirm('Eliminar cliente "'+nombre+'"'))return;
  apiDelete('/api/clientes/'+id).then(res=>{
    if(res.success){showToast('Cliente eliminado','success');renderClientes();}
    else showToast(res.error||'Error al eliminar','error');
  });
}

/* ==========================================
   FACTURAS CFDI
   ========================================== */
function renderCFDI(){
  apiGet('/api/cfdi/facturas?emp_id=1').then(res=>{
    if(!res.data)return;
    DB_FACTURAS=res.data;
    const tbody=document.getElementById('cfdiTableBody');
    const el=id=>document.getElementById(id);

    const timbradas=DB_FACTURAS.filter(f=>(f.CFDI_ESTADO||f.estado||'')==='timbrada').length;
    const pendientes=DB_FACTURAS.filter(f=>(f.CFDI_ESTADO||f.estado||'')==='pendiente').length;
    const canceladas=DB_FACTURAS.filter(f=>(f.CFDI_ESTADO||f.estado||'')==='cancelada').length;
    const totalFac=DB_FACTURAS.filter(f=>(f.CFDI_ESTADO||f.estado||'')==='timbrada').reduce((a,f)=>a+parseFloat(f.CFDI_IMPORTE||f.importe||0),0);

    if(el('cfdi-timbradas'))el('cfdi-timbradas').textContent=timbradas;
    if(el('cfdi-pendientes'))el('cfdi-pendientes').textContent=pendientes;
    if(el('cfdi-canceladas'))el('cfdi-canceladas').textContent=canceladas;
    if(el('cfdi-total'))el('cfdi-total').textContent=formatCurrency(totalFac);

    if(!tbody)return;
    tbody.innerHTML=DB_FACTURAS.slice(0,30).map(f=>{
      const id=f.CFDI_ID||f.id;
      const folio=f.CFDI_FOLIO||f.folio||'FAC-'+id;
      const uuid=(f.CFDI_UUID||f.uuid||'').substring(0,8);
      const cliente=f.CFDI_CLIENTE||f.cliente||'-';
      const rfc=f.CFDI_RFC||f.rfc||'-';
      const importe=f.CFDI_IMPORTE||f.importe||0;
      const fecha=f.CFDI_FECHA||f.fecha||'-';
      const estado=(f.CFDI_ESTADO||f.estado||'pendiente');
      return '<tr>'+
        '<td style="font-weight:500;color:var(--accent);">'+folio+'</td>'+
        '<td style="font-size:11px;font-family:monospace;">'+(uuid||'Sin timbrar')+'</td>'+
        '<td>'+cliente+'</td>'+
        '<td>'+rfc+'</td>'+
        '<td style="font-weight:500;">'+formatCurrency(importe)+'</td>'+
        '<td>'+fecha+'</td>'+
        '<td>'+statusBadge(estado)+'</td>'+
        '<td><div style="display:flex;gap:4px;">'+
          (estado==='pendiente'?'<button class="btn btn-success btn-sm" onclick="timbrarCFDI('+id+')" title="Timbrar"><i class="fas fa-stamp" style="font-size:10px;"></i></button>':'')+
          (estado==='timbrada'?'<button class="btn btn-danger btn-sm" onclick="cancelarCFDI('+id+')" title="Cancelar"><i class="fas fa-ban" style="font-size:10px;"></i></button>':'')+
        '</div></td></tr>';
    }).join('');
  }).catch(()=>showToast('Error cargando facturas','error'));
}

function timbrarCFDI(id){
  apiPost('/api/cfdi/facturas/'+id+'/timbrar',{}).then(res=>{
    if(res.success){showToast('Factura timbrada','success');renderCFDI();}
    else showToast(res.error||'Error al timbrar','error');
  });
}
function cancelarCFDI(id){
  if(!confirm('Cancelar esta factura?'))return;
  apiPost('/api/cfdi/facturas/'+id+'/cancelar',{}).then(res=>{
    if(res.success){showToast('Factura cancelada','success');renderCFDI();}
    else showToast(res.error||'Error al cancelar','error');
  });
}

/* ==========================================
   PAGOS
   ========================================== */
function renderPagos(){
  apiGet('/api/pagos/transacciones').then(res=>{
    if(!res.data)return;
    DB_PAGOS=res.data;
    const tbody=document.getElementById('pagosTableBody');

    const cobrado=DB_PAGOS.filter(p=>(p.TRP_ESTATUS||p.PAG_ESTADO||'')==='PAGADO'||(p.TRP_ESTATUS||'')==='COMPLETADO').reduce((a,p)=>a+parseFloat(p.TRP_MONTO||p.PAG_MONTO||p.monto||0),0);
    const pendiente=DB_PAGOS.filter(p=>(p.TRP_ESTATUS||p.PAG_ESTADO||'')==='PENDIENTE').reduce((a,p)=>a+parseFloat(p.TRP_MONTO||p.PAG_MONTO||p.monto||0),0);
    const el=id=>document.getElementById(id);
    if(el('pag-cobrado'))el('pag-cobrado').textContent=formatCurrency(cobrado);
    if(el('pag-pendiente'))el('pag-pendiente').textContent=formatCurrency(pendiente);

    if(!tbody)return;
    tbody.innerHTML=DB_PAGOS.slice(0,30).map(p=>{
      const id=p.TRP_ID||p.PAG_ID||p.id;
      const cliente=p.CLI_NOMBRE||p.cliente||'-';
      const monto=p.TRP_MONTO||p.PAG_MONTO||p.monto||0;
      const metodo=p.TRP_METODO||p.PAG_METODO||p.metodo||'-';
      const ref=p.TRP_NUM_REFERENCIA||p.PAG_REFERENCIA||p.referencia||'-';
      const fecha=p.TRP_FECHA_REGISTRO||p.PAG_FECHA||p.fecha||'-';
      const estado=(p.TRP_ESTATUS||p.PAG_ESTADO||p.estado||'PENDIENTE');
      return '<tr>'+
        '<td>#'+id+'</td>'+
        '<td>'+cliente+'</td>'+
        '<td style="font-weight:500;">'+formatCurrency(monto)+'</td>'+
        '<td>'+metodo+'</td>'+
        '<td style="font-family:monospace;font-size:11px;">'+ref+'</td>'+
        '<td>'+fecha+'</td>'+
        '<td>'+statusBadge(estado.toLowerCase())+'</td>'+
        '<td><button class="btn btn-ghost btn-sm" onclick="eliminarPago('+id+')" title="Eliminar" style="color:var(--danger,#ef4444);"><i class="fas fa-trash" style="font-size:10px;"></i></button></td>'+
        '</tr>';
    }).join('');
  }).catch(()=>showToast('Error cargando pagos','error'));
}

function eliminarPago(id){
  if(!confirm('Eliminar pago #'+id+'?'))return;
  apiDelete('/api/pagos/transacciones/'+id).then(res=>{
    if(res.success){showToast('Pago eliminado','success');renderPagos();}
    else showToast(res.error||'Error al eliminar','error');
  });
}

/* ==========================================
   SaaS / BILLING
   ========================================== */
let billingData = null;

function loadBilling() {
  // Load current billing state
  apiGet('/api/billing/estado').then(res => {
    if (!res.success || !res.data) return;
    billingData = res.data;
    DB_SAAS = res.data;

    const planName = document.getElementById('billing-plan-name');
    const planPrice = document.getElementById('billing-plan-price');
    const statusDot = document.getElementById('billing-status-dot');
    const statusText = document.getElementById('billing-status-text');
    const fechaInicio = document.getElementById('billing-fecha-inicio');
    const proximoCobro = document.getElementById('billing-proximo-cobro');
    const usoPedidos = document.getElementById('billing-uso-pedidos');
    const usoChoferes = document.getElementById('billing-uso-choferes');
    const usoUsuarios = document.getElementById('billing-uso-usuarios');

    if (planName) planName.textContent = billingData.plan_nombre || 'Starter';
    if (planPrice) planPrice.textContent = formatCurrency(billingData.precio_mensual || 999) + ' MXN/mes';

    if (billingData.suscripcion_activa) {
      if (statusDot) statusDot.style.background = 'var(--success)';
      if (statusText) statusText.textContent = 'Activa';
    } else {
      if (statusDot) statusDot.style.background = 'var(--warning)';
      if (statusText) statusText.textContent = 'Sin suscripcion';
    }

    if (fechaInicio) fechaInicio.textContent = 'Inicio: ' + (billingData.suscripcion_inicio || '--');
    if (proximoCobro) proximoCobro.textContent = 'Total pagado: ' + formatCurrency(billingData.monto_completado || 0);

    // Usage - real data from API
    if (usoPedidos) usoPedidos.textContent = (billingData.pedidos_usados || 0) + '/' + (billingData.limite_pedidos_mes || 500);
    if (usoChoferes) usoChoferes.textContent = (billingData.choferes || 0) + '/' + (billingData.limite_choferes || 10);
    if (usoUsuarios) usoUsuarios.textContent = (billingData.usuarios || 0) + '/' + (billingData.limite_usuarios || 5);
  }).catch(() => {});

  // Load payment history
  apiGet('/api/billing/pagos').then(res => {
    if (!res.success || !res.data) return;
    const tbody = document.getElementById('billingPagosTableBody');
    if (!tbody) return;

    if (res.data.length === 0) {
      tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;color:var(--text-muted);padding:24px;">Sin pagos registrados</td></tr>';
      return;
    }

    tbody.innerHTML = res.data.map(p => {
      const fecha = p.TRP_FECHA_REGISTRO || p.COB_FECHA_COBRO || '-';
      const monto = formatCurrency(p.TRP_MONTO || p.COB_MONTO || 0);
      const metodo = p.TRP_METODO || p.COB_METODO_PAGO || '-';
      const ref = p.TRP_NUM_REFERENCIA || p.COB_REFERENCIA_PAGO || '-';
      const estatus = (p.TRP_ESTATUS || p.COB_ESTATUS || 'PENDIENTE').toLowerCase();
      return '<tr>' +
        '<td>' + fecha + '</td>' +
        '<td style="font-weight:500;color:var(--success);">' + monto + '</td>' +
        '<td>' + metodo + '</td>' +
        '<td>' + ref + '</td>' +
        '<td>' + statusBadge(estatus) + '</td>' +
        '</tr>';
    }).join('');
  }).catch(() => {});

  // Init charts
  initBillingCharts();
}

function selectPlan(planName) {
  if (!confirm('Deseas cambiar al plan ' + planName + '?')) return;

  apiPost('/api/billing/suscripcion', { plan: planName, provider: 'manual' }).then(res => {
    if (res.success) {
      showToast('Plan actualizado a ' + planName, 'success');
      loadBilling();
    } else {
      showToast(res.error || 'Error actualizando plan', 'error');
    }
  }).catch(() => showToast('Error de conexion', 'error'));
}

function cancelarSuscripcion() {
  if (!confirm('Seguro que deseas cancelar tu suscripcion? Se revertira al plan Starter.')) return;

  apiPost('/api/billing/cancelar', {}).then(res => {
    if (res.success) {
      showToast('Suscripcion cancelada', 'success');
      loadBilling();
    } else {
      showToast(res.error || 'Error cancelando', 'error');
    }
  }).catch(() => showToast('Error de conexion', 'error'));
}

function openUpgradeModal() {
  showToast('Selecciona un plan de la lista', 'info');
}

function pagarManual() {
  const monto = prompt('Monto del pago (MXN):');
  if (!monto || isNaN(monto)) return;

  const metodo = prompt('Metodo de pago (EFECTIVO, TRANSFERENCIA, TARJETA):') || 'EFECTIVO';
  const ref = prompt('Referencia (opcional):') || '';

  apiPost('/api/billing/pago', {
    monto: parseFloat(monto),
    metodo: metodo,
    referencia: ref,
    notas: 'Pago manual registrado desde admin'
  }).then(res => {
    if (res.success) {
      showToast('Pago registrado: ' + formatCurrency(monto), 'success');
      loadBilling();
    } else {
      showToast(res.error || 'Error registrando pago', 'error');
    }
  }).catch(() => showToast('Error de conexion', 'error'));
}

function initBillingCharts() {
  const isDark = getTheme() === 'dark';
  const textColor = isDark ? '#9ca3af' : '#6b7280';
  const gridColor = isDark ? 'rgba(75,85,99,0.3)' : 'rgba(209,213,219,0.5)';

  // Get real data from loaded billing state
  const usageData = [
    DB_SAAS?.limites?.pedidos_mes ? Math.round((DB_SAAS.pedidos_usados||0)/DB_SAAS.limites.pedidos_mes*100) : 0,
    DB_SAAS?.limites?.choferes ? Math.round((DB_SAAS.choferes||0)/DB_SAAS.limites.choferes*100) : 0,
    DB_SAAS?.limites?.usuarios ? Math.round((DB_SAAS.usuarios||0)/DB_SAAS.limites.usuarios*100) : 0
  ];
  const revenueData = DB_SAAS?.pagos?.length > 0
    ? DB_SAAS.pagos.slice(-6).map(p => p.monto || 0)
    : [DB_SAAS?.precio_mensual || 0];
  const revenueLabels = DB_SAAS?.pagos?.length > 0
    ? DB_SAAS.pagos.slice(-6).map(p => { const d = new Date(p.fecha); return d.toLocaleString('es-MX',{month:'short'}); })
    : ['Actual'];

  // Usage chart
  const usageCtx = document.getElementById('chartUsageBilling');
  if (usageCtx && typeof Chart !== 'undefined') {
    if (window._usageBillingChart) window._usageBillingChart.destroy();
    window._usageBillingChart = new Chart(usageCtx, {
      type: 'doughnut',
      data: {
        labels: ['Pedidos', 'Choferes', 'Usuarios'],
        datasets: [{
          data: usageData,
          backgroundColor: ['var(--accent)', 'var(--success)', 'var(--warning)'],
          borderWidth: 0
        }]
      },
      options: {
        responsive: true,
        plugins: { legend: { position: 'bottom', labels: { color: textColor, font: { size: 11 } } } }
      }
    });
  }

  // Revenue chart
  const revCtx = document.getElementById('chartRevenueBilling');
  if (revCtx && typeof Chart !== 'undefined') {
    if (window._revBillingChart) window._revBillingChart.destroy();
    window._revBillingChart = new Chart(revCtx, {
      type: 'bar',
      data: {
        labels: revenueLabels,
        datasets: [{
          label: 'Ingresos',
          data: revenueData,
          backgroundColor: 'var(--accent)',
          borderRadius: 4
        }]
      },
      options: {
        responsive: true,
        scales: {
          y: { beginAtZero: true, ticks: { color: textColor, font: { size: 10 } }, grid: { color: gridColor } },
          x: { ticks: { color: textColor, font: { size: 10 } }, grid: { display: false } }
        },
        plugins: { legend: { display: false } }
      }
    });
  }
}

/* ==========================================
   USUARIOS
   ========================================== */
function renderUsuarios(){
  apiGet('/api/usuarios').then(res=>{
    if(!res.data)return;
    DB_USUARIOS=res.data;
    const tbody=document.getElementById('usuariosTableBody');
    if(!tbody)return;

    tbody.innerHTML=DB_USUARIOS.map(u=>{
      const id=u.USU_ID||u.id;
      const nombre=u.USU_NOMBRE||u.nombre||'-';
      const usuario=u.USU_USUARIO||u.usuario||'-';
      const rol=u.USU_ROL||u.rol||'-';
      const email=u.USU_EMAIL||u.email||'-';
      const activo=u.USU_ACTIVO||u.activo||'S';
      return '<tr>'+
        '<td>#'+id+'</td>'+
        '<td style="font-weight:500;">'+nombre+'</td>'+
        '<td>'+usuario+'</td>'+
        '<td>'+planBadge(rol)+'</td>'+
        '<td>'+email+'</td>'+
        '<td>'+(activo==='S'?statusBadge('activo'):statusBadge('inactivo'))+'</td>'+
        '<td><div style="display:flex;gap:4px;">'+
          '<button class="btn btn-ghost btn-sm" onclick="editarUsuario('+id+')" title="Editar"><i class="fas fa-pen" style="font-size:10px;"></i></button>'+
          '<button class="btn btn-ghost btn-sm" onclick="eliminarUsuario('+id+',\''+nombre.replace(/'/g,"\\'")+'\')" title="Eliminar" style="color:var(--danger,#ef4444);"><i class="fas fa-trash" style="font-size:10px;"></i></button>'+
        '</div></td></tr>';
    }).join('');
  }).catch(()=>showToast('Error cargando usuarios','error'));
}

function editarUsuario(id){
  const u=DB_USUARIOS.find(x=>(x.USU_ID||x.id)==id);
  if(!u)return showToast('Usuario no encontrado','error');
  const modal=document.getElementById('modalNuevoUsuario');
  if(!modal)return;
  const inputs=modal.querySelectorAll('input,select');
  inputs[0].value=u.USU_NOMBRE||'';
  inputs[1].value=u.USU_EMAIL||'';
  inputs[2].value=u.USU_ROL||'operacion';
  inputs[4].value='';
  inputs[5].value='';
  modal.setAttribute('data-editing',id);
  const hdr=modal.querySelector('.modal-header h3');
  if(hdr)hdr.textContent='Editar Usuario';
  const btn=modal.querySelector('.modal-footer .btn-primary');
  if(btn)btn.innerHTML='<i class="fas fa-save" style="font-size:10px;"></i> Actualizar';
  openModal('modalNuevoUsuario');
}

function saveUsuario(){
  const modal=document.getElementById('modalNuevoUsuario');
  if(!modal)return;
  const inputs=modal.querySelectorAll('input,select');
  const nombre=inputs[0].value.trim();
  const email=inputs[1].value.trim();
  const rol=inputs[2].value.toLowerCase();
  const password=inputs[4].value;
  const confirm=inputs[5].value;
  if(!nombre){showToast('Nombre requerido','error');return;}
  const editingId=modal.getAttribute('data-editing');
  const isEdit=editingId&&editingId!=='';
  if(!isEdit&&!password){showToast('Password requerido','error');return;}
  if(!isEdit&&password!==confirm){showToast('Passwords no coinciden','error');return;}
  const data={nombre:nombre,email:email,rol:rol};
  if(password)data.password=password;
  const promise=isEdit?apiPut('/api/usuarios/'+editingId,data):apiPost('/api/usuarios',data);
  promise.then(res=>{
    if(res.success){showToast(isEdit?'Usuario actualizado':'Usuario creado','success');closeModal('modalNuevoUsuario');modal.removeAttribute('data-editing');renderUsuarios();}
    else showToast(res.error||'Error al guardar','error');
  });
}
function eliminarUsuario(id,nombre){
  if(!confirm('Eliminar usuario "'+nombre+'"'))return;
  apiDelete('/api/usuarios/'+id).then(res=>{
    if(res.success){showToast('Usuario eliminado','success');renderUsuarios();}
    else showToast(res.error||'Error al eliminar','error');
  });
}

/* ==========================================
   AUDIT
   ========================================== */
function renderAudit(){
  apiGet('/api/audit?emp_id=1').then(res=>{
    if(!res.data)return;
    const tbody=document.getElementById('auditTableBody');
    if(!tbody)return;
    tbody.innerHTML=res.data.slice(0,30).map(a=>{
      const ts=a.AUD_FECHA||a.timestamp||'-';
      const usuario=a.AUD_USUARIO||a.usuario||'-';
      const accion=a.AUD_ACCION||a.accion||'-';
      const entidad=a.AUD_ENTIDAD||a.entidad||'-';
      const detalle=a.AUD_DETALLE||a.detalle||'-';
      return '<tr>'+
        '<td style="font-size:12px;color:var(--text-muted);white-space:nowrap;">'+ts+'</td>'+
        '<td style="font-weight:500;">'+usuario+'</td>'+
        '<td>'+statusBadge(accion.toLowerCase())+'</td>'+
        '<td>'+entidad+'</td>'+
        '<td style="max-width:250px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">'+detalle+'</td>'+
        '</tr>';
    }).join('');
  }).catch(()=>{});
}

/* ==========================================
   CHARTS
   ========================================== */
function initCharts(){
  if(pedidosChart)pedidosChart.destroy();
  if(revenueChart)revenueChart.destroy();
  const t=getTheme();
  const gridC=t==='dark'?'rgba(26,26,34,0.8)':'rgba(200,200,210,0.3)';
  const tickC=t==='dark'?'#4a4a5a':'#6b7280';

  pedidosChart=new Chart(document.getElementById('chartPedidos'),{type:'line',data:{labels:['Lun','Mar','Mie','Jue','Vie','Sab','Dom'],datasets:[{label:'Pedidos',data:[45,52,38,65,58,72,48],borderColor:'#6366f1',backgroundColor:'rgba(99,102,241,0.05)',fill:true,tension:.4,pointRadius:3,pointBackgroundColor:'#6366f1',borderWidth:2}]},options:{responsive:true,plugins:{legend:{display:false}},scales:{x:{grid:{color:gridC},ticks:{color:tickC,font:{size:10}}},y:{grid:{color:gridC},ticks:{color:tickC,font:{size:10}}}}}});
  revenueChart=new Chart(document.getElementById('chartRevenue'),{type:'bar',data:{labels:['Lun','Mar','Mie','Jue','Vie','Sab','Dom'],datasets:[{label:'Revenue',data:[12400,15600,9800,18200,14300,21500,11200],backgroundColor:'rgba(245,158,11,0.15)',borderColor:'rgba(245,158,11,0.4)',borderWidth:1,borderRadius:4}]},options:{responsive:true,plugins:{legend:{display:false}},scales:{x:{grid:{display:false},ticks:{color:tickC,font:{size:10}}},y:{grid:{color:gridC},ticks:{color:tickC,font:{size:10},callback:v=>'$'+(v/1000)+'k'}}}}});
}

function initCancelChart(){
  if(cancelChart)cancelChart.destroy();
  const t=getTheme();
  const gridC=t==='dark'?'rgba(26,26,34,0.8)':'rgba(200,200,210,0.3)';
  const tickC=t==='dark'?'#4a4a5a':'#6b7280';
  cancelChart=new Chart(document.getElementById('chartCancelaciones'),{type:'bar',data:{labels:['Ene','Feb','Mar','Abr','May','Jun','Jul'],datasets:[{label:'Cancelaciones',data:[32,28,41,35,52,38,47],backgroundColor:'rgba(239,68,68,0.15)',borderColor:'rgba(239,68,68,0.4)',borderWidth:1,borderRadius:4}]},options:{responsive:true,plugins:{legend:{display:false}},scales:{x:{grid:{display:false},ticks:{color:tickC,font:{size:10}}},y:{grid:{color:gridC},ticks:{color:tickC,font:{size:10}}}}}});
}

/* MRR/Usage charts removed - canvas IDs don't exist in HTML */

/* ==========================================
   MAPS
   ========================================== */
function initDashboardMap(){
  if(dashboardMap)return;
  try{
    dashboardMap=L.map('dashboardMap',{zoomControl:false}).setView([19.4326,-99.1332],12);
    const t=getTheme();
    L.tileLayer(t==='dark'?'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png':'https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png',{attribution:''}).addTo(dashboardMap);
  }catch(e){}
}

function initDashboardMapFromChofres(){
  apiGet('/api/choferes?emp_id=1').then(res=>{
    if(!res.data||!dashboardMap)return;
    res.data.forEach(c=>{
      const lat=19.43+(Math.random()-0.5)*0.08;
      const lng=-99.13+(Math.random()-0.5)*0.08;
      const nombre=c.CHF_NOMBRE||c.nombre||'-';
      L.circleMarker([lat,lng],{radius:5,color:'#6366f1',fillColor:'#6366f1',fillOpacity:0.7}).addTo(dashboardMap).bindPopup('<b>'+nombre+'</b>');
    });
  }).catch(()=>{});
}

function initActivityFeed(){
  const el=document.getElementById('activityFeed');
  if(!el)return;
  const acts=[
    {time:'Hace 5 min',text:'Carlos Lopez entrego PED-2840 en Polanco',dot:'green'},
    {time:'Hace 12 min',text:'Nuevo pedido PED-2851 creado para Transporte MX',dot:''},
    {time:'Hace 25 min',text:'Maria Garcia inicio ruta zona Condesa',dot:'yellow'},
    {time:'Hace 40 min',text:'Factura FAC-003 timbrada - Rapido Express',dot:'green'},
    {time:'Hace 1 hr',text:'Ticket #1 abierto: Error en facturacion CFDI',dot:'red'}
  ];
  el.innerHTML=acts.map(a=>'<div style="display:flex;gap:12px;padding:10px 0;border-bottom:1px solid var(--border-primary);"><div class="activity-dot '+a.dot+'"></div><div style="flex:1;"><div style="font-size:12px;font-weight:400;">'+a.text+'</div><div style="font-size:10px;color:var(--text-muted);margin-top:2px;">'+a.time+'</div></div></div>').join('');
}

/* ==========================================
   ZONAS Y RUTAS
   ========================================== */
let currentServicio='EXPRESS';

function switchServicioTab(serv){
  currentServicio=serv;
  document.querySelectorAll('.servicio-tab').forEach(t=>{
    const isActive=t.getAttribute('data-servicio')===serv;
    t.style.background=isActive?'var(--accent)':'var(--bg-tertiary)';
    t.style.color=isActive?'#fff':'var(--text-secondary)';
    t.style.borderColor=isActive?'var(--accent)':'var(--border-primary)';
    t.classList.toggle('active',isActive);
  });
  document.querySelectorAll('.servicio-panel').forEach(p=>p.style.display='none');
  const panel=document.getElementById('panel-'+serv);
  if(panel)panel.style.display='block';
  calcularEjemploTarifa(serv);
}

function calcularEjemploTarifa(serv){
  const inputs=document.querySelectorAll('.tarifa-input[data-serv="'+serv+'"]');
  const vals={};
  inputs.forEach(inp=>{vals[inp.getAttribute('data-field')]=parseFloat(inp.value)||0;});
  const peso=5,km=10;
  const costo=vals.monto_base+(peso*vals.monto_por_kg)+(km*vals.monto_por_km);
  const total=Math.max(costo,vals.monto_minimo);
  const el=document.getElementById('ejemplo-'+serv);
  if(el)el.textContent='$'+total.toFixed(2);
}

function calcularEjemplo(){
  const peso=parseFloat(document.getElementById('test-peso').value)||1;
  const largo=parseFloat(document.getElementById('test-largo').value)||0;
  const ancho=parseFloat(document.getElementById('test-ancho').value)||0;
  const alto=parseFloat(document.getElementById('test-alto').value)||0;
  const dist=parseFloat(document.getElementById('test-distancia').value)||0;
  const valor=parseFloat(document.getElementById('test-valor').value)||0;
  const inputs=document.querySelectorAll('.tarifa-input[data-serv="'+currentServicio+'"]');
  const vals={};
  inputs.forEach(inp=>{vals[inp.getAttribute('data-field')]=parseFloat(inp.value)||0;});
  const pesoVol=(largo*ancho*alto)/5000;
  const pesoCobrar=Math.max(peso,pesoVol);
  const costoBase=vals.monto_base;
  const costoKg=pesoCobrar*vals.monto_por_kg;
  const costoKm=dist*vals.monto_por_km;
  const m3=(largo*ancho*alto)/1000000;
  const costoVol=(pesoVol>peso)?m3*(vals.monto_por_m3||0):0;
  const subtotal=costoBase+costoKg+costoKm+costoVol;
  const seguro=valor*(vals.seguro_pct||0)/100;
  const total=Math.max(subtotal+seguro,vals.monto_minimo);
  document.getElementById('res-peso-real').textContent=peso+' kg';
  document.getElementById('res-peso-vol').textContent=pesoVol.toFixed(2)+' kg';
  document.getElementById('res-base').textContent='$'+costoBase.toFixed(2);
  document.getElementById('res-peso').textContent='$'+costoKg.toFixed(2);
  document.getElementById('res-km').textContent='$'+costoKm.toFixed(2);
  document.getElementById('res-vol').textContent='$'+costoVol.toFixed(2);
  document.getElementById('res-seguro').textContent='$'+seguro.toFixed(2);
  document.getElementById('res-total').textContent='$'+total.toFixed(2);
  document.getElementById('cotizador-resultado').style.display='block';
}

function guardarNuevaZona(){
  const nombre=document.getElementById('zon-nombre').value.trim();
  if(!nombre){showToast('El nombre de la zona es requerido','error');return;}
  const tarifas=['EXPRESS','ESTANDAR','ECONOMICO'].map(serv=>{
    const inputs=document.querySelectorAll('.tarifa-input[data-serv="'+serv+'"]');
    const vals={};
    inputs.forEach(inp=>{vals[inp.getAttribute('data-field')]=parseFloat(inp.value)||0;});
    vals.servicio=serv;return vals;
  });
  const payload={
    nombre:nombre,descripcion:document.getElementById('zon-descripcion').value.trim(),
    color:document.getElementById('zon-color').value,
    radio_km:parseFloat(document.getElementById('zon-radio').value)||5,
    centro_lat:parseFloat(document.getElementById('zon-lat').value)||19.4326,
    centro_lng:parseFloat(document.getElementById('zon-lng').value)||-99.1332,
    tarifas:tarifas
  };
  const editingId=document.getElementById('modalNuevaZona').getAttribute('data-editing');
  const isEdit=editingId&&editingId!=='';
  const url=isEdit?'/api/zonas/'+editingId:'/api/zonas';
  const method=isEdit?apiPut:apiPost;
  method(url,payload).then(res=>{
    if(res.success){
      showToast(isEdit?'Zona actualizada':'Zona "'+nombre+'" creada con 3 tarifas','success');
      closeModal('modalNuevaZona');resetModalZona();loadZonas();
    }else showToast(res.error||'Error al guardar zona','error');
  }).catch(()=>showToast('Error de conexion','error'));
}

function loadZonas(){
  apiGet('/api/zonas?emp_id=1').then(res=>{
    if(res.success){DB_ZONAS=res.data;renderZonasMap();renderZonasList();}
  }).catch(()=>{
    DB_ZONAS=[];renderZonasMap();renderZonasList();
  });
}

function renderZonasMap(){
  if(!rutasMap){
    try{
      rutasMap=L.map('rutasMap').setView([19.4326,-99.1332],12);
      const tileUrl=getTheme()==='dark'?'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png':'https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png';
      L.tileLayer(tileUrl,{attribution:''}).addTo(rutasMap);
    }catch(e){return;}
  }
  rutasMap.invalidateSize();
  DB_ZONAS.forEach(z=>{
    const lat=parseFloat(z.ZON_CENTRO_LAT)||19.43;
    const lng=parseFloat(z.ZON_CENTRO_LNG)||-99.13;
    const radio=parseFloat(z.ZON_RADIO_KM)||5;
    const color=z.ZON_COLOR||'#6366f1';
    const tarifaBase=(z.tarifas&&z.tarifas.length>0)?z.tarifas.find(t=>t.ZTA_SERVICIO==='ESTANDAR')||z.tarifas[0]:null;
    const precio=tarifaBase?'$'+parseFloat(tarifaBase.ZTA_MONTO_BASE||0).toFixed(0):'-';
    L.circle([lat,lng],{radius:radio*1000,color:color,fillColor:color,fillOpacity:0.1,weight:2}).addTo(rutasMap).bindPopup('<b>'+z.ZON_NOMBRE+'</b><br>Radio: '+radio+'km<br>Tarifa base: '+precio);
  });
}

function renderZonasList(){
  const container=document.getElementById('zonasList');
  if(!container)return;
  if(DB_ZONAS.length===0){container.innerHTML='<div style="text-align:center;padding:20px;color:var(--text-muted);font-size:12px;">No hay zonas configuradas</div>';return;}
  container.innerHTML=DB_ZONAS.map(z=>{
    const tarifa=(z.tarifas&&z.tarifas.length>0)?z.tarifas.find(t=>t.ZTA_SERVICIO==='ESTANDAR')||z.tarifas[0]:null;
    const precio=tarifa?'$'+parseFloat(tarifa.ZTA_MONTO_BASE||0).toFixed(0):'-';
    const servicios=(z.tarifas||[]).map(t=>'<span style="font-size:9px;padding:2px 6px;border-radius:4px;background:var(--bg-tertiary);border:1px solid var(--border-primary);color:var(--text-muted);">'+t.ZTA_SERVICIO+' $'+parseFloat(t.ZTA_MONTO_BASE||0).toFixed(0)+'</span>').join(' ');
    return '<div style="display:flex;justify-content:space-between;align-items:center;padding:12px 0;border-bottom:1px solid var(--border-primary);">'+
      '<div style="display:flex;align-items:center;gap:10px;flex:1;min-width:0;">'+
        '<div style="width:10px;height:10px;border-radius:50%;background:'+z.ZON_COLOR+';flex-shrink:0;"></div>'+
        '<div style="min-width:0;">'+
          '<div style="font-size:12px;font-weight:500;">'+z.ZON_NOMBRE+'</div>'+
          '<div style="font-size:10px;color:var(--text-muted);">Radio: '+z.ZON_RADIO_KM+'km</div>'+
          '<div style="margin-top:4px;display:flex;gap:4px;flex-wrap:wrap;">'+servicios+'</div>'+
        '</div>'+
      '</div>'+
      '<div style="text-align:right;display:flex;align-items:center;gap:12px;">'+
        '<div><div style="font-size:14px;font-weight:600;color:var(--text-primary);">'+precio+'</div><div style="font-size:9px;color:var(--text-muted);">base envio</div></div>'+
        '<div style="display:flex;gap:4px;">'+
          '<button class="btn btn-ghost btn-sm" onclick="editarZona('+z.ZON_ID+')" title="Editar" style="padding:4px 8px;"><i class="fas fa-pen" style="font-size:10px;"></i></button>'+
          '<button class="btn btn-ghost btn-sm" onclick="eliminarZona('+z.ZON_ID+',\''+z.ZON_NOMBRE.replace(/'/g,"\\'")+'\')" title="Eliminar" style="padding:4px 8px;color:var(--danger,#ef4444);"><i class="fas fa-trash" style="font-size:10px;"></i></button>'+
        '</div>'+
      '</div></div>';
  }).join('');
}

function editarZona(zonId){
  const zona=DB_ZONAS.find(z=>z.ZON_ID==zonId);
  if(!zona){showToast('Zona no encontrada','error');return;}
  document.getElementById('zon-nombre').value=zona.ZON_NOMBRE||'';
  document.getElementById('zon-descripcion').value=zona.ZON_DESCRIPCION||'';
  document.getElementById('zon-color').value=zona.ZON_COLOR||'#6366f1';
  document.getElementById('zon-color-hex').textContent=zona.ZON_COLOR||'#6366f1';
  ['EXPRESS','ESTANDAR','ECONOMICO'].forEach(serv=>{
    const t=(zona.tarifas||[]).find(x=>x.ZTA_SERVICIO===serv);
    document.querySelectorAll('.tarifa-input[data-serv="'+serv+'"]').forEach(inp=>{
      const field=inp.getAttribute('data-field');
      if(t&&t[field]!==undefined&&t[field]!==null)inp.value=t[field];
    });
    calcularEjemploTarifa(serv);
  });
  document.getElementById('modalNuevaZona').setAttribute('data-editing',zonId);
  const hdr=document.querySelector('#modalNuevaZona .modal-header h3');
  if(hdr)hdr.innerHTML='<i class="fas fa-edit" style="margin-right:8px;color:var(--accent);"></i> Editar Zona: '+zona.ZON_NOMBRE;
  const btn=document.querySelector('#modalNuevaZona .modal-footer .btn-primary');
  if(btn)btn.innerHTML='<i class="fas fa-save" style="font-size:10px;"></i> Actualizar Zona';
  switchServicioTab('EXPRESS');
  openModal('modalNuevaZona');
  setTimeout(()=>{
    initZonaPickerMap();
    const lat=parseFloat(zona.ZON_CENTRO_LAT)||19.4326;
    const lng=parseFloat(zona.ZON_CENTRO_LNG)||-99.1332;
    const radio=parseFloat(zona.ZON_RADIO_KM)||5;
    zonaPickerMap.setView([lat,lng],15);
    zonaPickerMarker.setLatLng([lat,lng]);
    actualizarCirculoZona(lat,lng,radio);
    actualizarUbicacionZona(lat,lng);
  },300);
}

function eliminarZona(zonId,nombre){
  if(!confirm('Eliminar la zona "'+nombre+'"?\n\nSe eliminaran todas sus tarifas.'))return;
  apiDelete('/api/zonas/'+zonId).then(res=>{
    if(res.success){showToast('Zona "'+nombre+'" eliminada','success');loadZonas();}
    else showToast(res.error||'Error al eliminar','error');
  }).catch(()=>showToast('Error de conexion','error'));
}

function resetModalZona(){
  document.getElementById('modalNuevaZona').removeAttribute('data-editing');
  const hdr=document.querySelector('#modalNuevaZona .modal-header h3');
  if(hdr)hdr.innerHTML='<i class="fas fa-map-marked-alt" style="margin-right:8px;color:var(--accent);"></i> Nueva Zona de Cobertura';
  const btn=document.querySelector('#modalNuevaZona .modal-footer .btn-primary');
  if(btn)btn.innerHTML='<i class="fas fa-save" style="font-size:10px;"></i> Guardar Zona';
  document.getElementById('zon-nombre').value='';
  document.getElementById('zon-descripcion').value='';
  document.getElementById('zon-color').value='#6366f1';
  document.getElementById('zon-color-hex').textContent='#6366f1';
  document.getElementById('zon-direccion').value='';
  document.getElementById('zon-direccion-resultado').style.display='none';
  document.getElementById('zon-lat').value=19.4326;
  document.getElementById('zon-lng').value=-99.1332;
  document.getElementById('zon-radio').value=5;
  ['EXPRESS','ESTANDAR','ECONOMICO'].forEach(serv=>calcularEjemploTarifa(serv));
  switchServicioTab('EXPRESS');
  setTimeout(()=>{
    initZonaPickerMap();
    if(zonaPickerMap&&zonaPickerMarker){
      zonaPickerMap.setView([19.4326,-99.1332],12);
      zonaPickerMarker.setLatLng([19.4326,-99.1332]);
      actualizarCirculoZona(19.4326,-99.1332,5);
    }
  },200);
}

function initRutasMap(){loadZonas();}

/* ==========================================
   MAPA PICKER (Buscador de direccion)
   ========================================== */
let zonaPickerMap=null,zonaPickerMarker=null,zonaPickerCircle=null;

function initZonaPickerMap(){
  if(zonaPickerMap){zonaPickerMap.invalidateSize();return;}
  try{
    const isDark=getTheme()==='dark';
    const tileUrl=isDark?'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png':'https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png';
    zonaPickerMap=L.map('zon-map-picker',{zoomControl:false}).setView([19.4326,-99.1332],12);
    L.tileLayer(tileUrl,{attribution:''}).addTo(zonaPickerMap);
    L.control.zoom({position:'topright'}).addTo(zonaPickerMap);
    zonaPickerMarker=L.marker([19.4326,-99.1332],{draggable:true}).addTo(zonaPickerMap);
    const radio=parseFloat(document.getElementById('zon-radio').value)||5;
    zonaPickerCircle=L.circle([19.4326,-99.1332],{radius:radio*1000,color:'#6366f1',fillColor:'#6366f1',fillOpacity:0.08,weight:2,dashArray:'5,5'}).addTo(zonaPickerMap);
    zonaPickerMarker.on('dragend',e=>{const pos=e.target.getLatLng();actualizarUbicacionZona(pos.lat,pos.lng);});
    zonaPickerMap.on('click',e=>{zonaPickerMarker.setLatLng(e.latlng);actualizarUbicacionZona(e.latlng.lat,e.latlng.lng);});
    document.getElementById('zon-radio').addEventListener('input',function(){if(zonaPickerMarker){const pos=zonaPickerMarker.getLatLng();actualizarCirculoZona(pos.lat,pos.lng,parseFloat(this.value)||5);}});
  }catch(e){console.warn('Map picker error:',e);}
}

function actualizarUbicacionZona(lat,lng){
  document.getElementById('zon-lat').value=lat.toFixed(6);
  document.getElementById('zon-lng').value=lng.toFixed(6);
  const radio=parseFloat(document.getElementById('zon-radio').value)||5;
  actualizarCirculoZona(lat,lng,radio);
  const color=document.getElementById('zon-color').value||'#6366f1';
  if(zonaPickerMarker){
    zonaPickerMarker.setIcon(L.divIcon({className:'',html:'<div style="width:24px;height:24px;background:'+color+';border:3px solid #fff;border-radius:50%;box-shadow:0 2px 6px rgba(0,0,0,0.4);"></div>',iconSize:[24,24],iconAnchor:[12,12]}));
  }
  reverseGeocode(lat,lng);
}

function actualizarCirculoZona(lat,lng,radio){if(zonaPickerCircle){zonaPickerCircle.setLatLng([lat,lng]);zonaPickerCircle.setRadius(radio*1000);}}

function reverseGeocode(lat,lng){
  const el=document.getElementById('zon-direccion-resultado');
  fetch('https://nominatim.openstreetmap.org/reverse?format=json&lat='+lat+'&lon='+lng+'&addressdetails=1&accept-language=es',{headers:{'User-Agent':'LastMilePlatform/1.0'}})
  .then(r=>r.json()).then(data=>{if(data.display_name){el.textContent=data.display_name;el.style.display='block';el.style.color='var(--accent)';}}).catch(()=>{});
}

function buscarDireccion(){
  const query=document.getElementById('zon-direccion').value.trim();
  if(!query){showToast('Escribe una direccion para buscar','error');return;}
  fetch('https://nominatim.openstreetmap.org/search?format=json&q='+encodeURIComponent(query)+'&limit=1&accept-language=es',{headers:{'User-Agent':'LastMilePlatform/1.0'}})
  .then(r=>r.json()).then(results=>{
    if(results.length===0){showToast('Direccion no encontrada. Intenta con mas detalle.','error');return;}
    const r=results[0];const lat=parseFloat(r.lat);const lng=parseFloat(r.lon);
    zonaPickerMap.setView([lat,lng],15);zonaPickerMarker.setLatLng([lat,lng]);
    actualizarUbicacionZona(lat,lng);
    document.getElementById('zon-direccion-resultado').textContent=r.display_name;
    document.getElementById('zon-direccion-resultado').style.display='block';
    showToast('Direccion encontrada','success');
  }).catch(()=>showToast('Error al buscar direccion','error'));
}

/* ==========================================
   REFRESH ALL
   ========================================== */
function refreshData(){
  showToast('Actualizando datos...','info');
  setTimeout(()=>{
    loadDashboard();renderPedidos();renderChoferes();renderVehiculos();
    renderClientes();renderCFDI();renderPagos();loadBilling();renderUsuarios();renderAudit();
    loadNotifications();
    showToast('Datos actualizados','success');
  },800);
}

/* ==========================================
   INIT
   ========================================== */
window.addEventListener('load',()=>{
  loadDashboard();renderPedidos();renderChoferes();renderVehiculos();
  renderClientes();renderCFDI();renderPagos();loadBilling();renderUsuarios();renderAudit();
  initCharts();initCancelChart();initActivityFeed();loadNotifications();
  setTimeout(()=>{initDashboardMap();initDashboardMapFromChofres();},500);
});

/* Theme toggle */
function toggleTheme(){ThemeManager.toggle();const icon=document.getElementById('theme-icon');if(icon)icon.className=getTheme()==='dark'?'fas fa-sun':'fas fa-moon'}

/* Re-render charts + maps on theme change */
window.addEventListener('themechange',()=>{
  const t=getTheme();
  const gridC=t==='dark'?'rgba(26,26,34,0.8)':'rgba(200,200,210,0.3)';
  const tickC=t==='dark'?'#4a4a5a':'#6b7280';
  if(pedidosChart){pedidosChart.options.scales.x.grid.color=gridC;pedidosChart.options.scales.y.grid.color=gridC;pedidosChart.options.scales.x.ticks.color=tickC;pedidosChart.options.scales.y.ticks.color=tickC;pedidosChart.update()}
  if(revenueChart){revenueChart.options.scales.x.grid.color=gridC;revenueChart.options.scales.y.grid.color=gridC;revenueChart.options.scales.x.ticks.color=tickC;revenueChart.options.scales.y.ticks.color=tickC;revenueChart.update()}
  if(dashboardMap){dashboardMap.eachLayer(l=>{if(l._url)l.setUrl(t==='dark'?'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png':'https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png')})}
  if(rutasMap){rutasMap.eachLayer(l=>{if(l._url)l.setUrl(t==='dark'?'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png':'https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png')})}
});

/* Color picker + tarifa input listeners */
document.addEventListener('DOMContentLoaded',()=>{
  const colorInput=document.getElementById('zon-color');
  if(colorInput){
    colorInput.addEventListener('input',()=>{
      const hex=document.getElementById('zon-color-hex');
      if(hex)hex.textContent=colorInput.value;
      const color=colorInput.value;
      if(zonaPickerMarker&&zonaPickerMap){
        zonaPickerMarker.setIcon(L.divIcon({className:'',html:'<div style="width:24px;height:24px;background:'+color+';border:3px solid #fff;border-radius:50%;box-shadow:0 2px 6px rgba(0,0,0,0.4);"></div>',iconSize:[24,24],iconAnchor:[12,12]}));
      }
      if(zonaPickerCircle)zonaPickerCircle.setStyle({color:color,fillColor:color});
    });
  }
  document.querySelectorAll('.tarifa-input').forEach(inp=>{
    inp.addEventListener('input',()=>{calcularEjemploTarifa(inp.getAttribute('data-serv'));});
  });
  const dirInput=document.getElementById('zon-direccion');
  if(dirInput){dirInput.addEventListener('keydown',e=>{if(e.key==='Enter'){e.preventDefault();buscarDireccion();}});}
  // Close modal on overlay click
  document.querySelectorAll('.modal-overlay').forEach(overlay=>{
    overlay.addEventListener('click',e=>{
      if(e.target===overlay){
        overlay.classList.remove('show');
        if(overlay.id==='modalNuevaZona')resetModalZona();
      }
  });
});

/* ==========================================
   NOTIFICATIONS
   ========================================== */
function toggleNotifDropdown(){
  const dd=document.getElementById('notif-dropdown');
  if(dd.style.display==='none'){dd.style.display='block';loadNotifications();}
  else dd.style.display='none';
}
document.addEventListener('click',e=>{
  const bell=document.getElementById('notif-bell');
  const dd=document.getElementById('notif-dropdown');
  if(bell&&dd&&!bell.contains(e.target))dd.style.display='none';
});

async function loadNotifications(){
  const list=document.getElementById('notif-list');
  const empty=document.getElementById('notif-empty');
  if(!list)return;
  list.innerHTML='<div style="padding:16px;text-align:center;font-size:12px;color:var(--text-muted);">Cargando...</div>';
  empty.style.display='none';
  const notifs=[];
  try{
    const [statsRes,pagosRes,chofRes]=await Promise.all([
      apiFetch('/api/pedidos/estadisticas'),
      apiFetch('/api/pagos'),
      apiFetch('/api/choferes')
    ]);
    if(statsRes&&statsRes.data){
      const d=statsRes.data;
      if(d.pendientes>0)notifs.push({icon:'fa-box',color:'var(--warning)',text:d.pendientes+' pedidos pendientes',section:'pedidos'});
      if(d.cancelados>0)notifs.push({icon:'fa-times-circle',color:'var(--danger)',text:d.cancelados+' pedidos cancelados',section:'pedidos'});
    }
    if(pagosRes&&pagosRes.data){
      const pend=pagosRes.data.filter(p=>(p.TRP_ESTATUS||p.PAG_ESTADO||'').toUpperCase()==='PENDIENTE');
      if(pend.length>0)notifs.push({icon:'fa-dollar-sign',color:'var(--warning)',text:pend.length+' pagos pendientes de cobro',section:'pagos'});
    }
    if(chofRes&&chofRes.data){
      const inact=chofRes.data.filter(c=>(c.CHO_ESTATUS||'').toUpperCase()==='INACTIVO');
      if(inact.length>0)notifs.push({icon:'fa-user-xmark',color:'var(--danger)',text:inact.length+' choferes inactivos',section:'choferes'});
    }
  }catch(e){console.warn('notif error',e);}

  const countEl=document.getElementById('notif-count');
  if(notifs.length>0){
    countEl.style.display='flex';
    countEl.textContent=notifs.length;
    list.innerHTML=notifs.map(n=>'<div class="notif-item" onclick="event.stopPropagation();document.getElementById(\'notif-dropdown\').style.display=\'none\';document.querySelector(\'[data-section='+n.section+']\').click();" style="padding:10px 16px;display:flex;align-items:center;gap:10px;cursor:pointer;border-bottom:1px solid var(--border-primary);transition:background 0.15s;font-size:12px;"><i class="fas '+n.icon+'" style="color:'+n.color+';font-size:13px;width:18px;text-align:center;"></i><span>'+n.text+'</span></div>').join('');
    list.querySelectorAll('.notif-item').forEach(el=>el.addEventListener('mouseenter',()=>el.style.background='var(--bg-card-hover)'));
    list.querySelectorAll('.notif-item').forEach(el=>el.addEventListener('mouseleave',()=>el.style.background=''));
    empty.style.display='none';
  }else{
    countEl.style.display='none';
    list.innerHTML='';
    empty.style.display='block';
  }
}

async function apiFetch(endpoint){
  try{
    const resp=await fetch(API_BASE+endpoint,{headers:HEADERS});
    if(!resp.ok)return null;
    return await resp.json();
  }catch(e){return null;}
}

function refreshNotifications(){loadNotifications();}
});
