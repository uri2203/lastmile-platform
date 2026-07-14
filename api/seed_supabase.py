"""Seed Supabase via REST API with lowercase table names"""
import urllib.request, json, hashlib, random

KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InlwYXJsaXhjcnRldGZmaGhla2tpIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4NDA1MTIyNywiZXhwIjoyMDk5NjI3MjI3fQ.daZyNEEovQ92tgUa_DcVEdujj9fdizUuBEDREu_9-xQ'
BASE = 'https://yparlixcrtetffhhekki.supabase.co/rest/v1'

def h(p): return hashlib.sha256(p.encode()).hexdigest()

def insert(table, data):
    url = f'{BASE}/{table}'
    body = json.dumps(data).encode()
    req = urllib.request.Request(url, data=body, method='POST', headers={
        'apikey': KEY, 'Authorization': f'Bearer {KEY}',
        'Content-Type': 'application/json', 'Prefer': 'return=minimal'
    })
    try:
        urllib.request.urlopen(req, timeout=30)
        return True
    except urllib.error.HTTPError as e:
        print(f'  ERR {table}: {e.read().decode()[:150]}')
        return False

def batch_insert(table, rows):
    url = f'{BASE}/{table}'
    body = json.dumps(rows).encode()
    req = urllib.request.Request(url, data=body, method='POST', headers={
        'apikey': KEY, 'Authorization': f'Bearer {KEY}',
        'Content-Type': 'application/json', 'Prefer': 'return=minimal'
    })
    try:
        urllib.request.urlopen(req, timeout=60)
        return True
    except urllib.error.HTTPError as e:
        print(f'  ERR BATCH {table}: {e.read().decode()[:200]}')
        return False

print('=== SEEDING SUPABASE (lowercase) ===')

# 1. EMPRESAS
print('[1/9] Empresas...')
batch_insert('empresas', [
    {'EMP_NOMBRE':'Express Delivery MX','EMP_RFC':'EDM230101AB1','EMP_DIRECCION':'Av. Reforma 255, Col. Centro, CDMX','EMP_TELEFONO':'5551234567','EMP_EMAIL':'admin@expressdelivery.mx','EMP_CONTACTO':'Carlos Mendez'},
    {'EMP_NOMBRE':'Transporte Rapido SA','EMP_RFC':'TRA230202CD2','EMP_DIRECCION':'Blvd. Insurgentes 890, Col. Roma, CDMX','EMP_TELEFONO':'5552345678','EMP_EMAIL':'admin@transporterapido.mx','EMP_CONTACTO':'Ana Torres'},
    {'EMP_NOMBRE':'Logistica Integral MX','EMP_RFC':'LIM230303EF3','EMP_DIRECCION':'Calz. de Tlalpan 456, Col. Del Valle, CDMX','EMP_TELEFONO':'5553456789','EMP_EMAIL':'admin@logisticaintegral.mx','EMP_CONTACTO':'Roberto Diaz'},
])
print('  3 OK')

