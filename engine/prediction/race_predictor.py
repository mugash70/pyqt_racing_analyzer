"""Main race prediction engine."""

from typing import Dict, List, Optional, Callable
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
import pickle
import os
import numpy as np


class RacePredictor:
    """Main race prediction engine."""
    
    def __init__(self, db_path: str):
        """Initialize race predictor with database connection."""
        self.data = DataIntegrator(db_path)
        self.universal = UniversalCapability(self.data)
        self.track_analyzer = TrackAnalyzer(self.data)
        self.risk_assessor = RiskAssessor(self.data)
        self.feature_factory = FeatureFactory(self.data)
        self.ensemble = EnsembleModel()
        self.odds_monitor = OddsMonitor(self.data)
        self.real_time_callbacks = []
        
        self.form_analyzer = ImprovedFormAnalyzer(self.data)
        self.feature_interactions = FeatureInteractionOptimizer(self.data)
        self.confidence_scorer = ConfidenceScorer()
        self.probability_calibrator = ProbabilityCalibrator()
        self.professional_calibrator = self._load_professional_calibrator()
    
    def _load_professional_calibrator(self):
        """Load professional calibrator or create default."""
        # Use simple default calibrator to avoid pickle issues
        return self._create_default_calibrator()
    
    def _create_default_calibrator(self):
        """Create default professional calibrator."""
        class DefaultCalibrator:
            def __init__(self):
                self.method = 'power_law'
                self.params = {'exponent': 0.75}
            
            def calibrate(self, raw_probs, market_odds=None):
                # Power law calibration
                calibrated = [p ** self.params['exponent'] for p in raw_probs]
                total = sum(calibrated)
                return [c / total for c in calibrated] if total > 0 else raw_probs
        
        return DefaultCalibrator()
    
    @staticmethod
    def _normalize_date(date_str: str) -> str:
        """Normalize date by removing timestamp for database queries."""
        if isinstance(date_str, str):
            if ' ' in date_str:
                date_str = date_str.split(' ')[0]
            return date_str
        return date_str
    
    def predict_race(self, race_date: str, race_number: int, track: str) -> Dict:
        """
        Predict a complete race with strict data validation.
        """
        normalized_date = self._normalize_date(race_date)
        try:
            race_info = self.data.get_race_info(normalized_date, race_number, track)
            field = self.data.get_field_horses(normalized_date, race_number, track)
            odds = self.data.get_live_odds(normalized_date, race_number, track)

        except ValueError as e:
            return {
                'error': str(e),
                'race_date': race_date,
                'race_number': race_number,
                'track': track
            }

        # Handle potential duplicates in field data
        unique_field = {}
        for horse in field:
            h_num = horse['number']
            if h_num not in unique_field:
                unique_field[h_num] = horse
        
        field = list(unique_field.values())
        field_size = len(field)
        odds_dict = {str(o['number']): o for o in odds}
        
        # Collect all raw probabilities for batch calibration
        raw_probabilities = []
        predictions = []
        
        for horse in field:
            horse_num = str(horse['number'])
            horse_odds = odds_dict.get(horse_num, {})
            current_odds = horse_odds.get('win_odds')
            
            # Note: For future races, we don't have odds, so we still predict them
            if current_odds is not None and (current_odds <= 0 or current_odds < 1.5):
                print(f"    Skipping {horse['name']}: Invalid odds {current_odds}")
                continue
                
            distance = race_info.get('distance')
            race_class = race_info.get('class')
            
            comprehensive_features = self.feature_factory.extract_all_features(
                horse_name=horse['name'],
                horse_number=horse['number'],
                jockey=horse.get('jockey', ''),
                trainer=horse.get('trainer', ''),
                weight=horse.get('weight', ''),
                draw=horse['draw'] or 0,
                race_date=race_date,
                race_number=race_number,
                track=track,
                distance=distance,
                race_class=race_class,
                current_odds=current_odds,
                field_size=field_size
            )
            
            universal_score = self.universal.get_overall_capability_score(horse['name'], horse.get('jockey', ''), horse.get('trainer', ''))
            track_score = self.track_analyzer.get_track_specialized_score(horse['name'], track, horse.get('jockey', ''), horse.get('trainer', ''))
            
            comprehensive_features['universal_score'] = float(universal_score)
            comprehensive_features['track_score'] = float(track_score)
            
            try:
                result = self.ensemble.predict_probability(comprehensive_features)
                win_prob = result['probability']
                contributions = result['contributions']
                
                # Model-style probabilities for confidence calculation
                xgb_prob = self.ensemble.predict_xgboost_style(comprehensive_features)
                nn_prob = self.ensemble.predict_neural_net_style(comprehensive_features)
                place_prob = self.ensemble.predict_place_probability(comprehensive_features)
            except ValueError:
                continue
            
            risk_profile = self.risk_assessor.create_risk_profile(
                horse['name'], race_date, track, 
                distance,
                horse.get('draw') or 0,
                horse.get('weight', '')
            )
            
            form_analysis = self.form_analyzer.combined_form_analysis(horse['name'], horse.get('jockey', ''), horse.get('trainer', ''))
            interaction_adjustments = self.feature_interactions.calculate_interaction_adjustments(
                horse['name'], horse.get('jockey', ''), horse.get('trainer', ''),
                track, distance, race_class, horse.get('draw') or 0, field_size
            )
            
            adjusted_win_prob = win_prob * interaction_adjustments['combined_multiplier']
            
            # Re-normalize contributions based on adjusted probability
            for key in contributions:
                contributions[key] *= interaction_adjustments['combined_multiplier']
                
            combined_confidence = self.confidence_scorer.calculate_combined_confidence(
                self.confidence_scorer.calculate_ensemble_confidence(xgb_prob, nn_prob, adjusted_win_prob),
                self.confidence_scorer.calculate_feature_alignment_confidence({
                    'universal_score': universal_score / 100,
                    'track_score': track_score / 100,
                    'form_score': form_analysis['combined_form_score'] / 100,
                    'interaction_strength': interaction_adjustments['combined_multiplier']
                }),
                self.confidence_scorer.calculate_prediction_stability_confidence(adjusted_win_prob, [xgb_prob, nn_prob]),
                self.confidence_scorer.calculate_historical_accuracy_confidence(horse['name'])
            )
            
            raw_probabilities.append(adjusted_win_prob)
            
            # Handle current_odds being None for future races
            if current_odds is not None and current_odds > 0:
                current_odds_val = float(current_odds)
            else:
                current_odds_val = None
            
            prediction = {
                'horse_number': horse['number'],
                'horse_name': horse['name'],
                'jockey': horse.get('jockey', ''),
                'trainer': horse.get('trainer', ''),
                'weight': horse.get('weight', ''),
                'draw': horse.get('draw', 0),
                'raw_probability': float(adjusted_win_prob),
                'place_probability': float(place_prob),
                'confidence': float(combined_confidence),
                'current_odds': current_odds_val,
                'risk_score': float(risk_profile['overall_risk_score']),
                'risk_recommendation': risk_profile['recommendation'],
                'mathematical_explanation': {
                    'base_factors': {k: float(v) for k, v in contributions.items()},
                    'interaction_multiplier': float(interaction_adjustments['combined_multiplier']),
                    'raw_probability': float(adjusted_win_prob)
                }
            }
            predictions.append(prediction)
        
        if not predictions:
            return {
                'error': f"No horses could be predicted for race {race_number} on {normalized_date} due to data gaps.",
                'race_date': race_date,
                'race_number': race_number,
                'track': track
            }

        # Apply professional calibration to all probabilities at once
        if raw_probabilities:
            calibrated_probs = self.professional_calibrator.calibrate(raw_probabilities)
            
            # Update predictions with calibrated probabilities and calculate values
            for pred, cal_prob in zip(predictions, calibrated_probs):
                pred['win_probability'] = float(cal_prob * 100)  # Convert to percentage
                
                # Calculate value using calibrated probability only if odds are available
                if pred['current_odds'] is not None and pred['current_odds'] > 0:
                    implied_prob = 1.0 / pred['current_odds']
                    value_ratio = ((implied_prob - cal_prob) / cal_prob)
                    pred['value_pct'] = float(value_ratio * 100)
                else:
                    pred['value_pct'] = None  # No odds available for future races
                
                # Update mathematical explanation
                pred['mathematical_explanation']['calibrated_prob'] = float(cal_prob)
                pred['mathematical_explanation']['calibration_reduction'] = float((pred['raw_probability'] - cal_prob) / pred['raw_probability'] * 100) if pred['raw_probability'] > 0 else 0
                pred['mathematical_explanation']['final_calibrated_prob'] = float(cal_prob)

        # Probabilities are already normalized by professional calibrator
        # Just ensure they sum to exactly 100%
        win_prob_sum = sum(p['win_probability'] for p in predictions)
        if abs(win_prob_sum - 100.0) > 0.1:  # Small adjustment if needed
            scale_factor = 100.0 / win_prob_sum
            for p in predictions:
                p['win_probability'] *= scale_factor
                # Recalculate value with adjusted probability only if odds are available
                if p.get('current_odds', 0) > 0:
                    implied_prob = 1.0 / p['current_odds']
                    model_prob = p['win_probability'] / 100.0
                    p['value_pct'] = float(((implied_prob - model_prob) / model_prob) * 100)

        # Normalize place probabilities to sum to 300% (3 places)
        place_prob_sum = sum(p['place_probability'] for p in predictions)
        if place_prob_sum > 0:
            for p in predictions:
                normalized_place = (p["place_probability"] / place_prob_sum) * 3.0
                p["place_probability"] = float(normalized_place * 100)  # Convert to percentage

        predictions.sort(key=lambda x: x['win_probability'], reverse=True)
        
        return {
            'race_info': {
                'date': race_date,
                'number': race_number,
                'track': track,
                'distance': race_info.get('distance'),
                'class': race_info.get('class'),
                'going': race_info.get('going')
            },
            'field_size': len(field),
            'predictions': predictions,
            'analysis': self._generate_race_analysis(predictions, race_info, race_number, track)
        }
    
    def _generate_race_analysis(self, predictions: List[Dict], race_info: Dict, race_number: int = None, track: str = None) -> str:
        """Generate a human-readable analysis of the race."""
        if not predictions:
            return "Insufficient data for analysis."
        
        # Sort by win probability for analysis
        sorted_preds = sorted(predictions, key=lambda x: x['win_probability'], reverse=True)
        top_pick = sorted_preds[0]
        
        race_num = race_info.get('number', race_number or 'Unknown')
        track_name = race_info.get('track', track or 'Unknown')
        
        analysis = []
        analysis.append(f"Race Analysis for Race {race_num} at {track_name}:")
        
        # Top selection
        analysis.append(f"Primary Selection: {top_pick['horse_name']} (#{top_pick['horse_number']})")
        analysis.append(f"- Win Probability: {top_pick['win_probability']:.1f}%")
        analysis.append(f"- Confidence Score: {top_pick['confidence'] * 100:.1f}%")
        
        # Key factors for top pick
        top_factors = []
        if top_pick['win_probability'] > 25:
            top_factors.append("Strong win probability")
        if top_pick['confidence'] > 0.7:
            top_factors.append("High confidence prediction")
        if top_pick.get('value_pct') is not None and top_pick['value_pct'] > 10:
            top_factors.append("Positive value bet")
        
        # Check mathematical explanation for interaction multiplier
        math_exp = top_pick.get('mathematical_explanation', {})
        interaction_mult = math_exp.get('interaction_multiplier', 1.0)
        if interaction_mult > 1.1:
            top_factors.append(f"Strong factor synergy ({interaction_mult:.2f}x)")
            
        if top_factors:
            analysis.append(f"- Key Strengths: {', '.join(top_factors)}")
            
        # Add a note about risk if it's moderate or high
        if top_pick['risk_score'] > 40:
            analysis.append(f"- Risk Assessment: {top_pick['risk_recommendation']}")
            
        # Value Picks - only show if odds are available
        value_picks = [p for p in predictions if p.get('value_pct') is not None and p.get('value_pct', 0) > 10]
        if value_picks:
            analysis.append("\nPotential Value Picks:")
            for vp in value_picks[:2]:
                analysis.append(f"- {vp['horse_name']} (#{vp['horse_number']}): {vp['value_pct']:.1f}% value at odds {vp.get('current_odds', 'N/A')}")
        
        # Risk assessment
        high_risk = [p for p in predictions[:3] if p['risk_score'] > 60]
        if high_risk:
            analysis.append("\nRisk Warnings:")
            for hr in high_risk:
                analysis.append(f"- {hr['horse_name']}: {hr['risk_recommendation']}")
        
        return "\n".join(analysis)
    
    def predict_multiple_races(self, race_date: str, track: str) -> List[Dict]:
        """Predict all races for a given date and track (usually 1-11)."""
        normalized_date = self._normalize_date(race_date)
        
        print(f"[Predictor] Starting full card prediction for {normalized_date} at {track}")
        
        predictions = []
        for race_num in range(1, 13):  # HK races are usually 1-10 or 1-11, sometimes 12
            race_pred = self.predict_race(normalized_date, race_num, track)
            
            # If we get an error, check if it's end of card or data issue
            if 'error' in race_pred:
                if 'No field data' in race_pred['error'] or 'No horses could be predicted' in race_pred['error'] or 'No race info found' in race_pred['error']:
                    if race_num > 8:  # End of card after race 8+
                        print(f"[Predictor] Card ended after race {race_num-1}")
                        break
                    else:
                        print(f"[Predictor] Warning: No data for race {race_num}, continuing...")
                continue
                
            predictions.append(race_pred)
        
        print(f"[Predictor] Completed {len(predictions)} race predictions")
        return predictions

    def register_real_time_callback(self, callback: Callable):
        """Register a callback for real-time odds updates."""
        self.real_time_callbacks.append(callback)
        
    def start_real_time_monitoring(self, race_date: str, race_number: int, track: str):
        """Start background monitoring of live odds."""
        def monitor_task():
            self.odds_monitor.start_monitoring(
                race_date, race_number, track,
                callback=self._handle_odds_update
            )
            
        self.monitor_thread = threading.Thread(target=monitor_task, daemon=True)
        self.monitor_thread.start()
        
    def stop_real_time_monitoring(self):
        """Stop real-time monitoring."""
        self.odds_monitor.stop_monitoring()
        
    def _handle_odds_update(self, odds_data: List[Dict]):
        """Handle new odds data and trigger re-prediction."""
        # Get context from odds monitor or state
        # For simplicity, we trigger callbacks with the new odds
        for callback in self.real_time_callbacks:
            callback(odds_data)
