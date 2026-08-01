"""
LAST MILE DELIVERY - Multi-Country Fiscal Providers
Abstract interface + implementations for Mexico, Brazil, Colombia, Argentina, Chile.
Platform integrates provider APIs; tenants own their fiscal data and certificates.
Platform has ZERO fiscal responsibility.
"""

import os
import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, Optional, List

logger = logging.getLogger('lastmile.fiscal')


class FiscalProvider(ABC):
    """Abstract base class for fiscal provider integrations."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.api_key = config.get('api_key', '')
        self.base_url = config.get('base_url', '')
        self.enabled = bool(self.api_key)

    @abstractmethod
    def emit_invoice(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """Emit an invoice/document. Returns {success, document_id, pdf_url, xml_url, error}"""
        pass

    @abstractmethod
    def cancel_invoice(self, document_id: str, reason: str) -> Dict[str, Any]:
        """Cancel an invoice. Returns {success, error}"""
        pass

    @abstractmethod
    def get_document_status(self, document_id: str) -> Dict[str, Any]:
        """Get document status. Returns {status, details, error}"""
        pass

    @abstractmethod
    def get_catalog(self, catalog_type: str) -> Dict[str, Any]:
        """Get tax catalog (product codes, tax regimes, etc). Returns {success, items, error}"""
        pass

    def test_connection(self) -> Dict[str, Any]:
        """Test API connection. Override in subclass for specific checks."""
        return {'success': self.enabled, 'provider': self.__class__.__name__}


class MexicoProvider(FiscalProvider):
    """Mexico CFDI 4.0 via FacturAPI."""

    COUNTRY_CODE = 'MX'
    CURRENCY = 'MXN'
    TAX_REGIMES = {
        '601': 'General de Ley Personas Morales',
        '603': 'Personas Morales con Fines no Lucrativos',
        '605': 'Sueldos y Salarios',
        '606': 'Arrendamiento',
        '610': 'Actividades Agrícolas, Ganaderas, Silvícolas y Pesqueras',
        '611': 'Para los Deficientes Intelectuales o con Discapacidad con Patria Potestad',
        '612': 'Actividades Empresariales y Profesionales',
        '614': 'Ingresos por Dividendos',
        '615': 'Sociedades y Asimiladas',
        '616': 'Sin Obligaciones Fiscales',
        '620': 'Sociedades Cooperativas de Producción',
        '621': 'Incorporación Fiscal',
        '622': 'Actividades Agrícolas, Ganaderas, Silvícolas y Pesqueras',
        '623': 'Obligados con los Regímenes de los Sectores Informal y Agropecuario',
        '624': 'General de Ley Personas Morales',
        '625': 'Régimen de las Actividades Empresariales y Profesionales',
        '626': 'Régimen Simplificado de Confianza'
    }
    FORMAS_PAGO = {
        '01': 'Efectivo',
        '02': 'Cheque nominativo',
        '03': 'Transferencia electrónica de fondos',
        '04': 'Tarjeta de crédito',
        '05': 'Monedero electrónico',
        '06': 'Dinero electrónico',
        '07': 'Vales de despensa',
        '08': 'Dación en pago',
        '09': 'Pago por subrogación',
        '10': 'Pago por consignación',
        '11': 'Letra de cambio',
        '12': 'Pago en especie',
        '13': 'Por cuenta de terceros',
        '14': 'Transferencia de deudas',
        '15': 'Tarjeta de débito',
        '16': 'Tarjeta de servicios',
        '17': 'Avería',
        '18': 'Anticipo',
        '19': 'Intercambio',
        '20': 'Facilidades de pago',
        '21': 'Gastos viajes',
        '22': 'Subrogación',
        '23': 'Pagos por servicios',
        '99': 'Otros'
    }

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.base_url = config.get('base_url', 'https://www.facturapi.io/v2')

    def emit_invoice(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        if not self.enabled:
            return {'success': False, 'error': 'FacturAPI not configured'}

        try:
            import requests
            payload = {
                'customer': {
                    'rfc': invoice_data.get('receptor_rfc', ''),
                    'nombre': invoice_data.get('receptor_razon', ''),
                    'email': invoice_data.get('receptor_email', ''),
                    'regimen_fiscal': invoice_data.get('receptor_regimen', '601'),
                    'domicilio': {
                        'pais': 'MEX',
                        'cp': invoice_data.get('receptor_cp', '00000')
                    }
                },
                'items': invoice_data.get('items', []),
                'forma_pago': invoice_data.get('forma_pago', '03'),
                'metodo_pago': invoice_data.get('metodo_pago', 'PUE'),
                'condiciones_pago': invoice_data.get('condiciones_pago', 'Contado'),
                'use': invoice_data.get('uso_cfdi', 'G03'),
                'folio': invoice_data.get('folio'),
                'series': invoice_data.get('serie', 'A'),
                'currency': invoice_data.get('currency', 'MXN'),
                'exchange_rate': invoice_data.get('exchange_rate', 1)
            }

            resp = requests.post(
                f'{self.base_url}/invoicing',
                headers={'Authorization': f'Bearer {self.api_key}', 'Content-Type': 'application/json'},
                json=payload,
                timeout=30
            )

            if resp.status_code in (200, 201):
                data = resp.json()
                return {
                    'success': True,
                    'document_id': data.get('id'),
                    'uuid': data.get('uuid'),
                    'pdf_url': data.get('pdf_url'),
                    'xml_url': data.get('xml_url'),
                    'folio': data.get('folio'),
                    'serie': data.get('serie')
                }
            else:
                return {'success': False, 'error': f'HTTP {resp.status_code}: {resp.text[:500]}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def cancel_invoice(self, document_id: str, reason: str) -> Dict[str, Any]:
        if not self.enabled:
            return {'success': False, 'error': 'FacturAPI not configured'}

        try:
            import requests
            payload = {'motivo': reason}
            resp = requests.delete(
                f'{self.base_url}/invoicing/{document_id}',
                headers={'Authorization': f'Bearer {self.api_key}', 'Content-Type': 'application/json'},
                json=payload,
                timeout=30
            )
            return {'success': resp.status_code in (200, 204), 'error': resp.text[:500] if resp.status_code not in (200, 204) else None}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_document_status(self, document_id: str) -> Dict[str, Any]:
        if not self.enabled:
            return {'success': False, 'error': 'FacturAPI not configured'}

        try:
            import requests
            resp = requests.get(
                f'{self.base_url}/invoicing/{document_id}',
                headers={'Authorization': f'Bearer {self.api_key}'},
                timeout=15
            )
            if resp.status_code == 200:
                data = resp.json()
                return {'success': True, 'status': data.get('status'), 'details': data}
            return {'success': False, 'error': f'HTTP {resp.status_code}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_catalog(self, catalog_type: str) -> Dict[str, Any]:
        if catalog_type == 'regimenes_fiscales':
            return {'success': True, 'items': self.TAX_REGIMES}
        elif catalog_type == 'formas_pago':
            return {'success': True, 'items': self.FORMAS_PAGO}
        return {'success': False, 'error': f'Unknown catalog: {catalog_type}'}


class BrazilProvider(FiscalProvider):
    """Brazil NF-e via NFe.io or FiscalAPI."""

    COUNTRY_CODE = 'BR'
    CURRENCY = 'BRL'
    PRODUCT_TYPES = {
        '0': 'Mercadoria para Revenda',
        '1': 'Materia Prima',
        '2': 'Embalagem',
        '3': 'Produto em Processo',
        '4': 'Produto Acabado',
        '5': 'Subproduto',
        '6': 'Produto Intermediário',
        '7': 'Material para Uso/Consumo',
        '8': 'Ativo Imobilizado',
        '9': 'Outros Insumos'
    }
    ICMS_ST = {
        'MG': 'Minas Gerais',
        'SP': 'São Paulo',
        'RJ': 'Rio de Janeiro',
        'BA': 'Bahia',
        'RS': 'Rio Grande do Sul',
        'PR': 'Paraná',
        'SC': 'Santa Catarina',
        'PE': 'Pernambuco',
        'CE': 'Ceará',
        'GO': 'Goiás'
    }

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.base_url = config.get('base_url', 'https://api.nfe.io/v1')

    def emit_invoice(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        if not self.enabled:
            return {'success': False, 'error': 'NFe.io not configured'}

        try:
            import requests
            payload = {
                'emitter': {
                    'cnpj': invoice_data.get('emitter_cnpj', ''),
                    'name': invoice_data.get('emitter_name', ''),
                    'state_registration': invoice_data.get('emitter_ie', ''),
                    'address': {
                        'street': invoice_data.get('emitter_street', ''),
                        'number': invoice_data.get('emitter_number', ''),
                        'neighborhood': invoice_data.get('emitter_neighborhood', ''),
                        'city': {'code': invoice_data.get('emitter_city_code', '')},
                        'state': {'acronym': invoice_data.get('emitter_state', '')},
                        'postal_code': invoice_data.get('emitter_postal_code', '')
                    }
                },
                'customer': {
                    'cnpj': invoice_data.get('customer_cnpj', ''),
                    'name': invoice_data.get('customer_name', ''),
                    'address': {
                        'street': invoice_data.get('customer_street', ''),
                        'number': invoice_data.get('customer_number', ''),
                        'neighborhood': invoice_data.get('customer_neighborhood', ''),
                        'city': {'code': invoice_data.get('customer_city_code', '')},
                        'state': {'acronym': invoice_data.get('customer_state', '')},
                        'postal_code': invoice_data.get('customer_postal_code', '')
                    }
                },
                'products': invoice_data.get('products', []),
                'natureza_operacao': invoice_data.get('natureza_operacao', 'Venda de Mercadoria'),
                'modalidade_frete': invoice_data.get('modalidade_frete', 9),
                'valor_total_produtos': invoice_data.get('valor_total', 0)
            }

            resp = requests.post(
                f'{self.base_url}/nfe',
                headers={'Authorization': f'Bearer {self.api_key}', 'Content-Type': 'application/json'},
                json=payload,
                timeout=30
            )

            if resp.status_code in (200, 201):
                data = resp.json()
                return {
                    'success': True,
                    'document_id': data.get('id'),
                    'chave': data.get('chave'),
                    'numero': data.get('numero'),
                    'serie': data.get('serie'),
                    'status': data.get('status'),
                    'xml_url': data.get('xml_url'),
                    'pdf_url': data.get('pdf_url')
                }
            return {'success': False, 'error': f'HTTP {resp.status_code}: {resp.text[:500]}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def cancel_invoice(self, document_id: str, reason: str) -> Dict[str, Any]:
        if not self.enabled:
            return {'success': False, 'error': 'NFe.io not configured'}

        try:
            import requests
            resp = requests.delete(
                f'{self.base_url}/nfe/{document_id}',
                headers={'Authorization': f'Bearer {self.api_key}'},
                params={'motivo': reason},
                timeout=30
            )
            return {'success': resp.status_code in (200, 204), 'error': resp.text[:500] if resp.status_code not in (200, 204) else None}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_document_status(self, document_id: str) -> Dict[str, Any]:
        if not self.enabled:
            return {'success': False, 'error': 'NFe.io not configured'}

        try:
            import requests
            resp = requests.get(
                f'{self.base_url}/nfe/{document_id}',
                headers={'Authorization': f'Bearer {self.api_key}'},
                timeout=15
            )
            if resp.status_code == 200:
                data = resp.json()
                return {'success': True, 'status': data.get('status'), 'details': data}
            return {'success': False, 'error': f'HTTP {resp.status_code}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_catalog(self, catalog_type: str) -> Dict[str, Any]:
        if catalog_type == 'product_types':
            return {'success': True, 'items': self.PRODUCT_TYPES}
        elif catalog_type == 'icms_states':
            return {'success': True, 'items': self.ICMS_ST}
        return {'success': False, 'error': f'Unknown catalog: {catalog_type}'}


class ColombiaProvider(FiscalProvider):
    """Colombia DIAN electronic invoicing via Validoo or Siigo."""

    COUNTRY_CODE = 'CO'
    CURRENCY = 'COP'
    DOCUMENT_TYPES = {
        '01': 'Factura Electrónica',
        '02': 'Nota Débito',
        '03': 'Nota Crédito',
        '04': 'Ajuste',
        '11': 'Factura Electrónica de Exportación',
        '12': 'Nota Débito de Exportación',
        '13': 'Nota Crédito de Exportación'
    }
    CURRENCIES = {
        'COP': 'Peso Colombiano',
        'USD': 'Dólar Estadounidense',
        'EUR': 'Euro'
    }

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.base_url = config.get('base_url', 'https://api.dian.gov.co/v1')

    def emit_invoice(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        if not self.enabled:
            return {'success': False, 'error': 'DIAN provider not configured'}

        try:
            import requests
            payload = {
                'tipo_documento': invoice_data.get('document_type', '01'),
                'numero': invoice_data.get('number', ''),
                'fecha': invoice_data.get('date', datetime.now().strftime('%Y-%m-%d')),
                'emisor': {
                    'nit': invoice_data.get('emitter_nit', ''),
                    'razon_social': invoice_data.get('emitter_name', ''),
                    'responsable_iva': invoice_data.get('emitter_responsable_iva', True),
                    'regimen_tributario': invoice_data.get('emitter_regimen', '48'),
                    'direccion': {
                        'direccion': invoice_data.get('emitter_address', ''),
                        'ciudad': invoice_data.get('emitter_city', ''),
                        'departamento': invoice_data.get('emitter_state', ''),
                        'pais': 'CO'
                    }
                },
                'receptor': {
                    'nit': invoice_data.get('receiver_nit', ''),
                    'razon_social': invoice_data.get('receiver_name', ''),
                    'responsable_iva': invoice_data.get('receiver_responsable_iva', True),
                    'regimen_tributario': invoice_data.get('receiver_regimen', '48'),
                    'direccion': {
                        'direccion': invoice_data.get('receiver_address', ''),
                        'ciudad': invoice_data.get('receiver_city', ''),
                        'departamento': invoice_data.get('receiver_state', ''),
                        'pais': 'CO'
                    }
                },
                'items': invoice_data.get('items', []),
                'moneda': invoice_data.get('currency', 'COP'),
                'medio_pago': invoice_data.get('payment_method', '1'),
                'total_base_gravable': invoice_data.get('subtotal', 0),
                'total_iva': invoice_data.get('tax', 0),
                'total_factura': invoice_data.get('total', 0)
            }

            resp = requests.post(
                f'{self.base_url}/invoices',
                headers={'Authorization': f'Bearer {self.api_key}', 'Content-Type': 'application/json'},
                json=payload,
                timeout=30
            )

            if resp.status_code in (200, 201):
                data = resp.json()
                return {
                    'success': True,
                    'document_id': data.get('id'),
                    'cufe': data.get('cufe'),
                    'numero': data.get('numero'),
                    'pdf_url': data.get('pdf_url'),
                    'xml_url': data.get('xml_url'),
                    'status': data.get('status')
                }
            return {'success': False, 'error': f'HTTP {resp.status_code}: {resp.text[:500]}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def cancel_invoice(self, document_id: str, reason: str) -> Dict[str, Any]:
        if not self.enabled:
            return {'success': False, 'error': 'DIAN provider not configured'}

        try:
            import requests
            resp = requests.post(
                f'{self.base_url}/invoices/{document_id}/void',
                headers={'Authorization': f'Bearer {self.api_key}', 'Content-Type': 'application/json'},
                json={'motivo': reason},
                timeout=30
            )
            return {'success': resp.status_code in (200, 204), 'error': resp.text[:500] if resp.status_code not in (200, 204) else None}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_document_status(self, document_id: str) -> Dict[str, Any]:
        if not self.enabled:
            return {'success': False, 'error': 'DIAN provider not configured'}

        try:
            import requests
            resp = requests.get(
                f'{self.base_url}/invoices/{document_id}',
                headers={'Authorization': f'Bearer {self.api_key}'},
                timeout=15
            )
            if resp.status_code == 200:
                data = resp.json()
                return {'success': True, 'status': data.get('status'), 'details': data}
            return {'success': False, 'error': f'HTTP {resp.status_code}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_catalog(self, catalog_type: str) -> Dict[str, Any]:
        if catalog_type == 'document_types':
            return {'success': True, 'items': self.DOCUMENT_TYPES}
        elif catalog_type == 'currencies':
            return {'success': True, 'items': self.CURRENCIES}
        return {'success': False, 'error': f'Unknown catalog: {catalog_type}'}


class ArgentinaProvider(FiscalProvider):
    """Argentina AFIP electronic invoicing via fiscalapi.com."""

    COUNTRY_CODE = 'AR'
    CURRENCY = 'ARS'
    CUIT_TYPES = {
        '20': 'Persona Física',
        '23': 'Persona Jurídica',
        '24': 'Persona Jurídica Extranjera',
        '27': 'Persona Física Extranjera',
        '30': 'Persona Jurídica',
        '33': 'Persona Jurídica Extranjera',
        '34': 'Persona Jurídica Extranjera'
    }
    CONCEPTOS = {
        '1': 'Productos',
        '2': 'Servicios',
        '3': 'Productos y Servicios',
        '4': 'Otras operaciones'
    }

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.base_url = config.get('base_url', 'https://api.fiscalapi.com/v1')

    def emit_invoice(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        if not self.enabled:
            return {'success': False, 'error': 'FiscalAPI not configured'}

        try:
            import requests
            payload = {
                'cuit_emisor': invoice_data.get('emitter_cuit', ''),
                'punto_de_venta': invoice_data.get('punto_venta', 1),
                'tipo_comprobante': invoice_data.get('comprobante_type', 'factura'),
                'concepto': invoice_data.get('concepto', '2'),
                'fecha_emision': invoice_data.get('date', datetime.now().strftime('%Y-%m-%d')),
                'tipo_doc_receptor': invoice_data.get('receiver_doc_type', '80'),
                'nro_doc_receptor': invoice_data.get('receiver_cuit', ''),
                'razon_social_receptor': invoice_data.get('receiver_name', ''),
                'domicilio_receptor': invoice_data.get('receiver_address', ''),
                'moneda': invoice_data.get('currency', 'ARS'),
                'items': invoice_data.get('items', []),
                'total': invoice_data.get('total', 0),
                'total_iva': invoice_data.get('tax', 0),
                'total_neto': invoice_data.get('subtotal', 0)
            }

            resp = requests.post(
                f'{self.base_url}/invoices',
                headers={'Authorization': f'Bearer {self.api_key}', 'Content-Type': 'application/json'},
                json=payload,
                timeout=30
            )

            if resp.status_code in (200, 201):
                data = resp.json()
                return {
                    'success': True,
                    'document_id': data.get('id'),
                    'cae': data.get('cae'),
                    'vencimiento_cae': data.get('vencimiento_cae'),
                    'numero': data.get('numero'),
                    'pdf_url': data.get('pdf_url'),
                    'xml_url': data.get('xml_url')
                }
            return {'success': False, 'error': f'HTTP {resp.status_code}: {resp.text[:500]}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def cancel_invoice(self, document_id: str, reason: str) -> Dict[str, Any]:
        if not self.enabled:
            return {'success': False, 'error': 'FiscalAPI not configured'}

        try:
            import requests
            resp = requests.delete(
                f'{self.base_url}/invoices/{document_id}',
                headers={'Authorization': f'Bearer {self.api_key}'},
                params={'motivo': reason},
                timeout=30
            )
            return {'success': resp.status_code in (200, 204), 'error': resp.text[:500] if resp.status_code not in (200, 204) else None}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_document_status(self, document_id: str) -> Dict[str, Any]:
        if not self.enabled:
            return {'success': False, 'error': 'FiscalAPI not configured'}

        try:
            import requests
            resp = requests.get(
                f'{self.base_url}/invoices/{document_id}',
                headers={'Authorization': f'Bearer {self.api_key}'},
                timeout=15
            )
            if resp.status_code == 200:
                data = resp.json()
                return {'success': True, 'status': data.get('status'), 'details': data}
            return {'success': False, 'error': f'HTTP {resp.status_code}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_catalog(self, catalog_type: str) -> Dict[str, Any]:
        if catalog_type == 'cuit_types':
            return {'success': True, 'items': self.CUIT_TYPES}
        elif catalog_type == 'conceptos':
            return {'success': True, 'items': self.CONCEPTOS}
        return {'success': False, 'error': f'Unknown catalog: {catalog_type}'}


class ChileProvider(FiscalProvider):
    """Chile SII electronic invoicing via SII SDK."""

    COUNTRY_CODE = 'CL'
    CURRENCY = 'CLP'
    DOCUMENT_TYPES = {
        '33': 'Factura Electrónica',
        '34': 'Factura No Afecta Electrónica',
        '39': 'Boleta Electrónica',
        '41': 'Boleta No Afecta Electrónica',
        '52': 'Guía de Despacho Electrónica',
        '56': 'Nota de Débito Electrónica',
        '61': 'Nota de Crédito Electrónica'
    }
    IVA_RATES = {
        'IVA': 19,
        'IVA_BC': 19,
        'IVA_0': 0,
        'IVA_EX': 0
    }

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.base_url = config.get('base_url', 'https://api.sii.cl/v1')

    def emit_invoice(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        if not self.enabled:
            return {'success': False, 'error': 'SII provider not configured'}

        try:
            import requests
            payload = {
                'tipo_documento': invoice_data.get('document_type', '33'),
                'folio': invoice_data.get('folio', 0),
                'fecha_emision': invoice_data.get('date', datetime.now().strftime('%Y-%m-%d')),
                'emisor': {
                    'rut': invoice_data.get('emitter_rut', ''),
                    'razon_social': invoice_data.get('emitter_name', ''),
                    'giro': invoice_data.get('emitter_giro', ''),
                    'direccion': {
                        'direccion': invoice_data.get('emitter_address', ''),
                        'comuna': invoice_data.get('emitter_commune', ''),
                        'ciudad': invoice_data.get('emitter_city', ''),
                        'region': invoice_data.get('emitter_region', '')
                    }
                },
                'receptor': {
                    'rut': invoice_data.get('receiver_rut', ''),
                    'razon_social': invoice_data.get('receiver_name', ''),
                    'giro': invoice_data.get('receiver_giro', ''),
                    'direccion': {
                        'direccion': invoice_data.get('receiver_address', ''),
                        'comuna': invoice_data.get('receiver_commune', ''),
                        'ciudad': invoice_data.get('receiver_city', ''),
                        'region': invoice_data.get('receiver_region', '')
                    }
                },
                'items': invoice_data.get('items', []),
                'medio_pago': invoice_data.get('payment_method', '33'),
                'total_neto': invoice_data.get('subtotal', 0),
                'total_iva': invoice_data.get('tax', 0),
                'total': invoice_data.get('total', 0),
                'moneda': invoice_data.get('currency', 'CLP')
            }

            resp = requests.post(
                f'{self.base_url}/invoices',
                headers={'Authorization': f'Bearer {self.api_key}', 'Content-Type': 'application/json'},
                json=payload,
                timeout=30
            )

            if resp.status_code in (200, 201):
                data = resp.json()
                return {
                    'success': True,
                    'document_id': data.get('id'),
                    'tracking_id': data.get('tracking_id'),
                    'folio': data.get('folio'),
                    'status': data.get('status'),
                    'pdf_url': data.get('pdf_url'),
                    'xml_url': data.get('xml_url')
                }
            return {'success': False, 'error': f'HTTP {resp.status_code}: {resp.text[:500]}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def cancel_invoice(self, document_id: str, reason: str) -> Dict[str, Any]:
        if not self.enabled:
            return {'success': False, 'error': 'SII provider not configured'}

        try:
            import requests
            resp = requests.post(
                f'{self.base_url}/invoices/{document_id}/cancel',
                headers={'Authorization': f'Bearer {self.api_key}', 'Content-Type': 'application/json'},
                json={'motivo': reason},
                timeout=30
            )
            return {'success': resp.status_code in (200, 204), 'error': resp.text[:500] if resp.status_code not in (200, 204) else None}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_document_status(self, document_id: str) -> Dict[str, Any]:
        if not self.enabled:
            return {'success': False, 'error': 'SII provider not configured'}

        try:
            import requests
            resp = requests.get(
                f'{self.base_url}/invoices/{document_id}',
                headers={'Authorization': f'Bearer {self.api_key}'},
                timeout=15
            )
            if resp.status_code == 200:
                data = resp.json()
                return {'success': True, 'status': data.get('status'), 'details': data}
            return {'success': False, 'error': f'HTTP {resp.status_code}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_catalog(self, catalog_type: str) -> Dict[str, Any]:
        if catalog_type == 'document_types':
            return {'success': True, 'items': self.DOCUMENT_TYPES}
        elif catalog_type == 'iva_rates':
            return {'success': True, 'items': self.IVA_RATES}
        return {'success': False, 'error': f'Unknown catalog: {catalog_type}'}


class PeruProvider(FiscalProvider):
    """Peru SUNAT electronic invoicing."""

    COUNTRY_CODE = 'PE'
    CURRENCY = 'PEN'
    DOCUMENT_TYPES = {
        '01': 'Factura',
        '03': 'Boleta de Venta',
        '07': 'Nota de Credito',
        '08': 'Nota de Debito'
    }
    IGV_RATES = {
        'IGV': 18,
        'IGV_0': 0,
        'IGV_EX': 0
    }

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.base_url = config.get('base_url', 'https://api.sunat.gob.pe/v1')

    def emit_invoice(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        if not self.enabled:
            return {'success': False, 'error': 'SUNAT provider not configured'}

        try:
            import requests
            payload = {
                'tipo_documento': invoice_data.get('document_type', '01'),
                'serie': invoice_data.get('serie', 'F001'),
                'correlativo': invoice_data.get('correlativo', 1),
                'fecha_emision': invoice_data.get('date', datetime.now().strftime('%Y-%m-%d')),
                'emisor': {
                    'ruc': invoice_data.get('emitter_ruc', ''),
                    'razon_social': invoice_data.get('emitter_name', ''),
                    'direccion': {
                        'direccion': invoice_data.get('emitter_address', ''),
                        'ubigeo': invoice_data.get('emitter_ubigeo', ''),
                        'departamento': invoice_data.get('emitter_department', ''),
                        'provincia': invoice_data.get('emitter_province', ''),
                        'distrito': invoice_data.get('emitter_district', '')
                    }
                },
                'receptor': {
                    'tipo_doc': invoice_data.get('receiver_doc_type', '6'),
                    'num_doc': invoice_data.get('receiver_ruc', ''),
                    'razon_social': invoice_data.get('receiver_name', ''),
                    'direccion': invoice_data.get('receiver_address', '')
                },
                'items': invoice_data.get('items', []),
                'moneda': invoice_data.get('currency', 'PEN'),
                'total_gravado': invoice_data.get('subtotal', 0),
                'total_igv': invoice_data.get('tax', 0),
                'total': invoice_data.get('total', 0)
            }

            resp = requests.post(
                f'{self.base_url}/invoices',
                headers={'Authorization': f'Bearer {self.api_key}', 'Content-Type': 'application/json'},
                json=payload,
                timeout=30
            )

            if resp.status_code in (200, 201):
                data = resp.json()
                return {
                    'success': True,
                    'document_id': data.get('id'),
                    'hash': data.get('hash'),
                    'numero': data.get('numero'),
                    'pdf_url': data.get('pdf_url'),
                    'xml_url': data.get('xml_url'),
                    'cdr_url': data.get('cdr_url'),
                    'status': data.get('status')
                }
            return {'success': False, 'error': f'HTTP {resp.status_code}: {resp.text[:500]}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def cancel_invoice(self, document_id: str, reason: str) -> Dict[str, Any]:
        if not self.enabled:
            return {'success': False, 'error': 'SUNAT provider not configured'}

        try:
            import requests
            resp = requests.delete(
                f'{self.base_url}/invoices/{document_id}',
                headers={'Authorization': f'Bearer {self.api_key}'},
                params={'motivo': reason},
                timeout=30
            )
            return {'success': resp.status_code in (200, 204), 'error': resp.text[:500] if resp.status_code not in (200, 204) else None}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_document_status(self, document_id: str) -> Dict[str, Any]:
        if not self.enabled:
            return {'success': False, 'error': 'SUNAT provider not configured'}

        try:
            import requests
            resp = requests.get(
                f'{self.base_url}/invoices/{document_id}',
                headers={'Authorization': f'Bearer {self.api_key}'},
                timeout=15
            )
            if resp.status_code == 200:
                data = resp.json()
                return {'success': True, 'status': data.get('status'), 'details': data}
            return {'success': False, 'error': f'HTTP {resp.status_code}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_catalog(self, catalog_type: str) -> Dict[str, Any]:
        if catalog_type == 'document_types':
            return {'success': True, 'items': self.DOCUMENT_TYPES}
        elif catalog_type == 'igv_rates':
            return {'success': True, 'items': self.IGV_RATES}
        return {'success': False, 'error': f'Unknown catalog: {catalog_type}'}


class UruguayProvider(FiscalProvider):
    """Uruguay DGI electronic invoicing."""

    COUNTRY_CODE = 'UY'
    CURRENCY = 'UYU'
    DOCUMENT_TYPES = {
        '1': 'Factura',
        '2': 'Nota de Credito',
        '3': 'Nota de Debito',
        '4': 'e-Ticket'
    }
    IVA_RATES = {
        'IVA_22': 22,
        'IVA_10': 10,
        'IVA_0': 0,
        'IVA_EX': 0
    }

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.base_url = config.get('base_url', 'https://api.dgi.gub.uy/v1')

    def emit_invoice(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        if not self.enabled:
            return {'success': False, 'error': 'DGI provider not configured'}

        try:
            import requests
            payload = {
                'tipo_documento': invoice_data.get('document_type', '1'),
                'serie': invoice_data.get('serie', 'A'),
                'numero': invoice_data.get('number', 1),
                'fecha_emision': invoice_data.get('date', datetime.now().strftime('%Y-%m-%d')),
                'emisor': {
                    'rut': invoice_data.get('emitter_rut', ''),
                    'razon_social': invoice_data.get('emitter_name', ''),
                    'direccion': {
                        'direccion': invoice_data.get('emitter_address', ''),
                        'departamento': invoice_data.get('emitter_department', ''),
                        'ciudad': invoice_data.get('emitter_city', '')
                    }
                },
                'receptor': {
                    'tipo_doc': invoice_data.get('receiver_doc_type', '2'),
                    'num_doc': invoice_data.get('receiver_rut', ''),
                    'razon_social': invoice_data.get('receiver_name', ''),
                    'direccion': invoice_data.get('receiver_address', '')
                },
                'items': invoice_data.get('items', []),
                'moneda': invoice_data.get('currency', 'UYU'),
                'total_gravado': invoice_data.get('subtotal', 0),
                'total_iva': invoice_data.get('tax', 0),
                'total': invoice_data.get('total', 0)
            }

            resp = requests.post(
                f'{self.base_url}/invoices',
                headers={'Authorization': f'Bearer {self.api_key}', 'Content-Type': 'application/json'},
                json=payload,
                timeout=30
            )

            if resp.status_code in (200, 201):
                data = resp.json()
                return {
                    'success': True,
                    'document_id': data.get('id'),
                    'cae': data.get('cae'),
                    'numero': data.get('numero'),
                    'pdf_url': data.get('pdf_url'),
                    'xml_url': data.get('xml_url'),
                    'status': data.get('status')
                }
            return {'success': False, 'error': f'HTTP {resp.status_code}: {resp.text[:500]}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def cancel_invoice(self, document_id: str, reason: str) -> Dict[str, Any]:
        if not self.enabled:
            return {'success': False, 'error': 'DGI provider not configured'}

        try:
            import requests
            resp = requests.delete(
                f'{self.base_url}/invoices/{document_id}',
                headers={'Authorization': f'Bearer {self.api_key}'},
                params={'motivo': reason},
                timeout=30
            )
            return {'success': resp.status_code in (200, 204), 'error': resp.text[:500] if resp.status_code not in (200, 204) else None}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_document_status(self, document_id: str) -> Dict[str, Any]:
        if not self.enabled:
            return {'success': False, 'error': 'DGI provider not configured'}

        try:
            import requests
            resp = requests.get(
                f'{self.base_url}/invoices/{document_id}',
                headers={'Authorization': f'Bearer {self.api_key}'},
                timeout=15
            )
            if resp.status_code == 200:
                data = resp.json()
                return {'success': True, 'status': data.get('status'), 'details': data}
            return {'success': False, 'error': f'HTTP {resp.status_code}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_catalog(self, catalog_type: str) -> Dict[str, Any]:
        if catalog_type == 'document_types':
            return {'success': True, 'items': self.DOCUMENT_TYPES}
        elif catalog_type == 'iva_rates':
            return {'success': True, 'items': self.IVA_RATES}
        return {'success': False, 'error': f'Unknown catalog: {catalog_type}'}


class EcuadorProvider(FiscalProvider):
    """Ecuador SRI electronic invoicing."""

    COUNTRY_CODE = 'EC'
    CURRENCY = 'USD'
    DOCUMENT_TYPES = {
        '01': 'Factura',
        '04': 'Liquidacion de Compra',
        '05': 'Nota de Venta',
        '06': 'Retencion',
        '07': 'Nota de Credito',
        '08': 'Nota de Debito',
        '09': 'Guia de Remision'
    }
    TARIFAS_IVA = {
        'IVA_15': 15,
        'IVA_0': 0,
        'IVA_EX': 0
    }

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.base_url = config.get('base_url', 'https://api.sri.gob.ec/v1')

    def emit_invoice(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        if not self.enabled:
            return {'success': False, 'error': 'SRI provider not configured'}

        try:
            import requests
            payload = {
                'tipo_documento': invoice_data.get('document_type', '01'),
                'serie': invoice_data.get('serie', '001'),
                'secuencial': invoice_data.get('sequential', 1),
                'fecha_emision': invoice_data.get('date', datetime.now().strftime('%Y-%m-%dT%H:%M:%S')),
                'emisor': {
                    'ruc': invoice_data.get('emitter_ruc', ''),
                    'razon_social': invoice_data.get('emitter_name', ''),
                    'direccion': {
                        'direccion': invoice_data.get('emitter_address', ''),
                        'ciudad': invoice_data.get('emitter_city', ''),
                        'provincia': invoice_data.get('emitter_province', '')
                    }
                },
                'receptor': {
                    'tipo_doc': invoice_data.get('receiver_doc_type', '04'),
                    'num_doc': invoice_data.get('receiver_ruc', ''),
                    'razon_social': invoice_data.get('receiver_name', ''),
                    'direccion': invoice_data.get('receiver_address', ''),
                    'email': invoice_data.get('receiver_email', '')
                },
                'items': invoice_data.get('items', []),
                'moneda': invoice_data.get('currency', 'USD'),
                'total_sin_impuestos': invoice_data.get('subtotal', 0),
                'total_con_impuestos': invoice_data.get('total', 0),
                'importe_total': invoice_data.get('total', 0),
                'propina': invoice_data.get('tip', 0)
            }

            resp = requests.post(
                f'{self.base_url}/invoices',
                headers={'Authorization': f'Bearer {self.api_key}', 'Content-Type': 'application/json'},
                json=payload,
                timeout=30
            )

            if resp.status_code in (200, 201):
                data = resp.json()
                return {
                    'success': True,
                    'document_id': data.get('id'),
                    'clave_acceso': data.get('clave_acceso'),
                    'numero': data.get('numero'),
                    'pdf_url': data.get('pdf_url'),
                    'xml_url': data.get('xml_url'),
                    'xml_firmado': data.get('xml_firmado'),
                    'status': data.get('status')
                }
            return {'success': False, 'error': f'HTTP {resp.status_code}: {resp.text[:500]}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def cancel_invoice(self, document_id: str, reason: str) -> Dict[str, Any]:
        if not self.enabled:
            return {'success': False, 'error': 'SRI provider not configured'}

        try:
            import requests
            resp = requests.delete(
                f'{self.base_url}/invoices/{document_id}',
                headers={'Authorization': f'Bearer {self.api_key}'},
                params={'motivo': reason},
                timeout=30
            )
            return {'success': resp.status_code in (200, 204), 'error': resp.text[:500] if resp.status_code not in (200, 204) else None}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_document_status(self, document_id: str) -> Dict[str, Any]:
        if not self.enabled:
            return {'success': False, 'error': 'SRI provider not configured'}

        try:
            import requests
            resp = requests.get(
                f'{self.base_url}/invoices/{document_id}',
                headers={'Authorization': f'Bearer {self.api_key}'},
                timeout=15
            )
            if resp.status_code == 200:
                data = resp.json()
                return {'success': True, 'status': data.get('status'), 'details': data}
            return {'success': False, 'error': f'HTTP {resp.status_code}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_catalog(self, catalog_type: str) -> Dict[str, Any]:
        if catalog_type == 'document_types':
            return {'success': True, 'items': self.DOCUMENT_TYPES}
        elif catalog_type == 'tarifas_iva':
            return {'success': True, 'items': self.TARIFAS_IVA}
        return {'success': False, 'error': f'Unknown catalog: {catalog_type}'}


class FiscalProviderRegistry:
    """Registry for managing fiscal providers by country."""

    PROVIDERS = {
        'MX': MexicoProvider,
        'BR': BrazilProvider,
        'CO': ColombiaProvider,
        'AR': ArgentinaProvider,
        'CL': ChileProvider,
        'PE': PeruProvider,
        'UY': UruguayProvider,
        'EC': EcuadorProvider
    }

    @classmethod
    def get_provider(cls, country_code: str, config: Dict[str, Any]) -> Optional[FiscalProvider]:
        """Get fiscal provider for a country."""
        provider_class = cls.PROVIDERS.get(country_code)
        if provider_class:
            return provider_class(config)
        return None

    @classmethod
    def get_available_countries(cls) -> List[Dict[str, str]]:
        """Get list of available countries with their providers."""
        countries = []
        for code, provider_class in cls.PROVIDERS.items():
            countries.append({
                'code': code,
                'provider': provider_class.__name__,
                'currency': provider_class.CURRENCY
            })
        return countries

    @classmethod
    def get_tax_catalogs(cls, country_code: str) -> Dict[str, Any]:
        """Get all available tax catalogs for a country."""
        provider_class = cls.PROVIDERS.get(country_code)
        if not provider_class:
            return {'success': False, 'error': f'No provider for {country_code}'}

        catalogs = {}
        if country_code == 'MX':
            catalogs = {
                'regimenes_fiscales': MexicoProvider.TAX_REGIMES,
                'formas_pago': MexicoProvider.FORMAS_PAGO
            }
        elif country_code == 'BR':
            catalogs = {
                'product_types': BrazilProvider.PRODUCT_TYPES,
                'icms_states': BrazilProvider.ICMS_ST
            }
        elif country_code == 'CO':
            catalogs = {
                'document_types': ColombiaProvider.DOCUMENT_TYPES,
                'currencies': ColombiaProvider.CURRENCIES
            }
        elif country_code == 'AR':
            catalogs = {
                'cuit_types': ArgentinaProvider.CUIT_TYPES,
                'conceptos': ArgentinaProvider.CONCEPTOS
            }
        elif country_code == 'CL':
            catalogs = {
                'document_types': ChileProvider.DOCUMENT_TYPES,
                'iva_rates': ChileProvider.IVA_RATES
            }
        elif country_code == 'PE':
            catalogs = {
                'document_types': PeruProvider.DOCUMENT_TYPES,
                'igv_rates': PeruProvider.IGV_RATES
            }
        elif country_code == 'UY':
            catalogs = {
                'document_types': UruguayProvider.DOCUMENT_TYPES,
                'iva_rates': UruguayProvider.IVA_RATES
            }
        elif country_code == 'EC':
            catalogs = {
                'document_types': EcuadorProvider.DOCUMENT_TYPES,
                'tarifas_iva': EcuadorProvider.TARIFAS_IVA
            }

        return {'success': True, 'country': country_code, 'catalogs': catalogs}


class MultiCountryFiscalService:
    """Service for managing fiscal operations across multiple countries."""

    def __init__(self):
        self.providers = {}

    def configure_tenant(self, emp_id: int, country_code: str, provider_config: Dict[str, Any]):
        """Configure fiscal provider for a tenant (empresa)."""
        provider = FiscalProviderRegistry.get_provider(country_code, provider_config)
        if provider:
            self.providers[emp_id] = {
                'country': country_code,
                'provider': provider,
                'configured_at': datetime.now().isoformat()
            }
            logger.info(f'[FISCAL] Configured {country_code} provider for empresa {emp_id}')
            return True
        logger.warning(f'[FISCAL] No provider for country {country_code}')
        return False

    def get_tenant_provider(self, emp_id: int) -> Optional[FiscalProvider]:
        """Get fiscal provider for a tenant."""
        config = self.providers.get(emp_id)
        if config:
            return config['provider']
        return None

    def get_tenant_country(self, emp_id: int) -> Optional[str]:
        """Get country code for a tenant."""
        config = self.providers.get(emp_id)
        if config:
            return config['country']
        return None

    def emit_invoice(self, emp_id: int, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """Emit invoice using tenant's configured provider."""
        provider = self.get_tenant_provider(emp_id)
        if not provider:
            return {'success': False, 'error': 'No fiscal provider configured for this empresa'}

        return provider.emit_invoice(invoice_data)

    def cancel_invoice(self, emp_id: int, document_id: str, reason: str) -> Dict[str, Any]:
        """Cancel invoice using tenant's configured provider."""
        provider = self.get_tenant_provider(emp_id)
        if not provider:
            return {'success': False, 'error': 'No fiscal provider configured for this empresa'}

        return provider.cancel_invoice(document_id, reason)

    def get_document_status(self, emp_id: int, document_id: str) -> Dict[str, Any]:
        """Get document status using tenant's configured provider."""
        provider = self.get_tenant_provider(emp_id)
        if not provider:
            return {'success': False, 'error': 'No fiscal provider configured for this empresa'}

        return provider.get_document_status(document_id)

    def get_available_countries(self) -> List[Dict[str, str]]:
        """Get list of available countries."""
        return FiscalProviderRegistry.get_available_countries()

    def get_tax_catalogs(self, country_code: str) -> Dict[str, Any]:
        """Get tax catalogs for a country."""
        return FiscalProviderRegistry.get_tax_catalogs(country_code)


def get_fiscal_service():
    """Get or create multi-country fiscal service."""
    if not hasattr(get_fiscal_service, '_instance'):
        get_fiscal_service._instance = MultiCountryFiscalService()
    return get_fiscal_service._instance


def get_fiscal_provider_for_empresa(emp_id: int):
    """Get fiscal provider for a specific empresa."""
    service = get_fiscal_service()
    return service.get_tenant_provider(emp_id)


def get_fiscal_country_for_empresa(emp_id: int):
    """Get country code for a specific empresa."""
    service = get_fiscal_service()
    return service.get_tenant_country(emp_id)
