"""Webhook + Payment endpoints for Stripe and MercadoPago multi-country payments."""
from flask import Blueprint, request, jsonify, g
import os
import json
import logging

webhook_bp = Blueprint('webhooks', __name__)
wh_logger = logging.getLogger('lastmile.webhooks')

STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY', '')
STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET', '')
MP_ACCESS_TOKEN = os.environ.get('MP_ACCESS_TOKEN', '')


# ========================================
# WEBHOOKS
# ========================================

@webhook_bp.route('/api/webhooks/stripe', methods=['POST'])
def stripe_webhook():
    payload = request.get_data(as_text=True)
    sig = request.headers.get('Stripe-Signature', '')
    if STRIPE_WEBHOOK_SECRET and sig:
        try:
            import stripe as _s
            _s.api_key = STRIPE_SECRET_KEY
            ev = _s.Webhook.construct_event(payload, sig, STRIPE_WEBHOOK_SECRET)
            _handle_stripe_event(ev)
        except Exception as e:
            wh_logger.warning(f'Stripe wh err: {e}')
            return jsonify({'error': str(e)}), 400
    else:
        try:
            ev = json.loads(payload)
            wh_logger.info(f'Stripe raw: {ev.get("type", "?")}')
        except Exception:
            return jsonify({'error': 'bad payload'}), 400
    return jsonify({'received': True})


def _handle_stripe_event(ev):
    from db import execute
    etype = ev.get('type', '')
    obj = ev.get('data', {}).get('object', {})
    wh_logger.info(f'Stripe event: {etype}')
    if etype == 'checkout.session.completed':
        oid = obj.get('metadata', {}).get('order_id', '')
        total = (obj.get('amount_total') or 0) / 100
        currency = (obj.get('currency') or 'mxn').upper()
        if oid:
            try:
                execute("UPDATE PEDIDOS SET PED_ESTADO='PAGADA', PED_MONEDA=?, PED_COSTO_TOTAL=? WHERE PED_ID=?", [currency, total, int(oid)])
            except Exception:
                pass
        wh_logger.info(f'Stripe checkout OK: order={oid} {total} {currency}')
    elif etype == 'payment_intent.succeeded':
        wh_logger.info(f'Stripe PI succeeded: {obj.get("id", "")}')
    elif etype == 'payment_intent.payment_failed':
        wh_logger.warning(f'Stripe PI failed: {obj.get("id", "")}')
    elif etype == 'charge.refunded':
        wh_logger.info(f'Stripe refund: {obj.get("id", "")}')


@webhook_bp.route('/api/webhooks/mercadopago', methods=['POST'])
def mercadopago_webhook():
    data = request.get_json(silent=True) or {}
    action = data.get('action', '')
    resource = data.get('resource', '')
    wh_logger.info(f'MP webhook: action={action} resource={resource}')
    if action in ('payment.created', 'payment.updated') and resource and MP_ACCESS_TOKEN:
        try:
            import requests
            pid = resource.split('/')[-1] if '/' in resource else resource
            r = requests.get(
                f'https://api.mercadopago.com/v1/payments/{pid}',
                headers={'Authorization': f'Bearer {MP_ACCESS_TOKEN}'},
                timeout=15,
            )
            if r.status_code == 200:
                pay = r.json()
                status = pay.get('status', '')
                oid = pay.get('external_reference', '')
                amount = pay.get('transaction_amount', 0)
                curr = pay.get('currency_id', 'MXN')
                wh_logger.info(f'MP payment: id={pid} status={status} order={oid} {amount} {curr}')
                if status == 'approved' and oid:
                    from db import execute
                    try:
                        execute("UPDATE PEDIDOS SET PED_ESTADO='PAGADA', PED_MONEDA=?, PED_COSTO_TOTAL=? WHERE PED_ID=?", [curr, amount, int(oid)])
                    except Exception:
                        pass
        except Exception as e:
            wh_logger.error(f'MP webhook fetch err: {e}')
    return jsonify({'received': True})


# ========================================
# PAYMENT ENDPOINTS
# ========================================

