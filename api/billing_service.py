"""
LAST MILE DELIVERY - Automated Billing Service
Handles recurring subscription charging, usage tracking, and limit enforcement.
"""

import os
import json
from datetime import datetime, timedelta
from db import query, execute, USE_POSTGRES


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
    """Process all due subscription charges. Called by cron job."""
    due = get_due_subscriptions()
    results = []

    for sub in due:
        result = process_subscription_charge(sub)
        results.append({
            'emp_id': sub['EMP_ID'],
            'empresa': sub.get('EMP_NOMBRE', ''),
            'result': result
        })

        # Update next billing date (add 1 month)
        try:
            execute(
                "UPDATE SAAS_SUSCRIPCIONES SET SUS_FECHA_PROXIMO_COBRO = "
                "(SUS_FECHA_PROXIMO_COBRO + INTERVAL '1 month') "
                "WHERE SUS_ID = ?",
                [sub['SUS_ID']]
            )
        except Exception:
            pass

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
            "WHERE EMP_ID=? AND COB_ESTATUS='COMPLETADO'",
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
