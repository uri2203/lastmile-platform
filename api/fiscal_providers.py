"""Multi-Country Fiscal Providers - 8 countries (MX, BR, CO, AR, CL, PE, UY, EC)"""
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List

logger = logging.getLogger('lastmile.fiscal')


class FiscalProvider(ABC):
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.api_key = config.get('api_key', '')
        self.base_url = config.get('base_url', '')
        self.enabled = bool(self.api_key)

    @abstractmethod
    def emit_invoice(self, data): pass
    @abstractmethod
    def cancel_invoice(self, doc_id, reason): pass
    @abstractmethod
    def get_document_status(self, doc_id): pass

    def test_connection(self):
        return {'success': self.enabled, 'provider': self.__class__.__name__}


class MexicoProvider(FiscalProvider):
    COUNTRY_CODE = 'MX'
    CURRENCY = 'MXN'
    def __init__(self, c):
        super().__init__(c)
        self.base_url = c.get('base_url', 'https://www.facturapi.io/v2')
    def emit_invoice(self, d):
        if not self.enabled: return {'success': False, 'error': 'Not configured'}
        try:
            import requests
            r = requests.post(f'{self.base_url}/invoicing', headers={'Authorization': f'Bearer {self.api_key}', 'Content-Type': 'application/json'}, json=d, timeout=30)
            if r.status_code in (200, 201): dd = r.json(); return {'success': True, 'document_id': dd.get('id'), 'uuid': dd.get('uuid')}
            return {'success': False, 'error': f'HTTP {r.status_code}'}
        except Exception as e: return {'success': False, 'error': str(e)}
    def cancel_invoice(self, did, reason):
        if not self.enabled: return {'success': False, 'error': 'Not configured'}
        try:
            import requests
            r = requests.delete(f'{self.base_url}/invoicing/{did}', headers={'Authorization': f'Bearer {self.api_key}'}, json={'motivo': reason}, timeout=30)
            return {'success': r.status_code in (200, 204)}
        except Exception as e: return {'success': False, 'error': str(e)}
    def get_document_status(self, did):
        if not self.enabled: return {'success': False, 'error': 'Not configured'}
        try:
            import requests
            r = requests.get(f'{self.base_url}/invoicing/{did}', headers={'Authorization': f'Bearer {self.api_key}'}, timeout=15)
            if r.status_code == 200: return {'success': True, 'status': r.json().get('status')}
            return {'success': False, 'error': f'HTTP {r.status_code}'}
        except Exception as e: return {'success': False, 'error': str(e)}


class BrazilProvider(FiscalProvider):
    COUNTRY_CODE = 'BR'
    CURRENCY = 'BRL'
    def __init__(self, c):
        super().__init__(c)
        self.base_url = c.get('base_url', 'https://api.nfe.io/v1')
    def emit_invoice(self, d):
        if not self.enabled: return {'success': False, 'error': 'Not configured'}
        try:
            import requests
            r = requests.post(f'{self.base_url}/nfe', headers={'Authorization': f'Bearer {self.api_key}', 'Content-Type': 'application/json'}, json=d, timeout=30)
            if r.status_code in (200, 201): dd = r.json(); return {'success': True, 'document_id': dd.get('id'), 'chave': dd.get('chave')}
            return {'success': False, 'error': f'HTTP {r.status_code}'}
        except Exception as e: return {'success': False, 'error': str(e)}
    def cancel_invoice(self, did, reason):
        if not self.enabled: return {'success': False, 'error': 'Not configured'}
        try:
            import requests
            r = requests.delete(f'{self.base_url}/nfe/{did}', headers={'Authorization': f'Bearer {self.api_key}'}, timeout=30)
            return {'success': r.status_code in (200, 204)}
        except Exception as e: return {'success': False, 'error': str(e)}
    def get_document_status(self, did):
        if not self.enabled: return {'success': False, 'error': 'Not configured'}
        try:
            import requests
            r = requests.get(f'{self.base_url}/nfe/{did}', headers={'Authorization': f'Bearer {self.api_key}'}, timeout=15)
            if r.status_code == 200: return {'success': True, 'status': r.json().get('status')}
            return {'success': False, 'error': f'HTTP {r.status_code}'}
        except Exception as e: return {'success': False, 'error': str(e)}


