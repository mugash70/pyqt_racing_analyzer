"""Enhanced feature engineering using all 29 database tables."""

from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import logging
from collections import defaultdict
import sys
import os

logger = logging.getLogger(__name__)

# Handle imports for both module and direct execution
try:
    from ..core.data_integrator import DataIntegrator
except ImportError:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from core.data_integrator import DataIntegrator


class EnhancedFeatureEngineer:
    """Creates 100+ features from all database tables for superior predictions."""
    
    def __init__(self, data_integrator):
        """Initialize with data integrator."""
        self.data = data_integrator
        self._cache = {}
    
    def extract_all_enhanced_features(
        self,
        horse_name: str,
        horse_number: int,
        jockey: str,
        trainer: str,
        weight: str,
        draw: int,
        race_date: str,
        race_number: int,
        track: str,
        distance: str,
        race_class: str,
        current_odds: float,
        field_size: int = 14,
        gear: str = None
    ) -> Dict[str, Any]:
        """Extract comprehensive features from all available data sources."""
        
        features = {}
        
        # Core performance features
        features.update(self._extract_form_features(horse_name))
        features.update(self._extract_track_features(horse_name, track))
        features.update(self._extract_distance_features(horse_name, distance))
        features.update(self._extract_class_features(horse_name, race_class))
        features.update(self._extract_form_line_features(horse_name))
        features.update(self._extract_running_style_features(horse_name))
        
        # Human factors
        features.update(self._extract_jockey_features(jockey, track, distance, race_class))
        features.update(self._extract_trainer_features(trainer, track, distance, race_class))
        features.update(self._extract_jockey_trainer_synergy(jockey, trainer))
        
        # Race conditions
        features.update(self._extract_draw_features(draw, field_size, track, distance, race_class))
        features.update(self._extract_weight_features(horse_name, weight, track, distance))
        
        # Market signals
        features.update(self._extract_odds_features(current_odds, horse_name, race_date, race_number, track))
        
        # Additional data sources
        features.update(self._extract_pedigree_features(horse_name))
        features.update(self._extract_gear_features(gear, horse_name))
        features.update(self._extract_weather_features(race_date, track))
        features.update(self._extract_wind_features(race_date, track))
        features.update(self._extract_barrier_trial_features(horse_name))
        features.update(self._extract_trackwork_features(horse_name))
        features.update(self._extract_veterinary_features(horse_name))
        features.update(self._extract_injury_features(horse_name))
        features.update(self._extract_competition_features(horse_name, race_date))
        features.update(self._extract_rating_features(horse_name, race_date))
        features.update(self._extract_barrier_draw_features(draw, track, distance))
        features.update(self._extract_gear_statistics_features(gear))
        features.update(self._extract_last_race_summary_features(horse_name))
        features.update(self._extract_new_horse_features(horse_name))
        features.update(self._extract_professional_schedule_features(jockey, trainer, race_date, race_number))
        features.update(self._extract_race_info_features(race_date, race_number, track))
        features.update(self._extract_horse_info_features(horse_name))
        
        # Interactions and derived features
        features.update(self._extract_interaction_features(features, track, distance, race_class))
        
        # Add identifiers
        features['horse_name'] = horse_name
        features['horse_number'] = horse_number
        features['race_number'] = race_number
        features['track'] = track
        features['distance'] = distance
        features['race_class'] = race_class
        features['field_size'] = field_size
        
        return features
    
    def _extract_form_features(self, horse_name: str) -> Dict:
        """Extract comprehensive form features with recency weighting."""
        results = self.data.get_horse_race_results(horse_name, limit=20)
        
        if not results:
            return {
                'form_available': 0.0,
                'last_5_avg': 8.0,
                'last_10_avg': 8.0,
                'career_avg': 8.0,
                'win_rate': 0.0,
                'place_rate': 0.0,
                'consistency_score': 0.0,
                'form_trend': 0.0,
                'momentum_score': 50.0,
                'recent_win_rate': 0.0,
                'recent_place_rate': 0.0,
                'days_since_last_race': 999,
                'first_up_flag': 0.0,
                'second_up_flag': 0.0,
                'form_pattern': 'unknown'
            }
        
        positions = [r['position'] for r in results if r['position']]
        
        if not positions:
            return {'form_available': 0.0, 'last_5_avg': 8.0, 'last_10_avg': 8.0}
        
        # Calculate recency-weighted averages
        last_5 = positions[:5] if len(positions) >= 5 else positions
        last_10 = positions[:10] if len(positions) >= 10 else positions
        
        # Exponential weighting (recent races weighted more)
        weights_5 = np.exp(np.arange(len(last_5)) / 1.5)
        weights_5 = weights_5 / weights_5.sum()
        last_5_weighted = np.average(last_5, weights=weights_5)
        
        # Form trend (improving = negative)
        if len(positions) >= 6:
            recent_3 = np.mean(positions[:3])
            older_3 = np.mean(positions[3:6])
            form_trend = recent_3 - older_3
        else:
            form_trend = 0.0
        
        # Momentum (last race vs previous)
        momentum = positions[0] - positions[1] if len(positions) > 1 else 0
        momentum_score = 50 + (momentum * -10)  # Higher score = improving
        
        # Win/place rates
        wins = sum(1 for p in positions if p == 1)
        places = sum(1 for p in positions if p <= 3)
        
        recent_wins = sum(1 for p in last_5 if p == 1)
        recent_places = sum(1 for p in last_5 if p <= 3)
        
        # Consistency (lower std = more consistent)
        consistency = max(0, 100 - (np.std(positions) * 15))
        
        # Days since last race
        try:
            last_date = datetime.strptime(results[0]['race_date'], '%Y-%m-%d')
            days_since = (datetime.now() - last_date).days
        except:
            days_since = 999
        
        # First/second up flags
        first_up = 1.0 if days_since > 60 else 0.0
        second_up = 1.0 if 30 < days_since <= 60 else 0.0
        
        # Form pattern
        if form_trend < -1.5:
            pattern = 'improving'
        elif form_trend > 1.5:
            pattern = 'declining'
        elif consistency > 70:
            pattern = 'consistent'
        else:
            pattern = 'variable'
        
        return {
            'form_available': 1.0,
            'last_5_avg': float(last_5_weighted),
            'last_10_avg': float(np.mean(last_10)),
            'career_avg': float(np.mean(positions)),
            'win_rate': float(wins / len(positions)),
            'place_rate': float(places / len(positions)),
            'consistency_score': float(consistency),
            'form_trend': float(form_trend),
            'momentum_score': float(np.clip(momentum_score, 0, 100)),
            'recent_win_rate': float(recent_wins / len(last_5)),
            'recent_place_rate': float(recent_places / len(last_5)),
            'days_since_last_race': float(days_since),
            'first_up_flag': first_up,
            'second_up_flag': second_up,
            'form_pattern': pattern,
            'total_races': float(len(positions))
        }
    
    def _extract_track_features(self, horse_name: str, track: str) -> Dict:
        """Extract track-specific features with detailed metrics."""
        perf = self.data.get_horse_track_performance(horse_name, track)
        
        if perf['total_races'] == 0:
            return {
                'track_experience': 0.0,
                'track_win_rate': 0.0,
                'track_place_rate': 0.0,
                'track_avg_position': 8.0,
                'track_score': 50.0,
                'track_favorite': 0.0
            }
        
        # Get detailed track results
        results = self.data.get_horse_race_results(horse_name, limit=50)
        track_results = [r for r in results if r['racecourse'] == track and r['position']]
        
        if track_results:
            avg_pos = np.mean([r['position'] for r in track_results])
            positions = [r['position'] for r in track_results]
            
            # Calculate track score (0-100)
            win_component = perf['win_rate'] * 3
            place_component = perf['place_rate'] * 1.5
            position_component = max(0, 100 - (avg_pos * 8))
            
            track_score = (win_component + place_component + position_component) / 3
            track_score = np.clip(track_score, 0, 100)
            
            # Track favorite (wins > 20% or places > 50%)
            is_favorite = 1.0 if perf['win_rate'] > 20 or perf['place_rate'] > 50 else 0.0
        else:
            avg_pos = 8.0
            track_score = 50.0
            is_favorite = 0.0
        
        return {
            'track_experience': float(perf['total_races']),
            'track_win_rate': float(perf['win_rate'] / 100),
            'track_place_rate': float(perf['place_rate'] / 100),
            'track_avg_position': float(avg_pos),
            'track_score': float(track_score),
            'track_favorite': is_favorite,
            'track_wins': float(perf['wins']),
            'track_places': float(perf['places'])
        }
    
    def _extract_distance_features(self, horse_name: str, distance: str) -> Dict:
        """Extract distance-specific features."""
        perf = self.data.get_horse_distance_performance(horse_name, distance)
        
        if perf['total_races'] == 0:
            return {
                'distance_experience': 0.0,
                'distance_win_rate': 0.0,
                'distance_place_rate': 0.0,
                'distance_score': 50.0,
                'distance_specialist': 0.0
            }
        
        # Distance score calculation
        win_component = perf['win_rate'] * 2
        place_component = perf['place_rate']
        experience_bonus = min(20, perf['total_races'] * 2)
        
        distance_score = (win_component + place_component + experience_bonus) / 3
        distance_score = np.clip(distance_score, 0, 100)
        
        # Distance specialist (strong record at this distance)
        is_specialist = 1.0 if perf['win_rate'] > 25 and perf['total_races'] >= 3 else 0.0
        
        return {
            'distance_experience': float(perf['total_races']),
            'distance_win_rate': float(perf['win_rate'] / 100),
            'distance_place_rate': float(perf['place_rate'] / 100),
            'distance_score': float(distance_score),
            'distance_specialist': is_specialist,
            'distance_wins': float(perf['wins']),
            'distance_places': float(perf['places'])
        }
    
    def _extract_class_features(self, horse_name: str, race_class: str) -> Dict:
        """Extract class-specific features."""
        results = self.data.get_race_results_by_class(race_class) if hasattr(self.data, 'get_race_results_by_class') else []
        horse_results = [r for r in results if r.get('horse_name') == horse_name and r.get('position')]
        
        if not horse_results:
            return {
                'class_experience': 0.0,
                'class_win_rate': 0.0,
                'class_place_rate': 0.0,
                'class_score': 50.0,
                'class_dropping': 0.0,
                'class_rising': 0.0
            }
        
        positions = [r['position'] for r in horse_results]
        wins = sum(1 for p in positions if p == 1)
        places = sum(1 for p in positions if p <= 3)
        
        win_rate = wins / len(positions)
        place_rate = places / len(positions)
        avg_pos = np.mean(positions)
        
        class_score = (win_rate * 100 * 2 + place_rate * 100 + max(0, 100 - avg_pos * 8)) / 3
        
        return {
            'class_experience': float(len(positions)),
            'class_win_rate': float(win_rate),
            'class_place_rate': float(place_rate),
            'class_avg_position': float(avg_pos),
            'class_score': float(np.clip(class_score, 0, 100)),
            'class_dropping': 0.0,  # Would need class hierarchy
            'class_rising': 0.0
        }
    
    def _extract_jockey_features(self, jockey: str, track: str, distance: str, race_class: str) -> Dict:
        """Extract comprehensive jockey features."""
        if not jockey:
            return {
                'jockey_win_rate': 0.08,
                'jockey_place_rate': 0.25,
                'jockey_score': 50.0,
                'jockey_track_win_rate': 0.08,
                'jockey_experience': 0.0
            }
        
        stats = self.data.get_jockey_stats(jockey)
        
        # Get jockey ranking if available
        ranking_data = self._get_jockey_ranking(jockey)
        
        # Base jockey score
        base_score = (stats['win_rate'] * 3 + stats['place_rate'] * 1.5) / 2
        
        # Adjust by ranking
        if ranking_data:
            rank_bonus = max(0, (50 - ranking_data['rank']) / 2)
            base_score += rank_bonus
        
        # Track-specific jockey performance (if data available)
        track_win_rate = stats['win_rate']  # Default to overall
        
        return {
            'jockey_win_rate': float(stats['win_rate'] / 100),
            'jockey_place_rate': float(stats['place_rate'] / 100),
            'jockey_score': float(np.clip(base_score, 0, 100)),
            'jockey_total_rides': float(stats['total_races']),
            'jockey_track_win_rate': float(track_win_rate / 100),
            'jockey_rank': float(ranking_data['rank']) if ranking_data else 99.0,
            'jockey_rank_pct': float(ranking_data['rank_pct']) if ranking_data else 0.5
        }
    
    def _extract_trainer_features(self, trainer: str, track: str, distance: str, race_class: str) -> Dict:
        """Extract comprehensive trainer features."""
        if not trainer:
            return {
                'trainer_win_rate': 0.10,
                'trainer_place_rate': 0.28,
                'trainer_score': 50.0,
                'trainer_track_win_rate': 0.10,
                'trainer_experience': 0.0
            }
        
        stats = self.data.get_trainer_stats(trainer)
        
        # Get trainer ranking if available
        ranking_data = self._get_trainer_ranking(trainer)
        
        # Base trainer score
        base_score = (stats['win_rate'] * 3 + stats['place_rate'] * 1.5) / 2
        
        # Adjust by ranking
        if ranking_data:
            rank_bonus = max(0, (50 - ranking_data['rank']) / 2)
            base_score += rank_bonus
        
        return {
            'trainer_win_rate': float(stats['win_rate'] / 100),
            'trainer_place_rate': float(stats['place_rate'] / 100),
            'trainer_score': float(np.clip(base_score, 0, 100)),
            'trainer_total_runs': float(stats['total_races']),
            'trainer_track_win_rate': float(stats['win_rate'] / 100),
            'trainer_rank': float(ranking_data['rank']) if ranking_data else 99.0,
            'trainer_rank_pct': float(ranking_data['rank_pct']) if ranking_data else 0.5
        }
    
    def _extract_jockey_trainer_synergy(self, jockey: str, trainer: str) -> Dict:
        """Extract jockey-trainer combination synergy."""
        if not jockey or not trainer:
            return {
                'jt_synergy': 0.0,
                'jt_combo_win_rate': 0.0,
                'jt_races_together': 0.0,
                'jt_synergy_score': 50.0
            }
        
        try:
            results = self.data.get_jockey_trainer_results(jockey, trainer)
        except:
            results = []
        
        if not results or len(results) < 3:
            return {
                'jt_synergy': 0.0,
                'jt_combo_win_rate': 0.0,
                'jt_races_together': float(len(results)),
                'jt_synergy_score': 50.0
            }
        
        # Convert positions to integers (database returns strings)
        positions = []
        for r in results:
            if r['position']:
                try:
                    positions.append(int(r['position']))
                except (ValueError, TypeError):
                    continue
        
        wins = sum(1 for p in positions if p == 1)
        places = sum(1 for p in positions if p <= 3)
        
        combo_win_rate = wins / len(positions)
        combo_place_rate = places / len(positions)
        
        # Compare to individual rates
        jockey_stats = self.data.get_jockey_stats(jockey)
        trainer_stats = self.data.get_trainer_stats(trainer)
        
        expected_win_rate = (jockey_stats['win_rate'] + trainer_stats['win_rate']) / 200
        synergy = combo_win_rate - expected_win_rate
        
        synergy_score = 50 + (synergy * 200)
        
        return {
            'jt_synergy': float(synergy),
            'jt_combo_win_rate': float(combo_win_rate),
            'jt_combo_place_rate': float(combo_place_rate),
            'jt_races_together': float(len(results)),
            'jt_synergy_score': float(np.clip(synergy_score, 0, 100))
        }
    
    def _extract_draw_features(self, draw: int, field_size: int, track: str, distance: str, race_class: str) -> Dict:
        """Extract comprehensive draw/barrier features."""
        # Ensure draw_val is a proper number
        try:
            draw_val = int(draw) if draw is not None else 8
        except (ValueError, TypeError):
            draw_val = 8
        field = max(field_size, 1)
        
        # Draw position ratio (1 = outside, 0 = inside)
        draw_ratio = draw_val / field
        
        # Track and distance specific draw bias
        if track == 'ST':
            if '1000' in str(distance) or '1200' in str(distance):
                # Sprints - inside draws slightly favored
                optimal_range = (1, 6)
            elif '1400' in str(distance) or '1600' in str(distance):
                # Middle - middle draws favored
                optimal_range = (3, 8)
            else:
                # Longer - wider draws okay
                optimal_range = (4, 10)
        else:  # HV
            # Happy Valley - tighter track, inside more important
            optimal_range = (1, 6)
        
        if optimal_range[0] <= draw_val <= optimal_range[1]:
            draw_advantage = 1.0
            draw_score = 80 + (5 - abs(draw_val - (optimal_range[0] + optimal_range[1]) / 2)) * 4
        elif draw_val <= 2:
            draw_advantage = 0.5  # Very inside can be trapped
            draw_score = 65
        elif draw_val >= field - 2:
            draw_advantage = -1.0  # Wide draw disadvantage
            draw_score = 40
        else:
            draw_advantage = 0.0
            draw_score = 60
        
        return {
            'draw': draw_val,
            'draw_ratio': draw_ratio,
            'draw_score': float(np.clip(draw_score, 0, 100)),
            'draw_advantage': draw_advantage,
            'inside_draw': 1.0 if draw_val <= 4 else 0.0,
            'outside_draw': 1.0 if draw_val >= 10 else 0.0,
            'middle_draw': 1.0 if 4 < draw_val < 10 else 0.0
        }
    
    def _extract_weight_features(self, horse_name: str, weight: str, track: str, distance: str) -> Dict:
        """Extract weight-related features."""
        try:
            weight_val = float(weight.split()[-1]) if weight else 126.0
        except:
            weight_val = 126.0
        
        # Weight benchmarks by track
        if track == 'ST':
            avg_weight = 125.0
            heavy_threshold = 133.0
        else:
            avg_weight = 123.0
            heavy_threshold = 130.0
        
        weight_diff = weight_val - avg_weight
        
        # Weight score (lighter generally better, but not too light)
        if weight_val < 115:
            weight_score = 75  # Very light
        elif weight_val < 125:
            weight_score = 85  # Optimal
        elif weight_val < heavy_threshold:
            weight_score = 70  # Getting heavy
        else:
            weight_score = 55  # Heavy
        
        # Check horse's weight carrying history
        results = self.data.get_horse_race_results(horse_name, limit=20)
        weight_performance = []
        
        for r in results:
            if r.get('weight'):
                try:
                    w = float(str(r['weight']).split()[-1])
                    weight_performance.append((w, r.get('position', 99)))
                except:
                    pass
        
        if weight_performance:
            # Correlation between weight and position
            weights_carried = [w for w, _ in weight_performance]
            positions = [p for _, p in weight_performance]
            
            if len(weights_carried) > 3:
                correlation = np.corrcoef(weights_carried, positions)[0, 1]
                weight_tolerance = 50 - (correlation * 30)  # Negative correlation = good
            else:
                weight_tolerance = 50
        else:
            weight_tolerance = 50
        
        return {
            'weight': weight_val,
            'weight_diff_from_avg': weight_diff,
            'weight_score': float(weight_score),
            'is_heavy_weight': 1.0 if weight_val >= heavy_threshold else 0.0,
            'is_light_weight': 1.0 if weight_val < 115 else 0.0,
            'weight_tolerance': float(np.clip(weight_tolerance, 0, 100))
        }
    
    def _extract_odds_features(self, current_odds: float, horse_name: str, race_date: str, race_number: int, track: str) -> Dict:
        """Extract comprehensive odds features."""
        if not current_odds or current_odds <= 0:
            return {
                'odds_available': 0.0,
                'implied_prob': 0.05,
                'odds_score': 30.0,
                'odds_movement': 0.0,
                'market_support': 0.0
            }
        
        implied_prob = 1.0 / current_odds
        
        # Odds score (higher odds = lower score, but long shots get some points)
        if current_odds < 2.5:
            odds_score = 95  # Hot favorite
        elif current_odds < 5:
            odds_score = 85  # Second favorite
        elif current_odds < 10:
            odds_score = 70  # Middle range
        elif current_odds < 20:
            odds_score = 55  # Roughie
        else:
            odds_score = 40  # Long shot
        
        # Try to get odds movement from history
        try:
            conn = self.data._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """SELECT win_odds FROM odds_history 
                   WHERE race_date LIKE ? AND race_number = ? AND horse_name = ?
                   ORDER BY scraped_at ASC LIMIT 3""",
                (f"{race_date[:10]}%", race_number, horse_name)
            )
            historical_odds = [row[0] for row in cursor.fetchall() if row[0]]
            conn.close()
            
            if len(historical_odds) >= 2:
                odds_movement = (historical_odds[-1] - historical_odds[0]) / historical_odds[0]
                # Negative movement = shortening (market support)
                market_support = -odds_movement * 100
            else:
                odds_movement = 0.0
                market_support = 0.0
        except:
            odds_movement = 0.0
            market_support = 0.0
        
        return {
            'odds_available': 1.0,
            'current_odds': float(current_odds),
            'implied_prob': float(implied_prob),
            'odds_score': float(odds_score),
            'odds_movement': float(odds_movement),
            'market_support': float(market_support),
            'is_favorite': 1.0 if current_odds < 3 else 0.0,
            'is_second_fav': 1.0 if 3 <= current_odds < 6 else 0.0
        }
    
    def _extract_pedigree_features(self, horse_name: str) -> Dict:
        """Extract pedigree features from horse_details table."""
        try:
            conn = self.data._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT sire, dam, birthplace, age FROM horse_details WHERE horse_name = ?",
                (horse_name,)
            )
            result = cursor.fetchone()
            conn.close()
            
            if result:
                sire, dam, birthplace, age = result
                
                # Calculate age-based maturity score
                try:
                    age_val = int(str(age).split()[0]) if age else 4
                    if age_val <= 3:
                        maturity = 60  # Still developing
                    elif age_val <= 5:
                        maturity = 90  # Prime
                    elif age_val <= 7:
                        maturity = 80  # Experienced
                    else:
                        maturity = 65  # Getting older
                except:
                    maturity = 70
                
                # Bloodline score (placeholder - would need sire/dam performance data)
                bloodline_score = 70 if sire or dam else 50
                
                return {
                    'pedigree_available': 1.0,
                    'age_maturity': float(maturity),
                    'bloodline_score': float(bloodline_score),
                    'has_australian_blood': 1.0 if birthplace and 'AUS' in str(birthplace).upper() else 0.0,
                    'has_new_zealand_blood': 1.0 if birthplace and 'NZ' in str(birthplace).upper() else 0.0
                }
        except Exception as e:
            logger.debug(f"Error extracting pedigree: {e}")
        
        return {
            'pedigree_available': 0.0,
            'age_maturity': 70.0,
            'bloodline_score': 50.0,
            'has_australian_blood': 0.0,
            'has_new_zealand_blood': 0.0
        }
    
    def _extract_gear_features(self, gear: str, horse_name: str) -> Dict:
        """Extract gear/equipment features."""
        if not gear:
            # Try to get from exceptional_factors
            try:
                conn = self.data._get_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT gear FROM exceptional_factors WHERE horse_name = ? ORDER BY race_date DESC LIMIT 1",
                    (horse_name,)
                )
                result = cursor.fetchone()
                conn.close()
                gear = result[0] if result else None
            except:
                gear = None
        
        if not gear:
            return {
                'gear_change': 0.0,
                'blinkers_on': 0.0,
                'blinkers_off': 0.0,
                'visors': 0.0,
                'gear_score': 50.0
            }
        
        gear_str = str(gear).upper()
        
        # Common gear indicators
        blinkers_on = 1.0 if 'B' in gear_str and 'OFF' not in gear_str else 0.0
        blinkers_off = 1.0 if 'B/O' in gear_str or 'BO' in gear_str else 0.0
        visors = 1.0 if 'V' in gear_str else 0.0
        
        # Gear change score (blinkers on often improves focus)
        if blinkers_on:
            gear_score = 75
        elif visors:
            gear_score = 70
        elif blinkers_off:
            gear_score = 60  # Removing gear sometimes helps
        else:
            gear_score = 65
        
        return {
            'gear_change': 1.0,
            'blinkers_on': blinkers_on,
            'blinkers_off': blinkers_off,
            'visors': visors,
            'gear_score': float(gear_score),
            'gear_type': gear
        }
    
    def _extract_weather_features(self, race_date: str, track: str) -> Dict:
        """Extract weather and track condition features."""
        try:
            conn = self.data._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT temperature, humidity, wind_speed, track_condition FROM weather WHERE race_date = ? AND racecourse = ?",
                (race_date, track)
            )
            result = cursor.fetchone()
            conn.close()
            
            if result:
                temp, humidity, wind, condition = result
                
                # Track condition score
                condition_scores = {
                    'GOOD': 90,
                    'GOOD TO FIRM': 85,
                    'FIRM': 80,
                    'GOOD TO SOFT': 75,
                    'SOFT': 60,
                    'HEAVY': 45
                }
                condition_score = condition_scores.get(str(condition).upper(), 75) if condition else 75
                
                return {
                    'weather_available': 1.0,
                    'temperature': float(temp) if temp else 25.0,
                    'humidity': float(humidity) if humidity else 70.0,
                    'wind_speed': float(wind) if wind else 10.0,
                    'track_condition_score': float(condition_score),
                    'is_good_track': 1.0 if condition and 'GOOD' in str(condition).upper() else 0.0,
                    'is_soft_track': 1.0 if condition and 'SOFT' in str(condition).upper() else 0.0
                }
        except Exception as e:
            logger.debug(f"Error extracting weather: {e}")
        
        return {
            'weather_available': 0.0,
            'temperature': 25.0,
            'humidity': 70.0,
            'wind_speed': 10.0,
            'track_condition_score': 75.0,
            'is_good_track': 1.0,
            'is_soft_track': 0.0
        }
    
    def _extract_barrier_trial_features(self, horse_name: str) -> Dict:
        """Extract barrier trial features."""
        try:
            trials = self.data.get_barrier_test_results(horse_name, limit=3)
        except:
            trials = []
        
        if not trials:
            return {
                'trial_available': 0.0,
                'last_trial_position': 99.0,
                'trial_score': 50.0,
                'recent_trial_count': 0.0
            }
        
        last_trial = trials[0]
        position = last_trial.get('position', 99)
        try:
            position = int(position) if position is not None else 99
        except (ValueError, TypeError):
            position = 99

        # Trial score based on position
        if position == 1:
            trial_score = 90
        elif position <= 3:
            trial_score = 80
        elif position <= 6:
            trial_score = 65
        else:
            trial_score = 50
        
        return {
            'trial_available': 1.0,
            'last_trial_position': float(position),
            'trial_score': float(trial_score),
            'recent_trial_count': float(len(trials)),
            'trial_win': 1.0 if position == 1 else 0.0
        }
    
    def _extract_trackwork_features(self, horse_name: str) -> Dict:
        """Extract morning trackwork features."""
        try:
            work = self.data.get_morning_trackwork(horse_name, limit=5)
        except:
            work = []
        
        if not work:
            return {
                'trackwork_available': 0.0,
                'trackwork_count': 0.0,
                'trackwork_score': 50.0
            }
        
        # Analyze trackwork intensity/quality from info text
        info_text = ' '.join([w.get('info', '') for w in work]).upper()
        
        # Keywords indicating good work
        positive_keywords = ['BULLET', 'GREAT', 'VERY WELL', 'IMPRESSIVE', 'STRONG']
        negative_keywords = ['SLOW', 'POOR', 'DISAPPOINTING', 'WEAK']
        
        pos_count = sum(1 for kw in positive_keywords if kw in info_text)
        neg_count = sum(1 for kw in negative_keywords if kw in info_text)
        
        trackwork_score = 50 + (pos_count * 10) - (neg_count * 10)
        trackwork_score = np.clip(trackwork_score, 30, 90)
        
        return {
            'trackwork_available': 1.0,
            'trackwork_count': float(len(work)),
            'trackwork_score': float(trackwork_score),
            'recent_trackwork': 1.0 if work else 0.0
        }
    
    def _extract_veterinary_features(self, horse_name: str) -> Dict:
        """Extract veterinary records features."""
        records = self.data.get_veterinary_records(horse_name)
        
        if not records:
            return {
                'vet_clear': 1.0,
                'vet_concerns': 0.0,
                'vet_score': 95.0,
                'recent_vet_visit': 0.0
            }
        
        # Check recent records for concerns
        recent_records = records[:3]
        concern_keywords = ['LAME', 'SORE', 'INJURY', 'PROBLEM', 'ISSUE']
        
        concerns = 0
        for record in recent_records:
            details = str(record.get('details', '')).upper()
            if any(kw in details for kw in concern_keywords):
                concerns += 1
        
        if concerns > 0:
            vet_score = 40
            vet_clear = 0.0
        else:
            vet_score = 90
            vet_clear = 1.0
        
        return {
            'vet_clear': vet_clear,
            'vet_concerns': float(concerns),
            'vet_score': float(vet_score),
            'recent_vet_visit': 1.0 if records else 0.0
        }
    
    def _extract_injury_features(self, horse_name: str) -> Dict:
        """Extract injury records features."""
        try:
            conn = self.data._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM injury_records WHERE horse_name = ?",
                (horse_name,)
            )
            count = cursor.fetchone()[0]
            conn.close()
            
            if count > 0:
                return {
                    'injury_history': 1.0,
                    'injury_count': float(count),
                    'injury_score': max(30, 70 - count * 15)
                }
        except:
            pass
        
        return {
            'injury_history': 0.0,
            'injury_count': 0.0,
            'injury_score': 90.0
        }
    
    def _extract_competition_features(self, horse_name: str, race_date: str) -> Dict:
        """Extract competition events features."""
        try:
            conn = self.data._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """SELECT competition_event FROM competition_events 
                   WHERE horse_name = ? AND race_date = ?""",
                (horse_name, race_date)
            )
            events = [row[0] for row in cursor.fetchall()]
            conn.close()
            
            if events:
                # Parse competition events
                event_str = ' '.join(events).upper()
                
                # Check for notable achievements
                is_champion = 1.0 if 'CHAMPION' in event_str else 0.0
                is_graded_winner = 1.0 if any(x in event_str for x in ['GRADE', 'GROUP', 'G1', 'G2', 'G3']) else 0.0
                
                competition_score = 70 + (is_champion * 20) + (is_graded_winner * 15)
                
                return {
                    'competition_history': 1.0,
                    'is_champion': is_champion,
                    'is_graded_winner': is_graded_winner,
                    'competition_score': float(competition_score)
                }
        except:
            pass
        
        return {
            'competition_history': 0.0,
            'is_champion': 0.0,
            'is_graded_winner': 0.0,
            'competition_score': 50.0
        }
    
    def _extract_rating_features(self, horse_name: str, race_date: str) -> Dict:
        """Extract horse rating features."""
        try:
            conn = self.data._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT rating FROM horse_ratings WHERE horse_name = ? ORDER BY rating_date DESC LIMIT 1",
                (horse_name,)
            )
            result = cursor.fetchone()
            conn.close()
            
            if result and result[0]:
                rating = float(result[0])
                # Convert rating to score (assuming higher is better, typical range 40-120)
                rating_score = min(100, max(30, (rating - 40) * 1.25))
                
                return {
                    'rating_available': 1.0,
                    'official_rating': rating,
                    'rating_score': float(rating_score)
                }
        except:
            pass
        
        return {
            'rating_available': 0.0,
            'official_rating': 60.0,
            'rating_score': 50.0
        }
    
    def _extract_interaction_features(self, features: Dict, track: str, distance: str, race_class: str) -> Dict:
        """Extract interaction and derived features."""
        interactions = {}
        
        # Track-Distance synergy
        track_score = features.get('track_score', 50)
        distance_score = features.get('distance_score', 50)
        interactions['track_distance_synergy'] = (track_score + distance_score) / 2
        
        # Human factor combined score
        jockey_score = features.get('jockey_score', 50)
        trainer_score = features.get('trainer_score', 50)
        jt_synergy = features.get('jt_synergy_score', 50)
        interactions['human_factor_score'] = (jockey_score * 0.4 + trainer_score * 0.4 + jt_synergy * 0.2)
        
        # Form momentum combined
        form_score = 100 - (features.get('last_5_avg', 8) * 10)
        momentum = features.get('momentum_score', 50)
        interactions['form_momentum_combined'] = (form_score + momentum) / 2
        
        # Health and fitness
        vet_score = features.get('vet_score', 90)
        injury_score = features.get('injury_score', 90)
        trackwork_score = features.get('trackwork_score', 50)
        interactions['fitness_health_score'] = (vet_score + injury_score + trackwork_score) / 3
        
        # Overall preparation
        interactions['preparation_score'] = (
            features.get('trial_score', 50) * 0.3 +
            trackwork_score * 0.3 +
            features.get('pedigree_available', 0) * 20
        )
        
        # Market confidence
        odds_score = features.get('odds_score', 50)
        market_support = features.get('market_support', 0)
        interactions['market_confidence'] = odds_score + market_support
        
        return interactions
    
    def _get_jockey_ranking(self, jockey: str) -> Optional[Dict]:
        """Get jockey ranking data."""
        try:
            conn = self.data._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT rank, total_rides, win_pct FROM jockey_rankings WHERE jockey = ?",
                (jockey,)
            )
            result = cursor.fetchone()
            conn.close()
            
            if result:
                rank, total, win_pct = result
                return {
                    'rank': rank,
                    'total_rides': total,
                    'win_pct': win_pct,
                    'rank_pct': 1.0 - (rank / 100) if rank else 0.5
                }
        except:
            pass
        return None
    
    def _get_trainer_ranking(self, trainer: str) -> Optional[Dict]:
        """Get trainer ranking data."""
        try:
            conn = self.data._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT rank, total_runs, win_pct FROM trainer_rankings WHERE trainer = ?",
                (trainer,)
            )
            result = cursor.fetchone()
            conn.close()
            
            if result:
                rank, total, win_pct = result
                return {
                    'rank': rank,
                    'total_runs': total,
                    'win_pct': win_pct,
                    'rank_pct': 1.0 - (rank / 100) if rank else 0.5
                }
        except:
            pass
        return None
    
    def _extract_wind_features(self, race_date: str, track: str) -> Dict:
        """Extract wind tracker features."""
        try:
            conn = self.data._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """SELECT wind_speed, wind_direction, wind_gust, temperature, humidity 
                   FROM wind_tracker 
                   WHERE race_date = ? AND racecourse = ?
                   ORDER BY updated_at DESC LIMIT 1""",
                (race_date, track)
            )
            result = cursor.fetchone()
            conn.close()
            
            if result:
                wind_speed, wind_dir, wind_gust, temp, humidity = result
                
                # Wind impact score
                if wind_speed and float(wind_speed) > 20:
                    wind_impact = 60  # Strong wind - challenging
                elif wind_speed and float(wind_speed) > 10:
                    wind_impact = 75  # Moderate wind
                else:
                    wind_impact = 90  # Light wind - good
                
                return {
                    'wind_data_available': 1.0,
                    'wind_speed': float(wind_speed) if wind_speed else 10.0,
                    'wind_gust': float(wind_gust) if wind_gust else 15.0,
                    'wind_impact_score': float(wind_impact),
                    'is_strong_wind': 1.0 if wind_speed and float(wind_speed) > 20 else 0.0
                }
        except Exception as e:
            logger.debug(f"Error extracting wind data: {e}")
        
        return {
            'wind_data_available': 0.0,
            'wind_speed': 10.0,
            'wind_gust': 15.0,
            'wind_impact_score': 85.0,
            'is_strong_wind': 0.0
        }
    
    def _extract_barrier_draw_features(self, draw: int, track: str, distance: str) -> Dict:
        """Extract barrier draw statistics features."""
        try:
            conn = self.data._get_connection()
            cursor = conn.cursor()
            
            # Get historical stats for this barrier position
            cursor.execute(
                """SELECT starters, wins 
                   FROM barrier_draws 
                   WHERE barrier_position = ? 
                   ORDER BY race_date DESC LIMIT 10""",
                (draw,)
            )
            results = cursor.fetchall()
            conn.close()
            
            if results:
                total_starters = sum(r[0] for r in results if r[0])
                total_wins = sum(r[1] for r in results if r[1])
                
                if total_starters > 0:
                    barrier_win_rate = total_wins / total_starters
                    barrier_score = min(100, 50 + (barrier_win_rate * 100))
                else:
                    barrier_win_rate = 0.1
                    barrier_score = 50.0
                
                return {
                    'barrier_stats_available': 1.0,
                    'barrier_historical_win_rate': float(barrier_win_rate),
                    'barrier_score': float(barrier_score),
                    'barrier_sample_size': float(len(results))
                }
        except Exception as e:
            logger.debug(f"Error extracting barrier draw stats: {e}")
        
        return {
            'barrier_stats_available': 0.0,
            'barrier_historical_win_rate': 0.1,
            'barrier_score': 50.0,
            'barrier_sample_size': 0.0
        }
    
    def _extract_gear_statistics_features(self, gear: str) -> Dict:
        """Extract gear statistics features."""
        if not gear:
            return {
                'gear_stats_available': 0.0,
                'gear_win_rate': 0.12,
                'gear_score': 50.0
            }
        
        try:
            conn = self.data._get_connection()
            cursor = conn.cursor()
            
            # Parse gear code
            gear_codes = []
            gear_str = str(gear).upper()
            if 'B' in gear_str and 'OFF' not in gear_str:
                gear_codes.append('B')
            if 'V' in gear_str:
                gear_codes.append('V')
            if 'P' in gear_str:
                gear_codes.append('P')
            
            if gear_codes:
                placeholders = ','.join('?' * len(gear_codes))
                cursor.execute(
                    f"""SELECT AVG(win_pct) FROM gear_statistics 
                       WHERE gear_code IN ({placeholders})""",
                    gear_codes
                )
                result = cursor.fetchone()
                conn.close()
                
                if result and result[0]:
                    avg_win_rate = float(result[0]) / 100  # Convert from percentage
                    gear_score = min(100, 50 + (avg_win_rate * 100))
                    
                    return {
                        'gear_stats_available': 1.0,
                        'gear_win_rate': float(avg_win_rate),
                        'gear_score': float(gear_score)
                    }
        except Exception as e:
            logger.debug(f"Error extracting gear statistics: {e}")
        
        return {
            'gear_stats_available': 0.0,
            'gear_win_rate': 0.12,
            'gear_score': 50.0
        }
    
    def _extract_last_race_summary_features(self, horse_name: str) -> Dict:
        """Extract last race summary features."""
        try:
            conn = self.data._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """SELECT summary FROM last_race_summaries 
                   WHERE horse_name = ? 
                   ORDER BY race_date DESC LIMIT 1""",
                (horse_name,)
            )
            result = cursor.fetchone()
            conn.close()
            
            if result and result[0]:
                summary = str(result[0]).upper()
                
                # Analyze summary text
                positive_keywords = ['WIN', 'GOOD', 'STRONG', 'IMPRESSIVE', 'EASY']
                negative_keywords = ['POOR', 'WEAK', 'DISAPPOINTED', 'TROUBLE', 'BLOCKED']
                
                pos_count = sum(1 for kw in positive_keywords if kw in summary)
                neg_count = sum(1 for kw in negative_keywords if kw in summary)
                
                summary_score = 50 + (pos_count * 15) - (neg_count * 15)
                summary_score = np.clip(summary_score, 20, 95)
                
                return {
                    'last_race_summary_available': 1.0,
                    'last_race_summary_score': float(summary_score),
                    'last_race_positive': float(pos_count),
                    'last_race_negative': float(neg_count)
                }
        except Exception as e:
            logger.debug(f"Error extracting last race summary: {e}")
        
        return {
            'last_race_summary_available': 0.0,
            'last_race_summary_score': 50.0,
            'last_race_positive': 0.0,
            'last_race_negative': 0.0
        }
    
    def _extract_new_horse_features(self, horse_name: str) -> Dict:
        """Extract new horse introduction features (for unraced/debut horses)."""
        try:
            conn = self.data._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """SELECT sire_intro, progeny_performance, dam_intro, comments 
                   FROM new_horse_introductions 
                   WHERE horse_name = ?""",
                (horse_name,)
            )
            result = cursor.fetchone()
            conn.close()
            
            if result:
                sire_intro, progeny_perf, dam_intro, comments = result
                
                # Analyze pedigree intro
                intro_text = ' '.join(filter(None, [sire_intro, progeny_perf, dam_intro, comments])).upper()
                
                # Keywords indicating quality bloodline
                quality_keywords = ['CHAMPION', 'WINNER', 'GROUP', 'GRADED', 'STAKES', 'SUCCESSFUL']
                
                quality_count = sum(1 for kw in quality_keywords if kw in intro_text)
                
                # New horses start with base score but get bonus for good pedigree
                new_horse_score = 45 + (quality_count * 8)
                new_horse_score = min(80, new_horse_score)  # Cap at 80 for unraced horses
                
                return {
                    'is_new_horse': 1.0,
                    'new_horse_pedigree_score': float(new_horse_score),
                    'pedigree_quality_markers': float(quality_count)
                }
        except Exception as e:
            logger.debug(f"Error extracting new horse data: {e}")
        
        return {
            'is_new_horse': 0.0,
            'new_horse_pedigree_score': 50.0,
            'pedigree_quality_markers': 0.0
        }
    
    def _extract_professional_schedule_features(self, jockey: str, trainer: str, race_date: str, race_number: int) -> Dict:
        """Extract professional schedule features (jockey/trainer bookings)."""
        features = {
            'jockey_booked_races': 0.0,
            'trainer_booked_races': 0.0,
            'jockey_workload': 'normal'
        }
        
        try:
            conn = self.data._get_connection()
            cursor = conn.cursor()
            
            # Count jockey's rides for the day
            if jockey:
                cursor.execute(
                    """SELECT COUNT(DISTINCT race_number) FROM professional_schedules 
                       WHERE professional_name = ? AND professional_type = 'Jockey' 
                       AND race_date = ?""",
                    (jockey, race_date)
                )
                result = cursor.fetchone()
                if result:
                    jockey_rides = result[0] or 0
                    features['jockey_booked_races'] = float(jockey_rides)
                    
                    # Workload assessment
                    if jockey_rides > 8:
                        features['jockey_workload'] = 'heavy'
                        features['jockey_workload_score'] = 60.0  # Heavy workload might reduce performance
                    elif jockey_rides > 5:
                        features['jockey_workload'] = 'moderate'
                        features['jockey_workload_score'] = 80.0
                    else:
                        features['jockey_workload'] = 'light'
                        features['jockey_workload_score'] = 90.0
            
            # Count trainer's runners for the day
            if trainer:
                cursor.execute(
                    """SELECT COUNT(DISTINCT race_number) FROM professional_schedules 
                       WHERE professional_name = ? AND professional_type = 'Trainer' 
                       AND race_date = ?""",
                    (trainer, race_date)
                )
                result = cursor.fetchone()
                if result:
                    trainer_runners = result[0] or 0
                    features['trainer_booked_races'] = float(trainer_runners)
                    
                    # Trainer workload assessment
                    if trainer_runners > 6:
                        features['trainer_workload_score'] = 70.0
                    elif trainer_runners > 3:
                        features['trainer_workload_score'] = 85.0
                    else:
                        features['trainer_workload_score'] = 95.0
            
            conn.close()
        except Exception as e:
            logger.debug(f"Error extracting professional schedules: {e}")
        
        return features

    def _extract_race_info_features(self, race_date: str, race_number: int, track: str) -> Dict:
        """Extract detailed race info features including sectional times and prize money."""
        try:
            conn = self.data._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """SELECT race_name, distance, race_class, track_type, course, 
                          going, prize_money, rating_range, sectional_time_1, 
                          sectional_time_2, sectional_time_3, notes
                   FROM race_info 
                   WHERE race_date = ? AND race_number = ? AND racecourse = ?""",
                (race_date, race_number, track)
            )
            result = cursor.fetchone()
            conn.close()
            
            if result:
                race_name, distance, race_class, track_type, course, going, prize_money, rating_range, sect_1, sect_2, sect_3, notes = result
                
                # Parse prize money (extract number from string like "HK$1,582,000")
                prize_value = 0
                if prize_money:
                    try:
                        prize_str = str(prize_money).replace('HK$', '').replace(',', '').replace('$', '')
                        prize_value = float(prize_str) if prize_str else 0
                    except:
                        pass
                
                # Class level based on prize money
                if prize_value > 2000000:
                    stakes_level = 90  # High stakes
                elif prize_value > 1000000:
                    stakes_level = 75  # Mid stakes
                else:
                    stakes_level = 60  # Lower stakes
                
                # Track type indicator
                is_turf = 1.0 if track_type and 'TURF' in str(track_type).upper() else 0.0
                is_awt = 1.0 if track_type and 'AWT' in str(track_type).upper() else 0.0
                
                return {
                    'race_info_available': 1.0,
                    'race_name': race_name or '',
                    'track_type': track_type or '',
                    'track_type_turf': is_turf,
                    'track_type_awt': is_awt,
                    'prize_money': float(prize_value),
                    'stakes_level_score': float(stakes_level),
                    'rating_range_str': rating_range or '',
                    'has_sectional_times': 1.0 if sect_1 or sect_2 or sect_3 else 0.0
                }
        except Exception as e:
            logger.debug(f"Error extracting race info features: {e}")
        
        return {
            'race_info_available': 0.0,
            'prize_money': 0.0,
            'stakes_level_score': 65.0,
            'track_type_turf': 1.0,
            'track_type_awt': 0.0,
            'has_sectional_times': 0.0
        }

    def _extract_horse_info_features(self, horse_name: str) -> Dict:
        """Extract basic horse info from horses table."""
        try:
            conn = self.data._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """SELECT horse_id, additional_info FROM horses WHERE horse_name = ?""",
                (horse_name,)
            )
            result = cursor.fetchone()
            conn.close()
            
            if result:
                horse_id, additional_info = result
                
                # Parse additional info if it contains useful data
                info_score = 50
                if additional_info:
                    info_text = str(additional_info).upper()
                    if any(x in info_text for x in ['CHAMPION', 'WINNER', 'GOOD']):
                        info_score = 75
                    elif any(x in info_text for x in ['PROSPECT', 'PROMISING']):
                        info_score = 65
                
                return {
                    'horse_info_available': 1.0,
                    'horse_id': horse_id or '',
                    'horse_info_score': float(info_score)
                }
        except Exception as e:
            logger.debug(f"Error extracting horse info features: {e}")
        
        return {
            'horse_info_available': 0.0,
            'horse_id': '',
            'horse_info_score': 50.0
        }

    def _extract_form_line_features(self, horse_name: str) -> Dict:
        """Extract detailed form line features including relative weight, rating, jockey changes."""
        try:
            conn = self.data._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """SELECT weight, rating, barrier, jockey, prev_jockey, 
                          finish, time, margin, rel_weight, rel_rating
                   FROM form_line 
                   WHERE horse_name = ? 
                   ORDER BY race_date DESC LIMIT 5""",
                (horse_name,)
            )
            results = cursor.fetchall()
            conn.close()
            
            if not results:
                return {
                    'form_line_available': 0.0,
                    'avg_relative_weight': 0.0,
                    'avg_relative_rating': 0.0,
                    'jockey_change': 0.0,
                    'recent_margin_avg': 99.0
                }
            
            rel_weights = []
            rel_ratings = []
            margins = []
            jockey_changes = 0
            
            for row in results:
                rel_weight = row[8]  # rel_weight column
                rel_rating = row[9]  # rel_rating column
                prev_jockey = row[4]  # prev_jockey column
                margin_str = row[7]  # margin column
                
                if rel_weight:
                    try:
                        rel_weights.append(float(rel_weight))
                    except:
                        pass
                
                if rel_rating:
                    try:
                        rel_ratings.append(float(rel_rating))
                    except:
                        pass
                
                if margin_str:
                    try:
                        # Parse margin (could be "1/2", "3/4", "1", etc.)
                        if '/' in str(margin_str):
                            parts = str(margin_str).split('/')
                            margin = float(parts[0]) / float(parts[1])
                        else:
                            margin = float(margin_str)
                        margins.append(margin)
                    except:
                        pass
                
                if prev_jockey and row[3]:  # current jockey != prev_jockey
                    jockey_changes += 1
            
            return {
                'form_line_available': 1.0,
                'avg_relative_weight': float(np.mean(rel_weights)) if rel_weights else 0.0,
                'avg_relative_rating': float(np.mean(rel_ratings)) if rel_ratings else 0.0,
                'relative_weight_score': float(50 + (np.mean(rel_weights) if rel_weights else 0)),
                'relative_rating_score': float(50 + (np.mean(rel_ratings) if rel_ratings else 0)),
                'jockey_change': float(jockey_changes),
                'jockey_change_rate': float(jockey_changes / len(results)),
                'recent_margin_avg': float(np.mean(margins)) if margins else 99.0,
                'recent_margin_score': float(max(0, 100 - (np.mean(margins) * 10))) if margins else 50.0
            }
            
        except Exception as e:
            logger.debug(f"Error extracting form line features: {e}")
        
        return {
            'form_line_available': 0.0,
            'avg_relative_weight': 0.0,
            'avg_relative_rating': 0.0,
            'jockey_change': 0.0,
            'recent_margin_avg': 99.0
        }

    def _extract_running_style_features(self, horse_name: str) -> Dict:
        """Extract running style features from race positioning and sectional data."""
        try:
            conn = self.data._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """SELECT positioning_200m, positioning_400m, positioning_600m, 
                          race_movement, finished_time
                   FROM race_results 
                   WHERE horse_name = ? AND position IS NOT NULL
                   ORDER BY race_date DESC LIMIT 5""",
                (horse_name,)
            )
            results = cursor.fetchall()
            conn.close()
            
            if not results:
                return {
                    'running_style_available': 0.0,
                    'early_speed_score': 50.0,
                    'finishing_strength': 50.0,
                    'running_style': 'unknown'
                }
            
            positions_200m = []
            positions_400m = []
            positions_600m = []
            
            for row in results:
                pos_200 = row[0]  # positioning_200m
                pos_400 = row[1]  # positioning_400m  
                pos_600 = row[2]  # positioning_600m
                
                # Extract position numbers (format like "1st", "3rd", "5th")
                if pos_200:
                    try:
                        pos = int(''.join(filter(str.isdigit, str(pos_200))))
                        positions_200m.append(pos)
                    except:
                        pass
                
                if pos_400:
                    try:
                        pos = int(''.join(filter(str.isdigit, str(pos_400))))
                        positions_400m.append(pos)
                    except:
                        pass
                
                if pos_600:
                    try:
                        pos = int(''.join(filter(str.isdigit, str(pos_600))))
                        positions_600m.append(pos)
                    except:
                        pass
            
            if positions_200m and positions_600m:
                avg_early = np.mean(positions_600m)  # Position at 600m (early)
                avg_late = np.mean(positions_200m)   # Position at 200m (late)
                
                # Calculate running style
                position_change = avg_early - avg_late
                
                if position_change > 1.5:
                    running_style = 'strong_finisher'
                    finishing_strength = 85
                    early_speed = 40
                elif position_change < -1.5:
                    running_style = 'front_runner'
                    finishing_strength = 40
                    early_speed = 85
                elif abs(position_change) < 0.5:
                    running_style = 'consistent_runner'
                    finishing_strength = 70
                    early_speed = 70
                else:
                    running_style = 'mid_pack'
                    finishing_strength = 60
                    early_speed = 60
                
                return {
                    'running_style_available': 1.0,
                    'early_speed_score': float(early_speed),
                    'finishing_strength': float(finishing_strength),
                    'running_style': running_style,
                    'position_change_avg': float(position_change),
                    'avg_position_600m': float(np.mean(positions_600m)),
                    'avg_position_200m': float(np.mean(positions_200m))
                }
            
        except Exception as e:
            logger.debug(f"Error extracting running style features: {e}")
        
        return {
            'running_style_available': 0.0,
            'early_speed_score': 50.0,
            'finishing_strength': 50.0,
            'running_style': 'unknown'
        }