# 2. USUARIOS
print('[2/9] Usuarios...')
batch_insert('usuarios', [
    {'USU_EMP_ID':1,'USU_USUARIO':'admin','USU_PASS':h('admin123'),'USU_NOMBRE':'Administrador','USU_EMAIL':'admin@delivery.mx','USU_TELEFONO':'5551001001','USU_ROL':'admin'},
    {'USU_EMP_ID':1,'USU_USUARIO':'operador','USU_PASS':h('oper123'),'USU_NOMBRE':'Operador General','USU_EMAIL':'ops@delivery.mx','USU_TELEFONO':'5551001002','USU_ROL':'operacion'},
    {'USU_EMP_ID':1,'USU_USUARIO':'chofer1','USU_PASS':h('chof123'),'USU_NOMBRE':'Carlos Rodriguez','USU_EMAIL':'carlos@delivery.mx','USU_TELEFONO':'5551001003','USU_ROL':'chofer'},
    {'USU_EMP_ID':1,'USU_USUARIO':'chofer2','USU_PASS':h('chof123'),'USU_NOMBRE':'Maria Lopez','USU_EMAIL':'maria@delivery.mx','USU_TELEFONO':'5551001004','USU_ROL':'chofer'},
    {'USU_EMP_ID':1,'USU_USUARIO':'cliente1','USU_PASS':h('clie123'),'USU_NOMBRE':'Juan Perez Store','USU_EMAIL':'juan@perez.mx','USU_TELEFONO':'5551001005','USU_ROL':'cliente'},
    {'USU_EMP_ID':1,'USU_USUARIO':'cliente2','USU_PASS':h('clie123'),'USU_NOMBRE':'Ana Garcia Shop','USU_EMAIL':'ana@garcia.mx','USU_TELEFONO':'5551001006','USU_ROL':'cliente'},
    {'USU_EMP_ID':2,'USU_USUARIO':'admin2','USU_PASS':h('admin123'),'USU_NOMBRE':'Admin Transporte Rapido','USU_EMAIL':'admin@transporte.mx','USU_TELEFONO':'5552002001','USU_ROL':'admin'},
    {'USU_EMP_ID':2,'USU_USUARIO':'ops2','USU_PASS':h('oper123'),'USU_NOMBRE':'Operador TR','USU_EMAIL':'ops@transporte.mx','USU_TELEFONO':'5552002002','USU_ROL':'operacion'},
    {'USU_EMP_ID':2,'USU_USUARIO':'chofer3','USU_PASS':h('chof123'),'USU_NOMBRE':'Pedro Sanchez','USU_EMAIL':'pedro@transporte.mx','USU_TELEFONO':'5552002003','USU_ROL':'chofer'},
    {'USU_EMP_ID':2,'USU_USUARIO':'cliente3','USU_PASS':h('clie123'),'USU_NOMBRE':'Tienda Rodriguez','USU_EMAIL':'tienda@rodriguez.mx','USU_TELEFONO':'5552002004','USU_ROL':'cliente'},
    {'USU_EMP_ID':3,'USU_USUARIO':'admin3','USU_PASS':h('admin123'),'USU_NOMBRE':'Admin Logistica Integral','USU_EMAIL':'admin@logistica.mx','USU_TELEFONO':'5553003001','USU_ROL':'admin'},
    {'USU_EMP_ID':3,'USU_USUARIO':'ops3','USU_PASS':h('oper123'),'USU_NOMBRE':'Operador LI','USU_EMAIL':'ops@logistica.mx','USU_TELEFONO':'5553003002','USU_ROL':'operacion'},
    {'USU_EMP_ID':3,'USU_USUARIO':'chofer4','USU_PASS':h('chof123'),'USU_NOMBRE':'Roberto Diaz','USU_EMAIL':'roberto@logistica.mx','USU_TELEFONO':'5553003003','USU_ROL':'chofer'},
    {'USU_EMP_ID':3,'USU_USUARIO':'cliente4','USU_PASS':h('clie123'),'USU_NOMBRE':'Comercial Torres','USU_EMAIL':'torres@comercial.mx','USU_TELEFONO':'5553003004','USU_ROL':'cliente'},
])
print('  14 OK')

