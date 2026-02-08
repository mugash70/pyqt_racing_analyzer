"""Comprehensive risk evaluation for horses."""

from typing import Dict, List, Tuple
from datetime import datetime, timedelta
import numpy as np
from .data_integrator import DataIntegrator


class RiskAssessor:
    """Evaluates comprehensive risk factors for horses."""
    
    def __init__(self, data_integrator: DataIntegrator):
        """Initialize with data integrator."""
        self.data = data_integrator
    
    def assess_first_up_risk(self, horse_name: str, race_date: str) -> Dict:
        """
        Assess first-up risk after layoff.
        
        Returns: risk level, layoff days, first-up performance.
        """
        results = self.data.get_horse_race_results(horse_name, limit=5)
        
        if not results:
            return {
                'risk_level': 'Unknown',
                'severity': 'high',
                'layoff_days': 0,
                'first_up_win_rate': 0.0
            }
        
        try:
            last_race_date = datetime.strptime(results[0]['race_date'], '%Y-%m-%d')
            current_date = datetime.strptime(race_date, '%Y-%m-%d')
            layoff_days = (current_date - last_race_date).days
        except (ValueError, TypeError):
            layoff_days = 0
        
        if layoff_days > 60:
            risk_level = 'High'
            severity = 'high'
        elif layoff_days > 30:
            risk_level = 'Medium'
            severity = 'medium'
        else:
            risk_level = 'Low'
            severity = 'low'
        
        return {
            'risk_level': risk_level,
            'severity': severity,
            'layoff_days': layoff_days,
            'first_up_win_rate': 0.0
        }
    
    def assess_weight_carry_risk(self, weight: str, track: str) -> Dict:
        """
        Assess weight carrying risk.
        
        Returns: risk level, capacity rating.
        """
        try:
            weight_val = float(weight.split()[-1]) if weight else 120
        except (ValueError, IndexError):
            weight_val = 120
        
        if track == 'ST':
            threshold_high = 135
            threshold_medium = 130
        else:
            threshold_high = 132
            threshold_medium = 128
        
        if weight_val >= threshold_high:
            return {
                'risk_level': 'High',
                'severity': 'high',
                'weight': weight_val,
                'capacity_rating': 'Overloaded'
            }
        elif weight_val >= threshold_medium:
            return {
                'risk_level': 'Medium',
                'severity': 'medium',
                'weight': weight_val,
                'capacity_rating': 'Heavy'
            }
        else:
            return {
                'risk_level': 'Low',
                'severity': 'low',
                'weight': weight_val,
                'capacity_rating': 'Comfortable'
            }
    
    def assess_draw_risk(self, draw: int, distance: str, track: str) -> Dict:
        """
        Assess barrier/draw position risk.
        
        Returns: risk level, position advantage/disadvantage.
        """
        # Ensure draw_val is an integer
        try:
            draw_val = int(draw) if draw is not None else 8
        except (ValueError, TypeError):
            draw_val = 8
        
        if track == 'ST':
            if distance in ['1000m', '1200m']:
                favorable_range = (2, 7)
            elif distance in ['1400m', '1600m']:
                favorable_range = (3, 8)
            else:
                favorable_range = (4, 9)
        else:
            favorable_range = (2, 6)
        
        if favorable_range[0] <= draw_val <= favorable_range[1]:
            return {
                'risk_level': 'Low',
                'severity': 'low',
                'draw': draw_val,
                'advantage': 'Favorable position'
            }
        elif 1 <= draw_val <= 2 or draw_val >= 12:
            return {
                'risk_level': 'High',
                'severity': 'high',
                'draw': draw_val,
                'advantage': 'Unfavorable position'
            }
        else:
            return {
                'risk_level': 'Medium',
                'severity': 'medium',
                'draw': draw_val,
                'advantage': 'Neutral position'
            }
    
    def assess_veterinary_risk(self, horse_name: str) -> Dict:
        """
        Assess veterinary and health risk.
        
        Returns: risk level, health status.
        """
        vet_records = self.data.get_veterinary_records(horse_name)
        
        if not vet_records:
            return {
                'risk_level': 'Low',
                'severity': 'low',
                'health_status': 'Clear',
                'recent_issues': []
            }
        
        recent_records = vet_records[:3]
        
        issues = []
        for record in recent_records:
            if record['details']:
                issues.append(record['details'])
        
        if issues:
            return {
                'risk_level': 'High',
                'severity': 'high',
                'health_status': 'Concerns detected',
                'recent_issues': issues
            }
        
        return {
            'risk_level': 'Low',
            'severity': 'low',
            'health_status': 'Clear',
            'recent_issues': []
        }
    
    def assess_form_decline_risk(self, horse_name: str) -> Dict:
        """
        Assess form decline risk.
        
        Returns: risk level, form trend.
        """
        results = self.data.get_horse_race_results(horse_name, limit=15)
        
        if len(results) < 5:
            return {
                'risk_level': 'Medium',
                'severity': 'medium',
                'form_trend': 'Insufficient data',
                'decline_rate': 0.0
            }
        
        recent_avg = np.mean([r['position'] for r in results[:5] if r['position']])
        older_avg = np.mean([r['position'] for r in results[5:10] if r['position']])
        
        decline_rate = recent_avg - older_avg
        
        if decline_rate > 3:
            return {
                'risk_level': 'High',
                'severity': 'high',
                'form_trend': 'Sharp decline',
                'decline_rate': float(decline_rate)
            }
        elif decline_rate > 1:
            return {
                'risk_level': 'Medium',
                'severity': 'medium',
                'form_trend': 'Gradual decline',
                'decline_rate': float(decline_rate)
            }
        else:
            return {
                'risk_level': 'Low',
                'severity': 'low',
                'form_trend': 'Stable or improving',
                'decline_rate': float(decline_rate)
            }
    
    def assess_track_unfamiliar_risk(self, horse_name: str, track: str) -> Dict:
        """
        Assess risk of racing at unfamiliar track.
        
        Returns: risk level, track experience.
        """
        track_perf = self.data.get_horse_track_performance(horse_name, track)
        
        races_at_track = track_perf['total_races']
        
        if races_at_track == 0:
            return {
                'risk_level': 'High',
                'severity': 'high',
                'track_experience': 'None',
                'races_at_track': 0
            }
        elif races_at_track < 3:
            return {
                'risk_level': 'Medium',
                'severity': 'medium',
                'track_experience': 'Limited',
                'races_at_track': races_at_track
            }
        else:
            return {
                'risk_level': 'Low',
                'severity': 'low',
                'track_experience': 'Experienced',
                'races_at_track': races_at_track
            }
    
    def assess_distance_unfamiliar_risk(self, horse_name: str, distance: str) -> Dict:
        """
        Assess risk of unfamiliar race distance.
        
        Returns: risk level, distance experience.
        """
        dist_perf = self.data.get_horse_distance_performance(horse_name, distance)
        
        races_at_distance = dist_perf['total_races']
        
        if races_at_distance == 0:
            return {
                'risk_level': 'High',
                'severity': 'high',
                'distance_experience': 'None',
                'races_at_distance': 0
            }
        elif races_at_distance < 2:
            return {
                'risk_level': 'Medium',
                'severity': 'medium',
                'distance_experience': 'Limited',
                'races_at_distance': races_at_distance
            }
        else:
            return {
                'risk_level': 'Low',
                'severity': 'low',
                'distance_experience': 'Experienced',
                'races_at_distance': races_at_distance
            }
    
    def calculate_overall_risk_score(self, horse_name: str, race_date: str, 
                                     track: str, distance: str, draw: int, 
                                     weight: str) -> Tuple[float, str]:
        """
        Calculate overall risk score (0-100, higher = more risk).
        
        Returns: risk score, recommendation.
        """
        first_up = self.assess_first_up_risk(horse_name, race_date)
        weight_risk = self.assess_weight_carry_risk(weight, track)
        draw_risk = self.assess_draw_risk(draw, distance, track)
        vet_risk = self.assess_veterinary_risk(horse_name)
        form_risk = self.assess_form_decline_risk(horse_name)
        track_risk = self.assess_track_unfamiliar_risk(horse_name, track)
        distance_risk = self.assess_distance_unfamiliar_risk(horse_name, distance)
        
        severity_mapping = {'low': 1, 'medium': 3, 'high': 5}
        
        risk_score = (
            severity_mapping.get(first_up['severity'], 3) * 0.15 +
            severity_mapping.get(weight_risk['severity'], 3) * 0.15 +
            severity_mapping.get(draw_risk['severity'], 3) * 0.10 +
            severity_mapping.get(vet_risk['severity'], 3) * 0.15 +
            severity_mapping.get(form_risk['severity'], 3) * 0.20 +
            severity_mapping.get(track_risk['severity'], 3) * 0.15 +
            severity_mapping.get(distance_risk['severity'], 3) * 0.10
        )
        
        risk_score = (risk_score / 5) * 100
        
        if risk_score < 30:
            recommendation = 'Low risk - Good prospect'
        elif risk_score < 60:
            recommendation = 'Moderate risk - Proceed with caution'
        else:
            recommendation = 'High risk - Avoid or reduce exposure'
        
        return float(risk_score), recommendation
    
    def create_risk_profile(self, horse_name: str, race_date: str, track: str, 
                           distance: str, draw: int, weight: str) -> Dict:
        """
        Create comprehensive risk profile for a horse.
        """
        risk_score, recommendation = self.calculate_overall_risk_score(
            horse_name, race_date, track, distance, draw, weight
        )
        
        return {
            'horse_name': horse_name,
            'overall_risk_score': risk_score,
            'recommendation': recommendation,
            'first_up_risk': self.assess_first_up_risk(horse_name, race_date),
            'weight_carry_risk': self.assess_weight_carry_risk(weight, track),
            'draw_risk': self.assess_draw_risk(draw, distance, track),
            'veterinary_risk': self.assess_veterinary_risk(horse_name),
            'form_decline_risk': self.assess_form_decline_risk(horse_name),
            'track_unfamiliar_risk': self.assess_track_unfamiliar_risk(horse_name, track),
            'distance_unfamiliar_risk': self.assess_distance_unfamiliar_risk(horse_name, distance)
        }
