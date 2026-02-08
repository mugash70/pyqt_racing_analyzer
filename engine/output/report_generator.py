"""Detailed race analysis report generation."""

from typing import Dict, List
from datetime import datetime


class ReportGenerator:
    """Generates detailed race analysis reports."""
    
    @staticmethod
    def _get_track_name(track_code: str) -> str:
        """Convert track code to display name."""
        track_map = {'ST': 'Sha Tin', 'HV': 'Happy Valley'}
        return track_map.get(track_code, track_code)
    
    @staticmethod
    def generate_race_report(predictions: Dict) -> str:
        """
        Generate detailed text report for a race.
        
        Args:
            predictions: Race predictions dictionary
            
        Returns:
            Formatted text report
        """
        report = []
        
        race_info = predictions.get('race_info', {})
        track_code = race_info.get('track', 'UNKNOWN')
        track_name = ReportGenerator._get_track_name(track_code)
        
        report.append("=" * 90)
        report.append(f"RACE REPORT - {track_name} Race {race_info.get('number', '?')}")
        report.append(f"Date: {race_info.get('date', 'Unknown')}")
        distance = race_info.get('distance') or 'TBA'
        race_class = race_info.get('class') or 'TBA'
        going = race_info.get('going') or 'TBA'
        report.append(f"Distance: {distance}")
        report.append(f"Class: {race_class}")
        report.append(f"Going: {going}")
        report.append(f"Field Size: {predictions.get('field_size', '?')}")
        report.append("=" * 90)
        report.append("")
        
        # Add Detailed Analysis if available
        if predictions.get('analysis'):
            report.append("EXPERT ANALYSIS")
            report.append("-" * 90)
            report.append(predictions['analysis'])
            report.append("-" * 90)
            report.append("")
        
        predictions_list = predictions.get('predictions', [])
        
        report.append("PREDICTED FINISHING ORDER")
        report.append("-" * 90)
        report.append(f"{'#':<3} {'Horse':<20} {'Jockey':<15} {'Win%':<8} {'Place%':<8} {'Odds':<8} {'Value%':<8}")
        report.append("-" * 90)
        
        for i, pred in enumerate(predictions_list, 1):
            horse = pred.get('horse_name', 'Unknown')[:19]
            jockey = pred.get('jockey', 'Unknown')[:14]
            win_prob = pred.get('win_probability', 0)
            place_prob = pred.get('place_probability', 0)
            current_odds = pred.get('current_odds')
            value_pct = pred.get('value_pct')
            
            win_prob_str = f"{win_prob:.1f}%"
            place_prob_str = f"{place_prob:.1f}%"
            odds_str = f"{current_odds:.1f}" if current_odds else "N/A"
            value_str = f"{value_pct:+.0f}%" if value_pct is not None else "N/A"
            
            report.append(f"{i:<3} {horse:<20} {jockey:<15} {win_prob_str:<8} {place_prob_str:<8} {odds_str:<8} {value_str:<8}")
            
            # Add mathematical explanation if available
            explanation = pred.get('mathematical_explanation')
            if explanation:
                factors = explanation.get('base_factors', {})
                factor_strs = [f"{k}: {v*100:+.1f}%" for k, v in factors.items()]
                report.append(f"    [Math] {' | '.join(factor_strs)}")
                report.append(f"    [Final] Base Prob: {explanation.get('final_calibrated_prob', 0)*100:.1f}% | Multiplier: x{explanation.get('interaction_multiplier', 1.0):.2f}")
        
        report.append("")
        report.append("=" * 90)
        report.append("KEY RECOMMENDATIONS")
        report.append("=" * 90)
        
        top_picks = predictions.get('top_3', [])
        if top_picks:
            report.append("\nTop Picks:")
            for i, pick in enumerate(top_picks, 1):
                name = pick.get('horse_name', 'Unknown')
                prob = pick.get('win_probability', 0)
                report.append(f"  {i}. {name} - {prob:.1f}% win probability")
        
        value_picks = predictions.get('value_picks', [])
        if value_picks:
            report.append("\nValue Picks:")
            for pick in value_picks[:3]:
                name = pick.get('horse_name', 'Unknown')
                prob = pick.get('win_probability', 0)
                odds = pick.get('current_odds')
                odds_str = f"@ {odds:.1f}" if odds else "(no odds available)"
                report.append(f"  • {name} - {prob:.1f}% {odds_str}")
        
        risk_horses = predictions.get('high_risk_horses', [])
        if risk_horses:
            report.append("\nHighest Risk Horses:")
            for horse in risk_horses[:3]:
                name = horse.get('horse_name', 'Unknown')
                risk = horse.get('risk_score', 0)
                report.append(f"  ⚠ {name} - Risk Score: {risk:.0f}/100")
        
        report.append("")
        report.append("=" * 70)
        
        return "\n".join(report)
    
    @staticmethod
    def generate_horse_report(horse_name: str, prediction: Dict, 
                             universal_profile: Dict, track_profile: Dict,
                             risk_profile: Dict) -> str:
        """
        Generate detailed individual horse analysis.
        
        Args:
            horse_name: Name of horse
            prediction: Race prediction data
            universal_profile: Universal capability profile
            track_profile: Track-specific profile
            risk_profile: Risk assessment profile
            
        Returns:
            Formatted text report
        """
        report = []
        
        report.append("=" * 70)
        report.append(f"DETAILED HORSE ANALYSIS: {horse_name}")
        report.append("=" * 70)
        report.append("")
        
        report.append("BASIC INFORMATION")
        report.append("-" * 70)
        report.append(f"Jockey: {prediction.get('jockey', 'Unknown')}")
        report.append(f"Trainer: {prediction.get('trainer', 'Unknown')}")
        report.append(f"Weight: {prediction.get('weight', 'Unknown')}")
        report.append(f"Draw: {prediction.get('draw', '?')}")
        report.append("")
        
        report.append("CAPABILITY SCORES")
        report.append("-" * 70)
        report.append(f"Universal Score: {prediction.get('universal_score', 0):.1f}/100")
        report.append(f"Track Score: {prediction.get('track_score', 0):.1f}/100")
        report.append(f"Win Probability: {prediction.get('win_probability', 0):.1f}%")
        report.append(f"Place Probability: {prediction.get('place_probability', 0):.1f}%")
        report.append("")
        
        report.append("CURRENT ODDS")
        report.append("-" * 70)
        report.append(f"Win Odds: {prediction.get('current_odds', 0):.2f}")
        report.append("")
        
        report.append("RISK ASSESSMENT")
        report.append("-" * 70)
        risk_factors = prediction.get('risk_factors', {})
        report.append(f"Overall Risk Score: {prediction.get('risk_score', 0):.0f}/100")
        report.append(f"Recommendation: {prediction.get('risk_recommendation', 'Unknown')}")
        report.append("")
        
        if risk_factors:
            for factor, level in risk_factors.items():
                report.append(f"  • {factor.replace('_', ' ').title()}: {level}")
        
        report.append("")
        report.append("=" * 90)
        
        return "\n".join(report)
    
    @staticmethod
    def generate_summary(predictions: Dict, num_races: int = 1) -> str:
        """Generate executive summary."""
        summary = []
        summary.append("RACING PREDICTIONS SUMMARY")
        summary.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        summary.append(f"Races Analyzed: {num_races}")
        summary.append("")
        
        if predictions:
            top_pick = predictions.get('predictions', [{}])[0]
            summary.append(f"Top Pick: {top_pick.get('horse_name', 'Unknown')}")
            summary.append(f"Confidence: {top_pick.get('confidence', 0):.0%}")
        
        return "\n".join(summary)
