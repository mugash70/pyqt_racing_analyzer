"""Enhanced ensemble model with advanced calibration and explainability."""

from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class EnhancedModelConfig:
    """Configuration for enhanced ensemble model."""
    
    # Feature weights (sum to 1.0)
    form_weight: float = 0.22
    track_weight: float = 0.15
    distance_weight: float = 0.12
    jockey_weight: float = 0.10
    trainer_weight: float = 0.08
    draw_weight: float = 0.08
    weight_carry_weight: float = 0.05
    market_weight: float = 0.12
    pedigree_weight: float = 0.03
    health_weight: float = 0.05
    
    # Model component weights
    form_model_weight: float = 0.30
    track_model_weight: float = 0.25
    market_model_weight: float = 0.20
    human_model_weight: float = 0.15
    health_model_weight: float = 0.10
    
    # Calibration parameters
    calibration_exponent: float = 0.82
    favorite_compression: float = 0.15
    longshot_boost: float = 0.08
    
    # Probability bounds
    min_probability: float = 0.005
    max_probability: float = 0.95
    
    # Place prediction parameters
    place_multiplier: float = 2.8
    place_win_weight: float = 0.40
    place_consistency_weight: float = 0.35
    place_form_weight: float = 0.25
    
    # Track-specific adjustments
    track_configs: Dict = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.track_configs:
            self.track_configs = {
                'ST': {'sprint_bias': 0.05, 'stamina_premium': 0.08},
                'HV': {'turn_handling': 0.10, 'draw_premium': 0.06}
            }


