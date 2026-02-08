"""Prediction module for HKJC race predictions."""

# Only import the main classes that don't have relative import issues
# Users should import specific modules directly when running as scripts

try:
    from .enhanced_predictor import EnhancedRacePredictor, MultiRaceAnalyzer
    from .race_predictor import RacePredictor
    from .confidence_scorer import ConfidenceScorer
    from .probability_calculator import ProbabilityCalculator
except ImportError:
    # When running as script, these will be imported directly
    pass

__all__ = [
    'EnhancedRacePredictor',
    'MultiRaceAnalyzer', 
    'RacePredictor',
    'ConfidenceScorer',
    'ProbabilityCalculator'
]
