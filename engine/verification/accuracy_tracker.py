"""
Prediction Accuracy Tracker - Verifies model predictions against actual results.
Tracks win rate, place rate, ROI, and other performance metrics.
"""

import sqlite3
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class PredictionResult:
    """Result of a single prediction vs actual."""
    race_date: str
    race_number: int
    horse_name: str
    predicted_rank: int
    predicted_win_prob: float
    actual_position: Optional[int]
    odds: Optional[float]
    confidence: float
    
    @property
    def is_winner(self) -> bool:
        return self.actual_position == 1
    
    @property
    def is_place(self) -> bool:
        return self.actual_position is not None and self.actual_position <= 3
    
    @property
    def predicted_correctly(self) -> bool:
        return self.actual_position == self.predicted_rank
    
    @property
    def within_2_places(self) -> bool:
        if self.actual_position is None:
            return False
        return abs(self.actual_position - self.predicted_rank) <= 2


@dataclass
class AccuracyMetrics:
    """Overall accuracy metrics for a period."""
    total_predictions: int
    total_races: int
    winners_correct: int
    top3_correct: int
    top5_correct: int
    exact_rank_correct: int
    within_2_places: int
    
    win_rate: float
    place_rate: float
    roi_percent: float
    average_odds: float
    
    avg_position_error: float
    calibration_error: float
    
    def to_dict(self) -> Dict:
        return {
            'total_predictions': self.total_predictions,
            'total_races': self.total_races,
            'winners_correct': self.winners_correct,
            'top3_correct': self.top3_correct,
            'top5_correct': self.top5_correct,
            'exact_rank_correct': self.exact_rank_correct,
            'within_2_places': self.within_2_places,
            'win_rate': self.win_rate,
            'place_rate': self.place_rate,
            'roi_percent': self.roi_percent,
            'average_odds': self.average_odds,
            'avg_position_error': self.avg_position_error,
            'calibration_error': self.calibration_error
        }


