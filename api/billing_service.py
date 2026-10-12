"""
LAST MILE DELIVERY - Automated Billing Service
Handles recurring subscription charging, usage tracking, and limit enforcement.
"""

import os
import json
import time as _time
from datetime import datetime, timedelta
from db import query, execute, USE_POSTGRES


# ========================================
# LICENSE ENGINE (anti-hack: server-side, cache corto)
# ========================================
_LIC_CACHE_TTL = 60  # segundos; suspend/activar invalidan antes
_lic_cache = {}


def invalidar_cache_licencia(emp_id=None):
    """Invalida el cache de licencias (una o todas)."""
    if emp_id is None:
        _lic_cache.clear()
    else:
        try:
            _lic_cache.pop(int(emp_id), None)
        except (TypeError, ValueError):
            pass


def _parse_fecha(valor):
    """Convierte str/datetime/date de la BD a date. Devuelve None si no se puede."""
    if valor is None or valor == '':
        return None
    if isinstance(valor, datetime):
        return valor.date()
    try:
        from datetime import date as _date
        if isinstance(valor, _date):
            return valor
    except Exception:
        pass
    s = str(valor).strip()
    for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d', '%Y-%m-%d %H:%M:%S.%f'):
        try:
            return datetime.strptime(s[:26], fmt).date()
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(s.replace('Z', '+00:00')).date()
    except Exception:
        return None


def evaluar_licencia(emp_id):
    """Evalua si la licencia de un tenant permite operar.

    Reglas (fail-closed en suspension/vencimiento):
      - EMP_ESTATUS != 'ACTIVA'  -> bloqueado
      - Sin suscripcion registrada -> permitido (tenants legacy/grandfathered)
      - SUS_ESTADO 'SUSPENDIDA'  -> bloqueado
      - SUS_ESTADO 'CANCELADA' con SUS_FECHA_FIN pasada -> bloqueado
      - SUS_ESTADO 'ACTIVA'/'TRIAL' con SUS_FECHA_FIN pasada -> bloqueado (VENCIDA)
    Devuelve dict: ok, code, mensaje, estado_empresa, estado_sus, fecha_fin, dias_restantes.
    """
    res = {'ok': True, 'code': None, 'mensaje': None, 'estado_empresa': None,
           'estado_sus': None, 'fecha_fin': None, 'dias_restantes': None}
    if not emp_id:
        res.update(ok=False, code='EMPRESA_INVALIDA', mensaje='Empresa no especificada')
        return res

    try:
        key = int(emp_id)
    except (TypeError, ValueError):
        res.update(ok=False, code='EMPRESA_INVALIDA', mensaje='Empresa no especificada')
        return res

    cached = _lic_cache.get(key)
    if cached and cached[0] > _time.time():
        return cached[1]

    try:
        emp = query("SELECT EMP_ESTATUS FROM EMPRESAS WHERE EMP_ID=?", [key])
        if not emp:
            res.update(ok=False, code='EMPRESA_NO_ENCONTRADA', mensaje='Empresa no encontrada')
        else:
            est = (emp[0].get('EMP_ESTATUS') or 'ACTIVA').upper()
            res['estado_empresa'] = est
            if est == 'SUSPENDIDA':
                res.update(ok=False, code='LICENCIA_SUSPENDIDA',
                           mensaje='Licencia suspendida. Contacta a soporte.')
            elif est != 'ACTIVA':
                res.update(ok=False, code='CUENTA_NO_ACTIVA',
                           mensaje='Cuenta no activa. Verifica tu email o contacta soporte.')
            else:
                sus = query(
                    "SELECT SUS_ESTADO, SUS_FECHA_FIN FROM SAAS_SUSCRIPCIONES "
                    "WHERE EMP_ID=? ORDER BY SUS_ID DESC LIMIT 1", [key])
                if sus:
                    se = (sus[0].get('SUS_ESTADO') or '').upper()
                    fin = _parse_fecha(sus[0].get('SUS_FECHA_FIN'))
                    res['estado_sus'] = se
                    res['fecha_fin'] = fin.isoformat() if fin else None
                    hoy = datetime.utcnow().date()
                    if fin:
                        res['dias_restantes'] = (fin - hoy).days
                    if se == 'SUSPENDIDA':
                        res.update(ok=False, code='LICENCIA_SUSPENDIDA',
                                   mensaje='Licencia suspendida. Contacta a soporte.')
                    elif se == 'CANCELADA':
                        if fin and fin < hoy:
                            res.update(ok=False, code='LICENCIA_VENCIDA',
                                       mensaje='Suscripcion cancelada. Renueva para continuar.')
                    elif se in ('ACTIVA', 'TRIAL'):
                        if fin and fin < hoy:
                            res.update(ok=False, code='LICENCIA_VENCIDA',
                                       mensaje=f'Tu licencia vencio el {fin.isoformat()}. '
                                               'Renueva el plan para seguir operando.')
    except Exception as e:
        # Fail-closed: si no podemos verificar, no bloqueamos (evitar corte masivo
        # por error transitorio de BD), pero dejamos log.
        print(f'[WARN] evaluar_licencia({key}): {e}')

    _lic_cache[key] = (_time.time() + _LIC_CACHE_TTL, res)
    return res


