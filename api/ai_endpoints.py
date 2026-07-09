"""
Last Mile Platform - AI Endpoints for Flask
Add these to server.py or run as separate module
"""
from flask import Blueprint, request, jsonify
import json

ai_bp = Blueprint('ai', __name__)

# Import AI service
try:
    from ai_service import chat, optimize_routes, get_suggestions
except ImportError:
    # Fallback if ai_service not found
    def chat(msg, context=None, history=None):
        return {'response': 'Servicio de IA no disponible', 'type': 'error', 'quick_replies': []}
    def optimize_routes(orders, drivers, start=None):
        return {'routes': {}, 'summary': {'total_orders': len(orders)}}
    def get_suggestions(panel='tenant'):
        return []

# ============================================================
# POST /api/ai/chat
# ============================================================
@ai_bp.route('/api/ai/chat', methods=['POST'])
def ai_chat():
    """
    Chat with AI agent
    
    Body:
    {
        "message": "cuantos envios llevo hoy",
        "panel": "tenant",          // tenant|support|admin|operacion
        "chat_history": [],         // optional: previous messages
        "context": {}               // optional: {emp_id, user_id, etc}
    }
    """
    data = request.get_json() or {}
    message = data.get('message', '').strip()
    
    if not message:
        return jsonify({'success': False, 'error': 'Message required'}), 400
    
    context = data.get('context', {})
    context['panel'] = data.get('panel', 'support')
    chat_history = data.get('chat_history', [])
    
    # Get response from AI service
    result = chat(message, context=context, chat_history=chat_history)
    
    return jsonify({
        'success': True,
        'data': result
    })

# ============================================================
# POST /api/ai/optimize-routes
# ============================================================
@ai_bp.route('/api/ai/optimize-routes', methods=['POST'])
def ai_optimize_routes():
    """
    Optimize delivery routes
    
    Body:
    {
        "orders": [
            {"id": 1, "lat": 19.43, "lng": -99.13, "priority": "normal"},
            ...
        ],
        "drivers": [
            {"id": 1, "lat": 19.42, "lng": -99.12, "capacity": 10, "current_orders": []},
            ...
        ],
        "start_location": {"lat": 19.43, "lng": -99.13}  // optional depot
    }
    """
    data = request.get_json() or {}
    orders = data.get('orders', [])
    drivers = data.get('drivers', [])
    start = data.get('start_location')
    
    if not orders or not drivers:
        return jsonify({'success': False, 'error': 'Orders and drivers required'}), 400
    
    result = optimize_routes(orders, drivers, start)
    
    return jsonify({
        'success': True,
        'data': result
    })

# ============================================================
# GET /api/ai/suggestions
# ============================================================
@ai_bp.route('/api/ai/suggestions', methods=['GET'])
def ai_suggestions():
    """
    Get contextual quick action suggestions
    
    Query params:
    - panel: tenant|support|admin|operacion
    """
    panel = request.args.get('panel', 'tenant')
    suggestions = get_suggestions(panel)
    
    return jsonify({
        'success': True,
        'data': suggestions
    })

# ============================================================
# POST /api/ai/route-preview
# ============================================================
@ai_bp.route('/api/ai/route-preview', methods=['POST'])
def ai_route_preview():
    """
    Quick route preview for a single driver
    
    Body:
    {
        "driver_lat": 19.42,
        "driver_lng": -99.12,
        "order_ids": [1, 2, 3, 4, 5]
    }
    """
    data = request.get_json() or {}
    driver_lat = data.get('driver_lat', 19.43)
    driver_lng = data.get('driver_lng', -99.13)
    order_ids = data.get('order_ids', [])
    
    # Demo: generate random order locations near driver
    import random
    orders = []
    for oid in order_ids:
        orders.append({
            'id': oid,
            'lat': driver_lat + random.uniform(-0.05, 0.05),
            'lng': driver_lng + random.uniform(-0.05, 0.05),
            'priority': random.choice(['normal', 'normal', 'express', 'urgente'])
        })
    
    drivers = [{
        'id': 1,
        'lat': driver_lat,
        'lng': driver_lng,
        'capacity': 10,
        'current_orders': [],
        'name': 'Chofer'
    }]
    
    result = optimize_routes(orders, drivers, {'lat': driver_lat, 'lng': driver_lng})
    
    return jsonify({
        'success': True,
        'data': result
    })

# ============================================================
# Register blueprint in server.py:
#   from ai_endpoints import ai_bp
#   app.register_blueprint(ai_bp)
# ============================================================
