"""
LAST MILE DELIVERY - Notification Service
Email via Resend + SMS via Twilio. Falls back to console logging.
"""

import os
import json
import logging

logger = logging.getLogger('lastmile.notifications')

# ========================================
# EMAIL SERVICE (Resend)
# ========================================

class EmailService:
    def __init__(self):
        self.api_key = os.environ.get('RESEND_API_KEY', '')
        self.enabled = bool(self.api_key)
        self.from_email = os.environ.get('EMAIL_FROM', 'notificaciones@lastmile.mx')
        self.from_name = os.environ.get('EMAIL_FROM_NAME', 'Last Mile Delivery')
        if self.enabled:
            logger.info('[EMAIL] Resend configured')
        else:
            logger.info('[EMAIL] No RESEND_API_KEY - email disabled')

    def send(self, to, subject, html_body, text_body=None):
        if not self.enabled:
            logger.info(f'[EMAIL] Would send to {to}: {subject}')
            return {'success': True, 'provider': 'console', 'message': 'Email logged (no API key)'}

        try:
            import requests
            resp = requests.post(
                'https://api.resend.com/emails',
                headers={
                    'Authorization': f'Bearer {self.api_key}',
                    'Content-Type': 'application/json'
                },
                json={
                    'from': f'{self.from_name} <{self.from_email}>',
                    'to': [to],
                    'subject': subject,
                    'html': html_body,
                    'text': text_body or html_body
                },
                timeout=15
            )
            if resp.status_code == 200:
                data = resp.json()
                logger.info(f'[EMAIL] Sent to {to}: {data.get("id", "ok")}')
                return {'success': True, 'id': data.get('id')}
            else:
                logger.error(f'[EMAIL] Error {resp.status_code}: {resp.text[:200]}')
                return {'success': False, 'error': resp.text[:200]}
        except Exception as e:
            logger.error(f'[EMAIL] Exception: {str(e)}')
            return {'success': False, 'error': str(e)}


# ========================================
# SMS SERVICE (Twilio)
# ========================================

class SMSService:
    def __init__(self):
        self.account_sid = os.environ.get('TWILIO_ACCOUNT_SID', '')
        self.auth_token = os.environ.get('TWILIO_AUTH_TOKEN', '')
        self.from_number = os.environ.get('TWILIO_PHONE', '')
        self.enabled = bool(self.account_sid and self.auth_token and self.from_number)
        if self.enabled:
            logger.info(f'[SMS] Twilio configured: {self.from_number}')
        else:
            logger.info('[SMS] No Twilio credentials - SMS disabled')

    def send(self, to, message):
        if not self.enabled:
            logger.info(f'[SMS] Would send to {to}: {message[:50]}...')
            return {'success': True, 'provider': 'console', 'message': 'SMS logged (no credentials)'}

        try:
            from twilio.rest import Client
            client = Client(self.account_sid, self.auth_token)
            sms = client.messages.create(
                body=message,
                from_=self.from_number,
                to=to
            )
            logger.info(f'[SMS] Sent to {to}: {sms.sid}')
            return {'success': True, 'sid': sms.sid}
        except Exception as e:
            logger.error(f'[SMS] Exception: {str(e)}')
            return {'success': False, 'error': str(e)}


# ========================================
# NOTIFICATION TEMPLATES
# ========================================

