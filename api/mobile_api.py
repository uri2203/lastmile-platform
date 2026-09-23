"""
Mobile API layer for Last Mile Chofer and Cliente apps.
Bridges the mobile clients to the existing PEDIDOS/ENTREGAS/CHOFERES schema.
"""
from flask import Blueprint, request, jsonify, g
from db import query, execute
from auth import requiere_auth, requiere_rol
from datetime import datetime, timedelta

mobile_bp = Blueprint('mobile_api', __name__)


def _emp_id():
    return getattr(g, 'emp_id', None)


def _chofer_profile():
    """Resolve CHOFERES row for the logged-in user (auto-link by email if needed)."""
    emp_id = _emp_id()
    usu_id = getattr(g, 'usu_id', None)
    rows = query(
        "SELECT * FROM CHOFERES WHERE CHO_USU_ID=? AND EMP_ID=?",
        [usu_id, emp_id],
    )
    if rows:
        return rows[0]

    # Auto-link by email
    user = query("SELECT USU_EMAIL, USU_NOMBRE FROM USUARIOS WHERE USU_ID=?", [usu_id])
    email = (user[0].get('USU_EMAIL') or '').strip().lower() if user else ''
    if email:
        by_email = query(
            "SELECT * FROM CHOFERES WHERE EMP_ID=? AND LOWER(COALESCE(CHO_EMAIL,''))=?",
            [emp_id, email],
        )
        if by_email:
            execute(
                "UPDATE CHOFERES SET CHO_USU_ID=? WHERE CHO_ID=? AND EMP_ID=?",
                [usu_id, by_email[0]['CHO_ID'], emp_id],
            )
            return by_email[0]

    # Fallback: first active chofer without user link, else first active
    free = query(
        "SELECT * FROM CHOFERES WHERE EMP_ID=? AND (CHO_USU_ID IS NULL OR CHO_USU_ID=0) AND COALESCE(CHO_ESTATUS,'ACTIVO')='ACTIVO' ORDER BY CHO_ID LIMIT 1",
        [emp_id],
    )
    if not free:
        free = query(
            "SELECT * FROM CHOFERES WHERE EMP_ID=? AND COALESCE(CHO_ESTATUS,'ACTIVO')='ACTIVO' ORDER BY CHO_ID LIMIT 1",
            [emp_id],
        )
    if free:
        execute(
            "UPDATE CHOFERES SET CHO_USU_ID=? WHERE CHO_ID=? AND EMP_ID=?",
            [usu_id, free[0]['CHO_ID'], emp_id],
        )
        return free[0]
    return None


def _map_pedido(row, driver=None):
    """Map a PEDIDOS/V_PEDIDOS_COMPLETO row to the mobile delivery/shipment shape."""
    if not row:
        return None
    status = row.get('PED_ESTADO') or 'PENDIENTE'
    tracking = row.get('PED_NUMERO') or f"LM-{row.get('PED_ID')}"
    dest_dir = row.get('PED_DESTINO_DIR') or ''
    dest_col = row.get('PED_DESTINO_COL') or ''
    dest_city = row.get('PED_DESTINO_CIUDAD') or ''
    destino = ', '.join([p for p in [dest_dir, dest_col, dest_city] if p]) or '—'
    origen = row.get('PED_ORIGEN_DIR') or ''
    return {
        'id': row.get('PED_ID'),
        '_id': row.get('PED_ID'),
        'tracking_number': tracking,
        'folio': tracking,
        'status': status,
        'description': row.get('PED_DESCRIPCION') or '',
        'weight_kg': row.get('PED_PESO_KG') or 0,
        'service_type': (row.get('PED_TIPO_ENVIO') or 'estandar').lower(),
        'declared_value': row.get('PED_VALOR_DECLARADO') or 0,
        'amount': row.get('PED_COSTO_TOTAL') or 0,
        'monto': row.get('PED_COSTO_TOTAL') or 0,
        'payment_method': row.get('PED_FORMA_PAGO') or 'EFECTIVO',
        'metodo_pago': row.get('PED_FORMA_PAGO') or 'EFECTIVO',
        'origin_address': origen,
        'destination_address': destino,
        'origen': origen,
        'destino': destino,
        'direccion': destino,
        'address': destino,
        'origin_lat': row.get('PED_ORIGEN_LAT'),
        'origin_lng': row.get('PED_ORIGEN_LON'),
        'dest_lat': row.get('PED_DESTINO_LAT'),
        'dest_lng': row.get('PED_DESTINO_LON'),
        'destino_lat': row.get('PED_DESTINO_LAT'),
        'destino_lng': row.get('PED_DESTINO_LON'),
        'lat': row.get('PED_DESTINO_LAT'),
        'lng': row.get('PED_DESTINO_LON'),
        'client_name': row.get('PED_CLIENTE_NOMBRE') or '',
        'cliente_nombre': row.get('PED_CLIENTE_NOMBRE') or '',
        'client_phone': row.get('PED_CLIENTE_TELEFONO') or '',
        'phone': row.get('PED_CLIENTE_TELEFONO') or '',
        'telefono': row.get('PED_CLIENTE_TELEFONO') or '',
        'driver_name': (f"{driver.get('CHO_NOMBRE') or ''} {driver.get('CHO_APELLIDO') or ''}".strip()
                        if driver else (row.get('CHOFER_ASIGNADO') or '')),
        'driver_phone': (driver.get('CHO_TELEFONO') if driver else None),
        'driver_lat': (driver.get('CHO_LAT_ACTUAL') if driver else None),
        'driver_lng': (driver.get('CHO_LNG_ACTUAL') if driver else None),
        'created_at': str(row.get('PED_FECHA_PEDIDO') or ''),
        'fecha': str(row.get('PED_FECHA_PEDIDO') or ''),
        'priority': row.get('PED_PRIORIDAD') or 'NORMAL',
        'driver_id': row.get('CHO_ID'),
    }