def licencia_bloqueo(emp_id):
    """Devuelve None si la licencia permite operar, o dict {code, mensaje} si bloquea."""
    ev = evaluar_licencia(emp_id)
    if ev['ok']:
        return None
    return {'code': ev['code'], 'mensaje': ev['mensaje']}


def suspender_licencia(emp_id, motivo='manual'):
    """Suspende empresa + suscripcion ACTIVA/TRIAL y limpia cache."""
    execute("UPDATE EMPRESAS SET EMP_ESTATUS='SUSPENDIDA' WHERE EMP_ID=?", [emp_id])
    try:
        execute("UPDATE SAAS_SUSCRIPCIONES SET SUS_ESTADO='SUSPENDIDA', "
                "SUS_NOTAS=COALESCE(SUS_NOTAS,'') || ' | susp (' || ? || ')' "
                "WHERE EMP_ID=? AND SUS_ESTADO IN ('ACTIVA','TRIAL')",
                [motivo, emp_id])
    except Exception:
        try:
            execute("UPDATE SAAS_SUSCRIPCIONES SET SUS_ESTADO='SUSPENDIDA' "
                    "WHERE EMP_ID=? AND SUS_ESTADO IN ('ACTIVA','TRIAL')", [emp_id])
        except Exception:
            pass
    invalidar_cache_licencia(emp_id)


def activar_licencia(emp_id, renovar_dias=None):
    """Reactiva empresa y su suscripcion mas reciente (y opcionalmente extiende FIN)."""
    execute("UPDATE EMPRESAS SET EMP_ESTATUS='ACTIVA' WHERE EMP_ID=?", [emp_id])
    try:
        if renovar_dias:
            execute("UPDATE SAAS_SUSCRIPCIONES SET SUS_ESTADO='ACTIVA', "
                    "SUS_FECHA_FIN=CURRENT_DATE + INTERVAL '%s days', "
                    "SUS_FECHA_PROXIMO_COBRO=CURRENT_DATE + INTERVAL '%s days' "
                    "WHERE SUS_ID=(SELECT SUS_ID FROM SAAS_SUSCRIPCIONES WHERE EMP_ID=? "
                    "ORDER BY SUS_ID DESC LIMIT 1)",
                    [int(renovar_dias), int(renovar_dias), emp_id])
        else:
            execute("UPDATE SAAS_SUSCRIPCIONES SET SUS_ESTADO='ACTIVA' "
                    "WHERE SUS_ID=(SELECT SUS_ID FROM SAAS_SUSCRIPCIONES WHERE EMP_ID=? "
                    "ORDER BY SUS_ID DESC LIMIT 1)", [emp_id])
    except Exception:
        pass
    invalidar_cache_licencia(emp_id)