# 3. CHOFERES
print('[3/9] Choferes...')
batch_insert('choferes', [
    {'EMP_ID':1,'CHO_NOMBRE':'Carlos','CHO_APELLIDO':'Rodriguez','CHO_RFC':'CARR850101','CHO_LICENCIA':'LIC-001','CHO_TELEFONO':'5551110001','CHO_EMAIL':'carlos@delivery.mx'},
    {'EMP_ID':1,'CHO_NOMBRE':'Maria','CHO_APELLIDO':'Lopez','CHO_RFC':'MALO900202','CHO_LICENCIA':'LIC-002','CHO_TELEFONO':'5551110002','CHO_EMAIL':'maria@delivery.mx'},
    {'EMP_ID':1,'CHO_NOMBRE':'Pedro','CHO_APELLIDO':'Sanchez','CHO_RFC':'PESA880303','CHO_LICENCIA':'LIC-003','CHO_TELEFONO':'5551110003','CHO_EMAIL':'pedro@delivery.mx'},
    {'EMP_ID':1,'CHO_NOMBRE':'Ana','CHO_APELLIDO':'Martinez','CHO_RFC':'AAMA920404','CHO_LICENCIA':'LIC-004','CHO_TELEFONO':'5551110004','CHO_EMAIL':'ana@delivery.mx'},
    {'EMP_ID':1,'CHO_NOMBRE':'Jose','CHO_APELLIDO':'Hernandez','CHO_RFC':'JOHE870505','CHO_LICENCIA':'LIC-005','CHO_TELEFONO':'5551110005','CHO_EMAIL':'jose@delivery.mx'},
    {'EMP_ID':2,'CHO_NOMBRE':'Pedro','CHO_APELLIDO':'Sanchez2','CHO_RFC':'PESA880606','CHO_LICENCIA':'LIC-006','CHO_TELEFONO':'5552220001','CHO_EMAIL':'pedro2@transporte.mx'},
    {'EMP_ID':2,'CHO_NOMBRE':'Laura','CHO_APELLIDO':'Garcia','CHO_RFC':'LAGA910707','CHO_LICENCIA':'LIC-007','CHO_TELEFONO':'5552220002','CHO_EMAIL':'laura@transporte.mx'},
    {'EMP_ID':2,'CHO_NOMBRE':'Miguel','CHO_APELLIDO':'Torres','CHO_RFC':'MITO890808','CHO_LICENCIA':'LIC-008','CHO_TELEFONO':'5552220003','CHO_EMAIL':'miguel@transporte.mx'},
    {'EMP_ID':3,'CHO_NOMBRE':'Roberto','CHO_APELLIDO':'Diaz','CHO_RFC':'RODI860909','CHO_LICENCIA':'LIC-009','CHO_TELEFONO':'5553330001','CHO_EMAIL':'roberto@logistica.mx'},
    {'EMP_ID':3,'CHO_NOMBRE':'Sofia','CHO_APELLIDO':'Ruiz','CHO_RFC':'SORU931010','CHO_LICENCIA':'LIC-010','CHO_TELEFONO':'5553330002','CHO_EMAIL':'sofia@logistica.mx'},
])
print('  10 OK')

# 4. VEHICULOS
print('[4/9] Vehiculos...')
batch_insert('vehiculos', [
    {'EMP_ID':1,'VEH_UNIDAD':'EXP-001','VEH_MARCA':'Nissan','VEH_MODELO':'NP300','VEH_ANIO':'2023','VEH_PLACAS':'ABC-123','VEH_COLOR':'Blanco','VEH_TIPO':'CAMIONETA','VEH_CAPACIDAD_KG':1000,'VEH_CAPACIDAD_M3':2.5},
    {'EMP_ID':1,'VEH_UNIDAD':'EXP-002','VEH_MARCA':'Volkswagen','VEH_MODELO':'Saveiro','VEH_ANIO':'2022','VEH_PLACAS':'DEF-456','VEH_COLOR':'Gris','VEH_TIPO':'CAMIONETA','VEH_CAPACIDAD_KG':800,'VEH_CAPACIDAD_M3':1.8},
    {'EMP_ID':1,'VEH_UNIDAD':'EXP-003','VEH_MARCA':'Ford','VEH_MODELO':'Ranger','VEH_ANIO':'2024','VEH_PLACAS':'GHI-789','VEH_COLOR':'Negro','VEH_TIPO':'CAMIONETA','VEH_CAPACIDAD_KG':1200,'VEH_CAPACIDAD_M3':3.0},
    {'EMP_ID':2,'VEH_UNIDAD':'TR-001','VEH_MARCA':'Chevrolet','VEH_MODELO':'Tornado','VEH_ANIO':'2023','VEH_PLACAS':'JKL-012','VEH_COLOR':'Rojo','VEH_TIPO':'CAMIONETA','VEH_CAPACIDAD_KG':900,'VEH_CAPACIDAD_M3':2.2},
    {'EMP_ID':2,'VEH_UNIDAD':'TR-002','VEH_MARCA':'Nissan','VEH_MODELO':'Frontier','VEH_ANIO':'2022','VEH_PLACAS':'MNO-345','VEH_COLOR':'Azul','VEH_TIPO':'CAMIONETA','VEH_CAPACIDAD_KG':1500,'VEH_CAPACIDAD_M3':3.5},
    {'EMP_ID':3,'VEH_UNIDAD':'LI-001','VEH_MARCA':'Toyota','VEH_MODELO':'Hilux','VEH_ANIO':'2024','VEH_PLACAS':'PQR-678','VEH_COLOR':'Blanco','VEH_TIPO':'CAMIONETA','VEH_CAPACIDAD_KG':1100,'VEH_CAPACIDAD_M3':2.8},
])
print('  6 OK')

