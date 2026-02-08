# professional_calibration.py
import pickle
import numpy as np
from datetime import datetime
import os

class ProfessionalCalibrator:
    """
    Professional calibration for horse racing models.
    Based on real betting principles and market behavior.
    """
    
    def __init__(self, method='power_law'):
        """
        Args:
            method: 'power_law', 'logit_shift', or 'market_adjusted'
        """
        self.method = method
        self.params = {}
        
        # Default parameters based on empirical studies
        if method == 'power_law':
            self.params['exponent'] = 0.75  # Reduces favorites, boosts longshots
        elif method == 'logit_shift':
            self.params['shift'] = -0.8  # Shift log-odds downward
        elif method == 'market_adjusted':
            self.params['market_weight'] = 0.3  # Blend 30% market info
        else:
            raise ValueError(f"Unknown method: {method}")
    
    def calibrate(self, raw_probs, market_odds=None):
        """
        Calibrate raw probabilities.
        
        Args:
            raw_probs: List of raw probabilities from model
            market_odds: List of market odds (optional)
            
        Returns:
            List of calibrated probabilities
        """
        if self.method == 'power_law':
            return self._power_law_calibration(raw_probs)
        elif self.method == 'logit_shift':
            return self._logit_shift_calibration(raw_probs)
        elif self.method == 'market_adjusted':
            if market_odds is None:
                raise ValueError("market_odds required for market_adjusted method")
            return self._market_adjusted_calibration(raw_probs, market_odds)
    
    def _power_law_calibration(self, raw_probs):
        """Power law: p' = p^exponent, then renormalize."""
        exponent = self.params['exponent']
        
        # Apply power law
        calibrated = [p ** exponent for p in raw_probs]
        
        # Normalize to sum to 1
        total = sum(calibrated)
        calibrated = [c / total for c in calibrated]
        
        return calibrated
    
    def _logit_shift_calibration(self, raw_probs):
        """Shift log-odds by constant amount."""
        shift = self.params['shift']
        
        calibrated = []
        for p in raw_probs:
            # Avoid extremes
            p = max(0.001, min(0.999, p))
            
            # Convert to log-odds
            logit = np.log(p / (1 - p))
            
            # Apply shift
            calibrated_logit = logit + shift
            
            # Convert back to probability
            calibrated_prob = 1 / (1 + np.exp(-calibrated_logit))
            calibrated.append(calibrated_prob)
        
        # Normalize
        total = sum(calibrated)
        calibrated = [c / total for c in calibrated]
        
        return calibrated
    
    def _market_adjusted_calibration(self, raw_probs, market_odds):
        """Blend model predictions with market implied probabilities."""
        market_weight = self.params['market_weight']
        
        # Convert odds to implied probabilities
        market_probs = [1 / odds for odds in market_odds]
        
        # Normalize market probabilities to sum to 1
        market_total = sum(market_probs)
        market_probs = [m / market_total for m in market_probs]
        
        # Blend model and market
        calibrated = []
        for model_p, market_p in zip(raw_probs, market_probs):
            blended = (1 - market_weight) * model_p + market_weight * market_p
            calibrated.append(blended)
        
        # Final normalization
        total = sum(calibrated)
        calibrated = [c / total for c in calibrated]
        
        return calibrated
    
    def fit_to_data(self, raw_probs_list, actual_wins_list, market_odds_list=None):
        """
        Fit calibration parameters to historical data.
        
        Args:
            raw_probs_list: List of lists of raw probabilities
            actual_wins_list: List of lists of actual outcomes (1 for win, 0 for loss)
            market_odds_list: Optional list of lists of market odds
        """
        if self.method == 'power_law':
            self._fit_power_law(raw_probs_list, actual_wins_list)
        elif self.method == 'logit_shift':
            self._fit_logit_shift(raw_probs_list, actual_wins_list)
        elif self.method == 'market_adjusted':
            if market_odds_list is None:
                raise ValueError("market_odds_list required for market_adjusted method")
            self._fit_market_adjusted(raw_probs_list, actual_wins_list, market_odds_list)
    
    def _fit_power_law(self, raw_probs_list, actual_wins_list):
        """Find optimal exponent for power law calibration."""
        # Grid search for best exponent
        best_score = float('inf')
        best_exponent = 0.75
        
        for exponent in np.arange(0.5, 1.1, 0.05):
            brier_scores = []
            
            for raw_probs, actuals in zip(raw_probs_list, actual_wins_list):
                if len(raw_probs) == 0:
                    continue
                
                # Apply calibration
                calibrated = [p ** exponent for p in raw_probs]
                total = sum(calibrated)
                if total > 0:
                    calibrated = [c / total for c in calibrated]
                
                # Calculate Brier score
                brier = np.mean([(c - a) ** 2 for c, a in zip(calibrated, actuals)])
                brier_scores.append(brier)
            
            if brier_scores:
                avg_brier = np.mean(brier_scores)
                if avg_brier < best_score:
                    best_score = avg_brier
                    best_exponent = exponent
        
        self.params['exponent'] = best_exponent
        print(f"Fitted power law exponent: {best_exponent:.3f} (Brier: {best_score:.4f})")
    
    def _fit_logit_shift(self, raw_probs_list, actual_wins_list):
        """Find optimal logit shift."""
        # Flatten all data
        all_raw = []
        all_actual = []
        
        for raw_probs, actuals in zip(raw_probs_list, actual_wins_list):
            all_raw.extend(raw_probs)
            all_actual.extend(actuals)
        
        # Find shift that minimizes Brier score
        best_score = float('inf')
        best_shift = -0.8
        
        for shift in np.arange(-2.0, 1.0, 0.1):
            brier_scores = []
            
            for raw_p, actual in zip(all_raw, all_actual):
                # Apply shift
                raw_p = max(0.001, min(0.999, raw_p))
                logit = np.log(raw_p / (1 - raw_p))
                calibrated_logit = logit + shift
                calibrated = 1 / (1 + np.exp(-calibrated_logit))
                
                brier = (calibrated - actual) ** 2
                brier_scores.append(brier)
            
            avg_brier = np.mean(brier_scores)
            if avg_brier < best_score:
                best_score = avg_brier
                best_shift = shift
        
        self.params['shift'] = best_shift
        print(f"Fitted logit shift: {best_shift:.3f} (Brier: {best_score:.4f})")

