"""Features module for horse racing feature engineering."""

try:
    from .enhanced_features import EnhancedFeatureEngineer
    from .feature_factory import FeatureFactory
    from .feature_interactions import FeatureInteractionOptimizer, JockeyTrainerSynergy
    from .form_analyzer_improved import ImprovedFormAnalyzer
    from .form_analyzer import FormAnalyzer
    from .pedigree_analyzer import PedigreeAnalyzer
except ImportError:
    # When running as script
    pass

__all__ = [
    'EnhancedFeatureEngineer',
    'FeatureFactory',
    'FeatureInteractionOptimizer',
    'JockeyTrainerSynergy',
    'ImprovedFormAnalyzer',
    'FormAnalyzer',
    'PedigreeAnalyzer'
]