class AccuracyTracker:
    """Tracks and calculates prediction accuracy metrics."""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            self.db_path = os.path.join(os.path.dirname(__file__), '..', 'database', 'hkjc_races.db')
        else:
            self.db_path = db_path
        
        self._ensure_tables()
    
    def _get_connection(self):
        return sqlite3.connect(self.db_path)
    
    def _ensure_tables(self):
        """Create accuracy tracking tables if needed."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Predictions storage table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS prediction_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                race_date TEXT,
                race_number INTEGER,
                racecourse TEXT,
                horse_name TEXT,
                horse_number INTEGER,
                predicted_rank INTEGER,
                predicted_win_prob REAL,
                predicted_place_prob REAL,
                confidence REAL,
                current_odds REAL,
                value_pct REAL,
                model_version TEXT,
                created_at TEXT,
                actual_position INTEGER,
                finished_time TEXT,
                validated_at TEXT
            )
        """)
        
        # Daily accuracy summary table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS accuracy_daily (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                race_date TEXT,
                racecourse TEXT,
                total_races INTEGER,
                total_predictions INTEGER,
                winners_correct INTEGER,
                top3_correct INTEGER,
                exact_rank_correct INTEGER,
                win_rate REAL,
                place_rate REAL,
                roi_percent REAL,
                avg_odds REAL,
                avg_position_error REAL,
                calibration_error REAL,
                computed_at TEXT
            )
        """)
        
        # Model version performance table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS model_performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_version TEXT,
                race_date_start TEXT,
                race_date_end TEXT,
                total_predictions INTEGER,
                win_rate REAL,
                place_rate REAL,
                roi_percent REAL,
                avg_position_error REAL,
                notes TEXT,
                computed_at TEXT
            )
        """)
        
        conn.commit()
        conn.close()
    
    def log_prediction(self, prediction_data: Dict, model_version: str = "v1.0"):
        """Log a prediction for later validation."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        created_at = datetime.now().isoformat()
        
        cursor.execute("""
            INSERT INTO prediction_log (
                race_date, race_number, racecourse, horse_name, horse_number,
                predicted_rank, predicted_win_prob, predicted_place_prob,
                confidence, current_odds, value_pct, model_version, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            prediction_data.get('race_date'),
            prediction_data.get('race_number'),
            prediction_data.get('racecourse'),
            prediction_data.get('horse_name'),
            prediction_data.get('horse_number'),
            prediction_data.get('predicted_rank'),
            prediction_data.get('win_probability', 0),
            prediction_data.get('place_probability', 0),
            prediction_data.get('confidence', 0),
            prediction_data.get('current_odds'),
            prediction_data.get('value_pct'),
            model_version,
            created_at
        ))
        
        conn.commit()
        conn.close()
        return cursor.lastrowid
    
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

    def validate_predictions(self, race_date: str, race_number: int = None, 
                           racecourse: str = None) -> List[PredictionResult]:
        """
        Validate logged predictions against actual results.
        Returns list of PredictionResult objects.
        """
        conn = self._get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get predictions
        query = """
            SELECT * FROM prediction_log 
            WHERE race_date = ?
        """
        params = [race_date]
        
        if race_number:
            query += " AND race_number = ?"
            params.append(race_number)
        
        if racecourse:
            query += " AND racecourse = ?"
            params.append(racecourse)
        
        cursor.execute(query, params)
        predictions = cursor.fetchall()
        
        if not predictions:
            conn.close()
            return []
        
        # Get actual results
        results_query = """
            SELECT horse_name, position, winning_odds, finished_time
            FROM race_results
            WHERE race_date = ? AND race_number = ?
        """
        
        actual_results = {}
        for pred in predictions:
            cursor.execute(results_query, (pred['race_date'], pred['race_number']))
            results = cursor.fetchall()
            for r in results:
                actual_results[r['horse_name']] = {
                    'position': self._parse_position(r['position']),
                    'odds': r['winning_odds'],
                    'time': r['finished_time']
                }
        
        conn.close()
        
        # Build prediction results
        results_list = []
        for pred in predictions:
            horse_name = pred['horse_name']
            actual = actual_results.get(horse_name, {})
            
            result = PredictionResult(
                race_date=pred['race_date'],
                race_number=pred['race_number'],
                horse_name=horse_name,
                predicted_rank=pred['predicted_rank'],
                predicted_win_prob=pred['predicted_win_prob'],
                actual_position=actual.get('position'),
                odds=actual.get('odds'),
                confidence=pred['confidence']
            )
            results_list.append(result)
            
            # Update the log with actual position
            self._update_validation(pred['id'], actual)
        
        return results_list
    
    def _update_validation(self, prediction_id: int, actual: Dict):
        """Update prediction log with actual results."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE prediction_log SET
                actual_position = ?,
                finished_time = ?,
                validated_at = ?
            WHERE id = ?
        """, (
            actual.get('position'),
            actual.get('time'),
            datetime.now().isoformat(),
            prediction_id
        ))
        
        conn.commit()
        conn.close()
    
    def calculate_metrics(self, predictions: List[PredictionResult]) -> AccuracyMetrics:
        """Calculate accuracy metrics from prediction results."""
        if not predictions:
            return AccuracyMetrics(
                total_predictions=0, total_races=0, winners_correct=0,
                top3_correct=0, top5_correct=0, exact_rank_correct=0,
                within_2_places=0, win_rate=0, place_rate=0, roi_percent=0,
                average_odds=0, avg_position_error=0, calibration_error=0
            )
        
        # Get unique races
        races = set((p.race_date, p.race_number) for p in predictions)
        
        # Count correct predictions
        winners_correct = sum(1 for p in predictions if p.is_winner)
        top3_correct = sum(1 for p in predictions if p.is_place)
        top5_correct = sum(1 for p in predictions 
                         if p.actual_position is not None and p.actual_position <= 5)
        exact_rank_correct = sum(1 for p in predictions if p.predicted_correctly)
        within_2_places = sum(1 for p in predictions if p.within_2_places)
        
        # Calculate position errors
        position_errors = []
        for p in predictions:
            if p.actual_position is not None:
                position_errors.append(abs(p.actual_position - p.predicted_rank))
        
        avg_position_error = sum(position_errors) / len(position_errors) if position_errors else 0
        
        # Calculate ROI (assuming $1 bet on each predicted winner)
        total_wagered = len([p for p in predictions if p.odds and p.odds > 0])
        total_won = sum(p.odds for p in predictions if p.is_winner and p.odds)
        roi_percent = ((total_won - total_wagered) / total_wagered * 100) if total_wagered > 0 else 0
        
        # Average odds
        valid_odds = [p.odds for p in predictions if p.odds and p.odds > 0]
        avg_odds = sum(valid_odds) / len(valid_odds) if valid_odds else 0
        
        # Calibration error (difference between predicted and actual win rate)
        high_conf_preds = [p for p in predictions if p.confidence > 0.7]
        if high_conf_preds:
            actual_high_win_rate = sum(1 for p in high_conf_preds if p.is_winner) / len(high_conf_preds)
            avg_high_conf = sum(p.confidence for p in high_conf_preds) / len(high_conf_preds)
            calibration_error = abs(avg_high_conf - actual_high_win_rate)
        else:
            calibration_error = 0
        
        return AccuracyMetrics(
            total_predictions=len(predictions),
            total_races=len(races),
            winners_correct=winners_correct,
            top3_correct=top3_correct,
            top5_correct=top5_correct,
            exact_rank_correct=exact_rank_correct,
            within_2_places=within_2_places,
            win_rate=winners_correct / len(predictions) * 100 if predictions else 0,
            place_rate=top3_correct / len(predictions) * 100 if predictions else 0,
            roi_percent=roi_percent,
            average_odds=avg_odds,
            avg_position_error=avg_position_error,
            calibration_error=calibration_error
        )
    
    def get_daily_summary(self, race_date: str, racecourse: str = None) -> Optional[Dict]:
        """Get or compute daily accuracy summary."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        query = "SELECT * FROM accuracy_daily WHERE race_date = ?"
        params = [race_date]
        
        if racecourse:
            query += " AND racecourse = ?"
            params.append(racecourse)
        
        cursor.execute(query, params)
        existing = cursor.fetchone()
        
        if existing:
            conn.close()
            return dict(existing)
        
        # Compute summary
        predictions = self.validate_predictions(race_date, racecourse=racecourse)
        metrics = self.calculate_metrics(predictions)
        
        # Store summary
        cursor.execute("""
            INSERT INTO accuracy_daily (
                race_date, racecourse, total_races, total_predictions,
                winners_correct, top3_correct, exact_rank_correct,
                win_rate, place_rate, roi_percent, avg_odds,
                avg_position_error, calibration_error, computed_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            race_date, racecourse, metrics.total_races, metrics.total_predictions,
            metrics.winners_correct, metrics.top3_correct, metrics.exact_rank_correct,
            metrics.win_rate, metrics.place_rate, metrics.roi_percent, metrics.average_odds,
            metrics.avg_position_error, metrics.calibration_error, datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
        
        return metrics.to_dict()
    
    def get_period_summary(self, start_date: str, end_date: str = None) -> AccuracyMetrics:
        """Get accuracy summary for a date range."""
        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')
        
        conn = self._get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM prediction_log
            WHERE race_date BETWEEN ? AND ?
            AND validated_at IS NOT NULL
        """, (start_date, end_date))
        
        predictions = []
        for row in cursor.fetchall():
            predictions.append(PredictionResult(
                race_date=row['race_date'],
                race_number=row['race_number'],
                horse_name=row['horse_name'],
                predicted_rank=row['predicted_rank'],
                predicted_win_prob=row['predicted_win_prob'],
                actual_position=row['actual_position'],
                odds=row['current_odds'],
                confidence=row['confidence']
            ))
        
        conn.close()
        
        return self.calculate_metrics(predictions)
    
    def get_leaderboard(self, top_n: int = 10) -> List[Dict]:
        """Get top performing horses/trainers/jockeys based on predictions."""
        conn = self._get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Top horses by prediction accuracy
        cursor.execute("""
            SELECT 
                horse_name,
                COUNT(*) as total_predictions,
                SUM(CASE WHEN actual_position = 1 THEN 1 ELSE 0 END) as wins,
                SUM(CASE WHEN actual_position <= 3 THEN 1 ELSE 0 END) as places,
                AVG(actual_position) as avg_position,
                SUM(CASE WHEN actual_position = predicted_rank THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as exact_rate
            FROM prediction_log
            WHERE validated_at IS NOT NULL
            GROUP BY horse_name
            HAVING total_predictions >= 5
            ORDER BY exact_rate DESC
            LIMIT ?
        """, (top_n,))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_roi_report(self, start_date: str = None, end_date: str = None,
                       bet_type: str = 'win', stake: float = 100) -> Dict:
        """Generate ROI report for betting strategy."""
        if start_date is None:
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        if bet_type == 'win':
            cursor.execute("""
                SELECT 
                    race_date,
                    SUM(CASE WHEN actual_position = 1 THEN current_odds * ? ELSE -? END) as daily_profit,
                    COUNT(*) as bets
                FROM prediction_log
                WHERE race_date BETWEEN ? AND ?
                AND predicted_rank = 1
                AND validated_at IS NOT NULL
                GROUP BY race_date
                ORDER BY race_date
            """, (stake, stake, start_date, end_date))
        elif bet_type == 'place':
            cursor.execute("""
                SELECT 
                    race_date,
                    SUM(CASE WHEN actual_position <= 3 THEN 1.1 * ? ELSE -? END) as daily_profit,
                    COUNT(*) as bets
                FROM prediction_log
                WHERE race_date BETWEEN ? AND ?
                AND predicted_rank <= 3
                AND validated_at IS NOT NULL
                GROUP BY race_date
                ORDER BY race_date
            """, (stake, stake, start_date, end_date))
        else:  # Each way
            cursor.execute("""
                SELECT 
                    race_date,
                    SUM(CASE 
                        WHEN actual_position = 1 THEN (current_odds + 1) * ? 
                        WHEN actual_position <= 3 THEN 0.1 * ?
                        ELSE -?
                    END) as daily_profit,
                    COUNT(*) as bets
                FROM prediction_log
                WHERE race_date BETWEEN ? AND ?
                AND validated_at IS NOT NULL
                GROUP BY race_date
                ORDER BY race_date
            """, (stake, stake, stake, start_date, end_date))
        
        results = cursor.fetchall()
        conn.close()
        
        total_profit = sum(r['daily_profit'] for r in results)
        total_bets = sum(r['bets'] for r in results)
        
        return {
            'bet_type': bet_type,
            'stake_per_bet': stake,
            'start_date': start_date,
            'end_date': end_date,
            'total_bets': total_bets,
            'total_profit': total_profit,
            'roi_percent': (total_profit / (total_bets * stake) * 100) if total_bets > 0 else 0,
            'daily_breakdown': [dict(r) for r in results]
        }


class PredictionVerifier:
    """Verifies prediction quality and model performance."""
    
    def __init__(self, db_path: str = None):
        self.tracker = AccuracyTracker(db_path)
    
    def verify_predictions_for_race(self, race_date: str, race_number: int,
                                   racecourse: str, predictions: List[Dict]) -> Dict:
        """Verify predictions for a single race against actual results."""
        # Log all predictions
        for i, pred in enumerate(predictions):
            self.tracker.log_prediction({
                'race_date': race_date,
                'race_number': race_number,
                'racecourse': racecourse,
                'horse_name': pred.get('horse_name'),
                'horse_number': pred.get('horse_number'),
                'predicted_rank': i + 1,
                'win_probability': pred.get('win_probability', 0),
                'place_probability': pred.get('place_probability', 0),
                'confidence': pred.get('confidence', 0),
                'current_odds': pred.get('current_odds'),
                'value_pct': pred.get('value_pct')
            })
        
        # Validate and get results
        results = self.tracker.validate_predictions(race_date, race_number, racecourse)
        metrics = self.tracker.calculate_metrics(results)
        
        return {
            'race_date': race_date,
            'race_number': race_number,
            'racecourse': racecourse,
            'predictions_count': len(predictions),
            'metrics': metrics.to_dict(),
            'detailed_results': [
                {
                    'horse_name': r.horse_name,
                    'predicted_rank': r.predicted_rank,
                    'actual_position': r.actual_position,
                    'predicted_prob': r.predicted_win_prob,
                    'is_winner': r.is_winner,
                    'is_place': r.is_place,
                    'within_2_places': r.within_2_places
                }
                for r in results
            ]
        }
    
    def get_model_health_check(self) -> Dict:
        """Get overall model health check."""
        # Get last 30 days performance
        thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        metrics = self.tracker.get_period_summary(thirty_days_ago)
        
        health = {
            'status': 'healthy',
            'issues': [],
            'warnings': [],
            'metrics': metrics.to_dict()
        }
        
        # Check for issues
        if metrics.win_rate < 10:
            health['status'] = 'critical'
            health['issues'].append('Win rate below 10%')
        elif metrics.win_rate < 15:
            health['warnings'].append('Win rate below 15%')
        
        if metrics.roi_percent < -20:
            health['status'] = 'critical'
            health['issues'].append('ROI below -20%')
        elif metrics.roi_percent < -10:
            health['warnings'].append('ROI below -10%')
        
        if metrics.calibration_error > 0.15:
            health['warnings'].append('Poor probability calibration')
        
        if metrics.avg_position_error > 3:
            health['warnings'].append('High average position error')
        
        return health
    
    def compare_models(self, predictions_a: List[Dict], predictions_b: List[Dict],
                      actual_results: Dict[str, int]) -> Dict:
        """Compare two prediction sets against actual results."""
        def calc_score(preds):
            score = 0
            for i, pred in enumerate(preds):
                horse = pred.get('horse_name')
                actual = actual_results.get(horse)
                if actual == i + 1:
                    score += 10  # Perfect prediction
                elif actual and actual <= 3 and i < 3:
                    score += 3  # Top 3 in predicted top 3
                elif actual and actual <= 5 and i < 5:
                    score += 1  # Top 5 in predicted top 5
            return score
        
        score_a = calc_score(predictions_a)
        score_b = calc_score(predictions_b)
        
        return {
            'model_a_score': score_a,
            'model_b_score': score_b,
            'winner': 'model_a' if score_a > score_b else 'model_b',
            'improvement': abs(score_a - score_b)
        }


# Convenience functions
def get_accuracy_summary(db_path: str = None, days: int = 30) -> Dict:
    """Get accuracy summary for the last N days."""
    tracker = AccuracyTracker(db_path)
    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    metrics = tracker.get_period_summary(start_date)
    return metrics.to_dict()


def verify_race_predictions(db_path: str = None) -> Dict:
    """Quick verification of all unvalidated predictions."""
    import sqlite3
    
    if db_path is None:
        db_path = os.path.join(os.path.dirname(__file__), '..', 'database', 'hkjc_races.db')
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get races with predictions but no validation
    cursor.execute("""
        SELECT DISTINCT race_date, race_number, racecourse
        FROM prediction_log
        WHERE validated_at IS NULL
        AND actual_position IS NOT NULL
    """)
    
    races_to_validate = cursor.fetchall()
    conn.close()
    
    verifier = PredictionVerifier(db_path)
    all_results = []
    
    for race_date, race_number, racecourse in races_to_validate:
        # Get predictions for this race
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM prediction_log
            WHERE race_date = ? AND race_number = ? AND racecourse = ?
            ORDER BY predicted_rank
        """, (race_date, race_number, racecourse))
        
        predictions = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        if predictions:
            result = verifier.verify_predictions_for_race(
                race_date, race_number, racecourse, predictions
            )
            all_results.append(result)
    
    return {
        'races_validated': len(all_results),
        'results': all_results
    }

