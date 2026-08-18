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
        },
        'fr': {
            'email_subject': 'Commande #{pedido_id} reçue',
            'email_html': '''
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
            <div style="background:#6366f1;color:white;padding:20px;text-align:center;">
                <h1 style="margin:0;font-size:20px;">Last Mile Delivery</h1>
            </div>
            <div style="padding:24px;background:#fff;">
                <h2 style="color:#111827;">Commande confirmée</h2>
                <p>Votre commande <strong>#{pedido_id}</strong> a été reçue avec succès.</p>
                <table style="width:100%;border-collapse:collapse;margin:16px 0;">
                    <tr><td style="padding:8px;color:#6b7280;">Destination :</td><td style="padding:8px;font-weight:600;">{destino}</td></tr>
                    <tr><td style="padding:8px;color:#6b7280;">Coût :</td><td style="padding:8px;font-weight:600;">{costo}</td></tr>
                    <tr><td style="padding:8px;color:#6b7280;">Mode de paiement :</td><td style="padding:8px;">{pago}</td></tr>
                </table>
                <p style="color:#6b7280;font-size:13px;">Vous pourrez suivre votre commande depuis votre espace client.</p>
            </div>
            <div style="padding:16px;background:#f8f9fc;text-align:center;color:#9ca3af;font-size:11px;">
                Last Mile Delivery Platform &copy; 2026
            </div>
        </div>
        ''',
            'sms': 'Last Mile : Votre commande #{pedido_id} a été reçue. Destination : {destino}. Coût : {costo}.'
        },
        'de': {
            'email_subject': 'Bestellung #{pedido_id} erhalten',
            'email_html': '''
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
            <div style="background:#6366f1;color:white;padding:20px;text-align:center;">
                <h1 style="margin:0;font-size:20px;">Last Mile Delivery</h1>
            </div>
            <div style="padding:24px;background:#fff;">
                <h2 style="color:#111827;">Bestellung bestätigt</h2>
                <p>Ihre Bestellung <strong>#{pedido_id}</strong> wurde erfolgreich erhalten.</p>
                <table style="width:100%;border-collapse:collapse;margin:16px 0;">
                    <tr><td style="padding:8px;color:#6b7280;">Ziel:</td><td style="padding:8px;font-weight:600;">{destino}</td></tr>
                    <tr><td style="padding:8px;color:#6b7280;">Kosten:</td><td style="padding:8px;font-weight:600;">{costo}</td></tr>
                    <tr><td style="padding:8px;color:#6b7280;">Zahlungsart:</td><td style="padding:8px;">{pago}</td></tr>
                </table>
                <p style="color:#6b7280;font-size:13px;">Sie können den Status über Ihr Kundenportal verfolgen.</p>
            </div>
            <div style="padding:16px;background:#f8f9fc;text-align:center;color:#9ca3af;font-size:11px;">
                Last Mile Delivery Platform &copy; 2026
            </div>
        </div>
        ''',
            'sms': 'Last Mile: Ihre Bestellung #{pedido_id} wurde erhalten. Ziel: {destino}. Kosten: {costo}.'
        },
        'it': {
            'email_subject': 'Ordine #{pedido_id} ricevuto',
            'email_html': '''
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
            <div style="background:#6366f1;color:white;padding:20px;text-align:center;">
                <h1 style="margin:0;font-size:20px;">Last Mile Delivery</h1>
            </div>
            <div style="padding:24px;background:#fff;">
                <h2 style="color:#111827;">Ordine confermato</h2>
                <p>Il tuo ordine <strong>#{pedido_id}</strong> è stato ricevuto con successo.</p>
                <table style="width:100%;border-collapse:collapse;margin:16px 0;">
                    <tr><td style="padding:8px;color:#6b7280;">Destinazione:</td><td style="padding:8px;font-weight:600;">{destino}</td></tr>
                    <tr><td style="padding:8px;color:#6b7280;">Costo:</td><td style="padding:8px;font-weight:600;">{costo}</td></tr>
                    <tr><td style="padding:8px;color:#6b7280;">Metodo di pagamento:</td><td style="padding:8px;">{pago}</td></tr>
                </table>
                <p style="color:#6b7280;font-size:13px;">Potrai seguire lo stato dal tuo portale cliente.</p>
            </div>
            <div style="padding:16px;background:#f8f9fc;text-align:center;color:#9ca3af;font-size:11px;">
                Last Mile Delivery Platform &copy; 2026
            </div>
        </div>
        ''',
            'sms': 'Last Mile: Il tuo ordine #{pedido_id} è stato ricevuto. Destinazione: {destino}. Costo: {costo}.'
        },
        'nl': {
            'email_subject': 'Bestelling #{pedido_id} ontvangen',
            'email_html': '''
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
            <div style="background:#6366f1;color:white;padding:20px;text-align:center;">
                <h1 style="margin:0;font-size:20px;">Last Mile Delivery</h1>
            </div>
            <div style="padding:24px;background:#fff;">
                <h2 style="color:#111827;">Bestelling bevestigd</h2>
                <p>Je bestelling <strong>#{pedido_id}</strong> is succesvol ontvangen.</p>
                <table style="width:100%;border-collapse:collapse;margin:16px 0;">
                    <tr><td style="padding:8px;color:#6b7280;">Bestemming:</td><td style="padding:8px;font-weight:600;">{destino}</td></tr>
                    <tr><td style="padding:8px;color:#6b7280;">Kosten:</td><td style="padding:8px;font-weight:600;">{costo}</td></tr>
                    <tr><td style="padding:8px;color:#6b7280;">Betaalmethode:</td><td style="padding:8px;">{pago}</td></tr>
                </table>
                <p style="color:#6b7280;font-size:13px;">Je kunt de status volgen via je klantenportaal.</p>
            </div>
            <div style="padding:16px;background:#f8f9fc;text-align:center;color:#9ca3af;font-size:11px;">
                Last Mile Delivery Platform &copy; 2026
            </div>
        </div>
        ''',
            'sms': 'Last Mile: Je bestelling #{pedido_id} is ontvangen. Bestemming: {destino}. Kosten: {costo}.'
        },
        'zh': {
            'email_subject': '订单 #{pedido_id} 已收到',
            'email_html': '''
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
            <div style="background:#6366f1;color:white;padding:20px;text-align:center;">
                <h1 style="margin:0;font-size:20px;">Last Mile Delivery</h1>
            </div>
            <div style="padding:24px;background:#fff;">
                <h2 style="color:#111827;">订单已确认</h2>
                <p>您的订单 <strong>#{pedido_id}</strong> 已成功接收。</p>
                <table style="width:100%;border-collapse:collapse;margin:16px 0;">
                    <tr><td style="padding:8px;color:#6b7280;">目的地：</td><td style="padding:8px;font-weight:600;">{destino}</td></tr>
                    <tr><td style="padding:8px;color:#6b7280;">费用：</td><td style="padding:8px;font-weight:600;">{costo}</td></tr>
                    <tr><td style="padding:8px;color:#6b7280;">付款方式：</td><td style="padding:8px;">{pago}</td></tr>
                </table>
                <p style="color:#6b7280;font-size:13px;">您可以在客户门户中查看订单进度。</p>
            </div>
            <div style="padding:16px;background:#f8f9fc;text-align:center;color:#9ca3af;font-size:11px;">
                Last Mile Delivery Platform &copy; 2026
            </div>
        </div>
        ''',
            'sms': 'Last Mile：您的订单 #{pedido_id} 已收到。目的地：{destino}。费用：{costo}。'
        },
        'ja': {
            'email_subject': '注文 #{pedido_id} を受け付けました',
            'email_html': '''
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
            <div style="background:#6366f1;color:white;padding:20px;text-align:center;">
                <h1 style="margin:0;font-size:20px;">Last Mile Delivery</h1>
            </div>
            <div style="padding:24px;background:#fff;">
                <h2 style="color:#111827;">注文確認</h2>
                <p>ご注文 <strong>#{pedido_id}</strong> を正常に受け付けました。</p>
                <table style="width:100%;border-collapse:collapse;margin:16px 0;">
                    <tr><td style="padding:8px;color:#6b7280;">配送先：</td><td style="padding:8px;font-weight:600;">{destino}</td></tr>
                    <tr><td style="padding:8px;color:#6b7280;">料金：</td><td style="padding:8px;font-weight:600;">{costo}</td></tr>
                    <tr><td style="padding:8px;color:#6b7280;">支払方法：</td><td style="padding:8px;">{pago}</td></tr>
                </table>
                <p style="color:#6b7280;font-size:13px;">お客様ポータルから配送状況をご確認いただけます。</p>
            </div>
            <div style="padding:16px;background:#f8f9fc;text-align:center;color:#9ca3af;font-size:11px;">
                Last Mile Delivery Platform &copy; 2026
            </div>
        </div>
        ''',
            'sms': 'Last Mile: ご注文 #{pedido_id} を受け付けました。配送先：{destino}。料金：{costo}。'
        },
        'ko': {
            'email_subject': '주문 #{pedido_id} 접수 완료',
            'email_html': '''
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
            <div style="background:#6366f1;color:white;padding:20px;text-align:center;">
                <h1 style="margin:0;font-size:20px;">Last Mile Delivery</h1>
            </div>
            <div style="padding:24px;background:#fff;">
                <h2 style="color:#111827;">주문이 확인되었습니다</h2>
                <p>고객님의 주문 <strong>#{pedido_id}</strong>이(가) 정상적으로 접수되었습니다.</p>
                <table style="width:100%;border-collapse:collapse;margin:16px 0;">
                    <tr><td style="padding:8px;color:#6b7280;">배송지:</td><td style="padding:8px;font-weight:600;">{destino}</td></tr>
                    <tr><td style="padding:8px;color:#6b7280;">비용:</td><td style="padding:8px;font-weight:600;">{costo}</td></tr>
                    <tr><td style="padding:8px;color:#6b7280;">결제 방법:</td><td style="padding:8px;">{pago}</td></tr>
                </table>
                <p style="color:#6b7280;font-size:13px;">고객 포털에서 진행 상황을 확인하실 수 있습니다.</p>
            </div>
            <div style="padding:16px;background:#f8f9fc;text-align:center;color:#9ca3af;font-size:11px;">
                Last Mile Delivery Platform &copy; 2026
            </div>
        </div>
        ''',
            'sms': 'Last Mile: 주문 #{pedido_id}이(가) 접수되었습니다. 배송지: {destino}. 비용: {costo}.'
        },
        'ar': {
            'email_subject': 'تم استلام الطلب #{pedido_id}',
            'email_html': '''
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
            <div style="background:#6366f1;color:white;padding:20px;text-align:center;">
                <h1 style="margin:0;font-size:20px;">Last Mile Delivery</h1>
            </div>
            <div style="padding:24px;background:#fff;">
                <h2 style="color:#111827;">تم تأكيد الطلب</h2>
                <p>تم استلام طلبك <strong>#{pedido_id}</strong> بنجاح.</p>
                <table style="width:100%;border-collapse:collapse;margin:16px 0;">
                    <tr><td style="padding:8px;color:#6b7280;">الوجهة:</td><td style="padding:8px;font-weight:600;">{destino}</td></tr>
                    <tr><td style="padding:8px;color:#6b7280;">التكلفة:</td><td style="padding:8px;font-weight:600;">{costo}</td></tr>
                    <tr><td style="padding:8px;color:#6b7280;">طريقة الدفع:</td><td style="padding:8px;">{pago}</td></tr>
                </table>
                <p style="color:#6b7280;font-size:13px;">يمكنك متابعة الطلب من بوابة العملاء الخاصة بك.</p>
            </div>
            <div style="padding:16px;background:#f8f9fc;text-align:center;color:#9ca3af;font-size:11px;">
                Last Mile Delivery Platform &copy; 2026
            </div>
        </div>
        ''',
            'sms': 'Last Mile: تم استلام طلبك #{pedido_id}. الوجهة: {destino}. التكلفة: {costo}.'
        },
        'hi': {
            'email_subject': 'ऑर्डर #{pedido_id} प्राप्त हुआ',
            'email_html': '''
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
            <div style="background:#6366f1;color:white;padding:20px;text-align:center;">
                <h1 style="margin:0;font-size:20px;">Last Mile Delivery</h1>
            </div>
            <div style="padding:24px;background:#fff;">
                <h2 style="color:#111827;">ऑर्डर की पुष्टि हो गई</h2>
                <p>आपका ऑर्डर <strong>#{pedido_id}</strong> सफलतापूर्वक प्राप्त हो गया है।</p>
                <table style="width:100%;border-collapse:collapse;margin:16px 0;">
                    <tr><td style="padding:8px;color:#6b7280;">गंतव्य:</td><td style="padding:8px;font-weight:600;">{destino}</td></tr>
                    <tr><td style="padding:8px;color:#6b7280;">लागत:</td><td style="padding:8px;font-weight:600;">{costo}</td></tr>
                    <tr><td style="padding:8px;color:#6b7280;">भुगतान का तरीका:</td><td style="padding:8px;">{pago}</td></tr>
                </table>
                <p style="color:#6b7280;font-size:13px;">आप अपने ग्राहक पोर्टल से इसकी स्थिति देख सकते हैं।</p>
            </div>
            <div style="padding:16px;background:#f8f9fc;text-align:center;color:#9ca3af;font-size:11px;">
                Last Mile Delivery Platform &copy; 2026
            </div>
        </div>
        ''',
            'sms': 'Last Mile: आपका ऑर्डर #{pedido_id} प्राप्त हो गया है। गंतव्य: {destino}. लागत: {costo}.'
        },
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
        },
        'fr': {
            'email_subject': 'La commande #{pedido_id} vous a été assignée',
            'email_html': '''
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
            <div style="background:#059669;color:white;padding:20px;text-align:center;">
                <h1 style="margin:0;font-size:20px;">Last Mile Delivery</h1>
            </div>
            <div style="padding:24px;background:#fff;">
                <h2 style="color:#111827;">Nouvelle commande assignée</h2>
                <p>La commande <strong>#{pedido_id}</strong> vous a été assignée.</p>
                <table style="width:100%;border-collapse:collapse;margin:16px 0;">
                    <tr><td style="padding:8px;color:#6b7280;">Client :</td><td style="padding:8px;font-weight:600;">{cliente}</td></tr>
                    <tr><td style="padding:8px;color:#6b7280;">Origine :</td><td style="padding:8px;">{origen}</td></tr>
                    <tr><td style="padding:8px;color:#6b7280;">Destination :</td><td style="padding:8px;font-weight:600;">{destino}</td></tr>
                    <tr><td style="padding:8px;color:#6b7280;">Colis :</td><td style="padding:8px;">{bultos}</td></tr>
                </table>
                <a href="{tracking_url}" style="display:inline-block;background:#6366f1;color:white;padding:12px 24px;border-radius:6px;text-decoration:none;font-weight:600;">Voir les détails</a>
            </div>
            <div style="padding:16px;background:#f8f9fc;text-align:center;color:#9ca3af;font-size:11px;">
                Last Mile Delivery Platform &copy; 2026
            </div>
        </div>
        ''',
            'sms': 'Last Mile : La commande #{pedido_id} vous a été assignée. Client : {cliente}. Destination : {destino}. Ouvrez l\'application pour voir les détails.'
        },
        'de': {
            'email_subject': 'Ihnen wurde die Bestellung #{pedido_id} zugewiesen',
            'email_html': '''
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
            <div style="background:#059669;color:white;padding:20px;text-align:center;">
                <h1 style="margin:0;font-size:20px;">Last Mile Delivery</h1>
            </div>
            <div style="padding:24px;background:#fff;">
                <h2 style="color:#111827;">Neue Bestellung zugewiesen</h2>
                <p>Ihnen wurde die Bestellung <strong>#{pedido_id}</strong> zugewiesen.</p>
                <table style="width:100%;border-collapse:collapse;margin:16px 0;">
                    <tr><td style="padding:8px;color:#6b7280;">Kunde:</td><td style="padding:8px;font-weight:600;">{cliente}</td></tr>
                    <tr><td style="padding:8px;color:#6b7280;">Ursprung:</td><td style="padding:8px;">{origen}</td></tr>
                    <tr><td style="padding:8px;color:#6b7280;">Ziel:</td><td style="padding:8px;font-weight:600;">{destino}</td></tr>
                    <tr><td style="padding:8px;color:#6b7280;">Pakete:</td><td style="padding:8px;">{bultos}</td></tr>
                </table>
                <a href="{tracking_url}" style="display:inline-block;background:#6366f1;color:white;padding:12px 24px;border-radius:6px;text-decoration:none;font-weight:600;">Details ansehen</a>
            </div>
            <div style="padding:16px;background:#f8f9fc;text-align:center;color:#9ca3af;font-size:11px;">
                Last Mile Delivery Platform &copy; 2026
            </div>
        </div>
        ''',
            'sms': 'Last Mile: Ihnen wurde die Bestellung #{pedido_id} zugewiesen. Kunde: {cliente}. Ziel: {destino}. Öffnen Sie die App für Details.'
        },
        'it': {
            'email_subject': 'Ti è stato assegnato l\'ordine #{pedido_id}',
            'email_html': '''
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
            <div style="background:#059669;color:white;padding:20px;text-align:center;">
                <h1 style="margin:0;font-size:20px;">Last Mile Delivery</h1>
            </div>
            <div style="padding:24px;background:#fff;">
                <h2 style="color:#111827;">Nuovo ordine assegnato</h2>
                <p>Ti è stato assegnato l'ordine <strong>#{pedido_id}</strong>.</p>
                <table style="width:100%;border-collapse:collapse;margin:16px 0;">
                    <tr><td style="padding:8px;color:#6b7280;">Cliente:</td><td style="padding:8px;font-weight:600;">{cliente}</td></tr>
                    <tr><td style="padding:8px;color:#6b7280;">Origine:</td><td style="padding:8px;">{origen}</td></tr>
                    <tr><td style="padding:8px;color:#6b7280;">Destinazione:</td><td style="padding:8px;font-weight:600;">{destino}</td></tr>
                    <tr><td style="padding:8px;color:#6b7280;">Colli:</td><td style="padding:8px;">{bultos}</td></tr>
                </table>
                <a href="{tracking_url}" style="display:inline-block;background:#6366f1;color:white;padding:12px 24px;border-radius:6px;text-decoration:none;font-weight:600;">Vedi dettagli</a>
            </div>
            <div style="padding:16px;background:#f8f9fc;text-align:center;color:#9ca3af;font-size:11px;">
                Last Mile Delivery Platform &copy; 2026
            </div>
        </div>
        ''',
            'sms': 'Last Mile: Ti è stato assegnato l\'ordine #{pedido_id}. Cliente: {cliente}. Destinazione: {destino}. Apri l\'app per i dettagli.'
        },
        'nl': {
            'email_subject': 'Bestelling #{pedido_id} aan jou toegewezen',
            'email_html': '''
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
            <div style="background:#059669;color:white;padding:20px;text-align:center;">
                <h1 style="margin:0;font-size:20px;">Last Mile Delivery</h1>
            </div>
            <div style="padding:24px;background:#fff;">
                <h2 style="color:#111827;">Nieuwe bestelling toegewezen</h2>
                <p>Bestelling <strong>#{pedido_id}</strong> is aan jou toegewezen.</p>
                <table style="width:100%;border-collapse:collapse;margin:16px 0;">
                    <tr><td style="padding:8px;color:#6b7280;">Klant:</td><td style="padding:8px;font-weight:600;">{cliente}</td></tr>
                    <tr><td style="padding:8px;color:#6b7280;">Herkomst:</td><td style="padding:8px;">{origen}</td></tr>
                    <tr><td style="padding:8px;color:#6b7280;">Bestemming:</td><td style="padding:8px;font-weight:600;">{destino}</td></tr>
                    <tr><td style="padding:8px;color:#6b7280;">Pakketten:</td><td style="padding:8px;">{bultos}</td></tr>
                </table>
                <a href="{tracking_url}" style="display:inline-block;background:#6366f1;color:white;padding:12px 24px;border-radius:6px;text-decoration:none;font-weight:600;">Details bekijken</a>
            </div>
            <div style="padding:16px;background:#f8f9fc;text-align:center;color:#9ca3af;font-size:11px;">
                Last Mile Delivery Platform &copy; 2026
            </div>
        </div>
        ''',
            'sms': 'Last Mile: Bestelling #{pedido_id} is aan jou toegewezen. Klant: {cliente}. Bestemming: {destino}. Open de app voor details.'
        },
        'zh': {
            'email_subject': '订单 #{pedido_id} 已分配给您',
            'email_html': '''
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
            <div style="background:#059669;color:white;padding:20px;text-align:center;">
                <h1 style="margin:0;font-size:20px;">Last Mile Delivery</h1>
            </div>
            <div style="padding:24px;background:#fff;">
                <h2 style="color:#111827;">已分配新订单</h2>
                <p>订单 <strong>#{pedido_id}</strong> 已分配给您。</p>
                <table style="width:100%;border-collapse:collapse;margin:16px 0;">
                    <tr><td style="padding:8px;color:#6b7280;">客户：</td><td style="padding:8px;font-weight:600;">{cliente}</td></tr>
                    <tr><td style="padding:8px;color:#6b7280;">起点：</td><td style="padding:8px;">{origen}</td></tr>
                    <tr><td style="padding:8px;color:#6b7280;">目的地：</td><td style="padding:8px;font-weight:600;">{destino}</td></tr>
                    <tr><td style="padding:8px;color:#6b7280;">包裹数：</td><td style="padding:8px;">{bultos}</td></tr>
                </table>
                <a href="{tracking_url}" style="display:inline-block;background:#6366f1;color:white;padding:12px 24px;border-radius:6px;text-decoration:none;font-weight:600;">查看详情</a>
            </div>
            <div style="padding:16px;background:#f8f9fc;text-align:center;color:#9ca3af;font-size:11px;">
                Last Mile Delivery Platform &copy; 2026
            </div>
        </div>
        ''',
            'sms': 'Last Mile：订单 #{pedido_id} 已分配给您。客户：{cliente}。目的地：{destino}。请打开应用查看详情。'
        },
        'ja': {
            'email_subject': '注文 #{pedido_id} が割り当てられました',
            'email_html': '''
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
            <div style="background:#059669;color:white;padding:20px;text-align:center;">
                <h1 style="margin:0;font-size:20px;">Last Mile Delivery</h1>
            </div>
            <div style="padding:24px;background:#fff;">
                <h2 style="color:#111827;">新しい注文が割り当てられました</h2>
                <p>注文 <strong>#{pedido_id}</strong> があなたに割り当てられました。</p>
                <table style="width:100%;border-collapse:collapse;margin:16px 0;">
                    <tr><td style="padding:8px;color:#6b7280;">お客様：</td><td style="padding:8px;font-weight:600;">{cliente}</td></tr>
                    <tr><td style="padding:8px;color:#6b7280;">出発地：</td><td style="padding:8px;">{origen}</td></tr>
                    <tr><td style="padding:8px;color:#6b7280;">配送先：</td><td style="padding:8px;font-weight:600;">{destino}</td></tr>
                    <tr><td style="padding:8px;color:#6b7280;">荷物数：</td><td style="padding:8px;">{bultos}</td></tr>
                </table>
                <a href="{tracking_url}" style="display:inline-block;background:#6366f1;color:white;padding:12px 24px;border-radius:6px;text-decoration:none;font-weight:600;">詳細を見る</a>
            </div>
            <div style="padding:16px;background:#f8f9fc;text-align:center;color:#9ca3af;font-size:11px;">
                Last Mile Delivery Platform &copy; 2026
            </div>
        </div>
        ''',
            'sms': 'Last Mile: 注文 #{pedido_id} が割り当てられました。お客様：{cliente}。配送先：{destino}。詳細はアプリでご確認ください。'
        },
        'ko': {
            'email_subject': '주문 #{pedido_id}이(가) 배정되었습니다',
            'email_html': '''
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
            <div style="background:#059669;color:white;padding:20px;text-align:center;">
                <h1 style="margin:0;font-size:20px;">Last Mile Delivery</h1>
            </div>
            <div style="padding:24px;background:#fff;">
                <h2 style="color:#111827;">새 주문이 배정되었습니다</h2>
                <p>주문 <strong>#{pedido_id}</strong>이(가) 귀하에게 배정되었습니다.</p>
                <table style="width:100%;border-collapse:collapse;margin:16px 0;">
                    <tr><td style="padding:8px;color:#6b7280;">고객:</td><td style="padding:8px;font-weight:600;">{cliente}</td></tr>
                    <tr><td style="padding:8px;color:#6b7280;">출발지:</td><td style="padding:8px;">{origen}</td></tr>
                    <tr><td style="padding:8px;color:#6b7280;">배송지:</td><td style="padding:8px;font-weight:600;">{destino}</td></tr>
                    <tr><td style="padding:8px;color:#6b7280;">화물 개수:</td><td style="padding:8px;">{bultos}</td></tr>
                </table>
                <a href="{tracking_url}" style="display:inline-block;background:#6366f1;color:white;padding:12px 24px;border-radius:6px;text-decoration:none;font-weight:600;">상세 정보 보기</a>
            </div>
            <div style="padding:16px;background:#f8f9fc;text-align:center;color:#9ca3af;font-size:11px;">
                Last Mile Delivery Platform &copy; 2026
            </div>
        </div>
        ''',
            'sms': 'Last Mile: 주문 #{pedido_id}이(가) 배정되었습니다. 고객: {cliente}. 배송지: {destino}. 앱에서 상세 정보를 확인하세요.'
        },
        'ar': {
            'email_subject': 'تم تعيينك للطلب #{pedido_id}',
            'email_html': '''
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
            <div style="background:#059669;color:white;padding:20px;text-align:center;">
                <h1 style="margin:0;font-size:20px;">Last Mile Delivery</h1>
            </div>
            <div style="padding:24px;background:#fff;">
                <h2 style="color:#111827;">تم تعيين طلب جديد</h2>
                <p>تم تعيينك للطلب <strong>#{pedido_id}</strong>.</p>
                <table style="width:100%;border-collapse:collapse;margin:16px 0;">
                    <tr><td style="padding:8px;color:#6b7280;">العميل:</td><td style="padding:8px;font-weight:600;">{cliente}</td></tr>
                    <tr><td style="padding:8px;color:#6b7280;">نقطة الانطلاق:</td><td style="padding:8px;">{origen}</td></tr>
                    <tr><td style="padding:8px;color:#6b7280;">الوجهة:</td><td style="padding:8px;font-weight:600;">{destino}</td></tr>
                    <tr><td style="padding:8px;color:#6b7280;">عدد الطرود:</td><td style="padding:8px;">{bultos}</td></tr>
                </table>
                <a href="{tracking_url}" style="display:inline-block;background:#6366f1;color:white;padding:12px 24px;border-radius:6px;text-decoration:none;font-weight:600;">عرض التفاصيل</a>
            </div>
            <div style="padding:16px;background:#f8f9fc;text-align:center;color:#9ca3af;font-size:11px;">
                Last Mile Delivery Platform &copy; 2026
            </div>
        </div>
        ''',
            'sms': 'Last Mile: تم تعيينك للطلب #{pedido_id}. العميل: {cliente}. الوجهة: {destino}. افتح التطبيق لعرض التفاصيل.'
        },
        'hi': {
            'email_subject': 'आपको ऑर्डर #{pedido_id} सौंपा गया है',
            'email_html': '''
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
            <div style="background:#059669;color:white;padding:20px;text-align:center;">
                <h1 style="margin:0;font-size:20px;">Last Mile Delivery</h1>
            </div>
            <div style="padding:24px;background:#fff;">
                <h2 style="color:#111827;">नया ऑर्डर सौंपा गया</h2>
                <p>आपको ऑर्डर <strong>#{pedido_id}</strong> सौंपा गया है।</p>
                <table style="width:100%;border-collapse:collapse;margin:16px 0;">
                    <tr><td style="padding:8px;color:#6b7280;">ग्राहक:</td><td style="padding:8px;font-weight:600;">{cliente}</td></tr>
                    <tr><td style="padding:8px;color:#6b7280;">प्रस्थान स्थान:</td><td style="padding:8px;">{origen}</td></tr>
                    <tr><td style="padding:8px;color:#6b7280;">गंतव्य:</td><td style="padding:8px;font-weight:600;">{destino}</td></tr>
                    <tr><td style="padding:8px;color:#6b7280;">पैकेज संख्या:</td><td style="padding:8px;">{bultos}</td></tr>
                </table>
                <a href="{tracking_url}" style="display:inline-block;background:#6366f1;color:white;padding:12px 24px;border-radius:6px;text-decoration:none;font-weight:600;">विवरण देखें</a>
            </div>
            <div style="padding:16px;background:#f8f9fc;text-align:center;color:#9ca3af;font-size:11px;">
                Last Mile Delivery Platform &copy; 2026
            </div>
        </div>
        ''',
            'sms': 'Last Mile: आपको ऑर्डर #{pedido_id} सौंपा गया है। ग्राहक: {cliente}. गंतव्य: {destino}. विवरण देखने के लिए ऐप खोलें।'
        },
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
        },
        'fr': {
            'email_subject': 'Commande #{pedido_id} en cours de livraison',
            'email_html': '''
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
            <div style="background:#2563eb;color:white;padding:20px;text-align:center;">
                <h1 style="margin:0;font-size:20px;">Last Mile Delivery</h1>
            </div>
            <div style="padding:24px;background:#fff;">
                <h2 style="color:#111827;">Votre commande est en route</h2>
                <p>La commande <strong>#{pedido_id}</strong> est en cours de livraison.</p>
                <table style="width:100%;border-collapse:collapse;margin:16px 0;">
                    <tr><td style="padding:8px;color:#6b7280;">Chauffeur :</td><td style="padding:8px;font-weight:600;">{chofer}</td></tr>
                    <tr><td style="padding:8px;color:#6b7280;">Destination :</td><td style="padding:8px;">{destino}</td></tr>
                </table>
                <a href="{tracking_url}" style="display:inline-block;background:#2563eb;color:white;padding:12px 24px;border-radius:6px;text-decoration:none;font-weight:600;">Suivre la commande</a>
            </div>
            <div style="padding:16px;background:#f8f9fc;text-align:center;color:#9ca3af;font-size:11px;">
                Last Mile Delivery Platform &copy; 2026
            </div>
        </div>
        ''',
            'sms': 'Last Mile : Votre commande #{pedido_id} est en route. Chauffeur : {chofer}. Suivez-la sur : {tracking_url}'
        },
        'de': {
            'email_subject': 'Bestellung #{pedido_id} unterwegs',
            'email_html': '''
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
            <div style="background:#2563eb;color:white;padding:20px;text-align:center;">
                <h1 style="margin:0;font-size:20px;">Last Mile Delivery</h1>
            </div>
            <div style="padding:24px;background:#fff;">
                <h2 style="color:#111827;">Ihre Bestellung ist unterwegs</h2>
                <p>Die Bestellung <strong>#{pedido_id}</strong> befindet sich auf dem Lieferweg.</p>
                <table style="width:100%;border-collapse:collapse;margin:16px 0;">
                    <tr><td style="padding:8px;color:#6b7280;">Fahrer:</td><td style="padding:8px;font-weight:600;">{chofer}</td></tr>
                    <tr><td style="padding:8px;color:#6b7280;">Ziel:</td><td style="padding:8px;">{destino}</td></tr>
                </table>
                <a href="{tracking_url}" style="display:inline-block;background:#2563eb;color:white;padding:12px 24px;border-radius:6px;text-decoration:none;font-weight:600;">Bestellung verfolgen</a>
            </div>
            <div style="padding:16px;background:#f8f9fc;text-align:center;color:#9ca3af;font-size:11px;">
                Last Mile Delivery Platform &copy; 2026
            </div>
        </div>
        ''',
            'sms': 'Last Mile: Ihre Bestellung #{pedido_id} ist unterwegs. Fahrer: {chofer}. Verfolgen Sie sie unter: {tracking_url}'
        },
        'it': {
            'email_subject': 'Ordine #{pedido_id} in consegna',
            'email_html': '''
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
            <div style="background:#2563eb;color:white;padding:20px;text-align:center;">
                <h1 style="margin:0;font-size:20px;">Last Mile Delivery</h1>
            </div>
            <div style="padding:24px;background:#fff;">
                <h2 style="color:#111827;">Il tuo ordine è in viaggio</h2>
                <p>L'ordine <strong>#{pedido_id}</strong> è in consegna.</p>
                <table style="width:100%;border-collapse:collapse;margin:16px 0;">
                    <tr><td style="padding:8px;color:#6b7280;">Autista:</td><td style="padding:8px;font-weight:600;">{chofer}</td></tr>
                    <tr><td style="padding:8px;color:#6b7280;">Destinazione:</td><td style="padding:8px;">{destino}</td></tr>
                </table>
                <a href="{tracking_url}" style="display:inline-block;background:#2563eb;color:white;padding:12px 24px;border-radius:6px;text-decoration:none;font-weight:600;">Traccia ordine</a>
            </div>
            <div style="padding:16px;background:#f8f9fc;text-align:center;color:#9ca3af;font-size:11px;">
                Last Mile Delivery Platform &copy; 2026
            </div>
        </div>
        ''',
            'sms': 'Last Mile: Il tuo ordine #{pedido_id} è in viaggio. Autista: {chofer}. Traccialo su: {tracking_url}'
        },
        'nl': {
            'email_subject': 'Bestelling #{pedido_id} onderweg',
            'email_html': '''
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
            <div style="background:#2563eb;color:white;padding:20px;text-align:center;">
                <h1 style="margin:0;font-size:20px;">Last Mile Delivery</h1>
            </div>
            <div style="padding:24px;background:#fff;">
                <h2 style="color:#111827;">Je bestelling is onderweg</h2>
                <p>Bestelling <strong>#{pedido_id}</strong> is onderweg voor bezorging.</p>
                <table style="width:100%;border-collapse:collapse;margin:16px 0;">
                    <tr><td style="padding:8px;color:#6b7280;">Chauffeur:</td><td style="padding:8px;font-weight:600;">{chofer}</td></tr>
                    <tr><td style="padding:8px;color:#6b7280;">Bestemming:</td><td style="padding:8px;">{destino}</td></tr>
                </table>
                <a href="{tracking_url}" style="display:inline-block;background:#2563eb;color:white;padding:12px 24px;border-radius:6px;text-decoration:none;font-weight:600;">Bestelling volgen</a>
            </div>
            <div style="padding:16px;background:#f8f9fc;text-align:center;color:#9ca3af;font-size:11px;">
                Last Mile Delivery Platform &copy; 2026
            </div>
        </div>
        ''',
            'sms': 'Last Mile: Je bestelling #{pedido_id} is onderweg. Chauffeur: {chofer}. Volg via: {tracking_url}'
        },
        'zh': {
            'email_subject': '订单 #{pedido_id} 正在配送',
            'email_html': '''
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
            <div style="background:#2563eb;color:white;padding:20px;text-align:center;">
                <h1 style="margin:0;font-size:20px;">Last Mile Delivery</h1>
            </div>
            <div style="padding:24px;background:#fff;">
                <h2 style="color:#111827;">您的订单正在配送中</h2>
                <p>订单 <strong>#{pedido_id}</strong> 正在配送途中。</p>
                <table style="width:100%;border-collapse:collapse;margin:16px 0;">
                    <tr><td style="padding:8px;color:#6b7280;">司机：</td><td style="padding:8px;font-weight:600;">{chofer}</td></tr>
                    <tr><td style="padding:8px;color:#6b7280;">目的地：</td><td style="padding:8px;">{destino}</td></tr>
                </table>
                <a href="{tracking_url}" style="display:inline-block;background:#2563eb;color:white;padding:12px 24px;border-radius:6px;text-decoration:none;font-weight:600;">追踪订单</a>
            </div>
            <div style="padding:16px;background:#f8f9fc;text-align:center;color:#9ca3af;font-size:11px;">
                Last Mile Delivery Platform &copy; 2026
            </div>
        </div>
        ''',
            'sms': 'Last Mile：您的订单 #{pedido_id} 正在配送中。司机：{chofer}。追踪链接：{tracking_url}'
        },
        'ja': {
            'email_subject': '注文 #{pedido_id} は配送中です',
            'email_html': '''
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
            <div style="background:#2563eb;color:white;padding:20px;text-align:center;">
                <h1 style="margin:0;font-size:20px;">Last Mile Delivery</h1>
            </div>
            <div style="padding:24px;background:#fff;">
                <h2 style="color:#111827;">ご注文の商品が配送中です</h2>
                <p>注文 <strong>#{pedido_id}</strong> は配送ルート上にあります。</p>
                <table style="width:100%;border-collapse:collapse;margin:16px 0;">
                    <tr><td style="padding:8px;color:#6b7280;">ドライバー：</td><td style="padding:8px;font-weight:600;">{chofer}</td></tr>
                    <tr><td style="padding:8px;color:#6b7280;">配送先：</td><td style="padding:8px;">{destino}</td></tr>
                </table>
                <a href="{tracking_url}" style="display:inline-block;background:#2563eb;color:white;padding:12px 24px;border-radius:6px;text-decoration:none;font-weight:600;">注文を追跡</a>
            </div>
            <div style="padding:16px;background:#f8f9fc;text-align:center;color:#9ca3af;font-size:11px;">
                Last Mile Delivery Platform &copy; 2026
            </div>
        </div>
        ''',
            'sms': 'Last Mile: ご注文 #{pedido_id} は配送中です。ドライバー：{chofer}。追跡はこちら：{tracking_url}'
        },
        'ko': {
            'email_subject': '주문 #{pedido_id} 배송 중',
            'email_html': '''
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
            <div style="background:#2563eb;color:white;padding:20px;text-align:center;">
                <h1 style="margin:0;font-size:20px;">Last Mile Delivery</h1>
            </div>
            <div style="padding:24px;background:#fff;">
                <h2 style="color:#111827;">주문이 배송 중입니다</h2>
                <p>주문 <strong>#{pedido_id}</strong>이(가) 배송 경로에 있습니다.</p>
                <table style="width:100%;border-collapse:collapse;margin:16px 0;">
                    <tr><td style="padding:8px;color:#6b7280;">기사:</td><td style="padding:8px;font-weight:600;">{chofer}</td></tr>
                    <tr><td style="padding:8px;color:#6b7280;">배송지:</td><td style="padding:8px;">{destino}</td></tr>
                </table>
                <a href="{tracking_url}" style="display:inline-block;background:#2563eb;color:white;padding:12px 24px;border-radius:6px;text-decoration:none;font-weight:600;">주문 추적</a>
            </div>
            <div style="padding:16px;background:#f8f9fc;text-align:center;color:#9ca3af;font-size:11px;">
                Last Mile Delivery Platform &copy; 2026
            </div>
        </div>
        ''',
            'sms': 'Last Mile: 주문 #{pedido_id}이(가) 배송 중입니다. 기사: {chofer}. 추적: {tracking_url}'
        },
        'ar': {
            'email_subject': 'الطلب #{pedido_id} في الطريق',
            'email_html': '''
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
            <div style="background:#2563eb;color:white;padding:20px;text-align:center;">
                <h1 style="margin:0;font-size:20px;">Last Mile Delivery</h1>
            </div>
            <div style="padding:24px;background:#fff;">
                <h2 style="color:#111827;">طلبك في الطريق</h2>
                <p>الطلب <strong>#{pedido_id}</strong> في طريقه للتسليم.</p>
                <table style="width:100%;border-collapse:collapse;margin:16px 0;">
                    <tr><td style="padding:8px;color:#6b7280;">السائق:</td><td style="padding:8px;font-weight:600;">{chofer}</td></tr>
                    <tr><td style="padding:8px;color:#6b7280;">الوجهة:</td><td style="padding:8px;">{destino}</td></tr>
                </table>
                <a href="{tracking_url}" style="display:inline-block;background:#2563eb;color:white;padding:12px 24px;border-radius:6px;text-decoration:none;font-weight:600;">تتبع الطلب</a>
            </div>
            <div style="padding:16px;background:#f8f9fc;text-align:center;color:#9ca3af;font-size:11px;">
                Last Mile Delivery Platform &copy; 2026
            </div>
        </div>
        ''',
            'sms': 'Last Mile: طلبك #{pedido_id} في الطريق. السائق: {chofer}. تتبع عبر: {tracking_url}'
        },
        'hi': {
            'email_subject': 'ऑर्डर #{pedido_id} रास्ते में है',
            'email_html': '''
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
            <div style="background:#2563eb;color:white;padding:20px;text-align:center;">
                <h1 style="margin:0;font-size:20px;">Last Mile Delivery</h1>
            </div>
            <div style="padding:24px;background:#fff;">
                <h2 style="color:#111827;">आपका ऑर्डर रास्ते में है</h2>
                <p>ऑर्डर <strong>#{pedido_id}</strong> डिलीवरी मार्ग पर है।</p>
                <table style="width:100%;border-collapse:collapse;margin:16px 0;">
                    <tr><td style="padding:8px;color:#6b7280;">ड्राइवर:</td><td style="padding:8px;font-weight:600;">{chofer}</td></tr>
                    <tr><td style="padding:8px;color:#6b7280;">गंतव्य:</td><td style="padding:8px;">{destino}</td></tr>
                </table>
                <a href="{tracking_url}" style="display:inline-block;background:#2563eb;color:white;padding:12px 24px;border-radius:6px;text-decoration:none;font-weight:600;">ऑर्डर ट्रैक करें</a>
            </div>
            <div style="padding:16px;background:#f8f9fc;text-align:center;color:#9ca3af;font-size:11px;">
                Last Mile Delivery Platform &copy; 2026
            </div>
        </div>
        ''',
            'sms': 'Last Mile: आपका ऑर्डर #{pedido_id} रास्ते में है। ड्राइवर: {chofer}. ट्रैक करें: {tracking_url}'
        },
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
        },
        'fr': {
            'email_subject': 'Commande #{pedido_id} livrée',
            'email_html': '''
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
            <div style="background:#059669;color:white;padding:20px;text-align:center;">
                <h1 style="margin:0;font-size:20px;">Last Mile Delivery</h1>
            </div>
            <div style="padding:24px;background:#fff;">
                <h2 style="color:#059669;">Livraison terminée</h2>
                <p>La commande <strong>#{pedido_id}</strong> a été livrée avec succès.</p>
                <table style="width:100%;border-collapse:collapse;margin:16px 0;">
                    <tr><td style="padding:8px;color:#6b7280;">Date de livraison :</td><td style="padding:8px;font-weight:600;">{fecha_entrega}</td></tr>
                    <tr><td style="padding:8px;color:#6b7280;">Destination :</td><td style="padding:8px;">{destino}</td></tr>
                </table>
                <p style="color:#6b7280;font-size:13px;">Merci de faire confiance à Last Mile Delivery.</p>
            </div>
            <div style="padding:16px;background:#f8f9fc;text-align:center;color:#9ca3af;font-size:11px;">
                Last Mile Delivery Platform &copy; 2026
            </div>
        </div>
        ''',
            'sms': 'Last Mile : Votre commande #{pedido_id} a été livrée. Merci pour votre achat.'
        },
        'de': {
            'email_subject': 'Bestellung #{pedido_id} geliefert',
            'email_html': '''
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
            <div style="background:#059669;color:white;padding:20px;text-align:center;">
                <h1 style="margin:0;font-size:20px;">Last Mile Delivery</h1>
            </div>
            <div style="padding:24px;background:#fff;">
                <h2 style="color:#059669;">Lieferung abgeschlossen</h2>
                <p>Die Bestellung <strong>#{pedido_id}</strong> wurde erfolgreich geliefert.</p>
                <table style="width:100%;border-collapse:collapse;margin:16px 0;">
                    <tr><td style="padding:8px;color:#6b7280;">Lieferdatum:</td><td style="padding:8px;font-weight:600;">{fecha_entrega}</td></tr>
                    <tr><td style="padding:8px;color:#6b7280;">Ziel:</td><td style="padding:8px;">{destino}</td></tr>
                </table>
                <p style="color:#6b7280;font-size:13px;">Vielen Dank für Ihr Vertrauen in Last Mile Delivery.</p>
            </div>
            <div style="padding:16px;background:#f8f9fc;text-align:center;color:#9ca3af;font-size:11px;">
                Last Mile Delivery Platform &copy; 2026
            </div>
        </div>
        ''',
            'sms': 'Last Mile: Ihre Bestellung #{pedido_id} wurde geliefert. Vielen Dank für Ihren Einkauf.'
        },
        'it': {
            'email_subject': 'Ordine #{pedido_id} consegnato',
            'email_html': '''
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
            <div style="background:#059669;color:white;padding:20px;text-align:center;">
                <h1 style="margin:0;font-size:20px;">Last Mile Delivery</h1>
            </div>
            <div style="padding:24px;background:#fff;">
                <h2 style="color:#059669;">Consegna completata</h2>
                <p>L'ordine <strong>#{pedido_id}</strong> è stato consegnato con successo.</p>
                <table style="width:100%;border-collapse:collapse;margin:16px 0;">
                    <tr><td style="padding:8px;color:#6b7280;">Data di consegna:</td><td style="padding:8px;font-weight:600;">{fecha_entrega}</td></tr>
                    <tr><td style="padding:8px;color:#6b7280;">Destinazione:</td><td style="padding:8px;">{destino}</td></tr>
                </table>
                <p style="color:#6b7280;font-size:13px;">Grazie per aver scelto Last Mile Delivery.</p>
            </div>
            <div style="padding:16px;background:#f8f9fc;text-align:center;color:#9ca3af;font-size:11px;">
                Last Mile Delivery Platform &copy; 2026
            </div>
        </div>
        ''',
            'sms': 'Last Mile: Il tuo ordine #{pedido_id} è stato consegnato. Grazie per il tuo acquisto.'
        },
        'nl': {
            'email_subject': 'Bestelling #{pedido_id} bezorgd',
            'email_html': '''
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
            <div style="background:#059669;color:white;padding:20px;text-align:center;">
                <h1 style="margin:0;font-size:20px;">Last Mile Delivery</h1>
            </div>
            <div style="padding:24px;background:#fff;">
                <h2 style="color:#059669;">Bezorging voltooid</h2>
                <p>Bestelling <strong>#{pedido_id}</strong> is succesvol bezorgd.</p>
                <table style="width:100%;border-collapse:collapse;margin:16px 0;">
                    <tr><td style="padding:8px;color:#6b7280;">Bezorgdatum:</td><td style="padding:8px;font-weight:600;">{fecha_entrega}</td></tr>
                    <tr><td style="padding:8px;color:#6b7280;">Bestemming:</td><td style="padding:8px;">{destino}</td></tr>
                </table>
                <p style="color:#6b7280;font-size:13px;">Bedankt voor je vertrouwen in Last Mile Delivery.</p>
            </div>
            <div style="padding:16px;background:#f8f9fc;text-align:center;color:#9ca3af;font-size:11px;">
                Last Mile Delivery Platform &copy; 2026
            </div>
        </div>
        ''',
            'sms': 'Last Mile: Je bestelling #{pedido_id} is bezorgd. Bedankt voor je aankoop.'
        },
        'zh': {
            'email_subject': '订单 #{pedido_id} 已送达',
            'email_html': '''
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
            <div style="background:#059669;color:white;padding:20px;text-align:center;">
                <h1 style="margin:0;font-size:20px;">Last Mile Delivery</h1>
            </div>
            <div style="padding:24px;background:#fff;">
                <h2 style="color:#059669;">配送完成</h2>
                <p>订单 <strong>#{pedido_id}</strong> 已成功送达。</p>
                <table style="width:100%;border-collapse:collapse;margin:16px 0;">
                    <tr><td style="padding:8px;color:#6b7280;">送达日期：</td><td style="padding:8px;font-weight:600;">{fecha_entrega}</td></tr>
                    <tr><td style="padding:8px;color:#6b7280;">目的地：</td><td style="padding:8px;">{destino}</td></tr>
                </table>
                <p style="color:#6b7280;font-size:13px;">感谢您对 Last Mile Delivery 的信任。</p>
            </div>
            <div style="padding:16px;background:#f8f9fc;text-align:center;color:#9ca3af;font-size:11px;">
                Last Mile Delivery Platform &copy; 2026
            </div>
        </div>
        ''',
            'sms': 'Last Mile：您的订单 #{pedido_id} 已送达。感谢您的惠顾。'
        },
        'ja': {
            'email_subject': '注文 #{pedido_id} をお届けしました',
            'email_html': '''
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
            <div style="background:#059669;color:white;padding:20px;text-align:center;">
                <h1 style="margin:0;font-size:20px;">Last Mile Delivery</h1>
            </div>
            <div style="padding:24px;background:#fff;">
                <h2 style="color:#059669;">配送完了</h2>
                <p>注文 <strong>#{pedido_id}</strong> は正常にお届けが完了しました。</p>
                <table style="width:100%;border-collapse:collapse;margin:16px 0;">
                    <tr><td style="padding:8px;color:#6b7280;">配達日：</td><td style="padding:8px;font-weight:600;">{fecha_entrega}</td></tr>
                    <tr><td style="padding:8px;color:#6b7280;">配送先：</td><td style="padding:8px;">{destino}</td></tr>
                </table>
                <p style="color:#6b7280;font-size:13px;">Last Mile Delivery をご利用いただきありがとうございます。</p>
            </div>
            <div style="padding:16px;background:#f8f9fc;text-align:center;color:#9ca3af;font-size:11px;">
                Last Mile Delivery Platform &copy; 2026
            </div>
        </div>
        ''',
            'sms': 'Last Mile: ご注文 #{pedido_id} をお届けしました。ご利用ありがとうございました。'
        },
        'ko': {
            'email_subject': '주문 #{pedido_id} 배송 완료',
            'email_html': '''
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
            <div style="background:#059669;color:white;padding:20px;text-align:center;">
                <h1 style="margin:0;font-size:20px;">Last Mile Delivery</h1>
            </div>
            <div style="padding:24px;background:#fff;">
                <h2 style="color:#059669;">배송 완료</h2>
                <p>주문 <strong>#{pedido_id}</strong>이(가) 성공적으로 배송되었습니다.</p>
                <table style="width:100%;border-collapse:collapse;margin:16px 0;">
                    <tr><td style="padding:8px;color:#6b7280;">배송 일자:</td><td style="padding:8px;font-weight:600;">{fecha_entrega}</td></tr>
                    <tr><td style="padding:8px;color:#6b7280;">배송지:</td><td style="padding:8px;">{destino}</td></tr>
                </table>
                <p style="color:#6b7280;font-size:13px;">Last Mile Delivery를 이용해 주셔서 감사합니다.</p>
            </div>
            <div style="padding:16px;background:#f8f9fc;text-align:center;color:#9ca3af;font-size:11px;">
                Last Mile Delivery Platform &copy; 2026
            </div>
        </div>
        ''',
            'sms': 'Last Mile: 주문 #{pedido_id}이(가) 배송되었습니다. 이용해 주셔서 감사합니다.'
        },
        'ar': {
            'email_subject': 'تم تسليم الطلب #{pedido_id}',
            'email_html': '''
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
            <div style="background:#059669;color:white;padding:20px;text-align:center;">
                <h1 style="margin:0;font-size:20px;">Last Mile Delivery</h1>
            </div>
            <div style="padding:24px;background:#fff;">
                <h2 style="color:#059669;">اكتمل التسليم</h2>
                <p>تم تسليم الطلب <strong>#{pedido_id}</strong> بنجاح.</p>
                <table style="width:100%;border-collapse:collapse;margin:16px 0;">
                    <tr><td style="padding:8px;color:#6b7280;">تاريخ التسليم:</td><td style="padding:8px;font-weight:600;">{fecha_entrega}</td></tr>
                    <tr><td style="padding:8px;color:#6b7280;">الوجهة:</td><td style="padding:8px;">{destino}</td></tr>
                </table>
                <p style="color:#6b7280;font-size:13px;">شكراً لثقتك في Last Mile Delivery.</p>
            </div>
            <div style="padding:16px;background:#f8f9fc;text-align:center;color:#9ca3af;font-size:11px;">
                Last Mile Delivery Platform &copy; 2026
            </div>
        </div>
        ''',
            'sms': 'Last Mile: تم تسليم طلبك #{pedido_id}. شكراً لتسوقك معنا.'
        },
        'hi': {
            'email_subject': 'ऑर्डर #{pedido_id} डिलीवर हो गया',
            'email_html': '''
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
            <div style="background:#059669;color:white;padding:20px;text-align:center;">
                <h1 style="margin:0;font-size:20px;">Last Mile Delivery</h1>
            </div>
            <div style="padding:24px;background:#fff;">
                <h2 style="color:#059669;">डिलीवरी पूरी हुई</h2>
                <p>ऑर्डर <strong>#{pedido_id}</strong> सफलतापूर्वक डिलीवर कर दिया गया है।</p>
                <table style="width:100%;border-collapse:collapse;margin:16px 0;">
                    <tr><td style="padding:8px;color:#6b7280;">डिलीवरी की तारीख:</td><td style="padding:8px;font-weight:600;">{fecha_entrega}</td></tr>
                    <tr><td style="padding:8px;color:#6b7280;">गंतव्य:</td><td style="padding:8px;">{destino}</td></tr>
                </table>
                <p style="color:#6b7280;font-size:13px;">Last Mile Delivery पर भरोसा करने के लिए धन्यवाद।</p>
            </div>
            <div style="padding:16px;background:#f8f9fc;text-align:center;color:#9ca3af;font-size:11px;">
                Last Mile Delivery Platform &copy; 2026
            </div>
        </div>
        ''',
            'sms': 'Last Mile: आपका ऑर्डर #{pedido_id} डिलीवर हो गया है। आपकी खरीदारी के लिए धन्यवाद।'
        },
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
        },
        'fr': {
            'email_subject': 'Commande #{pedido_id} annulée',
            'email_html': '''
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
            <div style="background:#dc2626;color:white;padding:20px;text-align:center;">
                <h1 style="margin:0;font-size:20px;">Last Mile Delivery</h1>
            </div>
            <div style="padding:24px;background:#fff;">
                <h2 style="color:#dc2626;">Commande annulée</h2>
                <p>La commande <strong>#{pedido_id}</strong> a été annulée.</p>
                <p style="color:#6b7280;">Motif : {razon}</p>
            </div>
            <div style="padding:16px;background:#f8f9fc;text-align:center;color:#9ca3af;font-size:11px;">
                Last Mile Delivery Platform &copy; 2026
            </div>
        </div>
        ''',
            'sms': 'Last Mile : Votre commande #{pedido_id} a été annulée. Motif : {razon}'
        },
        'de': {
            'email_subject': 'Bestellung #{pedido_id} storniert',
            'email_html': '''
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
            <div style="background:#dc2626;color:white;padding:20px;text-align:center;">
                <h1 style="margin:0;font-size:20px;">Last Mile Delivery</h1>
            </div>
            <div style="padding:24px;background:#fff;">
                <h2 style="color:#dc2626;">Bestellung storniert</h2>
                <p>Die Bestellung <strong>#{pedido_id}</strong> wurde storniert.</p>
                <p style="color:#6b7280;">Grund: {razon}</p>
            </div>
            <div style="padding:16px;background:#f8f9fc;text-align:center;color:#9ca3af;font-size:11px;">
                Last Mile Delivery Platform &copy; 2026
            </div>
        </div>
        ''',
            'sms': 'Last Mile: Ihre Bestellung #{pedido_id} wurde storniert. Grund: {razon}'
        },
        'it': {
            'email_subject': 'Ordine #{pedido_id} annullato',
            'email_html': '''
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
            <div style="background:#dc2626;color:white;padding:20px;text-align:center;">
                <h1 style="margin:0;font-size:20px;">Last Mile Delivery</h1>
            </div>
            <div style="padding:24px;background:#fff;">
                <h2 style="color:#dc2626;">Ordine annullato</h2>
                <p>L'ordine <strong>#{pedido_id}</strong> è stato annullato.</p>
                <p style="color:#6b7280;">Motivo: {razon}</p>
            </div>
            <div style="padding:16px;background:#f8f9fc;text-align:center;color:#9ca3af;font-size:11px;">
                Last Mile Delivery Platform &copy; 2026
            </div>
        </div>
        ''',
            'sms': 'Last Mile: Il tuo ordine #{pedido_id} è stato annullato. Motivo: {razon}'
        },
        'nl': {
            'email_subject': 'Bestelling #{pedido_id} geannuleerd',
            'email_html': '''
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
            <div style="background:#dc2626;color:white;padding:20px;text-align:center;">
                <h1 style="margin:0;font-size:20px;">Last Mile Delivery</h1>
            </div>
            <div style="padding:24px;background:#fff;">
                <h2 style="color:#dc2626;">Bestelling geannuleerd</h2>
                <p>Bestelling <strong>#{pedido_id}</strong> is geannuleerd.</p>
                <p style="color:#6b7280;">Reden: {razon}</p>
            </div>
            <div style="padding:16px;background:#f8f9fc;text-align:center;color:#9ca3af;font-size:11px;">
                Last Mile Delivery Platform &copy; 2026
            </div>
        </div>
        ''',
            'sms': 'Last Mile: Je bestelling #{pedido_id} is geannuleerd. Reden: {razon}'
        },
        'zh': {
            'email_subject': '订单 #{pedido_id} 已取消',
            'email_html': '''
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
            <div style="background:#dc2626;color:white;padding:20px;text-align:center;">
                <h1 style="margin:0;font-size:20px;">Last Mile Delivery</h1>
            </div>
            <div style="padding:24px;background:#fff;">
                <h2 style="color:#dc2626;">订单已取消</h2>
                <p>订单 <strong>#{pedido_id}</strong> 已被取消。</p>
                <p style="color:#6b7280;">原因：{razon}</p>
            </div>
            <div style="padding:16px;background:#f8f9fc;text-align:center;color:#9ca3af;font-size:11px;">
                Last Mile Delivery Platform &copy; 2026
            </div>
        </div>
        ''',
            'sms': 'Last Mile：您的订单 #{pedido_id} 已取消。原因：{razon}'
        },
        'ja': {
            'email_subject': '注文 #{pedido_id} はキャンセルされました',
            'email_html': '''
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
            <div style="background:#dc2626;color:white;padding:20px;text-align:center;">
                <h1 style="margin:0;font-size:20px;">Last Mile Delivery</h1>
            </div>
            <div style="padding:24px;background:#fff;">
                <h2 style="color:#dc2626;">注文がキャンセルされました</h2>
                <p>注文 <strong>#{pedido_id}</strong> はキャンセルされました。</p>
                <p style="color:#6b7280;">理由：{razon}</p>
            </div>
            <div style="padding:16px;background:#f8f9fc;text-align:center;color:#9ca3af;font-size:11px;">
                Last Mile Delivery Platform &copy; 2026
            </div>
        </div>
        ''',
            'sms': 'Last Mile: ご注文 #{pedido_id} はキャンセルされました。理由：{razon}'
        },
        'ko': {
            'email_subject': '주문 #{pedido_id} 취소됨',
            'email_html': '''
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
            <div style="background:#dc2626;color:white;padding:20px;text-align:center;">
                <h1 style="margin:0;font-size:20px;">Last Mile Delivery</h1>
            </div>
            <div style="padding:24px;background:#fff;">
                <h2 style="color:#dc2626;">주문 취소</h2>
                <p>주문 <strong>#{pedido_id}</strong>이(가) 취소되었습니다.</p>
                <p style="color:#6b7280;">사유: {razon}</p>
            </div>
            <div style="padding:16px;background:#f8f9fc;text-align:center;color:#9ca3af;font-size:11px;">
                Last Mile Delivery Platform &copy; 2026
            </div>
        </div>
        ''',
            'sms': 'Last Mile: 주문 #{pedido_id}이(가) 취소되었습니다. 사유: {razon}'
        },
        'ar': {
            'email_subject': 'تم إلغاء الطلب #{pedido_id}',
            'email_html': '''
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
            <div style="background:#dc2626;color:white;padding:20px;text-align:center;">
                <h1 style="margin:0;font-size:20px;">Last Mile Delivery</h1>
            </div>
            <div style="padding:24px;background:#fff;">
                <h2 style="color:#dc2626;">تم إلغاء الطلب</h2>
                <p>تم إلغاء الطلب <strong>#{pedido_id}</strong>.</p>
                <p style="color:#6b7280;">السبب: {razon}</p>
            </div>
            <div style="padding:16px;background:#f8f9fc;text-align:center;color:#9ca3af;font-size:11px;">
                Last Mile Delivery Platform &copy; 2026
            </div>
        </div>
        ''',
            'sms': 'Last Mile: تم إلغاء طلبك #{pedido_id}. السبب: {razon}'
        },
        'hi': {
            'email_subject': 'ऑर्डर #{pedido_id} रद्द किया गया',
            'email_html': '''
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
            <div style="background:#dc2626;color:white;padding:20px;text-align:center;">
                <h1 style="margin:0;font-size:20px;">Last Mile Delivery</h1>
            </div>
            <div style="padding:24px;background:#fff;">
                <h2 style="color:#dc2626;">ऑर्डर रद्द किया गया</h2>
                <p>ऑर्डर <strong>#{pedido_id}</strong> रद्द कर दिया गया है।</p>
                <p style="color:#6b7280;">कारण: {razon}</p>
            </div>
            <div style="padding:16px;background:#f8f9fc;text-align:center;color:#9ca3af;font-size:11px;">
                Last Mile Delivery Platform &copy; 2026
            </div>
        </div>
        ''',
            'sms': 'Last Mile: आपका ऑर्डर #{pedido_id} रद्द कर दिया गया है। कारण: {razon}'
        },
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
        },
        'fr': {
            'email_subject': 'Paiement de ${monto} reçu',
            'email_html': '''
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
            <div style="background:#059669;color:white;padding:20px;text-align:center;">
                <h1 style="margin:0;font-size:20px;">Last Mile Delivery</h1>
            </div>
            <div style="padding:24px;background:#fff;">
                <h2 style="color:#059669;">Paiement confirmé</h2>
                <p>Nous avons reçu votre paiement de <strong>{monto}</strong>.</p>
                <table style="width:100%;border-collapse:collapse;margin:16px 0;">
                    <tr><td style="padding:8px;color:#6b7280;">Méthode :</td><td style="padding:8px;">{metodo}</td></tr>
                    <tr><td style="padding:8px;color:#6b7280;">Référence :</td><td style="padding:8px;">{referencia}</td></tr>
                    <tr><td style="padding:8px;color:#6b7280;">Date :</td><td style="padding:8px;">{fecha}</td></tr>
                </table>
            </div>
            <div style="padding:16px;background:#f8f9fc;text-align:center;color:#9ca3af;font-size:11px;">
                Last Mile Delivery Platform &copy; 2026
            </div>
        </div>
        ''',
            'sms': 'Last Mile : Paiement de {monto} reçu via {metodo}. Réf : {referencia}.'
        },
        'de': {
            'email_subject': 'Zahlung von ${monto} erhalten',
            'email_html': '''
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
            <div style="background:#059669;color:white;padding:20px;text-align:center;">
                <h1 style="margin:0;font-size:20px;">Last Mile Delivery</h1>
            </div>
            <div style="padding:24px;background:#fff;">
                <h2 style="color:#059669;">Zahlung bestätigt</h2>
                <p>Wir haben Ihre Zahlung von <strong>{monto}</strong> erhalten.</p>
                <table style="width:100%;border-collapse:collapse;margin:16px 0;">
                    <tr><td style="padding:8px;color:#6b7280;">Methode:</td><td style="padding:8px;">{metodo}</td></tr>
                    <tr><td style="padding:8px;color:#6b7280;">Referenz:</td><td style="padding:8px;">{referencia}</td></tr>
                    <tr><td style="padding:8px;color:#6b7280;">Datum:</td><td style="padding:8px;">{fecha}</td></tr>
                </table>
            </div>
            <div style="padding:16px;background:#f8f9fc;text-align:center;color:#9ca3af;font-size:11px;">
                Last Mile Delivery Platform &copy; 2026
            </div>
        </div>
        ''',
            'sms': 'Last Mile: Zahlung von {monto} erhalten via {metodo}. Ref: {referencia}.'
        },
        'it': {
            'email_subject': 'Pagamento di ${monto} ricevuto',
            'email_html': '''
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
            <div style="background:#059669;color:white;padding:20px;text-align:center;">
                <h1 style="margin:0;font-size:20px;">Last Mile Delivery</h1>
            </div>
            <div style="padding:24px;background:#fff;">
                <h2 style="color:#059669;">Pagamento confermato</h2>
                <p>Abbiamo ricevuto il tuo pagamento di <strong>{monto}</strong>.</p>
                <table style="width:100%;border-collapse:collapse;margin:16px 0;">
                    <tr><td style="padding:8px;color:#6b7280;">Metodo:</td><td style="padding:8px;">{metodo}</td></tr>
                    <tr><td style="padding:8px;color:#6b7280;">Riferimento:</td><td style="padding:8px;">{referencia}</td></tr>
                    <tr><td style="padding:8px;color:#6b7280;">Data:</td><td style="padding:8px;">{fecha}</td></tr>
                </table>
            </div>
            <div style="padding:16px;background:#f8f9fc;text-align:center;color:#9ca3af;font-size:11px;">
                Last Mile Delivery Platform &copy; 2026
            </div>
        </div>
        ''',
            'sms': 'Last Mile: Pagamento di {monto} ricevuto tramite {metodo}. Rif: {referencia}.'
        },
        'nl': {
            'email_subject': 'Betaling van ${monto} ontvangen',
            'email_html': '''
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
            <div style="background:#059669;color:white;padding:20px;text-align:center;">
                <h1 style="margin:0;font-size:20px;">Last Mile Delivery</h1>
            </div>
            <div style="padding:24px;background:#fff;">
                <h2 style="color:#059669;">Betaling bevestigd</h2>
                <p>We hebben je betaling van <strong>{monto}</strong> ontvangen.</p>
                <table style="width:100%;border-collapse:collapse;margin:16px 0;">
                    <tr><td style="padding:8px;color:#6b7280;">Methode:</td><td style="padding:8px;">{metodo}</td></tr>
                    <tr><td style="padding:8px;color:#6b7280;">Referentie:</td><td style="padding:8px;">{referencia}</td></tr>
                    <tr><td style="padding:8px;color:#6b7280;">Datum:</td><td style="padding:8px;">{fecha}</td></tr>
                </table>
            </div>
            <div style="padding:16px;background:#f8f9fc;text-align:center;color:#9ca3af;font-size:11px;">
                Last Mile Delivery Platform &copy; 2026
            </div>
        </div>
        ''',
            'sms': 'Last Mile: Betaling van {monto} ontvangen via {metodo}. Ref: {referencia}.'
        },
        'zh': {
            'email_subject': '已收到 ${monto} 付款',
            'email_html': '''
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
            <div style="background:#059669;color:white;padding:20px;text-align:center;">
                <h1 style="margin:0;font-size:20px;">Last Mile Delivery</h1>
            </div>
            <div style="padding:24px;background:#fff;">
                <h2 style="color:#059669;">付款已确认</h2>
                <p>我们已收到您 <strong>{monto}</strong> 的付款。</p>
                <table style="width:100%;border-collapse:collapse;margin:16px 0;">
                    <tr><td style="padding:8px;color:#6b7280;">方式：</td><td style="padding:8px;">{metodo}</td></tr>
                    <tr><td style="padding:8px;color:#6b7280;">参考号：</td><td style="padding:8px;">{referencia}</td></tr>
                    <tr><td style="padding:8px;color:#6b7280;">日期：</td><td style="padding:8px;">{fecha}</td></tr>
                </table>
            </div>
            <div style="padding:16px;background:#f8f9fc;text-align:center;color:#9ca3af;font-size:11px;">
                Last Mile Delivery Platform &copy; 2026
            </div>
        </div>
        ''',
            'sms': 'Last Mile：已通过{metodo}收到 {monto} 的付款。参考号：{referencia}。'
        },
        'ja': {
            'email_subject': '${monto} のお支払いを受け付けました',
            'email_html': '''
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
            <div style="background:#059669;color:white;padding:20px;text-align:center;">
                <h1 style="margin:0;font-size:20px;">Last Mile Delivery</h1>
            </div>
            <div style="padding:24px;background:#fff;">
                <h2 style="color:#059669;">お支払い確認</h2>
                <p><strong>{monto}</strong> のお支払いを受け付けました。</p>
                <table style="width:100%;border-collapse:collapse;margin:16px 0;">
                    <tr><td style="padding:8px;color:#6b7280;">支払方法：</td><td style="padding:8px;">{metodo}</td></tr>
                    <tr><td style="padding:8px;color:#6b7280;">参照番号：</td><td style="padding:8px;">{referencia}</td></tr>
                    <tr><td style="padding:8px;color:#6b7280;">日付：</td><td style="padding:8px;">{fecha}</td></tr>
                </table>
            </div>
            <div style="padding:16px;background:#f8f9fc;text-align:center;color:#9ca3af;font-size:11px;">
                Last Mile Delivery Platform &copy; 2026
            </div>
        </div>
        ''',
            'sms': 'Last Mile: {metodo}経由で {monto} のお支払いを受け付けました。参照番号：{referencia}。'
        },
        'ko': {
            'email_subject': '${monto} 결제가 확인되었습니다',
            'email_html': '''
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
            <div style="background:#059669;color:white;padding:20px;text-align:center;">
                <h1 style="margin:0;font-size:20px;">Last Mile Delivery</h1>
            </div>
            <div style="padding:24px;background:#fff;">
                <h2 style="color:#059669;">결제 확인</h2>
                <p><strong>{monto}</strong> 결제가 확인되었습니다.</p>
                <table style="width:100%;border-collapse:collapse;margin:16px 0;">
                    <tr><td style="padding:8px;color:#6b7280;">결제 수단:</td><td style="padding:8px;">{metodo}</td></tr>
                    <tr><td style="padding:8px;color:#6b7280;">참조 번호:</td><td style="padding:8px;">{referencia}</td></tr>
                    <tr><td style="padding:8px;color:#6b7280;">날짜:</td><td style="padding:8px;">{fecha}</td></tr>
                </table>
            </div>
            <div style="padding:16px;background:#f8f9fc;text-align:center;color:#9ca3af;font-size:11px;">
                Last Mile Delivery Platform &copy; 2026
            </div>
        </div>
        ''',
            'sms': 'Last Mile: {metodo}을(를) 통해 {monto} 결제가 확인되었습니다. 참조: {referencia}.'
        },
        'ar': {
            'email_subject': 'تم استلام دفعة بقيمة ${monto}',
            'email_html': '''
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
            <div style="background:#059669;color:white;padding:20px;text-align:center;">
                <h1 style="margin:0;font-size:20px;">Last Mile Delivery</h1>
            </div>
            <div style="padding:24px;background:#fff;">
                <h2 style="color:#059669;">تم تأكيد الدفع</h2>
                <p>لقد استلمنا دفعتك بقيمة <strong>{monto}</strong>.</p>
                <table style="width:100%;border-collapse:collapse;margin:16px 0;">
                    <tr><td style="padding:8px;color:#6b7280;">طريقة الدفع:</td><td style="padding:8px;">{metodo}</td></tr>
                    <tr><td style="padding:8px;color:#6b7280;">الرقم المرجعي:</td><td style="padding:8px;">{referencia}</td></tr>
                    <tr><td style="padding:8px;color:#6b7280;">التاريخ:</td><td style="padding:8px;">{fecha}</td></tr>
                </table>
            </div>
            <div style="padding:16px;background:#f8f9fc;text-align:center;color:#9ca3af;font-size:11px;">
                Last Mile Delivery Platform &copy; 2026
            </div>
        </div>
        ''',
            'sms': 'Last Mile: تم استلام دفعة بقيمة {monto} عبر {metodo}. المرجع: {referencia}.'
        },
        'hi': {
            'email_subject': '${monto} का भुगतान प्राप्त हुआ',
            'email_html': '''
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
            <div style="background:#059669;color:white;padding:20px;text-align:center;">
                <h1 style="margin:0;font-size:20px;">Last Mile Delivery</h1>
            </div>
            <div style="padding:24px;background:#fff;">
                <h2 style="color:#059669;">भुगतान की पुष्टि हुई</h2>
                <p>हमें आपका <strong>{monto}</strong> का भुगतान प्राप्त हो गया है।</p>
                <table style="width:100%;border-collapse:collapse;margin:16px 0;">
                    <tr><td style="padding:8px;color:#6b7280;">तरीका:</td><td style="padding:8px;">{metodo}</td></tr>
                    <tr><td style="padding:8px;color:#6b7280;">संदर्भ:</td><td style="padding:8px;">{referencia}</td></tr>
                    <tr><td style="padding:8px;color:#6b7280;">तारीख:</td><td style="padding:8px;">{fecha}</td></tr>
                </table>
            </div>
            <div style="padding:16px;background:#f8f9fc;text-align:center;color:#9ca3af;font-size:11px;">
                Last Mile Delivery Platform &copy; 2026
            </div>
        </div>
        ''',
            'sms': 'Last Mile: {metodo} के माध्यम से {monto} का भुगतान प्राप्त हुआ। संदर्भ: {referencia}.'
        },
    }
}

# Language detection from country code.
# Mismo set de paises que fiscal_providers.py (COUNTRY_CURRENCIES) -- se
# mantiene alineado para que cualquier pais con soporte fiscal/de pago
# tambien tenga notificaciones en su idioma en vez de caer siempre a 'es'.
COUNTRY_LANG = {
    'MX': 'es', 'CO': 'es', 'AR': 'es', 'CL': 'es', 'PE': 'es', 'UY': 'es', 'EC': 'es', 'ES': 'es',
    'BR': 'pt', 'PT': 'pt',
    'US': 'en', 'CA': 'en', 'GB': 'en', 'AU': 'en', 'SG': 'en', 'HK': 'en', 'IE': 'en', 'EU': 'en',
    'DE': 'de', 'AT': 'de',
    'FR': 'fr', 'BE': 'fr',
    'IT': 'it',
    'NL': 'nl',
    'JP': 'ja',
    'CN': 'zh',
    'KR': 'ko',
    'IN': 'hi',
    'SA': 'ar', 'AE': 'ar',
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


# Singleton
notification_service = NotificationService()
