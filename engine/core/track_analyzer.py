"""Track-specific analysis for Sha Tin (ST) and Happy Valley (HV)."""

from typing import Dict, List, Optional
import numpy as np
from .data_integrator import DataIntegrator


class TrackAnalyzer:
    """Analyzes horse performance at specific tracks."""
    
    def __init__(self, data_integrator: DataIntegrator):
        """Initialize with data integrator."""
        self.data = data_integrator
    
    def analyze_st_suitability(self, horse_name: str, jockey_name: Optional[str] = None, trainer_name: Optional[str] = None) -> Dict:
        """
        Analyze Sha Tin suitability.

        Returns: distance preference, running style fit, draw impact.
        For future races, uses jockey/trainer performance as proxy.
        """
        st_perf = self.data.get_horse_track_performance(horse_name, 'ST')

        if st_perf['total_races'] < 3:
            # No historical ST data - use jockey/trainer performance as proxy
            base_running_style = 50.0
            base_draw_impact = 50.0

            if jockey_name:
                jockey_stats = self.data.get_jockey_stats(jockey_name)
                jockey_modifier = (jockey_stats['win_rate'] - 10) * 0.8  # +/- 32 points
                base_running_style += jockey_modifier
                base_draw_impact += jockey_modifier * 0.5

            if trainer_name:
                trainer_stats = self.data.get_trainer_stats(trainer_name)
                trainer_modifier = (trainer_stats['win_rate'] - 12) * 0.6  # +/- 24 points
                base_running_style += trainer_modifier
                base_draw_impact += trainer_modifier * 0.4

            return {
                'distance_preference': 'Unknown',
                'running_style_fit': float(max(30, min(80, base_running_style))),
                'draw_impact': float(max(35, min(75, base_draw_impact))),
                'recommendation': 'Limited ST experience'
            }

        win_rate = st_perf['win_rate']

        running_style = 75.0 if win_rate > 15 else 50.0
        draw_impact = 65.0 if st_perf['total_races'] > 5 else 55.0

        return {
            'distance_preference': 'Long straights (1200m+)',
            'running_style_fit': float(running_style),
            'draw_impact': float(draw_impact),
            'win_rate_st': float(win_rate),
            'total_races_st': st_perf['total_races']
        }
    
    def calculate_st_stamina_index(self, horse_name: str) -> float:
        """
        Calculate Sha Tin stamina index (0-100).
        
        Based on long straight performance and sustained speed.
        """
        st_perf = self.data.get_horse_track_performance(horse_name, 'ST')
        
        if st_perf['total_races'] == 0:
            return 50.0
        
        place_rate = st_perf['place_rate']
        stamina_score = (place_rate * 0.7) + 30
        
        return float(max(0, min(100, stamina_score)))
    
    def assess_st_weather_adaptation(self, horse_name: str) -> Dict:
        """
        Assess weather adaptation for Sha Tin.
        
        Returns: wet/dry track performance, temperature effect.
        """
        results = self.data.get_horse_race_results(horse_name, limit=20)
        
        st_results = [r for r in results if r['racecourse'] == 'ST']
        
        if not st_results:
            return {
                'wet_track_score': 50.0,
                'dry_track_score': 50.0,
                'temperature_sensitivity': 0.0
            }
        
        good_weather_score = 70.0
        wet_weather_score = 60.0
        
        return {
            'wet_track_score': float(wet_weather_score),
            'dry_track_score': float(good_weather_score),
            'temperature_sensitivity': 0.0
        }
    
    def analyze_hv_suitability(self, horse_name: str) -> Dict:
        """
        Analyze Happy Valley suitability.
        
        Returns: tight turn handling, acceleration, draw criticality.
        """
        hv_perf = self.data.get_horse_track_performance(horse_name, 'HV')
        
        if hv_perf['total_races'] < 3:
            return {
                'tight_turn_handling': 50.0,
                'acceleration': 50.0,
                'draw_criticality': 'Moderate',
                'recommendation': 'Limited HV experience'
            }
        
        win_rate = hv_perf['win_rate']
        place_rate = hv_perf['place_rate']
        
        turn_handling = 60.0 if win_rate > 12 else 45.0
        acceleration = 70.0 if place_rate > 40 else 55.0
        
        return {
            'tight_turn_handling': float(turn_handling),
            'acceleration': float(acceleration),
            'draw_criticality': 'High' if hv_perf['total_races'] >= 5 else 'Moderate',
            'win_rate_hv': float(win_rate),
            'place_rate_hv': float(place_rate),
            'total_races_hv': hv_perf['total_races']
        }
    
    def calculate_hv_tactical_speed(self, horse_name: str) -> float:
        """
        Calculate Happy Valley tactical speed index (0-100).
        
        Based on quick acceleration and position tactical awareness.
        """
        hv_perf = self.data.get_horse_track_performance(horse_name, 'HV')
        
        if hv_perf['total_races'] == 0:
            return 50.0
        
        win_rate = hv_perf['win_rate']
        
        tactical_speed = (win_rate * 2) + 50
        
        return float(max(0, min(100, tactical_speed)))
    
    def identify_valley_specialist(self, horse_name: str) -> bool:
        """
        Identify if horse is a consistent Happy Valley specialist.
        
        Returns: True if consistently performs well at HV.
        """
        hv_perf = self.data.get_horse_track_performance(horse_name, 'HV')
        
        if hv_perf['total_races'] < 5:
            return False
        
        is_specialist = hv_perf['win_rate'] > 15
        
        return is_specialist
    
    def get_track_specialized_score(self, horse_name: str, track: str, jockey_name: Optional[str] = None, trainer_name: Optional[str] = None) -> float:
        """
        Get track-specialized performance score (0-100).

        Combines all track-specific metrics.
        For future races, uses jockey/trainer performance when horse data unavailable.
        """
        if track == 'ST':
            suitability = self.analyze_st_suitability(horse_name, jockey_name, trainer_name)
            stamina = self.calculate_st_stamina_index(horse_name)

            if 'running_style_fit' in suitability:
                score = (suitability['running_style_fit'] * 0.4 +
                        suitability['draw_impact'] * 0.3 +
                        stamina * 0.3)
            else:
                score = 50.0

        elif track == 'HV':
            suitability = self.analyze_hv_suitability(horse_name)
            tactical = self.calculate_hv_tactical_speed(horse_name)

            if 'tight_turn_handling' in suitability:
                score = (suitability['tight_turn_handling'] * 0.35 +
                        suitability['acceleration'] * 0.35 +
                        tactical * 0.3)
            else:
                score = 50.0
        else:
            score = 50.0

        return float(score)
    
    def compare_track_suitability(self, horse_name: str) -> Dict:
        """
        Compare horse's suitability across both tracks.
        
        Returns: comparative analysis with preferred track.
        """
        st_score = self.get_track_specialized_score(horse_name, 'ST')
        hv_score = self.get_track_specialized_score(horse_name, 'HV')
        
        preferred = 'ST' if st_score >= hv_score else 'HV'
        preference_strength = abs(st_score - hv_score)
        
        return {
            'st_score': float(st_score),
            'hv_score': float(hv_score),
            'preferred_track': preferred,
            'preference_strength': float(preference_strength),
            'difference_ratio': float(st_score / (hv_score + 0.1))
        }
    
    def create_track_profile(self, horse_name: str) -> Dict:
        """
        Create comprehensive track profile for a horse.
        """
        return {
            'horse_name': horse_name,
            'st_analysis': self.analyze_st_suitability(horse_name),
            'st_stamina': self.calculate_st_stamina_index(horse_name),
            'st_weather': self.assess_st_weather_adaptation(horse_name),
            'hv_analysis': self.analyze_hv_suitability(horse_name),
            'hv_tactical_speed': self.calculate_hv_tactical_speed(horse_name),
            'hv_specialist': self.identify_valley_specialist(horse_name),
            'comparison': self.compare_track_suitability(horse_name)
        }
