import sqlite3
import os
import logging
import json
from datetime import datetime
from typing import List, Dict, Optional, Any

logger = logging.getLogger(__name__)

from .scraper import HKJCResultsScraper

class HKJCDataPipeline:
    """Pipeline for managing HKJC data scraping and database storage."""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            self.db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'hkjc_races.db')
        else:
            self.db_path = db_path
        
        self.scraper = HKJCResultsScraper()
        self._ensure_db_directory()
        self._initialize_new_tables()

    def _ensure_db_directory(self):
        db_dir = os.path.dirname(self.db_path)
        if not os.path.exists(db_dir):
            os.makedirs(db_dir)

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _initialize_new_tables(self):
        """Create new tables if they don't exist and migrate schema if needed."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # 1. Ensure tables exist
        self._create_tables_if_not_exists(cursor)
        
        # 2. Migration: Check for missing columns in existing tables
        self._migrate_schema(cursor)
        
        conn.commit()
        conn.close()

    def _create_tables_if_not_exists(self, cursor):
        """Create all tables with full schema."""
        # JKC Stats
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS jkc_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                jockey_name TEXT,
                last_10_points TEXT,
                avg_points REAL,
                season_avg REAL,
                scraped_at TEXT
            )
        """)
        
        # TNC Stats
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tnc_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trainer_name TEXT,
                last_10_points TEXT,
                avg_points REAL,
                season_avg REAL,
                scraped_at TEXT
            )
        """)
        
        # Conghua Movement
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conghua_movement (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                horse_name TEXT,
                movement_date TEXT,
                from_location TEXT,
                to_location TEXT,
                reason TEXT,
                scraped_at TEXT
            )
        """)
        
        # Horse Ratings
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS horse_ratings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                horse_name TEXT,
                current_rating INTEGER,
                previous_rating INTEGER,
                rating_change TEXT,
                class TEXT,
                scraped_at TEXT
            )
        """)
        
        # Detailed Trackwork
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS detailed_trackwork (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                race_date TEXT,
                racecourse TEXT,
                race_number INTEGER,
                horse_name TEXT,
                horse_number TEXT,
                trackwork_time TEXT,
                distance TEXT,
                track_condition TEXT,
                remarks TEXT,
                scraped_at TEXT
            )
        """)
        
        # Jockey Favourites
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS jockey_fav_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                jockey_name TEXT,
                fav_rides INTEGER,
                fav_wins INTEGER,
                fav_win_rate REAL,
                fav_places INTEGER,
                fav_place_rate REAL,
                scraped_at TEXT
            )
        """)
        
        # Trainer Favourites
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trainer_fav_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trainer_name TEXT,
                fav_runs INTEGER,
                fav_wins INTEGER,
                fav_win_rate REAL,
                fav_places INTEGER,
                fav_place_rate REAL,
                scraped_at TEXT
            )
        """)
        
        # Standard Times
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS standard_times (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                racecourse TEXT,
                distance TEXT,
                track_type TEXT,
                standard_time TEXT,
                record_time TEXT,
                record_holder TEXT,
                record_date TEXT,
                scraped_at TEXT
            )
        """)
        
        # Jockey Rankings
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS jockey_rankings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rank INTEGER,
                jockey_name TEXT,
                wins INTEGER,
                seconds INTEGER,
                thirds INTEGER,
                fourths INTEGER,
                fifths INTEGER,
                rides INTEGER,
                win_rate REAL,
                place_rate REAL,
                scraped_at TEXT
            )
        """)
        
        # Trainer Rankings
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trainer_rankings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rank INTEGER,
                trainer_name TEXT,
                wins INTEGER,
                seconds INTEGER,
                thirds INTEGER,
                fourths INTEGER,
                fifths INTEGER,
                runners INTEGER,
                win_rate REAL,
                place_rate REAL,
                scraped_at TEXT
            )
        """)
        
        # Trainer King Odds
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trainer_king_odds (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                race_date TEXT,
                scraped_at TEXT,
                trainer_name TEXT,
                odds REAL,
                trend TEXT
            )
        """)
        
        # Race Day Changes
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS race_day_changes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                race_date TEXT,
                race_number INTEGER,
                horse_number INTEGER,
                change_type TEXT,
                details TEXT,
                scraped_at TEXT
            )
        """)
        
        # Track Selection Data
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS track_selection_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                race_date TEXT,
                racecourse TEXT,
                track_type TEXT,
                course_setting TEXT,
                selection_stats TEXT,
                scraped_at TEXT
            )
        """)
        
        # Future Race Cards
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS future_race_cards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                race_date TEXT,
                race_time TEXT,
                race_number INTEGER,
                racecourse TEXT,
                horse_number INTEGER,
                horse_name TEXT,
                jockey TEXT,
                trainer TEXT,
                weight TEXT,
                draw INTEGER,
                race_distance TEXT,
                race_class TEXT,
                track_going TEXT,
                scraped_at TEXT
            )
        """)
        
        # Race Results
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS race_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                race_date TEXT,
                race_number INTEGER,
                racecourse TEXT,
                horse_number INTEGER,
                horse_name TEXT,
                jockey TEXT,
                trainer TEXT,
                actual_weight TEXT,
                draw INTEGER,
                position TEXT,
                finished_time TEXT,
                winning_odds REAL,
                scraped_at TEXT
            )
        """)
        
        # Live Odds
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS odds_live (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                race_date TEXT,
                race_number INTEGER,
                racecourse TEXT,
                horse_number INTEGER,
                horse_name TEXT,
                win_odds REAL,
                place_odds REAL,
                scraped_at TEXT
            )
        """)
        
        # Odds History
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS odds_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                race_date TEXT,
                race_number INTEGER,
                racecourse TEXT,
                horse_number INTEGER,
                horse_name TEXT,
                win_odds REAL,
                place_odds REAL,
                scraped_at TEXT
            )
        """)
        
        # Fixtures
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS fixtures (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                race_date TEXT,
                racecourse TEXT,
                day_night TEXT,
                track_type TEXT,
                race_count INTEGER,
                races_json TEXT,
                scraped_at TEXT
            )
        """)
        
        # Barrier Tests
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS barrier_tests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                horse_name TEXT,
                test_date TEXT,
                barrier TEXT,
                time TEXT,
                remarks TEXT,
                scraped_at TEXT
            )
        """)
        
        # Weather
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS weather (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                race_date TEXT,
                racecourse TEXT,
                temperature TEXT,
                humidity TEXT,
                condition TEXT,
                scraped_at TEXT
            )
        """)
        
        # Last Race Summaries
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS last_race_summaries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                race_date TEXT,
                race_number INTEGER,
                summary_text TEXT,
                scraped_at TEXT
            )
        """)
        
        # Professional Schedules
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS professional_schedules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                race_date TEXT,
                pro_type TEXT,
                professional_name TEXT,
                race_number TEXT,
                horse_name TEXT,
                schedule_details TEXT,
                scraped_at TEXT
            )
        """)
        
        # Barrier Stats
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS barrier_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                horse_name TEXT,
                barrier_position TEXT,
                wins INTEGER,
                runs INTEGER,
                win_rate REAL,
                scraped_at TEXT
            )
        """)
        
        # Wind Tracker
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS wind_tracker (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                race_date TEXT,
                track TEXT,
                position TEXT,
                wind_direction TEXT,
                wind_speed TEXT,
                gust_speed TEXT,
                temperature TEXT,
                humidity TEXT,
                rainfall TEXT,
                update_time TEXT,
                scraped_at TEXT
            )
        """)
        
        # Battle Memorandum
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS battle_memorandum (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                horse_name TEXT,
                last_race_date TEXT,
                memo TEXT,
                scraped_at TEXT
            )
        """)
        
        # New Horse Introductions
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS new_horse_introductions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                horse_name TEXT,
                origin TEXT,
                trainer TEXT,
                age TEXT,
                sex TEXT,
                scraped_at TEXT
            )
        """)
        
        # Injury Records
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS injury_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                horse_name TEXT,
                injury_date TEXT,
                condition TEXT,
                status TEXT,
                scraped_at TEXT
            )
        """)

    def _migrate_schema(self, cursor):
        """Add missing columns to existing tables."""
        migrations = {
            "new_horse_introductions": ["origin", "trainer", "age", "sex"],
            "wind_tracker": ["track", "position", "wind_direction", "wind_speed", "gust_speed", "temperature", "humidity", "rainfall", "update_time"],
            "injury_records": ["condition", "status"],
            "future_race_cards": ["race_time"]
        }
        
        for table, columns in migrations.items():
            try:
                cursor.execute(f"PRAGMA table_info({table})")
                existing_cols = [row[1] for row in cursor.fetchall()]
                
                for col in columns:
                    if col not in existing_cols:
                        logger.info(f"Migrating table {table}: adding column {col}")
                        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col} TEXT")
            except sqlite3.OperationalError as e:
                logger.error(f"Failed to migrate table {table}: {e}")

    def sync_all_rankings(self, *args, **kwargs) -> int:
        """Sync jockey and trainer rankings."""
        total = 0
        j_rankings = self.scraper.scrape_jockey_rankings()
        if j_rankings:
            total += self.save_jockey_rankings(j_rankings)
            
        t_rankings = self.scraper.scrape_trainer_rankings()
        if t_rankings:
            total += self.save_trainer_rankings(t_rankings)
            
        return total

    def save_jockey_rankings(self, rankings: List[Dict], *args, **kwargs) -> int:
        conn = self._get_connection()
        cursor = conn.cursor()
        scraped_at = datetime.now().isoformat()
        
        cursor.execute("DELETE FROM jockey_rankings")
        
        count = 0
        for r in rankings:
            cursor.execute("""
                INSERT INTO jockey_rankings (rank, jockey_name, wins, seconds, thirds, fourths, fifths, rides, win_rate, place_rate, scraped_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                r.get('rank', 0), 
                r.get('jockey_name', ''), 
                r.get('wins', 0), 
                r.get('seconds', 0), 
                r.get('thirds', 0), 
                r.get('fourths', 0), 
                r.get('fifths', 0), 
                r.get('rides', 0), 
                r.get('win_rate', 0.0), 
                r.get('place_rate', 0.0), 
                scraped_at
            ))
            count += 1
            
        conn.commit()
        conn.close()
        return count

    def save_trainer_rankings(self, rankings: List[Dict], *args, **kwargs) -> int:
        conn = self._get_connection()
        cursor = conn.cursor()
        scraped_at = datetime.now().isoformat()
        
        cursor.execute("DELETE FROM trainer_rankings")
        
        count = 0
        for r in rankings:
            cursor.execute("""
                INSERT INTO trainer_rankings (rank, trainer_name, wins, seconds, thirds, fourths, fifths, runners, win_rate, place_rate, scraped_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                r.get('rank', 0), 
                r.get('trainer_name', ''), 
                r.get('wins', 0), 
                r.get('seconds', 0), 
                r.get('thirds', 0), 
                r.get('fourths', 0), 
                r.get('fifths', 0), 
                r.get('runners', 0), 
                r.get('win_rate', 0.0), 
                r.get('place_rate', 0.0), 
                scraped_at
            ))
            count += 1
            
        conn.commit()
        conn.close()
        return count

    def save_future_race_cards(self, race_date, racecourse: str) -> int:
        """Fetch and save future race cards for all races in a day."""
        if isinstance(race_date, datetime):
            race_date = race_date.strftime('%Y-%m-%d')
            
        logger.info(f"Saving future race cards for {race_date} at {racecourse}")
        
        total_saved = 0
        for race_no in range(1, 13):
            data = self.scraper.scrape_race_card(race_date, race_no, racecourse)
            if not data:
                if race_no > 8:
                    break
                continue
                
            conn = self._get_connection()
            cursor = conn.cursor()
            
            for horse in data:
                cursor.execute("""
                    SELECT id FROM future_race_cards 
                    WHERE race_date = ? AND race_number = ? AND racecourse = ? AND horse_number = ?
                """, (horse['race_date'], horse['race_number'], horse['racecourse'], horse['horse_number']))
                
                existing = cursor.fetchone()
                if existing:
                    cursor.execute("""
                        UPDATE future_race_cards SET
                        horse_name = ?, jockey = ?, trainer = ?, weight = ?, draw = ?,
                        race_distance = ?, race_class = ?, track_going = ?, race_time = ?, scraped_at = ?
                        WHERE id = ?
                    """, (
                        horse['horse_name'], horse['jockey'], horse['trainer'], 
                        horse['weight'], horse['draw'], horse['race_distance'],
                        horse['race_class'], horse['track_going'], horse.get('race_time', ''),
                        horse['scraped_at'], existing[0]
                    ))
                else:
                    cursor.execute("""
                        INSERT INTO future_race_cards (
                            race_date, race_number, racecourse, horse_number, horse_name,
                            jockey, trainer, weight, draw, race_distance, race_class,
                            track_going, race_time, scraped_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        horse['race_date'], horse['race_number'], horse['racecourse'],
                        horse['horse_number'], horse['horse_name'], horse['jockey'],
                        horse['trainer'], horse['weight'], horse['draw'],
                        horse['race_distance'], horse['race_class'], horse['track_going'],
                        horse.get('race_time', ''), horse['scraped_at']
                    ))
                total_saved += 1
                
            conn.commit()
            conn.close()
            
        logger.info(f"Total horses saved for {race_date}: {total_saved}")
        return total_saved

    def save_race_results(self, race_date, racecourse: str) -> int:
        """Fetch and save race results for all races in a day."""
        if isinstance(race_date, datetime):
            race_date = race_date.strftime('%Y-%m-%d')
            
        logger.info(f"Saving race results for {race_date} at {racecourse}")
        
        total_saved = 0
        for race_no in range(1, 13):
            data = self.scraper.scrape_results(race_date, race_no, racecourse)
            if not data:
                if race_no > 8:
                    break
                continue
                
            conn = self._get_connection()
            cursor = conn.cursor()
            
            for horse in data:
                cursor.execute("""
                    SELECT id FROM race_results 
                    WHERE race_date = ? AND race_number = ? AND racecourse = ? AND horse_number = ?
                """, (horse['race_date'], horse['race_number'], horse['racecourse'], horse['horse_number']))
                
                existing = cursor.fetchone()
                if existing:
                    cursor.execute("""
                        UPDATE race_results SET
                        horse_name = ?, jockey = ?, trainer = ?, actual_weight = ?, 
                        draw = ?, position = ?, finished_time = ?, winning_odds = ?, scraped_at = ?
                        WHERE id = ?
                    """, (
                        horse['horse_name'], horse['jockey'], horse['trainer'], 
                        horse['actual_weight'], horse['draw'], horse['position'],
                        horse['finish_time'], horse['win_odds'], horse['scraped_at'],
                        existing[0]
                    ))
                else:
                    cursor.execute("""
                        INSERT INTO race_results (
                            race_date, race_number, racecourse, horse_number, horse_name,
                            jockey, trainer, actual_weight, draw, position, finished_time,
                            winning_odds, scraped_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        horse['race_date'], horse['race_number'], horse['racecourse'],
                        horse['horse_number'], horse['horse_name'], horse['jockey'],
                        horse['trainer'], horse['actual_weight'], horse['draw'],
                        horse['position'], horse['finish_time'], horse['win_odds'],
                        horse['scraped_at']
                    ))
                total_saved += 1
                
            conn.commit()
            conn.close()
            
        return total_saved

    def save_live_odds(self, race_date: str, race_number: int, racecourse: str) -> int:
        """Fetch and save live odds."""
        data = self.scraper.scrape_live_odds(race_date, race_number, racecourse)
        if not data:
            return 0
            
        conn = self._get_connection()
        cursor = conn.cursor()
        
        count = 0
        for odds in data:
            # Save to odds_live
            cursor.execute("""
                INSERT INTO odds_live (race_date, race_number, racecourse, horse_number, horse_name, win_odds, place_odds, scraped_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (odds['race_date'], odds['race_number'], odds['racecourse'], odds['horse_number'], odds['horse_name'], odds['win_odds'], odds['place_odds'], odds['scraped_at']))
            
            # Also save to odds_history
            cursor.execute("""
                INSERT INTO odds_history (race_date, race_number, racecourse, horse_number, horse_name, win_odds, place_odds, scraped_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (odds['race_date'], odds['race_number'], odds['racecourse'], odds['horse_number'], odds['horse_name'], odds['win_odds'], odds['place_odds'], odds['scraped_at']))
            count += 1
            
        conn.commit()
        conn.close()
        return count


    def save_trainer_king_odds(self, race_date: str, odds_data: List[Dict]) -> int:
        """Save Trainer King odds to database."""
        conn = self._get_connection()
        cursor = conn.cursor()
        scraped_at = datetime.now().isoformat()
        
        count = 0
        for entry in odds_data:
            cursor.execute(
                "INSERT INTO trainer_king_odds (race_date, scraped_at, trainer_name, odds, trend) VALUES (?, ?, ?, ?, ?)",
                (race_date, scraped_at, entry['trainer'], entry['odds'], entry.get('trend'))
            )
            count += 1
            
        conn.commit()
        conn.close()
        return count

    def save_race_day_changes(self, race_date: str, changes: List[Dict]) -> int:
        """Save race day changes (substitutions, etc) to database."""
        conn = self._get_connection()
        cursor = conn.cursor()
        scraped_at = datetime.now().isoformat()
        
        count = 0
        for change in changes:
            cursor.execute(
                "INSERT INTO race_day_changes (race_date, race_number, horse_number, change_type, details, scraped_at) VALUES (?, ?, ?, ?, ?, ?)",
                (race_date, change.get('race_number'), change.get('horse_number'), change.get('type', 'Change'), change['details'], scraped_at)
            )
            count += 1
            
        conn.commit()
        conn.close()
        return count

    def save_track_selection(self, race_date: str, data: Dict) -> int:
        """Save track selection data to database."""
        conn = self._get_connection()
        cursor = conn.cursor()
        scraped_at = datetime.now().isoformat()
        
        cursor.execute("""
            INSERT INTO track_selection_data (race_date, racecourse, track_type, course_setting, selection_stats, scraped_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (race_date, data.get('racecourse'), data.get('track_type'), data.get('course_setting'), data.get('stats'), scraped_at))
        
        conn.commit()
        conn.close()
        return 1

    def save_jkc_stats(self) -> int:
        """Fetch and save JKC stats."""
        data = self.scraper.scrape_jkc_stats()
        if not data:
            return 0
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM jkc_stats")
        for item in data:
            cursor.execute("""
                INSERT INTO jkc_stats (jockey_name, last_10_points, avg_points, season_avg, scraped_at)
                VALUES (?, ?, ?, ?, ?)
            """, (item.get('jockey'), str(item.get('points', '')), item.get('avg_points', 0), item.get('season_avg', 0), item.get('scraped_at', datetime.now().isoformat())))
        conn.commit()
        conn.close()
        return len(data)

    def save_tnc_stats(self) -> int:
        """Fetch and save TNC stats."""
        data = self.scraper.scrape_tnc_stats()
        if not data:
            return 0
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tnc_stats")
        for item in data:
            cursor.execute("""
                INSERT INTO tnc_stats (trainer_name, last_10_points, avg_points, season_avg, scraped_at)
                VALUES (?, ?, ?, ?, ?)
            """, (item.get('trainer'), str(item.get('points', '')), item.get('avg_points', 0), item.get('season_avg', 0), item.get('scraped_at', datetime.now().isoformat())))
        conn.commit()
        conn.close()
        return len(data)

    def save_conghua_movement(self) -> int:
        """Fetch and save Conghua movement records."""
        data = self.scraper.scrape_conghua_movement()
        if not data:
            return 0
        conn = self._get_connection()
        cursor = conn.cursor()
        for item in data:
            cursor.execute("""
                INSERT INTO conghua_movement (horse_name, movement_date, from_location, to_location, reason, scraped_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (item.get('horse_name'), item.get('movement_date'), item.get('from_location'), item.get('to_location'), item.get('reason'), item.get('scraped_at', datetime.now().isoformat())))
        conn.commit()
        conn.close()
        return len(data)

    def save_horse_ratings(self) -> int:
        """Fetch and save horse ratings."""
        data = self.scraper.scrape_horse_ratings()
        if not data:
            return 0
        conn = self._get_connection()
        cursor = conn.cursor()
        for item in data:
            cursor.execute("""
                INSERT INTO horse_ratings (horse_name, current_rating, previous_rating, rating_change, class, scraped_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (item.get('horse_name'), item.get('current_rating'), item.get('previous_rating'), item.get('rating_change'), item.get('class'), item.get('scraped_at', datetime.now().isoformat())))
        conn.commit()
        conn.close()
        return len(data)

    def save_detailed_trackwork(self, race_date: str, racecourse: str = "ST") -> int:
        """Fetch and save detailed trackwork."""
        data = self.scraper.scrape_detailed_trackwork(race_date, racecourse)
        if not data:
            return 0
        conn = self._get_connection()
        cursor = conn.cursor()
        for item in data:
            cursor.execute("""
                INSERT INTO detailed_trackwork (race_date, racecourse, race_number, horse_name, horse_number, trackwork_time, distance, track_condition, remarks, scraped_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (item.get('race_date'), item.get('racecourse'), item.get('race_number'), item.get('horse_name'), item.get('horse_number'), item.get('trackwork_time'), item.get('distance'), item.get('track_condition'), item.get('remarks'), item.get('scraped_at', datetime.now().isoformat())))
        conn.commit()
        conn.close()
        return len(data)

    def save_jockey_favourites(self) -> int:
        """Fetch and save jockey favourites."""
        data = self.scraper.scrape_jockey_favourites()
        if not data:
            return 0
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM jockey_fav_stats")
        for item in data:
            cursor.execute("""
                INSERT INTO jockey_fav_stats (jockey_name, fav_rides, fav_wins, fav_win_rate, fav_places, fav_place_rate, scraped_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (item.get('jockey_name'), item.get('fav_rides'), item.get('fav_wins'), item.get('fav_win_rate'), item.get('fav_places'), item.get('fav_place_rate'), item.get('scraped_at', datetime.now().isoformat())))
        conn.commit()
        conn.close()
        return len(data)

    def save_trainer_favourites(self) -> int:
        """Fetch and save trainer favourites."""
        data = self.scraper.scrape_trainer_favourites()
        if not data:
            return 0
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM trainer_fav_stats")
        for item in data:
            cursor.execute("""
                INSERT INTO trainer_fav_stats (trainer_name, fav_runs, fav_wins, fav_win_rate, fav_places, fav_place_rate, scraped_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (item.get('trainer_name'), item.get('fav_runs'), item.get('fav_wins'), item.get('fav_win_rate'), item.get('fav_places'), item.get('fav_place_rate'), item.get('scraped_at', datetime.now().isoformat())))
        conn.commit()
        conn.close()
        return len(data)

    def save_standard_times(self) -> int:
        """Fetch and save standard times."""
        data = self.scraper.scrape_standard_times()
        if not data:
            return 0
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM standard_times")
        for t in data:
            cursor.execute("""
                INSERT INTO standard_times (distance, track_type, standard_time, record_time, record_holder, record_date, scraped_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (t['distance'], t['track_type'], t['standard_time'], t['record_time'], t.get('record_holder'), t.get('record_date'), t['scraped_at']))
        conn.commit()
        conn.close()
        return len(data)

    def sync_trackwork(self, race_date: str) -> int:
        """Sync morning trackwork data."""
        data = self.scraper.scrape_morning_trackwork(race_date)
        if not data:
            return 0
            
        conn = self._get_connection()
        cursor = conn.cursor()
        scraped_at = datetime.now().isoformat()
        
        count = 0
        for t in data:
            cursor.execute("""
                INSERT INTO detailed_trackwork (race_date, horse_name, trackwork_time, track_condition, remarks, scraped_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (race_date, t['horse_name'], t['time'], t['track'], t['work'], scraped_at))
            count += 1
            
        conn.commit()
        conn.close()
        return count

    def save_fixtures(self, *args, **kwargs) -> int:
        """Fetch and save fixtures."""
        data = self.scraper.scrape_fixtures()
        if not data:
            return 0
        
        conn = self._get_connection()
        cursor = conn.cursor()
        scraped_at = datetime.now().isoformat()
        
        count = 0
        for item in data:
            # Convert races array to JSON string
            races_json = json.dumps(item.get('races', []))
            race_date = item.get('race_date')
            racecourse = item.get('racecourse')
            
            # Check if fixture already exists
            cursor.execute("""
                SELECT id FROM fixtures WHERE race_date = ? AND racecourse = ?
            """, (race_date, racecourse))
            
            existing = cursor.fetchone()
            if existing:
                # Update existing record
                cursor.execute("""
                    UPDATE fixtures SET day_night = ?, track_type = ?, race_count = ?, races_json = ?, scraped_at = ?
                    WHERE id = ?
                """, (
                    item.get('day_night'),
                    item.get('track_type'),
                    item.get('race_count', 0),
                    races_json,
                    scraped_at,
                    existing[0]
                ))
            else:
                # Insert new record
                cursor.execute("""
                    INSERT INTO fixtures (race_date, racecourse, day_night, track_type, race_count, races_json, scraped_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    race_date,
                    racecourse,
                    item.get('day_night'),
                    item.get('track_type'),
                    item.get('race_count', 0),
                    races_json,
                    scraped_at
                ))
            count += 1
        
        conn.commit()
        conn.close()
        return count

    def save_barrier_tests(self, *args, **kwargs) -> int:
        """Fetch and save barrier tests."""
        data = self.scraper.scrape_barrier_tests()
        if not data:
            return 0
        
        conn = self._get_connection()
        cursor = conn.cursor()
        scraped_at = datetime.now().isoformat()
        
        count = 0
        for item in data:
            horse_name = item.get('horse_name')
            test_date = item.get('test_date')
            
            # Check if barrier test already exists
            cursor.execute("""
                SELECT id FROM barrier_tests WHERE horse_name = ? AND test_date = ?
            """, (horse_name, test_date))
            
            existing = cursor.fetchone()
            if existing:
                # Update existing record
                cursor.execute("""
                    UPDATE barrier_tests SET barrier = ?, time = ?, remarks = ?, scraped_at = ?
                    WHERE id = ?
                """, (
                    item.get('barrier'),
                    item.get('time'),
                    item.get('remarks'),
                    scraped_at,
                    existing[0]
                ))
            else:
                # Insert new record
                cursor.execute("""
                    INSERT INTO barrier_tests (horse_name, test_date, barrier, time, remarks, scraped_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    horse_name,
                    test_date,
                    item.get('barrier'),
                    item.get('time'),
                    item.get('remarks'),
                    scraped_at
                ))
            count += 1
        
        conn.commit()
        conn.close()
        return count

    def save_weather(self, race_date, racecourse: str) -> int:
        """Fetch and save weather."""
        if isinstance(race_date, datetime):
            race_date = race_date.strftime('%Y-%m-%d')
        
        data = self.scraper.scrape_weather(race_date, racecourse)
        if not data:
            logger.info(f"No weather data available for {race_date} at {racecourse}")
            return 0
        
        conn = self._get_connection()
        cursor = conn.cursor()
        scraped_at = datetime.now().isoformat()
        
        count = 0
        for item in data:
            # Check if weather record already exists
            cursor.execute("""
                SELECT id FROM weather WHERE race_date = ? AND racecourse = ?
            """, (race_date, racecourse))
            
            existing = cursor.fetchone()
            if existing:
                # Update existing record
                cursor.execute("""
                    UPDATE weather SET temperature = ?, humidity = ?, condition = ?, scraped_at = ?
                    WHERE id = ?
                """, (
                    item.get('temperature'),
                    item.get('humidity'),
                    item.get('condition'),
                    scraped_at,
                    existing[0]
                ))
            else:
                # Insert new record
                cursor.execute("""
                    INSERT INTO weather (race_date, racecourse, temperature, humidity, condition, scraped_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    race_date,
                    racecourse,
                    item.get('temperature'),
                    item.get('humidity'),
                    item.get('condition'),
                    scraped_at
                ))
            count += 1
        
        conn.commit()
        conn.close()
        return count

    def save_last_race_summaries(self, race_date, *args, **kwargs) -> int:
        """Fetch and save last race summaries."""
        if isinstance(race_date, datetime):
            race_date = race_date.strftime('%Y-%m-%d')
        
        data = self.scraper.scrape_last_race_summaries(race_date)
        if not data:
            return 0
        
        conn = self._get_connection()
        cursor = conn.cursor()
        scraped_at = datetime.now().isoformat()
        
        count = 0
        for item in data:
            race_number = item.get('race_number')
            
            # Check if summary already exists
            cursor.execute("""
                SELECT id FROM last_race_summaries WHERE race_date = ? AND race_number = ?
            """, (race_date, race_number))
            
            existing = cursor.fetchone()
            if existing:
                # Update existing record
                cursor.execute("""
                    UPDATE last_race_summaries SET summary_text = ?, scraped_at = ?
                    WHERE id = ?
                """, (
                    item.get('summary_text'),
                    scraped_at,
                    existing[0]
                ))
            else:
                # Insert new record
                cursor.execute("""
                    INSERT INTO last_race_summaries (race_date, race_number, summary_text, scraped_at)
                    VALUES (?, ?, ?, ?)
                """, (
                    race_date,
                    race_number,
                    item.get('summary_text'),
                    scraped_at
                ))
            count += 1
        
        conn.commit()
        conn.close()
        return count

    def save_professional_schedules(self, pro_type: str, race_date: str = None) -> int:
        """Fetch and save professional schedules."""
        if race_date is None:
            race_date = datetime.now().strftime('%Y-%m-%d')
        
        data = self.scraper.scrape_professional_schedules(pro_type, race_date)
        if not data:
            return 0
        
        conn = self._get_connection()
        cursor = conn.cursor()
        scraped_at = datetime.now().isoformat()
        
        count = 0
        for item in data:
            professional_name = item.get('professional_name')
            race_number = item.get('race_number')
            
            # Check if schedule already exists
            cursor.execute("""
                SELECT id FROM professional_schedules 
                WHERE race_date = ? AND pro_type = ? AND professional_name = ? AND race_number = ?
            """, (race_date, pro_type, professional_name, race_number))
            
            existing = cursor.fetchone()
            if existing:
                # Update existing record
                cursor.execute("""
                    UPDATE professional_schedules SET horse_name = ?, schedule_details = ?, scraped_at = ?
                    WHERE id = ?
                """, (
                    item.get('horse_name'),
                    item.get('details'),
                    scraped_at,
                    existing[0]
                ))
            else:
                # Insert new record
                cursor.execute("""
                    INSERT INTO professional_schedules (race_date, pro_type, professional_name, race_number, horse_name, schedule_details, scraped_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    race_date,
                    pro_type,
                    professional_name,
                    race_number,
                    item.get('horse_name'),
                    item.get('details'),
                    scraped_at
                ))
            count += 1
        
        conn.commit()
        conn.close()
        return count

    def save_barrier_stats_v2(self) -> int:
        """Fetch and save barrier stats."""
        # Check if scraper method exists
        if not hasattr(self.scraper, 'scrape_barrier_stats_v2'):
            logger.warning("scrape_barrier_stats_v2 method not implemented in scraper")
            return 0
        
        data = self.scraper.scrape_barrier_stats_v2()
        if not data:
            return 0
        
        conn = self._get_connection()
        cursor = conn.cursor()
        scraped_at = datetime.now().isoformat()
        
        # Clear existing stats and insert fresh data (stats are refreshed completely)
        cursor.execute("DELETE FROM barrier_stats")
        
        count = 0
        for item in data:
            cursor.execute("""
                INSERT INTO barrier_stats (horse_name, barrier_position, wins, runs, win_rate, scraped_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                item.get('horse_name'),
                item.get('barrier_position'),
                item.get('wins', 0),
                item.get('runs', 0),
                item.get('win_rate', 0.0),
                scraped_at
            ))
            count += 1
        
        conn.commit()
        conn.close()
        return count

    def save_wind_tracker(self, race_date) -> int:
        """Fetch and save wind data."""
        if isinstance(race_date, datetime):
            race_date = race_date.strftime('%Y-%m-%d')
        
        data = self.scraper.scrape_wind_tracker(race_date)
        if not data:
            return 0
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Schema safety check
        try:
            cursor.execute("PRAGMA table_info(wind_tracker)")
            cols = [row[1] for row in cursor.fetchall()]
            if 'track' not in cols:
                cursor.execute("ALTER TABLE wind_tracker ADD COLUMN track TEXT")
        except: pass
            
        scraped_at = datetime.now().isoformat()
        
        count = 0
        for item in data:
            track = item.get('track')
            position = item.get('position')
            
            # Check if wind tracker record already exists
            cursor.execute("""
                SELECT id FROM wind_tracker WHERE race_date = ? AND track = ? AND position = ?
            """, (race_date, track, position))
            
            existing = cursor.fetchone()
            if existing:
                # Update existing record
                cursor.execute("""
                    UPDATE wind_tracker SET wind_direction = ?, wind_speed = ?, gust_speed = ?, 
                    temperature = ?, humidity = ?, rainfall = ?, update_time = ?, scraped_at = ?
                    WHERE id = ?
                """, (
                    item.get('wind_direction'),
                    item.get('wind_speed'),
                    item.get('gust_speed'),
                    item.get('temperature'),
                    item.get('humidity'),
                    item.get('rainfall'),
                    item.get('update_time'),
                    scraped_at,
                    existing[0]
                ))
            else:
                # Insert new record
                cursor.execute("""
                    INSERT INTO wind_tracker (race_date, track, position, wind_direction, wind_speed, gust_speed, temperature, humidity, rainfall, update_time, scraped_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    race_date,
                    track,
                    position,
                    item.get('wind_direction'),
                    item.get('wind_speed'),
                    item.get('gust_speed'),
                    item.get('temperature'),
                    item.get('humidity'),
                    item.get('rainfall'),
                    item.get('update_time'),
                    scraped_at
                ))
            count += 1
        
        conn.commit()
        conn.close()
        return count

    def save_battle_memorandum(self, *args, **kwargs) -> int:
        """Fetch and save battle memorandum."""
        data = self.scraper.scrape_battle_memorandum()
        if not data:
            return 0
        
        conn = self._get_connection()
        cursor = conn.cursor()
        scraped_at = datetime.now().isoformat()
        
        # Clear existing memoranda and insert fresh data (latest memo for each horse)
        cursor.execute("DELETE FROM battle_memorandum")
        
        count = 0
        for item in data:
            cursor.execute("""
                INSERT INTO battle_memorandum (horse_name, last_race_date, memo, scraped_at)
                VALUES (?, ?, ?, ?)
            """, (
                item.get('horse_name'),
                item.get('last_race_date'),
                item.get('memo'),
                scraped_at
            ))
            count += 1
        
        conn.commit()
        conn.close()
        return count

    def save_new_horse_introductions(self, *args, **kwargs) -> int:
        """Fetch and save new horse introductions."""
        data = self.scraper.scrape_new_horse_introductions()
        if not data:
            return 0
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Double check schema
        try:
            cursor.execute("PRAGMA table_info(new_horse_introductions)")
            cols = [row[1] for row in cursor.fetchall()]
            if 'origin' not in cols:
                cursor.execute("ALTER TABLE new_horse_introductions ADD COLUMN origin TEXT")
            if 'trainer' not in cols:
                cursor.execute("ALTER TABLE new_horse_introductions ADD COLUMN trainer TEXT")
            if 'age' not in cols:
                cursor.execute("ALTER TABLE new_horse_introductions ADD COLUMN age TEXT")
            if 'sex' not in cols:
                cursor.execute("ALTER TABLE new_horse_introductions ADD COLUMN sex TEXT")
        except:
            pass
            
        scraped_at = datetime.now().isoformat()
        
        # Clear existing introductions and insert fresh data (latest list of new horses)
        cursor.execute("DELETE FROM new_horse_introductions")
        
        count = 0
        for item in data:
            cursor.execute("""
                INSERT INTO new_horse_introductions (horse_name, origin, trainer, age, sex, scraped_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                item.get('horse_name'),
                item.get('origin'),
                item.get('trainer'),
                item.get('age'),
                item.get('sex'),
                scraped_at
            ))
            count += 1
        
        conn.commit()
        conn.close()
        return count

    def save_injury_records_v2(self) -> int:
        """Fetch and save injury records."""
        data = self.scraper.scrape_injury_records()
        if not data:
            return 0
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Schema safety check
        try:
            cursor.execute("PRAGMA table_info(injury_records)")
            cols = [row[1] for row in cursor.fetchall()]
            if 'condition' not in cols:
                cursor.execute("ALTER TABLE injury_records ADD COLUMN condition TEXT")
            if 'status' not in cols:
                cursor.execute("ALTER TABLE injury_records ADD COLUMN status TEXT")
        except: pass
            
        scraped_at = datetime.now().isoformat()
        
        count = 0
        for item in data:
            horse_name = item.get('horse_name')
            injury_date = item.get('injury_date')
            
            # Check if injury record already exists
            cursor.execute("""
                SELECT id FROM injury_records WHERE horse_name = ? AND injury_date = ?
            """, (horse_name, injury_date))
            
            existing = cursor.fetchone()
            if existing:
                # Update existing record
                cursor.execute("""
                    UPDATE injury_records SET condition = ?, status = ?, scraped_at = ?
                    WHERE id = ?
                """, (
                    item.get('condition'),
                    item.get('status'),
                    scraped_at,
                    existing[0]
                ))
            else:
                # Insert new record
                cursor.execute("""
                    INSERT INTO injury_records (horse_name, injury_date, condition, status, scraped_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    horse_name,
                    injury_date,
                    item.get('condition'),
                    item.get('status'),
                    scraped_at
                ))
            count += 1
        
        conn.commit()
        conn.close()
        return count


    def sync_professional_schedules(self, race_date: str, *args, **kwargs) -> int:
        """Sync jockey and trainer schedules."""
        total = 0
        for pro_type in ['jockey', 'trainer']:
            count = self.save_professional_schedules(pro_type, race_date)
            total += count
        return total
    def update_trainer_king_odds(self, race_date: str) -> int:
        """Update trainer king odds for a specific date."""
        data = self.scraper.scrape_trainer_king_odds(race_date)
        if data:
            return self.save_trainer_king_odds(race_date, data)
        return 0

    def update_race_day_changes(self, race_date: str) -> int:
        """Update race day changes for a specific date."""
        data = self.scraper.scrape_race_day_changes(race_date)
        if data:
            return self.save_race_day_changes(race_date, data)
        return 0

    def update_track_selection(self, race_date: str) -> int:
        """Update track selection data for a specific date."""
        data = self.scraper.scrape_track_selection(race_date)
        if data:
            return self.save_track_selection(race_date, data)
        return 0