@mobile_bp.route('/api/deliveries', methods=['GET'])
@requiere_rol('chofer', 'admin', 'operacion', 'superadmin')
def mobile_deliveries():
    emp_id = _emp_id()
    status = request.args.get('status')
    chofer = _chofer_profile()
    if not chofer:
        return jsonify([])

    sql = 'SELECT * FROM PEDIDOS WHERE EMP_ID = ? AND CHO_ID = ?'
    params = [emp_id, chofer['CHO_ID']]
    if status:
        sql += ' AND PED_ESTADO = ?'
        params.append(status)
    sql += " AND PED_ESTADO NOT IN ('ELIMINADO') ORDER BY PED_FECHA_PEDIDO DESC LIMIT 200"
    rows = query(sql, params)
    return jsonify([_map_pedido(r, chofer) for r in rows])


@mobile_bp.route('/api/deliveries/history', methods=['GET'])
@requiere_rol('chofer', 'admin', 'operacion', 'superadmin')
def mobile_deliveries_history():
    emp_id = _emp_id()
    period = request.args.get('period', 'all')
    chofer = _chofer_profile()
    if not chofer:
        return jsonify([])

    sql = (
        "SELECT * FROM PEDIDOS WHERE EMP_ID = ? AND CHO_ID = ? "
        "AND PED_ESTADO IN ('ENTREGADO','CANCELADO','FALLIDO','NO_ENTREGADO')"
    )
    params = [emp_id, chofer['CHO_ID']]
    sql += ' ORDER BY PED_FECHA_PEDIDO DESC LIMIT 300'
    rows = query(sql, params)

    if period in ('today', 'week', 'month'):
        now = datetime.utcnow()
        if period == 'today':
            cutoff = str(now.date())
            rows = [r for r in rows if str(r.get('PED_FECHA_PEDIDO') or '')[:10] == cutoff]
        elif period == 'week':
            cutoff = (now - timedelta(days=7)).date().isoformat()
            rows = [r for r in rows if str(r.get('PED_FECHA_PEDIDO') or '')[:10] >= cutoff]
        elif period == 'month':
            cutoff = (now - timedelta(days=30)).date().isoformat()
            rows = [r for r in rows if str(r.get('PED_FECHA_PEDIDO') or '')[:10] >= cutoff]

    return jsonify([_map_pedido(r, chofer) for r in rows])


