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
            return {'success': False, 'error': 'Error de notificacion'}


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
            return {'success': False, 'error': 'Error de notificacion'}


# ========================================
# NOTIFICATION TEMPLATES (MULTI-LANGUAGE)
# ========================================

TEMPLATES_I18N = {
    'pedido_creado': {
        'es': {
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
        'en': {
            'email_subject': 'Order #{pedido_id} received',
            'email_html': '''
            <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
                <div style="background:#6366f1;color:white;padding:20px;text-align:center;">
                    <h1 style="margin:0;font-size:20px;">Last Mile Delivery</h1>
                </div>
                <div style="padding:24px;background:#fff;">
                    <h2 style="color:#111827;">Order confirmed</h2>
                    <p>Your order <strong>#{pedido_id}</strong> has been received successfully.</p>
                    <table style="width:100%;border-collapse:collapse;margin:16px 0;">
                        <tr><td style="padding:8px;color:#6b7280;">Destination:</td><td style="padding:8px;font-weight:600;">{destino}</td></tr>
                        <tr><td style="padding:8px;color:#6b7280;">Cost:</td><td style="padding:8px;font-weight:600;">{costo}</td></tr>
                        <tr><td style="padding:8px;color:#6b7280;">Payment method:</td><td style="padding:8px;">{pago}</td></tr>
                    </table>
                    <p style="color:#6b7280;font-size:13px;">You can track your order from your client portal.</p>
                </div>
                <div style="padding:16px;background:#f8f9fc;text-align:center;color:#9ca3af;font-size:11px;">
                    Last Mile Delivery Platform &copy; 2026
                </div>
            </div>
            ''',
            'sms': 'Last Mile: Your order #{pedido_id} was received. Destination: {destino}. Cost: {costo}.'
        },
        'pt': {
            'email_subject': 'Pedido #{pedido_id} recebido',
            'email_html': '''
            <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
                <div style="background:#6366f1;color:white;padding:20px;text-align:center;">
                    <h1 style="margin:0;font-size:20px;">Last Mile Delivery</h1>
                </div>
                <div style="padding:24px;background:#fff;">
                    <h2 style="color:#111827;">Pedido confirmado</h2>
                    <p>Seu pedido <strong>#{pedido_id}</strong> foi recebido com sucesso.</p>
                    <table style="width:100%;border-collapse:collapse;margin:16px 0;">
                        <tr><td style="padding:8px;color:#6b7280;">Destino:</td><td style="padding:8px;font-weight:600;">{destino}</td></tr>
                        <tr><td style="padding:8px;color:#6b7280;">Custo:</td><td style="padding:8px;font-weight:600;">{costo}</td></tr>
                        <tr><td style="padding:8px;color:#6b7280;">Forma de pagamento:</td><td style="padding:8px;">{pago}</td></tr>
                    </table>
                    <p style="color:#6b7280;font-size:13px;">Voce pode acompanhar pelo portal do cliente.</p>
                </div>
                <div style="padding:16px;background:#f8f9fc;text-align:center;color:#9ca3af;font-size:11px;">
                    Last Mile Delivery Platform &copy; 2026
                </div>
            </div>
            ''',
            'sms': 'Last Mile: Seu pedido #{pedido_id} foi recebido. Destino: {destino}. Custo: {costo}.'
        }
    },
    'pedido_asignado_chofer': {
        'es': {
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
        'en': {
            'email_subject': 'Order #{pedido_id} assigned to you',
            'email_html': '''
            <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
                <div style="background:#059669;color:white;padding:20px;text-align:center;">
                    <h1 style="margin:0;font-size:20px;">Last Mile Delivery</h1>
                </div>
                <div style="padding:24px;background:#fff;">
                    <h2 style="color:#111827;">New order assigned</h2>
                    <p>Order <strong>#{pedido_id}</strong> has been assigned to you.</p>
                    <table style="width:100%;border-collapse:collapse;margin:16px 0;">
                        <tr><td style="padding:8px;color:#6b7280;">Client:</td><td style="padding:8px;font-weight:600;">{cliente}</td></tr>
                        <tr><td style="padding:8px;color:#6b7280;">Origin:</td><td style="padding:8px;">{origen}</td></tr>
                        <tr><td style="padding:8px;color:#6b7280;">Destination:</td><td style="padding:8px;font-weight:600;">{destino}</td></tr>
                        <tr><td style="padding:8px;color:#6b7280;">Packages:</td><td style="padding:8px;">{bultos}</td></tr>
                    </table>
                    <a href="{tracking_url}" style="display:inline-block;background:#6366f1;color:white;padding:12px 24px;border-radius:6px;text-decoration:none;font-weight:600;">View details</a>
                </div>
                <div style="padding:16px;background:#f8f9fc;text-align:center;color:#9ca3af;font-size:11px;">
                    Last Mile Delivery Platform &copy; 2026
                </div>
            </div>
            ''',
            'sms': 'Last Mile: Order #{pedido_id} assigned to you. Client: {cliente}. Destination: {destino}. Open the app for details.'
        },
        'pt': {
            'email_subject': 'Pedido #{pedido_id} atribuido a voce',
            'email_html': '''
            <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
                <div style="background:#059669;color:white;padding:20px;text-align:center;">
                    <h1 style="margin:0;font-size:20px;">Last Mile Delivery</h1>
                </div>
                <div style="padding:24px;background:#fff;">
                    <h2 style="color:#111827;">Novo pedido atribuido</h2>
                    <p>O pedido <strong>#{pedido_id}</strong> foi atribuido a voce.</p>
                    <table style="width:100%;border-collapse:collapse;margin:16px 0;">
                        <tr><td style="padding:8px;color:#6b7280;">Cliente:</td><td style="padding:8px;font-weight:600;">{cliente}</td></tr>
                        <tr><td style="padding:8px;color:#6b7280;">Origem:</td><td style="padding:8px;">{origen}</td></tr>
                        <tr><td style="padding:8px;color:#6b7280;">Destino:</td><td style="padding:8px;font-weight:600;">{destino}</td></tr>
                        <tr><td style="padding:8px;color:#6b7280;">Pacotes:</td><td style="padding:8px;">{bultos}</td></tr>
                    </table>
                    <a href="{tracking_url}" style="display:inline-block;background:#6366f1;color:white;padding:12px 24px;border-radius:6px;text-decoration:none;font-weight:600;">Ver detalhes</a>
                </div>
                <div style="padding:16px;background:#f8f9fc;text-align:center;color:#9ca3af;font-size:11px;">
                    Last Mile Delivery Platform &copy; 2026
                </div>
            </div>
            ''',
            'sms': 'Last Mile: Pedido #{pedido_id} atribuido a voce. Cliente: {cliente}. Destino: {destino}. Abra o app para detalhes.'
        }
    },
    'pedido_en_ruta': {
        'es': {
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
        'en': {
            'email_subject': 'Order #{pedido_id} on the way',
            'email_html': '''
            <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
                <div style="background:#2563eb;color:white;padding:20px;text-align:center;">
                    <h1 style="margin:0;font-size:20px;">Last Mile Delivery</h1>
                </div>
                <div style="padding:24px;background:#fff;">
                    <h2 style="color:#111827;">Your order is on the way</h2>
                    <p>Order <strong>#{pedido_id}</strong> is on its delivery route.</p>
                    <table style="width:100%;border-collapse:collapse;margin:16px 0;">
                        <tr><td style="padding:8px;color:#6b7280;">Driver:</td><td style="padding:8px;font-weight:600;">{chofer}</td></tr>
                        <tr><td style="padding:8px;color:#6b7280;">Destination:</td><td style="padding:8px;">{destino}</td></tr>
                    </table>
                    <a href="{tracking_url}" style="display:inline-block;background:#2563eb;color:white;padding:12px 24px;border-radius:6px;text-decoration:none;font-weight:600;">Track order</a>
                </div>
                <div style="padding:16px;background:#f8f9fc;text-align:center;color:#9ca3af;font-size:11px;">
                    Last Mile Delivery Platform &copy; 2026
                </div>
            </div>
            ''',
            'sms': 'Last Mile: Your order #{pedido_id} is on the way. Driver: {chofer}. Track at: {tracking_url}'
        },
        'pt': {
            'email_subject': 'Pedido #{pedido_id} a caminho',
            'email_html': '''
            <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
                <div style="background:#2563eb;color:white;padding:20px;text-align:center;">
                    <h1 style="margin:0;font-size:20px;">Last Mile Delivery</h1>
                </div>
                <div style="padding:24px;background:#fff;">
                    <h2 style="color:#111827;">Seu pedido esta a caminho</h2>
                    <p>O pedido <strong>#{pedido_id}</strong> esta em rota de entrega.</p>
                    <table style="width:100%;border-collapse:collapse;margin:16px 0;">
                        <tr><td style="padding:8px;color:#6b7280;">Motorista:</td><td style="padding:8px;font-weight:600;">{chofer}</td></tr>
                        <tr><td style="padding:8px;color:#6b7280;">Destino:</td><td style="padding:8px;">{destino}</td></tr>
                    </table>
                    <a href="{tracking_url}" style="display:inline-block;background:#2563eb;color:white;padding:12px 24px;border-radius:6px;text-decoration:none;font-weight:600;">Rastrear pedido</a>
                </div>
                <div style="padding:16px;background:#f8f9fc;text-align:center;color:#9ca3af;font-size:11px;">
                    Last Mile Delivery Platform &copy; 2026
                </div>
            </div>
            ''',
            'sms': 'Last Mile: Seu pedido #{pedido_id} esta a caminho. Motorista: {chofer}. Rastreie em: {tracking_url}'
        }
    },
    'pedido_entregado': {
        'es': {
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
        'en': {
            'email_subject': 'Order #{pedido_id} delivered',
            'email_html': '''
            <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
                <div style="background:#059669;color:white;padding:20px;text-align:center;">
                    <h1 style="margin:0;font-size:20px;">Last Mile Delivery</h1>
                </div>
                <div style="padding:24px;background:#fff;">
                    <h2 style="color:#059669;">Delivery completed</h2>
                    <p>Order <strong>#{pedido_id}</strong> has been delivered successfully.</p>
                    <table style="width:100%;border-collapse:collapse;margin:16px 0;">
                        <tr><td style="padding:8px;color:#6b7280;">Delivery date:</td><td style="padding:8px;font-weight:600;">{fecha_entrega}</td></tr>
                        <tr><td style="padding:8px;color:#6b7280;">Destination:</td><td style="padding:8px;">{destino}</td></tr>
                    </table>
                    <p style="color:#6b7280;font-size:13px;">Thank you for choosing Last Mile Delivery.</p>
                </div>
                <div style="padding:16px;background:#f8f9fc;text-align:center;color:#9ca3af;font-size:11px;">
                    Last Mile Delivery Platform &copy; 2026
                </div>
            </div>
            ''',
            'sms': 'Last Mile: Your order #{pedido_id} has been delivered. Thank you for your purchase.'
        },
        'pt': {
            'email_subject': 'Pedido #{pedido_id} entregue',
            'email_html': '''
            <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
                <div style="background:#059669;color:white;padding:20px;text-align:center;">
                    <h1 style="margin:0;font-size:20px;">Last Mile Delivery</h1>
                </div>
                <div style="padding:24px;background:#fff;">
                    <h2 style="color:#059669;">Entrega concluida</h2>
                    <p>O pedido <strong>#{pedido_id}</strong> foi entregue com sucesso.</p>
                    <table style="width:100%;border-collapse:collapse;margin:16px 0;">
                        <tr><td style="padding:8px;color:#6b7280;">Data de entrega:</td><td style="padding:8px;font-weight:600;">{fecha_entrega}</td></tr>
                        <tr><td style="padding:8px;color:#6b7280;">Destino:</td><td style="padding:8px;">{destino}</td></tr>
                    </table>
                    <p style="color:#6b7280;font-size:13px;">Obrigado por escolher o Last Mile Delivery.</p>
                </div>
                <div style="padding:16px;background:#f8f9fc;text-align:center;color:#9ca3af;font-size:11px;">
                    Last Mile Delivery Platform &copy; 2026
                </div>
            </div>
            ''',
            'sms': 'Last Mile: Seu pedido #{pedido_id} foi entregue. Obrigado pela sua compra.'
        }
    },
    'pedido_cancelado': {
        'es': {
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
        'en': {
            'email_subject': 'Order #{pedido_id} cancelled',
            'email_html': '''
            <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
                <div style="background:#dc2626;color:white;padding:20px;text-align:center;">
                    <h1 style="margin:0;font-size:20px;">Last Mile Delivery</h1>
                </div>
                <div style="padding:24px;background:#fff;">
                    <h2 style="color:#dc2626;">Order cancelled</h2>
                    <p>Order <strong>#{pedido_id}</strong> has been cancelled.</p>
                    <p style="color:#6b7280;">Reason: {razon}</p>
                </div>
                <div style="padding:16px;background:#f8f9fc;text-align:center;color:#9ca3af;font-size:11px;">
                    Last Mile Delivery Platform &copy; 2026
                </div>
            </div>
            ''',
            'sms': 'Last Mile: Your order #{pedido_id} has been cancelled. Reason: {razon}'
        },
        'pt': {
            'email_subject': 'Pedido #{pedido_id} cancelado',
            'email_html': '''
            <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
                <div style="background:#dc2626;color:white;padding:20px;text-align:center;">
                    <h1 style="margin:0;font-size:20px;">Last Mile Delivery</h1>
                </div>
                <div style="padding:24px;background:#fff;">
                    <h2 style="color:#dc2626;">Pedido cancelado</h2>
                    <p>O pedido <strong>#{pedido_id}</strong> foi cancelado.</p>
                    <p style="color:#6b7280;">Motivo: {razon}</p>
                </div>
                <div style="padding:16px;background:#f8f9fc;text-align:center;color:#9ca3af;font-size:11px;">
                    Last Mile Delivery Platform &copy; 2026
                </div>
            </div>
            ''',
            'sms': 'Last Mile: Seu pedido #{pedido_id} foi cancelado. Motivo: {razon}'
        }
    },
    'pago_recibido': {
        'es': {
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
        },
        'en': {
            'email_subject': 'Payment of ${monto} received',
            'email_html': '''
            <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
                <div style="background:#059669;color:white;padding:20px;text-align:center;">
                    <h1 style="margin:0;font-size:20px;">Last Mile Delivery</h1>
                </div>
                <div style="padding:24px;background:#fff;">
                    <h2 style="color:#059669;">Payment confirmed</h2>
                    <p>We received your payment of <strong>{monto}</strong>.</p>
                    <table style="width:100%;border-collapse:collapse;margin:16px 0;">
                        <tr><td style="padding:8px;color:#6b7280;">Method:</td><td style="padding:8px;">{metodo}</td></tr>
                        <tr><td style="padding:8px;color:#6b7280;">Reference:</td><td style="padding:8px;">{referencia}</td></tr>
                        <tr><td style="padding:8px;color:#6b7280;">Date:</td><td style="padding:8px;">{fecha}</td></tr>
                    </table>
                </div>
                <div style="padding:16px;background:#f8f9fc;text-align:center;color:#9ca3af;font-size:11px;">
                    Last Mile Delivery Platform &copy; 2026
                </div>
            </div>
            ''',
            'sms': 'Last Mile: Payment of {monto} received via {metodo}. Ref: {referencia}.'
        },
        'pt': {
            'email_subject': 'Pagamento de ${monto} recebido',
            'email_html': '''
            <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
                <div style="background:#059669;color:white;padding:20px;text-align:center;">
                    <h1 style="margin:0;font-size:20px;">Last Mile Delivery</h1>
                </div>
                <div style="padding:24px;background:#fff;">
                    <h2 style="color:#059669;">Pagamento confirmado</h2>
                    <p>Recebemos seu pagamento de <strong>{monto}</strong>.</p>
                    <table style="width:100%;border-collapse:collapse;margin:16px 0;">
                        <tr><td style="padding:8px;color:#6b7280;">Metodo:</td><td style="padding:8px;">{metodo}</td></tr>
                        <tr><td style="padding:8px;color:#6b7280;">Referencia:</td><td style="padding:8px;">{referencia}</td></tr>
                        <tr><td style="padding:8px;color:#6b7280;">Data:</td><td style="padding:8px;">{fecha}</td></tr>
                    </table>
                </div>
                <div style="padding:16px;background:#f8f9fc;text-align:center;color:#9ca3af;font-size:11px;">
                    Last Mile Delivery Platform &copy; 2026
                </div>
            </div>
            ''',
            'sms': 'Last Mile: Pagamento de {monto} recebido via {metodo}. Ref: {referencia}.'
        }
    }
}

# Language detection from country code
COUNTRY_LANG = {
    'MX': 'es', 'CO': 'es', 'AR': 'es', 'CL': 'es', 'PE': 'es', 'UY': 'es',
    'BR': 'pt',
    'EC': 'es',
}

# Legacy templates fallback (Spanish only, for backward compatibility)
TEMPLATES = {}
for tk, langs in TEMPLATES_I18N.items():
    TEMPLATES[tk] = langs['es']


# ========================================
# NOTIFICATION SERVICE
# ========================================

class NotificationService:
    def __init__(self):
        self.email = EmailService()
        self.sms = SMSService()
        try:
            from whatsapp_service import whatsapp_service
            self.whatsapp = whatsapp_service
        except Exception:
            self.whatsapp = None

    def _get_tenant_lang(self, emp_id):
        """Detect language from tenant's fiscal country config."""
        if not emp_id:
            return 'es'
        from db import query
        try:
            rows = query("SELECT TFC_COUNTRY_CODE FROM TENANT_FISCAL_CONFIG WHERE EMP_ID=?", [emp_id])
            if rows:
                country = rows[0].get('TFC_COUNTRY_CODE', 'MX')
                return COUNTRY_LANG.get(country, 'es')
        except Exception:
            pass
        return 'es'

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

    def send(self, template_key, pedido_id, emp_id=None, chofer_id=None, cli_id=None, extra=None, lang=None):
        """Send notification using template. Returns dict with email and sms results."""
        if not lang and emp_id:
            lang = self._get_tenant_lang(emp_id)
        if not lang:
            lang = 'es'
        lang_templates = TEMPLATES_I18N.get(template_key)
        if not lang_templates:
            return {'success': False, 'error': f'Template {template_key} not found'}
        template = lang_templates.get(lang) or lang_templates.get('es')

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

        results = {'email': None, 'sms': None, 'whatsapp': None}

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
                if self.whatsapp and self.whatsapp.enabled:
                    results['whatsapp'] = self.whatsapp.send(contacts['phone'], sms_text)

        if chofer_id and template_key == 'pedido_asignado_chofer':
            contacts = self.get_chofer_contacts(chofer_id)
            if contacts.get('email'):
                subject = template['email_subject'].format(**vars)
                html = template['email_html'].format(**vars)
                results['email'] = self.email.send(contacts['email'], subject, html)
            if contacts.get('phone'):
                sms_text = template['sms'].format(**vars)
                results['sms'] = self.sms.send(contacts['phone'], sms_text)
                if self.whatsapp and self.whatsapp.enabled:
                    results['whatsapp'] = self.whatsapp.send(contacts['phone'], sms_text)

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
            has_any = results.get('email') or results.get('sms') or results.get('whatsapp')
            execute(
                "INSERT INTO NOTIFICACIONES (EMP_ID, NOT_TIPO, NOT_MENSAJE, NOT_ESTADO, PED_ID, NOT_CREATED) "
                "VALUES (?, ?, ?, ?, ?, NOW())",
                [emp_id, template_key,
                 json.dumps({'template': template_key, 'pedido_id': pedido_id, 'results': str(results)}),
                 'ENVIADO' if has_any else 'LOG',
                 pedido_id]
            )
        except Exception:
            pass

    def send_custom(self, to_email=None, to_phone=None, subject=None, html=None, sms_text=None, whatsapp_text=None):
        """Send custom notification."""
        results = {'email': None, 'sms': None, 'whatsapp': None}
        if to_email and subject and html:
            results['email'] = self.email.send(to_email, subject, html)
        if to_phone and sms_text:
            results['sms'] = self.sms.send(to_phone, sms_text)
        if to_phone and (whatsapp_text or sms_text) and self.whatsapp and self.whatsapp.enabled:
            results['whatsapp'] = self.whatsapp.send(to_phone, whatsapp_text or sms_text)
        return results


def send_push_to_chofer(cho_id, emp_id, title, body, data=None):
    """Envia una notificacion push (Expo Push API) a todos los dispositivos
    Expo registrados de un chofer (NOTIF_DISPOSITIVOS, DISP_PLATAFORMA='EXPO').
    No falla el flujo que la llama si el envio no funciona -- es best-effort,
    igual que el resto de las notificaciones de la plataforma."""
    if not cho_id:
        return
    try:
        from db import query
        rows = query(
            "SELECT DISP_TOKEN FROM NOTIF_DISPOSITIVOS WHERE CHO_ID=? AND EMP_ID=? AND DISP_PLATAFORMA='EXPO' AND DISP_ACTIVO='S'",
            [cho_id, emp_id]
        )
        tokens = [r['DISP_TOKEN'] for r in rows if r.get('DISP_TOKEN')]
        if not tokens:
            return
        import requests
        messages = [{'to': t, 'title': title, 'body': body, 'data': data or {}, 'sound': 'default'} for t in tokens]
        requests.post(
            'https://exp.host/--/api/v2/push/send',
            headers={'Content-Type': 'application/json', 'Accept': 'application/json'},
            json=messages,
            timeout=10
        )
    except Exception as e:
        logger.warning(f'[EXPO PUSH] Error enviando a chofer {cho_id}: {str(e)}')


def send_push_to_admins(emp_id, title, body, data=None):
    """Envia una notificacion push a todos los usuarios admin/operacion del
    tenant que tengan un dispositivo Expo registrado (NOTIF_DISPOSITIVOS via
    USR_ID). Usado para avisos operativos como un percance de un chofer que
    necesita reasignacion manual desde el panel. Best-effort, igual que
    send_push_to_chofer."""
    if not emp_id:
        return
    try:
        from db import query
        usuarios = query(
            "SELECT USU_ID FROM USUARIOS WHERE USU_EMP_ID=? AND USU_ROL IN ('admin','operacion') AND USU_ACTIVO='S'",
            [emp_id]
        )
        usu_ids = [u['USU_ID'] for u in usuarios if u.get('USU_ID')]
        if not usu_ids:
            return
        placeholders = ','.join('?' * len(usu_ids))
        rows = query(
            f"SELECT DISP_TOKEN FROM NOTIF_DISPOSITIVOS WHERE USR_ID IN ({placeholders}) AND EMP_ID=? AND DISP_PLATAFORMA='EXPO' AND DISP_ACTIVO='S'",
            usu_ids + [emp_id]
        )
        tokens = [r['DISP_TOKEN'] for r in rows if r.get('DISP_TOKEN')]
        if not tokens:
            return
        import requests
        messages = [{'to': t, 'title': title, 'body': body, 'data': data or {}, 'sound': 'default'} for t in tokens]
        requests.post(
            'https://exp.host/--/api/v2/push/send',
            headers={'Content-Type': 'application/json', 'Accept': 'application/json'},
            json=messages,
            timeout=10
        )
    except Exception as e:
        logger.warning(f'[EXPO PUSH] Error enviando a admins de emp {emp_id}: {str(e)}')


# Singleton
notification_service = NotificationService()
