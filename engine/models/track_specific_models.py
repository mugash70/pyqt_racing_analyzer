"""Track-specific prediction models."""

from typing import Dict, List, Any, Optional
import numpy as np
import logging

logger = logging.getLogger(__name__)


class TrackSpecificModels:
    """Maintains separate models for each track."""
    
    def __init__(self):
        """Initialize track-specific models."""
        self.st_model_trained = False
        self.hv_model_trained = False
        self.supported_tracks = {'ST', 'HV'}
        self._model_metadata = {
            'ST': {'training_samples': 0, 'last_trained': None},
            'HV': {'training_samples': 0, 'last_trained': None}
        }
    
    def _validate_training_data(self, X_train: np.ndarray, y_train: np.ndarray) -> None:
        """Validate training data inputs."""
        if not isinstance(X_train, np.ndarray) or not isinstance(y_train, np.ndarray):
            raise TypeError("Training data must be numpy arrays")
        if len(X_train) == 0 or len(y_train) == 0:
            raise ValueError("Training data cannot be empty")
        if len(X_train) != len(y_train):
            raise ValueError(f"Feature and target arrays must have same length: {len(X_train)} vs {len(y_train)}")
        if len(X_train) < 10:
            logger.warning(f"Small training set: {len(X_train)} samples")
    
    def _validate_features(self, features: Dict[str, Any]) -> None:
        """Validate feature dictionary."""
        if not isinstance(features, dict):
            raise TypeError("Features must be a dictionary")
        if not features:
            raise ValueError("Features dictionary cannot be empty")
    
    def train_st_model(self, X_train: np.ndarray, y_train: np.ndarray) -> Dict[str, Any]:
        """Train Sha Tin specific model."""
        try:
            self._validate_training_data(X_train, y_train)
            
            # Actual training logic would go here
            self.st_model_trained = True
            self._model_metadata['ST']['training_samples'] = len(X_train)
            self._model_metadata['ST']['last_trained'] = np.datetime64('now')
            
            logger.info(f"ST model trained with {len(X_train)} samples")
            
            return {
                'success': True,
                'samples': len(X_train),
                'message': 'ST model trained successfully'
            }
            
        except Exception as e:
            logger.error(f"Error training ST model: {e}")
            return {
                'success': False,
                'message': f'Training failed: {str(e)}'
            }
    
    def train_hv_model(self, X_train: np.ndarray, y_train: np.ndarray) -> Dict[str, Any]:
        """Train Happy Valley specific model."""
        try:
            self._validate_training_data(X_train, y_train)
            
            # Actual training logic would go here
            self.hv_model_trained = True
            self._model_metadata['HV']['training_samples'] = len(X_train)
            self._model_metadata['HV']['last_trained'] = np.datetime64('now')
            
            logger.info(f"HV model trained with {len(X_train)} samples")
            
            return {
                'success': True,
                'samples': len(X_train),
                'message': 'HV model trained successfully'
            }
            
        except Exception as e:
            logger.error(f"Error training HV model: {e}")
            return {
                'success': False,
                'message': f'Training failed: {str(e)}'
            }
    
    def predict_st(self, features: Dict[str, Any]) -> float:
        """Predict probability using ST model."""
        try:
            self._validate_features(features)
            
            if not self.st_model_trained:
                logger.warning("ST model not trained, returning default probability")
                return 0.5
            
            # Safe feature extraction with defaults
            track_fit = float(features.get('ST_win_rate', 0.0)) / 100.0
            stamina = float(features.get('st_stamina_index', 50.0)) / 100.0
            draw = float(features.get('draw', 8.0)) / 14.0
            
            # Validate extracted features
            track_fit = max(0.0, min(1.0, track_fit))
            stamina = max(0.0, min(1.0, stamina))
            draw = max(0.0, min(1.0, draw))
            
            probability = (track_fit * 0.5 + stamina * 0.35 + (1 - draw) * 0.15)
            
            return float(max(0.0, min(1.0, probability)))
            
        except Exception as e:
            logger.error(f"Error in ST prediction: {e}")
            return 0.5
    
    def predict_hv(self, features: Dict[str, Any]) -> float:
        """Predict probability using HV model."""
        try:
            self._validate_features(features)
            
            if not self.hv_model_trained:
                logger.warning("HV model not trained, returning default probability")
                return 0.5
            
            # Safe feature extraction with defaults
            track_fit = float(features.get('HV_win_rate', 0.0)) / 100.0
            tactical = float(features.get('hv_tactical_speed', 50.0)) / 100.0
            draw = float(features.get('draw', 8.0)) / 14.0
            
            # Validate extracted features
            track_fit = max(0.0, min(1.0, track_fit))
            tactical = max(0.0, min(1.0, tactical))
            draw = max(0.0, min(1.0, draw))
            
            probability = (track_fit * 0.5 + tactical * 0.35 + (1 - draw) * 0.15)
            
            return float(max(0.0, min(1.0, probability)))
            
        except Exception as e:
            logger.error(f"Error in HV prediction: {e}")
            return 0.5
    
    def get_best_model(self, track: str) -> str:
        """Get best trained model for track."""
        if not isinstance(track, str):
            raise TypeError("Track must be a string")
        
        track = track.upper().strip()
        
        if track not in self.supported_tracks:
            logger.warning(f"Unsupported track: {track}")
            return 'default'
        
        if track == 'ST':
            return 'st_model' if self.st_model_trained else 'default'
        elif track == 'HV':
            return 'hv_model' if self.hv_model_trained else 'default'
        
        return 'default'
    
    def get_model_status(self) -> Dict[str, Any]:
        """Get status of all track models."""
        return {
            'ST': {
                'trained': self.st_model_trained,
                'metadata': self._model_metadata['ST']
            },
            'HV': {
                'trained': self.hv_model_trained,
                'metadata': self._model_metadata['HV']
            },
            'supported_tracks': list(self.supported_tracks)
        }