class ColombiaProvider(FiscalProvider):
    COUNTRY_CODE = 'CO'
    CURRENCY = 'COP'
    def __init__(self, c):
        super().__init__(c)
        self.base_url = c.get('base_url', 'https://api.dian.gov.co/v1')
    def emit_invoice(self, d):
        if not self.enabled: return {'success': False, 'error': 'Not configured'}
        try:
            import requests
            r = requests.post(f'{self.base_url}/invoices', headers={'Authorization': f'Bearer {self.api_key}', 'Content-Type': 'application/json'}, json=d, timeout=30)
            if r.status_code in (200, 201): dd = r.json(); return {'success': True, 'document_id': dd.get('id'), 'cufe': dd.get('cufe')}
            return {'success': False, 'error': f'HTTP {r.status_code}'}
        except Exception as e: return {'success': False, 'error': str(e)}
    def cancel_invoice(self, did, reason):
        if not self.enabled: return {'success': False, 'error': 'Not configured'}
        try:
            import requests
            r = requests.post(f'{self.base_url}/invoices/{did}/void', headers={'Authorization': f'Bearer {self.api_key}', 'Content-Type': 'application/json'}, json={'motivo': reason}, timeout=30)
            return {'success': r.status_code in (200, 204)}
        except Exception as e: return {'success': False, 'error': str(e)}
    def get_document_status(self, did):
        if not self.enabled: return {'success': False, 'error': 'Not configured'}
        try:
            import requests
            r = requests.get(f'{self.base_url}/invoices/{did}', headers={'Authorization': f'Bearer {self.api_key}'}, timeout=15)
            if r.status_code == 200: return {'success': True, 'status': r.json().get('status')}
            return {'success': False, 'error': f'HTTP {r.status_code}'}
        except Exception as e: return {'success': False, 'error': str(e)}


class ArgentinaProvider(FiscalProvider):
    COUNTRY_CODE = 'AR'
    CURRENCY = 'ARS'
    def __init__(self, c):
        super().__init__(c)
        self.base_url = c.get('base_url', 'https://api.fiscalapi.com/v1')
    def emit_invoice(self, d):
        if not self.enabled: return {'success': False, 'error': 'Not configured'}
        try:
            import requests
            r = requests.post(f'{self.base_url}/invoices', headers={'Authorization': f'Bearer {self.api_key}', 'Content-Type': 'application/json'}, json=d, timeout=30)
            if r.status_code in (200, 201): dd = r.json(); return {'success': True, 'document_id': dd.get('id'), 'cae': dd.get('cae')}
            return {'success': False, 'error': f'HTTP {r.status_code}'}
        except Exception as e: return {'success': False, 'error': str(e)}
    def cancel_invoice(self, did, reason): return {'success': False, 'error': 'Not supported'}
    def get_document_status(self, did):
        if not self.enabled: return {'success': False, 'error': 'Not configured'}
        try:
            import requests
            r = requests.get(f'{self.base_url}/invoices/{did}', headers={'Authorization': f'Bearer {self.api_key}'}, timeout=15)
            if r.status_code == 200: return {'success': True, 'status': r.json().get('status')}
            return {'success': False, 'error': f'HTTP {r.status_code}'}
        except Exception as e: return {'success': False, 'error': str(e)}


class ChileProvider(FiscalProvider):
    COUNTRY_CODE = 'CL'
    CURRENCY = 'CLP'
    def __init__(self, c):
        super().__init__(c)
        self.base_url = c.get('base_url', 'https://api.sii.cl/v1')
    def emit_invoice(self, d):
        if not self.enabled: return {'success': False, 'error': 'Not configured'}
        try:
            import requests
            r = requests.post(f'{self.base_url}/invoices', headers={'Authorization': f'Bearer {self.api_key}', 'Content-Type': 'application/json'}, json=d, timeout=30)
            if r.status_code in (200, 201): dd = r.json(); return {'success': True, 'document_id': dd.get('id'), 'tracking_id': dd.get('tracking_id')}
            return {'success': False, 'error': f'HTTP {r.status_code}'}
        except Exception as e: return {'success': False, 'error': str(e)}
    def cancel_invoice(self, did, reason):
        if not self.enabled: return {'success': False, 'error': 'Not configured'}
        try:
            import requests
            r = requests.post(f'{self.base_url}/invoices/{did}/cancel', headers={'Authorization': f'Bearer {self.api_key}', 'Content-Type': 'application/json'}, json={'motivo': reason}, timeout=30)
            return {'success': r.status_code in (200, 204)}
        except Exception as e: return {'success': False, 'error': str(e)}
    def get_document_status(self, did):
        if not self.enabled: return {'success': False, 'error': 'Not configured'}
        try:
            import requests
            r = requests.get(f'{self.base_url}/invoices/{did}', headers={'Authorization': f'Bearer {self.api_key}'}, timeout=15)
            if r.status_code == 200: return {'success': True, 'status': r.json().get('status')}
            return {'success': False, 'error': f'HTTP {r.status_code}'}
        except Exception as e: return {'success': False, 'error': str(e)}


