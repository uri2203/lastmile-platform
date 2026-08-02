"""
Agente 5: Predicción de Demanda
Predice volumen de pedidos por zona y hora usando:
- Datos históricos
- Patrones estacionales
- Días especiales
"""
from typing import Dict, List
from datetime import datetime, timedelta
import math

class DemandForecaster:
    def __init__(self):
        self.hourly_patterns = {
            0: 0.1, 1: 0.05, 2: 0.02, 3: 0.02, 4: 0.03, 5: 0.05,
            6: 0.1, 7: 0.3, 8: 0.6, 9: 0.8, 10: 0.9, 11: 1.0,
            12: 0.95, 13: 0.85, 14: 0.8, 15: 0.85, 16: 0.9, 17: 1.0,
            18: 0.95, 19: 0.8, 20: 0.6, 21: 0.4, 22: 0.25, 23: 0.15
        }
        self.weekly_patterns = {
            0: 1.0, 1: 1.0, 2: 1.05, 3: 1.0, 4: 1.1, 5: 1.2, 6: 0.7
        }
        self.zones_data = {}
    
    def get_demand_level(self, hour: int, day_of_week: int) -> str:
        hourly = self.hourly_patterns.get(hour, 0.5)
        weekly = self.weekly_patterns.get(day_of_week, 1.0)
        combined = hourly * weekly
        
        if combined > 0.8: return 'high'
        if combined > 0.5: return 'medium'
        if combined > 0.2: return 'low'
        return 'minimal'
    
    def predict_hourly_volume(self, zone: str, base_daily: int = 100) -> List[Dict]:
        now = datetime.now()
        predictions = []
        
        for h in range(24):
            hourly_factor = self.hourly_patterns.get(h, 0.5)
            predicted = round(base_daily * hourly_factor / 24)
            
            predictions.append({
                'hour': h,
                'time_label': f'{h:02d}:00',
                'predicted_orders': max(0, predicted),
                'demand_level': self.get_demand_level(h, now.weekday()),
                'recommended_drivers': max(1, round(predicted / 10))
            })
        
        return predictions
    
    def predict_weekly(self, zone: str, base_daily: int = 100) -> List[Dict]:
        days = ['Lunes', 'Martes', 'Miercoles', 'Jueves', 'Viernes', 'Sabado', 'Domingo']
        predictions = []
        
        for d in range(7):
            weekly_factor = self.weekly_patterns.get(d, 1.0)
            predicted = round(base_daily * weekly_factor)
            
            predictions.append({
                'day': d,
                'day_name': days[d],
                'predicted_orders': predicted,
                'peak_hour': max(self.hourly_patterns, key=self.hourly_patterns.get),
                'recommended_drivers': max(1, round(predicted / 80))
            })
        
        return predictions
    
    def get_recommendations(self, zone: str, current_hour: int) -> Dict:
        level = self.get_demand_level(current_hour, datetime.now().weekday())
        
        recommendations = {
            'high': {
                'action': 'Activar todos los choferes disponibles',
                'message': 'Alta demanda esperada. Considera activar choferes extra.',
                'surge_pricing': True
            },
            'medium': {
                'action': 'Mantener operación normal',
                'message': 'Demanda moderada. Operación estándar.',
                'surge_pricing': False
            },
            'low': {
                'action': 'Reducir choferes activos',
                'message': 'Baja demanda. Puedes reducir personal.',
                'surge_pricing': False
            },
            'minimal': {
                'action': 'Solo esenciales',
                'message': 'Demanda mínima. Solo mantener choferes esenciales.',
                'surge_pricing': False
            }
        }
        
        return {
            'zone': zone,
            'current_level': level,
            'recommendations': recommendations.get(level, recommendations['medium']),
            'next_peak_hour': self._find_next_peak(current_hour)
        }
    
    def _find_next_peak(self, current_hour: int) -> int:
        for h in range(current_hour + 1, 24):
            if self.hourly_patterns.get(h, 0) > 0.8:
                return h
        return 8  # Default morning peak

demand_forecaster = DemandForecaster()