class EnhancedEnsembleModel:
    """
    Enhanced ensemble model with multi-component prediction and detailed explanations.
    
    Components:
    1. Form Model: Recent performance, trends, momentum
    2. Track Model: Track/distance specialization
    3. Market Model: Odds and market signals
    4. Human Model: Jockey/trainer performance and synergy
    5. Health Model: Fitness, veterinary status, preparation
    """
    
    def __init__(self, config: Optional[EnhancedModelConfig] = None):
        self.config = config or EnhancedModelConfig()
        self.calibration_history = []
    
    def predict_with_explanation(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate prediction with detailed explanation.
        
        Returns comprehensive prediction with reasoning.
        """
        horse_name = features.get('horse_name', 'Unknown')
        
        try:
            # Calculate component scores
            form_result = self._form_model_predict(features)
            track_result = self._track_model_predict(features)
            market_result = self._market_model_predict(features)
            human_result = self._human_model_predict(features)
            health_result = self._health_model_predict(features)
            
            # Combine component predictions
            components = {
                'form': form_result,
                'track': track_result,
                'market': market_result,
                'human': human_result,
                'health': health_result
            }
            
            # Calculate weighted ensemble probability
            raw_probability = self._combine_components(components)
            
            # Apply calibration
            calibrated_prob = self._calibrate_probability(
                raw_probability, 
                features.get('current_odds', 10.0)
            )
            
            # Calculate place probability
            place_prob = self._calculate_place_probability(features, calibrated_prob)
            
            # Calculate confidence
            confidence = self._calculate_confidence(components, features)
            
            # Generate detailed explanation
            explanation = self._generate_detailed_explanation(
                components, features, calibrated_prob, confidence
            )
            
            return {
                'horse_name': horse_name,
                'win_probability': float(calibrated_prob),
                'place_probability': float(place_prob),
                'raw_probability': float(raw_probability),
                'confidence': float(confidence),
                'components': {
                    name: {
                        'score': comp['score'],
                        'probability': comp['probability'],
                        'weight': comp['weight']
                    }
                    for name, comp in components.items()
                },
                'explanation': explanation,
                'key_factors': explanation['key_factors'],
                'risk_assessment': explanation['risk_assessment'],
                'recommendation': explanation['recommendation']
            }
            
        except Exception as e:
            logger.error(f"Prediction error for {horse_name}: {e}")
            return self._fallback_prediction(horse_name)
    
    def _form_model_predict(self, features: Dict) -> Dict:
        """Form-based prediction component."""
        scores = []
        
        # Recent form (last 5 races)
        last_5_avg = features.get('last_5_avg', 8.0)
        form_score = max(0, 100 - (last_5_avg * 10))
        scores.append(('recent_form', form_score, 0.40))
        
        # Consistency
        consistency = features.get('consistency_score', 50)
        scores.append(('consistency', consistency, 0.20))
        
        # Momentum
        momentum = features.get('momentum_score', 50)
        scores.append(('momentum', momentum, 0.20))
        
        # Win rate
        win_rate = features.get('win_rate', 0) * 100
        scores.append(('win_rate', win_rate, 0.20))
        
        # Calculate weighted score
        total_weight = sum(w for _, _, w in scores)
        weighted_score = sum(s * w for _, s, w in scores) / total_weight
        
        # Convert to probability (0-1)
        probability = self._score_to_probability(weighted_score)
        
        return {
            'score': float(weighted_score),
            'probability': float(probability),
            'weight': self.config.form_model_weight,
            'details': {name: score for name, score, _ in scores}
        }
    
    def _track_model_predict(self, features: Dict) -> Dict:
        """Track/distance-based prediction component."""
        scores = []
        
        # Track score
        track_score = features.get('track_score', 50)
        scores.append(('track_fitness', track_score, 0.35))
        
        # Distance score
        distance_score = features.get('distance_score', 50)
        scores.append(('distance_fitness', distance_score, 0.35))
        
        # Track-distance synergy
        synergy = features.get('track_distance_synergy', 50)
        scores.append(('track_distance_synergy', synergy, 0.20))
        
        # Draw score
        draw_score = features.get('draw_score', 50)
        scores.append(('draw_position', draw_score, 0.10))
        
        weighted_score = sum(s * w for _, s, w in scores) / sum(w for _, _, w in scores)
        probability = self._score_to_probability(weighted_score)
        
        return {
            'score': float(weighted_score),
            'probability': float(probability),
            'weight': self.config.track_model_weight,
            'details': {name: score for name, score, _ in scores}
        }
    
    def _market_model_predict(self, features: Dict) -> Dict:
        """Market-based prediction component."""
        scores = []
        
        # Odds score
        odds_score = features.get('odds_score', 50)
        scores.append(('market_position', odds_score, 0.50))
        
        # Market support (odds movement)
        market_support = features.get('market_support', 0)
        market_support_score = 50 + market_support
        scores.append(('market_support', market_support_score, 0.30))
        
        # Implied probability confidence
        implied = features.get('implied_prob', 0.10) * 100
        scores.append(('implied_prob', implied, 0.20))
        
        weighted_score = sum(s * w for _, s, w in scores) / sum(w for _, _, w in scores)
        probability = self._score_to_probability(weighted_score)
        
        return {
            'score': float(weighted_score),
            'probability': float(probability),
            'weight': self.config.market_model_weight,
            'details': {name: score for name, score, _ in scores}
        }
    
    def _human_model_predict(self, features: Dict) -> Dict:
        """Jockey/trainer-based prediction component."""
        scores = []
        
        # Jockey score
        jockey_score = features.get('jockey_score', 50)
        scores.append(('jockey_ability', jockey_score, 0.35))
        
        # Trainer score
        trainer_score = features.get('trainer_score', 50)
        scores.append(('trainer_ability', trainer_score, 0.35))
        
        # Jockey-trainer synergy
        synergy_score = features.get('jt_synergy_score', 50)
        scores.append(('jockey_trainer_synergy', synergy_score, 0.30))
        
        weighted_score = sum(s * w for _, s, w in scores) / sum(w for _, _, w in scores)
        probability = self._score_to_probability(weighted_score)
        
        return {
            'score': float(weighted_score),
            'probability': float(probability),
            'weight': self.config.human_model_weight,
            'details': {name: score for name, score, _ in scores}
        }
    
    def _health_model_predict(self, features: Dict) -> Dict:
        """Health/fitness-based prediction component."""
        scores = []
        
        # Fitness/health score
        fitness = features.get('fitness_health_score', 70)
        scores.append(('fitness_health', fitness, 0.35))
        
        # Preparation (trials, trackwork)
        prep = features.get('preparation_score', 50)
        scores.append(('preparation', prep, 0.30))
        
        # First-up considerations
        if features.get('first_up_flag', 0):
            # Slight discount for first-up
            scores.append(('first_up_penalty', 65, 0.20))
        else:
            scores.append(('race_fitness', 75, 0.20))
        
        # Weight score
        weight_score = features.get('weight_score', 70)
        scores.append(('weight_carry', weight_score, 0.15))
        
        weighted_score = sum(s * w for _, s, w in scores) / sum(w for _, _, w in scores)
        probability = self._score_to_probability(weighted_score)
        
        return {
            'score': float(weighted_score),
            'probability': float(probability),
            'weight': self.config.health_model_weight,
            'details': {name: score for name, score, _ in scores}
        }
    
    def _combine_components(self, components: Dict) -> float:
        """Combine component probabilities into ensemble prediction."""
        weighted_sum = sum(
            comp['probability'] * comp['weight']
            for comp in components.values()
        )
        total_weight = sum(comp['weight'] for comp in components.values())
        
        return weighted_sum / total_weight
    
    def _calibrate_probability(self, raw_prob: float, current_odds: float) -> float:
        """Apply calibration to raw probability."""
        # Power law calibration
        calibrated = raw_prob ** self.config.calibration_exponent
        
        # Favorite compression (reduce favorite overconfidence)
        if calibrated > 0.35:
            calibrated = calibrated - (calibrated - 0.35) * self.config.favorite_compression
        
        # Longshot boost (slight boost to long shots)
        if calibrated < 0.08:
            calibrated = calibrated * (1 + self.config.longshot_boost)
        
        # Ensure bounds
        return float(np.clip(calibrated, self.config.min_probability, self.config.max_probability))
    
    def _calculate_place_probability(self, features: Dict, win_prob: float) -> float:
        """Calculate place (top 3) probability."""
        # Base place probability from win probability
        base_place = win_prob * self.config.place_multiplier
        
        # Adjust for consistency (consistent horses more likely to place)
        consistency = features.get('consistency_score', 50) / 100
        consistency_adj = consistency * self.config.place_consistency_weight
        
        # Adjust for form
        place_rate = features.get('place_rate', 0.25)
        form_adj = place_rate * self.config.place_form_weight
        
        # Combine
        place_prob = (win_prob * self.config.place_win_weight + 
                     consistency_adj + form_adj)
        
        # Normalize to reasonable bounds (place prob should be ~2.5-3x win prob)
        place_prob = np.clip(place_prob, win_prob * 1.5, min(0.85, win_prob * 4))
        
        return float(place_prob)
    
    def _calculate_confidence(self, components: Dict, features: Dict) -> float:
        """Calculate overall prediction confidence."""
        # Component agreement (lower variance = higher confidence)
        probs = [comp['probability'] for comp in components.values()]
        variance = np.var(probs)
        agreement_confidence = 1.0 - min(0.5, variance)
        
        # Data completeness
        completeness_factors = [
            features.get('form_available', 0),
            1.0 if features.get('track_experience', 0) > 0 else 0.5,
            features.get('odds_available', 0),
            1.0 if features.get('jockey_score', 50) > 40 else 0.6,
            features.get('vet_clear', 1)
        ]
        data_confidence = np.mean(completeness_factors)
        
        # Combine
        confidence = agreement_confidence * 0.6 + data_confidence * 0.4
        
        return float(np.clip(confidence, 0.15, 0.99))
    
    def _score_to_probability(self, score: float) -> float:
        """Convert 0-100 score to 0-1 probability with sigmoid."""
        # Normalize to -5 to 5 range
        normalized = (score - 50) / 10
        # Sigmoid
        return 1 / (1 + np.exp(-normalized))
    
    def _generate_detailed_explanation(
        self, 
        components: Dict, 
        features: Dict,
        probability: float,
        confidence: float
    ) -> Dict:
        """Generate detailed prediction explanation."""
        
        # Identify key positive factors
        key_factors = []
        
        # Form analysis
        if features.get('recent_win_rate', 0) > 0.3:
            key_factors.append({
                'factor': 'Recent Winning Form',
                'value': f"{features['recent_win_rate']*100:.0f}% win rate last 5 starts",
                'impact': 'Strong',
                'direction': 'positive'
            })
        
        if features.get('form_trend', 0) < -1:
            key_factors.append({
                'factor': 'Improving Form',
                'value': f"Trending {abs(features['form_trend']):.1f} positions better",
                'impact': 'Moderate',
                'direction': 'positive'
            })
        
        # Track/distance
        if features.get('track_favorite', 0):
            key_factors.append({
                'factor': 'Track Specialist',
                'value': f"{features.get('track_win_rate', 0)*100:.0f}% win rate at {features.get('track', 'track')}",
                'impact': 'Strong',
                'direction': 'positive'
            })
        
        if features.get('distance_specialist', 0):
            key_factors.append({
                'factor': 'Distance Specialist',
                'value': f"Proven at {features.get('distance', 'distance')}",
                'impact': 'Moderate',
                'direction': 'positive'
            })
        
        # Human factors
        if features.get('jt_synergy', 0) > 0.05:
            key_factors.append({
                'factor': 'Jockey-Trainer Synergy',
                'value': f"{features.get('jt_combo_win_rate', 0)*100:.0f}% win rate together",
                'impact': 'Moderate',
                'direction': 'positive'
            })
        
        jockey_score = features.get('jockey_score', 50)
        if jockey_score > 75:
            key_factors.append({
                'factor': 'Top Jockey',
                'value': f"{features.get('jockey', 'Jockey')} (score: {jockey_score:.0f})",
                'impact': 'Moderate',
                'direction': 'positive'
            })
        
        # Market
        if features.get('is_favorite', 0):
            key_factors.append({
                'factor': 'Market Favorite',
                'value': f"Odds: {features.get('current_odds', 0):.1f}",
                'impact': 'Strong',
                'direction': 'positive'
            })
        
        if features.get('market_support', 0) > 10:
            key_factors.append({
                'factor': 'Market Support',
                'value': f"Odds shortening ({features['market_support']:.0f}% improvement)",
                'impact': 'Moderate',
                'direction': 'positive'
            })
        
        # Health/Preparation
        if features.get('trial_win', 0):
            key_factors.append({
                'factor': 'Recent Trial Win',
                'value': "Won latest barrier trial",
                'impact': 'Moderate',
                'direction': 'positive'
            })
        
        # Identify risk factors
        risk_factors = []
        
        if features.get('first_up_flag', 0):
            risk_factors.append({
                'factor': 'First-Up',
                'description': f"{features.get('days_since_last_race', 0):.0f} days since last run",
                'severity': 'Medium'
            })
        
        if features.get('vet_concerns', 0) > 0:
            risk_factors.append({
                'factor': 'Veterinary Concerns',
                'description': "Recent veterinary attention noted",
                'severity': 'High'
            })
        
        if features.get('injury_history', 0):
            risk_factors.append({
                'factor': 'Injury History',
                'description': f"{features.get('injury_count', 0):.0f} previous injuries",
                'severity': 'Medium'
            })
        
        if features.get('is_heavy_weight', 0):
            risk_factors.append({
                'factor': 'Heavy Weight',
                'description': f"Carrying {features.get('weight', 0):.0f}lbs",
                'severity': 'Low'
            })
        
        if features.get('outside_draw', 0):
            risk_factors.append({
                'factor': 'Wide Draw',
                'description': f"Barrier {features.get('draw', 0):.0f}",
                'severity': 'Low'
            })
        
        if features.get('form_trend', 0) > 1.5:
            risk_factors.append({
                'factor': 'Declining Form',
                'description': f"Trending worse by {features['form_trend']:.1f} positions",
                'severity': 'Medium'
            })
        
        # Generate recommendation
        if probability > 0.25 and confidence > 0.7 and len(risk_factors) < 2:
            recommendation = 'STRONG CONTENDER - Clear winning chance'
        elif probability > 0.18 and len(risk_factors) < 3:
            recommendation = 'PLACE CHANCE - Good each-way prospect'
        elif probability > 0.12:
            recommendation = 'ROUGHIE - Small place chance'
        else:
            recommendation = 'OUTSIDER - Unlikely to figure'
        
        # Determine why this probability was assigned
        top_components = sorted(
            components.items(),
            key=lambda x: x[1]['score'],
            reverse=True
        )[:2]
        
        why_predicted = f"Predicted at {probability*100:.1f}% based on: "
        why_parts = []
        
        for name, comp in top_components:
            if comp['score'] > 65:
                why_parts.append(f"strong {name} ({comp['score']:.0f}/100)")
            elif comp['score'] > 50:
                why_parts.append(f"solid {name} ({comp['score']:.0f}/100)")
        
        if why_parts:
            why_predicted += ", ".join(why_parts)
        else:
            why_predicted += "average performance across all factors"
        
        return {
            'key_factors': key_factors,
            'risk_factors': risk_factors,
            'risk_assessment': 'Low' if len(risk_factors) == 0 else ('Medium' if len(risk_factors) < 3 else 'High'),
            'recommendation': recommendation,
            'why_predicted': why_predicted,
            'component_breakdown': {
                name: {
                    'score': comp['score'],
                    'probability': comp['probability'],
                    'contribution': comp['probability'] * comp['weight']
                }
                for name, comp in components.items()
            }
        }
    
    def _fallback_prediction(self, horse_name: str) -> Dict:
        """Fallback prediction when data is insufficient."""
        return {
            'horse_name': horse_name,
            'win_probability': 0.05,
            'place_probability': 0.15,
            'raw_probability': 0.05,
            'confidence': 0.20,
            'components': {},
            'explanation': {
                'key_factors': [],
                'risk_factors': [{'factor': 'Insufficient Data', 'description': 'Limited information available', 'severity': 'High'}],
                'risk_assessment': 'High',
                'recommendation': 'INSUFFICIENT DATA - Cannot assess chances',
                'why_predicted': 'Base rate probability due to data limitations'
            },
            'key_factors': [],
            'risk_assessment': 'High',
            'recommendation': 'INSUFFICIENT DATA'
        }
    
    def predict_batch(self, features_list: List[Dict]) -> List[Dict]:
        """Predict probabilities for multiple horses."""
        predictions = []
        
        for features in features_list:
            try:
                result = self.predict_with_explanation(features)
                predictions.append(result)
            except Exception as e:
                logger.error(f"Batch prediction error: {e}")
                predictions.append(self._fallback_prediction(
                    features.get('horse_name', 'Unknown')
                ))
        
        return predictions
    
    def calibrate_batch(self, predictions: List[Dict]) -> List[Dict]:
        """Apply batch calibration to ensure probabilities sum reasonably."""
        if not predictions:
            return predictions
        
        # Extract win probabilities
        win_probs = [p['win_probability'] for p in predictions]
        total = sum(win_probs)
        
        if total == 0:
            return predictions
        
        # Normalize to ensure sum is reasonable (typically 0.8-1.2 for realistic races)
        # but don't over-normalize
        target_sum = min(1.0, max(0.7, total * 0.9))
        
        if total > 1.3:
            # Compress probabilities
            scale = target_sum / total
            for pred in predictions:
                pred['win_probability'] *= scale
        
        return predictions