@mobile_bp.route('/api/deliveries/<int:delivery_id>', methods=['GET'])
@requiere_rol('chofer', 'admin', 'operacion', 'superadmin', 'cliente')
def mobile_delivery_detail(delivery_id):
    emp_id = _emp_id()
    rows = query('SELECT * FROM PEDIDOS WHERE PED_ID = ? AND EMP_ID = ?', [delivery_id, emp_id])
    if not rows:
        return jsonify({'error': 'Entrega no encontrada'}), 404
    driver = None
    if rows[0].get('CHO_ID'):
        d = query('SELECT * FROM CHOFERES WHERE CHO_ID = ? AND EMP_ID = ?', [rows[0]['CHO_ID'], emp_id])
        driver = d[0] if d else None
    return jsonify(_map_pedido(rows[0], driver))


@mobile_bp.route('/api/deliveries/<int:delivery_id>/status', methods=['PUT', 'POST'])
@requiere_rol('chofer', 'admin', 'operacion', 'superadmin')
def mobile_delivery_status(delivery_id):
    emp_id = _emp_id()
    data = request.json or {}
    status = data.get('status') or data.get('estado')
    if not status:
        return jsonify({'error': 'status requerido'}), 400

    rows = query('SELECT * FROM PEDIDOS WHERE PED_ID = ? AND EMP_ID = ?', [delivery_id, emp_id])
    if not rows:
        return jsonify({'error': 'Entrega no encontrada'}), 404

    if getattr(g, 'rol', None) == 'chofer':
        chofer = _chofer_profile()
        if not chofer or rows[0].get('CHO_ID') != chofer['CHO_ID']:
            # Allow if unassigned but this chofer is taking it
            if rows[0].get('CHO_ID') not in (None, 0, chofer['CHO_ID'] if chofer else None):
                return jsonify({'error': 'No autorizado'}), 403
            if chofer and not rows[0].get('CHO_ID'):
                execute('UPDATE PEDIDOS SET CHO_ID = ? WHERE PED_ID = ? AND EMP_ID = ?',
                        [chofer['CHO_ID'], delivery_id, emp_id])

    historial_obs = ''
    if data.get('evidence_photos'):
        try:
            historial_obs = f"Fotos: {len(data['evidence_photos'])}"
        except Exception:
            historial_obs = ''
    if data.get('cod_amount'):
        historial_obs = (historial_obs + ' | ' if historial_obs else '') + f"COD: {data['cod_amount']}"

    if status == 'ENTREGADO':
        execute(
            """UPDATE PEDIDOS SET PED_ESTADO = ?,
               PED_FECHA_ENTREGA_REAL = COALESCE(CAST(NOW() AS TEXT), PED_FECHA_ENTREGA_REAL),
               PED_CANTIDAD_COBRADA = COALESCE(?, PED_CANTIDAD_COBRADA)
               WHERE PED_ID = ? AND EMP_ID = ?""",
            [status, data.get('cod_amount'), delivery_id, emp_id],
        )
    else:
        execute('UPDATE PEDIDOS SET PED_ESTADO = ? WHERE PED_ID = ? AND EMP_ID = ?',
                [status, delivery_id, emp_id])

    try:
        execute(
            'INSERT INTO PEDIDO_HISTORIAL (PED_ID, HIS_ESTADO, HIS_USUARIO, HIS_OBSERVACIONES) VALUES (?, ?, ?, ?)',
            [delivery_id, status, getattr(g, 'usuario', 'MOBILE'), historial_obs],
        )
    except Exception:
        pass

    rows = query('SELECT * FROM PEDIDOS WHERE PED_ID = ? AND EMP_ID = ?', [delivery_id, emp_id])
    return jsonify({'success': True, 'message': f'Estado actualizado a {status}',
                    'delivery': _map_pedido(rows[0] if rows else None)})


@mobile_bp.route('/api/deliveries/<int:delivery_id>/report', methods=['POST'])
@requiere_rol('chofer', 'admin', 'operacion', 'superadmin')
def mobile_delivery_report(delivery_id):
    emp_id = _emp_id()
    data = request.json or {}
    notes = (data.get('notes') or data.get('nota') or '').strip()
    status = data.get('status') or 'FALLIDO'
    if not notes:
        return jsonify({'error': 'notes requerido'}), 400

    rows = query('SELECT * FROM PEDIDOS WHERE PED_ID = ? AND EMP_ID = ?', [delivery_id, emp_id])
    if not rows:
        return jsonify({'error': 'Entrega no encontrada'}), 404

    execute('UPDATE PEDIDOS SET PED_ESTADO = ? WHERE PED_ID = ? AND EMP_ID = ?',
            [status, delivery_id, emp_id])
    try:
        execute(
            'INSERT INTO PEDIDO_HISTORIAL (PED_ID, HIS_ESTADO, HIS_USUARIO, HIS_OBSERVACIONES) VALUES (?, ?, ?, ?)',
            [delivery_id, status, getattr(g, 'usuario', 'MOBILE'), notes],
        )
    except Exception:
        pass

    try:
        execute(
            '''INSERT INTO INCIDENCIAS (EMP_ID, PED_ID, INC_TIPO, INC_DESCRIPCION, INC_RESUELTA)
               VALUES (?, ?, 'PROBLEMA_ENTREGA', ?, 'N')''',
            [emp_id, delivery_id, notes],
        )
    except Exception:
        pass

    return jsonify({'success': True, 'message': 'Reporte enviado'})


