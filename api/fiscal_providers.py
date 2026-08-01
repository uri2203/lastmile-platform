"""
LAST MILE DELIVERY - Multi-Country Fiscal Providers
Abstract interface + implementations for 8 countries.
Platform integrates provider APIs; tenants own their fiscal data.
"""

import os
import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, Optional, List

logger = logging.getLogger('lastmile.fiscal')


class FiscalProvider(ABC):
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.api_key = config.get('api_key', '')
        self.base_url = config.get('base_url', '')
        self.enabled = bool(self.api_key)

    @abstractmethod
    def emit_invoice(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abstractmethod
    def cancel_invoice(self, document_id: str, reason: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_document_status(self, document_id: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_catalog(self, catalog_type: str) -> Dict[str, Any]:
        pass

    def test_connection(self) -> Dict[str, Any]:
        return {'success': self.enabled, 'provider': self.__class__.__name__}


class MexicoProvider(FiscalProvider):
    COUNTRY_CODE = 'MX'
    CURRENCY = 'MXN'
    TAX_REGIMES = {'601': 'General de Ley Personas Morales', '612': 'Actividades Empresariales', '626': 'Régimen Simplificado de Confianza'}
    FORMAS_PAGO = {'01': 'Efectivo', '03': 'Transferencia electrónica', '04': 'Tarjeta de crédito', '15': 'Tarjeta de débito'}

    def __init__(self, config):
        super().__init__(config)
        self.base_url = config.get('base_url', 'https://www.facturapi.io/v2')

    def emit_invoice(self, data):
        if not self.enabled: return {'success': False, 'error': 'Not configured'}
        try:
            import requests
            resp = requests.post(f'{self.base_url}/invoicing', headers={'Authorization': f'Bearer {self.api_key}', 'Content-Type': 'application/json'}, json=data, timeout=30)
            if resp.status_code in (200, 201):
                d = resp.json()
                return {'success': True, 'document_id': d.get('id'), 'uuid': d.get('uuid'), 'pdf_url': d.get('pdf_url')}
            return {'success': False, 'error': f'HTTP {resp.status_code}: {resp.text[:300]}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def cancel_invoice(self, doc_id, reason):
        if not self.enabled: return {'success': False, 'error': 'Not configured'}
        try:
            import requests
            resp = requests.delete(f'{self.base_url}/invoicing/{doc_id}', headers={'Authorization': f'Bearer {self.api_key}'}, json={'motivo': reason}, timeout=30)
            return {'success': resp.status_code in (200, 204)}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_document_status(self, doc_id):
        if not self.enabled: return {'success': False, 'error': 'Not configured'}
        try:
            import requests
            resp = requests.get(f'{self.base_url}/invoicing/{doc_id}', headers={'Authorization': f'Bearer {self.api_key}'}, timeout=15)
            if resp.status_code == 200: return {'success': True, 'status': resp.json().get('status'), 'details': resp.json()}
            return {'success': False, 'error': f'HTTP {resp.status_code}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_catalog(self, ct):
        if ct == 'regimenes_fiscales': return {'success': True, 'items': self.TAX_REGIMES}
        if ct == 'formas_pago': return {'success': True, 'items': self.FORMAS_PAGO}
        return {'success': False, 'error': f'Unknown: {ct}'}


class BrazilProvider(FiscalProvider):
    COUNTRY_CODE = 'BR'
    CURRENCY = 'BRL'

    def __init__(self, config):
        super().__init__(config)
        self.base_url = config.get('base_url', 'https://api.nfe.io/v1')

    def emit_invoice(self, data):
        if not self.enabled: return {'success': False, 'error': 'Not configured'}
        try:
            import requests
            resp = requests.post(f'{self.base_url}/nfe', headers={'Authorization': f'Bearer {self.api_key}', 'Content-Type': 'application/json'}, json=data, timeout=30)
            if resp.status_code in (200, 201):
                d = resp.json()
                return {'success': True, 'document_id': d.get('id'), 'chave': d.get('chave'), 'status': d.get('status')}
            return {'success': False, 'error': f'HTTP {resp.status_code}: {resp.text[:300]}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def cancel_invoice(self, doc_id, reason):
        if not self.enabled: return {'success': False, 'error': 'Not configured'}
        try:
            import requests
            resp = requests.delete(f'{self.base_url}/nfe/{doc_id}', headers={'Authorization': f'Bearer {self.api_key}'}, timeout=30)
            return {'success': resp.status_code in (200, 204)}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_document_status(self, doc_id):
        if not self.enabled: return {'success': False, 'error': 'Not configured'}
        try:
            import requests
            resp = requests.get(f'{self.base_url}/nfe/{doc_id}', headers={'Authorization': f'Bearer {self.api_key}'}, timeout=15)
            if resp.status_code == 200: return {'success': True, 'status': resp.json().get('status'), 'details': resp.json()}
            return {'success': False, 'error': f'HTTP {resp.status_code}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_catalog(self, ct):
        return {'success': False, 'error': f'Unknown: {ct}'}


class ColombiaProvider(FiscalProvider):
    COUNTRY_CODE = 'CO'
    CURRENCY = 'COP'

    def __init__(self, config):
        super().__init__(config)
        self.base_url = config.get('base_url', 'https://api.dian.gov.co/v1')

    def emit_invoice(self, data):
        if not self.enabled: return {'success': False, 'error': 'Not configured'}
        try:
            import requests
            resp = requests.post(f'{self.base_url}/invoices', headers={'Authorization': f'Bearer {self.api_key}', 'Content-Type': 'application/json'}, json=data, timeout=30)
            if resp.status_code in (200, 201):
                d = resp.json()
                return {'success': True, 'document_id': d.get('id'), 'cufe': d.get('cufe'), 'status': d.get('status')}
            return {'success': False, 'error': f'HTTP {resp.status_code}: {resp.text[:300]}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def cancel_invoice(self, doc_id, reason):
        if not self.enabled: return {'success': False, 'error': 'Not configured'}
        try:
            import requests
            resp = requests.post(f'{self.base_url}/invoices/{doc_id}/void', headers={'Authorization': f'Bearer {self.api_key}', 'Content-Type': 'application/json'}, json={'motivo': reason}, timeout=30)
            return {'success': resp.status_code in (200, 204)}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_document_status(self, doc_id):
        if not self.enabled: return {'success': False, 'error': 'Not configured'}
        try:
            import requests
            resp = requests.get(f'{self.base_url}/invoices/{doc_id}', headers={'Authorization': f'Bearer {self.api_key}'}, timeout=15)
            if resp.status_code == 200: return {'success': True, 'status': resp.json().get('status'), 'details': resp.json()}
            return {'success': False, 'error': f'HTTP {resp.status_code}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_catalog(self, ct):
        return {'success': False, 'error': f'Unknown: {ct}'}


class ArgentinaProvider(FiscalProvider):
    COUNTRY_CODE = 'AR'
    CURRENCY = 'ARS'

    def __init__(self, config):
        super().__init__(config)
        self.base_url = config.get('base_url', 'https://api.fiscalapi.com/v1')

    def emit_invoice(self, data):
        if not self.enabled: return {'success': False, 'error': 'Not configured'}
        try:
            import requests
            resp = requests.post(f'{self.base_url}/invoices', headers={'Authorization': f'Bearer {self.api_key}', 'Content-Type': 'application/json'}, json=data, timeout=30)
            if resp.status_code in (200, 201):
                d = resp.json()
                return {'success': True, 'document_id': d.get('id'), 'cae': d.get('cae'), 'numero': d.get('numero')}
            return {'success': False, 'error': f'HTTP {resp.status_code}: {resp.text[:300]}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def cancel_invoice(self, doc_id, reason):
        if not self.enabled: return {'success': False, 'error': 'Not configured'}
        return {'success': False, 'error': 'Not supported'}

    def get_document_status(self, doc_id):
        if not self.enabled: return {'success': False, 'error': 'Not configured'}
        try:
            import requests
            resp = requests.get(f'{self.base_url}/invoices/{doc_id}', headers={'Authorization': f'Bearer {self.api_key}'}, timeout=15)
            if resp.status_code == 200: return {'success': True, 'status': resp.json().get('status'), 'details': resp.json()}
            return {'success': False, 'error': f'HTTP {resp.status_code}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_catalog(self, ct):
        return {'success': False, 'error': f'Unknown: {ct}'}


class ChileProvider(FiscalProvider):
    COUNTRY_CODE = 'CL'
    CURRENCY = 'CLP'

    def __init__(self, config):
        super().__init__(config)
        self.base_url = config.get('base_url', 'https://api.sii.cl/v1')

    def emit_invoice(self, data):
        if not self.enabled: return {'success': False, 'error': 'Not configured'}
        try:
            import requests
            resp = requests.post(f'{self.base_url}/invoices', headers={'Authorization': f'Bearer {self.api_key}', 'Content-Type': 'application/json'}, json=data, timeout=30)
            if resp.status_code in (200, 201):
                d = resp.json()
                return {'success': True, 'document_id': d.get('id'), 'tracking_id': d.get('tracking_id'), 'status': d.get('status')}
            return {'success': False, 'error': f'HTTP {resp.status_code}: {resp.text[:300]}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def cancel_invoice(self, doc_id, reason):
        if not self.enabled: return {'success': False, 'error': 'Not configured'}
        try:
            import requests
            resp = requests.post(f'{self.base_url}/invoices/{doc_id}/cancel', headers={'Authorization': f'Bearer {self.api_key}', 'Content-Type': 'application/json'}, json={'motivo': reason}, timeout=30)
            return {'success': resp.status_code in (200, 204)}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_document_status(self, doc_id):
        if not self.enabled: return {'success': False, 'error': 'Not configured'}
        try:
            import requests
            resp = requests.get(f'{self.base_url}/invoices/{doc_id}', headers={'Authorization': f'Bearer {self.api_key}'}, timeout=15)
            if resp.status_code == 200: return {'success': True, 'status': resp.json().get('status'), 'details': resp.json()}
            return {'success': False, 'error': f'HTTP {resp.status_code}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_catalog(self, ct):
        return {'success': False, 'error': f'Unknown: {ct}'}


class PeruProvider(FiscalProvider):
    COUNTRY_CODE = 'PE'
    CURRENCY = 'PEN'

    def __init__(self, config):
        super().__init__(config)
        self.base_url = config.get('base_url', 'https://api.sunat.gob.pe/v1')

    def emit_invoice(self, data):
        if not self.enabled: return {'success': False, 'error': 'Not configured'}
        try:
            import requests
            resp = requests.post(f'{self.base_url}/invoices', headers={'Authorization': f'Bearer {self.api_key}', 'Content-Type': 'application/json'}, json=data, timeout=30)
            if resp.status_code in (200, 201):
                d = resp.json()
                return {'success': True, 'document_id': d.get('id'), 'hash': d.get('hash'), 'status': d.get('status')}
            return {'success': False, 'error': f'HTTP {resp.status_code}: {resp.text[:300]}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def cancel_invoice(self, doc_id, reason):
        return {'success': False, 'error': 'Not supported'}

    def get_document_status(self, doc_id):
        if not self.enabled: return {'success': False, 'error': 'Not configured'}
        try:
            import requests
            resp = requests.get(f'{self.base_url}/invoices/{doc_id}', headers={'Authorization': f'Bearer {self.api_key}'}, timeout=15)
            if resp.status_code == 200: return {'success': True, 'status': resp.json().get('status'), 'details': resp.json()}
            return {'success': False, 'error': f'HTTP {resp.status_code}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_catalog(self, ct):
        return {'success': False, 'error': f'Unknown: {ct}'}


class UruguayProvider(FiscalProvider):
    COUNTRY_CODE = 'UY'
    CURRENCY = 'UYU'

    def __init__(self, config):
        super().__init__(config)
        self.base_url = config.get('base_url', 'https://api.dgi.gub.uy/v1')

    def emit_invoice(self, data):
        if not self.enabled: return {'success': False, 'error': 'Not configured'}
        try:
            import requests
            resp = requests.post(f'{self.base_url}/invoices', headers={'Authorization': f'Bearer {self.api_key}', 'Content-Type': 'application/json'}, json=data, timeout=30)
            if resp.status_code in (200, 201):
                d = resp.json()
                return {'success': True, 'document_id': d.get('id'), 'cae': d.get('cae'), 'status': d.get('status')}
            return {'success': False, 'error': f'HTTP {resp.status_code}: {resp.text[:300]}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def cancel_invoice(self, doc_id, reason):
        return {'success': False, 'error': 'Not supported'}

    def get_document_status(self, doc_id):
        if not self.enabled: return {'success': False, 'error': 'Not configured'}
        try:
            import requests
            resp = requests.get(f'{self.base_url}/invoices/{doc_id}', headers={'Authorization': f'Bearer {self.api_key}'}, timeout=15)
            if resp.status_code == 200: return {'success': True, 'status': resp.json().get('status'), 'details': resp.json()}
            return {'success': False, 'error': f'HTTP {resp.status_code}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_catalog(self, ct):
        return {'success': False, 'error': f'Unknown: {ct}'}


class EcuadorProvider(FiscalProvider):
    COUNTRY_CODE = 'EC'
    CURRENCY = 'USD'

    def __init__(self, config):
        super().__init__(config)
        self.base_url = config.get('base_url', 'https://api.sri.gob.ec/v1')

    def emit_invoice(self, data):
        if not self.enabled: return {'success': False, 'error': 'Not configured'}
        try:
            import requests
            resp = requests.post(f'{self.base_url}/invoices', headers={'Authorization': f'Bearer {self.api_key}', 'Content-Type': 'application/json'}, json=data, timeout=30)
            if resp.status_code in (200, 201):
                d = resp.json()
                return {'success': True, 'document_id': d.get('id'), 'clave_acceso': d.get('clave_acceso'), 'status': d.get('status')}
            return {'success': False, 'error': f'HTTP {resp.status_code}: {resp.text[:300]}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def cancel_invoice(self, doc_id, reason):
        return {'success': False, 'error': 'Not supported'}

    def get_document_status(self, doc_id):
        if not self.enabled: return {'success': False, 'error': 'Not configured'}
        try:
            import requests
            resp = requests.get(f'{self.base_url}/invoices/{doc_id}', headers={'Authorization': f'Bearer {self.api_key}'}, timeout=15)
            if resp.status_code == 200: return {'success': True, 'status': resp.json().get('status'), 'details': resp.json()}
            return {'success': False, 'error': f'HTTP {resp.status_code}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_catalog(self, ct):
        return {'success': False, 'error': f'Unknown: {ct}'}


class FiscalProviderRegistry:
    PROVIDERS = {
        'MX': MexicoProvider, 'BR': BrazilProvider, 'CO': ColombiaProvider,
        'AR': ArgentinaProvider, 'CL': ChileProvider, 'PE': PeruProvider,
        'UY': UruguayProvider, 'EC': EcuadorProvider
    }

    @classmethod
    def get_provider(cls, cc, config):
        pc = cls.PROVIDERS.get(cc)
        return pc(config) if pc else None

    @classmethod
    def get_available_countries(cls):
        return [{'code': c, 'provider': p.__name__, 'currency': p.CURRENCY} for c, p in cls.PROVIDERS.items()]


class MultiCountryFiscalService:
    def __init__(self):
        self.providers = {}

    def configure_tenant(self, emp_id, cc, config):
        provider = FiscalProviderRegistry.get_provider(cc, config)
        if provider:
            self.providers[emp_id] = {'country': cc, 'provider': provider}
            return True
        return False

    def get_tenant_provider(self, emp_id):
        cfg = self.providers.get(emp_id)
        return cfg['provider'] if cfg else None

    def emit_invoice(self, emp_id, data):
        p = self.get_tenant_provider(emp_id)
        return p.emit_invoice(data) if p else {'success': False, 'error': 'No provider configured'}

    def cancel_invoice(self, emp_id, doc_id, reason):
        p = self.get_tenant_provider(emp_id)
        return p.cancel_invoice(doc_id, reason) if p else {'success': False, 'error': 'No provider configured'}

    def get_document_status(self, emp_id, doc_id):
        p = self.get_tenant_provider(emp_id)
        return p.get_document_status(doc_id) if p else {'success': False, 'error': 'No provider configured'}

    def get_available_countries(self):
        return FiscalProviderRegistry.get_available_countries()


def get_fiscal_service():
    if not hasattr(get_fiscal_service, '_instance'):
        get_fiscal_service._instance = MultiCountryFiscalService()
    return get_fiscal_service._instance
