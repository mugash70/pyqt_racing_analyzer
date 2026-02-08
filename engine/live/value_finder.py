"""Betting value detection and analysis."""

from typing import Dict, List
from ..prediction.probability_calculator import ProbabilityCalculator


class ValueFinder:
    """Finds betting value opportunities."""
    
    @staticmethod
    def calculate_value(estimated_probability: float, odds: float) -> float:
        """
        Calculate value of a bet.
        
        Positive value = underpriced, Negative value = overpriced
        """
        if odds is None or odds <= 0:
            return 0.0
        
        implied_probability = 1.0 / odds
        
        ev = (estimated_probability * odds) - 1.0
        
        return float(ev)
    
    @staticmethod
    def find_undervalued_horses(predictions: List[Dict]) -> List[Dict]:
        """Find horses with positive expected value when odds are available."""
        undervalued = []
        
        for pred in predictions:
            estimated_prob = pred.get('win_probability', 0) / 100.0
            odds = pred.get('current_odds')
            
            if odds is None or odds <= 0:
                continue
            
            value = ValueFinder.calculate_value(estimated_prob, odds)
            
            if value > 0.05:
                implied_prob = (1.0 / odds) * 100
                actual_prob = pred.get('win_probability', 0)
                
                undervalued.append({
                    'horse_name': pred.get('horse_name', ''),
                    'horse_number': pred.get('horse_number', 0),
                    'estimated_probability': actual_prob,
                    'implied_probability': implied_prob,
                    'current_odds': odds,
                    'fair_odds': 1.0 / (estimated_prob) if estimated_prob > 0 else 0,
                    'value': value * 100,
                    'confidence': pred.get('confidence', 0.5)
                })
        
        undervalued.sort(key=lambda x: x['value'], reverse=True)
        return undervalued
    
    @staticmethod
    def find_overvalued_horses(predictions: List[Dict]) -> List[Dict]:
        """Find horses with negative expected value."""
        overvalued = []
        
        for pred in predictions:
            estimated_prob = pred.get('win_probability', 0) / 100.0
            odds = pred.get('current_odds', 1.0)
            
            value = ValueFinder.calculate_value(estimated_prob, odds)
            
            if value < -0.05:
                implied_prob = (1.0 / odds) * 100
                actual_prob = pred.get('win_probability', 0)
                
                overvalued.append({
                    'horse_name': pred.get('horse_name', ''),
                    'horse_number': pred.get('horse_number', 0),
                    'estimated_probability': actual_prob,
                    'implied_probability': implied_prob,
                    'current_odds': odds,
                    'fair_odds': 1.0 / (estimated_prob) if estimated_prob > 0 else 0,
                    'value': value * 100,
                    'confidence': pred.get('confidence', 0.5)
                })
        
        overvalued.sort(key=lambda x: abs(x['value']), reverse=True)
        return overvalued
    
    @staticmethod
    def calculate_kelly_stake(probability: float, odds: float, 
                             bankroll: float) -> float:
        """
        Calculate optimal Kelly criterion stake.
        
        Args:
            probability: Estimated win probability (0-1)
            odds: Decimal odds
            bankroll: Available bankroll
            
        Returns:
            Recommended stake amount
        """
        if odds <= 1 or probability <= 0 or probability >= 1:
            return 0.0
        
        q = 1 - probability
        b = odds - 1
        
        kelly_fraction = (probability * b - q) / b
        
        if kelly_fraction <= 0:
            return 0.0
        
        half_kelly = kelly_fraction * 0.5
        
        stake = bankroll * half_kelly
        
        return float(max(0, stake))
    
    @staticmethod
    def rank_betting_opportunities(predictions: List[Dict], 
                                  min_value: float = 0.0) -> List[Dict]:
        """
        Rank horses by betting opportunity score.
        
        Combines value and confidence.
        """
        opportunities = []
        
        for pred in predictions:
            estimated_prob = pred.get('win_probability', 0) / 100.0
            odds = pred.get('current_odds', 1.0)
            confidence = pred.get('confidence', 0.5)
            
            value = ValueFinder.calculate_value(estimated_prob, odds)
            
            if value > min_value:
                score = (value * 100) * confidence
                
                opportunities.append({
                    'horse_name': pred.get('horse_name', ''),
                    'horse_number': pred.get('horse_number', 0),
                    'current_odds': odds,
                    'estimated_probability': pred.get('win_probability', 0),
                    'value_percentage': value * 100,
                    'confidence': confidence,
                    'opportunity_score': score,
                    'recommendation': ValueFinder._get_recommendation(score, value)
                })
        
        opportunities.sort(key=lambda x: x['opportunity_score'], reverse=True)
        return opportunities
    
    @staticmethod
    def _get_recommendation(score: float, value: float) -> str:
        """Get betting recommendation based on score and value."""
        if score > 0.5 and value > 0.2:
            return 'STRONG_BUY'
        elif score > 0.3 and value > 0.1:
            return 'BUY'
        elif score > 0.15 and value > 0.05:
            return 'CONSIDER'
        elif value < -0.1:
            return 'AVOID'
        else:
            return 'NEUTRAL'
    
    @staticmethod
    def calculate_parlay_odds(individual_odds: List[float]) -> float:
        """Calculate combined odds for multi-leg parlay."""
        if not individual_odds:
            return 0.0
        
        parlay_odds = 1.0
        for odds in individual_odds:
            if odds > 0:
                parlay_odds *= odds
        
        return float(parlay_odds)
    
    @staticmethod
    def identify_mispriced_races(races: List[Dict]) -> List[Dict]:
        """Identify races with significant value opportunities."""
        mispriced = []
        
        for race in races:
            predictions = race.get('predictions', [])
            undervalued = ValueFinder.find_undervalued_horses(predictions)
            
            if len(undervalued) >= 2:
                mispriced.append({
                    'race': race.get('race_info', {}),
                    'value_count': len(undervalued),
                    'top_value': undervalued[0] if undervalued else None,
                    'all_value_horses': undervalued[:3]
                })
        
        return mispriced
