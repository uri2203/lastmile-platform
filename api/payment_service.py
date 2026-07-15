"""
LAST MILE DELIVERY - Payment Service
Stripe + MercadoPago integration for SaaS subscriptions
"""

import os
import hashlib
import hmac
import json
import time
from datetime import datetime, timedelta
from db import query, execute, USE_POSTGRES

# ========================================
# PLAN CONFIGURATION
# ========================================
PLANS = {
    'STARTER': {
        'name': 'Starter',
        'price_mxn': 999,
        'max_usuarios': 5,
        'max_choferes': 10,
        'max_pedidos_mes': 500,
        'features': ['tracking_basico', 'reportes_basicos', 'soporte_email'],
        'stripe_price_id': os.environ.get('STRIPE_PRICE_STARTER', ''),
        'mp_plan_id': os.environ.get('MP_PLAN_STARTER', ''),
    },
    'PRO': {
        'name': 'Pro',
        'price_mxn': 2499,
        'max_usuarios': 15,
        'max_choferes': 30,
        'max_pedidos_mes': 2000,
        'features': ['tracking_basico', 'reportes_avanzados', 'soporte_telefono', 'api_acceso', 'whatsapp_integration'],
        'stripe_price_id': os.environ.get('STRIPE_PRICE_PRO', ''),
        'mp_plan_id': os.environ.get('MP_PLAN_PRO', ''),
    },
    'ENTERPRISE': {
        'name': 'Enterprise',
        'price_mxn': 5999,
        'max_usuarios': 50,
        'max_choferes': 100,
        'max_pedidos_mes': 10000,
        'features': ['tracking_basico', 'reportes_avanzados', 'soporte_dedicado', 'api_acceso', 'whatsapp_integration', 'custom_branding', 'sso', 'sla_garantizado'],
        'stripe_price_id': os.environ.get('STRIPE_PRICE_ENTERPRISE', ''),
        'mp_plan_id': os.environ.get('MP_PLAN_ENTERPRISE', ''),
    }
}


def get_plan_config(plan_name):
    return PLANS.get(plan_name.upper(), PLANS['STARTER'])


# ========================================
# STRIPE SERVICE
# ========================================
class StripeService:
    def __init__(self):
        self.secret_key = os.environ.get('STRIPE_SECRET_KEY', '')
        self.webhook_secret = os.environ.get('STRIPE_WEBHOOK_SECRET', '')
        self.enabled = bool(self.secret_key)

    def _headers(self):
        return {
            'Authorization': f'Bearer {self.secret_key}',
            'Content-Type': 'application/json'
        }

    def create_customer(self, empresa):
        if not self.enabled:
            return {'error': 'Stripe no configurado'}
        import requests
        resp = requests.post('https://api.stripe.com/v1/customers', headers=self._headers(), data={
            'name': empresa.get('EMP_NOMBRE', ''),
            'email': empresa.get('EMP_EMAIL', ''),
            'metadata[emp_id]': empresa.get('EMP_ID', ''),
        })
        return resp.json()

    def create_subscription(self, customer_id, price_id):
        if not self.enabled:
            return {'error': 'Stripe no configurado'}
        import requests
        resp = requests.post('https://api.stripe.com/v1/subscriptions', headers=self._headers(), data={
            'customer': customer_id,
            'items[0][price]': price_id,
            'payment_behavior': 'default_incomplete',
            'expand[]': 'latest_invoice.payment_intent',
        })
        return resp.json()

    def create_checkout_session(self, emp_id, plan_name, success_url, cancel_url):
        if not self.enabled:
            return {'error': 'Stripe no configurado'}
        import requests
        plan = get_plan_config(plan_name)
        resp = requests.post('https://api.stripe.com/v1/checkout/sessions', headers=self._headers(), data={
            'mode': 'subscription',
            'payment_method_types[]': 'card',
            'line_items[0][price]': plan['stripe_price_id'],
            'line_items[0][quantity]': 1,
            'success_url': success_url,
            'cancel_url': cancel_url,
            'metadata[emp_id]': emp_id,
            'metadata[plan]': plan_name,
        })
        return resp.json()

    def cancel_subscription(self, subscription_id):
        if not self.enabled:
            return {'error': 'Stripe no configurado'}
        import requests
        resp = requests.delete(f'https://api.stripe.com/v1/subscriptions/{subscription_id}', headers=self._headers())
        return resp.json()

    def verify_webhook(self, payload, sig_header):
        if not self.webhook_secret:
            return False
        try:
            import stripe
            stripe.api_key = self.secret_key
            event = stripe.Webhook.construct_event(payload, sig_header, self.webhook_secret)
            return event
        except Exception:
            return False


