import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.prediction.race_predictor import RacePredictor
from engine.output.report_generator import ReportGenerator

def validate_predictions(race_data):
    """Validate mathematical consistency of predictions"""
    predictions = race_data.get('predictions', [])
    
    print("\n=== VALIDATION RESULTS ===")
    
    # 1. Probability sum check
    total_win_prob = sum(p['win_probability'] for p in predictions)
    print(f"Win probability sum: {total_win_prob:.1f}% (should be 100%)")
    if abs(total_win_prob - 100) > 1:
        print("❌ ISSUE: Probabilities don't sum to 100%")
    
    # 2. Odds consistency check
    print("\n=== ODDS CONSISTENCY ===")
    for p in predictions:
        odds = p.get('current_odds', 0)
        model_prob = p['win_probability']
        if odds > 0:
            implied_prob = (1 / odds) * 100
            diff = abs(implied_prob - model_prob)
            if diff > 50:
                print(f"❌ {p['horse_name']}: Model={model_prob:.1f}%, Odds={odds} implies {implied_prob:.1f}%")
    
    # 3. Value calculation check
    print("\n=== VALUE CALCULATION ===")
    for p in predictions:
        odds = p.get('current_odds', 0)
        model_prob = p['win_probability'] / 100  # Convert to 0-1
        reported_value = p.get('value_pct', 0)
        if odds > 0:
            implied_prob = 1 / odds
            correct_value = ((implied_prob - model_prob) / model_prob) * 100
            if abs(correct_value - reported_value) > 20:
                print(f"❌ {p['horse_name']}: Expected={correct_value:.0f}%, Reported={reported_value:.0f}%")

def verify():
    # Database path fix
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "database", "hkjc_races.db")
    if not os.path.exists(db_path):
        print(f"Error: Database {db_path} not found.")
        return

    predictor = RacePredictor(db_path)
    # race_date = "2026-01-11"
    race_date = "2026-01-31"  # Has race card data

    track = "ST"
    
    print(f"Running predictions for {race_date} at {track}...")
    
    # Predict a single race first to see the analysis
    race_1_pred = predictor.predict_race(race_date, 1, track)
    
    if 'error' in race_1_pred:
        print(f"Error predicting race 1: {race_1_pred['error']}")
    else:
        # Validate predictions first
        validate_predictions(race_1_pred)
        
        print("\n" + "="*50)
        print("RACE 1 PREDICTION & ANALYSIS")
        print("="*50)
        report = ReportGenerator.generate_race_report(race_1_pred)
        print(report)
        
    # Now predict multiple races to verify full coverage
    print("\n" + "="*50)
    print("FULL CARD PREDICTION (Races 1-11)")
    print("="*50)
    all_preds = predictor.predict_multiple_races(race_date, track)
    print(f"Successfully predicted {len(all_preds)} races.")
    
    for i, pred in enumerate(all_preds):
        print(f"Race {pred['race_info']['number']}: {len(pred['predictions'])} horses predicted.")

if __name__ == "__main__":
    verify()