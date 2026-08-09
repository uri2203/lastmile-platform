"""
LAST MILE DELIVERY - CFDI 4.0 Service
Integration with FacturAPI for Mexican electronic invoicing.
Falls back to mock mode when no API key is configured.
"""

import os
import json
import logging
from datetime import datetime

logger = logging.getLogger('lastmile.cfdi')


class CFDIService:
    def __init__(self):
        self.api_key = os.environ.get('FACTURAPI_API_KEY', '')
        self.enabled = bool(self.api_key)
        self.base_url = 'https://www.facturapi.io/v2'
        self.empresa_data = {}

        if self.enabled:
            logger.info('[CFDI] FacturAPI configured')
        else:
            logger.info('[CFDI] No FACTURAPI_API_KEY - mock mode')

    def _headers(self):
        return {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

    def configure_empresa(self, emp_id):
        """Load empresa CFDI configuration from DB."""
        from db import query
        try:
            empresa = query(
                "SELECT EMP_RFC, EMP_NOMBRE, EMP_EMAIL, EMP_DIRECCION "
                "FROM EMPRESAS WHERE EMP_ID=?", [emp_id]
            )
            if empresa:
                self.empresa_data = empresa[0]
        except Exception:
            pass

    def create_customer(self, rfc, nombre, email=None, direccion=None, cp=None):
        """Create a customer in FacturAPI for CFDI generation."""
        if not self.enabled:
            return {'success': True, 'id': 'mock_customer', 'mode': 'mock'}

        try:
            import requests
            payload = {
                'rfc': rfc,
                'nombre': nombre,
                'email': email,
                'regimen_fiscal': '601',  # General de Ley Personas Morales
                'domicilio': {
                    'pais': 'MEX',
                    'cp': cp or '06600'
                }
            }
            if direccion:
                payload['domicilio']['calle'] = direccion

            resp = requests.post(
                f'{self.base_url}/customers',
                headers=self._headers(),
                json=payload,
                timeout=15
            )
            if resp.status_code in (200, 201):
                data = resp.json()
                return {'success': True, 'id': data.get('id')}
            else:
                logger.error(f'[CFDI] Customer create error {resp.status_code}: {resp.text[:200]}')
                return {'success': False, 'error': resp.text[:200]}
        except Exception as e:
            return {'success': False, 'error': 'Error de facturacion'}

    def create_product(self, nombre, clave=None, precio=0, unidad='H87'):
        """Create a product/service in FacturAPI."""
        if not self.enabled:
            return {'success': True, 'id': 'mock_product', 'mode': 'mock'}

        try:
            import requests
            payload = {
                'clave': clave or 'SERV001',
                'nombre': nombre,
                'unidad': unidad,
                'precio': precio
            }
            resp = requests.post(
                f'{self.base_url}/products',
                headers=self._headers(),
                json=payload,
                timeout=15
            )
            if resp.status_code in (200, 201):
                data = resp.json()
                return {'success': True, 'id': data.get('id')}
            else:
                return {'success': False, 'error': resp.text[:200]}
        except Exception as e:
            return {'success': False, 'error': 'Error de facturacion'}

    def create_invoice(self, pedido_id, emp_id):
        """Create and stamp a CFDI for a pedido."""
        self.configure_empresa(emp_id)

        if not self.enabled:
            return self._mock_invoice(pedido_id, emp_id)

        from db import query
        try:
            pedido = query(
                "SELECT * FROM PEDIDOS WHERE PED_ID=? AND EMP_ID=?", [pedido_id, emp_id]
            )
            if not pedido:
                return {'success': False, 'error': 'Pedido no encontrado'}

            p = pedido[0]

            # Get or create customer
            rfc = p.get('PED_CLIENTE_RFC', 'XAXX010101010')
            nombre = p.get('PED_CLIENTE_NOMBRE', 'Publico General')

            # Build invoice items
            items = [{
                'quantity': p.get('PED_BULTOS', 1),
                'product': {
                    'clave': 'SERV001',
                    'nombre': 'Servicio de envio/delivery',
                    'unidad': 'H87',
                    'precio': float(p.get('PED_COSTO_TOTAL', 0) or 0) / max(p.get('PED_BULTOS', 1), 1)
                }
            }]

            payload = {
                'customer': {
                    'rfc': rfc,
                    'nombre': nombre,
                    'email': p.get('PED_CLIENTE_EMAIL'),
                    'regimen_fiscal': '601',
                    'domicilio': {'pais': 'MEX', 'cp': '06600'}
                },
                'items': items,
                'forma_pago': '01',  # Efectivo
                'metodo_pago': 'PUE',  # Pago en una sola exhibicion
                'regimen_fiscal': self.empresa_data.get('EMP_REGIMEN_FISCAL', '601'),
                'lugar_expedicion': self.empresa_data.get('EMP_CP', '06600'),
                'uso_cfdi': 'G03'  # Gastos en general
            }

            resp = requests.post(
                f'{self.base_url}/invoices',
                headers=self._headers(),
                json=payload,
                timeout=30
            )

            if resp.status_code in (200, 201):
                data = resp.json()
                # Save to DB
                self._save_cfdi(pedido_id, emp_id, data, p)
                return {
                    'success': True,
                    'uuid': data.get('uuid'),
                    'folio': data.get('folio'),
                    'serie': data.get('serie'),
                    'xml': data.get('xml'),
                    'pdf_url': data.get('pdf_url'),
                    'tipo': 'TIMBRADA'
                }
            else:
                logger.error(f'[CFDI] Invoice error {resp.status_code}: {resp.text[:300]}')
                return {'success': False, 'error': resp.text[:200]}

        except Exception as e:
            logger.error(f'[CFDI] Exception: {str(e)}')
            return {'success': False, 'error': 'Error de facturacion'}

    def cancel_invoice(self, cfdi_id, emp_id, motivo='Cancelacion'):
        """Cancel a stamped CFDI."""
        if not self.enabled:
            return {'success': True, 'tipo': 'CANCELADA', 'mode': 'mock'}

        from db import query
        try:
            cfdi = query(
                "SELECT FAC_UUID, FAC_SERIE, FAC_FOLIO FROM CFDI_FACTURAS WHERE FAC_ID=? AND EMP_ID=?",
                [cfdi_id, emp_id]
            )
            if not cfdi:
                return {'success': False, 'error': 'CFDI no encontrado'}

            uuid = cfdi[0].get('FAC_UUID')
            if not uuid:
                return {'success': False, 'error': 'UUID no disponible'}

            import requests
            resp = requests.delete(
                f'{self.base_url}/invoices/{uuid}',
                headers=self._headers(),
                json={'motivo': motivo},
                timeout=15
            )

            if resp.status_code in (200, 204):
                from db import execute
                execute(
                    "UPDATE CFDI_FACTURAS SET FAC_ESTATUS='CANCELADA', FAC_MOTIVO_CANCELACION=? WHERE FAC_ID=? AND EMP_ID=?",
                    [motivo, cfdi_id, emp_id]
                )
                return {'success': True, 'tipo': 'CANCELADA'}
            else:
                return {'success': False, 'error': resp.text[:200]}

        except Exception as e:
            return {'success': False, 'error': 'Error de facturacion'}

    def get_status(self):
        """Check if FacturAPI is configured and responding."""
        if not self.enabled:
            return {'configured': False, 'mode': 'mock', 'message': 'No API key configured'}

        try:
            import requests
            resp = requests.get(
                f'{self.base_url}/company',
                headers=self._headers(),
                timeout=10
            )
            if resp.status_code == 200:
                data = resp.json()
                return {
                    'configured': True,
                    'mode': 'production',
                    'empresa': data.get('name', 'Unknown'),
                    'rfc': data.get('rfc')
                }
            else:
                return {'configured': True, 'mode': 'error', 'message': f'API error {resp.status_code}'}
        except Exception as e:
            return {'configured': True, 'mode': 'error', 'message': str(e)}

    def _mock_invoice(self, pedido_id, emp_id):
        """Generate a mock invoice for testing."""
        from db import query, execute
        try:
            pedido = query("SELECT * FROM PEDIDOS WHERE PED_ID=? AND EMP_ID=?", [pedido_id, emp_id])
            if not pedido:
                return {'success': False, 'error': 'Pedido no encontrado'}

            p = pedido[0]
            import uuid as uuid_mod
            mock_uuid = str(uuid_mod.uuid4())
            mock_folio = f'FAC-{emp_id}-{pedido_id}'

            execute(
                "INSERT INTO CFDI_FACTURAS (EMP_ID, FAC_PED_ID, FAC_UUID, FAC_FOLIO, FAC_SERIE, "
                "FAC_RECEPTOR_RAZON, FAC_RECEPTOR_RFC, FAC_TOTAL, FAC_ESTATUS, FAC_FECHA_EMISION) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'TIMBRADA', NOW())",
                [emp_id, pedido_id, mock_uuid, mock_folio, 'A',
                 p.get('PED_CLIENTE_NOMBRE', 'Publico General'),
                 p.get('PED_CLIENTE_RFC', 'XAXX010101010'),
                 p.get('PED_COSTO_TOTAL', 0)]
            )

            return {
                'success': True,
                'uuid': mock_uuid,
                'folio': mock_folio,
                'serie': 'A',
                'tipo': 'TIMBRADA',
                'mode': 'mock'
            }
        except Exception as e:
            return {'success': False, 'error': 'Error de facturacion'}

    def _save_cfdi(self, pedido_id, emp_id, data, pedido):
        """Save CFDI to database."""
        from db import execute
        try:
            execute(
                "INSERT INTO CFDI_FACTURAS (EMP_ID, FAC_PED_ID, FAC_UUID, FAC_FOLIO, FAC_SERIE, "
                "FAC_RECEPTOR_RAZON, FAC_RECEPTOR_RFC, FAC_TOTAL, FAC_ESTATUS, FAC_FECHA_EMISION, FAC_XML_TIMBRADO) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'TIMBRADA', NOW(), ?)",
                [emp_id, pedido_id,
                 data.get('uuid'),
                 data.get('folio'),
                 data.get('serie'),
                 pedido.get('PED_CLIENTE_NOMBRE', 'Publico General'),
                 pedido.get('PED_CLIENTE_RFC', 'XAXX010101010'),
                 float(pedido.get('PED_COSTO_TOTAL', 0) or 0),
                 data.get('xml', '')]
            )
        except Exception as e:
            logger.error(f'[CFDI] Save error: {str(e)}')


# Singleton
cfdi_service = CFDIService()