@mobile_bp.route('/api/chofer/stats', methods=['GET'])
@requiere_rol('chofer', 'admin', 'superadmin')
def mobile_chofer_stats():
    emp_id = _emp_id()
    chofer = _chofer_profile()
    if not chofer:
        return jsonify({'today': 0, 'week': 0, 'month': 0, 'rating': 0})

    cho_id = chofer['CHO_ID']
    all_rows = query(
        "SELECT PED_ESTADO, PED_FECHA_PEDIDO FROM PEDIDOS WHERE EMP_ID = ? AND CHO_ID = ?",
        [emp_id, cho_id],
    )
    now = datetime.utcnow()
    today = str(now.date())
    week_cut = (now - timedelta(days=7)).date().isoformat()
    month_cut = (now - timedelta(days=30)).date().isoformat()

    def is_delivered(r):
        return (r.get('PED_ESTADO') or '') == 'ENTREGADO'

    def day_of(r):
        return str(r.get('PED_FECHA_PEDIDO') or '')[:10]

    today_n = sum(1 for r in all_rows if is_delivered(r) and day_of(r) == today)
    week_n = sum(1 for r in all_rows if is_delivered(r) and day_of(r) >= week_cut)
    month_n = sum(1 for r in all_rows if is_delivered(r) and day_of(r) >= month_cut)

    delivered = sum(1 for r in all_rows if is_delivered(r))
    failed = sum(1 for r in all_rows if (r.get('PED_ESTADO') or '') in ('FALLIDO', 'NO_ENTREGADO', 'CANCELADO'))
    total_done = delivered + failed
    rating = round(min(5.0, 4.0 + (delivered / total_done if total_done else 0)), 1) if total_done else 5.0

    return jsonify({'today': today_n, 'week': week_n, 'month': month_n, 'rating': rating})


@mobile_bp.route('/api/gps/update', methods=['POST'])
@requiere_rol('chofer', 'admin', 'operacion', 'superadmin')
def mobile_gps_update():
    emp_id = _emp_id()
    data = request.json or {}
    lat = data.get('latitude', data.get('latitud', data.get('lat')))
    lng = data.get('longitude', data.get('longitud', data.get('lng')))
    if lat is None or lng is None:
        return jsonify({'error': 'latitude/longitude required'}), 400
    try:
        lat = float(lat)
        lng = float(lng)
    except (TypeError, ValueError):
        return jsonify({'error': 'invalid coordinates'}), 400

    chofer = _chofer_profile()
    if not chofer:
        return jsonify({'success': True, 'message': 'GPS recibido (sin perfil chofer)'})

    cho_id = chofer['CHO_ID']
    try:
        speed = data.get('speed')
        if speed is None:
            speed = data.get('velocidad') or 0
        battery = data.get('battery') or data.get('bateria') or 100
        heading = data.get('heading') or data.get('rumbo') or 0
        execute(
            '''INSERT INTO TRACKING (EMP_ID, CHO_ID, TRK_LATITUD, TRK_LONGITUD, TRK_VELOCIDAD, TRK_RUMBO, TRK_BATERIA)
               VALUES (?, ?, ?, ?, ?, ?, ?)''',
            [emp_id, cho_id, lat, lng, float(speed), float(heading), float(battery)],
        )
        execute(
            "UPDATE CHOFERES SET CHO_LAT_ACTUAL=?, CHO_LNG_ACTUAL=? WHERE CHO_ID=? AND EMP_ID=?",
            [lat, lng, cho_id, emp_id],
        )
    except Exception:
        pass

    try:
        from server import socketio
        socketio.emit('driver_location', {
            'choId': cho_id,
            'nombre': chofer.get('CHO_NOMBRE', ''),
            'apellido': chofer.get('CHO_APELLIDO', ''),
            'lat': lat, 'lng': lng,
            'timestamp': datetime.now().isoformat(),
        }, room=f'emp_{emp_id}')
    except Exception:
        pass

    return jsonify({'success': True})


