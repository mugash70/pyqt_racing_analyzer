"""Kelly criterion and fractional Kelly bet sizing for risk management."""

from typing import Dict, List, Optional, Tuple
import numpy as np
from datetime import datetime


class KellyCriterion:
    """
    Implements Kelly criterion and fractional Kelly for optimal bet sizing.
    
    Kelly Criterion: f* = (bp - q) / b
    where:
        f* = fraction of bankroll to bet
        b = odds - 1
        p = probability of winning
        q = probability of losing (1 - p)
    
    Uses fractional Kelly for safety (25%, 50%, 75% of full Kelly).
    """

    def __init__(self, bankroll: float = 1000.0):
        """
        Initialize Kelly calculator.
        
        Args:
            bankroll: Total bankroll for betting (default 1000)
        """
        self.bankroll = bankroll
        self.min_kelly = 0.0  # No bet if Kelly < 0%
        self.max_kelly = 0.25  # Never bet more than 25% of bankroll

    @staticmethod
    def calculate_full_kelly(win_probability: float, odds: float) -> float:
        """
        Calculate full Kelly fraction.
        
        Args:
            win_probability: Probability of winning (0.0 to 1.0)
            odds: Decimal odds (e.g., 3.0 means win $3 for $1 bet)
        
        Returns:
            Kelly fraction as decimal (0.0 to 1.0)
        """
        if odds <= 1.0 or win_probability <= 0 or win_probability >= 1:
            return 0.0
        
        p = win_probability
        q = 1 - win_probability
        b = odds - 1
        
        kelly = (b * p - q) / b
        
        return max(0.0, kelly)

    def calculate_fractional_kelly(
        self, 
        win_probability: float, 
        odds: float, 
        fraction: float = 0.25
    ) -> float:
        """
        Calculate fractional Kelly (safer than full Kelly).
        
        Args:
            win_probability: Probability of winning (0.0 to 1.0)
            odds: Decimal odds
            fraction: Fraction of full Kelly to use (default 0.25 = 25%)
        
        Returns:
            Kelly fraction as decimal
        """
        full_kelly = self.calculate_full_kelly(win_probability, odds)
        return full_kelly * fraction

    def calculate_bet_amount(
        self,
        win_probability: float,
        odds: float,
        kelly_fraction: float = 0.25,
        min_bet: float = 10.0,
        max_bet: Optional[float] = None
    ) -> Dict[str, float]:
        """
        Calculate actual bet amount based on Kelly criterion.
        
        Args:
            win_probability: Probability of winning (0.0 to 1.0)
            odds: Decimal odds
            kelly_fraction: Use this fraction of Kelly (0.25, 0.5, 0.75)
            min_bet: Minimum bet amount (default $10)
            max_bet: Maximum bet amount (optional)
        
        Returns:
            Dictionary with bet sizing details
        """
        if max_bet is None:
            max_bet = self.bankroll * self.max_kelly
        
        kelly_pct = self.calculate_fractional_kelly(
            win_probability, 
            odds, 
            kelly_fraction
        )
        
        bet_amount = self.bankroll * kelly_pct
        
        bet_amount = max(min_bet, min(bet_amount, max_bet))
        
        expected_value = (win_probability * (odds - 1) - (1 - win_probability)) * bet_amount
        
        return {
            'full_kelly_pct': self.calculate_full_kelly(win_probability, odds) * 100,
            'fractional_kelly_pct': kelly_pct * 100,
            'kelly_fraction_used': kelly_fraction,
            'bet_amount': round(bet_amount, 2),
            'min_bet': min_bet,
            'max_bet': max_bet,
            'expected_value': round(expected_value, 2),
            'win_probability': round(win_probability * 100, 1),
            'odds': odds,
            'recommendation': self._get_bet_recommendation(kelly_pct, expected_value, bet_amount)
        }

    def _get_bet_recommendation(self, kelly_pct: float, expected_value: float, bet_amount: float) -> str:
        """Generate recommendation based on Kelly percentage and EV."""
        if kelly_pct <= 0:
            return "SKIP - Negative Kelly (bad bet)"
        elif kelly_pct < 0.01:
            return "MINIMAL - Very small edge"
        elif kelly_pct < 0.05 and expected_value < 0:
            return "AVOID - Poor expected value"
        elif expected_value < 0:
            return "AVOID - Negative EV despite Kelly"
        elif kelly_pct < 0.02:
            return "CONSERVATIVE - Small edge, consider skipping"
        elif kelly_pct < 0.05:
            return "CAUTIOUS - Moderate edge"
        elif kelly_pct < 0.10:
            return "MODERATE - Good edge"
        else:
            return "AGGRESSIVE - Strong edge"


