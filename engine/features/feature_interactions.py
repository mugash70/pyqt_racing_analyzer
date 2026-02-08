"""Advanced feature interactions: jockey-trainer synergy, track-distance-class patterns, and draw bias."""

from typing import Dict, List, Optional, Tuple
import numpy as np
from collections import defaultdict


class JockeyTrainerSynergy:
    """Analyzes synergy between jockeys and trainers."""
    
    def __init__(self, data_integrator):
        """Initialize with data integrator."""
        self.data = data_integrator
    
    def analyze_jockey_trainer_combo(
        self,
        jockey: str,
        trainer: str
    ) -> Dict:
        """
        Analyze historical performance of jockey-trainer combination.
        
        Returns performance metrics for this specific pairing.
        """
        try:
            results = self.data.get_jockey_trainer_results(jockey, trainer)
        except (AttributeError, NotImplementedError):
            return {
                'combo_synergy': 0.0,
                'combined_win_rate': 0.0,
                'combined_place_rate': 0.0,
                'races_together': 0,
                'synergy_confidence': 0.0
            }
        
        if not results:
            return {
                'combo_synergy': 0.0,
                'combined_win_rate': 0.0,
                'combined_place_rate': 0.0,
                'races_together': 0,
                'synergy_confidence': 0.0
            }
        
        # Convert positions to integers (database returns strings)
        positions = []
        for r in results:
            if r['position']:
                try:
                    positions.append(int(r['position']))
                except (ValueError, TypeError):
                    continue
        
        if not positions:
            return {
                'combo_synergy': 0.0,
                'combined_win_rate': 0.0,
                'combined_place_rate': 0.0,
                'races_together': len(results),
                'synergy_confidence': 0.0
            }
        
        win_rate = sum(1 for p in positions if p == 1) / len(positions)
        place_rate = sum(1 for p in positions if p <= 3) / len(positions)
        
        jockey_avg = self.data.get_jockey_performance(jockey).get('win_rate', 0.15)
        trainer_avg = self.data.get_trainer_performance(trainer).get('win_rate', 0.15)
        
        individual_expected = (jockey_avg + trainer_avg) / 2
        synergy = win_rate - individual_expected
        
        confidence = min(1.0, len(positions) / 20.0)
        
        return {
            'combo_synergy': float(synergy),
            'combined_win_rate': float(win_rate),
            'combined_place_rate': float(place_rate),
            'races_together': len(results),
            'synergy_confidence': float(confidence)
        }
    
    def get_synergy_adjustment(self, jockey: str, trainer: str) -> float:
        """
        Get probability adjustment factor for jockey-trainer synergy.
        
        Returns multiplier to apply to base win probability.
        """
        synergy_data = self.analyze_jockey_trainer_combo(jockey, trainer)
        synergy = synergy_data['combo_synergy']
        confidence = synergy_data['synergy_confidence']
        
        if synergy > 0.05 and confidence > 0.5:
            return 1.125
        elif synergy < -0.05 and confidence > 0.5:
            return 0.85
        else:
            return 1.0


class TrackDistanceClassInteraction:
    """Analyzes interactions between track, distance, and race class."""
    
    def __init__(self, data_integrator):
        """Initialize with data integrator."""
        self.data = data_integrator
    
    def analyze_track_distance_interaction(
        self,
        horse_name: str,
        track: str,
        distance: str
    ) -> Dict:
        """
        Analyze how horse performs at specific track-distance combination.
        
        Returns performance metrics for this specific combination.
        """
        try:
            results = self.data.get_horse_track_distance_results(
                horse_name, track, distance
            )
        except (AttributeError, NotImplementedError):
            return {
                'interaction_strength': 0.0,
                'win_rate_combo': 0.0,
                'avg_position_combo': None,
                'races_at_combo': 0
            }
        
        if not results:
            return {
                'interaction_strength': 0.0,
                'win_rate_combo': 0.0,
                'avg_position_combo': None,
                'races_at_combo': 0
            }
        
        # Convert positions to integers (database returns strings)
        positions = []
        for r in results:
            if r['position']:
                try:
                    positions.append(int(r['position']))
                except (ValueError, TypeError):
                    continue
        
        if not positions:
            return {
                'interaction_strength': 0.0,
                'win_rate_combo': 0.0,
                'avg_position_combo': None,
                'races_at_combo': len(results)
            }
        
        win_rate = sum(1 for p in positions if p == 1) / len(positions)
        avg_position = np.mean(positions)
        
        track_only = self.data.get_horse_track_performance(horse_name, track)
        distance_only = self.data.get_horse_distance_performance(horse_name, distance)
        
        track_rate = track_only.get('win_rate', 0.15)
        distance_rate = distance_only.get('win_rate', 0.15)
        
        expected_combo = (track_rate * distance_rate) / 0.15
        strength = win_rate - expected_combo
        
        return {
            'interaction_strength': float(strength),
            'win_rate_combo': float(win_rate),
            'avg_position_combo': float(avg_position),
            'races_at_combo': len(results)
        }
    
    def analyze_class_distance_interaction(
        self,
        horse_name: str,
        race_class: str,
        distance: str
    ) -> Dict:
        """
        Analyze how horse performs at specific class-distance combination.
        """
        try:
            results = self.data.get_horse_class_distance_results(
                horse_name, race_class, distance
            )
        except (AttributeError, NotImplementedError):
            return {
                'class_distance_strength': 0.0,
                'win_rate': 0.0,
                'races': 0
            }
        
        if not results:
            return {
                'class_distance_strength': 0.0,
                'win_rate': 0.0,
                'races': 0
            }
        
        # Convert positions to integers (database returns strings)
        positions = []
        for r in results:
            if r['position']:
                try:
                    positions.append(int(r['position']))
                except (ValueError, TypeError):
                    continue
        
        if not positions:
            return {
                'class_distance_strength': 0.0,
                'win_rate': 0.0,
                'races': len(results)
            }
        
        win_rate = sum(1 for p in positions if p == 1) / len(positions)
        
        try:
            class_only = self.data.get_horse_class_performance(horse_name, race_class)
        except (AttributeError, NotImplementedError):
            class_only = {'win_rate': 0.15}
        
        distance_only = self.data.get_horse_distance_performance(horse_name, distance)
        
        class_rate = class_only.get('win_rate', 0.15)
        distance_rate = distance_only.get('win_rate', 0.15)
        
        expected = (class_rate + distance_rate) / 2
        strength = win_rate - expected
        
        return {
            'class_distance_strength': float(strength),
            'win_rate': float(win_rate),
            'races': len(results)
        }
    
    def get_interaction_adjustment(
        self,
        horse_name: str,
        track: str,
        distance: str,
        race_class: str
    ) -> float:
        """
        Get combined probability adjustment for all interactions.
        
        Returns multiplier to apply to base win probability.
        """
        track_distance = self.analyze_track_distance_interaction(
            horse_name, track, distance
        )
        class_distance = self.analyze_class_distance_interaction(
            horse_name, race_class, distance
        )
        
        adjustment = 1.0
        
        if track_distance['interaction_strength'] > 0.05:
            adjustment *= 1.08
        elif track_distance['interaction_strength'] < -0.05:
            adjustment *= 0.92
        
        if class_distance['class_distance_strength'] > 0.05:
            adjustment *= 1.08
        elif class_distance['class_distance_strength'] < -0.05:
            adjustment *= 0.92
        
        return adjustment