# ========================================
# MERCADOPAGO SERVICE
# ========================================
class MercadoPagoService:
    def __init__(self):
        self.access_token = os.environ.get('MP_ACCESS_TOKEN', '')
        self.public_key = os.environ.get('MP_PUBLIC_KEY', '')
        self.webhook_secret = os.environ.get('MP_WEBHOOK_SECRET', '')
        self.enabled = bool(self.access_token)

    def _headers(self):
        return {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }

    def create_preference(self, emp_id, plan_name, success_url, failure_url, pending_url):
        if not self.enabled:
            return {'error': 'MercadoPago no configurado'}
        import requests
        plan = get_plan_config(plan_name)
        resp = requests.post('https://api.mercadopago.com/preference', headers=self._headers(), json={
            'items': [{
                'title': f'Last Mile - Plan {plan["name"]}',
                'quantity': 1,
                'unit_price': plan['price_mxn'],
                'currency_id': 'MXN'
            }],
            'payer': {'email': ''},
            'back_urls': {
                'success': success_url,
                'failure': failure_url,
                'pending': pending_url
            },
            'auto_return': 'approved',
            'external_reference': f'emp_{emp_id}_{plan_name}',
            'notification_url': os.environ.get('MP_WEBHOOK_URL', ''),
        })
        return resp.json()

    def get_payment(self, payment_id):
        if not self.enabled:
            return {'error': 'MercadoPago no configurado'}
        import requests
        resp = requests.get(f'https://api.mercadopago.com/v1/payments/{payment_id}', headers=self._headers())
        return resp.json()


# ========================================
# BILLING DATABASE OPERATIONS
# ========================================
def get_empresa_billing(emp_id):
    rows = None
    try:
        rows = query(
            "SELECT EMP_ID, EMP_NOMBRE, EMP_EMAIL, EMP_PLAN, EMP_MAX_USUARIOS, EMP_MAX_CHOFERES, EMP_MAX_PEDIDOS_MES "
            "FROM EMPRESAS WHERE EMP_ID = ?", [emp_id]
        )
    except Exception:
        try:
            rows = query("SELECT EMP_ID, EMP_NOMBRE, EMP_EMAIL FROM EMPRESAS WHERE EMP_ID = ?", [emp_id])
        except Exception:
            return None

    if not rows:
        return None
    empresa = rows[0]
    plan_name = empresa.get('EMP_PLAN', 'STARTER') or 'STARTER'
    plan = get_plan_config(plan_name)
    empresa['plan_config'] = plan

    try:
        suscripciones = query(
            "SELECT * FROM SAAS_SUSCRIPCIONES WHERE EMP_ID = ? ORDER BY SUS_FECHA_INICIO DESC LIMIT 5", [emp_id]
        )
    except Exception:
        try:
            suscripciones = query(
                "SELECT * FROM SUSCRIPCIONES WHERE EMP_ID = ? ORDER BY SUS_FECHA_INICIO DESC LIMIT 5", [emp_id]
            )
        except Exception:
            suscripciones = []
    empresa['suscripciones'] = suscripciones

    try:
        pagos = query(
            "SELECT * FROM SAAS_COBROS WHERE EMP_ID = ? ORDER BY COB_FECHA_COBRO DESC LIMIT 10", [emp_id]
        )
    except Exception:
        try:
            pagos = query(
                "SELECT * FROM PAGOS_TRANSACCIONES WHERE EMP_ID = ? ORDER BY TRP_FECHA_REGISTRO DESC LIMIT 10", [emp_id]
            )
        except Exception:
            pagos = []
    empresa['pagos_recientes'] = pagos

    return empresa


