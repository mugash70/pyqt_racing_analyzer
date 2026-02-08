"""Real-time prediction updates based on live odds."""

from typing import Dict, List, Optional
from ..prediction.probability_calculator import ProbabilityCalculator


class RealTimeUpdater:
    """Updates predictions in real-time as odds change."""
    
    def __init__(self, predictor):
        """Initialize real-time updater."""
        self.predictor = predictor
        self.current_predictions = {}
        self.prediction_history = {}
    
    def update_predictions(self, odds_movements: Dict) -> Dict:
        """
        Update predictions based on new odds.
        
        Args:
            odds_movements: Dictionary of current odds movements
            
        Returns:
            Updated predictions
        """
        updated = {}
        
        for horse_num, odds_data in odds_movements.items():
            current_odds = odds_data.get('current_odds', 0)
            movement_pct = odds_data.get('movement_percentage', 0)
            
            if horse_num in self.current_predictions:
                old_pred = self.current_predictions[horse_num]
                
                win_prob = ProbabilityCalculator.calculate_win_probability(
                    current_odds,
                    old_pred.get('form_factor', 0.5),
                    old_pred.get('track_factor', 0.5)
                )
                
                confidence_adj = 1.0 - (abs(movement_pct) / 100.0) * 0.3
                
                updated[horse_num] = {
                    'horse_name': old_pred.get('horse_name', ''),
                    'current_odds': current_odds,
                    'win_probability': win_prob * 100,
                    'place_probability': old_pred.get('place_probability', 0),
                    'confidence': old_pred.get('confidence', 0.7) * confidence_adj,
                    'odds_movement_pct': movement_pct,
                    'updated_at': self._get_timestamp(),
                    'previous_probability': old_pred.get('win_probability', 0)
                }
                
                if horse_num not in self.prediction_history:
                    self.prediction_history[horse_num] = []
                
                self.prediction_history[horse_num].append(updated[horse_num])
        
        self.current_predictions = updated
        return updated
    
    def get_probability_changes(self, horse_num: str) -> Dict:
        """Get probability change trends."""
        if horse_num not in self.prediction_history:
            return {'status': 'No history'}
        
        history = self.prediction_history[horse_num]
        
        if len(history) < 2:
            return {'status': 'Insufficient data'}
        
        probabilities = [h['win_probability'] for h in history]
        first = probabilities[0]
        last = probabilities[-1]
        
        return {
            'horse_number': horse_num,
            'initial_probability': first,
            'current_probability': last,
            'change': last - first,
            'change_percentage': ((last - first) / first * 100) if first > 0 else 0,
            'trend': 'improving' if last > first else 'declining',
            'updates': len(history)
        }
    
    def detect_probability_flips(self, threshold: float = 5.0) -> List[Dict]:
        """Detect horses with significant probability changes."""
        flips = []
        
        for horse_num, history in self.prediction_history.items():
            if len(history) >= 2:
                change = self.get_probability_changes(horse_num)
                
                if abs(change.get('change', 0)) > threshold:
                    flips.append(change)
        
        flips.sort(key=lambda x: abs(x.get('change', 0)), reverse=True)
        return flips
    
    def get_convergence_signal(self, predictions: List[Dict]) -> Optional[Dict]:
        """
        Detect when market and model predictions are converging.
        
        Returns signal when alignment is high.
        """
        total_diff = 0
        count = 0
        
        for pred in predictions:
            implied_prob = (1 / pred.get('current_odds', 5.0)) * 100
            model_prob = pred.get('win_probability', 0)
            diff = abs(implied_prob - model_prob)
            total_diff += diff
            count += 1
        
        if count == 0:
            return None
        
        avg_diff = total_diff / count
        
        if avg_diff < 5:
            return {
                'signal': 'HIGH_CONVERGENCE',
                'confidence': 'High',
                'message': 'Market and model predictions are well aligned'
            }
        elif avg_diff < 10:
            return {
                'signal': 'MODERATE_CONVERGENCE',
                'confidence': 'Moderate',
                'message': 'Some divergence between market and model'
            }
        else:
            return {
                'signal': 'LOW_CONVERGENCE',
                'confidence': 'Low',
                'message': 'Significant divergence detected'
            }
    
    @staticmethod
    def _get_timestamp() -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()
