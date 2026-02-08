
import sqlite3
import os
import sys
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from engine.prediction.enhanced_predictor import EnhancedRacePredictor
from engine.verification.accuracy_tracker import AccuracyTracker

def populate():
    db_path = os.path.join(os.path.dirname(__file__), 'database', 'hkjc_races.db')
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return

    predictor = EnhancedRacePredictor(db_path)
    tracker = AccuracyTracker(db_path)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get some recent races with results
    cursor.execute("""
        SELECT DISTINCT race_date, race_number, racecourse 
        FROM race_results 
        WHERE race_date < DATE('now')
        ORDER BY race_date DESC 
        LIMIT 5
    """)
    
    races = cursor.fetchall()
    
    for race_date, race_number, racecourse in races:
        print(f"Generating predictions for {race_date} Race {race_number} at {racecourse}...")
        try:
            # Generate predictions
            # We need to catch error per horse to see which one fails
            results = predictor.predict_race(race_date, race_number, racecourse)
            
            if 'error' in results:
                print(f"  Error: {results['error']}")
                continue
            
            predictions = results.get('predictions', [])
            
            # Log predictions
            for pred in predictions:
                tracker.log_prediction({
                    'race_date': race_date,
                    'race_number': race_number,
                    'racecourse': racecourse,
                    'horse_name': pred.get('horse_name'),
                    'horse_number': pred.get('horse_number'),
                    'predicted_rank': pred.get('predicted_rank'),
                    'win_probability': pred.get('win_probability', 0),
                    'place_probability': pred.get('place_probability', 0),
                    'confidence': pred.get('confidence', 0),
                    'current_odds': pred.get('current_odds'),
                    'value_pct': pred.get('value_pct')
                })
            
            # Validate them immediately
            tracker.validate_predictions(race_date, race_number, racecourse)
            print(f"  Successfully predicted and validated {len(predictions)} horses.")
            
        except Exception as e:
            print(f"  Failed at race level: {e}")
            import traceback
            traceback.print_exc()

    conn.close()
    print("Done populating predictions.")

if __name__ == "__main__":
    populate()
