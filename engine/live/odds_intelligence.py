"""Odds intelligence: detecting smart money patterns and odds movement."""

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import numpy as np


class OddsMovementAnalyzer:
    """Analyzes odds movements to detect smart money and market sentiment."""
    
    def __init__(self, data_integrator):
        """Initialize with data integrator."""
        self.data = data_integrator
    
    def analyze_odds_movement(
        self,
        horse_number: int,
        race_date: str,
        race_number: int,
        track: str,
        hours_back: int = 24
    ) -> Dict:
        """
        Analyze how odds have moved over recent period.
        
        Detects sharp moves (smart money) vs gradual drifts.
        """
        odds_history = self.data.get_odds_history(
            horse_number, race_date, race_number, track
        )
        
        if not odds_history or len(odds_history) < 2:
            return {
                'odds_movement': 'Unknown',
                'movement_direction': None,
                'movement_magnitude': 0.0,
                'smart_money_indicator': 0.0,
                'price_pressure': 'Neutral'
            }
        
        oldest_odds = odds_history[-1]['win_odds']
        latest_odds = odds_history[0]['win_odds']
        
        if not oldest_odds or not latest_odds:
            return {
                'odds_movement': 'Unknown',
                'movement_direction': None,
                'movement_magnitude': 0.0,
                'smart_money_indicator': 0.0,
                'price_pressure': 'Neutral'
            }
        
        odds_change = (oldest_odds - latest_odds) / oldest_odds
        
        if odds_change > 0.1:
            direction = 'Shortening'
            pressure = 'Support'
        elif odds_change < -0.1:
            direction = 'Drifting'
            pressure = 'Resistance'
        else:
            direction = 'Stable'
            pressure = 'Neutral'
        
        smart_money = self._detect_smart_money(odds_history)
        
        return {
            'odds_movement': f'{abs(odds_change)*100:.1f}%',
            'movement_direction': direction,
            'movement_magnitude': float(odds_change),
            'smart_money_indicator': smart_money,
            'price_pressure': pressure
        }
    
    def detect_value_shift(
        self,
        horse_number: int,
        market_odds: float,
        model_probability: float,
        race_date: str,
        race_number: int,
        track: str
    ) -> Dict:
        """
        Detect if value has improved (or worsened) recently.
        
        Compares current odds to model prediction and tracks changes.
        """
        current_value = (market_odds * model_probability - 1) * 100
        
        odds_history = self.data.get_odds_history(
            horse_number, race_date, race_number, track, hours=6
        )
        
        if not odds_history:
            return {
                'current_value': float(current_value),
                'value_trend': 'Unknown',
                'value_deterioration': 0.0
            }
        
        historical_values = []
        for oh in odds_history:
            h_odds = oh['win_odds']
            if h_odds:
                h_value = (h_odds * model_probability - 1) * 100
                historical_values.append(h_value)
        
        if historical_values:
            avg_historical = np.mean(historical_values)
            value_change = current_value - avg_historical
            
            if value_change > 5:
                trend = 'Improving'
            elif value_change < -5:
                trend = 'Deteriorating'
            else:
                trend = 'Stable'
        else:
            trend = 'Unknown'
            value_change = 0.0
        
        return {
            'current_value': float(current_value),
            'value_trend': trend,
            'value_deterioration': float(-value_change)
        }
    
    def _detect_smart_money(self, odds_history: List[Dict]) -> float:
        """
        Detect smart money patterns in odds movement.
        
        Sharp sudden moves indicate smart money taking position.
        Returns score 0-1 indicating confidence of smart money presence.
        """
        if len(odds_history) < 3:
            return 0.0
        
        moves = []
        for i in range(len(odds_history) - 1):
            current = odds_history[i]['win_odds']
            previous = odds_history[i + 1]['win_odds']
            
            if current and previous:
                move = abs(current - previous) / previous
                moves.append(move)
        
        if not moves:
            return 0.0
        
        large_moves = sum(1 for m in moves if m > 0.15)
        total_moves = len(moves)
        
        if large_moves > 0 and total_moves > 0:
            smart_money_score = large_moves / total_moves
            return min(1.0, smart_money_score)
        
        return 0.0


