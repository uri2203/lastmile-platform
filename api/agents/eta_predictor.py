"""
Agente 3: Predicción de ETA
Predice tiempo real de llegada usando:
- Datos históricos de entregas
- Condiciones de tráfico actuales
- Distancia y ruta
- Hora del día
- Clima (opcional)
"""
import math
from typing import Dict, List, Optional
from datetime import datetime, timedelta

class ETAPredictor:
    def __init__(self):
        self.historical_data = []
        self.base_speed_kmh = 25  # Velocidad base en ciudad
    
    def get_traffic_factor(self, hour: int, day_of_week: int) -> float:
        factors = {
            (0, 7): 1.0, (0, 8): 1.4, (0, 9): 1.5, (0, 10): 1.2, (0, 11): 1.1,
            (0, 12): 1.2, (0, 13): 1.2, (0, 14): 1.1, (0, 15): 1.1, (0, 16): 1.3,
            (0, 17): 1.5, (0, 18): 1.4, (0, 19): 1.2, (0, 20): 1.1, (0, 21): 1.0,
            (6, 7): 0.8, (6, 8): 0.8, (6, 9): 0.9,  # Domingo
        }
        return factors.get((day_of_week, hour), 1.0)
    
    def calculate_distance(self, lat1, lon1, lat2, lon2) -> float:
        R = 6371
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
        return R * 2 * math.asin(math.sqrt(a))
    
    def predict_eta(self, origin: Dict, destination: Dict, context: Dict = None) -> Dict:
        now = datetime.now()
        hour = now.hour
        day = now.weekday()
        
        distance = self.calculate_distance(
            origin['lat'], origin['lng'],
            destination['lat'], destination['lng']
        )
        
        traffic_factor = self.get_traffic_factor(hour, day)
        adjusted_speed = self.base_speed_kmh / traffic_factor
        
        base_time_minutes = (distance / adjusted_speed) * 60
        
        # Ajustar por tipo de zona
        zone_factor = 1.0
        if context:
            zone_type = context.get('zone_type', 'urban')
            if zone_type == 'urban': zone_factor = 1.0
            elif zone_type == 'suburban': zone_factor = 0.9
            elif zone_type == 'highway': zone_factor = 0.7
            
            # Ajustar por clima
            weather = context.get('weather', 'clear')
            if weather == 'rain': zone_factor *= 1.2
            elif weather == 'storm': zone_factor *= 1.5
        
        estimated_minutes = round(base_time_minutes * zone_factor)
        confidence = 0.85 if distance < 10 else 0.7 if distance < 20 else 0.6
        
        return {
            'eta_minutes': estimated_minutes,
            'eta_arrival': (now + timedelta(minutes=estimated_minutes)).strftime('%H:%M'),
            'distance_km': round(distance, 2),
            'confidence': confidence,
            'traffic_level': 'high' if traffic_factor > 1.3 else 'medium' if traffic_factor > 1.1 else 'low',
            'factors': {
                'distance': round(distance, 2),
                'traffic_factor': traffic_factor,
                'zone_factor': zone_factor,
                'base_speed': self.base_speed_kmh,
                'adjusted_speed': round(adjusted_speed, 1)
            }
        }
    
    def update_with_actual(self, predicted: float, actual: float):
        self.historical_data.append({'predicted': predicted, 'actual': actual})
        if len(self.historical_data) > 1000:
            self.historical_data = self.historical_data[-500:]

eta_predictor = ETAPredictor()