# 5. CLIENTES_LM
print('[5/9] Clientes...')
batch_insert('clientes_lm', [
    {'EMP_ID':1,'CLI_RAZON_SOCIAL':'Tech Solutions SA','CLI_RFC':'TSA230101','CLI_CONTACTO':'Juan Perez','CLI_TELEFONO':'5551111111','CLI_EMAIL':'info@techsol.mx','CLI_DIRECCION':'Av. Reforma 255','CLI_COLONIA':'Centro','CLI_CIUDAD':'CDMX','CLI_ESTADO':'CDMX','CLI_CP':'06000'},
    {'EMP_ID':1,'CLI_RAZON_SOCIAL':'Comercial ABC','CLI_RFC':'CAB230202','CLI_CONTACTO':'Maria Garcia','CLI_TELEFONO':'5551111112','CLI_EMAIL':'ventas@comercial.mx','CLI_DIRECCION':'Calle 5 de Mayo 120','CLI_COLONIA':'Juarez','CLI_CIUDAD':'CDMX','CLI_ESTADO':'CDMX','CLI_CP':'06600'},
    {'EMP_ID':1,'CLI_RAZON_SOCIAL':'Distribuidora Norte','CLI_RFC':'DNO230303','CLI_CONTACTO':'Pedro Hernandez','CLI_TELEFONO':'5551111113','CLI_EMAIL':'pedidos@distnorte.mx','CLI_DIRECCION':'Blvd. Insurgentes 890','CLI_COLONIA':'Roma Norte','CLI_CIUDAD':'CDMX','CLI_ESTADO':'CDMX','CLI_CP':'06700'},
    {'EMP_ID':1,'CLI_RAZON_SOCIAL':'Farmacias Guadalajara','CLI_RFC':'FG230404','CLI_CONTACTO':'Ana Martinez','CLI_TELEFONO':'5551111114','CLI_EMAIL':'compras@fg.mx','CLI_DIRECCION':'Av. Universidad 300','CLI_COLONIA':'Narvarte','CLI_CIUDAD':'CDMX','CLI_ESTADO':'CDMX','CLI_CP':'03100'},
    {'EMP_ID':1,'CLI_RAZON_SOCIAL':'Restaurant El Bajio','CLI_RFC':'REB230505','CLI_CONTACTO':'Jose Luis Fernandez','CLI_TELEFONO':'5551111115','CLI_EMAIL':'reservas@elbajio.mx','CLI_DIRECCION':'Av. Patriotismo 222','CLI_COLONIA':'San Pedro de los Pinos','CLI_CIUDAD':'CDMX','CLI_ESTADO':'CDMX','CLI_CP':'03810'},
    {'EMP_ID':2,'CLI_RAZON_SOCIAL':'Mineria del Valle','CLI_RFC':'MDV230606','CLI_CONTACTO':'Roberto Torres','CLI_TELEFONO':'5552222221','CLI_EMAIL':'ops@miner.mx','CLI_DIRECCION':'Calz. de Tlalpan 456','CLI_COLONIA':'Portales','CLI_CIUDAD':'CDMX','CLI_ESTADO':'CDMX','CLI_CP':'03300'},
    {'EMP_ID':2,'CLI_RAZON_SOCIAL':'Superama Express','CLI_RFC':'SEX230707','CLI_CONTACTO':'Laura Sanchez','CLI_TELEFONO':'5552222222','CLI_EMAIL':'logistica@superama.mx','CLI_DIRECCION':'Calle Montes de Oca 45','CLI_COLONIA':'San Angel','CLI_CIUDAD':'CDMX','CLI_ESTADO':'CDMX','CLI_CP':'01000'},
    {'EMP_ID':3,'CLI_RAZON_SOCIAL':'Grupo Logistico MX','CLI_RFC':'GLM230808','CLI_CONTACTO':'Fernando Ruiz','CLI_TELEFONO':'5553333331','CLI_EMAIL':'contacto@glm.mx','CLI_DIRECCION':'Periferico Sur 1200','CLI_COLONIA':'Del Valle','CLI_CIUDAD':'CDMX','CLI_ESTADO':'CDMX','CLI_CP':'03103'},
])
print('  8 OK')