class PeruProvider(FiscalProvider):
    COUNTRY_CODE = 'PE'
    CURRENCY = 'PEN'
    def __init__(self, c):
        super().__init__(c)
        self.base_url = c.get('base_url', 'https://api.sunat.gob.pe/v1')
    def emit_invoice(self, d):
        if not self.enabled: return {'success': False, 'error': 'Not configured'}
        try:
            import requests
            r = requests.post(f'{self.base_url}/invoices', headers={'Authorization': f'Bearer {self.api_key}', 'Content-Type': 'application/json'}, json=d, timeout=30)
            if r.status_code in (200, 201): dd = r.json(); return {'success': True, 'document_id': dd.get('id'), 'hash': dd.get('hash')}
            return {'success': False, 'error': f'HTTP {r.status_code}'}
        except Exception as e: return {'success': False, 'error': str(e)}
    def cancel_invoice(self, did, reason): return {'success': False, 'error': 'Not supported'}
    def get_document_status(self, did):
        if not self.enabled: return {'success': False, 'error': 'Not configured'}
        try:
            import requests
            r = requests.get(f'{self.base_url}/invoices/{did}', headers={'Authorization': f'Bearer {self.api_key}'}, timeout=15)
            if r.status_code == 200: return {'success': True, 'status': r.json().get('status')}
            return {'success': False, 'error': f'HTTP {r.status_code}'}
        except Exception as e: return {'success': False, 'error': str(e)}


class UruguayProvider(FiscalProvider):
    COUNTRY_CODE = 'UY'
    CURRENCY = 'UYU'
    def __init__(self, c):
        super().__init__(c)
        self.base_url = c.get('base_url', 'https://api.dgi.gub.uy/v1')
    def emit_invoice(self, d):
        if not self.enabled: return {'success': False, 'error': 'Not configured'}
        try:
            import requests
            r = requests.post(f'{self.base_url}/invoices', headers={'Authorization': f'Bearer {self.api_key}', 'Content-Type': 'application/json'}, json=d, timeout=30)
            if r.status_code in (200, 201): dd = r.json(); return {'success': True, 'document_id': dd.get('id'), 'cae': dd.get('cae')}
            return {'success': False, 'error': f'HTTP {r.status_code}'}
        except Exception as e: return {'success': False, 'error': str(e)}
    def cancel_invoice(self, did, reason): return {'success': False, 'error': 'Not supported'}
    def get_document_status(self, did):
        if not self.enabled: return {'success': False, 'error': 'Not configured'}
        try:
            import requests
            r = requests.get(f'{self.base_url}/invoices/{did}', headers={'Authorization': f'Bearer {self.api_key}'}, timeout=15)
            if r.status_code == 200: return {'success': True, 'status': r.json().get('status')}
            return {'success': False, 'error': f'HTTP {r.status_code}'}
        except Exception as e: return {'success': False, 'error': str(e)}


class EcuadorProvider(FiscalProvider):
    COUNTRY_CODE = 'EC'
    CURRENCY = 'USD'
    def __init__(self, c):
        super().__init__(c)
        self.base_url = c.get('base_url', 'https://api.sri.gob.ec/v1')
    def emit_invoice(self, d):
        if not self.enabled: return {'success': False, 'error': 'Not configured'}
        try:
            import requests
            r = requests.post(f'{self.base_url}/invoices', headers={'Authorization': f'Bearer {self.api_key}', 'Content-Type': 'application/json'}, json=d, timeout=30)
            if r.status_code in (200, 201): dd = r.json(); return {'success': True, 'document_id': dd.get('id'), 'clave_acceso': dd.get('clave_acceso')}
            return {'success': False, 'error': f'HTTP {r.status_code}'}
        except Exception as e: return {'success': False, 'error': str(e)}
    def cancel_invoice(self, did, reason): return {'success': False, 'error': 'Not supported'}
    def get_document_status(self, did):
        if not self.enabled: return {'success': False, 'error': 'Not configured'}
        try:
            import requests
            r = requests.get(f'{self.base_url}/invoices/{did}', headers={'Authorization': f'Bearer {self.api_key}'}, timeout=15)
            if r.status_code == 200: return {'success': True, 'status': r.json().get('status')}
            return {'success': False, 'error': f'HTTP {r.status_code}'}
        except Exception as e: return {'success': False, 'error': str(e)}


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
        return p.emit_invoice(data) if p else {'success': False, 'error': 'No provider'}
    def cancel_invoice(self, emp_id, doc_id, reason):
        p = self.get_tenant_provider(emp_id)
        return p.cancel_invoice(doc_id, reason) if p else {'success': False, 'error': 'No provider'}
    def get_document_status(self, emp_id, doc_id):
        p = self.get_tenant_provider(emp_id)
        return p.get_document_status(doc_id) if p else {'success': False, 'error': 'No provider'}
    def get_available_countries(self):
        return FiscalProviderRegistry.get_available_countries()


def get_fiscal_service():
    if not hasattr(get_fiscal_service, '_instance'):
        get_fiscal_service._instance = MultiCountryFiscalService()
    return get_fiscal_service._instance