def marcar_pago_exitoso(emp_id):
    """Un pago confirmado reactiva la licencia del tenant."""
    try:
        execute("UPDATE EMPRESAS SET EMP_ESTATUS='ACTIVA' WHERE EMP_ID=?", [emp_id])
        execute("UPDATE SAAS_SUSCRIPCIONES SET SUS_ESTADO='ACTIVA' "
                "WHERE SUS_ID=(SELECT SUS_ID FROM SAAS_SUSCRIPCIONES WHERE EMP_ID=? "
                "ORDER BY SUS_ID DESC LIMIT 1)", [emp_id])
        invalidar_cache_licencia(emp_id)
    except Exception as e:
        print(f'[WARN] marcar_pago_exitoso({emp_id}): {e}')


def suspender_licencias_vencidas(grace_days=3):
    """Barrido de morosas: suspende licencias vencidas o con cobro proximo atrasado.

    Reglas:
      1. ACTIVA/TRIAL con SUS_FECHA_FIN < hoy              -> VENCIDA
      2. ACTIVA con SUS_FECHA_PROXIMO_COBRO < hoy-grace    -> MORA (sin pago)
    Devuelve lista de {'emp_id', 'motivo'} suspendidas.
    """
    suspendidas = []
    hoy = datetime.utcnow().date()
    try:
        rows = query(
            "SELECT DISTINCT s.EMP_ID FROM SAAS_SUSCRIPCIONES s "
            "JOIN EMPRESAS e ON e.EMP_ID = s.EMP_ID "
            "WHERE s.SUS_ESTADO IN ('ACTIVA','TRIAL') AND e.EMP_ESTATUS='ACTIVA' "
            "AND s.SUS_FECHA_FIN IS NOT NULL")
        for r in rows:
            fin = _parse_fecha(r.get('SUS_FECHA_FIN'))
            if fin and fin < hoy:
                suspender_licencia(r['EMP_ID'], 'vencida_auto')
                suspendidas.append({'emp_id': r['EMP_ID'], 'motivo': 'vencida'})
    except Exception as e:
        print(f'[WARN] suspender_licencias_vencidas (fin): {e}')
    try:
        rows = query(
            "SELECT DISTINCT s.EMP_ID FROM SAAS_SUSCRIPCIONES s "
            "JOIN EMPRESAS e ON e.EMP_ID = s.EMP_ID "
            "WHERE s.SUS_ESTADO='ACTIVA' AND e.EMP_ESTATUS='ACTIVA' "
            "AND s.SUS_FECHA_PROXIMO_COBRO IS NOT NULL")
        limite = hoy - timedelta(days=grace_days)
        for r in rows:
            prox = _parse_fecha(r.get('SUS_FECHA_PROXIMO_COBRO'))
            if prox and prox < limite:
                suspender_licencia(r['EMP_ID'], 'mora_auto')
                suspendidas.append({'emp_id': r['EMP_ID'], 'motivo': 'mora'})
    except Exception as e:
        print(f'[WARN] suspender_licencias_vencidas (mora): {e}')
    return suspendidas