# 6. ZONAS
print('[6/9] Zonas + Tarifas...')
batch_insert('zonas', [
    {'ZON_EMP_ID':1,'ZON_NOMBRE':'Centro Historico','ZON_DESCRIPCION':'Zona centro historico de CDMX','ZON_COLOR':'#6366f1','ZON_RADIO_KM':3.0,'ZON_CENTRO_LAT':19.4326,'ZON_CENTRO_LNG':-99.1332},
    {'ZON_EMP_ID':1,'ZON_NOMBRE':'Polanco / Reforma','ZON_DESCRIPCION':'Zona premium','ZON_COLOR':'#10b981','ZON_RADIO_KM':4.0,'ZON_CENTRO_LAT':19.4350,'ZON_CENTRO_LNG':-99.1950},
    {'ZON_EMP_ID':1,'ZON_NOMBRE':'Roma / Condesa','ZON_DESCRIPCION':'Zonas populares','ZON_COLOR':'#f59e0b','ZON_RADIO_KM':3.5,'ZON_CENTRO_LAT':19.4126,'ZON_CENTRO_LNG':-99.1600},
    {'ZON_EMP_ID':1,'ZON_NOMBRE':'Coyoacan / San Angel','ZON_DESCRIPCION':'Zona sur artistica','ZON_COLOR':'#8b5cf6','ZON_RADIO_KM':5.0,'ZON_CENTRO_LAT':19.3500,'ZON_CENTRO_LNG':-99.1550},
    {'ZON_EMP_ID':1,'ZON_NOMBRE':'Santa Fe / Cuajimalpa','ZON_DESCRIPCION':'Zona corporativa','ZON_COLOR':'#ef4444','ZON_RADIO_KM':6.0,'ZON_CENTRO_LAT':19.3600,'ZON_CENTRO_LNG':-99.2700},
    {'ZON_EMP_ID':1,'ZON_NOMBRE':'Del Valle / Narvarte','ZON_DESCRIPCION':'Zona residencial sur','ZON_COLOR':'#06b6d4','ZON_RADIO_KM':3.0,'ZON_CENTRO_LAT':19.3900,'ZON_CENTRO_LNG':-99.1700},
    {'ZON_EMP_ID':1,'ZON_NOMBRE':'Escandon / Tacubaya','ZON_DESCRIPCION':'Zona mixta poniente','ZON_COLOR':'#ec4899','ZON_RADIO_KM':2.5,'ZON_CENTRO_LAT':19.4050,'ZON_CENTRO_LNG':-99.2000},
])
print('  7 zonas OK')

