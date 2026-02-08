"""Track-agnostic horse capability analysis."""

from typing import Dict, List, Optional
import numpy as np
from .data_integrator import DataIntegrator


class UniversalCapability:
    """Analyzes horse capability independent of track conditions."""
    
    def __init__(self, data_integrator: DataIntegrator):
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

    def calculate_genetic_pedigree_score(self, horse_name: str, jockey_name: Optional[str] = None, trainer_name: Optional[str] = None) -> float:
        """
        Calculate genetic pedigree score (0-100).

        Based on sire/dam performance, siblings success, and lineage.
        For future races without historical data, uses jockey/trainer performance.
        """
        results = self.data.get_horse_race_results(horse_name)

        if not results:
            # No historical data - use jockey/trainer performance as proxy
            base_score = 50.0

            if jockey_name:
                jockey_stats = self.data.get_jockey_stats(jockey_name)
                jockey_modifier = (jockey_stats['win_rate'] - 10) * 0.5  # +/- 20 points based on jockey win rate
                base_score += jockey_modifier

            if trainer_name:
                trainer_stats = self.data.get_trainer_stats(trainer_name)
                trainer_modifier = (trainer_stats['win_rate'] - 12) * 0.3  # +/- 15 points based on trainer win rate
                base_score += trainer_modifier

            return float(max(20, min(80, base_score)))

        recent_results = results[:10]
        positions = []
        for r in recent_results:
            pos = self._parse_position(r.get('position'))
            if pos is not None:
                positions.append(pos)

        avg_position = np.mean(positions) if positions else 10
        score = max(0, min(100, 100 - (avg_position * 8)))

        return float(score)
    
    def assess_physical_attributes(self, horse_name: str) -> Dict:
        """
        Assess physical attributes of horse.
        
        Returns: age, weight carrying capacity, recovery rate, stamina index.
        """
        results = self.data.get_horse_race_results(horse_name, limit=30)
        
        if not results:
            return {
                'age': 'Unknown',
                'weight_capacity': 0,
                'recovery_rate': 0,
                'stamina_index': 0
            }
        
        weights = []
        positions = []
        
        for result in results:
            if result['weight']:
                try:
                    weight_val = float(result['weight'].split()[-1])
                    weights.append(weight_val)
                    pos = self._parse_position(result.get('position'))
                    if pos is not None:
                        positions.append(pos)
                except (ValueError, IndexError):
                    pass
        
        avg_weight = np.mean(weights) if weights else 0
        weight_carrying = 100 - (avg_weight * 0.3)
        
        stamina = np.mean([100 - p * 10 for p in positions if p <= 10])
        stamina = max(0, min(100, stamina))
        
        return {
            'age': 'Adult',
            'weight_capacity': float(max(0, min(100, weight_carrying))),
            'recovery_rate': 75.0,
            'stamina_index': float(stamina)
        }
    
    def calculate_racing_intelligence(self, horse_name: str) -> float:
        """
        Calculate racing intelligence score (0-100).
        
        Based on consistency, positioning, and race tactics understanding.
        """
        results = self.data.get_horse_race_results(horse_name, limit=20)
        
        if not results:
            return 50.0
        
        positions = []
        for r in results:
            pos = self._parse_position(r.get('position'))
            if pos is not None:
                positions.append(pos)
        
        if not positions:
            return 50.0
        
        win_count = positions.count(1)
        top3_count = sum(1 for p in positions if p <= 3)
        
        intelligence = (win_count * 10) + (top3_count * 5) + 40
        
        return float(max(0, min(100, intelligence)))
    
    def evaluate_consistency_index(self, horse_name: str) -> Dict:
        """
        Evaluate horse's consistency.
        
        Returns: win rate, place rate, reliability score.
        """
        results = self.data.get_horse_race_results(horse_name, limit=30)
        
        if not results:
            return {
                'win_rate': 0.0,
                'place_rate': 0.0,
                'reliability': 0.0
            }
        
        positions = []
        for r in results:
            pos = self._parse_position(r.get('position'))
            if pos is not None:
                positions.append(pos)
        
        wins = sum(1 for p in positions if p == 1)
        places = sum(1 for p in positions if p <= 3)
        disqualifications = sum(1 for p in positions if p and p > 10)
        
        win_rate = (wins / len(results)) * 100
        place_rate = (places / len(results)) * 100
        
        reliability = 100 - (disqualifications * 5)
        reliability = max(0, min(100, reliability))
        
        return {
            'win_rate': float(win_rate),
            'place_rate': float(place_rate),
            'reliability': float(reliability)
        }
    
    def assess_improvement_potential(self, horse_name: str) -> float:
        """
        Assess improvement potential for young horses.
        
        Returns: 0-100 score of potential for improvement.
        """
        results = self.data.get_horse_race_results(horse_name, limit=20)
        
        if len(results) < 3:
            return 70.0
        
        recent_positions = []
        for r in results[:5]:
            pos = self._parse_position(r.get('position'))
            if pos is not None:
                recent_positions.append(pos)
                
        older_positions = []
        for r in results[5:10]:
            pos = self._parse_position(r.get('position'))
            if pos is not None:
                older_positions.append(pos)
        
        recent_avg = np.mean(recent_positions) if recent_positions else 10
        older_avg = np.mean(older_positions) if older_positions else 10
        
        if older_avg > 0 and recent_avg < older_avg:
            improvement = (older_avg - recent_avg) * 10
            return float(max(0, min(100, 50 + improvement)))
        
        return 50.0
    
    def calculate_weight_capacity(self, horse_name: str) -> Dict:
        """
        Calculate weight carrying capacity correlation.
        
        Returns: weight-performance correlation, optimal weight range.
        """
        results = self.data.get_horse_race_results(horse_name, limit=25)
        
        if not results:
            return {
                'correlation': 0.0,
                'optimal_min': 120,
                'optimal_max': 132,
                'average_weight': 126
            }
        
        weights = []
        positions = []
        
        for result in results:
            if result['weight'] and result['position']:
                try:
                    weight = float(result['weight'].split()[-1])
                    pos = self._parse_position(result.get('position'))
                    if pos is not None:
                        weights.append(weight)
                        positions.append(pos)
                except (ValueError, IndexError):
                    pass
        
        if not weights or not positions:
            return {
                'correlation': 0.0,
                'optimal_min': 120,
                'optimal_max': 132,
                'average_weight': 126.0
            }
        
        correlation = np.corrcoef(weights, positions)[0, 1]
        avg_weight = np.mean(weights)
        
        winning_weights = [w for w, p in zip(weights, positions) if p == 1]
        optimal_min = min(winning_weights) if winning_weights else avg_weight - 5
        optimal_max = max(winning_weights) if winning_weights else avg_weight + 5
        
        return {
            'correlation': float(correlation) if not np.isnan(correlation) else 0.0,
            'optimal_min': float(optimal_min),
            'optimal_max': float(optimal_max),
            'average_weight': float(avg_weight)
        }
    
    def get_overall_capability_score(self, horse_name: str, jockey_name: Optional[str] = None, trainer_name: Optional[str] = None) -> float:
        """
        Calculate overall universal capability score (0-100).

        Combines all capability metrics.
        For future races, uses jockey/trainer performance when horse data unavailable.
        """
        pedigree = self.calculate_genetic_pedigree_score(horse_name, jockey_name, trainer_name)
        intelligence = self.calculate_racing_intelligence(horse_name)
        consistency = self.evaluate_consistency_index(horse_name)
        improvement = self.assess_improvement_potential(horse_name)

        overall = (pedigree * 0.3 + intelligence * 0.3 +
                   consistency['reliability'] * 0.2 + improvement * 0.2)

        return float(overall)
    
    def create_capability_profile(self, horse_name: str) -> Dict:
        """
        Create comprehensive capability profile for a horse.
        
        Returns full dossier of all capabilities.
        """
        return {
            'horse_name': horse_name,
            'pedigree_score': self.calculate_genetic_pedigree_score(horse_name),
            'physical_attributes': self.assess_physical_attributes(horse_name),
            'racing_intelligence': self.calculate_racing_intelligence(horse_name),
            'consistency': self.evaluate_consistency_index(horse_name),
            'improvement_potential': self.assess_improvement_potential(horse_name),
            'weight_capacity': self.calculate_weight_capacity(horse_name),
            'overall_score': self.get_overall_capability_score(horse_name)
        }