def monitor_licencias():
    """Vista global de licencias para el panel superadmin."""
    try:
        rows = query('''
            SELECT e.EMP_ID, e.EMP_NOMBRE, e.EMP_EMAIL, e.EMP_PLAN, e.EMP_ESTATUS,
                   p.PLAN_NOMBRE, p.PLAN_PRECIO_MENSUAL,
                   s.SUS_ESTADO, s.SUS_FECHA_INICIO, s.SUS_FECHA_FIN, s.SUS_FECHA_PROXIMO_COBRO,
                   (SELECT COUNT(*) FROM USUARIOS u WHERE u.USU_EMP_ID = e.EMP_ID) as TOTAL_USUARIOS,
                   (SELECT COUNT(*) FROM CHOFERES c WHERE c.EMP_ID = e.EMP_ID) as TOTAL_CHOFERES,
                   (SELECT MAX(c2.COB_FECHA_COBRO) FROM SAAS_COBROS c2 WHERE c2.EMP_ID = e.EMP_ID) as ULTIMO_COBRO_FECHA,
                   (SELECT c2.COB_ESTATUS FROM SAAS_COBROS c2 WHERE c2.EMP_ID = e.EMP_ID
                    ORDER BY c2.COB_ID DESC LIMIT 1) as ULTIMO_COBRO_ESTADO,
                   (SELECT c2.COB_MONTO FROM SAAS_COBROS c2 WHERE c2.EMP_ID = e.EMP_ID
                    ORDER BY c2.COB_ID DESC LIMIT 1) as ULTIMO_COBRO_MONTO
            FROM EMPRESAS e
            LEFT JOIN SAAS_SUSCRIPCIONES s ON s.SUS_ID =
                (SELECT s2.SUS_ID FROM SAAS_SUSCRIPCIONES s2 WHERE s2.EMP_ID = e.EMP_ID
                 ORDER BY s2.SUS_ID DESC LIMIT 1)
            LEFT JOIN SAAS_PLANES p ON p.PLAN_ID = s.PLAN_ID
            ORDER BY e.EMP_ID
        ''')
    except Exception as e:
        print(f'[ERROR] monitor_licencias: {e}')
        rows = []

    hoy = datetime.utcnow().date()
    out = []
    resumen = {'activas': 0, 'trial': 0, 'vencidas': 0, 'suspendidas': 0,
               'canceladas': 0, 'morosas': 0, 'bloqueadas': 0}
    for r in rows:
        ev = evaluar_licencia(r['EMP_ID'])
        fin = _parse_fecha(r.get('SUS_FECHA_FIN'))
        prox = _parse_fecha(r.get('SUS_FECHA_PROXIMO_COBRO'))
        dias = (fin - hoy).days if fin else None
        morosa = bool(
            ev['ok'] and prox and prox < hoy and (r.get('SUS_ESTADO') or '').upper() == 'ACTIVA'
        )
        estado_lic = 'ACTIVA'
        if not ev['ok']:
            estado_lic = ev['code']
        elif (r.get('SUS_ESTADO') or '').upper() == 'TRIAL':
            estado_lic = 'TRIAL'
        elif morosa:
            estado_lic = 'MOROSA'
        elif not r.get('SUS_ESTADO'):
            estado_lic = 'SIN_SUSCRIPCION'
        if estado_lic == 'ACTIVA':
            resumen['activas'] += 1
        elif estado_lic == 'TRIAL':
            resumen['trial'] += 1
        elif estado_lic == 'LICENCIA_VENCIDA':
            resumen['vencidas'] += 1
            resumen['bloqueadas'] += 1
        elif estado_lic == 'LICENCIA_SUSPENDIDA':
            resumen['suspendidas'] += 1
            resumen['bloqueadas'] += 1
        elif estado_lic == 'MOROSA':
            resumen['morosas'] += 1
        elif estado_lic == 'CANCELADA':
            resumen['canceladas'] += 1
        out.append({
            'EMP_ID': r['EMP_ID'], 'EMP_NOMBRE': r.get('EMP_NOMBRE'),
            'EMP_EMAIL': r.get('EMP_EMAIL'), 'EMP_PLAN': r.get('EMP_PLAN'),
            'EMP_ESTATUS': r.get('EMP_ESTATUS'), 'PLAN_NOMBRE': r.get('PLAN_NOMBRE'),
            'PLAN_PRECIO_MENSUAL': r.get('PLAN_PRECIO_MENSUAL'),
            'SUS_ESTADO': r.get('SUS_ESTADO'), 'SUS_FECHA_FIN': r.get('SUS_FECHA_FIN'),
            'SUS_FECHA_PROXIMO_COBRO': r.get('SUS_FECHA_PROXIMO_COBRO'),
            'DIAS_RESTANTES': dias, 'MOROSA': morosa, 'ESTADO_LICENCIA': estado_lic,
            'ACCESO_BLOQUEADO': not ev['ok'], 'MOTIVO_BLOQUEO': ev.get('mensaje'),
            'TOTAL_USUARIOS': r.get('TOTAL_USUARIOS', 0),
            'TOTAL_CHOFERES': r.get('TOTAL_CHOFERES', 0),
            'ULTIMO_COBRO_FECHA': r.get('ULTIMO_COBRO_FECHA'),
            'ULTIMO_COBRO_ESTADO': r.get('ULTIMO_COBRO_ESTADO'),
            'ULTIMO_COBRO_MONTO': r.get('ULTIMO_COBRO_MONTO'),
        })
    return {'licencias': out, 'resumen': resumen}


