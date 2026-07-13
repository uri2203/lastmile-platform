const API_BASE='http://localhost:5000';
const HEADERS={'X-Emp-Id':'1','Content-Type':'application/json'};
const DEMO={choferes:[{id:1,nombre:'Carlos Lopez',telefono:'55 1234 5678',vehiculo:'ABC-123 T-Max',entregas:12,rating:4.8,estado:'activo'},{id:2,nombre:'Maria Garcia',telefono:'55 2345 6789',vehiculo:'DEF-456 Van',entregas:9,rating:4.6,estado:'activo'},{id:3,nombre:'Juan Hernandez',telefono:'55 3456 7890',vehiculo:'GHI-789 Camioneta',entregas:15,rating:4.9,estado:'activo'},{id:4,nombre:'Ana Martinez',telefono:'55 4567 8901',vehiculo:'JKL-012 T-Max',entregas:8,rating:4.5,estado:'activo'},{id:5,nombre:'Pedro Sanchez',telefono:'55 5678 9012',vehiculo:'MNO-345 Van',entregas:11,rating:4.7,estado:'activo'},{id:6,nombre:'Laura Rodriguez',telefono:'55 6789 0123',vehiculo:'PQR-678 Auto',entregas:0,rating:4.3,estado:'inactivo'},{id:7,nombre:'Miguel Torres',telefono:'55 7890 1234',vehiculo:'STU-901 T-Max',entregas:14,rating:4.8,estado:'activo'},{id:8,nombre:'Sofia Flores',telefono:'55 8901 2345',vehiculo:'VWX-234 Camioneta',entregas:7,rating:4.4,estado:'activo'}],vehiculos:[{placa:'ABC-123',tipo:'Motocicleta',marca:'Yamaha T-Max 560',chofer:'Carlos Lopez',km:23450,ultimoServicio:'2026-06-15',estado:'activo'},{placa:'DEF-456',tipo:'Van',marca:'Nissan NV200',chofer:'Maria Garcia',km:45200,ultimoServicio:'2026-06-20',estado:'activo'},{placa:'GHI-789',tipo:'Camioneta',marca:'VW Saveiro',chofer:'Juan Hernandez',km:67800,ultimoServicio:'2026-05-10',estado:'mantenimiento'},{placa:'JKL-012',tipo:'Motocicleta',marca:'Honda ADV 160',chofer:'Ana Martinez',km:12300,ultimoServicio:'2026-07-01',estado:'activo'},{placa:'MNO-345',tipo:'Van',marca:'Ford Transit',chofer:'Pedro Sanchez',km:78900,ultimoServicio:'2026-06-28',estado:'activo'},{placa:'PQR-678',tipo:'Auto',marca:'Chevrolet Beat',chofer:'Laura Rodriguez',km:34500,ultimoServicio:'2026-04-20',estado:'inactivo'},{placa:'STU-901',tipo:'Motocicleta',marca:'Yamaha N-Max',chofer:'Miguel Torres',km:19800,ultimoServicio:'2026-07-05',estado:'activo'},{placa:'VWX-234',tipo:'Camioneta',marca:'Mitsubishi L200',chofer:'Sofia Flores',km:56700,ultimoServicio:'2026-06-10',estado:'activo'}],pedidos:[],clientes:[{id:1,empresa:'Express Logistics SA de CV',contacto:'Roberto Diaz',email:'roberto@expresslog.mx',plan:'Pro',pedidos:245,revenue:89500,estado:'activo'},{id:2,empresa:'Transporte MX SA de CV',contacto:'Fernanda Ruiz',email:'fernanda@transportemx.mx',plan:'Enterprise',pedidos:512,revenue:234000,estado:'activo'},{id:3,empresa:'Rapido Express',contacto:'Diego Morales',email:'diego@rapido.mx',plan:'Starter',pedidos:87,revenue:23400,estado:'activo'},{id:4,empresa:'Logistica Norte SA',contacto:'Patricia Vargas',email:'patricia@lognorte.mx',plan:'Pro',pedidos:178,revenue:67200,estado:'activo'},{id:5,empresa:'Distribuidora Central',contacto:'Javier Mendoza',email:'javier@discentral.mx',plan:'Enterprise',pedidos:389,revenue:156800,estado:'activo'},{id:6,empresa:'Envios Rapidos MX',contacto:'Camila Ortiz',email:'camila@enviosrap.mx',plan:'Starter',pedidos:45,revenue:12300,estado:'inactivo'}],facturas:[{folio:'FAC-001',uuid:'a1b2c3d4-e5f6-7890-abcd-ef1234567890',cliente:'Express Logistics',rfc:'ELO970101XYZ',importe:15230,fecha:'2026-07-01',estado:'timbrada'},{folio:'FAC-002',uuid:'b2c3d4e5-f6a7-8901-bcde-f12345678901',cliente:'Transporte MX',rfc:'TMX880202ABC',importe:34500,fecha:'2026-07-02',estado:'timbrada'},{folio:'FAC-003',uuid:'',cliente:'Rapido Express',rfc:'REX950303DEF',importe:8900,fecha:'2026-07-03',estado:'pendiente'},{folio:'FAC-004',uuid:'d4e5f6a7-b8c9-0123-cdef-234567890123',cliente:'Logistica Norte',rfc:'LNO900404GHI',importe:22100,fecha:'2026-07-04',estado:'timbrada'},{folio:'FAC-005',uuid:'',cliente:'Express Logistics',rfc:'ELO970101XYZ',importe:12800,fecha:'2026-07-05',estado:'cancelada'}],pagos:[{id:1,cliente:'Express Logistics',monto:15230,metodo:'Transferencia',referencia:'REF-2026-001',fecha:'2026-07-01',estado:'completado'},{id:2,cliente:'Transporte MX',monto:34500,metodo:'Transferencia',referencia:'REF-2026-002',fecha:'2026-07-02',estado:'completado'},{id:3,cliente:'Rapido Express',monto:8900,metodo:'Efectivo',referencia:'REF-2026-003',fecha:'2026-07-03',estado:'pendiente'},{id:4,cliente:'Logistica Norte',monto:22100,metodo:'Transferencia',referencia:'REF-2026-004',fecha:'2026-07-04',estado:'completado'},{id:5,cliente:'Distribuidora Central',monto:45000,metodo:'Efectivo',referencia:'REF-2026-005',fecha:'2026-07-05',estado:'completado'},{id:6,cliente:'Express Logistics',monto:12800,metodo:'Transferencia',referencia:'REF-2026-006',fecha:'2026-07-06',estado:'pendiente'}],usuarios:[{id:1,nombre:'Admin Principal',email:'admin@lastmile.mx',rol:'Admin',tenant:'Sistema',estado:'activo',ultimoAcceso:'2026-07-08 09:15'},{id:2,nombre:'Operador Ana',email:'ana@lastmile.mx',rol:'Operador',tenant:'Express Logistics',estado:'activo',ultimoAcceso:'2026-07-08 08:30'},{id:3,nombre:'Carlos Lopez',email:'carlos@lastmile.mx',rol:'Chofer',tenant:'Express Logistics',estado:'activo',ultimoAcceso:'2026-07-08 07:00'},{id:4,nombre:'Roberto Diaz',email:'roberto@expresslog.mx',rol:'Cliente',tenant:'Express Logistics',estado:'activo',ultimoAcceso:'2026-07-07 16:45'},{id:5,nombre:'Operador Miguel',email:'miguel@lastmile.mx',rol:'Operador',tenant:'Transporte MX',estado:'activo',ultimoAcceso:'2026-07-08 07:45'},{id:6,nombre:'Fernanda Ruiz',email:'fernanda@transportemx.mx',rol:'Cliente',tenant:'Transporte MX',estado:'activo',ultimoAcceso:'2026-07-07 14:20'}],tickets:[{id:1,asunto:'Error en facturacion CFDI',cliente:'Express Logistics',prioridad:'alta',estado:'abierto',asignado:'Admin',creado:'2026-07-08 10:30'},{id:2,asunto:'GPS no reporta ubicacion',cliente:'Transporte MX',prioridad:'critica',estado:'en_proceso',asignado:'Soporte T1',creado:'2026-07-07 14:20'},{id:3,asunto:'Solicitud acceso API',cliente:'Rapido Express',prioridad:'baja',estado:'resuelto',asignado:'Admin',creado:'2026-07-05 09:00'},{id:4,asunto:'Error al generar reporte',cliente:'Logistica Norte',prioridad:'media',estado:'en_proceso',asignado:'Soporte T1',creado:'2026-07-06 11:15'},{id:5,asunto:'Cobertura zona norte',cliente:'Distribuidora Central',prioridad:'media',estado:'abierto',asignado:'Admin',creado:'2026-07-08 08:00'}],audit:[{timestamp:'2026-07-08 09:15:32',usuario:'Admin',accion:'LOGIN',entidad:'Sistema',detalle:'Sesion iniciada Chrome/Win11',ip:'192.168.1.100'},{timestamp:'2026-07-08 09:12:18',usuario:'Operador Ana',accion:'UPDATE',entidad:'Pedido',detalle:'PED-2847 cambio a En Transito',ip:'192.168.1.101'},{timestamp:'2026-07-08 09:08:45',usuario:'Carlos Lopez',accion:'UPDATE',entidad:'Pedido',detalle:'Entrega confirmada PED-2840',ip:'10.0.0.55'},{timestamp:'2026-07-08 08:55:02',usuario:'Admin',accion:'CREATE',entidad:'Chofer',detalle:'Nuevo chofer: Sofia Flores',ip:'192.168.1.100'},{timestamp:'2026-07-08 08:40:17',usuario:'Operador Miguel',accion:'CREATE',entidad:'Pedido',detalle:'PED-2851 creado para Transporte MX',ip:'192.168.1.102'},{timestamp:'2026-07-08 08:30:00',usuario:'Sistema',accion:'SYSTEM',entidad:'Backup',detalle:'Backup automatico completado',ip:'127.0.0.1'},{timestamp:'2026-07-07 17:45:22',usuario:'Admin',accion:'UPDATE',entidad:'Config',detalle:'Politica cancelacion actualizada',ip:'192.168.1.100'},{timestamp:'2026-07-07 16:30:11',usuario:'Roberto Diaz',accion:'LOGIN',entidad:'Sistema',detalle:'Sesion Safari/MacOS',ip:'200.55.12.34'},{timestamp:'2026-07-07 15:20:05',usuario:'Admin',accion:'DELETE',entidad:'Pedido',detalle:'PED-2790 cancelado',ip:'192.168.1.100'},{timestamp:'2026-07-07 14:10:33',usuario:'Operador Ana',accion:'UPDATE',entidad:'Chofer',detalle:'Pedro Sanchez actualizado',ip:'192.168.1.101'}],zonas:[{nombre:'Centro Historico',tarifa:35,radio:3,color:'#6366f1'},{nombre:'Polanco / Reforma',tarifa:45,radio:4,color:'#10b981'},{nombre:'Roma / Condesa',tarifa:40,radio:3.5,color:'#f59e0b'},{nombre:'Coyoacan / San Angel',tarifa:50,radio:5,color:'#8b5cf6'},{nombre:'Santa Fe / Cuajimalpa',tarifa:60,radio:6,color:'#ef4444'},{nombre:'Del Valle / Narvarte',tarifa:42,radio:3,color:'#06b6d4'},{nombre:'Escandon / Tacubaya',tarifa:38,radio:2.5,color:'#ec4899'}]};
const statuses=['pendiente','transito','entregado','cancelado','fallido'];
const clients=['Express Logistics','Transporte MX','Rapido Express','Logistica Norte','Distribuidora Central'];
const drivers=['Carlos Lopez','Maria Garcia','Juan Hernandez','Ana Martinez','Pedro Sanchez'];
const colonias=['Polanco','Roma Norte','Condesa','Coyoacan','San Angel','Santa Fe','Centro','Juarez','Escandon','Del Valle'];
const calles=['Av. Reforma','Calle Durango','Insurgentes Sur','Paseo de la Reforma','Av. Patriotismo','Calle Ometeotl'];
for(let i=1;i<=85;i++){const d=new Date();d.setDate(d.getDate()-Math.floor(Math.random()*30));DEMO.pedidos.push({id:i,folio:'PED-'+(2770+i),cliente:clients[Math.floor(Math.random()*clients.length)],destino:calles[Math.floor(Math.random()*calles.length)]+' #'+(Math.floor(Math.random()*500)+1)+', '+colonias[Math.floor(Math.random()*colonias.length)],chofer:drivers[Math.floor(Math.random()*drivers.length)],estado:statuses[Math.floor(Math.random()*statuses.length)],fecha:d.toISOString().split('T')[0],total:Math.floor(Math.random()*500)+30,tenantId:Math.floor(Math.random()*3)+1})}
document.querySelectorAll('.nav-item[data-section]').forEach(item=>{item.addEventListener('click',function(){const sec=this.getAttribute('data-section');document.querySelectorAll('.section').forEach(s=>s.classList.remove('active'));document.querySelectorAll('.nav-item').forEach(n=>n.classList.remove('active'));document.getElementById('section-'+sec).classList.add('active');this.classList.add('active');if(sec==='rutas')setTimeout(initRutasMap,100)})});
function toggleSidebar(){document.getElementById('sidebar').classList.toggle('collapsed');document.getElementById('mainContent').classList.toggle('expanded')}
function openModal(id){document.getElementById(id).classList.add('show')}
function closeModal(id){document.getElementById(id).classList.remove('show')}
document.querySelectorAll('.modal-overlay').forEach(m=>{m.addEventListener('click',e=>{if(e.target===m)m.classList.remove('show')})});
function showToast(msg,type='info'){const c=document.getElementById('toastContainer');const t=document.createElement('div');t.className='toast toast-'+type;t.innerHTML='<i class="fas fa-'+(type==='success'?'check-circle':type==='error'?'times-circle':'info-circle')+'"></i> '+msg;c.appendChild(t);setTimeout(()=>t.remove(),4000)}
function formatCurrency(n){return '$'+n.toLocaleString('es-MX')}
function statusBadge(s){const m={pendiente:'badge-info',transito:'badge-warning',entregado:'badge-success',cancelado:'badge-danger',fallido:'badge-danger',activo:'badge-success',inactivo:'badge-gray',mantenimiento:'badge-warning',timbrada:'badge-success',completado:'badge-success',abierto:'badge-info',en_proceso:'badge-warning',resuelto:'badge-success',critica:'badge-danger',alta:'badge-danger',media:'badge-warning',baja:'badge-gray'};return '<span class="badge '+(m[s]||'badge-gray')+'">'+s+'</span>'}
function planBadge(p){const m={Starter:'badge-gray',Pro:'badge-info',Enterprise:'badge-warning'};return '<span class="badge '+(m[p]||'badge-gray')+'">'+p+'</span>'}
function renderPagination(id,total,page,perPage,fn){const pages=Math.ceil(total/perPage);let h='';for(let i=1;i<=Math.min(pages,7);i++)h+='<button class="'+(i===page?'active':'')+'" onclick="'+fn+'('+i+')">'+i+'</button>';document.getElementById(id).innerHTML=h}
let pedidosChart,revenueChart,dashboardMap,rutasMap,mrrChart,usageChart,cancelChart;
function loadDashboard(){document.getElementById('kpi-pedidos').textContent=DEMO.pedidos.length;const ent=DEMO.pedidos.filter(p=>p.estado==='entregado').length;document.getElementById('kpi-entregas').textContent=ent;document.getElementById('kpi-fallidos').textContent=DEMO.pedidos.filter(p=>p.estado==='fallido'||p.estado==='cancelado').length;document.getElementById('kpi-revenue').textContent=formatCurrency(DEMO.pedidos.reduce((a,p)=>a+p.total,0));document.getElementById('kpi-choferes').textContent=DEMO.choferes.filter(c=>c.estado==='activo').length;document.getElementById('kpi-tiempo').textContent='34m';initCharts();loadActivityFeed()}
function initCharts(){if(pedidosChart)pedidosChart.destroy();if(revenueChart)revenueChart.destroy();pedidosChart=new Chart(document.getElementById('chartPedidos'),{type:'line',data:{labels:['Lun','Mar','Mie','Jue','Vie','Sab','Dom'],datasets:[{label:'Pedidos',data:[45,52,38,65,58,72,48],borderColor:'#6366f1',backgroundColor:'rgba(99,102,241,0.05)',fill:true,tension:.4,pointRadius:3,pointBackgroundColor:'#6366f1',borderWidth:2}]},options:{responsive:true,plugins:{legend:{display:false}},scales:{x:{grid:{color:'rgba(26,26,34,0.8)'},ticks:{color:'#4a4a5a',font:{size:10}}},y:{grid:{color:'rgba(26,26,34,0.8)'},ticks:{color:'#4a4a5a',font:{size:10}}}}}});revenueChart=new Chart(document.getElementById('chartRevenue'),{type:'bar',data:{labels:['Lun','Mar','Mie','Jue','Vie','Sab','Dom'],datasets:[{label:'Revenue',data:[12400,15600,9800,18200,14300,21500,11200],backgroundColor:'rgba(245,158,11,0.15)',borderColor:'rgba(245,158,11,0.4)',borderWidth:1,borderRadius:4}]},options:{responsive:true,plugins:{legend:{display:false}},scales:{x:{grid:{display:false},ticks:{color:'#4a4a5a',font:{size:10}}},y:{grid:{color:'rgba(26,26,34,0.8)'},ticks:{color:'#4a4a5a',font:{size:10},callback:v=>'$'+(v/1000)+'k'}}}}})}
function initDashboardMap(){if(dashboardMap)return;try{dashboardMap=L.map('dashboardMap',{zoomControl:false}).setView([19.4326,-99.1332],12);L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',{attribution:''}).addTo(dashboardMap);DEMO.choferes.filter(c=>c.estado==='activo').forEach(c=>{const lat=19.43+(Math.random()-0.5)*0.08,lng=-99.13+(Math.random()-0.5)*0.08;L.circleMarker([lat,lng],{radius:5,color:'#6366f1',fillColor:'#6366f1',fillOpacity:0.7}).addTo(dashboardMap).bindPopup('<b>'+c.nombre+'</b><br>'+c.vehiculo+'<br>Entregas: '+c.entregas)})}catch(e){}}
function loadActivityFeed(){const acts=[{time:'Hace 5 min',text:'Carlos Lopez entrego PED-2840 en Polanco',dot:'green'},{time:'Hace 12 min',text:'Nuevo pedido PED-2851 creado para Transporte MX',dot:''},{time:'Hace 25 min',text:'Maria Garcia inicio ruta zona Condesa',dot:'yellow'},{time:'Hace 40 min',text:'Factura FAC-003 timbrada - Rapido Express',dot:'green'},{time:'Hace 1 hr',text:'Ticket #1 abierto: Error en facturacion CFDI',dot:'red'},{time:'Hace 1.5 hr',text:'Juan Hernandez entrega exitosa PED-2835',dot:'green'},{time:'Hace 2 hr',text:'Pedro Sanchez recogida en Santa Fe',dot:''}];document.getElementById('activityFeed').innerHTML=acts.map(a=>'<div style="display:flex;gap:12px;padding:10px 0;border-bottom:1px solid rgba(26,26,34,0.5);"><div class="activity-dot '+a.dot+'"></div><div style="flex:1;"><div style="font-size:12px;font-weight:400;">'+a.text+'</div><div style="font-size:10px;color:#4a4a5a;margin-top:2px;">'+a.time+'</div></div></div>').join('')}
let pedidosPage=1;const PEDIDOS_PER_PAGE=12;
function filterPedidos(status){document.getElementById('pedStatusFilter').value=status;renderPedidos()}
function renderPedidos(page){page=page||1;pedidosPage=page;const search=document.getElementById('pedSearch').value.toLowerCase();const status=document.getElementById('pedStatusFilter').value;const tenant=document.getElementById('pedTenantFilter').value;const date=document.getElementById('pedDateFilter').value;let filtered=DEMO.pedidos.filter(p=>{if(search&&!p.folio.toLowerCase().includes(search)&&!p.cliente.toLowerCase().includes(search))return false;if(status&&p.estado!==status)return false;if(tenant&&p.tenantId!==parseInt(tenant))return false;if(date&&p.fecha!==date)return false;return true});const start=(page-1)*PEDIDOS_PER_PAGE;const slice=filtered.slice(start,start+PEDIDOS_PER_PAGE);document.getElementById('pedidosTableBody').innerHTML=slice.map(p=>'<tr><td><span style="color:#6366f1;font-weight:500;">'+p.folio+'</span></td><td>'+p.cliente+'</td><td style="max-width:180px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">'+p.destino+'</td><td>'+p.chofer+'</td><td>'+statusBadge(p.estado)+'</td><td>'+p.fecha+'</td><td style="font-weight:500;">'+formatCurrency(p.total)+'</td><td><div style="display:flex;gap:4px;"><button class="btn btn-ghost btn-sm" onclick="viewPedido('+p.id+')" title="Ver"><i class="far fa-eye"></i></button><button class="btn btn-ghost btn-sm" onclick="cancelPedido('+p.id+')" title="Cancelar"><i class="fas fa-ban" style="color:#ef4444;font-size:10px;"></i></button></div></td></tr>').join('');document.getElementById('pedidosCount').textContent=filtered.length+' registros';['ped-total','ped-pendiente','ped-transito','ped-entregado','ped-cancelado'].forEach((id,i)=>{const counts=[DEMO.pedidos.length,DEMO.pedidos.filter(p=>p.estado==='pendiente').length,DEMO.pedidos.filter(p=>p.estado==='transito').length,DEMO.pedidos.filter(p=>p.estado==='entregado').length,DEMO.pedidos.filter(p=>p.estado==='cancelado').length];document.getElementById(id).textContent=counts[i]});renderPagination('pedidosPagination',filtered.length,page,PEDIDOS_PER_PAGE,'renderPedidos')}
function viewPedido(id){const p=DEMO.pedidos.find(x=>x.id===id);if(!p)return;const tl=[{time:p.fecha+' 08:00',text:'Pedido creado',icon:'plus-circle',color:'#6366f1'},{time:p.fecha+' 08:15',text:'Asignado a '+p.chofer,icon:'user-check',color:'#10b981'},{time:p.fecha+' 09:00',text:'En ruta de entrega',icon:'route',color:'#f59e0b'}];if(p.estado==='entregado')tl.push({time:p.fecha+' 10:30',text:'Entrega completada',icon:'check-circle',color:'#10b981'});if(p.estado==='cancelado')tl.push({time:p.fecha+' 09:30',text:'Pedido cancelado',icon:'times-circle',color:'#ef4444'});if(p.estado==='fallido')tl.push({time:p.fecha+' 10:00',text:'Intento fallido',icon:'exclamation-circle',color:'#ef4444'});document.getElementById('pedidoDetalleContent').innerHTML='<div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:20px;"><div><div style="font-size:10px;color:#4a4a5a;text-transform:uppercase;letter-spacing:0.5px;font-weight:500;">Folio</div><div style="font-size:16px;font-weight:600;color:#6366f1;">'+p.folio+'</div></div><div><div style="font-size:10px;color:#4a4a5a;text-transform:uppercase;letter-spacing:0.5px;font-weight:500;">Estado</div>'+statusBadge(p.estado)+'</div><div><div style="font-size:10px;color:#4a4a5a;text-transform:uppercase;letter-spacing:0.5px;font-weight:500;">Cliente</div><div style="font-size:13px;">'+p.cliente+'</div></div><div><div style="font-size:10px;color:#4a4a5a;text-transform:uppercase;letter-spacing:0.5px;font-weight:500;">Chofer</div><div style="font-size:13px;">'+p.chofer+'</div></div><div style="grid-column:1/-1;"><div style="font-size:10px;color:#4a4a5a;text-transform:uppercase;letter-spacing:0.5px;font-weight:500;">Destino</div><div style="font-size:13px;">'+p.destino+'</div></div><div><div style="font-size:10px;color:#4a4a5a;text-transform:uppercase;letter-spacing:0.5px;font-weight:500;">Total</div><div style="font-size:18px;font-weight:600;color:#e8e8ed;">'+formatCurrency(p.total)+'</div></div><div><div style="font-size:10px;color:#4a4a5a;text-transform:uppercase;letter-spacing:0.5px;font-weight:500;">Fecha</div><div style="font-size:13px;">'+p.fecha+'</div></div></div><h4 style="font-size:12px;font-weight:600;margin-bottom:12px;text-transform:uppercase;letter-spacing:0.5px;color:#4a4a5a;">Timeline</h4>'+tl.map(t=>'<div style="display:flex;gap:12px;padding:8px 0;border-bottom:1px solid rgba(26,26,34,0.5);"><div style="width:24px;height:24px;background:rgba(99,102,241,0.1);border-radius:50%;display:flex;align-items:center;justify-content:center;flex-shrink:0;"><i class="fas fa-'+t.icon+'" style="color:'+t.color+';font-size:10px;"></i></div><div style="flex:1;"><div style="font-size:12px;">'+t.text+'</div><div style="font-size:10px;color:#4a4a5a;margin-top:2px;">'+t.time+'</div></div></div>').join('');openModal('modalDetallePedido')}
function cancelPedido(id){const p=DEMO.pedidos.find(x=>x.id===id);if(!p)return;document.getElementById('penaltyAmount').textContent=(p.total*0.15).toFixed(2);openModal('modalCancelarPedido')}
function renderChoferes(){const ch=DEMO.choferes;document.getElementById('ch-activos').textContent=ch.filter(c=>c.estado==='activo').length;document.getElementById('ch-inactivos').textContent=ch.filter(c=>c.estado==='inactivo').length;document.getElementById('ch-rating').textContent=(ch.reduce((a,c)=>a+c.rating,0)/ch.length).toFixed(1);document.getElementById('ch-entregas-hoy').textContent=ch.reduce((a,c)=>a+c.entregas,0);document.getElementById('choferesTableBody').innerHTML=ch.map(c=>'<tr><td>#'+c.id+'</td><td style="font-weight:500;">'+c.nombre+'</td><td>'+c.telefono+'</td><td>'+c.vehiculo+'</td><td>'+c.entregas+'</td><td><span style="color:#f59e0b;"><i class="fas fa-star" style="font-size:10px;"></i></span> '+c.rating+'</td><td>'+statusBadge(c.estado)+'</td><td><div style="display:flex;gap:4px;"><button class="btn btn-ghost btn-sm"><i class="far fa-edit"></i></button><button class="btn btn-ghost btn-sm"><i class="far fa-eye"></i></button></div></td></tr>').join('')}
function renderVehiculos(){const vh=DEMO.vehiculos;document.getElementById('vh-activos').textContent=vh.filter(v=>v.estado==='activo').length;document.getElementById('vh-mant').textContent=vh.filter(v=>v.estado==='mantenimiento').length;document.getElementById('vh-inact').textContent=vh.filter(v=>v.estado==='inactivo').length;document.getElementById('vh-km').textContent=(vh.reduce((a,v)=>a+v.km,0)/1000).toFixed(0)+'k';document.getElementById('vehiculosTableBody').innerHTML=vh.map(v=>'<tr><td style="font-weight:500;color:#6366f1;">'+v.placa+'</td><td>'+v.tipo+'</td><td>'+v.marca+'</td><td>'+v.chofer+'</td><td>'+v.km.toLocaleString()+'</td><td>'+v.ultimoServicio+'</td><td>'+statusBadge(v.estado)+'</td><td><div style="display:flex;gap:4px;"><button class="btn btn-ghost btn-sm"><i class="far fa-edit"></i></button><button class="btn btn-ghost btn-sm"><i class="far fa-eye"></i></button></div></td></tr>').join('')}
/* ==========================================
   ZONAS Y RUTAS - Carga desde DB + CRUD
   ========================================== */
let DB_ZONAS = [];
let currentServicio = 'EXPRESS';

function switchServicioTab(serv) {
  currentServicio = serv;
  document.querySelectorAll('.servicio-tab').forEach(t => {
    const isActive = t.getAttribute('data-servicio') === serv;
    t.style.background = isActive ? 'var(--accent)' : 'var(--bg-tertiary)';
    t.style.color = isActive ? '#fff' : 'var(--text-secondary)';
    t.style.borderColor = isActive ? 'var(--accent)' : 'var(--border-primary)';
    t.classList.toggle('active', isActive);
  });
  document.querySelectorAll('.servicio-panel').forEach(p => p.style.display = 'none');
  const panel = document.getElementById('panel-' + serv);
  if (panel) panel.style.display = 'block';
  calcularEjemploTarifa(serv);
}

function calcularEjemploTarifa(serv) {
  const inputs = document.querySelectorAll('.tarifa-input[data-serv="' + serv + '"]');
  const vals = {};
  inputs.forEach(inp => { vals[inp.getAttribute('data-field')] = parseFloat(inp.value) || 0; });
  const peso = 5, km = 10;
  const costo = vals.monto_base + (peso * vals.monto_por_kg) + (km * vals.monto_por_km);
  const total = Math.max(costo, vals.monto_minimo);
  const el = document.getElementById('ejemplo-' + serv);
  if (el) el.textContent = '$' + total.toFixed(2);
}

function calcularEjemplo() {
  const peso = parseFloat(document.getElementById('test-peso').value) || 1;
  const largo = parseFloat(document.getElementById('test-largo').value) || 0;
  const ancho = parseFloat(document.getElementById('test-ancho').value) || 0;
  const alto = parseFloat(document.getElementById('test-alto').value) || 0;
  const dist = parseFloat(document.getElementById('test-distancia').value) || 0;
  const valor = parseFloat(document.getElementById('test-valor').value) || 0;

  const inputs = document.querySelectorAll('.tarifa-input[data-serv="' + currentServicio + '"]');
  const vals = {};
  inputs.forEach(inp => { vals[inp.getAttribute('data-field')] = parseFloat(inp.value) || 0; });

  const pesoVol = (largo * ancho * alto) / 5000;
  const pesoCobrar = Math.max(peso, pesoVol);
  const costoBase = vals.monto_base;
  const costoKg = pesoCobrar * vals.monto_por_kg;
  const costoKm = dist * vals.monto_por_km;
  const m3 = (largo * ancho * alto) / 1000000;
  const costoVol = (pesoVol > peso) ? m3 * (vals.monto_por_m3 || 0) : 0;
  const subtotal = costoBase + costoKg + costoKm + costoVol;
  const seguro = valor * (vals.seguro_pct || 0) / 100;
  const total = Math.max(subtotal + seguro, vals.monto_minimo);

  document.getElementById('res-peso-real').textContent = peso + ' kg';
  document.getElementById('res-peso-vol').textContent = pesoVol.toFixed(2) + ' kg';
  document.getElementById('res-base').textContent = '$' + costoBase.toFixed(2);
  document.getElementById('res-peso').textContent = '$' + costoKg.toFixed(2);
  document.getElementById('res-km').textContent = '$' + costoKm.toFixed(2);
  document.getElementById('res-vol').textContent = '$' + costoVol.toFixed(2);
  document.getElementById('res-seguro').textContent = '$' + seguro.toFixed(2);
  document.getElementById('res-total').textContent = '$' + total.toFixed(2);
  document.getElementById('cotizador-resultado').style.display = 'block';
}

function guardarNuevaZona() {
  const nombre = document.getElementById('zon-nombre').value.trim();
  if (!nombre) { showToast('El nombre de la zona es requerido', 'error'); return; }

  const tarifas = ['EXPRESS', 'ESTANDAR', 'ECONOMICO'].map(serv => {
    const inputs = document.querySelectorAll('.tarifa-input[data-serv="' + serv + '"]');
    const vals = {};
    inputs.forEach(inp => { vals[inp.getAttribute('data-field')] = parseFloat(inp.value) || 0; });
    vals.servicio = serv;
    return vals;
  });

  const payload = {
    nombre: nombre,
    descripcion: document.getElementById('zon-descripcion').value.trim(),
    color: document.getElementById('zon-color').value,
    radio_km: parseFloat(document.getElementById('zon-radio').value) || 5,
    centro_lat: parseFloat(document.getElementById('zon-lat').value) || 19.4326,
    centro_lng: parseFloat(document.getElementById('zon-lng').value) || -99.1332,
    tarifas: tarifas
  };

  fetch(API_BASE + '/api/zonas', {
    method: 'POST',
    headers: HEADERS,
    body: JSON.stringify(payload)
  }).then(r => r.json()).then(res => {
    if (res.success) {
      showToast('Zona "' + nombre + '" creada con 3 tarifas', 'success');
      closeModal('modalNuevaZona');
      document.getElementById('zon-nombre').value = '';
      document.getElementById('zon-descripcion').value = '';
      loadZonas();
    } else {
      showToast(res.error || 'Error al crear zona', 'error');
    }
  }).catch(() => showToast('Error de conexion', 'error'));
}

function loadZonas() {
  fetch(API_BASE + '/api/zonas', { headers: HEADERS })
    .then(r => r.json())
    .then(res => {
      if (res.success) {
        DB_ZONAS = res.data;
        renderZonasMap();
        renderZonasList();
      }
    }).catch(() => {
      // Fallback a DEMO si falla
      DB_ZONAS = DEMO.zonas.map((z, i) => ({
        ZON_ID: i + 1, ZON_NOMBRE: z.nombre, ZON_COLOR: z.color,
        ZON_RADIO_KM: z.radio, ZON_CENTRO_LAT: 19.43 + (Math.random()-0.5)*0.06,
        ZON_CENTRO_LNG: -99.13 + (Math.random()-0.5)*0.06,
        tarifas: [{ZTA_SERVICIO:'ESTANDAR', ZTA_MONTO_BASE: z.tarifa}]
      }));
      renderZonasMap();
      renderZonasList();
    });
}

function renderZonasMap() {
  if (!rutasMap) {
    try {
      rutasMap = L.map('rutasMap').setView([19.4326, -99.1332], 12);
      const tileUrl = ThemeManager.get() === 'dark'
        ? 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png'
        : 'https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png';
      L.tileLayer(tileUrl, { attribution: '' }).addTo(rutasMap);
    } catch(e) { return; }
  }
  rutasMap.invalidateSize();
  DB_ZONAS.forEach(z => {
    const lat = parseFloat(z.ZON_CENTRO_LAT) || 19.43;
    const lng = parseFloat(z.ZON_CENTRO_LNG) || -99.13;
    const radio = parseFloat(z.ZON_RADIO_KM) || 5;
    const color = z.ZON_COLOR || '#6366f1';
    const tarifaBase = (z.tarifas && z.tarifas.length > 0)
      ? z.tarifas.find(t => t.ZTA_SERVICIO === 'ESTANDAR') || z.tarifas[0]
      : null;
    const precio = tarifaBase ? '$' + parseFloat(tarifaBase.ZTA_MONTO_BASE || 0).toFixed(0) : '-';
    L.circle([lat, lng], {
      radius: radio * 1000, color: color, fillColor: color,
      fillOpacity: 0.1, weight: 2
    }).addTo(rutasMap).bindPopup(
      '<b>' + z.ZON_NOMBRE + '</b><br>Radio: ' + radio + 'km<br>Tarifa base: ' + precio
    );
  });
}

function renderZonasList() {
  const container = document.getElementById('zonasList');
  if (!container) return;
  if (DB_ZONAS.length === 0) {
    container.innerHTML = '<div style="text-align:center;padding:20px;color:var(--text-muted);font-size:12px;">No hay zonas configuradas</div>';
    return;
  }
  container.innerHTML = DB_ZONAS.map(z => {
    const tarifa = (z.tarifas && z.tarifas.length > 0)
      ? z.tarifas.find(t => t.ZTA_SERVICIO === 'ESTANDAR') || z.tarifas[0]
      : null;
    const precio = tarifa ? '$' + parseFloat(tarifa.ZTA_MONTO_BASE || 0).toFixed(0) : '-';
    const servicios = (z.tarifas || []).map(t =>
      '<span style="font-size:9px;padding:2px 6px;border-radius:4px;background:var(--bg-tertiary);border:1px solid var(--border-primary);color:var(--text-muted);">' + t.ZTA_SERVICIO + ' $' + parseFloat(t.ZTA_MONTO_BASE || 0).toFixed(0) + '</span>'
    ).join(' ');
    return '<div style="display:flex;justify-content:space-between;align-items:center;padding:12px 0;border-bottom:1px solid var(--border-primary);">' +
      '<div style="display:flex;align-items:center;gap:10px;">' +
        '<div style="width:10px;height:10px;border-radius:50%;background:' + z.ZON_COLOR + ';flex-shrink:0;"></div>' +
        '<div>' +
          '<div style="font-size:12px;font-weight:500;">' + z.ZON_NOMBRE + '</div>' +
          '<div style="font-size:10px;color:var(--text-muted);">Radio: ' + z.ZON_RADIO_KM + 'km</div>' +
          '<div style="margin-top:4px;display:flex;gap:4px;flex-wrap:wrap;">' + servicios + '</div>' +
        '</div>' +
      '</div>' +
      '<div style="text-align:right;">' +
        '<div style="font-size:14px;font-weight:600;color:var(--text-primary);">' + precio + '</div>' +
        '<div style="font-size:9px;color:var(--text-muted);">base envio</div>' +
      '</div>' +
    '</div>';
  }).join('');
}

function initRutasMap() {
  loadZonas();
}
function renderClientes(){document.getElementById('clientesTableBody').innerHTML=DEMO.clientes.map(c=>'<tr><td>#'+c.id+'</td><td style="font-weight:500;">'+c.empresa+'</td><td>'+c.contacto+'</td><td>'+c.email+'</td><td>'+planBadge(c.plan)+'</td><td>'+c.pedidos+'</td><td style="font-weight:500;color:#10b981;">'+formatCurrency(c.revenue)+'</td><td>'+statusBadge(c.estado)+'</td><td><div style="display:flex;gap:4px;"><button class="btn btn-ghost btn-sm"><i class="far fa-edit"></i></button><button class="btn btn-ghost btn-sm"><i class="far fa-eye"></i></button></div></td></tr>').join('')}
function renderCFDI(){const fc=DEMO.facturas;document.getElementById('cfdi-timbradas').textContent=fc.filter(f=>f.estado==='timbrada').length;document.getElementById('cfdi-pendientes').textContent=fc.filter(f=>f.estado==='pendiente').length;document.getElementById('cfdi-canceladas').textContent=fc.filter(f=>f.estado==='cancelada').length;document.getElementById('cfdi-total').textContent=formatCurrency(fc.filter(f=>f.estado==='timbrada').reduce((a,f)=>a+f.importe,0));document.getElementById('cfdiTableBody').innerHTML=fc.map(f=>'<tr><td style="font-weight:500;color:#6366f1;">'+f.folio+'</td><td style="font-size:11px;font-family:monospace;max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">'+(f.uuid||'Sin timbrar')+'</td><td>'+f.cliente+'</td><td>'+f.rfc+'</td><td style="font-weight:500;">'+formatCurrency(f.importe)+'</td><td>'+f.fecha+'</td><td>'+statusBadge(f.estado)+'</td><td><div style="display:flex;gap:4px;">'+(f.estado==='pendiente'?'<button class="btn btn-success btn-sm" onclick="showToast(\'Factura timbrada\',\'success\')"><i class="fas fa-stamp" style="font-size:10px;"></i></button>':'')+(f.estado==='timbrada'?'<button class="btn btn-danger btn-sm" onclick="showToast(\'Factura cancelada\',\'error\')"><i class="fas fa-ban" style="font-size:10px;"></i></button>':'')+'</div></td></tr>').join('')}
function renderPagos(){const pg=DEMO.pagos;const cobrado=pg.filter(p=>p.estado==='completado').reduce((a,p)=>a+p.monto,0);const pendiente=pg.filter(p=>p.estado==='pendiente').reduce((a,p)=>a+p.monto,0);const efectivo=pg.filter(p=>p.metodo==='Efectivo').reduce((a,p)=>a+p.monto,0);const transferencia=pg.filter(p=>p.metodo==='Transferencia').reduce((a,p)=>a+p.monto,0);document.getElementById('pag-cobrado').textContent=formatCurrency(cobrado);document.getElementById('pag-pendiente').textContent=formatCurrency(pendiente);document.getElementById('pag-efectivo').textContent=formatCurrency(efectivo);document.getElementById('pag-transferencia').textContent=formatCurrency(transferencia);document.getElementById('pagosTableBody').innerHTML=pg.map(p=>'<tr><td>#'+p.id+'</td><td>'+p.cliente+'</td><td style="font-weight:500;">'+formatCurrency(p.monto)+'</td><td>'+p.metodo+'</td><td style="font-family:monospace;font-size:11px;">'+p.referencia+'</td><td>'+p.fecha+'</td><td>'+statusBadge(p.estado)+'</td></tr>').join('')}
function initBillingCharts(){if(mrrChart)mrrChart.destroy();if(usageChart)usageChart.destroy();mrrChart=new Chart(document.getElementById('chartMRR'),{type:'line',data:{labels:['Ene','Feb','Mar','Abr','May','Jun','Jul'],datasets:[{label:'MRR',data:[28500,31200,33800,35100,38400,42000,44900],borderColor:'#6366f1',backgroundColor:'rgba(99,102,241,0.05)',fill:true,tension:.4,pointRadius:3,pointBackgroundColor:'#6366f1',borderWidth:2}]},options:{responsive:true,plugins:{legend:{display:false}},scales:{x:{grid:{color:'rgba(26,26,34,0.8)'},ticks:{color:'#4a4a5a',font:{size:10}}},y:{grid:{color:'rgba(26,26,34,0.8)'},ticks:{color:'#4a4a5a',font:{size:10},callback:v=>'$'+(v/1000)+'k'}}}}});usageChart=new Chart(document.getElementById('chartUsage'),{type:'doughnut',data:{labels:['Starter','Pro','Enterprise'],datasets:[{data:[12,28,8],backgroundColor:['#7a7a8a','#6366f1','#f59e0b'],borderWidth:0}]},options:{responsive:true,plugins:{legend:{position:'bottom',labels:{color:'#7a7a8a',padding:12,font:{size:11}}}}}})}
function renderBilling(){const bc=[{cliente:'Express Logistics',plan:'Pro',usados:245,limite:2000,facturacion:89500,estado:'activo'},{cliente:'Transporte MX',plan:'Enterprise',usados:512,limite:999999,facturacion:234000,estado:'activo'},{cliente:'Rapido Express',plan:'Starter',usados:87,limite:500,facturacion:23400,estado:'activo'},{cliente:'Logistica Norte',plan:'Pro',usados:178,limite:2000,facturacion:67200,estado:'activo'},{cliente:'Distribuidora Central',plan:'Enterprise',usados:389,limite:999999,facturacion:156800,estado:'activo'}];document.getElementById('billingTableBody').innerHTML=bc.map(b=>'<tr><td style="font-weight:500;">'+b.cliente+'</td><td>'+planBadge(b.plan)+'</td><td>'+b.usados+'</td><td>'+(b.limite>999?'Ilimitado':b.limite)+'</td><td style="font-weight:500;color:#10b981;">'+formatCurrency(b.facturacion)+'</td><td>'+statusBadge(b.estado)+'</td></tr>').join('');initBillingCharts()}
function initCancelChart(){if(cancelChart)cancelChart.destroy();cancelChart=new Chart(document.getElementById('chartCancelaciones'),{type:'bar',data:{labels:['Ene','Feb','Mar','Abr','May','Jun','Jul'],datasets:[{label:'Cancelaciones',data:[32,28,41,35,52,38,47],backgroundColor:'rgba(239,68,68,0.15)',borderColor:'rgba(239,68,68,0.4)',borderWidth:1,borderRadius:4}]},options:{responsive:true,plugins:{legend:{display:false}},scales:{x:{grid:{display:false},ticks:{color:'#4a4a5a',font:{size:10}}},y:{grid:{color:'rgba(26,26,34,0.8)'},ticks:{color:'#4a4a5a',font:{size:10}}}}}})}
function renderUsuarios(){document.getElementById('usuariosTableBody').innerHTML=DEMO.usuarios.map(u=>'<tr><td>#'+u.id+'</td><td style="font-weight:500;">'+u.nombre+'</td><td>'+u.email+'</td><td>'+planBadge(u.rol)+'</td><td>'+u.tenant+'</td><td>'+statusBadge(u.estado)+'</td><td style="font-size:12px;color:#4a4a5a;">'+u.ultimoAcceso+'</td><td><div style="display:flex;gap:4px;"><button class="btn btn-ghost btn-sm"><i class="far fa-edit"></i></button><button class="btn btn-ghost btn-sm"><i class="far fa-eye"></i></button></div></td></tr>').join('')}
function renderTickets(){document.getElementById('ticketsTableBody').innerHTML=DEMO.tickets.map(t=>'<tr><td>#'+t.id+'</td><td style="font-weight:500;">'+t.asunto+'</td><td>'+t.cliente+'</td><td>'+statusBadge(t.prioridad)+'</td><td>'+statusBadge(t.estado)+'</td><td>'+t.asignado+'</td><td style="font-size:12px;color:#4a4a5a;">'+t.creado+'</td><td><div style="display:flex;gap:4px;"><button class="btn btn-ghost btn-sm"><i class="far fa-edit"></i></button><button class="btn btn-ghost btn-sm"><i class="far fa-eye"></i></button></div></td></tr>').join('')}
function renderAudit(){document.getElementById('auditTableBody').innerHTML=DEMO.audit.map(a=>'<tr><td style="font-size:12px;color:#4a4a5a;white-space:nowrap;">'+a.timestamp+'</td><td style="font-weight:500;">'+a.usuario+'</td><td><span class="badge '+(a.accion==='CREATE'?'badge-success':a.accion==='UPDATE'?'badge-warning':a.accion==='DELETE'?'badge-danger':a.accion==='LOGIN'?'badge-info':'badge-gray')+'">'+a.accion+'</span></td><td>'+a.entidad+'</td><td style="max-width:250px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">'+a.detalle+'</td><td style="font-size:12px;font-family:monospace;color:#4a4a5a;">'+a.ip+'</td></tr>').join('')}
function refreshData(){showToast('Actualizando datos...','info');setTimeout(()=>{loadDashboard();renderPedidos();renderChoferes();renderVehiculos();renderClientes();renderCFDI();renderPagos();renderBilling();renderUsuarios();renderTickets();renderAudit();showToast('Datos actualizados','success')},800)}
window.addEventListener('load',()=>{loadDashboard();renderPedidos();renderChoferes();renderVehiculos();renderClientes();renderCFDI();renderPagos();renderBilling();initCancelChart();renderUsuarios();renderTickets();renderAudit();setTimeout(initDashboardMap,500)});
/* Theme toggle - uses ThemeManager from theme.js */
function toggleTheme(){ThemeManager.toggle();const icon=document.getElementById('theme-icon');if(icon)icon.className=ThemeManager.get()==='dark'?'fas fa-moon':'fas fa-sun'}
window.addEventListener('DOMContentLoaded',()=>{if(typeof ThemeManager!=='undefined')ThemeManager.init()});
/* Re-render charts + map on theme change */
window.addEventListener('themechange',()=>{
  const t=ThemeManager.get();
  const gridC=t==='dark'?'rgba(26,26,34,0.8)':'rgba(200,200,210,0.3)';
  const tickC=t==='dark'?'#4a4a5a':'#6b7280';
  if(pedidosChart){pedidosChart.options.scales.x.grid.color=gridC;pedidosChart.options.scales.y.grid.color=gridC;pedidosChart.options.scales.x.ticks.color=tickC;pedidosChart.options.scales.y.ticks.color=tickC;pedidosChart.update()}
  if(revenueChart){revenueChart.options.scales.x.grid.color=gridC;revenueChart.options.scales.y.grid.color=gridC;revenueChart.options.scales.x.ticks.color=tickC;revenueChart.options.scales.y.ticks.color=tickC;revenueChart.update()}
  if(dashboardMap){dashboardMap.eachLayer(l=>{if(l._url)l.setUrl(t==='dark'?'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png':'https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png')})}
  if(rutasMap){rutasMap.eachLayer(l=>{if(l._url)l.setUrl(t==='dark'?'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png':'https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png')})}
});
/* Color picker + tarifa input listeners */
document.addEventListener('DOMContentLoaded', () => {
  const colorInput = document.getElementById('zon-color');
  if (colorInput) {
    colorInput.addEventListener('input', () => {
      const hex = document.getElementById('zon-color-hex');
      if (hex) hex.textContent = colorInput.value;
    });
  }
  document.querySelectorAll('.tarifa-input').forEach(inp => {
    inp.addEventListener('input', () => {
      calcularEjemploTarifa(inp.getAttribute('data-serv'));
    });
  });
});