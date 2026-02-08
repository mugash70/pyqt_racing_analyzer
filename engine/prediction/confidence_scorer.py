"""Advanced confidence scoring using ensemble disagreement and feature alignment."""

from typing import Dict, List, Optional, Tuple
import numpy as np


class ConfidenceScorer:
    """
    Calculates prediction confidence based on:
    - Ensemble model agreement (XGBoost vs Neural Network)
    - Feature alignment (agreement between different feature types)
    - Historical accuracy on similar horses
    - Prediction stability across slight data variations
    """
    
    def __init__(self):
        """Initialize confidence scorer."""
        self.min_confidence = 0.15
        self.max_confidence = 0.99
    
    def calculate_ensemble_confidence(
        self,
        xgboost_prob: float,
        neural_net_prob: float,
        win_probability: float
    ) -> float:
        """
        Calculate confidence based on ensemble model agreement.
        
        Higher agreement = higher confidence.
        Uses ensemble spread and consistency with average prediction.
        """
        if not (0 <= xgboost_prob <= 1 and 0 <= neural_net_prob <= 1):
            return self.min_confidence
        
        agreement_distance = abs(xgboost_prob - neural_net_prob)
        agreement_score = 1.0 - min(0.5, agreement_distance)
        
        average_prediction = (xgboost_prob + neural_net_prob) / 2
        prediction_consistency = 1.0 - abs(average_prediction - win_probability)
        
        ensemble_confidence = (agreement_score * 0.7 + prediction_consistency * 0.3)
        
        return float(np.clip(ensemble_confidence, self.min_confidence, self.max_confidence))
    
    def calculate_feature_alignment_confidence(
        self,
        feature_scores: Dict[str, float]
    ) -> float:
        """
        Calculate confidence based on feature alignment.
        
        When different feature types (form, track, distance) all point to the same outcome,
        confidence is higher. When they conflict, confidence is lower.
        """
        if not feature_scores:
            return self.min_confidence
        
        scores = list(feature_scores.values())
        
        if len(scores) < 2:
            return self.min_confidence
        
        mean_score = np.mean(scores)
        std_dev = np.std(scores)
        
        if mean_score == 0:
            alignment = 0.5
        else:
            alignment = 1.0 - min(1.0, std_dev / max(abs(mean_score), 0.1))
        
        return float(np.clip(alignment, self.min_confidence, self.max_confidence))
    
    def calculate_prediction_stability_confidence(
        self,
        base_probability: float,
        perturbed_probabilities: List[float]
    ) -> float:
        """
        Calculate confidence based on prediction stability.
        
        If small changes to features cause wildly different predictions,
        confidence should be lower. If predictions are stable, confidence is higher.
        """
        if not perturbed_probabilities:
            return self.min_confidence
        
        all_probs = [base_probability] + perturbed_probabilities
        stability = 1.0 - np.std(all_probs)
        
        return float(np.clip(stability, self.min_confidence, self.max_confidence))
    
    def calculate_historical_accuracy_confidence(
        self,
        horse_name: str,
        similar_horses_accuracy: Optional[List[float]] = None,
        horse_track_record: Optional[Dict] = None
    ) -> float:
        """
        Calculate confidence based on historical accuracy on similar horses/conditions.
        
        Uses accuracy of predictions on horses with similar characteristics.
        """
        if not similar_horses_accuracy:
            base_confidence = 0.5
        else:
            base_confidence = float(np.mean(similar_horses_accuracy))
        
        if horse_track_record:
            track_accuracy = horse_track_record.get('win_rate', 0.0)
            historical_confidence = (base_confidence * 0.5 + track_accuracy * 0.5)
        else:
            historical_confidence = base_confidence
        
        return float(np.clip(historical_confidence, self.min_confidence, self.max_confidence))
    
    def calculate_combined_confidence(
        self,
        ensemble_confidence: float,
        feature_alignment_confidence: float,
        stability_confidence: float,
        historical_confidence: float,
        weights: Optional[Dict[str, float]] = None
    ) -> float:
        """
        Combine all confidence components into final prediction confidence.
        
        Default weights: Ensemble (40%), Features (30%), Stability (20%), History (10%)
        """
        if weights is None:
            weights = {
                'ensemble': 0.45,
                'features': 0.35,
                'stability': 0.15,
                'historical': 0.05
            }
        
        combined = (
            ensemble_confidence * weights.get('ensemble', 0.4) +
            feature_alignment_confidence * weights.get('features', 0.3) +
            stability_confidence * weights.get('stability', 0.2) +
            historical_confidence * weights.get('historical', 0.1)
        )
        
        return float(np.clip(combined, self.min_confidence, self.max_confidence))
    
    def calculate_confidence_explanation(
        self,
        ensemble_confidence: float,
        feature_alignment_confidence: float,
        stability_confidence: float,
        historical_confidence: float
    ) -> Dict[str, str]:
        """
        Provide human-readable explanation of confidence components.
        """
        def conf_to_text(conf: float) -> str:
            if conf >= 0.85:
                return "Very High"
            elif conf >= 0.75:
                return "High"
            elif conf >= 0.65:
                return "Moderate"
            elif conf >= 0.55:
                return "Low"
            else:
                return "Very Low"
        
        return {
            'ensemble_agreement': conf_to_text(ensemble_confidence),
            'feature_alignment': conf_to_text(feature_alignment_confidence),
            'prediction_stability': conf_to_text(stability_confidence),
            'historical_accuracy': conf_to_text(historical_confidence)
        }


