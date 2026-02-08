"""
Model Verifier - Comprehensive model verification and comparison tool.
Validates prediction quality, checks calibration, and compares model versions.
"""

import sqlite3
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import numpy as np
import json
from dataclasses import dataclass, asdict


@dataclass
class VerificationReport:
    """Complete verification report for model."""
    model_version: str
    verification_date: str
    period_start: str
    period_end: str
    
    # Coverage stats
    total_races: int
    total_predictions: int
    validated_predictions: int
    validation_rate: float
    
    # Accuracy metrics
    win_rate: float
    place_rate: float
    top5_rate: float
    exact_rank_accuracy: float
    avg_position_error: float
    
    # Calibration metrics
    calibration_score: float
    brier_score: float
    confidence_accuracy_correlation: float
    
    # ROI metrics
    roi_percent: float
    profit_loss: float
    total_staked: float
    
    # Risk metrics
    avg_odds: float
    max_consecutive_losses: int
    best_streak: int
    
    # Per-racecourse stats
    st_performance: Dict
    hv_performance: Dict
    
    # Recommendations
    recommendations: List[str]


class ModelVerifier:
    """Comprehensive model verification and analysis."""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            self.db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'database', 'hkjc_races.db')
        else:
            self.db_path = db_path
    
    def _get_connection(self):
        return sqlite3.connect(self.db_path)
    
    def verify_model(self, model_version: str = "v1.0", 
                    days: int = 30) -> VerificationReport:
        """Generate comprehensive verification report."""
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        end_date = datetime.now().strftime('%Y-%m-%d')
        
        conn = self._get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get predictions for period
        cursor.execute("""
            SELECT * FROM prediction_log
            WHERE created_at >= ?
            AND model_version = ?
            ORDER BY race_date, race_number, predicted_rank
        """, (start_date, model_version))
        
        predictions = [dict(row) for row in cursor.fetchall()]
        
        # Get validated predictions
        validated = [p for p in predictions if p.get('validated_at')]
        
        conn.close()
        
        if not validated:
            return self._empty_report(model_version, start_date, end_date)
        
        # Calculate metrics
        total_races = len(set((p['race_date'], p['race_number']) for p in predictions))
        validated_races = set((p['race_date'], p['race_number']) for p in validated)
        
        # Accuracy metrics
        winners = [p for p in validated if p['actual_position'] == 1]
        top3 = [p for p in validated if p['actual_position'] and p['actual_position'] <= 3]
        top5 = [p for p in validated if p['actual_position'] and p['actual_position'] <= 5]
        exact = [p for p in validated if p['actual_position'] == p['predicted_rank']]
        
        win_rate = len(winners) / len(validated) * 100 if validated else 0
        place_rate = len(top3) / len(validated) * 100 if validated else 0
        top5_rate = len(top5) / len(validated) * 100 if validated else 0
        exact_rank_accuracy = len(exact) / len(validated) * 100 if validated else 0
        
        # Position error
        position_errors = []
        for p in validated:
            if p['actual_position']:
                position_errors.append(abs(p['actual_position'] - p['predicted_rank']))
        avg_position_error = np.mean(position_errors) if position_errors else 0
        
        # ROI calculation
        total_odds = sum(p['current_odds'] for p in validated 
                        if p['current_odds'] and p['current_odds'] > 0)
        total_wagered = len([p for p in validated if p['current_odds'] and p['current_odds'] > 0])
        roi_percent = ((total_odds - total_wagered) / total_wagered * 100) if total_wagered > 0 else 0
        
        # Calibration analysis
        calibration_score = self._calculate_calibration(validated)
        brier_score = self._calculate_brier_score(validated)
        conf_acc_corr = self._calculate_confidence_correlation(validated)
        
        # Risk metrics
        avg_odds = total_odds / total_wagered if total_wagered > 0 else 0
        max_consecutive = self._calculate_max_consecutive_losses(validated)
        best_streak = self._calculate_best_streak(validated)
        
        # Per-racecourse performance
        st_preds = [p for p in validated if p.get('racecourse') == 'ST']
        hv_preds = [p for p in validated if p.get('racecourse') == 'HV']
        
        st_perf = self._calculate_performance_metrics(st_preds)
        hv_perf = self._calculate_performance_metrics(hv_preds)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            win_rate, place_rate, roi_percent, calibration_score, avg_position_error
        )
        
        return VerificationReport(
            model_version=model_version,
            verification_date=datetime.now().isoformat(),
            period_start=start_date,
            period_end=end_date,
            total_races=total_races,
            total_predictions=len(predictions),
            validated_predictions=len(validated),
            validation_rate=len(validated_races) / total_races * 100 if total_races > 0 else 0,
            win_rate=win_rate,
            place_rate=place_rate,
            top5_rate=top5_rate,
            exact_rank_accuracy=exact_rank_accuracy,
            avg_position_error=avg_position_error,
            calibration_score=calibration_score,
            brier_score=brier_score,
            confidence_accuracy_correlation=conf_acc_corr,
            roi_percent=roi_percent,
            profit_loss=total_odds - total_wagered,
            total_staked=total_wagered,
            avg_odds=avg_odds,
            max_consecutive_losses=max_consecutive,
            best_streak=best_streak,
            st_performance=st_perf,
            hv_performance=hv_perf,
            recommendations=recommendations
        )
    
    def _empty_report(self, model_version: str, start: str, end: str) -> VerificationReport:
        """Return empty report when no data available."""
        return VerificationReport(
            model_version=model_version,
            verification_date=datetime.now().isoformat(),
            period_start=start,
            period_end=end,
            total_races=0,
            total_predictions=0,
            validated_predictions=0,
            validation_rate=0,
            win_rate=0,
            place_rate=0,
            top5_rate=0,
            exact_rank_accuracy=0,
            avg_position_error=0,
            calibration_score=0,
            brier_score=0,
            confidence_accuracy_correlation=0,
            roi_percent=0,
            profit_loss=0,
            total_staked=0,
            avg_odds=0,
            max_consecutive_losses=0,
            best_streak=0,
            st_performance={},
            hv_performance={},
            recommendations=["No validated predictions available for analysis"]
        )
    
    def _calculate_calibration(self, predictions: List[Dict]) -> float:
        """Calculate calibration score (how well predicted probabilities match actual outcomes)."""
        if not predictions:
            return 0
        
        # Bin predictions by confidence level
        bins = [(0, 0.2), (0.2, 0.4), (0.4, 0.6), (0.6, 0.8), (0.8, 1.0)]
        bin_stats = {b: {'total': 0, 'wins': 0} for b in bins}
        
        for p in predictions:
            prob = p['predicted_win_prob'] / 100 if p['predicted_win_prob'] > 1 else p['predicted_win_prob']
            for low, high in bins:
                if low <= prob < high:
                    bin_stats[(low, high)]['total'] += 1
                    if p['actual_position'] == 1:
                        bin_stats[(low, high)]['wins'] += 1
                    break
        
        # Calculate calibration error
        calibration_error = 0
        for (low, high), stats in bin_stats.items():
            if stats['total'] > 0:
                actual_rate = stats['wins'] / stats['total']
                expected_rate = (low + high) / 2
                calibration_error += abs(actual_rate - expected_rate) * (stats['total'] / len(predictions))
        
        # Return calibration score (1 - error)
        return max(0, 1 - calibration_error * 2)  # Scale to 0-1
    
    def _calculate_brier_score(self, predictions: List[Dict]) -> float:
        """Calculate Brier score (lower is better)."""
        if not predictions:
            return 0
        
        brier = 0
        for p in predictions:
            prob = p['predicted_win_prob'] / 100 if p['predicted_win_prob'] > 1 else p['predicted_win_prob']
            actual = 1 if p['actual_position'] == 1 else 0
            brier += (prob - actual) ** 2
        
        return brier / len(predictions)
    
    def _calculate_confidence_correlation(self, predictions: List[Dict]) -> float:
        """Calculate correlation between confidence and accuracy."""
        if len(predictions) < 10:
            return 0
        
        confs = [p['confidence'] for p in predictions]
        accs = [1 if p['actual_position'] == p['predicted_rank'] else 0 for p in predictions]
        
        if np.std(confs) == 0 or np.std(accs) == 0:
            return 0
        
        correlation = np.corrcoef(confs, accs)[0, 1]
        return correlation if not np.isnan(correlation) else 0
    
    def _calculate_max_consecutive_losses(self, predictions: List[Dict]) -> int:
        """Calculate maximum consecutive losses."""
        if not predictions:
            return 0
        
        max_streak = 0
        current_streak = 0
        
        for p in predictions:
            if p['actual_position'] != 1:  # Loss
                current_streak += 1
                max_streak = max(max_streak, current_streak)
            else:  # Win
                current_streak = 0
        
        return max_streak
    
    def _calculate_best_streak(self, predictions: List[Dict]) -> int:
        """Calculate best winning streak (winners correctly predicted)."""
        if not predictions:
            return 0
        
        max_streak = 0
        current_streak = 0
        
        for p in predictions:
            if p['actual_position'] == 1:  # Correct prediction
                current_streak += 1
                max_streak = max(max_streak, current_streak)
            else:  # Wrong
                current_streak = 0
        
        return max_streak
    
    def _calculate_performance_metrics(self, predictions: List[Dict]) -> Dict:
        """Calculate performance metrics for a subset of predictions."""
        if not predictions:
            return {'races': 0, 'win_rate': 0, 'place_rate': 0, 'roi': 0}
        
        races = len(set((p['race_date'], p['race_number']) for p in predictions))
        winners = [p for p in predictions if p['actual_position'] == 1]
        top3 = [p for p in predictions if p['actual_position'] and p['actual_position'] <= 3]
        
        total_odds = sum(p['current_odds'] for p in predictions if p['current_odds'] and p['current_odds'] > 0)
        total_wagered = len([p for p in predictions if p['current_odds'] and p['current_odds'] > 0])
        
        roi = ((total_odds - total_wagered) / total_wagered * 100) if total_wagered > 0 else 0
        
        return {
            'races': races,
            'predictions': len(predictions),
            'wins': len(winners),
            'win_rate': len(winners) / len(predictions) * 100 if predictions else 0,
            'place_rate': len(top3) / len(predictions) * 100 if predictions else 0,
            'roi': roi
        }
    
    def _generate_recommendations(self, win_rate: float, place_rate: float,
                                 roi: float, calibration: float, 
                                 avg_error: float) -> List[str]:
        """Generate recommendations based on metrics."""
        recs = []
        
        if win_rate < 10:
            recs.append("⚠️ Win rate below 10% - Review model features and training data")
        elif win_rate > 20:
            recs.append("✅ Excellent win rate above 20%")
        
        if roi < -15:
            recs.append("⚠️ ROI significantly negative - Consider adjusting betting strategy")
        elif roi > 10:
            recs.append("✅ Strong positive ROI")
        
        if calibration < 0.7:
            recs.append("⚠️ Poor probability calibration - Model may be overconfident")
        
        if avg_error > 3:
            recs.append(f"⚠️ High average position error ({avg_error:.1f}) - Improve ranking logic")
        
        if place_rate < 35:
            recs.append("⚠️ Place rate below 35% - Focus on place predictions")
        
        if not recs:
            recs.append("✅ Model performance within acceptable ranges")
        
        return recs
    
    def compare_versions(self, version_a: str = "v1.0", 
                        version_b: str = "v2.0",
                        days: int = 30) -> Dict:
        """Compare two model versions."""
        report_a = self.verify_model(version_a, days)
        report_b = self.verify_model(version_b, days)
        
        return {
            'version_a': asdict(report_a),
            'version_b': asdict(report_b),
            'comparison': {
                'win_rate_improvement': report_b.win_rate - report_a.win_rate,
                'place_rate_improvement': report_b.place_rate - report_a.place_rate,
                'roi_improvement': report_b.roi_percent - report_a.roi_percent,
                'calibration_improvement': report_b.calibration_score - report_a.calibration_score,
                'winner': version_b if report_b.win_rate > report_a.win_rate else version_a
            }
        }
    
    def get_detailed_race_analysis(self, race_date: str, race_number: int,
                                  racecourse: str) -> Dict:
        """Get detailed analysis for a specific race."""
        conn = self._get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM prediction_log
            WHERE race_date = ? AND race_number = ? AND racecourse = ?
            ORDER BY predicted_rank
        """, (race_date, race_number, racecourse))
        
        predictions = [dict(row) for row in cursor.fetchall()]
        
        # Get actual results
        cursor.execute("""
            SELECT * FROM race_results
            WHERE race_date = ? AND race_number = ? AND racecourse = ?
            ORDER BY position
        """, (race_date, race_number, racecourse))
        
        results = {row['horse_name']: dict(row) for row in cursor.fetchall()}
        conn.close()
        
        if not predictions:
            return {'error': 'No predictions found for this race'}
        
        analysis = {
            'race_info': {
                'date': race_date,
                'number': race_number,
                'racecourse': racecourse,
                'total_predictions': len(predictions)
            },
            'predictions': [],
            'analysis': {
                'top_pick_correct': predictions[0].get('actual_position') == 1 if predictions else None,
                'top3_included_winner': any(p.get('actual_position') == 1 for p in predictions[:3]),
                'predicted_winner_odds': predictions[0].get('current_odds') if predictions else None,
                'actual_winner_odds': results.get(predictions[0].get('horse_name'), {}).get('winning_odds') if predictions else None
            },
            'grade': self._grade_prediction(predictions, results)
        }
        
        # Add detailed prediction info
        for i, pred in enumerate(predictions):
            actual = results.get(pred['horse_name'], {})
            analysis['predictions'].append({
                'rank': i + 1,
                'horse_name': pred['horse_name'],
                'predicted_prob': pred['predicted_win_prob'],
                'confidence': pred['confidence'],
                'actual_position': actual.get('position'),
                'finished_time': actual.get('finished_time'),
                'result': '✓' if actual.get('position') == i + 1 else ('~' if actual.get('position') and actual.get('position') <= 3 else '✗')
            })
        
        return analysis
    
    def _grade_prediction(self, predictions: List[Dict], results: Dict) -> str:
        """Grade the overall prediction quality."""
        if not predictions:
            return 'N/A'
        
        top_pick_won = predictions[0].get('actual_position') == 1
        top3_has_winner = any(p.get('actual_position') == 1 for p in predictions[:3])
        exact_count = sum(1 for p in predictions if p.get('actual_position') == p.get('predicted_rank'))
        
        score = 0
        if top_pick_won:
            score += 50
        elif top3_has_winner:
            score += 30
        score += exact_count * 10
        
        if score >= 80:
            return 'A+'
        elif score >= 60:
            return 'A'
        elif score >= 40:
            return 'B'
        elif score >= 20:
            return 'C'
        else:
            return 'D'
    
    def export_report(self, report: VerificationReport, format: str = 'json') -> str:
        """Export verification report in specified format."""
        if format == 'json':
            return json.dumps(asdict(report), indent=2)
        elif format == 'text':
            lines = [
                f"Model Verification Report",
                f"=" * 50,
                f"Model Version: {report.model_version}",
                f"Period: {report.period_start} to {report.period_end}",
                f"",
                f"Coverage:",
                f"  Total Races: {report.total_races}",
                f"  Total Predictions: {report.total_predictions}",
                f"  Validated: {report.validated_predictions} ({report.validation_rate:.1f}%)",
                f"",
                f"Accuracy:",
                f"  Win Rate: {report.win_rate:.1f}%",
                f"  Place Rate: {report.place_rate:.1f}%",
                f"  Top 5 Rate: {report.top5_rate:.1f}%",
                f"  Exact Rank: {report.exact_rank_accuracy:.1f}%",
                f"  Avg Position Error: {report.avg_position_error:.2f}",
                f"",
                f"Calibration:",
                f"  Calibration Score: {report.calibration_score:.2f}",
                f"  Brier Score: {report.brier_score:.4f}",
                f"  Confidence-Accuracy Correlation: {report.confidence_accuracy_correlation:.2f}",
                f"",
                f"ROI:",
                f"  ROI: {report.roi_percent:.1f}%",
                f"  Profit/Loss: ${report.profit_loss:.2f}",
                f"  Total Staked: ${report.total_staked:.2f}",
                f"  Avg Odds: {report.avg_odds:.2f}",
                f"",
                f"Risk:",
                f"  Max Consecutive Losses: {report.max_consecutive_losses}",
                f"  Best Streak: {report.best_streak}",
                f"",
                f"Recommendations:",
            ]
            for rec in report.recommendations:
                lines.append(f"  {rec}")
            
            return '\n'.join(lines)
        else:
            raise ValueError(f"Unknown format: {format}")


# Convenience functions
def quick_verify(days: int = 30) -> VerificationReport:
    """Quick verification of current model."""
    verifier = ModelVerifier()
    return verifier.verify_model(days=days)


def compare_with_previous(days: int = 30) -> Dict:
    """Compare current model with previous version."""
    verifier = ModelVerifier()
    return verifier.compare_versions("v1.0", "v2.0", days)