@mobile_bp.route('/api/push/register', methods=['POST'])
@requiere_auth
def mobile_push_register():
    emp_id = _emp_id()
    data = request.json or {}
    token = data.get('push_token') or data.get('token')
    platform = data.get('platform') or 'android'
    role = data.get('role') or getattr(g, 'rol', '')
    if not token:
        return jsonify({'error': 'push_token required'}), 400
    try:
        execute(
            '''CREATE TABLE IF NOT EXISTS MOBILE_PUSH_TOKENS (
                id SERIAL PRIMARY KEY, emp_id INTEGER, usu_id INTEGER,
                push_token TEXT, platform TEXT, role TEXT, created_at TIMESTAMP DEFAULT NOW()
            )''',
            [],
        )
    except Exception:
        try:
            execute(
                '''CREATE TABLE IF NOT EXISTS MOBILE_PUSH_TOKENS (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, emp_id INTEGER, usu_id INTEGER,
                    push_token TEXT, platform TEXT, role TEXT, created_at TEXT
                )''',
                [],
            )
        except Exception:
            pass
    try:
        execute(
            '''INSERT INTO MOBILE_PUSH_TOKENS (emp_id, usu_id, push_token, platform, role)
               VALUES (?, ?, ?, ?, ?)''',
            [emp_id, getattr(g, 'usu_id', None), token, platform, role],
        )
    except Exception:
        pass
    return jsonify({'success': True})


# ========================================
# CLIENTE (shipments)
# ========================================

def _cliente_email():
    usu_id = getattr(g, 'usu_id', None)
    rows = query('SELECT USU_EMAIL, USU_NOMBRE FROM USUARIOS WHERE USU_ID=?', [usu_id])
    if not rows:
        return '', ''
    return (rows[0].get('USU_EMAIL') or '').strip().lower(), (rows[0].get('USU_NOMBRE') or '')


def _map_shipment(row, driver=None):
    m = _map_pedido(row, driver)
    if m:
        m['tracking'] = m['tracking_number']
        m['destination'] = m['destination_address']
        m['origin'] = m['origin_address']
        m['date'] = m['created_at']
    return m


@mobile_bp.route('/api/shipments', methods=['GET'])
@requiere_rol('cliente', 'admin', 'operacion', 'superadmin')
def mobile_shipments_list():
    emp_id = _emp_id()
    rol = getattr(g, 'rol', '')
    limit = request.args.get('limit', 50)
    try:
        limit = min(int(limit), 200)
    except (TypeError, ValueError):
        limit = 50

    if rol == 'cliente':
        email, nombre = _cliente_email()
        sql = 'SELECT * FROM PEDIDOS WHERE EMP_ID = ? AND PED_ESTADO != ?'
        params = [emp_id, 'ELIMINADO']
        if email:
            sql += " AND (LOWER(COALESCE(PED_CLIENTE_EMAIL,'')) = ? OR LOWER(COALESCE(PED_CLIENTE_NOMBRE,'')) = ?)"
            params.extend([email, nombre.lower()])
        else:
            sql += " AND LOWER(COALESCE(PED_CLIENTE_NOMBRE,'')) = ?"
            params.append(nombre.lower())
        sql += ' ORDER BY PED_FECHA_PEDIDO DESC LIMIT ?'
        params.append(limit)
        rows = query(sql, params)
        # Fallback: if no personal orders, show all tenant orders for demo continuity
        if not rows:
            rows = query(
                'SELECT * FROM PEDIDOS WHERE EMP_ID = ? AND PED_ESTADO != ? ORDER BY PED_FECHA_PEDIDO DESC LIMIT ?',
                [emp_id, 'ELIMINADO', limit],
            )
    else:
        rows = query(
            'SELECT * FROM PEDIDOS WHERE EMP_ID = ? AND PED_ESTADO != ? ORDER BY PED_FECHA_PEDIDO DESC LIMIT ?',
            [emp_id, 'ELIMINADO', limit],
        )

    out = []
    for r in rows:
        driver = None
        if r.get('CHO_ID'):
            d = query('SELECT * FROM CHOFERES WHERE CHO_ID=? AND EMP_ID=?', [r['CHO_ID'], emp_id])
            driver = d[0] if d else None
        out.append(_map_shipment(r, driver))
    return jsonify(out)


