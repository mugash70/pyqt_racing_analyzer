#!/usr/bin/env python3
"""
Enhanced HKJC Race Prediction Engine Demo

This script demonstrates the improved prediction capabilities including:
- Top-3 predictions with detailed explanations
- Enhanced feature engineering from all 29 database tables
- Fixture and future race card integration
- Multi-race analysis (races 1-11)
- Detailed prediction reasoning
"""

import sys
import os
import json
import sqlite3
from datetime import datetime
import numpy as np

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from prediction.enhanced_predictor import EnhancedRacePredictor, MultiRaceAnalyzer


def print_separator(char="=", length=70):
    print(char * length)


def demo_single_race_prediction(predictor: EnhancedRacePredictor, race_date: str, race_num: int, track: str):
    """Demonstrate single race prediction with detailed explanation."""
    print_separator()
    print(f"SINGLE RACE PREDICTION DEMO")
    print(f"Race {race_num} at {track} on {race_date}")
    print_separator()
    
    result = predictor.predict_race(race_date, race_num, track)
    
    if not result.get('success'):
        print(f"Error: {result.get('error', 'Unknown error')}")
        return
    
    race_info = result['race_info']
    print(f"\nRace Info:")
    print(f"  Distance: {race_info.get('distance')}")
    print(f"  Class: {race_info.get('class')}")
    print(f"  Going: {race_info.get('going')}")
    print(f"  Field Size: {result['field_size']} runners")
    
    if race_info.get('fixture_info'):
        fixture = race_info['fixture_info']
        print(f"  Fixture: {fixture.get('day_night', 'Unknown')} meeting, {fixture.get('track_type', 'Unknown')} track")
    
    print(f"\nMarket Overround: {result.get('market_overround', 0):.1f}%")
    
    # Top 3
    print_separator("-", 50)
    print("TOP 3 PREDICTIONS:")
    print_separator("-", 50)
    
    for horse in result['top_3']:
        print(f"\n{horse['rank']}. #{horse['horse_number']} {horse['horse_name']}")
        print(f"   Win Probability: {horse['win_probability_pct']:.1f}%")
        print(f"   Place Probability: {horse['place_probability_pct']:.1f}%")
        print(f"   Confidence: {horse['confidence']*100:.0f}%")
        print(f"   Current Odds: {horse['current_odds']:.1f}")
        print(f"   Expected Value: {horse['expected_value']:.2f}")
        print(f"   Risk: {horse['risk_assessment']}")
        
        if horse.get('why_predicted'):
            print(f"   Why: {horse['why_predicted']}")
        
        if horse.get('key_factors'):
            print(f"   Key Factors:")
            for factor in horse['key_factors'][:2]:
                print(f"      • {factor['factor']}: {factor['value']}")
    
    # Value bets
    if result.get('value_bets'):
        print_separator("-", 50)
        print("VALUE BETTING OPPORTUNITIES:")
        print_separator("-", 50)
        
        for vb in result['value_bets'][:3]:
            print(f"\n  #{vb['horse_number']} {vb['horse_name']}")
            print(f"     Odds: {vb['current_odds']:.1f}")
            print(f"     Model Prob: {vb['model_probability']*100:.1f}%")
            print(f"     Implied Prob: {vb['implied_probability']*100:.1f}%")
            print(f"     Edge: +{vb['edge_pct']:.1f}%")
            print(f"     Expected Value: {vb['expected_value']:.2f}")
    
    # Full analysis
    print_separator()
    print("DETAILED ANALYSIS:")
    print_separator()
    print(result['analysis'])
    print()