TEMPLATES = {
    'pedido_creado': {
        'email_subject': 'Pedido #{pedido_id} recibido',
        'email_html': '''
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
            <div style="background:#6366f1;color:white;padding:20px;text-align:center;">
                <h1 style="margin:0;font-size:20px;">Last Mile Delivery</h1>
            </div>
            <div style="padding:24px;background:#fff;">
                <h2 style="color:#111827;">Pedido confirmado</h2>
                <p>Tu pedido <strong>#{pedido_id}</strong> ha sido recibido exitosamente.</p>
                <table style="width:100%;border-collapse:collapse;margin:16px 0;">
                    <tr><td style="padding:8px;color:#6b7280;">Destino:</td><td style="padding:8px;font-weight:600;">{destino}</td></tr>
                    <tr><td style="padding:8px;color:#6b7280;">Costo:</td><td style="padding:8px;font-weight:600;">{costo}</td></tr>
                    <tr><td style="padding:8px;color:#6b7280;">Forma de pago:</td><td style="padding:8px;">{pago}</td></tr>
                </table>
                <p style="color:#6b7280;font-size:13px;">Podras dar seguimiento desde tu portal de cliente.</p>
            </div>
            <div style="padding:16px;background:#f8f9fc;text-align:center;color:#9ca3af;font-size:11px;">
                Last Mile Delivery Platform &copy; 2026
            </div>
        </div>
        ''',
        'sms': 'Last Mile: Tu pedido #{pedido_id} fue recibido. Destino: {destino}. Costo: {costo}.'
    },
    'pedido_asignado_chofer': {
        'email_subject': 'Te asignaron el pedido #{pedido_id}',
        'email_html': '''
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
            <div style="background:#059669;color:white;padding:20px;text-align:center;">
                <h1 style="margin:0;font-size:20px;">Last Mile Delivery</h1>
            </div>
            <div style="padding:24px;background:#fff;">
                <h2 style="color:#111827;">Nuevo pedido asignado</h2>
                <p>Se te ha asignado el pedido <strong>#{pedido_id}</strong>.</p>
                <table style="width:100%;border-collapse:collapse;margin:16px 0;">
                    <tr><td style="padding:8px;color:#6b7280;">Cliente:</td><td style="padding:8px;font-weight:600;">{cliente}</td></tr>
                    <tr><td style="padding:8px;color:#6b7280;">Origen:</td><td style="padding:8px;">{origen}</td></tr>
                    <tr><td style="padding:8px;color:#6b7280;">Destino:</td><td style="padding:8px;font-weight:600;">{destino}</td></tr>
                    <tr><td style="padding:8px;color:#6b7280;">Bultos:</td><td style="padding:8px;">{bultos}</td></tr>
                </table>
                <a href="{tracking_url}" style="display:inline-block;background:#6366f1;color:white;padding:12px 24px;border-radius:6px;text-decoration:none;font-weight:600;">Ver detalles</a>
            </div>
            <div style="padding:16px;background:#f8f9fc;text-align:center;color:#9ca3af;font-size:11px;">
                Last Mile Delivery Platform &copy; 2026
            </div>
        </div>
        ''',
        'sms': 'Last Mile: Te asignaron pedido #{pedido_id}. Cliente: {cliente}. Destino: {destino}. Abre la app para ver detalles.'
    },
    'pedido_en_ruta': {
        'email_subject': 'Pedido #{pedido_id} en camino',
        'email_html': '''
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
            <div style="background:#2563eb;color:white;padding:20px;text-align:center;">
                <h1 style="margin:0;font-size:20px;">Last Mile Delivery</h1>
            </div>
            <div style="padding:24px;background:#fff;">
                <h2 style="color:#111827;">Tu pedido va en camino</h2>
                <p>El pedido <strong>#{pedido_id}</strong> esta en ruta de entrega.</p>
                <table style="width:100%;border-collapse:collapse;margin:16px 0;">
                    <tr><td style="padding:8px;color:#6b7280;">Chofer:</td><td style="padding:8px;font-weight:600;">{chofer}</td></tr>
                    <tr><td style="padding:8px;color:#6b7280;">Destino:</td><td style="padding:8px;">{destino}</td></tr>
                </table>
                <a href="{tracking_url}" style="display:inline-block;background:#2563eb;color:white;padding:12px 24px;border-radius:6px;text-decoration:none;font-weight:600;">Rastrear pedido</a>
            </div>
            <div style="padding:16px;background:#f8f9fc;text-align:center;color:#9ca3af;font-size:11px;">
                Last Mile Delivery Platform &copy; 2026
            </div>
        </div>
        ''',
        'sms': 'Last Mile: Tu pedido #{pedido_id} va en camino. Chofer: {chofer}. Rastrea en: {tracking_url}'
    },
    'pedido_entregado': {
        'email_subject': 'Pedido #{pedido_id} entregado',
        'email_html': '''
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
            <div style="background:#059669;color:white;padding:20px;text-align:center;">
                <h1 style="margin:0;font-size:20px;">Last Mile Delivery</h1>
            </div>
            <div style="padding:24px;background:#fff;">
                <h2 style="color:#059669;">Entrega completada</h2>
                <p>El pedido <strong>#{pedido_id}</strong> fue entregado exitosamente.</p>
                <table style="width:100%;border-collapse:collapse;margin:16px 0;">
                    <tr><td style="padding:8px;color:#6b7280;">Fecha entrega:</td><td style="padding:8px;font-weight:600;">{fecha_entrega}</td></tr>
                    <tr><td style="padding:8px;color:#6b7280;">Destino:</td><td style="padding:8px;">{destino}</td></tr>
                </table>
                <p style="color:#6b7280;font-size:13px;">Gracias por confiar en Last Mile Delivery.</p>
            </div>
            <div style="padding:16px;background:#f8f9fc;text-align:center;color:#9ca3af;font-size:11px;">
                Last Mile Delivery Platform &copy; 2026
            </div>
        </div>
        ''',
        'sms': 'Last Mile: Tu pedido #{pedido_id} fue entregado. Gracias por tu compra.'
    },
    'pedido_cancelado': {
        'email_subject': 'Pedido #{pedido_id} cancelado',
        'email_html': '''
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
            <div style="background:#dc2626;color:white;padding:20px;text-align:center;">
                <h1 style="margin:0;font-size:20px;">Last Mile Delivery</h1>
            </div>
            <div style="padding:24px;background:#fff;">
                <h2 style="color:#dc2626;">Pedido cancelado</h2>
                <p>El pedido <strong>#{pedido_id}</strong> ha sido cancelado.</p>
                <p style="color:#6b7280;">Razon: {razon}</p>
            </div>
            <div style="padding:16px;background:#f8f9fc;text-align:center;color:#9ca3af;font-size:11px;">
                Last Mile Delivery Platform &copy; 2026
            </div>
        </div>
        ''',
        'sms': 'Last Mile: Tu pedido #{pedido_id} fue cancelado. Razon: {razon}'
    },
    'pago_recibido': {
        'email_subject': 'Pago de ${monto} recibido',
        'email_html': '''
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
            <div style="background:#059669;color:white;padding:20px;text-align:center;">
                <h1 style="margin:0;font-size:20px;">Last Mile Delivery</h1>
            </div>
            <div style="padding:24px;background:#fff;">
                <h2 style="color:#059669;">Pago confirmado</h2>
                <p>Recibimos tu pago de <strong>{monto}</strong>.</p>
                <table style="width:100%;border-collapse:collapse;margin:16px 0;">
                    <tr><td style="padding:8px;color:#6b7280;">Metodo:</td><td style="padding:8px;">{metodo}</td></tr>
                    <tr><td style="padding:8px;color:#6b7280;">Referencia:</td><td style="padding:8px;">{referencia}</td></tr>
                    <tr><td style="padding:8px;color:#6b7280;">Fecha:</td><td style="padding:8px;">{fecha}</td></tr>
                </table>
            </div>
            <div style="padding:16px;background:#f8f9fc;text-align:center;color:#9ca3af;font-size:11px;">
                Last Mile Delivery Platform &copy; 2026
            </div>
        </div>
        ''',
        'sms': 'Last Mile: Pago de {monto} recibido via {metodo}. Ref: {referencia}.'
    }
}


