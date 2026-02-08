"""Probability calibration using Isotonic Regression and other methods."""

from typing import Dict, List, Optional, Tuple, Any
import numpy as np
from datetime import datetime, timedelta
import logging
import os
import pickle

logger = logging.getLogger(__name__)


class ProbabilityCalibrator:
    """
    Calibrates predicted probabilities to match actual observed frequencies.
    
    Ensures that when we predict 50% win probability, approximately 50% of those
    horses actually win (and similarly for other probability levels).
    """
    
    def __init__(self, model_path: Optional[str] = None):
        """Initialize calibrator."""
        self.calibration_data: List[Dict[str, Any]] = []
        self.calibration_model = None
        self.method: Optional[str] = None
        self.min_samples = 30
        self.is_fitted = False
        
        # Default model path if none provided
        if model_path is None:
            # Try to find calibration_model.pkl in the same directory as this file
            dir_path = os.path.dirname(os.path.abspath(__file__))
            model_path = os.path.join(dir_path, "calibration_model.pkl")
            
        if os.path.exists(model_path):
            # Skip loading to avoid pickle issues
            logger.info(f"跳過校準模型載入以避免相容性問題")
            pass
    
    def load_model(self, model_path: str) -> bool:
        """Load a saved calibration model."""
        try:
            with open(model_path, 'rb') as f:
                data = pickle.load(f)
                self.calibration_model = data.get('model')
                self.method = data.get('method')
                self.is_fitted = data.get('is_fitted', False)
            logger.info(f"Loaded calibration model from {model_path} (method: {self.method})")
            return True
        except Exception as e:
            logger.error(f"Failed to load calibration model: {e}")
            return False
    
    def add_calibration_sample(
        self,
        predicted_probability: float,
        actual_outcome: int,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Add a calibration sample.
        
        Args:
            predicted_probability: Model's predicted win probability (0-1)
            actual_outcome: 1 if horse won, 0 otherwise
            metadata: Optional metadata (horse_name, race_date, etc)
        """
        # Input validation
        if not isinstance(predicted_probability, (int, float)):
            raise TypeError("predicted_probability must be a number")
        if not (0 <= predicted_probability <= 1):
            raise ValueError(f"predicted_probability must be between 0 and 1, got {predicted_probability}")
        if actual_outcome not in [0, 1]:
            raise ValueError(f"actual_outcome must be 0 or 1, got {actual_outcome}")
        
        sample = {
            'predicted': float(predicted_probability),
            'actual': int(actual_outcome),
            'metadata': metadata or {},
            'timestamp': datetime.now().isoformat()
        }
        self.calibration_data.append(sample)
    
    def fit_isotonic_regression(self) -> Dict:
        """
        Fit isotonic regression for calibration.
        
        Creates a monotonically increasing mapping from predicted to observed probabilities.
        Best for ensuring calibration while preserving relative ordering.
        """
        if len(self.calibration_data) < self.min_samples:
            return {
                'success': False,
                'message': f'Need at least {self.min_samples} samples, have {len(self.calibration_data)}'
            }
        
        try:
            from sklearn.isotonic import IsotonicRegression
            
            predictions = np.array([s['predicted'] for s in self.calibration_data])
            outcomes = np.array([s['actual'] for s in self.calibration_data])
            
            self.calibration_model = IsotonicRegression(
                bounds=(0, 1),
                increasing=True,
                out_of_bounds='clip'
            )
            
            self.calibration_model.fit(predictions, outcomes)
            self.method = 'isotonic'
            self.is_fitted = True
            
            calibration_error = self._calculate_calibration_error(
                predictions, outcomes, self.calibration_model
            )
            
            return {
                'success': True,
                'method': 'isotonic',
                'samples': len(self.calibration_data),
                'calibration_error': float(calibration_error),
                'message': 'Isotonic regression fitted successfully'
            }
        
        except ImportError:
            return {
                'success': False,
                'message': 'scikit-learn not available'
            }
    
    def fit_platt_scaling(self) -> Dict:
        """
        Fit Platt scaling for calibration.
        
        Uses logistic regression to create a smooth S-curve mapping.
        Good for miscalibrated models with systematic bias.
        """
        if len(self.calibration_data) < self.min_samples:
            return {
                'success': False,
                'message': f'Need at least {self.min_samples} samples, have {len(self.calibration_data)}'
            }
        
        try:
            from sklearn.linear_model import LogisticRegression
            
            predictions = np.array([s['predicted'] for s in self.calibration_data]).reshape(-1, 1)
            outcomes = np.array([s['actual'] for s in self.calibration_data])
            
            self.calibration_model = LogisticRegression(max_iter=1000)
            self.calibration_model.fit(predictions, outcomes)
            self.method = 'platt'
            self.is_fitted = True
            
            predicted_calibrated = self.calibration_model.predict_proba(predictions)[:, 1]
            calibration_error = self._calculate_calibration_error(
                predictions.flatten(), outcomes, lambda p: self.calibration_model.predict_proba([[p]])[0][1]
            )
            
            return {
                'success': True,
                'method': 'platt',
                'samples': len(self.calibration_data),
                'calibration_error': float(calibration_error),
                'message': 'Platt scaling fitted successfully'
            }
        
        except ImportError:
            return {
                'success': False,
                'message': 'scikit-learn not available'
            }
    
    def fit_histogram_binning(self, n_bins: int = 10) -> Dict:
        """
        Fit histogram binning calibration.
        
        Divides probability range into bins and calculates average empirical frequency.
        Simpler but can be less smooth than other methods.
        """
        if len(self.calibration_data) < self.min_samples:
            return {
                'success': False,
                'message': f'Need at least {self.min_samples} samples, have {len(self.calibration_data)}'
            }
        
        predictions = np.array([s['predicted'] for s in self.calibration_data])
        outcomes = np.array([s['actual'] for s in self.calibration_data])
        
        bins = np.linspace(0, 1, n_bins + 1)
        bin_mapping = {}
        
        for i in range(n_bins):
            bin_start = bins[i]
            bin_end = bins[i + 1]
            
            mask = (predictions >= bin_start) & (predictions <= bin_end)
            
            if mask.sum() > 0:
                empirical_freq = outcomes[mask].mean()
                bin_center = (bin_start + bin_end) / 2
                bin_mapping[bin_center] = empirical_freq
        
        self.calibration_model = bin_mapping
        self.method = 'histogram'
        self.is_fitted = True
        
        return {
            'success': True,
            'method': 'histogram',
            'samples': len(self.calibration_data),
            'bins': len(bin_mapping),
            'message': f'Histogram binning fitted with {len(bin_mapping)} bins'
        }
    
    def calibrate_probability(self, raw_probability: float) -> float:
        """
        Apply fitted calibration to a raw probability.
        
        Args:
            raw_probability: Model's predicted probability (0-1)
        
        Returns:
            Calibrated probability
        """
        # Input validation
        if not isinstance(raw_probability, (int, float)):
            raise TypeError("raw_probability must be a number")
        if not (0 <= raw_probability <= 1):
            raise ValueError(f"raw_probability must be between 0 and 1, got {raw_probability}")
        
        if not self.is_fitted or self.calibration_model is None:
            logger.warning("Calibration model not fitted, returning raw probability")
            return float(raw_probability)
        
        raw_probability = float(np.clip(raw_probability, 0, 1))
        
        try:
            if self.method == 'isotonic':
                result = self.calibration_model.predict([raw_probability])[0]
                return float(np.clip(result, 0, 1))
            
            elif self.method == 'platt':
                result = self.calibration_model.predict_proba([[raw_probability]])[0][1]
                return float(np.clip(result, 0, 1))
            
            elif self.method == 'histogram':
                # For histogram method, interpolate between bins instead of using closest
                if len(self.calibration_model) == 0:
                    return float(raw_probability)
                
                bin_centers = sorted(self.calibration_model.keys())
                
                # If probability is outside range, use boundary values
                if raw_probability <= bin_centers[0]:
                    return float(self.calibration_model[bin_centers[0]])
                if raw_probability >= bin_centers[-1]:
                    return float(self.calibration_model[bin_centers[-1]])
                
                # Linear interpolation between bins
                for i in range(len(bin_centers) - 1):
                    if bin_centers[i] <= raw_probability <= bin_centers[i + 1]:
                        x0, x1 = bin_centers[i], bin_centers[i + 1]
                        y0, y1 = self.calibration_model[x0], self.calibration_model[x1]
                        
                        # Linear interpolation
                        result = y0 + (y1 - y0) * (raw_probability - x0) / (x1 - x0)
                        return float(np.clip(result, 0, 1))
                
                # Fallback to closest bin if interpolation fails
                closest_bin = min(
                    self.calibration_model.keys(),
                    key=lambda x: abs(x - raw_probability)
                )
                result = self.calibration_model[closest_bin]
                return float(np.clip(result, 0, 1))
            
        except Exception as e:
            logger.error(f"Error in calibration: {e}")
            return float(raw_probability)
        
        return float(raw_probability)
    
    def calibrate_probabilities(self, probabilities: List[float]) -> List[float]:
        """
        Calibrate multiple probabilities.
        """
        return [self.calibrate_probability(p) for p in probabilities]
    
    def get_calibration_report(self) -> Dict:
        """
        Generate comprehensive calibration report.
        """
        if len(self.calibration_data) < self.min_samples:
            return {
                'status': 'Insufficient data',
                'samples': len(self.calibration_data),
                'required': self.min_samples
            }
        
        predictions = np.array([s['predicted'] for s in self.calibration_data])
        outcomes = np.array([s['actual'] for s in self.calibration_data])
        
        report = {
            'total_samples': len(self.calibration_data),
            'method': self.method or 'not fitted',
            'overall_accuracy': float(np.mean(outcomes)),
            'prediction_range': {
                'min': float(predictions.min()),
                'max': float(predictions.max()),
                'mean': float(predictions.mean()),
                'std': float(predictions.std())
            }
        }
        
        if self.calibration_model is not None:
            report['calibration_error'] = float(self._calculate_calibration_error(
                predictions, outcomes, lambda p: self.calibrate_probability(p)
            ))
        
        bins = np.linspace(0, 1, 11)
        bin_analysis = []
        
        for i in range(len(bins) - 1):
            mask = (predictions >= bins[i]) & (predictions < bins[i + 1])
            if mask.sum() > 0:
                bin_analysis.append({
                    'probability_range': f'{bins[i]:.1f}-{bins[i+1]:.1f}',
                    'samples': int(mask.sum()),
                    'actual_frequency': float(outcomes[mask].mean())
                })
        
        report['bin_analysis'] = bin_analysis
        
        return report
    
    @staticmethod
    def _calculate_calibration_error(
        predictions: np.ndarray,
        outcomes: np.ndarray,
        calibration_func
    ) -> float:
        """
        Calculate calibration error (Expected Calibration Error).
        
        Measures how far predicted probabilities are from observed frequencies.
        """
        if callable(calibration_func):
            calibrated = np.array([calibration_func(p) for p in predictions])
        else:
            calibrated = calibration_func.predict(predictions)
        
        calibration_error = np.mean(np.abs(calibrated - outcomes))
        
        return calibration_error


class PerformanceBinner:
    """
    Groups predictions into bins and analyzes calibration by bin.
    
    Useful for identifying which probability ranges are well-calibrated.
    """
    
    def __init__(self, num_bins: int = 10):
        """Initialize with number of bins."""
        self.num_bins = num_bins
        self.bin_data = {}
    
    def bin_predictions(self, predictions: List[Dict]) -> Dict:
        """
        Bin predictions by probability level.
        
        Args:
            predictions: List of dicts with 'probability' and 'outcome' keys
        
        Returns:
            Analysis by bin
        """
        bins = {i: [] for i in range(self.num_bins)}
        
        for pred in predictions:
            prob = pred['probability']
            outcome = pred['outcome']
            
            bin_index = min(int(prob * self.num_bins), self.num_bins - 1)
            bins[bin_index].append(outcome)
        
        bin_analysis = {}
        
        for bin_idx, outcomes in bins.items():
            if len(outcomes) > 0:
                bin_start = bin_idx / self.num_bins
                bin_end = (bin_idx + 1) / self.num_bins
                
                bin_analysis[f'{bin_start:.1f}-{bin_end:.1f}'] = {
                    'samples': len(outcomes),
                    'win_frequency': np.mean(outcomes),
                    'expected_probability': (bin_start + bin_end) / 2
                }
        
        return bin_analysis
    
    def identify_poorly_calibrated_ranges(
        self,
        predictions: List[Dict],
        threshold: float = 0.1
    ) -> List[str]:
        """
        Identify probability ranges that are poorly calibrated.
        
        Args:
            predictions: List of predictions
            threshold: Error threshold (default 10%)
        
        Returns:
            List of poorly-calibrated probability ranges
        """
        bin_analysis = self.bin_predictions(predictions)
        
        poorly_calibrated = []
        
        for prob_range, stats in bin_analysis.items():
            expected = stats['expected_probability']
            actual = stats['win_frequency']
            
            error = abs(expected - actual)
            
            if error > threshold:
                poorly_calibrated.append(prob_range)
        
        return poorly_calibrated