class DrawBiasAnalyzer:
    """Analyzes draw position bias for different race classes."""
    
    def __init__(self, data_integrator):
        """Initialize with data integrator."""
        self.data = data_integrator
    
    def analyze_draw_bias_by_class(self, race_class: str) -> Dict[int, Dict]:
        """
        Analyze draw position success rates for a specific race class.
        
        Returns win rate, place rate, and sample size for each draw position.
        """
        try:
            results = self.data.get_draw_performance_by_class(race_class)
        except (AttributeError, NotImplementedError):
            return {}
        
        draw_stats = defaultdict(lambda: {'wins': 0, 'races': 0, 'places': 0})
        
        for result in results:
            draw = result.get('draw')
            position = result.get('position')
            
            if draw is None or position is None:
                continue
            
            # Convert position to integer (database returns string)
            try:
                position = int(position)
            except (ValueError, TypeError):
                continue
            
            draw_stats[draw]['races'] += 1
            
            if position == 1:
                draw_stats[draw]['wins'] += 1
            
            if position <= 3:
                draw_stats[draw]['places'] += 1
        
        draw_analysis = {}
        for draw, stats in draw_stats.items():
            if stats['races'] > 0:
                draw_analysis[draw] = {
                    'win_rate': stats['wins'] / stats['races'],
                    'place_rate': stats['places'] / stats['races'],
                    'sample_size': stats['races'],
                    'bias_strength': (stats['wins'] / stats['races']) - 0.1
                }
        
        return draw_analysis
    
    def get_draw_advantage(
        self,
        draw: int,
        race_class: str,
        field_size: int
    ) -> float:
        """
        Get probability adjustment for draw position in a specific class.
        
        Returns multiplier for draw advantage/disadvantage.
        """
        draw_bias = self.analyze_draw_bias_by_class(race_class)
        
        if draw not in draw_bias or draw_bias[draw]['sample_size'] < 10:
            return 1.0
        
        bias_strength = draw_bias[draw]['bias_strength']
        
        if bias_strength > 0.05:
            return 1.125
        elif bias_strength < -0.05:
            return 0.85
        else:
            return 1.0
    
    def get_draw_ranking_by_class(self, race_class: str) -> List[int]:
        """
        Get ranked list of draws from best to worst for a race class.
        """
        draw_analysis = self.analyze_draw_bias_by_class(race_class)
        
        ranked = sorted(
            draw_analysis.items(),
            key=lambda x: x[1]['win_rate'],
            reverse=True
        )
        
        return [draw for draw, _ in ranked]


class FeatureInteractionOptimizer:
    """Combines all feature interactions into comprehensive adjustments."""
    
    def __init__(self, data_integrator):
        """Initialize with data integrator."""
        self.data = data_integrator
        self.jockey_trainer = JockeyTrainerSynergy(data_integrator)
        self.track_distance = TrackDistanceClassInteraction(data_integrator)
        self.draw_bias = DrawBiasAnalyzer(data_integrator)
    
    def calculate_interaction_adjustments(
        self,
        horse_name: str,
        jockey: str,
        trainer: str,
        track: str,
        distance: str,
        race_class: str,
        draw: int,
        field_size: int
    ) -> Dict:
        """
        Calculate all interaction-based probability adjustments.
        
        Returns comprehensive dictionary of adjustments and their combinations.
        """
        jockey_trainer_adj = self.jockey_trainer.get_synergy_adjustment(jockey, trainer)
        
        interaction_adj = self.track_distance.get_interaction_adjustment(
            horse_name, track, distance, race_class
        )
        
        draw_adj = self.draw_bias.get_draw_advantage(draw, race_class, field_size)
        
        combined_multiplier = jockey_trainer_adj * interaction_adj * draw_adj
        
        return {
            'jockey_trainer_synergy': jockey_trainer_adj,
            'track_distance_interaction': interaction_adj,
            'draw_bias_adjustment': draw_adj,
            'combined_multiplier': combined_multiplier,
            'combined_probability_adjustment_pct': (combined_multiplier - 1.0) * 100
        }
