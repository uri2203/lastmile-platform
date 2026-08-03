"""Multi-Country Payment Providers - Stripe + MercadoPago"""
import os
import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger('lastmile.payment')

STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY', '')
STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET', '')
MERCADOPAGO_ACCESS_TOKEN = os.environ.get('MERCADOPAGO_ACCESS_TOKEN', '')


class StripeProvider:
    COUNTRY_METHODS = {
        'MX': ['TARJETA', 'OXXO', 'SPEI'],
        'BR': ['TARJETA', 'PIX'],
        'CO': ['TARJETA', 'PSE'],
        'AR': ['TARJETA'],
        'CL': ['TARJETA', 'WEBPAY'],
        'PE': ['TARJETA'],
        'UY': ['TARJETA'],
        'EC': ['TARJETA'],
        'US': ['TARJETA', 'APPLE_PAY', 'GOOGLE_PAY', 'KLARNA', 'AFFIRM', 'CASHAPP'],
        'CA': ['TARJETA'],
        'GB': ['TARJETA', 'BACS'],
        'DE': ['TARJETA', 'SEPA', 'GIROPAY', 'KLARNA'],
        'FR': ['TARJETA', 'SEPA', 'KLARNA'],
        'IT': ['TARJETA', 'SEPA', 'KLARNA'],
        'NL': ['TARJETA', 'IDEAL', 'SEPA', 'KLARNA'],
        'ES': ['TARJETA', 'SEPA'],
        'PT': ['TARJETA', 'SEPA'],
        'BE': ['TARJETA', 'BANCONTACT', 'SEPA'],
        'AT': ['TARJETA', 'SEPA', 'KLARNA'],
        'JP': ['TARJETA', 'KONBINI'],
        'CN': ['TARJETA', 'ALIPAY', 'WECHAT_PAY'],
        'KR': ['TARJETA'],
        'IN': ['TARJETA', 'UPI'],
        'AU': ['TARJETA'],
        'SG': ['TARJETA'],
        'SA': ['TARJETA', 'MADA'],
        'AE': ['TARJETA'],
    }

    COUNTRY_CURRENCIES = {
        'MX': 'mxn', 'BR': 'brl', 'CO': 'cop', 'AR': 'ars',
        'CL': 'clp', 'PE': 'pen', 'UY': 'uyu', 'EC': 'usd',
        'US': 'usd', 'CA': 'cad', 'GB': 'gbp', 'EU': 'eur',
        'DE': 'eur', 'FR': 'eur', 'IT': 'eur', 'NL': 'eur',
        'ES': 'eur', 'PT': 'eur', 'BE': 'eur', 'AT': 'eur',
        'JP': 'jpy', 'CN': 'cny', 'KR': 'krw', 'IN': 'inr',
        'AU': 'aud', 'SG': 'sgd', 'SA': 'sar', 'AE': 'aed',
    }

    def __init__(self):
        self.enabled = bool(STRIPE_SECRET_KEY)

    def create_checkout_session(self, data: Dict[str, Any]) -> Dict[str, Any]:
        if not self.enabled:
            return {'success': False, 'error': 'Stripe not configured'}
        try:
            import stripe
            stripe.api_key = STRIPE_SECRET_KEY
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': data.get('currency', 'mxn').lower(),
                        'product_data': {'name': data.get('description', 'Delivery payment')},
                        'unit_amount': int(data.get('amount', 0) * 100),
                    },
                    'quantity': 1,
                }],
                mode='payment',
                metadata={'order_id': data.get('order_id', ''), 'emp_id': data.get('emp_id', '')},
            )
            return {'success': True, 'session_id': session.id, 'url': session.url}
        except Exception as e:
            logger.error(f'Stripe error: {e}')
            return {'success': False, 'error': str(e)}

    def create_payment_intent(self, data: Dict[str, Any]) -> Dict[str, Any]:
        if not self.enabled:
            return {'success': False, 'error': 'Stripe not configured'}
        try:
            import stripe
            stripe.api_key = STRIPE_SECRET_KEY
            intent = stripe.PaymentIntent.create(
                amount=int(data.get('amount', 0) * 100),
                currency=data.get('currency', 'mxn').lower(),
                payment_method_types=data.get('payment_methods', ['card']),
                metadata=data.get('metadata', {}),
            )
            return {'success': True, 'payment_intent_id': intent.id, 'client_secret': intent.client_secret}
        except Exception as e:
            logger.error(f'Stripe PI error: {e}')
            return {'success': False, 'error': str(e)}

    def confirm_payment(self, payment_intent_id: str) -> Dict[str, Any]:
        if not self.enabled:
            return {'success': False, 'error': 'Stripe not configured'}
        try:
            import stripe
            stripe.api_key = STRIPE_SECRET_KEY
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            return {'success': True, 'status': intent.status, 'amount': intent.amount / 100}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def refund(self, payment_intent_id: str, amount: Optional[float] = None) -> Dict[str, Any]:
        if not self.enabled:
            return {'success': False, 'error': 'Stripe not configured'}
        try:
            import stripe
            stripe.api_key = STRIPE_SECRET_KEY
            params = {'payment_intent': payment_intent_id}
            if amount:
                params['amount'] = int(amount * 100)
            refund = stripe.Refund.create(**params)
            return {'success': True, 'refund_id': refund.id, 'status': refund.status}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_supported_methods(self, country_code: str) -> List[str]:
        return self.COUNTRY_METHODS.get(country_code.upper(), [])


