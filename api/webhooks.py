"""Webhook endpoints for Stripe and MercadoPago multi-country payments."""
from flask import Blueprint, request, jsonify
import os
import json
import logging

webhook_bp = Blueprint('webhooks', __name__)
wh_logger = logging.getLogger('lastmile.webhooks')


@webhook_bp.route('/api/webhooks/stripe', methods=['POST'])
def stripe_webhook():
    payload = request.get_data(as_text=True)
    sig = request.headers.get('Stripe-Signature', '')
    secret = os.environ.get('STRIPE_WEBHOOK_SECRET', '')
    if secret and sig:
        try:
            import stripe as _s
            _s.api_key = os.environ.get('STRIPE_SECRET_KEY', '')
            ev = _s.Webhook.construct_event(payload, sig, secret)
            wh_logger.info(f'Stripe: {ev["type"]}')
            if ev['type'] == 'checkout.session.completed':
                oid = ev['data']['object'].get('metadata', {}).get('order_id', '')
                if oid:
                    try:
                        from db import execute
                        execute("UPDATE ORDENES SET ORD_ESTATUS='PAGADA' WHERE ORD_ID=?", [int(oid)])
                    except Exception:
                        pass
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


@webhook_bp.route('/api/webhooks/mercadopago', methods=['POST'])
def mercadopago_webhook():
    data = request.get_json(silent=True) or {}
    wh_logger.info(f'MP: {data.get("action", "")} {data.get("resource", "")}')
    return jsonify({'received': True})
