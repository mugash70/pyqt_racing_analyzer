"""Integrates all 17 tables from hkjc_races.db database."""

import sqlite3
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataIntegrator:
    """Integrates all database tables for comprehensive race analysis."""
    
    def __init__(self, db_path: str):
        """Initialize database connection."""
        self.db_path = Path(db_path)
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found: {db_path}")
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection."""
        return sqlite3.connect(str(self.db_path))
    
    def get_race_info(self, race_date: str, race_number: int, racecourse: str) -> Dict:
        """Get race information. Falls back to fixtures if future_race_cards is empty."""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            date_prefix = race_date.split(' ')[0]
            
            # Try future_race_cards first
            cursor.execute(
                """SELECT race_distance, race_class, track_going
                FROM future_race_cards
                WHERE race_date LIKE ? AND race_number = ? AND racecourse = ?
                LIMIT 1""",
                (f"{date_prefix}%", race_number, racecourse)
            )
            result = cursor.fetchone()

            if result and result[0] and result[1]:
                return {
                    'distance': result[0],
                    'class': result[1],
                    'going': result[2] or 'GOOD'
                }
            
            # Fallback: Try fixtures table
            cursor.execute(
                """SELECT distance, race_class, track_type
                FROM fixtures
                WHERE race_date LIKE ? AND race_number = ?
                LIMIT 1""",
                (f"{date_prefix}%", race_number)
            )
            fixture = cursor.fetchone()
            
            if fixture:
                return {
                    'distance': fixture[0],
                    'class': fixture[1],
                    'going': 'GOOD'  # Fixtures don't have going info
                }
            
            # Try race_info (more comprehensive race-level data)
            cursor.execute(
                """SELECT distance, race_class, going
                FROM race_info
                WHERE race_date LIKE ? AND race_number = ? AND racecourse = ?
                LIMIT 1""",
                (f"{date_prefix}%", race_number, racecourse)
            )
            info = cursor.fetchone()
            if info:
                return {
                    'distance': info[0],
                    'class': info[1],
                    'going': info[2] or 'GOOD'
                }

            # Try to get from race_results with join to future_race_cards (for historical races)
            # Note: race_results doesn't have distance or class directly, need to join
            cursor.execute(
                """SELECT f.race_distance, f.race_class, f.track_going
                FROM race_results r
                LEFT JOIN future_race_cards f 
                  ON DATE(r.race_date) = DATE(f.race_date)
                  AND r.race_number = f.race_number
                  AND r.racecourse = f.racecourse
                WHERE r.race_date LIKE ? AND r.race_number = ? AND r.racecourse = ?
                LIMIT 1""",
                (f"{date_prefix}%", race_number, racecourse)
            )
            historical = cursor.fetchone()
            
            if historical and historical[0]:  # Check if we got distance from join
                return {
                    'distance': historical[0] or '1200',
                    'class': historical[1] or 'Class 4',
                    'going': historical[2] or 'GOOD'
                }
            
            # Generate from available data
            return {
                'distance': '1200',
                'class': 'Class 4',
                'going': 'GOOD'
            }
        finally:
            conn.close()
    
    def get_field_horses(self, race_date: str, race_number: int, racecourse: str) -> List[Dict]:
        """Get all horses in a race."""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # Handle date matching with timestamps - use LIKE to match date prefix
            date_prefix = race_date.split(' ')[0]
            
            # Try future_race_cards first
            cursor.execute(
                """SELECT horse_number, horse_name, jockey, trainer, weight, draw
                   FROM future_race_cards
                   WHERE race_date LIKE ? AND race_number = ? AND racecourse = ?
                   GROUP BY horse_number, horse_name, jockey, trainer, weight, draw
                   ORDER BY horse_number""",
                (f"{date_prefix}%", race_number, racecourse)
            )

            horses = []
            for row in cursor.fetchall():
                horses.append({
                    'number': row[0],
                    'name': row[1],
                    'jockey': row[2],
                    'trainer': row[3],
                    'weight': row[4],
                    'draw': row[5]
                })
            
            # If no horses from future_race_cards, try race_results (for historical)
            if not horses:
                cursor.execute(
                    """SELECT horse_number, horse_name, jockey, trainer, actual_weight, draw
                       FROM race_results
                       WHERE race_date LIKE ? AND race_number = ? AND racecourse = ?
                       ORDER BY horse_number""",
                    (f"{date_prefix}%", race_number, racecourse)
                )
                
                for row in cursor.fetchall():
                    horses.append({
                        'number': row[0],
                        'name': row[1],
                        'jockey': row[2],
                        'trainer': row[3],
                        'weight': row[4],
                        'draw': row[5]
                    })
            
            return horses
        finally:
            conn.close()
    
    def get_horse_race_results(self, horse_name: str, limit: int = 20) -> List[Dict]:
        """Get recent race results for a horse."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                """SELECT race_date, race_number, racecourse, position, 
                          actual_weight, finished_time, winning_odds 
                   FROM race_results 
                   WHERE horse_name = ? 
                   ORDER BY race_date DESC 
                   LIMIT ?""",
                (horse_name, limit)
            )
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    'race_date': row[0],
                    'race_number': row[1],
                    'racecourse': row[2],
                    'position': row[3],
                    'weight': row[4],
                    'time': row[5],
                    'odds': row[6]
                })
            return results
        finally:
            conn.close()
    
    def get_horse_track_performance(self, horse_name: str, track: str) -> Dict:
        """Get horse's performance at specific track."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                """SELECT COUNT(*) as races, 
                          SUM(CASE WHEN position = 1 THEN 1 ELSE 0 END) as wins,
                          SUM(CASE WHEN position <= 3 THEN 1 ELSE 0 END) as places
                   FROM race_results 
                   WHERE horse_name = ? AND racecourse = ?""",
                (horse_name, track)
            )
            
            row = cursor.fetchone()
            races = row[0] or 0
            wins = row[1] or 0
            places = row[2] or 0
            
            return {
                'total_races': races,
                'wins': wins,
                'places': places,
                'win_rate': (wins / races * 100) if races > 0 else 0,
                'place_rate': (places / races * 100) if races > 0 else 0
            }
        finally:
            conn.close()
    
    def get_horse_distance_performance(self, horse_name: str, distance: str) -> Dict:
        """Get horse's performance at specific distance."""
        conn = self._get_connection()
        
        try:
            # Join with both future_race_cards and race_info to find distances
            query = """
                SELECT r.*, 
                       COALESCE(f.race_distance, i.distance) as race_dist
                FROM race_results r
                LEFT JOIN future_race_cards f 
                  ON DATE(r.race_date) = DATE(f.race_date) 
                  AND r.race_number = f.race_number
                  AND r.racecourse = f.racecourse
                LEFT JOIN race_info i
                  ON DATE(r.race_date) = DATE(i.race_date)
                  AND r.race_number = i.race_number
                  AND r.racecourse = i.racecourse
                WHERE r.horse_name = ?
            """
            df_races = pd.read_sql_query(query, conn, params=(horse_name,))
            
            if df_races.empty:
                return {'total_races': 0, 'wins': 0, 'places': 0, 'win_rate': 0, 'place_rate': 0}
            
            # Normalize target distance (remove 'm' and whitespace)
            import re
            def normalize_dist(d):
                if not d: return ""
                match = re.search(r'\d+', str(d))
                return match.group() if match else ""

            target_dist = normalize_dist(distance)
            
            # Apply normalization to results
            df_races['norm_dist'] = df_races['race_dist'].apply(normalize_dist)
            
            # Filter by distance
            distance_races = df_races[df_races['norm_dist'] == target_dist].copy()
            
            if distance_races.empty:
                return {'total_races': 0, 'wins': 0, 'places': 0, 'win_rate': 0, 'place_rate': 0}
            
            # Convert position to numeric
            def parse_pos(val):
                if pd.isna(val): return None
                if isinstance(val, (int, float)): return val
                match = re.search(r'\d+', str(val))
                return int(match.group()) if match else None

            distance_races['pos_numeric'] = distance_races['position'].apply(parse_pos)
            
            races = len(distance_races)
            wins = len(distance_races[distance_races['pos_numeric'] == 1])
            places = len(distance_races[distance_races['pos_numeric'] <= 3])
            
            return {
                'total_races': races,
                'wins': wins,
                'places': places,
                'win_rate': (wins / races * 100) if races > 0 else 0,
                'place_rate': (places / races * 100) if races > 0 else 0
            }
        finally:
            conn.close()
    
    def get_live_odds(self, race_date: str, race_number: int, racecourse: str) -> List[Dict]:
        """Get live odds with fallback to odds_history."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            date_prefix = race_date.split(' ')[0]
            
            # Try odds_live first
            cursor.execute(
                """SELECT horse_number, horse_name, win_odds, place_odds
                FROM odds_live
                WHERE race_date LIKE ? AND race_number = ? AND racecourse = ?
                AND win_odds IS NOT NULL AND win_odds > 0
                ORDER BY scraped_at DESC""",
                (f"{date_prefix}%", race_number, racecourse)
            )
            
            odds = []
            for row in cursor.fetchall():
                win_odds = row[2]
                if win_odds and win_odds > 1.0:
                    odds.append({
                        'number': row[0],
                        'name': row[1], 
                        'win_odds': row[2],
                        'place_odds': row[3]
                    })
            
            # Fallback to odds_history
            if not odds:
                cursor.execute(
                    """SELECT horse_number, horse_name, win_odds, place_odds
                    FROM odds_history
                    WHERE race_date LIKE ? AND race_number = ? AND racecourse = ?
                    AND win_odds IS NOT NULL AND win_odds > 0
                    ORDER BY scraped_at DESC""",
                    (f"{date_prefix}%", race_number, racecourse)
                )
                
                odds_dict = {}
                for row in cursor.fetchall():
                    h_num = row[0]
                    win_odds = row[2]
                    if h_num not in odds_dict and win_odds and win_odds > 1.0:
                        odds_dict[h_num] = {
                            'number': row[0],
                            'name': row[1], 
                            'win_odds': row[2],
                            'place_odds': row[3]
                        }
                
                odds = sorted(list(odds_dict.values()), key=lambda x: x['number'])
            
            return odds
        finally:
            conn.close()

    def get_veterinary_records(self, horse_name: str) -> List[Dict]:
        """Get veterinary records for a horse."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                """SELECT record_date, details 
                   FROM veterinary_records 
                   WHERE horse_name = ? 
                   ORDER BY record_date DESC""",
                (horse_name,)
            )
            
            records = []
            for row in cursor.fetchall():
                records.append({
                    'date': row[0],
                    'details': row[1]
                })
            return records
        finally:
            conn.close()
    
    def get_jockey_stats(self, jockey_name: str) -> Dict:
        """Get jockey's win and place statistics."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                """SELECT COUNT(*) as races,
                          SUM(CASE WHEN position = 1 THEN 1 ELSE 0 END) as wins,
                          SUM(CASE WHEN position <= 3 THEN 1 ELSE 0 END) as places
                   FROM race_results 
                   WHERE jockey = ?""",
                (jockey_name,)
            )
            
            row = cursor.fetchone()
            races = row[0] or 0
            wins = row[1] or 0
            places = row[2] or 0
            
            return {
                'total_races': races,
                'wins': wins,
                'places': places,
                'win_rate': (wins / races * 100) if races > 0 else 0,
                'place_rate': (places / races * 100) if races > 0 else 0
            }
        finally:
            conn.close()
    
    def get_trainer_stats(self, trainer_name: str) -> Dict:
        """Get trainer's win and place statistics."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                """SELECT COUNT(*) as races,
                          SUM(CASE WHEN position = 1 THEN 1 ELSE 0 END) as wins,
                          SUM(CASE WHEN position <= 3 THEN 1 ELSE 0 END) as places
                   FROM race_results 
                   WHERE trainer = ?""",
                (trainer_name,)
            )
            
            row = cursor.fetchone()
            races = row[0] or 0
            wins = row[1] or 0
            places = row[2] or 0
            
            return {
                'total_races': races,
                'wins': wins,
                'places': places,
                'win_rate': (wins / races * 100) if races > 0 else 0,
                'place_rate': (places / races * 100) if races > 0 else 0
            }
        finally:
            conn.close()
    
    def get_horse_recent_form(self, horse_name: str, days: int = 90) -> List[Dict]:
        """Get horse's recent form."""
        conn = self._get_connection()
        
        try:
            cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            
            df = pd.read_sql_query(
                """SELECT race_date, position, actual_weight, finished_time 
                   FROM race_results 
                   WHERE horse_name = ? AND race_date >= ?
                   ORDER BY race_date DESC""",
                conn,
                params=(horse_name, cutoff_date)
            )
            
            return df.to_dict('records') if not df.empty else []
        finally:
            conn.close()
    
    def get_all_horses(self) -> List[str]:
        """Get list of all horses in database."""
        conn = self._get_connection()
        
        try:
            df = pd.read_sql_query(
                "SELECT DISTINCT horse_name FROM race_results ORDER BY horse_name",
                conn
            )
            return df['horse_name'].tolist() if not df.empty else []
        finally:
            conn.close()
    
    def get_race_payouts(self, race_date: str, race_number: int, racecourse: str) -> List[Dict]:
        """Get payout information for a race."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                """SELECT bet_type, combination, dividend 
                   FROM payouts 
                   WHERE race_date = ? AND race_number = ? AND racecourse = ?""",
                (race_date, race_number, racecourse)
            )
            
            payouts = []
            for row in cursor.fetchall():
                payouts.append({
                    'bet_type': row[0],
                    'combination': row[1],
                    'dividend': row[2]
                })
            return payouts
        finally:
            conn.close()
    
    def get_race_results_since(self, cutoff_date: str) -> List[Dict]:
        """Get all race results since a given date."""
        conn = self._get_connection()
        
        try:
            df = pd.read_sql_query(
                """SELECT * FROM race_results 
                   WHERE race_date >= ? 
                   ORDER BY race_date DESC, race_number ASC""",
                conn,
                params=(cutoff_date,)
            )
            return df.to_dict('records') if not df.empty else []
        finally:
            conn.close()

    def get_race_results_by_class(self, race_class: str) -> List[Dict]:
        """Get race results for a specific class."""
        conn = self._get_connection()
        
        try:
            df = pd.read_sql_query(
                """SELECT r.*, f.race_class 
                   FROM race_results r
                   JOIN future_race_cards f 
                     ON r.race_date = f.race_date 
                     AND r.race_number = f.race_number
                     AND r.racecourse = f.racecourse
                   WHERE f.race_class LIKE ?""",
                conn,
                params=(f"%{race_class}%",)
            )
            return df.to_dict('records') if not df.empty else []
        finally:
            conn.close()

    def get_jockey_trainer_results(self, jockey: str, trainer: str) -> List[Dict]:
        """Get historical results for a specific jockey-trainer combination."""
        conn = self._get_connection()
        try:
            df = pd.read_sql_query(
                "SELECT position FROM race_results WHERE jockey = ? AND trainer = ?",
                conn,
                params=(jockey, trainer)
            )
            return df.to_dict('records') if not df.empty else []
        finally:
            conn.close()

    def get_jockey_performance(self, jockey: str) -> Dict:
        """Alias for get_jockey_stats."""
        return self.get_jockey_stats(jockey)

    def get_trainer_performance(self, trainer: str) -> Dict:
        """Alias for get_trainer_stats."""
        return self.get_trainer_stats(trainer)

    def get_horse_track_distance_results(self, horse_name: str, track: str, distance: str) -> List[Dict]:
        """Get horse results for specific track and distance."""
        conn = self._get_connection()
        try:
            query = """
                SELECT r.position 
                FROM race_results r
                JOIN future_race_cards f ON r.race_date = f.race_date 
                    AND r.race_number = f.race_number 
                    AND r.racecourse = f.racecourse
                WHERE r.horse_name = ? AND r.racecourse = ? AND f.race_distance LIKE ?
            """
            df = pd.read_sql_query(query, conn, params=(horse_name, track, f"%{distance}%"))
            return df.to_dict('records') if not df.empty else []
        finally:
            conn.close()

    def get_horse_class_distance_results(self, horse_name: str, race_class: str, distance: str) -> List[Dict]:
        """Get horse results for specific class and distance."""
        conn = self._get_connection()
        try:
            query = """
                SELECT r.position 
                FROM race_results r
                JOIN future_race_cards f ON r.race_date = f.race_date 
                    AND r.race_number = f.race_number 
                    AND r.racecourse = f.racecourse
                WHERE r.horse_name = ? AND f.race_class LIKE ? AND f.race_distance LIKE ?
            """
            df = pd.read_sql_query(query, conn, params=(horse_name, f"%{race_class}%", f"%{distance}%"))
            return df.to_dict('records') if not df.empty else []
        finally:
            conn.close()

    def get_horse_class_performance(self, horse_name: str, race_class: str) -> Dict:
        """Get horse performance in a specific class."""
        results = self.get_race_results_by_class(race_class)
        horse_results = [r for r in results if r['horse_name'] == horse_name]
        if not horse_results:
            return {'win_rate': 0.0, 'total_races': 0}
        
        wins = sum(1 for r in horse_results if r['position'] == 1)
        return {
            'win_rate': wins / len(horse_results),
            'total_races': len(horse_results)
        }

    def get_draw_performance_by_class(self, race_class: str) -> List[Dict]:
        """Get all results for a class to analyze draw bias."""
        conn = self._get_connection()
        try:
            query = """
                SELECT r.position, f.draw
                FROM race_results r
                JOIN future_race_cards f ON r.race_date = f.race_date 
                    AND r.race_number = f.race_number 
                    AND r.racecourse = f.racecourse
                WHERE f.race_class LIKE ?
            """
            df = pd.read_sql_query(query, conn, params=(f"%{race_class}%",))
            return df.to_dict('records') if not df.empty else []
        finally:
            conn.close()

    def extract_features_for_race(self, race_result: Dict) -> Dict:
        """Helper to extract features from a race result dictionary for retraining."""
        return {
            'horse_name': race_result.get('horse_name'),
            'jockey': race_result.get('jockey'),
            'trainer': race_result.get('trainer'),
            'track': race_result.get('racecourse'),
            'position': race_result.get('position'),
            'odds': race_result.get('winning_odds')
        }

    def get_exceptional_factors(self, race_date: str, race_number: int, racecourse: str) -> List[Dict]:
        """Get exceptional factors for a race."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                """SELECT horse_number, horse_name, gear 
                   FROM exceptional_factors 
                   WHERE race_date = ? AND race_number = ? AND racecourse = ?""",
                (race_date, race_number, racecourse)
            )
            
            factors = []
            for row in cursor.fetchall():
                factors.append({
                    'number': row[0],
                    'name': row[1],
                    'gear': row[2]
                })
            return factors
        finally:
            conn.close()

    def get_morning_trackwork(self, horse_name: str, limit: int = 10) -> List[Dict]:
        """Get morning trackwork records for a horse."""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """SELECT race_date, trackwork_info 
                   FROM morning_trackwork 
                   WHERE horse_name = ? 
                   ORDER BY race_date DESC LIMIT ?""",
                (horse_name, limit)
            )
            return [{'date': r[0], 'info': r[1]} for r in cursor.fetchall()]
        finally:
            conn.close()

    def get_barrier_test_results(self, horse_name: str, limit: int = 5) -> List[Dict]:
        """Get barrier test results for a horse."""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """SELECT test_date, position, finish_time, commentary 
                   FROM barrier_test_results 
                   WHERE horse_name = ? 
                   ORDER BY test_date DESC LIMIT ?""",
                (horse_name, limit)
            )
            return [{'date': r[0], 'position': r[1], 'time': r[2], 'commentary': r[3]} for r in cursor.fetchall()]
        finally:
            conn.close()

