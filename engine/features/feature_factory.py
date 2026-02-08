"""Feature extraction and engineering factory - now using EnhancedFeatureEngineer."""

from typing import Dict, List
import numpy as np
import pandas as pd
import warnings
from ..core.data_integrator import DataIntegrator
from .enhanced_features import EnhancedFeatureEngineer

warnings.filterwarnings('ignore', message='Mean of empty slice')
warnings.filterwarnings('ignore', message='invalid value encountered in scalar divide')


class FeatureFactory:
    """Creates 100+ enhanced features for machine learning models using all database tables."""
    
    def __init__(self, data_integrator: DataIntegrator):
        """Initialize with data integrator and enhanced feature engineer."""
        self.data = data_integrator
        self.enhanced_engineer = EnhancedFeatureEngineer(data_integrator)
    
    def extract_all_features(self, horse_name: str, horse_number: int, 
                            jockey: str, trainer: str, weight: str, draw: int,
                            race_date: str, race_number: int, track: str, 
                            distance: str, race_class: str, current_odds: float = None,
                            field_size: int = 14) -> Dict:
        """
        Extract all 100+ enhanced features for a horse in a race.
        
        Combines features from all 29 database tables for comprehensive analysis.
        """
        # Use the enhanced feature engineer which extracts all available features
        features = self.enhanced_engineer.extract_all_enhanced_features(
            horse_name=horse_name,
            horse_number=horse_number,
            jockey=jockey,
            trainer=trainer,
            weight=weight,
            draw=draw,
            race_date=race_date,
            race_number=race_number,
            track=track,
            distance=distance,
            race_class=race_class,
            current_odds=current_odds,
            field_size=field_size
        )
        
        return features
    
    def create_feature_dataframe(self, horses_data: List[Dict]) -> pd.DataFrame:
        """
        Create feature dataframe from list of horse data.
        
        Each dict should contain: horse_name, horse_number, jockey, trainer, 
        weight, draw, race_date, race_number, track, distance, race_class, 
        current_odds, field_size
        """
        features_list = []
        
        for horse in horses_data:
            features = self.extract_all_features(
                horse_name=horse['horse_name'],
                horse_number=horse['horse_number'],
                jockey=horse['jockey'],
                trainer=horse['trainer'],
                weight=horse['weight'],
                draw=horse['draw'],
                race_date=horse['race_date'],
                race_number=horse['race_number'],
                track=horse['track'],
                distance=horse['distance'],
                race_class=horse['race_class'],
                current_odds=horse['current_odds'],
                field_size=horse.get('field_size', 14)
            )
            features_list.append(features)
        
        return pd.DataFrame(features_list)
