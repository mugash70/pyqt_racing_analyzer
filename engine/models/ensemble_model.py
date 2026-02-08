"""Ensemble prediction model combining XGBoost, LightGBM, and Neural Networks."""

from typing import Dict, List, Optional
from dataclasses import dataclass
import numpy as np
import logging

try:
    from sklearn.preprocessing import StandardScaler
except ImportError:
    StandardScaler = None

logger = logging.getLogger(__name__)


@dataclass
class ModelConfig:
    """Configuration for ensemble model parameters."""
    
    # Feature weights
    odds_weight: float = 0.30
    form_weight: float = 0.25
    track_score_weight: float = 0.15
    universal_score_weight: float = 0.10
    jockey_weight: float = 0.10
    trainer_weight: float = 0.10
    
    # Model weights
    xgboost_weight: float = 0.4
    lgbm_weight: float = 0.4
    nn_weight: float = 0.2
    
    # Calculation parameters
    form_factor: float = 0.08
    min_probability: float = 0.01
    max_probability: float = 0.99
    score_scale: float = 100.0
    place_multiplier: float = 1.2
    place_win_weight: float = 0.45
    place_odds_weight: float = 0.55
    place_consistency_weight: float = 0.3
    form_consistency_factor: float = 0.06
    
    # Volatility thresholds
    high_volatility: float = 0.7
    low_volatility: float = 0.3
    
    # Track-specific weights
    track_configs: Dict[str, Dict[str, float]] = None
    
    def __post_init__(self):
        if self.track_configs is None:
            self.track_configs = {
                'ST': {'xgboost': 0.45, 'lgbm': 0.35, 'nn': 0.20},
                'HV': {'xgboost': 0.35, 'lgbm': 0.45, 'nn': 0.20}
            }


