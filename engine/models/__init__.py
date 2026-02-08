"""Models module for horse racing prediction models."""

try:
    from .enhanced_ensemble import EnhancedEnsembleModel, EnhancedModelConfig
    from .ensemble_model import EnsembleModel, ModelConfig
    from .ensemble_optimizer import EnsembleWeightOptimizer, RecentDataRetrainer
    from .probability_calibration import ProbabilityCalibrator
    from .track_specific_models import TrackSpecificModels
except ImportError:
    # When running as script
    pass

__all__ = [
    'EnhancedEnsembleModel',
    'EnhancedModelConfig',
    'EnsembleModel',
    'ModelConfig',
    'EnsembleWeightOptimizer',
    'RecentDataRetrainer',
    'ProbabilityCalibrator',
    'TrackSpecificModels'
]
