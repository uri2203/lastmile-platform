"""
SEED DATA: Creates all tables + inserts demo data directly.
No dependency on legacy backup files.
Runs on first server start in cloud environments.
"""
import sqlite3
import os
import hashlib
from security import hash_password
import json
from datetime import datetime, timedelta
import random
import secrets

DATA_DIR = os.environ.get('DATA_DIR', os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(DATA_DIR, 'lastmile.db')


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def seed():
    """Create tables + seed data. Idempotent (safe to run multiple times)."""
    if os.path.exists(DB_PATH):
        # Check if already seeded
        conn = get_db()
        c = conn.cursor()
        try:
            c.execute("SELECT COUNT(*) FROM EMPRESAS")
            count = c.fetchone()[0]
            if count > 0:
                print(f'[SEED] Database already has {count} empresas. Skipping.')
                conn.close()
                return
        except:
            pass
        conn.close()

    print('[SEED] Creating tables and seeding data...')
    conn = get_db()
    c = conn.cursor()

    # ========================================
    # CREATE ALL TABLES
    # ========================================

    c.execute("""CREATE TABLE IF NOT EXISTS EMPRESAS (
        EMP_ID INTEGER PRIMARY KEY AUTOINCREMENT,
        EMP_NOMBRE TEXT NOT NULL, EMP_RFC TEXT, EMP_DIRECCION TEXT,
        EMP_TELEFONO TEXT, EMP_EMAIL TEXT, EMP_CONTACTO TEXT,
        EMP_FECHA_ALTA TEXT DEFAULT (datetime('now')), EMP_ESTATUS TEXT DEFAULT 'ACTIVA',
        EMP_PLAN TEXT DEFAULT 'STARTER', EMP_MAX_USUARIOS INTEGER DEFAULT 5,
        EMP_MAX_CHOFERES INTEGER DEFAULT 10, EMP_MAX_PEDIDOS_MES INTEGER DEFAULT 500
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS USUARIOS (
        USU_ID INTEGER PRIMARY KEY AUTOINCREMENT, USU_EMP_ID INTEGER NOT NULL,
        USU_USUARIO TEXT NOT NULL, USU_PASS TEXT NOT NULL, USU_NOMBRE TEXT NOT NULL,
        USU_EMAIL TEXT, USU_TELEFONO TEXT, USU_ROL TEXT NOT NULL DEFAULT 'operacion',
        USU_ACTIVO TEXT DEFAULT 'S', USU_CREATED TEXT DEFAULT (datetime('now')),
        USU_UPDATED TEXT DEFAULT (datetime('now')),
        FOREIGN KEY (USU_EMP_ID) REFERENCES EMPRESAS(EMP_ID)
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS CHOFERES (
        CHO_ID INTEGER PRIMARY KEY AUTOINCREMENT, EMP_ID INTEGER NOT NULL,
        CHO_NOMBRE TEXT, CHO_APELLIDO TEXT, CHO_RFC TEXT, CHO_LICENCIA TEXT,
        CHO_TELEFONO TEXT, CHO_EMAIL TEXT, CHO_FECHA_ALTA TEXT,
        CHO_ESTATUS TEXT DEFAULT 'ACTIVO', CHO_TIPO TEXT DEFAULT 'PROPIO',
        CHO_SALARIO_BASE REAL DEFAULT 0, CHO_COMISION_PCT REAL DEFAULT 0,
        FOREIGN KEY (EMP_ID) REFERENCES EMPRESAS(EMP_ID)
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS VEHICULOS (
        VEH_ID INTEGER PRIMARY KEY AUTOINCREMENT, EMP_ID INTEGER NOT NULL,
        VEH_UNIDAD TEXT, VEH_MARCA TEXT, VEH_MODELO TEXT, VEH_ANIO TEXT,
        VEH_PLACAS TEXT, VEH_COLOR TEXT, VEH_TIPO TEXT DEFAULT 'CAMIONETA',
        VEH_CAPACIDAD_KG REAL DEFAULT 0, VEH_CAPACIDAD_M3 REAL DEFAULT 0,
        VEH_ESTATUS TEXT DEFAULT 'DISPONIBLE', VEH_GPS_ACTIVO TEXT DEFAULT 'N',
        VEH_ULTIMA_VELOCIDAD REAL DEFAULT 0,
        FOREIGN KEY (EMP_ID) REFERENCES EMPRESAS(EMP_ID)
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS CLIENTES_LM (
        CLI_ID INTEGER PRIMARY KEY AUTOINCREMENT, EMP_ID INTEGER NOT NULL,
        CLI_RAZON_SOCIAL TEXT, CLI_RFC TEXT, CLI_CONTACTO TEXT, CLI_TELEFONO TEXT,
        CLI_EMAIL TEXT, CLI_DIRECCION TEXT, CLI_COLONIA TEXT, CLI_CIUDAD TEXT,
        CLI_ESTADO TEXT, CLI_CP TEXT, CLI_LATITUD REAL, CLI_LONGITUD REAL,
        CLI_ZONA TEXT, CLI_ESTATUS TEXT DEFAULT 'ACTIVO', CLI_FECHA_ALTA TEXT,
        CLI_TIPO_CLIENTE TEXT DEFAULT 'GENERAL', CLI_CREDITO REAL DEFAULT 0,
        CLI_SALDO REAL DEFAULT 0,
        FOREIGN KEY (EMP_ID) REFERENCES EMPRESAS(EMP_ID)
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS PEDIDOS (
        PED_ID INTEGER PRIMARY KEY AUTOINCREMENT, EMP_ID INTEGER NOT NULL,
        PED_NUMERO TEXT, CLI_ID INTEGER, PED_CLIENTE_NOMBRE TEXT,
        PED_CLIENTE_TELEFONO TEXT, PED_CLIENTE_EMAIL TEXT,
        PED_ORIGEN_DIR TEXT, PED_ORIGEN_LAT REAL, PED_ORIGEN_LON REAL,
        PED_DESTINO_DIR TEXT, PED_DESTINO_COL TEXT, PED_DESTINO_CIUDAD TEXT,
        PED_DESTINO_ESTADO TEXT, PED_DESTINO_CP TEXT, PED_DESTINO_LAT REAL,
        PED_DESTINO_LON REAL, PED_DESCRIPCION TEXT, PED_REFERENCIA TEXT,
        PED_PESO_KG REAL DEFAULT 0, PED_VOLUMEN_M3 REAL DEFAULT 0,
        PED_BULTOS INTEGER DEFAULT 1, PED_VALOR_DECLARADO REAL DEFAULT 0,
        PED_COSTO_ENVIO REAL DEFAULT 0, PED_COSTO_TOTAL REAL DEFAULT 0,
        PED_FORMA_PAGO TEXT DEFAULT 'EFECTIVO', PED_ESTADO TEXT DEFAULT 'PENDIENTE',
        PED_PRIORIDAD TEXT DEFAULT 'NORMAL',
        PED_FECHA_PEDIDO TEXT DEFAULT (datetime('now')),
        PED_FECHA_RECOLECTA TEXT, PED_FECHA_ENTREGA_EST TEXT,
        PED_FECHA_ENTREGA_REAL TEXT, PED_INSTRUCCIONES TEXT, PED_NOTASINTERNAS TEXT,
        CHO_ID INTEGER, VEH_ID INTEGER, CHOFER_ASIGNADO TEXT, UNIDAD_ASIGNADA TEXT,
        FOREIGN KEY (EMP_ID) REFERENCES EMPRESAS(EMP_ID)
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS PEDIDO_HISTORIAL (
        HIS_ID INTEGER PRIMARY KEY AUTOINCREMENT, PED_ID INTEGER NOT NULL,
        HIS_ESTADO TEXT NOT NULL, HIS_FECHA TEXT DEFAULT (datetime('now')),
        HIS_USUARIO TEXT, HIS_OBSERVACIONES TEXT,
        FOREIGN KEY (PED_ID) REFERENCES PEDIDOS(PED_ID)
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS TRACKING (
        TRK_ID INTEGER PRIMARY KEY AUTOINCREMENT, EMP_ID INTEGER NOT NULL,
        CHO_ID INTEGER, VEH_ID INTEGER, TRK_LATITUD REAL, TRK_LONGITUD REAL,
        TRK_VELOCIDAD REAL DEFAULT 0, TRK_RUMBO REAL DEFAULT 0,
        TRK_FECHA TEXT DEFAULT (datetime('now')), TRK_BATERIA REAL DEFAULT 100,
        FOREIGN KEY (EMP_ID) REFERENCES EMPRESAS(EMP_ID)
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS ZONAS (
        ZON_ID INTEGER PRIMARY KEY AUTOINCREMENT, ZON_EMP_ID INTEGER NOT NULL,
        ZON_NOMBRE TEXT NOT NULL, ZON_DESCRIPCION TEXT, ZON_COLOR TEXT DEFAULT '#6366f1',
        ZON_RADIO_KM REAL DEFAULT 5.0, ZON_CENTRO_LAT REAL, ZON_CENTRO_LNG REAL,
        ZON_ACTIVO TEXT DEFAULT 'S', ZON_CREATED TEXT DEFAULT (datetime('now')),
        ZON_UPDATED TEXT DEFAULT (datetime('now')),
        FOREIGN KEY (ZON_EMP_ID) REFERENCES EMPRESAS(EMP_ID)
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS ZONA_TARIFAS (
        ZTA_ID INTEGER PRIMARY KEY AUTOINCREMENT, ZTA_ZON_ID INTEGER NOT NULL,
        ZTA_EMP_ID INTEGER NOT NULL, ZTA_SERVICIO TEXT DEFAULT 'ESTANDAR',
        ZTA_MONTO_BASE REAL DEFAULT 0, ZTA_MONTO_POR_KG REAL DEFAULT 0,
        ZTA_MONTO_POR_KM REAL DEFAULT 0, ZTA_MONTO_POR_M3 REAL DEFAULT 0,
        ZTA_PESO_MIN_KG REAL DEFAULT 0.5, ZTA_PESO_MAX_KG REAL DEFAULT 30.0,
        ZTA_DISTANCIA_MAX_KM REAL DEFAULT 50.0, ZTA_MONTO_MINIMO REAL DEFAULT 35.0,
        ZTA_SEGURO_PCT REAL DEFAULT 0, ZTA_ACTIVO TEXT DEFAULT 'S',
        ZTA_CREATED TEXT DEFAULT (datetime('now')),
        FOREIGN KEY (ZTA_ZON_ID) REFERENCES ZONAS(ZON_ID)
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS CFDI_EMPRESA_FISCAL (
        FISC_ID INTEGER PRIMARY KEY AUTOINCREMENT, EMP_ID INTEGER NOT NULL UNIQUE,
        FISC_RFC TEXT, FISC_RAZON_SOCIAL TEXT, FISC_REGIMEN_FISCAL TEXT,
        FISC_CODIGO_POSTAL TEXT, FISC_COLONIA TEXT, FISC_CALLE TEXT,
        FISC_NUMERO_EXTERIOR TEXT, FISC_MUNICIPIO TEXT, FISC_ESTADO TEXT,
        FISC_TELEFONO TEXT, FISC_EMAIL TEXT, FISC_TIPO_PERSONA TEXT DEFAULT 'M'
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS CFDI_FOLIOS (
        FOL_ID INTEGER PRIMARY KEY AUTOINCREMENT, EMP_ID INTEGER NOT NULL,
        FOL_SERIE TEXT NOT NULL, FOL_SIGUIENTE INTEGER DEFAULT 1,
        FOL_FINAL INTEGER DEFAULT 1000, FOL_ESTATUS TEXT DEFAULT 'ACTIVO'
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS CFDI_FACTURAS (
        FAC_ID INTEGER PRIMARY KEY AUTOINCREMENT, EMP_ID INTEGER NOT NULL,
        FAC_UUID TEXT, FAC_SERIE TEXT, FAC_FOLIO TEXT,
        FAC_FECHA_EMISION TEXT DEFAULT (datetime('now')), FAC_FECHA_TIMBRADO TEXT,
        FAC_FORMA_PAGO TEXT DEFAULT '01', FAC_METODO_PAGO TEXT DEFAULT 'PUE',
        FAC_CONDICION_PAGO TEXT DEFAULT 'CONTADO', FAC_NUM_PARCIALIDADES INTEGER DEFAULT 1,
        FAC_SUBTOTAL REAL DEFAULT 0, FAC_DESCUENTO REAL DEFAULT 0,
        FAC_TOTAL_IVA REAL DEFAULT 0, FAC_TOTAL_ISR REAL DEFAULT 0,
        FAC_TOTAL_RETENCIONES REAL DEFAULT 0, FAC_TOTAL REAL DEFAULT 0,
        FAC_MONEDA TEXT DEFAULT 'MXN', FAC_TIPO_CAMBIO REAL DEFAULT 1,
        FAC_RECEPTOR_RFC TEXT, FAC_RECEPTOR_RAZON TEXT,
        FAC_RECEPTOR_REGIMEN TEXT DEFAULT '601', FAC_RECEPTOR_CP TEXT DEFAULT '00000',
        FAC_RECEPTOR_USO_CFDI TEXT DEFAULT 'G03', FAC_RECEPTOR_EMAIL TEXT,
        FAC_PED_ID INTEGER, FAC_XML_TIMBRADO TEXT, FAC_PDF_URL TEXT,
        FAC_ESTATUS TEXT DEFAULT 'PENDIENTE', FAC_MOTIVO_CANCELACION TEXT,
        FAC_UUID_SUSTITUCION TEXT, FAC_TIPO_DOCUMENTO TEXT DEFAULT 'INGRESO',
        FAC_NOTAS TEXT, FAC_FECHA_REGISTRO TEXT DEFAULT (datetime('now'))
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS CFDI_TIMBRADO_LOG (
        TIM_ID INTEGER PRIMARY KEY AUTOINCREMENT, FAC_ID INTEGER NOT NULL,
        TIM_PAC TEXT, TIM_REQUEST TEXT, TIM_RESPONSE TEXT,
        TIM_CODIGO_RESPUESTA TEXT, TIM_MENSAJE TEXT,
        TIM_FECHA TEXT DEFAULT (datetime('now')), TIM_EXITOSO TEXT DEFAULT 'N'
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS CFDI_CONCEPTOS_CATALOGO (
        COC_ID INTEGER PRIMARY KEY AUTOINCREMENT, EMP_ID INTEGER NOT NULL,
        COC_CLAVE_PROD_SERV TEXT, COC_DESCRIPCION TEXT, COC_CLAVE_UNIDAD TEXT,
        COC_UNIDAD TEXT, COC_PORCENTAJE_IVA REAL DEFAULT 16,
        COC_ESTATUS TEXT DEFAULT 'ACTIVO'
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS PAGOS_METODOS (
        PMT_ID INTEGER PRIMARY KEY AUTOINCREMENT, EMP_ID INTEGER NOT NULL,
        PMT_TIPO TEXT NOT NULL, PMT_NOMBRE TEXT, PMT_CONFIG TEXT,
        PMT_ACTIVO TEXT DEFAULT 'S'
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS PAGOS_TRANSACCIONES (
        TRP_ID INTEGER PRIMARY KEY AUTOINCREMENT, EMP_ID INTEGER NOT NULL,
        PED_ID INTEGER, FAC_ID INTEGER, TRP_NUM_REFERENCIA TEXT,
        TRP_MONTO REAL DEFAULT 0, TRP_MONEDA TEXT DEFAULT 'MXN',
        TRP_METODO TEXT, TRP_ESTATUS TEXT DEFAULT 'PENDIENTE',
        TRP_FECHA_REGISTRO TEXT DEFAULT (datetime('now')),
        TRP_FECHA_CONCILIACION TEXT, TRP_CONCILIADO TEXT DEFAULT 'N',
        TRP_NOTAS TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS AUDIT_LOG (
        AUD_ID INTEGER PRIMARY KEY AUTOINCREMENT, EMP_ID INTEGER NOT NULL,
        AUD_USUARIO TEXT, AUD_ACCION TEXT, AUD_TABLA TEXT,
        AUD_REGISTRO_ID INTEGER, AUD_DETALLE TEXT, AUD_IP TEXT,
        AUD_FECHA TEXT DEFAULT (datetime('now'))
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS CLIENTE_FINAL (
        CLIF_ID INTEGER PRIMARY KEY AUTOINCREMENT, EMP_ID INTEGER NOT NULL,
        PED_ID INTEGER NOT NULL, CLIF_NOMBRE TEXT, CLIF_TELEFONO TEXT,
        CLIF_EMAIL TEXT, CLIF_TOKEN_TRACKING TEXT UNIQUE,
        CLIF_NOTIF_SMS TEXT DEFAULT 'N', CLIF_NOTIF_WHATSAPP TEXT DEFAULT 'N',
        CLIF_NOTIF_EMAIL TEXT DEFAULT 'N',
        CLIF_FECHA_REGISTRO TEXT DEFAULT (datetime('now'))
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS SAAS_PLANES (
        PLAN_ID INTEGER PRIMARY KEY AUTOINCREMENT, PLAN_NOMBRE TEXT NOT NULL,
        PLAN_DESCRIPCION TEXT, PLAN_PRECIO_MENSUAL REAL DEFAULT 0,
        PLAN_PRECIO_ANUAL REAL DEFAULT 0, PLAN_MAX_CHOFERES INTEGER DEFAULT 5,
        PLAN_MAX_ENVIOS_MES INTEGER DEFAULT 100, PLAN_MAX_USUARIOS INTEGER DEFAULT 3,
        PLAN_MAX_SUCURSALES INTEGER DEFAULT 1, PLAN_FEATURES TEXT DEFAULT '{}',
        PLAN_ACTIVO TEXT DEFAULT 'S', PLAN_ORDEN INTEGER DEFAULT 0
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS SAAS_SUSCRIPCIONES (
        SUS_ID INTEGER PRIMARY KEY AUTOINCREMENT, EMP_ID INTEGER NOT NULL,
        PLAN_ID INTEGER NOT NULL, SUS_ESTADO TEXT DEFAULT 'TRIAL',
        SUS_FECHA_INICIO TEXT, SUS_FECHA_FIN TEXT, SUS_FECHA_PROXIMO_COBRO TEXT,
        SUS_FACTURACION_CICLO TEXT DEFAULT 'MENSUAL', SUS_METODO_PAGO TEXT,
        SUS_MP_CUSTOMER_ID TEXT, SUS_MP_SUBSCRIPTION_ID TEXT,
        SUS_STRIPE_CUSTOMER_ID TEXT, SUS_STRIPE_SUBSCRIPTION_ID TEXT,
        SUS_TOTAL_COBRADO REAL DEFAULT 0, SUS_FECHA_REGISTRO TEXT DEFAULT (datetime('now')),
        SUS_NOTAS TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS SAAS_COBROS (
        COB_ID INTEGER PRIMARY KEY AUTOINCREMENT, SUS_ID INTEGER NOT NULL,
        EMP_ID INTEGER NOT NULL, COB_MONTO REAL DEFAULT 0,
        COB_MONEDA TEXT DEFAULT 'MXN', COB_CONCEPTO TEXT,
        COB_ESTATUS TEXT DEFAULT 'PENDIENTE', COB_METODO_PAGO TEXT,
        COB_REFERENCIA_PAGO TEXT, COB_FECHA_COBRO TEXT DEFAULT (datetime('now')),
        COB_FECHA_APLICADO TEXT, COB_FACTURA_ID INTEGER,
        COB_JSON_RESPUESTA TEXT, COB_NOTAS TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS SAAS_USO_RECURSOS (
        USR_ID INTEGER PRIMARY KEY AUTOINCREMENT, EMP_ID INTEGER NOT NULL,
        USR_FECHA TEXT DEFAULT (date('now')), USR_PEDIDOS_CREADOS INTEGER DEFAULT 0,
        USR_PEDIDOS_ENTREGADOS INTEGER DEFAULT 0, USR_ENVIOS_SMS INTEGER DEFAULT 0,
        USR_ENVIOS_EMAIL INTEGER DEFAULT 0, USR_API_CALLS INTEGER DEFAULT 0
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS NOTIF_PUSH (
        NPUSH_ID INTEGER PRIMARY KEY AUTOINCREMENT, EMP_ID INTEGER NOT NULL,
        USR_ID INTEGER, CHO_ID INTEGER, NPUSH_TIPO TEXT, NPUSH_TITULO TEXT,
        NPUSH_CUERPO TEXT, NPUSH_DATA TEXT DEFAULT '{}',
        NPUSH_ENVIADO TEXT DEFAULT 'N', NPUSH_LEIDO TEXT DEFAULT 'N',
        NPUSH_FECHA_REGISTRO TEXT DEFAULT (datetime('now'))
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS NOTIF_DISPOSITIVOS (
        DISP_ID INTEGER PRIMARY KEY AUTOINCREMENT, EMP_ID INTEGER NOT NULL,
        USR_ID INTEGER, CHO_ID INTEGER, DISP_TOKEN TEXT,
        DISP_PLATAFORMA TEXT DEFAULT 'WEB', DISP_ACTIVO TEXT DEFAULT 'S',
        DISP_FECHA_REGISTRO TEXT DEFAULT (datetime('now'))
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS EMAIL_ENVIADOS (
        EMAIL_ID INTEGER PRIMARY KEY AUTOINCREMENT, EMP_ID INTEGER NOT NULL,
        PED_ID INTEGER, FAC_ID INTEGER, EMAIL_DESTINATARIO TEXT,
        EMAIL_ASUNTO TEXT, EMAIL_TIPO TEXT, EMAIL_BODY_HTML TEXT,
        EMAIL_ENVIADO TEXT DEFAULT 'N', EMAIL_FECHA_REGISTRO TEXT DEFAULT (datetime('now')),
        EMAIL_FECHA_ENVIO TEXT, EMAIL_ERROR TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS SMS_ENVIADOS (
        SMS_ID INTEGER PRIMARY KEY AUTOINCREMENT, EMP_ID INTEGER NOT NULL,
        PED_ID INTEGER, SMS_TELEFONO TEXT, SMS_MENSAJE TEXT,
        SMS_PLATAFORMA TEXT DEFAULT 'SMS', SMS_ENVIADO TEXT DEFAULT 'N',
        SMS_COSTO REAL DEFAULT 0, SMS_FECHA_REGISTRO TEXT DEFAULT (datetime('now')),
        SMS_FECHA_ENVIO TEXT, SMS_ERROR TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS REPORTES_GENERADOS (
        RPT_ID INTEGER PRIMARY KEY AUTOINCREMENT, EMP_ID INTEGER NOT NULL,
        RPT_TIPO TEXT NOT NULL, RPT_NOMBRE TEXT, RPT_PARAMETROS TEXT DEFAULT '{}',
        RPT_RUTA_ARCHIVO TEXT, RPT_GENERADO_POR TEXT,
        RPT_FECHA_GENERACION TEXT DEFAULT (datetime('now'))
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS ENTREGAS (
        ENT_ID INTEGER PRIMARY KEY AUTOINCREMENT, EMP_ID INTEGER NOT NULL,
        PED_ID INTEGER, CHO_ID INTEGER, VEH_ID INTEGER,
        ENT_ESTADO TEXT DEFAULT 'PENDIENTE', ENT_FECHA_SALIDA TEXT,
        ENT_FECHA_LLEGADA TEXT, ENT_EVIDENCIA TEXT, ENT_FIRMA TEXT,
        ENT_LATITUD REAL, ENT_LONGITUD REAL, ENT_NOTAS TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS INCIDENCIAS (
        INC_ID INTEGER PRIMARY KEY AUTOINCREMENT, EMP_ID INTEGER NOT NULL,
        PED_ID INTEGER, CHO_ID INTEGER, INC_TIPO TEXT, INC_DESCRIPCION TEXT,
        INC_FECHA TEXT DEFAULT (datetime('now')), INC_RESUELTA TEXT DEFAULT 'N',
        INC_FECHA_RESOLUCION TEXT, INC_USUARIO_REPORTA TEXT,
        INC_USUARIO_RESUELVE TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS KPI_DIARIO (
        KPI_ID INTEGER PRIMARY KEY AUTOINCREMENT, EMP_ID INTEGER NOT NULL,
        KPI_FECHA TEXT DEFAULT (date('now')), KPI_PEDIDOS_CREADOS INTEGER DEFAULT 0,
        KPI_PEDIDOS_ENTREGADOS INTEGER DEFAULT 0, KPI_PEDIDOS_CANCELADOS INTEGER DEFAULT 0,
        KPI_INGRESOS REAL DEFAULT 0, KPI_COSTOS REAL DEFAULT 0,
        KPI_UTILIDAD REAL DEFAULT 0, KPI_ENTREGAS_PUNTUALES INTEGER DEFAULT 0,
        KPI_ENTREGAS_TARDIAS INTEGER DEFAULT 0, KPI_INCIDENCIAS INTEGER DEFAULT 0,
        KPI_PROMEDIO_TIEMPO_ENTREGA REAL DEFAULT 0
    )""")

    # ========================================
    # CREATE VIEWS
    # ========================================
    for view_name in ['V_DASHBOARD_RESUMEN','V_PEDIDOS_COMPLETO','V_RENDIMIENTO_CHOFERES',
                       'V_ESTADO_FLOTA','V_COSTOS_RUTA','V_TOP_CLIENTES',
                       'V_KPI_CONSOLIDADO','V_INCIDENCIAS_RESUMEN']:
        c.execute(f"DROP VIEW IF EXISTS {view_name}")

    c.execute("""CREATE VIEW V_DASHBOARD_RESUMEN AS
        SELECT e.EMP_ID, e.EMP_NOMBRE,
            (SELECT COUNT(*) FROM PEDIDOS p WHERE p.EMP_ID = e.EMP_ID) as TOTAL_PEDIDOS,
            (SELECT COUNT(*) FROM PEDIDOS p WHERE p.EMP_ID = e.EMP_ID AND p.PED_ESTADO = 'PENDIENTE') as PEDIDOS_PENDIENTES,
            (SELECT COUNT(*) FROM PEDIDOS p WHERE p.EMP_ID = e.EMP_ID AND p.PED_ESTADO = 'EN_RUTA') as PEDIDOS_EN_RUTA,
            (SELECT COUNT(*) FROM PEDIDOS p WHERE p.EMP_ID = e.EMP_ID AND p.PED_ESTADO = 'ENTREGADO') as PEDIDOS_ENTREGADOS,
            (SELECT COUNT(*) FROM CHOFERES ch WHERE ch.EMP_ID = e.EMP_ID AND ch.CHO_ESTATUS = 'ACTIVO') as CHOFERES_ACTIVOS,
            (SELECT COUNT(*) FROM VEHICULOS v WHERE v.EMP_ID = e.EMP_ID AND v.VEH_ESTATUS = 'DISPONIBLE') as VEHICULOS_DISPONIBLES,
            (SELECT COUNT(*) FROM CLIENTES_LM cl WHERE cl.EMP_ID = e.EMP_ID) as TOTAL_CLIENTES,
            (SELECT COALESCE(SUM(p2.PED_COSTO_TOTAL), 0) FROM PEDIDOS p2 WHERE p2.EMP_ID = e.EMP_ID AND p2.PED_ESTADO = 'ENTREGADO') as INGRESOS_MES
        FROM EMPRESAS e""")

    c.execute("""CREATE VIEW V_PEDIDOS_COMPLETO AS
        SELECT p.*, e.EMP_NOMBRE,
            (SELECT COUNT(*) FROM PEDIDO_HISTORIAL h WHERE h.PED_ID = p.PED_ID) as TOTAL_MOVIMIENTOS
        FROM PEDIDOS p LEFT JOIN EMPRESAS e ON p.EMP_ID = e.EMP_ID""")

    c.execute("""CREATE VIEW V_RENDIMIENTO_CHOFERES AS
        SELECT ch.CHO_ID, ch.EMP_ID, ch.CHO_NOMBRE, ch.CHO_APELLIDO,
            (SELECT COUNT(*) FROM PEDIDOS p WHERE p.CHO_ID = ch.CHO_ID AND p.PED_ESTADO = 'ENTREGADO') as ENTREGAS_REALIZADAS,
            (SELECT COUNT(*) FROM PEDIDOS p WHERE p.CHO_ID = ch.CHO_ID) as TOTAL_ASIGNACIONES,
            0 as TASA_EXITO, 0 as PROMEDIO_HORAS, 0 as VELOCIDAD_PROMEDIO
        FROM CHOFERES ch""")

    c.execute("""CREATE VIEW V_ESTADO_FLOTA AS
        SELECT v.*, NULL as CHO_NOMBRE, NULL as CHO_APELLIDO,
            (SELECT COUNT(*) FROM PEDIDOS p WHERE p.VEH_ID = v.VEH_ID AND p.PED_ESTADO = 'EN_RUTA') as ENVIOS_ACTIVOS,
            NULL as ULT_LAT, NULL as ULT_LNG, NULL as ULT_VELOCIDAD
        FROM VEHICULOS v""")

    c.execute("""CREATE VIEW V_COSTOS_RUTA AS
        SELECT r.*, e.EMP_NOMBRE FROM PEDIDOS r LEFT JOIN EMPRESAS e ON r.EMP_ID = e.EMP_ID
        WHERE r.PED_ESTADO IN ('EN_RUTA', 'ENTREGADO')""")

    c.execute("""CREATE VIEW V_TOP_CLIENTES AS
        SELECT cl.CLI_ID, cl.EMP_ID, cl.CLI_RAZON_SOCIAL, cl.CLI_TELEFONO, cl.CLI_EMAIL,
            (SELECT COUNT(*) FROM PEDIDOS p WHERE p.CLI_ID = cl.CLI_ID) as TOTAL_PEDIDOS,
            (SELECT COALESCE(SUM(p.PED_COSTO_TOTAL), 0) FROM PEDIDOS p WHERE p.CLI_ID = cl.CLI_ID) as TOTAL_GASTADO
        FROM CLIENTES_LM cl""")

    c.execute("""CREATE VIEW V_KPI_CONSOLIDADO AS
        SELECT e.EMP_ID,
            (SELECT COUNT(*) FROM PEDIDOS p WHERE p.EMP_ID = e.EMP_ID AND p.PED_FECHA_PEDIDO >= date('now', '-30 days')) as PEDIDOS_MES,
            (SELECT COALESCE(SUM(p.PED_COSTO_TOTAL), 0) FROM PEDIDOS p WHERE p.EMP_ID = e.EMP_ID AND p.PED_FECHA_PEDIDO >= date('now', '-30 days')) as INGRESOS_MES,
            (SELECT COUNT(*) FROM PEDIDOS p WHERE p.EMP_ID = e.EMP_ID AND p.PED_ESTADO = 'ENTREGADO' AND p.PED_FECHA_PEDIDO >= date('now', '-30 days')) as ENTREGAS_MES,
            (SELECT COUNT(*) FROM INCIDENCIAS i WHERE i.EMP_ID = e.EMP_ID AND i.INC_FECHA >= date('now', '-30 days')) as INCIDENCIAS_MES
        FROM EMPRESAS e""")

    c.execute("""CREATE VIEW V_INCIDENCIAS_RESUMEN AS
        SELECT i.EMP_ID, COUNT(*) as TOTAL,
            SUM(CASE WHEN i.INC_RESUELTA = 'S' THEN 1 ELSE 0 END) as RESUELTAS,
            SUM(CASE WHEN i.INC_RESUELTA = 'N' THEN 1 ELSE 0 END) as PENDIENTES
        FROM INCIDENCIAS i GROUP BY i.EMP_ID""")

    # ========================================
    # SEED DATA
    # ========================================
    print('[SEED] Inserting demo data...')

    # Empresas
    empresas = [
        (1, 'Express Delivery MX', 'EDM230101AB1', 'Av. Reforma 255, Col. Centro, CDMX', '5551234567', 'admin@expressdelivery.mx', 'Carlos Mendez'),
        (2, 'Transporte Rapido SA', 'TRA230202CD2', 'Blvd. Insurgentes 890, Col. Roma, CDMX', '5552345678', 'admin@transporterapido.mx', 'Ana Torres'),
        (3, 'Logistica Integral MX', 'LIM230303EF3', 'Calz. de Tlalpan 456, Col. Del Valle, CDMX', '5553456789', 'admin@logisticaintegral.mx', 'Roberto Diaz'),
    ]
    for e in empresas:
        c.execute("INSERT INTO EMPRESAS (EMP_ID,EMP_NOMBRE,EMP_RFC,EMP_DIRECCION,EMP_TELEFONO,EMP_EMAIL,EMP_CONTACTO) VALUES (?,?,?,?,?,?,?)", list(e))

    # Usuarios (bcrypt hashed passwords)
    def h(p): return hash_password(p)
    usuarios = [
        (1,'admin',h('admin123'),'Administrador','admin@delivery.mx','5551001001','admin'),
        (1,'operador',h('oper123'),'Operador General','ops@delivery.mx','5551001002','operacion'),
        (1,'chofer1',h('chof123'),'Carlos Rodriguez','carlos@delivery.mx','5551001003','chofer'),
        (1,'chofer2',h('chof123'),'Maria Lopez','maria@delivery.mx','5551001004','chofer'),
        (1,'cliente1',h('clie123'),'Juan Perez Store','juan@perez.mx','5551001005','cliente'),
        (1,'cliente2',h('clie123'),'Ana Garcia Shop','ana@garcia.mx','5551001006','cliente'),
        (2,'admin2',h('admin123'),'Admin Transporte Rapido','admin@transporte.mx','5552002001','admin'),
        (2,'ops2',h('oper123'),'Operador TR','ops@transporte.mx','5552002002','operacion'),
        (2,'chofer3',h('chof123'),'Pedro Sanchez','pedro@transporte.mx','5552002003','chofer'),
        (2,'cliente3',h('clie123'),'Tienda Rodriguez','tienda@rodriguez.mx','5552002004','cliente'),
        (3,'admin3',h('admin123'),'Admin Logistica Integral','admin@logistica.mx','5553003001','admin'),
        (3,'ops3',h('oper123'),'Operador LI','ops@logistica.mx','5553003002','operacion'),
        (3,'chofer4',h('chof123'),'Roberto Diaz','roberto@logistica.mx','5553003003','chofer'),
        (3,'cliente4',h('clie123'),'Comercial Torres','torres@comercial.mx','5553003004','cliente'),
    ]
    for u in usuarios:
        c.execute("INSERT INTO USUARIOS (USU_EMP_ID,USU_USUARIO,USU_PASS,USU_NOMBRE,USU_EMAIL,USU_TELEFONO,USU_ROL) VALUES (?,?,?,?,?,?,?)", list(u))

    # Choferes
    choferes = [
        (1,'Carlos','Rodriguez','CARR850101','LIC-001','5551110001','carlos@delivery.mx','ACTIVO'),
        (1,'Maria','Lopez','MALO900202','LIC-002','5551110002','maria@delivery.mx','ACTIVO'),
        (1,'Pedro','Sanchez','PESA880303','LIC-003','5551110003','pedro@delivery.mx','ACTIVO'),
        (1,'Ana','Martinez','AAMA920404','LIC-004','5551110004','ana@delivery.mx','ACTIVO'),
        (1,'Jose','Hernandez','JOHE870505','LIC-005','5551110005','jose@delivery.mx','ACTIVO'),
        (2,'Pedro','Sanchez2','PESA880606','LIC-006','5552220001','pedro2@transporte.mx','ACTIVO'),
        (2,'Laura','Garcia','LAGA910707','LIC-007','5552220002','laura@transporte.mx','ACTIVO'),
        (2,'Miguel','Torres','MITO890808','LIC-008','5552220003','miguel@transporte.mx','ACTIVO'),
        (3,'Roberto','Diaz','RODI860909','LIC-009','5553330001','roberto@logistica.mx','ACTIVO'),
        (3,'Sofia','Ruiz','SORU931010','LIC-010','5553330002','sofia@logistica.mx','ACTIVO'),
    ]
    for ch in choferes:
        c.execute("INSERT INTO CHOFERES (EMP_ID,CHO_NOMBRE,CHO_APELLIDO,CHO_RFC,CHO_LICENCIA,CHO_TELEFONO,CHO_EMAIL,CHO_ESTATUS) VALUES (?,?,?,?,?,?,?,?)", list(ch))

    # Vehiculos
    vehiculos = [
        (1,'EXP-001','Nissan','NP300','2023','ABC-123','Blanco','CAMIONETA',1000,2.5,'DISPONIBLE'),
        (1,'EXP-002','Volkswagen','Saveiro','2022','DEF-456','Gris','CAMIONETA',800,1.8,'DISPONIBLE'),
        (1,'EXP-003','Ford','Ranger','2024','GHI-789','Negro','CAMIONETA',1200,3.0,'EN_RUTA'),
        (2,'TR-001','Chevrolet','Tornado','2023','JKL-012','Rojo','CAMIONETA',900,2.2,'DISPONIBLE'),
        (2,'TR-002','Nissan','Frontier','2022','MNO-345','Azul','CAMIONETA',1500,3.5,'DISPONIBLE'),
        (3,'LI-001','Toyota','Hilux','2024','PQR-678','Blanco','CAMIONETA',1100,2.8,'DISPONIBLE'),
    ]
    for v in vehiculos:
        c.execute("INSERT INTO VEHICULOS (EMP_ID,VEH_UNIDAD,VEH_MARCA,VEH_MODELO,VEH_ANIO,VEH_PLACAS,VEH_COLOR,VEH_TIPO,VEH_CAPACIDAD_KG,VEH_CAPACIDAD_M3,VEH_ESTATUS) VALUES (?,?,?,?,?,?,?,?,?,?,?)", list(v))

    # Clientes
    clientes = [
        (1,'Tech Solutions SA','TSA230101','Juan Perez','5551111111','info@techsol.mx','Av. Reforma 255','Centro','CDMX','CDMX','06000'),
        (1,'Comercial ABC','CAB230202','Maria Garcia','5551111112','ventas@comercial.mx','Calle 5 de Mayo 120','Juarez','CDMX','CDMX','06600'),
        (1,'Distribuidora Norte','DNO230303','Pedro Hernandez','5551111113','pedidos@distnorte.mx','Blvd. Insurgentes 890','Roma Norte','CDMX','CDMX','06700'),
        (1,'Farmacias Guadalajara','FG230404','Ana Martinez','5551111114',' compras@fg.mx','Av. Universidad 300','Narvarte','CDMX','CDMX','03100'),
        (1,'Restaurant El Bajio','REB230505','Jose Luis Fernandez','5551111115','reservas@elbajio.mx','Av. Patriotismo 222','San Pedro de los Pinos','CDMX','CDMX','03810'),
        (2,'Mineria del Valle','MDV230606','Roberto Torres','5552222221','ops@miner.mx','Calz. de Tlalpan 456','Portales','CDMX','CDMX','03300'),
        (2,'Superama Express','SEX230707','Laura Sanchez','5552222222','logistica@superama.mx','Calle Montes de Oca 45','San Angel','CDMX','CDMX','01000'),
        (3,'Grupo Logistico MX','GLM230808','Fernando Ruiz','5553333331','contacto@glm.mx','Periferico Sur 1200','Del Valle','CDMX','CDMX','03103'),
    ]
    for cl in clientes:
        c.execute("INSERT INTO CLIENTES_LM (EMP_ID,CLI_RAZON_SOCIAL,CLI_RFC,CLI_CONTACTO,CLI_TELEFONO,CLI_EMAIL,CLI_DIRECCION,CLI_COLONIA,CLI_CIUDAD,CLI_ESTADO,CLI_CP) VALUES (?,?,?,?,?,?,?,?,?,?,?)", list(cl))

    # Zonas de cobertura
    zonas = [
        (1,'Centro Historico','Zona centro historico de CDMX','#6366f1',3.0,19.4326,-99.1332),
        (1,'Polanco / Reforma','Zona premium','#10b981',4.0,19.4350,-99.1950),
        (1,'Roma / Condesa','Zonas populares','#f59e0b',3.5,19.4126,-99.1600),
        (1,'Coyoacan / San Angel','Zona sur artistica','#8b5cf6',5.0,19.3500,-99.1550),
        (1,'Santa Fe / Cuajimalpa','Zona corporativa','#ef4444',6.0,19.3600,-99.2700),
        (1,'Del Valle / Narvarte','Zona residencial sur','#06b6d4',3.0,19.3900,-99.1700),
        (1,'Escandon / Tacubaya','Zona mixta poniente','#ec4899',2.5,19.4050,-99.2000),
    ]
    for z in zonas:
        c.execute("INSERT INTO ZONAS (ZON_EMP_ID,ZON_NOMBRE,ZON_DESCRIPCION,ZON_COLOR,ZON_RADIO_KM,ZON_CENTRO_LAT,ZON_CENTRO_LNG) VALUES (?,?,?,?,?,?,?)", list(z))

    # Tarifas por zona
    tarifas = []
    for zon_id in range(1, 8):
        base = 35 + (zon_id * 5)
        tarifas.extend([
            (zon_id,1,'EXPRESS',base+10,8.00,5.00,0,0.5,15.0,20.0,base+10,2.0),
            (zon_id,1,'ESTANDAR',base,5.00,3.50,0,0.5,30.0,50.0,base,0),
            (zon_id,1,'ECONOMICO',base-10,3.00,2.00,0,1.0,30.0,50.0,base-10,0),
        ])
    for t in tarifas:
        c.execute("INSERT INTO ZONA_TARIFAS (ZTA_ZON_ID,ZTA_EMP_ID,ZTA_SERVICIO,ZTA_MONTO_BASE,ZTA_MONTO_POR_KG,ZTA_MONTO_POR_KM,ZTA_MONTO_POR_M3,ZTA_PESO_MIN_KG,ZTA_PESO_MAX_KG,ZTA_DISTANCIA_MAX_KM,ZTA_MONTO_MINIMO,ZTA_SEGURO_PCT) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", list(t))

    # SAAS Planes
    planes = [
        (1,'Starter','$999/mes - 5 choferes, 200 envios',999,9990,5,200,3,1,'basicos'),
        (2,'Pro','$2,499/mes - 15 choferes, 1000 envios',2499,24990,15,1000,10,5,'avanzado,reportes,api'),
        (3,'Enterprise','$5,999/mes - ilimitado',5999,59990,999,99999,999,99,'todo,soporte_dedicado,sla'),
    ]
    for p in planes:
        c.execute("INSERT INTO SAAS_PLANES (PLAN_ID,PLAN_NOMBRE,PLAN_DESCRIPCION,PLAN_PRECIO_MENSUAL,PLAN_PRECIO_ANUAL,PLAN_MAX_CHOFERES,PLAN_MAX_ENVIOS_MES,PLAN_MAX_USUARIOS,PLAN_MAX_SUCURSALES,PLAN_FEATURES) VALUES (?,?,?,?,?,?,?,?,?,?)", list(p))

    # Suscripciones
    for emp_id, plan_id in [(1,2),(2,1),(3,1)]:
        c.execute("INSERT INTO SAAS_SUSCRIPCIONES (EMP_ID,PLAN_ID,SUS_ESTADO,SUS_FECHA_INICIO,SUS_FECHA_FIN) VALUES (?,?,'ACTIVA',date('now'),date('now','+30 days'))", [emp_id, plan_id])

    # Pedidos de ejemplo (100 pedidos variados)
    estados = ['PENDIENTE','EN_RUTA','ENTREGADO','PENDIENTE','EN_RUTA','ENTREGADO','PENDIENTE','ENTREGADO']
    prioridades = ['NORMAL','ALTA','URGENTE','BAJA']
    formas_pago = ['EFECTIVO','TARJETA','TRANSFERENCIA','OXXO']
    nombres = ['Tech Solutions','Comercial ABC','Distribuidora Norte','Farmacias GDL','Restaurant El Bajio','Mineria del Valle','Superama Express','Grupo Logistico MX']
    direcciones = ['Av. Reforma 255','Calle 5 de Mayo 120','Blvd. Insurgentes 890','Av. Universidad 300','Calz. de Tlalpan 456','Periferico Sur 1200','Calle Montes de Oca 45','Av. Patriotismo 222']
    colonias = ['Centro','Juarez','Roma Norte','Narvarte','Portales','Del Valle','San Angel','Pedregal']
    nombres_chofer = ['Carlos Rodriguez','Maria Lopez','Pedro Sanchez','Ana Martinez','Jose Hernandez']
    unidades = ['EXP-001','EXP-002','EXP-003','TR-001','TR-002','LI-001']

    for i in range(100):
        emp_id = random.choice([1,1,1,2,2,3])
        cli_idx = random.randint(0, len(nombres)-1)
        estado = random.choice(estados)
        hoy = datetime.now()
        fecha = (hoy - timedelta(hours=random.randint(0, 720))).isoformat()
        peso = round(random.uniform(0.5, 30), 1)
        bultos = random.randint(1, 8)
        costo = round(random.uniform(80, 1500), 2)

        fecha_real = None
        if estado == 'ENTREGADO':
            fecha_real = (hoy - timedelta(hours=random.randint(0, 2))).isoformat()

        chofer = random.choice(nombres_chofer) if estado in ('EN_RUTA','ENTREGADO') else None
        unidad = random.choice(unidades) if estado in ('EN_RUTA','ENTREGADO') else None

        c.execute("""INSERT INTO PEDIDOS (EMP_ID,PED_NUMERO,CLI_ID,PED_CLIENTE_NOMBRE,PED_CLIENTE_TELEFONO,
            PED_DESTINO_DIR,PED_DESTINO_COL,PED_DESTINO_CIUDAD,PED_PESO_KG,PED_BULTOS,PED_COSTO_TOTAL,
            PED_FORMA_PAGO,PED_ESTADO,PED_PRIORIDAD,PED_FECHA_PEDIDO,PED_FECHA_ENTREGA_REAL,
            CHOFER_ASIGNADO,UNIDAD_ASIGNADA)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            [emp_id, f'PED-{2026}-{i+1:04d}', random.randint(1,8), nombres[cli_idx],
             f'555{random.randint(1000000,9999999)}', direcciones[cli_idx], colonias[cli_idx],
             'CDMX', peso, bultos, costo, random.choice(formas_pago), estado,
             random.choice(prioridades), fecha, fecha_real, chofer, unidad])

        # Historial basico
        c.execute("INSERT INTO PEDIDO_HISTORIAL (PED_ID,HIS_ESTADO,HIS_USUARIO) VALUES (?,?,'SYSTEM')",
                  [i+1, 'CREADO'])
        if estado in ('EN_RUTA','ENTREGADO'):
            c.execute("INSERT INTO PEDIDO_HISTORIAL (PED_ID,HIS_ESTADO,HIS_USUARIO) VALUES (?,?,'SYSTEM')",
                      [i+1, 'EN_RUTA'])
        if estado == 'ENTREGADO':
            c.execute("INSERT INTO PEDIDO_HISTORIAL (PED_ID,HIS_ESTADO,HIS_USUARIO) VALUES (?,?,'SYSTEM')",
                      [i+1, 'ENTREGADO'])

    # Pagos
    pagos = [
        (1,'EFECTIVO','Efectivo',None,'S'), (1,'TARJETA','Tarjeta de credito',None,'S'),
        (1,'TRANSFERENCIA','Transferencia bancaria',None,'S'), (1,'OXXO','Deposito OXXO',None,'S'),
    ]
    for p in pagos:
        c.execute("INSERT INTO PAGOS_METODOS (EMP_ID,PMT_TIPO,PMT_NOMBRE,PMT_CONFIG,PMT_ACTIVO) VALUES (?,?,?,?,?)", list(p))
    c.execute("INSERT INTO PAGOS_METODOS (EMP_ID,PMT_TIPO,PMT_NOMBRE,PMT_CONFIG,PMT_ACTIVO) VALUES (2,'EFECTIVO','Efectivo',NULL,'S')")
    c.execute("INSERT INTO PAGOS_METODOS (EMP_ID,PMT_TIPO,PMT_NOMBRE,PMT_CONFIG,PMT_ACTIVO) VALUES (2,'TARJETA','Tarjeta',NULL,'S')")
    c.execute("INSERT INTO PAGOS_METODOS (EMP_ID,PMT_TIPO,PMT_NOMBRE,PMT_CONFIG,PMT_ACTIVO) VALUES (3,'EFECTIVO','Efectivo',NULL,'S')")

    # CFDI Folios
    for emp_id in [1,2,3]:
        c.execute("INSERT INTO CFDI_FOLIOS (EMP_ID,FOL_SERIE,FOL_SIGUIENTE,FOL_FINAL,FOL_ESTATUS) VALUES (?,'A',1,1000,'ACTIVO')", [emp_id])

    conn.commit()
    conn.close()

    print(f'[SEED] DONE! Database created at {DB_PATH}')
    print(f'[SEED] Size: {os.path.getsize(DB_PATH)/1024:.1f} KB')
    print(f'[SEED] 3 empresas, 14 usuarios, 100 pedidos, 7 zonas, 21 tarifas')


def seed_pg():
    """Seed PostgreSQL database with demo data. Uses psycopg2."""
    import psycopg2
    db_url = os.environ.get('DATABASE_URL', '')
    if not db_url:
        print('[SEED-PG] No DATABASE_URL set, skipping')
        return

    # Check if already seeded
    conn = psycopg2.connect(db_url)
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM EMPRESAS")
        count = cur.fetchone()[0]
        if count > 0:
            print(f'[SEED-PG] Already has {count} empresas. Skipping.')
            conn.close()
            return
    except Exception:
        conn.close()
        return

    print('[SEED-PG] Seeding PostgreSQL...')
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()

    def h(p):
        return hash_password(p)

    # Empresas
    empresas = [
        ('Express Delivery MX', 'EDM230101AB1', 'Av. Reforma 255, Col. Centro, CDMX', '5551234567', 'admin@expressdelivery.mx', 'Carlos Mendez'),
        ('Transporte Rapido SA', 'TRA230202CD2', 'Blvd. Insurgentes 890, Col. Roma, CDMX', '5552345678', 'admin@transporterapido.mx', 'Ana Torres'),
        ('Logistica Integral MX', 'LIM230303EF3', 'Calz. de Tlalpan 456, Col. Del Valle, CDMX', '5553456789', 'admin@logisticaintegral.mx', 'Roberto Diaz'),
    ]
    for e in empresas:
        cur.execute("INSERT INTO EMPRESAS (EMP_NOMBRE,EMP_RFC,EMP_DIRECCION,EMP_TELEFONO,EMP_EMAIL,EMP_CONTACTO) VALUES (%s,%s,%s,%s,%s,%s) RETURNING EMP_ID", e)

    # Usuarios
    usuarios = [
        (1,'admin',h('admin123'),'Administrador','admin@delivery.mx','5551001001','admin'),
        (1,'operador',h('oper123'),'Operador General','ops@delivery.mx','5551001002','operacion'),
        (1,'chofer1',h('chof123'),'Carlos Rodriguez','carlos@delivery.mx','5551001003','chofer'),
        (1,'chofer2',h('chof123'),'Maria Lopez','maria@delivery.mx','5551001004','chofer'),
        (1,'cliente1',h('clie123'),'Juan Perez Store','juan@perez.mx','5551001005','cliente'),
        (1,'cliente2',h('clie123'),'Ana Garcia Shop','ana@garcia.mx','5551001006','cliente'),
        (2,'admin2',h('admin123'),'Admin Transporte Rapido','admin@transporte.mx','5552002001','admin'),
        (2,'ops2',h('oper123'),'Operador TR','ops@transporte.mx','5552002002','operacion'),
        (2,'chofer3',h('chof123'),'Pedro Sanchez','pedro@transporte.mx','5552002003','chofer'),
        (2,'cliente3',h('clie123'),'Tienda Rodriguez','tienda@rodriguez.mx','5552002004','cliente'),
        (3,'admin3',h('admin123'),'Admin Logistica Integral','admin@logistica.mx','5553003001','admin'),
        (3,'ops3',h('oper123'),'Operador LI','ops@logistica.mx','5553003002','operacion'),
        (3,'chofer4',h('chof123'),'Roberto Diaz','roberto@logistica.mx','5553003003','chofer'),
        (3,'cliente4',h('clie123'),'Comercial Torres','torres@comercial.mx','5553003004','cliente'),
    ]
    for u in usuarios:
        cur.execute("INSERT INTO USUARIOS (USU_EMP_ID,USU_USUARIO,USU_PASS,USU_NOMBRE,USU_EMAIL,USU_TELEFONO,USU_ROL) VALUES (%s,%s,%s,%s,%s,%s,%s)", u)

    # Choferes
    choferes = [
        (1,'Carlos','Rodriguez','CARR850101','LIC-001','5551110001','carlos@delivery.mx','ACTIVO'),
        (1,'Maria','Lopez','MALO900202','LIC-002','5551110002','maria@delivery.mx','ACTIVO'),
        (1,'Pedro','Sanchez','PESA880303','LIC-003','5551110003','pedro@delivery.mx','ACTIVO'),
        (1,'Ana','Martinez','AAMA920404','LIC-004','5551110004','ana@delivery.mx','ACTIVO'),
        (1,'Jose','Hernandez','JOHE870505','LIC-005','5551110005','jose@delivery.mx','ACTIVO'),
        (2,'Pedro','Sanchez2','PESA880606','LIC-006','5552220001','pedro2@transporte.mx','ACTIVO'),
        (2,'Laura','Garcia','LAGA910707','LIC-007','5552220002','laura@transporte.mx','ACTIVO'),
        (2,'Miguel','Torres','MITO890808','LIC-008','5552220003','miguel@transporte.mx','ACTIVO'),
        (3,'Roberto','Diaz','RODI860909','LIC-009','5553330001','roberto@logistica.mx','ACTIVO'),
        (3,'Sofia','Ruiz','SORU931010','LIC-010','5553330002','sofia@logistica.mx','ACTIVO'),
    ]
    for ch in choferes:
        cur.execute("INSERT INTO CHOFERES (EMP_ID,CHO_NOMBRE,CHO_APELLIDO,CHO_RFC,CHO_LICENCIA,CHO_TELEFONO,CHO_EMAIL,CHO_ESTATUS) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)", ch)

    # Vehiculos
    vehiculos = [
        (1,'EXP-001','Nissan','NP300','2023','ABC-123','Blanco','CAMIONETA',1000,2.5,'DISPONIBLE'),
        (1,'EXP-002','Volkswagen','Saveiro','2022','DEF-456','Gris','CAMIONETA',800,1.8,'DISPONIBLE'),
        (1,'EXP-003','Ford','Ranger','2024','GHI-789','Negro','CAMIONETA',1200,3.0,'EN_RUTA'),
        (2,'TR-001','Chevrolet','Tornado','2023','JKL-012','Rojo','CAMIONETA',900,2.2,'DISPONIBLE'),
        (2,'TR-002','Nissan','Frontier','2022','MNO-345','Azul','CAMIONETA',1500,3.5,'DISPONIBLE'),
        (3,'LI-001','Toyota','Hilux','2024','PQR-678','Blanco','CAMIONETA',1100,2.8,'DISPONIBLE'),
    ]
    for v in vehiculos:
        cur.execute("INSERT INTO VEHICULOS (EMP_ID,VEH_UNIDAD,VEH_MARCA,VEH_MODELO,VEH_ANIO,VEH_PLACAS,VEH_COLOR,VEH_TIPO,VEH_CAPACIDAD_KG,VEH_CAPACIDAD_M3,VEH_ESTATUS) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", v)

    # Clientes
    clientes = [
        (1,'Tech Solutions SA','TSA230101','Juan Perez','5551111111','info@techsol.mx','Av. Reforma 255','Centro','CDMX','CDMX','06000'),
        (1,'Comercial ABC','CAB230202','Maria Garcia','5551111112','ventas@comercial.mx','Calle 5 de Mayo 120','Juarez','CDMX','CDMX','06600'),
        (1,'Distribuidora Norte','DNO230303','Pedro Hernandez','5551111113','pedidos@distnorte.mx','Blvd. Insurgentes 890','Roma Norte','CDMX','CDMX','06700'),
        (1,'Farmacias Guadalajara','FG230404','Ana Martinez','5551111114','compras@fg.mx','Av. Universidad 300','Narvarte','CDMX','CDMX','03100'),
        (1,'Restaurant El Bajio','REB230505','Jose Luis Fernandez','5551111115','reservas@elbajio.mx','Av. Patriotismo 222','San Pedro de los Pinos','CDMX','CDMX','03810'),
        (2,'Mineria del Valle','MDV230606','Roberto Torres','5552222221','ops@miner.mx','Calz. de Tlalpan 456','Portales','CDMX','CDMX','03300'),
        (2,'Superama Express','SEX230707','Laura Sanchez','5552222222','logistica@superama.mx','Calle Montes de Oca 45','San Angel','CDMX','CDMX','01000'),
        (3,'Grupo Logistico MX','GLM230808','Fernando Ruiz','5553333331','contacto@glm.mx','Periferico Sur 1200','Del Valle','CDMX','CDMX','03103'),
    ]
    for cl in clientes:
        cur.execute("INSERT INTO CLIENTES_LM (EMP_ID,CLI_RAZON_SOCIAL,CLI_RFC,CLI_CONTACTO,CLI_TELEFONO,CLI_EMAIL,CLI_DIRECCION,CLI_COLONIA,CLI_CIUDAD,CLI_ESTADO,CLI_CP) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", cl)

    # Zonas
    zonas = [
        (1,'Centro Historico','Zona centro historico de CDMX','#6366f1',3.0,19.4326,-99.1332),
        (1,'Polanco / Reforma','Zona premium','#10b981',4.0,19.4350,-99.1950),
        (1,'Roma / Condesa','Zonas populares','#f59e0b',3.5,19.4126,-99.1600),
        (1,'Coyoacan / San Angel','Zona sur artistica','#8b5cf6',5.0,19.3500,-99.1550),
        (1,'Santa Fe / Cuajimalpa','Zona corporativa','#ef4444',6.0,19.3600,-99.2700),
        (1,'Del Valle / Narvarte','Zona residencial sur','#06b6d4',3.0,19.3900,-99.1700),
        (1,'Escandon / Tacubaya','Zona mixta poniente','#ec4899',2.5,19.4050,-99.2000),
    ]
    for z in zonas:
        cur.execute("INSERT INTO ZONAS (ZON_EMP_ID,ZON_NOMBRE,ZON_DESCRIPCION,ZON_COLOR,ZON_RADIO_KM,ZON_CENTRO_LAT,ZON_CENTRO_LNG) VALUES (%s,%s,%s,%s,%s,%s,%s)", z)

    # Tarifas
    for zon_id in range(1, 8):
        base = 35 + (zon_id * 5)
        for servicio, extra, kg, km, seguro in [
            ('EXPRESS', 10, 8.00, 5.00, 2.0),
            ('ESTANDAR', 0, 5.00, 3.50, 0),
            ('ECONOMICO', -10, 3.00, 2.00, 0),
        ]:
            cur.execute("INSERT INTO ZONA_TARIFAS (ZTA_ZON_ID,ZTA_EMP_ID,ZTA_SERVICIO,ZTA_MONTO_BASE,ZTA_MONTO_POR_KG,ZTA_MONTO_POR_KM,ZTA_MONTO_POR_M3,ZTA_PESO_MIN_KG,ZTA_PESO_MAX_KG,ZTA_DISTANCIA_MAX_KM,ZTA_MONTO_MINIMO,ZTA_SEGURO_PCT) VALUES (%s,%s,%s,%s,%s,%s,0,0.5,30.0,50.0,%s,%s)",
                        [zon_id, 1, servicio, base + extra, kg, km, base + extra, seguro])

    # SAAS Planes
    cur.execute("INSERT INTO SAAS_PLANES (PLAN_NOMBRE,PLAN_DESCRIPCION,PLAN_PRECIO_MENSUAL,PLAN_PRECIO_ANUAL,PLAN_MAX_CHOFERES,PLAN_MAX_ENVIOS_MES,PLAN_MAX_USUARIOS,PLAN_MAX_SUCURSALES,PLAN_FEATURES) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                ['Starter','$999/mes - 5 choferes, 200 envios',999,9990,5,200,3,1,'basicos'])
    cur.execute("INSERT INTO SAAS_PLANES (PLAN_NOMBRE,PLAN_DESCRIPCION,PLAN_PRECIO_MENSUAL,PLAN_PRECIO_ANUAL,PLAN_MAX_CHOFERES,PLAN_MAX_ENVIOS_MES,PLAN_MAX_USUARIOS,PLAN_MAX_SUCURSALES,PLAN_FEATURES) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                ['Pro','$2,499/mes - 15 choferes, 1000 envios',2499,24990,15,1000,10,5,'avanzado,reportes,api'])
    cur.execute("INSERT INTO SAAS_PLANES (PLAN_NOMBRE,PLAN_DESCRIPCION,PLAN_PRECIO_MENSUAL,PLAN_PRECIO_ANUAL,PLAN_MAX_CHOFERES,PLAN_MAX_ENVIOS_MES,PLAN_MAX_USUARIOS,PLAN_MAX_SUCURSALES,PLAN_FEATURES) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                ['Enterprise','$5,999/mes - ilimitado',5999,59990,999,99999,999,99,'todo,soporte_dedicado,sla'])

    # Suscripciones
    cur.execute("INSERT INTO SAAS_SUSCRIPCIONES (EMP_ID,PLAN_ID,SUS_ESTADO,SUS_FECHA_INICIO,SUS_FECHA_FIN) VALUES (1,2,'ACTIVA',CURRENT_DATE,CURRENT_DATE + INTERVAL '30 days')")
    cur.execute("INSERT INTO SAAS_SUSCRIPCIONES (EMP_ID,PLAN_ID,SUS_ESTADO,SUS_FECHA_INICIO,SUS_FECHA_FIN) VALUES (2,1,'ACTIVA',CURRENT_DATE,CURRENT_DATE + INTERVAL '30 days')")
    cur.execute("INSERT INTO SAAS_SUSCRIPCIONES (EMP_ID,PLAN_ID,SUS_ESTADO,SUS_FECHA_INICIO,SUS_FECHA_FIN) VALUES (3,1,'ACTIVA',CURRENT_DATE,CURRENT_DATE + INTERVAL '30 days')")

    # Pedidos (100 demo)
    import random
    estados = ['PENDIENTE','EN_RUTA','ENTREGADO']
    nombres = ['Tech Solutions','Comercial ABC','Distribuidora Norte','Farmacias GDL','Restaurant El Bajio','Mineria del Valle','Superama Express','Grupo Logistico MX']
    direcciones = ['Av. Reforma 255','Calle 5 de Mayo 120','Blvd. Insurgentes 890','Av. Universidad 300','Calz. de Tlalpan 456','Periferico Sur 1200','Calle Montes de Oca 45','Av. Patriotismo 222']
    colonias = ['Centro','Juarez','Roma Norte','Narvarte','Portales','Del Valle','San Angel','Pedregal']

    for i in range(100):
        emp_id = random.choice([1,1,1,2,2,3])
        idx = random.randint(0, len(nombres)-1)
        estado = random.choice(estados)
        peso = round(random.uniform(0.5, 30), 1)
        costo = round(random.uniform(80, 1500), 2)
        cur.execute("""INSERT INTO PEDIDOS (EMP_ID,PED_NUMERO,CLI_ID,PED_CLIENTE_NOMBRE,PED_CLIENTE_TELEFONO,
            PED_DESTINO_DIR,PED_DESTINO_COL,PED_DESTINO_CIUDAD,PED_PESO_KG,PED_BULTOS,PED_COSTO_TOTAL,
            PED_FORMA_PAGO,PED_ESTADO,PED_PRIORIDAD)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            [emp_id, f'PED-2026-{i+1:04d}', random.randint(1,8), nombres[idx],
             f'555{random.randint(1000000,9999999)}', direcciones[idx], colonias[idx],
             'CDMX', peso, random.randint(1,8), costo,
             random.choice(['EFECTIVO','TARJETA','TRANSFERENCIA','OXXO']), estado,
             random.choice(['NORMAL','ALTA','URGENTE','BAJA'])])

    # Pagos
    for emp_id, tipo, nombre in [(1,'EFECTIVO','Efectivo'),(1,'TARJETA','Tarjeta de credito'),(1,'TRANSFERENCIA','Transferencia bancaria'),(1,'OXXO','Deposito OXXO'),(2,'EFECTIVO','Efectivo'),(2,'TARJETA','Tarjeta'),(3,'EFECTIVO','Efectivo')]:
        cur.execute("INSERT INTO PAGOS_METODOS (EMP_ID,PMT_TIPO,PMT_NOMBRE,PMT_ACTIVO) VALUES (%s,%s,%s,'S')", [emp_id, tipo, nombre])

    # CFDI Folios
    for emp_id in [1,2,3]:
        cur.execute("INSERT INTO CFDI_FOLIOS (EMP_ID,FOL_SERIE,FOL_SIGUIENTE,FOL_FINAL,FOL_ESTATUS) VALUES (%s,'A',1,1000,'ACTIVO')", [emp_id])

    conn.commit()
    conn.close()
    print('[SEED-PG] DONE! 3 empresas, 14 usuarios, 100 pedidos, 7 zonas, 21 tarifas')


if __name__ == '__main__':
    seed()
