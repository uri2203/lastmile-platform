"""
LAST MILE DELIVERY - Multi-Country Payment Providers
Abstract interface + implementations for Mexico, Brazil, Colombia, Argentina, Chile, Peru, Uruguay, Ecuador.
Platform integrates payment gateways; tenants configure their own credentials.
"""

import os
import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, Optional, List

logger = logging.getLogger('lastmile.payments')


class PaymentProvider(ABC):
    """Abstract base class for payment provider integrations."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.api_key = config.get('api_key', '')
        self.api_secret = config.get('api_secret', '')
        self.enabled = bool(self.api_key)

    @abstractmethod
    def create_charge(self, amount: float, currency: str, payment_method: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Create a charge/payment. Returns {success, charge_id, status, error}"""
        pass

    @abstractmethod
    def create_customer(self, name: str, email: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Create a customer. Returns {success, customer_id, error}"""
        pass

    @abstractmethod
    def create_subscription(self, customer_id: str, plan_id: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Create a subscription. Returns {success, subscription_id, error}"""
        pass

    @abstractmethod
    def refund(self, charge_id: str, amount: Optional[float] = None) -> Dict[str, Any]:
        """Refund a charge. Returns {success, refund_id, error}"""
        pass

    @abstractmethod
    def get_payment_status(self, payment_id: str) -> Dict[str, Any]:
        """Get payment status. Returns {status, details, error}"""
        pass

    def test_connection(self) -> Dict[str, Any]:
        """Test API connection. Override in subclass for specific checks."""
        return {'success': self.enabled, 'provider': self.__class__.__name__}


class StripeProvider(PaymentProvider):
    """Stripe payment provider - supports 135+ currencies, 45+ countries."""

    SUPPORTED_COUNTRIES = {
        'MX': {'currency': 'MXN', 'name': 'Mexico'},
        'BR': {'currency': 'BRL', 'name': 'Brasil'},
        'CO': {'currency': 'COP', 'name': 'Colombia'},
        'AR': {'currency': 'ARS', 'name': 'Argentina'},
        'CL': {'currency': 'CLP', 'name': 'Chile'},
        'PE': {'currency': 'PEN', 'name': 'Peru'},
        'UY': {'currency': 'UYU', 'name': 'Uruguay'},
        'EC': {'currency': 'USD', 'name': 'Ecuador'},
        'US': {'currency': 'USD', 'name': 'Estados Unidos'},
        'ES': {'currency': 'EUR', 'name': 'Espana'},
        'CO': {'currency': 'COP', 'name': 'Colombia'},
        'GB': {'currency': 'GBP', 'name': 'Reino Unido'},
        'DE': {'currency': 'EUR', 'name': 'Alemania'},
        'FR': {'currency': 'EUR', 'name': 'Francia'},
        'IT': {'currency': 'EUR', 'name': 'Italia'}
    }

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        import stripe
        stripe.api_key = self.api_key
        self.stripe = stripe

    def create_charge(self, amount: float, currency: str, payment_method: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        if not self.enabled:
            return {'success': False, 'error': 'Stripe not configured'}

        try:
            amount_cents = int(amount * 100) if currency.upper() not in ['JPY', 'KRW'] else int(amount)

            payment_intent = self.stripe.PaymentIntent.create(
                amount=amount_cents,
                currency=currency.lower(),
                payment_method=payment_method,
                confirm=True,
                metadata=metadata,
                automatic_payment_methods={'enabled': True, 'allow_redirects': 'never'}
            )

            return {
                'success': True,
                'charge_id': payment_intent.id,
                'status': payment_intent.status,
                'amount': amount,
                'currency': currency
            }
        except self.stripe.error.CardError as e:
            return {'success': False, 'error': str(e.user_message)}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def create_customer(self, name: str, email: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        if not self.enabled:
            return {'success': False, 'error': 'Stripe not configured'}

        try:
            customer = self.stripe.Customer.create(
                name=name,
                email=email,
                metadata=metadata
            )
            return {'success': True, 'customer_id': customer.id}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def create_subscription(self, customer_id: str, plan_id: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        if not self.enabled:
            return {'success': False, 'error': 'Stripe not configured'}

        try:
            subscription = self.stripe.Subscription.create(
                customer=customer_id,
                items=[{'price': plan_id}],
                metadata=metadata
            )
            return {'success': True, 'subscription_id': subscription.id, 'status': subscription.status}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def refund(self, charge_id: str, amount: Optional[float] = None) -> Dict[str, Any]:
        if not self.enabled:
            return {'success': False, 'error': 'Stripe not configured'}

        try:
            refund_params = {'payment_intent': charge_id}
            if amount:
                refund_params['amount'] = int(amount * 100)

            refund = self.stripe.Refund.create(**refund_params)
            return {'success': True, 'refund_id': refund.id, 'status': refund.status}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_payment_status(self, payment_id: str) -> Dict[str, Any]:
        if not self.enabled:
            return {'success': False, 'error': 'Stripe not configured'}

        try:
            payment_intent = self.stripe.PaymentIntent.retrieve(payment_id)
            return {
                'success': True,
                'status': payment_intent.status,
                'amount': payment_intent.amount / 100,
                'currency': payment_intent.currency
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def create_pix_payment(self, amount: float, currency: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Create PIX payment for Brazil."""
        if not self.enabled:
            return {'success': False, 'error': 'Stripe not configured'}

        try:
            payment_intent = self.stripe.PaymentIntent.create(
                amount=int(amount * 100),
                currency='brl',
                payment_method_types=['pix'],
                metadata=metadata
            )
            return {
                'success': True,
                'charge_id': payment_intent.id,
                'status': payment_intent.status,
                'pix_qr_code': payment_intent.next_action.get('pix_display_qr_code', {}).get('data', ''),
                'pix_code': payment_intent.next_action.get('pix_display_qr_code', {}).get('encoded_image', '')
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}


class MercadoPagoProvider(PaymentProvider):
    """MercadoPago payment provider - Latin America focused."""

    SUPPORTED_COUNTRIES = {
        'MX': {'currency': 'MXN', 'name': 'Mexico'},
        'BR': {'currency': 'BRL', 'name': 'Brasil'},
        'AR': {'currency': 'ARS', 'name': 'Argentina'},
        'CO': {'currency': 'COP', 'name': 'Colombia'},
        'CL': {'currency': 'CLP', 'name': 'Chile'},
        'UY': {'currency': 'UYU', 'name': 'Uruguay'},
        'PE': {'currency': 'PEN', 'name': 'Peru'}
    }

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.base_url = 'https://api.mercadopago.com/v1'
        self.access_token = config.get('access_token', self.api_key)

    def _headers(self):
        return {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }

    def create_charge(self, amount: float, currency: str, payment_method: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        if not self.enabled:
            return {'success': False, 'error': 'MercadoPago not configured'}

        try:
            import requests
            payload = {
                'transaction_amount': amount,
                'payment_method_id': payment_method,
                'description': metadata.get('description', 'Last Mile Delivery'),
                'metadata': metadata
            }

            if 'token' in metadata:
                payload['token'] = metadata['token']
                payload['installments'] = metadata.get('installments', 1)

            if 'payer_email' in metadata:
                payload['payer'] = {'email': metadata['payer_email']}

            resp = requests.post(
                f'{self.base_url}/payments',
                headers=self._headers(),
                json=payload,
                timeout=30
            )

            if resp.status_code in (200, 201):
                data = resp.json()
                return {
                    'success': True,
                    'charge_id': str(data.get('id')),
                    'status': data.get('status'),
                    'status_detail': data.get('status_detail'),
                    'amount': amount,
                    'currency': currency
                }
            else:
                return {'success': False, 'error': f'HTTP {resp.status_code}: {resp.text[:500]}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def create_customer(self, name: str, email: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        if not self.enabled:
            return {'success': False, 'error': 'MercadoPago not configured'}

        try:
            import requests
            payload = {
                'email': email,
                'first_name': name.split()[0] if name else '',
                'last_name': ' '.join(name.split()[1:]) if name and len(name.split()) > 1 else '',
                'metadata': metadata
            }

            resp = requests.post(
                f'{self.base_url}/customers',
                headers=self._headers(),
                json=payload,
                timeout=30
            )

            if resp.status_code in (200, 201):
                data = resp.json()
                return {'success': True, 'customer_id': data.get('id')}
            return {'success': False, 'error': f'HTTP {resp.status_code}: {resp.text[:500]}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def create_subscription(self, customer_id: str, plan_id: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        if not self.enabled:
            return {'success': False, 'error': 'MercadoPago not configured'}

        try:
            import requests
            payload = {
                'preapproval_plan_id': plan_id,
                'payer_id': customer_id,
                'metadata': metadata
            }

            resp = requests.post(
                f'{self.base_url}/preapproval',
                headers=self._headers(),
                json=payload,
                timeout=30
            )

            if resp.status_code in (200, 201):
                data = resp.json()
                return {'success': True, 'subscription_id': data.get('id'), 'status': data.get('status')}
            return {'success': False, 'error': f'HTTP {resp.status_code}: {resp.text[:500]}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def refund(self, charge_id: str, amount: Optional[float] = None) -> Dict[str, Any]:
        if not self.enabled:
            return {'success': False, 'error': 'MercadoPago not configured'}

        try:
            import requests
            payload = {}
            if amount:
                payload['amount'] = amount

            resp = requests.post(
                f'{self.base_url}/payments/{charge_id}/refunds',
                headers=self._headers(),
                json=payload,
                timeout=30
            )

            if resp.status_code in (200, 201):
                data = resp.json()
                return {'success': True, 'refund_id': str(data.get('id')), 'status': data.get('status')}
            return {'success': False, 'error': f'HTTP {resp.status_code}: {resp.text[:500]}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_payment_status(self, payment_id: str) -> Dict[str, Any]:
        if not self.enabled:
            return {'success': False, 'error': 'MercadoPago not configured'}

        try:
            import requests
            resp = requests.get(
                f'{self.base_url}/payments/{payment_id}',
                headers=self._headers(),
                timeout=15
            )
            if resp.status_code == 200:
                data = resp.json()
                return {
                    'success': True,
                    'status': data.get('status'),
                    'status_detail': data.get('status_detail'),
                    'amount': data.get('transaction_amount'),
                    'currency': data.get('currency_id')
                }
            return {'success': False, 'error': f'HTTP {resp.status_code}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def create_pix_payment(self, amount: float, currency: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Create PIX payment via MercadoPago for Brazil."""
        if not self.enabled:
            return {'success': False, 'error': 'MercadoPago not configured'}

        return self.create_charge(amount, 'BRL', 'pix', metadata)


class PaymentProviderRegistry:
    """Registry for managing payment providers."""

    PROVIDERS = {
        'stripe': StripeProvider,
        'mercadopago': MercadoPagoProvider
    }

    COUNTRY_PROVIDERS = {
        'MX': ['stripe', 'mercadopago'],
        'BR': ['stripe', 'mercadopago'],
        'CO': ['stripe', 'mercadopago'],
        'AR': ['mercadopago', 'stripe'],
        'CL': ['stripe', 'mercadopago'],
        'PE': ['mercadopago', 'stripe'],
        'UY': ['mercadopago', 'stripe'],
        'EC': ['stripe', 'mercadopago'],
        'US': ['stripe'],
        'ES': ['stripe'],
        'GB': ['stripe'],
        'DE': ['stripe'],
        'FR': ['stripe'],
        'IT': ['stripe']
    }

    @classmethod
    def get_provider(cls, provider_name: str, config: Dict[str, Any]) -> Optional[PaymentProvider]:
        """Get payment provider by name."""
        provider_class = cls.PROVIDERS.get(provider_name)
        if provider_class:
            return provider_class(config)
        return None

    @classmethod
    def get_available_providers(cls, country_code: str) -> List[Dict[str, str]]:
        """Get available payment providers for a country."""
        providers = cls.COUNTRY_PROVIDERS.get(country_code, ['stripe'])
        return [{'id': p, 'name': p.replace('_', ' ').title()} for p in providers]

    @classmethod
    def get_payment_methods(cls, country_code: str) -> Dict[str, Any]:
        """Get available payment methods for a country."""
        from db import query
        methods = query(
            "SELECT * FROM PAYMENT_METHODS_COUNTRY WHERE PMC_COUNTRY_CODE=? AND PMC_ACTIVO='S'",
            [country_code]
        )
        return {'success': True, 'country': country_code, 'methods': methods}


class MultiCountryPaymentService:
    """Service for managing payment operations across multiple countries."""

    def __init__(self):
        self.providers = {}

    def configure_tenant(self, emp_id: int, provider_name: str, provider_config: Dict[str, Any]):
        """Configure payment provider for a tenant."""
        provider = PaymentProviderRegistry.get_provider(provider_name, provider_config)
        if provider:
            self.providers[emp_id] = {
                'provider_name': provider_name,
                'provider': provider,
                'configured_at': datetime.now().isoformat()
            }
            logger.info(f'[PAYMENTS] Configured {provider_name} for empresa {emp_id}')
            return True
        logger.warning(f'[PAYMENTS] No provider: {provider_name}')
        return False

    def get_tenant_provider(self, emp_id: int) -> Optional[PaymentProvider]:
        """Get payment provider for a tenant."""
        config = self.providers.get(emp_id)
        if config:
            return config['provider']
        return None

    def create_charge(self, emp_id: int, amount: float, currency: str, payment_method: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Create charge using tenant's configured provider."""
        provider = self.get_tenant_provider(emp_id)
        if not provider:
            return {'success': False, 'error': 'No payment provider configured for this empresa'}

        return provider.create_charge(amount, currency, payment_method, metadata)

    def create_customer(self, emp_id: int, name: str, email: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Create customer using tenant's configured provider."""
        provider = self.get_tenant_provider(emp_id)
        if not provider:
            return {'success': False, 'error': 'No payment provider configured for this empresa'}

        return provider.create_customer(name, email, metadata)

    def refund(self, emp_id: int, charge_id: str, amount: Optional[float] = None) -> Dict[str, Any]:
        """Refund using tenant's configured provider."""
        provider = self.get_tenant_provider(emp_id)
        if not provider:
            return {'success': False, 'error': 'No payment provider configured for this empresa'}

        return provider.refund(charge_id, amount)

    def get_payment_status(self, emp_id: int, payment_id: str) -> Dict[str, Any]:
        """Get payment status using tenant's configured provider."""
        provider = self.get_tenant_provider(emp_id)
        if not provider:
            return {'success': False, 'error': 'No payment provider configured for this empresa'}

        return provider.get_payment_status(payment_id)

    def get_available_providers(self, country_code: str) -> List[Dict[str, str]]:
        """Get available providers for a country."""
        return PaymentProviderRegistry.get_available_providers(country_code)

    def get_payment_methods(self, country_code: str) -> Dict[str, Any]:
        """Get payment methods for a country."""
        return PaymentProviderRegistry.get_payment_methods(country_code)


def get_payment_service():
    """Get or create multi-country payment service."""
    if not hasattr(get_payment_service, '_instance'):
        get_payment_service._instance = MultiCountryPaymentService()
    return get_payment_service._instance


def get_payment_provider_for_empresa(emp_id: int):
    """Get payment provider for a specific empresa."""
    service = get_payment_service()
    return service.get_tenant_provider(emp_id)
