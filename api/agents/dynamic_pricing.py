"""
Agente 6: Pricing Dinámico
Calcula precio justo basado en:
- Distancia
- Demanda actual
- Hora del día
- Prioridad
- Zona
"""
from typing import Dict
from datetime import datetime

class DynamicPricing:
    def __init__(self):
        self.base_price = 49.0  # MXN
        self.price_per_km = 8.5
        self.price_per_kg = 2.0
        self.surge_multipliers = {
            'high': 1.3,
            'medium': 1.0,
            'low': 0.9,
            'minimal': 0.85
        }
        self.priority_multipliers = {
            'normal': 1.0,
            'urgent': 1.5,
            'express': 2.0
        }
        self.zone_multipliers = {
            'centro': 1.0,
            'zona_norte': 1.1,
            'zona_sur': 1.05,
            'zona_este': 1.0,
            'zona_oeste': 1.08,
            'periferia': 1.2
        }
    
    def calculate_price(self, order: Dict, demand_level: str = 'medium') -> Dict:
        distance = order.get('distance_km', 5)
        weight = order.get('weight_kg', 1)
        priority = order.get('priority', 'normal')
        zone = order.get('zone', 'centro')
        
        # Base calculation
        base = self.base_price
        distance_cost = distance * self.price_per_km
        weight_cost = weight * self.price_per_kg
        
        # Subtotal
        subtotal = base + distance_cost + weight_cost
        
        # Apply multipliers
        demand_mult = self.surge_multipliers.get(demand_level, 1.0)
        priority_mult = self.priority_multipliers.get(priority, 1.0)
        zone_mult = self.zone_multipliers.get(zone, 1.0)
        
        total = subtotal * demand_mult * priority_mult * zone_mult
        
        # Minimum price
        total = max(total, 35.0)
        
        return {
            'price': round(total, 2),
            'currency': 'MXN',
            'breakdown': {
                'base': base,
                'distance': round(distance_cost, 2),
                'weight': round(weight_cost, 2),
                'subtotal': round(subtotal, 2),
                'demand_multiplier': demand_mult,
                'priority_multiplier': priority_mult,
                'zone_multiplier': zone_mult
            },
            'demand_level': demand_level,
            'estimated_delivery': self._estimate_delivery_time(distance, priority)
        }
    
    def _estimate_delivery_time(self, distance: float, priority: str) -> str:
        base_hours = 2 + (distance / 20)
        if priority == 'express': base_hours *= 0.5
        elif priority == 'urgent': base_hours *= 0.7
        
        if base_hours < 1: return '30-60 minutos'
        if base_hours < 2: return '1-2 horas'
        if base_hours < 4: return '2-4 horas'
        return '4-8 horas'
    
    def get_surge_info(self, zone: str) -> Dict:
        hour = datetime.now().hour
        if 7 <= hour <= 9 or 17 <= hour <= 19:
            return {'active': True, 'multiplier': 1.3, 'reason': 'Hora pico'}
        if 12 <= hour <= 14:
            return {'active': True, 'multiplier': 1.15, 'reason': 'Hora de almuerzo'}
        return {'active': False, 'multiplier': 1.0, 'reason': 'Tarifa normal'}

dynamic_pricing = DynamicPricing()