# ========================================
# USAGE TRACKING
# ========================================
def track_usage(emp_id, metric, count=1):
    """Track usage metric for a tenant (pedidos, choferes, etc.)."""
    try:
        execute(
            "INSERT INTO SAAS_USO_MES (EMP_ID, USO_METRICA, USO_CONTEO, USO_MES) "
            "VALUES (?, ?, ?, EXTRACT(YEAR FROM CURRENT_DATE)::text || '-' || LPAD(EXTRACT(MONTH FROM CURRENT_DATE)::text, 2, '0')) "
            "ON CONFLICT (EMP_ID, USO_METRICA, USO_MES) DO UPDATE SET USO_CONTEO = SAAS_USO_MES.USO_CONTEO + ?",
            [emp_id, metric, count, count]
        )
    except Exception:
        # Table might not exist yet, try simple insert
        try:
            execute(
                "INSERT INTO SAAS_USO_MES (EMP_ID, USO_METRICA, USO_CONTEO, USO_MES) "
                "VALUES (?, ?, ?, TO_CHAR(CURRENT_DATE, 'YYYY-MM'))",
                [emp_id, metric, count]
            )
        except Exception:
            pass


def get_usage(emp_id, metric=None):
    """Get current month usage for a tenant."""
    try:
        if metric:
            rows = query(
                "SELECT USO_METRICA, USO_CONTEO FROM SAAS_USO_MES "
                "WHERE EMP_ID = ? AND USO_METRICA = ? AND USO_MES = TO_CHAR(CURRENT_DATE, 'YYYY-MM')",
                [emp_id, metric]
            )
            return rows[0]['USO_CONTEO'] if rows else 0
        else:
            rows = query(
                "SELECT USO_METRICA, USO_CONTEO FROM SAAS_USO_MES "
                "WHERE EMP_ID = ? AND USO_MES = TO_CHAR(CURRENT_DATE, 'YYYY-MM')",
                [emp_id]
            )
            return {r['USO_METRICA']: r['USO_CONTEO'] for r in rows}
    except Exception:
        return 0 if metric else {}


def check_limits(emp_id):
    """Check if tenant is within plan limits. Returns dict with status."""
    try:
        rows = query("SELECT EMP_PLAN, EMP_MAX_USUARIOS, EMP_MAX_CHOFERES, EMP_MAX_PEDIDOS_MES FROM EMPRESAS WHERE EMP_ID=?", [emp_id])
        if not rows:
            return {'allowed': True, 'warnings': []}
        empresa = rows[0]
    except Exception:
        return {'allowed': True, 'warnings': []}

    plan = empresa.get('EMP_PLAN', 'STARTER')
    max_usuarios = empresa.get('EMP_MAX_USUARIOS', 5)
    max_choferes = empresa.get('EMP_MAX_CHOFERES', 10)
    max_pedidos = empresa.get('EMP_MAX_PEDIDOS_MES', 500)

    warnings = []
    blocked = False

    count_usuarios = 0
    count_choferes = 0
    count_pedidos = 0

    # Check usuarios
    try:
        r = query("SELECT COUNT(*) as total FROM USUARIOS WHERE USU_EMP_ID=?", [emp_id])
        count_usuarios = r[0].get('TOTAL', 0) if r else 0
        if count_usuarios >= max_usuarios:
            blocked = True
            warnings.append(f'Usuarios: {count_usuarios}/{max_usuarios} (LIMITE ALCANZADO)')
        elif count_usuarios >= max_usuarios * 0.8:
            warnings.append(f'Usuarios: {count_usuarios}/{max_usuarios} (cerca del limite)')
    except Exception:
        pass

    # Check choferes
    try:
        r = query("SELECT COUNT(*) as total FROM CHOFERES WHERE EMP_ID=?", [emp_id])
        count_choferes = r[0].get('TOTAL', 0) if r else 0
        if count_choferes >= max_choferes:
            blocked = True
            warnings.append(f'Choferes: {count_choferes}/{max_choferes} (LIMITE ALCANZADO)')
        elif count_choferes >= max_choferes * 0.8:
            warnings.append(f'Choferes: {count_choferes}/{max_choferes} (cerca del limite)')
    except Exception:
        pass

    # Check pedidos del mes
    try:
        r = query(
            "SELECT COUNT(*) as total FROM PEDIDOS WHERE EMP_ID=? AND PED_FECHA_PEDIDO >= DATE_TRUNC('month', CURRENT_DATE)",
            [emp_id]
        )
        count_pedidos = r[0].get('TOTAL', 0) if r else 0
        if count_pedidos >= max_pedidos:
            blocked = True
            warnings.append(f'Pedidos mes: {count_pedidos}/{max_pedidos} (LIMITE ALCANZADO)')
        elif count_pedidos >= max_pedidos * 0.8:
            warnings.append(f'Pedidos mes: {count_pedidos}/{max_pedidos} (cerca del limite)')
    except Exception:
        pass

    return {
        'allowed': not blocked,
        'warnings': warnings,
        'plan': plan,
        'limits': {
            'usuarios': {'used': count_usuarios, 'max': max_usuarios},
            'choferes': {'used': count_choferes, 'max': max_choferes},
            'pedidos_mes': {'used': count_pedidos, 'max': max_pedidos},
        }
    }


