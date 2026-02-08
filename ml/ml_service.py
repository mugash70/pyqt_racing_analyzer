import pandas as pd
import numpy as np
import sqlite3
import logging
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

# Import ML components
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from backup.ml_ensemble_model import EnsembleModel
from backup.feature_engineering import FeatureEngineer
from backup.data_preprocessing import DataPreprocessor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MLService:
    """Direct ML service integration for PyQt app"""

    def __init__(self, db_path: Optional[str] = None, model_path: Optional[str] = None):
        if db_path is None:
            db_path = os.path.join(os.path.dirname(__file__), '..', 'database', 'hkjc_races.db')
        if model_path is None:
            model_path = os.path.join(os.path.dirname(__file__), '..', '..', 'models', 'ensemble_model.pkl')
        self.db_path = Path(db_path).resolve()
        self.model_path = Path(model_path).resolve()

        # Initialize components
        self.ml_model: Optional[EnsembleModel] = None
        self.feature_engineer = FeatureEngineer()
        self.preprocessor = DataPreprocessor()

        # Load preprocessor if available
        preprocessor_path = str(self.model_path).replace('ensemble_model.pkl', 'preprocessor.pkl')
        if Path(preprocessor_path).exists():
            self.preprocessor.load(preprocessor_path)
            logger.info(f"Preprocessor loaded from {preprocessor_path}")
        else:
            logger.warning(f"Preprocessor not found at {preprocessor_path}")

        # Load model on initialization
        self.load_model()

    def load_model(self) -> bool:
        """Load the trained ML model"""
        try:
            if self.model_path.exists():
                self.ml_model = EnsembleModel()
                self.ml_model.load(str(self.model_path))
                logger.info(f"ML model loaded from {self.model_path}")
                return True
            else:
                logger.warning(f"Model not found at {self.model_path}")
                return False
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            return False

    def get_available_races(self) -> List[Dict]:
        """Get list of available races from database"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row

            query = """
            SELECT DISTINCT r.race_date, r.race_number, r.distance, r.race_class,
                           r.track_type, r.track_condition, COUNT(hp.horse_id) as horse_count
            FROM races r
            LEFT JOIN horse_performances hp ON r.race_date = hp.race_date AND r.race_number = hp.race_number
            GROUP BY r.race_date, r.race_number
            ORDER BY r.race_date DESC, r.race_number DESC
            LIMIT 50
            """

            cursor = conn.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()
            conn.close()

            races = []
            for row in rows:
                races.append({
                    'id': f"{row['race_date']}_{row['race_number']}",
                    'date': row['race_date'],
                    'race_number': row['race_number'],
                    'distance': row['distance'],
                    'race_class': row['race_class'] or 'Class 4',
                    'track_type': row['track_type'],
                    'track_condition': row['track_condition'],
                    'horse_count': row['horse_count'],
                    'display_name': f"{row['race_date']} - Race {row['race_number']} ({row['distance']}m, {row['horse_count']} horses)"
                })

            return races

        except Exception as e:
            logger.error(f"Error fetching races: {e}")
            return []

    def predict_race(self, race_date: str, race_number: int) -> Dict:
        """Generate ML predictions for a specific race"""
        try:
            if not self.ml_model:
                return {'error': 'ML model not loaded'}

            # Get race data from database
            race_data = self._get_race_data(race_date, race_number)
            if not race_data:
                return {'error': f'No data found for race {race_date} #{race_number}'}

            predictions = []

            for horse in race_data:
                # Engineer features for this horse
                features = self._engineer_horse_features(horse, race_date)

                if features:
                    # Make prediction
                    features_df = pd.DataFrame([features])
                    X_processed, _ = self.preprocessor.preprocess(features_df, fit=False)
                    X_processed = X_processed.reindex(columns=self.ml_model.feature_names, fill_value=0)
                    print(f"X_processed shape: {X_processed.shape}, columns: {len(X_processed.columns)}")
                    print(f"Model expects: {len(self.ml_model.feature_names)} features")

                    proba = self.ml_model.predict_proba(X_processed)
                    logger.info(f"Proba type: {type(proba)}, shape: {getattr(proba, 'shape', 'no shape')}, value: {proba}")
                    try:
                        if isinstance(proba, np.ndarray):
                            if proba.ndim == 0:
                                win_probability = float(proba)  # Scalar
                            elif proba.ndim == 1:
                                win_probability = float(proba[-1])  # Last element for positive class
                            else:  # 2D
                                win_probability = float(proba[0, -1])  # Last column
                        else:
                            # Handle other types (list, Series, etc.)
                            win_probability = float(proba[0] if hasattr(proba, '__getitem__') else proba)
                    except Exception as idx_error:
                        logger.error(f"Indexing error: {idx_error}, trying fallback")
                        win_probability = float(np.asarray(proba).flat[0])

                    predictions.append({
                        'horse_id': horse['horse_id'],
                        'horse_name': horse['horse_name'],
                        'jockey': horse['jockey'] or 'Unknown',
                        'trainer': horse['trainer'] or 'Unknown',
                        'weight': horse['weight'] or 0,
                        'draw': horse['draw'] or 0,
                        'odds': horse['odds'],  # Use real market odds from database
                        'win_probability': win_probability,
                        'win_percentage': f"{win_probability * 100:.1f}%",
                        'confidence': 'High' if win_probability > 0.25 else 'Medium' if win_probability > 0.15 else 'Low'
                    })

            # Sort by probability
            predictions.sort(key=lambda x: x['win_probability'], reverse=True)

            return {
                'race_info': {
                    'date': race_date,
                    'race_number': race_number,
                    'horse_count': len(predictions)
                },
                'predictions': predictions,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error predicting race: {e}")
            return {'error': str(e)}

    def _get_race_data(self, race_date: str, race_number: int) -> List[Dict]:
        """Get horse data for a specific race"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row

            # Get horse data
            horse_query = """
            SELECT hp.horse_id, h.horse_name, hp.jockey, hp.trainer,
                   hp.weight, hp.draw
            FROM horse_performances hp
            JOIN horses h ON hp.horse_id = h.horse_id
            JOIN races r ON hp.race_date = r.race_date AND hp.race_number = r.race_number
            WHERE r.race_date = ? AND r.race_number = ?
            ORDER BY hp.draw
            """

            cursor = conn.cursor()
            cursor.execute(horse_query, (race_date, race_number))
            horse_rows = cursor.fetchall()

            # Get positions_json for odds
            race_query = """
            SELECT positions_json FROM races
            WHERE race_date = ? AND race_number = ?
            """
            cursor.execute(race_query, (race_date, race_number))
            race_row = cursor.fetchone()
            conn.close()

            # Parse positions_json to get odds
            odds_dict = {}
            if race_row and race_row['positions_json']:
                try:
                    import json
                    positions_data = json.loads(race_row['positions_json'])
                    for pos_data in positions_data:
                        horse_number = pos_data.get('horse_number')
                        odds = pos_data.get('odds')
                        if horse_number and odds:
                            try:
                                odds_dict[str(horse_number)] = float(odds)
                            except (ValueError, TypeError):
                                pass
                except (json.JSONDecodeError, KeyError) as e:
                    logger.warning(f"Could not parse positions_json for odds: {e}")

            # Add race_number and real odds to each horse dict
            horses = [dict(row) for row in horse_rows]
            for horse in horses:
                horse['race_number'] = race_number
                # Try to get real odds, fallback to default based on draw position
                draw = horse.get('draw', 8)
                default_odds = 5.0 + (draw * 0.5)  # Inside draws get lower default odds
                horse['odds'] = odds_dict.get(str(draw), default_odds)
                
                # Ensure odds is never None
                if horse['odds'] is None or horse['odds'] <= 0:
                    horse['odds'] = default_odds
            return horses

        except Exception as e:
            logger.error(f"Error getting race data: {e}")
            return []

    def _engineer_horse_features(self, horse: Dict, race_date: str) -> Optional[Dict]:
        """Engineer features for a single horse using full feature engineering pipeline"""
        try:
            # Get race number from the predict_race call - need to pass it
            race_number = horse.get('race_number', 1)

            # Get race info
            race_info = self._get_race_info(race_date, race_number)

            # Basic features
            features = {
                'race_date': race_date,
                'race_number': race_number,
                'horse_id': horse['horse_id'],
                'horse_name': horse['horse_name'],
                'jockey': horse['jockey'] or 'Unknown',
                'trainer': horse['trainer'] or 'Unknown',
                'position': None,  # Not available for prediction
                'weight': horse['weight'] or 1150,
                'draw': horse['draw'] or 1,
                'distance': race_info.get('distance', 1650) if race_info else 1650,
                'race_class': race_info.get('race_class', 'Class 4') if race_info else 'Class 4',
                'track_type': race_info.get('track_type', 'Turf') if race_info else 'Turf',
                'track_condition': race_info.get('track_condition', 'Good') if race_info else 'Good',
                'odds': 0  # Remove hardcoded odds from features (not predictive)
            }

            # Calculate horse stats using historical data
            horse_stats = self._compute_horse_stats_historical(horse['horse_id'], race_date)
            features.update(horse_stats)

            # Calculate jockey stats
            jockey_stats = self._compute_jockey_stats_historical(horse['jockey'], race_date)
            features.update(jockey_stats)

            # Calculate trainer stats
            trainer_stats = self._compute_trainer_stats_historical(horse['trainer'], race_date)
            features.update(trainer_stats)

            # Add race-level features
            race_features = self._compute_race_features_for_race(race_date, horse.get('race_number', 1))
            features.update(race_features)

            # Engineer derived features
            features = self._engineer_derived_features_single(features)

            return features

        except Exception as e:
            logger.error(f"Error engineering features for {horse.get('horse_name', 'Unknown')}: {e}")
            return None

    def _compute_basic_stats(self, horse: Dict, race_date: str) -> Dict:
        """Compute basic statistical features"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row

            # Get recent performances for this horse
            query = """
            SELECT position, weight
            FROM horse_performances hp
            JOIN races r ON hp.race_date = r.race_date AND hp.race_number = r.race_number
            WHERE hp.horse_id = ? AND r.race_date < ?
            ORDER BY r.race_date DESC
            LIMIT 10
            """

            cursor = conn.cursor()
            cursor.execute(query, (horse['horse_id'], race_date))
            performances = cursor.fetchall()

            if len(performances) == 0:
                # No historical data - return default values
                return {
                    'recent_avg_position': 7.0,
                    'recent_win_rate': 0.0,
                    'career_races': 0,
                    'avg_odds': 10.0,
                    'weight_trend': 0
                }

            positions = []
            weights = []
            for p in performances:
                if p['position'] is not None:
                    try:
                        positions.append(float(p['position']))
                    except (ValueError, TypeError):
                        pass
                if p['weight'] is not None:
                    try:
                        weights.append(float(p['weight']))
                    except (ValueError, TypeError):
                        pass

            # Calculate stats
            avg_position = np.mean(positions) if positions else 7.0
            win_rate = len([p for p in positions if p == 1]) / len(positions) if positions else 0.0
            # Calculate estimated average odds based on performance
            # Better horses (lower avg_position, higher win_rate) have lower odds
            performance_score = win_rate * 2 + (8 - avg_position) / 7
            avg_odds = max(2.0, 25.0 - performance_score * 15)

            # Weight trend (recent - older)
            weight_trend = 0
            if len(weights) >= 2:
                recent_weights = weights[:3]  # Last 3 races
                older_weights = weights[3:] if len(weights) > 3 else weights
                if older_weights:
                    weight_trend = np.mean(recent_weights) - np.mean(older_weights)

            conn.close()

            return {
                'recent_avg_position': float(avg_position),
                'recent_win_rate': float(win_rate),
                'career_races': len(performances),
                'avg_odds': float(avg_odds),
                'weight_trend': float(weight_trend)
            }

        except Exception as e:
            logger.error(f"Error computing stats: {e}")
            return {
                'recent_avg_position': 7.0,
                'recent_win_rate': 0.0,
                'career_races': 0,
                'avg_odds': 10.0,
                'weight_trend': 0
            }

    def _get_race_info(self, race_date: str, race_number: int) -> Optional[Dict]:
        """Get race information"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row

            query = """
            SELECT distance, race_class, track_type, track_condition
            FROM races
            WHERE race_date = ? AND race_number = ?
            """

            cursor = conn.cursor()
            cursor.execute(query, (race_date, race_number))
            row = cursor.fetchone()
            conn.close()

            if row:
                return dict(row)
            return None

        except Exception as e:
            logger.error(f"Error getting race info: {e}")
            return None

    def _compute_horse_stats_historical(self, horse_id: str, race_date: str) -> Dict[str, float]:
        """Compute horse statistics using only races before the given date"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row

            # Get all historical races for this horse
            horse_races_query = """
            SELECT
                race_date,
                position,
                CAST(weight as FLOAT) as weight,
                draw
            FROM horse_performances
            WHERE horse_id = ? AND race_date < ?
            AND position IS NOT NULL
            ORDER BY race_date DESC
            """

            horse_races = pd.read_sql_query(horse_races_query, conn, params=(horse_id, race_date))

            if len(horse_races) == 0:
                return {
                    'win_rate': 0.08,  # Default for new horses
                    'top3_rate': 0.25,
                    'top5_rate': 0.45,
                    'avg_position': 6.5,
                    'consistency_score': 0.3,
                    'recent_form': 0.5,
                    'form_trend': 0.0,
                    'draw_performance': 0.5,
                    'weight_trend': 0.0
                }

            total_races = len(horse_races)
            wins = (horse_races['position'] == 1).sum()
            top3 = (horse_races['position'] <= 3).sum()
            top5 = (horse_races['position'] <= 5).sum()

            # Recent form (last 3 races)
            recent_races = horse_races.head(3)
            if len(recent_races) > 0:
                recent_avg_pos = recent_races['position'].mean()
                recent_form = 1 - (recent_avg_pos - 1) / 13  # Normalize to 0-1 scale
            else:
                recent_form = 0.5

            # Form trend (improvement over last 5 races)
            if len(horse_races) >= 5:
                early_races = horse_races.tail(3)['position'].mean()  # First 3 races (chronologically)
                late_races = horse_races.head(3)['position'].mean()   # Last 3 races
                if early_races > 0:
                    form_trend = (early_races - late_races) / early_races  # Positive = improving
                else:
                    form_trend = 0.0
            else:
                form_trend = 0.0

            # Draw performance (simplified - does horse win more with inside draws?)
            if len(horse_races) >= 3:
                # Simple heuristic: horses that win from outside draws are better
                outside_draws = horse_races[horse_races['draw'] > 6]
                if len(outside_draws) > 0:
                    outside_win_rate = (outside_draws['position'] == 1).mean()
                    draw_performance = 0.4 + (outside_win_rate * 0.6)  # Boost for outside draw winners
                else:
                    draw_performance = 0.5
            else:
                draw_performance = 0.5

            # Weight trend (is horse getting lighter?)
            if len(horse_races) >= 2:
                first_weight = horse_races['weight'].iloc[-1]  # First race weight
                last_weight = horse_races['weight'].iloc[0]   # Most recent weight
                if first_weight > 0:
                    weight_trend = (first_weight - last_weight) / first_weight  # Positive = getting lighter
                else:
                    weight_trend = 0.0
            else:
                weight_trend = 0.0

            # Consistency score (lower std dev = more consistent)
            position_std = horse_races['position'].std()
            consistency_score = 1 - min(position_std / 7, 1) if not pd.isna(position_std) else 0.5

            return {
                'win_rate': wins / total_races,
                'top3_rate': top3 / total_races,
                'top5_rate': top5 / total_races,
                'avg_position': horse_races['position'].mean(),
                'consistency_score': consistency_score,
                'recent_form': recent_form,
                'form_trend': form_trend,
                'draw_performance': draw_performance,
                'weight_trend': weight_trend
            }

        except Exception as e:
            logger.error(f"Error computing horse stats: {e}")
            return {
                'win_rate': 0.08,
                'top3_rate': 0.25,
                'top5_rate': 0.45,
                'avg_position': 6.5,
                'consistency_score': 0.3,
                'recent_form': 0.5,
                'form_trend': 0.0,
                'draw_performance': 0.5,
                'weight_trend': 0.0
            }

    def _compute_jockey_stats_historical(self, jockey: str, race_date: str) -> Dict[str, float]:
        """Compute jockey statistics using only races before the given date"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row

            # Get all jockey's recent races
            jockey_races_query = """
            SELECT
                race_date,
                position,
                draw
            FROM horse_performances
            WHERE jockey = ? AND race_date < ?
            AND position IS NOT NULL
            ORDER BY race_date DESC
            """

            jockey_races = pd.read_sql_query(jockey_races_query, conn, params=(jockey, race_date))

            if len(jockey_races) == 0:
                return {
                    'jockey_win_rate': 0.08,
                    'jockey_top3_rate': 0.22,
                    'jockey_races': 1,
                    'jockey_recent_form': 0.5,
                    'jockey_draw_skill': 0.5
                }

            total_races = len(jockey_races)
            wins = (jockey_races['position'] == 1).sum()
            top3 = (jockey_races['position'] <= 3).sum()

            # Recent form (last 10 rides)
            recent_rides = jockey_races.head(10)
            if len(recent_rides) > 0:
                recent_wins = (recent_rides['position'] == 1).sum()
                jockey_recent_form = recent_wins / len(recent_rides)
            else:
                jockey_recent_form = wins / total_races

            # Draw skill (simplified - jockeys who win from bad draws are skilled)
            if len(jockey_races) >= 5:
                # Count wins from outside draws (draw > 8 in a typical 12-horse field)
                outside_wins = ((jockey_races['draw'] > 8) & (jockey_races['position'] == 1)).sum()
                total_outside_rides = (jockey_races['draw'] > 8).sum()
                if total_outside_rides > 0:
                    outside_win_rate = outside_wins / total_outside_rides
                    jockey_draw_skill = 0.4 + (outside_win_rate * 0.6)  # Boost for outside draw wins
                else:
                    jockey_draw_skill = 0.5
            else:
                jockey_draw_skill = 0.5

            return {
                'jockey_win_rate': wins / total_races,
                'jockey_top3_rate': top3 / total_races,
                'jockey_races': total_races,
                'jockey_recent_form': jockey_recent_form,
                'jockey_draw_skill': jockey_draw_skill
            }

        except Exception as e:
            logger.error(f"Error computing jockey stats: {e}")
            return {
                'jockey_win_rate': 0.08,
                'jockey_top3_rate': 0.22,
                'jockey_races': 1,
                'jockey_recent_form': 0.5,
                'jockey_draw_skill': 0.5
            }

    def _compute_trainer_stats_historical(self, trainer: str, race_date: str) -> Dict[str, float]:
        """Compute trainer statistics using only races before the given date"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row

            query = """
            SELECT
                COUNT(*) as trainer_races,
                SUM(CASE WHEN position = 1 THEN 1 ELSE 0 END) as trainer_wins,
                SUM(CASE WHEN position IN (1, 2, 3) THEN 1 ELSE 0 END) as trainer_top3
            FROM horse_performances
            WHERE trainer = ? AND race_date < ? AND position IS NOT NULL
            """

            result = pd.read_sql_query(query, conn, params=(trainer, race_date))

            if len(result) == 0 or result.iloc[0]['trainer_races'] == 0:
                return {
                    'trainer_win_rate': 0.1,
                    'trainer_top3_rate': 0.25,
                    'trainer_races': 1
                }

            row = result.iloc[0]
            total_races = max(row['trainer_races'], 1)

            return {
                'trainer_win_rate': row['trainer_wins'] / total_races,
                'trainer_top3_rate': row['trainer_top3'] / total_races,
                'trainer_races': row['trainer_races']
            }

        except Exception as e:
            logger.error(f"Error computing trainer stats: {e}")
            return {
                'trainer_win_rate': 0.1,
                'trainer_top3_rate': 0.25,
                'trainer_races': 1
            }

    def _compute_race_features_for_race(self, race_date: str, race_number: int) -> Dict[str, float]:
        """Compute race-level features for a specific race"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row

            query = """
            SELECT
                distance,
                race_class,
                track_type,
                track_condition,
                COUNT(*) as field_size
            FROM horse_performances hp
            JOIN races r ON hp.race_date = r.race_date AND hp.race_number = r.race_number
            WHERE hp.race_date = ? AND hp.race_number = ?
            GROUP BY hp.race_date, hp.race_number
            """

            result = pd.read_sql_query(query, conn, params=(race_date, race_number))

            if len(result) == 0:
                return {
                    'field_size': 12,
                    'season': 6,
                    'is_handicap': 0,
                    'avg_field_odds': 10.0,
                    'odds_variance': 5.0,
                    'avg_odds': 10.0
                }

            row = result.iloc[0]

            return {
                'field_size': row['field_size'],
                'season': pd.to_datetime(race_date).month,
                'is_handicap': 1 if '班' in str(row['race_class']) else 0,
                'avg_field_odds': 0,  # Remove hardcoded odds
                'odds_variance': 0,     # Remove hardcoded odds
                'avg_odds': 0          # Remove hardcoded odds
            }

        except Exception as e:
            logger.error(f"Error computing race features: {e}")
            return {
                'field_size': 12,
                'season': 6,
                'is_handicap': 0,
                'avg_field_odds': 0,
                'odds_variance': 0,
                'avg_odds': 0
            }

    def _engineer_derived_features_single(self, features: Dict) -> Dict:
        """Engineer derived features for a single horse"""
        try:
            # Convert to DataFrame for easier computation
            df = pd.DataFrame([features])

            df['weight_adj_factor'] = 1 - (df['weight'].astype(float) - df['weight'].astype(float).mean()) / (df['weight'].astype(float).std() + 1e-6)

            df['draw_effect'] = 1 - (df['draw'].astype(float) - df['draw'].astype(float).median()) / (df['draw'].astype(float).std() + 1e-6)

            df['odds_confidence'] = 1 / (1 + np.exp(df['odds'].astype(float)))

            df['jockey_horse_synergy'] = (df['jockey_win_rate'].fillna(0) * df['win_rate'].fillna(0)) + 0.5

            df['trainer_class_specialty'] = df['trainer_win_rate'].fillna(0.5)

            df['distance_specialty'] = df['win_rate'].fillna(0.5)

            df['class_progression'] = 0.5

            df['recent_form_5'] = df['recent_form']

            df['recent_form_10'] = df['recent_form']

            df['field_strength'] = df['avg_field_odds'] * df['field_size']

            df['favorite_bias'] = (df['odds'].astype(float) < df['avg_odds'].fillna(999)).astype(int)

            df['track_condition_bonus'] = df['win_rate'].fillna(0.5)

            # Return the features dict
            return df.iloc[0].to_dict()

        except Exception as e:
            logger.error(f"Error engineering derived features: {e}")
            return features

    def close(self):
        """Clean up resources"""
        if hasattr(self, 'feature_engineer'):
            self.feature_engineer.close()
