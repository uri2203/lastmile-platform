"""
Agente 2: Asignación Inteligente
Asigna pedidos al chofer óptimo considerando:
- Cercanía al punto de recogida
- Carga actual del chofer
- Habilidad/rating del chofer
- Disponibilidad horaria
- Zona de dominio del chofer
"""
from typing import List, Dict, Optional
import math

class SmartAssignment:
    def __init__(self):
        self.weights = {
            'distance': 0.35,
            'load': 0.25,
            'rating': 0.20,
            'zone_expertise': 0.15,
            'availability': 0.05
        }
    
    def calculate_distance(self, lat1, lon1, lat2, lon2) -> float:
        R = 6371
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
        return R * 2 * math.asin(math.sqrt(a))
    
    def score_driver(self, driver: Dict, order: Dict, max_distance: float = 20) -> float:
        # Distance score (closer = better)
        dist = self.calculate_distance(
            driver.get('lat', 0), driver.get('lng', 0),
            order.get('pickup_lat', 0), order.get('pickup_lng', 0)
        )
        dist_score = max(0, 1 - (dist / max_distance))
        
        # Load score (less load = better)
        current_load = driver.get('active_orders', 0)
        max_load = driver.get('max_orders', 5)
        load_score = max(0, 1 - (current_load / max_load))
        
        # Rating score
        rating = driver.get('rating', 4.0)
        rating_score = rating / 5.0
        
        # Zone expertise
        driver_zones = driver.get('zones', [])
        order_zone = order.get('zone', '')
        zone_score = 1.0 if order_zone in driver_zones else 0.3
        
        # Availability
        availability = 1.0 if driver.get('status') == 'available' else 0.0
        
        total = (
            dist_score * self.weights['distance'] +
            load_score * self.weights['load'] +
            rating_score * self.weights['rating'] +
            zone_score * self.weights['zone_expertise'] +
            availability * self.weights['availability']
        )
        
        return round(total, 3)
    
    def assign_order(self, order: Dict, drivers: List[Dict]) -> Optional[Dict]:
        if not drivers:
            return None
        
        scored = [(d, self.score_driver(d, order)) for d in drivers]
        scored.sort(key=lambda x: x[1], reverse=True)
        
        best_driver, best_score = scored[0]
        
        return {
            'driver_id': best_driver['id'],
            'driver_name': best_driver.get('name', ''),
            'score': best_score,
            'distance_km': round(self.calculate_distance(
                best_driver.get('lat', 0), best_driver.get('lng', 0),
                order.get('pickup_lat', 0), order.get('pickup_lng', 0)
            ), 2),
            'reason': self._get_assignment_reason(best_driver, order, best_score)
        }
    
    def _get_assignment_reason(self, driver, order, score) -> str:
        reasons = []
        if score > 0.8: reasons.append('alta compatibilidad')
        dist = self.calculate_distance(
            driver.get('lat', 0), driver.get('lng', 0),
            order.get('pickup_lat', 0), order.get('pickup_lng', 0)
        )
        if dist < 3: reasons.append('muy cercano')
        if driver.get('rating', 0) >= 4.5: reasons.append('alto rating')
        if driver.get('active_orders', 0) == 0: reasons.append('disponible')
        return ', '.join(reasons) if reasons else 'mejor opción disponible'

smart_assignment = SmartAssignment()