class MercadoPagoProvider:
    COUNTRY_METHODS = {
        'MX': ['MERCADOPAGO', 'OXXO'],
        'BR': ['PIX', 'BOLETO', 'MERCADOPAGO'],
        'CO': ['PSE', 'MERCADOPAGO'],
        'AR': ['MERCADOPAGO'],
        'CL': ['MERCADOPAGO'],
        'PE': ['MERCADOPAGO'],
        'UY': ['MERCADOPAGO'],
        'EC': ['MERCADOPAGO'],
    }

    def __init__(self):
        self.enabled = bool(MERCADOPAGO_ACCESS_TOKEN)

    def create_preference(self, data: Dict[str, Any]) -> Dict[str, Any]:
        if not self.enabled:
            return {'success': False, 'error': 'MercadoPago not configured'}
        try:
            import requests
            r = requests.post(
                'https://api.mercadopago.com/checkout/preferences',
                headers={'Authorization': f'Bearer {MERCADOPAGO_ACCESS_TOKEN}', 'Content-Type': 'application/json'},
                json={
                    'items': [{'title': data.get('description', 'Delivery'), 'quantity': 1, 'unit_price': float(data.get('amount', 0))}],
                    'external_reference': data.get('order_id', ''),
                    'metadata': {'emp_id': data.get('emp_id', '')},
                },
                timeout=30,
            )
            if r.status_code in (200, 201):
                pref = r.json()
                return {'success': True, 'preference_id': pref['id'], 'init_point': pref['init_point']}
            return {'success': False, 'error': f'HTTP {r.status_code}: {r.text[:200]}'}
        except Exception as e:
            logger.error(f'MP preference error: {e}')
            return {'success': False, 'error': str(e)}

    def create_pix_payment(self, data: Dict[str, Any]) -> Dict[str, Any]:
        if not self.enabled:
            return {'success': False, 'error': 'MercadoPago not configured'}
        try:
            import requests
            r = requests.post(
                'https://api.mercadopago.com/v1/payments',
                headers={'Authorization': f'Bearer {MERCADOPAGO_ACCESS_TOKEN}', 'Content-Type': 'application/json'},
                json={
                    'transaction_amount': float(data.get('amount', 0)),
                    'description': data.get('description', 'Delivery'),
                    'payment_method_id': 'pix',
                    'external_reference': data.get('order_id', ''),
                    'date_of_expiration': data.get('expiration'),
                },
                timeout=30,
            )
            if r.status_code in (200, 201):
                pay = r.json()
                return {
                    'success': True,
                    'payment_id': pay['id'],
                    'qr_code': pay.get('point_of_interaction', {}).get('transaction_data', {}).get('qr_code_base64'),
                    'ticket_url': pay.get('point_of_interaction', {}).get('transaction_data', {}).get('ticket_url'),
                }
            return {'success': False, 'error': f'HTTP {r.status_code}: {r.text[:200]}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_payment_status(self, payment_id: str) -> Dict[str, Any]:
        if not self.enabled:
            return {'success': False, 'error': 'MercadoPago not configured'}
        try:
            import requests
            r = requests.get(
                f'https://api.mercadopago.com/v1/payments/{payment_id}',
                headers={'Authorization': f'Bearer {MERCADOPAGO_ACCESS_TOKEN}'},
                timeout=15,
            )
            if r.status_code == 200:
                pay = r.json()
                return {'success': True, 'status': pay.get('status'), 'status_detail': pay.get('status_detail')}
            return {'success': False, 'error': f'HTTP {r.status_code}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def refund(self, payment_id: str, amount: Optional[float] = None) -> Dict[str, Any]:
        if not self.enabled:
            return {'success': False, 'error': 'MercadoPago not configured'}
        try:
            import requests
            body = {}
            if amount:
                body['amount'] = amount
            r = requests.post(
                f'https://api.mercadopago.com/v1/payments/{payment_id}/refunds',
                headers={'Authorization': f'Bearer {MERCADOPAGO_ACCESS_TOKEN}', 'Content-Type': 'application/json'},
                json=body,
                timeout=30,
            )
            if r.status_code in (200, 201):
                ref = r.json()
                return {'success': True, 'refund_id': ref.get('id'), 'status': ref.get('status')}
            return {'success': False, 'error': f'HTTP {r.status_code}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_supported_methods(self, country_code: str) -> List[str]:
        return self.COUNTRY_METHODS.get(country_code.upper(), [])


class MultiCountryPaymentService:
    def __init__(self):
        self.stripe = StripeProvider()
        self.mercadopago = MercadoPagoProvider()

    def create_payment(self, data: Dict[str, Any]) -> Dict[str, Any]:
        method = data.get('payment_method', 'TARJETA').upper()
        country = data.get('country_code', 'MX').upper()
        if method in ('TARJETA', 'OXXO', 'WEBPAY', 'PSE', 'BOLETO'):
            return self.stripe.create_checkout_session(data)
        elif method in ('MERCADOPAGO', 'PIX', 'YAPE', 'PLIN', 'NEQUI', 'PICHINCHA'):
            if method == 'PIX':
                return self.mercadopago.create_pix_payment(data)
            return self.mercadopago.create_preference(data)
        return {'success': False, 'error': f'Unknown payment method: {method}'}

    def get_status(self, provider: str, payment_id: str) -> Dict[str, Any]:
        if provider == 'stripe':
            return self.stripe.confirm_payment(payment_id)
        elif provider == 'mercadopago':
            return self.mercadopago.get_payment_status(payment_id)
        return {'success': False, 'error': f'Unknown provider: {provider}'}

    def refund(self, provider: str, payment_id: str, amount: Optional[float] = None) -> Dict[str, Any]:
        if provider == 'stripe':
            return self.stripe.refund(payment_id, amount)
        elif provider == 'mercadopago':
            return self.mercadopago.refund(payment_id, amount)
        return {'success': False, 'error': f'Unknown provider: {provider}'}

    def get_supported_methods(self, country_code: str) -> Dict[str, List[str]]:
        return {
            'stripe': self.stripe.get_supported_methods(country_code),
            'mercadopago': self.mercadopago.get_supported_methods(country_code),
        }

    def get_status_summary(self) -> Dict[str, Any]:
        return {
            'stripe': {'configured': self.stripe.enabled, 'supported_countries': list(self.stripe.COUNTRY_METHODS.keys())},
            'mercadopago': {'configured': self.mercadopago.enabled, 'supported_countries': list(self.mercadopago.COUNTRY_METHODS.keys())},
        }


def get_payment_service():
    if not hasattr(get_payment_service, '_instance'):
        get_payment_service._instance = MultiCountryPaymentService()
    return get_payment_service._instance