def demo_multi_race_prediction(predictor: EnhancedRacePredictor, race_date: str, track: str):
    """Demonstrate multi-race prediction for a full meeting."""
    print_separator()
    print(f"FULL CARD PREDICTION DEMO")
    print(f"All races at {track} on {race_date}")
    print_separator()
    
    # Get full fixture analysis
    full_analysis = predictor.predict_with_fixture_analysis(race_date, track)
    
    print(f"\nNumber of races analyzed: {len(full_analysis['race_predictions'])}")
    
    # Fixture info
    if full_analysis.get('fixture'):
        fixture = full_analysis['fixture']
        print(f"\nFixture Information:")
        print(f"  Day/Night: {fixture.get('day_night', 'Unknown')}")
        print(f"  Track Type: {fixture.get('track_type', 'Unknown')}")
        print(f"  Expected Races: {fixture.get('expected_races', 'Unknown')}")
        if fixture.get('is_cup'):
            print(f"  *** CUP MEETING ***")
    
    # Track bias
    bias = full_analysis.get('track_bias_analysis', {})
    print(f"\nTrack Bias Analysis:")
    print(f"  Strength: {bias.get('bias_strength', 'Unknown')}")
    if bias.get('best_draws'):
        print(f"  Best Draws: {', '.join(map(str, bias['best_draws']))}")
    if bias.get('worst_draws'):
        print(f"  Worst Draws: {', '.join(map(str, bias['worst_draws']))}")
    
    # Best bets across the card
    if full_analysis.get('best_bets'):
        print_separator("-", 50)
        print("BEST BETS OF THE DAY:")
        print_separator("-", 50)
        
        for i, bet in enumerate(full_analysis['best_bets'][:5], 1):
            print(f"\n{i}. Race {bet['race_number']} - #{bet['horse_number']} {bet['horse_name']}")
            print(f"   Odds: {bet['current_odds']:.1f}")
            print(f"   Model Probability: {bet['model_probability']*100:.1f}%")
            print(f"   Edge: +{bet['edge_pct']:.1f}%")
            print(f"   EV: {bet['expected_value']:.2f}")
    
    # Races to avoid
    if full_analysis.get('races_to_avoid'):
        print_separator("-", 50)
        print("RACES TO APPROACH WITH CAUTION:")
        print_separator("-", 50)
        
        for race in full_analysis['races_to_avoid']:
            print(f"  Race {race['race_number']}: {race['reason']}")
    
    # Race summaries
    print_separator()
    print("RACE SUMMARIES:")
    print_separator()
    
    for race in full_analysis['race_predictions']:
        race_info = race['race_info']
        top_3 = race.get('top_3', [])
        
        if top_3:
            fav = top_3[0]
            print(f"\nRace {race_info['number']}: #{fav['horse_number']} {fav['horse_name']} ({fav['win_probability_pct']:.1f}%)")
            
            if len(top_3) > 1:
                second = top_3[1]
                print(f"  2nd: #{second['horse_number']} {second['horse_name']} ({second['win_probability_pct']:.1f}%)")
            if len(top_3) > 2:
                third = top_3[2]
                print(f"  3rd: #{third['horse_number']} {third['horse_name']} ({third['win_probability_pct']:.1f}%)")
    
    print()


def demo_jockey_trainer_analysis(predictor: EnhancedRacePredictor, race_date: str, track: str):
    """Demonstrate jockey and trainer day analysis."""
    analyzer = MultiRaceAnalyzer(predictor)
    
    print_separator()
    print(f"JOCKEY & TRAINER DAY ANALYSIS")
    print(f"{track} on {race_date}")
    print_separator()
    
    # Jockey analysis
    jockey_analysis = analyzer.analyze_jockey_day_performance(race_date, track)
    
    if jockey_analysis.get('jockey_analysis'):
        print("\nTOP JOCKEYS BY TOTAL WIN PROBABILITY:")
        print("-" * 50)
        
        for jockey in jockey_analysis['jockey_analysis'][:5]:
            print(f"\n  {jockey['jockey']}")
            print(f"     Total Rides: {jockey['total_rides']}")
            print(f"     Total Win Probability: {jockey['total_win_probability']*100:.1f}%")
            print(f"     Avg Win Chance per Ride: {jockey['avg_win_chance']*100:.1f}%")
            
            if jockey.get('best_chance'):
                best = jockey['best_chance']
                print(f"     Best Chance: Race {best['race_number']} - {best['horse_name']} ({best['win_probability']*100:.1f}%)")
    
    # Trainer analysis
    trainer_analysis = analyzer.identify_trainer_patterns(race_date, track)
    
    if trainer_analysis.get('trainer_patterns'):
        print("\n\nTRAINERS WITH MULTIPLE STRONG CHANCES:")
        print("-" * 50)
        
        for trainer in trainer_analysis['trainer_patterns'][:5]:
            print(f"\n  {trainer['trainer']}")
            print(f"     Total Runners: {trainer['total_runners']}")
            print(f"     Races: {', '.join(map(str, trainer['races']))}")
            print(f"     Total Win Probability: {trainer['total_win_probability']*100:.1f}%")
            print(f"     Avg Win Probability: {trainer['avg_win_probability']*100:.1f}%")
            
            if trainer.get('track_specialists'):
                print(f"     Track Specialists: {len(trainer['track_specialists'])}")
    
    print()


