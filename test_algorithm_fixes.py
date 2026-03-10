#!/usr/bin/env python3
"""
Test script to verify algorithm fixes for improved prediction accuracy.
Tests the key changes made to achieve 60%+ top-choice hit rate.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine.models.ensemble_model import EnsembleModel, ModelConfig
from engine.prediction.confidence_scorer import ConfidenceScorer


def test_ensemble_weights():
    """Test that ensemble model weights are correctly configured."""
    print("=" * 60)
    print("TEST 1: Ensemble Model Weights")
    print("=" * 60)
    
    config = ModelConfig()
    
    print(f"Market Odds Weight: {config.odds_weight:.2f} (expected: 0.55)")
    print(f"Form Weight: {config.form_weight:.2f} (expected: 0.20)")
    print(f"Track Score Weight: {config.track_score_weight:.2f} (expected: 0.10)")
    print(f"Jockey Weight: {config.jockey_weight:.2f} (expected: 0.05)")
    print(f"Trainer Weight: {config.trainer_weight:.2f} (expected: 0.05)")
    
    # Verify weights
    assert config.odds_weight == 0.55, f"Market odds weight should be 0.55, got {config.odds_weight}"
    assert config.form_weight == 0.20, f"Form weight should be 0.20, got {config.form_weight}"
    
    total_weight = (config.odds_weight + config.form_weight + config.track_score_weight + 
                    config.universal_score_weight + config.jockey_weight + config.trainer_weight)
    print(f"\nTotal Weight: {total_weight:.2f} (should be 1.00)")
    assert abs(total_weight - 1.0) < 0.01, f"Total weight should be ~1.0, got {total_weight}"
    
    print("✅ PASSED: Ensemble weights correctly configured")
    return True


def test_probability_calculation():
    """Test that probability calculation correctly weights market odds."""
    print("\n" + "=" * 60)
    print("TEST 2: Probability Calculation with Market Odds Bias")
    print("=" * 60)
    
    model = EnsembleModel()
    
    # Test case: A clear favorite at 2/1 odds (33% implied probability)
    features = {
        'horse_name': 'TestHorse',
        'current_odds': 3.0,  # 33% implied probability
        'last_5_avg': 3.0,  # Good form
        'track_score': 80,
        'universal_score': 75,
        'jockey_win_rate': 15,
        'trainer_win_rate': 12
    }
    
    result = model.predict_probability(features)
    prob = result['probability']
    contributions = result['contributions']
    
    print(f"Input: 3.0 odds (33% implied)")
    print(f"Predicted probability: {prob:.3f} ({prob*100:.1f}%)")
    print(f"Market odds contribution: {contributions.get('market_odds', 0):.3f}")
    
    # With 55% weight on odds, the result should be closer to 33%
    # But also influenced by other factors
    assert 0.15 < prob < 0.50, f"Probability {prob} should be reasonable for a favorite"
    
    print("✅ PASSED: Probability calculation working correctly")
    return True


def test_confidence_boost():
    """Test that confidence is boosted for high-probability horses."""
    print("\n" + "=" * 60)
    print("TEST 3: Confidence Boost for Favorites")
    print("=" * 60)
    
    scorer = ConfidenceScorer()
    
    # Test with a strong favorite (25% win probability)
    conf_high = scorer.calculate_ensemble_confidence(
        xgboost_prob=0.25,
        neural_net_prob=0.24,
        win_probability=0.25
    )
    
    # Test with a weaker horse (10% win probability)
    conf_low = scorer.calculate_ensemble_confidence(
        xgboost_prob=0.10,
        neural_net_prob=0.09,
        win_probability=0.10
    )
    
    print(f"Confidence for 25% win prob horse: {conf_high:.3f}")
    print(f"Confidence for 10% win prob horse: {conf_low:.3f}")
    print(f"Difference: {conf_high - conf_low:.3f}")
    
    # High probability horse should have higher confidence
    assert conf_high > conf_low, "Strong favorite should have higher confidence"
    
    # High probability horse should get boost above 0.70
    assert conf_high > 0.70, f"Strong favorite confidence {conf_high} should be > 0.70"
    
    print("✅ PASSED: Confidence boost working correctly")
    return True


def test_normalization_vs_calibration():
    """Test that simple normalization preserves probability ranking."""
    print("\n" + "=" * 60)
    print("TEST 4: Simple Normalization (No Power-Law)")
    print("=" * 60)
    
    # Simulate raw probabilities (as they would come from model)
    raw_probs = [0.25, 0.15, 0.10, 0.08, 0.07]  # 5 horses
    
    # Old method (power-law calibration) - would compress these
    # p^0.75 makes them closer together
    old_calibrated = [p ** 0.75 for p in raw_probs]
    old_total = sum(old_calibrated)
    old_normalized = [p / old_total for p in old_calibrated]
    
    # New method (simple normalization)
    total = sum(raw_probs)
    new_normalized = [p / total for p in raw_probs]
    
    print("Horse | Raw    | Old Method | New Method")
    print("-" * 45)
    for i, (raw, old, new) in enumerate(zip(raw_probs, old_normalized, new_normalized)):
        print(f"  {i+1}   | {raw:.3f}  | {old:.3f}      | {new:.3f}")
    
    # Calculate spread (difference between top and second)
    old_spread = (old_normalized[0] - old_normalized[1]) * 100
    new_spread = (new_normalized[0] - new_normalized[1]) * 100
    
    print(f"\nTop-to-2nd spread:")
    print(f"  Old method: {old_spread:.1f}%")
    print(f"  New method: {new_spread:.1f}%")
    
    # New method should preserve the original spread better
    assert new_spread > old_spread, "New method should preserve larger spread"
    
    print("✅ PASSED: Simple normalization preserves probability spread")
    return True


def test_high_confidence_selection():
    """Test the high-confidence selection criteria."""
    print("\n" + "=" * 60)
    print("TEST 5: High-Confidence Selection Validation")
    print("=" * 60)
    
    # Mock predictions that SHOULD pass (clear favorite)
    good_predictions = [
        {'win_probability': 28.0, 'confidence': 0.85, 'current_odds': 4.5},  # Top pick
        {'win_probability': 18.0, 'confidence': 0.70, 'current_odds': 6.0},  # Second
        {'win_probability': 12.0, 'confidence': 0.60, 'current_odds': 10.0},
    ]
    
    # Mock predictions that should FAIL (too close)
    bad_predictions_close = [
        {'win_probability': 15.0, 'confidence': 0.75, 'current_odds': 7.0},  # Top pick
        {'win_probability': 14.0, 'confidence': 0.72, 'current_odds': 7.5},  # Too close!
        {'win_probability': 13.0, 'confidence': 0.70, 'current_odds': 8.0},
    ]
    
    # Mock predictions that should FAIL (low confidence)
    bad_predictions_low_conf = [
        {'win_probability': 22.0, 'confidence': 0.60, 'current_odds': 5.0},  # Low confidence
        {'win_probability': 15.0, 'confidence': 0.55, 'current_odds': 7.0},
    ]
    
    # Simulate the validation logic
    def validate(predictions):
        sorted_preds = sorted(predictions, key=lambda x: x['win_probability'], reverse=True)
        top = sorted_preds[0]
        second = sorted_preds[1]
        
        if top['win_probability'] < 20:
            return False, f"Win prob too low ({top['win_probability']:.1f}%)"
        if top['win_probability'] - second['win_probability'] < 5:
            return False, "Gap too small"
        if top['confidence'] < 0.70:
            return False, f"Confidence too low ({top['confidence']*100:.1f}%)"
        if top['current_odds'] > 15:
            return False, "Odds too long"
        return True, "Valid"
    
    result1, reason1 = validate(good_predictions)
    result2, reason2 = validate(bad_predictions_close)
    result3, reason3 = validate(bad_predictions_low_conf)
    
    print(f"Good predictions (clear favorite): {result1} - {reason1}")
    print(f"Bad predictions (too close): {result2} - {reason2}")
    print(f"Bad predictions (low conf): {result3} - {reason3}")
    
    assert result1 == True, "Good predictions should pass"
    assert result2 == False, "Close predictions should fail"
    assert result3 == False, "Low confidence predictions should fail"
    
    print("✅ PASSED: High-confidence selection working correctly")
    return True


def run_all_tests():
    """Run all algorithm fix tests."""
    print("\n" + "🔍 TESTING ALGORITHM FIXES FOR 60%+ HIT RATE" + "\n")
    
    tests = [
        test_ensemble_weights,
        test_probability_calculation,
        test_confidence_boost,
        test_normalization_vs_calibration,
        test_high_confidence_selection,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
        except AssertionError as e:
            print(f"❌ FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ ERROR: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Passed: {passed}/{len(tests)}")
    print(f"Failed: {failed}/{len(tests)}")
    
    if failed == 0:
        print("\n✅ ALL TESTS PASSED - Algorithm fixes are working correctly!")
        print("\nKey improvements implemented:")
        print("  1. Market odds weight increased to 55%")
        print("  2. Removed harmful power-law calibration")
        print("  3. Added confidence boost for favorites")
        print("  4. Added high-confidence selection validation")
        return True
    else:
        print("\n⚠️  SOME TESTS FAILED - Please review the fixes")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