# ========================================
# NOTIFICATION SERVICE
# ========================================

class NotificationService:
    def __init__(self):
        self.email = EmailService()
        self.sms = SMSService()

    def get_empresa_contacts(self, emp_id):
        """Get email and phone for empresa admin and relevant contacts."""
        from db import query
        contacts = {'emails': [], 'phones': []}
        try:
            # Admin users
            users = query("SELECT USU_EMAIL, USU_TELEFONO, USU_ROL FROM USUARIOS WHERE USU_EMP_ID=? AND USU_ACTIVO='S'", [emp_id])
            for u in (users or []):
                if u.get('USU_EMAIL') and '@' in str(u['USU_EMAIL']):
                    contacts['emails'].append(u['USU_EMAIL'])
                if u.get('USU_TELEFONO') and len(str(u['USU_TELEFONO'])) >= 10:
                    contacts['phones'].append(u['USU_TELEFONO'])
        except Exception:
            pass
        return contacts

    def get_chofer_contacts(self, chofer_id):
        """Get chofer email and phone."""
        from db import query
        try:
            ch = query("SELECT CHO_EMAIL, CHO_TELEFONO FROM CHOFERES WHERE CHO_ID=?", [chofer_id])
            if ch:
                return {
                    'email': ch[0].get('CHO_EMAIL'),
                    'phone': ch[0].get('CHO_TELEFONO')
                }
        except Exception:
            pass
        return {'email': None, 'phone': None}

    def get_cliente_contacts(self, cli_id):
        """Get client email and phone."""
        from db import query
        try:
            cl = query("SELECT CLI_EMAIL, CLI_TELEFONO, CLI_CONTACTO FROM CLIENTES_LM WHERE CLI_ID=?", [cli_id])
            if cl:
                return {
                    'email': cl[0].get('CLI_EMAIL'),
                    'phone': cl[0].get('CLI_TELEFONO'),
                    'name': cl[0].get('CLI_CONTACTO')
                }
        except Exception:
            pass
        return {'email': None, 'phone': None, 'name': None}

    def send(self, template_key, pedido_id, emp_id=None, chofer_id=None, cli_id=None, extra=None):
        """Send notification using template. Returns dict with email and sms results."""
        template = TEMPLATES.get(template_key)
        if not template:
            return {'success': False, 'error': f'Template {template_key} not found'}

        extra = extra or {}
        base_url = os.environ.get('BASE_URL', 'https://lastmile-platform.onrender.com')

        # Get pedido data for template variables
        pedido_data = {}
        if pedido_id:
            from db import query
            try:
                p = query("SELECT * FROM PEDIDOS WHERE PED_ID=?", [pedido_id])
                if p:
                    pedido_data = p[0]
            except Exception:
                pass

        # Build template vars
        vars = {
            'pedido_id': pedido_id,
            'destino': pedido_data.get('PED_DESTINO_DIR', extra.get('destino', 'N/A')),
            'origen': pedido_data.get('PED_ORIGEN_DIR', extra.get('origen', 'N/A')),
            'costo': f"${float(pedido_data.get('PED_COSTO_TOTAL', 0) or 0):,.2f}",
            'pago': pedido_data.get('PED_FORMA_PAGO', 'N/A'),
            'cliente': pedido_data.get('PED_CLIENTE_NOMBRE', extra.get('cliente', 'N/A')),
            'chofer': extra.get('chofer', 'N/A'),
            'bultos': pedido_data.get('PED_BULTOS', 1),
            'fecha_entrega': extra.get('fecha_entrega', 'N/A'),
            'razon': extra.get('razon', 'N/A'),
            'monto': extra.get('monto', 'N/A'),
            'metodo': extra.get('metodo', 'N/A'),
            'referencia': extra.get('referencia', 'N/A'),
            'fecha': extra.get('fecha', 'N/A'),
            'tracking_url': f"{base_url}/tracking?pedido={pedido_id}",
        }

        results = {'email': None, 'sms': None}

        # Get contacts
        if cli_id:
            contacts = self.get_cliente_contacts(cli_id)
            if contacts.get('email'):
                subject = template['email_subject'].format(**vars)
                html = template['email_html'].format(**vars)
                results['email'] = self.email.send(contacts['email'], subject, html)
            if contacts.get('phone'):
                sms_text = template['sms'].format(**vars)
                results['sms'] = self.sms.send(contacts['phone'], sms_text)

        if chofer_id and template_key == 'pedido_asignado_chofer':
            contacts = self.get_chofer_contacts(chofer_id)
            if contacts.get('email'):
                subject = template['email_subject'].format(**vars)
                html = template['email_html'].format(**vars)
                results['email'] = self.email.send(contacts['email'], subject, html)
            if contacts.get('phone'):
                sms_text = template['sms'].format(**vars)
                results['sms'] = self.sms.send(contacts['phone'], sms_text)

        if emp_id and template_key in ('pedido_creado', 'pedido_entregado', 'pedido_cancelado', 'pago_recibido'):
            contacts = self.get_empresa_contacts(emp_id)
            if contacts['emails']:
                subject = template['email_subject'].format(**vars)
                html = template['email_html'].format(**vars)
                for email in contacts['emails'][:3]:
                    results['email'] = self.email.send(email, subject, html)

        # Log to DB
        self._log_notification(template_key, pedido_id, emp_id, results, extra)

        return results

    def _log_notification(self, template_key, pedido_id, emp_id, results, extra):
        """Log notification to database."""
        from db import execute
        try:
            execute(
                "INSERT INTO NOTIFICACIONES (EMP_ID, NOT_TIPO, NOT_MENSAJE, NOT_ESTADO, PED_ID, NOT_CREATED) "
                "VALUES (?, ?, ?, ?, ?, NOW())",
                [emp_id, template_key,
                 json.dumps({'template': template_key, 'pedido_id': pedido_id, 'results': str(results)}),
                 'ENVIADO' if results.get('email') or results.get('sms') else 'LOG',
                 pedido_id]
            )
        except Exception:
            pass

    def send_custom(self, to_email=None, to_phone=None, subject=None, html=None, sms_text=None):
        """Send custom notification."""
        results = {'email': None, 'sms': None}
        if to_email and subject and html:
            results['email'] = self.email.send(to_email, subject, html)
        if to_phone and sms_text:
            results['sms'] = self.sms.send(to_phone, sms_text)
        return results


# Singleton
notification_service = NotificationService()