class BankrollManager:
    """Manages bankroll with Kelly-based position sizing."""

    def __init__(self, initial_bankroll: float = 1000.0):
        """
        Initialize bankroll manager.
        
        Args:
            initial_bankroll: Starting bankroll amount
        """
        self.initial_bankroll = initial_bankroll
        self.current_bankroll = initial_bankroll
        self.kelly_calculator = KellyCriterion(initial_bankroll)
        self.bet_history = []
        self.max_consecutive_losses = 0
        self.consecutive_losses = 0

    def place_bet(
        self,
        horse_name: str,
        race_id: str,
        win_probability: float,
        odds: float,
        bet_type: str = "win",
        kelly_fraction: float = 0.25
    ) -> Dict:
        """
        Place a bet with Kelly sizing.
        
        Args:
            horse_name: Name of the horse
            race_id: Race identifier
            win_probability: Probability of winning
            odds: Current odds
            bet_type: Type of bet (win, place, exacta, etc.)
            kelly_fraction: Fraction of Kelly to use
        
        Returns:
            Bet details
        """
        bet_sizing = self.kelly_calculator.calculate_bet_amount(
            win_probability,
            odds,
            kelly_fraction=kelly_fraction
        )
        
        bet_info = {
            'timestamp': datetime.now().isoformat(),
            'horse_name': horse_name,
            'race_id': race_id,
            'bet_type': bet_type,
            'odds': odds,
            'win_probability': win_probability,
            'bet_amount': bet_sizing['bet_amount'],
            'kelly_pct': bet_sizing['fractional_kelly_pct'],
            'expected_value': bet_sizing['expected_value'],
            'recommendation': bet_sizing['recommendation'],
            'status': 'pending'
        }
        
        self.bet_history.append(bet_info)
        return bet_info

    def resolve_bet(
        self,
        bet_index: int,
        result: str,
        actual_payout: Optional[float] = None
    ) -> Dict:
        """
        Resolve a placed bet.
        
        Args:
            bet_index: Index of bet in history
            result: 'win', 'loss', 'void'
            actual_payout: Actual payout if different from odds
        
        Returns:
            Updated bankroll info
        """
        if bet_index >= len(self.bet_history):
            return {'error': 'Bet not found'}
        
        bet = self.bet_history[bet_index]
        bet['status'] = result
        bet['resolution_time'] = datetime.now().isoformat()
        
        if result == 'win':
            payout = actual_payout or (bet['bet_amount'] * bet['odds'])
            profit = payout - bet['bet_amount']
            self.current_bankroll += profit
            self.consecutive_losses = 0
        elif result == 'loss':
            self.current_bankroll -= bet['bet_amount']
            self.consecutive_losses += 1
            self.max_consecutive_losses = max(
                self.max_consecutive_losses,
                self.consecutive_losses
            )
        
        self.kelly_calculator.bankroll = self.current_bankroll
        
        return {
            'current_bankroll': round(self.current_bankroll, 2),
            'bankroll_change': round(
                self.current_bankroll - self.initial_bankroll, 2
            ),
            'roi': round(
                ((self.current_bankroll - self.initial_bankroll) 
                 / self.initial_bankroll * 100), 1
            ),
            'total_bets': len(self.bet_history),
            'wins': sum(1 for b in self.bet_history if b.get('status') == 'win'),
            'consecutive_losses': self.consecutive_losses,
            'max_consecutive_losses': self.max_consecutive_losses
        }

    def get_bankroll_stats(self) -> Dict:
        """Get comprehensive bankroll statistics."""
        wins = sum(1 for b in self.bet_history if b.get('status') == 'win')
        losses = sum(1 for b in self.bet_history if b.get('status') == 'loss')
        voids = sum(1 for b in self.bet_history if b.get('status') == 'void')
        total_bets = len(self.bet_history)
        
        if total_bets == 0:
            return {
                'total_bets': 0,
                'current_bankroll': self.current_bankroll,
                'message': 'No bets placed yet'
            }
        
        win_rate = (wins / total_bets * 100) if total_bets > 0 else 0
        
        total_staked = sum(b['bet_amount'] for b in self.bet_history if b.get('status'))
        avg_odds = (
            np.mean([b['odds'] for b in self.bet_history if b.get('odds')])
            if self.bet_history else 0
        )
        
        return {
            'current_bankroll': round(self.current_bankroll, 2),
            'initial_bankroll': self.initial_bankroll,
            'profit_loss': round(self.current_bankroll - self.initial_bankroll, 2),
            'roi_percent': round(
                ((self.current_bankroll - self.initial_bankroll) 
                 / self.initial_bankroll * 100), 1
            ),
            'total_bets': total_bets,
            'wins': wins,
            'losses': losses,
            'voids': voids,
            'win_rate_percent': round(win_rate, 1),
            'total_staked': round(total_staked, 2),
            'avg_odds': round(avg_odds, 2),
            'consecutive_losses': self.consecutive_losses,
            'max_consecutive_losses': self.max_consecutive_losses
        }