def save_prediction_json(result: dict, filename: str):
    """Save prediction result to JSON file."""
    # Convert numpy types to Python native types for JSON serialization
    def convert_to_native(obj):
        if isinstance(obj, dict):
            return {k: convert_to_native(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_to_native(i) for i in obj]
        elif isinstance(obj, (np.integer, np.floating)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return obj
    
    with open(filename, 'w') as f:
        json.dump(convert_to_native(result), f, indent=2, default=str)
    
    print(f"Prediction saved to: {filename}")


def main():
    """Main demo function."""
    # Database path
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'hkjc_races.db')
    
    if not os.path.exists(db_path):
        print(f"Error: Database not found at {db_path}")
        print("Please ensure the database file exists.")
        return
    
    print_separator()
    print("ENHANCED HKJC RACE PREDICTION ENGINE")
    print("Advanced Features:")
    print("  ✓ 100+ features from 29 database tables")
    print("  ✓ Top-3 predictions with detailed explanations")
    print("  ✓ Multi-model ensemble with 5 components")
    print("  ✓ Fixture and future race card integration")
    print("  ✓ Value betting identification")
    print("  ✓ Jockey/trainer day analysis")
    print_separator()
    
    # Initialize predictor
    print("\nInitializing predictor...")
    predictor = EnhancedRacePredictor(db_path)
    print("Predictor ready!\n")
    
    # Example usage - you can modify these values
    # For demo purposes, we'll use placeholder dates
    # In practice, use actual race dates from your database
    
    # Try to get a valid date from the database
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT race_date FROM future_race_cards LIMIT 1")
        result = cursor.fetchone()
        conn.close()
        
        if result:
            race_date = result[0].split()[0] if ' ' in result[0] else result[0]
        else:
            race_date = "2025-01-01"  # Fallback
    except:
        race_date = "2025-01-01"  # Fallback
    
    track = "ST"  # Sha Tin (or use "HV" for Happy Valley)
    
    print(f"Using race date: {race_date}")
    print(f"Track: {track}")
    print()
    
    # Demo 1: Single race prediction with detailed explanation
    try:
        demo_single_race_prediction(predictor, race_date, 1, track)
    except Exception as e:
        print(f"Single race demo error: {e}")
    
    # Demo 2: Multi-race prediction
    try:
        demo_multi_race_prediction(predictor, race_date, track)
    except Exception as e:
        print(f"Multi-race demo error: {e}")
    
    # Demo 3: Jockey/Trainer analysis
    try:
        demo_jockey_trainer_analysis(predictor, race_date, track)
    except Exception as e:
        print(f"Jockey/trainer demo error: {e}")
    
    print_separator()
    print("Demo completed!")
    print_separator()
    
    # Example of saving to JSON
    # result = predictor.predict_race(race_date, 1, track)
    # if result.get('success'):
    #     save_prediction_json(result, f"prediction_race_1_{race_date}.json")


if __name__ == "__main__":
    main()
