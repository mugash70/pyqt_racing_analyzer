"""Dynamic configuration system that calculates thresholds from data."""

import numpy as np
import sqlite3
from typing import Dict


class DynamicConfig:
    """Calculates configuration values from historical data."""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._config = {}
        self._calculate_config()
    
    def _calculate_config(self):
        """Calculate all configuration values from database."""
        conn = sqlite3.connect(self.db_path)
        
        try:
            # Default values from database statistics
            self._config.update(self._get_default_values(conn))
            
            # Probability bounds from historical data
            self._config.update(self._get_probability_bounds(conn))
            
            # Analysis thresholds from performance data
            self._config.update(self._get_analysis_thresholds(conn))
            
            # Race processing parameters
            self._config.update(self._get_race_parameters(conn))
            
        except Exception:
            # Fallback to sensible defaults if calculation fails
            self._config = self._get_fallback_config()
        finally:
            conn.close()
    
    def _get_default_values(self, conn) -> Dict:
        """Calculate default values from database statistics."""
        cursor = conn.cursor()
        
        # Default draw position (median)
        cursor.execute("SELECT draw FROM future_race_cards WHERE draw IS NOT NULL")
        draws = [row[0] for row in cursor.fetchall() if row[0]]
        default_draw = int(np.median(draws)) if draws else 8
        
        # Default weight (median)
        cursor.execute("SELECT weight FROM future_race_cards WHERE weight IS NOT NULL")
        weights = [int(row[0]) for row in cursor.fetchall() if row[0] and str(row[0]).isdigit()]
        default_weight = str(int(np.median(weights))) if weights else '120'
        
        # Default distance (mode)
        cursor.execute("SELECT race_distance FROM future_race_cards WHERE race_distance IS NOT NULL")
        distances = [row[0] for row in cursor.fetchall() if row[0]]
        default_distance = max(set(distances), key=distances.count) if distances else '1600m'
        
        # Default class (mode)
        cursor.execute("SELECT race_class FROM future_race_cards WHERE race_class IS NOT NULL")
        classes = [row[0] for row in cursor.fetchall() if row[0]]
        default_class = max(set(classes), key=classes.count) if classes else 'Class 4'
        
        # Minimum valid odds (5th percentile)
        cursor.execute("SELECT win_odds FROM odds_history WHERE win_odds > 0")
        odds = [row[0] for row in cursor.fetchall()]
        min_odds = np.percentile(odds, 5) if odds else 1.1
        
        return {
            'default_draw': default_draw,
            'default_weight': default_weight,
            'default_distance': default_distance,
            'default_class': default_class,
            'default_going': 'GOOD',
            'min_valid_odds': max(1.0, min_odds)
        }
    
    def _get_probability_bounds(self, conn) -> Dict:
        """Calculate probability bounds from historical win rates."""
        cursor = conn.cursor()
        
        # Get win rates by calculating from race results
        cursor.execute("""
            SELECT COUNT(*) as total, 
                   SUM(CASE WHEN position = 1 THEN 1 ELSE 0 END) as wins
            FROM race_results 
            GROUP BY horse_name
            HAVING total >= 5
        """)
        
        win_rates = []
        for row in cursor.fetchall():
            total, wins = row
            win_rate = wins / total
            win_rates.append(win_rate)
        
        if win_rates:
            min_prob = max(0.01, np.percentile(win_rates, 5))
            max_prob = min(0.95, np.percentile(win_rates, 95))
        else:
            min_prob, max_prob = 0.01, 0.95
        
        return {
            'min_probability': min_prob,
            'max_probability': max_prob
        }
    
    def _get_analysis_thresholds(self, conn) -> Dict:
        """Calculate analysis thresholds from performance data."""
        cursor = conn.cursor()
        
        # Strong probability threshold (mean of winning horses)
        cursor.execute("""
            SELECT COUNT(*) as field_size
            FROM future_race_cards 
            GROUP BY race_date, race_number
        """)
        field_sizes = [row[0] for row in cursor.fetchall()]
        avg_field_size = np.mean(field_sizes) if field_sizes else 12
        strong_prob_threshold = max(15.0, 100 / avg_field_size * 1.5)  # 1.5x average
        
        return {
            'strong_probability_threshold': strong_prob_threshold,
            'high_confidence_threshold': 0.7,
            'positive_value_threshold': 10.0,
            'interaction_multiplier_threshold': 1.1,
            'moderate_risk_threshold': 40.0,
            'high_risk_threshold': 60.0
        }
    
    def _get_race_parameters(self, conn) -> Dict:
        """Calculate race processing parameters."""
        cursor = conn.cursor()
        
        # Maximum races per day
        cursor.execute("""
            SELECT MAX(race_number) as max_race
            FROM future_race_cards 
            GROUP BY race_date
        """)
        max_races = [row[0] for row in cursor.fetchall() if row[0]]
        max_race_number = int(np.percentile(max_races, 90)) if max_races else 11
        
        # End of card threshold (80th percentile)
        end_threshold = int(np.percentile(max_races, 80)) if max_races else 8
        
        return {
            'max_race_number': max_race_number,
            'end_of_card_threshold': end_threshold,
            'percentage_multiplier': 100.0,
            'place_positions': 3.0
        }
    
    def _get_fallback_config(self) -> Dict:
        """Fallback configuration if database calculation fails."""
        return {
            'default_draw': 8,
            'default_weight': '120',
            'default_distance': '1600m',
            'default_class': 'Class 4',
            'default_going': 'GOOD',
            'min_valid_odds': 1.1,
            'min_probability': 0.01,
            'max_probability': 0.95,
            'strong_probability_threshold': 25.0,
            'high_confidence_threshold': 0.7,
            'positive_value_threshold': 10.0,
            'interaction_multiplier_threshold': 1.1,
            'moderate_risk_threshold': 40.0,
            'high_risk_threshold': 60.0,
            'max_race_number': 11,
            'end_of_card_threshold': 8,
            'percentage_multiplier': 100.0,
            'place_positions': 3.0
        }
    
    def get(self, key: str, default=None):
        """Get configuration value."""
        return self._config.get(key, default)