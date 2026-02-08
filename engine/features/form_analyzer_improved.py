"""Improved form analysis with recency weighting, acceleration detection, and class progression."""

from typing import Dict, List, Optional, Tuple
import numpy as np
from datetime import datetime, timedelta


class ImprovedFormAnalyzer:
    """Enhanced form analyzer with recency weighting and acceleration detection."""
    
    def __init__(self, data_integrator):
        """Initialize with data integrator."""
        self.data = data_integrator
    
    def _parse_position(self, pos_str: any) -> Optional[int]:
        """Extract numeric position from string (handles '3 平頭馬' etc)."""
        if pos_str is None:
            return None
        if isinstance(pos_str, int):
            return pos_str
        
        import re
        try:
            # Match first sequence of digits
            match = re.search(r'\d+', str(pos_str))
            if match:
                return int(match.group())
            return None
        except:
            return None

    def analyze_recent_form_weighted(self, horse_name: str, races: int = 10) -> Dict:
        """
        Analyze form with recency weighting (recent races worth 3-5x more).
        
        Uses exponential decay: weight = e^(race_index/decay_rate)
        """
        results = self.data.get_horse_race_results(horse_name, limit=races)
        
        if not results:
            return {
                'form_trend': 'No form',
                'consistency': 0.0,
                'momentum': 0.0,
                'weighted_avg_position': None,
                'recent_races': [],
                'recency_score': 0.0
            }
        
        positions = []
        for r in results:
            pos = self._parse_position(r.get('position'))
            if pos is not None:
                positions.append(pos)
        
        if not positions:
            return {
                'form_trend': 'No form',
                'consistency': 0.0,
                'momentum': 0.0,
                'weighted_avg_position': None,
                'recent_races': [],
                'recency_score': 0.0
            }
        
        weights = self._calculate_recency_weights(len(positions), decay_rate=2.0)
        weighted_positions = np.average(positions, weights=weights)
        
        consistency = 100 - (np.std(positions) * 10)
        momentum = int(positions[0]) - int(positions[-1])
        
        if momentum < -2:
            trend = 'Improving'
        elif momentum > 2:
            trend = 'Declining'
        else:
            trend = 'Steady'
        
        recency_score = self._calculate_recency_score(positions)
        
        return {
            'form_trend': trend,
            'consistency': float(max(0, min(100, consistency))),
            'momentum': float(momentum),
            'weighted_avg_position': float(weighted_positions),
            'recent_races': positions,
            'recency_score': float(recency_score)
        }
    
    def detect_form_acceleration(self, horse_name: str, races: int = 10) -> Dict:
        """
        Detect if horse is accelerating (improving) or decelerating (declining).
        
        Compares form over different periods to identify acceleration/deceleration rate.
        """
        results = self.data.get_horse_race_results(horse_name, limit=races)
        
        if not results or len(results) < 4:
            return {
                'acceleration_rate': 0.0,
                'acceleration_trend': 'Insufficient data',
                'velocity': 0.0,
                'acceleration_confidence': 0.0
            }
        
        positions = []
        for r in results:
            pos = self._parse_position(r.get('position'))
            if pos is not None:
                positions.append(pos)
        
        if len(positions) < 4:
            return {
                'acceleration_rate': 0.0,
                'acceleration_trend': 'Insufficient data',
                'velocity': 0.0,
                'acceleration_confidence': 0.0
            }
        
        mid_point = len(positions) // 2
        first_half = positions[mid_point:]
        second_half = positions[:mid_point]
        
        first_half_avg = np.mean(first_half)
        second_half_avg = np.mean(second_half)
        
        acceleration = first_half_avg - second_half_avg
        
        velocity = positions[0] - positions[-1]
        
        if acceleration < -1.5:
            trend = 'Accelerating (Improving)'
        elif acceleration > 1.5:
            trend = 'Decelerating (Declining)'
        else:
            trend = 'Stable'
        
        consistency_std = np.std(positions)
        confidence = 1.0 - (consistency_std / 10)
        confidence = float(max(0, min(1, confidence)))
        
        return {
            'acceleration_rate': float(acceleration),
            'acceleration_trend': trend,
            'velocity': float(velocity),
            'acceleration_confidence': confidence
        }
    
    def analyze_class_progression(self, horse_name: str) -> Dict:
        """
        Analyze how horse performs at different class levels.
        
        Identifies performance patterns at each class and progression trajectory.
        """
        results = self.data.get_horse_race_results(horse_name, limit=50)
        
        if not results:
            return {
                'class_progression': 'Unknown',
                'current_class_performance': None,
                'class_trend': None,
                'class_suitability': 0.0
            }
        
        class_performance = {}
        for result in results:
            race_class = result.get('race_class', 'Unknown')
            position = self._parse_position(result.get('position'))
            
            if race_class not in class_performance:
                class_performance[race_class] = []
            
            if position is not None:
                class_performance[race_class].append(position)
        
        if not class_performance:
            return {
                'class_progression': 'Unknown',
                'current_class_performance': None,
                'class_trend': None,
                'class_suitability': 0.0
            }
        
        class_averages = {}
        for race_class, positions in class_performance.items():
            class_averages[race_class] = np.mean(positions)
        
        current_result = results[0]
        current_class = current_result.get('race_class', 'Unknown')
        current_performance = class_averages.get(current_class)
        
        progression = self._determine_class_progression(
            list(class_averages.values()),
            class_averages.get(current_class, 0)
        )
        
        class_suitability = self._calculate_class_suitability(
            current_class,
            current_performance,
            class_averages
        )
        
        return {
            'class_progression': progression,
            'current_class_performance': float(current_performance) if current_performance else None,
            'class_trend': self._determine_trend(list(class_averages.values())),
            'class_suitability': class_suitability
        }
    
    def combined_form_analysis(self, horse_name: str, jockey_name: Optional[str] = None, trainer_name: Optional[str] = None) -> Dict:
        """
        Combine all form analyses into a comprehensive score.

        For future races without historical data, uses jockey/trainer performance as proxy.
        Weights: Recency (40%), Acceleration (30%), Class Progression (30%)
        """
        weighted_form = self.analyze_recent_form_weighted(horse_name)
        acceleration = self.detect_form_acceleration(horse_name)
        class_analysis = self.analyze_class_progression(horse_name)

        recency_score = weighted_form['recency_score']
        acceleration_score = max(0, 50 + acceleration['acceleration_rate'] * 10)
        class_score = class_analysis['class_suitability']

        # If no historical data, use jockey/trainer performance as proxy
        if recency_score == 0.0 and acceleration_score == 50.0 and class_score == 0.0:
            # No historical form data - use jockey/trainer stats as proxy
            base_form_score = 30.0  # Base score for horses with no form history

            if jockey_name:
                # Get jockey's recent performance as proxy for horse's form
                try:
                    jockey_stats = self.data.get_jockey_stats(jockey_name)
                    jockey_form_modifier = (jockey_stats['win_rate'] - 12) * 2  # +/- 24 points
                    base_form_score += jockey_form_modifier
                except:
                    pass

            if trainer_name:
                try:
                    trainer_stats = self.data.get_trainer_stats(trainer_name)
                    trainer_form_modifier = (trainer_stats['win_rate'] - 13) * 1.5  # +/- 18 points
                    base_form_score += trainer_form_modifier
                except:
                    pass

            # Distribute the form score across components
            combined_score = float(max(10, min(70, base_form_score)))
            recency_score = combined_score * 0.4
            acceleration_score = combined_score * 0.75  # Acceleration component
            class_score = combined_score * 0.5  # Class component
        else:
            # Normal calculation with historical data
            combined_score = (
                recency_score * 0.4 +
                acceleration_score * 0.3 +
                class_score * 0.3
            )

        return {
            'combined_form_score': float(combined_score),
            'recency_component': float(recency_score),
            'acceleration_component': float(acceleration_score),
            'class_component': float(class_score),
            'weighted_form': weighted_form,
            'acceleration': acceleration,
            'class_analysis': class_analysis
        }
    
    @staticmethod
    def _calculate_recency_weights(num_races: int, decay_rate: float = 2.0) -> np.ndarray:
        """
        Calculate exponential weights for recency.
        
        Most recent race gets highest weight, older races get progressively less.
        """
        indices = np.arange(num_races)
        weights = np.exp(indices / decay_rate)
        weights = weights / weights.sum()
        return weights
    
    @staticmethod
    def _calculate_recency_score(positions: List[int]) -> float:
        """
        Calculate recency score based on recent form.
        
        Prioritizes last 3 races heavily.
        """
        if not positions:
            return 0.0
        
        last_three = positions[:3]
        
        if len(positions) > 0:
            recent_weight = 3.0 / len(last_three) if last_three else 0
            avg_recent = np.mean(last_three)
            
            score = 100 - (avg_recent * 10)
            score = max(0, min(100, score * recent_weight))
            
            return float(score)
        
        return 0.0
    
    @staticmethod
    def _determine_class_progression(class_avgs: List[float], current_avg: float) -> str:
        """Determine if horse is progressing to higher classes (lower avg position)."""
        if not class_avgs or current_avg is None:
            return 'Unknown'
        
        sorted_avgs = sorted(class_avgs)
        
        if current_avg <= sorted_avgs[0]:
            return 'Class Rising (Elite)'
        elif current_avg <= sorted_avgs[len(sorted_avgs) // 2]:
            return 'Class Rising'
        elif current_avg >= sorted_avgs[-1]:
            return 'Class Declining'
        else:
            return 'Class Stable'
    
    @staticmethod
    def _determine_trend(values: List[float]) -> str:
        """Determine trend from values."""
        if len(values) < 2:
            return 'Insufficient data'
        
        if values[0] < values[-1]:
            return 'Improving'
        elif values[0] > values[-1]:
            return 'Declining'
        else:
            return 'Stable'
    
    @staticmethod
    def _calculate_class_suitability(current_class: str, current_perf: Optional[float],
                                     class_avgs: Dict[str, float]) -> float:
        """
        Calculate how suitable the current class is for the horse.
        
        Score of 100 = best class for this horse.
        """
        if not class_avgs or current_perf is None:
            return 50.0
        
        avgs = list(class_avgs.values())
        best_avg = min(avgs)
        worst_avg = max(avgs)
        
        if best_avg == worst_avg:
            return 50.0
        
        suitability = 100 - ((current_perf - best_avg) / (worst_avg - best_avg)) * 100
        
        return float(max(0, min(100, suitability)))