def ensure_billing_columns():
    """Add missing billing columns/tables to EMPRESAS if they don't exist."""
    if not USE_POSTGRES:
        return
    try:
        execute("ALTER TABLE EMPRESAS ADD COLUMN IF NOT EXISTS EMP_PLAN TEXT DEFAULT 'STARTER'")
    except Exception:
        pass
    try:
        execute("ALTER TABLE EMPRESAS ADD COLUMN IF NOT EXISTS EMP_MAX_USUARIOS INTEGER DEFAULT 5")
    except Exception:
        pass
    try:
        execute("ALTER TABLE EMPRESAS ADD COLUMN IF NOT EXISTS EMP_MAX_CHOFERES INTEGER DEFAULT 10")
    except Exception:
        pass
    try:
        execute("ALTER TABLE EMPRESAS ADD COLUMN IF NOT EXISTS EMP_MAX_PEDIDOS_MES INTEGER DEFAULT 500")
    except Exception:
        pass


def create_suscripcion(emp_id, plan_name, provider, external_id=None):
    plan = get_plan_config(plan_name)
    try:
        execute(
            "INSERT INTO SAAS_SUSCRIPCIONES (EMP_ID, PLAN_ID, SUS_ESTADO, SUS_FECHA_INICIO, SUS_METODO_PAGO, "
            "SUS_STRIPE_CUSTOMER_ID, SUS_STRIPE_SUBSCRIPTION_ID) "
            "VALUES (?, 1, 'ACTIVA', NOW(), ?, ?, ?)",
            [emp_id, provider.upper(), external_id if provider == 'stripe' else '', external_id if provider == 'stripe' else '']
        )
    except Exception:
        execute(
            "INSERT INTO SUSCRIPCIONES (EMP_ID, SUS_PLAN, SUS_PRECIO_MXN, SUS_PROVEEDOR, SUS_EXTERNAL_ID, SUS_ESTADO, SUS_FECHA_INICIO) "
            "VALUES (?, ?, ?, ?, ?, 'ACTIVA', NOW())",
            [emp_id, plan_name, plan['price_mxn'], provider, external_id or '']
        )
    execute(
        "UPDATE EMPRESAS SET EMP_PLAN=?, EMP_MAX_USUARIOS=?, EMP_MAX_CHOFERES=?, EMP_MAX_PEDIDOS_MES=? WHERE EMP_ID=?",
        [plan_name, plan['max_usuarios'], plan['max_choferes'], plan['max_pedidos_mes'], emp_id]
    )
    return True


def create_pago(emp_id, monto, metodo, referencia=None, notas=None):
    try:
        execute(
            "INSERT INTO SAAS_COBROS (SUS_ID, EMP_ID, COB_MONTO, COB_CONCEPTO, COB_ESTATUS, COB_METODO_PAGO, COB_REFERENCIA_PAGO) "
            "VALUES (0, ?, ?, ?, 'PENDIENTE', ?, ?)",
            [emp_id, monto, notas or 'Pago SaaS', metodo, referencia or '']
        )
    except Exception:
        execute(
            "INSERT INTO PAGOS_TRANSACCIONES (EMP_ID, TRP_MONTO, TRP_METODO, TRP_NUM_REFERENCIA, TRP_ESTATUS, TRP_NOTAS) "
            "VALUES (?, ?, ?, ?, 'PENDIENTE', ?)",
            [emp_id, monto, metodo, referencia or '', notas or '']
        )
    return True


