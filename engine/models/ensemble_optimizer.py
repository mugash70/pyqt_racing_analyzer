"""Ensemble model weight optimization and retraining on recent data."""

from typing import Dict, List, Optional, Tuple, Any
import numpy as np
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class EnsembleWeightOptimizer:
    """Optimizes weights of ensemble models (XGBoost, Neural Network) for better performance."""
    
    def __init__(self, data_integrator: Any):
        """Initialize with data integrator."""
        if data_integrator is None:
            raise ValueError("Data integrator cannot be None")
        self.data = data_integrator
        self.xgboost_weight = 0.5
        self.neural_net_weight = 0.5
        self._validate_weights()
    
    def _validate_weights(self) -> None:
        """Validate that weights sum to 1.0."""
        total = self.xgboost_weight + self.neural_net_weight
        if not 0.99 <= total <= 1.01:
            raise ValueError(f"Weights must sum to 1.0, got {total}")
    
    def _validate_inputs(self, days_back: int) -> None:
        """Validate input parameters."""
        if not isinstance(days_back, int) or days_back <= 0:
            raise ValueError("days_back must be a positive integer")
        if days_back > 365:
            logger.warning(f"Large days_back value: {days_back}")
    
    def analyze_model_performance_by_period(
        self,
        days_back: int = 90
    ) -> Dict[str, Any]:
        """
        Analyze performance of each model component over recent period.
        
        Identifies which model is more accurate recently.
        """
        self._validate_inputs(days_back)
        
        try:
            cutoff_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
            recent_results = self.data.get_race_results_since(cutoff_date)
            
            if not recent_results:
                logger.warning(f"No race results found for last {days_back} days")
                return self._get_default_performance_result()
            
            xgb_correct = 0
            nn_correct = 0
            total = 0
            
            for result in recent_results:
                if not isinstance(result, dict):
                    continue
                    
                actual_position = result.get('position')
                
                if actual_position and isinstance(actual_position, int):
                    xgb_pred = result.get('xgboost_prediction')
                    nn_pred = result.get('neural_net_prediction')
                    
                    if xgb_pred == actual_position:
                        xgb_correct += 1
                    
                    if nn_pred == actual_position:
                        nn_correct += 1
                    
                    total += 1
            
            if total == 0:
                logger.warning("No valid predictions found in results")
                return self._get_default_performance_result()
            
            xgb_accuracy = xgb_correct / total
            nn_accuracy = nn_correct / total
            
            total_accuracy = xgb_accuracy + nn_accuracy
            
            if total_accuracy > 0:
                xgb_weight = xgb_accuracy / total_accuracy
                nn_weight = nn_accuracy / total_accuracy
            else:
                xgb_weight = 0.5
                nn_weight = 0.5
            
            return {
                'xgboost_accuracy': float(xgb_accuracy),
                'neural_net_accuracy': float(nn_accuracy),
                'recommended_weights': {
                    'xgboost': float(xgb_weight),
                    'neural_net': float(nn_weight)
                },
                'sample_size': total
            }
            
        except Exception as e:
            logger.error(f"Error analyzing model performance: {e}")
            return self._get_default_performance_result()
    
    def _get_default_performance_result(self) -> Dict[str, Any]:
        """Return default performance result when analysis fails."""
        return {
            'xgboost_accuracy': 0.5,
            'neural_net_accuracy': 0.5,
            'recommended_weights': {
                'xgboost': 0.5,
                'neural_net': 0.5
            },
            'sample_size': 0
        }
    
    def optimize_weights_by_class(self) -> Dict[str, Dict]:
        """
        Optimize ensemble weights separately for each race class.
        
        Some models may be better at predicting certain classes.
        """
        classes = ['Class 2', 'Class 3', 'Class 4', 'Class 5', 'Handicap']
        
        class_weights = {}
        
        for race_class in classes:
            results = self.data.get_race_results_by_class(race_class)
            
            if not results:
                class_weights[race_class] = {'xgboost': 0.5, 'neural_net': 0.5}
                continue
            
            xgb_correct = 0
            nn_correct = 0
            total = 0
            
            for result in results:
                actual_position = result.get('position')
                
                if actual_position:
                    xgb_pred = result.get('xgboost_prediction')
                    nn_pred = result.get('neural_net_prediction')
                    
                    if xgb_pred == actual_position:
                        xgb_correct += 1
                    
                    if nn_pred == actual_position:
                        nn_correct += 1
                    
                    total += 1
            
            if total == 0:
                class_weights[race_class] = {'xgboost': 0.5, 'neural_net': 0.5}
                continue
            
            xgb_accuracy = xgb_correct / total
            nn_accuracy = nn_correct / total
            
            total_accuracy = xgb_accuracy + nn_accuracy
            
            if total_accuracy > 0:
                xgb_weight = xgb_accuracy / total_accuracy
                nn_weight = nn_accuracy / total_accuracy
            else:
                xgb_weight = 0.5
                nn_weight = 0.5
            
            class_weights[race_class] = {
                'xgboost': float(xgb_weight),
                'neural_net': float(nn_weight)
            }
        
        return class_weights
    
    def apply_optimized_weights(
        self,
        xgboost_prediction: float,
        neural_net_prediction: float,
        optimization_period: str = 'recent'
    ) -> float:
        """
        Apply optimized weights to ensemble predictions.
        
        Args:
            xgboost_prediction: Probability from XGBoost model
            neural_net_prediction: Probability from Neural Network
            optimization_period: 'recent' or specific number of days
        
        Returns:
            Weighted ensemble prediction
        """
        # Input validation
        if not (0 <= xgboost_prediction <= 1):
            raise ValueError(f"XGBoost prediction must be between 0 and 1, got {xgboost_prediction}")
        if not (0 <= neural_net_prediction <= 1):
            raise ValueError(f"Neural net prediction must be between 0 and 1, got {neural_net_prediction}")
        
        try:
            perf_data = self.analyze_model_performance_by_period(days_back=90)
            weights = perf_data['recommended_weights']
            
            weighted_pred = (
                xgboost_prediction * weights['xgboost'] +
                neural_net_prediction * weights['neural_net']
            )
            
            # Ensure result is within valid range
            return float(max(0.0, min(1.0, weighted_pred)))
            
        except Exception as e:
            logger.error(f"Error applying optimized weights: {e}")
            # Fallback to equal weights
            return float((xgboost_prediction + neural_net_prediction) / 2)


