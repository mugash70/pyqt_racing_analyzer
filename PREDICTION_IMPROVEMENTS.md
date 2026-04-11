ict the # Prediction Accuracy Improvements

## Summary

This document outlines the improvements made to increase prediction accuracy by better utilizing unused database tables and enhancing feature engineering.

## Changes Made

### 1. DataIntegrator Enhancements (`engine/core/data_integrator.py`)

Added new methods to query previously unused tables:

- **`get_jockey_ranking(jockey_name)`** - Retrieves jockey ranking data from `jockey_rankings` table
- **`get_trainer_ranking(trainer_name)`** - Retrieves trainer ranking data from `trainer_rankings` table
- **`get_barrier_trial_data(horse_name, limit)`** - Gets barrier trial data from `barrier_tests` table
- **`get_track_selection_data(race_date, racecourse)`** - Retrieves track conditions from `track_selection_data`
- **`get_jockey_track_performance(jockey_name, track)`** - Track-specific jockey statistics
- **`get_trainer_track_performance(trainer_name, track)`** - Track-specific trainer statistics
- **`get_jockey_distance_performance(jockey_name, distance)`** - Distance-specific jockey statistics
- **`get_trainer_distance_performance(trainer_name, distance)`** - Distance-specific trainer statistics

### 2. Enhanced Feature Engineering (`engine/features/enhanced_features.py`)

Updated feature extraction to leverage new data sources:

#### Jockey Features
- Track-specific win rate and ride count
- Distance-specific win rate and ride count
- Jockey ranking (rank, win rate, place rate)
- Track specialist flag (20+ rides with >5% above average win rate)
- Distance specialist flag (10+ rides with >5% above average win rate)

#### Trainer Features
- Track-specific win rate and runner count
- Distance-specific win rate and runner count
- Trainer ranking (rank, win rate, place rate)
- Track specialist flag
- Distance specialist flag

#### New Feature Flags
- `jockey_is_track_specialist` - Binary flag for jockey track expertise
- `jockey_is_distance_specialist` - Binary flag for jockey distance expertise
- `trainer_is_track_specialist` - Binary flag for trainer track expertise
- `trainer_is_distance_specialist` - Binary flag for trainer distance expertise

### 3. Ensemble Model Improvements (`engine/models/ensemble_model.py`)

#### Updated Weights
```python
odds_weight: 0.45        # Reduced from 0.55 (less market dominance)
form_weight: 0.20        # Unchanged
jockey_weight: 0.08      # INCREASED from 0.05
trainer_weight: 0.07     # INCREASED from 0.05
jockey_trainer_synergy_weight: 0.05  # NEW - for jockey-trainer combo bonus
```

#### New Prediction Logic
- Track specialization bonus (15% for jockey, 10% for trainer)
- Jockey-trainer synergy factor when synergy score > 50
- Uses enhanced jockey_score/trainer_score instead of just win_rate
- Falls back to win_rate if score not available

## Impact on Prediction Accuracy

### Before
- Only basic jockey/trainer win rates from race_results
- No track/distance specialization knowledge
- Heavy reliance on market odds (55% weight)
- Limited human factor consideration (10% combined)

### After
- Full jockey/trainer rankings from dedicated tables
- Track-specific and distance-specific performance metrics
- Specialist detection for both jockeys and trainers
- Better balanced weight distribution
- Jockey-trainer synergy bonus

## Tables Now Utilized

| Table | Previous Use | Current Use |
|-------|-------------|-------------|
| jockey_rankings | ❌ Unused | ✅ Full ranking data |
| trainer_rankings | ❌ Unused | ✅ Full ranking data |
| barrier_tests | ❌ Unused | ✅ Trial data available |
| track_selection_data | ❌ Unused | ✅ Track conditions |

## Key Features Added

1. **Track Specialization Detection**
   - Identifies jockeys/trainers with proven track records
   - Applies performance bonuses in predictions

2. **Distance Specialization Detection**
   - Identifies specialists at specific distances
   - Particularly valuable for sprint vs middle vs staying races

3. **Official Rankings Integration**
   - Uses official HKJC jockey/trainer rankings
   - Adds credibility to human factor assessment

4. **Jockey-Trainer Synergy**
   - Rewards proven combinations
   - Penalizes untested partnerships

## Testing Recommendations

To verify improvements:

1. Run predictions on historical races with known results
2. Compare accuracy metrics before/after changes:
   - Top pick win rate
   - Top 3 placement rate
   - ROI on value bets

3. Monitor specialist detection:
   - Check that top-ranked jockeys get appropriate boosts
   - Verify track specialists perform better at their tracks

## Future Enhancements

Potential additional improvements:

1. **Weather Integration** - Use `weather` and `wind_tracker` tables for condition-based adjustments
2. **Barrier Statistics** - Leverage `barrier_stats` table when populated
3. **Battle Memorandum** - Incorporate head-to-head horse histories
4. **Form Line Enhancement** - Better use of `form_line` relative weights and ratings
5. **Standard Times** - Compare against `standard_times` for time-based ratings

## Files Modified

- `engine/core/data_integrator.py` - Added 8 new query methods
- `engine/features/enhanced_features.py` - Enhanced jockey/trainer feature extraction
- `engine/models/ensemble_model.py` - Improved prediction weights and logic

## Database Statistics

Current data availability:
- 42 jockey rankings
- 38 trainer rankings
- 198 barrier test records
- 82 track selection records