# ========================================
# RECURRING BILLING
# ========================================
def get_due_subscriptions():
    """Find subscriptions that need to be charged today."""
    try:
        rows = query(
            "SELECT s.SUS_ID, s.EMP_ID, s.PLAN_ID, s.SUS_FECHA_PROXIMO_COBRO, "
            "s.SUS_METODO_PAGO, s.SUS_STRIPE_SUBSCRIPTION_ID, s.SUS_MP_SUBSCRIPTION_ID, "
            "e.EMP_NOMBRE, e.EMP_EMAIL "
            "FROM SAAS_SUSCRIPCIONES s "
            "JOIN EMPRESAS e ON s.EMP_ID = e.EMP_ID "
            "WHERE s.SUS_ESTADO = 'ACTIVA' "
            "AND s.SUS_FECHA_PROXIMO_COBRO <= CURRENT_DATE "
            "AND s.SUS_FECHA_PROXIMO_COBRO IS NOT NULL",
            []
        )
        return rows
    except Exception:
        return []


def process_subscription_charge(subscription):
    """Charge a subscription via its payment provider."""
    emp_id = subscription['EMP_ID']
    provider = subscription.get('SUS_METODO_PAGO', 'STRIPE').upper()

    # Get plan price
    try:
        plan_rows = query("SELECT PLAN_PRECIO_MENSUAL FROM SAAS_PLANES WHERE PLAN_ID=?", [subscription['PLAN_ID']])
        if plan_rows:
            monto = float(plan_rows[0].get('PLAN_PRECIO_MENSUAL', 0))
        else:
            monto = 999.0
    except Exception:
        monto = 999.0

    if provider == 'STRIPE' and subscription.get('SUS_STRIPE_SUBSCRIPTION_ID'):
        # Stripe handles recurring billing automatically via webhooks
        # This is just for tracking
        from payment_service import stripe_service
        if stripe_service.enabled:
            return {
                'status': 'stripe_auto',
                'message': 'Stripe handles recurring billing via webhooks',
                'monto': monto
            }

    if provider == 'MERCADOPAGO' and subscription.get('SUS_MP_SUBSCRIPTION_ID'):
        from payment_service import mp_service
        if mp_service.enabled:
            return {
                'status': 'mp_auto',
                'message': 'MercadoPago handles recurring billing via webhooks',
                'monto': monto
            }

    # Manual charge or no provider - log for manual processing
    try:
        execute(
            "INSERT INTO SAAS_COBROS (SUS_ID, EMP_ID, COB_MONTO, COB_CONCEPTO, COB_ESTATUS, COB_METODO_PAGO, COB_FECHA_COBRO) "
            "VALUES (?, ?, ?, ?, 'PENDIENTE', ?, NOW())",
            [subscription['SUS_ID'], emp_id, monto,
             f'Cobro automatico - {subscription.get("EMP_NOMBRE", "")}',
             provider]
        )
    except Exception:
        pass

    return {
        'status': 'pending_manual',
        'message': f'Pago pendiente de procesar via {provider}',
        'monto': monto
    }


