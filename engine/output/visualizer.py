"""Data visualization and charting."""

from typing import Dict, List


class Visualizer:
    """Creates visualizations and charts for race predictions."""
    
    @staticmethod
    def create_probability_chart_data(predictions: Dict) -> Dict:
        """Create data for probability bar chart."""
        horses = []
        probabilities = []
        
        for pred in predictions.get('predictions', []):
            horses.append(pred.get('horse_name', '')[:15])
            probabilities.append(pred.get('win_probability', 0))
        
        return {
            'type': 'bar',
            'labels': horses,
            'data': probabilities,
            'title': 'Win Probabilities',
            'unit': '%'
        }
    
    @staticmethod
    def create_odds_movement_data(initial_odds: List[float], 
                                 current_odds: List[float]) -> Dict:
        """Create data for odds movement chart."""
        movements = []
        for init, curr in zip(initial_odds, current_odds):
            if init > 0:
                movement = ((curr - init) / init) * 100
                movements.append(movement)
            else:
                movements.append(0)
        
        return {
            'type': 'line',
            'data': movements,
            'title': 'Odds Movement (%)',
            'colors': ['red' if m > 0 else 'green' for m in movements]
        }
    
    @staticmethod
    def create_risk_gauge_data(horse_name: str, risk_score: float) -> Dict:
        """Create data for risk gauge visualization."""
        if risk_score < 30:
            risk_level = 'LOW'
            color = 'green'
        elif risk_score < 60:
            risk_level = 'MEDIUM'
            color = 'yellow'
        else:
            risk_level = 'HIGH'
            color = 'red'
        
        return {
            'type': 'gauge',
            'value': risk_score,
            'max': 100,
            'title': f'{horse_name} - Risk Assessment',
            'level': risk_level,
            'color': color
        }
    
    @staticmethod
    def create_confidence_distribution(predictions: Dict) -> Dict:
        """Create confidence distribution data."""
        high_confidence = sum(1 for p in predictions.get('predictions', []) 
                            if p.get('confidence', 0) >= 0.75)
        medium_confidence = sum(1 for p in predictions.get('predictions', []) 
                              if 0.5 <= p.get('confidence', 0) < 0.75)
        low_confidence = sum(1 for p in predictions.get('predictions', []) 
                           if p.get('confidence', 0) < 0.5)
        
        return {
            'type': 'pie',
            'labels': ['High Confidence', 'Medium Confidence', 'Low Confidence'],
            'data': [high_confidence, medium_confidence, low_confidence],
            'colors': ['green', 'yellow', 'red']
        }
    
    @staticmethod
    def create_form_trend_data(recent_positions: List[int]) -> Dict:
        """Create form trend visualization."""
        return {
            'type': 'line',
            'labels': [f'Race {i}' for i in range(len(recent_positions), 0, -1)],
            'data': recent_positions,
            'title': 'Recent Form Trend',
            'invert_y': True
        }
    
    @staticmethod
    def create_comparison_radar(horse_name: str, scores: Dict) -> Dict:
        """Create radar chart for horse capability comparison."""
        return {
            'type': 'radar',
            'title': f'{horse_name} - Capability Profile',
            'categories': list(scores.keys()),
            'data': list(scores.values()),
            'max': 100
        }
    
    @staticmethod
    def create_market_efficiency_chart(market_probability: float, 
                                      model_probability: float) -> Dict:
        """Create market efficiency comparison."""
        difference = abs(market_probability - model_probability)
        
        return {
            'type': 'comparison',
            'market': market_probability,
            'model': model_probability,
            'difference': difference,
            'title': 'Market vs Model Probability',
            'opportunity': 'Undervalued' if market_probability < model_probability else 'Overvalued'
        }
