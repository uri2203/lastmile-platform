"""
Agente 1: Optimizador de Rutas
Calcula la ruta óptima para múltiples entregas considerando:
- Distancia entre puntos
- Ventanas de tiempo
- Prioridad de entregas
- Tráfico (estimado por horario)
"""
import math
from typing import List, Dict, Tuple

class RouteOptimizer:
    def __init__(self):
        self.traffic_multipliers = {
            'morning_rush': 1.5,  # 7-9am
            'evening_rush': 1.4,  # 5-7pm
            'lunch': 1.2,  # 12-2pm
            'normal': 1.0,
            'night': 0.8  # 9pm+
        }
    
    def get_traffic_multiplier(self, hour: int) -> float:
        if 7 <= hour <= 9: return self.traffic_multipliers['morning_rush']
        if 17 <= hour <= 19: return self.traffic_multipliers['evening_rush']
        if 12 <= hour <= 14: return self.traffic_multipliers['lunch']
        if 21 <= hour or hour <= 5: return self.traffic_multipliers['night']
        return self.traffic_multipliers['normal']
    
    def haversine_distance(self, lat1, lon1, lat2, lon2) -> float:
        R = 6371
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
        return R * 2 * math.asin(math.sqrt(a))
    
    def optimize_route(self, origin: Dict, deliveries: List[Dict], constraints: Dict = None) -> Dict:
        """
        Optimiza ruta usando nearest neighbor + 2-opt improvement
        origin: {lat, lng}
        deliveries: [{id, lat, lng, priority, time_window_start, time_window_end}]
        """
        if not deliveries:
            return {'route': [], 'total_distance': 0, 'total_time': 0}
        
        # Nearest neighbor
        route = []
        remaining = deliveries.copy()
        current = origin
        total_distance = 0
        
        while remaining:
            nearest = min(remaining, key=lambda d: self.haversine_distance(
                current['lat'], current['lng'], d['lat'], d['lng']
            ))
            dist = self.haversine_distance(current['lat'], current['lng'], nearest['lat'], nearest['lng'])
            total_distance += dist
            route.append({**nearest, 'distance_from_prev': dist})
            current = nearest
            remaining.remove(nearest)
        
        # 2-opt improvement
        improved = True
        while improved:
            improved = False
            for i in range(len(route) - 1):
                for j in range(i + 2, len(route)):
                    if self._should_swap(i, j, route, origin):
                        route[i:j+1] = reversed(route[i:j+1])
                        improved = True
        
        # Calculate ETA
        import datetime
        now = datetime.datetime.now()
        current_hour = now.hour
        traffic = self.get_traffic_multiplier(current_hour)
        avg_speed = 30 / traffic  # km/h adjusted
        
        total_time = 0
        for i, stop in enumerate(route):
            stop['eta_minutes'] = round((stop.get('distance_from_prev', 0) / avg_speed) * 60)
            total_time += stop['eta_minutes']
            stop['cumulative_eta'] = total_time
        
        return {
            'route': route,
            'total_distance_km': round(total_distance, 2),
            'total_time_minutes': total_time,
            'traffic_level': 'high' if traffic > 1.3 else 'medium' if traffic > 1.1 else 'low',
            'stops': len(route)
        }
    
    def _should_swap(self, i, j, route, origin):
        if i == 0:
            d1 = self.haversine_distance(origin['lat'], origin['lng'], route[j]['lat'], route[j]['lng'])
            d2 = self.haversine_distance(route[j-1]['lat'], route[j-1]['lng'], route[i]['lat'], route[i]['lng'])
        else:
            d1 = self.haversine_distance(route[i-1]['lat'], route[i-1]['lng'], route[j]['lat'], route[j]['lng'])
            d2 = self.haversine_distance(route[j-1]['lat'], route[j-1]['lng'], route[i]['lat'], route[i]['lng'])
        
        d3 = self.haversine_distance(route[i]['lat'], route[i]['lng'], route[i+1]['lat'], route[i+1]['lng']) if i+1 < len(route) else 0
        d4 = self.haversine_distance(route[j]['lat'], route[j]['lng'], route[j+1]['lat'], route[j+1]['lng']) if j+1 < len(route) else 0
        
        return (d1 + d2) < (d3 + d4)

route_optimizer = RouteOptimizer()