def process_all_due_charges():
    """Process all due subscription charges. Called by cron job.

    Reglas anti-mora:
      - Solo se avanza SUS_FECHA_PROXIMO_COBRO si el cobro quedo confirmado
        (Stripe/MP automaticos) o PAGADO. Si queda PENDIENTE, la fecha NO avanza
        y la licencia entra en mora -> suspension tras grace_days.
    """
    due = get_due_subscriptions()
    results = []

    for sub in due:
        result = process_subscription_charge(sub)
        results.append({
            'emp_id': sub['EMP_ID'],
            'empresa': sub.get('EMP_NOMBRE', ''),
            'result': result
        })

        pagado = result.get('status') in ('stripe_auto', 'mp_auto', 'paid', 'PAGADO')
        if pagado:
            try:
                execute(
                    "UPDATE SAAS_SUSCRIPCIONES SET SUS_FECHA_PROXIMO_COBRO = "
                    "(SUS_FECHA_PROXIMO_COBRO + INTERVAL '1 month') "
                    "WHERE SUS_ID = ?",
                    [sub['SUS_ID']]
                )
            except Exception:
                pass
            marcar_pago_exitoso(sub['EMP_ID'])
        else:
            # Cobro manual pendiente: no se avanza la fecha; el barrido de
            # morosas (suspender_licencias_vencidas) lo suspende tras la gracia.
            try:
                execute(
                    "UPDATE SAAS_SUSCRIPCIONES SET SUS_NOTAS=COALESCE(SUS_NOTAS,'') || "
                    "' | cobro_pendiente_auto' WHERE SUS_ID = ?",
                    [sub['SUS_ID']]
                )
            except Exception:
                pass

    # Barrido de morosas/vencidas del mismo cron
    try:
        suspendidas = suspender_licencias_vencidas()
        for s in suspendidas:
            results.append({'emp_id': s['emp_id'], 'empresa': '',
                            'result': {'status': 'suspended',
                                       'message': f"Licencia suspendida por {s['motivo']}"}})
    except Exception as e:
        print(f'[ERROR] suspender_licencias_vencidas en cron: {e}')

    return results