class BettingLineAnalyzer:
    """Analyzes betting lines (win, place, trifecta) for anomalies."""
    
    def __init__(self, data_integrator):
        """Initialize with data integrator."""
        self.data = data_integrator
    
    def analyze_win_place_spread(
        self,
        horse_number: int,
        win_odds: float,
        place_odds: float
    ) -> Dict:
        """
        Analyze spread between win and place odds.
        
        Unusual spreads can indicate market sentiment shifts.
        """
        if not win_odds or not place_odds:
            return {
                'spread': None,
                'spread_interpretation': 'Unknown',
                'anomaly_score': 0.0
            }
        
        spread = win_odds - place_odds
        
        expected_spread = win_odds * 0.35
        actual_spread = spread
        
        anomaly = abs(actual_spread - expected_spread) / expected_spread if expected_spread != 0 else 0
        
        if anomaly > 0.2:
            interpretation = 'Unusual spread - market uncertainty'
        elif spread < 0:
            interpretation = 'Place odds higher than win (rare)'
        else:
            interpretation = 'Normal spread'
        
        return {
            'spread': float(spread),
            'spread_interpretation': interpretation,
            'anomaly_score': float(min(1.0, anomaly))
        }
    
    def detect_odds_pressure(
        self,
        race_number: int,
        race_date: str,
        track: str
    ) -> Dict:
        """
        Detect which horses have strongest odds pressure (smart money action).
        
        Returns ranking of horses by odds pressure strength.
        """
        race_odds = self.data.get_race_odds(race_date, race_number, track)
        
        if not race_odds:
            return {'pressure_ranking': []}
        
        pressure_scores = []
        
        for odds in race_odds:
            horse_num = odds['horse_number']
            odds_history = self.data.get_odds_history(
                horse_num, race_date, race_number, track, hours=6
            )
            
            if odds_history and len(odds_history) > 2:
                oldest = odds_history[-1]['win_odds']
                latest = odds_history[0]['win_odds']
                
                if oldest and latest:
                    move = (oldest - latest) / oldest
                    pressure_scores.append({
                        'horse_number': horse_num,
                        'pressure_strength': move,
                        'direction': 'Support' if move > 0 else 'Resistance'
                    })
        
        ranking = sorted(
            pressure_scores,
            key=lambda x: abs(x['pressure_strength']),
            reverse=True
        )
        
        return {
            'pressure_ranking': ranking[:5],
            'total_horses_analyzed': len(race_odds)
        }


class MarketSentimentAnalyzer:
    """Analyzes overall market sentiment and consensus."""
    
    def __init__(self, data_integrator):
        """Initialize with data integrator."""
        self.data = data_integrator
    
    def analyze_market_consensus(
        self,
        race_date: str,
        race_number: int,
        track: str
    ) -> Dict:
        """
        Analyze market consensus (how much money on favorites vs longshots).
        
        Returns sentiment metrics for the race.
        """
        race_odds = self.data.get_race_odds(race_date, race_number, track)
        
        if not race_odds:
            return {
                'favorite_bias': 'Unknown',
                'market_confidence': 0.0,
                'consensus_strength': 0.0
            }
        
        odds_list = [o['win_odds'] for o in race_odds if o['win_odds']]
        
        if len(odds_list) < 3:
            return {
                'favorite_bias': 'Unknown',
                'market_confidence': 0.0,
                'consensus_strength': 0.0
            }
        
        favorites = [o for o in odds_list if o <= 3.5]
        longshots = [o for o in odds_list if o > 6.0]
        
        favorite_concentration = len(favorites) / len(odds_list)
        
        odds_std = np.std(odds_list)
        market_confidence = 1.0 / (1.0 + odds_std / 2.0)
        
        if favorite_concentration > 0.4:
            bias = 'Heavy favorite bias'
        elif favorite_concentration < 0.2:
            bias = 'Balanced market'
        else:
            bias = 'Moderate favorite bias'
        
        consensus = 1.0 - (odds_std / (max(odds_list) - min(odds_list)))
        
        return {
            'favorite_bias': bias,
            'market_confidence': float(market_confidence),
            'consensus_strength': float(max(0, consensus))
        }
    
    def identify_contrarian_plays(
        self,
        race_date: str,
        race_number: int,
        track: str,
        model_predictions: List[Dict]
    ) -> List[Dict]:
        """
        Identify horses that model likes but market doesn't (contrarian picks).
        
        These can be valuable betting opportunities.
        """
        race_odds = self.data.get_race_odds(race_date, race_number, track)
        
        if not race_odds or not model_predictions:
            return []
        
        odds_dict = {o['horse_number']: o['win_odds'] for o in race_odds}
        
        contrarian_plays = []
        
        for pred in model_predictions:
            horse_num = pred['horse_number']
            model_prob = pred['win_probability']
            market_odds = odds_dict.get(horse_num)
            
            if market_odds:
                implied_prob = 1.0 / market_odds
                
                discrepancy = model_prob - implied_prob
                
                if discrepancy > 0.05:
                    ev = (market_odds * model_prob) - 1
                    
                    contrarian_plays.append({
                        'horse_number': horse_num,
                        'horse_name': pred['horse_name'],
                        'model_probability': float(model_prob),
                        'market_odds': float(market_odds),
                        'implied_probability': float(implied_prob),
                        'discrepancy': float(discrepancy),
                        'expected_value': float(ev)
                    })
        
        return sorted(
            contrarian_plays,
            key=lambda x: x['discrepancy'],
            reverse=True
        )
