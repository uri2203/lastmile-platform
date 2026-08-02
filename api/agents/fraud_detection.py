"""
Agente 7: Detección de Fraude
Identifica pedidos/pagos sospechosos:
- Pedidos con monto inusual
- Múltiples intentos de pago
- Direcciones falsas
- Patrones anómalos
"""
from typing import Dict, List
from datetime import datetime, timedelta
import re

class FraudDetector:
    def __init__(self):
        self.risk_thresholds = {
            'high': 0.7,
            'medium': 0.4,
            'low': 0.2
        }
        self.suspicious_patterns = {
            'test_card': ['4111', '5555', '3782'],
            'disposable_email': ['tempmail', 'throwaway', 'guerrilla', 'mailinator'],
            'high_value': 10000,  # MXN
            'multiple_orders_hour': 5
        }
    
    def analyze_order(self, order: Dict, customer_history: Dict = None) -> Dict:
        risk_score = 0
        risk_factors = []
        
        # Check amount
        amount = order.get('total', 0)
        if amount > self.suspicious_patterns['high_value']:
            risk_score += 0.3
            risk_factors.append(f'Monto alto: ${amount}')
        
        # Check address
        address = order.get('address', '')
        if not address or len(address) < 10:
            risk_score += 0.2
            risk_factors.append('Dirección incompleta')
        
        # Check phone
        phone = order.get('phone', '')
        if not re.match(r'^\d{10}$', phone.replace('-', '').replace(' ', '')):
            risk_score += 0.15
            risk_factors.append('Teléfono inválido')
        
        # Check email
        email = order.get('email', '')
        for pattern in self.suspicious_patterns['disposable_email']:
            if pattern in email.lower():
                risk_score += 0.4
                risk_factors.append('Email desechable')
        
        # Check customer history
        if customer_history:
            recent_orders = customer_history.get('orders_last_hour', 0)
            if recent_orders > self.suspicious_patterns['multiple_orders_hour']:
                risk_score += 0.35
                risk_factors.append(f'{recent_orders} pedidos en la última hora')
            
            previous_fraud = customer_history.get('fraud_flags', 0)
            if previous_fraud > 0:
                risk_score += 0.5
                risk_factors.append(f'{previous_fraud} incidentes previos')
        
        # Check time
        hour = datetime.now().hour
        if 2 <= hour <= 5:
            risk_score += 0.1
            risk_factors.append('Pedido en horario nocturno')
        
        risk_level = 'low'
        if risk_score >= self.risk_thresholds['high']:
            risk_level = 'high'
        elif risk_score >= self.risk_thresholds['medium']:
            risk_level = 'medium'
        
        return {
            'risk_score': round(min(risk_score, 1.0), 2),
            'risk_level': risk_level,
            'risk_factors': risk_factors,
            'recommendation': self._get_recommendation(risk_level),
            'requires_review': risk_level in ['high', 'medium']
        }
    
    def analyze_payment(self, payment: Dict) -> Dict:
        risk_score = 0
        risk_factors = []
        
        # Check card number pattern
        card = payment.get('card_number', '')
        for test in self.suspicious_patterns['test_card']:
            if card.startswith(test):
                risk_score += 0.8
                risk_factors.append('Tarjeta de prueba detectada')
        
        # Check amount consistency
        if payment.get('amount', 0) != payment.get('expected_amount', 0):
            risk_score += 0.4
            risk_factors.append('Monto no coincide con pedido')
        
        # Check multiple attempts
        attempts = payment.get('attempts', 1)
        if attempts > 3:
            risk_score += 0.3
            risk_factors.append(f'{attempts} intentos de pago')
        
        risk_level = 'low'
        if risk_score >= 0.7: risk_level = 'high'
        elif risk_score >= 0.4: risk_level = 'medium'
        
        return {
            'risk_score': round(min(risk_score, 1.0), 2),
            'risk_level': risk_level,
            'risk_factors': risk_factors,
            'block_payment': risk_level == 'high'
        }
    
    def _get_recommendation(self, level: str) -> str:
        recommendations = {
            'high': 'Bloquear pedido y revisar manualmente. Notificar al admin.',
            'medium': 'Marcar para revisión. Permitir con verificación adicional.',
            'low': 'Procesar normalmente.'
        }
        return recommendations.get(level, recommendations['low'])

fraud_detector = FraudDetector()