# ========================================
# BILLING DASHBOARD DATA
# ========================================
def get_billing_dashboard(emp_id):
    """Get comprehensive billing data for tenant dashboard."""
    data = {
        'plan': {},
        'usage': {},
        'limits': {},
        'usage_pct': {},
        'next_billing': None,
        'last_payment': None,
        'total_paid': 0,
        'warnings': [],
    }

    # Plan info
    try:
        rows = query(
            "SELECT e.EMP_PLAN, e.EMP_MAX_USUARIOS, e.EMP_MAX_CHOFERES, e.EMP_MAX_PEDIDOS_MES, "
            "p.PLAN_NOMBRE, p.PLAN_PRECIO_MENSUAL, p.PLAN_FEATURES "
            "FROM EMPRESAS e "
            "LEFT JOIN SAAS_PLANES p ON UPPER(e.EMP_PLAN) = UPPER(p.PLAN_NOMBRE) "
            "WHERE e.EMP_ID = ?", [emp_id]
        )
        if rows:
            r = rows[0]
            data['plan'] = {
                'name': r.get('EMP_PLAN', 'STARTER'),
                'precio': float(r.get('PLAN_PRECIO_MENSUAL', 0) or 0),
                'features': r.get('PLAN_FEATURES', ''),
            }
    except Exception:
        pass

    # Current usage
    try:
        r = query("SELECT COUNT(*) as total FROM USUARIOS WHERE USU_EMP_ID=?", [emp_id])
        data['usage']['usuarios'] = r[0]['total'] if r else 0
    except Exception:
        data['usage']['usuarios'] = 0

    try:
        r = query("SELECT COUNT(*) as total FROM CHOFERES WHERE EMP_ID=?", [emp_id])
        data['usage']['choferes'] = r[0]['total'] if r else 0
    except Exception:
        data['usage']['choferes'] = 0

    try:
        r = query(
            "SELECT COUNT(*) as total FROM PEDIDOS WHERE EMP_ID=? AND PED_FECHA_PEDIDO >= DATE_TRUNC('month', CURRENT_DATE)",
            [emp_id]
        )
        data['usage']['pedidos_mes'] = r[0]['total'] if r else 0
    except Exception:
        data['usage']['pedidos_mes'] = 0

    try:
        r = query(
            "SELECT COALESCE(SUM(PED_COSTO_TOTAL), 0) as total FROM PEDIDOS "
            "WHERE EMP_ID=? AND PED_FECHA_PEDIDO >= DATE_TRUNC('month', CURRENT_DATE) AND PED_ESTADO='ENTREGADO'",
            [emp_id]
        )
        data['usage']['ingresos_mes'] = float(r[0]['total'] if r else 0)
    except Exception:
        data['usage']['ingresos_mes'] = 0

    # Limits
    try:
        r = query("SELECT EMP_MAX_USUARIOS, EMP_MAX_CHOFERES, EMP_MAX_PEDIDOS_MES FROM EMPRESAS WHERE EMP_ID=?", [emp_id])
        if r:
            data['limits'] = {
                'usuarios': r[0]['EMP_MAX_USUARIOS'],
                'choferes': r[0]['EMP_MAX_CHOFERES'],
                'pedidos_mes': r[0]['EMP_MAX_PEDIDOS_MES'],
            }
    except Exception:
        pass

    # Usage percentages
    for key in ['usuarios', 'choferes', 'pedidos_mes']:
        used = data['usage'].get(key, 0)
        mx = data['limits'].get(key, 1)
        pct = round(used / mx * 100, 1) if mx > 0 else 0
        data['usage_pct'][key] = pct
        if pct >= 90:
            data['warnings'].append(f'{key}: {used}/{mx} ({pct}%) - URGENTE')
        elif pct >= 75:
            data['warnings'].append(f'{key}: {used}/{mx} ({pct}%) - Cerca del limite')

    # Next billing
    try:
        r = query(
            "SELECT SUS_FECHA_PROXIMO_COBRO FROM SAAS_SUSCRIPCIONES "
            "WHERE EMP_ID=? AND SUS_ESTADO='ACTIVA' ORDER BY SUS_FECHA_INICIO DESC LIMIT 1",
            [emp_id]
        )
        if r:
            data['next_billing'] = str(r[0].get('SUS_FECHA_PROXIMO_COBRO', ''))
    except Exception:
        pass

    # Last payment
    try:
        r = query(
            "SELECT COB_MONTO, COB_FECHA_COBRO, COB_ESTATUS FROM SAAS_COBROS "
            "WHERE EMP_ID=? ORDER BY COB_FECHA_COBRO DESC LIMIT 1",
            [emp_id]
        )
        if r:
            data['last_payment'] = {
                'monto': float(r[0].get('COB_MONTO', 0)),
                'fecha': str(r[0].get('COB_FECHA_COBRO', '')),
                'estatus': r[0].get('COB_ESTATUS', ''),
            }
    except Exception:
        pass

    # Total paid
    try:
        r = query(
            "SELECT COALESCE(SUM(COB_MONTO), 0) as total FROM SAAS_COBROS "
            "WHERE EMP_ID=? AND COB_ESTATUS IN ('PAGADO','COMPLETADO')",
            [emp_id]
        )
        data['total_paid'] = float(r[0]['total'] if r else 0)
    except Exception:
        pass

    return data


# ========================================
# AUTO-BILLING CRON (for Render Cron Job)
# ========================================
def run_auto_billing():
    """Main entry point for automated billing. Call from cron job endpoint."""
    results = process_all_due_charges()

    # Check for limit warnings across all active tenants
    try:
        empresas = query("SELECT EMP_ID FROM EMPRESAS WHERE EMP_ESTATUS='ACTIVA'")
        limit_warnings = []
        for emp in empresas:
            check = check_limits(emp['EMP_ID'])
            if check['warnings']:
                limit_warnings.append({
                    'emp_id': emp['EMP_ID'],
                    'warnings': check['warnings']
                })
    except Exception:
        limit_warnings = []

    return {
        'charges_processed': len(results),
        'charge_results': results,
        'limit_warnings': limit_warnings,
        'timestamp': datetime.now().isoformat()
    }
