"""
LAST MILE DELIVERY - WhatsApp Business API Service
Uses Twilio WhatsApp channel (same SDK as SMS, different sending endpoint).
Falls back to console logging when credentials are not set.
"""

import os
import logging

logger = logging.getLogger('lastmile.whatsapp')


class WhatsAppService:
    """Send WhatsApp messages via Twilio WhatsApp Business API."""

    def __init__(self):
        self.account_sid = os.environ.get('TWILIO_ACCOUNT_SID', '')
        self.auth_token = os.environ.get('TWILIO_AUTH_TOKEN', '')
        self.from_number = os.environ.get('TWILIO_WHATSAPP_FROM', '')
        self.enabled = bool(self.account_sid and self.auth_token and self.from_number)
        if self.enabled:
            logger.info(f'[WHATSAPP] Twilio WhatsApp configured: {self.from_number}')
        else:
            logger.info('[WHATSAPP] No Twilio WhatsApp credentials - WhatsApp disabled')

    def send(self, to, message, template_sid=None, template_vars=None):
        """
        Send a WhatsApp message.

        Args:
            to: Recipient phone in E.164 format (e.g. '+5215512345678')
            message: Plain text message (used when no template_sid)
            template_sid: Optional Twilio Content SID for pre-approved templates
            template_vars: Optional dict of template variables

        Returns:
            dict with 'success', 'sid' or 'error'
        """
        if not self.enabled:
            logger.info(f'[WHATSAPP] Would send to {to}: {message[:80]}...')
            return {'success': True, 'provider': 'console', 'message': 'WhatsApp logged (no credentials)'}

        if not to:
            return {'success': False, 'error': 'No phone number provided'}

        # Ensure WhatsApp prefix
        wa_to = to if to.startswith('whatsapp:') else f'whatsapp:{to}'
        wa_from = self.from_number if self.from_number.startswith('whatsapp:') else f'whatsapp:{self.from_number}'

        try:
            from twilio.rest import Client
            client = Client(self.account_sid, self.auth_token)

            if template_sid:
                # Send using pre-approved template (required for first contact outside 24h window)
                from_vars = template_vars or {}
                msg = client.messages.create(
                    content_sid=template_sid,
                    content_variables=str(from_vars) if from_vars else None,
                    from_=wa_from,
                    to=wa_to
                )
            else:
                # Send free-form message (only works within 24h conversation window)
                msg = client.messages.create(
                    body=message,
                    from_=wa_from,
                    to=wa_to
                )

            logger.info(f'[WHATSAPP] Sent to {to}: {msg.sid}')
            return {'success': True, 'sid': msg.sid, 'status': msg.status}

        except Exception as e:
            error_msg = str(e)
            logger.error(f'[WHATSAPP] Exception sending to {to}: {error_msg}')
            return {'success': False, 'error': error_msg[:200]}

    def send_template(self, to, template_sid, language='es', variables=None):
        """
        Send a pre-approved WhatsApp template message.
        Required for first contact or messages outside the 24h window.

        Args:
            to: Recipient phone in E.164 format
            template_sid: Twilio Content SID for the template
            language: Template language code (es, en, pt)
            variables: Dict of template variables e.g. {"1": "Juan", "2": "PED-001"}
        """
        if not self.enabled:
            logger.info(f'[WHATSAPP] Would send template to {to}: {template_sid}')
            return {'success': True, 'provider': 'console', 'message': 'WhatsApp template logged'}

        wa_to = to if to.startswith('whatsapp:') else f'whatsapp:{to}'
        wa_from = self.from_number if self.from_number.startswith('whatsapp:') else f'whatsapp:{self.from_number}'

        try:
            from twilio.rest import Client
            client = Client(self.account_sid, self.auth_token)

            import json
            msg = client.messages.create(
                content_sid=template_sid,
                content_variables=json.dumps(variables) if variables else None,
                from_=wa_from,
                to=wa_to
            )

            logger.info(f'[WHATSAPP] Template sent to {to}: {msg.sid}')
            return {'success': True, 'sid': msg.sid, 'status': msg.status}

        except Exception as e:
            logger.error(f'[WHATSAPP] Template exception to {to}: {str(e)}')
            return {'success': False, 'error': str(e)[:200]}

    def get_status(self):
        """Return service configuration status."""
        return {
            'enabled': self.enabled,
            'provider': 'twilio_whatsapp',
            'from_number': self.from_number if self.enabled else None,
            'has_credentials': bool(self.account_sid and self.auth_token)
        }


# Singleton
whatsapp_service = WhatsAppService()