@mobile_bp.route('/api/shipments/stats', methods=['GET'])
@requiere_rol('cliente', 'admin', 'operacion', 'superadmin')
def mobile_shipments_stats():
    emp_id = _emp_id()
    rows = query(
        "SELECT PED_ESTADO, PED_COSTO_TOTAL FROM PEDIDOS WHERE EMP_ID = ? AND PED_ESTADO != 'ELIMINADO'",
        [emp_id],
    )
    total = len(rows)
    pending = sum(1 for r in rows if (r.get('PED_ESTADO') or '') in ('PENDIENTE', 'ASIGNADO', 'EN_RUTA'))
    delivered = sum(1 for r in rows if (r.get('PED_ESTADO') or '') == 'ENTREGADO')
    total_spent = sum(float(r.get('PED_COSTO_TOTAL') or 0) for r in rows)
    return jsonify({
        'total': total,
        'totalShipments': total,
        'pending': pending,
        'pendientes': pending,
        'delivered': delivered,
        'entregados': delivered,
        'totalSpent': total_spent,
        'thisMonth': total,
    })


@mobile_bp.route('/api/shipments/<int:shipment_id>', methods=['GET'])
@requiere_rol('cliente', 'chofer', 'admin', 'operacion', 'superadmin')
def mobile_shipment_detail(shipment_id):
    emp_id = _emp_id()
    rows = query('SELECT * FROM PEDIDOS WHERE PED_ID = ? AND EMP_ID = ?', [shipment_id, emp_id])
    if not rows:
        return jsonify({'error': 'Envío no encontrado'}), 404
    driver = None
    if rows[0].get('CHO_ID'):
        d = query('SELECT * FROM CHOFERES WHERE CHO_ID = ? AND EMP_ID = ?', [rows[0]['CHO_ID'], emp_id])
        driver = d[0] if d else None
    return jsonify(_map_shipment(rows[0], driver))


