"""
Agente 8: Análisis de Sentimiento
Analiza feedback de clientes:
- Reseñas
- Comentarios
- Quejas
- Sugerencias
"""
from typing import Dict, List
import re

class SentimentAnalyzer:
    def __init__(self):
        self.positive_words = [
            'excelente', 'bueno', 'buena', 'rapido', 'rapida', 'perfecto', 'perfecta',
            'genial', 'increible', 'fantastico', 'fantastica', 'satisfecho', 'satisfecha',
            'recomiendo', 'profesional', 'puntual', 'eficiente', 'facil', 'comoda',
            'love', 'great', 'excellent', 'perfect', 'amazing', 'fast', 'good',
            'wonderful', 'fantastic', 'satisfied', 'recommend', 'professional'
        ]
        self.negative_words = [
            'malo', 'mala', 'lento', 'lenta', 'terrible', 'horrible', 'pésimo',
            'pésima', 'no llego', 'no funciono', 'roto', 'rota', 'dañado', 'dañada',
            'furioso', 'furiosa', 'molesto', 'molesta', 'decepcionado', 'decepcionada',
            'bad', 'slow', 'terrible', 'horrible', 'broken', 'damaged', 'angry',
            'upset', 'disappointed', 'worst', 'never', 'lost'
        ]
        self.neutral_words = [
            'normal', 'regular', 'ok', 'aceptable', 'mediocre', 'average', 'fine', 'okay'
        ]
    
    def analyze(self, text: str) -> Dict:
        text_lower = text.lower()
        
        positive_count = sum(1 for w in self.positive_words if w in text_lower)
        negative_count = sum(1 for w in self.negative_words if w in text_lower)
        neutral_count = sum(1 for w in self.neutral_words if w in text_lower)
        
        total = positive_count + negative_count + neutral_count
        
        if total == 0:
            score = 0.5
            sentiment = 'neutral'
        else:
            score = (positive_count - negative_count + total) / (2 * total)
            if score > 0.6: sentiment = 'positive'
            elif score < 0.4: sentiment = 'negative'
            else: sentiment = 'neutral'
        
        keywords = self._extract_keywords(text_lower)
        
        return {
            'sentiment': sentiment,
            'score': round(score, 2),
            'confidence': round(min(0.5 + total * 0.1, 0.95), 2),
            'keywords': keywords,
            'suggested_response': self._suggest_response(sentiment, keywords)
        }
    
    def _extract_keywords(self, text: str) -> List[str]:
        words = re.findall(r'\b\w+\b', text)
        important = [w for w in words if len(w) > 4]
        return list(set(important))[:5]
    
    def _suggest_response(self, sentiment: str, keywords: List[str]) -> str:
        if sentiment == 'positive':
            return '¡Gracias por tu feedback! Nos alegra que estés satisfecho.'
        elif sentiment == 'negative':
            return 'Lamentamos tu experiencia. Por favor contacta soporte para resolver tu caso.'
        return 'Gracias por tu comentario. Lo tomamos en cuenta para mejorar.'
    
    def batch_analyze(self, texts: List[str]) -> Dict:
        results = [self.analyze(t) for t in texts]
        avg_score = sum(r['score'] for r in results) / len(results) if results else 0.5
        
        return {
            'total': len(results),
            'average_score': round(avg_score, 2),
            'positive': sum(1 for r in results if r['sentiment'] == 'positive'),
            'negative': sum(1 for r in results if r['sentiment'] == 'negative'),
            'neutral': sum(1 for r in results if r['sentiment'] == 'neutral'),
            'details': results
        }

sentiment_analyzer = SentimentAnalyzer()
