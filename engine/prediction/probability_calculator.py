"""Probability calculation engine."""

from typing import Dict, List
import numpy as np


class ProbabilityCalculator:
    """Calculates win and place probabilities."""
    
    @staticmethod
    def calculate_win_probability(base_odds: float, form_factor: float, 
                                 track_factor: float) -> float:
        """
        Calculate win probability from multiple factors.
        
        Args:
            base_odds: Current betting odds
            form_factor: Recent form score (0-1)
            track_factor: Track suitability (0-1)
            
        Returns:
            Win probability (0-1)
        """
        implied_prob = 1.0 / base_odds if base_odds > 0 else 0.2
        
        probability = (implied_prob * 0.4 + form_factor * 0.35 + track_factor * 0.25)
        
        return float(max(0.0, min(1.0, probability)))
    
    @staticmethod
    def calculate_place_probability(win_prob: float, place_odds: float) -> float:
        """
        Calculate place (top 3) probability.
        
        Args:
            win_prob: Win probability
            place_odds: Place odds
            
        Returns:
            Place probability (0-1)
        """
        implied_place = 1.0 / place_odds if place_odds > 0 else 0.5
        
        place_prob = (win_prob * 0.6 + implied_place * 0.4)
        
        return float(max(0.0, min(1.0, place_prob)))
    
    @staticmethod
    def normalize_probabilities(probabilities: List[float]) -> List[float]:
        """
        Normalize probabilities to sum to 1.0 across all horses.
        
        Args:
            probabilities: List of raw probabilities
            
        Returns:
            Normalized probabilities
        """
        total = sum(probabilities)
        
        if total == 0:
            return [1.0 / len(probabilities) for _ in probabilities]
        
        return [p / total for p in probabilities]
    
    @staticmethod
    def calculate_confidence(prediction_variance: float) -> float:
        """
        Calculate prediction confidence from variance.
        
        Args:
            prediction_variance: Variance in predictions (0-1)
            
        Returns:
            Confidence score (0-1)
        """
        confidence = 1.0 - (prediction_variance * 0.5)
        
        return float(max(0.5, min(0.95, confidence)))
    
    @staticmethod
    def calculate_expected_value(probability: float, odds: float) -> float:
        """
        Calculate expected value of a bet.
        
        Args:
            probability: Estimated win probability (0-1)
            odds: Decimal odds
            
        Returns:
            Expected value
        """
        if odds <= 0:
            return 0.0
        
        ev = (probability * odds) - (1 - probability)
        
        return float(ev)