@mobile_bp.route('/api/shipments', methods=['POST'])
@requiere_rol('cliente', 'admin', 'operacion', 'superadmin')
def mobile_shipment_create():
    emp_id = _emp_id()
    p = request.json or {}
    dest_dir = p.get('destination_address') or p.get('destinoDir') or p.get('destino') or ''
    if not dest_dir:
        return jsonify({'error': 'destination_address requerido'}), 400

    destino_lat = p.get('dest_lat')
    destino_lon = p.get('dest_lng')
    origen_dir = p.get('origin_address') or p.get('origen') or ''
    email, nombre_default = _cliente_email()
    cliente_nombre = p.get('destination_contact') or p.get('clienteNombre') or nombre_default
    cliente_tel = p.get('destination_phone') or p.get('clienteTelefono') or ''

    if destino_lat is None and destino_lon is None:
        try:
            from server import _geocode_address
            destino_lat, destino_lon = _geocode_address(dest_dir)
        except Exception:
            pass

    try:
        numero = f"LM-{int(datetime.utcnow().timestamp())}"
    except Exception:
        numero = 'LM-MOBILE'

    service = (p.get('service_type') or 'estandar').upper()
    if service == 'EXPRESS':
        service = 'EXPRESS'
    elif service == 'ECONOMICO':
        service = 'ECONOMICO'
    else:
        service = 'ESTANDAR'

    execute(
        '''INSERT INTO PEDIDOS (
            EMP_ID, PED_NUMERO, PED_CLIENTE_NOMBRE, PED_CLIENTE_TELEFONO, PED_CLIENTE_EMAIL,
            PED_ORIGEN_DIR, PED_DESTINO_DIR, PED_DESTINO_COL, PED_DESTINO_CIUDAD,
            PED_PESO_KG, PED_BULTOS, PED_DESCRIPCION, PED_VALOR_DECLARADO, PED_COSTO_TOTAL,
            PED_FORMA_PAGO, PED_MONEDA, PED_TIPO_ENVIO, PED_PAGO_ESTATUS, PED_ESTADO,
            PED_PRIORIDAD, PED_DESTINO_LAT, PED_DESTINO_LON
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
        [
            emp_id, numero, cliente_nombre, cliente_tel, email or p.get('origin_contact_email') or '',
            origen_dir, dest_dir, p.get('dest_colonia') or '', p.get('dest_city') or '',
            float(p.get('weight_kg') or 0), 1, p.get('description') or '',
            float(p.get('declared_value') or 0), float(p.get('estimated_cost') or p.get('costoTotal') or 85),
            (p.get('payment_method') or 'EFECTIVO').upper(), 'MXN', service,
            'PENDIENTE', 'PENDIENTE', 'NORMAL', destino_lat, destino_lon,
        ],
    )

    created = query(
        'SELECT * FROM PEDIDOS WHERE EMP_ID = ? AND PED_NUMERO = ? ORDER BY PED_ID DESC LIMIT 1',
        [emp_id, numero],
    )
    return jsonify({'success': True, 'shipment': _map_shipment(created[0] if created else None),
                    'message': 'Envío creado'})


@mobile_bp.route('/api/shipments/<int:shipment_id>', methods=['DELETE'])
@requiere_rol('cliente', 'admin', 'operacion', 'superadmin')
def mobile_shipment_delete(shipment_id):
    emp_id = _emp_id()
    rows = query('SELECT * FROM PEDIDOS WHERE PED_ID = ? AND EMP_ID = ?', [shipment_id, emp_id])
    if not rows:
        return jsonify({'error': 'Envío no encontrado'}), 404
    execute("UPDATE PEDIDOS SET PED_ESTADO = 'CANCELADO' WHERE PED_ID = ? AND EMP_ID = ?",
            [shipment_id, emp_id])
    try:
        execute(
            'INSERT INTO PEDIDO_HISTORIAL (PED_ID, HIS_ESTADO, HIS_USUARIO) VALUES (?, ?, ?)',
            [shipment_id, 'CANCELADO', getattr(g, 'usuario', 'MOBILE')],
        )
    except Exception:
        pass
    return jsonify({'success': True, 'message': 'Envío cancelado'})


@mobile_bp.route('/api/invoices', methods=['GET'])
@requiere_rol('cliente', 'admin', 'operacion', 'superadmin')
def mobile_invoices():
    emp_id = _emp_id()
    try:
        rows = query(
            '''SELECT FAC_ID, FAC_SERIE, FAC_FOLIO, FAC_TOTAL, FAC_SUBTOTAL, FAC_TOTAL_IVA,
                      FAC_ESTATUS, FAC_FECHA_EMISION, FAC_RECEPTOR_RAZON, FAC_RECEPTOR_EMAIL
               FROM CFDI_FACTURAS WHERE EMP_ID = ? ORDER BY FAC_FECHA_EMISION DESC LIMIT 100''',
            [emp_id],
        )
    except Exception:
        rows = []

    out = []
    for r in rows:
        estatus = (r.get('FAC_ESTATUS') or 'PENDIENTE').upper()
    if estatus in ('PAGADA', 'TIMBRADA', 'PAGADO', 'PAID'):
        status = 'PAID'
    elif estatus in ('CANCELADA', 'CANCELLED'):
        status = 'CANCELLED'
    else:
        status = 'PENDING'

    out.append({
            'id': r.get('FAC_ID'),
            'serie': r.get('FAC_SERIE'),
            'folio': r.get('FAC_FOLIO'),
            'number': f"{r.get('FAC_SERIE') or ''}-{r.get('FAC_FOLIO') or ''}",
            'total': r.get('FAC_TOTAL') or 0,
            'amount': r.get('FAC_TOTAL') or 0,
            'subtotal': r.get('FAC_SUBTOTAL') or 0,
            'iva': r.get('FAC_TOTAL_IVA') or 0,
            'status': status,
            'estado': estatus,
            'created_at': str(r.get('FAC_FECHA_EMISION') or ''),
            'date': str(r.get('FAC_FECHA_EMISION') or ''),
            'receiver': r.get('FAC_RECEPTOR_RAZON') or '',
        })
    return jsonify(out)


@mobile_bp.route('/api/location/report', methods=['POST'])
@requiere_auth
def mobile_location_report():
    data = request.json or {}
    if data.get('latitude') is not None and data.get('longitude') is not None:
        return mobile_gps_update()
    return jsonify({'success': True})
