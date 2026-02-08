"""Recent performance and form analysis."""

from typing import Dict, List
import numpy as np


class FormAnalyzer:
    """Analyzes recent horse form and performance trends."""
    
    def __init__(self, data_integrator):
        """Initialize with data integrator."""
        self.data = data_integrator
    
    def analyze_recent_form(self, horse_name: str, races: int = 5) -> Dict:
        """
        Analyze recent race form.
        
        Returns: form trend, consistency, momentum.
        """
        results = self.data.get_horse_race_results(horse_name, limit=races)
        
        if not results:
            return {
                'form_trend': 'No form',
                'consistency': 0.0,
                'momentum': 0.0,
                'recent_races': []
            }
        
        positions = [r['position'] for r in results if r['position']]
        
        if not positions:
            return {
                'form_trend': 'No form',
                'consistency': 0.0,
                'momentum': 0.0,
                'recent_races': []
            }
        
        avg_position = np.mean(positions)
        consistency = 100 - (np.std(positions) * 10)
        momentum = positions[0] - positions[-1]
        
        if momentum < -2:
            trend = 'Improving'
        elif momentum > 2:
            trend = 'Declining'
        else:
            trend = 'Steady'
        
        return {
            'form_trend': trend,
            'consistency': float(max(0, min(100, consistency))),
            'momentum': float(momentum),
            'average_position': float(avg_position),
            'recent_races': positions
        }
    
    def analyze_peak_performance(self, horse_name: str) -> Dict:
        """Analyze when horse is at peak performance."""
        results = self.data.get_horse_race_results(horse_name, limit=30)
        
        if not results:
            return {
                'peak_performance_age': 'Unknown',
                'current_form_vs_peak': 0.0,
                'races_since_peak': 0
            }
        
        positions = [r['position'] for r in results if r['position']]
        
        if positions:
            best_result = min(positions)
            races_since_best = positions.index(best_result) if best_result in positions else 0
            current_vs_peak = positions[0] - best_result
        else:
            races_since_best = 0
            current_vs_peak = 0
        
        return {
            'peak_performance_age': 'Prime',
            'current_form_vs_peak': float(current_vs_peak),
            'races_since_peak': races_since_best
        }
    
    def analyze_consistency_cycle(self, horse_name: str) -> Dict:
        """Analyze horse's consistency patterns."""
        results = self.data.get_horse_race_results(horse_name, limit=20)
        
        if not results:
            return {
                'cycle_pattern': 'Unknown',
                'peak_every_n_races': 0,
                'consistency_rating': 0.0
            }
        
        positions = [r['position'] for r in results if r['position']]
        
        if positions:
            top_3_count = sum(1 for p in positions if p <= 3)
            consistency = (top_3_count / len(positions)) * 100
        else:
            consistency = 0.0
        
        return {
            'cycle_pattern': 'Consistent' if consistency > 50 else 'Inconsistent',
            'peak_every_n_races': 3 if consistency > 40 else 5,
            'consistency_rating': float(consistency)
        }