# Tarifas (21 = 7 zonas x 3 servicios)
tarifas = []
for zon_id in range(1, 8):
    base = 35 + (zon_id * 5)
    for svc, extra, kg, km, seguro in [('EXPRESS',10,8.00,5.00,2.0),('ESTANDAR',0,5.00,3.50,0),('ECONOMICO',-10,3.00,2.00,0)]:
        tarifas.append({'ZTA_ZON_ID':zon_id,'ZTA_EMP_ID':1,'ZTA_SERVICIO':svc,'ZTA_MONTO_BASE':base+extra,'ZTA_MONTO_POR_KG':kg,'ZTA_MONTO_POR_KM':km,'ZTA_PESO_MIN_KG':0.5,'ZTA_PESO_MAX_KG':30.0,'ZTA_DISTANCIA_MAX_KM':50.0,'ZTA_MONTO_MINIMO':base+extra,'ZTA_SEGURO_PCT':seguro})
batch_insert('zona_tarifas', tarifas)
print('  21 tarifas OK')

# 7. SAAS_PLANES + SUSCRIPCIONES
print('[7/9] Planes SaaS...')
batch_insert('saas_planes', [
    {'PLAN_NOMBRE':'Starter','PLAN_DESCRIPCION':'$999/mes - 5 choferes, 200 envios','PLAN_PRECIO_MENSUAL':999,'PLAN_PRECIO_ANUAL':9990,'PLAN_MAX_CHOFERES':5,'PLAN_MAX_ENVIOS_MES':200,'PLAN_MAX_USUARIOS':3,'PLAN_MAX_SUCURSALES':1,'PLAN_FEATURES':'basicos'},
    {'PLAN_NOMBRE':'Pro','PLAN_DESCRIPCION':'$2,499/mes - 15 choferes, 1000 envios','PLAN_PRECIO_MENSUAL':2499,'PLAN_PRECIO_ANUAL':24990,'PLAN_MAX_CHOFERES':15,'PLAN_MAX_ENVIOS_MES':1000,'PLAN_MAX_USUARIOS':10,'PLAN_MAX_SUCURSALES':5,'PLAN_FEATURES':'avanzado,reportes,api'},
    {'PLAN_NOMBRE':'Enterprise','PLAN_DESCRIPCION':'$5,999/mes - ilimitado','PLAN_PRECIO_MENSUAL':5999,'PLAN_PRECIO_ANUAL':59990,'PLAN_MAX_CHOFERES':999,'PLAN_MAX_ENVIOS_MES':99999,'PLAN_MAX_USUARIOS':999,'PLAN_MAX_SUCURSALES':99,'PLAN_FEATURES':'todo,soporte_dedicado,sla'},
])
batch_insert('saas_suscripciones', [
    {'EMP_ID':1,'PLAN_ID':2,'SUS_ESTADO':'ACTIVA'},
    {'EMP_ID':2,'PLAN_ID':1,'SUS_ESTADO':'ACTIVA'},
    {'EMP_ID':3,'PLAN_ID':1,'SUS_ESTADO':'ACTIVA'},
])
print('  3 planes + 3 suscripciones OK')