class ConfidenceCalibrator:
    """
    Calibrates confidence scores to match actual prediction accuracy.
    
    Uses isotonic regression or Platt scaling to ensure confidence values
    correspond to actual win probabilities.
    """
    
    def __init__(self):
        """Initialize calibrator."""
        self.calibration_data = []
        self.calibration_function = None
    
    def add_calibration_sample(
        self,
        predicted_confidence: float,
        actual_outcome: int
    ) -> None:
        """
        Add a calibration sample (confidence -> actual outcome).
        
        Args:
            predicted_confidence: Predicted confidence (0-1)
            actual_outcome: 1 if prediction was correct, 0 otherwise
        """
        self.calibration_data.append({
            'confidence': predicted_confidence,
            'outcome': actual_outcome
        })
    
    def calibrate(self, method: str = 'isotonic') -> None:
        """
        Calibrate confidence scores using specified method.
        
        Args:
            method: 'isotonic' or 'platt'
        """
        if len(self.calibration_data) < 10:
            return
        
        if method == 'isotonic':
            self._calibrate_isotonic()
        elif method == 'platt':
            self._calibrate_platt()
    
    def calibrate_confidence(self, raw_confidence: float) -> float:
        """
        Apply calibration to raw confidence score.
        
        Returns calibrated confidence that better matches actual accuracy.
        """
        if self.calibration_function is None:
            return raw_confidence
        
        return self.calibration_function(raw_confidence)
    
    def _calibrate_isotonic(self) -> None:
        """
        Fit isotonic regression to calibration data.
        
        Creates a monotonic mapping from predicted confidence to actual accuracy.
        """
        try:
            from sklearn.isotonic import IsotonicRegression
            
            confidences = np.array([d['confidence'] for d in self.calibration_data])
            outcomes = np.array([d['outcome'] for d in self.calibration_data])
            
            iso_reg = IsotonicRegression(bounds=(0, 1), increasing=True)
            iso_reg.fit(confidences, outcomes)
            
            self.calibration_function = iso_reg.predict
            
        except ImportError:
            self.calibration_function = None
    
    def _calibrate_platt(self) -> None:
        """
        Fit Platt scaling to calibration data.
        
        Creates a sigmoid mapping from predictions to probabilities.
        """
        try:
            from sklearn.linear_model import LogisticRegression
            
            confidences = np.array([d['confidence'] for d in self.calibration_data]).reshape(-1, 1)
            outcomes = np.array([d['outcome'] for d in self.calibration_data])
            
            lr = LogisticRegression()
            lr.fit(confidences, outcomes)
            
            self.calibration_function = lambda x: lr.predict_proba([[x]])[0][1]
            
        except ImportError:
            self.calibration_function = None
