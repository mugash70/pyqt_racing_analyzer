"""
Enhanced Race Predictor - Improved prediction engine with detailed reasoning.
Features:
- Better probability calibration
- Detailed prediction reasons for each horse
- Confidence scoring improvements
- Feature importance explanations
"""

from typing import Dict, List, Optional, Tuple
import threading
import time
from ..core.data_integrator import DataIntegrator
from ..core.universal_capability import UniversalCapability
from ..core.track_analyzer import TrackAnalyzer
from ..core.risk_assessor import RiskAssessor
from ..features.feature_factory import FeatureFactory
from ..features.form_analyzer_improved import ImprovedFormAnalyzer
from ..features.feature_interactions import FeatureInteractionOptimizer
from ..models.ensemble_model import EnsembleModel
from ..models.probability_calibration import ProbabilityCalibrator
from ..live.odds_monitor import OddsMonitor
from ..prediction.confidence_scorer import ConfidenceScorer
import numpy as np


class EnhancedRacePredictor:
    """Enhanced race predictor with detailed reasoning and improved calibration."""
    
    def __init__(self, db_path: str):
        """Initialize enhanced predictor."""
        self.data = DataIntegrator(db_path)
        self.universal = UniversalCapability(self.data)
        self.track_analyzer = TrackAnalyzer(self.data)
        self.risk_assessor = RiskAssessor(self.data)
        self.feature_factory = FeatureFactory(self.data)
        self.ensemble = EnsembleModel()
        self.odds_monitor = OddsMonitor(self.data)
        
        self.form_analyzer = ImprovedFormAnalyzer(self.data)
        self.feature_interactions = FeatureInteractionOptimizer(self.data)
        self.confidence_scorer = ConfidenceScorer()
        self.probability_calibrator = ProbabilityCalibrator()
        
        self._init_calibrator()
    
    def _init_calibrator(self):
        """Initialize probability calibrator."""
        try:
            # Try to load trained calibrator
            self.calibrator = self.probability_calibrator.load('calibrator.pkl')
        except:
            # Use default power law calibration
            self.calibrator = self._create_default_calibrator()
    
    def _create_default_calibrator(self):
        """Create default calibrator with power law."""
        class DefaultCalibrator:
            def __init__(self):
                self.method = 'power_law'
                self.params = {'exponent': 0.85}  # Slightly less aggressive
            
            def calibrate(self, raw_probs, market_odds=None):
                if not raw_probs:
                    return raw_probs
                
                # Apply power law transformation
                calibrated = [p ** self.params['exponent'] for p in raw_probs]
                
                # Normalize to sum to 1
                total = sum(calibrated)
                if total > 0:
                    calibrated = [c / total for c in calibrated]
                
                return calibrated
            
            def predict(self, features: Dict) -> Dict:
                """Predict win probability with calibration."""
                # Get base probability from features
                base_prob = self._calculate_base_probability(features)
                
                # Apply calibration
                calibrated_prob = base_prob ** self.params['exponent']
                
                return {
                    'win_probability': calibrated_prob,
                    'raw_probability': base_prob
                }
            
            def _calculate_base_probability(self, features: Dict) -> float:
                """Calculate base probability from features."""
                factors = []
                
                # Market odds (strongest signal)
                odds = features.get('current_odds')
                if odds and odds > 0:
                    implied = 1.0 / odds
                    factors.append(('market', implied, 0.35))
                
                # Form (check both naming conventions)
                form = features.get('last_5_avg_position') or features.get('last_5_avg')
                if form and form > 0:
                    # Convert if needed (score 0-100 to position 1-14)
                    if form > 20:
                        form = max(1, min(14, 14 - (form / 100 * 14)))
                    form_prob = max(0.05, 1.0 - (form * 0.1))
                    factors.append(('form', form_prob, 0.25))
                
                # Track score
                track_score = features.get('track_score')
                if track_score is not None:
                    factors.append(('track', track_score / 100, 0.15))
                
                # Universal capability
                univ_score = features.get('universal_score')
                if univ_score is not None:
                    factors.append(('capability', univ_score / 100, 0.15))
                
                # Jockey
                jockey_rate = features.get('jockey_win_rate')
                if jockey_rate is not None:
                    factors.append(('jockey', jockey_rate / 100, 0.05))
                
                # Trainer
                trainer_rate = features.get('trainer_win_rate')
                if trainer_rate is not None:
                    factors.append(('trainer', trainer_rate / 100, 0.05))
                
                if not factors:
                    return 0.1
                
                total_weight = sum(w for _, _, w in factors)
                prob = sum(f * (w / total_weight) for f, _, w in factors)
                
                return max(0.01, min(0.99, prob))
        
        return DefaultCalibrator()
    
    @staticmethod
    def _normalize_date(date_str: str) -> str:
        """Normalize date by removing timestamp."""
        if isinstance(date_str, str) and ' ' in date_str:
            return date_str.split(' ')[0]
        return date_str
    
    def predict_race(self, race_date: str, race_number: int, track: str) -> Dict:
        """
        Generate comprehensive race predictions with detailed reasoning.
        """
        normalized_date = self._normalize_date(race_date)
        
        try:
            race_info = self.data.get_race_info(normalized_date, race_number, track)
            field = self.data.get_field_horses(normalized_date, race_number, track)
            odds = self.data.get_live_odds(normalized_date, race_number, track)
        except ValueError as e:
            return {'error': str(e), 'race_date': race_date, 'race_number': race_number, 'track': track}
        
        # Remove duplicates
        unique_field = {h['number']: h for h in field}
        field = list(unique_field.values())
        field_size = len(field)
        
        if field_size == 0:
            return {
                'error': f"No horses in field data for race {race_number}",
                'race_date': race_date, 'race_number': race_number, 'track': track
            }
        
        # Build odds lookup
        odds_dict = {str(o['number']): o for o in odds}
        
        # Collect all raw probabilities for batch calibration
        raw_predictions = []
        failed_horses = []
        
        for horse in field:
            horse_num = str(horse['number'])
            horse_name = horse.get('name', 'Unknown')
            horse_odds = odds_dict.get(horse_num, {})
            current_odds = horse_odds.get('win_odds')
            
            # Skip if invalid odds (except for future races where odds = None)
            if current_odds is not None and current_odds <= 0:
                continue
            
            prediction = self._predict_single_horse(
                horse, race_info, current_odds, field_size
            )
            if prediction:
                raw_predictions.append(prediction)
            else:
                failed_horses.append(horse_name)
        
        if not raw_predictions:
            return {
                'error': f"No horses could be predicted for race {race_number}",
                'race_date': race_date, 'race_number': race_number, 'track': track,
                'debug_info': {
                    'field_size': field_size,
                    'failed_horses': failed_horses
                }
            }
        
        # Apply calibration
        raw_probs = [p['raw_win_prob'] for p in raw_predictions]
        calibrated_probs = self.calibrator.calibrate(raw_probs)
        
        # Update predictions with calibrated probabilities
        for pred, cal_prob in zip(raw_predictions, calibrated_probs):
            pred['win_probability'] = cal_prob
            pred['calibrated_prob'] = cal_prob
            
            # Calculate value if odds available
            if pred.get('current_odds') and pred['current_odds'] > 0:
                implied = 1.0 / pred['current_odds']
                pred['value_pct'] = ((implied - cal_prob) / cal_prob) * 100
            else:
                pred['value_pct'] = None
        
        # Re-normalize to sum to 100%
        prob_sum = sum(p['win_probability'] for p in raw_predictions)
        if prob_sum > 0:
            for p in raw_predictions:
                p['win_probability'] = (p['win_probability'] / prob_sum) * 100
        
        # Sort by win probability
        raw_predictions.sort(key=lambda x: x['win_probability'], reverse=True)
        
        # Generate detailed reasons for each horse
        for i, pred in enumerate(raw_predictions):
            pred['predicted_rank'] = i + 1
            pred['detailed_reasons'] = self._generate_detailed_reasons(pred, race_info)
        
        return {
            'race_info': {
                'date': race_date,
                'number': race_number,
                'track': track,
                'distance': race_info.get('distance'),
                'class': race_info.get('class'),
                'going': race_info.get('going')
            },
            'field_size': field_size,
            'predictions': raw_predictions,
            'analysis': self._generate_race_analysis(raw_predictions, race_info),
            'model_info': {
                'version': 'enhanced_v2.0',
                'calibration': 'power_law',
                'features_used': self._count_features()
            }
        }
    
    def _predict_single_horse(self, horse: Dict, race_info: Dict, 
                             current_odds: float, field_size: int) -> Optional[Dict]:
        """Generate prediction for a single horse."""
        try:
            distance = race_info.get('distance')
            race_class = race_info.get('class')
            horse_name = horse.get('name', 'Unknown')
            
            # Extract features
            features = self.feature_factory.extract_all_features(
                horse_name=horse['name'],
                horse_number=horse['number'],
                jockey=horse.get('jockey', ''),
                trainer=horse.get('trainer', ''),
                weight=horse.get('weight', ''),
                draw=horse['draw'] or 0,
                race_date=race_info.get('date', ''),
                race_number=race_info.get('number', 0),
                track=race_info.get('track', ''),
                distance=distance,
                race_class=race_class,
                current_odds=current_odds,
                field_size=field_size
            )
            
            # Get capability scores
            universal_score = self.universal.get_overall_capability_score(
                horse['name'], horse.get('jockey', ''), horse.get('trainer', '')
            )
            track_score = self.track_analyzer.get_track_specialized_score(
                horse['name'], race_info.get('track', ''), 
                horse.get('jockey', ''), horse.get('trainer', '')
            )
            
            features['universal_score'] = float(universal_score)
            features['track_score'] = float(track_score)
            
            # Get ensemble prediction
            try:
                result = self.ensemble.predict_probability(features)
                win_prob = result['probability']
                contributions = result.get('contributions', {})
            except ValueError as ve:
                cal_result = self.calibrator.predict(features)
                win_prob = cal_result['win_probability']
                contributions = {'fallback': win_prob}
            
            # Get place probability
            place_prob = self.ensemble.predict_place_probability(features)
            
            # Risk assessment
            risk_profile = self.risk_assessor.create_risk_profile(
                horse['name'], race_info.get('date', ''), race_info.get('track', ''),
                distance, horse.get('draw') or 0, horse.get('weight', '')
            )
            
            # Form analysis
            form_analysis = self.form_analyzer.combined_form_analysis(
                horse['name'], horse.get('jockey', ''), horse.get('trainer', '')
            )
            
            # Interaction adjustments
            interaction_adjustments = self.feature_interactions.calculate_interaction_adjustments(
                horse['name'], horse.get('jockey', ''), horse.get('trainer', ''),
                race_info.get('track', ''), distance, race_class, 
                horse.get('draw') or 0, field_size
            )
            
            # Calculate confidence
            try:
                xgb_prob = self.ensemble.predict_xgboost_style(features)
                nn_prob = self.ensemble.predict_neural_net_style(features)
                
                combined_confidence = self.confidence_scorer.calculate_combined_confidence(
                    self.confidence_scorer.calculate_ensemble_confidence(xgb_prob, nn_prob, win_prob),
                    self.confidence_scorer.calculate_feature_alignment_confidence({
                        'universal_score': universal_score / 100,
                        'track_score': track_score / 100,
                        'form_score': form_analysis['combined_form_score'] / 100,
                        'interaction_strength': interaction_adjustments['combined_multiplier']
                    }),
                    self.confidence_scorer.calculate_prediction_stability_confidence(win_prob, [xgb_prob, nn_prob]),
                    self.confidence_scorer.calculate_historical_accuracy_confidence(horse['name'])
                )
            except Exception as ce:
                combined_confidence = 0.5
            
            # Build prediction dict
            prediction = {
                'horse_number': horse['number'],
                'horse_name': horse['name'],
                'jockey': horse.get('jockey', ''),
                'trainer': horse.get('trainer', ''),
                'weight': horse.get('weight', ''),
                'draw': horse.get('draw', 0),
                'raw_win_prob': win_prob,
                'win_probability': win_prob * 100,  # Will be updated with calibrated value
                'place_probability': place_prob * 100,
                'confidence': combined_confidence,
                'current_odds': current_odds,
                'risk_score': float(risk_profile['overall_risk_score']),
                'risk_recommendation': risk_profile['recommendation'],
                'form_score': form_analysis['combined_form_score'],
                'interaction_multiplier': interaction_adjustments['combined_multiplier'],
                'contributions': {k: float(v) for k, v in contributions.items()}
            }
            
            return prediction
            
        except Exception as e:
            import traceback
            print(f"[DEBUG] Error predicting horse {horse.get('name', 'Unknown')}: {e}")
            print(f"[DEBUG] Traceback: {traceback.format_exc()}")
            return None
    
    def _generate_detailed_reasons(self, prediction: Dict, race_info: Dict) -> Dict:
        """Generate detailed reasoning for why a horse is predicted."""
        reasons = {
            'positive_factors': [],
            'negative_factors': [],
            'key_statistics': [],
            'prediction_summary': ''
        }
        
        # Win probability factor
        win_prob = prediction.get('win_probability', 0)
        if win_prob > 30:
            reasons['positive_factors'].append(f"High win probability: {win_prob:.1f}%")
        elif win_prob > 15:
            reasons['positive_factors'].append(f"Moderate win probability: {win_prob:.1f}%")
        
        # Confidence factor
        confidence = prediction.get('confidence', 0)
        if confidence > 0.8:
            reasons['positive_factors'].append(f"High prediction confidence: {confidence:.0%}")
        elif confidence < 0.5:
            reasons['negative_factors'].append(f"Lower confidence: {confidence:.0%}")
        
        # Draw position
        draw = prediction.get('draw', 0)
        if draw <= 3:
            reasons['positive_factors'].append(f"Favorable inside draw (Gate {draw})")
        elif draw >= 10:
            reasons['negative_factors'].append(f"Challenging wide draw (Gate {draw})")
        
        # Jockey
        jockey = prediction.get('jockey', '')
        if jockey:
            reasons['key_statistics'].append(f"Jockey: {jockey}")
        
        # Trainer
        trainer = prediction.get('trainer', '')
        if trainer:
            reasons['key_statistics'].append(f"Trainer: {trainer}")
        
        # Weight
        weight = prediction.get('weight', '')
        if weight:
            reasons['key_statistics'].append(f"Weight: {weight}")
        
        # Form score
        form_score = prediction.get('form_score', 0)
        if form_score > 70:
            reasons['positive_factors'].append(f"Strong recent form: {form_score:.0f}%")
        elif form_score < 40:
            reasons['negative_factors'].append(f"Weak recent form: {form_score:.0f}%")
        
        # Interaction multiplier
        interaction = prediction.get('interaction_multiplier', 1)
        if interaction > 1.2:
            reasons['positive_factors'].append(f"Strong factor synergy: {interaction:.2f}x")
        elif interaction < 0.8:
            reasons['negative_factors'].append(f"Weak factor synergy: {interaction:.2f}x")
        
        # Risk score
        risk = prediction.get('risk_score', 0)
        if risk > 60:
            reasons['negative_factors'].append(f"Higher risk profile: {risk:.0f}/100")
        elif risk < 30:
            reasons['positive_factors'].append(f"Low risk profile: {risk:.0f}/100")
        
        # Value
        value = prediction.get('value_pct', None)
        if value is not None:
            if value > 20:
                reasons['positive_factors'].append(f"Strong value bet: +{value:.0f}%")
            elif value < -20:
                reasons['negative_factors'].append(f"Overvalued by model: {value:.0f}%")
        
        # Generate summary
        prob = prediction.get('win_probability', 0)
        conf = prediction.get('confidence', 0)
        
        if prob > 25 and conf > 0.7:
            summary = "Strong pick - High probability with good confidence"
        elif prob > 15 and conf > 0.5:
            summary = "Moderate pick - Decent probability with average confidence"
        elif prob > 10:
            summary = "Longshot - Lower probability but still competitive"
        else:
            summary = "Outsider - Low win probability expected"
        
        reasons['prediction_summary'] = summary
        
        return reasons
    
    def _generate_race_analysis(self, predictions: List[Dict], race_info: Dict) -> str:
        """Generate human-readable race analysis in Chinese."""
        if not predictions:
            return "數據不足以進行分析。"
        
        sorted_preds = sorted(predictions, key=lambda x: x['win_probability'], reverse=True)
        top_pick = sorted_preds[0]
        
        # Get race info with fallbacks for different key names
        race_num = race_info.get('number') or race_info.get('race_number') or '未知'
        track = race_info.get('track') or race_info.get('racecourse') or '未知'
        distance = race_info.get('distance') or race_info.get('race_distance', '')
        race_class = race_info.get('class') or race_info.get('race_class', '')
        
        analysis = []
        analysis.append(f"賽事分析 - 第{race_num}場 @ {track}")
        if distance:
            analysis.append(f"距離: {distance}")
        if race_class:
            analysis.append(f"班次: {race_class}")
        analysis.append("=" * 50)
        
        # Top selection
        analysis.append(f"\n 首選: {top_pick['horse_name']}")
        analysis.append(f"   勝出機率: {top_pick['win_probability']:.1f}%")
        analysis.append(f"   信心度: {top_pick['confidence']:.0%}")
        
        # Key factors
        if top_pick.get('detailed_reasons'):
            pos = top_pick['detailed_reasons'].get('positive_factors', [])
            if pos:
                analysis.append(f"   主要優勢:")
                for factor in pos[:3]:
                    analysis.append(f"     • {factor}")
        
        # Value picks
        value_picks = [p for p in predictions 
                      if p.get('value_pct') and p['value_pct'] > 10]
        if value_picks:
            analysis.append(f"\n💰 價值之選:")
            for vp in value_picks[:3]:
                analysis.append(f"   {vp['horse_name']}: +{vp['value_pct']:.0f}% 價值")
        
        # Risky picks
        risky = [p for p in predictions[:5] if p.get('risk_score', 0) > 60]
        if risky:
            analysis.append(f"\n 高風險:")
            for r in risky:
                analysis.append(f"   {r['horse_name']}: {r['risk_recommendation']}")
        
        return '\n'.join(analysis)
    
    def _count_features(self) -> int:
        """Count total features available."""
        try:
            # This would count from feature factory
            return 100  # Approximate
        except:
            return 50
    
    def predict_multiple_races(self, race_date: str, track: str) -> List[Dict]:
        """Predict all races for a given date and track."""
        normalized_date = self._normalize_date(race_date)
        
        predictions = []
        for race_num in range(1, 13):
            pred = self.predict_race(normalized_date, race_num, track)
            if 'error' not in pred:
                predictions.append(pred)
            elif race_num > 8:
                break
        
        return predictions


# Convenience function
def create_enhanced_predictor(db_path: str) -> EnhancedRacePredictor:
    """Create an enhanced predictor instance."""
    return EnhancedRacePredictor(db_path)
