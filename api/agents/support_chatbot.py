"""
Agente 4: Chatbot de Soporte
Atiende clientes 24/7 con:
- Respuestas frecuentes
- Tracking de pedidos
- Escalamiento a humano
"""
from typing import Dict, List, Optional
import re

class SupportChatbot:
    def __init__(self):
        self.faqs = {
            'tracking': {
                'patterns': ['rastrear', 'tracking', 'donde esta', 'ubicacion', 'paquete', 'envio'],
                'response': 'Para rastrear tu envío, ingresa tu token en tracking-cliente.html o proporciona tu número de pedido.'
            },
            'factura': {
                'patterns': ['factura', 'facturacion', 'cfdi', 'timbrar', 'xml'],
                'response': 'Las facturas CFDI 4.0 se generan automáticamente. Si necesitas una, contacta a facturacion@lastmile.mx con tu número de pedido.'
            },
            'pago': {
                'patterns': ['pago', 'pagar', 'cobro', 'tarjeta', 'oxxo', 'transferencia'],
                'response': 'Aceptamos: OXXO, transferencia SPEI, tarjeta de crédito/débito, y MercadoPago. ¿Cuál necesitas?'
            },
            'cancelar': {
                'patterns': ['cancelar', 'cancelacion', 'devolver', 'reembolso'],
                'response': 'Puedes cancelar si el pedido no ha sido asignado. Si ya está en camino, contacta soporte para asistencia.'
            },
            'chofer': {
                'patterns': ['chofer', 'conductor', 'repartidor', 'reparto'],
                'response': 'Tu chofer aparece en el mapa de tracking. Puedes llamarlo o enviarle WhatsApp desde ahí.'
            },
            'costo': {
                'patterns': ['costo', 'precio', 'cuanto cuesta', 'tarifa', 'cobro'],
                'response': 'El costo se calcula por zona, peso y dimensiones. Lo ves al crear el pedido antes de confirmar.'
            },
            'horario': {
                'patterns': ['horario', 'hora', 'cuando llega', 'tiempo'],
                'response': 'Los envios locales se entregan en 2-4 horas. Foraneos en 24-48 horas. El ETA exacto aparece en tracking.'
            },
            'cuenta': {
                'patterns': ['cuenta', 'contraseña', 'acceso', 'login', 'registro'],
                'response': 'Para crear cuenta ve a onboarding.html. Para recuperar contraseña, contacta soporte.'
            }
        }
        self.escalation_keywords = ['hablar con alguien', 'agente humano', 'soporte humano', 'queja', 'reclamo']
    
    def get_response(self, message: str, context: Dict = None) -> Dict:
        message_lower = message.lower()
        
        # Check for escalation
        for keyword in self.escalation_keywords:
            if keyword in message_lower:
                return {
                    'response': 'Te conecto con un agente humano. Por favor espera un momento...',
                    'type': 'escalation',
                    'confidence': 1.0
                }
        
        # Check FAQs
        for faq_key, faq_data in self.faqs.items():
            for pattern in faq_data['patterns']:
                if pattern in message_lower:
                    return {
                        'response': faq_data['response'],
                        'type': 'faq',
                        'confidence': 0.9,
                        'category': faq_key
                    }
        
        # Check if it's an order number
        order_match = re.search(r'PED-\d+', message, re.IGNORECASE)
        if order_match:
            return {
                'response': f'Buscando pedido {order_match.group()}... Por favor ingresa al tracking con tu token para ver el estado en tiempo real.',
                'type': 'order_lookup',
                'confidence': 0.85
            }
        
        # Default response
        return {
            'response': 'No estoy seguro de entender tu pregunta. Puedo ayudarte con: tracking, facturas, pagos, cancelaciones, costos, horarios y cuentas. ¿Sobre qué necesitas ayuda?',
            'type': 'fallback',
            'confidence': 0.3
        }
    
    def get_suggestions(self, partial_message: str) -> List[str]:
        suggestions = []
        partial_lower = partial_message.lower()
        for faq_data in self.faqs.values():
            for pattern in faq_data['patterns']:
                if partial_lower and pattern.startswith(partial_lower[:3]):
                    suggestions.append(pattern)
        return suggestions[:5]

support_chatbot = SupportChatbot()