COUNTRY_CURRENCIES = {
    'MX': 'mxn', 'BR': 'brl', 'CO': 'cop', 'AR': 'ars',
    'CL': 'clp', 'PE': 'pen', 'UY': 'uyu', 'EC': 'usd',
}

COUNTRY_PAYMENT_METHODS = {
    'MX': {'stripe': ['card'], 'mercadopago': ['visa', 'mastercard', 'oxxo']},
    'BR': {'stripe': ['card'], 'mercadopago': ['visa', 'mastercard', 'pix', 'boleto']},
    'CO': {'stripe': ['card'], 'mercadopago': ['visa', 'mastercard', 'pse', 'nequi']},
    'AR': {'stripe': ['card'], 'mercadopago': ['visa', 'mastercard', 'mercadopago_account', 'rapipago']},
    'CL': {'stripe': ['card'], 'mercadopago': ['visa', 'mastercard', 'webpay']},
    'PE': {'stripe': ['card'], 'mercadopago': ['visa', 'mastercard', 'yape', 'plin']},
    'UY': {'stripe': ['card'], 'mercadopago': ['visa', 'mastercard', 'mercadopago_account']},
    'EC': {'stripe': ['card'], 'mercadopago': ['visa', 'mastercard', 'pichincha']},
}


@webhook_bp.route('/api/payments/create', methods=['POST'])
def create_payment():
    try:
        data = request.get_json() or {}
        country = data.get('country_code', 'MX').upper()
        method = data.get('payment_method', 'TARJETA').upper()
        amount = float(data.get('amount', 0))
        description = data.get('description', 'Delivery payment')
        order_id = data.get('order_id', '')
        emp_id = data.get('emp_id', getattr(g, 'emp_id', ''))
        currency = COUNTRY_COUNTRIES.get(country, {}).get('currency', 'mxn') if False else COUNTRY_CURRENCIES.get(country, 'mxn')
        metadata = {'order_id': str(order_id), 'emp_id': str(emp_id), 'country': country, 'method': method}

        if method in ('TARJETA', 'OXXO', 'WEBPAY', 'PSE', 'BOLETO') and STRIPE_SECRET_KEY:
            return _create_stripe_session(amount, currency, description, metadata, country, method)
        elif MP_ACCESS_TOKEN:
            if method == 'PIX':
                return _create_mp_pix(amount, currency, description, order_id)
            return _create_mp_preference(amount, currency, description, order_id, metadata)
        return jsonify({'success': False, 'error': 'No payment provider configured'}), 400
    except Exception as e:
        wh_logger.error(f'create_payment err: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


def _create_stripe_session(amount, currency, description, metadata, country, method):
    import stripe
    stripe.api_key = STRIPE_SECRET_KEY
    pm_types = ['card']
    if method == 'OXXO' and country == 'MX':
        pm_types.append('oxxo')
    elif method == 'PSE' and country == 'CO':
        pm_types.append('pse')
    elif method == 'BOLETO' and country == 'BR':
        pm_types.append('boleto')
    session = stripe.checkout.Session.create(
        payment_method_types=pm_types,
        line_items=[{
            'price_data': {
                'currency': currency,
                'product_data': {'name': description},
                'unit_amount': int(amount * 100),
            },
            'quantity': 1,
        }],
        mode='payment',
        metadata=metadata,
    )
    wh_logger.info(f'Stripe session created: {session.id} {amount} {currency}')
    return jsonify({'success': True, 'provider': 'stripe', 'session_id': session.id, 'url': session.url, 'amount': amount, 'currency': currency})


def _create_mp_preference(amount, currency, description, order_id, metadata):
    import requests as _req
    body = {
        'items': [{'title': description, 'quantity': 1, 'unit_price': float(amount), 'currency_id': currency.upper()}],
        'external_reference': str(order_id),
        'metadata': metadata,
    }
    r = _req.post(
        'https://api.mercadopago.com/checkout/preferences',
        headers={'Authorization': f'Bearer {MP_ACCESS_TOKEN}', 'Content-Type': 'application/json'},
        json=body, timeout=30,
    )
    if r.status_code in (200, 201):
        pref = r.json()
        wh_logger.info(f'MP preference created: {pref["id"]} {amount} {currency}')
        return jsonify({'success': True, 'provider': 'mercadopago', 'preference_id': pref['id'], 'url': pref.get('init_point'), 'amount': amount, 'currency': currency})
    return jsonify({'success': False, 'error': f'MP API error: {r.status_code}'}), 400


def _create_mp_pix(amount, currency, description, order_id):
    import requests as _req
    body = {
        'transaction_amount': float(amount),
        'description': description,
        'payment_method_id': 'pix',
        'external_reference': str(order_id),
    }
    r = _req.post(
        'https://api.mercadopago.com/v1/payments',
        headers={'Authorization': f'Bearer {MP_ACCESS_TOKEN}', 'Content-Type': 'application/json'},
        json=body, timeout=30,
    )
    if r.status_code in (200, 201):
        pay = r.json()
        qr = pay.get('point_of_interaction', {}).get('transaction_data', {}).get('qr_code_base64')
        ticket = pay.get('point_of_interaction', {}).get('transaction_data', {}).get('ticket_url')
        wh_logger.info(f'MP PIX created: {pay["id"]} {amount} {currency}')
        return jsonify({'success': True, 'provider': 'mercadopago', 'payment_id': pay['id'], 'qr_code': qr, 'ticket_url': ticket, 'amount': amount, 'currency': currency})
    return jsonify({'success': False, 'error': f'MP PIX error: {r.status_code}'}), 400


@webhook_bp.route('/api/payments/status/<provider>/<payment_id>', methods=['GET'])
def get_payment_status(payment_id, provider):
    try:
        if provider == 'stripe' and STRIPE_SECRET_KEY:
            import stripe
            stripe.api_key = STRIPE_SECRET_KEY
            pi = stripe.PaymentIntent.retrieve(payment_id)
            return jsonify({'success': True, 'provider': 'stripe', 'status': pi.status, 'amount': pi.amount / 100, 'currency': pi.currency})
        elif provider == 'mercadopago' and MP_ACCESS_TOKEN:
            import requests as _req
            r = _req.get(f'https://api.mercadopago.com/v1/payments/{payment_id}', headers={'Authorization': f'Bearer {MP_ACCESS_TOKEN}'}, timeout=15)
            if r.status_code == 200:
                pay = r.json()
                return jsonify({'success': True, 'provider': 'mercadopago', 'status': pay.get('status'), 'status_detail': pay.get('status_detail'), 'amount': pay.get('transaction_amount'), 'currency': pay.get('currency_id')})
            return jsonify({'success': False, 'error': f'MP API: {r.status_code}'}), 400
        return jsonify({'success': False, 'error': 'Unknown provider'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@webhook_bp.route('/api/payments/refund', methods=['POST'])
def refund_payment():
    try:
        data = request.get_json() or {}
        provider = data.get('provider', '')
        payment_id = data.get('payment_id', '')
        amount = data.get('amount')
        if provider == 'stripe' and STRIPE_SECRET_KEY:
            import stripe
            stripe.api_key = STRIPE_SECRET_KEY
            params = {'payment_intent': payment_id}
            if amount:
                params['amount'] = int(float(amount) * 100)
            ref = stripe.Refund.create(**params)
            wh_logger.info(f'Stripe refund: {ref.id} for {payment_id}')
            return jsonify({'success': True, 'refund_id': ref.id, 'status': ref.status})
        elif provider == 'mercadopago' and MP_ACCESS_TOKEN:
            import requests as _req
            body = {}
            if amount:
                body['amount'] = float(amount)
            r = _req.post(f'https://api.mercadopago.com/v1/payments/{payment_id}/refunds', headers={'Authorization': f'Bearer {MP_ACCESS_TOKEN}', 'Content-Type': 'application/json'}, json=body, timeout=30)
            if r.status_code in (200, 201):
                ref = r.json()
                wh_logger.info(f'MP refund: {ref.get("id")} for {payment_id}')
                return jsonify({'success': True, 'refund_id': ref.get('id'), 'status': ref.get('status')})
            return jsonify({'success': False, 'error': f'MP API: {r.status_code}'}), 400
        return jsonify({'success': False, 'error': 'Unknown provider'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@webhook_bp.route('/api/payments/methods/<country_code>', methods=['GET'])
def get_country_payment_methods(country_code):
    cc = country_code.upper()
    methods = COUNTRY_PAYMENT_METHODS.get(cc, {})
    from db import query
    db_methods = query("SELECT PMC_METHOD_CODE, PMC_METHOD_NAME, PMC_PROVIDER FROM PAYMENT_METHODS_COUNTRY WHERE PMC_COUNTRY_CODE=? AND PMC_ACTIVO='S'", [cc])
    return jsonify({'success': True, 'country': cc, 'currency': COUNTRY_CURRENCIES.get(cc, 'usd'), 'stripe_methods': methods.get('stripe', []), 'mercadopago_methods': methods.get('mercadopago', []), 'db_methods': db_methods})


@webhook_bp.route('/api/payments/countries', methods=['GET'])
def payment_countries():
    return jsonify({'success': True, 'data': list(COUNTRY_CURRENCIES.keys())})


@webhook_bp.route('/api/payments/status-summary', methods=['GET'])
def payment_status_summary():
    summary = {
        'stripe': {'configured': bool(STRIPE_SECRET_KEY), 'countries': list(COUNTRY_PAYMENT_METHODS.keys())},
        'mercadopago': {'configured': bool(MP_ACCESS_TOKEN), 'countries': list(COUNTRY_PAYMENT_METHODS.keys())},
    }
    return jsonify({'success': True, 'data': summary})


# ===== MULTI-COUNTRY ANALYTICS =====

@webhook_bp.route('/api/analytics/multi-country', methods=['GET'])
def multi_country_analytics():
    import traceback as _tb
    try:
        from db import query
        data = {'countries_supported': list(COUNTRY_CURRENCIES.keys()), 'currencies': dict(COUNTRY_CURRENCIES)}
        try:
            rows = query("SELECT TFC_COUNTRY_CODE, COUNT(*) as cnt FROM TENANT_FISCAL_CONFIG GROUP BY TFC_COUNTRY_CODE")
            data['fiscal_configured'] = [{'country': r.get('TFC_COUNTRY_CODE',''), 'tenants': r.get('cnt',0)} for r in rows]
        except Exception:
            data['fiscal_configured'] = []
        try:
            rows = query("SELECT FD_COUNTRY_CODE, FD_ESTATUS, COUNT(*) as cnt FROM FISCAL_DOCUMENTS GROUP BY FD_COUNTRY_CODE, FD_ESTATUS")
            data['fiscal_documents'] = [{'country': r.get('FD_COUNTRY_CODE',''), 'status': r.get('FD_ESTATUS',''), 'count': r.get('cnt',0)} for r in rows]
        except Exception:
            data['fiscal_documents'] = []
        try:
            rows = query("SELECT PMC_COUNTRY_CODE, COUNT(*) as cnt FROM PAYMENT_METHODS_COUNTRY WHERE PMC_ACTIVO='S' GROUP BY PMC_COUNTRY_CODE")
            data['payment_methods'] = [{'country': r.get('PMC_COUNTRY_CODE',''), 'methods': r.get('cnt',0)} for r in rows]
        except Exception:
            data['payment_methods'] = []
        try:
            rows = query("SELECT COUNT(*) as cnt FROM EMPRESAS")
            data['total_tenants'] = rows[0].get('cnt', 0) if rows else 0
        except Exception:
            data['total_tenants'] = 0
        try:
            rows = query("SELECT PED_ESTADO, COUNT(*) as cnt, COALESCE(SUM(PED_COSTO_TOTAL), 0) as revenue FROM PEDIDOS GROUP BY PED_ESTADO ORDER BY cnt DESC LIMIT 10")
            data['orders_by_status'] = [{'status': r.get('PED_ESTADO',''), 'orders': r.get('cnt',0), 'revenue': float(r.get('revenue',0))} for r in rows]
        except Exception:
            data['orders_by_status'] = []
        return jsonify({'success': True, 'data': data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e), 'trace': _tb.format_exc()}), 500