class AdaptiveKellyManager:
    """
    Adaptive Kelly manager that adjusts Kelly fraction based on performance.
    
    Features:
    - Reduces Kelly fraction during losing streaks
    - Increases Kelly fraction during winning streaks
    - Prevents ruin through bankroll protection
    """

    def __init__(self, initial_bankroll: float = 1000.0, base_kelly_fraction: float = 0.25):
        """
        Initialize adaptive Kelly manager.
        
        Args:
            initial_bankroll: Starting bankroll
            base_kelly_fraction: Base Kelly fraction (0.25, 0.5, 0.75)
        """
        self.manager = BankrollManager(initial_bankroll)
        self.base_kelly_fraction = base_kelly_fraction
        self.kelly_multiplier = 1.0
        self.recent_performance = []
        self.performance_window = 10

    def get_adaptive_kelly_fraction(self) -> Tuple[float, str]:
        """
        Calculate adaptive Kelly fraction based on recent performance.
        
        Returns:
            Tuple of (kelly_fraction, adjustment_reason)
        """
        stats = self.manager.get_bankroll_stats()
        
        if stats.get('total_bets', 0) < 5:
            return self.base_kelly_fraction, "Insufficient data"
        
        recent_bets = self.manager.bet_history[-self.performance_window:]
        recent_wins = sum(1 for b in recent_bets if b.get('status') == 'win')
        recent_losses = sum(1 for b in recent_bets if b.get('status') == 'loss')
        recent_win_rate = recent_wins / len(recent_bets) if recent_bets else 0
        
        if stats['consecutive_losses'] >= 3:
            self.kelly_multiplier = 0.5
            reason = f"3+ losses: Using {self.kelly_multiplier}x Kelly"
        elif stats['consecutive_losses'] >= 2:
            self.kelly_multiplier = 0.75
            reason = f"2 losses: Using {self.kelly_multiplier}x Kelly"
        elif recent_win_rate >= 0.6:
            self.kelly_multiplier = 1.25
            reason = f"Hot streak: Using {self.kelly_multiplier}x Kelly"
        elif recent_win_rate >= 0.5:
            self.kelly_multiplier = 1.0
            reason = "Normal: Using 1.0x Kelly"
        else:
            self.kelly_multiplier = 0.75
            reason = f"Cold streak: Using {self.kelly_multiplier}x Kelly"
        
        adjusted_fraction = self.base_kelly_fraction * self.kelly_multiplier
        adjusted_fraction = max(0.05, min(0.25, adjusted_fraction))
        
        return adjusted_fraction, reason

    def place_adaptive_bet(
        self,
        horse_name: str,
        race_id: str,
        win_probability: float,
        odds: float,
        bet_type: str = "win"
    ) -> Dict:
        """
        Place bet with adaptive Kelly sizing.
        
        Args:
            horse_name: Horse name
            race_id: Race ID
            win_probability: Win probability
            odds: Odds
            bet_type: Bet type
        
        Returns:
            Bet info with adaptive Kelly applied
        """
        kelly_fraction, adjustment_reason = self.get_adaptive_kelly_fraction()
        
        bet_info = self.manager.place_bet(
            horse_name,
            race_id,
            win_probability,
            odds,
            bet_type,
            kelly_fraction
        )
        
        bet_info['adaptive_kelly_fraction'] = kelly_fraction
        bet_info['kelly_adjustment'] = adjustment_reason
        
        return bet_info


class RaceOptimizer:
    """Optimize betting portfolio across multiple races using Kelly."""

    @staticmethod
    def optimize_race_portfolio(
        races: List[Dict],
        total_bankroll: float,
        kelly_fraction: float = 0.25
    ) -> List[Dict]:
        """
        Optimize bet sizing across multiple races.
        
        Args:
            races: List of race predictions with odds
            total_bankroll: Total bankroll to allocate
            kelly_fraction: Kelly fraction to use
        
        Returns:
            Optimized betting portfolio
        """
        kelly_calc = KellyCriterion(total_bankroll)
        portfolio = []
        total_allocated = 0
        expected_portfolio_value = 0
        
        for race in races:
            for horse in race.get('predictions', []):
                kelly_bet = kelly_calc.calculate_bet_amount(
                    horse['win_probability'] / 100,
                    horse['current_odds'],
                    kelly_fraction=kelly_fraction
                )
                
                if kelly_bet['bet_amount'] > 0:
                    portfolio.append({
                        'race_id': race['race_info']['number'],
                        'horse_name': horse['horse_name'],
                        'odds': horse['current_odds'],
                        'win_probability': horse['win_probability'],
                        'bet_amount': kelly_bet['bet_amount'],
                        'kelly_pct': kelly_bet['fractional_kelly_pct'],
                        'expected_value': kelly_bet['expected_value'],
                        'recommendation': kelly_bet['recommendation']
                    })
                    
                    total_allocated += kelly_bet['bet_amount']
                    expected_portfolio_value += kelly_bet['expected_value']
        
        portfolio.sort(
            key=lambda x: x['expected_value'],
            reverse=True
        )
        
        return {
            'portfolio': portfolio,
            'total_allocated': round(total_allocated, 2),
            'bankroll_utilization_pct': round(
                (total_allocated / total_bankroll * 100), 1
            ),
            'expected_portfolio_value': round(expected_portfolio_value, 2),
            'portfolio_count': len(portfolio)
        }
