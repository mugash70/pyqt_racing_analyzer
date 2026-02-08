"""PyQT-ready output formatting."""

from typing import Dict, List


class UIFormatter:
    """Formats prediction output for PyQT interface."""
    
    @staticmethod
    def format_race_card(predictions: Dict) -> Dict:
        """
        Format race card for UI display.
        
        Returns structured data for table display.
        """
        formatted = {
            'race_info': predictions.get('race_info', {}),
            'horses': []
        }
        
        for pred in predictions.get('predictions', []):
            formatted['horses'].append({
                'number': pred.get('horse_number', 0),
                'name': pred.get('horse_name', ''),
                'jockey': pred.get('jockey', ''),
                'trainer': pred.get('trainer', ''),
                'weight': pred.get('weight', ''),
                'draw': pred.get('draw', 0),
                'win_probability': f"{pred.get('win_probability', 0):.1f}%",
                'place_probability': f"{pred.get('place_probability', 0):.1f}%",
                'current_odds': f"{pred.get('current_odds'):.2f}" if pred.get('current_odds') else "N/A",
                'confidence': f"{pred.get('confidence', 0):.0%}",
                'risk_score': f"{pred.get('risk_score', 0):.0f}",
                'recommendation': pred.get('risk_recommendation', 'Neutral'),
                'color': UIFormatter._get_confidence_color(pred.get('confidence', 0.5))
            })
        
        return formatted
    
    @staticmethod
    def format_horse_detail(prediction: Dict) -> Dict:
        """Format detailed horse information for popup."""
        return {
            'number': prediction.get('horse_number', 0),
            'name': prediction.get('horse_name', ''),
            'jockey': prediction.get('jockey', ''),
            'trainer': prediction.get('trainer', ''),
            'weight': prediction.get('weight', ''),
            'draw': prediction.get('draw', 0),
            'universal_score': f"{prediction.get('universal_score', 0):.0f}",
            'track_score': f"{prediction.get('track_score', 0):.0f}",
            'win_probability': f"{prediction.get('win_probability', 0):.1f}%",
            'place_probability': f"{prediction.get('place_probability', 0):.1f}%",
            'current_odds': f"{prediction.get('current_odds'):.2f}" if prediction.get('current_odds') else "N/A",
            'confidence': f"{prediction.get('confidence', 0):.0%}",
            'risk_score': f"{prediction.get('risk_score', 0):.0f}",
            'risk_recommendation': prediction.get('risk_recommendation', ''),
            'risk_factors': prediction.get('risk_factors', {})
        }
    
    @staticmethod
    def format_top_picks(predictions: Dict) -> List[Dict]:
        """Format top 3 picks for display."""
        top_picks = []
        
        for i, pred in enumerate(predictions.get('top_3', []), 1):
            top_picks.append({
                'rank': i,
                'horse_name': pred.get('horse_name', ''),
                'win_probability': f"{pred.get('win_probability', 0):.1f}%",
                'current_odds': f"{pred.get('current_odds', 0):.2f}",
                'confidence': f"{pred.get('confidence', 0):.0%}",
                'emoji': ['🥇', '🥈', '🥉'][min(i-1, 2)]
            })
        
        return top_picks
    
    @staticmethod
    def format_value_bets(predictions: Dict) -> List[Dict]:
        """Format value betting opportunities."""
        value_bets = []
        
        for pred in predictions.get('value_picks', [])[:3]:
            value_bets.append({
                'horse_name': pred.get('horse_name', ''),
                'win_probability': f"{pred.get('win_probability', 0):.1f}%",
                'current_odds': f"{pred.get('current_odds', 0):.2f}",
                'confidence': f"{pred.get('confidence', 0):.0%}"
            })
        
        return value_bets
    
    @staticmethod
    def format_risk_alerts(predictions: Dict) -> List[Dict]:
        """Format high-risk horse alerts."""
        alerts = []
        
        for pred in predictions.get('high_risk_horses', [])[:3]:
            alerts.append({
                'horse_name': pred.get('horse_name', ''),
                'risk_score': f"{pred.get('risk_score', 0):.0f}",
                'recommendation': pred.get('risk_recommendation', 'High Risk'),
                'icon': '⚠️'
            })
        
        return alerts
    
    @staticmethod
    def _get_confidence_color(confidence: float) -> str:
        """Get color code for confidence level."""
        if confidence >= 0.8:
            return 'green'
        elif confidence >= 0.65:
            return 'yellow'
        else:
            return 'red'
    
    @staticmethod
    def format_odds_table(odds_data: List[Dict]) -> List[Dict]:
        """Format live odds for table display."""
        formatted = []
        
        for odds in odds_data:
            formatted.append({
                'horse_number': odds.get('number', 0),
                'horse_name': odds.get('name', ''),
                'win_odds': f"{odds.get('win_odds', 0):.2f}",
                'place_odds': f"{odds.get('place_odds', 0):.2f}",
                'timestamp': odds.get('timestamp', '')
            })
        
        return formatted