class RecentDataRetrainer:
    """Retrains ensemble weights on recent data only (last 30-90 days)."""
    
    def __init__(self, data_integrator, model):
        """Initialize with data integrator and ensemble model."""
        self.data = data_integrator
        self.model = model
    
    def collect_recent_training_data(
        self,
        days_back: int = 90,
        min_sample_size: int = 50
    ) -> Dict:
        """
        Collect recent race data for retraining.
        
        Ensures sufficient sample size for reliable training.
        """
        cutoff_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
        
        recent_races = self.data.get_race_results_since(cutoff_date)
        
        if len(recent_races) < min_sample_size:
            return {
                'sufficient_data': False,
                'sample_size': len(recent_races),
                'required_size': min_sample_size,
                'message': f'Only {len(recent_races)} races available, need {min_sample_size}'
            }
        
        training_data = {
            'features': [],
            'labels': [],
            'metadata': []
        }
        
        for race in recent_races:
            race_features = self.data.extract_features_for_race(race)
            actual_winner = race.get('position') == 1
            
            training_data['features'].append(race_features)
            training_data['labels'].append(actual_winner)
            training_data['metadata'].append({
                'race_date': race.get('race_date'),
                'race_number': race.get('race_number'),
                'horse_name': race.get('horse_name')
            })
        
        return {
            'sufficient_data': True,
            'sample_size': len(training_data['features']),
            'data': training_data
        }
    
    def retrain_on_recent_data(
        self,
        days_back: int = 90
    ) -> Dict:
        """
        Retrain ensemble weights on recent data.
        
        Returns metrics on retraining performance and weight changes.
        """
        training_data_result = self.collect_recent_training_data(days_back=days_back)
        
        if not training_data_result['sufficient_data']:
            return {
                'success': False,
                'message': training_data_result['message']
            }
        
        training_data = training_data_result['data']
        
        try:
            old_weights = {
                'xgboost': self.model.xgboost_weight,
                'neural_net': self.model.neural_net_weight
            }
            
            self.model.retrain_weights(
                training_data['features'],
                training_data['labels']
            )
            
            new_weights = {
                'xgboost': self.model.xgboost_weight,
                'neural_net': self.model.neural_net_weight
            }
            
            weight_changes = {
                'xgboost': new_weights['xgboost'] - old_weights['xgboost'],
                'neural_net': new_weights['neural_net'] - old_weights['neural_net']
            }
            
            return {
                'success': True,
                'old_weights': old_weights,
                'new_weights': new_weights,
                'weight_changes': weight_changes,
                'sample_size': training_data_result['sample_size'],
                'message': 'Weights retrained successfully'
            }
        
        except Exception as e:
            return {
                'success': False,
                'message': f'Retraining failed: {str(e)}'
            }
    
    def get_model_drift_metrics(self, days_back: int = 90) -> Dict:
        """
        Monitor how model performance is drifting over time.
        
        Helps identify when retraining is necessary.
        """
        cutoff_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
        recent_results = self.data.get_race_results_since(cutoff_date)
        
        if not recent_results:
            return {
                'drift_detected': False,
                'message': 'No recent data'
            }
        
        accuracy_over_time = []
        dates_unique = sorted(set(r.get('race_date') for r in recent_results))
        
        for date in dates_unique[-7:]:
            day_results = [r for r in recent_results if r.get('race_date') == date]
            
            correct = sum(
                1 for r in day_results
                if r.get('xgboost_prediction') == r.get('position')
            )
            
            if day_results:
                accuracy = correct / len(day_results)
                accuracy_over_time.append({
                    'date': date,
                    'accuracy': accuracy,
                    'sample_size': len(day_results)
                })
        
        if len(accuracy_over_time) < 2:
            return {
                'drift_detected': False,
                'message': 'Insufficient data for drift detection'
            }
        
        accuracies = [a['accuracy'] for a in accuracy_over_time]
        drift = accuracies[0] - accuracies[-1]
        
        drift_detected = abs(drift) > 0.1
        
        return {
            'drift_detected': drift_detected,
            'drift_magnitude': float(drift),
            'recent_accuracy': float(accuracies[0]) if accuracies else 0.0,
            'older_accuracy': float(accuracies[-1]) if accuracies else 0.0,
            'recommendation': 'Retrain immediately' if drift_detected and drift < -0.1 else 'Monitor'
        }