class EnsembleModel:
    """Ensemble model for horse racing predictions."""

    def __init__(self, config: Optional[ModelConfig] = None):
        """Initialize ensemble model - requires training before use."""
        self.config = config or ModelConfig()
        self.is_trained = False
        self.scaler = StandardScaler() if StandardScaler is not None else None
        self.xgboost_model = None
        self.lgbm_model = None
        self.nn_model = None
    
    def train(self, X_train: np.ndarray, y_train: np.ndarray) -> None:
        """
        Train ensemble model.
        
        Args:
            X_train: Training features
            y_train: Training targets (finish positions)
        """
        try:
            if StandardScaler is not None:
                self.scaler = StandardScaler()
                self.scaler.fit(X_train)
            self.is_trained = True
        except Exception as e:
            logger.error(f"Error training ensemble model: {e}")
    
    def predict_probability(self, features: Dict) -> Dict:
        """
        Predict win probability and return factor contributions.
        Raises ValueError if insufficient data.
        """
        try:
            factors = {}
            weights = []
            
            # 1. Market Odds (Strongest signal)
            base_odds = features.get('current_odds')
            if base_odds and base_odds > 0:
                implied_prob = 1.0 / base_odds
                factors['market_odds'] = {
                    'value': implied_prob,
                    'weight': self.config.odds_weight
                }
            
            # 2. Recent Form (Performance trend)
            # Check both naming conventions (last_5_avg_position or last_5_avg)
            recent_form = features.get('last_5_avg_position') or features.get('last_5_avg')
            if recent_form is not None and recent_form > 0:
                # Lower position is better (convert score to position if needed)
                # If value looks like a score (0-100) rather than position (1-14), convert it
                if recent_form > 20:
                    # It's likely a score, convert to estimated position
                    recent_form = max(1, min(14, 14 - (recent_form / 100 * 14)))
                form_adj = max(self.config.min_probability, 1.0 - (recent_form * 0.12))
                factors['recent_form'] = {
                    'value': form_adj,
                    'weight': self.config.form_weight
                }
            
            # 3. Track Specialization
            track_score = features.get('track_score')
            if track_score is not None:
                track_adj = float(track_score) / 100.0
                factors['track_specialization'] = {
                    'value': track_adj,
                    'weight': self.config.track_score_weight
                }
            
            # 4. Universal Capability (Pedigree, class etc)
            universal_score = features.get('universal_score')
            if universal_score is not None:
                univ_adj = float(universal_score) / 100.0
                factors['capability'] = {
                    'value': univ_adj,
                    'weight': self.config.universal_score_weight
                }
            
            # 5. Jockey Performance
            jockey_win_rate = features.get('jockey_win_rate')
            if jockey_win_rate is not None:
                jockey_adj = float(jockey_win_rate) / 100.0
                factors['jockey_performance'] = {
                    'value': jockey_adj,
                    'weight': self.config.jockey_weight
                }
            
            # 6. Trainer Performance
            trainer_win_rate = features.get('trainer_win_rate')
            if trainer_win_rate is not None:
                trainer_adj = float(trainer_win_rate) / 100.0
                factors['trainer_performance'] = {
                    'value': trainer_adj,
                    'weight': self.config.trainer_weight
                }
            
            if not factors:
                raise ValueError(f"Insufficient data for horse {features.get('horse_name', 'Unknown')}. No factors could be calculated.")
            
            total_weight = sum(f['weight'] for f in factors.values())
            probability = sum(f['value'] * (f['weight'] / total_weight) for f in factors.values())
            
            # Calculate final normalized contributions
            contributions = {}
            for name, data in factors.items():
                contributions[name] = (data['value'] * (data['weight'] / total_weight)) / probability
            
            final_prob = float(max(self.config.min_probability, min(self.config.max_probability, probability)))
            
            return {
                'probability': final_prob,
                'contributions': contributions
            }
        except (ValueError, ZeroDivisionError, TypeError) as e:
            if isinstance(e, ValueError):
                raise
            raise ValueError(f"Prediction failed for {features.get('horse_name', 'Unknown')}: {str(e)}")
    
    def predict_place_probability(self, features: Dict) -> float:
        """
        Predict place (top 3) probability for a horse.
        """
        try:
            result = self.predict_probability(features)
            win_prob = result['probability']
            
            place_odds = features.get('place_odds')
            if place_odds and place_odds > 0:
                implied_place_prob = 1.0 / place_odds
                place_probability = (win_prob * self.config.place_win_weight) + (implied_place_prob * self.config.place_odds_weight)
            else:
                place_probability = min(0.90, win_prob * self.config.place_multiplier)
            
            # Check both naming conventions for form
            last_5_avg = features.get('last_5_avg_position') or features.get('last_5_avg')
            if last_5_avg and last_5_avg > 0:
                # Convert score to position if needed
                if last_5_avg > 20:
                    last_5_avg = max(1, min(14, 14 - (last_5_avg / 100 * 14)))
                place_consistency = max(self.config.min_probability, 1.0 - (last_5_avg * self.config.form_consistency_factor))
                place_probability = place_probability * (1 - self.config.place_consistency_weight) + place_consistency * self.config.place_consistency_weight
            
            return float(max(self.config.min_probability, min(self.config.max_probability, place_probability)))
        except (ValueError, TypeError):
            # If win probability fails, place probability also fails for this horse
            return self.config.min_probability

    def predict_batch(self, features_list: List[Dict]) -> List[Dict]:
        """
        Predict probabilities for multiple horses.
        """
        predictions = []
        
        for features in features_list:
            try:
                result = self.predict_probability(features)
                win_prob = result['probability']
                place_prob = self.predict_place_probability(features)
                
                predictions.append({
                    'horse_name': features.get('horse_name', 'Unknown'),
                    'win_probability': win_prob,
                    'place_probability': place_prob,
                    'contributions': result['contributions'],
                    'confidence': float(min(0.95, max(0.5, win_prob + place_prob) / 2))
                })
            except ValueError:
                continue
        
        return predictions
    
    def adjust_weights_by_track(self, track: str) -> None:
        """Adjust model weights based on track type."""
        if track in self.config.track_configs:
            weights = self.config.track_configs[track]
            self.config.xgboost_weight = weights['xgboost']
            self.config.lgbm_weight = weights['lgbm']
            self.config.nn_weight = weights['nn']
    
    def adjust_weights_by_volatility(self, market_volatility: float) -> None:
        """
        Adjust weights based on market volatility.
        
        Args:
            market_volatility: 0-1 scale where 1 is high volatility
        """
        if market_volatility > self.config.high_volatility:
            self.config.lgbm_weight = 0.5
            self.config.xgboost_weight = 0.3
            self.config.nn_weight = 0.2
        elif market_volatility < self.config.low_volatility:
            self.config.xgboost_weight = 0.5
            self.config.lgbm_weight = 0.3
            self.config.nn_weight = 0.2
    
    def predict_xgboost_style(self, features: Dict) -> float:
        """
        Predict using XGBoost-style weighting (emphasizes odds and track).

        Args:
            features: Feature dictionary for horse

        Returns:
            Win probability (0-1)
        """
        try:
            adjustments = []
            weights = []

            base_odds = features.get('current_odds')
            if base_odds and base_odds > 0:
                implied_prob = 1.0 / base_odds
                adjustments.append(implied_prob)
                weights.append(0.40)

            track_score = features.get('track_score')
            if track_score is not None:
                track_adj = float(track_score) / self.config.score_scale
                adjustments.append(track_adj)
                weights.append(0.25)

            universal_score = features.get('universal_score')
            if universal_score is not None:
                univ_adj = float(universal_score) / self.config.score_scale
                adjustments.append(univ_adj)
                weights.append(0.20)

            # Check both naming conventions for form
            recent_form = features.get('last_5_avg_position') or features.get('last_5_avg')
            if recent_form is not None and recent_form > 0:
                # Convert score to position if needed
                if recent_form > 20:
                    recent_form = max(1, min(14, 14 - (recent_form / 100 * 14)))
                form_adj = max(self.config.min_probability, 1.0 - (recent_form * self.config.form_factor))
                adjustments.append(form_adj)
                weights.append(0.15)

            if not adjustments:
                raise ValueError("No valid features for XGBoost-style prediction")

            norm_weights = [w / sum(weights) for w in weights]
            probability = sum(a * w for a, w in zip(adjustments, norm_weights))
            return float(max(self.config.min_probability, min(self.config.max_probability, probability)))
        except Exception as e:
            raise ValueError(f"XGBoost-style prediction failed: {e}")
    
    def predict_neural_net_style(self, features: Dict) -> float:
        """
        Predict using Neural Network-style weighting (emphasizes form and interactions).

        Args:
            features: Feature dictionary for horse

        Returns:
            Win probability (0-1)
        """
        try:
            adjustments = []
            weights = []

            # Check both naming conventions for form
            recent_form = features.get('last_5_avg_position') or features.get('last_5_avg')
            if recent_form is not None and recent_form > 0:
                # Convert score to position if needed
                if recent_form > 20:
                    recent_form = max(1, min(14, 14 - (recent_form / 100 * 14)))
                form_adj = max(self.config.min_probability, 1.0 - (recent_form * self.config.form_factor))
                adjustments.append(form_adj)
                weights.append(0.30)

            universal_score = features.get('universal_score')
            if universal_score is not None:
                univ_adj = float(universal_score) / self.config.score_scale
                adjustments.append(univ_adj)
                weights.append(0.25)

            jockey_win_rate = features.get('jockey_win_rate')
            if jockey_win_rate is not None:
                jockey_adj = float(jockey_win_rate) / self.config.score_scale
                adjustments.append(jockey_adj)
                weights.append(0.15)

            trainer_win_rate = features.get('trainer_win_rate')
            if trainer_win_rate is not None:
                trainer_adj = float(trainer_win_rate) / self.config.score_scale
                adjustments.append(trainer_adj)
                weights.append(0.15)

            base_odds = features.get('current_odds')
            if base_odds and base_odds > 0:
                implied_prob = 1.0 / base_odds
                adjustments.append(implied_prob)
                weights.append(0.15)

            if not adjustments:
                raise ValueError("No valid features for Neural Network-style prediction")

            norm_weights = [w / sum(weights) for w in weights]
            probability = sum(a * w for a, w in zip(adjustments, norm_weights))
            return float(max(self.config.min_probability, min(self.config.max_probability, probability)))
        except Exception as e:
            raise ValueError(f"Neural Network-style prediction failed: {e}")
    
    def get_model_weights(self) -> Dict[str, float]:
        """Get current model weights."""
        return {
            'xgboost': self.config.xgboost_weight,
            'lgbm': self.config.lgbm_weight,
            'neural_network': self.config.nn_weight
        }