def cancel_suscripcion(emp_id):
    try:
        execute(
            "UPDATE SAAS_SUSCRIPCIONES SET SUS_ESTADO='CANCELADA', SUS_FECHA_FIN=NOW() WHERE EMP_ID=? AND SUS_ESTADO='ACTIVA'",
            [emp_id]
        )
    except Exception:
        pass
    try:
        execute(
            "UPDATE SUSCRIPCIONES SET SUS_ESTADO='CANCELADA', SUS_FECHA_FIN=NOW() WHERE EMP_ID=? AND SUS_ESTADO='ACTIVA'",
            [emp_id]
        )
    except Exception:
        pass
    execute(
        "UPDATE EMPRESAS SET EMP_PLAN='STARTER', EMP_MAX_USUARIOS=5, EMP_MAX_CHOFERES=10, EMP_MAX_PEDIDOS_MES=500 WHERE EMP_ID=?",
        [emp_id]
    )
    return True


def get_suscripcion_activa(emp_id):
    try:
        rows = query(
            "SELECT * FROM SAAS_SUSCRIPCIONES WHERE EMP_ID = ? AND SUS_ESTADO = 'ACTIVA' ORDER BY SUS_FECHA_INICIO DESC LIMIT 1",
            [emp_id]
        )
        if rows:
            return rows[0]
    except Exception:
        pass
    try:
        rows = query(
            "SELECT * FROM SUSCRIPCIONES WHERE EMP_ID = ? AND SUS_ESTADO = 'ACTIVA' ORDER BY SUS_FECHA_INICIO DESC LIMIT 1",
            [emp_id]
        )
        return rows[0] if rows else None
    except Exception:
        return None


def get_billing_stats(emp_id):
    pagos = None
    try:
        pagos = query(
            "SELECT COUNT(*) as total_pagos, SUM(COB_MONTO) as monto_total, "
            "SUM(CASE WHEN COB_ESTATUS='COMPLETADO' THEN COB_MONTO ELSE 0 END) as monto_completado "
            "FROM SAAS_COBROS WHERE EMP_ID = ?", [emp_id]
        )
    except Exception:
        try:
            pagos = query(
                "SELECT COUNT(*) as total_pagos, SUM(TRP_MONTO) as monto_total, "
                "SUM(CASE WHEN TRP_ESTATUS='COMPLETADO' THEN TRP_MONTO ELSE 0 END) as monto_completado "
                "FROM PAGOS_TRANSACCIONES WHERE EMP_ID = ?", [emp_id]
            )
        except Exception:
            pass

    suscripcion = get_suscripcion_activa(emp_id)

    plan_name = 'STARTER'
    try:
        empresa = query("SELECT EMP_PLAN FROM EMPRESAS WHERE EMP_ID=?", [emp_id])
        if empresa and empresa[0].get('EMP_PLAN'):
            plan_name = empresa[0]['EMP_PLAN']
    except Exception:
        pass

    plan = get_plan_config(plan_name)

    total_pagos = 0
    monto_total = 0
    monto_completado = 0
    if pagos and len(pagos) > 0:
        total_pagos = pagos[0].get('total_pagos', 0) or 0
        monto_total = float(pagos[0].get('monto_total', 0) or 0)
        monto_completado = float(pagos[0].get('monto_completado', 0) or 0)

    return {
        'plan_actual': plan_name,
        'plan_nombre': plan['name'],
        'precio_mensual': plan['price_mxn'],
        'suscripcion_activa': suscripcion is not None,
        'suscripcion_inicio': str(suscripcion.get('SUS_FECHA_INICIO', '')) if suscripcion else None,
        'total_pagos': total_pagos,
        'monto_total': monto_total,
        'monto_completado': monto_completado,
        'limite_usuarios': plan['max_usuarios'],
        'limite_choferes': plan['max_choferes'],
        'limite_pedidos_mes': plan['max_pedidos_mes'],
    }


stripe_service = StripeService()
mp_service = MercadoPagoService()