def create_and_save_calibrator(method='power_law'):
    """Create and save a professional calibration model."""
    
    # Create calibrator
    calibrator = ProfessionalCalibrator(method=method)
    
    # You could load historical data here to fit parameters
    # For now, use sensible defaults
    
    # Save the model
    model_path = "os.path.join(os.path.dirname(__file__), "models", "calibration_model.pkl")"
    with open(model_path, 'wb') as f:
        pickle.dump({
            'calibrator': calibrator,
            'method': method,
            'created_date': datetime.now().isoformat(),
            'description': f'Professional {method} calibration for horse racing'
        }, f)
    
    print(f"Professional calibration model saved to {model_path}")
    print(f"Method: {method}")
    
    # Test it
    print("\n=== CALIBRATION TEST ===")
    test_raw = [0.4, 0.2, 0.15, 0.1, 0.08, 0.07]  # Example race
    test_odds = [2.5, 5.0, 6.67, 10.0, 12.5, 14.29] if method == 'market_adjusted' else None
    
    calibrated = calibrator.calibrate(test_raw, test_odds)
    
    print("Raw probabilities:")
    for i, p in enumerate(test_raw):
        print(f"  Horse {i+1}: {p:.1%}")
    
    print("\nCalibrated probabilities:")
    for i, p in enumerate(calibrated):
        print(f"  Horse {i+1}: {p:.1%}")
    
    print(f"\nSum of raw: {sum(test_raw):.1%}")
    print(f"Sum of calibrated: {sum(calibrated):.1%}")

# Usage in your race_predictor.py
def apply_professional_calibration(race_predictor, raw_predictions, market_odds=None):
    """
    Apply professional calibration to race predictions.
    
    Returns list of predictions with calibrated probabilities.
    """
    # Load calibrator
    model_path = "os.path.join(os.path.dirname(__file__), "models", "calibration_model.pkl")"
    
    if not os.path.exists(model_path):
        # Create default if doesn't exist
        create_and_save_calibrator()
    
    with open(model_path, 'rb') as f:
        cal_data = pickle.load(f)
    
    calibrator = cal_data['calibrator']
    
    # Extract raw probabilities
    raw_probs = [p['raw_probability'] for p in raw_predictions]
    
    # Apply calibration
    if calibrator.method == 'market_adjusted' and market_odds:
        calibrated_probs = calibrator.calibrate(raw_probs, market_odds)
    else:
        calibrated_probs = calibrator.calibrate(raw_probs)
    
    # Update predictions
    for pred, cal_prob in zip(raw_predictions, calibrated_probs):
        pred['win_probability'] = float(cal_prob * 100)  # Convert to percentage
    
    return raw_predictions

if __name__ == "__main__":
    # Create a professional calibration model
    create_and_save_calibrator(method='power_law')  # Or 'logit_shift' or 'market_adjusted'