# 8. PAGOS + CFDI
print('[8/9] Pagos + CFDI...')
batch_insert('pagos_metodos', [
    {'EMP_ID':1,'PMT_TIPO':'EFECTIVO','PMT_NOMBRE':'Efectivo','PMT_ACTIVO':'S'},
    {'EMP_ID':1,'PMT_TIPO':'TARJETA','PMT_NOMBRE':'Tarjeta de credito','PMT_ACTIVO':'S'},
    {'EMP_ID':1,'PMT_TIPO':'TRANSFERENCIA','PMT_NOMBRE':'Transferencia bancaria','PMT_ACTIVO':'S'},
    {'EMP_ID':1,'PMT_TIPO':'OXXO','PMT_NOMBRE':'Deposito OXXO','PMT_ACTIVO':'S'},
    {'EMP_ID':2,'PMT_TIPO':'EFECTIVO','PMT_NOMBRE':'Efectivo','PMT_ACTIVO':'S'},
    {'EMP_ID':2,'PMT_TIPO':'TARJETA','PMT_NOMBRE':'Tarjeta','PMT_ACTIVO':'S'},
    {'EMP_ID':3,'PMT_TIPO':'EFECTIVO','PMT_NOMBRE':'Efectivo','PMT_ACTIVO':'S'},
])
batch_insert('cfdi_folios', [
    {'EMP_ID':1,'FOL_SERIE':'A','FOL_SIGUIENTE':1,'FOL_FINAL':1000,'FOL_ESTATUS':'ACTIVO'},
    {'EMP_ID':2,'FOL_SERIE':'A','FOL_SIGUIENTE':1,'FOL_FINAL':1000,'FOL_ESTATUS':'ACTIVO'},
    {'EMP_ID':3,'FOL_SERIE':'A','FOL_SIGUIENTE':1,'FOL_FINAL':1000,'FOL_ESTATUS':'ACTIVO'},
])
print('  7 pagos + 3 folios OK')

# 9. PEDIDOS (100 demo)
print('[9/9] Pedidos (100)...')
nombres = ['Tech Solutions','Comercial ABC','Distribuidora Norte','Farmacias GDL','Restaurant El Bajio','Mineria del Valle','Superama Express','Grupo Logistico MX']
direcciones = ['Av. Reforma 255','Calle 5 de Mayo 120','Blvd. Insurgentes 890','Av. Universidad 300','Calz. de Tlalpan 456','Periferico Sur 1200','Calle Montes de Oca 45','Av. Patriotismo 222']
colonias = ['Centro','Juarez','Roma Norte','Narvarte','Portales','Del Valle','San Angel','Pedregal']
estados = ['PENDIENTE','EN_RUTA','ENTREGADO']
formas_pago = ['EFECTIVO','TARJETA','TRANSFERENCIA','OXXO']
prioridades = ['NORMAL','ALTA','URGENTE','BAJA']

# Insert in batches of 20
pedidos = []
for i in range(100):
    emp_id = random.choice([1,1,1,2,2,3])
    idx = random.randint(0, len(nombres)-1)
    pedidos.append({
        'EMP_ID': emp_id,
        'PED_NUMERO': f'PED-2026-{i+1:04d}',
        'CLI_ID': random.randint(1,8),
        'PED_CLIENTE_NOMBRE': nombres[idx],
        'PED_CLIENTE_TELEFONO': f'555{random.randint(1000000,9999999)}',
        'PED_DESTINO_DIR': direcciones[idx],
        'PED_DESTINO_COL': colonias[idx],
        'PED_DESTINO_CIUDAD': 'CDMX',
        'PED_PESO_KG': round(random.uniform(0.5, 30), 1),
        'PED_BULTOS': random.randint(1, 8),
        'PED_COSTO_TOTAL': round(random.uniform(80, 1500), 2),
        'PED_FORMA_PAGO': random.choice(formas_pago),
        'PED_ESTADO': random.choice(estados),
        'PED_PRIORIDAD': random.choice(prioridades),
    })

# Send in batches of 25
for batch_start in range(0, 100, 25):
    batch = pedidos[batch_start:batch_start+25]
    batch_insert('pedidos', batch)
print('  100 pedidos OK')

print()
print('=== SEED COMPLETO ===')
print('3 empresas, 14 usuarios, 10 choferes, 6 vehiculos')
print('8 clientes, 7 zonas, 21 tarifas, 3 planes, 100 pedidos')
